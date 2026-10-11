import importlib.util
import json
import os
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
spec = importlib.util.spec_from_file_location("mock_exam", ROOT / "exam_prep" / "mock_exam.py")
mock_exam = importlib.util.module_from_spec(spec)
sys.modules["mock_exam"] = mock_exam
spec.loader.exec_module(mock_exam)

from _harness import quizlib  # noqa: E402

TASK_OF = {1: "1.1", 2: "2.2", 3: "3.3", 4: "4.1"}


def raw(n, domain, multi=False):
    stem = (f"Mock question {n}: a company runs workload {n * 104729} on AWS in domain {domain} and needs a change. "
            + ("Which steps meet these requirements? (Select TWO.)" if multi else "Which solution meets these requirements?"))
    letters = "ABCDE" if multi else "ABCD"
    return {"id": f"mock1-q{n:02d}", "domain": domain, "task": TASK_OF[domain], "services": ["EC2"],
            "kind": "multi" if multi else "single", **({"choose": 2} if multi else {}), "stem": stem,
            "options": [f"Option {c} for {n}" for c in letters], "answer": ["A", "B"] if multi else ["ABCD"[n % 4]],
            "explain": {c: f"Explanation {c}." for c in letters}, "ref": "week_00_x/concepts/01.md"}


def full_bank():
    raws, n = [], 0
    for domain, count in mock_exam.DOMAIN_SPLIT.items():
        for i in range(count):
            n += 1
            raws.append(raw(n, domain, multi=(i < 2)))
    return raws


def toml(raws):
    out = []
    for q in raws:
        out.append("[[question]]")
        for k, v in q.items():
            out.append("explain = { " + ", ".join(f'{a} = "{b}"' for a, b in v.items()) + " }" if k == "explain" else f"{k} = {json.dumps(v)}")
        out.append("")
    return "\n".join(out)


def questions():
    return [quizlib.Question.from_raw(r) for r in full_bank()]


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def correct_display(exam, index):
    q = exam.questions[index]
    return "".join(d for d, o in exam.mappings[index] if o in q.answer).lower()


def test_mock_problems():
    assert mock_exam.mock_problems(questions()) == []
    short = questions()[:-1]
    assert any("65" in p for p in mock_exam.mock_problems(short))


def test_score_report_counts_unanswered_as_wrong():
    qs = questions()
    answers = {q.id: set(q.answer) for q in qs[:52]}
    report = mock_exam.score_report(qs, answers)
    assert report["correct"] == 52 and report["total"] == 65 and report["pct"] == 80
    assert report["passed_guide"] is True
    assert report["domains"][4] == {"correct": 0, "total": 13, "pct": 0}
    assert report["unanswered"] == 13


def test_run_answer_flag_navigate_review_submit():
    qs = questions()
    clock = Clock()
    exam = mock_exam.MockExam(qs, random.Random(2), clock=clock)
    script = [correct_display(exam, 0), "f", "p", "n", "g 65", "r", "s", "y"]
    # after answering Q1 the exam moves to Q2; "f" flags Q2; "p" goes back to Q1; "n" → Q2;
    # "g 65" jumps to the last question; "r" shows the review screen; "s" submits; "y" confirms
    feed = iter(script)
    out = []
    answers = exam.run(input_fn=lambda prompt: next(feed), print_fn=out.append)
    text = "\n".join(out)
    first, second = exam.questions[0], exam.questions[1]  # the exam shuffles question order
    assert answers == {first.id: set(first.answer)}
    assert second.id in exam.flags
    assert "Review" in text and "unanswered: 64" in text and "flagged: 1" in text


def test_time_up_submits():
    qs = questions()
    clock = Clock()
    exam = mock_exam.MockExam(qs, random.Random(2), clock=clock)

    def answer(prompt):
        clock.t += 131 * 60
        return correct_display(exam, exam.current)
    out = []
    answers = exam.run(input_fn=answer, print_fn=out.append)
    assert "Time is up" in "\n".join(out)
    assert len(answers) <= 1


def test_untimed_never_expires():
    exam = mock_exam.MockExam(questions(), random.Random(2), clock=Clock(), duration=None)
    assert exam.remaining() is None


def test_review_markdown_lists_missed():
    qs = questions()
    report = mock_exam.score_report(qs, {})
    text = mock_exam.review_markdown(qs, {}, report)
    assert text.count("### ") == 65 and "Explanation A." in text and "Domain 1" in text


def test_mock_cli_piped(tmp_path):
    course = tmp_path / "course"
    (course / "exam_prep" / "mock_exams").mkdir(parents=True)
    (course / "exam_prep" / "mock_exams" / "mock_1.toml").write_text(toml(full_bank()), encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
    proc = subprocess.run([PY, str(ROOT / "exam_prep" / "mock_exam.py"), "1", "--root", str(course), "--seed", "1"],
                          input=b"a\ns\ny\n", capture_output=True, env=env, timeout=120)
    out = proc.stdout.decode("utf-8")
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    assert "Score:" in out and "Domain 1" in out
    assert list((course / "_progress").glob("mock_1_*.md"))
    progress = json.loads((course / "_progress" / "progress.json").read_text(encoding="utf-8"))
    assert progress["mocks"][0]["mock"] == 1


def test_mock_cli_missing_bank(tmp_path):
    proc = subprocess.run([PY, str(ROOT / "exam_prep" / "mock_exam.py"), "2", "--root", str(tmp_path)],
                          capture_output=True, timeout=120)
    assert proc.returncode == 2 and "Mock exam 2 is not built yet" in proc.stdout.decode("utf-8")

import datetime as dt
import json
import os
import random
import subprocess
import sys
from pathlib import Path

import pytest

from _harness import quizlib
from _harness.quizlib import (BankError, Progress, bank_problems, grade, load_bank, near_duplicates,
                              parse_answer, retired_hits, run_session, select_questions, shuffle_options,
                              validate_question)
from bankgen import balanced_raws, raw_multi, raw_single, toml_bank

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
TODAY = dt.date(2026, 10, 8)


def to_questions(raws):
    return [quizlib.Question.from_raw(r) for r in raws]


def test_valid_single_and_multi():
    assert validate_question(raw_single()) == []
    assert validate_question(raw_multi(choose=2)) == []
    assert validate_question(raw_multi(choose=3)) == []


@pytest.mark.parametrize("change, problem", [
    ({"id": "bad id"}, "id"),
    ({"domain": 5}, "domain"),
    ({"task": "1.1"}, "task 1.1 is not in domain 4"),
    ({"task": "4.9"}, "unknown task"),
    ({"kind": "pick"}, "kind"),
    ({"options": ["a", "b", "c"]}, "4 options"),
    ({"options": ["a", "a", "b", "c"]}, "duplicate options"),
    ({"answer": ["E"]}, "answer letter"),
    ({"answer": ["A", "B"]}, "exactly 1"),
    ({"explain": {"A": "x", "B": "y", "C": "z"}}, "explain"),
    ({"stem": "Too short?"}, "stem"),
    ({"stem": "A long enough stem about storing logs in S3 for a long time without any question mark at the end."}, "end with"),
    ({"services": []}, "services"),
    ({"legacy": "yes"}, "legacy"),
])
def test_invalid_questions(change, problem):
    raw = {**raw_single(), **change}
    problems = validate_question(raw)
    assert any(problem in p for p in problems), problems


def test_multi_needs_select_suffix_and_counts():
    raw = raw_multi(choose=2)
    raw["stem"] = raw["stem"].replace("(Select TWO.)", "(Select THREE.)")
    assert any("(Select TWO.)" in p for p in validate_question(raw))
    raw = raw_multi(choose=2)
    raw["answer"] = ["A"]
    assert any("exactly 2" in p for p in validate_question(raw))


def test_ref_must_exist_when_root_given(tmp_path):
    (tmp_path / "week_04_storage" / "concepts").mkdir(parents=True)
    assert any("ref" in p for p in validate_question(raw_single(), root=tmp_path))
    (tmp_path / "week_04_storage" / "concepts" / "01_s3.md").write_text("x")
    assert validate_question(raw_single(), root=tmp_path) == []


def test_load_bank_reports_every_problem(tmp_path):
    path = tmp_path / "questions.toml"
    path.write_text(toml_bank([raw_single(1), {**raw_single(2), "domain": 9}, {**raw_single(3), "id": "w04-q01"}]),
                    encoding="utf-8")
    with pytest.raises(BankError) as info:
        load_bank(path)
    text = str(info.value)
    assert "w04-q02" in text and "duplicate id w04-q01" in text


def test_load_bank_reads_questions(tmp_path):
    path = tmp_path / "questions.toml"
    path.write_text(toml_bank([raw_single(1), raw_multi(2)]), encoding="utf-8")
    questions = load_bank(path)
    assert [q.id for q in questions] == ["w04-q01", "w04-q02"]
    assert questions[1].answer == frozenset({"A", "B"}) and questions[1].choose == 2
    assert questions[0].source == str(path)


def test_load_bank_bad_toml(tmp_path):
    path = tmp_path / "questions.toml"
    path.write_text("[[question]\nid = ", encoding="utf-8")
    with pytest.raises(BankError, match="TOML"):
        load_bank(path)


def balanced_bank(n=30, multi=4):
    return to_questions(balanced_raws(n, multi))


def test_bank_problems_clean_bank():
    assert bank_problems(balanced_bank(), expected_count=30) == []


def test_bank_problems_detects_count_multi_letters_and_longest():
    bank = balanced_bank(30, multi=0)
    problems = " | ".join(bank_problems(bank, expected_count=30))
    assert "multi-response" in problems
    one_letter = to_questions([raw_single(i, answer="A") for i in range(1, 31)])
    problems = " | ".join(bank_problems(one_letter, expected_count=31))
    assert "expected 31 questions" in problems and "letter A" in problems
    longest = []
    for i in range(1, 31):
        raw = raw_single(i, answer="ABCD"[i % 4])
        raw["options"] = [o + (" — clearly the longest option of all" if "ABCD"[k] == raw["answer"][0] else "")
                          for k, o in enumerate(raw["options"])]
        longest.append(raw)
    assert any("longest" in p for p in bank_problems(to_questions(longest), expected_count=30))


def test_near_duplicates():
    a = raw_single(1, stem="A company stores logs in Amazon S3 for seven years. Which storage class is the MOST cost-effective?")
    b = raw_single(2, stem="A company stores logs in Amazon S3 for seven years. Which storage class is MOST cost-effective?")
    c = raw_single(3, stem="An application needs single-digit millisecond reads from a key-value store at any scale. Which service fits?")
    pairs = near_duplicates(to_questions([a, b, c]))
    assert [(x, y) for x, y, _ in pairs] == [("w04-q01", "w04-q02")]


def test_retired_and_legacy_names():
    assert retired_hits("Use Amazon QLDB for the ledger") == ["Amazon QLDB"]
    assert retired_hits("Build a data pipeline with AWS Glue") == []  # the generic phrase is fine
    assert retired_hits("Create a launch configuration") == ["launch configurations"]
    assert quizlib.legacy_hits("Order an AWS Snowball Edge device") == ["Snowball Edge"]


def test_retired_service_in_bank_is_a_problem():
    raw = raw_single(1)
    raw["options"][0] = "Store the ledger in Amazon QLDB"
    assert any("retired" in p for p in bank_problems(to_questions([raw]), expected_count=1))
    raw = raw_single(2)
    raw["options"][0] = "Ship the data with AWS Snowball Edge"
    assert any("legacy" in p for p in bank_problems(to_questions([raw]), expected_count=1))
    raw["legacy"] = True
    assert not any("legacy" in p for p in bank_problems(to_questions([raw]), expected_count=1))


@pytest.mark.parametrize("text, n, choose, letters, error", [
    ("b", 4, 1, ["B"], ""), (" B ", 4, 1, ["B"], ""), ("a, c", 5, 2, ["A", "C"], ""), ("ca", 5, 2, ["A", "C"], ""),
    ("", 4, 1, None, "letter"), ("e", 4, 1, None, "A–D"), ("ab", 4, 1, None, "one letter"),
    ("a", 5, 2, None, "exactly 2"), ("aa", 5, 2, None, "once"), ("a1", 5, 2, None, "A–E"),
])
def test_parse_answer_variants(text, n, choose, letters, error):
    got, message = parse_answer(text, n, choose)
    assert got == letters
    assert (error in message) if error else message == ""


def test_shuffle_maps_back_to_original_letters():
    q = to_questions([raw_single(1, answer="C")])[0]
    mapping = shuffle_options(q, random.Random(3))
    assert sorted(o for _, o in mapping) == list("ABCD") and [d for d, _ in mapping] == list("ABCD")
    display_for_c = next(d for d, o in mapping if o == "C")
    original = [dict(mapping)[display_for_c]]
    assert grade(q, original) and not grade(q, ["A"] if original != ["A"] else ["B"])


def test_progress_boxes_and_due(tmp_path):
    p = Progress(tmp_path / "progress.json", today=TODAY)
    assert not p.seen("w04-q01")
    p.record("w04-q01", True, TODAY)
    assert p.box("w04-q01") == 2 and not p.is_due("w04-q01", TODAY)
    assert p.is_due("w04-q01", TODAY + dt.timedelta(days=1))
    p.record("w04-q01", True, TODAY)
    assert p.box("w04-q01") == 3
    p.record("w04-q01", False, TODAY)
    assert p.box("w04-q01") == 1 and p.is_due("w04-q01", TODAY)
    for _ in range(9):
        p.record("w04-q02", True, TODAY)
    assert p.box("w04-q02") == 5


def test_save_is_atomic_and_reloads(tmp_path):
    path = tmp_path / "sub" / "progress.json"
    p = Progress(path, today=TODAY)
    p.record("w04-q01", False, TODAY)
    p.save()
    assert not list(path.parent.glob("*.tmp"))
    assert Progress(path, today=TODAY).box("w04-q01") == 1


def test_corrupt_progress_is_backed_up(tmp_path):
    path = tmp_path / "progress.json"
    path.write_text('{"questions": {"w04-q01": {"box": 3', encoding="utf-8")
    p = Progress(path, today=TODAY)
    assert p.warning and "backed up" in p.warning
    assert p.data["questions"] == {}
    assert len(list(tmp_path.glob("progress.json.bad-*"))) == 1


def test_select_missed_first_then_unseen(tmp_path):
    bank = to_questions([raw_single(i) for i in range(1, 7)])
    p = Progress(tmp_path / "p.json", today=TODAY)
    p.record("w04-q05", False, TODAY)     # missed
    p.record("w04-q06", True, TODAY)      # seen, not due today
    chosen = select_questions(bank, p, 3, TODAY, random.Random(1))
    assert chosen[0].id == "w04-q05" and "w04-q06" not in [q.id for q in chosen]
    review = select_questions(bank, p, 10, TODAY, random.Random(1), review=True)
    assert [q.id for q in review] == ["w04-q05"]


def test_session_reprompts_on_bad_input(tmp_path):
    bank = to_questions([raw_single(1, answer="B")])
    p = Progress(tmp_path / "p.json", today=TODAY)
    mapping = shuffle_options(bank[0], random.Random(5))
    right = next(d for d, o in mapping if o == "B").lower()
    answers = iter(["", "zz", "ab", right])
    out = []
    summary = run_session(bank, p, input_fn=lambda prompt: next(answers), print_fn=out.append,
                          rng=random.Random(5), today=TODAY)
    text = "\n".join(out)
    assert summary == {"asked": 1, "correct": 1, "quit": False}
    assert "Use letters A–D" in text and "one letter" in text and "✔ Correct" in text
    assert "Because B." in text and "Read more: week_04_storage/concepts/01_s3.md" in text
    assert p.box("w04-q01") == 2


def test_session_quit_and_eof(tmp_path):
    bank = to_questions([raw_single(1), raw_single(2)])
    p = Progress(tmp_path / "p.json", today=TODAY)
    summary = run_session(bank, p, input_fn=lambda prompt: "q", print_fn=lambda *_: None, rng=random.Random(1), today=TODAY)
    assert summary == {"asked": 0, "correct": 0, "quit": True}

    def eof(prompt):
        raise EOFError
    assert run_session(bank, p, input_fn=eof, print_fn=lambda *_: None, rng=random.Random(1), today=TODAY)["quit"]


def make_course(tmp_path) -> Path:
    week = tmp_path / "course" / "week_04_storage"
    (week / "quiz").mkdir(parents=True)
    (week / "concepts").mkdir()
    (week / "concepts" / "01_s3.md").write_text("notes", encoding="utf-8")  # every question's ref must exist
    (week / "quiz" / "questions.toml").write_text(toml_bank([raw_single(i) for i in range(1, 4)]), encoding="utf-8")
    return tmp_path / "course"


def test_discover_banks(tmp_path):
    root = make_course(tmp_path)
    assert quizlib.discover_banks(root) == {4: root / "week_04_storage" / "quiz" / "questions.toml"}


def test_quiz_cli_piped(tmp_path):
    root = make_course(tmp_path)
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
    proc = subprocess.run([PY, str(ROOT / "quiz.py"), "--root", str(root), "--week", "4", "-n", "2", "--seed", "1"],
                          input=b"a\nq\n", capture_output=True, env=env, timeout=120)
    out = proc.stdout.decode("utf-8")
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    assert "Question 1 of 2" in out and ("✔ Correct" in out or "✘ Not quite" in out)
    assert (root / "_progress" / "progress.json").exists()
    stats = subprocess.run([PY, str(ROOT / "quiz.py"), "--root", str(root), "--stats"], capture_output=True, env=env, timeout=120)
    assert "Design Cost-Optimized Architectures" in stats.stdout.decode("utf-8")


def test_quiz_cli_missing_week(tmp_path):
    root = make_course(tmp_path)
    proc = subprocess.run([PY, str(ROOT / "quiz.py"), "--root", str(root), "--week", "7"], capture_output=True, timeout=120)
    assert proc.returncode == 2 and "no quiz for week 07" in proc.stdout.decode("utf-8")

"""mock_exam.py — a full SAA-C03 practice exam in the terminal.

    python exam_prep/mock_exam.py 1            mock exam 1: 65 questions, 130 minutes
    python exam_prep/mock_exam.py 1 --untimed  no clock

At the prompt:  letters answer (e.g. b or ac) · Enter or n next · p previous · g 12 go to question 12
                f flag/unflag for review · r review screen · s submit
Unanswered questions count as wrong (as in the real exam) — there is no penalty for guessing.
All 65 questions are scored here; the real exam scores 50 of them and hides 15 unscored ones.
"≥ 72 % raw" is only a guide: AWS reports a scaled score (100–1,000, pass 720) whose mapping from
raw answers is not published.
"""
from __future__ import annotations

import argparse
import datetime as dt
import random
import sys
import time
from pathlib import Path

ROOT_DEFAULT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DEFAULT))
from _harness import quizlib  # noqa: E402
from _harness.awslib.safety import force_utf8  # noqa: E402

DURATION_S = 130 * 60
DOMAIN_SPLIT = {1: 20, 2: 17, 3: 15, 4: 13}
PASS_GUIDE = 72


def mock_problems(questions) -> list[str]:
    problems = quizlib.bank_problems(questions, expected_count=65)
    for domain, want in DOMAIN_SPLIT.items():
        got = sum(q.domain == domain for q in questions)
        if got != want:
            problems.append(f"domain {domain} has {got} questions; a mock needs {want}")
    return problems


class MockExam:
    def __init__(self, questions, rng: random.Random, clock=time.monotonic, duration=DURATION_S):
        self.questions = list(questions)
        rng.shuffle(self.questions)
        self.mappings = [quizlib.shuffle_options(q, rng) for q in self.questions]
        self.clock, self.duration = clock, duration
        self.start = clock()
        self.answers: dict[str, set] = {}
        self.flags: set[str] = set()
        self.current = 0

    def remaining(self):
        if self.duration is None:
            return None
        return max(0.0, self.duration - (self.clock() - self.start))

    def _show(self, print_fn) -> None:
        q, mapping = self.questions[self.current], self.mappings[self.current]
        left = self.remaining()
        clock = "untimed" if left is None else f"{int(left // 60)}:{int(left % 60):02d} left"
        flag = "  [flagged]" if q.id in self.flags else ""
        print_fn(f"\n── Question {self.current + 1}/{len(self.questions)} · {clock}{flag}")
        print_fn(q.stem + "\n")
        chosen = {d for d, o in mapping if o in self.answers.get(q.id, set())}
        for display, original in mapping:
            mark = "●" if display in chosen else "○"
            print_fn(f"  {mark} {display}. {q.options[quizlib.LETTERS.index(original)]}")

    def _review(self, print_fn) -> None:
        unanswered = [i + 1 for i, q in enumerate(self.questions) if q.id not in self.answers]
        flagged = [i + 1 for i, q in enumerate(self.questions) if q.id in self.flags]
        print_fn("\n── Review")
        print_fn(f"answered: {len(self.questions) - len(unanswered)} · unanswered: {len(unanswered)} · flagged: {len(flagged)}")
        if flagged:
            print_fn("flagged questions: " + ", ".join(map(str, flagged)))
        if unanswered:
            print_fn("unanswered questions: " + ", ".join(map(str, unanswered[:40])) + (" …" if len(unanswered) > 40 else ""))

    def run(self, input_fn=input, print_fn=print) -> dict:
        self._show(print_fn)
        while True:
            left = self.remaining()
            if left is not None and left <= 0:
                print_fn("\nTime is up — the exam is submitted.")
                return self.answers
            try:
                text = input_fn("\n> ").strip()
            except EOFError:
                text = "s!"
            left = self.remaining()
            if left is not None and left <= 0:
                print_fn("\nTime is up — the exam is submitted.")
                return self.answers
            low = text.lower()
            q = self.questions[self.current]
            if low in ("", "n"):
                self.current = min(self.current + 1, len(self.questions) - 1)
            elif low == "p":
                self.current = max(self.current - 1, 0)
            elif low.startswith("g "):
                try:
                    self.current = min(max(int(low[2:]) - 1, 0), len(self.questions) - 1)
                except ValueError:
                    print_fn("Type g and a question number, e.g. g 12.")
                    continue
            elif low == "f":
                self.flags.symmetric_difference_update({q.id})
                print_fn("Flagged." if q.id in self.flags else "Flag removed.")
                continue
            elif low == "r":
                self._review(print_fn)
                continue
            elif low in ("s", "s!"):
                missing = sum(1 for x in self.questions if x.id not in self.answers)
                if low == "s" and missing:
                    try:
                        sure = input_fn(f"{missing} question(s) unanswered — they count as wrong. Submit? (y/n) ")
                    except EOFError:
                        sure = "y"
                    if sure.strip().lower() != "y":
                        continue
                return self.answers
            else:
                letters, message = quizlib.parse_answer(text, len(q.options), q.choose)
                if letters is None:
                    print_fn(message)
                    continue
                mapping = dict(self.mappings[self.current])
                self.answers[q.id] = {mapping[d] for d in letters}
                self.current = min(self.current + 1, len(self.questions) - 1)
            self._show(print_fn)


def score_report(questions, answers) -> dict:
    def pct(c, t):
        return round(100 * c / t) if t else 0

    correct = [q for q in questions if quizlib.grade(q, answers.get(q.id, set()))]
    report = {"correct": len(correct), "total": len(questions), "pct": pct(len(correct), len(questions)),
              "unanswered": sum(q.id not in answers for q in questions), "domains": {}, "tasks": {}}
    for domain in quizlib.DOMAINS:
        mine = [q for q in questions if q.domain == domain]
        c = sum(q in correct for q in mine)
        report["domains"][domain] = {"correct": c, "total": len(mine), "pct": pct(c, len(mine))}
    for task in sorted({q.task for q in questions}):
        mine = [q for q in questions if q.task == task]
        c = sum(q in correct for q in mine)
        report["tasks"][task] = {"correct": c, "total": len(mine), "pct": pct(c, len(mine))}
    report["passed_guide"] = report["pct"] >= PASS_GUIDE
    return report


def review_markdown(questions, answers, report) -> str:
    lines = [f"# Mock exam review — {report['correct']}/{report['total']} ({report['pct']} %)", ""]
    for domain, info in report["domains"].items():
        lines.append(f"- Domain {domain} {quizlib.DOMAINS[domain]}: {info['correct']}/{info['total']} ({info['pct']} %)")
    lines += ["", "## Questions you missed", ""]
    for q in questions:
        if quizlib.grade(q, answers.get(q.id, set())):
            continue
        chosen = ", ".join(sorted(answers.get(q.id, set()))) or "no answer"
        lines += [f"### {q.id} · Domain {q.domain} · task {q.task}", "", q.stem, ""]
        for i, option in enumerate(q.options):
            letter = quizlib.LETTERS[i]
            mark = "✔" if letter in q.answer else "·"
            lines.append(f"- {mark} **{letter}.** {option} — {q.explain[letter]}")
        lines += ["", f"Your answer: {chosen} · correct: {', '.join(sorted(q.answer))} · read: {q.ref}", ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    force_utf8()
    parser = argparse.ArgumentParser(description="Take a full SAA-C03 mock exam.")
    parser.add_argument("number", type=int)
    parser.add_argument("--untimed", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    root = args.root.resolve()
    bank = root / "exam_prep" / "mock_exams" / f"mock_{args.number}.toml"
    if not bank.exists():
        print(f"Mock exam {args.number} is not built yet.")
        return 2
    try:
        questions = quizlib.load_bank(bank)
    except quizlib.BankError as exc:
        print(f"The mock exam bank has problems:\n{exc}")
        return 2
    print(__doc__.split("\n\n")[2])
    exam = MockExam(questions, random.Random(args.seed), duration=None if args.untimed else DURATION_S)
    answers = exam.run()
    report = score_report(questions, answers)
    print(f"\nScore: {report['correct']}/{report['total']} ({report['pct']} %)  ·  unanswered: {report['unanswered']}")
    for domain, info in report["domains"].items():
        print(f"  Domain {domain} {quizlib.DOMAINS[domain]:<40} {info['correct']:>2}/{info['total']:<2} ({info['pct']} %)")
    verdict = "at or above" if report["passed_guide"] else "below"
    print(f"\nThat is {verdict} the {PASS_GUIDE} % guide (a rough stand-in for the scaled 720 pass mark).")
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = root / "_progress"
    out_dir.mkdir(parents=True, exist_ok=True)
    review = out_dir / f"mock_{args.number}_{stamp}.md"
    review.write_text(review_markdown(questions, answers, report), encoding="utf-8")
    print(f"Every missed question with explanations: {review}")
    progress = quizlib.Progress(out_dir / "progress.json")
    progress.data["mocks"].append({"mock": args.number, "date": dt.date.today().isoformat(),
                                   "pct": report["pct"], "domains": {str(k): v["pct"] for k, v in report["domains"].items()}})
    progress.save()
    return 0


if __name__ == "__main__":
    sys.exit(main())

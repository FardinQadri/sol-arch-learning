"""quiz.py — practise the course's scenario questions in the terminal.

    python quiz.py --week 4          10 questions from week 04 (missed and unseen first)
    python quiz.py --week 4 -n 30    the whole week
    python quiz.py --all -n 20       20 questions from every week built so far
    python quiz.py --domain 1        questions from one exam domain (1 Secure … 4 Cost)
    python quiz.py --review          questions you missed or that are due again (spaced repetition)
    python quiz.py --stats           your accuracy per exam domain

Your progress is kept in _progress/progress.json (not part of the course; safe to delete).
"""
from __future__ import annotations

import argparse
import datetime as dt
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _harness import quizlib  # noqa: E402
from _harness.awslib.safety import force_utf8  # noqa: E402


def load_all(root: Path, weeks) -> list:
    questions = []
    for week in weeks:
        questions += quizlib.load_bank(quizlib.discover_banks(root)[week], root)
    return questions


def stats(root: Path, progress: quizlib.Progress) -> None:
    banks = quizlib.discover_banks(root)
    by_id = {q.id: q for q in load_all(root, sorted(banks))}
    print("Accuracy per exam domain (answers so far):")
    for domain, name in quizlib.DOMAINS.items():
        entries = [e for qid, e in progress.data["questions"].items() if qid in by_id and by_id[qid].domain == domain]
        seen = sum(e["seen"] for e in entries)
        right = sum(e["right"] for e in entries)
        pct = f"{round(100 * right / seen)}%" if seen else "—"
        print(f"  {domain} {name:<40} {right:>4}/{seen:<4} {pct}")
    boxes = [e["box"] for e in progress.data["questions"].values()]
    print("Leitner boxes: " + "  ".join(f"{b}:{boxes.count(b)}" for b in range(1, 6)))


def main(argv=None) -> int:
    force_utf8()
    parser = argparse.ArgumentParser(description="Practise SAA-C03 scenario questions.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--week", type=int)
    group.add_argument("--all", action="store_true")
    group.add_argument("--domain", type=int, choices=sorted(quizlib.DOMAINS))
    group.add_argument("--review", action="store_true")
    group.add_argument("--stats", action="store_true")
    parser.add_argument("-n", type=int, default=None, help="how many questions (default 10, review 20)")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    root = args.root.resolve()
    progress = quizlib.Progress(root / "_progress" / "progress.json")
    banks = quizlib.discover_banks(root)
    try:
        if args.stats:
            stats(root, progress)
            return 0
        if args.week is not None:
            if args.week not in banks:
                print(f"There is no quiz for week {args.week:02d} yet. Built: {', '.join(f'{w:02d}' for w in sorted(banks)) or 'none'}.")
                return 2
            pool = load_all(root, [args.week])
        else:
            pool = load_all(root, sorted(banks))
            if args.domain:
                pool = [q for q in pool if q.domain == args.domain]
    except quizlib.BankError as exc:
        print(f"A question bank has problems:\n{exc}")
        return 2

    rng = random.Random(args.seed)
    today = dt.date.today()
    n = args.n or (20 if args.review else 10)
    chosen = quizlib.select_questions(pool, progress, n, today, rng, review=args.review)
    if not chosen:
        print("Nothing to review today — come back tomorrow, or try --week N.")
        return 0
    quizlib.run_session(chosen, progress, rng=rng, today=today)
    return 0


if __name__ == "__main__":
    sys.exit(main())

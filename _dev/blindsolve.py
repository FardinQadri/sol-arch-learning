"""blindsolve — maintainer tool for the blind-solve check on a question bank (spec §4.3).

    python _dev/blindsolve.py export week_00_*/quiz/questions.toml blind.md
        → stems and options only, for an independent solver who never sees answers or explanations
    python _dev/blindsolve.py compare week_00_*/quiz/questions.toml answers.json
        → lists every question where the solver's answer differs from the bank (exit 1 if any)
answers.json: {"w00-q01": ["B"], "w00-q02": ["A", "D"], …}
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import quizlib  # noqa: E402
from _harness.awslib.safety import force_utf8  # noqa: E402


def export(bank: Path, out: Path) -> int:
    lines = ["# Blind solve", "", "Reply with JSON: {\"<id>\": [\"<letter>\", …], …} — one entry per question.", ""]
    for q in quizlib.load_bank(bank):
        lines += [f"## {q.id}", "", q.stem, ""]
        lines += [f"{quizlib.LETTERS[i]}. {option}" for i, option in enumerate(q.options)]
        lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")
    return 0


def compare(bank: Path, answers_path: Path) -> int:
    answers = json.loads(answers_path.read_text(encoding="utf-8"))
    differ = []
    for q in quizlib.load_bank(bank):
        given = sorted(answers.get(q.id, []))
        if given != sorted(q.answer):
            differ.append(f"{q.id}: bank {''.join(sorted(q.answer))} · solver {''.join(given) or '—'}")
    for line in differ:
        print(line)
    print(f"{len(differ)} disagreement(s) out of {len(answers)} answered")
    return 1 if differ else 0


if __name__ == "__main__":
    force_utf8()
    if len(sys.argv) == 4 and sys.argv[1] == "export":
        sys.exit(export(Path(sys.argv[2]), Path(sys.argv[3])))
    if len(sys.argv) == 4 and sys.argv[1] == "compare":
        sys.exit(compare(Path(sys.argv[2]), Path(sys.argv[3])))
    print(__doc__)
    sys.exit(2)

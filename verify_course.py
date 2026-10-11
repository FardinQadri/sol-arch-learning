"""verify_course.py — maintainer checks for the AWS SAA course (spec §8).

    python verify_course.py                  every week, every milestone, all banks, currency
    python verify_course.py --week 0         one week (drills, mutants, notes, demos, README, quiz, lab)
    python verify_course.py --milestone 1    one milestone
    python verify_course.py --banks          question banks only (weekly + mock), incl. near-duplicates
    python verify_course.py --coverage       also write COVERAGE.md (--strict enforces spec §8 thresholds)
    python verify_course.py --self-test      the maintainer tests in _dev/tests
    python verify_course.py --root PATH      check another course folder (used by _dev/tests)

Exit code: 0 every check passed · 1 some check failed · 2 bad arguments.
"""
from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _harness import labclean, quizlib  # noqa: E402
from _harness.awsdrill import JSON_MARKER as DRILL_MARKER  # noqa: E402
from _harness.awslib.safety import force_utf8  # noqa: E402

CONCEPT_MAX_LINES = 350
NOTES_RANGE = (4, 6)
DEMOS_RANGE = (1, 3)
DRILLS_RANGE = (3, 10)   # the fake course in _dev/tests has 3 drills; real weeks have 8–10 (checked by week plans)
DRILL_SECONDS = 60
README_HEADINGS = ("## Goals", "## Your week", "## Exam tasks covered", "## Service comparison", "## Interview questions")
NOTE_PARTS = ("## Exam traps", "## Cost angle")
CLEAN_ENV_DROP = ("PYTHONIOENCODING", "PYTHONUTF8")
STRICT_MIN = {"notes": 1, "drills": 1, "questions": 12}


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


class VerifyError(Exception):
    """A tool did not print the machine-readable line we expected."""


def clean_env() -> dict:
    return {k: v for k, v in os.environ.items() if k not in CLEAN_ENV_DROP}


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(f"_verify_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses in the loaded file need it registered
    spec.loader.exec_module(module)
    return module


def marker_json(proc, marker: str) -> dict:
    for line in reversed(proc.stdout.splitlines()):
        if line.startswith(marker):
            return json.loads(line[len(marker):])
    raise VerifyError(f"no {marker.strip()} line (exit {proc.returncode}): {proc.stderr[-1200:]}")


def run_drills(py: str, exercises: Path, *extra: str) -> dict:
    proc = subprocess.run([py, str(exercises), *extra, "--json"], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=exercises.parent, env=clean_env(), timeout=900)
    return marker_json(proc, DRILL_MARKER)


def week_number(week_dir: Path) -> int:
    return int(re.match(r"week_(\d\d)_", week_dir.name).group(1))


def _all_tests(report):
    return [(drill, test, outcome) for drill, info in report["drills"].items() for test, outcome in info["tests"].items()]


# ── one week ────────────────────────────────────────────────────────


def verify_week(root: Path, week_dir: Path, py: str) -> list:
    checks = verify_drills(root, week_dir, py)
    checks += verify_concepts(week_dir, py)
    checks += verify_readme(week_dir)
    checks += verify_quiz(root, week_dir)
    checks += verify_lab(week_dir)
    return checks


def verify_drills(root: Path, week_dir: Path, py: str) -> list:
    exercises = week_dir / "practice" / "exercises.py"
    if not exercises.exists() or not (week_dir / "practice" / "solutions.py").exists():
        return [Check("practice/exercises.py and solutions.py exist", False)]
    try:
        stubs = run_drills(py, exercises)
        started = time.perf_counter()
        solved = run_drills(py, exercises, "--solutions")
        seconds = time.perf_counter() - started
    except (VerifyError, subprocess.TimeoutExpired) as exc:
        return [Check("drills run", False, str(exc))]
    green_on_stub = [f"{d}.{t}" for d, t, o in _all_tests(stubs) if o == "pass"]
    red_on_solution = [f"{d}.{t}={o}" for d, t, o in _all_tests(solved) if o != "pass"]
    without_tests = [d for d, info in solved["drills"].items() if not info["tests"]]
    stars = sum(1 for info in solved["drills"].values() if info["star"])
    bad_tasks = [d for d, info in solved["drills"].items()
                 if not info["tasks"] or any(t not in quizlib.TASKS for t in info["tasks"])]
    count = len(solved["drills"])
    checks = [
        Check("every test fails on the stubs", not green_on_stub, ", ".join(green_on_stub)),
        Check("every test passes with --solutions", not red_on_solution, ", ".join(red_on_solution)),
        Check("every drill has tests", not without_tests, ", ".join(without_tests)),
        Check("at least 3 ★ drills", stars >= 3, f"{stars} ★"),
        Check("every drill names valid exam tasks", not bad_tasks, ", ".join(bad_tasks)),
        Check(f"{DRILLS_RANGE[0]}–{DRILLS_RANGE[1]} drills", DRILLS_RANGE[0] <= count <= DRILLS_RANGE[1], f"{count} drills"),
        Check(f"solutions run in under {DRILL_SECONDS} s", seconds < DRILL_SECONDS, f"{seconds:.0f} s"),
    ]
    return checks + verify_week_mutants(root, week_number(week_dir), exercises, solved, py)


def verify_week_mutants(root: Path, nn: int, exercises: Path, solved: dict, py: str) -> list:
    path = root / "_dev" / "mutants" / f"week{nn:02d}.py"
    if not path.exists():
        return [Check(f"_dev/mutants/week{nn:02d}.py exists", False)]
    mutants = load_module(path).MUTANTS
    missing = sorted(set(solved["drills"]) - {f"Ex{m['drill']:02d}" for m in mutants})
    checks = [Check("every drill has a mutant", not missing, ", ".join(missing))]
    for mutant in mutants:
        name = f"Ex{mutant['drill']:02d}"
        try:
            report = run_drills(py, exercises, "--solutions", "--mutant", f"{path}#{mutant['id']}", str(mutant["drill"]))
            outcomes = report["drills"].get(name, {}).get("tests", {})
            caught, detail = any(o != "pass" for o in outcomes.values()), "every test still passes"
        except (VerifyError, subprocess.TimeoutExpired) as exc:
            caught, detail = False, f"the mutant did not run: {exc}"
        checks.append(Check(f"mutant {name}:{mutant['id']} is caught", caught, "" if caught else detail))
    return checks


def _note_tasks(text: str) -> list[str]:
    for line in text.splitlines()[:5]:
        if line.startswith("Exam tasks:"):
            return [t.strip() for t in line.split(":", 1)[1].split(",") if t.strip()]
    return []


def verify_concepts(week_dir: Path, py: str) -> list:
    notes = sorted((week_dir / "concepts").glob("[0-9][0-9]_*.md"))
    demos = sorted((week_dir / "concepts").glob("demo_*.py"))
    checks = [Check(f"{NOTES_RANGE[0]}–{NOTES_RANGE[1]} concept notes", NOTES_RANGE[0] <= len(notes) <= NOTES_RANGE[1], f"found {len(notes)}"),
              Check(f"{DEMOS_RANGE[0]}–{DEMOS_RANGE[1]} demos", DEMOS_RANGE[0] <= len(demos) <= DEMOS_RANGE[1], f"found {len(demos)}")]
    for path in notes:
        text = path.read_text(encoding="utf-8")
        lines = len(text.splitlines())
        tasks = _note_tasks(text)
        missing = [part for part in NOTE_PARTS if part not in text]
        if not tasks or any(t not in quizlib.TASKS for t in tasks):
            missing.append("an 'Exam tasks: x.y, …' line with valid tasks in the first 5 lines")
        if not re.search(r"now do drills?\b", text.lower()):
            missing.append("a 'Now do drill…' line")
        checks.append(Check(f"concepts/{path.name} is short (≤ {CONCEPT_MAX_LINES} lines)", lines <= CONCEPT_MAX_LINES, f"{lines} lines"))
        checks.append(Check(f"concepts/{path.name} has the required parts", not missing, "; ".join(missing)))
    for path in demos:
        try:
            proc = subprocess.run([py, str(path)], capture_output=True, cwd=path.parent, env=clean_env(), timeout=180)
            ok, detail = proc.returncode == 0, proc.stderr.decode("utf-8", "replace")[-800:]
        except subprocess.TimeoutExpired:
            ok, detail = False, "timed out after 180 s"
        checks.append(Check(f"concepts/{path.name} runs with piped output", ok, "" if ok else detail))
    return checks


def verify_readme(week_dir: Path) -> list:
    path = week_dir / "README.md"
    if not path.exists():
        return [Check("README.md exists", False)]
    text = path.read_text(encoding="utf-8")
    missing = [h for h in README_HEADINGS if h not in text]
    return [Check("README.md has the required headings", not missing, ", ".join(missing))]


def bank_size(week_dir: Path) -> int:
    return 15 if week_number(week_dir) == 0 else 30


def verify_quiz(root: Path, week_dir: Path) -> list:
    path = week_dir / "quiz" / "questions.toml"
    if not path.exists():
        return [Check("quiz/questions.toml exists", False)]
    try:
        questions = quizlib.load_bank(path, root)
    except quizlib.BankError as exc:
        return [Check("quiz/questions.toml loads", False, str(exc)[-1500:])]
    wrong_week = [q.id for q in questions if not q.id.startswith(f"w{week_number(week_dir):02d}-")]
    problems = quizlib.bank_problems(questions, bank_size(week_dir))
    return [Check("quiz/questions.toml loads", True),
            Check("quiz ids carry this week's number", not wrong_week, ", ".join(wrong_week)),
            Check("quiz/questions.toml follows the bank rules", not problems, "; ".join(problems))]


def verify_lab(week_dir: Path) -> list:
    lab, cleanup = week_dir / "lab" / "LAB.md", week_dir / "lab" / "cleanup.py"
    if not lab.exists() or not cleanup.exists():
        return [Check("lab/LAB.md and lab/cleanup.py exist", False)]
    text = lab.read_text(encoding="utf-8")
    match = re.search(r"main\(kinds=(\[.*?\])", cleanup.read_text(encoding="utf-8"), re.DOTALL)
    kinds = ast.literal_eval(match.group(1)) if match else []
    unknown = [k for k in kinds if k not in labclean.FINDERS]
    return [Check("lab/LAB.md tells the learner to run cleanup.py --yes", "cleanup.py" in text and "--yes" in text),
            Check("lab/cleanup.py uses known resource kinds", bool(kinds) and not unknown, ", ".join(unknown) or "no kinds found")]


# ── across the course ───────────────────────────────────────────────


def all_banks(root: Path) -> list[Path]:
    return sorted(root.glob("week_[0-9][0-9]_*/quiz/questions.toml")) + sorted(root.glob("exam_prep/mock_exams/mock_*.toml"))


def verify_banks(root: Path) -> list:
    questions, checks = [], []
    for path in all_banks(root):
        try:
            questions += quizlib.load_bank(path, root)
        except quizlib.BankError as exc:
            checks.append(Check(f"{path.relative_to(root)} loads", False, str(exc)[-800:]))
    mocks = sorted(root.glob("exam_prep/mock_exams/mock_*.toml"))
    if mocks:
        mock_exam = load_module(root / "exam_prep" / "mock_exam.py")
        for path in mocks:
            try:
                problems = mock_exam.mock_problems(quizlib.load_bank(path, root))
            except quizlib.BankError:
                continue
            checks.append(Check(f"{path.relative_to(root)} follows the mock rules", not problems, "; ".join(problems)))
    ids = [q.id for q in questions]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    checks.append(Check("question ids are unique across banks", not dupes, ", ".join(dupes)))
    pairs = quizlib.near_duplicates(questions)
    checks.append(Check("no near-duplicate questions across banks", not pairs,
                        ", ".join(f"{a}~{b} ({r})" for a, b, r in pairs[:20])))
    return checks


def verify_currency(root: Path) -> list:
    hits = []
    patterns = ("week_*/**/*.md", "course_project/**/*.md", "exam_prep/*.md", "README.md", "COURSE_FLOW.md")
    for pattern in patterns:
        for path in sorted(root.glob(pattern)):
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if "retired" in line.lower():
                    continue
                hits += [f"{path.relative_to(root)}:{lineno} ({name})" for name in quizlib.retired_hits(line)]
    return [Check("no retired services taught as current", not hits, "; ".join(hits))]


def _drill_tasks(exercises: Path) -> list[list[str]]:
    tree = ast.parse(exercises.read_text(encoding="utf-8"))
    found = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and re.fullmatch(r"Ex\d\d", node.name):
            for stmt in node.body:
                if isinstance(stmt, ast.Assign) and any(getattr(t, "id", None) == "tasks" for t in stmt.targets):
                    found.append(list(ast.literal_eval(stmt.value)))
    return found


def coverage(root: Path) -> dict:
    table = {task: {"title": title, "notes": 0, "drills": 0, "questions": 0} for task, title in quizlib.TASKS.items()}
    for note in root.glob("week_[0-9][0-9]_*/concepts/[0-9][0-9]_*.md"):
        for task in _note_tasks(note.read_text(encoding="utf-8")):
            if task in table:
                table[task]["notes"] += 1
    for exercises in root.glob("week_[0-9][0-9]_*/practice/exercises.py"):
        for tasks in _drill_tasks(exercises):
            for task in tasks:
                if task in table:
                    table[task]["drills"] += 1
    for path in all_banks(root):
        try:
            for q in quizlib.load_bank(path):
                table[q.task]["questions"] += 1
        except quizlib.BankError:
            pass
    return table


def write_coverage(root: Path, strict: bool) -> list:
    table = coverage(root)
    lines = ["# Exam coverage", "", "Generated by `python verify_course.py --coverage`. Counts across every week built so far.", "",
             "| Task | Title | Concept notes | Drills | Questions |", "|---|---|---|---|---|"]
    for task, row in table.items():
        lines.append(f"| {task} | {row['title']} | {row['notes']} | {row['drills']} | {row['questions']} |")
    (root / "COVERAGE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not strict:
        return []
    short = [f"{t} ({', '.join(k for k, m in STRICT_MIN.items() if row[k] < m)})"
             for t, row in table.items() if any(row[k] < m for k, m in STRICT_MIN.items())]
    return [Check("every task has ≥ 1 note, ≥ 1 drill, ≥ 12 questions", not short, "; ".join(short))]


def verify_self_test(root: Path, py: str) -> list:
    proc = subprocess.run([py, "-m", "pytest", "_dev/tests", "-q"], cwd=root, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=clean_env(), timeout=1800)
    tail = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else proc.stderr[-400:]
    return [Check("_dev/tests pass", proc.returncode == 0, tail)]


MILESTONE_MARKER = "MILESTONE_JSON "
IGNORE = shutil.ignore_patterns("__pycache__", ".pytest_cache", ".venv", "*.pyc")


def start_all(py: str, cp: Path, repo: Path, n: int) -> None:
    for k in range(1, n + 1):
        proc = subprocess.run([py, str(cp / "tools" / "start_milestone.py"), str(k), "--repo", str(repo)],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", env=clean_env(), timeout=120)
        if proc.returncode != 0:
            raise VerifyError(f"start_milestone.py {k} failed: {proc.stdout}{proc.stderr}")


def run_milestone(py: str, repo: Path, n: int) -> dict:
    proc = subprocess.run([py, "run_milestone.py", str(n), "--json"], cwd=repo, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", env=clean_env(), timeout=1800)
    return marker_json(proc, MILESTONE_MARKER)


def red_steps(report: dict, milestone=None) -> list:
    return [step for step, info in sorted(report["steps"].items())
            if not info["green"] and (milestone is None or step.startswith(f"M{milestone:02d}."))]


def apply_edits(repo: Path, mutant: dict) -> list:
    """A milestone mutant: {"id", "edits": {relpath: [[old, new], …]}, "delete": [relpath, …] (optional)}."""
    problems = []
    for rel, pairs in mutant.get("edits", {}).items():
        path = repo / rel
        text = path.read_text(encoding="utf-8")
        for old, new in pairs:
            found = text.count(old)
            if found != 1:
                problems.append(f"{rel}: expected 1 match of {old[:50]!r}, found {found}")
            else:
                text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")
    for rel in mutant.get("delete", []):
        (repo / rel).unlink()
    return problems


def _expect(py, cp, repo, n, name, want_red, only=None) -> Check:
    try:
        start_all(py, cp, repo, n)
        red = red_steps(run_milestone(py, repo, n), only)
    except (VerifyError, subprocess.TimeoutExpired) as exc:
        return Check(name, False, str(exc))
    if want_red:
        return Check(name, bool(red), "every step is green")
    return Check(name, not red, "red: " + ", ".join(red))


def verify_milestone(root: Path, n: int, py: str) -> list:
    cp = root / "course_project"
    snapshot = cp / "solutions" / f"m{n:02d}"
    checks = []
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        tmp = Path(tmp)
        repo = tmp / "solution repo"  # the space is deliberate: learners' paths have them
        shutil.copytree(snapshot, repo, ignore=IGNORE)
        checks.append(_expect(py, cp, repo, n, f"solutions/m{n:02d} passes run_milestone.py {n}", want_red=False))

        start = tmp / "starting repo"
        if n == 1:
            start.mkdir()
        else:
            shutil.copytree(cp / "solutions" / f"m{n - 1:02d}", start, ignore=IGNORE)
        checks.append(_expect(py, cp, start, n, f"the starting state fails M{n:02d}", want_red=True, only=n))

        lint_bad = []
        for template in sorted((snapshot / "infra").glob("*.yaml")) if (snapshot / "infra").is_dir() else []:
            from _harness.awslib import cfn
            errors = cfn.errors_only(cfn.lint_template(template))
            lint_bad += [f"{template.name}:{e['line']} {e['rule']}" for e in errors]
        checks.append(Check(f"solutions/m{n:02d} templates are cfn-lint clean", not lint_bad, ", ".join(lint_bad)))

        path = root / "_dev" / "mutants" / f"m{n:02d}.py"
        mutants = load_module(path).MUTANTS if path.exists() else []
        checks.append(Check(f"_dev/mutants/m{n:02d}.py has mutants", bool(mutants)))
        for i, mutant in enumerate(mutants):
            repo = tmp / f"mutant {i}"
            shutil.copytree(snapshot, repo, ignore=IGNORE)
            problems = apply_edits(repo, mutant)
            if problems:
                checks.append(Check(f"mutant {mutant['id']} applies cleanly", False, "; ".join(problems)))
                continue
            checks.append(_expect(py, cp, repo, n, f"mutant {mutant['id']} is caught", want_red=True))
    return checks


def print_section(title: str, checks: list) -> None:
    print(f"\n== {title}")
    for check in checks:
        mark = "✔" if check.ok else "✘"
        print(f"  {mark} {check.name}" + (f" — {check.detail}" if check.detail and not check.ok else ""))


def main(argv=None) -> int:
    force_utf8()
    parser = argparse.ArgumentParser(description="Maintainer checks for the AWS SAA course.")
    parser.add_argument("--week", type=int)
    parser.add_argument("--milestone", type=int)
    parser.add_argument("--banks", action="store_true")
    parser.add_argument("--coverage", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args(argv)
    root, py = args.root.resolve(), sys.executable

    weeks = sorted(root.glob("week_[0-9][0-9]_*"))
    solutions = root / "course_project" / "solutions"
    milestones = sorted(int(p.name[1:]) for p in solutions.glob("m[0-9][0-9]")) if solutions.is_dir() else []
    only = args.week is not None or args.milestone is not None or args.banks or args.self_test
    if args.week is not None:
        weeks = [w for w in weeks if week_number(w) == args.week]
        if not weeks:
            print(f"There is no week_{args.week:02d}_* folder in {root}.")
            return 2
    elif only:
        weeks = []
    if args.milestone is not None:
        if args.milestone not in milestones:
            print(f"There is no course_project/solutions/m{args.milestone:02d} in {root}.")
            return 2
        milestones = [args.milestone]
    elif only:
        milestones = []

    sections = []
    if args.self_test:
        sections.append(("maintainer tests", verify_self_test(root, py)))
    sections += [(week.name, verify_week(root, week, py)) for week in weeks]
    sections += [(f"milestone M{n:02d}", verify_milestone(root, n, py)) for n in milestones]
    if not only or args.banks:
        sections.append(("question banks", verify_banks(root)))
        sections.append(("content currency", verify_currency(root)))
    if args.coverage:
        sections.append(("coverage (COVERAGE.md written)", write_coverage(root, args.strict)))

    total = failures = 0
    for title, checks in sections:
        print_section(title, checks)
        total += len(checks)
        failures += sum(not c.ok for c in checks)
    print(f"\n{total - failures}/{total} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

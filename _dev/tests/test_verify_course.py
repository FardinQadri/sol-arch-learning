import importlib.util
import shutil
import sys
import textwrap
from pathlib import Path

import pytest

from bankgen import balanced_raws, toml_bank

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
spec = importlib.util.spec_from_file_location("verify_course", ROOT / "verify_course.py")
vc = importlib.util.module_from_spec(spec)
sys.modules["verify_course"] = vc  # dataclasses need the module registered
spec.loader.exec_module(vc)

EXERCISES = '''
import pathlib, sys
sys.path.insert(0, {root!r})
from _harness.awsdrill import Drill, run

def double(x):
    raise NotImplementedError

def triple(x):
    raise NotImplementedError

def square(x):
    raise NotImplementedError

class Ex01(Drill):
    """Double ★"""
    tasks = ("3.2",)
    def test_double(self):
        self.assertEqual(double(4), 8)

class Ex02(Drill):
    """Triple ★"""
    tasks = ("4.2",)
    def test_triple(self):
        self.assertEqual(triple(2), 6)

class Ex03(Drill):
    """Square ★"""
    tasks = ("2.2",)
    def test_square(self):
        self.assertEqual(square(3), 9)

if __name__ == "__main__":
    run()
'''
SOLUTIONS = "def double(x):\n    return 2 * x\n\ndef triple(x):\n    return 3 * x\n\ndef square(x):\n    return x * x\n"
MUTANTS = '''MUTANTS = [
    {"id": "plus", "drill": 1, "code": "def double(x):\\n    return x + 2\\n"},
    {"id": "off-by-one", "drill": 2, "code": "def triple(x):\\n    return 3 * x + 1\\n"},
    {"id": "times3", "drill": 3, "code": "def square(x):\\n    return 3 * x + 1\\n"},
]
'''
NOTE = """Exam tasks: 3.2, 4.2

# Note {n}

## What it is
Text.

## Exam traps
- A trap.

## Cost angle
Cheap.

Now do drills 01–03.
"""
README = """# Week 00

## Goals
## Your week
## Exam tasks covered
## Service comparison
## Interview questions
"""
DEMO = "import sys\nsys.stdout.reconfigure(encoding='utf-8')\nprint('✔ demo ran')\n"
LAB = "# Lab\n\nWhen you finish, run `python lab/cleanup.py` and then `python lab/cleanup.py --yes`.\n"
CLEANUP = ("import pathlib, sys\nsys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))\n"
           "from _harness.labclean import main\nif __name__ == '__main__':\n    sys.exit(main(kinds=['s3_buckets']))\n")


def make_course(tmp_path) -> Path:
    course = tmp_path / "course"
    week = course / "week_00_sample"
    for sub in ("concepts", "practice", "quiz", "lab"):
        (week / sub).mkdir(parents=True)
    (week / "practice" / "exercises.py").write_text(EXERCISES.format(root=str(ROOT)), encoding="utf-8")
    (week / "practice" / "solutions.py").write_text(SOLUTIONS, encoding="utf-8")
    for n in range(1, 5):
        (week / "concepts" / f"0{n}_note.md").write_text(NOTE.format(n=n), encoding="utf-8")
    (week / "concepts" / "demo_sample.py").write_text(DEMO, encoding="utf-8")
    (week / "README.md").write_text(README, encoding="utf-8")
    raws = balanced_raws(15, multi=2, week=0, ref="week_00_sample/concepts/01_note.md")
    (week / "quiz" / "questions.toml").write_text(toml_bank(raws), encoding="utf-8")
    (week / "lab" / "LAB.md").write_text(LAB, encoding="utf-8")
    (week / "lab" / "cleanup.py").write_text(CLEANUP, encoding="utf-8")
    (course / "_dev" / "mutants").mkdir(parents=True)
    (course / "_dev" / "mutants" / "week00.py").write_text(MUTANTS, encoding="utf-8")
    return course


def failing(checks):
    return {c.name: c.detail for c in checks if not c.ok}


def week_checks(course):
    return vc.verify_week(course, course / "week_00_sample", PY)


def test_good_week_passes(tmp_path):
    course = make_course(tmp_path)
    assert failing(week_checks(course)) == {}


def test_stub_that_passes_is_reported(tmp_path):
    course = make_course(tmp_path)
    path = course / "week_00_sample" / "practice" / "exercises.py"
    path.write_text(path.read_text(encoding="utf-8").replace("def double(x):\n    raise NotImplementedError",
                                                             "def double(x):\n    return 2 * x"), encoding="utf-8")
    assert "every test fails on the stubs" in failing(week_checks(course))


def test_uncaught_and_missing_mutants(tmp_path):
    course = make_course(tmp_path)
    (course / "_dev" / "mutants" / "week00.py").write_text(
        'MUTANTS = [{"id": "same", "drill": 1, "code": "def double(x):\\n    return x * 2\\n"}]\n', encoding="utf-8")
    bad = failing(week_checks(course))
    assert "mutant Ex01:same is caught" in bad and "every drill has a mutant" in bad


def test_too_few_stars_and_bad_tasks(tmp_path):
    course = make_course(tmp_path)
    path = course / "week_00_sample" / "practice" / "exercises.py"
    text = path.read_text(encoding="utf-8").replace('"""Square ★"""', '"""Square"""').replace('("2.2",)', '("9.9",)')
    path.write_text(text, encoding="utf-8")
    bad = failing(week_checks(course))
    assert "at least 3 ★ drills" in bad and "every drill names valid exam tasks" in bad


def test_concept_note_rules(tmp_path):
    course = make_course(tmp_path)
    note = course / "week_00_sample" / "concepts" / "02_note.md"
    note.write_text(NOTE.format(n=2).replace("## Exam traps", "## Traps").replace("Exam tasks: 3.2, 4.2", "Tasks: 3.2"),
                    encoding="utf-8")
    bad = failing(week_checks(course))
    assert "concepts/02_note.md has the required parts" in bad


def test_crashing_demo_is_reported(tmp_path):
    course = make_course(tmp_path)
    (course / "week_00_sample" / "concepts" / "demo_sample.py").write_text("raise SystemExit(3)\n", encoding="utf-8")
    assert "concepts/demo_sample.py runs with piped output" in failing(week_checks(course))


def test_bank_size_and_lab_kinds(tmp_path):
    course = make_course(tmp_path)
    raws = balanced_raws(14, multi=2, week=0, ref="week_00_sample/concepts/01_note.md")
    (course / "week_00_sample" / "quiz" / "questions.toml").write_text(toml_bank(raws), encoding="utf-8")
    (course / "week_00_sample" / "lab" / "cleanup.py").write_text(CLEANUP.replace("s3_buckets", "rockets"), encoding="utf-8")
    bad = failing(week_checks(course))
    assert "quiz/questions.toml follows the bank rules" in bad and "expected 15" in bad["quiz/questions.toml follows the bank rules"]
    assert "lab/cleanup.py uses known resource kinds" in bad


def test_currency_flags_retired_names(tmp_path):
    course = make_course(tmp_path)
    note = course / "week_00_sample" / "concepts" / "03_note.md"
    note.write_text(NOTE.format(n=3) + "\nUse Amazon QLDB for ledgers.\nAmazon QLDB was retired in 2025.\n", encoding="utf-8")
    bad = failing(vc.verify_currency(course))
    assert "03_note.md:" in bad["no retired services taught as current"]
    assert bad["no retired services taught as current"].count("03_note.md") == 1


def test_banks_find_near_duplicates_across_weeks(tmp_path):
    course = make_course(tmp_path)
    other = course / "week_01_copy" / "quiz"
    other.mkdir(parents=True)
    raws = balanced_raws(15, multi=2, week=1, ref="week_00_sample/concepts/01_note.md")
    (other / "questions.toml").write_text(toml_bank(raws), encoding="utf-8")
    assert "no near-duplicate questions across banks" in failing(vc.verify_banks(course))


def test_coverage_file(tmp_path):
    course = make_course(tmp_path)
    table = vc.coverage(course)
    assert table["3.2"]["notes"] == 4 and table["3.2"]["drills"] == 1 and table["1.1"]["drills"] == 0
    assert vc.write_coverage(course, strict=False) == []
    assert "| 3.2 |" in (course / "COVERAGE.md").read_text(encoding="utf-8")
    assert failing(vc.write_coverage(course, strict=True))


def test_main_unknown_week(tmp_path, capsys):
    course = make_course(tmp_path)
    assert vc.main(["--root", str(course), "--week", "7"]) == 2
    assert "There is no week_07_* folder" in capsys.readouterr().out

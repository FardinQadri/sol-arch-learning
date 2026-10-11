"""run_milestone.py — run the course's milestone tests (cumulative) and show progress per step.

    python run_milestone.py 3          runs tests/m01 … tests/m03 and shows which steps are green
    python run_milestone.py 3 --json   (course tools) also prints one MILESTONE_JSON line

Copied into your shortly-infra repo by the course's start_milestone.py. It belongs to the course and
is overwritten each time you start a milestone — don't edit it. Run it with the course venv's python.
Exit code: 0 every step green · 1 some step red · 2 a milestone's tests are missing.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MARKER = "MILESTONE_JSON "
REPO = Path(__file__).resolve().parent
STEP_FILE = re.compile(r"test_m(\d\d)_(\d+)_(\w+)\.py$")


def force_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def step_of(nodeid: str):
    """'tests/m01/test_m01_4_deployer.py::test_x' → ('M01.4', 'deployer'); None if not a step file."""
    match = STEP_FILE.search(nodeid.split("::")[0])
    if not match:
        return None
    return f"M{match.group(1)}.{int(match.group(2))}", match.group(3)


def short_reason(report) -> str:
    crash = getattr(report.longrepr, "reprcrash", None)
    if crash is not None and crash.message:
        text = crash.message.strip().splitlines()[0]
    else:
        lines = [line.strip() for line in str(report.longrepr).splitlines() if line.strip()]
        text = lines[-1] if lines else "failed"
    return re.sub(r"^(E\s+|Failed: )", "", text)[:200]


class StepCollector:
    """pytest plugin: records every test's outcome and every file that failed to import."""

    def __init__(self):
        self.outcomes, self.reasons, self.broken = {}, {}, {}

    def pytest_collectreport(self, report):
        if report.failed:
            self.broken[report.nodeid] = short_reason(report)

    def pytest_runtest_logreport(self, report):
        if report.failed:
            self.outcomes[report.nodeid] = "fail"
            self.reasons.setdefault(report.nodeid, short_reason(report))
        elif report.skipped:
            self.outcomes.setdefault(report.nodeid, "skip")
        elif report.when == "call":
            self.outcomes.setdefault(report.nodeid, "pass")


def summarize(collector: StepCollector, test_dirs: list):
    steps = {}
    for folder in test_dirs:
        for path in sorted(folder.glob("test_m*.py")):
            found = step_of(path.name)
            if found:
                steps[found[0]] = {"name": found[1], "tests": {}, "reason": ""}
    for nodeid, outcome in collector.outcomes.items():
        found = step_of(nodeid)
        if found and found[0] in steps:
            test_name = nodeid.split("::", 1)[-1]
            steps[found[0]]["tests"][test_name] = outcome
            if outcome == "fail" and not steps[found[0]]["reason"]:
                steps[found[0]]["reason"] = f"{test_name}: {collector.reasons.get(nodeid, '')}"
    for nodeid, reason in collector.broken.items():
        found = step_of(nodeid)
        if found and found[0] in steps:
            steps[found[0]]["reason"] = f"cannot import the test file: {reason}"
    for info in steps.values():
        info["green"] = (not info["reason"] and bool(info["tests"])
                         and all(o in ("pass", "skip") for o in info["tests"].values()))
        if not info["green"] and not info["reason"]:
            info["reason"] = "no tests ran"
    other_errors = [f"{nodeid}: {reason}" for nodeid, reason in collector.broken.items() if not step_of(nodeid)]
    return steps, other_errors


def _order(step: str):
    milestone, number = step[1:].split(".")
    return int(milestone), int(number)


def main(argv=None) -> int:
    force_utf8()
    parser = argparse.ArgumentParser(description="Run milestone tests (cumulative).")
    parser.add_argument("milestone", type=int)
    parser.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    test_dirs = [REPO / "tests" / f"m{k:02d}" for k in range(1, args.milestone + 1)]
    missing = [d for d in test_dirs if not d.is_dir()]
    if missing:
        k = int(missing[0].name[1:])
        print(f"tests/{missing[0].name} is missing. Copy it in first:\n"
              f"    python <course folder>/course_project/tools/start_milestone.py {k} --repo \"{REPO}\"")
        return 2

    import pytest

    sys.path.insert(0, str(REPO))
    collector = StepCollector()
    pytest.main(["-q", "--tb=short", "-p", "no:cacheprovider", "--continue-on-collection-errors",
                 "--rootdir", str(REPO), *map(str, test_dirs)], plugins=[collector])
    steps, other_errors = summarize(collector, test_dirs)

    print("\n──────── milestone progress ────────")
    for n in range(1, args.milestone + 1):
        mine = {key: info for key, info in steps.items() if key.startswith(f"M{n:02d}.")}
        print(f"M{n:02d}: {sum(i['green'] for i in mine.values())}/{len(mine)} steps green")
        for key in sorted(mine, key=_order):
            info = mine[key]
            print(f"  ✔ {key} {info['name']}" if info["green"] else f"  ✘ {key} {info['name']} — {info['reason']}")
    for error in other_errors:
        print(f"  ! {error}")
    all_green = bool(steps) and all(i["green"] for i in steps.values()) and not other_errors
    print("\nAll green — commit your work." if all_green else "\nFix the first ✘ step, then run again.")
    if args.json:
        print(MARKER + json.dumps({"steps": steps, "errors": other_errors}, ensure_ascii=False))
    return 0 if all_green else 1


if __name__ == "__main__":
    sys.exit(main())

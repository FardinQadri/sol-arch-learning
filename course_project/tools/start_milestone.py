"""start_milestone.py — copy a milestone's tests into your shortly-infra repo.

    python course_project/tools/start_milestone.py 1 --repo ~/code/shortly-infra

Copies (overwriting; these files belong to the course):
    course_project/tests/mNN/              → <repo>/tests/mNN/
    course_project/tools/conftest.py       → <repo>/tests/conftest.py
    course_project/tools/run_milestone.py  → <repo>/run_milestone.py
    _harness/awslib/*.py + prices.toml     → <repo>/tests/_course/   (template, policy and model helpers the tests use:
                                          cfn, policy_eval, network, compute, cost, S3 storage and lifecycle, EBS, DynamoDB, cache and
                                          database models)
    course_project/app/                    → <repo>/app/             (M03 and later: the Shortly app the tests look for)
Exit code: 0 copied · 2 unknown milestone or missing repo folder.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
COURSE_PROJECT = TOOLS.parent
AWSLIB = COURSE_PROJECT.parent / "_harness" / "awslib"
HELPERS = ("__init__.py", "safety.py", "cfn.py", "policy_eval.py", "cidr.py", "netsim.py",
           "ec2types.py", "elb.py", "scaling.py", "purchasing.py", "prices.py", "prices.toml",
           "s3cost.py", "lifecycle.py", "ebs.py", "dynamo.py", "caching.py", "dbmath.py")


def force_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def main(argv=None) -> int:
    force_utf8()
    parser = argparse.ArgumentParser(description="Copy a milestone's tests into your repo.")
    parser.add_argument("milestone", type=int)
    parser.add_argument("--repo", required=True, help="your shortly-infra repo folder")
    args = parser.parse_args(argv)
    n = args.milestone

    source = COURSE_PROJECT / "tests" / f"m{n:02d}"
    if not source.is_dir():
        known = sorted(p.name.upper() for p in (COURSE_PROJECT / "tests").glob("m[0-9][0-9]"))
        print(f"There are no tests for M{n:02d}. Available: {', '.join(known) or 'none yet'}.")
        return 2
    repo = Path(args.repo).expanduser().resolve()
    if not repo.is_dir():
        print(f"{repo} does not exist. Create your repo folder first (see course_project/milestones/M01.md, step 0).")
        return 2

    shutil.copytree(source, repo / "tests" / source.name, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(TOOLS / "conftest.py", repo / "tests" / "conftest.py")
    shutil.copy2(TOOLS / "run_milestone.py", repo / "run_milestone.py")
    helpers = repo / "tests" / "_course"
    helpers.mkdir(parents=True, exist_ok=True)
    for name in HELPERS:
        shutil.copy2(AWSLIB / name, helpers / name)

    app_source = COURSE_PROJECT / "app"
    if n >= 3 and app_source.is_dir():
        shutil.copytree(app_source, repo / "app", dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
        print(f"Copied app/ (the Shortly app your launch template will run) into {repo}")
    print(f"Copied tests/{source.name}/, tests/conftest.py, tests/_course/ and run_milestone.py into {repo}")
    print(f"Instructions:  {COURSE_PROJECT / 'milestones' / f'M{n:02d}.md'}")
    print(f"Progress:      cd \"{repo}\"   then   python run_milestone.py {n}")
    print("Use the course venv's python (it has moto and cfn-lint).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

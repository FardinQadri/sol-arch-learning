"""awsdrill — the drill harness for the AWS SAA course.

A drill file (week_XX_*/practice/exercises.py) looks like:

    import pathlib, sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
    from _harness.awsdrill import Drill, run

    def usable_ips(cidr):                # the learner's stub
        raise NotImplementedError

    class Ex03(Drill):
        '''Usable IPs in a subnet ★'''   # first docstring line = title; ★ = build-the-mechanism
        tasks = ("3.4",)                  # exam task statements this drill covers
        uses_aws = False                  # True → every test runs inside a fresh moto mock_aws()
        def test_slash_24(self): ...

    if __name__ == "__main__":
        run()

Command line (parsed by run()):
    python exercises.py                  every drill
    python exercises.py 4                drill 4 only
    python exercises.py --solutions      the same tests against solutions.py
    python exercises.py --mutant F#ID    (maintainers) inject mutant ID from file F
    python exercises.py --json           also print one AWSDRILL_JSON line (verify_course.py)
    python -m _harness.awsdrill digest SALT VALUE   (maintainers) digest for assertHashed

Contract: tests look learner names up at call time (module globals), so --solutions and
--mutant can swap them in. solutions.py and mutant code run in a namespace that already holds
everything exercises.py defines. A drill that overrides setUp must call super().setUp().
Importing this module forces fake AWS credentials (awslib.safety), so no drill reaches real AWS.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import re
import sys
import textwrap
import unittest
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness.awslib.safety import force_utf8, use_fake_aws_env  # noqa: E402

use_fake_aws_env()

JSON_MARKER = "AWSDRILL_JSON "
MOTO_CONFIG = {"lambda": {"use_docker": False}, "stepfunctions": {"execute_state_machine": True}}
_DRILL_NAME = re.compile(r"^Ex(\d\d)$")


# ── answers that are not readable in the file ───────────────────────


def normalise(value) -> str:
    """Canonical text of an answer: case- and space-insensitive; collections are order-insensitive."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple, set, frozenset)):
        return "|".join(sorted(normalise(v) for v in value))
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return " ".join(str(value).split()).casefold()


def digest(salt: str, value) -> str:
    return hashlib.sha256(f"{salt}:{normalise(value)}".encode("utf-8")).hexdigest()


class FakeClock:
    """A clock you control: clock() returns the current time, clock.advance(s) moves it forward."""

    def __init__(self, start: float = 0.0):
        self.now = float(start)

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class Drill(unittest.TestCase):
    """Base class for drills. Name subclasses Ex01, Ex02, …; the docstring's first line is the
    title shown by run(), and a ★ in it marks a build-the-mechanism drill."""

    maxDiff = None
    longMessage = False
    uses_aws = False
    tasks: tuple = ()

    def setUp(self):
        super().setUp()
        if self.uses_aws:
            from moto import mock_aws

            mock = mock_aws(config=MOTO_CONFIG)
            mock.start()
            self.addCleanup(mock.stop)

    def client(self, service: str, region: str = "us-east-1", **kwargs):
        import boto3

        return boto3.client(service, region_name=region, **kwargs)

    def resource(self, service: str, region: str = "us-east-1"):
        import boto3

        return boto3.resource(service, region_name=region)

    @contextlib.contextmanager
    def assertClientError(self, code: str):
        from botocore.exceptions import ClientError

        try:
            yield
        except ClientError as exc:
            got = exc.response.get("Error", {}).get("Code")
            if got != code:
                self.fail(f"expected AWS error {code}, got {got}")
        else:
            self.fail(f"expected AWS error {code}, but the call succeeded")

    def assertHashed(self, value, salt: str, expected: str, msg: str | None = None):
        if value is None:
            self.fail(msg or "fill in your answer (it is still None)")
        if digest(salt, value) != expected:
            self.fail(msg or f"{value!r} is not the right answer")


# ── swapping in solutions and mutants ───────────────────────────────


def inject_source(module, source: str, filename: str) -> list:
    """Run `source` in a namespace seeded with `module`'s globals, then copy every new or rebound
    name back into `module`. Returns the names that changed."""
    namespace = dict(vars(module))
    before = dict(namespace)
    exec(compile(source, filename, "exec"), namespace)
    changed = []
    for name, value in namespace.items():
        if name.startswith("__"):
            continue
        if name not in before or before[name] is not value:
            setattr(module, name, value)
            changed.append(name)
    return changed


def _load_file_module(path: Path):
    spec = importlib.util.spec_from_file_location(f"_awsdrill_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inject_solutions(module) -> None:
    path = Path(module.__file__).with_name("solutions.py")
    inject_source(module, path.read_text(encoding="utf-8"), str(path))


def inject_mutant(module, spec: str) -> None:
    """spec = "path/to/weekNN.py#mutant-id" (the path may contain ':' on Windows)."""
    file_part, _, mutant_id = spec.rpartition("#")
    for mutant in _load_file_module(Path(file_part)).MUTANTS:
        if mutant["id"] == mutant_id:
            inject_source(module, textwrap.dedent(mutant["code"]), f"<mutant {mutant_id}>")
            return
    raise SystemExit(f"no mutant {mutant_id!r} in {file_part}")


# ── running drills ──────────────────────────────────────────────────


def _describe(err) -> str:
    exc_type, exc, _tb = err
    if exc_type is NotImplementedError:
        return "not implemented yet"
    lines = str(exc).strip().splitlines()
    first = lines[0] if lines else ""
    label = "" if issubclass(exc_type, AssertionError) and first else f"{exc_type.__name__}: "
    return (label + first)[:220]


class _DrillResult(unittest.TestResult):
    """Remembers pass/fail/error per test method; a failing subTest fails its method."""

    def __init__(self):
        super().__init__()
        self.outcomes = {}
        self.messages = {}

    def _record(self, test, outcome, err=None):
        name = test._testMethodName
        if self.outcomes.get(name) in ("fail", "error"):
            return
        self.outcomes[name] = outcome
        if err is not None:
            self.messages[name] = _describe(err)

    def addSuccess(self, test):
        self._record(test, "pass")

    def addFailure(self, test, err):
        self._record(test, "fail", err)

    def addError(self, test, err):
        self._record(test, "error", err)

    def addSkip(self, test, reason):
        self._record(test, "skip")

    def addSubTest(self, test, subtest, err):
        if err is not None:
            self._record(test, "fail" if issubclass(err[0], test.failureException) else "error", err)


def _drills(module):
    found = []
    for name, obj in vars(module).items():
        match = _DRILL_NAME.match(name)
        if match and isinstance(obj, type) and issubclass(obj, unittest.TestCase):
            found.append((int(match.group(1)), obj))
    return sorted(found, key=lambda pair: pair[0])


def run(argv=None) -> None:
    force_utf8()
    parser = argparse.ArgumentParser(description="Run this week's drills.")
    parser.add_argument("drill", nargs="?", type=int, help="run only this drill number")
    parser.add_argument("--solutions", action="store_true", help="check the reference solutions")
    parser.add_argument("--mutant", metavar="FILE#ID", help=argparse.SUPPRESS)
    parser.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    module = sys.modules["__main__"]
    if args.solutions:
        inject_solutions(module)
    if args.mutant:
        inject_mutant(module, args.mutant)

    drills = _drills(module)
    if args.drill is not None:
        drills = [(n, cls) for n, cls in drills if n == args.drill]
        if not drills:
            print(f"There is no drill {args.drill}.")
            sys.exit(2)

    report, passing = {}, 0
    for number, cls in drills:
        result = _DrillResult()
        unittest.defaultTestLoader.loadTestsFromTestCase(cls).run(result)
        title = (cls.__doc__ or cls.__name__).strip().splitlines()[0]
        ok = bool(result.outcomes) and all(o in ("pass", "skip") for o in result.outcomes.values())
        passing += ok
        if ok:
            print(f"✔ Ex{number:02d}  {title}")
        else:
            failed = sorted(n for n, o in result.outcomes.items() if o not in ("pass", "skip"))
            why = f"{failed[0]}: {result.messages.get(failed[0], '')}" if failed else "no tests"
            print(f"✘ Ex{number:02d}  {title} — {why}")
        report[f"Ex{number:02d}"] = {"title": title, "star": "★" in title,
                                     "tasks": list(getattr(cls, "tasks", ())), "tests": result.outcomes}

    suffix = " (solutions)" if args.solutions else ""
    print(f"\n{passing}/{len(drills)} passing{suffix}")
    if args.json:
        print(JSON_MARKER + json.dumps({"drills": report, "passing": passing, "total": len(drills)},
                                       ensure_ascii=False))
    sys.exit(0 if passing == len(drills) else 1)


def _main(argv=None) -> int:
    force_utf8()
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) == 3 and argv[0] == "digest":
        try:
            value = json.loads(argv[2])
        except ValueError:
            value = argv[2]
        print(digest(argv[1], value))
        return 0
    print("usage: python -m _harness.awsdrill digest SALT VALUE")
    return 2


if __name__ == "__main__":
    sys.exit(_main())

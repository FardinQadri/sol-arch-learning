import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

from _harness import awsdrill

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable

SAMPLE = '''
import pathlib, sys
sys.path.insert(0, {root!r})
from _harness.awsdrill import Drill, run

def add(a, b):
    raise NotImplementedError

def left_as_pass(x):
    pass

BUCKET_ANSWER = None

class Ex01(Drill):
    """Add numbers ★"""
    tasks = ("3.2",)
    def test_add(self):
        self.assertEqual(add(2, 3), 5)

class Ex02(Drill):
    """A stub left as pass"""
    tasks = ("1.1",)
    def test_value(self):
        self.assertEqual(left_as_pass(1), 2, "left_as_pass(1) should be 2")

class Ex03(Drill):
    """Buckets in moto"""
    tasks = ("3.1",)
    uses_aws = True
    def test_bucket(self):
        s3 = self.client("s3")
        s3.create_bucket(Bucket="drill-bucket")
        self.assertEqual([b["Name"] for b in s3.list_buckets()["Buckets"]], ["drill-bucket"])
    def test_fresh_mock_each_test(self):
        self.assertEqual(self.client("s3").list_buckets()["Buckets"], [])
    def test_missing_bucket_error(self):
        with self.assertClientError("NoSuchBucket"):
            self.client("s3").get_object(Bucket="nope-bucket", Key="k")

class Ex04(Drill):
    """Hashed answer"""
    tasks = ("2.2",)
    def test_answer(self):
        self.assertHashed(BUCKET_ANSWER, "sample-ex04", {digest!r})

if __name__ == "__main__":
    run()
'''

SOLUTIONS = '''
def add(a, b):
    return a + b

def left_as_pass(x):
    return 2 * x

BUCKET_ANSWER = "S3 Glacier Deep Archive"
'''

MUTANTS = '''
MUTANTS = [{"id": "off-by-one", "drill": 1, "code": """
def add(a, b):
    return a + b + 1
"""}]
'''


def make_sample(tmp_path) -> Path:
    folder = tmp_path / "week sample" / "practice"  # the space is deliberate
    folder.mkdir(parents=True)
    exercises = folder / "exercises.py"
    exercises.write_text(SAMPLE.format(root=str(ROOT), digest=awsdrill.digest("sample-ex04", "s3 glacier  deep archive")),
                         encoding="utf-8")
    (folder / "solutions.py").write_text(SOLUTIONS, encoding="utf-8")
    (tmp_path / "mutants.py").write_text(MUTANTS, encoding="utf-8")
    return exercises


def run_file(path, *args, cwd=None, env=None):
    env = env or {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
    return subprocess.run([PY, str(path), *args], capture_output=True, cwd=cwd or path.parent, env=env, timeout=300)


def report(proc) -> dict:
    out = proc.stdout.decode("utf-8")
    line = [l for l in out.splitlines() if l.startswith(awsdrill.JSON_MARKER)][-1]
    return json.loads(line[len(awsdrill.JSON_MARKER):])


def test_normalise_and_digest():
    assert awsdrill.normalise("  S3   Glacier ") == "s3 glacier"
    assert awsdrill.normalise(True) == "true"
    assert awsdrill.normalise(3.0) == "3"
    assert awsdrill.normalise(["b", "A"]) == "a|b"
    assert awsdrill.digest("x", "Customer") == awsdrill.digest("x", "customer ")
    assert awsdrill.digest("x", "a") != awsdrill.digest("y", "a")


def test_digest_cli():
    proc = subprocess.run([PY, "-m", "_harness.awsdrill", "digest", "salt-1", "Allow"], cwd=ROOT,
                          capture_output=True, text=True, timeout=120)
    assert proc.stdout.strip() == awsdrill.digest("salt-1", "Allow")


def test_stubs_fail_cleanly(tmp_path):
    proc = run_file(make_sample(tmp_path), "--json")
    data = report(proc)
    assert proc.returncode == 1
    assert data["passing"] == 1 and data["total"] == 4  # only the moto drill passes on stubs
    out = proc.stdout.decode("utf-8")
    assert "✘ Ex01  Add numbers ★ — test_add: not implemented yet" in out
    assert "left_as_pass(1) should be 2" in out
    assert "fill in your answer (it is still None)" in out


def test_solutions_pass_and_report_tasks(tmp_path):
    proc = run_file(make_sample(tmp_path), "--solutions", "--json")
    data = report(proc)
    assert proc.returncode == 0 and data["passing"] == 4
    assert data["drills"]["Ex01"] == {"title": "Add numbers ★", "star": True, "tasks": ["3.2"],
                                      "tests": {"test_add": "pass"}}
    assert set(data["drills"]["Ex03"]["tests"].values()) == {"pass"}


def test_mutant_is_caught(tmp_path):
    exercises = make_sample(tmp_path)
    proc = run_file(exercises, "--solutions", "--mutant", f"{tmp_path / 'mutants.py'}#off-by-one", "1", "--json")
    assert report(proc)["drills"]["Ex01"]["tests"]["test_add"] == "fail"


def test_single_drill_and_unknown_drill(tmp_path):
    exercises = make_sample(tmp_path)
    assert list(report(run_file(exercises, "3", "--json"))["drills"]) == ["Ex03"]
    proc = run_file(exercises, "9")
    assert proc.returncode == 2 and "There is no drill 9." in proc.stdout.decode("utf-8")


def test_runs_from_any_working_directory(tmp_path):
    exercises = make_sample(tmp_path)
    for cwd in (ROOT, tmp_path, exercises.parent):
        assert report(run_file(exercises, "--solutions", "--json", cwd=cwd))["passing"] == 4


def test_piped_output_is_utf8(tmp_path):
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
    proc = run_file(make_sample(tmp_path), "--solutions", env=env)
    assert proc.returncode == 0
    assert "✔ Ex01  Add numbers ★" in proc.stdout.decode("utf-8")


def test_mock_stopped_after_error(tmp_path):
    folder = tmp_path / "p"
    folder.mkdir()
    path = folder / "exercises.py"
    path.write_text(textwrap.dedent(f'''
        import sys
        sys.path.insert(0, {str(ROOT)!r})
        from _harness.awsdrill import Drill, run
        class Ex01(Drill):
            """boom"""
            tasks = ("1.1",)
            uses_aws = True
            def test_boom(self):
                self.client("s3").create_bucket(Bucket="leaky-bucket")
                raise RuntimeError("boom")
        class Ex02(Drill):
            """sees a clean account"""
            tasks = ("1.1",)
            uses_aws = True
            def test_clean(self):
                self.assertEqual(self.client("s3").list_buckets()["Buckets"], [])
        if __name__ == "__main__":
            run()
    '''), encoding="utf-8")
    data = report(run_file(path, "--json"))
    assert data["drills"]["Ex01"]["tests"]["test_boom"] == "error"
    assert data["drills"]["Ex02"]["tests"]["test_clean"] == "pass"


def test_fake_clock():
    clock = awsdrill.FakeClock(10)
    clock.advance(2.5)
    assert clock() == 12.5

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
MARKER = "MILESTONE_JSON "


def fake_course(tmp_path) -> Path:
    """A course folder with the real tools and helpers and a two-step milestone M01."""
    course = tmp_path / "course"
    shutil.copytree(ROOT / "course_project" / "tools", course / "course_project" / "tools")
    shutil.copytree(ROOT / "_harness" / "awslib", course / "_harness" / "awslib",
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "course_project" / "app", course / "course_project" / "app", ignore=shutil.ignore_patterns("__pycache__"))
    tests = course / "course_project" / "tests" / "m01"
    tests.mkdir(parents=True)
    (tests / "test_m01_1_readme.py").write_text(
        "def test_readme(repo):\n    assert (repo / 'README.md').exists(), 'add README.md'\n", encoding="utf-8")
    (tests / "test_m01_2_creds.py").write_text(
        "import os\n\ndef test_fake_credentials():\n    assert os.environ['AWS_ACCESS_KEY_ID'] == 'testing'\n"
        "    assert 'AWS_PROFILE' not in os.environ\n", encoding="utf-8")
    return course


def start(course, repo, n=1, env=None):
    return subprocess.run([PY, str(course / "course_project" / "tools" / "start_milestone.py"), str(n), "--repo", str(repo)],
                          capture_output=True, text=True, encoding="utf-8", env=env, timeout=120)


def run(repo, n=1, env=None):
    proc = subprocess.run([PY, "run_milestone.py", str(n), "--json"], cwd=repo, capture_output=True, text=True,
                          encoding="utf-8", env=env, timeout=300)
    line = [l for l in proc.stdout.splitlines() if l.startswith(MARKER)]
    return proc, (json.loads(line[-1][len(MARKER):]) if line else None)


def test_start_copies_tests_conftest_runner_and_helpers(tmp_path):
    course = fake_course(tmp_path)
    repo = tmp_path / "my infra repo"
    repo.mkdir()
    proc = start(course, repo)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    for rel in ("tests/m01/test_m01_1_readme.py", "tests/conftest.py", "run_milestone.py",
                "tests/_course/__init__.py", "tests/_course/cfn.py", "tests/_course/policy_eval.py", "tests/_course/safety.py"):
        assert (repo / rel).exists(), rel
    assert "M01.md" in proc.stdout


def test_start_copies_model_helpers_and_the_app_from_milestone_3(tmp_path):
    course = fake_course(tmp_path)
    for n in (2, 3):
        folder = course / "course_project" / "tests" / f"m0{n}"
        folder.mkdir()
        (folder / f"test_m0{n}_1_x.py").write_text("def test_x():\n    pass\n", encoding="utf-8")
    repo = tmp_path / "repo"
    repo.mkdir()
    proc = start(course, repo, n=2)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert not (repo / "app").exists(), "M02 must not create app/"
    for name in ("ec2types.py", "elb.py", "scaling.py", "purchasing.py", "prices.py", "prices.toml"):
        assert (repo / "tests" / "_course" / name).exists(), name
    for name in ("s3cost.py", "lifecycle.py", "ebs.py", "dynamo.py", "caching.py", "dbmath.py"):
        assert (repo / "tests" / "_course" / name).exists(), name
    proc = start(course, repo, n=3)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (repo / "app" / "app.py").exists() and "app/" in proc.stdout
    (repo / "app" / "app.py").write_text("changed", encoding="utf-8")
    assert start(course, repo, n=3).returncode == 0
    assert "changed" not in (repo / "app" / "app.py").read_text(encoding="utf-8"), "app/ is overwritten"


def test_start_expands_home(tmp_path):
    course = fake_course(tmp_path)
    home = tmp_path / "home"
    (home / "code" / "shortly-infra").mkdir(parents=True)
    env = dict(os.environ, USERPROFILE=str(home), HOME=str(home))
    proc = start(course, "~/code/shortly-infra", env=env)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (home / "code" / "shortly-infra" / "run_milestone.py").exists()


def test_start_unknown_milestone_and_missing_repo(tmp_path):
    course = fake_course(tmp_path)
    proc = start(course, tmp_path, n=7)
    assert proc.returncode == 2 and "There are no tests for M07" in proc.stdout
    proc = start(course, tmp_path / "nope")
    assert proc.returncode == 2 and "does not exist" in proc.stdout


def test_run_reports_steps_and_conftest_forces_fake_credentials(tmp_path):
    course = fake_course(tmp_path)
    repo = tmp_path / "repo"
    repo.mkdir()
    start(course, repo)
    env = dict(os.environ, AWS_PROFILE="work", AWS_ACCESS_KEY_ID="AKIAREALKEY")
    env.pop("PYTHONIOENCODING", None)
    proc, data = run(repo, env=env)
    assert data["steps"]["M01.1"]["green"] is False and "add README.md" in data["steps"]["M01.1"]["reason"]
    assert data["steps"]["M01.2"]["green"] is True   # test_conftest_forces_fake_credentials
    assert "✘ M01.1 readme" in proc.stdout and proc.returncode == 1
    (repo / "README.md").write_text("# shortly-infra\n", encoding="utf-8")
    proc, data = run(repo, env=env)
    assert proc.returncode == 0 and all(s["green"] for s in data["steps"].values())


def test_run_missing_earlier_milestone(tmp_path):
    course = fake_course(tmp_path)
    repo = tmp_path / "repo"
    repo.mkdir()
    start(course, repo)
    proc, _ = run(repo, n=2)
    assert proc.returncode == 2 and "tests/m02 is missing" in proc.stdout


def test_conftest_fixtures_load_render_and_evaluate(tmp_path):
    course = fake_course(tmp_path)
    repo = tmp_path / "repo"
    (repo / "infra").mkdir(parents=True)
    (repo / "README.md").write_text("x", encoding="utf-8")
    (repo / "infra" / "iam.yaml").write_text(
        "AWSTemplateFormatVersion: '2010-09-09'\nParameters:\n  Prefix: {Type: String}\n  Env: {Type: String}\n"
        "Resources:\n  AppRole:\n    Type: AWS::IAM::Role\n    Properties:\n      RoleName: !Sub '${Prefix}-app'\n"
        "      AssumeRolePolicyDocument:\n        Version: '2012-10-17'\n        Statement:\n"
        "          - {Effect: Allow, Principal: {Service: ec2.amazonaws.com}, Action: 'sts:AssumeRole'}\n"
        "      Policies:\n        - PolicyName: app\n          PolicyDocument:\n            Version: '2012-10-17'\n"
        "            Statement:\n              - Effect: Allow\n                Action: sqs:SendMessage\n"
        "                Resource: !Sub 'arn:aws:sqs:${AWS::Region}:${AWS::AccountId}:${Prefix}-clicks'\n",
        encoding="utf-8")
    tests = course / "course_project" / "tests" / "m01"
    (tests / "test_m01_3_fixtures.py").write_text(
        "def test_fixtures(template, lint_errors, role_policies, evaluator, moto_stacks):\n"
        "    assert 'AppRole' in template('iam')['Resources']\n"
        "    assert lint_errors('iam') == []\n"
        "    req = evaluator.Request(principal='arn:aws:iam::111122223333:role/shortly-app', action='sqs:SendMessage',\n"
        "                            resource='arn:aws:sqs:us-east-1:111122223333:shortly-clicks')\n"
        "    assert evaluator.evaluate_policies(role_policies('iam', 'AppRole'), req) == 'Allow'\n"
        "    assert moto_stacks('iam') == 'CREATE_COMPLETE'\n", encoding="utf-8")
    start(course, repo)
    proc, data = run(repo)
    assert data["steps"]["M01.3"]["green"], data["steps"]["M01.3"]["reason"]


def test_verify_milestone_good_starting_and_mutant(tmp_path):
    course = fake_course(tmp_path)
    solution = course / "course_project" / "solutions" / "m01"
    solution.mkdir(parents=True)
    (solution / "README.md").write_text("# shortly-infra\n", encoding="utf-8")
    (course / "_dev" / "mutants").mkdir(parents=True)
    (course / "_dev" / "mutants" / "m01.py").write_text(
        "MUTANTS = []\n", encoding="utf-8")
    spec = importlib.util.spec_from_file_location("verify_course", ROOT / "verify_course.py")
    vc = importlib.util.module_from_spec(spec)
    sys.modules["verify_course"] = vc  # dataclasses need the module registered
    spec.loader.exec_module(vc)
    checks = {c.name: c for c in vc.verify_milestone(course, 1, PY)}
    assert checks["solutions/m01 passes run_milestone.py 1"].ok, checks["solutions/m01 passes run_milestone.py 1"].detail
    assert checks["the starting state fails M01"].ok
    assert not checks["_dev/mutants/m01.py has mutants"].ok
    # a mutant that deletes the README is caught
    (course / "_dev" / "mutants" / "m01.py").write_text(
        'MUTANTS = [{"id": "no-title", "edits": {"README.md": [["# shortly-infra", ""]]}, "delete": ["README.md"]}]\n',
        encoding="utf-8")
    checks = {c.name: c for c in vc.verify_milestone(course, 1, PY)}
    assert checks["mutant no-title is caught"].ok

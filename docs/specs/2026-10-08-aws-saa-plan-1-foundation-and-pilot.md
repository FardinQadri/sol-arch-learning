# AWS SAA Course — Plan 1: Foundation + Pilot (Steps 0–1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the course machinery (venv, drill harness, quiz engine, mock-exam runner, lab-cleanup library, `verify_course.py`, milestone tools, docs of record) and the pilot the learner tries before anything else is built: weeks 00–01 (concept notes, demos, drills, solutions, mutants, quiz, lab) and capstone milestone M01.

**Architecture:** Every week's `practice/exercises.py` is one runnable file of spec + stub + `unittest` tests driven by `_harness/awsdrill.py`; moto's `mock_aws` gives each AWS-backed test a fresh fake AWS, and the harness forces fake credentials so nothing can reach a real account. `_harness/awslib/` holds code shared by drills, milestone tests and tools (template loading/linting, the reference IAM policy evaluator, prices, credential safety). Quiz banks are TOML files read by `_harness/quizlib.py`; `quiz.py` and `exam_prep/mock_exam.py` are thin terminal front-ends. `verify_course.py` proves stubs fail, solutions pass, mutants are caught, banks are valid and milestones behave. The capstone lives in the learner's own repo; `start_milestone.py` copies step tests and course helpers into it and `run_milestone.py` reports per-step progress.

**Tech Stack:** Python 3.14.2 (Windows 11) · moto[all] 5.2.3 · boto3/botocore 1.43.109 · cfn-lint 1.57.2 · pytest 9.1.1 · stdlib `tomllib`, `unittest`, `ipaddress`, `difflib`.

**Spec:** `AWS_SAA_Course_claude/docs/specs/2026-10-08-aws-saa-course-design.md` (approved 2026-10-08). This plan implements spec §6 Step 0 and Step 1 only. Supporting research: `docs/research/2026-10-08-saa-c03-research.md` (exam guide v1.1 verbatim, retired services, Free plan, numbers) and `docs/research/2026-10-08-moto-cfnlint-spike.md` (what moto and cfn-lint do on this machine).

**Execution (learner's choice):** Sonnet implementer subagents write; independent tasks run in parallel (see "Waves"); the main session verifies every task itself — runs the task's commands, reads the files — before accepting it. **Stop after Task 20** and wait for the learner's pilot feedback before any week 02+ plan is written.

## Global Constraints

- **Course root:** `C:\Users\SyedQadri\Downloads\courses\AWS_SAA_Course_claude\` — every path below is relative to it. In Git Bash: `cd /c/Users/SyedQadri/Downloads/courses/AWS_SAA_Course_claude`.
- **Python:** `.venv/Scripts/python.exe` (the course venv). Never `pip install` globally. Never install Docker, WSL, Node or any system package.
- **No git.** Do not `git init` and do not commit — the learner commits at the end ("dont commit yet, we will commit in the end, i will tell u"). Every "commit" step of the usual workflow is skipped.
- **Never real AWS.** No command in this plan may use real credentials or call a real AWS endpoint. Every test and demo runs under moto `mock_aws` with fake credentials set by `_harness/awslib/safety.py`. Labs (`lab/LAB.md`, `lab/cleanup.py`) are written, never run against an account.
- **Windows-first:** every script that prints calls `force_utf8()` (✔/✘/★ must survive piped output under cp1252); drills and tests never touch the network.
- **Pinned versions (from the spike, no WDAC blocks):** moto[all]==5.2.3 · boto3==1.43.109 · botocore==1.43.109 · cfn-lint==1.57.2 · pytest==9.1.1. Anything else comes in as their dependencies.
- **moto facts (spike):** Lambda handler code never runs (test handlers directly) · Step Functions run only with `config={"stepfunctions": {"execute_state_machine": True}}` · CloudFormation silently skips `SNS::Subscription`, `CloudWatch::Alarm`, `SecretsManager::Secret`, `CloudFront::Distribution`, `WAFv2::WebACL` and drops `PublicAccessBlockConfiguration` / `LifecycleConfiguration` on `S3::Bucket` · `set_initial_no_auth_action_count(n)` enforces IAM · ≈ 1 s per moto-backed test · 1,100 `put_object` calls take ≈ 10 s (keep seeded data small).
- **cfn-lint facts (spike + probe):** `cfnlint.decode.decode_str(text) -> (template | None, matches)`; `cfnlint.api.lint(text) -> list[Match]` with `m.rule.id`, `m.linenumber`, `m.message`; ≈ 2 s per lint → always go through the cache in `awslib/cfn.py`.
- **Drill format (spec §4.1):** docstring spec + example + hint + stub, then an `ExNN(Drill)` class. Class docstring's first line = title; `★` in it marks build-the-mechanism (≥ 3 per week). Every drill class sets `tasks = ("x.y", …)` with exam task statements. Tests look learner names up at call time. `solutions.py` defines only learner-implemented names. Predict/decide answers are compared with `assertHashed` or computed by an oracle (moto or `awslib`), never written in clear.
- **Content rules (spec §4.2, §7):** concept notes are Markdown, ≤ 350 lines, start with an `Exam tasks:` line, contain `## Exam traps` and `## Cost angle` headings and a "Now do drill…" line; every number comes from `docs/facts.md`; retired services (spec §7 rule 1) appear only on lines containing the word "retired"; numbers that changed after 2022 are taught at today's value with the old value named once.
- **Quiz rules (spec §4.3):** original questions only; TOML schema exactly as in Task 4; single = 4 options, Select TWO = 5, Select THREE = 6; every option explained; week 00 bank = 15 questions, every other week = 30. The spec's "legacy ≤ 2 % per bank" is applied as at most max(1, 2 % of the bank) — so a 30-question bank may hold one legacy question (week 10 needs one for Snowball Edge).
- **Definition of done (spec §8):** every test fails on the stubs · every test passes with `--solutions` · every drill has ≥ 1 mutant and every mutant is caught · drills run < 60 s · demos exit 0 piped · banks valid · milestone snapshot passes cumulatively, starting state fails, every mutant caught · cleanup library passes its moto safety tests.

## Review Focus

1. **A learner's real AWS credentials** (`AWS_PROFILE`, `AWS_ACCESS_KEY_ID`, a real `~/.aws/credentials`) must never be picked up by a drill, demo, milestone test or `verify_course.py`. Tests: Task 2 `test_fake_env_overrides_real_credentials`, Task 8 `test_conftest_forces_fake_credentials`.
2. **`cleanup.py` in a real account** must change nothing without `--yes`, touch only `saa-course=lab` resources, and keep going when one deletion fails (AccessDenied, already gone). Tests: Task 6 `test_dry_run_deletes_nothing`, `test_only_tagged_resources_deleted`, `test_continues_after_a_failed_delete`.
3. **Piped output on Windows** (stdout cp1252, no `PYTHONIOENCODING`/`PYTHONUTF8`) must not crash on ✔/✘/★ — harness, quiz, mock exam, tools, demos. Tests: Task 2 `test_piped_output_is_utf8`, Task 4 `test_quiz_cli_piped`, Task 5 `test_mock_cli_piped`; `verify_course.py` runs every demo piped.
4. **Quiz input mistakes** — wrong number of letters, letters outside the options, `A, C`, `ca`, blank line, `q` — must re-prompt or quit cleanly, never crash or mark an answer. Tests: Task 4 `test_parse_answer_variants`, `test_session_reprompts_on_bad_input`.
5. **A corrupt or half-written `_progress/progress.json`** must not crash the quiz: back it up as `progress.json.bad-<timestamp>`, warn, start fresh; saves are atomic. Tests: Task 4 `test_corrupt_progress_is_backed_up`, `test_save_is_atomic`.

## Files this plan creates

```
AWS_SAA_Course_claude/
├── .gitignore · pytest.ini · requirements.txt · verify_course.py · quiz.py · README.md · COURSE_FLOW.md
├── _harness/__init__.py · awsdrill.py · quizlib.py · labclean.py
├── _harness/awslib/__init__.py · safety.py · cfn.py · policy_eval.py · prices.py · prices.toml
├── _dev/smoke_stack.py
├── _dev/tests/conftest.py · test_safety_cfn.py · test_awsdrill.py · test_policy_eval.py · test_quizlib.py
│     · test_mock_exam.py · test_labclean.py · test_verify_course.py · test_milestone_tools.py
├── _dev/mutants/week00.py · week01.py · m01.py
├── docs/exam_guide.md · docs/facts.md
├── exam_prep/mock_exam.py · exam_prep/mock_exams/.gitkeep
├── week_00_foundations_and_exam_technique/README.md · concepts/01..05_*.md · concepts/demo_*.py (2)
│     · practice/exercises.py · practice/solutions.py · quiz/questions.toml · lab/LAB.md · lab/cleanup.py
├── week_01_iam_and_governance/  (same shape; 5 notes, 2 demos)
└── course_project/README.md · DEPLOY.md · milestones/M01.md · tests/m01/test_m01_{1..6}_*.py
      · solutions/m01/{infra/iam.yaml, params/lab.json, params/prod.json, README.md, .gitignore}
      · tools/{start_milestone.py, run_milestone.py, conftest.py}
```

## Deferred to later plans (not built here)

- `awslib/cidr.py` (week 02 solution) → week 02 plan.
- `labclean` finders for EC2/VPC/ELB/RDS/… → the week plan whose lab first needs them.
- `prices.toml` sections other than `data_transfer` and `s3_standard_tiers` → the week that needs them.
- `course_project/app/` (stand-in app for user data) → M03 (week 03 plan).
- Mock-exam banks `mock_1..4.toml`, `FINAL_REVIEW.md`, strict coverage enforcement → Step 12 plan.

**Deviations from the spec (deliberate, small):**
- No `iam_enforced()` helper in the harness: the only user is week 01's demo, which calls moto's `set_initial_no_auth_action_count` directly; week 01's predict drill uses the reference evaluator as its oracle.
- Week 00 drill 06 seeds 250 objects (three pages of 100), not 2,500: moto takes ≈ 10 s per 1,100 `put_object` calls, and three pages prove pagination just as well.
- Template helpers (`load_template`, `lint_template`, `render`, …) live in `awslib/cfn.py` rather than on `Drill`, because milestone tests in the learner's repo need them too.

## Waves (what may run in parallel)

| Wave | Tasks | Needs |
|---|---|---|
| A | 1 | — |
| B | 2, 3, 6, 9 | 1 |
| C | 4, 8 | 2 (8 also needs 3) |
| D | 5, 7 | 4 (7 also needs 2 and 6) |
| E | 10, 12, 14, 16, 18 | 2–9 |
| F | 11 (after 10), 13 (after 12), 15 (after 14), 17 (after 16), 19 (after 18) | its partner in E |
| G | 20 | everything |

Inside a wave, tasks touch different files. The main session verifies each finished task before it counts as done; a later wave starts only when every task it needs is verified.

---

### Task 1: Venv, pinned requirements, smoke test

**Files:**
- Create: `requirements.txt`, `.gitignore`, `pytest.ini`, `_dev/smoke_stack.py`, `_harness/__init__.py`, `_harness/awslib/__init__.py`, `exam_prep/mock_exams/.gitkeep`

**Interfaces:**
- Consumes: nothing.
- Produces: `.venv/` with the pinned stack; `requirements.txt` used by learners and every later task.

- [ ] **Step 1: Create the venv**

```bash
cd /c/Users/SyedQadri/Downloads/courses/AWS_SAA_Course_claude
python -m venv .venv
.venv/Scripts/python.exe -m pip install --upgrade pip
.venv/Scripts/python.exe --version
```

Expected: `Python 3.14.2`.

- [ ] **Step 2: Write `requirements.txt`**

```text
# AWS SAA course — pinned versions (Windows 11, Python 3.14.2, verified 2026-10-08)
# Install (course folder, venv active):  python -m pip install -r requirements.txt
# The spike (docs/research/2026-10-08-moto-cfnlint-spike.md) found no Windows Application Control
# blocks with these versions. If .venv\Scripts\python.exe ever disappears, run:
#     python -m venv --upgrade .venv
moto[all]==5.2.3
boto3==1.43.109
botocore==1.43.109
cfn-lint==1.57.2
pytest==9.1.1
```

- [ ] **Step 3: Install and record what came in**

```bash
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pip freeze > _dev/requirements-lock.txt
```

Expected: install succeeds; `_dev/requirements-lock.txt` lists moto 5.2.3, boto3 1.43.109, cfn-lint 1.57.2. If a native wheel is blocked ("An Application Control policy has blocked this file"), stop and report — do not try other versions without the main session.

- [ ] **Step 4: Write `.gitignore`**

```text
.venv/
__pycache__/
*.pyc
.pytest_cache/
_progress/
.lintcache/
```

- [ ] **Step 5: Write `pytest.ini`**

```ini
[pytest]
testpaths = _dev/tests
norecursedirs = .venv course_project week_* _dev/mutants exam_prep
addopts = -q -p no:cacheprovider
```

- [ ] **Step 6: Create the package markers**

`_harness/__init__.py` and `_harness/awslib/__init__.py` each contain exactly one line:

```python
"""Course-owned helpers. Importing this package has no side effects."""
```

Create the empty file `exam_prep/mock_exams/.gitkeep`.

- [ ] **Step 7: Write `_dev/smoke_stack.py`**

```python
"""Smoke test of the pinned stack: moto, boto3 and cfn-lint import and work offline."""
import os
import sys
import time

os.environ.update(AWS_ACCESS_KEY_ID="testing", AWS_SECRET_ACCESS_KEY="testing",
                  AWS_SESSION_TOKEN="testing", AWS_DEFAULT_REGION="us-east-1")
for stream in (sys.stdout, sys.stderr):
    stream.reconfigure(encoding="utf-8", errors="replace")

import boto3  # noqa: E402
import cfnlint.api  # noqa: E402
import cfnlint.decode  # noqa: E402
from moto import mock_aws  # noqa: E402

TEMPLATE = """AWSTemplateFormatVersion: '2010-09-09'
Parameters:
  Prefix: {Type: String, Default: shortly}
Resources:
  Bucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${Prefix}-assets'
"""

start = time.perf_counter()
with mock_aws():
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="smoke-bucket")
    assert [b["Name"] for b in s3.list_buckets()["Buckets"]] == ["smoke-bucket"]
template, errors = cfnlint.decode.decode_str(TEMPLATE)
assert not errors and template["Resources"]["Bucket"]["Properties"]["BucketName"] == {"Fn::Sub": "${Prefix}-assets"}
assert cfnlint.api.lint(TEMPLATE) == []
assert [m.rule.id for m in cfnlint.api.lint(TEMPLATE.replace("BucketName", "BucketNme"))] == ["E3002"]
print(f"✔ stack works ({time.perf_counter() - start:.1f} s)")
```

- [ ] **Step 8: Run it piped**

```bash
.venv/Scripts/python.exe _dev/smoke_stack.py | cat
```

Expected: one line `✔ stack works (… s)`, exit 0.

- [ ] **Step 9: Commit** — skipped (no git; see Global Constraints).

---

### Task 2: Safety, template helpers and the drill harness

**Files:**
- Create: `_harness/awslib/safety.py`, `_harness/awslib/cfn.py`, `_harness/awsdrill.py`
- Test: `_dev/tests/conftest.py`, `_dev/tests/test_safety_cfn.py`, `_dev/tests/test_awsdrill.py`

**Interfaces:**
- Consumes: Task 1 venv.
- Produces:
  - `awslib.safety.use_fake_aws_env(environ=os.environ) -> None`; `awslib.safety.FAKE_ENV: dict`; `awslib.safety.force_utf8() -> None`.
  - `awslib.cfn.TemplateError(ValueError)`; `load_template_text(text) -> dict`; `load_template(path) -> dict`; `lint_text(text) -> list[dict]` (each `{"rule", "line", "message"}`); `lint_template(path) -> list[dict]`; `errors_only(findings) -> list[dict]`; `resources(template, type_=None) -> dict[str, dict]`; `render(value, params=None, pseudo=None) -> Any`; `DEFAULT_PSEUDO: dict`; `role_policies(template, logical_id, params=None, pseudo=None) -> list[dict]`; `trust_policy(template, logical_id, params=None, pseudo=None) -> dict`.
  - `awsdrill`: `Drill` (attrs `uses_aws: bool`, `tasks: tuple`; methods `client`, `resource`, `assertClientError`, `assertHashed`), `FakeClock`, `normalise(value) -> str`, `digest(salt, value) -> str`, `MOTO_CONFIG`, `JSON_MARKER = "AWSDRILL_JSON "`, `run(argv=None)`, `inject_source(module, source, filename) -> list`, `force_utf8` (re-exported). `python -m _harness.awsdrill digest SALT VALUE` prints a digest. JSON report per drill: `{"title", "star", "tasks", "tests"}`.

- [ ] **Step 1: Write `_dev/tests/conftest.py`**

```python
"""Make the course root importable and force fake AWS credentials for every maintainer test."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from _harness.awslib.safety import use_fake_aws_env  # noqa: E402

use_fake_aws_env()
```

- [ ] **Step 2: Write the failing tests `_dev/tests/test_safety_cfn.py`**

```python
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from _harness.awslib import cfn
from _harness.awslib.safety import FAKE_ENV, use_fake_aws_env

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable

TEMPLATE = """AWSTemplateFormatVersion: '2010-09-09'
Parameters:
  Prefix: {Type: String, Default: shortly}
Resources:
  Boundary:
    Type: AWS::IAM::ManagedPolicy
    Properties:
      PolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Action: ['s3:*']
            Resource: '*'
  AppRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal: {Service: ec2.amazonaws.com}
            Action: sts:AssumeRole
      ManagedPolicyArns: [!Ref Boundary]
      Policies:
        - PolicyName: app
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action: [s3:GetObject]
                Resource: !Sub 'arn:${AWS::Partition}:s3:::${Prefix}-assets-${AWS::AccountId}/*'
"""


def test_fake_env_overrides_real_credentials():
    env = {"AWS_PROFILE": "work", "AWS_ACCESS_KEY_ID": "AKIAREALKEY", "AWS_ENDPOINT_URL_S3": "http://x",
           "AWS_DEFAULT_PROFILE": "work", "PATH": "keep"}
    use_fake_aws_env(env)
    assert "AWS_PROFILE" not in env and "AWS_DEFAULT_PROFILE" not in env
    assert not any(k.startswith("AWS_ENDPOINT_URL") for k in env)
    for key, value in FAKE_ENV.items():
        assert env[key] == value
    assert not Path(env["AWS_CONFIG_FILE"]).exists()
    assert not Path(env["AWS_SHARED_CREDENTIALS_FILE"]).exists()
    assert env["PATH"] == "keep"


def test_real_profile_file_is_ignored(tmp_path):
    (tmp_path / "credentials").write_text("[default]\naws_access_key_id = AKIAREALKEY\n"
                                          "aws_secret_access_key = realsecret\n")
    code = ("import os, boto3; from _harness.awslib.safety import use_fake_aws_env; use_fake_aws_env(); "
            "print(boto3.Session().get_credentials().access_key)")
    env = dict(os.environ, AWS_SHARED_CREDENTIALS_FILE=str(tmp_path / "credentials"), AWS_PROFILE="default")
    for key in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_SECURITY_TOKEN"):
        env.pop(key, None)  # without use_fake_aws_env, boto3 would now read AKIAREALKEY from the file
    out = subprocess.run([PY, "-c", code], cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
    assert out.stdout.strip() == "testing", out.stderr


def test_load_template_decodes_short_tags():
    template = cfn.load_template_text(TEMPLATE)
    assert type(template) is dict
    sub = template["Resources"]["AppRole"]["Properties"]["Policies"][0]["PolicyDocument"]["Statement"][0]["Resource"]
    assert sub == {"Fn::Sub": "arn:${AWS::Partition}:s3:::${Prefix}-assets-${AWS::AccountId}/*"}


def test_load_template_reports_bad_yaml():
    with pytest.raises(cfn.TemplateError):
        cfn.load_template_text("Resources: [unclosed")


def test_lint_finds_errors_and_caches(tmp_path, monkeypatch):
    monkeypatch.setattr(cfn, "CACHE_DIR", tmp_path)
    assert cfn.lint_text(TEMPLATE) == []
    bad = TEMPLATE.replace("AssumeRolePolicyDocument", "AssumeRolePolicyDocumnt")
    findings = cfn.lint_text(bad)
    assert findings and findings[0]["rule"].startswith("E") and isinstance(findings[0]["line"], int)
    assert len(list(tmp_path.glob("*.json"))) == 2
    monkeypatch.setattr(cfn, "_run_cfnlint", lambda text: pytest.fail("cache was not used"))
    assert cfn.lint_text(bad) == findings


def test_errors_only_drops_warnings():
    findings = [{"rule": "W1001", "line": 1, "message": "w"}, {"rule": "E3002", "line": 2, "message": "e"}]
    assert cfn.errors_only(findings) == [findings[1]]


def test_resources_by_type():
    template = cfn.load_template_text(TEMPLATE)
    assert set(cfn.resources(template)) == {"Boundary", "AppRole"}
    assert set(cfn.resources(template, "AWS::IAM::Role")) == {"AppRole"}


def test_render_sub_ref_join_and_getatt():
    params = {"Prefix": "shortly"}
    assert cfn.render({"Fn::Sub": "${Prefix}-x-${AWS::AccountId}"}, params) == "shortly-x-111122223333"
    assert cfn.render({"Fn::Sub": ["${A}-${Prefix}", {"A": "a"}]}, params) == "a-shortly"
    assert cfn.render({"Ref": "Prefix"}, params) == "shortly"
    assert cfn.render({"Ref": "AWS::Region"}, params) == "us-east-1"
    assert cfn.render({"Ref": "SomeResource"}, params) == "SomeResource"
    assert cfn.render({"Fn::GetAtt": ["Role", "Arn"]}, params) == "Role.Arn"
    assert cfn.render({"Fn::GetAtt": "Role.Arn"}, params) == "Role.Arn"
    assert cfn.render({"Fn::Join": ["-", ["a", {"Ref": "Prefix"}]]}, params) == "a-shortly"
    assert cfn.render({"Fn::Sub": "${!Literal}"}, params) == "${Literal}"
    assert cfn.render(["x", {"k": {"Ref": "Prefix"}}], params) == ["x", {"k": "shortly"}]


def test_render_unknown_parameter_raises():
    with pytest.raises(cfn.TemplateError, match="Missing"):
        cfn.render({"Fn::Sub": "${Missing}"}, {})


def test_role_policies_and_trust():
    template = cfn.load_template_text(TEMPLATE)
    policies = cfn.role_policies(template, "AppRole", {"Prefix": "shortly"})
    resources = [s["Resource"] for p in policies for s in p["Statement"]]
    assert "arn:aws:s3:::shortly-assets-111122223333/*" in resources
    assert "*" in resources  # the in-template managed policy was followed through !Ref
    trust = cfn.trust_policy(template, "AppRole")
    assert trust["Statement"][0]["Principal"] == {"Service": "ec2.amazonaws.com"}
    with pytest.raises(cfn.TemplateError, match="NoSuchRole"):
        cfn.role_policies(template, "NoSuchRole")
```

- [ ] **Step 3: Run them to see them fail**

```bash
.venv/Scripts/python.exe -m pytest _dev/tests/test_safety_cfn.py
```

Expected: collection error — `ModuleNotFoundError: No module named '_harness.awslib.safety'`.

- [ ] **Step 4: Write `_harness/awslib/safety.py`**

```python
"""safety — keep every course check away from real AWS accounts.

use_fake_aws_env() replaces credential/profile variables with fake values and points boto3 at
config files that do not exist, so a learner's real ~/.aws profile can never be picked up.
The drill harness and the milestone conftest call it on import. The lab-cleanup library does
NOT — cleanup is meant for the learner's real account.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

FAKE_ENV = {
    "AWS_ACCESS_KEY_ID": "testing",
    "AWS_SECRET_ACCESS_KEY": "testing",
    "AWS_SESSION_TOKEN": "testing",
    "AWS_SECURITY_TOKEN": "testing",
    "AWS_DEFAULT_REGION": "us-east-1",
    "AWS_REGION": "us-east-1",
    "AWS_EC2_METADATA_DISABLED": "true",
}
_DROP = ("AWS_PROFILE", "AWS_DEFAULT_PROFILE", "AWS_ROLE_ARN", "AWS_ROLE_SESSION_NAME",
         "AWS_WEB_IDENTITY_TOKEN_FILE", "AWS_CONTAINER_CREDENTIALS_FULL_URI",
         "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI", "AWS_CONTAINER_AUTHORIZATION_TOKEN", "AWS_CA_BUNDLE")
NOWHERE = Path(tempfile.gettempdir()) / "saa-course-no-aws-config-here"


def use_fake_aws_env(environ=os.environ) -> None:
    for key in list(environ):
        if key in _DROP or key.startswith("AWS_ENDPOINT_URL"):
            del environ[key]
    environ.update(FAKE_ENV)
    environ["AWS_CONFIG_FILE"] = str(NOWHERE / "config")
    environ["AWS_SHARED_CREDENTIALS_FILE"] = str(NOWHERE / "credentials")


def force_utf8() -> None:
    """Let ✔/✘/★ print on Windows consoles and through pipes (their default encoding is cp1252)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
```

- [ ] **Step 5: Write `_harness/awslib/cfn.py`**

```python
"""cfn — load, lint and inspect CloudFormation templates.

Shared by drills, milestone tests (copied into the learner's repo as tests/_course/cfn.py) and
verify_course.py. Templates may use short-form tags (!Ref, !Sub, !GetAtt …); loading turns them
into the long form ({"Ref": …}, {"Fn::Sub": …}) as plain dicts and lists.
"""
from __future__ import annotations

import hashlib
import json
import re
import tempfile
from importlib.metadata import version
from pathlib import Path
from typing import Any

CACHE_DIR = Path(tempfile.gettempdir()) / "saa-course-lintcache"
DEFAULT_PSEUDO = {
    "AWS::AccountId": "111122223333",
    "AWS::Region": "us-east-1",
    "AWS::Partition": "aws",
    "AWS::URLSuffix": "amazonaws.com",
    "AWS::StackName": "shortly-stack",
    "AWS::NoValue": None,
}
_SUB_VAR = re.compile(r"\$\{([^}]+)\}")


class TemplateError(ValueError):
    """A template could not be loaded or rendered."""


def load_template_text(text: str) -> dict:
    from cfnlint.decode import decode_str

    template, errors = decode_str(text)
    if errors or template is None:
        problems = "; ".join(f"line {e.linenumber}: {e.message}" for e in errors) or "empty template"
        raise TemplateError(problems)
    return json.loads(json.dumps(template))


def load_template(path) -> dict:
    return load_template_text(Path(path).read_text(encoding="utf-8"))


def _run_cfnlint(text: str) -> list[dict]:
    import cfnlint.api

    return [{"rule": m.rule.id, "line": m.linenumber, "message": m.message} for m in cfnlint.api.lint(text)]


def lint_text(text: str) -> list[dict]:
    """cfn-lint findings for a template, cached by (cfn-lint version, text) because one run costs ≈ 2 s."""
    key = hashlib.sha256(f"{version('cfn-lint')}\0{text}".encode("utf-8")).hexdigest()
    cached = CACHE_DIR / f"{key}.json"
    try:
        return json.loads(cached.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    findings = _run_cfnlint(text)
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cached.write_text(json.dumps(findings), encoding="utf-8")
    except OSError:
        pass
    return findings


def lint_template(path) -> list[dict]:
    return lint_text(Path(path).read_text(encoding="utf-8"))


def errors_only(findings: list[dict]) -> list[dict]:
    return [f for f in findings if f["rule"].startswith("E")]


def resources(template: dict, type_: str | None = None) -> dict[str, dict]:
    found = template.get("Resources") or {}
    return {name: res for name, res in found.items() if type_ is None or res.get("Type") == type_}


def _lookup(name: str, params: dict, pseudo: dict):
    if name in params:
        return params[name]
    if name in pseudo:
        return pseudo[name]
    raise TemplateError(f"unknown parameter {name}")


def render(value: Any, params: dict | None = None, pseudo: dict | None = None) -> Any:
    """Resolve Ref / Fn::Sub / Fn::Join / Fn::GetAtt with test parameter values.
    A Ref to a resource renders as its logical id; Fn::GetAtt renders as "Logical.Attr"."""
    params = params or {}
    pseudo = {**DEFAULT_PSEUDO, **(pseudo or {})}
    if isinstance(value, list):
        return [render(v, params, pseudo) for v in value]
    if not isinstance(value, dict):
        return value
    if len(value) == 1:
        (key, arg), = value.items()
        if key == "Ref":
            if arg in params or arg in pseudo:
                return _lookup(arg, params, pseudo)
            return arg
        if key == "Fn::GetAtt":
            parts = arg.split(".", 1) if isinstance(arg, str) else arg
            return f"{parts[0]}.{parts[1]}"
        if key == "Fn::Join":
            sep, items = arg
            return sep.join(str(render(i, params, pseudo)) for i in items)
        if key == "Fn::Sub":
            text, local = (arg, {}) if isinstance(arg, str) else (arg[0], arg[1])
            local = {k: render(v, params, pseudo) for k, v in local.items()}

            def replace(match):
                name = match.group(1)
                if name.startswith("!"):
                    return "${" + name[1:] + "}"
                if name in local:
                    return str(local[name])
                if "." in name:
                    return name
                if name in params or name in pseudo:
                    return str(_lookup(name, params, pseudo))
                raise TemplateError(f"Fn::Sub uses ${{{name}}} but no parameter or pseudo parameter {name} exists")
            return _SUB_VAR.sub(replace, text)
    return {k: render(v, params, pseudo) for k, v in value.items()}


def _role(template: dict, logical_id: str) -> dict:
    res = resources(template).get(logical_id)
    if res is None or res.get("Type") != "AWS::IAM::Role":
        raise TemplateError(f"no AWS::IAM::Role named {logical_id}")
    return res.get("Properties") or {}


def role_policies(template: dict, logical_id: str, params=None, pseudo=None) -> list[dict]:
    """Every identity policy document attached to a role: inline Policies plus in-template
    AWS::IAM::ManagedPolicy resources referenced from ManagedPolicyArns (AWS-managed ARNs are
    skipped — their contents are not available offline)."""
    props = _role(template, logical_id)
    docs = [p["PolicyDocument"] for p in props.get("Policies") or []]
    for arn in props.get("ManagedPolicyArns") or []:
        if isinstance(arn, dict) and "Ref" in arn:
            target = resources(template).get(arn["Ref"])
            if target and target.get("Type") == "AWS::IAM::ManagedPolicy":
                docs.append(target["Properties"]["PolicyDocument"])
    return render(docs, params, pseudo)


def trust_policy(template: dict, logical_id: str, params=None, pseudo=None) -> dict:
    return render(_role(template, logical_id).get("AssumeRolePolicyDocument") or {}, params, pseudo)
```

- [ ] **Step 6: Run the safety/cfn tests**

```bash
.venv/Scripts/python.exe -m pytest _dev/tests/test_safety_cfn.py
```

Expected: `10 passed`.

- [ ] **Step 7: Write the failing harness tests `_dev/tests/test_awsdrill.py`**

```python
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
```

- [ ] **Step 8: Run them to see them fail**

```bash
.venv/Scripts/python.exe -m pytest _dev/tests/test_awsdrill.py
```

Expected: `ImportError: cannot import name 'awsdrill'`.

- [ ] **Step 9: Write `_harness/awsdrill.py`**

```python
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
```

- [ ] **Step 10: Run the harness tests**

```bash
.venv/Scripts/python.exe -m pytest _dev/tests/test_awsdrill.py _dev/tests/test_safety_cfn.py
```

Expected: `20 passed`. Note `json.loads("Allow")` fails, so the digest CLI hashes the raw string `Allow` — the test relies on that.

- [ ] **Step 11: Commit** — skipped (no git).

---

### Task 3: Reference IAM policy evaluator `awslib/policy_eval.py`

**Files:**
- Create: `_harness/awslib/policy_eval.py`
- Test: `_dev/tests/test_policy_eval.py`

**Interfaces:**
- Consumes: nothing (stdlib only).
- Produces (week 01 drills, M01 tests and later weeks rely on these exact names):
  - `Request(principal: str, action: str, resource: str, context: dict = {})` — frozen dataclass.
  - `as_list(value) -> list`; `statements(policy: dict) -> list[dict]`; `account_of(arn: str) -> str | None`.
  - `action_matches(pattern: str, action: str) -> bool`; `resource_matches(pattern: str, arn: str) -> bool`; `principal_matches(principal, caller_arn: str) -> bool`.
  - `condition_matches(condition: dict | None, context: dict) -> bool` (raises `ValueError` for unsupported operators).
  - `statement_applies(statement: dict, request: Request, *, check_principal: bool = False) -> bool`.
  - `evaluate_policies(policies: list[dict], request: Request) -> str` — `"Allow" | "ExplicitDeny" | "ImplicitDeny"`.
  - `evaluate(request, *, identity=(), resource_policy=None, scps=None, boundary=None, session=None, resource_account=None) -> str`; `scps` is a list of levels (root → OU → account), each a list of policies.
  - `evaluate_trust(trust_policy: dict, caller_arn: str, context: dict | None = None) -> bool`.

- [ ] **Step 1: Write the failing tests `_dev/tests/test_policy_eval.py`**

```python
import pytest

from _harness.awslib.policy_eval import (Request, account_of, action_matches, condition_matches,
                                         evaluate, evaluate_policies, evaluate_trust, principal_matches,
                                         resource_matches, statement_applies, statements)

A = "111122223333"
B = "444455556666"
ROLE = f"arn:aws:iam::{A}:role/app"
SESSION = f"arn:aws:sts::{A}:assumed-role/app/i-0abc"
BUCKET_OBJ = "arn:aws:s3:::shortly-assets/uploads/a.png"
FULL = {"Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]}


def allow(action, resource="*", **extra):
    return {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": action, "Resource": resource, **extra}]}


def deny(action, resource="*", **extra):
    return {"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Action": action, "Resource": resource, **extra}]}


def req(action="s3:GetObject", resource=BUCKET_OBJ, principal=ROLE, **context):
    return Request(principal=principal, action=action, resource=resource, context=context)


@pytest.mark.parametrize("pattern, action, expected", [
    ("s3:GetObject", "s3:GetObject", True), ("s3:getobject", "S3:GetObject", True),
    ("s3:Get*", "s3:GetObjectTagging", True), ("s3:*", "s3:PutObject", True), ("*", "ec2:RunInstances", True),
    ("s3:Get?bject", "s3:GetObject", True), ("s3:Get*", "s3:PutObject", False), ("ec2:*", "s3:GetObject", False),
    ("s3:List*", "s3:GetObject", False),
])
def test_action_matches(pattern, action, expected):
    assert action_matches(pattern, action) is expected


@pytest.mark.parametrize("pattern, arn, expected", [
    ("*", BUCKET_OBJ, True),
    ("arn:aws:s3:::shortly-assets/*", BUCKET_OBJ, True),
    ("arn:aws:s3:::shortly-assets/uploads/*", BUCKET_OBJ, True),
    ("arn:aws:s3:::shortly-assets", BUCKET_OBJ, False),
    ("arn:aws:s3:::Shortly-assets/*", BUCKET_OBJ, False),  # resources are case-sensitive
    ("arn:aws:dynamodb:*:*:table/shortly-*", f"arn:aws:dynamodb:us-east-1:{A}:table/shortly-links", True),
    ("arn:aws:dynamodb:*:*:table/shortly-*", f"arn:aws:dynamodb:us-east-1:{A}:table/other", False),
    ("arn:aws:lambda:us-east-1:*:function:f*", f"arn:aws:lambda:us-east-1:{A}:function:fn:PROD", True),
    ("arn:aws:*:us-east-1:*:*", f"arn:aws:sqs:eu-west-1:{A}:q", False),  # a wildcard never spans segments
])
def test_resource_matches(pattern, arn, expected):
    assert resource_matches(pattern, arn) is expected


def test_account_of():
    assert account_of(ROLE) == A
    assert account_of("arn:aws:s3:::bucket") is None
    assert account_of("ec2.amazonaws.com") is None


@pytest.mark.parametrize("principal, caller, expected", [
    ("*", ROLE, True), ({"AWS": "*"}, ROLE, True), ({"AWS": A}, ROLE, True),
    ({"AWS": f"arn:aws:iam::{A}:root"}, SESSION, True), ({"AWS": f"arn:aws:iam::{B}:root"}, ROLE, False),
    ({"AWS": ROLE}, ROLE, True), ({"AWS": ROLE}, SESSION, True),
    ({"AWS": f"arn:aws:iam::{A}:role/team/app"}, SESSION, True),  # role path is not in the session ARN
    ({"AWS": f"arn:aws:iam::{A}:role/other"}, SESSION, False),
    ({"Service": "ec2.amazonaws.com"}, "ec2.amazonaws.com", True),
    ({"Service": ["lambda.amazonaws.com"]}, "ec2.amazonaws.com", False),
])
def test_principal_matches(principal, caller, expected):
    assert principal_matches(principal, caller) is expected


def test_statements_accepts_single_dict():
    assert statements({"Statement": {"Effect": "Allow"}}) == [{"Effect": "Allow"}]


@pytest.mark.parametrize("condition, context, expected", [
    (None, {}, True),
    ({"StringEquals": {"aws:RequestedRegion": "us-east-1"}}, {"aws:RequestedRegion": "us-east-1"}, True),
    ({"StringEquals": {"aws:RequestedRegion": ["us-east-1", "eu-west-1"]}}, {"aws:RequestedRegion": "eu-west-1"}, True),
    ({"StringEquals": {"aws:RequestedRegion": "us-east-1"}}, {"aws:requestedregion": "us-east-1"}, True),  # keys are case-insensitive
    ({"StringEquals": {"aws:RequestedRegion": "us-east-1"}}, {}, False),
    ({"StringNotEquals": {"aws:RequestedRegion": ["us-east-1", "us-west-2"]}}, {"aws:RequestedRegion": "eu-west-1"}, True),
    ({"StringNotEquals": {"aws:RequestedRegion": ["us-east-1", "us-west-2"]}}, {"aws:RequestedRegion": "us-west-2"}, False),
    ({"StringNotEquals": {"aws:RequestedRegion": "us-east-1"}}, {}, True),  # negated operator, key missing
    ({"StringLike": {"s3:prefix": "home/*"}}, {"s3:prefix": "home/alice/"}, True),
    ({"StringLike": {"s3:prefix": "home/*"}}, {"s3:prefix": "Home/alice/"}, False),
    ({"StringEqualsIgnoreCase": {"aws:PrincipalTag/team": "Data"}}, {"aws:PrincipalTag/team": "data"}, True),
    ({"Bool": {"aws:SecureTransport": "true"}}, {"aws:SecureTransport": True}, True),
    ({"Bool": {"aws:SecureTransport": "true"}}, {"aws:SecureTransport": False}, False),
    ({"Bool": {"aws:MultiFactorAuthPresent": "true"}}, {}, False),
    ({"BoolIfExists": {"aws:MultiFactorAuthPresent": "false"}}, {}, True),
    ({"IpAddress": {"aws:SourceIp": "203.0.113.0/24"}}, {"aws:SourceIp": "203.0.113.7"}, True),
    ({"NotIpAddress": {"aws:SourceIp": "203.0.113.0/24"}}, {"aws:SourceIp": "198.51.100.1"}, True),
    ({"NumericLessThanEquals": {"s3:max-keys": "100"}}, {"s3:max-keys": 50}, True),
    ({"NumericGreaterThan": {"s3:max-keys": "100"}}, {"s3:max-keys": 50}, False),
    ({"ArnLike": {"aws:SourceArn": "arn:aws:sns:*:*:alerts"}}, {"aws:SourceArn": f"arn:aws:sns:us-east-1:{A}:alerts"}, True),
    ({"Null": {"aws:TokenIssueTime": "true"}}, {}, True),
    ({"Null": {"aws:TokenIssueTime": "false"}}, {}, False),
    ({"ForAnyValue:StringEquals": {"aws:TagKeys": ["env", "team"]}}, {"aws:TagKeys": ["owner", "env"]}, True),
    ({"ForAnyValue:StringEquals": {"aws:TagKeys": ["env"]}}, {}, False),
    ({"ForAllValues:StringEquals": {"aws:TagKeys": ["env", "team"]}}, {"aws:TagKeys": ["env", "owner"]}, False),
    ({"ForAllValues:StringEquals": {"aws:TagKeys": ["env", "team"]}}, {"aws:TagKeys": ["team"]}, True),
    ({"ForAllValues:StringEquals": {"aws:TagKeys": ["env"]}}, {}, True),  # the classic trap: empty set passes
    ({"StringEquals": {"a": "1"}, "Bool": {"b": "true"}}, {"a": "1", "b": False}, False),  # operators are ANDed
    ({"StringEquals": {"a": "1", "c": "2"}}, {"a": "1", "c": "3"}, False),  # keys are ANDed
])
def test_condition_matches(condition, context, expected):
    assert condition_matches(condition, context) is expected


def test_unsupported_operator_raises():
    with pytest.raises(ValueError, match="DateGreaterThan"):
        condition_matches({"DateGreaterThan": {"aws:CurrentTime": "2026-01-01T00:00:00Z"}}, {})


def test_statement_applies_not_action_and_not_resource():
    st = {"Effect": "Deny", "NotAction": ["iam:*", "sts:*"], "Resource": "*"}
    assert statement_applies(st, req("s3:PutObject"))
    assert not statement_applies(st, req("iam:CreateRole"))
    st = {"Effect": "Allow", "Action": "s3:*", "NotResource": "arn:aws:s3:::secret/*"}
    assert statement_applies(st, req("s3:GetObject", BUCKET_OBJ))
    assert not statement_applies(st, req("s3:GetObject", "arn:aws:s3:::secret/x"))


def test_statement_needs_principal_when_checked():
    st = {"Effect": "Allow", "Action": "s3:GetObject", "Resource": "*"}
    assert statement_applies(st, req())
    assert not statement_applies(st, req(), check_principal=True)


def test_evaluate_policies_deny_beats_allow():
    policies = [allow("s3:*", "arn:aws:s3:::shortly-assets/*"), deny("s3:DeleteObject")]
    assert evaluate_policies(policies, req("s3:GetObject")) == "Allow"
    assert evaluate_policies(policies, req("s3:DeleteObject")) == "ExplicitDeny"
    assert evaluate_policies(policies, req("ec2:RunInstances", "*")) == "ImplicitDeny"
    assert evaluate_policies([], req()) == "ImplicitDeny"


def test_evaluate_scp_levels_each_must_allow():
    identity = [FULL]
    assert evaluate(req(), identity=identity, scps=[[FULL], [FULL]]) == "Allow"
    assert evaluate(req(), identity=identity, scps=[[FULL], [allow("ec2:*")]]) == "ImplicitDeny"
    assert evaluate(req(), identity=identity, scps=[[FULL], [FULL, deny("s3:*")]]) == "ExplicitDeny"
    assert evaluate(req(), identity=[], scps=[[FULL]]) == "ImplicitDeny"  # SCPs never grant


def test_evaluate_boundary_and_session_limit():
    identity = [allow(["s3:*", "ec2:*"])]
    assert evaluate(req("ec2:RunInstances", "*"), identity=identity, boundary=allow("s3:*")) == "ImplicitDeny"
    assert evaluate(req("s3:GetObject"), identity=identity, boundary=allow("s3:*")) == "Allow"
    assert evaluate(req("s3:GetObject"), identity=identity, session=allow("s3:List*")) == "ImplicitDeny"


def test_evaluate_same_account_resource_policy_is_enough():
    bucket_policy = {"Statement": [{"Effect": "Allow", "Principal": {"AWS": ROLE}, "Action": "s3:GetObject",
                                    "Resource": "arn:aws:s3:::shortly-assets/*"}]}
    assert evaluate(req(), identity=[], resource_policy=bucket_policy, resource_account=A) == "Allow"


def test_evaluate_cross_account_needs_both_sides():
    caller = f"arn:aws:iam::{B}:role/partner"
    bucket_policy = {"Statement": [{"Effect": "Allow", "Principal": {"AWS": f"arn:aws:iam::{B}:root"},
                                    "Action": "s3:GetObject", "Resource": "arn:aws:s3:::shortly-assets/*"}]}
    identity = [allow("s3:GetObject", "arn:aws:s3:::shortly-assets/*")]
    assert evaluate(req(principal=caller), identity=identity, resource_account=A) == "ImplicitDeny"
    assert evaluate(req(principal=caller), identity=[], resource_policy=bucket_policy, resource_account=A) == "ImplicitDeny"
    assert evaluate(req(principal=caller), identity=identity, resource_policy=bucket_policy, resource_account=A) == "Allow"


def test_evaluate_resource_policy_explicit_deny_wins():
    bucket_policy = {"Statement": [{"Effect": "Deny", "Principal": "*", "Action": "s3:*", "Resource": "*",
                                    "Condition": {"Bool": {"aws:SecureTransport": "false"}}}]}
    identity = [allow("s3:GetObject")]
    assert evaluate(req(**{"aws:SecureTransport": False}), identity=identity, resource_policy=bucket_policy) == "ExplicitDeny"
    assert evaluate(req(**{"aws:SecureTransport": True}), identity=identity, resource_policy=bucket_policy) == "Allow"


def test_evaluate_trust_external_id_and_mfa():
    trust = {"Statement": [{"Effect": "Allow", "Principal": {"AWS": f"arn:aws:iam::{B}:root"},
                            "Action": "sts:AssumeRole",
                            "Condition": {"StringEquals": {"sts:ExternalId": "shortly-ext-42"}}}]}
    partner = f"arn:aws:iam::{B}:role/partner"
    assert evaluate_trust(trust, partner, {"sts:ExternalId": "shortly-ext-42"})
    assert not evaluate_trust(trust, partner, {"sts:ExternalId": "guess"})
    assert not evaluate_trust(trust, partner)
    assert not evaluate_trust(trust, ROLE, {"sts:ExternalId": "shortly-ext-42"})
```

- [ ] **Step 2: Run them to see them fail**

```bash
.venv/Scripts/python.exe -m pytest _dev/tests/test_policy_eval.py
```

Expected: `ModuleNotFoundError: No module named '_harness.awslib.policy_eval'`.

- [ ] **Step 3: Write `_harness/awslib/policy_eval.py`**

```python
"""policy_eval — a small, readable model of AWS IAM policy evaluation.

This is the reference solution for week 01's drills 01–04: finish those drills before you read it.

The model (from the official IAM "Policy evaluation logic" page, simplified where noted):
  • A statement applies to a request when its Action/NotAction, Resource/NotResource and Condition
    all match — and, for resource-based and trust policies, its Principal/NotPrincipal.
  • Within a set of policies: any applicable Deny → "ExplicitDeny"; otherwise any applicable
    Allow → "Allow"; otherwise "ImplicitDeny" (the default).
  • evaluate() combines policy types: an explicit Deny anywhere wins; every SCP level must allow;
    the identity policy OR a same-account resource-based policy must allow (cross-account: BOTH
    must); a permissions boundary and a session policy, when present, must also allow.
  • Simplifications: no policy variables (${aws:username}); no Date operators; no resource control
    policies (RCPs); a permissions boundary also limits same-account resource-policy grants (in AWS
    it does not when the resource policy names an IAM user or a role session directly).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from ipaddress import ip_address, ip_network

ALLOW, EXPLICIT_DENY, IMPLICIT_DENY = "Allow", "ExplicitDeny", "ImplicitDeny"


@dataclass(frozen=True)
class Request:
    principal: str                 # caller ARN, e.g. arn:aws:sts::111122223333:assumed-role/app/i-0abc
    action: str                    # e.g. "s3:GetObject"
    resource: str                  # resource ARN, or "*" for actions without resources
    context: dict = field(default_factory=dict)   # condition keys, e.g. {"aws:SecureTransport": True}


def as_list(value) -> list:
    if value is None:
        return []
    return list(value) if isinstance(value, (list, tuple, set)) else [value]


def statements(policy: dict) -> list[dict]:
    found = (policy or {}).get("Statement", [])
    return [found] if isinstance(found, dict) else list(found)


def account_of(arn: str) -> str | None:
    parts = str(arn).split(":", 5)
    if len(parts) == 6 and parts[0] == "arn" and re.fullmatch(r"\d{12}", parts[4]):
        return parts[4]
    return None


def _glob(pattern: str, text: str, ignore_case: bool) -> bool:
    regex = "".join(".*" if c == "*" else "." if c == "?" else re.escape(c) for c in pattern)
    flags = re.DOTALL | (re.IGNORECASE if ignore_case else 0)
    return re.fullmatch(regex, text, flags) is not None


def action_matches(pattern: str, action: str) -> bool:
    """Actions are case-insensitive; * matches any characters, ? one character."""
    return _glob(pattern, action, ignore_case=True)


def resource_matches(pattern: str, arn: str) -> bool:
    """Resources are case-sensitive and compared segment by segment (a wildcard never spans ':')."""
    if pattern == "*":
        return True
    p_parts, a_parts = pattern.split(":", 5), arn.split(":", 5)
    if len(p_parts) != 6 or len(a_parts) != 6:
        return _glob(pattern, arn, ignore_case=False)
    return all(_glob(p, a, ignore_case=False) for p, a in zip(p_parts, a_parts))


_ROLE = re.compile(r"arn:[^:]+:iam::(\d{12}):role/(?:.*/)?([^/]+)")
_SESSION = re.compile(r"arn:[^:]+:sts::(\d{12}):assumed-role/([^/]+)/.+")
_ROOT = re.compile(r"arn:[^:]+:iam::(\d{12}):root")


def principal_matches(principal, caller_arn: str) -> bool:
    if principal == "*":
        return True
    if isinstance(principal, str):
        principal = {"AWS": principal}
    for kind, values in principal.items():
        for value in as_list(values):
            if value == "*":
                return True
            if kind != "AWS":
                if value == caller_arn:
                    return True
                continue
            root = _ROOT.fullmatch(value)
            account = value if re.fullmatch(r"\d{12}", value) else (root.group(1) if root else None)
            if account is not None:
                if account_of(caller_arn) == account:
                    return True
                continue
            if value == caller_arn:
                return True
            role, session = _ROLE.fullmatch(value), _SESSION.fullmatch(caller_arn)
            if role and session and role.groups() == session.groups():
                return True
    return False


# ── conditions ──────────────────────────────────────────────────────

_NEGATED = {"StringNotEquals": "StringEquals", "StringNotEqualsIgnoreCase": "StringEqualsIgnoreCase",
            "StringNotLike": "StringLike", "NumericNotEquals": "NumericEquals",
            "NotIpAddress": "IpAddress", "ArnNotEquals": "ArnEquals", "ArnNotLike": "ArnLike"}
_NUMERIC = {"NumericEquals": lambda x, y: x == y, "NumericLessThan": lambda x, y: x < y,
            "NumericLessThanEquals": lambda x, y: x <= y, "NumericGreaterThan": lambda x, y: x > y,
            "NumericGreaterThanEquals": lambda x, y: x >= y}
_POSITIVE = {"StringEquals", "StringEqualsIgnoreCase", "StringLike", "Bool", "IpAddress",
             "ArnEquals", "ArnLike", *_NUMERIC}
SUPPORTED = _POSITIVE | set(_NEGATED) | {"Null"}


def _parse_operator(name: str):
    qualifier = None
    for prefix, label in (("ForAnyValue:", "any"), ("ForAllValues:", "all")):
        if name.startswith(prefix):
            qualifier, name = label, name[len(prefix):]
    if_exists = name.endswith("IfExists") and name != "Null"
    if if_exists:
        name = name[: -len("IfExists")]
    if name not in SUPPORTED:
        raise ValueError(f"unsupported condition operator {name}")
    return qualifier, name, if_exists


def _value_matches(op: str, actual, expected) -> bool:
    a, e = str(actual), str(expected)
    if op == "StringEquals":
        return a == e
    if op == "StringEqualsIgnoreCase":
        return a.casefold() == e.casefold()
    if op == "StringLike":
        return _glob(e, a, ignore_case=False)
    if op in _NUMERIC:
        return _NUMERIC[op](float(a), float(e))
    if op == "Bool":
        return a.lower() == e.lower()
    if op == "IpAddress":
        return ip_address(a) in ip_network(e, strict=False)
    if op in ("ArnEquals", "ArnLike"):
        return resource_matches(e, a)
    raise ValueError(f"unsupported condition operator {op}")


def _one(op: str, actual, expected_values: list) -> bool:
    if op in _NEGATED:
        return not any(_value_matches(_NEGATED[op], actual, e) for e in expected_values)
    return any(_value_matches(op, actual, e) for e in expected_values)


def _lookup(context: dict, key: str):
    for name, value in context.items():
        if name.lower() == key.lower():
            return value
    return None


def condition_matches(condition: dict | None, context: dict) -> bool:
    """Every operator and every key in the block must hold (AND); several values for one key are
    alternatives (OR). Missing keys: false for positive operators, true for negated ones and for
    ...IfExists; ForAllValues passes on an empty or missing set, ForAnyValue fails."""
    for operator, block in (condition or {}).items():
        qualifier, op, if_exists = _parse_operator(operator)
        for key, expected in block.items():
            expected_values = as_list(expected)
            actual = _lookup(context, key)
            present = actual is not None and actual != []
            if op == "Null":
                if (str(expected_values[0]).lower() == "true") == present:
                    return False
                continue
            if not present:
                if qualifier == "any":
                    return False
                if if_exists or qualifier == "all" or op in _NEGATED:
                    continue
                return False
            actual_values = as_list(actual)
            check = all if qualifier == "all" else any
            if not check(_one(op, a, expected_values) for a in actual_values):
                return False
    return True


# ── statements and decisions ────────────────────────────────────────


def statement_applies(statement: dict, request: Request, *, check_principal: bool = False) -> bool:
    if check_principal:
        if "Principal" in statement:
            if not principal_matches(statement["Principal"], request.principal):
                return False
        elif "NotPrincipal" in statement:
            if principal_matches(statement["NotPrincipal"], request.principal):
                return False
        else:
            return False
    if "Action" in statement:
        ok = any(action_matches(p, request.action) for p in as_list(statement["Action"]))
    elif "NotAction" in statement:
        ok = not any(action_matches(p, request.action) for p in as_list(statement["NotAction"]))
    else:
        return False
    if not ok:
        return False
    if "Resource" in statement:
        ok = any(resource_matches(p, request.resource) for p in as_list(statement["Resource"]))
    elif "NotResource" in statement:
        ok = not any(resource_matches(p, request.resource) for p in as_list(statement["NotResource"]))
    else:
        ok = check_principal  # trust policies have no Resource; identity policies must
    return ok and condition_matches(statement.get("Condition"), request.context)


def _decide(policies, request: Request, check_principal: bool = False) -> str:
    allowed = False
    for policy in policies:
        for st in statements(policy):
            if statement_applies(st, request, check_principal=check_principal):
                if st.get("Effect") == "Deny":
                    return EXPLICIT_DENY
                if st.get("Effect") == "Allow":
                    allowed = True
    return ALLOW if allowed else IMPLICIT_DENY


def evaluate_policies(policies: list[dict], request: Request) -> str:
    """Identity-based policies only."""
    return _decide(policies, request)


def evaluate(request: Request, *, identity=(), resource_policy=None, scps=None, boundary=None,
             session=None, resource_account=None) -> str:
    identity = list(identity)
    every = identity + [p for p in (boundary, session) if p] + [p for level in (scps or []) for p in level]
    if _decide(every, request) == EXPLICIT_DENY:
        return EXPLICIT_DENY
    if resource_policy and _decide([resource_policy], request, check_principal=True) == EXPLICIT_DENY:
        return EXPLICIT_DENY
    for level in scps or []:
        if _decide(level, request) != ALLOW:
            return IMPLICIT_DENY
    identity_ok = _decide(identity, request) == ALLOW
    resource_ok = bool(resource_policy) and _decide([resource_policy], request, check_principal=True) == ALLOW
    caller_account = account_of(request.principal)
    target_account = resource_account or account_of(request.resource) or caller_account
    granted = (identity_ok and resource_ok) if caller_account != target_account else (identity_ok or resource_ok)
    if not granted:
        return IMPLICIT_DENY
    for limit in (boundary, session):
        if limit is not None and _decide([limit], request) != ALLOW:
            return IMPLICIT_DENY
    return ALLOW


def evaluate_trust(trust_policy: dict, caller_arn: str, context: dict | None = None) -> bool:
    """May caller_arn call sts:AssumeRole on the role with this trust policy?"""
    request = Request(principal=caller_arn, action="sts:AssumeRole", resource="*", context=context or {})
    return _decide([trust_policy], request, check_principal=True) == ALLOW
```

- [ ] **Step 4: Run the tests**

```bash
.venv/Scripts/python.exe -m pytest _dev/tests/test_policy_eval.py
```

Expected: `70 passed` (the parametrised cases count individually).

- [ ] **Step 5: Commit** — skipped (no git).

---

### Task 4: Quiz engine `quizlib.py` + `quiz.py`

**Files:**
- Create: `_harness/quizlib.py`, `quiz.py`
- Test: `_dev/tests/bankgen.py` (shared bank builder, also used by Task 7 and later week plans), `_dev/tests/test_quizlib.py`

**Interfaces:**
- Consumes: `awslib.safety.force_utf8`.
- Produces (used by Task 5 `mock_exam.py`, Task 7 `verify_course.py`, every quiz bank):
  - Constants `DOMAINS: dict[int, str]`, `TASKS: dict[str, str]` (14 task statements), `LETTERS = "ABCDEF"`, `OPTION_COUNT = {1: 4, 2: 5, 3: 6}`, `RETIRED: dict[str, re.Pattern]`, `LEGACY: dict[str, re.Pattern]`.
  - `Question` (frozen dataclass: `id, domain, task, services, kind, choose, stem, options, answer: frozenset, explain: dict, ref, legacy, source`).
  - `BankError(ValueError)`; `validate_question(raw: dict, root: Path | None = None) -> list[str]`; `load_bank(path, root=None) -> list[Question]`; `bank_problems(questions, expected_count) -> list[str]`; `near_duplicates(questions, threshold=0.85) -> list[tuple[str, str, float]]`; `retired_hits(text) -> list[str]`; `legacy_hits(text) -> list[str]`.
  - `parse_answer(text, n_options, choose) -> tuple[list[str] | None, str]`; `shuffle_options(question, rng) -> list[tuple[str, str]]` (display letter, original letter); `grade(question, original_letters) -> bool`.
  - `Progress(path, today=None)` with `.record(qid, correct, today)`, `.box(qid)`, `.seen(qid)`, `.is_due(qid, today)`, `.save()`, `.data`, `.warning`.
  - `select_questions(questions, progress, n, today, rng, review=False) -> list[Question]`.
  - `run_session(questions, progress, *, input_fn=input, print_fn=print, rng=None, today=None) -> dict` (`asked`, `correct`, `quit`).
  - `discover_banks(root) -> dict[int, Path]`.

- [ ] **Step 0: Write `_dev/tests/bankgen.py`**

```python
"""bankgen — build valid (or deliberately broken) question banks for the maintainer tests."""
import json

from _harness import quizlib


def raw_single(n=1, domain=4, task="4.1", answer="A", stem=None, ref=None, week=4):
    return {
        "id": f"w{week:02d}-q{n:02d}", "domain": domain, "task": task, "services": ["S3"], "kind": "single",
        "stem": stem or (f"Question {n}: a company keeps logs in Amazon S3 and reads them for 30 days, then rarely. "
                         f"Variant {n * 7919 + week * 104729} of the scenario. Which solution is the MOST cost-effective?"),
        "options": [f"Option one {n}", f"Option two {n} longer", f"Option three {n}", f"Option four {n}"],
        "answer": [answer], "explain": {k: f"Because {k}." for k in "ABCD"},
        "ref": ref or "week_04_storage/concepts/01_s3.md",
    }


def raw_multi(n=2, choose=2, ref=None, week=4):
    q = raw_single(n, ref=ref, week=week)
    letters = quizlib.LETTERS[: quizlib.OPTION_COUNT[choose]]
    q.update(kind="multi", choose=choose, options=[f"Choice {c} {n}" for c in letters],
             answer=list(letters[:choose]), explain={c: f"Because {c}." for c in letters},
             stem=q["stem"].replace("Which solution is the MOST cost-effective?",
                                    "Which steps meet these requirements? " + quizlib.SELECT_SUFFIX[choose]))
    return q


def balanced_raws(n=30, multi=4, week=4, ref=None):
    """A bank that passes quizlib.bank_problems: spread answers, the correct option is never the longest."""
    raws = []
    for i in range(1, n + 1):
        if i <= multi:
            raws.append(raw_multi(i, ref=ref, week=week))
            continue
        raw = raw_single(i, answer="ABCD"[i % 4], ref=ref, week=week)
        right = "ABCD".index(raw["answer"][0])
        raw["options"] = [f"Option {i}-{k}" + (" padded" if k == (right + 1) % 4 else "") for k in range(4)]
        raws.append(raw)
    return raws


def toml_bank(questions) -> str:
    lines = []
    for q in questions:
        lines.append("[[question]]")
        for key, value in q.items():
            if key == "explain":
                lines.append("explain = { " + ", ".join(f"{k} = {json.dumps(v)}" for k, v in value.items()) + " }")
            else:
                lines.append(f"{key} = {json.dumps(value)}")
        lines.append("")
    return "\n".join(lines)
```

- [ ] **Step 1: Write the failing tests `_dev/tests/test_quizlib.py`**

```python
import datetime as dt
import json
import os
import random
import subprocess
import sys
from pathlib import Path

import pytest

from _harness import quizlib
from _harness.quizlib import (BankError, Progress, bank_problems, grade, load_bank, near_duplicates,
                              parse_answer, retired_hits, run_session, select_questions, shuffle_options,
                              validate_question)
from bankgen import balanced_raws, raw_multi, raw_single, toml_bank

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
TODAY = dt.date(2026, 10, 8)


def to_questions(raws):
    return [quizlib.Question.from_raw(r) for r in raws]


def test_valid_single_and_multi():
    assert validate_question(raw_single()) == []
    assert validate_question(raw_multi(choose=2)) == []
    assert validate_question(raw_multi(choose=3)) == []


@pytest.mark.parametrize("change, problem", [
    ({"id": "bad id"}, "id"),
    ({"domain": 5}, "domain"),
    ({"task": "1.1"}, "task 1.1 is not in domain 4"),
    ({"task": "4.9"}, "unknown task"),
    ({"kind": "pick"}, "kind"),
    ({"options": ["a", "b", "c"]}, "4 options"),
    ({"options": ["a", "a", "b", "c"]}, "duplicate options"),
    ({"answer": ["E"]}, "answer letter"),
    ({"answer": ["A", "B"]}, "exactly 1"),
    ({"explain": {"A": "x", "B": "y", "C": "z"}}, "explain"),
    ({"stem": "Too short?"}, "stem"),
    ({"stem": "A long enough stem about storing logs in S3 for a long time without any question mark at the end."}, "end with"),
    ({"services": []}, "services"),
    ({"legacy": "yes"}, "legacy"),
])
def test_invalid_questions(change, problem):
    raw = {**raw_single(), **change}
    problems = validate_question(raw)
    assert any(problem in p for p in problems), problems


def test_multi_needs_select_suffix_and_counts():
    raw = raw_multi(choose=2)
    raw["stem"] = raw["stem"].replace("(Select TWO.)", "(Select THREE.)")
    assert any("(Select TWO.)" in p for p in validate_question(raw))
    raw = raw_multi(choose=2)
    raw["answer"] = ["A"]
    assert any("exactly 2" in p for p in validate_question(raw))


def test_ref_must_exist_when_root_given(tmp_path):
    (tmp_path / "week_04_storage" / "concepts").mkdir(parents=True)
    assert any("ref" in p for p in validate_question(raw_single(), root=tmp_path))
    (tmp_path / "week_04_storage" / "concepts" / "01_s3.md").write_text("x")
    assert validate_question(raw_single(), root=tmp_path) == []


def test_load_bank_reports_every_problem(tmp_path):
    path = tmp_path / "questions.toml"
    path.write_text(toml_bank([raw_single(1), {**raw_single(2), "domain": 9}, {**raw_single(3), "id": "w04-q01"}]),
                    encoding="utf-8")
    with pytest.raises(BankError) as info:
        load_bank(path)
    text = str(info.value)
    assert "w04-q02" in text and "duplicate id w04-q01" in text


def test_load_bank_reads_questions(tmp_path):
    path = tmp_path / "questions.toml"
    path.write_text(toml_bank([raw_single(1), raw_multi(2)]), encoding="utf-8")
    questions = load_bank(path)
    assert [q.id for q in questions] == ["w04-q01", "w04-q02"]
    assert questions[1].answer == frozenset({"A", "B"}) and questions[1].choose == 2
    assert questions[0].source == str(path)


def test_load_bank_bad_toml(tmp_path):
    path = tmp_path / "questions.toml"
    path.write_text("[[question]\nid = ", encoding="utf-8")
    with pytest.raises(BankError, match="TOML"):
        load_bank(path)


def balanced_bank(n=30, multi=4):
    return to_questions(balanced_raws(n, multi))


def test_bank_problems_clean_bank():
    assert bank_problems(balanced_bank(), expected_count=30) == []


def test_bank_problems_detects_count_multi_letters_and_longest():
    bank = balanced_bank(30, multi=0)
    problems = " | ".join(bank_problems(bank, expected_count=30))
    assert "multi-response" in problems
    one_letter = to_questions([raw_single(i, answer="A") for i in range(1, 31)])
    problems = " | ".join(bank_problems(one_letter, expected_count=31))
    assert "expected 31 questions" in problems and "letter A" in problems
    longest = []
    for i in range(1, 31):
        raw = raw_single(i, answer="ABCD"[i % 4])
        raw["options"] = [o + (" — clearly the longest option of all" if "ABCD"[k] == raw["answer"][0] else "")
                          for k, o in enumerate(raw["options"])]
        longest.append(raw)
    assert any("longest" in p for p in bank_problems(to_questions(longest), expected_count=30))


def test_near_duplicates():
    a = raw_single(1, stem="A company stores logs in Amazon S3 for seven years. Which storage class is the MOST cost-effective?")
    b = raw_single(2, stem="A company stores logs in Amazon S3 for seven years. Which storage class is MOST cost-effective?")
    c = raw_single(3, stem="An application needs single-digit millisecond reads from a key-value store at any scale. Which service fits?")
    pairs = near_duplicates(to_questions([a, b, c]))
    assert [(x, y) for x, y, _ in pairs] == [("w04-q01", "w04-q02")]


def test_retired_and_legacy_names():
    assert retired_hits("Use Amazon QLDB for the ledger") == ["Amazon QLDB"]
    assert retired_hits("Build a data pipeline with AWS Glue") == []  # the generic phrase is fine
    assert retired_hits("Create a launch configuration") == ["launch configurations"]
    assert quizlib.legacy_hits("Order an AWS Snowball Edge device") == ["Snowball Edge"]


def test_retired_service_in_bank_is_a_problem():
    raw = raw_single(1)
    raw["options"][0] = "Store the ledger in Amazon QLDB"
    assert any("retired" in p for p in bank_problems(to_questions([raw]), expected_count=1))
    raw = raw_single(2)
    raw["options"][0] = "Ship the data with AWS Snowball Edge"
    assert any("legacy" in p for p in bank_problems(to_questions([raw]), expected_count=1))
    raw["legacy"] = True
    assert not any("legacy" in p for p in bank_problems(to_questions([raw]), expected_count=1))


@pytest.mark.parametrize("text, n, choose, letters, error", [
    ("b", 4, 1, ["B"], ""), (" B ", 4, 1, ["B"], ""), ("a, c", 5, 2, ["A", "C"], ""), ("ca", 5, 2, ["A", "C"], ""),
    ("", 4, 1, None, "letter"), ("e", 4, 1, None, "A–D"), ("ab", 4, 1, None, "one letter"),
    ("a", 5, 2, None, "exactly 2"), ("aa", 5, 2, None, "once"), ("a1", 5, 2, None, "A–E"),
])
def test_parse_answer_variants(text, n, choose, letters, error):
    got, message = parse_answer(text, n, choose)
    assert got == letters
    assert (error in message) if error else message == ""


def test_shuffle_maps_back_to_original_letters():
    q = to_questions([raw_single(1, answer="C")])[0]
    mapping = shuffle_options(q, random.Random(3))
    assert sorted(o for _, o in mapping) == list("ABCD") and [d for d, _ in mapping] == list("ABCD")
    display_for_c = next(d for d, o in mapping if o == "C")
    original = [dict(mapping)[display_for_c]]
    assert grade(q, original) and not grade(q, ["A"] if original != ["A"] else ["B"])


def test_progress_boxes_and_due(tmp_path):
    p = Progress(tmp_path / "progress.json", today=TODAY)
    assert not p.seen("w04-q01")
    p.record("w04-q01", True, TODAY)
    assert p.box("w04-q01") == 2 and not p.is_due("w04-q01", TODAY)
    assert p.is_due("w04-q01", TODAY + dt.timedelta(days=1))
    p.record("w04-q01", True, TODAY)
    assert p.box("w04-q01") == 3
    p.record("w04-q01", False, TODAY)
    assert p.box("w04-q01") == 1 and p.is_due("w04-q01", TODAY)
    for _ in range(9):
        p.record("w04-q02", True, TODAY)
    assert p.box("w04-q02") == 5


def test_save_is_atomic_and_reloads(tmp_path):
    path = tmp_path / "sub" / "progress.json"
    p = Progress(path, today=TODAY)
    p.record("w04-q01", False, TODAY)
    p.save()
    assert not list(path.parent.glob("*.tmp"))
    assert Progress(path, today=TODAY).box("w04-q01") == 1


def test_corrupt_progress_is_backed_up(tmp_path):
    path = tmp_path / "progress.json"
    path.write_text('{"questions": {"w04-q01": {"box": 3', encoding="utf-8")
    p = Progress(path, today=TODAY)
    assert p.warning and "backed up" in p.warning
    assert p.data["questions"] == {}
    assert len(list(tmp_path.glob("progress.json.bad-*"))) == 1


def test_select_missed_first_then_unseen(tmp_path):
    bank = to_questions([raw_single(i) for i in range(1, 7)])
    p = Progress(tmp_path / "p.json", today=TODAY)
    p.record("w04-q05", False, TODAY)     # missed
    p.record("w04-q06", True, TODAY)      # seen, not due today
    chosen = select_questions(bank, p, 3, TODAY, random.Random(1))
    assert chosen[0].id == "w04-q05" and "w04-q06" not in [q.id for q in chosen]
    review = select_questions(bank, p, 10, TODAY, random.Random(1), review=True)
    assert [q.id for q in review] == ["w04-q05"]


def test_session_reprompts_on_bad_input(tmp_path):
    bank = to_questions([raw_single(1, answer="B")])
    p = Progress(tmp_path / "p.json", today=TODAY)
    mapping = shuffle_options(bank[0], random.Random(5))
    right = next(d for d, o in mapping if o == "B").lower()
    answers = iter(["", "zz", "ab", right])
    out = []
    summary = run_session(bank, p, input_fn=lambda prompt: next(answers), print_fn=out.append,
                          rng=random.Random(5), today=TODAY)
    text = "\n".join(out)
    assert summary == {"asked": 1, "correct": 1, "quit": False}
    assert "Use letters A–D" in text and "one letter" in text and "✔ Correct" in text
    assert "Because B." in text and "Read more: week_04_storage/concepts/01_s3.md" in text
    assert p.box("w04-q01") == 2


def test_session_quit_and_eof(tmp_path):
    bank = to_questions([raw_single(1), raw_single(2)])
    p = Progress(tmp_path / "p.json", today=TODAY)
    summary = run_session(bank, p, input_fn=lambda prompt: "q", print_fn=lambda *_: None, rng=random.Random(1), today=TODAY)
    assert summary == {"asked": 0, "correct": 0, "quit": True}

    def eof(prompt):
        raise EOFError
    assert run_session(bank, p, input_fn=eof, print_fn=lambda *_: None, rng=random.Random(1), today=TODAY)["quit"]


def make_course(tmp_path) -> Path:
    week = tmp_path / "course" / "week_04_storage"
    (week / "quiz").mkdir(parents=True)
    (week / "concepts").mkdir()
    (week / "concepts" / "01_s3.md").write_text("notes", encoding="utf-8")  # every question's ref must exist
    (week / "quiz" / "questions.toml").write_text(toml_bank([raw_single(i) for i in range(1, 4)]), encoding="utf-8")
    return tmp_path / "course"


def test_discover_banks(tmp_path):
    root = make_course(tmp_path)
    assert quizlib.discover_banks(root) == {4: root / "week_04_storage" / "quiz" / "questions.toml"}


def test_quiz_cli_piped(tmp_path):
    root = make_course(tmp_path)
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
    proc = subprocess.run([PY, str(ROOT / "quiz.py"), "--root", str(root), "--week", "4", "-n", "2", "--seed", "1"],
                          input=b"a\nq\n", capture_output=True, env=env, timeout=120)
    out = proc.stdout.decode("utf-8")
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    assert "Question 1 of 2" in out and ("✔ Correct" in out or "✘ Not quite" in out)
    assert (root / "_progress" / "progress.json").exists()
    stats = subprocess.run([PY, str(ROOT / "quiz.py"), "--root", str(root), "--stats"], capture_output=True, env=env, timeout=120)
    assert "Design Cost-Optimized Architectures" in stats.stdout.decode("utf-8")


def test_quiz_cli_missing_week(tmp_path):
    root = make_course(tmp_path)
    proc = subprocess.run([PY, str(ROOT / "quiz.py"), "--root", str(root), "--week", "7"], capture_output=True, timeout=120)
    assert proc.returncode == 2 and "no quiz for week 07" in proc.stdout.decode("utf-8")
```

- [ ] **Step 2: Run them to see them fail**

```bash
.venv/Scripts/python.exe -m pytest _dev/tests/test_quizlib.py
```

Expected: `ImportError: cannot import name 'quizlib'`.

- [ ] **Step 3: Write `_harness/quizlib.py`**

```python
"""quizlib — load, validate, run and track the course's scenario-question banks (TOML).

One [[question]] table per question:
    id        "w04-q07" (weekly bank) or "mock1-q42" (mock exam)
    domain    1 Secure · 2 Resilient · 3 High-performing · 4 Cost-optimised
    task      exam task statement, e.g. "4.1" — must belong to the domain
    services  list of AWS services the question is about (non-empty)
    kind      "single" (4 options, 1 answer) or "multi" (choose = 2 → 5 options, 3 → 6 options)
    stem      2–6 sentences; single ends with "?", multi ends with "(Select TWO.)"/"(Select THREE.)"
    options   option texts in order A, B, C, …
    answer    list of correct letters
    explain   table: one explanation per option letter (why right / why wrong)
    ref       course-relative path of the concept note that teaches it
    legacy    optional bool: true when a correct answer is a service closed to new customers (spec §7)
"""
from __future__ import annotations

import datetime as dt
import difflib
import json
import os
import random
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

DOMAINS = {1: "Design Secure Architectures", 2: "Design Resilient Architectures",
           3: "Design High-Performing Architectures", 4: "Design Cost-Optimized Architectures"}
TASKS = {
    "1.1": "Design secure access to AWS resources",
    "1.2": "Design secure workloads and applications",
    "1.3": "Determine appropriate data security controls",
    "2.1": "Design scalable and loosely coupled architectures",
    "2.2": "Design highly available and/or fault-tolerant architectures",
    "3.1": "Determine high-performing and/or scalable storage solutions",
    "3.2": "Design high-performing and elastic compute solutions",
    "3.3": "Determine high-performing database solutions",
    "3.4": "Determine high-performing and/or scalable network architectures",
    "3.5": "Determine high-performing data ingestion and transformation solutions",
    "4.1": "Design cost-optimized storage solutions",
    "4.2": "Design cost-optimized compute solutions",
    "4.3": "Design cost-optimized database solutions",
    "4.4": "Design cost-optimized network architectures",
}
LETTERS = "ABCDEF"
OPTION_COUNT = {1: 4, 2: 5, 3: 6}
SELECT_SUFFIX = {2: "(Select TWO.)", 3: "(Select THREE.)"}
ID_PATTERN = re.compile(r"^(w\d\d|mock\d)-q\d{2,3}$")
LEITNER_DAYS = {1: 0, 2: 1, 3: 3, 4: 7, 5: 16}
REQUIRED = ("id", "domain", "task", "services", "kind", "stem", "options", "answer", "explain", "ref")

# spec §7 rule 1 — never in a bank, only on "retired" lines in notes (case-sensitive proper names)
RETIRED = {name: re.compile(rx) for name, rx in {
    "Amazon QLDB": r"\bQLDB\b",
    "Elastic Transcoder": r"\bElastic Transcoder\b",
    "AWS Data Pipeline": r"\bAWS Data Pipeline\b",
    "AWS Proton": r"\bAWS Proton\b",
    "Amazon Pinpoint": r"\bAmazon Pinpoint\b",
    "AWS OpsWorks": r"\bOpsWorks\b",
    "EC2-Classic": r"\bEC2-Classic\b",
    "Aurora Serverless v1": r"\bAurora Serverless v1\b",
    "Kinesis Data Analytics": r"\bKinesis Data Analytics\b",
    "WAF Classic": r"\bWAF Classic\b",
    "Inspector Classic": r"\bInspector Classic\b",
    "Snowmobile": r"\bSnowmobile\b",
    "Snowcone": r"\bSnowcone\b",
    "launch configurations": r"\b[Ll]aunch [Cc]onfigurations?\b",
    "S3 Select": r"\bS3 Select\b",
    "Glacier vaults": r"\bGlacier [Vv]aults?\b|\bVault Lock\b",
    "AWS Cloud9": r"\bCloud9\b",
    "AWS App Mesh": r"\bApp Mesh\b",
}.items()}
# spec §7 rule 2 — allowed as a correct answer only in questions marked legacy = true
LEGACY = {name: re.compile(rx) for name, rx in {
    "Snowball Edge": r"\bSnowball\b",
    "Application Discovery Service": r"\bApplication Discovery Service\b",
    "Migration Hub": r"\bMigration Hub\b",
}.items()}


class BankError(ValueError):
    """A bank file could not be loaded; the message lists every problem."""


@dataclass(frozen=True)
class Question:
    id: str
    domain: int
    task: str
    services: tuple
    kind: str
    choose: int
    stem: str
    options: tuple
    answer: frozenset
    explain: dict = field(hash=False, compare=False)
    ref: str = ""
    legacy: bool = False
    source: str = ""

    @classmethod
    def from_raw(cls, raw: dict, source: str = "") -> "Question":
        choose = raw.get("choose", 1) if raw.get("kind") == "multi" else 1
        return cls(id=raw["id"], domain=raw["domain"], task=raw["task"], services=tuple(raw["services"]),
                   kind=raw["kind"], choose=choose, stem=raw["stem"].strip(), options=tuple(raw["options"]),
                   answer=frozenset(raw["answer"]), explain=dict(raw["explain"]), ref=raw["ref"],
                   legacy=bool(raw.get("legacy", False)), source=source)


def retired_hits(text: str) -> list[str]:
    return [name for name, rx in RETIRED.items() if rx.search(text)]


def legacy_hits(text: str) -> list[str]:
    return [name for name, rx in LEGACY.items() if rx.search(text)]


def validate_question(raw: dict, root: Path | None = None) -> list[str]:
    qid = raw.get("id", "<no id>")
    problems = [f"missing {key}" for key in REQUIRED if key not in raw]
    if problems:
        return [f"{qid}: {p}" for p in problems]
    p = problems
    if not isinstance(raw["id"], str) or not ID_PATTERN.match(raw["id"]):
        p.append("id must look like w04-q07 or mock1-q42")
    if raw["domain"] not in DOMAINS:
        p.append("domain must be 1, 2, 3 or 4")
    if raw["task"] not in TASKS:
        p.append(f"unknown task {raw['task']!r}")
    elif raw["domain"] in DOMAINS and not raw["task"].startswith(f"{raw['domain']}."):
        p.append(f"task {raw['task']} is not in domain {raw['domain']}")
    if not isinstance(raw["services"], list) or not raw["services"] or not all(isinstance(s, str) and s for s in raw["services"]):
        p.append("services must be a non-empty list of names")
    if "legacy" in raw and not isinstance(raw["legacy"], bool):
        p.append("legacy must be true or false")
    if raw["kind"] not in ("single", "multi"):
        p.append("kind must be single or multi")
        return [f"{qid}: {x}" for x in p]
    choose = raw.get("choose", 1) if raw["kind"] == "multi" else 1
    if raw["kind"] == "multi" and choose not in (2, 3):
        p.append("multi questions need choose = 2 or 3")
        return [f"{qid}: {x}" for x in p]
    if raw["kind"] == "single" and raw.get("choose", 1) != 1:
        p.append("single questions must not set choose")
    want = OPTION_COUNT[choose]
    options = raw["options"]
    if not isinstance(options, list) or len(options) != want:
        p.append(f"needs {want} options")
    elif len(set(options)) != len(options) or not all(isinstance(o, str) and o.strip() for o in options):
        p.append("duplicate options or empty option text")
    letters = LETTERS[:want]
    answer = raw["answer"]
    if not isinstance(answer, list) or any(a not in letters for a in answer) or len(set(answer)) != len(answer):
        p.append(f"answer letters must be distinct letters from {letters}")
    elif len(answer) != choose:
        p.append(f"answer must have exactly {choose} letter(s)")
    explain = raw["explain"]
    if not isinstance(explain, dict) or set(explain) != set(letters) or not all(isinstance(v, str) and v.strip() for v in explain.values()):
        p.append(f"explain needs one non-empty text for each of {', '.join(letters)}")
    stem = raw["stem"].strip() if isinstance(raw["stem"], str) else ""
    if not 80 <= len(stem) <= 1200:
        p.append("stem must be a 2–6 sentence scenario (80–1200 characters)")
    ending = SELECT_SUFFIX[choose] if choose > 1 else "?"
    if stem and not stem.endswith(ending):
        p.append(f"stem must end with {ending}")
    if root is not None and isinstance(raw["ref"], str) and not (Path(root) / raw["ref"]).is_file():
        p.append(f"ref {raw['ref']} does not exist")
    return [f"{qid}: {x}" for x in p]


def load_bank(path, root=None) -> list[Question]:
    path = Path(path)
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise BankError(f"{path}: cannot read TOML: {exc}") from None
    raws = data.get("question", [])
    problems, seen = [], set()
    for raw in raws:
        problems += validate_question(raw, root)
        qid = raw.get("id")
        if qid in seen:
            problems.append(f"duplicate id {qid}")
        seen.add(qid)
    if problems:
        raise BankError(f"{path}:\n  " + "\n  ".join(problems))
    return [Question.from_raw(raw, str(path)) for raw in raws]


def _longest_is_correct(q: Question) -> bool:
    lengths = [len(o) for o in q.options]
    best = max(lengths)
    winners = [LETTERS[i] for i, n in enumerate(lengths) if n == best]
    return len(winners) == 1 and winners[0] in q.answer


def bank_problems(questions: list[Question], expected_count: int) -> list[str]:
    """Bank-level rules from spec §4.3 (count, multi share, answer-letter spread, longest-option bias,
    retired/legacy names, legacy cap)."""
    n = len(questions)
    problems = []
    if n != expected_count:
        problems.append(f"expected {expected_count} questions, found {n}")
    multi = sum(q.kind == "multi" for q in questions)
    low, high = int(0.10 * n), -(-n * 20 // 100)
    if n >= 10 and not low <= multi <= high:
        problems.append(f"{multi} multi-response questions; need {low}–{high} (10–20 %)")
    singles = [q for q in questions if q.kind == "single"]
    if len(singles) >= 12:
        counts = {letter: sum(letter in q.answer for q in singles) for letter in "ABCD"}
        cap, floor = -(-len(singles) * 40 // 100), int(0.10 * len(singles))
        for letter, count in counts.items():
            if count > cap or count < floor:
                problems.append(f"letter {letter} is the answer {count} times out of {len(singles)}; keep each between {floor} and {cap}")
        longest = sum(_longest_is_correct(q) for q in singles)
        if longest > 0.40 * len(singles):
            problems.append(f"the correct option is the longest in {longest} of {len(singles)} single questions (max 40 %)")
    legacy_cap = max(1, int(0.02 * n))
    if sum(q.legacy for q in questions) > legacy_cap:
        problems.append(f"more than {legacy_cap} legacy questions")
    for q in questions:
        text = " ".join([q.stem, *q.options, *q.explain.values()])
        for name in retired_hits(text):
            problems.append(f"{q.id}: mentions retired {name} (spec §7 rule 1)")
        correct = " ".join(q.options[LETTERS.index(a)] for a in q.answer)
        if legacy_hits(correct) and not q.legacy:
            problems.append(f"{q.id}: correct answer uses {', '.join(legacy_hits(correct))} — mark legacy = true (spec §7 rule 2)")
    return problems


def _norm(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", text.lower()).split())


def near_duplicates(questions: list[Question], threshold: float = 0.85) -> list[tuple[str, str, float]]:
    stems = [(q.id, _norm(q.stem)) for q in questions]
    found = []
    for i, (id_a, a) in enumerate(stems):
        for id_b, b in stems[i + 1:]:
            matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
            if matcher.real_quick_ratio() < threshold or matcher.quick_ratio() < threshold:
                continue
            ratio = matcher.ratio()
            if ratio >= threshold:
                found.append((id_a, id_b, round(ratio, 3)))
    return found


# ── answering ───────────────────────────────────────────────────────


def parse_answer(text: str, n_options: int, choose: int) -> tuple[list[str] | None, str]:
    allowed = LETTERS[:n_options]
    cleaned = re.sub(r"[\s,;/]+", "", text or "").upper()
    if not cleaned:
        return None, "Type the letter of your answer (or q to quit)."
    if any(c not in allowed for c in cleaned):
        return None, f"Use letters {allowed[0]}–{allowed[-1]}."
    if len(set(cleaned)) != len(cleaned):
        return None, "Use each letter once."
    if len(cleaned) != choose:
        return None, "Pick one letter." if choose == 1 else f"Pick exactly {choose} letters."
    return sorted(cleaned), ""


def shuffle_options(question: Question, rng: random.Random) -> list[tuple[str, str]]:
    originals = list(LETTERS[:len(question.options)])
    rng.shuffle(originals)
    return list(zip(LETTERS, originals))


def grade(question: Question, original_letters) -> bool:
    return frozenset(original_letters) == question.answer


# ── progress (Leitner boxes) ────────────────────────────────────────


class Progress:
    """Per-question Leitner box (1 = missed … 5 = well known) and due date, saved atomically."""

    def __init__(self, path, today: dt.date | None = None):
        self.path = Path(path)
        self.warning = ""
        self.data = {"version": 1, "questions": {}, "sessions": [], "mocks": []}
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
                if not isinstance(loaded, dict) or not isinstance(loaded.get("questions"), dict):
                    raise ValueError("unexpected shape")
                self.data.update(loaded)
            except (ValueError, OSError):
                stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
                backup = self.path.with_name(f"{self.path.name}.bad-{stamp}")
                os.replace(self.path, backup)
                self.warning = f"Your progress file was damaged; it was backed up to {backup.name} and a fresh one started."

    def _entry(self, qid: str) -> dict:
        return self.data["questions"].get(qid, {})

    def seen(self, qid: str) -> bool:
        return bool(self._entry(qid))

    def box(self, qid: str) -> int:
        return self._entry(qid).get("box", 0)

    def is_due(self, qid: str, today: dt.date) -> bool:
        due = self._entry(qid).get("due")
        return due is not None and dt.date.fromisoformat(due) <= today

    def record(self, qid: str, correct: bool, today: dt.date) -> None:
        entry = self.data["questions"].setdefault(qid, {"box": 0, "seen": 0, "right": 0})
        entry["seen"] += 1
        entry["right"] += int(correct)
        entry["box"] = min(5, max(entry["box"], 1) + 1) if correct else 1
        entry["due"] = (today + dt.timedelta(days=LEITNER_DAYS[entry["box"]])).isoformat()
        entry["last"] = today.isoformat()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps(self.data, indent=1), encoding="utf-8")
        os.replace(tmp, self.path)


def select_questions(questions, progress: Progress, n: int, today: dt.date, rng: random.Random,
                     review: bool = False) -> list[Question]:
    missed = [q for q in questions if progress.seen(q.id) and progress.box(q.id) == 1]
    due = [q for q in questions if progress.seen(q.id) and progress.box(q.id) > 1 and progress.is_due(q.id, today)]
    unseen = [q for q in questions if not progress.seen(q.id)]
    rest = [q for q in questions if q not in missed and q not in due and q not in unseen]
    for group in (missed, due, unseen, rest):
        rng.shuffle(group)
    ordered = missed + due if review else missed + unseen + due + rest
    return ordered[:n]


# ── a terminal session ──────────────────────────────────────────────


def render_question(q: Question, mapping, number: int, total: int) -> str:
    lines = [f"\nQuestion {number} of {total}  ·  Domain {q.domain}: {DOMAINS[q.domain]}  ·  task {q.task}", "", q.stem, ""]
    for display, original in mapping:
        lines.append(f"  {display}. {q.options[LETTERS.index(original)]}")
    return "\n".join(lines)


def render_feedback(q: Question, mapping, correct: bool) -> str:
    right = [d for d, o in mapping if o in q.answer]
    lines = ["", "✔ Correct" if correct else f"✘ Not quite — the answer is {', '.join(right)}", ""]
    for display, original in mapping:
        mark = "✔" if original in q.answer else "·"
        lines.append(f"  {mark} {display}. {q.explain[original]}")
    if q.legacy:
        lines.append("  (legacy: this service is closed to new customers in 2026 but still in the exam guide)")
    lines.append(f"\n  Read more: {q.ref}")
    return "\n".join(lines)


def run_session(questions, progress: Progress, *, input_fn=input, print_fn=print, rng=None, today=None) -> dict:
    rng = rng or random.Random()
    today = today or dt.date.today()
    if progress.warning:
        print_fn(progress.warning)
    asked = correct_count = 0
    quit_ = False
    for number, q in enumerate(questions, 1):
        mapping = shuffle_options(q, rng)
        print_fn(render_question(q, mapping, number, len(questions)))
        prompt = "\nYour answer (one letter, q to quit): " if q.choose == 1 else f"\nYour answer (pick {q.choose}, e.g. AC; q to quit): "
        while True:
            try:
                text = input_fn(prompt)
            except EOFError:
                text = "q"
            if text.strip().lower() == "q":
                quit_ = True
                break
            letters, message = parse_answer(text, len(q.options), q.choose)
            if letters is not None:
                break
            print_fn(message)
        if quit_:
            break
        originals = [dict(mapping)[d] for d in letters]
        ok = grade(q, originals)
        progress.record(q.id, ok, today)
        asked += 1
        correct_count += ok
        print_fn(render_feedback(q, mapping, ok))
    if asked:
        progress.data["sessions"].append({"date": today.isoformat(), "asked": asked, "correct": correct_count})
        print_fn(f"\nScore: {correct_count}/{asked} ({round(100 * correct_count / asked)}%)")
    progress.save()
    return {"asked": asked, "correct": correct_count, "quit": quit_}


def discover_banks(root) -> dict[int, Path]:
    banks = {}
    for path in sorted(Path(root).glob("week_[0-9][0-9]_*/quiz/questions.toml")):
        banks[int(path.parts[-3][5:7])] = path
    return banks
```

- [ ] **Step 4: Write `quiz.py`**

```python
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
```

- [ ] **Step 5: Run the tests**

```bash
.venv/Scripts/python.exe -m pytest _dev/tests/test_quizlib.py
```

Expected: every test passes. In `test_quiz_cli_piped` the first answer `a` may be right or wrong (options are shuffled); the second question is quit with `q`, and the session is saved.

- [ ] **Step 6: Commit** — skipped (no git).

---

### Task 5: Mock-exam runner `exam_prep/mock_exam.py`

**Files:**
- Create: `exam_prep/mock_exam.py`
- Test: `_dev/tests/test_mock_exam.py`

**Interfaces:**
- Consumes: `quizlib.load_bank`, `quizlib.shuffle_options`, `quizlib.parse_answer`, `quizlib.grade`, `quizlib.Progress`, `quizlib.DOMAINS`, `quizlib.TASKS`, `quizlib.LETTERS`; `awslib.safety.force_utf8`.
- Produces: `DURATION_S = 130 * 60`, `DOMAIN_SPLIT = {1: 20, 2: 17, 3: 15, 4: 13}`, `PASS_GUIDE = 72`; `mock_problems(questions) -> list[str]`; `class MockExam(questions, rng, clock=time.monotonic, duration=DURATION_S)` with `.run(input_fn=input, print_fn=print) -> dict` (answers by question id → set of original letters); `score_report(questions, answers) -> dict`; `review_markdown(questions, answers, report) -> str`; CLI `python exam_prep/mock_exam.py N [--untimed] [--seed S]`.

- [ ] **Step 1: Write the failing tests `_dev/tests/test_mock_exam.py`**

```python
import importlib.util
import json
import os
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
spec = importlib.util.spec_from_file_location("mock_exam", ROOT / "exam_prep" / "mock_exam.py")
mock_exam = importlib.util.module_from_spec(spec)
sys.modules["mock_exam"] = mock_exam
spec.loader.exec_module(mock_exam)

from _harness import quizlib  # noqa: E402

TASK_OF = {1: "1.1", 2: "2.2", 3: "3.3", 4: "4.1"}


def raw(n, domain, multi=False):
    stem = (f"Mock question {n}: a company runs workload {n * 104729} on AWS in domain {domain} and needs a change. "
            + ("Which steps meet these requirements? (Select TWO.)" if multi else "Which solution meets these requirements?"))
    letters = "ABCDE" if multi else "ABCD"
    return {"id": f"mock1-q{n:02d}", "domain": domain, "task": TASK_OF[domain], "services": ["EC2"],
            "kind": "multi" if multi else "single", **({"choose": 2} if multi else {}), "stem": stem,
            "options": [f"Option {c} for {n}" for c in letters], "answer": ["A", "B"] if multi else ["ABCD"[n % 4]],
            "explain": {c: f"Explanation {c}." for c in letters}, "ref": "week_00_x/concepts/01.md"}


def full_bank():
    raws, n = [], 0
    for domain, count in mock_exam.DOMAIN_SPLIT.items():
        for i in range(count):
            n += 1
            raws.append(raw(n, domain, multi=(i < 2)))
    return raws


def toml(raws):
    out = []
    for q in raws:
        out.append("[[question]]")
        for k, v in q.items():
            out.append("explain = { " + ", ".join(f'{a} = "{b}"' for a, b in v.items()) + " }" if k == "explain" else f"{k} = {json.dumps(v)}")
        out.append("")
    return "\n".join(out)


def questions():
    return [quizlib.Question.from_raw(r) for r in full_bank()]


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def correct_display(exam, index):
    q = exam.questions[index]
    return "".join(d for d, o in exam.mappings[index] if o in q.answer).lower()


def test_mock_problems():
    assert mock_exam.mock_problems(questions()) == []
    short = questions()[:-1]
    assert any("65" in p for p in mock_exam.mock_problems(short))


def test_score_report_counts_unanswered_as_wrong():
    qs = questions()
    answers = {q.id: set(q.answer) for q in qs[:52]}
    report = mock_exam.score_report(qs, answers)
    assert report["correct"] == 52 and report["total"] == 65 and report["pct"] == 80
    assert report["passed_guide"] is True
    assert report["domains"][4] == {"correct": 0, "total": 13, "pct": 0}
    assert report["unanswered"] == 13


def test_run_answer_flag_navigate_review_submit():
    qs = questions()
    clock = Clock()
    exam = mock_exam.MockExam(qs, random.Random(2), clock=clock)
    script = [correct_display(exam, 0), "f", "p", "n", "g 65", "r", "s", "y"]
    # after answering Q1 the exam moves to Q2; "f" flags Q2; "p" goes back to Q1; "n" → Q2;
    # "g 65" jumps to the last question; "r" shows the review screen; "s" submits; "y" confirms
    feed = iter(script)
    out = []
    answers = exam.run(input_fn=lambda prompt: next(feed), print_fn=out.append)
    text = "\n".join(out)
    first, second = exam.questions[0], exam.questions[1]  # the exam shuffles question order
    assert answers == {first.id: set(first.answer)}
    assert second.id in exam.flags
    assert "Review" in text and "unanswered: 64" in text and "flagged: 1" in text


def test_time_up_submits():
    qs = questions()
    clock = Clock()
    exam = mock_exam.MockExam(qs, random.Random(2), clock=clock)

    def answer(prompt):
        clock.t += 131 * 60
        return correct_display(exam, exam.current)
    out = []
    answers = exam.run(input_fn=answer, print_fn=out.append)
    assert "Time is up" in "\n".join(out)
    assert len(answers) <= 1


def test_untimed_never_expires():
    exam = mock_exam.MockExam(questions(), random.Random(2), clock=Clock(), duration=None)
    assert exam.remaining() is None


def test_review_markdown_lists_missed():
    qs = questions()
    report = mock_exam.score_report(qs, {})
    text = mock_exam.review_markdown(qs, {}, report)
    assert text.count("### ") == 65 and "Explanation A." in text and "Domain 1" in text


def test_mock_cli_piped(tmp_path):
    course = tmp_path / "course"
    (course / "exam_prep" / "mock_exams").mkdir(parents=True)
    (course / "exam_prep" / "mock_exams" / "mock_1.toml").write_text(toml(full_bank()), encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
    proc = subprocess.run([PY, str(ROOT / "exam_prep" / "mock_exam.py"), "1", "--root", str(course), "--seed", "1"],
                          input=b"a\ns\ny\n", capture_output=True, env=env, timeout=120)
    out = proc.stdout.decode("utf-8")
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    assert "Score:" in out and "Domain 1" in out
    assert list((course / "_progress").glob("mock_1_*.md"))
    progress = json.loads((course / "_progress" / "progress.json").read_text(encoding="utf-8"))
    assert progress["mocks"][0]["mock"] == 1


def test_mock_cli_missing_bank(tmp_path):
    proc = subprocess.run([PY, str(ROOT / "exam_prep" / "mock_exam.py"), "2", "--root", str(tmp_path)],
                          capture_output=True, timeout=120)
    assert proc.returncode == 2 and "Mock exam 2 is not built yet" in proc.stdout.decode("utf-8")
```

- [ ] **Step 2: Run them to see them fail**

```bash
.venv/Scripts/python.exe -m pytest _dev/tests/test_mock_exam.py
```

Expected: `FileNotFoundError` for `exam_prep/mock_exam.py`.

- [ ] **Step 3: Write `exam_prep/mock_exam.py`**

```python
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
```

- [ ] **Step 4: Run the tests**

```bash
.venv/Scripts/python.exe -m pytest _dev/tests/test_mock_exam.py
```

Expected: `8 passed`. In `test_time_up_submits` the first input advances the fake clock past 130 minutes, so the answer typed at that prompt is discarded and the exam submits — `answers` is empty (the assertion allows ≤ 1).

- [ ] **Step 5: Commit** — skipped (no git).

---

### Task 6: Lab-cleanup library `_harness/labclean.py`

**Files:**
- Create: `_harness/labclean.py`
- Test: `_dev/tests/test_labclean.py`

**Interfaces:**
- Consumes: boto3 (real or moto). Must NOT import `awsdrill` or call `use_fake_aws_env` — it is meant for the learner's real account.
- Produces: `TAG_KEY = "saa-course"`, `TAG_VALUE = "lab"`; `Found(kind, name, region, delete)` dataclass; `FINDERS: dict[str, Callable[[session, region], list[Found]]]` with keys `"s3_buckets"`, `"iam_roles"`, `"iam_policies"`, `"iam_users"`; `main(kinds, argv=None, session_factory=None) -> int`. Every lab's `cleanup.py` calls `main(kinds=[...])`.

- [ ] **Step 1: Write the failing tests `_dev/tests/test_labclean.py`**

```python
import json

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from _harness import labclean

TAG = [{"Key": "saa-course", "Value": "lab"}]


@pytest.fixture
def aws():
    with mock_aws():
        yield boto3.Session(region_name="us-east-1")


def seed(session):
    s3 = session.client("s3")
    for name, tagged in (("lab-bucket-1", True), ("my-real-bucket", False)):
        s3.create_bucket(Bucket=name)
        if tagged:
            s3.put_bucket_tagging(Bucket=name, Tagging={"TagSet": TAG})
    s3.put_bucket_versioning(Bucket="lab-bucket-1", VersioningConfiguration={"Status": "Enabled"})
    s3.put_object(Bucket="lab-bucket-1", Key="a.txt", Body=b"1")
    s3.put_object(Bucket="lab-bucket-1", Key="a.txt", Body=b"2")
    s3.delete_object(Bucket="lab-bucket-1", Key="a.txt")  # leaves a delete marker
    eu = session.client("s3", region_name="eu-west-1")
    eu.create_bucket(Bucket="lab-bucket-eu", CreateBucketConfiguration={"LocationConstraint": "eu-west-1"})
    eu.put_bucket_tagging(Bucket="lab-bucket-eu", Tagging={"TagSet": TAG})
    iam = session.client("iam")
    trust = json.dumps({"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "ec2.amazonaws.com"}, "Action": "sts:AssumeRole"}]})
    iam.create_role(RoleName="lab-role", AssumeRolePolicyDocument=trust, Tags=TAG)
    iam.create_role(RoleName="prod-role", AssumeRolePolicyDocument=trust)
    iam.put_role_policy(RoleName="lab-role", PolicyName="inline", PolicyDocument=json.dumps({"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "s3:ListBucket", "Resource": "*"}]}))
    pol = iam.create_policy(PolicyName="lab-policy", Tags=TAG, PolicyDocument=json.dumps({"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "s3:GetObject", "Resource": "*"}]}))
    iam.attach_role_policy(RoleName="lab-role", PolicyArn=pol["Policy"]["Arn"])
    iam.create_policy_version(PolicyArn=pol["Policy"]["Arn"], SetAsDefault=True, PolicyDocument=json.dumps({"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "s3:ListBucket", "Resource": "*"}]}))
    iam.create_instance_profile(InstanceProfileName="lab-role")
    iam.add_role_to_instance_profile(InstanceProfileName="lab-role", RoleName="lab-role")
    iam.create_user(UserName="lab-user", Tags=TAG)
    iam.create_access_key(UserName="lab-user")
    iam.attach_user_policy(UserName="lab-user", PolicyArn=pol["Policy"]["Arn"])
    iam.create_user(UserName="real-admin")


KINDS = ["s3_buckets", "iam_roles", "iam_policies", "iam_users"]


def names(session):
    iam = session.client("iam")
    return {
        "buckets": sorted(b["Name"] for b in session.client("s3").list_buckets()["Buckets"]),
        "roles": sorted(r["RoleName"] for r in iam.list_roles()["Roles"]),
        "policies": sorted(p["PolicyName"] for p in iam.list_policies(Scope="Local")["Policies"]),
        "users": sorted(u["UserName"] for u in iam.list_users()["Users"]),
    }


def test_dry_run_deletes_nothing(aws, capsys):
    seed(aws)
    before = names(aws)
    assert labclean.main(KINDS, ["--region", "us-east-1"], session_factory=lambda **kw: aws) == 0
    assert names(aws) == before
    out = capsys.readouterr().out
    assert "DRY RUN" in out and "lab-bucket-1" in out and "lab-role" in out and "lab-user" in out
    assert "my-real-bucket" not in out and "prod-role" not in out and "real-admin" not in out
    assert "lab-bucket-eu" not in out  # other region


def test_only_tagged_resources_deleted(aws, capsys):
    seed(aws)
    assert labclean.main(KINDS, ["--region", "us-east-1", "--yes"], session_factory=lambda **kw: aws) == 0
    after = names(aws)
    assert after == {"buckets": ["lab-bucket-eu", "my-real-bucket"], "roles": ["prod-role"],
                     "policies": [], "users": ["real-admin"]}
    assert "✔ deleted s3_buckets lab-bucket-1" in capsys.readouterr().out


def test_region_flag_selects_buckets(aws):
    seed(aws)
    labclean.main(["s3_buckets"], ["--region", "eu-west-1", "--yes"], session_factory=lambda **kw: aws)
    assert "lab-bucket-eu" not in names(aws)["buckets"] and "lab-bucket-1" in names(aws)["buckets"]


def test_continues_after_a_failed_delete(aws, capsys, monkeypatch):
    seed(aws)
    real = labclean.FINDERS["s3_buckets"]

    def broken(session, region):
        found = real(session, region)
        for item in found:
            def fail():
                raise ClientError({"Error": {"Code": "AccessDenied", "Message": "nope"}}, "DeleteBucket")
            item.delete = fail
        return found
    monkeypatch.setitem(labclean.FINDERS, "s3_buckets", broken)
    code = labclean.main(KINDS, ["--region", "us-east-1", "--yes"], session_factory=lambda **kw: aws)
    out = capsys.readouterr().out
    assert code == 1
    assert "✘ s3_buckets lab-bucket-1: AccessDenied" in out
    assert names(aws)["roles"] == ["prod-role"]  # the IAM deletions still ran


def test_unknown_kind_is_rejected():
    with pytest.raises(ValueError, match="no_such_kind"):
        labclean.main(["no_such_kind"], ["--region", "us-east-1"])


def test_nothing_found(aws, capsys):
    assert labclean.main(KINDS, ["--region", "us-east-1", "--yes"], session_factory=lambda **kw: aws) == 0
    assert "Nothing tagged saa-course=lab" in capsys.readouterr().out
```

- [ ] **Step 2: Run them to see them fail**

```bash
.venv/Scripts/python.exe -m pytest _dev/tests/test_labclean.py
```

Expected: `ImportError: cannot import name 'labclean'`.

- [ ] **Step 3: Write `_harness/labclean.py`**

```python
"""labclean — remove what a lab created in YOUR AWS account, and nothing else.

Every lab tags what it creates with  saa-course = lab . A week's lab/cleanup.py calls main() with
the kinds of resources that lab creates. Without --yes it only lists (dry run).

    python lab/cleanup.py                    list what would be deleted (us-east-1 or $AWS_DEFAULT_REGION)
    python lab/cleanup.py --region eu-west-1 --profile saa-lab
    python lab/cleanup.py --yes              actually delete

IAM is global: IAM kinds are listed whatever --region you give.
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Callable

TAG_KEY, TAG_VALUE = "saa-course", "lab"


@dataclass
class Found:
    kind: str
    name: str
    region: str
    delete: Callable[[], None]


def _error_code(exc) -> str:
    response = getattr(exc, "response", None) or {}
    return response.get("Error", {}).get("Code", type(exc).__name__)


def _tagged(tags) -> bool:
    return any(t.get("Key") == TAG_KEY and t.get("Value") == TAG_VALUE for t in tags or [])


# ── S3 ──────────────────────────────────────────────────────────────


def find_s3_buckets(session, region: str) -> list[Found]:
    from botocore.exceptions import ClientError

    s3 = session.client("s3", region_name=region)
    found = []
    for bucket in s3.list_buckets().get("Buckets", []):
        name = bucket["Name"]
        try:
            location = s3.get_bucket_location(Bucket=name).get("LocationConstraint") or "us-east-1"
            if location != region:
                continue
            tags = s3.get_bucket_tagging(Bucket=name).get("TagSet", [])
        except ClientError:
            continue  # untagged (NoSuchTagSet) or not ours to read
        if _tagged(tags):
            found.append(Found("s3_buckets", name, region, lambda name=name: _delete_bucket(s3, name)))
    return found


def _delete_bucket(s3, name: str) -> None:
    for page in s3.get_paginator("list_object_versions").paginate(Bucket=name):
        doomed = [{"Key": v["Key"], "VersionId": v["VersionId"]} for v in page.get("Versions", []) + page.get("DeleteMarkers", [])]
        for start in range(0, len(doomed), 1000):
            s3.delete_objects(Bucket=name, Delete={"Objects": doomed[start:start + 1000], "Quiet": True})
    s3.delete_bucket(Bucket=name)


# ── IAM (global) ────────────────────────────────────────────────────


def find_iam_roles(session, region: str) -> list[Found]:
    iam = session.client("iam")
    found = []
    for page in iam.get_paginator("list_roles").paginate():
        for role in page["Roles"]:
            name = role["RoleName"]
            if _tagged(iam.list_role_tags(RoleName=name).get("Tags")):
                found.append(Found("iam_roles", name, "global", lambda name=name: _delete_role(iam, name)))
    return found


def _delete_role(iam, name: str) -> None:
    for profile in iam.list_instance_profiles_for_role(RoleName=name)["InstanceProfiles"]:
        iam.remove_role_from_instance_profile(InstanceProfileName=profile["InstanceProfileName"], RoleName=name)
        if profile["InstanceProfileName"] == name:
            iam.delete_instance_profile(InstanceProfileName=name)
    for policy in iam.list_role_policies(RoleName=name)["PolicyNames"]:
        iam.delete_role_policy(RoleName=name, PolicyName=policy)
    for policy in iam.list_attached_role_policies(RoleName=name)["AttachedPolicies"]:
        iam.detach_role_policy(RoleName=name, PolicyArn=policy["PolicyArn"])
    iam.delete_role(RoleName=name)


def find_iam_policies(session, region: str) -> list[Found]:
    iam = session.client("iam")
    found = []
    for page in iam.get_paginator("list_policies").paginate(Scope="Local"):
        for policy in page["Policies"]:
            arn = policy["Arn"]
            if _tagged(iam.list_policy_tags(PolicyArn=arn).get("Tags")):
                found.append(Found("iam_policies", policy["PolicyName"], "global", lambda arn=arn: _delete_policy(iam, arn)))
    return found


def _delete_policy(iam, arn: str) -> None:
    entities = iam.list_entities_for_policy(PolicyArn=arn)
    for role in entities.get("PolicyRoles", []):
        iam.detach_role_policy(RoleName=role["RoleName"], PolicyArn=arn)
    for user in entities.get("PolicyUsers", []):
        iam.detach_user_policy(UserName=user["UserName"], PolicyArn=arn)
    for group in entities.get("PolicyGroups", []):
        iam.detach_group_policy(GroupName=group["GroupName"], PolicyArn=arn)
    for version in iam.list_policy_versions(PolicyArn=arn)["Versions"]:
        if not version["IsDefaultVersion"]:
            iam.delete_policy_version(PolicyArn=arn, VersionId=version["VersionId"])
    iam.delete_policy(PolicyArn=arn)


def find_iam_users(session, region: str) -> list[Found]:
    iam = session.client("iam")
    found = []
    for page in iam.get_paginator("list_users").paginate():
        for user in page["Users"]:
            name = user["UserName"]
            if _tagged(iam.list_user_tags(UserName=name).get("Tags")):
                found.append(Found("iam_users", name, "global", lambda name=name: _delete_user(iam, name)))
    return found


def _delete_user(iam, name: str) -> None:
    from botocore.exceptions import ClientError

    for key in iam.list_access_keys(UserName=name)["AccessKeyMetadata"]:
        iam.delete_access_key(UserName=name, AccessKeyId=key["AccessKeyId"])
    try:
        iam.delete_login_profile(UserName=name)
    except ClientError as exc:
        if _error_code(exc) != "NoSuchEntity":
            raise
    for policy in iam.list_user_policies(UserName=name)["PolicyNames"]:
        iam.delete_user_policy(UserName=name, PolicyName=policy)
    for policy in iam.list_attached_user_policies(UserName=name)["AttachedPolicies"]:
        iam.detach_user_policy(UserName=name, PolicyArn=policy["PolicyArn"])
    for group in iam.list_groups_for_user(UserName=name)["Groups"]:
        iam.remove_user_from_group(UserName=name, GroupName=group["GroupName"])
    for device in iam.list_mfa_devices(UserName=name)["MFADevices"]:
        iam.deactivate_mfa_device(UserName=name, SerialNumber=device["SerialNumber"])
    iam.delete_user(UserName=name)


# Order matters: roles and users first, so customer-managed policies are detached before deletion.
FINDERS = {
    "s3_buckets": find_s3_buckets,
    "iam_roles": find_iam_roles,
    "iam_users": find_iam_users,
    "iam_policies": find_iam_policies,
}


def _force_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def main(kinds, argv=None, session_factory=None) -> int:
    unknown = [k for k in kinds if k not in FINDERS]
    if unknown:
        raise ValueError(f"unknown resource kind(s): {', '.join(unknown)}")
    _force_utf8()
    parser = argparse.ArgumentParser(description="Delete what this lab created (tag saa-course=lab).")
    parser.add_argument("--region", default=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
    parser.add_argument("--profile", default=None)
    parser.add_argument("--yes", action="store_true", help="really delete (default: dry run)")
    args = parser.parse_args(argv)
    if session_factory is None:
        import boto3

        session_factory = boto3.Session
    kwargs = {"region_name": args.region}
    if args.profile:
        kwargs["profile_name"] = args.profile
    session = session_factory(**kwargs)

    ordered = [k for k in FINDERS if k in kinds]
    found, failures = [], 0
    for kind in ordered:
        try:
            found += FINDERS[kind](session, args.region)
        except Exception as exc:  # keep listing the other kinds
            failures += 1
            print(f"✘ could not list {kind}: {_error_code(exc)}")
    if not found:
        print(f"Nothing tagged {TAG_KEY}={TAG_VALUE} in {args.region} (or IAM). Nothing to do.")
        return 1 if failures else 0
    if not args.yes:
        print(f"DRY RUN — these would be deleted ({TAG_KEY}={TAG_VALUE}). Run again with --yes to delete:")
        for item in found:
            print(f"  · {item.kind:<13} {item.name}  ({item.region})")
        return 1 if failures else 0
    for item in found:
        try:
            item.delete()
            print(f"✔ deleted {item.kind} {item.name}")
        except Exception as exc:
            failures += 1
            print(f"✘ {item.kind} {item.name}: {_error_code(exc)}")
    print("Done." if not failures else f"Done with {failures} problem(s) — fix them in the console or run again.")
    return 1 if failures else 0
```

- [ ] **Step 4: Run the tests**

```bash
.venv/Scripts/python.exe -m pytest _dev/tests/test_labclean.py
```

Expected: `6 passed`. (Checked in the spike venv on 2026-10-08: moto 5.2.3 supports `list_entities_for_policy` and `list_mfa_devices`, returns `NoSuchEntity` from `delete_login_profile` for a user without a password, and deletes a versioned bucket after `delete_objects` on every version and delete marker.)

- [ ] **Step 5: Commit** — skipped (no git).

---

### Task 7: `verify_course.py` — weeks, banks, currency, coverage, self-test

**Files:**
- Create: `verify_course.py`
- Test: `_dev/tests/test_verify_course.py`

**Interfaces:**
- Consumes: `awsdrill.JSON_MARKER`, `awslib.safety.force_utf8`, `quizlib.load_bank`, `quizlib.bank_problems`, `quizlib.near_duplicates`, `quizlib.retired_hits`, `quizlib.TASKS`, `quizlib.BankError`, `labclean.FINDERS`, `_dev/tests/bankgen.py` from Task 4 (tests only).
- Produces: `Check(name, ok, detail)`; `verify_week(root, week_dir, py) -> list[Check]`; `verify_banks(root) -> list[Check]`; `verify_currency(root) -> list[Check]`; `coverage(root) -> dict[str, dict]`; `write_coverage(root, strict) -> list[Check]`; `verify_self_test(root, py) -> list[Check]`; `main(argv) -> int` (0 all passed · 1 a check failed · 2 bad arguments). Task 8 adds `verify_milestone`.

- [ ] **Step 1: Write the failing tests `_dev/tests/test_verify_course.py`**

```python
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
```

- [ ] **Step 2: Run them to see them fail**

```bash
.venv/Scripts/python.exe -m pytest _dev/tests/test_verify_course.py
```

Expected: `FileNotFoundError` for `verify_course.py`.

- [ ] **Step 3: Write `verify_course.py`**

```python
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


def verify_milestone(root: Path, n: int, py: str) -> list:
    """Implemented in Task 8."""
    return [Check(f"milestone checks for M{n:02d}", False, "verify_milestone is added in Task 8")]


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests**

```bash
.venv/Scripts/python.exe -m pytest _dev/tests/test_verify_course.py
```

Expected: all pass. The fake course runs real drills through the real harness, so this takes ≈ 30–60 s.

Note for `test_banks_find_near_duplicates_across_weeks`: weeks 00 and 01 generated by `balanced_raws` differ only in the variant number inside each stem, so their stems are near-duplicates — that is exactly what the test expects to be flagged. Ids differ by week prefix, so the duplicate-id check stays green.

- [ ] **Step 5: Commit** — skipped (no git).

---

### Task 8: Milestone tools + `verify_course.py` milestone checks

**Files:**
- Create: `course_project/tools/start_milestone.py`, `course_project/tools/run_milestone.py`, `course_project/tools/conftest.py`
- Modify: `verify_course.py` (replace the placeholder `verify_milestone` at the bottom)
- Test: `_dev/tests/test_milestone_tools.py`

**Interfaces:**
- Consumes: `_harness/awslib/{__init__,safety,cfn,policy_eval}.py` (copied into the learner's repo as `tests/_course/`).
- Produces:
  - `start_milestone.py N --repo PATH` copies `course_project/tests/mNN/ → <repo>/tests/mNN/`, `tools/conftest.py → <repo>/tests/conftest.py`, `tools/run_milestone.py → <repo>/run_milestone.py`, and `_harness/awslib/*.py → <repo>/tests/_course/`. Exit 0 copied · 2 unknown milestone or missing repo.
  - `run_milestone.py N [--json]` — cumulative pytest over `tests/m01 … tests/mNN`; per-step lines `✔ M01.2 app_role`; `MILESTONE_JSON {"steps": {...}, "errors": [...]}`; exit 0 all green · 1 red · 2 earlier milestone's tests missing.
  - Fixtures in the repo's `tests/conftest.py`: `repo`, `template(layer) -> dict`, `lint_errors(layer) -> list[dict]`, `render(value, **params)`, `role_policies(layer, role, **params) -> list[dict]`, `trust_policy(layer, role, **params) -> dict`, `evaluator` (the `policy_eval` module), `moto_stacks` (callable `deploy(layer, **params) -> stack status`), constants `PARAMS = {"Prefix": "shortly", "Env": "prod"}`, `ACCOUNT = "111122223333"`.
  - `verify_course.verify_milestone(root, n, py) -> list[Check]`.

- [ ] **Step 1: Write the failing tests `_dev/tests/test_milestone_tools.py`**

```python
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
                    ignore=shutil.ignore_patterns("__pycache__", "*.toml", "prices.py"))
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
```

- [ ] **Step 2: Run them to see them fail**

```bash
.venv/Scripts/python.exe -m pytest _dev/tests/test_milestone_tools.py
```

Expected: errors — `course_project/tools` does not exist.

- [ ] **Step 3: Write `course_project/tools/start_milestone.py`**

```python
"""start_milestone.py — copy a milestone's tests into your shortly-infra repo.

    python course_project/tools/start_milestone.py 1 --repo ~/code/shortly-infra

Copies (overwriting; these files belong to the course):
    course_project/tests/mNN/              → <repo>/tests/mNN/
    course_project/tools/conftest.py       → <repo>/tests/conftest.py
    course_project/tools/run_milestone.py  → <repo>/run_milestone.py
    _harness/awslib/*.py                   → <repo>/tests/_course/   (template + policy helpers the tests use)
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
HELPERS = ("__init__.py", "safety.py", "cfn.py", "policy_eval.py")


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

    print(f"Copied tests/{source.name}/, tests/conftest.py, tests/_course/ and run_milestone.py into {repo}")
    print(f"Instructions:  {COURSE_PROJECT / 'milestones' / f'M{n:02d}.md'}")
    print(f"Progress:      cd \"{repo}\"   then   python run_milestone.py {n}")
    print("Use the course venv's python (it has moto and cfn-lint).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Write `course_project/tools/run_milestone.py`**

Same behaviour as the Flask course's runner (proven there), with this docstring and a `tests` folder that pytest must not recurse into `_course` as tests:

```python
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
```

- [ ] **Step 5: Write `course_project/tools/conftest.py`**

```python
"""Course-owned pytest setup for your shortly-infra repo.

start_milestone.py copies this to tests/conftest.py (with helpers in tests/_course/) and overwrites
it each milestone — don't edit it. It forces fake AWS credentials first, so no test can ever reach
your real AWS account, even if you have a profile configured.
"""
import sys
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parent
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from _course.safety import use_fake_aws_env  # noqa: E402

use_fake_aws_env()

from _course import cfn, policy_eval  # noqa: E402

PARAMS = {"Prefix": "shortly", "Env": "prod"}
ACCOUNT = "111122223333"
PSEUDO = {"AWS::AccountId": ACCOUNT, "AWS::Region": "us-east-1"}
collect_ignore = ["_course"]


def _path(layer: str) -> Path:
    path = REPO / "infra" / f"{layer}.yaml"
    if not path.exists():
        pytest.fail(f"infra/{layer}.yaml does not exist yet", pytrace=False)
    return path


@pytest.fixture(scope="session")
def repo():
    return REPO


@pytest.fixture(scope="session")
def template():
    cache = {}

    def load(layer: str) -> dict:
        if layer not in cache:
            try:
                cache[layer] = cfn.load_template(_path(layer))
            except cfn.TemplateError as exc:
                pytest.fail(f"infra/{layer}.yaml does not load: {exc}", pytrace=False)
        return cache[layer]
    return load


@pytest.fixture(scope="session")
def lint_errors():
    return lambda layer: cfn.errors_only(cfn.lint_template(_path(layer)))


@pytest.fixture
def render():
    return lambda value, **params: cfn.render(value, {**PARAMS, **params}, PSEUDO)


@pytest.fixture
def role_policies(template):
    return lambda layer, role, **params: cfn.role_policies(template(layer), role, {**PARAMS, **params}, PSEUDO)


@pytest.fixture
def trust_policy(template):
    return lambda layer, role, **params: cfn.trust_policy(template(layer), role, {**PARAMS, **params}, PSEUDO)


@pytest.fixture
def evaluator():
    return policy_eval


@pytest.fixture
def moto_stacks():
    """deploy(layer, **params) creates the stack in a fake AWS (moto) and returns its status.
    moto skips some resource types silently, so tests only read back what moto really models."""
    import boto3
    from moto import mock_aws

    mock = mock_aws()
    mock.start()

    def deploy(layer: str, **params) -> str:
        body = _path(layer).read_text(encoding="utf-8")
        declared = cfn.load_template_text(body).get("Parameters") or {}
        merged = {**PARAMS, **params}
        cf = boto3.client("cloudformation", region_name="us-east-1")
        cf.create_stack(StackName=f"shortly-{layer}", TemplateBody=body,
                        Capabilities=["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"],
                        Parameters=[{"ParameterKey": k, "ParameterValue": str(v)} for k, v in merged.items() if k in declared])
        return cf.describe_stacks(StackName=f"shortly-{layer}")["Stacks"][0]["StackStatus"]
    yield deploy
    mock.stop()
```

- [ ] **Step 6: Replace `verify_milestone` in `verify_course.py`**

Delete the placeholder `verify_milestone` function at the bottom of `verify_course.py` and add, above `print_section`:

```python
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
```

- [ ] **Step 7: Run the tests**

```bash
.venv/Scripts/python.exe -m pytest _dev/tests/test_milestone_tools.py
```

Expected: `7 passed`. `test_conftest_fixtures_load_render_and_evaluate` runs cfn-lint once (≈ 3–5 s) and a moto stack; if moto reports something other than `CREATE_COMPLETE` for a single `AWS::IAM::Role`, report it — the spike deployed IAM roles successfully.

- [ ] **Step 8: Commit** — skipped (no git).

---

### Task 9: Docs of record and the price table

**Files:**
- Create: `docs/exam_guide.md`, `docs/facts.md`, `_harness/awslib/prices.toml`, `_harness/awslib/prices.py`
- Test: `_dev/tests/test_prices.py`

**Interfaces:**
- Consumes: `docs/research/2026-10-08-saa-c03-research.md` (sections 2–5).
- Produces: `docs/exam_guide.md` (verbatim exam guide); `docs/facts.md` (the only source of numbers for notes and questions); `prices.load() -> dict`, `prices.section(name) -> dict`, `prices.tiers(name) -> list[tuple[float | None, float]]`, `prices.tiered_cost(quantity, tiers) -> float`; sections `[meta]`, `[data_transfer]`, `[[s3_standard_tiers]]`.

- [ ] **Step 1: Write `docs/exam_guide.md`**

Header (exactly):

```markdown
# SAA-C03 exam guide (verbatim)

Source: AWS Certified Solutions Architect – Associate (SAA-C03) Exam Guide, Version 1.1 —
https://d1.awsstatic.com/training-and-certification/docs-sa-assoc/AWS-Certified-Solutions-Architect-Associate_Exam-Guide.pdf
Copied on 2026-10-08 from docs/research/2026-10-08-saa-c03-research.md §2. Before booking the exam,
re-check https://aws.amazon.com/certification/certified-solutions-architect-associate/ — AWS has
replaced associate exams with only 3–4 weeks' notice.
```

Then copy research §2.1–§2.4 unchanged (exam format table, domains, all 14 task statements with their "Knowledge of" / "Skills in" bullets, the in-scope and out-of-scope service lists), keeping the research file's warning paragraph at the top of §2.4. Verify with:

```bash
grep -c "^##### Task Statement" docs/exam_guide.md
```

Expected: `14`.

- [ ] **Step 2: Write `docs/facts.md`**

```markdown
# Facts of record

Every number, limit, date and status used in concept notes, drills and quiz questions comes from this
file. Each row names its official source. Checked 2026-10-08 (research: docs/research/2026-10-08-saa-c03-research.md).
A question never depends on a value marked "changed" — the exam may still use the old one.

## Exam

| Fact | Value | Source |
|---|---|---|
| Questions | 65 (50 scored + 15 unscored, not identified) | exam guide PDF v1.1 p.2 |
| Question types | multiple choice (1 of 4) · multiple response (2+ of 5+) | exam guide p.1 |
| Duration · cost | 130 minutes · 150 USD | aws.amazon.com/certification/certified-solutions-architect-associate/ |
| Scoring | scaled 100–1,000 · pass 720 · compensatory · no guessing penalty | exam guide p.2 |
| Domains | 1 Secure 30 % · 2 Resilient 26 % · 3 High-performing 24 % · 4 Cost 20 % | exam guide p.2 |

## Numbers to know

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Reserved IPs per subnet | 5 (network, .1 router, .2 DNS, .3 future, broadcast) | no | docs.aws.amazon.com/vpc/latest/userguide/subnet-sizing.html |
| S3 max object size | 50 TB | changed 2025-12-02 (was 5 TB) | aws.amazon.com/about-aws/whats-new/2025/12/amazon-s3-maximum-object-size-50-tb/ |
| S3 single PUT | up to 5 GB (multipart above that) | no | docs.aws.amazon.com/AmazonS3/latest/userguide/upload-objects.html |
| SQS max message | 1 MiB | changed 2025-08-04 (was 256 KiB) | docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html |
| SQS retention | default 4 days · 60 s – 14 days | no | same |
| SQS visibility timeout | default 30 s · max 12 hours | no | same |
| SQS delay | max 15 minutes | no | same |
| SQS FIFO | 300 API calls/s per action (3,000 messages/s with batches of 10); higher with high-throughput mode | no | same |
| Lambda | timeout 900 s · memory 128–10,240 MB · /tmp 512–10,240 MB · 6 MB sync payload · 1 MB async | no | docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html |
| DynamoDB item | 400 KB max | no | docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html |
| RDS MySQL read replicas | up to 15 per source (same Region) | no | docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_MySQL.Replication.ReadReplicas.html |
| Aurora replicas | up to 15 per cluster | no | docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.Replication.html |
| gp3 | 1 GiB–64 TiB · 3,000 IOPS / 125 MiB/s baseline · up to 80,000 IOPS / 2,000 MiB/s | changed (was 16 TiB / 16,000 / 1,000) | docs.aws.amazon.com/ebs/latest/userguide/ebs-volume-types.html |
| gp2 | up to 16 TiB · 16,000 IOPS · 250 MiB/s | no | same |
| io2 Block Express | up to 64 TiB · 256,000 IOPS · 4,000 MiB/s · 99.999 % durability · Multi-Attach | no | same |
| io1 | up to 16 TiB · 64,000 IOPS · 1,000 MiB/s · Multi-Attach | no | same |
| st1 / sc1 | HDD, not bootable · 500 / 250 MiB/s max | no | same |
| Glacier Flexible Retrieval | expedited 1–5 min · standard 3–5 h · bulk 5–12 h | no | docs.aws.amazon.com/AmazonS3/latest/userguide/restoring-objects-retrieval-options.html |
| Glacier Deep Archive | standard within 12 h · bulk within 48 h | no | same |
| Glacier Instant Retrieval | milliseconds | no | same |
| Minimum storage duration | Standard-IA 30 days (+128 KB min billable) · Glacier IR 90 · Glacier Flexible 90 · Deep Archive 180 · Standard and Intelligent-Tiering none | no | docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html |
| Public IPv4 address | 0.005 USD per hour, in use or idle | since 2024-02-01 | aws.amazon.com/blogs/aws/new-aws-public-ipv4-address-charge-public-ip-insights/ |

Not confirmed — do not state as numbers until a later plan confirms them from an official page:
RDS PostgreSQL read-replica count · One Zone-IA and S3 Express One Zone minimum durations · FIFO high-throughput limits.

## Defaults that changed

| Change | Date | Source |
|---|---|---|
| S3 encrypts every new object with SSE-S3 by default (cannot be turned off) | 2023-01-05 | aws.amazon.com/about-aws/whats-new/2023/01/amazon-s3-automatically-encrypts-new-objects/ |
| New S3 buckets: Block Public Access on, ACLs disabled (Bucket owner enforced) | from 2023-04 | aws.amazon.com/about-aws/whats-new/2023/04/amazon-s3-security-best-practices-buckets-default/ |
| IMDSv2 can be set as the account default for new launches; Amazon Linux 2023 disables IMDSv1 | 2024-03 / 2023 | aws.amazon.com/about-aws/whats-new/2024/03/set-imdsv2-default-new-instance-launches/ |
| Aurora Serverless v2 can scale to 0 ACUs (auto-pause) | 2024-11-20 | aws.amazon.com/about-aws/whats-new/2024/11/amazon-aurora-serverless-v2-scaling-zero-capacity/ |
| Launch configurations: no new instance types since 2023; new accounts since 2024-10-01 cannot create them — use launch templates | 2023–2024 | docs.aws.amazon.com/autoscaling/ec2/userguide/launch-configurations.html |
| AWS CodeCommit back in general availability | 2025-11-24 | aws.amazon.com/blogs/devops/aws-codecommit-returns-to-general-availability/ |
| Renames: AWS SSO → IAM Identity Center · Kinesis Data Analytics for Apache Flink → Amazon Managed Service for Apache Flink | — | AWS docs |

## Retired or closed services (spec §7)

Rule 1 — retired; mention only on a line that contains the word "retired"; never in a question:

| Service | Status | Source |
|---|---|---|
| Amazon QLDB | retired (shut down 2025-07-31) | docs.aws.amazon.com/general/latest/gr/full_shutdown_services.html |
| Amazon Elastic Transcoder | retired (2025-11-13) | same |
| AWS Data Pipeline | retired for new customers (maintenance) | docs.aws.amazon.com/datapipeline/latest/DeveloperGuide/what-is-datapipeline.html |
| AWS Proton | retired (end of support 2026-10-07) | docs.aws.amazon.com/proton/latest/userguide/proton-end-of-support.html |
| Amazon Pinpoint | retired (sunset, ends 2026-10-30) | docs.aws.amazon.com/pinpoint/latest/userguide/migrate.html |
| AWS OpsWorks | retired (2024-05-01) | full_shutdown_services |
| EC2-Classic | retired (2022-08-15) | aws.amazon.com/blogs/aws/ec2-classic-is-retiring-heres-how-to-prepare/ |
| Aurora Serverless v1 | retired (end of life 2025-03-31) | docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2.upgrade.html |
| Kinesis Data Analytics for SQL | retired (2026-01-27) | full_shutdown_services |
| AWS WAF Classic · Amazon Inspector Classic | retired (2026-10-07 · 2026-05-20) | sunset / full_shutdown_services |
| AWS Snowmobile · AWS Snowcone | retired (2024-03-14 · 2024-11-12) | full_shutdown_services; aws.amazon.com/blogs/storage/aws-snow-device-updates/ |
| Launch configurations | retired for new accounts (see above) | launch-configurations doc |
| S3 Select · S3 Object Lambda | retired for new customers (maintenance 2024-07-25 · 2025-11-07) | AWS storage blog; S3 docs |
| Original vault-based Amazon Glacier service | retired for new customers (2025-12-15); use the S3 Glacier storage classes | docs.aws.amazon.com/AmazonS3/latest/userguide/glacier-storage-classes.html |
| AWS Cloud9 · AWS App Mesh | retired for new customers (2024-07-25) · retired (2026-09-30) | AWS DevOps / containers blogs |

Rule 2 — closed to new customers but still in the exam guide; teach as the exam answer with this status note; questions using it as the answer carry `legacy = true`:

| Service | 2026 status | Successor | Source |
|---|---|---|---|
| AWS Snowball Edge (Snow Family) | closed to new customers since 2025-11-07 | AWS DataSync (online) · AWS Data Transfer Terminal (physical) | docs.aws.amazon.com/snowball/latest/developer-guide/snowball-edge-availability-change.html |
| AWS Application Discovery Service | closed to new customers 2025-11-07 | AWS Transform | docs.aws.amazon.com/application-discovery/latest/userguide/application-discovery-service-availability-change.html |
| AWS Migration Hub | maintenance (2025-11-07) | AWS Transform | docs.aws.amazon.com/migrationhub/latest/ug/migrationhub-availability-change.html |

## Account plans (for the optional labs)

| Fact | Source |
|---|---|
| New accounts pick a Free plan or a Paid plan; both get 100 USD credits plus up to 100 USD more for activities | docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html |
| The Free plan ends after 6 months or when credits run out; the account then closes (90 days to upgrade before deletion) | same |
| A Free-plan account is upgraded to Paid automatically if it joins AWS Organizations or sets up a Control Tower landing zone | same |
| Budgets templates: Zero spend budget · Monthly cost budget | docs.aws.amazon.com/cost-management/latest/userguide/budget-templates.html |
| Billing alarm: enable "Receive CloudWatch Billing Alerts", then alarm on EstimatedCharges in us-east-1 | docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/monitor_estimated_charges_with_cloudwatch.html |
| Do not promise the pre-2025 "12-month free tier" (750 h of t2/t3.micro) — it applies only to older accounts | free-tier-plans doc |
```

Note: the "retired" rows use the word "retired" on every line on purpose — `verify_course.py`'s currency check skips lines containing it, and `docs/` is not scanned anyway.

- [ ] **Step 3: Write `_harness/awslib/prices.toml`**

```toml
# Illustrative us-east-1 list prices for the course's cost drills — NOT a quote.
# Check https://calculator.aws/ for real numbers. The exam tests cost reasoning, not prices.
[meta]
region = "us-east-1"
as_of = "2026-10"

[data_transfer]
ingress_per_gb = 0.0               # into AWS from the internet
egress_internet_per_gb = 0.09      # out to the internet (first 10 TB/month tier)
inter_az_per_gb_each_way = 0.01    # between AZs in one Region: charged out AND in
inter_region_per_gb = 0.02         # between Regions (sender pays)

[[s3_standard_tiers]]              # S3 Standard storage, per GB-month
up_to_gb = 51200                   # first 50 TB
per_gb_month = 0.023

[[s3_standard_tiers]]
up_to_gb = 512000                  # next 450 TB
per_gb_month = 0.022

[[s3_standard_tiers]]              # over 500 TB (no upper bound)
per_gb_month = 0.021
```

- [ ] **Step 4: Write the failing test `_dev/tests/test_prices.py`**

```python
import pytest

from _harness.awslib import prices


def test_sections():
    assert prices.section("data_transfer")["inter_az_per_gb_each_way"] == 0.01
    assert prices.load()["meta"]["region"] == "us-east-1"


def test_tiers_and_tiered_cost():
    tiers = prices.tiers("s3_standard_tiers")
    assert tiers == [(51200, 0.023), (512000, 0.022), (None, 0.021)]
    assert prices.tiered_cost(1000, tiers) == pytest.approx(23.0)
    assert prices.tiered_cost(60000, tiers) == pytest.approx(51200 * 0.023 + 8800 * 0.022)
    assert prices.tiered_cost(600000, tiers) == pytest.approx(51200 * 0.023 + 460800 * 0.022 + 88000 * 0.021)
    assert prices.tiered_cost(0, tiers) == 0


def test_unknown_section():
    with pytest.raises(KeyError, match="no_such"):
        prices.section("no_such")
```

- [ ] **Step 5: Write `_harness/awslib/prices.py`**

```python
"""prices — the course's illustrative price table (prices.toml). Not a quote: see the file header."""
from __future__ import annotations

import tomllib
from functools import lru_cache
from pathlib import Path

PRICES_FILE = Path(__file__).with_name("prices.toml")


@lru_cache(maxsize=1)
def load() -> dict:
    return tomllib.loads(PRICES_FILE.read_text(encoding="utf-8"))


def section(name: str) -> dict:
    data = load()
    if name not in data:
        raise KeyError(f"prices.toml has no section {name}")
    return data[name]


def tiers(name: str) -> list[tuple[float | None, float]]:
    """[[name]] tables → [(cumulative upper bound or None, price per unit), …]."""
    return [(row.get("up_to_gb"), row["per_gb_month"]) for row in section(name)]


def tiered_cost(quantity: float, tier_list) -> float:
    total, lower = 0.0, 0.0
    for upper, price in tier_list:
        top = quantity if upper is None else min(quantity, upper)
        if top <= lower:
            break
        total += (top - lower) * price
        lower = top
    return total
```

- [ ] **Step 6: Run the test**

```bash
.venv/Scripts/python.exe -m pytest _dev/tests/test_prices.py
```

Expected: `3 passed`.

- [ ] **Step 7: Commit** — skipped (no git).

---

### Task 10: Week 00 drills 01–05

**Files:**
- Create: `week_00_foundations_and_exam_technique/practice/exercises.py` (drills 01–05 + header + `run()`), `week_00_foundations_and_exam_technique/practice/solutions.py` (01–05), `_dev/mutants/week00.py` (01–05)

**Interfaces:**
- Consumes: `awsdrill.Drill`, `awsdrill.run`, `awslib.prices` (Task 11 uses it; import it in the header now).
- Produces: learner names `parse_arn`, `series`, `parallel`, `downtime_minutes`, `per_az_needed`, `survives_az_loss`, `RESPONSIBILITY`, `whoami`, `region_names`; test data `RESPONSIBILITY_TASKS`, `RESPONSIBILITY_DIGESTS`. Task 11 appends drills 06–10 to the same three files.

- [ ] **Step 1: Write `exercises.py` with drills 01–05**

```python
"""
Week 00 drills — Foundations & exam technique
=============================================
Run:    python practice/exercises.py          every drill
        python practice/exercises.py 3        drill 3 only
Stuck?  read the hint line; then compare with practice/solutions.py.
Every drill runs offline: AWS calls go to moto (a fake AWS) with fake credentials — nothing here can
touch a real AWS account or cost money.
"""
import math  # noqa: F401  (you may need it)
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.awsdrill import Drill, run  # noqa: E402
from _harness.awslib import prices  # noqa: E402


# ── Exercise 01 ★: Read an ARN ───────────────────────────────────────
"""
parse_arn(arn: str) -> dict with keys partition, service, region, account, resource_type, resource_id

An ARN is  arn:PARTITION:SERVICE:REGION:ACCOUNT:RESOURCE  — split on the first five ':' only.
RESOURCE is "type/id", "type:id" or just "id": split it on whichever of '/' or ':' comes FIRST.
Exceptions: S3 has no resource type (all of RESOURCE is bucket[/key]); a resource with no '/' or ':'
has resource_type "". Empty region/account stay "" (S3 and IAM are global, so their ARNs leave them out).
Partitions: aws, aws-cn, aws-us-gov. Anything else, fewer than six parts, or a first part that is not
"arn" → ValueError.

Examples:
  parse_arn("arn:aws:iam::111122223333:role/team/app") == {"partition": "aws", "service": "iam",
      "region": "", "account": "111122223333", "resource_type": "role", "resource_id": "team/app"}
  parse_arn("arn:aws:s3:::shortly-assets/logos/a.png")["resource_id"] == "shortly-assets/logos/a.png"
  parse_arn("arn:aws:lambda:us-east-1:111122223333:function:shorten:PROD")["resource_id"] == "shorten:PROD"
Hint: arn.split(":", 5) gives exactly six parts for a valid ARN.
"""
def parse_arn(arn):
    raise NotImplementedError  # YOUR CODE


class Ex01(Drill):
    """Read an ARN ★"""
    tasks = ("1.1",)

    def test_iam_role_with_path(self):
        self.assertEqual(parse_arn("arn:aws:iam::111122223333:role/team/app"),
                         {"partition": "aws", "service": "iam", "region": "", "account": "111122223333",
                          "resource_type": "role", "resource_id": "team/app"})

    def test_s3_object_has_no_type(self):
        self.assertEqual(parse_arn("arn:aws:s3:::shortly-assets/logos/a.png"),
                         {"partition": "aws", "service": "s3", "region": "", "account": "",
                          "resource_type": "", "resource_id": "shortly-assets/logos/a.png"})

    def test_colon_separated_resource(self):
        got = parse_arn("arn:aws:lambda:us-east-1:111122223333:function:shorten:PROD")
        self.assertEqual((got["region"], got["resource_type"], got["resource_id"]), ("us-east-1", "function", "shorten:PROD"))

    def test_first_separator_wins(self):
        got = parse_arn("arn:aws:logs:us-east-1:111122223333:log-group:/shortly/app:*")
        self.assertEqual((got["resource_type"], got["resource_id"]), ("log-group", "/shortly/app:*"))

    def test_resource_without_type(self):
        got = parse_arn("arn:aws:sns:us-east-1:111122223333:alerts")
        self.assertEqual((got["resource_type"], got["resource_id"]), ("", "alerts"))

    def test_other_partitions(self):
        self.assertEqual(parse_arn("arn:aws-cn:s3:::b1")["partition"], "aws-cn")
        self.assertEqual(parse_arn("arn:aws-us-gov:iam::111122223333:user/x")["partition"], "aws-us-gov")

    def test_invalid(self):
        for bad in ("arn:aws:s3", "urn:aws:s3:::b1", "arn:azure:s3:::b1", ""):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError, msg=f"parse_arn({bad!r}) should raise ValueError"):
                    parse_arn(bad)


# ── Exercise 02 ★: Availability maths ────────────────────────────────
"""
series(*availabilities) -> float        every part is needed: multiply the availabilities
parallel(availability, copies) -> float  any one of `copies` identical parts is enough: 1 - (1 - a) ** copies
downtime_minutes(availability, days=30) -> float   expected minutes of downtime in `days` days
Availabilities are fractions (0.999, not 99.9). Values outside 0 < a ≤ 1, or copies < 1 → ValueError.

Examples:
  series(0.999, 0.999)  ≈ 0.998001
  parallel(0.99, 2)     ≈ 0.9999
  downtime_minutes(0.999) ≈ 43.2      (30 days × 24 h × 60 min × 0.001)
Why it matters: two instances in two AZs behind a load balancer are in parallel; the load balancer
and the database they all need are in series — a chain is never better than its weakest link.
Hint: math.prod() multiplies an iterable.
"""
def series(*availabilities):
    raise NotImplementedError  # YOUR CODE


def parallel(availability, copies):
    raise NotImplementedError  # YOUR CODE


def downtime_minutes(availability, days=30):
    raise NotImplementedError  # YOUR CODE


class Ex02(Drill):
    """Availability maths ★"""
    tasks = ("2.2",)

    def test_series(self):
        self.assertAlmostEqual(series(0.999, 0.999), 0.998001, places=9)
        self.assertAlmostEqual(series(0.9995), 0.9995, places=9)

    def test_parallel(self):
        self.assertAlmostEqual(parallel(0.99, 2), 0.9999, places=9)
        self.assertAlmostEqual(parallel(0.9, 3), 0.999, places=9)
        self.assertAlmostEqual(parallel(0.95, 1), 0.95, places=9)

    def test_downtime(self):
        self.assertAlmostEqual(downtime_minutes(0.999), 43.2, places=6)
        self.assertAlmostEqual(downtime_minutes(0.9999, days=365), 52.56, places=6)

    def test_web_tier_example(self):
        # load balancer (99.99 %) → two app instances in two AZs (99 % each) → database (99.95 %)
        expected = 0.9999 * (1 - 0.01 ** 2) * 0.9995
        self.assertAlmostEqual(series(0.9999, parallel(0.99, 2), 0.9995), expected, places=12)

    def test_rejects_bad_values(self):
        for call in (lambda: series(1.5), lambda: series(0.99, 0), lambda: parallel(0.9, 0), lambda: parallel(-0.1, 2)):
            with self.subTest():
                with self.assertRaises(ValueError):
                    call()


# ── Exercise 03 ★: Survive the loss of an AZ ─────────────────────────
"""
per_az_needed(needed, azs) -> int
    How many instances must run in EACH of `azs` Availability Zones so that `needed` instances are
    still running after any one AZ fails? Spread evenly, round up. azs < 2 → ValueError.
    per_az_needed(6, 3) == 3    (9 in total: lose one AZ, 6 remain)
survives_az_loss(layout, needed) -> bool
    layout maps AZ name → instances there. True when, whichever ONE AZ is lost, at least `needed`
    instances remain. A layout with fewer than two AZs never survives.
    survives_az_loss({"us-east-1a": 6, "us-east-1b": 2}, 6) is False   (lose 1a → 2 left)
This is "static stability": capacity already running, so an AZ failure needs no scaling to recover.
Hint: after losing the AZ with the most instances, how many are left?
"""
def per_az_needed(needed, azs):
    raise NotImplementedError  # YOUR CODE


def survives_az_loss(layout, needed):
    raise NotImplementedError  # YOUR CODE


class Ex03(Drill):
    """Survive the loss of an AZ ★"""
    tasks = ("2.2",)

    def test_per_az_needed(self):
        for (needed, azs), want in {(6, 3): 3, (4, 2): 4, (10, 3): 5, (7, 4): 3, (1, 2): 1}.items():
            with self.subTest(needed=needed, azs=azs):
                self.assertEqual(per_az_needed(needed, azs), want)

    def test_one_az_is_not_enough(self):
        with self.assertRaises(ValueError):
            per_az_needed(4, 1)

    def test_survives(self):
        self.assertTrue(survives_az_loss({"us-east-1a": 3, "us-east-1b": 3, "us-east-1c": 3}, 6))
        self.assertTrue(survives_az_loss({"us-east-1a": 4, "us-east-1b": 4}, 4))

    def test_does_not_survive(self):
        self.assertFalse(survives_az_loss({"us-east-1a": 6, "us-east-1b": 2}, 6))
        self.assertFalse(survives_az_loss({"us-east-1a": 3, "us-east-1b": 3, "us-east-1c": 2}, 6))
        self.assertFalse(survives_az_loss({"us-east-1a": 10}, 1))
        self.assertFalse(survives_az_loss({}, 1))


# ── Exercise 04 (decide): Who is responsible? ────────────────────────
"""
For each numbered task in RESPONSIBILITY_TASKS, who does it — "customer" or "aws"?
Replace every None in RESPONSIBILITY with "customer" or "aws".
The line AWS draws: AWS secures the cloud itself ("security OF the cloud"); you secure what you put
in it ("security IN the cloud"). The more managed the service, the more AWS does — but your data,
who can access it, and how you configure it always stay yours.
(The answers are stored as hashes, so reading the test will not give them away.)
"""
RESPONSIBILITY_TASKS = {
    1: ("Amazon EC2", "patch the guest operating system"),
    2: ("Amazon RDS", "patch the database engine"),
    3: ("AWS Lambda", "patch the operating system that runs your functions"),
    4: ("Amazon EC2", "configure security group rules"),
    5: ("Amazon S3", "turn on encryption for data at rest"),
    6: ("Amazon S3", "physical security of the data centres"),
    7: ("Amazon DynamoDB", "write IAM policies that grant access to a table"),
    8: ("Amazon EBS", "replace failed disks behind a volume"),
    9: ("AWS Lambda", "keep the libraries in your function code free of known vulnerabilities"),
    10: ("Amazon RDS", "choose which network ports a DB instance accepts traffic on"),
}
RESPONSIBILITY = {n: None for n in RESPONSIBILITY_TASKS}   # YOUR ANSWERS: "customer" or "aws"

RESPONSIBILITY_DIGESTS = {
    1: "8682259a3d1c74ad4125bc6d13e03d8732817a02ec6601058de2a5de05322157",
    2: "a4eac6f2e952919cb4646dfcc46769490f0eb7e084dff7b657244fa7551526e9",
    3: "234b6927abcc493df1f528666c12d40d158fccd6919e2fd6820696c417a929a8",
    4: "8fa7e625a1edd1bb65b1bc9d6e8246fc31c18638b0c75b0598cc46ca9ca4b253",
    5: "f6675df3fb3cfa269768cd5c4a9cb377c04f6d45e8a72dab449c9f6a63eff45c",
    6: "a9995d7cef5fe00b28a1038f71911305c082884e9f1481a319dffa89cab0c0e3",
    7: "27711b0e304c157bc0c85029fa2b5972876ad8f6e67e169a2ec20873ffc2ea04",
    8: "9ac7d2eaf30017ba60d930b003354829a8a98f43209919683b94f17013de9ebe",
    9: "c6d9da1d6e520b2e9042e4aeea14ff7ab08c014933195bd5bf1b7f2c63ef33f2",
    10: "2ae29c906ba517125916da97d183790a05c0284463b0355579079919629725f9",
}


class Ex04(Drill):
    """Who is responsible?"""
    tasks = ("1.2",)

    def test_each_task(self):
        for n, (service, task) in RESPONSIBILITY_TASKS.items():
            with self.subTest(n=n):
                value = RESPONSIBILITY.get(n)
                self.assertIn(value, ("customer", "aws"), f"task {n} ({service}: {task}): answer 'customer' or 'aws', not {value!r}")
                self.assertHashed(value, f"w00-ex04-{n}", RESPONSIBILITY_DIGESTS[n],
                                  f"task {n} ({service}: {task}): {value!r} is not right — think OF vs IN the cloud")


# ── Exercise 05: Who am I, and where? ────────────────────────────────
"""
whoami() -> {"account": str, "arn": str}    from STS GetCallerIdentity
region_names() -> list[str]                 every Region name from EC2 DescribeRegions, sorted
Create clients with boto3.client("sts") / boto3.client("ec2", region_name="us-east-1").
In this drill AWS is moto, whose fake account is 123456789012.
Example: whoami()["account"] == "123456789012";  "eu-west-1" in region_names()
Hint: get_caller_identity() returns a dict with "Account" and "Arn".
"""
def whoami():
    raise NotImplementedError  # YOUR CODE


def region_names():
    raise NotImplementedError  # YOUR CODE


class Ex05(Drill):
    """Who am I, and where?"""
    tasks = ("1.1",)
    uses_aws = True

    def test_whoami(self):
        got = whoami()
        self.assertEqual(set(got), {"account", "arn"}, "return exactly the keys 'account' and 'arn'")
        self.assertEqual(got["account"], "123456789012")
        self.assertTrue(got["arn"].startswith("arn:aws:"), got["arn"])

    def test_region_names(self):
        names = region_names()
        self.assertEqual(names, sorted(names), "sort the names")
        self.assertGreaterEqual(len(names), 30)
        self.assertTrue({"us-east-1", "eu-west-1", "ap-southeast-2"} <= set(names))
```

The `if __name__ == "__main__": run()` block goes at the very end of the file; Task 11 inserts drills 06–10 above it. For now end the file with:

```python
if __name__ == "__main__":
    run()
```

- [ ] **Step 2: Run it — every drill must fail on its stubs**

```bash
.venv/Scripts/python.exe week_00_foundations_and_exam_technique/practice/exercises.py
```

Expected: five `✘` lines (`not implemented yet` for 01–03 and 05; `task 1 … answer 'customer' or 'aws', not None` for 04) and `0/5 passing`.

- [ ] **Step 3: Write `solutions.py` (01–05)**

```python
"""Reference solutions for week 00. Read them after you have tried — the point is the struggle."""
import math

import boto3

PARTITIONS = {"aws", "aws-cn", "aws-us-gov"}


def parse_arn(arn):
    parts = arn.split(":", 5)
    if len(parts) != 6 or parts[0] != "arn" or parts[1] not in PARTITIONS:
        raise ValueError(f"not an ARN: {arn!r}")
    _, partition, service, region, account, resource = parts
    resource_type, resource_id = "", resource
    if service != "s3":
        cuts = [i for i in (resource.find("/"), resource.find(":")) if i != -1]
        if cuts:
            cut = min(cuts)
            resource_type, resource_id = resource[:cut], resource[cut + 1:]
    return {"partition": partition, "service": service, "region": region, "account": account,
            "resource_type": resource_type, "resource_id": resource_id}


def _check(a):
    if not 0 < a <= 1:
        raise ValueError(f"availability must be in (0, 1], got {a}")


def series(*availabilities):
    for a in availabilities:
        _check(a)
    return math.prod(availabilities)


def parallel(availability, copies):
    _check(availability)
    if copies < 1:
        raise ValueError("copies must be at least 1")
    return 1 - (1 - availability) ** copies


def downtime_minutes(availability, days=30):
    return (1 - availability) * days * 24 * 60


def per_az_needed(needed, azs):
    if azs < 2:
        raise ValueError("one AZ cannot survive its own failure")
    return math.ceil(needed / (azs - 1))


def survives_az_loss(layout, needed):
    if len(layout) < 2:
        return False
    return sum(layout.values()) - max(layout.values()) >= needed


RESPONSIBILITY = {1: "customer", 2: "aws", 3: "aws", 4: "customer", 5: "customer",
                  6: "aws", 7: "customer", 8: "aws", 9: "customer", 10: "customer"}


def whoami():
    identity = boto3.client("sts").get_caller_identity()
    return {"account": identity["Account"], "arn": identity["Arn"]}


def region_names():
    regions = boto3.client("ec2", region_name="us-east-1").describe_regions()["Regions"]
    return sorted(r["RegionName"] for r in regions)
```

- [ ] **Step 4: Write `_dev/mutants/week00.py` (01–05)**

```python
"""Deliberately wrong implementations for week 00 — verify_course.py checks that the drills catch each one."""
MUTANTS = [
    {"id": "slash-only", "drill": 1, "code": '''
def parse_arn(arn):
    parts = arn.split(":", 5)
    if len(parts) != 6 or parts[0] != "arn" or parts[1] not in {"aws", "aws-cn", "aws-us-gov"}:
        raise ValueError(arn)
    _, partition, service, region, account, resource = parts
    resource_type, _, resource_id = resource.partition("/") if "/" in resource else ("", "", resource)
    return {"partition": partition, "service": service, "region": region, "account": account,
            "resource_type": resource_type, "resource_id": resource_id}
'''},
    {"id": "parallel-multiplies", "drill": 2, "code": '''
import math
def series(*availabilities):
    return math.prod(availabilities)
def parallel(availability, copies):
    return availability ** copies
def downtime_minutes(availability, days=30):
    return (1 - availability) * days * 24 * 60
'''},
    {"id": "divide-by-all-azs", "drill": 3, "code": '''
import math
def per_az_needed(needed, azs):
    if azs < 2:
        raise ValueError("one AZ")
    return math.ceil(needed / azs)
def survives_az_loss(layout, needed):
    return sum(layout.values()) >= needed
'''},
    {"id": "rds-engine-is-yours", "drill": 4, "code": '''
RESPONSIBILITY = {1: "customer", 2: "customer", 3: "aws", 4: "customer", 5: "customer",
                  6: "aws", 7: "customer", 8: "aws", 9: "customer", 10: "customer"}
'''},
    {"id": "wrong-keys", "drill": 5, "code": '''
import boto3
def whoami():
    return boto3.client("sts").get_caller_identity()
def region_names():
    return [r["RegionName"] for r in boto3.client("ec2", region_name="us-east-1").describe_regions()["Regions"]][:10]
'''},
]
```

- [ ] **Step 5: Check stubs, solutions and mutants**

```bash
.venv/Scripts/python.exe week_00_foundations_and_exam_technique/practice/exercises.py --solutions
for id in slash-only parallel-multiplies divide-by-all-azs rds-engine-is-yours wrong-keys; do
  .venv/Scripts/python.exe week_00_foundations_and_exam_technique/practice/exercises.py --solutions --mutant "_dev/mutants/week00.py#$id" | tail -1
done
```

Expected: `5/5 passing (solutions)`; each mutant line shows `4/5 passing (solutions)` (exactly one drill fails).

- [ ] **Step 6: Commit** — skipped (no git).

---

### Task 11: Week 00 drills 06–10

**Files:**
- Modify: `week_00_foundations_and_exam_technique/practice/exercises.py` (insert above the final `if __name__` block), `practice/solutions.py` (append), `_dev/mutants/week00.py` (append to `MUTANTS`)

**Interfaces:**
- Consumes: Task 10's file; `awslib.prices.section("data_transfer")`.
- Produces: learner names `count_objects`, `bucket_exists`, `ensure_bucket`, `transfer_cost`, `make_client`, `inventory`; module constant `PRICES`.

- [ ] **Step 1: Insert drills 06–10 into `exercises.py`**

```python
# ── Exercise 06: Every page, not just the first ─────────────────────
"""
count_objects(s3, bucket, prefix="", page_size=1000) -> int
Count every object whose key starts with `prefix`. One ListObjectsV2 call returns at most
`page_size` keys (S3's maximum is 1,000), so a single call silently undercounts big buckets.
Use s3.get_paginator("list_objects_v2") with PaginationConfig={"PageSize": page_size}.
Example: 250 objects under "logs/", page_size=100 → 250, fetched in 3 calls.
Hint: each page has "KeyCount" (and no "Contents" when it is empty).
"""
def count_objects(s3, bucket, prefix="", page_size=1000):
    raise NotImplementedError  # YOUR CODE


class Ex06(Drill):
    """Every page, not just the first"""
    tasks = ("3.1",)
    uses_aws = True

    def test_counts_across_pages(self):
        s3 = self.client("s3")
        s3.create_bucket(Bucket="drill-logs")
        for i in range(250):
            s3.put_object(Bucket="drill-logs", Key=f"logs/{i:04d}.json", Body=b"{}")
        for i in range(5):
            s3.put_object(Bucket="drill-logs", Key=f"img/{i}.png", Body=b"")
        calls = []
        s3.meta.events.register("before-call.s3.ListObjectsV2", lambda **kwargs: calls.append(1))
        self.assertEqual(count_objects(s3, "drill-logs", "logs/", page_size=100), 250)
        self.assertEqual(len(calls), 3, "250 keys at 100 per page need 3 ListObjectsV2 calls")
        self.assertEqual(count_objects(s3, "drill-logs", "img/"), 5)
        self.assertEqual(count_objects(s3, "drill-logs"), 255)

    def test_empty_bucket(self):
        s3 = self.client("s3")
        s3.create_bucket(Bucket="drill-empty")
        self.assertEqual(count_objects(s3, "drill-empty"), 0)


# ── Exercise 07: Errors and the us-east-1 rule ───────────────────────
"""
bucket_exists(s3, name) -> bool
    head_bucket raises botocore.exceptions.ClientError when the bucket is missing (error code "404")
    or belongs to someone else ("403"). Return False for "404", True for "403" (it exists — just not
    yours), and re-raise any other error.
ensure_bucket(s3, name, region) -> "created" | "exists"
    Create the bucket unless it exists. The rule that trips everyone: in us-east-1 you must NOT pass
    CreateBucketConfiguration; in every other Region you MUST pass {"LocationConstraint": region}.
    If create_bucket answers "BucketAlreadyOwnedByYou", return "exists".
Hint: exc.response["Error"]["Code"] holds the error code.
"""
from botocore.exceptions import ClientError  # noqa: E402


def bucket_exists(s3, name):
    raise NotImplementedError  # YOUR CODE


def ensure_bucket(s3, name, region):
    raise NotImplementedError  # YOUR CODE


class _FakeS3:
    """A stand-in client whose head_bucket / create_bucket fail with a chosen error code."""

    def __init__(self, head_code=None, create_code=None):
        self.head_code, self.create_code, self.created = head_code, create_code, []

    def head_bucket(self, Bucket):
        if self.head_code:
            raise ClientError({"Error": {"Code": self.head_code, "Message": "x"}}, "HeadBucket")
        return {}

    def create_bucket(self, **kwargs):
        if self.create_code:
            raise ClientError({"Error": {"Code": self.create_code, "Message": "x"}}, "CreateBucket")
        self.created.append(kwargs)
        return {}


class Ex07(Drill):
    """Errors and the us-east-1 rule"""
    tasks = ("3.1",)
    uses_aws = True

    def test_exists(self):
        s3 = self.client("s3")
        self.assertFalse(bucket_exists(s3, "drill-missing"))
        s3.create_bucket(Bucket="drill-here")
        self.assertTrue(bucket_exists(s3, "drill-here"))

    def test_forbidden_means_it_exists(self):
        self.assertTrue(bucket_exists(_FakeS3(head_code="403"), "someone-elses"))

    def test_other_errors_are_raised(self):
        with self.assertRaises(ClientError):
            bucket_exists(_FakeS3(head_code="500"), "broken")

    def test_us_east_1(self):
        s3 = self.client("s3", "us-east-1")
        self.assertEqual(ensure_bucket(s3, "drill-east", "us-east-1"), "created")
        self.assertIsNone(s3.get_bucket_location(Bucket="drill-east")["LocationConstraint"])
        self.assertEqual(ensure_bucket(s3, "drill-east", "us-east-1"), "exists")

    def test_other_region(self):
        s3 = self.client("s3", "eu-west-1")
        self.assertEqual(ensure_bucket(s3, "drill-west", "eu-west-1"), "created")
        self.assertEqual(s3.get_bucket_location(Bucket="drill-west")["LocationConstraint"], "eu-west-1")

    def test_race_already_owned(self):
        fake = _FakeS3(head_code="404", create_code="BucketAlreadyOwnedByYou")
        self.assertEqual(ensure_bucket(fake, "raced", "eu-west-1"), "exists")


# ── Exercise 08 ★: What does moving data cost? ───────────────────────
"""
transfer_cost(flows, price=PRICES) -> float     (USD, rounded to 4 decimal places)
Each flow is (source, destination, gb). A place is "internet" or an Availability Zone name such as
"us-east-1a" (its Region is the name without the final letter).
  internet → AWS                   free
  AWS → internet                   gb × egress_internet_per_gb
  same AZ                          free (private IP addresses)
  different AZ, same Region        gb × inter_az_per_gb_each_way × 2   (charged going out AND coming in)
  different Region                 gb × inter_region_per_gb
A flow with "internet" at both ends → ValueError.
PRICES are the course's illustrative us-east-1 prices (_harness/awslib/prices.toml), not a quote.
Example: transfer_cost([("us-east-1a", "us-east-1b", 100)]) == 2.0
Hint: "us-east-1a"[:-1] == "us-east-1".
"""
PRICES = prices.section("data_transfer")


def transfer_cost(flows, price=PRICES):
    raise NotImplementedError  # YOUR CODE


class Ex08(Drill):
    """What does moving data cost? ★"""
    tasks = ("4.4",)

    def test_each_kind_of_flow(self):
        p = PRICES
        cases = {
            ("internet", "us-east-1a", 500): 0.0,
            ("us-east-1a", "internet", 1000): round(1000 * p["egress_internet_per_gb"], 4),
            ("us-east-1a", "us-east-1a", 800): 0.0,
            ("us-east-1a", "us-east-1b", 100): round(100 * p["inter_az_per_gb_each_way"] * 2, 4),
            ("us-east-1a", "eu-west-1b", 50): round(50 * p["inter_region_per_gb"], 4),
        }
        for flow, want in cases.items():
            with self.subTest(flow=flow):
                self.assertAlmostEqual(transfer_cost([flow]), want, places=4)

    def test_sum_of_flows(self):
        flows = [("us-east-1a", "us-east-1b", 100), ("us-east-1b", "internet", 10)]
        self.assertAlmostEqual(transfer_cost(flows), round(2.0 + 10 * PRICES["egress_internet_per_gb"], 4), places=4)

    def test_uses_the_price_argument(self):
        custom = {"ingress_per_gb": 0.0, "egress_internet_per_gb": 0.05, "inter_az_per_gb_each_way": 0.02,
                  "inter_region_per_gb": 0.04}
        self.assertAlmostEqual(transfer_cost([("us-east-1a", "us-east-1c", 10)], price=custom), 0.4, places=4)

    def test_internet_to_internet(self):
        with self.assertRaises(ValueError):
            transfer_cost([("internet", "internet", 1)])


# ── Exercise 09: A client that retries well ──────────────────────────
"""
make_client(service, region, total_attempts=5, connect_timeout=3, read_timeout=10)
Return a boto3 client that retries throttling and transient errors in "adaptive" mode, makes at
most `total_attempts` attempts in total (the first try included) and uses the given timeouts.
Hint: botocore.config.Config(retries={"total_max_attempts": ..., "mode": "adaptive"},
      connect_timeout=..., read_timeout=...)  — note botocore's own "max_attempts" key means RETRIES,
      one fewer than the total.
"""
def make_client(service, region, total_attempts=5, connect_timeout=3, read_timeout=10):
    raise NotImplementedError  # YOUR CODE


class Ex09(Drill):
    """A client that retries well"""
    tasks = ("2.1",)

    def test_defaults(self):
        client = make_client("s3", "eu-west-1")
        self.assertEqual(client.meta.region_name, "eu-west-1")
        self.assertEqual(client.meta.config.retries, {"mode": "adaptive", "total_max_attempts": 5})
        self.assertEqual((client.meta.config.connect_timeout, client.meta.config.read_timeout), (3, 10))

    def test_custom(self):
        client = make_client("dynamodb", "us-east-1", total_attempts=1, connect_timeout=1, read_timeout=2)
        self.assertEqual(client.meta.config.retries["total_max_attempts"], 1)
        self.assertEqual(client.meta.service_model.service_name, "dynamodb")
        self.assertEqual(client.meta.config.read_timeout, 2)


# ── Exercise 10 (combined): What is running where? ───────────────────
"""
inventory(regions) -> dict
For each Region name in `regions` report what exists there:
    {"us-east-1": {"buckets": ["a-bucket", …] (sorted), "instances": 2, "queues": 1}, …}
Buckets: S3's ListBuckets returns every bucket whatever the Region — place each one with
get_bucket_location (a LocationConstraint of None means us-east-1).
Instances: count every instance in every reservation of ec2.describe_instances() in that Region.
Queues: len(sqs.list_queues().get("QueueUrls", [])) in that Region.
Hint: make the clients inside the loop with region_name=region.
"""
def inventory(regions):
    raise NotImplementedError  # YOUR CODE


class Ex10(Drill):
    """What is running where?"""
    tasks = ("2.2",)
    uses_aws = True

    def test_two_regions(self):
        east, west = self.client("s3", "us-east-1"), self.client("s3", "eu-west-1")
        east.create_bucket(Bucket="inv-east-bucket")
        west.create_bucket(Bucket="inv-west-bucket", CreateBucketConfiguration={"LocationConstraint": "eu-west-1"})
        ec2 = self.client("ec2", "us-east-1")
        image = ec2.describe_images(Owners=["amazon"])["Images"][0]["ImageId"]
        ec2.run_instances(ImageId=image, MinCount=2, MaxCount=2)
        self.client("sqs", "eu-west-1").create_queue(QueueName="inv-queue")
        self.assertEqual(inventory(["us-east-1", "eu-west-1"]), {
            "us-east-1": {"buckets": ["inv-east-bucket"], "instances": 2, "queues": 0},
            "eu-west-1": {"buckets": ["inv-west-bucket"], "instances": 0, "queues": 1},
        })

    def test_empty_region(self):
        self.assertEqual(inventory(["ap-southeast-2"]), {"ap-southeast-2": {"buckets": [], "instances": 0, "queues": 0}})
```

- [ ] **Step 2: Append to `solutions.py`**

```python
from botocore.config import Config
from botocore.exceptions import ClientError


def count_objects(s3, bucket, prefix="", page_size=1000):
    pages = s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix,
                                                          PaginationConfig={"PageSize": page_size})
    return sum(page.get("KeyCount", 0) for page in pages)


def bucket_exists(s3, name):
    try:
        s3.head_bucket(Bucket=name)
        return True
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code in ("404", "NoSuchBucket"):
            return False
        if code == "403":
            return True
        raise


def ensure_bucket(s3, name, region):
    if bucket_exists(s3, name):
        return "exists"
    kwargs = {"Bucket": name}
    if region != "us-east-1":
        kwargs["CreateBucketConfiguration"] = {"LocationConstraint": region}
    try:
        s3.create_bucket(**kwargs)
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "BucketAlreadyOwnedByYou":
            return "exists"
        raise
    return "created"


def transfer_cost(flows, price=PRICES):
    total = 0.0
    for source, destination, gb in flows:
        if source == "internet" and destination == "internet":
            raise ValueError("a flow must start or end in AWS")
        if source == "internet":
            continue
        if destination == "internet":
            total += gb * price["egress_internet_per_gb"]
        elif source == destination:
            continue
        elif source[:-1] == destination[:-1]:
            total += gb * price["inter_az_per_gb_each_way"] * 2
        else:
            total += gb * price["inter_region_per_gb"]
    return round(total, 4)


def make_client(service, region, total_attempts=5, connect_timeout=3, read_timeout=10):
    config = Config(retries={"total_max_attempts": total_attempts, "mode": "adaptive"},
                    connect_timeout=connect_timeout, read_timeout=read_timeout)
    return boto3.client(service, region_name=region, config=config)


def inventory(regions):
    report = {}
    for region in regions:
        s3 = boto3.client("s3", region_name=region)
        buckets = [b["Name"] for b in s3.list_buckets()["Buckets"]
                   if (s3.get_bucket_location(Bucket=b["Name"])["LocationConstraint"] or "us-east-1") == region]
        ec2 = boto3.client("ec2", region_name=region)
        instances = sum(len(r["Instances"]) for r in ec2.describe_instances()["Reservations"])
        queues = boto3.client("sqs", region_name=region).list_queues().get("QueueUrls", [])
        report[region] = {"buckets": sorted(buckets), "instances": instances, "queues": len(queues)}
    return report
```

(`PRICES` is defined in `exercises.py`; solutions run in that namespace, so the default argument resolves.)

- [ ] **Step 3: Append to `MUTANTS` in `_dev/mutants/week00.py`**

```python
MUTANTS += [
    {"id": "one-call", "drill": 6, "code": '''
def count_objects(s3, bucket, prefix="", page_size=1000):
    return s3.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=page_size).get("KeyCount", 0)
'''},
    {"id": "always-location", "drill": 7, "code": '''
def bucket_exists(s3, name):
    try:
        s3.head_bucket(Bucket=name)
        return True
    except ClientError as exc:
        if exc.response["Error"]["Code"] in ("404", "NoSuchBucket"):
            return False
        if exc.response["Error"]["Code"] == "403":
            return True
        raise
def ensure_bucket(s3, name, region):
    if bucket_exists(s3, name):
        return "exists"
    s3.create_bucket(Bucket=name, CreateBucketConfiguration={"LocationConstraint": region})
    return "created"
'''},
    {"id": "inter-az-once", "drill": 8, "code": '''
def transfer_cost(flows, price=PRICES):
    total = 0.0
    for source, destination, gb in flows:
        if source == "internet" and destination == "internet":
            raise ValueError("x")
        if source == "internet" or source == destination:
            continue
        if destination == "internet":
            total += gb * price["egress_internet_per_gb"]
        elif source[:-1] == destination[:-1]:
            total += gb * price["inter_az_per_gb_each_way"]
        else:
            total += gb * price["inter_region_per_gb"]
    return round(total, 4)
'''},
    {"id": "standard-mode", "drill": 9, "code": '''
import boto3
from botocore.config import Config
def make_client(service, region, total_attempts=5, connect_timeout=3, read_timeout=10):
    return boto3.client(service, region_name=region, config=Config(
        retries={"max_attempts": total_attempts, "mode": "standard"},
        connect_timeout=connect_timeout, read_timeout=read_timeout))
'''},
    {"id": "ignore-location", "drill": 10, "code": '''
import boto3
def inventory(regions):
    report = {}
    for region in regions:
        buckets = [b["Name"] for b in boto3.client("s3", region_name=region).list_buckets()["Buckets"]]
        ec2 = boto3.client("ec2", region_name=region)
        instances = sum(len(r["Instances"]) for r in ec2.describe_instances()["Reservations"])
        queues = boto3.client("sqs", region_name=region).list_queues().get("QueueUrls", [])
        report[region] = {"buckets": sorted(buckets), "instances": instances, "queues": len(queues)}
    return report
'''},
]
```

- [ ] **Step 4: Verify the whole week's drills**

```bash
.venv/Scripts/python.exe week_00_foundations_and_exam_technique/practice/exercises.py | tail -1
.venv/Scripts/python.exe week_00_foundations_and_exam_technique/practice/exercises.py --solutions | tail -1
.venv/Scripts/python.exe verify_course.py --week 0 2>&1 | grep -E "drills|stubs|solutions|mutant|★|tasks"
```

Expected: `0/10 passing`; `10/10 passing (solutions)`; every drill/mutant check ✔ (concept, README, quiz and lab checks stay ✘ until Tasks 12–13). If `test_counts_across_pages` makes the file slower than 60 s, report the timing — do not shrink the 250 objects below 201 (the test needs three pages).

- [ ] **Step 5: Commit** — skipped (no git).

---

### Task 12: Week 00 concept notes, demos, README and lab

**Files:**
- Create in `week_00_foundations_and_exam_technique/`: `concepts/01_how_the_exam_works.md`, `concepts/02_global_infrastructure.md`, `concepts/03_shared_responsibility_and_well_architected.md`, `concepts/04_availability_and_failure.md`, `concepts/05_tools_credentials_and_cost_basics.md`, `concepts/demo_boto3_basics.py`, `concepts/demo_availability.py`, `README.md`, `lab/LAB.md`, `lab/cleanup.py`

**Interfaces:**
- Consumes: `docs/facts.md` (every number), `docs/exam_guide.md` (task statements), Task 10–11 drill numbering, `_harness/labclean.main`.
- Produces: the `ref` targets Task 13's questions point at (exact file names above).

**Writing rules (every note):** first line `Exam tasks: …` (valid task ids); sections in this order — `## What it is`, `## How it works`, `## Numbers to know`, `## When to choose it`, `## Exam traps`, `## Cost angle`, `## Comparison` (a Markdown table); last line "Now do drill(s) NN… and the quiz questions on …". 150–300 lines, plain English, short sentences, no filler. Every number must appear in `docs/facts.md` (or be arithmetic shown in the note). Predict/decide answers from drills (e.g. Ex04's responsibilities) are **not** stated in the notes — the notes teach the rule, the drill makes the learner apply it.

- [ ] **Step 1: Write the five notes with this content**

| File | Exam tasks line | Must cover |
|---|---|---|
| `01_how_the_exam_works.md` | `Exam tasks: 1.1, 2.2, 3.2, 4.2` | format and scoring from `docs/facts.md` (65 = 50 + 15 unscored, 130 min, 720 scaled, compensatory, no guessing penalty); the 4 domains and weights; the 14 task statements as a table; how to read a scenario: find the deciding requirement (MOST cost-effective · LEAST operational overhead · highest availability · minimum changes · most secure), cross out options that break a hard constraint, then choose between the last two on the deciding requirement; "Select TWO" questions; keyword → direction table (≥ 12 rows, e.g. "least operational overhead" → managed/serverless, "decouple" → SQS/SNS/EventBridge, "millisecond reads at any scale" → DynamoDB, "static content worldwide" → CloudFront); time plan (≈ 2 min per question, flag and move on); the course's `quiz.py` and mock exams; "re-check the certification page before booking" |
| `02_global_infrastructure.md` | `Exam tasks: 2.2, 3.4` | Regions, Availability Zones (separate facilities, low-latency links), Local Zones, Wavelength Zones, Outposts, edge locations / points of presence; choosing a Region (data residency and compliance, latency to users, service availability, price); what is global vs Regional vs zonal (IAM/Route 53/CloudFront global; S3 buckets Regional; EC2 instances and EBS volumes zonal; subnets live in one AZ); AZ names vs AZ IDs (`us-east-1a` differs per account, `use1-az1` does not); comparison table of the location types |
| `03_shared_responsibility_and_well_architected.md` | `Exam tasks: 1.1, 1.2, 1.3` | security OF vs IN the cloud; how the line moves for IaaS (EC2) → managed (RDS) → serverless (Lambda); what never moves (your data, IAM, configuration, client-side encryption choices); the six Well-Architected pillars (operational excellence, security, reliability, performance efficiency, cost optimisation, sustainability) with 2 design principles each and the exam task statements each pillar maps to; comparison table EC2 vs RDS vs Lambda responsibilities (without giving away Ex04's exact rows) |
| `04_availability_and_failure.md` | `Exam tasks: 2.2` | availability as a fraction; series vs parallel with worked numbers; nines → downtime per month table (computed); single points of failure; multi-AZ by default; static stability (spare capacity already running) vs scaling on failure; the "lose one AZ" sizing rule with a worked example; preview of RTO/RPO (week 09) |
| `05_tools_credentials_and_cost_basics.md` | `Exam tasks: 1.1, 4.4` | console vs CLI vs SDK (boto3) vs CloudFormation; the credential chain boto3 searches (env vars → shared files/profiles → IAM Identity Center/SSO → instance/container role) and why long-lived access keys on laptops/EC2 are a risk; `aws configure sso` profiles; error codes (`404`, `403`, `NoSuchBucket`, `BucketAlreadyOwnedByYou`) and the us-east-1 LocationConstraint rule; pagination (1,000-key pages); retries (standard vs adaptive mode, total attempts, exponential backoff with jitter preview); how AWS bills (pay-as-you-go, data transfer: in free / out paid / inter-AZ both ways / inter-Region), the public IPv4 charge, Free vs Paid account plans from `docs/facts.md` (no "12-month free tier" promises); why the course runs offline (moto) |

- [ ] **Step 2: Write `concepts/demo_boto3_basics.py`**

```python
"""Demo — boto3 against a fake AWS (moto): identity, Regions, buckets, pagination, error codes.
Run it: python concepts/demo_boto3_basics.py   (offline; nothing here touches a real account)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.awslib.safety import force_utf8, use_fake_aws_env  # noqa: E402

force_utf8()
use_fake_aws_env()

import boto3  # noqa: E402
from botocore.exceptions import ClientError  # noqa: E402
from moto import mock_aws  # noqa: E402

with mock_aws():
    identity = boto3.client("sts").get_caller_identity()
    print(f"Who am I?   account {identity['Account']}   arn {identity['Arn']}")

    regions = sorted(r["RegionName"] for r in boto3.client("ec2", region_name="us-east-1").describe_regions()["Regions"])
    print(f"Regions:    {len(regions)} — first five {regions[:5]}")

    east = boto3.client("s3", region_name="us-east-1")
    east.create_bucket(Bucket="demo-east-bucket")
    west = boto3.client("s3", region_name="eu-west-1")
    west.create_bucket(Bucket="demo-west-bucket", CreateBucketConfiguration={"LocationConstraint": "eu-west-1"})
    for name in ("demo-east-bucket", "demo-west-bucket"):
        location = east.get_bucket_location(Bucket=name)["LocationConstraint"]
        print(f"Bucket {name:<18} LocationConstraint = {location!r}")

    try:
        east.create_bucket(Bucket="demo-x-bucket", CreateBucketConfiguration={"LocationConstraint": "us-east-1"})
    except ClientError as exc:
        print(f"us-east-1 with a LocationConstraint → {exc.response['Error']['Code']}")

    try:
        east.head_bucket(Bucket="demo-missing-bucket")
    except ClientError as exc:
        print(f"head_bucket on a missing bucket → error code {exc.response['Error']['Code']!r}")

    for i in range(120):
        east.put_object(Bucket="demo-east-bucket", Key=f"logs/{i:03d}", Body=b"")
    calls = []
    east.meta.events.register("before-call.s3.ListObjectsV2", lambda **kw: calls.append(1))
    pages = east.get_paginator("list_objects_v2").paginate(Bucket="demo-east-bucket", PaginationConfig={"PageSize": 50})
    total = sum(p.get("KeyCount", 0) for p in pages)
    print(f"Paginated count: {total} objects in {len(calls)} calls of up to 50 keys")
    print("\nNow do drills 05–07 and 10.")
```

- [ ] **Step 3: Write `concepts/demo_availability.py`**

```python
"""Demo — what "nines" mean in minutes, and why parallel beats series. Pure Python, no AWS."""
import math
import sys

for stream in (sys.stdout, sys.stderr):
    stream.reconfigure(encoding="utf-8", errors="replace")

print(f"{'availability':>14} {'down per 30 days':>18} {'down per year':>15}")
for a in (0.99, 0.999, 0.9995, 0.9999, 0.99999):
    month = (1 - a) * 30 * 24 * 60
    year = (1 - a) * 365 * 24 * 60
    print(f"{a * 100:>13.3f}% {month:>15.1f} min {year / 60:>12.2f} h")

lb, app, db = 0.9999, 0.99, 0.9995
one_app = math.prod((lb, app, db))
two_apps = math.prod((lb, 1 - (1 - app) ** 2, db))
print(f"\nload balancer → ONE app instance → database:  {one_app:.5f}")
print(f"load balancer → TWO app instances → database:  {two_apps:.5f}   (the database is now the weak link)")
print("\nNow do drills 02–03.")
```

- [ ] **Step 4: Write `README.md`**

Headings exactly: `# Week 00 — Foundations & exam technique`, `## Goals`, `## Your week`, `## Exam tasks covered`, `## Service comparison`, `## Interview questions`.
- Goals: 5 bullets (read any ARN; reason about availability numerically; know what is global/Regional/zonal; know who secures what; run boto3 safely; know the exam's format and how to attack a scenario).
- Your week (≈ 6–8 h, no milestone): concepts 01–05 + both demos (~2.5 h) → drills `python practice/exercises.py` until 10/10 (~2.5 h) → quiz `python quiz.py --week 0 -n 15` until ≥ 80 % (~45 min) → optional lab (~1 h; account safety first).
- Exam tasks covered: table of the task ids from the notes' `Exam tasks:` lines with titles from `docs/exam_guide.md`.
- Service comparison: Region vs AZ vs Local Zone vs Wavelength vs Outposts vs edge location (what, latency, when).
- Interview questions (8): e.g. "What is an Availability Zone and why deploy across several?", "How would you size a fleet to survive the loss of an AZ?", "Explain the shared responsibility model for RDS vs EC2.", "How does boto3 find credentials, and which way is safest on EC2?", "Why do you need pagination when listing S3?", "What does data transfer cost between AZs vs out to the internet?", "What are the six Well-Architected pillars?", "Why is 99.99 % availability hard to reach with a single database?".
- A line: "Before week 01, read `_harness/awslib/policy_eval.py`? **No** — it is week 01's answer key."

- [ ] **Step 5: Write `lab/LAB.md` and `lab/cleanup.py`**

`LAB.md` (≈ 60–90 min, ≈ 0 USD), sections in order:
1. **Before you start** — this lab uses your real AWS account; it is optional; everything the course grades runs offline. Create an account if needed and choose the plan knowingly (Free vs Paid facts from `docs/facts.md`; the Free plan becomes Paid if you join Organizations or set up Control Tower — the course never asks you to in a lab).
2. **Lock the root user** — MFA on root; no root access keys; sign out of root.
3. **An admin you sign in with** — enable IAM Identity Center; create a user and the `AdministratorAccess` permission set; assign it to your account.
4. **CLI with short-lived credentials** — install AWS CLI v2; `aws configure sso` → profile name `saa-lab`; `aws sts get-caller-identity --profile saa-lab`; note how the ARN shows an assumed role, not a user (link to week 01).
5. **Spending guard-rails** — Budgets → Zero spend budget and a Monthly cost budget (e.g. 5 USD) with your e-mail; Billing preferences → "Receive CloudWatch Billing Alerts"; CloudWatch (us-east-1) alarm on `EstimatedCharges` > 5 USD → SNS e-mail.
6. **First calls** — `aws s3api create-bucket --bucket saa-lab-<your-initials>-<random> --region us-east-1 --profile saa-lab` (no LocationConstraint in us-east-1!), then try eu-west-1 with and without `--create-bucket-configuration LocationConstraint=eu-west-1` and note the error; `aws s3api put-bucket-tagging --bucket … --tagging 'TagSet=[{Key=saa-course,Value=lab}]'` on every bucket you made; upload a file; `aws s3api list-objects-v2 --max-items 1` and see `NextToken`.
7. **Clean up** — `python lab/cleanup.py --profile saa-lab` (dry run, read the list), then `python lab/cleanup.py --profile saa-lab --yes`, for each Region you used (`--region eu-west-1`). Budgets, the billing alarm, the SNS topic and Identity Center stay — they are your safety net.
8. **What to write down** — your account ID, the assumed-role ARN, the error you got in step 6.

`cleanup.py`:

```python
"""Week 00 lab cleanup — deletes only S3 buckets tagged saa-course=lab. Dry run unless you add --yes.

    python lab/cleanup.py --profile saa-lab                 list what would go
    python lab/cleanup.py --profile saa-lab --yes           delete it (repeat with --region eu-west-1)
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.labclean import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(kinds=["s3_buckets"]))
```

- [ ] **Step 6: Verify**

```bash
for f in week_00_foundations_and_exam_technique/concepts/demo_*.py; do .venv/Scripts/python.exe "$f" | cat; done
.venv/Scripts/python.exe verify_course.py --week 0 2>&1 | grep -E "concept|demo|README|lab"
.venv/Scripts/python.exe verify_course.py --banks 2>&1 | grep "retired"
```

Expected: both demos print their tables/lines and exit 0; every concept/demo/README/lab check ✔; "no retired services taught as current" ✔. The main session also reads every note against `docs/facts.md` (spot-check every number) before accepting the task.

- [ ] **Step 7: Commit** — skipped (no git).

---

### Task 13: Week 00 quiz (15 questions) + the blind-solve tool

**Files:**
- Create: `week_00_foundations_and_exam_technique/quiz/questions.toml`, `_dev/blindsolve.py`
- Test: `_dev/tests/test_blindsolve.py`

**Interfaces:**
- Consumes: `quizlib.load_bank`, Task 12's notes (as `ref` targets), `docs/facts.md`.
- Produces: `_dev/blindsolve.py export BANK OUT.md` (stems + options, no answers/explanations, options in stored order) and `_dev/blindsolve.py compare BANK ANSWERS.json` (prints every id where the blind answer differs; exit 1 if any). `ANSWERS.json` = `{"w00-q01": ["B"], …}`. Used by every later quiz task.

- [ ] **Step 1: Write the failing test `_dev/tests/test_blindsolve.py`**

```python
import json
import subprocess
import sys
from pathlib import Path

from bankgen import balanced_raws, toml_bank

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable


def test_export_hides_answers_and_compare_finds_disagreements(tmp_path):
    bank = tmp_path / "questions.toml"
    raws = balanced_raws(12, multi=2, week=0)
    bank.write_text(toml_bank(raws), encoding="utf-8")
    out = tmp_path / "blind.md"
    proc = subprocess.run([PY, str(ROOT / "_dev" / "blindsolve.py"), "export", str(bank), str(out)],
                          capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    text = out.read_text(encoding="utf-8")
    assert "w00-q01" in text and "Because" not in text  # explanations (and so answers) stay hidden
    assert "(Select TWO.)" in text
    answers = {r["id"]: r["answer"] for r in raws}
    answers["w00-q05"] = ["A"] if raws[4]["answer"] != ["A"] else ["B"]
    (tmp_path / "answers.json").write_text(json.dumps(answers), encoding="utf-8")
    proc = subprocess.run([PY, str(ROOT / "_dev" / "blindsolve.py"), "compare", str(bank), str(tmp_path / "answers.json")],
                          capture_output=True, text=True, timeout=120)
    assert proc.returncode == 1 and "w00-q05" in proc.stdout and "1 disagreement" in proc.stdout
```

- [ ] **Step 2: Write `_dev/blindsolve.py`**

```python
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
```

- [ ] **Step 3: Run the test**

```bash
.venv/Scripts/python.exe -m pytest _dev/tests/test_blindsolve.py
```

Expected: `1 passed`.

- [ ] **Step 4: Write the 15 questions**

Rules: Global Constraints "Quiz rules"; schema from Task 4; every number from `docs/facts.md`; every `ref` is one of Task 12's five notes; original scenarios (a company, a constraint, a deciding requirement); distractors are real AWS options that are wrong *for this scenario*; explanations say why each option is right or wrong in 1–3 sentences; vary the correct letter (the checker enforces spread and "correct is not the longest").

| ids | domain · task | kind | topic |
|---|---|---|---|
| w00-q01 | 2 · 2.2 | single | spread instances across AZs to survive an AZ failure |
| w00-q02 | 2 · 2.2 | single | static stability: capacity per AZ to keep N instances after losing one AZ |
| w00-q03 | 2 · 2.2 | single | series availability: which component limits the whole |
| w00-q04 | 3 · 3.4 | single | Region choice for latency vs data residency |
| w00-q05 | 3 · 3.4 | single | Local Zones / Wavelength / Outposts — which fits a low-latency on-premises or metro need |
| w00-q06 | 1 · 1.2 | single | shared responsibility on EC2 vs RDS (patching) |
| w00-q07 | 1 · 1.3 | single | data you put in S3 is the customer's to classify and protect |
| w00-q08 | 1 · 1.1 | single | credentials on an EC2 instance: instance role vs access keys |
| w00-q09 | 1 · 1.1 | multi (choose 2) | securing a brand-new account: root MFA + Identity Center admin (vs root access keys, sharing root, IAM user per team) |
| w00-q10 | 2 · 2.1 | single | retries with backoff vs failing fast for throttled API calls |
| w00-q11 | 4 · 4.4 | single | cheapest data path: same-AZ vs cross-AZ vs internet egress |
| w00-q12 | 4 · 4.4 | single | public IPv4 charges on idle Elastic IPs |
| w00-q13 | 4 · 4.2 | single | "MOST cost-effective" vs "LEAST operational overhead" — same scenario, two different right answers (write the LEAST-overhead one) |
| w00-q14 | 3 · 3.2 | single | managed vs self-managed for least operational overhead |
| w00-q15 | 2 · 2.2 | multi (choose 2) | single points of failure in a described architecture |

- [ ] **Step 5: Validate**

```bash
.venv/Scripts/python.exe verify_course.py --week 0 2>&1 | grep -i quiz
.venv/Scripts/python.exe quiz.py --week 0 -n 3 --seed 1 < /dev/null | head -40
```

Expected: the three quiz checks ✔; the quiz prints question 1 and exits cleanly at EOF.

- [ ] **Step 6: Blind-solve (main session runs this, not the implementer)**

```bash
.venv/Scripts/python.exe _dev/blindsolve.py export week_00_foundations_and_exam_technique/quiz/questions.toml "$SCRATCH/w00-blind.md"
```

Dispatch a **fresh** subagent (no access to the bank file; give it only `w00-blind.md`) with: "You are taking an AWS SAA-C03 practice quiz. Answer every question; reply with only the JSON object described at the top." Save its reply as `$SCRATCH/w00-answers.json`, then:

```bash
.venv/Scripts/python.exe _dev/blindsolve.py compare week_00_foundations_and_exam_technique/quiz/questions.toml "$SCRATCH/w00-answers.json"
```

For every disagreement the main session decides: the bank is wrong (fix answer/explanation), the question is ambiguous (rewrite the stem so exactly one option meets the deciding requirement), or the solver is wrong (keep, but make sure the explanation addresses the solver's choice). Re-run `verify_course.py --week 0`. Record the disagreement count and each ruling in the pilot report (Task 20). `$SCRATCH` is the session scratchpad directory — blind files never go into the course folder.

- [ ] **Step 7: Commit** — skipped (no git).

---

### Task 14: Week 01 drills 01–05 (the policy evaluator, least privilege)

**Files:**
- Create: `week_01_iam_and_governance/practice/exercises.py` (header + drills 01–05 + `run()`), `week_01_iam_and_governance/practice/solutions.py` (01–05), `_dev/mutants/week01.py` (01–05)

**Interfaces:**
- Consumes: `awsdrill.Drill`, `awsdrill.run`; `awslib.policy_eval` as `ref` (reference used by tests from drill 05 on) and its `Request`, `account_of`, `principal_matches` (given to the learner); `awslib.prices`.
- Produces: learner names `action_matches`, `resource_matches`, `condition_matches`, `evaluate_policies`, `evaluate`, `APP_POLICY`; constants `BROAD_POLICY`, `ACCOUNT = "111122223333"`. Task 15 appends 06–10.

- [ ] **Step 1: Write `exercises.py` with drills 01–05**

```python
"""
Week 01 drills — IAM & multi-account governance
===============================================
Run:    python practice/exercises.py          every drill
        python practice/exercises.py 3        drill 3 only
Drills 01–04 build a small IAM policy evaluator — the logic behind half the questions in the
Secure domain. Do them in order: 03 uses 01 and 02; 04 uses 03.
The course's own evaluator (_harness/awslib/policy_eval.py) is the answer key for 01–04 — don't
open it until you are done. Drills 05–10 use it (as `ref`) to check the policies YOU write.
Everything runs offline against moto (a fake AWS) with fake credentials.
"""
import pathlib
import re  # noqa: F401  (you will want it)
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.awsdrill import Drill, run  # noqa: E402
from _harness.awslib import policy_eval as ref  # noqa: E402
from _harness.awslib import prices  # noqa: E402
from _harness.awslib.policy_eval import Request, account_of, principal_matches  # noqa: E402,F401

ACCOUNT = "111122223333"
PARTNER = "444455556666"
APP = f"arn:aws:sts::{ACCOUNT}:assumed-role/shortly-app/i-0abc"
FULL_ACCESS = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]}


def allow(action, resource="*", **extra):
    return {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": action, "Resource": resource, **extra}]}


def deny(action, resource="*", **extra):
    return {"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Action": action, "Resource": resource, **extra}]}


# ── Exercise 01 ★: Wildcards in actions and resources ────────────────
"""
action_matches(pattern, action) -> bool
    Actions are case-insensitive. In a pattern, * matches any run of characters and ? exactly one.
    action_matches("s3:Get*", "s3:GetObject") is True;  action_matches("ec2:*", "s3:GetObject") is False
resource_matches(pattern, arn) -> bool
    Resources are case-SENSITIVE. "*" alone matches everything. Otherwise split pattern and ARN into
    their six ':'-separated parts (split(":", 5)) and match part by part, so a wildcard never spans a
    ':' — "arn:aws:*:us-east-1:*:*" matches nothing in eu-west-1. Inside one part, * does match '/':
    "arn:aws:s3:::shortly-assets/*" matches "arn:aws:s3:::shortly-assets/uploads/a.png".
    If either side lacks six parts, compare the whole strings with the same wildcard rules.
Hint: build a regex — re.escape every character except * (→ ".*") and ? (→ "."), then re.fullmatch.
"""
def action_matches(pattern, action):
    raise NotImplementedError  # YOUR CODE


def resource_matches(pattern, arn):
    raise NotImplementedError  # YOUR CODE


class Ex01(Drill):
    """Wildcards in actions and resources ★"""
    tasks = ("1.1",)

    def test_actions(self):
        cases = [("s3:GetObject", "s3:GetObject", True), ("s3:getobject", "S3:GetObject", True),
                 ("s3:Get*", "s3:GetObjectTagging", True), ("*", "ec2:RunInstances", True),
                 ("s3:Get?bject", "s3:GetObject", True), ("s3:Get*", "s3:PutObject", False),
                 ("ec2:*", "s3:GetObject", False)]
        for pattern, action, want in cases:
            with self.subTest(pattern=pattern, action=action):
                self.assertIs(action_matches(pattern, action), want)

    def test_resources(self):
        obj = "arn:aws:s3:::shortly-assets/uploads/a.png"
        cases = [("*", obj, True), ("arn:aws:s3:::shortly-assets/*", obj, True),
                 ("arn:aws:s3:::shortly-assets", obj, False), ("arn:aws:s3:::Shortly-assets/*", obj, False),
                 ("arn:aws:dynamodb:*:*:table/shortly-*", f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-links", True),
                 ("arn:aws:dynamodb:*:*:table/shortly-*", f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/billing", False),
                 ("arn:aws:*:us-east-1:*:*", f"arn:aws:sqs:eu-west-1:{ACCOUNT}:clicks", False),
                 ("arn:aws:lambda:us-east-1:*:function:f*", f"arn:aws:lambda:us-east-1:{ACCOUNT}:function:fn:PROD", True)]
        for pattern, arn, want in cases:
            with self.subTest(pattern=pattern, arn=arn):
                self.assertIs(resource_matches(pattern, arn), want)


# ── Exercise 02 ★: Conditions ────────────────────────────────────────
"""
condition_matches(condition, context) -> bool
`condition` is a statement's Condition block (or None); `context` holds the request's keys:
    {"StringEquals": {"aws:RequestedRegion": ["us-east-1", "eu-west-1"]}, "Bool": {"aws:SecureTransport": "true"}}
Rules (from the IAM documentation):
  • every operator, and every key inside it, must hold (AND); several values for ONE key are alternatives (OR)
  • condition keys are case-insensitive ("aws:sourceip" finds "aws:SourceIp")
  • support: StringEquals, StringNotEquals, StringEqualsIgnoreCase, StringLike (wildcards, case-sensitive),
    Bool (compare "true"/"false"; the context may hold True/False), IpAddress, NotIpAddress (CIDR blocks),
    NumericEquals, NumericLessThan, NumericLessThanEquals, NumericGreaterThan, NumericGreaterThanEquals,
    and Null ("true" means the key must be ABSENT, "false" that it must be present)
  • the suffix …IfExists: when the key is absent, that operator passes
  • when a key is absent: positive operators fail; negated ones (StringNotEquals, NotIpAddress) pass
  • ForAnyValue: / ForAllValues: prefixes, for keys whose context value is a list:
        ForAnyValue → at least one context value matches; absent or empty → fails
        ForAllValues → every context value matches; absent or empty → PASSES (a classic trap)
  • any other operator → ValueError
Hint: write one helper that compares ONE context value with ONE policy value, then build up from it.
"""
def condition_matches(condition, context):
    raise NotImplementedError  # YOUR CODE


class Ex02(Drill):
    """Conditions ★"""
    tasks = ("1.1",)

    CASES = [
        (None, {}, True),
        ({"StringEquals": {"aws:RequestedRegion": ["us-east-1", "eu-west-1"]}}, {"aws:RequestedRegion": "eu-west-1"}, True),
        ({"StringEquals": {"aws:RequestedRegion": "us-east-1"}}, {"aws:requestedregion": "us-east-1"}, True),
        ({"StringEquals": {"aws:RequestedRegion": "us-east-1"}}, {}, False),
        ({"StringNotEquals": {"aws:RequestedRegion": ["us-east-1", "us-west-2"]}}, {"aws:RequestedRegion": "eu-west-1"}, True),
        ({"StringNotEquals": {"aws:RequestedRegion": ["us-east-1", "us-west-2"]}}, {"aws:RequestedRegion": "us-west-2"}, False),
        ({"StringNotEquals": {"aws:RequestedRegion": "us-east-1"}}, {}, True),
        ({"StringLike": {"s3:prefix": "home/*"}}, {"s3:prefix": "home/alice/"}, True),
        ({"StringLike": {"s3:prefix": "home/*"}}, {"s3:prefix": "Home/alice/"}, False),
        ({"StringEqualsIgnoreCase": {"aws:PrincipalTag/team": "Data"}}, {"aws:PrincipalTag/team": "data"}, True),
        ({"Bool": {"aws:SecureTransport": "true"}}, {"aws:SecureTransport": True}, True),
        ({"Bool": {"aws:SecureTransport": "true"}}, {"aws:SecureTransport": False}, False),
        ({"Bool": {"aws:MultiFactorAuthPresent": "true"}}, {}, False),
        ({"BoolIfExists": {"aws:MultiFactorAuthPresent": "false"}}, {}, True),
        ({"IpAddress": {"aws:SourceIp": "203.0.113.0/24"}}, {"aws:SourceIp": "203.0.113.7"}, True),
        ({"NotIpAddress": {"aws:SourceIp": ["203.0.113.0/24", "198.51.100.0/24"]}}, {"aws:SourceIp": "192.0.2.1"}, True),
        ({"NumericLessThanEquals": {"s3:max-keys": "100"}}, {"s3:max-keys": 50}, True),
        ({"NumericGreaterThan": {"s3:max-keys": "100"}}, {"s3:max-keys": 50}, False),
        ({"Null": {"aws:TokenIssueTime": "true"}}, {}, True),
        ({"Null": {"aws:TokenIssueTime": "false"}}, {}, False),
        ({"ForAnyValue:StringEquals": {"aws:TagKeys": ["env", "team"]}}, {"aws:TagKeys": ["owner", "env"]}, True),
        ({"ForAnyValue:StringEquals": {"aws:TagKeys": ["env"]}}, {}, False),
        ({"ForAllValues:StringEquals": {"aws:TagKeys": ["env", "team"]}}, {"aws:TagKeys": ["env", "owner"]}, False),
        ({"ForAllValues:StringEquals": {"aws:TagKeys": ["env"]}}, {}, True),
        ({"StringEquals": {"a": "1"}, "Bool": {"b": "true"}}, {"a": "1", "b": False}, False),
        ({"StringEquals": {"a": "1", "c": "2"}}, {"a": "1", "c": "3"}, False),
    ]

    def test_cases(self):
        for condition, context, want in self.CASES:
            with self.subTest(condition=condition, context=context):
                self.assertIs(condition_matches(condition, context), want)

    def test_unknown_operator(self):
        with self.assertRaises(ValueError):
            condition_matches({"StringSoundsLike": {"a": "b"}}, {"a": "b"})


# ── Exercise 03 ★: Evaluate identity policies ────────────────────────
"""
evaluate_policies(policies, request) -> "Allow" | "ExplicitDeny" | "ImplicitDeny"
`policies` are identity-based policy documents; `request` is a Request(principal, action, resource, context).
A statement applies when ALL of these hold:
  • its Action matches (any pattern in it) — or, with NotAction, the action matches NONE of them
  • its Resource matches — or, with NotResource, matches none (a statement with neither never applies)
  • its Condition holds
Then: any applicable Deny → "ExplicitDeny" (even when an Allow also applies); otherwise any applicable
Allow → "Allow"; otherwise "ImplicitDeny" — the default when nothing says yes.
"Statement" may be one dict or a list; Action/NotAction/Resource/NotResource may be a string or a list.
Use YOUR action_matches, resource_matches and condition_matches.
Example: evaluate_policies([allow("s3:*"), deny("s3:DeleteObject")], Request(APP, "s3:DeleteObject", "*")) == "ExplicitDeny"
"""
def evaluate_policies(policies, request):
    raise NotImplementedError  # YOUR CODE


class Ex03(Drill):
    """Evaluate identity policies ★"""
    tasks = ("1.1",)

    def test_deny_beats_allow_in_any_order(self):
        policies = [allow("s3:*", "arn:aws:s3:::shortly-assets/*"), deny("s3:DeleteObject")]
        self.assertEqual(evaluate_policies(policies, Request(APP, "s3:GetObject", "arn:aws:s3:::shortly-assets/a")), "Allow")
        self.assertEqual(evaluate_policies(policies, Request(APP, "s3:DeleteObject", "arn:aws:s3:::shortly-assets/a")), "ExplicitDeny")

    def test_nothing_says_yes(self):
        self.assertEqual(evaluate_policies([allow("s3:GetObject")], Request(APP, "ec2:RunInstances", "*")), "ImplicitDeny")
        self.assertEqual(evaluate_policies([], Request(APP, "s3:GetObject", "*")), "ImplicitDeny")

    def test_not_action_and_not_resource(self):
        guard = {"Statement": {"Effect": "Deny", "NotAction": ["iam:*", "sts:*"], "Resource": "*"}}
        self.assertEqual(evaluate_policies([FULL_ACCESS, guard], Request(APP, "s3:PutObject", "*")), "ExplicitDeny")
        self.assertEqual(evaluate_policies([FULL_ACCESS, guard], Request(APP, "iam:ListRoles", "*")), "Allow")
        most = {"Statement": [{"Effect": "Allow", "Action": "s3:*", "NotResource": "arn:aws:s3:::secrets/*"}]}
        self.assertEqual(evaluate_policies([most], Request(APP, "s3:GetObject", "arn:aws:s3:::secrets/k")), "ImplicitDeny")

    def test_conditions_are_used(self):
        tls_only = allow("s3:GetObject", Condition={"Bool": {"aws:SecureTransport": "true"}})
        self.assertEqual(evaluate_policies([tls_only], Request(APP, "s3:GetObject", "*", {"aws:SecureTransport": True})), "Allow")
        self.assertEqual(evaluate_policies([tls_only], Request(APP, "s3:GetObject", "*", {"aws:SecureTransport": False})), "ImplicitDeny")

    def test_statement_without_resource_never_applies(self):
        broken = {"Statement": [{"Effect": "Allow", "Action": "s3:GetObject"}]}
        self.assertEqual(evaluate_policies([broken], Request(APP, "s3:GetObject", "*")), "ImplicitDeny")


# ── Exercise 04 ★: Every policy type together ────────────────────────
"""
evaluate(request, *, identity=(), resource_policy=None, scps=None, boundary=None, session=None,
         resource_account=None) -> "Allow" | "ExplicitDeny" | "ImplicitDeny"
Combine the policy types the way AWS does:
  1. an explicit Deny in ANY of them (identity, resource, SCPs, boundary, session) → "ExplicitDeny"
  2. scps is a list of LEVELS (root → OU → account), each a list of SCP documents. EVERY level must
     allow the action — SCPs never grant anything by themselves — otherwise "ImplicitDeny"
  3. the identity policies OR the resource-based policy must allow it. Cross-account — when the
     caller's account, account_of(request.principal), differs from the resource's account
     (resource_account, else account_of(request.resource)) — BOTH must allow it
  4. a permissions boundary and a session policy, when given, must also allow it
  5. otherwise → "Allow"
A resource-based policy (e.g. a bucket policy) is like an identity policy except each statement also
needs its Principal to match the caller: use principal_matches(statement["Principal"], request.principal)
— it and account_of are given to you. Use your evaluate_policies for the identity-style policy sets.
(Real AWS has one corner this ignores: a same-account resource policy that names an IAM user directly
is not limited by that user's permissions boundary. The exam almost never goes there.)
"""
def evaluate(request, *, identity=(), resource_policy=None, scps=None, boundary=None, session=None, resource_account=None):
    raise NotImplementedError  # YOUR CODE


class Ex04(Drill):
    """Every policy type together ★"""
    tasks = ("1.1",)
    GET = Request(APP, "s3:GetObject", "arn:aws:s3:::shortly-assets/a.png")

    def test_scp_levels(self):
        self.assertEqual(evaluate(self.GET, identity=[FULL_ACCESS], scps=[[FULL_ACCESS], [FULL_ACCESS]]), "Allow")
        self.assertEqual(evaluate(self.GET, identity=[FULL_ACCESS], scps=[[FULL_ACCESS], [allow("ec2:*")]]), "ImplicitDeny")
        self.assertEqual(evaluate(self.GET, identity=[FULL_ACCESS], scps=[[FULL_ACCESS, deny("s3:*")]]), "ExplicitDeny")
        self.assertEqual(evaluate(self.GET, identity=[], scps=[[FULL_ACCESS]]), "ImplicitDeny")

    def test_boundary_and_session(self):
        both = [allow(["s3:*", "ec2:*"])]
        self.assertEqual(evaluate(Request(APP, "ec2:RunInstances", "*"), identity=both, boundary=allow("s3:*")), "ImplicitDeny")
        self.assertEqual(evaluate(self.GET, identity=both, boundary=allow("s3:*")), "Allow")
        self.assertEqual(evaluate(self.GET, identity=both, session=allow("s3:List*")), "ImplicitDeny")

    def test_same_account_bucket_policy_is_enough(self):
        bucket = {"Statement": [{"Effect": "Allow", "Principal": {"AWS": f"arn:aws:iam::{ACCOUNT}:role/shortly-app"},
                                 "Action": "s3:GetObject", "Resource": "arn:aws:s3:::shortly-assets/*"}]}
        self.assertEqual(evaluate(self.GET, resource_policy=bucket, resource_account=ACCOUNT), "Allow")
        other = {"Statement": [{**bucket["Statement"][0], "Principal": {"AWS": f"arn:aws:iam::{ACCOUNT}:role/someone-else"}}]}
        self.assertEqual(evaluate(self.GET, resource_policy=other, resource_account=ACCOUNT), "ImplicitDeny")

    def test_cross_account_needs_both(self):
        partner = Request(f"arn:aws:iam::{PARTNER}:role/reporting", "s3:GetObject", "arn:aws:s3:::shortly-assets/r.csv")
        bucket = {"Statement": [{"Effect": "Allow", "Principal": {"AWS": f"arn:aws:iam::{PARTNER}:root"},
                                 "Action": "s3:GetObject", "Resource": "arn:aws:s3:::shortly-assets/*"}]}
        theirs = [allow("s3:GetObject", "arn:aws:s3:::shortly-assets/*")]
        self.assertEqual(evaluate(partner, identity=theirs, resource_account=ACCOUNT), "ImplicitDeny")
        self.assertEqual(evaluate(partner, resource_policy=bucket, resource_account=ACCOUNT), "ImplicitDeny")
        self.assertEqual(evaluate(partner, identity=theirs, resource_policy=bucket, resource_account=ACCOUNT), "Allow")

    def test_bucket_policy_deny_wins(self):
        tls = {"Statement": [{"Effect": "Deny", "Principal": "*", "Action": "s3:*", "Resource": "*",
                              "Condition": {"Bool": {"aws:SecureTransport": "false"}}}]}
        plain = Request(APP, "s3:GetObject", "arn:aws:s3:::shortly-assets/a.png", {"aws:SecureTransport": False})
        self.assertEqual(evaluate(plain, identity=[allow("s3:GetObject")], resource_policy=tls), "ExplicitDeny")


# ── Exercise 05 (fix the bug): Least privilege ───────────────────────
"""
shortly's web app needs exactly these permissions (account 111122223333, Region us-east-1):
  1. read its database secret:   secretsmanager:GetSecretValue on
                                 arn:aws:secretsmanager:us-east-1:111122223333:secret:shortly/db-*
  2. read and update daily click counts:  dynamodb:GetItem and dynamodb:UpdateItem on
                                 arn:aws:dynamodb:us-east-1:111122223333:table/shortly-clicks-daily
  3. read and write user uploads: s3:GetObject and s3:PutObject on arn:aws:s3:::shortly-assets/uploads/*
  4. queue click events:          sqs:SendMessage on arn:aws:sqs:us-east-1:111122223333:shortly-clicks
BROAD_POLICY was written in a hurry: it lets the app delete every table, bucket and secret in the
account — and it still forgot the queue, so click events fail. Replace APP_POLICY with a policy that
allows exactly those actions on exactly those resources:
no "*" inside any Action, and no Resource that is just "*". (Secrets Manager adds 6 random characters
to secret ARNs, which is why need 1 ends in "db-*".)
The tests check your policy with the course's reference evaluator.
"""
BROAD_POLICY = {"Version": "2012-10-17", "Statement": [
    {"Effect": "Allow", "Action": ["s3:*", "dynamodb:*", "secretsmanager:*"], "Resource": "*"}]}
APP_POLICY = BROAD_POLICY   # FIX ME


class Ex05(Drill):
    """Least privilege (fix the bug)"""
    tasks = ("1.1", "1.2")
    NEEDS = [
        ("secretsmanager:GetSecretValue", f"arn:aws:secretsmanager:us-east-1:{ACCOUNT}:secret:shortly/db-a1B2c3"),
        ("dynamodb:GetItem", f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-clicks-daily"),
        ("dynamodb:UpdateItem", f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-clicks-daily"),
        ("s3:GetObject", "arn:aws:s3:::shortly-assets/uploads/logo.png"),
        ("s3:PutObject", "arn:aws:s3:::shortly-assets/uploads/logo.png"),
        ("sqs:SendMessage", f"arn:aws:sqs:us-east-1:{ACCOUNT}:shortly-clicks"),
    ]
    MUST_NOT = [
        ("dynamodb:DeleteTable", f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-clicks-daily"),
        ("dynamodb:GetItem", f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/billing"),
        ("s3:DeleteObject", "arn:aws:s3:::shortly-assets/uploads/logo.png"),
        ("s3:GetObject", "arn:aws:s3:::shortly-assets/private/keys.txt"),
        ("s3:PutBucketPolicy", "arn:aws:s3:::shortly-assets"),
        ("sqs:DeleteQueue", f"arn:aws:sqs:us-east-1:{ACCOUNT}:shortly-clicks"),
        ("sqs:ReceiveMessage", f"arn:aws:sqs:us-east-1:{ACCOUNT}:shortly-clicks"),
        ("secretsmanager:GetSecretValue", f"arn:aws:secretsmanager:us-east-1:{ACCOUNT}:secret:prod/payments-x1Y2z3"),
        ("secretsmanager:DeleteSecret", f"arn:aws:secretsmanager:us-east-1:{ACCOUNT}:secret:shortly/db-a1B2c3"),
    ]

    def test_can_do_its_job(self):
        for action, arn in self.NEEDS:
            with self.subTest(action=action):
                self.assertEqual(ref.evaluate_policies([APP_POLICY], Request(APP, action, arn)), "Allow",
                                 f"the app still needs {action} on {arn}")

    def test_cannot_do_anything_else(self):
        for action, arn in self.MUST_NOT:
            with self.subTest(action=action, arn=arn):
                self.assertNotEqual(ref.evaluate_policies([APP_POLICY], Request(APP, action, arn)), "Allow",
                                    f"the app must NOT be allowed {action} on {arn}")

    def test_no_wildcard_actions_or_star_resources(self):
        for st in ref.statements(APP_POLICY):
            with self.subTest(statement=st):
                self.assertFalse(any("*" in a for a in ref.as_list(st.get("Action"))), "no * inside any Action")
                self.assertNotIn("*", ref.as_list(st.get("Resource")), 'no Resource that is just "*"')
```

End the file with the `if __name__ == "__main__": run()` block (Task 15 inserts above it).

- [ ] **Step 2: Run it — every drill fails on its stubs**

```bash
.venv/Scripts/python.exe week_01_iam_and_governance/practice/exercises.py
```

Expected: `0/5 passing`; drill 05 fails with "the app still needs sqs:SendMessage …" (the broad policy forgot the queue) — all three of its tests are red.

- [ ] **Step 3: Write `solutions.py` (01–05)**

```python
"""Reference solutions for week 01.

Drills 01–04: the course's reference evaluator IS the solution — read _harness/awslib/policy_eval.py
(action_matches, resource_matches, condition_matches, evaluate_policies, evaluate) and compare it with
yours. It is written to be read: short functions, one rule each.
"""
import json

import boto3

from _harness.awslib.policy_eval import (action_matches, condition_matches, evaluate,  # noqa: F401
                                         evaluate_policies, resource_matches)

APP_POLICY = {"Version": "2012-10-17", "Statement": [
    {"Sid": "ReadDbSecret", "Effect": "Allow", "Action": "secretsmanager:GetSecretValue",
     "Resource": f"arn:aws:secretsmanager:us-east-1:{ACCOUNT}:secret:shortly/db-*"},
    {"Sid": "ClickCounts", "Effect": "Allow", "Action": ["dynamodb:GetItem", "dynamodb:UpdateItem"],
     "Resource": f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-clicks-daily"},
    {"Sid": "Uploads", "Effect": "Allow", "Action": ["s3:GetObject", "s3:PutObject"],
     "Resource": "arn:aws:s3:::shortly-assets/uploads/*"},
    {"Sid": "SendClicks", "Effect": "Allow", "Action": "sqs:SendMessage",
     "Resource": f"arn:aws:sqs:us-east-1:{ACCOUNT}:shortly-clicks"},
]}
```

- [ ] **Step 4: Write `_dev/mutants/week01.py` (01–05)**

```python
"""Deliberately wrong implementations for week 01 — each must be caught by its drill."""
MUTANTS = [
    {"id": "case-sensitive-actions", "drill": 1, "code": '''
import fnmatch
from _harness.awslib.policy_eval import resource_matches
def action_matches(pattern, action):
    return fnmatch.fnmatchcase(action, pattern)
'''},
    {"id": "negated-missing-fails", "drill": 2, "code": '''
from _harness.awslib import policy_eval as _r
def condition_matches(condition, context):
    for operator, block in (condition or {}).items():
        if operator.startswith("StringNotEquals"):
            for key in block:
                if _r._lookup(context, key) is None:
                    return False
    return _r.condition_matches(condition, context)
'''},
    {"id": "first-match-wins", "drill": 3, "code": '''
from _harness.awslib.policy_eval import statements, statement_applies
def evaluate_policies(policies, request):
    for policy in policies:
        for st in statements(policy):
            if statement_applies(st, request):
                return "Allow" if st.get("Effect") == "Allow" else "ExplicitDeny"
    return "ImplicitDeny"
'''},
    {"id": "cross-account-either", "drill": 4, "code": '''
from _harness.awslib import policy_eval as _r
def evaluate(request, *, identity=(), resource_policy=None, scps=None, boundary=None, session=None, resource_account=None):
    return _r.evaluate(request, identity=identity, resource_policy=resource_policy, scps=scps, boundary=boundary,
                       session=session, resource_account=_r.account_of(request.principal))
'''},
    {"id": "s3-star-on-uploads", "drill": 5, "code": '''
APP_POLICY = {"Version": "2012-10-17", "Statement": [
    {"Effect": "Allow", "Action": "secretsmanager:GetSecretValue",
     "Resource": "arn:aws:secretsmanager:us-east-1:111122223333:secret:shortly/db-*"},
    {"Effect": "Allow", "Action": ["dynamodb:GetItem", "dynamodb:UpdateItem"],
     "Resource": "arn:aws:dynamodb:us-east-1:111122223333:table/shortly-clicks-daily"},
    {"Effect": "Allow", "Action": "s3:*", "Resource": "arn:aws:s3:::shortly-assets/uploads/*"},
    {"Effect": "Allow", "Action": "sqs:SendMessage", "Resource": "arn:aws:sqs:us-east-1:111122223333:shortly-clicks"},
]}
'''},
]
```

- [ ] **Step 5: Check stubs, solutions, mutants**

```bash
.venv/Scripts/python.exe week_01_iam_and_governance/practice/exercises.py --solutions | tail -1
for id in case-sensitive-actions negated-missing-fails first-match-wins cross-account-either s3-star-on-uploads; do
  .venv/Scripts/python.exe week_01_iam_and_governance/practice/exercises.py --solutions --mutant "_dev/mutants/week01.py#$id" | tail -1
done
```

Expected: `5/5 passing (solutions)`; each mutant `4/5 passing (solutions)`.

- [ ] **Step 6: Commit** — skipped (no git).

---

### Task 15: Week 01 drills 06–10 (policy generation, roles, trust, SCPs, predictions)

**Files:**
- Modify: `week_01_iam_and_governance/practice/exercises.py` (insert above the final `if __name__` block), `practice/solutions.py` (append), `_dev/mutants/week01.py` (append)

**Interfaces:**
- Consumes: Task 14's file; `prices.tiers("s3_standard_tiers")`, `prices.tiered_cost`.
- Produces: learner names `generate_policy`, `create_app_role`, `whoami_as`, `TRUST_POLICY`, `create_partner_role`, `region_guardrail_scp`, `attach_guardrail`, `pooled_savings`, `PREDICTIONS`; test data `SCENARIOS`.

- [ ] **Step 1: Insert drills 06–10 into `exercises.py`**

```python
# ── Exercise 06 ★: Write the policy from what the app really did ─────
"""
generate_policy(access_log) -> dict
access_log lists the (action, resource) pairs your app actually called — what IAM Access Analyzer
reads from CloudTrail when it generates a policy. Return the least-privilege policy document:
    {"Version": "2012-10-17", "Statement": [...]}
with ONE Allow statement per distinct resource: "Action" = the sorted distinct actions used on that
resource, "Resource" = that ARN. Sort the statements by resource. Repeats in the log appear once.
Example:
  generate_policy([("s3:GetObject", "arn:aws:s3:::b/k"), ("s3:GetObject", "arn:aws:s3:::b/k")]) ==
      {"Version": "2012-10-17", "Statement": [
          {"Effect": "Allow", "Action": ["s3:GetObject"], "Resource": "arn:aws:s3:::b/k"}]}
Why not one statement with every action and every resource? Because it would also allow every
action on every OTHER resource in the list.
"""
def generate_policy(access_log):
    raise NotImplementedError  # YOUR CODE


class Ex06(Drill):
    """Write the policy from what the app really did ★"""
    tasks = ("1.1",)
    TABLE = f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-clicks-daily"
    QUEUE = f"arn:aws:sqs:us-east-1:{ACCOUNT}:shortly-clicks"
    LOG = [("sqs:SendMessage", QUEUE), ("dynamodb:GetItem", TABLE), ("dynamodb:UpdateItem", TABLE),
           ("sqs:SendMessage", QUEUE), ("s3:PutObject", "arn:aws:s3:::shortly-assets/uploads/a.png")]

    def test_example(self):
        self.assertEqual(generate_policy([("s3:GetObject", "arn:aws:s3:::b/k")] * 2), {"Version": "2012-10-17", "Statement": [
            {"Effect": "Allow", "Action": ["s3:GetObject"], "Resource": "arn:aws:s3:::b/k"}]})

    def test_shape(self):
        policy = generate_policy(self.LOG)
        self.assertEqual([s["Resource"] for s in policy["Statement"]],
                         sorted({"arn:aws:s3:::shortly-assets/uploads/a.png", self.TABLE, self.QUEUE}))
        table = next(s for s in policy["Statement"] if s["Resource"] == self.TABLE)
        self.assertEqual(table["Action"], ["dynamodb:GetItem", "dynamodb:UpdateItem"])

    def test_allows_exactly_the_log(self):
        policy = generate_policy(self.LOG)
        for action, arn in self.LOG:
            self.assertEqual(ref.evaluate_policies([policy], Request(APP, action, arn)), "Allow")
        for action, arn in [("sqs:SendMessage", self.TABLE), ("dynamodb:GetItem", self.QUEUE), ("dynamodb:DeleteItem", self.TABLE)]:
            with self.subTest(action=action, arn=arn):
                self.assertEqual(ref.evaluate_policies([policy], Request(APP, action, arn)), "ImplicitDeny")

    def test_empty_log(self):
        self.assertEqual(generate_policy([]), {"Version": "2012-10-17", "Statement": []})


# ── Exercise 07: Roles and temporary credentials ─────────────────────
"""
create_app_role(iam, name, policy) -> str
    Create IAM role `name` that EC2 may assume (trust policy: Effect Allow, Principal
    {"Service": "ec2.amazonaws.com"}, Action "sts:AssumeRole"), tagged {"saa-course": "lab"}; add
    `policy` as an inline policy named f"{name}-inline"; create an instance profile with the same name;
    add the role to it; return the instance profile's ARN. (EC2 instances get a role ONLY through an
    instance profile — this is why the app never needs access keys.)
whoami_as(role_arn, session_name) -> str
    Call STS AssumeRole, then make a NEW STS client with the temporary credentials it returned and
    return the "Arn" from get_caller_identity. In AWS it looks like
    arn:aws:sts::ACCOUNT:assumed-role/ROLE_NAME/SESSION_NAME — that is what CloudTrail records.
Hint: boto3.client("sts", aws_access_key_id=…, aws_secret_access_key=…, aws_session_token=…)
"""
def create_app_role(iam, name, policy):
    raise NotImplementedError  # YOUR CODE


def whoami_as(role_arn, session_name):
    raise NotImplementedError  # YOUR CODE


class Ex07(Drill):
    """Roles and temporary credentials"""
    tasks = ("1.1",)
    uses_aws = True
    POLICY = allow("sqs:SendMessage", "arn:aws:sqs:us-east-1:123456789012:shortly-clicks")

    def test_create_app_role(self):
        iam = self.client("iam")
        arn = create_app_role(iam, "shortly-app", self.POLICY)
        self.assertTrue(arn.endswith(":instance-profile/shortly-app"), arn)
        role = iam.get_role(RoleName="shortly-app")["Role"]
        statement = role["AssumeRolePolicyDocument"]["Statement"][0]
        self.assertEqual(statement["Principal"], {"Service": "ec2.amazonaws.com"})
        self.assertIn({"Key": "saa-course", "Value": "lab"}, role.get("Tags", []))
        inline = iam.get_role_policy(RoleName="shortly-app", PolicyName="shortly-app-inline")["PolicyDocument"]
        self.assertEqual(inline, self.POLICY)
        profile = iam.get_instance_profile(InstanceProfileName="shortly-app")["InstanceProfile"]
        self.assertEqual([r["RoleName"] for r in profile["Roles"]], ["shortly-app"])

    def test_whoami_as(self):
        iam = self.client("iam")
        trust = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::123456789012:root"},
                                                         "Action": "sts:AssumeRole"}]}
        role = iam.create_role(RoleName="shortly-ops", AssumeRolePolicyDocument=json.dumps(trust))["Role"]
        self.assertEqual(whoami_as(role["Arn"], "drill-session"),
                         "arn:aws:sts::123456789012:assumed-role/shortly-ops/drill-session")


# ── Exercise 08: A trust policy for a partner (confused deputy) ──────
"""
A partner (account 444455556666) runs a reporting tool that reads your data through a role in YOUR
account. Write TRUST_POLICY (a trust policy document) so that:
  • only the partner's account may call sts:AssumeRole on it,
  • and only when it passes the external ID "shortly-ext-42" — this stops the "confused deputy":
    another customer of the same partner cannot trick the tool into using YOUR role,
  • nobody in your own account and no AWS service can assume it.
Then create_partner_role(iam) creates the role "shortly-partner-read" with TRUST_POLICY and returns its ARN.
Hint: the external ID arrives as the condition key "sts:ExternalId".
"""
import json  # noqa: E402

TRUST_POLICY = None   # YOUR POLICY (a dict)


def create_partner_role(iam):
    raise NotImplementedError  # YOUR CODE


class Ex08(Drill):
    """A trust policy for a partner"""
    tasks = ("1.1",)
    uses_aws = True
    PARTNER_ROLE = f"arn:aws:iam::{PARTNER}:role/reporting-tool"

    def test_partner_with_external_id(self):
        self.assertIsInstance(TRUST_POLICY, dict, "write TRUST_POLICY as a dict")
        self.assertTrue(ref.evaluate_trust(TRUST_POLICY, self.PARTNER_ROLE, {"sts:ExternalId": "shortly-ext-42"}))

    def test_everyone_else_is_refused(self):
        self.assertIsInstance(TRUST_POLICY, dict, "write TRUST_POLICY as a dict")
        cases = [(self.PARTNER_ROLE, {"sts:ExternalId": "guess"}), (self.PARTNER_ROLE, {}),
                 (f"arn:aws:iam::{ACCOUNT}:role/admin", {"sts:ExternalId": "shortly-ext-42"}),
                 ("ec2.amazonaws.com", {"sts:ExternalId": "shortly-ext-42"})]
        for caller, context in cases:
            with self.subTest(caller=caller, context=context):
                self.assertFalse(ref.evaluate_trust(TRUST_POLICY, caller, context))

    def test_create_partner_role(self):
        iam = self.client("iam")
        arn = create_partner_role(iam)
        self.assertEqual(arn, "arn:aws:iam::123456789012:role/shortly-partner-read")
        self.assertEqual(iam.get_role(RoleName="shortly-partner-read")["Role"]["AssumeRolePolicyDocument"], TRUST_POLICY)


# ── Exercise 09: Guardrails and consolidated billing ─────────────────
"""
region_guardrail_scp(allowed_regions) -> dict
    A service control policy that DENIES every action when aws:RequestedRegion is not one of
    allowed_regions — except global services, which you must exempt with NotAction:
    iam:*, organizations:*, sts:*, cloudfront:*, route53:*, support:*, budgets:*.
    (SCPs only take away. Accounts still need FullAWSAccess at every level and their own IAM Allow.)
attach_guardrail(org, target_id, allowed_regions) -> str
    Create the SCP in AWS Organizations (Name "region-guardrail", Type "SERVICE_CONTROL_POLICY",
    Content = json.dumps(...)), attach it to target_id (an OU or account id), return the policy id.
pooled_savings(usage_gb_by_account, tiers) -> float
    Consolidated billing adds usage across all accounts BEFORE applying tiered prices, so the
    organisation reaches cheaper tiers sooner. Return (each account billed alone) − (all accounts
    billed together), rounded to 2 decimal places. Use prices.tiered_cost(quantity, tiers).
"""
def region_guardrail_scp(allowed_regions):
    raise NotImplementedError  # YOUR CODE


def attach_guardrail(org, target_id, allowed_regions):
    raise NotImplementedError  # YOUR CODE


def pooled_savings(usage_gb_by_account, tiers):
    raise NotImplementedError  # YOUR CODE


class Ex09(Drill):
    """Guardrails and consolidated billing"""
    tasks = ("1.1", "4.1")
    uses_aws = True
    ALLOWED = ["us-east-1", "us-west-2"]

    def decide(self, action, region):
        request = Request(APP, action, "*", {"aws:RequestedRegion": region})
        return ref.evaluate(request, identity=[FULL_ACCESS], scps=[[FULL_ACCESS, region_guardrail_scp(self.ALLOWED)]])

    def test_guardrail_decisions(self):
        cases = {("s3:PutObject", "eu-west-1"): "ExplicitDeny", ("ec2:RunInstances", "ap-south-1"): "ExplicitDeny",
                 ("s3:PutObject", "us-east-1"): "Allow", ("ec2:RunInstances", "us-west-2"): "Allow",
                 ("iam:CreateRole", "eu-west-1"): "Allow", ("sts:GetCallerIdentity", "ap-south-1"): "Allow",
                 ("cloudfront:CreateDistribution", "eu-west-1"): "Allow"}
        for (action, region), want in cases.items():
            with self.subTest(action=action, region=region):
                self.assertEqual(self.decide(action, region), want)

    def test_attach_in_organizations(self):
        org = self.client("organizations")
        org.create_organization(FeatureSet="ALL")
        root = org.list_roots()["Roots"][0]["Id"]
        ou = org.create_organizational_unit(ParentId=root, Name="workloads")["OrganizationalUnit"]["Id"]
        policy_id = attach_guardrail(org, ou, self.ALLOWED)
        names = [p["Name"] for p in org.list_policies_for_target(TargetId=ou, Filter="SERVICE_CONTROL_POLICY")["Policies"]]
        self.assertIn("region-guardrail", names)
        content = json.loads(org.describe_policy(PolicyId=policy_id)["Policy"]["Content"])
        self.assertEqual(content, region_guardrail_scp(self.ALLOWED))

    def test_pooled_savings(self):
        tiers = prices.tiers("s3_standard_tiers")
        alone = 2 * prices.tiered_cost(40000, tiers)
        together = prices.tiered_cost(80000, tiers)
        self.assertEqual(pooled_savings({"dev": 40000, "prod": 40000}, tiers), round(alone - together, 2))
        self.assertEqual(pooled_savings({"dev": 100, "prod": 200}, tiers), 0.0)


# ── Exercise 10 (predict): Allow or Deny? ────────────────────────────
"""
Read each scenario, decide, and write "Allow" or "Deny" in PREDICTIONS — BEFORE you run anything.
The test computes the truth with the course's reference evaluator. When you miss one, find which
rule from drills 03–04 you forgot.
"""
BUCKET = "arn:aws:s3:::shortly-assets"
SCENARIOS = {
    1: ("The app's policy allows s3:* on the bucket's objects; a second policy denies s3:DeleteObject. It deletes an object.",
        dict(request=Request(APP, "s3:DeleteObject", BUCKET + "/uploads/a.png"),
             identity=[allow("s3:*", BUCKET + "/*"), deny("s3:DeleteObject")])),
    2: ("The app's policy allows s3:GetObject. The root has FullAWSAccess, but the OU's only SCP allows ec2:*. It reads an object.",
        dict(request=Request(APP, "s3:GetObject", BUCKET + "/uploads/a.png"),
             identity=[allow("s3:GetObject")], scps=[[FULL_ACCESS], [allow("ec2:*")]])),
    3: ("The app has no identity policy at all. The bucket (same account) has a bucket policy allowing the shortly-app role to s3:GetObject. It reads an object.",
        dict(request=Request(APP, "s3:GetObject", BUCKET + "/uploads/a.png"), identity=[], resource_account=ACCOUNT,
             resource_policy={"Statement": [{"Effect": "Allow", "Principal": {"AWS": f"arn:aws:iam::{ACCOUNT}:role/shortly-app"},
                                             "Action": "s3:GetObject", "Resource": BUCKET + "/*"}]})),
    4: ("A role in the partner's account has an identity policy allowing s3:GetObject on your bucket. Your bucket has no bucket policy. It reads an object.",
        dict(request=Request(f"arn:aws:iam::{PARTNER}:role/reporting", "s3:GetObject", BUCKET + "/report.csv"),
             identity=[allow("s3:GetObject", BUCKET + "/*")], resource_account=ACCOUNT)),
    5: ("A developer role's policy allows ec2:* and s3:*. Its permissions boundary allows only s3:*. It launches an instance.",
        dict(request=Request(f"arn:aws:sts::{ACCOUNT}:assumed-role/dev/alice", "ec2:RunInstances", "*"),
             identity=[allow(["ec2:*", "s3:*"])], boundary=allow("s3:*"))),
    6: ("The app's policy allows dynamodb:GetItem on arn:aws:dynamodb:*:*:table/shortly-*. It reads an item from the table shortly-links.",
        dict(request=Request(APP, "dynamodb:GetItem", f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-links"),
             identity=[allow("dynamodb:GetItem", "arn:aws:dynamodb:*:*:table/shortly-*")])),
}
PREDICTIONS = {n: None for n in SCENARIOS}   # YOUR ANSWERS: "Allow" or "Deny"


class Ex10(Drill):
    """Allow or Deny?"""
    tasks = ("1.1",)

    def test_predictions(self):
        for n, (story, kwargs) in SCENARIOS.items():
            with self.subTest(scenario=n):
                truth = "Allow" if ref.evaluate(**kwargs) == "Allow" else "Deny"
                self.assertIn(PREDICTIONS.get(n), ("Allow", "Deny"), f"scenario {n}: write 'Allow' or 'Deny'")
                self.assertEqual(PREDICTIONS[n], truth, f"scenario {n}: {story} — it is {truth}")
```

- [ ] **Step 2: Append to `solutions.py`**

```python
def generate_policy(access_log):
    by_resource = {}
    for action, resource in access_log:
        by_resource.setdefault(resource, set()).add(action)
    return {"Version": "2012-10-17", "Statement": [
        {"Effect": "Allow", "Action": sorted(actions), "Resource": resource}
        for resource, actions in sorted(by_resource.items())]}


EC2_TRUST = {"Version": "2012-10-17", "Statement": [
    {"Effect": "Allow", "Principal": {"Service": "ec2.amazonaws.com"}, "Action": "sts:AssumeRole"}]}


def create_app_role(iam, name, policy):
    iam.create_role(RoleName=name, AssumeRolePolicyDocument=json.dumps(EC2_TRUST),
                    Tags=[{"Key": "saa-course", "Value": "lab"}])
    iam.put_role_policy(RoleName=name, PolicyName=f"{name}-inline", PolicyDocument=json.dumps(policy))
    profile = iam.create_instance_profile(InstanceProfileName=name)["InstanceProfile"]
    iam.add_role_to_instance_profile(InstanceProfileName=name, RoleName=name)
    return profile["Arn"]


def whoami_as(role_arn, session_name):
    creds = boto3.client("sts").assume_role(RoleArn=role_arn, RoleSessionName=session_name)["Credentials"]
    sts = boto3.client("sts", aws_access_key_id=creds["AccessKeyId"], aws_secret_access_key=creds["SecretAccessKey"],
                       aws_session_token=creds["SessionToken"])
    return sts.get_caller_identity()["Arn"]


TRUST_POLICY = {"Version": "2012-10-17", "Statement": [{
    "Effect": "Allow", "Principal": {"AWS": f"arn:aws:iam::{PARTNER}:root"}, "Action": "sts:AssumeRole",
    "Condition": {"StringEquals": {"sts:ExternalId": "shortly-ext-42"}}}]}


def create_partner_role(iam):
    return iam.create_role(RoleName="shortly-partner-read", AssumeRolePolicyDocument=json.dumps(TRUST_POLICY))["Role"]["Arn"]


GLOBAL_SERVICES = ["iam:*", "organizations:*", "sts:*", "cloudfront:*", "route53:*", "support:*", "budgets:*"]


def region_guardrail_scp(allowed_regions):
    return {"Version": "2012-10-17", "Statement": [{
        "Sid": "DenyOutsideAllowedRegions", "Effect": "Deny", "NotAction": GLOBAL_SERVICES, "Resource": "*",
        "Condition": {"StringNotEquals": {"aws:RequestedRegion": list(allowed_regions)}}}]}


def attach_guardrail(org, target_id, allowed_regions):
    policy = org.create_policy(Content=json.dumps(region_guardrail_scp(allowed_regions)), Name="region-guardrail",
                               Description="Deny actions outside the allowed Regions", Type="SERVICE_CONTROL_POLICY")
    policy_id = policy["Policy"]["PolicySummary"]["Id"]
    org.attach_policy(PolicyId=policy_id, TargetId=target_id)
    return policy_id


def pooled_savings(usage_gb_by_account, tiers):
    alone = sum(prices.tiered_cost(gb, tiers) for gb in usage_gb_by_account.values())
    together = prices.tiered_cost(sum(usage_gb_by_account.values()), tiers)
    return round(alone - together, 2)


PREDICTIONS = {1: "Deny", 2: "Deny", 3: "Allow", 4: "Deny", 5: "Deny", 6: "Allow"}
```

- [ ] **Step 3: Append to `MUTANTS` in `_dev/mutants/week01.py`**

```python
MUTANTS += [
    {"id": "one-big-statement", "drill": 6, "code": '''
def generate_policy(access_log):
    if not access_log:
        return {"Version": "2012-10-17", "Statement": []}
    return {"Version": "2012-10-17", "Statement": [{"Effect": "Allow",
        "Action": sorted({a for a, _ in access_log}), "Resource": sorted({r for _, r in access_log})}]}
'''},
    {"id": "base-identity", "drill": 7, "code": '''
import json, boto3
def create_app_role(iam, name, policy):
    trust = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "ec2.amazonaws.com"}, "Action": "sts:AssumeRole"}]}
    iam.create_role(RoleName=name, AssumeRolePolicyDocument=json.dumps(trust), Tags=[{"Key": "saa-course", "Value": "lab"}])
    iam.put_role_policy(RoleName=name, PolicyName=f"{name}-inline", PolicyDocument=json.dumps(policy))
    profile = iam.create_instance_profile(InstanceProfileName=name)["InstanceProfile"]
    iam.add_role_to_instance_profile(InstanceProfileName=name, RoleName=name)
    return profile["Arn"]
def whoami_as(role_arn, session_name):
    boto3.client("sts").assume_role(RoleArn=role_arn, RoleSessionName=session_name)
    return boto3.client("sts").get_caller_identity()["Arn"]
'''},
    {"id": "no-external-id", "drill": 8, "code": '''
import json
TRUST_POLICY = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow",
    "Principal": {"AWS": "arn:aws:iam::444455556666:root"}, "Action": "sts:AssumeRole"}]}
def create_partner_role(iam):
    return iam.create_role(RoleName="shortly-partner-read", AssumeRolePolicyDocument=json.dumps(TRUST_POLICY))["Role"]["Arn"]
'''},
    {"id": "no-global-exemption", "drill": 9, "code": '''
import json
def region_guardrail_scp(allowed_regions):
    return {"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Action": "*", "Resource": "*",
        "Condition": {"StringNotEquals": {"aws:RequestedRegion": list(allowed_regions)}}}]}
def attach_guardrail(org, target_id, allowed_regions):
    pid = org.create_policy(Content=json.dumps(region_guardrail_scp(allowed_regions)), Name="region-guardrail",
                            Description="x", Type="SERVICE_CONTROL_POLICY")["Policy"]["PolicySummary"]["Id"]
    org.attach_policy(PolicyId=pid, TargetId=target_id)
    return pid
def pooled_savings(usage_gb_by_account, tiers):
    alone = sum(prices.tiered_cost(gb, tiers) for gb in usage_gb_by_account.values())
    return round(alone - prices.tiered_cost(sum(usage_gb_by_account.values()), tiers), 2)
'''},
    {"id": "bucket-policy-not-enough", "drill": 10, "code": '''
PREDICTIONS = {1: "Deny", 2: "Deny", 3: "Deny", 4: "Deny", 5: "Deny", 6: "Allow"}
'''},
]
```

- [ ] **Step 4: Verify the week's drills**

```bash
.venv/Scripts/python.exe week_01_iam_and_governance/practice/exercises.py | tail -1
.venv/Scripts/python.exe week_01_iam_and_governance/practice/exercises.py --solutions | tail -1
.venv/Scripts/python.exe verify_course.py --week 1 2>&1 | grep -E "stubs|solutions|mutant|★|tasks|drills"
```

Expected: `0/10 passing`; `10/10 passing (solutions)`; every drill and mutant check ✔.

- [ ] **Step 5: Commit** — skipped (no git).

---

### Task 16: Week 01 concept notes, demos, README and lab

**Files:**
- Create in `week_01_iam_and_governance/`: `concepts/01_iam_identities_and_policies.md`, `concepts/02_policy_evaluation.md`, `concepts/03_roles_sts_and_federation.md`, `concepts/04_multi_account_and_organizations.md`, `concepts/05_least_privilege_and_access_tools.md`, `concepts/demo_policy_decisions.py`, `concepts/demo_iam_enforced.py`, `README.md`, `lab/LAB.md`, `lab/cleanup.py`

**Interfaces:**
- Consumes: `docs/facts.md`, `docs/exam_guide.md` (task 1.1–1.2 bullets), `awslib.policy_eval`, `awsdrill.MOTO_CONFIG` style, `labclean.main`.
- Produces: `ref` targets for Task 17's questions.

**Writing rules:** exactly as Task 12 (first line `Exam tasks:`, the seven sections, 150–300 lines, numbers only from `docs/facts.md`, no answers to drill 10's predictions — use different scenarios in the notes and demos).

- [ ] **Step 1: Write the five notes**

| File | Exam tasks line | Must cover |
|---|---|---|
| `01_iam_identities_and_policies.md` | `Exam tasks: 1.1` | root user (what only root can do; lock it away), IAM users vs groups vs roles; why roles and federation beat long-lived users; policy types: identity-based (AWS managed, customer managed, inline), resource-based (bucket, key, queue, topic policies), permissions boundaries, SCPs/RCPs, session policies, ACLs (legacy, disabled by default on new buckets); policy JSON anatomy (Version, Statement, Sid, Effect, Action/NotAction, Resource/NotResource, Principal, Condition); ARNs (link to week 00 drill 01); a comparison table of policy types (who attaches it, what it can do, grants or only limits) |
| `02_policy_evaluation.md` | `Exam tasks: 1.1` | the evaluation flow as a numbered list matching drills 03–04 (explicit deny → SCPs → resource-based → identity → boundary → session), with a diagram in a fenced text block; implicit vs explicit deny; condition operators, IfExists, ForAnyValue/ForAllValues and the empty-set trap; common keys (`aws:SourceIp`, `aws:SecureTransport`, `aws:MultiFactorAuthPresent`, `aws:RequestedRegion`, `aws:PrincipalOrgID`, `aws:SourceVpce`, `aws:PrincipalTag/…`); cross-account: both sides must allow; the corner the drills ignore (same-account resource policy naming a user is not limited by a boundary); worked examples printed from `demo_policy_decisions.py` (different from drill 10's scenarios) |
| `03_roles_sts_and_federation.md` | `Exam tasks: 1.1, 1.2` | roles = trust policy + permissions; STS AssumeRole, temporary credentials, session duration, `RoleSessionName` and CloudTrail; instance profiles; service roles and `iam:PassRole` (+ `iam:PassedToService`); cross-account roles and the external ID (confused deputy); federation: SAML 2.0, OIDC (web identity, e.g. GitHub Actions to AWS), IAM Identity Center (successor of AWS SSO; permission sets; the recommended workforce sign-in); Cognito pointer (user pools vs identity pools in week 08); Directory Service (AWS Managed Microsoft AD, AD Connector) for "use our Active Directory" scenarios; a comparison table of federation options |
| `04_multi_account_and_organizations.md` | `Exam tasks: 1.1, 4.1` | why many accounts (blast radius, billing, limits); AWS Organizations: management account, OUs, SCPs (deny-list vs allow-list strategy, never affect the management account or service-linked roles, never grant), consolidated billing and pooled volume tiers (link drill 09), Savings Plans/RI sharing; Control Tower: landing zone, account factory, controls (preventive = SCPs, detective = Config rules, proactive = CloudFormation hooks); AWS RAM for sharing resources (subnets, Transit Gateways) across accounts; `aws:PrincipalOrgID` in resource policies; the Free-plan warning from `docs/facts.md` (joining Organizations upgrades a Free-plan account to Paid — practise SCPs offline); comparison table Organizations vs Control Tower vs RAM |
| `05_least_privilege_and_access_tools.md` | `Exam tasks: 1.1, 1.2` | least privilege in practice: start narrow, grow from evidence; IAM Access Analyzer (external-access findings, unused-access findings, policy validation, policy generation from CloudTrail — drill 06); IAM policy simulator; last-accessed information; credential report; MFA (virtual, hardware, passkeys), password policy; permissions-boundary delegation pattern (the deployer in M01); tagging and ABAC (`aws:PrincipalTag` = `aws:ResourceTag`); "least privilege" vs "least operational overhead" in exam wording; comparison table of the access tools |

- [ ] **Step 2: Write `concepts/demo_policy_decisions.py`**

```python
"""Demo — the reference evaluator deciding real-looking requests. Pure Python, no AWS.
Each line: the request, the policies in play, the decision and WHY."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.awslib.policy_eval import Request, evaluate  # noqa: E402
from _harness.awslib.safety import force_utf8  # noqa: E402

force_utf8()
A, B = "111122223333", "999988887777"
ANALYST = f"arn:aws:sts::{A}:assumed-role/analyst/bob"
FULL = {"Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]}
READ_LOGS = {"Statement": [{"Effect": "Allow", "Action": ["s3:GetObject", "s3:ListBucket"],
                            "Resource": ["arn:aws:s3:::acme-logs", "arn:aws:s3:::acme-logs/*"]}]}
ONLY_EU = {"Statement": [{"Effect": "Deny", "NotAction": ["iam:*", "sts:*"], "Resource": "*",
                          "Condition": {"StringNotEquals": {"aws:RequestedRegion": ["eu-west-1", "eu-central-1"]}}}]}
VPC_ONLY = {"Statement": [{"Effect": "Deny", "Principal": "*", "Action": "s3:*", "Resource": ["arn:aws:s3:::acme-logs/*"],
                           "Condition": {"StringNotEquals": {"aws:SourceVpce": "vpce-0abc"}}}]}

cases = [
    ("read a log object, identity policy only", Request(ANALYST, "s3:GetObject", "arn:aws:s3:::acme-logs/2026/10/08.gz"),
     dict(identity=[READ_LOGS]), "the identity policy allows it and nothing denies it"),
    ("delete a log object", Request(ANALYST, "s3:DeleteObject", "arn:aws:s3:::acme-logs/2026/10/08.gz"),
     dict(identity=[READ_LOGS]), "no statement allows DeleteObject → implicit deny"),
    ("read logs from us-east-1 under an EU-only SCP", Request(ANALYST, "s3:GetObject", "arn:aws:s3:::acme-logs/x", {"aws:RequestedRegion": "us-east-1"}),
     dict(identity=[READ_LOGS], scps=[[FULL, ONLY_EU]]), "the SCP's Deny matches (Region not in the list)"),
    ("read logs from outside the VPC endpoint", Request(ANALYST, "s3:GetObject", "arn:aws:s3:::acme-logs/x", {"aws:SourceVpce": "vpce-9zzz"}),
     dict(identity=[READ_LOGS], resource_policy=VPC_ONLY, resource_account=A), "the bucket policy denies requests not coming through vpce-0abc"),
    ("an analyst in another account, with only their own IAM policy", Request(f"arn:aws:iam::{B}:role/analyst", "s3:GetObject", "arn:aws:s3:::acme-logs/x"),
     dict(identity=[READ_LOGS], resource_account=A), "cross-account access needs the bucket policy to allow it too"),
]
for title, request, policies, why in cases:
    print(f"{evaluate(request, **policies):<13} {title}\n{'':14}because {why}")
print("\nNow do drills 03–04 and 10.")
```

- [ ] **Step 3: Write `concepts/demo_iam_enforced.py`**

```python
"""Demo — moto enforcing IAM: a user with a narrow policy is refused everything else.
Shows real AccessDenied errors from (fake) AWS. Offline."""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.awslib.safety import force_utf8, use_fake_aws_env  # noqa: E402

force_utf8()
use_fake_aws_env()
import boto3  # noqa: E402
from botocore.exceptions import ClientError  # noqa: E402
from moto import mock_aws  # noqa: E402
from moto.core import set_initial_no_auth_action_count  # noqa: E402

POLICY = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "s3:ListAllMyBuckets", "Resource": "*"}]}


@set_initial_no_auth_action_count(4)  # the first 4 calls (the setup below) run as admin; the rest are checked
@mock_aws
def main():
    iam = boto3.client("iam")
    iam.create_user(UserName="narrow")
    iam.put_user_policy(UserName="narrow", PolicyName="list-only", PolicyDocument=json.dumps(POLICY))
    key = iam.create_access_key(UserName="narrow")["AccessKey"]
    boto3.client("s3").create_bucket(Bucket="demo-enforced-bucket")
    s3 = boto3.client("s3", aws_access_key_id=key["AccessKeyId"], aws_secret_access_key=key["SecretAccessKey"])
    print("ListBuckets  →", [b["Name"] for b in s3.list_buckets()["Buckets"]])
    for label, call in (("CreateBucket", lambda: s3.create_bucket(Bucket="demo-second-bucket")),
                        ("PutObject   ", lambda: s3.put_object(Bucket="demo-enforced-bucket", Key="k", Body=b"x"))):
        try:
            call()
            print(f"{label} → allowed (unexpected)")
        except ClientError as exc:
            print(f"{label} → {exc.response['Error']['Code']}  (implicit deny: no statement allows it)")


main()
print("\nNow do drills 03 and 05.")
```

If the setup needs a different number of unauthenticated calls than 4 (create_user, put_user_policy, create_access_key, create_bucket), adjust the decorator argument to the exact count — the spike documented that it must match exactly.

- [ ] **Step 4: Write `README.md`**

Same headings as week 00. Goals (6): evaluate any policy set by hand; write least-privilege policies; use roles and temporary credentials everywhere; design cross-account access safely (external ID, both sides allow); choose a federation option; lay out accounts with Organizations, SCPs and Control Tower. Your week (≈ 10–12 h): notes + demos (~3 h) → drills (~3–4 h; 01–04 are the heart of the domain) → quiz `python quiz.py --week 1 -n 30` until ≥ 80 % (~1.5 h) → milestone M01 (~2 h) → optional lab (~1 h). Exam tasks covered: 1.1, 1.2, 4.1 with titles. Service comparison: IAM users vs roles vs Identity Center vs Cognito vs Directory Service (who signs in, credentials, when to use). Interview questions (10), e.g. "Walk through how AWS decides whether a request is allowed.", "Explicit vs implicit deny?", "How does an EC2 instance get credentials?", "How would you give a partner read access to one bucket?", "What is the confused-deputy problem?", "What can an SCP do that an IAM policy cannot, and what can it never do?", "How do permissions boundaries let you delegate role creation safely?", "How would you find and remove unused permissions?", "When would you use IAM Identity Center vs IAM users?", "How does consolidated billing save money?". Final line: "Now you may read `_harness/awslib/policy_eval.py` — compare it with your drills 01–04."

- [ ] **Step 5: Write `lab/LAB.md` and `lab/cleanup.py`**

`LAB.md` (≈ 60 min, 0 USD — IAM is free), sections: 1. Before you start (week 00 lab done; work with the `saa-lab` profile; do NOT create an Organization in a Free-plan account — `docs/facts.md`); 2. A role for EC2 in the console (trust EC2, inline policy allowing `s3:ListAllMyBuckets`, tag `saa-course=lab`; note the instance profile the console creates for you); 3. A role you can assume (trust your own account with MFA required; `aws sts assume-role … --serial-number … --token-code …` then `aws sts get-caller-identity` with the returned credentials — compare with week 00's ARN); 4. The IAM policy simulator (simulate `s3:DeleteObject` vs `s3:GetObject` for your role; add an explicit deny and re-run); 5. IAM Access Analyzer (create an account analyzer — free for external access; make a test bucket policy that allows another account and watch the finding appear; remove it); 6. A customer-managed policy and a user with no console access (both tagged `saa-course=lab`, for the cleanup to find); 7. Clean up: `python lab/cleanup.py --profile saa-lab` then `--yes` (deletes the tagged roles, policies and users; delete the Access Analyzer and any test bucket by hand, or tag the bucket and run week 00's cleanup); 8. What to write down (the assumed-role ARN, the simulator results, the analyzer finding).

`cleanup.py`:

```python
"""Week 01 lab cleanup — deletes only IAM roles, policies and users tagged saa-course=lab. Dry run unless --yes.

    python lab/cleanup.py --profile saa-lab          list what would go
    python lab/cleanup.py --profile saa-lab --yes    delete it
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.labclean import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(kinds=["iam_roles", "iam_users", "iam_policies"]))
```

- [ ] **Step 6: Verify**

```bash
for f in week_01_iam_and_governance/concepts/demo_*.py; do .venv/Scripts/python.exe "$f" | cat; done
.venv/Scripts/python.exe verify_course.py --week 1 2>&1 | grep -E "concept|demo|README|lab"
```

Expected: `demo_policy_decisions.py` prints five decisions (Allow, ImplicitDeny, ExplicitDeny, ExplicitDeny, ImplicitDeny); `demo_iam_enforced.py` prints the bucket list and two `AccessDenied` lines; every concept/demo/README/lab check ✔. The main session spot-checks every number against `docs/facts.md`.

- [ ] **Step 7: Commit** — skipped (no git).

---

### Task 17: Week 01 quiz (30 questions) + blind-solve

**Files:**
- Create: `week_01_iam_and_governance/quiz/questions.toml`

**Interfaces:**
- Consumes: Task 4 schema, Task 13 `_dev/blindsolve.py`, Task 16 notes as `ref` targets, `docs/facts.md`.
- Produces: the week 01 bank.

- [ ] **Step 1: Write the 30 questions** (rules as Task 13 Step 4; 3–6 multi-response; ids `w01-q01 … w01-q30`)

| ids | domain · task | topics (one question each, in order) |
|---|---|---|
| q01–q06 | 1 · 1.1 | explicit deny vs allow · implicit deny by default · NotAction in a deny guard · condition on `aws:SecureTransport` · `aws:SourceIp` restriction with a VPC endpoint caveat · ForAllValues empty-set trap (as a "why does this policy let untagged requests through" question) |
| q07–q11 | 1 · 1.1 | instance profile instead of access keys · AssumeRole temporary credentials for a script · cross-account S3 access needs bucket policy + identity policy · external ID for a third-party vendor · `iam:PassRole` for a service |
| q12–q16 | 1 · 1.1 | IAM Identity Center for a workforce of 200 with existing IdP · SAML federation to on-premises AD · OIDC from a CI system (no long-lived keys) · AWS Managed Microsoft AD vs AD Connector · Cognito identity pool for mobile users reaching S3 (Select TWO: identity pool + IAM role) |
| q17–q22 | 1 · 1.1 | SCP to block Regions (and why it never affects the management account) · SCP cannot grant · OU structure for dev/prod · Control Tower for a new multi-account landing zone (LEAST operational overhead) · RAM to share subnets · `aws:PrincipalOrgID` in a bucket policy |
| q23–q27 | 1 · 1.2 | permissions boundary for delegated role creation · Access Analyzer external-access finding · policy generation from CloudTrail for least privilege · MFA-protected API access for a sensitive action · root user best practice (Select TWO) |
| q28 | 1 · 1.3 | bucket policy denying requests without encryption-in-transit (the access-control angle of data protection) |
| q29 | 4 · 4.1 | consolidated billing pooling S3 tiers across accounts (MOST cost-effective) |
| q30 | 1 · 1.1 | combined scenario: a contractor needs time-limited read access to one bucket from their own account (Select TWO) |

- [ ] **Step 2: Validate**

```bash
.venv/Scripts/python.exe verify_course.py --week 1 2>&1 | grep -i quiz
.venv/Scripts/python.exe verify_course.py --banks 2>&1 | grep -E "near-duplicate|unique"
```

Expected: all quiz checks ✔; no near-duplicates with week 00.

- [ ] **Step 3: Blind-solve (main session)** — exactly as Task 13 Step 6 with `w01` file names. Record the disagreement count and rulings for the pilot report.

- [ ] **Step 4: Commit** — skipped (no git).

---

### Task 18: Capstone setup + M01 spec and tests

**Files:**
- Create: `course_project/README.md`, `course_project/DEPLOY.md`, `course_project/milestones/M01.md`, `course_project/tests/m01/test_m01_1_skeleton.py`, `test_m01_2_app_role.py`, `test_m01_3_consumer_role.py`, `test_m01_4_deployer_role.py`, `test_m01_5_auditor_role.py`, `test_m01_6_policy_checks.py`

**Interfaces:**
- Consumes: the repo fixtures from Task 8 (`repo`, `template`, `lint_errors`, `render`, `role_policies`, `trust_policy`, `evaluator`, `moto_stacks`).
- Produces: the M01 contract the learner's repo must meet — `infra/iam.yaml` with logical ids `AppBoundary` (AWS::IAM::ManagedPolicy, name `${Prefix}-boundary`), `AppRole` (`${Prefix}-app`), `AppInstanceProfile`, `ConsumerRole` (`${Prefix}-click-consumer`), `DeployerRole` (`${Prefix}-deployer`), `AuditorRole` (`${Prefix}-auditor`); parameters `Prefix` (default `shortly`) and `Env` (`lab`/`prod`); `params/lab.json`, `params/prod.json` as `{"Prefix": "shortly", "Env": "<env>"}`.

- [ ] **Step 1: Write the six test files**

`course_project/tests/m01/test_m01_1_skeleton.py`:

```python
"""M01.1 — repo skeleton and the iam stack's parameters."""
import json


def test_layout(repo):
    for rel in ("infra", "params", "README.md", ".gitignore"):
        assert (repo / rel).exists(), f"create {rel}"


def test_gitignore(repo):
    text = (repo / ".gitignore").read_text(encoding="utf-8")
    for entry in (".venv", "__pycache__"):
        assert entry in text, f".gitignore should list {entry}"


def test_params_files(repo):
    for env in ("lab", "prod"):
        path = repo / "params" / f"{env}.json"
        assert path.exists(), f"create params/{env}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data == {"Prefix": "shortly", "Env": env}, f"params/{env}.json should be {{\"Prefix\": \"shortly\", \"Env\": \"{env}\"}}"


def test_iam_parameters_and_lint(template, lint_errors):
    params = template("iam").get("Parameters", {})
    assert params.get("Prefix", {}).get("Default") == "shortly", "Parameter Prefix (String, Default shortly)"
    assert sorted(params.get("Env", {}).get("AllowedValues", [])) == ["lab", "prod"], "Parameter Env with AllowedValues [lab, prod]"
    errors = lint_errors("iam")
    assert errors == [], "cfn-lint errors: " + "; ".join(f"line {e['line']} {e['rule']} {e['message']}" for e in errors)
```

`test_m01_2_app_role.py`:

```python
"""M01.2 — the app's instance role: exactly what shortly needs, nothing more."""
ACCOUNT = "111122223333"
APP = f"arn:aws:sts::{ACCOUNT}:assumed-role/shortly-app/i-0123456789abcdef0"
NEEDS = [
    ("secretsmanager:GetSecretValue", f"arn:aws:secretsmanager:us-east-1:{ACCOUNT}:secret:shortly/db-AbCdEf", {}),
    ("dynamodb:GetItem", f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-clicks-daily", {}),
    ("dynamodb:Query", f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-clicks-daily", {}),
    ("s3:GetObject", f"arn:aws:s3:::shortly-assets-{ACCOUNT}/uploads/logo.png", {}),
    ("s3:PutObject", f"arn:aws:s3:::shortly-assets-{ACCOUNT}/uploads/logo.png", {}),
    ("sqs:SendMessage", f"arn:aws:sqs:us-east-1:{ACCOUNT}:shortly-clicks", {}),
    ("logs:PutLogEvents", f"arn:aws:logs:us-east-1:{ACCOUNT}:log-group:/shortly/app:log-stream:i-0abc", {}),
    ("cloudwatch:PutMetricData", "*", {"cloudwatch:namespace": "Shortly"}),
]


def resource(template, name):
    found = template("iam")["Resources"].get(name)
    assert found is not None, f"infra/iam.yaml needs a resource with logical id {name}"
    return found


def test_role_name(template, render):
    role = resource(template, "AppRole")
    assert role["Type"] == "AWS::IAM::Role"
    assert render(role["Properties"].get("RoleName")) == "shortly-app", "RoleName: !Sub '${Prefix}-app'"


def test_only_ec2_can_assume(trust_policy, evaluator):
    trust = trust_policy("iam", "AppRole")
    assert evaluator.evaluate_trust(trust, "ec2.amazonaws.com"), "EC2 must be able to assume the app role"
    assert not evaluator.evaluate_trust(trust, "lambda.amazonaws.com")
    assert not evaluator.evaluate_trust(trust, f"arn:aws:iam::{ACCOUNT}:root")


def test_instance_profile(template, render):
    profile = resource(template, "AppInstanceProfile")
    assert profile["Type"] == "AWS::IAM::InstanceProfile"
    assert profile["Properties"].get("Roles") == [{"Ref": "AppRole"}], "Roles: [!Ref AppRole]"
    assert render(profile["Properties"].get("InstanceProfileName")) == "shortly-app"


def test_app_can_do_its_job(role_policies, evaluator):
    policies = role_policies("iam", "AppRole")
    for action, arn, context in NEEDS:
        decision = evaluator.evaluate_policies(policies, evaluator.Request(APP, action, arn, context))
        assert decision == "Allow", f"the app must be allowed {action} on {arn} (got {decision})"
```

`test_m01_3_consumer_role.py`:

```python
"""M01.3 — the click consumer's Lambda execution role."""
ACCOUNT = "111122223333"
CONSUMER = f"arn:aws:sts::{ACCOUNT}:assumed-role/shortly-click-consumer/fn"
QUEUE = f"arn:aws:sqs:us-east-1:{ACCOUNT}:shortly-clicks"
TABLE = f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-clicks-daily"
LOGS = f"arn:aws:logs:us-east-1:{ACCOUNT}:log-group:/aws/lambda/shortly-click-consumer:log-stream:x"


def test_role(template, render):
    role = template("iam")["Resources"].get("ConsumerRole")
    assert role and role["Type"] == "AWS::IAM::Role", "add ConsumerRole (AWS::IAM::Role)"
    assert render(role["Properties"].get("RoleName")) == "shortly-click-consumer"


def test_only_lambda_can_assume(trust_policy, evaluator):
    trust = trust_policy("iam", "ConsumerRole")
    assert evaluator.evaluate_trust(trust, "lambda.amazonaws.com")
    assert not evaluator.evaluate_trust(trust, "ec2.amazonaws.com")


def test_consumer_permissions(role_policies, evaluator):
    policies = role_policies("iam", "ConsumerRole")

    def decide(action, arn):
        return evaluator.evaluate_policies(policies, evaluator.Request(CONSUMER, action, arn))
    for action in ("sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"):
        assert decide(action, QUEUE) == "Allow", f"the consumer needs {action} on the clicks queue"
    assert decide("dynamodb:UpdateItem", TABLE) == "Allow", "the consumer writes rollups with UpdateItem"
    assert decide("logs:PutLogEvents", LOGS) == "Allow", "Lambda needs to write its logs"
    assert decide("sqs:SendMessage", QUEUE) != "Allow", "the consumer only reads the queue"
    assert decide("dynamodb:DeleteItem", TABLE) != "Allow"
```

`test_m01_4_deployer_role.py`:

```python
"""M01.4 — a deployer that may create roles only inside the permissions boundary."""
ACCOUNT = "111122223333"
BOUNDARY = f"arn:aws:iam::{ACCOUNT}:policy/shortly-boundary"
DEPLOYER = f"arn:aws:sts::{ACCOUNT}:assumed-role/shortly-deployer/alice"
FULL = {"Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]}


def deployer(role_policies, evaluator):
    policies = role_policies("iam", "DeployerRole")
    return lambda action, arn, **ctx: evaluator.evaluate_policies(policies, evaluator.Request(DEPLOYER, action, arn, ctx))


def test_boundary_policy(template, render):
    res = template("iam")["Resources"].get("AppBoundary")
    assert res and res["Type"] == "AWS::IAM::ManagedPolicy", "add AppBoundary (AWS::IAM::ManagedPolicy)"
    assert render(res["Properties"].get("ManagedPolicyName")) == "shortly-boundary"


def test_app_roles_carry_the_boundary(template):
    for role in ("AppRole", "ConsumerRole"):
        assert template("iam")["Resources"][role]["Properties"].get("PermissionsBoundary") == {"Ref": "AppBoundary"}, \
            f"{role} needs PermissionsBoundary: !Ref AppBoundary"


def test_boundary_blocks_escalation(template, render, evaluator):
    boundary = render(template("iam")["Resources"]["AppBoundary"]["Properties"]["PolicyDocument"])
    escalate = evaluator.Request(DEPLOYER, "iam:CreateUser", "*")
    assert evaluator.evaluate(escalate, identity=[FULL], boundary=boundary) != "Allow", "the boundary must not allow IAM"
    normal = evaluator.Request(DEPLOYER, "s3:GetObject", "arn:aws:s3:::x/y")
    assert evaluator.evaluate(normal, identity=[FULL], boundary=boundary) == "Allow", "the boundary must still allow the app's services"


def test_roles_only_with_the_boundary(role_policies, evaluator):
    decide = deployer(role_policies, evaluator)
    worker = f"arn:aws:iam::{ACCOUNT}:role/shortly-worker"
    assert decide("iam:CreateRole", worker, **{"iam:PermissionsBoundary": BOUNDARY}) == "Allow"
    assert decide("iam:CreateRole", worker) != "Allow", "creating a role WITHOUT the boundary must fail"
    assert decide("iam:CreateRole", worker, **{"iam:PermissionsBoundary": f"arn:aws:iam::{ACCOUNT}:policy/other"}) != "Allow"
    assert decide("iam:CreateRole", f"arn:aws:iam::{ACCOUNT}:role/admin", **{"iam:PermissionsBoundary": BOUNDARY}) != "Allow", \
        "only roles named shortly-*"


def test_boundary_cannot_be_removed(role_policies, evaluator):
    decide = deployer(role_policies, evaluator)
    assert decide("iam:DeleteRolePermissionsBoundary", f"arn:aws:iam::{ACCOUNT}:role/shortly-app") == "ExplicitDeny"
    assert decide("iam:CreatePolicyVersion", BOUNDARY) == "ExplicitDeny", "nobody may rewrite the boundary"


def test_pass_role_only_to_compute(role_policies, evaluator):
    decide = deployer(role_policies, evaluator)
    role = f"arn:aws:iam::{ACCOUNT}:role/shortly-app"
    assert decide("iam:PassRole", role, **{"iam:PassedToService": "ec2.amazonaws.com"}) == "Allow"
    assert decide("iam:PassRole", role, **{"iam:PassedToService": "lambda.amazonaws.com"}) == "Allow"
    assert decide("iam:PassRole", role, **{"iam:PassedToService": "glue.amazonaws.com"}) != "Allow"


def test_own_stacks_only(role_policies, evaluator):
    decide = deployer(role_policies, evaluator)
    assert decide("cloudformation:CreateStack", f"arn:aws:cloudformation:us-east-1:{ACCOUNT}:stack/shortly-network/1a2b") == "Allow"
    assert decide("cloudformation:CreateStack", f"arn:aws:cloudformation:us-east-1:{ACCOUNT}:stack/billing/1a2b") != "Allow"


def test_humans_need_mfa(trust_policy, evaluator):
    trust = trust_policy("iam", "DeployerRole")
    alice = f"arn:aws:iam::{ACCOUNT}:user/alice"
    assert evaluator.evaluate_trust(trust, alice, {"aws:MultiFactorAuthPresent": True})
    assert not evaluator.evaluate_trust(trust, alice, {"aws:MultiFactorAuthPresent": False})
    assert not evaluator.evaluate_trust(trust, "arn:aws:iam::444455556666:user/mallory", {"aws:MultiFactorAuthPresent": True})
```

`test_m01_5_auditor_role.py`:

```python
"""M01.5 — a read-only auditor role, assumable only with MFA, for one hour at a time."""
ACCOUNT = "111122223333"


def test_read_only_managed_policy(template, render):
    props = template("iam")["Resources"].get("AuditorRole", {}).get("Properties", {})
    arns = render(props.get("ManagedPolicyArns", []))
    assert any(a in arns for a in ("arn:aws:iam::aws:policy/ReadOnlyAccess", "arn:aws:iam::aws:policy/SecurityAudit")), \
        "attach the AWS managed ReadOnlyAccess (or SecurityAudit) policy"
    assert not props.get("Policies"), "the auditor gets no inline policies"
    assert render(props.get("RoleName")) == "shortly-auditor"


def test_one_hour_sessions(template):
    props = template("iam")["Resources"]["AuditorRole"]["Properties"]
    assert props.get("MaxSessionDuration") == 3600, "MaxSessionDuration: 3600"


def test_mfa_required(trust_policy, evaluator):
    trust = trust_policy("iam", "AuditorRole")
    bob = f"arn:aws:iam::{ACCOUNT}:user/bob"
    assert evaluator.evaluate_trust(trust, bob, {"aws:MultiFactorAuthPresent": True})
    assert not evaluator.evaluate_trust(trust, bob, {})
    assert not evaluator.evaluate_trust(trust, bob, {"aws:MultiFactorAuthPresent": False})
```

`test_m01_6_policy_checks.py`:

```python
"""M01.6 — the whole IAM layer: no wildcards, ten things the app must never do, and it deploys."""
ACCOUNT = "111122223333"
APP = f"arn:aws:sts::{ACCOUNT}:assumed-role/shortly-app/i-0abc"
ROLES = ("AppRole", "ConsumerRole", "DeployerRole")
STAR_RESOURCE_OK = {"cloudwatch:PutMetricData"}  # PutMetricData has no resource ARN; limit it with a condition
NEVER = [
    ("dynamodb:DeleteTable", f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-clicks-daily", {}),
    ("dynamodb:PutItem", f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-clicks-daily", {}),
    ("s3:DeleteObject", f"arn:aws:s3:::shortly-assets-{ACCOUNT}/uploads/logo.png", {}),
    ("s3:GetObject", f"arn:aws:s3:::shortly-assets-{ACCOUNT}/private/keys.txt", {}),
    ("s3:PutBucketPolicy", f"arn:aws:s3:::shortly-assets-{ACCOUNT}", {}),
    ("sqs:ReceiveMessage", f"arn:aws:sqs:us-east-1:{ACCOUNT}:shortly-clicks", {}),
    ("sqs:DeleteQueue", f"arn:aws:sqs:us-east-1:{ACCOUNT}:shortly-clicks", {}),
    ("secretsmanager:GetSecretValue", f"arn:aws:secretsmanager:us-east-1:{ACCOUNT}:secret:prod/payments-x1Y2z3", {}),
    ("iam:CreateUser", "*", {}),
    ("cloudwatch:PutMetricData", "*", {"cloudwatch:namespace": "AWS/EC2"}),
]


def test_no_full_wildcard_action(role_policies, evaluator):
    for role in ROLES:
        for policy in role_policies("iam", role):
            for st in evaluator.statements(policy):
                assert "*" not in evaluator.as_list(st.get("Action")), f"{role} has Action: '*'"


def test_resource_star_only_for_metrics(role_policies, evaluator):
    for role in ROLES:
        for policy in role_policies("iam", role):
            for st in evaluator.statements(policy):
                if st.get("Effect") == "Allow" and "*" in evaluator.as_list(st.get("Resource")):
                    actions = set(evaluator.as_list(st.get("Action")))
                    assert actions <= STAR_RESOURCE_OK and st.get("Condition"), \
                        f"{role}: Resource '*' is only acceptable for {sorted(STAR_RESOURCE_OK)} with a Condition"


def test_ten_things_the_app_must_never_do(role_policies, evaluator):
    policies = role_policies("iam", "AppRole")
    for action, arn, context in NEVER:
        decision = evaluator.evaluate_policies(policies, evaluator.Request(APP, action, arn, context))
        assert decision != "Allow", f"the app must NOT be allowed {action} on {arn}"


def test_deploys_in_moto(moto_stacks):
    import boto3

    assert moto_stacks("iam") == "CREATE_COMPLETE"
    iam = boto3.client("iam")
    names = {r["RoleName"] for r in iam.list_roles()["Roles"]}
    assert {"shortly-app", "shortly-click-consumer", "shortly-deployer", "shortly-auditor"} <= names
    boundary = iam.get_role(RoleName="shortly-app")["Role"].get("PermissionsBoundary", {})
    assert boundary.get("PermissionsBoundaryArn", "").endswith(":policy/shortly-boundary")
```

- [ ] **Step 2: Write `course_project/milestones/M01.md`**

Sections: `# M01 — IAM baseline for shortly-infra` · **Step 0 — your repo (once)**: `mkdir ~/code/shortly-infra`, `cd` there, `git init`, create `README.md` (one paragraph: what shortly is — the URL shortener from the Flask course — and that this repo holds its AWS infrastructure as CloudFormation), `.gitignore` (`.venv/`, `__pycache__/`, `.pytest_cache/`), then from the course folder `python course_project/tools/start_milestone.py 1 --repo ~/code/shortly-infra`, and run tests with the course venv's python: `cd ~/code/shortly-infra` → `<course>/.venv/Scripts/python.exe run_milestone.py 1` · **What the tests rely on** (the Interfaces list of this task: file names, logical ids, names, parameters) · **M01.1 … M01.6** — one section per step restating what its test file checks, in plain words, with one YAML snippet each for M01.1 (Parameters block) and M01.2 (the trust policy and ONE example statement — not the whole policy) · **Done when**: `run_milestone.py 1` shows 6/6 steps green; commit and push · **Hints (read only when stuck)**: why `PutMetricData` needs `Resource: '*'` + a `cloudwatch:namespace` condition; Secrets Manager's 6-character suffix; `!Sub 'arn:${AWS::Partition}:…'`; the boundary's ARN is `arn:…:policy/${Prefix}-boundary`; tag roles with `project`/`env` so `Env` is used (cfn-lint warns about unused parameters) · **Why this matters in the exam**: delegation with boundaries, MFA on human roles, instance profiles not keys, least privilege.

- [ ] **Step 3: Write `course_project/README.md` and `course_project/DEPLOY.md`**

`README.md`: what the capstone is (the Flask course's shortly, now on AWS: 11 milestones, one layer per week, table M01–M11 copied from spec §4.4 with "built in week NN"); the two places (your repo / this folder); the loop (start_milestone → build → run_milestone → commit); the tools use the course venv; how checks work (cfn-lint, structural tests, the course's policy evaluator, a moto deploy — and that moto skips some resource types, so a green moto deploy is not proof the stack works in AWS); "Claude never deploys; deploying is optional and yours" → DEPLOY.md.

`DEPLOY.md`: optional; needs the week 00 lab done (budgets + billing alarm); the IAM stack (M01) costs nothing; command `aws cloudformation deploy --template-file infra/iam.yaml --stack-name shortly-iam --parameter-overrides Prefix=shortly Env=lab --capabilities CAPABILITY_NAMED_IAM --profile saa-lab`; teardown `aws cloudformation delete-stack --stack-name shortly-iam --profile saa-lab`; a table "what costs money even when idle" with rows filled in by later milestones (NAT gateway from M02, ALB from M03, RDS from M05) — for M01 only the IAM row ("free") is filled; "always delete stacks in reverse order of creation".

- [ ] **Step 4: Run the tests against an empty repo — every step must be red**

```bash
REPO="$SCRATCH/m01-empty"; mkdir -p "$REPO"
.venv/Scripts/python.exe course_project/tools/start_milestone.py 1 --repo "$REPO"
(cd "$REPO" && "$OLDPWD/.venv/Scripts/python.exe" run_milestone.py 1 | tail -9)
```

Expected: `M01: 0/6 steps green`, each step with a readable reason (e.g. `create infra`, `infra/iam.yaml does not exist yet`).

- [ ] **Step 5: Commit** — skipped (no git).

---

### Task 19: M01 reference solution + mutants

**Files:**
- Create: `course_project/solutions/m01/{infra/iam.yaml, params/lab.json, params/prod.json, README.md, .gitignore}`, `_dev/mutants/m01.py`

**Interfaces:**
- Consumes: Task 18 tests.
- Produces: the M01 snapshot that M02 (week 02 plan) starts from.

- [ ] **Step 1: Write `course_project/solutions/m01/infra/iam.yaml`**

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: shortly-infra M01 - IAM baseline (roles for the app, the click consumer, deployments and audits)

Parameters:
  Prefix:
    Type: String
    Default: shortly
    AllowedPattern: '[a-z][a-z0-9-]{1,20}'
  Env:
    Type: String
    AllowedValues: [lab, prod]

Resources:
  AppBoundary:
    Type: AWS::IAM::ManagedPolicy
    Properties:
      ManagedPolicyName: !Sub '${Prefix}-boundary'
      Description: The most any role created by the deployer may ever do
      PolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Sid: AppServicesOnly
            Effect: Allow
            Action: ['s3:*', 'sqs:*', 'dynamodb:*', 'secretsmanager:GetSecretValue', 'logs:*', 'cloudwatch:PutMetricData']
            Resource: '*'

  AppRole:
    Type: AWS::IAM::Role
    Properties:
      Tags:
        - {Key: project, Value: !Ref Prefix}
        - {Key: env, Value: !Ref Env}
      RoleName: !Sub '${Prefix}-app'
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal: {Service: ec2.amazonaws.com}
            Action: sts:AssumeRole
      PermissionsBoundary: !Ref AppBoundary
      Policies:
        - PolicyName: app
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Sid: ReadDbSecret
                Effect: Allow
                Action: secretsmanager:GetSecretValue
                Resource: !Sub 'arn:${AWS::Partition}:secretsmanager:${AWS::Region}:${AWS::AccountId}:secret:${Prefix}/db-*'
              - Sid: ReadClickCounts
                Effect: Allow
                Action: [dynamodb:GetItem, dynamodb:Query]
                Resource: !Sub 'arn:${AWS::Partition}:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${Prefix}-clicks-daily'
              - Sid: Uploads
                Effect: Allow
                Action: [s3:GetObject, s3:PutObject]
                Resource: !Sub 'arn:${AWS::Partition}:s3:::${Prefix}-assets-${AWS::AccountId}/uploads/*'
              - Sid: SendClicks
                Effect: Allow
                Action: sqs:SendMessage
                Resource: !Sub 'arn:${AWS::Partition}:sqs:${AWS::Region}:${AWS::AccountId}:${Prefix}-clicks'
              - Sid: Logs
                Effect: Allow
                Action: [logs:CreateLogStream, logs:PutLogEvents]
                Resource: !Sub 'arn:${AWS::Partition}:logs:${AWS::Region}:${AWS::AccountId}:log-group:/${Prefix}/app:*'
              - Sid: OwnMetricsOnly
                Effect: Allow
                Action: cloudwatch:PutMetricData
                Resource: '*'
                Condition:
                  StringEquals: {'cloudwatch:namespace': Shortly}

  AppInstanceProfile:
    Type: AWS::IAM::InstanceProfile
    Properties:
      InstanceProfileName: !Sub '${Prefix}-app'
      Roles: [!Ref AppRole]

  ConsumerRole:
    Type: AWS::IAM::Role
    Properties:
      Tags:
        - {Key: project, Value: !Ref Prefix}
        - {Key: env, Value: !Ref Env}
      RoleName: !Sub '${Prefix}-click-consumer'
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal: {Service: lambda.amazonaws.com}
            Action: sts:AssumeRole
      PermissionsBoundary: !Ref AppBoundary
      Policies:
        - PolicyName: consumer
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Sid: ReadClickQueue
                Effect: Allow
                Action: [sqs:ReceiveMessage, sqs:DeleteMessage, sqs:GetQueueAttributes]
                Resource: !Sub 'arn:${AWS::Partition}:sqs:${AWS::Region}:${AWS::AccountId}:${Prefix}-clicks'
              - Sid: WriteRollups
                Effect: Allow
                Action: dynamodb:UpdateItem
                Resource: !Sub 'arn:${AWS::Partition}:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${Prefix}-clicks-daily'
              - Sid: Logs
                Effect: Allow
                Action: [logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents]
                Resource: !Sub 'arn:${AWS::Partition}:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/${Prefix}-*'

  DeployerRole:
    Type: AWS::IAM::Role
    Properties:
      Tags:
        - {Key: project, Value: !Ref Prefix}
        - {Key: env, Value: !Ref Env}
      RoleName: !Sub '${Prefix}-deployer'
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal: {AWS: !Sub 'arn:${AWS::Partition}:iam::${AWS::AccountId}:root'}
            Action: sts:AssumeRole
            Condition:
              Bool: {'aws:MultiFactorAuthPresent': 'true'}
      Policies:
        - PolicyName: deployer
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Sid: OwnStacks
                Effect: Allow
                Action: [cloudformation:CreateStack, cloudformation:UpdateStack, cloudformation:DeleteStack, cloudformation:DescribeStacks, cloudformation:CreateChangeSet, cloudformation:ExecuteChangeSet, cloudformation:DescribeChangeSet]
                Resource: !Sub 'arn:${AWS::Partition}:cloudformation:${AWS::Region}:${AWS::AccountId}:stack/${Prefix}-*/*'
              - Sid: RolesOnlyWithTheBoundary
                Effect: Allow
                Action: [iam:CreateRole, iam:PutRolePolicy, iam:AttachRolePolicy, iam:DeleteRolePolicy, iam:DetachRolePolicy]
                Resource: !Sub 'arn:${AWS::Partition}:iam::${AWS::AccountId}:role/${Prefix}-*'
                Condition:
                  StringEquals:
                    'iam:PermissionsBoundary': !Sub 'arn:${AWS::Partition}:iam::${AWS::AccountId}:policy/${Prefix}-boundary'
              - Sid: PassOwnRolesToComputeOnly
                Effect: Allow
                Action: iam:PassRole
                Resource: !Sub 'arn:${AWS::Partition}:iam::${AWS::AccountId}:role/${Prefix}-*'
                Condition:
                  StringEquals:
                    'iam:PassedToService': [ec2.amazonaws.com, lambda.amazonaws.com]
              - Sid: NeverRemoveTheBoundary
                Effect: Deny
                Action: [iam:DeleteRolePermissionsBoundary, iam:PutRolePermissionsBoundary, iam:DeletePolicy, iam:CreatePolicyVersion]
                Resource:
                  - !Sub 'arn:${AWS::Partition}:iam::${AWS::AccountId}:role/*'
                  - !Sub 'arn:${AWS::Partition}:iam::${AWS::AccountId}:policy/${Prefix}-boundary'

  AuditorRole:
    Type: AWS::IAM::Role
    Properties:
      Tags:
        - {Key: project, Value: !Ref Prefix}
        - {Key: env, Value: !Ref Env}
      RoleName: !Sub '${Prefix}-auditor'
      MaxSessionDuration: 3600
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal: {AWS: !Sub 'arn:${AWS::Partition}:iam::${AWS::AccountId}:root'}
            Action: sts:AssumeRole
            Condition:
              Bool: {'aws:MultiFactorAuthPresent': 'true'}
      ManagedPolicyArns:
        - !Sub 'arn:${AWS::Partition}:iam::aws:policy/ReadOnlyAccess'

Outputs:
  AppRoleArn:
    Value: !GetAtt AppRole.Arn
    Export: {Name: !Sub '${Prefix}-app-role-arn'}
  AppInstanceProfileName:
    Value: !Ref AppInstanceProfile
    Export: {Name: !Sub '${Prefix}-app-instance-profile'}
  ConsumerRoleArn:
    Value: !GetAtt ConsumerRole.Arn
    Export: {Name: !Sub '${Prefix}-consumer-role-arn'}
  BoundaryArn:
    Value: !Ref AppBoundary
    Export: {Name: !Sub '${Prefix}-boundary-arn'}
```

(Checked in the spike venv on 2026-10-08: cfn-lint 1.57.2 reports nothing; moto creates the stack with all six resources and the boundary attached.)

- [ ] **Step 2: Write the other snapshot files**

`params/lab.json` → `{"Prefix": "shortly", "Env": "lab"}`; `params/prod.json` → `{"Prefix": "shortly", "Env": "prod"}`; `.gitignore` → `.venv/`, `__pycache__/`, `.pytest_cache/` (one per line); `README.md` → "# shortly-infra", one paragraph (what it is), "## Layers" table with one row (`iam` — roles for the app, consumer, deployer, auditor; M01), "## Check it" (`python run_milestone.py 1` with the course venv), "## Deploy (optional)" pointing at the course's DEPLOY.md.

- [ ] **Step 3: Write `_dev/mutants/m01.py`**

```python
"""Wrong versions of the M01 snapshot — exact text edits applied to a copy of course_project/solutions/m01."""
MUTANTS = [
    {"id": "app-s3-star", "edits": {"infra/iam.yaml": [["Action: [s3:GetObject, s3:PutObject]", "Action: 's3:*'"]]}},
    {"id": "auditor-12-hours", "edits": {"infra/iam.yaml": [["MaxSessionDuration: 3600", "MaxSessionDuration: 43200"]]}},
    {"id": "boundary-key-typo", "edits": {"infra/iam.yaml": [["'iam:PermissionsBoundary': !Sub", "'iam:PermissionBoundary': !Sub"]]}},
    {"id": "metrics-any-namespace", "edits": {"infra/iam.yaml": [["StringEquals: {'cloudwatch:namespace': Shortly}",
                                                                 "StringLike: {'cloudwatch:namespace': '*'}"]]}},
    {"id": "consumer-sends", "edits": {"infra/iam.yaml": [["Action: [sqs:ReceiveMessage, sqs:DeleteMessage, sqs:GetQueueAttributes]",
                                                          "Action: [sqs:SendMessage]"]]}},
    {"id": "no-params", "delete": ["params/prod.json"]},
]
```

- [ ] **Step 4: Verify the milestone**

```bash
.venv/Scripts/python.exe verify_course.py --milestone 1
```

Expected: ✔ `solutions/m01 passes run_milestone.py 1` · ✔ `the starting state fails M01` · ✔ `solutions/m01 templates are cfn-lint clean` · ✔ `_dev/mutants/m01.py has mutants` · ✔ each of the 6 mutants `is caught`.

- [ ] **Step 5: Commit** — skipped (no git).

---

### Task 20: Course docs, full verification, pilot report

**Files:**
- Create: `README.md`, `COURSE_FLOW.md`, `docs/specs/2026-10-08-aws-saa-plan-1-report.md`
- Generated: `COVERAGE.md` (by `verify_course.py --coverage`)

**Interfaces:**
- Consumes: everything above.
- Produces: the pilot the learner tries.

- [ ] **Step 1: Write `README.md` (course root)**

Sections: `# AWS Solutions Architect – Associate (SAA-C03)` · one-paragraph purpose (pass the exam and come out able to design and explain AWS architectures) · **Status**: pilot — weeks 00–01 and milestone M01 are built; weeks 02–11 and the mock exams follow after your feedback · **Set up once**: `python -m venv .venv` → `.venv\Scripts\activate` (Windows) → `python -m pip install -r requirements.txt` → `python _dev/smoke_stack.py`; "if `.venv\Scripts\python.exe` disappears: `python -m venv --upgrade .venv`" · **Safe by design**: every drill, demo and test runs offline against moto with fake credentials; your real AWS account is used only in optional labs, by you · **Your week** (the routine from spec §9) · **Weeks** table (00–12 with topics from spec §4.0; built ones linked) · **Tools**: `python week_NN_*/practice/exercises.py`, `python quiz.py --week N | --review | --stats`, `python exam_prep/mock_exam.py N` (from week 12), `course_project/tools/start_milestone.py`, `lab/cleanup.py` · **Exam facts** (from `docs/facts.md`) and "check the certification page before booking" · **Exam guide vs 2026 AWS** (spec §7 in four sentences) · **For maintainers**: `python verify_course.py`.

- [ ] **Step 2: Write `COURSE_FLOW.md`**

```markdown
# Course flow

One week at a time: concepts → drills → quiz → milestone → (optional) lab → review.

## Week 00 — Foundations & exam technique (no milestone)
- Concepts: `week_00_foundations_and_exam_technique/concepts/01 … 05` and both demos
- Drills: `python week_00_foundations_and_exam_technique/practice/exercises.py` → 10/10
- Quiz: `python quiz.py --week 0 -n 15` → ≥ 80 %
- Lab (optional): `week_00_…/lab/LAB.md` — account safety first

## Week 01 — IAM & multi-account governance
- Concepts: `week_01_iam_and_governance/concepts/01 … 05` and both demos
- Drills: `python week_01_iam_and_governance/practice/exercises.py` → 10/10
- Quiz: `python quiz.py --week 1 -n 30` → ≥ 80 %
- Milestone M01: `course_project/milestones/M01.md`
  - `python course_project/tools/start_milestone.py 1 --repo ~/code/shortly-infra`
  - in your repo: `<course>/.venv/Scripts/python.exe run_milestone.py 1` → 6/6 steps green, then commit
- Lab (optional): `week_01_…/lab/LAB.md`
- From now on, start each session with `python quiz.py --review`

## Weeks 02–12
Built after your pilot feedback. See the README's week table and the design spec.
```

- [ ] **Step 3: Run the full verification**

```bash
.venv/Scripts/python.exe verify_course.py --self-test
.venv/Scripts/python.exe verify_course.py --coverage
```

Expected: `_dev/tests pass`; then every section green — week_00, week_01, milestone M01, question banks, content currency — and `COVERAGE.md` written (not strict: weeks 02–11 are not built). Paste the final `N/N checks passed` line into the report.

- [ ] **Step 4: Learner-eye pass (main session)**

Run, read and judge as the learner would: `python week_00_…/practice/exercises.py` (the ✘ messages make sense on stubs), `python quiz.py --week 0 -n 3` (answer, read feedback), `python week_01_…/concepts/demo_policy_decisions.py`, and `start_milestone.py 1` into a scratch repo + `run_milestone.py 1` (the reasons point at what to do). Fix anything confusing before writing the report.

- [ ] **Step 5: Write `docs/specs/2026-10-08-aws-saa-plan-1-report.md`**

Sections: what was built (file list with counts: notes, demos, drills, questions, tests); what was verified (the commands above with their final lines; drill timings; mutant counts); blind-solve results for weeks 00 and 01 (disagreements and each ruling); deviations from this plan and why; known limits (moto gaps that shaped drills; facts not yet confirmed); what the learner should try first; what is deferred to the week 02 plan. No commits — say so.

- [ ] **Step 6: Stop.** Report to the learner: pilot ready, how to start (`README.md` → week 00), and ask for feedback before any week 02 plan is written.

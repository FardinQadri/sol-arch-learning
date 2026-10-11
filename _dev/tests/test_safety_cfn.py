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

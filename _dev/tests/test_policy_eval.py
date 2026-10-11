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


def test_decide_resource_policy_matches_service_principals():
    from _harness.awslib.policy_eval import decide_resource_policy
    elb = "logdelivery.elasticloadbalancing.amazonaws.com"
    policy = {"Statement": [
        {"Effect": "Allow", "Principal": {"Service": elb}, "Action": "s3:PutObject", "Resource": "arn:aws:s3:::logs/alb/*"},
        {"Effect": "Deny", "Principal": "*", "Action": "s3:*", "Resource": "arn:aws:s3:::logs/*",
         "Condition": {"Bool": {"aws:SecureTransport": "false"}}}]}

    def r(principal=elb, resource="arn:aws:s3:::logs/alb/x", **ctx):
        return Request(principal=principal, action="s3:PutObject", resource=resource, context=ctx)
    assert decide_resource_policy(policy, r()) == "Allow"
    assert decide_resource_policy(policy, r(resource="arn:aws:s3:::logs/other/x")) == "ImplicitDeny"
    assert decide_resource_policy(policy, r(principal=ROLE)) == "ImplicitDeny"
    assert decide_resource_policy(policy, r(**{"aws:SecureTransport": False})) == "ExplicitDeny"
    assert decide_resource_policy({"Statement": []}, r()) == "ImplicitDeny"

"""M04.4 — the logs bucket: SSE-S3, private, tiered by age, and writable only by the load balancer's log delivery."""
import json

import pytest

ACCOUNT = "111122223333"
BUCKET = f"arn:aws:s3:::shortly-logs-{ACCOUNT}"
DELIVERY = "logdelivery.elasticloadbalancing.amazonaws.com"
LOG_KEY = f"alb/AWSLogs/{ACCOUNT}/elasticloadbalancing/us-east-1/2026/10/11/{ACCOUNT}_elasticloadbalancing_us-east-1_app.shortly.1_20261011T0000Z_10.20.8.5_abc.log.gz"
TWO_MB = 2 * 1024 * 1024
HTTPS = {"aws:SecureTransport": "true"}


def logs_bucket(resources, **params):
    res = resources("storage", **params)
    assert res.get("LogsBucket", {}).get("Type") == "AWS::S3::Bucket", "add LogsBucket (AWS::S3::Bucket) to infra/storage.yaml"
    return res["LogsBucket"]["Properties"]


def to_api(rule):
    out = {"Status": rule.get("Status"), "ID": rule.get("Id"),
           "Filter": {"Prefix": rule["Prefix"]} if rule.get("Prefix") else {}}
    if "Transitions" in rule:
        out["Transitions"] = [{"Days": t["TransitionInDays"], "StorageClass": t["StorageClass"]} for t in rule["Transitions"]]
    if "ExpirationInDays" in rule:
        out["Expiration"] = {"Days": rule["ExpirationInDays"]}
    if "AbortIncompleteMultipartUpload" in rule:
        out["AbortIncompleteMultipartUpload"] = dict(rule["AbortIncompleteMultipartUpload"])
    return out


def api_rules(resources, **params):
    found = (logs_bucket(resources, **params).get("LifecycleConfiguration") or {}).get("Rules")
    assert found, "LogsBucket needs LifecycleConfiguration: Rules: [...] with a rule Id alb-logs"
    rules = [to_api(r) for r in found if r.get("Id") == "alb-logs"]
    assert rules, "add a lifecycle rule with Id: alb-logs"
    return rules


def test_name_and_encryption(resources):
    props = logs_bucket(resources)
    assert props.get("BucketName") == f"shortly-logs-{ACCOUNT}", "LogsBucket BucketName: !Sub '${Prefix}-logs-${AWS::AccountId}'"
    rules = (props.get("BucketEncryption") or {}).get("ServerSideEncryptionConfiguration") or []
    algorithm = ((rules[0].get("ServerSideEncryptionByDefault") or {}).get("SSEAlgorithm")) if rules else None
    assert algorithm == "AES256", \
        f"SSEAlgorithm is {algorithm!r}; use AES256 (SSE-S3). Load balancer access logs can only be delivered to a bucket that uses SSE-S3: with aws:kms the delivery fails and no logs arrive"


def test_private_and_owned(resources):
    props = logs_bucket(resources)
    block = props.get("PublicAccessBlockConfiguration") or {}
    for flag in ("BlockPublicAcls", "BlockPublicPolicy", "IgnorePublicAcls", "RestrictPublicBuckets"):
        assert block.get(flag) is True, f"LogsBucket PublicAccessBlockConfiguration: set {flag}: true"
    rules = (props.get("OwnershipControls") or {}).get("Rules") or []
    assert rules and rules[0].get("ObjectOwnership") == "BucketOwnerEnforced", \
        "LogsBucket: OwnershipControls Rules: [{ObjectOwnership: BucketOwnerEnforced}]"


def test_the_rules_are_valid(resources, lifecycle):
    try:
        lifecycle.validate(api_rules(resources))
    except ValueError as exc:
        raise AssertionError(f"the lifecycle rules are not valid: {exc}") from None


@pytest.mark.parametrize("age, expected", [(0, "STANDARD"), (29, "STANDARD"), (30, "STANDARD_IA"), (89, "STANDARD_IA"),
                                           (90, "GLACIER_IR"), (179, "GLACIER_IR"), (180, "DEEP_ARCHIVE")])
def test_logs_move_down_the_waterfall(resources, lifecycle, age, expected):
    rules = api_rules(resources)
    got = lifecycle.current_class(rules, LOG_KEY, age, TWO_MB)
    assert got == expected, (f"a 2 MB log under alb/ that is {age} days old should be {expected}, got {got}. "
                             "Rule alb-logs: Prefix alb/, Transitions STANDARD_IA at 30 days, GLACIER_IR at 90, DEEP_ARCHIVE at 180")


@pytest.mark.parametrize("env, days", [("prod", 730), ("lab", 365)])
def test_logs_expire_by_environment(resources, lifecycle, env, days):
    rules = api_rules(resources, Env=env)
    assert lifecycle.current_class(rules, LOG_KEY, days - 1, TWO_MB) == "DEEP_ARCHIVE", \
        f"Env={env}: a log {days - 1} days old should still be kept (in DEEP_ARCHIVE)"
    assert lifecycle.current_class(rules, LOG_KEY, days, TWO_MB) == "EXPIRED", \
        f"Env={env}: logs must expire after {days} days: ExpirationInDays: !If [IsProd, 730, 365]. Logs kept forever cost money forever"


def test_deep_archive_is_not_left_early(resources):
    for env in ("prod", "lab"):
        found = logs_bucket(resources, Env=env)["LifecycleConfiguration"]["Rules"]
        rule = next((r for r in found if r.get("Id") == "alb-logs"), {})
        deep = next((t["TransitionInDays"] for t in rule.get("Transitions", []) if t["StorageClass"] == "DEEP_ARCHIVE"), None)
        assert deep is not None and rule.get("ExpirationInDays", 0) >= deep + 180, \
            f"Env={env}: Deep Archive bills a 180-day minimum, so expire at least 180 days after the transition (an earlier delete is charged as if the object stayed)"


def test_only_alb_logs_are_covered(resources, lifecycle):
    rules = api_rules(resources)
    for key in ("other/x.log", "AWSLogs/x.log"):
        assert lifecycle.current_class(rules, key, 400, TWO_MB) == "STANDARD", \
            f"{key} is outside the alb/ prefix, so the rule must leave it alone (Prefix: alb/)"


def test_abort_incomplete_uploads(resources):
    rule = api_rules(resources)[0]
    assert rule.get("AbortIncompleteMultipartUpload", {}).get("DaysAfterInitiation", 99) <= 7, \
        "rule alb-logs: add AbortIncompleteMultipartUpload: {DaysAfterInitiation: 7}"


# ── the bucket policy ──────────────────────────────────────────────

def policy(resources):
    res = resources("storage")
    assert res.get("LogsBucketPolicy", {}).get("Type") == "AWS::S3::BucketPolicy", "add LogsBucketPolicy (AWS::S3::BucketPolicy)"
    props = res["LogsBucketPolicy"]["Properties"]
    assert props.get("Bucket") == "LogsBucket", "LogsBucketPolicy Bucket: !Ref LogsBucket"
    return json.loads(json.dumps(props["PolicyDocument"]).replace("LogsBucket.Arn", BUCKET))


def put(evaluator, principal=DELIVERY, key=LOG_KEY, **context):
    return evaluator.Request(principal, "s3:PutObject", f"{BUCKET}/{key}", context)


def test_log_delivery_may_write_its_prefix(resources, evaluator):
    doc = policy(resources)
    decision = evaluator.decide_resource_policy(doc, put(evaluator, **HTTPS))
    assert decision == "Allow", (f"the log delivery service ({DELIVERY}) must be allowed s3:PutObject under alb/AWSLogs/{ACCOUNT}/ (got {decision}). "
                                 "Statement AllowAlbLogDelivery: Principal Service, Action s3:PutObject, Resource '${LogsBucket.Arn}/alb/AWSLogs/${AWS::AccountId}/*'")


def test_log_delivery_is_limited_to_this_account_and_prefix(resources, evaluator):
    doc = policy(resources)
    for key in ("other/x.log", "alb/AWSLogs/999999999999/x.log", "alb/x.log"):
        assert evaluator.decide_resource_policy(doc, put(evaluator, key=key, **HTTPS)) != "Allow", \
            f"log delivery must not be able to write {key}: limit the Resource to alb/AWSLogs/<your account id>/*"


def test_nobody_else_writes_logs(resources, evaluator):
    doc = policy(resources)
    for who in (f"arn:aws:iam::{ACCOUNT}:role/shortly-app", "arn:aws:iam::444455556666:role/x", "anonymous"):
        assert evaluator.decide_resource_policy(doc, put(evaluator, principal=who, **HTTPS)) != "Allow", \
            f"{who} must not be allowed to write to the logs bucket"


def test_http_is_denied(resources, evaluator):
    doc = policy(resources)
    for resource in (BUCKET, f"{BUCKET}/{LOG_KEY}"):
        request = evaluator.Request(DELIVERY, "s3:PutObject", resource, {"aws:SecureTransport": "false"})
        assert evaluator.decide_resource_policy(doc, request) == "ExplicitDeny", \
            "add DenyInsecureTransport to the logs bucket policy too (Resource: the bucket ARN and the bucket ARN/*)"

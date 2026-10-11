"""M04.2 — the assets bucket policy: TLS only, and the app role may read and write only under uploads/."""
import json

ACCOUNT = "111122223333"
BUCKET = f"arn:aws:s3:::shortly-assets-{ACCOUNT}"
APP_ROLE = f"arn:aws:iam::{ACCOUNT}:role/shortly-app"
APP = f"arn:aws:sts::{ACCOUNT}:assumed-role/shortly-app/i-0123456789abcdef0"
OTHER = "arn:aws:iam::444455556666:role/someone-else"
HTTPS = {"aws:SecureTransport": "true"}
HTTP = {"aws:SecureTransport": "false"}


def concrete(document):
    """The rendered policy with the unresolved references swapped for the real ARNs the tests use."""
    text = json.dumps(document)
    for old, new in (("AssetsBucket.Arn", BUCKET), ("import:shortly-app-role-arn", APP_ROLE)):
        text = text.replace(old, new)
    return json.loads(text)


def policy(resources):
    res = resources("storage")
    assert res.get("AssetsBucketPolicy", {}).get("Type") == "AWS::S3::BucketPolicy", "add AssetsBucketPolicy (AWS::S3::BucketPolicy)"
    props = res["AssetsBucketPolicy"]["Properties"]
    assert props.get("Bucket") == "AssetsBucket", "AssetsBucketPolicy Bucket: !Ref AssetsBucket"
    assert props.get("PolicyDocument"), "AssetsBucketPolicy needs a PolicyDocument"
    return concrete(props["PolicyDocument"])


def request(evaluator, action="s3:GetObject", key="uploads/x.png", principal=APP, **context):
    resource = f"{BUCKET}/{key}" if key else BUCKET
    return evaluator.Request(principal, action, resource, context)


def test_app_role_reads_uploads_through_the_bucket_policy(resources, evaluator):
    doc = policy(resources)
    for action in ("s3:GetObject", "s3:PutObject"):
        decision = evaluator.decide_resource_policy(doc, request(evaluator, action, **HTTPS))
        assert decision == "Allow", \
            f"the bucket policy alone must allow the app role {action} on uploads/x.png over HTTPS (got {decision}); add statement AllowAppUploads with Principal AWS: the imported app role ARN"


def test_the_full_evaluation_allows_the_app(resources, evaluator, role_policies):
    doc = policy(resources)
    identity = role_policies("iam", "AppRole")
    decision = evaluator.evaluate(request(evaluator, **HTTPS), identity=identity, resource_policy=doc)
    assert decision == "Allow", f"identity policy plus bucket policy must allow the app to GET uploads/x.png (got {decision})"


def test_plain_http_is_denied_even_for_the_app(resources, evaluator, role_policies):
    doc = policy(resources)
    identity = role_policies("iam", "AppRole")
    decision = evaluator.evaluate(request(evaluator, **HTTP), identity=identity, resource_policy=doc)
    assert decision == "ExplicitDeny", \
        f"over HTTP (aws:SecureTransport false) the answer must be ExplicitDeny, got {decision}. Add a statement DenyInsecureTransport: Effect Deny, Principal '*', Action 's3:*', Condition Bool aws:SecureTransport 'false'"


def test_the_tls_deny_covers_the_bucket_itself(resources, evaluator):
    doc = policy(resources)
    decision = evaluator.decide_resource_policy(doc, request(evaluator, "s3:ListBucket", key=None, **HTTP))
    assert decision == "ExplicitDeny", \
        f"DenyInsecureTransport must list both the bucket ARN and the bucket ARN/* (ListBucket over HTTP gave {decision}); use Resource: [!GetAtt AssetsBucket.Arn, !Sub '${{AssetsBucket.Arn}}/*']"


def test_nobody_else_gets_in(resources, evaluator):
    doc = policy(resources)
    anonymous = evaluator.decide_resource_policy(doc, request(evaluator, principal="anonymous", **HTTPS))
    assert anonymous != "Allow", "an anonymous GET must not be allowed by the bucket policy; the bucket is not public"
    stranger = evaluator.decide_resource_policy(doc, request(evaluator, principal=OTHER, **HTTPS))
    assert stranger != "Allow", "a role from another account must not be allowed; the Principal is only the app role"


def test_the_app_is_limited_to_uploads(resources, evaluator):
    doc = policy(resources)
    for key in ("private/x.png", "x.png"):
        decision = evaluator.decide_resource_policy(doc, request(evaluator, key=key, **HTTPS))
        assert decision != "Allow", \
            f"the bucket policy must not let the app role read {key}: scope AllowAppUploads to '${{AssetsBucket.Arn}}/uploads/*'"
    decision = evaluator.decide_resource_policy(doc, request(evaluator, "s3:DeleteObject", **HTTPS))
    assert decision != "Allow", "the app role may only s3:GetObject and s3:PutObject, not delete"

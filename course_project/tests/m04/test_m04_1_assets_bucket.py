"""M04.1 — the assets bucket: versioned, encrypted, private, owned by the account, and never deleted with the stack."""
TYPE = "AWS::S3::Bucket"
ACCOUNT = "111122223333"


def bucket(resources, name="AssetsBucket", **params):
    res = resources("storage", **params)
    assert res.get(name, {}).get("Type") == TYPE, f"add {name} ({TYPE}) to infra/storage.yaml"
    return res[name]


def test_parameters(template):
    params = template("storage").get("Parameters", {})
    assert params.get("Prefix", {}).get("Default") == "shortly", "Parameter Prefix (String, Default shortly)"
    assert sorted(params.get("Env", {}).get("AllowedValues", [])) == ["lab", "prod"], "Parameter Env with AllowedValues [lab, prod]"


def test_name(resources):
    name = bucket(resources)["Properties"].get("BucketName")
    assert name == f"shortly-assets-{ACCOUNT}", \
        "AssetsBucket BucketName: !Sub '${Prefix}-assets-${AWS::AccountId}' (the app role's policy and the S3 endpoint policy already expect this name; the account id keeps it globally unique)"


def test_versioning_is_on(resources):
    status = (bucket(resources)["Properties"].get("VersioningConfiguration") or {}).get("Status")
    assert status == "Enabled", \
        f"VersioningConfiguration Status is {status!r}; use Enabled. Versioning is what lets you undo an overwrite or a delete (a delete only adds a delete marker)"


def test_default_encryption_is_kms_with_a_bucket_key(resources):
    rules = (bucket(resources)["Properties"].get("BucketEncryption") or {}).get("ServerSideEncryptionConfiguration") or []
    assert rules, "add BucketEncryption: ServerSideEncryptionConfiguration: [{ServerSideEncryptionByDefault: {SSEAlgorithm: aws:kms}, BucketKeyEnabled: true}]"
    rule = rules[0]
    default = rule.get("ServerSideEncryptionByDefault") or {}
    assert default.get("SSEAlgorithm") == "aws:kms", \
        f"SSEAlgorithm is {default.get('SSEAlgorithm')!r}; use aws:kms so every object is encrypted under a KMS key and each use shows in CloudTrail"
    assert rule.get("BucketKeyEnabled") is True, \
        "add BucketKeyEnabled: true next to ServerSideEncryptionByDefault. A Bucket Key makes S3 ask KMS for one short-lived key per bucket instead of one per object, which cuts KMS request charges by up to 99 %"
    assert "KMSMasterKeyID" not in default, \
        "leave KMSMasterKeyID out for now: S3 then uses the AWS managed key aws/s3. Milestone M08 brings your own customer managed key"


def test_block_public_access_all_four(resources):
    block = bucket(resources)["Properties"].get("PublicAccessBlockConfiguration") or {}
    for flag in ("BlockPublicAcls", "BlockPublicPolicy", "IgnorePublicAcls", "RestrictPublicBuckets"):
        assert block.get(flag) is True, f"PublicAccessBlockConfiguration: set {flag}: true (all four flags stay on; user uploads are never public)"


def test_object_ownership_is_enforced(resources):
    rules = (bucket(resources)["Properties"].get("OwnershipControls") or {}).get("Rules") or []
    assert rules and rules[0].get("ObjectOwnership") == "BucketOwnerEnforced", \
        "add OwnershipControls: Rules: [{ObjectOwnership: BucketOwnerEnforced}] — ACLs are switched off and the bucket owner owns every object"


def test_the_bucket_survives_the_stack(template):
    res = template("storage")["Resources"].get("AssetsBucket", {})
    assert res.get("DeletionPolicy") == "Retain", \
        "AssetsBucket: add DeletionPolicy: Retain — deleting the stack must not delete the users' uploads"
    assert res.get("UpdateReplacePolicy") == "Retain", \
        "AssetsBucket: add UpdateReplacePolicy: Retain — a change that replaces the bucket must not delete the old one either"

"""M04.3 — the assets bucket's lifecycle: old versions do not pile up, half-finished uploads are cleaned."""
import pytest


def to_api(rule):
    """One CloudFormation lifecycle rule in the shape the S3 API (and the lifecycle model) uses."""
    out = {"Status": rule.get("Status")}
    if "Id" in rule:
        out["ID"] = rule["Id"]
    parts = {}
    if rule.get("Prefix"):
        parts["Prefix"] = rule["Prefix"]
    if rule.get("TagFilters"):
        parts["Tags"] = [{"Key": t["Key"], "Value": t["Value"]} for t in rule["TagFilters"]]
    for name in ("ObjectSizeGreaterThan", "ObjectSizeLessThan"):
        if name in rule:
            parts[name] = int(rule[name])
    out["Filter"] = parts if len(parts) <= 1 and "Tags" not in parts else {"And": parts}
    if "Transitions" in rule:
        out["Transitions"] = [{"Days": t["TransitionInDays"], "StorageClass": t["StorageClass"]} for t in rule["Transitions"]]
    if "ExpirationInDays" in rule:
        out["Expiration"] = {"Days": rule["ExpirationInDays"]}
    if "NoncurrentVersionExpiration" in rule:
        out["NoncurrentVersionExpiration"] = dict(rule["NoncurrentVersionExpiration"])
    if "NoncurrentVersionTransitions" in rule:
        out["NoncurrentVersionTransitions"] = [{"NoncurrentDays": t["TransitionInDays"], "StorageClass": t["StorageClass"]}
                                                for t in rule["NoncurrentVersionTransitions"]]
    if "AbortIncompleteMultipartUpload" in rule:
        out["AbortIncompleteMultipartUpload"] = dict(rule["AbortIncompleteMultipartUpload"])
    return out


@pytest.fixture
def rules(resources):
    res = resources("storage").get("AssetsBucket")
    assert res, "add AssetsBucket (AWS::S3::Bucket) to infra/storage.yaml"
    found = (res["Properties"].get("LifecycleConfiguration") or {}).get("Rules")
    assert found, "AssetsBucket needs LifecycleConfiguration: Rules: [...] with a rule Id noncurrent-versions"
    return [to_api(r) for r in found]


@pytest.fixture
def rule(rules):
    named = [r for r in rules if r.get("ID") == "noncurrent-versions"]
    assert named, "add a lifecycle rule with Id: noncurrent-versions"
    return named[0]


def test_the_rules_are_valid(rules, lifecycle):
    try:
        lifecycle.validate(rules)
    except ValueError as exc:
        raise AssertionError(f"the lifecycle rules are not valid: {exc}") from None


def test_the_rule_is_enabled(rule):
    assert rule["Status"] == "Enabled", "rule noncurrent-versions: Status: Enabled (a Disabled rule does nothing)"


def test_old_versions_are_expired(rule):
    nexp = rule.get("NoncurrentVersionExpiration")
    assert nexp, ("rule noncurrent-versions needs NoncurrentVersionExpiration: {NoncurrentDays: 30, NewerNoncurrentVersions: 3}. "
                  "With versioning on and no expiry every overwrite is stored (and billed) forever")
    assert 1 <= nexp.get("NoncurrentDays", 0) <= 90, \
        f"NoncurrentDays is {nexp.get('NoncurrentDays')}; keep a replaced version for 1 to 90 days (30 is a good start: enough time to notice a mistake)"
    keep = nexp.get("NewerNoncurrentVersions")
    assert keep is not None, "add NewerNoncurrentVersions: 3 — how many noncurrent versions to keep no matter how old they are"
    assert 1 <= keep <= 5, \
        f"NewerNoncurrentVersions is {keep}; keep between 1 and 5. Each kept version is a full-price copy of the object, so 50 versions of a busy file cost 50 times as much"


def test_what_happens_to_old_versions(rules, lifecycle):
    key = "uploads/logo.png"
    assert lifecycle.noncurrent_fate(rules, key, 31, newer_noncurrent=3) == "DELETED", \
        "a version noncurrent for 31 days with 3 newer noncurrent versions must be deleted"
    assert lifecycle.noncurrent_fate(rules, key, 31, newer_noncurrent=2) != "DELETED", \
        "a version that is one of the 3 newest noncurrent versions must be kept, however old"
    assert lifecycle.noncurrent_fate(rules, key, 10, newer_noncurrent=5) != "DELETED", \
        "a version noncurrent for only 10 days must be kept: NoncurrentDays has not passed"


def test_incomplete_uploads_are_aborted(rules):
    aborting = [r["AbortIncompleteMultipartUpload"]["DaysAfterInitiation"] for r in rules if r.get("AbortIncompleteMultipartUpload")]
    assert aborting, ("add AbortIncompleteMultipartUpload: {DaysAfterInitiation: 7} to the rule. Parts of an unfinished multipart upload "
                      "are invisible in the console and billed until something deletes them")
    assert min(aborting) <= 7, f"DaysAfterInitiation is {min(aborting)}; abort unfinished uploads after 7 days or less"

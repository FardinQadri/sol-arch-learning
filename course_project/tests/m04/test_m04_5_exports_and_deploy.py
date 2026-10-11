"""M04.5 — exports for later stacks, lint-clean, and a deploy in moto (iam + storage) for both environments."""
import re

import pytest

EXPORTS = {"AssetsBucketName": ("shortly-assets-bucket", "AssetsBucket"),
           "AssetsBucketArn": ("shortly-assets-bucket-arn", "AssetsBucket.Arn"),
           "LogsBucketName": ("shortly-logs-bucket", "LogsBucket"),
           "LogsBucketArn": ("shortly-logs-bucket-arn", "LogsBucket.Arn")}


def test_exports(outputs):
    out = outputs("storage")
    for key, (export, value) in EXPORTS.items():
        assert key in out, f"add Output {key}"
        assert out[key].get("Export", {}).get("Name") == export, f"{key}: Export Name !Sub '${{Prefix}}-{export[8:]}'"
        assert str(out[key].get("Value")) == value, f"{key}: Value should render as {value} ({'!GetAtt ' + value if '.' in value else '!Ref ' + value})"


def test_lint_clean(lint_errors):
    errors = lint_errors("storage")
    assert errors == [], "cfn-lint errors: " + "; ".join(f"line {e['line']} {e['rule']} {e['message']}" for e in errors)


@pytest.mark.parametrize("env", ["prod", "lab"])
def test_deploys_in_moto(moto_stacks, env):
    import boto3

    for layer in ("iam", "storage"):
        status = moto_stacks(layer, Env=env)
        assert status == "CREATE_COMPLETE", f"the {layer} stack ended as {status}; fix infra/{layer}.yaml"
    s3 = boto3.client("s3", region_name="us-east-1")
    names = [b["Name"] for b in s3.list_buckets()["Buckets"]]
    assets = [n for n in names if re.fullmatch(r"shortly-assets-\d{12}", n)]
    logs = [n for n in names if re.fullmatch(r"shortly-logs-\d{12}", n)]
    assert len(assets) == 1 and len(logs) == 1, f"expected shortly-assets-<account> and shortly-logs-<account>, found {names}"

    def algorithm(bucket):
        rules = s3.get_bucket_encryption(Bucket=bucket)["ServerSideEncryptionConfiguration"]["Rules"]
        return rules[0]["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"]
    assert algorithm(assets[0]) == "aws:kms", "the assets bucket should encrypt with aws:kms"
    assert algorithm(logs[0]) == "AES256", "the logs bucket should encrypt with AES256 (SSE-S3)"

    cf = boto3.client("cloudformation", region_name="us-east-1")
    outputs = {o["OutputKey"] for o in cf.describe_stacks(StackName="shortly-storage")["Stacks"][0].get("Outputs", [])}
    assert set(EXPORTS) <= outputs, f"the stack is missing Outputs: {sorted(set(EXPORTS) - outputs)}"

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

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

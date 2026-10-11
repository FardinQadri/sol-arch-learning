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

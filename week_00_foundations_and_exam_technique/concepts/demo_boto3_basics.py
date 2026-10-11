"""Demo — boto3 against a fake AWS (moto): identity, Regions, buckets, pagination, error codes.
Run it: python concepts/demo_boto3_basics.py   (offline; nothing here touches a real account)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.awslib.safety import force_utf8, use_fake_aws_env  # noqa: E402

force_utf8()
use_fake_aws_env()

import boto3  # noqa: E402
from botocore.exceptions import ClientError  # noqa: E402
from moto import mock_aws  # noqa: E402

with mock_aws():
    identity = boto3.client("sts").get_caller_identity()
    print(f"Who am I?   account {identity['Account']}   arn {identity['Arn']}")

    regions = sorted(r["RegionName"] for r in boto3.client("ec2", region_name="us-east-1").describe_regions()["Regions"])
    print(f"Regions:    {len(regions)} — first five {regions[:5]}")

    east = boto3.client("s3", region_name="us-east-1")
    east.create_bucket(Bucket="demo-east-bucket")
    west = boto3.client("s3", region_name="eu-west-1")
    west.create_bucket(Bucket="demo-west-bucket", CreateBucketConfiguration={"LocationConstraint": "eu-west-1"})
    for name in ("demo-east-bucket", "demo-west-bucket"):
        location = east.get_bucket_location(Bucket=name)["LocationConstraint"]
        print(f"Bucket {name:<18} LocationConstraint = {location!r}")

    try:
        east.create_bucket(Bucket="demo-x-bucket", CreateBucketConfiguration={"LocationConstraint": "us-east-1"})
    except ClientError as exc:
        print(f"us-east-1 with a LocationConstraint → {exc.response['Error']['Code']}")

    try:
        east.head_bucket(Bucket="demo-missing-bucket")
    except ClientError as exc:
        print(f"head_bucket on a missing bucket → error code {exc.response['Error']['Code']!r}")

    for i in range(120):
        east.put_object(Bucket="demo-east-bucket", Key=f"logs/{i:03d}", Body=b"")
    calls = []
    east.meta.events.register("before-call.s3.ListObjectsV2", lambda **kw: calls.append(1))
    pages = east.get_paginator("list_objects_v2").paginate(Bucket="demo-east-bucket", PaginationConfig={"PageSize": 50})
    total = sum(p.get("KeyCount", 0) for p in pages)
    print(f"Paginated count: {total} objects in {len(calls)} calls of up to 50 keys")
    print("\nNow do drills 05–07 and 10.")

"""Reference solutions for week 00. Read them after you have tried — the point is the struggle."""
import math

import boto3

PARTITIONS = {"aws", "aws-cn", "aws-us-gov"}


def parse_arn(arn):
    parts = arn.split(":", 5)
    if len(parts) != 6 or parts[0] != "arn" or parts[1] not in PARTITIONS:
        raise ValueError(f"not an ARN: {arn!r}")
    _, partition, service, region, account, resource = parts
    resource_type, resource_id = "", resource
    if service != "s3":
        cuts = [i for i in (resource.find("/"), resource.find(":")) if i != -1]
        if cuts:
            cut = min(cuts)
            resource_type, resource_id = resource[:cut], resource[cut + 1:]
    return {"partition": partition, "service": service, "region": region, "account": account,
            "resource_type": resource_type, "resource_id": resource_id}


def _check(a):
    if not 0 < a <= 1:
        raise ValueError(f"availability must be in (0, 1], got {a}")


def series(*availabilities):
    for a in availabilities:
        _check(a)
    return math.prod(availabilities)


def parallel(availability, copies):
    _check(availability)
    if copies < 1:
        raise ValueError("copies must be at least 1")
    return 1 - (1 - availability) ** copies


def downtime_minutes(availability, days=30):
    return (1 - availability) * days * 24 * 60


def per_az_needed(needed, azs):
    if azs < 2:
        raise ValueError("one AZ cannot survive its own failure")
    return math.ceil(needed / (azs - 1))


def survives_az_loss(layout, needed):
    if len(layout) < 2:
        return False
    return sum(layout.values()) - max(layout.values()) >= needed


RESPONSIBILITY = {1: "customer", 2: "aws", 3: "aws", 4: "customer", 5: "customer",
                  6: "aws", 7: "customer", 8: "aws", 9: "customer", 10: "customer"}


def whoami():
    identity = boto3.client("sts").get_caller_identity()
    return {"account": identity["Account"], "arn": identity["Arn"]}


def region_names():
    regions = boto3.client("ec2", region_name="us-east-1").describe_regions()["Regions"]
    return sorted(r["RegionName"] for r in regions)


from botocore.config import Config
from botocore.exceptions import ClientError


def count_objects(s3, bucket, prefix="", page_size=1000):
    pages = s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix,
                                                          PaginationConfig={"PageSize": page_size})
    return sum(page.get("KeyCount", 0) for page in pages)


def bucket_exists(s3, name):
    try:
        s3.head_bucket(Bucket=name)
        return True
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code in ("404", "NoSuchBucket"):
            return False
        if code == "403":
            return True
        raise


def ensure_bucket(s3, name, region):
    if bucket_exists(s3, name):
        return "exists"
    kwargs = {"Bucket": name}
    if region != "us-east-1":
        kwargs["CreateBucketConfiguration"] = {"LocationConstraint": region}
    try:
        s3.create_bucket(**kwargs)
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "BucketAlreadyOwnedByYou":
            return "exists"
        raise
    return "created"


def transfer_cost(flows, price=PRICES):
    total = 0.0
    for source, destination, gb in flows:
        if source == "internet" and destination == "internet":
            raise ValueError("a flow must start or end in AWS")
        if source == "internet":
            continue
        if destination == "internet":
            total += gb * price["egress_internet_per_gb"]
        elif source == destination:
            continue
        elif source[:-1] == destination[:-1]:
            total += gb * price["inter_az_per_gb_each_way"] * 2
        else:
            total += gb * price["inter_region_per_gb"]
    return round(total, 4)


def make_client(service, region, total_attempts=5, connect_timeout=3, read_timeout=10):
    config = Config(retries={"total_max_attempts": total_attempts, "mode": "adaptive"},
                    connect_timeout=connect_timeout, read_timeout=read_timeout)
    return boto3.client(service, region_name=region, config=config)


def inventory(regions):
    report = {}
    for region in regions:
        s3 = boto3.client("s3", region_name=region)
        buckets = [b["Name"] for b in s3.list_buckets()["Buckets"]
                   if (s3.get_bucket_location(Bucket=b["Name"])["LocationConstraint"] or "us-east-1") == region]
        ec2 = boto3.client("ec2", region_name=region)
        instances = sum(len(r["Instances"]) for r in ec2.describe_instances()["Reservations"])
        queues = boto3.client("sqs", region_name=region).list_queues().get("QueueUrls", [])
        report[region] = {"buckets": sorted(buckets), "instances": instances, "queues": len(queues)}
    return report

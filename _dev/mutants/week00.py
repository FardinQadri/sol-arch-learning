"""Deliberately wrong implementations for week 00 — verify_course.py checks that the drills catch each one."""
MUTANTS = [
    {"id": "slash-only", "drill": 1, "code": '''
def parse_arn(arn):
    parts = arn.split(":", 5)
    if len(parts) != 6 or parts[0] != "arn" or parts[1] not in {"aws", "aws-cn", "aws-us-gov"}:
        raise ValueError(arn)
    _, partition, service, region, account, resource = parts
    resource_type, _, resource_id = resource.partition("/") if "/" in resource else ("", "", resource)
    return {"partition": partition, "service": service, "region": region, "account": account,
            "resource_type": resource_type, "resource_id": resource_id}
'''},
    {"id": "parallel-multiplies", "drill": 2, "code": '''
import math
def series(*availabilities):
    return math.prod(availabilities)
def parallel(availability, copies):
    return availability ** copies
def downtime_minutes(availability, days=30):
    return (1 - availability) * days * 24 * 60
'''},
    {"id": "divide-by-all-azs", "drill": 3, "code": '''
import math
def per_az_needed(needed, azs):
    if azs < 2:
        raise ValueError("one AZ")
    return math.ceil(needed / azs)
def survives_az_loss(layout, needed):
    return sum(layout.values()) >= needed
'''},
    {"id": "rds-engine-is-yours", "drill": 4, "code": '''
RESPONSIBILITY = {1: "customer", 2: "customer", 3: "aws", 4: "customer", 5: "customer",
                  6: "aws", 7: "customer", 8: "aws", 9: "customer", 10: "customer"}
'''},
    {"id": "wrong-keys", "drill": 5, "code": '''
import boto3
def whoami():
    return boto3.client("sts").get_caller_identity()
def region_names():
    return [r["RegionName"] for r in boto3.client("ec2", region_name="us-east-1").describe_regions()["Regions"]][:10]
'''},
]

MUTANTS += [
    {"id": "one-call", "drill": 6, "code": '''
def count_objects(s3, bucket, prefix="", page_size=1000):
    return s3.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=page_size).get("KeyCount", 0)
'''},
    {"id": "always-location", "drill": 7, "code": '''
def bucket_exists(s3, name):
    try:
        s3.head_bucket(Bucket=name)
        return True
    except ClientError as exc:
        if exc.response["Error"]["Code"] in ("404", "NoSuchBucket"):
            return False
        if exc.response["Error"]["Code"] == "403":
            return True
        raise
def ensure_bucket(s3, name, region):
    if bucket_exists(s3, name):
        return "exists"
    s3.create_bucket(Bucket=name, CreateBucketConfiguration={"LocationConstraint": region})
    return "created"
'''},
    {"id": "inter-az-once", "drill": 8, "code": '''
def transfer_cost(flows, price=PRICES):
    total = 0.0
    for source, destination, gb in flows:
        if source == "internet" and destination == "internet":
            raise ValueError("x")
        if source == "internet" or source == destination:
            continue
        if destination == "internet":
            total += gb * price["egress_internet_per_gb"]
        elif source[:-1] == destination[:-1]:
            total += gb * price["inter_az_per_gb_each_way"]
        else:
            total += gb * price["inter_region_per_gb"]
    return round(total, 4)
'''},
    {"id": "standard-mode", "drill": 9, "code": '''
import boto3
from botocore.config import Config
def make_client(service, region, total_attempts=5, connect_timeout=3, read_timeout=10):
    return boto3.client(service, region_name=region, config=Config(
        retries={"max_attempts": total_attempts, "mode": "standard"},
        connect_timeout=connect_timeout, read_timeout=read_timeout))
'''},
    {"id": "ignore-location", "drill": 10, "code": '''
import boto3
def inventory(regions):
    report = {}
    for region in regions:
        buckets = [b["Name"] for b in boto3.client("s3", region_name=region).list_buckets()["Buckets"]]
        ec2 = boto3.client("ec2", region_name=region)
        instances = sum(len(r["Instances"]) for r in ec2.describe_instances()["Reservations"])
        queues = boto3.client("sqs", region_name=region).list_queues().get("QueueUrls", [])
        report[region] = {"buckets": sorted(buckets), "instances": instances, "queues": len(queues)}
    return report
'''},
]

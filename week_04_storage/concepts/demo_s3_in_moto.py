"""Demo — S3 versioning, delete markers, default encryption and a lifecycle configuration with boto3 against a fake AWS (moto):
a versioned bucket whose default encryption is SSE-KMS with a Bucket Key, two versions of one object, a delete, the version
list, a restore by removing the delete marker, an archive-class read, and a stored lifecycle configuration.
Run it: python concepts/demo_s3_in_moto.py   (offline; nothing here touches a real account)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.awslib.safety import force_utf8, use_fake_aws_env  # noqa: E402

force_utf8()
use_fake_aws_env()

import boto3  # noqa: E402
from botocore.exceptions import ClientError  # noqa: E402
from moto import mock_aws  # noqa: E402

REGION = "us-east-1"
BUCKET = "saa-demo-reports-123456789012"
KEY = "reports/2026/q3.txt"


def error_code(call):
    """Run a boto3 call that should fail and return the error code."""
    try:
        call()
    except ClientError as err:
        return err.response["Error"]["Code"]
    return "(no error)"


with mock_aws():
    s3 = boto3.client("s3", region_name=REGION)
    kms = boto3.client("kms", region_name=REGION)

    # 1. A bucket with versioning on and SSE-KMS (with a Bucket Key) as the default encryption.
    key_arn = kms.create_key(Description="demo key")["KeyMetadata"]["Arn"]
    s3.create_bucket(Bucket=BUCKET)
    s3.put_bucket_versioning(Bucket=BUCKET, VersioningConfiguration={"Status": "Enabled"})
    s3.put_bucket_encryption(Bucket=BUCKET, ServerSideEncryptionConfiguration={"Rules": [{
        "ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "aws:kms", "KMSMasterKeyID": key_arn},
        "BucketKeyEnabled": True}]})
    rule = s3.get_bucket_encryption(Bucket=BUCKET)["ServerSideEncryptionConfiguration"]["Rules"][0]
    print(f"Bucket {BUCKET}")
    print(f"  versioning        : {s3.get_bucket_versioning(Bucket=BUCKET)['Status']}")
    print(f"  default encryption: {rule['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']}, Bucket Key {rule['BucketKeyEnabled']}")
    print("  (a real new bucket starts with SSE-S3 as the default; moto starts with none, so we set our own)")

    # 2. Two versions of one key, then a plain delete.
    v1 = s3.put_object(Bucket=BUCKET, Key=KEY, Body=b"draft one")["VersionId"]
    v2 = s3.put_object(Bucket=BUCKET, Key=KEY, Body=b"draft two, final")["VersionId"]
    head = s3.head_object(Bucket=BUCKET, Key=KEY)
    print(f"\nPut the key twice. Each put returned its own version id: v1 {v1[:8]}…  v2 {v2[:8]}…")
    print(f"  new objects inherit the bucket default: {head['ServerSideEncryption']}, Bucket Key {head['BucketKeyEnabled']}")

    deleted = s3.delete_object(Bucket=BUCKET, Key=KEY)
    marker_id = deleted["VersionId"]
    print(f"\nPlain DELETE (no version id): DeleteMarker={deleted['DeleteMarker']}, new marker id {marker_id[:8]}…")
    print(f"  GET without a version id  -> {error_code(lambda: s3.get_object(Bucket=BUCKET, Key=KEY))}")
    print(f"  list_objects_v2 key count -> {s3.list_objects_v2(Bucket=BUCKET)['KeyCount']}   (a current-version list hides the key)")

    # 3. The version list still shows everything.
    listing = s3.list_object_versions(Bucket=BUCKET, Prefix=KEY)
    print("\nlist_object_versions shows what the plain list hides:")
    for v in listing["Versions"]:
        print(f"  version       {v['VersionId'][:8]}…  IsLatest={v['IsLatest']!s:<5}  size {v['Size']} bytes")
    for m in listing["DeleteMarkers"]:
        print(f"  delete marker {m['VersionId'][:8]}…  IsLatest={m['IsLatest']!s:<5}  (no data, no size)")

    # 4. Old versions are still readable by id.
    old = s3.get_object(Bucket=BUCKET, Key=KEY, VersionId=v1)["Body"].read().decode()
    print(f"\nGET with the id of v1 -> {old!r}")

    # 5. Remove the delete marker (a DELETE that names the marker's version id) and the object is back.
    s3.delete_object(Bucket=BUCKET, Key=KEY, VersionId=marker_id)
    print(f"\nDeleted the delete marker. GET now returns: {s3.get_object(Bucket=BUCKET, Key=KEY)['Body'].read().decode()!r}")
    after = s3.list_object_versions(Bucket=BUCKET, Prefix=KEY)
    print(f"  versions {len(after['Versions'])}, delete markers {len(after.get('DeleteMarkers', []))}")

    # 6. A storage class is metadata on the object. Flexible Retrieval objects cannot be read until restored.
    s3.put_object(Bucket=BUCKET, Key="archive/old.csv", Body=b"a,b\n1,2\n", StorageClass="GLACIER")
    s3.put_object(Bucket=BUCKET, Key="archive/instant.csv", Body=b"a,b\n3,4\n", StorageClass="GLACIER_IR")
    print(f"\nGET a GLACIER object (Flexible Retrieval)     -> {error_code(lambda: s3.get_object(Bucket=BUCKET, Key='archive/old.csv'))}")
    print(f"GET a GLACIER_IR object (Instant Retrieval) -> {s3.get_object(Bucket=BUCKET, Key='archive/instant.csv')['Body'].read()!r}")

    # 7. A lifecycle configuration: stored and read back. Nothing runs it.
    s3.put_bucket_lifecycle_configuration(Bucket=BUCKET, LifecycleConfiguration={"Rules": [{
        "ID": "logs-tiering", "Status": "Enabled", "Filter": {"Prefix": "logs/"},
        "Transitions": [{"Days": 30, "StorageClass": "STANDARD_IA"}, {"Days": 120, "StorageClass": "GLACIER"}],
        "Expiration": {"Days": 365},
        "NoncurrentVersionExpiration": {"NoncurrentDays": 30},
        "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7}}]})
    stored = s3.get_bucket_lifecycle_configuration(Bucket=BUCKET)["Rules"][0]
    print("\nLifecycle configuration read back:")
    print(f"  rule {stored['ID']!r} on prefix {stored['Filter']['Prefix']!r}")
    print("  transitions :", ", ".join(f"day {t['Days']} -> {t['StorageClass']}" for t in stored["Transitions"]))
    print(f"  expire current versions at day {stored['Expiration']['Days']}; delete noncurrent versions after "
          f"{stored['NoncurrentVersionExpiration']['NoncurrentDays']} days; abort multipart uploads after "
          f"{stored['AbortIncompleteMultipartUpload']['DaysAfterInitiation']} days")

    print("\nWhat moto does NOT do:")
    print("  - Lifecycle never runs. The rule above is stored, but no object ever moves or expires.")
    print("  - Replication never copies. You can store a configuration; the destination bucket stays empty.")
    print("  - Bucket-policy Conditions are ignored. A Deny with aws:SecureTransport blocks every request, even yours.")
    print("  - Block Public Access and Object Ownership settings are stored but never enforced.")
    print("  - CloudFormation drops most S3 bucket settings: versioning, lifecycle, Block Public Access, Object Lock, replication.")
    print("  That is why drills 01-04 are models: you build the lifecycle, cost and size rules yourself.")

print("\nNow do drills 05–09.")

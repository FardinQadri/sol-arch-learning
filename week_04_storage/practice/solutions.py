"""Reference solutions for week 04.

Drills 01–04: the course's reference models ARE the solution — read _harness/awslib/s3cost.py, lifecycle.py and ebs.py
and compare them with yours.
"""
from _harness.awslib.ebs import choose_volume, gp2_iops, gp3_config, monthly_cost  # noqa: F401
from _harness.awslib.lifecycle import current_class, noncurrent_fate, validate  # noqa: F401
from _harness.awslib.s3cost import cheapest_class, plan_parts, prefixes_needed, storage_cost  # noqa: F401


def secure_bucket(s3, name, kms_key_id):
    if not kms_key_id:
        raise ValueError("SSE-KMS needs a KMS key")
    s3.create_bucket(Bucket=name)
    s3.put_bucket_versioning(Bucket=name, VersioningConfiguration={"Status": "Enabled"})
    s3.put_bucket_encryption(Bucket=name, ServerSideEncryptionConfiguration={"Rules": [{
        "ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "aws:kms", "KMSMasterKeyID": kms_key_id},
        "BucketKeyEnabled": True}]})
    s3.put_public_access_block(Bucket=name, PublicAccessBlockConfiguration={
        "BlockPublicAcls": True, "IgnorePublicAcls": True, "BlockPublicPolicy": True, "RestrictPublicBuckets": True})
    s3.put_bucket_ownership_controls(Bucket=name, OwnershipControls={"Rules": [{"ObjectOwnership": "BucketOwnerEnforced"}]})


def tls_only_policy(bucket):
    return {"Version": "2012-10-17", "Statement": [{
        "Sid": "DenyInsecureTransport", "Effect": "Deny", "Principal": "*", "Action": "s3:*",
        "Resource": [f"arn:aws:s3:::{bucket}", f"arn:aws:s3:::{bucket}/*"],
        "Condition": {"Bool": {"aws:SecureTransport": "false"}}}]}


def upload_in_parts(s3, bucket, key, data, part_mib):
    if not data or not 5 <= part_mib <= 5120:
        raise ValueError("need data and a part size of 5 MiB to 5 GiB")
    size = part_mib * MIB
    upload = s3.create_multipart_upload(Bucket=bucket, Key=key)["UploadId"]
    try:
        parts = []
        for number, start in enumerate(range(0, len(data), size), start=1):
            etag = s3.upload_part(Bucket=bucket, Key=key, UploadId=upload, PartNumber=number, Body=data[start:start + size])["ETag"]
            parts.append({"PartNumber": number, "ETag": etag})
        s3.complete_multipart_upload(Bucket=bucket, Key=key, UploadId=upload, MultipartUpload={"Parts": parts})
    except Exception:
        s3.abort_multipart_upload(Bucket=bucket, Key=key, UploadId=upload)
        raise


def share_link(s3, bucket, key, seconds):
    if not 1 <= seconds <= 604_800:
        raise ValueError("a presigned URL lives 1 second to 7 days")
    return s3.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=seconds)


PREDICTIONS = {1: "NoSuchKey", 2: "first", 3: 0, 4: "1 markers, 1 versions", 5: "second", 6: "NoSuchKey",
               7: "0 markers, 2 versions", 8: "first"}

ASSETS_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {"Sid": "ReadViaOurDistribution", "Effect": "Allow", "Principal": {"Service": "cloudfront.amazonaws.com"},
         "Action": "s3:GetObject", "Resource": f"{BUCKET_ARN}/*",
         "Condition": {"StringEquals": {"AWS:SourceArn": DISTRIBUTION_ARN}}},
        {"Sid": "AppUploads", "Effect": "Allow", "Principal": {"AWS": APP_ROLE_ARN},
         "Action": "s3:PutObject", "Resource": f"{BUCKET_ARN}/uploads/*"},
    ],
}


def make_replicated_pair(s3, source, destination, role_arn):
    if source == destination:
        raise ValueError("source and destination must differ")
    for name in (source, destination):
        s3.create_bucket(Bucket=name)
        s3.put_bucket_versioning(Bucket=name, VersioningConfiguration={"Status": "Enabled"})
    s3.put_bucket_replication(Bucket=source, ReplicationConfiguration={
        "Role": role_arn,
        "Rules": [{"ID": "all", "Status": "Enabled", "Priority": 1, "Filter": {"Prefix": ""},
                   "DeleteMarkerReplication": {"Status": "Enabled"},
                   "Destination": {"Bucket": f"arn:aws:s3:::{destination}"}}],
    })


CHOICES = {1: "efs", 2: "instance store", 3: "fsx for windows", 4: "fsx for lustre", 5: "ebs", 6: "storage gateway",
           7: "s3", 8: "fsx for ontap"}

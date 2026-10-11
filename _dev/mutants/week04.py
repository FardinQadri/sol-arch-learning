"""Deliberately wrong implementations for week 04 — each must be caught by its drill."""
MUTANTS = [
    {"id": "early-delete-is-free", "drill": 1, "code": '''
def storage_cost(storage_class, objects, object_kb, days, retrieved_gb=0.0, *, retrieval="standard", price=PRICES):
    if storage_class not in CLASSES or min(objects, object_kb, days, retrieved_gb) < 0 or retrieval not in ("standard", "bulk"):
        raise ValueError(storage_class)
    if storage_class == "STANDARD":
        rate = 0.0
    elif storage_class in RETRIEVAL_KEY:
        rate = price[RETRIEVAL_KEY[storage_class]]
    else:
        rate = price[ARCHIVE_RETRIEVAL_KEY[(storage_class, retrieval)]]
    billable_gb = objects * max(object_kb, MIN_OBJECT_KB[storage_class]) / 1_048_576
    return round(billable_gb * price[RATE_KEY[storage_class]] * days / 30 + retrieved_gb * rate, 2)
'''},
    {"id": "small-objects-move", "drill": 2, "code": '''
from _harness.awslib import lifecycle as _ref
def current_class(rules, key, age_days, size_bytes, tags=None):
    return _ref.current_class(rules, key, age_days, 1 << 30, tags)
'''},
    {"id": "gp3-charges-the-baseline", "drill": 3, "code": '''
from _harness.awslib import ebs as _ref
def monthly_cost(volume_type, size_gib, iops=None, throughput=None, price=PRICES):
    if volume_type == "gp3":
        cfg = _ref.gp3_config(size_gib, iops, throughput)
        return round(size_gib * price["ebs_gp3_per_gb_month"] + cfg["iops"] * price["ebs_gp3_per_iops_month"]
                     + (cfg["throughput"] - 125) * price["ebs_gp3_per_mibps_month"], 2)
    return _ref.monthly_cost(volume_type, size_gib, iops, throughput, price)
'''},
    {"id": "ten-thousand-and-one-parts", "drill": 4, "code": '''
def plan_parts(object_bytes, part_mib=None):
    if object_bytes <= 0 or object_bytes > MAX_OBJECT_BYTES:
        raise ValueError("object size")
    if part_mib is None:
        part_mib = max(5, math.ceil(object_bytes / (10_000 * MIB)))
    if not 5 <= part_mib <= 5120:
        raise ValueError("part size")
    part_bytes = part_mib * MIB
    parts = math.ceil(object_bytes / part_bytes)
    if parts > 10_001:
        raise ValueError("too many parts")
    return {"part_bytes": part_bytes, "parts": parts, "last_part_bytes": object_bytes - (parts - 1) * part_bytes,
            "multipart": object_bytes > 5 * GIB or object_bytes > 100 * MIB}
'''},
    {"id": "deny-objects-only", "drill": 5, "code": '''
def tls_only_policy(bucket):
    return {"Version": "2012-10-17", "Statement": [{
        "Sid": "DenyInsecureTransport", "Effect": "Deny", "Principal": "*", "Action": "s3:*",
        "Resource": f"arn:aws:s3:::{bucket}/*",
        "Condition": {"Bool": {"aws:SecureTransport": "false"}}}]}
'''},
    {"id": "expiry-not-checked", "drill": 6, "code": '''
def share_link(s3, bucket, key, seconds):
    return s3.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=seconds)
'''},
    {"id": "opposite-predictions", "drill": 7, "code": '''
PREDICTIONS = {1: "AccessDenied", 2: "second", 3: 1, 4: "0 markers, 1 versions", 5: "first", 6: "AccessDenied",
               7: "1 markers, 2 versions", 8: "second"}
'''},
    {"id": "public-read-kept", "drill": 8, "code": '''
ASSETS_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {"Sid": "ReadAssets", "Effect": "Allow", "Principal": "*", "Action": "s3:GetObject", "Resource": f"{BUCKET_ARN}/*"},
        {"Sid": "AppUploads", "Effect": "Allow", "Principal": {"AWS": APP_ROLE_ARN},
         "Action": "s3:PutObject", "Resource": f"{BUCKET_ARN}/uploads/*"},
    ],
}
'''},
    {"id": "source-only-versioning", "drill": 9, "code": '''
def make_replicated_pair(s3, source, destination, role_arn):
    if source == destination:
        raise ValueError("source and destination must differ")
    for name in (source, destination):
        s3.create_bucket(Bucket=name)
    s3.put_bucket_versioning(Bucket=source, VersioningConfiguration={"Status": "Enabled"})
    s3.put_bucket_replication(Bucket=source, ReplicationConfiguration={
        "Role": role_arn,
        "Rules": [{"ID": "all", "Status": "Enabled", "Priority": 1, "Filter": {"Prefix": ""},
                   "DeleteMarkerReplication": {"Status": "Enabled"},
                   "Destination": {"Bucket": f"arn:aws:s3:::{destination}"}}],
    })
'''},
    {"id": "no-answers", "drill": 10, "code": '''
CHOICES = {n: None for n in range(1, 9)}
'''},
]

# Week 04 feasibility spike: S3, EBS, EFS, FSx and storage CloudFormation (moto 5.2.3 + cfn-lint 1.57.2)

Course venv (`.venv`): moto 5.2.3, boto3 1.43.109, cfn-lint 1.57.2. Fake credentials, `mock_aws`, region us-east-1, no installs. Scripts and raw outputs are in the scratch folder `C:\Users\SYEDQA~1\AppData\Local\Temp\claude\C--Users-SyedQadri-Downloads-courses\65cfdac0-9a22-471b-8d76-56cc720b5245\scratchpad\spike04\`:
`common.py` (probe helper `p()`), `a_s3.py` (a.out), `a2_s3.py` (a2.out), `a3_dm.py`, `b_s3cfg.py` (b.out), `b2_follow.py` (b2.out), `c_ebs.py` (c.out), `c2_follow.py`, `d_efs_fsx.py` (d.out), `d2_follow.py`, `e_cfn.py` (e1.out, per-property bucket stacks), `e2_cfn.py` (e2.out, full storage stack), `e3_cfn.py`, `e4_outputs.py` (e4.out), `e5_more.py`, `e6_kms.py`, `f_lint.py` (f.out).
Earlier spikes: `2026-10-11-moto-compute-spike.md`, `2026-10-08-moto-cfnlint-spike.md`.

Headline:
- **S3 data plane is good** (versioning, delete markers, storage classes, Glacier read block, restore, multipart, tagging, presigned URLs via `requests`, object lock enforcement, S3-to-SQS events). Gaps: suspended versioning is wrong, `delete_bucket` ignores versions, bucket-name rules are not enforced.
- **S3 bucket policies are enforced, but crudely.** Any Deny statement whose Action and Resource match blocks every caller; `Principal` and `Condition` are ignored. The standard TLS-only Deny therefore blocks all of your own object requests. Block Public Access and ownership controls are stored but never enforced.
- **S3 configuration APIs store most things but validate almost nothing and silently drop some fields.** Lifecycle never executes; replication never copies.
- **moto's CloudFormation for storage is thin.** `AWS::S3::Bucket` applies only `BucketName`, `BucketEncryption` (not `BucketKeyEnabled`) and `Tags`. `AWS::S3::BucketPolicy` and `AWS::FSx::FileSystem` are skipped. `AWS::EC2::Volume` applies only `Size` and `AvailabilityZone`. `AWS::EFS::*` and `AWS::KMS::*` are good, with two crash traps.
- **EBS is partial.** Volume types and validation are patchy; Multi-Attach, encryption by default and snapshot tiering are not modelled; fast snapshot restore, Recycle Bin and DLM do not exist.
- **cfn-lint is the validation layer and covers much of what moto skips.** It misses all the cross-field timing rules (IA at 30 days, class order, replication needs versioning, EBS Iops ranges).

Note on one accidental outbound call: the probe "urllib GET of a presigned URL inside `mock_aws`" is not intercepted by moto, so it went out to the real network (host `mp-bkt.s3.amazonaws.com`, fake key `FOOBARKEY`, no real credentials) and returned HTTP 403. Course code must never fetch presigned URLs with `urllib`.

## A. S3 objects and versioning (`a_s3.py`, `a2_s3.py`, `a3_dm.py`)

| Feature | Result | Notes |
|---|---|---|
| put/get/head/delete, ranges, `delete_objects`, `IfNoneMatch="*"` | YES | `IfNoneMatch` on an existing key gives `PreconditionFailed` (412). `delete_objects` of a missing key reports it as Deleted. Delete of a missing key returns 204. |
| Bucket never versioned | YES | `get_bucket_versioning` returns no `Status` key. Puts return no `VersionId`; stored version id is the string `null`. |
| Versioning Enabled | YES | Each put returns a UUID `VersionId`. Versions appear in `list_object_versions` with `IsLatest`. The pre-versioning object appears as `VersionId: 'null'`. |
| Delete with versioning enabled (no version id) | YES | Returns `DeleteMarker: True`, a `VersionId`, and header `x-amz-delete-marker: true`. |
| GET (no version id) on delete marker | PARTIAL | `NoSuchKey`, "The specified key does not exist.", 404. The `x-amz-delete-marker` header is **not** present on the GET error (real S3 sends it). |
| GET with the delete marker's version id | PARTIAL | moto: `NoSuchVersion`, "The specified version does not exist.", 404. **Real S3 returns 405 `MethodNotAllowed`.** Do not teach this error code from moto output. |
| HEAD (no version id) | YES | 404 with `x-amz-delete-marker: true` and `x-amz-version-id`. |
| HEAD with delete marker's version id | YES | 405 (boto3 code `405`, message `Method Not Allowed`) with `x-amz-delete-marker: true`. |
| `list_objects_v2` after delete | YES | `KeyCount: 0` (current-version listing hides the key). |
| `list_object_versions` after delete | YES | `DeleteMarkers: [{Key, VersionId, IsLatest: True, ...}]`; older versions stay in `Versions` with `IsLatest: False`. |
| Delete the delete marker (by its version id) | YES | 204; the previous version becomes current again; GET returns the body. |
| Delete a specific version | YES | Permanent; the next older version becomes current. |
| Suspended versioning: `get_bucket_versioning` | YES | `Status: Suspended`. |
| Suspended: put | **NO (bug)** | Returns no `VersionId` (correct), but the write **wipes all older versions**: after `Enabled` put v1, `Suspended` put s1 and s2, `list_object_versions` shows only `null`; `get_object(VersionId=v1)` gives `NoSuchVersion`. Real S3 keeps v1. |
| Suspended: delete | **NO (bug)** | Returns 204 with no `DeleteMarker`; the key and all versions vanish; no null delete marker is created. Real S3 creates a delete marker with version id `null`. |
| `put_bucket_versioning` Status `Disabled` | PARTIAL | Accepted (200). Real S3 rejects it (cfn-lint also flags it). |
| MFADelete | PARTIAL | Accepted with a fake MFA string; `get_bucket_versioning` returns `Status` only, `MFADelete` is not echoed. |
| `delete_bucket` when only old versions/delete markers remain | **NO (bug)** | 204 success. Real S3: `BucketNotEmpty`. With a live current object moto does give `BucketNotEmpty` (409). |
| Bucket names | PARTIAL | 2 chars and 64 chars rejected (`InvalidBucketName`, "The specified bucket is not valid."). **Capitals (`Upper-Bkt`), underscores (`under_score`), IP-like (`192.168.1.1`), `xn--` prefix are all accepted.** Use cfn-lint (E1161) for naming rules. Re-creating an own bucket in us-east-1 returns 200 (matches real us-east-1). |
| `get_bucket_location` | YES | Returns the LocationConstraint given at create (`eu-west-1`) even from a us-east-1 client. |
| `copy_object` | YES | Copies body, metadata and (unless overridden) storage class. Copy onto self without changes: `InvalidRequest`, "This copy request is illegal because it is trying to copy an object to itself without changing the object's metadata, storage class, website redirect location or encryption attributes." (matches AWS). `StorageClass="GLACIER"` on copy is honoured; `STANDARD` shows as no `StorageClass` on HEAD. Copy of a DEEP_ARCHIVE source succeeds (real S3 would refuse until restored). |
| Storage class on put | YES | Accepted and returned by HEAD and `list_objects_v2`: STANDARD (field omitted on HEAD), STANDARD_IA, GLACIER, DEEP_ARCHIVE, INTELLIGENT_TIERING, GLACIER_IR, ONEZONE_IA, EXPRESS_ONEZONE, REDUCED_REDUNDANCY. `BOGUS`, `OUTPOSTS`, `SNOW` -> `InvalidStorageClass` "The storage class you specified is not valid" (400). |
| GET on GLACIER / DEEP_ARCHIVE | YES | `InvalidObjectState`, "The operation is not valid for the object's storage class", **403** (real S3 also 403). HEAD works. GLACIER_IR is readable. |
| `restore_object` | PARTIAL | GLACIER/DEEP_ARCHIVE: 202; the object is **immediately** restored (HEAD `Restore: ongoing-request="false", expiry-date="..."` = now+Days; GET then works). No asynchronous in-progress phase, no tier-based delay (Expedited accepted for DEEP_ARCHIVE, real S3 rejects). A second restore returns 200 (matches AWS). Restore on a STANDARD object -> `InvalidObjectState` 403. Restored copy does not expire. |
| Multipart: create / upload_part / list_parts / list_multipart_uploads / abort / complete | YES | `upload_part` of a 1 KiB part is accepted; the minimum is enforced at **complete**: non-last part < 5 MiB -> `EntityTooSmall`, "Your proposed upload is smaller than the minimum allowed object size." (400). 5 MiB + 100 B completes; ETag `<md5>-2`; `Location` is `http://<bucket>.s3.amazonaws.com/<key>`. `PartNumber` 10001 -> `InvalidArgument` "Part number must be an integer between 1 and 10000, inclusive". Bad ETag -> `InvalidPart`. Abort twice -> `NoSuchUpload`. `list_multipart_uploads` shows `Initiated` in 2010 (wrong clock, do not assert on it). **Bug:** `upload_part` with an unknown UploadId raises a raw `KeyError` inside moto (client sees an exception, not `NoSuchUpload`). |
| `generate_presigned_url` (get/put) | YES | URL is `https://<bucket>.s3.amazonaws.com/<key>?AWSAccessKeyId=FOOBARKEY&Signature=...&x-amz-security-token=testing&Expires=...`. |
| `requests.get/put` on that URL inside `mock_aws` | YES | `requests` is intercepted: GET returned the body, PUT stored the object (readable through boto3). |
| `urllib.request.urlopen` on that URL | **NO** | Not intercepted; goes to the real network (HTTP 403 from the real endpoint). Do not use. |
| `generate_presigned_post` | YES | Returns `url` plus `fields` (key, AWSAccessKeyId, policy, signature). |
| Object tagging | YES | `put_object_tagging` / `get_object_tagging` / `delete_object_tagging`; `put_object(Tagging="x=1&y=2")` works; `x-amz-tagging-count` and `TagCount` returned on GET/HEAD. |
| `head_object` fields | YES | `ContentLength, ETag, LastModified, ContentType, Metadata, CacheControl, StorageClass, ServerSideEncryption, SSEKMSKeyId, BucketKeyEnabled` (when set by bucket default), checksums (`ChecksumSHA256` with `ChecksumMode=ENABLED`), `Restore`, `ObjectLockMode/RetainUntilDate/LegalHold`, `VersionId` header. |
| Server-side encryption on put | YES | `ServerSideEncryption="AES256"` or `aws:kms` + `SSEKMSKeyId` echoed. Plain object under a bucket without default encryption: no `ServerSideEncryption` field (real S3 now reports AES256 for everything). |
| Lifecycle `Expiration` header on put/head | NO | `Expiration` is always absent even with an expiry rule. |

## B. S3 bucket configuration (`b_s3cfg.py`, `b2_follow.py`)

| Feature | Result | Notes |
|---|---|---|
| Default encryption on a new bucket | **NO** | `get_bucket_encryption` on a fresh bucket -> `ServerSideEncryptionConfigurationNotFoundError` (404). Real S3 returns SSE-S3 (AES256, BucketKeyEnabled false) for every new bucket since Jan 2023. Model "all buckets are encrypted by default" in text, not with moto. |
| `put/get_bucket_versioning` | YES | See section A. |
| `put/get/delete_public_access_block` | YES (stored) | Four flags round-trip. A partial config (only `BlockPublicAcls`) is stored with the other three False. Empty config -> `InvalidRequest` "Must specify at least one configuration." Fresh bucket -> `NoSuchPublicAccessBlockConfiguration`. Account-level (`s3control.get_public_access_block`) works and starts as `NoSuchPublicAccessBlockConfiguration`. |
| Block Public Access **enforcement** | **NO** | With all four flags True: `put_bucket_policy` with `Principal: *` Allow succeeded; `put_bucket_acl(ACL="public-read")` succeeded; `put_object(ACL="public-read")` succeeded. Real S3 returns `AccessDenied`. `get_bucket_policy_status` returns an empty `PolicyStatus` (no `IsPublic`). |
| `put_bucket_encryption` SSE-S3 | YES | Round-trips; `BucketKeyEnabled` returned as False by default. New objects then report `ServerSideEncryption: AES256`. |
| `put_bucket_encryption` SSE-KMS + `BucketKeyEnabled: true` | YES | Round-trips including the key ARN and `BucketKeyEnabled: True`. New objects report `aws:kms`, the key ARN and `BucketKeyEnabled: True`. |
| Encryption validation | NO | `SSEAlgorithm: BOGUS` accepted; `aws:kms:dsse` accepted; no check that the KMS key exists. |
| `put/get_bucket_policy` round trip | YES | `get_bucket_policy` returns **exactly the same string** that was put (`got == json.dumps(policy)`). |
| Policy validation | NO | Accepted without error: invalid JSON (`{nope`), `Principal: {"AWS": "not-an-arn"}`, Resource of a different bucket, missing `Version`. Real S3 rejects these (`MalformedPolicy`). cfn-lint catches the principal and missing-field cases at template level. |
| Policy enforcement | PARTIAL (crude) | Every `Deny` statement whose Action and Resource match denies **every request, including your own admin credentials**. `Principal` and `Condition` are **ignored**. Evidence: Deny `s3:*` with `aws:SecureTransport=false` -> a normal boto3 (https) `get_object`/`put_object` returns 403 `Forbidden`; `Deny s3:PutObject` unless `s3:x-amz-server-side-encryption=aws:kms` blocks the KMS put too; `Deny` for principal `arn:aws:iam::999999999999:root` blocks the owner. `Deny s3:DeleteObject` blocks delete but not get. Observed that `list_objects_v2` was not blocked by Deny `s3:*` (listing is not checked), and the owner can still `get/delete_bucket_policy`. An `Allow Principal:*  s3:GetObject` policy makes an anonymous `requests.get` return 200; without it anonymous GET returns 403. |
| `put/get_bucket_lifecycle_configuration`: stored fields | PARTIAL | Stored and returned: `ID`, `Status`, `Filter.Prefix`, `Filter.Tag`, `Filter.And.{Prefix,Tags}`, `Transitions` (Days, Date, StorageClass), `Expiration.{Days,Date,ExpiredObjectDeleteMarker}`, `NoncurrentVersionTransitions` incl. `NewerNoncurrentVersions`, `NoncurrentVersionExpiration.NoncurrentDays`, `AbortIncompleteMultipartUpload.DaysAfterInitiation`. |
| Lifecycle: **silently dropped** fields | **NO** | `Filter.ObjectSizeGreaterThan` and `ObjectSizeLessThan` (top level and inside `And`) are dropped: a size-filtered rule comes back with `Filter: {}` (looks like "applies to everything"). `NoncurrentVersionExpiration.NewerNoncurrentVersions` is dropped (only `NoncurrentDays` returns). |
| Lifecycle validation | **NO** | All of these are accepted (200): STANDARD_IA at 10 days, ONEZONE_IA at 10 days, DEEP_ARCHIVE(100) before GLACIER(200), Expiration(50) before transition(100), transition class `BOGUS`, transition to `STANDARD`, duplicate rule IDs, rule with no action, `Status: Maybe`, `Expiration.Days: 0`, legacy `Prefix` without `Filter`. Rejected: `Expiration` with both `Days` and `ExpiredObjectDeleteMarker` (`MalformedXML`), `NoncurrentVersionTransition` without `NoncurrentDays` (`MalformedXML`: "The XML you provided was not well-formed or did not validate against our published schema"). |
| Lifecycle execution | **NO** | Never runs. No objects expire or transition, no `Expiration` header, no clock-driven effect. Model in pure Python. |
| `put_bucket_replication` | PARTIAL | Source without versioning -> `InvalidRequest`, "Versioning must be 'Enabled' on the bucket to apply a replication configuration" (matches AWS). Destination bucket versioning, destination existence and role validity are **not** checked (nonexistent `arn:aws:s3:::nope-nope` and role `junk` accepted). IAM role is optional in practice. Stored/returned: `ID, Priority, Filter, Status, Destination.{Bucket,StorageClass,EncryptionConfiguration,ReplicationTime,Metrics}`. **Dropped:** `SourceSelectionCriteria`, `ExistingObjectReplication`; `DeleteMarkerReplication` is always returned as `Disabled` even when `Enabled` was set. |
| Replication copies objects | **NO** | After put on a replicated source the destination `KeyCount` is 0; `ReplicationStatus` is absent on HEAD. |
| Object Lock configuration | YES | `create_bucket(ObjectLockEnabledForBucket=True)` enables versioning automatically and `put/get_object_lock_configuration` round-trips (`DefaultRetention` Mode/Days; `Years` returned as 0). Enabling on a non-empty existing bucket -> `InvalidBucket` "Bucket needs to be empty" (stricter than AWS). Days and Years together -> `MalformedXML`. |
| Object Lock enforcement | YES | Default COMPLIANCE retention: deleting the locked version -> `AccessDenied` 403 (even with `BypassGovernanceRetention`). GOVERNANCE: delete without bypass -> `AccessDenied`; with `BypassGovernanceRetention=True` it succeeds. Delete without version id creates a delete marker (correct). Legal hold ON blocks version delete. `delete_objects` reports the failure per key: `Code: AccessDenied`, "Access Denied because object protected by object lock.". HEAD shows `ObjectLockMode` and `ObjectLockRetainUntilDate`. Gaps: `put_object_retention` **shortening** a COMPLIANCE retention is accepted (AWS rejects); suspending versioning on a lock bucket is accepted (AWS rejects). |
| `put_bucket_ownership_controls` | PARTIAL | Stored/returned; invalid value `Bogus` accepted. **Not enforced:** after `BucketOwnerEnforced`, `put_bucket_acl(ACL="public-read")` and `put_object(ACL=...)` still succeed (AWS: `AccessControlListNotSupported`). |
| `put_bucket_notification_configuration` | YES | SNS/SQS/Lambda configs stored; Lambda ARN of a nonexistent function accepted. Returned config gets a generated `Id`. `EventBridgeConfiguration` is not returned. **Events are delivered**: after config, SQS receives an `s3:TestEvent`, then real `ObjectCreated:Put` and `ObjectRemoved:Delete` records for matching keys (verified with a queue). |
| `put_bucket_logging` | YES | Requires the target bucket to exist and to grant logging (target bucket policy for `logging.s3.amazonaws.com`, or log-delivery ACL); otherwise `InvalidTargetBucketForLogging` "You must either provide the necessary permissions to the logging service using a bucket policy or give the log-delivery group WRITE and READ_ACP permissions to the target bucket" (nonexistent target: "The target bucket for logging does not exist."). With the policy in place moto writes log objects into the target bucket on subsequent requests (2 objects after 2 requests; contents not checked). |
| Transfer Acceleration | YES | `put/get_bucket_accelerate_configuration` round-trip (`Enabled`). A bucket name containing dots gave a misleading error ("Found unsupported HTTP method in CORS config. Unsupported method is PutBucketAccelerateConfiguration"). Fresh bucket returns no `Status`. |
| CORS, website, bucket tagging, request payment | YES | Round-trip. Request payment `get` returns no `Payer` field. |
| Intelligent-Tiering config | NO | `put_bucket_intelligent_tiering_configuration` returns 200 but `get` returns `{}` (tierings lost). |
| Analytics / inventory / metrics configs | PARTIAL | `put_*` accepted (200); read-back not verified beyond the CloudFormation path (also empty there). |
| `s3control` access points, multi-region access points | PARTIAL | `create_access_point` returns ARN and alias; `create_multi_region_access_point` returns a request token ARN. Account-level PAB works. |
| S3 Express One Zone directory buckets | NO | `create_bucket` with `Bucket.Type=Directory` -> `NoSuchBucket`. `StorageClass=EXPRESS_ONEZONE` on an ordinary bucket is accepted. |
| `select_object_content` | PARTIAL | Call returns a stream object (content not verified). |

## C. EBS via EC2 (`c_ebs.py`, `c2_follow.py`)

| Feature | Result | Notes |
|---|---|---|
| `create_volume` default type | YES | No type -> `gp2`, `Encrypted: False`, `State: available` (instant), no Iops/Throughput fields. |
| gp3 | PARTIAL | Default `Iops: 3000`. **`Throughput` has no default** (field absent, not 125); explicit `Throughput` echoed. No range validation: Iops 20000, Iops 2000 (<3000), Throughput 2000, Iops 10000 on a 10 GiB volume, Size 0 and Size 16385 are all accepted. |
| gp2 / st1 / sc1 / standard | PARTIAL | Created with no size-range validation (st1 at 100 GiB accepted; real minimum 125). gp2 given `Iops` fails with a **misleading** error: `InvalidParameterDependency`, "The parameter [VolumeType] requires the parameter Iops to be set." (also for gp2 with `Throughput`, and io2 with `Throughput`). |
| io1 / io2 | PARTIAL | Missing `Iops` -> `InvalidParameterDependency`, "The parameter [VolumeType] requires the parameter Iops to be set." (matches AWS in spirit). No range checks: io1 Iops 20, 64001; io2 Iops 256000 accepted. |
| Unknown volume type, bad AZ | NO | `VolumeType="bogus"` and `AvailabilityZone="us-east-1z"` are accepted. |
| Multi-Attach flag | PARTIAL | `MultiAttachEnabled=True` stored on io1/io2 and echoed. On gp3 the error is garbled: `InvalidParameterDependency`, "The parameter [MultiAttachEnabled] requires the parameter VolumeType to be set." (type was set). Behaviour not modelled: see attach row. |
| Encrypted / KmsKeyId | YES | `Encrypted=True` without key -> a default key ARN is generated; with `KmsKeyId` the ARN is echoed. `KmsKeyId` without `Encrypted` -> `InvalidParameterDependency`, "The parameter [KmsKeyId] requires the parameter Encrypted to be set." |
| `enable/disable/get_ebs_encryption_by_default` | PARTIAL | The flag toggles and reads back, but **new volumes and root volumes stay `Encrypted: False`**. `get_ebs_default_kms_key_id` is not implemented (`NotImplementedError`); `modify_ebs_default_kms_key_id` works. |
| `modify_volume` | PARTIAL | Applied instantly: `ModificationState: completed`, `Progress: 100`; `describe_volumes_modifications` returns the record with `Original*`/`Target*` fields; `describe_volumes` shows the new type/size/Iops/Throughput. No 6-hour cooldown (modifying twice in a row works), shrinking accepted, io2 without Iops accepted, nonexistent volume -> `InvalidVolume.NotFound`. |
| attach / detach | PARTIAL | `attach_volume` returns `State: attaching`; `describe_volumes` then shows `attached` and volume `in-use`. `detach_volume` works only when `InstanceId` and/or `Device` is passed; **`detach_volume(VolumeId=...)` alone crashes inside moto** (`TypeError: object of type 'NoneType' has no len()`). Deleting an attached volume -> `VolumeInUse`, "Volume <id> is currently attached to <instance>". Attaching a volume cross-AZ succeeds (AWS rejects). Instance `BlockDeviceMappings` list the attachment; `modify_instance_attribute` DeleteOnTermination accepted. |
| Multi-Attach behaviour | **NO** | Attaching a non-multi-attach volume to a second instance succeeds and **replaces** the first attachment. Attaching a `MultiAttachEnabled` io2 volume to two instances succeeds but `describe_volumes` shows only one attachment. Model in pure Python. |
| `run_instances` BlockDeviceMappings | PARTIAL | A 50 GiB gp3 volume is created and attached; `VolumeType`, `Size`, `Encrypted` kept, but `Iops` comes back 3000 (requested 4000) and `Throughput` is missing. |
| `create_snapshot` | YES | Returns `State: completed`, `Progress: 100%` immediately, `VolumeSize`, `StorageTier: standard`, tags via TagSpecifications. Snapshot of an encrypted volume is `Encrypted: True`. Missing volume -> `InvalidVolume.NotFound`. |
| `describe_snapshots` | **TRAP** | Without `SnapshotIds` the result includes **~1,178 pre-bundled snapshots** (owner 801119661308 etc.); `OwnerIds=["self"]` does **not** filter them out. Always pass `SnapshotIds` or filter by `volume-id`/tag. |
| `copy_snapshot` | PARTIAL | Plain, `Encrypted=True` + `KmsKeyId` (result `Encrypted: True`, KmsKeyId set), and cross-region (client in eu-west-1) all work and return a new `SnapshotId`. A nonexistent `KmsKeyId` (`alias/nope`) is accepted. |
| `create_volume` from snapshot | PARTIAL | Larger size accepted; smaller size also accepted (AWS rejects); from an encrypted snapshot the volume is `Encrypted: True`. |
| Snapshot sharing | YES | `modify_snapshot_attribute` createVolumePermission add by `UserIds` or `GroupNames=["all"]` works and reads back; sharing an encrypted snapshot is accepted (AWS needs a customer key shared). |
| Snapshot tiering | PARTIAL | `modify_snapshot_tier(StorageTier="archive")` and `restore_snapshot_tier` return plausible responses and `describe_snapshots` shows `StorageTier: archive`; no waiting period and no 90-day minimum. |
| Fast snapshot restore | **NO** | `enable_/describe_/disable_fast_snapshot_restores` -> `NotImplementedError`. |
| `lock_snapshot`, `get_snapshot_block_public_access_state`, `describe_volume_status`, `describe_volume_attribute` | **NO** | `NotImplementedError` ("The ... action has not been implemented" / "... is not yet implemented"). |
| Delete snapshot in use by an AMI | NO | Succeeds (AWS blocks). `register_image` from a snapshot works. |
| EBS direct APIs (`ebs`) | PARTIAL | `start_snapshot` works; `list_snapshot_blocks` on an EC2 snapshot raises `KeyError`. |
| Instance types EBS info | YES | `describe_instance_types` returns `EbsInfo` (BaselineBandwidthInMbps, MaximumIops, EbsOptimizedSupport, NvmeSupport) and `InstanceStorageInfo` for `m5d.large` (75 GB ssd): usable as a data source for pure-Python sizing exercises. |
| Recycle Bin (`rbin`) | **NO** | Every call -> HTTP 404 "Not yet implemented"; `ec2.list_snapshots_in_recycle_bin` -> `NotImplementedError`. |
| Data Lifecycle Manager (`dlm`) | **NO** | Every call -> 404 "Not yet implemented". |
| AWS Backup | PARTIAL | `create_backup_vault` and `create_backup_plan` (with `Lifecycle.DeleteAfterDays`) work; usable as the "backup" stand-in for EBS/EFS lifecycle teaching. |

## D. EFS, FSx and other storage services (`d_efs_fsx.py`, `d2_follow.py`)

| Feature | Result | Notes |
|---|---|---|
| EFS `create_file_system` defaults | YES | `PerformanceMode: generalPurpose`, `ThroughputMode: bursting`, `Encrypted: False`, `LifeCycleState: available` immediately, `SizeInBytes {Value, ValueInIA, ValueInStandard}`, `Name` taken from the `Name` tag. Same `CreationToken` twice -> `FileSystemAlreadyExists` (409). |
| EFS PerformanceMode / ThroughputMode | PARTIAL | `generalPurpose`, `maxIO`, `bursting`, `provisioned` (+ `ProvisionedThroughputInMibps`), `elastic` all accepted and echoed. **No validation:** `PerformanceMode: bogus`, `ThroughputMode: bogus`, `provisioned` without a value, `bursting` with a value are accepted. |
| EFS encryption | YES | `Encrypted=True` generates a key ARN; `KmsKeyId` echoed. `KmsKeyId` without `Encrypted` -> `BadRequest`, `If kms_key_id given, "encrypted" must be True.` |
| EFS One Zone | PARTIAL | `AvailabilityZoneName="us-east-1a"` accepted; response adds `AvailabilityZoneId: use1-az6`. One Zone + `maxIO` accepted (AWS rejects). A mount target for a One Zone file system in a **different** AZ's subnet succeeds (AWS rejects). |
| EFS lifecycle policies | PARTIAL | `put/describe_lifecycle_configuration` round-trips `TransitionToIA`, `TransitionToArchive`, `TransitionToPrimaryStorageClass`. No validation (`AFTER_31_DAYS`, Archive without IA accepted). No tiering ever executes (`ValueInIA` stays 0). |
| EFS `update_file_system` | **NO** | `NotImplementedError` (cannot switch throughput mode after create). |
| EFS backup policy | PARTIAL | `put_backup_policy` is `NotImplementedError`; `describe_backup_policy` -> `PolicyNotFound`. Via CloudFormation `BackupPolicy: ENABLED` does set it (see E). |
| EFS file system policy | YES | `put/describe_file_system_policy` round-trip the JSON string. |
| EFS replication, account preferences | **NO** | `create_replication_configuration`, `describe_replication_configurations`, `describe_account_preferences` -> `NotImplementedError`. |
| EFS mount targets | YES | `create_mount_target` returns `IpAddress` (next free in the subnet, or the one given), `NetworkInterfaceId`, `AvailabilityZoneName/Id`, `VpcId`, `LifeCycleState: available`; a second target in the same AZ -> `MountTargetConflict` 409 "mount target already exists in this AZ". Security groups round-trip (`describe/modify_mount_target_security_groups`). An ENI with that IP is created in the subnet. Deleting a file system that has mount targets -> `FileSystemInUse` 409 "Must delete all mount targets before deleting file system." |
| EFS access points | PARTIAL | Create/describe with `PosixUser`, `RootDirectory.CreationInfo`, tags works. Invalid `Permissions: "9999"` and a non-root path without `CreationInfo` accepted. |
| EFS tags | YES | `tag_resource`, `list_tags_for_resource`. |
| FSx `create_file_system` LUSTRE (SCRATCH_2, PERSISTENT_2) | PARTIAL | Created; response has `FileSystemId`, `DNSName`, `ResourceARN`, `StorageCapacity`, `SubnetIds`, `LustreConfiguration.DeploymentType`/`PerUnitStorageThroughput`. `ImportPath`/`ExportPath` dropped. Capacity 1000 (invalid) and `DeploymentType: BOGUS` accepted. |
| FSx WINDOWS | PARTIAL | SINGLE_AZ_2 and MULTI_AZ_1 (`ActiveDirectoryId`, `PreferredSubnetId`) and self-managed AD created; the password is not echoed. No AD requirement enforced. |
| FSx ONTAP / OPENZFS | PARTIAL | Create succeeds for MULTI_AZ_1 / SINGLE_AZ_1 (ONTAP) and SINGLE_AZ_1 (OpenZFS) with deployment type and throughput echoed; no ONTAP SVM/volume model (`create_volume` for ONTAP needs real SVM ids). |
| FSx describe | PARTIAL | **No `Lifecycle` field** in `describe_file_systems` (state is not shown; `delete_file_system` returns `Lifecycle: DELETING`). No `OwnerId`. |
| FSx tags, backups | PARTIAL | `tag_resource` OK; `create_backup` returns `Lifecycle: CREATING` and `describe_backups` lists none afterwards. |
| FSx `update_file_system`, data repository associations | **NO** | `NotImplementedError`. Invalid type `BOGUS` raises a raw `ValueError("Invalid FileSystemType: BOGUS")`. |
| Storage Gateway | **NO** | Every call (`list_gateways`, `activate_gateway`) -> HTTP 404 "Not yet implemented". |
| Snow Family (`snowball`) | **NO** | 404 "Not yet implemented". |
| DataSync, Transfer Family, Glacier (vaults), AWS Backup, s3tables | PARTIAL | `datasync.create_location_s3`, `transfer.create_server`, `glacier.create_vault`/`upload_archive` (returns archiveId and tree-hash checksum), `backup.create_backup_vault`, `s3tables.list_table_buckets` respond. Depth not tested. CloudFront `list_distributions` responds. |

## E. CloudFormation in moto (`e_cfn.py`, `e2_cfn.py`, `e4_outputs.py`, `e5_more.py`, `e6_kms.py`)

moto's S3 template path (`moto/s3/models.py: FakeBucket.create_from_cloudformation_json`) reads only `BucketName`, `BucketEncryption` and `Tags`. Everything else in the properties is ignored, with no warning.

### E1. `AWS::S3::Bucket` properties, one stack per property (read back with boto3)

| Property | Stack result | Applied in moto? |
|---|---|---|
| `BucketName` | CREATE_COMPLETE | YES (omitted name -> `<stack>-<logical>-<random>`, e.g. `s-bkt-hs4ngjj5u9bu`). **No name validation:** `UPPER_Name` creates a bucket. |
| `Tags` | CREATE_COMPLETE | YES (also on `update_stack`). |
| `BucketEncryption` (SSE-S3 AES256) | CREATE_COMPLETE | YES. |
| `BucketEncryption` (aws:kms, `KMSMasterKeyID: !GetAtt Key.Arn`) | CREATE_COMPLETE | PARTIAL: algorithm and key ARN applied; **`BucketKeyEnabled: true` dropped** (reads back False). |
| `VersioningConfiguration` | CREATE_COMPLETE | **DROPPED** (`get_bucket_versioning` has no Status). |
| `PublicAccessBlockConfiguration` | CREATE_COMPLETE | **DROPPED** (`NoSuchPublicAccessBlockConfiguration`). |
| `LifecycleConfiguration` (transitions, noncurrent, expiration, abort-multipart, ExpiredObjectDeleteMarker, TagFilters, ObjectSizeGreaterThan) | CREATE_COMPLETE | **DROPPED** (`NoSuchLifecycleConfiguration`). |
| `OwnershipControls` | CREATE_COMPLETE | **DROPPED** (`OwnershipControlsNotFoundError`). |
| `ObjectLockEnabled`, `ObjectLockConfiguration` | CREATE_COMPLETE | **DROPPED** (`ObjectLockConfigurationNotFoundError`). |
| `ReplicationConfiguration` | CREATE_COMPLETE | **DROPPED** (`ReplicationConfigurationNotFoundError`). |
| `NotificationConfiguration`, `LoggingConfiguration`, `AccelerateConfiguration` | CREATE_COMPLETE | **DROPPED** (empty on read-back). |
| `CorsConfiguration`, `WebsiteConfiguration` | CREATE_COMPLETE | **DROPPED** (`NoSuchCORSConfiguration`, `NoSuchWebsiteConfiguration`). |
| `IntelligentTieringConfigurations`, `AnalyticsConfigurations`, `InventoryConfigurations`, `MetricsConfigurations` | CREATE_COMPLETE | **DROPPED**. |
| `DeletionPolicy: Retain` | CREATE_COMPLETE | YES: bucket survives `delete_stack`. A bucket holding an object also survives `delete_stack` (real CloudFormation would end in DELETE_FAILED). |
| `Parameters`/`Conditions`/`Fn::If` with `Ref` into Tags | CREATE_COMPLETE | YES (a conditioned SQS queue was created). |

`!GetAtt Bucket.Arn`, `.DomainName`, `.RegionalDomainName`, `.DualStackDomainName`, `.WebsiteURL` all work and resolve to the expected strings (for example `arn:aws:s3:::stor-main-123456789012`, `stor-main-123456789012.s3.us-east-1.amazonaws.com`). `!Ref Bucket` gives the bucket name. `Fn::Sub "${Bucket.Arn}/*"` works.

### E2. Other resources (one full storage stack, `e2_cfn.py`)

| Resource / property | Result |
|---|---|
| `AWS::S3::BucketPolicy` | **SKIPPED.** moto prints "No Moto CloudFormation support for AWS::S3::BucketPolicy" (a UserWarning plus stdout line); the stack is still CREATE_COMPLETE and `get_bucket_policy` -> `NoSuchBucketPolicy`. The resource shows in `list_stack_resources` with empty type/physical id. So neither the TLS-only Deny nor the ELB log-delivery statement exists after deployment (which is a mixed blessing: the policy cannot lock tests out). |
| `AWS::KMS::Key` | PARTIAL. `Description`, `EnableKeyRotation`, `KeySpec`, `Enabled` applied (read back). **Trap 1:** `KeyPolicy` given as an object (normal CloudFormation YAML/JSON) is stored as a dict and every later `describe_key` crashes in moto with `TypeError: the JSON object must be str, bytes or bytearray, not dict` (create_stack itself succeeds). Pass `KeyPolicy` as a JSON string (`Fn::Sub`/`Fn::Join`/`json.dumps` in the test template) to avoid it. **Trap 2:** `Tags` (`[{Key,Value}]`) makes `create_stack` raise `KeyError: 'TagKey'`. **Trap 3:** omitting `KeyPolicy` raises `KeyError: 'KeyPolicy'`. `!GetAtt Key.Arn` works; `!GetAtt Key.KeyId` -> `create_stack` fails: "Template error: resource Key does not support attribute type KeyId in Fn::GetAtt". `!Ref Key` returns the key id. |
| `AWS::KMS::Alias` | YES (`alias/stor` created; `!Ref` returns the alias name). |
| `AWS::EC2::Volume` | **PARTIAL, mostly dropped.** Only `Size` and `AvailabilityZone` are applied. `VolumeType` (gp3 -> **gp2**), `Iops`, `Throughput`, `Encrypted`, `KmsKeyId`, `MultiAttachEnabled` and user `Tags` are dropped (the volume only carries the `aws:cloudformation:*` tags). `!Ref Vol` gives the volume id; `!GetAtt Vol.VolumeId` is not supported (see Outputs trap). |
| `AWS::EFS::FileSystem` | YES. `Encrypted`, `KmsKeyId` (from `!GetAtt Key.Arn`), `PerformanceMode`, `ThroughputMode`, `ProvisionedThroughputInMibps`, `LifecyclePolicies` (IA + Archive), `BackupPolicy`, `FileSystemTags` (Name tag -> `Name`), `AvailabilityZoneName` (One Zone) all read back correctly. `!Ref` returns the fs id. `!GetAtt Fs.Arn` and `FileSystemId` are not supported (Outputs trap). |
| `AWS::EFS::MountTarget` | YES (2 targets in 2 AZs, IPs assigned, security groups). `!GetAtt MtA.IpAddress` unsupported. |
| `AWS::EFS::AccessPoint` | YES (PosixUser, RootDirectory read back as numbers). `AccessPointTags` is read, but `!Ref Ap` yields the Python object repr `<moto.efs.models.AccessPoint object at 0x...>` and the physical id is empty; do not output or reference the access point. `!GetAtt Ap.Arn` unsupported. |
| `AWS::FSx::FileSystem` | **SKIPPED** (same "No Moto CloudFormation support" warning; stack COMPLETE; no FSx file system created). |
| Stack status | The full 17-resource template (KMS, S3, bucket policy, 2 volumes, VPC, 2 subnets, SG, 2 EFS, 2 mount targets, access point, FSx) reached CREATE_COMPLETE with no FAILED events. |

### E3. Outputs trap (important)

If **any** `Outputs` entry uses a `Fn::GetAtt` that moto does not support, `create_stack` still reaches CREATE_COMPLETE but **all Outputs of the stack are silently dropped** (`describe_stacks` has no `Outputs` key). Seen with `!GetAtt Vol.VolumeId`, `!GetAtt Fs.Arn`, `!GetAtt MtA.IpAddress`, `!GetAtt Ap.Arn`. Supported and verified individually: `Bucket.{Arn,DomainName,RegionalDomainName,DualStackDomainName,WebsiteURL}`, `Key.Arn`, and `!Ref` of Bucket, Key, Alias, Volume, FileSystem, MountTarget. In tests, assert on resources through boto3 rather than on stack Outputs that use unsupported GetAtt, or keep such outputs out of the deployed template.

### E4. Workarounds

- Properties dropped by moto: after `create_stack`, apply the same setting with boto3 using the physical bucket name from `describe_stack_resource` (for example `put_bucket_versioning`, `put_public_access_block`, `put_bucket_lifecycle_configuration`), or assert on the rendered template with `awslib.cfn.render`/`resources()` (the harness already reads `Properties` of the template as plain dicts) and on cfn-lint output. The second option is the recommendation: the template is the artifact being taught, and moto cannot prove those properties anyway.
- BucketPolicy: assert on the rendered template (`PolicyDocument` statements) and evaluate it with `awslib.policy_eval` rather than deploying it. If a policy must exist in moto, `put_bucket_policy` with boto3 (mind the crude Deny enforcement: never put a Condition-based Deny on a bucket you still need to write to).
- EBS volume attributes: assert on the rendered template; use boto3 `create_volume` for runtime behaviour.
- KMS key: pass `KeyPolicy` as a string; omit `Tags`; do not use `GetAtt KeyId`.
- Outputs: only use the supported GetAtt list above, or do not deploy Outputs with other attributes.

## F. cfn-lint 1.57.2 (`f_lint.py`, `f.out`)

In-process `cfnlint.api.lint` takes ~1.1-2.2 s per template here. The correct storage template (KMS key, alias, versioned/KMS-encrypted/PAB/ownership-controlled bucket with 3 transitions, noncurrent rules, abort-multipart and a delete-marker rule, BucketPolicy with TLS-deny and ELB log-delivery service principal, gp3 volume, EFS with IA+Archive, mount target) returned **0 findings**.

| Mistake injected | cfn-lint result |
|---|---|
| Transition to STANDARD_IA / ONEZONE_IA at 10 days | **NOT caught** (0 findings). Also not caught for noncurrent transitions at 10 days. |
| DEEP_ARCHIVE (100) listed before GLACIER (200); same-day transitions; expiration (60) before transitions (90/365) | **NOT caught** (0 findings). |
| Transition `StorageClass: STANDARD` or `BOGUS` | E3030 "'STANDARD' is not one of ['DEEP_ARCHIVE', 'GLACIER', 'Glacier', 'GLACIER_IR', 'INTELLIGENT_TIERING', 'ONEZONE_IA', 'STANDARD_IA']". |
| `NoncurrentVersionTransition` without `TransitionInDays` | E3003 "'TransitionInDays' is a required property". |
| `NoncurrentVersionExpiration` without `NoncurrentDays` | E3003 "'NoncurrentDays' is a required property". |
| `AbortIncompleteMultipartUpload: {}` | E3003 "'DaysAfterInitiation' is a required property". |
| Lifecycle `Status: Maybe` | E3030 "'Maybe' is not one of ['Enabled', 'Disabled']". |
| `ExpiredObjectDeleteMarker` together with `ExpirationInDays`; rule with no action; `ObjectSizeGreaterThan` as integer | NOT caught (0 findings). |
| BucketPolicy statement `Principal: {"AWS": "not-an-arn"}` | **Caught**, E3512 x6 ("'not-an-arn' is not valid under any of the given schemas", "'not-an-arn' does not match '^\\d{12}$'", "... does not match '^arn:(aws\|aws-cn\|aws-us-gov):iam::\\d{12}:(?:root\|user\|group\|role)'", ...). Noisy: six messages for one mistake. |
| Statement with no `Principal` | E3512 "Only one of ['Principal', 'NotPrincipal'] is a required property". |
| `Effect: Permit` | E3512 "'Permit' is not one of ['Allow', 'Deny']". |
| Bad action `s3:PutObjekt` | W3037 (warning, not error) listing the valid lower-cased actions. |
| Principal with an unknown key (`{"Service":..., "Bogus": "x"}`); `SecureTransport` condition as boolean `False`; PolicyDocument without `Version`; Resource ARN of another bucket | NOT caught (0 findings). |
| Bucket name with capitals (`MyBucket`) | **Caught**: E1161 "'MyBucket' is not a 'AWS::S3::Bucket.Name' with pattern '^(?![.\\-])(?!.*\\.\\.)(?!.*\\-\\.)(?!.*\\.\\-)[a-z0-9.\\-]{3,63}(?<![.\\-])$'" plus E3031 "'MyBucket' does not match '^([a-z0-9][a-z0-9.-]*[a-z0-9])?$'". Underscore name: same two; 2-char name: E1161; 64-char name: E1161 + E3033 "is longer than 63". `Fn::Sub` name with capitals: W1031 (warning) "... when 'Fn::Sub' is resolved". |
| `ReplicationConfiguration` without `VersioningConfiguration`, or with `Status: Suspended` | **NOT caught** (0 findings). |
| `ObjectLockEnabled: true` without versioning | NOT caught. |
| `VersioningConfiguration.Status: Disabled` | E3030 "'Disabled' is not one of ['Enabled', 'Suspended']". |
| SSE `AES128` | E3030 "'AES128' is not one of ['aws:kms', 'AES256', 'aws:kms:dsse']". `AES256` plus `KMSMasterKeyID` NOT caught. |
| PAB value `"yes"` | E3012 "'yes' is not of type 'boolean'". |
| `ObjectOwnership: Bogus` | E3030 "'Bogus' is not one of ['ObjectWriter', 'BucketOwnerPreferred', 'BucketOwnerEnforced']". `AccessControl: PublicRead` alongside BucketOwnerEnforced: only W3045 "'AccessControl' is a legacy property. Consider using 'AWS::S3::BucketPolicy' instead". |
| Bucket logging to itself | E3004 "Circular Dependencies for resource Bucket. Circular dependency with [Bucket]". |
| EBS: gp3 Iops 20000 / 2000, Throughput 2000, Iops 10000 on 10 GiB, io2 without Iops, gp2 with Iops, st1 at 100 GiB, Size 20000, MultiAttach on gp3, `KmsKeyId` without/with `Encrypted: false` | **None caught** (0 findings). |
| EBS `VolumeType: gp4` | E3030 "'gp4' is not one of ['gp2', 'gp3', 'io1', 'io2', 'sc1', 'st1', 'standard'] (case-insensitive)". |
| Volume without `Size` and `SnapshotId` | E3017 / E3003 "'Size' is a required property" ... (5 findings, noisy). |
| EFS `ThroughputMode: turbo`; IA `AFTER_31_DAYS` | E3030 "'turbo' is not one of ['bursting', 'elastic', 'provisioned']"; "'AFTER_31_DAYS' is not one of ['AFTER_14_DAYS', 'AFTER_180_DAYS', 'AFTER_1_DAY', 'AFTER_270_DAYS', 'AFTER_30_DAYS', 'AFTER_365_DAYS', 'AFTER_60_DAYS', 'AFTER_7_DAYS', 'AFTER_90_DAYS']". |
| EFS provisioned without `ProvisionedThroughputInMibps`; bursting with a value; One Zone + maxIO; Archive without IA; `KmsKeyId` without `Encrypted` | NOT caught. |
| FSx Lustre `StorageCapacity: 1000` | E3725 "1000 is less than the minimum of 1200 for 'LUSTRE' file systems". FSx Windows without AD and ONTAP MULTI_AZ_1 without `PreferredSubnetId`: NOT caught. |

Practical reading: cfn-lint reliably catches enumerations, required properties, types, naming patterns and principal shapes. It does **not** know AWS's cross-field business rules (IA >= 30 days, class ordering, replication requires versioning, EBS Iops/size ranges, EFS throughput pairing). Those rules must be taught and tested by pure-Python checkers over the rendered template.

## What the plan can rely on

- S3 object lifecycle of data: versioning enabled, delete markers (HEAD 404 with `x-amz-delete-marker`, `list_objects_v2` hides, `list_object_versions` shows `DeleteMarkers`), undelete by deleting the marker, permanent delete by version id, `null` version id for pre-versioning objects.
- Storage classes as metadata (all of STANDARD, STANDARD_IA, ONEZONE_IA, INTELLIGENT_TIERING, GLACIER_IR, GLACIER, DEEP_ARCHIVE, EXPRESS_ONEZONE, REDUCED_REDUNDANCY on put/copy), GLACIER/DEEP_ARCHIVE reads failing with `InvalidObjectState` (403), `restore_object` flipping the HEAD `Restore` header, `InvalidStorageClass` for unknown classes.
- Multipart upload: create, upload_part, list_parts, list_multipart_uploads, abort, complete, the 5 MiB minimum enforced at complete (`EntityTooSmall`), `InvalidPart`, `NoSuchUpload`.
- Presigned URLs via `generate_presigned_url` and fetching them with `requests` inside `mock_aws` (GET and PUT).
- Object tagging, head_object fields, copy_object (including the copy-onto-itself error), SSE headers per object, default-encryption (`put_bucket_encryption`) inheritance on new objects including KMS key ARN and `BucketKeyEnabled`.
- Object Lock: governance vs compliance vs legal hold enforcement on version delete, bypass header for governance, `delete_objects` per-key errors, lock-bucket creation enabling versioning.
- Bucket config round trips: PAB flags, encryption, ownership controls, CORS, website, tagging, accelerate, logging (with target bucket policy), notification (SQS events really arrive), policy string round trip, lifecycle storage of the supported fields (with the size-filter and `NewerNoncurrentVersions` drop in mind).
- Bucket-policy `Allow` to Principal `*` letting anonymous `requests` GETs through (for "public bucket" demonstrations), and a plain `Deny` (no Principal/Condition semantics) denying an action.
- EBS: create_volume for gp2/gp3/io1/io2/st1/sc1/standard with the gp3 default of 3000 Iops echoed; `modify_volume` with `describe_volumes_modifications`; attach/detach with explicit InstanceId; `VolumeInUse` on deleting attached volumes; snapshots (instant completed), encrypted copy with `KmsKeyId`, snapshot sharing attributes, create volume from snapshot; `describe_instance_types` EBS/instance-store facts. Always pass SnapshotIds when describing snapshots.
- EFS: file system creation with all modes, encryption + KMS, One Zone (AvailabilityZoneName/Id), lifecycle policies (IA, Archive, back to primary), file system policy, mount targets (one per AZ, `MountTargetConflict`, ENI created, security groups), access points, tags, `FileSystemInUse` on delete.
- FSx: create of LUSTRE/WINDOWS/ONTAP/OPENZFS file systems and the echoed deployment configuration (as existence/shape checks only); AWS Backup vault and plan; `datasync`, `transfer`, `glacier` vault basics for existence checks.
- CloudFormation: `AWS::S3::Bucket` with `BucketName`, `BucketEncryption` (algorithm + key) and `Tags`; `GetAtt` Arn/DomainName/RegionalDomainName/DualStackDomainName/WebsiteURL; `AWS::KMS::Key` (string `KeyPolicy`, Description, EnableKeyRotation) and `AWS::KMS::Alias`; `AWS::EFS::FileSystem` (full property set incl. lifecycle, backup policy, One Zone), `MountTarget`; `DeletionPolicy: Retain`; Parameters/Conditions; `update_stack` for tags/encryption.
- cfn-lint for: enum and type checks on every storage property (storage classes, SSE algorithm, ownership, EFS modes and lifecycle values, EBS volume types), required properties (noncurrent days, abort-multipart days, volume Size/SnapshotId), bucket-name rules (E1161/E3031/E3033), policy principal/effect shape, circular references, FSx Lustre capacity minimum.

## Must be modelled in pure Python instead

- Lifecycle execution (transitions, expiration, noncurrent cleanup, abort-multipart) and its validation: STANDARD_IA/ONEZONE_IA >= 30 days, transition ordering (STANDARD -> IA -> INTELLIGENT_TIERING/GLACIER_IR -> GLACIER -> DEEP_ARCHIVE), expiration after last transition, 128 KiB minimum size, 30/90/180-day minimum storage durations, early-deletion charges, `NewerNoncurrentVersions` and `ObjectSize*` filters (moto drops them).
- Suspended-versioning semantics (null version overwrite keeps older versions; delete creates a null delete marker), `BucketNotEmpty` when only versions or markers remain, MFA Delete, and the real GET-on-delete-marker response (405 `MethodNotAllowed`).
- Glacier retrieval tiers and timings (Expedited/Standard/Bulk, Instant Retrieval), restore expiry, Intelligent-Tiering access tiers, S3 Express One Zone directory buckets.
- Bucket policy evaluation with Principal, Condition (aws:SecureTransport, aws:SourceVpce, s3:x-amz-server-side-encryption, aws:PrincipalOrgID), explicit-deny-wins and cross-account logic: use `awslib.policy_eval`. Do not rely on moto's Deny for TLS-only or SSE-required exercises; it denies everything.
- Block Public Access and S3 Object Ownership/ACL enforcement, public-policy detection (`IsPublic`), default SSE-S3 on new buckets.
- Replication (SRR/CRR copy, versioning prerequisite on the destination, delete-marker replication, RTC 15-minute SLA, existing object replication, replica ownership), S3 Batch Operations, Storage Lens, Access Points policy delegation, Multi-Region Access Points routing.
- Presigned URL expiry/signature validation, Transfer Acceleration endpoint routing, requester pays.
- EBS performance and limits: gp3 Iops (3000-16000) and Throughput (125-1000 MiB/s) ranges and Iops:GiB ratios (gp3 500:1, io1 50:1, io2 1000:1), io1/io2 caps, st1/sc1 minimum 125 GiB, volume modification cooldown (6 hours), snapshot incremental storage cost, snapshot archive tier (24-72 h restore, 90-day minimum), fast snapshot restore credits, Multi-Attach rules (io1/io2 only, same AZ, Nitro, max 16 instances), cross-AZ attach rejection, encryption-by-default effect on new volumes, default KMS key, volume status checks and burst-balance credits.
- Recycle Bin retention rules, Data Lifecycle Manager policies, Storage Gateway (file/volume/tape) and Snow Family: these services are not implemented at all.
- EFS: throughput/performance-mode validation (provisioned needs a value, One Zone cannot be maxIO, Elastic vs Bursting economics), lifecycle tiering behaviour and IA size accounting, replication, backup policy via API, update_file_system, One-Zone mount-target AZ rule, NFS mount mechanics and POSIX permissions through access points.
- FSx: deployment-type rules (Lustre capacity increments, SCRATCH vs PERSISTENT, Windows AD requirement, ONTAP HA pairs and PreferredSubnetId), file system lifecycle state, throughput capacity sizing, data repository associations, backups.
- CloudFormation fidelity: properties moto drops from `AWS::S3::Bucket` (everything except name, encryption algorithm/key and tags) and `AWS::EC2::Volume` (everything except size and AZ), `AWS::S3::BucketPolicy` and `AWS::FSx::FileSystem` (skipped entirely), unsupported GetAtt names (silently drop all stack Outputs), and the KMS `KeyPolicy`/`Tags` traps. Check these properties on the rendered template (`awslib.cfn`) and with cfn-lint, never by reading them back from moto.

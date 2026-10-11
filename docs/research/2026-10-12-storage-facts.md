# Week 04 storage facts (collected 2026-10-11)

All rows below were read from official AWS pages on 2026-10-11 (the file is dated for the week-04 session on 2026-10-12). "Changed?" is "no" unless a change after 2022 is documented on the page read. Prices are illustrative (us-east-1, USD); always re-check.

URL key (base paths):
- S3UG = https://docs.aws.amazon.com/AmazonS3/latest/userguide/
- EBS = https://docs.aws.amazon.com/ebs/latest/userguide/
- EFS = https://docs.aws.amazon.com/efs/latest/ug/
- FSXW = https://docs.aws.amazon.com/fsx/latest/WindowsGuide/
- FSXL = https://docs.aws.amazon.com/fsx/latest/LustreGuide/
- FSXO = https://docs.aws.amazon.com/fsx/latest/ONTAPGuide/
- FSXZ = https://docs.aws.amazon.com/fsx/latest/OpenZFSGuide/
- SGW = https://docs.aws.amazon.com/storagegateway/latest/ (vgw/ = Volume Gateway, tgw/ = Tape Gateway)
- FGW = https://docs.aws.amazon.com/filegateway/latest/ (files3/ = S3 File Gateway, filefsxw/ = FSx File Gateway)
- CF = https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/
- ALB = https://docs.aws.amazon.com/elasticloadbalancing/latest/application/
- BKP = https://docs.aws.amazon.com/aws-backup/latest/devguide/
- DS = https://docs.aws.amazon.com/datasync/latest/userguide/
- TF = https://docs.aws.amazon.com/transfer/latest/userguide/
- SNOW = https://docs.aws.amazon.com/snowball/latest/developer-guide/
- WN = https://aws.amazon.com/about-aws/whats-new/
- S3 price file = https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonS3/current/us-east-1/index.json (publication date 2026-09-28)
- EFS price file = https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEFS/current/us-east-1/index.json
- DT price file = https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSDataTransfer/current/us-east-1/index.json
- EBS price page = https://aws.amazon.com/ebs/pricing/ (worked examples; region not always named)

## 1. S3 basics

| Fact | Value | Changed? | Source |
|---|---|---|---|
| S3 Standard design durability | 99.999999999 % (11 nines) | no | S3UG storage-class-intro.html |
| S3 Standard design availability | 99.99 % | no | S3UG storage-class-intro.html |
| S3 Standard-IA design durability / availability | 99.999999999 % / 99.9 % | no | S3UG storage-class-intro.html |
| S3 Intelligent-Tiering design durability / availability | 99.999999999 % / 99.9 % | no | S3UG storage-class-intro.html |
| S3 One Zone-IA design durability / availability | 99.999999999 % / 99.5 % | no | S3UG storage-class-intro.html |
| S3 Express One Zone design durability / availability | 99.999999999 % / 99.95 % | no | S3UG storage-class-intro.html |
| Glacier Instant Retrieval design durability / availability | 99.999999999 % / 99.9 % | no | S3UG storage-class-intro.html |
| Glacier Flexible Retrieval design durability / availability | 99.999999999 % / 99.99 % (after you restore objects) | no | S3UG storage-class-intro.html |
| Glacier Deep Archive design durability / availability | 99.999999999 % / 99.99 % (after you restore objects) | no | S3UG storage-class-intro.html |
| Reduced Redundancy Storage | Not recommended; durability 99.99 %, availability 99.99 %; "S3 Standard is more cost-effective" | no | S3UG storage-class-intro.html |
| Resilience to loss of an AZ | All classes except One Zone-IA and S3 Express One Zone are designed to survive the physical loss of an AZ | no | S3UG storage-class-intro.html |
| Max object size | 50 TB in all Regions, all storage classes (10x the previous 5 TB) | changed 2025-12-02 (was 5 TB) | WN 2025/12/amazon-s3-maximum-object-size-50-tb/ ; S3UG upload-objects.html |
| Multipart limits page object size | The multipart upload limits table still lists "Maximum object size 48.8 TiB" (stale vs the 50 TB statement; see Unconfirmed) | changed (conflicting pages) | S3UG qfacts.html |
| Single PUT limit | Up to 5 GB in one PUT operation (SDKs, REST API, CLI) | no | S3UG upload-objects.html |
| Console upload limit | Largest single file uploadable in the S3 console: 160 GB; larger files need CLI, SDK or REST API | no | S3UG upload-objects.html |
| Multipart upload size range | Multipart upload usable for objects from 5 MB to 50 TB | changed (upper end was 5 TB before 2025-12-02) | S3UG upload-objects.html |
| When to use multipart | "In general, when your object size reaches 100 MB, you should consider using multipart uploads" | no | S3UG qfacts.html |
| Part size | 5 MiB to 5 GiB; no minimum size for the last part | no | S3UG qfacts.html |
| Max parts per upload | 10,000 (part numbers 1 to 10,000) | no | S3UG qfacts.html |
| List parts / list uploads page | A list parts request and a list multipart uploads request each return at most 1,000 | no | S3UG qfacts.html |
| ListObjectsV2 page | Up to 1,000 keys per request | no | facts.md (S3 API ListObjectsV2); not re-read today |
| Transfers above 5 TB | AWS says use the S3 Transfer Manager in Java v1/v2, Python or AWS CLI SDKs, ideally with the latest AWS Common Runtime | changed 2025-12 (new guidance) | S3UG upload-objects.html |
| Console rename or property change | Creates a new object (new version if versioning is on) | no | S3UG upload-objects.html |
| Tags per object | Up to 10 tags; key up to 128 Unicode characters, value up to 255 | no | S3UG upload-objects.html |
| User-defined metadata | Up to 2 KB | no | S3UG upload-objects.html |
| Strong consistency | Strong read-after-write consistency for PUT and DELETE of objects in all Regions (new writes, overwrites, deletes); list-after-write also consistent | changed (strong consistency since Dec 2020; was eventual for overwrites/deletes) | S3UG Welcome.html |
| Strong consistency also covers | Reads on S3 Select, ACLs, object tags and object metadata (HEAD) | no | S3UG Welcome.html |
| Single-key updates | Atomic; concurrent PUTs resolved last-writer-wins by timestamp; no atomic updates across keys; no object locking for concurrent writers | no | S3UG Welcome.html |
| Bucket configurations | Eventually consistent (e.g. deleted bucket may still be listed) | no | S3UG Welcome.html |
| After enabling versioning | Wait about 15 minutes before issuing writes to the bucket (propagation) | no | S3UG Welcome.html |
| Request rate per prefix | At least 3,500 PUT/COPY/POST/DELETE and 5,500 GET/HEAD requests per second per partitioned prefix | no | S3UG optimizing-performance.html |
| Prefix count | No limit to the number of prefixes in a bucket; 10 prefixes in parallel scale reads to 55,000 per second | no | S3UG optimizing-performance.html |
| Scaling behaviour | Scales gradually; you may see 503 (Slow Down) while it scales | no | S3UG optimizing-performance.html |
| Latency | Small-object and first-byte latencies of roughly 100 to 200 ms | no | S3UG optimizing-performance.html |
| Single-instance throughput | Up to 100 Gb/s on one EC2 instance (data lake workloads) | no | S3UG optimizing-performance.html |
| Bucket name length | 3 to 63 characters | no | S3UG bucketnamingrules.html |
| Bucket name characters | Lowercase letters, numbers, periods, hyphens; begin and end with letter or number; no two adjacent periods; not formatted like an IP address | no | S3UG bucketnamingrules.html |
| Reserved prefixes | Must not start with xn--, sthree-, amzn-s3-demo- | no | S3UG bucketnamingrules.html |
| Reserved suffixes | Must not end with -s3alias, --ol-s3, .mrap, --x-s3 (directory buckets), --table-s3; -an only for account regional namespace | changed (--table-s3 and -an are newer) | S3UG bucketnamingrules.html |
| Global namespace | General purpose bucket names must be unique across all AWS accounts in all Regions of a partition; partitions: aws, aws-cn, aws-us-gov, aws-eusc | changed (aws-eusc partition is newer) | S3UG bucketnamingrules.html |
| Account regional namespace | Optional namespace only your account can use; name format prefix-accountId-region-an; created with x-amz-bucket-namespace: account-regional | changed (new feature) | S3UG bucketnamingrules.html |
| Name and Region are fixed | After creation you cannot change the bucket name or Region | no | S3UG bucketnamingrules.html |
| Name reuse after delete | After deleting a bucket another account may take the name; reuse is not guaranteed to be possible immediately or at all | no | S3UG bucketnamingrules.html |
| Periods in names | Avoid; breaks virtual-hosted-style HTTPS; Transfer Acceleration buckets cannot have periods | no | S3UG bucketnamingrules.html |
| Pre-2018 N. Virginia names | Before 2018-03-01 buckets in us-east-1 could be up to 255 characters with uppercase and underscores | no | S3UG bucketnamingrules.html |
| General purpose bucket quota | Default 10,000 buckets per account; increase through Service Quotas (view/manage from us-east-1); up to 1 million buckets on request | changed 2024-11 (was 100 default, 1,000 max) | S3UG BucketRestrictions.html ; WN 2024/11/amazon-s3-up-1-million-buckets-per-aws-account/ |
| Bucket quota side effects | First 2,000 buckets at no cost, small monthly fee above 2,000; unpaginated ListBuckets rejected when quota is above 10,000 | changed 2024-11 | search summary of WN 2024/11 page; S3UG BucketRestrictions.html |
| Bucket size and object count | No maximum bucket size and no limit on number of objects per bucket | no | S3UG BucketRestrictions.html |
| Bucket types | General purpose, directory, table, vector buckets | changed (table and vector buckets are newer) | S3UG Welcome.html |
| Directory bucket purpose | Low-latency (single AZ, S3 Express One Zone) and data residency (Local Zones, One Zone-IA) | changed (new bucket type) | S3UG Welcome.html |
| Directory bucket quota | Up to 100 directory buckets per account (adjustable); no limit on objects | no | S3UG directory-buckets-overview.html |
| Directory bucket request limits | Up to 200,000 read TPS and 100,000 write TPS per bucket; no prefix limits | no | S3UG directory-buckets-overview.html |
| Directory bucket namespace | Hierarchical directories, only delimiter is "/"; ListObjectsV2 returns unsorted results; name format base--zone-id--x-s3 | no | S3UG directory-buckets-overview.html |
| Directory bucket security | Block Public Access on, ACLs disabled (bucket owner enforced); settings cannot be modified | no | S3UG directory-buckets-overview.html |
| Inactive directory buckets | AZ directory buckets with no requests for 90 days become inactive (503 until reactivated, minutes); not applicable in Local Zones | changed (newer behaviour) | S3UG directory-buckets-overview.html |
| General purpose bucket default access | Private by default; Block Public Access on at bucket level | changed (BPA default on since 2023-04) | S3UG Welcome.html |
| Bucket policy size | Up to 20 KB | no | S3UG Welcome.html |
| Delete a bucket | Bucket must be empty (all objects, all versions, delete markers) and have no attached access points; not restorable by AWS; queued for deletion and propagates over time | no | S3UG delete-bucket.html ; S3UG empty-bucket.html |
| Incomplete multipart uploads when emptying | Docs "recommend" you also remove incomplete multipart uploads while emptying and use an AbortIncompleteMultipartUpload lifecycle rule (7 days suggested); the pages do not state that DeleteBucket itself fails because of them | no | S3UG empty-bucket.html |
| CLI delete limits | aws s3 rb --force does not delete versioned objects, so deletion fails on a versioned bucket | no | S3UG delete-bucket.html |
| Object Lambda | S3 Object Lambda still listed as a feature on the Welcome page (retired for new customers per facts.md) | no | S3UG Welcome.html |

## 2. S3 storage classes

| Fact | Value | Changed? | Source |
|---|---|---|---|
| S3 Standard | Default class; AZs: 3 or more; min storage duration none; min billable object size none; no retrieval fee | no | S3UG storage-class-intro.html |
| S3 Intelligent-Tiering | AZs 3 or more; min duration none; min billable size none; no retrieval fees; monitoring and automation fee per object | no | S3UG storage-class-intro.html |
| Intelligent-Tiering Frequent Access tier | Default tier for new or transitioned objects | no | S3UG intelligent-tiering-overview.html |
| Intelligent-Tiering Infrequent Access tier | Automatic move after 30 consecutive days without access | no | S3UG intelligent-tiering-overview.html |
| Intelligent-Tiering Archive Instant Access tier | Automatic move after 90 consecutive days without access; millisecond access | no | S3UG intelligent-tiering-overview.html |
| Intelligent-Tiering Archive Access tier | Optional (opt-in); at least 90 days, configurable up to 730 days; Glacier Flexible Retrieval performance; standard restore 3 to 5 hours | no | S3UG intelligent-tiering-overview.html |
| Intelligent-Tiering Deep Archive Access tier | Optional (opt-in); at least 180 days, configurable up to 730 days; Deep Archive performance; standard restore within 12 hours | no | S3UG intelligent-tiering-overview.html |
| Intelligent-Tiering tier count | 3 automatic tiers (Frequent, Infrequent, Archive Instant Access) plus 2 optional archive tiers = 5 | no | S3UG storage-class-intro.html ; Welcome.html |
| Intelligent-Tiering small objects | Objects under 128 KB are not monitored, not auto-tiered, and always stay in Frequent Access | no | S3UG intelligent-tiering-overview.html |
| Intelligent-Tiering return to Frequent | An object in Infrequent Access or Archive Instant Access returns to Frequent Access when accessed (GET, PUT, COPY source, restore, CompleteMultipartUpload) | no | S3UG intelligent-tiering-overview.html |
| Intelligent-Tiering non-access actions | HeadObject, ListObjects, tagging calls do not move an object back to Frequent Access | no | S3UG intelligent-tiering-overview.html |
| Intelligent-Tiering restore for archive tiers | Objects in Archive Access / Deep Archive Access must be restored with RestoreObject before reading; 1,000 restore TPS per account per Region | no | S3UG intelligent-tiering-overview.html |
| Intelligent-Tiering free retrievals | Standard retrievals free for objects in Intelligent-Tiering; bulk retrievals free for Glacier Flexible Retrieval or Intelligent-Tiering | no | S3UG restoring-objects-retrieval-options.html |
| S3 Standard-IA | AZs 3 or more; min duration 30 days; min billable size 128 KB; per-GB retrieval fee; millisecond access | no | S3UG storage-class-intro.html |
| S3 One Zone-IA | AZ: 1; min duration 30 days; min billable size 128 KB; per-GB retrieval fee; not resilient to AZ loss; millisecond access | no | S3UG storage-class-intro.html |
| One Zone-IA minimum duration (resolves "Not confirmed") | 30 days, confirmed on the comparison table and on the Standard-IA/One Zone-IA note | no | S3UG storage-class-intro.html ; https://aws.amazon.com/s3/storage-classes/ |
| IA early-delete rule | Objects deleted, overwritten or transitioned before 30 days incur normal storage plus a pro-rated charge for the remainder | no | S3UG storage-class-intro.html |
| IA small object rule | An object under 128 KB is charged as 128 KB | no | S3UG storage-class-intro.html |
| One Zone-IA recommended use | Re-creatable data, replicas for CRR, or data residency in Local Zones | no | S3UG storage-class-intro.html |
| S3 Express One Zone | AZ: 1 (chosen by you); single-digit millisecond access; design durability 11 nines; availability 99.95 % | changed (class launched 2023) | S3UG storage-class-intro.html |
| Express One Zone minimum duration (resolves "Not confirmed") | Comparison table says "None"; the storage-classes product page says 1 hour; the two official pages disagree (see Unconfirmed) | changed (conflicting pages) | S3UG storage-class-intro.html ; https://aws.amazon.com/s3/storage-classes/ |
| Express One Zone min billable size | None | no | S3UG storage-class-intro.html |
| Express One Zone request cost claim | "request costs 50 percent lower than S3 Standard" (storage-class page) vs "80 percent lower" (Welcome page); price file shows 0.00113 vs 0.005 USD per 1,000 PUT (about 77 % lower) | changed (conflicting pages) | S3UG storage-class-intro.html ; Welcome.html ; S3 price file |
| Express One Zone bucket type | Stored only in directory buckets; "up to 10x faster" data access than Standard | changed | S3UG storage-class-intro.html |
| Glacier Instant Retrieval | AZs 3 or more; min duration 90 days; min billable size 128 KB; millisecond retrieval; per-GB retrieval fee | no | S3UG storage-class-intro.html |
| Glacier Flexible Retrieval | AZs 3 or more; min duration 90 days; no min billable size but 40 KB overhead; per-GB retrieval fee; must restore before access | no | S3UG storage-class-intro.html |
| Glacier Deep Archive | AZs 3 or more; min duration 180 days; no min billable size but 40 KB overhead; per-GB retrieval fee; must restore before access | no | S3UG storage-class-intro.html |
| Archive per-object overhead | 40 KB per archived object: 32 KB at the archive rate and 8 KB at the S3 Standard rate (Flexible Retrieval and Deep Archive) | no | S3UG storage-class-intro.html ; lifecycle-transition-general-considerations.html |
| Retrieval fees by class | Yes: Standard-IA, One Zone-IA, Glacier IR, Glacier Flexible, Deep Archive (and Express: 0.0006 USD/GB). No: Standard, Intelligent-Tiering | no | S3UG storage-class-intro.html ; S3 price file |
| Glacier Flexible Expedited | Objects under 250 MB typically 1 to 5 minutes; for hundreds of objects at most | no | S3UG restoring-objects-retrieval-options.html |
| Glacier Flexible Standard | 3 to 5 hours (default tier when none is specified); with Batch Operations: minutes to 5 hours | no | S3UG restoring-objects-retrieval-options.html |
| Glacier Flexible Bulk | 5 to 12 hours | no | S3UG restoring-objects-retrieval-options.html |
| Deep Archive Standard | Within 12 hours (Batch Operations: 9 to 12 hours) | no | S3UG restoring-objects-retrieval-options.html |
| Deep Archive Bulk | Within 48 hours | no | S3UG restoring-objects-retrieval-options.html |
| Deep Archive Expedited | Not available | no | S3UG restoring-objects-retrieval-options.html |
| Provisioned capacity unit | Each unit guarantees at least 3 Expedited retrievals every 5 minutes and up to 300 MB/s; bought by the requester account; applies to Glacier Flexible Retrieval | no | S3UG restoring-objects-retrieval-options.html |
| Glacier restore request rate | 1,000 restore transactions per second; 1 to 2 PB per day per account; objects over 5 TB restore at up to 300 MB/s | no | S3UG restoring-objects-retrieval-options.html |
| Restored copy billing | While restored you pay for the archive rate plus a temporary S3 Standard copy; storage class stays Glacier | no | S3UG lifecycle-transition-general-considerations.html |
| One restore at a time | S3 processes one restore request at a time per object | no | S3UG lifecycle-transition-general-considerations.html |
| Original vault-based Glacier | Separate Amazon Glacier service; S3 Glacier storage-class objects cannot be accessed through the Glacier console or API (retired for new customers per facts.md; Glacier note not re-read) | changed (vault service status per facts.md) | S3UG storage-class-intro.html |
| Outposts storage class | S3 Outposts (OUTPOSTS) only in Outposts buckets; always SSE-S3, SSE-C optional, no SSE-KMS | no | S3UG storage-class-intro.html |
| Class selection guidance | Standard-IA for the only copy of non-re-creatable data; One Zone-IA for re-creatable data; Storage Class Analysis helps choose Standard vs Standard-IA | no | S3UG storage-class-intro.html |
| Storage class names (API values) | STANDARD, INTELLIGENT_TIERING, STANDARD_IA, ONEZONE_IA, EXPRESS_ONEZONE, GLACIER_IR, GLACIER, DEEP_ARCHIVE, REDUCED_REDUNDANCY, OUTPOSTS | no | S3UG storage-class-intro.html |

## 3. Lifecycle

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Action types | Transition (move to another class) and Expiration (delete); plus NoncurrentVersionTransition, NoncurrentVersionExpiration, AbortIncompleteMultipartUpload, ExpiredObjectDeleteMarker | no | S3UG object-lifecycle-mgmt.html ; intro-lifecycle-rules.html |
| Rules per configuration | Up to 1,000 rules per bucket; limit is not adjustable; rule ID up to 255 characters | changed (was 1,000 for a long time; "not adjustable" stated now) | S3UG intro-lifecycle-rules.html |
| One configuration per bucket | Each bucket has one lifecycle configuration | no | S3UG intro-lifecycle-rules.html |
| Waterfall from Standard | Standard to Standard-IA, Intelligent-Tiering, One Zone-IA, Glacier IR, Glacier Flexible, Deep Archive | no | S3UG lifecycle-transition-general-considerations.html |
| Waterfall from Standard-IA | To Intelligent-Tiering, One Zone-IA, Glacier IR, Glacier Flexible, Deep Archive | no | S3UG lifecycle-transition-general-considerations.html |
| Waterfall from One Zone-IA | Only to Glacier Flexible Retrieval or Deep Archive | no | S3UG lifecycle-transition-general-considerations.html |
| Waterfall from Glacier IR | Only to Glacier Flexible Retrieval or Deep Archive | no | S3UG lifecycle-transition-general-considerations.html |
| Waterfall from Glacier Flexible | Only to Deep Archive | no | S3UG lifecycle-transition-general-considerations.html |
| Waterfall from Deep Archive | None; one-way. Moving out needs restore then copy | no | S3UG lifecycle-transition-general-considerations.html |
| Intelligent-Tiering as a source | Frequent/Infrequent Access tiers to One Zone-IA, Glacier IR, Flexible, Deep Archive; Archive Instant Access to Glacier IR/Flexible/Deep Archive | changed (IT transitions documented in detail) | S3UG lifecycle-transition-general-considerations.html |
| 30-day wait before Standard-IA / One Zone-IA transition | The pages read do not state the old "objects must be 30 days old before transition to Standard-IA or One Zone-IA" rule (see Unconfirmed); the 30-day figure is documented as the minimum storage charge and as an example transition | no | S3UG storage-class-intro.html ; object-lifecycle-mgmt.html |
| 128 KB default minimum for transitions | Since September 2024 objects under 128 KB are not transitioned to any class by default | changed Sep 2024 (before: could go to Glacier Flexible/Deep Archive) | S3UG lifecycle-transition-general-considerations.html |
| Older configurations | Configurations created before Sep 2024 keep the old behaviour until you create, edit or delete rules | changed Sep 2024 | S3UG lifecycle-transition-general-considerations.html |
| Override small-object default | Add ObjectSizeGreaterThan / ObjectSizeLessThan filter, or send x-amz-transition-default-minimum-object-size in PutBucketLifecycleConfiguration | changed Sep 2024 | S3UG lifecycle-transition-general-considerations.html |
| Why 128 KB | Each transition is a billed request; for small objects request cost can outweigh storage savings | no | S3UG lifecycle-transition-general-considerations.html |
| Early transition charge | Moving out of a class with a minimum duration early incurs the remaining duration charge | no | S3UG lifecycle-transition-general-considerations.html |
| Two-step minimum rule | Quote: "You can't create a single Lifecycle rule that transitions objects from one storage class to another before the minimum storage duration period has passed." Example: Glacier IR has a 90-day minimum, so you can't transition to Glacier IR after 4 days and to Deep Archive after 20 days; "the S3 Glacier Deep Archive transition must occur after at least 94 days" (4 days in Standard + the 90-day minimum). Two separate rules work but you pay the minimum-duration charges | no | S3UG lifecycle-transition-general-considerations.html |
| Expiration on unversioned bucket | Object queued for asynchronous removal and permanently deleted | no | S3UG lifecycle-expire-general-considerations.html |
| Expiration on versioning-enabled bucket | Adds a delete marker as the current version; the old current version becomes noncurrent | no | S3UG lifecycle-expire-general-considerations.html |
| Expiration on versioning-suspended bucket | Creates a delete marker with null version ID (replaces a null-version object) | no | S3UG lifecycle-expire-general-considerations.html |
| Expiration scope | Expiration applies only to the current version | no | S3UG lifecycle-expire-general-considerations.html |
| Noncurrent version expiration | NoncurrentVersionExpiration permanently deletes noncurrent versions; cannot be recovered | no | S3UG intro-lifecycle-rules.html |
| NoncurrentDays | Days since the successor version was created; rounds up to next midnight UTC | no | S3UG intro-lifecycle-rules.html |
| NewerNoncurrentVersions | Number of newer noncurrent versions to retain, 1 to 100; both NoncurrentDays and this count must be exceeded; requires a Filter element or InvalidRequest | no | S3UG intro-lifecycle-rules.html |
| Expired object delete marker | A delete marker with zero noncurrent versions; Expiration action removes it | no | S3UG lifecycle-expire-general-considerations.html |
| ExpiredObjectDeleteMarker element | Cannot be used in a rule whose filter uses object tags | no | S3UG intro-lifecycle-rules.html |
| AbortIncompleteMultipartUpload | Sets max days a multipart upload may stay in progress, then aborts it; object expiration rules do not remove incomplete uploads; not allowed with a tag filter | no | S3UG intro-lifecycle-rules.html |
| Suggested abort window | 7 days is a good starting point | no | S3UG empty-bucket.html |
| Filters | Key prefix, object tags (logical AND with And element), object size (ObjectSizeGreaterThan / LessThan, bytes, exclusive), or combinations; one prefix per filter; empty filter = all objects | no | S3UG intro-lifecycle-rules.html |
| Different prefixes | Use separate rules per prefix | no | S3UG intro-lifecycle-rules.html |
| Day counting | Days from object creation/last modified; time = creation + N days rounded up to the next day at 00:00 UTC | no | S3UG intro-lifecycle-rules.html |
| Date-based rules | ISO 8601, midnight UTC, keep applying after the date while enabled; not creatable in console | no | S3UG intro-lifecycle-rules.html |
| Asynchronous | Lifecycle runs asynchronously; there can be a delay between eligibility and the action | no | S3UG lifecycle-expire-general-considerations.html |
| Billing at eligibility | Billing changes apply as soon as an object becomes eligible (you are not charged for expired objects) except transitions to Intelligent-Tiering, billed after the physical transition | no | S3UG object-lifecycle-mgmt.html |
| Rule propagation | Rule policy updates can take up to 15 minutes to propagate | changed (documented in newer pages) | S3UG lifecycle-expire-general-considerations.html |
| Tag-based rules | Evaluated daily; tags re-checked at execution; removing a tag does not guarantee cancellation | changed (newer behaviour note) | S3UG lifecycle-transition-general-considerations.html |
| Applies to existing objects | A new configuration applies to existing and future objects | no | S3UG object-lifecycle-mgmt.html |
| Lifecycle vs bucket policy | A bucket policy cannot prevent lifecycle deletions or transitions | no | S3UG object-lifecycle-mgmt.html |
| One action per day | An object is eligible for only one lifecycle action per day; least costly action applies; deletion beats transition, transition beats delete-marker creation | no | S3UG lifecycle-expire-general-considerations.html |
| Lifecycle and Object Lock | No action on noncurrent versions with Object Lock applied | no | S3UG lifecycle-expire-general-considerations.html |
| Lifecycle and replication | No action on current or noncurrent versions with Pending or Failed replication status | no | S3UG lifecycle-expire-general-considerations.html |
| Lifecycle and MFA delete | MFA delete cannot be used with lifecycle configurations | no | S3UG MultiFactorAuthenticationDelete.html |
| Transition retrieval charge | No data retrieval charges for lifecycle transitions; per-request ingestion charges apply | no | S3UG object-lifecycle-mgmt.html |
| Transition to Glacier Flexible/Deep Archive | Asynchronous; billed at destination rate from the date the rule is satisfied | no | S3UG lifecycle-transition-general-considerations.html |
| Expiring in a minimum-duration class | Expiring early charges the remaining minimum: 30 days (IA classes), 90 (Glacier Flexible), 180 (Deep Archive) | no | S3UG lifecycle-expire-general-considerations.html |
| Lifecycle event notifications | Lifecycle expiration and transition events exist as S3 Event Notifications event types | changed (newer feature) | S3UG EventNotifications.html |

## 4. Versioning, Object Lock, replication

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Versioning default | Disabled (unversioned) by default | no | S3UG Versioning.html |
| Versioning states | Unversioned, versioning-enabled, versioning-suspended | no | S3UG Versioning.html |
| Cannot unversion | After enabling, a bucket can never return to unversioned; it can only be suspended | no | S3UG Versioning.html |
| Existing objects | Objects before versioning have version ID null; unchanged until modified | no | S3UG Versioning.html |
| Who can enable versioning | Bucket owner, root account and authorized users | no | S3UG MultiFactorAuthenticationDelete.html |
| Versioning cost | Each version is a full object (not a diff); normal rates apply to every version | no | S3UG Versioning.html |
| Simple DELETE with versioning on | S3 adds a delete marker as the current version; nothing is deleted | no | S3UG DeleteMarker.html |
| Delete marker properties | No data, no ACL; billed by key-name size (1 to 4 bytes per character); stored in S3 Standard | no | S3UG DeleteMarker.html |
| GET after simple delete | GET without versionId returns 404 Not Found with x-amz-delete-marker: true | no | S3UG DeleteMarker.html |
| GET delete marker by versionId | Returns 405 Method Not Allowed with x-amz-delete-marker: true and Last-Modified | no | S3UG DeleteMarker.html |
| LIST after delete | ListObjects/ListObjectsV2 do not return objects whose current version is a delete marker; ListObjectVersions shows them | no | S3UG DeleteMarker.html |
| Restore a deleted object | Delete the delete marker (DELETE with its version ID) or copy a noncurrent version over | no | S3UG DeleteMarker.html ; intro-lifecycle-rules.html |
| Permanent delete | DELETE with a version ID permanently deletes that version | no | S3UG Versioning.html |
| Suspended behaviour | Existing versions stay; new writes get null version ID; expiration creates a null delete marker | no | S3UG Versioning.html ; intro-lifecycle-rules.html |
| Unversioned lifecycle gotcha | If an expiration rule exists on an unversioned bucket, add a noncurrent expiration rule after enabling versioning to keep permanent deletes | no | S3UG Versioning.html |
| MFA delete | Needs MFA to change versioning state or permanently delete a version; token = serial number + space + 6-digit code | no | S3UG MultiFactorAuthenticationDelete.html |
| MFA delete who and how | Only the bucket owner (root account) can enable it; not in the console; use CLI or API | no | S3UG MultiFactorAuthenticationDelete.html |
| Object Lock model | Write-once-read-many (WORM); works only in versioning-enabled buckets; protects individual object versions | no | S3UG object-lock.html |
| Object Lock regulation | Assessed by Cohasset Associates for SEC 17a-4, CFTC and FINRA | no | S3UG object-lock.html |
| Governance mode | Cannot overwrite/delete or alter lock unless you hold s3:BypassGovernanceRetention and send x-amz-bypass-governance-retention:true | no | S3UG object-lock.html |
| Governance mode console | Console includes the bypass header by default when you have the permission | no | S3UG object-lock.html |
| Compliance mode | No user, including root, can overwrite or delete; mode cannot change and period cannot be shortened | no | S3UG object-lock.html |
| Deleting under compliance | Only deleting the AWS account removes it before the retain-until date | no | S3UG object-lock.html |
| Retention period | Fixed retain-until-date per object version, or bucket default retention in days or years | no | S3UG object-lock.html |
| Variable retention | Event hold plus duration; S3 sets the retain-until-date when you release the hold | changed (new feature) | S3UG object-lock.html |
| Extending retention | Can extend (later date) with s3:PutObjectRetention; cannot shorten in compliance mode | no | S3UG object-lock.html |
| Legal hold | Same protection as retention but no expiry; independent of retention; needs s3:PutObjectLegalHold; any authorized user can add or remove | no | S3UG object-lock.html |
| Lock does not stop new versions | A lock protects only the specified version; new versions and delete markers can still be added | no | S3UG object-lock.html |
| Delete of locked version | Permanent DELETE with version ID returns 403; simple DELETE returns 200 and adds a delete marker | no | S3UG object-lock.html |
| Object Lock permissions | s3:BypassGovernanceRetention, Get/PutBucketObjectLockConfiguration, Get/PutObjectLegalHold, Get/PutObjectRetention | no | S3UG object-lock.html |
| Retention limit condition key | s3:object-lock-remaining-retention-days restricts allowed retention periods in a bucket policy | no | S3UG object-lock.html |
| Replication types | Live replication (new and updated objects) and on-demand replication (S3 Batch Replication) | changed (on-demand framing) | S3UG replication.html |
| CRR / SRR | CRR copies between buckets in different Regions; SRR within the same Region; accounts may differ | no | S3UG replication.html |
| Replication is asynchronous | Automatic, asynchronous copying; multiple destination buckets supported | no | S3UG replication.html |
| Versioning required | Quote: "Both source and destination buckets must have versioning enabled." Disabling versioning on the source is refused until replication is removed; disabling it on the destination makes replication fail (status FAILED) | no | S3UG replication-requirements.html |
| Replication permissions | S3 must have permission to replicate on your behalf (IAM role); if the source has Object Lock the destination must too, and the role needs s3:GetObjectRetention and s3:GetObjectLegalHold (s3:Get* satisfies it) | changed (Object Lock permissions are newer) | S3UG replication-requirements.html |
| Cross-account replication | Destination bucket owner must grant the source owner permission with a bucket policy; destination cannot be Requester Pays | no | S3UG replication-requirements.html |
| Existing objects | Live replication does not replicate objects that existed before setup; use S3 Batch Replication | no | S3UG replication.html |
| Batch Replication also covers | Previously failed objects, already replicated objects to new destinations, and replicas of replicas | no | S3UG replication.html |
| Replicas of replicas | Objects that are replicas from another rule are not replicated onward (no chaining) except via Batch Replication | no | S3UG replication-what-is-isnot-replicated.html |
| Delete markers | With the current (Filter) rule schema, delete markers are NOT replicated by default; optional delete marker replication on non-tag-based rules; V1 (no Filter) replicates user-initiated markers | no | S3UG replication-what-is-isnot-replicated.html |
| Version-specific deletes | A DELETE with version ID is not replicated, to protect against malicious deletes | no | S3UG replication-what-is-isnot-replicated.html |
| Lifecycle actions | Not replicated; use the same lifecycle configuration on both buckets | no | S3UG replication-what-is-isnot-replicated.html |
| Archived objects | Glacier Flexible, Deep Archive and Intelligent-Tiering archive tiers cannot be replicated until restored and copied | no | S3UG replication-what-is-isnot-replicated.html |
| Bucket-level subresources | Changes to lifecycle or notification configuration are not replicated | no | S3UG replication-what-is-isnot-replicated.html |
| What is replicated | New objects after configuration, metadata, tags, ACL updates, Object Lock retention info; SSE-S3, SSE-KMS and SSE-C objects by default | changed (annotations are newer) | S3UG replication-what-is-isnot-replicated.html |
| Replica storage class | Can replicate into a different class (e.g. Glacier) and change replica ownership (owner override) | no | S3UG replication.html |
| Replication Time Control (RTC) | Replicates 99.99 % of new objects within 15 minutes, SLA-backed; the workload table on the same page says 99.9 % (see Unconfirmed) | no | S3UG replication.html |
| RTC scope | Does not apply to Batch Replication | no | S3UG replication.html |
| Without RTC | SRR/CRR typically 24 to 48 hours, not SLA-backed (per workload table) | no | S3UG replication.html |
| Two-way replication | Bi-directional rules with replica modification sync replicate metadata changes (ACLs, tags, Object Lock) back; used with Multi-Region Access Point failover | no | S3UG replication.html |

## 5. Security

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Block Public Access settings | Four: BlockPublicAcls, IgnorePublicAcls, BlockPublicPolicy, RestrictPublicBuckets | no | S3UG access-control-block-public-access.html |
| BPA levels | Access point, bucket, account, and organization (AWS Organizations policy: all four together, all or none) | changed (organization level and access-point level are newer) | S3UG access-control-block-public-access.html |
| BPA precedence | Most restrictive combination across levels applies | no | S3UG access-control-block-public-access.html |
| BlockPublicAcls | PutBucketAcl / PutObjectAcl / PutObject with a public ACL fail; existing ACLs unchanged | no | S3UG access-control-block-public-access.html |
| IgnorePublicAcls | S3 ignores all public ACLs but still accepts PutObject with public ACL | no | S3UG access-control-block-public-access.html |
| BlockPublicPolicy | Rejects PutBucketPolicy (and access point policy) that allows public access | no | S3UG access-control-block-public-access.html |
| RestrictPublicBuckets | A bucket with a public policy is limited to AWS service principals and authorized users in the owner account | no | S3UG access-control-block-public-access.html |
| BPA defaults for new buckets | All four settings on at bucket level for new buckets | changed 2023-04 (facts.md date; page: default on) | S3UG Welcome.html ; facts.md |
| BPA existing policy | Does not alter existing policies/ACLs; turning BPA off makes public ones effective again | no | S3UG access-control-block-public-access.html |
| BPA access point | Access point BPA settings can only be set when creating the access point | no | S3UG access-control-block-public-access.html |
| Object Ownership default | Bucket owner enforced: ACLs disabled, bucket owner owns all objects | changed 2023-04 | S3UG Welcome.html |
| ACL guidance | AWS recommends keeping ACLs disabled and using bucket/access point/IAM policies | no | S3UG Welcome.html |
| Default encryption | All new object uploads encrypted with SSE-S3 (AES-256) automatically, at no cost, from 2023-01-05; cannot be turned off | changed 2023-01-05 | S3UG bucket-encryption.html |
| Default encryption for existing buckets | Buckets without default encryption were switched to SSE-S3; buckets already on SSE-S3 or SSE-KMS unchanged | changed 2023-01 | S3UG bucket-encryption.html |
| Existing unencrypted objects | Not re-encrypted automatically; use Batch Operations Copy or CopyObject | no | S3UG bucket-encryption.html |
| Encryption options | SSE-S3, SSE-KMS, DSSE-KMS (dual-layer), SSE-C | changed (DSSE-KMS is newer) | S3UG bucket-encryption.html |
| SSE-KMS key when none given | Uses the AWS managed key aws/s3 | no | S3UG bucket-encryption.html |
| SSE-KMS cross-account | Needs a customer managed key (aws/s3 cannot be shared); use full key ARN not alias | no | S3UG bucket-encryption.html |
| SSE-KMS key types | Symmetric KMS keys only; same Region as the bucket | no | S3UG upload-objects.html |
| S3 Bucket Keys | Bucket-level key reduces KMS request costs by up to 99 percent | no | S3UG bucket-key.html |
| Bucket Key scope | Applies to new objects only (CopyObject to apply to existing); shared only for objects with the same KMS key; encryption context becomes bucket ARN | no | S3UG bucket-key.html |
| Bucket Key not supported | Not supported with DSSE-KMS | changed (DSSE-KMS newer) | S3UG bucket-key.html |
| Server access log bucket | Must use SSE-S3, not SSE-KMS | no | S3UG bucket-encryption.html |
| SSE-C rules | Keys supplied on every request; S3 never stores the key; HTTPS required; not supported in the console | no | S3UG ServerSideEncryptionCustomerKeys.html |
| SSE-C default change | Starting April 2026 SSE-C is disabled by default for all new general purpose buckets and for existing buckets in accounts with no SSE-C objects; enable with BlockedEncryptionTypes = NONE via PutBucketEncryption; blocked writes return 403 AccessDenied | changed April 2026 | S3UG ServerSideEncryptionCustomerKeys.html |
| bucket policy: HTTPS only | Deny with Condition Bool aws:SecureTransport = "false" | no | S3UG example-bucket-policies.html |
| bucket policy: VPC endpoint | aws:SourceVpce (and aws:SourceVpc) with a fixed value keeps a policy non-public and restricts access to a VPC endpoint | no | S3UG access-control-block-public-access.html |
| bucket policy: require encryption | Condition key s3:x-amz-server-side-encryption (and ...-aws-kms-key-id) to enforce encrypted uploads (key name not re-checked in the long policy page; with default SSE-S3 now on, such denies are mainly for forcing SSE-KMS) | changed (SSE-S3 default makes old "deny unencrypted" policies less necessary) | S3UG bucket-encryption.html ; example-bucket-policies.html |
| Non-public policy conditions | aws:PrincipalOrgID, aws:SourceIp CIDR, aws:SourceArn, aws:SourceVpc, aws:SourceVpce, aws:SourceOwner, aws:SourceAccount, s3:DataAccessPointArn | no | S3UG access-control-block-public-access.html |
| Presigned URL expiry (SigV4) | Console: 1 minute to 12 hours; CLI/SDK: up to 7 days with an IAM user's long-term credentials | no | S3UG using-presigned-url.html |
| Presigned URL with temporary credentials | Expires when the credential expires (IAM role session, STS, EC2 instance profile about 6 hours) even if a longer time was requested | no | S3UG using-presigned-url.html |
| Presigned URL permissions | Carries the permissions of the principal that signed it; works for GET and PUT; can be reused until expiry; checked at request time | no | S3UG using-presigned-url.html |
| Presigned URL age condition | s3:signatureAge in a bucket policy can deny signatures older than a set time | no | S3UG using-presigned-url.html |
| Access points | Named network endpoints with their own policy (up to 20 KB); thousands per Region per account; can restrict to a VPC; attach to general purpose or directory buckets or FSx for OpenZFS volumes | changed (directory buckets and FSx OpenZFS targets are newer) | S3UG Welcome.html ; access-grants.html |
| CloudFront OAC | Origin Access Control is the recommended way to restrict an S3 origin; supports all Regions including opt-in Regions, SSE-KMS, and PUT/DELETE; policy principal cloudfront.amazonaws.com with AWS:SourceArn of the distribution | changed (OAC is newer than 2022 OAI guidance) | CF private-content-restricting-access-to-s3.html |
| CloudFront OAI | Legacy; no SSE-KMS, no all-Regions support, no PUT/POST/DELETE workarounds | changed (legacy) | CF private-content-restricting-access-to-s3.html |
| OAC and website endpoints | An S3 website endpoint origin cannot use OAC or OAI (use a custom origin) | no | CF private-content-restricting-access-to-s3.html |
| OAC and Object Ownership | OAC requires bucket owner enforced (the default) unless bucket owner preferred is chosen to use ACLs | no | CF private-content-restricting-access-to-s3.html |
| S3 Access Grants | Maps IAM principals or corporate-directory users/groups (through IAM Identity Center trusted identity propagation) to S3 prefixes, buckets or objects with read/write/read-write grants | changed (feature newer than 2022) | S3UG access-grants.html |
| IAM and bucket policy size | Bucket policy up to 20 KB; IAM policy size about 5 KB per the Access Grants page | no | S3UG access-grants.html |
| ALB access log bucket policy: principal | Recommended policy uses service principal logdelivery.elasticloadbalancing.amazonaws.com | changed (service principal replaced the per-Region account ID for Regions available after August 2022) | ALB enable-access-logging.html |
| ALB legacy policy: us-east-1 | Regions available before August 2022 can still use the legacy policy with the Elastic Load Balancing account ID; US East (N. Virginia) is 127311923021 | changed (legacy, "recommend that you replace it") | ALB enable-access-logging.html |
| ALB log policy action | s3:PutObject | no | ALB enable-access-logging.html |
| ALB log policy resource | arn:aws:s3:::bucket/prefix/AWSLogs/account-id/* (without a prefix: bucket/AWSLogs/account-id/*); always include the account ID, no wildcard in it | no | ALB enable-access-logging.html |
| ALB log bucket Region | Bucket must be in the same Region as the load balancer; may be owned by a different account | no | ALB enable-access-logging.html |
| ALB log bucket encryption | Only SSE-S3 (Amazon S3-managed keys) is supported; SSE-KMS causes access denied | no | ALB enable-access-logging.html |
| ALB log delivery interval | A log file per load balancer node every 5 minutes; delivery is eventually consistent and best effort | no | ALB load-balancer-access-logs.html |
| ALB log format | Compressed .log.gz files under AWSLogs/account-id/elasticloadbalancing/region/yyyy/mm/dd/ | no | ALB load-balancer-access-logs.html |
| ALB log cost | Pay only S3 storage; no charge for the delivery bandwidth | no | ALB load-balancer-access-logs.html |
| ALB log policy hardening | aws:SourceArn (loadbalancer ARN) and aws:SourceOrgId conditions recommended; Outposts uses logdelivery.elb.amazonaws.com with bucket-owner-full-control | changed (newer recommendations) | ALB enable-access-logging.html |
| ALB log extras | Newer ALB logging to CloudWatch Logs, Firehose or S3 is available besides legacy access logs | changed (new) | ALB load-balancer-access-logs.html |

## 6. Performance and transfer

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Parallelization | More prefixes and parallel requests raise throughput linearly | no | S3UG optimizing-performance.html |
| Multipart benefits | Parts upload independently, in any order and in parallel | no | S3UG upload-objects.html |
| Byte-range fetches | Parallel GETs of byte ranges (not re-read; guideline page not fetched) | no | S3UG optimizing-performance-guidelines.html (not fetched) |
| Transfer Acceleration | Bucket-level feature that uses CloudFront edge locations; data routed to S3 over an optimized network path | no | S3UG transfer-acceleration.html |
| Transfer Acceleration requirements | Virtual-hosted-style requests only; bucket name DNS-compliant without periods; enabled on the bucket | no | S3UG transfer-acceleration.html |
| Transfer Acceleration endpoint | bucket.s3-accelerate.amazonaws.com (dual-stack: s3-accelerate.dualstack.amazonaws.com) | no | S3UG transfer-acceleration.html |
| Transfer Acceleration activation | Can take up to 20 minutes after enabling before speed improves | no | S3UG transfer-acceleration.html |
| Transfer Acceleration cost | Extra data transfer charges might apply | no | S3UG transfer-acceleration.html |
| Transfer Acceleration owner | Only the bucket owner (or delegated) can set it; permissions s3:PutAccelerateConfiguration / GetAccelerateConfiguration | no | S3UG transfer-acceleration.html |
| Transfer Acceleration use | Customers upload from around the world to a central bucket or move GBs to TBs across continents | no | S3UG transfer-acceleration.html |
| S3 Select status | "Amazon S3 Select is no longer available to new customers. Existing customers can continue to use the feature as usual." | changed (closed to new customers; facts.md date 2024-07-25) | S3UG selecting-content-from-objects.html |
| S3 Select limits | One object per request; files up to 5 TB; SQL expression up to 256 KB; record up to 1 MB; not for Glacier Flexible/Deep Archive/RRS/IT archive tiers | no | S3UG selecting-content-from-objects.html |
| S3 Batch Operations | One operation on billions of objects with a manifest (S3 Inventory report or CSV) and completion report | no | S3UG batch-ops.html |
| Batch Operations operations | Copy, tag, ACL, Object Lock, restore from Glacier, invoke Lambda, update encryption, Batch Replication | changed (update encryption, Batch Replication are newer) | S3UG batch-ops.html |
| Batch Operations scale | 4 billion objects per job by default; up to 20 billion for some operations; 6 active jobs per account | changed (limits stated now) | S3UG batch-ops.html |
| Batch Operations cost | Billed for creating jobs, including cancelled ones | no | S3UG batch-ops.html |
| Event notification destinations | SNS topics, SQS queues, Lambda functions, Amazon EventBridge | no | S3UG EventNotifications.html |
| Event delivery | At least once; typically seconds, sometimes a minute or longer | no | S3UG EventNotifications.html |
| SQS FIFO | FIFO queues are not supported as a destination; use EventBridge | no | S3UG EventNotifications.html |
| Event types | Object created, removed, restore, RRS lost, replication, lifecycle expiration and transition, Intelligent-Tiering archival, tagging, ACL put, retention | changed (annotation/retention events newer) | S3UG EventNotifications.html |
| Loop warning | A notification that writes to the same bucket can cause an execution loop | no | S3UG EventNotifications.html |
| Storage Lens | 60+ usage and activity metrics, dashboards per org/account/Region/bucket/prefix | no | S3UG Welcome.html |
| Storage Class Analysis | Analyzes access patterns to recommend moving data | no | S3UG Welcome.html |
| S3 Inventory | Reports of objects and metadata (replication, encryption status) | no | S3UG Welcome.html |
| Requester Pays | Exam guide names Requester Pays buckets (4.1); the page was not fetched in this pass | no | exam_guide.md task 4.1 |

## 7. EBS

| Fact | Value | Changed? | Source |
|---|---|---|---|
| EBS scope | A volume lives in one Availability Zone and attaches to instances in that AZ | no | EBS ebs-volumes-multi.html (same-AZ requirement for Multi-Attach); general rule not re-read |
| gp3 size | 1 GiB to 64 TiB | changed 2025-09 (was 16 TiB) | EBS ebs-volume-types.html ; WN 2025/09/amazon-ebs-size-provisioned-performance-gp3-volumes/ |
| gp3 baseline | 3,000 IOPS and 125 MiB/s included in the storage price at any size | no | EBS general-purpose.html |
| gp3 max IOPS | 80,000 IOPS (was 16,000) | changed 2025-09 | EBS general-purpose.html ; WN 2025/09 page |
| gp3 max throughput | 2,000 MiB/s (was 1,000) | changed 2025-09 | EBS general-purpose.html ; WN 2025/09 page |
| gp3 IOPS ratio | Provision up to 500 IOPS per GiB; max IOPS needs 160 GiB or larger | no | EBS general-purpose.html |
| gp3 throughput ratio | Up to 0.25 MiB/s per provisioned IOPS; max throughput at 8,000 IOPS or more and 16 GiB or larger | no | EBS general-purpose.html |
| gp3 vs gp2 cost | gp3 is 20 percent lower price per GiB than gp2 | no | EBS general-purpose.html |
| gp3 burst | None; sustains full provisioned IOPS and throughput indefinitely | no | EBS general-purpose.html |
| gp3 durability | 99.8 to 99.9 % (AFR at most 0.2 %); provisioned performance delivered 99 % of the time | no | EBS general-purpose.html |
| gp3 on Outposts | Up to 16 TiB, 16,000 IOPS, 1,000 MiB/s | no | EBS general-purpose.html |
| gp3 console default | gp3 is the default volume type selection in the console | changed (default moved from gp2) | EBS general-purpose.html |
| gp2 baseline | 3 IOPS per GiB, minimum 100 IOPS, maximum 16,000 IOPS (reached at 5,334 GiB) | no | EBS general-purpose.html |
| gp2 size | 1 GiB to 16 TiB | no | EBS general-purpose.html |
| gp2 burst | Volumes under 1 TiB can burst to 3,000 IOPS using I/O credits | no | EBS general-purpose.html |
| gp2 I/O credit bucket | 5.4 million credits at start and maximum; earned at 3 credits per GiB per second below baseline; 5.4 million sustains 3,000 IOPS for at least 30 minutes | no | EBS general-purpose.html |
| gp2 throughput | 128 to 250 MiB/s depending on size (170 GiB and smaller: 128; 334 GiB and larger: 250) | no | EBS general-purpose.html |
| gp2 33.33 GiB | Volumes 33.33 GiB and smaller get the 100 IOPS minimum | no | EBS general-purpose.html |
| BurstBalance | CloudWatch metric showing percent of gp2 I/O credits remaining | no | EBS general-purpose.html |
| io2 Block Express size | 4 GiB to 64 TiB | no | EBS ebs-volume-types.html |
| io2 Block Express IOPS | Up to 256,000 IOPS (Nitro instances), ratio 1,000 IOPS per GiB, max at 256 GiB or larger; non-Nitro instances reach at most 32,000 | no | EBS provisioned-iops.html |
| io2 Block Express throughput | Up to 4,000 MiB/s; 0.256 MiB/s per provisioned IOPS; maximum at 16,000 IOPS or more | no | EBS provisioned-iops.html |
| io2 durability | 99.999 % (AFR at most 0.001 %), one failure per 100,000 volumes per year | no | EBS provisioned-iops.html |
| io2 latency | Average under 500 microseconds for 16 KiB I/O; sub-millisecond | no | EBS provisioned-iops.html |
| io2 Block Express universal | As of 2025-04-30 all new and existing io2 volumes are io2 Block Express | changed 2025-04-30 | EBS provisioned-iops.html |
| io2 use case | More than 80,000 IOPS or 2,000 MiB/s, or sub-millisecond latency (Oracle, SAP HANA, SQL Server) | no | EBS ebs-volume-types.html |
| io1 | 4 GiB to 16 TiB; 100 to 64,000 IOPS; ratio 50 IOPS per GiB; up to 1,000 MiB/s; 99.8 to 99.9 % durability | no | EBS provisioned-iops.html |
| io1 max IOPS size | Maximum 64,000 IOPS needs 1,280 GiB; 64,000 only on Nitro (32,000 otherwise) | no | EBS provisioned-iops.html |
| io1/io2 delivered performance | Provisioned IOPS delivered 99.9 % of the time | no | EBS provisioned-iops.html |
| st1 (Throughput Optimized HDD) | 125 GiB to 16 TiB; max 500 IOPS (1 MiB) and 500 MiB/s; not bootable; no Multi-Attach | no | EBS ebs-volume-types.html |
| sc1 (Cold HDD) | 125 GiB to 16 TiB; max 250 IOPS and 250 MiB/s; not bootable; no Multi-Attach; lowest cost | no | EBS ebs-volume-types.html |
| st1 / sc1 use cases | st1: big data, data warehouses, log processing; sc1: infrequently accessed, lowest cost | no | EBS ebs-volume-types.html |
| Magnetic (standard) | Previous generation; 1 GiB to 1 TiB; 40 to 200 IOPS; 40 to 90 MiB/s; bootable | no | EBS ebs-volume-types.html |
| Bootable types | gp2, gp3, io1, io2, magnetic; not st1 or sc1 | no | EBS ebs-volume-types.html |
| Root volume type change | A root volume of SSD or magnetic type cannot be modified to st1 or sc1 | no | EBS ebs-modify-volume.html |
| Multi-Attach types | Only io1 and io2 (Provisioned IOPS SSD); gp2/gp3/st1/sc1 not supported | no | EBS ebs-volumes-multi.html |
| Multi-Attach scope | Same Availability Zone only; up to 16 Nitro instances | no | EBS ebs-volumes-multi.html |
| Multi-Attach file system | XFS/ext4 are not cluster-aware; use a clustered file system; app must order writes | no | EBS ebs-volumes-multi.html |
| Multi-Attach OS | Linux supports io1 and io2; Windows supports io2 only | no | EBS ebs-volumes-multi.html |
| Multi-Attach limits | Cannot be a boot volume; cannot be enabled at launch via console/RunInstances; no extra charge | no | EBS ebs-volumes-multi.html |
| Multi-Attach change | Enable/disable on existing volume allowed when detached; io1 to io2 conversion allowed | changed (modification support is newer) | EBS ebs-volumes-multi.html |
| NVMe reservations | I/O fencing supported on io1/io2 | changed (new) | EBS ebs-volumes-multi.html |
| Snapshots are incremental | Only blocks changed since the last snapshot are saved | no | EBS ebs-snapshots.html |
| Snapshot storage | Stored in S3 buckets you cannot access directly; replicated across all AZs in the Region | no | EBS ebs-snapshots.html |
| Deleting a snapshot | May not reduce cost because data referenced by other snapshots is kept | no | EBS ebs-snapshots.html |
| Snapshot is not automatic | AWS does not back up EBS volumes automatically; use snapshots, Data Lifecycle Manager or AWS Backup | no | EBS ebs-snapshots.html |
| Fast Snapshot Restore | Volumes created from the snapshot are fully initialized at creation; enabled per snapshot per AZ | no | EBS ebs-fast-snapshot-restore.html |
| FSR limits | Snapshots of 16 TiB or less; up to 5 snapshots per Region; not on Outposts/Local Zones/Wavelength | no | EBS ebs-fast-snapshot-restore.html |
| FSR billing | Per minute per snapshot per AZ, minimum one hour; example 0.75 USD per hour | no | EBS ebs-fast-snapshot-restore.html |
| FSR on copy | A copy of an FSR-enabled snapshot is not automatically FSR-enabled | no | EBS ebs-fast-snapshot-restore.html |
| Snapshot Archive tier | Up to 75 percent lower storage cost for snapshots kept 90 days or longer; stored as full snapshots | no | EBS snapshot-archive.html |
| Archive minimum | Minimum archive period 90 days; deleting or restoring early bills remaining days | no | EBS snapshot-archive-considerations.html |
| Archive restore time | Up to 72 hours to restore to the standard tier | no | EBS snapshot-archive-considerations.html |
| Archive restrictions | Cannot create a volume, share or copy an archived snapshot; must restore first; FSR disabled on archive | no | EBS snapshot-archive-considerations.html |
| Archive quotas | 25 archived snapshots per volume; 25 concurrent archives; 5 concurrent restores per account | no | EBS snapshot-archive.html |
| Archive best use | Monthly, quarterly or yearly snapshots; daily incrementals can cost more than standard | no | EBS snapshot-archive-considerations.html |
| Recycle Bin | Recovers deleted EBS volumes, snapshots and EBS-backed AMIs for a retention period you set | changed (volume support is newer) | EBS recycle-bin.html |
| Recycle Bin quotas | 250 retention rules per Region; 50 tag key/value pairs per rule | no | EBS recycle-bin.html |
| Recycle Bin cost | No extra charge for rules; resources in the bin billed at the normal rate (archived snapshots at archive rate) | no | EBS recycle-bin.html |
| EBS encryption | Uses AWS KMS keys; encrypts data at rest and in transit between instance and volume; all instance types support it | no | EBS ebs-encryption.html |
| Encryption by default | Region-specific account setting; cannot disable per volume/snapshot in that Region once on; no effect on existing resources; default key aws/ebs | no | EBS encryption-by-default.html |
| Encrypt an unencrypted volume | Cannot encrypt in place; snapshot the volume, then copy/restore the snapshot with encryption | no | EBS ebs-encryption.html |
| Remove encryption | Encrypted volume or snapshot can never be made unencrypted; restores and copies stay encrypted | no | EBS ebs-encryption.html |
| Snapshot sharing | Public snapshots of encrypted volumes are not supported; can share with specific accounts | no | EBS ebs-encryption.html |
| Change key | KMS key of an existing volume/snapshot cannot change; choose another key on snapshot copy (full copy, extra storage) | no | EBS encryption-by-default.html |
| Elastic Volumes | Change size, type, IOPS, throughput of an in-use volume without detaching or stopping | no | EBS ebs-modify-volume.html |
| Elastic Volumes frequency | Up to four modifications in a rolling 24 hours, and each must reach completed before the next | changed (older docs said wait 6 hours) | EBS ebs-modify-volume.html |
| Elastic Volumes limits | Size can only increase; cannot cancel; no charge for the modify itself | no | EBS ebs-modify-volume.html |
| Elastic Volumes time | Best effort; a 1 TiB volume can take up to six hours | no | EBS ebs-modify-volume.html |
| gp2 to gp3 migration | Modify in place; unspecified performance becomes the higher of equivalent gp2 or gp3 baseline | no | EBS ebs-modify-volume.html |
| Data Lifecycle Manager | Automates creation, retention, deletion of EBS snapshots and EBS-backed AMIs; no additional cost; cross-Region/account copy for DR | no | EBS snapshot-lifecycle.html |
| DLM quotas | 100 custom lifecycle policies per Region; 1 default policy for snapshots and 1 for AMIs per Region; 45 tags | changed (default policies are newer) | EBS snapshot-lifecycle.html |
| DLM limits | Cannot manage snapshots/AMIs created by other means; not instance-store AMIs | no | EBS snapshot-lifecycle.html |

## 8. EFS

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Protocol | NFSv4.1 and NFSv4.0 (no NFSv2/v3) | no | EFS whatisefs.html ; limits.html |
| OS support | Linux; Microsoft Windows-based EC2 instances are not supported | no | EFS whatisefs.html |
| Serverless elastic | Grows and shrinks automatically to petabytes; no capacity provisioning | no | EFS whatisefs.html |
| Compute that can mount | EC2, ECS, EKS, Lambda, Fargate; on-premises over Direct Connect or VPN | no | EFS whatisefs.html ; limits.html |
| Regional file system | Data across multiple AZs (3 or more); durability 11 nines; availability 99.99 %; recommended | no | EFS features.html |
| One Zone file system | One AZ; durability 11 nines; availability 99.99 % in the file system table (99.9 % in the storage class table); not resilient to AZ loss; auto-backup with AWS Backup | no | EFS features.html |
| Mount targets | One mount target per AZ per file system; 1,400 mount targets per VPC; 5 security groups per mount target; 1 VPC per file system | no | EFS limits.html |
| Mount target security | Security groups are applied at mount targets | no | EFS efs-access-points.html |
| Storage class Standard | SSD; sub-millisecond reads (about 1 ms first-byte read, 2.7 ms write); lowest latency | no | EFS performance.html ; features.html |
| Storage class Infrequent Access (IA) | Data accessed only a few times a quarter; first byte tens of milliseconds; minimum billing 128 KiB per file; no minimum duration | no | EFS features.html |
| Storage class Archive | Data accessed a few times a year or less; tens of ms; minimum billing 128 KiB per file; 90-day minimum storage duration; Regional only | changed (Archive class is newer than 2022) | EFS features.html |
| Archive requires Elastic | Archive needs Elastic throughput; if a policy transitions to Archive you cannot switch to Bursting or Provisioned | changed | EFS features.html |
| One Zone classes | One Zone and One Zone-IA exist for One Zone file systems | no | EFS storage-classes.html |
| Lifecycle to IA thresholds | 1, 7, 14, 30, 60, 90, 180, 270, 365 days since last access | no | EFS storage-classes.html |
| Lifecycle back to Standard | Files can return to Standard on access (TransitionToPrimaryStorageClass AFTER_1_ACCESS) | no | EFS storage-classes.html |
| Small files | Since 2023-11-26 lifecycle policies can tier files under 128 KiB to IA; IA/Archive bill at least 128 KiB per file | changed 2023-11-26 | EFS features.html |
| Data access charges | Per-GB charge when reading IA/Archive or when data transitions between classes; not charged when AWS Backup backs up | no | EFS features.html |
| Throughput modes | Elastic (recommended default), Provisioned, Bursting | changed (Elastic is newer) | EFS performance.html |
| Elastic throughput | Scales automatically; best for spiky or unpredictable workloads (average-to-peak 5 % or less); pay per data read/written; no burst credits | changed | EFS performance.html |
| Provisioned throughput | You set throughput independent of size; use when average-to-peak is 5 % or more; billed above included baseline; after raising or switching, 24-hour restrictions on lowering or switching back | no | EFS performance.html |
| Bursting throughput | Baseline 50 KiB/s per GiB of Standard storage (50 MiB/s per TiB), burst to 100 MiB/s per TiB (minimum 100 MiB/s); credit cap 2.1 TiB; large file systems burst up to 12 hours a day | no | EFS performance.html |
| Elastic max throughput | Regional default 60 GiB/s read and 5 GiB/s write in major Regions (20 and 1 elsewhere); per-client 1,500 MiB/s with efs-utils 2.0+ | changed (numbers are newer) | EFS limits.html ; performance.html |
| Elastic IOPS | Up to 250,000 read IOPS (frequently accessed), 90,000 (infrequently accessed), 50,000 write by default; page table shows up to 2.5 million read | changed | EFS limits.html ; performance.html |
| Performance modes | General Purpose (default, lowest latency, recommended for all) and Max I/O (previous generation, higher latency) | changed (Max I/O now legacy) | EFS performance.html |
| Max I/O status | Not supported for One Zone file systems or Elastic throughput; AWS recommends General Purpose for all file systems | changed | EFS performance.html |
| Latency | About 1 ms read and 2.7 ms write (Regional); about 1.6 ms write on One Zone | no | EFS performance.html |
| Consistency | Close-to-open consistency; advisory locking only; up to 512 locks per file | no | EFS features.html |
| Max file size | 47.9 TiB per file | no | EFS limits.html |
| Connections and access points | 25,000 connections per file system; 10,000 access points per file system | no | EFS limits.html |
| File systems per Region | 1,000 per account per Region (adjustable) | no | EFS limits.html |
| Access points | Application-specific entry points that enforce a POSIX user/group identity and a root directory; combine with IAM policies; need a mount target | no | EFS efs-access-points.html |
| Encryption | At rest (enabled at creation, KMS) and in transit (enabled at mount via TLS); NFS client access also controlled by IAM and security groups | no | EFS whatisefs.html |
| IAM for NFS clients | IAM authorization for NFS clients available | changed (newer) | EFS features.html |
| Replication | Replicate a file system to another Region; RPO and RTO in minutes | changed (newer) | EFS features.html |
| EFS vs EBS | EFS: shared, multi-AZ, Linux NFS, elastic; EBS: one AZ, block, one instance (except Multi-Attach) | no | EFS whatisefs.html ; EBS ebs-volumes-multi.html |
| EFS price vs EBS gp3 | EFS Standard 0.30 USD per GB-month vs gp3 0.08 (about 3.75x, derived from price rows in section 12) | no | EFS price file ; EBS price page |

## 9. FSx

| Fact | Value | Changed? | Source |
|---|---|---|---|
| FSx for Windows File Server | Fully managed Windows Server file servers on a native Windows file system | no | FSXW what-is.html |
| FSx Windows protocol | SMB 2.0 to 3.1.1; accessible from Windows (Server 2008/Win 7 and later) and current Linux | no | FSXW what-is.html |
| FSx Windows AD integration | Works with Microsoft Active Directory for authentication and access control; join the file system to AD at creation (AWS Managed Microsoft AD or self-managed) | no | FSXW what-is.html |
| FSx Windows availability | Single-AZ and Multi-AZ (standby file server in a second AZ with failover) | no | FSXW what-is.html |
| FSx Windows features | NTFS ACLs, VSS shadow copies, DFS-based access via namespaces (DFS not re-read on the page), automatic daily backups on by default, DNS aliases | no | FSXW what-is.html |
| FSx Windows storage | SSD or HDD; storage, SSD IOPS and throughput provisioned independently | no | FSXW what-is.html |
| FSx Windows encryption | At rest with KMS; in transit with SMB Kerberos session keys | no | FSXW what-is.html |
| FSx Windows answer | Lift-and-shift Windows apps, home directories, SMB shares, AD-integrated | no | FSXW what-is.html |
| FSx for Lustre | Managed Lustre for ML, HPC, video processing, financial modeling; sub-millisecond latency, up to multiple TB/s throughput and millions of IOPS | no | FSXL what-is.html |
| FSx Lustre OS | POSIX-compliant; Linux clients (AL2023/AL2, RHEL, CentOS, Ubuntu, SUSE) | no | FSXL what-is.html |
| FSx Lustre scratch | Temporary storage and shorter-term processing; data not replicated and lost if a file server fails | no | FSXL what-is.html |
| FSx Lustre persistent | Longer-term storage; data replicated and failed servers replaced | no | FSXL what-is.html |
| FSx Lustre storage classes | SSD, Intelligent-Tiering and HDD | changed (Intelligent-Tiering class is newer) | FSXL what-is.html |
| FSx Lustre S3 integration | Link to an S3 bucket; objects appear as files; write data back to S3; data repository tasks | no | FSXL what-is.html |
| FSx Lustre integrations | SageMaker AI, AWS Batch, AWS ParallelCluster; on-prem burst over Direct Connect/VPN | no | FSXL what-is.html |
| FSx Lustre answer | HPC and ML training needing fast shared storage linked to S3 | no | FSXL what-is.html |
| FSx for NetApp ONTAP | Managed NetApp ONTAP; protocols NFS, SMB and iSCSI in one file system (multi-protocol); Windows, Linux, macOS clients | no | FSXO what-is-fsx-ont.html (summary only) |
| FSx ONTAP data features | Snapshots, FlexClone clones, SnapMirror replication, deduplication and compression, tiering to a lower-cost capacity pool, Multi-AZ | no | FSXO what-is-fsx-ont.html (summary only) |
| FSx ONTAP answer | Migrate on-premises NetApp or need NFS + SMB + iSCSI, replication to on-prem NetApp | no | FSXO what-is-fsx-ont.html (summary only) |
| FSx for OpenZFS | Managed OpenZFS; NFS v3, v4.0, v4.1, v4.2; Linux, Windows, macOS clients | no | FSXZ what-is-fsx.html |
| FSx OpenZFS performance | Up to 2 million IOPS, latencies of hundreds of microseconds; up to 21 GB/s from cache | no | FSXZ what-is-fsx.html |
| FSx OpenZFS features | Instant snapshots, cloning, compression, multiple volumes, thin provisioning, user and group quotas | no | FSXZ what-is-fsx.html |
| FSx OpenZFS deployment | Multi-AZ (HA), Single-AZ (HA), Single-AZ (non-HA); failover typically within 60 seconds | no | FSXZ what-is-fsx.html |
| FSx OpenZFS storage classes | Intelligent-Tiering and SSD | changed (newer) | FSXZ what-is-fsx.html |
| FSx OpenZFS S3 access points | S3 Access Points can attach to FSx for OpenZFS volumes | changed (new) | FSXZ what-is-fsx.html ; S3UG Welcome.html |
| FSx OpenZFS answer | Move on-premises ZFS or Linux file servers without changing apps | no | FSXZ what-is-fsx.html |
| FSx common | All encrypt at rest with KMS; HIPAA eligible; assessed for ISO, PCI-DSS, SOC | no | FSXW / FSXL / FSXZ what-is pages |
| Pick-a-file-system summary | Windows/SMB/AD: FSx Windows; HPC/Lustre: FSx Lustre; multi-protocol/NetApp: FSx ONTAP; ZFS/NFS: FSx OpenZFS; generic Linux NFS elastic: EFS | no | derived from the pages above |

## 10. Storage Gateway

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Gateway types | S3 File Gateway, FSx File Gateway, Volume Gateway, Tape Gateway | no | SGW storagegateway/ (docs index) |
| S3 File Gateway | Stores and retrieves objects in S3 using NFS v3 or v4.1 and SMB v2 or v3; transparent local caching; deploy as VM (ESXi, Hyper-V, KVM, Nutanix AHV), EC2 AMI, VMware Cloud on AWS, or hardware appliance | changed (Nutanix AHV support is newer) | FGW files3/what-is-file-s3.html |
| S3 File Gateway integrates | IAM, KMS, CloudWatch, CloudTrail; S3 lifecycle, CRR and versioning apply to the data | no | FGW files3/what-is-file-s3.html |
| FSx File Gateway | Provides on-premises access to FSx for Windows File Server shares; closed to new customers | changed (closed to new customers; blog dated 2024-10-28 per search result) | FGW filefsxw/ pages (search summary) |
| FSx File Gateway existing users | Existing customers can keep using it; migration between gateway types not supported | changed | FGW filefsxw/migrate-data.html (search summary) |
| Volume Gateway | iSCSI block volumes; cached or stored architecture; snapshots stored as EBS snapshots in S3 | no | SGW vgw/StorageGatewayConcepts.html |
| Cached volumes | Primary data in S3; frequently accessed data cached locally; volumes 1 GiB to 32 TiB; up to 32 volumes and 1,024 TiB per gateway | no | SGW vgw/StorageGatewayConcepts.html |
| Cached local disks | Cache storage plus upload buffer; allocate at least 20 percent of the existing file store as cache and cache larger than upload buffer | no | SGW vgw/StorageGatewayConcepts.html |
| Stored volumes | Primary data on-premises; async backup to S3 as EBS snapshots; volumes 1 GiB to 16 TiB; up to 32 volumes and 512 TiB per gateway | no | SGW vgw/StorageGatewayConcepts.html |
| Volume snapshots | Incremental snapshots stored in S3 as EBS snapshots; can seed a new EBS volume (snapshots up to 16 TiB for cached) | no | SGW vgw/StorageGatewayConcepts.html |
| Volume Gateway answer | Cached = low-latency access to hot data with S3 primary; Stored = entire data set local with cloud backup | no | SGW vgw/StorageGatewayConcepts.html |
| Tape Gateway | Virtual tape library for backup apps; archive in S3 Glacier Flexible Retrieval or Deep Archive; removes physical tape | no | SGW tgw/WhatIsStorageGateway.html |
| Hardware appliance | No longer sold: stopped being offered 2025-05-12; existing units supported until May 2028 | changed 2025-05-12 | SGW vgw/hardware-appliance.html (search summary) |
| Appliance OS note | Amazon Linux 2 based gateways: AWS asked migrations to AL2023 before 2026-06-30 | changed | FGW files3/al2-to-al2023-migration.html (search summary) |
| Local cache | All gateways use on-premises disks for cache; low-latency access to recent data | no | SGW vgw/StorageGatewayConcepts.html |

## 11. Other (Backup, DataSync, Transfer Family, Snow)

| Fact | Value | Changed? | Source |
|---|---|---|---|
| AWS Backup | Centralized, policy-based backup (backup plans, vaults, tag-based), cross-Region and cross-account copy, Vault Lock (WORM), Audit Manager | no | BKP whatisbackup.html |
| AWS Backup supported storage | EBS, S3, EFS, FSx (Lustre, Windows, ONTAP, OpenZFS), Storage Gateway Volume Gateway, EC2, RDS, DynamoDB and more | changed (EKS, Aurora DSQL, many others are newer) | BKP whatisbackup.html |
| AWS Backup cold tier | Lifecycle moves backups from warm to cold storage | no | BKP whatisbackup.html |
| Backup incremental | First backup full; later incrementals for supported resources | no | BKP whatisbackup.html |
| AWS DataSync | Online transfer between on-premises (NFS, SMB, HDFS, object storage), AWS storage (S3, EFS, FSx) and other clouds; encryption and integrity validation; scheduled tasks | changed (other-cloud sources are newer) | DS what-is-datasync.html |
| DataSync speed | Purpose-built protocol, parallel multi-threaded; a single task can use 10 Gbps | no | DS what-is-datasync.html ; SNOW snowball-edge-availability-change.html |
| DataSync use cases | Migrate, archive cold data to Glacier classes, replicate, move data for processing | no | DS what-is-datasync.html |
| AWS Transfer Family | Managed SFTP, FTPS, FTP, AS2 and browser-based (web app) transfers into and out of S3 and EFS | changed (web apps added 2024-12) | TF what-is-aws-transfer-family.html |
| Transfer Family details | Up to 3 AZs; FTP/FTPS data port range 8192 to 8200; managed workflows | no | TF what-is-aws-transfer-family.html |
| Snowball Edge status | No longer available to new customers; AWS will no longer offer Snow Family devices to new customers | changed 2025-11-07 (per facts.md) | SNOW snowball-edge-availability-change.html |
| Snow alternatives | DataSync (online), AWS Data Transfer Terminal (physical), AWS Partner solutions; Outposts for edge compute | changed | SNOW snowball-edge-availability-change.html |
| Existing Snow users | Not affected; AWS continues security and availability work | no | SNOW snowball-edge-availability-change.html |
| Snowcone / Snowmobile | Retired per facts.md; not re-read today | changed (per facts.md) | facts.md (not re-read) |

## 12. Prices (illustrative, us-east-1, USD)

| Fact | Value | Changed? | Source |
|---|---|---|---|
| S3 Standard storage | 0.023 per GB-month first 50 TB; 0.022 next 450 TB; 0.021 over 500 TB | no | S3 price file |
| S3 Intelligent-Tiering Frequent Access | 0.023 per GB-month (first 50 TB) | no | S3 price file |
| S3 Intelligent-Tiering Infrequent Access | 0.0125 per GB-month | no | S3 price file |
| S3 Intelligent-Tiering Archive Instant Access | 0.004 per GB-month | no | S3 price file |
| S3 Intelligent-Tiering Archive Access | 0.0036 per GB-month | no | S3 price file |
| S3 Intelligent-Tiering Deep Archive Access | 0.00099 per GB-month | no | S3 price file |
| S3 Intelligent-Tiering monitoring fee | 0.0025 per 1,000 objects per month | no | S3 price file |
| S3 Standard-IA storage | 0.0125 per GB-month | no | S3 price file |
| S3 One Zone-IA storage | 0.01 per GB-month | no | S3 price file |
| S3 Glacier Instant Retrieval storage | 0.004 per GB-month | no | S3 price file |
| S3 Glacier Flexible Retrieval storage | 0.0036 per GB-month (usage type TimedStorage-GlacierByteHrs, "Amazon Glacier") | no | S3 price file |
| S3 Glacier Deep Archive storage | $0.00099 per GB-month ("or $1 per TB-month") as printed on the official Glacier page; that page does not name the Region, and the us-east-1 price file has no Deep Archive storage row (the equal Intelligent-Tiering Deep Archive Access tier is 0.00099 there) | no | https://aws.amazon.com/s3/storage-classes/glacier/ |
| S3 Express One Zone storage | 0.11 per GB-month | no | S3 price file |
| S3 Reduced Redundancy storage | 0.024 per GB-month first 1 TB (legacy) | no | S3 price file |
| Standard-IA retrieval | 0.01 per GB | no | S3 price file |
| One Zone-IA retrieval | 0.01 per GB | no | S3 price file |
| Glacier Instant Retrieval retrieval | 0.03 per GB | no | S3 price file |
| Glacier Flexible Standard retrieval | 0.01 per GB | no | S3 price file |
| Glacier Flexible Bulk retrieval | 0.00 per GB (free) | no | S3 price file |
| Glacier Flexible Expedited retrieval | 0.03 per GB plus 0.01 per Expedited request | no | S3 price file |
| Deep Archive Standard retrieval | 0.02 per GB | no | S3 price file |
| Deep Archive Bulk retrieval | 0.0025 per GB | no | S3 price file |
| Express One Zone retrieval | 0.0006 per GB | no | S3 price file |
| Standard PUT/COPY/POST/LIST | 0.005 per 1,000 requests | no | S3 price file |
| Standard GET and other | 0.0004 per 1,000 requests (0.004 per 10,000) | no | S3 price file |
| Intelligent-Tiering requests | PUT/COPY/POST/LIST 0.005 per 1,000; GET 0.0004 per 1,000 | no | S3 price file |
| Standard-IA requests | PUT/COPY/POST/LIST 0.01 per 1,000; GET 0.001 per 1,000 (0.01 per 10,000) | no | S3 price file |
| One Zone-IA requests | PUT/COPY/POST/LIST 0.01 per 1,000; GET 0.001 per 1,000 | no | S3 price file |
| Glacier Instant Retrieval requests | PUT/COPY/POST/LIST 0.02 per 1,000; GET 0.01 per 1,000 (0.1 per 10,000) | no | S3 price file |
| Glacier Flexible requests | PutObject/CopyObject 0.03 per 1,000; GET and other 0.0004 per 1,000; lifecycle requests 0.03 per 1,000 | no | S3 price file |
| Deep Archive requests | Lifecycle requests 0.05 per 1,000; GET and other 0.0004 per 1,000 | no | S3 price file |
| Express One Zone requests | PUT/COPY/POST/LIST 0.00113 per 1,000; GET 0.00003 per 1,000 | no | S3 price file |
| Lifecycle transition requests | To Standard-IA, One Zone-IA or Intelligent-Tiering 0.01 per 1,000; to Glacier Instant Retrieval 0.02 per 1,000 | no | S3 price file |
| Early delete (IA) | Prorated storage rate: Standard-IA 0.0125, One Zone-IA 0.01 per GB-month | no | S3 price file |
| Early delete (Glacier) | Glacier Instant Retrieval 0.004; Glacier Flexible 0.0036 per GB-month prorated | no | S3 price file |
| S3 Select scanned / returned | Standard: 0.002 per GB scanned, 0.0007 per GB returned (existing customers only) | no | S3 price file |
| Data transfer out to internet (first tier) | 0.09 per GB for first 10 TB per month (beyond the global free tier); 0.085 next 40 TB; 0.07 next 100 TB; 0.05 over 150 TB | no | DT price file |
| S3 data transfer out (S3 to AWS outbound entry) | 0.0 per GB line for "S3-DT-AWS Outbound" in the S3 file (not the internet rate) | no | S3 price file |
| EBS gp3 storage | 0.08 per GB-month | no | EBS price page (example 1; region not named) |
| EBS gp3 extra IOPS | 0.005 per provisioned IOPS-month above 3,000 | no | EBS price page (example 1) |
| EBS gp3 extra throughput | 0.06 per provisioned MB/s-month above 125 | no | EBS price page (example 1) |
| EBS gp2 storage | 0.10 per GB-month | no | EBS price page (example 2) |
| EBS io2 storage | 0.125 per GB-month | no | EBS price page (example 3) |
| EBS io2 IOPS tiers | 0.065 per IOPS-month first 32,000; 0.046 for 32,001 to 64,000; third tier (over 64,000) not stated on the page | no | EBS price page (example 3) |
| EBS io1 | 0.125 per GB-month and 0.065 per provisioned IOPS-month | no | EBS price page (example 4) |
| EBS st1 | 0.045 per GB-month | no | EBS price page (example 5) |
| EBS sc1 | 0.015 per GB-month | no | EBS price page (example 6) |
| EBS snapshot standard | 0.05 per GB-month | no | EBS price page (example 10) |
| EBS snapshot archive | 0.0125 per GB-month (75 percent lower than standard, derived) | no | EBS price page (example 10) |
| EBS snapshot archive restore | 0.03 per GB | no | EBS price page (example 10) |
| EBS fast snapshot restore | 0.75 per DSU-hour per snapshot per AZ (US East N. Virginia) | no | EBS price page (example 8) ; EBS ebs-fast-snapshot-restore.html |
| EFS Standard (Regional) | 0.30 per GB-month | no | EFS price file |
| EFS Infrequent Access (Regional) | 0.025 per GB-month (0.016 per GB-month when the file system uses Elastic throughput) | no | EFS price file |
| EFS Archive (Regional) | 0.008 per GB-month | no | EFS price file |
| EFS One Zone Standard | 0.16 per GB-month | no | EFS price file |
| EFS One Zone-IA | 0.0133 per GB-month | no | EFS price file |
| EFS IA data access | 0.01 per GB reads and 0.01 per GB writes | no | EFS price file |
| EFS Archive data access | 0.03 per GB reads and 0.03 per GB writes/tiering | no | EFS price file |
| EFS Elastic throughput | 0.03 per GB read and 0.06 per GB written | no | EFS price file |
| EFS Provisioned throughput | 6.00 per MiBps-month | no | EFS price file |

## Unconfirmed

- Whether a lifecycle rule must wait 30 days before transitioning from Standard to Standard-IA / One Zone-IA: re-read the "Constraints and considerations for transitions" section of lifecycle-transition-general-considerations.html on 2026-10-11; it contains no such rule (only the 128 KB default, the minimum-duration charge and the two-step rule). Do not teach a "30-day transition minimum" as a number.
- S3 Glacier Deep Archive storage price in us-east-1 specifically: the Glacier product page prints $0.00099 per GB-month without naming a Region (kept in section 12 with that caveat). The Glacier provisioned capacity unit price is also still missing.
- S3 Express One Zone minimum storage duration: S3 user guide comparison table says "None"; the storage-classes product page says 1 hour. The two official pages disagree; both were read today.
- Express One Zone request-cost discount: storage-class page says 50 percent lower than Standard, Welcome page says 80 percent lower; price file ratio is about 77 percent (0.00113 vs 0.005 per 1,000 PUT).
- Max object size: multipart limits table still lists 48.8 TiB; upload and announcement pages say 50 TB (announced 2025-12-02). Use 50 TB.
- RTC percentage: replication overview says 99.99 percent within 15 minutes; the same page's workload table says 99.9 percent. Use "within 15 minutes, SLA-backed".
- Whether DeleteBucket fails while incomplete multipart uploads exist: pages say the bucket must be empty and recommend removing incomplete uploads while emptying; neither states the failure explicitly.
- Whether Object Lock can be turned on for an existing bucket: not on the overview page read.
- Byte-range fetch recommended size (8 MB or 16 MB) and Requester Pays details: guideline pages not fetched.
- s3:x-amz-server-side-encryption condition key with value aws:kms: specifying-s3-encryption.html (read 2026-10-11) shows only the x-amz-server-side-encryption request header with value AES256 (SSE-S3); no bucket-policy condition or aws:kms value appears there. Still unconfirmed on an official page.
- FSx for NetApp ONTAP and FSx Windows DFS details: ONTAP page returned only a thin summary; DFS Namespaces not seen on the Windows what-is page; FSx Lustre persistent deployment sub-types not read.
- FSx File Gateway closure date: docs search result says "no longer available to new customers"; the 2024-10-28 date comes from a blog snippet in search results, not from a page body read.
- Storage Gateway hardware appliance end of sale (2025-05-12, support to May 2028) comes from a search summary of the docs notice, not a full page body.
- EBS prices come from worked examples on the EBS pricing page; the page did not name the Region for most of them and the io2 third IOPS tier is not given. EBS offer file was too large to download for a rate-table check.
- S3 Select retirement date: page shows the new-customer notice but no date (facts.md carries 2024-07-25).
- EFS Archive lifecycle thresholds: the storage-classes page excerpt was truncated before the Archive day options.
- EFS One Zone availability: file-system table says 99.99 percent, storage-class table says 99.9 percent (One Zone).
- Snowcone / Snowmobile retirement dates: not re-read (kept from facts.md).
- Original vault-based Glacier closure date (2025-12-15 in facts.md): not re-read.

## Confidence notes

- High confidence: S3 storage class table (durability, availability, AZs, minimum durations, minimum sizes), Glacier retrieval times, lifecycle waterfall and 128 KB default, versioning/delete marker behaviour, Object Lock modes, BPA settings, SSE-C April 2026 default change, Bucket Key 99 percent, presigned URL limits, ALB log bucket policy, EBS volume type limits (gp3 64 TiB / 80,000 / 2,000 MiB/s), Multi-Attach rules, EBS Elastic Volumes limit, snapshot archive rules, EFS storage classes and quotas, S3 and EFS price rows (from the official price files published 2026-09-28).
- Medium confidence: EBS price rows (worked examples, Region not named but amounts match common us-east-1 rates), replication details (read from the replication pages but the requirements page was skipped), FSx ONTAP, Storage Gateway hardware/FSx File Gateway statuses (search summaries).
- Several documentation pages disagree on small points (Express One Zone minimum duration and request discount, RTC percentage, 48.8 TiB vs 50 TB, EFS One Zone availability). Course material should pick one wording and avoid quizzing the disputed number.
- Product-page tables of per-GB prices are rendered by script and were not readable; prices come from the machine-readable AWS price files instead.
- Many features here (variable retention, account regional namespace, S3 Tables, EFS Archive, SSE-C default off) are newer than SAA-C03; exam questions still centre on classic behaviour.
- Exam guide task statements 1.3, 3.1 and 4.1 were read first; section order follows the brief.

Exam tasks: 4.1, 1.3, 2.2

# 02 — S3 lifecycle, versioning, Object Lock and replication

## What it is

Four features keep S3 data cheap and safe over time:

| Feature | Job |
|---|---|
| **Lifecycle rules** | Move objects to cheaper classes and delete them on a schedule |
| **Versioning** | Keep every version of a key, so overwrites and deletes can be undone |
| **Object Lock** | Make object versions write-once-read-many (WORM) for a period |
| **Replication** | Copy new objects to another bucket, in the same or another Region |

Task 4.1 is lifecycle (data lifecycles, tiering). Task 1.3 is data recovery and retention. Task 2.2 is replication
as disaster recovery. Drill 02 builds a lifecycle validator. Drill 07 predicts what a versioned bucket returns.
Drill 09 fixes a replication rule.

## How it works

### Lifecycle actions

A **lifecycle configuration** is a list of rules on a bucket (up to 1,000 rules, one configuration per bucket). Each
rule has a filter and actions:

| Action | What it does |
|---|---|
| **Transition** | Move current versions to another class after N days |
| **Expiration** | Delete current versions after N days. With versioning on, it adds a delete marker instead |
| **NoncurrentVersionTransition** | Move old versions N days after they became noncurrent |
| **NoncurrentVersionExpiration** | Permanently delete old versions. Can keep the newest N noncurrent versions (1 to 100) |
| **ExpiredObjectDeleteMarker** | Remove a delete marker once no versions are left under it |
| **AbortIncompleteMultipartUpload** | Abort uploads still unfinished after N days (7 is a good start) |

- **Days count from creation** (or from the moment a version became noncurrent), rounded up to midnight UTC.
- Rules apply to **existing** objects as well as new ones.
- A **filter** is a prefix, object tags, an object size range, or a combination. An empty filter means every object.
  One prefix per filter: use several rules for several prefixes.
- Expiration deletes the object *for good* on an unversioned bucket. A bucket policy cannot stop a lifecycle delete.
- `ExpiredObjectDeleteMarker` and `AbortIncompleteMultipartUpload` cannot be used with a **tag** filter.
- Expiration rules do **not** clean up unfinished multipart uploads. Only the abort action does.

### The waterfall

Objects only move **down**. A rule can use only the transitions this table allows.

| From | To |
|---|---|
| Standard | any class below it |
| Standard-IA | Intelligent-Tiering, One Zone-IA, Glacier IR, Flexible, Deep Archive |
| One Zone-IA | Glacier Flexible Retrieval or Deep Archive only |
| Glacier Instant Retrieval | Flexible or Deep Archive only |
| Glacier Flexible Retrieval | Deep Archive only |
| Deep Archive | nowhere. To get out, restore, then copy |

Never to Standard. Never from Glacier Flexible back up to Standard-IA.

### The two-step minimum rule

One rule cannot move an object out of a class **before that class's minimum storage duration** has passed.
Glacier Instant Retrieval has a 90-day minimum. So "Glacier IR at day 4, Deep Archive at day 20" is refused. The
Deep Archive step must come at least 94 days after creation.

Standard-IA needs 30 days: Standard-IA at day 30, Flexible Retrieval no earlier than day 60. Two separate rules
get around the check, but you then pay the early-delete charge. Drill 02 checks this rule.

### The 128 KB default

Objects **under 128 KB are not transitioned** by default. (changed in September 2024: before, they could go to the
Glacier classes.) Reason: every transition is a billed request, and for tiny objects the request costs more than the
storage saves. To move small objects anyway, add an object size filter to the rule. Old configurations keep the old
behaviour until you edit them.

### Lifecycle runs asynchronously

Rules run in the background, not at the exact second. An object is billed at the new rate as soon as it is *eligible*, even
if S3 has not yet moved it. A rule change can take about 15 minutes to take effect. If an object is eligible for several
actions on one day, the cheapest wins: deletion beats transition. Lifecycle takes no action on noncurrent versions under Object Lock, or on objects with a
pending or failed replication. Drill 02 asks which class an object is in after N days.

### Versioning

Versioning keeps **every version** of every key. It has three states: unversioned (the default), enabled and
suspended. Once enabled it can only be **suspended**, never turned back off.

- Each PUT creates a new version with a new **version ID**. Each version is a full copy, billed in full.
- Objects stored before versioning have the version ID `null`.
- A **simple DELETE** (no version ID) adds a **delete marker** as the newest version. Nothing is removed.
- A DELETE **with a version ID** removes that version permanently.
- **Restore a deleted object** by deleting the delete marker. Or copy an old version over the top.
- When versioning is suspended, new writes get the version ID `null`. Old versions stay.

What the calls show after a simple delete:

| Call | Result |
|---|---|
| GET `invoice.pdf` | 404 Not Found (the response says a delete marker is current) |
| GET `invoice.pdf` with an old version ID | the old data |
| LIST (ListObjectsV2) | the key is missing |
| ListObjectVersions | every version, plus the delete marker |
| HEAD with the delete marker's version ID | 405 Method Not Allowed |

A second example. A bucket holds three versions of `a.txt`, then someone deletes the *newest version by its ID*. The
second newest becomes current at once, and a plain GET returns it. No marker is involved.

**MFA delete** adds a second factor to two actions: changing the versioning state and permanently deleting a version.
Only the bucket owner (the root user) can turn it on, and only with the CLI or API. It does not work with lifecycle rules.

### Object Lock

Object Lock needs versioning. It protects an **object version**, not a key: someone can still add a new version or
a delete marker, but cannot delete the locked version.

| | Governance mode | Compliance mode | Legal hold |
|---|---|---|---|
| Who can delete early | A user with `s3:BypassGovernanceRetention` who asks for the bypass | **Nobody**, not even root | Anyone with `s3:PutObjectLegalHold` can remove it |
| Can the period be shortened | By a user with bypass | No | There is no period |
| Ends | At the retain-until date | At the retain-until date | When you remove it |

- A **retention period** is a retain-until date per version, or a bucket default in days or years.
- A legal hold works on its own or together with retention. Use it for an investigation with no end date.
- A permanent delete of a locked version returns **403**.
- Use compliance mode for regulation such as SEC 17a-4. Use governance to test, or to let admins override.

### Replication

Replication copies new objects **asynchronously** to another bucket. **CRR** is cross-Region. **SRR** is same-Region.
The buckets can be in different accounts.

Requirements:

1. **Versioning on in both** buckets. Without it the rule is refused or fails.
2. An **IAM role** that S3 assumes to read the source and write the destination.
3. Cross-account: the destination owner grants permission with a bucket policy.
4. If the source has Object Lock, so must the destination.

What it does and does not copy:

- **Only new objects** after the rule exists. For **existing objects**, run **S3 Batch Replication**. It also retries failed objects.
- **Delete markers** are not copied by default. You can switch on delete marker replication.
- **Version-specific deletes** are never copied. This protects the replica from a malicious delete.
- **Lifecycle actions** are not replicated. Put the same lifecycle configuration on both buckets.
- **No chaining.** A replica is not replicated onward to a third bucket.
- Objects in Glacier Flexible, Deep Archive or the archive tiers cannot be replicated until restored.
- The replica can use a different storage class and owner. A replica can be a cheap Glacier copy in another Region.

**Replication Time Control (RTC)** copies new objects within **15 minutes**, backed by an SLA, with metrics. Without
it, replication is best effort and typically takes 24 to 48 hours. Drill 09 fixes a replication rule that never starts.

## Numbers to know

- Lifecycle: up to **1,000** rules; days from creation; 128 KB default minimum; abort unfinished uploads after **7** days is the usual start.
- Two-step minimum: Glacier IR 90 days, so Deep Archive at day **94** or later if the first move is at day 4.
- `NewerNoncurrentVersions`: **1 to 100**.
- Versioning: **three** states; cannot return to unversioned. Wait about 15 minutes after enabling before writing.
- Object Lock: **two** modes plus legal hold. Delete of a locked version: 403.
- Replication: **15 minutes** with RTC; **24 to 48 hours** without.

## When to choose it

| Need | Use |
|---|---|
| Logs cooling off over time | Lifecycle transitions, then expiration |
| Undo an accidental overwrite or delete | Versioning |
| Stop versions piling up | Noncurrent version expiration (keep the newest N) |
| Nobody, even root, may delete for 7 years | Object Lock, compliance mode |
| Admins may override, protect from mistakes | Object Lock, governance mode |
| Freeze data for an investigation | Legal hold |
| Copy to another Region for disaster recovery | CRR |
| Copy to a second account or a logs bucket in the same Region | SRR |
| Copy existing objects too | Batch Replication |
| A 15-minute recovery point with an SLA | Replication Time Control |
| Require a second factor for permanent deletes | MFA delete |

## Exam traps

- **Replication without versioning** on the source or the destination.
- **Expecting existing objects to replicate.** Only new objects do. Use Batch Replication.
- **Expecting deletes to replicate.** A version-specific delete never does. A delete marker does only if you enable it.
- **Lifecycle "to Standard".** The waterfall only goes down.
- **Tiny objects in a transition rule.** Under 128 KB they stay put unless the rule has a size filter.
- **Expiration on a versioned bucket does not free space.** It adds a delete marker. Add a noncurrent-version rule.
- **Versioning is not a backup against account loss.** It lives in the same bucket. Use replication or AWS Backup as well.
- **Governance vs compliance.** Root can override governance (with the right permission), never compliance.
- **Object Lock without versioning** is impossible.
- **Versioning grows the bill.** Every version is a full object.
- **Unfinished multipart uploads** are invisible in a listing but billed. Abort them with a lifecycle rule.
- **Suspending versioning** keeps the old versions and keeps charging for them.

## Cost angle

- Versioning without a noncurrent-version rule means every overwrite is stored forever. Cap the old versions: "keep 3 noncurrent versions for at most 30 days".
- A lifecycle transition costs a request: 0.01 USD per 1,000 into Standard-IA and 0.02 into Glacier IR. Millions of tiny objects can cost more to move than they save, which is why the 128 KB default exists.
- Moving early out of an IA or Glacier class bills the remaining minimum duration.
- A delete marker has no data but is billed by its key-name size. Remove expired delete markers.
- Replication costs the destination storage, the replication requests and inter-Region data transfer for CRR. RTC costs extra. A replica in Glacier is cheap.
- A restore from Glacier bills a temporary Standard copy as well as the archive copy.

## Comparison

| | Versioning | MFA delete | Object Lock | Replication | Lifecycle |
|---|---|---|---|---|---|
| Protects against | Overwrite, delete | Accidental permanent delete | Any delete, for a period | Loss of a Region or account | Nothing (it saves money) |
| Needs versioning | it is versioning | yes | yes | yes, on both buckets | no |
| Stops a determined admin | No | Partly | Compliance: yes | No | No |
| Cost | Every version billed | none | none | Storage + transfer | Request per transition |
| Existing objects | Old ones become `null` | n/a | Per version | Batch Replication | Yes |

Now do drill 02 (when does this object move), drill 07 (what survives a delete) and drill 09 (replication that never starts).

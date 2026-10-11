Exam tasks: 3.1, 4.1

# 01 — S3 fundamentals and storage classes

## What it is

**Amazon S3** is object storage. You store **objects** (a body plus metadata) in **buckets**. You read and write
them over HTTPS with an API. There is no disk to mount and no file system to manage. S3 has no limit on bucket
size or on the number of objects.

Three storage types come up all week:

| Type | What you get | AWS service |
|---|---|---|
| **Object** | Whole objects by key, over an API | S3 |
| **Block** | A raw disk that one server formats | EBS, instance store |
| **File** | A shared folder (NFS or SMB) | EFS, FSx |

Task 3.1 asks you to match a workload to a storage service. Task 4.1 asks you to match an access pattern to the
cheapest storage tier. Both start here. Drill 01 prices the classes. Drill 04 sizes big uploads.

## How it works

### Buckets, objects, keys and prefixes

- A **bucket** is a container. A general purpose bucket name is **globally unique** across all accounts and
  Regions of a partition. It is 3 to 63 characters: lowercase letters, numbers, periods and hyphens. You cannot
  change the name or the Region later.
- Avoid periods in names. They break HTTPS with virtual-hosted-style addressing and rule out Transfer Acceleration.
- The default quota is **10,000 buckets per account**, raisable to 1 million through Service Quotas.
  (changed: it was 100, with a maximum of 1,000.)
- An **object** is identified by its **key**, the full name, such as `logs/2026/10/app.log`.
- S3 is flat. There are no real folders. A **prefix** is just the start of a key. The console shows `/` as a folder
  because the delimiter is `/`.
- An object holds a body, system metadata, user metadata (up to 2 KB) and up to 10 tags.

### Size limits and multipart upload

- The maximum object size is **50 TB**. (changed in December 2025: it was 5 TB.)
- One PUT can send up to **5 GB**. Larger objects need **multipart upload**.
- Use multipart from about **100 MB** anyway. It uploads parts in parallel, in any order, and a failed part is
  retried alone.
- Parts are **5 MiB to 5 GiB** (the last part can be smaller). An upload has at most **10,000 parts**.
- Unfinished uploads keep costing storage. A lifecycle rule should abort them (note 02).
- The S3 console uploads at most 160 GB per file. Use the CLI or an SDK above that.

### Consistency

S3 gives **strong read-after-write consistency** for new objects, overwrites and deletes, in every Region. A GET
right after a PUT returns the new data. A LIST right after a PUT shows it. (changed in December 2020: overwrites
and deletes used to be eventually consistent.)

Two limits remain. Bucket *settings* (a deleted bucket may still be listed for a while) are eventually consistent. And
there is no locking: two writers to one key end with last-writer-wins.

### Request rates and prefixes

- At least **3,500 PUT/COPY/POST/DELETE** and **5,500 GET/HEAD** requests per second **per prefix**.
- There is no limit on the number of prefixes. Spread keys over 10 prefixes and reads scale to 55,000 a second.
- S3 scales gradually. During a sudden jump you may see `503 Slow Down`. Retry with backoff.
- Drill 04 asks how many prefixes a given request rate needs.

### Durability and availability

Every storage class in the table below is designed for **99.999999999 % (11 nines) durability**. That is a design number for
not losing an object. The One Zone classes keep that data in a single AZ, so they do not survive the loss of that AZ. Classes differ in **availability** and in how many AZs hold the data.

### Storage classes

All the numbers in one table. "Min days" is the minimum storage duration: delete or move an object sooner and
you still pay for the rest. "Min size" is the minimum billable object size.

| Class | AZs | Availability | Min days | Min size | Retrieval fee | Access |
|---|---|---|---|---|---|---|
| **Standard** | 3+ | 99.99 % | none | none | none | milliseconds |
| **Intelligent-Tiering** | 3+ | 99.9 % | none | none (but under 128 KB is never tiered) | none | milliseconds (archive tiers: restore) |
| **Standard-IA** | 3+ | 99.9 % | 30 | 128 KB | per GB | milliseconds |
| **One Zone-IA** | **1** | 99.5 % | 30 | 128 KB | per GB | milliseconds |
| **Glacier Instant Retrieval** | 3+ | 99.9 % | 90 | 128 KB | per GB | milliseconds |
| **Glacier Flexible Retrieval** | 3+ | 99.99 % (after restore) | 90 | none, 40 KB overhead | per GB | minutes to hours |
| **Glacier Deep Archive** | 3+ | 99.99 % (after restore) | 180 | none, 40 KB overhead | per GB | hours |
| **Express One Zone** | **1** | 99.95 % | none | none | per GB | single-digit ms |

- **Standard** is the default. Frequent access, no fees for moving data out of the class.
- **Standard-IA** (infrequent access) is cheaper to store and charges to read. For data kept at least 30 days and
  read rarely, but needed at once. Use it for the only copy of data you cannot re-create.
- **One Zone-IA** is the same in one AZ, 20 % cheaper to store. If that AZ is lost, the data is lost. Only for data you can
  re-create, or replicas.
- **Glacier Instant Retrieval** is archive pricing with millisecond reads. For data read about once a quarter.
- **Glacier Flexible Retrieval** and **Deep Archive** are the cheapest. You must **restore** an object before you
  read it. The restored copy is a temporary Standard copy; the object stays in Glacier.
- Each archived object carries **40 KB of overhead**: 32 KB at the archive price and 8 KB at the Standard price.
- Reduced Redundancy Storage is not recommended. Standard is cheaper. It is not an exam answer.

### Glacier restore options

| Option | Flexible Retrieval | Deep Archive |
|---|---|---|
| **Expedited** | 1 to 5 minutes (objects under 250 MB) | not available |
| **Standard** | 3 to 5 hours (the default) | within 12 hours |
| **Bulk** | 5 to 12 hours (free) | within 48 hours |

### Intelligent-Tiering

Use it when you **do not know the access pattern**. S3 moves each object between tiers by itself and charges no
retrieval fee.

| Tier | Moves there after | Access |
|---|---|---|
| Frequent Access | start | milliseconds |
| Infrequent Access | 30 days without access | milliseconds |
| Archive Instant Access | 90 days without access | milliseconds |
| Archive Access (opt-in) | 90 to 730 days, you choose | restore, 3 to 5 hours |
| Deep Archive Access (opt-in) | 180 to 730 days, you choose | restore, within 12 hours |

- Three tiers are automatic, two are opt-in: five in all.
- A read, write or copy moves an object back to Frequent Access. A HEAD or LIST does not.
- You pay a **monitoring fee of 0.0025 USD per 1,000 objects a month**. Objects under **128 KB** are not monitored
  and stay in Frequent Access, so they cost the Standard price and no fee.

### Express One Zone and directory buckets

**S3 Express One Zone** keeps data in **one AZ that you choose**, for single-digit-millisecond access. It is
up to 10 times faster than Standard and has its own bucket type, the **directory bucket**. Directory buckets have
no prefix limits (up to 200,000 reads and 100,000 writes per second per bucket), always block public access and
use only `/` as the delimiter. They cost about five times Standard to store. Use them for latency-critical,
repeated reads such as ML training or interactive analytics.

## Numbers to know

- Object: up to **50 TB**. Single PUT: up to **5 GB**. Multipart from about **100 MB**; parts **5 MiB–5 GiB**, at most **10,000**.
- Per prefix: **3,500** writes and **5,500** reads a second.
- Buckets: **10,000** per account by default. Name 3–63 characters.
- Durability **11 nines** for every class. Availability: Standard 99.99 %, IA and Intelligent-Tiering and Glacier IR 99.9 %, One Zone-IA 99.5 %.
- Minimum duration: IA classes **30** days, Glacier IR and Flexible **90**, Deep Archive **180**. Minimum size: **128 KB** for IA and Glacier IR.
- Restore: Expedited 1–5 minutes, Standard 3–5 hours, Bulk 5–12 hours (Flexible Retrieval); Deep Archive 12 and 48 hours.
- Intelligent-Tiering: 30 and 90 days, optional 90+ and 180+, monitoring 0.0025 USD per 1,000 objects, 128 KB.

## When to choose it

| Situation | Class |
|---|---|
| Active data, read often | Standard |
| Unknown or changing access pattern | Intelligent-Tiering |
| Read monthly or less, need it fast, only copy | Standard-IA |
| Same, but easy to re-create or a replica | One Zone-IA |
| Archive, rarely read, need milliseconds | Glacier Instant Retrieval |
| Archive, a wait of hours is fine | Glacier Flexible Retrieval |
| Compliance archive kept for years, almost never read | Glacier Deep Archive |
| Single-digit-millisecond access to hot data | Express One Zone |

## Exam traps

- **Cheapest per GB is not cheapest overall.** Small objects, short lives and heavy reads can make an IA or Glacier class dearer than Standard. Count the minimums and the retrieval fees.
- **128 KB objects in an IA class** are billed as 128 KB. A million 10 KB files cost more in Standard-IA than in Standard.
- **Early delete.** Remove an object from Standard-IA at day 10 and you still pay for 30 days.
- **One Zone-IA is not resilient to the loss of an AZ.** If the question says "critical" or "only copy", it is wrong.
- **"Milliseconds" rules out Flexible Retrieval and Deep Archive.** Glacier *Instant* Retrieval is the archive with milliseconds.
- **Expedited is not available for Deep Archive.**
- **Intelligent-Tiering with tiny objects.** Under 128 KB there is no tiering, so no saving.
- **Eventual consistency** is old advice. S3 is strongly consistent now.
- **5 GB is the single PUT limit, 50 TB the object limit.** Do not mix them up. (The old object limit was 5 TB.)
- **A "folder" is a prefix.** Renaming a folder copies every object.

## Cost angle

- Storage is billed per GB-month. You also pay per request (a PUT costs about 12 times a GET in Standard) and for data **out** to the internet (first tier 0.09 USD per GB).
- Start in Standard, learn the access pattern, then move data with lifecycle rules (note 02) or let Intelligent-Tiering do it.
- Price per GB-month: Standard 0.023, Intelligent-Tiering Frequent 0.023, Standard-IA 0.0125, One Zone-IA 0.01, Glacier IR 0.004, Flexible 0.0036, Deep Archive 0.00099, Express 0.11 (illustrative, us-east-1).
- Retrieval fee per GB: Standard-IA and One Zone-IA 0.01, Glacier IR 0.03, Deep Archive Standard 0.02. Bulk on Flexible Retrieval is free.
- A cost question is a sum: storage × billable days + retrieval. Billable size is the larger of the object and the minimum. Drill 01 does it.
- Use Storage Class Analysis to see which prefixes are cold. Use S3 Storage Lens for account-wide numbers.

## Comparison

| | Standard | Intelligent-Tiering | Standard-IA | One Zone-IA | Glacier IR | Flexible | Deep Archive |
|---|---|---|---|---|---|---|---|
| Storage USD/GB-month | 0.023 | 0.023 down to 0.00099 | 0.0125 | 0.01 | 0.004 | 0.0036 | 0.00099 |
| Min days | none | none | 30 | 30 | 90 | 90 | 180 |
| Retrieval fee | none | none | yes | yes | yes | yes | yes |
| Millisecond access | yes | yes (not archive tiers) | yes | yes | yes | no | no |
| AZs | 3+ | 3+ | 3+ | 1 | 3+ | 3+ | 3+ |
| Use for | Hot data | Unknown pattern | Rare reads, only copy | Re-creatable rare reads | Fast archive | Archive, hours OK | Years-long compliance |

Now do drill 01 (what does this storage cost) and drill 04 (big objects, busy buckets).

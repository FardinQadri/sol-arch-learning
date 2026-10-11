Exam tasks: 3.3, 4.3, 2.2

# 03 — Amazon DynamoDB

## What it is

**DynamoDB** is a fully managed key-value and document database. There are no servers, no instances and no
patching. You create a **table**, name a **key**, and read and write **items**. Latency is single-digit milliseconds
at any size. You design the table around the questions you will ask, not around the shape of the data.

Exam tasks:

- **3.3** capacity units, data access patterns, relational compared with non-relational.
- **4.3** "database capacity planning (for example, capacity units)", DynamoDB compared with RDS.
- **2.2** global tables, backups, point-in-time recovery.

## How it works

### Tables, items and keys

- A **table** holds **items** (rows). Items in one table can have different attributes.
- Maximum **item size is 400 KB**, counting attribute names and values.
- The primary key is either a **partition key** alone, or a **partition key plus a sort key** (composite).
- DynamoDB hashes the partition key to pick the **partition** (storage and throughput slice). Items with the same partition key sit together, ordered by sort key.
- Table size has no practical limit. Default quota: 2,500 tables per Region.
- Encryption at rest is **always on** (AWS owned key by default; AWS managed or customer managed keys optional). You cannot turn it off.

### Read and write units, and consistency

| Operation | Cost (per item) |
|---|---|
| Write | 1 write unit per 1 KB, rounded up |
| Transactional write | 2 write units per 1 KB |
| Strongly consistent read | 1 read unit per 4 KB, rounded up |
| Eventually consistent read | 0.5 read unit per 4 KB |
| Transactional read | 2 read units per 4 KB |

Examples with new numbers: a 9 KB item costs 3 read units strongly consistent (9/4 rounds up to 3), 1.5 eventually consistent
(round up to whole 4 KB blocks first, then halve), and 9 write units. A 300-byte write is 1 unit.

Reads are **eventually consistent by default**. A strongly consistent read returns the latest write. Strong reads work on tables and LSIs.
**GSIs and streams are always eventually consistent.** Drill 01 builds this arithmetic.

### Capacity modes

| | On-demand | Provisioned |
|---|---|---|
| You set | Nothing (optionally a maximum) | Read and write units per second |
| Billing | Per request unit | Per provisioned unit-hour, used or not |
| Scaling | Instant up to double the previous peak | Application Auto Scaling target tracking (AWS suggests 70 % utilisation) |
| Throttling | If traffic more than doubles within 30 minutes | If you exceed what you set (burst helps for ~5 minutes of saved capacity) |
| Good for | New, spiky or unknown traffic | Steady, predictable traffic |

On-demand is now the **default and recommended** mode. Its prices were cut by **50 %** on 2024-11-01 (the old prices were double today's).
Today: **0.625 USD per million write units** and **0.125 USD per million read units**. Provisioned: **0.00065 USD per WCU-hour** and **0.00013 USD per RCU-hour** (the first 25 of each are free).

**Switching:** provisioned to on-demand up to four times in a rolling 24 hours; on-demand to provisioned at any time.
You can also set a maximum throughput on an on-demand table to cap spend.
Provisioned **decreases** are limited (4 at the start of each day, plus one per hour, up to 27 a day). Increases are not.

**Break-even:** one provisioned unit-hour can serve 3,600 requests. On-demand prices those at 3,600 x price per million / 1,000,000.
Divide the provisioned hourly price by that figure to get the share of capacity you must really use for provisioned to win. Below it, on-demand is cheaper.
Drill 02 builds this.

Reserved capacity (provisioned only, blocks of 100 units) is cheaper again for steady use: AWS quotes savings up to 54 % (1 year) and 77 % (3 years).

### Partitions and hot keys

Each partition handles about **3,000 reads or 1,000 writes per second**. A **hot key** (one partition key getting most of the traffic) throttles even if the table has spare capacity overall.
Adaptive capacity moves capacity toward hot partitions automatically, but it cannot beat the per-partition ceiling.
Fix: a high-cardinality partition key, or add a random or calculated suffix to spread a hot key ("write sharding").

### Indexes

| | GSI (global secondary index) | LSI (local secondary index) |
|---|---|---|
| Keys | Different partition key and optional sort key | **Same** partition key, different sort key |
| Created | Any time | **Only when the table is created** |
| Limit per table | 20 (default) | 5 |
| Consistency | Eventually consistent only | Eventual or strong |
| Capacity | Its own (provisioned tables) | Shares the table's |
| Size limit | None | 10 GB per partition-key value |

Indexes copy ("project") attributes: KEYS_ONLY, INCLUDE or ALL. You read an index with Query or Scan only (not GetItem).
On a provisioned table, a GSI with too little write capacity throttles writes to the **base table**.

### Query vs Scan

- **Query** needs one partition key value. It can add a sort-key condition (`=`, `<`, `BETWEEN`, `begins_with`). It reads only matching items and is cheap.
- **Scan** reads **everything** in the table (or index). A `FilterExpression` is applied **after** the read, so you pay for all the items read.
- Both return at most **1 MB** per call. Use `LastEvaluatedKey` to page.

### Single-table design

DynamoDB has no joins. So you put items that are read together **in the same partition** and tell them apart with the sort key.
Example (a library): one table with `PK` and `SK`.

| PK | SK | What it is |
|---|---|---|
| `MEMBER#42` | `PROFILE` | the member |
| `MEMBER#42` | `LOAN#2026-03-02#B17` | a loan |
| `MEMBER#42` | `LOAN#2026-04-11#B09` | a loan |

One Query on `PK = MEMBER#42` returns the member and all loans. Add `begins_with(SK, "LOAN#2026-03")` for one month.
A GSI with `GSI1PK = BOOK#B17` answers "who has borrowed this book?". Rule: **list your access patterns first**, then choose keys and indexes.
Drill 03 asks for this with a different business.

### Conditional writes, optimistic locking, transactions

- A **condition expression** on `PutItem`, `UpdateItem` or `DeleteItem` makes the write succeed only if the condition is true. If false you get a `ConditionalCheckFailedException`.
- `attribute_not_exists(pk)` on a put means "create only, never overwrite".
- **Optimistic locking:** keep a `version` attribute. Update with `version = :seen` and set `version = :seen + 1`. If someone else wrote first, the condition fails; re-read and retry.
- **Transactions** (`TransactWriteItems`, `TransactGetItems`): all-or-nothing across up to **100 items** and 4 MB (changed: older material quotes a smaller limit). Each item costs **double** capacity, even if the transaction fails. No two actions on the same item. One account and one Region.
- `BatchWriteItem` (up to 25 puts or deletes) and `BatchGetItem` (up to 100 items) are **not** atomic.

### Streams and TTL

- **DynamoDB Streams:** an ordered log of item changes kept for **24 hours**. A view type picks what each record holds: keys only, new image, old image or both. Typical use: trigger Lambda. For longer retention (up to 1 year) use Kinesis Data Streams.
- **TTL:** you name a Number attribute holding a Unix timestamp (seconds). DynamoDB deletes expired items **in the background, typically within a few days**, free of write capacity. Expired items can still be read until then, so filter them in the query.

### Backups and global tables

- **Point-in-time recovery (PITR):** off by default. When on, you can restore to any second in the last **35 days** (configurable 1 to 35). Restore creates a **new table**.
- **On-demand backups:** full copies you start yourself, kept until you delete them. Restore makes a new table.
- Export to S3 needs PITR on and consumes no read units.
- **Global tables:** multi-active, write to any Region, **99.999 %** availability SLA (99.99 % single-Region).
  - **MREC** (multi-Region eventual consistency, the default): asynchronous, usually under a second, **last writer wins**.
  - **MRSC** (multi-Region strong consistency, newer): synchronous, RPO of zero, exactly three Regions; no TTL, no LSIs, no transactions.
- Version-based locking does not work across MREC Regions (last writer wins).
- **Table classes:** Standard (default) and Standard-IA, for tables where storage costs more than half of the throughput bill. A switch is limited to twice per 30 days.

## Numbers to know

| Fact | Value |
|---|---|
| Item size | 400 KB |
| Read unit | 4 KB strong; half that cost eventually consistent; 2x transactional |
| Write unit | 1 KB; 2x transactional |
| Query/Scan page | 1 MB |
| Partition limits | 3,000 reads or 1,000 writes per second |
| GSIs / LSIs per table | 20 / 5 |
| LSI collection limit | 10 GB per partition key |
| Transaction | up to 100 items, 4 MB |
| Batch write / get | 25 / 100 |
| Streams retention | 24 hours |
| PITR | up to 35 days |
| On-demand price | 0.625 per million writes, 0.125 per million reads |
| Auto scaling target | 70 % |
| Burst | about 5 minutes of unused capacity |
| Switch to on-demand | 4 times per 24 hours |

## When to choose it

- Known access patterns, huge scale, predictable low latency: shopping carts, sessions, game state, IoT and metadata lookups.
- Serverless apps (Lambda) that cannot hold database connections: DynamoDB uses HTTP, so there is no connection limit.
- You need multi-Region active-active writes: global tables.
- Unknown or spiky traffic: on-demand. Steady traffic you can predict: provisioned with auto scaling, then reserved capacity.
- Not for ad-hoc queries, many joins or analytics. Choose RDS or Aurora for those (note 05).

## Exam traps

- A **Scan** with a filter is not cheap: you pay for everything read.
- **Strongly consistent reads** are not available on GSIs. Global tables also cannot promise them across Regions under MREC.
- You **cannot add an LSI** after the table exists. You can add a GSI any time.
- A **GSI throttle** slows base table writes on a provisioned table.
- Eventual-consistent reads cost **half**. Transactions cost **double**.
- Capacity is rounded **up per item**: ten 1.1 KB writes are 20 write units, not 11.
- A hot partition throttles while the table total looks fine.
- TTL deletion is **not on time**; expired items can still appear in reads.
- DynamoDB Streams keep 24 hours. A Lambda consumer that is down for two days loses records.
- Optimistic locking uses a **condition**, not a lock. Losers get an exception and retry.
- DAX cannot speed strongly consistent reads (note 04).

## Cost angle

- On-demand wins when average utilisation of what you would provision is low (below the break-even); provisioned wins when it is high and steady.
- Storage: 0.25 USD per GB-month (first 25 GB free); Standard-IA 0.10 USD per GB-month with higher request prices.
- PITR costs 0.20 USD per GB-month. On-demand backups cost 0.10 USD per GB-month; restores 0.15 USD per GB.
- Strongly consistent reads cost double an eventual one. Smaller items cost fewer units: store big blobs in S3 and keep the pointer in DynamoDB.
- Every GSI repeats the item (write units and storage). Project only what you need.
- Global tables replicate writes: each replica Region pays replicated write units (0.625 USD per million, on-demand; the price was cut in 2024-11).
- Free tier: first 25 GB storage, 25 provisioned WCU and 25 RCU.

## Comparison

| | GSI | LSI |
|---|---|---|
| Partition key | Different from the table | Same as the table |
| Sort key | Optional, different | Required, different |
| Create after table exists | Yes | No |
| Strong reads | No | Yes |
| Capacity | Own | Shared with table |
| Item-collection limit | None | 10 GB per partition key |
| Quota | 20 | 5 |
| Use for | A new access pattern by another attribute | Another sort order inside the same partition |

Now do drill 01 (capacity units), drill 02 (on-demand or provisioned?), drills 03–05 (key design, locking, TTL and backups).

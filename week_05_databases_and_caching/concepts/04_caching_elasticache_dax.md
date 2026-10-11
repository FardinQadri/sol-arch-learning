Exam tasks: 3.3, 4.3

# 04 — Caching: ElastiCache, DAX and MemoryDB

## What it is

A **cache** keeps copies of hot data in fast memory so most reads never reach the database. It lowers latency, takes load off
the database and often lets you run a smaller (cheaper) database. The price is **stale data** and one more thing to run.

AWS has three caching answers:

- **Amazon ElastiCache**: managed in-memory data store for any app. Engines: **Valkey**, **Redis OSS** and **Memcached**.
- **DAX** (DynamoDB Accelerator): a cache built only for DynamoDB. No app logic needed beyond swapping the client.
- **MemoryDB**: an in-memory database that is **durable**, so it can be the system of record, not just a cache.

Exam tasks: **3.3** "caching strategies and services (for example, Amazon ElastiCache)" and "integrating caching to meet business
requirements"; **4.3** fewer database reads means a cheaper database.

## How it works

### ElastiCache engines

- **Valkey** (changed: added, and listed first on the docs page) is the open-source Redis fork. It is compatible with Redis OSS clients, and **cheaper**: node price is 80 % of Redis OSS.
- **Redis OSS**: the older engine; replication, failover, backups, pub/sub, sorted sets, geospatial.
- **Memcached**: the simplest. Multi-threaded, simple values, scale out with more nodes. **No replication, no persistence, no Multi-AZ failover** (node-based). Clients spread keys over nodes with consistent hashing. Auto Discovery finds the nodes.

Two ways to run it (changed: Serverless is new):

| | Node-based cluster | Serverless |
|---|---|---|
| You choose | Node type, node count, AZs, patch time | Nothing; it scales on memory, compute and network |
| Setup | Minutes | "In under a minute" |
| Pay | Per node-hour | Per GB-hour of data plus ECPUs |
| Fits | Steady, predictable load | Spiky or unknown load |

### Cluster mode and high availability (Valkey and Redis OSS)

- **Cluster mode disabled:** one **shard**: one primary plus 0 to 5 read replicas. Replication is asynchronous.
- **Cluster mode enabled:** 1 to **500 shards**, each with a primary and 0 to 5 replicas. Data is partitioned across shards, so you scale **writes** and memory, not just reads. Clients use a configuration endpoint.
- **Multi-AZ with automatic failover:** put replicas in other AZs. If the primary fails, the replica with the least lag is promoted, usually in a few seconds. The primary endpoint name stays the same. A tiny amount of data can be lost (asynchronous).
- Without replicas a failed primary is replaced empty, so data is lost unless you restore a snapshot.
- Global Datastore replicates across Regions for Valkey and Redis OSS.
- Memcached clusters have 1 to 60 nodes. A failed node loses its keys.

### Security and backups

- **At rest:** encryption is on for serverless and available on node-based clusters, but only **at creation**. To add it to an existing cluster, back it up and restore into a new encrypted one.
- **In transit:** TLS between clients and nodes. Always on for serverless.
- **Authentication:** IAM authentication, the Valkey/Redis **AUTH** command (a password or token), and **RBAC** (users and access strings) for authorization.
- It lives in your VPC. Control access with security groups.
- **Backups:** snapshots to S3 for Valkey, Redis OSS and serverless Memcached. Up to 35 days of automatic backups; 0 disables them. Restore creates a new cache. **Node-based Memcached has no backups.**

### Which one for which database

| Database behind it | Cache | Why |
|---|---|---|
| RDS or Aurora | ElastiCache (Valkey/Redis OSS) | Your code decides what to cache and when |
| DynamoDB | DAX | Same API; cached reads and write-through come built in |
| Nothing (it is the store) | MemoryDB | Durable, so no second database is needed |

### Caching strategies

| Strategy | How it works | Good | Bad |
|---|---|---|---|
| **Lazy loading** (cache-aside) | App checks the cache. On a miss it reads the DB and writes the result to the cache | Only requested data is cached; a cache node failure is not fatal | A miss costs three trips; data can go **stale** |
| **Write-through** | Every DB write also updates the cache | The cache is never stale | Write penalty (two writes); data that is never read fills the cache; a new node starts empty |
| **TTL** | Each key expires after N seconds | Limits staleness and clutter | Too short: many misses; too long: stale |

The usual answer is the **combination**: lazy loading plus write-through, with a TTL on everything. Write-through keeps hot data fresh,
lazy loading fills gaps (new nodes, evictions), and the TTL cleans up. Reading from **replicas** adds read capacity. Drill 06 simulates this.

Common uses: database query results, rendered pages, leaderboards (sorted sets), rate limits, and **session stores** (keep user sessions in
the cache so web servers stay stateless and any server can serve any user).

### A worked example: what a hit rate buys

Say an app makes 1,000 reads per second and the cache answers 90 % of them. The database now sees 100 reads per second instead of 1,000.
That is a tenth of the load. If the database is DynamoDB, it is a tenth of the read units. If it is RDS, it may be a smaller instance.
The same cache with a 50 % hit rate only halves the load. So a cache pays off for **repeated reads of the same keys** and does little for
data that is read once. Pick the TTL to match how much staleness the business accepts: a product page can be a minute old, an account balance cannot.

### DAX

DAX is a cluster of nodes in your VPC. You change the DynamoDB client to the DAX client; the app code stays the same.
AWS describes the speed as microsecond response for cached reads (cache hits).

- **Item cache** (GetItem, BatchGetItem) and **query cache** (Query, Scan result sets).
- **Write-through:** PutItem, UpdateItem, DeleteItem and BatchWriteItem pass through DAX to the table and update the cache.
- **Eventually consistent reads** are served from the cache. **Strongly consistent reads** pass straight through to DynamoDB and are **not cached**, so DAX does not speed them.
- The item cache TTL defaults to **5 minutes**. Least-recently-used eviction is always on.
- A cluster has one primary node plus 0 to 10 replicas (spread over AZs for availability); 50 nodes per account per Region.
- DAX is for **read-heavy, repeated reads** of the same keys. It does not help write-heavy or random-key workloads.
- Writes that arrive through global-table replication bypass DAX, so cached values can be stale until the TTL ends.

### MemoryDB

MemoryDB stores data in memory **and** in a multi-AZ transactional log, so it survives node failure with no loss.
Reads take microseconds, writes single-digit milliseconds. It is Valkey and Redis OSS compatible. Use it as a **primary database**
for fast workloads (leaderboards, session state you cannot lose, real-time inventory). ElastiCache is a cache in front of another database.

## Numbers to know

| Fact | Value |
|---|---|
| Cluster mode disabled | 1 shard, 0–5 replicas |
| Cluster mode enabled | 1–500 shards, 0–5 replicas each |
| Memcached cluster | 1–60 nodes |
| ElastiCache failover | typically a few seconds |
| Backup retention | up to 35 days |
| DAX item cache TTL | 5 minutes default |
| DAX nodes | 1 primary + 0–10 replicas |
| Valkey vs Redis OSS node price | 80 % |
| MemoryDB | microsecond reads, single-digit ms writes |

## When to choose it

- **Read-heavy, repeated reads, tolerant of slightly old data:** a cache in front of RDS or Aurora (ElastiCache) or DynamoDB (DAX).
- **DynamoDB with hot keys read thousands of times:** DAX, because it needs no code design.
- **Complex data structures, replication, persistence of snapshots, Multi-AZ:** Valkey or Redis OSS.
- **Simple, multi-threaded string cache you can lose:** Memcached.
- **Sessions or data that must survive and be fast:** MemoryDB (or Valkey/Redis with Multi-AZ and backups if loss is acceptable).
- **Unknown or spiky demand and no wish to size nodes:** ElastiCache Serverless.
- Do not use a cache when every read must be the latest committed value.

## Exam traps

- **DAX only works with DynamoDB.** For RDS the answer is ElastiCache.
- DAX does **not** cache strongly consistent reads.
- Lazy loading alone can serve **stale** data. Write-through alone fills the cache with data nobody reads. The balanced answer is both with a TTL.
- Memcached has no replication, no failover and no backups. If the question says "highly available" or "persistent", it is Valkey/Redis or MemoryDB.
- ElastiCache is a **cache**, so it does not replace the database. MemoryDB can.
- Cluster mode **enabled** scales writes; replicas in a disabled cluster only scale reads.
- Encryption at rest on a node-based cluster must be chosen at creation.
- A cache node failure with lazy loading is not fatal: the app falls back to the database.
- Cached results cannot give the very latest data. If the requirement is "always current", do not cache.

## Cost angle

- Caching cuts database cost: fewer reads means a smaller instance or fewer DynamoDB read units. One 4 KB strongly consistent read is a whole read unit; a cache hit is free of units.
- Node prices (illustrative): `cache.t4g.micro` is 0.0128 USD/hour for Valkey and 0.016 for Redis OSS or Memcached; `cache.m7g.large` is 0.1264 against 0.158. **Valkey is 20 % cheaper** for the same node.
- Serverless storage is 0.084 USD per GB-hour (Valkey) against 0.125 (Redis OSS and Memcached); ECPUs 0.0023 against 0.0034 per million. Valkey is also cheaper there.
- Node-based clusters bill every hour. Delete lab caches. Replicas and Multi-AZ multiply nodes.
- DAX `dax.t3.small` is 0.04 USD per node-hour. A production cluster runs several nodes across AZs, which is a fixed monthly cost. It pays off only when it removes many reads.
- Snapshot storage is 0.085 USD per GB-month beyond the free allocation.
- Reserved nodes and Database Savings Plans can lower steady-use cost (rates not in this course).

## Comparison

| | ElastiCache Valkey / Redis OSS | ElastiCache Memcached | DAX | MemoryDB |
|---|---|---|---|---|
| Works in front of | Any database | Any database | DynamoDB only | Nothing; it is the database |
| Durable | Snapshots; optional replication | No | No (cache) | Yes, multi-AZ log |
| Replication / failover | Yes, Multi-AZ | No | Yes (replica nodes) | Yes |
| Data model | Rich types, sorted sets, pub/sub | Simple key-value | DynamoDB items and queries | Valkey/Redis types |
| Needs code change | Yes (cache logic) | Yes | Swap the client | Yes (use as DB) |
| Backups | Yes | Serverless only | n/a | Yes |

Now do drill 06 (cache it right) and revisit drill 01 to see which reads a cache would save.

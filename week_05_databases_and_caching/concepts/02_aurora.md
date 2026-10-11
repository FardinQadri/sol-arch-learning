Exam tasks: 3.3, 2.2, 4.3

# 02 — Amazon Aurora

## What it is

**Aurora** is AWS's own relational engine, compatible with **MySQL** and **PostgreSQL**. It lives inside the RDS service
(same console, same CLI family) but it is built differently: the database engine and a **shared, distributed storage volume** are separate.

Exam tasks:

- **3.3** "determining an appropriate database type (for example, Amazon Aurora, Amazon DynamoDB)", read replicas, serverless.
- **2.2** failover and disaster recovery across AZs and Regions.
- **4.3** "cost-effective AWS database services … serverless", storage and I/O pricing.

## How it works

### Architecture

- One **cluster volume**: a single virtual SSD volume with copies of your data across **three AZs** in one Region.
- Data is replicated synchronously to **six storage nodes**. The amount of replication does not depend on how many instances you run.
- The volume **grows by itself** and shrinks when data is removed. You pay for the space you use. There is no storage size to pick.
- Maximum cluster volume: **256 TiB** on current engine versions (changed: it was 128 TiB; older versions are still at 128 TiB). Per-table limits: 64 TiB Aurora MySQL, 32 TiB Aurora PostgreSQL.
- Storage heals itself. Losing a copy or a node does not need a restore.
- Compute is a set of **instances** attached to the volume: one **writer** and up to **15 Aurora Replicas**.
- Replicas read the **same volume**, so lag is usually much less than **100 milliseconds**. Replicas are called asynchronous, but no data is copied between instances: they share the volume.

### Failover

- If the writer fails, Aurora promotes a replica. Service is typically back in under **60 seconds**, often under 30.
- No replica? Aurora rebuilds the writer in the same AZ, typically in under 10 minutes. That is why production wants at least one replica in another AZ.
- **Failover priority:** each replica has a tier from 0 (first) to 15 (last). Same tier: the largest instance wins. Changing a tier does not cause a failover.
- RDS Proxy cuts failover time by up to 66 %.

### Endpoints

| Endpoint | Points to | Use it for |
|---|---|---|
| **Cluster** (writer) | The current writer, always | Writes and general connections |
| **Reader** | Load-balances across the replicas | Read-only traffic |
| **Custom** | A subset you choose (up to 5 per cluster) | Send reporting to big replicas, web reads to small ones |
| **Instance** | One specific instance | Diagnosis. Does **not** follow failover |

Use the cluster endpoint in apps. Never hard-code an instance endpoint for writes: after failover it may be a reader.

### Aurora Serverless v2

Aurora Serverless v2 scales compute in **ACUs** (Aurora capacity units; one ACU is about 2 GiB of memory plus CPU and network).

- Range: from 0.5 ACU up to **256 ACUs** on current versions. Steps as small as 0.5 ACU. Processing does not pause while it scales.
- **Scale to 0** (changed, 2024-11): set the minimum to 0 and the cluster auto-pauses after an idle time (default 300 seconds, up to one day). No instance charge while paused. Storage still bills. Resume takes about 15 seconds.
- Auto-pause is blocked by open connections, an attached RDS Proxy, and the primary cluster of a Global Database.
- You can mix provisioned and serverless instances in one cluster, and have up to 15 serverless readers.
- Billing is per ACU-hour, measured per second.
- Aurora Serverless v1 is retired (end of life 2025-03-31). Older material that teaches "v1 pause and resume" is out of date.
- Names are moving: current docs call v2 "Aurora serverless". The exam still says Serverless v2.

### Global Database

One **primary Region** and up to **10 read-only secondary Regions** (changed: the current page says 10; the older, smaller limit is not
confirmed in the docs). Replication is at the **storage level** on dedicated infrastructure, normally under a second.

- Secondary clusters give low-latency reads close to users and a ready DR site.
- **RPO** is typically measured in seconds. **RTO** is in the order of minutes.
- **Switchover** (planned, no data loss, RPO 0, typically under 30 seconds on current versions) vs **failover** (unplanned, may lose unreplicated writes because replication is asynchronous).
- A **global writer endpoint** follows the primary across Regions.
- **Write forwarding** (changed, newer): an app can send writes to a secondary cluster. It forwards the SQL to the primary and the result replicates back.
- PostgreSQL has `rds.global_db_rpo` to bound lag: writes block if every secondary falls too far behind.
- No Backtrack on a global database, and no Aurora Auto Scaling on secondary clusters.

### Backtrack and cloning

- **Backtrack** rewinds an Aurora **MySQL** cluster in place, without restoring a backup. Up to **72 hours**. It only works on clusters created with Backtrack enabled. It is not a backup replacement. Aurora PostgreSQL has no Backtrack.
- **Cloning** makes a new cluster using copy-on-write. The clone shares data pages with the source and only stores what changes. It is fast and cheap. Up to 15 copy-on-write clones. Same Region only.
- Use a clone to test a migration or run a heavy report on production data without touching production.
- Aurora PITR and snapshots still exist, like RDS.

### Standard and I/O-Optimized

| Configuration | You pay | Best when |
|---|---|---|
| **Standard** | Per 1 million I/O requests (0.20 USD), storage 0.10 USD per GB-month | I/O is **under 25 %** of your Aurora bill |
| **I/O-Optimized** | No I/O charge. Higher instance price (0.359 against 0.276 USD/hour for `db.r7g.large`) and storage 0.225 USD per GB-month | I/O is **25 % or more** of the bill |

You can move from Standard to I/O-Optimized **once per 30 days**. You can move back to Standard at any time.

### Newer members (one line each)

- **Aurora DSQL** (changed, newer): serverless, distributed, PostgreSQL-compatible, active-active across Regions; 99.99 % in one Region, 99.999 % multi-Region.
- **Aurora PostgreSQL Limitless Database** (changed, newer): automatic horizontal scaling for millions of writes per second, using shard groups.

## Numbers to know

| Fact | Value |
|---|---|
| Copies of data | 6, across 3 AZs |
| Aurora Replicas per cluster | up to 15 |
| Replica lag | usually well under 100 ms |
| Failover | typically under 60 s, often under 30 s |
| Promotion tiers | 0 (first) to 15 |
| Custom endpoints | 5 per cluster |
| Cluster volume | up to 256 TiB (older 128 TiB) |
| Serverless v2 | 0 (scale to 0) or 0.5 to 256 ACUs |
| Auto-pause idle time | 300 s default, up to 86,400 s |
| Global Database secondaries | up to 10 Regions |
| Backtrack | MySQL only, up to 72 hours |
| Clones | 15 copy-on-write, same Region |
| I/O-Optimized switch | once per 30 days |
| Break-even I/O share | 25 % of the Aurora bill |

## When to choose it

- You want **RDS-style SQL** with faster failover, up to 15 replicas and storage that grows by itself.
- Read-heavy workload that needs many low-lag replicas.
- **Unpredictable or intermittent** load: Serverless v2 (dev and test databases can scale to 0).
- A global audience or a Region-level DR target with an RPO of seconds: Global Database.
- Fast test copies of production: cloning.
- Stay on plain RDS when the database is small and steady, you need an engine Aurora lacks (Oracle, SQL Server, MariaDB, Db2), or cost matters more than speed of failover.

## Exam traps

- Aurora replicas read the **shared volume**. They are not separate copies like RDS read replicas, so lag is tiny.
- A **Multi-AZ DB cluster** (RDS) is not Aurora, even though both have readable replicas.
- Aurora storage is **six copies in three AZs** whatever the number of instances. A single-instance Aurora cluster is still durable, but not highly available.
- The reader endpoint balances **connections**, not individual queries.
- An instance endpoint does not follow failover. Use the cluster endpoint.
- Backtrack is Aurora MySQL only and must be enabled at creation. It is not for Regional DR.
- Global Database is for **Region** failure and global reads. For AZ failure, ordinary replicas already cover it.
- Aurora Serverless v1 is retired. If an option says "v1", it is the wrong choice.
- Auto-pause is not available while an RDS Proxy is attached.
- Cross-Region failover is not lossless: replication is asynchronous. Only a planned switchover has RPO 0.

## Cost angle

- Aurora instances cost more than the same RDS class: `db.r7g.large` is 0.276 USD/hour (Standard) against 0.239 for RDS PostgreSQL Single-AZ, and 0.359 for I/O-Optimized (illustrative).
- You do not pay for a standby you cannot read. Each replica is a working reader, but it is a full instance price.
- Standard I/O is 0.20 USD per million requests. A chatty application can make I/O the biggest line. That is when I/O-Optimized wins (I/O at or above 25 % of the bill).
- Serverless v2 costs 0.12 USD per ACU-hour (Standard) or 0.16 (I/O-Optimized). A steady load is cheaper on provisioned instances with a reservation. A spiky or idle one is cheaper serverless.
- Global Database adds 0.20 USD per million replicated write I/Os plus the secondary instances.
- Backup storage beyond the free allocation is 0.021 USD per GB-month.
- Clones cost almost nothing until they diverge.

## Comparison

| | RDS (Multi-AZ instance) | Aurora |
|---|---|---|
| Storage | EBS volume per instance, you choose size and type | Shared cluster volume, auto-grows, 6 copies in 3 AZs |
| Max size | 64 TiB (256 TiB Oracle, SQL Server) | 256 TiB on current versions |
| Read replicas | Up to 15, asynchronous, own copy | Up to 15, shared storage, lag usually under 100 ms |
| Failover | Typically 60–120 s | Typically under 60 s, often under 30 s |
| Cross-Region | Cross-Region read replica | Global Database (up to 10 secondary Regions) |
| Serverless | No | Serverless v2 (scales to 0) |
| Engines | MySQL, MariaDB, PostgreSQL, Oracle, SQL Server, Db2 | MySQL and PostgreSQL compatible |
| Price | Lower per instance | Higher per instance, plus I/O unless I/O-Optimized |

Now do drill 09 (HA, read scale or DR?) and drill 10 (the right engine).

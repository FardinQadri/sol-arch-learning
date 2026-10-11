Exam tasks: 3.3, 2.2, 4.3

# 05 — Choosing a database

## What it is

AWS does not push one database for everything. It offers **purpose-built databases**: each is shaped for one kind of data and one
kind of question. The exam gives you a workload and asks you to pick. This note is the map, plus the rules that decide
between look-alike answers.

Exam tasks: **3.3** "determining an appropriate database type", **2.2** high availability and DR for databases (and "proxy concepts"),
**4.3** "determining cost-effective AWS database services with appropriate use cases" (DynamoDB compared with RDS, serverless,
time series, columnar).

## How it works

### The purpose-built map

| Data and question | Type | AWS service |
|---|---|---|
| Tables, joins, transactions, SQL | Relational | RDS, Aurora |
| Lookups by key at any scale, single-digit ms | Key-value / document | DynamoDB |
| JSON documents, MongoDB drivers | Document | DocumentDB |
| Huge key-based tables, Cassandra apps | Wide-column | Keyspaces |
| Relationships: friends, fraud rings, knowledge graphs | Graph | Neptune |
| Microsecond reads, caches, leaderboards | In-memory | ElastiCache, MemoryDB, DAX |
| Full-text search, log analytics, dashboards | Search | OpenSearch Service |
| Metrics over time | Time series | Timestream for InfluxDB |
| Big analytical scans over columns | Columnar warehouse | Redshift (later week) |

Three retired entries you may still see in older material: Amazon QLDB (ledger database) is retired, shut down 2025-07-31.
Timestream for LiveAnalytics is retired for new customers (closed 2025-06-20); AWS points new users to Timestream for InfluxDB.
Aurora Serverless v1 is retired too (end of life 2025-03-31); use Serverless v2.

### One paragraph each

- **DocumentDB**: MongoDB-compatible, fully managed document database. Six copies of data across three AZs, one writer plus up to 15 replicas, storage up to 256 TiB on current engines (older 128 TiB). Point-in-time recovery up to 35 days. Choose it to move a MongoDB app with few code changes.
- **Neptune**: managed graph database (Gremlin, openCypher, SPARQL). One writer plus up to 15 replicas on a shared volume across AZs, designed for more than 99.99 % availability. Choose it for recommendations, fraud detection and knowledge graphs, where queries follow many hops of relationships (a relational self-join would crawl).
- **Keyspaces**: serverless, Apache Cassandra-compatible (CQL). Choose it to run Cassandra workloads with no cluster to manage.
- **OpenSearch Service**: managed OpenSearch (and old Elasticsearch up to 7.10). Search, log analytics, real-time monitoring and clickstream analytics. It is usually a **secondary** index fed from the main database, not the system of record.
- **MemoryDB**: durable in-memory, Valkey/Redis compatible. Microsecond reads, a multi-AZ transaction log. The primary database for a fast workload (note 04).

### Five quick scenarios

1. A ride-sharing app stores the latest position of each driver and reads it by driver id thousands of times a second: **DynamoDB** (key lookups, scale), with **DAX** if the same keys are read repeatedly.
2. A finance team runs month-end reports with many joins on 2 TB of orders: **Aurora** or **RDS PostgreSQL** with a read replica for the reports.
3. A social app asks "friends of friends who like this band": **Neptune**. The same question in SQL needs deep self-joins.
4. A support site needs typo-tolerant search across millions of articles: **OpenSearch Service**, fed from the main database.
5. A game keeps a live leaderboard that must survive a node failure: **MemoryDB** (sorted sets, durable). If losing it is acceptable, ElastiCache is cheaper.

Ask three questions in order: what is the **shape** of the data, what is the **main query**, and what happens if it is **lost or slow**?

### HA, read scale or DR: the decision table

Match the **requirement word** to the feature. These are new scenarios, not drill ones.

| Scenario | Use | Why |
|---|---|---|
| A MySQL database must survive an AZ outage, with no reads needed on the standby | RDS Multi-AZ DB instance | Synchronous standby, same endpoint, failover typically 60–120 s |
| Same, but the standbys should also serve reads and failover should be faster | RDS Multi-AZ DB cluster | Two readable standbys, failover typically under 35 s |
| A reporting team's queries slow the main database | RDS read replica | Offload reads. Asynchronous, so reports may lag |
| Product pages in Asia need local reads of an Aurora database in us-east-1 | Aurora Global Database (secondary Region) | Storage-level replication, usually under a second |
| A compliance rule needs a copy in another Region for DR; the database is RDS PostgreSQL | Cross-Region read replica (promote on disaster) | RDS has no Global Database |
| Aurora needs 8 readers in one Region with tiny lag | Aurora Replicas | Share the volume, up to 15 |
| 2,000 short Lambda runs exhaust connections | RDS Proxy | Pools connections; also shortens failover |
| A bad deploy deleted rows an hour ago | Point-in-time restore to a new instance (Aurora MySQL could Backtrack) | HA copies replicate the delete too |
| Survive the loss of a whole Region with a few seconds of data loss | Aurora Global Database or DynamoDB global table | Cross-Region replication, RPO seconds |
| Zero data loss across Regions on DynamoDB | MRSC global table | Synchronous, RPO zero |

Three rules cover most questions:

1. **High availability** inside a Region = **Multi-AZ** (RDS) or Aurora replicas. Synchronous standby for RDS instance Multi-AZ.
2. **Read scale** = replicas, or a **cache**. A Multi-AZ instance standby never serves reads.
3. **Disaster recovery in another Region** = cross-Region replica, Global Database, global table or copied backups. The RPO and RTO in the
   question choose which: seconds of RPO means replication; hours means backups.

### Lambda and databases: connection maths

Every running Lambda copy opens its own database connection. Concurrency is requests per second times duration:
**concurrency = rate x seconds** (Little's law). 300 requests/s lasting 0.5 s need 150 concurrent runs, so 150 connections.
RDS PostgreSQL's default `max_connections` is `LEAST(DBInstanceClassMemory / 9531392, 5000)`. A 4 GiB instance gets about 450 (the real
figure is a bit lower). MySQL: `DBInstanceClassMemory / 12582880`. If connections beat `max_connections`, new ones are refused.

**RDS Proxy** keeps a pool of database connections and multiplexes many Lambda connections onto them. It also works for any app
without its own pooling, takes IAM or Secrets Manager credentials, and shortens failover. Alternatively use DynamoDB, which has no
connection limit. Drill 07 does this arithmetic.

### Database Savings Plans

Database Savings Plans exist (changed, newer) as a spend commitment for database usage. Reserved Instances/nodes and reserved DynamoDB capacity are the older equivalents. This course does not use their discount rates.

## Numbers to know

| Fact | Value |
|---|---|
| Aurora / DocumentDB / Neptune replicas | up to 15 per cluster |
| DocumentDB / Aurora copies of data | 6, across 3 AZs |
| DynamoDB item | 400 KB |
| RDS Multi-AZ failover | 60–120 s (instance), under 35 s (cluster) |
| Aurora failover | typically under 60 s |
| DocumentDB PITR | up to 35 days |
| Max RDS storage | 64 TiB (MySQL, MariaDB, PostgreSQL, Db2) |
| Aurora Global Database | up to 10 secondary Regions |
| Instance quota | 40 per Region (RDS, Aurora, Neptune, DocumentDB together) |

## When to choose it

Start from the **access pattern**, not the product:

- Many joins, ad hoc SQL, strict transactions: **relational**.
- You can list every query in advance and need huge scale: **DynamoDB**.
- Reads of the same data over and over: add a **cache**.
- Free-text queries: **OpenSearch**. Relationship traversal: **Neptune**.
- Existing MongoDB or Cassandra code: **DocumentDB** or **Keyspaces**.
- Unknown or idle-heavy load, and SQL: **Aurora Serverless v2**. Same, but key-value: **DynamoDB on-demand**.
- Migrating: same engine = homogeneous (simple, DMS or native tools); different engine = heterogeneous (convert the schema first).

## Exam traps

- "Relational with global low-latency reads and fast cross-Region DR" = Aurora Global Database, not RDS Multi-AZ.
- "Millions of requests a second, simple lookups, no ops" = DynamoDB, not Aurora.
- "Graph" or "relationships between millions of nodes" = Neptune. Do not pick DocumentDB because it is "NoSQL".
- "MongoDB-compatible" = DocumentDB. "Cassandra" = Keyspaces.
- Search is **OpenSearch**, not DynamoDB scans.
- A cache is not a database: MemoryDB is the durable in-memory one.
- Read replicas do not provide automatic failover on RDS. Multi-AZ does.
- RDS Proxy reduces connections and failover time; it does not scale writes.
- Time series: Timestream for InfluxDB. LiveAnalytics is retired for new customers, so it is the wrong answer for a new design.
- Aurora is not always the cheaper choice. A small steady RDS database is cheaper.

## Cost angle

- **RDS**: pay for instance hours (doubled by Multi-AZ), storage and backups beyond the free allocation. Predictable, good for steady load. Idle instances still bill.
- **Aurora**: higher per-instance price but fewer replicas needed for the same read scale. Standard pays 0.20 USD per million I/Os; I/O-Optimized has none and wins when I/O is 25 % or more of the bill. Serverless v2 can scale to 0.
- **DynamoDB**: no idle instance. On-demand costs 0.625 USD per million writes and 0.125 per million reads. Provisioned wins when utilisation passes the break-even.
- A cache or DAX in front can cut read costs more than any instance change.
- Overpaying pattern: Multi-AZ for dev, read replicas nobody reads, Provisioned IOPS for a quiet database, on-demand for a flat steady load, a graph or search engine used as the main store.
- A DynamoDB table with many GSIs repeats writes in every index.

## Comparison

| Need | Pick | Not this |
|---|---|---|
| Relational, steady, cost-sensitive | RDS | Aurora (costs more per instance) |
| Relational, many replicas, fast failover, global | Aurora | RDS Multi-AZ instance |
| Key lookups at massive scale | DynamoDB | RDS |
| Cache in front of RDS/Aurora | ElastiCache | DAX |
| Cache in front of DynamoDB | DAX | ElastiCache (more code) |
| Durable in-memory primary | MemoryDB | ElastiCache |
| MongoDB compatible | DocumentDB | DynamoDB |
| Cassandra compatible | Keyspaces | DynamoDB |
| Graph | Neptune | RDS with joins |
| Search / logs | OpenSearch Service | DynamoDB Scan |
| Time series | Timestream for InfluxDB | RDS |
| Lambda with a relational database | RDS Proxy | Bigger instance only |

Now do drill 10 (the right engine), drill 09 (HA, read scale or DR?) and drill 07 (too many connections).

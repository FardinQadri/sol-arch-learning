# Week 05 — Databases and caching: RDS, Aurora, DynamoDB, ElastiCache, DAX and purpose-built databases

## Goals

By the end of this week you can:

1. Choose RDS features for high availability, read scale and disaster recovery: Multi-AZ, read replicas, backups and RDS Proxy.
2. Say when Aurora is worth its price: shared storage, replicas, Serverless v2, Global Database and the I/O-Optimized rule.
3. Size and price a DynamoDB table: capacity units, consistency, on-demand or provisioned, and the break-even.
4. Design DynamoDB keys for a list of access patterns: partition and sort keys, GSI or LSI, Query not Scan.
5. Add a cache with the right strategy: lazy loading, write-through and TTL, on ElastiCache, DAX or MemoryDB.
6. Pick the right purpose-built database for a workload and defend the choice on cost.

## Your week

About 10–12 hours. Do the steps in order.

1. Concept notes 01–05 and the two demos in `concepts/` (~3 h). Run the demos:
   `python concepts/demo_dynamodb_in_moto.py` and `python concepts/demo_database_math.py`.
2. Drills: `python practice/exercises.py` (~3–4 h). Drills 01, 02, 06 and 07 are small models you build yourself:
   capacity units, on-demand against provisioned, a cache simulator and connection maths. Drills 03–05 and 08 use boto3
   against a fake AWS. Drills 09 and 10 are decisions. Do them in order.
3. Quiz: `python quiz.py --week 5 -n 30` until you score 80 % or more (~1.5 h).
4. Milestone M05: the course project's data tier (~2–3 h). See `course_project/milestones/M05.md`.
5. Optional lab (~1–1.5 h, a few cents): `lab/LAB.md`. A DynamoDB table and one small RDS PostgreSQL instance, then clean up.

## Exam tasks covered

| Task | Title |
|---|---|
| 2.2 | Design highly available and/or fault-tolerant architectures |
| 3.3 | Determine high-performing database solutions |
| 4.3 | Design cost-optimized database solutions |

Task 3.3 is the main target: replicas, engines, capacity planning, connections and proxies, caching. Task 2.2 appears through
Multi-AZ, Global Database, backups and failover. Task 4.3 is the cost of each choice: capacity units, serverless, instance size.

## Service comparison

| Service | Type | Scales by | Fails over | Use it when |
|---|---|---|---|---|
| RDS | Relational (6 engines) | Bigger instance, read replicas | Multi-AZ, typically 60–120 s (cluster: under 35 s) | Standard SQL app, steady load |
| Aurora | Relational (MySQL/PostgreSQL-compatible) | Up to 15 replicas, Serverless v2 | Typically under 60 s | Read-heavy, fast failover, global reads, spiky load |
| DynamoDB | Key-value / document | Partitions, automatic | Built in across 3 AZs; global tables for Regions | Known access patterns, huge scale, serverless |
| ElastiCache | In-memory (Valkey, Redis OSS, Memcached) | Shards and replicas, or Serverless | Multi-AZ replica promotion in seconds | Cache in front of a database; sessions |
| DAX | In-memory cache for DynamoDB | Up to 10 replica nodes | Replica nodes | Repeated eventually consistent reads on DynamoDB |
| DocumentDB | Document (MongoDB-compatible) | Up to 15 replicas | Replica promotion | MongoDB apps on AWS |
| Neptune | Graph | Up to 15 replicas | Replica promotion | Relationship queries, fraud, recommendations |

## Interview questions

Answer each out loud in under two minutes.

1. What is the difference between a Multi-AZ deployment and a read replica?
2. How do you encrypt an RDS database that is already running unencrypted?
3. When would you pay for Aurora instead of RDS?
4. DynamoDB: how do you pick a partition key, and what is a hot partition?
5. How many read units does a 9 KB strongly consistent read cost, and why?
6. On-demand or provisioned capacity? How do you decide?
7. GSI or LSI? What can you not change after the table exists?
8. Lazy loading or write-through? What does a TTL add?
9. Lambda keeps exhausting your database connections. What do you do?
10. Your team wants a graph, a search box and a leaderboard. Which databases, and why not one?

Now you may read `_harness/awslib/dynamo.py`, `caching.py` and `dbmath.py` — compare them with your drills 01, 02, 06 and 07.

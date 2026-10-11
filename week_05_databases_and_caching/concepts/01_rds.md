Exam tasks: 3.3, 2.2, 1.3

# 01 — Amazon RDS

## What it is

**Amazon RDS** runs a relational database for you. You pick an engine, an instance class and a disk. AWS builds
the instance, patches it, backs it up and replaces failed hardware. You do not get a shell on the host.

Three exam tasks lean on this note:

- **3.3** "configuring read replicas to meet business requirements", "database connections and proxies", capacity planning (instance types, Provisioned IOPS).
- **2.2** failover strategies, disaster recovery, "proxy concepts (for example, Amazon RDS Proxy)".
- **1.3** (secure workloads) fits the encryption, IAM authentication and password-management parts below.

Engines today: Db2, MariaDB, MySQL, PostgreSQL, Oracle and Microsoft SQL Server (changed: Db2 is the newer one).
Aurora is a separate engine family with its own storage (note 02).

### What AWS manages and what you still own

| AWS manages | You still own |
|---|---|
| Hardware, host OS patching, engine patching in the maintenance window | Schema, queries, indexes, parameter tuning |
| Automated backups and point-in-time recovery | Choosing the retention period and testing a restore |
| Multi-AZ failover when you switch it on | Choosing Multi-AZ, replicas and instance size |
| Encryption machinery (KMS) | Turning encryption on at creation; security groups; who can connect |

RDS Custom is the exception: it gives access to the OS and database, for Oracle and SQL Server only.

## How it works

### Instance classes and storage

Class families: general purpose (`db.m`), memory optimized (`db.r`, `db.x`, `db.z`), compute optimized (`db.c`)
and burstable (`db.t`). Newer names such as `db.m8g` and `db.r8g` exist. Treat generations as examples.
Burstable `db.t4g` classes run in Unlimited mode: they can burst past baseline for an extra charge.

| Storage type | Use it for |
|---|---|
| gp3 (General Purpose SSD) | The default choice. Baseline 3,000 IOPS and 125 MiB/s under 400 GiB; 12,000 IOPS and 500 MiB/s from 400 GiB |
| gp2 | Previous generation. 3 IOPS per GiB, minimum 100 IOPS. gp3 is recommended instead |
| io2 Block Express / io1 (Provisioned IOPS) | I/O-heavy production OLTP. io2 goes to 256,000 IOPS, sub-millisecond latency |

Magnetic storage is deprecated (changed): you cannot create new magnetic instances.
Provisioned IOPS are billed whether you use them or not.

- **Maximum size:** up to 64 TiB for MariaDB, MySQL, PostgreSQL and Db2. Oracle and SQL Server reach 256 TiB with extra storage volumes.
- **Storage autoscaling:** set a maximum storage threshold (`--max-allocated-storage`). RDS grows the disk when free space is at or below 10 % for 5 minutes. It needs no reboot and no downtime.
- **Storage never shrinks.** To go smaller you migrate (or use Blue/Green).
- RDS does **not** autoscale read replicas. You add and delete them yourself.

### Multi-AZ DB instance (the classic one)

RDS keeps a **synchronous standby** in a second AZ. If the primary fails, RDS flips the **DNS name** of the endpoint to the standby.
The endpoint stays the same. Clients must reconnect.

- You **cannot read from the standby.** It is for availability, not for read scaling.
- Failover is typically **60–120 seconds**.
- Triggers: unhealthy host, lost network, storage failure, instance modification, OS patching, manual reboot with failover.
- Synchronous writes can add some commit latency compared with Single-AZ.
- Turn it on later by modifying the instance (console, CLI or API).

### Multi-AZ DB cluster (the newer one)

One writer and **two readable standbys** in three AZs of one Region. Replication is semisynchronous: a commit needs an
acknowledgement from at least one reader. You get high availability **and** extra read capacity, with lower write latency than the
instance flavour. Failover is typically **under 35 seconds**. It is not Aurora. The AWS page names MySQL and PostgreSQL.
It uses only certain instance classes (for example `db.m6gd`, `db.r6gd`).

### Read replicas

A read replica is a read-only copy kept up to date by **asynchronous** replication (the engine's own mechanism).

- **Quota:** 15 read replicas per source in a Region (adjustable). AWS suggests about 5 for Oracle to limit lag.
- **Cross-Region** replicas work. Traffic between source and replica is encrypted.
- **Promote** a replica and it becomes a standalone, writable instance. This cannot be undone. Use it for disaster recovery.
- A source that is Multi-AZ can also have replicas.
- Replicas are billed as normal instances. No transfer charge in the same Region.
- If you delete a source, same-Region replicas are promoted automatically.
- The replica may use a different storage type from its source.
- Cascading replicas (a replica of a replica): MariaDB and MySQL yes; PostgreSQL from 14.1.
- MySQL replicas need automated backups switched on at the source.
- Lag exists. A read right after a write can return old data.

### Backups and restore

| Item | Rule |
|---|---|
| Automated backups | Daily snapshot in the backup window plus transaction logs, kept in S3 |
| Retention | 0 to 35 days. 0 turns them off. Default **7** in the console, **1** from the CLI or API |
| Point-in-time recovery | Any second in the retention window. Logs upload every 5 minutes, so the latest restorable time is about 5 minutes ago |
| Manual snapshot | Kept until you delete it, even after the instance is gone. Up to 100 per Region |
| Restore | Always creates a **new instance** with a new endpoint. The source is untouched |
| Cross-Region copy | Snapshots can be copied to another Region. Encrypted ones need a KMS key valid there |

Automated backups are deleted with the instance unless you choose to retain them. Take a final snapshot when you delete.
Changing retention between 0 and non-zero causes an outage. The backup window and maintenance window cannot overlap.

### Encryption

- **At rest:** AES-256 through KMS. It covers storage, logs, backups, snapshots and replicas.
- You can encrypt an instance **only when you create it.** You cannot switch it on later and you cannot switch it off.
- **To encrypt an existing database:** take a snapshot, copy the snapshot with encryption enabled (pick a KMS key), restore from the encrypted copy. A Blue/Green deployment can also do it.
- A replica must match its source: no encrypted replica of an unencrypted source, and the reverse.
- **In transit:** SSL/TLS on all engines. PostgreSQL 15 and later enforce it by default (`rds.force_ssl` = 1).

### Authentication and secrets

- **IAM database authentication** (MariaDB, MySQL, PostgreSQL): the app asks IAM for an auth token and uses it as the password. The token lasts **15 minutes** and only needs to be valid when the connection starts. It needs extra memory on the database (300 to 1000 MiB).
- **`ManageMasterUserPassword`** (`--manage-master-user-password`): RDS creates the master password in **Secrets Manager** and rotates it, by default every **7 days**. You never see or store it. Secrets Manager charges apply.

### RDS Proxy

A proxy sits between your app and the database. It **pools and shares connections**, so thousands of short-lived clients (Lambda) share a
small pool. It also makes failover less painful: it keeps client connections and skips DNS caches, cutting failover time by up to **66 %** for Multi-AZ.

- Clients can be forced to use IAM authentication; the proxy reaches the database with IAM or Secrets Manager credentials.
- It lives in the same VPC as the database and cannot be public.
- For replicated RDS instances it connects to the writer, not to a read replica.
- Long statements (over 16 KB) pin a session to one connection and reduce pooling.
- Quotas: 20 proxies per account.
- Why it matters: every database has a `max_connections` limit. For PostgreSQL the default is `LEAST(DBInstanceClassMemory/9531392, 5000)`. Drill 07 does the arithmetic.

### Blue/Green deployments

RDS builds a **green** copy of production (**blue**), keeps it in sync, and lets you change the engine version, parameters or schema there first.
You then **switch over**: typically under a minute, no data loss, no app change. The old environment is kept, renamed with `-old1`.
Available for MariaDB, MySQL and PostgreSQL. Managed master passwords are not supported with Blue/Green.

### Maintenance, deletion protection

- **Maintenance window:** weekly, 30 minutes. If you set none, RDS picks a random one. OS and engine patches arrive about every few months and cannot be put off for ever.
- On Multi-AZ, RDS patches the standby first, fails over, then patches the old primary.
- **Deletion protection** blocks `delete-db-instance`. It is on by default in the console. Turn it off by modifying the instance.
- **Extended Support** (changed, 2024) is a paid way to keep a major engine version past end of standard support, up to 3 years.

## Numbers to know

| Fact | Value |
|---|---|
| Backup retention | 0 to 35 days; console default 7; CLI/API default 1 |
| Multi-AZ DB instance failover | typically 60–120 s |
| Multi-AZ DB cluster failover | typically under 35 s |
| Read replicas per source | 15 |
| Max storage | 64 TiB (MySQL, MariaDB, PostgreSQL, Db2); 256 TiB (Oracle, SQL Server) |
| Autoscaling trigger | free space ≤ 10 % for 5 minutes |
| IAM auth token | 15 minutes |
| Managed secret rotation | every 7 days by default |
| Manual snapshots | 100 per Region |
| DB instances per Region | 40 |
| Latest restorable time | about 5 minutes ago |
| RDS Proxy failover gain | up to 66 % |

## When to choose it

- You need a **relational** engine with joins and transactions, and your team knows MySQL, PostgreSQL, Oracle or SQL Server.
- You are moving an existing database as-is (a homogeneous migration: same engine). A different engine needs a schema conversion first.
- You want high availability without Aurora's storage model: use Multi-AZ.
- You need **read scale**: add read replicas. Need **DR in another Region**: cross-Region replica or copied snapshots.
- Lambda or many short connections: put **RDS Proxy** in front.
- You must upgrade without surprise: use **Blue/Green**.
- If you need up to 15 low-lag replicas and fast storage-level failover, look at Aurora (note 02).

## Exam traps

- "The standby can serve read traffic" for a Multi-AZ **DB instance** is false. Only the Multi-AZ **DB cluster** has readable standbys.
- Read replicas are **asynchronous**, so they are not a high-availability tool by themselves and can lag. The Multi-AZ standby is synchronous.
- "Encrypt the running database" cannot be done in place. The answer is snapshot, copy with encryption, restore.
- A restore (PITR or snapshot) makes a **new** instance. You must point the app at the new endpoint.
- Multi-AZ keeps the **same endpoint**. A promoted read replica gets its own endpoint.
- Retention 0 means no automated backups and no PITR.
- Manual snapshots survive instance deletion. Automated backups do not (unless retained).
- Multi-AZ protects against AZ failure, not against a bad `DELETE`. Backups and PITR do that.
- Storage autoscaling grows. It never shrinks.
- RDS Proxy fixes **connection count** and failover time. It does not add read capacity.
- A cross-Region read replica is DR for a Region loss. Multi-AZ is not.

## Cost angle

- Multi-AZ doubles the instance price: PostgreSQL `db.t4g.micro` is 0.016 USD/hour Single-AZ and 0.032 Multi-AZ; `db.m7g.large` is 0.168 and 0.337 (illustrative).
- Multi-AZ storage costs more too: gp3 is 0.115 USD per GB-month Single-AZ, 0.23 for a Multi-AZ DB instance and 0.345 for a Multi-AZ DB cluster.
- Backup storage beyond the free allocation is 0.095 USD per GB-month (PostgreSQL).
- RDS Proxy costs 0.015 USD per vCPU-hour of the database instance.
- Read replicas are full instances. Ten replicas cost ten instances. Add them only when reads are the bottleneck.
- Delete lab databases, and delete old manual snapshots: they keep billing.
- Use Reserved Instances (or Database Savings Plans) for steady databases; do not buy them for a lab.

## Comparison

| | Multi-AZ DB instance | Multi-AZ DB cluster | Read replica |
|---|---|---|---|
| Replication | Synchronous | Semisynchronous | Asynchronous |
| Copies | 1 standby | 2 readable standbys | Up to 15 |
| Readable | No | Yes | Yes |
| Goal | High availability | High availability and read capacity | Read scale and DR |
| Failover | Automatic, typically 60–120 s | Automatic, typically under 35 s | Manual promotion |
| Endpoint after failover | Same | Clients reconnect | Own endpoint; promote it |
| Cross-Region | No | No | Yes |
| Storage cost vs Single-AZ | 2x | 3x | Same as a normal instance |

Now do drill 08 (a database that fails over), drill 07 (too many connections) and drill 09 (HA, read scale or DR?).

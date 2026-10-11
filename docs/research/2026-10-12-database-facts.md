# Week 05 databases and caching facts (collected 2026-10-12)

All rows below were read from official AWS pages on 2026-10-11/12 (session date 2026-10-11). "Changed?" is "no" unless a change after 2022 is documented on the page read. Prices are illustrative; always re-check.

URL key (base paths):
- RDS = https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/
- AUR = https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/
- DSQL = https://docs.aws.amazon.com/aurora-dsql/latest/userguide/
- DDB = https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/
- EC = https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/
- MDB = https://docs.aws.amazon.com/memorydb/latest/devguide/
- NEP = https://docs.aws.amazon.com/neptune/latest/userguide/
- DOC = https://docs.aws.amazon.com/documentdb/latest/developerguide/
- KS = https://docs.aws.amazon.com/keyspaces/latest/devguide/
- TS = https://docs.aws.amazon.com/timestream/latest/developerguide/
- OS = https://docs.aws.amazon.com/opensearch-service/latest/developerguide/
- GR = https://docs.aws.amazon.com/general/latest/gr/
- PL-RDS / PL-EC / PL-DDB / PL-DAX = AWS Price List files (see section 6)
- (other full URLs are written out in the Source column)

## 1. RDS

| Fact | Value | Changed? | Source |
|---|---|---|---|
| RDS engines (storage page) | Db2, MariaDB, MySQL, PostgreSQL, Oracle, Microsoft SQL Server | changed (Db2 is a newer engine; Aurora is separate) | RDS CHAP_Storage.html |
| DB instance class families | General purpose (db.m), memory optimized (db.r, db.x, db.z), compute optimized (db.c, only c6gd for Multi-AZ DB clusters), burstable (db.t), Optimized Reads (db.m8gd, db.r8gd, db.r6gd, db.r6id) | no | RDS Concepts.DBInstanceClass.Types.html |
| Latest general purpose classes named | db.m9g (Graviton5), db.m8g (Graviton4), db.m8i (Intel Xeon 6), db.m8a (AMD EPYC 5th gen), db.m7i, db.m7g (Graviton3) | changed (m7g and later are newer than 2022) | RDS Concepts.DBInstanceClass.Types.html |
| Latest memory optimized classes named | db.r8g (Graviton4), db.r8i, db.r8a, db.r7g, db.r7i; db.x2g, db.x2i, db.x1, db.x1e; db.z1d | changed | RDS Concepts.DBInstanceClass.Types.html |
| Burstable classes | db.t4g (Graviton2), db.t3, db.t2; all configured for Unlimited mode | no | RDS Concepts.DBInstanceClass.Types.html |
| db.t4g Unlimited mode | "Configured for Unlimited mode": can burst beyond baseline over a 24-hour window for an additional charge | no | RDS Concepts.DBInstanceClass.Types.html |
| db.t2 retirement | Creating db.t2 no longer supported; automatic upgrade to db.t3 began 2024-06-01; support ended 2024-12-31 (MariaDB, MySQL, SQL Server, PostgreSQL) | changed 2024 | RDS Concepts.DBInstanceClass.Types.html |
| db.m4 and db.r4 retirement | Same schedule: auto-upgrade from 2024-06-01 (to db.m5 / db.r5); support ended 2024-12-31 | changed 2024 | RDS Concepts.DBInstanceClass.Types.html |
| db.m3 and db.r3 | Cannot create; automatic upgrades started 2023-02-01 | changed 2023 | RDS Concepts.DBInstanceClass.Types.html |
| Storage types offered | Provisioned IOPS SSD (io1, io2 Block Express) and General Purpose SSD (gp2, gp3); API names io2, io1, gp3, gp2 | no | RDS CHAP_Storage.html |
| Magnetic storage | Deprecated; cannot create new DB instances; existing volumes migrated to gp3; from 2026-07-01 snapshots cannot be restored to magnetic | changed (deprecated; 2026-07-01 date) | RDS CHAP_Storage.html |
| Max storage, Db2 / MariaDB / MySQL / PostgreSQL | Up to 64 TiB | no | RDS CHAP_Storage.html |
| Max storage, Oracle and SQL Server | Up to 256 TiB using up to three additional storage volumes (primary volume up to 64 TiB) | changed (additional storage volumes are newer) | RDS CHAP_Storage.html |
| Max storage, small classes | db.t4g.micro 6 TiB (MariaDB, MySQL, PostgreSQL); db.t4g.small 16 TiB (PostgreSQL 16); db.t4g.medium MariaDB/MySQL 16, PostgreSQL 32 TiB | no | RDS CHAP_Storage.html |
| gp3 baseline, storage under 400 GiB | 3,000 IOPS and 125 MiB/s (Db2, MariaDB, MySQL, PostgreSQL; Oracle under 200 GiB) | no | RDS CHAP_Storage.html |
| gp3 baseline, storage 400 GiB and above | 12,000 IOPS and 500 MiB/s (striped across four volumes; Oracle from 200 GiB; SQL Server has no threshold, always 3,000 / 125) | no | RDS CHAP_Storage.html |
| gp3 provisioned range at/above threshold | 12,000 to 64,000 IOPS and 500 to 4,000 MiB/s (SQL Server 3,000 to 80,000 IOPS, 125 to 2,000 MiB/s) | no | RDS CHAP_Storage.html |
| gp3 size range | 20 to 65,536 GiB (SQL Server table row says 16,384 GiB in the comparison table) | no | RDS CHAP_Storage.html |
| gp3 latency wording | Single-digit millisecond, provided consistently 99% of the time | no | RDS CHAP_Storage.html |
| gp2 baseline | 3 IOPS per GiB, minimum 100 IOPS; below 1,000 GiB can burst to 3,000 IOPS (credit balance) | no | RDS CHAP_Storage.html |
| gp2 status | "Previous generation"; gp3 labelled recommended | changed (gp3 recommended) | RDS CHAP_Storage.html |
| io2 Block Express max | Up to 256,000 IOPS; sub-millisecond average latency on Nitro-based instances; 100 to 65,536 GiB (MariaDB, MySQL, PostgreSQL, Db2); IOPS-to-GiB ratio 0.5 to 1,000 | changed (io2 Block Express is newer) | RDS CHAP_Storage.html |
| io2 latency wording | Sub-millisecond, provided consistently 99.9% of the time | no | RDS CHAP_Storage.html |
| io1 | Previous generation; up to 256,000 IOPS (SQL Server 64,000); IOPS-to-GiB ratio 0.5 to 50 | no | RDS CHAP_Storage.html |
| Provisioned IOPS billing | Charged for provisioned resources whether or not you use them | no | RDS CHAP_Storage.html |
| Provisioned IOPS best fit | Production, I/O-intensive OLTP, recommended with Multi-AZ; General Purpose "best suited for development and testing environments" | no | RDS CHAP_Storage.html |
| Dedicated log volume (DLV) | For PIOPS storage only (io1, io2); fixed 1,024 GiB and 3,000 IOPS; not for gp2/gp3 | changed (newer feature) | RDS CHAP_Storage.html |
| Storage autoscaling trigger | Free space at or below 10% of allocated storage, low-storage condition lasting at least 5 minutes, and fewer than four storage modifications in the last 24 hours (previous optimization finished) | no | RDS USER_PIOPS.Autoscaling.html |
| Storage autoscaling increment | Greater of 10 GiB, 10% of allocated storage, or predicted growth over the next 7 hours | no | RDS USER_PIOPS.Autoscaling.html |
| Storage autoscaling threshold | Set Maximum storage threshold (--max-allocated-storage); must be at least 10% above current allocated (26% recommended) | no | RDS USER_PIOPS.Autoscaling.html |
| Storage autoscaling downtime | Enabling or changing it needs no reboot and no downtime | no | RDS USER_PIOPS.Autoscaling.html |
| Storage can shrink? | No: allocated storage cannot be reduced after allocation (use blue/green or migrate) | no | RDS USER_PIOPS.Autoscaling.html |
| Read replica autoscaling | RDS does not autoscale read replicas; create and delete them manually | no | RDS USER_ReadRepl.html |
| Multi-AZ DB instance deployment | Synchronous standby replica in a different AZ; "can't use a standby replica to serve read traffic" | no | RDS Concepts.MultiAZSingleStandby.html |
| Multi-AZ DB instance purpose | High availability, not a read-scaling solution; use a read replica or Multi-AZ DB cluster to serve reads | no | RDS Concepts.MultiAZSingleStandby.html |
| Multi-AZ DB instance failover wording | "Failover times are typically 60-120 seconds"; large transactions or lengthy recovery can increase it | no | RDS Concepts.MultiAZ.Failover.html |
| Multi-AZ failover endpoint | RDS changes the DNS record of the DB instance to point to the standby; clients must reconnect; AWS recommends JVM DNS TTL of no more than 60 seconds | no | RDS Concepts.MultiAZ.Failover.html |
| Multi-AZ failover triggers | OS patching, unhealthy primary host, loss of network connectivity, instance modification, busy/unresponsive primary, storage volume failure, manual reboot with failover | no | RDS Concepts.MultiAZ.Failover.html |
| Multi-AZ technology by engine | MariaDB, MySQL, Oracle, PostgreSQL use Amazon failover technology; SQL Server uses Database Mirroring or Always On Availability Groups | no | RDS Concepts.MultiAZSingleStandby.html |
| Multi-AZ write latency | Synchronous replication can increase write and commit latency compared with Single-AZ | no | RDS Concepts.MultiAZSingleStandby.html |
| Convert Single-AZ to Multi-AZ | Modify the DB instance and specify Multi-AZ (console, CLI or API) | no | RDS Concepts.MultiAZSingleStandby.html |
| Multi-AZ OS maintenance | Standby patched first, standby promoted, old primary patched; failover typically lasts less than a minute | no | RDS USER_UpgradeDBInstance.Maintenance.html |
| Multi-AZ engine upgrade | Both primary and standby are modified at the same time and both are unavailable until upgrade completes | no | RDS USER_UpgradeDBInstance.Maintenance.html |
| Multi-AZ DB cluster definition | Semisynchronous deployment with a writer and two readable reader instances in three separate AZs in one Region | changed (Multi-AZ DB clusters are newer than 2022 GA of Multi-AZ instance) | RDS multi-az-db-clusters-concepts.html |
| Multi-AZ DB cluster replication | Semisynchronous: commit needs acknowledgment from at least one reader | no | RDS multi-az-db-clusters-concepts.html |
| Multi-AZ DB cluster benefits | High availability, increased read capacity, lower write latency vs Multi-AZ DB instance | no | RDS multi-az-db-clusters-concepts.html |
| Multi-AZ DB cluster failover time | "Failover times are typically under 35 seconds"; completes when both readers applied outstanding transactions | no | RDS multi-az-db-clusters-concepts-failover.html |
| Multi-AZ DB cluster engines | Page names RDS for MySQL and RDS for PostgreSQL (replica lag and flow control sections) | no | RDS multi-az-db-clusters-concepts.html |
| Multi-AZ DB cluster instance classes | db.c6gd, db.m5d, db.m6gd, db.m6id, db.m6idn, db.m8gd, db.r5d, db.r6gd, db.r6id, db.r6idn, db.r8gd, db.x2iedn | changed (list contains newer classes) | RDS multi-az-db-clusters-concepts.html |
| Multi-AZ DB cluster backups | Cluster-level storage snapshot; retention 1 to 35 days (0 not allowed); "You can't copy a snapshot of a Multi-AZ DB cluster" (copy page limitation) | no | RDS USER_WorkingWithAutomatedBackups.BackupRetention.html ; RDS USER_CopySnapshot.html |
| Multi-AZ DB cluster vs Aurora | "Multi-AZ DB clusters aren't the same as Aurora DB clusters" | no | RDS multi-az-db-clusters-concepts.html |
| Read replica definition | Read-only copy of a DB instance; RDS uses engine native replication; source becomes the primary | no | RDS USER_ReadRepl.html |
| Read replica replication type | Asynchronous (standby replica in Multi-AZ is synchronous) | no | RDS USER_ReadRepl.html |
| Read replica creation | RDS takes a snapshot of the source and creates a read-only instance from it | no | RDS USER_ReadRepl.html |
| Read replica billing | Billed as a standard DB instance; no data transfer charge between source and replica in the same Region | no | RDS USER_ReadRepl.html |
| Read replica use cases | Scale reads, serve reads when source unavailable, reporting, disaster recovery by promotion | no | RDS USER_ReadRepl.html |
| Read replica on Multi-AZ source | Allowed: a source with a Multi-AZ standby can also have read replicas | no | RDS USER_ReadRepl.html |
| Read replica can itself be Multi-AZ | MySQL page lists a topic "Working with Multi-AZ read replica deployments with MySQL" (only the topic title was read, not its body) | no | RDS USER_MySQL.Replication.ReadReplicas.html |
| Read replicas per source (quota table) | "Read replicas per primary: 15" per Region, adjustable; cannot be adjusted for Aurora | no | RDS CHAP_Limits.html |
| RDS MySQL read replica max | "You can create up to 15 read replicas from one DB instance within the same Region" | no | RDS USER_MySQL.Replication.ReadReplicas.html |
| RDS PostgreSQL read replica max | PostgreSQL page states no number; the account quota "Read replicas per primary" is 15 and is not engine-specific; resolves the facts.md "Not confirmed" item as 15 (via the quota table) | no | RDS CHAP_Limits.html ; RDS USER_PostgreSQL.Replication.ReadReplicas.html |
| RDS Oracle read replica max | Up to 15 per source per Region, but AWS recommends limiting to 5 to minimize replication lag | no | RDS CHAP_Limits.html |
| Cascading read replicas | MariaDB and MySQL yes; PostgreSQL 14.1 and higher only; Db2, Oracle, SQL Server cannot replicate from a replica | changed (PostgreSQL cascading from 14.1) | RDS USER_ReadRepl.html ; RDS USER_PostgreSQL.Replication.ReadReplicas.html |
| MySQL replica requirement | Source needs automated backups on (retention not 0); replica cannot use a lower engine version than source | no | RDS USER_MySQL.Replication.ReadReplicas.html |
| Cross-Region read replicas | Supported; RDS sets up a secure channel; data in transit between source and replica is encrypted | no | RDS USER_ReadRepl.html ; RDS Overview.Encryption.html |
| Cross-Region replica quota | Concurrent cross-Region read replica requests default 20 per Region | no | RDS CHAP_Limits.html |
| Promote a read replica | Becomes a standalone writable DB instance; process is not reversible (PostgreSQL page) | no | RDS USER_PostgreSQL.Replication.ReadReplicas.html |
| Delete source with replicas | Same-Region replicas are automatically promoted to standalone instances | no | RDS USER_ReadRepl.html |
| Replica storage type | Can differ from source (e.g. gp3 replica for io2 source) | no | RDS USER_ReadRepl.html |
| PostgreSQL replica PITR | Point-in-time recovery not supported on read replicas; automated backups on replicas need PostgreSQL 14.1+ | no | RDS USER_PostgreSQL.Replication.ReadReplicas.html |
| PostgreSQL idle replica lag | With no transactions, reported lag can rise to 5 minutes (WAL segment switch every 5 minutes) | no | RDS USER_PostgreSQL.Replication.ReadReplicas.html |
| Automated backups: what | RDS storage volume snapshot of the whole instance during the backup window, plus transaction logs; saved per retention period; stored in Amazon S3 | no | RDS USER_WorkingWithAutomatedBackups.html |
| Retention range (DB instance) | 0 to 35 days; 0 disables automated backups | no | RDS USER_WorkingWithAutomatedBackups.BackupRetention.html |
| Retention default, console | 7 days | no | RDS USER_WorkingWithAutomatedBackups.BackupRetention.html |
| Retention default, CLI or API | 1 day | no | RDS USER_WorkingWithAutomatedBackups.BackupRetention.html |
| Changing retention 0 <-> nonzero | Causes an outage | no | RDS USER_WorkingWithAutomatedBackups.BackupRetention.html |
| Restore retention inheritance | A restored DB inherits the source retention unless set; new databases get the default | changed (explicit inheritance wording is recent) | RDS USER_WorkingWithAutomatedBackups.BackupRetention.html |
| Stopped DB instance | Time in stopped state not counted; automated backups not created while stopped | no | RDS USER_WorkingWithAutomatedBackups.BackupRetention.html |
| Backup window vs maintenance window | The maintenance window and the backup window cannot overlap | no | RDS USER_UpgradeDBInstance.Maintenance.html |
| Backup storage location | Backup storage per Region = automated backups + manual snapshots; stored in Amazon S3 | no | RDS USER_WorkingWithAutomatedBackups.html |
| First snapshot / later snapshots | First snapshot is full; subsequent snapshots incremental | no | RDS USER_WorkingWithAutomatedBackups.html |
| PITR transaction log upload | RDS uploads transaction logs to Amazon S3 every five minutes | no | RDS USER_PIT.html |
| Latest restorable time | Visible as LatestRestorableTime (describe-db-instances); typically within the last 5 minutes because logs upload every 5 minutes | no | RDS USER_PIT.html |
| PITR window | Any time within the backup retention period (earliest restorable time shown in console) | no | RDS USER_PIT.html |
| PITR creates new instance | "Creating a new DB instance without modifying the source DB instance" | no | RDS USER_PIT.html |
| Restore storage rule | Cannot reduce storage on restore; increase must be at least 10% | no | RDS USER_PIT.html |
| Restored instance defaults | Gets default parameter group and option group unless specified; volumes lazily load blocks from S3 so performance may be lower until initialization completes | no | RDS USER_PIT.html |
| Manual snapshots limit | Up to 100 per Region (adjustable quota); AWS Backup snapshots do not count | no | RDS CHAP_Limits.html |
| Manual snapshots retention | Kept until you delete them; not deleted when the DB instance is deleted | no | RDS USER_CopySnapshot.html ; RDS USER_DeleteInstance.html |
| Automated backups on instance delete | Deleted with the instance unless you choose Retain automated backups (kept for retention period, billed) | no | RDS USER_DeleteInstance.html |
| Cross-Region snapshot copy | Supported (not to or from China Regions); up to 20 concurrent copies per account per destination Region; data transfer charges; first copy is full, later can be incremental | no | RDS USER_CopySnapshot.html |
| Encrypted snapshot cross-Region copy | Must specify a KMS key valid in the destination Region (or a multi-Region key) | no | RDS USER_CopySnapshot.html |
| Share snapshots | Manual snapshots can be shared (including cross-account copy in one step after sharing, and sharing the KMS key); default AWS managed key snapshots cannot be shared | no | RDS USER_CopySnapshot.html ; RDS Overview.Encryption.html |
| Replicate automated backups | Automated backups can be replicated to another Region | no | RDS USER_DeleteInstance.html |
| Encryption at rest cipher | AES-256 via AWS KMS; covers storage, logs, automated backups, read replicas, snapshots | no | RDS Overview.Encryption.html |
| Encryption only at creation | "You can only encrypt an Amazon RDS DB instance when you create it, not after" | no | RDS Overview.Encryption.html |
| Encrypt an existing database | Snapshot, copy the snapshot with encryption enabled (KMS key), restore from the encrypted copy; blue/green deployment can also encrypt or change key | changed (blue/green route is newer) | RDS Overview.Encryption.html |
| Cannot unencrypt | Cannot turn off encryption; no encrypted snapshot of unencrypted instance directly | no | RDS Overview.Encryption.html |
| Replica encryption rule | "You can't have an encrypted read replica of an unencrypted DB instance or an unencrypted read replica of an encrypted DB instance"; same-Region encrypted replicas must use the source KMS key per the limitations list (the key section also mentions KmsKeyId override; see Unconfirmed) | no | RDS Overview.Encryption.html |
| Change KMS key | Cannot change KMS key of an existing encrypted instance (copy snapshot with new key instead) | no | RDS Overview.Encryption.html |
| Lost KMS key access | After disabling key, instance enters inaccessible-encryption-credentials-recoverable (2 hours after detection, 7 days to recover) then terminal state; RDS makes a final snapshot | changed (recoverable state and automatic final snapshot are newer) | RDS Overview.Encryption.html |
| Encryption in transit | SSL/TLS supported on all engines (Db2, MariaDB, SQL Server, MySQL, Oracle, PostgreSQL) | no | RDS UsingWithRDS.SSL.html |
| rds.force_ssl (PostgreSQL) | Parameter default 1 (on) for PostgreSQL 15 and later; 0 (off) for 14 and older; set via custom parameter group; non-SSL connections rejected | changed (default on for 15+) | RDS PostgreSQL.Concepts.General.SSL.html |
| PostgreSQL TLS versions | TLS 1.1 and 1.2; TLS 1.3 on PostgreSQL 16 and later; ssl_min_protocol_version shown as TLSv1.2 | changed | RDS PostgreSQL.Concepts.General.SSL.html |
| Default RDS CA | rds-ca-rsa2048-g1 (others rds-ca-rsa4096-g1, rds-ca-ecc384-g1) | changed (older rds-ca-2019 not listed) | RDS UsingWithRDS.SSL.html |
| IAM database authentication | Works with MariaDB, MySQL and PostgreSQL; no password, uses an authentication token | no | RDS UsingWithRDS.IAMDBAuth.html |
| IAM auth token lifetime | 15 minutes (only needed to authenticate; session continues after) | no | RDS UsingWithRDS.IAMDBAuth.html |
| IAM auth token signing | AWS Signature Version 4; connections use SSL/TLS | no | RDS UsingWithRDS.IAMDBAuth.html |
| IAM auth memory cost | Needs 300 to 1000 MiB extra memory on the database | no | RDS UsingWithRDS.IAMDBAuth.html |
| Secrets Manager master password | Set ManageMasterUserPassword=true (--manage-master-user-password); RDS generates and stores the password in Secrets Manager | changed (feature newer than 2022) | RDS rds-secrets-manager.html |
| Secrets Manager rotation default | RDS rotates the secret every seven days by default (schedule can be modified); resolves the "7 days?" query | changed | RDS rds-secrets-manager.html |
| Secrets Manager integration limits | Not supported with Blue/Green Deployments, RDS Custom, Oracle Data Guard switchover; creating replicas from a source that manages credentials not supported for most engines | changed | RDS rds-secrets-manager.html |
| Secrets Manager billing and KMS | Secrets Manager charges apply; KMS key for the secret cannot be changed once managed | no | RDS rds-secrets-manager.html |
| RDS Proxy purpose | Pool and share database connections; makes applications more resilient to database failures | no | RDS rds-proxy.html |
| RDS Proxy failover claim | Bypasses DNS caches to reduce failover times "by up to 66%" for RDS Multi-AZ DB instances (and for Aurora Multi-AZ) | no | RDS rds-proxy-planning.html ; AUR Concepts.AuroraHighAvailability.html |
| RDS Proxy auth | Clients can be forced to use IAM authentication; proxy connects to the database with IAM auth or Secrets Manager credentials | no | RDS rds-proxy.html |
| RDS Proxy engines (limitations sections) | MariaDB, MySQL, PostgreSQL, SQL Server | no | RDS rds-proxy.html |
| RDS Proxy and Lambda | Lambda functions are good candidates (frequent short connections); also any app without built-in pooling; not Lambda-only | no | RDS rds-proxy-planning.html |
| RDS Proxy quotas | 20 proxies per account; up to 200 Secrets Manager secrets per proxy; up to 20 additional endpoints per proxy | no | RDS rds-proxy.html |
| RDS Proxy network | Must be in the same VPC as the database; cannot be publicly accessible; not supported on dedicated-tenancy VPCs; default endpoint spans two AZs | no | RDS rds-proxy.html |
| RDS Proxy and replicas | For RDS instances in replication configurations, proxy can attach only to the writer (not a read replica) | no | RDS rds-proxy.html |
| RDS Proxy pinning | Statement text over 16 KB pins the session to a connection (reduces multiplexing) | no | RDS rds-proxy.html |
| RDS Proxy and Blue/Green | Proxy redirects connections to the green environment on switchover without waiting for DNS propagation | changed | RDS rds-proxy-planning.html |
| RDS Proxy and minor upgrade | Can reduce Multi-AZ DB cluster minor upgrade downtime to one second or less | changed | RDS multi-az-db-clusters-concepts.html |
| Blue/Green Deployments | Green staging environment copies production (blue) and stays in sync; switchover promotes green | changed (feature newer than 2022) | RDS blue-green-deployments-overview.html |
| Blue/Green RDS engines | RDS for MariaDB, MySQL and PostgreSQL | changed | RDS blue-green-deployments-overview.html |
| Blue/Green switchover time | "Typically takes under a minute" with no data loss and no application changes (downtime can be longer depending on workload) | changed | RDS blue-green-deployments-overview.html |
| Blue/Green after switchover | Names and endpoints move to new production; old environment renamed with -old1 suffix and kept for regression testing | no | RDS blue-green-deployments-overview.html |
| Maintenance window | Weekly interval; 30 minutes; if not specified RDS assigns a random 30-minute window on a random day from an 8-hour block per Region | no | RDS USER_UpgradeDBInstance.Maintenance.html |
| Maintenance window, us-east-1 block | 03:00 to 11:00 UTC | no | RDS USER_UpgradeDBInstance.Maintenance.html |
| Required maintenance | OS or database patches for security and reliability, scheduled automatically, "once every few months"; cannot be deferred indefinitely | no | RDS USER_UpgradeDBInstance.Maintenance.html |
| Operating system updates | Typically about 10 minutes; optional or mandatory with an apply date | no | RDS USER_UpgradeDBInstance.Maintenance.html |
| Deletion protection default, console | On by default for instances created with the console | no | RDS USER_DeleteInstance.html |
| Deletion protection, CLI or API | Page states the console default only; CLI/API default (off) not stated on this page | no | RDS USER_DeleteInstance.html (see Unconfirmed) |
| Deletion protection removal | Turn off by modifying the instance; no outage | no | RDS USER_DeleteInstance.html |
| Final snapshot on delete | Optional; can restore deleted instance from it; AWS Support may recover an accidentally deleted instance for up to six days | no | RDS USER_DeleteInstance.html |
| Database Insights | RDS enables Database Insights in Advanced mode by default (lock diagnostics, execution plan capture, fleet monitoring) | changed (Database Insights is newer; Performance Insights page now titled Database Insights) | RDS USER_PerfInsights.Overview.html |
| Database Insights retention | Default includes 7 days of history and 1 million API requests per month; longer retention selectable from 1 to 24 months | changed | RDS USER_PerfInsights.Overview.cost.html |
| Performance Insights status | Chapter title on the RDS guide is "Monitoring DB load with Amazon CloudWatch Database Insights"; Performance Insights API and CloudTrail topics still listed | changed | RDS USER_PerfInsights.html |
| RDS Custom | Managed database service with access to the underlying OS and database; engines Oracle Database and Microsoft SQL Server only | no | RDS rds-custom.html |
| RDS Extended Support | Paid option to keep running a major engine version past RDS end of standard support, up to 3 years; auto-enrolled if enabled at create/restore | changed (Extended Support launched 2024) | RDS extended-support.html |
| Extended Support example | MySQL 5.7 end of standard support 2024-02-29; charges started 2024-03-01 | changed 2024 | RDS extended-support.html |
| Extended Support coverage | Critical and high CVE security updates, bug fixes for critical issues, support cases; disabling after standard end triggers upgrade to next supported major version | changed | RDS extended-support.html |
| Instance quota | 40 DB instances per Region by default (20 in ap-south-1); counts RDS, Aurora, Neptune, DocumentDB instances | no | RDS CHAP_Limits.html |
| max_connections default (MySQL) | DBInstanceClassMemory/12582880; db.t3.micro about 60 | no | RDS CHAP_Limits.html |
| max_connections default (PostgreSQL) | LEAST(DBInstanceClassMemory/9531392, 5000) | no | RDS CHAP_Limits.html |
| Connection advice | Frequent open/close or many long-lived connections: use RDS Proxy | no | RDS CHAP_Limits.html |

## 2. Aurora

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Cluster volume | Single virtual SSD volume with copies of data across three Availability Zones in one Region | no | AUR Aurora.Overview.StorageReliability.html |
| Six copies | Data synchronously replicated to six storage nodes across AZs | no | AUR Concepts.AuroraHighAvailability.html |
| Replication independent of instances | Amount of replication is independent of the number of DB instances in the cluster | no | AUR Aurora.Overview.StorageReliability.html |
| Storage auto grow | Cluster volume grows automatically; you pay only for space used; space freed when data removed (dynamic resizing) | changed (dynamic shrinking is newer) | AUR Aurora.Overview.StorageReliability.html |
| Max cluster volume 256 TiB | Aurora PostgreSQL 17.5+, 16.9+, 15.13+; Aurora MySQL 3.10+ | changed (was 128 TiB) | AUR CHAP_Limits.html |
| Max cluster volume 128 TiB | All earlier Aurora PostgreSQL versions; Aurora MySQL 3 below 3.10; Aurora MySQL 2.09+ | changed | AUR CHAP_Limits.html |
| Table size limits | Aurora MySQL 64 TiB per table; Aurora PostgreSQL 32 TiB per table | no | AUR CHAP_Limits.html |
| Aurora Replicas max | Up to 15 per DB cluster; asynchronous, share the same cluster volume | no | AUR Aurora.Replication.html ; AUR Concepts.AuroraHighAvailability.html |
| Replica lag | "Usually much less than 100 milliseconds" after the writer updates | no | AUR Aurora.Replication.html |
| Replicas as failover targets | Writer failure promotes an Aurora Replica; without replicas the primary is recreated in same AZ (typically under 10 minutes) | no | AUR Concepts.AuroraHighAvailability.html |
| Aurora failover time | "Service is typically restored in less than 60 seconds, and often less than 30 seconds" | no | AUR Concepts.AuroraHighAvailability.html |
| Promotion priority tiers | 0 (highest) to 15 (lowest); same tier then largest size; priority change does not trigger failover | no | AUR Concepts.AuroraHighAvailability.html |
| Aurora with RDS Proxy | Reduces failover times by up to 66% for Aurora Multi-AZ | no | AUR Concepts.AuroraHighAvailability.html |
| Cluster (writer) endpoint | Always points to the current primary instance; use for read/write and general connections | no | AUR Aurora.Overview.Endpoints.html |
| Reader endpoint | Connection-balances read-only connections across Aurora Replicas | no | AUR Aurora.Overview.Endpoints.html |
| Custom endpoint | Maps to a chosen subset of instances; quota 5 per cluster (adjustable) | no | AUR Aurora.Overview.Endpoints.html ; AUR CHAP_Limits.html |
| Instance endpoint | Specific instance for diagnosis or tuning; does not follow failover | no | AUR Aurora.Overview.Endpoints.html |
| Global Database writer endpoint | Special endpoint that follows the primary cluster across Regions after switchover/failover | changed (newer) | AUR Aurora.Overview.Endpoints.html |
| Aurora Replicas and endpoints on failover | Reader endpoint may briefly send connections to the newly promoted primary | no | AUR Aurora.Overview.Endpoints.html |
| Global Database and Aurora Auto Scaling | Aurora Global Database does not support Aurora Auto Scaling for secondary DB clusters | no | AUR aurora-global-database.html |
| Serverless v2 ACU | Each ACU approximately 2 GiB memory plus corresponding CPU and networking | no | AUR aurora-serverless-v2.how-it-works.html |
| Serverless v2 capacity range | 0.5 to 128 ACUs (MySQL 3.02+); 0.5 to 256 (3.06+); 0 to 256 (3.08+; PostgreSQL 13.15+, 14.12+, 15.7+, 16.3+) | changed (scale to 0 and 256 ACU are newer) | AUR aurora-serverless-v2.how-it-works.html |
| Serverless v2 scaling step | Increments as small as 0.5 ACU; no pause in processing | no | AUR aurora-serverless-v2.how-it-works.html |
| Serverless v2 min 0 = auto-pause | Setting minimum capacity to 0 ACUs enables auto-pause; no instance charge while paused (storage still charged) | changed (2024-11-20 per facts.md) | AUR aurora-serverless-v2-auto-pause.html |
| Auto-pause timeout | Minimum 300 seconds (default) up to 86,400 seconds (one day) idle | changed | AUR aurora-serverless-v2-auto-pause.html |
| Auto-pause resume time | Typically about 15 seconds; 30 seconds or longer if paused over 24 hours | changed | AUR aurora-serverless-v2-auto-pause.html |
| Auto-pause blockers | Open user connections, RDS Proxy attached, primary cluster of a Global Database, logical replication/binlog on writer, zero-ETL | changed | AUR aurora-serverless-v2-auto-pause.html |
| Serverless v2 reader tiers | Readers in tiers 0 and 1 track writer capacity; tiers 2 to 15 scale independently | no | AUR aurora-serverless-v2.how-it-works.html |
| Serverless v2 readers | Up to 15 serverless readers across 3 AZs; mixed provisioned and serverless clusters allowed | no | AUR aurora-serverless-v2.how-it-works.html |
| Serverless v2 billing | ACU-hours, measured per second | no | AUR aurora-serverless-v2.html |
| Aurora Serverless v1 | "A deprecated product with a different architecture" (retired 2025-03-31 per facts.md) | changed | AUR aurora-serverless-v2.how-it-works.html |
| Global Database definition | One primary Region plus up to 10 read-only secondary Regions | changed (Aurora MySQL/PostgreSQL both state up to 10 secondary clusters; older limit was 5) | AUR aurora-global-database.html |
| Global Database replication | Storage-level, dedicated infrastructure, latency "typically under a second" | no | AUR aurora-global-database.html |
| Global Database secondary readers | Secondary cluster can have up to 16 read-only instances (limit 15 for a normal cluster) | no | AUR aurora-global-database.html |
| Global Database RTO wording | "RTO can be in the order of minutes" | no | AUR aurora-global-database-disaster-recovery.html |
| Global Database RPO wording | "RPO is typically measured in seconds" for failover; switchover RPO is 0 | no | AUR aurora-global-database-disaster-recovery.html |
| Switchover vs failover | Switchover (formerly managed planned failover): healthy, no data loss; failover (allow data loss): unplanned outage in primary Region | changed (terminology renamed) | AUR aurora-global-database-disaster-recovery.html |
| Switchover recovery time | Under 30 seconds typical on Aurora MySQL 3.09+ and Aurora PostgreSQL 16.8, 15.12, 14.17, 13.20 or higher | changed | AUR aurora-global-database-disaster-recovery.html |
| Manual failover (detach and promote) | Detach chosen secondary, which becomes a standalone cluster with read/write; recreate the global database by adding Regions | no | AUR aurora-global-database-disaster-recovery.html |
| Failover caution | Asynchronous replication means unreplicated writes can be lost; split-brain risk | no | AUR aurora-global-database-disaster-recovery.html |
| PostgreSQL RPO parameter | rds.global_db_rpo, valid values 20 to 2,147,483,647 seconds; transactions block if all secondaries exceed the RPO | changed | AUR aurora-global-database-disaster-recovery.html |
| Write forwarding | Secondary cluster forwards write SQL to the primary and results replicate back | changed (newer) | AUR aurora-global-database-write-forwarding.html |
| Global DB limits | No Backtrack; no Aurora Auto Scaling on secondaries; Secrets Manager integration unsupported | no | AUR aurora-global-database.html |
| Backtrack engine | Aurora MySQL only; "Backtrack is not available for Aurora PostgreSQL" | no | AUR AuroraMySQL.Managing.Backtrack.html |
| Backtrack window limit | 72 hours maximum | no | AUR AuroraMySQL.Managing.Backtrack.html |
| Backtrack mechanism | Rewinds the cluster in place without restoring from backup; no new cluster; brief disruption; hourly charge for change records | no | AUR AuroraMySQL.Managing.Backtrack.html |
| Backtrack enablement | Only on clusters created (or restored from snapshot) with Backtrack enabled; cannot be enabled by modifying | no | AUR AuroraMySQL.Managing.Backtrack.html |
| Backtrack not PITR replacement | "Backtracking is not a replacement for backing up your DB cluster" | no | AUR AuroraMySQL.Managing.Backtrack.html |
| Cloning | Copy-on-write at the storage layer; new cluster initially shares same data pages; fast and space-efficient | no | AUR Aurora.Managing.Clone.html |
| Clone limits | Up to 15 copy-on-write clones; the next is a full copy; same Region only; source needs at least one instance | no | AUR Aurora.Managing.Clone.html |
| Clone storage cost | Additional storage allocated only as source or clone changes data | no | AUR Aurora.Managing.Clone.html |
| Clone cross-account / cross-VPC | Cross-account via AWS RAM; cross-VPC allowed if subnets map to same AZs | changed | AUR Aurora.Managing.Clone.html |
| Aurora I/O-Optimized | No separate charge for read/write I/O; best when I/O spending is 25% or more of total Aurora spend | changed (I/O-Optimized launched 2023) | AUR Aurora.Overview.StorageReliability.html |
| Aurora Standard | Pay per 1 million I/O requests; best when I/O spending is under 25% of total | no | AUR Aurora.Overview.StorageReliability.html |
| Switching storage configuration | Standard to I/O-Optimized once per 30 days; no downtime for non-NVMe instances (including serverless); can switch I/O-Optimized to Standard any time | changed | AUR Aurora.Overview.StorageReliability.html |
| Aurora DSQL | Serverless, distributed relational database for transactional workloads; PostgreSQL-compatible (version 16) | changed (newer than 2022) | DSQL what-is-aurora-dsql.html |
| Aurora DSQL availability | 99.99% single-Region and 99.999% multi-Region; active-active; strong consistency | changed | DSQL what-is-aurora-dsql.html |
| Aurora DSQL multi-Region | Peered clusters in one Region set (cross-continent not supported) | changed | DSQL what-is-aurora-dsql.html |
| Aurora PostgreSQL Limitless Database | Automated horizontal scaling for millions of write transactions per second and petabytes of data; shard groups (quota 5 per Region) | changed (newer than 2022) | AUR limitless.html ; AUR CHAP_Limits.html |
| Aurora quotas | 40 DB clusters per Region; 5 IAM roles per cluster; 100 manual cluster snapshots | no | AUR CHAP_Limits.html |

## 3. DynamoDB

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Max item size | 400 KB, including attribute names (UTF-8 length) and values; confirms facts.md row | no | DDB Constraints.html |
| Binary units | 1 KB = 1024 bytes, 1 MB = 1024 KB | no | DDB Constraints.html |
| Partition key length | 1 byte minimum, 2048 bytes maximum | no | DDB Constraints.html |
| Sort key length | 1 byte minimum, 1024 bytes maximum | no | DDB Constraints.html |
| Number type | Up to 38 digits of precision | no | DDB Constraints.html |
| Nested attribute depth | Up to 32 levels | no | DDB Constraints.html |
| Table size | No practical limit on table size (items or bytes) | no | DDB ServiceQuotas.html |
| Tables per account per Region | Initial quota 2,500 (up to 10,000 via account team) | no (page gives no earlier value) | DDB ServiceQuotas.html |
| Write unit size | 1 write capacity/request unit = one write per second for an item up to 1 KB | no | DDB Constraints.html |
| Read unit size | 1 read capacity/request unit = one strongly consistent read per second, or two eventually consistent reads per second, for an item up to 4 KB | no | DDB Constraints.html |
| Eventually consistent read cost | 0.5 RCU/RRU per 4 KB (half of strongly consistent) | no | DDB Constraints.html ; DDB HowItWorks.ReadConsistency.html |
| Transactional read cost | 2 RCU/RRU per 4 KB item | no | DDB Constraints.html |
| Transactional write cost | 2 WCU/WRU per 1 KB item | no | DDB Constraints.html |
| Rounding | Item size divided by 4 KB (reads) or 1 KB (writes), rounded up to a whole number; examples: 3 KB read = 1 RCU, 512 byte write = 1 WCU | no | DDB provisioned-capacity-mode.html |
| Default read consistency | Eventually consistent for all read operations | no | DDB HowItWorks.ReadConsistency.html |
| Strongly consistent support | Tables and LSIs only; GSIs and streams are always eventually consistent | no | DDB HowItWorks.ReadConsistency.html |
| On-demand mode | Pay per request; "default and recommended throughput option" for most workloads | changed (now default and recommended; page gives no date) | DDB on-demand-capacity-mode.html |
| On-demand scaling | Instantly accommodates up to double the previous peak; exceeding double within 30 minutes can throttle | no | DDB on-demand-capacity-mode.html |
| On-demand new table throughput | New on-demand tables sustain up to 4,000 writes/s and 12,000 reads/s | no | DDB on-demand-capacity-mode.html |
| On-demand max throughput setting | Optional per-table / per-GSI maximum read or write throughput can be configured | changed (newer feature; no date on page) | DDB on-demand-capacity-mode.html |
| Provisioned mode | You specify RCUs and WCUs; billed per hour for provisioned capacity whether used or not | no | DDB provisioned-capacity-mode.html |
| Switch provisioned to on-demand | Up to four times in a 24-hour rolling window | changed (user brief says confirm current; earlier limit not stated on page) | DDB Constraints.html ; DDB bp-switching-capacity-modes.html |
| Switch on-demand to provisioned | At any time | changed (see row above) | DDB Constraints.html |
| Switch duration | Switching to on-demand can take several minutes; throughput stays at prior provisioned levels meanwhile | no | DDB bp-switching-capacity-modes.html |
| Provisioned decreases per day | Start each UTC day with 4 decreases, +1 each hour up to 4 available; up to 27 per day, per table and per GSI | no | DDB ServiceQuotas.html |
| Provisioned increases | Can increase RCU/WCU as often as necessary (not too rapidly) | no | DDB ServiceQuotas.html |
| Default throughput quota per table | 40,000 RCU/WCU (provisioned) or 40,000 RRU/WRU (on-demand); adjustable | no | DDB ServiceQuotas.html |
| Default throughput quota per account | 80,000 RCU and 80,000 WCU, provisioned only; adjustable; no account quota for on-demand | no | DDB ServiceQuotas.html |
| Minimum provisioned throughput | 1 RCU and 1 WCU per table or GSI | no | DDB ServiceQuotas.html |
| Auto scaling | Application Auto Scaling target tracking: set min, max and target utilization; triggers when consumption breaches target for two consecutive minutes | no | DDB provisioned-capacity-mode.html |
| Auto scaling target utilization | AWS recommends 70%; console creates tables with auto scaling enabled by default | no | DDB provisioned-capacity-mode.html |
| Auto scaling defaults on switch | Console recommends target 70%, minimum 5 units, maximum the Region maximum | no | DDB bp-switching-capacity-modes.html |
| Burst capacity | Retains up to five minutes (300 seconds) of unused read and write capacity; details "might change in the future" | no | DDB burst-adaptive-capacity.html |
| Adaptive capacity | Enabled automatically on every table at no additional cost; raises capacity for hot partitions up to partition max and table total | no | DDB burst-adaptive-capacity.html |
| Partition throughput limit | Throttling if one partition receives more than 3,000 read operations or 1,000 write operations; adaptive capacity can give up to 3,000 RCU and 1,000 WCU to a single item key | no | DDB burst-adaptive-capacity.html |
| Primary key | Partition key alone, or partition key plus sort key (composite) | no | DDB Constraints.html |
| Distinct key values | No practical limit on distinct partition key values; no practical limit on sort key values per partition key unless LSIs exist | no | DDB Constraints.html |
| GSI definition | Index with a different partition key and optional sort key than the base table; index key attributes are top-level String, Number or Binary | no | DDB GSI.html |
| GSI consistency | Updated asynchronously ("eventually consistent model"); strongly consistent reads from a GSI not supported | no | DDB GSI.html ; DDB HowItWorks.ReadConsistency.html |
| GSI default quota | 20 global secondary indexes per table (default) | no | DDB ServiceQuotas.html |
| GSI throughput | Own provisioned read and write capacity on provisioned tables; index writes consume the GSI's WCUs; too little GSI write capacity throttles base table writes | no | DDB GSI.html |
| GSI on existing tables | Page says multi-attribute keys work well "when creating global secondary indexes on existing tables" (so GSIs can be added after table creation) | no | DDB GSI.html |
| GSI multi-attribute keys | Partition key from up to four attributes and sort key from up to four attributes | changed (newer feature; no date on page) | DDB GSI.html |
| GSI reads | Query and Scan only; GetItem and BatchGetItem cannot be used on an index | no | DDB GSI.html |
| GSI key uniqueness | GSI key values need not be unique; an item missing an index key attribute is not written to the index | no | DDB GSI.html |
| GSI table class | A GSI always uses the same table class as its base table | no | DDB GSI.html |
| GSI storage overhead | 100 bytes of overhead per index item | no | DDB GSI.html |
| LSI definition | Same partition key as the base table, a different sort key (exactly one scalar attribute) | no | DDB LSI.html |
| LSI quota | Up to 5 local secondary indexes per table | no | DDB ServiceQuotas.html ; DDB LSI.html |
| LSI creation time | Created when the table is created (CreateTable LocalSecondaryIndexes parameter) | no | DDB LSI.html |
| LSI consistency | Query can be eventually or strongly consistent (ConsistentRead) | no | DDB LSI.html |
| LSI throughput | Index activity uses the table's provisioned throughput (no separate capacity) | no | DDB LSI.html |
| LSI item collection limit | 10 GB per partition key value (table plus all LSIs); ItemCollectionSizeLimitExceededException if exceeded; limit does not apply to GSIs or tables without LSIs | no | DDB LSI.html |
| Projection types | KEYS_ONLY, INCLUDE, ALL; max 100 user-specified projected attributes across all indexes of a table | no | DDB ServiceQuotas.html ; DDB GSI.html |
| Query | Needs the partition key attribute name and a single value; optional sort key condition; result set limited to 1 MB per call (LastEvaluatedKey to continue) | no | DDB Query.html ; DDB Constraints.html |
| Scan | Reads all data in the table or index; result limited to 1 MB per call; FilterExpression discards data only after it is read | no | DDB Constraints.html ; DDB GSI.html |
| Conditional writes | ConditionExpression on PutItem / UpdateItem / DeleteItem; false condition rejects the write ("The conditional request failed") | no | DDB Expressions.ConditionExpressions.html |
| Prevent overwrite | PutItem with attribute_not_exists(key) fails if an item with that key exists | no | DDB Expressions.ConditionExpressions.html |
| Optimistic locking | Version attribute; update or delete succeeds only if the server-side version equals the client's; mismatch raises ConditionalCheckFailedException; built on conditional writes | no | DDB DynamoDBMapper.OptimisticLocking.html |
| Optimistic locking and global tables | Global tables use last-writer-wins, so version-based locking "does not work as expected" across Regions | no | DDB DynamoDBMapper.OptimisticLocking.html |
| Transactions API | TransactWriteItems and TransactGetItems; ACID, all-or-nothing, synchronous | no | DDB transaction-apis.html |
| Transaction item limit | Up to 100 actions / unique items per transaction; aggregate size 4 MB | changed (user brief: prior limit 25; the earlier value and the change date are not on the page read) | DDB transaction-apis.html ; DDB Constraints.html |
| Transaction capacity | Two underlying reads or writes per item (prepare plus commit); consumed even if the transaction fails; no extra charge to enable | no | DDB transaction-apis.html |
| Transaction idempotency | ClientRequestToken valid for 10 minutes after the request finishes | no | DDB transaction-apis.html |
| Transaction restrictions | No two actions on the same item; one account and one Region only; not performed using indexes | no | DDB transaction-apis.html ; DDB Constraints.html |
| Transaction isolation | Serializable against single-item reads/writes and other transactions; read-committed for Query, Scan, BatchGetItem as a unit | no | DDB transaction-apis.html |
| Batch limits | BatchGetItem up to 100 items and 16 MB; BatchWriteItem up to 25 Put/Delete requests and 16 MB; batch writes are not atomic | no | DDB Constraints.html ; DDB transaction-apis.html |
| DynamoDB Streams retention | Time-ordered log of item changes stored for up to 24 hours | no | DDB Streams.html |
| Stream view types | KEYS_ONLY, NEW_IMAGE, OLD_IMAGE, NEW_AND_OLD_IMAGES (console: key attributes only, new image, old image, new and old images) | no | DDB Streams.html |
| Stream guarantees | Each stream record appears exactly once; per-item ordering preserved; no record if a write changes nothing | no | DDB Streams.html |
| Stream readers | At most two simultaneous readers per shard; Lambda ParallelizationFactor up to 10 | no | DDB Streams.html |
| Kinesis Data Streams for DynamoDB | Retention up to 1 year; up to 5 consumers per shard (20 with enhanced fan-out); duplicates possible. DynamoDB Streams: 24 hours, 2 consumers per shard, no duplicates | no | DDB streamsmain.html |
| Both streaming models | Can be enabled on the same table | no | DDB streamsmain.html |
| TTL attribute | Number type, Unix epoch seconds | no | DDB TTL.html |
| TTL deletion timing | "Deletes expired items within a few days of their expiration time"; expired items "might be deleted at any time, typically within a few days"; they can still be read or updated until deleted | no | DDB TTL.html |
| TTL cost | Deletion does not consume write throughput in the Region where it expires | no | DDB TTL.html |
| TTL and streams | Deleted items appear in streams as service deletions (not user deletes) | no | DDB TTL.html |
| TTL enable rate | One request to enable or disable TTL per table per hour | no | DDB Constraints.html |
| TTL and global tables | Replicated TTL deletes consume replicated write units in other Regions; TTL not supported on MRSC tables | no | DDB TTL.html ; DDB V2globaltables_HowItWorks.html |
| PITR window | Up to 35 days of recovery points at per-second granularity | no | DDB Point-in-time-recovery.html |
| PITR retention setting | RecoveryPeriodInDays default 35, configurable 1 to 35; shortening has no pricing impact | changed (configurable retention; no date on page) | DDB Point-in-time-recovery.html |
| PITR cross-Region restore | Restored table can be created in a different Region; pay for transfer out and restore | changed (no date on page) | DDB Point-in-time-recovery.html |
| PITR restore target | Restore creates an independent table; for a global table it is not part of the global table | no | DDB Point-in-time-recovery.html |
| PITR pricing basis | Based on size of table and local secondary indexes | no | DDB Point-in-time-recovery.html |
| Export to S3 | Needs PITR enabled; full or incremental; DynamoDB JSON or Amazon Ion; does not consume RCUs; billed by data size | changed (incremental export newer; no date on page) | DDB S3DataExport.HowItWorks.html |
| Global tables versions | Version 2019.11.21 (Current) and Version 2017.11.29 (Legacy); use Current | no | DDB V2globaltables_HowItWorks.html |
| Global tables replication | Multi-active; one replica per Region; write to any replica | no | DDB V2globaltables_HowItWorks.html |
| Global tables SLA | 99.999% availability SLA vs 99.99% for single-Region tables | no | DDB V2globaltables_HowItWorks.html |
| MREC | Multi-Region eventual consistency (default); asynchronous replication typically within a second or less; last-writer-wins conflict resolution | changed (MREC / MRSC naming is newer) | DDB V2globaltables_HowItWorks.html |
| MRSC | Multi-Region strong consistency; synchronous replication to at least one other Region before write returns; strongly consistent reads always latest; RPO of zero | changed (MRSC is newer; no date on page) | DDB V2globaltables_HowItWorks.html |
| MRSC topology | Exactly three Regions: three replicas, or two replicas plus a witness; mode cannot change after creation; table must be empty to convert | changed | DDB V2globaltables_HowItWorks.html |
| MRSC unsupported | TTL, local secondary indexes and transaction operations not supported on MRSC | changed | DDB V2globaltables_HowItWorks.html |
| MRSC quota | 400 MRSC global tables total | changed | DDB ServiceQuotas.html |
| Global tables and transactions | On MREC, transactions are atomic only within the invoking Region | no | DDB V2globaltables_HowItWorks.html |
| Global tables and DAX | Replicated writes bypass DAX, so caches can be stale until TTL expires | no | DDB V2globaltables_HowItWorks.html |
| Add-replica backfill quota | 10 TB per account per destination Region per 24 hours | no | DDB ServiceQuotas.html |
| DAX read path | Eventually consistent reads served from cache on a hit; strongly consistent reads passed through to DynamoDB and not cached | no | DDB DAX.concepts.html |
| DAX operations | Reads: GetItem, BatchGetItem, Query, Scan; writes (PutItem, UpdateItem, DeleteItem, BatchWriteItem) are write-through | no | DDB DAX.concepts.html |
| DAX caches | Item cache (GetItem/BatchGetItem) and query cache (Query/Scan result sets by parameter values) | no | DDB DAX.concepts.html |
| DAX default TTL | Item cache TTL default 5 minutes; TTL 0 means refresh only by LRU eviction or write-through; LRU always enabled | no | DDB DAX.concepts.html |
| DAX cluster size | Exactly one primary node plus zero to ten read replica nodes; 50 nodes per account per Region | no | DDB Constraints.html |
| DAX placement | Runs inside a VPC; DAX client sends DynamoDB API calls to the cluster; table management calls go directly to DynamoDB | no | DDB DAX.concepts.html |
| DAX and transactions | TransactWriteItems writes through DAX; TransactGetItems passed through without caching | no | DDB transaction-apis.html |
| DAX read latency | "DAX reduces the response times of eventually consistent read workloads by an order of magnitude from single-digit milliseconds to microseconds"; DynamoDB itself is "single-digit milliseconds" | no | DDB DAX.html |
| DAX use-case wording | "DAX provides access to eventually consistent data from DynamoDB tables, with microsecond latency. A Multi-AZ DAX cluster can serve millions of requests per second"; not ideal for strongly consistent reads, write-intensive or low cache-hit workloads (best when hit rates exceed 90%) | no | DDB DAX.html |
| Table classes | DynamoDB Standard (default) and Standard-Infrequent Access (Standard-IA) | no | DDB WorkingWithTables.tableclasses.html |
| Standard-IA break-even | When storage exceeds 50% of the throughput (reads and writes) cost of a Standard table, Standard-IA can lower total cost | no | DDB WorkingWithTables.tableclasses.html |
| Table class switch limit | No more than two table class updates per table in a 30-day trailing period; no code change; same performance | no | DDB WorkingWithTables.tableclasses.html |
| Encryption at rest | All user data always encrypted at rest (tables, indexes, streams, backups, global tables, DAX) | no | DDB EncryptionAtRest.html |
| Encryption key types | AWS owned key (default, no charge), AWS managed key, customer managed key (KMS charges apply); can switch any time | no | DDB EncryptionAtRest.html |
| Encryption key switch limit | Four key changes per 24 hours per table initially, then one per six-hour window (max 8 per day) | no | DDB Constraints.html |
| Reserved capacity | Provisioned capacity only; blocks of 100 units; page quotes savings up to 54% (1-year) and 77% (3-year); replicated WCUs cannot be reserved | no | https://aws.amazon.com/dynamodb/pricing/provisioned/ |
| On-demand price cut | On-demand throughput prices cut by 50% starting 2024-11-01 (posted 2024-11-14), all Regions | changed 2024-11-01 | https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-dynamo-db-reduces-prices-on-demand-throughput-global-tables/ |
| Global tables price cut | Replicated write price cut 67% (on-demand) and 33% (provisioned) from the same date | changed 2024-11-01 | https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-dynamo-db-reduces-prices-on-demand-throughput-global-tables/ |
| Free tier storage | First 25 GB of Standard storage | no | https://aws.amazon.com/dynamodb/pricing/provisioned/ |

## 4. ElastiCache

| Fact | Value | Changed? | Source |
|---|---|---|---|
| What it is | Web service to set up, manage and scale a distributed in-memory data store or cache in the cloud | no | EC WhatIs.html |
| Engines | Valkey, Memcached, Redis OSS | changed (Valkey added; page lists it first) | EC WhatIs.html |
| Latency wording | Product page: "Serverless, fully managed caching service delivering microsecond latency performance" and "scale to hundreds of millions of operations per second with microsecond latency" (the WhatIs.html page has no latency wording; the exact phrase "10 times" is not used) | no | https://aws.amazon.com/elasticache/ |
| Two formats | Serverless cache, or node-based cluster | changed (Serverless is newer than 2022) | EC WhatIs.html |
| Serverless | Create a highly available cache "in under a minute"; no instances or nodes to provision; scales automatically on memory, compute and network | changed | EC WhatIs.html |
| Serverless engine versions | Valkey 7.2 and later, Memcached 1.6.22 and later, Redis OSS 7.1 | changed | EC WhatIs.html |
| Serverless connection types | VPC or Public; public endpoints need IAM authentication and TLS 1.3 and Valkey 9.0 or later | changed | EC WhatIs.html |
| Node-based cluster | You choose node type, number of nodes, AZ placement and patch timing | no | EC WhatIs.html |
| Valkey durability | Valkey 9.0+ node-based: optional durability via Multi-AZ transactional log (zero data loss for sync writes); not for cluster mode disabled | changed | EC WhatIs.html ; EC Replication.Redis.Groups.html |
| Cluster mode disabled | One shard: one primary plus 0 to 5 read replicas; asynchronous replication; all in one Region | no | EC Replication.Redis.Groups.html ; EC WhatIs.Components.html |
| Cluster mode enabled | 1 to 500 shards (node groups), each with a primary and 0 to 5 replicas; data partitioned across shards; configuration endpoint | no | EC WhatIs.Components.html |
| Shard limit detail | 500 per cluster for Valkey 7.2+ / Redis OSS 5.0.6+; 250 for older versions; request increase via limit "Nodes per cluster per instance type" | no | EC Replication.Redis.Groups.html |
| Nodes per cluster example | Up to 90 nodes by default (e.g. 90 shards 0 replicas to 15 shards 5 replicas); 500 nodes after increase | no | EC Replication.Redis.Groups.html |
| Cluster mode comparison | Partitioning: disabled no, enabled yes; Multi-AZ optional vs required; add/delete shards: disabled no, enabled yes | no | EC WhatIs.Components.html |
| Multi-AZ with automatic failover | Replica with least replication lag promoted; "writes can resume ... typically just a few seconds"; DNS name of promoted replica propagated so primary endpoint unchanged | no | EC AutoFailover.html |
| Multi-AZ requirement | At least one replica in a different AZ than the primary; only on clusters with more than one node per shard | no | EC AutoFailover.html |
| Multi-AZ default | Enabled by default for cluster mode enabled (automatic failover required); recommended for cluster mode disabled | no | EC AutoFailover.html |
| Failover data loss | Replication is asynchronous, so a small amount of data can be lost on failover (not for durability-enabled clusters) | no | EC AutoFailover.html |
| Multi-AZ vs AOF | Multi-AZ and append-only file are mutually exclusive (Redis OSS) | no | EC AutoFailover.html |
| Without Multi-AZ | Failed primary is replaced by a new node; with no replicas the new primary starts empty and data is lost unless restored from snapshot | no | EC AutoFailover.html |
| Global datastore | Cross-Region replication (read replica clusters in other Regions) for Valkey/Redis OSS | no | EC WhatIs.Components.html |
| Backups | Snapshot of Valkey, Redis OSS or Serverless Memcached caches; written to Amazon S3; restore into a new cache | changed (Serverless Memcached backups newer; node-based Memcached has none) | EC backups.html |
| Memcached backups | Not available for node-based Memcached; available only for Memcached serverless | changed | EC backups.html ; EC SelectEngine.html |
| Backup retention | Maximum 35 days; retention limit 0 disables automatic backups; daily automatic backup with a configurable start time | no | EC backups-automatic.html |
| Manual backup limits | Up to 24 manual backups per serverless cache per 24 hours; 20 per node for node-based Valkey/Redis OSS | no | EC backups.html |
| Backup performance | Serverless backups have no performance impact; node-based can; back up from a replica; set reserved-memory-percent | no | EC backups.html |
| Encryption at rest | Encrypts disk during sync/backup/swap and backups in S3; enabled only at creation (existing cluster: backup, restore into new encrypted group); always on for serverless | no | EC at-rest-encryption.html |
| At-rest default | For Valkey the AtRestEncryptionEnabled parameter defaults to true | changed | EC at-rest-encryption.html |
| At-rest keys | Service-managed key (default) or symmetric customer managed KMS key | no | EC at-rest-encryption.html |
| Encryption in transit | TLS between clients and nodes and between nodes; always on for serverless; node-based: TransitEncryptionEnabled | no | EC in-transit-encryption.html |
| In transit on existing clusters | Modifying the setting on an existing replication group supported on Valkey 7.2+ and Redis OSS 7+ | changed | EC in-transit-encryption.html |
| Memcached encryption | In transit and at rest only from Memcached 1.6.12; at rest only on serverless Memcached; in transit enabled only at creation | changed | EC in-transit-encryption.html ; EC at-rest-encryption.html |
| mTLS | Not supported | no | EC in-transit-encryption.html |
| Minimum TLS | From 2026-04-28 AWS raises minimum TLS to 1.2 on Valkey 7.2+ and Redis OSS 6+ | changed 2026-04-28 | EC in-transit-encryption.html |
| Authentication | IAM authentication, Valkey/Redis OSS AUTH command, and Role-Based Access Control (RBAC) for authorization | changed (IAM auth newer) | EC encryption.html ; EC auth-redis.html |
| Redis OSS RBAC | Introduced with ElastiCache for Redis OSS 6.0 (Enhanced) | no | EC SelectEngine.html |
| Memcached model | Simplest model; multi-threaded; scale out and in by adding/removing nodes; no replication, no persistence/backups (node-based), no Multi-AZ failover | no | EC SelectEngine.html |
| Memcached cluster size | 1 to 60 nodes per cluster; up to 300 nodes per customer per Region | no | EC WhatIs.Components.html |
| Memcached partitioning | Data is partitioned across nodes; client should use consistent hashing | no | EC WhatIs.Components.html |
| Memcached Auto Discovery | Client connects to the configuration endpoint and learns all node endpoints, even as nodes are added or removed; not available for Valkey/Redis OSS | no | EC AutoDiscovery.html |
| Valkey/Redis vs Memcached | Valkey/Redis: replication, automatic failover, backup/restore, pub/sub, sorted sets, complex data types, geospatial; Memcached: multi-threaded, simple data types | no | EC SelectEngine.html |
| Valkey/Redis single-threaded | Comparison table lists multi-threaded "No" for Valkey/Redis OSS and "Yes" for Memcached | no | EC SelectEngine.html |
| Data tiering | Memory plus SSD on r6gd node type (engine 6.2+) | no | EC SelectEngine.html |
| Valkey features by version | 7.2 Functions and sharded pub/sub; 8.0 memory efficiency; 8.1 Bloom filters; 8.2 vector search; 9.0 full-text search, hash field expiration, durability | changed | EC SelectEngine.html |
| Lazy loading (cache-aside) | App checks cache first; on miss reads database then writes cache. Pro: only requested data cached, node failure not fatal. Con: miss penalty (three trips), stale data | no | EC Strategies.html |
| Write-through | Update cache whenever the database is written. Pro: cache never stale. Con: write penalty (two trips), missing data on new node, cache churn | no | EC Strategies.html |
| Adding TTL | TTL in seconds per key; expired key is treated as not found; combine with lazy loading or write-through to limit stale data and cache clutter | no | EC Strategies.html |
| Combination | "Lazy loading with write-through" and TTL give advantages of each | no | EC Strategies.html |
| Read replicas | Reading from replicas can significantly improve performance | no | EC Strategies.html |
| MemoryDB | Durable in-memory database, Valkey and Redis OSS compatible; microsecond reads and single-digit millisecond writes; data stored durably across multiple AZs via Multi-AZ transactional log; usable as primary database without a separate cache | no | MDB what-is-memorydb.html |
| MemoryDB vs ElastiCache | MemoryDB: durable primary database; ElastiCache: caching in front of another primary database | no | MDB related-services-choose-between-memorydb-and-redis.html |

## 5. Purpose-built databases

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Neptune | Fully managed graph database; Gremlin, openCypher, SPARQL; recommendation engines, fraud detection, knowledge graphs | no | NEP intro.html |
| Neptune architecture | One primary plus up to 15 Neptune Replicas on the same cluster volume; storage across multiple AZs; designed for greater than 99.99 percent availability | no | NEP intro.html |
| Neptune Analytics | Separate analytics engine to analyze graph data in memory | changed (newer) | NEP intro.html |
| DocumentDB | MongoDB-compatible fully managed document database | no | DOC what-is.html |
| DocumentDB storage | Six copies across three AZs; grows in 10 GB increments to a maximum of 256 TiB for engine 8.0+ (128 TiB earlier) | changed (256 TiB newer) | DOC what-is.html |
| DocumentDB cluster | 0 to 16 instances (primary plus up to 15 replicas), reader endpoint, replica lag often single-digit milliseconds | no | DOC what-is.html |
| DocumentDB backups | PITR to any second within retention, up to the last 5 minutes; retention up to 35 days; stored in S3 | no | DOC what-is.html |
| DocumentDB elastic clusters | Millions of reads/writes per second and petabytes of storage; Serverless instance class and I/O-optimized storage configuration exist | changed | DOC what-is.html |
| Keyspaces | Serverless, managed Apache Cassandra-compatible database using CQL | no | KS what-is-keyspaces.html |
| Timestream for LiveAnalytics | Purpose-built time series database; memory store for recent data, magnetic store for history; serverless; at least 3 AZs | no | TS what-is-timestream.html |
| Timestream LiveAnalytics availability | AWS closed new customer access effective 2025-06-20; existing workloads unaffected; evaluate Timestream for InfluxDB instead | changed 2025-06-20 | TS AmazonTimestreamForLiveAnalytics-availability-change.html |
| Timestream for InfluxDB | Recommended alternative with single-digit millisecond query response | changed | TS what-is-timestream.html |
| OpenSearch Service | Managed OpenSearch (and legacy Elasticsearch OSS up to 7.10); search, log analytics, real-time monitoring, clickstream | no | OS what-is.html |
| OpenSearch scale | Up to 1002 data nodes and up to 25 PB attached storage; UltraWarm and cold storage; Multi-AZ across two or three AZs | changed | OS what-is.html |
| OpenSearch Extended Support | Charges apply when domain runs a version past standard support (e.g. standard support for Elasticsearch/OpenSearch older versions ends 2025-11-07) | changed | OS what-is.html |
| MemoryDB | Durable Valkey/Redis OSS compatible in-memory database (see section 4) | no | MDB what-is-memorydb.html |
| QLDB | Amazon QLDB end of support / full shutdown 2025-07-31 (listed in Services in Full Shutdown); re-confirms facts.md | changed 2025-07-31 | GR full_shutdown_services.html |
| Aurora Serverless v1 | End of life 2025-03-31; no new v1 clusters from 2025-01-08; remaining clusters auto-migrated (v1 to v2) or converted to provisioned (search-result excerpt of AWS docs; page fetch returned title only) | changed 2025-03-31 | AUR aurora-serverless-v2.upgrade.html |
| Aurora Serverless v2 renamed | AWS blog notice (April 2026) says Aurora Serverless v2 renamed "Aurora serverless"; current docs use "Aurora serverless" | changed 2026 | AUR aurora-serverless-v2.html ; https://aws.amazon.com/blogs/database/upgrade-from-amazon-aurora-serverless-v1-to-v2-with-minimal-downtime/ |

## 6. Prices (illustrative, us-east-1, USD)

Prices below come from the public AWS Price List files (official pricing.us-east-1.amazonaws.com offers, region us-east-1 / "US East (N. Virginia)", On-Demand terms), because the aws.amazon.com pricing pages did not render rate tables in text. Price List publication dates: RDS and Aurora 2026-10-06, ElastiCache 2026-09-14, DynamoDB 2026-09-11, DAX 2026-10-09. PL keys: PL-RDS = https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRDS/current/us-east-1/index.json ; PL-EC = .../AmazonElastiCache/current/us-east-1/index.json ; PL-DDB = .../AmazonDynamoDB/current/us-east-1/index.json ; PL-DAX = .../AmazonDAX/current/us-east-1/index.json.

| Fact | Value | Changed? | Source |
|---|---|---|---|
| RDS PostgreSQL db.t4g.micro Single-AZ | 0.016 USD per hour | no | PL-RDS |
| RDS PostgreSQL db.t4g.micro Multi-AZ | 0.032 USD per hour (2x single) | no | PL-RDS |
| RDS PostgreSQL db.m7g.large Single-AZ | 0.168 USD per hour | no | PL-RDS |
| RDS PostgreSQL db.m7g.large Multi-AZ | 0.337 USD per hour (about 2x single) | no | PL-RDS |
| RDS PostgreSQL db.r7g.large Single-AZ / Multi-AZ | 0.239 / 0.478 USD per hour | no | PL-RDS |
| RDS gp3 storage (PostgreSQL) Single-AZ | 0.115 USD per GB-month | no | PL-RDS |
| RDS gp3 storage Multi-AZ DB instance | 0.23 USD per GB-month (2x) | no | PL-RDS |
| RDS gp3 storage Multi-AZ DB cluster (readable standbys) | 0.345 USD per GB-month (3x) | no | PL-RDS |
| RDS gp3 extra IOPS / throughput (Single-AZ) | 0.02 USD per IOPS-month; 0.08 USD per MiBps-month | no | PL-RDS |
| RDS io2 storage Single-AZ / Multi-AZ | 0.125 / 0.25 USD per GB-month; IOPS 0.10 / 0.20 USD per IOPS-month | no | PL-RDS |
| RDS io1 storage Single-AZ / Multi-AZ (PostgreSQL) | 0.125 / 0.25 USD per GB-month; IOPS 0.10 / 0.20 USD per IOPS-month | no | PL-RDS |
| RDS gp2 storage (PostgreSQL) Single-AZ / Multi-AZ | 0.115 / 0.23 USD per GB-month | no | PL-RDS |
| RDS backup storage beyond free allocation | 0.095 USD per GB-month (PostgreSQL) | no | PL-RDS |
| RDS Proxy | 0.015 USD per vCPU-hour of the associated RDS PostgreSQL instance; Aurora Serverless v2 0.015 USD per ACU-hour | no | PL-RDS |
| Aurora PostgreSQL db.r7g.large, Standard | 0.276 USD per hour | no | PL-RDS |
| Aurora PostgreSQL db.r7g.large, I/O-Optimized | 0.359 USD per hour | no | PL-RDS |
| Aurora storage, Standard | 0.10 USD per GB-month consumed | no | PL-RDS |
| Aurora I/O, Standard | 0.20 USD per 1 million I/O requests | no | PL-RDS |
| Aurora storage, I/O-Optimized | 0.225 USD per GB-month; no I/O charges | no | PL-RDS |
| Aurora Serverless v2 (PostgreSQL), Standard | 0.12 USD per ACU-hour | no | PL-RDS |
| Aurora Serverless v2 (PostgreSQL), I/O-Optimized | 0.16 USD per ACU-hour | no | PL-RDS |
| Aurora backup storage beyond free allocation | 0.021 USD per GB-month (Aurora PostgreSQL) | no | PL-RDS |
| Aurora Global Database replicated write I/O | 0.20 USD per 1 million replicated write I/O requests | no | PL-RDS |
| DynamoDB on-demand write | 0.625 USD per million write request units | changed 2024-11-01 (50% cut) | PL-DDB |
| DynamoDB on-demand read | 0.125 USD per million read request units | changed 2024-11-01 (50% cut) | PL-DDB |
| DynamoDB provisioned write | 0.00065 USD per WCU-hour (first 25 WCU free) | no | PL-DDB |
| DynamoDB provisioned read | 0.00013 USD per RCU-hour (first 25 RCU free) | no | PL-DDB |
| DynamoDB storage | 0.25 USD per GB-month after first 25 GB free (Standard); 0.10 USD per GB-month (Standard-IA) | no | PL-DDB |
| DynamoDB Standard-IA throughput | On-demand 0.78 USD per million WRU and 0.155 USD per million RRU; provisioned 0.00081 per WCU-hour and 0.00016 per RCU-hour | no | PL-DDB |
| DynamoDB PITR | 0.20 USD per GB-month | no | PL-DDB |
| DynamoDB on-demand backup | 0.10 USD per GB-month; restore 0.15 USD per GB | no | PL-DDB |
| DynamoDB export / import | Export 0.10 USD per GB; incremental export 0.10 USD per GB; import 0.15 USD per GB | no | PL-DDB |
| DynamoDB global tables replicated writes | 0.625 USD per million replicated WRU (on-demand); 0.00065 USD per replicated WCU-hour (provisioned) | changed 2024-11-01 | PL-DDB |
| DynamoDB Streams reads | 2.5 million read request units free per month, then 0.0000002 USD per unit | no | PL-DDB |
| DAX dax.t3.small | 0.04 USD per node-hour | no | PL-DAX |
| ElastiCache cache.t4g.micro | Valkey 0.0128; Redis OSS 0.016; Memcached 0.016 USD per node-hour | changed (Valkey priced lower) | PL-EC |
| ElastiCache cache.m7g.large | Valkey 0.1264; Redis OSS 0.158; Memcached 0.158 USD per node-hour | changed | PL-EC |
| Valkey vs Redis OSS node discount | Valkey node price is 80% of Redis OSS (0.1264 / 0.158 = 0.8; derived) | changed | PL-EC |
| ElastiCache Serverless data storage | Valkey 0.084 USD per GB-hour; Redis OSS and Memcached 0.125 USD per GB-hour | changed | PL-EC |
| ElastiCache Serverless ECPUs | Valkey 0.0023 USD per million ECPUs; Redis OSS and Memcached 0.0034 USD per million | changed | PL-EC |
| ElastiCache Serverless minimum metered storage | 100 MB for Valkey; 1 GB for Redis OSS and Memcached (from pricing page worked examples) | changed | https://aws.amazon.com/elasticache/pricing/ |
| ElastiCache snapshot storage | 0.085 USD per GB-month beyond free allocation | no | PL-EC |

## Unconfirmed

- RDS Multi-AZ DB cluster engines: the page names only RDS for MySQL and PostgreSQL in its replica lag text; a dedicated supported-engines table (Concepts.RDS_Fea_Regions_DB-eng.Feature.MultiAZDBClusters) was not read.
- Deletion protection default for CLI/API creation: the Deleting a DB instance page states only that it is on by default for console-created instances; the CLI/API default (expected off) is not stated there.
- RDS encrypted read replica key rule: the encryption page says both "same KMS key as the source when in the same Region" (limitations) and "or with a different KMS key via KmsKeyId" (key considerations); not reconciled.
- RDS snapshot sharing details (maximum accounts, public sharing): the share-snapshot page was not read; only the copy page was.
- RDS Proxy supported-engines table and the Regional/version table (Concepts.RDS_Fea_Regions_DB-eng.Feature.RDSProxy) not read; engine list is taken from the limitations sections (MariaDB, MySQL, PostgreSQL, SQL Server).
- IAM database authentication supported engines is stated on the page as MariaDB, MySQL and PostgreSQL; Aurora IAM auth not read separately.
- Database Insights / Performance Insights: the exact end-of-support date of the legacy Performance Insights paid tiers (if any) was not found on the pages read; only that Database Insights Advanced is the default and 7 days / 1 to 24 months retention.
- Aurora 10 GiB storage segments: not stated on the storage pages read.
- Aurora "six copies, tolerate loss of two copies for writes and three for reads" quorum wording: not on the pages read (only "six storage nodes across Availability Zones").
- Aurora Global Database previous limit of 5 secondary Regions: current page says up to 10 secondary clusters; the earlier value and change date are not on the page.
- Aurora Auto Scaling for replicas (target tracking, default metrics): not read.
- DynamoDB prior transaction limit of 25 items and the date it became 100: the pages state only 100; the brief says 25 earlier; date unconfirmed.
- DynamoDB prior capacity-mode switching limit (reported once per 24 hours) and date of change to four per 24-hour rolling window for provisioned to on-demand: pages state only the current rule.
- DynamoDB on-demand and on-demand-backup retention wording ("kept until deleted") and restore-to-new-table for on-demand backups: the backup pages were not read.
- DAX: node types and the 3-node production recommendation not confirmed (the microsecond latency wording is now confirmed on DAX.html).
- DynamoDB TTL timing: page says "typically within a few days"; no hour figure (older documents mention 48 hours) found on the page.
- DynamoDB tables-per-account earlier default (256) not on the page.
- DynamoDB GSI "can be added or removed at any time" is supported only indirectly (GSI on existing tables); the Managing GSIs page was not read.
- ElastiCache Serverless limits (maximum storage, maximum ECPU per second): the limits page returned only a title; not confirmed.
- ElastiCache engine "Valkey added in 2024" date: page does not give a date.
- ElastiCache failover time in seconds: page says "typically just a few seconds" for writes to resume; no numeric figure.
- Keyspaces specifics (replication copies, capacity modes, PITR retention): the intro page read gave only the description.
- Neptune storage maximum size and DocumentDB/Neptune pricing: not read.
- Timestream for InfluxDB details: only the recommendation was read.
- RDS Extended Support per-vCPU-hour prices: charges page not read.
- RDS Custom for Oracle/SQL Server pricing and feature specifics: not read.
- DynamoDB Standard-IA, reserved capacity and Database Savings Plans discount figures: only the Savings Plans 35 percent figure exists in facts.md; the DynamoDB pricing page did not render the tables.
- aws.amazon.com RDS, Aurora, RDS Proxy and ElastiCache pricing pages did not render rate tables; prices come from the Price List files and may differ from the console by Region or term.
- ElastiCache reserved node discount and Database Savings Plans: not read.
- RDS read replica "can itself be Multi-AZ" and RDS Multi-AZ read replica behaviour: only the topic title was seen; body not read.
- OpenSearch Serverless details and pricing: not read.

## Confidence notes

- High confidence: RDS Multi-AZ failover wording (60-120 s for DB instance, under 35 s for DB cluster), retention (0 to 35, console 7, API 1), PITR 5-minute log upload, storage autoscaling rules, gp3 baselines, IAM token 15 minutes, Secrets Manager 7-day rotation default, RDS Proxy 66% claim, read replica count 15 (MySQL page and quota table), DynamoDB item size, RCU/WCU rules, GSI/LSI quotas, 10 GB LSI limit, 100-item transactions, 24-hour streams, PITR 35 days, MREC/MRSC rules, DAX 5-minute TTL, ElastiCache cluster mode limits and engine list.
- Medium confidence: the RDS PostgreSQL read replica count (15) is inferred from the account quota table, not from a PostgreSQL-specific sentence; Aurora Serverless v1 retirement details come from a search excerpt; prices come from the Price List files rather than rendered pricing pages; OpenSearch and DocumentDB limits are as stated on landing pages.
- Many rows are newer than SAA-C03 (Valkey, ElastiCache Serverless durability, Aurora DSQL, Limitless, MRSC global tables, Database Insights, Aurora serverless rename). Exam questions still center on classic behavior; treat these as "know it exists".
- DynamoDB units: one page says "write request unit" for on-demand and "write capacity unit" for provisioned; both use 1 KB / 4 KB sizes.
- The exam guide (task statements 2.2, 3.3, 4.3) and facts.md sections were read first; section order follows the brief.
- The Price List "publicationDate" values are 2026-09 to 2026-10; prices are perishable.

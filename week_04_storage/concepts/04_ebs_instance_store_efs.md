Exam tasks: 3.1, 4.1, 2.2

# 04 — EBS, instance store and EFS

## What it is

Three ways to give servers a disk:

| | What it is | Shared? | Lifetime |
|---|---|---|---|
| **EBS** (Elastic Block Store) | A network disk (block storage) for one EC2 instance | One instance (Multi-Attach: a few) | Lives on its own until you delete it |
| **Instance store** | Disks inside the host server | One instance | Gone when the instance stops or terminates |
| **EFS** (Elastic File System) | A shared NFS folder that grows by itself | Thousands of clients | Lives on its own |

Task 3.1 asks which storage fits a performance need. Task 4.1 asks for the cheapest block type and for backup
strategy. Task 2.2 is snapshots and multi-AZ file storage. Drill 03 sizes and prices EBS volumes.

## How it works

### EBS basics

- A volume lives in **one Availability Zone** and attaches only to instances in that AZ. To move it, snapshot it and restore elsewhere.
- Volumes persist after the instance stops. The root volume is deleted at termination by default. Other volumes are kept.
- You pay for provisioned size (and IOPS or throughput where they are provisioned), **even when the instance is stopped**.
- Encryption uses KMS keys and covers data at rest, snapshots and the traffic to the instance.

### Volume types

| Type | Kind | Size | Max IOPS | Max throughput | Boot? | Use |
|---|---|---|---|---|---|---|
| **gp3** | SSD, general | 1 GiB–64 TiB | 80,000 | 2,000 MiB/s | yes | Default choice for almost everything |
| **gp2** | SSD, general | 1 GiB–16 TiB | 16,000 | 250 MiB/s | yes | Older. IOPS tied to size |
| **io2 Block Express** | SSD, provisioned | 4 GiB–64 TiB | 256,000 | 4,000 MiB/s | yes | Databases needing the most IOPS, 99.999 % durability |
| **io1** | SSD, provisioned | 4 GiB–16 TiB | 64,000 | 1,000 MiB/s | yes | Older provisioned IOPS |
| **st1** | HDD, throughput | 125 GiB–16 TiB | 500 | 500 MiB/s | **no** | Big sequential reads: logs, data warehouses |
| **sc1** | HDD, cold | 125 GiB–16 TiB | 250 | 250 MiB/s | **no** | Rarely used data, lowest cost |

The gp3 maximums changed in September 2025. It was 16 TiB, 16,000 IOPS and 1,000 MiB/s. Every io2 volume is now Block Express.

### IOPS and throughput maths

**gp2**: **3 IOPS per GiB**, at least 100, at most 16,000 (reached at 5,334 GiB). A 200 GiB gp2 volume gives 600 IOPS.
Volumes under 1 TiB can burst to 3,000 IOPS using credits. Credits run out. The `BurstBalance` metric shows what is left.
To get more IOPS from gp2 you must buy more GiB.

**gp3** includes **3,000 IOPS and 125 MiB/s at any size**, with no burst system. You pay extra to raise them:

- IOPS: up to **500 IOPS per GiB**, and up to 80,000. Reaching 80,000 needs at least 160 GiB.
- Throughput: up to **0.25 MiB/s per provisioned IOPS**, and up to 2,000 MiB/s.
- Worked example: a 100 GiB gp3 volume can have at most 50,000 IOPS (500 × 100). To get 400 MiB/s you need at least
  1,600 IOPS, which the free 3,000 already covers.
- Second example: 40 GiB asking for 30,000 IOPS fails, because 40 × 500 = 20,000.

**io2**: up to **1,000 IOPS per GiB**, up to 256,000 on Nitro instances. **io1**: 50 IOPS per GiB, up to 64,000.

### Choosing a type

1. Need more than 80,000 IOPS, more than 2,000 MiB/s, sub-millisecond latency or Multi-Attach? **io2**.
2. Big sequential scans, not a boot volume? **st1** (or **sc1** if rarely used and cheapest wins).
3. Everything else, including boot volumes: **gp3**. It is also cheaper per GiB than gp2.

HDD volumes can never be boot volumes. Migrate gp2 to gp3 in place with Elastic Volumes.

### Multi-Attach

One **io1 or io2** volume attached to up to **16 Nitro instances in the same AZ**. For clustered applications. Needs a cluster-aware
file system (XFS or ext4 are not). It cannot be a boot volume. gp3, st1 and sc1 do not support it.

### Elastic Volumes

Change size, type, IOPS or throughput of an **in-use** volume with no downtime. Size can only grow. Up to **four
modifications in 24 hours**, and each must finish first. (changed: older docs said wait six hours.) A big volume
can take hours. There is no charge for the change itself.

### Snapshots

- A **snapshot** is a point-in-time backup stored in S3 (you cannot see the bucket). It is **incremental**: after the first, only changed blocks are saved.
- Deleting one snapshot does not delete blocks that later snapshots use.
- **Copy across Regions** for disaster recovery. Share with other accounts.
- **Encrypt an unencrypted volume:** you cannot do it in place. Snapshot it, **copy the snapshot with encryption on**, create a volume from the copy. An encrypted volume cannot be made unencrypted.
- **Encryption by default** is a per-Region account setting. It affects new volumes only.
- **Fast Snapshot Restore (FSR)** makes volumes created from a snapshot fully initialised at once. Enabled per snapshot per AZ and billed per hour.
- **Snapshot Archive tier**: up to 75 % cheaper storage for snapshots kept at least 90 days. Restoring takes up to 72 hours.
- **Recycle Bin**: a retention rule that lets you recover deleted snapshots, AMIs and volumes.
- **Data Lifecycle Manager (DLM)** creates and deletes snapshots on a schedule, free. **AWS Backup** does the same centrally, across services.
- AWS never backs up EBS for you. You schedule it.

### Instance store

Disks physically attached to the host. Very fast, **no extra charge**, included in the instance price. Data **survives
a reboot** but is **erased on stop, hibernate or terminate**. Use it for caches, buffers and
scratch data. Never for data you cannot rebuild. Only EBS-backed instances can be stopped and started.

### EFS

**EFS** is a managed, elastic **NFS** file system for **Linux**. Windows instances are not supported.

- **NFSv4.1 and v4.0.** It grows and shrinks to petabytes by itself. No capacity to provision.
- **Regional** (the default choice): data in 3 or more AZs, 11 nines of durability, 99.99 % availability.
- **One Zone**: one AZ, cheaper, no protection against losing the AZ.
- You reach it through a **mount target**: one per AZ, with security groups. Mount from EC2, ECS, EKS, Lambda, Fargate, or on-premises through Direct Connect or VPN.
- **Access points** enforce a POSIX user and a root directory for an application.
- Encryption at rest (KMS) is chosen at creation. In transit uses TLS at mount time.
- It offers close-to-open consistency and advisory locking. Max file size 47.9 TiB.

**Storage classes** (lifecycle management moves files by last access: 1, 7, 14, 30, 60, 90, 180, 270 or 365 days):

| Class | For | Notes |
|---|---|---|
| Standard | Active files | About 1 ms reads |
| Infrequent Access (IA) | A few reads a quarter | Tens of ms; min billing 128 KiB per file; per-GB access fee |
| Archive | A few reads a year | 90-day minimum; needs Elastic throughput |
| One Zone / One Zone-IA | The same, in one AZ | For One Zone file systems |

**Throughput modes:** **Elastic** (the recommended default: scales by itself, pay per GB read or written, best for spiky
loads), **Provisioned** (you set MiB/s regardless of size), **Bursting** (baseline grows with Standard size, 50 KiB/s per GiB).
**Performance modes:** General Purpose (default, recommended). Max I/O is the older, legacy option.

## Numbers to know

- EBS: gp3 **3,000 IOPS / 125 MiB/s** free; max **80,000 / 2,000**; 1 GiB–**64 TiB**. gp2 **3 IOPS/GiB**, max 16,000.
- io2 BE: **256,000** IOPS, **4,000** MiB/s, **64 TiB**, 99.999 % durable. io1 max **64,000**.
- st1 500 / 500; sc1 250 / 250; 125 GiB minimum; **not bootable**.
- Multi-Attach: io1/io2 only, **16** instances, same AZ.
- Elastic Volumes: **4** changes per 24 hours. Snapshot archive: **90**-day minimum, up to **72 hours** to restore.
- EFS: NFS, **Linux only**, **1** mount target per AZ, **47.9 TiB** max file; 128 KiB minimum billing in IA and Archive.

## When to choose it

| Workload | Choose |
|---|---|
| Boot volume, web app, small database | gp3 |
| Database needing 100,000 IOPS or sub-ms latency | io2 Block Express |
| Clustered app writing the same block volume from several nodes | io2 with Multi-Attach |
| Hadoop, log processing, big sequential reads | st1 |
| Cold data on a disk, cheapest | sc1 |
| Scratch space, cache, buffers, high local IOPS | Instance store |
| Shared files for many Linux servers | EFS |
| Shared files, rarely touched | EFS with Infrequent Access lifecycle |
| Scheduled backups | DLM or AWS Backup |

## Exam traps

- **EBS is AZ-scoped.** "Attach the volume to an instance in another AZ" needs snapshot and restore.
- **Instance store survives a reboot, not a stop.** Do not store anything you need.
- **EFS from Windows.** Not supported. Windows file shares mean FSx for Windows File Server (note 05).
- **HDD as boot volume.** st1 and sc1 cannot boot.
- **gp2 burst credits.** A volume that works constantly drains its credits and slows. Move to gp3.
- **Multi-Attach on gp3.** Only io1 and io2.
- **Encrypting an existing volume.** Snapshot, encrypted copy, new volume.
- **Provisioned IOPS above 500 per GiB on gp3.** Rejected. Size or type must change.
- **Snapshots are per volume, not per instance,** and do not happen on their own.
- **EFS One Zone** does not survive the loss of an AZ.
- **A shared database disk across AZs.** A single EBS volume cannot do that.
- **Archive tier snapshots** cannot be used until restored (hours).

## Cost angle

- Illustrative us-east-1 prices per GB-month: **gp3 0.08**, gp2 0.10, io2 0.125 (plus IOPS), st1 0.045, sc1 0.015. Snapshot 0.05; archived snapshot 0.0125.
- gp3 beats gp2 by about 20 % per GiB, and also stops you buying size just to get IOPS. Extra gp3 IOPS cost 0.005 each per month above 3,000, extra throughput 0.06 per MiB/s above 125.
- io2 charges for IOPS as well: 0.065 per IOPS-month for the first 32,000.
- Stopped instances still pay for their EBS volumes. Delete unattached volumes and old snapshots.
- Snapshots are incremental, so many daily snapshots cost far less than many full copies.
- EFS Standard costs about **3.75 times gp3** per GB (0.30 against 0.08), but it is shared, multi-AZ and grows by itself. Move cold files to IA (0.025) or Archive (0.008).
- Elastic throughput bills per GB moved: 0.03 read, 0.06 written. Steady, heavy workloads may prefer Provisioned.
- Instance store is free, but you pay for the larger instance type that carries it.

## Comparison

| | EBS | Instance store | EFS |
|---|---|---|---|
| Type | Block | Block | File (NFS) |
| Scope | One AZ | One host | Region (or one AZ) |
| Shared by | One instance (Multi-Attach: 16) | One instance | Thousands of clients |
| Survives stop | Yes | **No** | Yes |
| Survives terminate | If not the root volume | No | Yes |
| Backup | Snapshots, DLM, AWS Backup | None | AWS Backup, replication |
| Capacity | You choose | Fixed by instance | Elastic |
| OS | Any | Any | Linux |
| Price | Per GiB (+IOPS) | Included | Per GB used, 3.75 × gp3 |

Now do drill 03 (pick the volume) and drill 10 (which storage service).

Exam tasks: 3.1, 4.1

# 05 — FSx, Storage Gateway and choosing storage

## What it is

Two groups of services fill the gaps around S3, EBS and EFS:

| Group | Services | Job |
|---|---|---|
| **Managed file systems** | FSx for Windows File Server, Lustre, NetApp ONTAP, OpenZFS | File storage with a protocol or feature EFS does not have |
| **Hybrid storage** | Storage Gateway (S3 File, Volume, Tape) | On-premises apps that use AWS storage through a local cache |

This note finishes the storage tour with the **big decision table**. Task 3.1 asks for the right storage service and the
right hybrid option. Task 4.1 asks for the cheapest fit, including data transfer services. Drill 10 is the decision drill.

## How it works

### Amazon FSx

**FSx** runs well-known file systems for you: patching, backups, failover. Pick by the **protocol or product** the application already uses.

| FSx for | Protocol | Clients | Pick it when |
|---|---|---|---|
| **Windows File Server** | **SMB** | Windows, current Linux | Windows apps, home directories, shares joined to **Active Directory** |
| **Lustre** | Lustre (POSIX) | Linux | HPC, machine learning, video, financial modelling: very fast shared scratch space |
| **NetApp ONTAP** | **NFS, SMB and iSCSI** | Windows, Linux, macOS | Moving NetApp from on-premises, or one system for all three protocols |
| **OpenZFS** | NFS v3 to v4.2 | Linux, Windows, macOS | Moving ZFS or Linux file servers without changing apps |

**FSx for Windows File Server**
- Real Windows file server: NTFS ACLs, shadow copies (VSS), DNS aliases, daily automatic backups.
- Joins an **AWS Managed Microsoft AD** or your own AD when you create it.
- **Single-AZ** or **Multi-AZ** (a standby in a second AZ with automatic failover). SSD or HDD storage.
- Encrypted at rest with KMS and in transit with SMB Kerberos.

**FSx for Lustre**
- Sub-millisecond latency, up to many TB/s and millions of IOPS.
- **Scratch** deployment: temporary storage, data is **not replicated** and is lost if a file server fails.
- **Persistent** deployment: longer term, data replicated, failed servers replaced.
- **S3 link:** the file system presents an S3 bucket as files and writes results back to S3. The classic pattern: S3 holds the data, Lustre runs the job, results go back to S3.

**FSx for NetApp ONTAP**
- Snapshots, FlexClone clones, SnapMirror replication to on-premises NetApp, deduplication and compression, and tiering to a cheaper capacity pool.
- The answer when a question says NFS, SMB **and** iSCSI, or "NetApp".

**FSx for OpenZFS**
- Up to 2 million IOPS, latency in hundreds of microseconds, instant snapshots and clones.
- Multi-AZ or Single-AZ deployments. The answer for "move our ZFS file server".

All FSx systems encrypt at rest with KMS.

### AWS Storage Gateway

A **gateway** is a virtual machine (or hardware appliance) in your data centre. Apps talk to it with a normal protocol. It keeps
a **local cache** of recent data and moves the rest to AWS.

| Gateway | Apps see | Data lives in | Use for |
|---|---|---|---|
| **S3 File Gateway** | NFS or SMB shares | **S3 objects** (one file = one object) | File shares backed by S3; S3 lifecycle, versioning and replication apply |
| **Volume Gateway, cached** | iSCSI volumes | S3; **hot data cached locally** | Low-latency hot data, S3 holds the whole set |
| **Volume Gateway, stored** | iSCSI volumes | **On premises**; async snapshots to S3 | The whole data set must stay local, with cloud backup |
| **Tape Gateway** | A virtual tape library | Tapes in S3, archived to Glacier Flexible or Deep Archive | Replace physical tape backup without changing the backup software |

- Volume snapshots are stored as **EBS snapshots** and can seed a new EBS volume.
- Cached volumes are 1 GiB–32 TiB each. Stored volumes are 1 GiB–16 TiB each.
- **FSx File Gateway** gave on-premises access to FSx for Windows File Server shares. It is retired for new customers: closed to new customers, existing customers keep it. The exam may still name it.
- Deploy as a VM (VMware ESXi, Hyper-V, KVM, Nutanix AHV), an EC2 AMI or a hardware appliance.

### Making S3 faster

| Technique | What it does |
|---|---|
| **Multipart upload** | Parallel parts for big objects (note 01) |
| **Byte-range fetches** | Download parts of an object in parallel, or only the bytes you need |
| **More prefixes** | Each prefix has its own 3,500 write / 5,500 read per second. 10 prefixes → 55,000 reads |
| **Transfer Acceleration** | Upload to the nearest CloudFront edge location, which carries the data to S3 over AWS's network. Long distances, a central bucket |
| **S3 Express One Zone** | Single-digit-millisecond access (note 01) |

**Transfer Acceleration** needs it enabled on the bucket, a DNS-compliant name **without periods**, and the endpoint
`bucket.s3-accelerate.amazonaws.com`. It can take up to 20 minutes to start working, and it adds transfer charges. Use it
for customers uploading from around the world to one bucket.

### Moving data and backing it up (later weeks)

- **AWS DataSync:** online transfer between on-premises (NFS, SMB, HDFS), other clouds and S3, EFS or FSx. Scheduled, with integrity checks.
- **AWS Transfer Family:** managed **SFTP, FTPS, FTP and AS2** into and out of S3 or EFS.
- **AWS Backup:** central, policy-based backups across EBS, S3, EFS, FSx, RDS and more, with cross-Region copy and vault lock.
- **Snow family (Snowball Edge):** physical devices for offline transfer. Closed to new customers since 2025-11-07. The exam guide still lists it. The successors are DataSync (online) and the AWS Data Transfer Terminal (physical).

### The big decision table

Read the scenario for the **keyword** that rules the other options out.

| Scenario | Choose | Why |
|---|---|---|
| Photos for a web site, grows without limit, read over HTTP | **S3** | Object storage, infinite, cheap |
| Boot disk and database volume for one EC2 instance | **EBS gp3** | Block, low latency |
| A database needing 200,000 IOPS | **EBS io2 Block Express** | Highest IOPS |
| 30 web servers share one uploads folder (Linux) | **EFS** | Shared NFS across AZs |
| Windows file shares with Active Directory permissions | **FSx for Windows** | SMB, AD, NTFS ACLs |
| ML training, thousands of cores, data in S3, results back to S3 | **FSx for Lustre** | Fast parallel file system with S3 link |
| Migrate a NetApp filer, clients speak NFS, SMB and iSCSI | **FSx for NetApp ONTAP** | Multi-protocol |
| Move an on-premises ZFS server unchanged | **FSx for OpenZFS** | Same file system |
| Cache for a high-speed temporary working set on the host | **Instance store** | Fastest, free, ephemeral |
| On-premises app needs a file share but wants the data in S3 | **S3 File Gateway** | NFS/SMB front, S3 behind |
| On-premises app needs iSCSI, whole data set stays local | **Volume Gateway, stored** | Local primary, cloud backup |
| On-premises app needs iSCSI, hot data local, rest in the cloud | **Volume Gateway, cached** | S3 primary, local cache |
| Replace tape backups without changing the backup software | **Tape Gateway** | Virtual tapes into Glacier |
| Nightly sync of an on-premises NFS share into S3 | **DataSync** | Managed transfer |
| Partners upload with SFTP into S3 | **Transfer Family** | Managed SFTP |
| Archive 500 TB, nobody reads it for years | **S3 Glacier Deep Archive** | Cheapest per GB |
| Backups of EBS, EFS and RDS under one policy | **AWS Backup** | Central plans |

## Numbers to know

- FSx: Windows = **SMB**, **Active Directory**; Lustre = scratch (not replicated) or persistent; ONTAP = **NFS + SMB + iSCSI**; OpenZFS = NFS.
- Storage Gateway: **4** types (S3 File, FSx File, Volume, Tape). Cached volumes up to **32 TiB** each, stored volumes up to **16 TiB** each.
- Transfer Acceleration: up to **20 minutes** to activate; no periods in the bucket name.
- Prefix scaling: **10 prefixes = 55,000** reads a second.
- Snowball Edge: closed to new customers since **2025-11-07**.

## When to choose it

| If the question says… | Think |
|---|---|
| SMB, Active Directory, Windows | FSx for Windows |
| HPC, ML, "link to S3", sub-millisecond | FSx for Lustre |
| NetApp, iSCSI + NFS + SMB | FSx for ONTAP |
| ZFS | FSx for OpenZFS |
| Linux, NFS, shared, elastic | EFS |
| On-premises + cache + S3 | S3 File Gateway |
| On-premises + iSCSI | Volume Gateway |
| Tape | Tape Gateway |
| Customers worldwide upload to one bucket | Transfer Acceleration |
| Online migration of files | DataSync |

## Exam traps

- **EFS for Windows.** Not supported. FSx for Windows.
- **Lustre scratch for data you need to keep.** It is lost if a server fails. Use persistent or write back to S3.
- **iSCSI means Volume Gateway,** not File Gateway. NFS or SMB to S3 means S3 File Gateway.
- **Stored vs cached.** Stored keeps all data on premises. Cached keeps only hot data locally.
- **Tape Gateway** archives to Glacier Flexible Retrieval or Deep Archive. Restores are slow.
- **FSx File Gateway** is closed to new customers. Prefer S3 File Gateway or FSx directly.
- **Transfer Acceleration for a bucket with periods in its name.** Not possible.
- **Transfer Acceleration to speed up a transfer inside one Region.** It helps over long distances.
- **S3 as a mounted disk for a database.** S3 is object storage. Use EBS or a file system.
- **Snowball Edge** is legacy. The exam may still show it as the offline transfer answer, but today you would use DataSync or the Data Transfer Terminal.
- **Multi-AZ shared block storage.** There is none. EBS is one AZ. Use EFS or FSx.
- **FSx for Lustre** is Linux only. It is not a Windows file share.

## Cost angle

- S3 Standard is 0.023 per GB-month, EFS Standard 0.30, gp3 0.08. S3 is the cheapest per GB for data that fits objects. Do not pay for a file system if a bucket will do.
- Cold data: S3 Glacier Deep Archive at 0.00099 (about 1 USD per TB-month). EFS Archive is 0.008.
- Storage Gateway keeps the cloud copy in S3 or as EBS snapshots, so you pay those prices. Tape Gateway removes physical tape.
- FSx for ONTAP tiers cold data to a cheaper capacity pool automatically.
- Transfer Acceleration adds data transfer charges. Test whether it helps before you switch it on.
- AWS Backup lifecycle moves old backups to cold storage.

## Comparison

| | S3 | EBS | Instance store | EFS | FSx | Storage Gateway |
|---|---|---|---|---|---|---|
| Type | Object | Block | Block | File (NFS) | File (SMB, NFS, Lustre, iSCSI) | Hybrid bridge |
| Access | HTTPS API | One instance (AZ) | One host | Many Linux clients | Many clients | On-premises apps |
| Scale | Unlimited | 64 TiB per volume | Fixed | Petabytes, elastic | Provisioned | Cache + cloud |
| Survives stop | Yes | Yes | **No** | Yes | Yes | Yes |
| Windows | API only | Yes | Yes | **No** | **Yes** (Windows File Server) | Yes |
| Best at | Cheap durable objects | Boot, databases | Scratch, cache | Shared Linux files | Windows, HPC, NetApp, ZFS | Hybrid, tape replacement |

Now do drill 10 (which storage service), then check yourself on drills 01–04 if you skipped any.

# Week 04 — Storage: S3, EBS, instance store, EFS, FSx and Storage Gateway

## Goals

By the end of this week you can:

1. Choose an S3 storage class for an access pattern and predict what it costs.
2. Design lifecycle and versioning rules that move and delete data on a schedule.
3. Protect data with versioning, Object Lock and replication.
4. Secure a bucket: Block Public Access, bucket policies, encryption and presigned URLs.
5. Choose and size block storage: EBS volume types, instance store and snapshots.
6. Choose a file or hybrid storage service: EFS, FSx and Storage Gateway.

## Your week

About 10–12 hours. Do the steps in order.

1. Concept notes 01–05 and the two demos in `concepts/` (~3 h). Run the demos:
   `python concepts/demo_s3_in_moto.py` and `python concepts/demo_storage_costs.py`.
2. Drills: `python practice/exercises.py` (~3–4 h). Drills 01–04 are small models you build yourself: storage-class
   cost, a lifecycle-rule validator, EBS volume maths and a multipart planner. Drills 05, 06, 08 and 09 use boto3 against a
   fake AWS. Drills 07 and 10 are predictions and decisions. Do them in order.
3. Quiz: `python quiz.py --week 4 -n 30` until you score 80 % or more (~1.5 h).
4. Milestone M04: the course project's storage tier (~2–3 h). See `course_project/milestones/M04.md`.
5. Optional lab (~1 h, a few cents): `lab/LAB.md`. Version a bucket, write a lifecycle rule, sign a URL and resize an EBS volume.

## Exam tasks covered

| Task | Title |
|---|---|
| 1.3 | Determine appropriate data security controls |
| 2.2 | Design highly available and/or fault-tolerant architectures |
| 3.1 | Determine high-performing and/or scalable storage solutions |
| 4.1 | Design cost-optimized storage solutions |

Task 3.1 and 4.1 are the main targets: which storage service, which class, which volume type, and what it costs.
Task 1.3 appears as encryption, Block Public Access and data retention. Task 2.2 appears as replication, snapshots and
multi-AZ file systems.

## Service comparison

| Service | Type | Scope | Shared by | Use it when |
|---|---|---|---|---|
| S3 | Object | Region | Anything with HTTPS | Unlimited, durable, cheap objects; data lakes; backups; static content |
| EBS | Block | One AZ | One instance (io1/io2 Multi-Attach: 16) | Boot disks and databases |
| Instance store | Block | One host | One instance | Scratch, caches; lost on stop |
| EFS | File (NFS) | Region (or one AZ) | Many Linux clients | Shared Linux files that grow by themselves |
| FSx | File (SMB, Lustre, NFS, iSCSI) | AZ or Multi-AZ | Many clients | Windows shares, HPC, NetApp, ZFS |
| Storage Gateway | Hybrid | On-premises + AWS | On-premises apps | A local cache in front of S3, EBS snapshots or Glacier |

| S3 class | Storage per GB-month | Min days | Retrieval fee | Use it for |
|---|---|---|---|---|
| Standard | 0.023 | none | no | Active data |
| Intelligent-Tiering | 0.023 down | none | no | Unknown access pattern |
| Standard-IA | 0.0125 | 30 | yes | Rare reads, only copy |
| One Zone-IA | 0.01 | 30 | yes | Re-creatable data |
| Glacier Instant Retrieval | 0.004 | 90 | yes | Archive, millisecond reads |
| Glacier Flexible Retrieval | 0.0036 | 90 | yes | Archive, hours are fine |
| Glacier Deep Archive | 0.00099 | 180 | yes | Long-term compliance archive |

Prices are illustrative (us-east-1). The drills use the same numbers.

## Interview questions

Answer each out loud in under two minutes.

1. How do you choose an S3 storage class?
2. What does a lifecycle rule do, and what can go wrong with versioning turned on?
3. What happens when you delete an object in a versioned bucket, and how do you get it back?
4. Governance mode or compliance mode for Object Lock?
5. What must be true for S3 replication to work, and what does it not copy?
6. How do you make sure data in S3 is encrypted and only sent over HTTPS?
7. How do you let a customer download one private file for an hour?
8. gp3 or io2? What do you do when a volume is too slow?
9. EFS, FSx or S3 for shared files?
10. An office needs file shares backed by AWS storage. Which Storage Gateway type, and why?

Now you may read `_harness/awslib/s3cost.py`, `lifecycle.py` and `ebs.py` — compare them with your drills 01–04.

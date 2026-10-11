Exam tasks: 3.2, 1.2, 2.2

# 03 — Launching instances safely

## What it is

Launching an instance is a handful of choices that you make once and then repeat many times: **which image**
(AMI), **which type**, **which network and firewall**, **which identity**, **what runs at boot**, **how it talks to
the metadata service**, and **where it sits on the hardware**.

Do not click through these each time. Write them down once as a **launch template**. Auto Scaling (note 04) launches
instances from that template, so every instance in a fleet is the same.

Three exam tasks meet here:

- **3.2** pick the right compute features and options.
- **1.2** secure the workload: instance profile instead of keys, IMDSv2, security groups.
- **2.2** survive failure: spread instances across hardware and Availability Zones.

Drill 06 builds a launch template with IMDSv2 required. Drill 08 fixes a fleet with settings that bite.
Drill 09 asks where instances should live.

## How it works

### AMIs

An **Amazon Machine Image** holds the root volume template, launch permissions and block device mapping.
An AMI belongs to one Region and one CPU architecture (`x86_64` or `arm64`).

Do not hard-code an AMI id. AWS publishes the current Amazon Linux id as a **public SSM parameter**. Ask for it by name:

```
/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64
```

Use `x86_64` in place of `arm64` for Intel and AMD. A launch template (or a CloudFormation parameter) can take that
name and resolve it at launch, so new instances always get a patched image. User data is **not** part of an AMI.

### Launch templates

A launch template stores the AMI, instance type, key or profile, security groups, storage, user data,
metadata options and tags.

- **Versions.** A template has numbered versions. Versions are immutable: to change something you create a new version.
- **`$Latest`** is the newest version. **`$Default`** is the version you mark as default. An Auto Scaling group that points at
  `$Latest` picks up every new version. Pointing at `$Default` or a number gives you control.
- Mixed instances, Spot options and multiple instance types need a launch template.
- Old-style launch configurations are retired for new accounts. Accounts created on or after 2024-10-01 cannot create them by any method
  (changed: AWS first stopped adding new instance types to them on 2023-01-01). Teach and use launch templates.

### User data

A script (or cloud-init directives) that runs when the instance boots.

- Limit: **16 KB** raw, before base64 encoding. The CLI and boto3 can encode for you.
- Linux scripts start with `#!` (shell) or `#cloud-config`.
- Runs **as root**. Do not use `sudo`.
- By default runs **only on first boot**. Stop and start does not run it again.
- Log: `/var/log/cloud-init-output.log`. Read it first when a boot script fails.
- To change user data, stop the instance first. The new data does not run by itself.
- User data is visible to anyone who can reach the metadata service. **Never put secrets in it.**
- It is an instance attribute. It is not saved in an AMI made from that instance.

### Identity: an instance profile, not keys

An instance needs AWS credentials to call S3, SQS and so on. Do not copy access keys onto it.

1. Create an **IAM role** trusted by EC2 (week 01).
2. Wrap it in an **instance profile**. The console does this for you.
3. Attach the profile in the launch template.

The SDK on the instance finds temporary credentials in the metadata service and rotates them. If a user data
script needs to call AWS, it needs the profile. The check "no long-term keys on instances" is a task 1.2 favourite.

### The instance metadata service (IMDS)

Software on the instance reads facts about itself at the link-local address `169.254.169.254`: the instance id,
the Region, the role credentials. There is no charge, and it works only from the instance.

| | IMDSv1 | IMDSv2 |
|---|---|---|
| Method | Plain GET request | Session: `PUT` for a token, then `GET` with the token |
| Token | None | `X-aws-ec2-metadata-token`, lifetime 1 second to 6 hours |
| Stops SSRF theft of credentials | No | Yes (needs a PUT with a header; a proxy request is rejected) |

The IMDSv2 flow, as the lab script does it:

```
TOKEN=$(curl -s -X PUT http://169.254.169.254/latest/api/token -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id
```

Settings in the launch template's metadata options:

- **`HttpTokens: required`** turns IMDSv1 off. This is the setting to remember. The console shows "Metadata version: V2 only".
  The default allows both versions ("optional").
- **Hop limit.** The token reply travels with a hop limit of **1** by default. A process in a **container** is one hop
  further away, so it fails. Set the hop limit to **2** for containers.
- Disabling the endpoint turns off access to user data and the SSH key from metadata.

Where the setting comes from, highest priority first: the launch template or launch call, then the **account-level
default**, then the AMI. Per Region, an account can now set "IMDSv2 required" as the default for new instances
(changed: newer than 2022; applies to new instances only), and can even enforce it so launches without IMDSv2 fail.
The exam answer is still: **require IMDSv2 in the launch template**.

### Placement groups

A placement group controls how instances sit on hardware. It is free. Without one, EC2 tries to spread instances
across hardware itself. An instance can be in only one group, and groups cannot be merged.

| | Cluster | Spread | Partition |
|---|---|---|---|
| Idea | Pack close together | Each instance on separate hardware | Groups of instances on separate racks |
| AZs | **One AZ** | Can span AZs | Can span AZs |
| Limit | Instance types: current generation, not burstable | **7 running instances per AZ per group** | **7 partitions per AZ** |
| Network | Up to 10 Gbps single flow inside the group (5 Gbps outside) | Normal | Normal |
| Goal | Low latency, high throughput | Reduce correlated failure for a few critical instances | Isolate failure domains of large distributed stores |
| Examples | HPC, tightly coupled jobs | Primary and standby, small critical groups | Hadoop, Cassandra, Kafka, HBase |

Rules worth knowing:

- Launch a cluster group in **one request with one instance type**. Adding later raises the chance of an insufficient capacity error. The fix is to stop and start all instances in the group.
- With partitions you can see which instance is in which partition (topology-aware apps).
- Three AZs with a spread group is 21 instances in all (7 each).
- Dedicated Hosts cannot go in a placement group. Spot that stops or hibernates cannot either.
- Moving an instance into or out of a group needs it stopped.

### Instance store or EBS

| | Instance store | EBS root volume |
|---|---|---|
| Where | Disks attached to the host | Network volume |
| Survives reboot | Yes | Yes |
| Survives stop / hibernate / terminate | **No, data is erased** | Stop: yes. Terminate: root deleted by default |
| Cost | In the instance price | Per GB-month |
| Use | Cache, buffers, scratch | Anything you keep |

Only EBS-backed instances can be stopped and started.

### Stop, hibernate, terminate and the bill

| Action | What happens | What you pay |
|---|---|---|
| **Reboot** | Same host, keeps public IP and instance store data | Nothing new |
| **Stop** | Moves to a new host on start, new public IPv4 unless an Elastic IP; private IP kept | No instance charge. **EBS still bills**, Elastic IPs may |
| **Hibernate** | RAM saved to the EBS root volume; same instance id on start | Not charged once stopped; EBS (including the RAM copy) bills |
| **Terminate** | Gone for good, root volume deleted by default | Charges stop at shutting-down. A reservation still bills to the end of its term |

**Hibernation prerequisites:** enabled **at launch** (not later); root volume on **EBS and encrypted**, large enough for
RAM plus OS; Linux RAM under 150 GiB; EBS type gp2, gp3, io1 or io2; not bare metal.
Use it to resume a slow-to-start app without a cold boot.

## Numbers to know

- User data: **16 KB**, root, first boot, log `/var/log/cloud-init-output.log`.
- IMDSv2 token lifetime: 1 second to **6 hours**. Default hop limit **1**; containers need **2**.
- Spread: **7 per AZ per group**. Partition: **7 partitions per AZ**.
- Cluster: single AZ, up to 10 Gbps single flow inside the group.
- Hibernate: RAM under 150 GiB (Linux), EBS root encrypted, enabled at launch.
- Billing: per second, 1-minute minimum for each start.
- Launch configurations: retired for new accounts since 2024-10-01.

## When to choose it

| Need | Choose |
|---|---|
| Newest patched Linux image without editing the template | SSM public parameter for the AMI |
| Same instance setup across an Auto Scaling group | Launch template with versions |
| Instance calls AWS APIs | Instance profile (IAM role), never access keys |
| Stop credential theft through SSRF | `HttpTokens: required` (IMDSv2 only) |
| Containers on the instance read metadata | IMDSv2 with hop limit 2 |
| HPC job, lowest latency between nodes | Cluster placement group |
| Five critical instances must not share hardware | Spread placement group |
| Large Kafka or Cassandra cluster | Partition placement group |
| Fast boot for a big-memory app | Hibernate (EBS root, encrypted) |
| Cheap scratch space that can vanish | Instance store |

## Exam traps

- **Hard-coded AMI ids.** They are Region-specific and go stale. Use the SSM parameter.
- **Editing a launch template.** You cannot. Create a new version. Group points at `$Latest`, `$Default` or a number.
- **User data runs every boot.** It does not (Linux). Only the first boot cycle.
- **Secrets in user data.** Readable from the metadata service. Use Secrets Manager or Parameter Store plus an instance profile.
- **"Access keys on the instance."** Wrong. Use an instance profile.
- **IMDSv2 optional.** Optional still allows IMDSv1. The answer is `required`.
- **Containers and IMDSv2.** Hop limit 1 breaks them. Raise it to 2.
- **Cluster placement group across AZs.** A cluster is one AZ. Spread and partition can span.
- **Spread group with eight instances in one AZ.** Seven is the limit.
- **Instance store after stop.** Data is gone. Only a reboot keeps it.
- **Hibernate on an existing instance.** Must be enabled at launch.
- **"Stopped instances are free."** The EBS volumes still bill.

## Cost angle

- Placement groups cost nothing.
- Stopped instances do not pay for compute, but their EBS volumes and any idle Elastic IPv4 addresses do.
- Hibernated instances keep a RAM copy on EBS: you pay for that storage.
- Instance store is included in the price. Use it for scratch instead of paying for EBS.
- Metadata and user data requests are free.
- A public IPv4 address bills 0.005 USD/hour per address, in use or idle. Private subnets and a load balancer avoid per-instance public IPs.
- Launch templates and AMIs are free. The snapshots behind an AMI are not.

## Comparison

| Strategy | Placement | Max per AZ | AZs | Best for | Fails when |
|---|---|---|---|---|---|
| None (default) | EC2 spreads across hardware | none stated | Any | General workloads | You need guaranteed isolation or latency |
| Cluster | Close together | Limited by capacity | One | Low latency HPC | One rack or AZ failure takes it all |
| Spread | Separate hardware per instance | 7 | Many | Few critical instances | You need more than 7 per AZ |
| Partition | Separate racks per partition | 7 partitions | Many | Large distributed stores | You need single-instance isolation |

Now do drill 06 (a fleet that heals itself), drill 08 (settings that bite) and drill 09 (where should these instances live?).

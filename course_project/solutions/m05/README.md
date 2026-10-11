# shortly-infra

The infrastructure-as-code for Shortly, the URL shortener you build up across the course. Each milestone adds one layer of CloudFormation templates, with parameter files for the lab and prod environments.

## Layers

| Layer | What it holds | Milestone |
|-------|---------------|-----------|
| `iam` | Roles for the app, the click consumer, the deployer and the auditor | M01 |
| `network` | VPC, three subnet tiers in two AZs, NAT, security groups, S3/DynamoDB endpoints, flow logs | M02 |
| `compute` | Application Load Balancer, launch template (IMDSv2), Auto Scaling group, listener rules | M03 |
| `storage` | Assets bucket (versioned, KMS-encrypted) and logs bucket (tiered, expiring), with their bucket policies | M04 |

## Network plan

VPC `10.20.0.0/16` in two Availability Zones (A = first AZ of the Region, B = second). Biggest subnets first, so every block stays aligned.

| Subnet | Tier | AZ | CIDR | Usable IPs |
|---|---|---|---|---|
| AppSubnetA | app (private, via NAT) | A | 10.20.0.0/22 | 1,019 |
| AppSubnetB | app (private, via NAT) | B | 10.20.4.0/22 | 1,019 |
| PublicSubnetA | public (ALB, NAT) | A | 10.20.8.0/24 | 251 |
| PublicSubnetB | public (ALB, NAT) | B | 10.20.9.0/24 | 251 |
| DataSubnetA | data (no internet) | A | 10.20.10.0/24 | 251 |
| DataSubnetB | data (no internet) | B | 10.20.11.0/24 | 251 |

`10.20.12.0` – `10.20.255.255` stays free for later tiers.

NAT: prod runs one NAT gateway per AZ (an AZ failure cannot cut off the other AZ); lab runs one, shared by both app subnets, to halve the hourly cost.

## Compute

The `compute` stack imports the IAM and network exports and creates an internet-facing Application Load Balancer in the public subnets, a target group that health-checks `/healthz` on port 8000, and an Auto Scaling group in the app subnets. Instances come from one launch template: Graviton, Amazon Linux 2023 (AMI id read from the public SSM parameter), IMDSv2 required, no SSH key (use Session Manager), and the Shortly app from `app/app.py` written to disk by user data and run by systemd. prod keeps 2 to 6 instances, lab 1 to 2; a target-tracking policy holds average CPU near 50 %.

The listener is HTTP only for now (M07 adds HTTPS). `/healthz` is answered with a 404 at the load balancer, because the health checks go straight to the instances and never through listener rules.

## Storage

The `storage` stack creates two buckets, both private (all four Block Public Access flags on) and with ACLs switched off (`BucketOwnerEnforced`).

- `shortly-assets-<account>` holds user uploads. Versioning is on, objects are encrypted with the AWS managed KMS key `aws/s3` through a Bucket Key (a customer managed key comes in M08), and the bucket has `DeletionPolicy` and `UpdateReplacePolicy` `Retain`, so deleting the stack never deletes uploads. Rule `noncurrent-versions` deletes a replaced version after 30 days but always keeps the 3 newest, and aborts unfinished multipart uploads after 7 days. The bucket policy denies every request that is not sent over TLS and lets only the app role read and write `uploads/*`.
- `shortly-logs-<account>` receives the load balancer's access logs. It uses SSE-S3 (`AES256`), because access-log delivery does not support KMS keys. Rule `alb-logs` moves objects under `alb/` to Standard-IA at 30 days, Glacier Instant Retrieval at 90 and Deep Archive at 180, and deletes them at 730 days in prod and 365 in lab (an expiry must come later than the last transition, and Deep Archive bills a 180-day minimum). The bucket policy denies non-TLS requests and lets only the log delivery service `logdelivery.elasticloadbalancing.amazonaws.com` write `alb/AWSLogs/<account>/*`.

Pointing the load balancer's access logs at the bucket is a later change to the `compute` stack.

## Data tier

The `data` stack gives Shortly three stores, because the three jobs are different:

- **PostgreSQL on RDS** holds links and users. That data is relational and needs transactions (a link belongs to a user; creating one must not half-succeed). The instance is encrypted, private (`PubliclyAccessible: false`, reachable only from the app security group), and RDS creates and rotates the master password in Secrets Manager (`ManageMasterUserPassword`). Prod is Multi-AZ with 7 days of backups and deletion protection; lab is Single-AZ with 1 day. Deleting the stack takes a final snapshot (`DeletionPolicy: Snapshot`). The app role gets `secretsmanager:GetSecretValue` on that one secret only.
- **Valkey (an ElastiCache replication group)** serves hot redirects. A redirect is a read of one small value, so a cache-aside lookup answers in well under a millisecond and keeps most traffic off PostgreSQL. Prod has a replica and automatic failover across two zones; both environments encrypt in transit and at rest.
- **DynamoDB** holds the daily click counts (`shortly-clicks-daily`, key `code` + `day`). It is a key-value, write-heavy workload with no joins, so on-demand capacity with PITR and a TTL on `expires_at` fits; the table is retained if the stack is deleted.

Click-table cost, on-demand: 30 million standard writes of 0.5 KB and 60 million eventually consistent reads of 1 KB per month cost about **22.50** USD per month (each 0.5 KB write is 1 write unit at 0.625 USD per million = 18.75; each 1 KB eventually consistent read is 0.5 read unit at 0.125 USD per million = 3.75). Storage and backups are extra.

## Check it

Run the milestone tests with the course venv:

```
python run_milestone.py 5
```

## Deploy (optional)

Deploying to a real account is optional; see the course's `DEPLOY.md`. The network stack costs money while it runs (NAT gateways and their public IPv4 addresses are billed by the hour).

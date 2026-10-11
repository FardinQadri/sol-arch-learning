# Deploying shortly-infra (optional)

You do not have to deploy anything to finish the course. The tests are the real check. Deploy only if you want to see your templates run in AWS.

## Before you start

- Finish the week 00 lab first. You need the budgets and the billing alarm in place before you create anything.
- Use your lab profile (`saa-lab` below) and never your root user.
- Run the commands from the root of your shortly-infra repo.

## M01 — the IAM stack

The IAM stack costs nothing.

Deploy:

```bash
aws cloudformation deploy --template-file infra/iam.yaml --stack-name shortly-iam --parameter-overrides Prefix=shortly Env=lab --capabilities CAPABILITY_NAMED_IAM --profile saa-lab
```

`CAPABILITY_NAMED_IAM` is required because the template creates IAM roles with fixed names. CloudFormation makes you confirm that on purpose.

Tear down:

```bash
aws cloudformation delete-stack --stack-name shortly-iam --profile saa-lab
```

## M02 — the network stack

The VPC, subnets, route tables, security groups and gateway endpoints are free. The flow log pays CloudWatch Logs ingestion for what it writes (small for a short test; the log group keeps 1–90 days). The NAT gateways and their public IPv4 addresses bill by the hour, even with no traffic. With `Env=lab` the stack creates one NAT gateway; `Env=prod` creates two. Deploy it for a short test and delete it the same day.

Deploy:

```bash
aws cloudformation deploy --template-file infra/network.yaml --stack-name shortly-network --parameter-overrides Prefix=shortly Env=lab --capabilities CAPABILITY_NAMED_IAM --profile saa-lab
```

The stack creates a role (`FlowLogsRole`), so it needs the capability flag.

Tear down. Delete `shortly-network` before `shortly-iam`, and delete any later stack that imports from it first:

```bash
aws cloudformation delete-stack --stack-name shortly-network --profile saa-lab
```

## M03 — the compute stack

This stack costs money while it exists. The Application Load Balancer bills by the hour plus load capacity units (LCUs), each instance bills by the hour, and the public IPv4 addresses of the ALB bill by the hour. `Env=lab` runs one instance (up to two when CPU is high); `Env=prod` runs at least two. Deploy it for a short test and delete it the same day.

Deploy it after the network stack, because it imports values from `shortly-iam` and `shortly-network`:

```bash
aws cloudformation deploy --template-file infra/compute.yaml --stack-name shortly-compute --parameter-overrides Prefix=shortly Env=lab --profile saa-lab
```

No IAM capability flag is needed, because the stack creates no roles (it only uses the instance profile from M01). If you add a role to the template, add `--capabilities CAPABILITY_NAMED_IAM`.

When it is done, the ALB's DNS name is in the stack output `AlbDnsName`. Wait a couple of minutes (new instances need time to boot and pass health checks), then try `curl -X POST http://<dns-name>/api/links -d '{"url": "https://example.com"}'`. Note that each instance keeps its links in memory, so with two instances a short link may only work on the one that created it. M05 moves them into a database.

Tear down. Delete `shortly-compute` first:

```bash
aws cloudformation delete-stack --stack-name shortly-compute --profile saa-lab
```

## M04 — the storage stack

Two S3 buckets cost money only for what is stored and for requests: S3 Standard is about 0.023 USD per GB-month for the first 50 TB (illustrative, see docs/facts.md), so a test with a few small files costs a fraction of a cent.

Deploy it after the IAM stack, because it imports the app role ARN from `shortly-iam`:

```bash
aws cloudformation deploy --template-file infra/storage.yaml --stack-name shortly-storage --parameter-overrides Prefix=shortly Env=lab --profile saa-lab
```

No IAM capability flag is needed, because the stack creates no roles.

Tear down. Delete `shortly-storage` before `shortly-iam`. The assets bucket has `DeletionPolicy: Retain`, so CloudFormation leaves it behind: empty it (all versions and delete markers) and delete it by hand, or it stays in your account:

```bash
aws cloudformation delete-stack --stack-name shortly-storage --profile saa-lab
```

## M05 — the data stack

This is the most expensive stack so far. The database and the cache nodes bill by the hour, even with no traffic. With `Env=lab` the stack creates one `db.t4g.micro` Single-AZ database (about 0.016 USD/hour) and a one-node cache (`cache.t4g.micro`, Valkey about 0.0128 USD/hour). With `Env=prod` it creates a `db.m7g.large` Multi-AZ database (about 0.337 USD/hour) and a two-node `cache.m7g.large` group (Valkey about 0.1264 USD/hour per node). The clicks table is on-demand and costs only for requests and storage (all illustrative, see docs/facts.md). Deploy `Env=lab` for a short test and delete it the same day.

Deploy it after the IAM and network stacks, because it imports the data subnets and the database and cache security groups from `shortly-network`, and it adds a policy to the app role from `shortly-iam`:

```bash
aws cloudformation deploy --template-file infra/data.yaml --stack-name shortly-data --parameter-overrides Prefix=shortly Env=lab --capabilities CAPABILITY_IAM --profile saa-lab
```

`CAPABILITY_IAM` is required because the stack creates an IAM policy (`AppDbSecretPolicy`). The stack creates no named role, so `CAPABILITY_NAMED_IAM` is not needed. Creating the database and the cache takes several minutes.

Tear down. Delete `shortly-data` before `shortly-network`. Two resources are left behind on purpose:

- The database has `DeletionPolicy: Snapshot`, so CloudFormation takes a final snapshot. It is stored and billed until you delete it by hand when you no longer need it. In prod the database also has deletion protection: switch it off first, or the stack delete fails.
- The clicks table has `DeletionPolicy: Retain`, so it stays in your account. Delete it by hand. In prod, switch off its deletion protection first.

```bash
aws cloudformation delete-stack --stack-name shortly-data --profile saa-lab
```

## What costs money even when idle

Later milestones fill in this table. Check it before you deploy a new layer.

| Milestone | Resource | Cost while idle |
|---|---|---|
| M01 | IAM roles and policies | Free |
| M02 | NAT gateway: 1 in lab, 2 in prod | About 0.045 USD/hour each plus 0.045 USD/GB processed, plus 0.005 USD/hour per public IPv4 address (illustrative, see docs/facts.md) |
| M03 | Application Load Balancer and instances | ALB about 0.0225 USD/hour + LCUs; t4g.small about 0.0168 USD/hour each — 1 in lab, 2+ in prod; plus 0.005 USD/hour per public IPv4 address of the ALB (illustrative, see docs/facts.md) |
| M04 | S3 buckets (assets, logs) | S3 Standard about 0.023 USD per GB-month for the first 50 TB, plus requests; old versions and logs add up until the lifecycle rules remove them (illustrative, see docs/facts.md). Tiny for a test |
| M05 | RDS database, cache nodes, DynamoDB table | RDS PostgreSQL db.t4g.micro about 0.016 USD/hour Single-AZ (lab), db.m7g.large about 0.337 USD/hour Multi-AZ (prod); Multi-AZ doubles the database price; gp3 storage about 0.115 USD per GB-month Single-AZ; Valkey cache.t4g.micro about 0.0128 USD/hour (1 node in lab), cache.m7g.large about 0.1264 USD/hour per node (2 in prod); DynamoDB on-demand: requests and storage only. The final snapshot and the retained table stay after teardown (illustrative, see docs/facts.md) |

## Teardown order

Always delete stacks in reverse order of creation. A stack that exports a value cannot be deleted while another stack still imports it, so delete the newest stack first and the oldest (IAM) last. For the layers so far: `shortly-data`, then `shortly-storage`, then `shortly-compute`, then `shortly-network`, then `shortly-iam`.

After you finish, run the week's `lab/cleanup.py` as a dry run to check that nothing is left behind.

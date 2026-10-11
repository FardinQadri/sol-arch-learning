# Week 05 lab — a DynamoDB table and a small RDS PostgreSQL database

About 60–90 minutes. Cost: cents. An on-demand DynamoDB table with a few items costs almost nothing (storage is free
for the first 25 GB). A `db.t4g.micro` PostgreSQL instance bills about 0.016 USD per hour Single-AZ, plus gp3 storage at
0.115 USD per GB-month (all illustrative). A free plan or the Free Tier may cover the instance. **Never choose Multi-AZ in this lab**: it doubles the
instance price. This lab is optional. Everything the course grades runs offline.

## 1. Before you start

- The week 00 guard rails are done (budget alert, MFA, no root keys) and you have the `saa-lab` profile.
- Use one Region for the whole lab and stay in it. In the examples `us-east-1` is used; replace it with yours.
- Tag **every** resource `saa-course=lab`: the table, the RDS instance, the snapshot and the DB subnet group. The cleanup script only finds tagged ones.
- Set the profile for the session: `export AWS_PROFILE=saa-lab` (PowerShell: `$env:AWS_PROFILE = "saa-lab"`).
- Keep a clock handy. Aim to be finished and cleaned up within 90 minutes.

## 2. DynamoDB

Create an on-demand table with a partition key and a sort key, tagged:

```bash
aws dynamodb create-table --table-name saa-lab-orders --billing-mode PAY_PER_REQUEST \
  --attribute-definitions AttributeName=pk,AttributeType=S AttributeName=sk,AttributeType=S \
  --key-schema AttributeName=pk,KeyType=HASH AttributeName=sk,KeyType=RANGE \
  --tags Key=saa-course,Value=lab --region us-east-1
aws dynamodb wait table-exists --table-name saa-lab-orders --region us-east-1
```

Put three items:

```bash
aws dynamodb put-item --table-name saa-lab-orders --region us-east-1 --item '{"pk":{"S":"CUSTOMER#1"},"sk":{"S":"ORDER#2026-01-05"},"total":{"N":"40"}}'
aws dynamodb put-item --table-name saa-lab-orders --region us-east-1 --item '{"pk":{"S":"CUSTOMER#1"},"sk":{"S":"ORDER#2026-02-09"},"total":{"N":"15"}}'
aws dynamodb put-item --table-name saa-lab-orders --region us-east-1 --item '{"pk":{"S":"CUSTOMER#2"},"sk":{"S":"ORDER#2026-02-11"},"total":{"N":"99"}}'
```

A conditional put that must fail, because the key already exists:

```bash
aws dynamodb put-item --table-name saa-lab-orders --region us-east-1 \
  --item '{"pk":{"S":"CUSTOMER#1"},"sk":{"S":"ORDER#2026-01-05"},"total":{"N":"1"}}' \
  --condition-expression "attribute_not_exists(pk)"
```

Expect `ConditionalCheckFailedException`. Run a Query for one customer (the cheap read), then compare with a Scan:

```bash
aws dynamodb query --table-name saa-lab-orders --region us-east-1 \
  --key-condition-expression "pk = :c AND begins_with(sk, :p)" \
  --expression-attribute-values '{":c":{"S":"CUSTOMER#1"},":p":{"S":"ORDER#2026"}}' --return-consumed-capacity TOTAL
aws dynamodb scan --table-name saa-lab-orders --region us-east-1 --return-consumed-capacity TOTAL
```

Compare `Count` and `ScannedCount` and the consumed capacity of the two calls. Then turn on point-in-time recovery and take an on-demand backup:

```bash
aws dynamodb update-continuous-backups --table-name saa-lab-orders --region us-east-1 \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
aws dynamodb create-backup --table-name saa-lab-orders --backup-name saa-lab-orders-backup --region us-east-1
aws dynamodb describe-continuous-backups --table-name saa-lab-orders --region us-east-1
```

Backups are not tagged by the table tag. The cleanup script finds them through the tagged table's name. Note the earliest and latest restorable times.

## 3. RDS PostgreSQL

Console: RDS → Create database → **Standard create**.

1. Engine **PostgreSQL**. Template **Free tier** or **Dev/Test**. Choose **Single-AZ** (a "Single DB instance"). **Do not pick Multi-AZ.**
2. DB instance identifier `saa-lab-pg`. Credentials: tick **Manage master credentials in AWS Secrets Manager**. Leave the default KMS key.
3. Instance class **db.t4g.micro**. Storage **gp3**, 20 GiB. Leave storage autoscaling off.
4. Connectivity: the default VPC, **Public access: No**. Choose or create a security group that allows nothing inbound (you will not connect).
5. Additional configuration: backup retention **7 days** (the console default), encryption on (the default), **deletion protection OFF** for this lab.
6. Tags: `saa-course=lab`. It also creates a DB subnet group in the default VPC. Tag it `saa-course=lab` too if the console lets you; otherwise note its name.
   If the console-created subnet group could not be tagged, the script leaves it. It costs nothing; delete it by hand if you want.

It takes about 5–10 minutes to become Available. While it is creating, read the setup summary. Then open the instance and write down:

- the **endpoint** and port. Is it the same name after a failover? (Yes, for Multi-AZ; you did not enable it.)
- the **backup retention** and the latest restorable time (Maintenance & backups tab).
- the **Multi-AZ setting you did not choose**. At 0.016 USD per hour Single-AZ, the same class Multi-AZ would be 0.032 USD per hour: double.
- the **maintenance window** and the **backup window**. Do they overlap?
- the **Secrets Manager secret** name (Configuration tab). You can read its rotation schedule: the default is every 7 days.

Take a manual snapshot: Actions → Take snapshot, name `saa-lab-pg-snap`, tag `saa-course=lab`. Compare the automated backups list with the manual snapshot.

Optional, still free: read the instance's CLI view.

```bash
aws rds describe-db-instances --db-instance-identifier saa-lab-pg --region us-east-1 \
  --query "DBInstances[0].[Endpoint.Address,MultiAZ,StorageEncrypted,BackupRetentionPeriod,DeletionProtection,MasterUserSecret.SecretArn]"
```

## 4. Clean up

Turn off deletion protection if you left it on, then:

```bash
python lab/cleanup.py --profile saa-lab          # dry run: read the list
python lab/cleanup.py --profile saa-lab --yes    # deletes tagged resources
```

The script deletes, in this order: the DynamoDB backups (found through their tagged table, so they go first), the DynamoDB tables,
the RDS instances (read replicas before their source; deletion protection is turned off only on tagged instances), the manual snapshots
and the DB subnet groups, all tagged `saa-course=lab`. It does not touch anything without the tag. It reports a failed deletion and carries on;
wait a minute and run it again.

Then check yourself:

- RDS → **Automated backups**: the instance's automated backups are gone (they are deleted with the instance unless you ask to retain them).
- RDS → **Snapshots**: the manual snapshot is gone.
- **Secrets Manager**: the secret RDS created for the master password is gone or scheduled for deletion. If it still shows, delete it.
- DynamoDB → **Tables** and **Backups**: both empty.
- Billing the next day: no RDS instance hours or DynamoDB charges remain.

## 5. What to write down

- The error the conditional put returned, and why it happened.
- `Count` against `ScannedCount` for the Query and the Scan, and what they cost in consumed capacity.
- The PITR earliest and latest restorable times, and what a restore would create (a new table).
- The RDS endpoint, the backup retention, and the latest restorable time.
- The Multi-AZ price you did not pay, and what Multi-AZ would have changed (a standby you cannot read, an automatic failover).
- Where the master password lives, who can read it, and its rotation period.
- How long the lab ran and the cost for that time.

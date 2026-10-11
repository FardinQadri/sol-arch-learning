# The capstone: shortly-infra

shortly is the URL shortener you built in the Flask course. In this capstone you put it on AWS, and you describe all of it as CloudFormation. You build one layer each week. There are 11 milestones.

| Milestone | What you build | Built in week | Spec |
|---|---|---|---|
| M01 | IAM: app, consumer, deployer and auditor roles, permissions boundary | 01 | built |
| M02 | Network: VPC, 3 tiers across 2 AZs, NAT, security groups, endpoints, flow logs | 02 | built |
| M03 | Compute: ALB, launch template, Auto Scaling group, listener rules | 03 | built |
| M04 | Storage: assets and logs buckets, lifecycle, bucket policies | 04 | built |
| M05 | Data: RDS PostgreSQL Multi-AZ, ElastiCache Valkey, DynamoDB | 05 | built |
| M06 | Async: SQS and DLQ, Lambda consumer, SNS, EventBridge schedule | 06 | planned |
| M07 | Edge: CloudFront, cache policies, HTTPS, Route 53, ALB locked to CloudFront | 07 | planned |
| M08 | Security: KMS key, WAF, secret rotation, GuardDuty | 08 | planned |
| M09 | Monitoring: alarms, dashboard, AWS Backup, CloudTrail, DR notes | 09 | planned |
| M10 | Analytics: Firehose, S3 data lake, Glue, Athena | 10 | planned |
| M11 | Cost and docs: tagging, budget, Spot mix, COST.md, ARCHITECTURE.md | 11 | planned |

## Two places

- **Your repo**, `~/code/shortly-infra`. You create it in M01. Your templates live in `infra/` and your parameter files in `params/`. You commit after every milestone and push to GitHub yourself.
- **This folder**, `course_project/`. It holds the milestone instructions (`milestones/`), the tests (`tests/`) and the tools (`tools/`). You do not edit it.

## The loop

1. `start_milestone.py N --repo PATH` copies milestone N's tests into your repo.
2. Read `milestones/MNN.md` and build the layer.
3. `run_milestone.py N` (run inside your repo) tells you which steps are green.
4. When all steps are green, commit.

All tools run with the course venv's Python, for example `<course>/.venv/Scripts/python.exe run_milestone.py 1`. Do not use another Python.

`run_milestone.py N` is cumulative: it runs the tests for M01 up to MN. A later milestone must not break an earlier one.

## How the checks work

Each milestone is checked in four ways:

1. **cfn-lint** reads your templates and reports mistakes.
2. **Structural tests** read the template and check the details: names, subnets, encryption flags, and so on. This is the main check.
3. **The policy evaluator** (the course's own, in `_harness/awslib`) decides whether a given IAM request would be allowed or denied by your policies.
4. **A moto deploy** creates your stack in a fake AWS on your computer.

Moto skips some resource types and properties without telling you. So a green moto deploy is not proof that the stack works in real AWS. The structural tests cover the parts moto skips.

The tests always use fake credentials. They can never reach your real AWS account.

## Deploying is optional

Claude never deploys anything, and the tests never need a real account. If you want to try a real deployment, it is your choice. See `DEPLOY.md` for the commands, the costs and the teardown steps.

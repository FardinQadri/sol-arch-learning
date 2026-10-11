# AWS Solutions Architect – Associate (SAA-C03)

This course has two goals. You pass the SAA-C03 exam. You also come out able to design and explain AWS architectures. You learn by doing: every week has notes, small demos, coding drills with automatic checks, a quiz, and a step in a running project (a multi-AZ URL shortener called `shortly`, written as CloudFormation).

## Status

Weeks 00–05 and milestones M01–M05 are built. Weeks 06–12 and the mock exams follow, one week at a time.

## Set up once

```
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python _dev/smoke_stack.py
```

If `.venv\Scripts\python.exe` disappears, run `python -m venv --upgrade .venv`.

## Safe by design

Every drill, demo and test runs offline against moto with fake credentials. Your real AWS account is used only in optional labs, and only by you. Labs are written down, never run for you.

## Your week

1. **Concepts** (2–3 h): read the notes, run the demos.
2. **Drills** (2–3 h): run `exercises.py` until it shows N/N. Stuck? Read the hint, then `solutions.py`.
3. **Quiz** (1 h): run `python quiz.py --week N` until you score 80 % or more. Read every explanation, even for answers you got right.
4. **Milestone** (2–3 h): start it, build it in your own repo, run `run_milestone.py N` until it is green, then commit and push.
5. **Lab** (optional, about 1 h): follow `lab/LAB.md` in a real account, then run `python lab/cleanup.py --yes`.
6. **Review** (15 min, from week 02): `python quiz.py --review`.

See `COURSE_FLOW.md` for the exact commands, week by week.

## Weeks

| Week | Topic | Tasks | Milestone |
|---|---|---|---|
| [00](week_00_foundations_and_exam_technique/README.md) | Foundations and exam technique: global infrastructure, shared responsibility, Well-Architected, availability maths, boto3/moto basics, account safety | 2.2, technique | none |
| [01](week_01_iam_and_governance/README.md) | IAM and multi-account governance: users, roles, policy evaluation, STS, federation, Identity Center, Organizations, SCPs/RCPs, Control Tower | 1.1 | M01 IAM baseline |
| [02](week_02_vpc_networking/README.md) | VPC networking: CIDR, routing, NAT, security groups vs NACLs, endpoints, peering, Transit Gateway | 1.2, 2.2, 3.4, 4.4 | M02 network |
| [03](week_03_compute_and_scaling/README.md) | Compute and scaling: EC2 instance types, purchasing options, launching instances (IMDSv2, placement groups), Auto Scaling, Elastic Load Balancing | 2.1, 2.2, 3.2, 4.2 | M03 web tier |
| [04](week_04_storage/README.md) | Storage: S3 classes, lifecycle, versioning, replication and security; EBS, instance store, EFS, FSx, Storage Gateway | 1.3, 2.2, 3.1, 4.1 | M04 buckets |
| [05](week_05_databases_and_caching/README.md) | Databases and caching: RDS, Aurora, DynamoDB, ElastiCache, DAX, purpose-built databases | 2.2, 3.3, 4.3 | M05 data tier |
| 06 | Decoupling, serverless and containers: SQS, SNS, EventBridge, Step Functions, Lambda, ECS | 2.1, 3.2 | M06 async pipeline (not built yet) |
| 07 | Edge, DNS and hybrid: Route 53, CloudFront, Global Accelerator, VPN, Direct Connect | 2.2, 3.4, 4.4 | M07 CDN + DNS (not built yet) |
| 08 | Security services and encryption: KMS, Secrets Manager, WAF, Shield, GuardDuty | 1.2, 1.3 | M08 hardening (not built yet) |
| 09 | Resilience, DR and observability: RTO/RPO, AWS Backup, CloudWatch, CloudTrail, Config | 2.1, 2.2 | M09 monitoring + DR (not built yet) |
| 10 | Data, analytics and migration: Kinesis, Glue, Athena, Redshift, DMS, DataSync, the 7 Rs | 3.5, 4.1 | M10 analytics (not built yet) |
| 11 | Cost optimisation review: Savings Plans, Spot, rightsizing, data-transfer costs, tagging | 4.1–4.4 | M11 cost + final docs (not built yet) |
| 12 | Exam prep: 4 mock exams, weak-area review, final checklist | all | none (not built yet) |

Weeks marked "not built yet" follow one at a time.

## Tools

- Drills: `python week_NN_*/practice/exercises.py` (for example `python week_00_foundations_and_exam_technique/practice/exercises.py`). Add `--solutions` to see the reference answers pass.
- Quiz: `python quiz.py --week N` (add `-n 15` to set the question count), `python quiz.py --review`, `python quiz.py --stats`. Your history lives in `_progress/progress.json`.
- Mock exam: `python exam_prep/mock_exam.py N` (from week 12; the mock banks are not built yet).
- Milestone: `python course_project/tools/start_milestone.py 1 --repo ~/code/shortly-infra`, then in that repo `<course>/.venv/Scripts/python.exe run_milestone.py 1`.
- Lab cleanup: `python lab/cleanup.py` inside a week folder. It is a dry run until you add `--yes`, and it touches only resources tagged `saa-course=lab`.

## Exam facts

From `docs/facts.md`, checked 2026-10-08:

- 65 questions: 50 scored and 15 unscored (not identified).
- Multiple choice (one of four) and multiple response (two or more of five or more).
- 130 minutes. Cost 150 USD.
- Scaled score 100–1,000. Pass mark 720. No penalty for guessing.
- Domains: 1 Secure 30 %, 2 Resilient 26 %, 3 High-performing 24 %, 4 Cost-optimised 20 %.

Check the certification page before booking. AWS can change an associate exam with only a few weeks' notice.

## Exam guide vs 2026 AWS

The official exam guide is older than today's AWS. Services AWS has since retired are mentioned at most in a one-line "retired" note and are never a correct quiz answer. Services closed to new customers but still in the guide (for example Snowball Edge) are taught for the exam, always with their 2026 status. Numbers that changed (S3 object size, SQS message size, gp3 limits) are taught at today's value, with the old value named once. No quiz question depends on a number that changed after 2022.

## For maintainers

`python verify_course.py` checks everything built so far (add `--self-test`, `--coverage` or `--banks` for one part). Details are in `docs/specs/2026-10-08-aws-saa-course-design.md`.

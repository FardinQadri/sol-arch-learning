# AWS Solutions Architect – Associate (SAA-C03) Course — Design Spec

- **Date:** 2026-10-08
- **Status:** Approach A approved in conversation ("looks good, build it"); this written spec awaits review
- **Scope:** new course at `courses/AWS_SAA_Course_claude/`. No other course is touched.

---

## 1. Purpose and success criteria

**Goal.** A full-length course that gets the learner through the **AWS Certified Solutions Architect – Associate (SAA-C03)** exam **and** leaves them able to design, build and explain AWS architectures in backend / data-engineering interviews. It keeps the Python course's week-by-week shape (`README` + `concepts/` + `practice/`) and fixes what the review found wrong with it: every exercise has a spec, examples, a stub and automatic checks; solutions live in a separate file; there are no read-only projects; `verify_course.py` proves all of it.

**What the learner said**
- Goal: pass the exam **and** gain real AWS skills; no fixed exam date; full-length course.
- Hands-on: auto-checked drills that run **offline and free** form the core; each week also has an **optional real-AWS lab** with a cleanup script and a billing alarm.
- Capstone: **one architecture grown week by week as CloudFormation**, tested offline; the product is the **URL shortener** from the Flask course.
- Level: "a little AWS" — has used S3/EC2/Lambda a bit, never designed a VPC or IAM setup.
- Quizzes: weekly scenario quizzes and full mock exams stay in (confirmed after a sample question).
- "Use as many subagents as you want."

**Assumptions (not stated by the learner — correct any in review)**
- Same format and machinery as the Flask course: shared drill harness, `solutions.py`, mutants, `verify_course.py`, milestone tools.
- ≈ 8–12 h/week; **12 content weeks (00–11) + 1 exam-prep week** ≈ 13 weeks. Week 00 is lighter.
- All quiz and mock-exam questions are **original**, written against the official exam guide. No exam dumps.
- Windows-first; Python packages only in `AWS_SAA_Course_claude/.venv`; no Docker, WSL or Node.
- No commits until the learner says so.

**Success criteria**
1. Every week has drills that report pass/fail per exercise in one command, using real boto3 code against moto (mocked AWS) or pure-Python models of AWS mechanisms.
2. No drill test passes on an empty stub; every drill test passes with the reference solution; every drill rejects at least one plausible wrong implementation.
3. Every week has ≥ 3 ★ build-the-mechanism drills.
4. Every week (01–11) has a 30-question auto-graded quiz (week 00: 15) that explains every option; 4 full mock exams (65 questions, 130 minutes, exam domain weights) exist.
5. Every exam task statement (§4.0) is covered by concept notes, ≥ 1 drill and ≥ 12 questions across quizzes and mocks; `COVERAGE.md` proves it.
6. The capstone ends as the learner's own repo `shortly-infra`: CloudFormation stacks for a multi-AZ URL shortener (network, IAM, compute, storage, database, cache, async pipeline, CDN/DNS, WAF/KMS, monitoring, backup/DR, analytics, cost controls), lint-clean and test-green, with `ARCHITECTURE.md`, `DR.md` and `COST.md`.
7. Every optional lab has a cleanup script that is dry-run by default and deletes only resources tagged for the course — proven by tests against moto.
8. No content teaches a retired AWS service or a removed default as current (list in §7).
9. **Claude never calls real AWS.** All automated checks run offline with fake credentials.

## 2. Context

- `courses/` holds 14 other courses, most sharing a `week_XX/{README.md, concepts/, practice/, projects/}` shape.
- **Hands-on lesson** (memory + audit of the Python course): the learner fills spec + example + stub exercises and skips read-only projects; without self-checks their solutions silently failed spec examples (e.g. week 2 `make_counter`, `uppercase_result`, `timed`). → Every exercise here has automated checks; no `projects/` folder of read-only code.
- **Flask course** (`Flask_Course_claude/`, pilot built 2026-09-26) supplies the machinery this course copies: `_harness/fldrill.py` (Drill base class, `run()` with `--solutions` / `--mutant` / `--json`), `verify_course.py`, `course_project/` with `start_milestone.py` / `run_milestone.py`. Its product is the URL shortener `shortly`, which this course deploys on paper and in CloudFormation.
- Existing AWS material elsewhere (BCG week 04, DE course week 08, HLD course) is interview-level only; nothing is exam-aligned.
- **Exam status (official AWS sources, fetched 2026-10-08; full notes in `docs/research/2026-10-08-saa-c03-research.md`):** SAA-C03 is current; exam guide **Version 1.1**. 65 questions = 50 scored + 15 unscored (not identified); multiple choice (1 correct of 4) and multiple response (2+ correct of 5+); 130 minutes; 150 USD; scaled score 100–1,000, pass 720, compensatory (no per-domain pass); no penalty for guessing. 4 domains, **14 task statements**. AWS's "coming soon" page announces no successor; third-party "SAA-C04" claims cite no AWS source and are ignored. AWS has updated other associate exams with only 3–4 weeks' notice, so exam-version-specific content stays in `docs/exam_guide.md` and the README tells the learner to re-check the certification page before booking.
- **The exam guide is older than today's AWS.** Its in-scope list still names services AWS has since retired or closed to new customers (Snow Family, QLDB, Data Pipeline, Elastic Transcoder, Proton, Pinpoint, Application Discovery Service, Migration Hub), and older study material uses superseded numbers (S3 objects up to 5 TB — now 50 TB since 2025-12-02; SQS messages up to 256 KiB — now 1 MiB since 2025-08-04; gp3 up to 16,000 IOPS — now 80,000). §7 defines how the course handles both.
- **Machine:** Windows 11, Python 3.14.2. Globally installed: boto3 1.42.38, cryptography 43.0.3, pytest 9.0.2 (the course uses its own venv).
- **Feasibility spike (2026-10-08, throwaway venv; report in `docs/research/2026-10-08-moto-cfnlint-spike.md`):**
  - `pip install "moto[all]" cfn-lint boto3 pytest` works with the latest versions and **no WDAC blocks**: moto 5.2.3, boto3/botocore 1.43.109, cfn-lint 1.57.2, pydantic 2.13.5, cryptography 50.0.2, PyYAML 6.0.3, pytest 9.1.1. No Docker needed.
  - All 37 smoke-tested services work under `mock_aws` (IAM, STS, Organizations + SCPs, EC2/VPC, ELBv2, Auto Scaling, S3, EBS, EFS, DynamoDB, RDS, ElastiCache, SQS incl. DLQ moves and FIFO dedup, SNS incl. filter policies, EventBridge, Step Functions, Lambda create, API Gateway, KMS, Secrets Manager, SSM, CloudWatch, Logs, CloudTrail, Config, Route 53, CloudFront, ACM, WAFv2, Kinesis, Firehose → S3, Glue, Athena, Backup, ECS, ECR, Cognito).
  - **Limits:** Lambda handler code never runs without Docker (invoke returns a stub); Step Functions executions run only with `config={"stepfunctions": {"execute_state_machine": True}}`; Athena returns empty results; EventBridge schedules do not fire.
  - **IAM enforcement works** with `set_initial_no_auth_action_count(n)` (AccessDenied for a limited principal).
  - **CloudFormation in moto:** short-form YAML, outputs, exports and `!ImportValue` work; a 46-resource stack deploys in ~2.8 s. It **silently skips** `SNS::Subscription`, `CloudWatch::Alarm`, `SecretsManager::Secret`, `CloudFront::Distribution` and `WAFv2::WebACL`, and drops `PublicAccessBlockConfiguration` and `LifecycleConfiguration` on `S3::Bucket`. moto does no template validation, so cfn-lint is the validator.
  - **cfn-lint:** `cfnlint.decode.decode_str(text)` → `(template, errors)`; `cfnlint.api.lint(text)` → matches. In-process lint ≈ 2.4 s per template, import ≈ 3.3 s; it caught all 3 injected errors (E3002, E1020, E3012).
  - **Timing:** ≈ 1 s per moto-backed test plus ≈ 4 s start-up (first EC2 use loads the AMI catalogue).
  - **UTF-8:** piped output crashes on `✔` (cp1252) unless stdout is reconfigured.
  - **Anomaly:** the venv's `python.exe` vanished once mid-run (no WDAC message); `python -m venv --upgrade .venv` restored it.

## 3. Constraints

- **No real AWS by Claude.** Every test and demo runs under moto's `mock_aws` with fake credentials. The harness sets `AWS_ACCESS_KEY_ID/SECRET/SESSION_TOKEN=testing`, `AWS_DEFAULT_REGION=us-east-1`, and points `AWS_CONFIG_FILE` / `AWS_SHARED_CREDENTIALS_FILE` at non-existent paths so a learner's real profile can never be picked up by a drill.
- **Labs are the learner's actions.** Claude writes lab instructions and cleanup scripts; Claude never runs them against an account.
- **No system installs.** Python packages go into `AWS_SAA_Course_claude/.venv` only.
- **Windows-first.** All tools run on Windows; output forced to UTF-8.
- **Offline.** No network access in drills, demos, quizzes or tests.
- **Original questions only.** No copying from dumps or paid practice tests.
- **Prices are illustrative.** Cost drills use a course-owned `prices.toml` (us-east-1 list prices, dated, labelled "illustrative — check the AWS Pricing Calculator"). The exam tests cost reasoning, not price memorisation.
- **No commits until the learner says so.**

## 4. Design

### 4.0 Syllabus at a glance

Exam domains: **1 Secure (30%)**, **2 Resilient (26%)**, **3 High-performing (24%)**, **4 Cost-optimised (20%)**. The 14 task statements (verbatim, with their knowledge/skill bullets, copied into `docs/exam_guide.md` in Step 0 from the research file):

| Task | Title |
|---|---|
| 1.1 | Design secure access to AWS resources |
| 1.2 | Design secure workloads and applications |
| 1.3 | Determine appropriate data security controls |
| 2.1 | Design scalable and loosely coupled architectures |
| 2.2 | Design highly available and/or fault-tolerant architectures |
| 3.1 | Determine high-performing and/or scalable storage solutions |
| 3.2 | Design high-performing and elastic compute solutions |
| 3.3 | Determine high-performing database solutions |
| 3.4 | Determine high-performing and/or scalable network architectures |
| 3.5 | Determine high-performing data ingestion and transformation solutions |
| 4.1 | Design cost-optimized storage solutions |
| 4.2 | Design cost-optimized compute solutions |
| 4.3 | Design cost-optimized database solutions |
| 4.4 | Design cost-optimized network architectures |

| Week | Topic | Main task statements | Milestone |
|---|---|---|---|
| 00 | Foundations & exam technique: global infrastructure, shared responsibility, Well-Architected, availability maths, boto3/moto basics, account safety | 2.2, all (technique) | — |
| 01 | IAM & multi-account governance: users/groups/roles, policy types and evaluation, STS, federation, Identity Center, Organizations, SCPs/RCPs, Control Tower | 1.1 | M01 IAM baseline |
| 02 | VPC networking: CIDR, subnets, routing, IGW/NAT, SG vs NACL, endpoints/PrivateLink, peering, Transit Gateway, flow logs | 1.2, 3.4, 4.4 | M02 network |
| 03 | Compute & scaling: EC2 families, purchasing options, placement groups, IMDSv2, Auto Scaling, ELB (ALB/NLB/GWLB) | 2.1, 2.2, 3.2, 4.2 | M03 web tier |
| 04 | Storage: S3 (classes, lifecycle, versioning, replication, security, performance), EBS, instance store, EFS, FSx, Storage Gateway | 1.3, 3.1, 4.1 | M04 buckets |
| 05 | Databases & caching: RDS, Aurora, DynamoDB, ElastiCache, DAX, RDS Proxy, purpose-built databases | 2.2, 3.3, 4.3 | M05 data tier |
| 06 | Decoupling, serverless & containers: SQS, SNS, EventBridge, Step Functions, Lambda, API Gateway, ECS/EKS/Fargate | 2.1, 3.2 | M06 async pipeline |
| 07 | Edge, DNS & hybrid: Route 53 routing policies, CloudFront, Global Accelerator, ACM, VPN, Direct Connect | 2.2, 3.4, 4.4 | M07 CDN + DNS |
| 08 | Security services & encryption: KMS, CloudHSM, Secrets Manager, Parameter Store, WAF, Shield, GuardDuty, Inspector, Macie, Security Hub, Cognito | 1.2, 1.3 | M08 hardening |
| 09 | Resilience, DR & observability: DR strategies, RTO/RPO, AWS Backup, CloudWatch, CloudTrail, Config, health checks, retries | 2.1, 2.2 | M09 monitoring + DR |
| 10 | Data, analytics & migration: Kinesis, Firehose, MSK, Glue, Athena, EMR, Redshift, Lake Formation, QuickSight, DMS, DataSync, Snow family, Transfer Family, the 7 Rs | 3.5, 4.1 | M10 analytics |
| 11 | Cost optimisation review: Savings Plans/RIs/Spot, rightsizing, data-transfer costs, storage/DB cost choices, cost tooling, tagging | 4.1–4.4 | M11 cost + final docs |
| 12 | Exam prep: 4 mock exams, weak-area review, final checklist | all | — |

Every week also has a **cost section** in its concept notes and ≥ 1 cost drill, so domain 4 is not crammed into week 11.

### 4.1 Drills (each week's `practice/`)

**Files per week:** `practice/exercises.py` (8–10 drills, easy → a final combined task) and `practice/solutions.py`.

**Shared harness — `_harness/awsdrill.py`** (adapted from `fldrill.py`)
- `Drill` — a `unittest.TestCase` subclass. Each test method runs inside a fresh `mock_aws(config={"lambda": {"use_docker": False}, "stepfunctions": {"execute_state_machine": True}})` context when the drill class sets `uses_aws = True`; pure-Python drills skip moto entirely (instant). Lambda drills test the **handler function directly** with a built event (moto cannot run handler code), and use moto only for the surrounding resources (event source mapping, queues, tables). Helpers:
  - `client(service, region="us-east-1")` / `resource(...)` — boto3 clients bound to the mock.
  - `assertClientError(code)` context manager — asserts a botocore `ClientError` with that error code.
  - `assertHashed(value, digest)` — for predict and decision drills: compares a normalised answer with a stored SHA-256 so the answer is not readable in the file.
  - `FakeClock` — injectable clock for SQS visibility, TTL, rate windows, alarm periods, backoff.
  - `load_template(path)` — CloudFormation YAML/JSON → dict with short-form intrinsics decoded via `cfnlint.decode.decode_str`; `lint_template(path)` → cfn-lint findings via `cfnlint.api.lint`, cached by file content hash (in `_progress/.lintcache/`) because one lint costs ≈ 2.4 s.
  - `iam_enforced(setup_calls)` — wraps moto's `set_initial_no_auth_action_count` so a drill can show a real `AccessDenied` for a limited principal (used in week 01 demos and one predict drill as a second oracle beside the course evaluator).
- Safety: on import, the harness sets the fake credentials and config paths from §3.
- `run()` — same CLI as Flask: `python exercises.py` (all), `python exercises.py 4` (one drill), `--solutions`, `--mutant F#ID`, `--json`. Prints `✔ Ex01 … ✘ Ex04: <first failure> … 7/10 passing`.
- **Harness contract** (as Flask): tests look up learner names at call time; `solutions.py` defines only learner-implemented names.

**Course library — `_harness/awslib/`** (reference implementations later weeks and the capstone tests rely on)
- `policy_eval.py` — the reference IAM policy evaluator (equals week 01's solution; README tells the learner not to open it before finishing week 01).
- `prices.toml` + `prices.py` — illustrative price table and loader.
- `cidr.py` — subnet helpers (equals week 02's solution).

**Drill shape** (docstring spec + example + stub + tests):

```python
# ── Exercise 3 ★: Usable IPs in an AWS subnet ─────────────────
"""
usable_ips(cidr: str) -> int
AWS reserves 5 addresses in every subnet (network, VPC router, DNS, future use, broadcast).
Raise ValueError for prefixes outside /16–/28 (the sizes a VPC subnet may have).
Example: usable_ips("10.0.1.0/24") == 251
Hint: (one line, read only if stuck)
"""
def usable_ips(cidr):
    raise NotImplementedError  # YOUR CODE

class Ex03(Drill):
    """Usable IPs ★"""
    def test_slash_24(self): ...
    def test_slash_28(self): ...
    def test_rejects_slash_29(self): ...
```

**Drill types, mixed each week**
- **write-from-spec (boto3)** — real boto3 calls against moto (create, configure, query); tests read state back through the API.
- **★ build-the-mechanism** — implement the AWS logic in small form: policy evaluation, SG/NACL filtering, route selection, scaling decisions, SQS visibility/DLQ, Route 53 routing, cache behaviour, capacity and cost formulas.
- **fix-the-bug** — a broken config or policy is provided, its test is red (public bucket policy, SSH open to the world, IMDSv1 allowed, Lambda timeout longer than the SQS visibility timeout, ASG on EC2 health checks behind an ALB).
- **predict-the-result** — the learner fills a constant (a policy decision, usable IP count, which object version a GET returns); the test gets the true value by running moto or the reference model, or compares with a hashed answer.
- **decide-the-architecture** — a function maps a structured requirement (RTO, RPO, latency, access pattern, budget) to a service or design; tests cover several scenarios; answers hashed. These train the exam's "which service fits" skill in code.

**Per-week drill content** (★ = build-the-mechanism)

| Week | Drills |
|---|---|
| 00 | ★ ARN parser (`partition/service/region/account/resource`, S3 and IAM edge cases) · ★ composite availability (series/parallel, nines → downtime per month) · ★ AZ-failure capacity check (instances per AZ, survives loss of one AZ?) · shared-responsibility decisions (patching, encryption, network config for EC2 vs RDS vs Lambda) · boto3 sessions/clients + `get_caller_identity` under moto · pagination with paginators over 2,500 objects · `ClientError` handling (`NoSuchBucket`, `BucketAlreadyOwnedByYou`) + retry config · data-transfer direction cost (in free, out paid, inter-AZ both ways) · combined: inventory script listing buckets/instances/queues across 2 regions |
| 01 | ★ action/resource wildcard matching · ★ policy evaluator v1: explicit deny > allow > implicit deny, multiple statements, `NotAction` · ★ conditions (`StringEquals`, `StringLike`, `IpAddress`, `Bool` with `aws:SecureTransport`/`aws:MultiFactorAuthPresent`, `aws:RequestedRegion`) · ★ evaluator v2: SCP ∩ permission boundary ∩ session policy ∩ identity policy, plus same-account resource-based policy (the model and its simplifications are stated in the drill docstring, taken from the official policy-evaluation-logic page) · fix-the-bug: `s3:*` on `*` → least privilege for a given task list (checked with the evaluator) · ★ least-privilege policy generator from an access log (Access Analyzer style) · boto3: role + trust policy + instance profile, `assume_role`, temporary credentials · cross-account trust with `sts:ExternalId` (confused deputy) checked with the evaluator · SCP region allowlist in Organizations (moto) · cost: consolidated billing — tiered usage pooled across member accounts · predict: 6 policy decisions |
| 02 | ★ subnet planner (`ipaddress`; tiers × AZs, non-overlapping) · ★ usable IPs (5 reserved; /16–/28) · ★ route table longest-prefix match (local, IGW, NAT, peering, TGW, prefix lists) · ★ SG vs NACL packet filter (stateful vs stateless, rule numbers, ephemeral ports for return traffic) · ★ reachability over peering (non-transitive) vs Transit Gateway · boto3: VPC with public/private subnets, IGW, NAT, route tables · boto3: SG chaining by SG id; fix-the-bug: port 22 open to `0.0.0.0/0` · gateway endpoint for S3 with endpoint policy + bucket policy `aws:SourceVpce` · cost: NAT gateway vs gateway endpoint for 5 TB/month · predict: can a private-subnet instance without NAT reach S3 with/without an endpoint |
| 03 | ★ instance-type decoder (`m7g.2xlarge` → family, generation, processor, size) and family chooser · ★ purchasing-option cost comparison (On-Demand / Savings Plan / RI / Spot) for a usage profile · ★ target-tracking simulator (desired capacity, min/max, cooldown) + step scaling · ★ ALB listener-rule matcher (host/path/header, priority, default) · ★ cross-zone load-balancing share per instance · boto3: launch template (IMDSv2 required) + ASG across 2 subnets + target tracking · boto3: ALB + target group + path rule · fix-the-bug: `HttpTokens=optional`; ASG `HealthCheckType=EC2` behind an ALB · decide: placement group (cluster/spread/partition, spread limit 7 per AZ) |
| 04 | ★ S3 storage-class cost with minimum duration, minimum billable size and retrieval fees · ★ lifecycle-rule simulator (filters, transitions, expiration, noncurrent versions, AWS transition constraints) · boto3: versioned bucket, default encryption, Block Public Access, TLS-only bucket policy · predict (moto as oracle): GET/LIST after delete on a versioned bucket (delete markers) · fix-the-bug: `Principal: "*"` bucket policy → OAC/role-scoped (checked with the evaluator) · boto3: presigned URL + multipart upload · replication requires versioning (fix-the-bug) · ★ EBS chooser + IOPS/throughput maths (gp3 baseline vs provisioned, io2, st1, sc1) · decide: S3 vs EBS vs instance store vs EFS vs FSx (Windows/Lustre/ONTAP/OpenZFS) vs Storage Gateway |
| 05 | ★ DynamoDB RCU/WCU calculator (item size, strong vs eventual, transactional) · ★ single-table key design: PK/SK + GSI chosen by the learner, tests run every access pattern as a moto query · boto3: optimistic locking with a condition expression, TTL, PITR, `transact_write_items` · ★ cache-aside vs write-through with TTL (counts DB reads, stale reads) · decide: Multi-AZ vs read replica vs Aurora replica vs Aurora Global Database for HA / read scale / DR · decide: engine for a workload (relational, key-value, document, graph, time series, search, in-memory) · RDS Proxy for Lambda connection storms (connection maths) · boto3: RDS Multi-AZ PostgreSQL + read replica + snapshot · cost: DynamoDB on-demand vs provisioned break-even |
| 06 | ★ SQS model: visibility timeout, receive count, DLQ after `maxReceiveCount` (`FakeClock`) · ★ FIFO: message groups, ordering, 5-minute deduplication window · ★ SNS/EventBridge event-pattern matcher (exact, prefix, numeric range, anything-but, exists) · boto3: SQS + DLQ redrive, verified end-to-end · boto3: SNS fan-out to SQS with filter policies · ★ Lambda concurrency maths (RPS × duration, reserved/provisioned, throttling) · fix-the-bug: Lambda timeout vs SQS visibility timeout (AWS guidance: ≥ 6×) · cost: Lambda requests + GB-seconds for a workload · Step Functions ASL with `Retry`/`Catch`, validated structurally · decide: SQS vs SNS vs EventBridge vs Kinesis; ECS on EC2 vs Fargate vs EKS vs Lambda |
| 07 | ★ Route 53 resolver: simple, weighted (seeded), latency, failover, geolocation (most specific wins), geoproximity with bias, multivalue · boto3: hosted zone, alias to ALB, failover pair + health check · ★ CloudFront behaviour matcher (ordered path patterns) + TTL rules (min/default/max vs `Cache-Control`) · ★ cache-hit ratio and origin-load estimate · boto3: CloudFront distribution with S3 origin + OAC · fix-the-bug: ACM certificate for CloudFront outside `us-east-1` · decide: CloudFront vs Global Accelerator; signed URLs vs signed cookies vs presigned URLs · ★ hybrid chooser: VPN vs Direct Connect vs DX + VPN backup, with bandwidth and lead time · cost: egress via CloudFront vs direct from S3 |
| 08 | ★ envelope encryption by hand: `GenerateDataKey` (moto) + AES-GCM locally, store the encrypted data key, decrypt via KMS · ★ KMS key-policy evaluation (key policy must allow; IAM only works when the key policy delegates to the account) via the evaluator · boto3: CMK with rotation, alias, grant · cost: KMS request charges with and without S3 Bucket Keys · fix-the-bug: bucket policy requiring SSE-KMS · boto3: Secrets Manager secret + rotation config; decide Secrets Manager vs Parameter Store · ★ WAF rate-based rule simulator (per-IP window, threshold, block) · decide: GuardDuty / Inspector / Macie / Security Hub / Detective / Shield Advanced / Firewall Manager / Network Firewall · fix-the-bug: access keys on EC2 → instance profile; plaintext secret in Lambda env vars · decide: Cognito user pool vs identity pool |
| 09 | ★ DR strategy chooser (backup & restore / pilot light / warm standby / multi-site) from RTO, RPO, budget · ★ worst-case RPO from backup schedules and replication lag; RTO from recovery steps · ★ static stability: instances needed to survive one AZ loss at peak · ★ CloudWatch alarm evaluator (M of N datapoints, missing-data treatment) · boto3: alarm + SNS action; dashboard · boto3: AWS Backup plan with cold-storage rule (cold ≥ 90 days constraint) + cross-region copy · ★ exponential backoff with full jitter · fix-the-bug: CloudTrail single-region trail without log-file validation · decide: CloudWatch vs CloudTrail vs Config vs X-Ray |
| 10 | ★ Kinesis shard calculator (1 MB/s or 1,000 records/s in, 2 MB/s out per shard; enhanced fan-out) · ★ hot-shard detection from MD5 hash-key ranges · boto3: Kinesis put/get; Firehose to S3 with buffering · ★ Hive-style partition keys + Athena scan-cost estimate (partition pruning, columnar compression) · boto3: Glue database + partitioned table · ★ transfer-time chooser: online (DataSync over DX or internet) vs offline by TB, bandwidth, utilisation, deadline — returns the exam-guide answer (Snowball Edge) and the 2026 reality (Snow devices closed to new customers since 2025-11-07; AWS Data Transfer Terminal) · decide: Athena / Redshift / EMR / Glue / OpenSearch / QuickSight / Lake Formation / MSK · decide: the 7 Rs; DMS homogeneous vs heterogeneous (+ SCT, CDC) |
| 11 | ★ Savings Plan / RI commitment optimiser over an hourly usage profile (coverage vs utilisation) · ★ Spot fleet blended cost with an On-Demand base · ★ rightsizing from p95 CPU/memory series · ★ data-transfer cost model of an architecture (NAT, inter-AZ, endpoints, CloudFront) · boto3: find untagged resources (Resource Groups Tagging API) + create a budget · S3 Intelligent-Tiering vs lifecycle break-even (per-object monitoring fee) · Lambda vs Fargate vs EC2 break-even for a request volume · gp2 → gp3 savings · decide: Cost Explorer / Budgets / Data Exports (CUR) / Compute Optimizer / Trusted Advisor / Cost Anomaly Detection |

Exact counts per week are fixed in each week's plan (8–10 drills, ≥ 3 ★). Behaviour that moto does not model (Step 0 spike decides which) is tested through the course's own models or structural checks, never assumed.

### 4.2 Concept files (each week's `concepts/`)

- **4–6 Markdown notes per week** (`01_<topic>.md` …), each ≈ 150–300 lines, in a fixed shape: *what it is → how it works → numbers to know → when to choose it / when not → exam traps → cost angle → comparison table*. Each ends with "now do drills X–Y and quiz questions on …".
- **1–3 runnable demos per week** (`demo_<topic>.py`): moto-backed scripts that print real API results (route tables, policy decisions, delete markers, DLQ moves). They exit 0 when stdout is piped on Windows.
- `week_NN/README.md` — goals, the routine, exam task statements covered, a "service X vs Y" table, and the interview questions the learner should be able to answer.
- Numbers and limits are taken from `docs/facts.md` (built in Step 0 from official sources, each with URL and date), not from memory.
- **Coverage tags:** every concept note starts with an `Exam tasks: 1.1, 3.4` line, every drill class sets `tasks = ("1.1",)`, and every question has `task`; `verify_course.py --coverage` builds `COVERAGE.md` from these three sources.

### 4.3 Quizzes and mock exams

**Question banks** — TOML (stdlib `tomllib`, no extra dependency):
- `week_NN/quiz/questions.toml` — 30 questions (week 00: 15).
- `exam_prep/mock_exams/mock_1.toml … mock_4.toml` — 65 questions each, **not reused** from the weekly banks.

```toml
[[question]]
id       = "w04-q07"
domain   = 4                 # 1 Secure · 2 Resilient · 3 High-performing · 4 Cost
task     = "4.1"             # exam-guide task statement
services = ["S3", "S3 Glacier Deep Archive"]
kind     = "single"          # or "multi" (then `choose = 2` or 3)
stem     = """A company stores application logs in S3 ... Which is the MOST cost-effective solution?"""
options  = ["S3 Standard, then a lifecycle rule to S3 Glacier Deep Archive after 30 days", "...", "...", "..."]
answer   = ["A"]
explain  = { A = "...", B = "...", C = "...", D = "..." }
ref      = "week_04_storage/concepts/02_s3_storage_classes.md"
```

**Runner — `quiz.py` (course root)**
- `python quiz.py --week 4` → 10 questions, missed/unseen first; `--all`, `--domain 1`, `--review` (questions due in the Leitner schedule).
- Options shuffled per attempt (letters remapped); multi-answer input like `ac`, count enforced.
- After each answer: right/wrong + why each option is right or wrong + the `ref` note.
- Progress in `_progress/progress.json` (git-ignored): per-question box, history, per-domain accuracy.

**Mock exams — `exam_prep/mock_exam.py N`**
- 65 questions, 130-minute countdown (`--untimed` allowed), flag-for-review and a review screen before submitting, as in the real exam.
- Domain split per mock: **20 / 17 / 15 / 13** (≈ 30/26/24/20 %); ≈ 15 % multi-response.
- Report: raw %, per-domain and per-task %, every missed question with explanations, saved to history. All 65 questions are scored (the real exam scores 50 and hides 15 unscored ones). The pass guide is "≥ 72 % raw" and is labelled an approximation (AWS uses a scaled 100–1,000 score with 720 to pass, compensatory across domains; the raw-to-scaled mapping is not published). Unanswered questions count as wrong, as in the exam, and the runner says so ("no penalty for guessing — answer everything").

**Question quality rules** (enforced by `verify_course.py` where mechanical)
- Scenario stem of 2–6 sentences with one deciding requirement (*MOST cost-effective*, *LEAST operational overhead*, *highest availability*, …).
- Single: 4 options; choose-two: 5; choose-three: 6. Every option is a real, plausible AWS design; every option has an explanation.
- The correct option is the longest option in ≤ 40 % of questions; correct letters spread evenly per bank.
- No near-duplicate stems across all banks (difflib ratio ≥ 0.85 is flagged).
- No retired service (§7 rule 1) as a correct answer; `legacy = true` questions (§7 rule 2) ≤ 2 % per bank.
- **Blind-solve check (during build, not in `verify_course.py`):** an independent subagent answers every bank without seeing answers or explanations; every disagreement is resolved by the main session by fixing the question, the answer or the explanation; counts go in the step report.

### 4.4 The capstone — `shortly-infra` (`course_project/`)

**Two places** (as in Flask)
- **Learner's repo** `~/code/shortly-infra`: created in M01, committed each milestone, pushed to GitHub by the learner.
- **Course folder `course_project/`:** `milestones/M01.md … M11.md` (specs split into steps, with hints); `tests/m01 … m11/` (one test file per step); `solutions/m01 … m11/` (full repo snapshot per milestone); `tools/start_milestone.py N --repo PATH`, `tools/run_milestone.py N` (cumulative: runs tests m01…mNN), `tools/conftest.py` (fixtures: `templates` dict loaded via `load_template`, `lint` results, `evaluator`, a `moto_stack(name)` deployer).

**Repo layout the tests rely on:** `infra/<layer>.yaml` per layer (`iam`, `network`, `app`, `storage`, `data`, `async`, `edge`, `security`, `monitoring`, `analytics`), cross-stack references through `Export` / `Fn::ImportValue`, a `Prefix` and `Env` parameter on every stack, and a **lab-size parameter set** (`params/lab.json`) that keeps an optional real deployment cheap.

**How milestones are checked:** (1) cfn-lint clean (cached per file content); (2) structural assertions on the decoded template — the primary check (AZ spread, routes, SG references, encryption flags, lifecycle rules, Block Public Access, alarm thresholds, WAF rules); (3) IAM statements evaluated with `awslib.policy_eval` (e.g. the app role may `dynamodb:PutItem` on the rollup table and may not `dynamodb:DeleteTable`); (4) a **moto deploy smoke test** per layer: the stacks are created in moto in order (exports → imports) and a few facts are read back through the API. Because moto silently skips some resource types and properties (§2), step 4 never asserts on `SNS::Subscription`, `CloudWatch::Alarm`, `SecretsManager::Secret`, `CloudFront::Distribution`, `WAFv2::WebACL`, or on S3 Block Public Access / lifecycle — those are covered by step 2 only. Lambda handler code in the templates lives in `infra/lambda/*.py` files and is tested by calling the handler directly.

| M | Wk | Steps (every item tested) |
|---|---|---|
| M01 | 01 | **.1** repo skeleton (`infra/`, `params/`, `README.md`, `.gitignore`), `Prefix`/`Env` parameters · **.2** app instance role + instance profile: least-privilege statements for the app's needs (secret read, rollup table write, assets bucket prefix, SQS send, logs/metrics) · **.3** Lambda execution role · **.4** deployer role whose created roles must carry a permissions boundary (`iam:PermissionsBoundary` condition) · **.5** auditor role: read-only, assumable only with MFA · **.6** evaluator checks: 10 required allows, 10 required denies, no `Action: "*"` |
| M02 | 02 | **.1** VPC + 3 tiers × 2 AZs (public / app / data), CIDR plan in README · **.2** IGW, NAT (`NatMode = single \| per-az`), route tables; data tier has no internet route · **.3** SGs chained ALB → app → db/cache by SG id · **.4** S3 + DynamoDB gateway endpoints · **.5** flow logs to CloudWatch Logs · **.6** exports consumed by later stacks |
| M03 | 03 | **.1** ALB in public subnets, target group health check `/healthz` · **.2** launch template: Graviton type parameter, IMDSv2 required, instance profile from M01, user data that writes and starts the small provided stdlib app (`course_project/app/`, inlined) · **.3** ASG min 2 across app subnets, ELB health checks, target tracking · **.4** listener rules (`/api/*`, default) · **.5** HTTP listener only for now; HTTPS arrives in M07 with the edge layer |
| M04 | 04 | **.1** assets bucket: versioning, encryption, Block Public Access, TLS-only policy · **.2** logs bucket with lifecycle (IA → Glacier tiers → expiry) and ALB access-log permissions · **.3** noncurrent-version expiry · **.4** bucket policy decisions checked with the evaluator |
| M05 | 05 | **.1** DB subnet group in data subnets; RDS PostgreSQL Multi-AZ, encrypted, `ManageMasterUserPassword` · **.2** backups, deletion protection (on in prod params, off in lab params) · **.3** ElastiCache Redis replication group, Multi-AZ, automatic failover, in-transit encryption · **.4** DynamoDB `clicks_daily` (on-demand, PITR) · **.5** README note: why Postgres + Redis + DynamoDB, with the week-05 calculators' numbers |
| M06 | 06 | **.1** SQS clicks queue + DLQ (`maxReceiveCount` 5), visibility ≥ 6 × consumer timeout · **.2** Lambda consumer with SQS event source (batch size, `ReportBatchItemFailures`) writing daily rollups · **.3** SNS alerts topic · **.4** EventBridge schedule for the nightly link-health check · **.5** roles from M01 cover the new actions (evaluator) |
| M07 | 07 | **.1** CloudFront: default behaviour → ALB, `/static/*` → S3 via OAC; S3 bucket policy allows only the distribution · **.2** cache and origin-request policies; response headers policy · **.3** viewer HTTPS always (CloudFront default certificate, or an ACM certificate in us-east-1 when `DomainName` is set); with a domain, an HTTPS listener on the ALB too, otherwise CloudFront → ALB over HTTP protected by step .5 · **.4** Route 53 alias A/AAAA records · **.5** ALB reachable only from CloudFront (managed prefix list + origin secret header) |
| M08 | 08 | **.1** customer-managed KMS key (rotation, key policy) used by S3, RDS, SQS · **.2** WAFv2 web ACL on CloudFront: AWS managed common rules + rate-based rule on `/shorten` · **.3** secret rotation · **.4** GuardDuty detector (parameter-gated) · **.5** evaluator: only the app role can decrypt with the key |
| M09 | 09 | **.1** alarms: ALB 5xx rate, target p95 latency, DLQ depth > 0, RDS CPU and free storage, Lambda errors → SNS · **.2** dashboard · **.3** AWS Backup plan (daily, retention, cross-region copy) · **.4** CloudTrail multi-region with log-file validation · **.5** `DR.md`: pilot light in a second region, RTO/RPO computed with the week-09 calculators |
| M10 | 10 | **.1** Firehose delivery stream → S3 data lake with Hive-style prefixes · **.2** consumer also emits click events to Firehose · **.3** Glue database + table with partition projection · **.4** Athena workgroup with a bytes-scanned limit · **.5** lifecycle on the lake (Intelligent-Tiering) |
| M11 | 11 | **.1** tagging policy: every taggable resource carries `project`, `env`, `owner` (test walks all templates) · **.2** monthly AWS Budget with alerts · **.3** ASG mixed instances: On-Demand base + Spot, several Graviton types · **.4** `COST.md`: monthly estimate (lab and prod params) computed with the week-11 calculators · **.5** `ARCHITECTURE.md`: Mermaid diagram + interview walkthrough (why each choice, what fails when an AZ dies, how it scales, what it costs) |

**Domain names.** M07 works without a domain: the `DomainName` parameter defaults to empty, in which case the edge stack uses the CloudFront default certificate and `*.cloudfront.net` name and creates no Route 53 or ACM resources (conditions); tests cover both cases. A learner who owns a domain sets it in `params/` for a real deployment. CloudFront-scoped resources (ACM certificate, WAF web ACL) are created in `us-east-1`, which tests check.

**Optional real deployment** (learner's choice, any milestone from M02): `course_project/DEPLOY.md` explains deploying with the AWS CLI using `params/lab.json`, shows the approximate hourly cost of what is running (NAT gateways, ALB and RDS cost money even when idle), and gives the teardown order. Claude never deploys.

### 4.5 Optional real-AWS labs (each week's `lab/`)

- `lab/LAB.md` — 30–90 minute console + CLI exercise mirroring the week's drills, with an estimated cost (most labs ≈ free; any paid step is marked and timed), what to observe, and screenshots to take for the learner's notes.
- `lab/cleanup.py` — lists and deletes only resources tagged `saa-course=lab` in the chosen region. **Dry-run by default**; `--yes` actually deletes; prints every resource it would touch. Tested against moto with tagged and untagged resources: only tagged ones go, and nothing goes without `--yes`.
- **Week 00 lab = account safety first:** root MFA, no root access keys, an IAM Identity Center admin user, a CLI profile via `aws configure sso`, a zero-spend budget and a monthly cost budget, a CloudWatch billing alarm (us-east-1), and the rule "run cleanup.py after every lab".
- **Account plan facts the labs depend on** (from the research file; re-checked in `docs/facts.md`): new accounts choose a **Free plan** (no charges; ends after 6 months or when the 100–200 USD credits run out, then the account closes with 90 days' retention) or a **Paid plan**. A Free-plan account is **automatically upgraded to Paid** if it joins AWS Organizations or sets up a Control Tower landing zone — so Organizations, SCPs and Control Tower are practised in moto only, never in a Free-plan lab. Public IPv4 addresses cost 0.005 USD/hour each since 2024-02-01, so labs release Elastic IPs and avoid idle public IPs. Labs never promise the pre-2025 "12-month free tier".

### 4.6 Exam prep (`exam_prep/`)

- `mock_exam.py` and the 4 mock banks (§4.3).
- `FINAL_REVIEW.md` — keyword → service table (e.g. "least operational overhead" → managed/serverless), the top traps per domain, numbers to know, and a 7-day plan: mock 1 → review weak tasks with `quiz.py --review` → mock 2 → … → book the exam when two mocks in a row are ≥ 80 %.

## 5. Target layout

```
AWS_SAA_Course_claude/
├── README.md · COURSE_FLOW.md · COVERAGE.md · requirements.txt · verify_course.py · quiz.py
├── _harness/
│   ├── awsdrill.py · quizlib.py
│   └── awslib/{policy_eval.py, cidr.py, prices.py, prices.toml}
├── _dev/{mutants/week00.py … week11.py, mutants/m01.py … m11.py, tests/}
├── _progress/                        # quiz history (git-ignored)
├── docs/{specs/, exam_guide.md, facts.md}
├── week_00_foundations_and_exam_technique/
│   ├── README.md
│   ├── concepts/{01_*.md …, demo_*.py}
│   ├── practice/{exercises.py, solutions.py}
│   ├── quiz/questions.toml
│   └── lab/{LAB.md, cleanup.py}
├── week_01_iam_and_governance/
├── week_02_vpc_networking/
├── week_03_compute_and_scaling/
├── week_04_storage/
├── week_05_databases_and_caching/
├── week_06_decoupling_serverless_containers/
├── week_07_edge_dns_hybrid/
├── week_08_security_and_encryption/
├── week_09_resilience_dr_observability/
├── week_10_data_analytics_migration/
├── week_11_cost_optimisation/
├── course_project/
│   ├── README.md · DEPLOY.md
│   ├── app/                          # tiny stand-in shortener started by user data (stdlib only)
│   ├── milestones/M01.md … M11.md
│   ├── tests/m01/ … m11/
│   ├── solutions/m01/ … m11/
│   └── tools/{start_milestone.py, run_milestone.py, conftest.py}
└── exam_prep/
    ├── FINAL_REVIEW.md · mock_exam.py
    └── mock_exams/mock_1.toml … mock_4.toml
```

## 6. Build order

| Step | Work | Gate |
|---|---|---|
| 0. Foundation | `.venv` + pinned `requirements.txt` (from the spike); `docs/exam_guide.md` (verbatim task statements + in-scope services) and `docs/facts.md` (numbers, Free Tier rules, retired services — each with source URL and date); `awsdrill.py`, `quizlib.py`, `quiz.py`, `mock_exam.py`, `verify_course.py`, milestone tools, `conftest.py`, `awslib/` skeleton, lab-cleanup library | `verify_course.py --self-test` (runs `_dev/tests`: harness, quiz engine, cleanup library, credential-safety test) green |
| 1. Pilot | Week 00 + week 01 fully built (concepts, demos, drills, solutions, mutants, quiz with blind-solve check, lab) + M01 + a pilot `README.md` and `COURSE_FLOW.md` | **Pause: the learner tries the pilot** (can be waived) |
| 2–11. Weeks 02–11 | **One plan per week**: concepts, demos, drills, solutions, mutants, quiz (blind-solved), lab, and its milestone. Week content (everything except milestones) can be built **in parallel** across weeks; milestones are built **in order** because each starts from the previous solution | Verification (§8) per week |
| 12. Exam prep + docs | 4 mock exams (blind-solved, domain split checked), `FINAL_REVIEW.md`, `COVERAGE.md`, root `README.md`, `COURSE_FLOW.md`, `DEPLOY.md` | Full `verify_course.py` green |

**Execution (learner's standing preference + "use as many subagents as you want"):** implementer subagents (Sonnet) write; independent tasks run in parallel; the main session verifies every task itself — runs the commands and `verify_course.py`, reads the files — before accepting it. Each step ends with a report: what was built, what was verified (with command output), what remains. No commits.

## 7. Content currency: exam guide vs 2026 reality

`docs/facts.md` (Step 0, from the research file) lists every retired or changed service, limit and default with its official source and date. Three rules follow from it:

1. **Retired and not needed for the exam** — QLDB (shut down 2025-07-31), Elastic Transcoder (2025-11-13), Data Pipeline (closed to new customers), Proton, Pinpoint, OpsWorks, EC2-Classic, Aurora Serverless v1, Kinesis Data Analytics for SQL, WAF Classic, Inspector Classic, Snowmobile, Snowcone, Launch Configurations, S3 Select, the original vault-based Glacier service, Cloud9, App Mesh. Mentioned at most in a one-line "retired" note; never a correct quiz answer; `verify_course.py` greps concepts and banks for these names outside `retired` notes.
2. **Closed to new customers but still in the exam guide — Snow Family (Snowball Edge).** Taught for exam purposes ("large offline transfer, limited bandwidth" → Snowball Edge), always with the 2026 status: closed to new customers since 2025-11-07, successors DataSync (online) and AWS Data Transfer Terminal (physical). Quiz questions where such a service is the correct answer carry `legacy = true`, show the status note in their explanation, and are capped at 2 % of each bank. Application Discovery Service and Migration Hub (maintenance) follow the same rule.
3. **Changed numbers and defaults** are taught at their current value, with the old value named once as "older material says…": S3 max object 50 TB (was 5 TB), SQS max message 1 MiB (was 256 KiB), gp3 up to 64 TiB / 80,000 IOPS / 2,000 MiB/s (was 16 TiB / 16,000 / 1,000), S3 default SSE-S3 encryption (2023-01-05), Block Public Access + ACLs disabled on new buckets (2023-04), IMDSv2-by-default options, public IPv4 charges (2024-02-01), Aurora Serverless v2 scaling to 0 ACUs (2024-11-20), CodeCommit back in general availability (2025-11-24). A question never hinges on a number that changed after 2022, because the exam may still use the old value.

Facts the research could not confirm (e.g. the RDS PostgreSQL read-replica count, One Zone-IA and Express One Zone minimum durations) are not stated as numbers anywhere until Step 0 confirms them from an official page.

## 8. Definition of done (verified by running, not asserted)

- **Drills:** per week, every test fails on the stubs; every test passes with `--solutions`; every mutant in `_dev/mutants/weekNN.py` is rejected (≥ 1 per drill); ≥ 3 ★ drills; the whole file runs in < 60 s (moto costs ≈ 1 s per test; pure-Python drills are instant).
- **Demos:** each `demo_*.py` exits 0 with stdout piped on Windows.
- **Quizzes and mocks:** schema valid (ids unique, answer letters exist, `choose` matches answer count, every option explained, `ref` file exists); counts (30 per week, 15 for week 00, 65 per mock with the 20/17/15/13 split, 10–20 % multi); correct-is-longest ≤ 40 %; letter spread; no near-duplicates; no retired service as an answer; blind-solve disagreements all resolved (step report).
- **Coverage:** `COVERAGE.md` generated by `verify_course.py --coverage`: every task statement has ≥ 1 concept note, ≥ 1 drill and ≥ 12 questions.
- **Milestones:** `solutions/mNN` passes `run_milestone.py N` (cumulative) and is cfn-lint clean; the starting state (`solutions/m(N-1)` + `tests/mNN`; an empty repo for M01) fails; every mutant in `_dev/mutants/mNN.py` makes at least one test fail.
- **Labs:** each `cleanup.py` passes its moto safety tests (dry-run default; only tagged resources deleted).
- **Safety:** a test proves the harness never resolves real credentials (a fake `~/.aws` profile in a temp dir is ignored).

## 9. Learner's weekly routine

1. **Concepts** (~2–3 h): read the notes, run the demos.
2. **Drills** (~2–3 h): `python practice/exercises.py` until N/N; stuck → hint → `solutions.py`.
3. **Quiz** (~1 h): `python quiz.py --week N` until ≥ 80 %; read every explanation, including for questions answered correctly.
4. **Milestone** (~2–3 h): `start_milestone.py N --repo ~/code/shortly-infra` → build → `python run_milestone.py N` until green → commit and push.
5. **Lab** (optional, ~1 h): `lab/LAB.md` in a real account → `python lab/cleanup.py --yes`.
6. **Review** (~15 min, from week 02): `python quiz.py --review`.

## 10. Out of scope

- Professional-level depth (SAP-C02), Terraform and CDK beyond a comparison note in week 00.
- Real deployments, account changes, or any AWS call by Claude.
- Editing any other course (including Flask, whose app this course only references).
- Booking the exam.

## 11. Risks and open items

- **moto fidelity.** Known gaps are recorded in §2 (Lambda handlers do not run, Athena returns nothing, some CloudFormation types and S3 properties are skipped). Drills and milestone checks use moto only for behaviour the spike verified; everything else goes through the course's own models or structural checks. A future moto upgrade is re-checked by `verify_course.py` before the pin moves.
- **Package compatibility.** The spike installed the latest versions with no WDAC blocks; Step 0 pins exactly those versions in `requirements.txt`. If the venv's `python.exe` disappears again, `README` documents `python -m venv --upgrade .venv`.
- **Speed.** moto ≈ 1 s per test and cfn-lint ≈ 2.4 s per template. Mitigated by pure-Python ★ drills, lint caching, and the cumulative milestone runner reusing one session.
- **AWS changes.** Limits, defaults and service status move. Every number lives in `docs/facts.md` with its source and date, so updates are one-file edits.
- **Question accuracy.** ~600 original questions is the largest risk. Mitigated by the blind-solve check, the mechanical checks in §8, and `ref` links back to concept notes so a wrong fact is found and fixed in one place.
- **Size.** Large. Mitigated by the pilot gate, per-week plans, parallel week builds and per-step verification.
- **Exam version.** If AWS announces a successor before the course is finished, the learner decides whether to retarget; `docs/exam_guide.md` makes the delta checkable.

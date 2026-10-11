# AWS SAA Course — Plan 5: Week 05 (Databases and caching) + M05 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build week 05 — databases and caching — in the shape of weeks 01–04: 5 concept notes, 2 demos, 10 drills (4 ★), a 30-question quiz, a real-AWS lab with a safe cleanup, and capstone milestone M05 (the `data` stack: RDS PostgreSQL, an ElastiCache Valkey/Redis replication group, the DynamoDB clicks table, and the app role's access to the database secret).

**Architecture:** Drills 01, 02, 06 and 07 are pure-Python models whose answer keys live in three new modules: `_harness/awslib/dynamo.py` (read/write units, provisioned capacity, on-demand vs provisioned cost and break-even), `caching.py` (lazy loading vs write-through with TTL: hits, misses, database reads, stale reads) and `dbmath.py` (Lambda concurrency vs `max_connections`, when RDS Proxy is needed). Drills 03–05 and 08 run boto3 against moto, which enforces DynamoDB conditions and transactions and RDS deletion protection but never expires TTL items, reports constant consumed capacity and has no Multi-AZ standby (spike: `docs/research/2026-10-12-moto-database-spike.md`). moto's CloudFormation skips ElastiCache, Secrets Manager and Aurora clusters (and crashes on a `!GetAtt` of them, or of `MasterUserSecret.SecretArn`), and drops many DB-instance and table properties; so M05's tests read the rendered template, and the deploy test uses the new `cfn.for_moto` to strip the skipped types and replace that GetAtt before `create_stack`. `labclean` learns DynamoDB tables and backups, RDS instances and snapshots, and DB subnet groups. Built together with plan 4 in one scratch copy; all code verified there before installation (Task 1).

**Tech Stack:** as plans 1–4. No new packages.

**Spec:** `docs/specs/2026-10-08-aws-saa-course-design.md` §4.0–§4.5 (week 05 row, drill row 05, M05 row). Facts: `docs/research/2026-10-12-database-facts.md` (official sources, read 2026-10-12). moto spike: `docs/research/2026-10-12-moto-database-spike.md`. Companion and shared constraints: `docs/specs/2026-10-12-aws-saa-plan-4-week-04.md`.

**Execution:** as plan 4 (joint build; the learner's instruction of 2026-10-12).

## Global Constraints

- Everything in plans 1–4's Global Constraints.
- **Exam vs 2026 reality:** teach today's values (DynamoDB on-demand prices cut 50 % on 2024-11-01, on-demand the default and recommended mode; transactions up to 100 items and 4 MB — the old limit is not confirmed, so it is not named; Aurora Serverless v2 scales to 0 and up to 256 ACUs; Aurora Global Database up to 10 secondary Regions; Valkey added to ElastiCache and cheaper than Redis OSS). QLDB, Aurora Serverless v1 and Timestream for LiveAnalytics appear only on lines containing "retired" and never in a question.
- **Lab cost:** cents — an on-demand DynamoDB table and a Single-AZ `db.t4g.micro` PostgreSQL instance (never Multi-AZ in the lab); every resource tagged `saa-course=lab`.

## Review Focus

1. **Cleanup must never delete or modify an untagged table, database or snapshot**, must turn off deletion protection only on tagged resources, delete read replicas before their source, and leave a tagged source alone if an untagged replica would be promoted. Tests: `_dev/tests/test_labclean_storage_db.py`.
2. **The data tier is checked on the template**, because moto drops ManageMasterUserPassword, DeletionProtection, VPCSecurityGroups, PITR and TTL and skips ElastiCache entirely. Tests: `test_m05_1…5`; mutants `plaintext-password`, `unprotected-prod`, `no-pitr`, `redis-no-tls`.
3. **The moto deploy must not crash on unsupported GetAtts**: `cfn.for_moto` removes skipped types and replaces `MasterUserSecret.SecretArn`. Test: `_dev/tests/test_cfn_intrinsics.py`, `test_m05_6_exports_and_deploy.py`.
4. **The app can read only its own database secret** (RDS names it `rds!db-…`, which M01's `shortly/db-*` statement does not cover). Test: `test_m05_3_secret_access.py`; mutant `any-secret`.
5. **M01–M04 keep passing** after `start_milestone.py 5`. Test: `run_milestone.py 5` is cumulative.

## Files this plan creates or changes

```
_harness/awslib/dynamo.py · caching.py · dbmath.py   (new: week 05 drills 01, 02, 06, 07 answer keys)
_harness/awslib/cfn.py             (changed: for_moto strips skipped types and replaces unsupported GetAtts)
_harness/awslib/prices.toml        (changed: [database] section)
_harness/labclean.py               (changed: dynamodb_backups, dynamodb_tables, rds_instances, rds_snapshots, db_subnet_groups finders; new FINDERS order)
_dev/tests/test_database_models.py   (new)
_dev/tests/test_cfn_intrinsics.py · test_milestone_tools.py   (changed)
_dev/mutants/week05.py · m05.py    (new)
course_project/tools/conftest.py · start_milestone.py   (changed: dynamo fixture; moto_stacks is deploy(layer, skip_types=(), getatt_values=None, **params); copies dynamo, caching, dbmath)
course_project/tests/m05/test_m05_{1..6}_*.py   (new)
course_project/solutions/m05/{infra/data.yaml, README.md; the M04 files unchanged}   (new)
course_project/milestones/M05.md · course_project/README.md · DEPLOY.md   (new / changed)
docs/facts.md                      (changed: databases and caching section, database prices, Timestream for LiveAnalytics in the retired table)
week_05_databases_and_caching/README.md · concepts/01..05_*.md · concepts/demo_*.py (2) · practice/exercises.py · practice/solutions.py · quiz/questions.toml · lab/LAB.md · lab/cleanup.py   (new)
README.md · COURSE_FLOW.md · COVERAGE.md · docs/specs/2026-10-12-aws-saa-plan-5-report.md   (changed / new)
```

## Rulings made while planning (spec deviations and choices)

- **Joint build with plan 4** (P4-1).
- **M05's deploy test strips the ElastiCache and Secrets Manager types and replaces the MasterUserSecret GetAtt** before `create_stack` (`cfn.for_moto`, P5-1): moto skips those types and crashes on their GetAtts.
- **The app role gets its database secret through `AppDbSecretPolicy` in the data stack**, scoped to `!GetAtt Database.MasterUserSecret.SecretArn`: RDS names its managed secret `rds!db-…`, which M01's `shortly/db-*` statement does not cover; M01's permissions boundary already allows `secretsmanager:GetSecretValue`.
- **Lab vs prod sizes**: prod `db.m7g.large` Multi-AZ with 7-day backups and deletion protection, a two-node cache with Multi-AZ failover, deletion protection on the table; lab `db.t4g.micro` Single-AZ, 1-day backups, a one-node cache, no deletion protection (spec M05.2 "deletion protection on in prod params, off in lab params").
- **The cache engine is Valkey if cfn-lint 1.57.2 accepts it** (cheaper than Redis OSS per facts.md), otherwise Redis OSS — recorded in the M05 report.
- **Drill 10 drops Timestream** (Timestream for LiveAnalytics closed to new customers on 2025-06-20) and has nine engine scenarios.
- **Drill 09 says "replication in under a second" rather than "RPO about one second"**, because facts.md gives the Global Database RPO only as "measured in seconds".

---

### Task 1: Install the verified code bundle (weeks 04 and 05 together)

**Files:** every file in Appendix A (create, or replace where it already exists), exactly as given.

- [ ] **Step 1: Write every Appendix A file** with exactly the content shown. Files already installed early (the six model modules, `prices.toml`, the two model test files) are listed for completeness.
- [ ] **Step 2:** `.venv/Scripts/python.exe -m pytest _dev/tests -o addopts="" -p no:cacheprovider -q | tail -1` → the count in Appendix A's header, all passed.
- [ ] **Step 3:** both weeks' drills 0/10 and `--solutions` 10/10; `verify_course.py --week 4` and `--week 5` all ✔; `--milestone 1` … `--milestone 5` all ✔.

---

### Task 2: Database facts in `docs/facts.md`

**Files:** Modify `docs/facts.md`.

- [ ] **Step 1:** Add a section `## Databases and caching (week 05)` after the "Storage (week 04)" section, built from `docs/research/2026-10-12-database-facts.md` sections 1–5, subsections: Amazon RDS · Amazon Aurora · Amazon DynamoDB · DAX · Amazon ElastiCache · Purpose-built databases. Keep every **confirmed** row that a week 05 note or question could need. Keep the `Fact | Value | Changed? | Source` columns and the research's sources, with a source key line at the top like the earlier week sections. Rows the research lists as unconfirmed are NOT added.
- [ ] **Step 2:** Add `### Databases and caching (week 05)` to `## Prices used in drills (illustrative, us-east-1)` with every `prices.toml [database]` value and its research row (DynamoDB on-demand and provisioned, storage, PITR; RDS PostgreSQL single-AZ and Multi-AZ; gp3; Aurora Serverless v2; RDS Proxy; ElastiCache). Say at the top that the prices come from the AWS Price List files.
- [ ] **Step 3:** Update the "Not confirmed" line: append the research's unconfirmed database items (condensed); REMOVE items that the week 04 and week 05 research resolved — "RDS PostgreSQL read-replica count" (resolved: 15 from the read-replicas-per-primary quota, medium confidence — carry that wording into the row) and "One Zone-IA and S3 Express One Zone minimum durations" (One Zone-IA resolved to 30 days; keep only "S3 Express One Zone minimum duration: pages disagree").
- [ ] **Step 4:** Retired/closed services: QLDB is already listed as retired; add Timestream for LiveAnalytics (closed to new customers 2025-06-20) to the Rule 1 table if the research confirms it, on a line containing the word "retired" (e.g. "retired for new customers"). Aurora Serverless v1 is already listed.
- [ ] **Step 5:** `grep -c "^| " docs/facts.md` grows by at least 150; `verify_course.py --banks | grep retired` stays ✔.

---

### Task 3: Week 05 concept notes, demos, README and lab

**Files:** Create in `week_05_databases_and_caching/`: `concepts/01_rds.md`, `concepts/02_aurora.md`, `concepts/03_dynamodb.md`, `concepts/04_caching_elasticache_dax.md`, `concepts/05_choosing_a_database.md`, `concepts/demo_dynamodb_in_moto.py`, `concepts/demo_database_math.py`, `README.md`, `lab/LAB.md`, `lab/cleanup.py`.

**Writing rules:** plan 1 Task 12's rules (first line `Exam tasks: …`; sections What it is / How it works / Numbers to know / When to choose it / Exam traps / Cost angle / Comparison; 150–300 lines; numbers only from `docs/facts.md`; plain English). Do **not** reveal drill 09's or drill 10's answers or paste drill solutions; teach the rules with other examples. Teach today's values for every "changed" row (name the old value once). Retired services (QLDB, Aurora Serverless v1, Timestream for LiveAnalytics) appear only on lines containing the word "retired".

| File | Exam tasks line | Must cover |
|---|---|---|
| `01_rds.md` | `Exam tasks: 3.3, 2.2, 1.3` | what RDS manages and what you still own; engines; instance classes and storage (gp3/io, autoscaling, max size); Multi-AZ DB instance (synchronous standby, not readable, failover time, same endpoint) vs Multi-AZ DB cluster (two readable standbys, faster failover); read replicas (async, quota, cross-Region, promote, Multi-AZ replica); backups (retention range and defaults, PITR, manual snapshots, restore = new instance); encryption (only at creation; the snapshot-copy path; in transit); IAM database authentication; ManageMasterUserPassword with Secrets Manager; RDS Proxy (pooling, failover help, IAM; drill 07); Blue/Green deployments; maintenance windows; deletion protection; comparison table Multi-AZ instance / Multi-AZ cluster / read replica |
| `02_aurora.md` | `Exam tasks: 3.3, 2.2, 4.3` | Aurora architecture (shared storage, copies across AZs, self-healing, max size), replicas and endpoints (cluster, reader, custom, instance), failover priority; Aurora Serverless v2 (ACU range, scale to 0 — changed; v1 on a line with "retired"); Global Database (secondary Regions — changed, replication lag, RPO/RTO wording, managed failover, write forwarding); Backtrack, cloning; Standard vs I/O-Optimized pricing rule; DSQL and Limitless one line each; comparison table RDS vs Aurora |
| `03_dynamodb.md` | `Exam tasks: 3.3, 4.3, 2.2` | tables, items (400 KB), partition and sort keys; read/write units and consistency (drill 01); on-demand vs provisioned (prices changed 2024-11, auto scaling, switching rules) and break-even (drill 02); partitions and hot keys; GSI vs LSI; Query vs Scan; the single-table design idea (drill 03 — your own example, not shortly's); conditional writes and optimistic locking; transactions (limit from facts.md); streams; TTL; backups and PITR; global tables (MREC, MRSC changed); table classes; encryption always on; comparison table GSI vs LSI |
| `04_caching_elasticache_dax.md` | `Exam tasks: 3.3, 4.3` | why cache; ElastiCache engines (Valkey added — changed, Redis OSS, Memcached) and node-based vs Serverless; cluster mode disabled vs enabled, replicas, Multi-AZ automatic failover; encryption and AUTH/RBAC; backups (Valkey/Redis only); caching strategies from AWS's page: lazy loading, write-through, TTL, the combination (drill 06); session stores; DAX (microseconds, item and query cache, write-through, default TTL, not for strongly consistent reads); MemoryDB (durable); comparison table ElastiCache Valkey/Redis / Memcached / DAX / MemoryDB |
| `05_choosing_a_database.md` | `Exam tasks: 3.3, 2.2, 4.3` | the purpose-built map (relational, key-value, document, wide-column, graph, in-memory, search, time series — Timestream for LiveAnalytics on a line with "retired" for new customers; QLDB on a line with "retired"); DocumentDB, Neptune, Keyspaces, OpenSearch Service, MemoryDB one paragraph each; the HA / read-scale / DR decision table (drill 09's topic, your own scenarios); Lambda and databases: connection maths and RDS Proxy (drill 07); cost angle across RDS, Aurora, DynamoDB (Database Savings Plans one line); the big decision table |

- [ ] **Step 1: Write the five notes** per the table.
- [ ] **Step 2: `concepts/demo_dynamodb_in_moto.py`** — offline moto demo: a table with PK/SK and one GSI (your own example, e.g. orders), a conditional put that fails (ConditionalCheckFailedException), a transaction that is cancelled as a whole, a Query by key range and a GSI query; then print plainly what moto does not simulate (TTL never deletes, ConsumedCapacity is not real, no Multi-AZ failover for RDS, CloudFormation skips ElastiCache) — "that is why drills 01, 02, 06 and 07 are models". Use only behaviours `docs/research/2026-10-12-moto-database-spike.md` confirms. Ends with "Now do drills 03–05 and 08." Exit 0 piped.
- [ ] **Step 3: `concepts/demo_database_math.py`** — pure Python with `dynamo`, `caching`, `dbmath`: a capacity-unit table for item sizes and consistencies; on-demand vs provisioned for two traffic shapes and the break-even; a cache simulation of the same event stream under lazy and write-through (hits, DB reads, stale reads); a Lambda connection storm with and without a proxy. Different numbers from the drills' examples. Ends with "Now do drills 01, 02, 06 and 07." Exit 0 piped.
- [ ] **Step 4: `README.md`** — headings as weeks 00–03. Goals (6): choose RDS features for HA, read scale and DR; know when Aurora is worth it; size and price a DynamoDB table; design DynamoDB keys for access patterns; add a cache with the right strategy; pick the right purpose-built database. Your week (≈ 10–12 h, quiz `python quiz.py --week 5 -n 30`, milestone M05). Exam tasks covered: 2.2, 3.3, 4.3. Service comparison table: RDS / Aurora / DynamoDB / ElastiCache / DAX / DocumentDB / Neptune. Interview questions (10). Final line: "Now you may read `_harness/awslib/dynamo.py`, `caching.py` and `dbmath.py` — compare them with your drills 01, 02, 06 and 07."
- [ ] **Step 5: `lab/LAB.md` and `lab/cleanup.py`** — LAB (≈ 60–90 min; cents — RDS db.t4g.micro single-AZ may be covered by the free plan or Free Tier; never choose Multi-AZ in the lab): 1 before you start (guard rails, profile `saa-lab`, one Region, tag EVERYTHING `saa-course=lab`); 2 DynamoDB: an on-demand table with PK/SK, put items, a conditional put that fails (CLI), a Query, turn on PITR, take an on-demand backup; 3 RDS: create PostgreSQL db.t4g.micro single-AZ with "Manage master credentials in AWS Secrets Manager", no public access, deletion protection OFF for the lab, tagged; read its configuration (endpoint, backups, the Multi-AZ setting you did not choose and its price), take a manual snapshot (tagged); 4 clean up: `python lab/cleanup.py --profile saa-lab` then `--yes`; check that the automated backups and the Secrets Manager secret are gone; 5 what to write down. `cleanup.py` = week 03's pattern with `kinds=["dynamodb_tables", "dynamodb_backups", "rds_instances", "rds_snapshots", "db_subnet_groups"]` and a docstring naming them (the main session confirms the final kind names when it installs the cleanup code).
- [ ] **Step 6: Verify** — demos exit 0 piped; `verify_course.py --week 5 2>&1 | grep -E "concept|demo|README|lab"` all ✔ (the lab line may show ✘ until the code bundle with the new cleanup kinds is installed — report it); `verify_course.py --banks | grep retired` ✔.

---

### Task 4: Week 05 quiz (30 questions) + blind solve

**Files:** Create `week_05_databases_and_caching/quiz/questions.toml`.

- [ ] **Step 1: Write the 30 questions** (quiz rules, ruling 8; ids `w05-q01 … w05-q30`; 3–6 Select TWO; refs = Task 3's five notes):

| ids | domain · task | topics (one question each, in order) |
|---|---|---|
| q01–q06 | 2 · 2.2 / 3 · 3.3 | Multi-AZ DB instance for automatic failover with the least change · read replicas to offload reporting reads · a cross-Region read replica for DR without moving to Aurora · Multi-AZ DB cluster for readable standbys and faster failover · encrypting an existing unencrypted RDS database (snapshot, encrypted copy, restore) · recovering from a bad UPDATE ten minutes ago (point-in-time restore to a new instance) |
| q07–q09 | 1 · 1.3 / 3 · 3.3 | database credentials without passwords in code, rotated automatically (Secrets Manager via managed master password; works-but-weaker: IAM user keys) · Lambda functions exhausting connections in a burst (RDS Proxy) · protecting a production database from accidental deletion (deletion protection + final snapshot / DeletionPolicy) |
| q10–q14 | 3 · 3.3 / 2 · 2.2 / 4 · 4.3 | Aurora replicas and the reader endpoint for read scaling · Aurora Global Database for a one-second RPO across Regions · Aurora Serverless v2 for a dev database idle most of the day (scale to zero) · Aurora cloning for a fast test copy of production · Aurora I/O-Optimized when I/O dominates the bill (MOST cost-effective) |
| q15–q22 | 3 · 3.3 / 4 · 4.3 | DynamoDB on-demand for a new app with unknown, spiky traffic · provisioned with auto scaling for a steady, predictable table (cost) · a GSI for a new access pattern on an existing table · an LSI must be created with the table (the team forgot) · optimistic locking with a condition expression · all-or-nothing updates across items (TransactWriteItems) · expiring session items at no write cost (TTL) · DAX for microsecond reads of a read-heavy DynamoDB table (vs ElastiCache) |
| q23–q26 | 3 · 3.3 | stale data after writes with lazy loading: add TTL and write-through (Select TWO) · a shared session store for a stateless web fleet (ElastiCache) · Valkey/Redis replication group with Multi-AZ automatic failover for a cache that must survive an AZ loss · Memcached for a simple multithreaded cache that needs no persistence or replication |
| q27–q30 | 3 · 3.3 / 4 · 4.3 | fraud detection over relationships (Neptune) · a MongoDB-compatible managed document database (DocumentDB) · moving a Cassandra application without managing servers (Keyspaces) · a key-value workload at very high request rates on an expensive large RDS instance (DynamoDB; works-but-costs-more: a bigger RDS instance with read replicas) |

- [ ] **Step 2: Validate** — `verify_course.py --week 5 2>&1 | grep -i quiz` all ✔; `verify_course.py --banks | tail -6` no near-duplicates.
- [ ] **Step 3: Blind solve (main session)** — export with `_dev/blindsolve.py export`, an independent Opus agent answers from the blind file only and lists doubts, `compare`; fix every disagreement and real doubt through the implementer; a fresh Opus agent re-solves the rewritten questions.

---

### Task 5: M05 spec and project docs

**Files:** Create `course_project/milestones/M05.md`; modify `course_project/README.md`, `course_project/DEPLOY.md`.

- [ ] **Step 1: `M05.md`** — same shape as M03.md and M04.md, matching `course_project/tests/m05/` exactly: intro (the data tier: PostgreSQL for links and users, a Valkey/Redis cache for hot redirects, DynamoDB for daily click counts; the most expensive layer so far when deployed — RDS and ElastiCache bill by the hour, Multi-AZ doubles the database); Step 0 (`start_milestone.py 5`, `run_milestone.py 5`, cumulative); What the tests rely on (file `infra/data.yaml`; parameters; the three imports from M02; every logical id; the six exports); M05.1–M05.6 in plain words (the database and its subnet group; backups, Multi-AZ and deletion protection per environment; the app's access to the RDS-managed secret and why M01's statement does not cover it; the cache replication group per environment; the clicks table; the README "## Data tier" section with the cost number the tests compute with the course's DynamoDB model — state the workload exactly as the test does; exports, lint and the moto deploy with the skipped types); YAML examples allowed: the DBInstance credential lines (`ManageMasterUserPassword` with no password), the `!If [IsProd, …]` pattern on one property, and the AppDbSecretPolicy statement — never the whole template; a note that moto's CloudFormation skips ElastiCache and Secrets Manager and drops several database and table settings, which is why most checks read the template and the deploy test strips those types; Done when; Hints (why ManageMasterUserPassword; Port 5432; failover needs at least two cache nodes; DeletionPolicy Snapshot vs Retain; PITR and TTL; a lint-clean EngineVersion); Why this matters in the exam.
- [ ] **Step 2: `course_project/README.md`** — M05 built. **`DEPLOY.md`** — the data stack: deploy after network (and iam), `--stack-name shortly-data --parameter-overrides Prefix=shortly Env=lab --capabilities CAPABILITY_IAM` if the stack creates an IAM policy, the cost rows (RDS `db.t4g.micro` Single-AZ in lab, `db.m7g.large` Multi-AZ in prod; cache nodes; DynamoDB on-demand — illustrative, docs/facts.md), the delete order (`shortly-data` before `shortly-network`; the DB takes a final snapshot because of DeletionPolicy Snapshot — delete that snapshot by hand when you no longer need it; the clicks table has DeletionPolicy Retain: delete it by hand).

---

### Task 6: Course docs, full verification, report

**Files:** Modify `README.md` (week 05 row links to its README; Status: weeks 00–05 + M01–M05 built), `COURSE_FLOW.md` (week 05 section, `start_milestone.py 5`, `run_milestone.py 5`); generate `COVERAGE.md`; create `docs/specs/2026-10-12-aws-saa-plan-5-report.md`.

- [ ] **Step 1:** README and COURSE_FLOW edits (with plan 4's).
- [ ] **Step 2 (main session):** `verify_course.py --self-test`, `--week 5`, `--milestone 1` … `--milestone 5` one at a time, and `--coverage`; everything green.
- [ ] **Step 3:** report (as plan 4's); update memory (weeks 00–05 + M01–M05 built; week 06 next).

---
## Appendix A — verified code bundle (Task 1, weeks 04 and 05)

Every file below was written and run in a scratch copy of the course before this plan was final, then installed by the main session (LF line endings). Results in the real course on 2026-10-12: `_dev/tests` 581 passed; `week_04_storage/practice/exercises.py` and `week_05_databases_and_caching/practice/exercises.py` 0/10 passing, `--solutions` 10/10 (10 and 12 mutants caught); `verify_course.py --week 4` 38/38 and `--week 5` 40/40 once Tasks 3–4 of both plans landed; `--milestone 1` 10/10, `--milestone 2` 14/14, `--milestone 3` 18/18, `--milestone 4` 24/24 (20 mutants caught), `--milestone 5` 32/32 (28 mutants caught); the full run with `--coverage` 333/333. The six model modules, `prices.toml` and the two model test files were installed before the rest (the notes and demos needed them); they are listed for completeness. `course_project/solutions/m04/` and `m05/` also hold `infra/iam.yaml`, `infra/network.yaml`, `infra/compute.yaml`, `app/app.py`, `params/*.json` and `.gitignore`, byte-identical to `solutions/m03/` and not repeated here; `solutions/m05/infra/storage.yaml` is byte-identical to `solutions/m04/infra/storage.yaml`.

### `_harness/awslib/s3cost.py`

````python
"""s3cost — what an S3 storage class costs, and how a big upload is split.

This is the reference solution for week 04's drills 01 (storage-class cost) and 04 (multipart and
request rates): finish those drills before you read it.
Rules (docs/research/2026-10-12-storage-facts.md §1, §2, §12): the IA and Glacier Instant Retrieval
classes bill at least 128 KB per object; Standard-IA and One Zone-IA bill at least 30 days, Glacier
Instant and Flexible Retrieval 90, Deep Archive 180 (delete early and you still pay the rest);
everything except Standard charges per GB retrieved; a single PUT is at most 5 GB; a multipart part is
5 MiB to 5 GiB, at most 10,000 parts, object at most 50 TB; 3,500 write and 5,500 read requests per
second per prefix. Prices are the course's illustrative figures (prices.toml).
Left out on purpose: Intelligent-Tiering (its monitoring fee and tiers are week 11), request charges,
Expedited retrieval (it also bills per request) and the 40 KB per-object overhead of the two archive
classes (32 KB at the archive rate plus 8 KB at the Standard rate).
"""
from __future__ import annotations

import math

from . import prices

PRICES = prices.section("storage")
CLASSES = ("STANDARD", "STANDARD_IA", "ONEZONE_IA", "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE")  # GLACIER = Glacier Flexible Retrieval
MIN_DAYS = {"STANDARD": 0, "STANDARD_IA": 30, "ONEZONE_IA": 30, "GLACIER_IR": 90, "GLACIER": 90, "DEEP_ARCHIVE": 180}
MIN_OBJECT_KB = {"STANDARD": 0, "STANDARD_IA": 128, "ONEZONE_IA": 128, "GLACIER_IR": 128, "GLACIER": 0, "DEEP_ARCHIVE": 0}
MILLISECOND_ACCESS = {"STANDARD": True, "STANDARD_IA": True, "ONEZONE_IA": True, "GLACIER_IR": True,
                      "GLACIER": False, "DEEP_ARCHIVE": False}
SINGLE_AZ = {"ONEZONE_IA"}

_STORAGE_KEY = {"STANDARD": "s3_standard_per_gb_month", "STANDARD_IA": "s3_standard_ia_per_gb_month",
                "ONEZONE_IA": "s3_onezone_ia_per_gb_month", "GLACIER_IR": "s3_glacier_ir_per_gb_month",
                "GLACIER": "s3_glacier_flexible_per_gb_month", "DEEP_ARCHIVE": "s3_deep_archive_per_gb_month"}
_RETRIEVAL_KEY = {"STANDARD_IA": "s3_standard_ia_retrieval_per_gb", "ONEZONE_IA": "s3_onezone_ia_retrieval_per_gb",
                  "GLACIER_IR": "s3_glacier_ir_retrieval_per_gb"}
_ARCHIVE_RETRIEVAL_KEY = {("GLACIER", "standard"): "s3_glacier_flexible_standard_retrieval_per_gb",
                          ("GLACIER", "bulk"): "s3_glacier_flexible_bulk_retrieval_per_gb",
                          ("DEEP_ARCHIVE", "standard"): "s3_deep_archive_standard_retrieval_per_gb",
                          ("DEEP_ARCHIVE", "bulk"): "s3_deep_archive_bulk_retrieval_per_gb"}

KB_PER_GB = 1_048_576
MIB = 1024 ** 2
GIB = 1024 ** 3
SINGLE_PUT_MAX = 5 * GIB                # one PUT: up to 5 GB
MULTIPART_ADVICE = 100 * MIB            # "when your object size reaches 100 MB, consider multipart"
MAX_OBJECT_BYTES = 50 * 10 ** 12         # 50 TB (decimal; 10,000 parts of 5 GiB hold 48.8 TiB) since 2025-12-02, was 5 TB
MIN_PART_MIB = 5
MAX_PART_MIB = 5 * 1024                 # 5 GiB
MAX_PARTS = 10_000
GET_PER_PREFIX = 5_500
WRITE_PER_PREFIX = 3_500


def _retrieval_rate(storage_class: str, retrieval: str, price: dict) -> float:
    if retrieval not in ("standard", "bulk"):
        raise ValueError(f"unknown retrieval option {retrieval!r}: choose 'standard' or 'bulk' "
                         "(Expedited is not modelled: it also bills per request)")
    if storage_class == "STANDARD":
        return 0.0
    if storage_class in _RETRIEVAL_KEY:
        return price[_RETRIEVAL_KEY[storage_class]]
    return price[_ARCHIVE_RETRIEVAL_KEY[(storage_class, retrieval)]]


def storage_cost(storage_class: str, objects: int, object_kb: float, days: float, retrieved_gb: float = 0.0, *,
                 retrieval: str = "standard", price: dict = PRICES) -> float:
    """USD to keep `objects` objects of `object_kb` KB for `days` days, then retrieve `retrieved_gb` GB.

    Billable size is at least MIN_OBJECT_KB per object, billable days at least MIN_DAYS (1 GB = 1,048,576 KB,
    a month = 30 days). `retrieval` ("standard"/"bulk") only matters for GLACIER and DEEP_ARCHIVE.

    >>> storage_cost("STANDARD", 1024, 1_048_576, 30)      # 1 TB for a month
    23.55
    """
    if storage_class not in CLASSES:
        raise ValueError(f"unknown storage class {storage_class!r}: choose from {CLASSES}")
    if objects < 0 or object_kb < 0 or days < 0 or retrieved_gb < 0:
        raise ValueError("objects, object_kb, days and retrieved_gb must not be negative")
    rate = _retrieval_rate(storage_class, retrieval, price)
    billable_gb = objects * max(object_kb, MIN_OBJECT_KB[storage_class]) / KB_PER_GB
    billable_days = max(days, MIN_DAYS[storage_class])
    storage = billable_gb * price[_STORAGE_KEY[storage_class]] * billable_days / 30
    return round(storage + retrieved_gb * rate, 2)


def cheapest_class(objects: int, object_kb: float, days: float, retrieved_gb: float = 0.0, *,
                   millisecond_access: bool = True, single_az_ok: bool = False,
                   price: dict = PRICES) -> tuple[str, float]:
    """The cheapest allowed class and its cost. A tie keeps the earlier class in CLASSES.

    millisecond_access=True excludes GLACIER and DEEP_ARCHIVE; ONEZONE_IA needs single_az_ok=True.
    Intelligent-Tiering is not modelled (week 11).
    """
    best: tuple[str, float] | None = None
    for cls in CLASSES:
        if millisecond_access and not MILLISECOND_ACCESS[cls]:
            continue
        if cls in SINGLE_AZ and not single_az_ok:
            continue
        cost = storage_cost(cls, objects, object_kb, days, retrieved_gb, price=price)
        if best is None or cost < best[1]:
            best = (cls, cost)
    assert best is not None  # STANDARD is always allowed
    return best


def plan_parts(object_bytes: int, part_mib: int | None = None) -> dict:
    """Split an upload into parts: {"part_bytes", "parts", "last_part_bytes", "multipart"}.

    part_mib None picks the smallest whole-MiB part size that is at least 5 MiB and keeps parts <= 10,000.
    `multipart` is True above the 100 MB advice threshold (and always above the 5 GB single-PUT limit).

    >>> plan_parts(10 * 1024**2)["parts"]
    2
    """
    if object_bytes <= 0:
        raise ValueError("object_bytes must be positive")
    if object_bytes > MAX_OBJECT_BYTES:
        raise ValueError(f"{object_bytes} bytes is more than the 50 TB S3 maximum object size")
    if part_mib is None:
        part_mib = max(MIN_PART_MIB, math.ceil(object_bytes / (MAX_PARTS * MIB)))
    if not MIN_PART_MIB <= part_mib <= MAX_PART_MIB:
        raise ValueError(f"part size {part_mib} MiB is outside {MIN_PART_MIB} MiB to 5 GiB")
    part_bytes = part_mib * MIB
    parts = math.ceil(object_bytes / part_bytes)
    if parts > MAX_PARTS:
        raise ValueError(f"{parts} parts is more than the {MAX_PARTS} limit: use a bigger part size")
    return {"part_bytes": part_bytes, "parts": parts,
            "last_part_bytes": object_bytes - (parts - 1) * part_bytes,
            "multipart": object_bytes > SINGLE_PUT_MAX or object_bytes > MULTIPART_ADVICE}


def prefixes_needed(gets_per_second: float, puts_per_second: float) -> int:
    """Fewest prefixes that carry the load: 5,500 GET/HEAD and 3,500 PUT/COPY/POST/DELETE per second each.

    >>> prefixes_needed(11_000, 3_500)
    2
    """
    if gets_per_second < 0 or puts_per_second < 0:
        raise ValueError("request rates must not be negative")
    return max(math.ceil(gets_per_second / GET_PER_PREFIX), math.ceil(puts_per_second / WRITE_PER_PREFIX), 1)
````

### `_harness/awslib/lifecycle.py`

````python
"""lifecycle — validate S3 lifecycle rules and replay what they do to an object.

This is the reference solution for week 04's drill 02 (lifecycle rules): finish that drill before you
read it. Rules use the S3 API shape that boto3 put_bucket_lifecycle_configuration takes.
Facts (docs/research/2026-10-12-storage-facts.md §3): the transition waterfall (Deep Archive is
one-way); the two-step minimum (a later transition must come at least the previous class's minimum
storage duration after the earlier one: Glacier IR on day 4 means Deep Archive no earlier than day 94);
objects under 128 KB are not transitioned by default (since Sep 2024) unless the rule has an
object-size filter; expiration beats transition, and among transitions the furthest down the waterfall
wins; ExpiredObjectDeleteMarker and AbortIncompleteMultipartUpload cannot be used with a tag filter;
NewerNoncurrentVersions is 1 to 100, needs NoncurrentDays and a Filter element.
NOT enforced: the old "30 days in Standard before Standard-IA" rule: the research could not confirm it.
Lifecycle runs asynchronously in AWS: these functions give the state "once the rule has run".
"""
from __future__ import annotations

from . import s3cost

WATERFALL = ("STANDARD", "STANDARD_IA", "INTELLIGENT_TIERING", "ONEZONE_IA", "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE")
_ALLOWED_NEXT = {
    "STANDARD": WATERFALL[1:],
    "STANDARD_IA": ("INTELLIGENT_TIERING", "ONEZONE_IA", "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE"),
    "INTELLIGENT_TIERING": ("ONEZONE_IA", "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE"),
    "ONEZONE_IA": ("GLACIER", "DEEP_ARCHIVE"),
    "GLACIER_IR": ("GLACIER", "DEEP_ARCHIVE"),
    "GLACIER": ("DEEP_ARCHIVE",),
    "DEEP_ARCHIVE": (),
}
_MIN_DAYS = {**s3cost.MIN_DAYS, "INTELLIGENT_TIERING": 0}
DEFAULT_MIN_TRANSITION_BYTES = 128 * 1024
MAX_RULES = 1000
_ACTIONS = ("Transitions", "Expiration", "NoncurrentVersionTransitions", "NoncurrentVersionExpiration",
            "AbortIncompleteMultipartUpload")
_FILTER_KEYS = ("Prefix", "Tag", "ObjectSizeGreaterThan", "ObjectSizeLessThan", "And")


def _rid(rule: dict, index: int) -> str:
    return f"rule {rule.get('ID', index)!r}"


def _filter_parts(flt: dict) -> dict:
    """Flatten a Filter into {"Prefix", "Tags": {k: v}, "gt", "lt"} (missing parts are None / empty)."""
    src = flt.get("And", flt)
    tags = {t["Key"]: t["Value"] for t in src.get("Tags", [])}
    if "Tag" in src:
        tags[src["Tag"]["Key"]] = src["Tag"]["Value"]
    return {"Prefix": src.get("Prefix"), "Tags": tags,
            "gt": src.get("ObjectSizeGreaterThan"), "lt": src.get("ObjectSizeLessThan")}


def _matches(flt: dict, key: str, size_bytes: int, tags: dict) -> bool:
    p = _filter_parts(flt)
    if p["Prefix"] and not key.startswith(p["Prefix"]):
        return False
    if any(tags.get(k) != v for k, v in p["Tags"].items()):
        return False
    if p["gt"] is not None and not size_bytes > p["gt"]:
        return False
    if p["lt"] is not None and not size_bytes < p["lt"]:
        return False
    return True


def _has_size_filter(flt: dict) -> bool:
    p = _filter_parts(flt)
    return p["gt"] is not None or p["lt"] is not None


def _check_chain(who: str, steps: list[tuple[str, int]], label: str) -> None:
    """steps = [(storage class, day)] in listed order: waterfall, increasing days, two-step minimum."""
    prev_cls, prev_day = "STANDARD", None
    for cls, day in steps:
        if cls not in WATERFALL or cls == "STANDARD":
            raise ValueError(f"{who}: {cls!r} is not a valid transition target {WATERFALL[1:]}")
        if cls not in _ALLOWED_NEXT[prev_cls]:
            raise ValueError(f"{who}: waterfall violated: {prev_cls} cannot transition to {cls}"
                             f" (allowed: {_ALLOWED_NEXT[prev_cls] or 'nothing, Deep Archive is one-way'})")
        if prev_day is not None:
            if day <= prev_day:
                raise ValueError(f"{who}: {label} must increase: {cls} at {day} follows {prev_cls} at {prev_day}")
            earliest = prev_day + _MIN_DAYS[prev_cls]
            if day < earliest:
                raise ValueError(f"{who}: two-step minimum violated: {prev_cls} has a {_MIN_DAYS[prev_cls]}-day"
                                 f" minimum, so {cls} cannot come before {label} {earliest} (got {day})")
        prev_cls, prev_day = cls, day


def validate(rules: list[dict]) -> None:
    """Raise ValueError (naming the constraint that failed) if the rules would be rejected or are unsound."""
    if len(rules) > MAX_RULES:
        raise ValueError(f"{len(rules)} rules is more than the {MAX_RULES} rules per bucket limit")
    seen: set[str] = set()
    for i, rule in enumerate(rules):
        who = _rid(rule, i)
        rid = rule.get("ID")
        if rid is not None:
            if len(rid) > 255:
                raise ValueError(f"{who}: ID is longer than 255 characters")
            if rid in seen:
                raise ValueError(f"{who}: duplicate rule ID")
            seen.add(rid)
        if rule.get("Status") not in ("Enabled", "Disabled"):
            raise ValueError(f"{who}: Status must be 'Enabled' or 'Disabled', got {rule.get('Status')!r}")
        if not any(rule.get(a) for a in _ACTIONS):
            raise ValueError(f"{who}: rule has no action (Transitions, Expiration, Noncurrent..., Abort...)")
        flt = rule.get("Filter", {})
        top = [k for k in _FILTER_KEYS if k in flt]
        if len(top) > 1:
            raise ValueError(f"{who}: Filter has {top} side by side: combine them inside 'And'")
        uses_tags = bool(_filter_parts(flt)["Tags"])

        trans = rule.get("Transitions", [])
        _check_chain(who, [(t["StorageClass"], t["Days"]) for t in trans], "day")
        exp = rule.get("Expiration")
        if exp is not None:
            if ("Days" in exp) == ("ExpiredObjectDeleteMarker" in exp):
                raise ValueError(f"{who}: Expiration needs exactly one of Days or ExpiredObjectDeleteMarker")
            if "Days" in exp and any(exp["Days"] <= t["Days"] for t in trans):
                raise ValueError(f"{who}: Expiration Days {exp['Days']} must be later than every transition")
            if "ExpiredObjectDeleteMarker" in exp and uses_tags:
                raise ValueError(f"{who}: ExpiredObjectDeleteMarker cannot be used with a tag filter")
        if rule.get("AbortIncompleteMultipartUpload") and uses_tags:
            raise ValueError(f"{who}: AbortIncompleteMultipartUpload cannot be used with a tag filter")

        ntrans = rule.get("NoncurrentVersionTransitions", [])
        _check_chain(who, [(t["StorageClass"], t["NoncurrentDays"]) for t in ntrans], "NoncurrentDays")
        nexp = rule.get("NoncurrentVersionExpiration")
        if nexp is not None:
            if "NewerNoncurrentVersions" in nexp:
                if "NoncurrentDays" not in nexp:
                    raise ValueError(f"{who}: NewerNoncurrentVersions needs NoncurrentDays")
                if not 1 <= nexp["NewerNoncurrentVersions"] <= 100:
                    raise ValueError(f"{who}: NewerNoncurrentVersions must be 1 to 100")
                if "Filter" not in rule:
                    raise ValueError(f"{who}: NewerNoncurrentVersions needs a Filter element (use {{}} for all)")
            if "NoncurrentDays" in nexp and any(nexp["NoncurrentDays"] <= t["NoncurrentDays"] for t in ntrans):
                raise ValueError(f"{who}: NoncurrentVersionExpiration must be later than every noncurrent transition")


def _applicable(rules, key, size_bytes, tags):
    for rule in rules:
        if rule.get("Status") == "Enabled" and _matches(rule.get("Filter", {}), key, size_bytes, tags):
            yield rule, (size_bytes >= DEFAULT_MIN_TRANSITION_BYTES or _has_size_filter(rule.get("Filter", {})))


def _furthest(classes: list[str]) -> str:
    return max(classes, key=WATERFALL.index, default="STANDARD")


def current_class(rules: list[dict], key: str, age_days: int, size_bytes: int, tags: dict | None = None) -> str:
    """Storage class of a current object `age_days` old once the rules have run, or "EXPIRED".

    Objects under 128 KB skip transitions unless the rule has an object-size filter.
    """
    tags = tags or {}
    reached = []
    for rule, may_transition in _applicable(rules, key, size_bytes, tags):
        exp = rule.get("Expiration", {})
        if "Days" in exp and age_days >= exp["Days"]:
            return "EXPIRED"
        if may_transition:
            reached += [t["StorageClass"] for t in rule.get("Transitions", []) if age_days >= t["Days"]]
    return _furthest(reached)


def noncurrent_fate(rules: list[dict], key: str, days_noncurrent: int, newer_noncurrent: int = 0,
                    size_bytes: int = 1 << 20, tags: dict | None = None) -> str:
    """Class of a noncurrent version, or "DELETED", `days_noncurrent` days after it became noncurrent."""
    tags = tags or {}
    reached = []
    for rule, may_transition in _applicable(rules, key, size_bytes, tags):
        nexp = rule.get("NoncurrentVersionExpiration")
        if nexp and days_noncurrent >= nexp.get("NoncurrentDays", 0) and (
                "NewerNoncurrentVersions" not in nexp or newer_noncurrent >= nexp["NewerNoncurrentVersions"]):
            return "DELETED"
        if may_transition:
            reached += [t["StorageClass"] for t in rule.get("NoncurrentVersionTransitions", [])
                        if days_noncurrent >= t["NoncurrentDays"]]
    return _furthest(reached)
````

### `_harness/awslib/ebs.py`

````python
"""ebs — EBS volume limits, cost and choice.

This is the reference solution for week 04's drill 03 (EBS volume types): finish that drill before you
read it. Facts (docs/research/2026-10-12-storage-facts.md §7, §12): gp3 is 1 GiB to 64 TiB with 3,000
IOPS and 125 MiB/s free at any size, up to 80,000 IOPS (500 per GiB) and 2,000 MiB/s (0.25 MiB/s per
IOPS) since Sep 2025; gp2 is 3 IOPS per GiB, 100 to 16,000; io2 Block Express is 4 GiB to 64 TiB, up to
256,000 IOPS (1,000 per GiB) and 4,000 MiB/s; st1/sc1 are 125 GiB to 16 TiB HDDs (500 / 250 IOPS and
MiB/s), never bootable; only io1/io2 support Multi-Attach. Prices are illustrative (prices.toml).
Left out: io1, the io2 IOPS price above 64,000 (the research does not give the third tier), snapshots.
"""
from __future__ import annotations

from . import prices

PRICES = prices.section("storage")

GIB_PER_TIB = 1024
GP3_BASELINE_IOPS, GP3_BASELINE_THROUGHPUT = 3000, 125
GP3_MAX_IOPS, GP3_MAX_THROUGHPUT = 80_000, 2000
GP3_IOPS_PER_GIB = 500
GP3_THROUGHPUT_PER_IOPS = 0.25
GP2_IOPS_PER_GIB, GP2_MIN_IOPS, GP2_MAX_IOPS = 3, 100, 16_000
IO2_MAX_IOPS, IO2_IOPS_PER_GIB, IO2_MAX_THROUGHPUT = 256_000, 1000, 4000
IO2_PRICED_IOPS = 64_000                 # the research prices io2 IOPS only up to here
HDD_MAX = {"st1": {"iops": 500, "throughput": 500}, "sc1": {"iops": 250, "throughput": 250}}
SIZE_GIB = {"gp3": (1, 64 * GIB_PER_TIB), "gp2": (1, 16 * GIB_PER_TIB), "io2": (4, 64 * GIB_PER_TIB),
            "st1": (125, 16 * GIB_PER_TIB), "sc1": (125, 16 * GIB_PER_TIB)}
VOLUME_TYPES = tuple(SIZE_GIB)
BOOTABLE = {"gp2", "gp3", "io1", "io2"}
MULTI_ATTACH = {"io1", "io2"}


def _check_size(volume_type: str, size_gib: int) -> None:
    if volume_type not in SIZE_GIB:
        raise ValueError(f"unknown volume type {volume_type!r}: choose from {VOLUME_TYPES}")
    low, high = SIZE_GIB[volume_type]
    if not low <= size_gib <= high:
        raise ValueError(f"{volume_type} volumes are {low} GiB to {high} GiB, got {size_gib}")


def gp2_iops(size_gib: int) -> int:
    """gp2 baseline IOPS: 3 per GiB, at least 100, at most 16,000 (reached at 5,334 GiB).

    >>> gp2_iops(10), gp2_iops(1000), gp2_iops(6000)
    (100, 3000, 16000)
    """
    _check_size("gp2", size_gib)
    return max(GP2_MIN_IOPS, min(GP2_MAX_IOPS, GP2_IOPS_PER_GIB * size_gib))


def gp3_config(size_gib: int, iops: int | None = None, throughput: int | None = None) -> dict:
    """Validate a gp3 request; None means the free baseline. Returns {"iops", "throughput"}.

    Above the baseline: IOPS at most 500 per GiB and 80,000; throughput at most 0.25 MiB/s per
    provisioned IOPS and 2,000 MiB/s. Below the baseline is not possible.

    >>> gp3_config(100)
    {'iops': 3000, 'throughput': 125}
    """
    _check_size("gp3", size_gib)
    iops = GP3_BASELINE_IOPS if iops is None else iops
    throughput = GP3_BASELINE_THROUGHPUT if throughput is None else throughput
    if iops < GP3_BASELINE_IOPS or throughput < GP3_BASELINE_THROUGHPUT:
        raise ValueError(f"gp3 includes {GP3_BASELINE_IOPS} IOPS and {GP3_BASELINE_THROUGHPUT} MiB/s: you cannot provision less")
    if iops > GP3_MAX_IOPS:
        raise ValueError(f"gp3 tops out at {GP3_MAX_IOPS} IOPS, got {iops}")
    if iops > GP3_BASELINE_IOPS and iops > GP3_IOPS_PER_GIB * size_gib:
        raise ValueError(f"gp3 allows {GP3_IOPS_PER_GIB} IOPS per GiB: {size_gib} GiB gives at most {GP3_IOPS_PER_GIB * size_gib}")
    if throughput > GP3_MAX_THROUGHPUT:
        raise ValueError(f"gp3 tops out at {GP3_MAX_THROUGHPUT} MiB/s, got {throughput}")
    if throughput > GP3_BASELINE_THROUGHPUT and throughput > GP3_THROUGHPUT_PER_IOPS * iops:
        raise ValueError(f"gp3 allows {GP3_THROUGHPUT_PER_IOPS} MiB/s per IOPS: {iops} IOPS gives at most {GP3_THROUGHPUT_PER_IOPS * iops:g}")
    return {"iops": iops, "throughput": throughput}


def _io2_iops_cost(iops: int, price: dict) -> float:
    if iops > IO2_PRICED_IOPS:
        raise ValueError(f"io2 IOPS above {IO2_PRICED_IOPS} have no price in the course's research")
    first = min(iops, 32_000)
    return first * price["ebs_io2_per_iops_month_first_32k"] + (iops - first) * price["ebs_io2_per_iops_month_32k_to_64k"]


def monthly_cost(volume_type: str, size_gib: int, iops: int | None = None, throughput: int | None = None,
                 price: dict = PRICES) -> float:
    """Monthly USD for one volume (no snapshots). gp3 pays only for IOPS above 3,000 and MiB/s above 125;
    io2 needs `iops`; gp2, st1 and sc1 are size only.

    >>> monthly_cost("gp3", 100)
    8.0
    """
    _check_size(volume_type, size_gib)
    if volume_type == "gp3":
        cfg = gp3_config(size_gib, iops, throughput)
        cost = (size_gib * price["ebs_gp3_per_gb_month"]
                + (cfg["iops"] - GP3_BASELINE_IOPS) * price["ebs_gp3_per_iops_month"]
                + (cfg["throughput"] - GP3_BASELINE_THROUGHPUT) * price["ebs_gp3_per_mibps_month"])
    elif volume_type == "io2":
        if iops is None or iops <= 0:
            raise ValueError("io2 is billed per provisioned IOPS: pass iops")
        if iops > IO2_MAX_IOPS or iops > IO2_IOPS_PER_GIB * size_gib:
            raise ValueError(f"io2 allows {IO2_IOPS_PER_GIB} IOPS per GiB and {IO2_MAX_IOPS} in total: {size_gib} GiB, {iops} IOPS")
        if throughput is not None and throughput > IO2_MAX_THROUGHPUT:
            raise ValueError(f"io2 tops out at {IO2_MAX_THROUGHPUT} MiB/s")
        cost = size_gib * price["ebs_io2_per_gb_month"] + _io2_iops_cost(iops, price)
    else:
        if iops is not None or throughput is not None:
            raise ValueError(f"{volume_type} performance is not provisioned: leave iops and throughput out")
        cost = size_gib * price[f"ebs_{volume_type}_per_gb_month"]
    return round(cost, 2)


def choose_volume(iops: int = 0, throughput_mibs: int = 0, *, boot: bool = False, multi_attach: bool = False,
                  sequential: bool = False, rarely_accessed: bool = False) -> str:
    """Cheapest volume type that meets the need.

    Rules, in order: Multi-Attach needs io2 (and cannot be a boot volume); IOPS above gp3's 80,000 or
    throughput above 2,000 MiB/s needs io2; a sequential, non-boot workload gets sc1 if it is rarely
    accessed and fits sc1 (250 IOPS, 250 MiB/s), else st1 if it fits st1 (500, 500); everything else gp3.
    HDDs are never chosen for a boot volume. ValueError if even io2 cannot do it.
    """
    if iops < 0 or throughput_mibs < 0:
        raise ValueError("iops and throughput_mibs must not be negative")
    if multi_attach and boot:
        raise ValueError("a Multi-Attach volume cannot be a boot volume")
    if iops > IO2_MAX_IOPS or throughput_mibs > IO2_MAX_THROUGHPUT:
        raise ValueError(f"no EBS volume gives more than {IO2_MAX_IOPS} IOPS or {IO2_MAX_THROUGHPUT} MiB/s")
    if multi_attach or iops > GP3_MAX_IOPS or throughput_mibs > GP3_MAX_THROUGHPUT:
        return "io2"
    if sequential and not boot:
        for kind, wanted in (("sc1", rarely_accessed), ("st1", True)):
            if wanted and iops <= HDD_MAX[kind]["iops"] and throughput_mibs <= HDD_MAX[kind]["throughput"]:
                return kind
    return "gp3"
````

### `_harness/awslib/dynamo.py`

````python
"""dynamo - DynamoDB capacity units and cost: provisioned vs on-demand.

This is the reference solution for week 05's drills 01-02: finish those drills before you read it.
Rules (docs/research/2026-10-12-database-facts.md section 3): an item is at most 400 KB; one read unit
reads up to 4 KB (strongly consistent 1, eventually consistent 0.5, transactional 2); one write unit
writes up to 1 KB (standard 1, transactional 2); item sizes round UP to the next 4 KB / 1 KB.
Provisioned capacity bills every hour whether you use it or not; on-demand bills per request.
Prices come from prices.toml [database] (illustrative). The "first 25 WCU/RCU free" provisioned
allowance is ignored here.
"""
from __future__ import annotations

import math

from . import prices

PRICES = prices.section("database")
MAX_ITEM_KB = 400
READ_UNIT_KB, WRITE_UNIT_KB = 4, 1
READ_FACTOR = {"eventual": 0.5, "strong": 1.0, "transactional": 2.0}
HOURS_PER_MONTH = 730


def _check_size(item_kb: float) -> None:
    if not 0 < item_kb <= MAX_ITEM_KB:
        raise ValueError(f"item size must be above 0 and at most {MAX_ITEM_KB} KB, got {item_kb}")


def read_units(item_kb: float, consistency: str = "eventual") -> float:
    """Read units for one read: 4 KB blocks (rounded up) x 0.5 / 1 / 2.

    >>> read_units(4.1, "strong")
    2.0
    >>> read_units(8)
    1.0
    """
    _check_size(item_kb)
    if consistency not in READ_FACTOR:
        raise ValueError(f"consistency must be one of {sorted(READ_FACTOR)}, got {consistency!r}")
    return math.ceil(item_kb / READ_UNIT_KB) * READ_FACTOR[consistency]


def write_units(item_kb: float, transactional: bool = False) -> int:
    """Write units for one write: 1 KB blocks (rounded up) x 1 (standard) or 2 (transactional).

    >>> write_units(1.5)
    2
    >>> write_units(1.5, transactional=True)
    4
    """
    _check_size(item_kb)
    return math.ceil(item_kb / WRITE_UNIT_KB) * (2 if transactional else 1)


def provisioned_capacity(reads_per_second: float, writes_per_second: float, item_kb: float,
                         consistency: str = "eventual", transactional_writes: bool = False) -> tuple[int, int]:
    """(RCU, WCU) to provision: ceil(reads x read units), ceil(writes x write units).

    >>> provisioned_capacity(100, 50, 6)
    (100, 300)
    """
    if reads_per_second < 0 or writes_per_second < 0:
        raise ValueError("request rates cannot be negative")
    rcu = math.ceil(reads_per_second * read_units(item_kb, consistency))
    wcu = math.ceil(writes_per_second * write_units(item_kb, transactional_writes))
    return rcu, wcu


def monthly_cost_on_demand(reads_per_month: float, writes_per_month: float, item_kb: float,
                           consistency: str = "eventual", transactional_writes: bool = False,
                           price: dict = PRICES) -> float:
    """On-demand cost: request units x price per million. Storage is not included.

    >>> monthly_cost_on_demand(1_000_000, 1_000_000, 1)
    0.6875
    """
    if reads_per_month < 0 or writes_per_month < 0:
        raise ValueError("request counts cannot be negative")
    read_cost = reads_per_month * read_units(item_kb, consistency) / 1e6 * price["dynamodb_on_demand_per_million_reads"]
    write_cost = writes_per_month * write_units(item_kb, transactional_writes) / 1e6 * price["dynamodb_on_demand_per_million_writes"]
    return round(read_cost + write_cost, 4)


def monthly_cost_provisioned(rcu: float, wcu: float, hours: float = HOURS_PER_MONTH, price: dict = PRICES) -> float:
    """Provisioned cost: you pay for every provisioned unit-hour, used or not.

    >>> monthly_cost_provisioned(100, 100)
    56.94
    """
    if rcu < 0 or wcu < 0 or hours < 0:
        raise ValueError("capacity and hours cannot be negative")
    return round(hours * (rcu * price["dynamodb_rcu_hour"] + wcu * price["dynamodb_wcu_hour"]), 4)


def break_even_utilisation(price: dict = PRICES) -> dict:
    """Average fraction of provisioned capacity you must use for provisioned to cost the same as on-demand.

    One unit-hour of provisioned capacity could serve 3,600 units of requests, which on-demand would
    price at 3,600 x (price per million / 1,000,000). Returns {"writes": f, "reads": f}, each rounded
    to 4 decimal places; below that utilisation on-demand is cheaper, above it provisioned is.

    >>> break_even_utilisation()
    {'writes': 0.2889, 'reads': 0.2889}
    """
    w = price["dynamodb_wcu_hour"] / (3600 * price["dynamodb_on_demand_per_million_writes"] / 1e6)
    r = price["dynamodb_rcu_hour"] / (3600 * price["dynamodb_on_demand_per_million_reads"] / 1e6)
    return {"writes": round(w, 4), "reads": round(r, 4)}
````

### `_harness/awslib/caching.py`

````python
"""caching - lazy loading (cache-aside) vs write-through, with TTL and stale reads.

This is the reference solution for week 05's drill 06: finish that drill before you read it.
Strategies follow AWS's ElastiCache caching strategies page (docs/research/2026-10-12-database-facts.md
section 4). Lazy: a miss reads the database and fills the cache; a write touches only the database,
so the cached copy can go stale until it expires. Write-through: a write updates the database AND the
cache, so cached values are never stale, at the cost of caching data that may never be read.
"""
from __future__ import annotations

STRATEGIES = ("lazy", "write-through")


def simulate(events, strategy: str, ttl: float | None = None) -> dict:
    """Replay (time_s, op, key[, value]) events, op "read" or "write", times non-decreasing.

    The database starts empty; reading a key never written returns None and still costs a database
    read on a miss. An entry cached at t expires at t + ttl (None = never); a read at exactly
    t + ttl is a miss. A stale read is a hit whose value differs from the database's current value.

    >>> r = simulate([(0, "write", "k", 1), (1, "read", "k")], "write-through")
    >>> (r["hits"], r["misses"], r["db_writes"], r["cache_writes"])
    (1, 0, 1, 1)
    """
    if strategy not in STRATEGIES:
        raise ValueError(f"strategy must be one of {STRATEGIES}, got {strategy!r}")
    if ttl is not None and ttl <= 0:
        raise ValueError("ttl must be positive or None")
    db: dict = {}
    cache: dict = {}  # key -> (value, expires_at or None)
    out = {"hits": 0, "misses": 0, "db_reads": 0, "db_writes": 0, "stale_reads": 0, "cache_writes": 0}
    last = None

    def put(key, value, now):
        cache[key] = (value, None if ttl is None else now + ttl)
        out["cache_writes"] += 1

    for event in events:
        if len(event) not in (3, 4):
            raise ValueError(f"event must be (time, op, key[, value]), got {event!r}")
        now, op, key = event[0], event[1], event[2]
        if last is not None and now < last:
            raise ValueError(f"event times go backwards: {now} after {last}")
        last = now
        if op == "write":
            if len(event) != 4:
                raise ValueError("a write event needs a value")
            db[key] = event[3]
            out["db_writes"] += 1
            if strategy == "write-through":
                put(key, event[3], now)
        elif op == "read":
            entry = cache.get(key)
            if entry is not None and (entry[1] is None or now < entry[1]):
                out["hits"] += 1
                if entry[0] != db.get(key):
                    out["stale_reads"] += 1
            else:
                out["misses"] += 1
                out["db_reads"] += 1
                put(key, db.get(key), now)
        else:
            raise ValueError(f"op must be 'read' or 'write', got {op!r}")
    return out
````

### `_harness/awslib/dbmath.py`

````python
"""dbmath - connection maths: how many connections a Lambda-style workload opens, and RDS Proxy sizing.

This is the reference solution for week 05's drill 07: finish that drill before you read it.
Concurrency by Little's law (requests in flight = rate x duration). max_connections defaults come
from docs/research/2026-10-12-database-facts.md section 1 (RDS CHAP_Limits): MySQL
DBInstanceClassMemory/12582880, PostgreSQL LEAST(DBInstanceClassMemory/9531392, 5000).
The research gives no default for RDS Proxy MaxConnectionsPercent, so proxy_pool_size requires it.
"""
from __future__ import annotations

import math

ENGINES = ("mysql", "postgres")


def _positive(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")


def peak_concurrency(requests_per_second: float, avg_duration_s: float) -> int:
    """Little's law: ceil(rps x duration).

    >>> peak_concurrency(500, 0.2)
    100
    """
    _positive("requests_per_second", requests_per_second)
    _positive("avg_duration_s", avg_duration_s)
    return math.ceil(round(requests_per_second * avg_duration_s, 9))


def connections_without_proxy(concurrency: int, connections_per_invocation: int = 1) -> int:
    """Every concurrent invocation opens its own connection(s) straight to the database.

    >>> connections_without_proxy(100, 2)
    200
    """
    _positive("concurrency", concurrency)
    _positive("connections_per_invocation", connections_per_invocation)
    return concurrency * connections_per_invocation


def needs_proxy(concurrency: int, max_connections: int, connections_per_invocation: int = 1,
                headroom: float = 0.0) -> bool:
    """True when connections exceed max_connections x (1 - headroom).

    >>> needs_proxy(100, 90)
    True
    """
    _positive("max_connections", max_connections)
    if not 0 <= headroom < 1:
        raise ValueError(f"headroom must be from 0 up to (not including) 1, got {headroom}")
    return connections_without_proxy(concurrency, connections_per_invocation) > max_connections * (1 - headroom)


def proxy_pool_size(max_connections: int, max_connections_percent: float) -> int:
    """Connections the proxy may open to the database: floor(max x percent / 100).

    >>> proxy_pool_size(90, 50)
    45
    """
    _positive("max_connections", max_connections)
    if not 0 < max_connections_percent <= 100:
        raise ValueError(f"max_connections_percent must be above 0 and at most 100, got {max_connections_percent}")
    return math.floor(max_connections * max_connections_percent / 100)


def default_max_connections(engine: str, memory_gib: float) -> int:
    """RDS default max_connections, using memory_gib x 2^30 as DBInstanceClassMemory.

    The real DBInstanceClassMemory is a little lower than the nominal memory (the OS and RDS
    management take a share), so real defaults are somewhat below these figures.

    >>> default_max_connections("postgres", 1)
    112
    """
    if engine not in ENGINES:
        raise ValueError(f"engine must be one of {ENGINES}, got {engine!r}")
    _positive("memory_gib", memory_gib)
    memory = memory_gib * 2**30
    if engine == "mysql":
        return int(memory // 12582880)
    return int(min(memory // 9531392, 5000))
````

### `_harness/awslib/prices.toml`

````toml
# Illustrative us-east-1 list prices for the course's cost drills — NOT a quote.
# Check https://calculator.aws/ for real numbers. The exam tests cost reasoning, not prices.
[meta]
region = "us-east-1"
as_of = "2026-10"

[data_transfer]
ingress_per_gb = 0.0               # into AWS from the internet
egress_internet_per_gb = 0.09      # out to the internet (first 10 TB/month tier)
inter_az_per_gb_each_way = 0.01    # between AZs in one Region: charged out AND in
inter_region_per_gb = 0.02         # between Regions (sender pays)

[[s3_standard_tiers]]              # S3 Standard storage, per GB-month
up_to_gb = 51200                   # first 50 TB
per_gb_month = 0.023

[[s3_standard_tiers]]
up_to_gb = 512000                  # next 450 TB
per_gb_month = 0.022

[[s3_standard_tiers]]              # over 500 TB (no upper bound)
per_gb_month = 0.021

[vpc]                                       # us-east-1, illustrative (docs/research/2026-10-10-vpc-facts.md)
nat_gateway_per_hour = 0.045                # per NAT gateway
nat_gateway_per_gb = 0.045                  # data processed by a NAT gateway
gateway_endpoint_per_gb = 0.0               # S3 / DynamoDB gateway endpoints are free
interface_endpoint_per_hour_per_az = 0.01   # PrivateLink interface endpoint, each AZ
interface_endpoint_per_gb = 0.01
transit_gateway_attachment_per_hour = 0.05
transit_gateway_per_gb = 0.02
vpn_connection_per_hour = 0.05
public_ipv4_per_hour = 0.005

[ec2]                                       # us-east-1 Linux On-Demand, illustrative (docs/research/2026-10-11-compute-facts.md)
t4g_micro_per_hour = 0.0084
t4g_small_per_hour = 0.0168
t4g_medium_per_hour = 0.0336
t3_micro_per_hour = 0.0104
m7g_large_per_hour = 0.0816
m7i_large_per_hour = 0.1008
c7g_large_per_hour = 0.0725
c7i_large_per_hour = 0.08925
r7g_large_per_hour = 0.1071
compute_savings_plan_discount = 0.31        # course example: AWS average 1-year Convertible RI discount (the SP FAQ: Compute SP "up to 66% (just like Convertible RIs)")
standard_ri_discount = 0.40                 # AWS average 1-year Standard RI discount ("up to 72%")
spot_discount = 0.70                        # course example; AWS says "up to 90%"
alb_per_hour = 0.0225
alb_per_lcu_hour = 0.008
nlb_per_hour = 0.0225
nlb_per_nlcu_hour = 0.006

[storage]                                   # us-east-1, illustrative (docs/research/2026-10-12-storage-facts.md section 12)
s3_standard_per_gb_month = 0.023            # first 50 TB tier, flat here
s3_standard_ia_per_gb_month = 0.0125
s3_onezone_ia_per_gb_month = 0.01
s3_glacier_ir_per_gb_month = 0.004
s3_glacier_flexible_per_gb_month = 0.0036
s3_deep_archive_per_gb_month = 0.00099      # Glacier product page, Region not named: illustrative
s3_standard_ia_retrieval_per_gb = 0.01
s3_onezone_ia_retrieval_per_gb = 0.01
s3_glacier_ir_retrieval_per_gb = 0.03
s3_glacier_flexible_standard_retrieval_per_gb = 0.01
s3_glacier_flexible_bulk_retrieval_per_gb = 0.0
s3_deep_archive_standard_retrieval_per_gb = 0.02
s3_deep_archive_bulk_retrieval_per_gb = 0.0025
ebs_gp3_per_gb_month = 0.08
ebs_gp3_per_iops_month = 0.005              # per provisioned IOPS above the free 3,000
ebs_gp3_per_mibps_month = 0.06              # per provisioned MiB/s above the free 125 (the price page says MB/s)
ebs_gp2_per_gb_month = 0.10
ebs_io2_per_gb_month = 0.125
ebs_io2_per_iops_month_first_32k = 0.065    # IOPS 1 to 32,000
ebs_io2_per_iops_month_32k_to_64k = 0.046   # IOPS 32,001 to 64,000 (third tier is not in the research)
ebs_st1_per_gb_month = 0.045
ebs_sc1_per_gb_month = 0.015
ebs_snapshot_per_gb_month = 0.05
ebs_snapshot_archive_per_gb_month = 0.0125
efs_standard_per_gb_month = 0.30
efs_ia_per_gb_month = 0.025
efs_archive_per_gb_month = 0.008

[database]                                  # us-east-1 On-Demand, illustrative (docs/research/2026-10-12-database-facts.md section 6, from the AWS Price List files)
dynamodb_on_demand_per_million_writes = 0.625
dynamodb_on_demand_per_million_reads = 0.125
dynamodb_wcu_hour = 0.00065                 # provisioned; the first 25 WCU are free (the course models ignore that)
dynamodb_rcu_hour = 0.00013                 # provisioned; the first 25 RCU are free (the course models ignore that)
dynamodb_storage_per_gb_month = 0.25        # Standard, after the first 25 GB free
dynamodb_pitr_per_gb_month = 0.20
rds_pg_t4g_micro_per_hour = 0.016
rds_pg_t4g_micro_multi_az_per_hour = 0.032
rds_pg_m7g_large_per_hour = 0.168
rds_pg_m7g_large_multi_az_per_hour = 0.337
rds_gp3_per_gb_month = 0.115                # Single-AZ; Multi-AZ DB instance is double
aurora_serverless_v2_per_acu_hour = 0.12    # Standard (I/O-Optimized is 0.16)
rds_proxy_per_vcpu_hour = 0.015
elasticache_t4g_micro_per_hour = 0.0128     # Valkey (Redis OSS is 0.016)
elasticache_m7g_large_per_hour = 0.1264     # Valkey (Redis OSS is 0.158)
````

### `_harness/awslib/cfn.py`

````python
"""cfn — load, lint and inspect CloudFormation templates.

Shared by drills, milestone tests (copied into the learner's repo as tests/_course/cfn.py) and
verify_course.py. Templates may use short-form tags (!Ref, !Sub, !GetAtt …); loading turns them
into the long form ({"Ref": …}, {"Fn::Sub": …}) as plain dicts and lists.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import tempfile
from importlib.metadata import version
from pathlib import Path
from typing import Any

CACHE_DIR = Path(tempfile.gettempdir()) / "saa-course-lintcache"
DEFAULT_PSEUDO = {
    "AWS::AccountId": "111122223333",
    "AWS::Region": "us-east-1",
    "AWS::Partition": "aws",
    "AWS::URLSuffix": "amazonaws.com",
    "AWS::StackName": "shortly-stack",
    "AWS::NoValue": None,
}
_SUB_VAR = re.compile(r"\$\{([^}]+)\}")


class TemplateError(ValueError):
    """A template could not be loaded or rendered."""


def load_template_text(text: str) -> dict:
    from cfnlint.decode import decode_str

    template, errors = decode_str(text)
    if errors or template is None:
        problems = "; ".join(f"line {e.linenumber}: {e.message}" for e in errors) or "empty template"
        raise TemplateError(problems)
    return json.loads(json.dumps(template))


def load_template(path) -> dict:
    return load_template_text(Path(path).read_text(encoding="utf-8"))


def _run_cfnlint(text: str) -> list[dict]:
    import cfnlint.api

    return [{"rule": m.rule.id, "line": m.linenumber, "message": m.message} for m in cfnlint.api.lint(text)]


def lint_text(text: str) -> list[dict]:
    """cfn-lint findings for a template, cached by (cfn-lint version, text) because one run costs ≈ 2 s."""
    key = hashlib.sha256(f"{version('cfn-lint')}\0{text}".encode("utf-8")).hexdigest()
    cached = CACHE_DIR / f"{key}.json"
    try:
        return json.loads(cached.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    findings = _run_cfnlint(text)
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cached.write_text(json.dumps(findings), encoding="utf-8")
    except OSError:
        pass
    return findings


def lint_template(path) -> list[dict]:
    return lint_text(Path(path).read_text(encoding="utf-8"))


def errors_only(findings: list[dict]) -> list[dict]:
    return [f for f in findings if f["rule"].startswith("E")]


def resources(template: dict, type_: str | None = None) -> dict[str, dict]:
    found = template.get("Resources") or {}
    return {name: res for name, res in found.items() if type_ is None or res.get("Type") == type_}


def _lookup(name: str, params: dict, pseudo: dict):
    if name in params:
        return params[name]
    if name in pseudo:
        return pseudo[name]
    raise TemplateError(f"unknown parameter {name}")


class _NoValue:
    """Marker for {"Ref": "AWS::NoValue"}: the property or list item is dropped."""

    def __repr__(self):
        return "AWS::NoValue"


NOVALUE = _NoValue()
AZ_LETTERS = "abcdef"


def parameter_values(template: dict, params: dict | None = None) -> dict:
    """The template's parameter Defaults, overridden by `params`."""
    defaults = {name: spec["Default"] for name, spec in (template.get("Parameters") or {}).items()
                if isinstance(spec, dict) and "Default" in spec}
    return {**defaults, **(params or {})}


def evaluate_conditions(template: dict, params: dict | None = None, pseudo: dict | None = None) -> dict[str, bool]:
    """Every entry of the template's Conditions section, evaluated with the given parameters.
    Supports Fn::Equals, Fn::Not, Fn::And, Fn::Or and {"Condition": name}."""
    params = parameter_values(template, params)
    pseudo = {**DEFAULT_PSEUDO, **(pseudo or {})}
    raw = template.get("Conditions") or {}
    done: dict[str, bool] = {}

    def value(name: str, stack: tuple = ()) -> bool:
        if name in done:
            return done[name]
        if name not in raw:
            raise TemplateError(f"unknown condition {name}")
        if name in stack:
            raise TemplateError(f"condition {name} refers to itself")
        done[name] = test(raw[name], stack + (name,))
        return done[name]

    def test(expr, stack) -> bool:
        if not isinstance(expr, dict) or len(expr) != 1:
            raise TemplateError(f"bad condition expression {expr!r}")
        (key, arg), = expr.items()
        if key == "Condition":
            return value(arg, stack)
        if key == "Fn::Equals":
            left, right = (render(a, params, pseudo, {}) for a in arg)
            return str(left) == str(right)
        if key == "Fn::Not":
            return not test(arg[0], stack)
        if key == "Fn::And":
            return all(test(a, stack) for a in arg)
        if key == "Fn::Or":
            return any(test(a, stack) for a in arg)
        raise TemplateError(f"unsupported condition function {key}")

    return {name: value(name) for name in raw}


def render(value: Any, params: dict | None = None, pseudo: dict | None = None, conditions: dict | None = None,
           mappings: dict | None = None) -> Any:
    """Resolve intrinsic functions with test parameter values:
    Ref, Fn::Sub, Fn::Join, Fn::Split, Fn::GetAtt, Fn::If, Fn::Select, Fn::GetAZs, Fn::Cidr,
    Fn::ImportValue, Fn::Base64, Fn::FindInMap (looks up the template's Mappings, which active_resources and
    the conftest `outputs` fixture pass in; a missing map or key is a TemplateError).
    A Ref to a resource renders as its logical id; Fn::GetAtt as "Logical.Attr"; Fn::ImportValue as
    "import:<name>"; Fn::GetAZs as the Region's names with letters a–f. Fn::If needs `conditions`
    (see evaluate_conditions). Fn::Split gives the list of pieces of a rendered string (a rendered
    list is an error). Fn::Base64 renders as its rendered input, NOT encoded, so a test can read the
    user data. {"Ref": "AWS::NoValue"} removes the property or list item."""
    global _MAPPINGS
    saved, _MAPPINGS = _MAPPINGS, mappings or {}
    try:
        result = _render(value, params or {}, {**DEFAULT_PSEUDO, **(pseudo or {})}, conditions)
    finally:
        _MAPPINGS = saved
    return None if result is NOVALUE else result


_MAPPINGS: dict = {}


def _render(value, params, pseudo, conditions):
    if isinstance(value, list):
        items = [_render(v, params, pseudo, conditions) for v in value]
        return [i for i in items if i is not NOVALUE]
    if not isinstance(value, dict):
        return value
    if len(value) == 1:
        (key, arg), = value.items()
        if key == "Ref":
            if arg == "AWS::NoValue":
                return NOVALUE
            if arg in params or arg in pseudo:
                return _lookup(arg, params, pseudo)
            return arg
        if key == "Fn::GetAtt":
            parts = arg.split(".", 1) if isinstance(arg, str) else arg
            return f"{parts[0]}.{parts[1]}"
        if key == "Fn::Join":
            sep, items = arg
            rendered = _render(items, params, pseudo, conditions)
            return sep.join(str(i) for i in rendered)
        if key == "Fn::Split":
            delimiter, source = arg
            rendered = _render(source, params, pseudo, conditions)
            if not isinstance(rendered, str):
                raise TemplateError(f"Fn::Split needs a string to split, got {rendered!r}")
            return rendered.split(delimiter)
        if key == "Fn::Base64":
            return _render(arg, params, pseudo, conditions)
        if key == "Fn::Select":
            index, items = arg
            rendered = _render(items, params, pseudo, conditions)
            position = int(_render(index, params, pseudo, conditions))
            if not isinstance(rendered, list) or not 0 <= position < len(rendered):
                raise TemplateError(f"Fn::Select index {position} is outside {rendered!r}")
            return rendered[position]
        if key == "Fn::GetAZs":
            region = _render(arg, params, pseudo, conditions) or pseudo["AWS::Region"]
            return [f"{region}{letter}" for letter in AZ_LETTERS]
        if key == "Fn::Cidr":
            block, count, bits = (_render(a, params, pseudo, conditions) for a in arg)
            network = ipaddress.ip_network(str(block))
            new_prefix = network.max_prefixlen - int(bits)
            subnets = network.subnets(new_prefix=new_prefix)
            return [str(next(subnets)) for _ in range(int(count))]
        if key == "Fn::FindInMap":
            name, first, second = (_render(a, params, pseudo, conditions) for a in arg)
            try:
                return _MAPPINGS[name][first][second]
            except (KeyError, TypeError):
                raise TemplateError(f"Fn::FindInMap: no value for {name} / {first} / {second} in Mappings") from None
        if key == "Fn::ImportValue":
            return f"import:{_render(arg, params, pseudo, conditions)}"
        if key == "Fn::If":
            if conditions is None:
                raise TemplateError("Fn::If needs condition values (use evaluate_conditions)")
            name, if_true, if_false = arg
            if name not in conditions:
                raise TemplateError(f"Fn::If uses unknown condition {name}")
            return _render(if_true if conditions[name] else if_false, params, pseudo, conditions)
        if key == "Fn::Sub":
            text, local = (arg, {}) if isinstance(arg, str) else (arg[0], arg[1])
            local = {k: _render(v, params, pseudo, conditions) for k, v in local.items()}

            def replace(match):
                name = match.group(1)
                if name.startswith("!"):
                    return "${" + name[1:] + "}"
                if name in local:
                    return str(local[name])
                if "." in name:
                    return name
                if name in params or name in pseudo:
                    return str(_lookup(name, params, pseudo))
                raise TemplateError(f"Fn::Sub uses ${{{name}}} but no parameter or pseudo parameter {name} exists")
            return _SUB_VAR.sub(replace, text)
    rendered = {k: _render(v, params, pseudo, conditions) for k, v in value.items()}
    return {k: v for k, v in rendered.items() if v is not NOVALUE}


def active_resources(template: dict, params: dict | None = None, pseudo: dict | None = None) -> dict[str, dict]:
    """Resources that exist for these parameters (their Condition, if any, is true), rendered."""
    params = parameter_values(template, params)
    conditions = evaluate_conditions(template, params, pseudo)
    found = {}
    for name, res in resources(template).items():
        condition = res.get("Condition")
        if condition is not None and not conditions.get(condition, False):
            continue
        found[name] = render(res, params, pseudo, conditions, template.get("Mappings"))
    return found


def inline_functions(template: dict, functions: set[str], params: dict | None = None, pseudo: dict | None = None) -> dict:
    """A copy of the template where every call to one of `functions` (e.g. {"Fn::Cidr"}) is replaced
    by its rendered value — for tools such as moto that cannot evaluate those functions."""
    params = parameter_values(template, params)
    conditions = evaluate_conditions(template, params, pseudo)

    def walk(value):
        if isinstance(value, list):
            return [walk(v) for v in value]
        if isinstance(value, dict):
            if len(value) == 1 and next(iter(value)) in functions:
                return render(value, params, pseudo, conditions, template.get("Mappings"))
            return {k: walk(v) for k, v in value.items()}
        return value
    return walk(template)


def _role(template: dict, logical_id: str) -> dict:
    res = resources(template).get(logical_id)
    if res is None or res.get("Type") != "AWS::IAM::Role":
        raise TemplateError(f"no AWS::IAM::Role named {logical_id}")
    return res.get("Properties") or {}


def role_policies(template: dict, logical_id: str, params=None, pseudo=None) -> list[dict]:
    """Every identity policy document attached to a role: inline Policies plus in-template
    AWS::IAM::ManagedPolicy resources referenced from ManagedPolicyArns (AWS-managed ARNs are
    skipped — their contents are not available offline)."""
    props = _role(template, logical_id)
    docs = [p["PolicyDocument"] for p in props.get("Policies") or []]
    for arn in props.get("ManagedPolicyArns") or []:
        if isinstance(arn, dict) and "Ref" in arn:
            target = resources(template).get(arn["Ref"])
            if target and target.get("Type") == "AWS::IAM::ManagedPolicy":
                docs.append(target["Properties"]["PolicyDocument"])
    params = parameter_values(template, params)
    return render(docs, params, pseudo, evaluate_conditions(template, params, pseudo), template.get("Mappings"))


def trust_policy(template: dict, logical_id: str, params=None, pseudo=None) -> dict:
    document = _role(template, logical_id).get("AssumeRolePolicyDocument") or {}
    params = parameter_values(template, params)
    return render(document, params, pseudo, evaluate_conditions(template, params, pseudo), template.get("Mappings"))


def _refs(value) -> set[str]:
    """Logical ids a template fragment points at: Ref, Fn::GetAtt, ${Name} / ${Name.Attr} in Fn::Sub, DependsOn."""
    found: set[str] = set()
    if isinstance(value, list):
        for item in value:
            found |= _refs(item)
    elif isinstance(value, dict):
        for key, arg in value.items():
            if key == "Ref" and isinstance(arg, str):
                found.add(arg)
            elif key == "Fn::GetAtt":
                found.add((arg.split(".", 1)[0] if isinstance(arg, str) else arg[0]))
            elif key == "Fn::Sub":
                text = arg if isinstance(arg, str) else arg[0]
                local = set() if isinstance(arg, str) else set(arg[1])
                found |= {m.split(".", 1)[0] for m in _SUB_VAR.findall(text) if not m.startswith("!")} - local
                if not isinstance(arg, str):
                    found |= _refs(arg[1])
            else:
                found |= _refs(arg)
    return found


def _getatt_name(arg) -> str:
    return arg if isinstance(arg, str) else ".".join(str(p) for p in arg)


def for_moto(template: dict, skip_types, getatt_values: dict | None = None) -> dict:
    """A copy of the template that moto can create, for types moto skips or attributes it lacks:
    - every resource whose Type is in `skip_types` is removed (also from DependsOn lists);
    - every Output that refers to a removed resource, or to an attribute listed in `getatt_values`, is removed;
    - every remaining Fn::GetAtt listed in `getatt_values` ("Logical.Attr.Path" -> literal) is replaced by that literal.
    A resource that still refers to a removed resource is a TemplateError naming both, so the test author
    sees it instead of a confusing crash inside moto."""
    skip_types = set(skip_types or ())
    getatt_values = dict(getatt_values or {})
    out = json.loads(json.dumps(template))
    removed = {name for name, res in (out.get("Resources") or {}).items() if res.get("Type") in skip_types}
    for name in removed:
        del out["Resources"][name]

    def replace(value):
        if isinstance(value, list):
            return [replace(v) for v in value]
        if isinstance(value, dict):
            if len(value) == 1 and next(iter(value)) == "Fn::GetAtt":
                key = _getatt_name(value["Fn::GetAtt"])
                if key in getatt_values:
                    return getatt_values[key]
            return {k: replace(v) for k, v in value.items()}
        return value

    def uses_listed_attribute(value) -> bool:
        if isinstance(value, list):
            return any(uses_listed_attribute(v) for v in value)
        if isinstance(value, dict):
            if len(value) == 1 and next(iter(value)) == "Fn::GetAtt" and _getatt_name(value["Fn::GetAtt"]) in getatt_values:
                return True
            return any(uses_listed_attribute(v) for v in value.values())
        return False

    for name, res in out.get("Resources", {}).items():
        depends = res.get("DependsOn")
        if isinstance(depends, list):
            res["DependsOn"] = [d for d in depends if d not in removed]
        elif depends in removed:
            del res["DependsOn"]
        bad = sorted(_refs(res) & removed)
        if bad:
            raise TemplateError(f"resource {name} still refers to {', '.join(bad)}, which for_moto removed "
                                f"(type in skip_types); remove it too or stop referring to it")
        out["Resources"][name] = replace(res)
    outputs = out.get("Outputs") or {}
    for key in list(outputs):
        if _refs(outputs[key]) & removed or uses_listed_attribute(outputs[key]):
            del outputs[key]
    if "Outputs" in out and not outputs:
        del out["Outputs"]
    return out
````

### `_harness/awslib/policy_eval.py`

````python
"""policy_eval — a small, readable model of AWS IAM policy evaluation.

This is the reference solution for week 01's drills 01–04: finish those drills before you read it.

The model (from the official IAM "Policy evaluation logic" page, simplified where noted):
  • A statement applies to a request when its Action/NotAction, Resource/NotResource and Condition
    all match — and, for resource-based and trust policies, its Principal/NotPrincipal.
  • Within a set of policies: any applicable Deny → "ExplicitDeny"; otherwise any applicable
    Allow → "Allow"; otherwise "ImplicitDeny" (the default).
  • evaluate() combines policy types: an explicit Deny anywhere wins; every SCP level must allow;
    the identity policy OR a same-account resource-based policy must allow (cross-account: BOTH
    must); a permissions boundary and a session policy, when present, must also allow.
  • Simplifications: no policy variables (${aws:username}); no Date operators; no resource control
    policies (RCPs); a permissions boundary also limits same-account resource-policy grants (in AWS
    it does not when the resource policy names an IAM user or a role session directly).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from ipaddress import ip_address, ip_network

ALLOW, EXPLICIT_DENY, IMPLICIT_DENY = "Allow", "ExplicitDeny", "ImplicitDeny"


@dataclass(frozen=True)
class Request:
    principal: str                 # caller ARN, e.g. arn:aws:sts::111122223333:assumed-role/app/i-0abc
    action: str                    # e.g. "s3:GetObject"
    resource: str                  # resource ARN, or "*" for actions without resources
    context: dict = field(default_factory=dict)   # condition keys, e.g. {"aws:SecureTransport": True}


def as_list(value) -> list:
    if value is None:
        return []
    return list(value) if isinstance(value, (list, tuple, set)) else [value]


def statements(policy: dict) -> list[dict]:
    found = (policy or {}).get("Statement", [])
    return [found] if isinstance(found, dict) else list(found)


def account_of(arn: str) -> str | None:
    parts = str(arn).split(":", 5)
    if len(parts) == 6 and parts[0] == "arn" and re.fullmatch(r"\d{12}", parts[4]):
        return parts[4]
    return None


def _glob(pattern: str, text: str, ignore_case: bool) -> bool:
    regex = "".join(".*" if c == "*" else "." if c == "?" else re.escape(c) for c in pattern)
    flags = re.DOTALL | (re.IGNORECASE if ignore_case else 0)
    return re.fullmatch(regex, text, flags) is not None


def action_matches(pattern: str, action: str) -> bool:
    """Actions are case-insensitive; * matches any characters, ? one character."""
    return _glob(pattern, action, ignore_case=True)


def resource_matches(pattern: str, arn: str) -> bool:
    """Resources are case-sensitive and compared segment by segment (a wildcard never spans ':')."""
    if pattern == "*":
        return True
    p_parts, a_parts = pattern.split(":", 5), arn.split(":", 5)
    if len(p_parts) != 6 or len(a_parts) != 6:
        return _glob(pattern, arn, ignore_case=False)
    return all(_glob(p, a, ignore_case=False) for p, a in zip(p_parts, a_parts))


_ROLE = re.compile(r"arn:[^:]+:iam::(\d{12}):role/(?:.*/)?([^/]+)")
_SESSION = re.compile(r"arn:[^:]+:sts::(\d{12}):assumed-role/([^/]+)/.+")
_ROOT = re.compile(r"arn:[^:]+:iam::(\d{12}):root")


def principal_matches(principal, caller_arn: str) -> bool:
    if principal == "*":
        return True
    if isinstance(principal, str):
        principal = {"AWS": principal}
    for kind, values in principal.items():
        for value in as_list(values):
            if value == "*":
                return True
            if kind != "AWS":
                if value == caller_arn:
                    return True
                continue
            root = _ROOT.fullmatch(value)
            account = value if re.fullmatch(r"\d{12}", value) else (root.group(1) if root else None)
            if account is not None:
                if account_of(caller_arn) == account:
                    return True
                continue
            if value == caller_arn:
                return True
            role, session = _ROLE.fullmatch(value), _SESSION.fullmatch(caller_arn)
            if role and session and role.groups() == session.groups():
                return True
    return False


# ── conditions ──────────────────────────────────────────────────────

_NEGATED = {"StringNotEquals": "StringEquals", "StringNotEqualsIgnoreCase": "StringEqualsIgnoreCase",
            "StringNotLike": "StringLike", "NumericNotEquals": "NumericEquals",
            "NotIpAddress": "IpAddress", "ArnNotEquals": "ArnEquals", "ArnNotLike": "ArnLike"}
_NUMERIC = {"NumericEquals": lambda x, y: x == y, "NumericLessThan": lambda x, y: x < y,
            "NumericLessThanEquals": lambda x, y: x <= y, "NumericGreaterThan": lambda x, y: x > y,
            "NumericGreaterThanEquals": lambda x, y: x >= y}
_POSITIVE = {"StringEquals", "StringEqualsIgnoreCase", "StringLike", "Bool", "IpAddress",
             "ArnEquals", "ArnLike", *_NUMERIC}
SUPPORTED = _POSITIVE | set(_NEGATED) | {"Null"}


def _parse_operator(name: str):
    qualifier = None
    for prefix, label in (("ForAnyValue:", "any"), ("ForAllValues:", "all")):
        if name.startswith(prefix):
            qualifier, name = label, name[len(prefix):]
    if_exists = name.endswith("IfExists") and name != "Null"
    if if_exists:
        name = name[: -len("IfExists")]
    if name not in SUPPORTED:
        raise ValueError(f"unsupported condition operator {name}")
    return qualifier, name, if_exists


def _value_matches(op: str, actual, expected) -> bool:
    a, e = str(actual), str(expected)
    if op == "StringEquals":
        return a == e
    if op == "StringEqualsIgnoreCase":
        return a.casefold() == e.casefold()
    if op == "StringLike":
        return _glob(e, a, ignore_case=False)
    if op in _NUMERIC:
        return _NUMERIC[op](float(a), float(e))
    if op == "Bool":
        return a.lower() == e.lower()
    if op == "IpAddress":
        return ip_address(a) in ip_network(e, strict=False)
    if op in ("ArnEquals", "ArnLike"):
        return resource_matches(e, a)
    raise ValueError(f"unsupported condition operator {op}")


def _one(op: str, actual, expected_values: list) -> bool:
    if op in _NEGATED:
        return not any(_value_matches(_NEGATED[op], actual, e) for e in expected_values)
    return any(_value_matches(op, actual, e) for e in expected_values)


def _lookup(context: dict, key: str):
    for name, value in context.items():
        if name.lower() == key.lower():
            return value
    return None


def condition_matches(condition: dict | None, context: dict) -> bool:
    """Every operator and every key in the block must hold (AND); several values for one key are
    alternatives (OR). Missing keys: false for positive operators, true for negated ones and for
    ...IfExists; ForAllValues passes on an empty or missing set, ForAnyValue fails."""
    for operator, block in (condition or {}).items():
        qualifier, op, if_exists = _parse_operator(operator)
        for key, expected in block.items():
            expected_values = as_list(expected)
            actual = _lookup(context, key)
            present = actual is not None and actual != []
            if op == "Null":
                if (str(expected_values[0]).lower() == "true") == present:
                    return False
                continue
            if not present:
                if qualifier == "any":
                    return False
                if if_exists or qualifier == "all" or op in _NEGATED:
                    continue
                return False
            actual_values = as_list(actual)
            check = all if qualifier == "all" else any
            if not check(_one(op, a, expected_values) for a in actual_values):
                return False
    return True


# ── statements and decisions ────────────────────────────────────────


def statement_applies(statement: dict, request: Request, *, check_principal: bool = False) -> bool:
    if check_principal:
        if "Principal" in statement:
            if not principal_matches(statement["Principal"], request.principal):
                return False
        elif "NotPrincipal" in statement:
            if principal_matches(statement["NotPrincipal"], request.principal):
                return False
        else:
            return False
    if "Action" in statement:
        ok = any(action_matches(p, request.action) for p in as_list(statement["Action"]))
    elif "NotAction" in statement:
        ok = not any(action_matches(p, request.action) for p in as_list(statement["NotAction"]))
    else:
        return False
    if not ok:
        return False
    if "Resource" in statement:
        ok = any(resource_matches(p, request.resource) for p in as_list(statement["Resource"]))
    elif "NotResource" in statement:
        ok = not any(resource_matches(p, request.resource) for p in as_list(statement["NotResource"]))
    else:
        ok = check_principal  # trust policies have no Resource; identity policies must
    return ok and condition_matches(statement.get("Condition"), request.context)


def _decide(policies, request: Request, check_principal: bool = False) -> str:
    allowed = False
    for policy in policies:
        for st in statements(policy):
            if statement_applies(st, request, check_principal=check_principal):
                if st.get("Effect") == "Deny":
                    return EXPLICIT_DENY
                if st.get("Effect") == "Allow":
                    allowed = True
    return ALLOW if allowed else IMPLICIT_DENY


def evaluate_policies(policies: list[dict], request: Request) -> str:
    """Identity-based policies only."""
    return _decide(policies, request)


def evaluate(request: Request, *, identity=(), resource_policy=None, scps=None, boundary=None,
             session=None, resource_account=None) -> str:
    identity = list(identity)
    every = identity + [p for p in (boundary, session) if p] + [p for level in (scps or []) for p in level]
    if _decide(every, request) == EXPLICIT_DENY:
        return EXPLICIT_DENY
    if resource_policy and _decide([resource_policy], request, check_principal=True) == EXPLICIT_DENY:
        return EXPLICIT_DENY
    for level in scps or []:
        if _decide(level, request) != ALLOW:
            return IMPLICIT_DENY
    identity_ok = _decide(identity, request) == ALLOW
    resource_ok = bool(resource_policy) and _decide([resource_policy], request, check_principal=True) == ALLOW
    caller_account = account_of(request.principal)
    target_account = resource_account or account_of(request.resource) or caller_account
    granted = (identity_ok and resource_ok) if caller_account != target_account else (identity_ok or resource_ok)
    if not granted:
        return IMPLICIT_DENY
    for limit in (boundary, session):
        if limit is not None and _decide([limit], request) != ALLOW:
            return IMPLICIT_DENY
    return ALLOW


def decide_resource_policy(policy: dict, request: Request) -> str:
    """Evaluate ONE resource-based policy on its own, matching the Principal element: "Allow",
    "ExplicitDeny" or "ImplicitDeny". Use it for callers that have no account, such as the service
    principal logdelivery.elasticloadbalancing.amazonaws.com (give it as request.principal; it matches
    a {"Service": ...} principal exactly), and to see what a bucket policy grants without any
    identity policy. For the full same-account / cross-account combination use evaluate()."""
    return _decide([policy], request, check_principal=True)


def evaluate_trust(trust_policy: dict, caller_arn: str, context: dict | None = None) -> bool:
    """May caller_arn call sts:AssumeRole on the role with this trust policy?"""
    request = Request(principal=caller_arn, action="sts:AssumeRole", resource="*", context=context or {})
    return _decide([trust_policy], request, check_principal=True) == ALLOW
````

### `_harness/labclean.py`

````python
"""labclean — remove what a lab created in YOUR AWS account, and nothing else.

Every lab tags what it creates with  saa-course = lab . A week's lab/cleanup.py calls main() with
the kinds of resources that lab creates. Without --yes it only lists (dry run).

    python lab/cleanup.py                    list what would be deleted (us-east-1 or $AWS_DEFAULT_REGION)
    python lab/cleanup.py --region eu-west-1 --profile saa-lab
    python lab/cleanup.py --yes              actually delete

IAM is global: IAM kinds are listed whatever --region you give.
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Callable

TAG_KEY, TAG_VALUE = "saa-course", "lab"


@dataclass
class Found:
    kind: str
    name: str
    region: str
    delete: Callable[[], None]


def _error_code(exc) -> str:
    response = getattr(exc, "response", None) or {}
    return response.get("Error", {}).get("Code", type(exc).__name__)


class Blocked(Exception):
    """A tagged resource that must be left in place on purpose (it is held by something we must not touch,
    or by something this script cannot remove). main() prints the message and counts it as a problem."""


def _tagged(tags) -> bool:
    return any(t.get("Key") == TAG_KEY and t.get("Value") == TAG_VALUE for t in tags or [])


# ── S3 ──────────────────────────────────────────────────────────────


def find_s3_buckets(session, region: str) -> list[Found]:
    from botocore.exceptions import ClientError

    s3 = session.client("s3", region_name=region)
    found = []
    for bucket in s3.list_buckets().get("Buckets", []):
        name = bucket["Name"]
        try:
            location = s3.get_bucket_location(Bucket=name).get("LocationConstraint") or "us-east-1"
            if location != region:
                continue
            tags = s3.get_bucket_tagging(Bucket=name).get("TagSet", [])
        except ClientError:
            continue  # untagged (NoSuchTagSet) or not ours to read
        if _tagged(tags):
            found.append(Found("s3_buckets", name, region, lambda name=name: _delete_bucket(s3, name)))
    return found


def _delete_bucket(s3, name: str) -> None:
    from botocore.exceptions import ClientError

    # An unfinished multipart upload keeps its parts (and its bill) and does not show up as an object.
    for page in s3.get_paginator("list_multipart_uploads").paginate(Bucket=name):
        for upload in page.get("Uploads", []):
            s3.abort_multipart_upload(Bucket=name, Key=upload["Key"], UploadId=upload["UploadId"])
    errors = []
    for page in s3.get_paginator("list_object_versions").paginate(Bucket=name):
        doomed = [{"Key": v["Key"], "VersionId": v["VersionId"]} for v in page.get("Versions", []) + page.get("DeleteMarkers", [])]
        for start in range(0, len(doomed), 1000):
            result = s3.delete_objects(Bucket=name, Delete={"Objects": doomed[start:start + 1000], "Quiet": True})
            errors += result.get("Errors", [])
    if errors:
        try:
            locked = s3.get_object_lock_configuration(Bucket=name)["ObjectLockConfiguration"].get("ObjectLockEnabled") == "Enabled"
        except ClientError:
            locked = False
        first = f"{errors[0].get('Code')}: {errors[0].get('Message')}"
        if locked:
            raise Blocked(f"bucket {name} has Object Lock and {len(errors)} object version(s) are under retention or legal hold, "
                          "which this script cannot (and must not) override. Wait for the retention to expire or remove the "
                          "hold in the console, then run the cleanup again.")
        raise Blocked(f"{len(errors)} object version(s) in bucket {name} could not be deleted ({first})")
    s3.delete_bucket(Bucket=name)


# ── IAM (global) ────────────────────────────────────────────────────


def find_iam_roles(session, region: str) -> list[Found]:
    iam = session.client("iam")
    found = []
    for page in iam.get_paginator("list_roles").paginate():
        for role in page["Roles"]:
            name = role["RoleName"]
            if _tagged(iam.list_role_tags(RoleName=name).get("Tags")):
                found.append(Found("iam_roles", name, "global", lambda name=name: _delete_role(iam, name)))
    return found


def _delete_role(iam, name: str) -> None:
    for profile in iam.list_instance_profiles_for_role(RoleName=name)["InstanceProfiles"]:
        iam.remove_role_from_instance_profile(InstanceProfileName=profile["InstanceProfileName"], RoleName=name)
        if profile["InstanceProfileName"] == name:
            iam.delete_instance_profile(InstanceProfileName=name)
    for policy in iam.list_role_policies(RoleName=name)["PolicyNames"]:
        iam.delete_role_policy(RoleName=name, PolicyName=policy)
    for policy in iam.list_attached_role_policies(RoleName=name)["AttachedPolicies"]:
        iam.detach_role_policy(RoleName=name, PolicyArn=policy["PolicyArn"])
    iam.delete_role(RoleName=name)


def find_iam_policies(session, region: str) -> list[Found]:
    iam = session.client("iam")
    found = []
    for page in iam.get_paginator("list_policies").paginate(Scope="Local"):
        for policy in page["Policies"]:
            arn = policy["Arn"]
            if _tagged(iam.list_policy_tags(PolicyArn=arn).get("Tags")):
                found.append(Found("iam_policies", policy["PolicyName"], "global", lambda arn=arn: _delete_policy(iam, arn)))
    return found


def _delete_policy(iam, arn: str) -> None:
    entities = iam.list_entities_for_policy(PolicyArn=arn)
    for role in entities.get("PolicyRoles", []):
        iam.detach_role_policy(RoleName=role["RoleName"], PolicyArn=arn)
    for user in entities.get("PolicyUsers", []):
        iam.detach_user_policy(UserName=user["UserName"], PolicyArn=arn)
    for group in entities.get("PolicyGroups", []):
        iam.detach_group_policy(GroupName=group["GroupName"], PolicyArn=arn)
    for version in iam.list_policy_versions(PolicyArn=arn)["Versions"]:
        if not version["IsDefaultVersion"]:
            iam.delete_policy_version(PolicyArn=arn, VersionId=version["VersionId"])
    iam.delete_policy(PolicyArn=arn)


def find_iam_users(session, region: str) -> list[Found]:
    iam = session.client("iam")
    found = []
    for page in iam.get_paginator("list_users").paginate():
        for user in page["Users"]:
            name = user["UserName"]
            if _tagged(iam.list_user_tags(UserName=name).get("Tags")):
                found.append(Found("iam_users", name, "global", lambda name=name: _delete_user(iam, name)))
    return found


def _delete_user(iam, name: str) -> None:
    from botocore.exceptions import ClientError

    for key in iam.list_access_keys(UserName=name)["AccessKeyMetadata"]:
        iam.delete_access_key(UserName=name, AccessKeyId=key["AccessKeyId"])
    try:
        iam.delete_login_profile(UserName=name)
    except ClientError as exc:
        if _error_code(exc) != "NoSuchEntity":
            raise
    for policy in iam.list_user_policies(UserName=name)["PolicyNames"]:
        iam.delete_user_policy(UserName=name, PolicyName=policy)
    for policy in iam.list_attached_user_policies(UserName=name)["AttachedPolicies"]:
        iam.detach_user_policy(UserName=name, PolicyArn=policy["PolicyArn"])
    for group in iam.list_groups_for_user(UserName=name)["Groups"]:
        iam.remove_user_from_group(UserName=name, GroupName=group["GroupName"])
    for device in iam.list_mfa_devices(UserName=name)["MFADevices"]:
        iam.deactivate_mfa_device(UserName=name, SerialNumber=device["SerialNumber"])
    iam.delete_user(UserName=name)


# ── EC2 and VPC (Regional) ──────────────────────────────────────────

WAIT_SECONDS = 5          # pause between state checks while AWS deletes something (tests set 0)
WAIT_ATTEMPTS = 120       # give up after WAIT_SECONDS × WAIT_ATTEMPTS
TAG_FILTER = [{"Name": f"tag:{TAG_KEY}", "Values": [TAG_VALUE]}]


def _wait_until(check, what: str) -> None:
    import time

    for _ in range(WAIT_ATTEMPTS):
        if check():
            return
        time.sleep(WAIT_SECONDS)
    raise TimeoutError(f"gave up waiting for {what}")


def _name(tags, fallback: str) -> str:
    names = [t["Value"] for t in tags or [] if t.get("Key") == "Name"]
    return f"{fallback} ({names[0]})" if names else fallback


def find_ec2_instances(session, region: str) -> list[Found]:
    ec2 = session.client("ec2", region_name=region)
    found = []
    filters = TAG_FILTER + [{"Name": "instance-state-name", "Values": ["pending", "running", "stopping", "stopped"]}]
    for page in ec2.get_paginator("describe_instances").paginate(Filters=filters):
        for reservation in page["Reservations"]:
            for instance in reservation["Instances"]:
                if not _tagged(instance.get("Tags")):  # never trust the server-side filter alone
                    continue
                iid = instance["InstanceId"]
                found.append(Found("ec2_instances", _name(instance.get("Tags"), iid), region,
                                   lambda iid=iid: _terminate(ec2, iid)))
    return found


def _terminate(ec2, instance_id: str) -> None:
    ec2.terminate_instances(InstanceIds=[instance_id])

    def gone():
        state = ec2.describe_instances(InstanceIds=[instance_id])["Reservations"][0]["Instances"][0]["State"]["Name"]
        return state == "terminated"
    _wait_until(gone, f"instance {instance_id} to terminate")


def _delete_nat(ec2, nat_id: str) -> None:
    ec2.delete_nat_gateway(NatGatewayId=nat_id)

    def gone():
        gateways = ec2.describe_nat_gateways(NatGatewayIds=[nat_id])["NatGateways"]
        return not gateways or gateways[0]["State"] in ("deleted", "failed")
    _wait_until(gone, f"NAT gateway {nat_id} to be deleted")


def find_nat_gateways(session, region: str) -> list[Found]:
    ec2 = session.client("ec2", region_name=region)
    found = []
    for nat in ec2.describe_nat_gateways(Filters=TAG_FILTER)["NatGateways"]:
        if nat["State"] in ("pending", "available") and _tagged(nat.get("Tags")):
            nat_id = nat["NatGatewayId"]
            found.append(Found("nat_gateways", _name(nat.get("Tags"), nat_id), region,
                               lambda nat_id=nat_id: _delete_nat(ec2, nat_id)))
    return found


def find_elastic_ips(session, region: str) -> list[Found]:
    ec2 = session.client("ec2", region_name=region)
    found = []
    for address in ec2.describe_addresses(Filters=TAG_FILTER)["Addresses"]:
        if not _tagged(address.get("Tags")):
            continue
        allocation = address["AllocationId"]
        found.append(Found("elastic_ips", f"{address.get('PublicIp', allocation)} ({allocation})", region,
                           lambda address=address: _release(ec2, address)))
    return found


def _release(ec2, address: dict) -> None:
    if address.get("AssociationId"):
        ec2.disassociate_address(AssociationId=address["AssociationId"])
    ec2.release_address(AllocationId=address["AllocationId"])


def find_vpcs(session, region: str) -> list[Found]:
    ec2 = session.client("ec2", region_name=region)
    return [Found("vpcs", _name(vpc.get("Tags"), vpc["VpcId"]), region, lambda vpc_id=vpc["VpcId"]: _delete_vpc(ec2, vpc_id))
            for vpc in ec2.describe_vpcs(Filters=TAG_FILTER)["Vpcs"] if _tagged(vpc.get("Tags"))]


def _delete_vpc(ec2, vpc_id: str) -> None:
    """Delete a VPC and everything inside it, in the order AWS accepts. Instances still running
    inside it are NOT terminated (unless tagged and listed earlier), so AWS refuses the VPC and the
    error is reported — nothing untagged is ever destroyed."""
    in_vpc = [{"Name": "vpc-id", "Values": [vpc_id]}]
    for nat in ec2.describe_nat_gateways(Filters=in_vpc)["NatGateways"]:
        if nat["State"] in ("pending", "available"):
            _delete_nat(ec2, nat["NatGatewayId"])
    endpoints = [e["VpcEndpointId"] for e in ec2.describe_vpc_endpoints(Filters=in_vpc)["VpcEndpoints"]
                 if e["State"].lower() not in ("deleted", "deleting")]
    if endpoints:
        ec2.delete_vpc_endpoints(VpcEndpointIds=endpoints)
    for igw in ec2.describe_internet_gateways(Filters=[{"Name": "attachment.vpc-id", "Values": [vpc_id]}])["InternetGateways"]:
        ec2.detach_internet_gateway(InternetGatewayId=igw["InternetGatewayId"], VpcId=vpc_id)
        ec2.delete_internet_gateway(InternetGatewayId=igw["InternetGatewayId"])
    for subnet in ec2.describe_subnets(Filters=in_vpc)["Subnets"]:
        ec2.delete_subnet(SubnetId=subnet["SubnetId"])
    for table in ec2.describe_route_tables(Filters=in_vpc)["RouteTables"]:
        if any(a.get("Main") for a in table.get("Associations", [])):
            continue
        for association in table.get("Associations", []):
            ec2.disassociate_route_table(AssociationId=association["RouteTableAssociationId"])
        ec2.delete_route_table(RouteTableId=table["RouteTableId"])
    groups = [g for g in ec2.describe_security_groups(Filters=in_vpc)["SecurityGroups"] if g["GroupName"] != "default"]
    for group in groups:  # rules that reference other groups block deletion, so remove rules first
        if group.get("IpPermissions"):
            ec2.revoke_security_group_ingress(GroupId=group["GroupId"], IpPermissions=group["IpPermissions"])
        if group.get("IpPermissionsEgress"):
            ec2.revoke_security_group_egress(GroupId=group["GroupId"], IpPermissions=group["IpPermissionsEgress"])
    for group in groups:
        ec2.delete_security_group(GroupId=group["GroupId"])
    for acl in ec2.describe_network_acls(Filters=in_vpc)["NetworkAcls"]:
        if not acl.get("IsDefault"):
            ec2.delete_network_acl(NetworkAclId=acl["NetworkAclId"])
    ec2.delete_vpc(VpcId=vpc_id)


# ── Compute and scaling (Regional): Auto Scaling, load balancers, launch templates, security groups ──


def find_autoscaling_groups(session, region: str) -> list[Found]:
    asg = session.client("autoscaling", region_name=region)
    found = []
    for page in asg.get_paginator("describe_auto_scaling_groups").paginate():
        for group in page["AutoScalingGroups"]:
            if _tagged(group.get("Tags")):  # ASG tags carry Key/Value like everything else
                name = group["AutoScalingGroupName"]
                found.append(Found("autoscaling_groups", name, region, lambda name=name: _delete_asg(asg, name)))
    return found


def _delete_asg(asg, name: str) -> None:
    from botocore.exceptions import ClientError

    def gone():  # a scaling activity in progress blocks the delete for a while: try again until it is gone
        if not asg.describe_auto_scaling_groups(AutoScalingGroupNames=[name])["AutoScalingGroups"]:
            return True
        try:
            asg.delete_auto_scaling_group(AutoScalingGroupName=name, ForceDelete=True)
        except ClientError as exc:
            if _error_code(exc) not in ("ScalingActivityInProgress", "ResourceInUse"):
                raise
        return False
    _wait_until(gone, f"Auto Scaling group {name} to be deleted")


def _tagged_arns(elb, arns: list[str]) -> set[str]:
    """ARNs (from any list) whose tags include the lab tag; describe_tags takes at most 20 ARNs."""
    tagged = set()
    for start in range(0, len(arns), 20):
        for description in elb.describe_tags(ResourceArns=arns[start:start + 20])["TagDescriptions"]:
            if _tagged(description.get("Tags")):
                tagged.add(description["ResourceArn"])
    return tagged


def find_load_balancers(session, region: str) -> list[Found]:
    elb = session.client("elbv2", region_name=region)
    balancers = [lb for page in elb.get_paginator("describe_load_balancers").paginate() for lb in page["LoadBalancers"]]
    tagged = _tagged_arns(elb, [lb["LoadBalancerArn"] for lb in balancers])
    return [Found("load_balancers", lb["LoadBalancerName"], region, lambda arn=lb["LoadBalancerArn"]: _delete_load_balancer(elb, arn))
            for lb in balancers if lb["LoadBalancerArn"] in tagged]


def _delete_load_balancer(elb, arn: str) -> None:
    from botocore.exceptions import ClientError

    elb.delete_load_balancer(LoadBalancerArn=arn)

    def gone():
        try:
            return not elb.describe_load_balancers(LoadBalancerArns=[arn])["LoadBalancers"]
        except ClientError as exc:
            if _error_code(exc) == "LoadBalancerNotFound":
                return True
            raise
    _wait_until(gone, f"load balancer {arn} to be deleted")


def find_target_groups(session, region: str) -> list[Found]:
    elb = session.client("elbv2", region_name=region)
    groups = [tg for page in elb.get_paginator("describe_target_groups").paginate() for tg in page["TargetGroups"]]
    tagged = _tagged_arns(elb, [tg["TargetGroupArn"] for tg in groups])
    return [Found("target_groups", tg["TargetGroupName"], region,
                  lambda arn=tg["TargetGroupArn"]: _delete_target_group(elb, arn))
            for tg in groups if tg["TargetGroupArn"] in tagged]


def _delete_target_group(elb, arn: str) -> None:
    from botocore.exceptions import ClientError

    def deleted():  # right after its load balancer goes, AWS may still report the group in use
        try:
            elb.delete_target_group(TargetGroupArn=arn)
            return True
        except ClientError as exc:
            if _error_code(exc) == "ResourceInUse":
                return False
            if _error_code(exc) == "TargetGroupNotFound":
                return True
            raise
    _wait_until(deleted, f"target group {arn} to be released")


def find_launch_templates(session, region: str) -> list[Found]:
    ec2 = session.client("ec2", region_name=region)
    found = []
    for page in ec2.get_paginator("describe_launch_templates").paginate():
        for template in page["LaunchTemplates"]:
            if _tagged(template.get("Tags")):
                tid = template["LaunchTemplateId"]
                found.append(Found("launch_templates", f"{template['LaunchTemplateName']} ({tid})", region,
                                   lambda tid=tid: ec2.delete_launch_template(LaunchTemplateId=tid)))
    return found


def find_security_groups(session, region: str) -> list[Found]:
    """ONE item for all tagged groups: they may reference each other, so rules go first, then groups."""
    ec2 = session.client("ec2", region_name=region)
    ids = []
    for page in ec2.get_paginator("describe_security_groups").paginate(Filters=TAG_FILTER):
        for group in page["SecurityGroups"]:
            if group["GroupName"] != "default" and _tagged(group.get("Tags")):  # never trust the filter alone
                ids.append(group["GroupId"])
    if not ids:
        return []
    return [Found("security_groups", ", ".join(ids), region, lambda ids=ids: _delete_security_groups(ec2, ids))]


def _delete_security_groups(ec2, ids: list[str]) -> None:
    from botocore.exceptions import ClientError

    for group in ec2.describe_security_groups(GroupIds=ids)["SecurityGroups"]:
        # only the rules of OUR groups are revoked; other groups are never modified
        if group.get("IpPermissions"):
            ec2.revoke_security_group_ingress(GroupId=group["GroupId"], IpPermissions=group["IpPermissions"])
        if group.get("IpPermissionsEgress"):
            ec2.revoke_security_group_egress(GroupId=group["GroupId"], IpPermissions=group["IpPermissionsEgress"])
    for group_id in ids:
        def deleted(group_id=group_id):  # a load balancer's network interfaces can linger for minutes
            try:
                ec2.delete_security_group(GroupId=group_id)
                return True
            except ClientError as exc:
                if _error_code(exc) == "DependencyViolation":
                    return False
                if _error_code(exc) == "InvalidGroup.NotFound":
                    return True
                raise
        _wait_until(deleted, f"security group {group_id} to have no dependants")


# ── Storage (Regional): EBS volumes and snapshots ───────────────────


def _is_missing(exc, *codes) -> bool:
    return _error_code(exc) in codes


def find_ebs_volumes(session, region: str) -> list[Found]:
    ec2 = session.client("ec2", region_name=region)
    found = []
    for page in ec2.get_paginator("describe_volumes").paginate(Filters=TAG_FILTER):
        for volume in page["Volumes"]:
            if not _tagged(volume.get("Tags")) or volume["State"] not in ("available", "in-use"):
                continue
            vid = volume["VolumeId"]
            label = _name(volume.get("Tags"), vid)
            reason = _volume_blocker(ec2, volume)
            if reason:  # shown in the dry run so nobody expects it to go
                label += f"  [WILL BE LEFT IN PLACE: {reason}]"
            found.append(Found("ebs_volumes", label, region, lambda vid=vid: _delete_volume(ec2, vid)))
    return found


def _volume_blocker(ec2, volume: dict) -> str | None:
    """Why this in-use volume must not be detached: every instance it is attached to must itself be tagged
    (we never touch an untagged instance's disk), and it must not be that instance's root disk."""
    for attachment in volume.get("Attachments", []):
        iid = attachment["InstanceId"]
        try:
            reservations = ec2.describe_instances(InstanceIds=[iid])["Reservations"]
        except Exception as exc:
            if _error_code(exc) == "InvalidInstanceID.NotFound":
                continue  # the instance is gone; the volume is about to be free
            raise
        for reservation in reservations:
            for instance in reservation["Instances"]:
                if not _tagged(instance.get("Tags")):
                    return f"attached to {iid}, which is not tagged {TAG_KEY}={TAG_VALUE}"
                if attachment.get("Device") == instance.get("RootDeviceName"):
                    return f"it is the root disk of {iid}; terminate the instance instead"
    return None


def _delete_volume(ec2, volume_id: str) -> None:
    from botocore.exceptions import ClientError

    def current():
        try:
            volumes = ec2.describe_volumes(VolumeIds=[volume_id])["Volumes"]
        except ClientError as exc:
            if _is_missing(exc, "InvalidVolume.NotFound"):
                return None
            raise
        return volumes[0] if volumes and volumes[0]["State"] != "deleted" else None

    volume = current()
    if volume is None:
        return
    if not _tagged(volume.get("Tags")):  # re-check right before touching it
        raise Blocked(f"volume {volume_id} is no longer tagged {TAG_KEY}={TAG_VALUE}")
    if volume["State"] == "in-use":
        reason = _volume_blocker(ec2, volume)
        if reason:
            raise Blocked(f"volume {volume_id} left in place: {reason}")
        for attachment in volume.get("Attachments", []):
            ec2.detach_volume(VolumeId=volume_id, InstanceId=attachment["InstanceId"])
        _wait_until(lambda: (current() or {"State": "available"})["State"] == "available", f"volume {volume_id} to detach")

    def deleted():
        try:
            ec2.delete_volume(VolumeId=volume_id)
        except ClientError as exc:
            if _is_missing(exc, "InvalidVolume.NotFound"):
                return True
            if _is_missing(exc, "VolumeInUse"):
                return False
            raise
        return True
    _wait_until(deleted, f"volume {volume_id} to be deleted")
    _wait_until(lambda: current() is None, f"volume {volume_id} to disappear")


def find_ebs_snapshots(session, region: str) -> list[Found]:
    ec2 = session.client("ec2", region_name=region)
    found = []
    # OwnerIds=["self"] keeps AWS's and other accounts' public snapshots out; the tag filter + client-side check
    # do the real work (moto ignores "self", and we never trust a server-side filter alone).
    for page in ec2.get_paginator("describe_snapshots").paginate(OwnerIds=["self"], Filters=TAG_FILTER):
        for snapshot in page["Snapshots"]:
            if _tagged(snapshot.get("Tags")):
                sid = snapshot["SnapshotId"]
                found.append(Found("ebs_snapshots", _name(snapshot.get("Tags"), sid), region,
                                   lambda sid=sid: _delete_snapshot(ec2, sid)))
    return found


def _delete_snapshot(ec2, snapshot_id: str) -> None:
    from botocore.exceptions import ClientError

    for image in ec2.describe_images(Owners=["self"])["Images"]:
        for mapping in image.get("BlockDeviceMappings", []):
            if mapping.get("Ebs", {}).get("SnapshotId") == snapshot_id:
                raise Blocked(f"snapshot {snapshot_id} is used by image {image['ImageId']}; deregister the image first")
    try:
        ec2.delete_snapshot(SnapshotId=snapshot_id)
    except ClientError as exc:
        if _is_missing(exc, "InvalidSnapshot.InUse"):
            raise Blocked(f"snapshot {snapshot_id} is in use by an image; deregister the image first") from exc
        if not _is_missing(exc, "InvalidSnapshot.NotFound"):
            raise


# ── Databases (Regional): DynamoDB, RDS ─────────────────────────────


def _tagged_tables(ddb) -> list[dict]:
    """Tagged DynamoDB tables as {name, arn}; tags live on the ARN, so every table costs a describe + a tag read."""
    tables = []
    for page in ddb.get_paginator("list_tables").paginate():
        for name in page["TableNames"]:
            arn = ddb.describe_table(TableName=name)["Table"]["TableArn"]
            tags, token = [], None
            while True:
                result = ddb.list_tags_of_resource(ResourceArn=arn, **({"NextToken": token} if token else {}))
                tags += result.get("Tags", [])
                token = result.get("NextToken")
                if not token:
                    break
            if _tagged(tags):
                tables.append({"name": name, "arn": arn})
    return tables


def find_dynamodb_backups(session, region: str) -> list[Found]:
    """On-demand backups have no tags of their own, so they are found through their (tagged) table. Listing
    happens before anything is deleted, so even a 'tables first' order would find them; a separate finder that
    sits BEFORE dynamodb_tables is clearer for the learner (backups appear as their own lines) and means a
    backup is never orphaned by a half-finished run: once the table is gone nothing could find it again."""
    ddb = session.client("dynamodb", region_name=region)
    found = []
    for table in _tagged_tables(ddb):
        token = None
        while True:
            result = ddb.list_backups(TableName=table["name"], BackupType="USER", **({"ExclusiveStartBackupArn": token} if token else {}))
            for backup in result.get("BackupSummaries", []):
                arn = backup["BackupArn"]
                found.append(Found("dynamodb_backups", f"{table['name']} / {backup['BackupName']}", region,
                                   lambda arn=arn: ddb.delete_backup(BackupArn=arn)))
            token = result.get("LastEvaluatedBackupArn")
            if not token:
                break
    return found


def find_dynamodb_tables(session, region: str) -> list[Found]:
    ddb = session.client("dynamodb", region_name=region)
    return [Found("dynamodb_tables", t["name"], region, lambda name=t["name"]: _delete_table(ddb, name))
            for t in _tagged_tables(ddb)]


def _delete_table(ddb, name: str) -> None:
    from botocore.exceptions import ClientError

    def gone():
        try:
            table = ddb.describe_table(TableName=name)["Table"]
        except ClientError as exc:
            if _is_missing(exc, "ResourceNotFoundException"):
                return True
            raise
        if table.get("TableStatus") == "DELETING":
            return False
        try:
            if table.get("DeletionProtectionEnabled"):  # only ever reached for a table found tagged
                ddb.update_table(TableName=name, DeletionProtectionEnabled=False)
            ddb.delete_table(TableName=name)
        except ClientError as exc:
            if not _is_missing(exc, "ResourceInUseException", "LimitExceededException"):  # still creating/updating
                raise
        return False
    _wait_until(gone, f"table {name} to be deleted")


def _rds_tags(rds, item: dict, arn_key: str) -> list:
    if "TagList" in item:
        return item["TagList"]
    return rds.list_tags_for_resource(ResourceName=item[arn_key]).get("TagList", [])


def _db_id(identifier: str) -> str:
    return identifier.rsplit(":", 1)[-1]  # a cross-Region replica names its source by ARN


def find_rds_instances(session, region: str) -> list[Found]:
    """Tagged standalone instances and read replicas. Aurora cluster members are not covered (clusters are not a
    lab kind). Replicas come first so a source is never deleted while its replicas still exist (AWS would
    otherwise promote them); a tagged source with an UNTAGGED replica is left alone, never promoting it."""
    rds = session.client("rds", region_name=region)
    instances = [i for page in rds.get_paginator("describe_db_instances").paginate() for i in page["DBInstances"]]
    source_of = {i["DBInstanceIdentifier"]: _db_id(i["ReadReplicaSourceDBInstanceIdentifier"])
                 for i in instances if i.get("ReadReplicaSourceDBInstanceIdentifier")}
    mine = [i for i in instances if not i.get("DBClusterIdentifier") and _tagged(_rds_tags(rds, i, "DBInstanceArn"))]
    mine_ids = {i["DBInstanceIdentifier"] for i in mine}

    def depth(identifier):  # replica of a replica is deeper
        count = 0
        while identifier in source_of and count < 20:
            identifier, count = source_of[identifier], count + 1
        return count
    mine.sort(key=lambda i: -depth(i["DBInstanceIdentifier"]))  # stable sort keeps the listing order otherwise
    found = []
    for instance in mine:
        iid = instance["DBInstanceIdentifier"]
        strangers = [r for r in instance.get("ReadReplicaDBInstanceIdentifiers", []) if r not in mine_ids]
        label = iid
        if strangers:
            label += f"  [WILL BE LEFT IN PLACE: it has read replica(s) not tagged {TAG_KEY}={TAG_VALUE}: {', '.join(strangers)}]"
        found.append(Found("rds_instances", label, region, lambda iid=iid, mine_ids=mine_ids: _delete_db_instance(rds, iid, mine_ids)))
    return found


def _delete_db_instance(rds, identifier: str, mine_ids: set) -> None:
    from botocore.exceptions import ClientError

    def gone():
        try:
            db = rds.describe_db_instances(DBInstanceIdentifier=identifier)["DBInstances"][0]
        except ClientError as exc:
            if _is_missing(exc, "DBInstanceNotFound", "DBInstanceNotFoundFault"):
                return True
            raise
        if db["DBInstanceStatus"] == "deleting":
            return False
        strangers = [r for r in db.get("ReadReplicaDBInstanceIdentifiers", []) if r not in mine_ids]
        if strangers:
            raise Blocked(f"{identifier} has read replica(s) not tagged {TAG_KEY}={TAG_VALUE} ({', '.join(strangers)}); "
                          "deleting it would promote them, so it is left in place")
        try:
            if db.get("DeletionProtection"):
                rds.modify_db_instance(DBInstanceIdentifier=identifier, DeletionProtection=False, ApplyImmediately=True)
            else:
                rds.delete_db_instance(DBInstanceIdentifier=identifier, SkipFinalSnapshot=True, DeleteAutomatedBackups=True)
        except ClientError as exc:
            if not _is_missing(exc, "InvalidDBInstanceState", "InvalidDBInstanceStateFault"):  # still creating/modifying
                raise
        return False
    _wait_until(gone, f"DB instance {identifier} to be deleted")


def find_rds_snapshots(session, region: str) -> list[Found]:
    rds = session.client("rds", region_name=region)
    found = []
    for page in rds.get_paginator("describe_db_snapshots").paginate(SnapshotType="manual"):
        for snapshot in page["DBSnapshots"]:
            if snapshot.get("SnapshotType", "manual") == "manual" and _tagged(_rds_tags(rds, snapshot, "DBSnapshotArn")):
                sid = snapshot["DBSnapshotIdentifier"]
                found.append(Found("rds_snapshots", sid, region, lambda sid=sid: _delete_db_snapshot(rds, sid)))
    return found


def _delete_db_snapshot(rds, identifier: str) -> None:
    from botocore.exceptions import ClientError

    def deleted():
        try:
            rds.delete_db_snapshot(DBSnapshotIdentifier=identifier)
            return True
        except ClientError as exc:
            if _is_missing(exc, "DBSnapshotNotFound", "DBSnapshotNotFoundFault"):
                return True
            if _is_missing(exc, "InvalidDBSnapshotState", "InvalidDBSnapshotStateFault"):  # still being created
                return False
            raise
    _wait_until(deleted, f"DB snapshot {identifier} to be deleted")


def find_db_subnet_groups(session, region: str) -> list[Found]:
    rds = session.client("rds", region_name=region)
    found = []
    for page in rds.get_paginator("describe_db_subnet_groups").paginate():
        for group in page["DBSubnetGroups"]:
            name = group["DBSubnetGroupName"]
            if name == "default":  # the account's built-in group can never be deleted
                continue
            if _tagged(rds.list_tags_for_resource(ResourceName=group["DBSubnetGroupArn"]).get("TagList")):
                found.append(Found("db_subnet_groups", name, region, lambda name=name: _delete_db_subnet_group(rds, name)))
    return found


def _delete_db_subnet_group(rds, name: str) -> None:
    from botocore.exceptions import ClientError

    def deleted():  # the instance that used it may still be shutting down
        try:
            rds.delete_db_subnet_group(DBSubnetGroupName=name)
            return True
        except ClientError as exc:
            if _is_missing(exc, "DBSubnetGroupNotFoundFault", "DBSubnetGroupNotFound"):
                return True
            if _is_missing(exc, "InvalidDBSubnetGroupStateFault", "InvalidDBSubnetGroupState"):
                return False
            raise
    _wait_until(deleted, f"DB subnet group {name} to be released")


# Order matters: scaling and load balancing before the EC2 things they use; EC2 before VPCs;
# databases before the VPC and security groups they sit in; IAM roles and users before customer-managed policies.
FINDERS = {
    "s3_buckets": find_s3_buckets,
    "autoscaling_groups": find_autoscaling_groups,  # first: stops it launching replacements while we delete instances
    "load_balancers": find_load_balancers,          # before target groups (a listener holds them) and security groups (its network interfaces use them)
    "target_groups": find_target_groups,            # after the load balancers that forward to them
    "ec2_instances": find_ec2_instances,            # instances before their VPC, and before the volumes/snapshots they hold
    "launch_templates": find_launch_templates,      # after the ASG that uses it (and the instances)
    "dynamodb_backups": find_dynamodb_backups,      # before the tables: backups are found through their table, so they go while it still exists
    "dynamodb_tables": find_dynamodb_tables,        # after their backups
    "rds_instances": find_rds_instances,            # replicas then sources; before the subnet group they use and the security groups/VPC around them
    "rds_snapshots": find_rds_snapshots,            # after the instances (no dependency; keeps "database things" together)
    "db_subnet_groups": find_db_subnet_groups,      # after the instances that use it, before the VPC that holds it
    "ebs_snapshots": find_ebs_snapshots,            # after instances (their AMI-less snapshots), before the volumes they came from
    "ebs_volumes": find_ebs_volumes,                # after instances (DeleteOnTermination disks vanish by themselves; the rest become 'available')
    "nat_gateways": find_nat_gateways,              # NAT gateways before the Elastic IPs they hold
    "elastic_ips": find_elastic_ips,
    "security_groups": find_security_groups,        # after everything that holds a group: instances, load balancers, NAT, databases; before the VPC
    "vpcs": find_vpcs,
    "iam_roles": find_iam_roles,
    "iam_users": find_iam_users,
    "iam_policies": find_iam_policies,
}


def _force_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def main(kinds, argv=None, session_factory=None) -> int:
    unknown = [k for k in kinds if k not in FINDERS]
    if unknown:
        raise ValueError(f"unknown resource kind(s): {', '.join(unknown)}")
    _force_utf8()
    parser = argparse.ArgumentParser(description="Delete what this lab created (tag saa-course=lab).")
    parser.add_argument("--region", default=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
    parser.add_argument("--profile", default=None)
    parser.add_argument("--yes", action="store_true", help="really delete (default: dry run)")
    args = parser.parse_args(argv)
    if session_factory is None:
        import boto3

        session_factory = boto3.Session
    kwargs = {"region_name": args.region}
    if args.profile:
        kwargs["profile_name"] = args.profile
    session = session_factory(**kwargs)

    ordered = [k for k in FINDERS if k in kinds]
    found, failures = [], 0
    for kind in ordered:
        try:
            found += FINDERS[kind](session, args.region)
        except Exception as exc:  # keep listing the other kinds
            failures += 1
            print(f"✘ could not list {kind}: {_error_code(exc)}")
    if not found:
        print(f"Nothing tagged {TAG_KEY}={TAG_VALUE} in {args.region} (or IAM). Nothing to do.")
        return 1 if failures else 0
    if not args.yes:
        print(f"DRY RUN — these would be deleted ({TAG_KEY}={TAG_VALUE}). Run again with --yes to delete:")
        for item in found:
            print(f"  · {item.kind:<18} {item.name}  ({item.region})")
        return 1 if failures else 0
    for item in found:
        try:
            item.delete()
            print(f"✔ deleted {item.kind} {item.name}")
        except Blocked as exc:
            failures += 1
            print(f"⚠ left in place {item.kind} {item.name}: {exc}")
        except Exception as exc:
            failures += 1
            print(f"✘ {item.kind} {item.name}: {_error_code(exc)}")
    print("Done." if not failures else f"Done with {failures} problem(s) — fix them in the console or run again.")
    return 1 if failures else 0
````

### `_dev/tests/test_storage_models.py`

````python
import copy

import pytest

from _harness.awslib import ebs, lifecycle, s3cost

TB_KB = 1_048_576  # object_kb that makes "objects" count whole GB (1 GB = 1,048,576 KB)


# ---------------------------------------------------------------- s3cost.storage_cost
def test_docstring_example():
    assert s3cost.storage_cost("STANDARD", 1024, TB_KB, 30) == 23.55


# 1,024 GB for 365 days, 100 GB retrieved
@pytest.mark.parametrize("cls,standard,bulk", [
    ("STANDARD", 286.55, 286.55),
    ("STANDARD_IA", 156.73, 156.73),
    ("ONEZONE_IA", 125.59, 125.59),
    ("GLACIER_IR", 52.83, 52.83),
    ("GLACIER", 45.85, 44.85),
    ("DEEP_ARCHIVE", 14.33, 12.58),
])
def test_storage_cost_a_year_with_retrieval(cls, standard, bulk):
    assert s3cost.storage_cost(cls, 1024, TB_KB, 365, 100) == standard
    assert s3cost.storage_cost(cls, 1024, TB_KB, 365, 100, retrieval="bulk") == bulk


def test_retrieval_only_costs_for_non_standard():
    assert s3cost.storage_cost("STANDARD", 0, 0, 0, 500) == 0.0
    assert s3cost.storage_cost("STANDARD_IA", 0, 0, 0, 500) == 5.0
    assert s3cost.storage_cost("GLACIER_IR", 0, 0, 0, 100) == 3.0
    assert s3cost.storage_cost("DEEP_ARCHIVE", 0, 0, 0, 100) == 2.0
    assert s3cost.storage_cost("DEEP_ARCHIVE", 0, 0, 0, 100, retrieval="bulk") == 0.25


def test_minimum_duration_is_billed():
    # deleting a Deep Archive object after 10 days still pays 180 days
    assert s3cost.storage_cost("DEEP_ARCHIVE", 1024, TB_KB, 10) == s3cost.storage_cost("DEEP_ARCHIVE", 1024, TB_KB, 180)
    assert s3cost.storage_cost("STANDARD_IA", 1024, TB_KB, 1) == s3cost.storage_cost("STANDARD_IA", 1024, TB_KB, 30) == 12.8
    # Standard has no minimum: 15 days is half a month
    assert s3cost.storage_cost("STANDARD", 1024, TB_KB, 15) == 11.78


def test_minimum_object_size_is_billed():
    # 4 KB objects are billed as 128 KB in the IA classes and Glacier IR, not in Standard or the archives
    small = (10_000_000, 4, 30)
    assert s3cost.storage_cost("STANDARD", *small) == 0.88
    assert s3cost.storage_cost("STANDARD_IA", *small) == 15.26
    assert s3cost.storage_cost("STANDARD_IA", 10_000_000, 128, 30) == 15.26
    assert s3cost.storage_cost("GLACIER", 10_000_000, 4, 90) == 0.41


@pytest.mark.parametrize("args,kwargs", [
    (("NOPE", 1, 1, 1), {}),
    (("STANDARD", -1, 1, 1), {}),
    (("STANDARD", 1, -1, 1), {}),
    (("STANDARD", 1, 1, -1), {}),
    (("STANDARD", 1, 1, 1, -1), {}),
    (("GLACIER", 1, 1, 1, 1), {"retrieval": "expedited"}),
    (("STANDARD", 1, 1, 1), {"retrieval": "fast"}),
])
def test_storage_cost_rejects(args, kwargs):
    with pytest.raises(ValueError):
        s3cost.storage_cost(*args, **kwargs)


def test_class_tables_agree():
    assert set(s3cost.MIN_DAYS) == set(s3cost.MIN_OBJECT_KB) == set(s3cost.MILLISECOND_ACCESS) == set(s3cost.CLASSES)
    assert s3cost.MIN_DAYS == {"STANDARD": 0, "STANDARD_IA": 30, "ONEZONE_IA": 30, "GLACIER_IR": 90,
                               "GLACIER": 90, "DEEP_ARCHIVE": 180}
    assert s3cost.SINGLE_AZ == {"ONEZONE_IA"}


# ---------------------------------------------------------------- s3cost.cheapest_class
def test_hot_small_objects_stay_standard():
    assert s3cost.cheapest_class(10_000_000, 4, 30) == ("STANDARD", 0.88)


def test_terabyte_kept_a_year_read_once():
    # needs milliseconds: Glacier Instant Retrieval; can wait hours: Deep Archive
    assert s3cost.cheapest_class(1024, TB_KB, 365, 1024) == ("GLACIER_IR", 80.55)
    assert s3cost.cheapest_class(1024, TB_KB, 365, 1024, millisecond_access=False) == ("DEEP_ARCHIVE", 32.81)


def test_single_az_ok_switches_ia_to_one_zone():
    assert s3cost.cheapest_class(100, TB_KB, 30, 100) == ("STANDARD_IA", 2.25)
    assert s3cost.cheapest_class(100, TB_KB, 30, 100, single_az_ok=True) == ("ONEZONE_IA", 2.0)


def test_cheapest_class_tie_keeps_earlier():
    assert s3cost.cheapest_class(0, 0, 0)[0] == "STANDARD"


# ---------------------------------------------------------------- s3cost.plan_parts / prefixes_needed
def test_plan_parts_smallest_object_edge():
    assert s3cost.plan_parts(5 * 1024 ** 2) == {"part_bytes": 5 * 1024 ** 2, "parts": 1,
                                                "last_part_bytes": 5 * 1024 ** 2, "multipart": False}
    assert s3cost.plan_parts(10 * 1024 ** 2)["parts"] == 2


def test_plan_parts_multipart_advice_threshold():
    assert s3cost.plan_parts(100 * 1024 ** 2)["multipart"] is False
    assert s3cost.plan_parts(100 * 1024 ** 2 + 1)["multipart"] is True


def test_plan_parts_single_put_limit():
    plan = s3cost.plan_parts(5 * 1024 ** 3 + 1)
    assert plan["multipart"] is True and plan["parts"] == 1025 and plan["last_part_bytes"] == 1
    assert s3cost.plan_parts(5 * 1024 ** 3)["multipart"] is True  # over the 100 MB advice


def test_plan_parts_ten_thousand_parts_edge():
    exactly = 10_000 * 5 * 1024 ** 2
    assert s3cost.plan_parts(exactly)["parts"] == 10_000
    bigger = s3cost.plan_parts(exactly + 1)          # the default part size grows by 1 MiB
    assert bigger["part_bytes"] == 6 * 1024 ** 2 and bigger["parts"] < 10_000
    with pytest.raises(ValueError):
        s3cost.plan_parts(exactly + 1, part_mib=5)


def test_plan_parts_last_part_and_biggest_object():
    plan = s3cost.plan_parts(12 * 1024 ** 2, part_mib=5)
    assert (plan["parts"], plan["last_part_bytes"]) == (3, 2 * 1024 ** 2)
    top = s3cost.plan_parts(50 * 10 ** 12)
    assert top["parts"] <= 10_000 and top["part_bytes"] <= 5 * 1024 ** 3
    assert (top["parts"] - 1) * top["part_bytes"] < 50 * 10 ** 12 <= top["parts"] * top["part_bytes"]


@pytest.mark.parametrize("size,part", [(0, None), (-1, None), (50 * 10 ** 12 + 1, None),
                                       (10 ** 9, 4), (10 ** 9, 5121)])
def test_plan_parts_rejects(size, part):
    with pytest.raises(ValueError):
        s3cost.plan_parts(size, part)


@pytest.mark.parametrize("gets,puts,want", [(0, 0, 1), (5500, 3500, 1), (5501, 0, 2), (0, 3501, 2),
                                            (11_000, 3_500, 2), (55_000, 100, 10), (100, 35_000, 10)])
def test_prefixes_needed(gets, puts, want):
    assert s3cost.prefixes_needed(gets, puts) == want


def test_prefixes_needed_rejects():
    with pytest.raises(ValueError):
        s3cost.prefixes_needed(-1, 0)
    with pytest.raises(ValueError):
        s3cost.prefixes_needed(0, -1)


# ---------------------------------------------------------------- lifecycle
LOGS = {"ID": "logs", "Status": "Enabled", "Filter": {"Prefix": "alb/"},
        "Transitions": [{"Days": 30, "StorageClass": "STANDARD_IA"}, {"Days": 90, "StorageClass": "GLACIER_IR"},
                        {"Days": 180, "StorageClass": "GLACIER"}],
        "Expiration": {"Days": 365}}


def test_realistic_rule_is_valid():
    lifecycle.validate([LOGS])


def test_waterfall_constant():
    assert lifecycle.WATERFALL == ("STANDARD", "STANDARD_IA", "INTELLIGENT_TIERING", "ONEZONE_IA",
                                   "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE")


def _rule(**kw):
    base = {"ID": "r", "Status": "Enabled", "Filter": {}}
    base.update(kw)
    return base


@pytest.mark.parametrize("rules,match", [
    ([_rule(Status="On", Expiration={"Days": 5})], "Status"),
    ([_rule()], "no action"),
    ([_rule(Transitions=[{"Days": 30, "StorageClass": "GLACIER"}, {"Days": 400, "StorageClass": "STANDARD_IA"}])], "waterfall"),
    ([_rule(Transitions=[{"Days": 30, "StorageClass": "ONEZONE_IA"}, {"Days": 100, "StorageClass": "STANDARD_IA"}])], "waterfall"),
    ([_rule(Transitions=[{"Days": 30, "StorageClass": "GLACIER_IR"}, {"Days": 100, "StorageClass": "ONEZONE_IA"}])], "waterfall"),
    ([_rule(Transitions=[{"Days": 30, "StorageClass": "DEEP_ARCHIVE"}, {"Days": 400, "StorageClass": "GLACIER"}])], "waterfall"),
    ([_rule(Transitions=[{"Days": 30, "StorageClass": "REDUCED_REDUNDANCY"}])], "valid transition target"),
    ([_rule(Transitions=[{"Days": 60, "StorageClass": "STANDARD_IA"}, {"Days": 60, "StorageClass": "GLACIER"}])], "increase"),
    ([_rule(Transitions=[{"Days": 90, "StorageClass": "STANDARD_IA"}, {"Days": 60, "StorageClass": "GLACIER"}])], "increase"),
    ([_rule(Transitions=[{"Days": 4, "StorageClass": "GLACIER_IR"}, {"Days": 93, "StorageClass": "DEEP_ARCHIVE"}])], "two-step"),
    ([_rule(Transitions=[{"Days": 30, "StorageClass": "STANDARD_IA"}, {"Days": 40, "StorageClass": "GLACIER"}])], "two-step"),
    ([_rule(Transitions=[{"Days": 30, "StorageClass": "STANDARD_IA"}], Expiration={"Days": 30})], "later than every transition"),
    ([_rule(Expiration={"Days": 5, "ExpiredObjectDeleteMarker": True})], "exactly one"),
    ([_rule(Expiration={})], "no action"),
    ([_rule(Expiration={"Days": 5}), _rule(Expiration={"Days": 9})], "duplicate"),
    ([_rule(NoncurrentVersionExpiration={"NewerNoncurrentVersions": 3})], "NoncurrentDays"),
    ([_rule(NoncurrentVersionExpiration={"NoncurrentDays": 5, "NewerNoncurrentVersions": 0})], "1 to 100"),
    ([_rule(NoncurrentVersionExpiration={"NoncurrentDays": 5, "NewerNoncurrentVersions": 101})], "1 to 100"),
    ([{"ID": "r", "Status": "Enabled", "NoncurrentVersionExpiration": {"NoncurrentDays": 5, "NewerNoncurrentVersions": 2}}], "Filter"),
    ([_rule(Filter={"Tag": {"Key": "k", "Value": "v"}}, Expiration={"ExpiredObjectDeleteMarker": True})], "tag filter"),
    ([_rule(Filter={"And": {"Prefix": "a/", "Tags": [{"Key": "k", "Value": "v"}]}},
            AbortIncompleteMultipartUpload={"DaysAfterInitiation": 7})], "tag filter"),
    ([_rule(Filter={"Prefix": "a/", "ObjectSizeGreaterThan": 5}, Expiration={"Days": 5})], "And"),
    ([_rule(NoncurrentVersionTransitions=[{"NoncurrentDays": 30, "StorageClass": "GLACIER"},
                                          {"NoncurrentDays": 400, "StorageClass": "GLACIER_IR"}])], "waterfall"),
    ([_rule(NoncurrentVersionTransitions=[{"NoncurrentDays": 4, "StorageClass": "GLACIER_IR"},
                                          {"NoncurrentDays": 50, "StorageClass": "DEEP_ARCHIVE"}])], "two-step"),
    ([_rule(NoncurrentVersionTransitions=[{"NoncurrentDays": 30, "StorageClass": "GLACIER"}],
            NoncurrentVersionExpiration={"NoncurrentDays": 20})], "later than every noncurrent"),
    ([_rule(Expiration={"Days": 5}, ID="x" * 256)], "255"),
])
def test_validate_rejects(rules, match):
    with pytest.raises(ValueError, match=match):
        lifecycle.validate(rules)


def test_validate_accepts_edges():
    lifecycle.validate([_rule(Transitions=[{"Days": 4, "StorageClass": "GLACIER_IR"},
                                           {"Days": 94, "StorageClass": "DEEP_ARCHIVE"}])])
    lifecycle.validate([_rule(Status="Disabled", Expiration={"Days": 1})])
    lifecycle.validate([_rule(Filter={"Prefix": "tmp/"}, AbortIncompleteMultipartUpload={"DaysAfterInitiation": 7})])
    lifecycle.validate([_rule(Filter={}, Expiration={"ExpiredObjectDeleteMarker": True})])
    lifecycle.validate([_rule(NoncurrentVersionExpiration={"NoncurrentDays": 30, "NewerNoncurrentVersions": 3})])
    lifecycle.validate([_rule(Transitions=[{"Days": 0, "StorageClass": "STANDARD_IA"}])])


def test_validate_rejects_too_many_rules():
    with pytest.raises(ValueError, match="1000"):
        lifecycle.validate([{"ID": str(i), "Status": "Enabled", "Expiration": {"Days": 1}} for i in range(1001)])


def test_validate_does_not_enforce_the_unconfirmed_30_day_rule():
    lifecycle.validate([_rule(Transitions=[{"Days": 1, "StorageClass": "STANDARD_IA"}])])


def test_validate_does_not_change_rules():
    rules = [copy.deepcopy(LOGS)]
    lifecycle.validate(rules)
    assert rules == [LOGS]


KB = 1024


@pytest.mark.parametrize("age,want", [(0, "STANDARD"), (29, "STANDARD"), (30, "STANDARD_IA"), (89, "STANDARD_IA"),
                                      (90, "GLACIER_IR"), (179, "GLACIER_IR"), (180, "GLACIER"), (364, "GLACIER"),
                                      (365, "EXPIRED"), (1000, "EXPIRED")])
def test_current_class_logs_rule(age, want):
    assert lifecycle.current_class([LOGS], "alb/2026/10/a.log.gz", age, 10 * KB * KB) == want


def test_current_class_filter_misses():
    assert lifecycle.current_class([LOGS], "other/a.log", 400, 10 * KB * KB) == "STANDARD"
    disabled = {**LOGS, "Status": "Disabled"}
    assert lifecycle.current_class([disabled], "alb/a", 400, 10 * KB * KB) == "STANDARD"


def test_small_objects_are_not_transitioned_but_still_expire():
    assert lifecycle.current_class([LOGS], "alb/a", 200, 127 * KB) == "STANDARD"
    assert lifecycle.current_class([LOGS], "alb/a", 200, 128 * KB) == "GLACIER"
    assert lifecycle.current_class([LOGS], "alb/a", 365, 1) == "EXPIRED"


def test_size_filter_lets_small_objects_transition():
    rule = _rule(Filter={"ObjectSizeLessThan": 128 * KB}, Transitions=[{"Days": 30, "StorageClass": "GLACIER"}])
    assert lifecycle.current_class([rule], "a", 40, 10 * KB) == "GLACIER"
    assert lifecycle.current_class([rule], "a", 40, 128 * KB) == "STANDARD"   # strictly less than
    big = _rule(Filter={"ObjectSizeGreaterThan": 1000}, Transitions=[{"Days": 30, "StorageClass": "GLACIER"}])
    assert lifecycle.current_class([big], "a", 40, 1000) == "STANDARD"        # strictly greater than
    assert lifecycle.current_class([big], "a", 40, 1001) == "GLACIER"


def test_tag_and_combined_filters():
    tagged = _rule(Filter={"Tag": {"Key": "tier", "Value": "cold"}}, Transitions=[{"Days": 10, "StorageClass": "GLACIER_IR"}])
    assert lifecycle.current_class([tagged], "a", 20, 1 << 20, {"tier": "cold"}) == "GLACIER_IR"
    assert lifecycle.current_class([tagged], "a", 20, 1 << 20, {"tier": "hot"}) == "STANDARD"
    assert lifecycle.current_class([tagged], "a", 20, 1 << 20) == "STANDARD"
    both = _rule(Filter={"And": {"Prefix": "p/", "Tags": [{"Key": "a", "Value": "1"}, {"Key": "b", "Value": "2"}],
                                 "ObjectSizeGreaterThan": 10}},
                 Expiration={"Days": 5})
    assert lifecycle.current_class([both], "p/x", 6, 100, {"a": "1", "b": "2", "c": "3"}) == "EXPIRED"
    assert lifecycle.current_class([both], "p/x", 6, 100, {"a": "1"}) == "STANDARD"
    assert lifecycle.current_class([both], "q/x", 6, 100, {"a": "1", "b": "2"}) == "STANDARD"


def test_several_rules_expiration_beats_transition_and_furthest_wins():
    cold = _rule(ID="cold", Transitions=[{"Days": 10, "StorageClass": "GLACIER"}])
    ia = _rule(ID="ia", Transitions=[{"Days": 5, "StorageClass": "STANDARD_IA"}])
    gone = _rule(ID="gone", Expiration={"Days": 20})
    assert lifecycle.current_class([ia, cold], "a", 12, 1 << 20) == "GLACIER"
    assert lifecycle.current_class([cold, ia], "a", 7, 1 << 20) == "STANDARD_IA"
    assert lifecycle.current_class([ia, cold, gone], "a", 20, 1 << 20) == "EXPIRED"


NONCURRENT = _rule(ID="nc", Filter={"Prefix": "docs/"},
                   NoncurrentVersionTransitions=[{"NoncurrentDays": 30, "StorageClass": "GLACIER_IR"}],
                   NoncurrentVersionExpiration={"NoncurrentDays": 90, "NewerNoncurrentVersions": 3})


def test_noncurrent_fate():
    nf = lifecycle.noncurrent_fate
    assert nf([NONCURRENT], "docs/a", 10) == "STANDARD"
    assert nf([NONCURRENT], "docs/a", 30) == "GLACIER_IR"
    assert nf([NONCURRENT], "docs/a", 90, newer_noncurrent=2) == "GLACIER_IR"   # still within the 3 newest to keep
    assert nf([NONCURRENT], "docs/a", 90, newer_noncurrent=3) == "DELETED"
    assert nf([NONCURRENT], "docs/a", 89, newer_noncurrent=50) == "GLACIER_IR"
    assert nf([NONCURRENT], "other/a", 500, newer_noncurrent=50) == "STANDARD"


def test_noncurrent_expiration_without_count_and_small_objects():
    plain = _rule(NoncurrentVersionExpiration={"NoncurrentDays": 7})
    assert lifecycle.noncurrent_fate([plain], "a", 7) == "DELETED"
    assert lifecycle.noncurrent_fate([plain], "a", 6) == "STANDARD"
    assert lifecycle.noncurrent_fate([NONCURRENT], "docs/a", 40, size_bytes=1000) == "STANDARD"


# ---------------------------------------------------------------- ebs
def test_gp2_iops():
    assert ebs.gp2_iops(10) == 100
    assert ebs.gp2_iops(33) == 100
    assert ebs.gp2_iops(34) == 102
    assert ebs.gp2_iops(1000) == 3000
    assert ebs.gp2_iops(5334) == 16_000
    assert ebs.gp2_iops(16_384) == 16_000


@pytest.mark.parametrize("size", [0, 16_385])
def test_gp2_iops_rejects(size):
    with pytest.raises(ValueError):
        ebs.gp2_iops(size)


def test_gp3_config_fills_the_free_baseline():
    assert ebs.gp3_config(100) == {"iops": 3000, "throughput": 125}
    assert ebs.gp3_config(1) == {"iops": 3000, "throughput": 125}
    assert ebs.gp3_config(100, iops=5000) == {"iops": 5000, "throughput": 125}


def test_gp3_config_maximums():
    assert ebs.gp3_config(160, 80_000, 2000) == {"iops": 80_000, "throughput": 2000}
    assert ebs.gp3_config(64 * 1024) == {"iops": 3000, "throughput": 125}


@pytest.mark.parametrize("args", [
    (0,), (65_537,),                 # size range 1 GiB to 64 TiB
    (200, 80_001),                   # over the 80,000 IOPS maximum
    (159, 80_000),                   # 500 IOPS per GiB: 160 GiB needed
    (100, 50_001),                   # 100 GiB gives 50,000
    (200, 4000, 2001),               # over 2,000 MiB/s
    (200, 4000, 1001),               # 0.25 MiB/s per IOPS: 4,000 IOPS gives 1,000
    (200, 2999),                     # below the free baseline
    (200, None, 124),                # below the free 125 MiB/s
])
def test_gp3_config_rejects(args):
    with pytest.raises(ValueError):
        ebs.gp3_config(*args)


def test_gp3_throughput_ratio_edge():
    assert ebs.gp3_config(200, 4000, 1000)["throughput"] == 1000
    assert ebs.gp3_config(200, None, 750)["throughput"] == 750
    with pytest.raises(ValueError):
        ebs.gp3_config(200, None, 751)


def test_monthly_cost_gp3():
    assert ebs.monthly_cost("gp3", 100) == 8.0
    assert ebs.monthly_cost("gp3", 500, 6000, 500) == 77.5           # 40 + 3,000 x 0.005 + 375 x 0.06
    assert ebs.monthly_cost("gp3", 100, throughput=125) == 8.0


def test_monthly_cost_other_types():
    assert ebs.monthly_cost("gp2", 100) == 10.0
    assert ebs.monthly_cost("st1", 1000) == 45.0
    assert ebs.monthly_cost("sc1", 1000) == 15.0
    assert ebs.monthly_cost("io2", 1000, 10_000) == 775.0            # 125 + 10,000 x 0.065
    assert ebs.monthly_cost("io2", 1000, 40_000) == 2573.0           # 125 + 32,000 x 0.065 + 8,000 x 0.046


def test_gp3_is_cheaper_than_gp2_per_gib():
    assert ebs.monthly_cost("gp3", 1000) == 0.8 * ebs.monthly_cost("gp2", 1000)


@pytest.mark.parametrize("args,kwargs", [
    (("magnetic", 100), {}),
    (("st1", 124), {}), (("sc1", 16_385), {}), (("io2", 3), {"iops": 100}),
    (("io2", 100), {}),                     # io2 needs iops
    (("io2", 100), {"iops": 100_001}),      # 1,000 IOPS per GiB
    (("io2", 1000), {"iops": 256_001}),
    (("io2", 1000), {"iops": 70_000}),      # third price tier unknown
    (("io2", 1000), {"iops": 1000, "throughput": 4001}),
    (("gp2", 100), {"iops": 3000}),
    (("st1", 500), {"throughput": 200}),
    (("gp3", 100), {"iops": 80_001}),
])
def test_monthly_cost_rejects(args, kwargs):
    with pytest.raises(ValueError):
        ebs.monthly_cost(*args, **kwargs)


def test_type_tables():
    assert ebs.BOOTABLE == {"gp2", "gp3", "io1", "io2"}
    assert ebs.MULTI_ATTACH == {"io1", "io2"}
    assert "st1" not in ebs.BOOTABLE and "sc1" not in ebs.BOOTABLE


@pytest.mark.parametrize("kwargs,want", [
    ({}, "gp3"),
    ({"iops": 16_000, "throughput_mibs": 1000}, "gp3"),
    ({"iops": 80_000}, "gp3"),
    ({"iops": 80_001}, "io2"),
    ({"throughput_mibs": 2001}, "io2"),
    ({"iops": 256_000, "throughput_mibs": 4000}, "io2"),
    ({"multi_attach": True}, "io2"),
    ({"sequential": True, "throughput_mibs": 400}, "st1"),
    ({"sequential": True, "throughput_mibs": 500, "iops": 500}, "st1"),
    ({"sequential": True, "throughput_mibs": 501}, "gp3"),
    ({"sequential": True, "throughput_mibs": 200, "rarely_accessed": True}, "sc1"),
    ({"sequential": True, "throughput_mibs": 251, "rarely_accessed": True}, "st1"),
    ({"sequential": True, "throughput_mibs": 100, "boot": True}, "gp3"),
    ({"rarely_accessed": True}, "gp3"),
    ({"sequential": True, "throughput_mibs": 100, "multi_attach": True}, "io2"),
])
def test_choose_volume(kwargs, want):
    assert ebs.choose_volume(**kwargs) == want


@pytest.mark.parametrize("kwargs", [{"iops": 256_001}, {"throughput_mibs": 4001}, {"multi_attach": True, "boot": True},
                                    {"iops": -1}, {"throughput_mibs": -1}])
def test_choose_volume_rejects(kwargs):
    with pytest.raises(ValueError):
        ebs.choose_volume(**kwargs)
````

### `_dev/tests/test_database_models.py`

````python
import doctest

import pytest

from _harness.awslib import caching, dbmath, dynamo, prices


def test_doctests():
    for mod in (dynamo, caching, dbmath):
        assert doctest.testmod(mod).failed == 0


# ---------------------------------------------------------------- dynamo
@pytest.mark.parametrize("kb,eventual,strong,trans", [
    (1, 0.5, 1, 2), (4, 0.5, 1, 2), (4.1, 1, 2, 4), (8, 1, 2, 4), (400, 50, 100, 200)])
def test_read_units(kb, eventual, strong, trans):
    assert dynamo.read_units(kb) == eventual
    assert dynamo.read_units(kb, "eventual") == eventual
    assert dynamo.read_units(kb, "strong") == strong
    assert dynamo.read_units(kb, "transactional") == trans


@pytest.mark.parametrize("kb,standard,trans", [(0.5, 1, 2), (1, 1, 2), (1.5, 2, 4), (3, 3, 6), (400, 400, 800)])
def test_write_units(kb, standard, trans):
    assert dynamo.write_units(kb) == standard
    assert dynamo.write_units(kb, transactional=True) == trans


def test_research_rounding_examples():
    assert dynamo.read_units(3, "strong") == 1      # 3 KB read = 1 RCU
    assert dynamo.write_units(0.5) == 1             # 512 byte write = 1 WCU


@pytest.mark.parametrize("kb", [0, -1, 400.1, 401])
def test_item_size_limits(kb):
    with pytest.raises(ValueError):
        dynamo.read_units(kb)
    with pytest.raises(ValueError):
        dynamo.write_units(kb)


def test_unknown_consistency():
    with pytest.raises(ValueError):
        dynamo.read_units(1, "fast")


def test_provisioned_capacity():
    assert dynamo.provisioned_capacity(100, 50, 6) == (100, 300)
    assert dynamo.provisioned_capacity(100, 50, 6, "strong") == (200, 300)
    assert dynamo.provisioned_capacity(100, 50, 6, "transactional", True) == (400, 600)
    assert dynamo.provisioned_capacity(3, 1, 4) == (2, 4)   # ceil(1.5) reads
    with pytest.raises(ValueError):
        dynamo.provisioned_capacity(-1, 1, 1)


def test_on_demand_cost():
    assert dynamo.monthly_cost_on_demand(1_000_000, 1_000_000, 1) == 0.6875
    assert dynamo.monthly_cost_on_demand(2_000_000, 0, 4, "strong") == 0.25
    assert dynamo.monthly_cost_on_demand(0, 1_000_000, 2, transactional_writes=True) == 2.5
    with pytest.raises(ValueError):
        dynamo.monthly_cost_on_demand(-1, 0, 1)


def test_on_demand_custom_price():
    p = {"dynamodb_on_demand_per_million_reads": 1.0, "dynamodb_on_demand_per_million_writes": 2.0}
    assert dynamo.monthly_cost_on_demand(1_000_000, 1_000_000, 1, price=p) == 2.5


def test_provisioned_cost():
    assert dynamo.monthly_cost_provisioned(100, 100) == 56.94
    assert dynamo.monthly_cost_provisioned(0, 0) == 0
    assert dynamo.monthly_cost_provisioned(10, 10, hours=100) == round(100 * 10 * (0.00013 + 0.00065), 4)
    p = {"dynamodb_rcu_hour": 1.0, "dynamodb_wcu_hour": 2.0}
    assert dynamo.monthly_cost_provisioned(1, 1, hours=10, price=p) == 30
    with pytest.raises(ValueError):
        dynamo.monthly_cost_provisioned(-1, 0)


def test_database_prices_section():
    p = prices.section("database")
    assert p["dynamodb_on_demand_per_million_writes"] == 0.625
    assert p["dynamodb_rcu_hour"] == 0.00013
    assert p["rds_proxy_per_vcpu_hour"] == 0.015


def test_break_even_and_crossover():
    assert dynamo.break_even_utilisation() == {"writes": 0.2889, "reads": 0.2889}
    # one WCU kept for the month: provisioned beats on-demand at full use, loses at 10% use
    units_full = 3600 * dynamo.HOURS_PER_MONTH
    prov = dynamo.monthly_cost_provisioned(0, 1)
    assert prov < dynamo.monthly_cost_on_demand(0, units_full, 1)
    assert prov > dynamo.monthly_cost_on_demand(0, units_full * 0.1, 1)
    p = {"dynamodb_wcu_hour": 1.0, "dynamodb_rcu_hour": 1.0,
         "dynamodb_on_demand_per_million_writes": 1e6 / 3600 * 2,
         "dynamodb_on_demand_per_million_reads": 1e6 / 3600}
    assert dynamo.break_even_utilisation(p) == {"writes": 0.5, "reads": 1.0}


# ---------------------------------------------------------------- caching
READ_HEAVY = [(0, "write", "k", "v1"), (1, "read", "k"), (2, "read", "k"), (3, "write", "k", "v2"),
              (4, "read", "k"), (5, "read", "k"), (11, "read", "k")]


def test_lazy_serves_stale_until_ttl():
    r = caching.simulate(READ_HEAVY, "lazy", ttl=10)
    # t=1 miss (fill v1, expires 11), t=2 hit, write v2 (db only), t=4,5 stale hits, t=11 expired -> miss
    assert r == {"hits": 3, "misses": 2, "db_reads": 2, "db_writes": 2, "stale_reads": 2, "cache_writes": 2}


def test_write_through_never_stale():
    r = caching.simulate(READ_HEAVY, "write-through", ttl=10)
    # writes at t=0 and t=3 refresh the cache; t=11 is inside the second entry (expires 13)
    assert r == {"hits": 5, "misses": 0, "db_reads": 0, "db_writes": 2, "stale_reads": 0, "cache_writes": 2}


def test_ttl_boundary_exact():
    ev = [(0, "write", "k", 1), (1, "read", "k"), (11, "read", "k")]
    assert caching.simulate(ev, "lazy", ttl=10)["misses"] == 2      # fill at t=1, expires t=11
    ev = [(0, "write", "k", 1), (0, "read", "k"), (9.99, "read", "k"), (10, "read", "k")]
    r = caching.simulate(ev, "lazy", ttl=10)
    assert (r["hits"], r["misses"]) == (1, 2)                       # fill at 0, hit 9.99, miss at exactly 10


def test_write_through_ttl_expiry_then_reload():
    ev = [(0, "write", "k", 1), (10, "read", "k"), (11, "read", "k")]
    r = caching.simulate(ev, "write-through", ttl=10)
    assert (r["hits"], r["misses"], r["db_reads"], r["cache_writes"]) == (1, 1, 1, 2)


def test_cold_start_and_missing_key():
    r = caching.simulate([(0, "read", "a"), (1, "read", "a"), (2, "read", "b")], "lazy")
    assert (r["hits"], r["misses"], r["db_reads"], r["stale_reads"]) == (1, 2, 2, 0)


def test_no_ttl_stays_stale_forever():
    ev = [(0, "read", "k"), (1, "write", "k", 5), (10**6, "read", "k")]
    assert caching.simulate(ev, "lazy")["stale_reads"] == 1
    assert caching.simulate(ev, "write-through")["stale_reads"] == 0


def test_caching_errors():
    with pytest.raises(ValueError):
        caching.simulate([], "write-back")
    with pytest.raises(ValueError):
        caching.simulate([(0, "delete", "k")], "lazy")
    with pytest.raises(ValueError):
        caching.simulate([(5, "read", "k"), (4, "read", "k")], "lazy")
    with pytest.raises(ValueError):
        caching.simulate([(0, "write", "k")], "lazy")
    with pytest.raises(ValueError):
        caching.simulate([], "lazy", ttl=0)
    assert caching.simulate([], "lazy")["hits"] == 0


# ---------------------------------------------------------------- dbmath
def test_peak_concurrency():
    assert dbmath.peak_concurrency(500, 0.2) == 100
    assert dbmath.peak_concurrency(10, 0.25) == 3
    assert dbmath.peak_concurrency(0.5, 1) == 1


def test_connections_and_needs_proxy():
    assert dbmath.connections_without_proxy(100) == 100
    assert dbmath.connections_without_proxy(100, 2) == 200
    assert dbmath.needs_proxy(100, 90) is True
    assert dbmath.needs_proxy(100, 100) is False
    assert dbmath.needs_proxy(90, 100, headroom=0.2) is True
    assert dbmath.needs_proxy(80, 100, headroom=0.2) is False
    assert dbmath.needs_proxy(60, 100, connections_per_invocation=2) is True


def test_proxy_pool_size():
    assert dbmath.proxy_pool_size(90, 50) == 45
    assert dbmath.proxy_pool_size(85, 50) == 42
    assert dbmath.proxy_pool_size(100, 100) == 100


def test_default_max_connections():
    assert dbmath.default_max_connections("postgres", 1) == 112
    assert dbmath.default_max_connections("mysql", 1) == 85
    assert dbmath.default_max_connections("postgres", 1024) == 5000     # capped
    assert dbmath.default_max_connections("mysql", 8) == 8 * 2**30 // 12582880


@pytest.mark.parametrize("call", [
    lambda: dbmath.peak_concurrency(0, 1), lambda: dbmath.peak_concurrency(1, -1),
    lambda: dbmath.connections_without_proxy(0), lambda: dbmath.connections_without_proxy(1, 0),
    lambda: dbmath.needs_proxy(1, 0), lambda: dbmath.needs_proxy(1, 10, headroom=1),
    lambda: dbmath.needs_proxy(1, 10, headroom=-0.1),
    lambda: dbmath.proxy_pool_size(0, 50), lambda: dbmath.proxy_pool_size(10, 0),
    lambda: dbmath.proxy_pool_size(10, 101),
    lambda: dbmath.default_max_connections("oracle", 1), lambda: dbmath.default_max_connections("mysql", 0)])
def test_dbmath_errors(call):
    with pytest.raises(ValueError):
        call()
````

### `_dev/tests/test_cfn_intrinsics.py`

````python
import pytest

from _harness.awslib import cfn

NETWORK = """AWSTemplateFormatVersion: '2010-09-09'
Parameters:
  Prefix: {Type: String, Default: shortly}
  Env: {Type: String, AllowedValues: [lab, prod]}
  VpcCidr: {Type: String, Default: 10.20.0.0/16}
Conditions:
  IsProd: !Equals [!Ref Env, prod]
  IsLab: !Not [!Condition IsProd]
  ProdInUsEast1: !And [!Condition IsProd, !Equals [!Ref 'AWS::Region', us-east-1]]
  Either: !Or [!Condition IsLab, !Condition ProdInUsEast1]
Resources:
  Vpc:
    Type: AWS::EC2::VPC
    Properties: {CidrBlock: !Ref VpcCidr}
  SubnetA:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref Vpc
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: !Select [0, !Cidr [!Ref VpcCidr, 6, 8]]
  SubnetB:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref Vpc
      AvailabilityZone: !Select [1, !GetAZs {Ref: 'AWS::Region'}]
      CidrBlock: !Select [1, !Cidr [!Ref VpcCidr, 6, 8]]
  NatA:
    Type: AWS::EC2::NatGateway
    Properties: {SubnetId: !Ref SubnetA}
  NatB:
    Type: AWS::EC2::NatGateway
    Condition: IsProd
    Properties: {SubnetId: !Ref SubnetB}
  RouteB:
    Type: AWS::EC2::Route
    Properties:
      DestinationCidrBlock: 0.0.0.0/0
      NatGatewayId: !If [IsProd, !Ref NatB, !Ref NatA]
      Description: !If [IsProd, per-az, !Ref 'AWS::NoValue']
      Tags: [{Key: a, Value: b}, !If [IsProd, {Key: env, Value: prod}, !Ref 'AWS::NoValue']]
Outputs:
  AppSubnets:
    Value: !Join [',', [!Ref SubnetA, !Ref SubnetB]]
  Imported:
    Value: !ImportValue {'Fn::Sub': '${Prefix}-vpc-id'}
"""


@pytest.fixture(scope="module")
def template():
    return cfn.load_template_text(NETWORK)


def test_conditions(template):
    assert cfn.evaluate_conditions(template, {"Env": "prod"}) == {"IsProd": True, "IsLab": False,
                                                                  "ProdInUsEast1": True, "Either": True}
    assert cfn.evaluate_conditions(template, {"Env": "lab"}) == {"IsProd": False, "IsLab": True,
                                                                 "ProdInUsEast1": False, "Either": True}
    assert cfn.evaluate_conditions(template, {"Env": "prod"}, {"AWS::Region": "eu-west-1"})["Either"] is False


def test_bad_conditions():
    with pytest.raises(cfn.TemplateError, match="unknown condition"):
        cfn.evaluate_conditions({"Conditions": {"A": {"Condition": "Missing"}}})
    with pytest.raises(cfn.TemplateError, match="itself"):
        cfn.evaluate_conditions({"Conditions": {"A": {"Condition": "A"}}})


def test_select_getazs_and_cidr(template):
    res = cfn.active_resources(template, {"Prefix": "shortly", "Env": "prod", "VpcCidr": "10.20.0.0/16"})
    assert res["SubnetA"]["Properties"]["AvailabilityZone"] == "us-east-1a"
    assert res["SubnetB"]["Properties"]["AvailabilityZone"] == "us-east-1b"
    assert res["SubnetA"]["Properties"]["CidrBlock"] == "10.20.0.0/24"
    assert res["SubnetB"]["Properties"]["CidrBlock"] == "10.20.1.0/24"
    assert cfn.render({"Fn::Cidr": ["10.0.0.0/16", 3, 12]}) == ["10.0.0.0/20", "10.0.16.0/20", "10.0.32.0/20"]
    assert cfn.render({"Fn::GetAZs": "eu-west-1"})[:2] == ["eu-west-1a", "eu-west-1b"]


def test_select_out_of_range():
    with pytest.raises(cfn.TemplateError, match="Fn::Select"):
        cfn.render({"Fn::Select": [9, ["a", "b"]]})


def test_condition_on_resource_and_if(template):
    prod = cfn.active_resources(template, {"Env": "prod"})
    lab = cfn.active_resources(template, {"Env": "lab"})
    assert "NatB" in prod and "NatB" not in lab
    assert prod["RouteB"]["Properties"]["NatGatewayId"] == "NatB"
    assert lab["RouteB"]["Properties"]["NatGatewayId"] == "NatA"


def test_novalue_drops_properties_and_items(template):
    prod = cfn.active_resources(template, {"Env": "prod"})["RouteB"]["Properties"]
    lab = cfn.active_resources(template, {"Env": "lab"})["RouteB"]["Properties"]
    assert prod["Description"] == "per-az" and "Description" not in lab
    assert prod["Tags"] == [{"Key": "a", "Value": "b"}, {"Key": "env", "Value": "prod"}]
    assert lab["Tags"] == [{"Key": "a", "Value": "b"}]
    assert cfn.render({"Ref": "AWS::NoValue"}) is None


def test_if_needs_conditions():
    with pytest.raises(cfn.TemplateError, match="evaluate_conditions"):
        cfn.render({"Fn::If": ["IsProd", "a", "b"]})


def test_join_of_refs_and_import_value(template):
    outputs = cfn.render(template["Outputs"], {"Prefix": "shortly"}, conditions={})
    assert outputs["AppSubnets"]["Value"] == "SubnetA,SubnetB"
    assert outputs["Imported"]["Value"] == "import:shortly-vpc-id"


def test_parameter_defaults_fill_in(template):
    assert cfn.parameter_values(template, {"Env": "lab"}) == {"Prefix": "shortly", "VpcCidr": "10.20.0.0/16", "Env": "lab"}
    res = cfn.active_resources(template, {"Env": "lab", "VpcCidr": "10.99.0.0/16"})
    assert res["Vpc"]["Properties"]["CidrBlock"] == "10.99.0.0/16"


def test_inline_functions_replaces_only_named(template):
    flat = cfn.inline_functions(template, {"Fn::Cidr"}, {"Env": "lab"})
    cidr_block = flat["Resources"]["SubnetA"]["Properties"]["CidrBlock"]
    assert cidr_block == {"Fn::Select": [0, ["10.20.0.0/24", "10.20.1.0/24", "10.20.2.0/24", "10.20.3.0/24",
                                             "10.20.4.0/24", "10.20.5.0/24"]]}
    assert flat["Resources"]["Vpc"]["Properties"]["CidrBlock"] == {"Ref": "VpcCidr"}


def test_base64_renders_unencoded_input():
    assert cfn.render({"Fn::Base64": {"Fn::Sub": "#!/bin/bash\necho ${Prefix}"}}, {"Prefix": "shortly"}) == "#!/bin/bash\necho shortly"


def test_split_of_join_and_import_value():
    joined = {"Fn::Join": [",", ["a", "b", "c"]]}
    assert cfn.render({"Fn::Split": [",", joined]}) == ["a", "b", "c"]
    assert cfn.render({"Fn::Split": [",", {"Fn::ImportValue": "name"}]}) == ["import:name"]
    assert cfn.render({"Fn::Select": [1, {"Fn::Split": ["-", "x-y-z"]}]}) == "y"


def test_split_of_a_list_is_an_error():
    with pytest.raises(cfn.TemplateError, match="Fn::Split"):
        cfn.render({"Fn::Split": [",", ["a", "b"]]})


MAPPED = """AWSTemplateFormatVersion: '2010-09-09'
Mappings:
  Elb:
    us-east-1: {Account: '127311923021'}
    eu-west-1: {Account: '156460612806'}
Resources:
  Policy:
    Type: AWS::S3::BucketPolicy
    Properties:
      Bucket: b
      PolicyDocument:
        Principal: {AWS: !Join [':', [arn, !FindInMap [Elb, !Ref 'AWS::Region', Account]]]}
Outputs:
  Acct:
    Value: !FindInMap [Elb, us-east-1, Account]
"""


def test_find_in_map_renders_with_template_mappings():
    tpl = cfn.load_template_text(MAPPED)
    res = cfn.active_resources(tpl, {}, {"AWS::Region": "eu-west-1"})
    assert res["Policy"]["Properties"]["PolicyDocument"]["Principal"]["AWS"] == "arn:156460612806"
    assert cfn.render(tpl["Outputs"], {}, None, {}, tpl["Mappings"]) == {"Acct": {"Value": "127311923021"}}


def test_find_in_map_missing_key_is_an_error():
    tpl = cfn.load_template_text(MAPPED)
    with pytest.raises(cfn.TemplateError, match="FindInMap"):
        cfn.active_resources(tpl, {}, {"AWS::Region": "ap-south-1"})
    with pytest.raises(cfn.TemplateError, match="FindInMap"):
        cfn.render({"Fn::FindInMap": ["Nope", "a", "b"]})


def test_render_mappings_do_not_leak_between_calls():
    tpl = cfn.load_template_text(MAPPED)
    assert cfn.render({"Fn::FindInMap": ["Elb", "us-east-1", "Account"]}, {}, None, {}, tpl["Mappings"]) == "127311923021"
    with pytest.raises(cfn.TemplateError):
        cfn.render({"Fn::FindInMap": ["Elb", "us-east-1", "Account"]})


MOTO = """AWSTemplateFormatVersion: '2010-09-09'
Resources:
  Cache:
    Type: AWS::ElastiCache::ReplicationGroup
    Properties: {ReplicationGroupDescription: x}
  Database:
    Type: AWS::RDS::DBInstance
    Properties: {Engine: postgres}
  Reader:
    Type: AWS::IAM::Policy
    DependsOn: [Cache, Database]
    Properties:
      PolicyDocument:
        Statement:
          - Resource: !GetAtt Database.MasterUserSecret.SecretArn
          - Resource: !Sub '${Database.Endpoint.Address}/x'
Outputs:
  Secret: {Value: !GetAtt Database.MasterUserSecret.SecretArn}
  Address: {Value: !GetAtt Database.Endpoint.Address}
  CacheAddress: {Value: !GetAtt Cache.PrimaryEndPoint.Address}
  CacheName: {Value: !Ref Cache}
"""
SECRET = {"Database.MasterUserSecret.SecretArn": "arn:aws:secretsmanager:us-east-1:111122223333:secret:rds!db-moto"}


def test_for_moto_removes_types_outputs_and_replaces_getatt():
    tpl = cfn.load_template_text(MOTO)
    out = cfn.for_moto(tpl, {"AWS::ElastiCache::ReplicationGroup"}, SECRET)
    assert set(out["Resources"]) == {"Database", "Reader"}
    assert out["Resources"]["Reader"]["DependsOn"] == ["Database"]
    assert out["Resources"]["Reader"]["Properties"]["PolicyDocument"]["Statement"][0]["Resource"] == SECRET["Database.MasterUserSecret.SecretArn"]
    assert out["Resources"]["Reader"]["Properties"]["PolicyDocument"]["Statement"][1]["Resource"] == {"Fn::Sub": "${Database.Endpoint.Address}/x"}
    assert set(out["Outputs"]) == {"Address"}
    assert "Cache" in tpl["Resources"], "the original template is not changed"


def test_for_moto_without_getatt_values_only_drops_types():
    out = cfn.for_moto(cfn.load_template_text(MOTO), ["AWS::ElastiCache::ReplicationGroup"])
    assert "Fn::GetAtt" in str(out["Resources"]["Reader"]) and set(out["Outputs"]) == {"Secret", "Address"}


def test_for_moto_names_a_resource_that_still_uses_a_removed_one():
    tpl = cfn.load_template_text(MOTO.replace("Resource: !Sub '${Database.Endpoint.Address}/x'", "Resource: !Ref Cache"))
    with pytest.raises(cfn.TemplateError, match="Reader.*Cache|Cache.*Reader"):
        cfn.for_moto(tpl, {"AWS::ElastiCache::ReplicationGroup"}, SECRET)
    sub = cfn.load_template_text(MOTO.replace("${Database.Endpoint.Address}/x", "${Cache.PrimaryEndPoint.Address}"))
    with pytest.raises(cfn.TemplateError, match="Cache"):
        cfn.for_moto(sub, {"AWS::ElastiCache::ReplicationGroup"}, SECRET)
````

### `_dev/tests/test_policy_eval.py`

````python
import pytest

from _harness.awslib.policy_eval import (Request, account_of, action_matches, condition_matches,
                                         evaluate, evaluate_policies, evaluate_trust, principal_matches,
                                         resource_matches, statement_applies, statements)

A = "111122223333"
B = "444455556666"
ROLE = f"arn:aws:iam::{A}:role/app"
SESSION = f"arn:aws:sts::{A}:assumed-role/app/i-0abc"
BUCKET_OBJ = "arn:aws:s3:::shortly-assets/uploads/a.png"
FULL = {"Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]}


def allow(action, resource="*", **extra):
    return {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": action, "Resource": resource, **extra}]}


def deny(action, resource="*", **extra):
    return {"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Action": action, "Resource": resource, **extra}]}


def req(action="s3:GetObject", resource=BUCKET_OBJ, principal=ROLE, **context):
    return Request(principal=principal, action=action, resource=resource, context=context)


@pytest.mark.parametrize("pattern, action, expected", [
    ("s3:GetObject", "s3:GetObject", True), ("s3:getobject", "S3:GetObject", True),
    ("s3:Get*", "s3:GetObjectTagging", True), ("s3:*", "s3:PutObject", True), ("*", "ec2:RunInstances", True),
    ("s3:Get?bject", "s3:GetObject", True), ("s3:Get*", "s3:PutObject", False), ("ec2:*", "s3:GetObject", False),
    ("s3:List*", "s3:GetObject", False),
])
def test_action_matches(pattern, action, expected):
    assert action_matches(pattern, action) is expected


@pytest.mark.parametrize("pattern, arn, expected", [
    ("*", BUCKET_OBJ, True),
    ("arn:aws:s3:::shortly-assets/*", BUCKET_OBJ, True),
    ("arn:aws:s3:::shortly-assets/uploads/*", BUCKET_OBJ, True),
    ("arn:aws:s3:::shortly-assets", BUCKET_OBJ, False),
    ("arn:aws:s3:::Shortly-assets/*", BUCKET_OBJ, False),  # resources are case-sensitive
    ("arn:aws:dynamodb:*:*:table/shortly-*", f"arn:aws:dynamodb:us-east-1:{A}:table/shortly-links", True),
    ("arn:aws:dynamodb:*:*:table/shortly-*", f"arn:aws:dynamodb:us-east-1:{A}:table/other", False),
    ("arn:aws:lambda:us-east-1:*:function:f*", f"arn:aws:lambda:us-east-1:{A}:function:fn:PROD", True),
    ("arn:aws:*:us-east-1:*:*", f"arn:aws:sqs:eu-west-1:{A}:q", False),  # a wildcard never spans segments
])
def test_resource_matches(pattern, arn, expected):
    assert resource_matches(pattern, arn) is expected


def test_account_of():
    assert account_of(ROLE) == A
    assert account_of("arn:aws:s3:::bucket") is None
    assert account_of("ec2.amazonaws.com") is None


@pytest.mark.parametrize("principal, caller, expected", [
    ("*", ROLE, True), ({"AWS": "*"}, ROLE, True), ({"AWS": A}, ROLE, True),
    ({"AWS": f"arn:aws:iam::{A}:root"}, SESSION, True), ({"AWS": f"arn:aws:iam::{B}:root"}, ROLE, False),
    ({"AWS": ROLE}, ROLE, True), ({"AWS": ROLE}, SESSION, True),
    ({"AWS": f"arn:aws:iam::{A}:role/team/app"}, SESSION, True),  # role path is not in the session ARN
    ({"AWS": f"arn:aws:iam::{A}:role/other"}, SESSION, False),
    ({"Service": "ec2.amazonaws.com"}, "ec2.amazonaws.com", True),
    ({"Service": ["lambda.amazonaws.com"]}, "ec2.amazonaws.com", False),
])
def test_principal_matches(principal, caller, expected):
    assert principal_matches(principal, caller) is expected


def test_statements_accepts_single_dict():
    assert statements({"Statement": {"Effect": "Allow"}}) == [{"Effect": "Allow"}]


@pytest.mark.parametrize("condition, context, expected", [
    (None, {}, True),
    ({"StringEquals": {"aws:RequestedRegion": "us-east-1"}}, {"aws:RequestedRegion": "us-east-1"}, True),
    ({"StringEquals": {"aws:RequestedRegion": ["us-east-1", "eu-west-1"]}}, {"aws:RequestedRegion": "eu-west-1"}, True),
    ({"StringEquals": {"aws:RequestedRegion": "us-east-1"}}, {"aws:requestedregion": "us-east-1"}, True),  # keys are case-insensitive
    ({"StringEquals": {"aws:RequestedRegion": "us-east-1"}}, {}, False),
    ({"StringNotEquals": {"aws:RequestedRegion": ["us-east-1", "us-west-2"]}}, {"aws:RequestedRegion": "eu-west-1"}, True),
    ({"StringNotEquals": {"aws:RequestedRegion": ["us-east-1", "us-west-2"]}}, {"aws:RequestedRegion": "us-west-2"}, False),
    ({"StringNotEquals": {"aws:RequestedRegion": "us-east-1"}}, {}, True),  # negated operator, key missing
    ({"StringLike": {"s3:prefix": "home/*"}}, {"s3:prefix": "home/alice/"}, True),
    ({"StringLike": {"s3:prefix": "home/*"}}, {"s3:prefix": "Home/alice/"}, False),
    ({"StringEqualsIgnoreCase": {"aws:PrincipalTag/team": "Data"}}, {"aws:PrincipalTag/team": "data"}, True),
    ({"Bool": {"aws:SecureTransport": "true"}}, {"aws:SecureTransport": True}, True),
    ({"Bool": {"aws:SecureTransport": "true"}}, {"aws:SecureTransport": False}, False),
    ({"Bool": {"aws:MultiFactorAuthPresent": "true"}}, {}, False),
    ({"BoolIfExists": {"aws:MultiFactorAuthPresent": "false"}}, {}, True),
    ({"IpAddress": {"aws:SourceIp": "203.0.113.0/24"}}, {"aws:SourceIp": "203.0.113.7"}, True),
    ({"NotIpAddress": {"aws:SourceIp": "203.0.113.0/24"}}, {"aws:SourceIp": "198.51.100.1"}, True),
    ({"NumericLessThanEquals": {"s3:max-keys": "100"}}, {"s3:max-keys": 50}, True),
    ({"NumericGreaterThan": {"s3:max-keys": "100"}}, {"s3:max-keys": 50}, False),
    ({"ArnLike": {"aws:SourceArn": "arn:aws:sns:*:*:alerts"}}, {"aws:SourceArn": f"arn:aws:sns:us-east-1:{A}:alerts"}, True),
    ({"Null": {"aws:TokenIssueTime": "true"}}, {}, True),
    ({"Null": {"aws:TokenIssueTime": "false"}}, {}, False),
    ({"ForAnyValue:StringEquals": {"aws:TagKeys": ["env", "team"]}}, {"aws:TagKeys": ["owner", "env"]}, True),
    ({"ForAnyValue:StringEquals": {"aws:TagKeys": ["env"]}}, {}, False),
    ({"ForAllValues:StringEquals": {"aws:TagKeys": ["env", "team"]}}, {"aws:TagKeys": ["env", "owner"]}, False),
    ({"ForAllValues:StringEquals": {"aws:TagKeys": ["env", "team"]}}, {"aws:TagKeys": ["team"]}, True),
    ({"ForAllValues:StringEquals": {"aws:TagKeys": ["env"]}}, {}, True),  # the classic trap: empty set passes
    ({"StringEquals": {"a": "1"}, "Bool": {"b": "true"}}, {"a": "1", "b": False}, False),  # operators are ANDed
    ({"StringEquals": {"a": "1", "c": "2"}}, {"a": "1", "c": "3"}, False),  # keys are ANDed
])
def test_condition_matches(condition, context, expected):
    assert condition_matches(condition, context) is expected


def test_unsupported_operator_raises():
    with pytest.raises(ValueError, match="DateGreaterThan"):
        condition_matches({"DateGreaterThan": {"aws:CurrentTime": "2026-01-01T00:00:00Z"}}, {})


def test_statement_applies_not_action_and_not_resource():
    st = {"Effect": "Deny", "NotAction": ["iam:*", "sts:*"], "Resource": "*"}
    assert statement_applies(st, req("s3:PutObject"))
    assert not statement_applies(st, req("iam:CreateRole"))
    st = {"Effect": "Allow", "Action": "s3:*", "NotResource": "arn:aws:s3:::secret/*"}
    assert statement_applies(st, req("s3:GetObject", BUCKET_OBJ))
    assert not statement_applies(st, req("s3:GetObject", "arn:aws:s3:::secret/x"))


def test_statement_needs_principal_when_checked():
    st = {"Effect": "Allow", "Action": "s3:GetObject", "Resource": "*"}
    assert statement_applies(st, req())
    assert not statement_applies(st, req(), check_principal=True)


def test_evaluate_policies_deny_beats_allow():
    policies = [allow("s3:*", "arn:aws:s3:::shortly-assets/*"), deny("s3:DeleteObject")]
    assert evaluate_policies(policies, req("s3:GetObject")) == "Allow"
    assert evaluate_policies(policies, req("s3:DeleteObject")) == "ExplicitDeny"
    assert evaluate_policies(policies, req("ec2:RunInstances", "*")) == "ImplicitDeny"
    assert evaluate_policies([], req()) == "ImplicitDeny"


def test_evaluate_scp_levels_each_must_allow():
    identity = [FULL]
    assert evaluate(req(), identity=identity, scps=[[FULL], [FULL]]) == "Allow"
    assert evaluate(req(), identity=identity, scps=[[FULL], [allow("ec2:*")]]) == "ImplicitDeny"
    assert evaluate(req(), identity=identity, scps=[[FULL], [FULL, deny("s3:*")]]) == "ExplicitDeny"
    assert evaluate(req(), identity=[], scps=[[FULL]]) == "ImplicitDeny"  # SCPs never grant


def test_evaluate_boundary_and_session_limit():
    identity = [allow(["s3:*", "ec2:*"])]
    assert evaluate(req("ec2:RunInstances", "*"), identity=identity, boundary=allow("s3:*")) == "ImplicitDeny"
    assert evaluate(req("s3:GetObject"), identity=identity, boundary=allow("s3:*")) == "Allow"
    assert evaluate(req("s3:GetObject"), identity=identity, session=allow("s3:List*")) == "ImplicitDeny"


def test_evaluate_same_account_resource_policy_is_enough():
    bucket_policy = {"Statement": [{"Effect": "Allow", "Principal": {"AWS": ROLE}, "Action": "s3:GetObject",
                                    "Resource": "arn:aws:s3:::shortly-assets/*"}]}
    assert evaluate(req(), identity=[], resource_policy=bucket_policy, resource_account=A) == "Allow"


def test_evaluate_cross_account_needs_both_sides():
    caller = f"arn:aws:iam::{B}:role/partner"
    bucket_policy = {"Statement": [{"Effect": "Allow", "Principal": {"AWS": f"arn:aws:iam::{B}:root"},
                                    "Action": "s3:GetObject", "Resource": "arn:aws:s3:::shortly-assets/*"}]}
    identity = [allow("s3:GetObject", "arn:aws:s3:::shortly-assets/*")]
    assert evaluate(req(principal=caller), identity=identity, resource_account=A) == "ImplicitDeny"
    assert evaluate(req(principal=caller), identity=[], resource_policy=bucket_policy, resource_account=A) == "ImplicitDeny"
    assert evaluate(req(principal=caller), identity=identity, resource_policy=bucket_policy, resource_account=A) == "Allow"


def test_evaluate_resource_policy_explicit_deny_wins():
    bucket_policy = {"Statement": [{"Effect": "Deny", "Principal": "*", "Action": "s3:*", "Resource": "*",
                                    "Condition": {"Bool": {"aws:SecureTransport": "false"}}}]}
    identity = [allow("s3:GetObject")]
    assert evaluate(req(**{"aws:SecureTransport": False}), identity=identity, resource_policy=bucket_policy) == "ExplicitDeny"
    assert evaluate(req(**{"aws:SecureTransport": True}), identity=identity, resource_policy=bucket_policy) == "Allow"


def test_evaluate_trust_external_id_and_mfa():
    trust = {"Statement": [{"Effect": "Allow", "Principal": {"AWS": f"arn:aws:iam::{B}:root"},
                            "Action": "sts:AssumeRole",
                            "Condition": {"StringEquals": {"sts:ExternalId": "shortly-ext-42"}}}]}
    partner = f"arn:aws:iam::{B}:role/partner"
    assert evaluate_trust(trust, partner, {"sts:ExternalId": "shortly-ext-42"})
    assert not evaluate_trust(trust, partner, {"sts:ExternalId": "guess"})
    assert not evaluate_trust(trust, partner)
    assert not evaluate_trust(trust, ROLE, {"sts:ExternalId": "shortly-ext-42"})


def test_decide_resource_policy_matches_service_principals():
    from _harness.awslib.policy_eval import decide_resource_policy
    elb = "logdelivery.elasticloadbalancing.amazonaws.com"
    policy = {"Statement": [
        {"Effect": "Allow", "Principal": {"Service": elb}, "Action": "s3:PutObject", "Resource": "arn:aws:s3:::logs/alb/*"},
        {"Effect": "Deny", "Principal": "*", "Action": "s3:*", "Resource": "arn:aws:s3:::logs/*",
         "Condition": {"Bool": {"aws:SecureTransport": "false"}}}]}

    def r(principal=elb, resource="arn:aws:s3:::logs/alb/x", **ctx):
        return Request(principal=principal, action="s3:PutObject", resource=resource, context=ctx)
    assert decide_resource_policy(policy, r()) == "Allow"
    assert decide_resource_policy(policy, r(resource="arn:aws:s3:::logs/other/x")) == "ImplicitDeny"
    assert decide_resource_policy(policy, r(principal=ROLE)) == "ImplicitDeny"
    assert decide_resource_policy(policy, r(**{"aws:SecureTransport": False})) == "ExplicitDeny"
    assert decide_resource_policy({"Statement": []}, r()) == "ImplicitDeny"
````

### `_dev/tests/test_milestone_tools.py`

````python
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
MARKER = "MILESTONE_JSON "


def fake_course(tmp_path) -> Path:
    """A course folder with the real tools and helpers and a two-step milestone M01."""
    course = tmp_path / "course"
    shutil.copytree(ROOT / "course_project" / "tools", course / "course_project" / "tools")
    shutil.copytree(ROOT / "_harness" / "awslib", course / "_harness" / "awslib",
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "course_project" / "app", course / "course_project" / "app", ignore=shutil.ignore_patterns("__pycache__"))
    tests = course / "course_project" / "tests" / "m01"
    tests.mkdir(parents=True)
    (tests / "test_m01_1_readme.py").write_text(
        "def test_readme(repo):\n    assert (repo / 'README.md').exists(), 'add README.md'\n", encoding="utf-8")
    (tests / "test_m01_2_creds.py").write_text(
        "import os\n\ndef test_fake_credentials():\n    assert os.environ['AWS_ACCESS_KEY_ID'] == 'testing'\n"
        "    assert 'AWS_PROFILE' not in os.environ\n", encoding="utf-8")
    return course


def start(course, repo, n=1, env=None):
    return subprocess.run([PY, str(course / "course_project" / "tools" / "start_milestone.py"), str(n), "--repo", str(repo)],
                          capture_output=True, text=True, encoding="utf-8", env=env, timeout=120)


def run(repo, n=1, env=None):
    proc = subprocess.run([PY, "run_milestone.py", str(n), "--json"], cwd=repo, capture_output=True, text=True,
                          encoding="utf-8", env=env, timeout=300)
    line = [l for l in proc.stdout.splitlines() if l.startswith(MARKER)]
    return proc, (json.loads(line[-1][len(MARKER):]) if line else None)


def test_start_copies_tests_conftest_runner_and_helpers(tmp_path):
    course = fake_course(tmp_path)
    repo = tmp_path / "my infra repo"
    repo.mkdir()
    proc = start(course, repo)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    for rel in ("tests/m01/test_m01_1_readme.py", "tests/conftest.py", "run_milestone.py",
                "tests/_course/__init__.py", "tests/_course/cfn.py", "tests/_course/policy_eval.py", "tests/_course/safety.py"):
        assert (repo / rel).exists(), rel
    assert "M01.md" in proc.stdout


def test_start_copies_model_helpers_and_the_app_from_milestone_3(tmp_path):
    course = fake_course(tmp_path)
    for n in (2, 3):
        folder = course / "course_project" / "tests" / f"m0{n}"
        folder.mkdir()
        (folder / f"test_m0{n}_1_x.py").write_text("def test_x():\n    pass\n", encoding="utf-8")
    repo = tmp_path / "repo"
    repo.mkdir()
    proc = start(course, repo, n=2)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert not (repo / "app").exists(), "M02 must not create app/"
    for name in ("ec2types.py", "elb.py", "scaling.py", "purchasing.py", "prices.py", "prices.toml"):
        assert (repo / "tests" / "_course" / name).exists(), name
    for name in ("s3cost.py", "lifecycle.py", "ebs.py", "dynamo.py", "caching.py", "dbmath.py"):
        assert (repo / "tests" / "_course" / name).exists(), name
    proc = start(course, repo, n=3)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (repo / "app" / "app.py").exists() and "app/" in proc.stdout
    (repo / "app" / "app.py").write_text("changed", encoding="utf-8")
    assert start(course, repo, n=3).returncode == 0
    assert "changed" not in (repo / "app" / "app.py").read_text(encoding="utf-8"), "app/ is overwritten"


def test_start_expands_home(tmp_path):
    course = fake_course(tmp_path)
    home = tmp_path / "home"
    (home / "code" / "shortly-infra").mkdir(parents=True)
    env = dict(os.environ, USERPROFILE=str(home), HOME=str(home))
    proc = start(course, "~/code/shortly-infra", env=env)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (home / "code" / "shortly-infra" / "run_milestone.py").exists()


def test_start_unknown_milestone_and_missing_repo(tmp_path):
    course = fake_course(tmp_path)
    proc = start(course, tmp_path, n=7)
    assert proc.returncode == 2 and "There are no tests for M07" in proc.stdout
    proc = start(course, tmp_path / "nope")
    assert proc.returncode == 2 and "does not exist" in proc.stdout


def test_run_reports_steps_and_conftest_forces_fake_credentials(tmp_path):
    course = fake_course(tmp_path)
    repo = tmp_path / "repo"
    repo.mkdir()
    start(course, repo)
    env = dict(os.environ, AWS_PROFILE="work", AWS_ACCESS_KEY_ID="AKIAREALKEY")
    env.pop("PYTHONIOENCODING", None)
    proc, data = run(repo, env=env)
    assert data["steps"]["M01.1"]["green"] is False and "add README.md" in data["steps"]["M01.1"]["reason"]
    assert data["steps"]["M01.2"]["green"] is True   # test_conftest_forces_fake_credentials
    assert "✘ M01.1 readme" in proc.stdout and proc.returncode == 1
    (repo / "README.md").write_text("# shortly-infra\n", encoding="utf-8")
    proc, data = run(repo, env=env)
    assert proc.returncode == 0 and all(s["green"] for s in data["steps"].values())


def test_run_missing_earlier_milestone(tmp_path):
    course = fake_course(tmp_path)
    repo = tmp_path / "repo"
    repo.mkdir()
    start(course, repo)
    proc, _ = run(repo, n=2)
    assert proc.returncode == 2 and "tests/m02 is missing" in proc.stdout


def test_conftest_fixtures_load_render_and_evaluate(tmp_path):
    course = fake_course(tmp_path)
    repo = tmp_path / "repo"
    (repo / "infra").mkdir(parents=True)
    (repo / "README.md").write_text("x", encoding="utf-8")
    (repo / "infra" / "iam.yaml").write_text(
        "AWSTemplateFormatVersion: '2010-09-09'\nParameters:\n  Prefix: {Type: String}\n  Env: {Type: String}\n"
        "Resources:\n  AppRole:\n    Type: AWS::IAM::Role\n    Properties:\n      RoleName: !Sub '${Prefix}-app'\n"
        "      AssumeRolePolicyDocument:\n        Version: '2012-10-17'\n        Statement:\n"
        "          - {Effect: Allow, Principal: {Service: ec2.amazonaws.com}, Action: 'sts:AssumeRole'}\n"
        "      Policies:\n        - PolicyName: app\n          PolicyDocument:\n            Version: '2012-10-17'\n"
        "            Statement:\n              - Effect: Allow\n                Action: sqs:SendMessage\n"
        "                Resource: !Sub 'arn:aws:sqs:${AWS::Region}:${AWS::AccountId}:${Prefix}-clicks'\n",
        encoding="utf-8")
    tests = course / "course_project" / "tests" / "m01"
    (tests / "test_m01_3_fixtures.py").write_text(
        "def test_fixtures(template, lint_errors, role_policies, evaluator, moto_stacks):\n"
        "    assert 'AppRole' in template('iam')['Resources']\n"
        "    assert lint_errors('iam') == []\n"
        "    req = evaluator.Request(principal='arn:aws:iam::111122223333:role/shortly-app', action='sqs:SendMessage',\n"
        "                            resource='arn:aws:sqs:us-east-1:111122223333:shortly-clicks')\n"
        "    assert evaluator.evaluate_policies(role_policies('iam', 'AppRole'), req) == 'Allow'\n"
        "    assert moto_stacks('iam') == 'CREATE_COMPLETE'\n", encoding="utf-8")
    start(course, repo)
    proc, data = run(repo)
    assert data["steps"]["M01.3"]["green"], data["steps"]["M01.3"]["reason"]


def test_verify_milestone_good_starting_and_mutant(tmp_path):
    course = fake_course(tmp_path)
    solution = course / "course_project" / "solutions" / "m01"
    solution.mkdir(parents=True)
    (solution / "README.md").write_text("# shortly-infra\n", encoding="utf-8")
    (course / "_dev" / "mutants").mkdir(parents=True)
    (course / "_dev" / "mutants" / "m01.py").write_text(
        "MUTANTS = []\n", encoding="utf-8")
    spec = importlib.util.spec_from_file_location("verify_course", ROOT / "verify_course.py")
    vc = importlib.util.module_from_spec(spec)
    sys.modules["verify_course"] = vc  # dataclasses need the module registered
    spec.loader.exec_module(vc)
    checks = {c.name: c for c in vc.verify_milestone(course, 1, PY)}
    assert checks["solutions/m01 passes run_milestone.py 1"].ok, checks["solutions/m01 passes run_milestone.py 1"].detail
    assert checks["the starting state fails M01"].ok
    assert not checks["_dev/mutants/m01.py has mutants"].ok
    # a mutant that deletes the README is caught
    (course / "_dev" / "mutants" / "m01.py").write_text(
        'MUTANTS = [{"id": "no-title", "edits": {"README.md": [["# shortly-infra", ""]]}, "delete": ["README.md"]}]\n',
        encoding="utf-8")
    checks = {c.name: c for c in vc.verify_milestone(course, 1, PY)}
    assert checks["mutant no-title is caught"].ok
````

### `_dev/tests/test_labclean_compute.py`

````python
import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from _harness import labclean

TAG = [{"Key": "saa-course", "Value": "lab"}]
OTHER = [{"Key": "owner", "Value": "someone-else"}]
WEEK3 = ["autoscaling_groups", "load_balancers", "target_groups", "launch_templates", "ec2_instances", "security_groups"]


@pytest.fixture
def aws(monkeypatch):
    monkeypatch.setattr(labclean, "WAIT_SECONDS", 0)
    with mock_aws():
        yield boto3.Session(region_name="us-east-1")


def run(aws, kinds, *args):
    return labclean.main(kinds, argv=list(args), session_factory=lambda **kw: aws)


def tags(on, resource_type):
    return [{"ResourceType": resource_type, "Tags": TAG if on else OTHER}]


def vpc_and_subnets(ec2):
    vpc = ec2.describe_vpcs(Filters=[{"Name": "is-default", "Values": ["true"]}])["Vpcs"][0]["VpcId"]
    subnets = [s["SubnetId"] for s in ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc]}])["Subnets"]][:2]
    return vpc, subnets


def make_sg(ec2, vpc, name, tagged):
    return ec2.create_security_group(GroupName=name, Description=name, VpcId=vpc,
                                     TagSpecifications=tags(tagged, "security-group"))["GroupId"]


def make_lt(ec2, name, tagged):
    ami = ec2.describe_images()["Images"][0]["ImageId"]
    return ec2.create_launch_template(LaunchTemplateName=name, LaunchTemplateData={"ImageId": ami, "InstanceType": "t3.micro"},
                                      TagSpecifications=tags(tagged, "launch-template"))["LaunchTemplate"]["LaunchTemplateId"]


def make_asg(aws, name, lt_id, subnets, tagged, tg_arns=()):
    aws.client("autoscaling").create_auto_scaling_group(
        AutoScalingGroupName=name, LaunchTemplate={"LaunchTemplateId": lt_id, "Version": "$Latest"},
        MinSize=1, MaxSize=2, DesiredCapacity=1, VPCZoneIdentifier=",".join(subnets), TargetGroupARNs=list(tg_arns),
        Tags=[{"Key": k["Key"], "Value": k["Value"], "PropagateAtLaunch": True} for k in (TAG if tagged else OTHER)])


def make_tg(elb, name, vpc, tagged):
    return elb.create_target_group(Name=name, Protocol="HTTP", Port=80, VpcId=vpc, Tags=TAG if tagged else OTHER)["TargetGroups"][0]["TargetGroupArn"]


def make_lb(elb, name, subnets, sgs, tagged):
    return elb.create_load_balancer(Name=name, Subnets=subnets, SecurityGroups=sgs, Tags=TAG if tagged else OTHER)["LoadBalancers"][0]["LoadBalancerArn"]


def lb_names(elb):
    return {lb["LoadBalancerName"] for lb in elb.describe_load_balancers()["LoadBalancers"]}


def sg_ids(ec2):
    return {g["GroupId"] for g in ec2.describe_security_groups()["SecurityGroups"] if g["GroupName"] != "default"}


# -- one kind at a time: tagged goes, untagged twin stays --


def test_asg_tagged_deleted_untagged_kept(aws):
    ec2, asg = aws.client("ec2"), aws.client("autoscaling")
    _, subnets = vpc_and_subnets(ec2)
    lt = make_lt(ec2, "lt", True)
    make_asg(aws, "mine", lt, subnets, True)
    make_asg(aws, "theirs", lt, subnets, False)
    assert run(aws, ["autoscaling_groups"], "--yes") == 0
    assert [g["AutoScalingGroupName"] for g in asg.describe_auto_scaling_groups()["AutoScalingGroups"]] == ["theirs"]


def test_load_balancer_tagged_deleted_untagged_kept(aws):
    ec2, elb = aws.client("ec2"), aws.client("elbv2")
    _, subnets = vpc_and_subnets(ec2)
    make_lb(elb, "mine", subnets, [], True)
    make_lb(elb, "theirs", subnets, [], False)
    assert run(aws, ["load_balancers"], "--yes") == 0
    assert lb_names(elb) == {"theirs"}


def test_load_balancer_tags_read_in_batches_of_at_most_20(aws, monkeypatch):
    ec2, elb = aws.client("ec2"), aws.client("elbv2")
    _, subnets = vpc_and_subnets(ec2)
    for i in range(23):
        make_lb(elb, f"lb{i:02d}", subnets, [], tagged=(i % 2 == 0))
    sizes = []

    class Spy:
        def __init__(self, client):
            self._client = client

        def describe_tags(self, **kw):
            sizes.append(len(kw["ResourceArns"]))
            return self._client.describe_tags(**kw)

        def __getattr__(self, name):
            return getattr(self._client, name)

    class SpySession:
        def client(self, *a, **kw):
            return Spy(aws.client(*a, **kw))

    found = labclean.find_load_balancers(SpySession(), "us-east-1")
    assert len(found) == 12
    assert sorted(sizes) == [3, 20]


def test_target_group_tagged_deleted_untagged_kept(aws):
    ec2, elb = aws.client("ec2"), aws.client("elbv2")
    vpc, _ = vpc_and_subnets(ec2)
    make_tg(elb, "mine", vpc, True)
    make_tg(elb, "theirs", vpc, False)
    assert run(aws, ["target_groups"], "--yes") == 0
    assert [t["TargetGroupName"] for t in elb.describe_target_groups()["TargetGroups"]] == ["theirs"]


def test_launch_template_tagged_deleted_untagged_kept(aws):
    ec2 = aws.client("ec2")
    make_lt(ec2, "mine", True)
    make_lt(ec2, "theirs", False)
    assert run(aws, ["launch_templates"], "--yes") == 0
    assert [t["LaunchTemplateName"] for t in ec2.describe_launch_templates()["LaunchTemplates"]] == ["theirs"]


def test_security_group_tagged_deleted_untagged_kept_default_untouched(aws):
    ec2 = aws.client("ec2")
    vpc, _ = vpc_and_subnets(ec2)
    make_sg(ec2, vpc, "mine", True)
    theirs = make_sg(ec2, vpc, "theirs", False)
    default = ec2.describe_security_groups(Filters=[{"Name": "group-name", "Values": ["default"]}])["SecurityGroups"][0]["GroupId"]
    ec2.create_tags(Resources=[default], Tags=TAG)  # even a (mis)tagged default group is never deleted
    assert run(aws, ["security_groups"], "--yes") == 0
    assert sg_ids(ec2) == {theirs}
    assert default in {g["GroupId"] for g in ec2.describe_security_groups()["SecurityGroups"]}


def test_security_groups_are_one_item_and_none_means_no_item(aws):
    ec2 = aws.client("ec2")
    assert labclean.find_security_groups(aws, "us-east-1") == []
    vpc, _ = vpc_and_subnets(ec2)
    a, b = make_sg(ec2, vpc, "a", True), make_sg(ec2, vpc, "b", True)
    items = labclean.find_security_groups(aws, "us-east-1")
    assert len(items) == 1 and items[0].kind == "security_groups"
    assert a in items[0].name and b in items[0].name


# -- dry run --


def test_dry_run_deletes_nothing_and_lists_everything(aws, capsys):
    ec2, elb, asg = aws.client("ec2"), aws.client("elbv2"), aws.client("autoscaling")
    vpc, subnets = vpc_and_subnets(ec2)
    sg = make_sg(ec2, vpc, "mine-sg", True)
    lt = make_lt(ec2, "mine-lt", True)
    tg = make_tg(elb, "mine-tg", vpc, True)
    make_lb(elb, "mine-lb", subnets, [sg], True)
    make_asg(aws, "mine-asg", lt, subnets, True)
    assert run(aws, WEEK3) == 0
    out = capsys.readouterr().out
    assert "DRY RUN" in out
    for needle in ("mine-asg", "mine-lb", "mine-tg", "mine-lt", sg):
        assert needle in out
    assert lb_names(elb) == {"mine-lb"}
    assert len(asg.describe_auto_scaling_groups()["AutoScalingGroups"]) == 1
    assert len(elb.describe_target_groups(TargetGroupArns=[tg])["TargetGroups"]) == 1
    assert len(ec2.describe_launch_templates()["LaunchTemplates"]) == 1
    assert sg in sg_ids(ec2)


# -- security groups that reference each other --


def test_two_tagged_groups_referencing_each_other_are_both_deleted(aws):
    ec2 = aws.client("ec2")
    vpc, _ = vpc_and_subnets(ec2)
    alb, app = make_sg(ec2, vpc, "alb", True), make_sg(ec2, vpc, "app", True)
    for target, source in ((app, alb), (alb, app)):  # a cycle
        ec2.authorize_security_group_ingress(GroupId=target, IpPermissions=[
            {"IpProtocol": "tcp", "FromPort": 80, "ToPort": 80, "UserIdGroupPairs": [{"GroupId": source}]}])
    # moto does not enforce DependencyViolation for referenced groups, so this proves the end state only
    assert run(aws, ["security_groups"], "--yes") == 0
    assert sg_ids(ec2) == set()


def test_untagged_group_referenced_by_tagged_group_survives(aws):
    ec2 = aws.client("ec2")
    vpc, _ = vpc_and_subnets(ec2)
    mine, theirs = make_sg(ec2, vpc, "mine", True), make_sg(ec2, vpc, "theirs", False)
    ec2.authorize_security_group_ingress(GroupId=mine, IpPermissions=[
        {"IpProtocol": "tcp", "FromPort": 80, "ToPort": 80, "UserIdGroupPairs": [{"GroupId": theirs}]}])
    ec2.authorize_security_group_ingress(GroupId=theirs, IpPermissions=[
        {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "10.0.0.0/8"}]}])
    before = ec2.describe_security_groups(GroupIds=[theirs])["SecurityGroups"][0]["IpPermissions"]
    assert run(aws, ["security_groups"], "--yes") == 0
    assert sg_ids(ec2) == {theirs}
    assert ec2.describe_security_groups(GroupIds=[theirs])["SecurityGroups"][0]["IpPermissions"] == before  # rules intact


def test_security_group_delete_retries_on_dependency_violation(aws, monkeypatch):
    ec2 = aws.client("ec2")
    vpc, _ = vpc_and_subnets(ec2)
    sg = make_sg(ec2, vpc, "mine", True)
    real = ec2.delete_security_group
    calls = []

    def flaky(**kw):
        calls.append(1)
        if len(calls) < 3:
            raise ClientError({"Error": {"Code": "DependencyViolation", "Message": "in use"}}, "DeleteSecurityGroup")
        return real(**kw)
    monkeypatch.setattr(ec2, "delete_security_group", flaky)
    labclean._delete_security_groups(ec2, [sg])
    assert len(calls) == 3 and sg not in sg_ids(ec2)


def test_security_group_delete_gives_up_with_timeout(aws, monkeypatch):
    ec2 = aws.client("ec2")
    vpc, _ = vpc_and_subnets(ec2)
    sg = make_sg(ec2, vpc, "mine", True)
    monkeypatch.setattr(labclean, "WAIT_ATTEMPTS", 3)

    def stuck(**kw):
        raise ClientError({"Error": {"Code": "DependencyViolation", "Message": "in use"}}, "DeleteSecurityGroup")
    monkeypatch.setattr(ec2, "delete_security_group", stuck)
    with pytest.raises(TimeoutError):
        labclean._delete_security_groups(ec2, [sg])


# -- the whole week 03 lab --


def test_full_week03_order_end_to_end(aws):
    ec2, elb, asg = aws.client("ec2"), aws.client("elbv2"), aws.client("autoscaling")
    vpc, subnets = vpc_and_subnets(ec2)
    stacks = {}
    for label, tagged in (("mine", True), ("theirs", False)):
        alb_sg, app_sg = make_sg(ec2, vpc, f"{label}-alb", tagged), make_sg(ec2, vpc, f"{label}-app", tagged)
        ec2.authorize_security_group_ingress(GroupId=app_sg, IpPermissions=[
            {"IpProtocol": "tcp", "FromPort": 80, "ToPort": 80, "UserIdGroupPairs": [{"GroupId": alb_sg}]}])
        lt = make_lt(ec2, f"{label}-lt", tagged)
        tg = make_tg(elb, f"{label}-tg", vpc, tagged)
        lb = make_lb(elb, f"{label}-lb", subnets, [alb_sg], tagged)
        elb.create_listener(LoadBalancerArn=lb, Protocol="HTTP", Port=80,
                            DefaultActions=[{"Type": "forward", "TargetGroupArn": tg}])
        make_asg(aws, f"{label}-asg", lt, subnets, tagged, [tg])
        stacks[label] = {"sgs": {alb_sg, app_sg}}
    instances = {}
    for reservation in ec2.describe_instances()["Reservations"]:
        for inst in reservation["Instances"]:
            instances[inst["InstanceId"]] = {t["Key"]: t["Value"] for t in inst.get("Tags", [])}
    mine_instances = [i for i, t in instances.items() if t.get("saa-course") == "lab"]
    theirs_instances = [i for i in instances if i not in mine_instances]
    assert mine_instances and theirs_instances  # moto propagates the ASG tags to its instances

    assert run(aws, WEEK3, "--yes") == 0

    assert [g["AutoScalingGroupName"] for g in asg.describe_auto_scaling_groups()["AutoScalingGroups"]] == ["theirs-asg"]
    assert lb_names(elb) == {"theirs-lb"}
    assert [t["TargetGroupName"] for t in elb.describe_target_groups()["TargetGroups"]] == ["theirs-tg"]
    assert [t["LaunchTemplateName"] for t in ec2.describe_launch_templates()["LaunchTemplates"]] == ["theirs-lt"]
    assert sg_ids(ec2) == stacks["theirs"]["sgs"]
    state = {i["InstanceId"]: i["State"]["Name"] for r in ec2.describe_instances()["Reservations"] for i in r["Instances"]}
    assert all(state[i] == "terminated" for i in mine_instances)
    assert all(state[i] != "terminated" for i in theirs_instances)
    assert run(aws, WEEK3, "--yes") == 0  # a second run finds nothing left of ours


def test_finders_order_for_week03():
    week03 = ["s3_buckets", "autoscaling_groups", "load_balancers", "target_groups", "ec2_instances", "launch_templates",
              "nat_gateways", "elastic_ips", "security_groups", "vpcs", "iam_roles", "iam_users", "iam_policies"]
    assert [k for k in labclean.FINDERS if k in week03] == week03, "later weeks may add kinds, but never reorder these"


def test_unknown_kind_rejected(aws):
    with pytest.raises(ValueError, match="unknown resource kind"):
        run(aws, ["load_balancers", "lambda_functions"])
````

### `_dev/tests/test_labclean_storage_db.py`

````python
import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from _harness import labclean

TAG = [{"Key": "saa-course", "Value": "lab"}]
OTHER = [{"Key": "owner", "Value": "someone-else"}]
WEEK4 = ["s3_buckets", "ebs_snapshots", "ebs_volumes"]
WEEK5 = ["dynamodb_tables", "dynamodb_backups", "rds_instances", "rds_snapshots", "db_subnet_groups"]
AZ = "us-east-1a"


@pytest.fixture
def aws(monkeypatch):
    monkeypatch.setattr(labclean, "WAIT_SECONDS", 0)
    with mock_aws():
        yield boto3.Session(region_name="us-east-1")


def run(aws, kinds, *args):
    return labclean.main(kinds, argv=list(args), session_factory=lambda **kw: aws)


def tags(on):
    return TAG if on else OTHER


def api_error(code, op):
    return ClientError({"Error": {"Code": code, "Message": code}}, op)


# -- builders --


def make_bucket(s3, name, on):
    s3.create_bucket(Bucket=name)
    s3.put_bucket_tagging(Bucket=name, Tagging={"TagSet": tags(on)})


def bucket_names(s3):
    return {b["Name"] for b in s3.list_buckets()["Buckets"]}


def make_volume(ec2, on):
    return ec2.create_volume(AvailabilityZone=AZ, Size=8, VolumeType="gp3",
                             TagSpecifications=[{"ResourceType": "volume", "Tags": tags(on)}])["VolumeId"]


def make_instance(ec2, on):
    ami = ec2.describe_images()["Images"][0]["ImageId"]
    return ec2.run_instances(ImageId=ami, InstanceType="t3.micro", MinCount=1, MaxCount=1, Placement={"AvailabilityZone": AZ},
                             TagSpecifications=[{"ResourceType": "instance", "Tags": tags(on)}])["Instances"][0]["InstanceId"]


def volume_ids(ec2):
    return {v["VolumeId"] for v in ec2.describe_volumes(Filters=[{"Name": "tag-key", "Values": ["saa-course", "owner"]}])["Volumes"]}


def make_snapshot(ec2, volume, on):
    return ec2.create_snapshot(VolumeId=volume, TagSpecifications=[{"ResourceType": "snapshot", "Tags": tags(on)}])["SnapshotId"]


def snapshot_exists(ec2, sid):
    return bool(ec2.describe_snapshots(SnapshotIds=[sid])["Snapshots"]) if _exists(lambda: ec2.describe_snapshots(SnapshotIds=[sid])) else False


def _exists(call):
    try:
        call()
        return True
    except ClientError:
        return False


def make_table(ddb, name, on, protected=False):
    ddb.create_table(TableName=name, BillingMode="PAY_PER_REQUEST", DeletionProtectionEnabled=protected,
                     AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"}],
                     KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}], Tags=tags(on))


def table_names(ddb):
    return set(ddb.list_tables()["TableNames"])


def make_db(rds, name, on, protected=False):
    rds.create_db_instance(DBInstanceIdentifier=name, Engine="postgres", DBInstanceClass="db.t4g.micro", AllocatedStorage=20,
                           MasterUsername="admin1", MasterUserPassword="password-1234", DeletionProtection=protected, Tags=tags(on))


def db_names(rds):
    return {d["DBInstanceIdentifier"] for d in rds.describe_db_instances()["DBInstances"]}


def make_subnet_group(aws, name, on):
    ec2, rds = aws.client("ec2"), aws.client("rds")
    vpc = ec2.describe_vpcs(Filters=[{"Name": "is-default", "Values": ["true"]}])["Vpcs"][0]["VpcId"]
    subnets = [s["SubnetId"] for s in ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc]}])["Subnets"]][:2]
    rds.create_db_subnet_group(DBSubnetGroupName=name, DBSubnetGroupDescription=name, SubnetIds=subnets, Tags=tags(on))


def subnet_group_names(rds):
    return {g["DBSubnetGroupName"] for g in rds.describe_db_subnet_groups()["DBSubnetGroups"]}


# ======================= S3 (week 04) =======================


def test_bucket_with_unfinished_multipart_upload_is_deleted(aws):
    s3 = aws.client("s3")
    make_bucket(s3, "mine", True)
    make_bucket(s3, "theirs", False)
    s3.create_multipart_upload(Bucket="mine", Key="big.bin")
    s3.create_multipart_upload(Bucket="theirs", Key="big.bin")
    assert run(aws, ["s3_buckets"], "--yes") == 0
    assert bucket_names(s3) == {"theirs"}
    assert len(s3.list_multipart_uploads(Bucket="theirs").get("Uploads", [])) == 1  # their upload untouched


def test_multipart_uploads_are_aborted_before_the_bucket_goes(aws):
    s3 = aws.client("s3")
    make_bucket(s3, "mine", True)
    s3.create_multipart_upload(Bucket="mine", Key="a")
    s3.create_multipart_upload(Bucket="mine", Key="b")
    aborted = []
    real = s3.abort_multipart_upload
    s3.abort_multipart_upload = lambda **kw: (aborted.append(kw["Key"]), real(**kw))[1]
    labclean._delete_bucket(s3, "mine")
    assert sorted(aborted) == ["a", "b"] and bucket_names(s3) == set()


def test_versioned_bucket_still_emptied(aws):
    s3 = aws.client("s3")
    make_bucket(s3, "mine", True)
    s3.put_bucket_versioning(Bucket="mine", VersioningConfiguration={"Status": "Enabled"})
    for _ in range(3):
        s3.put_object(Bucket="mine", Key="k", Body=b"x")
    s3.delete_object(Bucket="mine", Key="k")
    assert run(aws, ["s3_buckets"], "--yes") == 0
    assert bucket_names(s3) == set()


def test_object_lock_bucket_is_reported_not_failed_obscurely(aws, capsys):
    s3 = aws.client("s3")
    s3.create_bucket(Bucket="locked", ObjectLockEnabledForBucket=True)
    s3.put_bucket_tagging(Bucket="locked", Tagging={"TagSet": TAG})
    s3.put_object(Bucket="locked", Key="k", Body=b"x", ObjectLockMode="COMPLIANCE",
                  ObjectLockRetainUntilDate=__import__("datetime").datetime(2099, 1, 1))
    assert run(aws, ["s3_buckets"], "--yes") == 1
    out = capsys.readouterr().out
    assert "Object Lock" in out and "locked" in out and "left in place" in out
    assert bucket_names(s3) == {"locked"}
    assert len(s3.list_object_versions(Bucket="locked")["Versions"]) == 1


def test_object_lock_bucket_without_locked_objects_is_deleted(aws):
    s3 = aws.client("s3")
    s3.create_bucket(Bucket="lockable", ObjectLockEnabledForBucket=True)
    s3.put_bucket_tagging(Bucket="lockable", Tagging={"TagSet": TAG})
    s3.put_object(Bucket="lockable", Key="k", Body=b"x")
    assert run(aws, ["s3_buckets"], "--yes") == 0
    assert bucket_names(s3) == set()


# ======================= EBS volumes (week 04) =======================


def test_volume_tagged_deleted_untagged_kept(aws):
    ec2 = aws.client("ec2")
    mine, theirs = make_volume(ec2, True), make_volume(ec2, False)
    assert run(aws, ["ebs_volumes"], "--yes") == 0
    assert volume_ids(ec2) == {theirs} and mine not in volume_ids(ec2)


def test_volume_dry_run_lists_and_deletes_nothing(aws, capsys):
    ec2 = aws.client("ec2")
    mine = make_volume(ec2, True)
    assert run(aws, ["ebs_volumes"]) == 0
    out = capsys.readouterr().out
    assert "DRY RUN" in out and mine in out
    assert volume_ids(ec2) == {mine}


def test_attached_volume_on_untagged_instance_is_left_alone_and_reported(aws, capsys):
    ec2 = aws.client("ec2")
    instance = make_instance(ec2, False)
    volume = make_volume(ec2, True)
    ec2.attach_volume(VolumeId=volume, InstanceId=instance, Device="/dev/sdf")
    assert run(aws, ["ebs_volumes"]) == 0  # the dry run already warns
    assert "WILL BE LEFT IN PLACE" in capsys.readouterr().out
    assert run(aws, ["ebs_volumes"], "--yes") == 1
    out = capsys.readouterr().out
    assert "left in place" in out and instance in out
    info = ec2.describe_volumes(VolumeIds=[volume])["Volumes"][0]
    assert info["State"] == "in-use" and info["Attachments"][0]["InstanceId"] == instance  # never detached


def test_attached_volume_on_tagged_instance_is_detached_then_deleted(aws):
    ec2 = aws.client("ec2")
    instance = make_instance(ec2, True)
    volume = make_volume(ec2, True)
    ec2.attach_volume(VolumeId=volume, InstanceId=instance, Device="/dev/sdf")
    assert run(aws, ["ebs_volumes"], "--yes") == 0
    assert volume not in volume_ids(ec2)
    state = ec2.describe_instances(InstanceIds=[instance])["Reservations"][0]["Instances"][0]["State"]["Name"]
    assert state == "running"  # the instance itself is not this kind's business


def test_root_disk_of_a_tagged_instance_is_not_detached(aws):
    ec2 = aws.client("ec2")
    instance = make_instance(ec2, True)
    root = ec2.describe_instances(InstanceIds=[instance])["Reservations"][0]["Instances"][0]["RootDeviceName"]
    volume = make_volume(ec2, True)
    ec2.attach_volume(VolumeId=volume, InstanceId=instance, Device=root)
    with pytest.raises(labclean.Blocked, match="root disk"):
        labclean._delete_volume(ec2, volume)


def test_untagged_volume_on_untagged_instance_never_listed(aws):
    ec2 = aws.client("ec2")
    instance = make_instance(ec2, False)
    volume = make_volume(ec2, False)
    ec2.attach_volume(VolumeId=volume, InstanceId=instance, Device="/dev/sdf")
    assert labclean.find_ebs_volumes(aws, "us-east-1") == []


def test_volume_delete_retries_while_still_detaching(aws, monkeypatch):
    ec2 = aws.client("ec2")
    volume = make_volume(ec2, True)
    real, calls = ec2.delete_volume, []

    def flaky(**kw):
        calls.append(1)
        if len(calls) < 3:
            raise api_error("VolumeInUse", "DeleteVolume")
        return real(**kw)
    monkeypatch.setattr(ec2, "delete_volume", flaky)
    labclean._delete_volume(ec2, volume)
    assert len(calls) == 3 and volume not in volume_ids(ec2)


def test_volume_delete_gives_up_with_timeout(aws, monkeypatch):
    ec2 = aws.client("ec2")
    volume = make_volume(ec2, True)
    monkeypatch.setattr(labclean, "WAIT_ATTEMPTS", 3)
    monkeypatch.setattr(ec2, "delete_volume", lambda **kw: (_ for _ in ()).throw(api_error("VolumeInUse", "DeleteVolume")))
    with pytest.raises(TimeoutError):
        labclean._delete_volume(ec2, volume)


def test_volume_untagged_in_the_meantime_is_not_deleted(aws):
    ec2 = aws.client("ec2")
    volume = make_volume(ec2, True)
    ec2.delete_tags(Resources=[volume], Tags=TAG)  # someone removed the tag between listing and deleting
    with pytest.raises(labclean.Blocked):
        labclean._delete_volume(ec2, volume)
    assert ec2.describe_volumes(VolumeIds=[volume])["Volumes"]


# ======================= EBS snapshots (week 04) =======================


def test_snapshot_tagged_deleted_untagged_and_foreign_kept(aws):
    ec2 = aws.client("ec2")
    vol = make_volume(ec2, False)
    mine, theirs = make_snapshot(ec2, vol, True), make_snapshot(ec2, vol, False)
    before = len(ec2.describe_snapshots()["Snapshots"])  # includes moto's pre-bundled public snapshots
    assert run(aws, ["ebs_snapshots"], "--yes") == 0
    assert len(ec2.describe_snapshots()["Snapshots"]) == before - 1
    assert ec2.describe_snapshots(SnapshotIds=[theirs])["Snapshots"]
    with pytest.raises(ClientError):
        ec2.describe_snapshots(SnapshotIds=[mine])


def test_snapshot_dry_run(aws, capsys):
    ec2 = aws.client("ec2")
    snap = make_snapshot(ec2, make_volume(ec2, False), True)
    assert run(aws, ["ebs_snapshots"]) == 0
    assert snap in capsys.readouterr().out
    assert ec2.describe_snapshots(SnapshotIds=[snap])["Snapshots"]


def test_snapshot_used_by_an_image_is_reported_and_kept(aws):
    ec2 = aws.client("ec2")
    snap = make_snapshot(ec2, make_volume(ec2, False), True)
    # moto's register_image drops the snapshot id from the mappings and delete_snapshot ignores images, so the
    # image that really references the snapshot is injected here
    ec2.describe_images = lambda **kw: {"Images": [{"ImageId": "ami-0abc", "BlockDeviceMappings": [
        {"DeviceName": "/dev/sda1", "Ebs": {"SnapshotId": snap}}]}]}
    with pytest.raises(labclean.Blocked, match="ami-0abc"):
        labclean._delete_snapshot(ec2, snap)
    assert ec2.describe_snapshots(SnapshotIds=[snap])["Snapshots"]  # still there


def test_blocked_snapshot_is_reported_by_main_and_other_snapshots_still_go(aws, capsys, monkeypatch):
    ec2 = aws.client("ec2")
    vol = make_volume(ec2, False)
    held, free = make_snapshot(ec2, vol, True), make_snapshot(ec2, vol, True)
    real = labclean._delete_snapshot

    def pick(client, sid):
        if sid == held:
            raise labclean.Blocked(f"snapshot {sid} is used by image ami-0abc")
        real(client, sid)
    monkeypatch.setattr(labclean, "_delete_snapshot", pick)
    assert run(aws, ["ebs_snapshots"], "--yes") == 1
    assert "ami-0abc" in capsys.readouterr().out
    assert ec2.describe_snapshots(SnapshotIds=[held])["Snapshots"]
    with pytest.raises(ClientError):
        ec2.describe_snapshots(SnapshotIds=[free])


def test_snapshot_in_use_error_from_aws_is_reported(aws, monkeypatch):
    ec2 = aws.client("ec2")
    snap = make_snapshot(ec2, make_volume(ec2, False), True)
    monkeypatch.setattr(ec2, "delete_snapshot", lambda **kw: (_ for _ in ()).throw(api_error("InvalidSnapshot.InUse", "DeleteSnapshot")))
    with pytest.raises(labclean.Blocked, match="deregister"):
        labclean._delete_snapshot(ec2, snap)


def test_week04_end_to_end(aws):
    s3, ec2 = aws.client("s3"), aws.client("ec2")
    for label, on in (("mine", True), ("theirs", False)):
        make_bucket(s3, label, on)
        s3.put_bucket_versioning(Bucket=label, VersioningConfiguration={"Status": "Enabled"})
        s3.put_object(Bucket=label, Key="k", Body=b"x")
        s3.create_multipart_upload(Bucket=label, Key="up")
    vols = {on: make_volume(ec2, on) for on in (True, False)}
    snaps = {on: make_snapshot(ec2, vols[on], on) for on in (True, False)}
    assert run(aws, WEEK4) == 0 and bucket_names(s3) == {"mine", "theirs"}  # dry run
    assert run(aws, WEEK4, "--yes") == 0
    assert bucket_names(s3) == {"theirs"}
    assert volume_ids(ec2) == {vols[False]}
    assert ec2.describe_snapshots(SnapshotIds=[snaps[False]])["Snapshots"]
    with pytest.raises(ClientError):
        ec2.describe_snapshots(SnapshotIds=[snaps[True]])
    assert run(aws, WEEK4, "--yes") == 0  # second run finds nothing


# ======================= DynamoDB (week 05) =======================


def test_table_tagged_deleted_untagged_kept(aws):
    ddb = aws.client("dynamodb")
    make_table(ddb, "mine", True)
    make_table(ddb, "theirs", False)
    assert run(aws, ["dynamodb_tables"], "--yes") == 0
    assert table_names(ddb) == {"theirs"}


def test_table_dry_run(aws, capsys):
    ddb = aws.client("dynamodb")
    make_table(ddb, "mine", True)
    assert run(aws, ["dynamodb_tables"]) == 0
    assert "mine" in capsys.readouterr().out and table_names(ddb) == {"mine"}


def test_tagged_table_with_deletion_protection_is_deleted(aws):
    ddb = aws.client("dynamodb")
    make_table(ddb, "mine", True, protected=True)
    assert run(aws, ["dynamodb_tables"], "--yes") == 0
    assert table_names(ddb) == set()


def test_untagged_table_with_deletion_protection_is_untouched(aws):
    ddb = aws.client("dynamodb")
    make_table(ddb, "theirs", False, protected=True)
    make_table(ddb, "mine", True, protected=True)
    assert run(aws, ["dynamodb_tables"], "--yes") == 0
    assert table_names(ddb) == {"theirs"}
    assert ddb.describe_table(TableName="theirs")["Table"]["DeletionProtectionEnabled"] is True  # protection not switched off


def test_table_delete_waits_until_gone(aws, monkeypatch):
    ddb = aws.client("dynamodb")
    make_table(ddb, "mine", True)
    real_delete, real_describe, polls = ddb.delete_table, ddb.describe_table, []
    deleted = []
    monkeypatch.setattr(ddb, "delete_table", lambda **kw: (deleted.append(1), real_delete(**kw))[1])

    def slow(**kw):  # moto deletes at once; AWS shows DELETING for a while
        if deleted:
            polls.append(1)
            if len(polls) < 4:
                return {"Table": {"TableName": kw["TableName"], "TableStatus": "DELETING"}}
        return real_describe(**kw)
    monkeypatch.setattr(ddb, "describe_table", slow)
    labclean._delete_table(ddb, "mine")
    assert len(polls) >= 4 and len(deleted) == 1  # waited, and did not delete twice


def test_table_delete_retries_while_table_is_busy(aws, monkeypatch):
    ddb = aws.client("dynamodb")
    make_table(ddb, "mine", True)
    real, calls = ddb.delete_table, []

    def busy(**kw):
        calls.append(1)
        if len(calls) < 3:
            raise api_error("ResourceInUseException", "DeleteTable")
        return real(**kw)
    monkeypatch.setattr(ddb, "delete_table", busy)
    labclean._delete_table(ddb, "mine")
    assert len(calls) == 3 and table_names(ddb) == set()


def test_table_tag_listing_follows_next_token(aws):
    ddb = aws.client("dynamodb")
    make_table(ddb, "mine", True)

    class Paged:
        def __init__(self, client):
            self._c, self.calls = client, 0

        def list_tags_of_resource(self, **kw):
            self.calls += 1
            if "NextToken" not in kw:  # first page: only the unrelated tag, lab tag arrives on the second page
                return {"Tags": OTHER, "NextToken": "t2"}
            return self._c.list_tags_of_resource(ResourceArn=kw["ResourceArn"])

        def __getattr__(self, name):
            return getattr(self._c, name)

    paged = Paged(ddb)
    assert [t["name"] for t in labclean._tagged_tables(paged)] == ["mine"] and paged.calls == 2


def test_backups_of_tagged_table_deleted_untagged_table_backups_kept(aws):
    ddb = aws.client("dynamodb")
    make_table(ddb, "mine", True)
    make_table(ddb, "theirs", False)
    ddb.create_backup(TableName="mine", BackupName="bk1")
    ddb.create_backup(TableName="mine", BackupName="bk2")
    ddb.create_backup(TableName="theirs", BackupName="keep")
    assert run(aws, ["dynamodb_backups"], "--yes") == 0
    assert ddb.list_backups(TableName="mine")["BackupSummaries"] == []
    assert len(ddb.list_backups(TableName="theirs")["BackupSummaries"]) == 1
    assert table_names(ddb) == {"mine", "theirs"}  # this kind never deletes tables


def test_backup_dry_run_lists_backups_by_table(aws, capsys):
    ddb = aws.client("dynamodb")
    make_table(ddb, "mine", True)
    ddb.create_backup(TableName="mine", BackupName="bk1")
    assert run(aws, ["dynamodb_backups"]) == 0
    assert "mine / bk1" in capsys.readouterr().out
    assert len(ddb.list_backups(TableName="mine")["BackupSummaries"]) == 1


def test_backups_are_listed_before_and_deleted_before_their_table(aws, capsys):
    ddb = aws.client("dynamodb")
    make_table(ddb, "mine", True)
    ddb.create_backup(TableName="mine", BackupName="bk1")
    assert run(aws, WEEK5, "--yes") == 0
    out = capsys.readouterr().out
    assert out.index("deleted dynamodb_backups") < out.index("deleted dynamodb_tables")
    assert table_names(ddb) == set()


def test_backup_listing_follows_pagination(aws):
    ddb = aws.client("dynamodb")
    make_table(ddb, "mine", True)
    for i in range(3):
        ddb.create_backup(TableName="mine", BackupName=f"bk{i}")
    real = ddb.list_backups

    def one_at_a_time(**kw):
        kw["Limit"] = 1
        return real(**kw)

    class Limited:
        def __getattr__(self, name):
            return getattr(ddb, name)
        list_backups = staticmethod(one_at_a_time)

    class Sess:
        def client(self, *a, **kw):
            return Limited()

    assert len(labclean.find_dynamodb_backups(Sess(), "us-east-1")) == 3


# ======================= RDS (week 05) =======================


def test_rds_instance_tagged_deleted_untagged_kept(aws):
    rds = aws.client("rds")
    make_db(rds, "mine", True)
    make_db(rds, "theirs", False)
    assert run(aws, ["rds_instances"], "--yes") == 0
    assert db_names(rds) == {"theirs"}


def test_rds_dry_run(aws, capsys):
    rds = aws.client("rds")
    make_db(rds, "mine", True)
    assert run(aws, ["rds_instances"]) == 0
    assert "mine" in capsys.readouterr().out and db_names(rds) == {"mine"}


def test_rds_deletion_protected_instance_deleted_only_if_tagged(aws):
    rds = aws.client("rds")
    make_db(rds, "mine", True, protected=True)
    make_db(rds, "theirs", False, protected=True)
    assert run(aws, ["rds_instances"], "--yes") == 0
    assert db_names(rds) == {"theirs"}
    assert rds.describe_db_instances(DBInstanceIdentifier="theirs")["DBInstances"][0]["DeletionProtection"] is True


def test_rds_delete_skips_final_snapshot_and_deletes_automated_backups(aws):
    rds = aws.client("rds")
    make_db(rds, "mine", True)
    seen = {}
    real = rds.delete_db_instance
    rds.delete_db_instance = lambda **kw: (seen.update(kw), real(**kw))[1]
    labclean._delete_db_instance(rds, "mine", {"mine"})
    assert seen["SkipFinalSnapshot"] is True and seen["DeleteAutomatedBackups"] is True
    assert rds.describe_db_snapshots(SnapshotType="manual")["DBSnapshots"] == []


def test_rds_delete_waits_through_deleting_state(aws, monkeypatch):
    rds = aws.client("rds")
    make_db(rds, "mine", True)
    rds.delete_db_instance(DBInstanceIdentifier="mine", SkipFinalSnapshot=True)
    real, polls = rds.describe_db_instances, []

    def lingering(**kw):  # AWS keeps showing the instance as 'deleting' for minutes
        polls.append(1)
        if len(polls) < 4:
            return {"DBInstances": [{"DBInstanceIdentifier": "mine", "DBInstanceStatus": "deleting"}]}
        return real(**kw)
    monkeypatch.setattr(rds, "describe_db_instances", lingering)
    labclean._delete_db_instance(rds, "mine", {"mine"})
    assert len(polls) >= 4


def test_rds_delete_retries_while_instance_is_modifying(aws, monkeypatch):
    rds = aws.client("rds")
    make_db(rds, "mine", True)
    real, calls = rds.delete_db_instance, []

    def busy(**kw):
        calls.append(1)
        if len(calls) < 3:
            raise api_error("InvalidDBInstanceState", "DeleteDBInstance")
        return real(**kw)
    monkeypatch.setattr(rds, "delete_db_instance", busy)
    labclean._delete_db_instance(rds, "mine", {"mine"})
    assert len(calls) == 3 and db_names(rds) == set()


def test_rds_delete_gives_up_with_timeout(aws, monkeypatch):
    rds = aws.client("rds")
    make_db(rds, "mine", True)
    monkeypatch.setattr(labclean, "WAIT_ATTEMPTS", 3)
    monkeypatch.setattr(rds, "delete_db_instance", lambda **kw: (_ for _ in ()).throw(api_error("InvalidDBInstanceState", "DeleteDBInstance")))
    with pytest.raises(TimeoutError):
        labclean._delete_db_instance(rds, "mine", {"mine"})


def test_replica_and_source_both_deleted_replica_first(aws, capsys):
    rds = aws.client("rds")
    make_db(rds, "a-source", True)
    rds.create_db_instance_read_replica(DBInstanceIdentifier="z-replica", SourceDBInstanceIdentifier="a-source", Tags=TAG)
    names = [f.name for f in labclean.find_rds_instances(aws, "us-east-1")]
    assert names == ["z-replica", "a-source"]  # despite alphabetical order
    assert run(aws, ["rds_instances"], "--yes") == 0
    out = capsys.readouterr().out
    assert out.index("z-replica") < out.index("a-source") and db_names(rds) == set()


def test_replica_of_replica_goes_first(aws):
    rds = aws.client("rds")
    make_db(rds, "a-root", True)
    rds.create_db_instance_read_replica(DBInstanceIdentifier="b-mid", SourceDBInstanceIdentifier="a-root", Tags=TAG)
    rds.create_db_instance_read_replica(DBInstanceIdentifier="c-leaf", SourceDBInstanceIdentifier="b-mid", Tags=TAG)
    assert [f.name for f in labclean.find_rds_instances(aws, "us-east-1")] == ["c-leaf", "b-mid", "a-root"]


def test_tagged_source_with_untagged_replica_is_left_alone(aws, capsys):
    rds = aws.client("rds")
    make_db(rds, "mine", True)
    rds.create_db_instance_read_replica(DBInstanceIdentifier="theirs-replica", SourceDBInstanceIdentifier="mine", Tags=OTHER)
    assert run(aws, ["rds_instances"]) == 0
    assert "WILL BE LEFT IN PLACE" in capsys.readouterr().out
    assert run(aws, ["rds_instances"], "--yes") == 1  # deleting the source would promote their replica
    assert "left in place" in capsys.readouterr().out
    assert db_names(rds) == {"mine", "theirs-replica"}


def test_rds_instance_without_taglist_falls_back_to_list_tags(aws):
    rds = aws.client("rds")
    make_db(rds, "mine", True)
    make_db(rds, "theirs", False)
    real = rds.describe_db_instances

    def stripped(**kw):
        result = real(**kw)
        for db in result["DBInstances"]:
            db.pop("TagList", None)
        return result

    class Stripped:
        def describe_db_instances(self, **kw):
            return stripped(**kw)

        def get_paginator(self, name):
            assert name == "describe_db_instances"
            outer = self

            class P:
                def paginate(self, **kw):
                    yield outer.describe_db_instances(**kw)
            return P()

        def __getattr__(self, name):
            return getattr(rds, name)

    class Sess:
        def client(self, *a, **kw):
            return Stripped()

    assert [f.name for f in labclean.find_rds_instances(Sess(), "us-east-1")] == ["mine"]


# ---- RDS snapshots ----


def test_rds_snapshot_tagged_manual_deleted_untagged_kept(aws):
    rds = aws.client("rds")
    make_db(rds, "db", False)
    rds.create_db_snapshot(DBSnapshotIdentifier="mine", DBInstanceIdentifier="db", Tags=TAG)
    rds.create_db_snapshot(DBSnapshotIdentifier="theirs", DBInstanceIdentifier="db", Tags=OTHER)
    assert run(aws, ["rds_snapshots"], "--yes") == 0
    assert [s["DBSnapshotIdentifier"] for s in rds.describe_db_snapshots(SnapshotType="manual")["DBSnapshots"]] == ["theirs"]
    assert db_names(rds) == {"db"}


def test_rds_snapshot_dry_run(aws, capsys):
    rds = aws.client("rds")
    make_db(rds, "db", False)
    rds.create_db_snapshot(DBSnapshotIdentifier="mine", DBInstanceIdentifier="db", Tags=TAG)
    assert run(aws, ["rds_snapshots"]) == 0
    assert "mine" in capsys.readouterr().out
    assert len(rds.describe_db_snapshots(SnapshotType="manual")["DBSnapshots"]) == 1


def test_rds_snapshot_delete_retries_while_creating(aws, monkeypatch):
    rds = aws.client("rds")
    make_db(rds, "db", False)
    rds.create_db_snapshot(DBSnapshotIdentifier="mine", DBInstanceIdentifier="db", Tags=TAG)
    real, calls = rds.delete_db_snapshot, []

    def busy(**kw):
        calls.append(1)
        if len(calls) < 3:
            raise api_error("InvalidDBSnapshotState", "DeleteDBSnapshot")
        return real(**kw)
    monkeypatch.setattr(rds, "delete_db_snapshot", busy)
    labclean._delete_db_snapshot(rds, "mine")
    assert len(calls) == 3 and rds.describe_db_snapshots(SnapshotType="manual")["DBSnapshots"] == []


# ---- DB subnet groups ----


def test_subnet_group_tagged_deleted_untagged_kept(aws):
    rds = aws.client("rds")
    make_subnet_group(aws, "mine", True)
    make_subnet_group(aws, "theirs", False)
    assert run(aws, ["db_subnet_groups"], "--yes") == 0
    assert "theirs" in subnet_group_names(rds) and "mine" not in subnet_group_names(rds)


def test_subnet_group_dry_run_and_default_group_never_listed(aws, capsys):
    rds = aws.client("rds")
    make_subnet_group(aws, "mine", True)
    assert [f.name for f in labclean.find_db_subnet_groups(aws, "us-east-1")] == ["mine"]
    assert run(aws, ["db_subnet_groups"]) == 0
    assert "mine" in capsys.readouterr().out and "mine" in subnet_group_names(rds)


def test_subnet_group_delete_retries_while_instance_shuts_down(aws, monkeypatch):
    rds = aws.client("rds")
    make_subnet_group(aws, "mine", True)
    real, calls = rds.delete_db_subnet_group, []

    def busy(**kw):
        calls.append(1)
        if len(calls) < 3:
            raise api_error("InvalidDBSubnetGroupStateFault", "DeleteDBSubnetGroup")
        return real(**kw)
    monkeypatch.setattr(rds, "delete_db_subnet_group", busy)
    labclean._delete_db_subnet_group(rds, "mine")
    assert len(calls) == 3 and "mine" not in subnet_group_names(rds)


# ======================= whole labs, order, main =======================


def test_week05_end_to_end(aws):
    ddb, rds = aws.client("dynamodb"), aws.client("rds")
    for label, on in (("mine", True), ("theirs", False)):
        make_table(ddb, f"{label}-table", on, protected=True)
        ddb.create_backup(TableName=f"{label}-table", BackupName=f"{label}-backup")
        make_subnet_group(aws, f"{label}-sg", on)
        make_db(rds, f"{label}-db", on, protected=True)
        rds.create_db_snapshot(DBSnapshotIdentifier=f"{label}-snap", DBInstanceIdentifier=f"{label}-db", Tags=tags(on))
    assert run(aws, WEEK5) == 0  # dry run changes nothing
    assert table_names(ddb) == {"mine-table", "theirs-table"} and len(db_names(rds)) == 2
    assert run(aws, WEEK5, "--yes") == 0
    assert table_names(ddb) == {"theirs-table"}
    assert [b["BackupName"] for b in ddb.list_backups(TableName="theirs-table")["BackupSummaries"]] == ["theirs-backup"]
    assert db_names(rds) == {"theirs-db"}
    assert [s["DBSnapshotIdentifier"] for s in rds.describe_db_snapshots(SnapshotType="manual")["DBSnapshots"]] == ["theirs-snap"]
    assert "theirs-sg" in subnet_group_names(rds) and "mine-sg" not in subnet_group_names(rds)
    assert run(aws, WEEK5, "--yes") == 0  # nothing left of ours


def test_finders_order_for_weeks_04_and_05():
    assert list(labclean.FINDERS) == [
        "s3_buckets", "autoscaling_groups", "load_balancers", "target_groups", "ec2_instances", "launch_templates",
        "dynamodb_backups", "dynamodb_tables", "rds_instances", "rds_snapshots", "db_subnet_groups",
        "ebs_snapshots", "ebs_volumes", "nat_gateways", "elastic_ips", "security_groups", "vpcs",
        "iam_roles", "iam_users", "iam_policies"]


def test_main_rejects_unknown_kind(aws):
    with pytest.raises(ValueError, match="unknown resource kind"):
        run(aws, ["ebs_volumes", "efs_file_systems"])


def test_blocked_is_printed_with_its_message_and_counts_as_a_problem(aws, monkeypatch, capsys):
    def finder(session, region):
        def boom():
            raise labclean.Blocked("because of reasons")
        return [labclean.Found("ebs_volumes", "vol-1", region, boom)]
    monkeypatch.setitem(labclean.FINDERS, "ebs_volumes", finder)
    assert run(aws, ["ebs_volumes"], "--yes") == 1
    assert "because of reasons" in capsys.readouterr().out
````

### `_dev/mutants/week04.py`

````python
"""Deliberately wrong implementations for week 04 — each must be caught by its drill."""
MUTANTS = [
    {"id": "early-delete-is-free", "drill": 1, "code": '''
def storage_cost(storage_class, objects, object_kb, days, retrieved_gb=0.0, *, retrieval="standard", price=PRICES):
    if storage_class not in CLASSES or min(objects, object_kb, days, retrieved_gb) < 0 or retrieval not in ("standard", "bulk"):
        raise ValueError(storage_class)
    if storage_class == "STANDARD":
        rate = 0.0
    elif storage_class in RETRIEVAL_KEY:
        rate = price[RETRIEVAL_KEY[storage_class]]
    else:
        rate = price[ARCHIVE_RETRIEVAL_KEY[(storage_class, retrieval)]]
    billable_gb = objects * max(object_kb, MIN_OBJECT_KB[storage_class]) / 1_048_576
    return round(billable_gb * price[RATE_KEY[storage_class]] * days / 30 + retrieved_gb * rate, 2)
'''},
    {"id": "small-objects-move", "drill": 2, "code": '''
from _harness.awslib import lifecycle as _ref
def current_class(rules, key, age_days, size_bytes, tags=None):
    return _ref.current_class(rules, key, age_days, 1 << 30, tags)
'''},
    {"id": "gp3-charges-the-baseline", "drill": 3, "code": '''
from _harness.awslib import ebs as _ref
def monthly_cost(volume_type, size_gib, iops=None, throughput=None, price=PRICES):
    if volume_type == "gp3":
        cfg = _ref.gp3_config(size_gib, iops, throughput)
        return round(size_gib * price["ebs_gp3_per_gb_month"] + cfg["iops"] * price["ebs_gp3_per_iops_month"]
                     + (cfg["throughput"] - 125) * price["ebs_gp3_per_mibps_month"], 2)
    return _ref.monthly_cost(volume_type, size_gib, iops, throughput, price)
'''},
    {"id": "ten-thousand-and-one-parts", "drill": 4, "code": '''
def plan_parts(object_bytes, part_mib=None):
    if object_bytes <= 0 or object_bytes > MAX_OBJECT_BYTES:
        raise ValueError("object size")
    if part_mib is None:
        part_mib = max(5, math.ceil(object_bytes / (10_000 * MIB)))
    if not 5 <= part_mib <= 5120:
        raise ValueError("part size")
    part_bytes = part_mib * MIB
    parts = math.ceil(object_bytes / part_bytes)
    if parts > 10_001:
        raise ValueError("too many parts")
    return {"part_bytes": part_bytes, "parts": parts, "last_part_bytes": object_bytes - (parts - 1) * part_bytes,
            "multipart": object_bytes > 5 * GIB or object_bytes > 100 * MIB}
'''},
    {"id": "deny-objects-only", "drill": 5, "code": '''
def tls_only_policy(bucket):
    return {"Version": "2012-10-17", "Statement": [{
        "Sid": "DenyInsecureTransport", "Effect": "Deny", "Principal": "*", "Action": "s3:*",
        "Resource": f"arn:aws:s3:::{bucket}/*",
        "Condition": {"Bool": {"aws:SecureTransport": "false"}}}]}
'''},
    {"id": "expiry-not-checked", "drill": 6, "code": '''
def share_link(s3, bucket, key, seconds):
    return s3.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=seconds)
'''},
    {"id": "opposite-predictions", "drill": 7, "code": '''
PREDICTIONS = {1: "AccessDenied", 2: "second", 3: 1, 4: "0 markers, 1 versions", 5: "first", 6: "AccessDenied",
               7: "1 markers, 2 versions", 8: "second"}
'''},
    {"id": "public-read-kept", "drill": 8, "code": '''
ASSETS_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {"Sid": "ReadAssets", "Effect": "Allow", "Principal": "*", "Action": "s3:GetObject", "Resource": f"{BUCKET_ARN}/*"},
        {"Sid": "AppUploads", "Effect": "Allow", "Principal": {"AWS": APP_ROLE_ARN},
         "Action": "s3:PutObject", "Resource": f"{BUCKET_ARN}/uploads/*"},
    ],
}
'''},
    {"id": "source-only-versioning", "drill": 9, "code": '''
def make_replicated_pair(s3, source, destination, role_arn):
    if source == destination:
        raise ValueError("source and destination must differ")
    for name in (source, destination):
        s3.create_bucket(Bucket=name)
    s3.put_bucket_versioning(Bucket=source, VersioningConfiguration={"Status": "Enabled"})
    s3.put_bucket_replication(Bucket=source, ReplicationConfiguration={
        "Role": role_arn,
        "Rules": [{"ID": "all", "Status": "Enabled", "Priority": 1, "Filter": {"Prefix": ""},
                   "DeleteMarkerReplication": {"Status": "Enabled"},
                   "Destination": {"Bucket": f"arn:aws:s3:::{destination}"}}],
    })
'''},
    {"id": "no-answers", "drill": 10, "code": '''
CHOICES = {n: None for n in range(1, 9)}
'''},
]
````

### `_dev/mutants/week05.py`

````python
"""Deliberately wrong implementations for week 05 — each must be caught by its drill."""
MUTANTS = [
    {"id": "item-size-rounded-down", "drill": 1, "code": '''
import math
def read_units(item_kb, consistency="eventual"):
    if not 0 < item_kb <= 400:
        raise ValueError("item size")
    if consistency not in ("eventual", "strong", "transactional"):
        raise ValueError("consistency")
    return math.floor(item_kb / 4) * {"eventual": 0.5, "strong": 1.0, "transactional": 2.0}[consistency]
def write_units(item_kb, transactional=False):
    if not 0 < item_kb <= 400:
        raise ValueError("item size")
    return math.floor(item_kb) * (2 if transactional else 1)
'''},
    {"id": "provisioned-billed-for-used-hours", "drill": 2, "code": '''
def monthly_cost_provisioned(rcu, wcu, hours=730, price=PRICES):
    if rcu < 0 or wcu < 0 or hours < 0:
        raise ValueError("negative")
    busy_hours = hours * 8 / 24      # "we only use it in the working day, so we only pay then"
    return round(busy_hours * (rcu * price["dynamodb_rcu_hour"] + wcu * price["dynamodb_wcu_hour"]), 4)
'''},
    {"id": "owner-index-keys-swapped", "drill": 3, "code": '''
TABLE = {
    "KeySchema": [{"AttributeName": "pk", "KeyType": "HASH"}, {"AttributeName": "sk", "KeyType": "RANGE"}],
    "AttributeDefinitions": [{"AttributeName": n, "AttributeType": "S"} for n in ("pk", "sk", "gsi1pk", "gsi1sk")],
    "GlobalSecondaryIndexes": [{
        "IndexName": "owner-index",
        "KeySchema": [{"AttributeName": "gsi1sk", "KeyType": "HASH"}, {"AttributeName": "gsi1pk", "KeyType": "RANGE"}],
        "Projection": {"ProjectionType": "ALL"},
    }],
}
'''},
    {"id": "scan-instead-of-query", "drill": 3, "code": '''
def links_of_owner(table, owner):
    items = table.scan(FilterExpression=Key("owner").eq(owner))["Items"]
    return [i["code"] for i in sorted(items, key=lambda i: i["created"], reverse=True)]
'''},
    {"id": "lost-update", "drill": 4, "code": '''
def rename_link(table, code, new_url, expected_version):
    got = table.update_item(
        Key={"pk": f"LINK#{code}"}, UpdateExpression="SET #u = :u, #v = :next",
        ExpressionAttributeNames={"#u": "url", "#v": "version"},
        ExpressionAttributeValues={":u": new_url, ":next": expected_version + 1}, ReturnValues="ALL_NEW")
    return int(got["Attributes"]["version"])
'''},
    {"id": "transfer-without-a-transaction", "drill": 4, "code": '''
def transfer_owner(client, code, old_owner, new_owner):
    if old_owner == new_owner:
        raise ValueError("same owner")
    def key(pk):
        return {"pk": {"S": pk}}
    client.update_item(TableName=TABLE_NAME, Key=key(f"OWNER#{old_owner}"), UpdateExpression="ADD link_count :m",
                       ExpressionAttributeValues={":m": {"N": "-1"}})
    client.update_item(TableName=TABLE_NAME, Key=key(f"OWNER#{new_owner}"), UpdateExpression="ADD link_count :o",
                       ExpressionAttributeValues={":o": {"N": "1"}})
    client.update_item(TableName=TABLE_NAME, Key=key(f"LINK#{code}"), UpdateExpression="SET #o = :new ADD #v :o",
                       ExpressionAttributeNames={"#o": "owner", "#v": "version"},
                       ExpressionAttributeValues={":new": {"S": new_owner}, ":o": {"N": "1"}})
'''},
    {"id": "ttl-but-no-pitr", "drill": 5, "code": '''
def protect_table(client, table_name, ttl_attribute):
    client.update_time_to_live(TableName=table_name,
                               TimeToLiveSpecification={"Enabled": True, "AttributeName": ttl_attribute})
    return client.create_backup(TableName=table_name, BackupName=f"{table_name}-baseline")["BackupDetails"]["BackupArn"]
'''},
    {"id": "write-through-forgets-the-cache", "drill": 6, "code": '''
from _harness.awslib import caching as _ref
def simulate(events, strategy, ttl=None):
    return _ref.simulate(events, "lazy" if strategy == "write-through" else strategy, ttl)
'''},
    {"id": "concurrency-rounded-down", "drill": 7, "code": '''
import math
def peak_concurrency(requests_per_second, avg_duration_s):
    if requests_per_second <= 0 or avg_duration_s <= 0:
        raise ValueError("positive inputs only")
    return max(1, math.floor(round(requests_per_second * avg_duration_s, 9)))
'''},
    {"id": "single-az", "drill": 8, "code": '''
def create_primary(rds, subnet_group, sg_id):
    rds.create_db_instance(
        DBInstanceIdentifier="shortly-db", Engine="postgres", EngineVersion="17.4", DBInstanceClass="db.t4g.micro",
        AllocatedStorage=20, StorageType="gp3", MultiAZ=False, StorageEncrypted=True,
        MasterUsername="shortly_admin", ManageMasterUserPassword=True,
        BackupRetentionPeriod=7, DeletionProtection=True, PubliclyAccessible=False,
        DBSubnetGroupName=subnet_group, VpcSecurityGroupIds=[sg_id])
    return "shortly-db"
'''},
    {"id": "unanswered-ha", "drill": 9, "code": '''
CHOICES = {n: None for n in CHOICES}
'''},
    {"id": "unanswered-engines", "drill": 10, "code": '''
ENGINES = {n: None for n in ENGINES}
'''},
]
````

### `_dev/mutants/m04.py`

````python
"""Wrong versions of the M04 snapshot — exact text edits applied to a copy of course_project/solutions/m04."""
STORAGE = "infra/storage.yaml"
TLS_DENY = """          - Sid: DenyInsecureTransport
            Effect: Deny
            Principal: '*'
            Action: 's3:*'
            Resource:
              - !GetAtt AssetsBucket.Arn
              - !Sub '${AssetsBucket.Arn}/*'
            Condition:
              Bool: {'aws:SecureTransport': 'false'}
"""
PUBLIC_READ = """          - Sid: PublicRead
            Effect: Allow
            Principal: '*'
            Action: s3:GetObject
            Resource: !Sub '${AssetsBucket.Arn}/*'
"""
NONCURRENT = """            NoncurrentVersionExpiration:
              NoncurrentDays: 30
              NewerNoncurrentVersions: 3
"""
KMS_BPA = "SSEAlgorithm: aws:kms\n      PublicAccessBlockConfiguration:\n        BlockPublicAcls: true\n        BlockPublicPolicy: true"
MUTANTS = [
    {"id": "versioning-suspended", "edits": {STORAGE: [["        Status: Enabled\n      BucketEncryption", "        Status: Suspended\n      BucketEncryption"]]}},
    {"id": "bpa-off", "edits": {STORAGE: [[KMS_BPA, KMS_BPA.replace("BlockPublicPolicy: true", "BlockPublicPolicy: false")]]}},
    {"id": "sse-s3-on-assets", "edits": {STORAGE: [["SSEAlgorithm: aws:kms", "SSEAlgorithm: AES256"]]}},
    {"id": "no-bucket-key", "edits": {STORAGE: [["          - BucketKeyEnabled: true\n            ServerSideEncryptionByDefault:", "          - ServerSideEncryptionByDefault:"]]}},
    {"id": "http-allowed", "edits": {STORAGE: [[TLS_DENY, ""]]}},
    {"id": "tls-deny-objects-only", "edits": {STORAGE: [["              - !GetAtt AssetsBucket.Arn\n              - !Sub '${AssetsBucket.Arn}/*'\n", "              - !Sub '${AssetsBucket.Arn}/*'\n"]]}},
    {"id": "public-read", "edits": {STORAGE: [["          - Sid: AllowAppUploads\n", PUBLIC_READ + "          - Sid: AllowAppUploads\n"]]}},
    {"id": "app-role-everything", "edits": {STORAGE: [["Resource: !Sub '${AssetsBucket.Arn}/uploads/*'", "Resource: !Sub '${AssetsBucket.Arn}/*'"]]}},
    {"id": "noncurrent-forever", "edits": {STORAGE: [[NONCURRENT, ""]]}},
    {"id": "keep-50-versions", "edits": {STORAGE: [["NewerNoncurrentVersions: 3", "NewerNoncurrentVersions: 50"]]}},
    {"id": "no-multipart-cleanup-assets", "edits": {STORAGE: [["              NewerNoncurrentVersions: 3\n            AbortIncompleteMultipartUpload:\n              DaysAfterInitiation: 7\n", "              NewerNoncurrentVersions: 3\n"]]}},
    {"id": "logs-kms", "edits": {STORAGE: [["              SSEAlgorithm: AES256", "              SSEAlgorithm: aws:kms"]]}},
    {"id": "logs-never-expire", "edits": {STORAGE: [["            ExpirationInDays: !If [IsProd, 730, 365]\n", ""]]}},
    {"id": "lab-expires-too-early", "edits": {STORAGE: [["!If [IsProd, 730, 365]", "!If [IsProd, 730, 200]"]]}},
    {"id": "ia-after-glacier", "edits": {STORAGE: [["{StorageClass: STANDARD_IA, TransitionInDays: 30}", "{StorageClass: STANDARD_IA, TransitionInDays: 120}"]]}},
    {"id": "elb-anywhere", "edits": {STORAGE: [["Resource: !Sub '${LogsBucket.Arn}/alb/AWSLogs/${AWS::AccountId}/*'", "Resource: !Sub '${LogsBucket.Arn}/*'"]]}},
    {"id": "no-retain", "edits": {STORAGE: [["    DeletionPolicy: Retain\n", ""]]}},
    {"id": "no-update-replace-retain", "edits": {STORAGE: [["    UpdateReplacePolicy: Retain\n", ""]]}},
    {"id": "ownership-acls-allowed", "edits": {STORAGE: [["          - ObjectOwnership: BucketOwnerEnforced\n      LifecycleConfiguration:\n        Rules:\n          - Id: noncurrent", "          - ObjectOwnership: BucketOwnerPreferred\n      LifecycleConfiguration:\n        Rules:\n          - Id: noncurrent"]]}},
    {"id": "logs-prefix-missing", "edits": {STORAGE: [["            Prefix: alb/\n", ""]]}},
]
````

### `_dev/mutants/m05.py`

````python
"""Wrong versions of the M05 snapshot — exact text edits applied to a copy of course_project/solutions/m05."""
DATA = "infra/data.yaml"
README = "README.md"
MUTANTS = [
    {"id": "public-db", "edits": {DATA: [["PubliclyAccessible: false", "PubliclyAccessible: true"]]}},
    {"id": "plaintext-password", "edits": {DATA: [["      ManageMasterUserPassword: true\n", "      MasterUserPassword: hunter2-hunter2\n"]]}},
    {"id": "both-passwords", "edits": {DATA: [["      ManageMasterUserPassword: true\n", "      ManageMasterUserPassword: true\n      MasterUserPassword: hunter2-hunter2\n"]]}},
    {"id": "unencrypted-db", "edits": {DATA: [["      StorageEncrypted: true\n", "      StorageEncrypted: false\n"]]}},
    {"id": "default-security-group", "edits": {DATA: [["      VPCSecurityGroups:\n        - !ImportValue {'Fn::Sub': '${Prefix}-db-sg-id'}\n", "      VPCSecurityGroups:\n        - !ImportValue {'Fn::Sub': '${Prefix}-app-sg-id'}\n"]]}},
    {"id": "single-az-prod", "edits": {DATA: [["MultiAZ: !If [IsProd, true, false]", "MultiAZ: false"]]}},
    {"id": "no-backups", "edits": {DATA: [["BackupRetentionPeriod: !If [IsProd, 7, 1]", "BackupRetentionPeriod: 0"]]}},
    {"id": "no-lab-backups", "edits": {DATA: [["BackupRetentionPeriod: !If [IsProd, 7, 1]", "BackupRetentionPeriod: !If [IsProd, 7, 0]"]]}},
    {"id": "short-prod-backups", "edits": {DATA: [["BackupRetentionPeriod: !If [IsProd, 7, 1]", "BackupRetentionPeriod: !If [IsProd, 3, 1]"]]}},
    {"id": "unprotected-prod", "edits": {DATA: [["      DeletionProtection: !If [IsProd, true, false]\n", "      DeletionProtection: false\n"]]}},
    {"id": "no-snapshot-on-delete", "edits": {DATA: [["    DeletionPolicy: Snapshot\n", ""]]}},
    {"id": "no-snapshot-on-replace", "edits": {DATA: [["    UpdateReplacePolicy: Snapshot\n", ""]]}},
    {"id": "tags-not-copied", "edits": {DATA: [["      CopyTagsToSnapshot: true\n", ""]]}},
    {"id": "any-secret", "edits": {DATA: [["            Resource: !GetAtt Database.MasterUserSecret.SecretArn", "            Resource: '*'"]]}},
    {"id": "secret-admin", "edits": {DATA: [["            Action: secretsmanager:GetSecretValue", "            Action: 'secretsmanager:*'"]]}},
    {"id": "policy-on-wrong-role", "edits": {DATA: [["      Roles: [!Sub '${Prefix}-app']", "      Roles: [!Sub '${Prefix}-click-consumer']"]]}},
    {"id": "redis-no-tls", "edits": {DATA: [["      TransitEncryptionEnabled: true\n", "      TransitEncryptionEnabled: false\n"]]}},
    {"id": "cache-unencrypted-at-rest", "edits": {DATA: [["      AtRestEncryptionEnabled: true\n", "      AtRestEncryptionEnabled: false\n"]]}},
    {"id": "failover-without-replica", "edits": {DATA: [["NumCacheClusters: !If [IsProd, 2, 1]", "NumCacheClusters: 1"]]}},
    {"id": "no-prod-failover", "edits": {DATA: [["      AutomaticFailoverEnabled: !If [IsProd, true, false]\n", "      AutomaticFailoverEnabled: false\n"]]}},
    {"id": "cache-in-wrong-group", "edits": {DATA: [["        - !ImportValue {'Fn::Sub': '${Prefix}-cache-sg-id'}", "        - !ImportValue {'Fn::Sub': '${Prefix}-db-sg-id'}"]]}},
    {"id": "provisioned-clicks", "edits": {DATA: [["      BillingMode: PAY_PER_REQUEST\n", "      BillingMode: PROVISIONED\n      ProvisionedThroughput: {ReadCapacityUnits: 5, WriteCapacityUnits: 5}\n"]]}},
    {"id": "no-pitr", "edits": {DATA: [["      PointInTimeRecoverySpecification:\n        PointInTimeRecoveryEnabled: true\n", ""]]}},
    {"id": "no-ttl", "edits": {DATA: [["        Enabled: true\n      DeletionProtectionEnabled", "        Enabled: false\n      DeletionProtectionEnabled"]]}},
    {"id": "wrong-key", "edits": {DATA: [["{AttributeName: code, KeyType: HASH}\n        - {AttributeName: day, KeyType: RANGE}", "{AttributeName: day, KeyType: HASH}\n        - {AttributeName: code, KeyType: RANGE}"]]}},
    {"id": "clicks-deleted-with-stack", "edits": {DATA: [["    DeletionPolicy: Retain\n    UpdateReplacePolicy: Retain\n", ""]]}},
    {"id": "cost-not-documented", "edits": {README: [["**22.50** USD", "**2.25** USD"]]}},
    {"id": "no-data-tier-section", "edits": {README: [["## Data tier", "## Databases"]]}},
]
````

### `course_project/tools/conftest.py`

````python
"""Course-owned pytest setup for your shortly-infra repo.

start_milestone.py copies this to tests/conftest.py (with helpers in tests/_course/) and overwrites
it each milestone — don't edit it. It forces fake AWS credentials first, so no test can ever reach
your real AWS account, even if you have a profile configured.
"""
import json
import sys
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parent
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from _course.safety import use_fake_aws_env  # noqa: E402

use_fake_aws_env()

from _course import cfn, policy_eval  # noqa: E402
from _course import cidr as _cidr, dynamo as _dynamo, ec2types as _ec2types, elb as _elb, lifecycle as _lifecycle, netsim as _netsim, scaling as _scaling  # noqa: E402

PARAMS = {"Prefix": "shortly", "Env": "prod"}
ACCOUNT = "111122223333"
PSEUDO = {"AWS::AccountId": ACCOUNT, "AWS::Region": "us-east-1"}
collect_ignore = ["_course"]


def _path(layer: str) -> Path:
    path = REPO / "infra" / f"{layer}.yaml"
    if not path.exists():
        pytest.fail(f"infra/{layer}.yaml does not exist yet", pytrace=False)
    return path


@pytest.fixture(scope="session")
def repo():
    return REPO


@pytest.fixture(scope="session")
def template():
    cache = {}

    def load(layer: str) -> dict:
        if layer not in cache:
            try:
                cache[layer] = cfn.load_template(_path(layer))
            except cfn.TemplateError as exc:
                pytest.fail(f"infra/{layer}.yaml does not load: {exc}", pytrace=False)
        return cache[layer]
    return load


@pytest.fixture(scope="session")
def lint_errors():
    return lambda layer: cfn.errors_only(cfn.lint_template(_path(layer)))


@pytest.fixture
def render():
    return lambda value, **params: cfn.render(value, {**PARAMS, **params}, PSEUDO)


@pytest.fixture
def role_policies(template):
    return lambda layer, role, **params: cfn.role_policies(template(layer), role, {**PARAMS, **params}, PSEUDO)


@pytest.fixture
def trust_policy(template):
    return lambda layer, role, **params: cfn.trust_policy(template(layer), role, {**PARAMS, **params}, PSEUDO)


@pytest.fixture
def evaluator():
    return policy_eval


@pytest.fixture
def resources(template):
    """resources(layer, **params) -> {logical id: resource} that exist for these parameters, with
    every intrinsic function rendered (Conditions and !If applied; parameter Defaults filled in)."""
    return lambda layer, **params: cfn.active_resources(template(layer), {**PARAMS, **params}, PSEUDO)


@pytest.fixture
def outputs(template):
    """outputs(layer, **params) -> the rendered Outputs section."""
    def render(layer, **params):
        tpl = template(layer)
        values = cfn.parameter_values(tpl, {**PARAMS, **params})
        return cfn.render(tpl.get("Outputs") or {}, values, PSEUDO, cfn.evaluate_conditions(tpl, values, PSEUDO), tpl.get("Mappings"))
    return render


@pytest.fixture
def netsim():
    return _netsim


@pytest.fixture
def cidr():
    return _cidr


@pytest.fixture(scope="session")
def ec2types():
    return _ec2types


@pytest.fixture(scope="session")
def elb():
    return _elb


@pytest.fixture(scope="session")
def scaling():
    return _scaling


@pytest.fixture(scope="session")
def lifecycle():
    """The S3 lifecycle model: validate(rules), current_class(...), noncurrent_fate(...)."""
    return _lifecycle


@pytest.fixture(scope="session")
def dynamo():
    """The DynamoDB model: read_units, write_units, provisioned_capacity, monthly_cost_on_demand, …"""
    return _dynamo


@pytest.fixture
def user_data(resources):
    """user_data(layer, logical_id, **params) -> the rendered text of a launch template's UserData
    (the input of Fn::Base64, not encoded)."""
    def read(layer: str, logical_id: str, **params) -> str:
        res = resources(layer, **params).get(logical_id)
        if res is None:
            pytest.fail(f"infra/{layer}.yaml has no resource {logical_id}", pytrace=False)
        text = ((res.get("Properties") or {}).get("LaunchTemplateData") or {}).get("UserData")
        if not isinstance(text, str):
            pytest.fail(f"{logical_id}: LaunchTemplateData needs UserData: !Base64 !Sub | …", pytrace=False)
        return text
    return read


@pytest.fixture
def moto_stacks():
    """deploy(layer, skip_types=(), getatt_values=None, **params) creates the stack in a fake AWS (moto) and returns its status. Stacks that
    import another stack's exports (compute needs iam and network) are deployed after it, in the same test.
    moto skips some resource types silently, so tests only read back what moto really models."""
    import boto3
    from moto import mock_aws

    mock = mock_aws()
    mock.start()

    def deploy(layer: str, skip_types=(), getatt_values=None, **params) -> str:
        """skip_types: resource types moto cannot create (removed from the template, with the Outputs and
        references that point at them); getatt_values: {"Logical.Attr": "literal"} for attributes moto lacks."""
        merged = {**PARAMS, **params}
        tpl = cfn.load_template_text(_path(layer).read_text(encoding="utf-8"))
        declared = tpl.get("Parameters") or {}
        # moto cannot evaluate !Cidr, so hand it the rendered subnet blocks instead
        flat = cfn.inline_functions(tpl, {"Fn::Cidr"}, merged, PSEUDO)
        if skip_types or getatt_values:
            flat = cfn.for_moto(flat, skip_types, getatt_values)
        body = json.dumps(flat)
        cf = boto3.client("cloudformation", region_name="us-east-1")
        cf.create_stack(StackName=f"shortly-{layer}", TemplateBody=body,
                        Capabilities=["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"],
                        Parameters=[{"ParameterKey": k, "ParameterValue": str(v)} for k, v in merged.items() if k in declared])
        return cf.describe_stacks(StackName=f"shortly-{layer}")["Stacks"][0]["StackStatus"]
    yield deploy
    mock.stop()
````

### `course_project/tools/start_milestone.py`

````python
"""start_milestone.py — copy a milestone's tests into your shortly-infra repo.

    python course_project/tools/start_milestone.py 1 --repo ~/code/shortly-infra

Copies (overwriting; these files belong to the course):
    course_project/tests/mNN/              → <repo>/tests/mNN/
    course_project/tools/conftest.py       → <repo>/tests/conftest.py
    course_project/tools/run_milestone.py  → <repo>/run_milestone.py
    _harness/awslib/*.py + prices.toml     → <repo>/tests/_course/   (template, policy and model helpers the tests use:
                                          cfn, policy_eval, network, compute, cost, S3 storage and lifecycle, EBS, DynamoDB, cache and
                                          database models)
    course_project/app/                    → <repo>/app/             (M03 and later: the Shortly app the tests look for)
Exit code: 0 copied · 2 unknown milestone or missing repo folder.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
COURSE_PROJECT = TOOLS.parent
AWSLIB = COURSE_PROJECT.parent / "_harness" / "awslib"
HELPERS = ("__init__.py", "safety.py", "cfn.py", "policy_eval.py", "cidr.py", "netsim.py",
           "ec2types.py", "elb.py", "scaling.py", "purchasing.py", "prices.py", "prices.toml",
           "s3cost.py", "lifecycle.py", "ebs.py", "dynamo.py", "caching.py", "dbmath.py")


def force_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def main(argv=None) -> int:
    force_utf8()
    parser = argparse.ArgumentParser(description="Copy a milestone's tests into your repo.")
    parser.add_argument("milestone", type=int)
    parser.add_argument("--repo", required=True, help="your shortly-infra repo folder")
    args = parser.parse_args(argv)
    n = args.milestone

    source = COURSE_PROJECT / "tests" / f"m{n:02d}"
    if not source.is_dir():
        known = sorted(p.name.upper() for p in (COURSE_PROJECT / "tests").glob("m[0-9][0-9]"))
        print(f"There are no tests for M{n:02d}. Available: {', '.join(known) or 'none yet'}.")
        return 2
    repo = Path(args.repo).expanduser().resolve()
    if not repo.is_dir():
        print(f"{repo} does not exist. Create your repo folder first (see course_project/milestones/M01.md, step 0).")
        return 2

    shutil.copytree(source, repo / "tests" / source.name, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(TOOLS / "conftest.py", repo / "tests" / "conftest.py")
    shutil.copy2(TOOLS / "run_milestone.py", repo / "run_milestone.py")
    helpers = repo / "tests" / "_course"
    helpers.mkdir(parents=True, exist_ok=True)
    for name in HELPERS:
        shutil.copy2(AWSLIB / name, helpers / name)

    app_source = COURSE_PROJECT / "app"
    if n >= 3 and app_source.is_dir():
        shutil.copytree(app_source, repo / "app", dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
        print(f"Copied app/ (the Shortly app your launch template will run) into {repo}")
    print(f"Copied tests/{source.name}/, tests/conftest.py, tests/_course/ and run_milestone.py into {repo}")
    print(f"Instructions:  {COURSE_PROJECT / 'milestones' / f'M{n:02d}.md'}")
    print(f"Progress:      cd \"{repo}\"   then   python run_milestone.py {n}")
    print("Use the course venv's python (it has moto and cfn-lint).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
````

### `course_project/tests/m04/test_m04_1_assets_bucket.py`

````python
"""M04.1 — the assets bucket: versioned, encrypted, private, owned by the account, and never deleted with the stack."""
TYPE = "AWS::S3::Bucket"
ACCOUNT = "111122223333"


def bucket(resources, name="AssetsBucket", **params):
    res = resources("storage", **params)
    assert res.get(name, {}).get("Type") == TYPE, f"add {name} ({TYPE}) to infra/storage.yaml"
    return res[name]


def test_parameters(template):
    params = template("storage").get("Parameters", {})
    assert params.get("Prefix", {}).get("Default") == "shortly", "Parameter Prefix (String, Default shortly)"
    assert sorted(params.get("Env", {}).get("AllowedValues", [])) == ["lab", "prod"], "Parameter Env with AllowedValues [lab, prod]"


def test_name(resources):
    name = bucket(resources)["Properties"].get("BucketName")
    assert name == f"shortly-assets-{ACCOUNT}", \
        "AssetsBucket BucketName: !Sub '${Prefix}-assets-${AWS::AccountId}' (the app role's policy and the S3 endpoint policy already expect this name; the account id keeps it globally unique)"


def test_versioning_is_on(resources):
    status = (bucket(resources)["Properties"].get("VersioningConfiguration") or {}).get("Status")
    assert status == "Enabled", \
        f"VersioningConfiguration Status is {status!r}; use Enabled. Versioning is what lets you undo an overwrite or a delete (a delete only adds a delete marker)"


def test_default_encryption_is_kms_with_a_bucket_key(resources):
    rules = (bucket(resources)["Properties"].get("BucketEncryption") or {}).get("ServerSideEncryptionConfiguration") or []
    assert rules, "add BucketEncryption: ServerSideEncryptionConfiguration: [{ServerSideEncryptionByDefault: {SSEAlgorithm: aws:kms}, BucketKeyEnabled: true}]"
    rule = rules[0]
    default = rule.get("ServerSideEncryptionByDefault") or {}
    assert default.get("SSEAlgorithm") == "aws:kms", \
        f"SSEAlgorithm is {default.get('SSEAlgorithm')!r}; use aws:kms so every object is encrypted under a KMS key and each use shows in CloudTrail"
    assert rule.get("BucketKeyEnabled") is True, \
        "add BucketKeyEnabled: true next to ServerSideEncryptionByDefault. A Bucket Key makes S3 ask KMS for one short-lived key per bucket instead of one per object, which cuts KMS request charges by up to 99 %"
    assert "KMSMasterKeyID" not in default, \
        "leave KMSMasterKeyID out for now: S3 then uses the AWS managed key aws/s3. Milestone M08 brings your own customer managed key"


def test_block_public_access_all_four(resources):
    block = bucket(resources)["Properties"].get("PublicAccessBlockConfiguration") or {}
    for flag in ("BlockPublicAcls", "BlockPublicPolicy", "IgnorePublicAcls", "RestrictPublicBuckets"):
        assert block.get(flag) is True, f"PublicAccessBlockConfiguration: set {flag}: true (all four flags stay on; user uploads are never public)"


def test_object_ownership_is_enforced(resources):
    rules = (bucket(resources)["Properties"].get("OwnershipControls") or {}).get("Rules") or []
    assert rules and rules[0].get("ObjectOwnership") == "BucketOwnerEnforced", \
        "add OwnershipControls: Rules: [{ObjectOwnership: BucketOwnerEnforced}] — ACLs are switched off and the bucket owner owns every object"


def test_the_bucket_survives_the_stack(template):
    res = template("storage")["Resources"].get("AssetsBucket", {})
    assert res.get("DeletionPolicy") == "Retain", \
        "AssetsBucket: add DeletionPolicy: Retain — deleting the stack must not delete the users' uploads"
    assert res.get("UpdateReplacePolicy") == "Retain", \
        "AssetsBucket: add UpdateReplacePolicy: Retain — a change that replaces the bucket must not delete the old one either"
````

### `course_project/tests/m04/test_m04_2_assets_policy.py`

````python
"""M04.2 — the assets bucket policy: TLS only, and the app role may read and write only under uploads/."""
import json

ACCOUNT = "111122223333"
BUCKET = f"arn:aws:s3:::shortly-assets-{ACCOUNT}"
APP_ROLE = f"arn:aws:iam::{ACCOUNT}:role/shortly-app"
APP = f"arn:aws:sts::{ACCOUNT}:assumed-role/shortly-app/i-0123456789abcdef0"
OTHER = "arn:aws:iam::444455556666:role/someone-else"
HTTPS = {"aws:SecureTransport": "true"}
HTTP = {"aws:SecureTransport": "false"}


def concrete(document):
    """The rendered policy with the unresolved references swapped for the real ARNs the tests use."""
    text = json.dumps(document)
    for old, new in (("AssetsBucket.Arn", BUCKET), ("import:shortly-app-role-arn", APP_ROLE)):
        text = text.replace(old, new)
    return json.loads(text)


def policy(resources):
    res = resources("storage")
    assert res.get("AssetsBucketPolicy", {}).get("Type") == "AWS::S3::BucketPolicy", "add AssetsBucketPolicy (AWS::S3::BucketPolicy)"
    props = res["AssetsBucketPolicy"]["Properties"]
    assert props.get("Bucket") == "AssetsBucket", "AssetsBucketPolicy Bucket: !Ref AssetsBucket"
    assert props.get("PolicyDocument"), "AssetsBucketPolicy needs a PolicyDocument"
    return concrete(props["PolicyDocument"])


def request(evaluator, action="s3:GetObject", key="uploads/x.png", principal=APP, **context):
    resource = f"{BUCKET}/{key}" if key else BUCKET
    return evaluator.Request(principal, action, resource, context)


def test_app_role_reads_uploads_through_the_bucket_policy(resources, evaluator):
    doc = policy(resources)
    for action in ("s3:GetObject", "s3:PutObject"):
        decision = evaluator.decide_resource_policy(doc, request(evaluator, action, **HTTPS))
        assert decision == "Allow", \
            f"the bucket policy alone must allow the app role {action} on uploads/x.png over HTTPS (got {decision}); add statement AllowAppUploads with Principal AWS: the imported app role ARN"


def test_the_full_evaluation_allows_the_app(resources, evaluator, role_policies):
    doc = policy(resources)
    identity = role_policies("iam", "AppRole")
    decision = evaluator.evaluate(request(evaluator, **HTTPS), identity=identity, resource_policy=doc)
    assert decision == "Allow", f"identity policy plus bucket policy must allow the app to GET uploads/x.png (got {decision})"


def test_plain_http_is_denied_even_for_the_app(resources, evaluator, role_policies):
    doc = policy(resources)
    identity = role_policies("iam", "AppRole")
    decision = evaluator.evaluate(request(evaluator, **HTTP), identity=identity, resource_policy=doc)
    assert decision == "ExplicitDeny", \
        f"over HTTP (aws:SecureTransport false) the answer must be ExplicitDeny, got {decision}. Add a statement DenyInsecureTransport: Effect Deny, Principal '*', Action 's3:*', Condition Bool aws:SecureTransport 'false'"


def test_the_tls_deny_covers_the_bucket_itself(resources, evaluator):
    doc = policy(resources)
    decision = evaluator.decide_resource_policy(doc, request(evaluator, "s3:ListBucket", key=None, **HTTP))
    assert decision == "ExplicitDeny", \
        f"DenyInsecureTransport must list both the bucket ARN and the bucket ARN/* (ListBucket over HTTP gave {decision}); use Resource: [!GetAtt AssetsBucket.Arn, !Sub '${{AssetsBucket.Arn}}/*']"


def test_nobody_else_gets_in(resources, evaluator):
    doc = policy(resources)
    anonymous = evaluator.decide_resource_policy(doc, request(evaluator, principal="anonymous", **HTTPS))
    assert anonymous != "Allow", "an anonymous GET must not be allowed by the bucket policy; the bucket is not public"
    stranger = evaluator.decide_resource_policy(doc, request(evaluator, principal=OTHER, **HTTPS))
    assert stranger != "Allow", "a role from another account must not be allowed; the Principal is only the app role"


def test_the_app_is_limited_to_uploads(resources, evaluator):
    doc = policy(resources)
    for key in ("private/x.png", "x.png"):
        decision = evaluator.decide_resource_policy(doc, request(evaluator, key=key, **HTTPS))
        assert decision != "Allow", \
            f"the bucket policy must not let the app role read {key}: scope AllowAppUploads to '${{AssetsBucket.Arn}}/uploads/*'"
    decision = evaluator.decide_resource_policy(doc, request(evaluator, "s3:DeleteObject", **HTTPS))
    assert decision != "Allow", "the app role may only s3:GetObject and s3:PutObject, not delete"
````

### `course_project/tests/m04/test_m04_3_versions_and_uploads.py`

````python
"""M04.3 — the assets bucket's lifecycle: old versions do not pile up, half-finished uploads are cleaned."""
import pytest


def to_api(rule):
    """One CloudFormation lifecycle rule in the shape the S3 API (and the lifecycle model) uses."""
    out = {"Status": rule.get("Status")}
    if "Id" in rule:
        out["ID"] = rule["Id"]
    parts = {}
    if rule.get("Prefix"):
        parts["Prefix"] = rule["Prefix"]
    if rule.get("TagFilters"):
        parts["Tags"] = [{"Key": t["Key"], "Value": t["Value"]} for t in rule["TagFilters"]]
    for name in ("ObjectSizeGreaterThan", "ObjectSizeLessThan"):
        if name in rule:
            parts[name] = int(rule[name])
    out["Filter"] = parts if len(parts) <= 1 and "Tags" not in parts else {"And": parts}
    if "Transitions" in rule:
        out["Transitions"] = [{"Days": t["TransitionInDays"], "StorageClass": t["StorageClass"]} for t in rule["Transitions"]]
    if "ExpirationInDays" in rule:
        out["Expiration"] = {"Days": rule["ExpirationInDays"]}
    if "NoncurrentVersionExpiration" in rule:
        out["NoncurrentVersionExpiration"] = dict(rule["NoncurrentVersionExpiration"])
    if "NoncurrentVersionTransitions" in rule:
        out["NoncurrentVersionTransitions"] = [{"NoncurrentDays": t["TransitionInDays"], "StorageClass": t["StorageClass"]}
                                                for t in rule["NoncurrentVersionTransitions"]]
    if "AbortIncompleteMultipartUpload" in rule:
        out["AbortIncompleteMultipartUpload"] = dict(rule["AbortIncompleteMultipartUpload"])
    return out


@pytest.fixture
def rules(resources):
    res = resources("storage").get("AssetsBucket")
    assert res, "add AssetsBucket (AWS::S3::Bucket) to infra/storage.yaml"
    found = (res["Properties"].get("LifecycleConfiguration") or {}).get("Rules")
    assert found, "AssetsBucket needs LifecycleConfiguration: Rules: [...] with a rule Id noncurrent-versions"
    return [to_api(r) for r in found]


@pytest.fixture
def rule(rules):
    named = [r for r in rules if r.get("ID") == "noncurrent-versions"]
    assert named, "add a lifecycle rule with Id: noncurrent-versions"
    return named[0]


def test_the_rules_are_valid(rules, lifecycle):
    try:
        lifecycle.validate(rules)
    except ValueError as exc:
        raise AssertionError(f"the lifecycle rules are not valid: {exc}") from None


def test_the_rule_is_enabled(rule):
    assert rule["Status"] == "Enabled", "rule noncurrent-versions: Status: Enabled (a Disabled rule does nothing)"


def test_old_versions_are_expired(rule):
    nexp = rule.get("NoncurrentVersionExpiration")
    assert nexp, ("rule noncurrent-versions needs NoncurrentVersionExpiration: {NoncurrentDays: 30, NewerNoncurrentVersions: 3}. "
                  "With versioning on and no expiry every overwrite is stored (and billed) forever")
    assert 1 <= nexp.get("NoncurrentDays", 0) <= 90, \
        f"NoncurrentDays is {nexp.get('NoncurrentDays')}; keep a replaced version for 1 to 90 days (30 is a good start: enough time to notice a mistake)"
    keep = nexp.get("NewerNoncurrentVersions")
    assert keep is not None, "add NewerNoncurrentVersions: 3 — how many noncurrent versions to keep no matter how old they are"
    assert 1 <= keep <= 5, \
        f"NewerNoncurrentVersions is {keep}; keep between 1 and 5. Each kept version is a full-price copy of the object, so 50 versions of a busy file cost 50 times as much"


def test_what_happens_to_old_versions(rules, lifecycle):
    key = "uploads/logo.png"
    assert lifecycle.noncurrent_fate(rules, key, 31, newer_noncurrent=3) == "DELETED", \
        "a version noncurrent for 31 days with 3 newer noncurrent versions must be deleted"
    assert lifecycle.noncurrent_fate(rules, key, 31, newer_noncurrent=2) != "DELETED", \
        "a version that is one of the 3 newest noncurrent versions must be kept, however old"
    assert lifecycle.noncurrent_fate(rules, key, 10, newer_noncurrent=5) != "DELETED", \
        "a version noncurrent for only 10 days must be kept: NoncurrentDays has not passed"


def test_incomplete_uploads_are_aborted(rules):
    aborting = [r["AbortIncompleteMultipartUpload"]["DaysAfterInitiation"] for r in rules if r.get("AbortIncompleteMultipartUpload")]
    assert aborting, ("add AbortIncompleteMultipartUpload: {DaysAfterInitiation: 7} to the rule. Parts of an unfinished multipart upload "
                      "are invisible in the console and billed until something deletes them")
    assert min(aborting) <= 7, f"DaysAfterInitiation is {min(aborting)}; abort unfinished uploads after 7 days or less"
````

### `course_project/tests/m04/test_m04_4_logs_bucket.py`

````python
"""M04.4 — the logs bucket: SSE-S3, private, tiered by age, and writable only by the load balancer's log delivery."""
import json

import pytest

ACCOUNT = "111122223333"
BUCKET = f"arn:aws:s3:::shortly-logs-{ACCOUNT}"
DELIVERY = "logdelivery.elasticloadbalancing.amazonaws.com"
LOG_KEY = f"alb/AWSLogs/{ACCOUNT}/elasticloadbalancing/us-east-1/2026/10/11/{ACCOUNT}_elasticloadbalancing_us-east-1_app.shortly.1_20261011T0000Z_10.20.8.5_abc.log.gz"
TWO_MB = 2 * 1024 * 1024
HTTPS = {"aws:SecureTransport": "true"}


def logs_bucket(resources, **params):
    res = resources("storage", **params)
    assert res.get("LogsBucket", {}).get("Type") == "AWS::S3::Bucket", "add LogsBucket (AWS::S3::Bucket) to infra/storage.yaml"
    return res["LogsBucket"]["Properties"]


def to_api(rule):
    out = {"Status": rule.get("Status"), "ID": rule.get("Id"),
           "Filter": {"Prefix": rule["Prefix"]} if rule.get("Prefix") else {}}
    if "Transitions" in rule:
        out["Transitions"] = [{"Days": t["TransitionInDays"], "StorageClass": t["StorageClass"]} for t in rule["Transitions"]]
    if "ExpirationInDays" in rule:
        out["Expiration"] = {"Days": rule["ExpirationInDays"]}
    if "AbortIncompleteMultipartUpload" in rule:
        out["AbortIncompleteMultipartUpload"] = dict(rule["AbortIncompleteMultipartUpload"])
    return out


def api_rules(resources, **params):
    found = (logs_bucket(resources, **params).get("LifecycleConfiguration") or {}).get("Rules")
    assert found, "LogsBucket needs LifecycleConfiguration: Rules: [...] with a rule Id alb-logs"
    rules = [to_api(r) for r in found if r.get("Id") == "alb-logs"]
    assert rules, "add a lifecycle rule with Id: alb-logs"
    return rules


def test_name_and_encryption(resources):
    props = logs_bucket(resources)
    assert props.get("BucketName") == f"shortly-logs-{ACCOUNT}", "LogsBucket BucketName: !Sub '${Prefix}-logs-${AWS::AccountId}'"
    rules = (props.get("BucketEncryption") or {}).get("ServerSideEncryptionConfiguration") or []
    algorithm = ((rules[0].get("ServerSideEncryptionByDefault") or {}).get("SSEAlgorithm")) if rules else None
    assert algorithm == "AES256", \
        f"SSEAlgorithm is {algorithm!r}; use AES256 (SSE-S3). Load balancer access logs can only be delivered to a bucket that uses SSE-S3: with aws:kms the delivery fails and no logs arrive"


def test_private_and_owned(resources):
    props = logs_bucket(resources)
    block = props.get("PublicAccessBlockConfiguration") or {}
    for flag in ("BlockPublicAcls", "BlockPublicPolicy", "IgnorePublicAcls", "RestrictPublicBuckets"):
        assert block.get(flag) is True, f"LogsBucket PublicAccessBlockConfiguration: set {flag}: true"
    rules = (props.get("OwnershipControls") or {}).get("Rules") or []
    assert rules and rules[0].get("ObjectOwnership") == "BucketOwnerEnforced", \
        "LogsBucket: OwnershipControls Rules: [{ObjectOwnership: BucketOwnerEnforced}]"


def test_the_rules_are_valid(resources, lifecycle):
    try:
        lifecycle.validate(api_rules(resources))
    except ValueError as exc:
        raise AssertionError(f"the lifecycle rules are not valid: {exc}") from None


@pytest.mark.parametrize("age, expected", [(0, "STANDARD"), (29, "STANDARD"), (30, "STANDARD_IA"), (89, "STANDARD_IA"),
                                           (90, "GLACIER_IR"), (179, "GLACIER_IR"), (180, "DEEP_ARCHIVE")])
def test_logs_move_down_the_waterfall(resources, lifecycle, age, expected):
    rules = api_rules(resources)
    got = lifecycle.current_class(rules, LOG_KEY, age, TWO_MB)
    assert got == expected, (f"a 2 MB log under alb/ that is {age} days old should be {expected}, got {got}. "
                             "Rule alb-logs: Prefix alb/, Transitions STANDARD_IA at 30 days, GLACIER_IR at 90, DEEP_ARCHIVE at 180")


@pytest.mark.parametrize("env, days", [("prod", 730), ("lab", 365)])
def test_logs_expire_by_environment(resources, lifecycle, env, days):
    rules = api_rules(resources, Env=env)
    assert lifecycle.current_class(rules, LOG_KEY, days - 1, TWO_MB) == "DEEP_ARCHIVE", \
        f"Env={env}: a log {days - 1} days old should still be kept (in DEEP_ARCHIVE)"
    assert lifecycle.current_class(rules, LOG_KEY, days, TWO_MB) == "EXPIRED", \
        f"Env={env}: logs must expire after {days} days: ExpirationInDays: !If [IsProd, 730, 365]. Logs kept forever cost money forever"


def test_deep_archive_is_not_left_early(resources):
    for env in ("prod", "lab"):
        found = logs_bucket(resources, Env=env)["LifecycleConfiguration"]["Rules"]
        rule = next((r for r in found if r.get("Id") == "alb-logs"), {})
        deep = next((t["TransitionInDays"] for t in rule.get("Transitions", []) if t["StorageClass"] == "DEEP_ARCHIVE"), None)
        assert deep is not None and rule.get("ExpirationInDays", 0) >= deep + 180, \
            f"Env={env}: Deep Archive bills a 180-day minimum, so expire at least 180 days after the transition (an earlier delete is charged as if the object stayed)"


def test_only_alb_logs_are_covered(resources, lifecycle):
    rules = api_rules(resources)
    for key in ("other/x.log", "AWSLogs/x.log"):
        assert lifecycle.current_class(rules, key, 400, TWO_MB) == "STANDARD", \
            f"{key} is outside the alb/ prefix, so the rule must leave it alone (Prefix: alb/)"


def test_abort_incomplete_uploads(resources):
    rule = api_rules(resources)[0]
    assert rule.get("AbortIncompleteMultipartUpload", {}).get("DaysAfterInitiation", 99) <= 7, \
        "rule alb-logs: add AbortIncompleteMultipartUpload: {DaysAfterInitiation: 7}"


# ── the bucket policy ──────────────────────────────────────────────

def policy(resources):
    res = resources("storage")
    assert res.get("LogsBucketPolicy", {}).get("Type") == "AWS::S3::BucketPolicy", "add LogsBucketPolicy (AWS::S3::BucketPolicy)"
    props = res["LogsBucketPolicy"]["Properties"]
    assert props.get("Bucket") == "LogsBucket", "LogsBucketPolicy Bucket: !Ref LogsBucket"
    return json.loads(json.dumps(props["PolicyDocument"]).replace("LogsBucket.Arn", BUCKET))


def put(evaluator, principal=DELIVERY, key=LOG_KEY, **context):
    return evaluator.Request(principal, "s3:PutObject", f"{BUCKET}/{key}", context)


def test_log_delivery_may_write_its_prefix(resources, evaluator):
    doc = policy(resources)
    decision = evaluator.decide_resource_policy(doc, put(evaluator, **HTTPS))
    assert decision == "Allow", (f"the log delivery service ({DELIVERY}) must be allowed s3:PutObject under alb/AWSLogs/{ACCOUNT}/ (got {decision}). "
                                 "Statement AllowAlbLogDelivery: Principal Service, Action s3:PutObject, Resource '${LogsBucket.Arn}/alb/AWSLogs/${AWS::AccountId}/*'")


def test_log_delivery_is_limited_to_this_account_and_prefix(resources, evaluator):
    doc = policy(resources)
    for key in ("other/x.log", "alb/AWSLogs/999999999999/x.log", "alb/x.log"):
        assert evaluator.decide_resource_policy(doc, put(evaluator, key=key, **HTTPS)) != "Allow", \
            f"log delivery must not be able to write {key}: limit the Resource to alb/AWSLogs/<your account id>/*"


def test_nobody_else_writes_logs(resources, evaluator):
    doc = policy(resources)
    for who in (f"arn:aws:iam::{ACCOUNT}:role/shortly-app", "arn:aws:iam::444455556666:role/x", "anonymous"):
        assert evaluator.decide_resource_policy(doc, put(evaluator, principal=who, **HTTPS)) != "Allow", \
            f"{who} must not be allowed to write to the logs bucket"


def test_http_is_denied(resources, evaluator):
    doc = policy(resources)
    for resource in (BUCKET, f"{BUCKET}/{LOG_KEY}"):
        request = evaluator.Request(DELIVERY, "s3:PutObject", resource, {"aws:SecureTransport": "false"})
        assert evaluator.decide_resource_policy(doc, request) == "ExplicitDeny", \
            "add DenyInsecureTransport to the logs bucket policy too (Resource: the bucket ARN and the bucket ARN/*)"
````

### `course_project/tests/m04/test_m04_5_exports_and_deploy.py`

````python
"""M04.5 — exports for later stacks, lint-clean, and a deploy in moto (iam + storage) for both environments."""
import re

import pytest

EXPORTS = {"AssetsBucketName": ("shortly-assets-bucket", "AssetsBucket"),
           "AssetsBucketArn": ("shortly-assets-bucket-arn", "AssetsBucket.Arn"),
           "LogsBucketName": ("shortly-logs-bucket", "LogsBucket"),
           "LogsBucketArn": ("shortly-logs-bucket-arn", "LogsBucket.Arn")}


def test_exports(outputs):
    out = outputs("storage")
    for key, (export, value) in EXPORTS.items():
        assert key in out, f"add Output {key}"
        assert out[key].get("Export", {}).get("Name") == export, f"{key}: Export Name !Sub '${{Prefix}}-{export[8:]}'"
        assert str(out[key].get("Value")) == value, f"{key}: Value should render as {value} ({'!GetAtt ' + value if '.' in value else '!Ref ' + value})"


def test_lint_clean(lint_errors):
    errors = lint_errors("storage")
    assert errors == [], "cfn-lint errors: " + "; ".join(f"line {e['line']} {e['rule']} {e['message']}" for e in errors)


@pytest.mark.parametrize("env", ["prod", "lab"])
def test_deploys_in_moto(moto_stacks, env):
    import boto3

    for layer in ("iam", "storage"):
        status = moto_stacks(layer, Env=env)
        assert status == "CREATE_COMPLETE", f"the {layer} stack ended as {status}; fix infra/{layer}.yaml"
    s3 = boto3.client("s3", region_name="us-east-1")
    names = [b["Name"] for b in s3.list_buckets()["Buckets"]]
    assets = [n for n in names if re.fullmatch(r"shortly-assets-\d{12}", n)]
    logs = [n for n in names if re.fullmatch(r"shortly-logs-\d{12}", n)]
    assert len(assets) == 1 and len(logs) == 1, f"expected shortly-assets-<account> and shortly-logs-<account>, found {names}"

    def algorithm(bucket):
        rules = s3.get_bucket_encryption(Bucket=bucket)["ServerSideEncryptionConfiguration"]["Rules"]
        return rules[0]["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"]
    assert algorithm(assets[0]) == "aws:kms", "the assets bucket should encrypt with aws:kms"
    assert algorithm(logs[0]) == "AES256", "the logs bucket should encrypt with AES256 (SSE-S3)"

    cf = boto3.client("cloudformation", region_name="us-east-1")
    outputs = {o["OutputKey"] for o in cf.describe_stacks(StackName="shortly-storage")["Stacks"][0].get("Outputs", [])}
    assert set(EXPORTS) <= outputs, f"the stack is missing Outputs: {sorted(set(EXPORTS) - outputs)}"
````

### `course_project/tests/m05/test_m05_1_database.py`

````python
"""M05.1 — the PostgreSQL database: parameters, the subnet group, and an instance that is private, encrypted and has no password in the template."""


def database(resources, **params):
    res = resources("data", **params)
    assert res.get("Database", {}).get("Type") == "AWS::RDS::DBInstance", "add Database (AWS::RDS::DBInstance) to infra/data.yaml"
    return res["Database"]["Properties"]


def test_parameters(template):
    params = template("data").get("Parameters", {})
    assert params.get("Prefix", {}).get("Default") == "shortly", "Parameter Prefix (String, Default shortly)"
    assert sorted(params.get("Env", {}).get("AllowedValues", [])) == ["lab", "prod"], "Parameter Env with AllowedValues [lab, prod]"
    assert "IsProd" in (template("data").get("Conditions") or {}), "add Condition IsProd: !Equals [!Ref Env, prod]; prod and lab differ in size, Multi-AZ, backups and protection"


def test_subnet_group_uses_the_data_subnets(resources, template):
    res = resources("data")
    group = res.get("DbSubnetGroup", {})
    assert group.get("Type") == "AWS::RDS::DBSubnetGroup", "add DbSubnetGroup (AWS::RDS::DBSubnetGroup): it tells RDS which subnets (so which Availability Zones) the database may use"
    props = group["Properties"]
    assert props.get("DBSubnetGroupDescription"), "DbSubnetGroup needs a DBSubnetGroupDescription"
    assert props.get("SubnetIds") == ["import:shortly-data-subnet-ids"], \
        "DbSubnetGroup SubnetIds: !Split [',', !ImportValue {'Fn::Sub': '${Prefix}-data-subnet-ids'}] (the M02 data subnets have no route to the internet)"
    raw = template("data")["Resources"]["DbSubnetGroup"]["Properties"]["SubnetIds"]
    assert "Fn::Split" in raw, "the exported subnet ids are one comma separated string: wrap the import in !Split [',', …]"


def test_engine_and_version(resources):
    p = database(resources)
    assert p.get("Engine") == "postgres", f"Engine is {p.get('Engine')!r}; use postgres (Shortly's links and users are relational and need transactions)"
    version = str(p.get("EngineVersion", ""))
    assert version.startswith("17."), f"EngineVersion is {version!r}; use a current 17.x release (the course solution uses '17.9'). Quote it so YAML keeps it a string"


def test_instance_class_follows_the_environment(resources):
    assert database(resources, Env="prod").get("DBInstanceClass") == "db.m7g.large", "prod DBInstanceClass: db.m7g.large (Graviton, 2 vCPU, 8 GiB)"
    assert database(resources, Env="lab").get("DBInstanceClass") == "db.t4g.micro", "lab DBInstanceClass: db.t4g.micro (the cheapest class, burstable). Use !If [IsProd, db.m7g.large, db.t4g.micro]"


def test_storage_is_gp3_20gib_on_port_5432(resources):
    p = database(resources)
    assert int(p.get("AllocatedStorage", 0)) == 20, f"AllocatedStorage is {p.get('AllocatedStorage')!r}; use 20 (GiB), the gp3 minimum"
    assert p.get("StorageType") == "gp3", f"StorageType is {p.get('StorageType')!r}; use gp3 (cheaper than gp2 and 3,000 IOPS included)"
    assert int(p.get("Port", 0)) == 5432, "set Port: 5432 explicitly so the endpoint port is the PostgreSQL port (the DB security group allows 5432 only)"


def test_storage_is_encrypted(resources):
    assert database(resources).get("StorageEncrypted") is True, \
        "set StorageEncrypted: true. Encryption can only be chosen when a database is created (you cannot encrypt an existing one in place), and it also encrypts backups, snapshots and replicas"


def test_the_password_is_managed_by_rds(resources):
    p = database(resources)
    assert p.get("MasterUsername") == "shortly", "MasterUsername: shortly"
    assert "MasterUserPassword" not in p, \
        "remove MasterUserPassword: a password in the template ends up in git and in CloudFormation. Use ManageMasterUserPassword: true instead"
    assert p.get("ManageMasterUserPassword") is True, \
        "set ManageMasterUserPassword: true. RDS then creates the master password in AWS Secrets Manager and can rotate it; no human or template ever sees it"


def test_the_database_is_private(resources):
    p = database(resources)
    assert p.get("PubliclyAccessible") is False, \
        "set PubliclyAccessible: false. A database in the data subnets has no internet route anyway, but a public address would be one misplaced security-group rule away from exposure"


def test_subnet_group_and_security_group(resources):
    p = database(resources)
    assert p.get("DBSubnetGroupName") == "DbSubnetGroup", "Database DBSubnetGroupName: !Ref DbSubnetGroup"
    assert p.get("VPCSecurityGroups") == ["import:shortly-db-sg-id"], \
        "Database VPCSecurityGroups: [!ImportValue {'Fn::Sub': '${Prefix}-db-sg-id'}]. The M02 database security group lets only the app tier reach port 5432; without it RDS attaches the VPC's default group"
````

### `course_project/tests/m05/test_m05_2_backups_and_ha.py`

````python
"""M05.2 — backups, Multi-AZ and protection from deletion, for prod and for lab."""
import pytest


def database(resources, env):
    res = resources("data", Env=env)
    assert res.get("Database", {}).get("Type") == "AWS::RDS::DBInstance", "add Database (AWS::RDS::DBInstance) to infra/data.yaml"
    return res["Database"]["Properties"]


@pytest.mark.parametrize("env,expected", [("prod", True), ("lab", False)])
def test_multi_az_only_in_prod(resources, env, expected):
    value = database(resources, env).get("MultiAZ")
    assert value is expected, \
        f"{env}: MultiAZ is {value!r}; use !If [IsProd, true, false]. Multi-AZ keeps a synchronous standby in another zone and fails over by itself ({'prod needs it' if expected else 'lab does not need to pay twice for the instance'})"


@pytest.mark.parametrize("env,minimum", [("prod", 7), ("lab", 1)])
def test_automated_backups_are_on(resources, env, minimum):
    days = database(resources, env).get("BackupRetentionPeriod")
    assert isinstance(days, int) and days >= minimum, \
        f"{env}: BackupRetentionPeriod is {days!r}; use at least {minimum} (prod 7, lab 1). 0 switches automated backups off, and with them point-in-time recovery"
    assert days <= 35, f"{env}: BackupRetentionPeriod {days} is above the 35-day maximum"


@pytest.mark.parametrize("env,expected", [("prod", True), ("lab", False)])
def test_deletion_protection_only_in_prod(resources, env, expected):
    value = database(resources, env).get("DeletionProtection")
    assert value is expected, \
        f"{env}: DeletionProtection is {value!r}; use !If [IsProd, true, false]. In prod nobody can delete the database (even by deleting the stack) until the flag is switched off first; lab stays disposable"


@pytest.mark.parametrize("env", ["prod", "lab"])
def test_tags_are_copied_to_snapshots(resources, env):
    assert database(resources, env).get("CopyTagsToSnapshot") is True, \
        f"{env}: set CopyTagsToSnapshot: true so every snapshot carries the project and env tags (cost reports and tag-based IAM keep working)"


def test_deleting_the_stack_takes_a_snapshot(template):
    res = template("data")["Resources"].get("Database", {})
    assert res.get("DeletionPolicy") == "Snapshot", \
        "Database: add DeletionPolicy: Snapshot at the resource level (next to Type, not under Properties); deleting the stack then takes a final snapshot"
    assert res.get("UpdateReplacePolicy") == "Snapshot", \
        "Database: add UpdateReplacePolicy: Snapshot too; a change that replaces the instance then snapshots the old one instead of deleting it"
````

### `course_project/tests/m05/test_m05_3_secret_access.py`

````python
"""M05.3 — the app role may read the database secret RDS creates, and nothing else in Secrets Manager."""
import json

ACCOUNT = "111122223333"
SECRET = f"arn:aws:secretsmanager:us-east-1:{ACCOUNT}:secret:rds!db-1234abcd-0000-1111-2222-333344445555-AbCdEf"
OTHER = f"arn:aws:secretsmanager:us-east-1:{ACCOUNT}:secret:other-x"
APP = f"arn:aws:sts::{ACCOUNT}:assumed-role/shortly-app/i-0123456789abcdef0"


def concrete(document):
    """The rendered policy with the unresolved attribute reference swapped for the secret's ARN."""
    return json.loads(json.dumps(document).replace("Database.MasterUserSecret.SecretArn", SECRET))


def policy(resources):
    res = resources("data")
    assert res.get("AppDbSecretPolicy", {}).get("Type") == "AWS::IAM::Policy", \
        "add AppDbSecretPolicy (AWS::IAM::Policy) to infra/data.yaml: it adds a permission to the app role that M01 created"
    return res["AppDbSecretPolicy"]["Properties"]


def request(evaluator, resource=SECRET, action="secretsmanager:GetSecretValue"):
    return evaluator.Request(APP, action, resource, {})


def test_policy_is_attached_to_the_app_role(resources):
    props = policy(resources)
    assert props.get("Roles") == ["shortly-app"], "AppDbSecretPolicy Roles: [!Sub '${Prefix}-app'] (the role M01 created; reference it by name, the roles live in another stack)"
    assert props.get("PolicyName"), "AppDbSecretPolicy needs a PolicyName"


def test_one_statement_one_action_one_resource(resources):
    doc = policy(resources)["PolicyDocument"]
    statements = doc.get("Statement")
    statements = statements if isinstance(statements, list) else [statements]
    assert len(statements) == 1, f"AppDbSecretPolicy should have exactly one statement, found {len(statements)}"
    st = statements[0]
    assert st.get("Effect") == "Allow", "the statement Effect is Allow"
    assert st.get("Action") in ("secretsmanager:GetSecretValue", ["secretsmanager:GetSecretValue"]), \
        f"Action is {st.get('Action')!r}; the app only needs secretsmanager:GetSecretValue"
    assert st.get("Resource") == "Database.MasterUserSecret.SecretArn", \
        f"Resource is {st.get('Resource')!r}; use !GetAtt Database.MasterUserSecret.SecretArn — exactly the one secret RDS created, never '*'. (RDS names it rds!db-…, so M01's shortly/db-* statement does not cover it)"


def test_the_app_can_read_the_database_secret(resources, role_policies, evaluator):
    doc = concrete(policy(resources)["PolicyDocument"])
    identity = role_policies("iam", "AppRole") + [doc]
    decision = evaluator.evaluate_policies(identity, request(evaluator))
    assert decision == "Allow", f"the app role must be allowed GetSecretValue on the managed secret (got {decision})"
    assert evaluator.evaluate_policies([doc], request(evaluator)) == "Allow", "AppDbSecretPolicy alone must allow reading the secret; do not rely on other policies"


def test_the_app_cannot_read_other_secrets_through_this_policy(resources, evaluator):
    doc = concrete(policy(resources)["PolicyDocument"])
    decision = evaluator.evaluate_policies([doc], request(evaluator, OTHER))
    assert decision != "Allow", f"AppDbSecretPolicy must not allow other secrets such as {OTHER} (got {decision}); scope Resource to the one secret ARN"
    for action in ("secretsmanager:PutSecretValue", "secretsmanager:DeleteSecret", "secretsmanager:RotateSecret"):
        assert evaluator.evaluate_policies([doc], request(evaluator, action=action)) != "Allow", f"{action} must not be allowed: the app only reads the secret"


def test_the_permissions_boundary_still_allows_it(resources, evaluator):
    boundary = resources("iam")["AppBoundary"]["Properties"]["PolicyDocument"]
    doc = concrete(policy(resources)["PolicyDocument"])
    decision = evaluator.evaluate(request(evaluator), identity=[doc], boundary=boundary)
    assert decision == "Allow", \
        f"the identity policy and the M01 permissions boundary must both allow GetSecretValue (got {decision}); the boundary caps what any role can be granted, so the grant has to stay inside it"
````

### `course_project/tests/m05/test_m05_4_cache.py`

````python
"""M05.4 — the Valkey/Redis cache for hot redirects: subnets, node count, failover, encryption, security group."""
import pytest


def cache(resources, env="prod"):
    res = resources("data", Env=env)
    assert res.get("Cache", {}).get("Type") == "AWS::ElastiCache::ReplicationGroup", \
        "add Cache (AWS::ElastiCache::ReplicationGroup) to infra/data.yaml: a replication group is a primary node plus optional replicas"
    return res["Cache"]["Properties"]


def test_subnet_group(resources):
    group = resources("data").get("CacheSubnetGroup", {})
    assert group.get("Type") == "AWS::ElastiCache::SubnetGroup", "add CacheSubnetGroup (AWS::ElastiCache::SubnetGroup): it tells ElastiCache which subnets the nodes may use"
    props = group["Properties"]
    assert props.get("Description"), "CacheSubnetGroup needs a Description"
    assert props.get("SubnetIds") == ["import:shortly-data-subnet-ids"], "CacheSubnetGroup SubnetIds: !Split [',', !ImportValue {'Fn::Sub': '${Prefix}-data-subnet-ids'}]"
    assert cache(resources).get("CacheSubnetGroupName") == "CacheSubnetGroup", "Cache CacheSubnetGroupName: !Ref CacheSubnetGroup"


def test_engine(resources):
    engine = cache(resources).get("Engine")
    assert engine in ("valkey", "redis"), f"Engine is {engine!r}; use valkey (or redis). Both give sub-millisecond in-memory reads with replicas and failover; memcached has neither"


@pytest.mark.parametrize("env,node_type", [("prod", "cache.m7g.large"), ("lab", "cache.t4g.micro")])
def test_node_type(resources, env, node_type):
    assert cache(resources, env).get("CacheNodeType") == node_type, f"{env} CacheNodeType: {node_type} (!If [IsProd, cache.m7g.large, cache.t4g.micro])"


@pytest.mark.parametrize("env,nodes", [("prod", 2), ("lab", 1)])
def test_node_count(resources, env, nodes):
    value = cache(resources, env).get("NumCacheClusters")
    assert value == nodes, f"{env}: NumCacheClusters is {value!r}; use {nodes} ({'a primary and one replica in another zone' if nodes == 2 else 'a single node is enough in lab'})"


@pytest.mark.parametrize("env,expected", [("prod", True), ("lab", False)])
def test_failover_and_multi_az(resources, env, expected):
    p = cache(resources, env)
    for key in ("AutomaticFailoverEnabled", "MultiAZEnabled"):
        assert p.get(key) is expected, f"{env}: {key} is {p.get(key)!r}; use !If [IsProd, true, false]"
    if p.get("AutomaticFailoverEnabled"):
        assert p.get("NumCacheClusters", 1) >= 2, \
            "failover promotes a replica, so NumCacheClusters must be 2 or more when AutomaticFailoverEnabled is true (cfn-lint does not catch this; CloudFormation fails at deploy time)"


@pytest.mark.parametrize("env", ["prod", "lab"])
def test_encryption(resources, env):
    p = cache(resources, env)
    assert p.get("TransitEncryptionEnabled") is True, f"{env}: set TransitEncryptionEnabled: true. Without TLS, cached redirect targets cross the network in clear text (clients then connect with TLS)"
    assert p.get("AtRestEncryptionEnabled") is True, f"{env}: set AtRestEncryptionEnabled: true. Data on disk (snapshots, node storage) is encrypted"


def test_security_group(resources):
    assert cache(resources).get("SecurityGroupIds") == ["import:shortly-cache-sg-id"], \
        "Cache SecurityGroupIds: [!ImportValue {'Fn::Sub': '${Prefix}-cache-sg-id'}]. The M02 cache security group lets only the app tier reach port 6379"
````

### `course_project/tests/m05/test_m05_5_clicks_table.py`

````python
"""M05.5 — the DynamoDB click counts, and the README's case for three stores with a computed cost."""
import re


def table(resources, **params):
    res = resources("data", **params)
    assert res.get("ClicksTable", {}).get("Type") == "AWS::DynamoDB::Table", "add ClicksTable (AWS::DynamoDB::Table) to infra/data.yaml"
    return res["ClicksTable"]["Properties"]


def test_name_and_billing(resources):
    p = table(resources)
    assert p.get("TableName") == "shortly-clicks-daily", \
        f"TableName is {p.get('TableName')!r}; use !Sub '${{Prefix}}-clicks-daily' (the M01 app and consumer policies already name this table)"
    assert p.get("BillingMode") == "PAY_PER_REQUEST", \
        f"BillingMode is {p.get('BillingMode')!r}; use PAY_PER_REQUEST. Click traffic is spiky and unknown; on-demand pays per request and needs no capacity planning (provisioned capacity bills every hour, used or not)"
    assert "ProvisionedThroughput" not in p, "remove ProvisionedThroughput: on-demand tables have no provisioned capacity"


def test_keys(resources):
    p = table(resources)
    attrs = {a["AttributeName"]: a["AttributeType"] for a in p.get("AttributeDefinitions") or []}
    assert attrs == {"code": "S", "day": "S"}, f"AttributeDefinitions should be code (S) and day (S), found {attrs}"
    keys = {k["AttributeName"]: k["KeyType"] for k in p.get("KeySchema") or []}
    assert keys == {"code": "HASH", "day": "RANGE"}, \
        f"KeySchema should be code HASH (partition key: one short code's counters live together) and day RANGE (sort key: one item per code per day, queried by date range), found {keys}"


def test_point_in_time_recovery(resources):
    spec = table(resources).get("PointInTimeRecoverySpecification") or {}
    assert spec.get("PointInTimeRecoveryEnabled") is True, \
        "add PointInTimeRecoverySpecification: {PointInTimeRecoveryEnabled: true}. It lets you restore the table to any second in the last 35 days (an accidental bulk delete or a bad deploy)"


def test_ttl_on_expires_at(resources):
    ttl = table(resources).get("TimeToLiveSpecification") or {}
    assert ttl.get("AttributeName") == "expires_at" and ttl.get("Enabled") is True, \
        "add TimeToLiveSpecification: {AttributeName: expires_at, Enabled: true}. DynamoDB deletes old daily counters for free once expires_at (epoch seconds) has passed"


def test_deletion_protection_follows_environment(resources):
    assert table(resources, Env="prod").get("DeletionProtectionEnabled") is True, "prod: DeletionProtectionEnabled: true (!If [IsProd, true, false])"
    assert table(resources, Env="lab").get("DeletionProtectionEnabled") is False, "lab: DeletionProtectionEnabled: false so lab can be torn down"


def test_the_table_survives_the_stack(template):
    res = template("data")["Resources"].get("ClicksTable", {})
    assert res.get("DeletionPolicy") == "Retain", "ClicksTable: add DeletionPolicy: Retain — click history must outlive a stack deletion"
    assert res.get("UpdateReplacePolicy") == "Retain", "ClicksTable: add UpdateReplacePolicy: Retain too"


def section(repo):
    readme = repo / "README.md"
    assert readme.exists(), "README.md is missing"
    text = readme.read_text(encoding="utf-8")
    match = re.search(r"^## Data tier\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert match, "add a '## Data tier' section to README.md"
    return match.group(1)


def test_readme_explains_the_three_stores(repo):
    body = section(repo).lower()
    for words, why in ((("postgresql", "postgres"), "PostgreSQL (links and users: relational, transactions)"),
                       (("valkey", "redis"), "Valkey or Redis (hot redirects: sub-millisecond cached reads)"),
                       (("dynamodb",), "DynamoDB (click counts: key-value, write-heavy)")):
        assert any(w in body for w in words), f"the Data tier section should explain {why}"


def test_readme_states_the_monthly_cost(repo, dynamo):
    cost = dynamo.monthly_cost_on_demand(60_000_000, 30_000_000, 1)
    figure = f"{cost:.2f}"
    assert re.search(rf"(?<![\d.]){re.escape(figure)}(?!\d)", section(repo)), \
        (f"the Data tier section should state the clicks table's monthly on-demand cost: {figure} USD for 30 million writes of 0.5 KB and 60 million eventually consistent reads of 1 KB. "
         "Work it out: a 0.5 KB write rounds up to 1 write unit, a 1 KB eventually consistent read is 0.5 read unit; then use the price per million units (check your sums with awslib dynamo.monthly_cost_on_demand)")
````

### `course_project/tests/m05/test_m05_6_exports_and_deploy.py`

````python
"""M05.6 — exports for later stacks, lint-clean, and a deploy in moto (iam + network + data) for both environments."""
import pytest

EXPORTS = {"DbEndpointAddress": "db-endpoint", "DbPort": "db-port", "DbSecretArn": "db-secret-arn",
           "CacheEndpoint": "cache-endpoint", "ClicksTableName": "clicks-table", "ClicksTableArn": "clicks-table-arn"}
VALUES = {"DbEndpointAddress": "Database.Endpoint.Address", "DbPort": "Database.Endpoint.Port",
          "DbSecretArn": "Database.MasterUserSecret.SecretArn", "CacheEndpoint": "Cache.PrimaryEndPoint.Address",
          "ClicksTableName": "ClicksTable", "ClicksTableArn": "ClicksTable.Arn"}

# moto does not create ElastiCache or Secrets Manager resources from CloudFormation, and it cannot answer
# !GetAtt Database.MasterUserSecret.SecretArn. The deploy test therefore removes those resource types (and the
# Outputs that point at them) and gives moto a literal for the secret ARN. Everything else is really created.
MOTO_SKIP = ("AWS::ElastiCache::SubnetGroup", "AWS::ElastiCache::ReplicationGroup", "AWS::SecretsManager::Secret")
MOTO_SECRET = {"Database.MasterUserSecret.SecretArn": "arn:aws:secretsmanager:us-east-1:111122223333:secret:rds!db-moto"}


def test_exports(outputs):
    out = outputs("data")
    for key, export in EXPORTS.items():
        assert key in out, f"add Output {key}"
        assert out[key].get("Export", {}).get("Name") == f"shortly-{export}", f"{key}: Export Name !Sub '${{Prefix}}-{export}'"
        assert str(out[key].get("Value")) == VALUES[key], \
            f"{key}: Value should render as {VALUES[key]} ({'!GetAtt ' + VALUES[key] if '.' in VALUES[key] else '!Ref ' + VALUES[key]})"


def test_lint_clean(lint_errors):
    errors = lint_errors("data")
    assert errors == [], "cfn-lint errors: " + "; ".join(f"line {e['line']} {e['rule']} {e['message']}" for e in errors)


@pytest.mark.parametrize("env", ["prod", "lab"])
def test_deploys_in_moto(moto_stacks, env):
    import boto3

    for layer in ("iam", "network"):
        status = moto_stacks(layer, Env=env)
        assert status == "CREATE_COMPLETE", f"the {layer} stack ended as {status}; fix infra/{layer}.yaml"
    status = moto_stacks("data", skip_types=MOTO_SKIP, getatt_values=MOTO_SECRET, Env=env)
    assert status == "CREATE_COMPLETE", f"the data stack ended as {status}; fix infra/data.yaml (moto cannot create the cache, so that part is only checked on the template)"

    rds = boto3.client("rds", region_name="us-east-1")
    instances = rds.describe_db_instances()["DBInstances"]
    assert len(instances) == 1, f"expected one database instance, found {len(instances)}"
    db = instances[0]
    assert db["Engine"] == "postgres", f"the database engine is {db['Engine']!r}; use postgres"
    assert db["StorageEncrypted"] is True, "the database should be encrypted (StorageEncrypted: true)"
    assert db["MultiAZ"] is (env == "prod"), f"{env}: MultiAZ should be {env == 'prod'}"
    assert db["Endpoint"]["Port"] == 5432, f"the database port is {db['Endpoint']['Port']}; set Port: 5432"

    ec2 = boto3.client("ec2", region_name="us-east-1")
    subnet_ids = {s["SubnetIdentifier"] for s in db["DBSubnetGroup"]["Subnets"]}
    assert len(subnet_ids) == 2, f"the DB subnet group should hold the two data subnets, found {len(subnet_ids)}"
    names = {t["Value"] for s in ec2.describe_subnets(SubnetIds=sorted(subnet_ids))["Subnets"] for t in s.get("Tags", []) if t["Key"] == "Name"}
    assert names and all("data" in n for n in names), f"the DB subnet group should use the data subnets, found {sorted(names)}"

    ddb = boto3.client("dynamodb", region_name="us-east-1")
    clicks = ddb.describe_table(TableName="shortly-clicks-daily")["Table"]
    assert clicks["BillingModeSummary"]["BillingMode"] == "PAY_PER_REQUEST", "the clicks table should be PAY_PER_REQUEST"
    assert {(k["AttributeName"], k["KeyType"]) for k in clicks["KeySchema"]} == {("code", "HASH"), ("day", "RANGE")}, "the clicks table keys are code (HASH) and day (RANGE)"

    cf = boto3.client("cloudformation", region_name="us-east-1")
    exported = {o["OutputKey"] for o in cf.describe_stacks(StackName="shortly-data")["Stacks"][0].get("Outputs", [])}
    assert {"DbEndpointAddress", "DbPort", "ClicksTableName", "ClicksTableArn"} <= exported, f"the data stack is missing Outputs, found {sorted(exported)}"
````

### `course_project/solutions/m04/infra/storage.yaml`

````yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: shortly-infra M04 - storage (an assets bucket for uploads and a logs bucket for ALB access logs)

Parameters:
  Prefix:
    Type: String
    Default: shortly
    AllowedPattern: '[a-z][a-z0-9-]{1,20}'
  Env:
    Type: String
    AllowedValues: [lab, prod]

Conditions:
  IsProd: !Equals [!Ref Env, prod]

Resources:
  AssetsBucket:
    Type: AWS::S3::Bucket
    DeletionPolicy: Retain
    UpdateReplacePolicy: Retain
    Properties:
      BucketName: !Sub '${Prefix}-assets-${AWS::AccountId}'
      Tags:
        - {Key: project, Value: !Ref Prefix}
        - {Key: env, Value: !Ref Env}
      VersioningConfiguration:
        Status: Enabled
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - BucketKeyEnabled: true
            ServerSideEncryptionByDefault:
              SSEAlgorithm: aws:kms
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      OwnershipControls:
        Rules:
          - ObjectOwnership: BucketOwnerEnforced
      LifecycleConfiguration:
        Rules:
          - Id: noncurrent-versions
            Status: Enabled
            NoncurrentVersionExpiration:
              NoncurrentDays: 30
              NewerNoncurrentVersions: 3
            AbortIncompleteMultipartUpload:
              DaysAfterInitiation: 7

  AssetsBucketPolicy:
    Type: AWS::S3::BucketPolicy
    Properties:
      Bucket: !Ref AssetsBucket
      PolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Sid: DenyInsecureTransport
            Effect: Deny
            Principal: '*'
            Action: 's3:*'
            Resource:
              - !GetAtt AssetsBucket.Arn
              - !Sub '${AssetsBucket.Arn}/*'
            Condition:
              Bool: {'aws:SecureTransport': 'false'}
          - Sid: AllowAppUploads
            Effect: Allow
            Principal:
              AWS: !ImportValue
                Fn::Sub: '${Prefix}-app-role-arn'
            Action: [s3:GetObject, s3:PutObject]
            Resource: !Sub '${AssetsBucket.Arn}/uploads/*'

  LogsBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${Prefix}-logs-${AWS::AccountId}'
      Tags:
        - {Key: project, Value: !Ref Prefix}
        - {Key: env, Value: !Ref Env}
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      OwnershipControls:
        Rules:
          - ObjectOwnership: BucketOwnerEnforced
      LifecycleConfiguration:
        Rules:
          - Id: alb-logs
            Status: Enabled
            Prefix: alb/
            Transitions:
              - {StorageClass: STANDARD_IA, TransitionInDays: 30}
              - {StorageClass: GLACIER_IR, TransitionInDays: 90}
              - {StorageClass: DEEP_ARCHIVE, TransitionInDays: 180}
            ExpirationInDays: !If [IsProd, 730, 365]
            AbortIncompleteMultipartUpload:
              DaysAfterInitiation: 7

  LogsBucketPolicy:
    Type: AWS::S3::BucketPolicy
    Properties:
      Bucket: !Ref LogsBucket
      PolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Sid: DenyInsecureTransport
            Effect: Deny
            Principal: '*'
            Action: 's3:*'
            Resource:
              - !GetAtt LogsBucket.Arn
              - !Sub '${LogsBucket.Arn}/*'
            Condition:
              Bool: {'aws:SecureTransport': 'false'}
          - Sid: AllowAlbLogDelivery
            Effect: Allow
            Principal:
              Service: logdelivery.elasticloadbalancing.amazonaws.com
            Action: s3:PutObject
            Resource: !Sub '${LogsBucket.Arn}/alb/AWSLogs/${AWS::AccountId}/*'

Outputs:
  AssetsBucketName:
    Value: !Ref AssetsBucket
    Export: {Name: !Sub '${Prefix}-assets-bucket'}
  AssetsBucketArn:
    Value: !GetAtt AssetsBucket.Arn
    Export: {Name: !Sub '${Prefix}-assets-bucket-arn'}
  LogsBucketName:
    Value: !Ref LogsBucket
    Export: {Name: !Sub '${Prefix}-logs-bucket'}
  LogsBucketArn:
    Value: !GetAtt LogsBucket.Arn
    Export: {Name: !Sub '${Prefix}-logs-bucket-arn'}
````

### `course_project/solutions/m04/README.md`

````markdown
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

## Check it

Run the milestone tests with the course venv:

```
python run_milestone.py 4
```

## Deploy (optional)

Deploying to a real account is optional; see the course's `DEPLOY.md`. The network stack costs money while it runs (NAT gateways and their public IPv4 addresses are billed by the hour).
````

### `course_project/solutions/m05/infra/data.yaml`

````yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: shortly-infra M05 - data tier (PostgreSQL on RDS, a Valkey cache, the DynamoDB click counts)

Parameters:
  Prefix:
    Type: String
    Default: shortly
    AllowedPattern: '[a-z][a-z0-9-]{1,20}'
  Env:
    Type: String
    AllowedValues: [lab, prod]

Conditions:
  IsProd: !Equals [!Ref Env, prod]

Resources:
  DbSubnetGroup:
    Type: AWS::RDS::DBSubnetGroup
    Properties:
      DBSubnetGroupDescription: Data subnets for the Shortly database (no route to the internet)
      SubnetIds: !Split [',', !ImportValue {'Fn::Sub': '${Prefix}-data-subnet-ids'}]
      Tags:
        - {Key: project, Value: !Ref Prefix}
        - {Key: env, Value: !Ref Env}

  Database:
    Type: AWS::RDS::DBInstance
    DeletionPolicy: Snapshot
    UpdateReplacePolicy: Snapshot
    Properties:
      Engine: postgres
      EngineVersion: '17.9'
      DBInstanceClass: !If [IsProd, db.m7g.large, db.t4g.micro]
      AllocatedStorage: 20
      StorageType: gp3
      Port: 5432
      StorageEncrypted: true
      MasterUsername: shortly
      ManageMasterUserPassword: true
      DBSubnetGroupName: !Ref DbSubnetGroup
      VPCSecurityGroups:
        - !ImportValue {'Fn::Sub': '${Prefix}-db-sg-id'}
      PubliclyAccessible: false
      MultiAZ: !If [IsProd, true, false]
      BackupRetentionPeriod: !If [IsProd, 7, 1]
      DeletionProtection: !If [IsProd, true, false]
      CopyTagsToSnapshot: true
      Tags:
        - {Key: project, Value: !Ref Prefix}
        - {Key: env, Value: !Ref Env}

  AppDbSecretPolicy:
    Type: AWS::IAM::Policy
    Properties:
      PolicyName: !Sub '${Prefix}-app-db-secret'
      Roles: [!Sub '${Prefix}-app']
      PolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Sid: ReadManagedDbSecret
            Effect: Allow
            Action: secretsmanager:GetSecretValue
            Resource: !GetAtt Database.MasterUserSecret.SecretArn

  CacheSubnetGroup:
    Type: AWS::ElastiCache::SubnetGroup
    Properties:
      Description: Data subnets for the Shortly cache
      SubnetIds: !Split [',', !ImportValue {'Fn::Sub': '${Prefix}-data-subnet-ids'}]

  Cache:
    Type: AWS::ElastiCache::ReplicationGroup
    Properties:
      ReplicationGroupDescription: !Sub '${Prefix} redirect cache'
      Engine: valkey
      CacheNodeType: !If [IsProd, cache.m7g.large, cache.t4g.micro]
      NumCacheClusters: !If [IsProd, 2, 1]
      AutomaticFailoverEnabled: !If [IsProd, true, false]
      MultiAZEnabled: !If [IsProd, true, false]
      TransitEncryptionEnabled: true
      AtRestEncryptionEnabled: true
      CacheSubnetGroupName: !Ref CacheSubnetGroup
      SecurityGroupIds:
        - !ImportValue {'Fn::Sub': '${Prefix}-cache-sg-id'}
      Tags:
        - {Key: project, Value: !Ref Prefix}
        - {Key: env, Value: !Ref Env}

  ClicksTable:
    Type: AWS::DynamoDB::Table
    DeletionPolicy: Retain
    UpdateReplacePolicy: Retain
    Properties:
      TableName: !Sub '${Prefix}-clicks-daily'
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - {AttributeName: code, AttributeType: S}
        - {AttributeName: day, AttributeType: S}
      KeySchema:
        - {AttributeName: code, KeyType: HASH}
        - {AttributeName: day, KeyType: RANGE}
      PointInTimeRecoverySpecification:
        PointInTimeRecoveryEnabled: true
      TimeToLiveSpecification:
        AttributeName: expires_at
        Enabled: true
      DeletionProtectionEnabled: !If [IsProd, true, false]
      Tags:
        - {Key: project, Value: !Ref Prefix}
        - {Key: env, Value: !Ref Env}

Outputs:
  DbEndpointAddress:
    Value: !GetAtt Database.Endpoint.Address
    Export: {Name: !Sub '${Prefix}-db-endpoint'}
  DbPort:
    Value: !GetAtt Database.Endpoint.Port
    Export: {Name: !Sub '${Prefix}-db-port'}
  DbSecretArn:
    Value: !GetAtt Database.MasterUserSecret.SecretArn
    Export: {Name: !Sub '${Prefix}-db-secret-arn'}
  CacheEndpoint:
    Value: !GetAtt Cache.PrimaryEndPoint.Address
    Export: {Name: !Sub '${Prefix}-cache-endpoint'}
  ClicksTableName:
    Value: !Ref ClicksTable
    Export: {Name: !Sub '${Prefix}-clicks-table'}
  ClicksTableArn:
    Value: !GetAtt ClicksTable.Arn
    Export: {Name: !Sub '${Prefix}-clicks-table-arn'}
````

### `course_project/solutions/m05/README.md`

````markdown
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
````

### `week_04_storage/practice/exercises.py`

````python
"""
Week 04 drills — storage
========================
Run:    python practice/exercises.py          every drill
        python practice/exercises.py 4        drill 4 only
Drills 01–04 are pure Python models of how storage is billed and limited: what a storage class costs,
when a lifecycle rule moves an object, which EBS volume fits, and how a big upload is split. Drills
05–09 build, predict and fix the real thing with boto3 against moto (a fake AWS) or with the policy
evaluator you met in week 01. Drill 10 is a decide drill. Nothing here can touch a real account or
cost money.
The course's own versions of drills 01–04 (_harness/awslib/s3cost.py, lifecycle.py, ebs.py) are their
answer key — don't open them until you are done.
Note: moto stores what you send but enforces little. It never runs lifecycle rules, never copies
replicated objects, ignores Block Public Access, and treats a bucket-policy Deny crudely (it ignores
Principal and Condition). So the drills read your settings back, and the models and the policy
evaluator show the behaviour. Never open a presigned URL in a test: it could leave your machine.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.awsdrill import Drill, normalise, run  # noqa: E402
from _harness.awslib import prices  # noqa: E402


# ── Exercise 01 ★: What does this storage cost? ──────────────────────
"""
PRICES (given) are illustrative us-east-1 numbers from _harness/awslib/prices.toml. The six classes are
CLASSES; GLACIER means Glacier Flexible Retrieval and GLACIER_IR means Glacier Instant Retrieval.
Given: RATE_KEY (the price name of each class's storage), MIN_DAYS and MIN_OBJECT_KB (the billing minimums),
RETRIEVAL_KEY (retrieval price per GB, for the classes that charge it) and ARCHIVE_RETRIEVAL_KEY (the two
archive classes have a standard and a bulk retrieval price).
storage_cost(storage_class, objects, object_kb, days, retrieved_gb=0.0, *, retrieval="standard", price=PRICES) -> float
    USD to keep `objects` objects of `object_kb` KB each for `days` days, then retrieve `retrieved_gb` GB in
    total. Round to 2 decimal places.
      billable GB   = objects x max(object_kb, MIN_OBJECT_KB[class]) / 1,048,576      (1 GB = 1,048,576 KB)
      billable days = max(days, MIN_DAYS[class])
      storage       = billable GB x price per GB-month x billable days / 30           (a month = 30 days)
      retrieval     = retrieved_gb x the class's retrieval price     (Standard has none)
    `retrieval` ("standard" or "bulk") only changes the price for GLACIER and DEEP_ARCHIVE.
    ValueError for: an unknown class, an unknown retrieval option, a negative objects, object_kb, days
    or retrieved_gb.
cheapest_class(objects, object_kb, days, retrieved_gb=0.0, *, millisecond_access=True, single_az_ok=False, price=PRICES)
    -> (class, cost)
    The cheapest ALLOWED class. millisecond_access=True rules out GLACIER and DEEP_ARCHIVE (they take minutes
    to hours to read). ONEZONE_IA keeps data in one AZ, so it is allowed only when single_az_ok is True.
    A tie goes to the class that comes first in CLASSES. (Intelligent-Tiering is not modelled: week 11.)
Examples (1 TB = 1024 objects of 1 GiB = 1,048,576 KB):
    storage_cost("STANDARD", 1024, 1_048_576, 30) == 23.55
    storage_cost("STANDARD_IA", 1024, 1_048_576, 5) == 12.8      # deleted after 5 days, billed for 30
    storage_cost("STANDARD_IA", 1_000_000, 10, 30) == 1.53        # 10 KB objects are billed as 128 KB each
    cheapest_class(1024, 1_048_576, 365, 0) == ("GLACIER_IR", 49.83)
Why? Cheap classes are cheap because they charge for something else: a minimum time, a minimum size and a fee
per GB you read back. The cheapest class on the price list is often the dearest for your access pattern.
Hint: write storage_cost first; cheapest_class is a min() over the allowed classes (keep the first on a tie).
"""
PRICES = prices.section("storage")
CLASSES = ("STANDARD", "STANDARD_IA", "ONEZONE_IA", "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE")
MIN_DAYS = {"STANDARD": 0, "STANDARD_IA": 30, "ONEZONE_IA": 30, "GLACIER_IR": 90, "GLACIER": 90, "DEEP_ARCHIVE": 180}
MIN_OBJECT_KB = {"STANDARD": 0, "STANDARD_IA": 128, "ONEZONE_IA": 128, "GLACIER_IR": 128, "GLACIER": 0, "DEEP_ARCHIVE": 0}
RATE_KEY = {"STANDARD": "s3_standard_per_gb_month", "STANDARD_IA": "s3_standard_ia_per_gb_month",
            "ONEZONE_IA": "s3_onezone_ia_per_gb_month", "GLACIER_IR": "s3_glacier_ir_per_gb_month",
            "GLACIER": "s3_glacier_flexible_per_gb_month", "DEEP_ARCHIVE": "s3_deep_archive_per_gb_month"}
RETRIEVAL_KEY = {"STANDARD_IA": "s3_standard_ia_retrieval_per_gb", "ONEZONE_IA": "s3_onezone_ia_retrieval_per_gb",
                 "GLACIER_IR": "s3_glacier_ir_retrieval_per_gb"}
ARCHIVE_RETRIEVAL_KEY = {("GLACIER", "standard"): "s3_glacier_flexible_standard_retrieval_per_gb",
                         ("GLACIER", "bulk"): "s3_glacier_flexible_bulk_retrieval_per_gb",
                         ("DEEP_ARCHIVE", "standard"): "s3_deep_archive_standard_retrieval_per_gb",
                         ("DEEP_ARCHIVE", "bulk"): "s3_deep_archive_bulk_retrieval_per_gb"}


def storage_cost(storage_class, objects, object_kb, days, retrieved_gb=0.0, *, retrieval="standard", price=PRICES):
    raise NotImplementedError  # YOUR CODE


def cheapest_class(objects, object_kb, days, retrieved_gb=0.0, *, millisecond_access=True, single_az_ok=False, price=PRICES):
    raise NotImplementedError  # YOUR CODE


class Ex01(Drill):
    """What does this storage cost? ★"""
    tasks = ("4.1",)
    TB = (1024, 1_048_576)   # 1 TB as 1024 objects of 1 GiB

    def test_a_month_in_each_class(self):
        want = {"STANDARD": 23.55, "STANDARD_IA": 12.8, "ONEZONE_IA": 10.24, "GLACIER_IR": 12.29, "GLACIER": 11.06, "DEEP_ARCHIVE": 6.08}
        for cls, cost in want.items():
            with self.subTest(cls=cls):
                self.assertEqual(storage_cost(cls, *self.TB, 30), cost)

    def test_a_year_in_each_class(self):
        want = {"STANDARD": 286.55, "STANDARD_IA": 155.73, "GLACIER_IR": 49.83, "GLACIER": 44.85, "DEEP_ARCHIVE": 12.33}
        for cls, cost in want.items():
            with self.subTest(cls=cls):
                self.assertEqual(storage_cost(cls, *self.TB, 365), cost, "days / 30 x the monthly rate")

    def test_deleting_early_still_pays_the_minimum_duration(self):
        self.assertEqual(storage_cost("STANDARD", *self.TB, 5), 3.93, "Standard has no minimum: 5 days cost 5 days")
        for cls in ("STANDARD_IA", "ONEZONE_IA", "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE"):
            with self.subTest(cls=cls):
                self.assertEqual(storage_cost(cls, *self.TB, 5), storage_cost(cls, *self.TB, MIN_DAYS[cls]),
                                 f"{cls} bills at least {MIN_DAYS[cls]} days even if you delete after 5")
        self.assertEqual(storage_cost("STANDARD_IA", *self.TB, 45), 19.2, "past the minimum, the real days count")

    def test_tiny_objects_are_billed_at_the_minimum_size(self):
        self.assertEqual(storage_cost("STANDARD", 1_000_000, 10, 30), 0.22)
        self.assertEqual(storage_cost("STANDARD_IA", 1_000_000, 10, 30), 1.53, "10 KB objects bill as 128 KB in Standard-IA")
        self.assertEqual(storage_cost("STANDARD_IA", 1_000_000, 10, 30), storage_cost("STANDARD_IA", 1_000_000, 128, 30))
        self.assertEqual(storage_cost("GLACIER_IR", 1_000_000, 10, 30), 1.46)
        self.assertEqual(storage_cost("GLACIER", 1_000_000, 10, 90), 0.1, "Glacier Flexible has no minimum size here")
        self.assertEqual(storage_cost("STANDARD_IA", 1_000_000, 200, 30), 2.38, "above the minimum, the real size counts")

    def test_retrieval_fees(self):
        self.assertEqual(storage_cost("STANDARD", *self.TB, 365, 100), 286.55, "Standard has no retrieval fee")
        self.assertEqual(storage_cost("STANDARD_IA", *self.TB, 365, 100), 156.73)
        self.assertEqual(storage_cost("GLACIER_IR", *self.TB, 365, 100), 52.83)
        self.assertEqual(storage_cost("GLACIER", *self.TB, 365, 100), 45.85)
        self.assertEqual(storage_cost("DEEP_ARCHIVE", *self.TB, 365, 100), 14.33)

    def test_bulk_retrieval(self):
        self.assertEqual(storage_cost("GLACIER", *self.TB, 100, 100, retrieval="bulk"), 12.29, "bulk from Flexible Retrieval is free")
        self.assertEqual(storage_cost("DEEP_ARCHIVE", *self.TB, 200, 100, retrieval="bulk"), 7.01)
        self.assertEqual(storage_cost("DEEP_ARCHIVE", *self.TB, 200, 100), 8.76, "standard retrieval is the default")
        self.assertEqual(storage_cost("STANDARD_IA", *self.TB, 30, 100, retrieval="bulk"), 13.8, "bulk only matters for the archive classes")

    def test_the_price_argument_is_used(self):
        custom = dict(PRICES, s3_standard_per_gb_month=0.5)
        self.assertEqual(storage_cost("STANDARD", 10, 1_048_576, 30, price=custom), 5.0)

    def test_storage_cost_rejects_bad_inputs(self):
        for call in (lambda: storage_cost("GLACIER_FLEX", 1, 1, 1), lambda: storage_cost("STANDARD", -1, 1, 1),
                     lambda: storage_cost("STANDARD", 1, -1, 1), lambda: storage_cost("STANDARD", 1, 1, -1),
                     lambda: storage_cost("STANDARD", 1, 1, 1, -1), lambda: storage_cost("GLACIER", 1, 1, 1, retrieval="expedited")):
            with self.subTest():
                with self.assertRaises(ValueError):
                    call()

    def test_a_year_kept_and_read_once_wants_an_archive_class(self):
        self.assertEqual(cheapest_class(*self.TB, 365, 0), ("GLACIER_IR", 49.83))
        self.assertEqual(cheapest_class(*self.TB, 365, 0, millisecond_access=False), ("DEEP_ARCHIVE", 12.33))
        self.assertEqual(cheapest_class(*self.TB, 365, 1024), ("GLACIER_IR", 80.55), "reading it all back adds 3 cents per GB")
        self.assertEqual(cheapest_class(*self.TB, 365, 1024, millisecond_access=False), ("DEEP_ARCHIVE", 32.81))

    def test_hot_or_tiny_data_stays_in_standard(self):
        self.assertEqual(cheapest_class(1_000_000, 10, 365), ("STANDARD", 2.67), "tiny objects: the 128 KB minimum kills the IA classes")
        self.assertEqual(cheapest_class(*self.TB, 10, 0, single_az_ok=True), ("STANDARD", 7.85), "10 days: the 30-day minimum is paid in full")
        self.assertEqual(cheapest_class(1000, 10, 365, 0)[0], "STANDARD")

    def test_one_month_data_is_cheapest_in_glacier_instant(self):
        self.assertEqual(cheapest_class(*self.TB, 30, 0), ("GLACIER_IR", 12.29), "Glacier IR beats Standard-IA, even at 30 days")

    def test_one_zone_needs_permission(self):
        self.assertEqual(cheapest_class(*self.TB, 30, 0, single_az_ok=True), ("ONEZONE_IA", 10.24))
        self.assertEqual(cheapest_class(*self.TB, 30, 0)[0], "GLACIER_IR", "without single_az_ok, One Zone-IA is out")
        self.assertEqual(cheapest_class(*self.TB, 60, 500, single_az_ok=True), ("ONEZONE_IA", 25.48))
        self.assertEqual(cheapest_class(*self.TB, 365, 10000, single_az_ok=True), ("ONEZONE_IA", 224.59))

    def test_cheapest_uses_the_price_argument(self):
        custom = dict(PRICES, s3_standard_per_gb_month=0.0001)
        self.assertEqual(cheapest_class(*self.TB, 365, 0, price=custom)[0], "STANDARD")


# ── Exercise 02 ★: When does this object move? ───────────────────────
"""
A lifecycle configuration is a list of rules in the S3 API shape (what boto3 put_bucket_lifecycle_configuration
takes). A rule is a dict with these keys (all optional except Status and at least one action):
    "ID": str                       "Status": "Enabled" or "Disabled"        "Filter": {...}   (missing means {})
    "Transitions": [{"Days": 30, "StorageClass": "STANDARD_IA"}, ...]
    "Expiration": {"Days": 365}  or  {"ExpiredObjectDeleteMarker": True}
    "NoncurrentVersionTransitions": [{"NoncurrentDays": 30, "StorageClass": "GLACIER_IR"}, ...]
    "NoncurrentVersionExpiration": {"NoncurrentDays": 90, "NewerNoncurrentVersions": 3}
    "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7}
A Filter is ONE of: {"Prefix": "logs/"}, {"Tag": {"Key": k, "Value": v}}, {"ObjectSizeGreaterThan": n},
{"ObjectSizeLessThan": n} or {"And": {"Prefix": ..., "Tags": [{"Key": k, "Value": v}], "ObjectSizeGreaterThan": n,
"ObjectSizeLessThan": n}}. Two of them side by side is not allowed: combine them inside "And". Sizes are bytes.
WATERFALL = STANDARD, STANDARD_IA, INTELLIGENT_TIERING, ONEZONE_IA, GLACIER_IR, GLACIER, DEEP_ARCHIVE (given).
Objects only move DOWN it, and not every step is allowed. ALLOWED_NEXT (given) lists, for each class, the classes
it may move to. Deep Archive is one-way.
validate(rules) -> None
    Raise ValueError (the message names the rule and the constraint) for:
      more than 1000 rules; an ID longer than 255 characters or used twice; a Status that is not Enabled/Disabled;
      a rule with no action at all; a Filter with two of its parts side by side (not in "And");
      a transition to a class that is not in the waterfall or is STANDARD, or one the previous class may not
      move to (start from STANDARD); transition days (or NoncurrentDays) that do not increase;
      the TWO-STEP MINIMUM: a later transition must come at least the previous class's MIN_DAYS after the earlier
      one (Glacier IR at day 4 means Deep Archive no earlier than day 94; Standard-IA at 30 means Glacier no earlier
      than 60), because an object that leaves a class early is still billed for the minimum;
      Expiration with both or neither of Days and ExpiredObjectDeleteMarker; Expiration Days that is not later than
      every transition; ExpiredObjectDeleteMarker or AbortIncompleteMultipartUpload on a rule whose filter uses a
      tag; NewerNoncurrentVersions without NoncurrentDays, outside 1 to 100, or in a rule with no "Filter" key;
      a NoncurrentVersionExpiration that is not later than every noncurrent transition.
    Apply the waterfall, increasing-days and two-step checks to NoncurrentVersionTransitions too.
    Do NOT require 30 days before Standard-IA: the course's research could not confirm that old rule.
current_class(rules, key, age_days, size_bytes, tags=None) -> str
    The storage class of a CURRENT object `age_days` old once the rules have run: a class name or "EXPIRED".
    Only Enabled rules count. A rule applies when its Filter matches: the key starts with the Prefix; every filter
    tag is on the object with that value; size_bytes is STRICTLY greater than ObjectSizeGreaterThan and STRICTLY
    less than ObjectSizeLessThan. (An empty Filter matches everything.)
    A transition counts once age_days >= its Days. If several rules apply: expiration wins over any transition
    (Expiration Days <= age_days -> "EXPIRED"); among transitions, the one furthest down the waterfall wins.
    SMALL OBJECTS: an object under 128 KB (131,072 bytes) is not transitioned unless the rule's Filter has an
    object-size part. It still expires. No transition reached -> "STANDARD".
noncurrent_fate(rules, key, days_noncurrent, newer_noncurrent=0, size_bytes=1 << 20, tags=None) -> str
    Same idea for a NONCURRENT version, `days_noncurrent` days after it stopped being current, when
    `newer_noncurrent` newer noncurrent versions of the same key exist. "DELETED" when a NoncurrentVersionExpiration
    applies (days_noncurrent >= its NoncurrentDays and, if it has NewerNoncurrentVersions, newer_noncurrent >= that
    number); otherwise the furthest NoncurrentVersionTransitions class reached, else "STANDARD". The same filter and
    small-object rules apply.
Example (a logs rule):
    LOGS = [{"ID": "logs", "Status": "Enabled", "Filter": {"Prefix": "logs/"},
             "Transitions": [{"Days": 30, "StorageClass": "STANDARD_IA"}, {"Days": 90, "StorageClass": "GLACIER"}],
             "Expiration": {"Days": 365}}]
    current_class(LOGS, "logs/a.gz", 45, 1 << 20) == "STANDARD_IA"      current_class(LOGS, "logs/a.gz", 400, 1 << 20) == "EXPIRED"
    current_class(LOGS, "logs/a.gz", 45, 1000) == "STANDARD"           # tiny: not transitioned
Why? Lifecycle rules are how you stop paying Standard prices for old data, but every move has rules: the
waterfall, minimum durations that make a quick second hop pointless, and small objects that cost more in
IA than they save. AWS runs lifecycle in the background; these functions give the state once the rule has run.
Hint: write a helper that flattens a Filter (look inside "And") and one that says whether a rule applies;
      max(classes, key=WATERFALL.index) finds the furthest class.
"""
WATERFALL = ("STANDARD", "STANDARD_IA", "INTELLIGENT_TIERING", "ONEZONE_IA", "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE")
ALLOWED_NEXT = {
    "STANDARD": WATERFALL[1:],
    "STANDARD_IA": ("INTELLIGENT_TIERING", "ONEZONE_IA", "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE"),
    "INTELLIGENT_TIERING": ("ONEZONE_IA", "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE"),
    "ONEZONE_IA": ("GLACIER", "DEEP_ARCHIVE"),
    "GLACIER_IR": ("GLACIER", "DEEP_ARCHIVE"),
    "GLACIER": ("DEEP_ARCHIVE",),
    "DEEP_ARCHIVE": (),
}


def validate(rules):
    raise NotImplementedError  # YOUR CODE


def current_class(rules, key, age_days, size_bytes, tags=None):
    raise NotImplementedError  # YOUR CODE


def noncurrent_fate(rules, key, days_noncurrent, newer_noncurrent=0, size_bytes=1 << 20, tags=None):
    raise NotImplementedError  # YOUR CODE


class Ex02(Drill):
    """When does this object move? ★"""
    tasks = ("4.1", "1.3")
    MIB = 1 << 20
    LOGS = [{"ID": "logs", "Status": "Enabled", "Filter": {"Prefix": "logs/"},
             "Transitions": [{"Days": 30, "StorageClass": "STANDARD_IA"}, {"Days": 90, "StorageClass": "GLACIER"}],
             "Expiration": {"Days": 365}}]
    VERSIONED = [{"ID": "old-versions", "Status": "Enabled", "Filter": {},
                  "NoncurrentVersionTransitions": [{"NoncurrentDays": 30, "StorageClass": "GLACIER_IR"}],
                  "NoncurrentVersionExpiration": {"NoncurrentDays": 90, "NewerNoncurrentVersions": 3}}]

    def rule(self, **parts):
        return dict({"ID": "r", "Status": "Enabled", "Filter": {}}, **parts)

    def test_good_rules_are_accepted(self):
        good = [self.LOGS, self.VERSIONED,
                [self.rule(Transitions=[{"Days": 4, "StorageClass": "GLACIER_IR"}, {"Days": 94, "StorageClass": "DEEP_ARCHIVE"}])],
                [self.rule(Transitions=[{"Days": 30, "StorageClass": "STANDARD_IA"}, {"Days": 60, "StorageClass": "GLACIER"}])],
                [self.rule(Filter={"Prefix": "tmp/"}, Expiration={"ExpiredObjectDeleteMarker": True})],
                [self.rule(Filter={"And": {"Prefix": "a/", "Tags": [{"Key": "k", "Value": "v"}]}}, Expiration={"Days": 30})],
                [self.rule(AbortIncompleteMultipartUpload={"DaysAfterInitiation": 7})],
                [self.rule(Status="Disabled", Expiration={"Days": 1})],
                [{"ID": "x", "Status": "Enabled", "Expiration": {"Days": 10}}]]
        for rules in good:
            with self.subTest(rules=rules):
                validate(rules)

    def test_validation_status_actions_and_ids(self):
        bad = {
            "bad status": [self.rule(Status="On", Expiration={"Days": 30})],
            "no action": [self.rule()],
            "duplicate ids": [self.rule(Expiration={"Days": 30}), self.rule(Expiration={"Days": 60})],
            "id too long": [self.rule(ID="x" * 256, Expiration={"Days": 30})],
            "too many rules": [self.rule(ID=f"r{i}", Expiration={"Days": 30}) for i in range(1001)],
            "filter parts side by side": [self.rule(Filter={"Prefix": "a/", "Tag": {"Key": "k", "Value": "v"}}, Expiration={"Days": 30})],
        }
        for label, rules in bad.items():
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    validate(rules)

    def test_validation_waterfall(self):
        def t(*steps):
            return [self.rule(Transitions=[{"Days": d, "StorageClass": c} for c, d in steps])]
        bad = {
            "back up the waterfall": t(("GLACIER", 90), ("STANDARD_IA", 200)),
            "to Standard": t(("STANDARD", 30)),
            "unknown class": t(("BOGUS", 30)),
            "out of Deep Archive": t(("DEEP_ARCHIVE", 100), ("GLACIER", 400)),
            "One Zone-IA to Standard-IA": t(("ONEZONE_IA", 30), ("STANDARD_IA", 90)),
            "days that do not increase": t(("STANDARD_IA", 60), ("GLACIER", 60)),
            "days that go down": t(("STANDARD_IA", 60), ("GLACIER", 40)),
        }
        for label, rules in bad.items():
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    validate(rules)

    def test_validation_two_step_minimum(self):
        def t(*steps):
            return [self.rule(Transitions=[{"Days": d, "StorageClass": c} for c, d in steps])]
        for label, rules in {"Glacier IR at 4, Deep Archive at 50": t(("GLACIER_IR", 4), ("DEEP_ARCHIVE", 50)),
                             "Standard-IA at 30, Glacier at 40": t(("STANDARD_IA", 30), ("GLACIER", 40)),
                             "Glacier at 100, Deep Archive at 150": t(("GLACIER", 100), ("DEEP_ARCHIVE", 150))}.items():
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    validate(rules)
        validate(t(("GLACIER", 100), ("DEEP_ARCHIVE", 190)))
        with self.assertRaises(ValueError):
            validate([self.rule(NoncurrentVersionTransitions=[{"NoncurrentDays": 4, "StorageClass": "GLACIER_IR"},
                                                              {"NoncurrentDays": 50, "StorageClass": "DEEP_ARCHIVE"}])])
        with self.assertRaises(ValueError):
            validate([self.rule(NoncurrentVersionTransitions=[{"NoncurrentDays": 90, "StorageClass": "GLACIER"},
                                                              {"NoncurrentDays": 120, "StorageClass": "STANDARD_IA"}])])

    def test_validation_expiration(self):
        bad = {
            "expires before it transitions": [self.rule(Transitions=[{"Days": 30, "StorageClass": "STANDARD_IA"}], Expiration={"Days": 20})],
            "expires the day it transitions": [self.rule(Transitions=[{"Days": 30, "StorageClass": "STANDARD_IA"}], Expiration={"Days": 30})],
            "both kinds of expiration": [self.rule(Expiration={"Days": 30, "ExpiredObjectDeleteMarker": True})],
            "neither kind of expiration": [self.rule(Expiration={})],
            "delete marker with a tag filter": [self.rule(Filter={"Tag": {"Key": "k", "Value": "v"}}, Expiration={"ExpiredObjectDeleteMarker": True})],
            "abort multipart with a tag filter": [self.rule(Filter={"And": {"Prefix": "a/", "Tags": [{"Key": "k", "Value": "v"}]}},
                                                            AbortIncompleteMultipartUpload={"DaysAfterInitiation": 7})],
        }
        for label, rules in bad.items():
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    validate(rules)

    def test_validation_noncurrent_versions(self):
        trans = [{"NoncurrentDays": 30, "StorageClass": "GLACIER_IR"}]
        bad = {
            "newer count without days": [self.rule(NoncurrentVersionExpiration={"NewerNoncurrentVersions": 3})],
            "newer count of 0": [self.rule(NoncurrentVersionExpiration={"NoncurrentDays": 30, "NewerNoncurrentVersions": 0})],
            "newer count of 101": [self.rule(NoncurrentVersionExpiration={"NoncurrentDays": 30, "NewerNoncurrentVersions": 101})],
            "newer count with no Filter element": [{"ID": "x", "Status": "Enabled",
                                                    "NoncurrentVersionExpiration": {"NoncurrentDays": 30, "NewerNoncurrentVersions": 3}}],
            "deleted before it transitions": [self.rule(NoncurrentVersionTransitions=trans, NoncurrentVersionExpiration={"NoncurrentDays": 30})],
        }
        for label, rules in bad.items():
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    validate(rules)
        validate([self.rule(NoncurrentVersionExpiration={"NoncurrentDays": 30, "NewerNoncurrentVersions": 100})])

    def test_a_logs_rule_by_age(self):
        want = {0: "STANDARD", 29: "STANDARD", 30: "STANDARD_IA", 89: "STANDARD_IA", 90: "GLACIER", 364: "GLACIER", 365: "EXPIRED", 1000: "EXPIRED"}
        for age, cls in want.items():
            with self.subTest(age=age):
                self.assertEqual(current_class(self.LOGS, "logs/a.gz", age, self.MIB), cls)

    def test_a_filter_that_does_not_match_changes_nothing(self):
        self.assertEqual(current_class(self.LOGS, "images/a.png", 1000, self.MIB), "STANDARD")
        self.assertEqual(current_class(self.LOGS, "xlogs/a.gz", 100, self.MIB), "STANDARD", "a prefix must match from the start of the key")

    def test_small_objects_are_not_transitioned(self):
        self.assertEqual(current_class(self.LOGS, "logs/a", 100, 100 * 1024), "STANDARD", "100 KB is under the 128 KB default minimum")
        self.assertEqual(current_class(self.LOGS, "logs/a", 100, 131_071), "STANDARD")
        self.assertEqual(current_class(self.LOGS, "logs/a", 100, 131_072), "GLACIER", "exactly 128 KB is big enough")
        self.assertEqual(current_class(self.LOGS, "logs/a", 400, 100), "EXPIRED", "small objects still expire")

    def test_an_object_size_filter_lets_small_objects_move(self):
        small = [self.rule(Filter={"ObjectSizeLessThan": 100_000}, Transitions=[{"Days": 30, "StorageClass": "STANDARD_IA"}])]
        self.assertEqual(current_class(small, "k", 40, 50_000), "STANDARD_IA", "the size filter explicitly asks for small objects")
        self.assertEqual(current_class(small, "k", 40, 200_000), "STANDARD", "too big for the filter")
        self.assertEqual(current_class(small, "k", 40, 100_000), "STANDARD", "ObjectSizeLessThan is strict")
        big = [self.rule(Filter={"And": {"Prefix": "v/", "ObjectSizeGreaterThan": 1_000_000}},
                         Transitions=[{"Days": 30, "StorageClass": "STANDARD_IA"}])]
        self.assertEqual(current_class(big, "v/a", 40, 1_000_001), "STANDARD_IA")
        self.assertEqual(current_class(big, "v/a", 40, 1_000_000), "STANDARD", "ObjectSizeGreaterThan is strict")
        self.assertEqual(current_class(big, "w/a", 40, 5_000_000), "STANDARD", "prefix AND size must both match")

    def test_tag_filters(self):
        single = [self.rule(Filter={"Tag": {"Key": "archive", "Value": "yes"}}, Transitions=[{"Days": 30, "StorageClass": "GLACIER_IR"}])]
        self.assertEqual(current_class(single, "k", 40, self.MIB, {"archive": "yes", "team": "x"}), "GLACIER_IR")
        self.assertEqual(current_class(single, "k", 40, self.MIB, {"archive": "no"}), "STANDARD")
        self.assertEqual(current_class(single, "k", 40, self.MIB), "STANDARD")
        both = [self.rule(Filter={"And": {"Prefix": "a/", "Tags": [{"Key": "k1", "Value": "v1"}, {"Key": "k2", "Value": "v2"}]}},
                          Transitions=[{"Days": 30, "StorageClass": "GLACIER_IR"}])]
        self.assertEqual(current_class(both, "a/x", 40, self.MIB, {"k1": "v1", "k2": "v2"}), "GLACIER_IR")
        self.assertEqual(current_class(both, "a/x", 40, self.MIB, {"k1": "v1"}), "STANDARD", "every tag must match")
        self.assertEqual(current_class(both, "b/x", 40, self.MIB, {"k1": "v1", "k2": "v2"}), "STANDARD")

    def test_disabled_rules_do_nothing(self):
        off = [dict(self.LOGS[0], Status="Disabled")]
        self.assertEqual(current_class(off, "logs/a.gz", 1000, self.MIB), "STANDARD")

    def test_expiration_beats_transition_and_the_furthest_transition_wins(self):
        a = self.rule(ID="a", Transitions=[{"Days": 30, "StorageClass": "GLACIER"}])
        b = self.rule(ID="b", Expiration={"Days": 60})
        for rules in ([a, b], [b, a]):
            self.assertEqual(current_class(rules, "k", 59, self.MIB), "GLACIER")
            self.assertEqual(current_class(rules, "k", 60, self.MIB), "EXPIRED", "expiration beats a transition, whatever the rule order")
        c = self.rule(ID="c", Transitions=[{"Days": 30, "StorageClass": "STANDARD_IA"}])
        d = self.rule(ID="d", Transitions=[{"Days": 30, "StorageClass": "GLACIER_IR"}])
        for rules in ([c, d], [d, c]):
            self.assertEqual(current_class(rules, "k", 30, self.MIB), "GLACIER_IR", "two rules at once: the furthest class wins")

    def test_noncurrent_versions(self):
        for days, newer, want in ((10, 0, "STANDARD"), (30, 0, "GLACIER_IR"), (89, 5, "GLACIER_IR"), (90, 2, "GLACIER_IR"),
                                  (90, 3, "DELETED"), (400, 0, "GLACIER_IR"), (400, 10, "DELETED"), (45, 50, "GLACIER_IR")):
            with self.subTest(days=days, newer=newer):
                self.assertEqual(noncurrent_fate(self.VERSIONED, "k", days, newer), want,
                                 "delete only when the version is old enough AND at least 3 newer noncurrent versions exist")

    def test_noncurrent_expiration_without_a_count_is_by_age_alone(self):
        rules = [self.rule(NoncurrentVersionExpiration={"NoncurrentDays": 90})]
        self.assertEqual(noncurrent_fate(rules, "k", 89), "STANDARD")
        self.assertEqual(noncurrent_fate(rules, "k", 90), "DELETED")

    def test_noncurrent_small_versions_and_filters(self):
        self.assertEqual(noncurrent_fate(self.VERSIONED, "k", 40, size_bytes=1000), "STANDARD", "small versions are not transitioned")
        self.assertEqual(noncurrent_fate(self.VERSIONED, "k", 100, 5, size_bytes=1000), "DELETED", "but they can still be deleted")
        scoped = [self.rule(Filter={"Prefix": "docs/"}, NoncurrentVersionTransitions=[{"NoncurrentDays": 30, "StorageClass": "GLACIER_IR"}])]
        self.assertEqual(noncurrent_fate(scoped, "docs/a", 40), "GLACIER_IR")
        self.assertEqual(noncurrent_fate(scoped, "other/a", 40), "STANDARD")


# ── Exercise 03 ★: Pick the volume ───────────────────────────────────
"""
An EBS volume lives in one AZ and is attached to an instance. Pick the type and check the limits.
PRICES (given) are illustrative numbers from prices.toml. Types: gp3, gp2, io2, st1, sc1 (VOLUME_TYPES).
Limits (given as SIZE_GIB, in GiB): gp3 1 to 65,536 (64 TiB); gp2 1 to 16,384; io2 4 to 65,536;
st1 and sc1 125 to 16,384. They are HDDs: never boot volumes, and big-sequential-only.
gp2_iops(size_gib) -> int
    gp2 gives 3 IOPS per GiB, at least 100 and at most 16,000 (reached at 5,334 GiB). ValueError outside its size range.
gp3_config(size_gib, iops=None, throughput=None) -> {"iops": ..., "throughput": ...}
    gp3 includes 3,000 IOPS and 125 MiB/s at ANY size, free. None means that baseline. Provisioning less is a ValueError.
    Above the baseline: IOPS at most 500 per GiB (so 10 GiB allows 5,000) and 80,000 in total; throughput at most
    0.25 MiB/s per provisioned IOPS and 2,000 MiB/s in total. ValueError for any limit broken or a size out of range.
monthly_cost(volume_type, size_gib, iops=None, throughput=None, price=PRICES) -> float     (2 decimal places)
    gp3: size x ebs_gp3_per_gb_month, PLUS ebs_gp3_per_iops_month for each IOPS above 3,000, PLUS
         ebs_gp3_per_mibps_month for each MiB/s above 125. The baseline is free.
    gp2, st1, sc1: size x their per-GB price; iops or throughput given -> ValueError (nothing to provision).
    io2: size x ebs_io2_per_gb_month, PLUS provisioned IOPS: ebs_io2_per_iops_month_first_32k for the first 32,000,
         ebs_io2_per_iops_month_32k_to_64k for the next 32,000. `iops` is required, at most 1,000 per GiB and 256,000;
         above 64,000 has no price here -> ValueError. throughput above 4,000 -> ValueError.
    An unknown type (io1 is left out) or a size out of range -> ValueError.
choose_volume(iops=0, throughput_mibs=0, *, boot=False, multi_attach=False, sequential=False, rarely_accessed=False) -> str
    The cheapest type that does the job, by these rules in order:
      1. multi_attach with boot -> ValueError (a Multi-Attach volume cannot be a boot volume).
         Negative iops or throughput -> ValueError. More than 256,000 IOPS or 4,000 MiB/s -> ValueError (no EBS volume does).
      2. Multi-Attach (only io1/io2 support it), or iops above gp3's 80,000, or throughput above gp3's 2,000 -> "io2".
      3. sequential and not boot: "sc1" if rarely_accessed and the need fits sc1 (250 IOPS and 250 MiB/s),
         else "st1" if it fits st1 (500 IOPS and 500 MiB/s).
      4. Otherwise "gp3".
Examples:
    gp2_iops(1000) == 3000     gp3_config(100) == {"iops": 3000, "throughput": 125}     monthly_cost("gp3", 100) == 8.0
    monthly_cost("gp3", 1000, 6000) == 95.0      monthly_cost("io2", 100, 5000) == 337.5      choose_volume(iops=100000) == "io2"
Why? gp3 is cheaper than gp2 and its speed is independent of its size, so gp3 is the default. io2 is for
the database that needs more than gp3 can give, or a volume shared by two instances. HDDs are for big
sequential reads (logs, data warehouses) and cold data, never for boot or random I/O.
Hint: gp3_config does all the validating; monthly_cost for gp3 calls it and charges only for the part above the baseline.
"""
SIZE_GIB = {"gp3": (1, 65_536), "gp2": (1, 16_384), "io2": (4, 65_536), "st1": (125, 16_384), "sc1": (125, 16_384)}
VOLUME_TYPES = tuple(SIZE_GIB)


def gp2_iops(size_gib):
    raise NotImplementedError  # YOUR CODE


def gp3_config(size_gib, iops=None, throughput=None):
    raise NotImplementedError  # YOUR CODE


def monthly_cost(volume_type, size_gib, iops=None, throughput=None, price=PRICES):
    raise NotImplementedError  # YOUR CODE


def choose_volume(iops=0, throughput_mibs=0, *, boot=False, multi_attach=False, sequential=False, rarely_accessed=False):
    raise NotImplementedError  # YOUR CODE


class Ex03(Drill):
    """Pick the volume ★"""
    tasks = ("3.1", "4.1")

    def test_gp2_iops(self):
        for size, want in {1: 100, 33: 100, 34: 102, 1000: 3000, 5333: 15999, 5334: 16000, 6000: 16000, 16384: 16000}.items():
            with self.subTest(size=size):
                self.assertEqual(gp2_iops(size), want, "3 IOPS per GiB, never below 100 or above 16,000")

    def test_gp2_rejects_bad_sizes(self):
        for size in (0, 16385):
            with self.subTest(size=size):
                with self.assertRaises(ValueError):
                    gp2_iops(size)

    def test_gp3_baseline_is_free_at_any_size(self):
        self.assertEqual(gp3_config(1), {"iops": 3000, "throughput": 125})
        self.assertEqual(gp3_config(100), {"iops": 3000, "throughput": 125})
        self.assertEqual(gp3_config(100, 3000, 125), {"iops": 3000, "throughput": 125})
        self.assertEqual(gp3_config(1000, 16000, 1000), {"iops": 16000, "throughput": 1000})
        self.assertEqual(gp3_config(10, 5000), {"iops": 5000, "throughput": 125}, "500 IOPS per GiB: 10 GiB allows 5,000")
        self.assertEqual(gp3_config(200, 3000, 750), {"iops": 3000, "throughput": 750}, "0.25 MiB/s per IOPS: 3,000 allows 750")

    def test_gp3_limits(self):
        bad = {"size 0": (0,), "size over 64 TiB": (65_537,), "below the IOPS baseline": (100, 2999),
               "below the throughput baseline": (100, None, 124), "over 80,000 IOPS": (1000, 80_001),
               "more than 500 IOPS per GiB": (10, 5001), "throughput over 0.25 per IOPS": (200, 3000, 751),
               "over 2,000 MiB/s": (1000, 80_000, 2001)}
        for label, args in bad.items():
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    gp3_config(*args)
        self.assertEqual(gp3_config(1000, 80_000, 2000), {"iops": 80_000, "throughput": 2000})

    def test_gp3_costs(self):
        self.assertEqual(monthly_cost("gp3", 100), 8.0)
        self.assertEqual(monthly_cost("gp3", 1000), 80.0, "the free baseline is never charged")
        self.assertEqual(monthly_cost("gp3", 1000, 6000), 95.0, "only the 3,000 IOPS above the baseline are charged")
        self.assertEqual(monthly_cost("gp3", 1000, 6000, 500), 117.5, "plus 375 MiB/s above 125")
        self.assertEqual(monthly_cost("gp3", 500, 16000, 1000), 157.5)
        self.assertEqual(monthly_cost("gp3", 100, 3000, 125), 8.0)

    def test_other_volume_costs(self):
        self.assertEqual(monthly_cost("gp2", 1000), 100.0)
        self.assertEqual(monthly_cost("st1", 1000), 45.0)
        self.assertEqual(monthly_cost("sc1", 1000), 15.0)
        self.assertEqual(monthly_cost("io2", 100, 5000), 337.5)
        self.assertEqual(monthly_cost("io2", 1000, 50000), 3033.0, "32,000 IOPS at the first rate, 18,000 at the second")
        self.assertEqual(monthly_cost("io2", 2000, 64000), 3802.0)

    def test_gp3_beats_gp2_for_the_same_speed(self):
        for size in (100, 500, 1000, 3000, 5334):
            with self.subTest(size=size):
                speed = gp2_iops(size)
                self.assertLess(monthly_cost("gp3", size, max(3000, speed)), monthly_cost("gp2", size),
                                f"{size} GiB: gp3 gives the same {speed} IOPS for less money")
        self.assertEqual(monthly_cost("gp3", 5334, 16000), 491.72)
        self.assertEqual(monthly_cost("gp2", 5334), 533.4)

    def test_cost_rejects_bad_inputs(self):
        calls = {"gp2 with iops": lambda: monthly_cost("gp2", 100, 3000), "st1 with throughput": lambda: monthly_cost("st1", 500, None, 100),
                 "st1 under 125 GiB": lambda: monthly_cost("st1", 124), "io2 without iops": lambda: monthly_cost("io2", 100),
                 "io2 under 4 GiB": lambda: monthly_cost("io2", 3, 100), "io2 over 1,000 IOPS per GiB": lambda: monthly_cost("io2", 10, 10001),
                 "io2 above the priced range": lambda: monthly_cost("io2", 1000, 70000), "io2 over 4,000 MiB/s": lambda: monthly_cost("io2", 100, 5000, 4001),
                 "unknown type": lambda: monthly_cost("io1", 100, 1000), "gp3 over the ratio": lambda: monthly_cost("gp3", 10, 6000)}
        for label, call in calls.items():
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    call()

    def test_the_price_argument_is_used(self):
        custom = dict(PRICES, ebs_gp3_per_gb_month=1.0, ebs_gp3_per_iops_month=0.0, ebs_gp3_per_mibps_month=0.0)
        self.assertEqual(monthly_cost("gp3", 10, 5000, 500, price=custom), 10.0)

    def test_choose_volume_default_and_high_end(self):
        self.assertEqual(choose_volume(), "gp3")
        self.assertEqual(choose_volume(iops=6000, throughput_mibs=500), "gp3")
        self.assertEqual(choose_volume(iops=80_000, throughput_mibs=2000), "gp3", "gp3's own maximum is still gp3")
        self.assertEqual(choose_volume(iops=80_001), "io2")
        self.assertEqual(choose_volume(iops=100_000), "io2")
        self.assertEqual(choose_volume(throughput_mibs=2001), "io2")
        self.assertEqual(choose_volume(iops=100, multi_attach=True), "io2", "only io1/io2 can be attached to several instances")

    def test_choose_volume_hdds(self):
        self.assertEqual(choose_volume(iops=300, throughput_mibs=400, sequential=True), "st1")
        self.assertEqual(choose_volume(iops=100, throughput_mibs=200, sequential=True, rarely_accessed=True), "sc1")
        self.assertEqual(choose_volume(iops=400, throughput_mibs=500, sequential=True, rarely_accessed=True), "st1", "too fast for sc1")
        self.assertEqual(choose_volume(iops=600, throughput_mibs=100, sequential=True), "gp3", "too many IOPS for an HDD")
        self.assertEqual(choose_volume(iops=300, throughput_mibs=400), "gp3", "random access: no HDD")
        self.assertEqual(choose_volume(iops=100, throughput_mibs=200, sequential=True, rarely_accessed=True, boot=True), "gp3",
                         "HDDs cannot be boot volumes")

    def test_choose_volume_rejects_the_impossible(self):
        for kwargs in ({"iops": 300_000}, {"throughput_mibs": 4001}, {"multi_attach": True, "boot": True}, {"iops": -1}, {"throughput_mibs": -5}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    choose_volume(**kwargs)


# ── Exercise 04 ★: Big objects, busy buckets ─────────────────────────
"""
S3 limits (given): MIB = 1024 x 1024 bytes; a single PUT is at most 5 GiB; a multipart upload has parts of
5 MiB to 5 GiB (only the LAST part may be smaller than 5 MiB), at most 10,000 parts, and an object is at most 50 TB
(50 x 10^12 bytes, MAX_OBJECT_BYTES). AWS suggests multipart once an object passes 100 MiB. S3 serves at least
5,500 GET/HEAD and 3,500 PUT/COPY/POST/DELETE requests per second PER PREFIX.
plan_parts(object_bytes, part_mib=None) -> {"part_bytes", "parts", "last_part_bytes", "multipart"}
    Split an upload into parts of part_mib MiB. parts = ceil(object_bytes / part_bytes); the last part holds
    whatever is left (a full part when it divides exactly). "multipart" is True when object_bytes is MORE than
    100 MiB or more than 5 GiB (the single-PUT limit). part_mib None picks the smallest whole-MiB part size that is
    at least 5 MiB and keeps the parts at 10,000 or fewer.
    ValueError for: object_bytes of 0 or less; more than MAX_OBJECT_BYTES; a part_mib below 5 or above 5,120 (5 GiB);
    more than 10,000 parts.
prefixes_needed(gets_per_second, puts_per_second) -> int
    The fewest prefixes that carry the load: max(ceil(gets / 5500), ceil(puts / 3500)), at least 1. Negative rates -> ValueError.
Examples:
    plan_parts(10 * MIB) == {"part_bytes": 5 * MIB, "parts": 2, "last_part_bytes": 5 * MIB, "multipart": False}
    plan_parts(11 * MIB)["parts"] == 3        plan_parts(1024 * MIB * 1024)["part_bytes"] == 105 * MIB      # 1 TiB
    prefixes_needed(11_000, 3_500) == 2
Why? Parts are the unit of retry and of parallelism: lose a part, resend only that part. The 10,000-part cap makes the
part size grow with the object. And a hot bucket is scaled by spreading keys over prefixes, not by buying anything.
Hint: math.ceil; the automatic part size is max(5, ceil(object_bytes / (10_000 x MIB))).
"""
import math  # noqa: E402,F401

MIB = 1024 ** 2
GIB = 1024 ** 3
MAX_OBJECT_BYTES = 50 * 10 ** 12


def plan_parts(object_bytes, part_mib=None):
    raise NotImplementedError  # YOUR CODE


def prefixes_needed(gets_per_second, puts_per_second):
    raise NotImplementedError  # YOUR CODE


class Ex04(Drill):
    """Big objects, busy buckets ★"""
    tasks = ("3.1",)

    def test_small_uploads(self):
        self.assertEqual(plan_parts(10 * MIB), {"part_bytes": 5 * MIB, "parts": 2, "last_part_bytes": 5 * MIB, "multipart": False})
        got = plan_parts(11 * MIB)
        self.assertEqual((got["parts"], got["last_part_bytes"]), (3, 1 * MIB))
        self.assertEqual(plan_parts(1)["parts"], 1)
        self.assertEqual(plan_parts(1)["last_part_bytes"], 1)

    def test_a_chosen_part_size(self):
        got = plan_parts(100 * MIB, 16)
        self.assertEqual((got["part_bytes"], got["parts"], got["last_part_bytes"]), (16 * MIB, 7, 4 * MIB))
        got = plan_parts(96 * MIB, 16)
        self.assertEqual((got["parts"], got["last_part_bytes"]), (6, 16 * MIB), "an exact fit: the last part is a full part")

    def test_when_to_use_multipart(self):
        self.assertFalse(plan_parts(50 * MIB)["multipart"])
        self.assertFalse(plan_parts(100 * MIB)["multipart"], "the course rule is MORE than 100 MiB, so exactly 100 MiB is not")
        self.assertTrue(plan_parts(100 * MIB + 1)["multipart"])
        self.assertTrue(plan_parts(200 * MIB)["multipart"])
        self.assertTrue(plan_parts(5 * GIB + 1)["multipart"], "above 5 GiB a single PUT is impossible")
        self.assertTrue(plan_parts(6 * GIB)["multipart"])

    def test_the_automatic_part_size_grows_with_the_object(self):
        self.assertEqual(plan_parts(1024 * GIB)["part_bytes"], 105 * MIB, "1 TiB / 10,000 parts, rounded up to whole MiB")
        self.assertEqual(plan_parts(100 * GIB)["part_bytes"], 11 * MIB, "100 GiB / 10,000 = 10.24 MiB, rounded up")
        self.assertEqual(plan_parts(10 * GIB)["part_bytes"], 5 * MIB, "never below 5 MiB")
        for size in (10 * GIB, 500 * GIB, 5 * 10 ** 12, MAX_OBJECT_BYTES):
            with self.subTest(size=size):
                got = plan_parts(size)
                self.assertLessEqual(got["parts"], 10_000)
                self.assertLessEqual(got["part_bytes"], 5 * GIB)
                self.assertEqual((got["parts"] - 1) * got["part_bytes"] + got["last_part_bytes"], size, "the parts add up to the object")

    def test_the_part_count_limit_is_10000(self):
        ok = plan_parts(50_000 * MIB, 5)
        self.assertEqual(ok["parts"], 10_000, "exactly 10,000 parts is allowed")
        with self.assertRaises(ValueError):
            plan_parts(50_000 * MIB + 1, 5)
        with self.assertRaises(ValueError):
            plan_parts(60 * GIB, 5)

    def test_the_part_size_limits(self):
        self.assertEqual(plan_parts(10 * GIB, 5)["part_bytes"], 5 * MIB)
        self.assertEqual(plan_parts(10 * GIB, 5120)["part_bytes"], 5 * GIB)
        for part in (4, 0, -5, 5121):
            with self.subTest(part=part):
                with self.assertRaises(ValueError):
                    plan_parts(10 * GIB, part)

    def test_the_object_size_limits(self):
        self.assertEqual(plan_parts(MAX_OBJECT_BYTES)["parts"], 9999)
        for size in (0, -1, MAX_OBJECT_BYTES + 1):
            with self.subTest(size=size):
                with self.assertRaises(ValueError):
                    plan_parts(size)

    def test_prefixes_needed(self):
        for gets, puts, want in ((100, 100, 1), (0, 0, 1), (5500, 3500, 1), (5501, 0, 2), (0, 3501, 2), (11_000, 3_500, 2),
                                 (11_000, 10_500, 3), (55_000, 1000, 10), (1000, 35_000, 10)):
            with self.subTest(gets=gets, puts=puts):
                self.assertEqual(prefixes_needed(gets, puts), want, "reads and writes have separate limits: the larger need decides")

    def test_prefixes_needed_rejects_negative_rates(self):
        for args in ((-1, 0), (0, -1)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    prefixes_needed(*args)


# ── helpers for the boto3 drills ─────────────────────────────────────
import random  # noqa: E402


class _NetworkDrop(Exception):
    """The simulated failure of one upload part."""


class _Spy:
    """Wraps a boto3 client: logs every call as (name, kwargs) in .calls and can fail one upload part.
    The drills pass it to your function in place of the client, so they can see WHAT you called and in what order."""

    def __init__(self, client, fail_part=None):
        self._client, self._fail_part, self.calls = client, fail_part, []

    def __getattr__(self, name):
        attr = getattr(self._client, name)
        if not callable(attr):
            return attr

        def call(*args, **kwargs):
            self.calls.append((name, kwargs))
            if name == "upload_part" and kwargs.get("PartNumber") == self._fail_part:
                raise _NetworkDrop("the network dropped this part")
            return attr(*args, **kwargs)
        return call

    def names(self):
        return [name for name, _ in self.calls]


# ── Exercise 05: A bucket that keeps secrets ─────────────────────────
"""
secure_bucket(s3, name, kms_key_id) -> None
    Create the bucket `name` (us-east-1, so no location constraint) and lock it down, using the boto3 client `s3`:
      versioning                   Enabled (a delete or overwrite can be undone)
      default encryption           SSE-KMS with the key kms_key_id, and Bucket Keys ON (BucketKeyEnabled=True: far
                                   fewer KMS calls, so a lower KMS bill)
      Block Public Access          ALL FOUR settings True: BlockPublicAcls, IgnorePublicAcls, BlockPublicPolicy,
                                   RestrictPublicBuckets. Setting only some leaves the others False.
      Object Ownership             BucketOwnerEnforced (ACLs are switched off; the bucket policy and IAM decide everything)
    An empty kms_key_id -> ValueError (SSE-KMS needs YOUR key: that is what gives you key policies and an audit trail).
tls_only_policy(bucket) -> dict
    RETURN (do not put) a bucket policy, as a Python dict, with Version "2012-10-17" that DENIES every S3 action
    (s3:*) to everyone ("*") when the request did not use HTTPS: Condition Bool aws:SecureTransport "false".
    It must cover BOTH the bucket ARN (arn:aws:s3:::name — ListBucket and friends) and the objects (arn:aws:s3:::name/*).
    It must contain no Allow: a deny-only policy adds a guard rail without opening anything.
    Why it is not put in this drill: moto enforces a bucket-policy Deny crudely. It ignores Condition and Principal, so
    this Deny would block the test's own HTTPS calls too. In real AWS you would put_bucket_policy it. The tests evaluate
    the dict with the policy evaluator from week 01 instead.
Examples:
    tls_only_policy("logs")["Statement"][0]["Effect"] == "Deny"
Why? "Deny unless HTTPS" is the standard guard rail, because a Deny beats every Allow. And the policy must name the
bucket ARN as well as the objects, or a plain-HTTP ListBucket request slips through.
Hint: put_bucket_versioning(Bucket=…, VersioningConfiguration={"Status": "Enabled"}); put_bucket_encryption(Bucket=…,
      ServerSideEncryptionConfiguration={"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "aws:kms",
      "KMSMasterKeyID": …}, "BucketKeyEnabled": True}]}); put_public_access_block(…, PublicAccessBlockConfiguration={…});
      put_bucket_ownership_controls(…, OwnershipControls={"Rules": [{"ObjectOwnership": "BucketOwnerEnforced"}]}).
"""
def secure_bucket(s3, name, kms_key_id):
    raise NotImplementedError  # YOUR CODE


def tls_only_policy(bucket):
    raise NotImplementedError  # YOUR CODE


from _harness.awslib import policy_eval as _pe  # noqa: E402


class Ex05(Drill):
    """A bucket that keeps secrets"""
    tasks = ("1.3",)
    uses_aws = True
    KEY = "arn:aws:kms:us-east-1:111122223333:key/1234abcd-12ab-34cd-56ef-1234567890ab"
    ALICE = "arn:aws:iam::111122223333:user/alice"
    ALLOW_ALL = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "s3:*", "Resource": "*"}]}

    def make(self, name="shortly-secrets"):
        s3 = self.client("s3")
        secure_bucket(s3, name, self.KEY)
        return s3, name

    def verdict(self, policy, action, resource, https):
        request = _pe.Request(self.ALICE, action, resource, {"aws:SecureTransport": https})
        return _pe.evaluate(request, identity=[self.ALLOW_ALL], resource_policy=policy)

    def test_the_bucket_exists_and_is_versioned(self):
        s3, name = self.make()
        self.assertIn(name, [b["Name"] for b in s3.list_buckets()["Buckets"]])
        self.assertEqual(s3.get_bucket_versioning(Bucket=name).get("Status"), "Enabled")

    def test_default_encryption_is_kms_with_a_bucket_key(self):
        s3, name = self.make()
        rule = s3.get_bucket_encryption(Bucket=name)["ServerSideEncryptionConfiguration"]["Rules"][0]
        default = rule["ApplyServerSideEncryptionByDefault"]
        self.assertEqual(default["SSEAlgorithm"], "aws:kms", "SSE-S3 (AES256) is not enough: use your own KMS key")
        self.assertEqual(default["KMSMasterKeyID"], self.KEY)
        self.assertTrue(rule["BucketKeyEnabled"], "turn Bucket Keys on: they cut KMS request costs")

    def test_new_objects_inherit_the_encryption(self):
        s3, name = self.make()
        s3.put_object(Bucket=name, Key="a.txt", Body=b"hello")
        head = s3.head_object(Bucket=name, Key="a.txt")
        self.assertEqual(head["ServerSideEncryption"], "aws:kms")
        self.assertEqual(head["SSEKMSKeyId"], self.KEY)

    def test_all_four_public_access_settings_are_on(self):
        s3, name = self.make()
        config = s3.get_public_access_block(Bucket=name)["PublicAccessBlockConfiguration"]
        self.assertEqual(config, {"BlockPublicAcls": True, "IgnorePublicAcls": True,
                                  "BlockPublicPolicy": True, "RestrictPublicBuckets": True},
                         "Block Public Access has four switches: turn on all four")

    def test_acls_are_off(self):
        s3, name = self.make()
        rules = s3.get_bucket_ownership_controls(Bucket=name)["OwnershipControls"]["Rules"]
        self.assertEqual(rules, [{"ObjectOwnership": "BucketOwnerEnforced"}])

    def test_a_key_is_required(self):
        s3 = self.client("s3")
        for bad in ("", None):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    secure_bucket(s3, "shortly-nokey", bad)

    def test_tls_policy_lets_https_through_and_blocks_http(self):
        policy = tls_only_policy("shortly-secrets")
        self.assertEqual(policy["Version"], "2012-10-17")
        json.dumps(policy)
        bucket, objects = "arn:aws:s3:::shortly-secrets", "arn:aws:s3:::shortly-secrets/report.csv"
        for action, resource in (("s3:GetObject", objects), ("s3:PutObject", objects), ("s3:ListBucket", bucket)):
            with self.subTest(action=action):
                self.assertEqual(self.verdict(policy, action, resource, https=True), "Allow", "HTTPS requests must not be affected")
                self.assertEqual(self.verdict(policy, action, resource, https=False), "ExplicitDeny", "plain HTTP must be denied")

    def test_the_bucket_itself_is_covered_not_only_its_objects(self):
        policy = tls_only_policy("shortly-secrets")
        self.assertEqual(self.verdict(policy, "s3:ListBucket", "arn:aws:s3:::shortly-secrets", https=False), "ExplicitDeny",
                         "listing the bucket over HTTP is on the BUCKET ARN, which has no /*")
        self.assertEqual(self.verdict(policy, "s3:GetBucketPolicy", "arn:aws:s3:::shortly-secrets", https=False), "ExplicitDeny")

    def test_the_policy_is_deny_only_and_belongs_to_this_bucket(self):
        policy = tls_only_policy("shortly-secrets")
        self.assertTrue(policy["Statement"], "at least one statement")
        self.assertTrue(all(s["Effect"] == "Deny" for s in policy["Statement"]), "a guard rail denies; it never allows")
        self.assertEqual(self.verdict(policy, "s3:GetObject", "arn:aws:s3:::another-bucket/x", https=False), "Allow",
                         "the policy must name this bucket only")
        self.assertEqual(self.verdict(policy, "s3:GetObject", "arn:aws:s3:::shortly-secrets/x", https=False), "ExplicitDeny")


# ── Exercise 06: Upload big, share briefly ───────────────────────────
"""
upload_in_parts(s3, bucket, key, data, part_mib) -> None
    Upload the bytes `data` to s3://bucket/key as a MULTIPART upload with parts of part_mib MiB (the last part may be
    smaller): create_multipart_upload, then upload_part for part numbers 1, 2, 3 ... (they start at 1), then
    complete_multipart_upload with the list of {"PartNumber", "ETag"} you collected. Use drill 04's plan_parts if you
    like, or just slice the data.
    If any part fails, ABORT the upload (abort_multipart_upload) and re-raise the error: an upload left unfinished keeps
    billing you for the stored parts and never shows up in a normal listing.
    ValueError (before anything is created) for a part_mib outside 5 to 5,120, or empty data.
share_link(s3, bucket, key, seconds) -> str
    A presigned GET URL for the object that stops working after `seconds` seconds: s3.generate_presigned_url("get_object",
    Params={"Bucket": …, "Key": …}, ExpiresIn=seconds). A presigned URL carries YOUR permissions to whoever holds it, so keep it
    short. ValueError if seconds is less than 1 or more than 604,800 (7 days, the longest SigV4 allows).
    (Signed with temporary credentials such as an IAM role, the URL also dies when those credentials expire.)
    NEVER open the URL in a test: urllib would go to the real internet. The tests read the URL's parts.
Examples:
    upload_in_parts(s3, "b", "big.bin", data_of_12_MiB, 5)   # 3 parts: 5 MiB, 5 MiB, 2 MiB
    share_link(s3, "b", "report.pdf", 3600)   # …/report.pdf?X-Amz-Expires=3600&X-Amz-Signature=…
Why? Multipart makes a big upload retryable and parallel; the abort keeps failures from leaving billable debris. And a
link is a key to the door: the shorter it lives, the less it matters if it leaks.
"""
def upload_in_parts(s3, bucket, key, data, part_mib):
    raise NotImplementedError  # YOUR CODE


def share_link(s3, bucket, key, seconds):
    raise NotImplementedError  # YOUR CODE


class Ex06(Drill):
    """Upload big, share briefly"""
    tasks = ("3.1", "1.3")
    uses_aws = True

    def data(self, size):
        return random.Random(4).randbytes(size)

    def bucket(self):
        s3 = self.client("s3")
        s3.create_bucket(Bucket="shortly-uploads")
        return s3

    def test_the_object_reads_back_intact(self):
        s3 = self.bucket()
        data = self.data(12 * MIB + 123)
        upload_in_parts(s3, "shortly-uploads", "big.bin", data, 5)
        body = s3.get_object(Bucket="shortly-uploads", Key="big.bin")["Body"].read()
        self.assertEqual(len(body), len(data))
        self.assertTrue(body == data, "the parts must go back together in order")

    def test_it_really_used_a_multipart_upload(self):
        s3 = self.bucket()
        spy = _Spy(s3)
        upload_in_parts(spy, "shortly-uploads", "big.bin", self.data(12 * MIB + 123), 5)
        etag = s3.head_object(Bucket="shortly-uploads", Key="big.bin")["ETag"].strip('"')
        self.assertTrue(etag.endswith("-3"), f"a 3-part multipart object has an ETag ending -3, got {etag}")
        parts = [kwargs["PartNumber"] for name, kwargs in spy.calls if name == "upload_part"]
        self.assertEqual(parts, [1, 2, 3], "part numbers start at 1 and go up by one")
        self.assertEqual(spy.names().count("complete_multipart_upload"), 1)

    def test_part_size_decides_the_number_of_parts(self):
        s3 = self.bucket()
        spy = _Spy(s3)
        upload_in_parts(spy, "shortly-uploads", "a.bin", self.data(17 * MIB), 8)
        self.assertEqual(spy.names().count("upload_part"), 3, "17 MiB in 8 MiB parts is 8 + 8 + 1")
        small = _Spy(s3)
        upload_in_parts(small, "shortly-uploads", "b.bin", self.data(1 * MIB), 5)
        self.assertEqual(small.names().count("upload_part"), 1, "an object smaller than one part is a single (last) part")
        self.assertEqual(len(s3.get_object(Bucket="shortly-uploads", Key="b.bin")["Body"].read()), 1 * MIB)

    def test_a_failed_part_aborts_the_upload(self):
        s3 = self.bucket()
        spy = _Spy(s3, fail_part=2)
        with self.assertRaises(_NetworkDrop):
            upload_in_parts(spy, "shortly-uploads", "big.bin", self.data(12 * MIB), 5)
        self.assertEqual(s3.list_multipart_uploads(Bucket="shortly-uploads").get("Uploads", []), [],
                         "abort_multipart_upload, or the stored parts keep costing money")
        with self.assertClientError("NoSuchKey"):
            s3.get_object(Bucket="shortly-uploads", Key="big.bin")

    def test_bad_part_sizes_and_empty_data_create_nothing(self):
        s3 = self.bucket()
        spy = _Spy(s3)
        for part_mib, data in ((4, b"x" * 10), (5121, b"x" * 10), (0, b"x" * 10), (5, b"")):
            with self.subTest(part_mib=part_mib, size=len(data)):
                with self.assertRaises(ValueError):
                    upload_in_parts(spy, "shortly-uploads", "bad.bin", data, part_mib)
        self.assertEqual(spy.calls, [], "validate first: no call to S3 for a request that cannot work")

    def test_the_link_names_the_object_and_expires(self):
        from botocore.config import Config
        s3 = self.client("s3", config=Config(signature_version="s3v4"))
        s3.create_bucket(Bucket="shortly-uploads")
        url = share_link(s3, "shortly-uploads", "reports/q1.pdf", 3600)
        self.assertIsInstance(url, str)
        self.assertIn("shortly-uploads", url)
        self.assertIn("reports/q1.pdf", url)
        self.assertIn("X-Amz-Expires=3600", url, "ExpiresIn is what makes the link short-lived")
        self.assertIn("X-Amz-Signature=", url)
        self.assertIn("X-Amz-Expires=60&", share_link(s3, "shortly-uploads", "reports/q1.pdf", 60) + "&")

    def test_the_longest_link_is_seven_days(self):
        from botocore.config import Config
        s3 = self.client("s3", config=Config(signature_version="s3v4"))
        self.assertIn("X-Amz-Expires=604800", share_link(s3, "b", "k", 604_800))
        for seconds in (604_801, 0, -5):
            with self.subTest(seconds=seconds):
                with self.assertRaises(ValueError):
                    share_link(s3, "b", "k", seconds)
        self.assertIn("X-Amz-Expires=1", share_link(s3, "b", "k", 1))


# ── Exercise 07 (predict): What survives a delete? ───────────────────
"""
A VERSIONED bucket never loses data on a plain delete: it adds a DELETE MARKER on top. For each scenario, work out the
answer BEFORE running anything and write it in PREDICTIONS. The test runs the scenario against moto (a fake S3 that
follows these rules) and shows the truth when you are wrong.
Answers: an AWS error code like "AccessDenied" (what boto3 puts in e.response["Error"]["Code"]), the object's body text,
a number, or "M markers, V versions" (always plural, for example "2 markers, 5 versions").
"""
SCENARIOS7 = {
    1: "A versioned bucket holds report.txt with body 'first'. You call delete_object(Bucket, Key) with no VersionId, then get_object(Bucket, Key). "
       "Which error code comes back?",
    2: "The same, but now you call get_object with the VersionId the object had BEFORE the delete. What is the body?",
    3: "The same plain delete. How many keys does list_objects_v2 return for the bucket? (a number)",
    4: "The same plain delete. What does list_object_versions show? Answer like '2 markers, 5 versions'.",
    5: "report.txt has two versions, 'first' then 'second'. You delete it with no VersionId, then delete the DELETE MARKER by its own VersionId, "
       "then get_object. What is the body?",
    6: "report.txt has ONE version, 'first'. You call delete_object with that version's VersionId, then get_object. Which error code comes back?",
    7: "report.txt is written twice: 'first', then 'second'. What does list_object_versions show? Answer like '2 markers, 5 versions'.",
    8: "report.txt has two versions, 'first' then 'second'. You delete the LATEST version by its VersionId, then get_object with no VersionId. "
       "What is the body?",
}
PREDICTIONS = {n: None for n in SCENARIOS7}   # YOUR ANSWERS: an error code, a body, a number or "M markers, V versions"


def _versioned_bucket(s3, name, bodies):
    """A fresh versioned bucket whose key report.txt was written once per body; returns the version ids in order."""
    s3.create_bucket(Bucket=name)
    s3.put_bucket_versioning(Bucket=name, VersioningConfiguration={"Status": "Enabled"})
    return [s3.put_object(Bucket=name, Key="report.txt", Body=body)["VersionId"] for body in bodies]


def _error_code(call):
    from botocore.exceptions import ClientError
    try:
        call()
    except ClientError as exc:
        return exc.response["Error"]["Code"]
    return "no error"


def _text(s3, name, **kwargs):
    return s3.get_object(Bucket=name, Key="report.txt", **kwargs)["Body"].read().decode()


def _counts(s3, name):
    listed = s3.list_object_versions(Bucket=name)
    return f"{len(listed.get('DeleteMarkers', []))} markers, {len(listed.get('Versions', []))} versions"


def _run7(n, s3):
    name = f"shortly-ex07-s{n}"
    if n in (1, 2, 3, 4):
        (first,) = _versioned_bucket(s3, name, [b"first"])
        s3.delete_object(Bucket=name, Key="report.txt")
        return {1: lambda: _error_code(lambda: _text(s3, name)), 2: lambda: _text(s3, name, VersionId=first),
                3: lambda: s3.list_objects_v2(Bucket=name)["KeyCount"], 4: lambda: _counts(s3, name)}[n]()
    if n == 5:
        _versioned_bucket(s3, name, [b"first", b"second"])
        marker = s3.delete_object(Bucket=name, Key="report.txt")["VersionId"]
        s3.delete_object(Bucket=name, Key="report.txt", VersionId=marker)
        return _text(s3, name)
    if n == 6:
        (first,) = _versioned_bucket(s3, name, [b"first"])
        s3.delete_object(Bucket=name, Key="report.txt", VersionId=first)
        return _error_code(lambda: _text(s3, name))
    if n == 7:
        _versioned_bucket(s3, name, [b"first", b"second"])
        return _counts(s3, name)
    _, second = _versioned_bucket(s3, name, [b"first", b"second"])
    s3.delete_object(Bucket=name, Key="report.txt", VersionId=second)
    return _text(s3, name)


class Ex07(Drill):
    """What survives a delete? (predict)"""
    tasks = ("1.3", "2.2")
    uses_aws = True

    def test_predictions(self):
        s3 = self.client("s3")
        for n, story in SCENARIOS7.items():
            with self.subTest(scenario=n):
                truth = _run7(n, s3)
                self.assertIsNotNone(PREDICTIONS.get(n), f"scenario {n}: write your answer")
                self.assertEqual(normalise(PREDICTIONS[n]), normalise(truth), f"scenario {n}: {story} — the answer is {truth!r}")


# ── Exercise 08 (fix the bug): Too public ────────────────────────────
"""
ASSETS_POLICY is the bucket policy of "shortly-assets", the bucket behind a CloudFront distribution. It is too open: it
lets ANYONE on the internet read every object, and ANYONE write to it. Edit ASSETS_POLICY (a Python dict) so that:
  * s3:GetObject on the objects (arn:aws:s3:::shortly-assets/*) is allowed ONLY to the CloudFront service
    (Principal {"Service": "cloudfront.amazonaws.com"}) and ONLY when the request comes from OUR distribution:
    Condition StringEquals "AWS:SourceArn" = DISTRIBUTION_ARN. This is Origin Access Control (OAC). Without the
    condition ANY CloudFront distribution in the world could serve your files, a "confused deputy".
  * s3:PutObject is allowed ONLY to the application role (Principal {"AWS": APP_ROLE_ARN}) and ONLY under the
    uploads/ prefix (arn:aws:s3:::shortly-assets/uploads/*).
Nobody else gets anything from this policy.
Why? A bucket policy is an open door unless every Allow names WHO and, where it matters, WHERE the request comes from.
Principal "*" means everyone, including people with no AWS account. The tests evaluate your policy with the policy
evaluator from week 01 (moto cannot: it ignores principals and conditions).
Hint: the CloudFront caller is the service itself, so Principal is {"Service": "cloudfront.amazonaws.com"}, not an AWS ARN.
"""
BUCKET_ARN = "arn:aws:s3:::shortly-assets"
DISTRIBUTION_ARN = "arn:aws:cloudfront::111122223333:distribution/E2EXAMPLE1234"
APP_ROLE_ARN = "arn:aws:iam::111122223333:role/shortly-app"
ASSETS_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {"Sid": "ReadAssets", "Effect": "Allow", "Principal": "*", "Action": "s3:GetObject", "Resource": f"{BUCKET_ARN}/*"},
        {"Sid": "WriteAssets", "Effect": "Allow", "Principal": "*", "Action": "s3:PutObject", "Resource": f"{BUCKET_ARN}/*"},
    ],
}


class Ex08(Drill):
    """Too public (fix the bug)"""
    tasks = ("1.3",)
    CLOUDFRONT = "cloudfront.amazonaws.com"
    OTHER_DISTRIBUTION = "arn:aws:cloudfront::999999999999:distribution/EEVIL000000"
    APP_SESSION = "arn:aws:sts::111122223333:assumed-role/shortly-app/i-0abc123"
    OTHER_SESSION = "arn:aws:sts::111122223333:assumed-role/other-team/i-0def456"
    ALICE = "arn:aws:iam::111122223333:user/alice"
    ASSET = f"{BUCKET_ARN}/images/logo.png"

    def verdict(self, principal, action, resource, **context):
        return _pe.evaluate(_pe.Request(principal, action, resource, context), resource_policy=ASSETS_POLICY)

    def test_only_our_distribution_can_read(self):
        json.dumps(ASSETS_POLICY)
        self.assertEqual(ASSETS_POLICY["Version"], "2012-10-17")
        self.assertEqual(self.verdict(self.CLOUDFRONT, "s3:GetObject", self.ASSET, **{"aws:SourceArn": DISTRIBUTION_ARN}), "Allow",
                         "our distribution must still be able to read")
        self.assertNotEqual(self.verdict("anonymous", "s3:GetObject", self.ASSET), "Allow", "an anonymous visitor must not read the bucket directly")
        self.assertNotEqual(self.verdict(self.ALICE, "s3:GetObject", self.ASSET), "Allow", "no other principal is granted read")

    def test_another_distribution_is_refused(self):
        self.assertNotEqual(self.verdict(self.CLOUDFRONT, "s3:GetObject", self.ASSET, **{"aws:SourceArn": self.OTHER_DISTRIBUTION}), "Allow",
                            "the SourceArn condition is what stops other people's distributions")
        self.assertNotEqual(self.verdict(self.CLOUDFRONT, "s3:GetObject", self.ASSET), "Allow", "CloudFront with no source ARN at all")
        self.assertEqual(self.verdict(self.CLOUDFRONT, "s3:GetObject", self.ASSET, **{"aws:SourceArn": DISTRIBUTION_ARN}), "Allow")

    def test_cloudfront_reads_but_never_writes(self):
        ours = {"aws:SourceArn": DISTRIBUTION_ARN}
        self.assertEqual(self.verdict(self.CLOUDFRONT, "s3:GetObject", f"{BUCKET_ARN}/uploads/a.png", **ours), "Allow")
        self.assertNotEqual(self.verdict(self.CLOUDFRONT, "s3:PutObject", f"{BUCKET_ARN}/uploads/a.png", **ours), "Allow")
        self.assertNotEqual(self.verdict(self.CLOUDFRONT, "s3:DeleteObject", self.ASSET, **ours), "Allow")

    def test_the_app_role_writes_only_under_uploads(self):
        self.assertEqual(self.verdict(self.APP_SESSION, "s3:PutObject", f"{BUCKET_ARN}/uploads/a.png"), "Allow", "the app must still be able to upload")
        self.assertEqual(self.verdict(self.APP_SESSION, "s3:PutObject", f"{BUCKET_ARN}/uploads/2026/b.png"), "Allow")
        self.assertNotEqual(self.verdict(self.APP_SESSION, "s3:PutObject", self.ASSET), "Allow", "outside uploads/ the app role may not write")
        self.assertNotEqual(self.verdict(self.APP_SESSION, "s3:PutObject", f"{BUCKET_ARN}/index.html"), "Allow")

    def test_nobody_else_can_write(self):
        target = f"{BUCKET_ARN}/uploads/a.png"
        self.assertEqual(self.verdict(self.APP_SESSION, "s3:PutObject", target), "Allow")
        for who in ("anonymous", self.ALICE, self.OTHER_SESSION):
            with self.subTest(who=who):
                self.assertNotEqual(self.verdict(who, "s3:PutObject", target), "Allow", f"{who} must not be able to upload")


# ── Exercise 09 (fix the bug): Replication that never starts ─────────
"""
make_replicated_pair(s3, source, destination, role_arn) -> None
    Create two buckets and replicate every new object from `source` to `destination`. As written it fails the moment it
    calls put_bucket_replication. Fix it so that:
      * both buckets exist, and versioning is Enabled on BOTH — and turned on BEFORE the replication rule is put.
        Replication copies object VERSIONS, so S3 refuses a rule when the source is not versioned, and a destination that
        is not versioned cannot receive them.
      * ONE rule, Status "Enabled", for all objects (Filter {"Prefix": ""}), with Priority 1.
      * the rule's Destination Bucket is the destination bucket's ARN (arn:aws:s3:::name), NOT its name.
      * the replication Role is role_arn (S3 assumes this role to copy; its trust policy names s3.amazonaws.com).
      * DeleteMarkerReplication Status "Enabled": a delete in the source is copied as a delete marker. Say "Disabled" and the
        two buckets drift apart after the first delete.
    source and destination must differ (ValueError).
Note: moto stores the rule but never copies a byte, and always reads DeleteMarkerReplication back as "Disabled". So the
tests check the settings you send, not a copy.
Why? Replication is a copy of every new version, so it needs a versioned source and destination. Existing objects are not
copied by a new rule (that needs S3 Batch Replication). Cross-region copies cost transfer, and the same-region kind
(SRR) is for log aggregation or a separate-owner copy.
"""
def make_replicated_pair(s3, source, destination, role_arn):
    s3.create_bucket(Bucket=source)
    s3.create_bucket(Bucket=destination)
    s3.put_bucket_replication(Bucket=source, ReplicationConfiguration={
        "Role": role_arn,
        "Rules": [{"ID": "all", "Status": "Enabled", "Prefix": "", "Destination": {"Bucket": destination}}],
    })


class Ex09(Drill):
    """Replication that never starts (fix the bug)"""
    tasks = ("2.2", "1.3")
    uses_aws = True
    ROLE = "arn:aws:iam::111122223333:role/shortly-replication"

    def make(self):
        s3 = self.client("s3")
        spy = _Spy(s3)
        make_replicated_pair(spy, "shortly-src", "shortly-dst", self.ROLE)
        return s3, spy

    def rule(self, s3):
        return s3.get_bucket_replication(Bucket="shortly-src")["ReplicationConfiguration"]["Rules"][0]

    def test_both_buckets_are_versioned(self):
        s3, _ = self.make()
        for name in ("shortly-src", "shortly-dst"):
            with self.subTest(bucket=name):
                self.assertEqual(s3.get_bucket_versioning(Bucket=name).get("Status"), "Enabled",
                                 f"{name}: replication copies versions, so both ends need versioning")

    def test_versioning_comes_before_the_rule(self):
        _, spy = self.make()
        names = spy.names()
        self.assertIn("put_bucket_replication", names)
        rule_at = names.index("put_bucket_replication")
        for bucket in ("shortly-src", "shortly-dst"):
            with self.subTest(bucket=bucket):
                turned_on = [i for i, (name, kwargs) in enumerate(spy.calls) if name == "put_bucket_versioning" and kwargs["Bucket"] == bucket]
                self.assertTrue(turned_on and turned_on[0] < rule_at, f"turn versioning on for {bucket} before you put the replication rule")

    def test_the_rule_points_at_the_destination_arn(self):
        s3, _ = self.make()
        rule = self.rule(s3)
        self.assertEqual(rule["Status"], "Enabled")
        self.assertEqual(rule["Destination"]["Bucket"], "arn:aws:s3:::shortly-dst", "the destination is an ARN, not a bucket name")
        self.assertEqual(len(s3.get_bucket_replication(Bucket="shortly-src")["ReplicationConfiguration"]["Rules"]), 1)

    def test_the_role_and_scope(self):
        s3, _ = self.make()
        config = s3.get_bucket_replication(Bucket="shortly-src")["ReplicationConfiguration"]
        self.assertEqual(config["Role"], self.ROLE)
        rule = config["Rules"][0]
        self.assertEqual(rule.get("Filter", {}).get("Prefix", ""), "", "replicate everything: an empty prefix")
        self.assertEqual(rule.get("Priority"), 1)

    def test_deletes_are_replicated_as_delete_markers(self):
        _, spy = self.make()
        sent = [kwargs for name, kwargs in spy.calls if name == "put_bucket_replication"][0]["ReplicationConfiguration"]["Rules"][0]
        self.assertEqual(sent.get("DeleteMarkerReplication"), {"Status": "Enabled"},
                         "DeleteMarkerReplication is part of the rule you send (moto will not show it when read back)")

    def test_both_buckets_exist_and_must_differ(self):
        s3, _ = self.make()
        s3.head_bucket(Bucket="shortly-src")
        s3.head_bucket(Bucket="shortly-dst")
        with self.assertRaises(ValueError):
            make_replicated_pair(s3, "shortly-same", "shortly-same", self.ROLE)


# ── Exercise 10 (decide): Which storage service? ─────────────────────
"""
Choose the best storage service for each scenario. Replace every None in CHOICES with one of these words:
  "s3"                object storage at any scale over HTTP: websites, backups, data lakes
  "ebs"               a block volume for ONE EC2 instance (in one AZ): boot disks, databases
  "instance store"    disks physically on the host: very fast, but gone when the instance stops or fails
  "efs"               shared NFS file system for Linux, across AZs, grows by itself
  "fsx for windows"   managed Windows file server: SMB, Active Directory, NTFS
  "fsx for lustre"    high-performance file system for HPC and ML, can read an S3 bucket
  "fsx for ontap"     NetApp ONTAP: NFS, SMB and iSCSI on the same data, snapshots, SnapMirror
  "storage gateway"   an on-premises appliance that caches locally and stores in AWS
(The answers are stored as hashes, so reading the test will not give them away.)
"""
SCENARIOS10 = {
    1: "A shared POSIX file system that 20 Linux web servers in 3 Availability Zones mount at the same time.",
    2: "Scratch space for a temporary cache that may vanish when the instance stops.",
    3: "Windows home directories for a company using Active Directory, reached over SMB.",
    4: "An HPC job that reads a 50 TB dataset stored in S3 at hundreds of GB/s.",
    5: "The boot volume of one EC2 instance.",
    6: "An on-premises file server that must keep local caching but store its data in S3.",
    7: "Static website images and backups, at any scale, with no capacity planning.",
    8: "NFS and SMB clients using the same data, with NetApp snapshots and SnapMirror replication.",
}
OPTIONS10 = ("s3", "ebs", "instance store", "efs", "fsx for windows", "fsx for lustre", "fsx for ontap", "storage gateway")
CHOICES = {n: None for n in SCENARIOS10}   # YOUR ANSWERS: one of the words in the docstring
CHOICE_DIGESTS = {
    1: "186c54acc6d75432c2b61825c4fc8ebb4df485e158395661da3b41ab5b8151d3",
    2: "f2984e1c134a0ec3c0331678376188006f45239c7834c7a6aeaf83796f19e8a2",
    3: "c235d5c3b017c6b21430e476fc522b65a3b152e7b410b25f7c20aa38a7c20efe",
    4: "41844a05eb6cae94cee1416c1bdc0e386eac64bc79d6fa7245198dae11c840ae",
    5: "e6d30d3dec3b88800ed52b0ed20dd3cb6381974d8d672ecbdd64abedd90f601b",
    6: "c3a5443e81dc92b7daf1dea2ac4ec2fc33e82133b62e6f7b5620ac4be6e3ec84",
    7: "3f83e0575a4ae45f4aa452cb719fffffd0a586a9619d0e84059582a1db79ce4d",
    8: "8dd82848a36c9dd09ef4ec452bb19ece39f78b8a9bfe3212a52ae3dcfdb39d29",
}


class Ex10(Drill):
    """Which storage service? (decide)"""
    tasks = ("3.1", "4.1")

    def test_choices(self):
        for n, story in SCENARIOS10.items():
            with self.subTest(scenario=n):
                value = CHOICES.get(n)
                self.assertIn(value, OPTIONS10, f"scenario {n}: answer one of {OPTIONS10}, not {value!r}")
                self.assertHashed(value, f"w04-ex10-{n}", CHOICE_DIGESTS[n],
                                  f"scenario {n} ({story}): {value!r} is not right — who mounts it, which protocol, how long must it last?")


if __name__ == "__main__":
    run()
````

### `week_04_storage/practice/solutions.py`

````python
"""Reference solutions for week 04.

Drills 01–04: the course's reference models ARE the solution — read _harness/awslib/s3cost.py, lifecycle.py and ebs.py
and compare them with yours.
"""
from _harness.awslib.ebs import choose_volume, gp2_iops, gp3_config, monthly_cost  # noqa: F401
from _harness.awslib.lifecycle import current_class, noncurrent_fate, validate  # noqa: F401
from _harness.awslib.s3cost import cheapest_class, plan_parts, prefixes_needed, storage_cost  # noqa: F401


def secure_bucket(s3, name, kms_key_id):
    if not kms_key_id:
        raise ValueError("SSE-KMS needs a KMS key")
    s3.create_bucket(Bucket=name)
    s3.put_bucket_versioning(Bucket=name, VersioningConfiguration={"Status": "Enabled"})
    s3.put_bucket_encryption(Bucket=name, ServerSideEncryptionConfiguration={"Rules": [{
        "ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "aws:kms", "KMSMasterKeyID": kms_key_id},
        "BucketKeyEnabled": True}]})
    s3.put_public_access_block(Bucket=name, PublicAccessBlockConfiguration={
        "BlockPublicAcls": True, "IgnorePublicAcls": True, "BlockPublicPolicy": True, "RestrictPublicBuckets": True})
    s3.put_bucket_ownership_controls(Bucket=name, OwnershipControls={"Rules": [{"ObjectOwnership": "BucketOwnerEnforced"}]})


def tls_only_policy(bucket):
    return {"Version": "2012-10-17", "Statement": [{
        "Sid": "DenyInsecureTransport", "Effect": "Deny", "Principal": "*", "Action": "s3:*",
        "Resource": [f"arn:aws:s3:::{bucket}", f"arn:aws:s3:::{bucket}/*"],
        "Condition": {"Bool": {"aws:SecureTransport": "false"}}}]}


def upload_in_parts(s3, bucket, key, data, part_mib):
    if not data or not 5 <= part_mib <= 5120:
        raise ValueError("need data and a part size of 5 MiB to 5 GiB")
    size = part_mib * MIB
    upload = s3.create_multipart_upload(Bucket=bucket, Key=key)["UploadId"]
    try:
        parts = []
        for number, start in enumerate(range(0, len(data), size), start=1):
            etag = s3.upload_part(Bucket=bucket, Key=key, UploadId=upload, PartNumber=number, Body=data[start:start + size])["ETag"]
            parts.append({"PartNumber": number, "ETag": etag})
        s3.complete_multipart_upload(Bucket=bucket, Key=key, UploadId=upload, MultipartUpload={"Parts": parts})
    except Exception:
        s3.abort_multipart_upload(Bucket=bucket, Key=key, UploadId=upload)
        raise


def share_link(s3, bucket, key, seconds):
    if not 1 <= seconds <= 604_800:
        raise ValueError("a presigned URL lives 1 second to 7 days")
    return s3.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=seconds)


PREDICTIONS = {1: "NoSuchKey", 2: "first", 3: 0, 4: "1 markers, 1 versions", 5: "second", 6: "NoSuchKey",
               7: "0 markers, 2 versions", 8: "first"}

ASSETS_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {"Sid": "ReadViaOurDistribution", "Effect": "Allow", "Principal": {"Service": "cloudfront.amazonaws.com"},
         "Action": "s3:GetObject", "Resource": f"{BUCKET_ARN}/*",
         "Condition": {"StringEquals": {"AWS:SourceArn": DISTRIBUTION_ARN}}},
        {"Sid": "AppUploads", "Effect": "Allow", "Principal": {"AWS": APP_ROLE_ARN},
         "Action": "s3:PutObject", "Resource": f"{BUCKET_ARN}/uploads/*"},
    ],
}


def make_replicated_pair(s3, source, destination, role_arn):
    if source == destination:
        raise ValueError("source and destination must differ")
    for name in (source, destination):
        s3.create_bucket(Bucket=name)
        s3.put_bucket_versioning(Bucket=name, VersioningConfiguration={"Status": "Enabled"})
    s3.put_bucket_replication(Bucket=source, ReplicationConfiguration={
        "Role": role_arn,
        "Rules": [{"ID": "all", "Status": "Enabled", "Priority": 1, "Filter": {"Prefix": ""},
                   "DeleteMarkerReplication": {"Status": "Enabled"},
                   "Destination": {"Bucket": f"arn:aws:s3:::{destination}"}}],
    })


CHOICES = {1: "efs", 2: "instance store", 3: "fsx for windows", 4: "fsx for lustre", 5: "ebs", 6: "storage gateway",
           7: "s3", 8: "fsx for ontap"}
````

### `week_05_databases_and_caching/practice/exercises.py`

````python
"""
Week 05 drills — databases and caching
======================================
Run:    python practice/exercises.py          every drill
        python practice/exercises.py 4        drill 4 only
Drills 01–02 are pure Python models of DynamoDB capacity: how many read and write units one request
costs, and when provisioned capacity beats paying per request. Drill 03 designs one DynamoDB table
that answers three questions, drill 04 makes concurrent updates safe, drill 05 protects a table.
Drill 06 simulates a cache, drill 07 does connection maths for RDS Proxy. Drill 08 builds a
fault-tolerant RDS database with boto3. Drills 09–10 are decide drills. Everything runs against moto
(a fake AWS) or plain Python, so nothing here can touch a real account or cost money.
The course's own versions of drills 01, 02, 06 and 07 (_harness/awslib/dynamo.py, caching.py and
dbmath.py) are their answer key — don't open them until you are done.
Note: moto stores what you send and enforces DynamoDB conditions and transactions, but it never
expires items by TTL, never throttles, reports made-up consumed capacity, and has no Multi-AZ
standby. So the drills read your settings back and the models show the behaviour.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from boto3.dynamodb.conditions import Key  # noqa: E402,F401  (for drill 03)
from botocore.exceptions import ClientError  # noqa: E402,F401  (for drills 04 and 05)
from _harness.awsdrill import Drill, run  # noqa: E402
from _harness.awslib import prices  # noqa: E402

PRICES = prices.section("database")


# ── Exercise 01 ★: Read units and write units ────────────────────────
"""
DynamoDB meters every request in units, and the unit size is fixed:
    one read unit  = one read of an item up to 4 KB, strongly consistent
    one write unit = one write of an item up to 1 KB
The item size is ROUNDED UP to the next whole block (4 KB for reads, 1 KB for writes) before you
multiply. A 4.1 KB item reads as 8 KB; a 0.5 KB item still writes as 1 KB.
Multipliers:
    reads   strongly consistent 1 · eventually consistent 0.5 (the default, half price) · transactional 2
    writes  standard 1 · transactional 2
The biggest item DynamoDB accepts is 400 KB. Item size 0 or less, or above 400 KB, is a ValueError.
read_units(item_kb, consistency="eventual") -> float
    consistency is "eventual", "strong" or "transactional"; anything else is a ValueError.
write_units(item_kb, transactional=False) -> int
provisioned_capacity(reads_per_second, writes_per_second, item_kb, consistency="eventual",
                     transactional_writes=False) -> (rcu, wcu)
    The capacity to provision: reads per second x read units, writes per second x write units, each
    rounded UP to a whole number (you cannot provision 1.5 units). Negative rates are a ValueError.
Examples:
    read_units(4.1, "strong") == 2.0        read_units(8) == 1.0         write_units(1.5) == 2
    write_units(1.5, transactional=True) == 4       provisioned_capacity(100, 50, 6) == (100, 300)
Why? Rounding is where bills surprise people. Cutting a 1.1 KB item to 1.0 KB halves the write cost,
and reading eventually consistent halves the read cost. The exam asks you to do exactly this sum.
Hint: math.ceil(item_kb / 4) is the number of 4 KB blocks.
"""
def read_units(item_kb, consistency="eventual"):
    raise NotImplementedError  # YOUR CODE


def write_units(item_kb, transactional=False):
    raise NotImplementedError  # YOUR CODE


def provisioned_capacity(reads_per_second, writes_per_second, item_kb, consistency="eventual",
                         transactional_writes=False):
    raise NotImplementedError  # YOUR CODE


class Ex01(Drill):
    """Read units and write units ★"""
    tasks = ("3.3",)

    def test_reads_round_up_to_4_kb(self):
        cases = {1: 1.0, 3: 1.0, 4: 1.0, 4.1: 2.0, 8: 2.0, 8.5: 3.0, 400: 100.0}
        for kb, want in cases.items():
            with self.subTest(item_kb=kb):
                self.assertEqual(read_units(kb, "strong"), want, f"{kb} KB strongly consistent: round {kb}/4 UP")

    def test_consistency_factors(self):
        self.assertEqual(read_units(4, "strong"), 1.0)
        self.assertEqual(read_units(4, "eventual"), 0.5, "eventually consistent reads cost half")
        self.assertEqual(read_units(4, "transactional"), 2.0, "transactional reads cost double")
        self.assertEqual(read_units(8), 1.0, "the default is eventually consistent")
        self.assertEqual(read_units(0.1), 0.5, "even a tiny item is one 4 KB block")

    def test_writes_round_up_to_1_kb(self):
        cases = {0.1: 1, 0.5: 1, 1: 1, 1.01: 2, 1.5: 2, 3: 3, 400: 400}
        for kb, want in cases.items():
            with self.subTest(item_kb=kb):
                self.assertEqual(write_units(kb), want, f"{kb} KB write: round {kb}/1 UP")

    def test_transactional_writes_cost_double(self):
        self.assertEqual(write_units(1, transactional=True), 2)
        self.assertEqual(write_units(1.5, transactional=True), 4)
        self.assertEqual(write_units(3, transactional=True), 6)

    def test_item_size_limits(self):
        for bad in (0, -1, 400.1, 500):
            with self.subTest(item_kb=bad):
                with self.assertRaises(ValueError):
                    read_units(bad)
                with self.assertRaises(ValueError):
                    write_units(bad)
        read_units(400)
        write_units(400)

    def test_unknown_consistency(self):
        with self.assertRaises(ValueError):
            read_units(4, "sometimes")

    def test_a_worked_workload(self):
        # 100 reads/s and 50 writes/s of 6 KB items: 6 KB is 2 blocks of 4 KB (eventual: 1 unit) and 6 write units.
        self.assertEqual(provisioned_capacity(100, 50, 6), (100, 300))
        # Strongly consistent reads of the same items cost double: 2 units each. Transactional writes: 12 units.
        self.assertEqual(provisioned_capacity(80, 10, 6, "strong"), (160, 60))
        self.assertEqual(provisioned_capacity(80, 10, 6, "strong", transactional_writes=True), (160, 120))

    def test_capacity_rounds_up_to_whole_units(self):
        # 3 eventual reads/s of 1 KB = 1.5 units: you must provision 2.
        self.assertEqual(provisioned_capacity(3, 0, 1), (2, 0))
        self.assertEqual(provisioned_capacity(0, 0, 1), (0, 0))

    def test_negative_rates(self):
        with self.assertRaises(ValueError):
            provisioned_capacity(-1, 5, 1)
        with self.assertRaises(ValueError):
            provisioned_capacity(1, -5, 1)


# ── Exercise 02 ★: On-demand or provisioned? ─────────────────────────
"""
DynamoDB has two ways to pay:
    on-demand    you pay per request: price per million x units used. Nothing when idle.
    provisioned  you choose read and write units per second and pay for EVERY hour of them, whether
                 you use them or not.
PRICES (from prices.toml, illustrative) holds the four numbers you need:
    dynamodb_on_demand_per_million_writes, dynamodb_on_demand_per_million_reads (per million units),
    dynamodb_wcu_hour, dynamodb_rcu_hour (per provisioned unit per hour).
Write three functions. Reuse your read_units / write_units from drill 1.
monthly_cost_on_demand(reads_per_month, writes_per_month, item_kb, consistency="eventual",
                       transactional_writes=False, price=PRICES) -> float
    (reads x read_units / 1,000,000 x read price) + (writes x write_units / 1,000,000 x write price),
    rounded to 4 decimal places. Storage is not included. Negative counts are a ValueError.
monthly_cost_provisioned(rcu, wcu, hours=730, price=PRICES) -> float
    hours x (rcu x rcu price + wcu x wcu price), rounded to 4 decimal places. Negative inputs are a
    ValueError. A month is 730 hours.
break_even_utilisation(price=PRICES) -> {"writes": f, "reads": f}
    The average fraction of provisioned capacity you must actually use for provisioned to cost the
    same as on-demand. One unit-hour of provisioned capacity can serve 3,600 units of requests
    (one per second). On-demand would charge 3,600 x (price per million / 1,000,000) for the same.
    So utilisation = unit-hour price / that amount. Round each to 4 decimal places.
Examples (with the default prices):
    monthly_cost_on_demand(1_000_000, 1_000_000, 1) == 0.6875
    monthly_cost_provisioned(100, 100) == 56.94
    break_even_utilisation() == {"writes": 0.2889, "reads": 0.2889}
Why? Provisioned is cheaper only for steady, busy tables: below about 29% average use you pay for
idle capacity. A spiky or unpredictable table belongs on on-demand (AWS now makes it the default for
most workloads). Reserved capacity can cut provisioned further, but only if the load is steady.
Hint: round(x, 4). The two on-demand prices differ, so reads and writes get their own sum.
"""
def monthly_cost_on_demand(reads_per_month, writes_per_month, item_kb, consistency="eventual",
                           transactional_writes=False, price=PRICES):
    raise NotImplementedError  # YOUR CODE


def monthly_cost_provisioned(rcu, wcu, hours=730, price=PRICES):
    raise NotImplementedError  # YOUR CODE


def break_even_utilisation(price=PRICES):
    raise NotImplementedError  # YOUR CODE


class Ex02(Drill):
    """On-demand or provisioned? ★"""
    tasks = ("4.3",)

    SECONDS_PER_MONTH = 730 * 3600

    def test_on_demand_cost(self):
        self.assertEqual(monthly_cost_on_demand(1_000_000, 1_000_000, 1), 0.6875)
        self.assertEqual(monthly_cost_on_demand(0, 2_000_000, 1), 1.25)
        self.assertEqual(monthly_cost_on_demand(2_000_000, 0, 1, "strong"), 0.25)

    def test_on_demand_uses_units_not_requests(self):
        # 1 million writes of 2.5 KB are 3 write units each, so 3 million units.
        self.assertEqual(monthly_cost_on_demand(0, 1_000_000, 2.5), 1.875)
        self.assertEqual(monthly_cost_on_demand(0, 1_000_000, 2.5, transactional_writes=True), 3.75)
        self.assertEqual(monthly_cost_on_demand(1_000_000, 0, 6, "transactional"), 0.5)

    def test_provisioned_cost_is_for_every_hour(self):
        self.assertEqual(monthly_cost_provisioned(100, 100), 56.94)
        self.assertEqual(monthly_cost_provisioned(0, 0), 0.0)
        self.assertEqual(monthly_cost_provisioned(100, 100, hours=365), 28.47)

    def test_provisioned_cost_does_not_depend_on_use(self):
        # The function has no 'requests' input at all: idle or busy, the bill is the same.
        self.assertEqual(monthly_cost_provisioned(25, 100), 49.8225)
        self.assertEqual(monthly_cost_provisioned(25, 100, hours=730), 49.8225)

    def test_a_spiky_low_traffic_table_is_cheaper_on_demand(self):
        # Busy for one hour a month: 100 writes/s and 50 reads/s of 1 KB items, idle the rest of the time.
        writes, reads = 100 * 3600, 50 * 3600
        on_demand = monthly_cost_on_demand(reads, writes, 1)
        rcu, wcu = provisioned_capacity(50, 100, 1)   # provisioned must be sized for the peak
        provisioned = monthly_cost_provisioned(rcu, wcu)
        self.assertAlmostEqual(on_demand, 0.2363, places=3)
        self.assertAlmostEqual(provisioned, 49.8225, places=3)
        self.assertLess(on_demand, provisioned, "idle capacity is the cost of provisioned mode")

    def test_a_steady_busy_table_is_cheaper_provisioned(self):
        # 100 writes/s and 200 reads/s of 1 KB items, all month long.
        writes, reads = 100 * self.SECONDS_PER_MONTH, 200 * self.SECONDS_PER_MONTH
        on_demand = monthly_cost_on_demand(reads, writes, 1)
        rcu, wcu = provisioned_capacity(200, 100, 1)
        provisioned = monthly_cost_provisioned(rcu, wcu)
        self.assertAlmostEqual(on_demand, 197.1, places=2)
        self.assertAlmostEqual(provisioned, 56.94, places=2)
        self.assertLess(provisioned, on_demand, "full use of provisioned capacity beats paying per request")

    def test_break_even(self):
        self.assertEqual(break_even_utilisation(), {"writes": 0.2889, "reads": 0.2889})

    def test_custom_prices_are_honoured(self):
        custom = {"dynamodb_on_demand_per_million_writes": 1.0, "dynamodb_on_demand_per_million_reads": 0.5,
                  "dynamodb_wcu_hour": 0.001, "dynamodb_rcu_hour": 0.0005}
        self.assertEqual(monthly_cost_on_demand(2_000_000, 1_000_000, 1, price=custom), 1.5)
        self.assertEqual(monthly_cost_provisioned(10, 10, hours=100, price=custom), 1.5)
        self.assertEqual(break_even_utilisation(custom), {"writes": 0.2778, "reads": 0.2778})

    def test_negative_inputs(self):
        with self.assertRaises(ValueError):
            monthly_cost_on_demand(-1, 0, 1)
        with self.assertRaises(ValueError):
            monthly_cost_on_demand(0, -1, 1)
        with self.assertRaises(ValueError):
            monthly_cost_provisioned(-1, 0)
        with self.assertRaises(ValueError):
            monthly_cost_provisioned(1, 1, hours=-5)


# ── Exercise 03 ★: One table, every question ─────────────────────────
"""
DynamoDB is fast because every question must start from a partition key: Query reads ONE partition,
in sort-key order. Scan reads everything and bills for all of it. So you design the table around the
questions, and "single-table design" puts different kinds of items in one table with generic key names.
Shortly's three questions:
    1. Get a link by its code.
    2. All clicks of one link between two days, in date order.
    3. All links of one owner, newest first.
Design ONE table that answers all three with Query (never Scan).
TABLE = {"KeySchema": [...], "AttributeDefinitions": [...], "GlobalSecondaryIndexes": [one index]}
    Pick the key names yourself ("pk" and "sk" are conventional). The table has a partition key and a
    sort key. It has exactly ONE global secondary index (GSI) and no local secondary index. A GSI is a
    second copy of the data under a different partition key: that is how you ask question 3, because the
    base table is keyed by link and the question is about owners. Each index needs IndexName, KeySchema
    and a Projection (use {"ProjectionType": "ALL"}). AttributeDefinitions lists every attribute used in
    any key, once, with type "S" (string) — and no others.
link_item(code, url, owner, created) -> dict
    The item to store for a link. `created` is an ISO time like "2026-10-12T09:30:00Z". Put the table's
    key attributes in it, plus "code", "url", "owner", "created", and the GSI key attributes.
click_item(code, day, count) -> dict
    The item for the clicks of one link on one day (`day` is "2026-10-12"). Same table, same partition
    as the link, so one Query can fetch them in order. Include "day" and "count".
get_link(table, code) -> dict or None
    The link item's "code", "url" and "owner" as a dict, or None if there is no such link.
clicks_between(table, code, first_day, last_day) -> list of (day, count)
    Clicks for the link from first_day to last_day INCLUDING both ends, oldest first. One Query.
links_of_owner(table, owner) -> list of codes
    Every link of that owner, newest `created` first. One Query on the GSI.
`table` is a boto3 Table resource (items are plain dicts); `Key` from boto3.dynamodb.conditions is
imported for you. The tests build the table from your TABLE, write items with your builders, and fail
the moment you call Scan.
Why? You cannot join in DynamoDB, so the key design IS the query design. Prefixes such as "LINK#abc"
let different item types share a partition, and an ISO date as a sort key makes between() work.
Hint: Key("pk").eq(...) & Key("sk").between(a, b) and table.query(KeyConditionExpression=..., IndexName=...,
      ScanIndexForward=False). Sort-key conditions on strings compare alphabetically, which is why dates
      are written year-month-day.
"""
TABLE = {
    "KeySchema": [],               # YOUR CODE
    "AttributeDefinitions": [],    # YOUR CODE
    "GlobalSecondaryIndexes": [],  # YOUR CODE (exactly one)
}


def link_item(code, url, owner, created):
    raise NotImplementedError  # YOUR CODE


def click_item(code, day, count):
    raise NotImplementedError  # YOUR CODE


def get_link(table, code):
    raise NotImplementedError  # YOUR CODE


def clicks_between(table, code, first_day, last_day):
    raise NotImplementedError  # YOUR CODE


def links_of_owner(table, owner):
    raise NotImplementedError  # YOUR CODE


class Ex03(Drill):
    """One table, every question ★"""
    tasks = ("3.3",)
    uses_aws = True

    def make(self):
        """Create the table from TABLE, load sample data, and forbid Scan."""
        ddb = self.resource("dynamodb")
        table = ddb.create_table(TableName="shortly-single", BillingMode="PAY_PER_REQUEST", **TABLE)

        def no_scan(**kwargs):
            raise AssertionError("you called Scan, which reads the whole table; answer with Query")

        table.meta.client.meta.events.register("before-parameter-build.dynamodb.Scan", no_scan)
        links = [("abc", "https://example.com/a", "alice", "2026-10-01T08:00:00Z"),
                 ("def", "https://example.com/d", "alice", "2026-10-03T08:00:00Z"),
                 ("ghi", "https://example.com/g", "alice", "2026-10-02T08:00:00Z"),
                 ("xyz", "https://example.com/x", "bob", "2026-10-04T08:00:00Z")]
        for code, url, owner, created in links:
            table.put_item(Item=link_item(code, url, owner, created))
        for day in range(8, 15):
            table.put_item(Item=click_item("abc", f"2026-10-{day:02d}", day * 10))
        table.put_item(Item=click_item("xyz", "2026-10-10", 5))
        return table

    def test_table_shape(self):
        self.assertEqual(len(TABLE["KeySchema"]), 2, "a partition key and a sort key")
        self.assertEqual({k["KeyType"] for k in TABLE["KeySchema"]}, {"HASH", "RANGE"})
        self.assertEqual(len(TABLE["GlobalSecondaryIndexes"]), 1, "exactly one GSI")
        self.assertNotIn("LocalSecondaryIndexes", TABLE, "no local secondary index")
        gsi = TABLE["GlobalSecondaryIndexes"][0]
        self.assertTrue({"IndexName", "KeySchema", "Projection"} <= set(gsi), "an index needs a name, keys and a projection")
        used = {k["AttributeName"] for k in TABLE["KeySchema"]} | {k["AttributeName"] for k in gsi["KeySchema"]}
        defined = {a["AttributeName"] for a in TABLE["AttributeDefinitions"]}
        self.assertEqual(defined, used, "AttributeDefinitions lists exactly the key attributes, once each")

    def test_builders_set_every_key_attribute(self):
        self.assertTrue(TABLE["KeySchema"] and TABLE["GlobalSecondaryIndexes"], "define TABLE first")
        keys = {k["AttributeName"] for k in TABLE["KeySchema"]}
        index_keys = {k["AttributeName"] for k in TABLE["GlobalSecondaryIndexes"][0]["KeySchema"]}
        link = link_item("abc", "https://example.com/a", "alice", "2026-10-01T08:00:00Z")
        self.assertTrue((keys | index_keys) <= set(link), "a link item needs the table keys and the index keys")
        click = click_item("abc", "2026-10-08", 3)
        self.assertTrue(keys <= set(click), "a click item needs the table keys")
        self.assertEqual((click["day"], click["count"]), ("2026-10-08", 3))

    def test_get_link_by_code(self):
        table = self.make()
        got = get_link(table, "abc")
        self.assertEqual((got["code"], got["url"], got["owner"]), ("abc", "https://example.com/a", "alice"))
        self.assertIsNone(get_link(table, "nope"))

    def test_clicks_between_dates_in_order(self):
        table = self.make()
        self.assertEqual(clicks_between(table, "abc", "2026-10-10", "2026-10-12"),
                         [("2026-10-10", 100), ("2026-10-11", 110), ("2026-10-12", 120)])

    def test_clicks_bounds_are_inclusive_and_per_link(self):
        table = self.make()
        self.assertEqual(clicks_between(table, "abc", "2026-10-08", "2026-10-08"), [("2026-10-08", 80)])
        self.assertEqual(clicks_between(table, "xyz", "2026-10-01", "2026-10-31"), [("2026-10-10", 5)],
                         "another link's clicks must not leak in, and a link's own item is not a click")
        self.assertEqual(len(clicks_between(table, "abc", "2026-10-01", "2026-10-31")), 7)
        self.assertEqual(clicks_between(table, "abc", "2026-11-01", "2026-11-30"), [])

    def test_links_of_owner_newest_first(self):
        table = self.make()
        self.assertEqual(links_of_owner(table, "alice"), ["def", "ghi", "abc"])
        self.assertEqual(links_of_owner(table, "bob"), ["xyz"])
        self.assertEqual(links_of_owner(table, "carol"), [])


# ── Exercise 04: Never lose an update ────────────────────────────────
"""
Two people open the same link, both change it, both save. Without protection the second save silently
overwrites the first: a LOST UPDATE. DynamoDB gives you conditional writes: a ConditionExpression is
checked and the write happens in one atomic step, so the check cannot be beaten by a race.
Optimistic locking uses a `version` number: read the item (and its version), change it, and write it back
only IF the version is still what you read. If somebody else got there first, the condition fails and
you must re-read and try again. This table is already created for you (TABLE_NAME, key "pk"):
    link   {"pk": "LINK#<code>", "url": ..., "owner": ..., "version": 1}
    owner  {"pk": "OWNER#<name>", "link_count": 3}
class StaleVersion(Exception)    Define it: raised when the version you expected is out of date.
rename_link(table, code, new_url, expected_version) -> int
    `table` is a Table resource. Set the link's url and raise its version by one, only if the stored
    version equals expected_version. Return the new version. If the condition fails (ConditionalCheck-
    FailedException) raise StaleVersion; re-raise any other error. A link that does not exist counts as
    stale too: your call must NOT create it.
transfer_owner(client, code, old_owner, new_owner)
    `client` is a low-level dynamodb client (typed values like {"S": "alice"}). Move a link to a new owner
    and fix both owners' link_count, in ONE transact_write_items call:
      - the link: set owner to new_owner and raise version by one, only if its owner is old_owner
      - OWNER#old_owner: link_count down by one
      - OWNER#new_owner: link_count up by one (the owner item may not exist yet; ADD creates it)
    A transaction is all-or-nothing: if the link is not owned by old_owner, NOTHING changes, and the
    TransactionCanceledException reaches the caller. old_owner equal to new_owner is a ValueError.
Why? "Read, change, write" is a race. A condition makes the database referee it. A transaction makes
several items change together or not at all, so a counter can never disagree with the data it counts.
Hint: update_item(Key=..., UpdateExpression="SET #u = :u, #v = :next", ConditionExpression="#v = :expected",
      ExpressionAttributeNames=..., ExpressionAttributeValues=...) — url and version are easier through
      #name placeholders. ADD link_count :one both creates and increments a number. In a transaction each
      item in TransactItems is {"Update": {"TableName": ..., "Key": ..., ...}}.
"""
TABLE_NAME = "shortly"
StaleVersion = None  # YOUR CODE: define an Exception subclass called StaleVersion


def rename_link(table, code, new_url, expected_version):
    raise NotImplementedError  # YOUR CODE


def transfer_owner(client, code, old_owner, new_owner):
    raise NotImplementedError  # YOUR CODE


class Ex04(Drill):
    """Never lose an update"""
    tasks = ("3.3", "2.2")
    uses_aws = True

    def make(self):
        ddb = self.client("dynamodb")
        ddb.create_table(TableName=TABLE_NAME, BillingMode="PAY_PER_REQUEST",
                         KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}],
                         AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"}])
        table = self.resource("dynamodb").Table(TABLE_NAME)
        table.put_item(Item={"pk": "LINK#abc", "url": "https://example.com/old", "owner": "alice", "version": 1})
        table.put_item(Item={"pk": "OWNER#alice", "link_count": 3})
        return ddb, table

    def link(self, table):
        return table.get_item(Key={"pk": "LINK#abc"}, ConsistentRead=True)["Item"]

    def count(self, table, owner):
        item = table.get_item(Key={"pk": f"OWNER#{owner}"}, ConsistentRead=True).get("Item")
        return None if item is None else int(item["link_count"])

    def test_rename_bumps_the_version(self):
        _, table = self.make()
        self.assertEqual(rename_link(table, "abc", "https://example.com/new", 1), 2)
        item = self.link(table)
        self.assertEqual((item["url"], int(item["version"])), ("https://example.com/new", 2))
        self.assertEqual(item["owner"], "alice", "other attributes are untouched")
        self.assertEqual(rename_link(table, "abc", "https://example.com/newer", 2), 3)

    def test_two_readers_one_wins(self):
        _, table = self.make()
        seen_by_a = seen_by_b = int(self.link(table)["version"])      # both read version 1
        rename_link(table, "abc", "https://example.com/from-a", seen_by_a)
        with self.assertRaises(StaleVersion, msg="B read the old version, so B's write must be refused"):
            rename_link(table, "abc", "https://example.com/from-b", seen_by_b)
        item = self.link(table)
        self.assertEqual(item["url"], "https://example.com/from-a", "A's update must not be overwritten")
        self.assertEqual(int(item["version"]), 2)

    def test_a_missing_link_is_stale_and_not_created(self):
        _, table = self.make()
        with self.assertRaises(StaleVersion):
            rename_link(table, "ghost", "https://example.com/x", 1)
        self.assertNotIn("Item", table.get_item(Key={"pk": "LINK#ghost"}),
                         "update_item creates missing items unless your condition stops it")

    def test_stale_version_is_an_exception_class(self):
        self.assertTrue(isinstance(StaleVersion, type) and issubclass(StaleVersion, Exception))

    def test_transfer_moves_the_link_and_both_counters(self):
        ddb, table = self.make()
        transfer_owner(ddb, "abc", "alice", "bob")
        item = self.link(table)
        self.assertEqual((item["owner"], int(item["version"])), ("bob", 2))
        self.assertEqual(self.count(table, "alice"), 2)
        self.assertEqual(self.count(table, "bob"), 1, "a first link creates the owner's counter")

    def test_a_failed_transfer_changes_nothing(self):
        ddb, table = self.make()
        with self.assertClientError("TransactionCanceledException"):
            transfer_owner(ddb, "abc", "carol", "bob")      # the link is alice's, not carol's
        item = self.link(table)
        self.assertEqual((item["owner"], int(item["version"])), ("alice", 1))
        self.assertEqual(self.count(table, "alice"), 3, "counters must not move when the transaction fails")
        self.assertIsNone(self.count(table, "bob"))
        self.assertIsNone(self.count(table, "carol"))

    def test_repeating_a_transfer_is_refused(self):
        ddb, table = self.make()
        transfer_owner(ddb, "abc", "alice", "bob")
        with self.assertClientError("TransactionCanceledException"):
            transfer_owner(ddb, "abc", "alice", "bob")      # alice no longer owns it
        self.assertEqual((self.count(table, "alice"), self.count(table, "bob")), (2, 1))

    def test_same_owner_is_a_value_error(self):
        ddb, _ = self.make()
        with self.assertRaises(ValueError):
            transfer_owner(ddb, "abc", "alice", "alice")


# ── Exercise 05: Keep it tidy, keep it safe ──────────────────────────
"""
Three protections every real table wants, and each is one API call.
protect_table(client, table_name, ttl_attribute) -> str
    `client` is a low-level dynamodb client. Do all three, then return the backup's ARN:
      1. TTL (time to live) on the attribute `ttl_attribute`: update_time_to_live. The attribute holds a
         Unix time in seconds (a Number). DynamoDB deletes items whose time has passed, in the
         background, for free: it does not use write capacity.
      2. Point-in-time recovery (PITR) on: update_continuous_backups. You can then restore the table to
         any second in the last 35 days (the default; you may choose 1 to 35).
      3. An on-demand backup named "<table_name>-baseline": create_backup. It is kept until you delete it.
What each one will NOT do:
  - TTL is not a timer. Expired items are deleted "within a few days" of expiring, and until then they
    can still be read. Code that must hide expired items has to filter on the time itself.
    (moto never deletes anything by TTL, so no test here waits for it.)
  - A restore never overwrites: both PITR and backup restores create a NEW table. You then switch your
    application to it (or copy the data back).
  - Turning protections on later does not give you history from before: PITR starts when you enable it.
Why? Backups and recovery are the standard answer to "someone deleted or corrupted the data", and TTL is
the standard answer to "sessions and temporary rows pile up forever".
Hint: update_time_to_live(TableName=..., TimeToLiveSpecification={"Enabled": True, "AttributeName": ...});
      update_continuous_backups(TableName=..., PointInTimeRecoverySpecification={"PointInTimeRecoveryEnabled": True});
      create_backup(TableName=..., BackupName=...)["BackupDetails"]["BackupArn"].
"""
def protect_table(client, table_name, ttl_attribute):
    raise NotImplementedError  # YOUR CODE


class Ex05(Drill):
    """Keep it tidy, keep it safe"""
    tasks = ("3.3", "2.2")
    uses_aws = True

    def make(self, name="sessions"):
        ddb = self.client("dynamodb")
        ddb.create_table(TableName=name, BillingMode="PAY_PER_REQUEST",
                         KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}],
                         AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"}])
        return ddb

    def test_ttl_is_enabled_on_the_attribute(self):
        ddb = self.make()
        protect_table(ddb, "sessions", "expires_at")
        ttl = ddb.describe_time_to_live(TableName="sessions")["TimeToLiveDescription"]
        self.assertIn(ttl["TimeToLiveStatus"], ("ENABLED", "ENABLING"))
        self.assertEqual(ttl.get("AttributeName"), "expires_at")

    def test_point_in_time_recovery_is_on(self):
        ddb = self.make()
        before = ddb.describe_continuous_backups(TableName="sessions")["ContinuousBackupsDescription"]
        self.assertEqual(before["PointInTimeRecoveryDescription"]["PointInTimeRecoveryStatus"], "DISABLED")
        protect_table(ddb, "sessions", "expires_at")
        after = ddb.describe_continuous_backups(TableName="sessions")["ContinuousBackupsDescription"]
        self.assertEqual(after["PointInTimeRecoveryDescription"]["PointInTimeRecoveryStatus"], "ENABLED",
                         "PITR is what lets you undo a bad write from an hour ago")

    def test_baseline_backup_exists_and_its_arn_is_returned(self):
        ddb = self.make()
        arn = protect_table(ddb, "sessions", "expires_at")
        backups = ddb.list_backups(TableName="sessions")["BackupSummaries"]
        self.assertEqual([b["BackupName"] for b in backups], ["sessions-baseline"])
        self.assertEqual(arn, backups[0]["BackupArn"])
        self.assertIn("arn:aws:dynamodb", arn)

    def test_works_for_any_table_name_and_attribute(self):
        ddb = self.make("orders")
        protect_table(ddb, "orders", "delete_after")
        self.assertEqual(ddb.describe_time_to_live(TableName="orders")["TimeToLiveDescription"]["AttributeName"], "delete_after")
        self.assertEqual(ddb.list_backups(TableName="orders")["BackupSummaries"][0]["BackupName"], "orders-baseline")

    def test_a_restore_creates_a_new_table(self):
        ddb = self.make()
        ddb.put_item(TableName="sessions", Item={"pk": {"S": "s1"}})
        arn = protect_table(ddb, "sessions", "expires_at")
        ddb.restore_table_from_backup(TargetTableName="sessions-restored", BackupArn=arn)
        names = ddb.list_tables()["TableNames"]
        self.assertIn("sessions", names)
        self.assertIn("sessions-restored", names, "a restore makes a NEW table; it never overwrites the old one")
        self.assertEqual(ddb.get_item(TableName="sessions-restored", Key={"pk": {"S": "s1"}})["Item"]["pk"]["S"], "s1")


# ── Exercise 06 ★: Cache it right ────────────────────────────────────
"""
A cache sits in front of a database and answers repeat reads from memory. Two common ways to fill it:
    "lazy" (lazy loading, cache-aside)  a read looks in the cache first. On a MISS it reads the database and
        stores the value in the cache. A write goes to the database only, so the cached copy can be STALE
        until it expires.
    "write-through"  every write goes to the database AND to the cache, so cached values are never stale.
        The price: you also cache data nobody may ever read, and each write does two things.
A TTL (time to live) on each cached entry limits how long a stale value can survive.
simulate(events, strategy, ttl=None) -> dict
    events is a list of tuples (time_s, "read", key) for a read or (time_s, "write", key, value) for a
    write; times never go backwards. The database starts empty. Replay the events and return these counts:
      "hits"          reads answered from the cache
      "misses"        reads not in the cache (never cached, or expired)
      "db_reads"      database reads (one per miss, even for a key never written, which reads as None)
      "db_writes"     database writes
      "cache_writes"  times a value is put in the cache (on a miss, and on every write-through write)
      "stale_reads"   hits whose cached value differs from the database's current value
    An entry cached at time t expires at t + ttl; a read at exactly t + ttl is a MISS. ttl None = never.
    A read of a key nobody wrote returns None and is still cached (so it can hit next time).
    ValueError for: strategy not "lazy" or "write-through"; op not "read"/"write"; a write without a value;
    an event that is not 3 or 4 long; time going backwards; ttl zero or negative.
Examples:
    simulate([(0, "write", "k", 1), (1, "read", "k")], "write-through")
        -> hits 1, misses 0, db_writes 1, cache_writes 1
    simulate([(0, "read", "k"), (1, "write", "k", 5), (2, "read", "k")], "lazy")
        -> the second read is a hit on the OLD cached value: stale_reads 1
Why? This is the heart of every "improve read performance" question: lazy loading is simple and only
caches what is read, but can serve stale data; write-through keeps the cache fresh but writes more.
AWS recommends combining either with a TTL.
Hint: keep two dicts, db and cache; cache[key] = (value, expires_at). Check expiry with now < expires_at.
"""
def simulate(events, strategy, ttl=None):
    raise NotImplementedError  # YOUR CODE


class Ex06(Drill):
    """Cache it right ★"""
    tasks = ("3.3",)

    def count(self, result, **want):
        got = {k: result[k] for k in want}
        self.assertEqual(got, want)

    def test_cold_start_misses_then_hits(self):
        result = simulate([(0, "write", "k", 1), (1, "read", "k"), (2, "read", "k"), (3, "read", "k")], "lazy")
        self.count(result, hits=2, misses=1, db_reads=1, db_writes=1, cache_writes=1, stale_reads=0)

    def test_every_key_misses_the_first_time(self):
        events = [(0, "write", "a", 1), (0, "write", "b", 2), (1, "read", "a"), (1, "read", "b"), (2, "read", "a")]
        self.count(simulate(events, "lazy"), hits=1, misses=2, db_reads=2)

    def test_reading_a_key_nobody_wrote(self):
        result = simulate([(0, "read", "ghost"), (1, "read", "ghost")], "lazy")
        self.count(result, misses=1, hits=1, db_reads=1, cache_writes=1, stale_reads=0)

    def test_lazy_serves_stale_reads_after_a_write(self):
        events = [(0, "write", "k", 1), (1, "read", "k"), (2, "write", "k", 2), (3, "read", "k"), (4, "read", "k")]
        result = simulate(events, "lazy")
        self.count(result, hits=2, misses=1, stale_reads=2, db_writes=2, cache_writes=1)

    def test_write_through_is_never_stale(self):
        events = [(0, "write", "k", 1), (1, "read", "k"), (2, "write", "k", 2), (3, "read", "k"), (4, "read", "k")]
        result = simulate(events, "write-through")
        self.count(result, hits=3, misses=0, stale_reads=0, db_reads=0, db_writes=2, cache_writes=2)

    def test_write_through_caches_data_nobody_reads(self):
        events = [(0, "write", "a", 1), (1, "write", "b", 2), (2, "write", "c", 3), (3, "read", "a")]
        self.count(simulate(events, "write-through"), cache_writes=3, hits=1)
        self.count(simulate(events, "lazy"), cache_writes=1, hits=0, misses=1)

    def test_ttl_boundary_is_a_miss(self):
        events = [(0, "write", "k", 1), (10, "read", "k"), (70, "read", "k"), (71, "read", "k")]
        result = simulate(events, "lazy", ttl=60)
        # t=10 miss (cached, expires 70) · t=70 exactly at expiry: miss again (expires 130) · t=71 hit
        self.count(result, misses=2, hits=1, db_reads=2)

    def test_just_before_expiry_is_a_hit(self):
        result = simulate([(0, "write", "k", 1), (0, "read", "k"), (59.9, "read", "k")], "lazy", ttl=60)
        self.count(result, hits=1, misses=1)

    def test_ttl_ends_staleness(self):
        events = [(0, "write", "k", 1), (1, "read", "k"), (2, "write", "k", 2), (30, "read", "k"), (61, "read", "k"), (62, "read", "k")]
        result = simulate(events, "lazy", ttl=60)
        # cached at t=1 (expires 61): t=30 hit but stale; t=61 miss reloads value 2; t=62 hit, fresh
        self.count(result, hits=2, misses=2, stale_reads=1, db_reads=2)

    def test_write_through_entries_expire_too(self):
        events = [(0, "write", "k", 1), (59, "read", "k"), (60, "read", "k")]
        result = simulate(events, "write-through", ttl=60)
        self.count(result, hits=1, misses=1, db_reads=1, cache_writes=2)

    def test_empty_event_list(self):
        self.count(simulate([], "lazy"), hits=0, misses=0, db_reads=0, db_writes=0, cache_writes=0, stale_reads=0)

    def test_returns_exactly_the_six_counts(self):
        self.assertEqual(set(simulate([], "lazy")), {"hits", "misses", "db_reads", "db_writes", "cache_writes", "stale_reads"})

    def test_invalid_input(self):
        bad = [
            ([(0, "read", "k")], "write-behind", None),
            ([(0, "delete", "k")], "lazy", None),
            ([(0, "write", "k")], "lazy", None),
            ([(0, "read")], "lazy", None),
            ([(5, "read", "k"), (4, "read", "k")], "lazy", None),
            ([(0, "read", "k")], "lazy", 0),
            ([(0, "read", "k")], "lazy", -5),
        ]
        for events, strategy, ttl in bad:
            with self.subTest(events=events, strategy=strategy, ttl=ttl):
                with self.assertRaises(ValueError):
                    simulate(events, strategy, ttl)


# ── Exercise 07: Too many connections ────────────────────────────────
"""
Every database connection costs memory, so a database has a ceiling called max_connections (RDS sets it
from the instance memory: bigger instance, more connections; a tiny one allows only a few dozen to a
hundred). A web server reuses a handful of connections. Lambda cannot: each running function instance
opens its own, so a burst of requests becomes a burst of connections, and the database starts refusing
them ("too many connections") long before the CPU is busy.
RDS Proxy fixes this: it keeps a POOL of database connections open and shares them among many short
client connections, and it also makes failover faster (it skips waiting for DNS to update).
peak_concurrency(requests_per_second, avg_duration_s) -> int
    How many function instances run at once (Little's law): requests per second x duration, rounded UP.
    Beware floating point: 10 x 0.3 is 3.0000000000000004 in Python and must give 3. Zero or negative
    inputs are a ValueError.
needs_proxy(concurrency, max_connections, connections_per_invocation=1, headroom=0.0) -> bool
    Without a proxy every concurrent invocation holds connections_per_invocation connections. True when
    that total is MORE than max_connections x (1 - headroom) (exactly equal still fits). headroom is the
    share you keep free for admin and replication, from 0 up to but not including 1. Zero or negative
    concurrency or max_connections, or a bad headroom, is a ValueError.
proxy_pool_size(max_connections, max_connections_percent) -> int
    The connections the proxy may open to the database: max_connections x percent / 100, rounded DOWN.
    The percent must be above 0 and at most 100; otherwise ValueError.
Examples:
    peak_concurrency(500, 0.2) == 100       needs_proxy(100, 90) is True       proxy_pool_size(90, 50) == 45
Why? The proxy lets 300 short function instances share, say, 50 database connections. The exam signal is
"Lambda + RDS + connection errors" and the answer is RDS Proxy (or fewer connections per function).
Hint: math.ceil(round(x, 9)) removes float noise before rounding up; math.floor for the pool.
"""
def peak_concurrency(requests_per_second, avg_duration_s):
    raise NotImplementedError  # YOUR CODE


def needs_proxy(concurrency, max_connections, connections_per_invocation=1, headroom=0.0):
    raise NotImplementedError  # YOUR CODE


def proxy_pool_size(max_connections, max_connections_percent):
    raise NotImplementedError  # YOUR CODE


class Ex07(Drill):
    """Too many connections"""
    tasks = ("3.3",)

    def test_peak_concurrency(self):
        self.assertEqual(peak_concurrency(500, 0.2), 100)
        self.assertEqual(peak_concurrency(1000, 0.3), 300)
        self.assertEqual(peak_concurrency(1, 1), 1)

    def test_concurrency_rounds_up(self):
        self.assertEqual(peak_concurrency(7, 0.5), 4, "3.5 instances do not exist: you need 4")
        self.assertEqual(peak_concurrency(1, 0.01), 1, "a tiny load still needs one instance")

    def test_float_noise_does_not_add_an_instance(self):
        self.assertEqual(peak_concurrency(10, 0.3), 3, "10 x 0.3 is 3.0000000000000004 in floating point")
        self.assertEqual(peak_concurrency(3, 0.1), 1)

    def test_concurrency_rejects_bad_input(self):
        for rps, dur in ((0, 1), (-5, 1), (5, 0), (5, -1)):
            with self.subTest(rps=rps, dur=dur):
                with self.assertRaises(ValueError):
                    peak_concurrency(rps, dur)

    def test_a_lambda_burst_needs_a_proxy(self):
        concurrency = peak_concurrency(1000, 0.3)      # 300 functions at once
        self.assertTrue(needs_proxy(concurrency, 100), "300 connections against a 100-connection database")
        self.assertFalse(needs_proxy(concurrency, 500))

    def test_exactly_at_the_limit_still_fits(self):
        self.assertFalse(needs_proxy(100, 100))
        self.assertTrue(needs_proxy(101, 100))
        self.assertTrue(needs_proxy(100, 90))

    def test_several_connections_per_invocation(self):
        self.assertTrue(needs_proxy(60, 100, connections_per_invocation=2), "60 x 2 = 120 connections")
        self.assertFalse(needs_proxy(50, 100, connections_per_invocation=2))

    def test_headroom_keeps_connections_free(self):
        self.assertFalse(needs_proxy(85, 100))
        self.assertTrue(needs_proxy(85, 100, headroom=0.2), "only 80 of the 100 may be used")
        self.assertFalse(needs_proxy(80, 100, headroom=0.2))

    def test_needs_proxy_rejects_bad_input(self):
        for args, kwargs in (((0, 100), {}), ((10, 0), {}), ((10, -1), {}), ((10, 100), {"headroom": -0.1}),
                             ((10, 100), {"headroom": 1.0})):
            with self.subTest(args=args, kwargs=kwargs):
                with self.assertRaises(ValueError):
                    needs_proxy(*args, **kwargs)

    def test_pool_size(self):
        self.assertEqual(proxy_pool_size(90, 50), 45)
        self.assertEqual(proxy_pool_size(100, 100), 100)
        self.assertEqual(proxy_pool_size(100, 33), 33)

    def test_pool_size_rounds_down(self):
        self.assertEqual(proxy_pool_size(91, 50), 45, "45.5 connections: you cannot open half, and must not exceed the share")
        self.assertEqual(proxy_pool_size(10, 99), 9)

    def test_pool_size_rejects_bad_input(self):
        for maxc, pct in ((0, 50), (-1, 50), (100, 0), (100, -5), (100, 101)):
            with self.subTest(max_connections=maxc, percent=pct):
                with self.assertRaises(ValueError):
                    proxy_pool_size(maxc, pct)

    def test_the_proxy_makes_the_burst_fit(self):
        pool = proxy_pool_size(100, 80)
        self.assertEqual(pool, 80)
        self.assertLess(pool, peak_concurrency(1000, 0.3), "the proxy shares 80 connections among 300 functions")


# ── Exercise 08: A database that fails over ──────────────────────────
"""
Build shortly's production database with boto3. Each setting answers a failure or a risk:
create_primary(rds, subnet_group, sg_id) -> "shortly-db"
    create_db_instance with: identifier "shortly-db" · engine "postgres", EngineVersion "17.4" ·
    class "db.t4g.micro" · 20 GiB of "gp3" storage ·
    MultiAZ True  (a synchronous standby in another AZ: if the AZ fails, RDS fails over automatically in
                   about 60-120 seconds; the standby serves NO reads — it is for availability only) ·
    StorageEncrypted True  (encryption can only be turned on at creation, never later) ·
    ManageMasterUserPassword True with MasterUsername "shortly_admin" and NO MasterUserPassword
                   (RDS creates the password in Secrets Manager and rotates it; it never sits in your code) ·
    BackupRetentionPeriod 7 (days of point-in-time restore) · DeletionProtection True (a delete is refused
    until protection is switched off) · PubliclyAccessible False ·
    DBSubnetGroupName=subnet_group · VpcSecurityGroupIds=[sg_id]
add_replica(rds, primary_id) -> "shortly-db-replica"
    create_db_instance_read_replica from the primary, class "db.t4g.micro". A read replica copies data
    asynchronously and CAN serve reads (reporting, scaling reads). It is a different tool from Multi-AZ.
take_snapshot(rds, db_id) -> "<db_id>-baseline"
    create_db_snapshot with that id. A manual snapshot is kept until you delete it, even after the
    database is gone.
Note: moto stores these settings but has no standby, no failover and no real replication, so the tests
read the settings back.
Why? These are the five defaults of a database you can defend in an exam answer: Multi-AZ, encryption,
no hard-coded password, backups, and protection against accidental deletion.
Hint: rds.create_db_instance(DBInstanceIdentifier=..., Engine=..., MultiAZ=True, ...);
      rds.create_db_instance_read_replica(DBInstanceIdentifier=..., SourceDBInstanceIdentifier=...).
"""
def create_primary(rds, subnet_group, sg_id):
    raise NotImplementedError  # YOUR CODE


def add_replica(rds, primary_id):
    raise NotImplementedError  # YOUR CODE


def take_snapshot(rds, db_id):
    raise NotImplementedError  # YOUR CODE


class Ex08(Drill):
    """A database that fails over"""
    tasks = ("2.2", "3.3")
    uses_aws = True

    def make(self):
        ec2, rds = self.client("ec2"), self.client("rds")
        vpc = ec2.create_vpc(CidrBlock="10.80.0.0/16")["Vpc"]["VpcId"]
        subnets = [ec2.create_subnet(VpcId=vpc, CidrBlock=f"10.80.{i}.0/24", AvailabilityZone=az)["Subnet"]["SubnetId"]
                   for i, az in enumerate(("us-east-1a", "us-east-1b"))]
        sg = ec2.create_security_group(GroupName="shortly-db", Description="db", VpcId=vpc)["GroupId"]
        rds.create_db_subnet_group(DBSubnetGroupName="shortly-subnets", DBSubnetGroupDescription="db", SubnetIds=subnets)
        calls = []
        rds.meta.events.register("provide-client-params.rds.CreateDBInstance",
                                 lambda params, **kw: calls.append(dict(params)))
        return rds, sg, calls

    def primary(self):
        rds, sg, calls = self.make()
        db_id = create_primary(rds, "shortly-subnets", sg)
        described = rds.describe_db_instances(DBInstanceIdentifier=db_id)["DBInstances"][0]
        return rds, sg, db_id, described, calls

    def test_identity_and_engine(self):
        _, _, db_id, db, _ = self.primary()
        self.assertEqual(db_id, "shortly-db")
        self.assertEqual((db["Engine"], db["DBInstanceClass"]), ("postgres", "db.t4g.micro"))
        self.assertTrue(db["EngineVersion"].startswith("17"), "pass EngineVersion explicitly (17.4)")

    def test_multi_az(self):
        _, _, _, db, _ = self.primary()
        self.assertTrue(db["MultiAZ"], "Multi-AZ gives a standby in a second AZ and automatic failover")

    def test_encrypted_gp3_storage(self):
        _, _, _, db, _ = self.primary()
        self.assertTrue(db["StorageEncrypted"], "encryption can only be set when the database is created")
        self.assertEqual((db["StorageType"], db["AllocatedStorage"]), ("gp3", 20))

    def test_password_is_managed_by_secrets_manager(self):
        rds, _, db_id, db, calls = self.primary()
        self.assertTrue(db.get("MasterUserSecret", {}).get("SecretArn"), "set ManageMasterUserPassword=True")
        self.assertEqual(db["MasterUsername"], "shortly_admin")
        self.assertTrue(calls, "create_db_instance was not called")
        self.assertNotIn("MasterUserPassword", calls[0], "no password in code: let RDS manage it")
        secrets = self.client("secretsmanager").list_secrets()["SecretList"]
        self.assertEqual(len(secrets), 1)
        self.assertTrue(secrets[0]["Name"].startswith("rds!"), "RDS-managed secrets are named rds!...")

    def test_backups_and_deletion_protection(self):
        rds, _, db_id, db, _ = self.primary()
        self.assertEqual(db["BackupRetentionPeriod"], 7)
        self.assertTrue(db["DeletionProtection"])
        with self.assertClientError("InvalidParameterCombination"):
            rds.delete_db_instance(DBInstanceIdentifier=db_id, SkipFinalSnapshot=True)

    def test_private_and_inside_your_network(self):
        _, sg, _, db, _ = self.primary()
        self.assertFalse(db["PubliclyAccessible"])
        self.assertEqual(db["DBSubnetGroup"]["DBSubnetGroupName"], "shortly-subnets")
        self.assertEqual([g["VpcSecurityGroupId"] for g in db["VpcSecurityGroups"]], [sg])

    def test_read_replica(self):
        rds, _, db_id, _, _ = self.primary()
        replica_id = add_replica(rds, db_id)
        self.assertEqual(replica_id, "shortly-db-replica")
        replica = rds.describe_db_instances(DBInstanceIdentifier=replica_id)["DBInstances"][0]
        self.assertEqual(replica["ReadReplicaSourceDBInstanceIdentifier"], db_id)
        self.assertEqual(replica["DBInstanceClass"], "db.t4g.micro")
        source = rds.describe_db_instances(DBInstanceIdentifier=db_id)["DBInstances"][0]
        self.assertEqual(source["ReadReplicaDBInstanceIdentifiers"], [replica_id])

    def test_manual_snapshot(self):
        rds, _, db_id, _, _ = self.primary()
        snapshot_id = take_snapshot(rds, db_id)
        self.assertEqual(snapshot_id, "shortly-db-baseline")
        snap = rds.describe_db_snapshots(DBSnapshotIdentifier=snapshot_id)["DBSnapshots"][0]
        self.assertEqual((snap["DBInstanceIdentifier"], snap["SnapshotType"], snap["Status"]), (db_id, "manual", "available"))


# ── Exercise 09 (decide): High availability, read scale or disaster recovery? ──
"""
Databases fail in different ways, and each AWS feature answers one of them. Choose ONE answer for
each scenario in CHOICES:
  "multi-az instance"          RDS: a synchronous standby in another AZ; automatic failover; the standby
                               serves no reads
  "multi-az cluster"           RDS: a writer plus two readable standbys in three AZs; faster failover
  "read replica"               RDS: an asynchronous copy that serves reads (and can be promoted)
  "aurora replica"             Aurora: up to 15 readers on the shared cluster storage; also failover targets
  "aurora global database"     Aurora: storage-level replication to other Regions, read-only secondaries
  "cross-region read replica"  RDS: a read replica in a different Region
  "rds proxy"                  a connection pool in front of the database
Replace every None with one of those answers. (The answers are stored as hashes, so reading the test
will not give them away.)
"""
CHOICE_SCENARIOS = {
    1: "RDS PostgreSQL on a single instance. It must survive the loss of an Availability Zone with automatic failover. "
       "It does not need more read capacity, and the team wants the smallest change.",
    2: "An RDS MySQL primary is slowed down by heavy reporting queries. Move the reports to a separate copy of the data. "
       "Reports may lag a little. Nobody asked for faster failover.",
    3: "An Aurora cluster needs more read capacity inside its Region, and wants a standby to take over quickly if the writer fails.",
    4: "A global Aurora MySQL application needs local low-latency reads in two other Regions, replication in under a second, "
       "and the ability to move writes to another Region if the primary Region fails.",
    5: "RDS PostgreSQL in one Region needs automatic failover that typically finishes in under 35 seconds, "
       "and two standby copies in other AZs that can also serve reads.",
    6: "An RDS MySQL database must have a copy in another Region that can be promoted for disaster recovery, "
       "without moving the database to Aurora.",
    7: "Lambda functions exhaust the database's connections during traffic bursts, and failovers take too long "
       "because applications wait for DNS to update.",
}
CHOICE_OPTIONS = ("multi-az instance", "multi-az cluster", "read replica", "aurora replica",
                  "aurora global database", "cross-region read replica", "rds proxy")
CHOICES = {n: None for n in CHOICE_SCENARIOS}   # YOUR ANSWERS: one of CHOICE_OPTIONS
CHOICE_DIGESTS = {
    1: "9a87adb6fb66d7fe68574ae02b3d4f4c81c1eaf464a0e7636368ea07bef8bdcf",
    2: "f8071d9f65c8d5e948c254d0653ce1e7588877d412392e2fe2f67880f113bb2e",
    3: "f47b6d932e642ca85546dd39f351b71d933fc37d038b7fc22c1b2dcd63cede13",
    4: "a04c8e260796069883ff55331ace0594671fe9656ffb9ee8b6f9773d197f59f4",
    5: "bfbe4038d81632b639c5678ba672f36ef84ba19a37dd7f209bd7dead1cf65e46",
    6: "9a48f643bf177be908753e817d0bc07bd2e70eae11c11e9a3ce1e73b152b6e62",
    7: "485f3fb0643281d5bafae2c5c04a879c039698af2df9931157b4a6a222705c25",
}


class Ex09(Drill):
    """High availability, read scale or disaster recovery? (decide)"""
    tasks = ("2.2", "3.3")

    def test_choices(self):
        for n, story in CHOICE_SCENARIOS.items():
            with self.subTest(scenario=n):
                value = CHOICES.get(n)
                self.assertIn(value, CHOICE_OPTIONS, f"scenario {n}: answer one of {CHOICE_OPTIONS}, not {value!r}")
                self.assertHashed(value, f"w05-ex09-{n}", CHOICE_DIGESTS[n],
                                  f"scenario {n} ({story}): {value!r} is not right — is it availability, read scale, "
                                  "another Region, or connections?")


# ── Exercise 10 (decide): The right engine ───────────────────────────
"""
AWS has a purpose-built database for most shapes of data. Choose the best service for each scenario:
  "rds"          managed MySQL, PostgreSQL, MariaDB, Oracle, SQL Server or Db2 on an instance
  "aurora"       MySQL- or PostgreSQL-compatible relational database with shared, auto-growing storage
  "dynamodb"     serverless key-value and document database
  "elasticache"  managed Valkey, Redis OSS or Memcached, used mostly as a cache
  "documentdb"   MongoDB-compatible document database
  "neptune"      graph database
  "keyspaces"    Apache Cassandra-compatible database
  "opensearch"   search and log analytics
  "memorydb"     durable in-memory database, Valkey and Redis OSS compatible
Replace every None in ENGINES. (Hashed answers again.)
"""
ENGINE_SCENARIOS = {
    1: "A relational order system built on PostgreSQL. Managed PostgreSQL on a single small instance is enough: "
       "no cluster features, and the least change from the current setup.",
    2: "A MySQL-compatible database that needs up to 15 low-lag read replicas sharing one storage volume that grows by itself.",
    3: "Shopping carts as key-value items: millions of requests per second, single-digit-millisecond latency, no servers to manage.",
    4: "A sub-millisecond leaderboard that sits in front of an existing database to take repeated reads off it.",
    5: "An application that stores JSON documents and talks to its database with MongoDB drivers.",
    6: "Fraud-ring detection: finding connections between accounts, cards and devices several hops apart.",
    7: "An existing application written for Apache Cassandra (CQL) that should run without managing any servers.",
    8: "Full-text search and log analytics over millions of events.",
    9: "A durable in-memory PRIMARY database (Redis-compatible) that must survive the loss of a node without losing acknowledged writes.",
}
ENGINE_OPTIONS = ("rds", "aurora", "dynamodb", "elasticache", "documentdb", "neptune", "keyspaces", "opensearch", "memorydb")
ENGINES = {n: None for n in ENGINE_SCENARIOS}   # YOUR ANSWERS: one of ENGINE_OPTIONS
ENGINE_DIGESTS = {
    1: "337191136a5f4a9dcc250faa253a757c167d3be737c4f9ff705399f74601e5ba",
    2: "dc9e0e13925bb2e0b2363fb3edc5d6b0156fade881ca79241ec64cda0666afb9",
    3: "7427a03aa2793b419a44df614b578523aed2c436a5e14b6405db408cb88adcb2",
    4: "dd986df93c9559e5778734fe568b6ef7d7dd51313d623c2ab13e07499845a68c",
    5: "eb9aeb6ac11bb890420fcd6836354610fa84cdde4c3ca3a249ced1cb63f17b77",
    6: "1034682c5cb780b756888d02cccc6e36b992f081bb93eefb2b0fc22a6ae7d611",
    7: "ab299714018294bb185827d55ce494c799d34c0fee08868528bc75f84d1e15aa",
    8: "7a23a497d65fc2f7cbb14348d8b08c89d4280f191e2944d5aff7554b51217ea9",
    9: "e46a403adec715d29ee7c93a002364831253659a7a917ee7b415fb9de3557c4e",
}


class Ex10(Drill):
    """The right engine (decide)"""
    tasks = ("3.3",)

    def test_engines(self):
        for n, story in ENGINE_SCENARIOS.items():
            with self.subTest(scenario=n):
                value = ENGINES.get(n)
                self.assertIn(value, ENGINE_OPTIONS, f"scenario {n}: answer one of {ENGINE_OPTIONS}, not {value!r}")
                self.assertHashed(value, f"w05-ex10-{n}", ENGINE_DIGESTS[n],
                                  f"scenario {n} ({story}): {value!r} is not right — what shape is the data and "
                                  "what is the service's job?")


if __name__ == "__main__":
    run()
````

### `week_05_databases_and_caching/practice/solutions.py`

````python
"""Reference solutions for week 05.

Drills 01, 02, 06 and 07: the course's reference models ARE the solution — read _harness/awslib/dynamo.py,
caching.py and dbmath.py and compare them with yours.
"""
from _harness.awslib.caching import simulate  # noqa: F401
from _harness.awslib.dbmath import needs_proxy, peak_concurrency, proxy_pool_size  # noqa: F401
from _harness.awslib.dynamo import (  # noqa: F401
    break_even_utilisation, monthly_cost_on_demand, monthly_cost_provisioned,
    provisioned_capacity, read_units, write_units,
)

# ── Drill 03: one table, every question ──
TABLE = {
    "KeySchema": [{"AttributeName": "pk", "KeyType": "HASH"}, {"AttributeName": "sk", "KeyType": "RANGE"}],
    "AttributeDefinitions": [{"AttributeName": n, "AttributeType": "S"} for n in ("pk", "sk", "gsi1pk", "gsi1sk")],
    "GlobalSecondaryIndexes": [{
        "IndexName": "owner-index",
        "KeySchema": [{"AttributeName": "gsi1pk", "KeyType": "HASH"}, {"AttributeName": "gsi1sk", "KeyType": "RANGE"}],
        "Projection": {"ProjectionType": "ALL"},
    }],
}


def link_item(code, url, owner, created):
    return {"pk": f"LINK#{code}", "sk": "META", "code": code, "url": url, "owner": owner, "created": created,
            "gsi1pk": f"OWNER#{owner}", "gsi1sk": created}


def click_item(code, day, count):
    return {"pk": f"LINK#{code}", "sk": f"DAY#{day}", "day": day, "count": count}


def get_link(table, code):
    item = table.get_item(Key={"pk": f"LINK#{code}", "sk": "META"}).get("Item")
    return None if item is None else {"code": item["code"], "url": item["url"], "owner": item["owner"]}


def clicks_between(table, code, first_day, last_day):
    result = table.query(KeyConditionExpression=Key("pk").eq(f"LINK#{code}") & Key("sk").between(f"DAY#{first_day}", f"DAY#{last_day}"))
    return [(item["day"], int(item["count"])) for item in result["Items"]]


def links_of_owner(table, owner):
    result = table.query(IndexName="owner-index", KeyConditionExpression=Key("gsi1pk").eq(f"OWNER#{owner}"),
                         ScanIndexForward=False)
    return [item["code"] for item in result["Items"]]


# ── Drill 04: never lose an update ──
class StaleVersion(Exception):
    """The item changed since you read it."""


def rename_link(table, code, new_url, expected_version):
    try:
        got = table.update_item(
            Key={"pk": f"LINK#{code}"}, UpdateExpression="SET #u = :u, #v = :next",
            ConditionExpression="#v = :expected", ExpressionAttributeNames={"#u": "url", "#v": "version"},
            ExpressionAttributeValues={":u": new_url, ":next": expected_version + 1, ":expected": expected_version},
            ReturnValues="ALL_NEW")
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise StaleVersion(f"link {code} is no longer at version {expected_version}") from exc
        raise
    return int(got["Attributes"]["version"])


def transfer_owner(client, code, old_owner, new_owner):
    if old_owner == new_owner:
        raise ValueError("old and new owner are the same")

    def key(pk):
        return {"pk": {"S": pk}}

    client.transact_write_items(TransactItems=[
        {"Update": {"TableName": TABLE_NAME, "Key": key(f"LINK#{code}"),
                    "UpdateExpression": "SET #o = :new ADD #v :one", "ConditionExpression": "#o = :old",
                    "ExpressionAttributeNames": {"#o": "owner", "#v": "version"},
                    "ExpressionAttributeValues": {":new": {"S": new_owner}, ":old": {"S": old_owner}, ":one": {"N": "1"}}}},
        {"Update": {"TableName": TABLE_NAME, "Key": key(f"OWNER#{old_owner}"),
                    "UpdateExpression": "ADD link_count :minus", "ExpressionAttributeValues": {":minus": {"N": "-1"}}}},
        {"Update": {"TableName": TABLE_NAME, "Key": key(f"OWNER#{new_owner}"),
                    "UpdateExpression": "ADD link_count :one", "ExpressionAttributeValues": {":one": {"N": "1"}}}},
    ])


# ── Drill 05: keep it tidy, keep it safe ──
def protect_table(client, table_name, ttl_attribute):
    client.update_time_to_live(TableName=table_name,
                               TimeToLiveSpecification={"Enabled": True, "AttributeName": ttl_attribute})
    client.update_continuous_backups(TableName=table_name,
                                     PointInTimeRecoverySpecification={"PointInTimeRecoveryEnabled": True})
    return client.create_backup(TableName=table_name, BackupName=f"{table_name}-baseline")["BackupDetails"]["BackupArn"]


# ── Drill 08: a database that fails over ──
def create_primary(rds, subnet_group, sg_id):
    rds.create_db_instance(
        DBInstanceIdentifier="shortly-db", Engine="postgres", EngineVersion="17.4", DBInstanceClass="db.t4g.micro",
        AllocatedStorage=20, StorageType="gp3", MultiAZ=True, StorageEncrypted=True,
        MasterUsername="shortly_admin", ManageMasterUserPassword=True,
        BackupRetentionPeriod=7, DeletionProtection=True, PubliclyAccessible=False,
        DBSubnetGroupName=subnet_group, VpcSecurityGroupIds=[sg_id])
    return "shortly-db"


def add_replica(rds, primary_id):
    rds.create_db_instance_read_replica(DBInstanceIdentifier="shortly-db-replica",
                                        SourceDBInstanceIdentifier=primary_id, DBInstanceClass="db.t4g.micro")
    return "shortly-db-replica"


def take_snapshot(rds, db_id):
    snapshot_id = f"{db_id}-baseline"
    rds.create_db_snapshot(DBSnapshotIdentifier=snapshot_id, DBInstanceIdentifier=db_id)
    return snapshot_id


# ── Drills 09 and 10: decide ──
CHOICES = {1: "multi-az instance", 2: "read replica", 3: "aurora replica", 4: "aurora global database",
           5: "multi-az cluster", 6: "cross-region read replica", 7: "rds proxy"}
ENGINES = {1: "rds", 2: "aurora", 3: "dynamodb", 4: "elasticache", 5: "documentdb", 6: "neptune",
           7: "keyspaces", 8: "opensearch", 9: "memorydb"}
````

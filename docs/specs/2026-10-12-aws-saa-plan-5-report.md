# Plan 5 report — week 05 (Databases and caching) and milestone M05

Plan: `docs/specs/2026-10-12-aws-saa-plan-5-week-05.md`. Built 2026-10-12, together with plan 4 (week 04) in one scratch copy (ruling P4-1). No commits (the learner commits at the end).

## What was built

| Area | Files | Size |
|---|---|---|
| Research | `docs/research/2026-10-12-database-facts.md` (official AWS pages and the AWS Price List files), `docs/research/2026-10-12-moto-database-spike.md` | 440 table rows; spike sections A–F |
| Facts of record | `docs/facts.md`: "Databases and caching (week 05)" (RDS, Aurora, DynamoDB, DAX, ElastiCache, purpose-built databases) and its prices; Timestream for LiveAnalytics added to the retired table | rows 1212 → 1645 |
| Reference models | `_harness/awslib/dynamo.py` (read and write units, provisioned capacity, on-demand vs provisioned cost and break-even), `caching.py` (lazy loading vs write-through with TTL), `dbmath.py` (Lambda-style concurrency vs `max_connections`, RDS Proxy sizing), `prices.toml [database]` | answer keys for drills 01, 02, 06 and 07, reused by M05's tests |
| Tooling | `cfn.py` (`for_moto`: strips the types moto skips and replaces unsupported GetAtts), `labclean.py` (DynamoDB tables and backups, RDS instances and snapshots, DB subnet groups), `conftest.py` (`dynamo` fixture; `moto_stacks` is `deploy(layer, skip_types=(), getatt_values=None, **params)`), `start_milestone.py` (copies the new models) | — |
| Maintainer tests | `_dev/tests/test_database_models.py` + changes to `test_cfn_intrinsics.py`, `test_milestone_tools.py` (the labclean tests are shared with plan 4); mutants `_dev/mutants/week05.py`, `m05.py` | 581 tests pass (plans 4 and 5) |
| Drills | `week_05_databases_and_caching/practice/exercises.py` + hidden `solutions.py` | 10 drills (4 ★), 12 mutants |
| Concept notes | `concepts/01 … 05` (RDS; Aurora; DynamoDB; caching with ElastiCache and DAX; choosing a database) | 156–201 lines each |
| Demos | `demo_dynamodb_in_moto.py` (an orders table: partition and sort key, a GSI, a failed conditional put, a cancelled transaction, key-range and GSI queries); `demo_database_math.py` (capacity units, on-demand vs provisioned and the break-even, one event stream through lazy loading and write-through) | both exit 0 piped |
| Week README, lab | `README.md` (goals, service comparison, interview questions), `lab/LAB.md` (an on-demand DynamoDB table, then a Single-AZ `db.t4g.micro` PostgreSQL instance with a managed master secret; cents), `lab/cleanup.py` (`dynamodb_tables`, `dynamodb_backups`, `rds_instances`, `rds_snapshots`, `db_subnet_groups`) | — |
| Quiz | `quiz/questions.toml` | 30 questions: 27 single, 3 Select TWO |
| Milestone M05 | `course_project/milestones/M05.md`, tests `course_project/tests/m05/` (6 steps), solution `course_project/solutions/m05/` (`infra/data.yaml`: RDS PostgreSQL 17 with a managed master password, prod Multi-AZ with 7-day backups and deletion protection; the app role's access to the RDS-managed secret; a Valkey replication group, two nodes with failover in prod; the `shortly-clicks-daily` on-demand table with PITR and TTL; README "## Data tier" with the clicks table's monthly cost, 22.50 USD) | 196-line spec; 37 test functions; 28 mutants |
| Project and course docs | `course_project/README.md`, `DEPLOY.md` (data stack with `CAPABILITY_IAM`, cost row, retained snapshot and table, delete order), `README.md`, `COURSE_FLOW.md`, `COVERAGE.md` | — |

## Verification (main session, real course)

- `_dev/tests`: 581 passed. `verify_course.py --self-test`: ✔ (re-run after the `for_moto` cleanup, with the tests: 581 passed).
- Week 05 drills: stubs 0/10, solutions 10/10, all 12 mutants caught.
- `verify_course.py --week 5`: 40/40.
- `--milestone 5` 32/32: the reference solution passes in lab and prod, the M04 starting state fails, all 28 mutants are caught, and every template is cfn-lint clean. `--milestone 1` … `--milestone 4` still pass (10/10, 14/14, 18/18, 24/24).
- The full run, `verify_course.py --coverage`: 333/333. Week 05 gives tasks 3.3 and 4.3 their first coverage.
- Reviews and fixes:
  - **Models and drills:** I read every model against `docs/facts.md`. Each decide scenario in drills 09 and 10 has one best answer. Drill 10 drops Timestream, because Timestream for LiveAnalytics is closed to new customers. Drill 09 says "replication in under a second" rather than an RPO number, because facts.md gives the Global Database RPO only as "measured in seconds".
  - **Content:** I read every note, the lab, the demos and M05.md against `docs/facts.md`. Fixes:
    - a note named the old DynamoDB transaction limit, which the research could not confirm; only today's 100 items / 4 MB stays;
    - a table row with no source in facts.md was removed;
    - Multi-AZ failover is "typically 60 to 120 seconds", not "about a minute";
    - the lab's cleanup order;
    - the project README's M05 row says Valkey, the engine the milestone uses.
  - **M05.md:** every logical id, value and `!If` pair matches the tests. The README workload is stated exactly as the test states it. I confirmed with cfn-lint 1.57.2 that a one-node replication group with failover switched on passes lint, as the hint says, so the test is what catches it.
  - **Tooling:** `cfn.for_moto` accepted `params` and `pseudo` and never used them; both were removed, and the tests, `--self-test` and `--milestone 5` were re-run.
  - **M05 solution:** the solution README's "Check it" command said `run_milestone.py 4`; fixed to 5 before install.

## Blind solve (quiz)

- An independent Opus solver, working only from the exported stems and options, matched the answer key on 30/30.
- It raised seven doubts:
  - q02 was ambiguous between a Multi-AZ DB instance and a Multi-AZ DB cluster;
  - q04, q06, q07, q12, q28 and q29 were giveaways, because the correct option echoed the stem;
  - q26 relied on an unsourced claim, which was removed.
- All were rewritten. The research agent added the DAX and ElastiCache microsecond-latency rows to facts.md for the rewrites. A fresh Opus solver answered the rewritten questions: matched, nothing flagged.

## Rulings

- P4-1 (shared): weeks 04 and 05 were built together.
- P5-1: M05's deploy test strips the ElastiCache and Secrets Manager types and replaces the `MasterUserSecret` GetAtt before `create_stack` (`cfn.for_moto`). Moto skips those types and crashes on their GetAtts.
- Planning rulings (in the plan):
  - the app role reads its database secret through `AppDbSecretPolicy` in the data stack, scoped to the one secret, because RDS names it `rds!db-…` and M01's `shortly/db-*` statement does not match it;
  - prod is `db.m7g.large` Multi-AZ, 7-day backups and deletion protection, with a two-node cache and failover; lab is `db.t4g.micro` Single-AZ, 1-day backups and one cache node;
  - the cache engine is Valkey (cfn-lint 1.57.2 accepts it, and it costs 80 % of Redis OSS per node); the test also accepts `redis`.

## Known limits

- Moto enforces DynamoDB conditions and transactions and RDS deletion protection. It never expires TTL items, reports constant consumed capacity and has no Multi-AZ standby. Its CloudFormation skips ElastiCache, Secrets Manager, Aurora clusters and global tables, and drops `ManageMasterUserPassword`, `DeletionProtection`, `VPCSecurityGroups`, PITR, TTL and table encryption. So M05's tests read the rendered template, and the deploy test proves only what moto really creates.
- The models are teaching models. `dynamo` ignores the 25 free provisioned units. `caching` uses one TTL for every key. `dbmath` needs the proxy's `MaxConnectionsPercent` given, because the research found no default.
- Prices are illustrative. No question depends on a live price or on a "changed" row. QLDB, Aurora Serverless v1 and Timestream for LiveAnalytics appear only on "retired" lines.
- The lab and `cleanup.py` target a real account and were never run here. Cleanup is a dry run unless `--yes`, and it touches only `saa-course=lab` resources. It switches off deletion protection only on tagged resources, deletes read replicas before their source, and leaves a tagged source alone when an untagged replica would be promoted. Cross-Region replicas, global-table replicas, Aurora clusters and AWS Backup-managed DynamoDB backups are not covered.

## What to try first

1. `python week_05_databases_and_caching/concepts/demo_database_math.py`, then note 03 and drills 01–03.
2. Notes 01, 02, 04 and 05 with drills 04–10 (drills 01, 02, 06 and 07 are the models, 03–05 and 08 boto3, 09–10 decide).
3. Quiz: `python quiz.py --week 5 -n 30`.
4. M05: `python course_project/tools/start_milestone.py 5 --repo ~/code/shortly-infra`, then `run_milestone.py 5` in your repo.
5. The optional lab, a DynamoDB table and a Single-AZ PostgreSQL instance. Delete them the same day and run `cleanup.py --yes`.

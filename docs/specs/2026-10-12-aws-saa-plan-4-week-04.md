# AWS SAA Course — Plan 4: Week 04 (Storage) + M04 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build week 04 — storage — in the shape of weeks 01–03: 5 concept notes, 2 demos, 10 drills (4 ★), a 30-question quiz, a real-AWS lab with a safe cleanup, and capstone milestone M04 (the `storage` stack: an assets bucket and a logs bucket, their policies and lifecycle rules), plus the library pieces the drills and tests need.

**Architecture:** Drills 01–04 are pure-Python models whose answer keys live in three new modules: `_harness/awslib/s3cost.py` (storage-class cost with minimum duration, minimum billable size and retrieval fees; multipart planning; prefixes for a request rate), `lifecycle.py` (lifecycle-rule validation — waterfall, two-step minimum, tag-filter limits — and a replay of where an object or noncurrent version is after N days) and `ebs.py` (gp2/gp3/io2 limits and cost, choosing a volume type). Drills 05–09 run boto3 against moto. moto keeps a bucket's API state but its CloudFormation drops almost every bucket setting (versioning, Block Public Access, lifecycle, ownership) and skips bucket policies; its bucket-policy enforcement ignores Condition and Principal (spike: `docs/research/2026-10-12-moto-storage-spike.md`). So M04's tests read the rendered template and decide policies with the course's evaluator (`policy_eval.decide_resource_policy`, new) and lifecycle with the `lifecycle` model; moto only proves the stacks deploy and the buckets exist with their encryption. `labclean` learns EBS volumes and snapshots and aborts unfinished multipart uploads. This plan was built together with plan 5 (week 05) in one scratch copy; all code was written and verified there before installation (Task 1).

**Tech Stack:** as plans 1–3 (Python 3.14.2, moto 5.2.3, boto3 1.43.109, cfn-lint 1.57.2, pytest 9.1.1). No new packages.

**Spec:** `docs/specs/2026-10-08-aws-saa-course-design.md` §4.0–§4.5 (week 04 row, drill row 04, M04 row). Facts: `docs/research/2026-10-12-storage-facts.md` (official sources, read 2026-10-12). moto spike: `docs/research/2026-10-12-moto-storage-spike.md`. Previous plans 1–3 (their Global Constraints still apply). Companion: `docs/specs/2026-10-12-aws-saa-plan-5-week-05.md`.

**Execution (learner's instruction, 2026-10-12: "plan and execute week 4 and week 5, use as many subagents as you want"):** research and moto-spike agents first; design documents; Sonnet implementers in parallel in one scratch copy with one owner per file (shared files: `prices.toml` append-only, `labclean.py` one owner, `conftest.py`/`start_milestone.py`/`cfn.py` M04 then M05, `docs/facts.md` week 04 then week 05); the main session verifies every task itself (runs the commands, reads every model, drill file, note and milestone against `docs/facts.md`, blind-solves each quiz with an independent Opus agent and re-solves rewritten questions with a fresh one). No git, no commits.

## Global Constraints

- Everything in plan 1's Global Constraints and plans 2–3's (quiz style ruling 8; services from later weeks may appear in questions; numbers only from `docs/facts.md`; "changed" rows taught at today's value with the old value named once, never hinging a question).
- **Exam vs 2026 reality:** teach today's values (S3 object size 50 TB, bucket quota 10,000, SSE-C off by default since April 2026, the 128 KB lifecycle default since September 2024, gp3 maxima 80,000 IOPS / 2,000 MiB/s, Elastic Volumes four changes per 24 hours, io2 is all Block Express). The "30 days before Standard-IA" transition rule is NOT taught as a number (the research could not confirm it on an official page); the two-step minimum rule is. S3 Select and the original Glacier vault service are "retired" (facts.md Rule 1); FSx File Gateway is closed to new customers ("retired for new customers"); Snowball Edge is Rule 2 (legacy, exam answer with a status note).
- **Lab cost:** cents (a versioned bucket, an unattached gp3 volume of at most 8 GiB, two snapshots); every resource tagged `saa-course=lab`.

## Review Focus

1. **Cleanup must never touch an untagged instance's disk**, never detach a tagged instance's root disk, and must abort unfinished multipart uploads before deleting a tagged bucket. Tests: `_dev/tests/test_labclean_storage_db.py`.
2. **Bucket policies are decided by the evaluator, not by moto** (moto ignores Condition and Principal and its CloudFormation skips bucket policies). Tests: `test_m04_2_assets_policy.py`, `test_m04_4_logs_bucket.py`; mutants `http-allowed`, `public-read`, `elb-anywhere`.
3. **Lifecycle rules are validated and replayed by the model**, because moto neither validates nor runs them. Tests: `test_m04_3_*.py`, `test_m04_4_*.py`; mutants `ia-after-glacier`, `logs-never-expire`, `noncurrent-forever`.
4. **Drills never open a presigned URL** (urllib is not intercepted by moto and would reach the real network). Drill 06 checks the URL's parts only.
5. **M01–M03 keep passing** after `start_milestone.py 4` overwrites the course-owned files. Test: `run_milestone.py 4` is cumulative.

## Files this plan creates or changes

```
_harness/awslib/s3cost.py · lifecycle.py · ebs.py   (new: week 04 drills 01–04 answer keys)
_harness/awslib/cfn.py             (changed: Fn::FindInMap; render takes the template's Mappings)
_harness/awslib/policy_eval.py     (changed: decide_resource_policy for service principals)
_harness/awslib/prices.toml        (changed: [storage] section)
_harness/labclean.py               (changed: ebs_volumes and ebs_snapshots finders, Blocked; a tagged bucket's unfinished multipart uploads are aborted and Object Lock is reported — one owner for weeks 04 and 05)
_dev/tests/test_storage_models.py · test_labclean_storage_db.py   (new; the labclean tests cover both weeks)
_dev/tests/test_cfn_intrinsics.py · test_policy_eval.py · test_milestone_tools.py · test_labclean_compute.py   (changed)
_dev/mutants/week04.py · m04.py    (new)
course_project/tools/conftest.py · start_milestone.py   (changed: lifecycle fixture; copies s3cost, lifecycle, ebs)
course_project/tests/m04/test_m04_{1..5}_*.py   (new)
course_project/solutions/m04/{infra/storage.yaml, README.md; the M03 files unchanged}   (new)
course_project/milestones/M04.md · course_project/README.md · DEPLOY.md   (new / changed)
docs/facts.md                      (changed: storage section, storage prices)
week_04_storage/README.md · concepts/01..05_*.md · concepts/demo_*.py (2) · practice/exercises.py · practice/solutions.py · quiz/questions.toml · lab/LAB.md · lab/cleanup.py   (new)
README.md · COURSE_FLOW.md · COVERAGE.md · docs/specs/2026-10-12-aws-saa-plan-4-report.md   (changed / new)
```

## Rulings made while planning (spec deviations and choices)

- **Weeks 04 and 05 are planned and built together** (P4-1): one scratch copy, one owner per file; shared files have a fixed order. Cost if wrong: a merge conflict, caught by the main-session diff before install.
- **No "30 days before Standard-IA" rule in the lifecycle model or the course** (P4-4): the research could not confirm it on the official lifecycle pages; the two-step minimum rule, which they state, is enforced instead. Quiz q07 was rewritten so it does not depend on either.
- **Drill 05 returns the TLS-only policy instead of putting it; drill 06 never opens the presigned URL; drill 07 avoids a GET on a delete-marker version id and suspended versioning** (P4-3): moto enforces bucket-policy Denies crudely, does not intercept urllib, answers 404 where S3 answers 405, and mishandles suspended versioning.
- **The assets bucket uses SSE-KMS with the AWS managed key and a Bucket Key** (a customer managed key arrives with KMS in week 08); **the logs bucket uses SSE-S3**, the only encryption ALB access logs support.
- **ALB log delivery uses the service principal** `logdelivery.elasticloadbalancing.amazonaws.com` (AWS's recommended form); the legacy us-east-1 account id is mentioned, not required. The compute stack is not changed to enable access logs (it would make M03's deploy test depend on the storage stack).
- **Lab log expiry is 365 days (prod 730)**, not 30: expiry must come after the last transition (Deep Archive at day 180) and Deep Archive bills a 180-day minimum.
- **policy_eval gains `decide_resource_policy`** for service principals that have no account (log delivery, CloudFront).

## Waves (plans 4 and 5 together)

| Wave | Work | Needs |
|---|---|---|
| 0 | research ×2, moto spikes ×2 | — |
| A | storage and database models (scratch) + facts week 04 then week 05 (real course) | research |
| B | drills ×2, M04, labclean (scratch); notes ×2 and quizzes ×2 (real course, models installed first) | A, spikes |
| C | M05 (scratch, after M04); M04.md; blind solves | B |
| D | install the bundle (Task 1), M05.md, docs, full verification, reports | C |

---

### Task 1: Install the verified code bundle

**Files:** every file in Appendix A of plan 5 (the joint bundle for weeks 04 and 05), exactly as given.

- [ ] **Step 1:** Write every Appendix A file (plan 5) with exactly the content shown; replace files that exist.
- [ ] **Step 2:** `.venv/Scripts/python.exe -m pytest _dev/tests -o addopts="" -p no:cacheprovider -q` → all passed.
- [ ] **Step 3:** `week_04_storage/practice/exercises.py` 0/10, `--solutions` 10/10; `verify_course.py --week 4` all ✔; `--milestone 1` … `--milestone 4` all ✔.

---

### Task 2: Storage facts in `docs/facts.md`

**Files:** Modify `docs/facts.md`.

- [ ] **Step 1:** Add a section `## Storage (week 04)` after the "Compute and scaling (week 03)" section, built from `docs/research/2026-10-12-storage-facts.md` sections 1–11, subsections: S3 basics · S3 storage classes · S3 lifecycle · Versioning, Object Lock and replication · S3 security · S3 performance and transfer · EBS · EFS · FSx · Storage Gateway · Other storage services. Keep every **confirmed** row that a week 04 note or question could need. Keep the `Fact | Value | Changed? | Source` columns and the research's sources, with a source key line at the top like the week 03 section. Rows the research lists as unconfirmed are NOT added; append them, condensed, to the existing "Not confirmed" line. Where the research corrects a row in the older "## Numbers to know" table (gp3, S3 object size, minimum durations, Glacier retrievals), leave the old table alone and make sure the new section carries the current value.
- [ ] **Step 2:** Add `### Storage (week 04)` to `## Prices used in drills (illustrative, us-east-1)` with every `prices.toml [storage]` value and its research row (S3 per class, retrievals, EBS, snapshots, EFS). Rows of medium confidence (EBS prices from worked examples; the Deep Archive price page names no Region) say so in the value.
- [ ] **Step 3:** `grep -c "^| " docs/facts.md` grows by at least 150; `verify_course.py --banks | grep retired` stays ✔ (a retired or retired-for-new-customers service — S3 Select, the original Glacier vault service, FSx File Gateway if the research says it closed — appears only on a line containing the word "retired").

---

### Task 3: Week 04 concept notes, demos, README and lab

**Files:** Create in `week_04_storage/`: `concepts/01_s3_fundamentals_and_classes.md`, `concepts/02_s3_lifecycle_versioning_replication.md`, `concepts/03_s3_security.md`, `concepts/04_ebs_instance_store_efs.md`, `concepts/05_fsx_gateway_and_choosing.md`, `concepts/demo_s3_in_moto.py`, `concepts/demo_storage_costs.py`, `README.md`, `lab/LAB.md`, `lab/cleanup.py`.

**Writing rules:** plan 1 Task 12's rules (first line `Exam tasks: …`; sections What it is / How it works / Numbers to know / When to choose it / Exam traps / Cost angle / Comparison; 150–300 lines; numbers only from `docs/facts.md`; plain English). Do **not** reveal drill 07's or drill 10's answers or paste drill solutions; teach the rules with other examples. Teach today's values for every "changed" row (name the old value once).

| File | Exam tasks line | Must cover |
|---|---|---|
| `01_s3_fundamentals_and_classes.md` | `Exam tasks: 3.1, 4.1` | buckets, objects, keys and prefixes; global names, bucket quota (changed); durability and availability by class; strong consistency; object size limit (changed) and single PUT vs multipart; request rates per prefix (drill 04); every storage class with minimum duration, minimum billable size, retrieval fee and AZs (table); Glacier retrieval options and times; Intelligent-Tiering (tiers, monitoring fee, 128 KB); Express One Zone and directory buckets one paragraph; storage-class cost reasoning (drill 01); comparison table of classes |
| `02_s3_lifecycle_versioning_replication.md` | `Exam tasks: 4.1, 1.3, 2.2` | lifecycle actions (transition, expiration, noncurrent, expired delete markers, abort multipart); the waterfall; the two-step minimum rule; the 128 KB default (changed); filters; asynchronous timing (drill 02); versioning states, delete markers and what GET/LIST/version calls show (teach with your own examples, not drill 07's), MFA delete; Object Lock modes, retention and legal hold; replication CRR/SRR, requirements (versioning on both, a role), existing objects (Batch Replication), the delete-marker option, RTC; comparison table of data-protection features |
| `03_s3_security.md` | `Exam tasks: 1.3, 1.2` | the access stack: IAM policies, bucket policies, Block Public Access (account and bucket, defaults changed), Object Ownership and ACLs disabled; useful bucket-policy conditions (aws:SecureTransport, aws:SourceVpce from week 02, aws:SourceArn for CloudFront OAC); encryption: SSE-S3 default (changed), SSE-KMS and Bucket Keys, DSSE-KMS, SSE-C (changed 2026), client-side; presigned URLs and their expiry limit; access points; CloudFront OAC vs legacy OAI; the ALB access-log bucket policy (service principal, SSE-S3 only); comparison table of encryption options |
| `04_ebs_instance_store_efs.md` | `Exam tasks: 3.1, 4.1, 2.2` | EBS: AZ scope, volume types table (gp3, gp2, io2 Block Express, io1, st1, sc1) with IOPS/throughput/size and boot, gp2 3 IOPS per GiB, gp3 baseline and the changed maxima, IOPS/throughput maths (drill 03), Multi-Attach, Elastic Volumes (changed frequency), snapshots (incremental, cross-Region copy, encrypting an unencrypted volume through a copy, Fast Snapshot Restore, archive tier, Recycle Bin, DLM); instance store recap (week 03); EFS: NFS, Linux, Regional vs One Zone, mount targets, storage classes and lifecycle, throughput and performance modes, cost vs EBS; comparison table EBS / instance store / EFS |
| `05_fsx_gateway_and_choosing.md` | `Exam tasks: 3.1, 4.1` | FSx for Windows File Server, Lustre (scratch vs persistent, S3 link), NetApp ONTAP, OpenZFS — when each; Storage Gateway types (S3 File, Volume cached vs stored, Tape; FSx File Gateway status from facts.md on a line containing "retired" if it is closed to new customers); S3 performance: Transfer Acceleration, byte-range fetches, multipart, prefixes (drill 04); DataSync, Transfer Family and AWS Backup one line each (later weeks); Snow family status (legacy, facts.md Rule 2); the big decision table (drill 10's topic, your own scenarios) |

- [ ] **Step 1: Write the five notes** per the table.
- [ ] **Step 2: `concepts/demo_s3_in_moto.py`** — offline moto demo in the week 03 demo style: a versioned bucket with SSE-KMS default encryption; put two versions, delete, show list_object_versions (versions + delete marker), get an old version by id, remove the delete marker and show the object is back; put a lifecycle configuration and read it back; then print plainly what moto does NOT do (lifecycle never runs, replication never copies, bucket-policy Conditions are ignored, CloudFormation drops most bucket settings) — "that is why drills 01–04 are models". Use only behaviours `docs/research/2026-10-12-moto-storage-spike.md` marks as matching real S3; never open a presigned URL. Ends with "Now do drills 05–09." Exit 0 piped.
- [ ] **Step 3: `concepts/demo_storage_costs.py`** — pure Python with `s3cost`, `lifecycle`, `ebs`: one dataset priced in every class for two access patterns (table); a log object's journey under a lifecycle rule by day; gp2 vs gp3 for the same size and IOPS; a multipart plan for a big file. Different numbers from the drills' examples. Ends with "Now do drills 01–04 and 10." Exit 0 piped.
- [ ] **Step 4: `README.md`** — headings as weeks 00–03. Goals (6): choose an S3 storage class and predict its cost; design lifecycle and versioning rules; protect data with versioning, Object Lock and replication; secure a bucket (BPA, policies, encryption, presigned URLs); choose and size block storage (EBS, instance store); choose a file or hybrid storage service (EFS, FSx, Storage Gateway). Your week (≈ 10–12 h, same split as week 03, quiz `python quiz.py --week 4 -n 30`, milestone M04). Exam tasks covered: 1.3, 2.2, 3.1, 4.1. Service comparison table: S3 / EBS / instance store / EFS / FSx / Storage Gateway. Interview questions (10). Final line: "Now you may read `_harness/awslib/s3cost.py`, `lifecycle.py` and `ebs.py` — compare them with your drills 01–04."
- [ ] **Step 5: `lab/LAB.md` and `lab/cleanup.py`** — LAB (≈ 60 min; cost a few cents): 1 before you start (guard rails, profile `saa-lab`, one Region, tag EVERYTHING `saa-course=lab`); 2 an S3 bucket: versioning on, check the default encryption, Block Public Access settings and Object Ownership; upload a file twice, delete it, find the delete marker and the old version, restore it (CLI commands given); 3 a lifecycle rule (current versions to Standard-IA, noncurrent expire, abort incomplete multipart uploads) and read it back — it runs asynchronously, nothing moves today; 4 a presigned URL with `aws s3 presign` for 300 seconds, open it, wait, see it expire; 5 EBS: create an unattached 1 GiB gp3 volume (tagged), modify it to 2 GiB and 4,000 IOPS (watch the modification state), snapshot it, copy the snapshot encrypted, look at the snapshot sizes; 6 clean up: `python lab/cleanup.py --profile saa-lab` then `--yes`; 7 what to write down. `cleanup.py` = week 03's pattern with `kinds=["s3_buckets", "ebs_snapshots", "ebs_volumes"]` and a docstring naming them.
- [ ] **Step 6: Verify** — demos exit 0 piped; `verify_course.py --week 4 2>&1 | grep -E "concept|demo|README|lab"` all ✔ (the lab line may show ✘ until the code bundle with the new cleanup kinds is installed — report it); `verify_course.py --banks | grep retired` ✔.

---

### Task 4: Week 04 quiz (30 questions) + blind solve

**Files:** Create `week_04_storage/quiz/questions.toml`.

- [ ] **Step 1: Write the 30 questions** (quiz rules, ruling 8; ids `w04-q01 … w04-q30`; 3–6 Select TWO; refs = Task 3's five notes):

| ids | domain · task | topics (one question each, in order) |
|---|---|---|
| q01–q08 | 4 · 4.1 / 3 · 3.1 | Standard-IA for data read monthly that needs millisecond access · One Zone-IA for re-creatable copies · Glacier Instant Retrieval for quarterly reads in milliseconds · Deep Archive for 7-year compliance archives retrieved within 48 hours · Glacier Flexible bulk retrieval as the cheapest way to restore a large archive (works-but-costs-more option: expedited) · Intelligent-Tiering for unknown or changing access patterns · deleting IA objects after 10 days still bills the minimum duration · millions of 20 KB objects: the minimum billable size makes IA a bad choice |
| q09–q14 | 4 · 4.1 / 1 · 1.3 | lifecycle for logs: IA then Glacier then expire · noncurrent-version expiration to stop versioning costs growing (keep N versions) · restoring an accidentally deleted object in a versioned bucket (remove the delete marker) · WORM retention for regulators: Object Lock compliance mode · governance vs compliance mode for admins who may need to shorten retention · abort incomplete multipart uploads to stop paying for orphaned parts |
| q15–q18 | 2 · 2.2 | cross-Region replication for DR (Select TWO: versioning on both buckets; an IAM role / replication rule) · Replication Time Control for a 15-minute replication target · copying the objects that existed before replication was enabled (Batch Replication) · same-Region replication to aggregate logs into one account |
| q19–q23 | 1 · 1.3 | prevent any bucket in the account from becoming public (account-level Block Public Access) · enforce HTTPS with a bucket policy (aws:SecureTransport) · cut KMS request costs on a busy SSE-KMS bucket (S3 Bucket Keys) · temporary download link for a private object (presigned URL) · keep a bucket private behind CloudFront (Select TWO: OAC; bucket policy allowing only that distribution) |
| q24–q26 | 3 · 3.1 | faster uploads of 5 GB files over a good link (multipart, parallel parts) · users on another continent uploading to one bucket (Transfer Acceleration) · a workload above one prefix's request rate (spread keys over prefixes) |
| q27–q30 | 3 · 3.1 / 4 · 4.1 | gp2 → gp3 for the same IOPS at lower cost (MOST cost-effective; works-but-costs-more: io2) · a clustered app needing a shared block volume in one AZ (io2 Multi-Attach) · shared POSIX files for Linux instances in three AZs (EFS) vs Windows SMB with Active Directory (FSx for Windows) — pick one scenario per question: make q29 EFS and q30 a hybrid on-premises file share backed by S3 with a local cache (S3 File Gateway) |

- [ ] **Step 2: Validate** — `verify_course.py --week 4 2>&1 | grep -i quiz` all ✔; `verify_course.py --banks | tail -6` no near-duplicates.
- [ ] **Step 3: Blind solve (main session)** — export with `_dev/blindsolve.py export`, an independent Opus agent answers from the blind file only and lists doubts, `compare`; fix every disagreement and real doubt through the implementer; a fresh Opus agent re-solves the rewritten questions.

---

### Task 5: M04 spec and project docs

**Files:** Create `course_project/milestones/M04.md`; modify `course_project/README.md`, `course_project/DEPLOY.md`.

- [ ] **Step 1: `M04.md`** — same shape as M03.md, matching `course_project/tests/m04/` exactly: intro (the storage layer: an assets bucket for user uploads and a logs bucket for load balancer access logs; storage costs money only for what is stored — tiny for a test); Step 0 (`start_milestone.py 4`, `run_milestone.py 4`, cumulative); What the tests rely on (file `infra/storage.yaml`; parameters; the import of the M01 app role ARN; every logical id; the four exports); M04.1–M04.5 in plain words (assets bucket settings; the assets bucket policy and how the tests evaluate it with the course's policy evaluator; noncurrent-version expiry and aborting unfinished uploads, replayed with the lifecycle model; the logs bucket: SSE-S3 only, tiers by age, lab and prod expiry, the log-delivery principal; exports, lint and the moto deploy); YAML examples allowed: the BucketEncryption block with a Bucket Key, the DenyInsecureTransport statement, and one lifecycle rule — never the whole template; a note that moto's CloudFormation keeps only a bucket's name, tags and encryption (it drops versioning, Block Public Access, lifecycle and the bucket policies), which is why the tests read the template; Done when; Hints (why Bucket Keys; why SSE-S3 on the logs bucket; the two-step lifecycle minimum; NewerNoncurrentVersions needs NoncurrentDays; `${AssetsBucket.Arn}/*` vs the bucket ARN; DeletionPolicy Retain on the assets bucket); Why this matters in the exam.
- [ ] **Step 2: `course_project/README.md`** — M04 built. **`DEPLOY.md`** — the storage stack: deploy after iam (`--stack-name shortly-storage --parameter-overrides Prefix=shortly Env=lab`), the cost row (S3 storage per GB-month, illustrative; tiny for a test), delete order note (the assets bucket has DeletionPolicy Retain: CloudFormation leaves it, empty and delete it by hand; delete shortly-storage before shortly-iam).

---

### Task 6: Course docs, full verification, report

**Files:** Modify `README.md` (week 04 row links to its README), `COURSE_FLOW.md` (week 04 section like week 03's, `start_milestone.py 4`, `run_milestone.py 4`); generate `COVERAGE.md`; create `docs/specs/2026-10-12-aws-saa-plan-4-report.md`. Done together with plan 5's Task 6.

- [ ] **Step 1:** README and COURSE_FLOW edits (weeks 04 and 05 in one pass).
- [ ] **Step 2 (main session):** `verify_course.py --self-test`, `--week 4`, `--milestone 4` and `--coverage`; everything green.
- [ ] **Step 3:** report (what was built with counts; verification; blind-solve results; rulings; known limits; what to try first).

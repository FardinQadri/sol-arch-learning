# Plan 4 report — week 04 (Storage) and milestone M04

Plan: `docs/specs/2026-10-12-aws-saa-plan-4-week-04.md`. Built 2026-10-12, together with plan 5 (week 05) in one scratch copy (ruling P4-1). No commits (the learner commits at the end).

## What was built

| Area | Files | Size |
|---|---|---|
| Research | `docs/research/2026-10-12-storage-facts.md` (official AWS pages), `docs/research/2026-10-12-moto-storage-spike.md` (what moto and cfn-lint really do) | 514 table rows; spike sections A–F |
| Facts of record | `docs/facts.md`: "Storage (week 04)" (11 subsections) and "Storage (week 04)" prices | rows 710 → 1212 |
| Reference models | `_harness/awslib/s3cost.py`, `lifecycle.py`, `ebs.py`, `prices.toml [storage]` | answer keys for drills 01–04, reused by M04's tests |
| Tooling | `cfn.py` (`Fn::FindInMap`), `policy_eval.py` (`decide_resource_policy` for service principals), `labclean.py` (EBS volumes and snapshots; a tagged bucket's unfinished multipart uploads are aborted, Object Lock is reported, `Blocked` for resources left in place on purpose), `conftest.py` (`lifecycle` fixture), `start_milestone.py` (copies the new models) | — |
| Maintainer tests | `_dev/tests/test_storage_models.py`, `test_labclean_storage_db.py` (51 tests, weeks 04 and 05) + changes to `test_cfn_intrinsics.py`, `test_policy_eval.py`, `test_milestone_tools.py`, `test_labclean_compute.py`; mutants `_dev/mutants/week04.py`, `m04.py` | 581 tests pass (plans 4 and 5) |
| Drills | `week_04_storage/practice/exercises.py` + hidden `solutions.py` | 10 drills (4 ★), 10 mutants |
| Concept notes | `concepts/01 … 05` (S3 fundamentals and classes; lifecycle, versioning and replication; S3 security; EBS, instance store and EFS; FSx, Storage Gateway and choosing) | 172–210 lines each |
| Demos | `demo_s3_in_moto.py` (versioning, delete markers, SSE-KMS with a Bucket Key, a restore, a stored lifecycle configuration); `demo_storage_costs.py` (one dataset in every class, a log object's lifecycle journey and a rule AWS refuses, gp2 vs gp3) | both exit 0 piped |
| Week README, lab | `README.md` (goals, service comparison, interview questions), `lab/LAB.md` (a versioned bucket, a lifecycle rule, a presigned URL, a gp3 volume grown from 1 to 8 GiB, two snapshots; a few cents), `lab/cleanup.py` (`s3_buckets`, `ebs_snapshots`, `ebs_volumes`) | — |
| Quiz | `quiz/questions.toml` | 30 questions: 27 single, 3 Select TWO |
| Milestone M04 | `course_project/milestones/M04.md`, tests `course_project/tests/m04/` (5 steps), solution `course_project/solutions/m04/` (`infra/storage.yaml`: assets bucket with SSE-KMS + Bucket Key, versioning, Block Public Access, owner-enforced, noncurrent-version and multipart lifecycle, TLS-only and app-upload policy; logs bucket with SSE-S3, a Standard-IA → Glacier IR → Deep Archive → expiry rule and ALB log delivery by service principal) | 185-line spec; 33 test functions; 20 mutants |
| Project and course docs | `course_project/README.md`, `DEPLOY.md` (storage stack, cost row, delete order), `README.md`, `COURSE_FLOW.md`, `COVERAGE.md` | — |

## Verification (main session, real course)

- `_dev/tests`: 581 passed. `verify_course.py --self-test`: ✔.
- Week 04 drills: stubs 0/10, solutions 10/10, all 10 mutants caught.
- `verify_course.py --week 4`: 38/38 (the cleanup kinds check went green once the labclean finders were installed).
- `--milestone 1` 10/10, `--milestone 2` 14/14, `--milestone 3` 18/18, `--milestone 4` 24/24: the reference solution passes, the M03 starting state fails, all 20 mutants are caught, and every template is cfn-lint clean.
- The full run, `verify_course.py --coverage` (every week, every milestone, the banks, content currency): 333/333. Week 04 gives task 3.1 its first coverage and adds most of 4.1.
- Reviews and fixes:
  - **Models and drills:** I read every model against `docs/facts.md`. My lifecycle spec had the expiration timing reversed, and the writer corrected it. The "30 days in Standard before Standard-IA" rule is not confirmed on an official page, so it is not enforced; the stated two-step minimum rule is. Drills 05–07 use only moto behaviours that match real S3 (ruling P4-3).
  - **Lab:** the brief asked for a 2 GiB gp3 volume at 4,000 IOPS, which breaks the 500 IOPS per GiB limit. The writer turned the refusal into a learning step and grows the volume to 8 GiB.
  - **Lab cleanup:** the week 03 FINDERS test asserted the exact old list, so it now checks relative order.
  - **Content:** I read every note, the lab, the demos and M04.md against `docs/facts.md`. Fixes:
    - the durability sentence;
    - the cleanup's multipart wording;
    - M04.md said the logs bucket "receives" ALB logs, but access logging is not switched on in M03's ALB, so it now says the bucket is ready for them;
    - DEPLOY.md's teardown order now follows the reverse of creation.
  - **M04 solution:** lab log expiry is 365 days (prod 730), not 30. Expiry must come after the last transition (Deep Archive at day 180), and Deep Archive bills a 180-day minimum.

## Blind solve (quiz)

- An independent Opus solver, working only from the exported stems and options, matched the answer key on 30/30.
- It raised two doubts:
  - q07 depended on the unconfirmed 30-day Standard-IA rule. It was rewritten around direct uploads.
  - q26 stated the per-prefix request limit in the stem. The number was removed.
- A fresh Opus solver answered the rewritten questions: matched, nothing flagged.

## Rulings

- P4-1: weeks 04 and 05 were planned and built together, because the learner asked for both in one instruction. One scratch copy, one owner per file; shared files had a fixed order.
- P4-2: notes and quiz were dispatched before the drills and M04 were installed. The models were installed first and the drill topics fixed in advance.
- P4-3: drill 05 returns the TLS-only policy instead of putting it; drill 06 never opens the presigned URL; drill 07 avoids a GET on a delete-marker version id and suspended versioning.
- Planning rulings (in the plan):
  - the assets bucket uses SSE-KMS with the AWS managed key and a Bucket Key (a customer managed key arrives with KMS in week 08);
  - the logs bucket uses SSE-S3, the only encryption ALB access logs support;
  - ALB log delivery uses the service principal, and the compute stack is not changed to switch access logs on;
  - lab log expiry is 365 days;
  - `policy_eval` gains `decide_resource_policy`.

## Known limits

- Moto keeps a bucket's API state, but its CloudFormation keeps only the bucket name, tags and encryption, and skips bucket policies. Its bucket-policy enforcement ignores Condition and Principal, urllib is not intercepted, a GET on a delete-marker version answers 404 where S3 answers 405, and suspended versioning is buggy. So M04's tests read the rendered template, decide the policies with the course's evaluator and replay the lifecycle rules with the `lifecycle` model; moto only proves that the stacks deploy and the buckets exist with their encryption.
- The models are teaching models. `s3cost` prices storage, retrieval, minimum duration and minimum billable size. It leaves out, on purpose, Intelligent-Tiering (its monitoring fee comes in week 11), request charges, Expedited retrieval and the archive classes' 40 KB per-object overhead. `lifecycle` validates and replays rules and gives the state "once the rule has run". Real lifecycle runs asynchronously. It has no prices.
- Prices are illustrative. No question depends on a live price or on a "changed" row.
- The lab and `cleanup.py` target a real account and were never run here. Cleanup is a dry run unless `--yes`, and it touches only `saa-course=lab` resources. It never detaches a root disk, never touches an untagged instance's disk and never bypasses Object Lock. Real-AWS delays (VolumeInUse, snapshots in use) are tested by injecting the errors.

## What to try first

1. `python week_04_storage/concepts/demo_storage_costs.py`, then note 01 and drill 01.
2. Notes 02–05 with drills 02–10 (drills 01–04 are the models, 05–09 boto3, 10 decides).
3. Quiz: `python quiz.py --week 4 -n 30`.
4. M04: `python course_project/tools/start_milestone.py 4 --repo ~/code/shortly-infra`, then `run_milestone.py 4` in your repo.
5. The optional lab, to watch versions, delete markers and a lifecycle rule in a real bucket. Run `cleanup.py --yes` when you finish.

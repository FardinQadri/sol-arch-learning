# AWS SAA course — plan 1 (foundation and pilot) report

Date: 2026-10-08. Nothing is committed: the course folder is not a git repo and the learner asked for no commits until they say so.

## 1. What was built

| Part | Count |
|---|---|
| Concept notes (Markdown) | 10 (5 for week 00, 5 for week 01) |
| Demos | 4 (2 per week) |
| Drills | 20 (10 per week; each week has at least 3 build-the-mechanism drills) |
| Quiz questions | 45 (week 00: 15, week 01: 30) |
| Milestone | M01 IAM baseline (6 steps, with solution snapshot, tests and mutants) |
| Maintainer tests | 171 (`_dev/tests`) |
| Tools | `quiz.py`, `exam_prep/mock_exam.py` (no mock banks yet), `verify_course.py`, `course_project/tools/{start,run}_milestone.py`, `_harness/labclean.py`, `week_NN/lab/cleanup.py` for weeks 00 and 01 |
| Docs | `README.md`, `COURSE_FLOW.md`, `COVERAGE.md`, `docs/exam_guide.md`, `docs/facts.md`, labs for weeks 00 and 01 |

Also built: the harness (`awsdrill`, `quizlib`, `bankgen`, `awslib`: safety, policy evaluator, cfn helpers with lint cache, prices; the CIDR helper is deferred to week 02), the pinned `requirements.txt`, and the venv.

## 2. What was verified

Controller's final runs, 2026-10-08:

- `verify_course.py --self-test`: `_dev/tests pass` (1/1).
- `verify_course.py --coverage`: **89/89 checks passed** (week_00, week_01, milestone M01, question banks, content currency). `COVERAGE.md` was written. The run is non-strict because weeks 02–11 are not built.
- Drills with `--solutions`: week 00 about 16 s, week 01 about 3 s; 10 drills each, all pass; every test fails on the stubs. All 20 mutants are caught (10 per week).
- Milestone M01: the solution is green, an empty repo is red (0/6, with reasons that say what to do), cfn-lint is clean, and 6/6 mutants are caught.
- Content currency: `verify_course.py --banks` reports "no retired services taught as current".
- Learner-eye pass: the quiz re-prompts on a one-letter answer to a Select TWO question; drill ✘ messages are clear on the stubs; `run_milestone` in an empty repo gives actionable reasons.

Coverage table (pilot weeks only):

| Task | Title | Concept notes | Drills | Questions |
|---|---|---|---|---|
| 1.1 | Design secure access to AWS resources | 8 | 12 | 25 |
| 1.2 | Design secure workloads and applications | 3 | 2 | 6 |
| 1.3 | Determine appropriate data security controls | 1 | 0 | 2 |
| 2.1 | Design scalable and loosely coupled architectures | 0 | 1 | 1 |
| 2.2 | Design highly available and/or fault-tolerant architectures | 3 | 3 | 4 |
| 3.1 | Determine high-performing and/or scalable storage solutions | 0 | 2 | 0 |
| 3.2 | Design high-performing and elastic compute solutions | 1 | 0 | 1 |
| 3.3 | Determine high-performing database solutions | 0 | 0 | 0 |
| 3.4 | Determine high-performing and/or scalable network architectures | 1 | 0 | 2 |
| 3.5 | Determine high-performing data ingestion and transformation solutions | 0 | 0 | 0 |
| 4.1 | Design cost-optimized storage solutions | 1 | 1 | 1 |
| 4.2 | Design cost-optimized compute solutions | 1 | 0 | 1 |
| 4.3 | Design cost-optimized database solutions | 0 | 0 | 0 |
| 4.4 | Design cost-optimized network architectures | 1 | 1 | 2 |

The zeros are expected: those task statements belong to weeks 02–11.

## 3. Blind-solve results and rulings

An independent Opus solver saw only a blind file (questions and options, no answers).

**Week 00**
- Round 1: 0/15 disagreements. The solver flagged q02, q03 and q12 as giveaways.
- Ruling 8 (bank-wide rule): options are actions or designs, never their own justification, and cost questions include a "meets the need but costs more" option.
- Fixes: q02, q03 and q12 rewritten (q02 gained a surviving-but-costlier distractor); reason clauses removed from q01, q04, q06, q09, q10.
- Round 2: 0/15 disagreements. q12 is still easy to solve. Kept as a deferred minor: acceptable for a foundations question.

**Week 01**
- 0/30 disagreements. Three refinements: q05 stem now says a corporate range is not needed; q08 option D changed to IAM Identity Center; q30 explanation now separates a trust-policy date condition from live sessions.
- Mini re-check of q05 and q08: both correct, no doubt.

## 4. Deviations and rulings

Deviations from the spec, listed in the plan:
1. No `iam_enforced()` helper in the harness. Week 01's demo calls moto's `set_initial_no_auth_action_count` directly, and the predict drill uses the reference evaluator as its oracle.
2. Week 00 drill 06 seeds 250 objects (three pages of 100), not 2,500. moto takes about 10 s per 1,100 `put_object` calls, and three pages prove pagination equally well.
3. Template helpers (`load_template`, `lint_template`, `render`) live in `awslib/cfn.py`, not on `Drill`, because milestone tests in the learner's repo need them too.

Execution rulings (ledger):
- Ruling 1: no git worktree and no review-package scripts, since the folder is not a repo. Verification ran the plan's commands.
- Ruling 2: the main session verified each task instead of dispatching reviewer subagents (the learner's standing preference). Cost: less independent review.
- Ruling 3: `.superpowers/` added to `.gitignore` so the ledger is never committed.
- Ruling 4: waves B and C re-ordered because the tests of tasks 3 and 6 depend on task 2's conftest.
- Ruling 5: subagents ran in parallel inside a wave, as the learner allowed; the tasks touched disjoint files.
- Ruling 6: task 8 ran after task 7, because it rewrites `verify_milestone` in the file task 7 creates.
- Ruling 7: `docs/facts.md` gained rows (ListObjectsV2 1,000 keys; IAM/STS, Identity Center, RAM and Organizations are free; Simple AD) because the notes needed them from official sources.
- Ruling 8: see section 3.
- Ruling 9: no separate final-review subagent. The final gate was the full `verify_course` run, the self-test, the learner-eye pass and three blind solves.

Content fixes from review: week 00 note 05 (botocore `max_attempts` meaning; credential-chain order); week 01 note 02 (same-account role-ARN corner case); note 03 (Simple AD in maintenance since 2026-06-30); note 05 (Access Analyzer custom policy checks are charged).

## 5. Known limits

- moto gaps shaped the drills: Lambda handler code never runs, so handlers are tested directly; CloudFormation silently skips some resource types and S3 properties, so milestone checks lean on cfn-lint and structural tests.
- Facts not yet confirmed from an official page, so stated nowhere as numbers: the RDS PostgreSQL read-replica count, the One Zone-IA and S3 Express One Zone minimum durations, and FIFO high-throughput limits.
- The mock exam banks do not exist yet; `exam_prep/mock_exam.py` is built and tested only.
- Deferred minor: week 00 q12 distractors are easy to eliminate.
- Labs are written and their cleanup scripts are proven against moto, but no lab has been run against a real account.

## 6. What the learner should try first

1. Read `README.md`, then set up the venv and run `python _dev/smoke_stack.py`.
2. Week 00: concepts and demos, then `exercises.py` to 10/10, then `python quiz.py --week 0 -n 15`.
3. Week 01: the same, with `python quiz.py --week 1 -n 30`.
4. Milestone M01: `python course_project/tools/start_milestone.py 1 --repo ~/code/shortly-infra`, then `run_milestone.py 1` in that repo.
5. Send feedback on pace, difficulty, question style and the drills before week 02 is planned.

## 7. Deferred to the week 02 plan

- Weeks 02–12: notes, demos, drills, quizzes, milestones M02–M11, and labs.
- The four mock exam banks and `FINAL_REVIEW.md`.
- Confirming the unconfirmed facts above.
- Any changes from pilot feedback. The weeks 02–11 coverage gaps close as those weeks land.

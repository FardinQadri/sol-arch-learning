# Plan 3 report — week 03 (Compute and scaling) and milestone M03

Plan: `docs/specs/2026-10-11-aws-saa-plan-3-week-03.md`. Built 2026-10-11. No commits (the learner commits at the end).

## What was built

| Area | Files | Size |
|---|---|---|
| Research | `docs/research/2026-10-11-compute-facts.md` (official AWS pages), `docs/research/2026-10-11-moto-compute-spike.md` (what moto and cfn-lint really do) | 463 fact rows; spike sections A–F |
| Facts of record | `docs/facts.md`: "Compute and scaling (week 03)" (7 subsections) and "EC2 and load balancers (week 03)" prices | rows 242 → 710 |
| Reference models | `_harness/awslib/ec2types.py`, `purchasing.py`, `scaling.py`, `elb.py`, `prices.toml [ec2]` | answer keys for drills 01–05 and 10, reused by M03's tests |
| Tooling | `cfn.py` (`Fn::Base64`, `Fn::Split`), `labclean.py` (Auto Scaling groups, load balancers, target groups, launch templates, security groups), `conftest.py` (`user_data`, `ec2types`, `elb`, `scaling` fixtures), `start_milestone.py` (new helpers, copies the course app from M03 on) | — |
| Maintainer tests | `_dev/tests/test_compute_models.py`, `test_app.py`, `test_labclean_compute.py` (+ changes to `test_cfn_intrinsics.py`, `test_milestone_tools.py`); mutants `_dev/mutants/week03.py`, `m03.py` | 336 tests pass |
| Drills | `week_03_compute_and_scaling/practice/exercises.py` + hidden `solutions.py` | 10 drills (5 ★), 10 mutants |
| Concept notes | `concepts/01 … 05` (instance types, purchasing options, launching instances, Auto Scaling, Elastic Load Balancing) | 206–235 lines each |
| Demos | `demo_fleet_in_moto.py` (launch template, ALB, rules, ASG in moto, and what moto does not simulate); `demo_scaling_and_routing.py` (a day of target tracking vs simple scaling, cross-zone 2/8, five routed requests) | both exit 0 piped |
| Week README, lab | `README.md` (6 goals, 10 interview questions), `lab/LAB.md` (default VPC, ALB + ASG of two t4g.micro, self-healing and a broken health check, ≈ 0.10 USD), `lab/cleanup.py` | — |
| Quiz | `quiz/questions.toml` | 30 questions: 26 single, 4 Select TWO |
| The app | `course_project/app/app.py` — a standard-library URL shortener (`/healthz`, `POST /api/links`, `GET /api/links/<code>`, `GET /<code>` → 302), Python 3.9-compatible | ~75 lines |
| Milestone M03 | `course_project/milestones/M03.md`, tests `course_project/tests/m03/` (6 steps), solution `course_project/solutions/m03/` | 220-line spec; 27 test functions; 14 mutants |
| Project and course docs | `course_project/README.md`, `DEPLOY.md` (compute stack, cost row, delete order), `README.md`, `COURSE_FLOW.md`, `COVERAGE.md` | — |

## Verification (main session, real course)

- `_dev/tests`: 336 passed. `verify_course.py --self-test`: ✔.
- Week 03 drills: stubs 0/10, solutions 10/10, all 10 mutants caught.
- `verify_course.py --week 3`: 38/38. `--milestone 1` 10/10, `--milestone 2` 14/14, `--milestone 3` 18/18 (the reference solution passes in lab and prod, the M02 starting state fails, all 14 mutants caught; all three templates lint with zero findings).
- `verify_course.py --coverage`: 197/197. Week 03 adds coverage of tasks 2.1, 2.2, 3.2 and 4.2.
- Reviews and fixes:
  - **Code:** I read every reference model. Then I fixed four drill issues before install:
    - drill 03's examples answered drill 10's first two predictions, so drill 10 got new numbers;
    - "about 20 %" became "up to 20 %", for Graviton;
    - an unsourced claim that cross-zone is "free" on an ALB was removed;
    - drill 08's title was wrong.
  - **M03 solution:** its user data dropped an unneeded `!Sub`, which removes a cfn-lint warning.
  - **Lab cleanup:** an Auto Scaling group delete now retries while a scaling activity blocks it.
  - **Content:** I read every note, the lab, the demos and M03.md against `docs/facts.md`. Fixes:
    - only Compute Savings Plans cover Fargate and Lambda;
    - the break-even wording;
    - the drill 08 references;
    - in M03.md, where the app comes from and how a new launch-template version rolls out.

## Blind solve (quiz)

- An independent Opus solver, working only from the exported stems and options, matched the answer key on 30/30.
- It flagged six giveaways: q13, q14, q15, q19, q20 and q23. In each, the correct option was the only one that echoed the stem, or the stem named the setting. The main review also moved q03–q06 to the note that teaches them (note 03).
- All six were rewritten so every option is a plausible setting of the same kind. A fresh Opus solver answered the six: 6/6 matched, nothing flagged.

## Rulings

- P3-1: build directly after planning, because the learner asked to "plan and write week 3" in one instruction.
- P3-2 and P3-4: the facts, notes and quiz were dispatched before the plan file was final, to save time. Their briefs are the plan's own task text, and the reference models were installed first so the demos could run.
- P3-3: the lab cleanup's Auto Scaling group delete retries inside its wait loop.
- Planning rulings (in the plan):
  - prod 2–6 / lab 1–2 instances;
  - scaling policy, IMDSv2 and instance profile checked on the template, because moto skips or ignores them;
  - `/healthz` hidden behind a fixed-response rule;
  - Graviton-only instance types;
  - a course-owned app;
  - drill 09 also decides purchase options;
  - drill 10 is a prediction drill;
  - the lab uses the default VPC;
  - the purchase discounts (31 % / 40 % / 70 %) are labelled course examples.

## Known limits

- Moto stores launch templates, Auto Scaling groups and load balancers but simulates almost none of their behaviour:
  - instances all land in one AZ;
  - targets are always healthy;
  - nothing ever scales;
  - template settings never reach instances;
  - placement groups are not implemented.

  The drills teach that behaviour through the four models, and the M03 tests read the rendered template. The week 03 demo prints the gaps.
- The models are teaching models. Target tracking is modelled as "proportional, round up, clamp" and ignores warm-up and cooldown interplay. The simple-scaling cooldown model is per sample. Replacement inside the grace period is not modelled.
- Prices and the three discounts are illustrative. No question depends on a live price, on a "changed" row or on an instance generation newer than 7.
- The lab and `cleanup.py` target a real account and were never run here. Cleanup is a dry run unless `--yes`, and it touches only `saa-course=lab` resources. Moto cannot reproduce real-AWS delays (lingering load-balancer network interfaces, ASG deletion time), so the retry paths are tested by injecting the errors.
- The app keeps links in memory, so with two instances a short link only works on the instance that created it (`DEPLOY.md` says so). M05 moves storage to a database.

## What to try first

1. `python week_03_compute_and_scaling/concepts/demo_scaling_and_routing.py`, then note 01 and drill 01.
2. Notes 02–05 with drills 02–10 (drills 03–05 are the models, 06–08 boto3, 09–10 decide and predict).
3. Quiz: `python quiz.py --week 3 -n 30`.
4. M03: `python course_project/tools/start_milestone.py 3 --repo ~/code/shortly-infra` (it also copies `app/`), then `run_milestone.py 3` in your repo.
5. The optional lab, to watch an Auto Scaling group heal itself behind a real ALB. Clean up within 90 minutes.

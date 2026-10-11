# Plan 2 report — week 02 (VPC networking) and milestone M02

Plan: `docs/specs/2026-10-10-aws-saa-plan-2-week-02.md`. Built 2026-10-10. No commits (the learner commits at the end).

## What was built

| Area | Files | Size |
|---|---|---|
| Facts of record | `docs/facts.md`: new "VPC networking (week 02)" (7 subsections) and "Prices used in drills" | rows 71 → 242, every row sourced |
| Harness | `_harness/awslib/cidr.py`, `netsim.py`, `cfn.py` (parameters, conditions, `!If`, `!Cidr` inlining), `prices.toml [vpc]`, `labclean.py` (NAT gateways, Elastic IPs, VPCs) | — |
| Maintainer tests | `_dev/tests/test_cfn_intrinsics.py`, `test_cidr_netsim.py`, `test_labclean_vpc.py`; mutants `_dev/mutants/week02.py`, `m02.py` | 210 tests pass |
| Drills | `week_02_vpc_networking/practice/exercises.py` + hidden `solutions.py` | 10 drills, 10 mutants |
| Concept notes | `concepts/01 … 05` (CIDR, routing + NAT, SGs/NACLs + flow logs, endpoints + PrivateLink, connecting networks) | 164–200 lines each |
| Demos | `demo_vpc_in_moto.py` (route tables, prefix-list route, reserved IPs), `demo_packet_paths.py` (8 connection checks) | both exit 0 piped |
| Week README, lab | `README.md` (6 goals, 10 interview questions), `lab/LAB.md` (60–90 min, about 0.05 USD), `lab/cleanup.py` | — |
| Quiz | `quiz/questions.toml` | 30 questions: 27 single, 3 Select TWO |
| Milestone M02 | `course_project/milestones/M02.md`, tests `course_project/tests/m02/` (6 steps), solution `course_project/solutions/m02/` | 225-line spec; 24 test functions |
| Project docs | `course_project/README.md` (M02 built), `DEPLOY.md` (network stack, NAT cost row, delete order) | — |
| Course docs | `README.md` (status, week 02 row), `COURSE_FLOW.md` (week 02 section), `COVERAGE.md` | — |

## Verification (main session)

- `_dev/tests`: 210 passed. `verify_course.py --self-test`: ✔.
- Week 02 drills: stubs 0/10, solutions 10/10, all 10 mutants caught.
- Milestones: `verify_course.py --milestone 1` 10/10 and `--milestone 2` 14/14 (the reference solution passes every step, and every mutant is caught). The M02 solution deploys in moto for `Env=lab` (one NAT gateway) and `Env=prod` (two).
- `verify_course.py --coverage`: 141/141 checks passed. Week 02 adds coverage of tasks 1.2, 2.2, 3.4 and 4.4.
- Content review: every number in the five notes, M02.md, DEPLOY.md and the quiz was checked against `docs/facts.md`. Fixes made: 12 in the notes and lab (Task 3 fix round 1) and 1 in DEPLOY.md (flow logs are not free).

## Blind solve (quiz)

- An independent Opus solver, working only from the exported stems and options, matched the answer key on 30/30.
- It flagged q23 and q29 as giveaways. The main review added three more: q29's "remove public IPs" option would have broken Session Manager without endpoints, q09 had a self-justifying option, and q30's correct option was by far the longest.
- All four were rewritten. A fresh Opus solver answered the four rewritten questions: 4/4 matched, no doubts.

## Rulings

- P2-1: build directly after writing the plan, because the learner asked for both in one instruction.
- P2-2: the NAT design comes from `Env` (no NatMode parameter); the flow-logs role lives in the network stack; `!Cidr` is inlined for moto; subnet associations are checked structurally.
- P2-3: `labclean` checks tags client-side for every EC2 finder, because moto ignored the NAT gateway tag filter.
- P2-4: the quiz was written in parallel with the notes (fixed note file names, facts from `facts.md`).
- P2-5: the lab turns the flow log on before the NAT gateway and only reads it later, because Session Manager stops when the NAT gateway is deleted.
- P2-6: three qualitative Direct Connect/VPN statements stay in note 05 without `facts.md` rows; week 07 adds them.

## Known limits

- Moto does not enforce `SubnetRouteTableAssociation`, `MapPublicIpOnLaunch` or `EnableDnsHostnames`, and it cannot run `!Cidr`. The M02 tests check these on the rendered template instead, and the test tools expand `!Cidr` before deploying.
- `netsim` is a teaching model. It covers security groups, network ACLs, routes and peering vs Transit Gateway, not every AWS edge case (for example prefix lists or the newer local-route replacement).
- Prices are illustrative (`facts.md` notes which ones were not seen for us-east-1). No drill or question depends on a live price.
- The lab and `cleanup.py` target a real account and were never run here. The cleanup is dry-run unless `--yes`, and it touches only `saa-course=lab` resources. The flow-log service role the console creates is untagged, so the lab tells you to delete it by hand.

## What to try first

1. Run `python week_02_vpc_networking/concepts/demo_vpc_in_moto.py`, then read note 01 and do drills 01–02.
2. Work through notes 02–05 with drills 03–10.
3. Quiz: `python quiz.py --week 2 -n 30`.
4. M02: `python course_project/tools/start_milestone.py 2 --repo ~/code/shortly-infra`, then `run_milestone.py 2` in your repo.
5. The optional lab, if you want to see a NAT gateway and flow logs for real. Delete the NAT gateway within 30 minutes.

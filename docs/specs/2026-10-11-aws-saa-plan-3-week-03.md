# AWS SAA Course — Plan 3: Week 03 (Compute and scaling) + M03 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build week 03 — compute and scaling — in the shape of weeks 01–02: 5 concept notes, 2 demos, 10 drills (5 ★), a 30-question quiz, a real-AWS lab with a safe cleanup, and capstone milestone M03 (the `compute` stack: ALB, launch template with IMDSv2, Auto Scaling group, listener rules), plus the small app the instances run and the library pieces the drills and tests need.

**Architecture:** Drills 01–05 are pure-Python models whose answer keys live in four new modules: `_harness/awslib/ec2types.py` (instance-type names, choosing C/M/R by memory per vCPU), `purchasing.py` (On-Demand / Compute Savings Plan / Standard RI / Spot monthly cost), `scaling.py` (target tracking, step and simple scaling, health-check replacement) and `elb.py` (ALB listener-rule matching, cross-zone share, ALB cost). The milestone tests reuse them. Drills 06–08 run boto3 against moto. moto stores launch templates, Auto Scaling groups and load balancers faithfully but simulates almost none of their behaviour (spike: `docs/research/2026-10-11-moto-compute-spike.md`) — so behaviour is taught through the models, and M03's tests check scaling policies, IMDSv2 and rule routing on the rendered template, using moto only to prove the three stacks deploy together. `cfn.py` learns `Fn::Base64` and `Fn::Split`; `start_milestone.py` copies the new helpers and the course-owned app (`course_project/app/app.py`, a standard-library URL shortener) into the learner's repo; `labclean` learns Auto Scaling groups, load balancers, target groups, launch templates and security groups. All code in this plan was written and run in a scratch copy of the course before the plan was written (results in Task 1).

**Tech Stack:** as plans 1–2 (Python 3.14.2, moto 5.2.3, boto3 1.43.109, cfn-lint 1.57.2, pytest 9.1.1). No new packages.

**Spec:** `docs/specs/2026-10-08-aws-saa-course-design.md` §4.0–§4.5 (week 03 row, drill row 03, M03 row). Facts: `docs/research/2026-10-11-compute-facts.md` (official sources, read 2026-10-11). moto spike: `docs/research/2026-10-11-moto-compute-spike.md`. Previous plans: `docs/specs/2026-10-08-aws-saa-plan-1-foundation-and-pilot.md` (its Global Constraints still apply) and `docs/specs/2026-10-10-aws-saa-plan-2-week-02.md`.

**Execution (learner's instruction, 2026-10-11: "looks good, use as many subagents u want, plan and write week 3"):** Sonnet implementers, parallel where files are disjoint; the main session verifies every task itself (runs the commands, reads every note against `docs/facts.md`, blind-solves the quiz with an independent Opus agent and re-solves rewritten questions with a fresh one). No git, no commits.

## Global Constraints

- Everything in plan 1's Global Constraints (course root, `.venv` only, no git, never real AWS, Windows-first + `force_utf8`, pinned versions, drill format, content rules, quiz rules, definition of done) and plan 2's (quiz style ruling 8; services from later weeks may appear in questions).
- **Numbers:** every number in notes and questions comes from `docs/facts.md`; Task 2 adds the compute rows. Instance and load-balancer prices are illustrative (`prices.toml [ec2]`). The course's purchase discounts are examples: Compute Savings Plan 31 % (AWS's average 1-year Convertible RI discount, which the Savings Plans FAQ compares it to), Standard RI 40 % (AWS's 1-year average), Spot 70 % (AWS says "up to 90 %").
- **Exam vs 2026 reality:** teach the exam answers. Launch configurations: teach launch templates; state once, as "changed", that new accounts can no longer create launch configurations (2024-10-01). Instance generations change fast (M8g/M9g, Graviton5 …): notes may name them once as examples; no question depends on a generation newer than 7 or on a "changed" row. Database Savings Plans exist (one line, week 05 detail).
- **Lab cost:** the week 03 lab runs one ALB and two t4g.micro instances in the default VPC for at most about 90 minutes (≈ 0.10 USD; ALB 0.0225 USD/hour + LCUs, instances 0.0084 USD/hour each, public IPv4 0.005 USD/hour each, all illustrative); every resource tagged `saa-course=lab`, the Auto Scaling group with PropagateAtLaunch.

## Review Focus

1. **`cleanup.py` must never delete untagged load balancers, target groups, launch templates, Auto Scaling groups or security groups**, and must delete security groups that reference each other. Tests: `_dev/tests/test_labclean_compute.py` (untagged twin of every kind survives; referencing pair deleted; untagged referenced group survives).
2. **IMDSv2 and the instance profile are checked on the launch template, not on instances** — moto does not apply template MetadataOptions to instances, so a test reading instances would pass a learner who wrote `optional`. Tests: `test_m03_2_launch_template.py`, `test_m03_6_exports_and_deploy.py` (reads `describe_launch_template_versions`), mutant `imdsv1-allowed`.
3. **The scaling policy is checked on the rendered template** — moto silently skips `AWS::AutoScaling::ScalingPolicy`, so a deploy-only test would pass a template without one. Test: `test_m03_4_auto_scaling.py`; mutant `no-scaling-policy`.
4. **The user data must carry the course's app verbatim and stay under the 16 KB user-data limit**, or instances boot without a working app. Test: `test_m03_3_user_data.py`; mutant `app-not-inlined`.
5. **M01 and M02 keep passing** after `start_milestone.py 3` overwrites `tests/conftest.py`, `tests/_course/` and copies `app/`. Test: `run_milestone.py 3` is cumulative (verify_course milestone check), `_dev/tests/test_milestone_tools.py`.

## Rulings made while planning (spec deviations and choices)

- **Lab environment sizes the group smaller**: spec M03.3 says "ASG min 2". Prod keeps MinSize 2 / MaxSize 6 (survives the loss of an AZ); `Env=lab` uses 1 / 2 to halve the instance hours of a test deploy. M01's test pins `params/*.json` to `{"Prefix", "Env"}`, so the sizes come from `!If [IsProd, …]`. Cost if wrong: one `!If` to change.
- **The scaling policy, IMDSv2 and the instance profile are checked on the rendered template**, not on moto's deployed state (moto skips `AWS::AutoScaling::ScalingPolicy` and does not apply template MetadataOptions/profile to instances — spike §B, §D, §F3).
- **The public listener hides `/healthz`** (rule priority 10 → fixed-response 404) and routes `/api/*` explicitly (priority 20) with the default rule forwarding everything else (short-link redirects). Health checks go straight to the targets, so they keep working. This gives spec M03.4's "listener rules (/api/*, default)" a real job.
- **`InstanceType` allows Graviton types only** (`t4g.small` default, `t4g.medium`, `m7g.large`, `c7g.large`) — spec "Graviton type parameter"; the test decodes each allowed value with `ec2types.decode`.
- **The app is course-owned** (`course_project/app/app.py`, standard library, Python 3.9-compatible because Amazon Linux 2023 ships 3.9) and `start_milestone.py 3+` copies it into the learner's repo; the learner pastes it into the user data, and the test checks every line is there and the user data stays ≤ 16 KB.
- **Drill 09 decides purchase options as well as placement groups** (spec lists only placement): task 4.2 needs a decision drill, and drill 02 only computes cost.
- **Drill 10 is a predict drill** (spec lists nine items for week 03): like weeks 01–02, ten drills with the last one a prediction answered by the reference models.
- **The week 03 lab uses the default VPC** (public subnets, no NAT gateway, so it costs about 0.10 USD); the notes and M03 say production puts instances in private subnets behind the ALB.
- **Purchase discounts are course examples** (31 % / 40 % / 70 %), labelled as such in `prices.toml` and `docs/facts.md`, because AWS publishes only "up to" figures and averages.

## Files this plan creates or changes

```
_harness/awslib/ec2types.py · purchasing.py · scaling.py · elb.py   (new: week 03 drills 01–05 answer keys)
_harness/awslib/cfn.py             (changed: Fn::Base64, Fn::Split)
_harness/awslib/prices.toml        (changed: [ec2] section)
_harness/labclean.py               (changed: autoscaling_groups, load_balancers, target_groups, launch_templates, security_groups finders; new FINDERS order)
_dev/tests/test_compute_models.py · test_app.py · test_labclean_compute.py   (new)
_dev/tests/test_cfn_intrinsics.py · test_milestone_tools.py   (changed)
_dev/mutants/week03.py · m03.py    (new)
course_project/app/app.py          (new: the course-owned app)
course_project/tools/conftest.py · start_milestone.py   (changed: ec2types/elb/scaling fixtures; copies new helpers and app/)
course_project/tests/m03/test_m03_{1..6}_*.py   (new)
course_project/solutions/m03/{infra/iam.yaml, infra/network.yaml, infra/compute.yaml, app/app.py, params/*.json, README.md, .gitignore}   (new)
course_project/milestones/M03.md · course_project/README.md · DEPLOY.md   (new / changed)
docs/facts.md                      (changed: compute section, prices rows)
week_03_compute_and_scaling/README.md · concepts/01..05_*.md · concepts/demo_*.py (2) · practice/exercises.py · practice/solutions.py · quiz/questions.toml · lab/LAB.md · lab/cleanup.py   (new)
README.md · COURSE_FLOW.md · COVERAGE.md · docs/specs/2026-10-11-aws-saa-plan-3-report.md   (changed / new)
```

## Waves

| Wave | Tasks | Needs |
|---|---|---|
| A | 1 (code bundle), 2 (facts) | — |
| B | 3 (notes, demos, README, lab), 4 (quiz + blind solve), 5 (M03.md + project docs) | 1, 2 (4 uses Task 3's fixed note file names, as plan 2 ruling P2-4) |
| C | 6 (docs, full verification, report) | everything |

---

### Task 1: Install the verified code bundle

**Files:** every file in Appendix A (create, or replace where it already exists), exactly as given.

**Interfaces:**
- Produces: `ec2types.decode / choose_type`; `purchasing.OPTIONS / monthly_cost / cheapest / break_even_hours`; `scaling.target_tracking / step_scaling / simple_scaling_run / replaces_instance`; `elb.match_rule / cross_zone_share / alb_monthly_cost`; `prices.section("ec2")`; `cfn.render` handles `Fn::Base64` (renders as plain text) and `Fn::Split`; `labclean.FINDERS` keys `autoscaling_groups`, `load_balancers`, `target_groups`, `launch_templates`, `security_groups` (plus plans 1–2's); milestone fixtures `ec2types`, `elb`, `scaling`; `start_milestone.py` copies `course_project/app/` to `<repo>/app/` from M03 on.

- [ ] **Step 1: Write every Appendix A file** with exactly the content shown (each file's heading gives its course-relative path). Where a file already exists, replace the whole file. Create `course_project/solutions/m03/infra/iam.yaml`, `infra/network.yaml`, `params/lab.json`, `params/prod.json` and `.gitignore` by copying them unchanged from `course_project/solutions/m02/`.
- [ ] **Step 2: Run the maintainer tests** — `.venv/Scripts/python.exe -m pytest _dev/tests -o addopts="" -p no:cacheprovider -q | tail -1` → the count recorded in Appendix A's header, all passed.
- [ ] **Step 3: Check the drills and the milestones** — `exercises.py | tail -1` → `0/10 passing`; `--solutions | tail -1` → `10/10 passing (solutions)`; `verify_course.py --week 3` drill and mutant lines ✔; `verify_course.py --milestone 1`, `2`, `3` → all checks passed.
- [ ] **Step 4: Commit** — skipped (no git).

---

### Task 2: Compute facts in `docs/facts.md`

**Files:** Modify `docs/facts.md`.

- [ ] **Step 1:** Add a section `## Compute and scaling (week 03)` after the VPC section, built from `docs/research/2026-10-11-compute-facts.md` sections 1–7, subsections: EC2 instance types · Purchasing options · Placement groups · Instance metadata and user data · Instance storage and states · EC2 Auto Scaling · Elastic Load Balancing. Keep every **confirmed** row that a week 03 note or question could need (naming and option letters; families and C/M/R memory ratios; Graviton cost claim; burstable credits, modes and defaults; vCPU quotas; per-second billing; Savings Plans types, flexibility and "up to" figures with the FAQ comparison to RIs; RI types, scope and Marketplace rule; Spot notice, rebalance, interruption behaviours; Dedicated Host vs Instance; ODCR; Capacity Blocks one row; placement strategies and limits; IMDSv1/v2, hop limit, account default; user data size, run-once, root, log; instance store; stop/hibernate/terminate billing; hibernation requirements; ASG min/max/desired, health checks and grace period, cooldown, policy types and target-tracking wording, step bounds, scheduled limit, warmup, termination policy, lifecycle hooks, warm pools, instance refresh, mixed instances and allocation strategies, capacity rebalancing, max instance lifetime, AZ rebalancing; launch configuration status rows (changed, dated); ALB/NLB/GWLB/CLB layer, protocols, rules, conditions and case rules, quotas, health-check defaults, deregistration delay, slow start, stickiness, cross-zone defaults and the 2/8 example, NLB static IPs, security groups (changed), client IP preservation; CLB status). Keep the `Fact | Value | Changed? | Source` columns and the research file's sources. Rows the research lists as unconfirmed are NOT added; append them to the existing "Not confirmed" line.
- [ ] **Step 2:** Extend `## Prices used in drills (illustrative, us-east-1)` with every `prices.toml [ec2]` value and its research row; the three discounts are marked "course example" with the AWS figure they come from.
- [ ] **Step 3:** `grep -c "^| " docs/facts.md` grows by at least 120; `verify_course.py --banks | grep retired` stays ✔.

---

### Task 3: Week 03 concept notes, demos, README and lab

**Files:** Create in `week_03_compute_and_scaling/`: `concepts/01_ec2_instance_types.md`, `concepts/02_purchasing_options.md`, `concepts/03_launching_instances.md`, `concepts/04_auto_scaling.md`, `concepts/05_elastic_load_balancing.md`, `concepts/demo_fleet_in_moto.py`, `concepts/demo_scaling_and_routing.py`, `README.md`, `lab/LAB.md`, `lab/cleanup.py`.

**Writing rules:** plan 1 Task 12's rules (first line `Exam tasks: …`; sections What it is / How it works / Numbers to know / When to choose it / Exam traps / Cost angle / Comparison; 150–300 lines; numbers only from `docs/facts.md`; plain English). Do **not** reveal drill 09's or drill 10's answers or paste drill solutions; teach the rules with other examples.

| File | Exam tasks line | Must cover |
|---|---|---|
| `01_ec2_instance_types.md` | `Exam tasks: 3.2, 4.2` | what an instance type is; reading a name (series, generation, option letters, size — drill 01); the families and what each is for; memory per vCPU C 2 / M 4 / R 8 GiB and choosing by ratio; Graviton (Arm, "up to 20 % less cost" claim) and when x86 is still needed; burstable T: CPU credits, baseline, standard vs unlimited (default for T3/T4g), surplus charges; sizes double; vCPU quotas; newest generations named once as examples; comparison table of families |
| `02_purchasing_options.md` | `Exam tasks: 4.2` | On-Demand (per second, 60 s minimum); Savings Plans (Compute vs EC2 Instance, "up to 66 % / 72 %", 1 or 3 years, payment options, the FAQ comparison to RIs, Database SP one line); Reserved Instances (Standard vs Convertible, regional vs zonal — only zonal reserves capacity, Marketplace for Standard); Spot (up to 90 %, two-minute notice, rebalance recommendation, interruption behaviours, not covered by Savings Plans); Dedicated Hosts vs Dedicated Instances (BYOL, per-host billing); On-Demand Capacity Reservations (no discount alone; combine); Capacity Blocks one line; the commitment break-even idea with the course's example discounts (drill 02); baseline on commitments + peaks On-Demand/Spot; comparison table |
| `03_launching_instances.md` | `Exam tasks: 3.2, 1.2, 2.2` | AMIs and the SSM public parameter for the latest Amazon Linux; launch templates (versions, $Latest/$Default) and the launch-configuration status ("changed", dated); user data (16 KB, root, first boot only, log path); instance profiles instead of keys; IMDSv1 vs IMDSv2 (token PUT, hop limit 1 vs 2 for containers, require it; account-level default as "changed"); placement groups: cluster, spread (7 per AZ), partition (7 partitions per AZ), rules; instance store vs EBS root; stop / hibernate (requirements) / terminate and what is billed; comparison table of placement strategies |
| `04_auto_scaling.md` | `Exam tasks: 2.1, 2.2, 3.2` | groups: min/max/desired, multiple AZs, AZ rebalancing; health checks EC2 vs ELB and the grace period (300 s console / 0 API); policies: target tracking (proportional, rounds up, scales in gradually; predefined metrics incl. ALBRequestCountPerTarget), step (bounds), simple + cooldown (300 s, AWS recommends against), scheduled (125 actions, UTC), predictive; instance warmup; termination policy order; lifecycle hooks (3,600 s default); warm pools; instance refresh (90 % min healthy); mixed instances + price-capacity-optimized + capacity rebalancing; max instance lifetime; suspend processes; comparison table of policy types (drill 03) |
| `05_elastic_load_balancing.md` | `Exam tasks: 2.1, 2.2, 3.2` | ALB (layer 7, listeners, rules: priority, conditions and case rules, actions, default rule — drill 04; target types; health-check defaults; deregistration delay 300 s; slow start; sticky sessions; X-Forwarded-For; SNI/multiple certificates; 2 AZs minimum); NLB (layer 4, TCP/UDP/TLS, one static IP per AZ / Elastic IP, client IP preservation, security groups "changed"); GWLB (layer 3, GENEVE 6081, appliances); CLB previous generation; cross-zone defaults and the 2/8 example (drill 05), NLB inter-AZ charges; internet-facing vs internal; ALB + ASG integration; cost (ALB hour + LCU, NLB + NLCU); comparison table ALB / NLB / GWLB / CLB |

- [ ] **Step 1: Write the five notes** per the table.
- [ ] **Step 2: `concepts/demo_fleet_in_moto.py`** — offline moto demo in week 02's demo style: VPC + 2 subnets + SG; the latest Amazon Linux arm64 AMI from the SSM public parameter; a launch template with IMDSv2 required; target group with `/healthz`; ALB + listener + the two rules; an ASG of 2 attached to the target group with a target-tracking policy. Print what was built (template MetadataOptions, ASG sizes and health check type, rules in priority order — sorted, because moto keeps creation order, target health). Then print, plainly, what moto does NOT simulate (AZ spreading, health, scaling — "that is why drills 03–05 are models"). Ends with "Now do drills 06–08." Exit 0 piped.
- [ ] **Step 3: `concepts/demo_scaling_and_routing.py`** — pure Python with the models: a day of CPU readings through target tracking vs simple scaling with a 300 s cooldown (table of desired capacity per hour); the cross-zone 2/8 example both ways; five requests routed through a rule set (different rules and requests from drills 04, 07 and 10). Ends with "Now do drills 03–05 and 10." Exit 0 piped.
- [ ] **Step 4: `README.md`** — headings as weeks 00–02. Goals (6): read an instance type and choose a family and size; choose a purchasing option for a usage pattern; launch instances safely (launch template, IMDSv2, instance profile, user data, placement); build a self-healing, self-scaling Auto Scaling group; choose and configure a load balancer and its rules; reason about compute cost. Your week (≈ 10–12 h, same split as week 02, quiz `python quiz.py --week 3 -n 30`, milestone M03). Exam tasks covered: 2.1, 2.2, 3.2, 4.2. Service comparison: On-Demand vs Savings Plan vs RI vs Spot vs Dedicated Host, and ALB vs NLB vs GWLB. Interview questions (10): e.g. "How do you choose an instance type?", "Savings Plan or Reserved Instance?", "When is Spot the right answer?", "Why require IMDSv2?", "What does an Auto Scaling group do when an AZ fails?", "EC2 or ELB health checks?", "Target tracking vs step scaling?", "ALB vs NLB?", "What is cross-zone load balancing and when does it cost money?", "How would you cut the cost of a web fleet?". Final line: "Now you may read `_harness/awslib/ec2types.py`, `purchasing.py`, `scaling.py` and `elb.py` — compare them with your drills 01–05."
- [ ] **Step 5: `lab/LAB.md` and `lab/cleanup.py`** — LAB (≈ 60–90 min; ≈ 0.10 USD; free plan or Free Tier may cover the t4g.micro hours): 1 before you start (guard rails, profile `saa-lab`, one Region, tag EVERYTHING `saa-course=lab`, the ASG tag with "Tag new instances"); 2 two security groups in the default VPC (ALB: 80 from anywhere; instances: 80 from the ALB group only); 3 a launch template: Amazon Linux 2023 arm64, t4g.micro, IMDSv2 required (look for "Metadata version: V2 only"), user data that installs nothing and runs `python3 -m http.server 80` from a folder with an `index.html` holding the instance id fetched with an IMDSv2 token (give the exact script), and a `healthz` file; 4 a target group (HTTP 80, health check path `/healthz`), an internet-facing ALB in two or more default subnets, listener 80 → the target group; 5 an ASG (min 2, max 4, desired 2, the default subnets, attach the target group, ELB health checks, grace period 120 s, target tracking CPU 50 %); 6 watch the targets turn healthy, `curl` the ALB DNS name several times and see two instance ids; 7 self-healing: terminate one instance in the EC2 console and watch the ASG replace it; then edit the target group's health check path to `/nope`, watch the targets go unhealthy and the ASG start replacing them, change it back; 8 clean up: `python lab/cleanup.py --profile saa-lab` (dry run, read it), then `--yes` (deletes the ASG with its instances, the ALB, the target group, the launch template, tagged instances left over, then the two security groups); check the next day in Billing; 9 what to write down. `cleanup.py` = week 02's pattern with `kinds=["autoscaling_groups", "load_balancers", "target_groups", "launch_templates", "ec2_instances", "security_groups"]` and a docstring naming them.
- [ ] **Step 6: Verify** — demos exit 0 piped; `verify_course.py --week 3 2>&1 | grep -E "concept|demo|README|lab"` all ✔; `verify_course.py --banks | grep retired` ✔.

---

### Task 4: Week 03 quiz (30 questions) + blind solve

**Files:** Create `week_03_compute_and_scaling/quiz/questions.toml`.

- [ ] **Step 1: Write the 30 questions** (quiz rules, ruling 8; ids `w03-q01 … w03-q30`; 3–6 Select TWO; refs = Task 3's five notes):

| ids | domain · task | topics (one question each, in order) |
|---|---|---|
| q01–q07 | 3 · 3.2 | family for an in-memory workload (memory per vCPU) · burstable T for a low, spiky load and the unlimited-mode surcharge · cluster placement group for tightly coupled HPC · spread placement for a few critical instances (7 per AZ) · partition placement for a rack-aware big-data cluster · instance store for scratch data vs EBS for data that must survive a stop · hibernation to keep a warmed-up in-memory state (requirements) |
| q08–q10 | 1 · 1.2 | require IMDSv2 to stop SSRF credential theft · instance profile instead of access keys in user data · hop limit 2 for containers on the instance |
| q11–q19 | 2 · 2.2 / 2.1 | ASG across two AZs with min 2 for an AZ failure · ELB health checks when the app dies but the instance runs · grace period too short → replacement loop · user data runs once: roll a change with an instance refresh · lifecycle hook or warm pool for a slow boot (Select TWO) · scheduled scaling for a known 8 a.m. peak · target tracking on ALBRequestCountPerTarget · sessions lost on scale-in: move state out vs stickiness (Select TWO) · deregistration delay during scale-in |
| q20–q25 | 3 · 3.2 / 2.1 | ALB path-based routing to two services · host-based routing for two domains with SNI on one ALB · NLB for static IPs per AZ and client IP preservation · NLB for UDP / millions of requests per second · GWLB for third-party firewall appliances · cross-zone load balancing with uneven targets per AZ |
| q26–q30 | 4 · 4.2 | Compute Savings Plan for steady use across families and Lambda (MOST cost-effective) · Spot with a mixed-instances group: On-Demand base + Spot, price-capacity-optimized (Select TWO) · Dedicated Host for per-core BYOL licensing · capacity for a two-week event: On-Demand Capacity Reservation vs zonal RI · cut a dev fleet's cost: Graviton + scheduled scale to zero at night (works-but-costs-more option included) |

- [ ] **Step 2: Validate** — `verify_course.py --week 3 2>&1 | grep -i quiz` all ✔; `verify_course.py --banks | tail -6` no near-duplicates.
- [ ] **Step 3: Blind solve (main session)** — export with `_dev/blindsolve.py export`, an independent Opus agent answers from the blind file only and lists doubts, `compare`; fix every disagreement and real doubt through the implementer; a fresh Opus agent re-solves the rewritten questions.

---

### Task 5: M03 spec and project docs

**Files:** Create `course_project/milestones/M03.md`; modify `course_project/README.md`, `course_project/DEPLOY.md`.

- [ ] **Step 1: `M03.md`** — same shape as M02.md, matching `course_project/tests/m03/` exactly: intro (the compute layer: ALB, launch template, ASG; costs money only when deployed — ALB hourly + LCU, instances, public IPv4 of the ALB); Step 0 (`start_milestone.py 3` — it also copies the course's app into `app/`; `run_milestone.py 3`, cumulative); What the tests rely on (file `infra/compute.yaml`; parameters incl. `InstanceType` and the SSM-typed `ImageId`; the six imports by export name; every logical id from the tests; the four exports); M03.1–M03.6 in plain words; YAML examples allowed: the SSM `ImageId` parameter, the launch template's `MetadataOptions` block, the user-data skeleton with the app elided (`# … paste app/app.py here …`), and one listener rule — never the whole template; a note that moto does not run scaling policies or apply launch-template settings to instances, which is why the tests read the template; Done when; Hints (why ELB health checks; grace period; `!GetAtt AppLaunchTemplate.LatestVersionNumber`; `!Split [",", !ImportValue …]`; `${` in the app would break `!Sub`; user data ≤ 16 KB; why `/healthz` is hidden); Why this matters in the exam.
- [ ] **Step 2: `course_project/README.md`** — M03 built. **`DEPLOY.md`** — the compute stack: deploy after network (`--stack-name shortly-compute --parameter-overrides Prefix=shortly Env=lab`; no IAM capability needed unless the stack creates roles), the cost row "ALB about 0.0225 USD/hour + LCUs; t4g.small about 0.0168 USD/hour each — 1 in lab, 2+ in prod (illustrative)", delete order `shortly-compute` → `shortly-network` → `shortly-iam`.

---

### Task 6: Course docs, full verification, report

**Files:** Modify `README.md` (week 03 row links to its README; Status: weeks 00–03 + M01–M03 built), `COURSE_FLOW.md` (week 03 section like week 02's, `start_milestone.py 3`, `run_milestone.py 3`); generate `COVERAGE.md`; create `docs/specs/2026-10-11-aws-saa-plan-3-report.md`.

- [ ] **Step 1:** README and COURSE_FLOW edits.
- [ ] **Step 2 (main session):** `verify_course.py --self-test`, `--milestone 3` and `--coverage`; everything green.
- [ ] **Step 3:** report (what was built with counts; verification; blind-solve results; rulings; known limits; what to try first); update memory.

---
## Appendix A — verified code bundle (Task 1)

Every file below was written and run in a scratch copy of the course before this plan was final, then installed by the main session (LF line endings). Results in the real course on 2026-10-11: `_dev/tests` 336 passed; `week_03_compute_and_scaling/practice/exercises.py` 0/10 passing, `--solutions` 10/10; `verify_course.py --week 3` drill and mutant lines all ✔ (38/38 once Tasks 3–4 landed); `--milestone 1` 10/10, `--milestone 2` 14/14, `--milestone 3` 18/18 (14 mutants caught). `course_project/solutions/m03/infra/iam.yaml`, `infra/network.yaml`, `params/*.json` and `.gitignore` are byte-identical copies of `solutions/m02/` and are not repeated here.

### `_harness/awslib/ec2types.py`

````python
"""ec2types — read EC2 instance-type names and pick a size.

This is the reference solution for week 03's drill 01: finish that drill before you read it.
Rules (docs/research/2026-10-11-compute-facts.md §1): a name is <series><generation><options>.<size>,
e.g. c7gn.xlarge = series c, generation 7, options g (Graviton) and n (network optimized), size xlarge.
Memory per vCPU: C = 2 GiB, M = 4 GiB, R = 8 GiB (c7g.large, m7g.large, r7g.large).
"""
from __future__ import annotations

import re

SERIES = {  # longest prefixes first when parsing
    "mac": "general purpose", "inf": "accelerated computing", "trn": "accelerated computing",
    "hpc": "high performance computing", "dl": "accelerated computing", "vt": "accelerated computing",
    "m": "general purpose", "t": "general purpose", "a": "general purpose",
    "c": "compute optimized",
    "r": "memory optimized", "x": "memory optimized", "z": "memory optimized", "u": "memory optimized",
    "i": "storage optimized", "d": "storage optimized", "h": "storage optimized",
    "p": "accelerated computing", "g": "accelerated computing", "f": "accelerated computing",
}
OPTIONS = {"a": "AMD processor", "g": "AWS Graviton processor", "i": "Intel processor",
           "d": "instance store volumes", "n": "network and EBS optimized",
           "e": "extra storage or memory", "z": "high CPU frequency", "b": "block storage optimized",
           "q": "Qualcomm inference accelerators", "flex": "flex instance"}
PROCESSORS = {"g": "AWS Graviton", "a": "AMD", "i": "Intel"}
_SIZE = re.compile(r"nano|micro|small|medium|large|xlarge|[1-9][0-9]*xlarge|metal(-[0-9]+xl)?")


def decode(instance_type: str) -> dict:
    """Split an instance type name into its parts. Raises ValueError naming what is wrong."""
    name = instance_type.strip().lower()
    if "." not in name:
        raise ValueError(f"{instance_type!r} has no '.' between the family and the size")
    family, size = name.split(".", 1)
    if not _SIZE.fullmatch(size):
        raise ValueError(f"{instance_type!r}: unknown size {size!r}")
    flex = family.endswith("-flex")
    if flex:
        family = family[: -len("-flex")]
    series = next((key for key in sorted(SERIES, key=len, reverse=True) if family.startswith(key)), None)
    if series is None:
        raise ValueError(f"{instance_type!r}: unknown series in {family!r}")
    rest = family[len(series):]
    digits = re.match(r"[0-9]+", rest)
    if not digits or int(digits.group()) < 1:
        raise ValueError(f"{instance_type!r}: no generation number after the series {series!r}")
    options = list(rest[digits.end():])
    for letter in options:
        if letter not in OPTIONS:
            raise ValueError(f"{instance_type!r}: unknown option letter {letter!r}")
    if flex:
        options.append("flex")
    processor = next((PROCESSORS[o] for o in options if o in PROCESSORS), "not stated")
    return {"series": series, "category": SERIES[series], "generation": int(digits.group()),
            "options": options, "processor": processor, "size": size, "burstable": series == "t",
            "instance_store": "d" in options, "bare_metal": size.startswith("metal"), "flex": flex}


def choose_type(vcpus: int, memory_gib: float, processor: str = "graviton", generation: int = 7) -> str:
    """Pick C, M or R by memory per vCPU (<= 2, <= 4, <= 8 GiB) and the size by vCPU count."""
    if vcpus <= 0 or memory_gib <= 0:
        raise ValueError("vcpus and memory_gib must be positive")
    letters = {"graviton": "g", "intel": "i", "amd": "a"}
    if processor not in letters:
        raise ValueError(f"unknown processor {processor!r}: use graviton, intel or amd")
    ratio = memory_gib / vcpus
    if ratio <= 2:
        series = "c"
    elif ratio <= 4:
        series = "m"
    elif ratio <= 8:
        series = "r"
    else:
        raise ValueError("more than 8 GiB per vCPU: look at the X or U families")
    if vcpus == 1:
        size = "medium"
    elif vcpus == 2:
        size = "large"
    elif vcpus == 4:
        size = "xlarge"
    elif vcpus % 4 == 0:
        size = f"{vcpus // 4}xlarge"
    else:
        raise ValueError(f"no standard size has {vcpus} vCPUs")
    return f"{series}{generation}{letters[processor]}.{size}"
````

### `_harness/awslib/purchasing.py`

````python
"""purchasing — what the same fleet costs under each EC2 purchasing option.

This is the reference solution for week 03's drill 02: finish that drill before you read it.
Rules (docs/research/2026-10-11-compute-facts.md §2): On-Demand and Spot bill only for the hours an
instance runs; Savings Plans and Reserved Instances are commitments billed for every hour of the month.
A Standard RI is locked to an instance type and Region; a Compute Savings Plan follows you to any
family, Region, Fargate or Lambda. Discounts are the course's illustrative figures (prices.toml).
"""
from __future__ import annotations

from . import prices

PRICES = prices.section("ec2")
OPTIONS = ("on-demand", "compute savings plan", "standard reserved", "spot")
_COMMITMENT_DISCOUNT = {"compute savings plan": "compute_savings_plan_discount",
                        "standard reserved": "standard_ri_discount"}


def monthly_cost(option: str, rate: float, instances: int, hours_used: float, *,
                 hours_in_month: int = 730, price: dict = PRICES) -> float:
    """Monthly USD cost. `rate` is the On-Demand price per instance-hour."""
    if option not in OPTIONS:
        raise ValueError(f"unknown purchasing option {option!r}: choose from {OPTIONS}")
    if rate < 0 or instances < 0 or hours_used < 0:
        raise ValueError("rate, instances and hours_used must not be negative")
    if hours_used > hours_in_month:
        raise ValueError(f"hours_used {hours_used} is more than the {hours_in_month} hours in the month")
    if option == "on-demand":
        cost = instances * hours_used * rate
    elif option == "spot":
        cost = instances * hours_used * rate * (1 - price["spot_discount"])
    else:
        cost = instances * hours_in_month * rate * (1 - price[_COMMITMENT_DISCOUNT[option]])
    return round(cost, 2)


def cheapest(rate: float, instances: int, hours_used: float, *, interruptible: bool = False,
             may_change_family: bool = False, hours_in_month: int = 730,
             price: dict = PRICES) -> tuple[str, float]:
    """The cheapest allowed option. A tie keeps the earlier option in OPTIONS."""
    candidates = ["on-demand", "compute savings plan"]
    if not may_change_family:
        candidates.append("standard reserved")
    if interruptible:
        candidates.append("spot")
    costs = [(opt, monthly_cost(opt, rate, instances, hours_used, hours_in_month=hours_in_month, price=price))
             for opt in sorted(candidates, key=OPTIONS.index)]
    best = costs[0]
    for opt, cost in costs[1:]:
        if cost < best[1]:
            best = (opt, cost)
    return best


def break_even_hours(option: str, *, hours_in_month: int = 730, price: dict = PRICES) -> float:
    """Monthly hours of use at which a commitment costs the same as On-Demand."""
    if option not in _COMMITMENT_DISCOUNT:
        raise ValueError(f"{option!r} has no commitment: use 'compute savings plan' or 'standard reserved'")
    return round(hours_in_month * (1 - price[_COMMITMENT_DISCOUNT[option]]), 1)
````

### `_harness/awslib/scaling.py`

````python
"""scaling — Auto Scaling policy maths: target tracking, step and simple scaling, health checks.

This is the reference solution for week 03's drill 03 (and drill 10): finish those drills before you read it.
Rules (docs/research/2026-10-11-compute-facts.md §6): dynamic scaling never leaves [min, max]; target
tracking scales in direct proportion to load and rounds up; step bounds are offsets from the alarm
threshold (above it: lower inclusive, upper exclusive; below it: lower exclusive, upper inclusive);
simple scaling waits out a cooldown (default 300 s) after each action.
"""
from __future__ import annotations

import math

DEFAULT_COOLDOWN = 300


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def _check_bounds(minimum: int, maximum: int) -> None:
    if minimum < 0 or minimum > maximum:
        raise ValueError(f"need 0 <= minimum <= maximum, got {minimum} and {maximum}")


def target_tracking(current: int, metric: float, target: float, minimum: int, maximum: int) -> int:
    """New desired capacity = ceil(current * metric / target), clamped to [minimum, maximum]."""
    _check_bounds(minimum, maximum)
    if current < 0 or target <= 0:
        raise ValueError("current must not be negative and target must be positive")
    if current == 0:
        return minimum
    return _clamp(math.ceil(round(current * metric / target, 9)), minimum, maximum)


def step_scaling(current: int, metric: float, threshold: float,
                 steps: list[tuple[float | None, float | None, int]], minimum: int, maximum: int) -> int:
    """Apply the step whose interval holds the breach (metric - threshold); no match = no change."""
    _check_bounds(minimum, maximum)
    spans = [(-math.inf if lo is None else lo, math.inf if up is None else up) for lo, up, _ in steps]
    for i, (lo_a, up_a) in enumerate(spans):
        if lo_a >= up_a:
            raise ValueError(f"step {i} has a lower bound that is not below its upper bound")
        for lo_b, up_b in spans[i + 1:]:
            if max(lo_a, lo_b) < min(up_a, up_b):
                raise ValueError("step intervals overlap")
    breach = metric - threshold
    for (lower, upper), (_, _, change) in zip(spans, steps):
        matched = lower <= breach < upper if breach >= 0 else lower < breach <= upper
        if matched:
            return _clamp(current + change, minimum, maximum)
    return _clamp(current, minimum, maximum)


def simple_scaling_run(metrics: list[float], start: int, high: float, low: float, change: int,
                       cooldown: int, minimum: int, maximum: int, period: int = 60) -> list[int]:
    """Desired capacity after each metric sample (one per `period` seconds) under a simple scaling
    policy. An action that really changes the capacity starts a cooldown during which alarms are ignored."""
    _check_bounds(minimum, maximum)
    desired = _clamp(start, minimum, maximum)
    last_action: int | None = None
    history = []
    for t, metric in enumerate(metrics):
        now = t * period
        in_cooldown = last_action is not None and now < last_action + cooldown
        if not in_cooldown:
            if metric > high:
                new = _clamp(desired + change, minimum, maximum)
            elif metric < low:
                new = _clamp(desired - change, minimum, maximum)
            else:
                new = desired
            if new != desired:
                desired, last_action = new, now
        history.append(desired)
    return history


def replaces_instance(health_check_type: str, ec2_ok: bool, elb_ok: bool, in_grace_period: bool = False) -> bool:
    """Whether Auto Scaling replaces the instance. "EC2" looks at the EC2 status checks only; "ELB" also
    at the load balancer's. Inside the grace period nothing is replaced (an instance that has left the
    running state is replaced even then — not modelled)."""
    if health_check_type not in ("EC2", "ELB"):
        raise ValueError(f"unknown health check type {health_check_type!r}: use 'EC2' or 'ELB'")
    if in_grace_period:
        return False
    return not ec2_ok if health_check_type == "EC2" else (not ec2_ok or not elb_ok)
````

### `_harness/awslib/elb.py`

````python
"""elb — Application Load Balancer rule matching, cross-zone load balancing and cost.

This is the reference solution for week 03's drills 04–05: finish those drills before you read it.
Rules (docs/research/2026-10-11-compute-facts.md §7): rules are checked in ascending priority and the
default rule last; a rule matches when ALL its conditions match, a condition when ANY of its values
match; up to 3 values per condition and 5 per rule. Host, header and query matching ignore case; path
and method are case-sensitive; `*` matches any run of characters and `?` one character.
"""
from __future__ import annotations

import ipaddress
import re

from . import prices

PRICES = prices.section("ec2")
MAX_VALUES_PER_CONDITION, MAX_VALUES_PER_RULE = 3, 5
MIN_PRIORITY, MAX_PRIORITY = 1, 50000
FIELDS = ("host-header", "path-pattern", "http-request-method", "http-header", "query-string", "source-ip")


def _wild(pattern: str, text: str, *, ignore_case: bool) -> bool:
    regex = "".join(".*" if c == "*" else "." if c == "?" else re.escape(c) for c in pattern)
    return re.fullmatch(regex, text, re.DOTALL | (re.IGNORECASE if ignore_case else 0)) is not None


def _validate(rules: list[dict]) -> list[dict]:
    defaults = [r for r in rules if r.get("priority") == "default"]
    if len(defaults) != 1 or defaults[0].get("conditions"):
        raise ValueError("exactly one rule must have priority 'default' and no conditions")
    numbered = [r for r in rules if r.get("priority") != "default"]
    seen = set()
    for rule in numbered:
        p = rule.get("priority")
        if isinstance(p, bool) or not isinstance(p, int) or not MIN_PRIORITY <= p <= MAX_PRIORITY:
            raise ValueError(f"priority must be an integer from {MIN_PRIORITY} to {MAX_PRIORITY}, got {p!r}")
        if p in seen:
            raise ValueError(f"two rules share priority {p}")
        seen.add(p)
        conditions = rule.get("conditions") or []
        if not conditions:
            raise ValueError(f"rule {p} has no conditions: only the default rule may have none")
        total = 0
        for cond in conditions:
            if cond.get("field") not in FIELDS:
                raise ValueError(f"rule {p}: unknown condition field {cond.get('field')!r}")
            values = cond.get("values") or []
            if not values:
                raise ValueError(f"rule {p}: condition {cond['field']} has no values")
            if len(values) > MAX_VALUES_PER_CONDITION:
                raise ValueError(f"rule {p}: more than {MAX_VALUES_PER_CONDITION} values in one condition")
            total += len(values)
        if total > MAX_VALUES_PER_RULE:
            raise ValueError(f"rule {p}: more than {MAX_VALUES_PER_RULE} values in total")
    return sorted(numbered, key=lambda r: r["priority"]) + defaults


def _condition_matches(cond: dict, request: dict) -> bool:
    field, values = cond["field"], cond["values"]
    if field == "host-header":
        host = request.get("host", "")
        return any(_wild(v, host, ignore_case=True) for v in values)
    if field == "path-pattern":
        path = request.get("path", "").split("?", 1)[0]
        return any(_wild(v, path, ignore_case=False) for v in values)
    if field == "http-request-method":
        return request.get("method", "") in values
    if field == "http-header":
        wanted = cond.get("name", "").lower()
        found = [str(val) for key, val in (request.get("headers") or {}).items() if key.lower() == wanted]
        return any(_wild(v, got, ignore_case=True) for v in values for got in found)
    if field == "query-string":
        pairs = [(str(k), str(v)) for k, v in (request.get("query") or {}).items()]
        for want in values:
            for key, val in pairs:
                if "key" in want and not _wild(want["key"], key, ignore_case=True):
                    continue
                if _wild(want.get("value", "*"), val, ignore_case=True):
                    return True
        return False
    ip = request.get("source_ip")
    if not ip:
        return False
    return any(ipaddress.ip_address(ip) in ipaddress.ip_network(v, strict=False) for v in values)


def match_rule(request: dict, rules: list[dict]):
    """The action of the first rule (lowest priority number first, default last) whose conditions all match."""
    for rule in _validate(rules):
        if all(_condition_matches(c, request) for c in rule.get("conditions") or []):
            return rule["action"]
    raise ValueError("no rule matched")  # unreachable: the default rule has no conditions


def cross_zone_share(targets_per_az: dict[str, int], cross_zone: bool) -> dict[str, float]:
    """Share of all requests that ONE target in each AZ receives (0–1)."""
    if any(n < 0 for n in targets_per_az.values()):
        raise ValueError("target counts must not be negative")
    total = sum(targets_per_az.values())
    if total == 0:
        raise ValueError("there are no targets in any AZ")
    if cross_zone:
        return {az: (1 / total if n else 0.0) for az, n in targets_per_az.items()}
    live = sum(1 for n in targets_per_az.values() if n)
    return {az: (1 / live / n if n else 0.0) for az, n in targets_per_az.items()}


def alb_monthly_cost(lcus: float, hours: int = 730, price: dict = PRICES) -> float:
    """hours * (hourly charge + LCUs * per-LCU-hour charge), rounded to cents."""
    if lcus < 0 or hours < 0:
        raise ValueError("lcus and hours must not be negative")
    return round(hours * (price["alb_per_hour"] + lcus * price["alb_per_lcu_hour"]), 2)
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
````

### `_dev/tests/test_compute_models.py`

````python
import pytest

from _harness.awslib import ec2types, elb, purchasing, scaling


# ---------------------------------------------------------------- ec2types
def test_decode_m7g_2xlarge():
    assert ec2types.decode("m7g.2xlarge") == {
        "series": "m", "category": "general purpose", "generation": 7, "options": ["g"],
        "processor": "AWS Graviton", "size": "2xlarge", "burstable": False, "instance_store": False,
        "bare_metal": False, "flex": False}


def test_decode_c7gn():
    d = ec2types.decode("c7gn.xlarge")
    assert (d["series"], d["generation"], d["options"], d["processor"]) == ("c", 7, ["g", "n"], "AWS Graviton")
    assert d["category"] == "compute optimized"


def test_decode_instance_store():
    d = ec2types.decode("r6id.large")
    assert d["options"] == ["i", "d"] and d["processor"] == "Intel" and d["instance_store"] is True


def test_decode_flex():
    d = ec2types.decode("m7i-flex.large")
    assert d["options"] == ["i", "flex"] and d["flex"] is True


def test_decode_burstable():
    d = ec2types.decode("t4g.micro")
    assert d["burstable"] is True and d["processor"] == "AWS Graviton"


def test_decode_multi_letter_series():
    d = ec2types.decode("inf2.xlarge")
    assert (d["series"], d["category"], d["generation"], d["options"]) == ("inf", "accelerated computing", 2, [])
    assert ec2types.decode("mac2.metal")["series"] == "mac"
    assert ec2types.decode("mac2.metal")["bare_metal"] is True


def test_decode_many_options():
    assert ec2types.decode("x2iedn.xlarge")["options"] == ["i", "e", "d", "n"]


def test_decode_not_stated_and_case():
    assert ec2types.decode("  C7.Large ")["processor"] == "not stated"
    assert ec2types.decode("M7G.LARGE")["series"] == "m"


@pytest.mark.parametrize("bad", ["m7g", "k7g.large", "mg.large", "m0g.large", "m7y.large", "m7g.huge",
                                 "u-6tb1.metal", "m7g.0xlarge", ""])
def test_decode_rejects(bad):
    with pytest.raises(ValueError):
        ec2types.decode(bad)


@pytest.mark.parametrize("args, kwargs, expected", [
    ((8, 32), {}, "m7g.2xlarge"), ((4, 8), {}, "c7g.xlarge"), ((2, 16), {}, "r7g.large"),
    ((2, 5), {}, "m7g.large"), ((16, 64), {"processor": "intel"}, "m7i.4xlarge"), ((1, 4), {}, "m7g.medium"),
    ((4, 16), {"processor": "amd", "generation": 6}, "m6a.xlarge"),
])
def test_choose_type(args, kwargs, expected):
    assert ec2types.choose_type(*args, **kwargs) == expected


@pytest.mark.parametrize("args, kwargs", [
    ((2, 17), {}), ((3, 12), {}), ((6, 24), {}), ((0, 4), {}), ((-4, 8), {}), ((4, 0), {}), ((4, 8), {"processor": "arm"}),
])
def test_choose_type_rejects(args, kwargs):
    with pytest.raises(ValueError):
        ec2types.choose_type(*args, **kwargs)


# -------------------------------------------------------------- purchasing
def test_prices_come_from_toml():
    assert purchasing.PRICES["m7g_large_per_hour"] == 0.0816
    assert purchasing.PRICES["compute_savings_plan_discount"] == 0.31


def test_monthly_cost_each_option():
    rate = 0.1
    assert purchasing.monthly_cost("on-demand", rate, 10, 100) == 100.0
    assert purchasing.monthly_cost("spot", rate, 10, 100) == 30.0
    assert purchasing.monthly_cost("compute savings plan", rate, 10, 100) == round(10 * 730 * 0.1 * 0.69, 2)
    assert purchasing.monthly_cost("standard reserved", rate, 10, 0) == 438.0


def test_commitments_pay_for_unused_hours():
    assert (purchasing.monthly_cost("compute savings plan", 0.0816, 4, 0)
            == purchasing.monthly_cost("compute savings plan", 0.0816, 4, 730))


@pytest.mark.parametrize("args", [("nope", 0.1, 1, 1), ("on-demand", -0.1, 1, 1), ("on-demand", 0.1, -1, 1),
                                  ("on-demand", 0.1, 1, -1), ("on-demand", 0.1, 1, 731)])
def test_monthly_cost_rejects(args):
    with pytest.raises(ValueError):
        purchasing.monthly_cost(*args)


def test_cheapest_light_use_is_on_demand():
    assert purchasing.cheapest(0.1, 1, 100)[0] == "on-demand"


def test_cheapest_steady_use_prefers_standard_ri_unless_family_may_change():
    assert purchasing.cheapest(0.1, 1, 730)[0] == "standard reserved"
    assert purchasing.cheapest(0.1, 1, 730, may_change_family=True)[0] == "compute savings plan"


def test_cheapest_spot_only_if_interruptible():
    assert purchasing.cheapest(0.1, 1, 730)[0] != "spot"
    assert purchasing.cheapest(0.1, 1, 730, interruptible=True) == ("spot", 21.9)


def test_cheapest_tie_keeps_earlier_option():
    assert purchasing.cheapest(0.0, 3, 10, interruptible=True) == ("on-demand", 0.0)


def test_break_even_hours():
    assert purchasing.break_even_hours("compute savings plan") == 503.7
    assert purchasing.break_even_hours("standard reserved") == 438.0
    assert purchasing.break_even_hours("standard reserved", hours_in_month=720) == 432.0


@pytest.mark.parametrize("option", ["on-demand", "spot", "bogus"])
def test_break_even_rejects(option):
    with pytest.raises(ValueError):
        purchasing.break_even_hours(option)


# ----------------------------------------------------------------- scaling
@pytest.mark.parametrize("args, expected", [((4, 90, 50, 2, 10), 8), ((4, 20, 50, 2, 10), 2),
                                            ((10, 100, 50, 2, 12), 12), ((0, 90, 50, 2, 10), 2),
                                            ((3, 50, 50, 1, 10), 3), ((10, 55, 50, 1, 30), 11)])
def test_target_tracking(args, expected):
    assert scaling.target_tracking(*args) == expected


def test_target_tracking_float_error_does_not_round_up():
    assert scaling.target_tracking(3, 0.7 * 10, 7.0, 1, 10) == 3  # 3 * 7.000000000000001 / 7


@pytest.mark.parametrize("args", [(-1, 50, 50, 1, 5), (2, 50, 0, 1, 5), (2, 50, -5, 1, 5), (2, 50, 50, 6, 5), (2, 50, 50, -1, 5)])
def test_target_tracking_rejects(args):
    with pytest.raises(ValueError):
        scaling.target_tracking(*args)


STEPS = [(0, 10, 1), (10, 20, 2), (20, None, 3)]


@pytest.mark.parametrize("metric, expected", [(65, 5), (80, 7), (75, 6), (60, 5), (70, 6), (59, 4)])
def test_step_scaling_above(metric, expected):
    assert scaling.step_scaling(4, metric, 60, STEPS, 1, 10) == expected


def test_step_scaling_below_threshold_bounds():
    steps = [(None, -20, -2), (-20, -10, -1)]
    assert scaling.step_scaling(5, 40, 60, steps, 1, 10) == 3      # breach -20: upper inclusive of the first step, lower exclusive of the second
    assert scaling.step_scaling(5, 30, 60, steps, 1, 10) == 3      # breach -30
    assert scaling.step_scaling(5, 50, 60, steps, 1, 10) == 4      # breach -10: upper inclusive of (-20, -10]
    assert scaling.step_scaling(5, 55, 60, steps, 1, 10) == 5      # breach -5: nothing


def test_step_scaling_clamps_and_negative_change():
    assert scaling.step_scaling(9, 90, 60, STEPS, 1, 10) == 10
    assert scaling.step_scaling(2, 40, 60, [(None, 0, -5)], 2, 10) == 2


def test_step_scaling_overlap_rejected():
    with pytest.raises(ValueError):
        scaling.step_scaling(4, 70, 60, [(0, 15, 1), (10, None, 2)], 1, 10)
    with pytest.raises(ValueError):
        scaling.step_scaling(4, 70, 60, [(0, None, 1), (5, 10, 2)], 1, 10)
    with pytest.raises(ValueError):
        scaling.step_scaling(4, 70, 60, STEPS, 5, 2)


def test_simple_scaling_cooldown_example():
    assert scaling.simple_scaling_run([90] * 7, 2, 70, 30, 1, 300, 1, 10) == [3, 3, 3, 3, 3, 4, 4]


def test_simple_scaling_no_cooldown_and_scale_in():
    assert scaling.simple_scaling_run([90, 90, 90], 2, 70, 30, 1, 0, 1, 10) == [3, 4, 5]
    assert scaling.simple_scaling_run([10, 10, 50, 10], 3, 70, 30, 2, 0, 1, 10) == [1, 1, 1, 1]


def test_simple_scaling_clamp_does_not_start_cooldown():
    # at max already: no change, so no cooldown; once load drops the scale-in happens at once
    assert scaling.simple_scaling_run([90, 10], 5, 70, 30, 1, 300, 1, 5) == [5, 4]


def test_simple_scaling_rejects_bad_bounds():
    with pytest.raises(ValueError):
        scaling.simple_scaling_run([1], 2, 70, 30, 1, 300, 5, 2)


def test_default_cooldown_constant():
    assert scaling.DEFAULT_COOLDOWN == 300


@pytest.mark.parametrize("kind, ec2_ok, elb_ok, grace, expected", [
    ("EC2", True, False, False, False), ("EC2", False, True, False, True),
    ("ELB", True, False, False, True), ("ELB", False, True, False, True), ("ELB", True, True, False, False),
    ("ELB", False, False, True, False),
])
def test_replaces_instance(kind, ec2_ok, elb_ok, grace, expected):
    assert scaling.replaces_instance(kind, ec2_ok, elb_ok, grace) is expected


def test_replaces_instance_rejects_unknown_type():
    with pytest.raises(ValueError):
        scaling.replaces_instance("HTTP", True, True)


# --------------------------------------------------------------------- elb
REQ = {"host": "api.shortly.example", "path": "/api/links", "method": "GET",
       "headers": {"User-Agent": "Mozilla Mobile Safari"}, "query": {"lang": "en", "Version": "V1"},
       "source_ip": "203.0.113.7"}


def rule(priority, action, *conditions):
    return {"priority": priority, "conditions": list(conditions), "action": action}


DEFAULT = {"priority": "default", "conditions": [], "action": "default"}


def test_match_rule_priority_order_and_default():
    rules = [DEFAULT, rule(20, "late", {"field": "path-pattern", "values": ["/api/*"]}),
             rule(10, "early", {"field": "host-header", "values": ["*.shortly.example"]})]
    assert elb.match_rule(REQ, rules) == "early"
    assert elb.match_rule({**REQ, "host": "other.test"}, rules) == "late"
    assert elb.match_rule({"host": "x.test", "path": "/"}, rules) == "default"


def test_match_rule_all_conditions_and_any_value():
    r = rule(1, "hit", {"field": "path-pattern", "values": ["/nope", "/api/*"]},
             {"field": "http-request-method", "values": ["POST"]})
    assert elb.match_rule(REQ, [r, DEFAULT]) == "default"
    assert elb.match_rule({**REQ, "method": "POST"}, [r, DEFAULT]) == "hit"


def test_host_header_case_and_wildcard():
    r = rule(1, "hit", {"field": "host-header", "values": ["*.EXAMPLE.com"]})
    assert elb.match_rule({"host": "test.example.com"}, [r, DEFAULT]) == "hit"
    assert elb.match_rule({"host": "example.com"}, [r, DEFAULT]) == "default"


def test_path_is_case_sensitive_and_ignores_query():
    r = rule(1, "hit", {"field": "path-pattern", "values": ["/api/?inks"]})
    assert elb.match_rule({"path": "/api/links"}, [r, DEFAULT]) == "hit"
    assert elb.match_rule({"path": "/API/links"}, [r, DEFAULT]) == "default"
    assert elb.match_rule({"path": "/api/links?x=1"}, [r, DEFAULT]) == "hit"


def test_method_is_exact_and_case_sensitive():
    r = rule(1, "hit", {"field": "http-request-method", "values": ["GET"]})
    assert elb.match_rule({"method": "GET"}, [r, DEFAULT]) == "hit"
    assert elb.match_rule({"method": "get"}, [r, DEFAULT]) == "default"
    star = rule(1, "hit", {"field": "http-request-method", "values": ["G*"]})
    assert elb.match_rule({"method": "GET"}, [star, DEFAULT]) == "default"


def test_http_header_name_and_value_ignore_case():
    r = rule(1, "hit", {"field": "http-header", "name": "user-agent", "values": ["*mobile*"]})
    assert elb.match_rule(REQ, [r, DEFAULT]) == "hit"
    assert elb.match_rule({"headers": {}}, [r, DEFAULT]) == "default"
    assert elb.match_rule({}, [r, DEFAULT]) == "default"


def test_query_string_key_value_and_value_only():
    both = rule(1, "hit", {"field": "query-string", "values": [{"key": "VERSION", "value": "v1"}]})
    assert elb.match_rule(REQ, [both, DEFAULT]) == "hit"
    wrong_key = rule(1, "hit", {"field": "query-string", "values": [{"key": "lang", "value": "v1"}]})
    assert elb.match_rule(REQ, [wrong_key, DEFAULT]) == "default"
    value_only = rule(1, "hit", {"field": "query-string", "values": [{"value": "E?"}]})
    assert elb.match_rule(REQ, [value_only, DEFAULT]) == "hit"


def test_source_ip():
    r = rule(1, "hit", {"field": "source-ip", "values": ["203.0.113.0/24"]})
    assert elb.match_rule(REQ, [r, DEFAULT]) == "hit"
    assert elb.match_rule({**REQ, "source_ip": "198.51.100.1"}, [r, DEFAULT]) == "default"
    assert elb.match_rule({}, [r, DEFAULT]) == "default"


def test_rule_validation():
    cond = {"field": "path-pattern", "values": ["/a"]}
    bad_sets = [
        [rule(1, "x", cond)],                                        # no default
        [DEFAULT, DEFAULT],                                          # two defaults
        [{**DEFAULT, "conditions": [cond]}],                         # default with conditions
        [DEFAULT, rule(1, "x", cond), rule(1, "y", cond)],           # duplicate priority
        [DEFAULT, rule(0, "x", cond)],                               # below 1
        [DEFAULT, rule(50001, "x", cond)],                           # above 50000
        [DEFAULT, rule(True, "x", cond)],                            # bool
        [DEFAULT, rule(1.5, "x", cond)],                             # not an int
        [DEFAULT, rule(1, "x")],                                     # numeric rule, no conditions
        [DEFAULT, rule(1, "x", {"field": "nope", "values": ["a"]})],  # unknown field
        [DEFAULT, rule(1, "x", {"field": "host-header", "values": []})],
        [DEFAULT, rule(1, "x", {"field": "host-header", "values": list("abcd")})],  # 4 > 3
        [DEFAULT, rule(1, "x", {"field": "host-header", "values": list("abc")},
                       {"field": "path-pattern", "values": list("abc")})],           # 6 > 5
    ]
    for rules in bad_sets:
        with pytest.raises(ValueError):
            elb.match_rule(REQ, rules)


def test_rule_limits_boundaries_accepted():
    r = rule(50000, "ok", {"field": "host-header", "values": list("abc")},
             {"field": "path-pattern", "values": list("de")})
    assert elb.match_rule(REQ, [r, DEFAULT]) == "default"


def test_cross_zone_docs_example():
    assert elb.cross_zone_share({"a": 2, "b": 8}, True) == {"a": 0.1, "b": 0.1}
    assert elb.cross_zone_share({"a": 2, "b": 8}, False) == {"a": 0.25, "b": 0.0625}


def test_cross_zone_empty_az_is_out_of_dns():
    assert elb.cross_zone_share({"a": 0, "b": 4}, False) == {"a": 0.0, "b": 0.25}
    assert elb.cross_zone_share({"a": 0, "b": 4}, True) == {"a": 0.0, "b": 0.25}


@pytest.mark.parametrize("counts", [{"a": 0, "b": 0}, {}, {"a": -1, "b": 3}])
def test_cross_zone_rejects(counts):
    with pytest.raises(ValueError):
        elb.cross_zone_share(counts, True)


def test_alb_monthly_cost():
    assert elb.alb_monthly_cost(0) == 16.43
    assert elb.alb_monthly_cost(10) == round(730 * (0.0225 + 10 * 0.008), 2) == 74.83
    assert elb.alb_monthly_cost(1, hours=100) == 3.05


@pytest.mark.parametrize("args", [(-1,), (1, -5)])
def test_alb_monthly_cost_rejects(args):
    with pytest.raises(ValueError):
        elb.alb_monthly_cost(*args)
````

### `_dev/mutants/m03.py`

````python
"""Wrong versions of the M03 snapshot — exact text edits applied to a copy of course_project/solutions/m03."""
COMPUTE = "infra/compute.yaml"
HEALTHZ_RULE = """  HealthzRule:
    Type: AWS::ElasticLoadBalancingV2::ListenerRule
    Properties:
      ListenerArn: !Ref HttpListener
      Priority: 10
      Conditions:
        - {Field: path-pattern, PathPatternConfig: {Values: [/healthz]}}
      Actions:
        - Type: fixed-response
          FixedResponseConfig: {StatusCode: '404', ContentType: text/plain, MessageBody: not found}

"""
HTTPS_LISTENER = """  HttpsListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      LoadBalancerArn: !Ref LoadBalancer
      Port: 443
      Protocol: HTTPS
      Certificates:
        - CertificateArn: arn:aws:acm:us-east-1:111122223333:certificate/12345678-1234-1234-1234-123456789012
      DefaultActions:
        - {Type: forward, TargetGroupArn: !Ref AppTargetGroup}

"""
MUTANTS = [
    {"id": "imdsv1-allowed", "edits": {COMPUTE: [["HttpTokens: required", "HttpTokens: optional"]]}},
    {"id": "hop-limit-3", "edits": {COMPUTE: [["HttpPutResponseHopLimit: 1", "HttpPutResponseHopLimit: 3"]]}},
    {"id": "ec2-health-checks", "edits": {COMPUTE: [["HealthCheckType: ELB", "HealthCheckType: EC2"]]}},
    {"id": "x86-type-allowed", "edits": {COMPUTE: [["AllowedValues: [t4g.small, t4g.medium, m7g.large, c7g.large]",
                                                    "AllowedValues: [t4g.small, t4g.medium, m7g.large, c7g.large, m7i.large]"]]}},
    {"id": "ssh-key", "edits": {COMPUTE: [["        InstanceType: !Ref InstanceType\n", "        InstanceType: !Ref InstanceType\n        KeyName: shortly\n"]]}},
    {"id": "prod-single-instance", "edits": {COMPUTE: [["MinSize: !If [IsProd, 2, 1]", "MinSize: !If [IsProd, 1, 1]"]]}},
    {"id": "healthz-public", "edits": {COMPUTE: [[HEALTHZ_RULE, ""]]}},
    {"id": "scale-at-95-percent", "edits": {COMPUTE: [["TargetValue: 50", "TargetValue: 95"]]}},
    {"id": "app-not-inlined", "edits": {COMPUTE: [["            LINKS = {}\n", ""]]}},
    {"id": "drain-300", "edits": {COMPUTE: [["Value: '30'}", "Value: '300'}"]]}},
    {"id": "https-too-early", "edits": {COMPUTE: [["  HealthzRule:\n", HTTPS_LISTENER + "  HealthzRule:\n"]]}},
    {"id": "duplicate-priority", "edits": {COMPUTE: [["Priority: 20", "Priority: 10"]]}},
    {"id": "grace-period-zero", "edits": {COMPUTE: [["HealthCheckGracePeriod: 120", "HealthCheckGracePeriod: 0"]]}},
    {"id": "service-not-enabled", "edits": {COMPUTE: [["            systemctl enable --now shortly\n", "            systemctl start shortly\n"]]}},
]
````

### `_dev/mutants/week03.py`

````python
"""Deliberately wrong implementations for week 03 — each must be caught by its drill."""
MUTANTS = [
    {"id": "g-means-graviton", "drill": 1, "code": '''
from _harness.awslib import ec2types as _ref
def decode(instance_type):
    got = _ref.decode(instance_type)
    if "g" in instance_type.lower().split(".")[0]:
        got["processor"] = "AWS Graviton"
    return got
'''},
    {"id": "commitment-by-the-hour", "drill": 2, "code": '''
def monthly_cost(option, rate, instances, hours_used, *, hours_in_month=730, price=PRICES):
    if option not in OPTIONS or min(rate, instances, hours_used) < 0 or hours_used > hours_in_month:
        raise ValueError(option)
    factor = {"on-demand": 1.0, "spot": 1 - price["spot_discount"],
              "compute savings plan": 1 - price["compute_savings_plan_discount"],
              "standard reserved": 1 - price["standard_ri_discount"]}[option]
    return round(instances * hours_used * rate * factor, 2)
'''},
    {"id": "round-to-nearest", "drill": 3, "code": '''
def target_tracking(current, metric, target, minimum, maximum):
    if minimum < 0 or minimum > maximum or current < 0 or target <= 0:
        raise ValueError("bad input")
    if current == 0:
        return minimum
    return max(minimum, min(maximum, round(current * metric / target)))
'''},
    {"id": "list-order", "drill": 4, "code": '''
from _harness.awslib import elb as _ref
def match_rule(request, rules):
    _ref._validate(rules)
    ordered = [r for r in rules if r["priority"] != "default"] + [r for r in rules if r["priority"] == "default"]
    for rule in ordered:
        if all(_ref._condition_matches(c, request) for c in rule.get("conditions") or []):
            return rule["action"]
'''},
    {"id": "per-target-split", "drill": 5, "code": '''
def cross_zone_share(targets_per_az, cross_zone):
    if any(n < 0 for n in targets_per_az.values()):
        raise ValueError("negative")
    total = sum(targets_per_az.values())
    if total == 0:
        raise ValueError("no targets")
    return {az: (1 / total if n else 0.0) for az, n in targets_per_az.items()}
'''},
    {"id": "imdsv1-allowed", "drill": 6, "code": '''
def create_web_fleet(ec2, autoscaling, subnet_ids, sg_id, profile_name, ami_id):
    template = ec2.create_launch_template(LaunchTemplateName="shortly-web", LaunchTemplateData={
        "ImageId": ami_id, "InstanceType": "t4g.small", "IamInstanceProfile": {"Name": profile_name},
        "SecurityGroupIds": [sg_id],
        "MetadataOptions": {"HttpTokens": "optional", "HttpPutResponseHopLimit": 1, "HttpEndpoint": "enabled"}})["LaunchTemplate"]["LaunchTemplateId"]
    autoscaling.create_auto_scaling_group(AutoScalingGroupName="shortly-web", LaunchTemplate={"LaunchTemplateId": template, "Version": "$Latest"},
        MinSize=2, MaxSize=6, DesiredCapacity=2, VPCZoneIdentifier=",".join(subnet_ids), HealthCheckType="ELB", HealthCheckGracePeriod=120)
    autoscaling.put_scaling_policy(AutoScalingGroupName="shortly-web", PolicyName="cpu-50", PolicyType="TargetTrackingScaling",
        TargetTrackingConfiguration={"PredefinedMetricSpecification": {"PredefinedMetricType": "ASGAverageCPUUtilization"}, "TargetValue": 50.0})
    return {"launch_template_id": template, "asg_name": "shortly-web"}
'''},
    {"id": "healthz-exposed", "drill": 7, "code": '''
def build_alb(elbv2, vpc_id, subnet_ids, sg_id):
    tg = elbv2.create_target_group(Name="shortly-app", Protocol="HTTP", Port=8000, VpcId=vpc_id, TargetType="instance",
                                   HealthCheckPath="/healthz", Matcher={"HttpCode": "200"})["TargetGroups"][0]["TargetGroupArn"]
    lb = elbv2.create_load_balancer(Name="shortly-alb", Subnets=list(subnet_ids), SecurityGroups=[sg_id],
                                    Scheme="internet-facing", Type="application")["LoadBalancers"][0]["LoadBalancerArn"]
    listener = elbv2.create_listener(LoadBalancerArn=lb, Protocol="HTTP", Port=80,
                                     DefaultActions=[{"Type": "forward", "TargetGroupArn": tg}])["Listeners"][0]["ListenerArn"]
    elbv2.create_rule(ListenerArn=listener, Priority=20, Conditions=[{"Field": "path-pattern", "Values": ["/api/*"]}],
                      Actions=[{"Type": "forward", "TargetGroupArn": tg}])
    return {"lb_arn": lb, "tg_arn": tg, "listener_arn": listener}
'''},
    {"id": "grace-period-forgotten", "drill": 8, "code": '''
def fleet_settings(subnet_ids, launch_template_id):
    return {
        "launch_template_data": {"InstanceType": "t4g.small",
            "MetadataOptions": {"HttpTokens": "required", "HttpPutResponseHopLimit": 1, "HttpEndpoint": "enabled"}},
        "asg": {"MinSize": 2, "MaxSize": 6, "DesiredCapacity": 2,
            "LaunchTemplate": {"LaunchTemplateId": launch_template_id, "Version": "$Latest"},
            "VPCZoneIdentifier": ",".join(subnet_ids), "TargetGroupARNs": [TARGET_GROUP_ARN],
            "HealthCheckType": "ELB", "HealthCheckGracePeriod": 0},
    }
'''},
    {"id": "seven-in-total", "drill": 9, "code": '''
def max_spread_instances(azs):
    if azs < 1:
        raise ValueError("need an AZ")
    return 7
'''},
    {"id": "opposite-predictions", "drill": 10, "code": '''
PREDICTIONS = {1: 7, 2: 3, 3: "yes", 4: "no", 5: 25, 6: "forward api"}
'''},
]
````

### `_dev/tests/test_app.py`

````python
import http.client
import importlib.util
import json
import re
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[2] / "course_project" / "app" / "app.py"


@pytest.fixture(scope="module")
def server():
    spec = importlib.util.spec_from_file_location("shortly_app", APP)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), module.Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd.server_address[1]
    httpd.shutdown()
    httpd.server_close()


def call(port, method, path, body=None, raw=None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    data = raw if raw is not None else (json.dumps(body) if body is not None else None)
    conn.request(method, path, body=data, headers={"Content-Type": "application/json"} if data else {})
    resp = conn.getresponse()
    text = resp.read().decode("utf-8")
    conn.close()
    return resp.status, dict(resp.getheaders()), text


def test_healthz(server):
    status, headers, text = call(server, "GET", "/healthz")
    assert (status, text) == (200, "ok") and headers["Content-Type"].startswith("text/plain")


def test_create_get_and_redirect(server):
    status, _, text = call(server, "POST", "/api/links", {"url": "https://example.com/a?b=1"})
    created = json.loads(text)
    assert status == 201 and re.fullmatch(r"[A-Za-z0-9]{7}", created["code"])
    assert created["url"] == "https://example.com/a?b=1"
    status, _, text = call(server, "GET", f"/api/links/{created['code']}")
    assert status == 200 and json.loads(text) == created
    status, headers, _ = call(server, "GET", f"/{created['code']}")
    assert status == 302 and headers["Location"] == "https://example.com/a?b=1"


@pytest.mark.parametrize("body, raw", [({}, None), ({"url": "ftp://x.example"}, None), ({"url": "nope"}, None),
                                       ({"url": 5}, None), (None, "{not json")])
def test_bad_requests(server, body, raw):
    status, _, text = call(server, "POST", "/api/links", body, raw)
    assert status == 400 and "error" in json.loads(text)


def test_unknown_paths(server):
    assert call(server, "GET", "/api/links/zzzzzzz")[0] == 404
    assert json.loads(call(server, "GET", "/api/links/zzzzzzz")[2])["error"]
    assert call(server, "GET", "/zzzzzzz")[0] == 404
    assert call(server, "GET", "/a/b/c")[0] == 404
    assert call(server, "POST", "/elsewhere", {"url": "https://example.com"})[0] == 404


def test_file_is_safe_to_paste_into_cloudformation_sub():
    text = APP.read_text(encoding="utf-8")
    assert "${" not in text and "\t" not in text
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
    assert list(labclean.FINDERS) == [
        "s3_buckets", "autoscaling_groups", "load_balancers", "target_groups", "ec2_instances", "launch_templates",
        "nat_gateways", "elastic_ips", "security_groups", "vpcs", "iam_roles", "iam_users", "iam_policies"]


def test_unknown_kind_rejected(aws):
    with pytest.raises(ValueError, match="unknown resource kind"):
        run(aws, ["load_balancers", "lambda_functions"])
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


def render(value: Any, params: dict | None = None, pseudo: dict | None = None, conditions: dict | None = None) -> Any:
    """Resolve intrinsic functions with test parameter values:
    Ref, Fn::Sub, Fn::Join, Fn::Split, Fn::GetAtt, Fn::If, Fn::Select, Fn::GetAZs, Fn::Cidr,
    Fn::ImportValue, Fn::Base64.
    A Ref to a resource renders as its logical id; Fn::GetAtt as "Logical.Attr"; Fn::ImportValue as
    "import:<name>"; Fn::GetAZs as the Region's names with letters a–f. Fn::If needs `conditions`
    (see evaluate_conditions). Fn::Split gives the list of pieces of a rendered string (a rendered
    list is an error). Fn::Base64 renders as its rendered input, NOT encoded, so a test can read the
    user data. {"Ref": "AWS::NoValue"} removes the property or list item."""
    result = _render(value, params or {}, {**DEFAULT_PSEUDO, **(pseudo or {})}, conditions)
    return None if result is NOVALUE else result


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
        found[name] = render(res, params, pseudo, conditions)
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
                return render(value, params, pseudo, conditions)
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
    return render(docs, params, pseudo, evaluate_conditions(template, params, pseudo))


def trust_policy(template: dict, logical_id: str, params=None, pseudo=None) -> dict:
    document = _role(template, logical_id).get("AssumeRolePolicyDocument") or {}
    params = parameter_values(template, params)
    return render(document, params, pseudo, evaluate_conditions(template, params, pseudo))
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
    for page in s3.get_paginator("list_object_versions").paginate(Bucket=name):
        doomed = [{"Key": v["Key"], "VersionId": v["VersionId"]} for v in page.get("Versions", []) + page.get("DeleteMarkers", [])]
        for start in range(0, len(doomed), 1000):
            s3.delete_objects(Bucket=name, Delete={"Objects": doomed[start:start + 1000], "Quiet": True})
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


# Order matters: scaling and load balancing before the EC2 things they use; EC2 before VPCs;
# IAM roles and users before customer-managed policies.
FINDERS = {
    "s3_buckets": find_s3_buckets,
    "autoscaling_groups": find_autoscaling_groups,  # first: stops it launching replacements while we delete instances
    "load_balancers": find_load_balancers,          # before target groups (a listener holds them) and security groups (its network interfaces use them)
    "target_groups": find_target_groups,            # after the load balancers that forward to them
    "ec2_instances": find_ec2_instances,            # instances before their VPC
    "launch_templates": find_launch_templates,      # after the ASG that uses it (and the instances)
    "nat_gateways": find_nat_gateways,              # NAT gateways before the Elastic IPs they hold
    "elastic_ips": find_elastic_ips,
    "security_groups": find_security_groups,        # after everything that holds a group: instances, load balancers, NAT; before the VPC
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
        except Exception as exc:
            failures += 1
            print(f"✘ {item.kind} {item.name}: {_error_code(exc)}")
    print("Done." if not failures else f"Done with {failures} problem(s) — fix them in the console or run again.")
    return 1 if failures else 0
````

### `course_project/app/app.py`

````python
"""shortly - a tiny URL shortener (standard library only, runs on Python 3.9+).

Links live in a dict in memory, so they vanish when the process restarts and each server
has its own copy. Milestone M05 moves them into a database.

    PORT=8000 python3 app.py
"""
import json
import os
import random
import string
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

LINKS = {}
ALPHABET = string.ascii_letters + string.digits


def new_code():
    while True:
        code = "".join(random.choice(ALPHABET) for _ in range(7))
        if code not in LINKS:
            return code


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, body, content_type="application/json", headers=None):
        data = (json.dumps(body) if content_type == "application/json" else body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/healthz":
            self.reply(200, "ok", "text/plain")
        elif path.startswith("/api/links/"):
            code = path[len("/api/links/"):]
            if code in LINKS:
                self.reply(200, {"code": code, "url": LINKS[code]})
            else:
                self.reply(404, {"error": "unknown code"})
        elif path.count("/") == 1 and path[1:] in LINKS:
            self.reply(302, "", "text/plain", {"Location": LINKS[path[1:]]})
        else:
            self.reply(404, "not found", "text/plain")

    def do_POST(self):
        if self.path.split("?")[0] != "/api/links":
            return self.reply(404, "not found", "text/plain")
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
            url = body["url"]
            parts = urlparse(url if isinstance(url, str) else "")
            if parts.scheme not in ("http", "https") or not parts.netloc:
                raise ValueError("url must start with http:// or https://")
        except (ValueError, KeyError, TypeError) as exc:
            return self.reply(400, {"error": "send JSON like {\"url\": \"https://example.com\"}: %s" % exc})
        code = new_code()
        LINKS[code] = url
        self.reply(201, {"code": code, "url": url})

    def log_message(self, format, *args):
        print("%s %s" % (self.command, self.path))


def main():
    port = int(os.environ.get("PORT", "8000"))
    print("shortly listening on port %d" % port)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
````

### `course_project/solutions/m03/app/app.py`

````python
"""shortly - a tiny URL shortener (standard library only, runs on Python 3.9+).

Links live in a dict in memory, so they vanish when the process restarts and each server
has its own copy. Milestone M05 moves them into a database.

    PORT=8000 python3 app.py
"""
import json
import os
import random
import string
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

LINKS = {}
ALPHABET = string.ascii_letters + string.digits


def new_code():
    while True:
        code = "".join(random.choice(ALPHABET) for _ in range(7))
        if code not in LINKS:
            return code


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, body, content_type="application/json", headers=None):
        data = (json.dumps(body) if content_type == "application/json" else body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/healthz":
            self.reply(200, "ok", "text/plain")
        elif path.startswith("/api/links/"):
            code = path[len("/api/links/"):]
            if code in LINKS:
                self.reply(200, {"code": code, "url": LINKS[code]})
            else:
                self.reply(404, {"error": "unknown code"})
        elif path.count("/") == 1 and path[1:] in LINKS:
            self.reply(302, "", "text/plain", {"Location": LINKS[path[1:]]})
        else:
            self.reply(404, "not found", "text/plain")

    def do_POST(self):
        if self.path.split("?")[0] != "/api/links":
            return self.reply(404, "not found", "text/plain")
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
            url = body["url"]
            parts = urlparse(url if isinstance(url, str) else "")
            if parts.scheme not in ("http", "https") or not parts.netloc:
                raise ValueError("url must start with http:// or https://")
        except (ValueError, KeyError, TypeError) as exc:
            return self.reply(400, {"error": "send JSON like {\"url\": \"https://example.com\"}: %s" % exc})
        code = new_code()
        LINKS[code] = url
        self.reply(201, {"code": code, "url": url})

    def log_message(self, format, *args):
        print("%s %s" % (self.command, self.path))


def main():
    port = int(os.environ.get("PORT", "8000"))
    print("shortly listening on port %d" % port)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
````

### `course_project/solutions/m03/infra/compute.yaml`

````yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: shortly-infra M03 - compute (load balancer, launch template, Auto Scaling group)

Parameters:
  Prefix:
    Type: String
    Default: shortly
    AllowedPattern: '[a-z][a-z0-9-]{1,20}'
  Env:
    Type: String
    AllowedValues: [lab, prod]
  InstanceType:
    Type: String
    Default: t4g.small
    AllowedValues: [t4g.small, t4g.medium, m7g.large, c7g.large]
  ImageId:
    Type: AWS::SSM::Parameter::Value<AWS::EC2::Image::Id>
    Default: /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64

Conditions:
  IsProd: !Equals [!Ref Env, prod]

Resources:
  LoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: !Sub '${Prefix}-alb'
      Type: application
      Scheme: internet-facing
      Subnets: !Split [',', !ImportValue {'Fn::Sub': '${Prefix}-public-subnet-ids'}]
      SecurityGroups: [!ImportValue {'Fn::Sub': '${Prefix}-alb-sg-id'}]

  AppTargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Name: !Sub '${Prefix}-app'
      Protocol: HTTP
      Port: 8000
      VpcId: !ImportValue {'Fn::Sub': '${Prefix}-vpc-id'}
      TargetType: instance
      HealthCheckPath: /healthz
      Matcher: {HttpCode: '200'}
      TargetGroupAttributes:
        - {Key: deregistration_delay.timeout_seconds, Value: '30'}

  HttpListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      LoadBalancerArn: !Ref LoadBalancer
      Port: 80
      Protocol: HTTP
      DefaultActions:
        - {Type: forward, TargetGroupArn: !Ref AppTargetGroup}

  HealthzRule:
    Type: AWS::ElasticLoadBalancingV2::ListenerRule
    Properties:
      ListenerArn: !Ref HttpListener
      Priority: 10
      Conditions:
        - {Field: path-pattern, PathPatternConfig: {Values: [/healthz]}}
      Actions:
        - Type: fixed-response
          FixedResponseConfig: {StatusCode: '404', ContentType: text/plain, MessageBody: not found}

  ApiRule:
    Type: AWS::ElasticLoadBalancingV2::ListenerRule
    Properties:
      ListenerArn: !Ref HttpListener
      Priority: 20
      Conditions:
        - {Field: path-pattern, PathPatternConfig: {Values: [/api/*]}}
      Actions:
        - {Type: forward, TargetGroupArn: !Ref AppTargetGroup}

  AppLaunchTemplate:
    Type: AWS::EC2::LaunchTemplate
    Properties:
      LaunchTemplateName: !Sub '${Prefix}-app'
      LaunchTemplateData:
        ImageId: !Ref ImageId
        InstanceType: !Ref InstanceType
        IamInstanceProfile:
          Name: !ImportValue {'Fn::Sub': '${Prefix}-app-instance-profile'}
        SecurityGroupIds: [!ImportValue {'Fn::Sub': '${Prefix}-app-sg-id'}]
        MetadataOptions:
          HttpTokens: required
          HttpPutResponseHopLimit: 1
          HttpEndpoint: enabled
        UserData:
          Fn::Base64: |
            #!/bin/bash
            set -euo pipefail
            useradd --system --no-create-home shortly || true
            mkdir -p /opt/shortly
            cat > /opt/shortly/app.py <<'EOF'
            """shortly - a tiny URL shortener (standard library only, runs on Python 3.9+).

            Links live in a dict in memory, so they vanish when the process restarts and each server
            has its own copy. Milestone M05 moves them into a database.

                PORT=8000 python3 app.py
            """
            import json
            import os
            import random
            import string
            from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
            from urllib.parse import urlparse

            LINKS = {}
            ALPHABET = string.ascii_letters + string.digits


            def new_code():
                while True:
                    code = "".join(random.choice(ALPHABET) for _ in range(7))
                    if code not in LINKS:
                        return code


            class Handler(BaseHTTPRequestHandler):
                def reply(self, status, body, content_type="application/json", headers=None):
                    data = (json.dumps(body) if content_type == "application/json" else body).encode("utf-8")
                    self.send_response(status)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Length", str(len(data)))
                    for name, value in (headers or {}).items():
                        self.send_header(name, value)
                    self.end_headers()
                    self.wfile.write(data)

                def do_GET(self):
                    path = self.path.split("?")[0]
                    if path == "/healthz":
                        self.reply(200, "ok", "text/plain")
                    elif path.startswith("/api/links/"):
                        code = path[len("/api/links/"):]
                        if code in LINKS:
                            self.reply(200, {"code": code, "url": LINKS[code]})
                        else:
                            self.reply(404, {"error": "unknown code"})
                    elif path.count("/") == 1 and path[1:] in LINKS:
                        self.reply(302, "", "text/plain", {"Location": LINKS[path[1:]]})
                    else:
                        self.reply(404, "not found", "text/plain")

                def do_POST(self):
                    if self.path.split("?")[0] != "/api/links":
                        return self.reply(404, "not found", "text/plain")
                    try:
                        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
                        url = body["url"]
                        parts = urlparse(url if isinstance(url, str) else "")
                        if parts.scheme not in ("http", "https") or not parts.netloc:
                            raise ValueError("url must start with http:// or https://")
                    except (ValueError, KeyError, TypeError) as exc:
                        return self.reply(400, {"error": "send JSON like {\"url\": \"https://example.com\"}: %s" % exc})
                    code = new_code()
                    LINKS[code] = url
                    self.reply(201, {"code": code, "url": url})

                def log_message(self, format, *args):
                    print("%s %s" % (self.command, self.path))


            def main():
                port = int(os.environ.get("PORT", "8000"))
                print("shortly listening on port %d" % port)
                ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


            if __name__ == "__main__":
                main()
            EOF
            cat > /etc/systemd/system/shortly.service <<'EOF'
            [Unit]
            Description=shortly URL shortener
            After=network-online.target
            [Service]
            User=shortly
            Environment=PORT=8000
            ExecStart=/usr/bin/python3 /opt/shortly/app.py
            Restart=always
            [Install]
            WantedBy=multi-user.target
            EOF
            systemctl daemon-reload
            systemctl enable --now shortly

  AppAutoScalingGroup:
    Type: AWS::AutoScaling::AutoScalingGroup
    Properties:
      AutoScalingGroupName: !Sub '${Prefix}-app'
      LaunchTemplate:
        LaunchTemplateId: !Ref AppLaunchTemplate
        Version: !GetAtt AppLaunchTemplate.LatestVersionNumber
      VPCZoneIdentifier: !Split [',', !ImportValue {'Fn::Sub': '${Prefix}-app-subnet-ids'}]
      MinSize: !If [IsProd, 2, 1]
      MaxSize: !If [IsProd, 6, 2]
      HealthCheckType: ELB
      HealthCheckGracePeriod: 120
      TargetGroupARNs: [!Ref AppTargetGroup]
      Tags:
        - {Key: Name, Value: !Sub '${Prefix}-app', PropagateAtLaunch: true}

  CpuTargetTracking:
    Type: AWS::AutoScaling::ScalingPolicy
    Properties:
      AutoScalingGroupName: !Ref AppAutoScalingGroup
      PolicyType: TargetTrackingScaling
      TargetTrackingConfiguration:
        PredefinedMetricSpecification: {PredefinedMetricType: ASGAverageCPUUtilization}
        TargetValue: 50

Outputs:
  AlbDnsName:
    Value: !GetAtt LoadBalancer.DNSName
    Export: {Name: !Sub '${Prefix}-alb-dns-name'}
  AlbArn:
    Value: !Ref LoadBalancer
    Export: {Name: !Sub '${Prefix}-alb-arn'}
  AppTargetGroupArn:
    Value: !Ref AppTargetGroup
    Export: {Name: !Sub '${Prefix}-app-tg-arn'}
  AppAsgName:
    Value: !Ref AppAutoScalingGroup
    Export: {Name: !Sub '${Prefix}-app-asg-name'}
````

### `course_project/solutions/m03/README.md`

````markdown
# shortly-infra

The infrastructure-as-code for Shortly, the URL shortener you build up across the course. Each milestone adds one layer of CloudFormation templates, with parameter files for the lab and prod environments.

## Layers

| Layer | What it holds | Milestone |
|-------|---------------|-----------|
| `iam` | Roles for the app, the click consumer, the deployer and the auditor | M01 |
| `network` | VPC, three subnet tiers in two AZs, NAT, security groups, S3/DynamoDB endpoints, flow logs | M02 |
| `compute` | Application Load Balancer, launch template (IMDSv2), Auto Scaling group, listener rules | M03 |

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

## Check it

Run the milestone tests with the course venv:

```
python run_milestone.py 2
```

## Deploy (optional)

Deploying to a real account is optional; see the course's `DEPLOY.md`. The network stack costs money while it runs (NAT gateways and their public IPv4 addresses are billed by the hour).
````

### `course_project/tests/m03/test_m03_1_load_balancer.py`

````python
"""M03.1 — the Application Load Balancer and the target group behind it."""


def props(res, name, type_):
    assert res.get(name, {}).get("Type") == type_, f"add {name} ({type_})"
    return res[name]["Properties"]


def test_parameters(template):
    params = template("compute").get("Parameters", {})
    assert params.get("Prefix", {}).get("Default") == "shortly", "Parameter Prefix (String, Default shortly)"
    assert sorted(params.get("Env", {}).get("AllowedValues", [])) == ["lab", "prod"], "Parameter Env with AllowedValues [lab, prod]"
    assert params.get("InstanceType", {}).get("Default") == "t4g.small", \
        "Parameter InstanceType (String) with Default t4g.small — a small Graviton instance"
    assert params["InstanceType"].get("AllowedValues"), "give InstanceType AllowedValues so nobody can pick an unreviewed type"
    image = params.get("ImageId", {})
    assert image.get("Type") == "AWS::SSM::Parameter::Value<AWS::EC2::Image::Id>", \
        "Parameter ImageId: Type AWS::SSM::Parameter::Value<AWS::EC2::Image::Id> — CloudFormation looks up the newest AMI when the stack is created"
    assert str(image.get("Default", "")).endswith("al2023-ami-kernel-default-arm64"), \
        "ImageId Default: /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64 (Amazon Linux 2023, arm64 to match Graviton)"


def test_load_balancer(resources):
    p = props(resources("compute"), "LoadBalancer", "AWS::ElasticLoadBalancingV2::LoadBalancer")
    assert p.get("Type", "application") == "application", "LoadBalancer Type: application (an ALB routes HTTP by path)"
    assert p.get("Scheme") == "internet-facing", "LoadBalancer Scheme: internet-facing"
    assert p.get("Subnets") == ["import:shortly-public-subnet-ids"], \
        "LoadBalancer Subnets: !Split [',', !ImportValue …-public-subnet-ids] (the ALB lives in the public subnets)"
    assert p.get("SecurityGroups") == ["import:shortly-alb-sg-id"], "LoadBalancer SecurityGroups: [!ImportValue …-alb-sg-id]"


def test_target_group(resources):
    p = props(resources("compute"), "AppTargetGroup", "AWS::ElasticLoadBalancingV2::TargetGroup")
    assert (p.get("Protocol"), p.get("Port")) == ("HTTP", 8000), "AppTargetGroup: Protocol HTTP, Port 8000 (where the app listens)"
    assert p.get("VpcId") == "import:shortly-vpc-id", "AppTargetGroup VpcId: !ImportValue …-vpc-id"
    assert p.get("TargetType", "instance") == "instance", "AppTargetGroup TargetType: instance"
    assert p.get("HealthCheckPath") == "/healthz", "AppTargetGroup HealthCheckPath: /healthz"
    assert str((p.get("Matcher") or {}).get("HttpCode")) == "200", "AppTargetGroup Matcher: {HttpCode: '200'}"


def test_deregistration_delay_is_short(resources):
    p = props(resources("compute"), "AppTargetGroup", "AWS::ElasticLoadBalancingV2::TargetGroup")
    attrs = {a.get("Key"): a.get("Value") for a in p.get("TargetGroupAttributes") or []}
    assert "deregistration_delay.timeout_seconds" in attrs, \
        "set TargetGroupAttributes: - {Key: deregistration_delay.timeout_seconds, Value: '30'} — the default is 300 s"
    seconds = int(attrs["deregistration_delay.timeout_seconds"])
    assert seconds <= 60, (f"deregistration delay is {seconds} s; use 60 or less. The default 300 s makes every scale-in "
                           "wait five minutes for an app whose requests take milliseconds")
````

### `course_project/tests/m03/test_m03_2_launch_template.py`

````python
"""M03.2 — the launch template: Graviton, IMDSv2, instance profile, no SSH key."""
import pytest

TYPE = "AWS::EC2::LaunchTemplate"


@pytest.fixture
def data(resources):
    res = resources("compute")
    assert res.get("AppLaunchTemplate", {}).get("Type") == TYPE, f"add AppLaunchTemplate ({TYPE})"
    props = res["AppLaunchTemplate"]["Properties"]
    assert props.get("LaunchTemplateData"), "AppLaunchTemplate needs LaunchTemplateData"
    return props


def test_name_image_and_type(data, template):
    assert data.get("LaunchTemplateName") == "shortly-app", "LaunchTemplateName: !Sub '${Prefix}-app'"
    raw = template("compute")["Resources"]["AppLaunchTemplate"]["Properties"]["LaunchTemplateData"]
    assert raw.get("ImageId") == {"Ref": "ImageId"}, "LaunchTemplateData ImageId: !Ref ImageId (the parameter, not a hard-coded AMI id)"
    assert raw.get("InstanceType") == {"Ref": "InstanceType"}, "LaunchTemplateData InstanceType: !Ref InstanceType"


def test_every_allowed_instance_type_is_graviton(template, ec2types):
    spec = template("compute").get("Parameters", {}).get("InstanceType", {})
    assert spec.get("Default") and spec.get("AllowedValues"), "InstanceType needs a Default and AllowedValues"
    for name in list(spec["AllowedValues"]) + [spec["Default"]]:
        try:
            info = ec2types.decode(str(name))
        except ValueError as exc:
            pytest.fail(f"{name} is not an instance type name: {exc}", pytrace=False)
        assert info["processor"] == "AWS Graviton", \
            (f"{name} is {info['processor']}, not Graviton. Remove it: Graviton costs up to 20 % less than comparable x86 "
             "instances (and the AMI is arm64, so an x86 type would not even boot)")


def test_imdsv2_required(data):
    meta = data["LaunchTemplateData"].get("MetadataOptions") or {}
    assert meta.get("HttpTokens") == "required", \
        ("IMDSv2: MetadataOptions HttpTokens: required. With 'optional', a request-forgery bug in the app can steal the "
         "instance role's credentials with one GET")
    assert meta.get("HttpEndpoint", "enabled") == "enabled", "MetadataOptions HttpEndpoint: enabled (the app's SDK needs the metadata service)"
    assert meta.get("HttpPutResponseHopLimit") in (1, 2), \
        ("MetadataOptions HttpPutResponseHopLimit: 1. The token reply may cross one network hop; "
         "2 is only for containers that run on the instance")


def test_instance_profile_and_security_group(data):
    d = data["LaunchTemplateData"]
    assert (d.get("IamInstanceProfile") or {}).get("Name") == "import:shortly-app-instance-profile", \
        "IamInstanceProfile: {Name: !ImportValue …-app-instance-profile} (created in M01)"
    assert d.get("SecurityGroupIds") == ["import:shortly-app-sg-id"], "SecurityGroupIds: [!ImportValue …-app-sg-id] (created in M02)"


def test_no_ssh_key_and_no_public_ip(data):
    d = data["LaunchTemplateData"]
    assert "KeyName" not in d, "remove KeyName: use Session Manager, not SSH keys. The app security group has no port 22 anyway"
    for nic in d.get("NetworkInterfaces") or []:
        assert nic.get("AssociatePublicIpAddress") in (None, False, "false"), \
            "instances stay private (app subnets): remove AssociatePublicIpAddress; they reach the internet through NAT"
````

### `course_project/tests/m03/test_m03_3_user_data.py`

````python
"""M03.3 — user data that installs and starts the Shortly app."""
import pytest


@pytest.fixture
def script(user_data):
    return user_data("compute", "AppLaunchTemplate")


def test_starts_with_a_shebang(script):
    assert script.startswith("#!/bin/bash"), "UserData must begin with #!/bin/bash (cloud-init runs it as a script)"


def test_contains_the_whole_app(script, repo):
    app = repo / "app" / "app.py"
    assert app.exists(), "app/app.py is missing: run  python <course>/course_project/tools/start_milestone.py 3 --repo <your repo>"
    lines = [l for l in app.read_text(encoding="utf-8").splitlines() if l.strip()]
    present = set(script.splitlines())
    missing = [l for l in lines if l not in present]
    assert not missing, (f"UserData is missing {len(missing)} line(s) of app/app.py, first: {missing[0]!r}. Write the file with a "
                         "heredoc (cat > /opt/shortly/app.py <<'EOF' … EOF) and paste app.py between the markers, unchanged")


def test_runs_as_a_service(script):
    assert "systemctl enable --now shortly" in script, "start the app with systemctl enable --now shortly (so it also starts after a reboot)"
    assert "[Service]" in script and "ExecStart=" in script, "write /etc/systemd/system/shortly.service with a [Service] section and ExecStart="
    assert "PORT=8000" in script, "the unit needs Environment=PORT=8000: the target group sends traffic to port 8000"
    assert "Restart=always" in script, "add Restart=always so systemd restarts the app if it crashes"


def test_fits_the_user_data_limit(script):
    size = len(script.encode("utf-8"))
    assert size <= 16384, f"UserData is {size} bytes; EC2 allows 16 KB (16384) before base64. Keep the script small"
````

### `course_project/tests/m03/test_m03_4_auto_scaling.py`

````python
"""M03.4 — the Auto Scaling group and its CPU target-tracking policy. prod: 2–6 instances; lab: 1–2."""
import pytest

ASG = "AWS::AutoScaling::AutoScalingGroup"
POLICY = "AWS::AutoScaling::ScalingPolicy"
SIZES = {"prod": (2, 6), "lab": (1, 2)}


def asg(resources, **params):
    res = resources("compute", **params)
    assert res.get("AppAutoScalingGroup", {}).get("Type") == ASG, f"add AppAutoScalingGroup ({ASG})"
    return res["AppAutoScalingGroup"]["Properties"]


def policy(resources, **params):
    res = resources("compute", **params)
    assert res.get("CpuTargetTracking", {}).get("Type") == POLICY, f"add CpuTargetTracking ({POLICY})"
    return res["CpuTargetTracking"]["Properties"]


@pytest.mark.parametrize("env", ["prod", "lab"])
def test_size_per_environment(resources, env):
    p = asg(resources, Env=env)
    low, high = SIZES[env]
    assert (p.get("MinSize"), p.get("MaxSize")) == (low, high), \
        f"Env={env}: MinSize {low}, MaxSize {high} (!If [IsProd, …, …]; prod needs two instances so one AZ can fail)"
    assert "DesiredCapacity" not in p, "remove DesiredCapacity: the group starts at MinSize and the scaling policy then owns the number"


def test_uses_elb_health_checks(resources):
    p = asg(resources)
    assert p.get("HealthCheckType") == "ELB", \
        "HealthCheckType: ELB. Behind a load balancer use ELB health checks, or Auto Scaling never replaces an instance whose app has died"
    grace = p.get("HealthCheckGracePeriod")
    assert isinstance(grace, int) and 60 <= grace <= 600, \
        f"HealthCheckGracePeriod is {grace!r}; use 60–600 seconds (time for boot, user data and the first healthy check)"


def test_launch_template_and_target_group(resources):
    p = asg(resources)
    lt = p.get("LaunchTemplate") or {}
    assert lt.get("LaunchTemplateId") == "AppLaunchTemplate", "LaunchTemplate: LaunchTemplateId: !Ref AppLaunchTemplate"
    assert lt.get("Version") == "AppLaunchTemplate.LatestVersionNumber", \
        "LaunchTemplate Version: !GetAtt AppLaunchTemplate.LatestVersionNumber (so editing the template rolls out a new version)"
    assert p.get("TargetGroupARNs") == ["AppTargetGroup"], "TargetGroupARNs: [!Ref AppTargetGroup]"
    assert p.get("VPCZoneIdentifier") == ["import:shortly-app-subnet-ids"], \
        "VPCZoneIdentifier: !Split [',', !ImportValue …-app-subnet-ids] (private app subnets in both AZs)"


def test_instances_are_tagged(resources):
    tags = {t.get("Key"): t for t in asg(resources).get("Tags") or []}
    assert tags.get("Name", {}).get("Value") == "shortly-app", "Tags: Key Name, Value !Sub '${Prefix}-app'"
    assert tags["Name"].get("PropagateAtLaunch") in (True, "true"), "the Name tag needs PropagateAtLaunch: true to reach the instances"


def test_cpu_target_tracking(resources):
    p = policy(resources)
    assert p.get("PolicyType") == "TargetTrackingScaling", "CpuTargetTracking PolicyType: TargetTrackingScaling"
    assert p.get("AutoScalingGroupName") == "AppAutoScalingGroup", "AutoScalingGroupName: !Ref AppAutoScalingGroup"
    config = p.get("TargetTrackingConfiguration") or {}
    metric = (config.get("PredefinedMetricSpecification") or {}).get("PredefinedMetricType")
    assert metric == "ASGAverageCPUUtilization", "PredefinedMetricSpecification PredefinedMetricType: ASGAverageCPUUtilization"
    target = config.get("TargetValue")
    assert isinstance(target, (int, float)) and 40 <= target <= 70, \
        f"TargetValue is {target!r}; use 40–70. Lower wastes money, higher leaves no room for a traffic spike while new instances boot"


@pytest.mark.parametrize("env", ["prod", "lab"])
def test_scaling_model(resources, scaling, env):
    p, target = asg(resources, Env=env), policy(resources, Env=env)["TargetTrackingConfiguration"]["TargetValue"]
    low, high = p["MinSize"], p["MaxSize"]
    wanted = scaling.target_tracking(low, 100.0, float(target), low, high)
    assert wanted > low, (f"Env={env}: at MinSize ({low}) and 100 % CPU the policy should add instances, but the model keeps {wanted}. "
                          "Is MaxSize larger than MinSize?")
    assert wanted <= high, f"Env={env}: the policy would grow past MaxSize ({high})"
    assert scaling.target_tracking(high, 100.0, float(target), low, high) == high, "the group never grows past MaxSize"
````

### `course_project/tests/m03/test_m03_5_listener_rules.py`

````python
"""M03.5 — the HTTP listener and path-based rules: /healthz hidden from the internet, /api/* explicit."""
import pytest

LISTENER = "AWS::ElasticLoadBalancingV2::Listener"
RULE = "AWS::ElasticLoadBalancingV2::ListenerRule"


def of_type(res, type_):
    return {name: r for name, r in res.items() if r["Type"] == type_}


def action_key(action):
    """('forward', 'AppTargetGroup') or ('fixed-response', 404) — comparable in a test."""
    kind = action.get("Type")
    if kind == "forward":
        return ("forward", action.get("TargetGroupArn") or [t.get("TargetGroupArn") for t in (action.get("ForwardConfig") or {}).get("TargetGroups", [])][0])
    if kind == "fixed-response":
        return ("fixed-response", int(action["FixedResponseConfig"]["StatusCode"]))
    return (kind, None)


def to_model_rules(res):
    """The listener rules as elb.match_rule wants them: conditions with AWS field names, plus the default."""
    rules = [{"priority": "default", "conditions": [], "action": action_key(res["HttpListener"]["Properties"]["DefaultActions"][0])}]
    for rule in of_type(res, RULE).values():
        p = rule["Properties"]
        conditions = []
        for c in p.get("Conditions") or []:
            config = c.get("PathPatternConfig") or c.get("HostHeaderConfig") or {}
            conditions.append({"field": c["Field"], "values": list(config.get("Values") or c.get("Values") or [])})
        rules.append({"priority": int(p["Priority"]), "conditions": conditions, "action": action_key(p["Actions"][0])})
    return rules


def route(elb, request, model):
    try:
        return elb.match_rule(request, model)
    except ValueError as exc:
        pytest.fail(f"the listener rules are not valid: {exc}", pytrace=False)


@pytest.fixture
def rules(resources):
    res = resources("compute")
    assert res.get("HttpListener", {}).get("Type") == LISTENER, f"add HttpListener ({LISTENER})"
    return res, to_model_rules(res)


def test_http_listener(resources):
    res = resources("compute")
    assert res.get("HttpListener", {}).get("Type") == LISTENER, f"add HttpListener ({LISTENER})"
    p = res["HttpListener"]["Properties"]
    assert p.get("LoadBalancerArn") == "LoadBalancer", "HttpListener LoadBalancerArn: !Ref LoadBalancer"
    assert (p.get("Port"), p.get("Protocol")) == (80, "HTTP"), "HttpListener: Port 80, Protocol HTTP"
    actions = [action_key(a) for a in p.get("DefaultActions") or []]
    assert actions == [("forward", "AppTargetGroup")], "HttpListener DefaultActions: forward to AppTargetGroup"


def test_no_https_yet(resources):
    for name, listener in of_type(resources("compute"), LISTENER).items():
        p = listener["Properties"]
        assert p.get("Protocol") not in ("HTTPS", "TLS") and int(p.get("Port", 0)) != 443, \
            f"{name}: no HTTPS listener yet. It needs a certificate, which milestone M07 adds; keep M03 HTTP only"


def test_priorities_are_unique(resources):
    res = of_type(resources("compute"), RULE)
    for name in ("HealthzRule", "ApiRule"):
        assert name in res, f"add {name} ({RULE})"
    priorities = [(n, r["Properties"].get("Priority")) for n, r in res.items()]
    values = [p for _, p in priorities]
    assert len(values) == len(set(values)), f"two rules share a priority {priorities}: every rule on a listener needs its own number"
    assert res["HealthzRule"]["Properties"].get("Priority") == 10 and res["ApiRule"]["Properties"].get("Priority") == 20, \
        "HealthzRule has Priority 10 and ApiRule Priority 20 (the lowest number is checked first)"


def test_healthz_is_not_public(rules, elb):
    _, model = rules
    request = {"method": "GET", "path": "/healthz", "host": "shortly-alb.example.com"}
    assert route(elb, request, model) == ("fixed-response", 404), \
        ("GET /healthz from the internet must get a fixed-response 404 from the load balancer. Target health checks go straight "
         "to the instances and never pass through listener rules, so hiding the endpoint does not break them")


def test_api_requests_reach_the_app(rules, elb):
    _, model = rules
    api = {"method": "POST", "path": "/api/links", "host": "shortly-alb.example.com"}
    assert route(elb, api, model) == ("forward", "AppTargetGroup"), "POST /api/links must forward to AppTargetGroup (ApiRule: path-pattern /api/*)"
    short = {"method": "GET", "path": "/Ab3dE9x", "host": "shortly-alb.example.com"}
    assert route(elb, short, model) == ("forward", "AppTargetGroup"), "a short link like /Ab3dE9x must still reach the app (default action)"
````

### `course_project/tests/m03/test_m03_6_exports_and_deploy.py`

````python
"""M03.6 — exports for later stacks, lint-clean, and a deploy in moto (iam + network + compute) for both environments."""
import pytest

EXPORTS = {"AlbDnsName": ("shortly-alb-dns-name", "LoadBalancer.DNSName"),
           "AlbArn": ("shortly-alb-arn", "LoadBalancer"),
           "AppTargetGroupArn": ("shortly-app-tg-arn", "AppTargetGroup"),
           "AppAsgName": ("shortly-app-asg-name", "AppAutoScalingGroup")}


def test_exports(outputs):
    out = outputs("compute")
    for key, (export, value) in EXPORTS.items():
        assert key in out, f"add Output {key}"
        assert out[key].get("Export", {}).get("Name") == export, f"{key}: Export Name !Sub '${{Prefix}}-{export[8:]}'"
        assert str(out[key].get("Value")) == value, f"{key}: Value should render as {value} ({'!GetAtt ' + value if '.' in value else '!Ref ' + value})"


def test_lint_clean(lint_errors):
    errors = lint_errors("compute")
    assert errors == [], "cfn-lint errors: " + "; ".join(f"line {e['line']} {e['rule']} {e['message']}" for e in errors)


@pytest.mark.parametrize("env, instances", [("prod", 2), ("lab", 1)])
def test_deploys_in_moto(moto_stacks, env, instances):
    import boto3

    for layer in ("iam", "network", "compute"):
        status = moto_stacks(layer, Env=env)
        assert status == "CREATE_COMPLETE", f"the {layer} stack ended as {status}; fix infra/{layer}.yaml"
    region = {"region_name": "us-east-1"}
    asg_client = boto3.client("autoscaling", **region)
    groups = asg_client.describe_auto_scaling_groups()["AutoScalingGroups"]
    assert len(groups) == 1, "expected one Auto Scaling group"
    group = groups[0]
    assert group["MinSize"] == instances and len(group["Instances"]) == instances, f"Env={env}: expected {instances} instance(s)"
    assert group["HealthCheckType"] == "ELB"

    elb_client = boto3.client("elbv2", **region)
    target_groups = elb_client.describe_target_groups()["TargetGroups"]
    assert [t["HealthCheckPath"] for t in target_groups] == ["/healthz"]
    balancers = elb_client.describe_load_balancers()["LoadBalancers"]
    assert len(balancers) == 1 and len(balancers[0]["AvailabilityZones"]) == 2, "the load balancer should span two Availability Zones"

    # moto stores the launch template but never applies its settings to instances, so read the template itself
    ec2 = boto3.client("ec2", **region)
    versions = ec2.describe_launch_template_versions(LaunchTemplateName="shortly-app", Versions=["$Latest"])["LaunchTemplateVersions"]
    assert versions[0]["LaunchTemplateData"]["MetadataOptions"]["HttpTokens"] == "required"
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
from _course import cidr as _cidr, ec2types as _ec2types, elb as _elb, netsim as _netsim, scaling as _scaling  # noqa: E402

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
        return cfn.render(tpl.get("Outputs") or {}, values, PSEUDO, cfn.evaluate_conditions(tpl, values, PSEUDO))
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
    """deploy(layer, **params) creates the stack in a fake AWS (moto) and returns its status. Stacks that
    import another stack's exports (compute needs iam and network) are deployed after it, in the same test.
    moto skips some resource types silently, so tests only read back what moto really models."""
    import boto3
    from moto import mock_aws

    mock = mock_aws()
    mock.start()

    def deploy(layer: str, **params) -> str:
        merged = {**PARAMS, **params}
        tpl = cfn.load_template_text(_path(layer).read_text(encoding="utf-8"))
        declared = tpl.get("Parameters") or {}
        # moto cannot evaluate !Cidr, so hand it the rendered subnet blocks instead
        body = json.dumps(cfn.inline_functions(tpl, {"Fn::Cidr"}, merged, PSEUDO))
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
    _harness/awslib/*.py + prices.toml     → <repo>/tests/_course/   (template, policy and model helpers the tests use)
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
           "ec2types.py", "elb.py", "scaling.py", "purchasing.py", "prices.py", "prices.toml")


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

### `week_03_compute_and_scaling/practice/exercises.py`

````python
"""
Week 03 drills — compute and scaling
====================================
Run:    python practice/exercises.py          every drill
        python practice/exercises.py 4        drill 4 only
Drills 01–05 are pure Python models of how compute works: instance-type names, what the same
fleet costs under each purchasing option, how Auto Scaling sizes a group, which load-balancer rule
answers a request, and how cross-zone load balancing splits traffic. Drills 06–08 build and fix
the real thing with boto3 against moto (a fake AWS). Drills 09–10 are decide and predict drills.
Nothing here can touch a real account or cost money.
The course's own versions of drills 01–05 (_harness/awslib/ec2types.py, purchasing.py, scaling.py
and elb.py) are their answer key — don't open them until you are done.
Note: moto only stores what you send. It never launches Graviton chips, spreads instances over
zones or replaces sick ones. So the drills read your settings back and the models show the behaviour.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.awsdrill import Drill, run  # noqa: E402
from _harness.awslib import prices  # noqa: E402


# ── Exercise 01 ★: Read an instance type ─────────────────────────────
"""
An instance type name is  <series><generation><options>.<size>.  In c7gn.xlarge: series c,
generation 7, options g and n, size xlarge.
decode(instance_type) -> dict
    Trim and lower-case the name first (" C7G.Large " is fine). Return exactly these keys:
      "series"        the longest series prefix of the part before the dot: c, m, r, t, x, i, g, mac, hpc ...
      "category"      the family group of that series (table below)
      "generation"    the number after the series, as an int (at least 1)
      "options"       the letters after the generation, as a list of one-letter strings, in order
      "processor"     "AWS Graviton" (option g), "AMD" (option a), "Intel" (option i), else "not stated"
      "size"          the part after the dot, unchanged
      "burstable"     True when the series is t
      "instance_store"  True when the option letter d is present
      "bare_metal"    True when the size starts with "metal"
      "flex"          True when the family ends with "-flex" (m7i-flex.large). Strip "-flex" before
                      parsing, then add "flex" at the end of "options".
    Series -> category (try longer prefixes first, so "mac" is not "m" and "dl" is not "d"):
      general purpose: m t a mac       compute optimized: c      memory optimized: r x z u
      storage optimized: i d h         high performance computing: hpc
      accelerated computing: inf trn dl vt p g f
    Option letters: a AMD, g Graviton, i Intel, d instance store, n network and EBS optimized,
      e extra storage or memory, z high CPU frequency, b block storage optimized, q Qualcomm
      inference accelerators.
    Sizes: nano, micro, small, medium, large, xlarge, a number then xlarge (3xlarge, 16xlarge),
      metal, or metal-<n>xl. Anything else is not a size.
    ValueError for: no "." in the name, an unknown size, an unknown series, a missing or zero
    generation, an unknown option letter.
    WATCH OUT: the processor comes from the OPTION letters only. g5.xlarge is a GPU series (g),
    not a Graviton chip. g5g.xlarge has the option g, so it is Graviton.
choose_type(vcpus, memory_gib, processor="graviton", generation=7) -> str
    Pick the series from memory per vCPU: at most 2 GiB per vCPU -> c, at most 4 -> m, at most 8 -> r
    (4 GiB on 2 vCPUs is 2 GiB per vCPU, so c; 8 GiB on 2 vCPUs is 4 per vCPU, so m).
    Pick the size from the vCPU count: 1 -> medium, 2 -> large, 4 -> xlarge, any other multiple
    of 4 -> f"{vcpus // 4}xlarge". The processor option letter: graviton g, intel i, amd a.
    Name = series + generation + letter + "." + size.
    ValueError for: vcpus or memory not positive, an unknown processor, more than 8 GiB per vCPU
    (look at the X or U families), a vCPU count with no standard size (3, 6, 10 ...).
Examples:
    decode("c7gn.xlarge")["options"] == ["g", "n"]       decode("t3.micro")["processor"] == "not stated"
    choose_type(2, 4) == "c7g.large"      choose_type(2, 8) == "m7g.large"     choose_type(2, 16) == "r7g.large"
    choose_type(16, 32, "amd", 6) == "c6a.4xlarge"
Why? Names are the cheapest documentation AWS has: you can read the chip, the generation and the
memory shape from the name, and the exam expects you to.
Hint: re.match(r"[0-9]+", rest) finds the generation; sorted(SERIES, key=len, reverse=True) tries
      long prefixes first. Graviton is the cheapest 'good' default (AWS: up to 20% less than comparable x86).
"""
def decode(instance_type):
    raise NotImplementedError  # YOUR CODE


def choose_type(vcpus, memory_gib, processor="graviton", generation=7):
    raise NotImplementedError  # YOUR CODE


class Ex01(Drill):
    """Read an instance type ★"""
    tasks = ("3.2",)

    def test_decode_a_full_name(self):
        got = decode("c7gn.xlarge")
        self.assertEqual((got["series"], got["category"], got["generation"], got["options"], got["size"]),
                         ("c", "compute optimized", 7, ["g", "n"], "xlarge"))
        self.assertEqual(got["processor"], "AWS Graviton")
        self.assertEqual(set(got), {"series", "category", "generation", "options", "processor", "size",
                                    "burstable", "instance_store", "bare_metal", "flex"}, "return exactly the documented keys")

    def test_processor_comes_from_the_option_letters(self):
        for name, want in {"m7g.large": "AWS Graviton", "m7i.large": "Intel", "m7a.large": "AMD", "t3.micro": "not stated",
                           "g5.xlarge": "not stated", "g5g.xlarge": "AWS Graviton", "i3en.3xlarge": "not stated"}.items():
            with self.subTest(name=name):
                self.assertEqual(decode(name)["processor"], want,
                                 f"{name}: only the option letters (after the generation) name the processor, not the series")

    def test_flags(self):
        self.assertTrue(decode("t3.micro")["burstable"])
        self.assertFalse(decode("m7g.large")["burstable"])
        self.assertTrue(decode("x2gd.metal-24xl")["instance_store"])
        self.assertTrue(decode("x2gd.metal-24xl")["bare_metal"])
        self.assertTrue(decode("mac2.metal")["bare_metal"])
        self.assertFalse(decode("c7g.16xlarge")["bare_metal"])

    def test_long_prefixes_and_flex(self):
        self.assertEqual((decode("mac2.metal")["series"], decode("mac2.metal")["category"]), ("mac", "general purpose"))
        self.assertEqual(decode("hpc7g.16xlarge")["series"], "hpc")
        self.assertEqual(decode("dl1.24xlarge")["series"], "dl")
        flex = decode("m7i-flex.large")
        self.assertEqual((flex["series"], flex["options"], flex["processor"], flex["flex"]), ("m", ["i", "flex"], "Intel", True))

    def test_trims_and_ignores_case(self):
        self.assertEqual(decode(" C7G.Large "), decode("c7g.large"))
        self.assertEqual(decode("C7G.Large")["size"], "large")

    def test_decode_rejects_bad_names(self):
        for bad in ("c7g", "c7g.huge", "q7g.large", "c.large", "c0g.large", "c7w.large", "m7i-flex", ""):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    decode(bad)

    def test_choose_type(self):
        cases = {(2, 4): "c7g.large", (2, 8): "m7g.large", (2, 16): "r7g.large", (1, 1): "c7g.medium", (4, 16): "m7g.xlarge",
                 (8, 64): "r7g.2xlarge", (2, 4.5): "m7g.large"}
        for (vcpus, memory), want in cases.items():
            with self.subTest(vcpus=vcpus, memory=memory):
                self.assertEqual(choose_type(vcpus, memory), want)

    def test_choose_type_boundaries_are_inclusive(self):
        self.assertEqual(choose_type(4, 8)[0], "c", "exactly 2 GiB per vCPU is still C")
        self.assertEqual(choose_type(4, 16)[0], "m", "exactly 4 GiB per vCPU is still M")
        self.assertEqual(choose_type(4, 32)[0], "r", "exactly 8 GiB per vCPU is still R")

    def test_choose_type_processor_and_generation(self):
        self.assertEqual(choose_type(4, 16, "intel"), "m7i.xlarge")
        self.assertEqual(choose_type(16, 32, "amd", 6), "c6a.4xlarge")
        self.assertEqual(choose_type(48, 96, generation=8), "c8g.12xlarge")

    def test_choose_type_rejects_what_cannot_be_built(self):
        for args in ((0, 4), (2, 0), (2, 4, "arm"), (2, 17), (3, 6), (6, 12)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    choose_type(*args)


# ── Exercise 02 ★: Pay for the hours you use ─────────────────────────
"""
PRICES (given) are illustrative us-east-1 numbers from _harness/awslib/prices.toml:
compute_savings_plan_discount 0.31, standard_ri_discount 0.40, spot_discount 0.70.
`rate` is the On-Demand price for ONE instance-hour (for example PRICES["m7g_large_per_hour"]).
The four options are OPTIONS = ("on-demand", "compute savings plan", "standard reserved", "spot").
monthly_cost(option, rate, instances, hours_used, *, hours_in_month=730, price=PRICES) -> float
    USD per month, rounded to 2 decimal places.
      on-demand               instances x hours_used x rate
      spot                    the same, times (1 - spot_discount)
      compute savings plan    instances x hours_in_month x rate x (1 - compute_savings_plan_discount)
      standard reserved       instances x hours_in_month x rate x (1 - standard_ri_discount)
    A commitment is billed for EVERY hour of the month, used or not. On-Demand and Spot bill only
    the hours the instance runs.
    ValueError for: an unknown option, a negative rate, instances or hours_used, or hours_used
    greater than hours_in_month.
cheapest(rate, instances, hours_used, *, interruptible=False, may_change_family=False,
         hours_in_month=730, price=PRICES) -> (option, cost)
    The cheapest ALLOWED option. On-Demand and the Compute Savings Plan are always allowed.
    A Standard RI is locked to one instance type and Region, so it is allowed only when
    may_change_family is False. Spot is allowed only when interruptible is True.
    A tie goes to the option that comes first in OPTIONS.
break_even_hours(option, *, hours_in_month=730, price=PRICES) -> float
    The hours of use per month where a commitment costs the same as On-Demand:
    hours_in_month x (1 - discount), rounded to 1 decimal. Only "compute savings plan" and
    "standard reserved" have one — any other option → ValueError.
Examples (m7g.large, rate 0.0816):
    monthly_cost("on-demand", 0.0816, 1, 730) == 59.57       monthly_cost("compute savings plan", 0.0816, 1, 730) == 41.1
    cheapest(0.0816, 4, 730) == ("standard reserved", 142.96)    # runs all month: commit
    cheapest(0.0816, 4, 173) == ("on-demand", 56.47)             # 9-to-5 on weekdays: 173 hours, stay On-Demand
    break_even_hours("compute savings plan") == 503.7            # 69% of the month
Why? A commitment is a bet that you will use the hours. Below the break-even point you pay for
hours you never use. Savings Plans follow you across families, Regions, Fargate and Lambda; a
Standard RI is cheaper but stuck to one type.
Hint: write monthly_cost first; cheapest is a min() over the allowed options, break_even_hours is one line.
"""
PRICES = prices.section("ec2")
OPTIONS = ("on-demand", "compute savings plan", "standard reserved", "spot")


def monthly_cost(option, rate, instances, hours_used, *, hours_in_month=730, price=PRICES):
    raise NotImplementedError  # YOUR CODE


def cheapest(rate, instances, hours_used, *, interruptible=False, may_change_family=False, hours_in_month=730, price=PRICES):
    raise NotImplementedError  # YOUR CODE


def break_even_hours(option, *, hours_in_month=730, price=PRICES):
    raise NotImplementedError  # YOUR CODE


class Ex02(Drill):
    """Pay for the hours you use ★"""
    tasks = ("4.2",)
    M7G = PRICES["m7g_large_per_hour"]

    def test_monthly_cost_each_option(self):
        self.assertEqual(monthly_cost("on-demand", self.M7G, 1, 730), 59.57)
        self.assertEqual(monthly_cost("compute savings plan", self.M7G, 1, 730), 41.1)
        self.assertEqual(monthly_cost("standard reserved", self.M7G, 1, 730), 35.74)
        self.assertEqual(monthly_cost("spot", self.M7G, 1, 730), 17.87)

    def test_commitments_bill_every_hour_of_the_month(self):
        part_time = monthly_cost("compute savings plan", self.M7G, 4, 173)
        self.assertEqual(part_time, monthly_cost("compute savings plan", self.M7G, 4, 730),
                         "a commitment costs the same however few hours you use")
        self.assertEqual(monthly_cost("standard reserved", self.M7G, 4, 0), monthly_cost("standard reserved", self.M7G, 4, 730))
        self.assertEqual(monthly_cost("on-demand", self.M7G, 4, 173), 56.47, "On-Demand bills only the hours used")
        self.assertEqual(monthly_cost("spot", self.M7G, 4, 173), 16.94)

    def test_a_24_7_fleet_commits(self):
        self.assertEqual(cheapest(self.M7G, 4, 730), ("standard reserved", 142.96))
        self.assertEqual(cheapest(self.M7G, 4, 730, may_change_family=True), ("compute savings plan", 164.41),
                         "a Standard RI is locked to one instance type: it is out when the family may change")

    def test_a_nine_to_five_fleet_stays_on_demand(self):
        self.assertEqual(cheapest(self.M7G, 4, 173), ("on-demand", 56.47),
                         "173 hours is far below the break-even point: a commitment would pay for idle hours")

    def test_spot_only_when_interruptible(self):
        self.assertEqual(cheapest(self.M7G, 4, 730, interruptible=True), ("spot", 71.48))
        self.assertEqual(cheapest(self.M7G, 4, 173, interruptible=True), ("spot", 16.94))
        self.assertNotEqual(cheapest(self.M7G, 4, 730)[0], "spot", "a workload that cannot be interrupted must not get Spot")

    def test_tie_goes_to_the_earlier_option(self):
        self.assertEqual(cheapest(1.0, 1, 503.7, may_change_family=True), ("on-demand", 503.7))

    def test_break_even(self):
        self.assertEqual(break_even_hours("compute savings plan"), 503.7)
        self.assertEqual(break_even_hours("standard reserved"), 438.0)
        self.assertEqual(break_even_hours("standard reserved", hours_in_month=720), 432.0)
        for option in ("on-demand", "spot", "dedicated"):
            with self.subTest(option=option):
                with self.assertRaises(ValueError):
                    break_even_hours(option)

    def test_uses_the_price_argument(self):
        custom = dict(PRICES, compute_savings_plan_discount=0.5, standard_ri_discount=0.0, spot_discount=0.9)
        self.assertEqual(monthly_cost("compute savings plan", 1.0, 1, 10, price=custom), 365.0)
        self.assertEqual(monthly_cost("spot", 1.0, 1, 10, price=custom), 1.0)
        self.assertEqual(cheapest(1.0, 1, 730, price=custom), ("compute savings plan", 365.0))
        self.assertEqual(monthly_cost("on-demand", 1.0, 1, 10, hours_in_month=100), 10.0)

    def test_rejects_bad_inputs(self):
        for call in (lambda: monthly_cost("free", 1, 1, 1), lambda: monthly_cost("on-demand", -1, 1, 1),
                     lambda: monthly_cost("on-demand", 1, -1, 1), lambda: monthly_cost("on-demand", 1, 1, -1),
                     lambda: monthly_cost("on-demand", 1, 1, 731)):
            with self.subTest():
                with self.assertRaises(ValueError):
                    call()


# ── Exercise 03 ★: Let the group size itself ─────────────────────────
"""
An Auto Scaling group keeps its desired capacity between a minimum and a maximum. Every function
below first checks 0 <= minimum <= maximum (otherwise ValueError) and never returns a number
outside [minimum, maximum].
target_tracking(current, metric, target, minimum, maximum) -> int
    You pick a target for a metric (say 50% average CPU); AWS adds or removes instances in direct
    proportion: new capacity = ceil(current x metric / target), then clamped. Round UP — rounding
    down would leave you above the target. current == 0 → minimum. A negative current or a target
    of 0 or less → ValueError.
    target_tracking(4, 80, 50, 2, 10) == 7        (4 x 80 / 50 = 6.4, rounded up)
    target_tracking(4, 15, 50, 2, 10) == 2        (1.2 would be 2, and the floor is 2 anyway)
step_scaling(current, metric, threshold, steps, minimum, maximum) -> int
    `steps` is a list of (lower, upper, change). The bounds are OFFSETS from the alarm threshold,
    and None means no limit (minus or plus infinity). breach = metric - threshold.
    Above the threshold (breach >= 0) a step matches when lower <= breach < upper (lower inclusive).
    Below it (breach < 0) a step matches when lower < breach <= upper (upper inclusive).
    The matching step's `change` is added to current, then clamped. No step matches → unchanged
    (but still clamped). Steps that overlap, or a step whose lower is not below its upper →
    ValueError.
    steps = [(0, 10, 1), (10, 20, 2), (20, None, 3)], threshold 70: metric 79.9 → +1, metric 80 → +2.
simple_scaling_run(metrics, start, high, low, change, cooldown, minimum, maximum, period=60) -> list[int]
    One metric sample every `period` seconds (the first at second 0). Return the desired capacity
    after each sample. metric > high adds `change`, metric < low removes `change` (clamped). An
    action that really changes the capacity starts a cooldown: samples at less than `cooldown`
    seconds after it are ignored. An action that changes nothing (already at the maximum) does NOT
    start a cooldown.
    simple_scaling_run([80]*6, 2, 70, 30, 1, 300, 1, 10) == [3, 3, 3, 3, 3, 4]
    (second 0 adds one; seconds 60–240 are inside the 300 s cooldown; second 300 adds another)
Why? Target tracking is the one to reach for: you state the goal, AWS does the sums. Step scaling
reacts harder to bigger breaches. Simple scaling is the oldest: one action, then it waits out the cooldown.
Hint: math.ceil(current * metric / target) — a float like 6.000000000000001 would round up to 7,
      so round the product to 9 places first.
"""
import math  # noqa: E402,F401


def target_tracking(current, metric, target, minimum, maximum):
    raise NotImplementedError  # YOUR CODE


def step_scaling(current, metric, threshold, steps, minimum, maximum):
    raise NotImplementedError  # YOUR CODE


def simple_scaling_run(metrics, start, high, low, change, cooldown, minimum, maximum, period=60):
    raise NotImplementedError  # YOUR CODE


class Ex03(Drill):
    """Let the group size itself ★"""
    tasks = ("3.2", "2.1")
    SCALE_OUT = [(0, 10, 1), (10, 20, 2), (20, None, 3)]
    SCALE_IN = [(None, -20, -2), (-20, 0, -1)]

    def test_target_tracking_rounds_up(self):
        self.assertEqual(target_tracking(4, 80, 50, 2, 10), 7, "4 x 80 / 50 = 6.4 → you need 7, not 6")
        self.assertEqual(target_tracking(4, 25, 50, 2, 10), 2)
        self.assertEqual(target_tracking(4, 50, 50, 2, 10), 4, "on target: no change")
        self.assertEqual(target_tracking(3, 51, 50, 1, 10), 4)

    def test_target_tracking_stays_inside_the_bounds(self):
        self.assertEqual(target_tracking(10, 100, 50, 2, 10), 10, "20 wanted, 10 allowed")
        self.assertEqual(target_tracking(4, 15, 50, 2, 10), 2, "the minimum is a floor")
        self.assertEqual(target_tracking(0, 90, 50, 2, 10), 2, "an empty group goes to the minimum")

    def test_target_tracking_rejects_nonsense(self):
        for args in ((4, 50, 0, 1, 5), (-1, 50, 50, 1, 5), (4, 50, 50, 5, 1), (4, 50, 50, -1, 5)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    target_tracking(*args)

    def test_step_bounds_above_the_threshold(self):
        for metric, want in {69: 5, 70: 6, 79.9: 6, 80: 7, 90: 8, 100: 8}.items():
            with self.subTest(metric=metric):
                self.assertEqual(step_scaling(5, metric, 70, self.SCALE_OUT, 1, 10), want,
                                 "above the threshold the LOWER bound is inclusive and the upper is exclusive")

    def test_step_bounds_below_the_threshold(self):
        for metric, want in {31: 5, 30: 5, 29: 4, 10: 3, 9: 3}.items():
            with self.subTest(metric=metric):
                self.assertEqual(step_scaling(5, metric, 30, self.SCALE_IN, 1, 10), want,
                                 "below the threshold the UPPER bound is inclusive and the lower is exclusive")

    def test_step_scaling_is_clamped(self):
        self.assertEqual(step_scaling(9, 100, 70, self.SCALE_OUT, 1, 10), 10)
        self.assertEqual(step_scaling(2, 5, 30, self.SCALE_IN, 1, 10), 1)

    def test_step_scaling_rejects_bad_steps(self):
        for steps in ([(0, 10, 1), (5, 15, 2)], [(10, 10, 1)], [(10, 5, 1)]):
            with self.subTest(steps=steps):
                with self.assertRaises(ValueError):
                    step_scaling(5, 80, 70, steps, 1, 10)

    def test_simple_scaling_cooldown(self):
        self.assertEqual(simple_scaling_run([80] * 6, 2, 70, 30, 1, 300, 1, 10), [3, 3, 3, 3, 3, 4],
                         "the cooldown is 300 s: samples at 60–240 s are ignored, the one at 300 s counts")
        self.assertEqual(simple_scaling_run([80, 20, 20, 20, 20, 20, 20], 2, 70, 30, 1, 300, 1, 10), [3, 3, 3, 3, 3, 2, 2])

    def test_simple_scaling_period_and_change(self):
        self.assertEqual(simple_scaling_run([80, 50, 80, 80, 80, 80, 80, 80, 80, 80, 80], 2, 70, 30, 2, 120, 1, 5),
                         [4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5])
        self.assertEqual(simple_scaling_run([80, 80, 80], 2, 70, 30, 1, 60, 1, 10, period=30), [3, 3, 4])

    def test_an_action_that_changes_nothing_starts_no_cooldown(self):
        self.assertEqual(simple_scaling_run([90, 10], 10, 70, 30, 1, 300, 1, 10), [10, 9],
                         "at the maximum nothing happened, so there is no cooldown to wait out")


# ── Exercise 04 ★: Which rule answers? ───────────────────────────────
"""
An Application Load Balancer listener holds rules. Model the choice of rule.
A rule:     {"priority": 1..50000 or "default", "conditions": [condition, ...], "action": anything}
A condition: {"field": F, "values": [...]} where F is one of
    "host-header"        values are host patterns ("admin.*")
    "path-pattern"       values are path patterns ("/api/*")
    "http-request-method" values are methods ("GET", "POST")
    "http-header"        also has "name": "X-Canary"; values are patterns for that header
    "query-string"       values are dicts {"key": pattern, "value": pattern}; either part may be left out
    "source-ip"          values are CIDR blocks ("10.0.0.0/8")
A request: {"host": …, "path": …, "method": …, "headers": {…}, "query": {…}, "source_ip": …} (any key may be missing).
match_rule(request, rules) -> the "action" of the rule that answers.
    Check the numbered rules in ASCENDING priority (1 before 5, whatever their order in the list),
    and the default rule last. A rule matches when ALL its conditions match (AND); a condition
    matches when ANY of its values match (OR). The default rule has no conditions and matches everything.
    Matching:  "*" matches any run of characters (even none), "?" matches exactly one character.
      host, header (name and value) and query-string (key and value): ignore case.
      path and method: exact case. The path is compared WITHOUT its query string ("/a?x=1" → "/a").
      source-ip: the address is inside the CIDR. A request with no source_ip does not match.
    Check the rules first and raise ValueError for: not exactly one default rule, or a default rule
    with conditions; a numbered rule with no conditions; two rules with the same priority; a
    priority that is not an int from 1 to 50000; an unknown condition field; a condition with no
    values; more than 3 values in one condition; more than 5 values in one rule (all conditions together).
Example:
    rules = [{"priority": 20, "conditions": [{"field": "path-pattern", "values": ["/api/*"]}], "action": "api"},
             {"priority": 10, "conditions": [{"field": "path-pattern", "values": ["/api/admin/*"]}], "action": "block"},
             {"priority": "default", "action": "web"}]
    match_rule({"path": "/api/admin/users"}, rules) == "block"     # 10 is checked first, though listed second
    match_rule({"path": "/Ab3dE9x"}, rules) == "web"
Why? Priority, not list order, decides. Put the narrow rule (block /api/admin/*) before the wide one
(forward /api/*) or the wide one swallows it. The default rule is the safety net — every listener has one.
Hint: validate, then sorted(numbered, key=priority) + [default]; re.fullmatch on a regex built from the
      pattern ("*" → ".*", "?" → ".", everything else re.escape'd) does the wildcards.
"""
import ipaddress  # noqa: E402,F401
import re  # noqa: E402,F401


def match_rule(request, rules):
    raise NotImplementedError  # YOUR CODE


def _rule(priority, field, values, action, **extra):
    return {"priority": priority, "conditions": [{"field": field, "values": values, **extra}], "action": action}


DEFAULT = {"priority": "default", "action": "web"}


class Ex04(Drill):
    """Which rule answers? ★"""
    tasks = ("3.2", "2.1")
    RULES = [
        _rule(30, "path-pattern", ["/api/*"], "api"),
        {"priority": 10, "action": "admin", "conditions": [{"field": "host-header", "values": ["admin.shortly.example"]},
                                                          {"field": "source-ip", "values": ["10.0.0.0/8"]}]},
        {"priority": 20, "action": "api-write", "conditions": [{"field": "http-request-method", "values": ["POST", "PUT"]},
                                                              {"field": "path-pattern", "values": ["/api/*"]}]},
        DEFAULT,
    ]

    def test_priority_beats_list_order(self):
        self.assertEqual(match_rule({"method": "POST", "path": "/api/links"}, self.RULES), "api-write",
                         "priority 20 is checked before priority 30, even though 30 is listed first")
        self.assertEqual(match_rule({"method": "GET", "path": "/api/links"}, self.RULES), "api")

    def test_default_is_last(self):
        self.assertEqual(match_rule({"path": "/Ab3dE9x", "method": "GET"}, self.RULES), "web")
        self.assertEqual(match_rule({}, [DEFAULT]), "web")
        early_default = [DEFAULT, _rule(1, "path-pattern", ["/a"], "a")]
        self.assertEqual(match_rule({"path": "/a"}, early_default), "a", "the default rule is tried last wherever it is listed")

    def test_and_across_conditions_or_within(self):
        admin = {"host": "admin.shortly.example", "source_ip": "10.1.2.3", "path": "/x", "method": "GET"}
        self.assertEqual(match_rule(admin, self.RULES), "admin")
        self.assertEqual(match_rule(dict(admin, source_ip="203.0.113.5"), self.RULES), "web", "both conditions must match")
        self.assertEqual(match_rule(dict(admin, host="shortly.example"), self.RULES), "web")
        self.assertEqual(match_rule({"method": "PUT", "path": "/api/x"}, self.RULES), "api-write", "PUT is one of the allowed methods")
        self.assertEqual(match_rule({"method": "DELETE", "path": "/api/x"}, self.RULES), "api")

    def test_host_ignores_case_and_wildcards_work(self):
        rules = [_rule(1, "host-header", ["*.shortly.example"], "tenant"), DEFAULT]
        self.assertEqual(match_rule({"host": "ACME.Shortly.Example"}, rules), "tenant")
        self.assertEqual(match_rule({"host": "shortly.example"}, rules), "web", "'*.' needs a dot and something before it")
        question = [_rule(1, "host-header", ["app?.shortly.example"], "app"), DEFAULT]
        self.assertEqual(match_rule({"host": "app1.shortly.example"}, question), "app")
        self.assertEqual(match_rule({"host": "app12.shortly.example"}, question), "web", "'?' is exactly one character")

    def test_path_is_case_sensitive_and_ignores_the_query(self):
        self.assertEqual(match_rule({"method": "GET", "path": "/API/links"}, self.RULES), "web", "paths are case-sensitive")
        self.assertEqual(match_rule({"method": "GET", "path": "/api/links?page=2"}, self.RULES), "api",
                         "the query string is not part of the path")
        self.assertEqual(match_rule({"method": "get", "path": "/api/x"}, self.RULES), "api", "'get' is not 'POST'")
        self.assertEqual(match_rule({"method": "post", "path": "/api/x"}, self.RULES), "api", "methods are case-sensitive")

    def test_header_and_query_string_conditions(self):
        rules = [_rule(1, "http-header", ["yes"], "canary", name="X-Canary"),
                 _rule(2, "query-string", [{"key": "v", "value": "2"}], "v2"),
                 _rule(3, "query-string", [{"value": "debug*"}], "debug"), DEFAULT]
        self.assertEqual(match_rule({"headers": {"x-canary": "YES"}}, rules), "canary", "header names and values ignore case")
        self.assertEqual(match_rule({"headers": {"x-canary": "no"}}, rules), "web")
        self.assertEqual(match_rule({"query": {"V": "2"}}, rules), "v2")
        self.assertEqual(match_rule({"query": {"v": "3"}}, rules), "web")
        self.assertEqual(match_rule({"query": {"anything": "debug-mode"}}, rules), "debug", "a value-only condition ignores the key")

    def test_source_ip(self):
        rules = [_rule(1, "source-ip", ["192.0.2.0/24", "198.51.100.7/32"], "office"), DEFAULT]
        self.assertEqual(match_rule({"source_ip": "192.0.2.77"}, rules), "office")
        self.assertEqual(match_rule({"source_ip": "198.51.100.7"}, rules), "office")
        self.assertEqual(match_rule({"source_ip": "198.51.100.8"}, rules), "web")
        self.assertEqual(match_rule({}, rules), "web", "no source address, no match")

    def test_invalid_rule_sets(self):
        ok = _rule(1, "path-pattern", ["/a"], "a")
        v = ["/1", "/2", "/3", "/4"]
        bad = {
            "duplicate priority": [ok, _rule(1, "path-pattern", ["/b"], "b"), DEFAULT],
            "two defaults": [ok, DEFAULT, dict(DEFAULT)],
            "no default": [ok],
            "numbered rule without conditions": [{"priority": 5, "action": "x"}, DEFAULT],
            "default with conditions": [ok, dict(DEFAULT, conditions=ok["conditions"])],
            "4 values in one condition": [_rule(1, "path-pattern", v, "a"), DEFAULT],
            "6 values in one rule": [{"priority": 1, "action": "a", "conditions": [
                {"field": "path-pattern", "values": v[:3]}, {"field": "host-header", "values": ["a", "b", "c"]}]}, DEFAULT],
            "priority 0": [_rule(0, "path-pattern", ["/a"], "a"), DEFAULT],
            "priority 50001": [_rule(50001, "path-pattern", ["/a"], "a"), DEFAULT],
            "unknown field": [_rule(1, "cookie", ["a"], "a"), DEFAULT],
            "condition without values": [_rule(1, "path-pattern", [], "a"), DEFAULT],
        }
        for name, rules in bad.items():
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    match_rule({"path": "/zzz"}, rules)

    def test_limits_themselves_are_allowed(self):
        three = [_rule(1, "path-pattern", ["/1", "/2", "/3"], "a"), DEFAULT]
        self.assertEqual(match_rule({"path": "/3"}, three), "a", "3 values in a condition is the limit, not an error")
        five = [{"priority": 50000, "action": "a", "conditions": [
            {"field": "path-pattern", "values": ["/1", "/2", "/3"]}, {"field": "host-header", "values": ["a", "b"]}]}, DEFAULT]
        self.assertEqual(match_rule({"path": "/2", "host": "B"}, five), "a", "5 values in a rule and priority 50000 are allowed")


# ── Exercise 05 ★: Who gets the traffic? ─────────────────────────────
"""
cross_zone_share(targets_per_az, cross_zone) -> dict[az, float]
    `targets_per_az` maps an AZ name to how many targets (instances) it holds. Return the share of
    ALL requests that ONE target in each AZ receives, as a fraction from 0 to 1.
    Cross-zone ON: the load balancer spreads over every target in every AZ → each target gets 1 / total.
    Cross-zone OFF: each AZ that has at least one target gets an EQUAL slice of the traffic, then
    splits it among its own targets → 1 / (AZs with targets) / (targets in this AZ).
    An AZ with no targets gets 0.0 either way. Negative counts, or no targets at all → ValueError.
    The AWS docs example, AZ-a has 2 targets and AZ-b has 8:
        cross_zone_share({"a": 2, "b": 8}, True)  == {"a": 0.1,  "b": 0.1}      every target 10%
        cross_zone_share({"a": 2, "b": 8}, False) == {"a": 0.25, "b": 0.0625}   a: 25% each, b: 6.25% each
alb_monthly_cost(lcus, hours=730, price=PRICES) -> float
    hours x (alb_per_hour + lcus x alb_per_lcu_hour), rounded to 2 decimal places. `lcus` is the
    average Load Balancer Capacity Units per hour. Negative lcus or hours → ValueError.
    alb_monthly_cost(10) == 74.83         alb_monthly_cost(0) == 16.43   (the hourly fee alone)
Why? An uneven target count with cross-zone off overloads the small zone's targets (25% each against
6.25% each). An ALB always has cross-zone ON at the load balancer; a Network Load Balancer has it OFF by
default, and cross-AZ data transfer charges apply when you turn it on.
Hint: total = sum(counts); live = number of AZs whose count is above 0.
"""
def cross_zone_share(targets_per_az, cross_zone):
    raise NotImplementedError  # YOUR CODE


def alb_monthly_cost(lcus, hours=730, price=PRICES):
    raise NotImplementedError  # YOUR CODE


class Ex05(Drill):
    """Who gets the traffic? ★"""
    tasks = ("2.2", "4.2")

    def test_cross_zone_on_is_even_per_target(self):
        got = cross_zone_share({"a": 2, "b": 8}, True)
        self.assertAlmostEqual(got["a"], 0.1)
        self.assertAlmostEqual(got["b"], 0.1, msg="with cross-zone on, every target gets the same share")

    def test_cross_zone_off_is_even_per_zone(self):
        got = cross_zone_share({"a": 2, "b": 8}, False)
        self.assertAlmostEqual(got["a"], 0.25, msg="each of the 2 zones gets half; a splits it over 2 targets")
        self.assertAlmostEqual(got["b"], 0.0625, msg="b splits its half over 8 targets")
        three = cross_zone_share({"a": 1, "b": 1, "c": 4}, False)
        self.assertAlmostEqual(three["a"], 1 / 3)
        self.assertAlmostEqual(three["c"], 1 / 12)

    def test_a_zone_without_targets(self):
        for cross_zone in (True, False):
            got = cross_zone_share({"a": 2, "b": 0}, cross_zone)
            with self.subTest(cross_zone=cross_zone):
                self.assertEqual(got["b"], 0.0)
                self.assertAlmostEqual(got["a"], 0.5, msg="the empty zone gets no traffic, so the others share everything")

    def test_shares_add_up(self):
        counts = {"a": 3, "b": 5, "c": 2}
        for cross_zone in (True, False):
            got = cross_zone_share(counts, cross_zone)
            with self.subTest(cross_zone=cross_zone):
                self.assertAlmostEqual(sum(got[az] * n for az, n in counts.items()), 1.0)

    def test_bad_counts(self):
        for counts in ({"a": 0, "b": 0}, {}, {"a": -1, "b": 3}):
            with self.subTest(counts=counts):
                with self.assertRaises(ValueError):
                    cross_zone_share(counts, True)

    def test_alb_cost(self):
        self.assertEqual(alb_monthly_cost(10), 74.83)
        self.assertEqual(alb_monthly_cost(0), 16.43)
        self.assertEqual(alb_monthly_cost(0, hours=100), 2.25)

    def test_alb_cost_uses_the_price_argument(self):
        custom = dict(PRICES, alb_per_hour=1.0, alb_per_lcu_hour=0.5)
        self.assertEqual(alb_monthly_cost(5, hours=100, price=custom), 350.0)
        for args in ((-1,), (1, -5)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    alb_monthly_cost(*args)


# ── Exercise 06: A fleet that heals itself ───────────────────────────
"""
latest_ami(ssm) -> str
    The AMI id AWS publishes in the public SSM parameter
    /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64 (Amazon Linux 2023 for Graviton).
    Never hard-code an AMI id: it differs per Region and goes stale. The parameter always points at the latest.
create_web_fleet(ec2, autoscaling, subnet_ids, sg_id, profile_name, ami_id) -> dict
    Build shortly's web fleet and return {"launch_template_id": …, "asg_name": "shortly-web"}.
    Launch template "shortly-web":
      ImageId ami_id · InstanceType "t4g.small" (Graviton: cheaper, see drill 1) ·
      IamInstanceProfile {"Name": profile_name} · SecurityGroupIds [sg_id] ·
      MetadataOptions HttpTokens "required", HttpPutResponseHopLimit 1, HttpEndpoint "enabled"
      (IMDSv2 only: the token requirement stops a stolen URL from reading the instance's credentials).
    Auto Scaling group "shortly-web":
      launch template at version "$Latest" · MinSize 2, MaxSize 6, DesiredCapacity 2 ·
      VPCZoneIdentifier = ALL the subnet ids joined with "," (one subnet per AZ: that is how it survives an AZ) ·
      HealthCheckType "ELB" · HealthCheckGracePeriod 120 (seconds before health checks start counting)
    A target-tracking scaling policy named "cpu-50" on the group: predefined metric
    ASGAverageCPUUtilization, TargetValue 50.
Hint: ssm.get_parameter(Name=…)["Parameter"]["Value"]; ec2.create_launch_template(LaunchTemplateName=…,
      LaunchTemplateData={…}); autoscaling.create_auto_scaling_group(AutoScalingGroupName=…, LaunchTemplate={
      "LaunchTemplateId": …, "Version": "$Latest"}, …); autoscaling.put_scaling_policy(PolicyType="TargetTrackingScaling",
      TargetTrackingConfiguration={"PredefinedMetricSpecification": {"PredefinedMetricType": …}, "TargetValue": …}).
"""
AMI_PARAMETER = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"


def latest_ami(ssm):
    raise NotImplementedError  # YOUR CODE


def create_web_fleet(ec2, autoscaling, subnet_ids, sg_id, profile_name, ami_id):
    raise NotImplementedError  # YOUR CODE


from _harness.awslib import ec2types as _ref_types  # noqa: E402


class Ex06(Drill):
    """A fleet that heals itself"""
    tasks = ("2.2", "3.2")
    uses_aws = True

    def make(self):
        ec2, autoscaling, ssm = self.client("ec2"), self.client("autoscaling"), self.client("ssm")
        vpc = ec2.create_vpc(CidrBlock="10.60.0.0/16")["Vpc"]["VpcId"]
        subnets = [ec2.create_subnet(VpcId=vpc, CidrBlock=f"10.60.{i}.0/24", AvailabilityZone=az)["Subnet"]["SubnetId"]
                   for i, az in enumerate(("us-east-1a", "us-east-1b"))]
        sg = ec2.create_security_group(GroupName="shortly-app", Description="app", VpcId=vpc)["GroupId"]
        ami = ssm.get_parameter(Name=AMI_PARAMETER)["Parameter"]["Value"]
        out = create_web_fleet(ec2, autoscaling, subnets, sg, "shortly-app-profile", ami)
        return ec2, autoscaling, subnets, sg, ami, out

    def template(self, ec2, out):
        versions = ec2.describe_launch_template_versions(LaunchTemplateId=out["launch_template_id"], Versions=["$Latest"])
        return versions["LaunchTemplateVersions"][0]["LaunchTemplateData"]

    def group(self, autoscaling):
        return autoscaling.describe_auto_scaling_groups(AutoScalingGroupNames=["shortly-web"])["AutoScalingGroups"][0]

    def test_latest_ami(self):
        ssm = self.client("ssm")
        self.assertEqual(latest_ami(ssm), ssm.get_parameter(Name=AMI_PARAMETER)["Parameter"]["Value"])
        self.assertTrue(latest_ami(ssm).startswith("ami-"))

    def test_returns_the_ids(self):
        ec2, autoscaling, *_, out = self.make()
        self.assertEqual(set(out), {"launch_template_id", "asg_name"})
        self.assertEqual(out["asg_name"], "shortly-web")
        names = [t["LaunchTemplateName"] for t in ec2.describe_launch_templates(LaunchTemplateIds=[out["launch_template_id"]])["LaunchTemplates"]]
        self.assertEqual(names, ["shortly-web"])

    def test_launch_template_is_graviton_and_imdsv2_only(self):
        ec2, _, _, sg, ami, out = self.make()
        data = self.template(ec2, out)
        self.assertEqual((data["ImageId"], data["InstanceType"]), (ami, "t4g.small"))
        self.assertEqual(_ref_types.decode(data["InstanceType"])["processor"], "AWS Graviton")
        self.assertEqual(data["IamInstanceProfile"]["Name"], "shortly-app-profile")
        self.assertEqual(data["SecurityGroupIds"], [sg])
        meta = data["MetadataOptions"]
        self.assertEqual(meta["HttpTokens"], "required", "IMDSv2 only: a token is required to read instance metadata")
        self.assertEqual((meta["HttpPutResponseHopLimit"], meta["HttpEndpoint"]), (1, "enabled"))

    def test_group_size_and_zones(self):
        ec2, autoscaling, subnets, _, _, out = self.make()
        group = self.group(autoscaling)
        self.assertEqual((group["MinSize"], group["MaxSize"], group["DesiredCapacity"]), (2, 6, 2))
        self.assertEqual(set(group["VPCZoneIdentifier"].split(",")), set(subnets), "the group must use a subnet in every AZ")
        self.assertEqual(len(group["Instances"]), 2, "two instances should be launched")

    def test_group_uses_the_template_and_elb_health(self):
        _, autoscaling, _, _, _, out = self.make()
        group = self.group(autoscaling)
        launch = group["LaunchTemplate"]
        self.assertEqual((launch["LaunchTemplateId"], launch["Version"]), (out["launch_template_id"], "$Latest"))
        self.assertEqual(group["HealthCheckType"], "ELB", "replace instances the load balancer calls unhealthy, not only dead ones")
        self.assertEqual(group["HealthCheckGracePeriod"], 120)

    def test_cpu_target_tracking_policy(self):
        _, autoscaling, *_ = self.make()
        policies = autoscaling.describe_policies(AutoScalingGroupName="shortly-web")["ScalingPolicies"]
        self.assertEqual([p["PolicyName"] for p in policies], ["cpu-50"])
        self.assertEqual(policies[0]["PolicyType"], "TargetTrackingScaling")
        config = policies[0]["TargetTrackingConfiguration"]
        self.assertEqual(config["PredefinedMetricSpecification"]["PredefinedMetricType"], "ASGAverageCPUUtilization")
        self.assertEqual(config["TargetValue"], 50.0)


# ── Exercise 07: A load balancer with rules ──────────────────────────
"""
build_alb(elbv2, vpc_id, subnet_ids, sg_id) -> {"lb_arn": …, "tg_arn": …, "listener_arn": …}
    Target group "shortly-app": protocol HTTP, port 8000, in the VPC, target type "instance",
    health check path "/healthz", success codes (Matcher HttpCode) "200".
    Load balancer "shortly-alb": type "application", scheme "internet-facing", in the subnets,
    with the security group.
    Listener on HTTP port 80 whose DEFAULT action forwards to the target group.
    Two rules on that listener:
      priority 10  path-pattern /healthz → a fixed response: status 404, content type text/plain,
                   body "not found"  (the health check hits the instances directly; the internet
                   has no business reading it through the load balancer)
      priority 20  path-pattern /api/*   → forward to the target group
    Why numbers like 10 and 20? Leave gaps so a rule can be slipped in between later.
Note: moto lists rules in creation order and keeps every field you sent. Real AWS lists them by priority.
Hint: elbv2.create_target_group(Name=…, Protocol=…, Port=…, VpcId=…, TargetType=…, HealthCheckPath=…,
      Matcher={"HttpCode": "200"}); create_load_balancer(Name=…, Subnets=…, SecurityGroups=…, Scheme=…, Type=…);
      create_listener(LoadBalancerArn=…, Protocol="HTTP", Port=80, DefaultActions=[{"Type": "forward", "TargetGroupArn": …}]);
      create_rule(ListenerArn=…, Priority=10, Conditions=[{"Field": "path-pattern", "Values": ["/healthz"]}],
      Actions=[{"Type": "fixed-response", "FixedResponseConfig": {…}}]).
"""
def build_alb(elbv2, vpc_id, subnet_ids, sg_id):
    raise NotImplementedError  # YOUR CODE


from _harness.awslib import elb as _ref_elb  # noqa: E402


class Ex07(Drill):
    """A load balancer with rules"""
    tasks = ("2.1", "2.2")
    uses_aws = True

    def make(self):
        ec2, elbv2 = self.client("ec2"), self.client("elbv2")
        vpc = ec2.create_vpc(CidrBlock="10.70.0.0/16")["Vpc"]["VpcId"]
        subnets = [ec2.create_subnet(VpcId=vpc, CidrBlock=f"10.70.{i}.0/24", AvailabilityZone=az)["Subnet"]["SubnetId"]
                   for i, az in enumerate(("us-east-1a", "us-east-1b"))]
        sg = ec2.create_security_group(GroupName="shortly-alb", Description="alb", VpcId=vpc)["GroupId"]
        return elbv2, vpc, subnets, sg, build_alb(elbv2, vpc, subnets, sg)

    def rules(self, elbv2, out):
        found = elbv2.describe_rules(ListenerArn=out["listener_arn"])["Rules"]
        return sorted((r for r in found if not r.get("IsDefault") and r["Priority"] != "default"), key=lambda r: int(r["Priority"]))

    def as_model(self, elbv2, out):
        """Turn the rules read back from (fake) AWS into the drill-04 rule format."""
        def action(actions):
            first = actions[0]
            if first["Type"] == "fixed-response":
                return f"fixed-response {first['FixedResponseConfig']['StatusCode']}"
            return "forward"
        model = []
        for rule in self.rules(elbv2, out):
            conditions = []
            for cond in rule["Conditions"]:
                values = cond.get("Values") or cond.get("PathPatternConfig", {}).get("Values")
                conditions.append({"field": cond["Field"], "values": values})
            model.append({"priority": int(rule["Priority"]), "conditions": conditions, "action": action(rule["Actions"])})
        return model + [{"priority": "default", "action": "forward"}]

    def test_target_group(self):
        elbv2, vpc, _, _, out = self.make()
        tg = elbv2.describe_target_groups(TargetGroupArns=[out["tg_arn"]])["TargetGroups"][0]
        self.assertEqual((tg["TargetGroupName"], tg["Protocol"], tg["Port"], tg["VpcId"], tg["TargetType"]),
                         ("shortly-app", "HTTP", 8000, vpc, "instance"))
        self.assertEqual(tg["HealthCheckPath"], "/healthz")
        self.assertEqual(tg["Matcher"]["HttpCode"], "200")

    def test_load_balancer(self):
        elbv2, _, subnets, sg, out = self.make()
        lb = elbv2.describe_load_balancers(LoadBalancerArns=[out["lb_arn"]])["LoadBalancers"][0]
        self.assertEqual((lb["LoadBalancerName"], lb["Type"], lb["Scheme"]), ("shortly-alb", "application", "internet-facing"))
        self.assertEqual(lb["SecurityGroups"], [sg])
        self.assertEqual({z["SubnetId"] for z in lb["AvailabilityZones"]}, set(subnets), "put the load balancer in a subnet of every AZ")

    def test_listener_forwards_by_default(self):
        elbv2, _, _, _, out = self.make()
        listener = elbv2.describe_listeners(ListenerArns=[out["listener_arn"]])["Listeners"][0]
        self.assertEqual((listener["Protocol"], listener["Port"], listener["LoadBalancerArn"]), ("HTTP", 80, out["lb_arn"]))
        default = listener["DefaultActions"][0]
        self.assertEqual((default["Type"], default["TargetGroupArn"]), ("forward", out["tg_arn"]))

    def test_the_two_rules(self):
        elbv2, _, _, _, out = self.make()
        rules = self.rules(elbv2, out)
        self.assertEqual([r["Priority"] for r in rules], ["10", "20"], "exactly two numbered rules, priority 10 and 20")
        healthz, api = rules
        self.assertEqual(healthz["Conditions"][0]["Field"], "path-pattern")
        fixed = healthz["Actions"][0]
        self.assertEqual(fixed["Type"], "fixed-response", "/healthz must be answered by the load balancer itself")
        self.assertEqual((fixed["FixedResponseConfig"]["StatusCode"], fixed["FixedResponseConfig"]["ContentType"],
                          fixed["FixedResponseConfig"]["MessageBody"]), ("404", "text/plain", "not found"))
        self.assertEqual((api["Actions"][0]["Type"], api["Actions"][0]["TargetGroupArn"]), ("forward", out["tg_arn"]))

    def test_requests_are_routed_as_intended(self):
        elbv2, _, _, _, out = self.make()
        model = self.as_model(elbv2, out)
        for request, want in (({"method": "GET", "path": "/healthz"}, "fixed-response 404"),
                              ({"method": "POST", "path": "/api/links"}, "forward"),
                              ({"method": "GET", "path": "/Ab3dE9x"}, "forward")):
            with self.subTest(request=request):
                self.assertEqual(_ref_elb.match_rule(request, model), want)
        self.assertEqual([r["field"] for rule in model[:-1] for r in rule["conditions"]], ["path-pattern", "path-pattern"])


# ── Exercise 08 (fix the bug): Settings that bite ────────────────────
"""
shortly's web fleet sits behind an Application Load Balancer. fleet_settings(subnet_ids,
launch_template_id) returns the settings for the launch template ("launch_template_data") and the
Auto Scaling group ("asg"). It works — and it is wrong in five ways. The team reports:
  - Security found that a bug in the app (an SSRF) let a visitor fetch the instance's temporary
    credentials from the metadata service.
  - A deploy shipped an app that crashes on start. Every instance showed "running" and all
    status checks passed, yet the load balancer sent users 502 errors for hours and nothing was replaced.
  - New instances take about 90 seconds to boot and pass their first health check. During a scale-out
    they keep being terminated and replaced before they ever serve a request.
  - When one Availability Zone had an outage the whole site went down.
  - With a single instance, any restart or failed check is an outage: there is no high availability.
Fix fleet_settings (keep everything that already works: the group size limits, the launch template
reference and the target group). The tests name each symptom, and one test builds the fleet in moto.
Hint: read the symptoms as settings — one metadata option, two health-check settings, one list of
      subnets, one minimum. Do not weaken anything else.
"""
TARGET_GROUP_ARN = "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/shortly-app/0123456789abcdef"


def fleet_settings(subnet_ids, launch_template_id):
    return {
        "launch_template_data": {
            "InstanceType": "t4g.small",
            "MetadataOptions": {"HttpTokens": "optional", "HttpPutResponseHopLimit": 1, "HttpEndpoint": "enabled"},
        },
        "asg": {
            "MinSize": 1, "MaxSize": 6, "DesiredCapacity": 1,
            "LaunchTemplate": {"LaunchTemplateId": launch_template_id, "Version": "$Latest"},
            "VPCZoneIdentifier": subnet_ids[0],
            "TargetGroupARNs": [TARGET_GROUP_ARN],
            "HealthCheckType": "EC2",
            "HealthCheckGracePeriod": 0,
        },
    }


class Ex08(Drill):
    """Settings that bite (fix the bug)"""
    tasks = ("1.2", "2.2")
    uses_aws = True
    SUBNETS = ["subnet-0a1", "subnet-0b2", "subnet-0c3"]

    def settings(self):
        return fleet_settings(self.SUBNETS, "lt-0abc")

    def test_instance_metadata_needs_a_token(self):
        meta = self.settings()["launch_template_data"]["MetadataOptions"]
        self.assertEqual(meta["HttpTokens"], "required",
                         "symptom: credentials stolen through the metadata service — require IMDSv2 tokens")
        self.assertEqual(meta["HttpEndpoint"], "enabled", "keep the metadata service on: the instance still needs its role credentials")

    def test_the_load_balancer_check_counts(self):
        asg = self.settings()["asg"]
        self.assertTrue(asg["TargetGroupARNs"], "keep the target group")
        self.assertEqual(asg["HealthCheckType"], "ELB",
                         "symptom: a crashed app was never replaced — EC2 status checks cannot see an app that has crashed")

    def test_new_instances_get_time_to_boot(self):
        grace = self.settings()["asg"]["HealthCheckGracePeriod"]
        self.assertGreaterEqual(grace, 90, "symptom: instances killed while booting — the grace period must cover the boot time")
        self.assertLessEqual(grace, 600, "a grace period of many minutes also hides a broken instance for too long")

    def test_every_zone_is_used(self):
        zones = self.settings()["asg"]["VPCZoneIdentifier"]
        self.assertEqual(set(zones.split(",")), set(self.SUBNETS), "symptom: one AZ outage took everything — use all the subnets")
        self.assertIsInstance(zones, str, "VPCZoneIdentifier is one string, ids joined with commas")

    def test_at_least_two_instances(self):
        asg = self.settings()["asg"]
        self.assertGreaterEqual(asg["MinSize"], 2, "symptom: one instance is no high availability — keep at least two running")
        self.assertGreaterEqual(asg["DesiredCapacity"], asg["MinSize"])

    def test_nothing_else_changed(self):
        asg = self.settings()["asg"]
        self.assertEqual(self.settings()["launch_template_data"]["MetadataOptions"]["HttpTokens"], "required",
                         "fix the bugs first; then this test checks that you did not break anything else")
        self.assertEqual(asg["MaxSize"], 6)
        self.assertEqual(asg["LaunchTemplate"], {"LaunchTemplateId": "lt-0abc", "Version": "$Latest"})
        self.assertEqual(self.settings()["launch_template_data"]["InstanceType"], "t4g.small")
        self.assertEqual(self.settings()["launch_template_data"]["MetadataOptions"]["HttpPutResponseHopLimit"], 1)

    def test_the_settings_create_a_fleet(self):
        ec2, autoscaling, elbv2, ssm = (self.client(s) for s in ("ec2", "autoscaling", "elbv2", "ssm"))
        vpc = ec2.create_vpc(CidrBlock="10.80.0.0/16")["Vpc"]["VpcId"]
        subnets = [ec2.create_subnet(VpcId=vpc, CidrBlock=f"10.80.{i}.0/24", AvailabilityZone=az)["Subnet"]["SubnetId"]
                   for i, az in enumerate(("us-east-1a", "us-east-1b"))]
        tg = elbv2.create_target_group(Name="shortly-app", Protocol="HTTP", Port=8000, VpcId=vpc)["TargetGroups"][0]["TargetGroupArn"]
        ami = ssm.get_parameter(Name=AMI_PARAMETER)["Parameter"]["Value"]
        data = dict(fleet_settings(subnets, "lt-placeholder")["launch_template_data"], ImageId=ami)
        lt = ec2.create_launch_template(LaunchTemplateName="shortly-web", LaunchTemplateData=data)["LaunchTemplate"]["LaunchTemplateId"]
        asg = dict(fleet_settings(subnets, lt)["asg"], TargetGroupARNs=[tg])
        autoscaling.create_auto_scaling_group(AutoScalingGroupName="shortly-web", **asg)
        group = autoscaling.describe_auto_scaling_groups(AutoScalingGroupNames=["shortly-web"])["AutoScalingGroups"][0]
        want = fleet_settings(subnets, lt)
        self.assertEqual(group["MaxSize"], want["asg"]["MaxSize"])
        self.assertEqual(len(group["Instances"]), group["DesiredCapacity"])
        self.assertGreaterEqual(len(group["Instances"]), 2, "a real fleet starts with at least two instances")
        got = ec2.describe_launch_template_versions(LaunchTemplateId=lt, Versions=["$Latest"])["LaunchTemplateVersions"][0]
        self.assertEqual(got["LaunchTemplateData"]["MetadataOptions"], want["launch_template_data"]["MetadataOptions"])
        self.assertEqual((group["HealthCheckType"], group["HealthCheckGracePeriod"]),
                         (want["asg"]["HealthCheckType"], want["asg"]["HealthCheckGracePeriod"]))
        self.assertEqual(set(group["VPCZoneIdentifier"].split(",")), set(subnets), "the group must really sit in every subnet")


# ── Exercise 09 (decide): Where should these instances live? ─────────
"""
Placement groups control WHERE instances sit on AWS hardware. Choose one for each scenario:
  "cluster"    packed close together in one AZ: lowest latency, highest network throughput, one failure can hit all
  "spread"     each instance on distinct hardware (its own rack): at most 7 running instances per AZ per group
  "partition"  groups of instances on separate racks, and you can see which instance sits in which partition:
               for big, rack-aware systems (HDFS, HBase, Cassandra, Kafka); at most 7 partitions per AZ
  "none"       no placement group at all: the default, and EC2 already tries to spread instances out
Replace every None in PLACEMENT with one of those words.
Then choose a purchasing option for each scenario in PURCHASE:
  "on-demand", "savings plan", "reserved instance", "spot", "dedicated host", "capacity reservation"
Last, write max_spread_instances(azs) -> int: how many instances a spread placement group can hold
across `azs` AZs (7 running instances per AZ). Fewer than 1 AZ → ValueError.
    max_spread_instances(3) == 21
(The answers are stored as hashes, so reading the test will not give them away.)
"""
PLACEMENT_SCENARIOS = {
    1: "A 16-node tightly coupled HPC job that needs the lowest possible network latency between nodes.",
    2: "Three critical instances (a primary, a standby and a witness) must never share the same hardware.",
    3: "A 60-node HDFS/HBase cluster whose software is rack-aware and needs to know which rack each node is on.",
    4: "Twelve critical instances over 2 AZs, each one on its own hardware, so one rack failure loses at most one.",
    5: "A stateless web fleet behind an ALB in an Auto Scaling group.",
    6: "Thirty Kafka brokers in one AZ whose replicas must be kept on different racks.",
}
PURCHASE_SCENARIOS = {
    1: "A steady 24/7 baseline for 3 years, while the team plans to move between instance families and towards Lambda.",
    2: "A nightly video-transcoding batch that can restart from checkpoints.",
    3: "Software licensed per physical core, which must run on a server where you can see the sockets and cores.",
    4: "A two-week product launch that must be sure of capacity in one AZ, with no long commitment.",
}
PLACEMENT = {n: None for n in PLACEMENT_SCENARIOS}   # YOUR ANSWERS: "cluster", "spread", "partition" or "none"
PURCHASE = {n: None for n in PURCHASE_SCENARIOS}     # YOUR ANSWERS: see the list in the docstring
PLACEMENT_DIGESTS = {
    1: "99aa07b819862d92e2d455679c5fd64ec8f05c6bd94fad4faf6f82e4323844f9",
    2: "4a2e634ba8048c5ffdee09d38c9b4902bebd7e1254767cacf59686ca9e2a013b",
    3: "68803df9e7ad9014032b7d2aefbcd67d40571de95ad4c1d09ecc477b7e2e9659",
    4: "1c98624b52516fac1c51d43c0ff02f75e8aaaa040e8478987ee5a21a7acbabaf",
    5: "bf59fa373098491dfb6816f0a1c671ecc92e559010a80b7cf0d795757501991d",
    6: "ed2400e3757fccb437c02cc6efbe65a7297b679b43e68346e40a53cf5fb79c6a",
}
PURCHASE_DIGESTS = {
    1: "037a90c81ae22195bdbe8ddbb2dfacda13d376dc086b0f6a8a7b1bb386bca1e4",
    2: "8fad2a8b4478ea5a35a6965fd3fd641b9f8cf56f9fd06b599f68cf0e157414bc",
    3: "205cd608e6e3bfdbdd6d73bb68075f8d715931e7b0086841280d1f929c6bebc1",
    4: "5bda520c2543fd0ad0b68d9e1621cc09a980a415b550fcc2ce9407f8e2708f7b",
}


def max_spread_instances(azs):
    raise NotImplementedError  # YOUR CODE


class Ex09(Drill):
    """Where should these instances live? (decide)"""
    tasks = ("3.2", "4.2")
    STRATEGIES = ("cluster", "spread", "partition", "none")
    OPTIONS = ("on-demand", "savings plan", "reserved instance", "spot", "dedicated host", "capacity reservation")

    def test_placement(self):
        for n, story in PLACEMENT_SCENARIOS.items():
            with self.subTest(scenario=n):
                value = PLACEMENT.get(n)
                self.assertIn(value, self.STRATEGIES, f"placement {n}: answer one of {self.STRATEGIES}, not {value!r}")
                self.assertHashed(value, f"w03-ex09-p{n}", PLACEMENT_DIGESTS[n],
                                  f"placement {n} ({story}): {value!r} is not right — latency, hardware failure or rack awareness?")

    def test_purchasing(self):
        for n, story in PURCHASE_SCENARIOS.items():
            with self.subTest(scenario=n):
                value = PURCHASE.get(n)
                self.assertIn(value, self.OPTIONS, f"purchase {n}: answer one of {self.OPTIONS}, not {value!r}")
                self.assertHashed(value, f"w03-ex09-b{n}", PURCHASE_DIGESTS[n],
                                  f"purchase {n} ({story}): {value!r} is not right — what does the team need to be flexible or sure of?")

    def test_spread_limit(self):
        for azs, want in {1: 7, 2: 14, 3: 21, 6: 42}.items():
            with self.subTest(azs=azs):
                self.assertEqual(max_spread_instances(azs), want, "7 running instances per AZ per spread group")

    def test_spread_limit_rejects_no_zones(self):
        for azs in (0, -1):
            with self.subTest(azs=azs):
                with self.assertRaises(ValueError):
                    max_spread_instances(azs)


# ── Exercise 10 (predict): What does Auto Scaling do? ────────────────
"""
For each scenario, work out the answer BEFORE running anything and write it in PREDICTIONS.
Answers are whole numbers or the exact words named in each scenario. The test asks the course's
reference models (scaling.py and elb.py) for the truth and shows it when you are wrong.
"""
from _harness.awslib import elb as _ref_lb  # noqa: E402
from _harness.awslib import scaling as _ref_scaling  # noqa: E402

_PRIORITY_RULES = [
    {"priority": 5, "conditions": [{"field": "path-pattern", "values": ["/api/*"]}], "action": "forward api"},
    {"priority": 1, "conditions": [{"field": "host-header", "values": ["admin.*"]}], "action": "fixed-response 403"},
    {"priority": "default", "action": "forward web"},
]
SCENARIOS = {
    1: ("A group has 6 instances, min 2, max 12, with a target-tracking policy at 60% CPU. Average CPU jumps to 75%. How many instances does it want? (a number)",
        ("tracking", 6, 75, 60, 2, 12)),
    2: ("The same group, but average CPU falls to 35%. How many instances does it want? (a number)",
        ("tracking", 6, 35, 60, 2, 12)),
    3: ("The group uses EC2 health checks. The app on one instance has crashed, but the instance is running and its status checks pass. Is it replaced? ('yes' or 'no')",
        ("replace", "EC2", True, False)),
    4: ("The same crashed app, but the group uses ELB health checks and the load balancer's check fails. Is it replaced? ('yes' or 'no')",
        ("replace", "ELB", True, False)),
    5: ("Cross-zone load balancing is off. AZ-a has 1 target, AZ-b has 3. What percent of all requests does the AZ-a target receive? (a whole number)",
        ("share", {"a": 1, "b": 3}, "a")),
    6: ("A listener has: priority 5 path /api/* → forward api; priority 1 host admin.* → fixed-response 403; default → forward web. "
        "A request arrives for host admin.shortly.example, path /api/x. Which action answers? ('forward api', 'fixed-response 403' or 'forward web')",
        ("rule", {"host": "admin.shortly.example", "path": "/api/x"}, _PRIORITY_RULES)),
}
PREDICTIONS = {n: None for n in SCENARIOS}   # YOUR ANSWERS: numbers or the exact words


def _truth(kind, *args):
    if kind == "tracking":
        return _ref_scaling.target_tracking(*args)
    if kind == "replace":
        return "yes" if _ref_scaling.replaces_instance(*args) else "no"
    if kind == "share":
        return round(_ref_lb.cross_zone_share(args[0], False)[args[1]] * 100)
    return _ref_lb.match_rule(*args)


class Ex10(Drill):
    """What does Auto Scaling do? (predict)"""
    tasks = ("2.1", "3.2")

    def test_predictions(self):
        for n, (story, scenario) in SCENARIOS.items():
            with self.subTest(scenario=n):
                truth = _truth(*scenario)
                self.assertIsNotNone(PREDICTIONS.get(n), f"scenario {n}: write your answer (a number or the exact words)")
                self.assertEqual(PREDICTIONS[n], truth, f"scenario {n}: {story} — the answer is {truth!r}")


if __name__ == "__main__":
    run()
````

### `week_03_compute_and_scaling/practice/solutions.py`

````python
"""Reference solutions for week 03.

Drills 01–05: the course's reference models ARE the solution — read _harness/awslib/ec2types.py,
purchasing.py, scaling.py and elb.py and compare them with yours.
"""
from _harness.awslib.ec2types import choose_type, decode  # noqa: F401
from _harness.awslib.elb import alb_monthly_cost, cross_zone_share, match_rule  # noqa: F401
from _harness.awslib.purchasing import break_even_hours, cheapest, monthly_cost  # noqa: F401
from _harness.awslib.scaling import simple_scaling_run, step_scaling, target_tracking  # noqa: F401


def latest_ami(ssm):
    return ssm.get_parameter(Name=AMI_PARAMETER)["Parameter"]["Value"]


def create_web_fleet(ec2, autoscaling, subnet_ids, sg_id, profile_name, ami_id):
    template = ec2.create_launch_template(LaunchTemplateName="shortly-web", LaunchTemplateData={
        "ImageId": ami_id, "InstanceType": "t4g.small",
        "IamInstanceProfile": {"Name": profile_name}, "SecurityGroupIds": [sg_id],
        "MetadataOptions": {"HttpTokens": "required", "HttpPutResponseHopLimit": 1, "HttpEndpoint": "enabled"},
    })["LaunchTemplate"]["LaunchTemplateId"]
    autoscaling.create_auto_scaling_group(
        AutoScalingGroupName="shortly-web", LaunchTemplate={"LaunchTemplateId": template, "Version": "$Latest"},
        MinSize=2, MaxSize=6, DesiredCapacity=2, VPCZoneIdentifier=",".join(subnet_ids),
        HealthCheckType="ELB", HealthCheckGracePeriod=120)
    autoscaling.put_scaling_policy(
        AutoScalingGroupName="shortly-web", PolicyName="cpu-50", PolicyType="TargetTrackingScaling",
        TargetTrackingConfiguration={"PredefinedMetricSpecification": {"PredefinedMetricType": "ASGAverageCPUUtilization"},
                                     "TargetValue": 50.0})
    return {"launch_template_id": template, "asg_name": "shortly-web"}


def build_alb(elbv2, vpc_id, subnet_ids, sg_id):
    tg = elbv2.create_target_group(Name="shortly-app", Protocol="HTTP", Port=8000, VpcId=vpc_id, TargetType="instance",
                                   HealthCheckPath="/healthz", Matcher={"HttpCode": "200"})["TargetGroups"][0]["TargetGroupArn"]
    lb = elbv2.create_load_balancer(Name="shortly-alb", Subnets=list(subnet_ids), SecurityGroups=[sg_id],
                                    Scheme="internet-facing", Type="application")["LoadBalancers"][0]["LoadBalancerArn"]
    listener = elbv2.create_listener(LoadBalancerArn=lb, Protocol="HTTP", Port=80,
                                     DefaultActions=[{"Type": "forward", "TargetGroupArn": tg}])["Listeners"][0]["ListenerArn"]
    elbv2.create_rule(ListenerArn=listener, Priority=10, Conditions=[{"Field": "path-pattern", "Values": ["/healthz"]}],
                      Actions=[{"Type": "fixed-response", "FixedResponseConfig": {
                          "StatusCode": "404", "ContentType": "text/plain", "MessageBody": "not found"}}])
    elbv2.create_rule(ListenerArn=listener, Priority=20, Conditions=[{"Field": "path-pattern", "Values": ["/api/*"]}],
                      Actions=[{"Type": "forward", "TargetGroupArn": tg}])
    return {"lb_arn": lb, "tg_arn": tg, "listener_arn": listener}


def fleet_settings(subnet_ids, launch_template_id):
    return {
        "launch_template_data": {
            "InstanceType": "t4g.small",
            "MetadataOptions": {"HttpTokens": "required", "HttpPutResponseHopLimit": 1, "HttpEndpoint": "enabled"},
        },
        "asg": {
            "MinSize": 2, "MaxSize": 6, "DesiredCapacity": 2,
            "LaunchTemplate": {"LaunchTemplateId": launch_template_id, "Version": "$Latest"},
            "VPCZoneIdentifier": ",".join(subnet_ids),
            "TargetGroupARNs": [TARGET_GROUP_ARN],
            "HealthCheckType": "ELB",
            "HealthCheckGracePeriod": 120,
        },
    }


def max_spread_instances(azs):
    if azs < 1:
        raise ValueError("need at least one Availability Zone")
    return 7 * azs


PLACEMENT = {1: "cluster", 2: "spread", 3: "partition", 4: "spread", 5: "none", 6: "partition"}
PURCHASE = {1: "savings plan", 2: "spot", 3: "dedicated host", 4: "capacity reservation"}
PREDICTIONS = {1: 8, 2: 4, 3: "no", 4: "yes", 5: 50, 6: "fixed-response 403"}
````

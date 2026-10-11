# AWS SAA Course — Plan 2: Week 02 (VPC networking) + M02 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build week 02 — VPC networking — in the same shape as the pilot: 5 concept notes, 2 demos, 10 drills (5 ★), a 30-question quiz, a real-AWS lab with a safe cleanup, and capstone milestone M02 (the `network` stack), plus the library pieces they need.

**Architecture:** Drills 01–05 are pure-Python models whose answer keys live in `_harness/awslib/cidr.py` and `_harness/awslib/netsim.py` (reused by later weeks and by M02's tests, like `policy_eval.py` in week 01). Drills 06–08 run real boto3 against moto. `awslib/cfn.py` learns Conditions, `!If`, `!Select`, `!GetAZs`, `!Cidr`, `!ImportValue`, parameter Defaults and `AWS::NoValue`, so milestone tests can check per-environment templates. `labclean` learns EC2 instances, NAT gateways, Elastic IPs and whole VPCs, and checks tags client-side. All code in this plan was written and run in a scratch copy of the course before the plan was written (`_dev/tests`: 210 passed; `verify_course.py --week 2` drill/mutant checks all ✔; `--milestone 2` 14/14).

**Tech Stack:** as plan 1 (Python 3.14.2, moto 5.2.3, boto3 1.43.109, cfn-lint 1.57.2, pytest 9.1.1). No new packages.

**Spec:** `docs/specs/2026-10-08-aws-saa-course-design.md` §4.0–§4.5 (week 02 row, M02 row). Facts: `docs/research/2026-10-10-vpc-facts.md` (163 confirmed rows, official sources). Previous plan: `docs/specs/2026-10-08-aws-saa-plan-1-foundation-and-pilot.md` (its Global Constraints still apply).

**Execution (learner's choice, 2026-10-10: "plan week 02 now, and write it, use as many subagents as you want"):** Sonnet implementers, parallel where files are disjoint; the main session verifies every task itself (runs the commands, reads the files, blind-solves the quiz with an independent Opus agent). No git, no commits. The learner's pilot feedback (2026-10-10): week 00 "looks good"; quizzes may name services taught in later weeks — keep doing that (memory: feedback-quiz-forward-references).

## Global Constraints

- Everything in plan 1's Global Constraints (course root, `.venv` only, no git, never real AWS, Windows-first + `force_utf8`, pinned versions, drill format, content rules, quiz rules, definition of done).
- **Numbers:** every number in notes and questions comes from `docs/facts.md`; Task 2 adds the VPC rows. NAT gateway and interface-endpoint prices are illustrative (`prices.toml [vpc]`).
- **Exam vs 2026 reality:** teach the exam answer (one zonal NAT gateway per AZ for high availability); mention the newer *regional* NAT gateway availability mode once as a "changed" note; no question depends on it. Same for "the local route can be replaced by a more specific route to an appliance" (newer; one line, no questions).
- **Quiz style (ruling 8 from plan 1):** options are actions/designs only, never self-justifying; cost questions include an option that works but costs more. Services from later weeks may appear (learner preference).
- **Lab cost:** the week 02 lab may run one NAT gateway for at most 30 minutes and says so (≈ 0.045 USD/hour + data + its public IPv4 address); every created resource is tagged `saa-course=lab`, including the Elastic IP.

## Review Focus

1. **`cleanup.py` must never delete untagged EC2/VPC resources even when the server-side tag filter is ignored** (moto ignores it for NAT gateways). Test: `_dev/tests/test_labclean_vpc.py::test_deletes_tagged_vpc_and_its_contents_only` (an untagged VPC with NAT, EIP and instance survives).
2. **A VPC with resources inside that cleanup does not own** (an untagged instance in a tagged VPC) must fail loudly, not terminate the instance. Covered by design (`_delete_vpc` never terminates); the error is reported per resource and the run continues (`test_continues_after_a_failed_delete` pattern from plan 1).
3. **Learners who write `!Cidr`** must still pass the moto deploy step. Test: `test_m02_6_exports_and_deploy.py::test_deploys_in_moto` against the reference solution, which uses `!Cidr`.
4. **Per-environment templates** (Env=lab vs prod) must be checked in both modes. Tests: `test_m02_2_routing.py` parametrised on Env.
5. **M01 keeps passing** after start_milestone 2 overwrites `tests/conftest.py` and `tests/_course/`. Test: `run_milestone.py 2` runs M01's tests cumulatively (verify_course milestone check).

## Rulings made while planning (spec deviations)

- **NAT mode comes from `Env`, not a `NatMode` parameter** (spec §4.4 M02.2 says `NatMode = single | per-az`): M01's test pins `params/*.json` to exactly `{"Prefix", "Env"}`, and "prod = one NAT per AZ, lab = one NAT" is the decision anyway. Cost if wrong: a learner who wants per-AZ NAT in lab edits one condition.
- **The flow-logs delivery role lives in the `network` stack**, not `iam.yaml`: it is owned by the VPC feature and deleted with it.
- **moto cannot deploy `!Cidr`**, so the milestone conftest replaces `Fn::Cidr` with its rendered value before `create_stack` (`cfn.inline_functions`).
- **moto's CloudFormation ignores `SubnetRouteTableAssociation`**, so associations are checked structurally only (M02.2), never through the moto deploy.

## Files this plan creates or changes

```
_harness/awslib/cfn.py            (changed: Conditions, !If, !Select, !GetAZs, !Cidr, !ImportValue, Defaults, NoValue, active_resources, inline_functions)
_harness/awslib/cidr.py · netsim.py   (new: week 02 drills 01–05 answer keys)
_harness/awslib/prices.toml       (changed: [vpc] section)
_harness/labclean.py              (changed: ec2_instances, nat_gateways, elastic_ips, vpcs finders)
_dev/tests/test_cfn_intrinsics.py · test_cidr_netsim.py · test_labclean_vpc.py   (new)
_dev/mutants/week02.py · m02.py   (new)
course_project/tools/conftest.py · start_milestone.py   (changed: resources/outputs/netsim/cidr fixtures; !Cidr inlining; copies cidr.py + netsim.py)
course_project/tests/m02/test_m02_{1..6}_*.py   (new)
course_project/solutions/m02/{infra/iam.yaml, infra/network.yaml, params/*.json, README.md, .gitignore}   (new)
course_project/milestones/M02.md · course_project/README.md · DEPLOY.md   (new / changed)
docs/facts.md                     (changed: VPC networking section)
week_02_vpc_networking/README.md · concepts/01..05_*.md · concepts/demo_*.py (2) · practice/exercises.py · practice/solutions.py · quiz/questions.toml · lab/LAB.md · lab/cleanup.py   (new)
README.md · COURSE_FLOW.md · COVERAGE.md · docs/specs/2026-10-10-aws-saa-plan-2-report.md   (changed / new)
```

## Waves

| Wave | Tasks | Needs |
|---|---|---|
| A | 1 (code bundle), 2 (facts) | — |
| B | 3 (notes, demos, README, lab), 5 (M02.md + project docs) | 1, 2 |
| C | 4 (quiz + blind solve) | 3 |
| D | 6 (docs, full verification, report) | everything |

---

### Task 1: Install the verified code bundle

**Files:** every file in Appendix A (create, or replace where it already exists), exactly as given.

**Interfaces:**
- Produces (later tasks and later weeks rely on these): `cfn.parameter_values(template, params)`, `cfn.evaluate_conditions(template, params, pseudo)`, `cfn.render(value, params, pseudo, conditions)`, `cfn.active_resources(template, params, pseudo)`, `cfn.inline_functions(template, functions, params, pseudo)`, `cfn.NOVALUE`; `cidr.usable_ips / reserved_ips / prefix_for_hosts / plan_subnets / overlaps`; `netsim.route_target / sg_allows / nacl_allows / Host / tcp_connection / can_peer / can_reach / peerings_for_full_mesh / ANY_OUT / NACL_ALLOW_ALL`; `labclean.FINDERS` keys `ec2_instances`, `nat_gateways`, `elastic_ips`, `vpcs` (plus plan 1's); milestone fixtures `resources(layer, **params)`, `outputs(layer, **params)`, `netsim`, `cidr`; `prices.section("vpc")`.

- [ ] **Step 1: Write every Appendix A file** with exactly the content shown (each file's heading gives its course-relative path). Where a file already exists (`cfn.py`, `labclean.py`, `prices.toml`, `conftest.py`, `start_milestone.py`), replace the whole file. Create `course_project/solutions/m02/infra/iam.yaml`, `params/lab.json`, `params/prod.json` and `.gitignore` by copying them unchanged from `course_project/solutions/m01/`.
- [ ] **Step 2: Run the maintainer tests**

```bash
.venv/Scripts/python.exe -m pytest _dev/tests -o addopts="" -p no:cacheprovider -q | tail -1
```

Expected: `210 passed`.

- [ ] **Step 3: Check the drills and the milestone**

```bash
.venv/Scripts/python.exe week_02_vpc_networking/practice/exercises.py | tail -1
.venv/Scripts/python.exe week_02_vpc_networking/practice/exercises.py --solutions | tail -1
.venv/Scripts/python.exe verify_course.py --week 2 2>&1 | grep -E "stubs|solutions|mutant|★|tasks|drills"
.venv/Scripts/python.exe verify_course.py --milestone 1 | tail -1
.venv/Scripts/python.exe verify_course.py --milestone 2 | tail -1
```

Expected: `0/10 passing`; `10/10 passing (solutions)`; every drill and mutant line ✔ (concept/README/quiz/lab lines belong to Tasks 3–4); `10/10 checks passed`; `14/14 checks passed`.

- [ ] **Step 4: Commit** — skipped (no git).

---

### Task 2: VPC facts in `docs/facts.md`

**Files:** Modify `docs/facts.md`.

- [ ] **Step 1:** Add a section `## VPC networking (week 02)` after "Defaults that changed", built from `docs/research/2026-10-10-vpc-facts.md` sections 1–7: keep every **confirmed** row that a week 02 note or question could need (CIDR sizes, reserved IPs, secondary CIDRs, IPv6 sizes, default VPC, local route, longest-prefix match, IGW, NAT gateway (zonal; the regional mode as a "changed" row), egress-only IGW, NAT instance, SG vs NACL rules and defaults, ephemeral ports, quotas, gateway vs interface endpoints, endpoint policies and condition keys, peering rules, Transit Gateway, Site-to-Site VPN tunnels, VPC Lattice, flow-log destinations, levels, traffic types and what is not captured). Keep the research file's `Fact | Value | Changed? | Source` columns and its sources. Rows the research marked unconfirmed are NOT added; append them to the existing "Not confirmed" line instead.
- [ ] **Step 2:** Add a section `## Prices used in drills (illustrative, us-east-1)` listing each `prices.toml [vpc]` value with its research row (NAT gateway hour and GB — the research saw the us-east-2 example; mark "illustrative"), and the existing data-transfer and S3 tier rows.
- [ ] **Step 3:** `grep -c "^| " docs/facts.md` grows by at least 60; `verify_course.py --banks | grep retired` stays ✔.

---

### Task 3: Week 02 concept notes, demos, README and lab

**Files:** Create in `week_02_vpc_networking/`: `concepts/01_vpc_subnets_and_cidr.md`, `concepts/02_routing_internet_and_nat.md`, `concepts/03_security_groups_and_nacls.md`, `concepts/04_vpc_endpoints_and_privatelink.md`, `concepts/05_connecting_vpcs_and_networks.md`, `concepts/demo_vpc_in_moto.py`, `concepts/demo_packet_paths.py`, `README.md`, `lab/LAB.md`, `lab/cleanup.py`.

**Writing rules:** plan 1 Task 12's rules (first line `Exam tasks: …`; sections What it is / How it works / Numbers to know / When to choose it / Exam traps / Cost angle / Comparison; 150–300 lines; numbers only from `docs/facts.md`; plain English). Do **not** reveal drill 10's six answers or paste drill solutions; teach the rules with other examples.

| File | Exam tasks line | Must cover |
|---|---|---|
| `01_vpc_subnets_and_cidr.md` | `Exam tasks: 3.4, 1.2` | what a VPC is (Regional, spans the Region's AZs); CIDR notation and sizes (/16–/28), RFC 1918 ranges, secondary CIDR blocks; subnets live in one AZ; the 5 reserved addresses with a worked /24 and /28; public vs private vs isolated subnets (defined by routes, not by a checkbox); sizing method (biggest first, aligned — link drill 02); plan for growth and never overlap with networks you may peer with; IPv6 in one paragraph (VPC /56, subnets from facts.md); the default VPC and why production uses its own; comparison table of subnet tiers |
| `02_routing_internet_and_nat.md` | `Exam tasks: 3.4, 2.2, 4.4` | route tables, the main route table, associations; the local route; longest-prefix match (drill 03); internet gateway (what makes a subnet public; instances also need a public IP); NAT gateway (outbound-only for private subnets, lives in a public subnet, needs an Elastic IP for public NAT, zonal → one per AZ for HA, private NAT type); the regional NAT gateway mode as a one-line "changed" note; egress-only internet gateway for IPv6; NAT instance (legacy; source/destination check); bastion hosts vs Session Manager (no inbound SSH); cost of NAT (hourly + per GB + public IPv4) and the lab-vs-prod choice; comparison table IGW / NAT gateway / NAT instance / egress-only IGW |
| `03_security_groups_and_nacls.md` | `Exam tasks: 1.2` | security groups (ENI level, stateful, allow-only, default rules, referencing other groups, rules quotas); network ACLs (subnet level, stateless, numbered rules lowest first, allow + deny, default NACL vs a new custom NACL, the final `*` deny); ephemeral ports and why replies need them (drill 04); layering: SG for most control, NACL for subnet-wide deny (e.g. block an IP range); VPC Flow Logs: what they capture (ACCEPT/REJECT), destinations, what they don't capture, how to read a REJECT; comparison table SG vs NACL |
| `04_vpc_endpoints_and_privatelink.md` | `Exam tasks: 1.2, 3.4, 4.4` | why private subnets need a path to AWS services; gateway endpoints (S3 and DynamoDB only, free, route-table prefix-list routes, same Region); interface endpoints / PrivateLink (ENIs with private IPs, private DNS, charged per hour per AZ and per GB, most services); endpoint policies; bucket policies with `aws:SourceVpce` / `aws:SourceVpc`, and why `aws:SourceIp` stops working through endpoints; PrivateLink for your own services (NLB + endpoint service) and SaaS; the NAT-vs-endpoint cost comparison (drill 09) with the prices table; comparison table gateway endpoint / interface endpoint / NAT gateway |
| `05_connecting_vpcs_and_networks.md` | `Exam tasks: 3.4, 2.2, 4.4` | VPC peering (one-to-one, non-transitive, no overlapping CIDRs, cross-account and cross-Region, no edge-to-edge routing); full-mesh maths n(n−1)/2 (drill 05); Transit Gateway (Regional hub, transitive, route tables for segmentation, attachments incl. VPN and Direct Connect gateway, inter-Region peering); sharing subnets with AWS RAM (week 01) vs peering; Site-to-Site VPN (two tunnels, bandwidth per tunnel from facts.md, over the internet, encrypted); Direct Connect as a pointer to week 07; VPC Lattice one line; cost: TGW per attachment-hour + per GB vs peering's data-transfer-only; comparison table peering / Transit Gateway / VPN / PrivateLink |

- [ ] **Step 1: Write the five notes** per the table.
- [ ] **Step 2: `concepts/demo_vpc_in_moto.py`** — an offline moto demo in the style of week 00's `demo_boto3_basics.py` (path insert, `force_utf8`, `use_fake_aws_env`, `mock_aws`): build a VPC with one public and one private subnet, an internet gateway, a public route table and a private one; add an S3 gateway endpoint on the private table; print each route table's routes (showing the local route, the 0.0.0.0/0 → igw route and the prefix-list route added by the endpoint); print the reserved IPs of the public subnet using `_harness.awslib.cidr.reserved_ips`. Ends with "Now do drills 01, 03 and 06–08." Must exit 0 with stdout piped.
- [ ] **Step 3: `concepts/demo_packet_paths.py`** — pure Python with `_harness.awslib.netsim`: five connection checks printed as a table (allowed? / blocking check), using different hosts and ports from drill 10 (e.g. an internet client to an app server without a load balancer, a bastion-less SSH attempt, a NACL that forgets ephemeral ports for a database, two hosts in one subnet behind a deny-all NACL, a peering chain of three VPCs). Ends with "Now do drills 04, 05 and 10." Exit 0 piped.
- [ ] **Step 4: `README.md`** — headings as week 00/01. Goals (6): plan a VPC's address space; make a subnet public, private or isolated with routes; give private subnets safe outbound access; control traffic with security groups and network ACLs; reach AWS services privately with endpoints; connect VPCs and on-premises networks. Your week (≈ 10–12 h): notes + demos ~3 h; drills ~3 h; quiz `python quiz.py --week 2 -n 30` ~1.5 h; milestone M02 ~2–3 h; optional lab ~1 h. Exam tasks covered: 1.2, 2.2, 3.4, 4.4. Service comparison: IGW vs NAT gateway vs gateway endpoint vs interface endpoint vs peering vs Transit Gateway. Interview questions (10): e.g. "Walk through how a packet from a private instance reaches the internet", "Security group vs network ACL?", "Why one NAT gateway per AZ?", "How do private instances reach S3 without NAT?", "When would you pick Transit Gateway over peering?", "What breaks when two VPCs' CIDRs overlap?", "How would you block one malicious IP range?", "How do you debug a connection timeout in a VPC?", "How do you make a subnet public?", "How much does NAT cost and how would you cut it?". Final line: "Now you may read `_harness/awslib/cidr.py` and `netsim.py` — compare them with your drills 01–05."
- [ ] **Step 5: `lab/LAB.md` and `lab/cleanup.py`** — LAB (≈ 60–90 min; cost ≈ 0.05 USD if the NAT step stays under 30 minutes; everything else free or pennies): 1 before you start (week 00 guard rails done; profile `saa-lab`; tag EVERY resource `saa-course=lab` — VPC, Elastic IP, NAT gateway, instance; the cleanup only finds tagged ones); 2 create a VPC with the console's "VPC and more" wizard (2 AZs, 1 public + 1 private subnet per AZ, NO NAT gateways, S3 gateway endpoint on) and read what it created; 3 launch one t4g.micro or t3.micro instance in a private subnet with no key pair and an IAM role for Session Manager (`AmazonSSMManagedInstanceCore`), see it fail to register without internet; 4 add ONE NAT gateway (tag it and its Elastic IP), add 0.0.0.0/0 → NAT to the private route table, watch Session Manager connect; note the time — delete the NAT gateway within 30 minutes; 5 security groups vs NACLs: from the instance `curl https://aws.amazon.com`, then add a NACL deny rule for outbound 443 and watch it fail, remove it; 6 turn on a VPC flow log to CloudWatch Logs (retention 1 day), find an ACCEPT and a REJECT record; 7 clean up: `python lab/cleanup.py --profile saa-lab` (dry run, read it), then `--yes` (terminates tagged instances, deletes tagged NAT gateways, releases tagged Elastic IPs, deletes tagged VPCs with everything inside); delete the flow-log log group by hand; 8 what to write down. `cleanup.py` = week 01's pattern with `kinds=["ec2_instances", "nat_gateways", "elastic_ips", "vpcs"]` and a docstring naming them.
- [ ] **Step 6: Verify** — `for f in week_02_vpc_networking/concepts/demo_*.py; do .venv/Scripts/python.exe "$f" | cat; done` exit 0; `verify_course.py --week 2 2>&1 | grep -E "concept|demo|README|lab"` all ✔; `verify_course.py --banks | grep retired` ✔.

---

### Task 4: Week 02 quiz (30 questions) + blind solve

**Files:** Create `week_02_vpc_networking/quiz/questions.toml`.

- [ ] **Step 1: Write the 30 questions** (plan 1's quiz rules and ruling 8; ids `w02-q01 … w02-q30`; 3–6 Select TWO; refs = Task 3's five notes):

| ids | domain · task | topics (one question each, in order) |
|---|---|---|
| q01–q04 | 3 · 3.4 | subnet size for N hosts with the 5 reserved IPs · overlapping CIDRs block a future peering — choose a VPC CIDR · secondary CIDR to grow a full VPC · what makes a subnet public |
| q05–q09 | 2 · 2.2 | one NAT gateway per AZ vs one shared (AZ failure) · private subnets in two AZs behind an ALB · NAT gateway vs NAT instance for least operational overhead · egress-only internet gateway for IPv6 outbound · Session Manager instead of a bastion (Select TWO) |
| q10–q15 | 1 · 1.2 | SG referencing another SG · NACL to block one IP range (deny + rule order) · ephemeral ports on a custom NACL · security group default rules · stateful vs stateless troubleshooting (replies dropped) · flow logs to find rejected traffic |
| q16–q20 | 1 · 1.2 | S3 gateway endpoint + bucket policy `aws:SourceVpce` · `aws:SourceIp` stops working through an endpoint · interface endpoint for a service without a gateway endpoint (e.g. Secrets Manager) with private DNS · endpoint policy limiting buckets · PrivateLink to expose a service to another account (Select TWO) |
| q21–q25 | 3 · 3.4 | peering is not transitive · Transit Gateway for 20 VPCs · TGW route tables to isolate dev from prod · Site-to-Site VPN for quick encrypted on-premises access · shared VPC subnets via RAM vs peering |
| q26–q30 | 4 · 4.4 | NAT data-processing cost vs S3 gateway endpoint (MOST cost-effective) · interface endpoints per AZ cost · cross-AZ data transfer in a chatty design · idle Elastic IPs / public IPv4 · lab vs prod NAT choice (Select TWO) |

- [ ] **Step 2: Validate** — `verify_course.py --week 2 2>&1 | grep -i quiz` all ✔; `verify_course.py --banks | tail -6` no near-duplicates.
- [ ] **Step 3: Blind solve (main session)** — export with `_dev/blindsolve.py export`, an independent Opus agent answers from the blind file only and lists doubts, `compare`; fix every disagreement or real doubt through the implementer; re-check changed questions.

---

### Task 5: M02 spec and project docs

**Files:** Create `course_project/milestones/M02.md`; modify `course_project/README.md`, `course_project/DEPLOY.md`.

- [ ] **Step 1: `M02.md`** — same shape as M01.md: intro (the network layer; it costs money only when deployed — NAT gateways and their IPv4 addresses bill hourly); Step 0 (`start_milestone.py 2 --repo ~/code/shortly-infra`, then `run_milestone.py 2`; M01 keeps running); What the tests rely on (file `infra/network.yaml`; parameters Prefix, Env, VpcCidr default 10.20.0.0/16; Condition `IsProd`; logical ids: Vpc, PublicSubnetA/B, AppSubnetA/B, DataSubnetA/B, InternetGateway, a VPCGatewayAttachment, NatEipA/NatGatewayA (+B with Condition IsProd), PublicRouteTable, AppRouteTableA/B, DataRouteTable, AWS::EC2::Route resources, SubnetRouteTableAssociations, AlbSecurityGroup, AppSecurityGroup, DbSecurityGroup, CacheSecurityGroup, S3Endpoint, DynamoDbEndpoint, FlowLogsLogGroup (name `/${Prefix}/vpc-flow-logs`), FlowLogsRole, VpcFlowLog; the 8 exports); M02.1–M02.6 explaining each test file in plain words (sizes: public ≥ 250 usable IPs, app ≥ 1,000, data ≥ 250; A = first AZ, B = second; README "## Network plan" table); one YAML example each for a subnet with `!Select`/`!GetAZs`, the conditional NAT B and `!If` route, and one SG reference — never the whole template; Done when; Hints (plan with drill 02's function; `!Cidr [!Ref VpcCidr, count, bits]` gives equal blocks — two calls for two sizes; `DependsOn: GatewayAttachment` for routes and EIPs; SG ids via `!GetAtt X.GroupId` or `!Ref X`; the endpoint policy's `aws:ResourceAccount` condition; RetentionInDays; why lab uses one NAT); Why this matters in the exam.
- [ ] **Step 2: `course_project/README.md`** — mark M02 as built in its milestone table. **`DEPLOY.md`** — add the network stack: deploy command (`--stack-name shortly-network --parameter-overrides Prefix=shortly Env=lab`), the cost table row "NAT gateway — 1 in lab, 2 in prod — about 0.045 USD/hour each plus 0.045 USD/GB, plus 0.005 USD/hour per public IPv4 address (illustrative, docs/facts.md)", and "delete shortly-network before shortly-iam".

---

### Task 6: Course docs, full verification, report

**Files:** Modify `README.md` (week 02 row links to its README; Status: weeks 00–02 + M01–M02 built), `COURSE_FLOW.md` (add a week 02 section like week 01's, with `start_milestone.py 2` and `run_milestone.py 2`); generate `COVERAGE.md`; create `docs/specs/2026-10-10-aws-saa-plan-2-report.md`.

- [ ] **Step 1:** README and COURSE_FLOW edits.
- [ ] **Step 2 (main session):** `verify_course.py --self-test` and `verify_course.py --coverage`; everything green.
- [ ] **Step 3:** report (what was built with counts; verification results; blind-solve results; rulings; known limits; what the learner should try first).

---

## Appendix A — verified code bundle (Task 1)

Every file below was run in a scratch copy of the course on 2026-10-10. Write each one exactly.

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
    Ref, Fn::Sub, Fn::Join, Fn::GetAtt, Fn::If, Fn::Select, Fn::GetAZs, Fn::Cidr, Fn::ImportValue.
    A Ref to a resource renders as its logical id; Fn::GetAtt as "Logical.Attr"; Fn::ImportValue as
    "import:<name>"; Fn::GetAZs as the Region's names with letters a–f. Fn::If needs `conditions`
    (see evaluate_conditions). {"Ref": "AWS::NoValue"} removes the property or list item."""
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

### `_harness/awslib/cidr.py`

````python
"""cidr — IPv4 subnet maths for AWS VPCs.

This is the reference solution for week 02's drills 01–02: finish those drills before you read it.
Rules (docs/facts.md): a VPC or subnet IPv4 block is /16 to /28; AWS reserves 5 addresses in every
subnet — the network address, .1 (VPC router), .2 (Amazon DNS), .3 (future use) and the last address.
"""
from __future__ import annotations

import ipaddress

RESERVED_PER_SUBNET = 5
MIN_PREFIX, MAX_PREFIX = 16, 28


def _network(cidr: str) -> ipaddress.IPv4Network:
    try:
        net = ipaddress.ip_network(cidr, strict=True)
    except ValueError as exc:
        raise ValueError(f"not a network block: {cidr!r} ({exc})") from None
    if net.version != 4 or not MIN_PREFIX <= net.prefixlen <= MAX_PREFIX:
        raise ValueError(f"{cidr} is outside the /{MIN_PREFIX}–/{MAX_PREFIX} range AWS allows")
    return net


def usable_ips(cidr: str) -> int:
    return _network(cidr).num_addresses - RESERVED_PER_SUBNET


def reserved_ips(cidr: str) -> list[str]:
    net = _network(cidr)
    first = int(net.network_address)
    return [str(ipaddress.ip_address(first + i)) for i in range(4)] + [str(net.broadcast_address)]


def prefix_for_hosts(hosts: int) -> int:
    """The smallest subnet (largest prefix length) with at least `hosts` usable addresses."""
    if hosts < 1:
        raise ValueError("hosts must be at least 1")
    for prefix in range(MAX_PREFIX, MIN_PREFIX - 1, -1):
        if 2 ** (32 - prefix) - RESERVED_PER_SUBNET >= hosts:
            return prefix
    raise ValueError(f"{hosts} hosts do not fit in one subnet (a /{MIN_PREFIX} holds {2 ** 16 - 5})")


def plan_subnets(vpc_cidr: str, tiers: dict[str, int], azs: list[str]) -> dict[tuple[str, str], str]:
    """One subnet per (tier, AZ). `tiers` maps tier name → hosts needed in each subnet.
    Biggest subnets first (ties keep the order of `tiers`), each aligned to its own size and packed
    from the start of the VPC block. Raises ValueError when they do not fit."""
    vpc = _network(vpc_cidr)
    order = sorted(tiers, key=lambda tier: (prefix_for_hosts(tiers[tier]), list(tiers).index(tier)))
    plan, cursor, end = {}, int(vpc.network_address), int(vpc.broadcast_address)
    for tier in order:
        prefix = prefix_for_hosts(tiers[tier])
        size = 2 ** (32 - prefix)
        for az in azs:
            cursor = -(-cursor // size) * size  # align up to a multiple of the block size
            if cursor + size - 1 > end:
                raise ValueError(f"the subnets do not fit in {vpc_cidr}")
            plan[(tier, az)] = str(ipaddress.ip_network((cursor, prefix)))
            cursor += size
    return plan


def overlaps(a: str, b: str) -> bool:
    return ipaddress.ip_network(a).overlaps(ipaddress.ip_network(b))
````

### `_harness/awslib/netsim.py`

````python
"""netsim — small, readable models of VPC routing, security groups, network ACLs and VPC links.

This is the reference solution for week 02's drills 03–05: finish those drills before you read it.

Rules modelled (docs/facts.md):
  • A route table sends a packet to the target of the most specific route that contains the
    destination (longest prefix match). The local route covers the VPC's own CIDR.
  • Security groups are stateful and only allow: a reply to an allowed request is always let back.
    A rule's "peer" is a CIDR block or another security group's id.
  • Network ACLs are stateless, allow AND deny, and are checked in rule-number order — the first
    matching rule decides; if none matches, the final "*" rule denies. Replies must be allowed
    explicitly, on the client's ephemeral port. Traffic between two hosts in the same subnet does
    not cross a network ACL.
  • VPC peering is not transitive. A transit gateway is a hub: attached VPCs reach each other.
"""
from __future__ import annotations

import ipaddress
from dataclasses import dataclass

ANY_OUT = {"protocol": "-1", "ports": (0, 65535), "peer": "0.0.0.0/0"}
NACL_ALLOW_ALL = {"rule": 100, "action": "allow", "protocol": "-1", "ports": (0, 65535), "cidr": "0.0.0.0/0"}


def route_target(destination_ip: str, routes: dict[str, str]) -> str | None:
    """`routes` maps destination CIDR → target id. Returns the target of the longest matching
    prefix, or None when no route matches (the packet is dropped)."""
    ip = ipaddress.ip_address(destination_ip)
    best, best_len = None, -1
    for cidr, target in routes.items():
        net = ipaddress.ip_network(cidr)
        if ip in net and net.prefixlen > best_len:
            best, best_len = target, net.prefixlen
    return best


def _protocol_matches(rule_protocol: str, protocol: str) -> bool:
    return rule_protocol == "-1" or rule_protocol == protocol


def _port_matches(ports, protocol: str, port: int) -> bool:
    low, high = ports
    return protocol == "icmp" or low <= port <= high


def sg_allows(rules, peer_ip: str, peer_sgs, protocol: str, port: int) -> bool:
    """True if any rule allows traffic with this peer (its IP, or one of its security groups)."""
    ip = ipaddress.ip_address(peer_ip)
    for rule in rules:
        if not (_protocol_matches(rule["protocol"], protocol) and _port_matches(rule["ports"], protocol, port)):
            continue
        peer = rule["peer"]
        if peer.startswith("sg-"):
            if peer in peer_sgs:
                return True
        elif ip in ipaddress.ip_network(peer):
            return True
    return False


def nacl_allows(rules, peer_ip: str, protocol: str, port: int) -> bool:
    """Lowest rule number first; the first rule that matches decides; nothing matches → deny."""
    ip = ipaddress.ip_address(peer_ip)
    for rule in sorted(rules, key=lambda r: r["rule"]):
        if (_protocol_matches(rule["protocol"], protocol) and _port_matches(rule["ports"], protocol, port)
                and ip in ipaddress.ip_network(rule["cidr"])):
            return rule["action"] == "allow"
    return False


@dataclass(frozen=True)
class Host:
    """One network interface: its IP, subnet, security groups (ids + rules) and its subnet's NACL."""
    ip: str
    subnet: str
    sgs: tuple = ()
    sg_in: tuple = ()
    sg_out: tuple = (ANY_OUT,)
    nacl_in: tuple = (NACL_ALLOW_ALL,)
    nacl_out: tuple = (NACL_ALLOW_ALL,)


def tcp_connection(client: Host, server: Host, port: int, client_port: int = 49152) -> tuple[bool, str]:
    """Can `client` open a TCP connection to `server` on `port` and get replies back?
    Returns (True, "allowed") or (False, <the first check that blocks it>)."""
    crosses = client.subnet != server.subnet
    checks = [("client security group (outbound)",
               sg_allows(client.sg_out, server.ip, server.sgs, "tcp", port))]
    if crosses:
        checks += [("client network ACL (outbound)", nacl_allows(client.nacl_out, server.ip, "tcp", port)),
                   ("server network ACL (inbound)", nacl_allows(server.nacl_in, client.ip, "tcp", port))]
    checks.append(("server security group (inbound)", sg_allows(server.sg_in, client.ip, client.sgs, "tcp", port)))
    if crosses:  # replies: security groups are stateful, network ACLs are not
        checks += [("server network ACL (outbound, reply)", nacl_allows(server.nacl_out, client.ip, "tcp", client_port)),
                   ("client network ACL (inbound, reply)", nacl_allows(client.nacl_in, server.ip, "tcp", client_port))]
    for name, ok in checks:
        if not ok:
            return False, name
    return True, "allowed"


def can_peer(cidr_a: str, cidr_b: str) -> bool:
    """Two VPCs can be peered only if their CIDR blocks do not overlap."""
    return not ipaddress.ip_network(cidr_a).overlaps(ipaddress.ip_network(cidr_b))


def can_reach(source: str, target: str, peerings, tgw_attachments=()) -> bool:
    """`peerings` is a collection of (vpc, vpc) pairs; `tgw_attachments` the VPCs attached to one
    transit gateway (with routes to each other). Peering is not transitive."""
    if source == target:
        return True
    if {source, target} in [set(pair) for pair in peerings]:
        return True
    attached = set(tgw_attachments)
    return source in attached and target in attached


def peerings_for_full_mesh(vpcs: int) -> int:
    """Peering connections needed so every one of `vpcs` VPCs can reach every other."""
    if vpcs < 0:
        raise ValueError("vpcs must not be negative")
    return vpcs * (vpcs - 1) // 2
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


# Order matters: EC2 before VPCs; IAM roles and users before customer-managed policies.
FINDERS = {
    "s3_buckets": find_s3_buckets,
    "ec2_instances": find_ec2_instances,   # instances before their VPC
    "nat_gateways": find_nat_gateways,     # NAT gateways before the Elastic IPs they hold
    "elastic_ips": find_elastic_ips,
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
            print(f"  · {item.kind:<13} {item.name}  ({item.region})")
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
````

### `_dev/tests/test_cidr_netsim.py`

````python
import pytest

from _harness.awslib import cidr, netsim
from _harness.awslib.netsim import Host


@pytest.mark.parametrize("block, usable", [("10.0.0.0/24", 251), ("10.0.0.0/28", 11), ("10.0.0.0/16", 65531),
                                           ("10.0.0.0/20", 4091)])
def test_usable_ips(block, usable):
    assert cidr.usable_ips(block) == usable


@pytest.mark.parametrize("bad", ["10.0.0.0/29", "10.0.0.0/15", "10.0.0.1/24", "not-a-cidr", "2001:db8::/64"])
def test_usable_ips_rejects(bad):
    with pytest.raises(ValueError):
        cidr.usable_ips(bad)


def test_reserved_ips():
    assert cidr.reserved_ips("10.0.1.0/24") == ["10.0.1.0", "10.0.1.1", "10.0.1.2", "10.0.1.3", "10.0.1.255"]


@pytest.mark.parametrize("hosts, prefix", [(1, 28), (11, 28), (12, 27), (251, 24), (252, 23), (1000, 22), (65531, 16)])
def test_prefix_for_hosts(hosts, prefix):
    assert cidr.prefix_for_hosts(hosts) == prefix


def test_prefix_for_hosts_too_big():
    with pytest.raises(ValueError):
        cidr.prefix_for_hosts(65532)


def test_plan_subnets_biggest_first_and_aligned():
    plan = cidr.plan_subnets("10.0.0.0/16", {"public": 200, "app": 1000, "data": 100}, ["us-east-1a", "us-east-1b"])
    assert plan == {("app", "us-east-1a"): "10.0.0.0/22", ("app", "us-east-1b"): "10.0.4.0/22",
                    ("public", "us-east-1a"): "10.0.8.0/24", ("public", "us-east-1b"): "10.0.9.0/24",
                    ("data", "us-east-1a"): "10.0.10.0/25", ("data", "us-east-1b"): "10.0.10.128/25"}
    blocks = list(plan.values())
    assert not any(cidr.overlaps(a, b) for i, a in enumerate(blocks) for b in blocks[i + 1:])


def test_plan_subnets_does_not_fit():
    with pytest.raises(ValueError, match="do not fit"):
        cidr.plan_subnets("10.0.0.0/24", {"app": 200}, ["a", "b"])


def test_route_target_longest_prefix():
    routes = {"10.0.0.0/16": "local", "0.0.0.0/0": "igw-1", "10.1.0.0/16": "pcx-1", "10.1.5.0/24": "tgw-1"}
    assert netsim.route_target("10.0.3.4", routes) == "local"
    assert netsim.route_target("8.8.8.8", routes) == "igw-1"
    assert netsim.route_target("10.1.9.9", routes) == "pcx-1"
    assert netsim.route_target("10.1.5.9", routes) == "tgw-1"
    assert netsim.route_target("8.8.8.8", {"10.0.0.0/16": "local"}) is None


SG_ALB = "sg-alb"
SG_APP = "sg-app"


def web_hosts(nacl_in=(netsim.NACL_ALLOW_ALL,), nacl_out=(netsim.NACL_ALLOW_ALL,)):
    alb = Host(ip="10.0.0.10", subnet="public-a", sgs=(SG_ALB,))
    app = Host(ip="10.0.8.20", subnet="app-a", sgs=(SG_APP,),
               sg_in=({"protocol": "tcp", "ports": (8000, 8000), "peer": SG_ALB},),
               nacl_in=nacl_in, nacl_out=nacl_out)
    return alb, app


def test_sg_reference_allows_only_that_group():
    alb, app = web_hosts()
    assert netsim.tcp_connection(alb, app, 8000) == (True, "allowed")
    assert netsim.tcp_connection(alb, app, 22) == (False, "server security group (inbound)")
    stranger = Host(ip="10.0.0.11", subnet="public-a", sgs=("sg-other",))
    assert netsim.tcp_connection(stranger, app, 8000) == (False, "server security group (inbound)")


def test_nacl_order_and_return_traffic():
    deny_alb = ({"rule": 90, "action": "deny", "protocol": "tcp", "ports": (8000, 8000), "cidr": "10.0.0.10/32"},
                netsim.NACL_ALLOW_ALL)
    alb, app = web_hosts(nacl_in=deny_alb)
    assert netsim.tcp_connection(alb, app, 8000) == (False, "server network ACL (inbound)")
    later_deny = (netsim.NACL_ALLOW_ALL,
                  {"rule": 200, "action": "deny", "protocol": "tcp", "ports": (8000, 8000), "cidr": "10.0.0.10/32"})
    alb, app = web_hosts(nacl_in=later_deny)
    assert netsim.tcp_connection(alb, app, 8000) == (True, "allowed")  # rule 100 matched first
    only_8000_out = ({"rule": 100, "action": "allow", "protocol": "tcp", "ports": (8000, 8000), "cidr": "0.0.0.0/0"},)
    alb, app = web_hosts(nacl_out=only_8000_out)
    assert netsim.tcp_connection(alb, app, 8000) == (False, "server network ACL (outbound, reply)")
    ephemeral = ({"rule": 100, "action": "allow", "protocol": "tcp", "ports": (1024, 65535), "cidr": "0.0.0.0/0"},)
    alb, app = web_hosts(nacl_out=ephemeral)
    assert netsim.tcp_connection(alb, app, 8000) == (True, "allowed")


def test_same_subnet_skips_nacls_and_client_egress_counts():
    blocked = ({"rule": 100, "action": "deny", "protocol": "-1", "ports": (0, 65535), "cidr": "0.0.0.0/0"},)
    a = Host(ip="10.0.8.5", subnet="app-a", sgs=("sg-a",), nacl_in=blocked, nacl_out=blocked)
    b = Host(ip="10.0.8.6", subnet="app-a", sgs=("sg-b",), nacl_in=blocked, nacl_out=blocked,
             sg_in=({"protocol": "tcp", "ports": (5432, 5432), "peer": "10.0.8.0/24"},))
    assert netsim.tcp_connection(a, b, 5432) == (True, "allowed")
    no_egress = Host(ip="10.0.8.5", subnet="app-a", sgs=("sg-a",), sg_out=())
    assert netsim.tcp_connection(no_egress, b, 5432) == (False, "client security group (outbound)")


def test_empty_nacl_denies_everything():
    alb, app = web_hosts(nacl_in=())
    assert netsim.tcp_connection(alb, app, 8000) == (False, "server network ACL (inbound)")


def test_peering_and_transit_gateway():
    peerings = [("a", "b"), ("b", "c")]
    assert netsim.can_reach("a", "b", peerings)
    assert not netsim.can_reach("a", "c", peerings)  # not transitive
    assert netsim.can_reach("a", "c", peerings, tgw_attachments=["a", "c", "d"])
    assert netsim.can_reach("a", "a", [])
    assert not netsim.can_reach("a", "d", peerings, tgw_attachments=["d"])
    assert [netsim.peerings_for_full_mesh(n) for n in (0, 1, 2, 5, 10)] == [0, 0, 1, 10, 45]
    assert netsim.can_peer("10.0.0.0/16", "10.1.0.0/16")
    assert not netsim.can_peer("10.0.0.0/16", "10.0.128.0/17")
````

### `_dev/tests/test_labclean_vpc.py`

````python
import boto3
import pytest
from moto import mock_aws

from _harness import labclean

TAG = [{"Key": "saa-course", "Value": "lab"}]
KINDS = ["ec2_instances", "nat_gateways", "elastic_ips", "vpcs"]


@pytest.fixture
def aws(monkeypatch):
    monkeypatch.setattr(labclean, "WAIT_SECONDS", 0)
    with mock_aws():
        yield boto3.Session(region_name="us-east-1")


def tag(ec2, resource_id):
    ec2.create_tags(Resources=[resource_id], Tags=TAG)


def build(ec2, cidr, tagged):
    vpc = ec2.create_vpc(CidrBlock=cidr)["Vpc"]["VpcId"]
    a = ec2.create_subnet(VpcId=vpc, CidrBlock=cidr.replace("0.0/16", "1.0/24"), AvailabilityZone="us-east-1a")["Subnet"]["SubnetId"]
    b = ec2.create_subnet(VpcId=vpc, CidrBlock=cidr.replace("0.0/16", "2.0/24"), AvailabilityZone="us-east-1b")["Subnet"]["SubnetId"]
    igw = ec2.create_internet_gateway()["InternetGateway"]["InternetGatewayId"]
    ec2.attach_internet_gateway(InternetGatewayId=igw, VpcId=vpc)
    rt = ec2.create_route_table(VpcId=vpc)["RouteTable"]["RouteTableId"]
    ec2.create_route(RouteTableId=rt, DestinationCidrBlock="0.0.0.0/0", GatewayId=igw)
    ec2.associate_route_table(RouteTableId=rt, SubnetId=a)
    alb = ec2.create_security_group(GroupName="alb", Description="alb", VpcId=vpc)["GroupId"]
    app = ec2.create_security_group(GroupName="app", Description="app", VpcId=vpc)["GroupId"]
    ec2.authorize_security_group_ingress(GroupId=app, IpPermissions=[{"IpProtocol": "tcp", "FromPort": 8000, "ToPort": 8000,
                                                                      "UserIdGroupPairs": [{"GroupId": alb}]}])
    acl = ec2.create_network_acl(VpcId=vpc)["NetworkAcl"]["NetworkAclId"]
    ec2.create_vpc_endpoint(VpcEndpointType="Gateway", VpcId=vpc, ServiceName="com.amazonaws.us-east-1.s3", RouteTableIds=[rt])
    eip = ec2.allocate_address(Domain="vpc")["AllocationId"]
    nat = ec2.create_nat_gateway(SubnetId=a, AllocationId=eip)["NatGateway"]["NatGatewayId"]
    image = ec2.describe_images(Owners=["amazon"])["Images"][0]["ImageId"]
    instance = ec2.run_instances(ImageId=image, MinCount=1, MaxCount=1, SubnetId=b)["Instances"][0]["InstanceId"]
    if tagged:
        for resource in (vpc, nat, eip, instance):
            tag(ec2, resource)
    return {"vpc": vpc, "nat": nat, "eip": eip, "instance": instance, "acl": acl}


def state(ec2):
    instances = {i["InstanceId"]: i["State"]["Name"] for r in ec2.describe_instances()["Reservations"] for i in r["Instances"]}
    return {"vpcs": {v["VpcId"] for v in ec2.describe_vpcs()["Vpcs"]},
            "eips": {a["AllocationId"] for a in ec2.describe_addresses()["Addresses"]},
            "nats": {n["NatGatewayId"] for n in ec2.describe_nat_gateways()["NatGateways"] if n["State"] == "available"},
            "running": {i for i, s in instances.items() if s != "terminated"}}


def test_dry_run_lists_tagged_only(aws, capsys):
    ec2 = aws.client("ec2")
    lab, mine = build(ec2, "10.60.0.0/16", True), build(ec2, "10.61.0.0/16", False)
    before = state(ec2)
    assert labclean.main(KINDS, ["--region", "us-east-1"], session_factory=lambda **kw: aws) == 0
    assert state(ec2) == before
    out = capsys.readouterr().out
    for resource in ("vpc", "nat", "eip", "instance"):
        assert lab[resource] in out and mine[resource] not in out


def test_deletes_tagged_vpc_and_its_contents_only(aws, capsys):
    ec2 = aws.client("ec2")
    lab, mine = build(ec2, "10.60.0.0/16", True), build(ec2, "10.61.0.0/16", False)
    assert labclean.main(KINDS, ["--region", "us-east-1", "--yes"], session_factory=lambda **kw: aws) == 0
    after = state(ec2)
    assert lab["vpc"] not in after["vpcs"] and mine["vpc"] in after["vpcs"]
    assert lab["eip"] not in after["eips"] and mine["eip"] in after["eips"]
    assert lab["nat"] not in after["nats"] and mine["nat"] in after["nats"]
    assert lab["instance"] not in after["running"] and mine["instance"] in after["running"]
    assert not ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [lab["vpc"]]}])["Subnets"]
    assert ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [mine["vpc"]]}])["Subnets"]
    assert "✔ deleted vpcs" in capsys.readouterr().out


def test_other_region_untouched(aws):
    east, west = aws.client("ec2", region_name="us-east-1"), aws.client("ec2", region_name="eu-west-1")
    vpc_west = west.create_vpc(CidrBlock="10.70.0.0/16")["Vpc"]["VpcId"]
    tag(west, vpc_west)
    labclean.main(KINDS, ["--region", "us-east-1", "--yes"], session_factory=lambda **kw: aws)
    assert vpc_west in {v["VpcId"] for v in west.describe_vpcs()["Vpcs"]}
    labclean.main(KINDS, ["--region", "eu-west-1", "--yes"], session_factory=lambda **kw: aws)
    assert vpc_west not in {v["VpcId"] for v in west.describe_vpcs()["Vpcs"]}
````

### `_dev/mutants/week02.py`

````python
"""Deliberately wrong implementations for week 02 — each must be caught by its drill."""
MUTANTS = [
    {"id": "forgets-reserved", "drill": 1, "code": '''
import ipaddress
from _harness.awslib.cidr import reserved_ips
def usable_ips(cidr):
    net = ipaddress.ip_network(cidr, strict=True)
    if net.version != 4 or not 16 <= net.prefixlen <= 28:
        raise ValueError(cidr)
    return net.num_addresses - 2
'''},
    {"id": "smallest-first", "drill": 2, "code": '''
import ipaddress
from _harness.awslib.cidr import prefix_for_hosts
def plan_subnets(vpc_cidr, tiers, azs):
    vpc = ipaddress.ip_network(vpc_cidr)
    order = sorted(tiers, key=lambda t: -prefix_for_hosts(tiers[t]))
    plan, cursor = {}, int(vpc.network_address)
    for tier in order:
        prefix = prefix_for_hosts(tiers[tier]); size = 2 ** (32 - prefix)
        for az in azs:
            cursor = -(-cursor // size) * size
            if cursor + size - 1 > int(vpc.broadcast_address):
                raise ValueError("no fit")
            plan[(tier, az)] = str(ipaddress.ip_network((cursor, prefix))); cursor += size
    return plan
'''},
    {"id": "first-match", "drill": 3, "code": '''
import ipaddress
def route_target(destination_ip, routes):
    for cidr, target in routes.items():
        if ipaddress.ip_address(destination_ip) in ipaddress.ip_network(cidr):
            return target
    return None
'''},
    {"id": "nacl-is-stateful", "drill": 4, "code": '''
from _harness.awslib.netsim import sg_allows, nacl_allows
def tcp_connection(client, server, port, client_port=49152):
    crosses = client.subnet != server.subnet
    checks = [("client security group (outbound)", sg_allows(client.sg_out, server.ip, server.sgs, "tcp", port))]
    if crosses:
        checks += [("client network ACL (outbound)", nacl_allows(client.nacl_out, server.ip, "tcp", port)),
                   ("server network ACL (inbound)", nacl_allows(server.nacl_in, client.ip, "tcp", port))]
    checks.append(("server security group (inbound)", sg_allows(server.sg_in, client.ip, client.sgs, "tcp", port)))
    for name, ok in checks:
        if not ok:
            return False, name
    return True, "allowed"
'''},
    {"id": "transitive-peering", "drill": 5, "code": '''
from _harness.awslib.netsim import can_peer, peerings_for_full_mesh
def can_reach(source, target, peerings, tgw_attachments=()):
    seen, frontier = {source}, [source]
    while frontier:
        here = frontier.pop()
        for a, b in peerings:
            for x, y in ((a, b), (b, a)):
                if x == here and y not in seen:
                    seen.add(y); frontier.append(y)
    attached = set(tgw_attachments)
    return target in seen or (source in attached and target in attached)
'''},
    {"id": "private-to-igw", "drill": 6, "code": '''
def build_vpc(ec2, cidr, plan):
    vpc = ec2.create_vpc(CidrBlock=cidr)["Vpc"]["VpcId"]
    ec2.modify_vpc_attribute(VpcId=vpc, EnableDnsSupport={"Value": True})
    ec2.modify_vpc_attribute(VpcId=vpc, EnableDnsHostnames={"Value": True})
    subnets = {k: ec2.create_subnet(VpcId=vpc, CidrBlock=b, AvailabilityZone=k[1])["Subnet"]["SubnetId"] for k, b in plan.items()}
    igw = ec2.create_internet_gateway()["InternetGateway"]["InternetGatewayId"]
    ec2.attach_internet_gateway(InternetGatewayId=igw, VpcId=vpc)
    tables = {}
    for (tier, az), subnet in subnets.items():
        key = "public" if tier == "public" else az
        if key not in tables:
            tables[key] = ec2.create_route_table(VpcId=vpc)["RouteTable"]["RouteTableId"]
            ec2.create_route(RouteTableId=tables[key], DestinationCidrBlock="0.0.0.0/0", GatewayId=igw)
        ec2.associate_route_table(RouteTableId=tables[key], SubnetId=subnet)
    return {"vpc": vpc, "igw": igw, "subnets": subnets, "route_tables": tables}
'''},
    {"id": "app-open-to-vpc", "drill": 7, "code": '''
def create_web_sgs(ec2, vpc_id):
    sgs = {r: ec2.create_security_group(GroupName=f"shortly-{r}", Description=r, VpcId=vpc_id)["GroupId"] for r in ("alb", "app", "db")}
    ec2.authorize_security_group_ingress(GroupId=sgs["alb"], IpPermissions=[{"IpProtocol": "tcp", "FromPort": 443, "ToPort": 443, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}])
    ec2.authorize_security_group_ingress(GroupId=sgs["app"], IpPermissions=[{"IpProtocol": "tcp", "FromPort": 8000, "ToPort": 8000, "IpRanges": [{"CidrIp": "10.40.0.0/16"}]}])
    ec2.authorize_security_group_ingress(GroupId=sgs["db"], IpPermissions=[{"IpProtocol": "tcp", "FromPort": 5432, "ToPort": 5432, "UserIdGroupPairs": [{"GroupId": sgs["app"]}]}])
    return sgs
'''},
    {"id": "objects-only", "drill": 8, "code": '''
import json
def add_s3_gateway_endpoint(ec2, vpc_id, route_table_ids, bucket):
    policy = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": "*",
              "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"], "Resource": [f"arn:aws:s3:::{bucket}", f"arn:aws:s3:::{bucket}/*"]}]}
    return ec2.create_vpc_endpoint(VpcEndpointType="Gateway", VpcId=vpc_id, RouteTableIds=list(route_table_ids),
                                   ServiceName=f"com.amazonaws.{ec2.meta.region_name}.s3", PolicyDocument=json.dumps(policy))["VpcEndpoint"]["VpcEndpointId"]
def vpce_only_bucket_policy(bucket, vpce_id):
    return {"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Principal": "*", "Action": "s3:*",
            "Resource": f"arn:aws:s3:::{bucket}/*", "Condition": {"StringNotEquals": {"aws:SourceVpce": vpce_id}}}]}
'''},
    {"id": "forgets-hourly", "drill": 9, "code": '''
def nat_monthly_cost(gb, nat_gateways, hours=730, price=PRICES):
    if min(gb, nat_gateways, hours) < 0:
        raise ValueError("negative")
    return round(gb * price["nat_gateway_per_gb"], 2)
'''},
    {"id": "endpoint-reaches-internet", "drill": 10, "code": '''
PREDICTIONS = {1: "no", 2: "yes", 3: "yes", 4: "yes", 5: "no", 6: "no"}
'''},
]
````

### `_dev/mutants/m02.py`

````python
"""Wrong versions of the M02 snapshot — exact text edits applied to a copy of course_project/solutions/m02."""
NET = "infra/network.yaml"
MUTANTS = [
    {"id": "second-nat-in-lab", "edits": {NET: [["  NatGatewayB:\n    Type: AWS::EC2::NatGateway\n    Condition: IsProd\n",
                                                 "  NatGatewayB:\n    Type: AWS::EC2::NatGateway\n"]]}},
    {"id": "data-tier-to-nat", "edits": {NET: [["  PublicSubnetARoutes:", "  DataDefaultRoute:\n    Type: AWS::EC2::Route\n    Properties:\n"
                                                "      RouteTableId: !Ref DataRouteTable\n      DestinationCidrBlock: 0.0.0.0/0\n"
                                                "      NatGatewayId: !Ref NatGatewayA\n\n  PublicSubnetARoutes:"]]}},
    {"id": "app-open-to-vpc", "edits": {NET: [["SourceSecurityGroupId: !Ref AlbSecurityGroup}", "CidrIp: 10.20.0.0/16}"]]}},
    {"id": "ssh-from-anywhere", "edits": {NET: [["        - {IpProtocol: tcp, FromPort: 8000, ToPort: 8000, SourceSecurityGroupId: !Ref AlbSecurityGroup}",
                                                 "        - {IpProtocol: tcp, FromPort: 8000, ToPort: 8000, SourceSecurityGroupId: !Ref AlbSecurityGroup}\n"
                                                 "        - {IpProtocol: tcp, FromPort: 22, ToPort: 22, CidrIp: 0.0.0.0/0}"]]}},
    {"id": "s3-endpoint-misses-data", "edits": {NET: [["RouteTableIds: [!Ref AppRouteTableA, !Ref AppRouteTableB, !Ref DataRouteTable]\n      PolicyDocument",
                                                       "RouteTableIds: [!Ref AppRouteTableA, !Ref AppRouteTableB]\n      PolicyDocument"]]}},
    {"id": "endpoint-any-account", "edits": {NET: [["            Condition:\n              StringEquals: {'aws:ResourceAccount': !Ref 'AWS::AccountId'}\n", ""]]}},
    {"id": "logs-kept-forever", "edits": {NET: [["      RetentionInDays: 30\n", ""]]}},
    {"id": "flow-role-any-group", "edits": {NET: [["log-group:/${Prefix}/vpc-flow-logs:*'", "log-group:*'"]]}},
    {"id": "overlapping-subnets", "edits": {NET: [["CidrBlock: !Select [10, !Cidr [!Ref VpcCidr, 12, 8]]", "CidrBlock: !Select [9, !Cidr [!Ref VpcCidr, 12, 8]]"]]}},
    {"id": "plan-not-documented", "edits": {"README.md": [["## Network plan", "## Network"]]}},
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
from _course import cidr as _cidr, netsim as _netsim  # noqa: E402

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


@pytest.fixture
def moto_stacks():
    """deploy(layer, **params) creates the stack in a fake AWS (moto) and returns its status.
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
    _harness/awslib/*.py                   → <repo>/tests/_course/   (template + policy helpers the tests use)
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
HELPERS = ("__init__.py", "safety.py", "cfn.py", "policy_eval.py", "cidr.py", "netsim.py")


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

    print(f"Copied tests/{source.name}/, tests/conftest.py, tests/_course/ and run_milestone.py into {repo}")
    print(f"Instructions:  {COURSE_PROJECT / 'milestones' / f'M{n:02d}.md'}")
    print(f"Progress:      cd \"{repo}\"   then   python run_milestone.py {n}")
    print("Use the course venv's python (it has moto and cfn-lint).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
````

### `course_project/tests/m02/test_m02_1_vpc_and_subnets.py`

````python
"""M02.1 — the VPC and six subnets: three tiers in two Availability Zones, planned and documented."""
import ipaddress

SUBNETS = {"PublicSubnetA": ("public", 0), "PublicSubnetB": ("public", 1), "AppSubnetA": ("app", 0),
           "AppSubnetB": ("app", 1), "DataSubnetA": ("data", 0), "DataSubnetB": ("data", 1)}
MIN_HOSTS = {"public": 250, "app": 1000, "data": 250}


def test_parameters(template):
    params = template("network").get("Parameters", {})
    assert params.get("VpcCidr", {}).get("Default") == "10.20.0.0/16", "Parameter VpcCidr (String, Default 10.20.0.0/16)"
    for name in ("Prefix", "Env"):
        assert name in params, f"the network stack also takes the {name} parameter"


def test_vpc(resources):
    vpc = resources("network").get("Vpc")
    assert vpc and vpc["Type"] == "AWS::EC2::VPC", "add a resource Vpc (AWS::EC2::VPC)"
    props = vpc["Properties"]
    assert props.get("CidrBlock") == "10.20.0.0/16", "CidrBlock: !Ref VpcCidr"
    assert props.get("EnableDnsSupport") is True and props.get("EnableDnsHostnames") is True, \
        "turn on EnableDnsSupport and EnableDnsHostnames (VPC endpoints and RDS need DNS)"


def test_six_subnets_in_two_azs(resources):
    res = resources("network")
    for name, (_, az) in SUBNETS.items():
        subnet = res.get(name)
        assert subnet and subnet["Type"] == "AWS::EC2::Subnet", f"add {name} (AWS::EC2::Subnet)"
        assert subnet["Properties"].get("VpcId") == "Vpc", f"{name}: VpcId: !Ref Vpc"
        assert subnet["Properties"].get("AvailabilityZone") == f"us-east-1{'ab'[az]}", \
            f"{name}: AvailabilityZone: !Select [{az}, !GetAZs ''] (A = first AZ, B = second)"


def test_subnet_sizes_fit_and_never_overlap(resources, cidr):
    res = resources("network")
    blocks = {name: res[name]["Properties"]["CidrBlock"] for name in SUBNETS}
    for name, block in blocks.items():
        tier = SUBNETS[name][0]
        assert ipaddress.ip_network(block).subnet_of(ipaddress.ip_network("10.20.0.0/16")), f"{name} ({block}) must be inside the VPC"
        assert cidr.usable_ips(block) >= MIN_HOSTS[tier], f"{name} ({block}) needs at least {MIN_HOSTS[tier]} usable addresses"
    names = list(blocks)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            assert not cidr.overlaps(blocks[a], blocks[b]), f"{a} ({blocks[a]}) overlaps {b} ({blocks[b]})"


def test_private_subnets_never_hand_out_public_ips(resources):
    res = resources("network")
    for name in ("AppSubnetA", "AppSubnetB", "DataSubnetA", "DataSubnetB"):
        assert res[name]["Properties"].get("MapPublicIpOnLaunch") is not True, f"{name} must not give instances public IPs"


def test_readme_documents_the_plan(repo, resources):
    text = (repo / "README.md").read_text(encoding="utf-8")
    assert "## Network plan" in text, "add a '## Network plan' section to README.md"
    res = resources("network")
    for name in SUBNETS:
        block = res[name]["Properties"]["CidrBlock"]
        assert block in text, f"README's network plan should list {name}: {block}"
````

### `course_project/tests/m02/test_m02_2_routing.py`

````python
"""M02.2 — internet gateway, NAT gateways and route tables. prod: one NAT per AZ; lab: one NAT."""
import pytest

ROUTE_TABLES = {"PublicSubnetA": "PublicRouteTable", "PublicSubnetB": "PublicRouteTable",
                "AppSubnetA": "AppRouteTableA", "AppSubnetB": "AppRouteTableB",
                "DataSubnetA": "DataRouteTable", "DataSubnetB": "DataRouteTable"}


def of_type(res, type_):
    return {name: r for name, r in res.items() if r["Type"] == type_}


def default_routes(res, table):
    return [r["Properties"] for r in of_type(res, "AWS::EC2::Route").values()
            if r["Properties"].get("RouteTableId") == table and r["Properties"].get("DestinationCidrBlock") == "0.0.0.0/0"]


def test_internet_gateway_attached(resources):
    res = resources("network")
    assert res.get("InternetGateway", {}).get("Type") == "AWS::EC2::InternetGateway", "add InternetGateway"
    attachments = [a["Properties"] for a in of_type(res, "AWS::EC2::VPCGatewayAttachment").values()]
    assert {"VpcId": "Vpc", "InternetGatewayId": "InternetGateway"} in [
        {k: a.get(k) for k in ("VpcId", "InternetGatewayId")} for a in attachments], "attach InternetGateway to Vpc"


@pytest.mark.parametrize("env, nats", [("prod", {"NatGatewayA", "NatGatewayB"}), ("lab", {"NatGatewayA"})])
def test_nat_gateways_per_environment(resources, env, nats):
    res = resources("network", Env=env)
    assert set(of_type(res, "AWS::EC2::NatGateway")) == nats, \
        f"Env={env} should create {sorted(nats)} (NatGatewayB only when Env is prod: Condition IsProd)"
    assert res["NatGatewayA"]["Properties"].get("SubnetId") == "PublicSubnetA", "NAT gateways live in public subnets"
    if env == "prod":
        assert res["NatGatewayB"]["Properties"].get("SubnetId") == "PublicSubnetB"
    for nat in of_type(res, "AWS::EC2::NatGateway").values():
        assert str(nat["Properties"].get("AllocationId", "")).endswith(".AllocationId"), \
            "give each NAT gateway an Elastic IP: AllocationId: !GetAtt NatEipA.AllocationId"


def test_subnet_associations(resources):
    res = resources("network")
    pairs = {a["Properties"].get("SubnetId"): a["Properties"].get("RouteTableId")
             for a in of_type(res, "AWS::EC2::SubnetRouteTableAssociation").values()}
    for subnet, table in ROUTE_TABLES.items():
        assert pairs.get(subnet) == table, f"associate {subnet} with {table}"
    for table in set(ROUTE_TABLES.values()):
        assert res.get(table, {}).get("Type") == "AWS::EC2::RouteTable", f"add {table} (AWS::EC2::RouteTable)"


def test_public_routes_to_the_internet_gateway(resources):
    routes = default_routes(resources("network"), "PublicRouteTable")
    assert [r.get("GatewayId") for r in routes] == ["InternetGateway"], "PublicRouteTable: 0.0.0.0/0 → InternetGateway"


@pytest.mark.parametrize("env, b_target", [("prod", "NatGatewayB"), ("lab", "NatGatewayA")])
def test_app_routes_to_nat(resources, env, b_target):
    res = resources("network", Env=env)
    assert [r.get("NatGatewayId") for r in default_routes(res, "AppRouteTableA")] == ["NatGatewayA"]
    assert [r.get("NatGatewayId") for r in default_routes(res, "AppRouteTableB")] == [b_target], \
        f"Env={env}: AppRouteTableB's default route goes to {b_target} (!If [IsProd, …, …])"


def test_data_tier_has_no_way_out(resources):
    res = resources("network")
    routes = [r["Properties"] for r in of_type(res, "AWS::EC2::Route").values() if r["Properties"].get("RouteTableId") == "DataRouteTable"]
    assert not routes, "DataRouteTable gets no routes besides the local one (no internet, no NAT)"
````

### `course_project/tests/m02/test_m02_3_security_groups.py`

````python
"""M02.3 — security groups chained by reference: internet → ALB → app → database / cache."""
GROUPS = ("AlbSecurityGroup", "AppSecurityGroup", "DbSecurityGroup", "CacheSecurityGroup")


def ingress_rules(res):
    """Every inbound rule, inline or as a separate AWS::EC2::SecurityGroupIngress, as
    {group: [{"protocol", "ports", "peer"}]} in the course's netsim rule format."""
    rules = {g: [] for g in GROUPS}

    def add(group, rule):
        peer = rule.get("SourceSecurityGroupId") or rule.get("CidrIp") or rule.get("CidrIpv6") or rule.get("SourcePrefixListId")
        protocol = str(rule.get("IpProtocol"))
        ports = (int(rule.get("FromPort", 0)), int(rule.get("ToPort", 65535))) if protocol != "-1" else (0, 65535)
        rules.setdefault(group, []).append({"protocol": protocol, "ports": ports, "peer": f"sg-{peer}" if peer in GROUPS else peer})

    for name, r in res.items():
        if r["Type"] == "AWS::EC2::SecurityGroup":
            for rule in r["Properties"].get("SecurityGroupIngress", []):
                add(name, rule)
        if r["Type"] == "AWS::EC2::SecurityGroupIngress":
            add(r["Properties"].get("GroupId"), r["Properties"])
    return rules


def test_groups_exist_in_the_vpc(resources):
    res = resources("network")
    for group in GROUPS:
        assert res.get(group, {}).get("Type") == "AWS::EC2::SecurityGroup", f"add {group} (AWS::EC2::SecurityGroup)"
        assert res[group]["Properties"].get("VpcId") == "Vpc", f"{group}: VpcId: !Ref Vpc"


def test_exact_inbound_rules(resources):
    rules = ingress_rules(resources("network"))
    alb = sorted((r["protocol"], r["ports"], r["peer"]) for r in rules["AlbSecurityGroup"])
    assert ("tcp", (443, 443), "0.0.0.0/0") in alb, "the ALB accepts HTTPS (443) from anywhere"
    assert all(r[2] == "0.0.0.0/0" and r[1] in ((443, 443), (80, 80)) for r in alb), "the ALB accepts only 80 and 443"
    expected = {"AppSecurityGroup": [("tcp", (8000, 8000), "sg-AlbSecurityGroup")],
                "DbSecurityGroup": [("tcp", (5432, 5432), "sg-AppSecurityGroup")],
                "CacheSecurityGroup": [("tcp", (6379, 6379), "sg-AppSecurityGroup")]}
    for group, want in expected.items():
        got = [(r["protocol"], r["ports"], r["peer"]) for r in rules[group]]
        assert got == want, f"{group} inbound must be exactly {want}, found {got}"


def test_paths_with_the_course_model(resources, netsim):
    rules = ingress_rules(resources("network"))
    host = lambda ip, group: netsim.Host(ip=ip, subnet=group, sgs=(f"sg-{group}",), sg_in=tuple(rules[group]))
    internet = netsim.Host(ip="203.0.113.50", subnet="internet")
    alb, app = host("10.20.0.10", "AlbSecurityGroup"), host("10.20.4.10", "AppSecurityGroup")
    db, cache = host("10.20.12.10", "DbSecurityGroup"), host("10.20.13.10", "CacheSecurityGroup")
    assert netsim.tcp_connection(internet, alb, 443)[0]
    assert netsim.tcp_connection(alb, app, 8000)[0]
    assert netsim.tcp_connection(app, db, 5432)[0] and netsim.tcp_connection(app, cache, 6379)[0]
    for client, server, port in ((internet, app, 8000), (internet, db, 5432), (alb, db, 5432), (internet, app, 22)):
        assert not netsim.tcp_connection(client, server, port)[0], f"{client.ip} must not reach {server.subnet} on {port}"
````

### `course_project/tests/m02/test_m02_4_endpoints.py`

````python
"""M02.4 — gateway endpoints for S3 and DynamoDB, so private subnets reach them without NAT."""
import pytest

PRIVATE_TABLES = {"AppRouteTableA", "AppRouteTableB", "DataRouteTable"}


@pytest.mark.parametrize("name, service", [("S3Endpoint", "s3"), ("DynamoDbEndpoint", "dynamodb")])
def test_gateway_endpoint(resources, name, service):
    endpoint = resources("network").get(name)
    assert endpoint and endpoint["Type"] == "AWS::EC2::VPCEndpoint", f"add {name} (AWS::EC2::VPCEndpoint)"
    props = endpoint["Properties"]
    assert props.get("VpcEndpointType", "Gateway") == "Gateway", f"{name} is a Gateway endpoint (free; Interface ones cost money)"
    assert props.get("ServiceName") == f"com.amazonaws.us-east-1.{service}", \
        f"{name}: ServiceName: !Sub 'com.amazonaws.${{AWS::Region}}.{service}'"
    assert props.get("VpcId") == "Vpc"
    assert PRIVATE_TABLES <= set(props.get("RouteTableIds", [])), f"{name} must be on {sorted(PRIVATE_TABLES)}"


def test_s3_endpoint_policy_stays_in_this_account(resources, evaluator):
    props = resources("network")["S3Endpoint"]["Properties"]
    policy = props.get("PolicyDocument")
    assert policy, "give S3Endpoint a PolicyDocument (an endpoint policy)"
    mine = "arn:aws:s3:::shortly-assets-111122223333/uploads/a.png"
    caller = "arn:aws:sts::111122223333:assumed-role/shortly-app/i-1"

    def decide(arn, **context):
        return evaluator.evaluate(evaluator.Request(caller, "s3:GetObject", arn, {"aws:ResourceAccount": "111122223333", **context}),
                                  identity=[], resource_policy=policy, resource_account="111122223333")
    assert decide(mine) == "Allow", "the endpoint must let the app reach this account's buckets"
    other = evaluator.Request(caller, "s3:GetObject", "arn:aws:s3:::attacker-bucket/x", {"aws:ResourceAccount": "444455556666"})
    assert evaluator.evaluate(other, identity=[], resource_policy=policy, resource_account="111122223333") != "Allow", \
        "the endpoint must not reach buckets owned by other accounts (condition on aws:ResourceAccount)"
````

### `course_project/tests/m02/test_m02_5_flow_logs.py`

````python
"""M02.5 — VPC flow logs to CloudWatch Logs, with a role that may write only to that log group."""
ACCOUNT = "111122223333"


def test_log_group_with_retention(resources):
    group = resources("network").get("FlowLogsLogGroup")
    assert group and group["Type"] == "AWS::Logs::LogGroup", "add FlowLogsLogGroup (AWS::Logs::LogGroup)"
    days = group["Properties"].get("RetentionInDays")
    assert isinstance(days, int) and 1 <= days <= 90, "set RetentionInDays (1–90): logs kept forever cost money forever"


def test_flow_log(resources):
    flow = resources("network").get("VpcFlowLog")
    assert flow and flow["Type"] == "AWS::EC2::FlowLog", "add VpcFlowLog (AWS::EC2::FlowLog)"
    props = flow["Properties"]
    assert (props.get("ResourceId"), props.get("ResourceType")) == ("Vpc", "VPC"), "log the whole VPC"
    assert props.get("TrafficType") in ("ALL", "REJECT"), "TrafficType ALL (or REJECT to keep costs down)"
    assert props.get("LogDestinationType", "cloud-watch-logs") == "cloud-watch-logs"
    assert props.get("LogGroupName") == "FlowLogsLogGroup", "LogGroupName: !Ref FlowLogsLogGroup"
    assert props.get("DeliverLogsPermissionArn") == "FlowLogsRole.Arn", "DeliverLogsPermissionArn: !GetAtt FlowLogsRole.Arn"


def test_role_trusts_the_flow_logs_service(trust_policy, evaluator):
    trust = trust_policy("network", "FlowLogsRole")
    assert evaluator.evaluate_trust(trust, "vpc-flow-logs.amazonaws.com")
    assert not evaluator.evaluate_trust(trust, "ec2.amazonaws.com")


def test_role_writes_only_its_log_group(role_policies, evaluator, resources):
    policies = role_policies("network", "FlowLogsRole")
    role = f"arn:aws:sts::{ACCOUNT}:assumed-role/shortly-flow-logs/x"
    group_name = resources("network")["FlowLogsLogGroup"]["Properties"].get("LogGroupName", "")
    assert group_name.startswith("/shortly/"), "LogGroupName: !Sub '/${Prefix}/vpc-flow-logs'"
    mine = f"arn:aws:logs:us-east-1:{ACCOUNT}:log-group:{group_name}:log-stream:eni-1"
    other = f"arn:aws:logs:us-east-1:{ACCOUNT}:log-group:/other/app:log-stream:x"
    for action in ("logs:CreateLogStream", "logs:PutLogEvents"):
        assert evaluator.evaluate_policies(policies, evaluator.Request(role, action, mine)) == "Allow", f"FlowLogsRole needs {action} on its group"
        assert evaluator.evaluate_policies(policies, evaluator.Request(role, action, other)) != "Allow", f"{action} only on its own group"
````

### `course_project/tests/m02/test_m02_6_exports_and_deploy.py`

````python
"""M02.6 — exports for later stacks, lint-clean, and a deploy in moto for both environments."""
import pytest

EXPORTS = {"VpcId": ("shortly-vpc-id", "Vpc"),
           "PublicSubnetIds": ("shortly-public-subnet-ids", "PublicSubnetA,PublicSubnetB"),
           "AppSubnetIds": ("shortly-app-subnet-ids", "AppSubnetA,AppSubnetB"),
           "DataSubnetIds": ("shortly-data-subnet-ids", "DataSubnetA,DataSubnetB"),
           "AlbSecurityGroupId": ("shortly-alb-sg-id", "AlbSecurityGroup"),
           "AppSecurityGroupId": ("shortly-app-sg-id", "AppSecurityGroup"),
           "DbSecurityGroupId": ("shortly-db-sg-id", "DbSecurityGroup"),
           "CacheSecurityGroupId": ("shortly-cache-sg-id", "CacheSecurityGroup")}


def test_exports(outputs):
    out = outputs("network")
    for key, (export, value) in EXPORTS.items():
        assert key in out, f"add Output {key}"
        assert out[key].get("Export", {}).get("Name") == export, f"{key}: Export Name !Sub '${{Prefix}}-{export[8:]}'"
        assert str(out[key].get("Value")).replace(".GroupId", "") == value, f"{key}: Value should be {value}"


def test_lint_clean(lint_errors):
    errors = lint_errors("network")
    assert errors == [], "cfn-lint errors: " + "; ".join(f"line {e['line']} {e['rule']} {e['message']}" for e in errors)


@pytest.mark.parametrize("env, nats", [("prod", 2), ("lab", 1)])
def test_deploys_in_moto(moto_stacks, env, nats):
    import boto3

    assert moto_stacks("network", Env=env) == "CREATE_COMPLETE"
    ec2 = boto3.client("ec2", region_name="us-east-1")
    vpcs = [v for v in ec2.describe_vpcs()["Vpcs"] if v["CidrBlock"] == "10.20.0.0/16"]
    assert len(vpcs) == 1
    vpc = vpcs[0]["VpcId"]
    in_vpc = [{"Name": "vpc-id", "Values": [vpc]}]
    assert len(ec2.describe_subnets(Filters=in_vpc)["Subnets"]) == 6
    live = [n for n in ec2.describe_nat_gateways(Filters=in_vpc)["NatGateways"] if n["State"] == "available"]
    assert len(live) == nats, f"Env={env}: expected {nats} NAT gateway(s)"
    endpoints = ec2.describe_vpc_endpoints(Filters=in_vpc)["VpcEndpoints"]
    assert {e["ServiceName"].rsplit(".", 1)[-1] for e in endpoints} == {"s3", "dynamodb"}
````

### `course_project/solutions/m02/infra/network.yaml`

````yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: shortly-infra M02 - network (VPC, three tiers in two AZs, NAT, security groups, endpoints, flow logs)

Parameters:
  Prefix:
    Type: String
    Default: shortly
    AllowedPattern: '[a-z][a-z0-9-]{1,20}'
  Env:
    Type: String
    AllowedValues: [lab, prod]
  VpcCidr:
    Type: String
    Default: 10.20.0.0/16

Conditions:
  IsProd: !Equals [!Ref Env, prod]

Resources:
  Vpc:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: !Ref VpcCidr
      EnableDnsSupport: true
      EnableDnsHostnames: true
      Tags:
        - {Key: Name, Value: !Sub '${Prefix}-vpc'}
        - {Key: project, Value: !Ref Prefix}
        - {Key: env, Value: !Ref Env}

  # ── subnets: app /22s first (biggest), then public and data /24s ─────
  AppSubnetA:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref Vpc
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: !Select [0, !Cidr [!Ref VpcCidr, 2, 10]]
      Tags: [{Key: Name, Value: !Sub '${Prefix}-app-a'}]
  AppSubnetB:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref Vpc
      AvailabilityZone: !Select [1, !GetAZs '']
      CidrBlock: !Select [1, !Cidr [!Ref VpcCidr, 2, 10]]
      Tags: [{Key: Name, Value: !Sub '${Prefix}-app-b'}]
  PublicSubnetA:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref Vpc
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: !Select [8, !Cidr [!Ref VpcCidr, 12, 8]]
      Tags: [{Key: Name, Value: !Sub '${Prefix}-public-a'}]
  PublicSubnetB:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref Vpc
      AvailabilityZone: !Select [1, !GetAZs '']
      CidrBlock: !Select [9, !Cidr [!Ref VpcCidr, 12, 8]]
      Tags: [{Key: Name, Value: !Sub '${Prefix}-public-b'}]
  DataSubnetA:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref Vpc
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: !Select [10, !Cidr [!Ref VpcCidr, 12, 8]]
      Tags: [{Key: Name, Value: !Sub '${Prefix}-data-a'}]
  DataSubnetB:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref Vpc
      AvailabilityZone: !Select [1, !GetAZs '']
      CidrBlock: !Select [11, !Cidr [!Ref VpcCidr, 12, 8]]
      Tags: [{Key: Name, Value: !Sub '${Prefix}-data-b'}]

  # ── internet access ─────────────────────────────────────────────────
  InternetGateway:
    Type: AWS::EC2::InternetGateway
    Properties:
      Tags: [{Key: Name, Value: !Sub '${Prefix}-igw'}]
  GatewayAttachment:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref Vpc
      InternetGatewayId: !Ref InternetGateway

  NatEipA:
    Type: AWS::EC2::EIP
    DependsOn: GatewayAttachment
    Properties:
      Domain: vpc
  NatGatewayA:
    Type: AWS::EC2::NatGateway
    Properties:
      SubnetId: !Ref PublicSubnetA
      AllocationId: !GetAtt NatEipA.AllocationId
      Tags: [{Key: Name, Value: !Sub '${Prefix}-nat-a'}]
  NatEipB:
    Type: AWS::EC2::EIP
    Condition: IsProd
    DependsOn: GatewayAttachment
    Properties:
      Domain: vpc
  NatGatewayB:
    Type: AWS::EC2::NatGateway
    Condition: IsProd
    Properties:
      SubnetId: !Ref PublicSubnetB
      AllocationId: !GetAtt NatEipB.AllocationId
      Tags: [{Key: Name, Value: !Sub '${Prefix}-nat-b'}]

  # ── route tables ────────────────────────────────────────────────────
  PublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref Vpc
      Tags: [{Key: Name, Value: !Sub '${Prefix}-public'}]
  PublicDefaultRoute:
    Type: AWS::EC2::Route
    DependsOn: GatewayAttachment
    Properties:
      RouteTableId: !Ref PublicRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway
  AppRouteTableA:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref Vpc
      Tags: [{Key: Name, Value: !Sub '${Prefix}-app-a'}]
  AppDefaultRouteA:
    Type: AWS::EC2::Route
    Properties:
      RouteTableId: !Ref AppRouteTableA
      DestinationCidrBlock: 0.0.0.0/0
      NatGatewayId: !Ref NatGatewayA
  AppRouteTableB:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref Vpc
      Tags: [{Key: Name, Value: !Sub '${Prefix}-app-b'}]
  AppDefaultRouteB:
    Type: AWS::EC2::Route
    Properties:
      RouteTableId: !Ref AppRouteTableB
      DestinationCidrBlock: 0.0.0.0/0
      NatGatewayId: !If [IsProd, !Ref NatGatewayB, !Ref NatGatewayA]   # lab: one NAT to save money
  DataRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref Vpc
      Tags: [{Key: Name, Value: !Sub '${Prefix}-data'}]

  PublicSubnetARoutes:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties: {SubnetId: !Ref PublicSubnetA, RouteTableId: !Ref PublicRouteTable}
  PublicSubnetBRoutes:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties: {SubnetId: !Ref PublicSubnetB, RouteTableId: !Ref PublicRouteTable}
  AppSubnetARoutes:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties: {SubnetId: !Ref AppSubnetA, RouteTableId: !Ref AppRouteTableA}
  AppSubnetBRoutes:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties: {SubnetId: !Ref AppSubnetB, RouteTableId: !Ref AppRouteTableB}
  DataSubnetARoutes:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties: {SubnetId: !Ref DataSubnetA, RouteTableId: !Ref DataRouteTable}
  DataSubnetBRoutes:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties: {SubnetId: !Ref DataSubnetB, RouteTableId: !Ref DataRouteTable}

  # ── security groups: internet → ALB → app → database / cache ────────
  AlbSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Load balancer - HTTPS from anywhere
      VpcId: !Ref Vpc
      SecurityGroupIngress:
        - {IpProtocol: tcp, FromPort: 443, ToPort: 443, CidrIp: 0.0.0.0/0}
        - {IpProtocol: tcp, FromPort: 80, ToPort: 80, CidrIp: 0.0.0.0/0}
  AppSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: App servers - only from the load balancer
      VpcId: !Ref Vpc
      SecurityGroupIngress:
        - {IpProtocol: tcp, FromPort: 8000, ToPort: 8000, SourceSecurityGroupId: !Ref AlbSecurityGroup}
  DbSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: PostgreSQL - only from the app servers
      VpcId: !Ref Vpc
      SecurityGroupIngress:
        - {IpProtocol: tcp, FromPort: 5432, ToPort: 5432, SourceSecurityGroupId: !Ref AppSecurityGroup}
  CacheSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Redis - only from the app servers
      VpcId: !Ref Vpc
      SecurityGroupIngress:
        - {IpProtocol: tcp, FromPort: 6379, ToPort: 6379, SourceSecurityGroupId: !Ref AppSecurityGroup}

  # ── gateway endpoints: S3 and DynamoDB without NAT, free ────────────
  S3Endpoint:
    Type: AWS::EC2::VPCEndpoint
    Properties:
      VpcEndpointType: Gateway
      VpcId: !Ref Vpc
      ServiceName: !Sub 'com.amazonaws.${AWS::Region}.s3'
      RouteTableIds: [!Ref AppRouteTableA, !Ref AppRouteTableB, !Ref DataRouteTable]
      PolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Sid: OnlyThisAccountsBuckets
            Effect: Allow
            Principal: '*'
            Action: 's3:*'
            Resource: '*'
            Condition:
              StringEquals: {'aws:ResourceAccount': !Ref 'AWS::AccountId'}
  DynamoDbEndpoint:
    Type: AWS::EC2::VPCEndpoint
    Properties:
      VpcEndpointType: Gateway
      VpcId: !Ref Vpc
      ServiceName: !Sub 'com.amazonaws.${AWS::Region}.dynamodb'
      RouteTableIds: [!Ref AppRouteTableA, !Ref AppRouteTableB, !Ref DataRouteTable]

  # ── flow logs ───────────────────────────────────────────────────────
  FlowLogsLogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub '/${Prefix}/vpc-flow-logs'
      RetentionInDays: 30
  FlowLogsRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub '${Prefix}-flow-logs'
      Tags:
        - {Key: project, Value: !Ref Prefix}
        - {Key: env, Value: !Ref Env}
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal: {Service: vpc-flow-logs.amazonaws.com}
            Action: sts:AssumeRole
      Policies:
        - PolicyName: write-flow-logs
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action: [logs:CreateLogStream, logs:PutLogEvents, logs:DescribeLogStreams]
                Resource: !Sub 'arn:${AWS::Partition}:logs:${AWS::Region}:${AWS::AccountId}:log-group:/${Prefix}/vpc-flow-logs:*'
  VpcFlowLog:
    Type: AWS::EC2::FlowLog
    Properties:
      ResourceId: !Ref Vpc
      ResourceType: VPC
      TrafficType: ALL
      LogDestinationType: cloud-watch-logs
      LogGroupName: !Ref FlowLogsLogGroup
      DeliverLogsPermissionArn: !GetAtt FlowLogsRole.Arn

Outputs:
  VpcId:
    Value: !Ref Vpc
    Export: {Name: !Sub '${Prefix}-vpc-id'}
  PublicSubnetIds:
    Value: !Join [',', [!Ref PublicSubnetA, !Ref PublicSubnetB]]
    Export: {Name: !Sub '${Prefix}-public-subnet-ids'}
  AppSubnetIds:
    Value: !Join [',', [!Ref AppSubnetA, !Ref AppSubnetB]]
    Export: {Name: !Sub '${Prefix}-app-subnet-ids'}
  DataSubnetIds:
    Value: !Join [',', [!Ref DataSubnetA, !Ref DataSubnetB]]
    Export: {Name: !Sub '${Prefix}-data-subnet-ids'}
  AlbSecurityGroupId:
    Value: !GetAtt AlbSecurityGroup.GroupId
    Export: {Name: !Sub '${Prefix}-alb-sg-id'}
  AppSecurityGroupId:
    Value: !GetAtt AppSecurityGroup.GroupId
    Export: {Name: !Sub '${Prefix}-app-sg-id'}
  DbSecurityGroupId:
    Value: !GetAtt DbSecurityGroup.GroupId
    Export: {Name: !Sub '${Prefix}-db-sg-id'}
  CacheSecurityGroupId:
    Value: !GetAtt CacheSecurityGroup.GroupId
    Export: {Name: !Sub '${Prefix}-cache-sg-id'}
````

### `course_project/solutions/m02/README.md`

````markdown
# shortly-infra

The infrastructure-as-code for Shortly, the URL shortener you build up across the course. Each milestone adds one layer of CloudFormation templates, with parameter files for the lab and prod environments.

## Layers

| Layer | What it holds | Milestone |
|-------|---------------|-----------|
| `iam` | Roles for the app, the click consumer, the deployer and the auditor | M01 |
| `network` | VPC, three subnet tiers in two AZs, NAT, security groups, S3/DynamoDB endpoints, flow logs | M02 |

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

## Check it

Run the milestone tests with the course venv:

```
python run_milestone.py 2
```

## Deploy (optional)

Deploying to a real account is optional; see the course's `DEPLOY.md`. The network stack costs money while it runs (NAT gateways and their public IPv4 addresses are billed by the hour).
````

### `week_02_vpc_networking/practice/exercises.py`

````python
"""
Week 02 drills — VPC networking
===============================
Run:    python practice/exercises.py          every drill
        python practice/exercises.py 4        drill 4 only
Drills 01–05 are pure Python models of how a VPC works: address maths, routing, security groups
vs network ACLs, and how VPCs connect. Drills 06–10 build the real thing with boto3 against moto
(a fake AWS) — nothing here can touch a real account or cost money.
The course's own versions of drills 01–05 (_harness/awslib/cidr.py and netsim.py) are their answer
key — don't open them until you are done.
"""
import ipaddress  # noqa: F401  (you will want it)
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.awsdrill import Drill, run  # noqa: E402
from _harness.awslib import policy_eval as ref_policy  # noqa: E402
from _harness.awslib import prices  # noqa: E402
from _harness.awslib.netsim import ANY_OUT, NACL_ALLOW_ALL, Host  # noqa: E402,F401


# ── Exercise 01 ★: How many addresses can you use? ───────────────────
"""
usable_ips(cidr) -> int
    AWS reserves 5 addresses in every subnet, so a subnet holds (block size − 5) usable addresses.
    Accept only IPv4 network blocks from /16 to /28 (the sizes AWS allows for VPCs and subnets);
    anything else — /29, /15, "10.0.0.1/24" (host bits set), garbage text, IPv6 — → ValueError.
reserved_ips(cidr) -> list[str]
    The 5 reserved addresses in order: network address, +1 (VPC router), +2 (Amazon DNS),
    +3 (reserved for future use), and the last address (broadcast — AWS does not support it).
Examples:
    usable_ips("10.0.1.0/24") == 251      usable_ips("10.0.0.0/28") == 11
    reserved_ips("10.0.1.0/24") == ["10.0.1.0", "10.0.1.1", "10.0.1.2", "10.0.1.3", "10.0.1.255"]
Hint: ipaddress.ip_network(cidr, strict=True) raises ValueError for host bits; .num_addresses,
      .prefixlen, .version and .broadcast_address do the rest.
"""
def usable_ips(cidr):
    raise NotImplementedError  # YOUR CODE


def reserved_ips(cidr):
    raise NotImplementedError  # YOUR CODE


class Ex01(Drill):
    """How many addresses can you use? ★"""
    tasks = ("3.4",)

    def test_usable(self):
        for block, want in {"10.0.1.0/24": 251, "10.0.0.0/28": 11, "172.16.0.0/16": 65531, "10.8.0.0/21": 2043}.items():
            with self.subTest(block=block):
                self.assertEqual(usable_ips(block), want)

    def test_rejects_what_aws_rejects(self):
        for bad in ("10.0.0.0/29", "10.0.0.0/15", "10.0.0.1/24", "ten-dot-zero", "2001:db8::/64"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    usable_ips(bad)

    def test_reserved(self):
        self.assertEqual(reserved_ips("10.0.1.0/24"), ["10.0.1.0", "10.0.1.1", "10.0.1.2", "10.0.1.3", "10.0.1.255"])
        self.assertEqual(reserved_ips("10.20.32.0/20")[-1], "10.20.47.255")


# ── Exercise 02 ★: Plan the subnets ──────────────────────────────────
"""
prefix_for_hosts(hosts) -> int
    The SMALLEST subnet (largest prefix length, /28 at most) that still has `hosts` usable
    addresses after AWS's 5 reserved ones. hosts < 1 or more than a /16 can hold → ValueError.
    prefix_for_hosts(251) == 24      prefix_for_hosts(252) == 23      prefix_for_hosts(1) == 28
plan_subnets(vpc_cidr, tiers, azs) -> dict[(tier, az), cidr]
    One subnet per (tier, AZ). `tiers` maps tier name → hosts needed in each of its subnets.
    Allocate the biggest subnets first (on a tie, keep the order the tiers were given), each
    aligned to its own size, packed from the start of the VPC block, AZs in the order given.
    Subnets that do not fit in the VPC → ValueError.
Example:
    plan_subnets("10.0.0.0/16", {"public": 200, "app": 1000, "data": 100}, ["us-east-1a", "us-east-1b"]) ==
      {("app", "us-east-1a"): "10.0.0.0/22",  ("app", "us-east-1b"): "10.0.4.0/22",
       ("public", "us-east-1a"): "10.0.8.0/24", ("public", "us-east-1b"): "10.0.9.0/24",
       ("data", "us-east-1a"): "10.0.10.0/25", ("data", "us-east-1b"): "10.0.10.128/25"}
Why biggest first? Small blocks placed first leave gaps that big, aligned blocks cannot use.
Hint: keep a cursor (an int address); round it up to a multiple of the block size before each subnet.
"""
def prefix_for_hosts(hosts):
    raise NotImplementedError  # YOUR CODE


def plan_subnets(vpc_cidr, tiers, azs):
    raise NotImplementedError  # YOUR CODE


class Ex02(Drill):
    """Plan the subnets ★"""
    tasks = ("3.4",)

    def test_prefix_for_hosts(self):
        for hosts, want in {1: 28, 11: 28, 12: 27, 251: 24, 252: 23, 500: 23, 1000: 22, 65531: 16}.items():
            with self.subTest(hosts=hosts):
                self.assertEqual(prefix_for_hosts(hosts), want)
        for bad in (0, 65532):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    prefix_for_hosts(bad)

    def test_example_plan(self):
        self.assertEqual(plan_subnets("10.0.0.0/16", {"public": 200, "app": 1000, "data": 100}, ["us-east-1a", "us-east-1b"]), {
            ("app", "us-east-1a"): "10.0.0.0/22", ("app", "us-east-1b"): "10.0.4.0/22",
            ("public", "us-east-1a"): "10.0.8.0/24", ("public", "us-east-1b"): "10.0.9.0/24",
            ("data", "us-east-1a"): "10.0.10.0/25", ("data", "us-east-1b"): "10.0.10.128/25"})

    def test_three_azs_and_ties(self):
        plan = plan_subnets("10.50.0.0/20", {"web": 100, "jobs": 100}, ["a", "b", "c"])
        self.assertEqual(list(plan.values()), ["10.50.0.0/25", "10.50.0.128/25", "10.50.1.0/25",
                                               "10.50.1.128/25", "10.50.2.0/25", "10.50.2.128/25"])
        self.assertEqual(list(plan)[0], ("web", "a"))

    def test_does_not_fit(self):
        with self.assertRaises(ValueError):
            plan_subnets("10.0.0.0/24", {"app": 200}, ["a", "b"])


# ── Exercise 03 ★: Which way does the packet go? ─────────────────────
"""
route_target(destination_ip, routes) -> str | None
`routes` maps destination CIDR → target, like a route table:
    {"10.0.0.0/16": "local", "0.0.0.0/0": "nat-0a1", "10.1.0.0/16": "pcx-07b"}
Return the target of the MOST SPECIFIC route (longest prefix) that contains the destination, or
None when no route matches — then the packet is dropped. The local route is just a route: it wins
for VPC addresses because nothing more specific usually exists.
Examples:
    route_target("10.0.3.4", routes) == "local"      route_target("8.8.8.8", routes) == "nat-0a1"
Hint: ipaddress.ip_address(ip) in ipaddress.ip_network(cidr); compare .prefixlen.
"""
def route_target(destination_ip, routes):
    raise NotImplementedError  # YOUR CODE


class Ex03(Drill):
    """Which way does the packet go? ★"""
    tasks = ("3.4",)
    ROUTES = {"10.0.0.0/16": "local", "0.0.0.0/0": "igw-01", "10.1.0.0/16": "pcx-01", "10.1.5.0/24": "tgw-01",
              "192.168.0.0/16": "vgw-01"}

    def test_longest_prefix_wins(self):
        cases = {"10.0.3.4": "local", "8.8.8.8": "igw-01", "10.1.9.9": "pcx-01", "10.1.5.9": "tgw-01",
                 "192.168.4.4": "vgw-01", "10.2.0.1": "igw-01"}
        for ip, want in cases.items():
            with self.subTest(ip=ip):
                self.assertEqual(route_target(ip, self.ROUTES), want)

    def test_private_route_table_without_default_route(self):
        private = {"10.0.0.0/16": "local"}
        self.assertEqual(route_target("10.0.200.1", private), "local")
        self.assertIsNone(route_target("52.95.110.1", private))


# ── Exercise 04 ★: Security groups vs network ACLs ───────────────────
"""
Model one TCP connection from a client to a server inside a VPC.
A security-group rule:  {"protocol": "tcp" | "udp" | "icmp" | "-1" (all), "ports": (from, to), "peer": CIDR or "sg-…"}
A network-ACL rule:     {"rule": 100, "action": "allow" | "deny", "protocol": …, "ports": (from, to), "cidr": CIDR}
Host (given) = ip, subnet, sgs (its security-group ids), sg_in, sg_out, nacl_in, nacl_out.
ANY_OUT and NACL_ALLOW_ALL (given) are the default "allow everything" rules.

sg_allows(rules, peer_ip, peer_sgs, protocol, port) -> bool
    True if ANY rule matches the protocol and port and its peer is a CIDR containing peer_ip or a
    security-group id in peer_sgs. (Security groups only allow; there are no deny rules.)
nacl_allows(rules, peer_ip, protocol, port) -> bool
    Check rules in rule-number order, LOWEST first; the first rule that matches decides
    (allow → True, deny → False); if none matches, the hidden final rule denies → False.
tcp_connection(client, server, port, client_port=49152) -> (bool, str)
    Check in this order and return (False, <name>) for the first check that fails, else (True, "allowed"):
      "client security group (outbound)"        client.sg_out allows server (ip / sgs) on port
      "client network ACL (outbound)"           *  client.nacl_out allows server.ip on port
      "server network ACL (inbound)"            *  server.nacl_in allows client.ip on port
      "server security group (inbound)"         server.sg_in allows client (ip / sgs) on port
      "server network ACL (outbound, reply)"    *  server.nacl_out allows client.ip on client_port
      "client network ACL (inbound, reply)"     *  client.nacl_in allows server.ip on client_port
    * only when the two hosts are in different subnets — traffic inside one subnet never crosses
      its network ACL. Security groups are STATEFUL: replies are let back without a rule. Network
      ACLs are STATELESS: the reply to port `port` comes back to the client's ephemeral port.
"""
def sg_allows(rules, peer_ip, peer_sgs, protocol, port):
    raise NotImplementedError  # YOUR CODE


def nacl_allows(rules, peer_ip, protocol, port):
    raise NotImplementedError  # YOUR CODE


def tcp_connection(client, server, port, client_port=49152):
    raise NotImplementedError  # YOUR CODE


def _app_server(nacl_in=(NACL_ALLOW_ALL,), nacl_out=(NACL_ALLOW_ALL,), sg_in=None):
    rules = sg_in if sg_in is not None else ({"protocol": "tcp", "ports": (8000, 8000), "peer": "sg-alb"},)
    return Host(ip="10.0.8.20", subnet="app-a", sgs=("sg-app",), sg_in=rules, nacl_in=nacl_in, nacl_out=nacl_out)


ALB = Host(ip="10.0.0.10", subnet="public-a", sgs=("sg-alb",))


class Ex04(Drill):
    """Security groups vs network ACLs ★"""
    tasks = ("1.2",)

    def test_sg_and_nacl_rules(self):
        rules = [{"protocol": "tcp", "ports": (443, 443), "peer": "0.0.0.0/0"}, {"protocol": "-1", "ports": (0, 65535), "peer": "sg-ops"}]
        self.assertTrue(sg_allows(rules, "203.0.113.9", (), "tcp", 443))
        self.assertFalse(sg_allows(rules, "203.0.113.9", (), "tcp", 22))
        self.assertTrue(sg_allows(rules, "10.0.0.5", ("sg-ops",), "udp", 53))
        nacl = [{"rule": 200, "action": "allow", "protocol": "tcp", "ports": (0, 65535), "cidr": "0.0.0.0/0"},
                {"rule": 100, "action": "deny", "protocol": "tcp", "ports": (22, 22), "cidr": "0.0.0.0/0"}]
        self.assertFalse(nacl_allows(nacl, "198.51.100.1", "tcp", 22))   # rule 100 is checked first
        self.assertTrue(nacl_allows(nacl, "198.51.100.1", "tcp", 443))
        self.assertFalse(nacl_allows(nacl, "198.51.100.1", "udp", 53))   # nothing matches → denied

    def test_security_group_reference(self):
        self.assertEqual(tcp_connection(ALB, _app_server(), 8000), (True, "allowed"))
        self.assertEqual(tcp_connection(ALB, _app_server(), 22), (False, "server security group (inbound)"))
        stranger = Host(ip="10.0.0.11", subnet="public-a", sgs=("sg-other",))
        self.assertEqual(tcp_connection(stranger, _app_server(), 8000), (False, "server security group (inbound)"))

    def test_nacl_rule_order(self):
        deny_first = ({"rule": 90, "action": "deny", "protocol": "tcp", "ports": (8000, 8000), "cidr": "10.0.0.10/32"}, NACL_ALLOW_ALL)
        self.assertEqual(tcp_connection(ALB, _app_server(nacl_in=deny_first), 8000), (False, "server network ACL (inbound)"))
        deny_later = (NACL_ALLOW_ALL, {"rule": 200, "action": "deny", "protocol": "tcp", "ports": (8000, 8000), "cidr": "10.0.0.10/32"})
        self.assertEqual(tcp_connection(ALB, _app_server(nacl_in=deny_later), 8000), (True, "allowed"))

    def test_stateless_replies_need_ephemeral_ports(self):
        only_8000 = ({"rule": 100, "action": "allow", "protocol": "tcp", "ports": (8000, 8000), "cidr": "0.0.0.0/0"},)
        self.assertEqual(tcp_connection(ALB, _app_server(nacl_out=only_8000), 8000), (False, "server network ACL (outbound, reply)"))
        ephemeral = ({"rule": 100, "action": "allow", "protocol": "tcp", "ports": (1024, 65535), "cidr": "0.0.0.0/0"},)
        self.assertEqual(tcp_connection(ALB, _app_server(nacl_out=ephemeral), 8000), (True, "allowed"))
        client = Host(ip="10.0.0.10", subnet="public-a", sgs=("sg-alb",), nacl_in=only_8000)
        self.assertEqual(tcp_connection(client, _app_server(), 8000), (False, "client network ACL (inbound, reply)"))

    def test_same_subnet_and_client_egress(self):
        closed = ({"rule": 100, "action": "deny", "protocol": "-1", "ports": (0, 65535), "cidr": "0.0.0.0/0"},)
        a = Host(ip="10.0.8.5", subnet="app-a", sgs=("sg-a",), nacl_in=closed, nacl_out=closed)
        b = Host(ip="10.0.8.6", subnet="app-a", sgs=("sg-b",), nacl_in=closed, nacl_out=closed,
                 sg_in=({"protocol": "tcp", "ports": (5432, 5432), "peer": "10.0.8.0/24"},))
        self.assertEqual(tcp_connection(a, b, 5432), (True, "allowed"))
        silent = Host(ip="10.0.8.5", subnet="app-a", sgs=("sg-a",), sg_out=())
        self.assertEqual(tcp_connection(silent, b, 5432), (False, "client security group (outbound)"))


# ── Exercise 05 ★: Peering or a transit gateway? ─────────────────────
"""
can_peer(cidr_a, cidr_b) -> bool
    Two VPCs can be peered only if their CIDR blocks do NOT overlap.
can_reach(source, target, peerings, tgw_attachments=()) -> bool
    `peerings` is a list of (vpc, vpc) pairs, in either order. `tgw_attachments` lists the VPCs
    attached to ONE transit gateway that routes between all of them. A VPC always reaches itself.
    VPC peering is NOT transitive: a–b and b–c peered does not let a reach c. A transit gateway is
    a hub: any two attached VPCs reach each other.
peerings_for_full_mesh(vpcs) -> int
    How many peering connections let every one of `vpcs` VPCs reach every other (negative → ValueError).
    peerings_for_full_mesh(5) == 10 — while a transit gateway needs only 5 attachments.
"""
def can_peer(cidr_a, cidr_b):
    raise NotImplementedError  # YOUR CODE


def can_reach(source, target, peerings, tgw_attachments=()):
    raise NotImplementedError  # YOUR CODE


def peerings_for_full_mesh(vpcs):
    raise NotImplementedError  # YOUR CODE


class Ex05(Drill):
    """Peering or a transit gateway? ★"""
    tasks = ("3.4", "4.4")

    def test_can_peer(self):
        self.assertTrue(can_peer("10.0.0.0/16", "10.1.0.0/16"))
        self.assertFalse(can_peer("10.0.0.0/16", "10.0.128.0/17"))
        self.assertFalse(can_peer("172.31.0.0/16", "172.31.0.0/16"))

    def test_peering_is_not_transitive(self):
        peerings = [("shared", "prod"), ("dev", "shared")]
        self.assertTrue(can_reach("prod", "shared", peerings))
        self.assertTrue(can_reach("shared", "dev", peerings))
        self.assertFalse(can_reach("prod", "dev", peerings))
        self.assertTrue(can_reach("prod", "prod", []))

    def test_transit_gateway_is_a_hub(self):
        self.assertTrue(can_reach("prod", "dev", [], tgw_attachments=["prod", "dev", "shared"]))
        self.assertFalse(can_reach("prod", "lab", [], tgw_attachments=["prod", "dev"]))

    def test_full_mesh_count(self):
        self.assertEqual([peerings_for_full_mesh(n) for n in (0, 1, 2, 3, 5, 10)], [0, 0, 1, 3, 10, 45])
        with self.assertRaises(ValueError):
            peerings_for_full_mesh(-1)


# ── Exercise 06: Build a VPC with boto3 ──────────────────────────────
"""
build_vpc(ec2, cidr, plan) -> dict
`plan` maps (tier, az) → subnet CIDR — exactly what your plan_subnets returns. The tier named
"public" is public; every other tier is private. With the `ec2` client, create:
  1. a VPC with `cidr`, then turn on DNS support and DNS hostnames (modify_vpc_attribute, one
     attribute per call);
  2. one subnet per plan entry, in its AZ, with its CIDR;
  3. an internet gateway, attached to the VPC;
  4. ONE public route table with a default route (0.0.0.0/0) to the internet gateway, associated
     with every public subnet;
  5. ONE private route table PER AZ, with no default route (no internet), associated with every
     private subnet in that AZ.
Return {"vpc": vpc_id, "igw": igw_id, "subnets": {(tier, az): subnet_id},
        "route_tables": {"public": rt_id, az: rt_id for each AZ that has private subnets}}.
Hint: ec2.create_vpc(CidrBlock=…)["Vpc"]["VpcId"]; create_subnet(VpcId=…, CidrBlock=…, AvailabilityZone=…);
      create_internet_gateway / attach_internet_gateway; create_route_table / create_route / associate_route_table.
"""
def build_vpc(ec2, cidr, plan):
    raise NotImplementedError  # YOUR CODE


PLAN = {("public", "us-east-1a"): "10.30.0.0/24", ("public", "us-east-1b"): "10.30.1.0/24",
        ("app", "us-east-1a"): "10.30.8.0/22", ("app", "us-east-1b"): "10.30.12.0/22",
        ("data", "us-east-1a"): "10.30.16.0/24", ("data", "us-east-1b"): "10.30.17.0/24"}


def _routes(ec2, rt_id):
    return ec2.describe_route_tables(RouteTableIds=[rt_id])["RouteTables"][0]


class Ex06(Drill):
    """Build a VPC with boto3"""
    tasks = ("3.4", "2.2")
    uses_aws = True

    def build(self):
        ec2 = self.client("ec2")
        return ec2, build_vpc(ec2, "10.30.0.0/16", PLAN)

    def test_vpc_dns_and_igw(self):
        ec2, out = self.build()
        vpc = ec2.describe_vpcs(VpcIds=[out["vpc"]])["Vpcs"][0]
        self.assertEqual(vpc["CidrBlock"], "10.30.0.0/16")
        for attribute, key in (("enableDnsSupport", "EnableDnsSupport"), ("enableDnsHostnames", "EnableDnsHostnames")):
            got = ec2.describe_vpc_attribute(VpcId=out["vpc"], Attribute=attribute)[key]["Value"]
            self.assertTrue(got, f"turn on {attribute}")
        igw = ec2.describe_internet_gateways(InternetGatewayIds=[out["igw"]])["InternetGateways"][0]
        self.assertEqual([a["VpcId"] for a in igw["Attachments"]], [out["vpc"]])

    def test_subnets_follow_the_plan(self):
        ec2, out = self.build()
        self.assertEqual(set(out["subnets"]), set(PLAN))
        for key, subnet_id in out["subnets"].items():
            subnet = ec2.describe_subnets(SubnetIds=[subnet_id])["Subnets"][0]
            with self.subTest(key=key):
                self.assertEqual((subnet["CidrBlock"], subnet["AvailabilityZone"], subnet["VpcId"]), (PLAN[key], key[1], out["vpc"]))

    def test_public_route_table(self):
        ec2, out = self.build()
        table = _routes(ec2, out["route_tables"]["public"])
        defaults = [r for r in table["Routes"] if r.get("DestinationCidrBlock") == "0.0.0.0/0"]
        self.assertEqual([r.get("GatewayId") for r in defaults], [out["igw"]], "public: 0.0.0.0/0 → the internet gateway")
        associated = {a.get("SubnetId") for a in table["Associations"]}
        self.assertEqual(associated - {None}, {out["subnets"][k] for k in PLAN if k[0] == "public"})

    def test_private_route_tables_have_no_internet(self):
        ec2, out = self.build()
        for az in ("us-east-1a", "us-east-1b"):
            table = _routes(ec2, out["route_tables"][az])
            with self.subTest(az=az):
                self.assertFalse([r for r in table["Routes"] if r.get("DestinationCidrBlock") == "0.0.0.0/0"],
                                 "private route tables have no default route")
                associated = {a.get("SubnetId") for a in table["Associations"]} - {None}
                self.assertEqual(associated, {out["subnets"][k] for k in PLAN if k[0] != "public" and k[1] == az})


# ── Exercise 07: Security groups that reference each other ───────────
"""
create_web_sgs(ec2, vpc_id) -> {"alb": sg_id, "app": sg_id, "db": sg_id}
Three security groups in the VPC, named "shortly-alb", "shortly-app" and "shortly-db":
  alb  inbound TCP 443 from anywhere (0.0.0.0/0)
  app  inbound TCP 8000 ONLY from the alb security group (a security-group reference, not a CIDR)
  db   inbound TCP 5432 ONLY from the app security group
Nothing else inbound — in particular no SSH (22) from anywhere: use Session Manager to get a shell.
Leave the default outbound rule (all traffic) alone.
Why references? Instances come and go and their IPs change; "from the app security group" keeps
working for every instance that carries that group.
Hint: authorize_security_group_ingress(GroupId=…, IpPermissions=[{"IpProtocol": "tcp", "FromPort": 8000,
      "ToPort": 8000, "UserIdGroupPairs": [{"GroupId": alb_id}]}]) — for a CIDR use "IpRanges": [{"CidrIp": …}].
"""
def create_web_sgs(ec2, vpc_id):
    raise NotImplementedError  # YOUR CODE


def _ingress(ec2, sg_id):
    return ec2.describe_security_groups(GroupIds=[sg_id])["SecurityGroups"][0]["IpPermissions"]


class Ex07(Drill):
    """Security groups that reference each other"""
    tasks = ("1.2",)
    uses_aws = True

    def make(self):
        ec2 = self.client("ec2")
        vpc = ec2.create_vpc(CidrBlock="10.40.0.0/16")["Vpc"]["VpcId"]
        return ec2, vpc, create_web_sgs(ec2, vpc)

    def test_names_and_vpc(self):
        ec2, vpc, sgs = self.make()
        self.assertEqual(set(sgs), {"alb", "app", "db"})
        for role, sg_id in sgs.items():
            group = ec2.describe_security_groups(GroupIds=[sg_id])["SecurityGroups"][0]
            with self.subTest(role=role):
                self.assertEqual((group["GroupName"], group["VpcId"]), (f"shortly-{role}", vpc))

    def test_chain(self):
        ec2, _, sgs = self.make()
        alb = _ingress(ec2, sgs["alb"])
        self.assertEqual([(p["FromPort"], [r["CidrIp"] for r in p.get("IpRanges", [])]) for p in alb], [(443, ["0.0.0.0/0"])])
        for role, port, source in (("app", 8000, "alb"), ("db", 5432, "app")):
            rules = _ingress(ec2, sgs[role])
            with self.subTest(role=role):
                self.assertEqual(len(rules), 1, f"{role}: exactly one inbound rule")
                self.assertEqual((rules[0]["IpProtocol"], rules[0]["FromPort"], rules[0]["ToPort"]), ("tcp", port, port))
                self.assertEqual([g["GroupId"] for g in rules[0].get("UserIdGroupPairs", [])], [sgs[source]])
                self.assertFalse(rules[0].get("IpRanges"), f"{role}: no CIDR sources, only the {source} security group")

    def test_no_ssh_from_the_internet(self):
        ec2, _, sgs = self.make()
        for role, sg_id in sgs.items():
            for p in _ingress(ec2, sg_id):
                with self.subTest(role=role):
                    self.assertFalse(p.get("FromPort", 0) <= 22 <= p.get("ToPort", 65535) and p.get("IpRanges"),
                                     f"{role} opens SSH to an address range")


# ── Exercise 08: Reach S3 without the internet ───────────────────────
"""
add_s3_gateway_endpoint(ec2, vpc_id, route_table_ids, bucket) -> endpoint_id
    Create a GATEWAY VPC endpoint for S3 in the client's Region (service name
    f"com.amazonaws.{ec2.meta.region_name}.s3"), attached to `route_table_ids`, with an endpoint
    policy that allows only s3:GetObject, s3:PutObject and s3:ListBucket on that one bucket
    (arn:aws:s3:::BUCKET and arn:aws:s3:::BUCKET/*) for any principal ("Principal": "*").
    AWS then adds a route for S3's prefix list to each of those route tables.
vpce_only_bucket_policy(bucket, vpce_id) -> dict
    A bucket policy that DENIES every s3:* action on the bucket and its objects, for any
    principal, unless the request came through `vpce_id` (condition key aws:SourceVpce).
    Gateway endpoints are free and keep S3 traffic on the AWS network — no NAT gateway needed.
Hint: create_vpc_endpoint(VpcEndpointType="Gateway", VpcId=…, ServiceName=…, RouteTableIds=[…],
      PolicyDocument=json.dumps(policy))["VpcEndpoint"]["VpcEndpointId"].
"""
import json  # noqa: E402


def add_s3_gateway_endpoint(ec2, vpc_id, route_table_ids, bucket):
    raise NotImplementedError  # YOUR CODE


def vpce_only_bucket_policy(bucket, vpce_id):
    raise NotImplementedError  # YOUR CODE


class Ex08(Drill):
    """Reach S3 without the internet"""
    tasks = ("1.2", "3.4")
    uses_aws = True
    BUCKET = "shortly-assets-drill"

    def make(self):
        ec2 = self.client("ec2")
        vpc = ec2.create_vpc(CidrBlock="10.50.0.0/16")["Vpc"]["VpcId"]
        tables = [ec2.create_route_table(VpcId=vpc)["RouteTable"]["RouteTableId"] for _ in range(2)]
        return ec2, vpc, tables, add_s3_gateway_endpoint(ec2, vpc, tables, self.BUCKET)

    def test_endpoint(self):
        ec2, vpc, tables, endpoint_id = self.make()
        endpoint = ec2.describe_vpc_endpoints(VpcEndpointIds=[endpoint_id])["VpcEndpoints"][0]
        self.assertEqual((endpoint["VpcEndpointType"], endpoint["ServiceName"], endpoint["VpcId"]),
                         ("Gateway", "com.amazonaws.us-east-1.s3", vpc))
        self.assertEqual(sorted(endpoint["RouteTableIds"]), sorted(tables))
        for table in ec2.describe_route_tables(RouteTableIds=tables)["RouteTables"]:
            with self.subTest(table=table["RouteTableId"]):
                self.assertTrue(any(r.get("DestinationPrefixListId") for r in table["Routes"]), "a prefix-list route to S3")

    def test_endpoint_policy_is_narrow(self):
        ec2, _, _, endpoint_id = self.make()
        raw = ec2.describe_vpc_endpoints(VpcEndpointIds=[endpoint_id])["VpcEndpoints"][0]["PolicyDocument"]
        policy = json.loads(raw) if isinstance(raw, str) else raw
        role = "arn:aws:sts::123456789012:assumed-role/shortly-app/i-1"
        decide = lambda action, arn: ref_policy.evaluate(ref_policy.Request(role, action, arn), identity=[],
                                                         resource_policy=policy, resource_account="123456789012")
        self.assertEqual(decide("s3:GetObject", f"arn:aws:s3:::{self.BUCKET}/a.png"), "Allow")
        self.assertEqual(decide("s3:ListBucket", f"arn:aws:s3:::{self.BUCKET}"), "Allow")
        self.assertNotEqual(decide("s3:GetObject", "arn:aws:s3:::someone-elses-bucket/a.png"), "Allow")
        self.assertNotEqual(decide("s3:DeleteObject", f"arn:aws:s3:::{self.BUCKET}/a.png"), "Allow")

    def test_bucket_policy_requires_the_endpoint(self):
        policy = vpce_only_bucket_policy(self.BUCKET, "vpce-0abc")
        app = [{"Statement": [{"Effect": "Allow", "Action": "s3:*", "Resource": "*"}]}]
        role = "arn:aws:sts::123456789012:assumed-role/shortly-app/i-1"
        obj = f"arn:aws:s3:::{self.BUCKET}/a.png"
        for context, want in (({"aws:SourceVpce": "vpce-0abc"}, "Allow"), ({"aws:SourceVpce": "vpce-9zzz"}, "ExplicitDeny"),
                              ({}, "ExplicitDeny")):
            with self.subTest(context=context):
                got = ref_policy.evaluate(ref_policy.Request(role, "s3:GetObject", obj, context), identity=app,
                                          resource_policy=policy, resource_account="123456789012")
                self.assertEqual(got, want)
        bucket_level = ref_policy.Request(role, "s3:ListBucket", f"arn:aws:s3:::{self.BUCKET}", {})
        self.assertEqual(ref_policy.evaluate(bucket_level, identity=app, resource_policy=policy), "ExplicitDeny",
                         "cover the bucket ARN as well as its objects")


# ── Exercise 09 ★: NAT gateway or endpoint? ──────────────────────────
"""
Private instances move `gb` GB per month to and from S3. Compare three paths (USD per month,
rounded to 2 decimal places), using PRICES (illustrative us-east-1 prices, _harness/awslib/prices.toml):
nat_monthly_cost(gb, nat_gateways, hours=730, price=PRICES)
    nat_gateways × hours × nat_gateway_per_hour  +  gb × nat_gateway_per_gb
interface_endpoint_monthly_cost(gb, azs, hours=730, price=PRICES)
    azs × hours × interface_endpoint_per_hour_per_az  +  gb × interface_endpoint_per_gb
s3_path_costs(gb, nat_gateways, azs, hours=730, price=PRICES) -> dict
    {"nat gateway": …, "interface endpoint": …, "gateway endpoint": gb × gateway_endpoint_per_gb (free)}
Example (2 NAT gateways, 2 AZs, 5,000 GB): the NAT path costs 2 × 730 × 0.045 + 5,000 × 0.045 = 290.70.
Negative gb, nat_gateways or azs → ValueError.
"""
PRICES = prices.section("vpc")


def nat_monthly_cost(gb, nat_gateways, hours=730, price=PRICES):
    raise NotImplementedError  # YOUR CODE


def interface_endpoint_monthly_cost(gb, azs, hours=730, price=PRICES):
    raise NotImplementedError  # YOUR CODE


def s3_path_costs(gb, nat_gateways, azs, hours=730, price=PRICES):
    raise NotImplementedError  # YOUR CODE


class Ex09(Drill):
    """NAT gateway or endpoint? ★"""
    tasks = ("4.4",)

    def test_nat(self):
        p = PRICES
        self.assertAlmostEqual(nat_monthly_cost(5000, 2), round(2 * 730 * p["nat_gateway_per_hour"] + 5000 * p["nat_gateway_per_gb"], 2))
        self.assertAlmostEqual(nat_monthly_cost(0, 1, hours=100), round(100 * p["nat_gateway_per_hour"], 2))

    def test_interface_endpoint(self):
        p = PRICES
        self.assertAlmostEqual(interface_endpoint_monthly_cost(5000, 2),
                               round(2 * 730 * p["interface_endpoint_per_hour_per_az"] + 5000 * p["interface_endpoint_per_gb"], 2))

    def test_all_paths(self):
        costs = s3_path_costs(5000, 2, 2)
        self.assertEqual(set(costs), {"nat gateway", "interface endpoint", "gateway endpoint"})
        self.assertEqual(costs["gateway endpoint"], round(5000 * PRICES["gateway_endpoint_per_gb"], 2))
        self.assertLess(costs["gateway endpoint"], costs["interface endpoint"])
        self.assertLess(costs["interface endpoint"], costs["nat gateway"])

    def test_uses_the_price_argument(self):
        custom = dict(PRICES, nat_gateway_per_hour=1.0, nat_gateway_per_gb=0.0)
        self.assertEqual(nat_monthly_cost(999, 1, hours=10, price=custom), 10.0)

    def test_rejects_negative_inputs(self):
        for call in (lambda: nat_monthly_cost(-1, 1), lambda: nat_monthly_cost(1, -1), lambda: interface_endpoint_monthly_cost(1, -2)):
            with self.subTest():
                with self.assertRaises(ValueError):
                    call()


# ── Exercise 10 (predict): Does the traffic get through? ─────────────
"""
For each scenario, decide "yes" (the traffic gets through) or "no" — BEFORE running anything —
and write it in PREDICTIONS. The test asks the course's reference models (netsim) for the truth.
"""
from _harness.awslib import netsim as _ref_net  # noqa: E402

S3_PREFIX = "52.216.0.0/15"   # stands in for S3's prefix list in us-east-1
SCENARIOS = {
    1: ("A private subnet's route table has only the local route 10.0.0.0/16. An instance there calls S3 at 52.216.4.10.",
        ("route", "52.216.4.10", {"10.0.0.0/16": "local"})),
    2: ("The same route table after adding an S3 gateway endpoint (its prefix list routes to vpce-s3). The instance calls S3 at 52.216.4.10.",
        ("route", "52.216.4.10", {"10.0.0.0/16": "local", S3_PREFIX: "vpce-s3"})),
    3: ("With only the S3 gateway endpoint (no NAT gateway), the instance downloads an OS update from 151.101.0.1.",
        ("route", "151.101.0.1", {"10.0.0.0/16": "local", S3_PREFIX: "vpce-s3"})),
    4: ("The app's security group allows TCP 8000 from the load balancer's security group; both subnets use the default network ACL. The load balancer connects on 8000.",
        ("tcp", ALB, _app_server(), 8000)),
    5: ("The app subnet's network ACL allows inbound TCP 8000 and outbound TCP 8000 only. The load balancer connects on 8000.",
        ("tcp", ALB, _app_server(nacl_in=({"rule": 100, "action": "allow", "protocol": "tcp", "ports": (8000, 8000), "cidr": "0.0.0.0/0"},),
                                 nacl_out=({"rule": 100, "action": "allow", "protocol": "tcp", "ports": (8000, 8000), "cidr": "0.0.0.0/0"},)), 8000)),
    6: ("VPC prod is peered with shared, and shared is peered with dev. An instance in prod connects to one in dev.",
        ("reach", "prod", "dev", [("prod", "shared"), ("shared", "dev")])),
}
PREDICTIONS = {n: None for n in SCENARIOS}   # YOUR ANSWERS: "yes" or "no"


def _truth(kind, *args):
    if kind == "route":
        return _ref_net.route_target(args[0], args[1]) is not None
    if kind == "tcp":
        return _ref_net.tcp_connection(*args)[0]
    return _ref_net.can_reach(*args)


class Ex10(Drill):
    """Does the traffic get through?"""
    tasks = ("3.4", "1.2")

    def test_predictions(self):
        for n, (story, scenario) in SCENARIOS.items():
            with self.subTest(scenario=n):
                truth = "yes" if _truth(*scenario) else "no"
                self.assertIn(PREDICTIONS.get(n), ("yes", "no"), f"scenario {n}: write 'yes' or 'no'")
                self.assertEqual(PREDICTIONS[n], truth, f"scenario {n}: {story} — the answer is {truth}")


if __name__ == "__main__":
    run()
````

### `week_02_vpc_networking/practice/solutions.py`

````python
"""Reference solutions for week 02.

Drills 01–05: the course's reference models ARE the solution — read _harness/awslib/cidr.py and
_harness/awslib/netsim.py and compare them with yours.
"""
import json

from _harness.awslib.cidr import plan_subnets, prefix_for_hosts, reserved_ips, usable_ips  # noqa: F401
from _harness.awslib.netsim import (can_peer, can_reach, nacl_allows, peerings_for_full_mesh,  # noqa: F401
                                    route_target, sg_allows, tcp_connection)


def build_vpc(ec2, cidr, plan):
    vpc = ec2.create_vpc(CidrBlock=cidr)["Vpc"]["VpcId"]
    ec2.modify_vpc_attribute(VpcId=vpc, EnableDnsSupport={"Value": True})
    ec2.modify_vpc_attribute(VpcId=vpc, EnableDnsHostnames={"Value": True})
    subnets = {key: ec2.create_subnet(VpcId=vpc, CidrBlock=block, AvailabilityZone=key[1])["Subnet"]["SubnetId"]
               for key, block in plan.items()}
    igw = ec2.create_internet_gateway()["InternetGateway"]["InternetGatewayId"]
    ec2.attach_internet_gateway(InternetGatewayId=igw, VpcId=vpc)
    public = ec2.create_route_table(VpcId=vpc)["RouteTable"]["RouteTableId"]
    ec2.create_route(RouteTableId=public, DestinationCidrBlock="0.0.0.0/0", GatewayId=igw)
    tables = {"public": public}
    for (tier, az), subnet in subnets.items():
        if tier == "public":
            ec2.associate_route_table(RouteTableId=public, SubnetId=subnet)
            continue
        if az not in tables:
            tables[az] = ec2.create_route_table(VpcId=vpc)["RouteTable"]["RouteTableId"]
        ec2.associate_route_table(RouteTableId=tables[az], SubnetId=subnet)
    return {"vpc": vpc, "igw": igw, "subnets": subnets, "route_tables": tables}


def _tcp(port, **source):
    return {"IpProtocol": "tcp", "FromPort": port, "ToPort": port, **source}


def create_web_sgs(ec2, vpc_id):
    sgs = {role: ec2.create_security_group(GroupName=f"shortly-{role}", Description=f"shortly {role} tier",
                                           VpcId=vpc_id)["GroupId"] for role in ("alb", "app", "db")}
    ec2.authorize_security_group_ingress(GroupId=sgs["alb"], IpPermissions=[_tcp(443, IpRanges=[{"CidrIp": "0.0.0.0/0"}])])
    ec2.authorize_security_group_ingress(GroupId=sgs["app"], IpPermissions=[_tcp(8000, UserIdGroupPairs=[{"GroupId": sgs["alb"]}])])
    ec2.authorize_security_group_ingress(GroupId=sgs["db"], IpPermissions=[_tcp(5432, UserIdGroupPairs=[{"GroupId": sgs["app"]}])])
    return sgs


def add_s3_gateway_endpoint(ec2, vpc_id, route_table_ids, bucket):
    policy = {"Version": "2012-10-17", "Statement": [{
        "Effect": "Allow", "Principal": "*", "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
        "Resource": [f"arn:aws:s3:::{bucket}", f"arn:aws:s3:::{bucket}/*"]}]}
    endpoint = ec2.create_vpc_endpoint(VpcEndpointType="Gateway", VpcId=vpc_id, RouteTableIds=list(route_table_ids),
                                       ServiceName=f"com.amazonaws.{ec2.meta.region_name}.s3",
                                       PolicyDocument=json.dumps(policy))
    return endpoint["VpcEndpoint"]["VpcEndpointId"]


def vpce_only_bucket_policy(bucket, vpce_id):
    return {"Version": "2012-10-17", "Statement": [{
        "Sid": "OnlyThroughOurEndpoint", "Effect": "Deny", "Principal": "*", "Action": "s3:*",
        "Resource": [f"arn:aws:s3:::{bucket}", f"arn:aws:s3:::{bucket}/*"],
        "Condition": {"StringNotEquals": {"aws:SourceVpce": vpce_id}}}]}


def _check(*values):
    if any(v < 0 for v in values):
        raise ValueError("inputs must not be negative")


def nat_monthly_cost(gb, nat_gateways, hours=730, price=PRICES):
    _check(gb, nat_gateways, hours)
    return round(nat_gateways * hours * price["nat_gateway_per_hour"] + gb * price["nat_gateway_per_gb"], 2)


def interface_endpoint_monthly_cost(gb, azs, hours=730, price=PRICES):
    _check(gb, azs, hours)
    return round(azs * hours * price["interface_endpoint_per_hour_per_az"] + gb * price["interface_endpoint_per_gb"], 2)


def s3_path_costs(gb, nat_gateways, azs, hours=730, price=PRICES):
    _check(gb, nat_gateways, azs, hours)
    return {"nat gateway": nat_monthly_cost(gb, nat_gateways, hours, price),
            "interface endpoint": interface_endpoint_monthly_cost(gb, azs, hours, price),
            "gateway endpoint": round(gb * price["gateway_endpoint_per_gb"], 2)}


PREDICTIONS = {1: "no", 2: "yes", 3: "no", 4: "yes", 5: "no", 6: "no"}
````


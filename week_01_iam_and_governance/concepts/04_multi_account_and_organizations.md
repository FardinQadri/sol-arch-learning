Exam tasks: 1.1, 4.1

# 04 — Multi-account design: Organizations, Control Tower, RAM

## What it is

Serious AWS setups use **many accounts**, not one. An account is the strongest
boundary AWS gives you: separate IAM, separate limits, separate bill line.

Three services help you run many accounts:

- **AWS Organizations** — groups accounts, applies guardrails (SCPs), and
  combines billing.
- **AWS Control Tower** — sets up a well-built multi-account environment for you
  (a "landing zone") on top of Organizations.
- **AWS Resource Access Manager (RAM)** — shares resources, such as subnets,
  between accounts without copying them.

## How it works

### Why many accounts

- **Blast radius.** A mistake or breach in one account stops at its edge. A
  compromised dev account cannot touch prod.
- **Clean billing.** One account per workload or team makes cost allocation
  trivial.
- **Limits.** Service quotas are per account and Region. Separate accounts do
  not compete for them.
- **Compliance.** Regulated data lives in an account with tighter controls and
  fewer people.
- **Simple IAM.** "Everyone in the dev account may do X" beats a tangle of
  per-resource conditions.

A common layout: a management account (billing and Organizations only, no
workloads), a **log archive** account, a **security/audit** account, a shared
**network** account, then workload accounts for `dev`, `test` and `prod`
grouped in OUs.

### AWS Organizations

- The **management account** creates the organization. It pays for everyone.
  Keep it nearly empty and heavily protected.
- **Member accounts** join (invited) or are created in the organization.
- **Organizational units (OUs)** are folders of accounts. They can nest. A
  policy attached to an OU applies to everything beneath it.
- The **organization root** is the top node.

**Service control policies (SCPs)** set the *maximum* permissions for the
accounts they cover. The rules to know cold:

- An SCP **never grants** anything. It only limits what identity and resource
  policies in the account can allow.
- SCPs affect **all principals in member accounts, including their root user**.
- SCPs **do not affect the management account**. Never run workloads there
  expecting guardrails.
- SCPs do not affect **service-linked roles**.
- The effective permission is the intersection of every SCP from the root down
  to the account, plus the identity policy.

Two strategies:

| Strategy | How | Trade-off |
|---|---|---|
| **Deny-list** | Keep `FullAWSAccess` attached; add `Deny` SCPs for what you forbid | Easy to run, the common choice; new services are allowed by default |
| **Allow-list** | Remove `FullAWSAccess`; attach SCPs allowing only chosen services | Strict; more work, because every needed service must be listed |

Typical deny-list guardrails: deny leaving the organization, deny disabling
CloudTrail or GuardDuty, deny actions outside approved Regions (note 02, demo
case 3), deny root user actions in member accounts, deny creating unencrypted
resources.

**Resource control policies (RCPs)** do the same for resources: "nothing in our
accounts may be shared outside the organization". Like SCPs, they never grant.

**Tag policies** standardise tag keys and values. **Backup policies** and
**AI opt-out policies** exist too; the exam mostly asks about SCPs.

**`aws:PrincipalOrgID`** — in a resource policy, a condition on this key means
"any principal from my organization". It replaces a long list of account IDs and
stays correct as accounts come and go.

```json
{"Effect": "Allow", "Principal": "*", "Action": "s3:GetObject",
 "Resource": "arn:aws:s3:::acme-shared-data/*",
 "Condition": {"StringEquals": {"aws:PrincipalOrgID": "o-exampleorgid"}}}
```

**Consolidated billing.** The management account receives one bill for all
members. The benefits:

- **Pooled volume discounts.** Tiered prices (for example, S3 storage or data
  transfer that gets cheaper per unit as total use grows) count the *combined*
  usage of all accounts, so the whole group reaches cheaper tiers sooner. Drill 09
  puts numbers on this.
- **Savings Plans and Reserved Instance sharing.** Unused commitment in one
  account is applied to matching usage in another. A member account does not
  waste a commitment while a sibling pays on-demand. (This sharing can be turned
  off per account.)
- One payment, one place for budgets and cost reports.

### AWS Control Tower

Control Tower builds and governs a **landing zone**: a pre-configured,
multi-account environment that follows AWS best practice. It sets up:

- an Organizations structure with OUs;
- a log archive and an audit account;
- IAM Identity Center for sign-in;
- centralised CloudTrail and Config logging;
- **Account Factory** — a way to create new accounts to a standard baseline,
  with guardrails already attached.

**Controls** (formerly "guardrails") are the rules it applies:

| Control type | Implemented with | What it does |
|---|---|---|
| Preventive | SCPs (and RCPs) | Stops the action from happening |
| Detective | AWS Config rules | Finds and reports non-compliance after the fact |
| Proactive | CloudFormation hooks | Blocks a non-compliant resource before it is created |

Exam habit: "set up a secure multi-account environment with the **least
operational effort**" = Control Tower. "Prevent" = preventive control = SCP.
"Detect" = Config. "Check a template before deploy" = proactive.

### AWS RAM

Some resources can be **shared** with other accounts (or the whole organization)
rather than duplicated:

- VPC **subnets** — workload accounts launch into a shared subnet owned by a
  network account;
- **Transit Gateways**, Route 53 Resolver rules, License Manager configurations,
  and more.

RAM shares the resource; the receiving account uses it as if local. It is the
answer to "many accounts must use the same network or gateway without
connecting separate copies". Sharing within an organization can be switched on
once, so no per-share invitations are needed. RAM itself is free.

Not every resource is shareable with RAM. For S3, KMS and SQS you share with a
resource policy (and `aws:PrincipalOrgID`), not RAM.

### Practising offline

`docs/facts.md` warns: a **Free-plan account is upgraded to Paid automatically
if it joins AWS Organizations or sets up a Control Tower landing zone.** So this
course never asks you to create an organization in a lab. You practise SCPs
**offline**: the reference evaluator and the drills evaluate SCP chains, and
the milestone uses CloudFormation-style checks, not a live organization.

## Numbers to know

| Fact | Value |
|---|---|
| Free plan, joins Organizations or Control Tower | upgraded to Paid automatically |
| Free plan ends | after 6 months or when credits run out |
| Days to upgrade before deletion after closure | 90 |
| Domain 4 weight | 20 % |
| Management account | 1 per organization; SCPs never apply to it |

There are no quota numbers for accounts or OUs in `docs/facts.md`, so none are taught here.

## When to choose it

| Need | Pick |
|---|---|
| Group accounts and set guardrails | Organizations + SCPs |
| Forbid an action everywhere, even for admins | SCP `Deny` (affects member-account root, too) |
| Set up a secure multi-account baseline fast | Control Tower |
| Create accounts to a standard | Control Tower Account Factory |
| Detect non-compliant resources | Detective control (Config rule) |
| Block bad templates before deploy | Proactive control (CloudFormation hook) |
| Share one VPC subnet or Transit Gateway across accounts | RAM |
| Allow every account in my organization to read a bucket | `aws:PrincipalOrgID` in the bucket policy |
| Lower the price of combined usage | Consolidated billing (pooled tiers) |
| Reuse a Savings Plan across teams | Organizations (sharing on) |

## Exam traps

- **SCPs never grant.** "Add an SCP so the dev account can use EC2" does nothing alone.
- **SCPs do not affect the management account** or service-linked roles.
- **SCPs do affect the root user of member accounts.** "Even root" questions: SCP.
- **Deny-list vs allow-list.** Default setup is deny-list because `FullAWSAccess` is attached.
- **Preventive = SCP; detective = Config; proactive = CloudFormation hook.** Do not swap them.
- **Control Tower ≠ Organizations.** Control Tower *uses* Organizations; it is the easy button, not a replacement.
- **RAM shares resources; policies share data services.** Subnets and TGWs via RAM; buckets and keys via resource policies.
- **PrincipalOrgID beats listing accounts** when the question says "all accounts, including future ones".
- **Free-plan accounts.** Joining Organizations or Control Tower upgrades them to Paid.
- **One bill ≠ one account.** Consolidated billing combines payment; it does not merge permissions.

## Cost angle

This note is why task 4.1 appears next to 1.1.

- Consolidated billing pools usage across accounts: tiered discounts arrive sooner.
- Savings Plans and Reserved Instance commitments can be shared, so none is wasted.
- Guardrail SCPs (deny unapproved Regions, deny large instance types in dev) stop cost at the source.
- Separate accounts make cost allocation clear; add budgets per account.
- Control Tower and Organizations are free to use, but Control Tower turns on services such as Config and CloudTrail that have their own charges.
- RAM sharing a NAT-fronted network account saves paying for NAT in every account.

## Comparison

| Service | What it does | Grants permissions? | Cost | Pick it when |
|---|---|---|---|---|
| Organizations | Groups accounts; SCPs, RCPs, billing | No (limits only) | Free | You need account structure and guardrails |
| Control Tower | Landing zone, Account Factory, controls | No | Free itself; pays for Config, CloudTrail | You want a secure baseline with least effort |
| RAM | Shares resources across accounts | Yes, to use the shared resource | Free | Many accounts need the same subnet or gateway |
| Resource policy + `aws:PrincipalOrgID` | Shares data services org-wide | Yes | Free | Bucket, key or queue shared with the whole organization |
| IAM Identity Center | One sign-in across accounts | Yes (permission sets) | Free | Staff access to many accounts |

Now do drill 09 for the billing maths, then drill 04 again with an SCP chain in mind.

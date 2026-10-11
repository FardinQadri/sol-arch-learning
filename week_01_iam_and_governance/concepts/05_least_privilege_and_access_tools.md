Exam tasks: 1.1, 1.2

# 05 — Least privilege and the access tools

## What it is

**Least privilege** means giving an identity exactly the permissions it needs, no
more, and only for as long as it needs them. It runs through the exam guide's
security knowledge lists.

Nobody writes a perfect policy on the first try. So the practice is a loop:
**start narrow, watch what is denied, grow from evidence, remove what is
never used.** AWS gives you tools for each step of the loop.

## How it works

### Writing narrow policies

Start from the job, not from `*`:

1. List the exact API calls the workload makes (read the code, or use
   Access Analyzer policy generation below).
2. Name the exact resources by ARN, not `Resource: "*"`.
3. Add conditions that fit the job: MFA, Region, source VPC endpoint, tags.
4. Split roles by job. One role for the web app, another for the batch job.
5. Test with the policy simulator. Then deploy.

Smells in review: `Action: "*"`, `Resource: "*"` on write actions,
`iam:*` or `iam:PassRole` on `*`, `NotAction` with `Allow`, a wildcard
`Principal` with no condition, an AWS managed `*FullAccess` policy on an app role.

Some actions truly do not support resource-level restrictions (many `List*` and
`Describe*` calls). A `Resource: "*"` there is fine, ideally with a condition.

### The tools

**IAM Access Analyzer** — a family of checks:

- *External access findings* — finds resources shared outside your zone of trust
  (your account or organization): S3 buckets, KMS keys, IAM roles, SQS queues,
  and more. The first check to run before an audit.
- *Unused access findings* — finds unused roles, unused access keys, unused
  passwords and unused permissions. Remove them.
- *Policy validation* — checks a policy for syntax errors, security warnings and
  best-practice suggestions as you write it.
- *Custom policy checks* — assert in CI that a new policy does not grant more
  than before (or specific forbidden actions). Charged per check — check pricing.
- *Policy generation* — reads CloudTrail history for a role over a period and
  writes a policy with only the actions it really used. Drill 06 builds the idea
  yourself: count what was used, write what was needed.

**IAM policy simulator** — answers "would this identity be allowed to do X on
Y?" without making the call. Use it to test a new policy, or to see which
statement caused a denial. It does not change anything.

**Last accessed information** — for each user, role or policy: which services
(and, for some, which actions) were last used and when. Anything not used for a
long time is a candidate for removal.

**IAM credential report** — a CSV of every user in the account: password age,
MFA on or off, access key age and last use. The audit answer to "find users
without MFA" or "find old access keys".

**AWS CloudTrail** — records the API calls. It is the evidence behind policy
generation and every investigation.

### MFA and passwords

- **Virtual MFA** — an authenticator app. Cheap, widely used.
- **Hardware MFA** — a physical token. Stronger; use for root and admins.
- **Passkeys / FIDO2 security keys** — phishing-resistant. Recommended wherever
  supported, especially for root.

Enforce MFA in a policy with `aws:MultiFactorAuthPresent`: allow sensitive
actions only when it is `true`, or deny when it is `false` (watch the
missing-key trap in note 02). Require it in a role's trust policy for sensitive
roles.

The **account password policy** sets minimum length, character types, expiry and
reuse for IAM users. With Identity Center and federation you rarely need it: your
identity provider owns passwords.

### Permissions-boundary delegation

Problem: you want developers to create their own roles for their apps, but not
roles more powerful than themselves. If developers can create any role and attach
any policy, they can create an admin role.

Solution:

1. Write a **permissions boundary** policy: the maximum any developer-made
   role may have (for example, only their team's services).
2. Give the developer's permissions a condition: `iam:CreateRole` and
   `iam:PutRolePolicy` or `iam:AttachRolePolicy` are allowed **only if**
   the request carries `iam:PermissionsBoundary` equal to that boundary's ARN.
3. Deny `iam:DeleteRolePermissionsBoundary` so they cannot remove it.

Now every role they make is capped, whatever policies they attach. This is the
pattern behind the **deployer role** in milestone M01: the pipeline may create
roles, but only under the boundary.

### Tags and ABAC

**Role-based access control (RBAC)** gives each role its own policy.
**Attribute-based access control (ABAC)** uses tags so one policy scales:

```json
"Condition": {"StringEquals": {"aws:ResourceTag/project": "${aws:PrincipalTag/project}"}}
```

Reading: "you may touch a resource when its `project` tag equals your `project`
tag". New projects need new tags, not new policies. Control who may change tags
(`aws:TagKeys`, `aws:RequestTag/...`), or users could tag themselves into access.

### "Least privilege" vs "least operational overhead"

Exam wording matters:

- *"Grant only the required permissions"* → narrow custom policy; generate from
  CloudTrail; add a boundary.
- *"With the least operational overhead"* → an AWS managed policy, a group, an
  Identity Center permission set, Control Tower or ABAC. Not a hand-written
  policy per user.

If both appear, satisfy the hard security word first (least privilege), then pick
the lowest-effort way to do it (a customer managed policy generated by Access
Analyzer beats hand-editing every policy).

## Numbers to know

| Fact | Value |
|---|---|
| Access Analyzer external-access findings | free for account analyzers |
| Policy simulator, credential report, last accessed | free |
| Root access keys to create | 0 |
| Policy language version | `2012-10-17` |
| Secure domain weight | 30 % |

Prices for Access Analyzer's unused-access analyzer are not in `docs/facts.md`;
check the pricing page before turning it on.

## When to choose it

| Task | Tool |
|---|---|
| "Which of our resources are shared with outsiders?" | Access Analyzer external access |
| "Which roles and keys are unused?" | Access Analyzer unused access, last accessed |
| "Write a policy from what the app really did" | Access Analyzer policy generation |
| "Is this policy valid and safe?" | Policy validation / custom checks |
| "Would user X be allowed to do Y?" | Policy simulator |
| "Who has no MFA? Whose keys are old?" | Credential report |
| "Let developers create roles safely" | Permissions boundary + condition on create |
| "One policy for many teams" | ABAC with tags |
| "Force MFA for dangerous actions" | `aws:MultiFactorAuthPresent` condition |

## Exam traps

- **Access Analyzer finds external access; the simulator tests a policy.** They answer different questions.
- **Policy generation needs CloudTrail** to be on. No trail, no history, no generated policy.
- **A boundary does not grant.** Delegation also needs the developer's own permissions.
- **Delegation needs the condition.** Without `iam:PermissionsBoundary`, the developer can create an unbounded role.
- **`*FullAccess` on an app role** is the usual wrong answer to "least privilege".
- **Credential report** is account-wide and CSV. It is not Access Analyzer.
- **ABAC needs tag control.** If users can edit their own tags, ABAC is bypassed.
- **MFA on root** is the standard answer to "secure the root user" — plus no access keys.
- **Reading the question.** "Least operational overhead" does not mean "broadest permissions".

## Cost angle

The access tools above are mostly free; check pricing for the unused-access
analyzer. Least privilege is a cost control in itself: an app that cannot launch
instances cannot launch a thousand of them after a leak. Removing unused
roles and keys reduces both risk and the number of things to audit. ABAC saves
engineering time (fewer policies to write and review).

## Comparison

| Tool | Answers | Input | Output | Free? |
|---|---|---|---|---|
| Access Analyzer: external access | What is shared outside our org? | Resource policies | Findings | Yes for account analyzers |
| Access Analyzer: unused access | What is never used? | Access activity | Findings | Check pricing |
| Access Analyzer: policy generation | What did this role actually use? | CloudTrail history | A draft policy | Yes |
| Access Analyzer: policy validation | Is this policy valid and safe? | A policy document | Warnings, errors | Yes |
| Access Analyzer: custom policy checks | Does this policy grant more than before? | Two policy documents | Pass / fail | Check pricing |
| Policy simulator | Would this call be allowed? | Identity + action + resource | Allowed / denied, with the deciding policy | Yes |
| Last accessed information | When was this last used? | Usage data | Service / action timestamps | Yes |
| Credential report | Who has MFA and old keys? | All users | CSV | Yes |
| CloudTrail | What happened? | API activity | Event log | Check pricing |

Now do drills 05 and 06, then start milestone M01.

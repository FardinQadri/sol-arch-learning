Exam tasks: 1.1

# 02 — How AWS decides: policy evaluation

## What it is

Every request to AWS is checked against every policy that applies. The result is
one of three outcomes:

- **Explicit deny** — a `Deny` statement matched. The request fails. Nothing overrides it.
- **Allow** — no explicit deny, and the right policies allowed it.
- **Implicit deny** — nothing allowed it. The request fails. This is the default.

The rule to burn in: **everything is denied unless allowed, and an explicit deny
beats every allow.**

This is the most tested idea in the Secure domain. Drills 03 and 04 make you
build the evaluator yourself.

## How it works

### The flow

For a request inside one account:

1. **Explicit deny anywhere?** Look at every policy: SCPs, resource policy,
   identity policies, boundary, session policy. Any matching `Deny` ends it.
2. **SCPs** (if the account is in an organization). They must allow the action.
   No allow in the SCP chain means implicit deny.
3. **Resource-based policy.** An allow here can be enough on its own (see the
   corner case below).
4. **Identity-based policies.** They must allow the action.
5. **Permissions boundary** (if set). It must allow the action too.
6. **Session policy** (if the session has one). It must allow the action too.
7. If nothing denied and the needed allows are present: **Allow**. Otherwise implicit deny.

```text
request
  |
  v
any matching Deny (any policy)? --yes--> EXPLICIT DENY
  | no
  v
SCP chain allows?        --no---> implicit deny
  | yes
  v
resource policy allows?  --yes--> (same account: ALLOW, see corner case)
  | no
  v
identity policy allows?  --no---> implicit deny
  | yes
  v
boundary allows (if set)?   --no--> implicit deny
  | yes
  v
session policy allows (if set)? --no--> implicit deny
  | yes
  v
ALLOW
```

How to read it in a scenario question: find the **Deny** first. Then check each
layer that exists asks "allow?". A layer that does not exist (no boundary, no
session policy) is skipped. An SCP chain must allow at **every level** from the
organization root down to the account: root, each OU, then the account.

### Cross-account: both sides must allow

When the caller is in account A and the resource is in account B, two doors
exist, and both must open:

- Account A's side: the caller's identity policy allows the action (and A's
  boundary and SCPs do not block it).
- Account B's side: the resource policy names the caller (or the caller's
  account) and allows the action.

Either side missing means implicit deny. Demo case 5 below shows it.

The fix for the caller's side is easy to forget on the exam: the *other* account
granted access, but the caller's own role still needs an `Allow`.

Alternative: the caller **assumes a role in account B**. Then the caller is in
account B for the request, and only account B's policies for that role matter.

### The corner the drills ignore

Inside one account, a resource-based policy that names an **IAM user** (or a
role's assumed-role session) directly can allow access even if the user's
identity policies do not. And a permissions boundary does **not** cut that
grant, because the boundary only limits what the identity policies can give.

Example: a queue policy names user `ana` with `sqs:SendMessage`. Ana has no
identity policy at all and a boundary that allows only `s3:*`. She can still
send to that queue. An explicit deny still beats it, and SCPs still apply.

Limits on this corner (same-account policies only):

- A resource policy that names a **role ARN** grants access with no identity-policy
  allow. But a permissions boundary or session policy **can** still limit it.
- A resource policy that names an **IAM user ARN** or an assumed-role **session
  ARN** is not limited by an implicit deny in a boundary or session policy.
- An explicit deny and SCPs always apply, in every case.

### Conditions

A `Condition` block adds tests. Shape:

```json
"Condition": {"OperatorName": {"condition-key": "value or [values]"}}
```

Operators:

| Operator family | Examples | Notes |
|---|---|---|
| String | `StringEquals`, `StringLike` (wildcards), `StringNotEquals` | Case-sensitive. `StringEqualsIgnoreCase` exists. |
| Numeric / Date | `NumericLessThan`, `DateGreaterThan` | |
| Bool | `Bool` | Value is the string `"true"` or `"false"`. |
| IP | `IpAddress`, `NotIpAddress` | CIDR ranges. |
| ARN | `ArnLike`, `ArnEquals` | |
| Null | `Null` | `"true"` means the key is absent. |

Rules for several tests:

- Several **keys** in one block: all must match (AND).
- Several **values** for one key: any may match (OR).
- A key that is **missing** from the request makes a positive test false. That
  is why negative operators (`StringNotEquals`) on a missing key match, and a
  `Deny` built on them can fire by surprise.

**`IfExists`** — add it to an operator (`StringEqualsIfExists`) to make a
missing key count as a match. Use it when the key is not always present.

**Set operators** for multivalued keys such as tag lists:

- `ForAnyValue:` at least one request value must match.
- `ForAllValues:` every request value must match.

The empty-set trap: if the request has **no values** for the key,
`ForAllValues` is **true** (nothing broke the rule) and `ForAnyValue` is
**false**. So `Allow ... ForAllValues:StringEquals` quietly allows a request that
sends no values at all. Pair it with a `Null` check to require the key.

### Common condition keys

| Key | Use |
|---|---|
| `aws:SourceIp` | Caller's public IP. Not useful from inside a VPC or through a VPC endpoint. |
| `aws:SecureTransport` | `false` when the request used plain HTTP. Deny it to force TLS. |
| `aws:MultiFactorAuthPresent` | `true` if the session used MFA. Missing for long-lived keys. |
| `aws:RequestedRegion` | The Region the call targets. Basis of Region guardrails. |
| `aws:PrincipalOrgID` | The caller's organization ID. "Anyone in our organization." |
| `aws:SourceVpce` / `aws:SourceVpc` | Came through that VPC endpoint or VPC. |
| `aws:PrincipalTag/<key>` | A tag on the caller. The "who" side of ABAC (note 05). |
| `aws:ResourceTag/<key>` | A tag on the resource. The "what" side of ABAC. |
| `aws:PrincipalArn` | The caller's ARN. |
| `aws:CalledVia` / `aws:ViaAWSService` | The call was made by an AWS service on your behalf. |

### Worked examples

`concepts/demo_policy_decisions.py` runs five requests through the course
evaluator. Run it and read the output.

| # | Request | Policies | Result | Why |
|---|---|---|---|---|
| 1 | `GetObject` on a log object | Identity: read logs | Allow | Allowed, nothing denies |
| 2 | `DeleteObject` on a log object | Identity: read logs | Implicit deny | No statement allows it |
| 3 | `GetObject` with Region `us-east-1` | Identity: read logs. SCP: allow all, deny non-EU Regions | Explicit deny | The SCP's Deny matched |
| 4 | `GetObject` from outside the VPC endpoint | Identity: read logs. Bucket policy denies requests not via `vpce-0abc` | Explicit deny | The resource policy's Deny matched |
| 5 | `GetObject` by a role from account B | Identity (B): read logs. No bucket policy in A | Implicit deny | Account A's side never allowed it |

Case 3 shows a common SCP pattern: `Deny` + `NotAction` + a Region condition.
The `NotAction` keeps global services (IAM, STS) working. Case 4 is the standard
"data only reachable from our VPC" pattern.

Mini-exercise: in case 1, what if the SCP chain contained only the EU-only Deny
and no `Allow`? Answer: implicit deny. An SCP chain needs an allow too; AWS
attaches `FullAWSAccess` by default so this normally works. Remove it and
everything stops.

## Numbers to know

| Fact | Value |
|---|---|
| Evaluation outcomes | 3: explicit deny, allow, implicit deny |
| Layers that only limit | SCP, RCP, boundary, session policy |
| Layers that can grant | identity policy, resource policy |
| Cross-account | 2 sides must allow (caller's identity + resource policy) |
| Policy language version | `2012-10-17` |

There are no quotas to memorise in this note.

## When to choose it

Use this note when a question gives you several policies and asks for the
outcome, or asks which **one change** fixes a denial. Work in this order:

1. Find any `Deny` that matches. If found, the answer is deny.
2. Is the caller in another account? Check both sides.
3. Is there an SCP, boundary or session policy? Each must allow.
4. Is there an identity or resource allow? If not, implicit deny.

To fix a denial, change the layer that is actually blocking. Adding an allow to
the identity policy does nothing against an SCP deny.

## Exam traps

- **Deny always wins.** An `Allow *` on the identity policy loses to any matching `Deny`.
- **Limits are intersections, not unions.** Identity allow ∩ boundary ∩ session.
- **SCPs do not grant.** An SCP allowing `s3:*` gives nobody S3 access.
- **Cross-account needs both sides** (identity policy and resource policy), unless the caller assumes a role in the target account.
- **Missing key + negative operator.** `StringNotEquals` on an absent key matches. A `Deny` built on it can block calls that never carried the key.
- **`ForAllValues` on an empty set is true.** Add a `Null` test.
- **`aws:SourceIp` with VPC endpoints.** The caller's IP is private there. Use `aws:SourceVpce`.
- **Bool values.** Write them as the strings `"true"`/`"false"`, as the AWS docs do.
- **Resource policy for a same-account user** can bypass the boundary (corner case above).
- **Explicit deny in a resource policy** also stops callers that identity policy allows.

## Cost angle

Policy evaluation is free and adds no latency you can measure. The cost link is
indirect: Region-guardrail SCPs and tag conditions stop expensive resources
from appearing in Regions or accounts nobody watches. A `Deny` on
`aws:RequestedRegion` is one of the cheapest cost controls available.

## Comparison

| Layer | Needs an Allow? | Can Deny? | Missing means | Applies to |
|---|---|---|---|---|
| SCP chain | Yes, at every level | Yes | Implicit deny | Member accounts' principals |
| Resource policy | Only for cross-account (or as an alternative grant in-account) | Yes | Skipped in-account | The resource |
| Identity policy | Yes (unless a same-account resource policy grants) | Yes | Implicit deny | The caller |
| Permissions boundary | Yes, if set | Yes | Skipped if unset | One user or role |
| Session policy | Yes, if set | Yes | Skipped if unset | One session |

Now do drills 03 and 04, then run the demo again after drill 10.

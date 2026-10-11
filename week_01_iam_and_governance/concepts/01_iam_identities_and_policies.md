Exam tasks: 1.1

# 01 — IAM identities and policy types

## What it is

AWS Identity and Access Management (IAM) answers two questions for every API
call: **who are you?** (authentication) and **may you do this?**
(authorization). IAM is global. One IAM setup covers every Region of an account.
IAM itself costs nothing.

You will use IAM in every domain. A large share of the Secure domain (30 % of
the exam, see `docs/facts.md`) is IAM in disguise.

### The identities

- **Root user** — the e-mail address that created the account. IAM policies and
  boundaries cannot limit it. (SCPs can limit the root user of a member account,
  but never of the management account — note 04.) Treat it as a break-glass tool.
- **IAM user** — a named identity with a long-lived password and/or access keys.
- **IAM group** — a bag of users. You attach policies to the group. A group is
  not an identity: it cannot sign in and it cannot be named as a `Principal`.
- **IAM role** — an identity with no password and no keys. Someone (a person, a
  service, another account) **assumes** it and receives short-lived credentials.
- **Federated identity** — a person or app that signed in somewhere else
  (your company directory, Google, GitHub) and is mapped to a role.

### What only root can do

Day-to-day work never needs root. A short list does, for example:

- change the account name, e-mail address or root password;
- close the account;
- change or cancel the AWS Support plan;
- fix an S3 bucket policy that denies everyone, admins included;
- restore IAM permissions when no IAM admin is left.

Exam habit: "a task that **requires** root" is a valid reason to use root. "It
is easier" is never one.

Lock root away:

1. Turn on MFA for root (a hardware key or passkey is best).
2. Create no access keys for root. Delete any that exist.
3. Keep a long random password in a vault; use a shared mailbox for the e-mail.
4. Sign in as root only for a root-only task. Alarm on every root sign-in.

## How it works

### Why roles and federation beat long-lived users

A user's access key is a password that never expires. It leaks into Git
history, laptops, CI logs and chat. A leaked key works from anywhere until
someone notices.

Roles fix this:

- credentials are **temporary** and rotate on their own (see note 03);
- there is nothing to store: EC2, Lambda and ECS receive them from the platform;
- people sign in through one central identity provider, so leaving the company
  removes access in one place;
- every use is logged with the session name in CloudTrail.

So the exam answer to "an app on EC2 needs to read S3" is **an instance profile
with a role**, never an access key in a config file. The answer to "our
engineers need console access" is **federation / IAM Identity Center**, not
one IAM user each.

Use IAM users only when you must: a legacy tool that cannot assume roles, or a
break-glass account. Even then, prefer a role.

### The policy types

A policy is a JSON document that says who may do what. IAM has several types.
They differ in **who attaches them** and whether they **grant** or only **limit**.

**Identity-based policies** attach to a user, group or role.

- *AWS managed* — written and updated by AWS (`AdministratorAccess`,
  `ReadOnlyAccess`). Handy, but broad.
- *Customer managed* — you write it once, attach it to many identities, and it
  has versions. Best for reuse.
- *Inline* — embedded in one identity and deleted with it. Use for a strict
  one-to-one link.

**Resource-based policies** attach to a resource: S3 bucket policy, KMS key
policy, SQS queue policy, SNS topic policy, Lambda function policy, Secrets
Manager secret policy, and a role's trust policy. They contain a `Principal`.
They can grant access to a principal in **another account** directly.

**Permissions boundary** — a limit on a user or role. It never grants. The
identity can do only what its identity policies allow **and** the boundary
allows. Its job is safe delegation (note 05).

**Service control policy (SCP)** — a limit on a whole account or OU in AWS
Organizations. It never grants. Note 04.

**Resource control policy (RCP)** — the mirror image of an SCP: an Organizations
limit on what can be done **to resources** in member accounts, whoever the caller
is. Use it to enforce "no resource in our accounts is shared outside the
organization". It never grants.

**Session policy** — passed when you assume a role or federate. It narrows that
one session below the role's own permissions. It never grants.

**Access control list (ACL)** — the legacy S3 way of granting access per object
or bucket. New buckets have ACLs **disabled** (Bucket owner enforced) since
2023-04, per `docs/facts.md`. Keep them off and use policies.

### Policy JSON anatomy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadReports",
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::acme-reports/*",
      "Condition": {"Bool": {"aws:SecureTransport": "true"}}
    }
  ]
}
```

| Element | Meaning |
|---|---|
| `Version` | Policy language version. Always `2012-10-17`. The older `2008-10-17` lacks policy variables. |
| `Statement` | One or more rules. A request is checked against all of them. |
| `Sid` | Optional label for humans. |
| `Effect` | `Allow` or `Deny`. Nothing else. |
| `Action` | The API operations, as `service:Operation`. Wildcards allowed: `s3:Get*`. |
| `NotAction` | Everything **except** these actions. With `Allow` it is very broad. Used mostly with `Deny`. |
| `Resource` | The ARNs the statement applies to. Wildcards allowed. |
| `NotResource` | Everything except these ARNs. |
| `Principal` | Who. **Only** in resource-based and trust policies. Never in an identity policy. |
| `Condition` | Extra tests that must be true (note 02). |

Two details that cost marks:

- Identity policies have no `Principal`: the principal is whoever the policy is attached to.
- Resource-based policies must name a `Principal`. `"Principal": "*"` means
  everyone, including anonymous callers.

### ARNs

An Amazon Resource Name is the full address of a resource:

```
arn:partition:service:region:account-id:resource
arn:aws:s3:::acme-reports/2026/q3.csv              (S3: no Region, no account)
arn:aws:iam::111122223333:role/analyst             (IAM: no Region)
arn:aws:sqs:eu-west-1:111122223333:orders          (SQS: all parts)
```

S3 needs two ARNs: the bucket (`arn:aws:s3:::acme-reports`) for bucket actions
such as `s3:ListBucket`, and the objects (`arn:aws:s3:::acme-reports/*`) for
object actions such as `s3:GetObject`. Mixing them up is a classic bug. You
practised ARN parsing in week 00 (drill 01); drill 01 here adds wildcard matching.

## Numbers to know

IAM questions are about rules, not quotas. The facts worth keeping:

| Fact | Value |
|---|---|
| Policy language version | `2012-10-17` |
| IAM scope and price | global; free |
| ACLs on new S3 buckets | disabled (Bucket owner enforced) from 2023-04 |
| Block Public Access on new S3 buckets | on, from 2023-04 |
| Every new S3 object | encrypted with SSE-S3 since 2023-01-05 |
| Secure domain weight | 30 % |

IAM has hard quotas (policies per user, policy size, and so on). The exam does
not test exact values, so this course does not teach them.

## When to choose it

| Need | Pick |
|---|---|
| A person needs the console or CLI | Federation / IAM Identity Center (note 03) |
| An app on AWS needs AWS access | A role (instance profile, task role, execution role) |
| An outside system needs AWS access | A role it assumes, or OIDC federation |
| Reuse one permission set on many identities | Customer managed policy |
| Tie a permission to exactly one identity | Inline policy |
| Share a bucket, key or queue with another account | Resource-based policy (plus the other side's identity policy) |
| Stop admins creating over-powerful roles | Permissions boundary |
| Stop a whole account doing something | SCP (or RCP for resources) |
| Make one session weaker than its role | Session policy |

## Exam traps

- **"Group" as a principal.** Groups cannot be a `Principal`. Name the users or roles.
- **Boundaries, SCPs, RCPs and session policies grant nothing.** If the identity
  policy does not allow the action, no limit will fix that.
- **`Allow` + `NotAction`** is not "deny the rest". It allows everything else.
- **Root keys.** Any answer that creates or uses root access keys is wrong.
- **Access keys on EC2.** Wrong whenever a role is possible.
- **Bucket vs object ARN.** `s3:ListBucket` needs the bucket ARN; `s3:GetObject` the `/*` ARN.
- **ACLs.** If an answer enables ACLs to "fix" a permission problem, look for a
  bucket policy instead. ACLs are legacy.
- **Inline vs managed.** "Reuse across many roles" means customer managed. Inline cannot be shared.
- **Wildcard `Principal` with no condition** on a resource policy makes it public.

## Cost angle

IAM, STS and the policy types above are free. The cost of IAM is a bad design,
not a bill: a leaked long-lived key can run up a large compute bill within
hours. Roles with temporary credentials are the cheapest control you can buy.
Access to billing data is also controlled by IAM: only the right role should
see Cost Explorer and Budgets.

## Comparison

| Policy type | Attached to | Grants? | Limits? | Has `Principal`? | Typical use |
|---|---|---|---|---|---|
| Identity-based (managed or inline) | User, group, role | Yes | Yes (via Deny) | No | "What can this identity do?" |
| Resource-based | A resource | Yes, incl. cross-account | Yes (via Deny) | Yes | Bucket, key, queue, topic sharing |
| Permissions boundary | One user or role | No | Yes | No | Safe delegation to developers |
| SCP | Org root, OU or account | No | Yes | No | Guardrails across accounts |
| RCP | Org root, OU or account | No | Yes (on resources) | No | Data perimeter on resources |
| Session policy | One role session | No | Yes | No | Narrow a shared role per user |
| ACL (legacy) | S3 bucket or object | Yes | No | Grantee | Avoid; disabled on new buckets |

Now do drill 01, then drills 02–04.

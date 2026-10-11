Exam tasks: 1.1, 1.2

# 03 — Roles, STS and federation

## What it is

A **role** is an identity that anyone you trust can *assume*. It has no
password and no keys. Assuming it gives the caller **temporary credentials**
from the AWS Security Token Service (STS).

A role is made of two policies:

- the **trust policy** (a resource-based policy on the role): *who may assume me?*
- the **permissions policies** (identity-based): *what can I do once assumed?*

Most "secure access" questions end in one sentence: *use a role.* This note
shows which kind of role, and how people and systems get to it.

## How it works

### STS and temporary credentials

`sts:AssumeRole` checks the trust policy, then returns three values: an access
key ID, a secret key and a **session token**. They expire. The session length
is set on the role (with a maximum) and can be shortened per call. When they
expire, the caller assumes the role again.

Why that matters:

- a stolen temporary credential stops working on its own;
- nothing long-lived sits on disk;
- the role is the unit you manage: change the policy once and every session follows.

`aws sts get-caller-identity` shows who you are. For a role session the ARN looks like
`arn:aws:sts::111122223333:assumed-role/analyst/bob`: account, role name,
**session name**. You set the session name (`RoleSessionName`) when you assume.
CloudTrail records it, so a shared role still tells you *who* acted. Make
people use a meaningful name (for example their e-mail) and require it in the
trust policy if you need to.

Other STS calls to know: `AssumeRoleWithSAML` and `AssumeRoleWithWebIdentity`
(federation, below), `GetSessionToken` (temporary credentials for a user, used
to add MFA to a CLI session), `GetCallerIdentity`.

A trust policy example (account `111122223333` may assume, only with MFA):

```json
{"Effect": "Allow",
 "Principal": {"AWS": "arn:aws:iam::111122223333:root"},
 "Action": "sts:AssumeRole",
 "Condition": {"Bool": {"aws:MultiFactorAuthPresent": "true"}}}
```

`...:root` here means "any principal in that account whose own identity policy
allows `sts:AssumeRole`" — it is not the root user.

### Roles for AWS services

- **EC2 instance profile** — a container that carries one role to an instance.
  The console creates it for you; the CLI makes you create it. Code on the
  instance gets credentials from the instance metadata service (use IMDSv2).
  The SDK finds them without any configuration.
- **Service role** — a role an AWS service assumes to act for you (Lambda
  execution role, ECS task role, CloudFormation role, Glue role). Its trust
  policy names the service: `"Principal": {"Service": "lambda.amazonaws.com"}`.
- **Service-linked role** — predefined by a service, created by it, cannot be
  edited by you.

**`iam:PassRole`** — to hand a role to a service (start an EC2 instance with a
role, create a Lambda function with an execution role), the caller needs
`iam:PassRole` on that role. Without it, anyone who can create a function could
attach an admin role and become admin. Tighten it:

- `Resource`: list only the role ARNs the caller may pass;
- condition `iam:PassedToService` = `lambda.amazonaws.com` (or whichever service).

Exam habit: "a developer can launch instances but not escalate privileges" =
`ec2:RunInstances` plus a narrow `iam:PassRole`.

### Cross-account roles and the confused deputy

To let account B's people or apps work in account A: create a role in A that
trusts B. B's identities need `sts:AssumeRole` on it. The role's policies decide
what they can do. This is the usual alternative to resource policies when
access spans many services.

**The confused-deputy problem.** You hire a SaaS vendor and give it a role in
your account. The vendor serves many customers. A different customer could
trick the vendor into using *their own request* with *your* role ARN. The vendor
is the "deputy" that was confused about whom it works for.

The fix is an **external ID**: a secret value you and the vendor agree on. Your
trust policy requires `sts:ExternalId` to equal it. The vendor sends the
customer-specific ID on each assume call, so another customer cannot use your
role. Use it for any third party, not for your own accounts.

For AWS services acting on your resources (SNS delivering to S3, for example),
the equivalent guard is the `aws:SourceArn` / `aws:SourceAccount` condition.

### Federation

Federation means *trust someone else's sign-in* instead of creating IAM users.

**SAML 2.0.** Your company identity provider (Entra ID, Okta, AD FS) signs an
assertion. The user is sent to AWS, which exchanges the assertion for role
credentials (`AssumeRoleWithSAML`). Used for workforce single sign-on, but
largely replaced by IAM Identity Center for new setups.

**OIDC / web identity.** A token from an OpenID Connect provider (Google,
GitHub Actions, a Kubernetes cluster) is exchanged for role credentials
(`AssumeRoleWithWebIdentity`). You create an IAM OIDC provider and a role whose
trust policy checks the token's claims. Example: GitHub Actions deploys to AWS
with **no stored keys** — the trust policy allows only your repo and branch
(`token.actions.githubusercontent.com:sub`). This is the modern answer to
"CI needs to deploy to AWS".

**IAM Identity Center** (the new name of AWS SSO; renamed per `docs/facts.md`).
The recommended way to sign in your **workforce**:

- connect it to your own directory (Active Directory, Okta, Entra ID) or use
  its built-in directory;
- create **permission sets** (a bundle of policies) and **assign** a user or
  group + a permission set to one or more accounts;
- Identity Center creates a role in each assigned account and gives users a
  portal with short-lived credentials for the console and CLI (`aws configure sso`);
- works across an organization, so it is the single sign-in for many accounts.

If the question says "many accounts", "workforce", "single place to manage access"
or "least operational overhead", the answer is IAM Identity Center.

**Amazon Cognito** — for your **application's** customers, not your staff.
*User pools* sign users in and hand your app tokens. *Identity pools* swap those
tokens (or social/SAML logins) for AWS credentials. Week 08 covers it; for now
remember: customers → Cognito, employees → Identity Center.

**AWS Directory Service** — for "use our existing Active Directory" scenarios:

- *AWS Managed Microsoft AD* — a real Microsoft AD run by AWS. Pick it when
  workloads (EC2 Windows, RDS for SQL Server, FSx) need a domain, or you want a
  trust with on-premises AD.
- *AD Connector* — a proxy to your on-premises AD. No directory is stored in AWS.
  Pick it when you only want to forward sign-in requests.
- *Simple AD* — a small, basic directory; in maintenance and closed to new customers since 2026-06-30, so choose AWS Managed Microsoft AD for new directories.

To let AD users into AWS accounts: connect the directory to IAM Identity Center.

## Numbers to know

| Fact | Value |
|---|---|
| Credentials from `AssumeRole` | access key ID + secret key + session token, all temporary |
| Service in trust policy | `lambda.amazonaws.com`, `ec2.amazonaws.com`, ... |
| Renames | AWS SSO → IAM Identity Center |
| IMDSv2 | account default settable from 2024-03; Amazon Linux 2023 disables IMDSv1 |

Session length limits and role-chaining limits are in the AWS docs. They are not
in `docs/facts.md`, so this course does not teach exact values.

## When to choose it

| Scenario | Answer |
|---|---|
| App on EC2 reads S3 | Instance profile + role |
| Lambda writes to DynamoDB | Execution role |
| Staff sign in to many accounts | IAM Identity Center |
| Staff use the company's SAML provider for one account | SAML federation (or Identity Center) |
| CI pipeline (GitHub Actions) deploys | OIDC federation to a role, no keys |
| Mobile app users upload photos | Cognito (identity pool for AWS credentials) |
| Third-party vendor reads your data | Role with an external ID |
| Account B needs to use account A's resources | Cross-account role, or a resource policy |
| Windows workloads need a domain | AWS Managed Microsoft AD |
| Keep AD on premises, sign in to AWS with it | AD Connector, or Identity Center + the directory |
| Stop a developer attaching an admin role to a function | Narrow `iam:PassRole` |

## Exam traps

- **Keys in code, config files or AMIs.** Wrong. The answer is a role.
- **Role ARN vs instance profile.** The instance carries a profile; the profile carries a role. The console hides this.
- **Trust policy ≠ permissions policy.** Failing to *assume* is a trust problem. Failing to *do* is a permissions problem.
- **Both sides for cross-account assume.** The trust policy must name the caller, and the caller needs `sts:AssumeRole` on it.
- **External ID is for third parties.** It does not protect against your own accounts' users.
- **Cognito vs Identity Center.** App customers vs staff. A classic swap.
- **AD Connector vs Managed AD.** Proxy to on-prem vs a real directory in AWS.
- **`iam:PassRole` is not a role permission.** The caller needs it, not the role being passed.
- **Root ARN in a principal** means the account, not the root user.

## Cost angle

IAM roles, STS and IAM Identity Center are free. Cognito and Directory Service
are paid services with their own price lists (`docs/facts.md` has no figures for
them, so check the pricing pages before you build). The money roles save is
operational: no key rotation, no leak response. Directory Service bills for as
long as the directory exists, so a forgotten directory is a lab cost. Delete one
after practising.

## Comparison

| Option | Who signs in | Credentials | Best for |
|---|---|---|---|
| IAM user | A named person or tool | Long-lived password / keys | Legacy tools, break-glass only |
| IAM role (assumed) | Anyone trusted | Temporary (STS) | Services, cross-account, everything else |
| IAM Identity Center | Your workforce | Temporary, via a portal | Many accounts, central sign-in |
| SAML 2.0 federation | Workforce from your IdP | Temporary | One account, an existing SAML IdP |
| OIDC / web identity | Tokens from Google, GitHub, a cluster | Temporary | CI pipelines, Kubernetes workloads |
| Cognito | Your app's customers | Tokens (and AWS credentials via identity pools) | Customer sign-up and sign-in |
| AWS Managed Microsoft AD | Domain users and computers | Kerberos / AD | Windows workloads, trust to on-premises AD |
| AD Connector | On-prem AD users | Forwarded to on-prem AD | Reuse on-prem AD without storing data in AWS |

Now do drill 05, then the rest of this week's drills on roles and trust policies.

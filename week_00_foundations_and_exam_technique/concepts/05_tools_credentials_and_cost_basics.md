Exam tasks: 1.1, 4.4

# 05 — Tools, credentials and cost basics

## What it is

Four ways to talk to AWS, one way to prove who you are, and one way you get
billed. This note covers all three because you need them before any other week.

**Four ways to use AWS.** They all end in the same API calls.

| Tool | What it is | Best for |
|---|---|---|
| Management Console | the web interface | exploring, one-off tasks, learning |
| AWS CLI | a command-line program (`aws s3api ...`) | scripts, quick checks, automation in shells |
| SDK (boto3 for Python) | a library for your code | applications, tests, data jobs |
| CloudFormation | declarative templates (infrastructure as code) | repeatable, reviewable environments |

Clicking in the console cannot be reviewed, repeated or rolled back. For
anything you will build twice, use a template. That is the operational-excellence
pillar in practice.

## How it works

### Credentials: how boto3 finds out who you are

Every call is signed with credentials. The SDK looks in a fixed order and stops
at the first source that gives it something. Simplified, from first to last:

1. Credentials passed in code or arguments (avoid; they end up in source control).
2. Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`,
   optionally `AWS_SESSION_TOKEN`.
3. The profile from `~/.aws/config` and `~/.aws/credentials` (`AWS_PROFILE` picks
   it). A profile may hold static keys, an IAM Identity Center (SSO) session, or a
   role to assume.
4. A container role (the ECS task role).
5. The EC2 instance profile role, fetched through instance metadata.

Lambda puts its execution role's temporary credentials into environment
variables, so it is found at step 2.

This is simplified. For the exam, remember two things:

- **Anything you set explicitly beats what is further down the list.** Environment
  variables override the files. A stray `AWS_ACCESS_KEY_ID` in your shell can
  make you act as the wrong identity. That is why this course's drills set fake
  credentials themselves and never read yours.
- **The safest source is the last one: a role.** The credentials are temporary,
  rotate on their own, and are never written to disk by you.

### Why long-lived access keys are a risk

An IAM user's access key does not expire. Anyone who finds it can use it from
anywhere, until you notice and delete it. Keys leak through source control,
screenshots, logs, laptops and AMIs.

Better:

- On EC2, containers and Lambda: use a **role**. No key to leak.
- On a laptop: use **IAM Identity Center** and `aws configure sso`. It stores no
  permanent secret, only a short-lived session.
- For the root user: no access keys at all, ever. Protect it with MFA and use it
  rarely.

When you do `aws sts get-caller-identity`, a role-based identity shows an
`assumed-role` ARN. A long-lived key shows a `user` ARN. In week 01 you learn how
the assumed role works.

### `aws configure sso`

You run it once per profile. It asks for the Identity Center start URL and
Region, opens a browser to sign you in, lets you pick an account and a
permission set, and asks for a profile name. After that:

```
aws sso login --profile saa-lab
aws sts get-caller-identity --profile saa-lab
```

The session expires, and you log in again. That is the point.

### Region and the S3 `LocationConstraint` rule

Boto3 clients have a Region. For S3, creating a bucket has one quirk:

- In `us-east-1`, call `create_bucket` with **no** `CreateBucketConfiguration`.
  Giving `LocationConstraint: us-east-1` is an error (`InvalidLocationConstraint`).
- In any other Region, you **must** pass
  `CreateBucketConfiguration={"LocationConstraint": "<that Region>"}`. Leaving it
  out is an error (`IllegalLocationConstraintException`).
- Reading a bucket's location with `get_bucket_location` returns `None` for
  `us-east-1`, and the Region name for others.

The demo `concepts/demo_boto3_basics.py` shows these.

### Error codes you will meet

Boto3 raises `ClientError`. The code is in `exc.response["Error"]["Code"]`.

| Code | Usual meaning |
|---|---|
| `404` | from `head_bucket` / `head_object`: not found. These calls have no body, so the code is the bare status number |
| `NoSuchBucket` | a call that returns a body (such as list or get) found no such bucket. Often the wrong Region or a typo |
| `403` / `AccessDenied` | the bucket or object exists, but you are not allowed. Also seen when a bucket exists in another account |
| `BucketAlreadyExists` | the name is taken by someone else (names are global) |
| `BucketAlreadyOwnedByYou` | you already own a bucket with that name. Outside `us-east-1`, creating it again returns this error; in `us-east-1` the same call succeeds |
| `InvalidLocationConstraint` | you gave a LocationConstraint to `us-east-1` |
| `IllegalLocationConstraintException` | you left it out in another Region |

Read the code, not the English message. Handle the codes you expect and let
others raise.

A 403 where you expect a 404 is a common surprise: S3 may answer 403 for a missing
object when you lack list permission, to avoid revealing what exists.

### Pagination

List calls return a limited number of items per call. S3 `list_objects_v2`
returns at most 1,000 keys per page. If you have more, you get a continuation
token (`NextContinuationToken`; on the CLI `NextToken`) and must ask again.

Three habits:

- Use `client.get_paginator("list_objects_v2")` and loop over its pages. Do not
  hand-roll token passing.
- Never assume the first page is everything. A script that lists a bucket once
  silently misses the rest when the bucket grows.
- Page size is a request setting. The demo asks for 50 per page and gets 3 calls
  for 120 objects (50 + 50 + 20).

### Retries

AWS APIs throttle and sometimes fail transiently. The SDK retries for you.
Settings (in the client's config or `AWS_RETRY_MODE`):

- **standard** mode: a fixed number of attempts with exponential backoff.
- **adaptive** mode: standard, plus client-side rate limiting that slows down
  when it sees throttling.
- In botocore's `Config(retries={...})`, `max_attempts` counts **retries**, not the
  first call. `total_max_attempts` counts **every attempt including the first**.
  Example: `Config(retries={"max_attempts": 4})` means 5 attempts in total.
- In `~/.aws/config` and the `AWS_MAX_ATTEMPTS` variable, `max_attempts` means
  **total attempts**. Same name, different meaning: check where you set it.
- Drill 09 uses `total_max_attempts`.

**Exponential backoff with jitter** (a preview): wait a little after the first
failure, about twice as long after the second, and so on. Jitter adds a random
amount so many clients do not retry at the same moment. You meet this again with
SQS, Lambda and DynamoDB.

Retries only help with errors that may go away (throttling, timeouts, server
errors). Retrying `AccessDenied` or `NoSuchBucket` never helps.

### How AWS bills

The model is pay-as-you-go: you pay for what you use, when you use it, with
no up-front commitment. Discount models (Savings Plans, Reserved capacity,
Spot) come in later weeks.

A bill has three kinds of line:

1. **Compute and capacity** — time an instance runs, or requests and run time.
2. **Storage** — GB-months, plus requests.
3. **Data transfer** — often the surprise.

Data transfer rules of thumb:

| Direction | Charged? |
|---|---|
| Into AWS from the internet | free |
| Out of AWS to the internet | charged |
| Between AZs in one Region | charged, in both directions |
| Between Regions | charged |
| Within one AZ over private addresses | generally free |

### The public IPv4 charge

Since 2024-02-01, every public IPv4 address costs 0.005 USD per hour, **whether
in use or idle**. For a 30-day month: 0.005 × 24 × 30 = 3.60 USD per address.
Ten addresses are 36 USD a month. Release what you do not need, and prefer
private addressing and load balancers over giving every instance a public
address.

### Free plan and Paid plan (for the optional lab)

From `docs/facts.md`:

- New accounts choose a **Free plan** or a **Paid plan**. Both receive 100 USD in
  credits, plus up to 100 USD more for completing activities.
- The Free plan ends after 6 months or when the credits run out. The account
  then closes, with 90 days to upgrade before deletion.
- A Free-plan account is upgraded to Paid automatically if it joins AWS
  Organizations or sets up a Control Tower landing zone.
- Do not rely on the older "12-month free tier" (750 hours of a small instance).
  It applies only to older accounts.

### Why this course runs offline

Every drill, demo and test uses **moto**, a library that fakes AWS in memory.

- Nothing can bill you.
- Nothing can touch a real account, because the harness sets fake credentials
  and ignores yours.
- Tests run in about a second and can be repeated.

moto is a model, not the real thing. It does not run Lambda code and it skips
some resource types. The labs (optional) use a real account, with guard rails.

## Numbers to know

| Fact | Value |
|---|---|
| S3 list page size | 1,000 keys per call |
| Public IPv4 address | 0.005 USD per hour, in use or idle |
| One address, 30 days | 3.60 USD (0.005 × 24 × 30) |
| Plan credits | 100 USD, plus up to 100 USD for activities |
| Free plan length | 6 months or until credits run out |
| Upgrade window after Free plan ends | 90 days |
| S3 single PUT | up to 5 GB (multipart above that) |
| S3 max object size | 50 TB (changed 2025-12-02; was 5 TB) |

## When to choose it

| Situation | Choose |
|---|---|
| Exploring a new service | console |
| Quick one-off check or script | CLI |
| Application or data job in Python | boto3 |
| Same environment, many times | CloudFormation |
| Code running on AWS | a role, never a key |
| Developer laptop | IAM Identity Center profile |
| Listing S3 | a paginator |

## Exam traps

- **Access keys in code or on an instance.** The exam answer is a role.
- **Root access keys.** Never. Lock the root user with MFA.
- **Forgetting the Region on a bucket call.** A "missing" bucket is often just in
  another Region.
- **Assuming the first page is complete.** Use pagination.
- **Thinking inbound transfer costs money.** Into AWS is free. Out is charged.
- **Ignoring cross-AZ transfer.** Charged both ways. It surprises on chatty
  designs.
- **Thinking an idle public IP is free.** It is charged hourly.
- **Treating retries as a fix for permission errors.**
- **"AWS SSO."** It was renamed IAM Identity Center. The exam guide still uses
  both names.

## Cost angle

- The cheapest account habit is budget alerts before you build anything. The lab
  sets a Zero spend budget and a Monthly cost budget, plus a billing alarm.
- Tag everything you create in a lab with `saa-course=lab`. Tags drive cost
  allocation reports (tasks 4.1–4.4 list cost allocation tags) and the cleanup
  script.
- Delete what you create. A public IPv4 address, a NAT gateway or an idle
  database keeps charging.
- Choose the tool by cost of people's time too: a template saves rework.
- Keep traffic in one AZ when you can, and use endpoints and edge caching to cut
  data transfer (task 4.4).

## Comparison

| | Console | CLI | SDK (boto3) | CloudFormation |
|---|---|---|---|---|
| Repeatable | no | yes (scripts) | yes (code) | yes (templates) |
| Reviewable before running | no | partly | in code review | yes (change sets) |
| Learning curve | lowest | low | medium | medium |
| Good for | exploring | quick tasks | applications | whole environments |
| Credentials | sign-in session | profile | credential chain | the caller's or a service role |

Now do drills 05–07 and 10, run `python concepts/demo_boto3_basics.py`, then the quiz questions on tools and cost basics.

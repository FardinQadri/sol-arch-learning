Exam tasks: 1.3, 1.2

# 03 — S3 security

## What it is

S3 is private by default. Access is decided by a **stack** of controls, and encryption protects the data even if access goes wrong.

| Layer | Question it answers |
|---|---|
| **Block Public Access** | Can anything on this bucket or account ever be public? |
| **IAM policy** | What may this user or role do? |
| **Bucket policy** | Who may do what to this bucket, and under which conditions? |
| **Access point** | A separate door, with its own policy, for one application |
| **Object Ownership / ACLs** | Who owns the objects? (Today: the bucket owner, always.) |
| **Encryption** | Is the data unreadable without the key? |

Task 1.3 is data security controls: encryption and key management. Task 1.2 is secure access to AWS resources. Drill 05
builds a locked-down bucket. Drill 06 makes a presigned URL. Drill 08 fixes a public bucket policy.

## How it works

### Evaluating access

- A request is allowed if an IAM policy **or** a bucket policy allows it and nothing **denies** it. Explicit deny always wins.
- Inside one account, an Allow in either place is enough. Across accounts, **both** accounts must allow it.
- **Block Public Access** (BPA) sits on top and overrides policies that would make data public.
- A bucket policy is a resource policy: it names a `Principal`. It can be up to **20 KB**.

### Block Public Access

BPA has four settings. All four are **on by default** for new buckets (changed in April 2023: they used to be off).

| Setting | Effect |
|---|---|
| **BlockPublicAcls** | Requests that set a public ACL fail |
| **IgnorePublicAcls** | Existing public ACLs are ignored |
| **BlockPublicPolicy** | A bucket policy that grants public access is rejected |
| **RestrictPublicBuckets** | A bucket with a public policy is limited to AWS services and users in the owner account |

- Set at the **account** or the **bucket** (also at access point and organization level). The **most restrictive** setting wins.
- BPA does not change existing policies. It switches their public effect off. Turn BPA off and they work again.
- Account level is the safety net: one switch for every bucket.

### Object Ownership and ACLs

New buckets use **Bucket owner enforced**: **ACLs are disabled** and the bucket owner owns every object, whoever uploads it.
(changed in April 2023: ACLs used to be on.) AWS recommends staying there and using policies. Only turn ACLs on for a
legacy workflow that needs them.

### Useful bucket-policy conditions

| Condition key | Use |
|---|---|
| `aws:SecureTransport` = `false` (with Deny) | Force **HTTPS**. Denies every plain HTTP request |
| `aws:SourceVpce` / `aws:SourceVpc` | Allow only traffic through your **VPC endpoint** (week 02). Keeps a policy non-public |
| `aws:SourceArn` | Let one named service resource in. CloudFront OAC uses the distribution ARN here |
| `aws:PrincipalOrgID` | Allow every account in your AWS Organization |
| `aws:SourceIp` | Allow a CIDR range |
| `s3:x-amz-server-side-encryption` | Deny uploads that are not encrypted the way you require |

Pattern: a **Deny with a negated condition** is the strongest form. "Deny `s3:*` unless `aws:SecureTransport` is true"
blocks plain HTTP for everyone.

### Encryption at rest

Every new object is encrypted. **SSE-S3** (AES-256) is the default for all new uploads, free, and cannot be turned off.
(changed on 5 January 2023: before that, you had to ask for it.)

| Option | Keys managed by | Notes |
|---|---|---|
| **SSE-S3** | S3 | Default. No cost. No key policy to manage |
| **SSE-KMS** | KMS key (AWS managed `aws/s3` or your own) | Audit trail in CloudTrail, key policy control, per-request KMS cost |
| **DSSE-KMS** | KMS key | Two layers of encryption, for strict compliance rules |
| **SSE-C** | You send the key on every request | S3 never stores the key. HTTPS only |
| **Client-side** | You, before upload | S3 only ever sees ciphertext |

- **SSE-KMS** needs permission on both the object and the KMS key. For cross-account access use a **customer managed key**:
  the AWS managed key `aws/s3` cannot be shared.
- **S3 Bucket Keys** cut KMS request costs by up to **99 %**. S3 uses a short-lived bucket-level key instead of calling KMS
  for each object. They apply to new objects and are not supported with DSSE-KMS.
- **SSE-C** is switched off by default for new buckets (changed in April 2026). You enable it deliberately. Blocked writes return 403.
- Existing unencrypted objects are not re-encrypted. Copy them over themselves (CopyObject or Batch Operations).
- **In transit:** HTTPS with TLS. Enforce it with the `aws:SecureTransport` deny.

### Presigned URLs

A **presigned URL** gives temporary access to one object, with the permissions of whoever signed it. Anyone holding the URL can use it until it expires.

- Made with the SDK or `aws s3 presign`. Works for GET and PUT.
- The CLI and SDK allow up to **7 days** when signed with an IAM user's long-term keys. The console allows 1 minute to 12 hours.
- Signed with **temporary credentials** (a role, STS, an instance profile), the URL dies when those credentials expire, even if you asked for longer. Often hours.
- The signer must have permission to the object when the URL is *used*, not only when it is made.
- Use it to let a browser upload or download without AWS credentials.

### Access points

An **access point** is a named endpoint with its own policy and, if you want, a VPC restriction. One bucket can have many.
Give each team or application its own access point and keep the bucket policy small. It also works for directory buckets and
FSx for OpenZFS volumes. **S3 Access Grants** map users from a corporate directory to prefixes.

### CloudFront with a private bucket

To serve a private bucket through CloudFront, use **Origin Access Control (OAC)**. The bucket policy allows the principal
`cloudfront.amazonaws.com` with a condition `aws:SourceArn` equal to the distribution ARN. OAC supports SSE-KMS, all Regions
and PUT/DELETE. The older **Origin Access Identity (OAI)** is legacy: no SSE-KMS and fewer Regions. A bucket used as an S3
*website endpoint* cannot use OAC. Treat it as a custom origin.

### Log delivery buckets

An **ALB access log** bucket needs a bucket policy that lets the logging service write. The recommended statement:

- Principal: the service principal `logdelivery.elasticloadbalancing.amazonaws.com`.
- Action: `s3:PutObject`. Resource: `arn:aws:s3:::bucket/prefix/AWSLogs/account-id/*`, with your real account ID.
- The bucket must be in the **same Region** as the load balancer.
- The bucket must use **SSE-S3**. SSE-KMS causes access denied. The same holds for S3 server access log buckets.
- Older Regions can still use a per-Region Elastic Load Balancing account ID as the principal. The service principal replaced it.

## Numbers to know

- BPA: **4** settings, all on for new buckets. ACLs disabled by default.
- Default encryption: **SSE-S3**, since January 2023.
- Bucket policy: up to **20 KB**.
- Presigned URL: **7 days** max with long-term keys (CLI/SDK); console 1 minute to 12 hours; shorter if the signer has temporary credentials.
- Bucket Keys: up to **99 %** fewer KMS requests.
- Encryption options: **four** server-side (SSE-S3, SSE-KMS, DSSE-KMS, SSE-C) plus client-side.

## When to choose it

| Need | Choose |
|---|---|
| No special needs, just encrypted | SSE-S3 (default) |
| Audit who used the key; control the key policy | SSE-KMS with a customer managed key |
| Many small objects with SSE-KMS and a large KMS bill | Add a Bucket Key |
| Strict dual-layer compliance rule | DSSE-KMS |
| Key must stay with you; S3 never holds it | SSE-C or client-side |
| Only HTTPS | Deny on `aws:SecureTransport` false |
| Only my VPC may read | `aws:SourceVpce` condition + gateway endpoint |
| Public website content, private bucket | CloudFront + OAC |
| Time-limited download link for a customer | Presigned URL |
| One bucket, many apps with different rules | Access points |
| ALB access logs | Service principal policy, SSE-S3 bucket |

## Exam traps

- **Making a bucket public to share one file.** Use a presigned URL or CloudFront with OAC.
- **Public policy with BPA on.** The policy is rejected or ignored. Check BPA first.
- **ACLs as the answer.** ACLs are disabled by default. Pick policies.
- **KMS for ALB logs.** It fails. Logs need SSE-S3.
- **Cross-account SSE-KMS with `aws/s3`.** It cannot be shared. Use a customer managed key.
- **Presigned URL expiry.** Signing with a role gives a URL that expires with the role session.
- **Presigned URLs are bearer tokens.** Anyone with the link has the access.
- **OAI vs OAC.** OAI is legacy. SSE-KMS needs OAC.
- **"Encrypt in transit" for S3** means HTTPS, plus the `aws:SecureTransport` deny to enforce it.
- **Default encryption does not need enabling** and cannot be disabled. Do not pick "enable encryption" as the fix.
- **Bucket Keys** reduce KMS calls and cost. They do not change who can decrypt.
- **Explicit deny wins** over any allow. A Deny for non-TLS blocks even admins.

## Cost angle

- SSE-S3 is free. SSE-KMS charges for every KMS request and for the key. A busy bucket with SSE-KMS can have a KMS bill larger than its storage bill. Turn on a Bucket Key (up to 99 % fewer requests).
- Block Public Access, ownership controls and bucket policies are free. Access points are free.
- A VPC **gateway endpoint** for S3 costs nothing and keeps S3 traffic off the NAT gateway, which would charge per GB.
- ALB access logs cost only the S3 storage. Expire them with a lifecycle rule.

## Comparison

| | SSE-S3 | SSE-KMS | DSSE-KMS | SSE-C | Client-side |
|---|---|---|---|---|---|
| Who holds the key | S3 | KMS | KMS | You (sent each request) | You |
| Default | **Yes** | No | No | Off by default | No |
| Extra cost | none | KMS requests (Bucket Key cuts it) | KMS requests | none | your code |
| Audit of key use | no | CloudTrail | CloudTrail | no | n/a |
| Works for ALB log bucket | **Yes** | **No** | No | No | No |
| Choose when | Nothing special | Compliance, control | Two-layer mandate | Own the key, S3 never stores it | S3 must never see plaintext |

Now do drill 05 (a bucket that keeps secrets), drill 06 (upload big, share briefly) and drill 08 (too public).

Exam tasks: 1.2, 3.4, 4.4

# 04 — VPC endpoints and PrivateLink

## What it is

AWS services such as S3, DynamoDB, SQS and Systems Manager have public API
addresses. A private instance with no internet path cannot reach them. You have
two ways to fix that:

1. Route the traffic through a **NAT gateway** and the internet gateway. It works, costs per GB, and the traffic leaves your VPC.
2. Give the VPC a **VPC endpoint**: a private door straight to the service. The traffic stays on the AWS network and never touches the internet.

There are two main kinds:

- **Gateway endpoint:** only **S3 and DynamoDB**. A route-table entry. **Free.**
- **Interface endpoint** (powered by **AWS PrivateLink**): a network interface with a private IP in your subnet. Works for most services. **Costs money.**

A third type, the **Gateway Load Balancer endpoint**, sends traffic to a fleet of
security appliances (firewalls). It is a niche topic for this week.

## How it works

### Gateway endpoints

- Supported services: **Amazon S3 and Amazon DynamoDB. Nothing else.**
- You create the endpoint and pick the route tables. AWS adds a route to each one: destination = the service's **prefix list** (`pl-…`, a managed list of the service's addresses), target = the endpoint (`vpce-…`). You cannot edit these routes by hand.
- It wins over the NAT or IGW route because it is more specific (longest-prefix match, note 02).
- **No hourly charge, no per-GB charge.**
- Works only in **the same Region** as the VPC and the bucket.
- It does **not** work from on-premises networks, from peered VPCs in other Regions, or through a Transit Gateway. The route lives in your VPC's route tables, so only that VPC's subnets use it.
- It is not PrivateLink and has no network interface, no security group, no private DNS.

Drill 08 has you create one and read the route it adds.

### Interface endpoints (PrivateLink)

- AWS creates an **elastic network interface (ENI) with a private IP** in each subnet you choose. Pick one subnet per AZ for availability.
- **Security groups** attach to those ENIs. Allow 443 from your workloads.
- **Private DNS** is on by default. The normal service name (for example the SQS or SSM hostname) resolves to the endpoint's private IP, so your code needs no change. This needs DNS resolution and DNS hostnames enabled on the VPC.
- Works for a large number of AWS services, and for services other companies publish.
- **Reachable from on-premises** (over VPN or Direct Connect), from peered VPCs and through a Transit Gateway. The gateway endpoint cannot do that. S3 also offers an interface endpoint for these cases.
- It does not answer ping. That is normal.
- **Billing:** an hourly charge **per endpoint per AZ**, plus a **per-GB** data processing charge.

### Endpoint policies

An **endpoint policy** is a resource policy attached to the endpoint. It limits
what can pass through. The default allows everything.

Example use: allow only `s3:GetObject` on one company bucket through the endpoint,
so a compromised instance cannot copy data to the attacker's bucket. On a gateway
endpoint the principal must be `"*"`; restrict who with a condition such as `aws:PrincipalArn`.

An endpoint policy is **one more layer**. A request must pass the endpoint policy and also the
normal week 01 evaluation of identity and resource policies; an explicit deny anywhere wins.

### Locking a bucket to a VPC

A bucket policy can say "only accept requests that come through my endpoint":

- `aws:SourceVpce` matches one **specific endpoint** ID.
- `aws:SourceVpc` matches a **whole VPC** (handy when it has several endpoints).

A `Deny` with `StringNotEquals` on one of these blocks everything that does not
come through the VPC. Take care: a mistake locks out you and your admins.

**`aws:SourceIp` stops working through an endpoint.** Requests through an endpoint
arrive with a private address, so the source IP condition no longer sees the public IP.
Use `aws:SourceVpce`, `aws:SourceVpc`, or `aws:VpcSourceIp` instead.

### PrivateLink for your own services

PrivateLink also lets you publish a service, and lets others use it, with no
peering and no route tables:

1. The provider puts the service behind a **Network Load Balancer** (or Gateway Load Balancer).
2. The provider creates a **VPC endpoint service** on it.
3. The consumer creates an **interface endpoint** to that service in their VPC (same or other account).

The consumer sees only that one service as private IPs in their own subnets.
**Overlapping CIDRs do not matter**, and the consumer cannot reach anything else in the
provider's VPC. This is the answer for "expose one service to hundreds of customer
VPCs" and for consuming SaaS products privately. Connections start only on the consumer side; the provider cannot open connections into the consumer's VPC.

### NAT gateway or endpoint? The maths

Drill 09 has you compute this. Illustrative prices:

| Item | Price |
|---|---|
| NAT gateway, per hour | 0.045 USD |
| NAT gateway, per GB | 0.045 USD |
| Gateway endpoint (S3, DynamoDB) | 0.00 USD hourly, 0.00 USD per GB |
| Interface endpoint, per hour per AZ | 0.01 USD |
| Interface endpoint, per GB | 0.01 USD |

Example inputs (made up for the sum): 2,000 GB a month to S3 from a private subnet, in a month of 730 hours:

- Through NAT: 730 × 0.045 + 2,000 × 0.045 = 32.85 + 90.00 = **122.85 USD** (plus the IPv4 address).
- Through a gateway endpoint: **0.00 USD**.

Example, the same 2,000 GB to a service that has no gateway endpoint, using an
interface endpoint in 2 AZs:

- Interface endpoint: 2 × 730 × 0.01 + 2,000 × 0.01 = 14.60 + 20.00 = **34.60 USD**.
- Cheaper than NAT at this volume. At very low volume, the hourly charge makes the endpoint worse: a few GB a month is cheaper on a NAT gateway you already run.

Rule of thumb: S3 or DynamoDB → gateway endpoint, always. Another AWS service with
steady traffic → interface endpoint. Occasional traffic to the internet → NAT.

## Numbers to know

- Gateway endpoint services: **S3 and DynamoDB only**. Cost: **free**.
- Interface endpoint: ~0.01 USD per hour per AZ + 0.01 USD per GB (illustrative).
- NAT gateway: 0.045 USD per hour + 0.045 USD per GB (illustrative).
- Gateway endpoints: 20 per Region by default (adjustable); 255 per VPC.
- Endpoint policy: maximum 20,480 characters.
- One interface-endpoint ENI per chosen subnet, one subnet per AZ.

## When to choose it

| Need | Choose |
|---|---|
| Private instances read and write S3 or DynamoDB | Gateway endpoint |
| Private instances call SQS, SNS, SSM, KMS, Secrets Manager | Interface endpoint |
| On-premises must reach S3 over private links | S3 interface endpoint |
| Let only this VPC read a bucket | Bucket policy with `aws:SourceVpce` or `aws:SourceVpc` |
| Stop data leaving to other buckets | Endpoint policy |
| Offer one internal service to many VPCs, CIDRs may overlap | PrivateLink: NLB + endpoint service |
| Consume a SaaS vendor privately | Interface endpoint to their endpoint service |
| General internet access (patches, third-party APIs) | NAT gateway |
| Inspect traffic with a firewall fleet | Gateway Load Balancer endpoint |

## Exam traps

- **"Gateway endpoint for SQS."** No. Gateway endpoints support only S3 and DynamoDB.
- **Interface endpoint for S3 to save money.** The gateway endpoint is free. Pick the interface type for S3 only when you need on-premises or cross-Region peered access.
- **Gateway endpoint from on-premises.** Not supported. Use an interface endpoint.
- **`aws:SourceIp` in the bucket policy** to restrict to the VPC. It will not match. Use `aws:SourceVpce`.
- **Gateway endpoint in the wrong Region.** It reaches only same-Region buckets.
- **Forgetting the route.** A gateway endpoint works through route-table entries. Associate the right route tables.
- **Forgetting the security group.** Interface endpoints have one. Allow 443 from the workload.
- **Private DNS off.** The service name still resolves to the public address and the traffic goes to the NAT or fails.
- **PrivateLink needs peering.** It does not. It also does not need matching CIDRs.
- **Endpoint policy replaces the IAM policy.** It does not. Both must allow.

## Cost angle

- The first cost cut in many bills: add S3 and DynamoDB gateway endpoints. They are free and they drain bytes off the 0.045 USD per GB NAT charge.
- Interface endpoints cost per AZ per hour. A dozen of them across three AZs is a real monthly bill. Share one set of endpoints through a central "shared services" VPC when you have many VPCs.
- Compare before you buy: for low or sporadic traffic, a NAT gateway you already pay for can be cheaper than a new interface endpoint.
- The exam answer to "reduce NAT cost, traffic goes to S3" is the **gateway endpoint**.

## Comparison

| | Gateway endpoint | Interface endpoint | NAT gateway |
|---|---|---|---|
| Services | S3, DynamoDB only | Most AWS services, SaaS, your own | Anything on the internet |
| How it works | Route-table prefix-list entry | ENI with private IP, private DNS | Translates private IP, via IGW |
| Hourly cost | None | Per endpoint per AZ | Per gateway |
| Per-GB cost | None | Yes (low) | Yes (higher) |
| Security groups | No | Yes | No (on resources behind it) |
| From on-premises | No | Yes | No |
| Needs an internet gateway | No | No | Yes |
| Policy control | Endpoint policy | Endpoint policy + SG | None |

Now do drill 08 (reach S3 without the internet) and drill 09 (NAT gateway or endpoint).

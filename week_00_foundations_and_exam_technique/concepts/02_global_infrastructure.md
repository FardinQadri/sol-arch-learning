Exam tasks: 2.2, 3.4

# 02 — Global infrastructure

## What it is

AWS runs its services from physical sites around the world. You choose where
your resources live. That choice affects latency, law, price and how well you
survive failures.

The building blocks, from biggest to smallest:

- **Region** — a geographic area, such as `us-east-1` (N. Virginia) or
  `eu-west-1` (Ireland). A Region holds several Availability Zones. Regions are
  isolated from each other by design.
- **Availability Zone (AZ)** — one or more separate data-centre facilities inside
  a Region, with their own power, cooling and networking. AZs in a Region are
  joined by fast, low-latency links. They are far enough apart that one fire or
  flood should not hit two, and close enough for synchronous replication.
- **Local Zone** — an extension of a Region placed in a big city, close to users
  or on-site systems. You get a subset of services with very low
  latency to that city.
- **Wavelength Zone** — AWS compute and storage placed inside a 5G network
  operator's data centres, so mobile devices reach your app without leaving the
  carrier network first.
- **Outposts** — AWS-managed racks (or servers) installed in your own data
  centre. Same APIs, but the hardware sits on your site. Use it for local data
  processing or strict on-premises data residency.
- **Edge location / point of presence (PoP)** — a small site close to end users
  that runs edge services: CloudFront (content delivery), Route 53 (DNS),
  Global Accelerator, and AWS WAF and Shield protection at the edge. Edge
  locations cache and route. They do not host your databases or servers.

## How it works

### Choosing a Region

Four factors, usually in this order of strength:

1. **Data residency and compliance.** If a law or contract says the data must
   stay in a country, that decides it. No other factor can override it.
2. **Latency to users.** Pick the Region nearest your users. Distance adds
   latency you cannot buy back.
3. **Service availability.** New services and features arrive in some Regions
   first. Check that every service you need exists in the Region.
4. **Price.** Prices differ by Region for the same service. Cost is the last
   tie-breaker, never the first.

Exam habit: a hard constraint (residency, a required service) removes options.
Only then do latency and price decide between what is left.

### Global, Regional or zonal?

Every AWS resource has a scope. It tells you where it lives and what happens if
that place fails.

| Scope | Meaning | Examples |
|---|---|---|
| Global | One control plane for the whole account; not tied to one Region | IAM (users, roles, policies), Route 53, CloudFront, AWS Organizations |
| Regional | Lives in one Region; spread across the Region's AZs by AWS | S3 buckets, DynamoDB tables, SQS queues, SNS topics, Lambda functions, VPCs, RDS Multi-AZ (when configured) |
| Zonal | Lives in exactly one AZ | EC2 instances, EBS volumes, subnets, NAT gateways, single-AZ RDS instances |

Notes that surprise people:

- An S3 *bucket* is Regional: you choose a Region when you create it. Its object
  names are in one global namespace, so bucket names must be unique worldwide.
- A VPC spans all the AZs of one Region. A **subnet** lives in one AZ. To use
  several AZs you create a subnet in each.
- An EBS volume exists in one AZ and attaches only to instances in that AZ. To
  move data to another AZ you snapshot and restore.
- IAM is global. A role you create is usable in every Region. That is why IAM
  does not need a Region to be picked.
- "Highly available" for a zonal resource is your job: run more than one, in more
  than one AZ. A Regional service has already done that for you.

### AZ names versus AZ IDs

When you see `us-east-1a`, that is an **AZ name**. AWS maps names to physical
AZs *separately for each account*, to spread load. So your `us-east-1a` may be
a different building from another account's `us-east-1a`.

An **AZ ID**, such as `use1-az1`, always points to the same physical AZ in every
account. Use AZ IDs when two accounts must agree on the same physical location,
for example when sharing a subnet or placing resources next to each other to
avoid cross-AZ transfer charges.

Rule: names are labels per account; IDs are the truth.

### Reading an ARN

Almost everything in AWS has an Amazon Resource Name. It is the unique address of
a resource, used in policies, logs and APIs.

```
arn:PARTITION:SERVICE:REGION:ACCOUNT:RESOURCE
```

Rules of thumb:

- The first part is always the literal `arn`.
- Partitions are `aws`, `aws-cn` (China) and `aws-us-gov` (GovCloud).
- Global services leave the REGION part empty (IAM). S3 leaves both REGION and
  ACCOUNT empty because bucket names are globally unique.
- RESOURCE is often `type/id` or `type:id`. The separator differs by service, so
  split on whichever comes first.

You build a parser for this in drill 01.

### Discovering where you are

You will use boto3 in the demo. A client is tied to one Region. If you create an
S3 client for `us-east-1` and ask about a bucket in `eu-west-1`, calls can fail
or redirect. When something "does not exist", check the Region first.

## Numbers to know

The exam rarely asks for the exact count of Regions or AZs, and they grow over
time, so do not memorise totals. The numbers worth knowing:

| Fact | Value |
|---|---|
| Reserved IP addresses per subnet | 5 (network, .1 router, .2 DNS, .3 future use, broadcast) |
| AZs a subnet lives in | exactly 1 |
| AZs you need for "survive the loss of one AZ" | at least 2 |
| Public IPv4 address charge | 0.005 USD per hour, in use or idle |

Subnet sizing example: a subnet with 256 addresses leaves 256 − 5 = 251 you can
use.

## When to choose it

| Need | Choose |
|---|---|
| Data must stay in a country | a Region in that country |
| Lowest latency to a large user base | the Region nearest them, plus CloudFront for content |
| Survive an AZ outage | spread across at least 2 AZs in one Region |
| Survive a whole-Region outage | a second Region (see disaster recovery, week 09) |
| Very low latency to one big city, other services from the Region | Local Zone |
| Ultra-low latency to 5G mobile devices | Wavelength Zone |
| AWS APIs on your own premises, local data processing | Outposts |
| Cache or accelerate for users everywhere | edge locations through CloudFront or Global Accelerator |

## Exam traps

- **"Multi-AZ equals multi-Region."** It does not. Multi-AZ protects against the
  loss of a facility. Only a second Region protects against the loss of a Region.
- **Edge locations are not Regions.** You cannot launch EC2 in an edge location.
  CloudFront caches there. That is all.
- **Local Zone versus Outposts.** Local Zones are AWS-run sites in cities. Outposts
  are AWS hardware in *your* building. "Our own data centre" points to Outposts.
- **Wavelength versus Local Zone.** Wavelength is for 5G, inside carrier networks.
- **Assuming `us-east-1a` is the same everywhere.** AZ names are per account.
- **Choosing a Region on price when residency applies.** Residency wins.
- **Forgetting that a subnet is zonal.** One subnet, one AZ. A "multi-AZ" design
  needs subnets in at least two AZs.
- **IAM and Route 53 are global.** You do not create them "in" a Region.
- **Cross-AZ traffic is not free.** See the cost angle.

## Cost angle

- Prices differ by Region. The same instance can cost more in one Region than
  another. Region choice is a cost lever, but only after residency and latency.
- Data transfer is a bill line:
  - data *into* AWS from the internet is free;
  - data *out* to the internet is charged;
  - data between AZs in the same Region is charged, in both directions;
  - data between Regions is charged.
  So a chatty design that crosses AZs on every call has a hidden cost. Keep
  traffic inside an AZ where you can, and cache at the edge for global content.
- A public IPv4 address costs 0.005 USD per hour whether used or idle. One
  address left running for a 30-day month: 0.005 × 24 × 30 = 3.60 USD.
- Edge caching with CloudFront reduces load on your origin and can reduce the
  transfer you pay to send data out.
- A single NAT gateway shared by all AZs saves the cost of one per AZ but adds
  cross-AZ traffic and a single point of failure. You will revisit this in the
  networking weeks.

## Comparison

| Location type | What it is | Latency | Typical use |
|---|---|---|---|
| Region | geographic area with several AZs, isolated from other Regions | baseline for most workloads | where your workload normally runs; compliance boundary |
| Availability Zone | one or more data-centre facilities inside a Region | very low between AZs in the same Region | spread instances for high availability |
| Local Zone | Region extension in a large city, limited services | very low to that city | latency-sensitive apps, media, gaming near one city |
| Wavelength Zone | AWS compute inside a 5G carrier network | lowest for mobile devices on that carrier | 5G apps, AR/VR, live video |
| Outposts | AWS rack in your own data centre | local, no WAN trip | on-premises data processing, residency on your site |
| Edge location (PoP) | small site for CDN, DNS and acceleration | close to end users | CloudFront, Route 53, Global Accelerator, WAF |

Now do drill 01 (read an ARN) and drill 05, then the quiz questions on global infrastructure.

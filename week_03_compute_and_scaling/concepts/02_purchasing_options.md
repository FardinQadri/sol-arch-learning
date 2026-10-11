Exam tasks: 4.2

# 02 — Purchasing options

## What it is

The same instance can be bought in several ways. The instance is identical. The **price**, the **commitment**
and whether **capacity is guaranteed** differ.

| Question | Options that answer it |
|---|---|
| How much do I pay per hour? | On-Demand, Savings Plans, Reserved Instances, Spot |
| Is capacity guaranteed in an AZ? | Zonal Reserved Instances, On-Demand Capacity Reservations |
| Do I need my own server (licences, compliance)? | Dedicated Hosts, Dedicated Instances |

Task 4.2 asks you to match a usage pattern to the cheapest option that still meets the requirement. Drill 02
prices a fleet four ways. Drill 09 asks you to decide for given scenarios.

## How it works

### On-Demand

- Pay **per second**, only while the instance is running, with a **60-second minimum**.
- No commitment, no discount. Fixed per-second price.
- If AWS has no capacity in the AZ, the launch fails with an insufficient-capacity error.
- Best for: new, short-lived or unpredictable workloads, and the peaks above your committed baseline.

### Savings Plans

You commit to a **dollar amount per hour** of usage for **1 or 3 years**. Usage up to the commitment is billed
at the lower rate. Anything above it is On-Demand.

| Plan | Discount (up to) | What it covers |
|---|---|---|
| **Compute** Savings Plan | 66 % | Any instance family, size, Region, OS and tenancy. Also Fargate and Lambda |
| **EC2 Instance** Savings Plan | 72 % | One instance **family** in one **Region** (for example m5 in Virginia). Any size, OS and tenancy inside it |
| Database Savings Plan | up to 35 % | Aurora, RDS, DynamoDB, ElastiCache and more (week 05 has detail) |

- Payment options: **All upfront**, **Partial upfront**, **No upfront**. More upfront means a bigger discount.
- A plan cannot be changed or cancelled after purchase. Buy another plan when usage grows.
- **Spot Instances are not covered.** Spot spend does not use up the commitment.
- Compute and EC2 Instance plans also apply to the EC2 instances inside ECS, EKS and EMR clusters.
- A Savings Plan is a billing discount. It does **not reserve capacity**.

### Reserved Instances (RIs)

An RI is also a billing discount, not a physical instance. It matches running instances by instance type, Region,
tenancy and platform. Terms are 1 or 3 years with the same three payment options. It is not renewed automatically.

| | Standard RI | Convertible RI |
|---|---|---|
| Discount | up to 72 % (1-year average 40 %) | up to 66 % (1-year average 31 %) |
| Change later | Modify only | Exchange for other family, type, platform, tenancy; also modify |
| Sell in the Reserved Instance Marketplace | **Yes** | No |

**Scope** decides whether an RI reserves capacity. The price is the same either way.

| Scope | Capacity reserved? | Discount applies | Size flexibility |
|---|---|---|---|
| **Regional** | **No** | In any AZ in the Region | Yes (Linux/Unix, default tenancy) |
| **Zonal** | **Yes**, in that AZ | Only in that AZ | No |

Exam rule: "reserve capacity in an AZ and get a discount" means a **zonal RI**. A regional RI or any Savings Plan
gives the discount only.

AWS now says "We recommend Savings Plans over Reserved Instances". The exam still asks about both.
The Savings Plans FAQ compares them: Compute Savings Plans "up to 66% (just like Convertible RIs)" and EC2 Instance
Savings Plans "up to 72% (just like Standard RIs)". So Compute SP is the flexible, Convertible-like choice, and
EC2 Instance SP is the deeper-discount, Standard-like choice. Compute Savings Plans also cover Fargate and Lambda; EC2 Instance Savings Plans and RIs do not.

### Spot Instances

Spare EC2 capacity at up to **90 %** off On-Demand. EC2 sets the price. It adjusts gradually from supply and
demand (the old bidding model is gone). A Spot capacity pool is one instance type in one AZ.

- AWS can take the capacity back. You get a **two-minute interruption notice** (EventBridge and instance metadata,
  best effort). Check the metadata item `spot/instance-action` about every 5 seconds.
- A **rebalance recommendation** can arrive earlier. It says the instance is at elevated risk of interruption.
- Interruption behaviour, set in the request: **terminate**, **stop** or **hibernate**. Hibernate gives no
  two-minute lead because it starts at once.
- Request types: **one-time** or **persistent** (a persistent request is resubmitted after an interruption).
- Setting a maximum price makes interruptions **more** frequent. Usually leave it unset.
- Spread across many instance types and AZs to find more capacity pools (note 04, mixed instances).

Best for: stateless, fault-tolerant, flexible work. Batch, CI runners, data processing, web tiers behind an ASG
with an On-Demand base. Never for a single database or anything that must not stop.

### Dedicated Hosts and Dedicated Instances

| | Dedicated Host | Dedicated Instance |
|---|---|---|
| What you get | A whole physical server for you | Instances on hardware used by one account only |
| Visibility | Sockets and cores; host affinity; targeted placement | None |
| Billing | **Per host** | **Per instance**, plus 2 USD/hour per Region with one running |
| BYOL (bring your own licence) | Full: per-socket, per-core, per-VM | Partial |
| Hardware sharing | Not shared | May share with your other (non-dedicated) instances |

Choose a **Host** when a licence is tied to sockets or cores, or when you need host-level control.
Choose a **Dedicated Instance** when you only need single-tenant hardware for compliance.
Hosts can be bought On-Demand or with a Savings Plan; Host Reservations go up to 70 % off. Savings Plans do not
discount the Dedicated Instance Region fee.

### On-Demand Capacity Reservations (ODCR)

Reserve capacity in one AZ for as long as you like. Create or cancel at any time. No term.

- **No billing discount by itself.** You pay On-Demand rates whether the instances run or not.
- Combine with a Savings Plan or a Regional RI to get a discount.
- Matches on instance type, platform, AZ and tenancy.
- Unlike a zonal RI, no 1- or 3-year commitment.
- It counts against your On-Demand quota, even if unused.

**Capacity Blocks for ML** reserve GPU instances for a future date for a short period. Up to 8 weeks ahead.
They cannot be cancelled.

### Choosing and combining

The standard cost-saving pattern for a steady service:

1. **Baseline** (always running): cover with a Savings Plan or RIs.
2. **Peaks** (hours or days): On-Demand, or Spot if the work tolerates interruption.
3. **Must-have capacity in an AZ**: add an ODCR or a zonal RI.

AWS guidance, in one table: commit to a spend amount, use Savings Plans. Need capacity in an AZ, use an RI or a
Capacity Reservation. A GPU cluster for a short window, Capacity Blocks. Can be interrupted, Spot. Compliance or
licences, Dedicated Hosts or Instances.

### The commitment break-even idea

A commitment bills for **every hour**, used or not. It wins only if you use the instance for more than a fraction of
the hours equal to **1 minus the discount**.

Course example discounts (examples, not AWS prices): Compute Savings Plan **31 %**, Standard RI **40 %**, Spot **70 %**.
With `m7g.large` at 0.0816 USD/hour On-Demand:

| Option | Effective hourly price | Break-even use vs On-Demand |
|---|---|---|
| On-Demand | 0.0816 | n/a |
| Compute Savings Plan (31 % off) | 0.0563 | used more than 69 % of hours |
| Standard RI (40 % off) | 0.0490 | used more than 60 % of hours |
| Spot (70 % off) | 0.0245 | no commitment, but can be interrupted |

An instance that runs 8 hours a day uses 33 % of hours. A commitment loses money there. On-Demand wins there — or Spot, if the work can be interrupted.
Drill 02 asks for the same sums with a fleet.

## Numbers to know

- On-Demand: per second, **60-second** minimum.
- Savings Plans: **1 or 3 years**; Compute up to **66 %**, EC2 Instance up to **72 %**; Database up to 35 %.
- Standard RI: up to **72 %**, 1-year average 40 %. Convertible RI: up to **66 %**, 1-year average 31 %.
- Spot: up to **90 %** off; **two-minute** interruption notice.
- Zonal RI: reserves capacity. Regional RI and Savings Plans: do not.
- Dedicated Instance Region fee: 2 USD/hour. Capacity Blocks: up to 8 weeks ahead, cannot be cancelled.
- RI limits: 20 per AZ (zonal) or 20 per Region (regional) by default.
- Marketplace sale of Standard RIs: at least 1 month left, AWS fee 12 %.

## When to choose it

| Usage pattern | Choose |
|---|---|
| Steady 24/7 for a year or more, may change instance family | Compute Savings Plan |
| Steady, family and Region fixed, want the deepest discount | EC2 Instance Savings Plan (or Standard RI) |
| Need capacity reserved in one AZ plus a discount | Zonal RI, or ODCR plus a plan |
| Might need to sell the commitment early | Standard RI (Marketplace) |
| Unpredictable, short, spiky | On-Demand |
| Batch, CI, fault-tolerant, flexible | Spot |
| Licence tied to sockets or cores | Dedicated Host |
| Single-tenant hardware, no licence rules | Dedicated Instance |
| GPU training for two weeks next month | Capacity Blocks |
| Serverless and containers also use compute | Compute Savings Plan (covers Fargate and Lambda) |

## Exam traps

- **"Reserve capacity" with a Savings Plan or regional RI.** They do not. Only a zonal RI or an ODCR does.
- **Capacity Reservation as a discount.** An ODCR has none by itself.
- **Spot with a Savings Plan.** Not covered. Spot has its own price.
- **Convertible RI in the Marketplace.** Only Standard RIs can be sold.
- **Spot for a database or a single instance.** Use it for stateless, restartable work.
- **Dedicated Instance vs Dedicated Host.** BYOL by socket or core means Host.
- **Commitments for unpredictable load.** Cover only the baseline.
- **Savings Plans cannot be cancelled.** Over-commit and you pay the hourly amount anyway.
- **RI "renews".** It does not. When the term ends you are back on On-Demand rates.
- **Spot interruption.** Two minutes, not twenty. Design for fast shutdown.

## Cost angle

- Start with right-sizing (note 01), then buy commitments. Committing to a bloated fleet locks in the waste.
- Cover the **minimum** usage you will have all term, not the average.
- 3 years saves more than 1 year, with more risk. More upfront saves more than none.
- Mixed instance groups (note 04) let an ASG run an On-Demand base with Spot on top. Your RIs and plans apply to the On-Demand part.
- Unused Capacity Reservations cost the full On-Demand rate. Cancel what you do not need.
- Cost Explorer and AWS Budgets show coverage and utilisation of your commitments. Watch both.
- The Dedicated Instance Region fee (2 USD/hour) is large next to a small fleet. Hosts suit big, licence-bound fleets.

## Comparison

| | On-Demand | Savings Plan | Reserved Instance | Spot | Dedicated Host |
|---|---|---|---|---|---|
| Commitment | None | $/hour, 1 or 3 years | Instance, 1 or 3 years | None | On-Demand or reservation |
| Discount (up to) | 0 | 66 % / 72 % | 66 % / 72 % | 90 % | 70 % with reservation |
| Reserves capacity | No | No | Zonal only | No | Your own host |
| Interruptible | No | No | No | **Yes** (2-minute notice) | No |
| Flexibility | Total | Compute: very high | Standard low, Convertible medium | Pool-dependent | Low |
| Best for | Spiky, new | Steady baseline | Steady, AZ capacity | Fault-tolerant batch | Licences, compliance |

Now do drill 02 (pay for the hours you use) and drill 09 (decide where instances live and how to buy them).

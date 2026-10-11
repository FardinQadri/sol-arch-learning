Exam tasks: 2.2

# 04 — Availability and failure

## What it is

**Availability** is the fraction of time a system works when users need it.
It is written as a percentage, or as "nines": 99.9 % is "three nines".

    availability = time up ÷ total time

**Fault tolerance** is stronger than high availability. A highly available system
recovers quickly from a failure, perhaps with a short blip. A fault-tolerant
system keeps working with no interruption when a component fails.

Everything fails sooner or later: disks, servers, racks, whole data centres.
Resilient design assumes this and plans for it. Task 2.2 asks you to design
for it and to remove single points of failure.

## How it works

### Nines turn into minutes

Downtime allowed = (1 − availability) × time period.

Use 30 days = 43,200 minutes (30 × 24 × 60) and one year = 525,600 minutes
(365 × 24 × 60). Computed:

| Availability | Down per 30 days | Down per year |
|---|---|---|
| 99 % | 432 min (1 − 0.99 = 0.01; 0.01 × 43,200) | 5,256 min = 87.6 h |
| 99.9 % | 43.2 min | 525.6 min = 8.76 h |
| 99.95 % | 21.6 min | 262.8 min = 4.38 h |
| 99.99 % | 4.32 min | 52.56 min |
| 99.999 % | 0.432 min (about 26 s) | 5.256 min |

Each extra nine cuts the allowed downtime by ten. It also raises the effort and
cost a lot. Run `python concepts/demo_availability.py` to see the same table
from code. In drill 02 you compute it yourself.

### Components in series

If a request must pass through every component, and each can fail, the system
works only when **all** of them work. You multiply:

    A(system) = A1 × A2 × A3 × ...

Example: a load balancer at 0.9999, one app instance at 0.99 and a database at
0.9995.

    0.9999 × 0.99 × 0.9995 = 0.98941

That is lower than the weakest part alone (0.99). Series
chains are always worse than their weakest link. Every extra dependency makes
it worse.

### Components in parallel

If you run **copies** of a component and any one can serve the request, the
system fails only when **all** copies fail. Chance of failure for one copy is
(1 − A). For n independent copies:

    A(group) = 1 − (1 − A)^n

Two app instances at 0.99 each:

    1 − (1 − 0.99)^2 = 1 − 0.0001 = 0.9999

Put that group back in the chain:

    0.9999 × 0.9999 × 0.9995 = 0.99930

Availability moved from 0.98941 to 0.99930 just by adding a second instance.
Now the database (0.9995) is the weak link. More app copies will not fix it.
You need a Multi-AZ database, too. The lesson: find the weakest component, make
it redundant, then find the next weakest one.

"Independent" matters. Two instances in the **same** AZ share that AZ's power
and network. When the AZ fails, both fail. So the formula only holds if the
copies sit in separate failure domains: separate AZs.

### Single points of failure (SPOF)

A SPOF is any one component whose failure takes the whole system down. Hunt for
them by asking "if this one thing disappeared, what stops?" Common SPOFs:

- one EC2 instance (zonal)
- one EBS volume (zonal)
- a database in a single AZ
- one NAT gateway serving private subnets in several AZs
- one load balancer node, if you front it yourself
- one Region, when the business needs Region-level survival
- a human step that no one else can do

The fix is almost always redundancy in another AZ, plus something that notices
the failure and shifts the traffic (a load balancer health check, Route 53
health check, Auto Scaling replacement).

### Multi-AZ by default

For anything that matters, design as if one AZ can vanish:

- Run at least 2 AZs. A subnet lives in one AZ, so create subnets in several.
- Put an Auto Scaling group across the subnets of several AZs.
- Put a load balancer across several AZs.
- Use Multi-AZ for relational databases. Regional services (S3, DynamoDB, SQS)
  already spread across AZs for you.

Note on Aurora: its read replicas (up to 15 per cluster) double as failover
targets and can sit in other AZs.

### Static stability

Imagine an AZ fails. You have two ways to handle the lost capacity.

1. **Scale on failure.** Wait for the failure, then ask AWS to launch new
   instances in the surviving AZs. This depends on launches succeeding at the
   very moment a lot of customers are doing the same, and it takes time.
2. **Static stability.** Keep **spare capacity already running** in the other AZs
   before any failure. When one AZ is lost, the survivors can take the load
   immediately, with no need to launch anything.

Static stability is the preferred design for important workloads. It trades
extra running cost for a fast, dependable recovery. The idea: during a failure,
rely on things that already exist, not on new things being created.

### The "lose one AZ" sizing rule

You need N instances' worth of capacity to carry the peak load. You want to keep
carrying it after one AZ is gone. With `a` AZs in use, after one fails you have
`a − 1` left, and they must carry N between them.

    per AZ = ceil(N ÷ (a − 1))
    total  = a × per AZ

Worked example A: N = 10, three AZs.

    per AZ = ceil(10 ÷ 2) = 5      total = 3 × 5 = 15

You run 15 instances for 10 instances of work. Overhead: 5 extra, so 50 %.

Worked example B: N = 10, two AZs.

    per AZ = ceil(10 ÷ 1) = 10     total = 2 × 10 = 20

Overhead: 100 %. You pay for double.

Worked example C: N = 7, three AZs. Rounding up matters.

    per AZ = ceil(7 ÷ 2) = ceil(3.5) = 4     total = 3 × 4 = 12

More AZs means less overhead (for N = 10: 20 instances with two AZs, 15 with
three AZs). Each extra AZ spreads the spare capacity thinner. You build this
calculator in drill 03.

### Preview: RTO and RPO

Two numbers define a disaster recovery plan. Week 09 covers them in full.

- **RTO (recovery time objective)** — how long the business can be down. How fast
  must you be back?
- **RPO (recovery point objective)** — how much data the business can lose,
  measured in time. How far back can you restore to?

The four strategies in the exam guide, from cheapest and slowest to dearest and
fastest: backup and restore, pilot light, warm standby, active-active.

## Numbers to know

| Fact | Value |
|---|---|
| Minutes in 30 days | 43,200 |
| Minutes in a year | 525,600 |
| Downtime at 99.9 % | 43.2 min per 30 days |
| Downtime at 99.99 % | 4.32 min per 30 days |
| Series | multiply availabilities |
| Parallel | 1 − (1 − A)^n |
| Aurora replicas | up to 15 per cluster |
| Minimum AZs to survive losing one | 2 (but 3 is cheaper per unit of capacity) |

## When to choose it

| Requirement in the question | Design |
|---|---|
| Survive an instance failure | Auto Scaling group with health checks |
| Survive an AZ failure | resources in at least 2 AZs with a load balancer, Multi-AZ database |
| Recover fast from an AZ failure without new launches | static stability: spare capacity already running |
| Survive a Region failure | second Region plus a DR strategy chosen from RTO and RPO |
| Keep cost low and tolerate some downtime | fewer nines: single AZ with backups |

## Exam traps

- **Adding a second instance in the same AZ.** It helps with instance failure
  but not AZ failure.
- **Treating series like parallel.** More components in a chain lower
  availability. More copies in parallel raise it.
- **Strongest-sounding answer.** Multi-Region is not always the answer. If the
  requirement is "survive one AZ" a Multi-AZ design is enough and cheaper.
- **Scale-on-failure sold as high availability.** If the requirement says
  "immediately" or "no capacity gap", pick spare running capacity.
- **Forgetting the data tier.** An application with two copies and a single-AZ
  database is still a single point of failure.
- **Mixing up HA and fault tolerance.** Fault tolerant means no interruption.
- **Mixing up RTO and RPO.** RTO is time to be back. RPO is data you can lose.
- **Confusing Multi-AZ with read replicas.** Multi-AZ is for availability.
  Read replicas are for read scale (up to 15 per source for RDS MySQL), although
  they can be promoted.

## Cost angle

- Redundancy costs money. Two AZs doubles the footprint of the sizing rule above
  (100 % overhead for N = 10). Three AZs costs 50 % extra for the same N. If
  the question asks for the most cost-effective resilient design, three AZs
  can beat two.
- Higher nines cost more. Do not buy 99.99 % for a system that may be down
  during a nightly window.
- Non-production environments do not usually need Multi-AZ. Task 4.2 says to
  determine the required availability for different classes of workload.
- Cross-AZ data transfer is charged in both directions. Synchronous replication
  and chatty calls across AZs show up on the bill.
- Idle standby capacity costs the same as busy capacity. That is the price of
  static stability.

## Comparison

| Approach | Survives | Recovery | Extra cost | Use when |
|---|---|---|---|---|
| Single instance, single AZ | nothing | rebuild by hand | none | dev or test |
| Auto Scaling in one AZ | instance failure | minutes (replacement) | low | tolerant of AZ loss |
| Multi-AZ with spare capacity (static stability) | AZ failure | immediate | moderate (spare servers) | production, strict availability |
| Multi-AZ, scale on failure | AZ failure | minutes, depends on launches working | low | moderate availability needs |
| Multi-Region | Region failure | depends on DR strategy | high | Region-level survival required |

Now do drills 02 and 03, then the quiz questions on availability and failure.

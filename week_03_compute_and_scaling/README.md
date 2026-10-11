# Week 03 — EC2 compute, purchasing, Auto Scaling and load balancing

## Goals

By the end of this week you can:

1. Read an instance type and choose a family and size for a workload.
2. Choose a purchasing option for a usage pattern: On-Demand, Savings Plan, Reserved Instance, Spot, Dedicated.
3. Launch instances safely: a launch template, IMDSv2 required, an instance profile, user data and placement.
4. Build a self-healing, self-scaling Auto Scaling group across Availability Zones.
5. Choose and configure a load balancer and its listener rules.
6. Reason about compute cost: right-sizing, commitments, Spot and load balancer charges.

## Your week

About 10–12 hours. Do the steps in order.

1. Concept notes 01–05 and the two demos in `concepts/` (~3 h). Run the demos:
   `python concepts/demo_fleet_in_moto.py` and `python concepts/demo_scaling_and_routing.py`.
2. Drills: `python practice/exercises.py` (~3–4 h). Drills 01–05 are small models you build yourself: an instance-type
   decoder, a cost calculator, scaling policies, a listener-rule matcher and cross-zone maths. Drills 06–08 use boto3
   against a fake AWS. Drills 09 and 10 are decisions and predictions. Do them in order.
3. Quiz: `python quiz.py --week 3 -n 30` until you score 80 % or more (~1.5 h).
4. Milestone M03: the course project's compute tier (~2–3 h). See `course_project/milestones/M03.md`.
5. Optional lab (~1–1.5 h, about 0.10 USD): `lab/LAB.md`. Run a two-instance web fleet behind an ALB and watch it heal.

## Exam tasks covered

| Task | Title |
|---|---|
| 2.1 | Design scalable and loosely coupled architectures |
| 2.2 | Design highly available and/or fault-tolerant architectures |
| 3.2 | Design high-performing and elastic compute solutions |
| 4.2 | Design cost-optimized compute solutions |

Task 3.2 is the main target: instance types, scaling metrics and conditions. Task 2.1 and 2.2 appear through load
balancing, multiple AZs and self-healing groups. Task 4.2 is the purchasing options and the choice between ALB, NLB and GWLB.

## Service comparison

| Option | What it is | Commitment | Capacity guaranteed | Interruptible | Use it when |
|---|---|---|---|---|---|
| On-Demand | Pay per second | None | No | No | Spiky or new load, peaks |
| Savings Plan | $/hour for 1 or 3 years | Yes | No | No | Steady baseline, flexible family |
| Reserved Instance | Billing discount per instance | Yes | Zonal only | No | Steady load, AZ capacity |
| Spot | Spare capacity, up to 90 % off | None | No | Yes, 2-minute notice | Fault-tolerant, flexible jobs |
| Dedicated Host | A whole server | Optional | Your host | No | Per-socket or per-core licences |

| Load balancer | Layer | Protocols | Routes by | Pick it for |
|---|---|---|---|---|
| ALB | 7 | HTTP, HTTPS | Host, path, header, method | Web apps and microservices |
| NLB | 4 | TCP, UDP, TLS | Port | Extreme performance, static IPs, PrivateLink |
| GWLB | 3 | IP packets (GENEVE) | Transparent | Firewalls and inspection appliances |

## Interview questions

Answer each out loud in under two minutes.

1. How do you choose an instance type?
2. Savings Plan or Reserved Instance? When each?
3. When is Spot the right answer, and how do you handle the interruption?
4. Why require IMDSv2?
5. What does an Auto Scaling group do when an AZ fails?
6. EC2 or ELB health checks? What goes wrong with the wrong one?
7. Target tracking or step scaling?
8. ALB or NLB?
9. What is cross-zone load balancing, and when does it cost money?
10. How would you cut the cost of a web fleet?

Now you may read `_harness/awslib/ec2types.py`, `purchasing.py`, `scaling.py` and `elb.py` — compare them with your drills 01–05.

# Week 00 — Foundations & exam technique

Before you design anything on AWS you need three things: a clear picture of how
the exam asks questions, a feel for where AWS resources live and how they fail,
and safe habits for talking to AWS from code. This week gives you all three.
Everything graded runs offline against a fake AWS (moto), so nothing here can
cost money or touch a real account.

## Goals

By the end of the week you can:

- read any ARN and say which service, Region, account and resource it names;
- reason about availability with numbers: nines to minutes, series versus parallel,
  and sizing a fleet to survive the loss of an Availability Zone;
- say whether a resource is global, Regional or zonal, and pick a Region for the
  right reasons;
- say who secures what under the shared responsibility model, and name the six
  Well-Architected pillars;
- read an IP address and a CIDR block: how many addresses it holds, whether an
  address is inside it, and how many a subnet leaves you after AWS reserves 5;
- run boto3 safely (credential chain, Regions, pagination, error codes) without
  ever risking a real account;
- explain the exam's format and attack a scenario: find the deciding requirement,
  cross out options that break a hard constraint, then choose.

## Your week

About 6–8 hours. There is no milestone this week.

1. **Concepts, about 3 h.** Read `concepts/01` to `06` in order. Note 06 is a
   networking primer (IP addresses, CIDR, subnets); skim it if you already know
   these. Run both demos: `python concepts/demo_availability.py` and
   `python concepts/demo_boto3_basics.py`.
2. **Drills, about 2.5 h.** `python practice/exercises.py` until it shows 10/10.
   Run one drill with `python practice/exercises.py 3`. Read the hint before you
   look at `practice/solutions.py`.
3. **Quiz, about 45 min.** `python quiz.py --week 0 -n 15` until you score 80 %
   or more.
4. **Lab, optional, about 1 h.** `lab/LAB.md`. It uses a real AWS account, so read
   the account-safety section first. Skip it if you prefer; nothing else depends on it.

Before week 01, read `_harness/awslib/policy_eval.py`? **No** — it is week 01's answer key.

## Exam tasks covered

| Id | Task statement | Notes |
|---|---|---|
| 1.1 | Design secure access to AWS resources | 01, 03, 05 |
| 1.2 | Design secure workloads and applications | 03 |
| 1.3 | Determine appropriate data security controls | 03 |
| 2.2 | Design highly available and/or fault-tolerant architectures | 01, 02, 04 |
| 3.2 | Design high-performing and elastic compute solutions | 01 |
| 3.4 | Determine high-performing and/or scalable network architectures | 02, 06 |
| 4.2 | Design cost-optimized compute solutions | 01 |
| 4.4 | Design cost-optimized network architectures | 05 |

## Service comparison

Where can a resource live? Pick the smallest thing that meets the need.

| Location | What it is | Latency | When to use it |
|---|---|---|---|
| Region | geographic area with several isolated AZs | baseline | where the workload runs; compliance boundary |
| Availability Zone | one or more data-centre facilities in a Region | very low to other AZs in the Region | spread across at least 2 for high availability |
| Local Zone | Region extension in a big city, fewer services | very low to that city | latency-sensitive apps near one city |
| Wavelength Zone | AWS compute inside a 5G carrier network | lowest for mobile devices on that network | 5G apps, live video, AR/VR |
| Outposts | AWS-managed rack in your own data centre | local, no trip over the WAN | on-premises processing, residency on your site |
| Edge location | small site for CDN, DNS and acceleration | close to end users | CloudFront, Route 53, Global Accelerator |

## Interview questions

Practise answering each aloud in under two minutes.

1. What is an Availability Zone and why deploy across several?
2. How would you size a fleet to survive the loss of an AZ?
3. Explain the shared responsibility model for RDS versus EC2.
4. How does boto3 find credentials, and which way is safest on EC2?
5. Why do you need pagination when listing S3?
6. What does data transfer cost between AZs versus out to the internet?
7. What are the six Well-Architected pillars?
8. Why is 99.99 % availability hard to reach with a single database?
9. What does `10.0.1.0/24` mean, and how many instances fit in that subnet on AWS?

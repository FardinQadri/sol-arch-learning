# Week 02 — Amazon VPC networking

## Goals

By the end of this week you can:

1. Plan a VPC's address space: CIDR blocks, reserved addresses, aligned subnets, room to grow.
2. Make a subnet public, private or isolated with routes, and explain why it is the routes that decide.
3. Give private subnets safe outbound access with NAT gateways, and know the cost and availability trade-offs.
4. Control traffic with security groups and network ACLs, and read VPC Flow Logs.
5. Reach AWS services privately with gateway endpoints, interface endpoints and PrivateLink.
6. Connect VPCs and on-premises networks with peering, Transit Gateway and Site-to-Site VPN.

## Your week

About 10–12 hours. Do the steps in order.

1. Concept notes 01–05 and the two demos in `concepts/` (~3 h). Run the demos:
   `python concepts/demo_vpc_in_moto.py` and `python concepts/demo_packet_paths.py`.
2. Drills: `python practice/exercises.py` (~3 h). Drills 01–05 are small models you build yourself: address maths,
   a subnet planner, a route lookup, the two firewalls, peering vs Transit Gateway. Drills 06–10 use boto3
   against a fake AWS. Do them in order.
3. Quiz: `python quiz.py --week 2 -n 30` until you score 80 % or more (~1.5 h).
4. Milestone M02: the course project's network (~2–3 h). See `course_project/milestones/M02.md`.
5. Optional lab (~1 h, about 0.05 USD): `lab/LAB.md`. Build a VPC, add one NAT gateway for under 30 minutes, tear it all down.

## Exam tasks covered

| Task | Title |
|---|---|
| 1.2 | Design secure workloads and applications |
| 2.2 | Design highly available and/or fault-tolerant architectures |
| 3.4 | Determine high-performing and/or scalable network architectures |
| 4.4 | Design cost-optimized network architectures |

Task 3.4 is the main target: subnet tiers, routing, IP addressing, network connection options.
Task 1.2 appears through security groups, network ACLs and endpoints. Task 2.2 is one NAT gateway per AZ and
redundant links. Task 4.4 is the cost of NAT, endpoints, Transit Gateway and data transfer.

## Service comparison

| Option | What it does | Direction | Cost | Use it when |
|---|---|---|---|---|
| Internet gateway | Two-way door to the internet | In and out | Free | Public subnets |
| NAT gateway | Lets private subnets call out | Out only | Hourly + per GB + IPv4 | Private instances need the internet |
| Gateway endpoint | Private path to S3 or DynamoDB | Out | Free | Private instances use S3 or DynamoDB |
| Interface endpoint | Private IP for most AWS services (PrivateLink) | Out | Hourly per AZ + per GB | Other AWS services, on-premises access, SaaS |
| VPC peering | Direct link between two VPCs | Both | Data transfer only | Few VPCs, no transit needed |
| Transit Gateway | Regional hub for many VPCs and sites | Both | Per attachment-hour + per GB | Many VPCs, transitive routing, segmentation |

## Interview questions

Answer each out loud in under two minutes.

1. Walk through how a packet from a private instance reaches the internet.
2. What is the difference between a security group and a network ACL?
3. Why do you deploy one NAT gateway per AZ?
4. How do private instances reach S3 without a NAT gateway?
5. When would you pick Transit Gateway over VPC peering?
6. What breaks when two VPCs' CIDR ranges overlap?
7. How would you block one malicious IP range?
8. How do you debug a connection timeout in a VPC?
9. How do you make a subnet public?
10. How much does a NAT gateway cost, and how would you cut it?

Now you may read `_harness/awslib/cidr.py` and `netsim.py` — compare them with your drills 01–05.

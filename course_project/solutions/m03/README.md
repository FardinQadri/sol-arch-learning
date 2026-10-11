# shortly-infra

The infrastructure-as-code for Shortly, the URL shortener you build up across the course. Each milestone adds one layer of CloudFormation templates, with parameter files for the lab and prod environments.

## Layers

| Layer | What it holds | Milestone |
|-------|---------------|-----------|
| `iam` | Roles for the app, the click consumer, the deployer and the auditor | M01 |
| `network` | VPC, three subnet tiers in two AZs, NAT, security groups, S3/DynamoDB endpoints, flow logs | M02 |
| `compute` | Application Load Balancer, launch template (IMDSv2), Auto Scaling group, listener rules | M03 |

## Network plan

VPC `10.20.0.0/16` in two Availability Zones (A = first AZ of the Region, B = second). Biggest subnets first, so every block stays aligned.

| Subnet | Tier | AZ | CIDR | Usable IPs |
|---|---|---|---|---|
| AppSubnetA | app (private, via NAT) | A | 10.20.0.0/22 | 1,019 |
| AppSubnetB | app (private, via NAT) | B | 10.20.4.0/22 | 1,019 |
| PublicSubnetA | public (ALB, NAT) | A | 10.20.8.0/24 | 251 |
| PublicSubnetB | public (ALB, NAT) | B | 10.20.9.0/24 | 251 |
| DataSubnetA | data (no internet) | A | 10.20.10.0/24 | 251 |
| DataSubnetB | data (no internet) | B | 10.20.11.0/24 | 251 |

`10.20.12.0` – `10.20.255.255` stays free for later tiers.

NAT: prod runs one NAT gateway per AZ (an AZ failure cannot cut off the other AZ); lab runs one, shared by both app subnets, to halve the hourly cost.

## Compute

The `compute` stack imports the IAM and network exports and creates an internet-facing Application Load Balancer in the public subnets, a target group that health-checks `/healthz` on port 8000, and an Auto Scaling group in the app subnets. Instances come from one launch template: Graviton, Amazon Linux 2023 (AMI id read from the public SSM parameter), IMDSv2 required, no SSH key (use Session Manager), and the Shortly app from `app/app.py` written to disk by user data and run by systemd. prod keeps 2 to 6 instances, lab 1 to 2; a target-tracking policy holds average CPU near 50 %.

The listener is HTTP only for now (M07 adds HTTPS). `/healthz` is answered with a 404 at the load balancer, because the health checks go straight to the instances and never through listener rules.

## Check it

Run the milestone tests with the course venv:

```
python run_milestone.py 2
```

## Deploy (optional)

Deploying to a real account is optional; see the course's `DEPLOY.md`. The network stack costs money while it runs (NAT gateways and their public IPv4 addresses are billed by the hour).

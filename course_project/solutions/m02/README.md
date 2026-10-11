# shortly-infra

The infrastructure-as-code for Shortly, the URL shortener you build up across the course. Each milestone adds one layer of CloudFormation templates, with parameter files for the lab and prod environments.

## Layers

| Layer | What it holds | Milestone |
|-------|---------------|-----------|
| `iam` | Roles for the app, the click consumer, the deployer and the auditor | M01 |
| `network` | VPC, three subnet tiers in two AZs, NAT, security groups, S3/DynamoDB endpoints, flow logs | M02 |

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

## Check it

Run the milestone tests with the course venv:

```
python run_milestone.py 2
```

## Deploy (optional)

Deploying to a real account is optional; see the course's `DEPLOY.md`. The network stack costs money while it runs (NAT gateways and their public IPv4 addresses are billed by the hour).

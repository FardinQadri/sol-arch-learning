Exam tasks: 3.4, 2.2, 4.4

# 02 — Routing, internet access and NAT

## What it is

Routing decides where a packet goes next. Every subnet is tied to one **route
table**. The table is a list of rules: "traffic for this range goes to that target".

The targets are the gateways. This note covers the ones that reach the internet:

- **Internet gateway (IGW):** two-way door to the internet.
- **NAT gateway:** one-way door. Private instances can call out. Nobody can call in.
- **Egress-only internet gateway:** the one-way door for IPv6.
- **NAT instance:** the old do-it-yourself NAT. Legacy.

## How it works

### Route tables

- A VPC always has a **main route table**. Any subnet you do not explicitly associate with another table uses it. New subnets join it automatically.
- A subnet is associated with **exactly one** route table. One route table can serve many subnets.
- Best practice: leave the main table alone and strict. Create custom tables for public and private subnets and associate them on purpose. A new subnet then cannot become public by accident.

### The local route

Every table has a **local route** for the VPC's own CIDR. It sends VPC-internal
traffic straight to its target inside the VPC. It is there from the start, it
has the highest priority, and you cannot delete it.

Because of the local route, **all subnets in a VPC can reach each other by
default**, whatever their route tables say. Only security groups and network
ACLs can stop that.

Changed (newer than the 2022 exam guide): you can now replace the local route's target with an
appliance, such as a firewall, to inspect traffic inside the VPC. Know it exists. The exam answer
is still "local always wins".

### Longest-prefix match

When more than one route matches, **the most specific route wins**. Specific means
the longest prefix (the biggest `/` number).

Example table:

| Destination | Target |
|---|---|
| `10.0.0.0/16` | local |
| `10.1.0.0/16` | pcx-peer |
| `0.0.0.0/0` | nat-gw |

A packet to `10.1.4.9` matches both `10.1.0.0/16` and `0.0.0.0/0`. The `/16` is
longer, so it goes to the peer. A packet to `8.8.8.8` only matches the default
route, so it goes to the NAT gateway. A packet that matches nothing is dropped.

If two routes have the same prefix, a static route beats a prefix-list route, and
both beat a propagated route (from a VPN or Direct Connect). Drill 03 builds this lookup.

### Internet gateway

An IGW is attached to a VPC (only one per VPC). It is horizontally scaled,
redundant, and has no bandwidth limit and **no charge**.

For an instance to talk to the internet both must be true:

1. Its subnet's route table has `0.0.0.0/0 → igw-…`. (This is what makes the subnet public.)
2. The instance has a **public IPv4 address** or Elastic IP. The IGW translates the private address to the public one, one-to-one.

Missing either one is the classic "I can't reach my instance" problem. Security
groups and network ACLs must allow it too.

### NAT gateway

A private instance needs updates, packages and API calls, but must not accept
connections from outside. A **NAT gateway** does that.

How to set it up:

1. Create the NAT gateway **in a public subnet**.
2. A public NAT gateway needs an **Elastic IP** when you create it.
3. In the private subnet's route table add `0.0.0.0/0 → nat-…`.
4. The NAT gateway's own subnet has the usual `0.0.0.0/0 → igw-…`.

Traffic then flows: private instance → NAT gateway → internet gateway → internet.
Replies come back the same way. The NAT gateway only accepts replies to
connections that started inside.

Things to know:

- It is **managed**: it scales from 5 Gbps up to 100 Gbps. No patching.
- It supports TCP, UDP and ICMP.
- You **cannot attach a security group** to a NAT gateway. Use security groups on the instances behind it. Use network ACLs on its subnet.
- It is **zonal**. It sits in one AZ and is redundant only inside that AZ.
- **High availability = one NAT gateway per AZ.** Each private subnet's route table points to the NAT gateway in its own AZ. If one AZ fails, the other AZs keep their internet access. One shared NAT gateway is cheaper but it is a single point of failure, and traffic from other AZs pays cross-AZ data charges.
- A **private NAT gateway** has no Elastic IP. It is for talking to other private networks (on-premises or other VPCs) through a Transit Gateway or virtual private gateway. It cannot reach the internet: an IGW drops its traffic.

Changed: AWS now offers a **regional** NAT gateway mode. One gateway spans the AZs for you and
needs no public subnet. The exam answer is still "one zonal NAT gateway per AZ". No question
depends on the new mode.

### Egress-only internet gateway

IPv6 addresses are public. To let private IPv6 instances call out but block
inbound connections, use an **egress-only internet gateway**. Add the route
`::/0 → eigw-…`. It is IPv6 only, stateful, free (data transfer still applies).
For IPv4 outbound-only, use a NAT gateway. The two are the same idea for two IP versions.

### NAT instance (legacy)

A NAT instance is an ordinary EC2 instance that you set up to forward traffic.

- You must **disable the source/destination check** on it. An instance normally drops traffic that is neither from nor to itself. A NAT instance must forward such traffic.
- You manage patching, failover and size. Bandwidth depends on the instance type.
- It can use security groups, port forwarding and double as a bastion.
- The NAT AMI is built on an old Amazon Linux version and its maintenance support has ended. AWS recommends NAT gateways.

It still shows up in cost questions: a NAT instance can be cheaper for a tiny,
low-traffic lab. In production, choose the NAT gateway.

### Getting into private instances

You do not need a public IP, or any inbound port, to manage a private instance.

- **Bastion host (jump box):** a hardened instance in a public subnet. You SSH to it, then on to the private instance. You pay for it, patch it, and open port 22 to the internet (or to your office range).
- **AWS Systems Manager Session Manager:** a shell through the SSM agent. **No inbound ports, no bastion, no SSH keys.** Access is controlled by IAM and logged. The instance needs an IAM role (for example `AmazonSSMManagedInstanceCore`) and a path to the SSM service: NAT gateway or interface endpoints (note 04).

Exam rule: "access private instances securely without opening SSH" → Session Manager.

### Cost of NAT

A NAT gateway bills three ways:

| Item | Illustrative price |
|---|---|
| Hours it exists | 0.045 USD per hour |
| Data processed | 0.045 USD per GB |
| Its public IPv4 address | 0.005 USD per hour |

Prices are illustrative. The pattern is what matters: you pay for **every gigabyte**
that goes through, in either direction. Heavy traffic to S3 or DynamoDB through NAT is
the classic waste; a free gateway endpoint fixes it (note 04, drill 09).

Lab versus production:

- **Lab:** one NAT gateway, deleted when you finish. Never leave it running.
- **Production:** one per AZ for availability. Add endpoints to cut the bytes that flow through it.

## Numbers to know

- One IGW per VPC. IGW: no charge.
- NAT gateway: **5 Gbps**, scales to **100 Gbps**. Zonal. Up to 5 per AZ by default.
- NAT gateway cost: 0.045 USD/hour + 0.045 USD/GB (illustrative) + public IPv4 0.005 USD/hour.
- Route table limits: 500 non-propagated routes (adjustable), 200 route tables per VPC.
- Route to IGW: `0.0.0.0/0` (IPv4) or `::/0` (IPv6).

## When to choose it

| Need | Choose |
|---|---|
| Public web servers, two-way internet | Internet gateway + public IP |
| Private servers need to download updates | NAT gateway in a public subnet |
| Survive the loss of an AZ | One NAT gateway per AZ, each AZ routes to its own |
| Private IPv6 instances call out | Egress-only internet gateway |
| Lowest-cost tiny test, accept the work | NAT instance (legacy) |
| Shell access to private servers, no open ports | Session Manager |
| Private instances talk to S3 only | Gateway endpoint instead of NAT |

## Exam traps

- **NAT gateway in a private subnet.** Wrong. It must be in a public subnet, with a route to the IGW.
- **One NAT gateway for three AZs.** Works, but it is not highly available. "Highly available" means one per AZ.
- **Public subnet = instances reachable.** Not without a public IP and permissive security groups.
- **NAT for IPv6.** The answer is the egress-only internet gateway.
- **Private subnet with a route to IGW.** By definition that subnet is public.
- **Bastion host when the question says "no open ports" or "least operational overhead".** Pick Session Manager.
- **NAT instance without disabling the source/destination check.** It will not forward traffic.
- **Peering borrows a NAT.** A peered VPC cannot use your NAT gateway or IGW (note 05).
- **Security group on a NAT gateway.** Not supported.

## Cost angle

- The IGW and egress-only IGW cost nothing. The NAT gateway is the expensive part of many small VPCs.
- Idle NAT gateways bill for every hour. Three AZs means three hourly charges plus three IPv4 addresses.
- A shared single NAT gateway saves the hourly cost but adds cross-AZ data charges and risk. Pick it only for non-production.
- Biggest saving: send S3 and DynamoDB traffic through free gateway endpoints and keep it off NAT.
- Public IPv4 addresses cost 0.005 USD per hour each, in use or idle. Release unused Elastic IPs.

## Comparison

| | Internet gateway | NAT gateway | NAT instance | Egress-only IGW |
|---|---|---|---|---|
| Direction | Two-way | Outbound only | Outbound only | Outbound only |
| IP version | IPv4 and IPv6 | IPv4 | IPv4 | IPv6 only |
| Managed by | AWS | AWS | You | AWS |
| Availability | Built in | Per AZ; deploy one per AZ | You build failover | Built in |
| Security groups | No (on instances) | Not supported | Supported | Not supported |
| Cost | Free | Hourly + per GB + IPv4 | Instance + IPv4 | Free (data applies) |
| Use for | Public subnets | Private subnets, production | Tiny low-cost tests | Private IPv6 |

Now do drill 03 (routing) and drill 06 (build a VPC with boto3), then run `python concepts/demo_vpc_in_moto.py`.

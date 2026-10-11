Exam tasks: 3.4, 1.2

# 01 — The VPC, subnets and CIDR planning

## What it is

A **VPC** (Virtual Private Cloud) is your own private network inside AWS. You pick
its IP address range. Nothing gets in or out unless you build a path for it.

- A VPC lives in one **Region**. It can have subnets in every Availability Zone (AZ) of that Region.
- A **subnet** is a slice of the VPC's address range. A subnet lives in **exactly one AZ**. It never spans AZs.
- Resources such as EC2 instances, RDS databases and load balancers get a private IP from a subnet.

Think of it like this: the VPC is the building, the subnets are the floors you
rent in each wing (AZ), and route tables decide which doors are open.

This is the base for everything else this week. Notes 02 to 05 add the doors,
the guards and the bridges.

## How it works

### CIDR notation

A **CIDR block** such as `10.0.0.0/16` has two parts:

- the address `10.0.0.0`, and
- the prefix length `/16`: how many leading bits are fixed.

A smaller prefix number means a **bigger** block. `/16` is big, `/28` is tiny.
The number of addresses is `2^(32 − prefix)`.

| Prefix | Addresses | Usable in a subnet (minus 5) |
|---|---|---|
| /16 | 65,536 | 65,531 |
| /20 | 4,096 | 4,091 |
| /24 | 256 | 251 |
| /26 | 64 | 59 |
| /28 | 16 | 11 |

AWS allows IPv4 VPCs and subnets from **/16 down to /28**. Nothing bigger,
nothing smaller.

### Private ranges (RFC 1918)

Use these for a VPC. AWS recommends them:

- `10.0.0.0/8`
- `172.16.0.0/12`
- `192.168.0.0/16`

A VPC cannot use `0.0.0.0/8`, `127.0.0.0/8`, `169.254.0.0/16` or `224.0.0.0/4`.
Avoid `172.17.0.0/16`: some AWS services use it.

### Secondary CIDR blocks

Ran out of addresses? You cannot resize a block. You **add a secondary CIDR
block** to the VPC instead.

- Same size rules (/16 to /28). It must not overlap any block the VPC already has.
- A VPC holds 5 IPv4 blocks by default (primary plus secondary). You can raise this to 50.
- You can never remove the primary block.

### The 5 reserved addresses

AWS keeps **5 addresses in every subnet**. You cannot use them.

| Address in `10.0.1.0/24` | Role |
|---|---|
| `10.0.1.0` | Network address |
| `10.0.1.1` | VPC router |
| `10.0.1.2` | Amazon DNS (base address + 2) |
| `10.0.1.3` | Reserved for future use |
| `10.0.1.255` | Broadcast (not supported, still reserved) |

Worked example, a /24: 256 addresses − 5 = **251 usable**.

Worked example, a /28 such as `10.0.5.16/28`: the range is `.16` to `.31`. That is 16
addresses. Reserved: `.16`, `.17`, `.18`, `.19` and `.31`. Usable: `.20` to `.30`, which
is **11**. The demo prints these for you.

The exam loves this: a /28 does not hold 16 instances. It holds 11.

### Public, private and isolated subnets

There is **no "public" checkbox**. A subnet is defined by its route table:

- **Public subnet:** its route table has `0.0.0.0/0 → internet gateway`. Instances there also need a public IPv4 address (or Elastic IP) to be reachable.
- **Private subnet:** no route to an internet gateway. It may have `0.0.0.0/0 → NAT gateway` for outbound-only access.
- **Isolated subnet:** no route to the internet at all, not even through NAT. Only the `local` route, plus maybe endpoints. Typical for databases.

Change the route table and you change the type of the subnet. Note 02 shows how.

### A typical three-tier layout

| Tier | Subnet type | What lives there |
|---|---|---|
| Web | Public | Load balancer, NAT gateway, (bastion host) |
| App | Private | Application servers |
| Data | Isolated | Databases |

Repeat each tier in at least two AZs. One subnet per tier per AZ.

### Sizing method

1. List the tiers and AZs. Count the instances each subnet must hold now, plus growth.
2. Add 5 to each subnet for the reserved addresses.
3. Round up to the next power of two. That gives the prefix.
4. Place the **biggest subnets first**, each starting at an address that is a multiple of its own size. A /24 starts at x.x.N.0; a /22 starts where the third octet is a multiple of 4 (10.0.0.0, 10.0.4.0, 10.0.8.0 …). This is called being *aligned*.
5. Leave spare space for new tiers and new AZs.

Why biggest first? A big block that starts in the wrong place leaves a gap you
cannot reuse. Drill 02 makes you build this planner.

Other planning rules:

- **Plan for growth.** Moving a database to a bigger subnet means downtime. Pick a /16 VPC and leave plenty unassigned.
- **Never overlap with networks you may connect to.** Peering and Transit Gateway need non-overlapping ranges (note 05). So do VPNs to your office. Keep a company-wide address plan, so every VPC gets its own slice.
- **Do not make subnets too small.** Load balancers, endpoints and Lambda in a VPC all take IPs from your subnets.

### IPv6 in one paragraph

A VPC can also have IPv6. AWS gives you a block, for example a **/56**, and you
cannot pick the range. Subnets get a **/64**. IPv6 addresses are all public and
routable, so a "private" IPv6 subnet is made with an egress-only internet
gateway (note 02), not NAT. A VPC can hold 5 IPv6 blocks by default.

### The default VPC

Every Region comes with a **default VPC**:

- CIDR `172.31.0.0/16`.
- One **/20** public subnet per AZ (4,096 addresses each).
- An internet gateway, and a main route table with `0.0.0.0/0 → IGW`.
- Instances launched there get a public IPv4 address automatically.

It is great for quick tests and bad for production. Everything is public by
default, the ranges are the same in every account (so they overlap when you
peer), and you did not design it. **Production uses its own VPC.**

Quotas to recognise: 5 VPCs per Region and 200 subnets per VPC by default. Both
can be raised.

## Numbers to know

- IPv4 VPC and subnet sizes: **/16 to /28**.
- **5** reserved addresses per subnet. A /28 gives 11 usable. A /24 gives 251.
- A subnet lives in **one AZ**. A VPC spans the AZs of **one Region**.
- **5** IPv4 CIDR blocks per VPC by default (primary + secondary).
- Default VPC: `172.31.0.0/16`, a /20 subnet per AZ.
- IPv6: VPC /56 (Amazon-provided), subnet /64.
- 5 VPCs per Region, 200 subnets per VPC (defaults; adjustable).

## When to choose it

| Need | Choose |
|---|---|
| A quick experiment | Default VPC |
| Production workload | Your own VPC with a planned /16 (or smaller) |
| Out of addresses | Add a secondary CIDR block |
| Web servers reachable from the internet | Public subnet |
| App servers that call out but must not be reachable | Private subnet + NAT gateway |
| Databases that never need the internet | Isolated subnet |
| Different failure domains | Subnets in at least two AZs |

## Exam traps

- **"A subnet spans two AZs."** False. One subnet, one AZ. For two AZs you need two subnets.
- **"A VPC is zonal."** False. A VPC is Regional.
- **"A /28 has 16 usable IPs."** False. 16 − 5 = 11.
- **"Public subnet" is a setting.** It is not. It is a route to an internet gateway. A subnet with no such route is private even if you named it "public".
- **A route to the IGW is not enough.** The instance also needs a public IPv4 address or an Elastic IP.
- **You cannot resize a CIDR block.** Add a secondary block.
- **Overlapping CIDRs cannot be peered.** Re-address one VPC, or expose just the one service with PrivateLink (note 04).
- **Default VPC for production** is almost always the wrong answer.
- **IPv6 does not use NAT.** Outbound-only IPv6 uses an egress-only internet gateway.

## Cost angle

- A VPC, subnets, route tables, security groups and network ACLs are **free**.
- Cost starts with what you attach: NAT gateways, endpoints, Transit Gateway, VPN, public IPv4 addresses (0.005 USD per hour each, in use or idle).
- Good CIDR planning is a cost control too. Re-addressing a live VPC to allow peering is expensive in time and risk.
- Traffic between AZs costs money (0.01 USD per GB, charged out and in). Spreading tiers over AZs buys availability and costs a little data transfer.

## Comparison

| | Public subnet | Private subnet | Isolated subnet |
|---|---|---|---|
| Route to IGW | Yes | No | No |
| Route to NAT gateway | No | Usually yes | No |
| Reachable from the internet | Yes, with a public IP | No | No |
| Can start outbound internet calls | Yes | Yes, via NAT | No |
| Typical use | Load balancers, NAT | App servers | Databases |
| Reaches AWS services | Via IGW or endpoint | Via NAT or endpoint | Via endpoint only |

Now do drill 01 (address maths) and drill 02 (subnet planner), then run `python concepts/demo_vpc_in_moto.py`.

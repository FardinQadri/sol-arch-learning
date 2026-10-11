Exam tasks: 3.4, 2.2, 4.4

# 05 — Connecting VPCs and networks

## What it is

One VPC is rarely enough. You will have several VPCs (per team, per environment,
per account) and an office or data centre to join. AWS gives you these links:

- **VPC peering:** a direct, private link between two VPCs.
- **AWS Transit Gateway (TGW):** a Regional hub. Attach many VPCs and networks to it.
- **Site-to-Site VPN:** an encrypted tunnel over the internet to your on-premises network.
- **AWS Direct Connect:** a private physical line to AWS. Covered in week 07.
- **PrivateLink:** exposes one service, not a whole network (note 04).
- **AWS RAM subnet sharing:** several accounts use the same VPC (week 01 introduced RAM).
- **VPC Lattice:** a managed application-networking service that connects services across VPCs and accounts. One line to remember; it is newer than the 2022 guide.

## How it works

### VPC peering

A peering connection links **two** VPCs. Traffic stays on the AWS network.

- Works across **accounts** and across **Regions** (inter-Region peering).
- To set it up: one side sends a request, the other **accepts** (a request expires if nobody accepts it within 7 days).
- Then **both sides add routes**: destination = the other VPC's CIDR, target = `pcx-…`. Security groups may need new rules too. A security group can reference a group in a peered VPC.
- **No overlapping CIDRs.** Not even unused secondary blocks. If the ranges overlap, the peering cannot be created.
- **Not transitive.** If A peers with B and B peers with C, then A cannot reach C through B. You must peer A and C too.
- **No edge-to-edge routing.** A peer cannot use your internet gateway, NAT gateway, VPN, Direct Connect or gateway endpoint. Each VPC needs its own.
- No single point of failure and no bandwidth bottleneck. It is not a gateway or a VPN.

#### The full-mesh problem

To let `n` VPCs all talk to each other with peering you need `n × (n − 1) / 2`
connections, each with routes on both sides.

| VPCs | Peering connections |
|---|---|
| 3 | 3 |
| 5 | 10 |
| 10 | 45 |
| 20 | 190 |

It grows with the square of `n`. At some point it is unmanageable. That is
where Transit Gateway comes in. Drill 05 makes you compute this and decide.

### Transit Gateway

A **Transit Gateway** is a Regional virtual router. You attach VPCs and other
networks to it. Each attachment gets routes to the TGW.

- **Transitive.** Attached networks can reach each other through the hub. You need one attachment per VPC, so `n` attachments instead of `n × (n − 1) / 2` peerings.
- **Route tables** on the TGW control which attachment can reach which. Each attachment is associated with one table; routes can propagate into one or more tables. Use separate tables to **segment**: for example, let dev VPCs reach shared services but not production.
- **Attachment types** include VPC, Site-to-Site VPN, Direct Connect gateway, TGW peering and others.
- **Inter-Region peering:** connect two Transit Gateways in different Regions. Routes between them are static.
- **Enable a subnet in each AZ** you want reachable from the TGW. Each VPC attachment uses one subnet per AZ.
- It is Regional. A VPC attaches to a TGW in its own Region.
- Share it with other accounts using AWS RAM.
- A gateway endpoint does not work through a TGW (note 04). Interface endpoints do.

A TGW is also the usual place to end many VPN connections, so a branch office
reaches every VPC through one hub.

### Sharing subnets instead (AWS RAM)

Another way to avoid many VPCs: put workloads from several accounts into **one VPC**.
The owner account **shares subnets** with other accounts using AWS RAM. Each
account launches its own resources into the shared subnets and pays for them,
but the network is one. No peering, no TGW and no charges for either (normal cross-AZ data rates still apply).

| Approach | Good for |
|---|---|
| RAM subnet sharing | One network, many accounts (Organizations) |
| Peering | A few VPCs, simple, cheapest |
| Transit Gateway | Many VPCs, transitive, central control |

### Site-to-Site VPN

A **Site-to-Site VPN** connects your on-premises network to AWS over the
**public internet**, **encrypted** with IPsec.

- You have a **customer gateway** (your router/firewall) and a **virtual private gateway (VGW)** or a **Transit Gateway** on the AWS side. A VGW serves one VPC; a TGW serves many.
- Each VPN connection has **two tunnels** in two AZs, for redundancy. Configure both.
- A standard tunnel carries up to **1.25 Gbps**. Newer large-bandwidth tunnels reach 5 Gbps, but only on a Transit Gateway or Cloud WAN.
- With dynamic (BGP) routing on a TGW, equal-cost multipath (ECMP) can add several tunnels together for more bandwidth. A VGW cannot.
- It is quick to set up (minutes) and cheap. But performance depends on the internet: latency and bandwidth vary.
- IPv6 over VPN needs a TGW (a virtual private gateway does not support it).

### Direct Connect (pointer)

**Direct Connect (DX)** is a dedicated private network line from your site to AWS.
It gives steady latency and bandwidth and takes weeks to order. It is **not
encrypted by default**. A common design is **DX as the main path with a VPN as the
backup**, or a VPN over DX. Details come in week 07 (hybrid and migration).

### Choosing

Ask four questions:

1. **How many networks?** Two: peering. Many: TGW.
2. **Do they need to reach each other through a middle one (transit)?** Yes: TGW. Peering cannot.
3. **Is the other side AWS or on-premises?** On-premises: VPN or DX (often through a TGW).
4. **Do I need to share a whole network or one service?** One service: PrivateLink. It also tolerates overlapping CIDRs.

## Numbers to know

- Peering pending-acceptance request: expires after **7 days**.
- Full mesh: **n × (n − 1) / 2** peerings. 5 VPCs = 10. 10 VPCs = 45.
- VPN: **2 tunnels** per connection; **1.25 Gbps** per standard tunnel; 5 Gbps for large-bandwidth tunnels (TGW or Cloud WAN only).
- VPN connections per Region: 50 (default).
- Transit Gateway: 0.05 USD per attachment-hour, 0.02 USD per GB processed.
- Site-to-Site VPN: 0.05 USD per connection-hour.
- Peering data: free in the same AZ; 0.01 USD per GB each way across AZs in a Region.
- Inter-Region data transfer: 0.02 USD per GB, sender pays.
- MTU: 9001 for peering in a Region; 8500 for inter-Region peering and for TGW (1500 over VPN).

## When to choose it

| Need | Choose |
|---|---|
| Two VPCs, simple, lowest cost | VPC peering |
| Five or more VPCs that all talk to each other | Transit Gateway |
| Isolate dev from prod but share a services VPC | Transit Gateway with separate route tables |
| VPCs in two Regions | Inter-Region peering, or TGW peering |
| Branch office to AWS, fast and cheap | Site-to-Site VPN |
| One VPN reaching many VPCs | VPN attached to a Transit Gateway |
| Steady high bandwidth to on-premises | Direct Connect (week 07) |
| Many accounts in one network | RAM subnet sharing |
| Expose one service, CIDRs overlap | PrivateLink |

## Exam traps

- **Transitive peering.** "A peers B, B peers C, so A reaches C." False. This is the most-tested trap.
- **Overlapping CIDRs** between peered VPCs. Not allowed. Re-address, or use PrivateLink for a single service.
- **Routing only on one side.** Peering needs routes in both VPCs' route tables.
- **Using the peer's NAT gateway or internet gateway.** Not allowed. No edge-to-edge routing.
- **Gateway endpoint reached from a peered VPC in another Region or on-premises.** Not possible.
- **Single VPN tunnel.** A VPN connection has two tunnels. Use both for high availability.
- **VPN is private by default.** It is encrypted but travels over the public internet. Direct Connect is private but not encrypted.
- **"Hundreds of VPCs, full mesh of peering."** The answer is the Transit Gateway.
- **Transit Gateway across Regions as one gateway.** A TGW is Regional. Connect Regions with TGW peering.

## Cost angle

- **Peering** has no hourly charge. You pay only for data: free in the same AZ, 0.01 USD per GB each way across AZs, and inter-Region rates between Regions.
- **Transit Gateway** costs 0.05 USD per attachment per hour and 0.02 USD per GB processed. Ten VPCs is ten attachments billed all month, plus every gigabyte that crosses it. Peering is cheaper for few VPCs and high traffic; the TGW wins on operations when there are many VPCs.
- **VPN** costs 0.05 USD per connection-hour plus data transfer out to the internet.
- A VPN attached to a TGW pays an attachment charge too.
- RAM subnet sharing has no extra charge and no cross-VPC data fees. It is the cheapest way to connect accounts, if one network suits you.
- Moving data across AZs or Regions through any of these costs money. Keep chatty services in the same AZ when the design allows.

## Comparison

| | VPC peering | Transit Gateway | Site-to-Site VPN | PrivateLink |
|---|---|---|---|---|
| Connects | Two VPCs | Many VPCs and sites | VPC/TGW to on-premises | One service to consumers |
| Transitive | No | Yes | Via TGW | No (one way) |
| Overlapping CIDRs | Not allowed | Cannot route between them | Cannot route between them | Allowed |
| Bandwidth | No bottleneck | Elastic | 1.25 Gbps per tunnel | Per endpoint ENI |
| Encryption | Private AWS network | Private AWS network | IPsec over internet | Private AWS network |
| Cost | Data only | Per attachment-hour + per GB | Per connection-hour + data | Per endpoint-hour + per GB |
| Best for | Few VPCs, simple | Hub and spoke, many VPCs | Fast hybrid link | Service exposure, SaaS |

Now do drill 05 (peering or a transit gateway) and drill 10 (does the traffic get through), then run `python concepts/demo_packet_paths.py`.

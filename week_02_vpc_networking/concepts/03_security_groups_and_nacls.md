Exam tasks: 1.2

# 03 — Security groups, network ACLs and Flow Logs

## What it is

Two firewalls work at different levels of a VPC:

- A **security group (SG)** sits at the instance level, on the network interface (ENI). It is **stateful** and only **allows**.
- A **network ACL (NACL)** sits at the subnet boundary. It is **stateless** and has **allow and deny** rules.

Route tables decide whether a path exists. These two decide whether traffic may
use it. **VPC Flow Logs** record what was accepted or rejected, so you can see
what happened.

This is the core of task 1.2 for networking: "control ports, protocols and
network traffic". Drill 04 builds both firewalls. Drill 07 builds SGs that
reference each other.

## How it works

### Security groups

- Attached to **network interfaces**. An instance can have several SGs, and the rules are combined (any allow wins). By default an ENI can have 5 SGs (up to 16 on request).
- **Allow rules only.** You cannot write a deny rule.
- **Stateful.** If a request is allowed in, the reply is allowed out automatically. The reverse is also true. You never open ports for replies.
- A new SG has **no inbound rules** (all inbound denied) and one **outbound allow-all** rule.
- The **default SG** of a VPC allows all traffic from members of the same SG and all outbound. You cannot delete it, but you can change its rules.
- A rule's source can be a CIDR range, a prefix list, or **another security group**.

#### Referencing another security group

Instead of an IP range, say "allow port 3306 from the app tier's SG". Any
instance wearing that SG is allowed, whatever its IP, and new instances are
covered automatically. This is the standard pattern for tiers:

| SG | Inbound rule |
|---|---|
| `alb-sg` | 443 from `0.0.0.0/0` |
| `app-sg` | 8080 from `alb-sg` |
| `db-sg` | 5432 from `app-sg` |

Nobody on the internet can reach the database or the app directly. You can
reference SGs in the same VPC, in a peered VPC, or (for inbound) through a Transit Gateway.

SG quotas: 60 inbound and 60 outbound rules per SG, 2,500 SGs per Region (defaults).

### Network ACLs

- One NACL per subnet. One NACL can serve many subnets.
- Rules are **numbered, 1 to 32766**. They are checked **lowest number first**. The first rule that matches decides, and checking stops. (Leave gaps: 100, 200, 300.)
- Rules can **allow or deny**.
- Every NACL ends with an unchangeable `*` rule: **deny everything** that no rule matched.
- **Stateless.** The reply is a new packet and is checked on its own. You must allow it explicitly, in both directions.
- It applies at the subnet boundary. Traffic between two instances **inside the same subnet** does not cross the NACL.
- Defaults: 20 inbound and 20 outbound rules per NACL (adjustable), 200 NACLs per VPC.

#### Default vs custom NACL

| | Default NACL | New custom NACL |
|---|---|---|
| Starting rules | Allow all in and out (rule 100) | **Only** the `*` deny |
| Result | Everything passes | **Everything blocked** until you add allows |
| Gets attached to | Subnets without another NACL | Only the subnets you associate |

The trap: you create a custom NACL, associate it with a subnet, and the subnet
goes dark. Add allow rules for both directions.

### Ephemeral ports

When a client connects to a server on port 443, the client uses a random
high-numbered port as its source. That is the **ephemeral port**. The reply goes
back to *that* port.

Because a NACL is stateless, the server subnet's NACL needs:

- **Inbound** allow for the service port (443).
- **Outbound** allow for the client's ephemeral ports.

And the client subnet's NACL needs the mirror image. Ranges to know:

| Client | Ephemeral ports |
|---|---|
| Linux | 32768 – 61000 |
| Windows Server 2008 and later | 49152 – 65535 |
| Load balancers, NAT gateways, Lambda | 1024 – 65535 |

When you do not know the client, **open 1024 – 65535**. Drill 04 shows what
breaks when you forget. A security group never has this problem, because it is stateful.

### Layering the two

- Do **most control with security groups**: tier-to-tier rules, referencing SGs.
- Use the **NACL as a subnet-wide backstop**: its special power is the **deny**.
  Example: an attacker's range `198.51.100.0/24` keeps probing. A security group cannot deny, so add a NACL rule `90 deny 198.51.100.0/24` above your allow rules.
- A request needs to pass **both**: the NACL at the subnet edge, then the SG at the instance. A deny at either layer blocks it.

Neither SGs nor NACLs filter some AWS traffic: Amazon DNS, DHCP, instance
metadata and the VPC router addresses.

### VPC Flow Logs

Flow Logs record IP traffic metadata (not packet contents) for a VPC, a subnet or a single ENI.

- Each record shows source, destination, ports, protocol, bytes and an action: **ACCEPT** or **REJECT**.
- Choose to log accepted traffic, rejected traffic or all.
- Destinations: **CloudWatch Logs, Amazon S3 or Amazon Data Firehose** (Firehose is newer than the 2022 guide).
- Logs are **not real time**. Expect a delay of minutes. They do not slow your traffic.
- You cannot edit a flow log after it exists. Delete it and create a new one.
- They also cover ENIs of ELB, RDS, NAT gateways and Transit Gateways.

**Not captured:** traffic to the Amazon DNS server, instance metadata
(`169.254.169.254`), the Time Sync address, DHCP, Windows license activation
and the VPC router's reserved address.

#### Reading a REJECT

A `REJECT` means a security group **or** a NACL refused the packet. The log does
not say which. Work it out:

1. Does the matching ACCEPT for the same flow exist in the opposite direction? If requests are ACCEPT but replies are REJECT, suspect a **NACL** that forgets ephemeral ports (SGs would let replies back).
2. Is the REJECT at the destination ENI? Then check the SG's inbound rule and the subnet's NACL.
3. Check the NACL rule order. A deny with a low number may sit above your allow.

Flow Logs are the answer to "why can't A reach B?" and "who was scanning us?".

## Numbers to know

- SG: 60 inbound + 60 outbound rules; 5 SGs per ENI (adjustable to 16); 2,500 SGs per Region.
- NACL: rule numbers **1 to 32766**; 20 + 20 rules by default; 200 per VPC.
- Ephemeral ports: Linux 32768–61000; Windows 49152–65535; open **1024–65535** to cover all.
- SGs and NACLs: **no charge**.
- Flow Logs destinations: CloudWatch Logs, S3, Firehose.

## When to choose it

| Need | Choose |
|---|---|
| Let the web tier talk to the app tier only | Security group referencing the web SG |
| Block one hostile IP range for a whole subnet | NACL deny rule |
| Explicitly deny a single port | NACL (SGs cannot deny) |
| Find out why a connection times out | Flow Logs, then check SG and NACL |
| Audit rejected traffic cheaply over time | Flow Logs to S3 |
| Search logs with Logs Insights or alarm on them | Flow Logs to CloudWatch Logs |
| Default protection for everything | SG with minimum rules; leave the default NACL |

## Exam traps

- **"Block this IP address" with a security group.** Impossible. SGs have no deny. Use a NACL.
- **Forgetting the return traffic in a NACL.** Stateless means replies need their own allow rule on ephemeral ports.
- **Rule order.** A deny at rule 200 never fires if rule 100 already allowed the traffic.
- **New custom NACL.** It denies everything. The default NACL allows everything.
- **"The SG allows it but it still fails."** Look at the NACL, the route table and the OS firewall too.
- **Outbound rules in an SG.** Not needed for replies. They matter only for connections the instance starts.
- **Flow Logs capture packet contents.** They do not. Metadata only.
- **Flow Logs show metadata traffic.** Metadata, DNS and DHCP are not logged.
- **A SG attached to a NAT gateway.** Not supported.
- **Same-subnet traffic blocked by a NACL.** The NACL does not see it. Only SGs do.

## Cost angle

- Security groups and NACLs are free. Use as many as you need.
- Flow Logs add log ingestion and archival charges (see CloudWatch Logs or S3 pricing). They do not slow your traffic.
- Log only what you need: REJECT-only logs are far smaller than ALL logs.
- Set a retention period on the log group. Old flow logs add up, and they are easy to forget.
- In a lab, set retention to 1 day and delete the log group afterwards.

## Comparison

| | Security group | Network ACL |
|---|---|---|
| Level | Instance / ENI | Subnet |
| State | Stateful | Stateless |
| Rule types | Allow only | Allow and deny |
| Evaluation | All rules together | In number order, first match wins |
| Replies | Automatic | Must be allowed (ephemeral ports) |
| Default | Deny in, allow out | Default NACL allows all; custom denies all |
| Can reference another group | Yes | No (CIDR only) |
| Best for | Tier-to-tier control | Subnet-wide deny, backstop |

Now do drill 04 (security groups vs network ACLs) and drill 07 (security groups that reference each other).

Exam tasks: 2.1, 2.2, 3.2

# 05 — Elastic Load Balancing

## What it is

A load balancer gives clients **one address** and spreads their traffic over many **targets** in several AZs.
It checks the health of each target and stops sending traffic to the ones that fail.

Elastic Load Balancing has four types:

| Type | Layer | One line |
|---|---|---|
| **Application (ALB)** | 7 (HTTP/HTTPS) | Routes by what is in the request: host, path, header |
| **Network (NLB)** | 4 (TCP, UDP, TLS) | Very fast, static IPs, any TCP/UDP protocol |
| **Gateway (GWLB)** | 3 (IP packets) | Sends traffic through firewalls and other appliances |
| **Classic (CLB)** | 4 and 7 | The previous generation. AWS recommends migrating |

Task 2.1 ("load balancing concepts, for example Application Load Balancer"), 2.2 (remove single points of failure)
and 3.2 (scalability) all use this note. 4.2 asks for the choice "ALB (Layer 7) compared with NLB (Layer 4) compared
with GWLB". Drill 04 builds the rule matcher. Drill 05 does cross-zone maths and cost. Drill 07 builds an ALB with boto3.

## How it works

### The ALB model

```
client → DNS name → ALB nodes (one per AZ) → listener (port 80 or 443)
                                              → rules, lowest priority number first
                                              → action: forward / redirect / fixed-response
                                              → target group → targets (instances, IPs, a Lambda)
```

- A **listener** checks for connection requests on one protocol and port (HTTP or HTTPS, ports 1 to 65535).
- A listener holds **rules**. Each rule has a **priority**, **conditions** and an **action**.
- A **target group** is a set of targets plus a health check. One target group belongs to one load balancer (an ALB can have up to 100).

#### Rules, step by step

1. Rules are checked in **ascending priority**: 1 before 5 before 100. Priorities are integers from 1 to 50,000, and no two rules in a listener share one.
2. A rule matches when **all** its conditions match. A condition matches when **any** of its values match.
3. The first match wins. Its action runs. Checking stops.
4. The **default rule** has no conditions, is evaluated **last** and cannot be deleted. It answers whatever nothing else matched.

Condition types: `host-header`, `path-pattern`, `http-request-method`, `source-ip`, `http-header`, `query-string`.
Limits: up to **3** match values per condition and **5** per rule. 100 rules per ALB, excluding the default.

Case rules are an exam favourite:

| Condition | Case-sensitive? | Wildcards |
|---|---|---|
| host-header | **No** | `*` (zero or more) and `?` (exactly one) |
| path-pattern | **Yes** | `*` and `?` |
| http-header | No (name and value) | In values only |
| query-string | No | `*` and `?` |
| http-request-method | **Yes** | None. Exact match |
| source-ip | n/a | None. CIDR. Matches the proxy's IP, not `X-Forwarded-For` |

`*.shop.example` matches `www.shop.example` but not `shop.example`. A path pattern looks at the path only, never the
query string. `/img/*` matches `/img/a.png` but not `/IMG/a.png`.

Rule actions: **forward** (to one or more target groups, with weights), **redirect** (for example HTTP → HTTPS), **fixed-response**
(return a status and a body, such as a health page or a 404). Authentication (Cognito or OIDC) can come before the forward.

Example: three rules on one listener.

| Priority | Conditions | Action |
|---|---|---|
| 10 | path `/admin/*` AND source IP `203.0.113.0/24` | forward to `admin-tg` |
| 20 | host `api.shop.example` | forward to `api-tg` |
| 50 | path `/static/*` | redirect to a CDN |
| default | none | forward to `web-tg` |

A request to `/admin/users` from a different network skips rule 10 (the IP condition fails), skips 20 and 50, and falls to the default.

#### Target types and health checks

Target types: **instance**, **ip** (any private address, including on-premises over VPN or Direct Connect) and **lambda**.
Instances launched by an Auto Scaling group register themselves (note 04).

Health check defaults (instance and IP targets):

| Setting | Default | Range |
|---|---|---|
| Path | `/` | |
| Interval | 30 s | 5 to 300 |
| Timeout | 5 s | 2 to 120 |
| Healthy threshold | 5 | 2 to 10 |
| Unhealthy threshold | 2 | 2 to 10 |
| Success codes | 200 | 200 to 499 |

Use a light dedicated path such as `/healthz`. If **all** targets in a group are unhealthy, the ALB **fails open** and
sends to all of them rather than to none.

#### Other ALB settings

- **Deregistration delay** (connection draining): **300 seconds** by default, 0 to 3,600. In-flight requests finish. It ends early if nothing is in flight.
- **Slow start**: a new target gets a linearly growing share, 30 to 900 seconds. Off by default.
- **Sticky sessions**: set on the target group. A load-balancer cookie (`AWSALB`) or your application's cookie. Duration 1 second to 7 days.
- **X-Forwarded-For**: the ALB adds it so your app can see the client's IP (also `X-Forwarded-Proto` and `-Port`).
- **HTTPS and SNI**: an HTTPS listener needs a certificate. With **SNI** one listener can serve **multiple certificates**, up to 25 plus the default.
- **Idle timeout**: 60 seconds by default.
- **Subnets**: at least **two AZs**, a /27 or larger subnet with 8 free addresses each.
- **Scheme**: **internet-facing** (public IPs) or **internal** (private IPs only). Targets need no public IP either way.
- **AWS WAF** attaches to an ALB. Security groups attach to an ALB too.
- Routing algorithms: round robin (default), least outstanding requests, weighted random.

### Network Load Balancer

- **Layer 4**: TCP, UDP, TLS.
- **One static IP per enabled AZ**, and you can attach your own **Elastic IP** to each. Good for firewall allow-lists.
- **Client IP preservation** is on by default for instance targets, so the app sees the real client address.
  IP targets over TCP/TLS default to off. Proxy protocol v2 can pass the address too.
- Targets can be instances, IPs or an ALB.
- Flow hash picks the target from protocol, source and destination IP and port.
- TCP idle timeout 350 s. UDP 120 s.
- Security groups on an NLB are now supported (changed: older NLBs had none). One created without a security group cannot get one later.
- NLB is the front door for **PrivateLink** services (week 02).

### Gateway Load Balancer

- **Layer 3**. Listens for all IP packets on all ports. Uses **GENEVE on port 6081**.
- Deploys and scales **virtual appliances**: firewalls, intrusion detection, deep packet inspection.
- A **GWLB endpoint** sits in the route table as the next hop. It is transparent: traffic goes through the appliances and on to its destination.
- Cross-zone is off by default.

### Classic Load Balancer

The previous generation. TCP/SSL and HTTP/HTTPS listeners in one product. IPv4 only. AWS says to migrate to a
current-generation load balancer. On the exam it is the wrong answer for new designs.

### Cross-zone load balancing

Each load balancer puts a node in every enabled AZ. **Without** cross-zone, a node splits its traffic only among
targets **in its own AZ**. DNS sends equal traffic to each AZ. **With** cross-zone, each node spreads over all targets.

| | Default |
|---|---|
| ALB | **On**, cannot be turned off for the load balancer (can be overridden per target group) |
| NLB | **Off** |
| GWLB | **Off** |
| CLB | On in the console, off through the API |

Example: 10 targets, 2 in AZ A and 8 in AZ B.

- Cross-zone **on**: every target gets 1/10 = **10 %**.
- Cross-zone **off**: each AZ gets 50 %. The 2 targets in A get **25 %** each. The 8 targets in B get **6.25 %** each.

Off leaves the small AZ overloaded. On evens it out, but traffic crosses AZs. For an NLB, enabling it brings
**inter-AZ data transfer charges**. Sticky sessions need cross-zone on.

### Load balancing and Auto Scaling together

The standard web design: an internet-facing ALB in public subnets, an Auto Scaling group in private subnets across
two or more AZs, security groups that let the instances accept traffic **only from the ALB's security group**, ELB health
checks, target tracking on `ALBRequestCountPerTarget`. A failed instance is replaced. Load spreads. No client ever sees a server IP.

## Numbers to know

- ALB: layer **7**, at least **2 AZs**, **100** rules per ALB, priority **1 to 50,000**, **3** values per condition, **5** per rule.
- Health check defaults: interval **30 s**, timeout **5 s**, healthy **5**, unhealthy **2**, path `/`, code 200.
- Deregistration delay **300 s**. Slow start off (30 to 900 s). ALB idle timeout **60 s**.
- Sticky session duration up to **7 days**. Certificates per ALB: **25** plus default.
- NLB: layer **4**, one static IP per AZ, cross-zone **off**.
- GWLB: layer **3**, GENEVE **port 6081**.
- DNS TTL of a load balancer: **60 seconds**.
- Prices (illustrative): ALB 0.0225 USD/hour + 0.008 USD per LCU-hour. NLB 0.0225/hour + 0.006 per NLCU-hour.

## When to choose it

| Need | Choose |
|---|---|
| Route by path or host, many services behind one DNS name | ALB |
| Redirect HTTP to HTTPS, fixed 404 page | ALB |
| Targets are containers, IPs or Lambda functions | ALB (or NLB for IPs) |
| WebSockets, HTTP/2, gRPC | ALB |
| Extreme throughput, TCP/UDP, non-HTTP protocol | NLB |
| Static IP or Elastic IP for allow-lists | NLB |
| Expose a service through PrivateLink | NLB |
| Inspect all traffic with a third-party firewall | GWLB |
| Existing Classic load balancer | Migrate to ALB or NLB |
| Keep clients' source IP visible to the app | NLB (preservation), or ALB with `X-Forwarded-For` |

## Exam traps

- **ALB with a static IP.** ALB IPs change. For a static IP use an NLB (or put an NLB in front of an ALB).
- **NLB path routing.** NLB cannot route by path. That is ALB.
- **Rule order.** Lowest number first. A broad rule at priority 1 can hide every other rule.
- **Case.** Paths and methods are case-sensitive. Hosts and headers are not.
- **Default rule.** It cannot be deleted and matches last. A request that matches nothing goes there.
- **Health check on `/` of a heavy page.** Use a light `/healthz`.
- **Real client IP behind an ALB.** Read `X-Forwarded-For`; the TCP source is the ALB.
- **Cross-zone defaults.** ALB on, NLB off. Cost surprises appear on NLB.
- **One AZ.** An ALB needs two. Fewer defeats the purpose.
- **Target in a private subnet needs a public IP.** No. The load balancer reaches it by private IP.
- **GWLB for ordinary web traffic.** It is for appliances, not web servers.
- **Deregistration.** In-flight requests get 300 seconds by default. Lower it to speed up deploys.

## Cost angle

- An ALB bills **per hour plus LCU-hours**. An LCU measures the highest of four things: new connections (25 per second),
  active connections (3,000 per minute), data processed (1 GB per hour) and rule evaluations (1,000 per second, the first 10 rules free).
- An NLB bills per hour plus NLCU-hours (different dimensions for TCP, UDP and TLS). GWLB is 0.0125 USD/hour plus GLCU-hours.
- Data transfer and public IPv4 addresses (0.005 USD/hour each) are billed separately.
- One ALB with host and path rules replaces many ALBs. A load balancer per service is the common waste.
- Enabling cross-zone on an NLB adds inter-AZ transfer at 0.01 USD per GB in each direction (charged out and in).
- An idle load balancer still bills the hourly charge. Delete lab ones.
- Prefer ALB over CLB: path routing and per-target-group health checks (CLB example: 0.025 USD/hour + 0.008 USD per GB).

## Comparison

| | ALB | NLB | GWLB | CLB |
|---|---|---|---|---|
| Layer | 7 | 4 | 3 | 4 and 7 |
| Protocols | HTTP, HTTPS, WebSockets, gRPC | TCP, UDP, TLS | IP packets (GENEVE 6081) | TCP, SSL, HTTP, HTTPS |
| Routing | Host, path, header, method, query, source IP | Port and protocol | Transparent | Basic |
| Static IP | No | One per AZ, Elastic IP | n/a | No |
| Targets | Instance, IP, Lambda | Instance, IP, ALB | Appliances | Instance |
| Cross-zone default | On | Off | Off | Console on / API off |
| Pricing unit | Hour + LCU | Hour + NLCU | Hour + GLCU | Hour + per GB |
| Use it for | Web apps, microservices | Extreme performance, static IPs, PrivateLink | Firewalls, inspection | Nothing new |

Now do drill 04 (which rule answers?), drill 05 (who gets the traffic?), drill 07 (a load balancer with rules) and drill 10 (what does Auto Scaling do?).

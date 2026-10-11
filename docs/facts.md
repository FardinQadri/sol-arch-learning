# Facts of record

Every number, limit, date and status used in concept notes, drills and quiz questions comes from this
file. Each row names its official source. Checked 2026-10-08 (research: docs/research/2026-10-08-saa-c03-research.md).
A question never depends on a value marked "changed" — the exam may still use the old one.

## Exam

| Fact | Value | Source |
|---|---|---|
| Questions | 65 (50 scored + 15 unscored, not identified) | exam guide PDF v1.1 p.2 |
| Question types | multiple choice (1 of 4) · multiple response (2+ of 5+) | exam guide p.1 |
| Duration · cost | 130 minutes · 150 USD | aws.amazon.com/certification/certified-solutions-architect-associate/ |
| Scoring | scaled 100–1,000 · pass 720 · compensatory · no guessing penalty | exam guide p.2 |
| Domains | 1 Secure 30 % · 2 Resilient 26 % · 3 High-performing 24 % · 4 Cost 20 % | exam guide p.2 |

## Numbers to know

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Reserved IPs per subnet | 5 (network, .1 router, .2 DNS, .3 future, broadcast) | no | docs.aws.amazon.com/vpc/latest/userguide/subnet-sizing.html |
| S3 max object size | 50 TB | changed 2025-12-02 (was 5 TB) | aws.amazon.com/about-aws/whats-new/2025/12/amazon-s3-maximum-object-size-50-tb/ |
| S3 single PUT | up to 5 GB (multipart above that) | no | docs.aws.amazon.com/AmazonS3/latest/userguide/upload-objects.html |
| SQS max message | 1 MiB | changed 2025-08-04 (was 256 KiB) | docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html |
| SQS retention | default 4 days · 60 s – 14 days | no | same |
| SQS visibility timeout | default 30 s · max 12 hours | no | same |
| SQS delay | max 15 minutes | no | same |
| SQS FIFO | 300 API calls/s per action (3,000 messages/s with batches of 10); higher with high-throughput mode | no | same |
| Lambda | timeout 900 s · memory 128–10,240 MB · /tmp 512–10,240 MB · 6 MB sync payload · 1 MB async | no | docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html |
| DynamoDB item | 400 KB max | no | docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html |
| RDS MySQL read replicas | up to 15 per source (same Region) | no | docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_MySQL.Replication.ReadReplicas.html |
| Aurora replicas | up to 15 per cluster | no | docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.Replication.html |
| gp3 | 1 GiB–64 TiB · 3,000 IOPS / 125 MiB/s baseline · up to 80,000 IOPS / 2,000 MiB/s | changed (was 16 TiB / 16,000 / 1,000) | docs.aws.amazon.com/ebs/latest/userguide/ebs-volume-types.html |
| gp2 | up to 16 TiB · 16,000 IOPS · 250 MiB/s | no | same |
| io2 Block Express | up to 64 TiB · 256,000 IOPS · 4,000 MiB/s · 99.999 % durability · Multi-Attach | no | same |
| io1 | up to 16 TiB · 64,000 IOPS · 1,000 MiB/s · Multi-Attach | no | same |
| st1 / sc1 | HDD, not bootable · 500 / 250 MiB/s max | no | same |
| Glacier Flexible Retrieval | expedited 1–5 min · standard 3–5 h · bulk 5–12 h | no | docs.aws.amazon.com/AmazonS3/latest/userguide/restoring-objects-retrieval-options.html |
| Glacier Deep Archive | standard within 12 h · bulk within 48 h | no | same |
| Glacier Instant Retrieval | milliseconds | no | same |
| Minimum storage duration | Standard-IA 30 days (+128 KB min billable) · Glacier IR 90 · Glacier Flexible 90 · Deep Archive 180 · Standard and Intelligent-Tiering none | no | docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html |
| Public IPv4 address | 0.005 USD per hour, in use or idle | since 2024-02-01 | aws.amazon.com/blogs/aws/new-aws-public-ipv4-address-charge-public-ip-insights/ |
| S3 ListObjectsV2 page | up to 1,000 keys per request | no | docs.aws.amazon.com/AmazonS3/latest/API/API_ListObjectsV2.html |

Not confirmed — do not state as numbers until a later plan confirms them from an official page:
FIFO high-throughput limits · NAT gateway and interface-endpoint list prices for us-east-1 (only us-east-2 / per-ENI examples seen) · exact start date of the public IPv4 charge on an official page · regional NAT gateway launch date · whether the local route can be deleted · flow-log aggregation interval choices · whether IPv6 subnets must be exactly /64 · maximum hibernation duration · whether per-second billing has an OS caveat on any page · ALB authentication action names beyond authenticate-oidc (cognito, jwt-validation) · the word "aggressively" in target tracking wording (the docs say "in direct proportion") · ALB wildcard limit (the condition page says 5 per rule, the quota table 6) · launch dates of NLB security groups and the ALB target-group cross-zone override · dates and instance-type list for IMDSv2-only defaults · Spot blocks (defined duration) status · a Graviton price-performance percentage (only "up to 20% less cost" is on the Graviton page) · predictive scaling history and forecast numbers · default warmup for predictive scaling · instance vCPU and memory sizes come from the AWS pricing JSON, not the instance-type spec pages · S3 minimum storage duration of Express One Zone (user guide says none, product page says 1 hour) · Express One Zone request-price discount (50 or 80 percent, pages disagree) · whether a lifecycle rule must wait 30 days before Standard to Standard-IA or One Zone-IA · S3 Replication Time Control percentage (99.9 or 99.99) · whether DeleteBucket fails while incomplete multipart uploads exist · whether Object Lock can be enabled on an existing bucket · S3 byte-range fetch recommended size and Requester Pays details · the bucket-policy condition value for requiring SSE-KMS · FSx for NetApp ONTAP and FSx for Windows DFS Namespaces details · FSx File Gateway closure date · Storage Gateway hardware appliance end-of-sale dates and Amazon Linux 2 gateway migration deadline · S3 bucket-quota fee details (first 2,000 buckets free) · retired services: exact dates for S3 Select and Snowcone/Snowmobile (Rule 1 rows keep their dates) · EFS Archive lifecycle day options · EFS One Zone availability percentage · Glacier provisioned capacity unit price · Glacier Deep Archive storage price in us-east-1 specifically · EBS io2 price above 64,000 IOPS and EBS prices by Region · the 48.8 TiB vs 50 TB maximum object size wording (use 50 TB) · RDS Multi-AZ DB cluster supported-engine table (page names MySQL and PostgreSQL only) · RDS Proxy supported-engine table (limitations sections list MariaDB, MySQL, PostgreSQL, SQL Server) · deletion protection default for CLI/API creation · which KMS key a same-Region encrypted read replica may use · RDS snapshot-sharing details (maximum accounts, public sharing) · end date of the legacy Performance Insights paid tiers · an RDS read replica that is itself Multi-AZ (only a topic title seen) · RDS Extended Support and RDS Custom prices · Aurora 10 GiB storage segments and the six-copy write/read quorum wording · earlier Aurora Global Database limit of 5 secondary Regions and its change date · Aurora Auto Scaling for replicas (target tracking, metrics) · earlier DynamoDB transaction limit of 25 items and its change date · earlier DynamoDB capacity-mode switching limit and its change date · DynamoDB on-demand backup retention and restore details · DynamoDB TTL hour figure (page says only "typically within a few days") · earlier DynamoDB tables-per-account default (256) · GSIs added or removed at any time (only indirect wording) · DAX microsecond-latency claim, node types and 3-node production advice · DynamoDB Standard-IA, reserved-capacity and Database Savings Plans discount figures beyond the page quotes · ElastiCache Serverless maximum storage and ECPU limits · ElastiCache Valkey launch date · numeric ElastiCache failover time (page says "typically just a few seconds") · ElastiCache reserved-node discount and Database Savings Plans · Keyspaces replication, capacity modes and PITR retention · Neptune maximum storage and Neptune/DocumentDB pricing · Timestream for InfluxDB details · OpenSearch Serverless details and pricing.

## Defaults that changed

| Change | Date | Source |
|---|---|---|
| S3 encrypts every new object with SSE-S3 by default (cannot be turned off) | 2023-01-05 | aws.amazon.com/about-aws/whats-new/2023/01/amazon-s3-automatically-encrypts-new-objects/ |
| New S3 buckets: Block Public Access on, ACLs disabled (Bucket owner enforced) | from 2023-04 | aws.amazon.com/about-aws/whats-new/2023/04/amazon-s3-security-best-practices-buckets-default/ |
| IMDSv2 can be set as the account default for new launches; Amazon Linux 2023 disables IMDSv1 | 2024-03 / 2023 | aws.amazon.com/about-aws/whats-new/2024/03/set-imdsv2-default-new-instance-launches/ |
| Aurora Serverless v2 can scale to 0 ACUs (auto-pause) | 2024-11-20 | aws.amazon.com/about-aws/whats-new/2024/11/amazon-aurora-serverless-v2-scaling-zero-capacity/ |
| Launch configurations: no new instance types since 2023; new accounts since 2024-10-01 cannot create them — use launch templates | 2023–2024 | docs.aws.amazon.com/autoscaling/ec2/userguide/launch-configurations.html |
| AWS CodeCommit back in general availability | 2025-11-24 | aws.amazon.com/blogs/devops/aws-codecommit-returns-to-general-availability/ |
| Renames: AWS SSO → IAM Identity Center · Kinesis Data Analytics for Apache Flink → Amazon Managed Service for Apache Flink | — | AWS docs |

## VPC networking (week 02)

Source key: UG = docs.aws.amazon.com/vpc/latest/userguide/ · PL = docs.aws.amazon.com/vpc/latest/privatelink/ · PEER = docs.aws.amazon.com/vpc/latest/peering/ · TGW = docs.aws.amazon.com/vpc/latest/tgw/ · VPN = docs.aws.amazon.com/vpn/latest/s2svpn/ (page name follows). Research: docs/research/2026-10-10-vpc-facts.md, read 2026-10-10. "changed" rows: teach the exam answer; no question depends on them.

### VPC and subnets

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Allowed IPv4 VPC CIDR size | /16 (65,536 IPs) to /28 (16 IPs) | no | UG vpc-cidr-blocks.html |
| Allowed IPv4 subnet size | /16 to /28 | no | UG subnet-sizing.html |
| Reserved IPs per subnet | 5 (first 4 + last): network, VPC router, DNS (base+2), future use, broadcast | no | UG subnet-sizing.html |
| Secondary IPv4 CIDRs per VPC (default quota) | IPv4 CIDR blocks per VPC = 5 total (primary + secondary count); adjustable up to 50 | no | UG amazon-vpc-limits.html |
| Secondary CIDR rules | Same /16-/28 size, no overlap with existing CIDRs, cannot resize an existing block, cannot disassociate the primary | no | UG vpc-cidr-blocks.html |
| IPv6 CIDR blocks per VPC (default quota) | 5; adjustable up to 50 | no | UG amazon-vpc-limits.html |
| IPv6 VPC size (Amazon-provided) | /56 example; user cannot choose the range | no | UG vpc-cidr-blocks.html |
| IPv6 VPC sizes (multiple blocks) | Up to five IPv6 blocks, /44 to /60 in steps of /4 | no | UG vpc-cidr-blocks.html |
| IPv6 subnet size | /64 in AWS examples (page lists /44 to /64 in steps of /4) | no | UG vpc-cidr-blocks.html ; UG subnet-sizing.html |
| RFC 1918 ranges AWS recommends | 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 | no | UG vpc-cidr-blocks.html |
| CIDRs not allowed for a VPC | 0.0.0.0/8, 127.0.0.0/8, 169.254.0.0/16, 224.0.0.0/4 | no | UG vpc-cidr-blocks.html |
| Range to avoid | 172.17.0.0/16 (used by some AWS services) | no | UG vpc-cidr-blocks.html |
| Does a subnet span AZs? | No. A subnet resides entirely in one AZ | no | UG configure-subnets.html |
| VPC spans AZs? | A VPC can have subnets in several AZs (diagram: subnets in two AZs) | no | UG configure-subnets.html |
| Default VPC CIDR | 172.31.0.0/16 | no | UG default-vpc-components.html |
| Default subnets | One /20 public subnet per AZ (4,096 addresses) | no | UG default-vpc-components.html |
| Default VPC internet gateway | Created and attached; main route table has 0.0.0.0/0 -> IGW | no | UG default-vpc-components.html |
| Default VPC IPv6 route to IGW | None by default (no ::/0 route; no auto IPv6 address) | no | UG VPC_Internet_Gateway.html |
| Default VPC public IPv4 on launch | Yes, auto-assigned in default subnets; no in non-default subnets | no | UG VPC_Internet_Gateway.html |
| VPCs per Region (default) | 5 (adjustable) | no | UG amazon-vpc-limits.html |
| Subnets per VPC (default) | 200 (adjustable) | no | UG amazon-vpc-limits.html |
| Public vs private subnet definition | Public = route table has a route to an IGW; private = no such route | no | UG VPC_Internet_Gateway.html |

### Routing

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Local route | Default route for communication within the VPC; one per CIDR block (separate IPv4 and IPv6) | no | UG RouteTables.html |
| Local route priority | Highest priority in a VPC route table (priority 1 in AWS example) | no | TGW how-transit-gateways-work.html |
| Replace local route target | Allowed: target can be replaced (e.g. with an appliance network interface) and later restored to local | changed (newer than 2022; date not confirmed) | UG replace-local-route-target.html |
| More specific route than local | Allowed to an appliance (NAT gateway, network interface, GWLB endpoint); destination must match an entire subnet CIDR | changed (newer; was: not allowed; date not confirmed) | UG route-table-options.html |
| Less specific route does not override local | Appliance route for 0.0.0.0/0 must be less specific than the local route; intra-VPC traffic still follows local | no | UG route-table-options.html |
| Longest prefix match | Most specific matching route wins; IPv4 and IPv6 routes are independent | no | UG route-tables-priority.html |
| Route priority order | Longest prefix, then static routes, then prefix-list routes, then propagated (DX BGP, VPN static, VPN BGP) | no | UG route-tables-priority.html |
| Static route targets | IGW, NAT gateway, network interface, instance ID, gateway VPC endpoint, transit gateway, VPC peering, GWLB endpoint | no | UG route-tables-priority.html |
| Main route table | Controls routing for every subnet not explicitly associated with another route table; new subnets auto-associate with it | no | UG RouteTables.html ; UG configure-subnets.html |
| A subnet associates with | Exactly one route table (a route table can serve many subnets) | no | UG amazon-vpc-limits.html |
| Route to IGW | 0.0.0.0/0 (IPv4) or ::/0 (IPv6) with target igw-id | no | UG route-table-options.html |
| Route to NAT gateway | 0.0.0.0/0 with target nat-id in the private subnet's table | no | UG route-table-options.html |
| Route to VPC peering | Destination = peer VPC CIDR, target pcx-id; both sides must add routes | no | UG route-table-options.html |
| Route to Transit Gateway | Destination = remote CIDR (or 0.0.0.0/0), target tgw-id | no | UG route-table-options.html |
| Route to gateway endpoint | Destination = AWS-managed prefix list (pl-xxxx), target vpce-id; auto-added, cannot be edited or deleted manually | no | UG route-table-options.html ; PL gateway-endpoints.html |
| Routes per route table (default) | 500 non-propagated (adjustable to 1,000); 100 propagated (fixed) | no | UG amazon-vpc-limits.html |
| Route tables per VPC (default) | 200 (adjustable) | no | UG amazon-vpc-limits.html |
| Gateway route table | Route table associated with an IGW or VGW (edge association) for inbound inspection | no | UG RouteTables.html |

### Internet access

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Internet gateway scaling | Horizontally scaled, redundant, highly available; no availability risk or bandwidth constraints | no | UG VPC_Internet_Gateway.html |
| IGW per VPC | Only one internet gateway can be attached to a VPC at a time | no | UG amazon-vpc-limits.html |
| IGW cost | No charge for the IGW; EC2 data transfer charges apply | no | UG VPC_Internet_Gateway.html |
| IGW does NAT | One-to-one NAT for instances with public IPv4 / Elastic IP | no | UG VPC_Internet_Gateway.html |
| NAT gateway scope | Created in a specific AZ, redundant within that AZ (zonal) | changed: regional availability mode added (date not confirmed, see notes) | UG nat-gateway-basics.html |
| NAT gateway types | Public (default; needs Elastic IP at creation; lives in public subnet; routes to IGW) and Private (no EIP; via TGW/VGW) | no | UG vpc-nat-gateway.html |
| Private NAT gateway to internet | IGW drops the traffic | no | UG vpc-nat-gateway.html |
| NAT gateway bandwidth | 5 Gbps, automatically scales up to 100 Gbps | no | UG nat-gateway-basics.html |
| NAT gateway packet rate | 1 million pps, scales to 10 million pps | no | UG nat-gateway-basics.html |
| NAT gateway connections | 55,000 simultaneous connections per IP per unique destination | no | UG nat-gateway-basics.html |
| NAT gateway EIPs | Default 2 per public NAT gateway (adjustable up to 8) | no | UG amazon-vpc-limits.html |
| NAT gateway protocols | TCP, UDP, ICMP | no | UG nat-gateway-basics.html |
| NAT gateway ports | Uses ports 1024-65535 | no | UG nat-gateway-basics.html |
| Security groups on NAT gateway | Not supported; use SGs on resources behind it; NACLs on its subnet | no | UG nat-gateway-basics.html |
| One NAT per AZ for resilience | Yes: create a NAT gateway in each AZ and route each AZ to its own | no | UG nat-gateway-basics.html |
| NAT gateways per AZ (default) | 5 (adjustable) | no | UG amazon-vpc-limits.html |
| Regional NAT gateway | Single NAT gateway spans AZs automatically; no public subnet needed; up to 32 IPs per AZ; no private NAT support | changed (new since 2022; launch date not confirmed) | UG nat-gateways-regional.html |
| NAT instance status | Legacy: NAT AMI built on Amazon Linux AMI 2018.03 (end of maintenance support 2023-12-31); AWS recommends NAT gateways | changed (end-of-support dates are after 2022) | UG VPC_NAT_Instance.html |
| NAT instance source/dest check | Must be disabled (instance must forward traffic it neither sends nor receives) | no | UG work-with-nat-instances.html |
| NAT instance vs gateway | Instance: you manage failover, bandwidth depends on instance type, can use SGs and as bastion, port forwarding possible. Gateway: managed, up to 100 Gbps, no SGs | no | UG vpc-nat-comparison.html |
| Egress-only internet gateway | IPv6 only; outbound-only; stateful; horizontally scaled; no charge (data transfer charges apply); no security group on it | no | UG egress-only-internet-gateway.html |
| EIGW route | ::/0 with target eigw-id; for IPv4 outbound-only use NAT gateway | no | UG egress-only-internet-gateway.html |
| IPv6 and NAT gateway | NAT gateway can do NAT64 with DNS64 for IPv6-to-IPv4 | no | UG nat-gateway-basics.html |

### Security groups vs network ACLs

| Fact | Value | Changed? | Source |
|---|---|---|---|
| SG state | Stateful: responses automatically allowed | no | UG vpc-security-groups.html |
| SG rule types | Allow rules only, no deny | no | UG security-group-rules.html |
| SG new group defaults | No inbound rules (all inbound denied); one outbound allow-all rule | no | UG security-group-rules.html |
| Default SG inbound | Allow all protocols/ports from the same SG | no | UG default-security-group.html |
| Default SG outbound | Allow all IPv4 (0.0.0.0/0), plus ::/0 if VPC has IPv6 | no | UG default-security-group.html |
| Default SG removal | Cannot be deleted; rules can be changed | no | UG default-security-group.html |
| SG can reference another SG | Yes, as source/destination (same VPC, peered VPC, or via TGW for inbound) | no | UG security-group-rules.html |
| SG scope | Attached to resources via their network interfaces; multiple SGs per resource, rules aggregated | no | UG vpc-security-groups.html ; UG security-group-rules.html |
| SG traffic not filtered | Amazon DNS, DHCP, instance metadata, ECS task metadata, Windows license activation, Time Sync, VPC router reserved IPs | no | UG vpc-security-groups.html |
| SG rules per SG (default) | 60 inbound and 60 outbound (separately; also per IPv4 vs IPv6) | no | UG amazon-vpc-limits.html |
| SGs per network interface (default) | 5 (adjustable up to 16); rules-per-SG x SGs-per-ENI cannot exceed 1,000 | no | UG amazon-vpc-limits.html |
| SGs per Region (default) | 2,500 | no | UG amazon-vpc-limits.html |
| NACL state | Stateless: return traffic must be explicitly allowed | no | UG vpc-network-acls.html |
| NACL rule types | Allow and deny | no | UG vpc-network-acls.html |
| NACL evaluation order | Ascending rule number, lowest first; first match applies, evaluation stops | no | UG vpc-network-acls.html |
| NACL rule number range | 1 to 32766 (AWS suggests steps of 10 or 100) | no | UG vpc-network-acls.html |
| Default NACL | Allows all inbound and outbound (rule 100 IPv4, 101 IPv6); final * rule denies | no | UG default-network-acl.html |
| Custom NACL default | Only the * rule (deny all) until you add allow rules | no | UG custom-network-acl.html |
| NACL per subnet | A subnet has exactly one NACL; one NACL can be associated with many subnets | no | UG vpc-network-acls.html |
| NACL applies at | Subnet boundary (traffic entering/leaving the subnet, not within it) | no | UG vpc-network-acls.html |
| NACL rules per NACL (default) | 20 inbound and 20 outbound; max 40 each (80 total) | no | UG amazon-vpc-limits.html |
| NACLs per VPC (default) | 200 | no | UG amazon-vpc-limits.html |
| Ephemeral ports (AWS guidance) | To cover all client types open 1024-65535. Linux 32768-61000, Windows Server 2008+ 49152-65535, ELB/NAT gateway/Lambda 1024-65535 | no | UG custom-network-acl.html |
| NACL does not filter | Amazon DNS, DHCP, instance metadata, ECS task metadata, Windows license activation, Time Sync, VPC router reserved IPs | no | UG vpc-network-acls.html |
| SG vs NACL level | SG = instance/ENI level; NACL = subnet level | no | UG infrastructure-security.html |
| Cost | No additional charge for SGs or NACLs | no | UG vpc-security-groups.html ; UG vpc-network-acls.html |

### VPC endpoints and PrivateLink

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Gateway endpoint services | Only Amazon S3 and DynamoDB | no | PL gateway-endpoints.html |
| Gateway endpoint cost | No additional charge | no | PL gateway-endpoints.html |
| Gateway endpoint mechanism | Route-table entry: destination = service prefix list, target = endpoint; not PrivateLink | no | PL gateway-endpoints.html |
| Gateway endpoint Region | Available only in the Region where created; same Region as the S3 buckets | no | PL vpc-endpoints-s3.html |
| Gateway endpoint reach | Not usable from on-premises, peered VPCs in other Regions, or through a transit gateway | no | PL vpc-endpoints-s3.html |
| Gateway endpoint quotas | 20 per Region default (adjustable); 255 per VPC | no | PL vpc-endpoints-s3.html |
| Gateway endpoint longest-prefix | Endpoint route beats 0.0.0.0/0 to IGW for same-Region S3/DynamoDB traffic | no | PL gateway-endpoints.html |
| Interface endpoint | Creates an endpoint network interface (ENI) with a private IP in each chosen subnet (one subnet per AZ); powered by PrivateLink | no | PL create-interface-endpoint.html ; PL concepts.html |
| Interface endpoint private DNS | Enabled by default so public service names resolve to the endpoint (needs DNS hostnames and DNS resolution on the VPC) | no | PL create-interface-endpoint.html |
| Interface endpoint security | Security groups attach to the endpoint ENIs (default SG applied if none chosen) | no | PL create-interface-endpoint.html |
| Interface endpoint billing | Hourly usage per endpoint per AZ plus data processing per GB | no | PL create-interface-endpoint.html ; https://aws.amazon.com/privatelink/pricing/ |
| Interface endpoint ping | Does not respond to ping | no | PL create-interface-endpoint.html |
| S3 interface endpoint vs gateway | Interface endpoints (extra cost) work from on-premises, other-Region peering, TGW | no | PL vpc-endpoints-s3.html |
| Endpoint policy | IAM resource policy on the endpoint; default policy allows all principals/actions/resources; max 20,480 characters | no | PL vpc-endpoints-access.html |
| Endpoint policy on gateway endpoints | Principal must be "*"; use aws:PrincipalArn condition to restrict | no | PL vpc-endpoints-access.html |
| aws:SourceVpce | Bucket policy condition to restrict access to a specific endpoint | no | PL vpc-endpoints-s3.html |
| aws:SourceVpc | Bucket policy condition to restrict access to a specific VPC (useful with multiple endpoints in one VPC) | no | PL vpc-endpoints-s3.html |
| aws:SourceIp via endpoint | Not usable for requests through a VPC endpoint; use aws:VpcSourceIp | no | PL vpc-endpoints-s3.html |
| Gateway Load Balancer endpoint | Endpoint type sending traffic to a virtual-appliance fleet; targeted from route tables; billed hourly + data processing; up to 10 Gbps per AZ, scales to 100 Gbps | no | PL gateway-load-balancer-endpoints.html ; PL concepts.html |
| Other endpoint types | Resource, Tunnel, Service network endpoints exist alongside Interface, GWLB, Gateway | changed (resource/service-network types are newer than 2022) | PL concepts.html |

### Connecting VPCs and networks

| Fact | Value | Changed? | Source |
|---|---|---|---|
| VPC peering is non-transitive | A-B and A-C peering does not let B reach C via A | no | PEER vpc-peering-basics.html |
| Peering CIDR rule | No matching or overlapping IPv4 or IPv6 CIDRs (any block, even if unused) | no | PEER vpc-peering-basics.html |
| Peering cross-account / cross-Region | Both allowed (inter-Region peering supported) | no | PEER what-is-vpc-peering.html |
| Peering needs routes | Each side must add a route to the peer CIDR; SG rules may need updating | no | PEER vpc-peering-basics.html |
| Peering: no edge-to-edge routing | Peer cannot use the other VPC's IGW, NAT device, VPN, Direct Connect, or gateway endpoint | no | PEER vpc-peering-basics.html |
| Peering architecture | Not a gateway or VPN; no single point of failure or bandwidth bottleneck | no | PEER what-is-vpc-peering.html |
| Peering MTU | 9001 same Region; 8500 inter-Region | no | PEER vpc-peering-basics.html |
| Peering request expiry | Pending-acceptance request expires after 7 days | no | PEER vpc-peering-basics.html |
| Transit Gateway | Regional virtual router (layer 3) hub for VPCs and on-premises networks; scales elastically | no | TGW how-transit-gateways-work.html |
| TGW transitive routing | Yes: attachments route to each other via TGW route tables | no | TGW how-transit-gateways-work.html |
| TGW attachment types | VPC, VPN, VPN Concentrator, Direct Connect gateway, Connect, TGW peering, Client VPN, network function | changed (VPN Concentrator and network function attachments are newer) | TGW what-is-transit-gateway.html |
| TGW route tables | Default route table plus optional extra tables; each attachment associates with exactly one table; propagation to one or more tables; static and blackhole routes | no | TGW how-transit-gateways-work.html |
| TGW peering routing | Static routes only | no | TGW how-transit-gateways-work.html |
| TGW AZ requirement | Enable a subnet in each AZ of a VPC attachment to reach resources in that AZ | no | TGW how-transit-gateways-work.html |
| TGW MTU | 8500 for VPC/DX/Connect/peering attachments; 1500 for VPN | no | TGW what-is-transit-gateway.html |
| Site-to-Site VPN tunnels | Two IPsec tunnels per VPN connection | no | VPN VPC_VPN.html |
| VPN max bandwidth per tunnel | Standard up to 1.25 Gbps (140,000 pps) | no | VPN vpn-limits.html |
| VPN large bandwidth tunnel | Up to 5 Gbps per tunnel (400,000 pps), only on Transit Gateway or Cloud WAN | changed (newer than 2022) | VPN VPC_VPN.html ; VPN vpn-limits.html |
| VPN aggregate bandwidth | ECMP on a transit gateway (dynamic routing only) aggregates tunnels | no | VPN vpn-limits.html |
| VPN termination options | Virtual private gateway (one VPC) or transit gateway | no | VPN VPC_VPN.html |
| VPN IPv6 | Not supported on a virtual private gateway; supported on TGW and Cloud WAN | changed (IPv6 VPN is newer) | VPN VPC_VPN.html |
| VPN connections per Region (default) | 50 | no | VPN vpn-limits.html |
| VPC Lattice | Fully managed application-networking service to connect, secure and monitor services across VPCs and accounts | changed (new service since 2022) | https://docs.aws.amazon.com/vpc-lattice/latest/ug/what-is-vpc-lattice.html |

### VPC Flow Logs

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Destinations | CloudWatch Logs, Amazon S3, Amazon Data Firehose | changed (Firehose is newer) | UG flow-logs.html |
| Levels | VPC, subnet, or network interface (VPC/subnet cover all ENIs within) | no | UG flow-logs-basics.html |
| Traffic types | Accepted, rejected, or all (ACCEPT/REJECT/ALL) | no | UG flow-logs-basics.html |
| Real time? | No; not a real-time stream; can take several minutes to start publishing | no | UG flow-logs-basics.html |
| Aggregation on Nitro instances | Always 1 minute or less regardless of configured maximum | no | UG flow-logs-limitations.html |
| Performance impact | Collected outside the traffic path; no effect on throughput or latency | no | UG flow-logs.html |
| Not logged: Amazon DNS | Traffic to the Amazon DNS server (your own DNS server is logged) | no | UG flow-logs-limitations.html |
| Not logged: metadata and time | 169.254.169.254 instance metadata; 169.254.169.123 Time Sync | no | UG flow-logs-limitations.html |
| Not logged: other | Windows license activation, DHCP, VPC router reserved IP, ARP, mirrored source traffic, endpoint ENI to NLB ENI | no | UG flow-logs-limitations.html |
| Config immutable | Cannot change a flow log's configuration or record format after creation; delete and recreate | no | UG flow-logs-limitations.html |
| Can log ENIs of other services | ELB, RDS, ElastiCache, Redshift, WorkSpaces, NAT gateways, transit gateways | no | UG flow-logs-basics.html |
| Flow log cost | Vended-log ingestion and archival charges apply (see CloudWatch Logs pricing) | no | UG flow-logs.html |
| Peer VPC logging | Cannot enable flow logs for a peer VPC unless it is in your account | no | UG flow-logs-limitations.html |
| Record statuses | OK, NODATA, SKIPDATA in log-status | no | UG flow-logs-records-examples.html |

## Compute and scaling (week 03)

Source key: ITN = docs.aws.amazon.com/ec2/latest/instancetypes/ · EC2 = docs.aws.amazon.com/AWSEC2/latest/UserGuide/ · ASG = docs.aws.amazon.com/autoscaling/ec2/userguide/ · ALB = docs.aws.amazon.com/elasticloadbalancing/latest/application/ · NLB = …/latest/network/ · GWLB = …/latest/gateway/ · CLB = …/latest/classic/ · ELB = …/latest/userguide/ · SP = docs.aws.amazon.com/savingsplans/latest/userguide/ (page name follows). Full https URLs are pricing or API-reference pages. Research: docs/research/2026-10-11-compute-facts.md, read 2026-10-11. Instance generations are perishable: notes may name them once as examples; no question depends on a generation newer than 7 or on a "changed" row.

### EC2 instance types

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Name structure | Instance family + instance size, e.g. c7gn.xlarge. 1st position of the family = series (c), 2nd = generation (7), 3rd = options (gn); after the period = size (small, 4xlarge, metal) | no | ITN instance-type-names.html |
| Series C | Compute optimized | no | ITN instance-type-names.html |
| Series M | General purpose | no | ITN instance-type-names.html |
| Series T | Burstable performance | no | ITN instance-type-names.html |
| Series Mac | macOS | no | ITN instance-type-names.html |
| Series R | Memory optimized | no | ITN instance-type-names.html |
| Series X | Memory intensive | no | ITN instance-type-names.html |
| Series Z | High memory (also high CPU frequency, z1d) | no | ITN instance-type-names.html |
| Series U | High memory (3 TiB to 32 TiB RAM, e.g. u-6tb1, U7i) | no | ITN instance-type-names.html |
| Series I | Storage optimized | no | ITN instance-type-names.html |
| Series D | Dense storage | no | ITN instance-type-names.html |
| Series H | Listed in the current-generation list (H1) under Storage optimized; not defined in the naming table | no | ITN instance-types.html |
| Series P | GPU accelerated | no | ITN instance-type-names.html |
| Series G | Graphics intensive | no | ITN instance-type-names.html |
| Series Inf | AWS Inferentia | no | ITN instance-type-names.html |
| Series Trn | AWS Trainium | no | ITN instance-type-names.html |
| Series F | FPGA | no | ITN instance-type-names.html |
| Series VT | Video transcoding | no | ITN instance-type-names.html |
| Series DL | Appears in the accelerated list (DL1, DL2q); not defined in the naming table | no | ITN instance-types.html |
| Series Hpc | High performance computing (own category in the docs) | changed (Hpc is a separate category in current docs) | ITN instance-type-names.html |
| Series A | Powered by Arm-based AWS Graviton processors (A1 is previous generation) | no | ITN instance-type-names.html ; ITN instance-types.html |
| Option letter g | AWS Graviton processors | no | ITN instance-type-names.html |
| Option letter a | AMD processors | no | ITN instance-type-names.html |
| Option letter i | Intel processors | no | ITN instance-type-names.html |
| Option letter d | Instance store volumes | no | ITN instance-type-names.html |
| Option letter n | Network and EBS optimized | no | ITN instance-type-names.html |
| Option letter e | Extra storage (storage optimized), extra memory (memory optimized) or extra GPU memory (accelerated) | no | ITN instance-type-names.html |
| Option letter z | High CPU frequency | no | ITN instance-type-names.html |
| Option letter b | Block storage optimization | no | ITN instance-type-names.html |
| Option letter q | Qualcomm inference accelerators | no | ITN instance-type-names.html |
| Option flex | Flex instance (e.g. M7i-flex, C7i-flex) | no | ITN instance-type-names.html |
| Size "metal" | Bare metal instances | no | ITN instance-type-names.html |
| General purpose current list | Includes M5/M6/M7/M8/M9 variants (e.g. M7g, M7i, M8g, M8i, M9g), Mac1/Mac2/Mac-m4 variants, T2, T3, T3a, T4g, T8i | changed (M8*, M9g and T8i are newer than 2022) | ITN instance-types.html |
| Compute optimized current list | Includes C5, C6g/C6i, C7g/C7i/C7a, C8g/C8i, C9g (also C7i-flex, C8i-flex) | changed (C8*, C9g are newer) | ITN instance-types.html |
| Memory optimized current list | Includes R5, R6g/R6i, R7g/R7i, R8g/R8i, R9g, X1, X1e, X2gd, X8g, X8i, z1d, U-3tb1 to U-24tb1, U7i/U7in | changed (R8*, R9g, X8* are newer) | ITN instance-types.html |
| Storage optimized current list | D2, D3, D3en, H1, I3, I3en, I4g, I4i, I7i, I7ie, I8g, I8ge, Im4gn, Is4gen | changed (I7*, I8* are newer) | ITN instance-types.html |
| Accelerated current list | DL1, DL2q, F2, G4ad, G4dn, G5, G5g, G6, G6e, G7, Inf1, Inf2, P4d, P4de, P5, P5e, P5en, P6-B200, P6-B300, Trn1, Trn1n, Trn2, VT1 | changed (P6, G7, Trn2 are newer) | ITN instance-types.html |
| Latest Graviton general purpose / compute / memory generation named on docs list | M9g, C9g, R9g (M8g, C8g, R8g listed as well) | changed (Graviton4 and later families are newer than 2022) | ITN instance-types.html |
| Latest Intel general purpose generation named in docs list | M8i (M7i also listed) | changed | ITN instance-types.html |
| Previous generation examples | General purpose A1, M1 to M4, T1; compute C1, C3, C4; memory R3, R4; storage I2; accelerated G3, P3, P3dn | no | ITN instance-types.html |
| End of sale notice | U-9tb1, U-12tb1, U-18tb1, U-24tb1 no longer available for new launches; AWS recommends U7i | changed (end of sale notice is newer) | ITN instance-types.html |
| Fixed performance instances | Fixed CPU resources; can sustain full CPU at any time | no | ITN instance-types.html |
| Burstable (T) concept | Baseline CPU with ability to burst, governed by CPU credits; instance earns credits below baseline, spends above | no | ITN instance-types.html ; EC2 burstable-credits-baseline-concepts.html |
| Flex instances | C7i-flex, C8i-flex, M7i-flex, M8i-flex, R8i-flex: baseline 40 percent CPU; up to 100 percent CPU for 95 percent of the time over 24 h | changed (flex family is newer than 2022) | ITN instance-types.html |
| Burstable families named | T8i, T4g, T3a, T3 (latest generation); T2 (previous generation) | changed (T8i is newer) | EC2 burstable-performance-instances.html |
| T instance cost claim | Up to 15 percent cost saving vs M instances | no | EC2 burstable-performance-instances.html |
| T instance smallest size | As low as 2 vCPUs and 0.5 GiB memory (nano sizes) | no | EC2 burstable-performance-instances.html |
| CPU credit definition | 1 CPU credit = 1 vCPU x 100 percent utilization x 1 minute | no | EC2 burstable-credits-baseline-concepts.html |
| Baseline utilization formula | (credits earned per hour / number of vCPUs) / 60 minutes | no | EC2 burstable-credits-baseline-concepts.html |
| t3.nano credits | 6 credits per hour, max 144 accrued, 2 vCPUs, 5 percent baseline per vCPU | no | EC2 burstable-credits-baseline-concepts.html |
| t3.micro / t4g.micro credits | 12 credits per hour, max 288 accrued, 2 vCPUs, 10 percent baseline per vCPU | no | EC2 burstable-credits-baseline-concepts.html |
| t3.small / t3.medium credits | 24 credits per hour, max 576, 2 vCPUs, 20 percent baseline | no | EC2 burstable-credits-baseline-concepts.html |
| t3.large credits | 36 credits per hour, max 864, 2 vCPUs, 30 percent baseline | no | EC2 burstable-credits-baseline-concepts.html |
| t3.xlarge / t3.2xlarge credits | xlarge: 96/hr, 4 vCPUs, 40 percent; 2xlarge: 192/hr, 8 vCPUs, 40 percent | no | EC2 burstable-credits-baseline-concepts.html |
| Credit accrual limit | In general the credits earnable in 24 hours (t3.nano: 24 x 6 = 144) | no | EC2 burstable-credits-baseline-concepts.html |
| Credits on running instance | Do not expire; credits earned above the limit are discarded | no | EC2 burstable-credits-baseline-concepts.html |
| Credits after stop (T8i, T4g, T3a, T3) | Persist 7 days after the instance stops, lost thereafter | changed (T2: lost immediately on stop, 0 days) | EC2 burstable-credits-baseline-concepts.html |
| Standard mode | Instance bursts using accrued credits; with none left it falls back gradually to baseline | no | EC2 burstable-credits-baseline-concepts.html |
| Unlimited mode | Bursts beyond accrued credits using surplus credits; if average CPU over rolling 24 h exceeds baseline, billed a flat additional rate per vCPU-hour | no | EC2 burstable-credits-baseline-concepts.html |
| Default mode T3 / T3a / T4g / T8i | Unlimited (can change the account default) | changed (T2 default is Standard; T3 launched 2018 so unlimited default is not new) | EC2 burstable-performance-instances-unlimited-mode.html |
| Default mode T2 | Standard | no | EC2 burstable-credits-baseline-concepts.html |
| Launch credits | Only T2 in Standard mode; T3, T3a, T4g, T8i earn no launch credits | no | EC2 burstable-credits-baseline-concepts.html |
| T3 on Dedicated Host | Launches as standard; unlimited mode not supported | no | EC2 burstable-credits-baseline-concepts.html |
| Unlimited and Spot | AWS recommends launching burstable Spot Instances in standard mode to avoid surplus credit charges | no | EC2 burstable-performance-instances-unlimited-mode.html |
| T instance purchase options | On-Demand, Reserved, Spot; Dedicated Instances and Dedicated Hosts for T3 only | no | EC2 burstable-performance-instances.html |
| Graviton claim: cost | Graviton instances "cost up to 20% less than comparable x86-based Amazon EC2 instances" | changed (wording on current Graviton page) | https://aws.amazon.com/ec2/graviton/ |
| Graviton claim: energy | "Use up to 60% less energy than comparable EC2 instances for the same performance" | changed | https://aws.amazon.com/ec2/graviton/ |
| Graviton latest generation named | Graviton5 (192 cores, 5x larger cache, up to 33 percent lower inter-core latency per the page) | changed (Graviton5 is newer) | https://aws.amazon.com/ec2/graviton/ |
| Graviton processors | AWS-designed Arm-based; M7g page: up to 25 percent better performance than Graviton2-based M6g | no | https://aws.amazon.com/ec2/instance-types/m7g/ |
| T4g | Graviton2 (Arm Neoverse N1); up to 40 percent higher price/performance and 20 percent lower cost vs T3 | no | EC2 burstable-performance-instances.html |
| T3a | AMD processors; 10 percent lower cost than T3 | no | EC2 burstable-performance-instances.html |
| On-Demand vCPU quota, Standard (A, C, D, H, I, M, R, T, Z) | Default 5 vCPUs, adjustable | no | EC2 ec2-on-demand-instances.html |
| On-Demand vCPU quota, G/VT, P, Inf, Trn, X, DL, F, HPC, High Memory | Default 0 each, adjustable | no | EC2 ec2-on-demand-instances.html |
| Quota basis | Counted in vCPUs of running On-Demand instances; pending, stopping, stopped and hibernated do not count; unused Capacity Reservations do count | no | EC2 ec2-on-demand-instances.html |
| c7g.large (compute) | 2 vCPU, 4 GiB (2 GiB per vCPU) | no | AWS pricing JSON (awsstatic, N. Virginia, Linux) ; https://aws.amazon.com/ec2/instance-types/c7g/ |
| m7g.large (general purpose) | 2 vCPU, 8 GiB (4 GiB per vCPU) | no | AWS pricing JSON ; https://aws.amazon.com/ec2/instance-types/m7g/ |
| r7g.large (memory) | 2 vCPU, 16 GiB (8 GiB per vCPU) | no | AWS pricing JSON (awsstatic, N. Virginia, Linux) |
| Memory-per-vCPU ratio C / M / R | Compute 2, general purpose 4, memory optimized 8 GiB per vCPU (derived from the three large sizes above; c7i.large is also 2 vCPU 4 GiB) | no | AWS pricing JSON (derived) |
| m7g.medium | 1 vCPU, 4 GiB | no | AWS pricing JSON |
| m7g.large | 2 vCPU, 8 GiB | no | AWS pricing JSON |
| m7g.xlarge | 4 vCPU, 16 GiB | no | AWS pricing JSON |
| m7g.2xlarge | 8 vCPU, 32 GiB | no | AWS pricing JSON |
| m7g.4xlarge | 16 vCPU, 64 GiB | no | AWS pricing JSON |
| m7g.8xlarge | 32 vCPU, 128 GiB | no | AWS pricing JSON |
| m7g.12xlarge | 48 vCPU, 192 GiB | no | AWS pricing JSON |
| m7g.16xlarge | 64 vCPU, 256 GiB | no | AWS pricing JSON |
| m7g size ladder pattern | From large upward vCPU and memory double per step (large, xlarge, 2xlarge, 4xlarge, 8xlarge = 2, 4, 8, 16, 32 vCPU); 12xlarge is 48 vCPU; medium is 1 vCPU | no | AWS pricing JSON (derived) |
| t4g.micro | 2 vCPU, 1 GiB | no | AWS pricing JSON |
| t4g.small | 2 vCPU, 2 GiB | no | AWS pricing JSON |
| t4g.medium | 2 vCPU, 4 GiB | no | AWS pricing JSON |

### Purchasing options

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Purchasing options list | On-Demand, Savings Plans, Reserved Instances, Spot, Dedicated Hosts, Dedicated Instances, Capacity Reservations (Capacity Blocks for GPU clusters) | no | EC2 instance-purchasing-options.html |
| On-Demand billing | Pay by the second, only while in running state, 60-second minimum; no commitment | no | EC2 ec2-on-demand-instances.html ; https://aws.amazon.com/ec2/pricing/ |
| Per-second scope | Page states per-second billing with 60 s minimum for usage (not restricted to Linux on the pages read) | no | https://aws.amazon.com/ec2/pricing/ |
| On-Demand price | Fixed per-second price | no | EC2 ec2-on-demand-instances.html |
| Savings Plans basics | Commit to USD per hour of consistent usage for 1 or 3 years | no | EC2 instance-purchasing-options.html ; SP what-is-savings-plans.html |
| Term definitions | 1 year = 365 days (31,536,000 s); 3 years = 1,095 days (94,608,000 s) | no | SP what-is-savings-plans.html |
| Savings Plans types | Four: Compute, Database, EC2 Instance, SageMaker AI | changed (Database Savings Plans is a newer type) | SP plan-types.html |
| Compute Savings Plans discount | Up to 66 percent off On-Demand (plan-types page and Compute pricing page) | no | SP plan-types.html ; https://aws.amazon.com/savingsplans/compute-pricing/ |
| Compute SP flexibility | Any instance family, size, Region, OS, tenancy; also applies to Fargate and Lambda | no | SP plan-types.html |
| EC2 Instance Savings Plans discount | Up to 72 percent off On-Demand | no | SP plan-types.html |
| EC2 Instance SP flexibility | Commit to an instance family in a chosen Region (e.g. m5 in Virginia); any size, OS, tenancy within it | no | SP plan-types.html |
| Database Savings Plans | Up to 35 percent on Aurora, RDS, DynamoDB, ElastiCache, DocumentDB, Timestream, Neptune, Keyspaces, DMS, OpenSearch Service | changed (new plan type) | SP plan-types.html |
| SageMaker AI Savings Plans | Up to 64 percent off | no | SP plan-types.html |
| Savings Plans headline | "Save up to 72%" on compute | no | SP what-is-savings-plans.html ; https://aws.amazon.com/ec2/pricing/ |
| Savings Plans payment options | All upfront, Partial upfront, No upfront | no | SP what-is-savings-plans.html |
| Savings Plans commitment change | Terms cannot be changed after purchase; buy additional plans as usage changes | no | SP plan-types.html |
| Savings Plans and Spot | Spot Instances are not covered by Savings Plans; Spot spend does not use up the commitment | no | EC2 using-spot-instances.html |
| Savings Plans and Dedicated Instances | Dedicated Instances per-Region fee (2 USD/hour) is not discounted by Savings Plans | no | SP plan-types.html |
| Savings Plans cover EMR/ECS/EKS EC2 | Both Compute and EC2 Instance plans apply to EC2 in EMR, EKS, ECS clusters; EKS control-plane charges not covered | no | SP plan-types.html |
| AWS recommendation | "We recommend Savings Plans over Reserved Instances" | changed (current wording) | EC2 ec2-reserved-instances.html |
| Reserved Instance nature | Billing discount applied to matching On-Demand usage, not a physical instance | no | EC2 ec2-reserved-instances.html |
| RI pricing attributes | Instance type, Region, tenancy, platform (plus term, payment option, offering class) | no | EC2 ec2-reserved-instances.html |
| RI terms | 1 or 3 years; 3-year gives a bigger discount; not renewed automatically (reverts to On-Demand rates) | no | EC2 ec2-reserved-instances.html |
| RI payment options | All Upfront, Partial Upfront, No Upfront | no | EC2 ec2-reserved-instances.html |
| RI cancellation | Cannot cancel; may modify, exchange (Convertible) or sell (Standard) | no | EC2 ec2-reserved-instances.html |
| Standard RI discount | Up to 72 percent; averages 40 percent (1-yr) and 60 percent (3-yr) | no | https://aws.amazon.com/ec2/pricing/reserved-instances/ |
| Convertible RI discount | Up to 66 percent; averages 31 percent (1-yr) and 54 percent (3-yr) | no | https://aws.amazon.com/ec2/pricing/reserved-instances/ |
| Standard vs Convertible | Standard: bigger discount, can be modified not exchanged. Convertible: smaller discount, can be exchanged (family, type, platform, scope, tenancy) and modified | no | EC2 reserved-instances-types.html |
| Selling RIs | Only Standard RIs (regional or zonal) can be sold in the Reserved Instance Marketplace; Convertible cannot be sold or bought there | no | EC2 reserved-instances-types.html ; EC2 ri-market-general.html |
| Marketplace sale rules | At least 1 month left in term; active at least 30 days; AWS charges 12 percent service fee on the upfront price; lifetime limits 50,000 USD and 5,000 RIs; seller needs a US bank | no | EC2 ri-market-general.html |
| Regional RI | Discount applies in any AZ in the Region; does NOT reserve capacity; instance size flexibility (Linux/Unix, default tenancy) | no | EC2 reserved-instances-scope.html |
| Zonal RI | Reserves capacity in the specified AZ; discount only in that AZ; no size flexibility | no | EC2 reserved-instances-scope.html |
| RI scope and price | Scope does not affect the price | no | EC2 reserved-instances-scope.html |
| RI instance limit | Default 20 per AZ (zonal) or 20 per Region (regional) | no | EC2 ec2-capacity-reservations.html |
| Spot concept | Spare EC2 capacity at a discount; Spot price set by EC2, adjusted gradually from long-term supply and demand | changed (since 2017 no bidding; price adjusts gradually; date not on page) | EC2 using-spot-instances.html |
| Spot discount | "Discount of up to 90% compared to On-Demand prices" | no | https://aws.amazon.com/ec2/pricing/ |
| Spot capacity pool | Unused instances of same type in same AZ | no | EC2 using-spot-instances.html |
| Spot request types | One-time or persistent (persistent is resubmitted after interruption) | no | EC2 using-spot-instances.html |
| Spot interruption notice | Two-minute warning before stop or terminate; exposed via EventBridge and instance metadata; best effort; AWS recommends checking every 5 seconds | no | EC2 spot-instance-termination-notices.html |
| Spot hibernate behaviour | Interruption notice is sent but without the 2 minute lead, because hibernation starts immediately | no | EC2 spot-instance-termination-notices.html |
| Spot interruption behaviors | Terminate, stop or hibernate (set in the request) | no | EC2 spot-interruptions.html |
| Spot interruption reasons | Capacity, price (Spot price above your max price), constraints (launch group / AZ group) | no | EC2 spot-interruptions.html |
| Spot max price | Specifying one makes interruptions more frequent than not specifying | no | EC2 spot-interruptions.html |
| Metadata item for notice | meta-data/spot/instance-action (JSON with action and time); 404 if not scheduled | no | EC2 spot-instance-termination-notices.html |
| Rebalance recommendation | Signal that a running Spot Instance is at elevated risk of interruption, can arrive before the 2-minute notice | no | EC2 using-spot-instances.html |
| Spot price view | Spot price page updated every five minutes; price history for the past three months in console / CLI | no | EC2 using-spot-instances.html |
| Spot vs On-Demand availability | Spot request keeps trying until capacity exists; On-Demand returns an insufficient capacity error | no | EC2 using-spot-instances.html |
| Spot interrupted billing | Charged seconds used, full hour or nothing depending on OS and who interrupted | no | EC2 using-spot-instances.html |
| Dedicated Host | Physical server fully dedicated to you; visibility of sockets and cores; host affinity; targeted placement | no | EC2 dedicated-hosts-overview.html |
| Dedicated Host BYOL | Comprehensive BYOL support for per-socket, per-core, per-VM licenses | no | EC2 dedicated-hosts-overview.html |
| Dedicated Host billing | Per-host billing | no | EC2 dedicated-hosts-overview.html |
| Dedicated Host options | Can be bought On-Demand (hourly) or with Savings Plans; Dedicated Host Reservations up to 70 percent off | no | https://aws.amazon.com/ec2/pricing/ ; EC2 dedicated-hosts-overview.html |
| Dedicated Host restrictions | Cannot launch Dedicated Hosts in placement groups; free tier not available; Capacity Reservations not supported | no | EC2 dedicated-hosts-overview.html |
| Dedicated Instance | Instances on hardware dedicated to a single AWS account; may share hardware with your non-dedicated instances; no placement visibility or host affinity | no | EC2 dedicated-instance.html |
| Dedicated Instance billing | Per-instance billing | no | EC2 dedicated-hosts-overview.html |
| Dedicated Instance BYOL | Partial support (SQL Server License Mobility via SA, Windows VDA) | no | EC2 dedicated-instance.html |
| Dedicated Instance per-Region fee | 2 USD per hour in each Region with at least one Dedicated Instance running | no | SP plan-types.html |
| Dedicated Instance limits | EBS volume does not run on single-tenant hardware | no | EC2 dedicated-instance.html |
| On-Demand Capacity Reservation | Reserve capacity in a specific AZ for any duration; create or cancel at any time (immediate-use); no term commitment | no | EC2 ec2-capacity-reservations.html |
| ODCR discount | "No billing discount" by itself; combine with Savings Plans or Regional RIs for a discount | no | EC2 ec2-capacity-reservations.html |
| ODCR matching attributes | Instance type, platform, AZ, tenancy | no | EC2 ec2-capacity-reservations.html |
| ODCR vs zonal RI | Both reserve capacity in an AZ; zonal RI needs 1 or 3 year commitment, ODCR does not | no | EC2 ec2-capacity-reservations.html |
| ODCR quota | Counts toward On-Demand instance quota, even if unused | no | EC2 ec2-capacity-reservations.html |
| Future-dated ODCR | Reserve for a future date with a commitment duration; min 32 vCPUs | changed (future-dated reservations are newer) | EC2 ec2-capacity-reservations.html |
| Capacity Blocks for ML | Reserve GPU instances on a future date for a defined short period, placed in UltraClusters | no | EC2 ec2-capacity-blocks.html |
| Capacity Blocks limits | Start up to 8 weeks ahead; up to 64 instances per block; 256 across blocks; cannot cancel | no | EC2 ec2-capacity-blocks.html |
| Savings Plans vs Convertible RIs | FAQ: "Compute Savings Plans, which provides savings up to 66% (just like Convertible RIs)" | no | https://aws.amazon.com/savingsplans/faqs/ |
| Savings Plans vs Standard RIs | FAQ: "EC2 Instance Savings Plans, which provide savings up to 72% (just like Standard RIs)" | no | https://aws.amazon.com/savingsplans/faqs/ |
| Reservation choice guidance | Commit to usage amount: Savings Plans. Need capacity: RI or Capacity Reservation in an AZ. GPU cluster: Capacity Blocks. Interruptible OK: Spot. Compliance or licenses: Dedicated Hosts or Instances | no | EC2 instance-purchasing-options.html |

### Placement groups

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Strategies | Cluster, Partition, Spread (plus Precision time) | changed (precision time placement group is newer) | EC2 placement-groups.html |
| Placement group cost | No charge for creating a placement group | no | EC2 placement-groups.html |
| Optional | If no placement group, EC2 tries to spread instances across hardware | no | EC2 placement-groups.html |
| Cluster purpose | Instances packed close together in a single AZ; low latency, high throughput for tightly coupled HPC | no | EC2 placement-strategies.html |
| Cluster scope | Single AZ only; can span peered VPCs in same Region | no | EC2 placement-strategies.html |
| Cluster single-flow bandwidth | Up to 10 Gbps inside group vs 5 Gbps outside (enhanced networking) | no | EC2 placement-strategies.html |
| Cluster internet / Direct Connect | Traffic to internet and over Direct Connect limited to 5 Gbps | no | EC2 placement-strategies.html |
| Cluster instance types | Current generation except burstable (e.g. T2), Mac1 and M7i-flex; older A1, C3, C4, I2, M4, R3, R4 | no | EC2 placement-strategies.html |
| Cluster best practice | Single launch request, same instance type; adding later or mixing types raises insufficient capacity risk | no | EC2 placement-strategies.html |
| Cluster capacity error fix | Stop and start all instances in the group, then retry | no | EC2 placement-strategies.html |
| Cluster Capacity Reservation | Recommend an ODCR in the cluster placement group; zonal RIs cannot reserve capacity in a group | no | EC2 placement-strategies.html |
| Partition purpose | Instances in logical partitions on separate racks (own network and power); for Hadoop, Cassandra, Kafka, HDFS, HBase | no | EC2 placement-strategies.html |
| Partition limit | Max 7 partitions per AZ | no | EC2 placement-strategies.html |
| Partition scale | Instance count limited only by account limits ("hundreds of instances" not stated) | no | EC2 placement-strategies.html |
| Partition AZ scope | Can have partitions in multiple AZs in the same Region | no | EC2 placement-strategies.html |
| Partition visibility | You can see which instance is in which partition (topology-aware apps) | no | EC2 placement-strategies.html |
| Partition with Dedicated Instances | Max 2 partitions | no | EC2 placement-strategies.html |
| Partition and ODCR | Capacity Reservations do not reserve capacity in a partition group | no | EC2 placement-strategies.html |
| Spread purpose | Small group of instances on distinct hardware to reduce correlated failure | no | EC2 placement-strategies.html |
| Spread limit | Max 7 running instances per AZ per group (rack-level); 3 AZs gives 21 | no | EC2 placement-strategies.html |
| Spread AZ scope | Rack-level spread group can span multiple AZs in the Region | no | EC2 placement-strategies.html |
| Spread levels | Rack-level (Regions and Outposts); host-level (Outposts only) | changed (host-level spread is newer) | EC2 placement-strategies.html |
| Spread on Outposts | Rack spread holds as many instances as racks; host spread as many as hosts | no | EC2 placement-groups-outpost.html |
| Spread not supported | Dedicated Instances; capacity reservations do not apply | no | EC2 placement-strategies.html |
| One group per instance | An instance can be in only one placement group at a time | no | EC2 placement-groups.html |
| Merge | You cannot merge placement groups | no | EC2 placement-groups.html |
| Move instance | Instance must be stopped; add, move or remove via modify-instance-placement (empty name removes) | no | EC2 change-instance-placement-group.html |
| Dedicated Hosts and groups | Cannot launch Dedicated Hosts in placement groups | no | EC2 placement-groups.html |
| Spot hibernate/stop and groups | Cannot launch Spot that stops or hibernates on interruption in a placement group | no | EC2 placement-groups.html |
| Capacity Blocks and groups | Do not support placement groups | no | EC2 ec2-capacity-blocks.html |

### Instance metadata and user data

| Fact | Value | Changed? | Source |
|---|---|---|---|
| IMDS address | http://169.254.169.254/latest/meta-data/ (link-local, valid only from the instance) | no | EC2 instancedata-data-retrieval.html |
| IMDS IPv6 address | [fd00:ec2::254]; Nitro instances in IPv6 subnet; must be enabled explicitly | changed (IPv6 endpoint is newer) | EC2 instancedata-data-retrieval.html ; EC2 configuring-instance-metadata-options.html |
| User data URL | http://169.254.169.254/latest/user-data (404 if none) | no | EC2 instancedata-data-retrieval.html |
| Dynamic data URL | http://169.254.169.254/latest/dynamic/ | no | EC2 instancedata-data-retrieval.html |
| Metadata billing | No charge for metadata and user data HTTP requests | no | EC2 instancedata-data-retrieval.html |
| IMDSv1 | Request/response method, no token | no | EC2 configuring-instance-metadata-service.html |
| IMDSv2 | Session-oriented: PUT to /latest/api/token with X-aws-ec2-metadata-token-ttl-seconds, then GET with X-aws-ec2-metadata-token header | no | EC2 configuring-instance-metadata-service.html |
| Token TTL | Minimum 1 second, maximum 6 hours (21,600 s) | no | EC2 configuring-instance-metadata-service.html |
| Token scope | Instance-specific; invalid on other instances | no | EC2 configuring-instance-metadata-service.html |
| PUT with X-Forwarded-For | PUT requests are rejected if they contain an X-Forwarded-For header | no | EC2 configuring-instance-metadata-service.html |
| IMDSv2 errors | 401 if invalid or expired token (when token required); 403 forbidden; 404 not found | no | EC2 instancedata-data-retrieval.html |
| Default hop limit | PUT response hop limit of 1 | no | EC2 configuring-instance-metadata-service.html |
| Hop limit range | 1 to 64 | no | EC2 configuring-instance-metadata-options.html |
| Containers | Hop limit 1 can break container calls; AWS recommends hop limit 2 (or pass settings to the container) | no | EC2 instancedata-data-retrieval.html |
| Default version | "By default, you can use either IMDSv1 or IMDSv2, or both" (token optional) | no | EC2 configuring-instance-metadata-service.html |
| Require IMDSv2 | Set HttpTokens=required; IMDSv1 calls then fail | no | EC2 configuring-instance-metadata-service.html |
| Account-level default | Per Region, set default metadata version, hop limit, endpoint; applies to new instances only | changed (account-level IMDS defaults are newer; date not on page) | EC2 configuring-IMDS-new-instances.html |
| Account default IMDSv2 effect | New instances launch with HttpTokens=required and hop limit 2 (console: V2 only, hop 2) | changed | EC2 configuring-IMDS-new-instances.html |
| Account "No preference" hop limit | At launch defaults to 2 if the AMI has ImdsSupport v2.0, otherwise 1 | changed | EC2 configuring-IMDS-new-instances.html |
| AMI imds-support v2.0 | Instances from the AMI default to IMDSv2 required and hop limit 2; cannot be undone | no | EC2 configuring-IMDS-new-instances.html |
| Precedence | 1 launch template or launch parameters (a launch configuration is retired for new accounts), 2 account settings, 3 AMI | no | EC2 configuring-instance-metadata-options.html |
| IMDSv2 enforcement | Account-level HttpTokensEnforced=enabled makes launches fail unless IMDSv2 is required | changed (enforcement setting is newer) | EC2 configuring-IMDS-new-instances.html |
| Declarative policies | Account/Org IMDS settings can be set via declarative policies | changed | EC2 configuring-IMDS-new-instances.html |
| Throughput limit | 1,024 packets per second for link-local services (DNS, IMDS, Time Sync, Windows licensing) | no | EC2 instancedata-data-retrieval.html |
| User data size | Limited to 16 KB raw (before base64) | no | EC2 user-data.html |
| User data encoding | Must be base64; console / CLI v2 / Boto3 may encode for you | no | EC2 user-data.html |
| User data types (Linux) | Shell scripts (start with #!) and cloud-init directives (#cloud-config) | no | EC2 user-data.html |
| User data run frequency | By default runs only during the first boot cycle when you launch the instance | no | EC2 user-data.html |
| User data user | Scripts run as root; do not use sudo | no | EC2 user-data.html |
| User data log | /var/log/cloud-init-output.log | no | EC2 user-data.html |
| Update user data | Instance must be stopped (EBS root); updated user data is not run automatically on start | no | EC2 user-data.html |
| Windows persist tag | <persist>true</persist> runs user data on every reboot/start | no | EC2 user-data.html |
| User data and AMI | User data is an instance attribute and is not included in an AMI created from the instance | no | EC2 user-data.html |
| Instance profile | Required to give a user data script AWS credentials for API calls (IAM role in an instance profile) | no | EC2 user-data.html |
| IMDS disabled | Disabling IMDS at launch turns off access to user data and the SSH public key from metadata | no | EC2 configuring-IMDS-new-instances.html |
| Tags in metadata | Instance tags not available in metadata unless explicitly allowed | changed (tags in IMDS is newer) | EC2 configuring-IMDS-new-instances.html |

### Instance storage and states

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Instance store | Temporary block-level storage on disks physically attached to the host | no | EC2 InstanceStorage.html |
| Instance store use | Buffers, caches, scratch data, temporary content | no | EC2 InstanceStorage.html |
| Instance store cost | No additional charge; included in instance price | no | EC2 InstanceStorage.html |
| Instance store device names | ephemeral0 to ephemeral23 | no | EC2 InstanceStorage.html |
| Instance store on reboot | Data preserved | no | EC2 ec2-instance-lifecycle.html |
| Instance store on stop / hibernate / terminate | Data erased | no | EC2 ec2-instance-lifecycle.html |
| Root volume on terminate | Deleted by default (DeleteOnTermination true for root; other EBS volumes preserved) | no | EC2 ec2-instance-lifecycle.html |
| Stop/start requirement | Only EBS-backed instances can be stopped and started | no | EC2 Stop_Start.html |
| Stop/start host | Instance typically moves to a new host and gets a new public IPv4 (unless Elastic IP) | no | EC2 Stop_Start.html |
| Private IP / Elastic IP on stop | Private IPv4 and IPv6 retained; Elastic IP stays associated | no | EC2 ec2-instance-lifecycle.html |
| Reboot | Stays on same host, keeps public IP and instance store data, does not start a new billing period | no | EC2 ec2-instance-lifecycle.html |
| Billing: running | Billed per second, one-minute minimum | no | EC2 ec2-instance-lifecycle.html |
| Billing: stopped | No instance usage or data transfer charges; EBS volume storage still charged | no | EC2 ec2-instance-lifecycle.html |
| Billing: each start | New billing period, minimum one minute each stopped-to-running transition | no | EC2 ec2-instance-lifecycle.html |
| Billing: terminated | Stop incurring charges when state is shutting-down; RIs that applied still billed to end of term | no | EC2 ec2-instance-lifecycle.html |
| Billing: hibernate | Charged while in stopping state; not charged when stopped; EBS (incl. RAM storage) still charged | no | EC2 ec2-instance-lifecycle.html |
| Charges regardless of state | EBS volumes and Elastic IP addresses can incur charges regardless of instance state | no | EC2 ec2-instance-lifecycle.html |
| Hibernation mechanism | RAM contents saved to the EBS root volume; RAM reloaded on start; instance keeps ID | no | EC2 Hibernate.html |
| Hibernation: enable timing | Must enable at launch; cannot enable on an existing instance | no | EC2 hibernating-prerequisites.html |
| Hibernation: RAM limit | Linux: less than 150 GiB; Windows: 16 GiB or less | no | EC2 hibernating-prerequisites.html |
| Hibernation: root volume | Must be EBS (not instance store) and encrypted | no | EC2 hibernating-prerequisites.html |
| Hibernation: root size | Large enough to hold RAM plus OS and apps | no | EC2 hibernating-prerequisites.html |
| Hibernation: EBS types | gp2, gp3, io1, io2 | no | EC2 hibernating-prerequisites.html |
| Hibernation: bare metal | Not supported | no | EC2 hibernating-prerequisites.html |
| Hibernation: Spot | Persistent request type, no launch group | no | EC2 hibernating-prerequisites.html |
| Hibernation: Regions | All AWS Regions | no | EC2 hibernating-prerequisites.html |
| Hibernation: ODCR | Capacity Reservations do not guarantee a hibernated instance can resume | no | EC2 ec2-capacity-reservations.html |
| Shutdown behavior default | OS shutdown on EBS-backed instance stops it by default (InstanceInitiatedShutdownBehavior); instance-store root always terminates | no | EC2 ec2-instance-lifecycle.html |
| Terminated instance | Remains visible in console briefly, cannot be recovered | no | EC2 ec2-instance-lifecycle.html |

### EC2 Auto Scaling

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Auto Scaling group | Collection of EC2 instances managed as a logical unit | no | ASG what-is-amazon-ec2-auto-scaling.html |
| Min size | Group never goes below it | no | ASG what-is-amazon-ec2-auto-scaling.html |
| Max size | Group never goes above it | no | ASG what-is-amazon-ec2-auto-scaling.html |
| Desired capacity | Group maintains this many instances | no | ASG what-is-amazon-ec2-auto-scaling.html |
| Docs example | Min 4, desired 6, max 12 | no | ASG what-is-amazon-ec2-auto-scaling.html |
| Scaling bounds | Dynamic scaling never goes outside min/max (except weighted instances) | no | ASG as-scale-based-on-demand.html |
| Pricing | No additional fee; pay for the underlying resources | no | ASG what-is-amazon-ec2-auto-scaling.html |
| Launch configurations (retired for new accounts): limit 1 | "As of January 1, 2023, new Amazon EC2 instance types are no longer supported in launch configurations" | changed 2023-01-01 | ASG launch-configurations.html |
| Launch configurations (retired for new accounts): limit 2 | "Accounts created on or after June 1, 2023 cannot create new launch configurations using the console" | changed 2023-06-01 | ASG launch-configurations.html |
| Launch configurations (retired for new accounts): limit 3 | "Accounts created on or after October 1, 2024 cannot create new launch configurations using any method (console, API, AWS CLI, or CloudFormation)" | changed 2024-10-01 | ASG launch-configurations.html |
| Launch configurations (retired for new accounts): guidance | "Migrate to launch templates" | changed | ASG launch-configurations.html |
| Launch configurations (retired for new accounts): immutable | Cannot modify a launch configuration after creation; only one per group | no | ASG launch-configurations.html |
| Health sources | EC2, Elastic Load Balancing, VPC Lattice, EBS, custom health checks | changed (VPC Lattice and EBS health checks are newer) | ASG ec2-auto-scaling-health-checks.html |
| Unhealthy action | InService unhealthy instance is replaced to maintain desired capacity | no | ASG ec2-auto-scaling-health-checks.html |
| Default health check | EC2 status checks built in; ELB check is optional | no | ASG ec2-auto-scaling-health-checks.html |
| Health check grace period default | 300 seconds in the console; 0 seconds when using CLI or SDK | no | ASG health-check-grace-period.html |
| Grace period meaning | Minimum time to keep a new instance in service before terminating it for failing health checks | no | ASG health-check-grace-period.html |
| Grace period exception | If instance is no longer in EC2 running state it is replaced immediately (e.g. you stop it) | no | ASG health-check-grace-period.html |
| Default cooldown | 300 seconds (not set in console at creation; editable afterwards) | no | ASG ec2-auto-scaling-scaling-cooldowns.html |
| Cooldown applies to | Simple scaling policies | no | ASG ec2-auto-scaling-scaling-cooldowns.html |
| Cooldown exceptions | Target tracking, step scaling and scheduled actions can scale immediately; unhealthy replacement ignores cooldown; manual scaling ignores it by default | no | ASG ec2-auto-scaling-scaling-cooldowns.html |
| AWS guidance on simple scaling | "We recommend that you do not use simple scaling policies and scaling cooldowns"; prefer target tracking or step | changed (guidance wording) | ASG ec2-auto-scaling-scaling-cooldowns.html |
| ELB deregistration in cooldown | ELB waits 300 seconds by default for deregistration | no | ASG ec2-auto-scaling-scaling-cooldowns.html |
| Dynamic policy types | Target tracking, step scaling, simple scaling | no | ASG as-scale-based-on-demand.html |
| Recommended policy | Target tracking is strongly recommended | no | ASG as-scale-based-on-demand.html |
| Target tracking predefined metrics | ASGAverageCPUUtilization, ASGAverageNetworkIn, ASGAverageNetworkOut, ALBRequestCountPerTarget | no | ASG as-scaling-target-tracking.html |
| Target tracking alarms | Auto Scaling creates and manages the CloudWatch alarms; do not edit them | no | ASG as-scaling-target-tracking.html |
| Target tracking scale-in | Scales in only if all target tracking policies are ready to scale in; scale-out if any is ready | no | ASG as-scaling-target-tracking.html |
| Target tracking ELB RequestCount | Load balancer RequestCount does not work as a target tracking metric; use ALBRequestCountPerTarget | no | ASG as-scaling-target-tracking.html |
| Step scaling | Adjustments vary with alarm breach size; you create the CloudWatch alarms | no | ASG as-scaling-simple-step.html |
| Simple scaling | Single adjustment plus cooldown | no | ASG as-scaling-simple-step.html |
| Adjustment types | ChangeInCapacity, ExactCapacity, PercentChangeInCapacity | no | ASG as-scaling-simple-step.html |
| Multiple policies | When several policies trigger, the one giving the largest capacity wins | no | ASG as-scale-based-on-demand.html |
| Scheduled scaling | Scheduled actions change min, max, desired at a time; one-time or recurring (cron) | no | ASG ec2-auto-scaling-scheduled-scaling.html |
| Scheduled limit | Max 125 scheduled actions per group | no | ASG ec2-auto-scaling-scheduled-scaling.html |
| Scheduled time zone | UTC by default; IANA time zones supported (DST aware) | no | ASG ec2-auto-scaling-scheduled-scaling.html |
| Predictive scaling | Analyses historical load for daily/weekly patterns to forecast and add capacity ahead of time | changed (predictive scaling is newer than 2022 GA of EC2 ASG feature set; date not on page) | ASG ec2-auto-scaling-predictive-scaling.html |
| Default instance warmup | Not enabled or configured by default; AWS strongly recommends setting it | no | ASG ec2-auto-scaling-default-instance-warmup.html |
| Warmup fallback | If unset, target tracking/step use the default cooldown value; instance refresh uses the health check grace period | no | ASG ec2-auto-scaling-default-instance-warmup.html |
| Warmup starting point | AWS suggests 300 seconds if unsure | no | ASG ec2-auto-scaling-default-instance-warmup.html |
| Warmup effect | Warming instances are not counted in aggregated metrics; scale-in blocked until warmup done | no | ASG ec2-auto-scaling-default-instance-warmup.html |
| Default termination policy | 1) Pick the AZ with the most instances 2) outdated configuration first (launch configuration, retired for new accounts; then different launch template, then oldest template version) 3) closest to next billing hour 4) random | no | ASG ec2-auto-scaling-termination-policies.html |
| AZ balance first | AZ balancing takes precedence over the termination policy | no | ASG ec2-auto-scaling-termination-policies.html |
| Billing-hour criterion | Docs note most EC2 is per-second billed so this criterion helps less | changed (note is newer) | ASG ec2-auto-scaling-termination-policies.html |
| Predefined termination policies | Default, AllocationStrategy, OldestLaunchTemplate, OldestLaunchConfiguration, ClosestToNextInstanceHour, NewestInstance, OldestInstance | no | ASG ec2-auto-scaling-termination-policies.html |
| Unhealthy and termination policy | Instances already unhealthy skip termination policy evaluation | no | ASG ec2-auto-scaling-termination-policies.html |
| Lifecycle hooks purpose | Pause instance in a wait state at launch or terminate to run custom actions | no | ASG lifecycle-hooks.html |
| Lifecycle hook default timeout | One hour (3,600 s) heartbeat timeout | no | ASG lifecycle-hooks.html |
| Lifecycle hook global timeout | 48 hours or 100 times the heartbeat timeout, whichever is smaller | no | ASG lifecycle-hooks.html |
| Lifecycle hook result | Continue or abandon (abandon on launch: instance terminated and replaced) | no | ASG lifecycle-hooks.html |
| Lifecycle hook notifications | Sent to Amazon EventBridge by default | no | ASG lifecycle-hooks.html |
| Termination hook | Best effort by default; if timed out or abandoned, termination proceeds | changed (instance lifecycle policy for retention is newer) | ASG lifecycle-hooks.html |
| Warm pool | Pool of pre-initialized instances beside the group to cut scale-out latency | no | ASG ec2-auto-scaling-warm-pools.html |
| Warm pool states | Stopped, Running, Hibernated | no | ASG ec2-auto-scaling-warm-pools.html |
| Warm pool cost | Stopped: pay only for EBS volumes and Elastic IPs; Running not recommended | no | ASG ec2-auto-scaling-warm-pools.html |
| Warm pool default size | Max capacity minus desired capacity | no | ASG ec2-auto-scaling-warm-pools.html |
| Warm pool limits | No weighted mixed groups; no Spot in mixed groups; EBS root required | changed (mixed instances support is newer) | ASG ec2-auto-scaling-warm-pools.html |
| Instance refresh | Rolling replacement of instances after AMI or launch template change | no | ASG asg-instance-refresh.html |
| Instance refresh min healthy default | 90 percent (when no instance maintenance policy) | no | ASG understand-instance-refresh-default-values.html |
| Instance refresh max healthy default | 100 percent / null (when no maintenance policy) | no | ASG understand-instance-refresh-default-values.html |
| Instance refresh other defaults | Checkpoints off; checkpoint delay 3600 s; auto rollback off; bake time zero | changed (rollback and bake time are newer) | ASG understand-instance-refresh-default-values.html |
| Instance refresh skip matching | Disabled in CLI/SDK, enabled in console | changed | ASG understand-instance-refresh-default-values.html |
| Mixed instances group | Multiple instance types and purchase options (On-Demand and Spot) in one group | no | ASG ec2-auto-scaling-mixed-instances-groups.html |
| RI / SP in mixed groups | Discounts apply to On-Demand portion | no | ASG ec2-auto-scaling-mixed-instances-groups.html |
| Spot allocation: price-capacity-optimized | Recommended; considers price and capacity | changed (newer than 2022) | ASG allocation-strategies.html |
| Spot allocation: capacity-optimized | Launches from the pool with optimal capacity; also capacity-optimized-prioritized | no | ASG allocation-strategies.html |
| Spot allocation: lowest-price | "Not recommended", highest interruption risk; CLI only | changed | ASG allocation-strategies.html |
| On-Demand allocation | lowest-price or prioritized | no | ASG allocation-strategies.html |
| Capacity Rebalancing | Proactively replaces Spot Instances that get a rebalance recommendation; launches new, then terminates old | no | ASG ec2-auto-scaling-capacity-rebalancing.html |
| Capacity Rebalancing max overshoot | Group may temporarily exceed max by up to 10 percent of desired capacity | no | ASG ec2-auto-scaling-capacity-rebalancing.html |
| Capacity Rebalancing off | Without it, Spot replaced only after interruption and failed health check | no | ASG ec2-auto-scaling-capacity-rebalancing.html |
| Max instance lifetime minimum | At least 86,400 seconds (one day); 0 clears the setting | no | ASG asg-max-instance-lifetime.html |
| Max instance lifetime console | Cannot be set at group creation in console; edit after | no | ASG asg-max-instance-lifetime.html |
| AZ distribution | Auto Scaling launches in the AZ with fewest instances to keep balance | no | ASG auto-scaling-benefits.html |
| AZ rebalancing | Launches new before terminating old; may exceed max by 10 percent or one instance, whichever is greater | no | ASG auto-scaling-benefits.html |
| AZ rebalancing triggers | AZ list change, terminate/detach/standby, AZ recovery, Spot price back below max | no | ASG auto-scaling-benefits.html |
| Suspend processes | Launch, Terminate, AddToLoadBalancer, AlarmNotification, AZRebalance, HealthCheck, InstanceRefresh, ReplaceUnhealthy, ScheduledActions | no | ASG as-suspend-resume-processes.html |
| Administrative suspension | Auto Scaling may suspend processes for groups failing to launch for over 24 hours | no | ASG as-suspend-resume-processes.html |
| Load balancer integration | Instances auto-registered / deregistered with target groups | no | ASG what-is-amazon-ec2-auto-scaling.html |
| Target tracking proportionality | "With target tracking, your Auto Scaling group scales in direct proportion to the actual load on your application"; works best with a metric that changes inversely proportional to group size | no | ASG as-scale-based-on-demand.html |
| Target tracking rounding | "We round up and add two instances" (example: 1.5 needed); also chooses not to scale in until removal will not cause oscillation | no | ASG as-scaling-target-tracking.html |
| Target tracking scale-in pace | "Prioritizes availability ... by scaling in more gradually when traffic is decreasing" | no | ASG as-scaling-target-tracking.html |
| Step scaling bounds above threshold | Metric above breach threshold: lower bound inclusive, upper bound exclusive | no | ASG as-scaling-simple-step.html |
| Step scaling bounds below threshold | Metric below breach threshold: lower bound exclusive, upper bound inclusive | no | ASG as-scaling-simple-step.html |

### Elastic Load Balancing

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Load balancer types | Application, Network, Gateway, Classic | no | ALB introduction.html |
| ALB layer | Layer 7 (application layer) | no | ALB introduction.html |
| ALB protocols | Listeners: HTTP, HTTPS; ports 1 to 65535; WebSockets native; HTTP/2 on HTTPS listeners (128 parallel requests) | no | ALB load-balancer-listeners.html |
| ALB minimum AZs | At least two Availability Zones required (one subnet per AZ) | no | ELB how-elastic-load-balancing-works.html ; ALB application-load-balancers.html |
| ALB subnet size | At least /27 and 8 free IPs per subnet | no | ALB application-load-balancers.html |
| ALB routing algorithm | Round robin default; least outstanding requests; weighted random | changed (weighted random is newer) | ALB edit-target-group-attributes.html |
| ALB components | Listener, rules (priority, actions, conditions), target groups | no | ALB introduction.html |
| ALB default rule | Every listener has one, no conditions, evaluated last, cannot be deleted | no | ALB listener-rules.html |
| ALB rule evaluation | Lowest priority number first | no | ALB listener-rules.html |
| ALB rule actions | Exactly one of forward, redirect, fixed-response, last in the rule; authentication actions are separate actions | no | ALB listener-rules.html |
| ALB rule conditions | host-header, http-request-method, path-pattern, source-ip; also http-header and query-string | no | ALB listener-rules.html |
| ALB condition limits | Up to 3 comparison strings per condition and 5 per rule | no | ALB listener-rules.html |
| ALB rule transforms | Host header rewrite and URL rewrite (one each per rule) | changed (rule transforms are newer) | ALB listener-rules.html |
| ALB rules per ALB | 100 (excluding default), adjustable | no | ALB load-balancer-limits.html |
| ALB condition values per rule | 5, not adjustable | no | ALB load-balancer-limits.html |
| ALBs per Region | 50 | no | ALB load-balancer-limits.html |
| ALB listeners per ALB | 50 | no | ALB load-balancer-limits.html |
| ALB target groups per ALB | 100 | no | ALB load-balancer-limits.html |
| ALB targets per ALB | 1,000 | no | ALB load-balancer-limits.html |
| ALB certificates per ALB | 25 (excluding default) | no | ALB load-balancer-limits.html |
| Targets per target group | 1,000 (instances or IPs); Lambda: 1 | no | ALB load-balancer-limits.html |
| Load balancers per target group | 1 | no | ALB load-balancer-limits.html |
| Target groups per Region | 3,000 (shared with NLB) | no | ALB load-balancer-limits.html |
| Target types | instance, ip, lambda (alb for NLB target) | no | ALB target-group-register-targets.html ; NLB edit-target-group-attributes.html |
| IP targets CIDRs | Subnets of target group VPC, 10.0.0.0/8, 100.64.0.0/10, 172.16.0.0/12, 192.168.0.0/16 | no | ALB target-group-register-targets.html |
| Lambda target | Targets per group: 1; health check defaults differ (timeout 30 s, interval 35 s) | no | ALB target-group-health-checks.html |
| Health check interval default | 30 seconds (instance / ip); range 5 to 300 | no | ALB target-group-health-checks.html |
| Health check timeout default | 5 seconds (instance / ip); range 2 to 120 | no | ALB target-group-health-checks.html |
| Healthy threshold default | 5 (range 2 to 10) | no | ALB target-group-health-checks.html |
| Unhealthy threshold default | 2 (range 2 to 10) | no | ALB target-group-health-checks.html |
| Success codes default | 200 (HTTP range 200 to 499); gRPC default 12 | no | ALB target-group-health-checks.html |
| Health check path default | / | no | ALB target-group-health-checks.html |
| Health check protocol | HTTP (default) or HTTPS, GET method | no | ALB target-group-health-checks.html |
| Fail-open | If all targets unhealthy, ALB routes to all targets regardless | no | ALB target-group-health-checks.html |
| Deregistration delay default | 300 seconds (connection draining) | no | ALB edit-target-group-attributes.html |
| Deregistration early finish | Completes immediately if no in-flight requests | no | ALB edit-target-group-attributes.html |
| Slow start | Linear ramp for new targets; not available with least outstanding requests or weighted random; 0 disables | no | ALB edit-target-group-attributes.html |
| Sticky sessions | Target-group level; duration-based cookie AWSALB or application-based cookie; duration 1 second to 7 days | no | ALB edit-target-group-attributes.html |
| Stickiness requirement | Not supported when cross-zone load balancing is off for the target group | no | ALB edit-target-group-attributes.html |
| Stickiness cookie lifetime | Generated cookie has own 7 day expiry (non-configurable) | no | ALB edit-target-group-attributes.html |
| ALB cross-zone | Always on at load balancer level, cannot be turned off | no | ALB application-load-balancers.html |
| ALB cross-zone per target group | Can be turned off at the target group level (default inherits LB) | changed (target-group level override is newer; date not on page) | ALB edit-target-group-attributes.html |
| ALB idle timeout | Default 60 seconds | no | ALB application-load-balancers.html |
| ALB deletion protection | Default off | no | ALB application-load-balancers.html |
| ALB desync mitigation default | defensive | no | ALB application-load-balancers.html |
| ALB X-Forwarded-For | ALB adds X-Forwarded-For, X-Forwarded-Proto, X-Forwarded-Port; xff_header_processing.mode default append (preserve or remove optional) | no | ELB how-elastic-load-balancing-works.html ; ALB application-load-balancers.html |
| ALB IP address types | ipv4, dualstack, dualstack-without-public-ipv4 | changed (dualstack-without-public-ipv4 is newer) | ALB application-load-balancers.html |
| ALB SNI / certificates | HTTPS listener needs at least one certificate; multiple certificates up to 25 plus default | no | ALB load-balancer-listeners.html ; ALB load-balancer-limits.html |
| ALB advantages over CLB | Path, host, header, method, query, source IP routing; redirect; fixed response; IP and Lambda targets; user authentication; per-target-group health checks | no | ALB introduction.html |
| ALB with WAF | AWS WAF can be attached to an ALB | no | ALB introduction.html |
| ALB pricing model | Hourly plus LCU-hours | no | https://aws.amazon.com/elasticloadbalancing/pricing/ |
| NLB layer | Layer 4 (connection level) | no | ELB how-elastic-load-balancing-works.html |
| NLB protocols | TCP, UDP, TLS (also TCP_UDP, QUIC target group protocols appear in docs) | changed (QUIC protocols are newer) | ELB how-elastic-load-balancing-works.html ; NLB edit-target-group-attributes.html |
| NLB static IP | One IP address per enabled AZ (network interface); optional Elastic IP per AZ | no | ELB how-elastic-load-balancing-works.html |
| NLB source IP | Client IP preservation default enabled for instance targets; IP targets TCP/TLS default disabled | no | NLB edit-target-group-attributes.html |
| NLB flow hash | Flow hash on protocol, source IP/port, destination IP/port, TCP sequence number | no | ELB how-elastic-load-balancing-works.html |
| NLB TCP idle timeout | 350 seconds default (60 to 6000 adjustable); TLS 350 s fixed; UDP 120 s fixed | no | NLB network-load-balancers.html |
| NLB cross-zone | Disabled by default; can enable; EC2 inter-AZ data transfer charges apply when enabled | no | NLB edit-target-group-attributes.html ; ELB how-elastic-load-balancing-works.html |
| NLB security groups | Can associate at creation and change later; if created without any SG, cannot add one later | changed (NLB security group support is newer than 2022; date not on page) | NLB load-balancer-security-groups.html |
| NLB deregistration delay | 300 seconds default | no | NLB edit-target-group-attributes.html |
| NLB connection termination for unhealthy | Enabled by default | changed | NLB edit-target-group-attributes.html |
| NLB proxy protocol | v2 supported; needed to see client IP via PrivateLink | no | NLB edit-target-group-attributes.html |
| NLB IP types | ipv4 and dualstack | no | NLB network-load-balancers.html |
| GWLB layer | Layer 3 (network layer) | no | GWLB introduction.html |
| GWLB protocol | GENEVE on port 6081 | no | GWLB introduction.html |
| GWLB purpose | Deploy, scale, manage virtual appliances (firewalls, IDS/IPS, deep packet inspection); transparent network gateway plus load balancer | no | GWLB introduction.html |
| GWLB listens | All IP packets across all ports | no | GWLB introduction.html |
| GWLB flow stickiness | 5-tuple default (also 3-tuple, 2-tuple) | no | GWLB introduction.html |
| GWLB endpoints | VPC endpoint providing private connectivity between consumer VPC and appliance VPC; used as route table next hop | no | GWLB introduction.html |
| GWLB cross-zone | Disabled by default | no | ELB how-elastic-load-balancing-works.html |
| GWLB MTU | 8500 | no | ELB how-elastic-load-balancing-works.html |
| LB MTU | Jumbo frames (9001) on ALB, NLB, CLB nodes | no | ELB how-elastic-load-balancing-works.html |
| Classic Load Balancer status | "Classic Load Balancers are the previous generation of load balancers from Elastic Load Balancing. We recommend that you migrate to a current generation load balancer." | changed (current wording; EC2-Classic retired 2022-08-15 not stated on page) | CLB introduction.html |
| CLB features | TCP and SSL listeners; sticky sessions with application cookies | no | CLB introduction.html |
| CLB cross-zone | API/CLI: disabled by default; console: option selected by default | no | ELB how-elastic-load-balancing-works.html |
| CLB routing | Round robin for TCP; least outstanding requests for HTTP/HTTPS | no | ELB how-elastic-load-balancing-works.html |
| CLB IP types | IPv4 only | no | ELB how-elastic-load-balancing-works.html |
| Cross-zone summary | ALB on (target group override), NLB off, GWLB off, CLB console on / API off | no | ELB how-elastic-load-balancing-works.html |
| Cross-zone effect example | 2 targets in AZ A, 8 in AZ B: enabled 10 percent each; disabled 25 percent and 6.25 percent | no | ELB how-elastic-load-balancing-works.html |
| LB DNS TTL | 60 seconds | no | ELB how-elastic-load-balancing-works.html |
| LB schemes | internal (private IPs) or internet-facing (public IPs) | no | ELB how-elastic-load-balancing-works.html |
| Targets need no public IP | LB routes to targets via private IPs | no | ELB how-elastic-load-balancing-works.html |
| Connection draining | Called deregistration delay on ALB/NLB; status "draining" | no | ALB target-group-register-targets.html |
| ALB and ASG | Instances launched by ASG are auto-registered with attached target group | no | ALB target-group-register-targets.html |
| Zonal shift | ARC zonal shift supported on load balancers | changed (zonal shift is newer) | ELB how-elastic-load-balancing-works.html |
| Rule priority range | Integer, minimum 1, maximum 50000; a listener cannot have two rules with the same priority | no | https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_CreateRule.html |
| Slow start range | 30 to 900 seconds; default 0 (disabled) | no | https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_TargetGroupAttribute.html |
| Deregistration delay range | 0 to 3600 seconds, default 300 | no | https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_TargetGroupAttribute.html |
| Stickiness duration range | 1 second to 1 week (604,800 s); default 1 day (86,400 s) for lb_cookie and app_cookie | no | https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_TargetGroupAttribute.html |
| Condition: host-header case | "A hostname is not case-sensitive", up to 128 characters, needs at least one "."; wildcards * (0 or more) and ? (exactly 1) | no | ALB rule-condition-types.html |
| Host wildcard example | *.example.com matches test.example.com but not example.com | no | ALB rule-condition-types.html |
| Condition: path-pattern case | "A path pattern is case-sensitive", up to 128 characters; wildcards * and ? | no | ALB rule-condition-types.html |
| Path pattern scope | "Applied only to the path of the URL, not to its query parameters"; evaluated after URI normalization; does not alter the request | no | ALB rule-condition-types.html |
| Condition: http-header case | "The header name and the match evaluation are not case-sensitive"; wildcards * and ? allowed in values, not in the header name | no | ALB rule-condition-types.html |
| Condition: http-request-method case | "The match evaluation is case-sensitive"; wildcards not supported (exact match); standard or custom methods | no | ALB rule-condition-types.html |
| Condition: query-string case | "The match evaluation is not case-sensitive"; wildcards * and ? supported; key/value pairs or value only | no | ALB rule-condition-types.html |
| Condition: source-ip | CIDR format, IPv4 and IPv6; no wildcards; matches proxy IP, not X-Forwarded-For (use http-header for that) | no | ALB rule-condition-types.html |
| Regex matching | host-header, http-header and path-pattern support value matching or regex (RegexValues); no lookaheads, lookbehinds, backreferences | changed (regex conditions are newer) | ALB rule-condition-types.html |
| Match evaluations | Up to 3 per condition, 5 per rule | no | ALB rule-condition-types.html |

## Storage (week 04)

Source key: S3UG = docs.aws.amazon.com/AmazonS3/latest/userguide/ · EBS = docs.aws.amazon.com/ebs/latest/userguide/ · EFS = docs.aws.amazon.com/efs/latest/ug/ · FSXW = docs.aws.amazon.com/fsx/latest/WindowsGuide/ · FSXL = …/fsx/latest/LustreGuide/ · FSXO = …/fsx/latest/ONTAPGuide/ · FSXZ = …/fsx/latest/OpenZFSGuide/ · SGW = docs.aws.amazon.com/storagegateway/latest/ (vgw/ Volume Gateway, tgw/ Tape Gateway) · FGW = docs.aws.amazon.com/filegateway/latest/ (files3/ S3 File Gateway, filefsxw/ FSx File Gateway) · CF = docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/ · ALB = docs.aws.amazon.com/elasticloadbalancing/latest/application/ · BKP = docs.aws.amazon.com/aws-backup/latest/devguide/ · DS = docs.aws.amazon.com/datasync/latest/userguide/ · TF = docs.aws.amazon.com/transfer/latest/userguide/ · SNOW = docs.aws.amazon.com/snowball/latest/developer-guide/ · WN = aws.amazon.com/about-aws/whats-new/ (page name follows). Research: docs/research/2026-10-12-storage-facts.md, official pages read 2026-10-11. Where a row says "changed", teach today's value and name the old one once; where two official pages disagree on a number, the course states no number (see Not confirmed). Classic exam behaviour still centres the questions; no question depends on a "changed" row from 2025 or later.

### S3 basics

| Fact | Value | Changed? | Source |
|---|---|---|---|
| S3 Standard design durability | 99.999999999 % (11 nines) | no | S3UG storage-class-intro.html |
| S3 Standard design availability | 99.99 % | no | S3UG storage-class-intro.html |
| S3 Standard-IA design durability / availability | 99.999999999 % / 99.9 % | no | S3UG storage-class-intro.html |
| S3 Intelligent-Tiering design durability / availability | 99.999999999 % / 99.9 % | no | S3UG storage-class-intro.html |
| S3 One Zone-IA design durability / availability | 99.999999999 % / 99.5 % | no | S3UG storage-class-intro.html |
| S3 Express One Zone design durability / availability | 99.999999999 % / 99.95 % | no | S3UG storage-class-intro.html |
| Glacier Instant Retrieval design durability / availability | 99.999999999 % / 99.9 % | no | S3UG storage-class-intro.html |
| Glacier Flexible Retrieval design durability / availability | 99.999999999 % / 99.99 % (after you restore objects) | no | S3UG storage-class-intro.html |
| Glacier Deep Archive design durability / availability | 99.999999999 % / 99.99 % (after you restore objects) | no | S3UG storage-class-intro.html |
| Reduced Redundancy Storage | Not recommended; durability 99.99 %, availability 99.99 %; "S3 Standard is more cost-effective" | no | S3UG storage-class-intro.html |
| Resilience to loss of an AZ | All classes except One Zone-IA and S3 Express One Zone are designed to survive the physical loss of an AZ | no | S3UG storage-class-intro.html |
| Max object size | 50 TB in all Regions, all storage classes (10x the previous 5 TB) | changed 2025-12-02 (was 5 TB) | WN 2025/12/amazon-s3-maximum-object-size-50-tb/ ; S3UG upload-objects.html |
| Single PUT limit | Up to 5 GB in one PUT operation (SDKs, REST API, CLI) | no | S3UG upload-objects.html |
| Console upload limit | Largest single file uploadable in the S3 console: 160 GB; larger files need CLI, SDK or REST API | no | S3UG upload-objects.html |
| Multipart upload size range | Multipart upload usable for objects from 5 MB to 50 TB | changed (upper end was 5 TB before 2025-12-02) | S3UG upload-objects.html |
| When to use multipart | "In general, when your object size reaches 100 MB, you should consider using multipart uploads" | no | S3UG qfacts.html |
| Part size | 5 MiB to 5 GiB; no minimum size for the last part | no | S3UG qfacts.html |
| Max parts per upload | 10,000 (part numbers 1 to 10,000) | no | S3UG qfacts.html |
| List parts / list uploads page | A list parts request and a list multipart uploads request each return at most 1,000 | no | S3UG qfacts.html |
| ListObjectsV2 page | Up to 1,000 keys per request | no | facts.md (S3 API ListObjectsV2); not re-read today |
| Transfers above 5 TB | AWS says use the S3 Transfer Manager in Java v1/v2, Python or AWS CLI SDKs, ideally with the latest AWS Common Runtime | changed 2025-12 (new guidance) | S3UG upload-objects.html |
| Console rename or property change | Creates a new object (new version if versioning is on) | no | S3UG upload-objects.html |
| Tags per object | Up to 10 tags; key up to 128 Unicode characters, value up to 255 | no | S3UG upload-objects.html |
| User-defined metadata | Up to 2 KB | no | S3UG upload-objects.html |
| Strong consistency | Strong read-after-write consistency for PUT and DELETE of objects in all Regions (new writes, overwrites, deletes); list-after-write also consistent | changed (strong consistency since Dec 2020; was eventual for overwrites/deletes) | S3UG Welcome.html |
| Strong consistency also covers | Reads, ACLs, object tags and object metadata (HEAD); the page also names the retired-for-new-customers S3 Select | no | S3UG Welcome.html |
| Single-key updates | Atomic; concurrent PUTs resolved last-writer-wins by timestamp; no atomic updates across keys; no object locking for concurrent writers | no | S3UG Welcome.html |
| Bucket configurations | Eventually consistent (e.g. deleted bucket may still be listed) | no | S3UG Welcome.html |
| After enabling versioning | Wait about 15 minutes before issuing writes to the bucket (propagation) | no | S3UG Welcome.html |
| Request rate per prefix | At least 3,500 PUT/COPY/POST/DELETE and 5,500 GET/HEAD requests per second per partitioned prefix | no | S3UG optimizing-performance.html |
| Prefix count | No limit to the number of prefixes in a bucket; 10 prefixes in parallel scale reads to 55,000 per second | no | S3UG optimizing-performance.html |
| Scaling behaviour | Scales gradually; you may see 503 (Slow Down) while it scales | no | S3UG optimizing-performance.html |
| Latency | Small-object and first-byte latencies of roughly 100 to 200 ms | no | S3UG optimizing-performance.html |
| Single-instance throughput | Up to 100 Gb/s on one EC2 instance (data lake workloads) | no | S3UG optimizing-performance.html |
| Bucket name length | 3 to 63 characters | no | S3UG bucketnamingrules.html |
| Bucket name characters | Lowercase letters, numbers, periods, hyphens; begin and end with letter or number; no two adjacent periods; not formatted like an IP address | no | S3UG bucketnamingrules.html |
| Reserved prefixes | Must not start with xn--, sthree-, amzn-s3-demo- | no | S3UG bucketnamingrules.html |
| Reserved suffixes | Must not end with -s3alias, --ol-s3, .mrap, --x-s3 (directory buckets), --table-s3; -an only for account regional namespace | changed (--table-s3 and -an are newer) | S3UG bucketnamingrules.html |
| Global namespace | General purpose bucket names must be unique across all AWS accounts in all Regions of a partition; partitions: aws, aws-cn, aws-us-gov, aws-eusc | changed (aws-eusc partition is newer) | S3UG bucketnamingrules.html |
| Account regional namespace | Optional namespace only your account can use; name format prefix-accountId-region-an; created with x-amz-bucket-namespace: account-regional | changed (new feature) | S3UG bucketnamingrules.html |
| Name and Region are fixed | After creation you cannot change the bucket name or Region | no | S3UG bucketnamingrules.html |
| Name reuse after delete | After deleting a bucket another account may take the name; reuse is not guaranteed to be possible immediately or at all | no | S3UG bucketnamingrules.html |
| Periods in names | Avoid; breaks virtual-hosted-style HTTPS; Transfer Acceleration buckets cannot have periods | no | S3UG bucketnamingrules.html |
| Pre-2018 N. Virginia names | Before 2018-03-01 buckets in us-east-1 could be up to 255 characters with uppercase and underscores | no | S3UG bucketnamingrules.html |
| General purpose bucket quota | Default 10,000 buckets per account; increase through Service Quotas (view/manage from us-east-1); up to 1 million buckets on request | changed 2024-11 (was 100 default, 1,000 max) | S3UG BucketRestrictions.html ; WN 2024/11/amazon-s3-up-1-million-buckets-per-aws-account/ |
| Bucket size and object count | No maximum bucket size and no limit on number of objects per bucket | no | S3UG BucketRestrictions.html |
| Bucket types | General purpose, directory, table, vector buckets | changed (table and vector buckets are newer) | S3UG Welcome.html |
| Directory bucket purpose | Low-latency (single AZ, S3 Express One Zone) and data residency (Local Zones, One Zone-IA) | changed (new bucket type) | S3UG Welcome.html |
| Directory bucket quota | Up to 100 directory buckets per account (adjustable); no limit on objects | no | S3UG directory-buckets-overview.html |
| Directory bucket request limits | Up to 200,000 read TPS and 100,000 write TPS per bucket; no prefix limits | no | S3UG directory-buckets-overview.html |
| Directory bucket namespace | Hierarchical directories, only delimiter is "/"; ListObjectsV2 returns unsorted results; name format base--zone-id--x-s3 | no | S3UG directory-buckets-overview.html |
| Directory bucket security | Block Public Access on, ACLs disabled (bucket owner enforced); settings cannot be modified | no | S3UG directory-buckets-overview.html |
| Inactive directory buckets | AZ directory buckets with no requests for 90 days become inactive (503 until reactivated, minutes); not applicable in Local Zones | changed (newer behaviour) | S3UG directory-buckets-overview.html |
| General purpose bucket default access | Private by default; Block Public Access on at bucket level | changed (BPA default on since 2023-04) | S3UG Welcome.html |
| Bucket policy size | Up to 20 KB | no | S3UG Welcome.html |
| Delete a bucket | Bucket must be empty (all objects, all versions, delete markers) and have no attached access points; not restorable by AWS; queued for deletion and propagates over time | no | S3UG delete-bucket.html ; S3UG empty-bucket.html |
| Incomplete multipart uploads when emptying | Docs recommend also removing incomplete multipart uploads while emptying, with an AbortIncompleteMultipartUpload lifecycle rule (7 days suggested) | no | S3UG empty-bucket.html |
| CLI delete limits | aws s3 rb --force does not delete versioned objects, so deletion fails on a versioned bucket | no | S3UG delete-bucket.html |
| Object Lambda | S3 Object Lambda is retired for new customers; still listed on the S3 Welcome page | changed (see Retired services Rule 1) | S3UG Welcome.html |

### S3 storage classes

| Fact | Value | Changed? | Source |
|---|---|---|---|
| S3 Standard | Default class; AZs: 3 or more; min storage duration none; min billable object size none; no retrieval fee | no | S3UG storage-class-intro.html |
| S3 Intelligent-Tiering | AZs 3 or more; min duration none; min billable size none; no retrieval fees; monitoring and automation fee per object | no | S3UG storage-class-intro.html |
| Intelligent-Tiering Frequent Access tier | Default tier for new or transitioned objects | no | S3UG intelligent-tiering-overview.html |
| Intelligent-Tiering Infrequent Access tier | Automatic move after 30 consecutive days without access | no | S3UG intelligent-tiering-overview.html |
| Intelligent-Tiering Archive Instant Access tier | Automatic move after 90 consecutive days without access; millisecond access | no | S3UG intelligent-tiering-overview.html |
| Intelligent-Tiering Archive Access tier | Optional (opt-in); at least 90 days, configurable up to 730 days; Glacier Flexible Retrieval performance; standard restore 3 to 5 hours | no | S3UG intelligent-tiering-overview.html |
| Intelligent-Tiering Deep Archive Access tier | Optional (opt-in); at least 180 days, configurable up to 730 days; Deep Archive performance; standard restore within 12 hours | no | S3UG intelligent-tiering-overview.html |
| Intelligent-Tiering tier count | 3 automatic tiers (Frequent, Infrequent, Archive Instant Access) plus 2 optional archive tiers = 5 | no | S3UG storage-class-intro.html ; Welcome.html |
| Intelligent-Tiering small objects | Objects under 128 KB are not monitored, not auto-tiered, and always stay in Frequent Access | no | S3UG intelligent-tiering-overview.html |
| Intelligent-Tiering return to Frequent | An object in Infrequent Access or Archive Instant Access returns to Frequent Access when accessed (GET, PUT, COPY source, restore, CompleteMultipartUpload) | no | S3UG intelligent-tiering-overview.html |
| Intelligent-Tiering non-access actions | HeadObject, ListObjects, tagging calls do not move an object back to Frequent Access | no | S3UG intelligent-tiering-overview.html |
| Intelligent-Tiering restore for archive tiers | Objects in Archive Access / Deep Archive Access must be restored with RestoreObject before reading; 1,000 restore TPS per account per Region | no | S3UG intelligent-tiering-overview.html |
| Intelligent-Tiering free retrievals | Standard retrievals free for objects in Intelligent-Tiering; bulk retrievals free for Glacier Flexible Retrieval or Intelligent-Tiering | no | S3UG restoring-objects-retrieval-options.html |
| S3 Standard-IA | AZs 3 or more; min duration 30 days; min billable size 128 KB; per-GB retrieval fee; millisecond access | no | S3UG storage-class-intro.html |
| S3 One Zone-IA | AZ: 1; min duration 30 days; min billable size 128 KB; per-GB retrieval fee; not resilient to AZ loss; millisecond access | no | S3UG storage-class-intro.html |
| One Zone-IA minimum duration | 30 days, confirmed on the comparison table and on the Standard-IA/One Zone-IA note | no | S3UG storage-class-intro.html ; https://aws.amazon.com/s3/storage-classes/ |
| IA early-delete rule | Objects deleted, overwritten or transitioned before 30 days incur normal storage plus a pro-rated charge for the remainder | no | S3UG storage-class-intro.html |
| IA small object rule | An object under 128 KB is charged as 128 KB | no | S3UG storage-class-intro.html |
| One Zone-IA recommended use | Re-creatable data, replicas for CRR, or data residency in Local Zones | no | S3UG storage-class-intro.html |
| S3 Express One Zone | AZ: 1 (chosen by you); single-digit millisecond access; design durability 11 nines; availability 99.95 % | changed (class launched 2023) | S3UG storage-class-intro.html |
| Express One Zone min billable size | None | no | S3UG storage-class-intro.html |
| Express One Zone bucket type | Stored only in directory buckets; "up to 10x faster" data access than Standard | changed | S3UG storage-class-intro.html |
| Glacier Instant Retrieval | AZs 3 or more; min duration 90 days; min billable size 128 KB; millisecond retrieval; per-GB retrieval fee | no | S3UG storage-class-intro.html |
| Glacier Flexible Retrieval | AZs 3 or more; min duration 90 days; no min billable size but 40 KB overhead; per-GB retrieval fee; must restore before access | no | S3UG storage-class-intro.html |
| Glacier Deep Archive | AZs 3 or more; min duration 180 days; no min billable size but 40 KB overhead; per-GB retrieval fee; must restore before access | no | S3UG storage-class-intro.html |
| Archive per-object overhead | 40 KB per archived object: 32 KB at the archive rate and 8 KB at the S3 Standard rate (Flexible Retrieval and Deep Archive) | no | S3UG storage-class-intro.html ; lifecycle-transition-general-considerations.html |
| Retrieval fees by class | Yes: Standard-IA, One Zone-IA, Glacier IR, Glacier Flexible, Deep Archive (and Express: 0.0006 USD/GB). No: Standard, Intelligent-Tiering | no | S3UG storage-class-intro.html ; S3 price file |
| Glacier Flexible Expedited | Objects under 250 MB typically 1 to 5 minutes; for hundreds of objects at most | no | S3UG restoring-objects-retrieval-options.html |
| Glacier Flexible Standard | 3 to 5 hours (default tier when none is specified); with Batch Operations: minutes to 5 hours | no | S3UG restoring-objects-retrieval-options.html |
| Glacier Flexible Bulk | 5 to 12 hours | no | S3UG restoring-objects-retrieval-options.html |
| Deep Archive Standard | Within 12 hours (Batch Operations: 9 to 12 hours) | no | S3UG restoring-objects-retrieval-options.html |
| Deep Archive Bulk | Within 48 hours | no | S3UG restoring-objects-retrieval-options.html |
| Deep Archive Expedited | Not available | no | S3UG restoring-objects-retrieval-options.html |
| Provisioned capacity unit | Each unit guarantees at least 3 Expedited retrievals every 5 minutes and up to 300 MB/s; bought by the requester account; applies to Glacier Flexible Retrieval | no | S3UG restoring-objects-retrieval-options.html |
| Glacier restore request rate | 1,000 restore transactions per second; 1 to 2 PB per day per account; objects over 5 TB restore at up to 300 MB/s | no | S3UG restoring-objects-retrieval-options.html |
| Restored copy billing | While restored you pay for the archive rate plus a temporary S3 Standard copy; storage class stays Glacier | no | S3UG lifecycle-transition-general-considerations.html |
| One restore at a time | S3 processes one restore request at a time per object | no | S3UG lifecycle-transition-general-considerations.html |
| Original vault-based Glacier | The original vault-based Glacier service is retired for new customers; S3 Glacier storage-class objects cannot be accessed through the Glacier console or API | changed (see Retired services Rule 1) | S3UG storage-class-intro.html |
| Outposts storage class | S3 Outposts (OUTPOSTS) only in Outposts buckets; always SSE-S3, SSE-C optional, no SSE-KMS | no | S3UG storage-class-intro.html |
| Class selection guidance | Standard-IA for the only copy of non-re-creatable data; One Zone-IA for re-creatable data; Storage Class Analysis helps choose Standard vs Standard-IA | no | S3UG storage-class-intro.html |
| Storage class names (API values) | STANDARD, INTELLIGENT_TIERING, STANDARD_IA, ONEZONE_IA, EXPRESS_ONEZONE, GLACIER_IR, GLACIER, DEEP_ARCHIVE, REDUCED_REDUNDANCY, OUTPOSTS | no | S3UG storage-class-intro.html |

### S3 lifecycle

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Action types | Transition (move to another class) and Expiration (delete); plus NoncurrentVersionTransition, NoncurrentVersionExpiration, AbortIncompleteMultipartUpload, ExpiredObjectDeleteMarker | no | S3UG object-lifecycle-mgmt.html ; intro-lifecycle-rules.html |
| Rules per configuration | Up to 1,000 rules per bucket; limit is not adjustable; rule ID up to 255 characters | changed (was 1,000 for a long time; "not adjustable" stated now) | S3UG intro-lifecycle-rules.html |
| One configuration per bucket | Each bucket has one lifecycle configuration | no | S3UG intro-lifecycle-rules.html |
| Waterfall from Standard | Standard to Standard-IA, Intelligent-Tiering, One Zone-IA, Glacier IR, Glacier Flexible, Deep Archive | no | S3UG lifecycle-transition-general-considerations.html |
| Waterfall from Standard-IA | To Intelligent-Tiering, One Zone-IA, Glacier IR, Glacier Flexible, Deep Archive | no | S3UG lifecycle-transition-general-considerations.html |
| Waterfall from One Zone-IA | Only to Glacier Flexible Retrieval or Deep Archive | no | S3UG lifecycle-transition-general-considerations.html |
| Waterfall from Glacier IR | Only to Glacier Flexible Retrieval or Deep Archive | no | S3UG lifecycle-transition-general-considerations.html |
| Waterfall from Glacier Flexible | Only to Deep Archive | no | S3UG lifecycle-transition-general-considerations.html |
| Waterfall from Deep Archive | None; one-way. Moving out needs restore then copy | no | S3UG lifecycle-transition-general-considerations.html |
| Intelligent-Tiering as a source | Frequent/Infrequent Access tiers to One Zone-IA, Glacier IR, Flexible, Deep Archive; Archive Instant Access to Glacier IR/Flexible/Deep Archive | changed (IT transitions documented in detail) | S3UG lifecycle-transition-general-considerations.html |
| 128 KB default minimum for transitions | Since September 2024 objects under 128 KB are not transitioned to any class by default | changed Sep 2024 (before: could go to Glacier Flexible/Deep Archive) | S3UG lifecycle-transition-general-considerations.html |
| Older configurations | Configurations created before Sep 2024 keep the old behaviour until you create, edit or delete rules | changed Sep 2024 | S3UG lifecycle-transition-general-considerations.html |
| Override small-object default | Add ObjectSizeGreaterThan / ObjectSizeLessThan filter, or send x-amz-transition-default-minimum-object-size in PutBucketLifecycleConfiguration | changed Sep 2024 | S3UG lifecycle-transition-general-considerations.html |
| Why 128 KB | Each transition is a billed request; for small objects request cost can outweigh storage savings | no | S3UG lifecycle-transition-general-considerations.html |
| Early transition charge | Moving out of a class with a minimum duration early incurs the remaining duration charge | no | S3UG lifecycle-transition-general-considerations.html |
| Two-step minimum rule | Quote: "You can't create a single Lifecycle rule that transitions objects from one storage class to another before the minimum storage duration period has passed." Example: Glacier IR has a 90-day minimum, so you can't transition to Glacier IR after 4 days and to Deep Archive after 20 days; "the S3 Glacier Deep Archive transition must occur after at least 94 days" (4 days in Standard + the 90-day minimum). Two separate rules work but you pay the minimum-duration charges | no | S3UG lifecycle-transition-general-considerations.html |
| Expiration on unversioned bucket | Object queued for asynchronous removal and permanently deleted | no | S3UG lifecycle-expire-general-considerations.html |
| Expiration on versioning-enabled bucket | Adds a delete marker as the current version; the old current version becomes noncurrent | no | S3UG lifecycle-expire-general-considerations.html |
| Expiration on versioning-suspended bucket | Creates a delete marker with null version ID (replaces a null-version object) | no | S3UG lifecycle-expire-general-considerations.html |
| Expiration scope | Expiration applies only to the current version | no | S3UG lifecycle-expire-general-considerations.html |
| Noncurrent version expiration | NoncurrentVersionExpiration permanently deletes noncurrent versions; cannot be recovered | no | S3UG intro-lifecycle-rules.html |
| NoncurrentDays | Days since the successor version was created; rounds up to next midnight UTC | no | S3UG intro-lifecycle-rules.html |
| NewerNoncurrentVersions | Number of newer noncurrent versions to retain, 1 to 100; both NoncurrentDays and this count must be exceeded; requires a Filter element or InvalidRequest | no | S3UG intro-lifecycle-rules.html |
| Expired object delete marker | A delete marker with zero noncurrent versions; Expiration action removes it | no | S3UG lifecycle-expire-general-considerations.html |
| ExpiredObjectDeleteMarker element | Cannot be used in a rule whose filter uses object tags | no | S3UG intro-lifecycle-rules.html |
| AbortIncompleteMultipartUpload | Sets max days a multipart upload may stay in progress, then aborts it; object expiration rules do not remove incomplete uploads; not allowed with a tag filter | no | S3UG intro-lifecycle-rules.html |
| Suggested abort window | 7 days is a good starting point | no | S3UG empty-bucket.html |
| Filters | Key prefix, object tags (logical AND with And element), object size (ObjectSizeGreaterThan / LessThan, bytes, exclusive), or combinations; one prefix per filter; empty filter = all objects | no | S3UG intro-lifecycle-rules.html |
| Different prefixes | Use separate rules per prefix | no | S3UG intro-lifecycle-rules.html |
| Day counting | Days from object creation/last modified; time = creation + N days rounded up to the next day at 00:00 UTC | no | S3UG intro-lifecycle-rules.html |
| Date-based rules | ISO 8601, midnight UTC, keep applying after the date while enabled; not creatable in console | no | S3UG intro-lifecycle-rules.html |
| Asynchronous | Lifecycle runs asynchronously; there can be a delay between eligibility and the action | no | S3UG lifecycle-expire-general-considerations.html |
| Billing at eligibility | Billing changes apply as soon as an object becomes eligible (you are not charged for expired objects) except transitions to Intelligent-Tiering, billed after the physical transition | no | S3UG object-lifecycle-mgmt.html |
| Rule propagation | Rule policy updates can take up to 15 minutes to propagate | changed (documented in newer pages) | S3UG lifecycle-expire-general-considerations.html |
| Tag-based rules | Evaluated daily; tags re-checked at execution; removing a tag does not guarantee cancellation | changed (newer behaviour note) | S3UG lifecycle-transition-general-considerations.html |
| Applies to existing objects | A new configuration applies to existing and future objects | no | S3UG object-lifecycle-mgmt.html |
| Lifecycle vs bucket policy | A bucket policy cannot prevent lifecycle deletions or transitions | no | S3UG object-lifecycle-mgmt.html |
| One action per day | An object is eligible for only one lifecycle action per day; least costly action applies; deletion beats transition, transition beats delete-marker creation | no | S3UG lifecycle-expire-general-considerations.html |
| Lifecycle and Object Lock | No action on noncurrent versions with Object Lock applied | no | S3UG lifecycle-expire-general-considerations.html |
| Lifecycle and replication | No action on current or noncurrent versions with Pending or Failed replication status | no | S3UG lifecycle-expire-general-considerations.html |
| Lifecycle and MFA delete | MFA delete cannot be used with lifecycle configurations | no | S3UG MultiFactorAuthenticationDelete.html |
| Transition retrieval charge | No data retrieval charges for lifecycle transitions; per-request ingestion charges apply | no | S3UG object-lifecycle-mgmt.html |
| Transition to Glacier Flexible/Deep Archive | Asynchronous; billed at destination rate from the date the rule is satisfied | no | S3UG lifecycle-transition-general-considerations.html |
| Expiring in a minimum-duration class | Expiring early charges the remaining minimum: 30 days (IA classes), 90 (Glacier Flexible), 180 (Deep Archive) | no | S3UG lifecycle-expire-general-considerations.html |
| Lifecycle event notifications | Lifecycle expiration and transition events exist as S3 Event Notifications event types | changed (newer feature) | S3UG EventNotifications.html |

### Versioning, Object Lock and replication

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Versioning default | Disabled (unversioned) by default | no | S3UG Versioning.html |
| Versioning states | Unversioned, versioning-enabled, versioning-suspended | no | S3UG Versioning.html |
| Cannot unversion | After enabling, a bucket can never return to unversioned; it can only be suspended | no | S3UG Versioning.html |
| Existing objects | Objects before versioning have version ID null; unchanged until modified | no | S3UG Versioning.html |
| Who can enable versioning | Bucket owner, root account and authorized users | no | S3UG MultiFactorAuthenticationDelete.html |
| Versioning cost | Each version is a full object (not a diff); normal rates apply to every version | no | S3UG Versioning.html |
| Simple DELETE with versioning on | S3 adds a delete marker as the current version; nothing is deleted | no | S3UG DeleteMarker.html |
| Delete marker properties | No data, no ACL; billed by key-name size (1 to 4 bytes per character); stored in S3 Standard | no | S3UG DeleteMarker.html |
| GET after simple delete | GET without versionId returns 404 Not Found with x-amz-delete-marker: true | no | S3UG DeleteMarker.html |
| GET delete marker by versionId | Returns 405 Method Not Allowed with x-amz-delete-marker: true and Last-Modified | no | S3UG DeleteMarker.html |
| LIST after delete | ListObjects/ListObjectsV2 do not return objects whose current version is a delete marker; ListObjectVersions shows them | no | S3UG DeleteMarker.html |
| Restore a deleted object | Delete the delete marker (DELETE with its version ID) or copy a noncurrent version over | no | S3UG DeleteMarker.html ; intro-lifecycle-rules.html |
| Permanent delete | DELETE with a version ID permanently deletes that version | no | S3UG Versioning.html |
| Suspended behaviour | Existing versions stay; new writes get null version ID; expiration creates a null delete marker | no | S3UG Versioning.html ; intro-lifecycle-rules.html |
| Unversioned lifecycle gotcha | If an expiration rule exists on an unversioned bucket, add a noncurrent expiration rule after enabling versioning to keep permanent deletes | no | S3UG Versioning.html |
| MFA delete | Needs MFA to change versioning state or permanently delete a version; token = serial number + space + 6-digit code | no | S3UG MultiFactorAuthenticationDelete.html |
| MFA delete who and how | Only the bucket owner (root account) can enable it; not in the console; use CLI or API | no | S3UG MultiFactorAuthenticationDelete.html |
| Object Lock model | Write-once-read-many (WORM); works only in versioning-enabled buckets; protects individual object versions | no | S3UG object-lock.html |
| Object Lock regulation | Assessed by Cohasset Associates for SEC 17a-4, CFTC and FINRA | no | S3UG object-lock.html |
| Governance mode | Cannot overwrite/delete or alter lock unless you hold s3:BypassGovernanceRetention and send x-amz-bypass-governance-retention:true | no | S3UG object-lock.html |
| Governance mode console | Console includes the bypass header by default when you have the permission | no | S3UG object-lock.html |
| Compliance mode | No user, including root, can overwrite or delete; mode cannot change and period cannot be shortened | no | S3UG object-lock.html |
| Deleting under compliance | Only deleting the AWS account removes it before the retain-until date | no | S3UG object-lock.html |
| Retention period | Fixed retain-until-date per object version, or bucket default retention in days or years | no | S3UG object-lock.html |
| Variable retention | Event hold plus duration; S3 sets the retain-until-date when you release the hold | changed (new feature) | S3UG object-lock.html |
| Extending retention | Can extend (later date) with s3:PutObjectRetention; cannot shorten in compliance mode | no | S3UG object-lock.html |
| Legal hold | Same protection as retention but no expiry; independent of retention; needs s3:PutObjectLegalHold; any authorized user can add or remove | no | S3UG object-lock.html |
| Lock does not stop new versions | A lock protects only the specified version; new versions and delete markers can still be added | no | S3UG object-lock.html |
| Delete of locked version | Permanent DELETE with version ID returns 403; simple DELETE returns 200 and adds a delete marker | no | S3UG object-lock.html |
| Object Lock permissions | s3:BypassGovernanceRetention, Get/PutBucketObjectLockConfiguration, Get/PutObjectLegalHold, Get/PutObjectRetention | no | S3UG object-lock.html |
| Retention limit condition key | s3:object-lock-remaining-retention-days restricts allowed retention periods in a bucket policy | no | S3UG object-lock.html |
| Replication types | Live replication (new and updated objects) and on-demand replication (S3 Batch Replication) | changed (on-demand framing) | S3UG replication.html |
| CRR / SRR | CRR copies between buckets in different Regions; SRR within the same Region; accounts may differ | no | S3UG replication.html |
| Replication is asynchronous | Automatic, asynchronous copying; multiple destination buckets supported | no | S3UG replication.html |
| Versioning required | Quote: "Both source and destination buckets must have versioning enabled." Disabling versioning on the source is refused until replication is removed; disabling it on the destination makes replication fail (status FAILED) | no | S3UG replication-requirements.html |
| Replication permissions | S3 must have permission to replicate on your behalf (IAM role); if the source has Object Lock the destination must too, and the role needs s3:GetObjectRetention and s3:GetObjectLegalHold (s3:Get* satisfies it) | changed (Object Lock permissions are newer) | S3UG replication-requirements.html |
| Cross-account replication | Destination bucket owner must grant the source owner permission with a bucket policy; destination cannot be Requester Pays | no | S3UG replication-requirements.html |
| Existing objects | Live replication does not replicate objects that existed before setup; use S3 Batch Replication | no | S3UG replication.html |
| Batch Replication also covers | Previously failed objects, already replicated objects to new destinations, and replicas of replicas | no | S3UG replication.html |
| Replicas of replicas | Objects that are replicas from another rule are not replicated onward (no chaining) except via Batch Replication | no | S3UG replication-what-is-isnot-replicated.html |
| Delete markers | With the current (Filter) rule schema, delete markers are NOT replicated by default; optional delete marker replication on non-tag-based rules; V1 (no Filter) replicates user-initiated markers | no | S3UG replication-what-is-isnot-replicated.html |
| Version-specific deletes | A DELETE with version ID is not replicated, to protect against malicious deletes | no | S3UG replication-what-is-isnot-replicated.html |
| Lifecycle actions | Not replicated; use the same lifecycle configuration on both buckets | no | S3UG replication-what-is-isnot-replicated.html |
| Archived objects | Glacier Flexible, Deep Archive and Intelligent-Tiering archive tiers cannot be replicated until restored and copied | no | S3UG replication-what-is-isnot-replicated.html |
| Bucket-level subresources | Changes to lifecycle or notification configuration are not replicated | no | S3UG replication-what-is-isnot-replicated.html |
| What is replicated | New objects after configuration, metadata, tags, ACL updates, Object Lock retention info; SSE-S3, SSE-KMS and SSE-C objects by default | changed (annotations are newer) | S3UG replication-what-is-isnot-replicated.html |
| Replica storage class | Can replicate into a different class (e.g. Glacier) and change replica ownership (owner override) | no | S3UG replication.html |
| Replication Time Control (RTC) | Replicates new objects within 15 minutes, SLA-backed (the page gives two percentages; the course states none) | no | S3UG replication.html |
| RTC scope | Does not apply to Batch Replication | no | S3UG replication.html |
| Without RTC | SRR/CRR typically 24 to 48 hours, not SLA-backed (per workload table) | no | S3UG replication.html |
| Two-way replication | Bi-directional rules with replica modification sync replicate metadata changes (ACLs, tags, Object Lock) back; used with Multi-Region Access Point failover | no | S3UG replication.html |

### S3 security

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Block Public Access settings | Four: BlockPublicAcls, IgnorePublicAcls, BlockPublicPolicy, RestrictPublicBuckets | no | S3UG access-control-block-public-access.html |
| BPA levels | Access point, bucket, account, and organization (AWS Organizations policy: all four together, all or none) | changed (organization level and access-point level are newer) | S3UG access-control-block-public-access.html |
| BPA precedence | Most restrictive combination across levels applies | no | S3UG access-control-block-public-access.html |
| BlockPublicAcls | PutBucketAcl / PutObjectAcl / PutObject with a public ACL fail; existing ACLs unchanged | no | S3UG access-control-block-public-access.html |
| IgnorePublicAcls | S3 ignores all public ACLs but still accepts PutObject with public ACL | no | S3UG access-control-block-public-access.html |
| BlockPublicPolicy | Rejects PutBucketPolicy (and access point policy) that allows public access | no | S3UG access-control-block-public-access.html |
| RestrictPublicBuckets | A bucket with a public policy is limited to AWS service principals and authorized users in the owner account | no | S3UG access-control-block-public-access.html |
| BPA defaults for new buckets | All four settings on at bucket level for new buckets | changed 2023-04 (facts.md date; page: default on) | S3UG Welcome.html ; facts.md |
| BPA existing policy | Does not alter existing policies/ACLs; turning BPA off makes public ones effective again | no | S3UG access-control-block-public-access.html |
| BPA access point | Access point BPA settings can only be set when creating the access point | no | S3UG access-control-block-public-access.html |
| Object Ownership default | Bucket owner enforced: ACLs disabled, bucket owner owns all objects | changed 2023-04 | S3UG Welcome.html |
| ACL guidance | AWS recommends keeping ACLs disabled and using bucket/access point/IAM policies | no | S3UG Welcome.html |
| Default encryption | All new object uploads encrypted with SSE-S3 (AES-256) automatically, at no cost, from 2023-01-05; cannot be turned off | changed 2023-01-05 | S3UG bucket-encryption.html |
| Default encryption for existing buckets | Buckets without default encryption were switched to SSE-S3; buckets already on SSE-S3 or SSE-KMS unchanged | changed 2023-01 | S3UG bucket-encryption.html |
| Existing unencrypted objects | Not re-encrypted automatically; use Batch Operations Copy or CopyObject | no | S3UG bucket-encryption.html |
| Encryption options | SSE-S3, SSE-KMS, DSSE-KMS (dual-layer), SSE-C | changed (DSSE-KMS is newer) | S3UG bucket-encryption.html |
| SSE-KMS key when none given | Uses the AWS managed key aws/s3 | no | S3UG bucket-encryption.html |
| SSE-KMS cross-account | Needs a customer managed key (aws/s3 cannot be shared); use full key ARN not alias | no | S3UG bucket-encryption.html |
| SSE-KMS key types | Symmetric KMS keys only; same Region as the bucket | no | S3UG upload-objects.html |
| S3 Bucket Keys | Bucket-level key reduces KMS request costs by up to 99 percent | no | S3UG bucket-key.html |
| Bucket Key scope | Applies to new objects only (CopyObject to apply to existing); shared only for objects with the same KMS key; encryption context becomes bucket ARN | no | S3UG bucket-key.html |
| Bucket Key not supported | Not supported with DSSE-KMS | changed (DSSE-KMS newer) | S3UG bucket-key.html |
| Server access log bucket | Must use SSE-S3, not SSE-KMS | no | S3UG bucket-encryption.html |
| SSE-C rules | Keys supplied on every request; S3 never stores the key; HTTPS required; not supported in the console | no | S3UG ServerSideEncryptionCustomerKeys.html |
| SSE-C default change | Starting April 2026 SSE-C is disabled by default for all new general purpose buckets and for existing buckets in accounts with no SSE-C objects; enable with BlockedEncryptionTypes = NONE via PutBucketEncryption; blocked writes return 403 AccessDenied | changed April 2026 | S3UG ServerSideEncryptionCustomerKeys.html |
| bucket policy: HTTPS only | Deny with Condition Bool aws:SecureTransport = "false" | no | S3UG example-bucket-policies.html |
| bucket policy: VPC endpoint | aws:SourceVpce (and aws:SourceVpc) with a fixed value keeps a policy non-public and restricts access to a VPC endpoint | no | S3UG access-control-block-public-access.html |
| Non-public policy conditions | aws:PrincipalOrgID, aws:SourceIp CIDR, aws:SourceArn, aws:SourceVpc, aws:SourceVpce, aws:SourceOwner, aws:SourceAccount, s3:DataAccessPointArn | no | S3UG access-control-block-public-access.html |
| Presigned URL expiry (SigV4) | Console: 1 minute to 12 hours; CLI/SDK: up to 7 days with an IAM user's long-term credentials | no | S3UG using-presigned-url.html |
| Presigned URL with temporary credentials | Expires when the credential expires (IAM role session, STS, EC2 instance profile about 6 hours) even if a longer time was requested | no | S3UG using-presigned-url.html |
| Presigned URL permissions | Carries the permissions of the principal that signed it; works for GET and PUT; can be reused until expiry; checked at request time | no | S3UG using-presigned-url.html |
| Presigned URL age condition | s3:signatureAge in a bucket policy can deny signatures older than a set time | no | S3UG using-presigned-url.html |
| Access points | Named network endpoints with their own policy (up to 20 KB); thousands per Region per account; can restrict to a VPC; attach to general purpose or directory buckets or FSx for OpenZFS volumes | changed (directory buckets and FSx OpenZFS targets are newer) | S3UG Welcome.html ; access-grants.html |
| CloudFront OAC | Origin Access Control is the recommended way to restrict an S3 origin; supports all Regions including opt-in Regions, SSE-KMS, and PUT/DELETE; policy principal cloudfront.amazonaws.com with AWS:SourceArn of the distribution | changed (OAC is newer than 2022 OAI guidance) | CF private-content-restricting-access-to-s3.html |
| CloudFront OAI | Legacy; no SSE-KMS, no all-Regions support, no PUT/POST/DELETE workarounds | changed (legacy) | CF private-content-restricting-access-to-s3.html |
| OAC and website endpoints | An S3 website endpoint origin cannot use OAC or OAI (use a custom origin) | no | CF private-content-restricting-access-to-s3.html |
| OAC and Object Ownership | OAC requires bucket owner enforced (the default) unless bucket owner preferred is chosen to use ACLs | no | CF private-content-restricting-access-to-s3.html |
| S3 Access Grants | Maps IAM principals or corporate-directory users/groups (through IAM Identity Center trusted identity propagation) to S3 prefixes, buckets or objects with read/write/read-write grants | changed (feature newer than 2022) | S3UG access-grants.html |
| IAM and bucket policy size | Bucket policy up to 20 KB; IAM policy size about 5 KB per the Access Grants page | no | S3UG access-grants.html |
| ALB access log bucket policy: principal | Recommended policy uses service principal logdelivery.elasticloadbalancing.amazonaws.com | changed (service principal replaced the per-Region account ID for Regions available after August 2022) | ALB enable-access-logging.html |
| ALB legacy policy: us-east-1 | Regions available before August 2022 can still use the legacy policy with the Elastic Load Balancing account ID; US East (N. Virginia) is 127311923021 | changed (legacy, "recommend that you replace it") | ALB enable-access-logging.html |
| ALB log policy action | s3:PutObject | no | ALB enable-access-logging.html |
| ALB log policy resource | arn:aws:s3:::bucket/prefix/AWSLogs/account-id/* (without a prefix: bucket/AWSLogs/account-id/*); always include the account ID, no wildcard in it | no | ALB enable-access-logging.html |
| ALB log bucket Region | Bucket must be in the same Region as the load balancer; may be owned by a different account | no | ALB enable-access-logging.html |
| ALB log bucket encryption | Only SSE-S3 (Amazon S3-managed keys) is supported; SSE-KMS causes access denied | no | ALB enable-access-logging.html |
| ALB log delivery interval | A log file per load balancer node every 5 minutes; delivery is eventually consistent and best effort | no | ALB load-balancer-access-logs.html |
| ALB log format | Compressed .log.gz files under AWSLogs/account-id/elasticloadbalancing/region/yyyy/mm/dd/ | no | ALB load-balancer-access-logs.html |
| ALB log cost | Pay only S3 storage; no charge for the delivery bandwidth | no | ALB load-balancer-access-logs.html |
| ALB log policy hardening | aws:SourceArn (loadbalancer ARN) and aws:SourceOrgId conditions recommended; Outposts uses logdelivery.elb.amazonaws.com with bucket-owner-full-control | changed (newer recommendations) | ALB enable-access-logging.html |
| ALB log extras | Newer ALB logging to CloudWatch Logs, Firehose or S3 is available besides legacy access logs | changed (new) | ALB load-balancer-access-logs.html |

### S3 performance and transfer

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Parallelization | More prefixes and parallel requests raise throughput linearly | no | S3UG optimizing-performance.html |
| Multipart benefits | Parts upload independently, in any order and in parallel | no | S3UG upload-objects.html |
| Transfer Acceleration | Bucket-level feature that uses CloudFront edge locations; data routed to S3 over an optimized network path | no | S3UG transfer-acceleration.html |
| Transfer Acceleration requirements | Virtual-hosted-style requests only; bucket name DNS-compliant without periods; enabled on the bucket | no | S3UG transfer-acceleration.html |
| Transfer Acceleration endpoint | bucket.s3-accelerate.amazonaws.com (dual-stack: s3-accelerate.dualstack.amazonaws.com) | no | S3UG transfer-acceleration.html |
| Transfer Acceleration activation | Can take up to 20 minutes after enabling before speed improves | no | S3UG transfer-acceleration.html |
| Transfer Acceleration cost | Extra data transfer charges might apply | no | S3UG transfer-acceleration.html |
| Transfer Acceleration owner | Only the bucket owner (or delegated) can set it; permissions s3:PutAccelerateConfiguration / GetAccelerateConfiguration | no | S3UG transfer-acceleration.html |
| Transfer Acceleration use | Customers upload from around the world to a central bucket or move GBs to TBs across continents | no | S3UG transfer-acceleration.html |
| S3 Select status | S3 Select is retired for new customers: "no longer available to new customers. Existing customers can continue to use the feature as usual." | changed (closed to new customers; see Retired services Rule 1) | S3UG selecting-content-from-objects.html |
| S3 Select limits | Retired for new customers; existing use: one object per request; files up to 5 TB; SQL expression up to 256 KB; record up to 1 MB; not for Glacier Flexible/Deep Archive/RRS/IT archive tiers | no | S3UG selecting-content-from-objects.html |
| S3 Batch Operations | One operation on billions of objects with a manifest (S3 Inventory report or CSV) and completion report | no | S3UG batch-ops.html |
| Batch Operations operations | Copy, tag, ACL, Object Lock, restore from Glacier, invoke Lambda, update encryption, Batch Replication | changed (update encryption, Batch Replication are newer) | S3UG batch-ops.html |
| Batch Operations scale | 4 billion objects per job by default; up to 20 billion for some operations; 6 active jobs per account | changed (limits stated now) | S3UG batch-ops.html |
| Batch Operations cost | Billed for creating jobs, including cancelled ones | no | S3UG batch-ops.html |
| Event notification destinations | SNS topics, SQS queues, Lambda functions, Amazon EventBridge | no | S3UG EventNotifications.html |
| Event delivery | At least once; typically seconds, sometimes a minute or longer | no | S3UG EventNotifications.html |
| SQS FIFO | FIFO queues are not supported as a destination; use EventBridge | no | S3UG EventNotifications.html |
| Event types | Object created, removed, restore, RRS lost, replication, lifecycle expiration and transition, Intelligent-Tiering archival, tagging, ACL put, retention | changed (annotation/retention events newer) | S3UG EventNotifications.html |
| Loop warning | A notification that writes to the same bucket can cause an execution loop | no | S3UG EventNotifications.html |
| Storage Lens | 60+ usage and activity metrics, dashboards per org/account/Region/bucket/prefix | no | S3UG Welcome.html |
| Storage Class Analysis | Analyzes access patterns to recommend moving data | no | S3UG Welcome.html |
| S3 Inventory | Reports of objects and metadata (replication, encryption status) | no | S3UG Welcome.html |

### EBS

| Fact | Value | Changed? | Source |
|---|---|---|---|
| EBS scope | A volume lives in one Availability Zone and attaches to instances in that AZ | no | EBS ebs-volumes-multi.html (same-AZ requirement for Multi-Attach); general rule not re-read |
| gp3 size | 1 GiB to 64 TiB | changed 2025-09 (was 16 TiB) | EBS ebs-volume-types.html ; WN 2025/09/amazon-ebs-size-provisioned-performance-gp3-volumes/ |
| gp3 baseline | 3,000 IOPS and 125 MiB/s included in the storage price at any size | no | EBS general-purpose.html |
| gp3 max IOPS | 80,000 IOPS (was 16,000) | changed 2025-09 | EBS general-purpose.html ; WN 2025/09 page |
| gp3 max throughput | 2,000 MiB/s (was 1,000) | changed 2025-09 | EBS general-purpose.html ; WN 2025/09 page |
| gp3 IOPS ratio | Provision up to 500 IOPS per GiB; max IOPS needs 160 GiB or larger | no | EBS general-purpose.html |
| gp3 throughput ratio | Up to 0.25 MiB/s per provisioned IOPS; max throughput at 8,000 IOPS or more and 16 GiB or larger | no | EBS general-purpose.html |
| gp3 vs gp2 cost | gp3 is 20 percent lower price per GiB than gp2 | no | EBS general-purpose.html |
| gp3 burst | None; sustains full provisioned IOPS and throughput indefinitely | no | EBS general-purpose.html |
| gp3 durability | 99.8 to 99.9 % (AFR at most 0.2 %); provisioned performance delivered 99 % of the time | no | EBS general-purpose.html |
| gp3 on Outposts | Up to 16 TiB, 16,000 IOPS, 1,000 MiB/s | no | EBS general-purpose.html |
| gp3 console default | gp3 is the default volume type selection in the console | changed (default moved from gp2) | EBS general-purpose.html |
| gp2 baseline | 3 IOPS per GiB, minimum 100 IOPS, maximum 16,000 IOPS (reached at 5,334 GiB) | no | EBS general-purpose.html |
| gp2 size | 1 GiB to 16 TiB | no | EBS general-purpose.html |
| gp2 burst | Volumes under 1 TiB can burst to 3,000 IOPS using I/O credits | no | EBS general-purpose.html |
| gp2 I/O credit bucket | 5.4 million credits at start and maximum; earned at 3 credits per GiB per second below baseline; 5.4 million sustains 3,000 IOPS for at least 30 minutes | no | EBS general-purpose.html |
| gp2 throughput | 128 to 250 MiB/s depending on size (170 GiB and smaller: 128; 334 GiB and larger: 250) | no | EBS general-purpose.html |
| gp2 33.33 GiB | Volumes 33.33 GiB and smaller get the 100 IOPS minimum | no | EBS general-purpose.html |
| BurstBalance | CloudWatch metric showing percent of gp2 I/O credits remaining | no | EBS general-purpose.html |
| io2 Block Express size | 4 GiB to 64 TiB | no | EBS ebs-volume-types.html |
| io2 Block Express IOPS | Up to 256,000 IOPS (Nitro instances), ratio 1,000 IOPS per GiB, max at 256 GiB or larger; non-Nitro instances reach at most 32,000 | no | EBS provisioned-iops.html |
| io2 Block Express throughput | Up to 4,000 MiB/s; 0.256 MiB/s per provisioned IOPS; maximum at 16,000 IOPS or more | no | EBS provisioned-iops.html |
| io2 durability | 99.999 % (AFR at most 0.001 %), one failure per 100,000 volumes per year | no | EBS provisioned-iops.html |
| io2 latency | Average under 500 microseconds for 16 KiB I/O; sub-millisecond | no | EBS provisioned-iops.html |
| io2 Block Express universal | As of 2025-04-30 all new and existing io2 volumes are io2 Block Express | changed 2025-04-30 | EBS provisioned-iops.html |
| io2 use case | More than 80,000 IOPS or 2,000 MiB/s, or sub-millisecond latency (Oracle, SAP HANA, SQL Server) | no | EBS ebs-volume-types.html |
| io1 | 4 GiB to 16 TiB; 100 to 64,000 IOPS; ratio 50 IOPS per GiB; up to 1,000 MiB/s; 99.8 to 99.9 % durability | no | EBS provisioned-iops.html |
| io1 max IOPS size | Maximum 64,000 IOPS needs 1,280 GiB; 64,000 only on Nitro (32,000 otherwise) | no | EBS provisioned-iops.html |
| io1/io2 delivered performance | Provisioned IOPS delivered 99.9 % of the time | no | EBS provisioned-iops.html |
| st1 (Throughput Optimized HDD) | 125 GiB to 16 TiB; max 500 IOPS (1 MiB) and 500 MiB/s; not bootable; no Multi-Attach | no | EBS ebs-volume-types.html |
| sc1 (Cold HDD) | 125 GiB to 16 TiB; max 250 IOPS and 250 MiB/s; not bootable; no Multi-Attach; lowest cost | no | EBS ebs-volume-types.html |
| st1 / sc1 use cases | st1: big data, data warehouses, log processing; sc1: infrequently accessed, lowest cost | no | EBS ebs-volume-types.html |
| Magnetic (standard) | Previous generation; 1 GiB to 1 TiB; 40 to 200 IOPS; 40 to 90 MiB/s; bootable | no | EBS ebs-volume-types.html |
| Bootable types | gp2, gp3, io1, io2, magnetic; not st1 or sc1 | no | EBS ebs-volume-types.html |
| Root volume type change | A root volume of SSD or magnetic type cannot be modified to st1 or sc1 | no | EBS ebs-modify-volume.html |
| Multi-Attach types | Only io1 and io2 (Provisioned IOPS SSD); gp2/gp3/st1/sc1 not supported | no | EBS ebs-volumes-multi.html |
| Multi-Attach scope | Same Availability Zone only; up to 16 Nitro instances | no | EBS ebs-volumes-multi.html |
| Multi-Attach file system | XFS/ext4 are not cluster-aware; use a clustered file system; app must order writes | no | EBS ebs-volumes-multi.html |
| Multi-Attach OS | Linux supports io1 and io2; Windows supports io2 only | no | EBS ebs-volumes-multi.html |
| Multi-Attach limits | Cannot be a boot volume; cannot be enabled at launch via console/RunInstances; no extra charge | no | EBS ebs-volumes-multi.html |
| Multi-Attach change | Enable/disable on existing volume allowed when detached; io1 to io2 conversion allowed | changed (modification support is newer) | EBS ebs-volumes-multi.html |
| NVMe reservations | I/O fencing supported on io1/io2 | changed (new) | EBS ebs-volumes-multi.html |
| Snapshots are incremental | Only blocks changed since the last snapshot are saved | no | EBS ebs-snapshots.html |
| Snapshot storage | Stored in S3 buckets you cannot access directly; replicated across all AZs in the Region | no | EBS ebs-snapshots.html |
| Deleting a snapshot | May not reduce cost because data referenced by other snapshots is kept | no | EBS ebs-snapshots.html |
| Snapshot is not automatic | AWS does not back up EBS volumes automatically; use snapshots, Data Lifecycle Manager or AWS Backup | no | EBS ebs-snapshots.html |
| Fast Snapshot Restore | Volumes created from the snapshot are fully initialized at creation; enabled per snapshot per AZ | no | EBS ebs-fast-snapshot-restore.html |
| FSR limits | Snapshots of 16 TiB or less; up to 5 snapshots per Region; not on Outposts/Local Zones/Wavelength | no | EBS ebs-fast-snapshot-restore.html |
| FSR billing | Per minute per snapshot per AZ, minimum one hour; example 0.75 USD per hour | no | EBS ebs-fast-snapshot-restore.html |
| FSR on copy | A copy of an FSR-enabled snapshot is not automatically FSR-enabled | no | EBS ebs-fast-snapshot-restore.html |
| Snapshot Archive tier | Up to 75 percent lower storage cost for snapshots kept 90 days or longer; stored as full snapshots | no | EBS snapshot-archive.html |
| Archive minimum | Minimum archive period 90 days; deleting or restoring early bills remaining days | no | EBS snapshot-archive-considerations.html |
| Archive restore time | Up to 72 hours to restore to the standard tier | no | EBS snapshot-archive-considerations.html |
| Archive restrictions | Cannot create a volume, share or copy an archived snapshot; must restore first; FSR disabled on archive | no | EBS snapshot-archive-considerations.html |
| Archive quotas | 25 archived snapshots per volume; 25 concurrent archives; 5 concurrent restores per account | no | EBS snapshot-archive.html |
| Archive best use | Monthly, quarterly or yearly snapshots; daily incrementals can cost more than standard | no | EBS snapshot-archive-considerations.html |
| Recycle Bin | Recovers deleted EBS volumes, snapshots and EBS-backed AMIs for a retention period you set | changed (volume support is newer) | EBS recycle-bin.html |
| Recycle Bin quotas | 250 retention rules per Region; 50 tag key/value pairs per rule | no | EBS recycle-bin.html |
| Recycle Bin cost | No extra charge for rules; resources in the bin billed at the normal rate (archived snapshots at archive rate) | no | EBS recycle-bin.html |
| EBS encryption | Uses AWS KMS keys; encrypts data at rest and in transit between instance and volume; all instance types support it | no | EBS ebs-encryption.html |
| Encryption by default | Region-specific account setting; cannot disable per volume/snapshot in that Region once on; no effect on existing resources; default key aws/ebs | no | EBS encryption-by-default.html |
| Encrypt an unencrypted volume | Cannot encrypt in place; snapshot the volume, then copy/restore the snapshot with encryption | no | EBS ebs-encryption.html |
| Remove encryption | Encrypted volume or snapshot can never be made unencrypted; restores and copies stay encrypted | no | EBS ebs-encryption.html |
| Snapshot sharing | Public snapshots of encrypted volumes are not supported; can share with specific accounts | no | EBS ebs-encryption.html |
| Change key | KMS key of an existing volume/snapshot cannot change; choose another key on snapshot copy (full copy, extra storage) | no | EBS encryption-by-default.html |
| Elastic Volumes | Change size, type, IOPS, throughput of an in-use volume without detaching or stopping | no | EBS ebs-modify-volume.html |
| Elastic Volumes frequency | Up to four modifications in a rolling 24 hours, and each must reach completed before the next | changed (older docs said wait 6 hours) | EBS ebs-modify-volume.html |
| Elastic Volumes limits | Size can only increase; cannot cancel; no charge for the modify itself | no | EBS ebs-modify-volume.html |
| Elastic Volumes time | Best effort; a 1 TiB volume can take up to six hours | no | EBS ebs-modify-volume.html |
| gp2 to gp3 migration | Modify in place; unspecified performance becomes the higher of equivalent gp2 or gp3 baseline | no | EBS ebs-modify-volume.html |
| Data Lifecycle Manager | Automates creation, retention, deletion of EBS snapshots and EBS-backed AMIs; no additional cost; cross-Region/account copy for DR | no | EBS snapshot-lifecycle.html |
| DLM quotas | 100 custom lifecycle policies per Region; 1 default policy for snapshots and 1 for AMIs per Region; 45 tags | changed (default policies are newer) | EBS snapshot-lifecycle.html |
| DLM limits | Cannot manage snapshots/AMIs created by other means; not instance-store AMIs | no | EBS snapshot-lifecycle.html |

### EFS

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Protocol | NFSv4.1 and NFSv4.0 (no NFSv2/v3) | no | EFS whatisefs.html ; limits.html |
| OS support | Linux; Microsoft Windows-based EC2 instances are not supported | no | EFS whatisefs.html |
| Serverless elastic | Grows and shrinks automatically to petabytes; no capacity provisioning | no | EFS whatisefs.html |
| Compute that can mount | EC2, ECS, EKS, Lambda, Fargate; on-premises over Direct Connect or VPN | no | EFS whatisefs.html ; limits.html |
| Regional file system | Data across multiple AZs (3 or more); durability 11 nines; availability 99.99 %; recommended | no | EFS features.html |
| One Zone file system | One AZ; durability 11 nines; not resilient to AZ loss; auto-backup with AWS Backup (the page gives two availability figures; the course states none) | no | EFS features.html |
| Mount targets | One mount target per AZ per file system; 1,400 mount targets per VPC; 5 security groups per mount target; 1 VPC per file system | no | EFS limits.html |
| Mount target security | Security groups are applied at mount targets | no | EFS efs-access-points.html |
| Storage class Standard | SSD; sub-millisecond reads (about 1 ms first-byte read, 2.7 ms write); lowest latency | no | EFS performance.html ; features.html |
| Storage class Infrequent Access (IA) | Data accessed only a few times a quarter; first byte tens of milliseconds; minimum billing 128 KiB per file; no minimum duration | no | EFS features.html |
| Storage class Archive | Data accessed a few times a year or less; tens of ms; minimum billing 128 KiB per file; 90-day minimum storage duration; Regional only | changed (Archive class is newer than 2022) | EFS features.html |
| Archive requires Elastic | Archive needs Elastic throughput; if a policy transitions to Archive you cannot switch to Bursting or Provisioned | changed | EFS features.html |
| One Zone classes | One Zone and One Zone-IA exist for One Zone file systems | no | EFS storage-classes.html |
| Lifecycle to IA thresholds | 1, 7, 14, 30, 60, 90, 180, 270, 365 days since last access | no | EFS storage-classes.html |
| Lifecycle back to Standard | Files can return to Standard on access (TransitionToPrimaryStorageClass AFTER_1_ACCESS) | no | EFS storage-classes.html |
| Small files | Since 2023-11-26 lifecycle policies can tier files under 128 KiB to IA; IA/Archive bill at least 128 KiB per file | changed 2023-11-26 | EFS features.html |
| Data access charges | Per-GB charge when reading IA/Archive or when data transitions between classes; not charged when AWS Backup backs up | no | EFS features.html |
| Throughput modes | Elastic (recommended default), Provisioned, Bursting | changed (Elastic is newer) | EFS performance.html |
| Elastic throughput | Scales automatically; best for spiky or unpredictable workloads (average-to-peak 5 % or less); pay per data read/written; no burst credits | changed | EFS performance.html |
| Provisioned throughput | You set throughput independent of size; use when average-to-peak is 5 % or more; billed above included baseline; after raising or switching, 24-hour restrictions on lowering or switching back | no | EFS performance.html |
| Bursting throughput | Baseline 50 KiB/s per GiB of Standard storage (50 MiB/s per TiB), burst to 100 MiB/s per TiB (minimum 100 MiB/s); credit cap 2.1 TiB; large file systems burst up to 12 hours a day | no | EFS performance.html |
| Elastic max throughput | Regional default 60 GiB/s read and 5 GiB/s write in major Regions (20 and 1 elsewhere); per-client 1,500 MiB/s with efs-utils 2.0+ | changed (numbers are newer) | EFS limits.html ; performance.html |
| Elastic IOPS | Up to 250,000 read IOPS (frequently accessed), 90,000 (infrequently accessed), 50,000 write by default; page table shows up to 2.5 million read | changed | EFS limits.html ; performance.html |
| Performance modes | General Purpose (default, lowest latency, recommended for all) and Max I/O (previous generation, higher latency) | changed (Max I/O now legacy) | EFS performance.html |
| Max I/O status | Not supported for One Zone file systems or Elastic throughput; AWS recommends General Purpose for all file systems | changed | EFS performance.html |
| Latency | About 1 ms read and 2.7 ms write (Regional); about 1.6 ms write on One Zone | no | EFS performance.html |
| Consistency | Close-to-open consistency; advisory locking only; up to 512 locks per file | no | EFS features.html |
| Max file size | 47.9 TiB per file | no | EFS limits.html |
| Connections and access points | 25,000 connections per file system; 10,000 access points per file system | no | EFS limits.html |
| File systems per Region | 1,000 per account per Region (adjustable) | no | EFS limits.html |
| Access points | Application-specific entry points that enforce a POSIX user/group identity and a root directory; combine with IAM policies; need a mount target | no | EFS efs-access-points.html |
| Encryption | At rest (enabled at creation, KMS) and in transit (enabled at mount via TLS); NFS client access also controlled by IAM and security groups | no | EFS whatisefs.html |
| IAM for NFS clients | IAM authorization for NFS clients available | changed (newer) | EFS features.html |
| Replication | Replicate a file system to another Region; RPO and RTO in minutes | changed (newer) | EFS features.html |
| EFS vs EBS | EFS: shared, multi-AZ, Linux NFS, elastic; EBS: one AZ, block, one instance (except Multi-Attach) | no | EFS whatisefs.html ; EBS ebs-volumes-multi.html |
| EFS price vs EBS gp3 | EFS Standard 0.30 USD per GB-month vs gp3 0.08 (about 3.75x, derived from price rows in section 12) | no | EFS price file ; EBS price page |

### FSx

| Fact | Value | Changed? | Source |
|---|---|---|---|
| FSx for Windows File Server | Fully managed Windows Server file servers on a native Windows file system | no | FSXW what-is.html |
| FSx Windows protocol | SMB 2.0 to 3.1.1; accessible from Windows (Server 2008/Win 7 and later) and current Linux | no | FSXW what-is.html |
| FSx Windows AD integration | Works with Microsoft Active Directory for authentication and access control; join the file system to AD at creation (AWS Managed Microsoft AD or self-managed) | no | FSXW what-is.html |
| FSx Windows availability | Single-AZ and Multi-AZ (standby file server in a second AZ with failover) | no | FSXW what-is.html |
| FSx Windows features | NTFS ACLs, VSS shadow copies, automatic daily backups on by default, DNS aliases | no | FSXW what-is.html |
| FSx Windows storage | SSD or HDD; storage, SSD IOPS and throughput provisioned independently | no | FSXW what-is.html |
| FSx Windows encryption | At rest with KMS; in transit with SMB Kerberos session keys | no | FSXW what-is.html |
| FSx Windows answer | Lift-and-shift Windows apps, home directories, SMB shares, AD-integrated | no | FSXW what-is.html |
| FSx for Lustre | Managed Lustre for ML, HPC, video processing, financial modeling; sub-millisecond latency, up to multiple TB/s throughput and millions of IOPS | no | FSXL what-is.html |
| FSx Lustre OS | POSIX-compliant; Linux clients (AL2023/AL2, RHEL, CentOS, Ubuntu, SUSE) | no | FSXL what-is.html |
| FSx Lustre scratch | Temporary storage and shorter-term processing; data not replicated and lost if a file server fails | no | FSXL what-is.html |
| FSx Lustre persistent | Longer-term storage; data replicated and failed servers replaced | no | FSXL what-is.html |
| FSx Lustre storage classes | SSD, Intelligent-Tiering and HDD | changed (Intelligent-Tiering class is newer) | FSXL what-is.html |
| FSx Lustre S3 integration | Link to an S3 bucket; objects appear as files; write data back to S3; data repository tasks | no | FSXL what-is.html |
| FSx Lustre integrations | SageMaker AI, AWS Batch, AWS ParallelCluster; on-prem burst over Direct Connect/VPN | no | FSXL what-is.html |
| FSx Lustre answer | HPC and ML training needing fast shared storage linked to S3 | no | FSXL what-is.html |
| FSx for NetApp ONTAP | Managed NetApp ONTAP; protocols NFS, SMB and iSCSI in one file system (multi-protocol); Windows, Linux, macOS clients | no | FSXO what-is-fsx-ont.html (thin page summary, medium confidence) |
| FSx ONTAP data features | Snapshots, FlexClone clones, SnapMirror replication, deduplication and compression, tiering to a lower-cost capacity pool, Multi-AZ | no | FSXO what-is-fsx-ont.html (thin page summary, medium confidence) |
| FSx ONTAP answer | Migrate on-premises NetApp or need NFS + SMB + iSCSI, replication to on-prem NetApp | no | FSXO what-is-fsx-ont.html (thin page summary, medium confidence) |
| FSx for OpenZFS | Managed OpenZFS; NFS v3, v4.0, v4.1, v4.2; Linux, Windows, macOS clients | no | FSXZ what-is-fsx.html |
| FSx OpenZFS performance | Up to 2 million IOPS, latencies of hundreds of microseconds; up to 21 GB/s from cache | no | FSXZ what-is-fsx.html |
| FSx OpenZFS features | Instant snapshots, cloning, compression, multiple volumes, thin provisioning, user and group quotas | no | FSXZ what-is-fsx.html |
| FSx OpenZFS deployment | Multi-AZ (HA), Single-AZ (HA), Single-AZ (non-HA); failover typically within 60 seconds | no | FSXZ what-is-fsx.html |
| FSx OpenZFS storage classes | Intelligent-Tiering and SSD | changed (newer) | FSXZ what-is-fsx.html |
| FSx OpenZFS S3 access points | S3 Access Points can attach to FSx for OpenZFS volumes | changed (new) | FSXZ what-is-fsx.html ; S3UG Welcome.html |
| FSx OpenZFS answer | Move on-premises ZFS or Linux file servers without changing apps | no | FSXZ what-is-fsx.html |
| FSx common | All encrypt at rest with KMS; HIPAA eligible; assessed for ISO, PCI-DSS, SOC | no | FSXW / FSXL / FSXZ what-is pages |
| Pick-a-file-system summary | Windows/SMB/AD: FSx Windows; HPC/Lustre: FSx Lustre; multi-protocol/NetApp: FSx ONTAP; ZFS/NFS: FSx OpenZFS; generic Linux NFS elastic: EFS | no | derived from the pages above |

### Storage Gateway

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Gateway types | S3 File Gateway, FSx File Gateway, Volume Gateway, Tape Gateway | no | SGW storagegateway/ (docs index) |
| S3 File Gateway | Stores and retrieves objects in S3 using NFS v3 or v4.1 and SMB v2 or v3; transparent local caching; deploy as VM (ESXi, Hyper-V, KVM, Nutanix AHV), EC2 AMI, VMware Cloud on AWS, or hardware appliance | changed (Nutanix AHV support is newer) | FGW files3/what-is-file-s3.html |
| S3 File Gateway integrates | IAM, KMS, CloudWatch, CloudTrail; S3 lifecycle, CRR and versioning apply to the data | no | FGW files3/what-is-file-s3.html |
| FSx File Gateway | Provides on-premises access to FSx for Windows File Server shares; closed to new customers | changed (closed to new customers; closure date not confirmed) | FGW filefsxw/ pages (medium confidence) |
| FSx File Gateway existing users | Existing customers can keep using it; migration between gateway types not supported | changed | FGW filefsxw/migrate-data.html (medium confidence) |
| Volume Gateway | iSCSI block volumes; cached or stored architecture; snapshots stored as EBS snapshots in S3 | no | SGW vgw/StorageGatewayConcepts.html |
| Cached volumes | Primary data in S3; frequently accessed data cached locally; volumes 1 GiB to 32 TiB; up to 32 volumes and 1,024 TiB per gateway | no | SGW vgw/StorageGatewayConcepts.html |
| Cached local disks | Cache storage plus upload buffer; allocate at least 20 percent of the existing file store as cache and cache larger than upload buffer | no | SGW vgw/StorageGatewayConcepts.html |
| Stored volumes | Primary data on-premises; async backup to S3 as EBS snapshots; volumes 1 GiB to 16 TiB; up to 32 volumes and 512 TiB per gateway | no | SGW vgw/StorageGatewayConcepts.html |
| Volume snapshots | Incremental snapshots stored in S3 as EBS snapshots; can seed a new EBS volume (snapshots up to 16 TiB for cached) | no | SGW vgw/StorageGatewayConcepts.html |
| Volume Gateway answer | Cached = low-latency access to hot data with S3 primary; Stored = entire data set local with cloud backup | no | SGW vgw/StorageGatewayConcepts.html |
| Tape Gateway | Virtual tape library for backup apps; archive in S3 Glacier Flexible Retrieval or Deep Archive; removes physical tape | no | SGW tgw/WhatIsStorageGateway.html |
| Local cache | All gateways use on-premises disks for cache; low-latency access to recent data | no | SGW vgw/StorageGatewayConcepts.html |

### Other storage services

| Fact | Value | Changed? | Source |
|---|---|---|---|
| AWS Backup | Centralized, policy-based backup (backup plans, vaults, tag-based), cross-Region and cross-account copy, vault lock (WORM), Audit Manager | no | BKP whatisbackup.html |
| AWS Backup supported storage | EBS, S3, EFS, FSx (Lustre, Windows, ONTAP, OpenZFS), Storage Gateway Volume Gateway, EC2, RDS, DynamoDB and more | changed (EKS, Aurora DSQL, many others are newer) | BKP whatisbackup.html |
| AWS Backup cold tier | Lifecycle moves backups from warm to cold storage | no | BKP whatisbackup.html |
| Backup incremental | First backup full; later incrementals for supported resources | no | BKP whatisbackup.html |
| AWS DataSync | Online transfer between on-premises (NFS, SMB, HDFS, object storage), AWS storage (S3, EFS, FSx) and other clouds; encryption and integrity validation; scheduled tasks | changed (other-cloud sources are newer) | DS what-is-datasync.html |
| DataSync speed | Purpose-built protocol, parallel multi-threaded; a single task can use 10 Gbps | no | DS what-is-datasync.html ; SNOW snowball-edge-availability-change.html |
| DataSync use cases | Migrate, archive cold data to Glacier classes, replicate, move data for processing | no | DS what-is-datasync.html |
| AWS Transfer Family | Managed SFTP, FTPS, FTP, AS2 and browser-based (web app) transfers into and out of S3 and EFS | changed (web apps added 2024-12) | TF what-is-aws-transfer-family.html |
| Transfer Family details | Up to 3 AZs; FTP/FTPS data port range 8192 to 8200; managed workflows | no | TF what-is-aws-transfer-family.html |
| Snowball Edge status | Snowball Edge: no longer available to new customers; AWS no longer offers Snow Family devices to new customers (Retired services Rule 2) | changed 2025-11-07 (per existing facts.md row) | SNOW snowball-edge-availability-change.html |
| Snow alternatives | DataSync (online), AWS Data Transfer Terminal (physical), AWS Partner solutions; Outposts for edge compute | changed | SNOW snowball-edge-availability-change.html |
| Existing Snow users | Not affected; AWS continues security and availability work | no | SNOW snowball-edge-availability-change.html |

## Databases and caching (week 05)

Source key: RDS = docs.aws.amazon.com/AmazonRDS/latest/UserGuide/ · AUR = docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/ · DSQL = docs.aws.amazon.com/aurora-dsql/latest/userguide/ · DDB = docs.aws.amazon.com/amazondynamodb/latest/developerguide/ · EC = docs.aws.amazon.com/AmazonElastiCache/latest/dg/ · MDB = docs.aws.amazon.com/memorydb/latest/devguide/ · NEP = docs.aws.amazon.com/neptune/latest/userguide/ · DOC = docs.aws.amazon.com/documentdb/latest/developerguide/ · KS = docs.aws.amazon.com/keyspaces/latest/devguide/ · TS = docs.aws.amazon.com/timestream/latest/developerguide/ · OS = docs.aws.amazon.com/opensearch-service/latest/developerguide/ · GR = docs.aws.amazon.com/general/latest/gr/ (page name follows). Research: docs/research/2026-10-12-database-facts.md, official AWS pages read 2026-10-11/12. Where a row says "changed", teach today's value and name the old one once; a "changed" row with no date means the page gives no date, so no question depends on it. Rows marked "medium confidence" come from an inference or a search excerpt. Many rows (Valkey, ElastiCache Serverless, Aurora DSQL, Limitless, MRSC global tables, Database Insights) are newer than SAA-C03: know they exist; exam questions still centre on the classic behaviour (Multi-AZ, read replicas, Aurora replicas, DynamoDB capacity and indexes, cache strategies).

### Amazon RDS

| Fact | Value | Changed? | Source |
|---|---|---|---|
| RDS engines (storage page) | Db2, MariaDB, MySQL, PostgreSQL, Oracle, Microsoft SQL Server | changed (Db2 is a newer engine; Aurora is separate) | RDS CHAP_Storage.html |
| DB instance class families | General purpose (db.m), memory optimized (db.r, db.x, db.z), compute optimized (db.c, only c6gd for Multi-AZ DB clusters), burstable (db.t), Optimized Reads (db.m8gd, db.r8gd, db.r6gd, db.r6id) | no | RDS Concepts.DBInstanceClass.Types.html |
| Latest general purpose classes named | db.m9g (Graviton5), db.m8g (Graviton4), db.m8i (Intel Xeon 6), db.m8a (AMD EPYC 5th gen), db.m7i, db.m7g (Graviton3) | changed (m7g and later are newer than 2022) | RDS Concepts.DBInstanceClass.Types.html |
| Latest memory optimized classes named | db.r8g (Graviton4), db.r8i, db.r8a, db.r7g, db.r7i; db.x2g, db.x2i, db.x1, db.x1e; db.z1d | changed | RDS Concepts.DBInstanceClass.Types.html |
| Burstable classes | db.t4g (Graviton2), db.t3, db.t2; all configured for Unlimited mode | no | RDS Concepts.DBInstanceClass.Types.html |
| db.t4g Unlimited mode | "Configured for Unlimited mode": can burst beyond baseline over a 24-hour window for an additional charge | no | RDS Concepts.DBInstanceClass.Types.html |
| db.t2 retirement | Creating db.t2 no longer supported; automatic upgrade to db.t3 began 2024-06-01; support ended 2024-12-31 (MariaDB, MySQL, SQL Server, PostgreSQL) | changed 2024 | RDS Concepts.DBInstanceClass.Types.html |
| db.m4 and db.r4 retirement | Same schedule: auto-upgrade from 2024-06-01 (to db.m5 / db.r5); support ended 2024-12-31 | changed 2024 | RDS Concepts.DBInstanceClass.Types.html |
| db.m3 and db.r3 | Cannot create; automatic upgrades started 2023-02-01 | changed 2023 | RDS Concepts.DBInstanceClass.Types.html |
| Storage types offered | Provisioned IOPS SSD (io1, io2 Block Express) and General Purpose SSD (gp2, gp3); API names io2, io1, gp3, gp2 | no | RDS CHAP_Storage.html |
| Magnetic storage | Deprecated; cannot create new DB instances; existing volumes migrated to gp3; from 2026-07-01 snapshots cannot be restored to magnetic | changed (deprecated; 2026-07-01 date) | RDS CHAP_Storage.html |
| Max storage, Db2 / MariaDB / MySQL / PostgreSQL | Up to 64 TiB | no | RDS CHAP_Storage.html |
| Max storage, Oracle and SQL Server | Up to 256 TiB using up to three additional storage volumes (primary volume up to 64 TiB) | changed (additional storage volumes are newer) | RDS CHAP_Storage.html |
| Max storage, small classes | db.t4g.micro 6 TiB (MariaDB, MySQL, PostgreSQL); db.t4g.small 16 TiB (PostgreSQL 16); db.t4g.medium MariaDB/MySQL 16, PostgreSQL 32 TiB | no | RDS CHAP_Storage.html |
| gp3 baseline, storage under 400 GiB | 3,000 IOPS and 125 MiB/s (Db2, MariaDB, MySQL, PostgreSQL; Oracle under 200 GiB) | no | RDS CHAP_Storage.html |
| gp3 baseline, storage 400 GiB and above | 12,000 IOPS and 500 MiB/s (striped across four volumes; Oracle from 200 GiB; SQL Server has no threshold, always 3,000 / 125) | no | RDS CHAP_Storage.html |
| gp3 provisioned range at/above threshold | 12,000 to 64,000 IOPS and 500 to 4,000 MiB/s (SQL Server 3,000 to 80,000 IOPS, 125 to 2,000 MiB/s) | no | RDS CHAP_Storage.html |
| gp3 size range | 20 to 65,536 GiB (SQL Server table row says 16,384 GiB in the comparison table) | no | RDS CHAP_Storage.html |
| gp3 latency wording | Single-digit millisecond, provided consistently 99% of the time | no | RDS CHAP_Storage.html |
| gp2 baseline | 3 IOPS per GiB, minimum 100 IOPS; below 1,000 GiB can burst to 3,000 IOPS (credit balance) | no | RDS CHAP_Storage.html |
| gp2 status | "Previous generation"; gp3 labelled recommended | changed (gp3 recommended) | RDS CHAP_Storage.html |
| io2 Block Express max | Up to 256,000 IOPS; sub-millisecond average latency on Nitro-based instances; 100 to 65,536 GiB (MariaDB, MySQL, PostgreSQL, Db2); IOPS-to-GiB ratio 0.5 to 1,000 | changed (io2 Block Express is newer) | RDS CHAP_Storage.html |
| io2 latency wording | Sub-millisecond, provided consistently 99.9% of the time | no | RDS CHAP_Storage.html |
| io1 | Previous generation; up to 256,000 IOPS (SQL Server 64,000); IOPS-to-GiB ratio 0.5 to 50 | no | RDS CHAP_Storage.html |
| Provisioned IOPS billing | Charged for provisioned resources whether or not you use them | no | RDS CHAP_Storage.html |
| Provisioned IOPS best fit | Production, I/O-intensive OLTP, recommended with Multi-AZ; General Purpose "best suited for development and testing environments" | no | RDS CHAP_Storage.html |
| Dedicated log volume (DLV) | For PIOPS storage only (io1, io2); fixed 1,024 GiB and 3,000 IOPS; not for gp2/gp3 | changed (newer feature) | RDS CHAP_Storage.html |
| Storage autoscaling trigger | Free space at or below 10% of allocated storage, low-storage condition lasting at least 5 minutes, and fewer than four storage modifications in the last 24 hours (previous optimization finished) | no | RDS USER_PIOPS.Autoscaling.html |
| Storage autoscaling increment | Greater of 10 GiB, 10% of allocated storage, or predicted growth over the next 7 hours | no | RDS USER_PIOPS.Autoscaling.html |
| Storage autoscaling threshold | Set Maximum storage threshold (--max-allocated-storage); must be at least 10% above current allocated (26% recommended) | no | RDS USER_PIOPS.Autoscaling.html |
| Storage autoscaling downtime | Enabling or changing it needs no reboot and no downtime | no | RDS USER_PIOPS.Autoscaling.html |
| Storage can shrink? | No: allocated storage cannot be reduced after allocation (use blue/green or migrate) | no | RDS USER_PIOPS.Autoscaling.html |
| Read replica autoscaling | RDS does not autoscale read replicas; create and delete them manually | no | RDS USER_ReadRepl.html |
| Multi-AZ DB instance deployment | Synchronous standby replica in a different AZ; "can't use a standby replica to serve read traffic" | no | RDS Concepts.MultiAZSingleStandby.html |
| Multi-AZ DB instance purpose | High availability, not a read-scaling solution; use a read replica or Multi-AZ DB cluster to serve reads | no | RDS Concepts.MultiAZSingleStandby.html |
| Multi-AZ DB instance failover wording | "Failover times are typically 60-120 seconds"; large transactions or lengthy recovery can increase it | no | RDS Concepts.MultiAZ.Failover.html |
| Multi-AZ failover endpoint | RDS changes the DNS record of the DB instance to point to the standby; clients must reconnect; AWS recommends JVM DNS TTL of no more than 60 seconds | no | RDS Concepts.MultiAZ.Failover.html |
| Multi-AZ failover triggers | OS patching, unhealthy primary host, loss of network connectivity, instance modification, busy/unresponsive primary, storage volume failure, manual reboot with failover | no | RDS Concepts.MultiAZ.Failover.html |
| Multi-AZ technology by engine | MariaDB, MySQL, Oracle, PostgreSQL use Amazon failover technology; SQL Server uses Database Mirroring or Always On Availability Groups | no | RDS Concepts.MultiAZSingleStandby.html |
| Multi-AZ write latency | Synchronous replication can increase write and commit latency compared with Single-AZ | no | RDS Concepts.MultiAZSingleStandby.html |
| Convert Single-AZ to Multi-AZ | Modify the DB instance and specify Multi-AZ (console, CLI or API) | no | RDS Concepts.MultiAZSingleStandby.html |
| Multi-AZ OS maintenance | Standby patched first, standby promoted, old primary patched; failover typically lasts less than a minute | no | RDS USER_UpgradeDBInstance.Maintenance.html |
| Multi-AZ engine upgrade | Both primary and standby are modified at the same time and both are unavailable until upgrade completes | no | RDS USER_UpgradeDBInstance.Maintenance.html |
| Multi-AZ DB cluster definition | Semisynchronous deployment with a writer and two readable reader instances in three separate AZs in one Region | changed (Multi-AZ DB clusters are newer than 2022 GA of Multi-AZ instance) | RDS multi-az-db-clusters-concepts.html |
| Multi-AZ DB cluster replication | Semisynchronous: commit needs acknowledgment from at least one reader | no | RDS multi-az-db-clusters-concepts.html |
| Multi-AZ DB cluster benefits | High availability, increased read capacity, lower write latency vs Multi-AZ DB instance | no | RDS multi-az-db-clusters-concepts.html |
| Multi-AZ DB cluster failover time | "Failover times are typically under 35 seconds"; completes when both readers applied outstanding transactions | no | RDS multi-az-db-clusters-concepts-failover.html |
| Multi-AZ DB cluster instance classes | db.c6gd, db.m5d, db.m6gd, db.m6id, db.m6idn, db.m8gd, db.r5d, db.r6gd, db.r6id, db.r6idn, db.r8gd, db.x2iedn | changed (list contains newer classes) | RDS multi-az-db-clusters-concepts.html |
| Multi-AZ DB cluster backups | Cluster-level storage snapshot; retention 1 to 35 days (0 not allowed); "You can't copy a snapshot of a Multi-AZ DB cluster" (copy page limitation) | no | RDS USER_WorkingWithAutomatedBackups.BackupRetention.html ; RDS USER_CopySnapshot.html |
| Multi-AZ DB cluster vs Aurora | "Multi-AZ DB clusters aren't the same as Aurora DB clusters" | no | RDS multi-az-db-clusters-concepts.html |
| Read replica definition | Read-only copy of a DB instance; RDS uses engine native replication; source becomes the primary | no | RDS USER_ReadRepl.html |
| Read replica replication type | Asynchronous (standby replica in Multi-AZ is synchronous) | no | RDS USER_ReadRepl.html |
| Read replica creation | RDS takes a snapshot of the source and creates a read-only instance from it | no | RDS USER_ReadRepl.html |
| Read replica billing | Billed as a standard DB instance; no data transfer charge between source and replica in the same Region | no | RDS USER_ReadRepl.html |
| Read replica use cases | Scale reads, serve reads when source unavailable, reporting, disaster recovery by promotion | no | RDS USER_ReadRepl.html |
| Read replica on Multi-AZ source | Allowed: a source with a Multi-AZ standby can also have read replicas | no | RDS USER_ReadRepl.html |
| Read replicas per source (quota table) | "Read replicas per primary: 15" per Region, adjustable; cannot be adjusted for Aurora | no | RDS CHAP_Limits.html |
| RDS MySQL read replica max | "You can create up to 15 read replicas from one DB instance within the same Region" | no | RDS USER_MySQL.Replication.ReadReplicas.html |
| RDS PostgreSQL read replica max | 15, from the account quota "Read replicas per primary" (not engine-specific); the PostgreSQL page itself states no number (medium confidence) | no | RDS CHAP_Limits.html ; RDS USER_PostgreSQL.Replication.ReadReplicas.html |
| RDS Oracle read replica max | Up to 15 per source per Region, but AWS recommends limiting to 5 to minimize replication lag | no | RDS CHAP_Limits.html |
| Cascading read replicas | MariaDB and MySQL yes; PostgreSQL 14.1 and higher only; Db2, Oracle, SQL Server cannot replicate from a replica | changed (PostgreSQL cascading from 14.1) | RDS USER_ReadRepl.html ; RDS USER_PostgreSQL.Replication.ReadReplicas.html |
| MySQL replica requirement | Source needs automated backups on (retention not 0); replica cannot use a lower engine version than source | no | RDS USER_MySQL.Replication.ReadReplicas.html |
| Cross-Region read replicas | Supported; RDS sets up a secure channel; data in transit between source and replica is encrypted | no | RDS USER_ReadRepl.html ; RDS Overview.Encryption.html |
| Cross-Region replica quota | Concurrent cross-Region read replica requests default 20 per Region | no | RDS CHAP_Limits.html |
| Promote a read replica | Becomes a standalone writable DB instance; process is not reversible (PostgreSQL page) | no | RDS USER_PostgreSQL.Replication.ReadReplicas.html |
| Delete source with replicas | Same-Region replicas are automatically promoted to standalone instances | no | RDS USER_ReadRepl.html |
| Replica storage type | Can differ from source (e.g. gp3 replica for io2 source) | no | RDS USER_ReadRepl.html |
| PostgreSQL replica PITR | Point-in-time recovery not supported on read replicas; automated backups on replicas need PostgreSQL 14.1+ | no | RDS USER_PostgreSQL.Replication.ReadReplicas.html |
| PostgreSQL idle replica lag | With no transactions, reported lag can rise to 5 minutes (WAL segment switch every 5 minutes) | no | RDS USER_PostgreSQL.Replication.ReadReplicas.html |
| Automated backups: what | RDS storage volume snapshot of the whole instance during the backup window, plus transaction logs; saved per retention period; stored in Amazon S3 | no | RDS USER_WorkingWithAutomatedBackups.html |
| Retention range (DB instance) | 0 to 35 days; 0 disables automated backups | no | RDS USER_WorkingWithAutomatedBackups.BackupRetention.html |
| Retention default, console | 7 days | no | RDS USER_WorkingWithAutomatedBackups.BackupRetention.html |
| Retention default, CLI or API | 1 day | no | RDS USER_WorkingWithAutomatedBackups.BackupRetention.html |
| Changing retention 0 <-> nonzero | Causes an outage | no | RDS USER_WorkingWithAutomatedBackups.BackupRetention.html |
| Restore retention inheritance | A restored DB inherits the source retention unless set; new databases get the default | changed (explicit inheritance wording is recent) | RDS USER_WorkingWithAutomatedBackups.BackupRetention.html |
| Stopped DB instance | Time in stopped state not counted; automated backups not created while stopped | no | RDS USER_WorkingWithAutomatedBackups.BackupRetention.html |
| Backup window vs maintenance window | The maintenance window and the backup window cannot overlap | no | RDS USER_UpgradeDBInstance.Maintenance.html |
| Backup storage location | Backup storage per Region = automated backups + manual snapshots; stored in Amazon S3 | no | RDS USER_WorkingWithAutomatedBackups.html |
| First snapshot / later snapshots | First snapshot is full; subsequent snapshots incremental | no | RDS USER_WorkingWithAutomatedBackups.html |
| PITR transaction log upload | RDS uploads transaction logs to Amazon S3 every five minutes | no | RDS USER_PIT.html |
| Latest restorable time | Visible as LatestRestorableTime (describe-db-instances); typically within the last 5 minutes because logs upload every 5 minutes | no | RDS USER_PIT.html |
| PITR window | Any time within the backup retention period (earliest restorable time shown in console) | no | RDS USER_PIT.html |
| PITR creates new instance | "Creating a new DB instance without modifying the source DB instance" | no | RDS USER_PIT.html |
| Restore storage rule | Cannot reduce storage on restore; increase must be at least 10% | no | RDS USER_PIT.html |
| Restored instance defaults | Gets default parameter group and option group unless specified; volumes lazily load blocks from S3 so performance may be lower until initialization completes | no | RDS USER_PIT.html |
| Manual snapshots limit | Up to 100 per Region (adjustable quota); AWS Backup snapshots do not count | no | RDS CHAP_Limits.html |
| Manual snapshots retention | Kept until you delete them; not deleted when the DB instance is deleted | no | RDS USER_CopySnapshot.html ; RDS USER_DeleteInstance.html |
| Automated backups on instance delete | Deleted with the instance unless you choose Retain automated backups (kept for retention period, billed) | no | RDS USER_DeleteInstance.html |
| Cross-Region snapshot copy | Supported (not to or from China Regions); up to 20 concurrent copies per account per destination Region; data transfer charges; first copy is full, later can be incremental | no | RDS USER_CopySnapshot.html |
| Encrypted snapshot cross-Region copy | Must specify a KMS key valid in the destination Region (or a multi-Region key) | no | RDS USER_CopySnapshot.html |
| Share snapshots | Manual snapshots can be shared (including cross-account copy in one step after sharing, and sharing the KMS key); default AWS managed key snapshots cannot be shared | no | RDS USER_CopySnapshot.html ; RDS Overview.Encryption.html |
| Replicate automated backups | Automated backups can be replicated to another Region | no | RDS USER_DeleteInstance.html |
| Encryption at rest cipher | AES-256 via AWS KMS; covers storage, logs, automated backups, read replicas, snapshots | no | RDS Overview.Encryption.html |
| Encryption only at creation | "You can only encrypt an Amazon RDS DB instance when you create it, not after" | no | RDS Overview.Encryption.html |
| Encrypt an existing database | Snapshot, copy the snapshot with encryption enabled (KMS key), restore from the encrypted copy; blue/green deployment can also encrypt or change key | changed (blue/green route is newer) | RDS Overview.Encryption.html |
| Cannot unencrypt | Cannot turn off encryption; no encrypted snapshot of unencrypted instance directly | no | RDS Overview.Encryption.html |
| Replica encryption rule | "You can't have an encrypted read replica of an unencrypted DB instance or an unencrypted read replica of an encrypted DB instance" (which KMS key a same-Region replica may use is not confirmed) | no | RDS Overview.Encryption.html |
| Change KMS key | Cannot change KMS key of an existing encrypted instance (copy snapshot with new key instead) | no | RDS Overview.Encryption.html |
| Lost KMS key access | After disabling key, instance enters inaccessible-encryption-credentials-recoverable (2 hours after detection, 7 days to recover) then terminal state; RDS makes a final snapshot | changed (recoverable state and automatic final snapshot are newer) | RDS Overview.Encryption.html |
| Encryption in transit | SSL/TLS supported on all engines (Db2, MariaDB, SQL Server, MySQL, Oracle, PostgreSQL) | no | RDS UsingWithRDS.SSL.html |
| rds.force_ssl (PostgreSQL) | Parameter default 1 (on) for PostgreSQL 15 and later; 0 (off) for 14 and older; set via custom parameter group; non-SSL connections rejected | changed (default on for 15+) | RDS PostgreSQL.Concepts.General.SSL.html |
| PostgreSQL TLS versions | TLS 1.1 and 1.2; TLS 1.3 on PostgreSQL 16 and later; ssl_min_protocol_version shown as TLSv1.2 | changed | RDS PostgreSQL.Concepts.General.SSL.html |
| Default RDS CA | rds-ca-rsa2048-g1 (others rds-ca-rsa4096-g1, rds-ca-ecc384-g1) | changed (older rds-ca-2019 not listed) | RDS UsingWithRDS.SSL.html |
| IAM database authentication | Works with MariaDB, MySQL and PostgreSQL; no password, uses an authentication token | no | RDS UsingWithRDS.IAMDBAuth.html |
| IAM auth token lifetime | 15 minutes (only needed to authenticate; session continues after) | no | RDS UsingWithRDS.IAMDBAuth.html |
| IAM auth token signing | AWS Signature Version 4; connections use SSL/TLS | no | RDS UsingWithRDS.IAMDBAuth.html |
| IAM auth memory cost | Needs 300 to 1000 MiB extra memory on the database | no | RDS UsingWithRDS.IAMDBAuth.html |
| Secrets Manager master password | Set ManageMasterUserPassword=true (--manage-master-user-password); RDS generates and stores the password in Secrets Manager | changed (feature newer than 2022) | RDS rds-secrets-manager.html |
| Secrets Manager rotation default | RDS rotates the secret every seven days by default (schedule can be modified); resolves the "7 days?" query | changed | RDS rds-secrets-manager.html |
| Secrets Manager integration limits | Not supported with Blue/Green Deployments, RDS Custom, Oracle Data Guard switchover; creating replicas from a source that manages credentials not supported for most engines | changed | RDS rds-secrets-manager.html |
| Secrets Manager billing and KMS | Secrets Manager charges apply; KMS key for the secret cannot be changed once managed | no | RDS rds-secrets-manager.html |
| RDS Proxy purpose | Pool and share database connections; makes applications more resilient to database failures | no | RDS rds-proxy.html |
| RDS Proxy failover claim | Bypasses DNS caches to reduce failover times "by up to 66%" for RDS Multi-AZ DB instances (and for Aurora Multi-AZ) | no | RDS rds-proxy-planning.html ; AUR Concepts.AuroraHighAvailability.html |
| RDS Proxy auth | Clients can be forced to use IAM authentication; proxy connects to the database with IAM auth or Secrets Manager credentials | no | RDS rds-proxy.html |
| RDS Proxy and Lambda | Lambda functions are good candidates (frequent short connections); also any app without built-in pooling; not Lambda-only | no | RDS rds-proxy-planning.html |
| RDS Proxy quotas | 20 proxies per account; up to 200 Secrets Manager secrets per proxy; up to 20 additional endpoints per proxy | no | RDS rds-proxy.html |
| RDS Proxy network | Must be in the same VPC as the database; cannot be publicly accessible; not supported on dedicated-tenancy VPCs; default endpoint spans two AZs | no | RDS rds-proxy.html |
| RDS Proxy and replicas | For RDS instances in replication configurations, proxy can attach only to the writer (not a read replica) | no | RDS rds-proxy.html |
| RDS Proxy pinning | Statement text over 16 KB pins the session to a connection (reduces multiplexing) | no | RDS rds-proxy.html |
| RDS Proxy and Blue/Green | Proxy redirects connections to the green environment on switchover without waiting for DNS propagation | changed | RDS rds-proxy-planning.html |
| RDS Proxy and minor upgrade | Can reduce Multi-AZ DB cluster minor upgrade downtime to one second or less | changed | RDS multi-az-db-clusters-concepts.html |
| Blue/Green Deployments | Green staging environment copies production (blue) and stays in sync; switchover promotes green | changed (feature newer than 2022) | RDS blue-green-deployments-overview.html |
| Blue/Green RDS engines | RDS for MariaDB, MySQL and PostgreSQL | changed | RDS blue-green-deployments-overview.html |
| Blue/Green switchover time | "Typically takes under a minute" with no data loss and no application changes (downtime can be longer depending on workload) | changed | RDS blue-green-deployments-overview.html |
| Blue/Green after switchover | Names and endpoints move to new production; old environment renamed with -old1 suffix and kept for regression testing | no | RDS blue-green-deployments-overview.html |
| Maintenance window | Weekly interval; 30 minutes; if not specified RDS assigns a random 30-minute window on a random day from an 8-hour block per Region | no | RDS USER_UpgradeDBInstance.Maintenance.html |
| Maintenance window, us-east-1 block | 03:00 to 11:00 UTC | no | RDS USER_UpgradeDBInstance.Maintenance.html |
| Required maintenance | OS or database patches for security and reliability, scheduled automatically, "once every few months"; cannot be deferred indefinitely | no | RDS USER_UpgradeDBInstance.Maintenance.html |
| Operating system updates | Typically about 10 minutes; optional or mandatory with an apply date | no | RDS USER_UpgradeDBInstance.Maintenance.html |
| Deletion protection default, console | On by default for instances created with the console (the CLI/API default is not confirmed) | no | RDS USER_DeleteInstance.html |
| Deletion protection removal | Turn off by modifying the instance; no outage | no | RDS USER_DeleteInstance.html |
| Final snapshot on delete | Optional; can restore deleted instance from it; AWS Support may recover an accidentally deleted instance for up to six days | no | RDS USER_DeleteInstance.html |
| Database Insights | RDS enables Database Insights in Advanced mode by default (lock diagnostics, execution plan capture, fleet monitoring) | changed (Database Insights is newer; Performance Insights page now titled Database Insights) | RDS USER_PerfInsights.Overview.html |
| Database Insights retention | Default includes 7 days of history and 1 million API requests per month; longer retention selectable from 1 to 24 months | changed | RDS USER_PerfInsights.Overview.cost.html |
| Performance Insights status | Chapter title on the RDS guide is "Monitoring DB load with Amazon CloudWatch Database Insights"; Performance Insights API and CloudTrail topics still listed | changed | RDS USER_PerfInsights.html |
| RDS Custom | Managed database service with access to the underlying OS and database; engines Oracle Database and Microsoft SQL Server only | no | RDS rds-custom.html |
| RDS Extended Support | Paid option to keep running a major engine version past RDS end of standard support, up to 3 years; auto-enrolled if enabled at create/restore | changed (Extended Support launched 2024) | RDS extended-support.html |
| Extended Support example | MySQL 5.7 end of standard support 2024-02-29; charges started 2024-03-01 | changed 2024 | RDS extended-support.html |
| Extended Support coverage | Critical and high CVE security updates, bug fixes for critical issues, support cases; disabling after standard end triggers upgrade to next supported major version | changed | RDS extended-support.html |
| Instance quota | 40 DB instances per Region by default (20 in ap-south-1); counts RDS, Aurora, Neptune, DocumentDB instances | no | RDS CHAP_Limits.html |
| max_connections default (MySQL) | DBInstanceClassMemory/12582880; db.t3.micro about 60 | no | RDS CHAP_Limits.html |
| max_connections default (PostgreSQL) | LEAST(DBInstanceClassMemory/9531392, 5000) | no | RDS CHAP_Limits.html |
| Connection advice | Frequent open/close or many long-lived connections: use RDS Proxy | no | RDS CHAP_Limits.html |

### Amazon Aurora

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Cluster volume | Single virtual SSD volume with copies of data across three Availability Zones in one Region | no | AUR Aurora.Overview.StorageReliability.html |
| Six copies | Data synchronously replicated to six storage nodes across AZs | no | AUR Concepts.AuroraHighAvailability.html |
| Replication independent of instances | Amount of replication is independent of the number of DB instances in the cluster | no | AUR Aurora.Overview.StorageReliability.html |
| Storage auto grow | Cluster volume grows automatically; you pay only for space used; space freed when data removed (dynamic resizing) | changed (dynamic shrinking is newer) | AUR Aurora.Overview.StorageReliability.html |
| Max cluster volume 256 TiB | Aurora PostgreSQL 17.5+, 16.9+, 15.13+; Aurora MySQL 3.10+ | changed (was 128 TiB) | AUR CHAP_Limits.html |
| Max cluster volume 128 TiB | All earlier Aurora PostgreSQL versions; Aurora MySQL 3 below 3.10; Aurora MySQL 2.09+ | changed | AUR CHAP_Limits.html |
| Table size limits | Aurora MySQL 64 TiB per table; Aurora PostgreSQL 32 TiB per table | no | AUR CHAP_Limits.html |
| Aurora Replicas max | Up to 15 per DB cluster; asynchronous, share the same cluster volume | no | AUR Aurora.Replication.html ; AUR Concepts.AuroraHighAvailability.html |
| Replica lag | "Usually much less than 100 milliseconds" after the writer updates | no | AUR Aurora.Replication.html |
| Replicas as failover targets | Writer failure promotes an Aurora Replica; without replicas the primary is recreated in same AZ (typically under 10 minutes) | no | AUR Concepts.AuroraHighAvailability.html |
| Aurora failover time | "Service is typically restored in less than 60 seconds, and often less than 30 seconds" | no | AUR Concepts.AuroraHighAvailability.html |
| Promotion priority tiers | 0 (highest) to 15 (lowest); same tier then largest size; priority change does not trigger failover | no | AUR Concepts.AuroraHighAvailability.html |
| Aurora with RDS Proxy | Reduces failover times by up to 66% for Aurora Multi-AZ | no | AUR Concepts.AuroraHighAvailability.html |
| Cluster (writer) endpoint | Always points to the current primary instance; use for read/write and general connections | no | AUR Aurora.Overview.Endpoints.html |
| Reader endpoint | Connection-balances read-only connections across Aurora Replicas | no | AUR Aurora.Overview.Endpoints.html |
| Custom endpoint | Maps to a chosen subset of instances; quota 5 per cluster (adjustable) | no | AUR Aurora.Overview.Endpoints.html ; AUR CHAP_Limits.html |
| Instance endpoint | Specific instance for diagnosis or tuning; does not follow failover | no | AUR Aurora.Overview.Endpoints.html |
| Global Database writer endpoint | Special endpoint that follows the primary cluster across Regions after switchover/failover | changed (newer) | AUR Aurora.Overview.Endpoints.html |
| Aurora Replicas and endpoints on failover | Reader endpoint may briefly send connections to the newly promoted primary | no | AUR Aurora.Overview.Endpoints.html |
| Global Database and Aurora Auto Scaling | Aurora Global Database does not support Aurora Auto Scaling for secondary DB clusters | no | AUR aurora-global-database.html |
| Serverless v2 ACU | Each ACU approximately 2 GiB memory plus corresponding CPU and networking | no | AUR aurora-serverless-v2.how-it-works.html |
| Serverless v2 capacity range | 0.5 to 128 ACUs (MySQL 3.02+); 0.5 to 256 (3.06+); 0 to 256 (3.08+; PostgreSQL 13.15+, 14.12+, 15.7+, 16.3+) | changed (scale to 0 and 256 ACU are newer) | AUR aurora-serverless-v2.how-it-works.html |
| Serverless v2 scaling step | Increments as small as 0.5 ACU; no pause in processing | no | AUR aurora-serverless-v2.how-it-works.html |
| Serverless v2 min 0 = auto-pause | Setting minimum capacity to 0 ACUs enables auto-pause; no instance charge while paused (storage still charged) | changed 2024-11-20 | AUR aurora-serverless-v2-auto-pause.html |
| Auto-pause timeout | Minimum 300 seconds (default) up to 86,400 seconds (one day) idle | changed | AUR aurora-serverless-v2-auto-pause.html |
| Auto-pause resume time | Typically about 15 seconds; 30 seconds or longer if paused over 24 hours | changed | AUR aurora-serverless-v2-auto-pause.html |
| Auto-pause blockers | Open user connections, RDS Proxy attached, primary cluster of a Global Database, logical replication/binlog on writer, zero-ETL | changed | AUR aurora-serverless-v2-auto-pause.html |
| Serverless v2 reader tiers | Readers in tiers 0 and 1 track writer capacity; tiers 2 to 15 scale independently | no | AUR aurora-serverless-v2.how-it-works.html |
| Serverless v2 readers | Up to 15 serverless readers across 3 AZs; mixed provisioned and serverless clusters allowed | no | AUR aurora-serverless-v2.how-it-works.html |
| Serverless v2 billing | ACU-hours, measured per second | no | AUR aurora-serverless-v2.html |
| Aurora Serverless v1 | retired: end of life 2025-03-31; no new v1 clusters from 2025-01-08; remaining clusters auto-migrated (v1 to v2) or converted to provisioned (medium confidence: search-result excerpt) | changed 2025-03-31 | AUR aurora-serverless-v2.upgrade.html |
| Global Database definition | One primary Region plus up to 10 read-only secondary Regions | changed (up to 10 secondary clusters on the current page; earlier limit and date not confirmed) | AUR aurora-global-database.html |
| Global Database replication | Storage-level, dedicated infrastructure, latency "typically under a second" | no | AUR aurora-global-database.html |
| Global Database secondary readers | Secondary cluster can have up to 16 read-only instances (limit 15 for a normal cluster) | no | AUR aurora-global-database.html |
| Global Database RTO wording | "RTO can be in the order of minutes" | no | AUR aurora-global-database-disaster-recovery.html |
| Global Database RPO wording | "RPO is typically measured in seconds" for failover; switchover RPO is 0 | no | AUR aurora-global-database-disaster-recovery.html |
| Switchover vs failover | Switchover (formerly managed planned failover): healthy, no data loss; failover (allow data loss): unplanned outage in primary Region | changed (terminology renamed) | AUR aurora-global-database-disaster-recovery.html |
| Switchover recovery time | Under 30 seconds typical on Aurora MySQL 3.09+ and Aurora PostgreSQL 16.8, 15.12, 14.17, 13.20 or higher | changed | AUR aurora-global-database-disaster-recovery.html |
| Manual failover (detach and promote) | Detach chosen secondary, which becomes a standalone cluster with read/write; recreate the global database by adding Regions | no | AUR aurora-global-database-disaster-recovery.html |
| Failover caution | Asynchronous replication means unreplicated writes can be lost; split-brain risk | no | AUR aurora-global-database-disaster-recovery.html |
| PostgreSQL RPO parameter | rds.global_db_rpo, valid values 20 to 2,147,483,647 seconds; transactions block if all secondaries exceed the RPO | changed | AUR aurora-global-database-disaster-recovery.html |
| Write forwarding | Secondary cluster forwards write SQL to the primary and results replicate back | changed (newer) | AUR aurora-global-database-write-forwarding.html |
| Global DB limits | No Backtrack; no Aurora Auto Scaling on secondaries; Secrets Manager integration unsupported | no | AUR aurora-global-database.html |
| Backtrack engine | Aurora MySQL only; "Backtrack is not available for Aurora PostgreSQL" | no | AUR AuroraMySQL.Managing.Backtrack.html |
| Backtrack window limit | 72 hours maximum | no | AUR AuroraMySQL.Managing.Backtrack.html |
| Backtrack mechanism | Rewinds the cluster in place without restoring from backup; no new cluster; brief disruption; hourly charge for change records | no | AUR AuroraMySQL.Managing.Backtrack.html |
| Backtrack enablement | Only on clusters created (or restored from snapshot) with Backtrack enabled; cannot be enabled by modifying | no | AUR AuroraMySQL.Managing.Backtrack.html |
| Backtrack not PITR replacement | "Backtracking is not a replacement for backing up your DB cluster" | no | AUR AuroraMySQL.Managing.Backtrack.html |
| Cloning | Copy-on-write at the storage layer; new cluster initially shares same data pages; fast and space-efficient | no | AUR Aurora.Managing.Clone.html |
| Clone limits | Up to 15 copy-on-write clones; the next is a full copy; same Region only; source needs at least one instance | no | AUR Aurora.Managing.Clone.html |
| Clone storage cost | Additional storage allocated only as source or clone changes data | no | AUR Aurora.Managing.Clone.html |
| Clone cross-account / cross-VPC | Cross-account via AWS RAM; cross-VPC allowed if subnets map to same AZs | changed | AUR Aurora.Managing.Clone.html |
| Aurora I/O-Optimized | No separate charge for read/write I/O; best when I/O spending is 25% or more of total Aurora spend | changed (I/O-Optimized launched 2023) | AUR Aurora.Overview.StorageReliability.html |
| Aurora Standard | Pay per 1 million I/O requests; best when I/O spending is under 25% of total | no | AUR Aurora.Overview.StorageReliability.html |
| Switching storage configuration | Standard to I/O-Optimized once per 30 days; no downtime for non-NVMe instances (including serverless); can switch I/O-Optimized to Standard any time | changed | AUR Aurora.Overview.StorageReliability.html |
| Aurora DSQL | Serverless, distributed relational database for transactional workloads; PostgreSQL-compatible (version 16) | changed (newer than 2022) | DSQL what-is-aurora-dsql.html |
| Aurora DSQL availability | 99.99% single-Region and 99.999% multi-Region; active-active; strong consistency | changed | DSQL what-is-aurora-dsql.html |
| Aurora DSQL multi-Region | Peered clusters in one Region set (cross-continent not supported) | changed | DSQL what-is-aurora-dsql.html |
| Aurora PostgreSQL Limitless Database | Automated horizontal scaling for millions of write transactions per second and petabytes of data; shard groups (quota 5 per Region) | changed (newer than 2022) | AUR limitless.html ; AUR CHAP_Limits.html |
| Aurora quotas | 40 DB clusters per Region; 5 IAM roles per cluster; 100 manual cluster snapshots | no | AUR CHAP_Limits.html |

### Amazon DynamoDB

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Max item size | 400 KB, including attribute names (UTF-8 length) and values; confirms facts.md row | no | DDB Constraints.html |
| Binary units | 1 KB = 1024 bytes, 1 MB = 1024 KB | no | DDB Constraints.html |
| Partition key length | 1 byte minimum, 2048 bytes maximum | no | DDB Constraints.html |
| Sort key length | 1 byte minimum, 1024 bytes maximum | no | DDB Constraints.html |
| Number type | Up to 38 digits of precision | no | DDB Constraints.html |
| Nested attribute depth | Up to 32 levels | no | DDB Constraints.html |
| Table size | No practical limit on table size (items or bytes) | no | DDB ServiceQuotas.html |
| Tables per account per Region | Initial quota 2,500 (up to 10,000 via account team) | no (page gives no earlier value) | DDB ServiceQuotas.html |
| Write unit size | 1 write capacity/request unit = one write per second for an item up to 1 KB | no | DDB Constraints.html |
| Read unit size | 1 read capacity/request unit = one strongly consistent read per second, or two eventually consistent reads per second, for an item up to 4 KB | no | DDB Constraints.html |
| Eventually consistent read cost | 0.5 RCU/RRU per 4 KB (half of strongly consistent) | no | DDB Constraints.html ; DDB HowItWorks.ReadConsistency.html |
| Transactional read cost | 2 RCU/RRU per 4 KB item | no | DDB Constraints.html |
| Transactional write cost | 2 WCU/WRU per 1 KB item | no | DDB Constraints.html |
| Rounding | Item size divided by 4 KB (reads) or 1 KB (writes), rounded up to a whole number; examples: 3 KB read = 1 RCU, 512 byte write = 1 WCU | no | DDB provisioned-capacity-mode.html |
| Default read consistency | Eventually consistent for all read operations | no | DDB HowItWorks.ReadConsistency.html |
| Strongly consistent support | Tables and LSIs only; GSIs and streams are always eventually consistent | no | DDB HowItWorks.ReadConsistency.html |
| On-demand mode | Pay per request; "default and recommended throughput option" for most workloads | changed (now default and recommended; page gives no date) | DDB on-demand-capacity-mode.html |
| On-demand scaling | Instantly accommodates up to double the previous peak; exceeding double within 30 minutes can throttle | no | DDB on-demand-capacity-mode.html |
| On-demand new table throughput | New on-demand tables sustain up to 4,000 writes/s and 12,000 reads/s | no | DDB on-demand-capacity-mode.html |
| On-demand max throughput setting | Optional per-table / per-GSI maximum read or write throughput can be configured | changed (newer feature; no date on page) | DDB on-demand-capacity-mode.html |
| Provisioned mode | You specify RCUs and WCUs; billed per hour for provisioned capacity whether used or not | no | DDB provisioned-capacity-mode.html |
| Switch provisioned to on-demand | Up to four times in a 24-hour rolling window | changed (earlier limit and change date not confirmed) | DDB Constraints.html ; DDB bp-switching-capacity-modes.html |
| Switch on-demand to provisioned | At any time | no | DDB Constraints.html |
| Switch duration | Switching to on-demand can take several minutes; throughput stays at prior provisioned levels meanwhile | no | DDB bp-switching-capacity-modes.html |
| Provisioned decreases per day | Start each UTC day with 4 decreases, +1 each hour up to 4 available; up to 27 per day, per table and per GSI | no | DDB ServiceQuotas.html |
| Provisioned increases | Can increase RCU/WCU as often as necessary (not too rapidly) | no | DDB ServiceQuotas.html |
| Default throughput quota per table | 40,000 RCU/WCU (provisioned) or 40,000 RRU/WRU (on-demand); adjustable | no | DDB ServiceQuotas.html |
| Default throughput quota per account | 80,000 RCU and 80,000 WCU, provisioned only; adjustable; no account quota for on-demand | no | DDB ServiceQuotas.html |
| Minimum provisioned throughput | 1 RCU and 1 WCU per table or GSI | no | DDB ServiceQuotas.html |
| Auto scaling | Application Auto Scaling target tracking: set min, max and target utilization; triggers when consumption breaches target for two consecutive minutes | no | DDB provisioned-capacity-mode.html |
| Auto scaling target utilization | AWS recommends 70%; console creates tables with auto scaling enabled by default | no | DDB provisioned-capacity-mode.html |
| Auto scaling defaults on switch | Console recommends target 70%, minimum 5 units, maximum the Region maximum | no | DDB bp-switching-capacity-modes.html |
| Burst capacity | Retains up to five minutes (300 seconds) of unused read and write capacity; details "might change in the future" | no | DDB burst-adaptive-capacity.html |
| Adaptive capacity | Enabled automatically on every table at no additional cost; raises capacity for hot partitions up to partition max and table total | no | DDB burst-adaptive-capacity.html |
| Partition throughput limit | Throttling if one partition receives more than 3,000 read operations or 1,000 write operations; adaptive capacity can give up to 3,000 RCU and 1,000 WCU to a single item key | no | DDB burst-adaptive-capacity.html |
| Primary key | Partition key alone, or partition key plus sort key (composite) | no | DDB Constraints.html |
| Distinct key values | No practical limit on distinct partition key values; no practical limit on sort key values per partition key unless LSIs exist | no | DDB Constraints.html |
| GSI definition | Index with a different partition key and optional sort key than the base table; index key attributes are top-level String, Number or Binary | no | DDB GSI.html |
| GSI consistency | Updated asynchronously ("eventually consistent model"); strongly consistent reads from a GSI not supported | no | DDB GSI.html ; DDB HowItWorks.ReadConsistency.html |
| GSI default quota | 20 global secondary indexes per table (default) | no | DDB ServiceQuotas.html |
| GSI throughput | Own provisioned read and write capacity on provisioned tables; index writes consume the GSI's WCUs; too little GSI write capacity throttles base table writes | no | DDB GSI.html |
| GSI multi-attribute keys | Partition key from up to four attributes and sort key from up to four attributes | changed (newer feature; no date on page) | DDB GSI.html |
| GSI reads | Query and Scan only; GetItem and BatchGetItem cannot be used on an index | no | DDB GSI.html |
| GSI key uniqueness | GSI key values need not be unique; an item missing an index key attribute is not written to the index | no | DDB GSI.html |
| GSI table class | A GSI always uses the same table class as its base table | no | DDB GSI.html |
| GSI storage overhead | 100 bytes of overhead per index item | no | DDB GSI.html |
| LSI definition | Same partition key as the base table, a different sort key (exactly one scalar attribute) | no | DDB LSI.html |
| LSI quota | Up to 5 local secondary indexes per table | no | DDB ServiceQuotas.html ; DDB LSI.html |
| LSI creation time | Created when the table is created (CreateTable LocalSecondaryIndexes parameter) | no | DDB LSI.html |
| LSI consistency | Query can be eventually or strongly consistent (ConsistentRead) | no | DDB LSI.html |
| LSI throughput | Index activity uses the table's provisioned throughput (no separate capacity) | no | DDB LSI.html |
| LSI item collection limit | 10 GB per partition key value (table plus all LSIs); ItemCollectionSizeLimitExceededException if exceeded; limit does not apply to GSIs or tables without LSIs | no | DDB LSI.html |
| Projection types | KEYS_ONLY, INCLUDE, ALL; max 100 user-specified projected attributes across all indexes of a table | no | DDB ServiceQuotas.html ; DDB GSI.html |
| Query | Needs the partition key attribute name and a single value; optional sort key condition; result set limited to 1 MB per call (LastEvaluatedKey to continue) | no | DDB Query.html ; DDB Constraints.html |
| Scan | Reads all data in the table or index; result limited to 1 MB per call; FilterExpression discards data only after it is read | no | DDB Constraints.html ; DDB GSI.html |
| Conditional writes | ConditionExpression on PutItem / UpdateItem / DeleteItem; false condition rejects the write ("The conditional request failed") | no | DDB Expressions.ConditionExpressions.html |
| Prevent overwrite | PutItem with attribute_not_exists(key) fails if an item with that key exists | no | DDB Expressions.ConditionExpressions.html |
| Optimistic locking | Version attribute; update or delete succeeds only if the server-side version equals the client's; mismatch raises ConditionalCheckFailedException; built on conditional writes | no | DDB DynamoDBMapper.OptimisticLocking.html |
| Optimistic locking and global tables | Global tables use last-writer-wins, so version-based locking "does not work as expected" across Regions | no | DDB DynamoDBMapper.OptimisticLocking.html |
| Transactions API | TransactWriteItems and TransactGetItems; ACID, all-or-nothing, synchronous | no | DDB transaction-apis.html |
| Transaction item limit | Up to 100 actions / unique items per transaction; aggregate size 4 MB | changed (earlier limit 25 and change date not confirmed on the pages read) | DDB transaction-apis.html ; DDB Constraints.html |
| Transaction capacity | Two underlying reads or writes per item (prepare plus commit); consumed even if the transaction fails; no extra charge to enable | no | DDB transaction-apis.html |
| Transaction idempotency | ClientRequestToken valid for 10 minutes after the request finishes | no | DDB transaction-apis.html |
| Transaction restrictions | No two actions on the same item; one account and one Region only; not performed using indexes | no | DDB transaction-apis.html ; DDB Constraints.html |
| Transaction isolation | Serializable against single-item reads/writes and other transactions; read-committed for Query, Scan, BatchGetItem as a unit | no | DDB transaction-apis.html |
| Batch limits | BatchGetItem up to 100 items and 16 MB; BatchWriteItem up to 25 Put/Delete requests and 16 MB; batch writes are not atomic | no | DDB Constraints.html ; DDB transaction-apis.html |
| DynamoDB Streams retention | Time-ordered log of item changes stored for up to 24 hours | no | DDB Streams.html |
| Stream view types | KEYS_ONLY, NEW_IMAGE, OLD_IMAGE, NEW_AND_OLD_IMAGES (console: key attributes only, new image, old image, new and old images) | no | DDB Streams.html |
| Stream guarantees | Each stream record appears exactly once; per-item ordering preserved; no record if a write changes nothing | no | DDB Streams.html |
| Stream readers | At most two simultaneous readers per shard; Lambda ParallelizationFactor up to 10 | no | DDB Streams.html |
| Kinesis Data Streams for DynamoDB | Retention up to 1 year; up to 5 consumers per shard (20 with enhanced fan-out); duplicates possible. DynamoDB Streams: 24 hours, 2 consumers per shard, no duplicates | no | DDB streamsmain.html |
| Both streaming models | Can be enabled on the same table | no | DDB streamsmain.html |
| TTL attribute | Number type, Unix epoch seconds | no | DDB TTL.html |
| TTL deletion timing | "Deletes expired items within a few days of their expiration time"; expired items "might be deleted at any time, typically within a few days"; they can still be read or updated until deleted | no | DDB TTL.html |
| TTL cost | Deletion does not consume write throughput in the Region where it expires | no | DDB TTL.html |
| TTL and streams | Deleted items appear in streams as service deletions (not user deletes) | no | DDB TTL.html |
| TTL enable rate | One request to enable or disable TTL per table per hour | no | DDB Constraints.html |
| TTL and global tables | Replicated TTL deletes consume replicated write units in other Regions; TTL not supported on MRSC tables | no | DDB TTL.html ; DDB V2globaltables_HowItWorks.html |
| PITR window | Up to 35 days of recovery points at per-second granularity | no | DDB Point-in-time-recovery.html |
| PITR retention setting | RecoveryPeriodInDays default 35, configurable 1 to 35; shortening has no pricing impact | changed (configurable retention; no date on page) | DDB Point-in-time-recovery.html |
| PITR cross-Region restore | Restored table can be created in a different Region; pay for transfer out and restore | changed (no date on page) | DDB Point-in-time-recovery.html |
| PITR restore target | Restore creates an independent table; for a global table it is not part of the global table | no | DDB Point-in-time-recovery.html |
| PITR pricing basis | Based on size of table and local secondary indexes | no | DDB Point-in-time-recovery.html |
| Export to S3 | Needs PITR enabled; full or incremental; DynamoDB JSON or Amazon Ion; does not consume RCUs; billed by data size | changed (incremental export newer; no date on page) | DDB S3DataExport.HowItWorks.html |
| Global tables versions | Version 2019.11.21 (Current) and Version 2017.11.29 (Legacy); use Current | no | DDB V2globaltables_HowItWorks.html |
| Global tables replication | Multi-active; one replica per Region; write to any replica | no | DDB V2globaltables_HowItWorks.html |
| Global tables SLA | 99.999% availability SLA vs 99.99% for single-Region tables | no | DDB V2globaltables_HowItWorks.html |
| MREC | Multi-Region eventual consistency (default); asynchronous replication typically within a second or less; last-writer-wins conflict resolution | changed (MREC / MRSC naming is newer) | DDB V2globaltables_HowItWorks.html |
| MRSC | Multi-Region strong consistency; synchronous replication to at least one other Region before write returns; strongly consistent reads always latest; RPO of zero | changed (MRSC is newer; no date on page) | DDB V2globaltables_HowItWorks.html |
| MRSC topology | Exactly three Regions: three replicas, or two replicas plus a witness; mode cannot change after creation; table must be empty to convert | changed | DDB V2globaltables_HowItWorks.html |
| MRSC unsupported | TTL, local secondary indexes and transaction operations not supported on MRSC | changed | DDB V2globaltables_HowItWorks.html |
| MRSC quota | 400 MRSC global tables total | changed | DDB ServiceQuotas.html |
| Global tables and transactions | On MREC, transactions are atomic only within the invoking Region | no | DDB V2globaltables_HowItWorks.html |
| Global tables and DAX | Replicated writes bypass DAX, so caches can be stale until TTL expires | no | DDB V2globaltables_HowItWorks.html |
| Add-replica backfill quota | 10 TB per account per destination Region per 24 hours | no | DDB ServiceQuotas.html |
| Table classes | DynamoDB Standard (default) and Standard-Infrequent Access (Standard-IA) | no | DDB WorkingWithTables.tableclasses.html |
| Standard-IA break-even | When storage exceeds 50% of the throughput (reads and writes) cost of a Standard table, Standard-IA can lower total cost | no | DDB WorkingWithTables.tableclasses.html |
| Table class switch limit | No more than two table class updates per table in a 30-day trailing period; no code change; same performance | no | DDB WorkingWithTables.tableclasses.html |
| Encryption at rest | All user data always encrypted at rest (tables, indexes, streams, backups, global tables, DAX) | no | DDB EncryptionAtRest.html |
| Encryption key types | AWS owned key (default, no charge), AWS managed key, customer managed key (KMS charges apply); can switch any time | no | DDB EncryptionAtRest.html |
| Encryption key switch limit | Four key changes per 24 hours per table initially, then one per six-hour window (max 8 per day) | no | DDB Constraints.html |
| Reserved capacity | Provisioned capacity only; blocks of 100 units; page quotes savings up to 54% (1-year) and 77% (3-year); replicated WCUs cannot be reserved | no | https://aws.amazon.com/dynamodb/pricing/provisioned/ |
| On-demand price cut | On-demand throughput prices cut by 50% starting 2024-11-01 (posted 2024-11-14), all Regions | changed 2024-11-01 | https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-dynamo-db-reduces-prices-on-demand-throughput-global-tables/ |
| Global tables price cut | Replicated write price cut 67% (on-demand) and 33% (provisioned) from the same date | changed 2024-11-01 | https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-dynamo-db-reduces-prices-on-demand-throughput-global-tables/ |
| Free tier storage | First 25 GB of Standard storage | no | https://aws.amazon.com/dynamodb/pricing/provisioned/ |

### DAX

| Fact | Value | Changed? | Source |
|---|---|---|---|
| DAX read path | Eventually consistent reads served from cache on a hit; strongly consistent reads passed through to DynamoDB and not cached | no | DDB DAX.concepts.html |
| DAX operations | Reads: GetItem, BatchGetItem, Query, Scan; writes (PutItem, UpdateItem, DeleteItem, BatchWriteItem) are write-through | no | DDB DAX.concepts.html |
| DAX caches | Item cache (GetItem/BatchGetItem) and query cache (Query/Scan result sets by parameter values) | no | DDB DAX.concepts.html |
| DAX default TTL | Item cache TTL default 5 minutes; TTL 0 means refresh only by LRU eviction or write-through; LRU always enabled | no | DDB DAX.concepts.html |
| DAX cluster size | Exactly one primary node plus zero to ten read replica nodes; 50 nodes per account per Region | no | DDB Constraints.html |
| DAX placement | Runs inside a VPC; DAX client sends DynamoDB API calls to the cluster; table management calls go directly to DynamoDB | no | DDB DAX.concepts.html |
| DAX and transactions | TransactWriteItems writes through DAX; TransactGetItems passed through without caching | no | DDB transaction-apis.html |
| DAX read latency | "DAX reduces the response times of eventually consistent read workloads by an order of magnitude from single-digit milliseconds to microseconds"; DynamoDB itself is "single-digit milliseconds" | no | DDB DAX.html |
| DAX use-case wording | "DAX provides access to eventually consistent data from DynamoDB tables, with microsecond latency. A Multi-AZ DAX cluster can serve millions of requests per second"; not ideal for strongly consistent reads, write-intensive or low cache-hit workloads (best when hit rates exceed 90%) | no | DDB DAX.html |

### Amazon ElastiCache

| Fact | Value | Changed? | Source |
|---|---|---|---|
| What it is | Web service to set up, manage and scale a distributed in-memory data store or cache in the cloud | no | EC WhatIs.html |
| Engines | Valkey, Memcached, Redis OSS | changed (Valkey added; page lists it first) | EC WhatIs.html |
| Latency wording | Product page: "Serverless, fully managed caching service delivering microsecond latency performance" and "scale to hundreds of millions of operations per second with microsecond latency" (the WhatIs.html page has no latency wording; the exact phrase "10 times" is not used) | no | https://aws.amazon.com/elasticache/ |
| Two formats | Serverless cache, or node-based cluster | changed (Serverless is newer than 2022) | EC WhatIs.html |
| Serverless | Create a highly available cache "in under a minute"; no instances or nodes to provision; scales automatically on memory, compute and network | changed | EC WhatIs.html |
| Serverless engine versions | Valkey 7.2 and later, Memcached 1.6.22 and later, Redis OSS 7.1 | changed | EC WhatIs.html |
| Serverless connection types | VPC or Public; public endpoints need IAM authentication and TLS 1.3 and Valkey 9.0 or later | changed | EC WhatIs.html |
| Node-based cluster | You choose node type, number of nodes, AZ placement and patch timing | no | EC WhatIs.html |
| Valkey durability | Valkey 9.0+ node-based: optional durability via Multi-AZ transactional log (zero data loss for sync writes); not for cluster mode disabled | changed | EC WhatIs.html ; EC Replication.Redis.Groups.html |
| Cluster mode disabled | One shard: one primary plus 0 to 5 read replicas; asynchronous replication; all in one Region | no | EC Replication.Redis.Groups.html ; EC WhatIs.Components.html |
| Cluster mode enabled | 1 to 500 shards (node groups), each with a primary and 0 to 5 replicas; data partitioned across shards; configuration endpoint | no | EC WhatIs.Components.html |
| Shard limit detail | 500 per cluster for Valkey 7.2+ / Redis OSS 5.0.6+; 250 for older versions; request increase via limit "Nodes per cluster per instance type" | no | EC Replication.Redis.Groups.html |
| Nodes per cluster example | Up to 90 nodes by default (e.g. 90 shards 0 replicas to 15 shards 5 replicas); 500 nodes after increase | no | EC Replication.Redis.Groups.html |
| Cluster mode comparison | Partitioning: disabled no, enabled yes; Multi-AZ optional vs required; add/delete shards: disabled no, enabled yes | no | EC WhatIs.Components.html |
| Multi-AZ with automatic failover | Replica with least replication lag promoted; "writes can resume ... typically just a few seconds"; DNS name of promoted replica propagated so primary endpoint unchanged | no | EC AutoFailover.html |
| Multi-AZ requirement | At least one replica in a different AZ than the primary; only on clusters with more than one node per shard | no | EC AutoFailover.html |
| Multi-AZ default | Enabled by default for cluster mode enabled (automatic failover required); recommended for cluster mode disabled | no | EC AutoFailover.html |
| Failover data loss | Replication is asynchronous, so a small amount of data can be lost on failover (not for durability-enabled clusters) | no | EC AutoFailover.html |
| Multi-AZ vs AOF | Multi-AZ and append-only file are mutually exclusive (Redis OSS) | no | EC AutoFailover.html |
| Without Multi-AZ | Failed primary is replaced by a new node; with no replicas the new primary starts empty and data is lost unless restored from snapshot | no | EC AutoFailover.html |
| Global datastore | Cross-Region replication (read replica clusters in other Regions) for Valkey/Redis OSS | no | EC WhatIs.Components.html |
| Backups | Snapshot of Valkey, Redis OSS or Serverless Memcached caches; written to Amazon S3; restore into a new cache | changed (Serverless Memcached backups newer; node-based Memcached has none) | EC backups.html |
| Memcached backups | Not available for node-based Memcached; available only for Memcached serverless | changed | EC backups.html ; EC SelectEngine.html |
| Backup retention | Maximum 35 days; retention limit 0 disables automatic backups; daily automatic backup with a configurable start time | no | EC backups-automatic.html |
| Manual backup limits | Up to 24 manual backups per serverless cache per 24 hours; 20 per node for node-based Valkey/Redis OSS | no | EC backups.html |
| Backup performance | Serverless backups have no performance impact; node-based can; back up from a replica; set reserved-memory-percent | no | EC backups.html |
| Encryption at rest | Encrypts disk during sync/backup/swap and backups in S3; enabled only at creation (existing cluster: backup, restore into new encrypted group); always on for serverless | no | EC at-rest-encryption.html |
| At-rest default | For Valkey the AtRestEncryptionEnabled parameter defaults to true | changed | EC at-rest-encryption.html |
| At-rest keys | Service-managed key (default) or symmetric customer managed KMS key | no | EC at-rest-encryption.html |
| Encryption in transit | TLS between clients and nodes and between nodes; always on for serverless; node-based: TransitEncryptionEnabled | no | EC in-transit-encryption.html |
| In transit on existing clusters | Modifying the setting on an existing replication group supported on Valkey 7.2+ and Redis OSS 7+ | changed | EC in-transit-encryption.html |
| Memcached encryption | In transit and at rest only from Memcached 1.6.12; at rest only on serverless Memcached; in transit enabled only at creation | changed | EC in-transit-encryption.html ; EC at-rest-encryption.html |
| mTLS | Not supported | no | EC in-transit-encryption.html |
| Minimum TLS | From 2026-04-28 AWS raises minimum TLS to 1.2 on Valkey 7.2+ and Redis OSS 6+ | changed 2026-04-28 | EC in-transit-encryption.html |
| Authentication | IAM authentication, Valkey/Redis OSS AUTH command, and Role-Based Access Control (RBAC) for authorization | changed (IAM auth newer) | EC encryption.html ; EC auth-redis.html |
| Redis OSS RBAC | Introduced with ElastiCache for Redis OSS 6.0 (Enhanced) | no | EC SelectEngine.html |
| Memcached model | Simplest model; multi-threaded; scale out and in by adding/removing nodes; no replication, no persistence/backups (node-based), no Multi-AZ failover | no | EC SelectEngine.html |
| Memcached cluster size | 1 to 60 nodes per cluster; up to 300 nodes per customer per Region | no | EC WhatIs.Components.html |
| Memcached partitioning | Data is partitioned across nodes; client should use consistent hashing | no | EC WhatIs.Components.html |
| Memcached Auto Discovery | Client connects to the configuration endpoint and learns all node endpoints, even as nodes are added or removed; not available for Valkey/Redis OSS | no | EC AutoDiscovery.html |
| Valkey/Redis vs Memcached | Valkey/Redis: replication, automatic failover, backup/restore, pub/sub, sorted sets, complex data types, geospatial; Memcached: multi-threaded, simple data types | no | EC SelectEngine.html |
| Valkey/Redis single-threaded | Comparison table lists multi-threaded "No" for Valkey/Redis OSS and "Yes" for Memcached | no | EC SelectEngine.html |
| Data tiering | Memory plus SSD on r6gd node type (engine 6.2+) | no | EC SelectEngine.html |
| Valkey features by version | 7.2 Functions and sharded pub/sub; 8.0 memory efficiency; 8.1 Bloom filters; 8.2 vector search; 9.0 full-text search, hash field expiration, durability | changed | EC SelectEngine.html |
| Lazy loading (cache-aside) | App checks cache first; on miss reads database then writes cache. Pro: only requested data cached, node failure not fatal. Con: miss penalty (three trips), stale data | no | EC Strategies.html |
| Write-through | Update cache whenever the database is written. Pro: cache never stale. Con: write penalty (two trips), missing data on new node, cache churn | no | EC Strategies.html |
| Adding TTL | TTL in seconds per key; expired key is treated as not found; combine with lazy loading or write-through to limit stale data and cache clutter | no | EC Strategies.html |
| Combination | "Lazy loading with write-through" and TTL give advantages of each | no | EC Strategies.html |
| Read replicas | Reading from replicas can significantly improve performance | no | EC Strategies.html |
| MemoryDB | Durable in-memory database, Valkey and Redis OSS compatible; microsecond reads and single-digit millisecond writes; data stored durably across multiple AZs via Multi-AZ transactional log; usable as primary database without a separate cache | no | MDB what-is-memorydb.html |
| MemoryDB vs ElastiCache | MemoryDB: durable primary database; ElastiCache: caching in front of another primary database | no | MDB related-services-choose-between-memorydb-and-redis.html |

### Purpose-built databases

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Neptune | Fully managed graph database; Gremlin, openCypher, SPARQL; recommendation engines, fraud detection, knowledge graphs | no | NEP intro.html |
| Neptune architecture | One primary plus up to 15 Neptune Replicas on the same cluster volume; storage across multiple AZs; designed for greater than 99.99 percent availability | no | NEP intro.html |
| Neptune Analytics | Separate analytics engine to analyze graph data in memory | changed (newer) | NEP intro.html |
| DocumentDB | MongoDB-compatible fully managed document database | no | DOC what-is.html |
| DocumentDB storage | Six copies across three AZs; grows in 10 GB increments to a maximum of 256 TiB for engine 8.0+ (128 TiB earlier) | changed (256 TiB newer) | DOC what-is.html |
| DocumentDB cluster | 0 to 16 instances (primary plus up to 15 replicas), reader endpoint, replica lag often single-digit milliseconds | no | DOC what-is.html |
| DocumentDB backups | PITR to any second within retention, up to the last 5 minutes; retention up to 35 days; stored in S3 | no | DOC what-is.html |
| DocumentDB elastic clusters | Millions of reads/writes per second and petabytes of storage; Serverless instance class and I/O-optimized storage configuration exist | changed | DOC what-is.html |
| Keyspaces | Serverless, managed Apache Cassandra-compatible database using CQL | no | KS what-is-keyspaces.html |
| Timestream for LiveAnalytics | Purpose-built time series database; memory store for recent data, magnetic store for history; serverless; at least 3 AZs | no | TS what-is-timestream.html |
| Timestream LiveAnalytics availability | AWS closed new customer access effective 2025-06-20; existing workloads unaffected; evaluate Timestream for InfluxDB instead | changed 2025-06-20 | TS AmazonTimestreamForLiveAnalytics-availability-change.html |
| Timestream for InfluxDB | Recommended alternative with single-digit millisecond query response | changed | TS what-is-timestream.html |
| OpenSearch Service | Managed OpenSearch (and legacy Elasticsearch OSS up to 7.10); search, log analytics, real-time monitoring, clickstream | no | OS what-is.html |
| OpenSearch scale | Up to 1002 data nodes and up to 25 PB attached storage; UltraWarm and cold storage; Multi-AZ across two or three AZs | changed | OS what-is.html |
| OpenSearch Extended Support | Charges apply when domain runs a version past standard support (e.g. standard support for Elasticsearch/OpenSearch older versions ends 2025-11-07) | changed | OS what-is.html |
| QLDB | Amazon QLDB retired: end of support / full shutdown 2025-07-31 (listed in Services in Full Shutdown) | changed 2025-07-31 | GR full_shutdown_services.html |
| Aurora Serverless v1 | retired: end of life 2025-03-31; no new v1 clusters from 2025-01-08; remaining clusters auto-migrated (v1 to v2) or converted to provisioned (medium confidence: search-result excerpt) | changed 2025-03-31 | AUR aurora-serverless-v2.upgrade.html |
| Aurora Serverless v2 renamed | AWS blog notice (April 2026) says Aurora Serverless v2 renamed "Aurora serverless"; current docs use "Aurora serverless" | changed 2026 | AUR aurora-serverless-v2.html ; https://aws.amazon.com/blogs/database/upgrade-from-amazon-aurora-serverless-v1-to-v2-with-minimal-downtime/ |

## Prices used in drills (illustrative, us-east-1)

Mirrors `_harness/awslib/prices.toml` `[vpc]`. Prices are illustrative and move; the lab and drills never depend on a live price.

| Fact | Value | Source |
|---|---|---|
| NAT gateway per hour | 0.045 USD (illustrative; the price page example is us-east-2, us-east-1 not seen) | aws.amazon.com/vpc/pricing/ |
| NAT gateway per GB processed | 0.045 USD (illustrative; same caveat) | aws.amazon.com/vpc/pricing/ |
| Gateway endpoint (S3, DynamoDB) per GB | 0.00 USD, no hourly charge | docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html |
| Interface endpoint per hour per AZ | 0.01 USD (illustrative; the page example is per ENI-hour) | aws.amazon.com/privatelink/pricing/ |
| Interface endpoint per GB | 0.01 USD (first 1 PB per month) | aws.amazon.com/privatelink/pricing/ |
| Transit Gateway attachment per hour | 0.05 USD | aws.amazon.com/transit-gateway/pricing/ |
| Transit Gateway per GB processed | 0.02 USD | aws.amazon.com/transit-gateway/pricing/ |
| Site-to-Site VPN connection per hour | 0.05 USD | aws.amazon.com/vpn/pricing/ |
| Public IPv4 address per hour | 0.005 USD, in use or idle | aws.amazon.com/vpc/pricing/ |
| VPC peering data, same AZ | free | docs.aws.amazon.com/vpc/latest/peering/what-is-vpc-peering.html |
| VPC peering data, cross-AZ same Region | 0.01 USD per GB each way | aws.amazon.com/vpc/pricing/ |
| IGW, egress-only IGW, security groups, NACLs | no charge | docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html |
| Data transfer in from the internet | 0.00 USD per GB | prices.toml `[data_transfer]` (earlier plan) |
| Data transfer out to the internet | 0.09 USD per GB (first 10 TB per month) | prices.toml `[data_transfer]` |
| Data transfer between AZs | 0.01 USD per GB charged out and in | prices.toml `[data_transfer]` |
| Data transfer between Regions | 0.02 USD per GB, sender pays | prices.toml `[data_transfer]` |
| S3 Standard storage | 0.023 USD per GB-month first 50 TB · 0.022 next 450 TB · 0.021 over 500 TB | prices.toml `[[s3_standard_tiers]]` |


### EC2 and load balancers (week 03)

Mirrors `_harness/awslib/prices.toml` `[ec2]` (us-east-1, Linux, On-Demand, shared tenancy; research docs/research/2026-10-11-compute-facts.md section 8). Illustrative. The three discounts are course examples, not AWS prices.

| Fact | Value | Source |
|---|---|---|
| t4g.micro per hour | 0.0084 USD (2 vCPU, 1 GiB) | AWS pricing JSON (awsstatic, N. Virginia, Linux) |
| t4g.small per hour | 0.0168 USD (2 vCPU, 2 GiB) | same |
| t4g.medium per hour | 0.0336 USD (2 vCPU, 4 GiB) | same |
| t3.micro per hour | 0.0104 USD (2 vCPU, 1 GiB, 10 percent baseline) | same; aws.amazon.com/ec2/instance-types/t3/ |
| m7g.large per hour | 0.0816 USD (2 vCPU, 8 GiB) | same |
| m7i.large per hour | 0.1008 USD (2 vCPU, 8 GiB) | same |
| c7g.large per hour | 0.0725 USD (2 vCPU, 4 GiB) | same |
| c7i.large per hour | 0.08925 USD (2 vCPU, 4 GiB) | same |
| r7g.large per hour | 0.1071 USD (2 vCPU, 16 GiB) | same |
| m7g.xlarge per hour | 0.1632 USD (4 vCPU, 16 GiB; exactly 2x m7g.large) | same |
| Compute Savings Plan discount (course example) | 31 percent = AWS's average 1-year Convertible RI discount, which the Savings Plans FAQ compares Compute Savings Plans to ("up to 66% (just like Convertible RIs)"); AWS maximum up to 66 percent | aws.amazon.com/ec2/pricing/reserved-instances/; aws.amazon.com/savingsplans/faqs/ |
| Standard RI discount (course example) | 40 percent = AWS's average 1-year Standard RI discount; AWS maximum up to 72 percent | aws.amazon.com/ec2/pricing/reserved-instances/ |
| Spot discount (course example) | 70 percent; AWS says "up to 90%" vs On-Demand | aws.amazon.com/ec2/pricing/ |
| ALB per hour | 0.0225 USD (from the pricing-page example, N. Virginia) | aws.amazon.com/elasticloadbalancing/pricing/ |
| ALB per LCU-hour | 0.008 USD | aws.amazon.com/elasticloadbalancing/pricing/ |
| ALB LCU dimensions | new connections 25/s · active connections 3,000/min (1,500 with mTLS) · 1 GB/hour processed (0.4 GB for Lambda) · rule evaluations 1,000/s (first 10 rules free) · highest dimension is billed | aws.amazon.com/elasticloadbalancing/pricing/ |
| NLB per hour | 0.0225 USD | aws.amazon.com/elasticloadbalancing/pricing/ |
| NLB per NLCU-hour | 0.006 USD | aws.amazon.com/elasticloadbalancing/pricing/ |
| NLCU dimensions | TCP: 800 new conn/s, 100,000 active, 1 GB/h · UDP: 400 new flows/s, 50,000 active, 1 GB/h · TLS: 50 new conn/s, 3,000 active, 1 GB/h | aws.amazon.com/elasticloadbalancing/pricing/ |
| GWLB | 0.0125 USD per hour plus 0.004 USD per GLCU-hour (600 new conn/s, 60,000 active/min, 1 GB/hour) | aws.amazon.com/elasticloadbalancing/pricing/ |
| CLB (price example) | 0.025 USD per hour plus 0.008 USD per GB processed | aws.amazon.com/elasticloadbalancing/pricing/ |
| ELB other charges | data transfer and public IPv4 billed separately | aws.amazon.com/elasticloadbalancing/pricing/ |
| Week 03 lab cost | about 0.10 USD for one ALB and two t4g.micro instances, at most about 90 minutes (ALB 0.0225/hour + LCUs, instances 0.0084/hour each, public IPv4 0.005/hour each) | computed from the rows above and the public IPv4 row |

### Storage (week 04)

Illustrative us-east-1 USD from the official S3 and EFS price files published 2026-09-28 (research docs/research/2026-10-12-storage-facts.md section 12); `_harness/awslib/prices.toml` `[storage]` carries the same values. Prices move; the lab and drills never depend on a live price. Rows marked medium confidence come from worked examples or a page that names no Region.

| Fact | Value | Source |
|---|---|---|
| S3 Standard storage | 0.023 per GB-month first 50 TB; 0.022 next 450 TB; 0.021 over 500 TB | S3 price file |
| S3 Intelligent-Tiering Frequent Access | 0.023 per GB-month (first 50 TB) | S3 price file |
| S3 Intelligent-Tiering Infrequent Access | 0.0125 per GB-month | S3 price file |
| S3 Intelligent-Tiering Archive Instant Access | 0.004 per GB-month | S3 price file |
| S3 Intelligent-Tiering Archive Access | 0.0036 per GB-month | S3 price file |
| S3 Intelligent-Tiering Deep Archive Access | 0.00099 per GB-month | S3 price file |
| S3 Intelligent-Tiering monitoring fee | 0.0025 per 1,000 objects per month | S3 price file |
| S3 Standard-IA storage | 0.0125 per GB-month | S3 price file |
| S3 One Zone-IA storage | 0.01 per GB-month | S3 price file |
| S3 Glacier Instant Retrieval storage | 0.004 per GB-month | S3 price file |
| S3 Glacier Flexible Retrieval storage | 0.0036 per GB-month (usage type TimedStorage-GlacierByteHrs, "Amazon Glacier") | S3 price file |
| S3 Glacier Deep Archive storage | 0.00099 per GB-month ("or $1 per TB-month") (medium confidence: the official Glacier page prints it without naming a Region and the us-east-1 price file has no Deep Archive storage row; the Intelligent-Tiering Deep Archive Access tier is 0.00099 there) | https://aws.amazon.com/s3/storage-classes/glacier/ |
| S3 Express One Zone storage | 0.11 per GB-month | S3 price file |
| S3 Reduced Redundancy storage | 0.024 per GB-month first 1 TB (legacy) | S3 price file |
| Standard-IA retrieval | 0.01 per GB | S3 price file |
| One Zone-IA retrieval | 0.01 per GB | S3 price file |
| Glacier Instant Retrieval retrieval | 0.03 per GB | S3 price file |
| Glacier Flexible Standard retrieval | 0.01 per GB | S3 price file |
| Glacier Flexible Bulk retrieval | 0.00 per GB (free) | S3 price file |
| Glacier Flexible Expedited retrieval | 0.03 per GB plus 0.01 per Expedited request | S3 price file |
| Deep Archive Standard retrieval | 0.02 per GB | S3 price file |
| Deep Archive Bulk retrieval | 0.0025 per GB | S3 price file |
| Express One Zone retrieval | 0.0006 per GB | S3 price file |
| Standard PUT/COPY/POST/LIST | 0.005 per 1,000 requests | S3 price file |
| Standard GET and other | 0.0004 per 1,000 requests (0.004 per 10,000) | S3 price file |
| Intelligent-Tiering requests | PUT/COPY/POST/LIST 0.005 per 1,000; GET 0.0004 per 1,000 | S3 price file |
| Standard-IA requests | PUT/COPY/POST/LIST 0.01 per 1,000; GET 0.001 per 1,000 (0.01 per 10,000) | S3 price file |
| One Zone-IA requests | PUT/COPY/POST/LIST 0.01 per 1,000; GET 0.001 per 1,000 | S3 price file |
| Glacier Instant Retrieval requests | PUT/COPY/POST/LIST 0.02 per 1,000; GET 0.01 per 1,000 (0.1 per 10,000) | S3 price file |
| Glacier Flexible requests | PutObject/CopyObject 0.03 per 1,000; GET and other 0.0004 per 1,000; lifecycle requests 0.03 per 1,000 | S3 price file |
| Deep Archive requests | Lifecycle requests 0.05 per 1,000; GET and other 0.0004 per 1,000 | S3 price file |
| Express One Zone requests | PUT/COPY/POST/LIST 0.00113 per 1,000; GET 0.00003 per 1,000 | S3 price file |
| Lifecycle transition requests | To Standard-IA, One Zone-IA or Intelligent-Tiering 0.01 per 1,000; to Glacier Instant Retrieval 0.02 per 1,000 | S3 price file |
| Early delete (IA) | Prorated storage rate: Standard-IA 0.0125, One Zone-IA 0.01 per GB-month | S3 price file |
| Early delete (Glacier) | Glacier Instant Retrieval 0.004; Glacier Flexible 0.0036 per GB-month prorated | S3 price file |
| S3 Select (retired for new customers) scanned / returned | Standard: 0.002 per GB scanned, 0.0007 per GB returned (existing customers only) | S3 price file |
| Data transfer out to internet (first tier) | 0.09 per GB for first 10 TB per month (beyond the global free tier); 0.085 next 40 TB; 0.07 next 100 TB; 0.05 over 150 TB | DT price file |
| EBS gp3 storage | 0.08 per GB-month (medium confidence: from a worked example on the pricing page, Region not named) | EBS price page (example 1; region not named) |
| EBS gp3 extra IOPS | 0.005 per provisioned IOPS-month above 3,000 (medium confidence: from a worked example on the pricing page, Region not named) | EBS price page (example 1) |
| EBS gp3 extra throughput | 0.06 per provisioned MB/s-month above 125 (medium confidence: from a worked example on the pricing page, Region not named) | EBS price page (example 1) |
| EBS gp2 storage | 0.10 per GB-month (medium confidence: from a worked example on the pricing page, Region not named) | EBS price page (example 2) |
| EBS io2 storage | 0.125 per GB-month (medium confidence: from a worked example on the pricing page, Region not named) | EBS price page (example 3) |
| EBS io2 IOPS tiers | 0.065 per IOPS-month first 32,000; 0.046 for 32,001 to 64,000 (higher tier not used) (medium confidence: from a worked example on the pricing page, Region not named) | EBS price page (example 3) |
| EBS io1 | 0.125 per GB-month and 0.065 per provisioned IOPS-month (medium confidence: from a worked example on the pricing page, Region not named) | EBS price page (example 4) |
| EBS st1 | 0.045 per GB-month (medium confidence: from a worked example on the pricing page, Region not named) | EBS price page (example 5) |
| EBS sc1 | 0.015 per GB-month (medium confidence: from a worked example on the pricing page, Region not named) | EBS price page (example 6) |
| EBS snapshot standard | 0.05 per GB-month (medium confidence: from a worked example on the pricing page, Region not named) | EBS price page (example 10) |
| EBS snapshot archive | 0.0125 per GB-month (75 percent lower than standard, derived) (medium confidence: from a worked example on the pricing page, Region not named) | EBS price page (example 10) |
| EBS snapshot archive restore | 0.03 per GB (medium confidence: from a worked example on the pricing page, Region not named) | EBS price page (example 10) |
| EBS fast snapshot restore | 0.75 per DSU-hour per snapshot per AZ (US East N. Virginia) (medium confidence: from a worked example on the pricing page, Region not named) (the user guide gives the same 0.75 example) | EBS price page (example 8) ; EBS ebs-fast-snapshot-restore.html |
| EFS Standard (Regional) | 0.30 per GB-month | EFS price file |
| EFS Infrequent Access (Regional) | 0.025 per GB-month (0.016 per GB-month when the file system uses Elastic throughput) | EFS price file |
| EFS Archive (Regional) | 0.008 per GB-month | EFS price file |
| EFS One Zone Standard | 0.16 per GB-month | EFS price file |
| EFS One Zone-IA | 0.0133 per GB-month | EFS price file |
| EFS IA data access | 0.01 per GB reads and 0.01 per GB writes | EFS price file |
| EFS Archive data access | 0.03 per GB reads and 0.03 per GB writes/tiering | EFS price file |
| EFS Elastic throughput | 0.03 per GB read and 0.06 per GB written | EFS price file |
| EFS Provisioned throughput | 6.00 per MiBps-month | EFS price file |

### Databases and caching (week 05)

Mirrors `_harness/awslib/prices.toml` `[database]`. All prices come from the public AWS Price List files (pricing.us-east-1.amazonaws.com offers, us-east-1, On-Demand; research docs/research/2026-10-12-database-facts.md section 6), because the aws.amazon.com pricing pages did not render rate tables. Price List dates: RDS and Aurora 2026-10-06, ElastiCache 2026-09-14, DynamoDB 2026-09-11, DAX 2026-10-09. PL-RDS / PL-EC / PL-DDB / PL-DAX = the AmazonRDS / AmazonElastiCache / AmazonDynamoDB / AmazonDAX offer file. Illustrative: prices move, may differ by Region or term, and the drills never depend on a live price. The `[database]` values are the DynamoDB on-demand and provisioned, storage and PITR rows; RDS PostgreSQL db.t4g.micro and db.m7g.large Single-AZ and Multi-AZ; RDS gp3 storage; Aurora Serverless v2 Standard ACU-hour; RDS Proxy per vCPU-hour; ElastiCache Valkey cache.t4g.micro and cache.m7g.large node-hours.

| Fact | Value | Source |
|---|---|---|
| RDS PostgreSQL db.t4g.micro Single-AZ | 0.016 USD per hour | PL-RDS |
| RDS PostgreSQL db.t4g.micro Multi-AZ | 0.032 USD per hour (2x single) | PL-RDS |
| RDS PostgreSQL db.m7g.large Single-AZ | 0.168 USD per hour | PL-RDS |
| RDS PostgreSQL db.m7g.large Multi-AZ | 0.337 USD per hour (about 2x single) | PL-RDS |
| RDS PostgreSQL db.r7g.large Single-AZ / Multi-AZ | 0.239 / 0.478 USD per hour | PL-RDS |
| RDS gp3 storage (PostgreSQL) Single-AZ | 0.115 USD per GB-month | PL-RDS |
| RDS gp3 storage Multi-AZ DB instance | 0.23 USD per GB-month (2x) | PL-RDS |
| RDS gp3 storage Multi-AZ DB cluster (readable standbys) | 0.345 USD per GB-month (3x) | PL-RDS |
| RDS gp3 extra IOPS / throughput (Single-AZ) | 0.02 USD per IOPS-month; 0.08 USD per MiBps-month | PL-RDS |
| RDS io2 storage Single-AZ / Multi-AZ | 0.125 / 0.25 USD per GB-month; IOPS 0.10 / 0.20 USD per IOPS-month | PL-RDS |
| RDS io1 storage Single-AZ / Multi-AZ (PostgreSQL) | 0.125 / 0.25 USD per GB-month; IOPS 0.10 / 0.20 USD per IOPS-month | PL-RDS |
| RDS gp2 storage (PostgreSQL) Single-AZ / Multi-AZ | 0.115 / 0.23 USD per GB-month | PL-RDS |
| RDS backup storage beyond free allocation | 0.095 USD per GB-month (PostgreSQL) | PL-RDS |
| RDS Proxy | 0.015 USD per vCPU-hour of the associated RDS PostgreSQL instance; Aurora Serverless v2 0.015 USD per ACU-hour | PL-RDS |
| Aurora PostgreSQL db.r7g.large, Standard | 0.276 USD per hour | PL-RDS |
| Aurora PostgreSQL db.r7g.large, I/O-Optimized | 0.359 USD per hour | PL-RDS |
| Aurora storage, Standard | 0.10 USD per GB-month consumed | PL-RDS |
| Aurora I/O, Standard | 0.20 USD per 1 million I/O requests | PL-RDS |
| Aurora storage, I/O-Optimized | 0.225 USD per GB-month; no I/O charges | PL-RDS |
| Aurora Serverless v2 (PostgreSQL), Standard | 0.12 USD per ACU-hour | PL-RDS |
| Aurora Serverless v2 (PostgreSQL), I/O-Optimized | 0.16 USD per ACU-hour | PL-RDS |
| Aurora backup storage beyond free allocation | 0.021 USD per GB-month (Aurora PostgreSQL) | PL-RDS |
| Aurora Global Database replicated write I/O | 0.20 USD per 1 million replicated write I/O requests | PL-RDS |
| DynamoDB on-demand write | 0.625 USD per million write request units (changed 2024-11-01 (50% cut)) | PL-DDB |
| DynamoDB on-demand read | 0.125 USD per million read request units (changed 2024-11-01 (50% cut)) | PL-DDB |
| DynamoDB provisioned write | 0.00065 USD per WCU-hour (first 25 WCU free) | PL-DDB |
| DynamoDB provisioned read | 0.00013 USD per RCU-hour (first 25 RCU free) | PL-DDB |
| DynamoDB storage | 0.25 USD per GB-month after first 25 GB free (Standard); 0.10 USD per GB-month (Standard-IA) | PL-DDB |
| DynamoDB Standard-IA throughput | On-demand 0.78 USD per million WRU and 0.155 USD per million RRU; provisioned 0.00081 per WCU-hour and 0.00016 per RCU-hour | PL-DDB |
| DynamoDB PITR | 0.20 USD per GB-month | PL-DDB |
| DynamoDB on-demand backup | 0.10 USD per GB-month; restore 0.15 USD per GB | PL-DDB |
| DynamoDB export / import | Export 0.10 USD per GB; incremental export 0.10 USD per GB; import 0.15 USD per GB | PL-DDB |
| DynamoDB global tables replicated writes | 0.625 USD per million replicated WRU (on-demand); 0.00065 USD per replicated WCU-hour (provisioned) (changed 2024-11-01) | PL-DDB |
| DynamoDB Streams reads | 2.5 million read request units free per month, then 0.0000002 USD per unit | PL-DDB |
| DAX dax.t3.small | 0.04 USD per node-hour | PL-DAX |
| ElastiCache cache.t4g.micro | Valkey 0.0128; Redis OSS 0.016; Memcached 0.016 USD per node-hour (changed (Valkey priced lower)) | PL-EC |
| ElastiCache cache.m7g.large | Valkey 0.1264; Redis OSS 0.158; Memcached 0.158 USD per node-hour (changed) | PL-EC |
| Valkey vs Redis OSS node discount | Valkey node price is 80% of Redis OSS (0.1264 / 0.158 = 0.8; derived) (changed) | PL-EC |
| ElastiCache Serverless data storage | Valkey 0.084 USD per GB-hour; Redis OSS and Memcached 0.125 USD per GB-hour (changed) | PL-EC |
| ElastiCache Serverless ECPUs | Valkey 0.0023 USD per million ECPUs; Redis OSS and Memcached 0.0034 USD per million (changed) | PL-EC |
| ElastiCache Serverless minimum metered storage | 100 MB for Valkey; 1 GB for Redis OSS and Memcached (from pricing page worked examples) (changed) | https://aws.amazon.com/elasticache/pricing/ |
| ElastiCache snapshot storage | 0.085 USD per GB-month beyond free allocation | PL-EC |

## Retired or closed services (spec §7)

Rule 1 — retired; mention only on a line that contains the word "retired"; never in a question:

| Service | Status | Source |
|---|---|---|
| Amazon QLDB | retired (shut down 2025-07-31) | docs.aws.amazon.com/general/latest/gr/full_shutdown_services.html |
| Amazon Elastic Transcoder | retired (2025-11-13) | same |
| AWS Data Pipeline | retired for new customers (maintenance) | docs.aws.amazon.com/datapipeline/latest/DeveloperGuide/what-is-datapipeline.html |
| AWS Proton | retired (end of support 2026-10-07) | docs.aws.amazon.com/proton/latest/userguide/proton-end-of-support.html |
| Amazon Pinpoint | retired (sunset, ends 2026-10-30) | docs.aws.amazon.com/pinpoint/latest/userguide/migrate.html |
| AWS OpsWorks | retired (2024-05-01) | full_shutdown_services |
| EC2-Classic | retired (2022-08-15) | aws.amazon.com/blogs/aws/ec2-classic-is-retiring-heres-how-to-prepare/ |
| Aurora Serverless v1 | retired (end of life 2025-03-31) | docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2.upgrade.html |
| Timestream for LiveAnalytics | retired for new customers (closed to new customers 2025-06-20; existing workloads unaffected; Timestream for InfluxDB is the alternative) | docs.aws.amazon.com/timestream/latest/developerguide/AmazonTimestreamForLiveAnalytics-availability-change.html |
| Kinesis Data Analytics for SQL | retired (2026-01-27) | full_shutdown_services |
| AWS WAF Classic · Amazon Inspector Classic | retired (2026-10-07 · 2026-05-20) | sunset / full_shutdown_services |
| AWS Snowmobile · AWS Snowcone | retired (2024-03-14 · 2024-11-12) | full_shutdown_services; aws.amazon.com/blogs/storage/aws-snow-device-updates/ |
| Launch configurations | retired for new accounts (see above) | launch-configurations doc |
| S3 Select · S3 Object Lambda | retired for new customers (maintenance 2024-07-25 · 2025-11-07) | AWS storage blog; S3 docs |
| Original vault-based Amazon Glacier service | retired for new customers (2025-12-15); use the S3 Glacier storage classes | docs.aws.amazon.com/AmazonS3/latest/userguide/glacier-storage-classes.html |
| AWS Cloud9 · AWS App Mesh | retired for new customers (2024-07-25) · retired (2026-09-30) | AWS DevOps / containers blogs |

Rule 2 — closed to new customers but still in the exam guide; teach as the exam answer with this status note; questions using it as the answer carry `legacy = true`:

| Service | 2026 status | Successor | Source |
|---|---|---|---|
| AWS Snowball Edge (Snow Family) | closed to new customers since 2025-11-07 | AWS DataSync (online) · AWS Data Transfer Terminal (physical) | docs.aws.amazon.com/snowball/latest/developer-guide/snowball-edge-availability-change.html |
| AWS Application Discovery Service | closed to new customers 2025-11-07 | AWS Transform | docs.aws.amazon.com/application-discovery/latest/userguide/application-discovery-service-availability-change.html |
| AWS Migration Hub | maintenance (2025-11-07) | AWS Transform | docs.aws.amazon.com/migrationhub/latest/ug/migrationhub-availability-change.html |
| Simple AD (AWS Directory Service) | maintenance — closed to new customers (2026-06-30) | AWS Managed Microsoft AD | docs.aws.amazon.com/general/latest/gr/maintenance_services.html |

## Account plans (for the optional labs)

| Fact | Source |
|---|---|
| New accounts pick a Free plan or a Paid plan; both get 100 USD credits plus up to 100 USD more for activities | docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html |
| The Free plan ends after 6 months or when credits run out; the account then closes (90 days to upgrade before deletion) | same |
| A Free-plan account is upgraded to Paid automatically if it joins AWS Organizations or sets up a Control Tower landing zone | same |
| Budgets templates: Zero spend budget · Monthly cost budget | docs.aws.amazon.com/cost-management/latest/userguide/budget-templates.html |
| Billing alarm: enable "Receive CloudWatch Billing Alerts", then alarm on EstimatedCharges in us-east-1 | docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/monitor_estimated_charges_with_cloudwatch.html |
| Do not promise the pre-2025 "12-month free tier" (750 h of t2/t3.micro) — it applies only to older accounts | free-tier-plans doc |

## Free services used in the course

| Service | Charge | Source |
|---|---|---|
| IAM (users, groups, roles, policies) and STS | no additional charge | aws.amazon.com/iam/pricing/ |
| IAM Identity Center | no additional charge | aws.amazon.com/iam/identity-center/faqs/ |
| AWS Resource Access Manager | no additional charge | aws.amazon.com/ram/pricing/ |
| AWS Organizations (and consolidated billing) | no additional charge | aws.amazon.com/organizations/pricing/ |

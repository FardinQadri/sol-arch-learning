# Week 03 compute and scaling facts (collected 2026-10-11)

All rows below were read from official AWS pages on 2026-10-11. "Changed?" is "no" unless a change after 2022 is documented. Prices are illustrative; always re-check.

URL key (base paths):
- ITN = https://docs.aws.amazon.com/ec2/latest/instancetypes/
- EC2 = https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/
- ASG = https://docs.aws.amazon.com/autoscaling/ec2/userguide/
- ALB = https://docs.aws.amazon.com/elasticloadbalancing/latest/application/
- NLB = https://docs.aws.amazon.com/elasticloadbalancing/latest/network/
- GWLB = https://docs.aws.amazon.com/elasticloadbalancing/latest/gateway/
- CLB = https://docs.aws.amazon.com/elasticloadbalancing/latest/classic/
- ELB = https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/
- SP = https://docs.aws.amazon.com/savingsplans/latest/userguide/

## 1. EC2 instance types

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
| Unlimited surplus rate example | CloudWatch / price page mention T4g Linux unlimited at 0.04 USD per vCPU-hour | no | https://aws.amazon.com/ec2/pricing/on-demand/ |
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

## 2. Purchasing options

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

## 3. Placement groups

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

## 4. Instance metadata, user data, instance profiles

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
| Precedence | 1 launch configuration (launch template / parameters), 2 account settings, 3 AMI | no | EC2 configuring-instance-metadata-options.html |
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

## 5. EC2 storage basics and instance states

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

## 6. EC2 Auto Scaling

| Fact | Value | Changed? | Source |
|---|---|---|---|
| Auto Scaling group | Collection of EC2 instances managed as a logical unit | no | ASG what-is-amazon-ec2-auto-scaling.html |
| Min size | Group never goes below it | no | ASG what-is-amazon-ec2-auto-scaling.html |
| Max size | Group never goes above it | no | ASG what-is-amazon-ec2-auto-scaling.html |
| Desired capacity | Group maintains this many instances | no | ASG what-is-amazon-ec2-auto-scaling.html |
| Docs example | Min 4, desired 6, max 12 | no | ASG what-is-amazon-ec2-auto-scaling.html |
| Scaling bounds | Dynamic scaling never goes outside min/max (except weighted instances) | no | ASG as-scale-based-on-demand.html |
| Pricing | No additional fee; pay for the underlying resources | no | ASG what-is-amazon-ec2-auto-scaling.html |
| Launch config limit 1 | "As of January 1, 2023, new Amazon EC2 instance types are no longer supported in launch configurations" | changed 2023-01-01 | ASG launch-configurations.html |
| Launch config limit 2 | "Accounts created on or after June 1, 2023 cannot create new launch configurations using the console" | changed 2023-06-01 | ASG launch-configurations.html |
| Launch config limit 3 | "Accounts created on or after October 1, 2024 cannot create new launch configurations using any method (console, API, AWS CLI, or CloudFormation)" | changed 2024-10-01 | ASG launch-configurations.html |
| Launch config guidance | "Migrate to launch templates" | changed | ASG launch-configurations.html |
| Launch config immutable | Cannot modify a launch configuration after creation; only one per group | no | ASG launch-configurations.html |
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
| Default termination policy | 1) Pick the AZ with the most instances 2) outdated configuration first (launch config, then different launch template, then oldest template version) 3) closest to next billing hour 4) random | no | ASG ec2-auto-scaling-termination-policies.html |
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

## 7. Elastic Load Balancing

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
| ALB rule actions | Exactly one of forward, redirect, fixed-response, last in the rule; authentication actions are separate (see Unconfirmed) | no | ALB listener-rules.html |
| ALB rule conditions | host-header, http-request-method, path-pattern, source-ip; also http-header and query-string | no | ALB listener-rules.html |
| ALB condition limits | Up to 3 comparison strings per condition and 5 per rule | no | ALB listener-rules.html |
| ALB rule transforms | Host header rewrite and URL rewrite (one each per rule) | changed (rule transforms are newer) | ALB listener-rules.html |
| ALB rules per ALB | 100 (excluding default), adjustable | no | ALB load-balancer-limits.html |
| ALB condition values per rule | 5, not adjustable | no | ALB load-balancer-limits.html |
| ALB wildcards per rule | 6 | no | ALB load-balancer-limits.html |
| ALBs per Region | 50 | no | ALB load-balancer-limits.html |
| ALB listeners per ALB | 50 | no | ALB load-balancer-limits.html |
| ALB target groups per ALB | 100 | no | ALB load-balancer-limits.html |
| ALB targets per ALB | 1,000 | no | ALB load-balancer-limits.html |
| ALB certificates per ALB | 25 (excluding default) | no | ALB load-balancer-limits.html |
| Targets per target group | 1,000 (instances or IPs); Lambda: 1 | no | ALB load-balancer-limits.html |
| Load balancers per target group | 1 | no | ALB load-balancer-limits.html |
| Target groups per Region | 3,000 (shared with NLB) | no | ALB load-balancer-limits.html |
| ALB HTTP header limits | Request line 16 K, single header 16 K, response header 32 K, request header 64 K | no | ALB load-balancer-limits.html |
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
| ALB mutual TLS | Modes: passthrough and verify; uses trust store; X-Amzn-Mtls headers | changed (mTLS is newer than 2022) | ALB mutual-authentication.html |
| ALB mTLS quotas | Trust stores per account 20; CA certificates per trust store 25; mTLS verify listeners per ALB 2 | changed | ALB load-balancer-limits.html |
| ALB mTLS unsupported | Local Zone and Outpost subnets; session resumption not supported | changed | ALB application-load-balancers.html ; ALB mutual-authentication.html |
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
| Wildcard limit | 5 wildcard characters per rule (docs text); quota table lists 6 condition wildcards per rule | no | ALB rule-condition-types.html ; ALB load-balancer-limits.html |
| Regex matching | host-header, http-header and path-pattern support value matching or regex (RegexValues); no lookaheads, lookbehinds, backreferences | changed (regex conditions are newer) | ALB rule-condition-types.html |
| Match evaluations | Up to 3 per condition, 5 per rule | no | ALB rule-condition-types.html |
| Authentication action example | CreateRule API example uses authenticate-oidc with order 1 then forward with order 2 | no | https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_CreateRule.html |

## 8. Prices (illustrative, us-east-1 / US East (N. Virginia), USD)

| Fact | Value | Changed? | Source |
|---|---|---|---|
| m7g.large On-Demand Linux | 0.0816 USD per hour (2 vCPU, 8 GiB) | no | https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ec2-ondemand-without-sec-sel/US%20East%20(N.%20Virginia)/Linux/index.json |
| m7i.large On-Demand Linux | 0.1008 USD per hour (2 vCPU, 8 GiB) | no | same awsstatic JSON |
| t4g.micro On-Demand Linux | 0.0084 USD per hour | no | same awsstatic JSON |
| t3.micro On-Demand Linux | 0.0104 USD per hour (2 vCPU, 1 GiB, 10 percent baseline) | no | same awsstatic JSON ; https://aws.amazon.com/ec2/instance-types/t3/ |
| c7g.large On-Demand Linux | 0.0725 USD per hour (2 vCPU, 4 GiB) | no | same awsstatic JSON |
| ALB hourly | 0.0225 USD per hour | no | https://aws.amazon.com/elasticloadbalancing/pricing/ |
| ALB LCU | 0.008 USD per LCU-hour | no | https://aws.amazon.com/elasticloadbalancing/pricing/ |
| ALB LCU dimensions | New connections 25/s; active connections 3,000/min (1,500 with mTLS); 1 GB/hour processed (0.4 GB for Lambda); rule evaluations 1,000/s (first 10 rules free); highest dimension billed | no | https://aws.amazon.com/elasticloadbalancing/pricing/ |
| NLB hourly | 0.0225 USD per hour | no | https://aws.amazon.com/elasticloadbalancing/pricing/ |
| NLB NLCU | 0.006 USD per NLCU-hour | no | https://aws.amazon.com/elasticloadbalancing/pricing/ |
| NLCU dimensions | TCP: 800 new conn/s, 100,000 active, 1 GB/h; UDP: 400 new flows/s, 50,000 active, 1 GB/h; TLS: 50 new conn/s, 3,000 active, 1 GB/h | no | https://aws.amazon.com/elasticloadbalancing/pricing/ |
| GWLB hourly | 0.0125 USD per hour plus 0.004 USD per GLCU-hour | no | https://aws.amazon.com/elasticloadbalancing/pricing/ |
| GLCU dimensions | 600 new conn/s, 60,000 active/min, 1 GB/hour | no | https://aws.amazon.com/elasticloadbalancing/pricing/ |
| CLB price example | 0.025 USD per hour plus 0.008 USD per GB processed | no | https://aws.amazon.com/elasticloadbalancing/pricing/ |
| ELB other charges | Data transfer and public IPv4 charges billed separately | changed (public IPv4 charge is newer) | https://aws.amazon.com/elasticloadbalancing/pricing/ |
| Savings Plans example discount | "Up to 72%" (headline); Compute SP up to 66 percent; EC2 Instance SP up to 72 percent | no | https://aws.amazon.com/ec2/pricing/ ; SP plan-types.html |
| RI example discount | Standard up to 72 percent, Convertible up to 66 percent | no | https://aws.amazon.com/ec2/pricing/reserved-instances/ |
| Spot example discount | "Up to 90%" vs On-Demand | no | https://aws.amazon.com/ec2/pricing/ |
| EC2 Free Tier (accounts created before 2025-07-15) | 12 months: t2.micro (or t3.micro where t2.micro unavailable) within usage limits | changed | EC2 burstable-performance-instances.html |
| EC2 Free Tier (accounts created on or after 2025-07-15) | t3.micro, t3.small, t4g.micro, t4g.small, t8i.micro, t8i.small for 6 months or until credits are used | changed 2025-07-15 | EC2 burstable-performance-instances.html |
| t4g.small On-Demand Linux | 0.0168 USD per hour | no | AWS pricing JSON (awsstatic, N. Virginia, Linux) |
| t4g.medium On-Demand Linux | 0.0336 USD per hour | no | AWS pricing JSON |
| c7i.large On-Demand Linux | 0.08925 USD per hour (2 vCPU, 4 GiB) | no | AWS pricing JSON |
| r7g.large On-Demand Linux | 0.1071 USD per hour (2 vCPU, 16 GiB) | no | AWS pricing JSON |
| m7g.xlarge On-Demand Linux | 0.1632 USD per hour (4 vCPU, 16 GiB; exactly 2x m7g.large) | no | AWS pricing JSON |
| Graviton free trial | t4g.small free up to 750 hours per month until Dec 31, 2026 (per Graviton page) | changed | https://aws.amazon.com/ec2/graviton/ |

## Unconfirmed

- Maximum hibernation duration (60 days): not stated on the Hibernate or prerequisites pages read.
- Whether per-second billing excludes non-Linux OS (older "Linux only" wording): the current pages state per-second with 60 s minimum without an OS caveat.
- ALB authentication actions authenticate-cognito and jwt-validation: not confirmed by name (authenticate-oidc seen only in the CreateRule example).
- Target tracking wording "aggressively": the docs say "in direct proportion", round up, and "more gradually" scale-in; the word "aggressive" was not found. Not confirmed.
- Instance vCPU/GiB values come from the AWS pricing JSON, not from the instancetypes gp/co/mo spec pages (those pages were not read in this follow-up).
- Wildcard limit mismatch: rule-condition-types says 5 wildcards per rule, the quota table says 6; not reconciled.
- Date NLB security group support launched (reported as 2023): page gives no date.
- Date ALB target-group cross-zone override launched (reported as 2022): page gives no date.
- Date IMDSv2 became default for AL2023 and newer instance types/AMIs: the pages describe account-level defaults and AMI imds-support but give no dates or list of instance types that default to IMDSv2 only.
- Spot blocks (defined duration) status: no page read mentions them (EC2 purchasing options page no longer lists them).
- Graviton price-performance percentage: Graviton page gives "up to 20% less cost" and "up to 60% less energy"; no price-performance figure was found there. T4g: "up to 40% higher price/performance vs T3" is on the burstable page.
- Predictive scaling details (history required, forecast horizon): the overview page gave no numbers.
- Default instance warmup / grace period for predictive scaling: none documented ("no default warmup time").
- AWS EC2-Classic retirement date for CLB context: not on the CLB page read.
- ALB price for us-east-1 is taken from the pricing-page examples (page said N. Virginia); not independently re-checked in a rate table.
- ASG scale-in default termination "closest to next billing hour" benefit: noted by AWS as limited; no further numbers.
- Whether t4g.micro and other T-instance prices include unlimited-mode surcharge: not applicable; only base price read.

## Confidence notes

- High confidence: ASG defaults (cooldown 300 s, grace period 300 s console / 0 CLI, lifecycle timeout 3,600 s, 48 h or 100x, max lifetime minimum 86,400 s), placement group limits, IMDSv2 mechanics, user data 16 KB, ALB health check defaults and quotas, RI/SP discount maxima (read from AWS pages today).
- Medium confidence: instance family lists and latest generations change frequently (the docs list included M9g/C9g/R9g and T8i today); treat generation names as perishable. Compute Savings Plans maximum is 66 percent on two pages while the headline "up to 72%" applies to EC2 Instance Savings Plans.
- Instance prices come from AWS public pricing JSON for N. Virginia (Linux, no preinstalled software, shared tenancy assumed); the JSON "Tenancy" field was empty. ELB prices come from the pricing page examples. All illustrative.
- Several docs now include features newer than SAA-C03 (Database Savings Plans, regional rules transforms, mTLS, price-capacity-optimized, instance maintenance policies). Exam questions still center on classic behaviour.
- The exam guide was not re-read for this pass; section order follows the brief.

Exam tasks: 3.2, 4.2

# 01 — EC2 instance types

## What it is

An **instance type** is a fixed bundle of vCPUs, memory, network and (sometimes) local disk. You pick one
when you launch an instance. Pick badly and you either pay for idle memory or run out of it.

Two exam tasks lean on this note:

- **3.2** "select the appropriate compute options and features (for example, EC2 instance types)".
- **4.2** "select the appropriate instance family" and "the appropriate instance size".

The job is always the same: read the workload, find the bottleneck (CPU, memory, disk, GPU), and choose the
family that fits. Then choose the smallest size that carries the load. Drill 01 builds a name decoder and a chooser.

## How it works

### Reading a name

`m7g.2xlarge` has two parts, split by the period:

| Part | Example | Meaning |
|---|---|---|
| Series | `m` | The family's purpose: M = general purpose |
| Generation | `7` | Newer number = newer hardware, usually better price/performance |
| Option letters | `g` | Extra traits: here AWS Graviton (Arm) |
| Size | `2xlarge` | How much of the family you get |

`c7gn.xlarge` reads the same way: series C, generation 7, options `g` and `n`, size xlarge.

Option letters to know:

| Letter | Meaning |
|---|---|
| `g` | AWS Graviton processor (Arm) |
| `a` | AMD processor |
| `i` | Intel processor |
| `d` | Instance store volumes (local disk) |
| `n` | Network and EBS optimized |
| `e` | Extra storage, memory or GPU memory |
| `z` | High CPU frequency |
| `b` | Block storage optimization |

A size of `metal` means bare metal: no hypervisor.
Newer names exist (for example M8g, M9g, C8i, T8i, and `-flex` types). Treat generations as examples. The exam asks
about families, not about the newest number.

### The families

| Series | Family | Use it for |
|---|---|---|
| M | General purpose | Web and app servers, small databases. Balanced CPU and memory. The default choice |
| T | Burstable | Low average CPU with short peaks: dev boxes, small sites |
| C | Compute optimized | CPU-bound work: batch, encoding, game servers, high-traffic web tier |
| R | Memory optimized | In-memory caches, big databases, real-time analytics |
| X, U, z | Memory intensive / high memory | Very large in-memory databases (U goes from 3 TiB to 32 TiB RAM). `z` also has a high clock speed |
| I, D, H | Storage optimized (D = dense storage) | High local disk I/O: NoSQL, data warehouses, big sequential reads |
| P, G | GPU (P accelerated; G graphics intensive) | ML training, graphics, video |
| Inf, Trn | AWS Inferentia, AWS Trainium | ML inference and training on AWS chips |
| F | FPGA | Custom hardware acceleration |
| VT | Video transcoding | Live video |
| Mac | macOS | Building iOS and macOS apps |
| Hpc | High performance computing | Tightly coupled simulations |

### Choose by memory per vCPU

The three main families keep a fixed ratio. This is the fastest way to choose:

| Family | GiB per vCPU | Example `large` (2 vCPU) |
|---|---|---|
| C compute | 2 | c7g.large: 4 GiB |
| M general | 4 | m7g.large: 8 GiB |
| R memory | 8 | r7g.large: 16 GiB |

Work out `memory ÷ vCPUs` for the workload. A job that needs 8 vCPUs and 16 GiB is 2 GiB per vCPU, so C.
A job that needs 4 vCPUs and 32 GiB is 8 GiB per vCPU, so R. Above 8 GiB per vCPU, look at X or U.
Drill 01's `choose_type` does exactly this.

### Sizes double

Inside a family, one step up doubles vCPUs, memory and (roughly) price. For m7g:

| Size | vCPU | Memory |
|---|---|---|
| medium | 1 | 4 GiB |
| large | 2 | 8 GiB |
| xlarge | 4 | 16 GiB |
| 2xlarge | 8 | 32 GiB |
| 4xlarge | 16 | 64 GiB |
| 8xlarge | 32 | 128 GiB |

The ladder breaks at 12xlarge (48 vCPU). Expect odd sizes between the big steps.
Because price doubles with size, one `m7g.xlarge` costs the same as two `m7g.large`. Choose by what the workload
needs, not by price per hour.

### Graviton (Arm) or x86

**Graviton** processors are AWS-designed and Arm-based. They carry the option letter `g` (M7g, C7g, R7g, T4g).
AWS says Graviton instances "cost up to 20% less than comparable x86-based Amazon EC2 instances".
In the course prices, `m7g.large` is 0.0816 USD/hour and `m7i.large` (Intel) is 0.1008 USD/hour.

Use Graviton by default for new Linux workloads. Stay on x86 (Intel `i`, AMD `a`) when:

- the software is only built for x86-64 (a vendor binary, an older container image, some Windows workloads);
- you must run Windows or another OS without an Arm build;
- you do not have time to rebuild and test for Arm.

An AMI is built for one architecture. An `arm64` AMI will not boot on an x86 type, and the reverse. On the exam,
"lowest cost, application recompiles easily" points to Graviton.

### Burstable (T) instances and CPU credits

T types give you a **baseline** CPU share and let you **burst** above it using **CPU credits**.

- 1 CPU credit = one vCPU at 100 % for one minute.
- Below the baseline, the instance **earns** credits. Above it, it **spends** them.
- Baseline is a percentage of each vCPU. t3.micro and t4g.micro: 10 %. t3.nano: 5 %. t3.large: 30 %.
- Credits do not expire while the instance runs. An instance can hold about 24 hours of earned credits; extra is discarded.
- T3, T3a and T4g keep their credits for 7 days after a stop. T2 loses them at once.

Two modes:

| Mode | Behaviour when credits run out | Cost effect |
|---|---|---|
| Standard | CPU falls back gradually to the baseline | No extra charge. The app slows down |
| Unlimited | Keeps bursting by borrowing **surplus credits** | If the 24-hour average CPU is above baseline, a flat extra rate per vCPU-hour is billed |

T3, T3a and T4g default to **Unlimited**. T2 defaults to Standard. Only T2 in Standard mode gets launch credits.
AWS recommends **Standard** for burstable Spot Instances, to avoid surprise surplus charges.

A T instance whose CPU stays high all day is the wrong choice. It is both slower and, in Unlimited mode,
more expensive than an M. Use T when the average is well under the baseline. AWS says T instances can save up to
15 % against M instances.

### vCPU quotas

On-Demand limits are counted in **vCPUs of running instances**, per family group:

| Group | Default quota |
|---|---|
| Standard (A, C, D, H, I, M, R, T, Z) | 5 vCPUs, adjustable |
| G and VT, P, Inf, Trn, X, DL, F, HPC, High Memory | 0 each, adjustable |

With the default quota of 5 vCPUs you can run two `t4g.micro` (2 vCPUs each) and not a third. Stopped instances do not count. An unused
Capacity Reservation does. If a launch fails with `VcpuLimitExceeded`, ask for a quota increase.
GPU families start at **zero**: request them before you need them.

## Numbers to know

- Memory per vCPU: **C 2 / M 4 / R 8 GiB**.
- Sizes double from `large` upward (`large` 2, `xlarge` 4, `2xlarge` 8 ... vCPUs).
- T credits: 1 credit = 1 vCPU at 100 % for 1 minute. t3.micro/t4g.micro baseline 10 %.
- T3/T3a/T4g default to Unlimited. T2 defaults to Standard.
- Graviton: "up to 20 % less cost" than comparable x86. T4g: 20 % lower cost than T3.
- Default Standard-family vCPU quota: 5. GPU and X families: 0.
- Course prices (illustrative): t4g.micro 0.0084 USD/h, m7g.large 0.0816, c7g.large 0.0725, r7g.large 0.1071.

## When to choose it

| Workload | Choose |
|---|---|
| Balanced web or app server | M (general purpose) |
| CPU-bound: encoding, batch, busy web tier | C |
| Large cache or in-memory database | R (X or U if even larger) |
| Idle most of the day, short peaks | T |
| Very fast local disk | I or D (storage optimized) |
| ML training | P or Trn; inference Inf |
| New Linux workload that runs on Arm | The `g` version (Graviton) |
| Software only for x86 | `i` (Intel) or `a` (AMD) |
| Low-latency network between nodes | `n` option, plus a cluster placement group (note 03) |

## Exam traps

- **Choosing by name, not need.** "Compute optimized" is for CPU-bound work. A cache that needs lots of RAM is R, not C.
- **T for constant load.** Burstable is for low averages. Constant 80 % CPU belongs on M or C.
- **Unlimited surprise.** T3 and T4g launch in Unlimited mode. A hot T3 can cost more than an M.
- **Architecture mismatch.** An arm64 AMI needs a Graviton type, and an x86 AMI needs Intel or AMD.
- **Instance store is not a disk you keep.** The `d` letter and I/D families have local disks. Data is lost on stop and terminate (note 03).
- **Bigger is not faster at the same price.** Price doubles with size, so scale out with more small instances when the app can.
- **Scaling up vs scaling out.** Changing the size (vertical) needs a stop and start. Adding instances (horizontal) is what Auto Scaling does (note 04).
- **Quota errors.** A fresh launch of a GPU type fails until its default quota of 0 is raised.

## Cost angle

- You pay for the size you launch, whether it is busy or not. Right-size first, then look at purchase options (note 02).
- Graviton is the simplest saving: up to 20 % less for comparable x86, often with better performance.
- T types are cheapest for spiky, low-average loads. Watch Unlimited surplus charges.
- Memory-heavy jobs on C or M waste money: you buy extra vCPUs to get RAM. Use R.
- Rightsizing tools look at real utilisation and suggest a smaller size. Use them after a few weeks of data.
- A stopped instance has no compute charge. Its EBS volumes still bill.

## Comparison

| Family | Series | GiB per vCPU | Strength | Typical use | Watch out |
|---|---|---|---|---|---|
| General purpose | M | 4 | Balance | Web, app, small DB | Not the cheapest for CPU-only work |
| Burstable | T | varies | Low cost for low average CPU | Dev, small sites | Credits, Unlimited charges |
| Compute optimized | C | 2 | Most CPU per dollar | Batch, encoding | Little memory |
| Memory optimized | R | 8 | Memory per dollar | Cache, big DB | Pays for RAM you may not use |
| Memory intensive | X, U, z | above 8 | Terabytes of RAM | In-memory databases | Quota starts at 0 |
| Storage optimized | I, D, H | varies | Local disk I/O | NoSQL, warehouses | Instance store is temporary |
| Accelerated | P, G, Inf, Trn, F | varies | GPUs and chips | ML, graphics | Quota starts at 0, cost |

Now do drill 01 (read an instance type and choose a family and size) and drill 09 (decide which instances to buy).

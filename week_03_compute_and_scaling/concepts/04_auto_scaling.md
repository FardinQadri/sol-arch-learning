Exam tasks: 2.1, 2.2, 3.2

# 04 — EC2 Auto Scaling

## What it is

An **Auto Scaling group (ASG)** is a collection of EC2 instances managed as one unit. It does two jobs:

1. **Keep the right number of healthy instances running** (self-healing, spread over AZs).
2. **Change that number as demand changes** (scaling).

There is no extra fee. You pay for the instances and the other resources the group uses.

This is the "elastic" half of the course. Task 2.1 (scalable, loosely coupled), 2.2 (highly available) and 3.2
("identify metrics and conditions to perform scaling actions") all use it. Drill 03 builds the scaling maths.
Drill 06 builds a group with boto3. Drill 10 asks you to predict what the group does.

## How it works

### The three numbers

| Setting | Meaning |
|---|---|
| **Minimum** | The group never goes below it |
| **Desired capacity** | How many instances the group tries to run right now |
| **Maximum** | The group never goes above it |

Example: min 2, desired 3, max 6. Scaling policies move **desired** between min and max. You can also set desired by
hand. Dynamic scaling never leaves the min/max range.

The group takes a **launch template** (note 03) and a list of **subnets in more than one AZ**. Use at least two AZs.
The group launches new instances in the AZ with the **fewest** instances, to keep the group balanced.

### Staying balanced: AZ rebalancing

If the AZs drift out of balance (an AZ list changes, an AZ recovers, you terminate an instance by hand), the group
**launches new instances first and then terminates old ones**. It may briefly go above max, by 10 % or one instance,
whichever is greater. Rebalancing is a feature of the group, not of the load balancer.

If an AZ fails, the group launches replacements in the remaining AZs to get back to desired capacity.

### Health checks

| Health check | What it sees | Default? |
|---|---|---|
| **EC2** | The EC2 status checks only (instance running, hardware OK) | Yes |
| **ELB** | Also the load balancer's target health | Optional, turn it on |
| Others | VPC Lattice, EBS, custom | Optional |

An unhealthy instance is **terminated and replaced**.

The classic mistake: a web app crashes but the instance is still "running". With EC2 checks the group sees nothing wrong.
With **ELB checks** and a `/healthz` path, the target fails, the group sees it, and it replaces the instance.
Always use ELB health checks behind a load balancer.

**Health check grace period.** A new instance is not judged for failing checks until this time has passed, so the
app can start. Default **300 seconds in the console, 0 seconds in the CLI and SDK**. Zero is a trap: the group may
kill instances that are still booting. Set it to the real start-up time. (An instance that is no longer in the EC2
running state, for example one you stopped, is replaced at once.)

### Scaling policies

| Policy | How it works | You manage |
|---|---|---|
| **Target tracking** | Hold a metric at a target (CPU 50 %). The group scales in proportion to load | Just the target. Auto Scaling creates the alarms |
| **Step scaling** | Different adjustments for different size breaches of an alarm | The alarm and the steps |
| **Simple scaling** | One adjustment per alarm, then waits out a **cooldown** | The alarm, the adjustment and the cooldown |
| **Scheduled** | Changes min, max, desired at a set time | The schedule |
| **Predictive** | Forecasts daily and weekly patterns and adds capacity before the load | Turn it on, pick a metric |

#### Target tracking (the one AWS recommends)

- Choose a **predefined metric**: `ASGAverageCPUUtilization`, `ASGAverageNetworkIn`, `ASGAverageNetworkOut` or
  **`ALBRequestCountPerTarget`**. The load balancer's plain `RequestCount` does not work; use the per-target one.
- The group scales **in proportion** to the load: new capacity = current × metric ÷ target, **rounded up**.
  Example: 4 instances at 75 % CPU with a 50 % target → 4 × 75 ÷ 50 = 6. At 60 % → 4.8, so 5.
- It **scales in more gradually** than it scales out, to protect availability.
- With several target tracking policies the group scales **out** if any wants it and scales **in** only if all agree.
- Works best with a metric that falls as you add instances (CPU does, total request count does not).
- Do not edit its CloudWatch alarms by hand.

#### Step scaling

You make the CloudWatch alarm and define steps. Step bounds are **offsets from the alarm threshold**.
Take a CPU alarm at 60 %:

| Breach | Bounds | Adjustment |
|---|---|---|
| CPU 60 to under 70 | 0 to 10 | +1 |
| CPU 70 to under 85 | 10 to 25 | +2 |
| CPU 85 and above | 25 and up | +4 |

Above the threshold the lower bound is **inclusive** and the upper bound **exclusive**. Below the threshold it flips.
Adjustment types: `ChangeInCapacity`, `ExactCapacity`, `PercentChangeInCapacity`.
Step scaling reacts faster to a big spike than a single step can. Drill 03 has a step-scaling part.

#### Simple scaling and cooldowns

One alarm, one adjustment. After it acts, the group waits for a **cooldown** (default **300 seconds**) and ignores
further alarms. In a fast spike this is slow: the group adds one instance, then sits out five minutes.
AWS says: "We recommend that you do not use simple scaling policies and scaling cooldowns". Use target tracking or step.
Cooldowns only apply to **simple** scaling. Target tracking, step and scheduled actions can scale at once, and the
replacement of an unhealthy instance ignores the cooldown.

#### Scheduled and predictive scaling

- **Scheduled** actions change min, max or desired once or on a recurring (cron) schedule. Up to **125** per group.
  Times are **UTC** unless you give an IANA time zone. Use them when the pattern is known: "business hours Monday to Friday".
- **Predictive** scaling studies the history to forecast the next day and adds capacity ahead of time.
  Pair it with target tracking, which handles surprises.

#### Warmup

A new instance takes time to be useful. **Instance warmup** keeps it out of the aggregated metrics until it is ready,
and blocks scale-in until the warmup ends. It is **not on by default**. AWS strongly recommends setting a
**default instance warmup** (300 seconds is a reasonable start). Without one, target tracking falls back to the cooldown value.

### Which instance goes first? Termination policy

On scale-in the **default** policy works in this order:

1. Choose the **AZ with the most instances** (balance beats everything else).
2. Within it, prefer instances using an **outdated** launch template or version.
3. Then the instance **closest to the next billing hour** (matters less, as billing is per second).
4. Then random.

Other policies: `OldestInstance`, `NewestInstance`, `OldestLaunchTemplate`, `AllocationStrategy`,
`ClosestToNextInstanceHour`. Already-unhealthy instances are removed first.

### Lifecycle hooks

A hook pauses an instance in a wait state when it launches or terminates, so you can run your own steps.
Examples: install software before the instance serves traffic; upload logs before it disappears.

- Default timeout: **3,600 seconds** (one hour). The overall cap is 48 hours or 100 times the timeout, whichever is smaller.
- The result is **continue** or **abandon**. Abandon at launch: the instance is terminated and replaced.
- Notifications go to Amazon EventBridge by default.

### Warm pools

A **warm pool** holds pre-initialised instances beside the group so that scale-out is fast. States: **Stopped**, Running or
Hibernated. In the Stopped state you pay only for EBS volumes and Elastic IPs. The pool needs an EBS root volume.
Good for apps with a very slow boot.

### Changing the fleet: instance refresh

When you change the AMI or the launch template, **instance refresh** replaces instances in a rolling way.
The default **minimum healthy percentage is 90 %**. Lower it to replace faster; raise it to stay safer.
This is how you ship a new AMI with no downtime.

**Max instance lifetime** (at least 86,400 seconds, one day) replaces every instance when it gets that old.
Use it for long-running instances that should be refreshed regularly.

### Mixed instances and Spot

A **mixed instances policy** lets one group use several instance types and both On-Demand and Spot.

- Set an **On-Demand base** plus a percentage above the base for Spot.
- Spot allocation strategy: **`price-capacity-optimized`** (recommended). `capacity-optimized` is also fine. `lowest-price`
  is "not recommended": the highest interruption risk.
- **Capacity Rebalancing** launches a replacement Spot Instance when the old one gets a rebalance recommendation, then
  terminates the old one. The group may briefly exceed max by up to 10 % of desired.
- Your Savings Plans and RIs apply to the On-Demand portion.

### Suspending processes

You can suspend individual processes (Launch, Terminate, HealthCheck, ReplaceUnhealthy, AZRebalance, AlarmNotification,
ScheduledActions, AddToLoadBalancer, InstanceRefresh) while you debug. Remember to resume them.

### Auto Scaling with a load balancer

Attach a target group to the group. New instances **register automatically**; terminated ones deregister and drain
(note 05). Turn on **ELB health checks**. Scale on `ALBRequestCountPerTarget` for web traffic.

## Numbers to know

- Grace period: **300 s** in the console, **0** in the CLI/SDK.
- Cooldown: **300 s** default, simple scaling only. AWS recommends against simple scaling.
- Scheduled actions: **125** per group; time zone UTC by default.
- Lifecycle hook timeout: **3,600 s**.
- Instance refresh minimum healthy: **90 %**.
- Max instance lifetime: at least **86,400 s**.
- AZ rebalancing may exceed max by 10 % or one instance. Capacity Rebalancing by up to 10 % of desired.
- Target tracking metrics: CPU, network in, network out, `ALBRequestCountPerTarget`.

## When to choose it

| Need | Choose |
|---|---|
| Keep N instances alive across AZs | An ASG with min = desired |
| Follow demand with little tuning | Target tracking |
| Big, fast spikes with different responses | Step scaling |
| A known daily or weekly pattern | Scheduled scaling |
| Regular patterns, spare capacity ready early | Predictive scaling |
| Web fleet behind an ALB | Target tracking on `ALBRequestCountPerTarget`, ELB health checks |
| Slow-booting app | Warm pool, or predictive scaling |
| Run custom steps on launch or terminate | Lifecycle hook |
| Roll out a new AMI | Instance refresh |
| Cheap, interruption-tolerant capacity | Mixed instances with Spot |

## Exam traps

- **EC2 health checks behind an ALB.** The group will not replace an instance whose app is dead. Use ELB.
- **Grace period 0 from the CLI.** New instances are judged at once and may be replaced in a loop.
- **One subnet.** A single AZ is a single point of failure. Use at least two.
- **Min = 1 for a "highly available" tier.** One instance is not HA while it is replaced. Use min 2 across two AZs.
- **Simple scaling in a spike.** The cooldown blocks the next action. Prefer target tracking or step.
- **Target tracking on `RequestCount`.** Not supported. Use `ALBRequestCountPerTarget`.
- **Scaling beyond max.** It cannot. If you still need capacity, raise max.
- **Scheduled actions run in the Region's local time.** They run in UTC unless you set a zone.
- **Warm pool Running state.** It costs the full instance price. Stopped is the cheap one.
- **Terminating the biggest AZ.** The default policy picks the AZ with the most instances first.
- **Launch configurations.** Retired for new accounts; use launch templates.

## Cost angle

- The ASG itself is free. Scaling in is the saving: fewer instances at night.
- Set max as a safety cap. A runaway scale-out ends at max, not at your credit limit.
- Combine a Savings Plan for the baseline (min) with On-Demand and Spot above it.
- Warm pools in the Stopped state cost EBS and Elastic IPs only.
- Scheduled scaling to zero in a dev environment overnight stops paying for idle hours.
- Predictive scaling adds capacity just before the load, so you do not keep spare instances running all day.
- Unhealthy-instance replacement loops (grace period too short) bill every new instance for at least a minute.

## Comparison

| Policy | Trigger | Reacts to | You set | Cooldown | Pick it when |
|---|---|---|---|---|---|
| Target tracking | Metric vs target | Proportion of load | Target value | No | Default choice |
| Step | CloudWatch alarm | Size of breach | Alarm and steps | No | You want stronger moves for bigger spikes |
| Simple | CloudWatch alarm | One threshold | Alarm, adjustment, cooldown | **Yes (300 s)** | Almost never (AWS recommends against) |
| Scheduled | Clock | Known pattern | Time and min/max/desired | No | Predictable events |
| Predictive | Forecast | History | Metric and mode | No | Recurring daily or weekly cycles |

Now do drill 03 (let the group size itself), drill 06 (a fleet that heals itself), drill 08 (fix the bug) and drill 10 (what does Auto Scaling do?).

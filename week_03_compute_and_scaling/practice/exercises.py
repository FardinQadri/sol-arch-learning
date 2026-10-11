"""
Week 03 drills — compute and scaling
====================================
Run:    python practice/exercises.py          every drill
        python practice/exercises.py 4        drill 4 only
Drills 01–05 are pure Python models of how compute works: instance-type names, what the same
fleet costs under each purchasing option, how Auto Scaling sizes a group, which load-balancer rule
answers a request, and how cross-zone load balancing splits traffic. Drills 06–08 build and fix
the real thing with boto3 against moto (a fake AWS). Drills 09–10 are decide and predict drills.
Nothing here can touch a real account or cost money.
The course's own versions of drills 01–05 (_harness/awslib/ec2types.py, purchasing.py, scaling.py
and elb.py) are their answer key — don't open them until you are done.
Note: moto only stores what you send. It never launches Graviton chips, spreads instances over
zones or replaces sick ones. So the drills read your settings back and the models show the behaviour.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.awsdrill import Drill, run  # noqa: E402
from _harness.awslib import prices  # noqa: E402


# ── Exercise 01 ★: Read an instance type ─────────────────────────────
"""
An instance type name is  <series><generation><options>.<size>.  In c7gn.xlarge: series c,
generation 7, options g and n, size xlarge.
decode(instance_type) -> dict
    Trim and lower-case the name first (" C7G.Large " is fine). Return exactly these keys:
      "series"        the longest series prefix of the part before the dot: c, m, r, t, x, i, g, mac, hpc ...
      "category"      the family group of that series (table below)
      "generation"    the number after the series, as an int (at least 1)
      "options"       the letters after the generation, as a list of one-letter strings, in order
      "processor"     "AWS Graviton" (option g), "AMD" (option a), "Intel" (option i), else "not stated"
      "size"          the part after the dot, unchanged
      "burstable"     True when the series is t
      "instance_store"  True when the option letter d is present
      "bare_metal"    True when the size starts with "metal"
      "flex"          True when the family ends with "-flex" (m7i-flex.large). Strip "-flex" before
                      parsing, then add "flex" at the end of "options".
    Series -> category (try longer prefixes first, so "mac" is not "m" and "dl" is not "d"):
      general purpose: m t a mac       compute optimized: c      memory optimized: r x z u
      storage optimized: i d h         high performance computing: hpc
      accelerated computing: inf trn dl vt p g f
    Option letters: a AMD, g Graviton, i Intel, d instance store, n network and EBS optimized,
      e extra storage or memory, z high CPU frequency, b block storage optimized, q Qualcomm
      inference accelerators.
    Sizes: nano, micro, small, medium, large, xlarge, a number then xlarge (3xlarge, 16xlarge),
      metal, or metal-<n>xl. Anything else is not a size.
    ValueError for: no "." in the name, an unknown size, an unknown series, a missing or zero
    generation, an unknown option letter.
    WATCH OUT: the processor comes from the OPTION letters only. g5.xlarge is a GPU series (g),
    not a Graviton chip. g5g.xlarge has the option g, so it is Graviton.
choose_type(vcpus, memory_gib, processor="graviton", generation=7) -> str
    Pick the series from memory per vCPU: at most 2 GiB per vCPU -> c, at most 4 -> m, at most 8 -> r
    (4 GiB on 2 vCPUs is 2 GiB per vCPU, so c; 8 GiB on 2 vCPUs is 4 per vCPU, so m).
    Pick the size from the vCPU count: 1 -> medium, 2 -> large, 4 -> xlarge, any other multiple
    of 4 -> f"{vcpus // 4}xlarge". The processor option letter: graviton g, intel i, amd a.
    Name = series + generation + letter + "." + size.
    ValueError for: vcpus or memory not positive, an unknown processor, more than 8 GiB per vCPU
    (look at the X or U families), a vCPU count with no standard size (3, 6, 10 ...).
Examples:
    decode("c7gn.xlarge")["options"] == ["g", "n"]       decode("t3.micro")["processor"] == "not stated"
    choose_type(2, 4) == "c7g.large"      choose_type(2, 8) == "m7g.large"     choose_type(2, 16) == "r7g.large"
    choose_type(16, 32, "amd", 6) == "c6a.4xlarge"
Why? Names are the cheapest documentation AWS has: you can read the chip, the generation and the
memory shape from the name, and the exam expects you to.
Hint: re.match(r"[0-9]+", rest) finds the generation; sorted(SERIES, key=len, reverse=True) tries
      long prefixes first. Graviton is the cheapest 'good' default (AWS: up to 20% less than comparable x86).
"""
def decode(instance_type):
    raise NotImplementedError  # YOUR CODE


def choose_type(vcpus, memory_gib, processor="graviton", generation=7):
    raise NotImplementedError  # YOUR CODE


class Ex01(Drill):
    """Read an instance type ★"""
    tasks = ("3.2",)

    def test_decode_a_full_name(self):
        got = decode("c7gn.xlarge")
        self.assertEqual((got["series"], got["category"], got["generation"], got["options"], got["size"]),
                         ("c", "compute optimized", 7, ["g", "n"], "xlarge"))
        self.assertEqual(got["processor"], "AWS Graviton")
        self.assertEqual(set(got), {"series", "category", "generation", "options", "processor", "size",
                                    "burstable", "instance_store", "bare_metal", "flex"}, "return exactly the documented keys")

    def test_processor_comes_from_the_option_letters(self):
        for name, want in {"m7g.large": "AWS Graviton", "m7i.large": "Intel", "m7a.large": "AMD", "t3.micro": "not stated",
                           "g5.xlarge": "not stated", "g5g.xlarge": "AWS Graviton", "i3en.3xlarge": "not stated"}.items():
            with self.subTest(name=name):
                self.assertEqual(decode(name)["processor"], want,
                                 f"{name}: only the option letters (after the generation) name the processor, not the series")

    def test_flags(self):
        self.assertTrue(decode("t3.micro")["burstable"])
        self.assertFalse(decode("m7g.large")["burstable"])
        self.assertTrue(decode("x2gd.metal-24xl")["instance_store"])
        self.assertTrue(decode("x2gd.metal-24xl")["bare_metal"])
        self.assertTrue(decode("mac2.metal")["bare_metal"])
        self.assertFalse(decode("c7g.16xlarge")["bare_metal"])

    def test_long_prefixes_and_flex(self):
        self.assertEqual((decode("mac2.metal")["series"], decode("mac2.metal")["category"]), ("mac", "general purpose"))
        self.assertEqual(decode("hpc7g.16xlarge")["series"], "hpc")
        self.assertEqual(decode("dl1.24xlarge")["series"], "dl")
        flex = decode("m7i-flex.large")
        self.assertEqual((flex["series"], flex["options"], flex["processor"], flex["flex"]), ("m", ["i", "flex"], "Intel", True))

    def test_trims_and_ignores_case(self):
        self.assertEqual(decode(" C7G.Large "), decode("c7g.large"))
        self.assertEqual(decode("C7G.Large")["size"], "large")

    def test_decode_rejects_bad_names(self):
        for bad in ("c7g", "c7g.huge", "q7g.large", "c.large", "c0g.large", "c7w.large", "m7i-flex", ""):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    decode(bad)

    def test_choose_type(self):
        cases = {(2, 4): "c7g.large", (2, 8): "m7g.large", (2, 16): "r7g.large", (1, 1): "c7g.medium", (4, 16): "m7g.xlarge",
                 (8, 64): "r7g.2xlarge", (2, 4.5): "m7g.large"}
        for (vcpus, memory), want in cases.items():
            with self.subTest(vcpus=vcpus, memory=memory):
                self.assertEqual(choose_type(vcpus, memory), want)

    def test_choose_type_boundaries_are_inclusive(self):
        self.assertEqual(choose_type(4, 8)[0], "c", "exactly 2 GiB per vCPU is still C")
        self.assertEqual(choose_type(4, 16)[0], "m", "exactly 4 GiB per vCPU is still M")
        self.assertEqual(choose_type(4, 32)[0], "r", "exactly 8 GiB per vCPU is still R")

    def test_choose_type_processor_and_generation(self):
        self.assertEqual(choose_type(4, 16, "intel"), "m7i.xlarge")
        self.assertEqual(choose_type(16, 32, "amd", 6), "c6a.4xlarge")
        self.assertEqual(choose_type(48, 96, generation=8), "c8g.12xlarge")

    def test_choose_type_rejects_what_cannot_be_built(self):
        for args in ((0, 4), (2, 0), (2, 4, "arm"), (2, 17), (3, 6), (6, 12)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    choose_type(*args)


# ── Exercise 02 ★: Pay for the hours you use ─────────────────────────
"""
PRICES (given) are illustrative us-east-1 numbers from _harness/awslib/prices.toml:
compute_savings_plan_discount 0.31, standard_ri_discount 0.40, spot_discount 0.70.
`rate` is the On-Demand price for ONE instance-hour (for example PRICES["m7g_large_per_hour"]).
The four options are OPTIONS = ("on-demand", "compute savings plan", "standard reserved", "spot").
monthly_cost(option, rate, instances, hours_used, *, hours_in_month=730, price=PRICES) -> float
    USD per month, rounded to 2 decimal places.
      on-demand               instances x hours_used x rate
      spot                    the same, times (1 - spot_discount)
      compute savings plan    instances x hours_in_month x rate x (1 - compute_savings_plan_discount)
      standard reserved       instances x hours_in_month x rate x (1 - standard_ri_discount)
    A commitment is billed for EVERY hour of the month, used or not. On-Demand and Spot bill only
    the hours the instance runs.
    ValueError for: an unknown option, a negative rate, instances or hours_used, or hours_used
    greater than hours_in_month.
cheapest(rate, instances, hours_used, *, interruptible=False, may_change_family=False,
         hours_in_month=730, price=PRICES) -> (option, cost)
    The cheapest ALLOWED option. On-Demand and the Compute Savings Plan are always allowed.
    A Standard RI is locked to one instance type and Region, so it is allowed only when
    may_change_family is False. Spot is allowed only when interruptible is True.
    A tie goes to the option that comes first in OPTIONS.
break_even_hours(option, *, hours_in_month=730, price=PRICES) -> float
    The hours of use per month where a commitment costs the same as On-Demand:
    hours_in_month x (1 - discount), rounded to 1 decimal. Only "compute savings plan" and
    "standard reserved" have one — any other option → ValueError.
Examples (m7g.large, rate 0.0816):
    monthly_cost("on-demand", 0.0816, 1, 730) == 59.57       monthly_cost("compute savings plan", 0.0816, 1, 730) == 41.1
    cheapest(0.0816, 4, 730) == ("standard reserved", 142.96)    # runs all month: commit
    cheapest(0.0816, 4, 173) == ("on-demand", 56.47)             # 9-to-5 on weekdays: 173 hours, stay On-Demand
    break_even_hours("compute savings plan") == 503.7            # 69% of the month
Why? A commitment is a bet that you will use the hours. Below the break-even point you pay for
hours you never use. Savings Plans follow you across families, Regions, Fargate and Lambda; a
Standard RI is cheaper but stuck to one type.
Hint: write monthly_cost first; cheapest is a min() over the allowed options, break_even_hours is one line.
"""
PRICES = prices.section("ec2")
OPTIONS = ("on-demand", "compute savings plan", "standard reserved", "spot")


def monthly_cost(option, rate, instances, hours_used, *, hours_in_month=730, price=PRICES):
    raise NotImplementedError  # YOUR CODE


def cheapest(rate, instances, hours_used, *, interruptible=False, may_change_family=False, hours_in_month=730, price=PRICES):
    raise NotImplementedError  # YOUR CODE


def break_even_hours(option, *, hours_in_month=730, price=PRICES):
    raise NotImplementedError  # YOUR CODE


class Ex02(Drill):
    """Pay for the hours you use ★"""
    tasks = ("4.2",)
    M7G = PRICES["m7g_large_per_hour"]

    def test_monthly_cost_each_option(self):
        self.assertEqual(monthly_cost("on-demand", self.M7G, 1, 730), 59.57)
        self.assertEqual(monthly_cost("compute savings plan", self.M7G, 1, 730), 41.1)
        self.assertEqual(monthly_cost("standard reserved", self.M7G, 1, 730), 35.74)
        self.assertEqual(monthly_cost("spot", self.M7G, 1, 730), 17.87)

    def test_commitments_bill_every_hour_of_the_month(self):
        part_time = monthly_cost("compute savings plan", self.M7G, 4, 173)
        self.assertEqual(part_time, monthly_cost("compute savings plan", self.M7G, 4, 730),
                         "a commitment costs the same however few hours you use")
        self.assertEqual(monthly_cost("standard reserved", self.M7G, 4, 0), monthly_cost("standard reserved", self.M7G, 4, 730))
        self.assertEqual(monthly_cost("on-demand", self.M7G, 4, 173), 56.47, "On-Demand bills only the hours used")
        self.assertEqual(monthly_cost("spot", self.M7G, 4, 173), 16.94)

    def test_a_24_7_fleet_commits(self):
        self.assertEqual(cheapest(self.M7G, 4, 730), ("standard reserved", 142.96))
        self.assertEqual(cheapest(self.M7G, 4, 730, may_change_family=True), ("compute savings plan", 164.41),
                         "a Standard RI is locked to one instance type: it is out when the family may change")

    def test_a_nine_to_five_fleet_stays_on_demand(self):
        self.assertEqual(cheapest(self.M7G, 4, 173), ("on-demand", 56.47),
                         "173 hours is far below the break-even point: a commitment would pay for idle hours")

    def test_spot_only_when_interruptible(self):
        self.assertEqual(cheapest(self.M7G, 4, 730, interruptible=True), ("spot", 71.48))
        self.assertEqual(cheapest(self.M7G, 4, 173, interruptible=True), ("spot", 16.94))
        self.assertNotEqual(cheapest(self.M7G, 4, 730)[0], "spot", "a workload that cannot be interrupted must not get Spot")

    def test_tie_goes_to_the_earlier_option(self):
        self.assertEqual(cheapest(1.0, 1, 503.7, may_change_family=True), ("on-demand", 503.7))

    def test_break_even(self):
        self.assertEqual(break_even_hours("compute savings plan"), 503.7)
        self.assertEqual(break_even_hours("standard reserved"), 438.0)
        self.assertEqual(break_even_hours("standard reserved", hours_in_month=720), 432.0)
        for option in ("on-demand", "spot", "dedicated"):
            with self.subTest(option=option):
                with self.assertRaises(ValueError):
                    break_even_hours(option)

    def test_uses_the_price_argument(self):
        custom = dict(PRICES, compute_savings_plan_discount=0.5, standard_ri_discount=0.0, spot_discount=0.9)
        self.assertEqual(monthly_cost("compute savings plan", 1.0, 1, 10, price=custom), 365.0)
        self.assertEqual(monthly_cost("spot", 1.0, 1, 10, price=custom), 1.0)
        self.assertEqual(cheapest(1.0, 1, 730, price=custom), ("compute savings plan", 365.0))
        self.assertEqual(monthly_cost("on-demand", 1.0, 1, 10, hours_in_month=100), 10.0)

    def test_rejects_bad_inputs(self):
        for call in (lambda: monthly_cost("free", 1, 1, 1), lambda: monthly_cost("on-demand", -1, 1, 1),
                     lambda: monthly_cost("on-demand", 1, -1, 1), lambda: monthly_cost("on-demand", 1, 1, -1),
                     lambda: monthly_cost("on-demand", 1, 1, 731)):
            with self.subTest():
                with self.assertRaises(ValueError):
                    call()


# ── Exercise 03 ★: Let the group size itself ─────────────────────────
"""
An Auto Scaling group keeps its desired capacity between a minimum and a maximum. Every function
below first checks 0 <= minimum <= maximum (otherwise ValueError) and never returns a number
outside [minimum, maximum].
target_tracking(current, metric, target, minimum, maximum) -> int
    You pick a target for a metric (say 50% average CPU); AWS adds or removes instances in direct
    proportion: new capacity = ceil(current x metric / target), then clamped. Round UP — rounding
    down would leave you above the target. current == 0 → minimum. A negative current or a target
    of 0 or less → ValueError.
    target_tracking(4, 80, 50, 2, 10) == 7        (4 x 80 / 50 = 6.4, rounded up)
    target_tracking(4, 15, 50, 2, 10) == 2        (1.2 would be 2, and the floor is 2 anyway)
step_scaling(current, metric, threshold, steps, minimum, maximum) -> int
    `steps` is a list of (lower, upper, change). The bounds are OFFSETS from the alarm threshold,
    and None means no limit (minus or plus infinity). breach = metric - threshold.
    Above the threshold (breach >= 0) a step matches when lower <= breach < upper (lower inclusive).
    Below it (breach < 0) a step matches when lower < breach <= upper (upper inclusive).
    The matching step's `change` is added to current, then clamped. No step matches → unchanged
    (but still clamped). Steps that overlap, or a step whose lower is not below its upper →
    ValueError.
    steps = [(0, 10, 1), (10, 20, 2), (20, None, 3)], threshold 70: metric 79.9 → +1, metric 80 → +2.
simple_scaling_run(metrics, start, high, low, change, cooldown, minimum, maximum, period=60) -> list[int]
    One metric sample every `period` seconds (the first at second 0). Return the desired capacity
    after each sample. metric > high adds `change`, metric < low removes `change` (clamped). An
    action that really changes the capacity starts a cooldown: samples at less than `cooldown`
    seconds after it are ignored. An action that changes nothing (already at the maximum) does NOT
    start a cooldown.
    simple_scaling_run([80]*6, 2, 70, 30, 1, 300, 1, 10) == [3, 3, 3, 3, 3, 4]
    (second 0 adds one; seconds 60–240 are inside the 300 s cooldown; second 300 adds another)
Why? Target tracking is the one to reach for: you state the goal, AWS does the sums. Step scaling
reacts harder to bigger breaches. Simple scaling is the oldest: one action, then it waits out the cooldown.
Hint: math.ceil(current * metric / target) — a float like 6.000000000000001 would round up to 7,
      so round the product to 9 places first.
"""
import math  # noqa: E402,F401


def target_tracking(current, metric, target, minimum, maximum):
    raise NotImplementedError  # YOUR CODE


def step_scaling(current, metric, threshold, steps, minimum, maximum):
    raise NotImplementedError  # YOUR CODE


def simple_scaling_run(metrics, start, high, low, change, cooldown, minimum, maximum, period=60):
    raise NotImplementedError  # YOUR CODE


class Ex03(Drill):
    """Let the group size itself ★"""
    tasks = ("3.2", "2.1")
    SCALE_OUT = [(0, 10, 1), (10, 20, 2), (20, None, 3)]
    SCALE_IN = [(None, -20, -2), (-20, 0, -1)]

    def test_target_tracking_rounds_up(self):
        self.assertEqual(target_tracking(4, 80, 50, 2, 10), 7, "4 x 80 / 50 = 6.4 → you need 7, not 6")
        self.assertEqual(target_tracking(4, 25, 50, 2, 10), 2)
        self.assertEqual(target_tracking(4, 50, 50, 2, 10), 4, "on target: no change")
        self.assertEqual(target_tracking(3, 51, 50, 1, 10), 4)

    def test_target_tracking_stays_inside_the_bounds(self):
        self.assertEqual(target_tracking(10, 100, 50, 2, 10), 10, "20 wanted, 10 allowed")
        self.assertEqual(target_tracking(4, 15, 50, 2, 10), 2, "the minimum is a floor")
        self.assertEqual(target_tracking(0, 90, 50, 2, 10), 2, "an empty group goes to the minimum")

    def test_target_tracking_rejects_nonsense(self):
        for args in ((4, 50, 0, 1, 5), (-1, 50, 50, 1, 5), (4, 50, 50, 5, 1), (4, 50, 50, -1, 5)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    target_tracking(*args)

    def test_step_bounds_above_the_threshold(self):
        for metric, want in {69: 5, 70: 6, 79.9: 6, 80: 7, 90: 8, 100: 8}.items():
            with self.subTest(metric=metric):
                self.assertEqual(step_scaling(5, metric, 70, self.SCALE_OUT, 1, 10), want,
                                 "above the threshold the LOWER bound is inclusive and the upper is exclusive")

    def test_step_bounds_below_the_threshold(self):
        for metric, want in {31: 5, 30: 5, 29: 4, 10: 3, 9: 3}.items():
            with self.subTest(metric=metric):
                self.assertEqual(step_scaling(5, metric, 30, self.SCALE_IN, 1, 10), want,
                                 "below the threshold the UPPER bound is inclusive and the lower is exclusive")

    def test_step_scaling_is_clamped(self):
        self.assertEqual(step_scaling(9, 100, 70, self.SCALE_OUT, 1, 10), 10)
        self.assertEqual(step_scaling(2, 5, 30, self.SCALE_IN, 1, 10), 1)

    def test_step_scaling_rejects_bad_steps(self):
        for steps in ([(0, 10, 1), (5, 15, 2)], [(10, 10, 1)], [(10, 5, 1)]):
            with self.subTest(steps=steps):
                with self.assertRaises(ValueError):
                    step_scaling(5, 80, 70, steps, 1, 10)

    def test_simple_scaling_cooldown(self):
        self.assertEqual(simple_scaling_run([80] * 6, 2, 70, 30, 1, 300, 1, 10), [3, 3, 3, 3, 3, 4],
                         "the cooldown is 300 s: samples at 60–240 s are ignored, the one at 300 s counts")
        self.assertEqual(simple_scaling_run([80, 20, 20, 20, 20, 20, 20], 2, 70, 30, 1, 300, 1, 10), [3, 3, 3, 3, 3, 2, 2])

    def test_simple_scaling_period_and_change(self):
        self.assertEqual(simple_scaling_run([80, 50, 80, 80, 80, 80, 80, 80, 80, 80, 80], 2, 70, 30, 2, 120, 1, 5),
                         [4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5])
        self.assertEqual(simple_scaling_run([80, 80, 80], 2, 70, 30, 1, 60, 1, 10, period=30), [3, 3, 4])

    def test_an_action_that_changes_nothing_starts_no_cooldown(self):
        self.assertEqual(simple_scaling_run([90, 10], 10, 70, 30, 1, 300, 1, 10), [10, 9],
                         "at the maximum nothing happened, so there is no cooldown to wait out")


# ── Exercise 04 ★: Which rule answers? ───────────────────────────────
"""
An Application Load Balancer listener holds rules. Model the choice of rule.
A rule:     {"priority": 1..50000 or "default", "conditions": [condition, ...], "action": anything}
A condition: {"field": F, "values": [...]} where F is one of
    "host-header"        values are host patterns ("admin.*")
    "path-pattern"       values are path patterns ("/api/*")
    "http-request-method" values are methods ("GET", "POST")
    "http-header"        also has "name": "X-Canary"; values are patterns for that header
    "query-string"       values are dicts {"key": pattern, "value": pattern}; either part may be left out
    "source-ip"          values are CIDR blocks ("10.0.0.0/8")
A request: {"host": …, "path": …, "method": …, "headers": {…}, "query": {…}, "source_ip": …} (any key may be missing).
match_rule(request, rules) -> the "action" of the rule that answers.
    Check the numbered rules in ASCENDING priority (1 before 5, whatever their order in the list),
    and the default rule last. A rule matches when ALL its conditions match (AND); a condition
    matches when ANY of its values match (OR). The default rule has no conditions and matches everything.
    Matching:  "*" matches any run of characters (even none), "?" matches exactly one character.
      host, header (name and value) and query-string (key and value): ignore case.
      path and method: exact case. The path is compared WITHOUT its query string ("/a?x=1" → "/a").
      source-ip: the address is inside the CIDR. A request with no source_ip does not match.
    Check the rules first and raise ValueError for: not exactly one default rule, or a default rule
    with conditions; a numbered rule with no conditions; two rules with the same priority; a
    priority that is not an int from 1 to 50000; an unknown condition field; a condition with no
    values; more than 3 values in one condition; more than 5 values in one rule (all conditions together).
Example:
    rules = [{"priority": 20, "conditions": [{"field": "path-pattern", "values": ["/api/*"]}], "action": "api"},
             {"priority": 10, "conditions": [{"field": "path-pattern", "values": ["/api/admin/*"]}], "action": "block"},
             {"priority": "default", "action": "web"}]
    match_rule({"path": "/api/admin/users"}, rules) == "block"     # 10 is checked first, though listed second
    match_rule({"path": "/Ab3dE9x"}, rules) == "web"
Why? Priority, not list order, decides. Put the narrow rule (block /api/admin/*) before the wide one
(forward /api/*) or the wide one swallows it. The default rule is the safety net — every listener has one.
Hint: validate, then sorted(numbered, key=priority) + [default]; re.fullmatch on a regex built from the
      pattern ("*" → ".*", "?" → ".", everything else re.escape'd) does the wildcards.
"""
import ipaddress  # noqa: E402,F401
import re  # noqa: E402,F401


def match_rule(request, rules):
    raise NotImplementedError  # YOUR CODE


def _rule(priority, field, values, action, **extra):
    return {"priority": priority, "conditions": [{"field": field, "values": values, **extra}], "action": action}


DEFAULT = {"priority": "default", "action": "web"}


class Ex04(Drill):
    """Which rule answers? ★"""
    tasks = ("3.2", "2.1")
    RULES = [
        _rule(30, "path-pattern", ["/api/*"], "api"),
        {"priority": 10, "action": "admin", "conditions": [{"field": "host-header", "values": ["admin.shortly.example"]},
                                                          {"field": "source-ip", "values": ["10.0.0.0/8"]}]},
        {"priority": 20, "action": "api-write", "conditions": [{"field": "http-request-method", "values": ["POST", "PUT"]},
                                                              {"field": "path-pattern", "values": ["/api/*"]}]},
        DEFAULT,
    ]

    def test_priority_beats_list_order(self):
        self.assertEqual(match_rule({"method": "POST", "path": "/api/links"}, self.RULES), "api-write",
                         "priority 20 is checked before priority 30, even though 30 is listed first")
        self.assertEqual(match_rule({"method": "GET", "path": "/api/links"}, self.RULES), "api")

    def test_default_is_last(self):
        self.assertEqual(match_rule({"path": "/Ab3dE9x", "method": "GET"}, self.RULES), "web")
        self.assertEqual(match_rule({}, [DEFAULT]), "web")
        early_default = [DEFAULT, _rule(1, "path-pattern", ["/a"], "a")]
        self.assertEqual(match_rule({"path": "/a"}, early_default), "a", "the default rule is tried last wherever it is listed")

    def test_and_across_conditions_or_within(self):
        admin = {"host": "admin.shortly.example", "source_ip": "10.1.2.3", "path": "/x", "method": "GET"}
        self.assertEqual(match_rule(admin, self.RULES), "admin")
        self.assertEqual(match_rule(dict(admin, source_ip="203.0.113.5"), self.RULES), "web", "both conditions must match")
        self.assertEqual(match_rule(dict(admin, host="shortly.example"), self.RULES), "web")
        self.assertEqual(match_rule({"method": "PUT", "path": "/api/x"}, self.RULES), "api-write", "PUT is one of the allowed methods")
        self.assertEqual(match_rule({"method": "DELETE", "path": "/api/x"}, self.RULES), "api")

    def test_host_ignores_case_and_wildcards_work(self):
        rules = [_rule(1, "host-header", ["*.shortly.example"], "tenant"), DEFAULT]
        self.assertEqual(match_rule({"host": "ACME.Shortly.Example"}, rules), "tenant")
        self.assertEqual(match_rule({"host": "shortly.example"}, rules), "web", "'*.' needs a dot and something before it")
        question = [_rule(1, "host-header", ["app?.shortly.example"], "app"), DEFAULT]
        self.assertEqual(match_rule({"host": "app1.shortly.example"}, question), "app")
        self.assertEqual(match_rule({"host": "app12.shortly.example"}, question), "web", "'?' is exactly one character")

    def test_path_is_case_sensitive_and_ignores_the_query(self):
        self.assertEqual(match_rule({"method": "GET", "path": "/API/links"}, self.RULES), "web", "paths are case-sensitive")
        self.assertEqual(match_rule({"method": "GET", "path": "/api/links?page=2"}, self.RULES), "api",
                         "the query string is not part of the path")
        self.assertEqual(match_rule({"method": "get", "path": "/api/x"}, self.RULES), "api", "'get' is not 'POST'")
        self.assertEqual(match_rule({"method": "post", "path": "/api/x"}, self.RULES), "api", "methods are case-sensitive")

    def test_header_and_query_string_conditions(self):
        rules = [_rule(1, "http-header", ["yes"], "canary", name="X-Canary"),
                 _rule(2, "query-string", [{"key": "v", "value": "2"}], "v2"),
                 _rule(3, "query-string", [{"value": "debug*"}], "debug"), DEFAULT]
        self.assertEqual(match_rule({"headers": {"x-canary": "YES"}}, rules), "canary", "header names and values ignore case")
        self.assertEqual(match_rule({"headers": {"x-canary": "no"}}, rules), "web")
        self.assertEqual(match_rule({"query": {"V": "2"}}, rules), "v2")
        self.assertEqual(match_rule({"query": {"v": "3"}}, rules), "web")
        self.assertEqual(match_rule({"query": {"anything": "debug-mode"}}, rules), "debug", "a value-only condition ignores the key")

    def test_source_ip(self):
        rules = [_rule(1, "source-ip", ["192.0.2.0/24", "198.51.100.7/32"], "office"), DEFAULT]
        self.assertEqual(match_rule({"source_ip": "192.0.2.77"}, rules), "office")
        self.assertEqual(match_rule({"source_ip": "198.51.100.7"}, rules), "office")
        self.assertEqual(match_rule({"source_ip": "198.51.100.8"}, rules), "web")
        self.assertEqual(match_rule({}, rules), "web", "no source address, no match")

    def test_invalid_rule_sets(self):
        ok = _rule(1, "path-pattern", ["/a"], "a")
        v = ["/1", "/2", "/3", "/4"]
        bad = {
            "duplicate priority": [ok, _rule(1, "path-pattern", ["/b"], "b"), DEFAULT],
            "two defaults": [ok, DEFAULT, dict(DEFAULT)],
            "no default": [ok],
            "numbered rule without conditions": [{"priority": 5, "action": "x"}, DEFAULT],
            "default with conditions": [ok, dict(DEFAULT, conditions=ok["conditions"])],
            "4 values in one condition": [_rule(1, "path-pattern", v, "a"), DEFAULT],
            "6 values in one rule": [{"priority": 1, "action": "a", "conditions": [
                {"field": "path-pattern", "values": v[:3]}, {"field": "host-header", "values": ["a", "b", "c"]}]}, DEFAULT],
            "priority 0": [_rule(0, "path-pattern", ["/a"], "a"), DEFAULT],
            "priority 50001": [_rule(50001, "path-pattern", ["/a"], "a"), DEFAULT],
            "unknown field": [_rule(1, "cookie", ["a"], "a"), DEFAULT],
            "condition without values": [_rule(1, "path-pattern", [], "a"), DEFAULT],
        }
        for name, rules in bad.items():
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    match_rule({"path": "/zzz"}, rules)

    def test_limits_themselves_are_allowed(self):
        three = [_rule(1, "path-pattern", ["/1", "/2", "/3"], "a"), DEFAULT]
        self.assertEqual(match_rule({"path": "/3"}, three), "a", "3 values in a condition is the limit, not an error")
        five = [{"priority": 50000, "action": "a", "conditions": [
            {"field": "path-pattern", "values": ["/1", "/2", "/3"]}, {"field": "host-header", "values": ["a", "b"]}]}, DEFAULT]
        self.assertEqual(match_rule({"path": "/2", "host": "B"}, five), "a", "5 values in a rule and priority 50000 are allowed")


# ── Exercise 05 ★: Who gets the traffic? ─────────────────────────────
"""
cross_zone_share(targets_per_az, cross_zone) -> dict[az, float]
    `targets_per_az` maps an AZ name to how many targets (instances) it holds. Return the share of
    ALL requests that ONE target in each AZ receives, as a fraction from 0 to 1.
    Cross-zone ON: the load balancer spreads over every target in every AZ → each target gets 1 / total.
    Cross-zone OFF: each AZ that has at least one target gets an EQUAL slice of the traffic, then
    splits it among its own targets → 1 / (AZs with targets) / (targets in this AZ).
    An AZ with no targets gets 0.0 either way. Negative counts, or no targets at all → ValueError.
    The AWS docs example, AZ-a has 2 targets and AZ-b has 8:
        cross_zone_share({"a": 2, "b": 8}, True)  == {"a": 0.1,  "b": 0.1}      every target 10%
        cross_zone_share({"a": 2, "b": 8}, False) == {"a": 0.25, "b": 0.0625}   a: 25% each, b: 6.25% each
alb_monthly_cost(lcus, hours=730, price=PRICES) -> float
    hours x (alb_per_hour + lcus x alb_per_lcu_hour), rounded to 2 decimal places. `lcus` is the
    average Load Balancer Capacity Units per hour. Negative lcus or hours → ValueError.
    alb_monthly_cost(10) == 74.83         alb_monthly_cost(0) == 16.43   (the hourly fee alone)
Why? An uneven target count with cross-zone off overloads the small zone's targets (25% each against
6.25% each). An ALB always has cross-zone ON at the load balancer; a Network Load Balancer has it OFF by
default, and cross-AZ data transfer charges apply when you turn it on.
Hint: total = sum(counts); live = number of AZs whose count is above 0.
"""
def cross_zone_share(targets_per_az, cross_zone):
    raise NotImplementedError  # YOUR CODE


def alb_monthly_cost(lcus, hours=730, price=PRICES):
    raise NotImplementedError  # YOUR CODE


class Ex05(Drill):
    """Who gets the traffic? ★"""
    tasks = ("2.2", "4.2")

    def test_cross_zone_on_is_even_per_target(self):
        got = cross_zone_share({"a": 2, "b": 8}, True)
        self.assertAlmostEqual(got["a"], 0.1)
        self.assertAlmostEqual(got["b"], 0.1, msg="with cross-zone on, every target gets the same share")

    def test_cross_zone_off_is_even_per_zone(self):
        got = cross_zone_share({"a": 2, "b": 8}, False)
        self.assertAlmostEqual(got["a"], 0.25, msg="each of the 2 zones gets half; a splits it over 2 targets")
        self.assertAlmostEqual(got["b"], 0.0625, msg="b splits its half over 8 targets")
        three = cross_zone_share({"a": 1, "b": 1, "c": 4}, False)
        self.assertAlmostEqual(three["a"], 1 / 3)
        self.assertAlmostEqual(three["c"], 1 / 12)

    def test_a_zone_without_targets(self):
        for cross_zone in (True, False):
            got = cross_zone_share({"a": 2, "b": 0}, cross_zone)
            with self.subTest(cross_zone=cross_zone):
                self.assertEqual(got["b"], 0.0)
                self.assertAlmostEqual(got["a"], 0.5, msg="the empty zone gets no traffic, so the others share everything")

    def test_shares_add_up(self):
        counts = {"a": 3, "b": 5, "c": 2}
        for cross_zone in (True, False):
            got = cross_zone_share(counts, cross_zone)
            with self.subTest(cross_zone=cross_zone):
                self.assertAlmostEqual(sum(got[az] * n for az, n in counts.items()), 1.0)

    def test_bad_counts(self):
        for counts in ({"a": 0, "b": 0}, {}, {"a": -1, "b": 3}):
            with self.subTest(counts=counts):
                with self.assertRaises(ValueError):
                    cross_zone_share(counts, True)

    def test_alb_cost(self):
        self.assertEqual(alb_monthly_cost(10), 74.83)
        self.assertEqual(alb_monthly_cost(0), 16.43)
        self.assertEqual(alb_monthly_cost(0, hours=100), 2.25)

    def test_alb_cost_uses_the_price_argument(self):
        custom = dict(PRICES, alb_per_hour=1.0, alb_per_lcu_hour=0.5)
        self.assertEqual(alb_monthly_cost(5, hours=100, price=custom), 350.0)
        for args in ((-1,), (1, -5)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    alb_monthly_cost(*args)


# ── Exercise 06: A fleet that heals itself ───────────────────────────
"""
latest_ami(ssm) -> str
    The AMI id AWS publishes in the public SSM parameter
    /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64 (Amazon Linux 2023 for Graviton).
    Never hard-code an AMI id: it differs per Region and goes stale. The parameter always points at the latest.
create_web_fleet(ec2, autoscaling, subnet_ids, sg_id, profile_name, ami_id) -> dict
    Build shortly's web fleet and return {"launch_template_id": …, "asg_name": "shortly-web"}.
    Launch template "shortly-web":
      ImageId ami_id · InstanceType "t4g.small" (Graviton: cheaper, see drill 1) ·
      IamInstanceProfile {"Name": profile_name} · SecurityGroupIds [sg_id] ·
      MetadataOptions HttpTokens "required", HttpPutResponseHopLimit 1, HttpEndpoint "enabled"
      (IMDSv2 only: the token requirement stops a stolen URL from reading the instance's credentials).
    Auto Scaling group "shortly-web":
      launch template at version "$Latest" · MinSize 2, MaxSize 6, DesiredCapacity 2 ·
      VPCZoneIdentifier = ALL the subnet ids joined with "," (one subnet per AZ: that is how it survives an AZ) ·
      HealthCheckType "ELB" · HealthCheckGracePeriod 120 (seconds before health checks start counting)
    A target-tracking scaling policy named "cpu-50" on the group: predefined metric
    ASGAverageCPUUtilization, TargetValue 50.
Hint: ssm.get_parameter(Name=…)["Parameter"]["Value"]; ec2.create_launch_template(LaunchTemplateName=…,
      LaunchTemplateData={…}); autoscaling.create_auto_scaling_group(AutoScalingGroupName=…, LaunchTemplate={
      "LaunchTemplateId": …, "Version": "$Latest"}, …); autoscaling.put_scaling_policy(PolicyType="TargetTrackingScaling",
      TargetTrackingConfiguration={"PredefinedMetricSpecification": {"PredefinedMetricType": …}, "TargetValue": …}).
"""
AMI_PARAMETER = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"


def latest_ami(ssm):
    raise NotImplementedError  # YOUR CODE


def create_web_fleet(ec2, autoscaling, subnet_ids, sg_id, profile_name, ami_id):
    raise NotImplementedError  # YOUR CODE


from _harness.awslib import ec2types as _ref_types  # noqa: E402


class Ex06(Drill):
    """A fleet that heals itself"""
    tasks = ("2.2", "3.2")
    uses_aws = True

    def make(self):
        ec2, autoscaling, ssm = self.client("ec2"), self.client("autoscaling"), self.client("ssm")
        vpc = ec2.create_vpc(CidrBlock="10.60.0.0/16")["Vpc"]["VpcId"]
        subnets = [ec2.create_subnet(VpcId=vpc, CidrBlock=f"10.60.{i}.0/24", AvailabilityZone=az)["Subnet"]["SubnetId"]
                   for i, az in enumerate(("us-east-1a", "us-east-1b"))]
        sg = ec2.create_security_group(GroupName="shortly-app", Description="app", VpcId=vpc)["GroupId"]
        ami = ssm.get_parameter(Name=AMI_PARAMETER)["Parameter"]["Value"]
        out = create_web_fleet(ec2, autoscaling, subnets, sg, "shortly-app-profile", ami)
        return ec2, autoscaling, subnets, sg, ami, out

    def template(self, ec2, out):
        versions = ec2.describe_launch_template_versions(LaunchTemplateId=out["launch_template_id"], Versions=["$Latest"])
        return versions["LaunchTemplateVersions"][0]["LaunchTemplateData"]

    def group(self, autoscaling):
        return autoscaling.describe_auto_scaling_groups(AutoScalingGroupNames=["shortly-web"])["AutoScalingGroups"][0]

    def test_latest_ami(self):
        ssm = self.client("ssm")
        self.assertEqual(latest_ami(ssm), ssm.get_parameter(Name=AMI_PARAMETER)["Parameter"]["Value"])
        self.assertTrue(latest_ami(ssm).startswith("ami-"))

    def test_returns_the_ids(self):
        ec2, autoscaling, *_, out = self.make()
        self.assertEqual(set(out), {"launch_template_id", "asg_name"})
        self.assertEqual(out["asg_name"], "shortly-web")
        names = [t["LaunchTemplateName"] for t in ec2.describe_launch_templates(LaunchTemplateIds=[out["launch_template_id"]])["LaunchTemplates"]]
        self.assertEqual(names, ["shortly-web"])

    def test_launch_template_is_graviton_and_imdsv2_only(self):
        ec2, _, _, sg, ami, out = self.make()
        data = self.template(ec2, out)
        self.assertEqual((data["ImageId"], data["InstanceType"]), (ami, "t4g.small"))
        self.assertEqual(_ref_types.decode(data["InstanceType"])["processor"], "AWS Graviton")
        self.assertEqual(data["IamInstanceProfile"]["Name"], "shortly-app-profile")
        self.assertEqual(data["SecurityGroupIds"], [sg])
        meta = data["MetadataOptions"]
        self.assertEqual(meta["HttpTokens"], "required", "IMDSv2 only: a token is required to read instance metadata")
        self.assertEqual((meta["HttpPutResponseHopLimit"], meta["HttpEndpoint"]), (1, "enabled"))

    def test_group_size_and_zones(self):
        ec2, autoscaling, subnets, _, _, out = self.make()
        group = self.group(autoscaling)
        self.assertEqual((group["MinSize"], group["MaxSize"], group["DesiredCapacity"]), (2, 6, 2))
        self.assertEqual(set(group["VPCZoneIdentifier"].split(",")), set(subnets), "the group must use a subnet in every AZ")
        self.assertEqual(len(group["Instances"]), 2, "two instances should be launched")

    def test_group_uses_the_template_and_elb_health(self):
        _, autoscaling, _, _, _, out = self.make()
        group = self.group(autoscaling)
        launch = group["LaunchTemplate"]
        self.assertEqual((launch["LaunchTemplateId"], launch["Version"]), (out["launch_template_id"], "$Latest"))
        self.assertEqual(group["HealthCheckType"], "ELB", "replace instances the load balancer calls unhealthy, not only dead ones")
        self.assertEqual(group["HealthCheckGracePeriod"], 120)

    def test_cpu_target_tracking_policy(self):
        _, autoscaling, *_ = self.make()
        policies = autoscaling.describe_policies(AutoScalingGroupName="shortly-web")["ScalingPolicies"]
        self.assertEqual([p["PolicyName"] for p in policies], ["cpu-50"])
        self.assertEqual(policies[0]["PolicyType"], "TargetTrackingScaling")
        config = policies[0]["TargetTrackingConfiguration"]
        self.assertEqual(config["PredefinedMetricSpecification"]["PredefinedMetricType"], "ASGAverageCPUUtilization")
        self.assertEqual(config["TargetValue"], 50.0)


# ── Exercise 07: A load balancer with rules ──────────────────────────
"""
build_alb(elbv2, vpc_id, subnet_ids, sg_id) -> {"lb_arn": …, "tg_arn": …, "listener_arn": …}
    Target group "shortly-app": protocol HTTP, port 8000, in the VPC, target type "instance",
    health check path "/healthz", success codes (Matcher HttpCode) "200".
    Load balancer "shortly-alb": type "application", scheme "internet-facing", in the subnets,
    with the security group.
    Listener on HTTP port 80 whose DEFAULT action forwards to the target group.
    Two rules on that listener:
      priority 10  path-pattern /healthz → a fixed response: status 404, content type text/plain,
                   body "not found"  (the health check hits the instances directly; the internet
                   has no business reading it through the load balancer)
      priority 20  path-pattern /api/*   → forward to the target group
    Why numbers like 10 and 20? Leave gaps so a rule can be slipped in between later.
Note: moto lists rules in creation order and keeps every field you sent. Real AWS lists them by priority.
Hint: elbv2.create_target_group(Name=…, Protocol=…, Port=…, VpcId=…, TargetType=…, HealthCheckPath=…,
      Matcher={"HttpCode": "200"}); create_load_balancer(Name=…, Subnets=…, SecurityGroups=…, Scheme=…, Type=…);
      create_listener(LoadBalancerArn=…, Protocol="HTTP", Port=80, DefaultActions=[{"Type": "forward", "TargetGroupArn": …}]);
      create_rule(ListenerArn=…, Priority=10, Conditions=[{"Field": "path-pattern", "Values": ["/healthz"]}],
      Actions=[{"Type": "fixed-response", "FixedResponseConfig": {…}}]).
"""
def build_alb(elbv2, vpc_id, subnet_ids, sg_id):
    raise NotImplementedError  # YOUR CODE


from _harness.awslib import elb as _ref_elb  # noqa: E402


class Ex07(Drill):
    """A load balancer with rules"""
    tasks = ("2.1", "2.2")
    uses_aws = True

    def make(self):
        ec2, elbv2 = self.client("ec2"), self.client("elbv2")
        vpc = ec2.create_vpc(CidrBlock="10.70.0.0/16")["Vpc"]["VpcId"]
        subnets = [ec2.create_subnet(VpcId=vpc, CidrBlock=f"10.70.{i}.0/24", AvailabilityZone=az)["Subnet"]["SubnetId"]
                   for i, az in enumerate(("us-east-1a", "us-east-1b"))]
        sg = ec2.create_security_group(GroupName="shortly-alb", Description="alb", VpcId=vpc)["GroupId"]
        return elbv2, vpc, subnets, sg, build_alb(elbv2, vpc, subnets, sg)

    def rules(self, elbv2, out):
        found = elbv2.describe_rules(ListenerArn=out["listener_arn"])["Rules"]
        return sorted((r for r in found if not r.get("IsDefault") and r["Priority"] != "default"), key=lambda r: int(r["Priority"]))

    def as_model(self, elbv2, out):
        """Turn the rules read back from (fake) AWS into the drill-04 rule format."""
        def action(actions):
            first = actions[0]
            if first["Type"] == "fixed-response":
                return f"fixed-response {first['FixedResponseConfig']['StatusCode']}"
            return "forward"
        model = []
        for rule in self.rules(elbv2, out):
            conditions = []
            for cond in rule["Conditions"]:
                values = cond.get("Values") or cond.get("PathPatternConfig", {}).get("Values")
                conditions.append({"field": cond["Field"], "values": values})
            model.append({"priority": int(rule["Priority"]), "conditions": conditions, "action": action(rule["Actions"])})
        return model + [{"priority": "default", "action": "forward"}]

    def test_target_group(self):
        elbv2, vpc, _, _, out = self.make()
        tg = elbv2.describe_target_groups(TargetGroupArns=[out["tg_arn"]])["TargetGroups"][0]
        self.assertEqual((tg["TargetGroupName"], tg["Protocol"], tg["Port"], tg["VpcId"], tg["TargetType"]),
                         ("shortly-app", "HTTP", 8000, vpc, "instance"))
        self.assertEqual(tg["HealthCheckPath"], "/healthz")
        self.assertEqual(tg["Matcher"]["HttpCode"], "200")

    def test_load_balancer(self):
        elbv2, _, subnets, sg, out = self.make()
        lb = elbv2.describe_load_balancers(LoadBalancerArns=[out["lb_arn"]])["LoadBalancers"][0]
        self.assertEqual((lb["LoadBalancerName"], lb["Type"], lb["Scheme"]), ("shortly-alb", "application", "internet-facing"))
        self.assertEqual(lb["SecurityGroups"], [sg])
        self.assertEqual({z["SubnetId"] for z in lb["AvailabilityZones"]}, set(subnets), "put the load balancer in a subnet of every AZ")

    def test_listener_forwards_by_default(self):
        elbv2, _, _, _, out = self.make()
        listener = elbv2.describe_listeners(ListenerArns=[out["listener_arn"]])["Listeners"][0]
        self.assertEqual((listener["Protocol"], listener["Port"], listener["LoadBalancerArn"]), ("HTTP", 80, out["lb_arn"]))
        default = listener["DefaultActions"][0]
        self.assertEqual((default["Type"], default["TargetGroupArn"]), ("forward", out["tg_arn"]))

    def test_the_two_rules(self):
        elbv2, _, _, _, out = self.make()
        rules = self.rules(elbv2, out)
        self.assertEqual([r["Priority"] for r in rules], ["10", "20"], "exactly two numbered rules, priority 10 and 20")
        healthz, api = rules
        self.assertEqual(healthz["Conditions"][0]["Field"], "path-pattern")
        fixed = healthz["Actions"][0]
        self.assertEqual(fixed["Type"], "fixed-response", "/healthz must be answered by the load balancer itself")
        self.assertEqual((fixed["FixedResponseConfig"]["StatusCode"], fixed["FixedResponseConfig"]["ContentType"],
                          fixed["FixedResponseConfig"]["MessageBody"]), ("404", "text/plain", "not found"))
        self.assertEqual((api["Actions"][0]["Type"], api["Actions"][0]["TargetGroupArn"]), ("forward", out["tg_arn"]))

    def test_requests_are_routed_as_intended(self):
        elbv2, _, _, _, out = self.make()
        model = self.as_model(elbv2, out)
        for request, want in (({"method": "GET", "path": "/healthz"}, "fixed-response 404"),
                              ({"method": "POST", "path": "/api/links"}, "forward"),
                              ({"method": "GET", "path": "/Ab3dE9x"}, "forward")):
            with self.subTest(request=request):
                self.assertEqual(_ref_elb.match_rule(request, model), want)
        self.assertEqual([r["field"] for rule in model[:-1] for r in rule["conditions"]], ["path-pattern", "path-pattern"])


# ── Exercise 08 (fix the bug): Settings that bite ────────────────────
"""
shortly's web fleet sits behind an Application Load Balancer. fleet_settings(subnet_ids,
launch_template_id) returns the settings for the launch template ("launch_template_data") and the
Auto Scaling group ("asg"). It works — and it is wrong in five ways. The team reports:
  - Security found that a bug in the app (an SSRF) let a visitor fetch the instance's temporary
    credentials from the metadata service.
  - A deploy shipped an app that crashes on start. Every instance showed "running" and all
    status checks passed, yet the load balancer sent users 502 errors for hours and nothing was replaced.
  - New instances take about 90 seconds to boot and pass their first health check. During a scale-out
    they keep being terminated and replaced before they ever serve a request.
  - When one Availability Zone had an outage the whole site went down.
  - With a single instance, any restart or failed check is an outage: there is no high availability.
Fix fleet_settings (keep everything that already works: the group size limits, the launch template
reference and the target group). The tests name each symptom, and one test builds the fleet in moto.
Hint: read the symptoms as settings — one metadata option, two health-check settings, one list of
      subnets, one minimum. Do not weaken anything else.
"""
TARGET_GROUP_ARN = "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/shortly-app/0123456789abcdef"


def fleet_settings(subnet_ids, launch_template_id):
    return {
        "launch_template_data": {
            "InstanceType": "t4g.small",
            "MetadataOptions": {"HttpTokens": "optional", "HttpPutResponseHopLimit": 1, "HttpEndpoint": "enabled"},
        },
        "asg": {
            "MinSize": 1, "MaxSize": 6, "DesiredCapacity": 1,
            "LaunchTemplate": {"LaunchTemplateId": launch_template_id, "Version": "$Latest"},
            "VPCZoneIdentifier": subnet_ids[0],
            "TargetGroupARNs": [TARGET_GROUP_ARN],
            "HealthCheckType": "EC2",
            "HealthCheckGracePeriod": 0,
        },
    }


class Ex08(Drill):
    """Settings that bite (fix the bug)"""
    tasks = ("1.2", "2.2")
    uses_aws = True
    SUBNETS = ["subnet-0a1", "subnet-0b2", "subnet-0c3"]

    def settings(self):
        return fleet_settings(self.SUBNETS, "lt-0abc")

    def test_instance_metadata_needs_a_token(self):
        meta = self.settings()["launch_template_data"]["MetadataOptions"]
        self.assertEqual(meta["HttpTokens"], "required",
                         "symptom: credentials stolen through the metadata service — require IMDSv2 tokens")
        self.assertEqual(meta["HttpEndpoint"], "enabled", "keep the metadata service on: the instance still needs its role credentials")

    def test_the_load_balancer_check_counts(self):
        asg = self.settings()["asg"]
        self.assertTrue(asg["TargetGroupARNs"], "keep the target group")
        self.assertEqual(asg["HealthCheckType"], "ELB",
                         "symptom: a crashed app was never replaced — EC2 status checks cannot see an app that has crashed")

    def test_new_instances_get_time_to_boot(self):
        grace = self.settings()["asg"]["HealthCheckGracePeriod"]
        self.assertGreaterEqual(grace, 90, "symptom: instances killed while booting — the grace period must cover the boot time")
        self.assertLessEqual(grace, 600, "a grace period of many minutes also hides a broken instance for too long")

    def test_every_zone_is_used(self):
        zones = self.settings()["asg"]["VPCZoneIdentifier"]
        self.assertEqual(set(zones.split(",")), set(self.SUBNETS), "symptom: one AZ outage took everything — use all the subnets")
        self.assertIsInstance(zones, str, "VPCZoneIdentifier is one string, ids joined with commas")

    def test_at_least_two_instances(self):
        asg = self.settings()["asg"]
        self.assertGreaterEqual(asg["MinSize"], 2, "symptom: one instance is no high availability — keep at least two running")
        self.assertGreaterEqual(asg["DesiredCapacity"], asg["MinSize"])

    def test_nothing_else_changed(self):
        asg = self.settings()["asg"]
        self.assertEqual(self.settings()["launch_template_data"]["MetadataOptions"]["HttpTokens"], "required",
                         "fix the bugs first; then this test checks that you did not break anything else")
        self.assertEqual(asg["MaxSize"], 6)
        self.assertEqual(asg["LaunchTemplate"], {"LaunchTemplateId": "lt-0abc", "Version": "$Latest"})
        self.assertEqual(self.settings()["launch_template_data"]["InstanceType"], "t4g.small")
        self.assertEqual(self.settings()["launch_template_data"]["MetadataOptions"]["HttpPutResponseHopLimit"], 1)

    def test_the_settings_create_a_fleet(self):
        ec2, autoscaling, elbv2, ssm = (self.client(s) for s in ("ec2", "autoscaling", "elbv2", "ssm"))
        vpc = ec2.create_vpc(CidrBlock="10.80.0.0/16")["Vpc"]["VpcId"]
        subnets = [ec2.create_subnet(VpcId=vpc, CidrBlock=f"10.80.{i}.0/24", AvailabilityZone=az)["Subnet"]["SubnetId"]
                   for i, az in enumerate(("us-east-1a", "us-east-1b"))]
        tg = elbv2.create_target_group(Name="shortly-app", Protocol="HTTP", Port=8000, VpcId=vpc)["TargetGroups"][0]["TargetGroupArn"]
        ami = ssm.get_parameter(Name=AMI_PARAMETER)["Parameter"]["Value"]
        data = dict(fleet_settings(subnets, "lt-placeholder")["launch_template_data"], ImageId=ami)
        lt = ec2.create_launch_template(LaunchTemplateName="shortly-web", LaunchTemplateData=data)["LaunchTemplate"]["LaunchTemplateId"]
        asg = dict(fleet_settings(subnets, lt)["asg"], TargetGroupARNs=[tg])
        autoscaling.create_auto_scaling_group(AutoScalingGroupName="shortly-web", **asg)
        group = autoscaling.describe_auto_scaling_groups(AutoScalingGroupNames=["shortly-web"])["AutoScalingGroups"][0]
        want = fleet_settings(subnets, lt)
        self.assertEqual(group["MaxSize"], want["asg"]["MaxSize"])
        self.assertEqual(len(group["Instances"]), group["DesiredCapacity"])
        self.assertGreaterEqual(len(group["Instances"]), 2, "a real fleet starts with at least two instances")
        got = ec2.describe_launch_template_versions(LaunchTemplateId=lt, Versions=["$Latest"])["LaunchTemplateVersions"][0]
        self.assertEqual(got["LaunchTemplateData"]["MetadataOptions"], want["launch_template_data"]["MetadataOptions"])
        self.assertEqual((group["HealthCheckType"], group["HealthCheckGracePeriod"]),
                         (want["asg"]["HealthCheckType"], want["asg"]["HealthCheckGracePeriod"]))
        self.assertEqual(set(group["VPCZoneIdentifier"].split(",")), set(subnets), "the group must really sit in every subnet")


# ── Exercise 09 (decide): Where should these instances live? ─────────
"""
Placement groups control WHERE instances sit on AWS hardware. Choose one for each scenario:
  "cluster"    packed close together in one AZ: lowest latency, highest network throughput, one failure can hit all
  "spread"     each instance on distinct hardware (its own rack): at most 7 running instances per AZ per group
  "partition"  groups of instances on separate racks, and you can see which instance sits in which partition:
               for big, rack-aware systems (HDFS, HBase, Cassandra, Kafka); at most 7 partitions per AZ
  "none"       no placement group at all: the default, and EC2 already tries to spread instances out
Replace every None in PLACEMENT with one of those words.
Then choose a purchasing option for each scenario in PURCHASE:
  "on-demand", "savings plan", "reserved instance", "spot", "dedicated host", "capacity reservation"
Last, write max_spread_instances(azs) -> int: how many instances a spread placement group can hold
across `azs` AZs (7 running instances per AZ). Fewer than 1 AZ → ValueError.
    max_spread_instances(3) == 21
(The answers are stored as hashes, so reading the test will not give them away.)
"""
PLACEMENT_SCENARIOS = {
    1: "A 16-node tightly coupled HPC job that needs the lowest possible network latency between nodes.",
    2: "Three critical instances (a primary, a standby and a witness) must never share the same hardware.",
    3: "A 60-node HDFS/HBase cluster whose software is rack-aware and needs to know which rack each node is on.",
    4: "Twelve critical instances over 2 AZs, each one on its own hardware, so one rack failure loses at most one.",
    5: "A stateless web fleet behind an ALB in an Auto Scaling group.",
    6: "Thirty Kafka brokers in one AZ whose replicas must be kept on different racks.",
}
PURCHASE_SCENARIOS = {
    1: "A steady 24/7 baseline for 3 years, while the team plans to move between instance families and towards Lambda.",
    2: "A nightly video-transcoding batch that can restart from checkpoints.",
    3: "Software licensed per physical core, which must run on a server where you can see the sockets and cores.",
    4: "A two-week product launch that must be sure of capacity in one AZ, with no long commitment.",
}
PLACEMENT = {n: None for n in PLACEMENT_SCENARIOS}   # YOUR ANSWERS: "cluster", "spread", "partition" or "none"
PURCHASE = {n: None for n in PURCHASE_SCENARIOS}     # YOUR ANSWERS: see the list in the docstring
PLACEMENT_DIGESTS = {
    1: "99aa07b819862d92e2d455679c5fd64ec8f05c6bd94fad4faf6f82e4323844f9",
    2: "4a2e634ba8048c5ffdee09d38c9b4902bebd7e1254767cacf59686ca9e2a013b",
    3: "68803df9e7ad9014032b7d2aefbcd67d40571de95ad4c1d09ecc477b7e2e9659",
    4: "1c98624b52516fac1c51d43c0ff02f75e8aaaa040e8478987ee5a21a7acbabaf",
    5: "bf59fa373098491dfb6816f0a1c671ecc92e559010a80b7cf0d795757501991d",
    6: "ed2400e3757fccb437c02cc6efbe65a7297b679b43e68346e40a53cf5fb79c6a",
}
PURCHASE_DIGESTS = {
    1: "037a90c81ae22195bdbe8ddbb2dfacda13d376dc086b0f6a8a7b1bb386bca1e4",
    2: "8fad2a8b4478ea5a35a6965fd3fd641b9f8cf56f9fd06b599f68cf0e157414bc",
    3: "205cd608e6e3bfdbdd6d73bb68075f8d715931e7b0086841280d1f929c6bebc1",
    4: "5bda520c2543fd0ad0b68d9e1621cc09a980a415b550fcc2ce9407f8e2708f7b",
}


def max_spread_instances(azs):
    raise NotImplementedError  # YOUR CODE


class Ex09(Drill):
    """Where should these instances live? (decide)"""
    tasks = ("3.2", "4.2")
    STRATEGIES = ("cluster", "spread", "partition", "none")
    OPTIONS = ("on-demand", "savings plan", "reserved instance", "spot", "dedicated host", "capacity reservation")

    def test_placement(self):
        for n, story in PLACEMENT_SCENARIOS.items():
            with self.subTest(scenario=n):
                value = PLACEMENT.get(n)
                self.assertIn(value, self.STRATEGIES, f"placement {n}: answer one of {self.STRATEGIES}, not {value!r}")
                self.assertHashed(value, f"w03-ex09-p{n}", PLACEMENT_DIGESTS[n],
                                  f"placement {n} ({story}): {value!r} is not right — latency, hardware failure or rack awareness?")

    def test_purchasing(self):
        for n, story in PURCHASE_SCENARIOS.items():
            with self.subTest(scenario=n):
                value = PURCHASE.get(n)
                self.assertIn(value, self.OPTIONS, f"purchase {n}: answer one of {self.OPTIONS}, not {value!r}")
                self.assertHashed(value, f"w03-ex09-b{n}", PURCHASE_DIGESTS[n],
                                  f"purchase {n} ({story}): {value!r} is not right — what does the team need to be flexible or sure of?")

    def test_spread_limit(self):
        for azs, want in {1: 7, 2: 14, 3: 21, 6: 42}.items():
            with self.subTest(azs=azs):
                self.assertEqual(max_spread_instances(azs), want, "7 running instances per AZ per spread group")

    def test_spread_limit_rejects_no_zones(self):
        for azs in (0, -1):
            with self.subTest(azs=azs):
                with self.assertRaises(ValueError):
                    max_spread_instances(azs)


# ── Exercise 10 (predict): What does Auto Scaling do? ────────────────
"""
For each scenario, work out the answer BEFORE running anything and write it in PREDICTIONS.
Answers are whole numbers or the exact words named in each scenario. The test asks the course's
reference models (scaling.py and elb.py) for the truth and shows it when you are wrong.
"""
from _harness.awslib import elb as _ref_lb  # noqa: E402
from _harness.awslib import scaling as _ref_scaling  # noqa: E402

_PRIORITY_RULES = [
    {"priority": 5, "conditions": [{"field": "path-pattern", "values": ["/api/*"]}], "action": "forward api"},
    {"priority": 1, "conditions": [{"field": "host-header", "values": ["admin.*"]}], "action": "fixed-response 403"},
    {"priority": "default", "action": "forward web"},
]
SCENARIOS = {
    1: ("A group has 6 instances, min 2, max 12, with a target-tracking policy at 60% CPU. Average CPU jumps to 75%. How many instances does it want? (a number)",
        ("tracking", 6, 75, 60, 2, 12)),
    2: ("The same group, but average CPU falls to 35%. How many instances does it want? (a number)",
        ("tracking", 6, 35, 60, 2, 12)),
    3: ("The group uses EC2 health checks. The app on one instance has crashed, but the instance is running and its status checks pass. Is it replaced? ('yes' or 'no')",
        ("replace", "EC2", True, False)),
    4: ("The same crashed app, but the group uses ELB health checks and the load balancer's check fails. Is it replaced? ('yes' or 'no')",
        ("replace", "ELB", True, False)),
    5: ("Cross-zone load balancing is off. AZ-a has 1 target, AZ-b has 3. What percent of all requests does the AZ-a target receive? (a whole number)",
        ("share", {"a": 1, "b": 3}, "a")),
    6: ("A listener has: priority 5 path /api/* → forward api; priority 1 host admin.* → fixed-response 403; default → forward web. "
        "A request arrives for host admin.shortly.example, path /api/x. Which action answers? ('forward api', 'fixed-response 403' or 'forward web')",
        ("rule", {"host": "admin.shortly.example", "path": "/api/x"}, _PRIORITY_RULES)),
}
PREDICTIONS = {n: None for n in SCENARIOS}   # YOUR ANSWERS: numbers or the exact words


def _truth(kind, *args):
    if kind == "tracking":
        return _ref_scaling.target_tracking(*args)
    if kind == "replace":
        return "yes" if _ref_scaling.replaces_instance(*args) else "no"
    if kind == "share":
        return round(_ref_lb.cross_zone_share(args[0], False)[args[1]] * 100)
    return _ref_lb.match_rule(*args)


class Ex10(Drill):
    """What does Auto Scaling do? (predict)"""
    tasks = ("2.1", "3.2")

    def test_predictions(self):
        for n, (story, scenario) in SCENARIOS.items():
            with self.subTest(scenario=n):
                truth = _truth(*scenario)
                self.assertIsNotNone(PREDICTIONS.get(n), f"scenario {n}: write your answer (a number or the exact words)")
                self.assertEqual(PREDICTIONS[n], truth, f"scenario {n}: {story} — the answer is {truth!r}")


if __name__ == "__main__":
    run()

"""Demo — the scaling and routing rules as small Python models (no boto3, no fake AWS).
1. A day of load through target tracking vs simple scaling with a 300 s cooldown.
2. Cross-zone load balancing on and off with 2 targets in one AZ and 8 in the other.
3. Five requests walked through an Application Load Balancer rule set.
Run it: python concepts/demo_scaling_and_routing.py   (offline; nothing here touches a real account)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.awslib.elb import cross_zone_share, match_rule  # noqa: E402
from _harness.awslib.safety import force_utf8  # noqa: E402
from _harness.awslib.scaling import simple_scaling_run, target_tracking  # noqa: E402

force_utf8()

# ---------------------------------------------------------------- 1. a day of load
# Total demand in "CPU percent summed over the fleet". With 4 instances, a load of 200 means 50 % CPU each.
LOAD_BY_HOUR = [80] * 7 + [160, 280, 400, 400, 400, 520, 520, 400, 400, 400, 300, 200] + [100] * 5
MINIMUM, MAXIMUM, TARGET = 2, 12, 50


def cpu(load: float, instances: int) -> float:
    return min(100.0, load / instances)  # a CPU cannot read more than 100 %


tracking = [MINIMUM]
simple = [MINIMUM]
overloaded = {"tracking": 0, "simple": 0}
for minute in range(24 * 60):
    load = LOAD_BY_HOUR[minute // 60]
    # Target tracking: look at the metric, scale in proportion, round up.
    now = target_tracking(tracking[-1], cpu(load, tracking[-1]), TARGET, MINIMUM, MAXIMUM)
    tracking.append(now)
    # Simple scaling: +1 above 70 %, -1 below 30 %, then ignore alarms for 300 s (5 minutes).
    # The model takes the whole list of readings, so replay the day so far with the reading this minute added.
    readings = [cpu(LOAD_BY_HOUR[m // 60], simple[m]) for m in range(minute)] + [cpu(load, simple[-1])]
    simple.append(simple_scaling_run(readings, MINIMUM, 70, 30, 1, 300, MINIMUM, MAXIMUM)[-1])
    overloaded["tracking"] += load / tracking[-1] > 70
    overloaded["simple"] += load / simple[-1] > 70

print("1. One day, minute by minute. Target tracking at 50 % CPU vs simple scaling (+1 over 70 %, -1 under 30 %, 300 s cooldown)")
print(f"   min {MINIMUM}, max {MAXIMUM}. Desired capacity at the end of the first minute of each hour:\n")
print("   hour  load  tracking  simple   CPU under simple")
for hour in range(24):
    i = hour * 60 + 1
    print(f"   {hour:02d}:00 {LOAD_BY_HOUR[hour]:>5} {tracking[i]:>9} {simple[i]:>7}   {cpu(LOAD_BY_HOUR[hour], simple[i]):>5.0f} %")
print(f"\n   Minutes with fleet CPU above 70 %: target tracking {overloaded['tracking']}, simple scaling {overloaded['simple']}.")
print("   Target tracking jumps straight to the size the load needs. Simple scaling adds one instance, then waits.")

# ---------------------------------------------------------------- 2. cross-zone
print("\n2. Cross-zone load balancing: 2 targets in AZ a, 8 targets in AZ b (share of ALL requests per target)")
for flag in (True, False):
    share = cross_zone_share({"a": 2, "b": 8}, flag)
    label = "on " if flag else "off"
    print(f"   cross-zone {label}: a {share['a']:.2%} each, b {share['b']:.2%} each")
print("   Off: each AZ gets half the traffic, so the 2 targets in a work 4 times harder than the 8 in b.")
print("   An ALB has it on. An NLB has it off, and turning it on adds inter-AZ data transfer charges.")

# ---------------------------------------------------------------- 3. listener rules
RULES = [
    {"priority": 10, "conditions": [{"field": "path-pattern", "values": ["/healthz"]}],
     "action": "fixed-response 200 ok"},
    {"priority": 20, "conditions": [{"field": "path-pattern", "values": ["/api/*"]}],
     "action": "forward to api-tg"},
    {"priority": 25, "conditions": [{"field": "path-pattern", "values": ["/api/v2/*"]}],
     "action": "forward to api-v2-tg"},
    {"priority": 30, "conditions": [{"field": "host-header", "values": ["admin.shop.example"]},
                                    {"field": "source-ip", "values": ["203.0.113.0/24"]}],
     "action": "forward to admin-tg"},
    {"priority": "default", "conditions": [], "action": "forward to web-tg"},
]
REQUESTS = [
    ("GET /healthz on shop.example", {"host": "shop.example", "path": "/healthz", "method": "GET"}),
    ("GET /API/orders (capital letters)", {"host": "shop.example", "path": "/API/orders", "method": "GET"}),
    ("GET / on ADMIN.shop.example from 203.0.113.9",
     {"host": "ADMIN.shop.example", "path": "/", "method": "GET", "source_ip": "203.0.113.9"}),
    ("GET / on admin.shop.example from 198.51.100.7",
     {"host": "admin.shop.example", "path": "/", "method": "GET", "source_ip": "198.51.100.7"}),
    ("GET /api/v2/users", {"host": "shop.example", "path": "/api/v2/users", "method": "GET"}),
]
print("\n3. Five requests through one listener (lowest priority number first, default rule last)")
for rule in RULES:
    shown = ", ".join(f"{c['field']} {c['values']}" for c in rule["conditions"]) or "no conditions"
    print(f"   rule {rule['priority']!s:<8} {shown:<62} -> {rule['action']}")
print()
for text, request in REQUESTS:
    print(f"   {text:<48} -> {match_rule(request, RULES)}")
print("   Notes: path matching is case-sensitive, host matching is not, ALL conditions of a rule must match,")
print("   and rule 25 can never fire because rule 20 matches every /api/ path first.")

print("\nNow do drills 03–05 and 10.")

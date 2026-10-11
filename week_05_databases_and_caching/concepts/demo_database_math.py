"""Demo — the week 05 rules as small Python models (no boto3, no fake AWS).
1. DynamoDB capacity units for item sizes and consistencies.
2. On-demand vs provisioned for two traffic shapes, and the break-even.
3. One event stream through a cache: lazy loading vs write-through.
4. A Lambda connection storm with and without a proxy.
Run it: python concepts/demo_database_math.py   (offline; nothing here touches a real account)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.awslib.caching import simulate  # noqa: E402
from _harness.awslib.dbmath import (  # noqa: E402
    connections_without_proxy, default_max_connections, needs_proxy, peak_concurrency, proxy_pool_size,
)
from _harness.awslib.dynamo import (  # noqa: E402
    break_even_utilisation, monthly_cost_on_demand, monthly_cost_provisioned, provisioned_capacity,
    read_units, write_units,
)
from _harness.awslib.safety import force_utf8  # noqa: E402

force_utf8()

# ---------------------------------------------------------------- 1. capacity units
print("1. Capacity units per request (reads round up to 4 KB, writes to 1 KB)")
print(f"   {'item':>8}  {'eventual':>8}  {'strong':>6}  {'transact.':>9}  {'write':>5}  {'transact. write':>15}")
for kb in (0.3, 1, 3.5, 4, 9, 25):
    print(f"   {kb:>5} KB  {read_units(kb, 'eventual'):>8}  {read_units(kb, 'strong'):>6}  "
          f"{read_units(kb, 'transactional'):>9}  {write_units(kb):>5}  {write_units(kb, transactional=True):>15}")
rcu, wcu = provisioned_capacity(reads_per_second=240, writes_per_second=35, item_kb=7, consistency="strong")
print(f"   240 strong reads/s + 35 writes/s of 7 KB items -> provision {rcu} RCU and {wcu} WCU")

# ---------------------------------------------------------------- 2. on-demand vs provisioned
SECONDS_PER_MONTH = 730 * 3600
print("\n2. On-demand vs provisioned (730-hour month, 2 KB items, eventually consistent reads)")
break_even = break_even_utilisation()
print(f"   break-even utilisation: writes {break_even['writes']:.1%}, reads {break_even['reads']:.1%}"
      "  (below it on-demand is cheaper, above it provisioned is)")
SHAPES = {
    "steady API (flat 200 reads/s, 50 writes/s)": {"avg_reads": 200, "avg_writes": 50, "peak_reads": 220, "peak_writes": 55},
    "nightly batch (avg 20 reads/s, 5 writes/s, peaks 600 / 150)": {"avg_reads": 20, "avg_writes": 5, "peak_reads": 600, "peak_writes": 150},
}
for name, shape in SHAPES.items():
    on_demand = monthly_cost_on_demand(shape["avg_reads"] * SECONDS_PER_MONTH, shape["avg_writes"] * SECONDS_PER_MONTH, 2)
    rcu, wcu = provisioned_capacity(shape["peak_reads"], shape["peak_writes"], 2)
    provisioned = monthly_cost_provisioned(rcu, wcu)
    winner = "on-demand" if on_demand < provisioned else "provisioned"
    print(f"   {name}")
    print(f"     on-demand {on_demand:>9.2f} USD   provisioned for the peak ({rcu} RCU, {wcu} WCU) {provisioned:>9.2f} USD   -> {winner}")
print("   Provisioning for the peak wastes money when the average is far below it. Auto scaling narrows that gap.")

# ---------------------------------------------------------------- 3. cache strategies
print("\n3. One event stream, two strategies (TTL 30 s)")
EVENTS = [(0, "write", "p1", "v1"), (1, "write", "p2", "v1"), (2, "read", "p1"), (3, "read", "p2"), (5, "read", "p1"),
          (10, "write", "p1", "v2"), (12, "read", "p1"), (15, "read", "p2"), (20, "read", "p3"), (25, "read", "p1"),
          (31, "read", "p1"), (40, "write", "p2", "v2"), (42, "read", "p2"), (45, "read", "p1"), (50, "read", "p3")]
print(f"   {'strategy':<14} {'hits':>4} {'misses':>6} {'db reads':>8} {'db writes':>9} {'cache writes':>12} {'stale reads':>11}")
for strategy in ("lazy", "write-through"):
    r = simulate(EVENTS, strategy, ttl=30)
    print(f"   {strategy:<14} {r['hits']:>4} {r['misses']:>6} {r['db_reads']:>8} {r['db_writes']:>9} {r['cache_writes']:>12} {r['stale_reads']:>11}")
print("   Lazy loading serves old values after a write until the TTL runs out. Write-through never does, but it writes the cache on every write.")

# ---------------------------------------------------------------- 4. connection storm
print("\n4. A Lambda connection storm against RDS PostgreSQL")
DB_GIB = 4
limit = default_max_connections("postgres", DB_GIB)
print(f"   a {DB_GIB} GiB PostgreSQL instance: default max_connections about {limit} (real instances are a little lower)")
print(f"   {'requests/s':>10} {'seconds':>8} {'concurrent':>10} {'connections':>11}  {'proxy needed?':<13} {'proxy pool (50 %)':>17}")
for rps, seconds in ((100, 0.3), (300, 0.5), (900, 0.8)):
    conc = peak_concurrency(rps, seconds)
    direct = connections_without_proxy(conc)
    print(f"   {rps:>10} {seconds:>8} {conc:>10} {direct:>11}  {'YES' if needs_proxy(conc, limit) else 'no':<13} {proxy_pool_size(limit, 50):>17}")
print("   Without a proxy every concurrent run opens its own connection. With RDS Proxy the database sees only the pool.")

print("\nNow do drills 01, 02, 06 and 07.")

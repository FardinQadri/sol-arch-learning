"""Demo — storage cost and size rules as small Python models (no boto3, no fake AWS).
1. One dataset priced in every S3 storage class for two access patterns.
2. A log object's journey under a lifecycle rule, day by day (and one rule that AWS would refuse).
3. gp2 against gp3 for the same size and the same IOPS.
4. A multipart plan for a big file, and the prefixes a busy bucket needs.
Run it: python concepts/demo_storage_costs.py   (offline; nothing here touches a real account)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.awslib import ebs, lifecycle, s3cost  # noqa: E402
from _harness.awslib.safety import force_utf8  # noqa: E402

force_utf8()

# ---------------------------------------------------------------- 1. every class, two patterns
PATTERNS = [
    ("A: 30,000 photos of 2 MB (about 59 GB), kept 45 days, 6 GB read back", 30_000, 2048, 45, 6.0),
    ("B: 800,000 sensor files of 48 KB (about 37 GB), kept 400 days, 1 GB read back", 800_000, 48, 400, 1.0),
]
print("1. The same data in every class. Cost = storage for the billable days + retrieval fees (requests left out).")
for title, objects, kb, days, read_gb in PATTERNS:
    print(f"\n   Pattern {title}")
    print("   class          USD     notes")
    for cls in s3cost.CLASSES:
        cost = s3cost.storage_cost(cls, objects, kb, days, read_gb)
        notes = []
        if kb < s3cost.MIN_OBJECT_KB[cls]:
            notes.append(f"each object billed as {s3cost.MIN_OBJECT_KB[cls]} KB")
        if days < s3cost.MIN_DAYS[cls]:
            notes.append(f"billed for {s3cost.MIN_DAYS[cls]} days, not {days}")
        if not s3cost.MILLISECOND_ACCESS[cls]:
            notes.append("must restore before reading")
        if cls in s3cost.SINGLE_AZ:
            notes.append("one AZ only")
        print(f"   {cls:<13} {cost:>7.2f}   {'; '.join(notes)}")
    best, best_cost = s3cost.cheapest_class(objects, kb, days, read_gb)
    print(f"   Cheapest with millisecond access in 3+ AZs: {best} at {best_cost:.2f} USD")
print("\n   Small objects change the answer: the 128 KB minimum makes the IA classes dearer than they look.")
print("   (Intelligent-Tiering is not in this model: it adds a monitoring fee per object and moves data by itself.)")

# ---------------------------------------------------------------- 2. a log object's journey
RULES = [{"ID": "logs", "Status": "Enabled", "Filter": {"Prefix": "logs/"},
          "Transitions": [{"Days": 45, "StorageClass": "STANDARD_IA"}, {"Days": 150, "StorageClass": "GLACIER"}],
          "Expiration": {"Days": 400},
          "NoncurrentVersionExpiration": {"NoncurrentDays": 30}}]
lifecycle.validate(RULES)
print("\n2. Rule: logs/ -> Standard-IA at day 45, Flexible Retrieval at day 150, delete at day 400 (once the rule has run).")
print("   day   5 MB log        40 KB log        old version (day = days since replaced; deleted at 30)")
for day in (0, 29, 30, 44, 45, 149, 150, 399, 400):
    big = lifecycle.current_class(RULES, "logs/app.log", day, 5 * 1024 * 1024)
    tiny = lifecycle.current_class(RULES, "logs/tiny.log", day, 40 * 1024)
    old = lifecycle.noncurrent_fate(RULES, "logs/app.log", day)
    print(f"   {day:>3}   {big:<15} {tiny:<16} {old}")
print("   The 40 KB log never transitions: objects under 128 KB are skipped by default (since September 2024).")
BAD = [{"ID": "too-fast", "Status": "Enabled", "Filter": {},
        "Transitions": [{"Days": 20, "StorageClass": "STANDARD_IA"}, {"Days": 30, "StorageClass": "GLACIER"}]}]
try:
    lifecycle.validate(BAD)
except ValueError as err:
    print(f"\n   A rule AWS would refuse (Standard-IA at day 20, Flexible Retrieval at day 30):\n   {err}")

# ---------------------------------------------------------------- 3. gp2 vs gp3
print("\n3. A database volume that must deliver 6,000 IOPS and 400 MiB/s.")
need_iops = 6000
gp2_size = -(-need_iops // ebs.GP2_IOPS_PER_GIB)  # gp2 gives 3 IOPS per GiB: size the volume for the IOPS
gp2_cost = ebs.monthly_cost("gp2", gp2_size)
print(f"   gp2: 3 IOPS per GiB means {gp2_size:,} GiB just to reach {need_iops:,} IOPS -> {gp2_cost:,.2f} USD a month")
for size in (500, 2000):
    cfg = ebs.gp3_config(size, need_iops, 400)
    cost = ebs.monthly_cost("gp3", size, need_iops, 400)
    print(f"   gp3 at {size:>5,} GiB: {cfg['iops']:,} IOPS, {cfg['throughput']} MiB/s -> {cost:,.2f} USD a month")
print("   gp3 sets size and IOPS separately; gp2 ties them together. Even at the same 2,000 GiB gp3 is cheaper,")
print("   and a 500 GiB gp3 volume does the job for about a third of the gp2 price.")
print(f"   A 12 TiB log-processing volume read in big sequential scans (400 MiB/s): "
      f"{ebs.choose_volume(400, 400, sequential=True)} costs {ebs.monthly_cost('st1', 12 * 1024):,.2f} USD a month; "
      f"gp3 would cost {ebs.monthly_cost('gp3', 12 * 1024, 3000, 400):,.2f}.")

# ---------------------------------------------------------------- 4. multipart and prefixes
print("\n4. Big uploads.")
for label, size in (("80 MiB export", 80 * 1024**2), ("300 MiB export", 300 * 1024**2),("6 GiB backup", 6 * 1024**3), ("3 TiB archive", 3 * 1024**4)):
    plan = s3cost.plan_parts(size)
    how = "multipart" if plan["multipart"] else "one PUT is fine"
    detail = (f"{plan['parts']:,} parts of {plan['part_bytes'] // 1024**2} MiB (last part {plan['last_part_bytes'] / 1024**2:,.0f} MiB)"
              if plan["multipart"] else "")
    print(f"   {label:<14} -> {how:<16} {detail}")
try:
    s3cost.plan_parts(60 * 10**12)
except ValueError as err:
    print(f"   60 TB -> {err}")
print(f"   12,000 GET and 2,000 PUT per second need {s3cost.prefixes_needed(12_000, 2_000)} prefixes "
      "(5,500 GET or 3,500 write per second each).")

print("\nNow do drills 01–04 and 10.")

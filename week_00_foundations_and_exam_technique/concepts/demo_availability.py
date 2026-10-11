"""Demo — what "nines" mean in minutes, and why parallel beats series. Pure Python, no AWS."""
import math
import sys

for stream in (sys.stdout, sys.stderr):
    stream.reconfigure(encoding="utf-8", errors="replace")

print(f"{'availability':>14} {'down per 30 days':>18} {'down per year':>15}")
for a in (0.99, 0.999, 0.9995, 0.9999, 0.99999):
    month = (1 - a) * 30 * 24 * 60
    year = (1 - a) * 365 * 24 * 60
    print(f"{a * 100:>13.3f}% {month:>15.1f} min {year / 60:>12.2f} h")

lb, app, db = 0.9999, 0.99, 0.9995
one_app = math.prod((lb, app, db))
two_apps = math.prod((lb, 1 - (1 - app) ** 2, db))
print(f"\nload balancer → ONE app instance → database:  {one_app:.5f}")
print(f"load balancer → TWO app instances → database:  {two_apps:.5f}   (the database is now the weak link)")
print("\nNow do drills 02–03.")

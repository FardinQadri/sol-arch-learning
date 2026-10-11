"""elb — Application Load Balancer rule matching, cross-zone load balancing and cost.

This is the reference solution for week 03's drills 04–05: finish those drills before you read it.
Rules (docs/research/2026-10-11-compute-facts.md §7): rules are checked in ascending priority and the
default rule last; a rule matches when ALL its conditions match, a condition when ANY of its values
match; up to 3 values per condition and 5 per rule. Host, header and query matching ignore case; path
and method are case-sensitive; `*` matches any run of characters and `?` one character.
"""
from __future__ import annotations

import ipaddress
import re

from . import prices

PRICES = prices.section("ec2")
MAX_VALUES_PER_CONDITION, MAX_VALUES_PER_RULE = 3, 5
MIN_PRIORITY, MAX_PRIORITY = 1, 50000
FIELDS = ("host-header", "path-pattern", "http-request-method", "http-header", "query-string", "source-ip")


def _wild(pattern: str, text: str, *, ignore_case: bool) -> bool:
    regex = "".join(".*" if c == "*" else "." if c == "?" else re.escape(c) for c in pattern)
    return re.fullmatch(regex, text, re.DOTALL | (re.IGNORECASE if ignore_case else 0)) is not None


def _validate(rules: list[dict]) -> list[dict]:
    defaults = [r for r in rules if r.get("priority") == "default"]
    if len(defaults) != 1 or defaults[0].get("conditions"):
        raise ValueError("exactly one rule must have priority 'default' and no conditions")
    numbered = [r for r in rules if r.get("priority") != "default"]
    seen = set()
    for rule in numbered:
        p = rule.get("priority")
        if isinstance(p, bool) or not isinstance(p, int) or not MIN_PRIORITY <= p <= MAX_PRIORITY:
            raise ValueError(f"priority must be an integer from {MIN_PRIORITY} to {MAX_PRIORITY}, got {p!r}")
        if p in seen:
            raise ValueError(f"two rules share priority {p}")
        seen.add(p)
        conditions = rule.get("conditions") or []
        if not conditions:
            raise ValueError(f"rule {p} has no conditions: only the default rule may have none")
        total = 0
        for cond in conditions:
            if cond.get("field") not in FIELDS:
                raise ValueError(f"rule {p}: unknown condition field {cond.get('field')!r}")
            values = cond.get("values") or []
            if not values:
                raise ValueError(f"rule {p}: condition {cond['field']} has no values")
            if len(values) > MAX_VALUES_PER_CONDITION:
                raise ValueError(f"rule {p}: more than {MAX_VALUES_PER_CONDITION} values in one condition")
            total += len(values)
        if total > MAX_VALUES_PER_RULE:
            raise ValueError(f"rule {p}: more than {MAX_VALUES_PER_RULE} values in total")
    return sorted(numbered, key=lambda r: r["priority"]) + defaults


def _condition_matches(cond: dict, request: dict) -> bool:
    field, values = cond["field"], cond["values"]
    if field == "host-header":
        host = request.get("host", "")
        return any(_wild(v, host, ignore_case=True) for v in values)
    if field == "path-pattern":
        path = request.get("path", "").split("?", 1)[0]
        return any(_wild(v, path, ignore_case=False) for v in values)
    if field == "http-request-method":
        return request.get("method", "") in values
    if field == "http-header":
        wanted = cond.get("name", "").lower()
        found = [str(val) for key, val in (request.get("headers") or {}).items() if key.lower() == wanted]
        return any(_wild(v, got, ignore_case=True) for v in values for got in found)
    if field == "query-string":
        pairs = [(str(k), str(v)) for k, v in (request.get("query") or {}).items()]
        for want in values:
            for key, val in pairs:
                if "key" in want and not _wild(want["key"], key, ignore_case=True):
                    continue
                if _wild(want.get("value", "*"), val, ignore_case=True):
                    return True
        return False
    ip = request.get("source_ip")
    if not ip:
        return False
    return any(ipaddress.ip_address(ip) in ipaddress.ip_network(v, strict=False) for v in values)


def match_rule(request: dict, rules: list[dict]):
    """The action of the first rule (lowest priority number first, default last) whose conditions all match."""
    for rule in _validate(rules):
        if all(_condition_matches(c, request) for c in rule.get("conditions") or []):
            return rule["action"]
    raise ValueError("no rule matched")  # unreachable: the default rule has no conditions


def cross_zone_share(targets_per_az: dict[str, int], cross_zone: bool) -> dict[str, float]:
    """Share of all requests that ONE target in each AZ receives (0–1)."""
    if any(n < 0 for n in targets_per_az.values()):
        raise ValueError("target counts must not be negative")
    total = sum(targets_per_az.values())
    if total == 0:
        raise ValueError("there are no targets in any AZ")
    if cross_zone:
        return {az: (1 / total if n else 0.0) for az, n in targets_per_az.items()}
    live = sum(1 for n in targets_per_az.values() if n)
    return {az: (1 / live / n if n else 0.0) for az, n in targets_per_az.items()}


def alb_monthly_cost(lcus: float, hours: int = 730, price: dict = PRICES) -> float:
    """hours * (hourly charge + LCUs * per-LCU-hour charge), rounded to cents."""
    if lcus < 0 or hours < 0:
        raise ValueError("lcus and hours must not be negative")
    return round(hours * (price["alb_per_hour"] + lcus * price["alb_per_lcu_hour"]), 2)

"""dynamo - DynamoDB capacity units and cost: provisioned vs on-demand.

This is the reference solution for week 05's drills 01-02: finish those drills before you read it.
Rules (docs/research/2026-10-12-database-facts.md section 3): an item is at most 400 KB; one read unit
reads up to 4 KB (strongly consistent 1, eventually consistent 0.5, transactional 2); one write unit
writes up to 1 KB (standard 1, transactional 2); item sizes round UP to the next 4 KB / 1 KB.
Provisioned capacity bills every hour whether you use it or not; on-demand bills per request.
Prices come from prices.toml [database] (illustrative). The "first 25 WCU/RCU free" provisioned
allowance is ignored here.
"""
from __future__ import annotations

import math

from . import prices

PRICES = prices.section("database")
MAX_ITEM_KB = 400
READ_UNIT_KB, WRITE_UNIT_KB = 4, 1
READ_FACTOR = {"eventual": 0.5, "strong": 1.0, "transactional": 2.0}
HOURS_PER_MONTH = 730


def _check_size(item_kb: float) -> None:
    if not 0 < item_kb <= MAX_ITEM_KB:
        raise ValueError(f"item size must be above 0 and at most {MAX_ITEM_KB} KB, got {item_kb}")


def read_units(item_kb: float, consistency: str = "eventual") -> float:
    """Read units for one read: 4 KB blocks (rounded up) x 0.5 / 1 / 2.

    >>> read_units(4.1, "strong")
    2.0
    >>> read_units(8)
    1.0
    """
    _check_size(item_kb)
    if consistency not in READ_FACTOR:
        raise ValueError(f"consistency must be one of {sorted(READ_FACTOR)}, got {consistency!r}")
    return math.ceil(item_kb / READ_UNIT_KB) * READ_FACTOR[consistency]


def write_units(item_kb: float, transactional: bool = False) -> int:
    """Write units for one write: 1 KB blocks (rounded up) x 1 (standard) or 2 (transactional).

    >>> write_units(1.5)
    2
    >>> write_units(1.5, transactional=True)
    4
    """
    _check_size(item_kb)
    return math.ceil(item_kb / WRITE_UNIT_KB) * (2 if transactional else 1)


def provisioned_capacity(reads_per_second: float, writes_per_second: float, item_kb: float,
                         consistency: str = "eventual", transactional_writes: bool = False) -> tuple[int, int]:
    """(RCU, WCU) to provision: ceil(reads x read units), ceil(writes x write units).

    >>> provisioned_capacity(100, 50, 6)
    (100, 300)
    """
    if reads_per_second < 0 or writes_per_second < 0:
        raise ValueError("request rates cannot be negative")
    rcu = math.ceil(reads_per_second * read_units(item_kb, consistency))
    wcu = math.ceil(writes_per_second * write_units(item_kb, transactional_writes))
    return rcu, wcu


def monthly_cost_on_demand(reads_per_month: float, writes_per_month: float, item_kb: float,
                           consistency: str = "eventual", transactional_writes: bool = False,
                           price: dict = PRICES) -> float:
    """On-demand cost: request units x price per million. Storage is not included.

    >>> monthly_cost_on_demand(1_000_000, 1_000_000, 1)
    0.6875
    """
    if reads_per_month < 0 or writes_per_month < 0:
        raise ValueError("request counts cannot be negative")
    read_cost = reads_per_month * read_units(item_kb, consistency) / 1e6 * price["dynamodb_on_demand_per_million_reads"]
    write_cost = writes_per_month * write_units(item_kb, transactional_writes) / 1e6 * price["dynamodb_on_demand_per_million_writes"]
    return round(read_cost + write_cost, 4)


def monthly_cost_provisioned(rcu: float, wcu: float, hours: float = HOURS_PER_MONTH, price: dict = PRICES) -> float:
    """Provisioned cost: you pay for every provisioned unit-hour, used or not.

    >>> monthly_cost_provisioned(100, 100)
    56.94
    """
    if rcu < 0 or wcu < 0 or hours < 0:
        raise ValueError("capacity and hours cannot be negative")
    return round(hours * (rcu * price["dynamodb_rcu_hour"] + wcu * price["dynamodb_wcu_hour"]), 4)


def break_even_utilisation(price: dict = PRICES) -> dict:
    """Average fraction of provisioned capacity you must use for provisioned to cost the same as on-demand.

    One unit-hour of provisioned capacity could serve 3,600 units of requests, which on-demand would
    price at 3,600 x (price per million / 1,000,000). Returns {"writes": f, "reads": f}, each rounded
    to 4 decimal places; below that utilisation on-demand is cheaper, above it provisioned is.

    >>> break_even_utilisation()
    {'writes': 0.2889, 'reads': 0.2889}
    """
    w = price["dynamodb_wcu_hour"] / (3600 * price["dynamodb_on_demand_per_million_writes"] / 1e6)
    r = price["dynamodb_rcu_hour"] / (3600 * price["dynamodb_on_demand_per_million_reads"] / 1e6)
    return {"writes": round(w, 4), "reads": round(r, 4)}

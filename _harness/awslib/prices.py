"""prices — the course's illustrative price table (prices.toml). Not a quote: see the file header."""
from __future__ import annotations

import tomllib
from functools import lru_cache
from pathlib import Path

PRICES_FILE = Path(__file__).with_name("prices.toml")


@lru_cache(maxsize=1)
def load() -> dict:
    return tomllib.loads(PRICES_FILE.read_text(encoding="utf-8"))


def section(name: str) -> dict:
    data = load()
    if name not in data:
        raise KeyError(f"prices.toml has no section {name}")
    return data[name]


def tiers(name: str) -> list[tuple[float | None, float]]:
    """[[name]] tables → [(cumulative upper bound or None, price per unit), …]."""
    return [(row.get("up_to_gb"), row["per_gb_month"]) for row in section(name)]


def tiered_cost(quantity: float, tier_list) -> float:
    total, lower = 0.0, 0.0
    for upper, price in tier_list:
        top = quantity if upper is None else min(quantity, upper)
        if top <= lower:
            break
        total += (top - lower) * price
        lower = top
    return total

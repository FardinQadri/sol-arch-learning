"""purchasing — what the same fleet costs under each EC2 purchasing option.

This is the reference solution for week 03's drill 02: finish that drill before you read it.
Rules (docs/research/2026-10-11-compute-facts.md §2): On-Demand and Spot bill only for the hours an
instance runs; Savings Plans and Reserved Instances are commitments billed for every hour of the month.
A Standard RI is locked to an instance type and Region; a Compute Savings Plan follows you to any
family, Region, Fargate or Lambda. Discounts are the course's illustrative figures (prices.toml).
"""
from __future__ import annotations

from . import prices

PRICES = prices.section("ec2")
OPTIONS = ("on-demand", "compute savings plan", "standard reserved", "spot")
_COMMITMENT_DISCOUNT = {"compute savings plan": "compute_savings_plan_discount",
                        "standard reserved": "standard_ri_discount"}


def monthly_cost(option: str, rate: float, instances: int, hours_used: float, *,
                 hours_in_month: int = 730, price: dict = PRICES) -> float:
    """Monthly USD cost. `rate` is the On-Demand price per instance-hour."""
    if option not in OPTIONS:
        raise ValueError(f"unknown purchasing option {option!r}: choose from {OPTIONS}")
    if rate < 0 or instances < 0 or hours_used < 0:
        raise ValueError("rate, instances and hours_used must not be negative")
    if hours_used > hours_in_month:
        raise ValueError(f"hours_used {hours_used} is more than the {hours_in_month} hours in the month")
    if option == "on-demand":
        cost = instances * hours_used * rate
    elif option == "spot":
        cost = instances * hours_used * rate * (1 - price["spot_discount"])
    else:
        cost = instances * hours_in_month * rate * (1 - price[_COMMITMENT_DISCOUNT[option]])
    return round(cost, 2)


def cheapest(rate: float, instances: int, hours_used: float, *, interruptible: bool = False,
             may_change_family: bool = False, hours_in_month: int = 730,
             price: dict = PRICES) -> tuple[str, float]:
    """The cheapest allowed option. A tie keeps the earlier option in OPTIONS."""
    candidates = ["on-demand", "compute savings plan"]
    if not may_change_family:
        candidates.append("standard reserved")
    if interruptible:
        candidates.append("spot")
    costs = [(opt, monthly_cost(opt, rate, instances, hours_used, hours_in_month=hours_in_month, price=price))
             for opt in sorted(candidates, key=OPTIONS.index)]
    best = costs[0]
    for opt, cost in costs[1:]:
        if cost < best[1]:
            best = (opt, cost)
    return best


def break_even_hours(option: str, *, hours_in_month: int = 730, price: dict = PRICES) -> float:
    """Monthly hours of use at which a commitment costs the same as On-Demand."""
    if option not in _COMMITMENT_DISCOUNT:
        raise ValueError(f"{option!r} has no commitment: use 'compute savings plan' or 'standard reserved'")
    return round(hours_in_month * (1 - price[_COMMITMENT_DISCOUNT[option]]), 1)

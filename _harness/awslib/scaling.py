"""scaling — Auto Scaling policy maths: target tracking, step and simple scaling, health checks.

This is the reference solution for week 03's drill 03 (and drill 10): finish those drills before you read it.
Rules (docs/research/2026-10-11-compute-facts.md §6): dynamic scaling never leaves [min, max]; target
tracking scales in direct proportion to load and rounds up; step bounds are offsets from the alarm
threshold (above it: lower inclusive, upper exclusive; below it: lower exclusive, upper inclusive);
simple scaling waits out a cooldown (default 300 s) after each action.
"""
from __future__ import annotations

import math

DEFAULT_COOLDOWN = 300


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def _check_bounds(minimum: int, maximum: int) -> None:
    if minimum < 0 or minimum > maximum:
        raise ValueError(f"need 0 <= minimum <= maximum, got {minimum} and {maximum}")


def target_tracking(current: int, metric: float, target: float, minimum: int, maximum: int) -> int:
    """New desired capacity = ceil(current * metric / target), clamped to [minimum, maximum]."""
    _check_bounds(minimum, maximum)
    if current < 0 or target <= 0:
        raise ValueError("current must not be negative and target must be positive")
    if current == 0:
        return minimum
    return _clamp(math.ceil(round(current * metric / target, 9)), minimum, maximum)


def step_scaling(current: int, metric: float, threshold: float,
                 steps: list[tuple[float | None, float | None, int]], minimum: int, maximum: int) -> int:
    """Apply the step whose interval holds the breach (metric - threshold); no match = no change."""
    _check_bounds(minimum, maximum)
    spans = [(-math.inf if lo is None else lo, math.inf if up is None else up) for lo, up, _ in steps]
    for i, (lo_a, up_a) in enumerate(spans):
        if lo_a >= up_a:
            raise ValueError(f"step {i} has a lower bound that is not below its upper bound")
        for lo_b, up_b in spans[i + 1:]:
            if max(lo_a, lo_b) < min(up_a, up_b):
                raise ValueError("step intervals overlap")
    breach = metric - threshold
    for (lower, upper), (_, _, change) in zip(spans, steps):
        matched = lower <= breach < upper if breach >= 0 else lower < breach <= upper
        if matched:
            return _clamp(current + change, minimum, maximum)
    return _clamp(current, minimum, maximum)


def simple_scaling_run(metrics: list[float], start: int, high: float, low: float, change: int,
                       cooldown: int, minimum: int, maximum: int, period: int = 60) -> list[int]:
    """Desired capacity after each metric sample (one per `period` seconds) under a simple scaling
    policy. An action that really changes the capacity starts a cooldown during which alarms are ignored."""
    _check_bounds(minimum, maximum)
    desired = _clamp(start, minimum, maximum)
    last_action: int | None = None
    history = []
    for t, metric in enumerate(metrics):
        now = t * period
        in_cooldown = last_action is not None and now < last_action + cooldown
        if not in_cooldown:
            if metric > high:
                new = _clamp(desired + change, minimum, maximum)
            elif metric < low:
                new = _clamp(desired - change, minimum, maximum)
            else:
                new = desired
            if new != desired:
                desired, last_action = new, now
        history.append(desired)
    return history


def replaces_instance(health_check_type: str, ec2_ok: bool, elb_ok: bool, in_grace_period: bool = False) -> bool:
    """Whether Auto Scaling replaces the instance. "EC2" looks at the EC2 status checks only; "ELB" also
    at the load balancer's. Inside the grace period nothing is replaced (an instance that has left the
    running state is replaced even then — not modelled)."""
    if health_check_type not in ("EC2", "ELB"):
        raise ValueError(f"unknown health check type {health_check_type!r}: use 'EC2' or 'ELB'")
    if in_grace_period:
        return False
    return not ec2_ok if health_check_type == "EC2" else (not ec2_ok or not elb_ok)

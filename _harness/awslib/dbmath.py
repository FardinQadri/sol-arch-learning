"""dbmath - connection maths: how many connections a Lambda-style workload opens, and RDS Proxy sizing.

This is the reference solution for week 05's drill 07: finish that drill before you read it.
Concurrency by Little's law (requests in flight = rate x duration). max_connections defaults come
from docs/research/2026-10-12-database-facts.md section 1 (RDS CHAP_Limits): MySQL
DBInstanceClassMemory/12582880, PostgreSQL LEAST(DBInstanceClassMemory/9531392, 5000).
The research gives no default for RDS Proxy MaxConnectionsPercent, so proxy_pool_size requires it.
"""
from __future__ import annotations

import math

ENGINES = ("mysql", "postgres")


def _positive(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")


def peak_concurrency(requests_per_second: float, avg_duration_s: float) -> int:
    """Little's law: ceil(rps x duration).

    >>> peak_concurrency(500, 0.2)
    100
    """
    _positive("requests_per_second", requests_per_second)
    _positive("avg_duration_s", avg_duration_s)
    return math.ceil(round(requests_per_second * avg_duration_s, 9))


def connections_without_proxy(concurrency: int, connections_per_invocation: int = 1) -> int:
    """Every concurrent invocation opens its own connection(s) straight to the database.

    >>> connections_without_proxy(100, 2)
    200
    """
    _positive("concurrency", concurrency)
    _positive("connections_per_invocation", connections_per_invocation)
    return concurrency * connections_per_invocation


def needs_proxy(concurrency: int, max_connections: int, connections_per_invocation: int = 1,
                headroom: float = 0.0) -> bool:
    """True when connections exceed max_connections x (1 - headroom).

    >>> needs_proxy(100, 90)
    True
    """
    _positive("max_connections", max_connections)
    if not 0 <= headroom < 1:
        raise ValueError(f"headroom must be from 0 up to (not including) 1, got {headroom}")
    return connections_without_proxy(concurrency, connections_per_invocation) > max_connections * (1 - headroom)


def proxy_pool_size(max_connections: int, max_connections_percent: float) -> int:
    """Connections the proxy may open to the database: floor(max x percent / 100).

    >>> proxy_pool_size(90, 50)
    45
    """
    _positive("max_connections", max_connections)
    if not 0 < max_connections_percent <= 100:
        raise ValueError(f"max_connections_percent must be above 0 and at most 100, got {max_connections_percent}")
    return math.floor(max_connections * max_connections_percent / 100)


def default_max_connections(engine: str, memory_gib: float) -> int:
    """RDS default max_connections, using memory_gib x 2^30 as DBInstanceClassMemory.

    The real DBInstanceClassMemory is a little lower than the nominal memory (the OS and RDS
    management take a share), so real defaults are somewhat below these figures.

    >>> default_max_connections("postgres", 1)
    112
    """
    if engine not in ENGINES:
        raise ValueError(f"engine must be one of {ENGINES}, got {engine!r}")
    _positive("memory_gib", memory_gib)
    memory = memory_gib * 2**30
    if engine == "mysql":
        return int(memory // 12582880)
    return int(min(memory // 9531392, 5000))

"""caching - lazy loading (cache-aside) vs write-through, with TTL and stale reads.

This is the reference solution for week 05's drill 06: finish that drill before you read it.
Strategies follow AWS's ElastiCache caching strategies page (docs/research/2026-10-12-database-facts.md
section 4). Lazy: a miss reads the database and fills the cache; a write touches only the database,
so the cached copy can go stale until it expires. Write-through: a write updates the database AND the
cache, so cached values are never stale, at the cost of caching data that may never be read.
"""
from __future__ import annotations

STRATEGIES = ("lazy", "write-through")


def simulate(events, strategy: str, ttl: float | None = None) -> dict:
    """Replay (time_s, op, key[, value]) events, op "read" or "write", times non-decreasing.

    The database starts empty; reading a key never written returns None and still costs a database
    read on a miss. An entry cached at t expires at t + ttl (None = never); a read at exactly
    t + ttl is a miss. A stale read is a hit whose value differs from the database's current value.

    >>> r = simulate([(0, "write", "k", 1), (1, "read", "k")], "write-through")
    >>> (r["hits"], r["misses"], r["db_writes"], r["cache_writes"])
    (1, 0, 1, 1)
    """
    if strategy not in STRATEGIES:
        raise ValueError(f"strategy must be one of {STRATEGIES}, got {strategy!r}")
    if ttl is not None and ttl <= 0:
        raise ValueError("ttl must be positive or None")
    db: dict = {}
    cache: dict = {}  # key -> (value, expires_at or None)
    out = {"hits": 0, "misses": 0, "db_reads": 0, "db_writes": 0, "stale_reads": 0, "cache_writes": 0}
    last = None

    def put(key, value, now):
        cache[key] = (value, None if ttl is None else now + ttl)
        out["cache_writes"] += 1

    for event in events:
        if len(event) not in (3, 4):
            raise ValueError(f"event must be (time, op, key[, value]), got {event!r}")
        now, op, key = event[0], event[1], event[2]
        if last is not None and now < last:
            raise ValueError(f"event times go backwards: {now} after {last}")
        last = now
        if op == "write":
            if len(event) != 4:
                raise ValueError("a write event needs a value")
            db[key] = event[3]
            out["db_writes"] += 1
            if strategy == "write-through":
                put(key, event[3], now)
        elif op == "read":
            entry = cache.get(key)
            if entry is not None and (entry[1] is None or now < entry[1]):
                out["hits"] += 1
                if entry[0] != db.get(key):
                    out["stale_reads"] += 1
            else:
                out["misses"] += 1
                out["db_reads"] += 1
                put(key, db.get(key), now)
        else:
            raise ValueError(f"op must be 'read' or 'write', got {op!r}")
    return out

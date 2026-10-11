import doctest

import pytest

from _harness.awslib import caching, dbmath, dynamo, prices


def test_doctests():
    for mod in (dynamo, caching, dbmath):
        assert doctest.testmod(mod).failed == 0


# ---------------------------------------------------------------- dynamo
@pytest.mark.parametrize("kb,eventual,strong,trans", [
    (1, 0.5, 1, 2), (4, 0.5, 1, 2), (4.1, 1, 2, 4), (8, 1, 2, 4), (400, 50, 100, 200)])
def test_read_units(kb, eventual, strong, trans):
    assert dynamo.read_units(kb) == eventual
    assert dynamo.read_units(kb, "eventual") == eventual
    assert dynamo.read_units(kb, "strong") == strong
    assert dynamo.read_units(kb, "transactional") == trans


@pytest.mark.parametrize("kb,standard,trans", [(0.5, 1, 2), (1, 1, 2), (1.5, 2, 4), (3, 3, 6), (400, 400, 800)])
def test_write_units(kb, standard, trans):
    assert dynamo.write_units(kb) == standard
    assert dynamo.write_units(kb, transactional=True) == trans


def test_research_rounding_examples():
    assert dynamo.read_units(3, "strong") == 1      # 3 KB read = 1 RCU
    assert dynamo.write_units(0.5) == 1             # 512 byte write = 1 WCU


@pytest.mark.parametrize("kb", [0, -1, 400.1, 401])
def test_item_size_limits(kb):
    with pytest.raises(ValueError):
        dynamo.read_units(kb)
    with pytest.raises(ValueError):
        dynamo.write_units(kb)


def test_unknown_consistency():
    with pytest.raises(ValueError):
        dynamo.read_units(1, "fast")


def test_provisioned_capacity():
    assert dynamo.provisioned_capacity(100, 50, 6) == (100, 300)
    assert dynamo.provisioned_capacity(100, 50, 6, "strong") == (200, 300)
    assert dynamo.provisioned_capacity(100, 50, 6, "transactional", True) == (400, 600)
    assert dynamo.provisioned_capacity(3, 1, 4) == (2, 4)   # ceil(1.5) reads
    with pytest.raises(ValueError):
        dynamo.provisioned_capacity(-1, 1, 1)


def test_on_demand_cost():
    assert dynamo.monthly_cost_on_demand(1_000_000, 1_000_000, 1) == 0.6875
    assert dynamo.monthly_cost_on_demand(2_000_000, 0, 4, "strong") == 0.25
    assert dynamo.monthly_cost_on_demand(0, 1_000_000, 2, transactional_writes=True) == 2.5
    with pytest.raises(ValueError):
        dynamo.monthly_cost_on_demand(-1, 0, 1)


def test_on_demand_custom_price():
    p = {"dynamodb_on_demand_per_million_reads": 1.0, "dynamodb_on_demand_per_million_writes": 2.0}
    assert dynamo.monthly_cost_on_demand(1_000_000, 1_000_000, 1, price=p) == 2.5


def test_provisioned_cost():
    assert dynamo.monthly_cost_provisioned(100, 100) == 56.94
    assert dynamo.monthly_cost_provisioned(0, 0) == 0
    assert dynamo.monthly_cost_provisioned(10, 10, hours=100) == round(100 * 10 * (0.00013 + 0.00065), 4)
    p = {"dynamodb_rcu_hour": 1.0, "dynamodb_wcu_hour": 2.0}
    assert dynamo.monthly_cost_provisioned(1, 1, hours=10, price=p) == 30
    with pytest.raises(ValueError):
        dynamo.monthly_cost_provisioned(-1, 0)


def test_database_prices_section():
    p = prices.section("database")
    assert p["dynamodb_on_demand_per_million_writes"] == 0.625
    assert p["dynamodb_rcu_hour"] == 0.00013
    assert p["rds_proxy_per_vcpu_hour"] == 0.015


def test_break_even_and_crossover():
    assert dynamo.break_even_utilisation() == {"writes": 0.2889, "reads": 0.2889}
    # one WCU kept for the month: provisioned beats on-demand at full use, loses at 10% use
    units_full = 3600 * dynamo.HOURS_PER_MONTH
    prov = dynamo.monthly_cost_provisioned(0, 1)
    assert prov < dynamo.monthly_cost_on_demand(0, units_full, 1)
    assert prov > dynamo.monthly_cost_on_demand(0, units_full * 0.1, 1)
    p = {"dynamodb_wcu_hour": 1.0, "dynamodb_rcu_hour": 1.0,
         "dynamodb_on_demand_per_million_writes": 1e6 / 3600 * 2,
         "dynamodb_on_demand_per_million_reads": 1e6 / 3600}
    assert dynamo.break_even_utilisation(p) == {"writes": 0.5, "reads": 1.0}


# ---------------------------------------------------------------- caching
READ_HEAVY = [(0, "write", "k", "v1"), (1, "read", "k"), (2, "read", "k"), (3, "write", "k", "v2"),
              (4, "read", "k"), (5, "read", "k"), (11, "read", "k")]


def test_lazy_serves_stale_until_ttl():
    r = caching.simulate(READ_HEAVY, "lazy", ttl=10)
    # t=1 miss (fill v1, expires 11), t=2 hit, write v2 (db only), t=4,5 stale hits, t=11 expired -> miss
    assert r == {"hits": 3, "misses": 2, "db_reads": 2, "db_writes": 2, "stale_reads": 2, "cache_writes": 2}


def test_write_through_never_stale():
    r = caching.simulate(READ_HEAVY, "write-through", ttl=10)
    # writes at t=0 and t=3 refresh the cache; t=11 is inside the second entry (expires 13)
    assert r == {"hits": 5, "misses": 0, "db_reads": 0, "db_writes": 2, "stale_reads": 0, "cache_writes": 2}


def test_ttl_boundary_exact():
    ev = [(0, "write", "k", 1), (1, "read", "k"), (11, "read", "k")]
    assert caching.simulate(ev, "lazy", ttl=10)["misses"] == 2      # fill at t=1, expires t=11
    ev = [(0, "write", "k", 1), (0, "read", "k"), (9.99, "read", "k"), (10, "read", "k")]
    r = caching.simulate(ev, "lazy", ttl=10)
    assert (r["hits"], r["misses"]) == (1, 2)                       # fill at 0, hit 9.99, miss at exactly 10


def test_write_through_ttl_expiry_then_reload():
    ev = [(0, "write", "k", 1), (10, "read", "k"), (11, "read", "k")]
    r = caching.simulate(ev, "write-through", ttl=10)
    assert (r["hits"], r["misses"], r["db_reads"], r["cache_writes"]) == (1, 1, 1, 2)


def test_cold_start_and_missing_key():
    r = caching.simulate([(0, "read", "a"), (1, "read", "a"), (2, "read", "b")], "lazy")
    assert (r["hits"], r["misses"], r["db_reads"], r["stale_reads"]) == (1, 2, 2, 0)


def test_no_ttl_stays_stale_forever():
    ev = [(0, "read", "k"), (1, "write", "k", 5), (10**6, "read", "k")]
    assert caching.simulate(ev, "lazy")["stale_reads"] == 1
    assert caching.simulate(ev, "write-through")["stale_reads"] == 0


def test_caching_errors():
    with pytest.raises(ValueError):
        caching.simulate([], "write-back")
    with pytest.raises(ValueError):
        caching.simulate([(0, "delete", "k")], "lazy")
    with pytest.raises(ValueError):
        caching.simulate([(5, "read", "k"), (4, "read", "k")], "lazy")
    with pytest.raises(ValueError):
        caching.simulate([(0, "write", "k")], "lazy")
    with pytest.raises(ValueError):
        caching.simulate([], "lazy", ttl=0)
    assert caching.simulate([], "lazy")["hits"] == 0


# ---------------------------------------------------------------- dbmath
def test_peak_concurrency():
    assert dbmath.peak_concurrency(500, 0.2) == 100
    assert dbmath.peak_concurrency(10, 0.25) == 3
    assert dbmath.peak_concurrency(0.5, 1) == 1


def test_connections_and_needs_proxy():
    assert dbmath.connections_without_proxy(100) == 100
    assert dbmath.connections_without_proxy(100, 2) == 200
    assert dbmath.needs_proxy(100, 90) is True
    assert dbmath.needs_proxy(100, 100) is False
    assert dbmath.needs_proxy(90, 100, headroom=0.2) is True
    assert dbmath.needs_proxy(80, 100, headroom=0.2) is False
    assert dbmath.needs_proxy(60, 100, connections_per_invocation=2) is True


def test_proxy_pool_size():
    assert dbmath.proxy_pool_size(90, 50) == 45
    assert dbmath.proxy_pool_size(85, 50) == 42
    assert dbmath.proxy_pool_size(100, 100) == 100


def test_default_max_connections():
    assert dbmath.default_max_connections("postgres", 1) == 112
    assert dbmath.default_max_connections("mysql", 1) == 85
    assert dbmath.default_max_connections("postgres", 1024) == 5000     # capped
    assert dbmath.default_max_connections("mysql", 8) == 8 * 2**30 // 12582880


@pytest.mark.parametrize("call", [
    lambda: dbmath.peak_concurrency(0, 1), lambda: dbmath.peak_concurrency(1, -1),
    lambda: dbmath.connections_without_proxy(0), lambda: dbmath.connections_without_proxy(1, 0),
    lambda: dbmath.needs_proxy(1, 0), lambda: dbmath.needs_proxy(1, 10, headroom=1),
    lambda: dbmath.needs_proxy(1, 10, headroom=-0.1),
    lambda: dbmath.proxy_pool_size(0, 50), lambda: dbmath.proxy_pool_size(10, 0),
    lambda: dbmath.proxy_pool_size(10, 101),
    lambda: dbmath.default_max_connections("oracle", 1), lambda: dbmath.default_max_connections("mysql", 0)])
def test_dbmath_errors(call):
    with pytest.raises(ValueError):
        call()

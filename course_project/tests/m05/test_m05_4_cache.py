"""M05.4 — the Valkey/Redis cache for hot redirects: subnets, node count, failover, encryption, security group."""
import pytest


def cache(resources, env="prod"):
    res = resources("data", Env=env)
    assert res.get("Cache", {}).get("Type") == "AWS::ElastiCache::ReplicationGroup", \
        "add Cache (AWS::ElastiCache::ReplicationGroup) to infra/data.yaml: a replication group is a primary node plus optional replicas"
    return res["Cache"]["Properties"]


def test_subnet_group(resources):
    group = resources("data").get("CacheSubnetGroup", {})
    assert group.get("Type") == "AWS::ElastiCache::SubnetGroup", "add CacheSubnetGroup (AWS::ElastiCache::SubnetGroup): it tells ElastiCache which subnets the nodes may use"
    props = group["Properties"]
    assert props.get("Description"), "CacheSubnetGroup needs a Description"
    assert props.get("SubnetIds") == ["import:shortly-data-subnet-ids"], "CacheSubnetGroup SubnetIds: !Split [',', !ImportValue {'Fn::Sub': '${Prefix}-data-subnet-ids'}]"
    assert cache(resources).get("CacheSubnetGroupName") == "CacheSubnetGroup", "Cache CacheSubnetGroupName: !Ref CacheSubnetGroup"


def test_engine(resources):
    engine = cache(resources).get("Engine")
    assert engine in ("valkey", "redis"), f"Engine is {engine!r}; use valkey (or redis). Both give sub-millisecond in-memory reads with replicas and failover; memcached has neither"


@pytest.mark.parametrize("env,node_type", [("prod", "cache.m7g.large"), ("lab", "cache.t4g.micro")])
def test_node_type(resources, env, node_type):
    assert cache(resources, env).get("CacheNodeType") == node_type, f"{env} CacheNodeType: {node_type} (!If [IsProd, cache.m7g.large, cache.t4g.micro])"


@pytest.mark.parametrize("env,nodes", [("prod", 2), ("lab", 1)])
def test_node_count(resources, env, nodes):
    value = cache(resources, env).get("NumCacheClusters")
    assert value == nodes, f"{env}: NumCacheClusters is {value!r}; use {nodes} ({'a primary and one replica in another zone' if nodes == 2 else 'a single node is enough in lab'})"


@pytest.mark.parametrize("env,expected", [("prod", True), ("lab", False)])
def test_failover_and_multi_az(resources, env, expected):
    p = cache(resources, env)
    for key in ("AutomaticFailoverEnabled", "MultiAZEnabled"):
        assert p.get(key) is expected, f"{env}: {key} is {p.get(key)!r}; use !If [IsProd, true, false]"
    if p.get("AutomaticFailoverEnabled"):
        assert p.get("NumCacheClusters", 1) >= 2, \
            "failover promotes a replica, so NumCacheClusters must be 2 or more when AutomaticFailoverEnabled is true (cfn-lint does not catch this; CloudFormation fails at deploy time)"


@pytest.mark.parametrize("env", ["prod", "lab"])
def test_encryption(resources, env):
    p = cache(resources, env)
    assert p.get("TransitEncryptionEnabled") is True, f"{env}: set TransitEncryptionEnabled: true. Without TLS, cached redirect targets cross the network in clear text (clients then connect with TLS)"
    assert p.get("AtRestEncryptionEnabled") is True, f"{env}: set AtRestEncryptionEnabled: true. Data on disk (snapshots, node storage) is encrypted"


def test_security_group(resources):
    assert cache(resources).get("SecurityGroupIds") == ["import:shortly-cache-sg-id"], \
        "Cache SecurityGroupIds: [!ImportValue {'Fn::Sub': '${Prefix}-cache-sg-id'}]. The M02 cache security group lets only the app tier reach port 6379"

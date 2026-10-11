import pytest

from _harness.awslib import cidr, netsim
from _harness.awslib.netsim import Host


@pytest.mark.parametrize("block, usable", [("10.0.0.0/24", 251), ("10.0.0.0/28", 11), ("10.0.0.0/16", 65531),
                                           ("10.0.0.0/20", 4091)])
def test_usable_ips(block, usable):
    assert cidr.usable_ips(block) == usable


@pytest.mark.parametrize("bad", ["10.0.0.0/29", "10.0.0.0/15", "10.0.0.1/24", "not-a-cidr", "2001:db8::/64"])
def test_usable_ips_rejects(bad):
    with pytest.raises(ValueError):
        cidr.usable_ips(bad)


def test_reserved_ips():
    assert cidr.reserved_ips("10.0.1.0/24") == ["10.0.1.0", "10.0.1.1", "10.0.1.2", "10.0.1.3", "10.0.1.255"]


@pytest.mark.parametrize("hosts, prefix", [(1, 28), (11, 28), (12, 27), (251, 24), (252, 23), (1000, 22), (65531, 16)])
def test_prefix_for_hosts(hosts, prefix):
    assert cidr.prefix_for_hosts(hosts) == prefix


def test_prefix_for_hosts_too_big():
    with pytest.raises(ValueError):
        cidr.prefix_for_hosts(65532)


def test_plan_subnets_biggest_first_and_aligned():
    plan = cidr.plan_subnets("10.0.0.0/16", {"public": 200, "app": 1000, "data": 100}, ["us-east-1a", "us-east-1b"])
    assert plan == {("app", "us-east-1a"): "10.0.0.0/22", ("app", "us-east-1b"): "10.0.4.0/22",
                    ("public", "us-east-1a"): "10.0.8.0/24", ("public", "us-east-1b"): "10.0.9.0/24",
                    ("data", "us-east-1a"): "10.0.10.0/25", ("data", "us-east-1b"): "10.0.10.128/25"}
    blocks = list(plan.values())
    assert not any(cidr.overlaps(a, b) for i, a in enumerate(blocks) for b in blocks[i + 1:])


def test_plan_subnets_does_not_fit():
    with pytest.raises(ValueError, match="do not fit"):
        cidr.plan_subnets("10.0.0.0/24", {"app": 200}, ["a", "b"])


def test_route_target_longest_prefix():
    routes = {"10.0.0.0/16": "local", "0.0.0.0/0": "igw-1", "10.1.0.0/16": "pcx-1", "10.1.5.0/24": "tgw-1"}
    assert netsim.route_target("10.0.3.4", routes) == "local"
    assert netsim.route_target("8.8.8.8", routes) == "igw-1"
    assert netsim.route_target("10.1.9.9", routes) == "pcx-1"
    assert netsim.route_target("10.1.5.9", routes) == "tgw-1"
    assert netsim.route_target("8.8.8.8", {"10.0.0.0/16": "local"}) is None


SG_ALB = "sg-alb"
SG_APP = "sg-app"


def web_hosts(nacl_in=(netsim.NACL_ALLOW_ALL,), nacl_out=(netsim.NACL_ALLOW_ALL,)):
    alb = Host(ip="10.0.0.10", subnet="public-a", sgs=(SG_ALB,))
    app = Host(ip="10.0.8.20", subnet="app-a", sgs=(SG_APP,),
               sg_in=({"protocol": "tcp", "ports": (8000, 8000), "peer": SG_ALB},),
               nacl_in=nacl_in, nacl_out=nacl_out)
    return alb, app


def test_sg_reference_allows_only_that_group():
    alb, app = web_hosts()
    assert netsim.tcp_connection(alb, app, 8000) == (True, "allowed")
    assert netsim.tcp_connection(alb, app, 22) == (False, "server security group (inbound)")
    stranger = Host(ip="10.0.0.11", subnet="public-a", sgs=("sg-other",))
    assert netsim.tcp_connection(stranger, app, 8000) == (False, "server security group (inbound)")


def test_nacl_order_and_return_traffic():
    deny_alb = ({"rule": 90, "action": "deny", "protocol": "tcp", "ports": (8000, 8000), "cidr": "10.0.0.10/32"},
                netsim.NACL_ALLOW_ALL)
    alb, app = web_hosts(nacl_in=deny_alb)
    assert netsim.tcp_connection(alb, app, 8000) == (False, "server network ACL (inbound)")
    later_deny = (netsim.NACL_ALLOW_ALL,
                  {"rule": 200, "action": "deny", "protocol": "tcp", "ports": (8000, 8000), "cidr": "10.0.0.10/32"})
    alb, app = web_hosts(nacl_in=later_deny)
    assert netsim.tcp_connection(alb, app, 8000) == (True, "allowed")  # rule 100 matched first
    only_8000_out = ({"rule": 100, "action": "allow", "protocol": "tcp", "ports": (8000, 8000), "cidr": "0.0.0.0/0"},)
    alb, app = web_hosts(nacl_out=only_8000_out)
    assert netsim.tcp_connection(alb, app, 8000) == (False, "server network ACL (outbound, reply)")
    ephemeral = ({"rule": 100, "action": "allow", "protocol": "tcp", "ports": (1024, 65535), "cidr": "0.0.0.0/0"},)
    alb, app = web_hosts(nacl_out=ephemeral)
    assert netsim.tcp_connection(alb, app, 8000) == (True, "allowed")


def test_same_subnet_skips_nacls_and_client_egress_counts():
    blocked = ({"rule": 100, "action": "deny", "protocol": "-1", "ports": (0, 65535), "cidr": "0.0.0.0/0"},)
    a = Host(ip="10.0.8.5", subnet="app-a", sgs=("sg-a",), nacl_in=blocked, nacl_out=blocked)
    b = Host(ip="10.0.8.6", subnet="app-a", sgs=("sg-b",), nacl_in=blocked, nacl_out=blocked,
             sg_in=({"protocol": "tcp", "ports": (5432, 5432), "peer": "10.0.8.0/24"},))
    assert netsim.tcp_connection(a, b, 5432) == (True, "allowed")
    no_egress = Host(ip="10.0.8.5", subnet="app-a", sgs=("sg-a",), sg_out=())
    assert netsim.tcp_connection(no_egress, b, 5432) == (False, "client security group (outbound)")


def test_empty_nacl_denies_everything():
    alb, app = web_hosts(nacl_in=())
    assert netsim.tcp_connection(alb, app, 8000) == (False, "server network ACL (inbound)")


def test_peering_and_transit_gateway():
    peerings = [("a", "b"), ("b", "c")]
    assert netsim.can_reach("a", "b", peerings)
    assert not netsim.can_reach("a", "c", peerings)  # not transitive
    assert netsim.can_reach("a", "c", peerings, tgw_attachments=["a", "c", "d"])
    assert netsim.can_reach("a", "a", [])
    assert not netsim.can_reach("a", "d", peerings, tgw_attachments=["d"])
    assert [netsim.peerings_for_full_mesh(n) for n in (0, 1, 2, 5, 10)] == [0, 0, 1, 10, 45]
    assert netsim.can_peer("10.0.0.0/16", "10.1.0.0/16")
    assert not netsim.can_peer("10.0.0.0/16", "10.0.128.0/17")

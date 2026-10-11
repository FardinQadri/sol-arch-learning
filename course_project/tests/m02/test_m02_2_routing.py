"""M02.2 — internet gateway, NAT gateways and route tables. prod: one NAT per AZ; lab: one NAT."""
import pytest

ROUTE_TABLES = {"PublicSubnetA": "PublicRouteTable", "PublicSubnetB": "PublicRouteTable",
                "AppSubnetA": "AppRouteTableA", "AppSubnetB": "AppRouteTableB",
                "DataSubnetA": "DataRouteTable", "DataSubnetB": "DataRouteTable"}


def of_type(res, type_):
    return {name: r for name, r in res.items() if r["Type"] == type_}


def default_routes(res, table):
    return [r["Properties"] for r in of_type(res, "AWS::EC2::Route").values()
            if r["Properties"].get("RouteTableId") == table and r["Properties"].get("DestinationCidrBlock") == "0.0.0.0/0"]


def test_internet_gateway_attached(resources):
    res = resources("network")
    assert res.get("InternetGateway", {}).get("Type") == "AWS::EC2::InternetGateway", "add InternetGateway"
    attachments = [a["Properties"] for a in of_type(res, "AWS::EC2::VPCGatewayAttachment").values()]
    assert {"VpcId": "Vpc", "InternetGatewayId": "InternetGateway"} in [
        {k: a.get(k) for k in ("VpcId", "InternetGatewayId")} for a in attachments], "attach InternetGateway to Vpc"


@pytest.mark.parametrize("env, nats", [("prod", {"NatGatewayA", "NatGatewayB"}), ("lab", {"NatGatewayA"})])
def test_nat_gateways_per_environment(resources, env, nats):
    res = resources("network", Env=env)
    assert set(of_type(res, "AWS::EC2::NatGateway")) == nats, \
        f"Env={env} should create {sorted(nats)} (NatGatewayB only when Env is prod: Condition IsProd)"
    assert res["NatGatewayA"]["Properties"].get("SubnetId") == "PublicSubnetA", "NAT gateways live in public subnets"
    if env == "prod":
        assert res["NatGatewayB"]["Properties"].get("SubnetId") == "PublicSubnetB"
    for nat in of_type(res, "AWS::EC2::NatGateway").values():
        assert str(nat["Properties"].get("AllocationId", "")).endswith(".AllocationId"), \
            "give each NAT gateway an Elastic IP: AllocationId: !GetAtt NatEipA.AllocationId"


def test_subnet_associations(resources):
    res = resources("network")
    pairs = {a["Properties"].get("SubnetId"): a["Properties"].get("RouteTableId")
             for a in of_type(res, "AWS::EC2::SubnetRouteTableAssociation").values()}
    for subnet, table in ROUTE_TABLES.items():
        assert pairs.get(subnet) == table, f"associate {subnet} with {table}"
    for table in set(ROUTE_TABLES.values()):
        assert res.get(table, {}).get("Type") == "AWS::EC2::RouteTable", f"add {table} (AWS::EC2::RouteTable)"


def test_public_routes_to_the_internet_gateway(resources):
    routes = default_routes(resources("network"), "PublicRouteTable")
    assert [r.get("GatewayId") for r in routes] == ["InternetGateway"], "PublicRouteTable: 0.0.0.0/0 → InternetGateway"


@pytest.mark.parametrize("env, b_target", [("prod", "NatGatewayB"), ("lab", "NatGatewayA")])
def test_app_routes_to_nat(resources, env, b_target):
    res = resources("network", Env=env)
    assert [r.get("NatGatewayId") for r in default_routes(res, "AppRouteTableA")] == ["NatGatewayA"]
    assert [r.get("NatGatewayId") for r in default_routes(res, "AppRouteTableB")] == [b_target], \
        f"Env={env}: AppRouteTableB's default route goes to {b_target} (!If [IsProd, …, …])"


def test_data_tier_has_no_way_out(resources):
    res = resources("network")
    routes = [r["Properties"] for r in of_type(res, "AWS::EC2::Route").values() if r["Properties"].get("RouteTableId") == "DataRouteTable"]
    assert not routes, "DataRouteTable gets no routes besides the local one (no internet, no NAT)"

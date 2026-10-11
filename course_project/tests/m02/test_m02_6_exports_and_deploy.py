"""M02.6 — exports for later stacks, lint-clean, and a deploy in moto for both environments."""
import pytest

EXPORTS = {"VpcId": ("shortly-vpc-id", "Vpc"),
           "PublicSubnetIds": ("shortly-public-subnet-ids", "PublicSubnetA,PublicSubnetB"),
           "AppSubnetIds": ("shortly-app-subnet-ids", "AppSubnetA,AppSubnetB"),
           "DataSubnetIds": ("shortly-data-subnet-ids", "DataSubnetA,DataSubnetB"),
           "AlbSecurityGroupId": ("shortly-alb-sg-id", "AlbSecurityGroup"),
           "AppSecurityGroupId": ("shortly-app-sg-id", "AppSecurityGroup"),
           "DbSecurityGroupId": ("shortly-db-sg-id", "DbSecurityGroup"),
           "CacheSecurityGroupId": ("shortly-cache-sg-id", "CacheSecurityGroup")}


def test_exports(outputs):
    out = outputs("network")
    for key, (export, value) in EXPORTS.items():
        assert key in out, f"add Output {key}"
        assert out[key].get("Export", {}).get("Name") == export, f"{key}: Export Name !Sub '${{Prefix}}-{export[8:]}'"
        assert str(out[key].get("Value")).replace(".GroupId", "") == value, f"{key}: Value should be {value}"


def test_lint_clean(lint_errors):
    errors = lint_errors("network")
    assert errors == [], "cfn-lint errors: " + "; ".join(f"line {e['line']} {e['rule']} {e['message']}" for e in errors)


@pytest.mark.parametrize("env, nats", [("prod", 2), ("lab", 1)])
def test_deploys_in_moto(moto_stacks, env, nats):
    import boto3

    assert moto_stacks("network", Env=env) == "CREATE_COMPLETE"
    ec2 = boto3.client("ec2", region_name="us-east-1")
    vpcs = [v for v in ec2.describe_vpcs()["Vpcs"] if v["CidrBlock"] == "10.20.0.0/16"]
    assert len(vpcs) == 1
    vpc = vpcs[0]["VpcId"]
    in_vpc = [{"Name": "vpc-id", "Values": [vpc]}]
    assert len(ec2.describe_subnets(Filters=in_vpc)["Subnets"]) == 6
    live = [n for n in ec2.describe_nat_gateways(Filters=in_vpc)["NatGateways"] if n["State"] == "available"]
    assert len(live) == nats, f"Env={env}: expected {nats} NAT gateway(s)"
    endpoints = ec2.describe_vpc_endpoints(Filters=in_vpc)["VpcEndpoints"]
    assert {e["ServiceName"].rsplit(".", 1)[-1] for e in endpoints} == {"s3", "dynamodb"}

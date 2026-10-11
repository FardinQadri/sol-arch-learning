import boto3
import pytest
from moto import mock_aws

from _harness import labclean

TAG = [{"Key": "saa-course", "Value": "lab"}]
KINDS = ["ec2_instances", "nat_gateways", "elastic_ips", "vpcs"]


@pytest.fixture
def aws(monkeypatch):
    monkeypatch.setattr(labclean, "WAIT_SECONDS", 0)
    with mock_aws():
        yield boto3.Session(region_name="us-east-1")


def tag(ec2, resource_id):
    ec2.create_tags(Resources=[resource_id], Tags=TAG)


def build(ec2, cidr, tagged):
    vpc = ec2.create_vpc(CidrBlock=cidr)["Vpc"]["VpcId"]
    a = ec2.create_subnet(VpcId=vpc, CidrBlock=cidr.replace("0.0/16", "1.0/24"), AvailabilityZone="us-east-1a")["Subnet"]["SubnetId"]
    b = ec2.create_subnet(VpcId=vpc, CidrBlock=cidr.replace("0.0/16", "2.0/24"), AvailabilityZone="us-east-1b")["Subnet"]["SubnetId"]
    igw = ec2.create_internet_gateway()["InternetGateway"]["InternetGatewayId"]
    ec2.attach_internet_gateway(InternetGatewayId=igw, VpcId=vpc)
    rt = ec2.create_route_table(VpcId=vpc)["RouteTable"]["RouteTableId"]
    ec2.create_route(RouteTableId=rt, DestinationCidrBlock="0.0.0.0/0", GatewayId=igw)
    ec2.associate_route_table(RouteTableId=rt, SubnetId=a)
    alb = ec2.create_security_group(GroupName="alb", Description="alb", VpcId=vpc)["GroupId"]
    app = ec2.create_security_group(GroupName="app", Description="app", VpcId=vpc)["GroupId"]
    ec2.authorize_security_group_ingress(GroupId=app, IpPermissions=[{"IpProtocol": "tcp", "FromPort": 8000, "ToPort": 8000,
                                                                      "UserIdGroupPairs": [{"GroupId": alb}]}])
    acl = ec2.create_network_acl(VpcId=vpc)["NetworkAcl"]["NetworkAclId"]
    ec2.create_vpc_endpoint(VpcEndpointType="Gateway", VpcId=vpc, ServiceName="com.amazonaws.us-east-1.s3", RouteTableIds=[rt])
    eip = ec2.allocate_address(Domain="vpc")["AllocationId"]
    nat = ec2.create_nat_gateway(SubnetId=a, AllocationId=eip)["NatGateway"]["NatGatewayId"]
    image = ec2.describe_images(Owners=["amazon"])["Images"][0]["ImageId"]
    instance = ec2.run_instances(ImageId=image, MinCount=1, MaxCount=1, SubnetId=b)["Instances"][0]["InstanceId"]
    if tagged:
        for resource in (vpc, nat, eip, instance):
            tag(ec2, resource)
    return {"vpc": vpc, "nat": nat, "eip": eip, "instance": instance, "acl": acl}


def state(ec2):
    instances = {i["InstanceId"]: i["State"]["Name"] for r in ec2.describe_instances()["Reservations"] for i in r["Instances"]}
    return {"vpcs": {v["VpcId"] for v in ec2.describe_vpcs()["Vpcs"]},
            "eips": {a["AllocationId"] for a in ec2.describe_addresses()["Addresses"]},
            "nats": {n["NatGatewayId"] for n in ec2.describe_nat_gateways()["NatGateways"] if n["State"] == "available"},
            "running": {i for i, s in instances.items() if s != "terminated"}}


def test_dry_run_lists_tagged_only(aws, capsys):
    ec2 = aws.client("ec2")
    lab, mine = build(ec2, "10.60.0.0/16", True), build(ec2, "10.61.0.0/16", False)
    before = state(ec2)
    assert labclean.main(KINDS, ["--region", "us-east-1"], session_factory=lambda **kw: aws) == 0
    assert state(ec2) == before
    out = capsys.readouterr().out
    for resource in ("vpc", "nat", "eip", "instance"):
        assert lab[resource] in out and mine[resource] not in out


def test_deletes_tagged_vpc_and_its_contents_only(aws, capsys):
    ec2 = aws.client("ec2")
    lab, mine = build(ec2, "10.60.0.0/16", True), build(ec2, "10.61.0.0/16", False)
    assert labclean.main(KINDS, ["--region", "us-east-1", "--yes"], session_factory=lambda **kw: aws) == 0
    after = state(ec2)
    assert lab["vpc"] not in after["vpcs"] and mine["vpc"] in after["vpcs"]
    assert lab["eip"] not in after["eips"] and mine["eip"] in after["eips"]
    assert lab["nat"] not in after["nats"] and mine["nat"] in after["nats"]
    assert lab["instance"] not in after["running"] and mine["instance"] in after["running"]
    assert not ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [lab["vpc"]]}])["Subnets"]
    assert ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [mine["vpc"]]}])["Subnets"]
    assert "✔ deleted vpcs" in capsys.readouterr().out


def test_other_region_untouched(aws):
    east, west = aws.client("ec2", region_name="us-east-1"), aws.client("ec2", region_name="eu-west-1")
    vpc_west = west.create_vpc(CidrBlock="10.70.0.0/16")["Vpc"]["VpcId"]
    tag(west, vpc_west)
    labclean.main(KINDS, ["--region", "us-east-1", "--yes"], session_factory=lambda **kw: aws)
    assert vpc_west in {v["VpcId"] for v in west.describe_vpcs()["Vpcs"]}
    labclean.main(KINDS, ["--region", "eu-west-1", "--yes"], session_factory=lambda **kw: aws)
    assert vpc_west not in {v["VpcId"] for v in west.describe_vpcs()["Vpcs"]}

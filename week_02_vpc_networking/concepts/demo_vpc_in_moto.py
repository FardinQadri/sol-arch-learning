"""Demo — a VPC with a public and a private subnet, built with boto3 against a fake AWS (moto).
Shows the routes that make a subnet public, and the route an S3 gateway endpoint adds.
Run it: python concepts/demo_vpc_in_moto.py   (offline; nothing here touches a real account)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.awslib.cidr import reserved_ips  # noqa: E402
from _harness.awslib.safety import force_utf8, use_fake_aws_env  # noqa: E402

force_utf8()
use_fake_aws_env()

import boto3  # noqa: E402
from moto import mock_aws  # noqa: E402

REGION = "us-east-1"


def show_routes(ec2, table_id, label, names):
    table = ec2.describe_route_tables(RouteTableIds=[table_id])["RouteTables"][0]
    print(f"\n{label} ({table_id})")
    for route in table["Routes"]:
        destination = route.get("DestinationCidrBlock") or route.get("DestinationPrefixListId")
        target = route.get("GatewayId") or route.get("NatGatewayId") or "?"
        kind = names.get(target, "")
        print(f"  {destination:<20} → {target:<26} {kind}")
    subnets = [a["SubnetId"] for a in table["Associations"] if a.get("SubnetId")]
    print(f"  associated subnets: {subnets}")


with mock_aws():
    ec2 = boto3.client("ec2", region_name=REGION)

    vpc_id = ec2.create_vpc(CidrBlock="10.0.0.0/16")["Vpc"]["VpcId"]
    public = ec2.create_subnet(VpcId=vpc_id, CidrBlock="10.0.1.0/24", AvailabilityZone="us-east-1a")["Subnet"]
    private = ec2.create_subnet(VpcId=vpc_id, CidrBlock="10.0.2.0/24", AvailabilityZone="us-east-1a")["Subnet"]
    print(f"VPC {vpc_id} 10.0.0.0/16 with a public subnet {public['CidrBlock']} and a private subnet {private['CidrBlock']}")

    igw_id = ec2.create_internet_gateway()["InternetGateway"]["InternetGatewayId"]
    ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)

    # Two custom route tables. The VPC's main route table stays untouched.
    public_rt = ec2.create_route_table(VpcId=vpc_id)["RouteTable"]["RouteTableId"]
    private_rt = ec2.create_route_table(VpcId=vpc_id)["RouteTable"]["RouteTableId"]
    ec2.associate_route_table(RouteTableId=public_rt, SubnetId=public["SubnetId"])
    ec2.associate_route_table(RouteTableId=private_rt, SubnetId=private["SubnetId"])
    # This one route is what makes the public subnet public.
    ec2.create_route(RouteTableId=public_rt, DestinationCidrBlock="0.0.0.0/0", GatewayId=igw_id)

    names = {igw_id: "(internet gateway)", "local": "(the local route)"}

    print("\n--- Before the endpoint ---")
    show_routes(ec2, public_rt, "Public route table", names)
    show_routes(ec2, private_rt, "Private route table", names)

    endpoint = ec2.create_vpc_endpoint(
        VpcId=vpc_id,
        ServiceName=f"com.amazonaws.{REGION}.s3",
        VpcEndpointType="Gateway",
        RouteTableIds=[private_rt],
    )["VpcEndpoint"]
    names[endpoint["VpcEndpointId"]] = "(S3 gateway endpoint)"

    print("\n--- After adding an S3 gateway endpoint to the private table ---")
    show_routes(ec2, private_rt, "Private route table", names)
    print("  The pl-… destination is the S3 prefix list: a managed list of S3's addresses.")
    print("  It is more specific than any default route, so S3 traffic uses the endpoint.")

    cidr = public["CidrBlock"]
    print(f"\nReserved addresses in {cidr} (5 per subnet, you cannot use them):")
    labels = ["network address", "VPC router", "Amazon DNS (base + 2)", "reserved for future use", "broadcast"]
    for ip, label in zip(reserved_ips(cidr), labels):
        print(f"  {ip:<12} {label}")
    print("  A /24 has 256 addresses, so 251 are usable.")

print("\nNow do drills 01, 03 and 06–08.")

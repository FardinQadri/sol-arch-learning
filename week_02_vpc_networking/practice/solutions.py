"""Reference solutions for week 02.

Drills 01–05: the course's reference models ARE the solution — read _harness/awslib/cidr.py and
_harness/awslib/netsim.py and compare them with yours.
"""
import json

from _harness.awslib.cidr import plan_subnets, prefix_for_hosts, reserved_ips, usable_ips  # noqa: F401
from _harness.awslib.netsim import (can_peer, can_reach, nacl_allows, peerings_for_full_mesh,  # noqa: F401
                                    route_target, sg_allows, tcp_connection)


def build_vpc(ec2, cidr, plan):
    vpc = ec2.create_vpc(CidrBlock=cidr)["Vpc"]["VpcId"]
    ec2.modify_vpc_attribute(VpcId=vpc, EnableDnsSupport={"Value": True})
    ec2.modify_vpc_attribute(VpcId=vpc, EnableDnsHostnames={"Value": True})
    subnets = {key: ec2.create_subnet(VpcId=vpc, CidrBlock=block, AvailabilityZone=key[1])["Subnet"]["SubnetId"]
               for key, block in plan.items()}
    igw = ec2.create_internet_gateway()["InternetGateway"]["InternetGatewayId"]
    ec2.attach_internet_gateway(InternetGatewayId=igw, VpcId=vpc)
    public = ec2.create_route_table(VpcId=vpc)["RouteTable"]["RouteTableId"]
    ec2.create_route(RouteTableId=public, DestinationCidrBlock="0.0.0.0/0", GatewayId=igw)
    tables = {"public": public}
    for (tier, az), subnet in subnets.items():
        if tier == "public":
            ec2.associate_route_table(RouteTableId=public, SubnetId=subnet)
            continue
        if az not in tables:
            tables[az] = ec2.create_route_table(VpcId=vpc)["RouteTable"]["RouteTableId"]
        ec2.associate_route_table(RouteTableId=tables[az], SubnetId=subnet)
    return {"vpc": vpc, "igw": igw, "subnets": subnets, "route_tables": tables}


def _tcp(port, **source):
    return {"IpProtocol": "tcp", "FromPort": port, "ToPort": port, **source}


def create_web_sgs(ec2, vpc_id):
    sgs = {role: ec2.create_security_group(GroupName=f"shortly-{role}", Description=f"shortly {role} tier",
                                           VpcId=vpc_id)["GroupId"] for role in ("alb", "app", "db")}
    ec2.authorize_security_group_ingress(GroupId=sgs["alb"], IpPermissions=[_tcp(443, IpRanges=[{"CidrIp": "0.0.0.0/0"}])])
    ec2.authorize_security_group_ingress(GroupId=sgs["app"], IpPermissions=[_tcp(8000, UserIdGroupPairs=[{"GroupId": sgs["alb"]}])])
    ec2.authorize_security_group_ingress(GroupId=sgs["db"], IpPermissions=[_tcp(5432, UserIdGroupPairs=[{"GroupId": sgs["app"]}])])
    return sgs


def add_s3_gateway_endpoint(ec2, vpc_id, route_table_ids, bucket):
    policy = {"Version": "2012-10-17", "Statement": [{
        "Effect": "Allow", "Principal": "*", "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
        "Resource": [f"arn:aws:s3:::{bucket}", f"arn:aws:s3:::{bucket}/*"]}]}
    endpoint = ec2.create_vpc_endpoint(VpcEndpointType="Gateway", VpcId=vpc_id, RouteTableIds=list(route_table_ids),
                                       ServiceName=f"com.amazonaws.{ec2.meta.region_name}.s3",
                                       PolicyDocument=json.dumps(policy))
    return endpoint["VpcEndpoint"]["VpcEndpointId"]


def vpce_only_bucket_policy(bucket, vpce_id):
    return {"Version": "2012-10-17", "Statement": [{
        "Sid": "OnlyThroughOurEndpoint", "Effect": "Deny", "Principal": "*", "Action": "s3:*",
        "Resource": [f"arn:aws:s3:::{bucket}", f"arn:aws:s3:::{bucket}/*"],
        "Condition": {"StringNotEquals": {"aws:SourceVpce": vpce_id}}}]}


def _check(*values):
    if any(v < 0 for v in values):
        raise ValueError("inputs must not be negative")


def nat_monthly_cost(gb, nat_gateways, hours=730, price=PRICES):
    _check(gb, nat_gateways, hours)
    return round(nat_gateways * hours * price["nat_gateway_per_hour"] + gb * price["nat_gateway_per_gb"], 2)


def interface_endpoint_monthly_cost(gb, azs, hours=730, price=PRICES):
    _check(gb, azs, hours)
    return round(azs * hours * price["interface_endpoint_per_hour_per_az"] + gb * price["interface_endpoint_per_gb"], 2)


def s3_path_costs(gb, nat_gateways, azs, hours=730, price=PRICES):
    _check(gb, nat_gateways, azs, hours)
    return {"nat gateway": nat_monthly_cost(gb, nat_gateways, hours, price),
            "interface endpoint": interface_endpoint_monthly_cost(gb, azs, hours, price),
            "gateway endpoint": round(gb * price["gateway_endpoint_per_gb"], 2)}


PREDICTIONS = {1: "no", 2: "yes", 3: "no", 4: "yes", 5: "no", 6: "no"}

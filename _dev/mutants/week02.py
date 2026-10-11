"""Deliberately wrong implementations for week 02 — each must be caught by its drill."""
MUTANTS = [
    {"id": "forgets-reserved", "drill": 1, "code": '''
import ipaddress
from _harness.awslib.cidr import reserved_ips
def usable_ips(cidr):
    net = ipaddress.ip_network(cidr, strict=True)
    if net.version != 4 or not 16 <= net.prefixlen <= 28:
        raise ValueError(cidr)
    return net.num_addresses - 2
'''},
    {"id": "smallest-first", "drill": 2, "code": '''
import ipaddress
from _harness.awslib.cidr import prefix_for_hosts
def plan_subnets(vpc_cidr, tiers, azs):
    vpc = ipaddress.ip_network(vpc_cidr)
    order = sorted(tiers, key=lambda t: -prefix_for_hosts(tiers[t]))
    plan, cursor = {}, int(vpc.network_address)
    for tier in order:
        prefix = prefix_for_hosts(tiers[tier]); size = 2 ** (32 - prefix)
        for az in azs:
            cursor = -(-cursor // size) * size
            if cursor + size - 1 > int(vpc.broadcast_address):
                raise ValueError("no fit")
            plan[(tier, az)] = str(ipaddress.ip_network((cursor, prefix))); cursor += size
    return plan
'''},
    {"id": "first-match", "drill": 3, "code": '''
import ipaddress
def route_target(destination_ip, routes):
    for cidr, target in routes.items():
        if ipaddress.ip_address(destination_ip) in ipaddress.ip_network(cidr):
            return target
    return None
'''},
    {"id": "nacl-is-stateful", "drill": 4, "code": '''
from _harness.awslib.netsim import sg_allows, nacl_allows
def tcp_connection(client, server, port, client_port=49152):
    crosses = client.subnet != server.subnet
    checks = [("client security group (outbound)", sg_allows(client.sg_out, server.ip, server.sgs, "tcp", port))]
    if crosses:
        checks += [("client network ACL (outbound)", nacl_allows(client.nacl_out, server.ip, "tcp", port)),
                   ("server network ACL (inbound)", nacl_allows(server.nacl_in, client.ip, "tcp", port))]
    checks.append(("server security group (inbound)", sg_allows(server.sg_in, client.ip, client.sgs, "tcp", port)))
    for name, ok in checks:
        if not ok:
            return False, name
    return True, "allowed"
'''},
    {"id": "transitive-peering", "drill": 5, "code": '''
from _harness.awslib.netsim import can_peer, peerings_for_full_mesh
def can_reach(source, target, peerings, tgw_attachments=()):
    seen, frontier = {source}, [source]
    while frontier:
        here = frontier.pop()
        for a, b in peerings:
            for x, y in ((a, b), (b, a)):
                if x == here and y not in seen:
                    seen.add(y); frontier.append(y)
    attached = set(tgw_attachments)
    return target in seen or (source in attached and target in attached)
'''},
    {"id": "private-to-igw", "drill": 6, "code": '''
def build_vpc(ec2, cidr, plan):
    vpc = ec2.create_vpc(CidrBlock=cidr)["Vpc"]["VpcId"]
    ec2.modify_vpc_attribute(VpcId=vpc, EnableDnsSupport={"Value": True})
    ec2.modify_vpc_attribute(VpcId=vpc, EnableDnsHostnames={"Value": True})
    subnets = {k: ec2.create_subnet(VpcId=vpc, CidrBlock=b, AvailabilityZone=k[1])["Subnet"]["SubnetId"] for k, b in plan.items()}
    igw = ec2.create_internet_gateway()["InternetGateway"]["InternetGatewayId"]
    ec2.attach_internet_gateway(InternetGatewayId=igw, VpcId=vpc)
    tables = {}
    for (tier, az), subnet in subnets.items():
        key = "public" if tier == "public" else az
        if key not in tables:
            tables[key] = ec2.create_route_table(VpcId=vpc)["RouteTable"]["RouteTableId"]
            ec2.create_route(RouteTableId=tables[key], DestinationCidrBlock="0.0.0.0/0", GatewayId=igw)
        ec2.associate_route_table(RouteTableId=tables[key], SubnetId=subnet)
    return {"vpc": vpc, "igw": igw, "subnets": subnets, "route_tables": tables}
'''},
    {"id": "app-open-to-vpc", "drill": 7, "code": '''
def create_web_sgs(ec2, vpc_id):
    sgs = {r: ec2.create_security_group(GroupName=f"shortly-{r}", Description=r, VpcId=vpc_id)["GroupId"] for r in ("alb", "app", "db")}
    ec2.authorize_security_group_ingress(GroupId=sgs["alb"], IpPermissions=[{"IpProtocol": "tcp", "FromPort": 443, "ToPort": 443, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}])
    ec2.authorize_security_group_ingress(GroupId=sgs["app"], IpPermissions=[{"IpProtocol": "tcp", "FromPort": 8000, "ToPort": 8000, "IpRanges": [{"CidrIp": "10.40.0.0/16"}]}])
    ec2.authorize_security_group_ingress(GroupId=sgs["db"], IpPermissions=[{"IpProtocol": "tcp", "FromPort": 5432, "ToPort": 5432, "UserIdGroupPairs": [{"GroupId": sgs["app"]}]}])
    return sgs
'''},
    {"id": "objects-only", "drill": 8, "code": '''
import json
def add_s3_gateway_endpoint(ec2, vpc_id, route_table_ids, bucket):
    policy = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": "*",
              "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"], "Resource": [f"arn:aws:s3:::{bucket}", f"arn:aws:s3:::{bucket}/*"]}]}
    return ec2.create_vpc_endpoint(VpcEndpointType="Gateway", VpcId=vpc_id, RouteTableIds=list(route_table_ids),
                                   ServiceName=f"com.amazonaws.{ec2.meta.region_name}.s3", PolicyDocument=json.dumps(policy))["VpcEndpoint"]["VpcEndpointId"]
def vpce_only_bucket_policy(bucket, vpce_id):
    return {"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Principal": "*", "Action": "s3:*",
            "Resource": f"arn:aws:s3:::{bucket}/*", "Condition": {"StringNotEquals": {"aws:SourceVpce": vpce_id}}}]}
'''},
    {"id": "forgets-hourly", "drill": 9, "code": '''
def nat_monthly_cost(gb, nat_gateways, hours=730, price=PRICES):
    if min(gb, nat_gateways, hours) < 0:
        raise ValueError("negative")
    return round(gb * price["nat_gateway_per_gb"], 2)
'''},
    {"id": "endpoint-reaches-internet", "drill": 10, "code": '''
PREDICTIONS = {1: "no", 2: "yes", 3: "yes", 4: "yes", 5: "no", 6: "no"}
'''},
]

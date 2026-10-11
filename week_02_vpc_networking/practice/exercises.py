"""
Week 02 drills — VPC networking
===============================
Run:    python practice/exercises.py          every drill
        python practice/exercises.py 4        drill 4 only
Drills 01–05 are pure Python models of how a VPC works: address maths, routing, security groups
vs network ACLs, and how VPCs connect. Drills 06–10 build the real thing with boto3 against moto
(a fake AWS) — nothing here can touch a real account or cost money.
The course's own versions of drills 01–05 (_harness/awslib/cidr.py and netsim.py) are their answer
key — don't open them until you are done.
"""
import ipaddress  # noqa: F401  (you will want it)
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.awsdrill import Drill, run  # noqa: E402
from _harness.awslib import policy_eval as ref_policy  # noqa: E402
from _harness.awslib import prices  # noqa: E402
from _harness.awslib.netsim import ANY_OUT, NACL_ALLOW_ALL, Host  # noqa: E402,F401


# ── Exercise 01 ★: How many addresses can you use? ───────────────────
"""
usable_ips(cidr) -> int
    AWS reserves 5 addresses in every subnet, so a subnet holds (block size − 5) usable addresses.
    Accept only IPv4 network blocks from /16 to /28 (the sizes AWS allows for VPCs and subnets);
    anything else — /29, /15, "10.0.0.1/24" (host bits set), garbage text, IPv6 — → ValueError.
reserved_ips(cidr) -> list[str]
    The 5 reserved addresses in order: network address, +1 (VPC router), +2 (Amazon DNS),
    +3 (reserved for future use), and the last address (broadcast — AWS does not support it).
Examples:
    usable_ips("10.0.1.0/24") == 251      usable_ips("10.0.0.0/28") == 11
    reserved_ips("10.0.1.0/24") == ["10.0.1.0", "10.0.1.1", "10.0.1.2", "10.0.1.3", "10.0.1.255"]
Hint: ipaddress.ip_network(cidr, strict=True) raises ValueError for host bits; .num_addresses,
      .prefixlen, .version and .broadcast_address do the rest.
"""
def usable_ips(cidr):
    raise NotImplementedError  # YOUR CODE


def reserved_ips(cidr):
    raise NotImplementedError  # YOUR CODE


class Ex01(Drill):
    """How many addresses can you use? ★"""
    tasks = ("3.4",)

    def test_usable(self):
        for block, want in {"10.0.1.0/24": 251, "10.0.0.0/28": 11, "172.16.0.0/16": 65531, "10.8.0.0/21": 2043}.items():
            with self.subTest(block=block):
                self.assertEqual(usable_ips(block), want)

    def test_rejects_what_aws_rejects(self):
        for bad in ("10.0.0.0/29", "10.0.0.0/15", "10.0.0.1/24", "ten-dot-zero", "2001:db8::/64"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    usable_ips(bad)

    def test_reserved(self):
        self.assertEqual(reserved_ips("10.0.1.0/24"), ["10.0.1.0", "10.0.1.1", "10.0.1.2", "10.0.1.3", "10.0.1.255"])
        self.assertEqual(reserved_ips("10.20.32.0/20")[-1], "10.20.47.255")


# ── Exercise 02 ★: Plan the subnets ──────────────────────────────────
"""
prefix_for_hosts(hosts) -> int
    The SMALLEST subnet (largest prefix length, /28 at most) that still has `hosts` usable
    addresses after AWS's 5 reserved ones. hosts < 1 or more than a /16 can hold → ValueError.
    prefix_for_hosts(251) == 24      prefix_for_hosts(252) == 23      prefix_for_hosts(1) == 28
plan_subnets(vpc_cidr, tiers, azs) -> dict[(tier, az), cidr]
    One subnet per (tier, AZ). `tiers` maps tier name → hosts needed in each of its subnets.
    Allocate the biggest subnets first (on a tie, keep the order the tiers were given), each
    aligned to its own size, packed from the start of the VPC block, AZs in the order given.
    Subnets that do not fit in the VPC → ValueError.
Example:
    plan_subnets("10.0.0.0/16", {"public": 200, "app": 1000, "data": 100}, ["us-east-1a", "us-east-1b"]) ==
      {("app", "us-east-1a"): "10.0.0.0/22",  ("app", "us-east-1b"): "10.0.4.0/22",
       ("public", "us-east-1a"): "10.0.8.0/24", ("public", "us-east-1b"): "10.0.9.0/24",
       ("data", "us-east-1a"): "10.0.10.0/25", ("data", "us-east-1b"): "10.0.10.128/25"}
Why biggest first? Small blocks placed first leave gaps that big, aligned blocks cannot use.
Hint: keep a cursor (an int address); round it up to a multiple of the block size before each subnet.
"""
def prefix_for_hosts(hosts):
    raise NotImplementedError  # YOUR CODE


def plan_subnets(vpc_cidr, tiers, azs):
    raise NotImplementedError  # YOUR CODE


class Ex02(Drill):
    """Plan the subnets ★"""
    tasks = ("3.4",)

    def test_prefix_for_hosts(self):
        for hosts, want in {1: 28, 11: 28, 12: 27, 251: 24, 252: 23, 500: 23, 1000: 22, 65531: 16}.items():
            with self.subTest(hosts=hosts):
                self.assertEqual(prefix_for_hosts(hosts), want)
        for bad in (0, 65532):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    prefix_for_hosts(bad)

    def test_example_plan(self):
        self.assertEqual(plan_subnets("10.0.0.0/16", {"public": 200, "app": 1000, "data": 100}, ["us-east-1a", "us-east-1b"]), {
            ("app", "us-east-1a"): "10.0.0.0/22", ("app", "us-east-1b"): "10.0.4.0/22",
            ("public", "us-east-1a"): "10.0.8.0/24", ("public", "us-east-1b"): "10.0.9.0/24",
            ("data", "us-east-1a"): "10.0.10.0/25", ("data", "us-east-1b"): "10.0.10.128/25"})

    def test_three_azs_and_ties(self):
        plan = plan_subnets("10.50.0.0/20", {"web": 100, "jobs": 100}, ["a", "b", "c"])
        self.assertEqual(list(plan.values()), ["10.50.0.0/25", "10.50.0.128/25", "10.50.1.0/25",
                                               "10.50.1.128/25", "10.50.2.0/25", "10.50.2.128/25"])
        self.assertEqual(list(plan)[0], ("web", "a"))

    def test_does_not_fit(self):
        with self.assertRaises(ValueError):
            plan_subnets("10.0.0.0/24", {"app": 200}, ["a", "b"])


# ── Exercise 03 ★: Which way does the packet go? ─────────────────────
"""
route_target(destination_ip, routes) -> str | None
`routes` maps destination CIDR → target, like a route table:
    {"10.0.0.0/16": "local", "0.0.0.0/0": "nat-0a1", "10.1.0.0/16": "pcx-07b"}
Return the target of the MOST SPECIFIC route (longest prefix) that contains the destination, or
None when no route matches — then the packet is dropped. The local route is just a route: it wins
for VPC addresses because nothing more specific usually exists.
Examples:
    route_target("10.0.3.4", routes) == "local"      route_target("8.8.8.8", routes) == "nat-0a1"
Hint: ipaddress.ip_address(ip) in ipaddress.ip_network(cidr); compare .prefixlen.
"""
def route_target(destination_ip, routes):
    raise NotImplementedError  # YOUR CODE


class Ex03(Drill):
    """Which way does the packet go? ★"""
    tasks = ("3.4",)
    ROUTES = {"10.0.0.0/16": "local", "0.0.0.0/0": "igw-01", "10.1.0.0/16": "pcx-01", "10.1.5.0/24": "tgw-01",
              "192.168.0.0/16": "vgw-01"}

    def test_longest_prefix_wins(self):
        cases = {"10.0.3.4": "local", "8.8.8.8": "igw-01", "10.1.9.9": "pcx-01", "10.1.5.9": "tgw-01",
                 "192.168.4.4": "vgw-01", "10.2.0.1": "igw-01"}
        for ip, want in cases.items():
            with self.subTest(ip=ip):
                self.assertEqual(route_target(ip, self.ROUTES), want)

    def test_private_route_table_without_default_route(self):
        private = {"10.0.0.0/16": "local"}
        self.assertEqual(route_target("10.0.200.1", private), "local")
        self.assertIsNone(route_target("52.95.110.1", private))


# ── Exercise 04 ★: Security groups vs network ACLs ───────────────────
"""
Model one TCP connection from a client to a server inside a VPC.
A security-group rule:  {"protocol": "tcp" | "udp" | "icmp" | "-1" (all), "ports": (from, to), "peer": CIDR or "sg-…"}
A network-ACL rule:     {"rule": 100, "action": "allow" | "deny", "protocol": …, "ports": (from, to), "cidr": CIDR}
Host (given) = ip, subnet, sgs (its security-group ids), sg_in, sg_out, nacl_in, nacl_out.
ANY_OUT and NACL_ALLOW_ALL (given) are the default "allow everything" rules.

sg_allows(rules, peer_ip, peer_sgs, protocol, port) -> bool
    True if ANY rule matches the protocol and port and its peer is a CIDR containing peer_ip or a
    security-group id in peer_sgs. (Security groups only allow; there are no deny rules.)
nacl_allows(rules, peer_ip, protocol, port) -> bool
    Check rules in rule-number order, LOWEST first; the first rule that matches decides
    (allow → True, deny → False); if none matches, the hidden final rule denies → False.
tcp_connection(client, server, port, client_port=49152) -> (bool, str)
    Check in this order and return (False, <name>) for the first check that fails, else (True, "allowed"):
      "client security group (outbound)"        client.sg_out allows server (ip / sgs) on port
      "client network ACL (outbound)"           *  client.nacl_out allows server.ip on port
      "server network ACL (inbound)"            *  server.nacl_in allows client.ip on port
      "server security group (inbound)"         server.sg_in allows client (ip / sgs) on port
      "server network ACL (outbound, reply)"    *  server.nacl_out allows client.ip on client_port
      "client network ACL (inbound, reply)"     *  client.nacl_in allows server.ip on client_port
    * only when the two hosts are in different subnets — traffic inside one subnet never crosses
      its network ACL. Security groups are STATEFUL: replies are let back without a rule. Network
      ACLs are STATELESS: the reply to port `port` comes back to the client's ephemeral port.
"""
def sg_allows(rules, peer_ip, peer_sgs, protocol, port):
    raise NotImplementedError  # YOUR CODE


def nacl_allows(rules, peer_ip, protocol, port):
    raise NotImplementedError  # YOUR CODE


def tcp_connection(client, server, port, client_port=49152):
    raise NotImplementedError  # YOUR CODE


def _app_server(nacl_in=(NACL_ALLOW_ALL,), nacl_out=(NACL_ALLOW_ALL,), sg_in=None):
    rules = sg_in if sg_in is not None else ({"protocol": "tcp", "ports": (8000, 8000), "peer": "sg-alb"},)
    return Host(ip="10.0.8.20", subnet="app-a", sgs=("sg-app",), sg_in=rules, nacl_in=nacl_in, nacl_out=nacl_out)


ALB = Host(ip="10.0.0.10", subnet="public-a", sgs=("sg-alb",))


class Ex04(Drill):
    """Security groups vs network ACLs ★"""
    tasks = ("1.2",)

    def test_sg_and_nacl_rules(self):
        rules = [{"protocol": "tcp", "ports": (443, 443), "peer": "0.0.0.0/0"}, {"protocol": "-1", "ports": (0, 65535), "peer": "sg-ops"}]
        self.assertTrue(sg_allows(rules, "203.0.113.9", (), "tcp", 443))
        self.assertFalse(sg_allows(rules, "203.0.113.9", (), "tcp", 22))
        self.assertTrue(sg_allows(rules, "10.0.0.5", ("sg-ops",), "udp", 53))
        nacl = [{"rule": 200, "action": "allow", "protocol": "tcp", "ports": (0, 65535), "cidr": "0.0.0.0/0"},
                {"rule": 100, "action": "deny", "protocol": "tcp", "ports": (22, 22), "cidr": "0.0.0.0/0"}]
        self.assertFalse(nacl_allows(nacl, "198.51.100.1", "tcp", 22))   # rule 100 is checked first
        self.assertTrue(nacl_allows(nacl, "198.51.100.1", "tcp", 443))
        self.assertFalse(nacl_allows(nacl, "198.51.100.1", "udp", 53))   # nothing matches → denied

    def test_security_group_reference(self):
        self.assertEqual(tcp_connection(ALB, _app_server(), 8000), (True, "allowed"))
        self.assertEqual(tcp_connection(ALB, _app_server(), 22), (False, "server security group (inbound)"))
        stranger = Host(ip="10.0.0.11", subnet="public-a", sgs=("sg-other",))
        self.assertEqual(tcp_connection(stranger, _app_server(), 8000), (False, "server security group (inbound)"))

    def test_nacl_rule_order(self):
        deny_first = ({"rule": 90, "action": "deny", "protocol": "tcp", "ports": (8000, 8000), "cidr": "10.0.0.10/32"}, NACL_ALLOW_ALL)
        self.assertEqual(tcp_connection(ALB, _app_server(nacl_in=deny_first), 8000), (False, "server network ACL (inbound)"))
        deny_later = (NACL_ALLOW_ALL, {"rule": 200, "action": "deny", "protocol": "tcp", "ports": (8000, 8000), "cidr": "10.0.0.10/32"})
        self.assertEqual(tcp_connection(ALB, _app_server(nacl_in=deny_later), 8000), (True, "allowed"))

    def test_stateless_replies_need_ephemeral_ports(self):
        only_8000 = ({"rule": 100, "action": "allow", "protocol": "tcp", "ports": (8000, 8000), "cidr": "0.0.0.0/0"},)
        self.assertEqual(tcp_connection(ALB, _app_server(nacl_out=only_8000), 8000), (False, "server network ACL (outbound, reply)"))
        ephemeral = ({"rule": 100, "action": "allow", "protocol": "tcp", "ports": (1024, 65535), "cidr": "0.0.0.0/0"},)
        self.assertEqual(tcp_connection(ALB, _app_server(nacl_out=ephemeral), 8000), (True, "allowed"))
        client = Host(ip="10.0.0.10", subnet="public-a", sgs=("sg-alb",), nacl_in=only_8000)
        self.assertEqual(tcp_connection(client, _app_server(), 8000), (False, "client network ACL (inbound, reply)"))

    def test_same_subnet_and_client_egress(self):
        closed = ({"rule": 100, "action": "deny", "protocol": "-1", "ports": (0, 65535), "cidr": "0.0.0.0/0"},)
        a = Host(ip="10.0.8.5", subnet="app-a", sgs=("sg-a",), nacl_in=closed, nacl_out=closed)
        b = Host(ip="10.0.8.6", subnet="app-a", sgs=("sg-b",), nacl_in=closed, nacl_out=closed,
                 sg_in=({"protocol": "tcp", "ports": (5432, 5432), "peer": "10.0.8.0/24"},))
        self.assertEqual(tcp_connection(a, b, 5432), (True, "allowed"))
        silent = Host(ip="10.0.8.5", subnet="app-a", sgs=("sg-a",), sg_out=())
        self.assertEqual(tcp_connection(silent, b, 5432), (False, "client security group (outbound)"))


# ── Exercise 05 ★: Peering or a transit gateway? ─────────────────────
"""
can_peer(cidr_a, cidr_b) -> bool
    Two VPCs can be peered only if their CIDR blocks do NOT overlap.
can_reach(source, target, peerings, tgw_attachments=()) -> bool
    `peerings` is a list of (vpc, vpc) pairs, in either order. `tgw_attachments` lists the VPCs
    attached to ONE transit gateway that routes between all of them. A VPC always reaches itself.
    VPC peering is NOT transitive: a–b and b–c peered does not let a reach c. A transit gateway is
    a hub: any two attached VPCs reach each other.
peerings_for_full_mesh(vpcs) -> int
    How many peering connections let every one of `vpcs` VPCs reach every other (negative → ValueError).
    peerings_for_full_mesh(5) == 10 — while a transit gateway needs only 5 attachments.
"""
def can_peer(cidr_a, cidr_b):
    raise NotImplementedError  # YOUR CODE


def can_reach(source, target, peerings, tgw_attachments=()):
    raise NotImplementedError  # YOUR CODE


def peerings_for_full_mesh(vpcs):
    raise NotImplementedError  # YOUR CODE


class Ex05(Drill):
    """Peering or a transit gateway? ★"""
    tasks = ("3.4", "4.4")

    def test_can_peer(self):
        self.assertTrue(can_peer("10.0.0.0/16", "10.1.0.0/16"))
        self.assertFalse(can_peer("10.0.0.0/16", "10.0.128.0/17"))
        self.assertFalse(can_peer("172.31.0.0/16", "172.31.0.0/16"))

    def test_peering_is_not_transitive(self):
        peerings = [("shared", "prod"), ("dev", "shared")]
        self.assertTrue(can_reach("prod", "shared", peerings))
        self.assertTrue(can_reach("shared", "dev", peerings))
        self.assertFalse(can_reach("prod", "dev", peerings))
        self.assertTrue(can_reach("prod", "prod", []))

    def test_transit_gateway_is_a_hub(self):
        self.assertTrue(can_reach("prod", "dev", [], tgw_attachments=["prod", "dev", "shared"]))
        self.assertFalse(can_reach("prod", "lab", [], tgw_attachments=["prod", "dev"]))

    def test_full_mesh_count(self):
        self.assertEqual([peerings_for_full_mesh(n) for n in (0, 1, 2, 3, 5, 10)], [0, 0, 1, 3, 10, 45])
        with self.assertRaises(ValueError):
            peerings_for_full_mesh(-1)


# ── Exercise 06: Build a VPC with boto3 ──────────────────────────────
"""
build_vpc(ec2, cidr, plan) -> dict
`plan` maps (tier, az) → subnet CIDR — exactly what your plan_subnets returns. The tier named
"public" is public; every other tier is private. With the `ec2` client, create:
  1. a VPC with `cidr`, then turn on DNS support and DNS hostnames (modify_vpc_attribute, one
     attribute per call);
  2. one subnet per plan entry, in its AZ, with its CIDR;
  3. an internet gateway, attached to the VPC;
  4. ONE public route table with a default route (0.0.0.0/0) to the internet gateway, associated
     with every public subnet;
  5. ONE private route table PER AZ, with no default route (no internet), associated with every
     private subnet in that AZ.
Return {"vpc": vpc_id, "igw": igw_id, "subnets": {(tier, az): subnet_id},
        "route_tables": {"public": rt_id, az: rt_id for each AZ that has private subnets}}.
Hint: ec2.create_vpc(CidrBlock=…)["Vpc"]["VpcId"]; create_subnet(VpcId=…, CidrBlock=…, AvailabilityZone=…);
      create_internet_gateway / attach_internet_gateway; create_route_table / create_route / associate_route_table.
"""
def build_vpc(ec2, cidr, plan):
    raise NotImplementedError  # YOUR CODE


PLAN = {("public", "us-east-1a"): "10.30.0.0/24", ("public", "us-east-1b"): "10.30.1.0/24",
        ("app", "us-east-1a"): "10.30.8.0/22", ("app", "us-east-1b"): "10.30.12.0/22",
        ("data", "us-east-1a"): "10.30.16.0/24", ("data", "us-east-1b"): "10.30.17.0/24"}


def _routes(ec2, rt_id):
    return ec2.describe_route_tables(RouteTableIds=[rt_id])["RouteTables"][0]


class Ex06(Drill):
    """Build a VPC with boto3"""
    tasks = ("3.4", "2.2")
    uses_aws = True

    def build(self):
        ec2 = self.client("ec2")
        return ec2, build_vpc(ec2, "10.30.0.0/16", PLAN)

    def test_vpc_dns_and_igw(self):
        ec2, out = self.build()
        vpc = ec2.describe_vpcs(VpcIds=[out["vpc"]])["Vpcs"][0]
        self.assertEqual(vpc["CidrBlock"], "10.30.0.0/16")
        for attribute, key in (("enableDnsSupport", "EnableDnsSupport"), ("enableDnsHostnames", "EnableDnsHostnames")):
            got = ec2.describe_vpc_attribute(VpcId=out["vpc"], Attribute=attribute)[key]["Value"]
            self.assertTrue(got, f"turn on {attribute}")
        igw = ec2.describe_internet_gateways(InternetGatewayIds=[out["igw"]])["InternetGateways"][0]
        self.assertEqual([a["VpcId"] for a in igw["Attachments"]], [out["vpc"]])

    def test_subnets_follow_the_plan(self):
        ec2, out = self.build()
        self.assertEqual(set(out["subnets"]), set(PLAN))
        for key, subnet_id in out["subnets"].items():
            subnet = ec2.describe_subnets(SubnetIds=[subnet_id])["Subnets"][0]
            with self.subTest(key=key):
                self.assertEqual((subnet["CidrBlock"], subnet["AvailabilityZone"], subnet["VpcId"]), (PLAN[key], key[1], out["vpc"]))

    def test_public_route_table(self):
        ec2, out = self.build()
        table = _routes(ec2, out["route_tables"]["public"])
        defaults = [r for r in table["Routes"] if r.get("DestinationCidrBlock") == "0.0.0.0/0"]
        self.assertEqual([r.get("GatewayId") for r in defaults], [out["igw"]], "public: 0.0.0.0/0 → the internet gateway")
        associated = {a.get("SubnetId") for a in table["Associations"]}
        self.assertEqual(associated - {None}, {out["subnets"][k] for k in PLAN if k[0] == "public"})

    def test_private_route_tables_have_no_internet(self):
        ec2, out = self.build()
        for az in ("us-east-1a", "us-east-1b"):
            table = _routes(ec2, out["route_tables"][az])
            with self.subTest(az=az):
                self.assertFalse([r for r in table["Routes"] if r.get("DestinationCidrBlock") == "0.0.0.0/0"],
                                 "private route tables have no default route")
                associated = {a.get("SubnetId") for a in table["Associations"]} - {None}
                self.assertEqual(associated, {out["subnets"][k] for k in PLAN if k[0] != "public" and k[1] == az})


# ── Exercise 07: Security groups that reference each other ───────────
"""
create_web_sgs(ec2, vpc_id) -> {"alb": sg_id, "app": sg_id, "db": sg_id}
Three security groups in the VPC, named "shortly-alb", "shortly-app" and "shortly-db":
  alb  inbound TCP 443 from anywhere (0.0.0.0/0)
  app  inbound TCP 8000 ONLY from the alb security group (a security-group reference, not a CIDR)
  db   inbound TCP 5432 ONLY from the app security group
Nothing else inbound — in particular no SSH (22) from anywhere: use Session Manager to get a shell.
Leave the default outbound rule (all traffic) alone.
Why references? Instances come and go and their IPs change; "from the app security group" keeps
working for every instance that carries that group.
Hint: authorize_security_group_ingress(GroupId=…, IpPermissions=[{"IpProtocol": "tcp", "FromPort": 8000,
      "ToPort": 8000, "UserIdGroupPairs": [{"GroupId": alb_id}]}]) — for a CIDR use "IpRanges": [{"CidrIp": …}].
"""
def create_web_sgs(ec2, vpc_id):
    raise NotImplementedError  # YOUR CODE


def _ingress(ec2, sg_id):
    return ec2.describe_security_groups(GroupIds=[sg_id])["SecurityGroups"][0]["IpPermissions"]


class Ex07(Drill):
    """Security groups that reference each other"""
    tasks = ("1.2",)
    uses_aws = True

    def make(self):
        ec2 = self.client("ec2")
        vpc = ec2.create_vpc(CidrBlock="10.40.0.0/16")["Vpc"]["VpcId"]
        return ec2, vpc, create_web_sgs(ec2, vpc)

    def test_names_and_vpc(self):
        ec2, vpc, sgs = self.make()
        self.assertEqual(set(sgs), {"alb", "app", "db"})
        for role, sg_id in sgs.items():
            group = ec2.describe_security_groups(GroupIds=[sg_id])["SecurityGroups"][0]
            with self.subTest(role=role):
                self.assertEqual((group["GroupName"], group["VpcId"]), (f"shortly-{role}", vpc))

    def test_chain(self):
        ec2, _, sgs = self.make()
        alb = _ingress(ec2, sgs["alb"])
        self.assertEqual([(p["FromPort"], [r["CidrIp"] for r in p.get("IpRanges", [])]) for p in alb], [(443, ["0.0.0.0/0"])])
        for role, port, source in (("app", 8000, "alb"), ("db", 5432, "app")):
            rules = _ingress(ec2, sgs[role])
            with self.subTest(role=role):
                self.assertEqual(len(rules), 1, f"{role}: exactly one inbound rule")
                self.assertEqual((rules[0]["IpProtocol"], rules[0]["FromPort"], rules[0]["ToPort"]), ("tcp", port, port))
                self.assertEqual([g["GroupId"] for g in rules[0].get("UserIdGroupPairs", [])], [sgs[source]])
                self.assertFalse(rules[0].get("IpRanges"), f"{role}: no CIDR sources, only the {source} security group")

    def test_no_ssh_from_the_internet(self):
        ec2, _, sgs = self.make()
        for role, sg_id in sgs.items():
            for p in _ingress(ec2, sg_id):
                with self.subTest(role=role):
                    self.assertFalse(p.get("FromPort", 0) <= 22 <= p.get("ToPort", 65535) and p.get("IpRanges"),
                                     f"{role} opens SSH to an address range")


# ── Exercise 08: Reach S3 without the internet ───────────────────────
"""
add_s3_gateway_endpoint(ec2, vpc_id, route_table_ids, bucket) -> endpoint_id
    Create a GATEWAY VPC endpoint for S3 in the client's Region (service name
    f"com.amazonaws.{ec2.meta.region_name}.s3"), attached to `route_table_ids`, with an endpoint
    policy that allows only s3:GetObject, s3:PutObject and s3:ListBucket on that one bucket
    (arn:aws:s3:::BUCKET and arn:aws:s3:::BUCKET/*) for any principal ("Principal": "*").
    AWS then adds a route for S3's prefix list to each of those route tables.
vpce_only_bucket_policy(bucket, vpce_id) -> dict
    A bucket policy that DENIES every s3:* action on the bucket and its objects, for any
    principal, unless the request came through `vpce_id` (condition key aws:SourceVpce).
    Gateway endpoints are free and keep S3 traffic on the AWS network — no NAT gateway needed.
Hint: create_vpc_endpoint(VpcEndpointType="Gateway", VpcId=…, ServiceName=…, RouteTableIds=[…],
      PolicyDocument=json.dumps(policy))["VpcEndpoint"]["VpcEndpointId"].
"""
import json  # noqa: E402


def add_s3_gateway_endpoint(ec2, vpc_id, route_table_ids, bucket):
    raise NotImplementedError  # YOUR CODE


def vpce_only_bucket_policy(bucket, vpce_id):
    raise NotImplementedError  # YOUR CODE


class Ex08(Drill):
    """Reach S3 without the internet"""
    tasks = ("1.2", "3.4")
    uses_aws = True
    BUCKET = "shortly-assets-drill"

    def make(self):
        ec2 = self.client("ec2")
        vpc = ec2.create_vpc(CidrBlock="10.50.0.0/16")["Vpc"]["VpcId"]
        tables = [ec2.create_route_table(VpcId=vpc)["RouteTable"]["RouteTableId"] for _ in range(2)]
        return ec2, vpc, tables, add_s3_gateway_endpoint(ec2, vpc, tables, self.BUCKET)

    def test_endpoint(self):
        ec2, vpc, tables, endpoint_id = self.make()
        endpoint = ec2.describe_vpc_endpoints(VpcEndpointIds=[endpoint_id])["VpcEndpoints"][0]
        self.assertEqual((endpoint["VpcEndpointType"], endpoint["ServiceName"], endpoint["VpcId"]),
                         ("Gateway", "com.amazonaws.us-east-1.s3", vpc))
        self.assertEqual(sorted(endpoint["RouteTableIds"]), sorted(tables))
        for table in ec2.describe_route_tables(RouteTableIds=tables)["RouteTables"]:
            with self.subTest(table=table["RouteTableId"]):
                self.assertTrue(any(r.get("DestinationPrefixListId") for r in table["Routes"]), "a prefix-list route to S3")

    def test_endpoint_policy_is_narrow(self):
        ec2, _, _, endpoint_id = self.make()
        raw = ec2.describe_vpc_endpoints(VpcEndpointIds=[endpoint_id])["VpcEndpoints"][0]["PolicyDocument"]
        policy = json.loads(raw) if isinstance(raw, str) else raw
        role = "arn:aws:sts::123456789012:assumed-role/shortly-app/i-1"
        decide = lambda action, arn: ref_policy.evaluate(ref_policy.Request(role, action, arn), identity=[],
                                                         resource_policy=policy, resource_account="123456789012")
        self.assertEqual(decide("s3:GetObject", f"arn:aws:s3:::{self.BUCKET}/a.png"), "Allow")
        self.assertEqual(decide("s3:ListBucket", f"arn:aws:s3:::{self.BUCKET}"), "Allow")
        self.assertNotEqual(decide("s3:GetObject", "arn:aws:s3:::someone-elses-bucket/a.png"), "Allow")
        self.assertNotEqual(decide("s3:DeleteObject", f"arn:aws:s3:::{self.BUCKET}/a.png"), "Allow")

    def test_bucket_policy_requires_the_endpoint(self):
        policy = vpce_only_bucket_policy(self.BUCKET, "vpce-0abc")
        app = [{"Statement": [{"Effect": "Allow", "Action": "s3:*", "Resource": "*"}]}]
        role = "arn:aws:sts::123456789012:assumed-role/shortly-app/i-1"
        obj = f"arn:aws:s3:::{self.BUCKET}/a.png"
        for context, want in (({"aws:SourceVpce": "vpce-0abc"}, "Allow"), ({"aws:SourceVpce": "vpce-9zzz"}, "ExplicitDeny"),
                              ({}, "ExplicitDeny")):
            with self.subTest(context=context):
                got = ref_policy.evaluate(ref_policy.Request(role, "s3:GetObject", obj, context), identity=app,
                                          resource_policy=policy, resource_account="123456789012")
                self.assertEqual(got, want)
        bucket_level = ref_policy.Request(role, "s3:ListBucket", f"arn:aws:s3:::{self.BUCKET}", {})
        self.assertEqual(ref_policy.evaluate(bucket_level, identity=app, resource_policy=policy), "ExplicitDeny",
                         "cover the bucket ARN as well as its objects")


# ── Exercise 09 ★: NAT gateway or endpoint? ──────────────────────────
"""
Private instances move `gb` GB per month to and from S3. Compare three paths (USD per month,
rounded to 2 decimal places), using PRICES (illustrative us-east-1 prices, _harness/awslib/prices.toml):
nat_monthly_cost(gb, nat_gateways, hours=730, price=PRICES)
    nat_gateways × hours × nat_gateway_per_hour  +  gb × nat_gateway_per_gb
interface_endpoint_monthly_cost(gb, azs, hours=730, price=PRICES)
    azs × hours × interface_endpoint_per_hour_per_az  +  gb × interface_endpoint_per_gb
s3_path_costs(gb, nat_gateways, azs, hours=730, price=PRICES) -> dict
    {"nat gateway": …, "interface endpoint": …, "gateway endpoint": gb × gateway_endpoint_per_gb (free)}
Example (2 NAT gateways, 2 AZs, 5,000 GB): the NAT path costs 2 × 730 × 0.045 + 5,000 × 0.045 = 290.70.
Negative gb, nat_gateways or azs → ValueError.
"""
PRICES = prices.section("vpc")


def nat_monthly_cost(gb, nat_gateways, hours=730, price=PRICES):
    raise NotImplementedError  # YOUR CODE


def interface_endpoint_monthly_cost(gb, azs, hours=730, price=PRICES):
    raise NotImplementedError  # YOUR CODE


def s3_path_costs(gb, nat_gateways, azs, hours=730, price=PRICES):
    raise NotImplementedError  # YOUR CODE


class Ex09(Drill):
    """NAT gateway or endpoint? ★"""
    tasks = ("4.4",)

    def test_nat(self):
        p = PRICES
        self.assertAlmostEqual(nat_monthly_cost(5000, 2), round(2 * 730 * p["nat_gateway_per_hour"] + 5000 * p["nat_gateway_per_gb"], 2))
        self.assertAlmostEqual(nat_monthly_cost(0, 1, hours=100), round(100 * p["nat_gateway_per_hour"], 2))

    def test_interface_endpoint(self):
        p = PRICES
        self.assertAlmostEqual(interface_endpoint_monthly_cost(5000, 2),
                               round(2 * 730 * p["interface_endpoint_per_hour_per_az"] + 5000 * p["interface_endpoint_per_gb"], 2))

    def test_all_paths(self):
        costs = s3_path_costs(5000, 2, 2)
        self.assertEqual(set(costs), {"nat gateway", "interface endpoint", "gateway endpoint"})
        self.assertEqual(costs["gateway endpoint"], round(5000 * PRICES["gateway_endpoint_per_gb"], 2))
        self.assertLess(costs["gateway endpoint"], costs["interface endpoint"])
        self.assertLess(costs["interface endpoint"], costs["nat gateway"])

    def test_uses_the_price_argument(self):
        custom = dict(PRICES, nat_gateway_per_hour=1.0, nat_gateway_per_gb=0.0)
        self.assertEqual(nat_monthly_cost(999, 1, hours=10, price=custom), 10.0)

    def test_rejects_negative_inputs(self):
        for call in (lambda: nat_monthly_cost(-1, 1), lambda: nat_monthly_cost(1, -1), lambda: interface_endpoint_monthly_cost(1, -2)):
            with self.subTest():
                with self.assertRaises(ValueError):
                    call()


# ── Exercise 10 (predict): Does the traffic get through? ─────────────
"""
For each scenario, decide "yes" (the traffic gets through) or "no" — BEFORE running anything —
and write it in PREDICTIONS. The test asks the course's reference models (netsim) for the truth.
"""
from _harness.awslib import netsim as _ref_net  # noqa: E402

S3_PREFIX = "52.216.0.0/15"   # stands in for S3's prefix list in us-east-1
SCENARIOS = {
    1: ("A private subnet's route table has only the local route 10.0.0.0/16. An instance there calls S3 at 52.216.4.10.",
        ("route", "52.216.4.10", {"10.0.0.0/16": "local"})),
    2: ("The same route table after adding an S3 gateway endpoint (its prefix list routes to vpce-s3). The instance calls S3 at 52.216.4.10.",
        ("route", "52.216.4.10", {"10.0.0.0/16": "local", S3_PREFIX: "vpce-s3"})),
    3: ("With only the S3 gateway endpoint (no NAT gateway), the instance downloads an OS update from 151.101.0.1.",
        ("route", "151.101.0.1", {"10.0.0.0/16": "local", S3_PREFIX: "vpce-s3"})),
    4: ("The app's security group allows TCP 8000 from the load balancer's security group; both subnets use the default network ACL. The load balancer connects on 8000.",
        ("tcp", ALB, _app_server(), 8000)),
    5: ("The app subnet's network ACL allows inbound TCP 8000 and outbound TCP 8000 only. The load balancer connects on 8000.",
        ("tcp", ALB, _app_server(nacl_in=({"rule": 100, "action": "allow", "protocol": "tcp", "ports": (8000, 8000), "cidr": "0.0.0.0/0"},),
                                 nacl_out=({"rule": 100, "action": "allow", "protocol": "tcp", "ports": (8000, 8000), "cidr": "0.0.0.0/0"},)), 8000)),
    6: ("VPC prod is peered with shared, and shared is peered with dev. An instance in prod connects to one in dev.",
        ("reach", "prod", "dev", [("prod", "shared"), ("shared", "dev")])),
}
PREDICTIONS = {n: None for n in SCENARIOS}   # YOUR ANSWERS: "yes" or "no"


def _truth(kind, *args):
    if kind == "route":
        return _ref_net.route_target(args[0], args[1]) is not None
    if kind == "tcp":
        return _ref_net.tcp_connection(*args)[0]
    return _ref_net.can_reach(*args)


class Ex10(Drill):
    """Does the traffic get through?"""
    tasks = ("3.4", "1.2")

    def test_predictions(self):
        for n, (story, scenario) in SCENARIOS.items():
            with self.subTest(scenario=n):
                truth = "yes" if _truth(*scenario) else "no"
                self.assertIn(PREDICTIONS.get(n), ("yes", "no"), f"scenario {n}: write 'yes' or 'no'")
                self.assertEqual(PREDICTIONS[n], truth, f"scenario {n}: {story} — the answer is {truth}")


if __name__ == "__main__":
    run()

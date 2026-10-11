"""M02.3 — security groups chained by reference: internet → ALB → app → database / cache."""
GROUPS = ("AlbSecurityGroup", "AppSecurityGroup", "DbSecurityGroup", "CacheSecurityGroup")


def ingress_rules(res):
    """Every inbound rule, inline or as a separate AWS::EC2::SecurityGroupIngress, as
    {group: [{"protocol", "ports", "peer"}]} in the course's netsim rule format."""
    rules = {g: [] for g in GROUPS}

    def add(group, rule):
        peer = rule.get("SourceSecurityGroupId") or rule.get("CidrIp") or rule.get("CidrIpv6") or rule.get("SourcePrefixListId")
        protocol = str(rule.get("IpProtocol"))
        ports = (int(rule.get("FromPort", 0)), int(rule.get("ToPort", 65535))) if protocol != "-1" else (0, 65535)
        rules.setdefault(group, []).append({"protocol": protocol, "ports": ports, "peer": f"sg-{peer}" if peer in GROUPS else peer})

    for name, r in res.items():
        if r["Type"] == "AWS::EC2::SecurityGroup":
            for rule in r["Properties"].get("SecurityGroupIngress", []):
                add(name, rule)
        if r["Type"] == "AWS::EC2::SecurityGroupIngress":
            add(r["Properties"].get("GroupId"), r["Properties"])
    return rules


def test_groups_exist_in_the_vpc(resources):
    res = resources("network")
    for group in GROUPS:
        assert res.get(group, {}).get("Type") == "AWS::EC2::SecurityGroup", f"add {group} (AWS::EC2::SecurityGroup)"
        assert res[group]["Properties"].get("VpcId") == "Vpc", f"{group}: VpcId: !Ref Vpc"


def test_exact_inbound_rules(resources):
    rules = ingress_rules(resources("network"))
    alb = sorted((r["protocol"], r["ports"], r["peer"]) for r in rules["AlbSecurityGroup"])
    assert ("tcp", (443, 443), "0.0.0.0/0") in alb, "the ALB accepts HTTPS (443) from anywhere"
    assert all(r[2] == "0.0.0.0/0" and r[1] in ((443, 443), (80, 80)) for r in alb), "the ALB accepts only 80 and 443"
    expected = {"AppSecurityGroup": [("tcp", (8000, 8000), "sg-AlbSecurityGroup")],
                "DbSecurityGroup": [("tcp", (5432, 5432), "sg-AppSecurityGroup")],
                "CacheSecurityGroup": [("tcp", (6379, 6379), "sg-AppSecurityGroup")]}
    for group, want in expected.items():
        got = [(r["protocol"], r["ports"], r["peer"]) for r in rules[group]]
        assert got == want, f"{group} inbound must be exactly {want}, found {got}"


def test_paths_with_the_course_model(resources, netsim):
    rules = ingress_rules(resources("network"))
    host = lambda ip, group: netsim.Host(ip=ip, subnet=group, sgs=(f"sg-{group}",), sg_in=tuple(rules[group]))
    internet = netsim.Host(ip="203.0.113.50", subnet="internet")
    alb, app = host("10.20.0.10", "AlbSecurityGroup"), host("10.20.4.10", "AppSecurityGroup")
    db, cache = host("10.20.12.10", "DbSecurityGroup"), host("10.20.13.10", "CacheSecurityGroup")
    assert netsim.tcp_connection(internet, alb, 443)[0]
    assert netsim.tcp_connection(alb, app, 8000)[0]
    assert netsim.tcp_connection(app, db, 5432)[0] and netsim.tcp_connection(app, cache, 6379)[0]
    for client, server, port in ((internet, app, 8000), (internet, db, 5432), (alb, db, 5432), (internet, app, 22)):
        assert not netsim.tcp_connection(client, server, port)[0], f"{client.ip} must not reach {server.subnet} on {port}"

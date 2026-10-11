"""M02.1 — the VPC and six subnets: three tiers in two Availability Zones, planned and documented."""
import ipaddress

SUBNETS = {"PublicSubnetA": ("public", 0), "PublicSubnetB": ("public", 1), "AppSubnetA": ("app", 0),
           "AppSubnetB": ("app", 1), "DataSubnetA": ("data", 0), "DataSubnetB": ("data", 1)}
MIN_HOSTS = {"public": 250, "app": 1000, "data": 250}


def test_parameters(template):
    params = template("network").get("Parameters", {})
    assert params.get("VpcCidr", {}).get("Default") == "10.20.0.0/16", "Parameter VpcCidr (String, Default 10.20.0.0/16)"
    for name in ("Prefix", "Env"):
        assert name in params, f"the network stack also takes the {name} parameter"


def test_vpc(resources):
    vpc = resources("network").get("Vpc")
    assert vpc and vpc["Type"] == "AWS::EC2::VPC", "add a resource Vpc (AWS::EC2::VPC)"
    props = vpc["Properties"]
    assert props.get("CidrBlock") == "10.20.0.0/16", "CidrBlock: !Ref VpcCidr"
    assert props.get("EnableDnsSupport") is True and props.get("EnableDnsHostnames") is True, \
        "turn on EnableDnsSupport and EnableDnsHostnames (VPC endpoints and RDS need DNS)"


def test_six_subnets_in_two_azs(resources):
    res = resources("network")
    for name, (_, az) in SUBNETS.items():
        subnet = res.get(name)
        assert subnet and subnet["Type"] == "AWS::EC2::Subnet", f"add {name} (AWS::EC2::Subnet)"
        assert subnet["Properties"].get("VpcId") == "Vpc", f"{name}: VpcId: !Ref Vpc"
        assert subnet["Properties"].get("AvailabilityZone") == f"us-east-1{'ab'[az]}", \
            f"{name}: AvailabilityZone: !Select [{az}, !GetAZs ''] (A = first AZ, B = second)"


def test_subnet_sizes_fit_and_never_overlap(resources, cidr):
    res = resources("network")
    blocks = {name: res[name]["Properties"]["CidrBlock"] for name in SUBNETS}
    for name, block in blocks.items():
        tier = SUBNETS[name][0]
        assert ipaddress.ip_network(block).subnet_of(ipaddress.ip_network("10.20.0.0/16")), f"{name} ({block}) must be inside the VPC"
        assert cidr.usable_ips(block) >= MIN_HOSTS[tier], f"{name} ({block}) needs at least {MIN_HOSTS[tier]} usable addresses"
    names = list(blocks)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            assert not cidr.overlaps(blocks[a], blocks[b]), f"{a} ({blocks[a]}) overlaps {b} ({blocks[b]})"


def test_private_subnets_never_hand_out_public_ips(resources):
    res = resources("network")
    for name in ("AppSubnetA", "AppSubnetB", "DataSubnetA", "DataSubnetB"):
        assert res[name]["Properties"].get("MapPublicIpOnLaunch") is not True, f"{name} must not give instances public IPs"


def test_readme_documents_the_plan(repo, resources):
    text = (repo / "README.md").read_text(encoding="utf-8")
    assert "## Network plan" in text, "add a '## Network plan' section to README.md"
    res = resources("network")
    for name in SUBNETS:
        block = res[name]["Properties"]["CidrBlock"]
        assert block in text, f"README's network plan should list {name}: {block}"

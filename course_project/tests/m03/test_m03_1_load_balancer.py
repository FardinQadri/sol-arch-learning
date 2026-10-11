"""M03.1 — the Application Load Balancer and the target group behind it."""


def props(res, name, type_):
    assert res.get(name, {}).get("Type") == type_, f"add {name} ({type_})"
    return res[name]["Properties"]


def test_parameters(template):
    params = template("compute").get("Parameters", {})
    assert params.get("Prefix", {}).get("Default") == "shortly", "Parameter Prefix (String, Default shortly)"
    assert sorted(params.get("Env", {}).get("AllowedValues", [])) == ["lab", "prod"], "Parameter Env with AllowedValues [lab, prod]"
    assert params.get("InstanceType", {}).get("Default") == "t4g.small", \
        "Parameter InstanceType (String) with Default t4g.small — a small Graviton instance"
    assert params["InstanceType"].get("AllowedValues"), "give InstanceType AllowedValues so nobody can pick an unreviewed type"
    image = params.get("ImageId", {})
    assert image.get("Type") == "AWS::SSM::Parameter::Value<AWS::EC2::Image::Id>", \
        "Parameter ImageId: Type AWS::SSM::Parameter::Value<AWS::EC2::Image::Id> — CloudFormation looks up the newest AMI when the stack is created"
    assert str(image.get("Default", "")).endswith("al2023-ami-kernel-default-arm64"), \
        "ImageId Default: /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64 (Amazon Linux 2023, arm64 to match Graviton)"


def test_load_balancer(resources):
    p = props(resources("compute"), "LoadBalancer", "AWS::ElasticLoadBalancingV2::LoadBalancer")
    assert p.get("Type", "application") == "application", "LoadBalancer Type: application (an ALB routes HTTP by path)"
    assert p.get("Scheme") == "internet-facing", "LoadBalancer Scheme: internet-facing"
    assert p.get("Subnets") == ["import:shortly-public-subnet-ids"], \
        "LoadBalancer Subnets: !Split [',', !ImportValue …-public-subnet-ids] (the ALB lives in the public subnets)"
    assert p.get("SecurityGroups") == ["import:shortly-alb-sg-id"], "LoadBalancer SecurityGroups: [!ImportValue …-alb-sg-id]"


def test_target_group(resources):
    p = props(resources("compute"), "AppTargetGroup", "AWS::ElasticLoadBalancingV2::TargetGroup")
    assert (p.get("Protocol"), p.get("Port")) == ("HTTP", 8000), "AppTargetGroup: Protocol HTTP, Port 8000 (where the app listens)"
    assert p.get("VpcId") == "import:shortly-vpc-id", "AppTargetGroup VpcId: !ImportValue …-vpc-id"
    assert p.get("TargetType", "instance") == "instance", "AppTargetGroup TargetType: instance"
    assert p.get("HealthCheckPath") == "/healthz", "AppTargetGroup HealthCheckPath: /healthz"
    assert str((p.get("Matcher") or {}).get("HttpCode")) == "200", "AppTargetGroup Matcher: {HttpCode: '200'}"


def test_deregistration_delay_is_short(resources):
    p = props(resources("compute"), "AppTargetGroup", "AWS::ElasticLoadBalancingV2::TargetGroup")
    attrs = {a.get("Key"): a.get("Value") for a in p.get("TargetGroupAttributes") or []}
    assert "deregistration_delay.timeout_seconds" in attrs, \
        "set TargetGroupAttributes: - {Key: deregistration_delay.timeout_seconds, Value: '30'} — the default is 300 s"
    seconds = int(attrs["deregistration_delay.timeout_seconds"])
    assert seconds <= 60, (f"deregistration delay is {seconds} s; use 60 or less. The default 300 s makes every scale-in "
                           "wait five minutes for an app whose requests take milliseconds")

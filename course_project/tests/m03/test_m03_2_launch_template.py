"""M03.2 — the launch template: Graviton, IMDSv2, instance profile, no SSH key."""
import pytest

TYPE = "AWS::EC2::LaunchTemplate"


@pytest.fixture
def data(resources):
    res = resources("compute")
    assert res.get("AppLaunchTemplate", {}).get("Type") == TYPE, f"add AppLaunchTemplate ({TYPE})"
    props = res["AppLaunchTemplate"]["Properties"]
    assert props.get("LaunchTemplateData"), "AppLaunchTemplate needs LaunchTemplateData"
    return props


def test_name_image_and_type(data, template):
    assert data.get("LaunchTemplateName") == "shortly-app", "LaunchTemplateName: !Sub '${Prefix}-app'"
    raw = template("compute")["Resources"]["AppLaunchTemplate"]["Properties"]["LaunchTemplateData"]
    assert raw.get("ImageId") == {"Ref": "ImageId"}, "LaunchTemplateData ImageId: !Ref ImageId (the parameter, not a hard-coded AMI id)"
    assert raw.get("InstanceType") == {"Ref": "InstanceType"}, "LaunchTemplateData InstanceType: !Ref InstanceType"


def test_every_allowed_instance_type_is_graviton(template, ec2types):
    spec = template("compute").get("Parameters", {}).get("InstanceType", {})
    assert spec.get("Default") and spec.get("AllowedValues"), "InstanceType needs a Default and AllowedValues"
    for name in list(spec["AllowedValues"]) + [spec["Default"]]:
        try:
            info = ec2types.decode(str(name))
        except ValueError as exc:
            pytest.fail(f"{name} is not an instance type name: {exc}", pytrace=False)
        assert info["processor"] == "AWS Graviton", \
            (f"{name} is {info['processor']}, not Graviton. Remove it: Graviton costs up to 20 % less than comparable x86 "
             "instances (and the AMI is arm64, so an x86 type would not even boot)")


def test_imdsv2_required(data):
    meta = data["LaunchTemplateData"].get("MetadataOptions") or {}
    assert meta.get("HttpTokens") == "required", \
        ("IMDSv2: MetadataOptions HttpTokens: required. With 'optional', a request-forgery bug in the app can steal the "
         "instance role's credentials with one GET")
    assert meta.get("HttpEndpoint", "enabled") == "enabled", "MetadataOptions HttpEndpoint: enabled (the app's SDK needs the metadata service)"
    assert meta.get("HttpPutResponseHopLimit") in (1, 2), \
        ("MetadataOptions HttpPutResponseHopLimit: 1. The token reply may cross one network hop; "
         "2 is only for containers that run on the instance")


def test_instance_profile_and_security_group(data):
    d = data["LaunchTemplateData"]
    assert (d.get("IamInstanceProfile") or {}).get("Name") == "import:shortly-app-instance-profile", \
        "IamInstanceProfile: {Name: !ImportValue …-app-instance-profile} (created in M01)"
    assert d.get("SecurityGroupIds") == ["import:shortly-app-sg-id"], "SecurityGroupIds: [!ImportValue …-app-sg-id] (created in M02)"


def test_no_ssh_key_and_no_public_ip(data):
    d = data["LaunchTemplateData"]
    assert "KeyName" not in d, "remove KeyName: use Session Manager, not SSH keys. The app security group has no port 22 anyway"
    for nic in d.get("NetworkInterfaces") or []:
        assert nic.get("AssociatePublicIpAddress") in (None, False, "false"), \
            "instances stay private (app subnets): remove AssociatePublicIpAddress; they reach the internet through NAT"

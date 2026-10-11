"""M03.6 — exports for later stacks, lint-clean, and a deploy in moto (iam + network + compute) for both environments."""
import pytest

EXPORTS = {"AlbDnsName": ("shortly-alb-dns-name", "LoadBalancer.DNSName"),
           "AlbArn": ("shortly-alb-arn", "LoadBalancer"),
           "AppTargetGroupArn": ("shortly-app-tg-arn", "AppTargetGroup"),
           "AppAsgName": ("shortly-app-asg-name", "AppAutoScalingGroup")}


def test_exports(outputs):
    out = outputs("compute")
    for key, (export, value) in EXPORTS.items():
        assert key in out, f"add Output {key}"
        assert out[key].get("Export", {}).get("Name") == export, f"{key}: Export Name !Sub '${{Prefix}}-{export[8:]}'"
        assert str(out[key].get("Value")) == value, f"{key}: Value should render as {value} ({'!GetAtt ' + value if '.' in value else '!Ref ' + value})"


def test_lint_clean(lint_errors):
    errors = lint_errors("compute")
    assert errors == [], "cfn-lint errors: " + "; ".join(f"line {e['line']} {e['rule']} {e['message']}" for e in errors)


@pytest.mark.parametrize("env, instances", [("prod", 2), ("lab", 1)])
def test_deploys_in_moto(moto_stacks, env, instances):
    import boto3

    for layer in ("iam", "network", "compute"):
        status = moto_stacks(layer, Env=env)
        assert status == "CREATE_COMPLETE", f"the {layer} stack ended as {status}; fix infra/{layer}.yaml"
    region = {"region_name": "us-east-1"}
    asg_client = boto3.client("autoscaling", **region)
    groups = asg_client.describe_auto_scaling_groups()["AutoScalingGroups"]
    assert len(groups) == 1, "expected one Auto Scaling group"
    group = groups[0]
    assert group["MinSize"] == instances and len(group["Instances"]) == instances, f"Env={env}: expected {instances} instance(s)"
    assert group["HealthCheckType"] == "ELB"

    elb_client = boto3.client("elbv2", **region)
    target_groups = elb_client.describe_target_groups()["TargetGroups"]
    assert [t["HealthCheckPath"] for t in target_groups] == ["/healthz"]
    balancers = elb_client.describe_load_balancers()["LoadBalancers"]
    assert len(balancers) == 1 and len(balancers[0]["AvailabilityZones"]) == 2, "the load balancer should span two Availability Zones"

    # moto stores the launch template but never applies its settings to instances, so read the template itself
    ec2 = boto3.client("ec2", **region)
    versions = ec2.describe_launch_template_versions(LaunchTemplateName="shortly-app", Versions=["$Latest"])["LaunchTemplateVersions"]
    assert versions[0]["LaunchTemplateData"]["MetadataOptions"]["HttpTokens"] == "required"

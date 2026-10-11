"""M03.4 — the Auto Scaling group and its CPU target-tracking policy. prod: 2–6 instances; lab: 1–2."""
import pytest

ASG = "AWS::AutoScaling::AutoScalingGroup"
POLICY = "AWS::AutoScaling::ScalingPolicy"
SIZES = {"prod": (2, 6), "lab": (1, 2)}


def asg(resources, **params):
    res = resources("compute", **params)
    assert res.get("AppAutoScalingGroup", {}).get("Type") == ASG, f"add AppAutoScalingGroup ({ASG})"
    return res["AppAutoScalingGroup"]["Properties"]


def policy(resources, **params):
    res = resources("compute", **params)
    assert res.get("CpuTargetTracking", {}).get("Type") == POLICY, f"add CpuTargetTracking ({POLICY})"
    return res["CpuTargetTracking"]["Properties"]


@pytest.mark.parametrize("env", ["prod", "lab"])
def test_size_per_environment(resources, env):
    p = asg(resources, Env=env)
    low, high = SIZES[env]
    assert (p.get("MinSize"), p.get("MaxSize")) == (low, high), \
        f"Env={env}: MinSize {low}, MaxSize {high} (!If [IsProd, …, …]; prod needs two instances so one AZ can fail)"
    assert "DesiredCapacity" not in p, "remove DesiredCapacity: the group starts at MinSize and the scaling policy then owns the number"


def test_uses_elb_health_checks(resources):
    p = asg(resources)
    assert p.get("HealthCheckType") == "ELB", \
        "HealthCheckType: ELB. Behind a load balancer use ELB health checks, or Auto Scaling never replaces an instance whose app has died"
    grace = p.get("HealthCheckGracePeriod")
    assert isinstance(grace, int) and 60 <= grace <= 600, \
        f"HealthCheckGracePeriod is {grace!r}; use 60–600 seconds (time for boot, user data and the first healthy check)"


def test_launch_template_and_target_group(resources):
    p = asg(resources)
    lt = p.get("LaunchTemplate") or {}
    assert lt.get("LaunchTemplateId") == "AppLaunchTemplate", "LaunchTemplate: LaunchTemplateId: !Ref AppLaunchTemplate"
    assert lt.get("Version") == "AppLaunchTemplate.LatestVersionNumber", \
        "LaunchTemplate Version: !GetAtt AppLaunchTemplate.LatestVersionNumber (so editing the template rolls out a new version)"
    assert p.get("TargetGroupARNs") == ["AppTargetGroup"], "TargetGroupARNs: [!Ref AppTargetGroup]"
    assert p.get("VPCZoneIdentifier") == ["import:shortly-app-subnet-ids"], \
        "VPCZoneIdentifier: !Split [',', !ImportValue …-app-subnet-ids] (private app subnets in both AZs)"


def test_instances_are_tagged(resources):
    tags = {t.get("Key"): t for t in asg(resources).get("Tags") or []}
    assert tags.get("Name", {}).get("Value") == "shortly-app", "Tags: Key Name, Value !Sub '${Prefix}-app'"
    assert tags["Name"].get("PropagateAtLaunch") in (True, "true"), "the Name tag needs PropagateAtLaunch: true to reach the instances"


def test_cpu_target_tracking(resources):
    p = policy(resources)
    assert p.get("PolicyType") == "TargetTrackingScaling", "CpuTargetTracking PolicyType: TargetTrackingScaling"
    assert p.get("AutoScalingGroupName") == "AppAutoScalingGroup", "AutoScalingGroupName: !Ref AppAutoScalingGroup"
    config = p.get("TargetTrackingConfiguration") or {}
    metric = (config.get("PredefinedMetricSpecification") or {}).get("PredefinedMetricType")
    assert metric == "ASGAverageCPUUtilization", "PredefinedMetricSpecification PredefinedMetricType: ASGAverageCPUUtilization"
    target = config.get("TargetValue")
    assert isinstance(target, (int, float)) and 40 <= target <= 70, \
        f"TargetValue is {target!r}; use 40–70. Lower wastes money, higher leaves no room for a traffic spike while new instances boot"


@pytest.mark.parametrize("env", ["prod", "lab"])
def test_scaling_model(resources, scaling, env):
    p, target = asg(resources, Env=env), policy(resources, Env=env)["TargetTrackingConfiguration"]["TargetValue"]
    low, high = p["MinSize"], p["MaxSize"]
    wanted = scaling.target_tracking(low, 100.0, float(target), low, high)
    assert wanted > low, (f"Env={env}: at MinSize ({low}) and 100 % CPU the policy should add instances, but the model keeps {wanted}. "
                          "Is MaxSize larger than MinSize?")
    assert wanted <= high, f"Env={env}: the policy would grow past MaxSize ({high})"
    assert scaling.target_tracking(high, 100.0, float(target), low, high) == high, "the group never grows past MaxSize"

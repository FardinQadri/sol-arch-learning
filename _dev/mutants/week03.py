"""Deliberately wrong implementations for week 03 — each must be caught by its drill."""
MUTANTS = [
    {"id": "g-means-graviton", "drill": 1, "code": '''
from _harness.awslib import ec2types as _ref
def decode(instance_type):
    got = _ref.decode(instance_type)
    if "g" in instance_type.lower().split(".")[0]:
        got["processor"] = "AWS Graviton"
    return got
'''},
    {"id": "commitment-by-the-hour", "drill": 2, "code": '''
def monthly_cost(option, rate, instances, hours_used, *, hours_in_month=730, price=PRICES):
    if option not in OPTIONS or min(rate, instances, hours_used) < 0 or hours_used > hours_in_month:
        raise ValueError(option)
    factor = {"on-demand": 1.0, "spot": 1 - price["spot_discount"],
              "compute savings plan": 1 - price["compute_savings_plan_discount"],
              "standard reserved": 1 - price["standard_ri_discount"]}[option]
    return round(instances * hours_used * rate * factor, 2)
'''},
    {"id": "round-to-nearest", "drill": 3, "code": '''
def target_tracking(current, metric, target, minimum, maximum):
    if minimum < 0 or minimum > maximum or current < 0 or target <= 0:
        raise ValueError("bad input")
    if current == 0:
        return minimum
    return max(minimum, min(maximum, round(current * metric / target)))
'''},
    {"id": "list-order", "drill": 4, "code": '''
from _harness.awslib import elb as _ref
def match_rule(request, rules):
    _ref._validate(rules)
    ordered = [r for r in rules if r["priority"] != "default"] + [r for r in rules if r["priority"] == "default"]
    for rule in ordered:
        if all(_ref._condition_matches(c, request) for c in rule.get("conditions") or []):
            return rule["action"]
'''},
    {"id": "per-target-split", "drill": 5, "code": '''
def cross_zone_share(targets_per_az, cross_zone):
    if any(n < 0 for n in targets_per_az.values()):
        raise ValueError("negative")
    total = sum(targets_per_az.values())
    if total == 0:
        raise ValueError("no targets")
    return {az: (1 / total if n else 0.0) for az, n in targets_per_az.items()}
'''},
    {"id": "imdsv1-allowed", "drill": 6, "code": '''
def create_web_fleet(ec2, autoscaling, subnet_ids, sg_id, profile_name, ami_id):
    template = ec2.create_launch_template(LaunchTemplateName="shortly-web", LaunchTemplateData={
        "ImageId": ami_id, "InstanceType": "t4g.small", "IamInstanceProfile": {"Name": profile_name},
        "SecurityGroupIds": [sg_id],
        "MetadataOptions": {"HttpTokens": "optional", "HttpPutResponseHopLimit": 1, "HttpEndpoint": "enabled"}})["LaunchTemplate"]["LaunchTemplateId"]
    autoscaling.create_auto_scaling_group(AutoScalingGroupName="shortly-web", LaunchTemplate={"LaunchTemplateId": template, "Version": "$Latest"},
        MinSize=2, MaxSize=6, DesiredCapacity=2, VPCZoneIdentifier=",".join(subnet_ids), HealthCheckType="ELB", HealthCheckGracePeriod=120)
    autoscaling.put_scaling_policy(AutoScalingGroupName="shortly-web", PolicyName="cpu-50", PolicyType="TargetTrackingScaling",
        TargetTrackingConfiguration={"PredefinedMetricSpecification": {"PredefinedMetricType": "ASGAverageCPUUtilization"}, "TargetValue": 50.0})
    return {"launch_template_id": template, "asg_name": "shortly-web"}
'''},
    {"id": "healthz-exposed", "drill": 7, "code": '''
def build_alb(elbv2, vpc_id, subnet_ids, sg_id):
    tg = elbv2.create_target_group(Name="shortly-app", Protocol="HTTP", Port=8000, VpcId=vpc_id, TargetType="instance",
                                   HealthCheckPath="/healthz", Matcher={"HttpCode": "200"})["TargetGroups"][0]["TargetGroupArn"]
    lb = elbv2.create_load_balancer(Name="shortly-alb", Subnets=list(subnet_ids), SecurityGroups=[sg_id],
                                    Scheme="internet-facing", Type="application")["LoadBalancers"][0]["LoadBalancerArn"]
    listener = elbv2.create_listener(LoadBalancerArn=lb, Protocol="HTTP", Port=80,
                                     DefaultActions=[{"Type": "forward", "TargetGroupArn": tg}])["Listeners"][0]["ListenerArn"]
    elbv2.create_rule(ListenerArn=listener, Priority=20, Conditions=[{"Field": "path-pattern", "Values": ["/api/*"]}],
                      Actions=[{"Type": "forward", "TargetGroupArn": tg}])
    return {"lb_arn": lb, "tg_arn": tg, "listener_arn": listener}
'''},
    {"id": "grace-period-forgotten", "drill": 8, "code": '''
def fleet_settings(subnet_ids, launch_template_id):
    return {
        "launch_template_data": {"InstanceType": "t4g.small",
            "MetadataOptions": {"HttpTokens": "required", "HttpPutResponseHopLimit": 1, "HttpEndpoint": "enabled"}},
        "asg": {"MinSize": 2, "MaxSize": 6, "DesiredCapacity": 2,
            "LaunchTemplate": {"LaunchTemplateId": launch_template_id, "Version": "$Latest"},
            "VPCZoneIdentifier": ",".join(subnet_ids), "TargetGroupARNs": [TARGET_GROUP_ARN],
            "HealthCheckType": "ELB", "HealthCheckGracePeriod": 0},
    }
'''},
    {"id": "seven-in-total", "drill": 9, "code": '''
def max_spread_instances(azs):
    if azs < 1:
        raise ValueError("need an AZ")
    return 7
'''},
    {"id": "opposite-predictions", "drill": 10, "code": '''
PREDICTIONS = {1: 7, 2: 3, 3: "yes", 4: "no", 5: 25, 6: "forward api"}
'''},
]

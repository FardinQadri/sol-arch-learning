"""Reference solutions for week 03.

Drills 01–05: the course's reference models ARE the solution — read _harness/awslib/ec2types.py,
purchasing.py, scaling.py and elb.py and compare them with yours.
"""
from _harness.awslib.ec2types import choose_type, decode  # noqa: F401
from _harness.awslib.elb import alb_monthly_cost, cross_zone_share, match_rule  # noqa: F401
from _harness.awslib.purchasing import break_even_hours, cheapest, monthly_cost  # noqa: F401
from _harness.awslib.scaling import simple_scaling_run, step_scaling, target_tracking  # noqa: F401


def latest_ami(ssm):
    return ssm.get_parameter(Name=AMI_PARAMETER)["Parameter"]["Value"]


def create_web_fleet(ec2, autoscaling, subnet_ids, sg_id, profile_name, ami_id):
    template = ec2.create_launch_template(LaunchTemplateName="shortly-web", LaunchTemplateData={
        "ImageId": ami_id, "InstanceType": "t4g.small",
        "IamInstanceProfile": {"Name": profile_name}, "SecurityGroupIds": [sg_id],
        "MetadataOptions": {"HttpTokens": "required", "HttpPutResponseHopLimit": 1, "HttpEndpoint": "enabled"},
    })["LaunchTemplate"]["LaunchTemplateId"]
    autoscaling.create_auto_scaling_group(
        AutoScalingGroupName="shortly-web", LaunchTemplate={"LaunchTemplateId": template, "Version": "$Latest"},
        MinSize=2, MaxSize=6, DesiredCapacity=2, VPCZoneIdentifier=",".join(subnet_ids),
        HealthCheckType="ELB", HealthCheckGracePeriod=120)
    autoscaling.put_scaling_policy(
        AutoScalingGroupName="shortly-web", PolicyName="cpu-50", PolicyType="TargetTrackingScaling",
        TargetTrackingConfiguration={"PredefinedMetricSpecification": {"PredefinedMetricType": "ASGAverageCPUUtilization"},
                                     "TargetValue": 50.0})
    return {"launch_template_id": template, "asg_name": "shortly-web"}


def build_alb(elbv2, vpc_id, subnet_ids, sg_id):
    tg = elbv2.create_target_group(Name="shortly-app", Protocol="HTTP", Port=8000, VpcId=vpc_id, TargetType="instance",
                                   HealthCheckPath="/healthz", Matcher={"HttpCode": "200"})["TargetGroups"][0]["TargetGroupArn"]
    lb = elbv2.create_load_balancer(Name="shortly-alb", Subnets=list(subnet_ids), SecurityGroups=[sg_id],
                                    Scheme="internet-facing", Type="application")["LoadBalancers"][0]["LoadBalancerArn"]
    listener = elbv2.create_listener(LoadBalancerArn=lb, Protocol="HTTP", Port=80,
                                     DefaultActions=[{"Type": "forward", "TargetGroupArn": tg}])["Listeners"][0]["ListenerArn"]
    elbv2.create_rule(ListenerArn=listener, Priority=10, Conditions=[{"Field": "path-pattern", "Values": ["/healthz"]}],
                      Actions=[{"Type": "fixed-response", "FixedResponseConfig": {
                          "StatusCode": "404", "ContentType": "text/plain", "MessageBody": "not found"}}])
    elbv2.create_rule(ListenerArn=listener, Priority=20, Conditions=[{"Field": "path-pattern", "Values": ["/api/*"]}],
                      Actions=[{"Type": "forward", "TargetGroupArn": tg}])
    return {"lb_arn": lb, "tg_arn": tg, "listener_arn": listener}


def fleet_settings(subnet_ids, launch_template_id):
    return {
        "launch_template_data": {
            "InstanceType": "t4g.small",
            "MetadataOptions": {"HttpTokens": "required", "HttpPutResponseHopLimit": 1, "HttpEndpoint": "enabled"},
        },
        "asg": {
            "MinSize": 2, "MaxSize": 6, "DesiredCapacity": 2,
            "LaunchTemplate": {"LaunchTemplateId": launch_template_id, "Version": "$Latest"},
            "VPCZoneIdentifier": ",".join(subnet_ids),
            "TargetGroupARNs": [TARGET_GROUP_ARN],
            "HealthCheckType": "ELB",
            "HealthCheckGracePeriod": 120,
        },
    }


def max_spread_instances(azs):
    if azs < 1:
        raise ValueError("need at least one Availability Zone")
    return 7 * azs


PLACEMENT = {1: "cluster", 2: "spread", 3: "partition", 4: "spread", 5: "none", 6: "partition"}
PURCHASE = {1: "savings plan", 2: "spot", 3: "dedicated host", 4: "capacity reservation"}
PREDICTIONS = {1: 8, 2: 4, 3: "no", 4: "yes", 5: 50, 6: "fixed-response 403"}

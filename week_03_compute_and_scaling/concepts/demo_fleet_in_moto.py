"""Demo — a small web fleet built with boto3 against a fake AWS (moto): a launch template that requires IMDSv2,
an Application Load Balancer with two rules, and an Auto Scaling group of 2 with a target-tracking policy.
Run it: python concepts/demo_fleet_in_moto.py   (offline; nothing here touches a real account)"""
import base64
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.awslib.safety import force_utf8, use_fake_aws_env  # noqa: E402

force_utf8()
use_fake_aws_env()

import boto3  # noqa: E402
from moto import mock_aws  # noqa: E402

REGION = "us-east-1"
AMI_PARAMETER = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"
USER_DATA = "#!/bin/bash\nmkdir -p /srv/www\necho ok > /srv/www/healthz\ncd /srv/www && python3 -m http.server 80\n"

with mock_aws():
    ec2 = boto3.client("ec2", region_name=REGION)
    ssm = boto3.client("ssm", region_name=REGION)
    elbv2 = boto3.client("elbv2", region_name=REGION)
    asg = boto3.client("autoscaling", region_name=REGION)

    # 1. Network: one VPC, two subnets in two AZs, one security group.
    vpc_id = ec2.create_vpc(CidrBlock="10.0.0.0/16")["Vpc"]["VpcId"]
    subnets = [
        ec2.create_subnet(VpcId=vpc_id, CidrBlock=cidr, AvailabilityZone=az)["Subnet"]["SubnetId"]
        for cidr, az in (("10.0.1.0/24", "us-east-1a"), ("10.0.2.0/24", "us-east-1b"))
    ]
    sg_id = ec2.create_security_group(GroupName="web", Description="web tier", VpcId=vpc_id)["GroupId"]
    ec2.authorize_security_group_ingress(
        GroupId=sg_id, IpPermissions=[{"IpProtocol": "tcp", "FromPort": 80, "ToPort": 80,
                                       "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}])
    print(f"VPC {vpc_id} with 2 subnets in 2 AZs and one security group")

    # 2. The image: ask SSM for the latest Amazon Linux 2023 arm64 AMI instead of hard-coding an id.
    ami_id = ssm.get_parameter(Name=AMI_PARAMETER)["Parameter"]["Value"]
    print(f"\nSSM public parameter {AMI_PARAMETER}\n  -> {ami_id}")

    # 3. The launch template: IMDSv2 required. Moto does not copy this setting to instances,
    #    so we read it back from the template, which is also what the course tests do.
    ec2.create_launch_template(
        LaunchTemplateName="web-template",
        LaunchTemplateData={
            "ImageId": ami_id,
            "InstanceType": "t4g.micro",
            "SecurityGroupIds": [sg_id],
            "UserData": base64.b64encode(USER_DATA.encode()).decode(),
            "MetadataOptions": {"HttpTokens": "required", "HttpPutResponseHopLimit": 1, "HttpEndpoint": "enabled"},
        },
    )
    version = ec2.describe_launch_template_versions(LaunchTemplateName="web-template", Versions=["$Latest"])
    data = version["LaunchTemplateVersions"][0]["LaunchTemplateData"]
    print(f"\nLaunch template web-template, version {version['LaunchTemplateVersions'][0]['VersionNumber']}")
    print(f"  instance type : {data['InstanceType']}")
    print(f"  MetadataOptions: {data['MetadataOptions']}   <- HttpTokens=required means IMDSv2 only")

    # 4. Target group, load balancer, listener and two rules.
    tg = elbv2.create_target_group(
        Name="web-tg", Protocol="HTTP", Port=80, VpcId=vpc_id, TargetType="instance",
        HealthCheckPath="/healthz", HealthCheckIntervalSeconds=15,
    )["TargetGroups"][0]
    alb = elbv2.create_load_balancer(
        Name="web-alb", Subnets=subnets, SecurityGroups=[sg_id], Scheme="internet-facing", Type="application",
    )["LoadBalancers"][0]
    listener = elbv2.create_listener(
        LoadBalancerArn=alb["LoadBalancerArn"], Protocol="HTTP", Port=80,
        DefaultActions=[{"Type": "forward", "TargetGroupArn": tg["TargetGroupArn"]}],
    )["Listeners"][0]
    # Created out of order on purpose: 20 first, then 10.
    elbv2.create_rule(
        ListenerArn=listener["ListenerArn"], Priority=20,
        Conditions=[{"Field": "path-pattern", "Values": ["/api/*"]}],
        Actions=[{"Type": "forward", "TargetGroupArn": tg["TargetGroupArn"]}],
    )
    elbv2.create_rule(
        ListenerArn=listener["ListenerArn"], Priority=10,
        Conditions=[{"Field": "path-pattern", "Values": ["/healthz"]}],
        Actions=[{"Type": "fixed-response",
                  "FixedResponseConfig": {"StatusCode": "200", "ContentType": "text/plain", "MessageBody": "ok"}}],
    )
    print(f"\nTarget group web-tg: health check path {tg['HealthCheckPath']}, interval {tg['HealthCheckIntervalSeconds']} s")
    print(f"Load balancer web-alb: {alb['Scheme']}, {alb['Type']}, DNS {alb['DNSName']}")

    rules = elbv2.describe_rules(ListenerArn=listener["ListenerArn"])["Rules"]
    # Moto lists rules in creation order. AWS evaluates them by priority, so sort them yourself.
    rules.sort(key=lambda r: (r["Priority"] == "default", int(r["Priority"]) if r["Priority"] != "default" else 0))
    print("Listener rules in the order AWS evaluates them:")
    for rule in rules:
        cond = rule["Conditions"][0]["Values"] if rule["Conditions"] else "(no conditions)"
        action = rule["Actions"][0]["Type"]
        print(f"  priority {rule['Priority']:<8} {str(cond):<14} -> {action}")

    # 5. The Auto Scaling group, attached to the target group, with a target-tracking policy.
    asg.create_auto_scaling_group(
        AutoScalingGroupName="web-asg",
        LaunchTemplate={"LaunchTemplateName": "web-template", "Version": "$Latest"},
        MinSize=2, MaxSize=4, DesiredCapacity=2,
        VPCZoneIdentifier=",".join(subnets),
        TargetGroupARNs=[tg["TargetGroupArn"]],
        HealthCheckType="ELB", HealthCheckGracePeriod=120,
    )
    asg.put_scaling_policy(
        AutoScalingGroupName="web-asg", PolicyName="cpu-50", PolicyType="TargetTrackingScaling",
        TargetTrackingConfiguration={
            "PredefinedMetricSpecification": {"PredefinedMetricType": "ASGAverageCPUUtilization"},
            "TargetValue": 50.0,
        },
    )
    group = asg.describe_auto_scaling_groups(AutoScalingGroupNames=["web-asg"])["AutoScalingGroups"][0]
    policy = asg.describe_policies(AutoScalingGroupName="web-asg")["ScalingPolicies"][0]
    print(f"\nAuto Scaling group web-asg: min {group['MinSize']}, desired {group['DesiredCapacity']}, max {group['MaxSize']}")
    print(f"  health check: {group['HealthCheckType']}, grace period {group['HealthCheckGracePeriod']} s")
    print(f"  instances: {len(group['Instances'])}   target groups: {len(group['TargetGroupARNs'])}")
    target = policy["TargetTrackingConfiguration"]
    print(f"  policy {policy['PolicyName']}: keep {target['PredefinedMetricSpecification']['PredefinedMetricType']}"
          f" at {target['TargetValue']:.0f}")

    health = elbv2.describe_target_health(TargetGroupArn=tg["TargetGroupArn"])["TargetHealthDescriptions"]
    print(f"\nTarget health: {[h['TargetHealth']['State'] for h in health]}")

    print("\nWhat moto does NOT simulate:")
    print("  - AZ spreading: both instances may land in one AZ although the group has two subnets.")
    print("  - Health: a target is 'healthy' at once. Nothing ever checks /healthz or turns it unhealthy.")
    print("  - Scaling: the policy is stored, but no CPU metric exists, so nothing ever scales.")
    print("  - Settings: IMDSv2 and the instance profile in the template never reach the instances.")
    print("  That is why drills 03-05 are models: you build the behaviour yourself.")

print("\nNow do drills 06–08.")

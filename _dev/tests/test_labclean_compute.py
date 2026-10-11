import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from _harness import labclean

TAG = [{"Key": "saa-course", "Value": "lab"}]
OTHER = [{"Key": "owner", "Value": "someone-else"}]
WEEK3 = ["autoscaling_groups", "load_balancers", "target_groups", "launch_templates", "ec2_instances", "security_groups"]


@pytest.fixture
def aws(monkeypatch):
    monkeypatch.setattr(labclean, "WAIT_SECONDS", 0)
    with mock_aws():
        yield boto3.Session(region_name="us-east-1")


def run(aws, kinds, *args):
    return labclean.main(kinds, argv=list(args), session_factory=lambda **kw: aws)


def tags(on, resource_type):
    return [{"ResourceType": resource_type, "Tags": TAG if on else OTHER}]


def vpc_and_subnets(ec2):
    vpc = ec2.describe_vpcs(Filters=[{"Name": "is-default", "Values": ["true"]}])["Vpcs"][0]["VpcId"]
    subnets = [s["SubnetId"] for s in ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc]}])["Subnets"]][:2]
    return vpc, subnets


def make_sg(ec2, vpc, name, tagged):
    return ec2.create_security_group(GroupName=name, Description=name, VpcId=vpc,
                                     TagSpecifications=tags(tagged, "security-group"))["GroupId"]


def make_lt(ec2, name, tagged):
    ami = ec2.describe_images()["Images"][0]["ImageId"]
    return ec2.create_launch_template(LaunchTemplateName=name, LaunchTemplateData={"ImageId": ami, "InstanceType": "t3.micro"},
                                      TagSpecifications=tags(tagged, "launch-template"))["LaunchTemplate"]["LaunchTemplateId"]


def make_asg(aws, name, lt_id, subnets, tagged, tg_arns=()):
    aws.client("autoscaling").create_auto_scaling_group(
        AutoScalingGroupName=name, LaunchTemplate={"LaunchTemplateId": lt_id, "Version": "$Latest"},
        MinSize=1, MaxSize=2, DesiredCapacity=1, VPCZoneIdentifier=",".join(subnets), TargetGroupARNs=list(tg_arns),
        Tags=[{"Key": k["Key"], "Value": k["Value"], "PropagateAtLaunch": True} for k in (TAG if tagged else OTHER)])


def make_tg(elb, name, vpc, tagged):
    return elb.create_target_group(Name=name, Protocol="HTTP", Port=80, VpcId=vpc, Tags=TAG if tagged else OTHER)["TargetGroups"][0]["TargetGroupArn"]


def make_lb(elb, name, subnets, sgs, tagged):
    return elb.create_load_balancer(Name=name, Subnets=subnets, SecurityGroups=sgs, Tags=TAG if tagged else OTHER)["LoadBalancers"][0]["LoadBalancerArn"]


def lb_names(elb):
    return {lb["LoadBalancerName"] for lb in elb.describe_load_balancers()["LoadBalancers"]}


def sg_ids(ec2):
    return {g["GroupId"] for g in ec2.describe_security_groups()["SecurityGroups"] if g["GroupName"] != "default"}


# -- one kind at a time: tagged goes, untagged twin stays --


def test_asg_tagged_deleted_untagged_kept(aws):
    ec2, asg = aws.client("ec2"), aws.client("autoscaling")
    _, subnets = vpc_and_subnets(ec2)
    lt = make_lt(ec2, "lt", True)
    make_asg(aws, "mine", lt, subnets, True)
    make_asg(aws, "theirs", lt, subnets, False)
    assert run(aws, ["autoscaling_groups"], "--yes") == 0
    assert [g["AutoScalingGroupName"] for g in asg.describe_auto_scaling_groups()["AutoScalingGroups"]] == ["theirs"]


def test_load_balancer_tagged_deleted_untagged_kept(aws):
    ec2, elb = aws.client("ec2"), aws.client("elbv2")
    _, subnets = vpc_and_subnets(ec2)
    make_lb(elb, "mine", subnets, [], True)
    make_lb(elb, "theirs", subnets, [], False)
    assert run(aws, ["load_balancers"], "--yes") == 0
    assert lb_names(elb) == {"theirs"}


def test_load_balancer_tags_read_in_batches_of_at_most_20(aws, monkeypatch):
    ec2, elb = aws.client("ec2"), aws.client("elbv2")
    _, subnets = vpc_and_subnets(ec2)
    for i in range(23):
        make_lb(elb, f"lb{i:02d}", subnets, [], tagged=(i % 2 == 0))
    sizes = []

    class Spy:
        def __init__(self, client):
            self._client = client

        def describe_tags(self, **kw):
            sizes.append(len(kw["ResourceArns"]))
            return self._client.describe_tags(**kw)

        def __getattr__(self, name):
            return getattr(self._client, name)

    class SpySession:
        def client(self, *a, **kw):
            return Spy(aws.client(*a, **kw))

    found = labclean.find_load_balancers(SpySession(), "us-east-1")
    assert len(found) == 12
    assert sorted(sizes) == [3, 20]


def test_target_group_tagged_deleted_untagged_kept(aws):
    ec2, elb = aws.client("ec2"), aws.client("elbv2")
    vpc, _ = vpc_and_subnets(ec2)
    make_tg(elb, "mine", vpc, True)
    make_tg(elb, "theirs", vpc, False)
    assert run(aws, ["target_groups"], "--yes") == 0
    assert [t["TargetGroupName"] for t in elb.describe_target_groups()["TargetGroups"]] == ["theirs"]


def test_launch_template_tagged_deleted_untagged_kept(aws):
    ec2 = aws.client("ec2")
    make_lt(ec2, "mine", True)
    make_lt(ec2, "theirs", False)
    assert run(aws, ["launch_templates"], "--yes") == 0
    assert [t["LaunchTemplateName"] for t in ec2.describe_launch_templates()["LaunchTemplates"]] == ["theirs"]


def test_security_group_tagged_deleted_untagged_kept_default_untouched(aws):
    ec2 = aws.client("ec2")
    vpc, _ = vpc_and_subnets(ec2)
    make_sg(ec2, vpc, "mine", True)
    theirs = make_sg(ec2, vpc, "theirs", False)
    default = ec2.describe_security_groups(Filters=[{"Name": "group-name", "Values": ["default"]}])["SecurityGroups"][0]["GroupId"]
    ec2.create_tags(Resources=[default], Tags=TAG)  # even a (mis)tagged default group is never deleted
    assert run(aws, ["security_groups"], "--yes") == 0
    assert sg_ids(ec2) == {theirs}
    assert default in {g["GroupId"] for g in ec2.describe_security_groups()["SecurityGroups"]}


def test_security_groups_are_one_item_and_none_means_no_item(aws):
    ec2 = aws.client("ec2")
    assert labclean.find_security_groups(aws, "us-east-1") == []
    vpc, _ = vpc_and_subnets(ec2)
    a, b = make_sg(ec2, vpc, "a", True), make_sg(ec2, vpc, "b", True)
    items = labclean.find_security_groups(aws, "us-east-1")
    assert len(items) == 1 and items[0].kind == "security_groups"
    assert a in items[0].name and b in items[0].name


# -- dry run --


def test_dry_run_deletes_nothing_and_lists_everything(aws, capsys):
    ec2, elb, asg = aws.client("ec2"), aws.client("elbv2"), aws.client("autoscaling")
    vpc, subnets = vpc_and_subnets(ec2)
    sg = make_sg(ec2, vpc, "mine-sg", True)
    lt = make_lt(ec2, "mine-lt", True)
    tg = make_tg(elb, "mine-tg", vpc, True)
    make_lb(elb, "mine-lb", subnets, [sg], True)
    make_asg(aws, "mine-asg", lt, subnets, True)
    assert run(aws, WEEK3) == 0
    out = capsys.readouterr().out
    assert "DRY RUN" in out
    for needle in ("mine-asg", "mine-lb", "mine-tg", "mine-lt", sg):
        assert needle in out
    assert lb_names(elb) == {"mine-lb"}
    assert len(asg.describe_auto_scaling_groups()["AutoScalingGroups"]) == 1
    assert len(elb.describe_target_groups(TargetGroupArns=[tg])["TargetGroups"]) == 1
    assert len(ec2.describe_launch_templates()["LaunchTemplates"]) == 1
    assert sg in sg_ids(ec2)


# -- security groups that reference each other --


def test_two_tagged_groups_referencing_each_other_are_both_deleted(aws):
    ec2 = aws.client("ec2")
    vpc, _ = vpc_and_subnets(ec2)
    alb, app = make_sg(ec2, vpc, "alb", True), make_sg(ec2, vpc, "app", True)
    for target, source in ((app, alb), (alb, app)):  # a cycle
        ec2.authorize_security_group_ingress(GroupId=target, IpPermissions=[
            {"IpProtocol": "tcp", "FromPort": 80, "ToPort": 80, "UserIdGroupPairs": [{"GroupId": source}]}])
    # moto does not enforce DependencyViolation for referenced groups, so this proves the end state only
    assert run(aws, ["security_groups"], "--yes") == 0
    assert sg_ids(ec2) == set()


def test_untagged_group_referenced_by_tagged_group_survives(aws):
    ec2 = aws.client("ec2")
    vpc, _ = vpc_and_subnets(ec2)
    mine, theirs = make_sg(ec2, vpc, "mine", True), make_sg(ec2, vpc, "theirs", False)
    ec2.authorize_security_group_ingress(GroupId=mine, IpPermissions=[
        {"IpProtocol": "tcp", "FromPort": 80, "ToPort": 80, "UserIdGroupPairs": [{"GroupId": theirs}]}])
    ec2.authorize_security_group_ingress(GroupId=theirs, IpPermissions=[
        {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "10.0.0.0/8"}]}])
    before = ec2.describe_security_groups(GroupIds=[theirs])["SecurityGroups"][0]["IpPermissions"]
    assert run(aws, ["security_groups"], "--yes") == 0
    assert sg_ids(ec2) == {theirs}
    assert ec2.describe_security_groups(GroupIds=[theirs])["SecurityGroups"][0]["IpPermissions"] == before  # rules intact


def test_security_group_delete_retries_on_dependency_violation(aws, monkeypatch):
    ec2 = aws.client("ec2")
    vpc, _ = vpc_and_subnets(ec2)
    sg = make_sg(ec2, vpc, "mine", True)
    real = ec2.delete_security_group
    calls = []

    def flaky(**kw):
        calls.append(1)
        if len(calls) < 3:
            raise ClientError({"Error": {"Code": "DependencyViolation", "Message": "in use"}}, "DeleteSecurityGroup")
        return real(**kw)
    monkeypatch.setattr(ec2, "delete_security_group", flaky)
    labclean._delete_security_groups(ec2, [sg])
    assert len(calls) == 3 and sg not in sg_ids(ec2)


def test_security_group_delete_gives_up_with_timeout(aws, monkeypatch):
    ec2 = aws.client("ec2")
    vpc, _ = vpc_and_subnets(ec2)
    sg = make_sg(ec2, vpc, "mine", True)
    monkeypatch.setattr(labclean, "WAIT_ATTEMPTS", 3)

    def stuck(**kw):
        raise ClientError({"Error": {"Code": "DependencyViolation", "Message": "in use"}}, "DeleteSecurityGroup")
    monkeypatch.setattr(ec2, "delete_security_group", stuck)
    with pytest.raises(TimeoutError):
        labclean._delete_security_groups(ec2, [sg])


# -- the whole week 03 lab --


def test_full_week03_order_end_to_end(aws):
    ec2, elb, asg = aws.client("ec2"), aws.client("elbv2"), aws.client("autoscaling")
    vpc, subnets = vpc_and_subnets(ec2)
    stacks = {}
    for label, tagged in (("mine", True), ("theirs", False)):
        alb_sg, app_sg = make_sg(ec2, vpc, f"{label}-alb", tagged), make_sg(ec2, vpc, f"{label}-app", tagged)
        ec2.authorize_security_group_ingress(GroupId=app_sg, IpPermissions=[
            {"IpProtocol": "tcp", "FromPort": 80, "ToPort": 80, "UserIdGroupPairs": [{"GroupId": alb_sg}]}])
        lt = make_lt(ec2, f"{label}-lt", tagged)
        tg = make_tg(elb, f"{label}-tg", vpc, tagged)
        lb = make_lb(elb, f"{label}-lb", subnets, [alb_sg], tagged)
        elb.create_listener(LoadBalancerArn=lb, Protocol="HTTP", Port=80,
                            DefaultActions=[{"Type": "forward", "TargetGroupArn": tg}])
        make_asg(aws, f"{label}-asg", lt, subnets, tagged, [tg])
        stacks[label] = {"sgs": {alb_sg, app_sg}}
    instances = {}
    for reservation in ec2.describe_instances()["Reservations"]:
        for inst in reservation["Instances"]:
            instances[inst["InstanceId"]] = {t["Key"]: t["Value"] for t in inst.get("Tags", [])}
    mine_instances = [i for i, t in instances.items() if t.get("saa-course") == "lab"]
    theirs_instances = [i for i in instances if i not in mine_instances]
    assert mine_instances and theirs_instances  # moto propagates the ASG tags to its instances

    assert run(aws, WEEK3, "--yes") == 0

    assert [g["AutoScalingGroupName"] for g in asg.describe_auto_scaling_groups()["AutoScalingGroups"]] == ["theirs-asg"]
    assert lb_names(elb) == {"theirs-lb"}
    assert [t["TargetGroupName"] for t in elb.describe_target_groups()["TargetGroups"]] == ["theirs-tg"]
    assert [t["LaunchTemplateName"] for t in ec2.describe_launch_templates()["LaunchTemplates"]] == ["theirs-lt"]
    assert sg_ids(ec2) == stacks["theirs"]["sgs"]
    state = {i["InstanceId"]: i["State"]["Name"] for r in ec2.describe_instances()["Reservations"] for i in r["Instances"]}
    assert all(state[i] == "terminated" for i in mine_instances)
    assert all(state[i] != "terminated" for i in theirs_instances)
    assert run(aws, WEEK3, "--yes") == 0  # a second run finds nothing left of ours


def test_finders_order_for_week03():
    week03 = ["s3_buckets", "autoscaling_groups", "load_balancers", "target_groups", "ec2_instances", "launch_templates",
              "nat_gateways", "elastic_ips", "security_groups", "vpcs", "iam_roles", "iam_users", "iam_policies"]
    assert [k for k in labclean.FINDERS if k in week03] == week03, "later weeks may add kinds, but never reorder these"


def test_unknown_kind_rejected(aws):
    with pytest.raises(ValueError, match="unknown resource kind"):
        run(aws, ["load_balancers", "lambda_functions"])

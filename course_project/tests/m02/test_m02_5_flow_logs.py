"""M02.5 — VPC flow logs to CloudWatch Logs, with a role that may write only to that log group."""
ACCOUNT = "111122223333"


def test_log_group_with_retention(resources):
    group = resources("network").get("FlowLogsLogGroup")
    assert group and group["Type"] == "AWS::Logs::LogGroup", "add FlowLogsLogGroup (AWS::Logs::LogGroup)"
    days = group["Properties"].get("RetentionInDays")
    assert isinstance(days, int) and 1 <= days <= 90, "set RetentionInDays (1–90): logs kept forever cost money forever"


def test_flow_log(resources):
    flow = resources("network").get("VpcFlowLog")
    assert flow and flow["Type"] == "AWS::EC2::FlowLog", "add VpcFlowLog (AWS::EC2::FlowLog)"
    props = flow["Properties"]
    assert (props.get("ResourceId"), props.get("ResourceType")) == ("Vpc", "VPC"), "log the whole VPC"
    assert props.get("TrafficType") in ("ALL", "REJECT"), "TrafficType ALL (or REJECT to keep costs down)"
    assert props.get("LogDestinationType", "cloud-watch-logs") == "cloud-watch-logs"
    assert props.get("LogGroupName") == "FlowLogsLogGroup", "LogGroupName: !Ref FlowLogsLogGroup"
    assert props.get("DeliverLogsPermissionArn") == "FlowLogsRole.Arn", "DeliverLogsPermissionArn: !GetAtt FlowLogsRole.Arn"


def test_role_trusts_the_flow_logs_service(trust_policy, evaluator):
    trust = trust_policy("network", "FlowLogsRole")
    assert evaluator.evaluate_trust(trust, "vpc-flow-logs.amazonaws.com")
    assert not evaluator.evaluate_trust(trust, "ec2.amazonaws.com")


def test_role_writes_only_its_log_group(role_policies, evaluator, resources):
    policies = role_policies("network", "FlowLogsRole")
    role = f"arn:aws:sts::{ACCOUNT}:assumed-role/shortly-flow-logs/x"
    group_name = resources("network")["FlowLogsLogGroup"]["Properties"].get("LogGroupName", "")
    assert group_name.startswith("/shortly/"), "LogGroupName: !Sub '/${Prefix}/vpc-flow-logs'"
    mine = f"arn:aws:logs:us-east-1:{ACCOUNT}:log-group:{group_name}:log-stream:eni-1"
    other = f"arn:aws:logs:us-east-1:{ACCOUNT}:log-group:/other/app:log-stream:x"
    for action in ("logs:CreateLogStream", "logs:PutLogEvents"):
        assert evaluator.evaluate_policies(policies, evaluator.Request(role, action, mine)) == "Allow", f"FlowLogsRole needs {action} on its group"
        assert evaluator.evaluate_policies(policies, evaluator.Request(role, action, other)) != "Allow", f"{action} only on its own group"

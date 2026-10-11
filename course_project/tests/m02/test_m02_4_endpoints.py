"""M02.4 — gateway endpoints for S3 and DynamoDB, so private subnets reach them without NAT."""
import pytest

PRIVATE_TABLES = {"AppRouteTableA", "AppRouteTableB", "DataRouteTable"}


@pytest.mark.parametrize("name, service", [("S3Endpoint", "s3"), ("DynamoDbEndpoint", "dynamodb")])
def test_gateway_endpoint(resources, name, service):
    endpoint = resources("network").get(name)
    assert endpoint and endpoint["Type"] == "AWS::EC2::VPCEndpoint", f"add {name} (AWS::EC2::VPCEndpoint)"
    props = endpoint["Properties"]
    assert props.get("VpcEndpointType", "Gateway") == "Gateway", f"{name} is a Gateway endpoint (free; Interface ones cost money)"
    assert props.get("ServiceName") == f"com.amazonaws.us-east-1.{service}", \
        f"{name}: ServiceName: !Sub 'com.amazonaws.${{AWS::Region}}.{service}'"
    assert props.get("VpcId") == "Vpc"
    assert PRIVATE_TABLES <= set(props.get("RouteTableIds", [])), f"{name} must be on {sorted(PRIVATE_TABLES)}"


def test_s3_endpoint_policy_stays_in_this_account(resources, evaluator):
    props = resources("network")["S3Endpoint"]["Properties"]
    policy = props.get("PolicyDocument")
    assert policy, "give S3Endpoint a PolicyDocument (an endpoint policy)"
    mine = "arn:aws:s3:::shortly-assets-111122223333/uploads/a.png"
    caller = "arn:aws:sts::111122223333:assumed-role/shortly-app/i-1"

    def decide(arn, **context):
        return evaluator.evaluate(evaluator.Request(caller, "s3:GetObject", arn, {"aws:ResourceAccount": "111122223333", **context}),
                                  identity=[], resource_policy=policy, resource_account="111122223333")
    assert decide(mine) == "Allow", "the endpoint must let the app reach this account's buckets"
    other = evaluator.Request(caller, "s3:GetObject", "arn:aws:s3:::attacker-bucket/x", {"aws:ResourceAccount": "444455556666"})
    assert evaluator.evaluate(other, identity=[], resource_policy=policy, resource_account="111122223333") != "Allow", \
        "the endpoint must not reach buckets owned by other accounts (condition on aws:ResourceAccount)"

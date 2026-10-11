"""M01.3 — the click consumer's Lambda execution role."""
ACCOUNT = "111122223333"
CONSUMER = f"arn:aws:sts::{ACCOUNT}:assumed-role/shortly-click-consumer/fn"
QUEUE = f"arn:aws:sqs:us-east-1:{ACCOUNT}:shortly-clicks"
TABLE = f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-clicks-daily"
LOGS = f"arn:aws:logs:us-east-1:{ACCOUNT}:log-group:/aws/lambda/shortly-click-consumer:log-stream:x"


def test_role(template, render):
    role = template("iam")["Resources"].get("ConsumerRole")
    assert role and role["Type"] == "AWS::IAM::Role", "add ConsumerRole (AWS::IAM::Role)"
    assert render(role["Properties"].get("RoleName")) == "shortly-click-consumer"


def test_only_lambda_can_assume(trust_policy, evaluator):
    trust = trust_policy("iam", "ConsumerRole")
    assert evaluator.evaluate_trust(trust, "lambda.amazonaws.com")
    assert not evaluator.evaluate_trust(trust, "ec2.amazonaws.com")


def test_consumer_permissions(role_policies, evaluator):
    policies = role_policies("iam", "ConsumerRole")

    def decide(action, arn):
        return evaluator.evaluate_policies(policies, evaluator.Request(CONSUMER, action, arn))
    for action in ("sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"):
        assert decide(action, QUEUE) == "Allow", f"the consumer needs {action} on the clicks queue"
    assert decide("dynamodb:UpdateItem", TABLE) == "Allow", "the consumer writes rollups with UpdateItem"
    assert decide("logs:PutLogEvents", LOGS) == "Allow", "Lambda needs to write its logs"
    assert decide("sqs:SendMessage", QUEUE) != "Allow", "the consumer only reads the queue"
    assert decide("dynamodb:DeleteItem", TABLE) != "Allow"

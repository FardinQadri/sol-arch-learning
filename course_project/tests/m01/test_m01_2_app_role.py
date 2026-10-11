"""M01.2 — the app's instance role: exactly what shortly needs, nothing more."""
ACCOUNT = "111122223333"
APP = f"arn:aws:sts::{ACCOUNT}:assumed-role/shortly-app/i-0123456789abcdef0"
NEEDS = [
    ("secretsmanager:GetSecretValue", f"arn:aws:secretsmanager:us-east-1:{ACCOUNT}:secret:shortly/db-AbCdEf", {}),
    ("dynamodb:GetItem", f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-clicks-daily", {}),
    ("dynamodb:Query", f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-clicks-daily", {}),
    ("s3:GetObject", f"arn:aws:s3:::shortly-assets-{ACCOUNT}/uploads/logo.png", {}),
    ("s3:PutObject", f"arn:aws:s3:::shortly-assets-{ACCOUNT}/uploads/logo.png", {}),
    ("sqs:SendMessage", f"arn:aws:sqs:us-east-1:{ACCOUNT}:shortly-clicks", {}),
    ("logs:PutLogEvents", f"arn:aws:logs:us-east-1:{ACCOUNT}:log-group:/shortly/app:log-stream:i-0abc", {}),
    ("cloudwatch:PutMetricData", "*", {"cloudwatch:namespace": "Shortly"}),
]


def resource(template, name):
    found = template("iam")["Resources"].get(name)
    assert found is not None, f"infra/iam.yaml needs a resource with logical id {name}"
    return found


def test_role_name(template, render):
    role = resource(template, "AppRole")
    assert role["Type"] == "AWS::IAM::Role"
    assert render(role["Properties"].get("RoleName")) == "shortly-app", "RoleName: !Sub '${Prefix}-app'"


def test_only_ec2_can_assume(trust_policy, evaluator):
    trust = trust_policy("iam", "AppRole")
    assert evaluator.evaluate_trust(trust, "ec2.amazonaws.com"), "EC2 must be able to assume the app role"
    assert not evaluator.evaluate_trust(trust, "lambda.amazonaws.com")
    assert not evaluator.evaluate_trust(trust, f"arn:aws:iam::{ACCOUNT}:root")


def test_instance_profile(template, render):
    profile = resource(template, "AppInstanceProfile")
    assert profile["Type"] == "AWS::IAM::InstanceProfile"
    assert profile["Properties"].get("Roles") == [{"Ref": "AppRole"}], "Roles: [!Ref AppRole]"
    assert render(profile["Properties"].get("InstanceProfileName")) == "shortly-app"


def test_app_can_do_its_job(role_policies, evaluator):
    policies = role_policies("iam", "AppRole")
    for action, arn, context in NEEDS:
        decision = evaluator.evaluate_policies(policies, evaluator.Request(APP, action, arn, context))
        assert decision == "Allow", f"the app must be allowed {action} on {arn} (got {decision})"

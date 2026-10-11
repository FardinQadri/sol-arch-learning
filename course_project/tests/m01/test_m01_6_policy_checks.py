"""M01.6 — the whole IAM layer: no wildcards, ten things the app must never do, and it deploys."""
ACCOUNT = "111122223333"
APP = f"arn:aws:sts::{ACCOUNT}:assumed-role/shortly-app/i-0abc"
ROLES = ("AppRole", "ConsumerRole", "DeployerRole")
STAR_RESOURCE_OK = {"cloudwatch:PutMetricData"}  # PutMetricData has no resource ARN; limit it with a condition
NEVER = [
    ("dynamodb:DeleteTable", f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-clicks-daily", {}),
    ("dynamodb:PutItem", f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-clicks-daily", {}),
    ("s3:DeleteObject", f"arn:aws:s3:::shortly-assets-{ACCOUNT}/uploads/logo.png", {}),
    ("s3:GetObject", f"arn:aws:s3:::shortly-assets-{ACCOUNT}/private/keys.txt", {}),
    ("s3:PutBucketPolicy", f"arn:aws:s3:::shortly-assets-{ACCOUNT}", {}),
    ("sqs:ReceiveMessage", f"arn:aws:sqs:us-east-1:{ACCOUNT}:shortly-clicks", {}),
    ("sqs:DeleteQueue", f"arn:aws:sqs:us-east-1:{ACCOUNT}:shortly-clicks", {}),
    ("secretsmanager:GetSecretValue", f"arn:aws:secretsmanager:us-east-1:{ACCOUNT}:secret:prod/payments-x1Y2z3", {}),
    ("iam:CreateUser", "*", {}),
    ("cloudwatch:PutMetricData", "*", {"cloudwatch:namespace": "AWS/EC2"}),
]


def test_no_full_wildcard_action(role_policies, evaluator):
    for role in ROLES:
        for policy in role_policies("iam", role):
            for st in evaluator.statements(policy):
                assert "*" not in evaluator.as_list(st.get("Action")), f"{role} has Action: '*'"


def test_resource_star_only_for_metrics(role_policies, evaluator):
    for role in ROLES:
        for policy in role_policies("iam", role):
            for st in evaluator.statements(policy):
                if st.get("Effect") == "Allow" and "*" in evaluator.as_list(st.get("Resource")):
                    actions = set(evaluator.as_list(st.get("Action")))
                    assert actions <= STAR_RESOURCE_OK and st.get("Condition"), \
                        f"{role}: Resource '*' is only acceptable for {sorted(STAR_RESOURCE_OK)} with a Condition"


def test_ten_things_the_app_must_never_do(role_policies, evaluator):
    policies = role_policies("iam", "AppRole")
    for action, arn, context in NEVER:
        decision = evaluator.evaluate_policies(policies, evaluator.Request(APP, action, arn, context))
        assert decision != "Allow", f"the app must NOT be allowed {action} on {arn}"


def test_deploys_in_moto(moto_stacks):
    import boto3

    assert moto_stacks("iam") == "CREATE_COMPLETE"
    iam = boto3.client("iam")
    names = {r["RoleName"] for r in iam.list_roles()["Roles"]}
    assert {"shortly-app", "shortly-click-consumer", "shortly-deployer", "shortly-auditor"} <= names
    boundary = iam.get_role(RoleName="shortly-app")["Role"].get("PermissionsBoundary", {})
    assert boundary.get("PermissionsBoundaryArn", "").endswith(":policy/shortly-boundary")

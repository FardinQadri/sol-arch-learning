"""M05.3 — the app role may read the database secret RDS creates, and nothing else in Secrets Manager."""
import json

ACCOUNT = "111122223333"
SECRET = f"arn:aws:secretsmanager:us-east-1:{ACCOUNT}:secret:rds!db-1234abcd-0000-1111-2222-333344445555-AbCdEf"
OTHER = f"arn:aws:secretsmanager:us-east-1:{ACCOUNT}:secret:other-x"
APP = f"arn:aws:sts::{ACCOUNT}:assumed-role/shortly-app/i-0123456789abcdef0"


def concrete(document):
    """The rendered policy with the unresolved attribute reference swapped for the secret's ARN."""
    return json.loads(json.dumps(document).replace("Database.MasterUserSecret.SecretArn", SECRET))


def policy(resources):
    res = resources("data")
    assert res.get("AppDbSecretPolicy", {}).get("Type") == "AWS::IAM::Policy", \
        "add AppDbSecretPolicy (AWS::IAM::Policy) to infra/data.yaml: it adds a permission to the app role that M01 created"
    return res["AppDbSecretPolicy"]["Properties"]


def request(evaluator, resource=SECRET, action="secretsmanager:GetSecretValue"):
    return evaluator.Request(APP, action, resource, {})


def test_policy_is_attached_to_the_app_role(resources):
    props = policy(resources)
    assert props.get("Roles") == ["shortly-app"], "AppDbSecretPolicy Roles: [!Sub '${Prefix}-app'] (the role M01 created; reference it by name, the roles live in another stack)"
    assert props.get("PolicyName"), "AppDbSecretPolicy needs a PolicyName"


def test_one_statement_one_action_one_resource(resources):
    doc = policy(resources)["PolicyDocument"]
    statements = doc.get("Statement")
    statements = statements if isinstance(statements, list) else [statements]
    assert len(statements) == 1, f"AppDbSecretPolicy should have exactly one statement, found {len(statements)}"
    st = statements[0]
    assert st.get("Effect") == "Allow", "the statement Effect is Allow"
    assert st.get("Action") in ("secretsmanager:GetSecretValue", ["secretsmanager:GetSecretValue"]), \
        f"Action is {st.get('Action')!r}; the app only needs secretsmanager:GetSecretValue"
    assert st.get("Resource") == "Database.MasterUserSecret.SecretArn", \
        f"Resource is {st.get('Resource')!r}; use !GetAtt Database.MasterUserSecret.SecretArn — exactly the one secret RDS created, never '*'. (RDS names it rds!db-…, so M01's shortly/db-* statement does not cover it)"


def test_the_app_can_read_the_database_secret(resources, role_policies, evaluator):
    doc = concrete(policy(resources)["PolicyDocument"])
    identity = role_policies("iam", "AppRole") + [doc]
    decision = evaluator.evaluate_policies(identity, request(evaluator))
    assert decision == "Allow", f"the app role must be allowed GetSecretValue on the managed secret (got {decision})"
    assert evaluator.evaluate_policies([doc], request(evaluator)) == "Allow", "AppDbSecretPolicy alone must allow reading the secret; do not rely on other policies"


def test_the_app_cannot_read_other_secrets_through_this_policy(resources, evaluator):
    doc = concrete(policy(resources)["PolicyDocument"])
    decision = evaluator.evaluate_policies([doc], request(evaluator, OTHER))
    assert decision != "Allow", f"AppDbSecretPolicy must not allow other secrets such as {OTHER} (got {decision}); scope Resource to the one secret ARN"
    for action in ("secretsmanager:PutSecretValue", "secretsmanager:DeleteSecret", "secretsmanager:RotateSecret"):
        assert evaluator.evaluate_policies([doc], request(evaluator, action=action)) != "Allow", f"{action} must not be allowed: the app only reads the secret"


def test_the_permissions_boundary_still_allows_it(resources, evaluator):
    boundary = resources("iam")["AppBoundary"]["Properties"]["PolicyDocument"]
    doc = concrete(policy(resources)["PolicyDocument"])
    decision = evaluator.evaluate(request(evaluator), identity=[doc], boundary=boundary)
    assert decision == "Allow", \
        f"the identity policy and the M01 permissions boundary must both allow GetSecretValue (got {decision}); the boundary caps what any role can be granted, so the grant has to stay inside it"

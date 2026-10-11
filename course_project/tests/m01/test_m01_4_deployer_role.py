"""M01.4 — a deployer that may create roles only inside the permissions boundary."""
ACCOUNT = "111122223333"
BOUNDARY = f"arn:aws:iam::{ACCOUNT}:policy/shortly-boundary"
DEPLOYER = f"arn:aws:sts::{ACCOUNT}:assumed-role/shortly-deployer/alice"
FULL = {"Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]}


def deployer(role_policies, evaluator):
    policies = role_policies("iam", "DeployerRole")
    return lambda action, arn, **ctx: evaluator.evaluate_policies(policies, evaluator.Request(DEPLOYER, action, arn, ctx))


def test_boundary_policy(template, render):
    res = template("iam")["Resources"].get("AppBoundary")
    assert res and res["Type"] == "AWS::IAM::ManagedPolicy", "add AppBoundary (AWS::IAM::ManagedPolicy)"
    assert render(res["Properties"].get("ManagedPolicyName")) == "shortly-boundary"


def test_app_roles_carry_the_boundary(template):
    for role in ("AppRole", "ConsumerRole"):
        assert template("iam")["Resources"][role]["Properties"].get("PermissionsBoundary") == {"Ref": "AppBoundary"}, \
            f"{role} needs PermissionsBoundary: !Ref AppBoundary"


def test_boundary_blocks_escalation(template, render, evaluator):
    boundary = render(template("iam")["Resources"]["AppBoundary"]["Properties"]["PolicyDocument"])
    escalate = evaluator.Request(DEPLOYER, "iam:CreateUser", "*")
    assert evaluator.evaluate(escalate, identity=[FULL], boundary=boundary) != "Allow", "the boundary must not allow IAM"
    normal = evaluator.Request(DEPLOYER, "s3:GetObject", "arn:aws:s3:::x/y")
    assert evaluator.evaluate(normal, identity=[FULL], boundary=boundary) == "Allow", "the boundary must still allow the app's services"


def test_roles_only_with_the_boundary(role_policies, evaluator):
    decide = deployer(role_policies, evaluator)
    worker = f"arn:aws:iam::{ACCOUNT}:role/shortly-worker"
    assert decide("iam:CreateRole", worker, **{"iam:PermissionsBoundary": BOUNDARY}) == "Allow"
    assert decide("iam:CreateRole", worker) != "Allow", "creating a role WITHOUT the boundary must fail"
    assert decide("iam:CreateRole", worker, **{"iam:PermissionsBoundary": f"arn:aws:iam::{ACCOUNT}:policy/other"}) != "Allow"
    assert decide("iam:CreateRole", f"arn:aws:iam::{ACCOUNT}:role/admin", **{"iam:PermissionsBoundary": BOUNDARY}) != "Allow", \
        "only roles named shortly-*"


def test_boundary_cannot_be_removed(role_policies, evaluator):
    decide = deployer(role_policies, evaluator)
    assert decide("iam:DeleteRolePermissionsBoundary", f"arn:aws:iam::{ACCOUNT}:role/shortly-app") == "ExplicitDeny"
    assert decide("iam:CreatePolicyVersion", BOUNDARY) == "ExplicitDeny", "nobody may rewrite the boundary"


def test_pass_role_only_to_compute(role_policies, evaluator):
    decide = deployer(role_policies, evaluator)
    role = f"arn:aws:iam::{ACCOUNT}:role/shortly-app"
    assert decide("iam:PassRole", role, **{"iam:PassedToService": "ec2.amazonaws.com"}) == "Allow"
    assert decide("iam:PassRole", role, **{"iam:PassedToService": "lambda.amazonaws.com"}) == "Allow"
    assert decide("iam:PassRole", role, **{"iam:PassedToService": "glue.amazonaws.com"}) != "Allow"


def test_own_stacks_only(role_policies, evaluator):
    decide = deployer(role_policies, evaluator)
    assert decide("cloudformation:CreateStack", f"arn:aws:cloudformation:us-east-1:{ACCOUNT}:stack/shortly-network/1a2b") == "Allow"
    assert decide("cloudformation:CreateStack", f"arn:aws:cloudformation:us-east-1:{ACCOUNT}:stack/billing/1a2b") != "Allow"


def test_humans_need_mfa(trust_policy, evaluator):
    trust = trust_policy("iam", "DeployerRole")
    alice = f"arn:aws:iam::{ACCOUNT}:user/alice"
    assert evaluator.evaluate_trust(trust, alice, {"aws:MultiFactorAuthPresent": True})
    assert not evaluator.evaluate_trust(trust, alice, {"aws:MultiFactorAuthPresent": False})
    assert not evaluator.evaluate_trust(trust, "arn:aws:iam::444455556666:user/mallory", {"aws:MultiFactorAuthPresent": True})

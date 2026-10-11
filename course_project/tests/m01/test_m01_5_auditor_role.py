"""M01.5 — a read-only auditor role, assumable only with MFA, for one hour at a time."""
ACCOUNT = "111122223333"


def test_read_only_managed_policy(template, render):
    props = template("iam")["Resources"].get("AuditorRole", {}).get("Properties", {})
    arns = render(props.get("ManagedPolicyArns", []))
    assert any(a in arns for a in ("arn:aws:iam::aws:policy/ReadOnlyAccess", "arn:aws:iam::aws:policy/SecurityAudit")), \
        "attach the AWS managed ReadOnlyAccess (or SecurityAudit) policy"
    assert not props.get("Policies"), "the auditor gets no inline policies"
    assert render(props.get("RoleName")) == "shortly-auditor"


def test_one_hour_sessions(template):
    props = template("iam")["Resources"]["AuditorRole"]["Properties"]
    assert props.get("MaxSessionDuration") == 3600, "MaxSessionDuration: 3600"


def test_mfa_required(trust_policy, evaluator):
    trust = trust_policy("iam", "AuditorRole")
    bob = f"arn:aws:iam::{ACCOUNT}:user/bob"
    assert evaluator.evaluate_trust(trust, bob, {"aws:MultiFactorAuthPresent": True})
    assert not evaluator.evaluate_trust(trust, bob, {})
    assert not evaluator.evaluate_trust(trust, bob, {"aws:MultiFactorAuthPresent": False})

"""policy_eval — a small, readable model of AWS IAM policy evaluation.

This is the reference solution for week 01's drills 01–04: finish those drills before you read it.

The model (from the official IAM "Policy evaluation logic" page, simplified where noted):
  • A statement applies to a request when its Action/NotAction, Resource/NotResource and Condition
    all match — and, for resource-based and trust policies, its Principal/NotPrincipal.
  • Within a set of policies: any applicable Deny → "ExplicitDeny"; otherwise any applicable
    Allow → "Allow"; otherwise "ImplicitDeny" (the default).
  • evaluate() combines policy types: an explicit Deny anywhere wins; every SCP level must allow;
    the identity policy OR a same-account resource-based policy must allow (cross-account: BOTH
    must); a permissions boundary and a session policy, when present, must also allow.
  • Simplifications: no policy variables (${aws:username}); no Date operators; no resource control
    policies (RCPs); a permissions boundary also limits same-account resource-policy grants (in AWS
    it does not when the resource policy names an IAM user or a role session directly).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from ipaddress import ip_address, ip_network

ALLOW, EXPLICIT_DENY, IMPLICIT_DENY = "Allow", "ExplicitDeny", "ImplicitDeny"


@dataclass(frozen=True)
class Request:
    principal: str                 # caller ARN, e.g. arn:aws:sts::111122223333:assumed-role/app/i-0abc
    action: str                    # e.g. "s3:GetObject"
    resource: str                  # resource ARN, or "*" for actions without resources
    context: dict = field(default_factory=dict)   # condition keys, e.g. {"aws:SecureTransport": True}


def as_list(value) -> list:
    if value is None:
        return []
    return list(value) if isinstance(value, (list, tuple, set)) else [value]


def statements(policy: dict) -> list[dict]:
    found = (policy or {}).get("Statement", [])
    return [found] if isinstance(found, dict) else list(found)


def account_of(arn: str) -> str | None:
    parts = str(arn).split(":", 5)
    if len(parts) == 6 and parts[0] == "arn" and re.fullmatch(r"\d{12}", parts[4]):
        return parts[4]
    return None


def _glob(pattern: str, text: str, ignore_case: bool) -> bool:
    regex = "".join(".*" if c == "*" else "." if c == "?" else re.escape(c) for c in pattern)
    flags = re.DOTALL | (re.IGNORECASE if ignore_case else 0)
    return re.fullmatch(regex, text, flags) is not None


def action_matches(pattern: str, action: str) -> bool:
    """Actions are case-insensitive; * matches any characters, ? one character."""
    return _glob(pattern, action, ignore_case=True)


def resource_matches(pattern: str, arn: str) -> bool:
    """Resources are case-sensitive and compared segment by segment (a wildcard never spans ':')."""
    if pattern == "*":
        return True
    p_parts, a_parts = pattern.split(":", 5), arn.split(":", 5)
    if len(p_parts) != 6 or len(a_parts) != 6:
        return _glob(pattern, arn, ignore_case=False)
    return all(_glob(p, a, ignore_case=False) for p, a in zip(p_parts, a_parts))


_ROLE = re.compile(r"arn:[^:]+:iam::(\d{12}):role/(?:.*/)?([^/]+)")
_SESSION = re.compile(r"arn:[^:]+:sts::(\d{12}):assumed-role/([^/]+)/.+")
_ROOT = re.compile(r"arn:[^:]+:iam::(\d{12}):root")


def principal_matches(principal, caller_arn: str) -> bool:
    if principal == "*":
        return True
    if isinstance(principal, str):
        principal = {"AWS": principal}
    for kind, values in principal.items():
        for value in as_list(values):
            if value == "*":
                return True
            if kind != "AWS":
                if value == caller_arn:
                    return True
                continue
            root = _ROOT.fullmatch(value)
            account = value if re.fullmatch(r"\d{12}", value) else (root.group(1) if root else None)
            if account is not None:
                if account_of(caller_arn) == account:
                    return True
                continue
            if value == caller_arn:
                return True
            role, session = _ROLE.fullmatch(value), _SESSION.fullmatch(caller_arn)
            if role and session and role.groups() == session.groups():
                return True
    return False


# ── conditions ──────────────────────────────────────────────────────

_NEGATED = {"StringNotEquals": "StringEquals", "StringNotEqualsIgnoreCase": "StringEqualsIgnoreCase",
            "StringNotLike": "StringLike", "NumericNotEquals": "NumericEquals",
            "NotIpAddress": "IpAddress", "ArnNotEquals": "ArnEquals", "ArnNotLike": "ArnLike"}
_NUMERIC = {"NumericEquals": lambda x, y: x == y, "NumericLessThan": lambda x, y: x < y,
            "NumericLessThanEquals": lambda x, y: x <= y, "NumericGreaterThan": lambda x, y: x > y,
            "NumericGreaterThanEquals": lambda x, y: x >= y}
_POSITIVE = {"StringEquals", "StringEqualsIgnoreCase", "StringLike", "Bool", "IpAddress",
             "ArnEquals", "ArnLike", *_NUMERIC}
SUPPORTED = _POSITIVE | set(_NEGATED) | {"Null"}


def _parse_operator(name: str):
    qualifier = None
    for prefix, label in (("ForAnyValue:", "any"), ("ForAllValues:", "all")):
        if name.startswith(prefix):
            qualifier, name = label, name[len(prefix):]
    if_exists = name.endswith("IfExists") and name != "Null"
    if if_exists:
        name = name[: -len("IfExists")]
    if name not in SUPPORTED:
        raise ValueError(f"unsupported condition operator {name}")
    return qualifier, name, if_exists


def _value_matches(op: str, actual, expected) -> bool:
    a, e = str(actual), str(expected)
    if op == "StringEquals":
        return a == e
    if op == "StringEqualsIgnoreCase":
        return a.casefold() == e.casefold()
    if op == "StringLike":
        return _glob(e, a, ignore_case=False)
    if op in _NUMERIC:
        return _NUMERIC[op](float(a), float(e))
    if op == "Bool":
        return a.lower() == e.lower()
    if op == "IpAddress":
        return ip_address(a) in ip_network(e, strict=False)
    if op in ("ArnEquals", "ArnLike"):
        return resource_matches(e, a)
    raise ValueError(f"unsupported condition operator {op}")


def _one(op: str, actual, expected_values: list) -> bool:
    if op in _NEGATED:
        return not any(_value_matches(_NEGATED[op], actual, e) for e in expected_values)
    return any(_value_matches(op, actual, e) for e in expected_values)


def _lookup(context: dict, key: str):
    for name, value in context.items():
        if name.lower() == key.lower():
            return value
    return None


def condition_matches(condition: dict | None, context: dict) -> bool:
    """Every operator and every key in the block must hold (AND); several values for one key are
    alternatives (OR). Missing keys: false for positive operators, true for negated ones and for
    ...IfExists; ForAllValues passes on an empty or missing set, ForAnyValue fails."""
    for operator, block in (condition or {}).items():
        qualifier, op, if_exists = _parse_operator(operator)
        for key, expected in block.items():
            expected_values = as_list(expected)
            actual = _lookup(context, key)
            present = actual is not None and actual != []
            if op == "Null":
                if (str(expected_values[0]).lower() == "true") == present:
                    return False
                continue
            if not present:
                if qualifier == "any":
                    return False
                if if_exists or qualifier == "all" or op in _NEGATED:
                    continue
                return False
            actual_values = as_list(actual)
            check = all if qualifier == "all" else any
            if not check(_one(op, a, expected_values) for a in actual_values):
                return False
    return True


# ── statements and decisions ────────────────────────────────────────


def statement_applies(statement: dict, request: Request, *, check_principal: bool = False) -> bool:
    if check_principal:
        if "Principal" in statement:
            if not principal_matches(statement["Principal"], request.principal):
                return False
        elif "NotPrincipal" in statement:
            if principal_matches(statement["NotPrincipal"], request.principal):
                return False
        else:
            return False
    if "Action" in statement:
        ok = any(action_matches(p, request.action) for p in as_list(statement["Action"]))
    elif "NotAction" in statement:
        ok = not any(action_matches(p, request.action) for p in as_list(statement["NotAction"]))
    else:
        return False
    if not ok:
        return False
    if "Resource" in statement:
        ok = any(resource_matches(p, request.resource) for p in as_list(statement["Resource"]))
    elif "NotResource" in statement:
        ok = not any(resource_matches(p, request.resource) for p in as_list(statement["NotResource"]))
    else:
        ok = check_principal  # trust policies have no Resource; identity policies must
    return ok and condition_matches(statement.get("Condition"), request.context)


def _decide(policies, request: Request, check_principal: bool = False) -> str:
    allowed = False
    for policy in policies:
        for st in statements(policy):
            if statement_applies(st, request, check_principal=check_principal):
                if st.get("Effect") == "Deny":
                    return EXPLICIT_DENY
                if st.get("Effect") == "Allow":
                    allowed = True
    return ALLOW if allowed else IMPLICIT_DENY


def evaluate_policies(policies: list[dict], request: Request) -> str:
    """Identity-based policies only."""
    return _decide(policies, request)


def evaluate(request: Request, *, identity=(), resource_policy=None, scps=None, boundary=None,
             session=None, resource_account=None) -> str:
    identity = list(identity)
    every = identity + [p for p in (boundary, session) if p] + [p for level in (scps or []) for p in level]
    if _decide(every, request) == EXPLICIT_DENY:
        return EXPLICIT_DENY
    if resource_policy and _decide([resource_policy], request, check_principal=True) == EXPLICIT_DENY:
        return EXPLICIT_DENY
    for level in scps or []:
        if _decide(level, request) != ALLOW:
            return IMPLICIT_DENY
    identity_ok = _decide(identity, request) == ALLOW
    resource_ok = bool(resource_policy) and _decide([resource_policy], request, check_principal=True) == ALLOW
    caller_account = account_of(request.principal)
    target_account = resource_account or account_of(request.resource) or caller_account
    granted = (identity_ok and resource_ok) if caller_account != target_account else (identity_ok or resource_ok)
    if not granted:
        return IMPLICIT_DENY
    for limit in (boundary, session):
        if limit is not None and _decide([limit], request) != ALLOW:
            return IMPLICIT_DENY
    return ALLOW


def decide_resource_policy(policy: dict, request: Request) -> str:
    """Evaluate ONE resource-based policy on its own, matching the Principal element: "Allow",
    "ExplicitDeny" or "ImplicitDeny". Use it for callers that have no account, such as the service
    principal logdelivery.elasticloadbalancing.amazonaws.com (give it as request.principal; it matches
    a {"Service": ...} principal exactly), and to see what a bucket policy grants without any
    identity policy. For the full same-account / cross-account combination use evaluate()."""
    return _decide([policy], request, check_principal=True)


def evaluate_trust(trust_policy: dict, caller_arn: str, context: dict | None = None) -> bool:
    """May caller_arn call sts:AssumeRole on the role with this trust policy?"""
    request = Request(principal=caller_arn, action="sts:AssumeRole", resource="*", context=context or {})
    return _decide([trust_policy], request, check_principal=True) == ALLOW

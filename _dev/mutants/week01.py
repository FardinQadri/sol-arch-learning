"""Deliberately wrong implementations for week 01 — each must be caught by its drill."""
MUTANTS = [
    {"id": "case-sensitive-actions", "drill": 1, "code": '''
import fnmatch
from _harness.awslib.policy_eval import resource_matches
def action_matches(pattern, action):
    return fnmatch.fnmatchcase(action, pattern)
'''},
    {"id": "negated-missing-fails", "drill": 2, "code": '''
from _harness.awslib import policy_eval as _r
def condition_matches(condition, context):
    for operator, block in (condition or {}).items():
        if operator.startswith("StringNotEquals"):
            for key in block:
                if _r._lookup(context, key) is None:
                    return False
    return _r.condition_matches(condition, context)
'''},
    {"id": "first-match-wins", "drill": 3, "code": '''
from _harness.awslib.policy_eval import statements, statement_applies
def evaluate_policies(policies, request):
    for policy in policies:
        for st in statements(policy):
            if statement_applies(st, request):
                return "Allow" if st.get("Effect") == "Allow" else "ExplicitDeny"
    return "ImplicitDeny"
'''},
    {"id": "cross-account-either", "drill": 4, "code": '''
from _harness.awslib import policy_eval as _r
def evaluate(request, *, identity=(), resource_policy=None, scps=None, boundary=None, session=None, resource_account=None):
    return _r.evaluate(request, identity=identity, resource_policy=resource_policy, scps=scps, boundary=boundary,
                       session=session, resource_account=_r.account_of(request.principal))
'''},
    {"id": "s3-star-on-uploads", "drill": 5, "code": '''
APP_POLICY = {"Version": "2012-10-17", "Statement": [
    {"Effect": "Allow", "Action": "secretsmanager:GetSecretValue",
     "Resource": "arn:aws:secretsmanager:us-east-1:111122223333:secret:shortly/db-*"},
    {"Effect": "Allow", "Action": ["dynamodb:GetItem", "dynamodb:UpdateItem"],
     "Resource": "arn:aws:dynamodb:us-east-1:111122223333:table/shortly-clicks-daily"},
    {"Effect": "Allow", "Action": "s3:*", "Resource": "arn:aws:s3:::shortly-assets/uploads/*"},
    {"Effect": "Allow", "Action": "sqs:SendMessage", "Resource": "arn:aws:sqs:us-east-1:111122223333:shortly-clicks"},
]}
'''},
]


MUTANTS += [
    {"id": "one-big-statement", "drill": 6, "code": '''
def generate_policy(access_log):
    if not access_log:
        return {"Version": "2012-10-17", "Statement": []}
    return {"Version": "2012-10-17", "Statement": [{"Effect": "Allow",
        "Action": sorted({a for a, _ in access_log}), "Resource": sorted({r for _, r in access_log})}]}
'''},
    {"id": "base-identity", "drill": 7, "code": '''
import json, boto3
def create_app_role(iam, name, policy):
    trust = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "ec2.amazonaws.com"}, "Action": "sts:AssumeRole"}]}
    iam.create_role(RoleName=name, AssumeRolePolicyDocument=json.dumps(trust), Tags=[{"Key": "saa-course", "Value": "lab"}])
    iam.put_role_policy(RoleName=name, PolicyName=f"{name}-inline", PolicyDocument=json.dumps(policy))
    profile = iam.create_instance_profile(InstanceProfileName=name)["InstanceProfile"]
    iam.add_role_to_instance_profile(InstanceProfileName=name, RoleName=name)
    return profile["Arn"]
def whoami_as(role_arn, session_name):
    boto3.client("sts").assume_role(RoleArn=role_arn, RoleSessionName=session_name)
    return boto3.client("sts").get_caller_identity()["Arn"]
'''},
    {"id": "no-external-id", "drill": 8, "code": '''
import json
TRUST_POLICY = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow",
    "Principal": {"AWS": "arn:aws:iam::444455556666:root"}, "Action": "sts:AssumeRole"}]}
def create_partner_role(iam):
    return iam.create_role(RoleName="shortly-partner-read", AssumeRolePolicyDocument=json.dumps(TRUST_POLICY))["Role"]["Arn"]
'''},
    {"id": "no-global-exemption", "drill": 9, "code": '''
import json
def region_guardrail_scp(allowed_regions):
    return {"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Action": "*", "Resource": "*",
        "Condition": {"StringNotEquals": {"aws:RequestedRegion": list(allowed_regions)}}}]}
def attach_guardrail(org, target_id, allowed_regions):
    pid = org.create_policy(Content=json.dumps(region_guardrail_scp(allowed_regions)), Name="region-guardrail",
                            Description="x", Type="SERVICE_CONTROL_POLICY")["Policy"]["PolicySummary"]["Id"]
    org.attach_policy(PolicyId=pid, TargetId=target_id)
    return pid
def pooled_savings(usage_gb_by_account, tiers):
    alone = sum(prices.tiered_cost(gb, tiers) for gb in usage_gb_by_account.values())
    return round(alone - prices.tiered_cost(sum(usage_gb_by_account.values()), tiers), 2)
'''},
    {"id": "bucket-policy-not-enough", "drill": 10, "code": '''
PREDICTIONS = {1: "Deny", 2: "Deny", 3: "Deny", 4: "Deny", 5: "Deny", 6: "Allow"}
'''},
]

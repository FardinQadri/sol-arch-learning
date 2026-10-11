"""Reference solutions for week 01.

Drills 01–04: the course's reference evaluator IS the solution — read _harness/awslib/policy_eval.py
(action_matches, resource_matches, condition_matches, evaluate_policies, evaluate) and compare it with
yours. It is written to be read: short functions, one rule each.
"""
import json

import boto3

from _harness.awslib.policy_eval import (action_matches, condition_matches, evaluate,  # noqa: F401
                                         evaluate_policies, resource_matches)

APP_POLICY = {"Version": "2012-10-17", "Statement": [
    {"Sid": "ReadDbSecret", "Effect": "Allow", "Action": "secretsmanager:GetSecretValue",
     "Resource": f"arn:aws:secretsmanager:us-east-1:{ACCOUNT}:secret:shortly/db-*"},
    {"Sid": "ClickCounts", "Effect": "Allow", "Action": ["dynamodb:GetItem", "dynamodb:UpdateItem"],
     "Resource": f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-clicks-daily"},
    {"Sid": "Uploads", "Effect": "Allow", "Action": ["s3:GetObject", "s3:PutObject"],
     "Resource": "arn:aws:s3:::shortly-assets/uploads/*"},
    {"Sid": "SendClicks", "Effect": "Allow", "Action": "sqs:SendMessage",
     "Resource": f"arn:aws:sqs:us-east-1:{ACCOUNT}:shortly-clicks"},
]}


def generate_policy(access_log):
    by_resource = {}
    for action, resource in access_log:
        by_resource.setdefault(resource, set()).add(action)
    return {"Version": "2012-10-17", "Statement": [
        {"Effect": "Allow", "Action": sorted(actions), "Resource": resource}
        for resource, actions in sorted(by_resource.items())]}


EC2_TRUST = {"Version": "2012-10-17", "Statement": [
    {"Effect": "Allow", "Principal": {"Service": "ec2.amazonaws.com"}, "Action": "sts:AssumeRole"}]}


def create_app_role(iam, name, policy):
    iam.create_role(RoleName=name, AssumeRolePolicyDocument=json.dumps(EC2_TRUST),
                    Tags=[{"Key": "saa-course", "Value": "lab"}])
    iam.put_role_policy(RoleName=name, PolicyName=f"{name}-inline", PolicyDocument=json.dumps(policy))
    profile = iam.create_instance_profile(InstanceProfileName=name)["InstanceProfile"]
    iam.add_role_to_instance_profile(InstanceProfileName=name, RoleName=name)
    return profile["Arn"]


def whoami_as(role_arn, session_name):
    creds = boto3.client("sts").assume_role(RoleArn=role_arn, RoleSessionName=session_name)["Credentials"]
    sts = boto3.client("sts", aws_access_key_id=creds["AccessKeyId"], aws_secret_access_key=creds["SecretAccessKey"],
                       aws_session_token=creds["SessionToken"])
    return sts.get_caller_identity()["Arn"]


TRUST_POLICY = {"Version": "2012-10-17", "Statement": [{
    "Effect": "Allow", "Principal": {"AWS": f"arn:aws:iam::{PARTNER}:root"}, "Action": "sts:AssumeRole",
    "Condition": {"StringEquals": {"sts:ExternalId": "shortly-ext-42"}}}]}


def create_partner_role(iam):
    return iam.create_role(RoleName="shortly-partner-read", AssumeRolePolicyDocument=json.dumps(TRUST_POLICY))["Role"]["Arn"]


GLOBAL_SERVICES = ["iam:*", "organizations:*", "sts:*", "cloudfront:*", "route53:*", "support:*", "budgets:*"]


def region_guardrail_scp(allowed_regions):
    return {"Version": "2012-10-17", "Statement": [{
        "Sid": "DenyOutsideAllowedRegions", "Effect": "Deny", "NotAction": GLOBAL_SERVICES, "Resource": "*",
        "Condition": {"StringNotEquals": {"aws:RequestedRegion": list(allowed_regions)}}}]}


def attach_guardrail(org, target_id, allowed_regions):
    policy = org.create_policy(Content=json.dumps(region_guardrail_scp(allowed_regions)), Name="region-guardrail",
                               Description="Deny actions outside the allowed Regions", Type="SERVICE_CONTROL_POLICY")
    policy_id = policy["Policy"]["PolicySummary"]["Id"]
    org.attach_policy(PolicyId=policy_id, TargetId=target_id)
    return policy_id


def pooled_savings(usage_gb_by_account, tiers):
    alone = sum(prices.tiered_cost(gb, tiers) for gb in usage_gb_by_account.values())
    together = prices.tiered_cost(sum(usage_gb_by_account.values()), tiers)
    return round(alone - together, 2)


PREDICTIONS = {1: "Deny", 2: "Deny", 3: "Allow", 4: "Deny", 5: "Deny", 6: "Allow"}

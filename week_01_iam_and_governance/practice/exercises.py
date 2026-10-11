"""
Week 01 drills — IAM & multi-account governance
===============================================
Run:    python practice/exercises.py          every drill
        python practice/exercises.py 3        drill 3 only
Drills 01–04 build a small IAM policy evaluator — the logic behind half the questions in the
Secure domain. Do them in order: 03 uses 01 and 02; 04 uses 03.
The course's own evaluator (_harness/awslib/policy_eval.py) is the answer key for 01–04 — don't
open it until you are done. Drills 05–10 use it (as `ref`) to check the policies YOU write.
Everything runs offline against moto (a fake AWS) with fake credentials.
"""
import pathlib
import re  # noqa: F401  (you will want it)
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.awsdrill import Drill, run  # noqa: E402
from _harness.awslib import policy_eval as ref  # noqa: E402
from _harness.awslib import prices  # noqa: E402
from _harness.awslib.policy_eval import Request, account_of, principal_matches  # noqa: E402,F401

ACCOUNT = "111122223333"
PARTNER = "444455556666"
APP = f"arn:aws:sts::{ACCOUNT}:assumed-role/shortly-app/i-0abc"
FULL_ACCESS = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]}


def allow(action, resource="*", **extra):
    return {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": action, "Resource": resource, **extra}]}


def deny(action, resource="*", **extra):
    return {"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Action": action, "Resource": resource, **extra}]}


# ── Exercise 01 ★: Wildcards in actions and resources ────────────────
"""
action_matches(pattern, action) -> bool
    Actions are case-insensitive. In a pattern, * matches any run of characters and ? exactly one.
    action_matches("s3:Get*", "s3:GetObject") is True;  action_matches("ec2:*", "s3:GetObject") is False
resource_matches(pattern, arn) -> bool
    Resources are case-SENSITIVE. "*" alone matches everything. Otherwise split pattern and ARN into
    their six ':'-separated parts (split(":", 5)) and match part by part, so a wildcard never spans a
    ':' — "arn:aws:*:us-east-1:*:*" matches nothing in eu-west-1. Inside one part, * does match '/':
    "arn:aws:s3:::shortly-assets/*" matches "arn:aws:s3:::shortly-assets/uploads/a.png".
    If either side lacks six parts, compare the whole strings with the same wildcard rules.
Hint: build a regex — re.escape every character except * (→ ".*") and ? (→ "."), then re.fullmatch.
"""
def action_matches(pattern, action):
    raise NotImplementedError  # YOUR CODE


def resource_matches(pattern, arn):
    raise NotImplementedError  # YOUR CODE


class Ex01(Drill):
    """Wildcards in actions and resources ★"""
    tasks = ("1.1",)

    def test_actions(self):
        cases = [("s3:GetObject", "s3:GetObject", True), ("s3:getobject", "S3:GetObject", True),
                 ("s3:Get*", "s3:GetObjectTagging", True), ("*", "ec2:RunInstances", True),
                 ("s3:Get?bject", "s3:GetObject", True), ("s3:Get*", "s3:PutObject", False),
                 ("ec2:*", "s3:GetObject", False)]
        for pattern, action, want in cases:
            with self.subTest(pattern=pattern, action=action):
                self.assertIs(action_matches(pattern, action), want)

    def test_resources(self):
        obj = "arn:aws:s3:::shortly-assets/uploads/a.png"
        cases = [("*", obj, True), ("arn:aws:s3:::shortly-assets/*", obj, True),
                 ("arn:aws:s3:::shortly-assets", obj, False), ("arn:aws:s3:::Shortly-assets/*", obj, False),
                 ("arn:aws:dynamodb:*:*:table/shortly-*", f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-links", True),
                 ("arn:aws:dynamodb:*:*:table/shortly-*", f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/billing", False),
                 ("arn:aws:*:us-east-1:*:*", f"arn:aws:sqs:eu-west-1:{ACCOUNT}:clicks", False),
                 ("arn:aws:lambda:us-east-1:*:function:f*", f"arn:aws:lambda:us-east-1:{ACCOUNT}:function:fn:PROD", True)]
        for pattern, arn, want in cases:
            with self.subTest(pattern=pattern, arn=arn):
                self.assertIs(resource_matches(pattern, arn), want)


# ── Exercise 02 ★: Conditions ────────────────────────────────────────
"""
condition_matches(condition, context) -> bool
`condition` is a statement's Condition block (or None); `context` holds the request's keys:
    {"StringEquals": {"aws:RequestedRegion": ["us-east-1", "eu-west-1"]}, "Bool": {"aws:SecureTransport": "true"}}
Rules (from the IAM documentation):
  • every operator, and every key inside it, must hold (AND); several values for ONE key are alternatives (OR)
  • condition keys are case-insensitive ("aws:sourceip" finds "aws:SourceIp")
  • support: StringEquals, StringNotEquals, StringEqualsIgnoreCase, StringLike (wildcards, case-sensitive),
    Bool (compare "true"/"false"; the context may hold True/False), IpAddress, NotIpAddress (CIDR blocks),
    NumericEquals, NumericLessThan, NumericLessThanEquals, NumericGreaterThan, NumericGreaterThanEquals,
    and Null ("true" means the key must be ABSENT, "false" that it must be present)
  • the suffix …IfExists: when the key is absent, that operator passes
  • when a key is absent: positive operators fail; negated ones (StringNotEquals, NotIpAddress) pass
  • ForAnyValue: / ForAllValues: prefixes, for keys whose context value is a list:
        ForAnyValue → at least one context value matches; absent or empty → fails
        ForAllValues → every context value matches; absent or empty → PASSES (a classic trap)
  • any other operator → ValueError
Hint: write one helper that compares ONE context value with ONE policy value, then build up from it.
"""
def condition_matches(condition, context):
    raise NotImplementedError  # YOUR CODE


class Ex02(Drill):
    """Conditions ★"""
    tasks = ("1.1",)

    CASES = [
        (None, {}, True),
        ({"StringEquals": {"aws:RequestedRegion": ["us-east-1", "eu-west-1"]}}, {"aws:RequestedRegion": "eu-west-1"}, True),
        ({"StringEquals": {"aws:RequestedRegion": "us-east-1"}}, {"aws:requestedregion": "us-east-1"}, True),
        ({"StringEquals": {"aws:RequestedRegion": "us-east-1"}}, {}, False),
        ({"StringNotEquals": {"aws:RequestedRegion": ["us-east-1", "us-west-2"]}}, {"aws:RequestedRegion": "eu-west-1"}, True),
        ({"StringNotEquals": {"aws:RequestedRegion": ["us-east-1", "us-west-2"]}}, {"aws:RequestedRegion": "us-west-2"}, False),
        ({"StringNotEquals": {"aws:RequestedRegion": "us-east-1"}}, {}, True),
        ({"StringLike": {"s3:prefix": "home/*"}}, {"s3:prefix": "home/alice/"}, True),
        ({"StringLike": {"s3:prefix": "home/*"}}, {"s3:prefix": "Home/alice/"}, False),
        ({"StringEqualsIgnoreCase": {"aws:PrincipalTag/team": "Data"}}, {"aws:PrincipalTag/team": "data"}, True),
        ({"Bool": {"aws:SecureTransport": "true"}}, {"aws:SecureTransport": True}, True),
        ({"Bool": {"aws:SecureTransport": "true"}}, {"aws:SecureTransport": False}, False),
        ({"Bool": {"aws:MultiFactorAuthPresent": "true"}}, {}, False),
        ({"BoolIfExists": {"aws:MultiFactorAuthPresent": "false"}}, {}, True),
        ({"IpAddress": {"aws:SourceIp": "203.0.113.0/24"}}, {"aws:SourceIp": "203.0.113.7"}, True),
        ({"NotIpAddress": {"aws:SourceIp": ["203.0.113.0/24", "198.51.100.0/24"]}}, {"aws:SourceIp": "192.0.2.1"}, True),
        ({"NumericLessThanEquals": {"s3:max-keys": "100"}}, {"s3:max-keys": 50}, True),
        ({"NumericGreaterThan": {"s3:max-keys": "100"}}, {"s3:max-keys": 50}, False),
        ({"Null": {"aws:TokenIssueTime": "true"}}, {}, True),
        ({"Null": {"aws:TokenIssueTime": "false"}}, {}, False),
        ({"ForAnyValue:StringEquals": {"aws:TagKeys": ["env", "team"]}}, {"aws:TagKeys": ["owner", "env"]}, True),
        ({"ForAnyValue:StringEquals": {"aws:TagKeys": ["env"]}}, {}, False),
        ({"ForAllValues:StringEquals": {"aws:TagKeys": ["env", "team"]}}, {"aws:TagKeys": ["env", "owner"]}, False),
        ({"ForAllValues:StringEquals": {"aws:TagKeys": ["env"]}}, {}, True),
        ({"StringEquals": {"a": "1"}, "Bool": {"b": "true"}}, {"a": "1", "b": False}, False),
        ({"StringEquals": {"a": "1", "c": "2"}}, {"a": "1", "c": "3"}, False),
    ]

    def test_cases(self):
        for condition, context, want in self.CASES:
            with self.subTest(condition=condition, context=context):
                self.assertIs(condition_matches(condition, context), want)

    def test_unknown_operator(self):
        with self.assertRaises(ValueError):
            condition_matches({"StringSoundsLike": {"a": "b"}}, {"a": "b"})


# ── Exercise 03 ★: Evaluate identity policies ────────────────────────
"""
evaluate_policies(policies, request) -> "Allow" | "ExplicitDeny" | "ImplicitDeny"
`policies` are identity-based policy documents; `request` is a Request(principal, action, resource, context).
A statement applies when ALL of these hold:
  • its Action matches (any pattern in it) — or, with NotAction, the action matches NONE of them
  • its Resource matches — or, with NotResource, matches none (a statement with neither never applies)
  • its Condition holds
Then: any applicable Deny → "ExplicitDeny" (even when an Allow also applies); otherwise any applicable
Allow → "Allow"; otherwise "ImplicitDeny" — the default when nothing says yes.
"Statement" may be one dict or a list; Action/NotAction/Resource/NotResource may be a string or a list.
Use YOUR action_matches, resource_matches and condition_matches.
Example: evaluate_policies([allow("s3:*"), deny("s3:DeleteObject")], Request(APP, "s3:DeleteObject", "*")) == "ExplicitDeny"
"""
def evaluate_policies(policies, request):
    raise NotImplementedError  # YOUR CODE


class Ex03(Drill):
    """Evaluate identity policies ★"""
    tasks = ("1.1",)

    def test_deny_beats_allow_in_any_order(self):
        policies = [allow("s3:*", "arn:aws:s3:::shortly-assets/*"), deny("s3:DeleteObject")]
        self.assertEqual(evaluate_policies(policies, Request(APP, "s3:GetObject", "arn:aws:s3:::shortly-assets/a")), "Allow")
        self.assertEqual(evaluate_policies(policies, Request(APP, "s3:DeleteObject", "arn:aws:s3:::shortly-assets/a")), "ExplicitDeny")

    def test_nothing_says_yes(self):
        self.assertEqual(evaluate_policies([allow("s3:GetObject")], Request(APP, "ec2:RunInstances", "*")), "ImplicitDeny")
        self.assertEqual(evaluate_policies([], Request(APP, "s3:GetObject", "*")), "ImplicitDeny")

    def test_not_action_and_not_resource(self):
        guard = {"Statement": {"Effect": "Deny", "NotAction": ["iam:*", "sts:*"], "Resource": "*"}}
        self.assertEqual(evaluate_policies([FULL_ACCESS, guard], Request(APP, "s3:PutObject", "*")), "ExplicitDeny")
        self.assertEqual(evaluate_policies([FULL_ACCESS, guard], Request(APP, "iam:ListRoles", "*")), "Allow")
        most = {"Statement": [{"Effect": "Allow", "Action": "s3:*", "NotResource": "arn:aws:s3:::secrets/*"}]}
        self.assertEqual(evaluate_policies([most], Request(APP, "s3:GetObject", "arn:aws:s3:::secrets/k")), "ImplicitDeny")

    def test_conditions_are_used(self):
        tls_only = allow("s3:GetObject", Condition={"Bool": {"aws:SecureTransport": "true"}})
        self.assertEqual(evaluate_policies([tls_only], Request(APP, "s3:GetObject", "*", {"aws:SecureTransport": True})), "Allow")
        self.assertEqual(evaluate_policies([tls_only], Request(APP, "s3:GetObject", "*", {"aws:SecureTransport": False})), "ImplicitDeny")

    def test_statement_without_resource_never_applies(self):
        broken = {"Statement": [{"Effect": "Allow", "Action": "s3:GetObject"}]}
        self.assertEqual(evaluate_policies([broken], Request(APP, "s3:GetObject", "*")), "ImplicitDeny")


# ── Exercise 04 ★: Every policy type together ────────────────────────
"""
evaluate(request, *, identity=(), resource_policy=None, scps=None, boundary=None, session=None,
         resource_account=None) -> "Allow" | "ExplicitDeny" | "ImplicitDeny"
Combine the policy types the way AWS does:
  1. an explicit Deny in ANY of them (identity, resource, SCPs, boundary, session) → "ExplicitDeny"
  2. scps is a list of LEVELS (root → OU → account), each a list of SCP documents. EVERY level must
     allow the action — SCPs never grant anything by themselves — otherwise "ImplicitDeny"
  3. the identity policies OR the resource-based policy must allow it. Cross-account — when the
     caller's account, account_of(request.principal), differs from the resource's account
     (resource_account, else account_of(request.resource)) — BOTH must allow it
  4. a permissions boundary and a session policy, when given, must also allow it
  5. otherwise → "Allow"
A resource-based policy (e.g. a bucket policy) is like an identity policy except each statement also
needs its Principal to match the caller: use principal_matches(statement["Principal"], request.principal)
— it and account_of are given to you. Use your evaluate_policies for the identity-style policy sets.
(Real AWS has one corner this ignores: a same-account resource policy that names an IAM user directly
is not limited by that user's permissions boundary. The exam almost never goes there.)
"""
def evaluate(request, *, identity=(), resource_policy=None, scps=None, boundary=None, session=None, resource_account=None):
    raise NotImplementedError  # YOUR CODE


class Ex04(Drill):
    """Every policy type together ★"""
    tasks = ("1.1",)
    GET = Request(APP, "s3:GetObject", "arn:aws:s3:::shortly-assets/a.png")

    def test_scp_levels(self):
        self.assertEqual(evaluate(self.GET, identity=[FULL_ACCESS], scps=[[FULL_ACCESS], [FULL_ACCESS]]), "Allow")
        self.assertEqual(evaluate(self.GET, identity=[FULL_ACCESS], scps=[[FULL_ACCESS], [allow("ec2:*")]]), "ImplicitDeny")
        self.assertEqual(evaluate(self.GET, identity=[FULL_ACCESS], scps=[[FULL_ACCESS, deny("s3:*")]]), "ExplicitDeny")
        self.assertEqual(evaluate(self.GET, identity=[], scps=[[FULL_ACCESS]]), "ImplicitDeny")

    def test_boundary_and_session(self):
        both = [allow(["s3:*", "ec2:*"])]
        self.assertEqual(evaluate(Request(APP, "ec2:RunInstances", "*"), identity=both, boundary=allow("s3:*")), "ImplicitDeny")
        self.assertEqual(evaluate(self.GET, identity=both, boundary=allow("s3:*")), "Allow")
        self.assertEqual(evaluate(self.GET, identity=both, session=allow("s3:List*")), "ImplicitDeny")

    def test_same_account_bucket_policy_is_enough(self):
        bucket = {"Statement": [{"Effect": "Allow", "Principal": {"AWS": f"arn:aws:iam::{ACCOUNT}:role/shortly-app"},
                                 "Action": "s3:GetObject", "Resource": "arn:aws:s3:::shortly-assets/*"}]}
        self.assertEqual(evaluate(self.GET, resource_policy=bucket, resource_account=ACCOUNT), "Allow")
        other = {"Statement": [{**bucket["Statement"][0], "Principal": {"AWS": f"arn:aws:iam::{ACCOUNT}:role/someone-else"}}]}
        self.assertEqual(evaluate(self.GET, resource_policy=other, resource_account=ACCOUNT), "ImplicitDeny")

    def test_cross_account_needs_both(self):
        partner = Request(f"arn:aws:iam::{PARTNER}:role/reporting", "s3:GetObject", "arn:aws:s3:::shortly-assets/r.csv")
        bucket = {"Statement": [{"Effect": "Allow", "Principal": {"AWS": f"arn:aws:iam::{PARTNER}:root"},
                                 "Action": "s3:GetObject", "Resource": "arn:aws:s3:::shortly-assets/*"}]}
        theirs = [allow("s3:GetObject", "arn:aws:s3:::shortly-assets/*")]
        self.assertEqual(evaluate(partner, identity=theirs, resource_account=ACCOUNT), "ImplicitDeny")
        self.assertEqual(evaluate(partner, resource_policy=bucket, resource_account=ACCOUNT), "ImplicitDeny")
        self.assertEqual(evaluate(partner, identity=theirs, resource_policy=bucket, resource_account=ACCOUNT), "Allow")

    def test_bucket_policy_deny_wins(self):
        tls = {"Statement": [{"Effect": "Deny", "Principal": "*", "Action": "s3:*", "Resource": "*",
                              "Condition": {"Bool": {"aws:SecureTransport": "false"}}}]}
        plain = Request(APP, "s3:GetObject", "arn:aws:s3:::shortly-assets/a.png", {"aws:SecureTransport": False})
        self.assertEqual(evaluate(plain, identity=[allow("s3:GetObject")], resource_policy=tls), "ExplicitDeny")


# ── Exercise 05 (fix the bug): Least privilege ───────────────────────
"""
shortly's web app needs exactly these permissions (account 111122223333, Region us-east-1):
  1. read its database secret:   secretsmanager:GetSecretValue on
                                 arn:aws:secretsmanager:us-east-1:111122223333:secret:shortly/db-*
  2. read and update daily click counts:  dynamodb:GetItem and dynamodb:UpdateItem on
                                 arn:aws:dynamodb:us-east-1:111122223333:table/shortly-clicks-daily
  3. read and write user uploads: s3:GetObject and s3:PutObject on arn:aws:s3:::shortly-assets/uploads/*
  4. queue click events:          sqs:SendMessage on arn:aws:sqs:us-east-1:111122223333:shortly-clicks
BROAD_POLICY was written in a hurry: it lets the app delete every table, bucket and secret in the
account — and it still forgot the queue, so click events fail. Replace APP_POLICY with a policy that
allows exactly those actions on exactly those resources:
no "*" inside any Action, and no Resource that is just "*". (Secrets Manager adds 6 random characters
to secret ARNs, which is why need 1 ends in "db-*".)
The tests check your policy with the course's reference evaluator.
"""
BROAD_POLICY = {"Version": "2012-10-17", "Statement": [
    {"Effect": "Allow", "Action": ["s3:*", "dynamodb:*", "secretsmanager:*"], "Resource": "*"}]}
APP_POLICY = BROAD_POLICY   # FIX ME


class Ex05(Drill):
    """Least privilege (fix the bug)"""
    tasks = ("1.1", "1.2")
    NEEDS = [
        ("secretsmanager:GetSecretValue", f"arn:aws:secretsmanager:us-east-1:{ACCOUNT}:secret:shortly/db-a1B2c3"),
        ("dynamodb:GetItem", f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-clicks-daily"),
        ("dynamodb:UpdateItem", f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-clicks-daily"),
        ("s3:GetObject", "arn:aws:s3:::shortly-assets/uploads/logo.png"),
        ("s3:PutObject", "arn:aws:s3:::shortly-assets/uploads/logo.png"),
        ("sqs:SendMessage", f"arn:aws:sqs:us-east-1:{ACCOUNT}:shortly-clicks"),
    ]
    MUST_NOT = [
        ("dynamodb:DeleteTable", f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-clicks-daily"),
        ("dynamodb:GetItem", f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/billing"),
        ("s3:DeleteObject", "arn:aws:s3:::shortly-assets/uploads/logo.png"),
        ("s3:GetObject", "arn:aws:s3:::shortly-assets/private/keys.txt"),
        ("s3:PutBucketPolicy", "arn:aws:s3:::shortly-assets"),
        ("sqs:DeleteQueue", f"arn:aws:sqs:us-east-1:{ACCOUNT}:shortly-clicks"),
        ("sqs:ReceiveMessage", f"arn:aws:sqs:us-east-1:{ACCOUNT}:shortly-clicks"),
        ("secretsmanager:GetSecretValue", f"arn:aws:secretsmanager:us-east-1:{ACCOUNT}:secret:prod/payments-x1Y2z3"),
        ("secretsmanager:DeleteSecret", f"arn:aws:secretsmanager:us-east-1:{ACCOUNT}:secret:shortly/db-a1B2c3"),
    ]

    def test_can_do_its_job(self):
        for action, arn in self.NEEDS:
            with self.subTest(action=action):
                self.assertEqual(ref.evaluate_policies([APP_POLICY], Request(APP, action, arn)), "Allow",
                                 f"the app still needs {action} on {arn}")

    def test_cannot_do_anything_else(self):
        for action, arn in self.MUST_NOT:
            with self.subTest(action=action, arn=arn):
                self.assertNotEqual(ref.evaluate_policies([APP_POLICY], Request(APP, action, arn)), "Allow",
                                    f"the app must NOT be allowed {action} on {arn}")

    def test_no_wildcard_actions_or_star_resources(self):
        for st in ref.statements(APP_POLICY):
            with self.subTest(statement=st):
                self.assertFalse(any("*" in a for a in ref.as_list(st.get("Action"))), "no * inside any Action")
                self.assertNotIn("*", ref.as_list(st.get("Resource")), 'no Resource that is just "*"')


# ── Exercise 06 ★: Write the policy from what the app really did ─────
"""
generate_policy(access_log) -> dict
access_log lists the (action, resource) pairs your app actually called — what IAM Access Analyzer
reads from CloudTrail when it generates a policy. Return the least-privilege policy document:
    {"Version": "2012-10-17", "Statement": [...]}
with ONE Allow statement per distinct resource: "Action" = the sorted distinct actions used on that
resource, "Resource" = that ARN. Sort the statements by resource. Repeats in the log appear once.
Example:
  generate_policy([("s3:GetObject", "arn:aws:s3:::b/k"), ("s3:GetObject", "arn:aws:s3:::b/k")]) ==
      {"Version": "2012-10-17", "Statement": [
          {"Effect": "Allow", "Action": ["s3:GetObject"], "Resource": "arn:aws:s3:::b/k"}]}
Why not one statement with every action and every resource? Because it would also allow every
action on every OTHER resource in the list.
"""
def generate_policy(access_log):
    raise NotImplementedError  # YOUR CODE


class Ex06(Drill):
    """Write the policy from what the app really did ★"""
    tasks = ("1.1",)
    TABLE = f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-clicks-daily"
    QUEUE = f"arn:aws:sqs:us-east-1:{ACCOUNT}:shortly-clicks"
    LOG = [("sqs:SendMessage", QUEUE), ("dynamodb:GetItem", TABLE), ("dynamodb:UpdateItem", TABLE),
           ("sqs:SendMessage", QUEUE), ("s3:PutObject", "arn:aws:s3:::shortly-assets/uploads/a.png")]

    def test_example(self):
        self.assertEqual(generate_policy([("s3:GetObject", "arn:aws:s3:::b/k")] * 2), {"Version": "2012-10-17", "Statement": [
            {"Effect": "Allow", "Action": ["s3:GetObject"], "Resource": "arn:aws:s3:::b/k"}]})

    def test_shape(self):
        policy = generate_policy(self.LOG)
        self.assertEqual([s["Resource"] for s in policy["Statement"]],
                         sorted({"arn:aws:s3:::shortly-assets/uploads/a.png", self.TABLE, self.QUEUE}))
        table = next(s for s in policy["Statement"] if s["Resource"] == self.TABLE)
        self.assertEqual(table["Action"], ["dynamodb:GetItem", "dynamodb:UpdateItem"])

    def test_allows_exactly_the_log(self):
        policy = generate_policy(self.LOG)
        for action, arn in self.LOG:
            self.assertEqual(ref.evaluate_policies([policy], Request(APP, action, arn)), "Allow")
        for action, arn in [("sqs:SendMessage", self.TABLE), ("dynamodb:GetItem", self.QUEUE), ("dynamodb:DeleteItem", self.TABLE)]:
            with self.subTest(action=action, arn=arn):
                self.assertEqual(ref.evaluate_policies([policy], Request(APP, action, arn)), "ImplicitDeny")

    def test_empty_log(self):
        self.assertEqual(generate_policy([]), {"Version": "2012-10-17", "Statement": []})


# ── Exercise 07: Roles and temporary credentials ─────────────────────
"""
create_app_role(iam, name, policy) -> str
    Create IAM role `name` that EC2 may assume (trust policy: Effect Allow, Principal
    {"Service": "ec2.amazonaws.com"}, Action "sts:AssumeRole"), tagged {"saa-course": "lab"}; add
    `policy` as an inline policy named f"{name}-inline"; create an instance profile with the same name;
    add the role to it; return the instance profile's ARN. (EC2 instances get a role ONLY through an
    instance profile — this is why the app never needs access keys.)
whoami_as(role_arn, session_name) -> str
    Call STS AssumeRole, then make a NEW STS client with the temporary credentials it returned and
    return the "Arn" from get_caller_identity. In AWS it looks like
    arn:aws:sts::ACCOUNT:assumed-role/ROLE_NAME/SESSION_NAME — that is what CloudTrail records.
Hint: boto3.client("sts", aws_access_key_id=…, aws_secret_access_key=…, aws_session_token=…)
"""
def create_app_role(iam, name, policy):
    raise NotImplementedError  # YOUR CODE


def whoami_as(role_arn, session_name):
    raise NotImplementedError  # YOUR CODE


class Ex07(Drill):
    """Roles and temporary credentials"""
    tasks = ("1.1",)
    uses_aws = True
    POLICY = allow("sqs:SendMessage", "arn:aws:sqs:us-east-1:123456789012:shortly-clicks")

    def test_create_app_role(self):
        iam = self.client("iam")
        arn = create_app_role(iam, "shortly-app", self.POLICY)
        self.assertTrue(arn.endswith(":instance-profile/shortly-app"), arn)
        role = iam.get_role(RoleName="shortly-app")["Role"]
        statement = role["AssumeRolePolicyDocument"]["Statement"][0]
        self.assertEqual(statement["Principal"], {"Service": "ec2.amazonaws.com"})
        self.assertIn({"Key": "saa-course", "Value": "lab"}, role.get("Tags", []))
        inline = iam.get_role_policy(RoleName="shortly-app", PolicyName="shortly-app-inline")["PolicyDocument"]
        self.assertEqual(inline, self.POLICY)
        profile = iam.get_instance_profile(InstanceProfileName="shortly-app")["InstanceProfile"]
        self.assertEqual([r["RoleName"] for r in profile["Roles"]], ["shortly-app"])

    def test_whoami_as(self):
        iam = self.client("iam")
        trust = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::123456789012:root"},
                                                         "Action": "sts:AssumeRole"}]}
        role = iam.create_role(RoleName="shortly-ops", AssumeRolePolicyDocument=json.dumps(trust))["Role"]
        self.assertEqual(whoami_as(role["Arn"], "drill-session"),
                         "arn:aws:sts::123456789012:assumed-role/shortly-ops/drill-session")


# ── Exercise 08: A trust policy for a partner (confused deputy) ──────
"""
A partner (account 444455556666) runs a reporting tool that reads your data through a role in YOUR
account. Write TRUST_POLICY (a trust policy document) so that:
  • only the partner's account may call sts:AssumeRole on it,
  • and only when it passes the external ID "shortly-ext-42" — this stops the "confused deputy":
    another customer of the same partner cannot trick the tool into using YOUR role,
  • nobody in your own account and no AWS service can assume it.
Then create_partner_role(iam) creates the role "shortly-partner-read" with TRUST_POLICY and returns its ARN.
Hint: the external ID arrives as the condition key "sts:ExternalId".
"""
import json  # noqa: E402

TRUST_POLICY = None   # YOUR POLICY (a dict)


def create_partner_role(iam):
    raise NotImplementedError  # YOUR CODE


class Ex08(Drill):
    """A trust policy for a partner"""
    tasks = ("1.1",)
    uses_aws = True
    PARTNER_ROLE = f"arn:aws:iam::{PARTNER}:role/reporting-tool"

    def test_partner_with_external_id(self):
        self.assertIsInstance(TRUST_POLICY, dict, "write TRUST_POLICY as a dict")
        self.assertTrue(ref.evaluate_trust(TRUST_POLICY, self.PARTNER_ROLE, {"sts:ExternalId": "shortly-ext-42"}))

    def test_everyone_else_is_refused(self):
        self.assertIsInstance(TRUST_POLICY, dict, "write TRUST_POLICY as a dict")
        cases = [(self.PARTNER_ROLE, {"sts:ExternalId": "guess"}), (self.PARTNER_ROLE, {}),
                 (f"arn:aws:iam::{ACCOUNT}:role/admin", {"sts:ExternalId": "shortly-ext-42"}),
                 ("ec2.amazonaws.com", {"sts:ExternalId": "shortly-ext-42"})]
        for caller, context in cases:
            with self.subTest(caller=caller, context=context):
                self.assertFalse(ref.evaluate_trust(TRUST_POLICY, caller, context))

    def test_create_partner_role(self):
        iam = self.client("iam")
        arn = create_partner_role(iam)
        self.assertEqual(arn, "arn:aws:iam::123456789012:role/shortly-partner-read")
        self.assertEqual(iam.get_role(RoleName="shortly-partner-read")["Role"]["AssumeRolePolicyDocument"], TRUST_POLICY)


# ── Exercise 09: Guardrails and consolidated billing ─────────────────
"""
region_guardrail_scp(allowed_regions) -> dict
    A service control policy that DENIES every action when aws:RequestedRegion is not one of
    allowed_regions — except global services, which you must exempt with NotAction:
    iam:*, organizations:*, sts:*, cloudfront:*, route53:*, support:*, budgets:*.
    (SCPs only take away. Accounts still need FullAWSAccess at every level and their own IAM Allow.)
attach_guardrail(org, target_id, allowed_regions) -> str
    Create the SCP in AWS Organizations (Name "region-guardrail", Type "SERVICE_CONTROL_POLICY",
    Content = json.dumps(...)), attach it to target_id (an OU or account id), return the policy id.
pooled_savings(usage_gb_by_account, tiers) -> float
    Consolidated billing adds usage across all accounts BEFORE applying tiered prices, so the
    organisation reaches cheaper tiers sooner. Return (each account billed alone) − (all accounts
    billed together), rounded to 2 decimal places. Use prices.tiered_cost(quantity, tiers).
"""
def region_guardrail_scp(allowed_regions):
    raise NotImplementedError  # YOUR CODE


def attach_guardrail(org, target_id, allowed_regions):
    raise NotImplementedError  # YOUR CODE


def pooled_savings(usage_gb_by_account, tiers):
    raise NotImplementedError  # YOUR CODE


class Ex09(Drill):
    """Guardrails and consolidated billing"""
    tasks = ("1.1", "4.1")
    uses_aws = True
    ALLOWED = ["us-east-1", "us-west-2"]

    def decide(self, action, region):
        request = Request(APP, action, "*", {"aws:RequestedRegion": region})
        return ref.evaluate(request, identity=[FULL_ACCESS], scps=[[FULL_ACCESS, region_guardrail_scp(self.ALLOWED)]])

    def test_guardrail_decisions(self):
        cases = {("s3:PutObject", "eu-west-1"): "ExplicitDeny", ("ec2:RunInstances", "ap-south-1"): "ExplicitDeny",
                 ("s3:PutObject", "us-east-1"): "Allow", ("ec2:RunInstances", "us-west-2"): "Allow",
                 ("iam:CreateRole", "eu-west-1"): "Allow", ("sts:GetCallerIdentity", "ap-south-1"): "Allow",
                 ("cloudfront:CreateDistribution", "eu-west-1"): "Allow"}
        for (action, region), want in cases.items():
            with self.subTest(action=action, region=region):
                self.assertEqual(self.decide(action, region), want)

    def test_attach_in_organizations(self):
        org = self.client("organizations")
        org.create_organization(FeatureSet="ALL")
        root = org.list_roots()["Roots"][0]["Id"]
        ou = org.create_organizational_unit(ParentId=root, Name="workloads")["OrganizationalUnit"]["Id"]
        policy_id = attach_guardrail(org, ou, self.ALLOWED)
        names = [p["Name"] for p in org.list_policies_for_target(TargetId=ou, Filter="SERVICE_CONTROL_POLICY")["Policies"]]
        self.assertIn("region-guardrail", names)
        content = json.loads(org.describe_policy(PolicyId=policy_id)["Policy"]["Content"])
        self.assertEqual(content, region_guardrail_scp(self.ALLOWED))

    def test_pooled_savings(self):
        tiers = prices.tiers("s3_standard_tiers")
        alone = 2 * prices.tiered_cost(40000, tiers)
        together = prices.tiered_cost(80000, tiers)
        self.assertEqual(pooled_savings({"dev": 40000, "prod": 40000}, tiers), round(alone - together, 2))
        self.assertEqual(pooled_savings({"dev": 100, "prod": 200}, tiers), 0.0)


# ── Exercise 10 (predict): Allow or Deny? ────────────────────────────
"""
Read each scenario, decide, and write "Allow" or "Deny" in PREDICTIONS — BEFORE you run anything.
The test computes the truth with the course's reference evaluator. When you miss one, find which
rule from drills 03–04 you forgot.
"""
BUCKET = "arn:aws:s3:::shortly-assets"
SCENARIOS = {
    1: ("The app's policy allows s3:* on the bucket's objects; a second policy denies s3:DeleteObject. It deletes an object.",
        dict(request=Request(APP, "s3:DeleteObject", BUCKET + "/uploads/a.png"),
             identity=[allow("s3:*", BUCKET + "/*"), deny("s3:DeleteObject")])),
    2: ("The app's policy allows s3:GetObject. The root has FullAWSAccess, but the OU's only SCP allows ec2:*. It reads an object.",
        dict(request=Request(APP, "s3:GetObject", BUCKET + "/uploads/a.png"),
             identity=[allow("s3:GetObject")], scps=[[FULL_ACCESS], [allow("ec2:*")]])),
    3: ("The app has no identity policy at all. The bucket (same account) has a bucket policy allowing the shortly-app role to s3:GetObject. It reads an object.",
        dict(request=Request(APP, "s3:GetObject", BUCKET + "/uploads/a.png"), identity=[], resource_account=ACCOUNT,
             resource_policy={"Statement": [{"Effect": "Allow", "Principal": {"AWS": f"arn:aws:iam::{ACCOUNT}:role/shortly-app"},
                                             "Action": "s3:GetObject", "Resource": BUCKET + "/*"}]})),
    4: ("A role in the partner's account has an identity policy allowing s3:GetObject on your bucket. Your bucket has no bucket policy. It reads an object.",
        dict(request=Request(f"arn:aws:iam::{PARTNER}:role/reporting", "s3:GetObject", BUCKET + "/report.csv"),
             identity=[allow("s3:GetObject", BUCKET + "/*")], resource_account=ACCOUNT)),
    5: ("A developer role's policy allows ec2:* and s3:*. Its permissions boundary allows only s3:*. It launches an instance.",
        dict(request=Request(f"arn:aws:sts::{ACCOUNT}:assumed-role/dev/alice", "ec2:RunInstances", "*"),
             identity=[allow(["ec2:*", "s3:*"])], boundary=allow("s3:*"))),
    6: ("The app's policy allows dynamodb:GetItem on arn:aws:dynamodb:*:*:table/shortly-*. It reads an item from the table shortly-links.",
        dict(request=Request(APP, "dynamodb:GetItem", f"arn:aws:dynamodb:us-east-1:{ACCOUNT}:table/shortly-links"),
             identity=[allow("dynamodb:GetItem", "arn:aws:dynamodb:*:*:table/shortly-*")])),
}
PREDICTIONS = {n: None for n in SCENARIOS}   # YOUR ANSWERS: "Allow" or "Deny"


class Ex10(Drill):
    """Allow or Deny?"""
    tasks = ("1.1",)

    def test_predictions(self):
        for n, (story, kwargs) in SCENARIOS.items():
            with self.subTest(scenario=n):
                truth = "Allow" if ref.evaluate(**kwargs) == "Allow" else "Deny"
                self.assertIn(PREDICTIONS.get(n), ("Allow", "Deny"), f"scenario {n}: write 'Allow' or 'Deny'")
                self.assertEqual(PREDICTIONS[n], truth, f"scenario {n}: {story} — it is {truth}")


if __name__ == "__main__":
    run()

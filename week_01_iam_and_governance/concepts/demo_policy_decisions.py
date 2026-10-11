"""Demo — the reference evaluator deciding real-looking requests. Pure Python, no AWS.
Each line: the request, the policies in play, the decision and WHY."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.awslib.policy_eval import Request, evaluate  # noqa: E402
from _harness.awslib.safety import force_utf8  # noqa: E402

force_utf8()
A, B = "111122223333", "999988887777"
ANALYST = f"arn:aws:sts::{A}:assumed-role/analyst/bob"
FULL = {"Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]}
READ_LOGS = {"Statement": [{"Effect": "Allow", "Action": ["s3:GetObject", "s3:ListBucket"],
                            "Resource": ["arn:aws:s3:::acme-logs", "arn:aws:s3:::acme-logs/*"]}]}
ONLY_EU = {"Statement": [{"Effect": "Deny", "NotAction": ["iam:*", "sts:*"], "Resource": "*",
                          "Condition": {"StringNotEquals": {"aws:RequestedRegion": ["eu-west-1", "eu-central-1"]}}}]}
VPC_ONLY = {"Statement": [{"Effect": "Deny", "Principal": "*", "Action": "s3:*", "Resource": ["arn:aws:s3:::acme-logs/*"],
                           "Condition": {"StringNotEquals": {"aws:SourceVpce": "vpce-0abc"}}}]}

cases = [
    ("read a log object, identity policy only", Request(ANALYST, "s3:GetObject", "arn:aws:s3:::acme-logs/2026/10/08.gz"),
     dict(identity=[READ_LOGS]), "the identity policy allows it and nothing denies it"),
    ("delete a log object", Request(ANALYST, "s3:DeleteObject", "arn:aws:s3:::acme-logs/2026/10/08.gz"),
     dict(identity=[READ_LOGS]), "no statement allows DeleteObject → implicit deny"),
    ("read logs from us-east-1 under an EU-only SCP", Request(ANALYST, "s3:GetObject", "arn:aws:s3:::acme-logs/x", {"aws:RequestedRegion": "us-east-1"}),
     dict(identity=[READ_LOGS], scps=[[FULL, ONLY_EU]]), "the SCP's Deny matches (Region not in the list)"),
    ("read logs from outside the VPC endpoint", Request(ANALYST, "s3:GetObject", "arn:aws:s3:::acme-logs/x", {"aws:SourceVpce": "vpce-9zzz"}),
     dict(identity=[READ_LOGS], resource_policy=VPC_ONLY, resource_account=A), "the bucket policy denies requests not coming through vpce-0abc"),
    ("an analyst in another account, with only their own IAM policy", Request(f"arn:aws:iam::{B}:role/analyst", "s3:GetObject", "arn:aws:s3:::acme-logs/x"),
     dict(identity=[READ_LOGS], resource_account=A), "cross-account access needs the bucket policy to allow it too"),
]
for title, request, policies, why in cases:
    print(f"{evaluate(request, **policies):<13} {title}\n{'':14}because {why}")
print("\nNow do drills 03–04 and 10.")

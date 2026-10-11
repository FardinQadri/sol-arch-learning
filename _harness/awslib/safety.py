"""safety — keep every course check away from real AWS accounts.

use_fake_aws_env() replaces credential/profile variables with fake values and points boto3 at
config files that do not exist, so a learner's real ~/.aws profile can never be picked up.
The drill harness and the milestone conftest call it on import. The lab-cleanup library does
NOT — cleanup is meant for the learner's real account.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

FAKE_ENV = {
    "AWS_ACCESS_KEY_ID": "testing",
    "AWS_SECRET_ACCESS_KEY": "testing",
    "AWS_SESSION_TOKEN": "testing",
    "AWS_SECURITY_TOKEN": "testing",
    "AWS_DEFAULT_REGION": "us-east-1",
    "AWS_REGION": "us-east-1",
    "AWS_EC2_METADATA_DISABLED": "true",
}
_DROP = ("AWS_PROFILE", "AWS_DEFAULT_PROFILE", "AWS_ROLE_ARN", "AWS_ROLE_SESSION_NAME",
         "AWS_WEB_IDENTITY_TOKEN_FILE", "AWS_CONTAINER_CREDENTIALS_FULL_URI",
         "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI", "AWS_CONTAINER_AUTHORIZATION_TOKEN", "AWS_CA_BUNDLE")
NOWHERE = Path(tempfile.gettempdir()) / "saa-course-no-aws-config-here"


def use_fake_aws_env(environ=os.environ) -> None:
    for key in list(environ):
        if key in _DROP or key.startswith("AWS_ENDPOINT_URL"):
            del environ[key]
    environ.update(FAKE_ENV)
    environ["AWS_CONFIG_FILE"] = str(NOWHERE / "config")
    environ["AWS_SHARED_CREDENTIALS_FILE"] = str(NOWHERE / "credentials")


def force_utf8() -> None:
    """Let ✔/✘/★ print on Windows consoles and through pipes (their default encoding is cp1252)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

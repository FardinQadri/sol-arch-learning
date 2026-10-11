"""Make the course root importable and force fake AWS credentials for every maintainer test."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from _harness.awslib.safety import use_fake_aws_env  # noqa: E402

use_fake_aws_env()

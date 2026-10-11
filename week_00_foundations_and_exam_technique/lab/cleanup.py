"""Week 00 lab cleanup — deletes only S3 buckets tagged saa-course=lab. Dry run unless you add --yes.

    python lab/cleanup.py --profile saa-lab                 list what would go
    python lab/cleanup.py --profile saa-lab --yes           delete it (repeat with --region eu-west-1)
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.labclean import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(kinds=["s3_buckets"]))

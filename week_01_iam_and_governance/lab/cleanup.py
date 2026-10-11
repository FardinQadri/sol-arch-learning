"""Week 01 lab cleanup — deletes only IAM roles, policies and users tagged saa-course=lab. Dry run unless --yes.

    python lab/cleanup.py --profile saa-lab          list what would go
    python lab/cleanup.py --profile saa-lab --yes    delete it
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.labclean import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(kinds=["iam_roles", "iam_users", "iam_policies"]))

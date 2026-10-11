"""Week 04 lab cleanup — deletes only S3 buckets, EBS snapshots and EBS volumes tagged saa-course=lab.
Buckets are emptied first: unfinished multipart uploads aborted, every object version and delete marker removed.
Snapshots go before the volumes. Dry run unless --yes.

    python lab/cleanup.py --profile saa-lab          list what would go
    python lab/cleanup.py --profile saa-lab --yes    delete it
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.labclean import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(kinds=["s3_buckets", "ebs_snapshots", "ebs_volumes"]))

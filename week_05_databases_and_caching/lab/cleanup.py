"""Week 05 lab cleanup — deletes only DynamoDB tables, DynamoDB on-demand backups, RDS instances, RDS manual
snapshots and DB subnet groups tagged saa-course=lab. Backups go first (found through their tagged table), then tables, then RDS instances (read replicas before their
source; deletion protection is turned off only on tagged instances), then manual snapshots, then the subnet groups. Dry run unless --yes.

    python lab/cleanup.py --profile saa-lab          list what would go
    python lab/cleanup.py --profile saa-lab --yes    delete it
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.labclean import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(kinds=["dynamodb_tables", "dynamodb_backups", "rds_instances", "rds_snapshots", "db_subnet_groups"]))

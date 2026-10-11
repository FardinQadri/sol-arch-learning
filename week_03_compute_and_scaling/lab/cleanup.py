"""Week 03 lab cleanup — deletes only Auto Scaling groups, load balancers, target groups, launch templates,
EC2 instances and security groups tagged saa-course=lab. Deleting an Auto Scaling group also terminates its
instances; tagged instances left over are terminated next, then the two security groups. Dry run unless --yes.

    python lab/cleanup.py --profile saa-lab          list what would go
    python lab/cleanup.py --profile saa-lab --yes    delete it
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.labclean import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(kinds=["autoscaling_groups", "load_balancers", "target_groups", "launch_templates",
                         "ec2_instances", "security_groups"]))

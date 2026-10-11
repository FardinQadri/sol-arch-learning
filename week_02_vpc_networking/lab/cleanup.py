"""Week 02 lab cleanup — deletes only EC2 instances, NAT gateways, Elastic IPs and VPCs tagged saa-course=lab.
A tagged VPC is deleted with everything inside it. Dry run unless --yes.

    python lab/cleanup.py --profile saa-lab          list what would go
    python lab/cleanup.py --profile saa-lab --yes    delete it
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.labclean import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(kinds=["ec2_instances", "nat_gateways", "elastic_ips", "vpcs"]))

"""labclean — remove what a lab created in YOUR AWS account, and nothing else.

Every lab tags what it creates with  saa-course = lab . A week's lab/cleanup.py calls main() with
the kinds of resources that lab creates. Without --yes it only lists (dry run).

    python lab/cleanup.py                    list what would be deleted (us-east-1 or $AWS_DEFAULT_REGION)
    python lab/cleanup.py --region eu-west-1 --profile saa-lab
    python lab/cleanup.py --yes              actually delete

IAM is global: IAM kinds are listed whatever --region you give.
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Callable

TAG_KEY, TAG_VALUE = "saa-course", "lab"


@dataclass
class Found:
    kind: str
    name: str
    region: str
    delete: Callable[[], None]


def _error_code(exc) -> str:
    response = getattr(exc, "response", None) or {}
    return response.get("Error", {}).get("Code", type(exc).__name__)


class Blocked(Exception):
    """A tagged resource that must be left in place on purpose (it is held by something we must not touch,
    or by something this script cannot remove). main() prints the message and counts it as a problem."""


def _tagged(tags) -> bool:
    return any(t.get("Key") == TAG_KEY and t.get("Value") == TAG_VALUE for t in tags or [])


# ── S3 ──────────────────────────────────────────────────────────────


def find_s3_buckets(session, region: str) -> list[Found]:
    from botocore.exceptions import ClientError

    s3 = session.client("s3", region_name=region)
    found = []
    for bucket in s3.list_buckets().get("Buckets", []):
        name = bucket["Name"]
        try:
            location = s3.get_bucket_location(Bucket=name).get("LocationConstraint") or "us-east-1"
            if location != region:
                continue
            tags = s3.get_bucket_tagging(Bucket=name).get("TagSet", [])
        except ClientError:
            continue  # untagged (NoSuchTagSet) or not ours to read
        if _tagged(tags):
            found.append(Found("s3_buckets", name, region, lambda name=name: _delete_bucket(s3, name)))
    return found


def _delete_bucket(s3, name: str) -> None:
    from botocore.exceptions import ClientError

    # An unfinished multipart upload keeps its parts (and its bill) and does not show up as an object.
    for page in s3.get_paginator("list_multipart_uploads").paginate(Bucket=name):
        for upload in page.get("Uploads", []):
            s3.abort_multipart_upload(Bucket=name, Key=upload["Key"], UploadId=upload["UploadId"])
    errors = []
    for page in s3.get_paginator("list_object_versions").paginate(Bucket=name):
        doomed = [{"Key": v["Key"], "VersionId": v["VersionId"]} for v in page.get("Versions", []) + page.get("DeleteMarkers", [])]
        for start in range(0, len(doomed), 1000):
            result = s3.delete_objects(Bucket=name, Delete={"Objects": doomed[start:start + 1000], "Quiet": True})
            errors += result.get("Errors", [])
    if errors:
        try:
            locked = s3.get_object_lock_configuration(Bucket=name)["ObjectLockConfiguration"].get("ObjectLockEnabled") == "Enabled"
        except ClientError:
            locked = False
        first = f"{errors[0].get('Code')}: {errors[0].get('Message')}"
        if locked:
            raise Blocked(f"bucket {name} has Object Lock and {len(errors)} object version(s) are under retention or legal hold, "
                          "which this script cannot (and must not) override. Wait for the retention to expire or remove the "
                          "hold in the console, then run the cleanup again.")
        raise Blocked(f"{len(errors)} object version(s) in bucket {name} could not be deleted ({first})")
    s3.delete_bucket(Bucket=name)


# ── IAM (global) ────────────────────────────────────────────────────


def find_iam_roles(session, region: str) -> list[Found]:
    iam = session.client("iam")
    found = []
    for page in iam.get_paginator("list_roles").paginate():
        for role in page["Roles"]:
            name = role["RoleName"]
            if _tagged(iam.list_role_tags(RoleName=name).get("Tags")):
                found.append(Found("iam_roles", name, "global", lambda name=name: _delete_role(iam, name)))
    return found


def _delete_role(iam, name: str) -> None:
    for profile in iam.list_instance_profiles_for_role(RoleName=name)["InstanceProfiles"]:
        iam.remove_role_from_instance_profile(InstanceProfileName=profile["InstanceProfileName"], RoleName=name)
        if profile["InstanceProfileName"] == name:
            iam.delete_instance_profile(InstanceProfileName=name)
    for policy in iam.list_role_policies(RoleName=name)["PolicyNames"]:
        iam.delete_role_policy(RoleName=name, PolicyName=policy)
    for policy in iam.list_attached_role_policies(RoleName=name)["AttachedPolicies"]:
        iam.detach_role_policy(RoleName=name, PolicyArn=policy["PolicyArn"])
    iam.delete_role(RoleName=name)


def find_iam_policies(session, region: str) -> list[Found]:
    iam = session.client("iam")
    found = []
    for page in iam.get_paginator("list_policies").paginate(Scope="Local"):
        for policy in page["Policies"]:
            arn = policy["Arn"]
            if _tagged(iam.list_policy_tags(PolicyArn=arn).get("Tags")):
                found.append(Found("iam_policies", policy["PolicyName"], "global", lambda arn=arn: _delete_policy(iam, arn)))
    return found


def _delete_policy(iam, arn: str) -> None:
    entities = iam.list_entities_for_policy(PolicyArn=arn)
    for role in entities.get("PolicyRoles", []):
        iam.detach_role_policy(RoleName=role["RoleName"], PolicyArn=arn)
    for user in entities.get("PolicyUsers", []):
        iam.detach_user_policy(UserName=user["UserName"], PolicyArn=arn)
    for group in entities.get("PolicyGroups", []):
        iam.detach_group_policy(GroupName=group["GroupName"], PolicyArn=arn)
    for version in iam.list_policy_versions(PolicyArn=arn)["Versions"]:
        if not version["IsDefaultVersion"]:
            iam.delete_policy_version(PolicyArn=arn, VersionId=version["VersionId"])
    iam.delete_policy(PolicyArn=arn)


def find_iam_users(session, region: str) -> list[Found]:
    iam = session.client("iam")
    found = []
    for page in iam.get_paginator("list_users").paginate():
        for user in page["Users"]:
            name = user["UserName"]
            if _tagged(iam.list_user_tags(UserName=name).get("Tags")):
                found.append(Found("iam_users", name, "global", lambda name=name: _delete_user(iam, name)))
    return found


def _delete_user(iam, name: str) -> None:
    from botocore.exceptions import ClientError

    for key in iam.list_access_keys(UserName=name)["AccessKeyMetadata"]:
        iam.delete_access_key(UserName=name, AccessKeyId=key["AccessKeyId"])
    try:
        iam.delete_login_profile(UserName=name)
    except ClientError as exc:
        if _error_code(exc) != "NoSuchEntity":
            raise
    for policy in iam.list_user_policies(UserName=name)["PolicyNames"]:
        iam.delete_user_policy(UserName=name, PolicyName=policy)
    for policy in iam.list_attached_user_policies(UserName=name)["AttachedPolicies"]:
        iam.detach_user_policy(UserName=name, PolicyArn=policy["PolicyArn"])
    for group in iam.list_groups_for_user(UserName=name)["Groups"]:
        iam.remove_user_from_group(UserName=name, GroupName=group["GroupName"])
    for device in iam.list_mfa_devices(UserName=name)["MFADevices"]:
        iam.deactivate_mfa_device(UserName=name, SerialNumber=device["SerialNumber"])
    iam.delete_user(UserName=name)


# ── EC2 and VPC (Regional) ──────────────────────────────────────────

WAIT_SECONDS = 5          # pause between state checks while AWS deletes something (tests set 0)
WAIT_ATTEMPTS = 120       # give up after WAIT_SECONDS × WAIT_ATTEMPTS
TAG_FILTER = [{"Name": f"tag:{TAG_KEY}", "Values": [TAG_VALUE]}]


def _wait_until(check, what: str) -> None:
    import time

    for _ in range(WAIT_ATTEMPTS):
        if check():
            return
        time.sleep(WAIT_SECONDS)
    raise TimeoutError(f"gave up waiting for {what}")


def _name(tags, fallback: str) -> str:
    names = [t["Value"] for t in tags or [] if t.get("Key") == "Name"]
    return f"{fallback} ({names[0]})" if names else fallback


def find_ec2_instances(session, region: str) -> list[Found]:
    ec2 = session.client("ec2", region_name=region)
    found = []
    filters = TAG_FILTER + [{"Name": "instance-state-name", "Values": ["pending", "running", "stopping", "stopped"]}]
    for page in ec2.get_paginator("describe_instances").paginate(Filters=filters):
        for reservation in page["Reservations"]:
            for instance in reservation["Instances"]:
                if not _tagged(instance.get("Tags")):  # never trust the server-side filter alone
                    continue
                iid = instance["InstanceId"]
                found.append(Found("ec2_instances", _name(instance.get("Tags"), iid), region,
                                   lambda iid=iid: _terminate(ec2, iid)))
    return found


def _terminate(ec2, instance_id: str) -> None:
    ec2.terminate_instances(InstanceIds=[instance_id])

    def gone():
        state = ec2.describe_instances(InstanceIds=[instance_id])["Reservations"][0]["Instances"][0]["State"]["Name"]
        return state == "terminated"
    _wait_until(gone, f"instance {instance_id} to terminate")


def _delete_nat(ec2, nat_id: str) -> None:
    ec2.delete_nat_gateway(NatGatewayId=nat_id)

    def gone():
        gateways = ec2.describe_nat_gateways(NatGatewayIds=[nat_id])["NatGateways"]
        return not gateways or gateways[0]["State"] in ("deleted", "failed")
    _wait_until(gone, f"NAT gateway {nat_id} to be deleted")


def find_nat_gateways(session, region: str) -> list[Found]:
    ec2 = session.client("ec2", region_name=region)
    found = []
    for nat in ec2.describe_nat_gateways(Filters=TAG_FILTER)["NatGateways"]:
        if nat["State"] in ("pending", "available") and _tagged(nat.get("Tags")):
            nat_id = nat["NatGatewayId"]
            found.append(Found("nat_gateways", _name(nat.get("Tags"), nat_id), region,
                               lambda nat_id=nat_id: _delete_nat(ec2, nat_id)))
    return found


def find_elastic_ips(session, region: str) -> list[Found]:
    ec2 = session.client("ec2", region_name=region)
    found = []
    for address in ec2.describe_addresses(Filters=TAG_FILTER)["Addresses"]:
        if not _tagged(address.get("Tags")):
            continue
        allocation = address["AllocationId"]
        found.append(Found("elastic_ips", f"{address.get('PublicIp', allocation)} ({allocation})", region,
                           lambda address=address: _release(ec2, address)))
    return found


def _release(ec2, address: dict) -> None:
    if address.get("AssociationId"):
        ec2.disassociate_address(AssociationId=address["AssociationId"])
    ec2.release_address(AllocationId=address["AllocationId"])


def find_vpcs(session, region: str) -> list[Found]:
    ec2 = session.client("ec2", region_name=region)
    return [Found("vpcs", _name(vpc.get("Tags"), vpc["VpcId"]), region, lambda vpc_id=vpc["VpcId"]: _delete_vpc(ec2, vpc_id))
            for vpc in ec2.describe_vpcs(Filters=TAG_FILTER)["Vpcs"] if _tagged(vpc.get("Tags"))]


def _delete_vpc(ec2, vpc_id: str) -> None:
    """Delete a VPC and everything inside it, in the order AWS accepts. Instances still running
    inside it are NOT terminated (unless tagged and listed earlier), so AWS refuses the VPC and the
    error is reported — nothing untagged is ever destroyed."""
    in_vpc = [{"Name": "vpc-id", "Values": [vpc_id]}]
    for nat in ec2.describe_nat_gateways(Filters=in_vpc)["NatGateways"]:
        if nat["State"] in ("pending", "available"):
            _delete_nat(ec2, nat["NatGatewayId"])
    endpoints = [e["VpcEndpointId"] for e in ec2.describe_vpc_endpoints(Filters=in_vpc)["VpcEndpoints"]
                 if e["State"].lower() not in ("deleted", "deleting")]
    if endpoints:
        ec2.delete_vpc_endpoints(VpcEndpointIds=endpoints)
    for igw in ec2.describe_internet_gateways(Filters=[{"Name": "attachment.vpc-id", "Values": [vpc_id]}])["InternetGateways"]:
        ec2.detach_internet_gateway(InternetGatewayId=igw["InternetGatewayId"], VpcId=vpc_id)
        ec2.delete_internet_gateway(InternetGatewayId=igw["InternetGatewayId"])
    for subnet in ec2.describe_subnets(Filters=in_vpc)["Subnets"]:
        ec2.delete_subnet(SubnetId=subnet["SubnetId"])
    for table in ec2.describe_route_tables(Filters=in_vpc)["RouteTables"]:
        if any(a.get("Main") for a in table.get("Associations", [])):
            continue
        for association in table.get("Associations", []):
            ec2.disassociate_route_table(AssociationId=association["RouteTableAssociationId"])
        ec2.delete_route_table(RouteTableId=table["RouteTableId"])
    groups = [g for g in ec2.describe_security_groups(Filters=in_vpc)["SecurityGroups"] if g["GroupName"] != "default"]
    for group in groups:  # rules that reference other groups block deletion, so remove rules first
        if group.get("IpPermissions"):
            ec2.revoke_security_group_ingress(GroupId=group["GroupId"], IpPermissions=group["IpPermissions"])
        if group.get("IpPermissionsEgress"):
            ec2.revoke_security_group_egress(GroupId=group["GroupId"], IpPermissions=group["IpPermissionsEgress"])
    for group in groups:
        ec2.delete_security_group(GroupId=group["GroupId"])
    for acl in ec2.describe_network_acls(Filters=in_vpc)["NetworkAcls"]:
        if not acl.get("IsDefault"):
            ec2.delete_network_acl(NetworkAclId=acl["NetworkAclId"])
    ec2.delete_vpc(VpcId=vpc_id)


# ── Compute and scaling (Regional): Auto Scaling, load balancers, launch templates, security groups ──


def find_autoscaling_groups(session, region: str) -> list[Found]:
    asg = session.client("autoscaling", region_name=region)
    found = []
    for page in asg.get_paginator("describe_auto_scaling_groups").paginate():
        for group in page["AutoScalingGroups"]:
            if _tagged(group.get("Tags")):  # ASG tags carry Key/Value like everything else
                name = group["AutoScalingGroupName"]
                found.append(Found("autoscaling_groups", name, region, lambda name=name: _delete_asg(asg, name)))
    return found


def _delete_asg(asg, name: str) -> None:
    from botocore.exceptions import ClientError

    def gone():  # a scaling activity in progress blocks the delete for a while: try again until it is gone
        if not asg.describe_auto_scaling_groups(AutoScalingGroupNames=[name])["AutoScalingGroups"]:
            return True
        try:
            asg.delete_auto_scaling_group(AutoScalingGroupName=name, ForceDelete=True)
        except ClientError as exc:
            if _error_code(exc) not in ("ScalingActivityInProgress", "ResourceInUse"):
                raise
        return False
    _wait_until(gone, f"Auto Scaling group {name} to be deleted")


def _tagged_arns(elb, arns: list[str]) -> set[str]:
    """ARNs (from any list) whose tags include the lab tag; describe_tags takes at most 20 ARNs."""
    tagged = set()
    for start in range(0, len(arns), 20):
        for description in elb.describe_tags(ResourceArns=arns[start:start + 20])["TagDescriptions"]:
            if _tagged(description.get("Tags")):
                tagged.add(description["ResourceArn"])
    return tagged


def find_load_balancers(session, region: str) -> list[Found]:
    elb = session.client("elbv2", region_name=region)
    balancers = [lb for page in elb.get_paginator("describe_load_balancers").paginate() for lb in page["LoadBalancers"]]
    tagged = _tagged_arns(elb, [lb["LoadBalancerArn"] for lb in balancers])
    return [Found("load_balancers", lb["LoadBalancerName"], region, lambda arn=lb["LoadBalancerArn"]: _delete_load_balancer(elb, arn))
            for lb in balancers if lb["LoadBalancerArn"] in tagged]


def _delete_load_balancer(elb, arn: str) -> None:
    from botocore.exceptions import ClientError

    elb.delete_load_balancer(LoadBalancerArn=arn)

    def gone():
        try:
            return not elb.describe_load_balancers(LoadBalancerArns=[arn])["LoadBalancers"]
        except ClientError as exc:
            if _error_code(exc) == "LoadBalancerNotFound":
                return True
            raise
    _wait_until(gone, f"load balancer {arn} to be deleted")


def find_target_groups(session, region: str) -> list[Found]:
    elb = session.client("elbv2", region_name=region)
    groups = [tg for page in elb.get_paginator("describe_target_groups").paginate() for tg in page["TargetGroups"]]
    tagged = _tagged_arns(elb, [tg["TargetGroupArn"] for tg in groups])
    return [Found("target_groups", tg["TargetGroupName"], region,
                  lambda arn=tg["TargetGroupArn"]: _delete_target_group(elb, arn))
            for tg in groups if tg["TargetGroupArn"] in tagged]


def _delete_target_group(elb, arn: str) -> None:
    from botocore.exceptions import ClientError

    def deleted():  # right after its load balancer goes, AWS may still report the group in use
        try:
            elb.delete_target_group(TargetGroupArn=arn)
            return True
        except ClientError as exc:
            if _error_code(exc) == "ResourceInUse":
                return False
            if _error_code(exc) == "TargetGroupNotFound":
                return True
            raise
    _wait_until(deleted, f"target group {arn} to be released")


def find_launch_templates(session, region: str) -> list[Found]:
    ec2 = session.client("ec2", region_name=region)
    found = []
    for page in ec2.get_paginator("describe_launch_templates").paginate():
        for template in page["LaunchTemplates"]:
            if _tagged(template.get("Tags")):
                tid = template["LaunchTemplateId"]
                found.append(Found("launch_templates", f"{template['LaunchTemplateName']} ({tid})", region,
                                   lambda tid=tid: ec2.delete_launch_template(LaunchTemplateId=tid)))
    return found


def find_security_groups(session, region: str) -> list[Found]:
    """ONE item for all tagged groups: they may reference each other, so rules go first, then groups."""
    ec2 = session.client("ec2", region_name=region)
    ids = []
    for page in ec2.get_paginator("describe_security_groups").paginate(Filters=TAG_FILTER):
        for group in page["SecurityGroups"]:
            if group["GroupName"] != "default" and _tagged(group.get("Tags")):  # never trust the filter alone
                ids.append(group["GroupId"])
    if not ids:
        return []
    return [Found("security_groups", ", ".join(ids), region, lambda ids=ids: _delete_security_groups(ec2, ids))]


def _delete_security_groups(ec2, ids: list[str]) -> None:
    from botocore.exceptions import ClientError

    for group in ec2.describe_security_groups(GroupIds=ids)["SecurityGroups"]:
        # only the rules of OUR groups are revoked; other groups are never modified
        if group.get("IpPermissions"):
            ec2.revoke_security_group_ingress(GroupId=group["GroupId"], IpPermissions=group["IpPermissions"])
        if group.get("IpPermissionsEgress"):
            ec2.revoke_security_group_egress(GroupId=group["GroupId"], IpPermissions=group["IpPermissionsEgress"])
    for group_id in ids:
        def deleted(group_id=group_id):  # a load balancer's network interfaces can linger for minutes
            try:
                ec2.delete_security_group(GroupId=group_id)
                return True
            except ClientError as exc:
                if _error_code(exc) == "DependencyViolation":
                    return False
                if _error_code(exc) == "InvalidGroup.NotFound":
                    return True
                raise
        _wait_until(deleted, f"security group {group_id} to have no dependants")


# ── Storage (Regional): EBS volumes and snapshots ───────────────────


def _is_missing(exc, *codes) -> bool:
    return _error_code(exc) in codes


def find_ebs_volumes(session, region: str) -> list[Found]:
    ec2 = session.client("ec2", region_name=region)
    found = []
    for page in ec2.get_paginator("describe_volumes").paginate(Filters=TAG_FILTER):
        for volume in page["Volumes"]:
            if not _tagged(volume.get("Tags")) or volume["State"] not in ("available", "in-use"):
                continue
            vid = volume["VolumeId"]
            label = _name(volume.get("Tags"), vid)
            reason = _volume_blocker(ec2, volume)
            if reason:  # shown in the dry run so nobody expects it to go
                label += f"  [WILL BE LEFT IN PLACE: {reason}]"
            found.append(Found("ebs_volumes", label, region, lambda vid=vid: _delete_volume(ec2, vid)))
    return found


def _volume_blocker(ec2, volume: dict) -> str | None:
    """Why this in-use volume must not be detached: every instance it is attached to must itself be tagged
    (we never touch an untagged instance's disk), and it must not be that instance's root disk."""
    for attachment in volume.get("Attachments", []):
        iid = attachment["InstanceId"]
        try:
            reservations = ec2.describe_instances(InstanceIds=[iid])["Reservations"]
        except Exception as exc:
            if _error_code(exc) == "InvalidInstanceID.NotFound":
                continue  # the instance is gone; the volume is about to be free
            raise
        for reservation in reservations:
            for instance in reservation["Instances"]:
                if not _tagged(instance.get("Tags")):
                    return f"attached to {iid}, which is not tagged {TAG_KEY}={TAG_VALUE}"
                if attachment.get("Device") == instance.get("RootDeviceName"):
                    return f"it is the root disk of {iid}; terminate the instance instead"
    return None


def _delete_volume(ec2, volume_id: str) -> None:
    from botocore.exceptions import ClientError

    def current():
        try:
            volumes = ec2.describe_volumes(VolumeIds=[volume_id])["Volumes"]
        except ClientError as exc:
            if _is_missing(exc, "InvalidVolume.NotFound"):
                return None
            raise
        return volumes[0] if volumes and volumes[0]["State"] != "deleted" else None

    volume = current()
    if volume is None:
        return
    if not _tagged(volume.get("Tags")):  # re-check right before touching it
        raise Blocked(f"volume {volume_id} is no longer tagged {TAG_KEY}={TAG_VALUE}")
    if volume["State"] == "in-use":
        reason = _volume_blocker(ec2, volume)
        if reason:
            raise Blocked(f"volume {volume_id} left in place: {reason}")
        for attachment in volume.get("Attachments", []):
            ec2.detach_volume(VolumeId=volume_id, InstanceId=attachment["InstanceId"])
        _wait_until(lambda: (current() or {"State": "available"})["State"] == "available", f"volume {volume_id} to detach")

    def deleted():
        try:
            ec2.delete_volume(VolumeId=volume_id)
        except ClientError as exc:
            if _is_missing(exc, "InvalidVolume.NotFound"):
                return True
            if _is_missing(exc, "VolumeInUse"):
                return False
            raise
        return True
    _wait_until(deleted, f"volume {volume_id} to be deleted")
    _wait_until(lambda: current() is None, f"volume {volume_id} to disappear")


def find_ebs_snapshots(session, region: str) -> list[Found]:
    ec2 = session.client("ec2", region_name=region)
    found = []
    # OwnerIds=["self"] keeps AWS's and other accounts' public snapshots out; the tag filter + client-side check
    # do the real work (moto ignores "self", and we never trust a server-side filter alone).
    for page in ec2.get_paginator("describe_snapshots").paginate(OwnerIds=["self"], Filters=TAG_FILTER):
        for snapshot in page["Snapshots"]:
            if _tagged(snapshot.get("Tags")):
                sid = snapshot["SnapshotId"]
                found.append(Found("ebs_snapshots", _name(snapshot.get("Tags"), sid), region,
                                   lambda sid=sid: _delete_snapshot(ec2, sid)))
    return found


def _delete_snapshot(ec2, snapshot_id: str) -> None:
    from botocore.exceptions import ClientError

    for image in ec2.describe_images(Owners=["self"])["Images"]:
        for mapping in image.get("BlockDeviceMappings", []):
            if mapping.get("Ebs", {}).get("SnapshotId") == snapshot_id:
                raise Blocked(f"snapshot {snapshot_id} is used by image {image['ImageId']}; deregister the image first")
    try:
        ec2.delete_snapshot(SnapshotId=snapshot_id)
    except ClientError as exc:
        if _is_missing(exc, "InvalidSnapshot.InUse"):
            raise Blocked(f"snapshot {snapshot_id} is in use by an image; deregister the image first") from exc
        if not _is_missing(exc, "InvalidSnapshot.NotFound"):
            raise


# ── Databases (Regional): DynamoDB, RDS ─────────────────────────────


def _tagged_tables(ddb) -> list[dict]:
    """Tagged DynamoDB tables as {name, arn}; tags live on the ARN, so every table costs a describe + a tag read."""
    tables = []
    for page in ddb.get_paginator("list_tables").paginate():
        for name in page["TableNames"]:
            arn = ddb.describe_table(TableName=name)["Table"]["TableArn"]
            tags, token = [], None
            while True:
                result = ddb.list_tags_of_resource(ResourceArn=arn, **({"NextToken": token} if token else {}))
                tags += result.get("Tags", [])
                token = result.get("NextToken")
                if not token:
                    break
            if _tagged(tags):
                tables.append({"name": name, "arn": arn})
    return tables


def find_dynamodb_backups(session, region: str) -> list[Found]:
    """On-demand backups have no tags of their own, so they are found through their (tagged) table. Listing
    happens before anything is deleted, so even a 'tables first' order would find them; a separate finder that
    sits BEFORE dynamodb_tables is clearer for the learner (backups appear as their own lines) and means a
    backup is never orphaned by a half-finished run: once the table is gone nothing could find it again."""
    ddb = session.client("dynamodb", region_name=region)
    found = []
    for table in _tagged_tables(ddb):
        token = None
        while True:
            result = ddb.list_backups(TableName=table["name"], BackupType="USER", **({"ExclusiveStartBackupArn": token} if token else {}))
            for backup in result.get("BackupSummaries", []):
                arn = backup["BackupArn"]
                found.append(Found("dynamodb_backups", f"{table['name']} / {backup['BackupName']}", region,
                                   lambda arn=arn: ddb.delete_backup(BackupArn=arn)))
            token = result.get("LastEvaluatedBackupArn")
            if not token:
                break
    return found


def find_dynamodb_tables(session, region: str) -> list[Found]:
    ddb = session.client("dynamodb", region_name=region)
    return [Found("dynamodb_tables", t["name"], region, lambda name=t["name"]: _delete_table(ddb, name))
            for t in _tagged_tables(ddb)]


def _delete_table(ddb, name: str) -> None:
    from botocore.exceptions import ClientError

    def gone():
        try:
            table = ddb.describe_table(TableName=name)["Table"]
        except ClientError as exc:
            if _is_missing(exc, "ResourceNotFoundException"):
                return True
            raise
        if table.get("TableStatus") == "DELETING":
            return False
        try:
            if table.get("DeletionProtectionEnabled"):  # only ever reached for a table found tagged
                ddb.update_table(TableName=name, DeletionProtectionEnabled=False)
            ddb.delete_table(TableName=name)
        except ClientError as exc:
            if not _is_missing(exc, "ResourceInUseException", "LimitExceededException"):  # still creating/updating
                raise
        return False
    _wait_until(gone, f"table {name} to be deleted")


def _rds_tags(rds, item: dict, arn_key: str) -> list:
    if "TagList" in item:
        return item["TagList"]
    return rds.list_tags_for_resource(ResourceName=item[arn_key]).get("TagList", [])


def _db_id(identifier: str) -> str:
    return identifier.rsplit(":", 1)[-1]  # a cross-Region replica names its source by ARN


def find_rds_instances(session, region: str) -> list[Found]:
    """Tagged standalone instances and read replicas. Aurora cluster members are not covered (clusters are not a
    lab kind). Replicas come first so a source is never deleted while its replicas still exist (AWS would
    otherwise promote them); a tagged source with an UNTAGGED replica is left alone, never promoting it."""
    rds = session.client("rds", region_name=region)
    instances = [i for page in rds.get_paginator("describe_db_instances").paginate() for i in page["DBInstances"]]
    source_of = {i["DBInstanceIdentifier"]: _db_id(i["ReadReplicaSourceDBInstanceIdentifier"])
                 for i in instances if i.get("ReadReplicaSourceDBInstanceIdentifier")}
    mine = [i for i in instances if not i.get("DBClusterIdentifier") and _tagged(_rds_tags(rds, i, "DBInstanceArn"))]
    mine_ids = {i["DBInstanceIdentifier"] for i in mine}

    def depth(identifier):  # replica of a replica is deeper
        count = 0
        while identifier in source_of and count < 20:
            identifier, count = source_of[identifier], count + 1
        return count
    mine.sort(key=lambda i: -depth(i["DBInstanceIdentifier"]))  # stable sort keeps the listing order otherwise
    found = []
    for instance in mine:
        iid = instance["DBInstanceIdentifier"]
        strangers = [r for r in instance.get("ReadReplicaDBInstanceIdentifiers", []) if r not in mine_ids]
        label = iid
        if strangers:
            label += f"  [WILL BE LEFT IN PLACE: it has read replica(s) not tagged {TAG_KEY}={TAG_VALUE}: {', '.join(strangers)}]"
        found.append(Found("rds_instances", label, region, lambda iid=iid, mine_ids=mine_ids: _delete_db_instance(rds, iid, mine_ids)))
    return found


def _delete_db_instance(rds, identifier: str, mine_ids: set) -> None:
    from botocore.exceptions import ClientError

    def gone():
        try:
            db = rds.describe_db_instances(DBInstanceIdentifier=identifier)["DBInstances"][0]
        except ClientError as exc:
            if _is_missing(exc, "DBInstanceNotFound", "DBInstanceNotFoundFault"):
                return True
            raise
        if db["DBInstanceStatus"] == "deleting":
            return False
        strangers = [r for r in db.get("ReadReplicaDBInstanceIdentifiers", []) if r not in mine_ids]
        if strangers:
            raise Blocked(f"{identifier} has read replica(s) not tagged {TAG_KEY}={TAG_VALUE} ({', '.join(strangers)}); "
                          "deleting it would promote them, so it is left in place")
        try:
            if db.get("DeletionProtection"):
                rds.modify_db_instance(DBInstanceIdentifier=identifier, DeletionProtection=False, ApplyImmediately=True)
            else:
                rds.delete_db_instance(DBInstanceIdentifier=identifier, SkipFinalSnapshot=True, DeleteAutomatedBackups=True)
        except ClientError as exc:
            if not _is_missing(exc, "InvalidDBInstanceState", "InvalidDBInstanceStateFault"):  # still creating/modifying
                raise
        return False
    _wait_until(gone, f"DB instance {identifier} to be deleted")


def find_rds_snapshots(session, region: str) -> list[Found]:
    rds = session.client("rds", region_name=region)
    found = []
    for page in rds.get_paginator("describe_db_snapshots").paginate(SnapshotType="manual"):
        for snapshot in page["DBSnapshots"]:
            if snapshot.get("SnapshotType", "manual") == "manual" and _tagged(_rds_tags(rds, snapshot, "DBSnapshotArn")):
                sid = snapshot["DBSnapshotIdentifier"]
                found.append(Found("rds_snapshots", sid, region, lambda sid=sid: _delete_db_snapshot(rds, sid)))
    return found


def _delete_db_snapshot(rds, identifier: str) -> None:
    from botocore.exceptions import ClientError

    def deleted():
        try:
            rds.delete_db_snapshot(DBSnapshotIdentifier=identifier)
            return True
        except ClientError as exc:
            if _is_missing(exc, "DBSnapshotNotFound", "DBSnapshotNotFoundFault"):
                return True
            if _is_missing(exc, "InvalidDBSnapshotState", "InvalidDBSnapshotStateFault"):  # still being created
                return False
            raise
    _wait_until(deleted, f"DB snapshot {identifier} to be deleted")


def find_db_subnet_groups(session, region: str) -> list[Found]:
    rds = session.client("rds", region_name=region)
    found = []
    for page in rds.get_paginator("describe_db_subnet_groups").paginate():
        for group in page["DBSubnetGroups"]:
            name = group["DBSubnetGroupName"]
            if name == "default":  # the account's built-in group can never be deleted
                continue
            if _tagged(rds.list_tags_for_resource(ResourceName=group["DBSubnetGroupArn"]).get("TagList")):
                found.append(Found("db_subnet_groups", name, region, lambda name=name: _delete_db_subnet_group(rds, name)))
    return found


def _delete_db_subnet_group(rds, name: str) -> None:
    from botocore.exceptions import ClientError

    def deleted():  # the instance that used it may still be shutting down
        try:
            rds.delete_db_subnet_group(DBSubnetGroupName=name)
            return True
        except ClientError as exc:
            if _is_missing(exc, "DBSubnetGroupNotFoundFault", "DBSubnetGroupNotFound"):
                return True
            if _is_missing(exc, "InvalidDBSubnetGroupStateFault", "InvalidDBSubnetGroupState"):
                return False
            raise
    _wait_until(deleted, f"DB subnet group {name} to be released")


# Order matters: scaling and load balancing before the EC2 things they use; EC2 before VPCs;
# databases before the VPC and security groups they sit in; IAM roles and users before customer-managed policies.
FINDERS = {
    "s3_buckets": find_s3_buckets,
    "autoscaling_groups": find_autoscaling_groups,  # first: stops it launching replacements while we delete instances
    "load_balancers": find_load_balancers,          # before target groups (a listener holds them) and security groups (its network interfaces use them)
    "target_groups": find_target_groups,            # after the load balancers that forward to them
    "ec2_instances": find_ec2_instances,            # instances before their VPC, and before the volumes/snapshots they hold
    "launch_templates": find_launch_templates,      # after the ASG that uses it (and the instances)
    "dynamodb_backups": find_dynamodb_backups,      # before the tables: backups are found through their table, so they go while it still exists
    "dynamodb_tables": find_dynamodb_tables,        # after their backups
    "rds_instances": find_rds_instances,            # replicas then sources; before the subnet group they use and the security groups/VPC around them
    "rds_snapshots": find_rds_snapshots,            # after the instances (no dependency; keeps "database things" together)
    "db_subnet_groups": find_db_subnet_groups,      # after the instances that use it, before the VPC that holds it
    "ebs_snapshots": find_ebs_snapshots,            # after instances (their AMI-less snapshots), before the volumes they came from
    "ebs_volumes": find_ebs_volumes,                # after instances (DeleteOnTermination disks vanish by themselves; the rest become 'available')
    "nat_gateways": find_nat_gateways,              # NAT gateways before the Elastic IPs they hold
    "elastic_ips": find_elastic_ips,
    "security_groups": find_security_groups,        # after everything that holds a group: instances, load balancers, NAT, databases; before the VPC
    "vpcs": find_vpcs,
    "iam_roles": find_iam_roles,
    "iam_users": find_iam_users,
    "iam_policies": find_iam_policies,
}


def _force_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def main(kinds, argv=None, session_factory=None) -> int:
    unknown = [k for k in kinds if k not in FINDERS]
    if unknown:
        raise ValueError(f"unknown resource kind(s): {', '.join(unknown)}")
    _force_utf8()
    parser = argparse.ArgumentParser(description="Delete what this lab created (tag saa-course=lab).")
    parser.add_argument("--region", default=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
    parser.add_argument("--profile", default=None)
    parser.add_argument("--yes", action="store_true", help="really delete (default: dry run)")
    args = parser.parse_args(argv)
    if session_factory is None:
        import boto3

        session_factory = boto3.Session
    kwargs = {"region_name": args.region}
    if args.profile:
        kwargs["profile_name"] = args.profile
    session = session_factory(**kwargs)

    ordered = [k for k in FINDERS if k in kinds]
    found, failures = [], 0
    for kind in ordered:
        try:
            found += FINDERS[kind](session, args.region)
        except Exception as exc:  # keep listing the other kinds
            failures += 1
            print(f"✘ could not list {kind}: {_error_code(exc)}")
    if not found:
        print(f"Nothing tagged {TAG_KEY}={TAG_VALUE} in {args.region} (or IAM). Nothing to do.")
        return 1 if failures else 0
    if not args.yes:
        print(f"DRY RUN — these would be deleted ({TAG_KEY}={TAG_VALUE}). Run again with --yes to delete:")
        for item in found:
            print(f"  · {item.kind:<18} {item.name}  ({item.region})")
        return 1 if failures else 0
    for item in found:
        try:
            item.delete()
            print(f"✔ deleted {item.kind} {item.name}")
        except Blocked as exc:
            failures += 1
            print(f"⚠ left in place {item.kind} {item.name}: {exc}")
        except Exception as exc:
            failures += 1
            print(f"✘ {item.kind} {item.name}: {_error_code(exc)}")
    print("Done." if not failures else f"Done with {failures} problem(s) — fix them in the console or run again.")
    return 1 if failures else 0

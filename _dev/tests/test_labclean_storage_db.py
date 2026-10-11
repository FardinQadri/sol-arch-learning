import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from _harness import labclean

TAG = [{"Key": "saa-course", "Value": "lab"}]
OTHER = [{"Key": "owner", "Value": "someone-else"}]
WEEK4 = ["s3_buckets", "ebs_snapshots", "ebs_volumes"]
WEEK5 = ["dynamodb_tables", "dynamodb_backups", "rds_instances", "rds_snapshots", "db_subnet_groups"]
AZ = "us-east-1a"


@pytest.fixture
def aws(monkeypatch):
    monkeypatch.setattr(labclean, "WAIT_SECONDS", 0)
    with mock_aws():
        yield boto3.Session(region_name="us-east-1")


def run(aws, kinds, *args):
    return labclean.main(kinds, argv=list(args), session_factory=lambda **kw: aws)


def tags(on):
    return TAG if on else OTHER


def api_error(code, op):
    return ClientError({"Error": {"Code": code, "Message": code}}, op)


# -- builders --


def make_bucket(s3, name, on):
    s3.create_bucket(Bucket=name)
    s3.put_bucket_tagging(Bucket=name, Tagging={"TagSet": tags(on)})


def bucket_names(s3):
    return {b["Name"] for b in s3.list_buckets()["Buckets"]}


def make_volume(ec2, on):
    return ec2.create_volume(AvailabilityZone=AZ, Size=8, VolumeType="gp3",
                             TagSpecifications=[{"ResourceType": "volume", "Tags": tags(on)}])["VolumeId"]


def make_instance(ec2, on):
    ami = ec2.describe_images()["Images"][0]["ImageId"]
    return ec2.run_instances(ImageId=ami, InstanceType="t3.micro", MinCount=1, MaxCount=1, Placement={"AvailabilityZone": AZ},
                             TagSpecifications=[{"ResourceType": "instance", "Tags": tags(on)}])["Instances"][0]["InstanceId"]


def volume_ids(ec2):
    return {v["VolumeId"] for v in ec2.describe_volumes(Filters=[{"Name": "tag-key", "Values": ["saa-course", "owner"]}])["Volumes"]}


def make_snapshot(ec2, volume, on):
    return ec2.create_snapshot(VolumeId=volume, TagSpecifications=[{"ResourceType": "snapshot", "Tags": tags(on)}])["SnapshotId"]


def snapshot_exists(ec2, sid):
    return bool(ec2.describe_snapshots(SnapshotIds=[sid])["Snapshots"]) if _exists(lambda: ec2.describe_snapshots(SnapshotIds=[sid])) else False


def _exists(call):
    try:
        call()
        return True
    except ClientError:
        return False


def make_table(ddb, name, on, protected=False):
    ddb.create_table(TableName=name, BillingMode="PAY_PER_REQUEST", DeletionProtectionEnabled=protected,
                     AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"}],
                     KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}], Tags=tags(on))


def table_names(ddb):
    return set(ddb.list_tables()["TableNames"])


def make_db(rds, name, on, protected=False):
    rds.create_db_instance(DBInstanceIdentifier=name, Engine="postgres", DBInstanceClass="db.t4g.micro", AllocatedStorage=20,
                           MasterUsername="admin1", MasterUserPassword="password-1234", DeletionProtection=protected, Tags=tags(on))


def db_names(rds):
    return {d["DBInstanceIdentifier"] for d in rds.describe_db_instances()["DBInstances"]}


def make_subnet_group(aws, name, on):
    ec2, rds = aws.client("ec2"), aws.client("rds")
    vpc = ec2.describe_vpcs(Filters=[{"Name": "is-default", "Values": ["true"]}])["Vpcs"][0]["VpcId"]
    subnets = [s["SubnetId"] for s in ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc]}])["Subnets"]][:2]
    rds.create_db_subnet_group(DBSubnetGroupName=name, DBSubnetGroupDescription=name, SubnetIds=subnets, Tags=tags(on))


def subnet_group_names(rds):
    return {g["DBSubnetGroupName"] for g in rds.describe_db_subnet_groups()["DBSubnetGroups"]}


# ======================= S3 (week 04) =======================


def test_bucket_with_unfinished_multipart_upload_is_deleted(aws):
    s3 = aws.client("s3")
    make_bucket(s3, "mine", True)
    make_bucket(s3, "theirs", False)
    s3.create_multipart_upload(Bucket="mine", Key="big.bin")
    s3.create_multipart_upload(Bucket="theirs", Key="big.bin")
    assert run(aws, ["s3_buckets"], "--yes") == 0
    assert bucket_names(s3) == {"theirs"}
    assert len(s3.list_multipart_uploads(Bucket="theirs").get("Uploads", [])) == 1  # their upload untouched


def test_multipart_uploads_are_aborted_before_the_bucket_goes(aws):
    s3 = aws.client("s3")
    make_bucket(s3, "mine", True)
    s3.create_multipart_upload(Bucket="mine", Key="a")
    s3.create_multipart_upload(Bucket="mine", Key="b")
    aborted = []
    real = s3.abort_multipart_upload
    s3.abort_multipart_upload = lambda **kw: (aborted.append(kw["Key"]), real(**kw))[1]
    labclean._delete_bucket(s3, "mine")
    assert sorted(aborted) == ["a", "b"] and bucket_names(s3) == set()


def test_versioned_bucket_still_emptied(aws):
    s3 = aws.client("s3")
    make_bucket(s3, "mine", True)
    s3.put_bucket_versioning(Bucket="mine", VersioningConfiguration={"Status": "Enabled"})
    for _ in range(3):
        s3.put_object(Bucket="mine", Key="k", Body=b"x")
    s3.delete_object(Bucket="mine", Key="k")
    assert run(aws, ["s3_buckets"], "--yes") == 0
    assert bucket_names(s3) == set()


def test_object_lock_bucket_is_reported_not_failed_obscurely(aws, capsys):
    s3 = aws.client("s3")
    s3.create_bucket(Bucket="locked", ObjectLockEnabledForBucket=True)
    s3.put_bucket_tagging(Bucket="locked", Tagging={"TagSet": TAG})
    s3.put_object(Bucket="locked", Key="k", Body=b"x", ObjectLockMode="COMPLIANCE",
                  ObjectLockRetainUntilDate=__import__("datetime").datetime(2099, 1, 1))
    assert run(aws, ["s3_buckets"], "--yes") == 1
    out = capsys.readouterr().out
    assert "Object Lock" in out and "locked" in out and "left in place" in out
    assert bucket_names(s3) == {"locked"}
    assert len(s3.list_object_versions(Bucket="locked")["Versions"]) == 1


def test_object_lock_bucket_without_locked_objects_is_deleted(aws):
    s3 = aws.client("s3")
    s3.create_bucket(Bucket="lockable", ObjectLockEnabledForBucket=True)
    s3.put_bucket_tagging(Bucket="lockable", Tagging={"TagSet": TAG})
    s3.put_object(Bucket="lockable", Key="k", Body=b"x")
    assert run(aws, ["s3_buckets"], "--yes") == 0
    assert bucket_names(s3) == set()


# ======================= EBS volumes (week 04) =======================


def test_volume_tagged_deleted_untagged_kept(aws):
    ec2 = aws.client("ec2")
    mine, theirs = make_volume(ec2, True), make_volume(ec2, False)
    assert run(aws, ["ebs_volumes"], "--yes") == 0
    assert volume_ids(ec2) == {theirs} and mine not in volume_ids(ec2)


def test_volume_dry_run_lists_and_deletes_nothing(aws, capsys):
    ec2 = aws.client("ec2")
    mine = make_volume(ec2, True)
    assert run(aws, ["ebs_volumes"]) == 0
    out = capsys.readouterr().out
    assert "DRY RUN" in out and mine in out
    assert volume_ids(ec2) == {mine}


def test_attached_volume_on_untagged_instance_is_left_alone_and_reported(aws, capsys):
    ec2 = aws.client("ec2")
    instance = make_instance(ec2, False)
    volume = make_volume(ec2, True)
    ec2.attach_volume(VolumeId=volume, InstanceId=instance, Device="/dev/sdf")
    assert run(aws, ["ebs_volumes"]) == 0  # the dry run already warns
    assert "WILL BE LEFT IN PLACE" in capsys.readouterr().out
    assert run(aws, ["ebs_volumes"], "--yes") == 1
    out = capsys.readouterr().out
    assert "left in place" in out and instance in out
    info = ec2.describe_volumes(VolumeIds=[volume])["Volumes"][0]
    assert info["State"] == "in-use" and info["Attachments"][0]["InstanceId"] == instance  # never detached


def test_attached_volume_on_tagged_instance_is_detached_then_deleted(aws):
    ec2 = aws.client("ec2")
    instance = make_instance(ec2, True)
    volume = make_volume(ec2, True)
    ec2.attach_volume(VolumeId=volume, InstanceId=instance, Device="/dev/sdf")
    assert run(aws, ["ebs_volumes"], "--yes") == 0
    assert volume not in volume_ids(ec2)
    state = ec2.describe_instances(InstanceIds=[instance])["Reservations"][0]["Instances"][0]["State"]["Name"]
    assert state == "running"  # the instance itself is not this kind's business


def test_root_disk_of_a_tagged_instance_is_not_detached(aws):
    ec2 = aws.client("ec2")
    instance = make_instance(ec2, True)
    root = ec2.describe_instances(InstanceIds=[instance])["Reservations"][0]["Instances"][0]["RootDeviceName"]
    volume = make_volume(ec2, True)
    ec2.attach_volume(VolumeId=volume, InstanceId=instance, Device=root)
    with pytest.raises(labclean.Blocked, match="root disk"):
        labclean._delete_volume(ec2, volume)


def test_untagged_volume_on_untagged_instance_never_listed(aws):
    ec2 = aws.client("ec2")
    instance = make_instance(ec2, False)
    volume = make_volume(ec2, False)
    ec2.attach_volume(VolumeId=volume, InstanceId=instance, Device="/dev/sdf")
    assert labclean.find_ebs_volumes(aws, "us-east-1") == []


def test_volume_delete_retries_while_still_detaching(aws, monkeypatch):
    ec2 = aws.client("ec2")
    volume = make_volume(ec2, True)
    real, calls = ec2.delete_volume, []

    def flaky(**kw):
        calls.append(1)
        if len(calls) < 3:
            raise api_error("VolumeInUse", "DeleteVolume")
        return real(**kw)
    monkeypatch.setattr(ec2, "delete_volume", flaky)
    labclean._delete_volume(ec2, volume)
    assert len(calls) == 3 and volume not in volume_ids(ec2)


def test_volume_delete_gives_up_with_timeout(aws, monkeypatch):
    ec2 = aws.client("ec2")
    volume = make_volume(ec2, True)
    monkeypatch.setattr(labclean, "WAIT_ATTEMPTS", 3)
    monkeypatch.setattr(ec2, "delete_volume", lambda **kw: (_ for _ in ()).throw(api_error("VolumeInUse", "DeleteVolume")))
    with pytest.raises(TimeoutError):
        labclean._delete_volume(ec2, volume)


def test_volume_untagged_in_the_meantime_is_not_deleted(aws):
    ec2 = aws.client("ec2")
    volume = make_volume(ec2, True)
    ec2.delete_tags(Resources=[volume], Tags=TAG)  # someone removed the tag between listing and deleting
    with pytest.raises(labclean.Blocked):
        labclean._delete_volume(ec2, volume)
    assert ec2.describe_volumes(VolumeIds=[volume])["Volumes"]


# ======================= EBS snapshots (week 04) =======================


def test_snapshot_tagged_deleted_untagged_and_foreign_kept(aws):
    ec2 = aws.client("ec2")
    vol = make_volume(ec2, False)
    mine, theirs = make_snapshot(ec2, vol, True), make_snapshot(ec2, vol, False)
    before = len(ec2.describe_snapshots()["Snapshots"])  # includes moto's pre-bundled public snapshots
    assert run(aws, ["ebs_snapshots"], "--yes") == 0
    assert len(ec2.describe_snapshots()["Snapshots"]) == before - 1
    assert ec2.describe_snapshots(SnapshotIds=[theirs])["Snapshots"]
    with pytest.raises(ClientError):
        ec2.describe_snapshots(SnapshotIds=[mine])


def test_snapshot_dry_run(aws, capsys):
    ec2 = aws.client("ec2")
    snap = make_snapshot(ec2, make_volume(ec2, False), True)
    assert run(aws, ["ebs_snapshots"]) == 0
    assert snap in capsys.readouterr().out
    assert ec2.describe_snapshots(SnapshotIds=[snap])["Snapshots"]


def test_snapshot_used_by_an_image_is_reported_and_kept(aws):
    ec2 = aws.client("ec2")
    snap = make_snapshot(ec2, make_volume(ec2, False), True)
    # moto's register_image drops the snapshot id from the mappings and delete_snapshot ignores images, so the
    # image that really references the snapshot is injected here
    ec2.describe_images = lambda **kw: {"Images": [{"ImageId": "ami-0abc", "BlockDeviceMappings": [
        {"DeviceName": "/dev/sda1", "Ebs": {"SnapshotId": snap}}]}]}
    with pytest.raises(labclean.Blocked, match="ami-0abc"):
        labclean._delete_snapshot(ec2, snap)
    assert ec2.describe_snapshots(SnapshotIds=[snap])["Snapshots"]  # still there


def test_blocked_snapshot_is_reported_by_main_and_other_snapshots_still_go(aws, capsys, monkeypatch):
    ec2 = aws.client("ec2")
    vol = make_volume(ec2, False)
    held, free = make_snapshot(ec2, vol, True), make_snapshot(ec2, vol, True)
    real = labclean._delete_snapshot

    def pick(client, sid):
        if sid == held:
            raise labclean.Blocked(f"snapshot {sid} is used by image ami-0abc")
        real(client, sid)
    monkeypatch.setattr(labclean, "_delete_snapshot", pick)
    assert run(aws, ["ebs_snapshots"], "--yes") == 1
    assert "ami-0abc" in capsys.readouterr().out
    assert ec2.describe_snapshots(SnapshotIds=[held])["Snapshots"]
    with pytest.raises(ClientError):
        ec2.describe_snapshots(SnapshotIds=[free])


def test_snapshot_in_use_error_from_aws_is_reported(aws, monkeypatch):
    ec2 = aws.client("ec2")
    snap = make_snapshot(ec2, make_volume(ec2, False), True)
    monkeypatch.setattr(ec2, "delete_snapshot", lambda **kw: (_ for _ in ()).throw(api_error("InvalidSnapshot.InUse", "DeleteSnapshot")))
    with pytest.raises(labclean.Blocked, match="deregister"):
        labclean._delete_snapshot(ec2, snap)


def test_week04_end_to_end(aws):
    s3, ec2 = aws.client("s3"), aws.client("ec2")
    for label, on in (("mine", True), ("theirs", False)):
        make_bucket(s3, label, on)
        s3.put_bucket_versioning(Bucket=label, VersioningConfiguration={"Status": "Enabled"})
        s3.put_object(Bucket=label, Key="k", Body=b"x")
        s3.create_multipart_upload(Bucket=label, Key="up")
    vols = {on: make_volume(ec2, on) for on in (True, False)}
    snaps = {on: make_snapshot(ec2, vols[on], on) for on in (True, False)}
    assert run(aws, WEEK4) == 0 and bucket_names(s3) == {"mine", "theirs"}  # dry run
    assert run(aws, WEEK4, "--yes") == 0
    assert bucket_names(s3) == {"theirs"}
    assert volume_ids(ec2) == {vols[False]}
    assert ec2.describe_snapshots(SnapshotIds=[snaps[False]])["Snapshots"]
    with pytest.raises(ClientError):
        ec2.describe_snapshots(SnapshotIds=[snaps[True]])
    assert run(aws, WEEK4, "--yes") == 0  # second run finds nothing


# ======================= DynamoDB (week 05) =======================


def test_table_tagged_deleted_untagged_kept(aws):
    ddb = aws.client("dynamodb")
    make_table(ddb, "mine", True)
    make_table(ddb, "theirs", False)
    assert run(aws, ["dynamodb_tables"], "--yes") == 0
    assert table_names(ddb) == {"theirs"}


def test_table_dry_run(aws, capsys):
    ddb = aws.client("dynamodb")
    make_table(ddb, "mine", True)
    assert run(aws, ["dynamodb_tables"]) == 0
    assert "mine" in capsys.readouterr().out and table_names(ddb) == {"mine"}


def test_tagged_table_with_deletion_protection_is_deleted(aws):
    ddb = aws.client("dynamodb")
    make_table(ddb, "mine", True, protected=True)
    assert run(aws, ["dynamodb_tables"], "--yes") == 0
    assert table_names(ddb) == set()


def test_untagged_table_with_deletion_protection_is_untouched(aws):
    ddb = aws.client("dynamodb")
    make_table(ddb, "theirs", False, protected=True)
    make_table(ddb, "mine", True, protected=True)
    assert run(aws, ["dynamodb_tables"], "--yes") == 0
    assert table_names(ddb) == {"theirs"}
    assert ddb.describe_table(TableName="theirs")["Table"]["DeletionProtectionEnabled"] is True  # protection not switched off


def test_table_delete_waits_until_gone(aws, monkeypatch):
    ddb = aws.client("dynamodb")
    make_table(ddb, "mine", True)
    real_delete, real_describe, polls = ddb.delete_table, ddb.describe_table, []
    deleted = []
    monkeypatch.setattr(ddb, "delete_table", lambda **kw: (deleted.append(1), real_delete(**kw))[1])

    def slow(**kw):  # moto deletes at once; AWS shows DELETING for a while
        if deleted:
            polls.append(1)
            if len(polls) < 4:
                return {"Table": {"TableName": kw["TableName"], "TableStatus": "DELETING"}}
        return real_describe(**kw)
    monkeypatch.setattr(ddb, "describe_table", slow)
    labclean._delete_table(ddb, "mine")
    assert len(polls) >= 4 and len(deleted) == 1  # waited, and did not delete twice


def test_table_delete_retries_while_table_is_busy(aws, monkeypatch):
    ddb = aws.client("dynamodb")
    make_table(ddb, "mine", True)
    real, calls = ddb.delete_table, []

    def busy(**kw):
        calls.append(1)
        if len(calls) < 3:
            raise api_error("ResourceInUseException", "DeleteTable")
        return real(**kw)
    monkeypatch.setattr(ddb, "delete_table", busy)
    labclean._delete_table(ddb, "mine")
    assert len(calls) == 3 and table_names(ddb) == set()


def test_table_tag_listing_follows_next_token(aws):
    ddb = aws.client("dynamodb")
    make_table(ddb, "mine", True)

    class Paged:
        def __init__(self, client):
            self._c, self.calls = client, 0

        def list_tags_of_resource(self, **kw):
            self.calls += 1
            if "NextToken" not in kw:  # first page: only the unrelated tag, lab tag arrives on the second page
                return {"Tags": OTHER, "NextToken": "t2"}
            return self._c.list_tags_of_resource(ResourceArn=kw["ResourceArn"])

        def __getattr__(self, name):
            return getattr(self._c, name)

    paged = Paged(ddb)
    assert [t["name"] for t in labclean._tagged_tables(paged)] == ["mine"] and paged.calls == 2


def test_backups_of_tagged_table_deleted_untagged_table_backups_kept(aws):
    ddb = aws.client("dynamodb")
    make_table(ddb, "mine", True)
    make_table(ddb, "theirs", False)
    ddb.create_backup(TableName="mine", BackupName="bk1")
    ddb.create_backup(TableName="mine", BackupName="bk2")
    ddb.create_backup(TableName="theirs", BackupName="keep")
    assert run(aws, ["dynamodb_backups"], "--yes") == 0
    assert ddb.list_backups(TableName="mine")["BackupSummaries"] == []
    assert len(ddb.list_backups(TableName="theirs")["BackupSummaries"]) == 1
    assert table_names(ddb) == {"mine", "theirs"}  # this kind never deletes tables


def test_backup_dry_run_lists_backups_by_table(aws, capsys):
    ddb = aws.client("dynamodb")
    make_table(ddb, "mine", True)
    ddb.create_backup(TableName="mine", BackupName="bk1")
    assert run(aws, ["dynamodb_backups"]) == 0
    assert "mine / bk1" in capsys.readouterr().out
    assert len(ddb.list_backups(TableName="mine")["BackupSummaries"]) == 1


def test_backups_are_listed_before_and_deleted_before_their_table(aws, capsys):
    ddb = aws.client("dynamodb")
    make_table(ddb, "mine", True)
    ddb.create_backup(TableName="mine", BackupName="bk1")
    assert run(aws, WEEK5, "--yes") == 0
    out = capsys.readouterr().out
    assert out.index("deleted dynamodb_backups") < out.index("deleted dynamodb_tables")
    assert table_names(ddb) == set()


def test_backup_listing_follows_pagination(aws):
    ddb = aws.client("dynamodb")
    make_table(ddb, "mine", True)
    for i in range(3):
        ddb.create_backup(TableName="mine", BackupName=f"bk{i}")
    real = ddb.list_backups

    def one_at_a_time(**kw):
        kw["Limit"] = 1
        return real(**kw)

    class Limited:
        def __getattr__(self, name):
            return getattr(ddb, name)
        list_backups = staticmethod(one_at_a_time)

    class Sess:
        def client(self, *a, **kw):
            return Limited()

    assert len(labclean.find_dynamodb_backups(Sess(), "us-east-1")) == 3


# ======================= RDS (week 05) =======================


def test_rds_instance_tagged_deleted_untagged_kept(aws):
    rds = aws.client("rds")
    make_db(rds, "mine", True)
    make_db(rds, "theirs", False)
    assert run(aws, ["rds_instances"], "--yes") == 0
    assert db_names(rds) == {"theirs"}


def test_rds_dry_run(aws, capsys):
    rds = aws.client("rds")
    make_db(rds, "mine", True)
    assert run(aws, ["rds_instances"]) == 0
    assert "mine" in capsys.readouterr().out and db_names(rds) == {"mine"}


def test_rds_deletion_protected_instance_deleted_only_if_tagged(aws):
    rds = aws.client("rds")
    make_db(rds, "mine", True, protected=True)
    make_db(rds, "theirs", False, protected=True)
    assert run(aws, ["rds_instances"], "--yes") == 0
    assert db_names(rds) == {"theirs"}
    assert rds.describe_db_instances(DBInstanceIdentifier="theirs")["DBInstances"][0]["DeletionProtection"] is True


def test_rds_delete_skips_final_snapshot_and_deletes_automated_backups(aws):
    rds = aws.client("rds")
    make_db(rds, "mine", True)
    seen = {}
    real = rds.delete_db_instance
    rds.delete_db_instance = lambda **kw: (seen.update(kw), real(**kw))[1]
    labclean._delete_db_instance(rds, "mine", {"mine"})
    assert seen["SkipFinalSnapshot"] is True and seen["DeleteAutomatedBackups"] is True
    assert rds.describe_db_snapshots(SnapshotType="manual")["DBSnapshots"] == []


def test_rds_delete_waits_through_deleting_state(aws, monkeypatch):
    rds = aws.client("rds")
    make_db(rds, "mine", True)
    rds.delete_db_instance(DBInstanceIdentifier="mine", SkipFinalSnapshot=True)
    real, polls = rds.describe_db_instances, []

    def lingering(**kw):  # AWS keeps showing the instance as 'deleting' for minutes
        polls.append(1)
        if len(polls) < 4:
            return {"DBInstances": [{"DBInstanceIdentifier": "mine", "DBInstanceStatus": "deleting"}]}
        return real(**kw)
    monkeypatch.setattr(rds, "describe_db_instances", lingering)
    labclean._delete_db_instance(rds, "mine", {"mine"})
    assert len(polls) >= 4


def test_rds_delete_retries_while_instance_is_modifying(aws, monkeypatch):
    rds = aws.client("rds")
    make_db(rds, "mine", True)
    real, calls = rds.delete_db_instance, []

    def busy(**kw):
        calls.append(1)
        if len(calls) < 3:
            raise api_error("InvalidDBInstanceState", "DeleteDBInstance")
        return real(**kw)
    monkeypatch.setattr(rds, "delete_db_instance", busy)
    labclean._delete_db_instance(rds, "mine", {"mine"})
    assert len(calls) == 3 and db_names(rds) == set()


def test_rds_delete_gives_up_with_timeout(aws, monkeypatch):
    rds = aws.client("rds")
    make_db(rds, "mine", True)
    monkeypatch.setattr(labclean, "WAIT_ATTEMPTS", 3)
    monkeypatch.setattr(rds, "delete_db_instance", lambda **kw: (_ for _ in ()).throw(api_error("InvalidDBInstanceState", "DeleteDBInstance")))
    with pytest.raises(TimeoutError):
        labclean._delete_db_instance(rds, "mine", {"mine"})


def test_replica_and_source_both_deleted_replica_first(aws, capsys):
    rds = aws.client("rds")
    make_db(rds, "a-source", True)
    rds.create_db_instance_read_replica(DBInstanceIdentifier="z-replica", SourceDBInstanceIdentifier="a-source", Tags=TAG)
    names = [f.name for f in labclean.find_rds_instances(aws, "us-east-1")]
    assert names == ["z-replica", "a-source"]  # despite alphabetical order
    assert run(aws, ["rds_instances"], "--yes") == 0
    out = capsys.readouterr().out
    assert out.index("z-replica") < out.index("a-source") and db_names(rds) == set()


def test_replica_of_replica_goes_first(aws):
    rds = aws.client("rds")
    make_db(rds, "a-root", True)
    rds.create_db_instance_read_replica(DBInstanceIdentifier="b-mid", SourceDBInstanceIdentifier="a-root", Tags=TAG)
    rds.create_db_instance_read_replica(DBInstanceIdentifier="c-leaf", SourceDBInstanceIdentifier="b-mid", Tags=TAG)
    assert [f.name for f in labclean.find_rds_instances(aws, "us-east-1")] == ["c-leaf", "b-mid", "a-root"]


def test_tagged_source_with_untagged_replica_is_left_alone(aws, capsys):
    rds = aws.client("rds")
    make_db(rds, "mine", True)
    rds.create_db_instance_read_replica(DBInstanceIdentifier="theirs-replica", SourceDBInstanceIdentifier="mine", Tags=OTHER)
    assert run(aws, ["rds_instances"]) == 0
    assert "WILL BE LEFT IN PLACE" in capsys.readouterr().out
    assert run(aws, ["rds_instances"], "--yes") == 1  # deleting the source would promote their replica
    assert "left in place" in capsys.readouterr().out
    assert db_names(rds) == {"mine", "theirs-replica"}


def test_rds_instance_without_taglist_falls_back_to_list_tags(aws):
    rds = aws.client("rds")
    make_db(rds, "mine", True)
    make_db(rds, "theirs", False)
    real = rds.describe_db_instances

    def stripped(**kw):
        result = real(**kw)
        for db in result["DBInstances"]:
            db.pop("TagList", None)
        return result

    class Stripped:
        def describe_db_instances(self, **kw):
            return stripped(**kw)

        def get_paginator(self, name):
            assert name == "describe_db_instances"
            outer = self

            class P:
                def paginate(self, **kw):
                    yield outer.describe_db_instances(**kw)
            return P()

        def __getattr__(self, name):
            return getattr(rds, name)

    class Sess:
        def client(self, *a, **kw):
            return Stripped()

    assert [f.name for f in labclean.find_rds_instances(Sess(), "us-east-1")] == ["mine"]


# ---- RDS snapshots ----


def test_rds_snapshot_tagged_manual_deleted_untagged_kept(aws):
    rds = aws.client("rds")
    make_db(rds, "db", False)
    rds.create_db_snapshot(DBSnapshotIdentifier="mine", DBInstanceIdentifier="db", Tags=TAG)
    rds.create_db_snapshot(DBSnapshotIdentifier="theirs", DBInstanceIdentifier="db", Tags=OTHER)
    assert run(aws, ["rds_snapshots"], "--yes") == 0
    assert [s["DBSnapshotIdentifier"] for s in rds.describe_db_snapshots(SnapshotType="manual")["DBSnapshots"]] == ["theirs"]
    assert db_names(rds) == {"db"}


def test_rds_snapshot_dry_run(aws, capsys):
    rds = aws.client("rds")
    make_db(rds, "db", False)
    rds.create_db_snapshot(DBSnapshotIdentifier="mine", DBInstanceIdentifier="db", Tags=TAG)
    assert run(aws, ["rds_snapshots"]) == 0
    assert "mine" in capsys.readouterr().out
    assert len(rds.describe_db_snapshots(SnapshotType="manual")["DBSnapshots"]) == 1


def test_rds_snapshot_delete_retries_while_creating(aws, monkeypatch):
    rds = aws.client("rds")
    make_db(rds, "db", False)
    rds.create_db_snapshot(DBSnapshotIdentifier="mine", DBInstanceIdentifier="db", Tags=TAG)
    real, calls = rds.delete_db_snapshot, []

    def busy(**kw):
        calls.append(1)
        if len(calls) < 3:
            raise api_error("InvalidDBSnapshotState", "DeleteDBSnapshot")
        return real(**kw)
    monkeypatch.setattr(rds, "delete_db_snapshot", busy)
    labclean._delete_db_snapshot(rds, "mine")
    assert len(calls) == 3 and rds.describe_db_snapshots(SnapshotType="manual")["DBSnapshots"] == []


# ---- DB subnet groups ----


def test_subnet_group_tagged_deleted_untagged_kept(aws):
    rds = aws.client("rds")
    make_subnet_group(aws, "mine", True)
    make_subnet_group(aws, "theirs", False)
    assert run(aws, ["db_subnet_groups"], "--yes") == 0
    assert "theirs" in subnet_group_names(rds) and "mine" not in subnet_group_names(rds)


def test_subnet_group_dry_run_and_default_group_never_listed(aws, capsys):
    rds = aws.client("rds")
    make_subnet_group(aws, "mine", True)
    assert [f.name for f in labclean.find_db_subnet_groups(aws, "us-east-1")] == ["mine"]
    assert run(aws, ["db_subnet_groups"]) == 0
    assert "mine" in capsys.readouterr().out and "mine" in subnet_group_names(rds)


def test_subnet_group_delete_retries_while_instance_shuts_down(aws, monkeypatch):
    rds = aws.client("rds")
    make_subnet_group(aws, "mine", True)
    real, calls = rds.delete_db_subnet_group, []

    def busy(**kw):
        calls.append(1)
        if len(calls) < 3:
            raise api_error("InvalidDBSubnetGroupStateFault", "DeleteDBSubnetGroup")
        return real(**kw)
    monkeypatch.setattr(rds, "delete_db_subnet_group", busy)
    labclean._delete_db_subnet_group(rds, "mine")
    assert len(calls) == 3 and "mine" not in subnet_group_names(rds)


# ======================= whole labs, order, main =======================


def test_week05_end_to_end(aws):
    ddb, rds = aws.client("dynamodb"), aws.client("rds")
    for label, on in (("mine", True), ("theirs", False)):
        make_table(ddb, f"{label}-table", on, protected=True)
        ddb.create_backup(TableName=f"{label}-table", BackupName=f"{label}-backup")
        make_subnet_group(aws, f"{label}-sg", on)
        make_db(rds, f"{label}-db", on, protected=True)
        rds.create_db_snapshot(DBSnapshotIdentifier=f"{label}-snap", DBInstanceIdentifier=f"{label}-db", Tags=tags(on))
    assert run(aws, WEEK5) == 0  # dry run changes nothing
    assert table_names(ddb) == {"mine-table", "theirs-table"} and len(db_names(rds)) == 2
    assert run(aws, WEEK5, "--yes") == 0
    assert table_names(ddb) == {"theirs-table"}
    assert [b["BackupName"] for b in ddb.list_backups(TableName="theirs-table")["BackupSummaries"]] == ["theirs-backup"]
    assert db_names(rds) == {"theirs-db"}
    assert [s["DBSnapshotIdentifier"] for s in rds.describe_db_snapshots(SnapshotType="manual")["DBSnapshots"]] == ["theirs-snap"]
    assert "theirs-sg" in subnet_group_names(rds) and "mine-sg" not in subnet_group_names(rds)
    assert run(aws, WEEK5, "--yes") == 0  # nothing left of ours


def test_finders_order_for_weeks_04_and_05():
    assert list(labclean.FINDERS) == [
        "s3_buckets", "autoscaling_groups", "load_balancers", "target_groups", "ec2_instances", "launch_templates",
        "dynamodb_backups", "dynamodb_tables", "rds_instances", "rds_snapshots", "db_subnet_groups",
        "ebs_snapshots", "ebs_volumes", "nat_gateways", "elastic_ips", "security_groups", "vpcs",
        "iam_roles", "iam_users", "iam_policies"]


def test_main_rejects_unknown_kind(aws):
    with pytest.raises(ValueError, match="unknown resource kind"):
        run(aws, ["ebs_volumes", "efs_file_systems"])


def test_blocked_is_printed_with_its_message_and_counts_as_a_problem(aws, monkeypatch, capsys):
    def finder(session, region):
        def boom():
            raise labclean.Blocked("because of reasons")
        return [labclean.Found("ebs_volumes", "vol-1", region, boom)]
    monkeypatch.setitem(labclean.FINDERS, "ebs_volumes", finder)
    assert run(aws, ["ebs_volumes"], "--yes") == 1
    assert "because of reasons" in capsys.readouterr().out

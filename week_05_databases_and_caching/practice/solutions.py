"""Reference solutions for week 05.

Drills 01, 02, 06 and 07: the course's reference models ARE the solution — read _harness/awslib/dynamo.py,
caching.py and dbmath.py and compare them with yours.
"""
from _harness.awslib.caching import simulate  # noqa: F401
from _harness.awslib.dbmath import needs_proxy, peak_concurrency, proxy_pool_size  # noqa: F401
from _harness.awslib.dynamo import (  # noqa: F401
    break_even_utilisation, monthly_cost_on_demand, monthly_cost_provisioned,
    provisioned_capacity, read_units, write_units,
)

# ── Drill 03: one table, every question ──
TABLE = {
    "KeySchema": [{"AttributeName": "pk", "KeyType": "HASH"}, {"AttributeName": "sk", "KeyType": "RANGE"}],
    "AttributeDefinitions": [{"AttributeName": n, "AttributeType": "S"} for n in ("pk", "sk", "gsi1pk", "gsi1sk")],
    "GlobalSecondaryIndexes": [{
        "IndexName": "owner-index",
        "KeySchema": [{"AttributeName": "gsi1pk", "KeyType": "HASH"}, {"AttributeName": "gsi1sk", "KeyType": "RANGE"}],
        "Projection": {"ProjectionType": "ALL"},
    }],
}


def link_item(code, url, owner, created):
    return {"pk": f"LINK#{code}", "sk": "META", "code": code, "url": url, "owner": owner, "created": created,
            "gsi1pk": f"OWNER#{owner}", "gsi1sk": created}


def click_item(code, day, count):
    return {"pk": f"LINK#{code}", "sk": f"DAY#{day}", "day": day, "count": count}


def get_link(table, code):
    item = table.get_item(Key={"pk": f"LINK#{code}", "sk": "META"}).get("Item")
    return None if item is None else {"code": item["code"], "url": item["url"], "owner": item["owner"]}


def clicks_between(table, code, first_day, last_day):
    result = table.query(KeyConditionExpression=Key("pk").eq(f"LINK#{code}") & Key("sk").between(f"DAY#{first_day}", f"DAY#{last_day}"))
    return [(item["day"], int(item["count"])) for item in result["Items"]]


def links_of_owner(table, owner):
    result = table.query(IndexName="owner-index", KeyConditionExpression=Key("gsi1pk").eq(f"OWNER#{owner}"),
                         ScanIndexForward=False)
    return [item["code"] for item in result["Items"]]


# ── Drill 04: never lose an update ──
class StaleVersion(Exception):
    """The item changed since you read it."""


def rename_link(table, code, new_url, expected_version):
    try:
        got = table.update_item(
            Key={"pk": f"LINK#{code}"}, UpdateExpression="SET #u = :u, #v = :next",
            ConditionExpression="#v = :expected", ExpressionAttributeNames={"#u": "url", "#v": "version"},
            ExpressionAttributeValues={":u": new_url, ":next": expected_version + 1, ":expected": expected_version},
            ReturnValues="ALL_NEW")
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise StaleVersion(f"link {code} is no longer at version {expected_version}") from exc
        raise
    return int(got["Attributes"]["version"])


def transfer_owner(client, code, old_owner, new_owner):
    if old_owner == new_owner:
        raise ValueError("old and new owner are the same")

    def key(pk):
        return {"pk": {"S": pk}}

    client.transact_write_items(TransactItems=[
        {"Update": {"TableName": TABLE_NAME, "Key": key(f"LINK#{code}"),
                    "UpdateExpression": "SET #o = :new ADD #v :one", "ConditionExpression": "#o = :old",
                    "ExpressionAttributeNames": {"#o": "owner", "#v": "version"},
                    "ExpressionAttributeValues": {":new": {"S": new_owner}, ":old": {"S": old_owner}, ":one": {"N": "1"}}}},
        {"Update": {"TableName": TABLE_NAME, "Key": key(f"OWNER#{old_owner}"),
                    "UpdateExpression": "ADD link_count :minus", "ExpressionAttributeValues": {":minus": {"N": "-1"}}}},
        {"Update": {"TableName": TABLE_NAME, "Key": key(f"OWNER#{new_owner}"),
                    "UpdateExpression": "ADD link_count :one", "ExpressionAttributeValues": {":one": {"N": "1"}}}},
    ])


# ── Drill 05: keep it tidy, keep it safe ──
def protect_table(client, table_name, ttl_attribute):
    client.update_time_to_live(TableName=table_name,
                               TimeToLiveSpecification={"Enabled": True, "AttributeName": ttl_attribute})
    client.update_continuous_backups(TableName=table_name,
                                     PointInTimeRecoverySpecification={"PointInTimeRecoveryEnabled": True})
    return client.create_backup(TableName=table_name, BackupName=f"{table_name}-baseline")["BackupDetails"]["BackupArn"]


# ── Drill 08: a database that fails over ──
def create_primary(rds, subnet_group, sg_id):
    rds.create_db_instance(
        DBInstanceIdentifier="shortly-db", Engine="postgres", EngineVersion="17.4", DBInstanceClass="db.t4g.micro",
        AllocatedStorage=20, StorageType="gp3", MultiAZ=True, StorageEncrypted=True,
        MasterUsername="shortly_admin", ManageMasterUserPassword=True,
        BackupRetentionPeriod=7, DeletionProtection=True, PubliclyAccessible=False,
        DBSubnetGroupName=subnet_group, VpcSecurityGroupIds=[sg_id])
    return "shortly-db"


def add_replica(rds, primary_id):
    rds.create_db_instance_read_replica(DBInstanceIdentifier="shortly-db-replica",
                                        SourceDBInstanceIdentifier=primary_id, DBInstanceClass="db.t4g.micro")
    return "shortly-db-replica"


def take_snapshot(rds, db_id):
    snapshot_id = f"{db_id}-baseline"
    rds.create_db_snapshot(DBSnapshotIdentifier=snapshot_id, DBInstanceIdentifier=db_id)
    return snapshot_id


# ── Drills 09 and 10: decide ──
CHOICES = {1: "multi-az instance", 2: "read replica", 3: "aurora replica", 4: "aurora global database",
           5: "multi-az cluster", 6: "cross-region read replica", 7: "rds proxy"}
ENGINES = {1: "rds", 2: "aurora", 3: "dynamodb", 4: "elasticache", 5: "documentdb", 6: "neptune",
           7: "keyspaces", 8: "opensearch", 9: "memorydb"}

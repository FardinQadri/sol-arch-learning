"""Deliberately wrong implementations for week 05 — each must be caught by its drill."""
MUTANTS = [
    {"id": "item-size-rounded-down", "drill": 1, "code": '''
import math
def read_units(item_kb, consistency="eventual"):
    if not 0 < item_kb <= 400:
        raise ValueError("item size")
    if consistency not in ("eventual", "strong", "transactional"):
        raise ValueError("consistency")
    return math.floor(item_kb / 4) * {"eventual": 0.5, "strong": 1.0, "transactional": 2.0}[consistency]
def write_units(item_kb, transactional=False):
    if not 0 < item_kb <= 400:
        raise ValueError("item size")
    return math.floor(item_kb) * (2 if transactional else 1)
'''},
    {"id": "provisioned-billed-for-used-hours", "drill": 2, "code": '''
def monthly_cost_provisioned(rcu, wcu, hours=730, price=PRICES):
    if rcu < 0 or wcu < 0 or hours < 0:
        raise ValueError("negative")
    busy_hours = hours * 8 / 24      # "we only use it in the working day, so we only pay then"
    return round(busy_hours * (rcu * price["dynamodb_rcu_hour"] + wcu * price["dynamodb_wcu_hour"]), 4)
'''},
    {"id": "owner-index-keys-swapped", "drill": 3, "code": '''
TABLE = {
    "KeySchema": [{"AttributeName": "pk", "KeyType": "HASH"}, {"AttributeName": "sk", "KeyType": "RANGE"}],
    "AttributeDefinitions": [{"AttributeName": n, "AttributeType": "S"} for n in ("pk", "sk", "gsi1pk", "gsi1sk")],
    "GlobalSecondaryIndexes": [{
        "IndexName": "owner-index",
        "KeySchema": [{"AttributeName": "gsi1sk", "KeyType": "HASH"}, {"AttributeName": "gsi1pk", "KeyType": "RANGE"}],
        "Projection": {"ProjectionType": "ALL"},
    }],
}
'''},
    {"id": "scan-instead-of-query", "drill": 3, "code": '''
def links_of_owner(table, owner):
    items = table.scan(FilterExpression=Key("owner").eq(owner))["Items"]
    return [i["code"] for i in sorted(items, key=lambda i: i["created"], reverse=True)]
'''},
    {"id": "lost-update", "drill": 4, "code": '''
def rename_link(table, code, new_url, expected_version):
    got = table.update_item(
        Key={"pk": f"LINK#{code}"}, UpdateExpression="SET #u = :u, #v = :next",
        ExpressionAttributeNames={"#u": "url", "#v": "version"},
        ExpressionAttributeValues={":u": new_url, ":next": expected_version + 1}, ReturnValues="ALL_NEW")
    return int(got["Attributes"]["version"])
'''},
    {"id": "transfer-without-a-transaction", "drill": 4, "code": '''
def transfer_owner(client, code, old_owner, new_owner):
    if old_owner == new_owner:
        raise ValueError("same owner")
    def key(pk):
        return {"pk": {"S": pk}}
    client.update_item(TableName=TABLE_NAME, Key=key(f"OWNER#{old_owner}"), UpdateExpression="ADD link_count :m",
                       ExpressionAttributeValues={":m": {"N": "-1"}})
    client.update_item(TableName=TABLE_NAME, Key=key(f"OWNER#{new_owner}"), UpdateExpression="ADD link_count :o",
                       ExpressionAttributeValues={":o": {"N": "1"}})
    client.update_item(TableName=TABLE_NAME, Key=key(f"LINK#{code}"), UpdateExpression="SET #o = :new ADD #v :o",
                       ExpressionAttributeNames={"#o": "owner", "#v": "version"},
                       ExpressionAttributeValues={":new": {"S": new_owner}, ":o": {"N": "1"}})
'''},
    {"id": "ttl-but-no-pitr", "drill": 5, "code": '''
def protect_table(client, table_name, ttl_attribute):
    client.update_time_to_live(TableName=table_name,
                               TimeToLiveSpecification={"Enabled": True, "AttributeName": ttl_attribute})
    return client.create_backup(TableName=table_name, BackupName=f"{table_name}-baseline")["BackupDetails"]["BackupArn"]
'''},
    {"id": "write-through-forgets-the-cache", "drill": 6, "code": '''
from _harness.awslib import caching as _ref
def simulate(events, strategy, ttl=None):
    return _ref.simulate(events, "lazy" if strategy == "write-through" else strategy, ttl)
'''},
    {"id": "concurrency-rounded-down", "drill": 7, "code": '''
import math
def peak_concurrency(requests_per_second, avg_duration_s):
    if requests_per_second <= 0 or avg_duration_s <= 0:
        raise ValueError("positive inputs only")
    return max(1, math.floor(round(requests_per_second * avg_duration_s, 9)))
'''},
    {"id": "single-az", "drill": 8, "code": '''
def create_primary(rds, subnet_group, sg_id):
    rds.create_db_instance(
        DBInstanceIdentifier="shortly-db", Engine="postgres", EngineVersion="17.4", DBInstanceClass="db.t4g.micro",
        AllocatedStorage=20, StorageType="gp3", MultiAZ=False, StorageEncrypted=True,
        MasterUsername="shortly_admin", ManageMasterUserPassword=True,
        BackupRetentionPeriod=7, DeletionProtection=True, PubliclyAccessible=False,
        DBSubnetGroupName=subnet_group, VpcSecurityGroupIds=[sg_id])
    return "shortly-db"
'''},
    {"id": "unanswered-ha", "drill": 9, "code": '''
CHOICES = {n: None for n in CHOICES}
'''},
    {"id": "unanswered-engines", "drill": 10, "code": '''
ENGINES = {n: None for n in ENGINES}
'''},
]

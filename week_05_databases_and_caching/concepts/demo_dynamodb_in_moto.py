"""Demo — an orders table in DynamoDB built with boto3 against a fake AWS (moto): partition + sort key, one GSI,
a conditional put that fails, a transaction that is cancelled as a whole, a Query by key range and a GSI query.
Run it: python concepts/demo_dynamodb_in_moto.py   (offline; nothing here touches a real account)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.awslib.safety import force_utf8, use_fake_aws_env  # noqa: E402

force_utf8()
use_fake_aws_env()

import boto3  # noqa: E402
from botocore.exceptions import ClientError  # noqa: E402
from moto import mock_aws  # noqa: E402

REGION = "us-east-1"

with mock_aws():
    ddb = boto3.client("dynamodb", region_name=REGION)

    # 1. The table: partition key customer, sort key order_id, and a GSI that answers "orders by status, newest first".
    ddb.create_table(
        TableName="orders",
        BillingMode="PAY_PER_REQUEST",
        AttributeDefinitions=[
            {"AttributeName": "customer", "AttributeType": "S"},
            {"AttributeName": "order_id", "AttributeType": "S"},
            {"AttributeName": "status", "AttributeType": "S"},
            {"AttributeName": "placed_at", "AttributeType": "S"},
        ],
        KeySchema=[{"AttributeName": "customer", "KeyType": "HASH"}, {"AttributeName": "order_id", "KeyType": "RANGE"}],
        GlobalSecondaryIndexes=[{
            "IndexName": "by_status",
            "KeySchema": [{"AttributeName": "status", "KeyType": "HASH"}, {"AttributeName": "placed_at", "KeyType": "RANGE"}],
            "Projection": {"ProjectionType": "ALL"},
        }],
    )
    table = ddb.describe_table(TableName="orders")["Table"]
    print(f"Table {table['TableName']}: key {[k['AttributeName'] for k in table['KeySchema']]}, "
          f"billing {table['BillingModeSummary']['BillingMode']}, "
          f"GSI {[g['IndexName'] for g in table['GlobalSecondaryIndexes']]}")

    def order(customer, order_id, status, placed_at, total):
        return {"customer": {"S": customer}, "order_id": {"S": order_id}, "status": {"S": status},
                "placed_at": {"S": placed_at}, "total": {"N": str(total)}}

    seed = [
        order("alice", "2026-01#001", "shipped", "2026-01-05", 40),
        order("alice", "2026-01#002", "shipped", "2026-01-19", 15),
        order("alice", "2026-02#003", "pending", "2026-02-02", 99),
        order("alice", "2026-03#004", "pending", "2026-03-11", 20),
        order("bob", "2026-02#005", "pending", "2026-02-08", 60),
        order("bob", "2026-02#006", "cancelled", "2026-02-20", 10),
    ]
    for item in seed:
        ddb.put_item(TableName="orders", Item=item)
    print(f"\nPut {len(seed)} items.")

    # 2. A conditional put: create-only. The second try hits an existing key and fails.
    print("\n2. Conditional put (attribute_not_exists) - 'create the order only if it is new'")
    for attempt in (1, 2):
        try:
            ddb.put_item(TableName="orders", Item=order("carol", "2026-03#007", "pending", "2026-03-15", 5),
                         ConditionExpression="attribute_not_exists(customer)")
            print(f"   attempt {attempt}: written")
        except ClientError as err:
            print(f"   attempt {attempt}: {err.response['Error']['Code']} - {err.response['Error']['Message']}")

    # 3. A transaction: mark one order shipped (condition: still pending) and add a second order.
    #    The condition on the first fails, so the whole transaction is cancelled and the second put never lands.
    print("\n3. A transaction that is cancelled as a whole")
    try:
        ddb.transact_write_items(TransactItems=[
            {"Update": {"TableName": "orders", "Key": {"customer": {"S": "bob"}, "order_id": {"S": "2026-02#006"}},
                        "UpdateExpression": "SET #s = :shipped", "ConditionExpression": "#s = :pending",
                        "ExpressionAttributeNames": {"#s": "status"},
                        "ExpressionAttributeValues": {":shipped": {"S": "shipped"}, ":pending": {"S": "pending"}}}},
            {"Put": {"TableName": "orders", "Item": order("bob", "2026-03#008", "pending", "2026-03-20", 70)}},
        ])
    except ClientError as err:
        reasons = [r["Code"] for r in err.response["CancellationReasons"]]
        print(f"   {err.response['Error']['Code']}, reasons per action: {reasons}")
    check = ddb.get_item(TableName="orders", Key={"customer": {"S": "bob"}, "order_id": {"S": "2026-03#008"}})
    print(f"   was the second order written? {'Item' in check}   (all or nothing: no)")

    # 4. Query by key range: one partition key value, then a sort-key condition. This is the cheap read.
    print("\n4. Query: alice's orders from February and March (sort key between two values)")
    q = ddb.query(TableName="orders", KeyConditionExpression="customer = :c AND order_id BETWEEN :a AND :b",
                  ExpressionAttributeValues={":c": {"S": "alice"}, ":a": {"S": "2026-02"}, ":b": {"S": "2026-03~"}})
    for item in q["Items"]:
        print(f"   {item['order_id']['S']:<13} {item['status']['S']:<10} total {item['total']['N']}")
    q = ddb.query(TableName="orders", KeyConditionExpression="customer = :c AND begins_with(order_id, :p)",
                  ExpressionAttributeValues={":c": {"S": "alice"}, ":p": {"S": "2026-01"}}, ScanIndexForward=False)
    print(f"   begins_with '2026-01', newest first: {[i['order_id']['S'] for i in q['Items']]}")

    # 5. A GSI query answers a question the table key cannot: all pending orders, oldest first.
    print("\n5. GSI query: every pending order across customers, sorted by date")
    g = ddb.query(TableName="orders", IndexName="by_status", KeyConditionExpression="#s = :p",
                  ExpressionAttributeNames={"#s": "status"}, ExpressionAttributeValues={":p": {"S": "pending"}})
    for item in g["Items"]:
        print(f"   {item['placed_at']['S']}  {item['customer']['S']:<6} {item['order_id']['S']}")
    try:
        ddb.query(TableName="orders", IndexName="by_status", ConsistentRead=True, KeyConditionExpression="#s = :p",
                  ExpressionAttributeNames={"#s": "status"}, ExpressionAttributeValues={":p": {"S": "pending"}})
    except ClientError as err:
        print(f"   strongly consistent read on a GSI: {err.response['Error']['Message']}")

    print("\nWhat moto does NOT simulate (so the course models it in pure Python):")
    print("  - TTL: the setting is stored, but expired items never disappear.")
    print("  - Capacity: ConsumedCapacity is a constant that ignores item size, and provisioned tables never throttle.")
    print("  - RDS: no Multi-AZ standby and no failover; a reboot with ForceFailover changes nothing.")
    print("  - ElastiCache: CloudFormation skips replication groups and no cache behaviour (hits, expiry, failover) exists.")
    print("  That is why drills 01, 02, 06 and 07 are models: you build the behaviour yourself.")

print("\nNow do drills 03–05 and 08.")

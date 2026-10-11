"""M05.6 — exports for later stacks, lint-clean, and a deploy in moto (iam + network + data) for both environments."""
import pytest

EXPORTS = {"DbEndpointAddress": "db-endpoint", "DbPort": "db-port", "DbSecretArn": "db-secret-arn",
           "CacheEndpoint": "cache-endpoint", "ClicksTableName": "clicks-table", "ClicksTableArn": "clicks-table-arn"}
VALUES = {"DbEndpointAddress": "Database.Endpoint.Address", "DbPort": "Database.Endpoint.Port",
          "DbSecretArn": "Database.MasterUserSecret.SecretArn", "CacheEndpoint": "Cache.PrimaryEndPoint.Address",
          "ClicksTableName": "ClicksTable", "ClicksTableArn": "ClicksTable.Arn"}

# moto does not create ElastiCache or Secrets Manager resources from CloudFormation, and it cannot answer
# !GetAtt Database.MasterUserSecret.SecretArn. The deploy test therefore removes those resource types (and the
# Outputs that point at them) and gives moto a literal for the secret ARN. Everything else is really created.
MOTO_SKIP = ("AWS::ElastiCache::SubnetGroup", "AWS::ElastiCache::ReplicationGroup", "AWS::SecretsManager::Secret")
MOTO_SECRET = {"Database.MasterUserSecret.SecretArn": "arn:aws:secretsmanager:us-east-1:111122223333:secret:rds!db-moto"}


def test_exports(outputs):
    out = outputs("data")
    for key, export in EXPORTS.items():
        assert key in out, f"add Output {key}"
        assert out[key].get("Export", {}).get("Name") == f"shortly-{export}", f"{key}: Export Name !Sub '${{Prefix}}-{export}'"
        assert str(out[key].get("Value")) == VALUES[key], \
            f"{key}: Value should render as {VALUES[key]} ({'!GetAtt ' + VALUES[key] if '.' in VALUES[key] else '!Ref ' + VALUES[key]})"


def test_lint_clean(lint_errors):
    errors = lint_errors("data")
    assert errors == [], "cfn-lint errors: " + "; ".join(f"line {e['line']} {e['rule']} {e['message']}" for e in errors)


@pytest.mark.parametrize("env", ["prod", "lab"])
def test_deploys_in_moto(moto_stacks, env):
    import boto3

    for layer in ("iam", "network"):
        status = moto_stacks(layer, Env=env)
        assert status == "CREATE_COMPLETE", f"the {layer} stack ended as {status}; fix infra/{layer}.yaml"
    status = moto_stacks("data", skip_types=MOTO_SKIP, getatt_values=MOTO_SECRET, Env=env)
    assert status == "CREATE_COMPLETE", f"the data stack ended as {status}; fix infra/data.yaml (moto cannot create the cache, so that part is only checked on the template)"

    rds = boto3.client("rds", region_name="us-east-1")
    instances = rds.describe_db_instances()["DBInstances"]
    assert len(instances) == 1, f"expected one database instance, found {len(instances)}"
    db = instances[0]
    assert db["Engine"] == "postgres", f"the database engine is {db['Engine']!r}; use postgres"
    assert db["StorageEncrypted"] is True, "the database should be encrypted (StorageEncrypted: true)"
    assert db["MultiAZ"] is (env == "prod"), f"{env}: MultiAZ should be {env == 'prod'}"
    assert db["Endpoint"]["Port"] == 5432, f"the database port is {db['Endpoint']['Port']}; set Port: 5432"

    ec2 = boto3.client("ec2", region_name="us-east-1")
    subnet_ids = {s["SubnetIdentifier"] for s in db["DBSubnetGroup"]["Subnets"]}
    assert len(subnet_ids) == 2, f"the DB subnet group should hold the two data subnets, found {len(subnet_ids)}"
    names = {t["Value"] for s in ec2.describe_subnets(SubnetIds=sorted(subnet_ids))["Subnets"] for t in s.get("Tags", []) if t["Key"] == "Name"}
    assert names and all("data" in n for n in names), f"the DB subnet group should use the data subnets, found {sorted(names)}"

    ddb = boto3.client("dynamodb", region_name="us-east-1")
    clicks = ddb.describe_table(TableName="shortly-clicks-daily")["Table"]
    assert clicks["BillingModeSummary"]["BillingMode"] == "PAY_PER_REQUEST", "the clicks table should be PAY_PER_REQUEST"
    assert {(k["AttributeName"], k["KeyType"]) for k in clicks["KeySchema"]} == {("code", "HASH"), ("day", "RANGE")}, "the clicks table keys are code (HASH) and day (RANGE)"

    cf = boto3.client("cloudformation", region_name="us-east-1")
    exported = {o["OutputKey"] for o in cf.describe_stacks(StackName="shortly-data")["Stacks"][0].get("Outputs", [])}
    assert {"DbEndpointAddress", "DbPort", "ClicksTableName", "ClicksTableArn"} <= exported, f"the data stack is missing Outputs, found {sorted(exported)}"

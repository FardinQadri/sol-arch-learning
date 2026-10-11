"""M05.5 — the DynamoDB click counts, and the README's case for three stores with a computed cost."""
import re


def table(resources, **params):
    res = resources("data", **params)
    assert res.get("ClicksTable", {}).get("Type") == "AWS::DynamoDB::Table", "add ClicksTable (AWS::DynamoDB::Table) to infra/data.yaml"
    return res["ClicksTable"]["Properties"]


def test_name_and_billing(resources):
    p = table(resources)
    assert p.get("TableName") == "shortly-clicks-daily", \
        f"TableName is {p.get('TableName')!r}; use !Sub '${{Prefix}}-clicks-daily' (the M01 app and consumer policies already name this table)"
    assert p.get("BillingMode") == "PAY_PER_REQUEST", \
        f"BillingMode is {p.get('BillingMode')!r}; use PAY_PER_REQUEST. Click traffic is spiky and unknown; on-demand pays per request and needs no capacity planning (provisioned capacity bills every hour, used or not)"
    assert "ProvisionedThroughput" not in p, "remove ProvisionedThroughput: on-demand tables have no provisioned capacity"


def test_keys(resources):
    p = table(resources)
    attrs = {a["AttributeName"]: a["AttributeType"] for a in p.get("AttributeDefinitions") or []}
    assert attrs == {"code": "S", "day": "S"}, f"AttributeDefinitions should be code (S) and day (S), found {attrs}"
    keys = {k["AttributeName"]: k["KeyType"] for k in p.get("KeySchema") or []}
    assert keys == {"code": "HASH", "day": "RANGE"}, \
        f"KeySchema should be code HASH (partition key: one short code's counters live together) and day RANGE (sort key: one item per code per day, queried by date range), found {keys}"


def test_point_in_time_recovery(resources):
    spec = table(resources).get("PointInTimeRecoverySpecification") or {}
    assert spec.get("PointInTimeRecoveryEnabled") is True, \
        "add PointInTimeRecoverySpecification: {PointInTimeRecoveryEnabled: true}. It lets you restore the table to any second in the last 35 days (an accidental bulk delete or a bad deploy)"


def test_ttl_on_expires_at(resources):
    ttl = table(resources).get("TimeToLiveSpecification") or {}
    assert ttl.get("AttributeName") == "expires_at" and ttl.get("Enabled") is True, \
        "add TimeToLiveSpecification: {AttributeName: expires_at, Enabled: true}. DynamoDB deletes old daily counters for free once expires_at (epoch seconds) has passed"


def test_deletion_protection_follows_environment(resources):
    assert table(resources, Env="prod").get("DeletionProtectionEnabled") is True, "prod: DeletionProtectionEnabled: true (!If [IsProd, true, false])"
    assert table(resources, Env="lab").get("DeletionProtectionEnabled") is False, "lab: DeletionProtectionEnabled: false so lab can be torn down"


def test_the_table_survives_the_stack(template):
    res = template("data")["Resources"].get("ClicksTable", {})
    assert res.get("DeletionPolicy") == "Retain", "ClicksTable: add DeletionPolicy: Retain — click history must outlive a stack deletion"
    assert res.get("UpdateReplacePolicy") == "Retain", "ClicksTable: add UpdateReplacePolicy: Retain too"


def section(repo):
    readme = repo / "README.md"
    assert readme.exists(), "README.md is missing"
    text = readme.read_text(encoding="utf-8")
    match = re.search(r"^## Data tier\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert match, "add a '## Data tier' section to README.md"
    return match.group(1)


def test_readme_explains_the_three_stores(repo):
    body = section(repo).lower()
    for words, why in ((("postgresql", "postgres"), "PostgreSQL (links and users: relational, transactions)"),
                       (("valkey", "redis"), "Valkey or Redis (hot redirects: sub-millisecond cached reads)"),
                       (("dynamodb",), "DynamoDB (click counts: key-value, write-heavy)")):
        assert any(w in body for w in words), f"the Data tier section should explain {why}"


def test_readme_states_the_monthly_cost(repo, dynamo):
    cost = dynamo.monthly_cost_on_demand(60_000_000, 30_000_000, 1)
    figure = f"{cost:.2f}"
    assert re.search(rf"(?<![\d.]){re.escape(figure)}(?!\d)", section(repo)), \
        (f"the Data tier section should state the clicks table's monthly on-demand cost: {figure} USD for 30 million writes of 0.5 KB and 60 million eventually consistent reads of 1 KB. "
         "Work it out: a 0.5 KB write rounds up to 1 write unit, a 1 KB eventually consistent read is 0.5 read unit; then use the price per million units (check your sums with awslib dynamo.monthly_cost_on_demand)")

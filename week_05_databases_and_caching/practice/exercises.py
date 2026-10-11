"""
Week 05 drills — databases and caching
======================================
Run:    python practice/exercises.py          every drill
        python practice/exercises.py 4        drill 4 only
Drills 01–02 are pure Python models of DynamoDB capacity: how many read and write units one request
costs, and when provisioned capacity beats paying per request. Drill 03 designs one DynamoDB table
that answers three questions, drill 04 makes concurrent updates safe, drill 05 protects a table.
Drill 06 simulates a cache, drill 07 does connection maths for RDS Proxy. Drill 08 builds a
fault-tolerant RDS database with boto3. Drills 09–10 are decide drills. Everything runs against moto
(a fake AWS) or plain Python, so nothing here can touch a real account or cost money.
The course's own versions of drills 01, 02, 06 and 07 (_harness/awslib/dynamo.py, caching.py and
dbmath.py) are their answer key — don't open them until you are done.
Note: moto stores what you send and enforces DynamoDB conditions and transactions, but it never
expires items by TTL, never throttles, reports made-up consumed capacity, and has no Multi-AZ
standby. So the drills read your settings back and the models show the behaviour.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from boto3.dynamodb.conditions import Key  # noqa: E402,F401  (for drill 03)
from botocore.exceptions import ClientError  # noqa: E402,F401  (for drills 04 and 05)
from _harness.awsdrill import Drill, run  # noqa: E402
from _harness.awslib import prices  # noqa: E402

PRICES = prices.section("database")


# ── Exercise 01 ★: Read units and write units ────────────────────────
"""
DynamoDB meters every request in units, and the unit size is fixed:
    one read unit  = one read of an item up to 4 KB, strongly consistent
    one write unit = one write of an item up to 1 KB
The item size is ROUNDED UP to the next whole block (4 KB for reads, 1 KB for writes) before you
multiply. A 4.1 KB item reads as 8 KB; a 0.5 KB item still writes as 1 KB.
Multipliers:
    reads   strongly consistent 1 · eventually consistent 0.5 (the default, half price) · transactional 2
    writes  standard 1 · transactional 2
The biggest item DynamoDB accepts is 400 KB. Item size 0 or less, or above 400 KB, is a ValueError.
read_units(item_kb, consistency="eventual") -> float
    consistency is "eventual", "strong" or "transactional"; anything else is a ValueError.
write_units(item_kb, transactional=False) -> int
provisioned_capacity(reads_per_second, writes_per_second, item_kb, consistency="eventual",
                     transactional_writes=False) -> (rcu, wcu)
    The capacity to provision: reads per second x read units, writes per second x write units, each
    rounded UP to a whole number (you cannot provision 1.5 units). Negative rates are a ValueError.
Examples:
    read_units(4.1, "strong") == 2.0        read_units(8) == 1.0         write_units(1.5) == 2
    write_units(1.5, transactional=True) == 4       provisioned_capacity(100, 50, 6) == (100, 300)
Why? Rounding is where bills surprise people. Cutting a 1.1 KB item to 1.0 KB halves the write cost,
and reading eventually consistent halves the read cost. The exam asks you to do exactly this sum.
Hint: math.ceil(item_kb / 4) is the number of 4 KB blocks.
"""
def read_units(item_kb, consistency="eventual"):
    raise NotImplementedError  # YOUR CODE


def write_units(item_kb, transactional=False):
    raise NotImplementedError  # YOUR CODE


def provisioned_capacity(reads_per_second, writes_per_second, item_kb, consistency="eventual",
                         transactional_writes=False):
    raise NotImplementedError  # YOUR CODE


class Ex01(Drill):
    """Read units and write units ★"""
    tasks = ("3.3",)

    def test_reads_round_up_to_4_kb(self):
        cases = {1: 1.0, 3: 1.0, 4: 1.0, 4.1: 2.0, 8: 2.0, 8.5: 3.0, 400: 100.0}
        for kb, want in cases.items():
            with self.subTest(item_kb=kb):
                self.assertEqual(read_units(kb, "strong"), want, f"{kb} KB strongly consistent: round {kb}/4 UP")

    def test_consistency_factors(self):
        self.assertEqual(read_units(4, "strong"), 1.0)
        self.assertEqual(read_units(4, "eventual"), 0.5, "eventually consistent reads cost half")
        self.assertEqual(read_units(4, "transactional"), 2.0, "transactional reads cost double")
        self.assertEqual(read_units(8), 1.0, "the default is eventually consistent")
        self.assertEqual(read_units(0.1), 0.5, "even a tiny item is one 4 KB block")

    def test_writes_round_up_to_1_kb(self):
        cases = {0.1: 1, 0.5: 1, 1: 1, 1.01: 2, 1.5: 2, 3: 3, 400: 400}
        for kb, want in cases.items():
            with self.subTest(item_kb=kb):
                self.assertEqual(write_units(kb), want, f"{kb} KB write: round {kb}/1 UP")

    def test_transactional_writes_cost_double(self):
        self.assertEqual(write_units(1, transactional=True), 2)
        self.assertEqual(write_units(1.5, transactional=True), 4)
        self.assertEqual(write_units(3, transactional=True), 6)

    def test_item_size_limits(self):
        for bad in (0, -1, 400.1, 500):
            with self.subTest(item_kb=bad):
                with self.assertRaises(ValueError):
                    read_units(bad)
                with self.assertRaises(ValueError):
                    write_units(bad)
        read_units(400)
        write_units(400)

    def test_unknown_consistency(self):
        with self.assertRaises(ValueError):
            read_units(4, "sometimes")

    def test_a_worked_workload(self):
        # 100 reads/s and 50 writes/s of 6 KB items: 6 KB is 2 blocks of 4 KB (eventual: 1 unit) and 6 write units.
        self.assertEqual(provisioned_capacity(100, 50, 6), (100, 300))
        # Strongly consistent reads of the same items cost double: 2 units each. Transactional writes: 12 units.
        self.assertEqual(provisioned_capacity(80, 10, 6, "strong"), (160, 60))
        self.assertEqual(provisioned_capacity(80, 10, 6, "strong", transactional_writes=True), (160, 120))

    def test_capacity_rounds_up_to_whole_units(self):
        # 3 eventual reads/s of 1 KB = 1.5 units: you must provision 2.
        self.assertEqual(provisioned_capacity(3, 0, 1), (2, 0))
        self.assertEqual(provisioned_capacity(0, 0, 1), (0, 0))

    def test_negative_rates(self):
        with self.assertRaises(ValueError):
            provisioned_capacity(-1, 5, 1)
        with self.assertRaises(ValueError):
            provisioned_capacity(1, -5, 1)


# ── Exercise 02 ★: On-demand or provisioned? ─────────────────────────
"""
DynamoDB has two ways to pay:
    on-demand    you pay per request: price per million x units used. Nothing when idle.
    provisioned  you choose read and write units per second and pay for EVERY hour of them, whether
                 you use them or not.
PRICES (from prices.toml, illustrative) holds the four numbers you need:
    dynamodb_on_demand_per_million_writes, dynamodb_on_demand_per_million_reads (per million units),
    dynamodb_wcu_hour, dynamodb_rcu_hour (per provisioned unit per hour).
Write three functions. Reuse your read_units / write_units from drill 1.
monthly_cost_on_demand(reads_per_month, writes_per_month, item_kb, consistency="eventual",
                       transactional_writes=False, price=PRICES) -> float
    (reads x read_units / 1,000,000 x read price) + (writes x write_units / 1,000,000 x write price),
    rounded to 4 decimal places. Storage is not included. Negative counts are a ValueError.
monthly_cost_provisioned(rcu, wcu, hours=730, price=PRICES) -> float
    hours x (rcu x rcu price + wcu x wcu price), rounded to 4 decimal places. Negative inputs are a
    ValueError. A month is 730 hours.
break_even_utilisation(price=PRICES) -> {"writes": f, "reads": f}
    The average fraction of provisioned capacity you must actually use for provisioned to cost the
    same as on-demand. One unit-hour of provisioned capacity can serve 3,600 units of requests
    (one per second). On-demand would charge 3,600 x (price per million / 1,000,000) for the same.
    So utilisation = unit-hour price / that amount. Round each to 4 decimal places.
Examples (with the default prices):
    monthly_cost_on_demand(1_000_000, 1_000_000, 1) == 0.6875
    monthly_cost_provisioned(100, 100) == 56.94
    break_even_utilisation() == {"writes": 0.2889, "reads": 0.2889}
Why? Provisioned is cheaper only for steady, busy tables: below about 29% average use you pay for
idle capacity. A spiky or unpredictable table belongs on on-demand (AWS now makes it the default for
most workloads). Reserved capacity can cut provisioned further, but only if the load is steady.
Hint: round(x, 4). The two on-demand prices differ, so reads and writes get their own sum.
"""
def monthly_cost_on_demand(reads_per_month, writes_per_month, item_kb, consistency="eventual",
                           transactional_writes=False, price=PRICES):
    raise NotImplementedError  # YOUR CODE


def monthly_cost_provisioned(rcu, wcu, hours=730, price=PRICES):
    raise NotImplementedError  # YOUR CODE


def break_even_utilisation(price=PRICES):
    raise NotImplementedError  # YOUR CODE


class Ex02(Drill):
    """On-demand or provisioned? ★"""
    tasks = ("4.3",)

    SECONDS_PER_MONTH = 730 * 3600

    def test_on_demand_cost(self):
        self.assertEqual(monthly_cost_on_demand(1_000_000, 1_000_000, 1), 0.6875)
        self.assertEqual(monthly_cost_on_demand(0, 2_000_000, 1), 1.25)
        self.assertEqual(monthly_cost_on_demand(2_000_000, 0, 1, "strong"), 0.25)

    def test_on_demand_uses_units_not_requests(self):
        # 1 million writes of 2.5 KB are 3 write units each, so 3 million units.
        self.assertEqual(monthly_cost_on_demand(0, 1_000_000, 2.5), 1.875)
        self.assertEqual(monthly_cost_on_demand(0, 1_000_000, 2.5, transactional_writes=True), 3.75)
        self.assertEqual(monthly_cost_on_demand(1_000_000, 0, 6, "transactional"), 0.5)

    def test_provisioned_cost_is_for_every_hour(self):
        self.assertEqual(monthly_cost_provisioned(100, 100), 56.94)
        self.assertEqual(monthly_cost_provisioned(0, 0), 0.0)
        self.assertEqual(monthly_cost_provisioned(100, 100, hours=365), 28.47)

    def test_provisioned_cost_does_not_depend_on_use(self):
        # The function has no 'requests' input at all: idle or busy, the bill is the same.
        self.assertEqual(monthly_cost_provisioned(25, 100), 49.8225)
        self.assertEqual(monthly_cost_provisioned(25, 100, hours=730), 49.8225)

    def test_a_spiky_low_traffic_table_is_cheaper_on_demand(self):
        # Busy for one hour a month: 100 writes/s and 50 reads/s of 1 KB items, idle the rest of the time.
        writes, reads = 100 * 3600, 50 * 3600
        on_demand = monthly_cost_on_demand(reads, writes, 1)
        rcu, wcu = provisioned_capacity(50, 100, 1)   # provisioned must be sized for the peak
        provisioned = monthly_cost_provisioned(rcu, wcu)
        self.assertAlmostEqual(on_demand, 0.2363, places=3)
        self.assertAlmostEqual(provisioned, 49.8225, places=3)
        self.assertLess(on_demand, provisioned, "idle capacity is the cost of provisioned mode")

    def test_a_steady_busy_table_is_cheaper_provisioned(self):
        # 100 writes/s and 200 reads/s of 1 KB items, all month long.
        writes, reads = 100 * self.SECONDS_PER_MONTH, 200 * self.SECONDS_PER_MONTH
        on_demand = monthly_cost_on_demand(reads, writes, 1)
        rcu, wcu = provisioned_capacity(200, 100, 1)
        provisioned = monthly_cost_provisioned(rcu, wcu)
        self.assertAlmostEqual(on_demand, 197.1, places=2)
        self.assertAlmostEqual(provisioned, 56.94, places=2)
        self.assertLess(provisioned, on_demand, "full use of provisioned capacity beats paying per request")

    def test_break_even(self):
        self.assertEqual(break_even_utilisation(), {"writes": 0.2889, "reads": 0.2889})

    def test_custom_prices_are_honoured(self):
        custom = {"dynamodb_on_demand_per_million_writes": 1.0, "dynamodb_on_demand_per_million_reads": 0.5,
                  "dynamodb_wcu_hour": 0.001, "dynamodb_rcu_hour": 0.0005}
        self.assertEqual(monthly_cost_on_demand(2_000_000, 1_000_000, 1, price=custom), 1.5)
        self.assertEqual(monthly_cost_provisioned(10, 10, hours=100, price=custom), 1.5)
        self.assertEqual(break_even_utilisation(custom), {"writes": 0.2778, "reads": 0.2778})

    def test_negative_inputs(self):
        with self.assertRaises(ValueError):
            monthly_cost_on_demand(-1, 0, 1)
        with self.assertRaises(ValueError):
            monthly_cost_on_demand(0, -1, 1)
        with self.assertRaises(ValueError):
            monthly_cost_provisioned(-1, 0)
        with self.assertRaises(ValueError):
            monthly_cost_provisioned(1, 1, hours=-5)


# ── Exercise 03 ★: One table, every question ─────────────────────────
"""
DynamoDB is fast because every question must start from a partition key: Query reads ONE partition,
in sort-key order. Scan reads everything and bills for all of it. So you design the table around the
questions, and "single-table design" puts different kinds of items in one table with generic key names.
Shortly's three questions:
    1. Get a link by its code.
    2. All clicks of one link between two days, in date order.
    3. All links of one owner, newest first.
Design ONE table that answers all three with Query (never Scan).
TABLE = {"KeySchema": [...], "AttributeDefinitions": [...], "GlobalSecondaryIndexes": [one index]}
    Pick the key names yourself ("pk" and "sk" are conventional). The table has a partition key and a
    sort key. It has exactly ONE global secondary index (GSI) and no local secondary index. A GSI is a
    second copy of the data under a different partition key: that is how you ask question 3, because the
    base table is keyed by link and the question is about owners. Each index needs IndexName, KeySchema
    and a Projection (use {"ProjectionType": "ALL"}). AttributeDefinitions lists every attribute used in
    any key, once, with type "S" (string) — and no others.
link_item(code, url, owner, created) -> dict
    The item to store for a link. `created` is an ISO time like "2026-10-12T09:30:00Z". Put the table's
    key attributes in it, plus "code", "url", "owner", "created", and the GSI key attributes.
click_item(code, day, count) -> dict
    The item for the clicks of one link on one day (`day` is "2026-10-12"). Same table, same partition
    as the link, so one Query can fetch them in order. Include "day" and "count".
get_link(table, code) -> dict or None
    The link item's "code", "url" and "owner" as a dict, or None if there is no such link.
clicks_between(table, code, first_day, last_day) -> list of (day, count)
    Clicks for the link from first_day to last_day INCLUDING both ends, oldest first. One Query.
links_of_owner(table, owner) -> list of codes
    Every link of that owner, newest `created` first. One Query on the GSI.
`table` is a boto3 Table resource (items are plain dicts); `Key` from boto3.dynamodb.conditions is
imported for you. The tests build the table from your TABLE, write items with your builders, and fail
the moment you call Scan.
Why? You cannot join in DynamoDB, so the key design IS the query design. Prefixes such as "LINK#abc"
let different item types share a partition, and an ISO date as a sort key makes between() work.
Hint: Key("pk").eq(...) & Key("sk").between(a, b) and table.query(KeyConditionExpression=..., IndexName=...,
      ScanIndexForward=False). Sort-key conditions on strings compare alphabetically, which is why dates
      are written year-month-day.
"""
TABLE = {
    "KeySchema": [],               # YOUR CODE
    "AttributeDefinitions": [],    # YOUR CODE
    "GlobalSecondaryIndexes": [],  # YOUR CODE (exactly one)
}


def link_item(code, url, owner, created):
    raise NotImplementedError  # YOUR CODE


def click_item(code, day, count):
    raise NotImplementedError  # YOUR CODE


def get_link(table, code):
    raise NotImplementedError  # YOUR CODE


def clicks_between(table, code, first_day, last_day):
    raise NotImplementedError  # YOUR CODE


def links_of_owner(table, owner):
    raise NotImplementedError  # YOUR CODE


class Ex03(Drill):
    """One table, every question ★"""
    tasks = ("3.3",)
    uses_aws = True

    def make(self):
        """Create the table from TABLE, load sample data, and forbid Scan."""
        ddb = self.resource("dynamodb")
        table = ddb.create_table(TableName="shortly-single", BillingMode="PAY_PER_REQUEST", **TABLE)

        def no_scan(**kwargs):
            raise AssertionError("you called Scan, which reads the whole table; answer with Query")

        table.meta.client.meta.events.register("before-parameter-build.dynamodb.Scan", no_scan)
        links = [("abc", "https://example.com/a", "alice", "2026-10-01T08:00:00Z"),
                 ("def", "https://example.com/d", "alice", "2026-10-03T08:00:00Z"),
                 ("ghi", "https://example.com/g", "alice", "2026-10-02T08:00:00Z"),
                 ("xyz", "https://example.com/x", "bob", "2026-10-04T08:00:00Z")]
        for code, url, owner, created in links:
            table.put_item(Item=link_item(code, url, owner, created))
        for day in range(8, 15):
            table.put_item(Item=click_item("abc", f"2026-10-{day:02d}", day * 10))
        table.put_item(Item=click_item("xyz", "2026-10-10", 5))
        return table

    def test_table_shape(self):
        self.assertEqual(len(TABLE["KeySchema"]), 2, "a partition key and a sort key")
        self.assertEqual({k["KeyType"] for k in TABLE["KeySchema"]}, {"HASH", "RANGE"})
        self.assertEqual(len(TABLE["GlobalSecondaryIndexes"]), 1, "exactly one GSI")
        self.assertNotIn("LocalSecondaryIndexes", TABLE, "no local secondary index")
        gsi = TABLE["GlobalSecondaryIndexes"][0]
        self.assertTrue({"IndexName", "KeySchema", "Projection"} <= set(gsi), "an index needs a name, keys and a projection")
        used = {k["AttributeName"] for k in TABLE["KeySchema"]} | {k["AttributeName"] for k in gsi["KeySchema"]}
        defined = {a["AttributeName"] for a in TABLE["AttributeDefinitions"]}
        self.assertEqual(defined, used, "AttributeDefinitions lists exactly the key attributes, once each")

    def test_builders_set_every_key_attribute(self):
        self.assertTrue(TABLE["KeySchema"] and TABLE["GlobalSecondaryIndexes"], "define TABLE first")
        keys = {k["AttributeName"] for k in TABLE["KeySchema"]}
        index_keys = {k["AttributeName"] for k in TABLE["GlobalSecondaryIndexes"][0]["KeySchema"]}
        link = link_item("abc", "https://example.com/a", "alice", "2026-10-01T08:00:00Z")
        self.assertTrue((keys | index_keys) <= set(link), "a link item needs the table keys and the index keys")
        click = click_item("abc", "2026-10-08", 3)
        self.assertTrue(keys <= set(click), "a click item needs the table keys")
        self.assertEqual((click["day"], click["count"]), ("2026-10-08", 3))

    def test_get_link_by_code(self):
        table = self.make()
        got = get_link(table, "abc")
        self.assertEqual((got["code"], got["url"], got["owner"]), ("abc", "https://example.com/a", "alice"))
        self.assertIsNone(get_link(table, "nope"))

    def test_clicks_between_dates_in_order(self):
        table = self.make()
        self.assertEqual(clicks_between(table, "abc", "2026-10-10", "2026-10-12"),
                         [("2026-10-10", 100), ("2026-10-11", 110), ("2026-10-12", 120)])

    def test_clicks_bounds_are_inclusive_and_per_link(self):
        table = self.make()
        self.assertEqual(clicks_between(table, "abc", "2026-10-08", "2026-10-08"), [("2026-10-08", 80)])
        self.assertEqual(clicks_between(table, "xyz", "2026-10-01", "2026-10-31"), [("2026-10-10", 5)],
                         "another link's clicks must not leak in, and a link's own item is not a click")
        self.assertEqual(len(clicks_between(table, "abc", "2026-10-01", "2026-10-31")), 7)
        self.assertEqual(clicks_between(table, "abc", "2026-11-01", "2026-11-30"), [])

    def test_links_of_owner_newest_first(self):
        table = self.make()
        self.assertEqual(links_of_owner(table, "alice"), ["def", "ghi", "abc"])
        self.assertEqual(links_of_owner(table, "bob"), ["xyz"])
        self.assertEqual(links_of_owner(table, "carol"), [])


# ── Exercise 04: Never lose an update ────────────────────────────────
"""
Two people open the same link, both change it, both save. Without protection the second save silently
overwrites the first: a LOST UPDATE. DynamoDB gives you conditional writes: a ConditionExpression is
checked and the write happens in one atomic step, so the check cannot be beaten by a race.
Optimistic locking uses a `version` number: read the item (and its version), change it, and write it back
only IF the version is still what you read. If somebody else got there first, the condition fails and
you must re-read and try again. This table is already created for you (TABLE_NAME, key "pk"):
    link   {"pk": "LINK#<code>", "url": ..., "owner": ..., "version": 1}
    owner  {"pk": "OWNER#<name>", "link_count": 3}
class StaleVersion(Exception)    Define it: raised when the version you expected is out of date.
rename_link(table, code, new_url, expected_version) -> int
    `table` is a Table resource. Set the link's url and raise its version by one, only if the stored
    version equals expected_version. Return the new version. If the condition fails (ConditionalCheck-
    FailedException) raise StaleVersion; re-raise any other error. A link that does not exist counts as
    stale too: your call must NOT create it.
transfer_owner(client, code, old_owner, new_owner)
    `client` is a low-level dynamodb client (typed values like {"S": "alice"}). Move a link to a new owner
    and fix both owners' link_count, in ONE transact_write_items call:
      - the link: set owner to new_owner and raise version by one, only if its owner is old_owner
      - OWNER#old_owner: link_count down by one
      - OWNER#new_owner: link_count up by one (the owner item may not exist yet; ADD creates it)
    A transaction is all-or-nothing: if the link is not owned by old_owner, NOTHING changes, and the
    TransactionCanceledException reaches the caller. old_owner equal to new_owner is a ValueError.
Why? "Read, change, write" is a race. A condition makes the database referee it. A transaction makes
several items change together or not at all, so a counter can never disagree with the data it counts.
Hint: update_item(Key=..., UpdateExpression="SET #u = :u, #v = :next", ConditionExpression="#v = :expected",
      ExpressionAttributeNames=..., ExpressionAttributeValues=...) — url and version are easier through
      #name placeholders. ADD link_count :one both creates and increments a number. In a transaction each
      item in TransactItems is {"Update": {"TableName": ..., "Key": ..., ...}}.
"""
TABLE_NAME = "shortly"
StaleVersion = None  # YOUR CODE: define an Exception subclass called StaleVersion


def rename_link(table, code, new_url, expected_version):
    raise NotImplementedError  # YOUR CODE


def transfer_owner(client, code, old_owner, new_owner):
    raise NotImplementedError  # YOUR CODE


class Ex04(Drill):
    """Never lose an update"""
    tasks = ("3.3", "2.2")
    uses_aws = True

    def make(self):
        ddb = self.client("dynamodb")
        ddb.create_table(TableName=TABLE_NAME, BillingMode="PAY_PER_REQUEST",
                         KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}],
                         AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"}])
        table = self.resource("dynamodb").Table(TABLE_NAME)
        table.put_item(Item={"pk": "LINK#abc", "url": "https://example.com/old", "owner": "alice", "version": 1})
        table.put_item(Item={"pk": "OWNER#alice", "link_count": 3})
        return ddb, table

    def link(self, table):
        return table.get_item(Key={"pk": "LINK#abc"}, ConsistentRead=True)["Item"]

    def count(self, table, owner):
        item = table.get_item(Key={"pk": f"OWNER#{owner}"}, ConsistentRead=True).get("Item")
        return None if item is None else int(item["link_count"])

    def test_rename_bumps_the_version(self):
        _, table = self.make()
        self.assertEqual(rename_link(table, "abc", "https://example.com/new", 1), 2)
        item = self.link(table)
        self.assertEqual((item["url"], int(item["version"])), ("https://example.com/new", 2))
        self.assertEqual(item["owner"], "alice", "other attributes are untouched")
        self.assertEqual(rename_link(table, "abc", "https://example.com/newer", 2), 3)

    def test_two_readers_one_wins(self):
        _, table = self.make()
        seen_by_a = seen_by_b = int(self.link(table)["version"])      # both read version 1
        rename_link(table, "abc", "https://example.com/from-a", seen_by_a)
        with self.assertRaises(StaleVersion, msg="B read the old version, so B's write must be refused"):
            rename_link(table, "abc", "https://example.com/from-b", seen_by_b)
        item = self.link(table)
        self.assertEqual(item["url"], "https://example.com/from-a", "A's update must not be overwritten")
        self.assertEqual(int(item["version"]), 2)

    def test_a_missing_link_is_stale_and_not_created(self):
        _, table = self.make()
        with self.assertRaises(StaleVersion):
            rename_link(table, "ghost", "https://example.com/x", 1)
        self.assertNotIn("Item", table.get_item(Key={"pk": "LINK#ghost"}),
                         "update_item creates missing items unless your condition stops it")

    def test_stale_version_is_an_exception_class(self):
        self.assertTrue(isinstance(StaleVersion, type) and issubclass(StaleVersion, Exception))

    def test_transfer_moves_the_link_and_both_counters(self):
        ddb, table = self.make()
        transfer_owner(ddb, "abc", "alice", "bob")
        item = self.link(table)
        self.assertEqual((item["owner"], int(item["version"])), ("bob", 2))
        self.assertEqual(self.count(table, "alice"), 2)
        self.assertEqual(self.count(table, "bob"), 1, "a first link creates the owner's counter")

    def test_a_failed_transfer_changes_nothing(self):
        ddb, table = self.make()
        with self.assertClientError("TransactionCanceledException"):
            transfer_owner(ddb, "abc", "carol", "bob")      # the link is alice's, not carol's
        item = self.link(table)
        self.assertEqual((item["owner"], int(item["version"])), ("alice", 1))
        self.assertEqual(self.count(table, "alice"), 3, "counters must not move when the transaction fails")
        self.assertIsNone(self.count(table, "bob"))
        self.assertIsNone(self.count(table, "carol"))

    def test_repeating_a_transfer_is_refused(self):
        ddb, table = self.make()
        transfer_owner(ddb, "abc", "alice", "bob")
        with self.assertClientError("TransactionCanceledException"):
            transfer_owner(ddb, "abc", "alice", "bob")      # alice no longer owns it
        self.assertEqual((self.count(table, "alice"), self.count(table, "bob")), (2, 1))

    def test_same_owner_is_a_value_error(self):
        ddb, _ = self.make()
        with self.assertRaises(ValueError):
            transfer_owner(ddb, "abc", "alice", "alice")


# ── Exercise 05: Keep it tidy, keep it safe ──────────────────────────
"""
Three protections every real table wants, and each is one API call.
protect_table(client, table_name, ttl_attribute) -> str
    `client` is a low-level dynamodb client. Do all three, then return the backup's ARN:
      1. TTL (time to live) on the attribute `ttl_attribute`: update_time_to_live. The attribute holds a
         Unix time in seconds (a Number). DynamoDB deletes items whose time has passed, in the
         background, for free: it does not use write capacity.
      2. Point-in-time recovery (PITR) on: update_continuous_backups. You can then restore the table to
         any second in the last 35 days (the default; you may choose 1 to 35).
      3. An on-demand backup named "<table_name>-baseline": create_backup. It is kept until you delete it.
What each one will NOT do:
  - TTL is not a timer. Expired items are deleted "within a few days" of expiring, and until then they
    can still be read. Code that must hide expired items has to filter on the time itself.
    (moto never deletes anything by TTL, so no test here waits for it.)
  - A restore never overwrites: both PITR and backup restores create a NEW table. You then switch your
    application to it (or copy the data back).
  - Turning protections on later does not give you history from before: PITR starts when you enable it.
Why? Backups and recovery are the standard answer to "someone deleted or corrupted the data", and TTL is
the standard answer to "sessions and temporary rows pile up forever".
Hint: update_time_to_live(TableName=..., TimeToLiveSpecification={"Enabled": True, "AttributeName": ...});
      update_continuous_backups(TableName=..., PointInTimeRecoverySpecification={"PointInTimeRecoveryEnabled": True});
      create_backup(TableName=..., BackupName=...)["BackupDetails"]["BackupArn"].
"""
def protect_table(client, table_name, ttl_attribute):
    raise NotImplementedError  # YOUR CODE


class Ex05(Drill):
    """Keep it tidy, keep it safe"""
    tasks = ("3.3", "2.2")
    uses_aws = True

    def make(self, name="sessions"):
        ddb = self.client("dynamodb")
        ddb.create_table(TableName=name, BillingMode="PAY_PER_REQUEST",
                         KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}],
                         AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"}])
        return ddb

    def test_ttl_is_enabled_on_the_attribute(self):
        ddb = self.make()
        protect_table(ddb, "sessions", "expires_at")
        ttl = ddb.describe_time_to_live(TableName="sessions")["TimeToLiveDescription"]
        self.assertIn(ttl["TimeToLiveStatus"], ("ENABLED", "ENABLING"))
        self.assertEqual(ttl.get("AttributeName"), "expires_at")

    def test_point_in_time_recovery_is_on(self):
        ddb = self.make()
        before = ddb.describe_continuous_backups(TableName="sessions")["ContinuousBackupsDescription"]
        self.assertEqual(before["PointInTimeRecoveryDescription"]["PointInTimeRecoveryStatus"], "DISABLED")
        protect_table(ddb, "sessions", "expires_at")
        after = ddb.describe_continuous_backups(TableName="sessions")["ContinuousBackupsDescription"]
        self.assertEqual(after["PointInTimeRecoveryDescription"]["PointInTimeRecoveryStatus"], "ENABLED",
                         "PITR is what lets you undo a bad write from an hour ago")

    def test_baseline_backup_exists_and_its_arn_is_returned(self):
        ddb = self.make()
        arn = protect_table(ddb, "sessions", "expires_at")
        backups = ddb.list_backups(TableName="sessions")["BackupSummaries"]
        self.assertEqual([b["BackupName"] for b in backups], ["sessions-baseline"])
        self.assertEqual(arn, backups[0]["BackupArn"])
        self.assertIn("arn:aws:dynamodb", arn)

    def test_works_for_any_table_name_and_attribute(self):
        ddb = self.make("orders")
        protect_table(ddb, "orders", "delete_after")
        self.assertEqual(ddb.describe_time_to_live(TableName="orders")["TimeToLiveDescription"]["AttributeName"], "delete_after")
        self.assertEqual(ddb.list_backups(TableName="orders")["BackupSummaries"][0]["BackupName"], "orders-baseline")

    def test_a_restore_creates_a_new_table(self):
        ddb = self.make()
        ddb.put_item(TableName="sessions", Item={"pk": {"S": "s1"}})
        arn = protect_table(ddb, "sessions", "expires_at")
        ddb.restore_table_from_backup(TargetTableName="sessions-restored", BackupArn=arn)
        names = ddb.list_tables()["TableNames"]
        self.assertIn("sessions", names)
        self.assertIn("sessions-restored", names, "a restore makes a NEW table; it never overwrites the old one")
        self.assertEqual(ddb.get_item(TableName="sessions-restored", Key={"pk": {"S": "s1"}})["Item"]["pk"]["S"], "s1")


# ── Exercise 06 ★: Cache it right ────────────────────────────────────
"""
A cache sits in front of a database and answers repeat reads from memory. Two common ways to fill it:
    "lazy" (lazy loading, cache-aside)  a read looks in the cache first. On a MISS it reads the database and
        stores the value in the cache. A write goes to the database only, so the cached copy can be STALE
        until it expires.
    "write-through"  every write goes to the database AND to the cache, so cached values are never stale.
        The price: you also cache data nobody may ever read, and each write does two things.
A TTL (time to live) on each cached entry limits how long a stale value can survive.
simulate(events, strategy, ttl=None) -> dict
    events is a list of tuples (time_s, "read", key) for a read or (time_s, "write", key, value) for a
    write; times never go backwards. The database starts empty. Replay the events and return these counts:
      "hits"          reads answered from the cache
      "misses"        reads not in the cache (never cached, or expired)
      "db_reads"      database reads (one per miss, even for a key never written, which reads as None)
      "db_writes"     database writes
      "cache_writes"  times a value is put in the cache (on a miss, and on every write-through write)
      "stale_reads"   hits whose cached value differs from the database's current value
    An entry cached at time t expires at t + ttl; a read at exactly t + ttl is a MISS. ttl None = never.
    A read of a key nobody wrote returns None and is still cached (so it can hit next time).
    ValueError for: strategy not "lazy" or "write-through"; op not "read"/"write"; a write without a value;
    an event that is not 3 or 4 long; time going backwards; ttl zero or negative.
Examples:
    simulate([(0, "write", "k", 1), (1, "read", "k")], "write-through")
        -> hits 1, misses 0, db_writes 1, cache_writes 1
    simulate([(0, "read", "k"), (1, "write", "k", 5), (2, "read", "k")], "lazy")
        -> the second read is a hit on the OLD cached value: stale_reads 1
Why? This is the heart of every "improve read performance" question: lazy loading is simple and only
caches what is read, but can serve stale data; write-through keeps the cache fresh but writes more.
AWS recommends combining either with a TTL.
Hint: keep two dicts, db and cache; cache[key] = (value, expires_at). Check expiry with now < expires_at.
"""
def simulate(events, strategy, ttl=None):
    raise NotImplementedError  # YOUR CODE


class Ex06(Drill):
    """Cache it right ★"""
    tasks = ("3.3",)

    def count(self, result, **want):
        got = {k: result[k] for k in want}
        self.assertEqual(got, want)

    def test_cold_start_misses_then_hits(self):
        result = simulate([(0, "write", "k", 1), (1, "read", "k"), (2, "read", "k"), (3, "read", "k")], "lazy")
        self.count(result, hits=2, misses=1, db_reads=1, db_writes=1, cache_writes=1, stale_reads=0)

    def test_every_key_misses_the_first_time(self):
        events = [(0, "write", "a", 1), (0, "write", "b", 2), (1, "read", "a"), (1, "read", "b"), (2, "read", "a")]
        self.count(simulate(events, "lazy"), hits=1, misses=2, db_reads=2)

    def test_reading_a_key_nobody_wrote(self):
        result = simulate([(0, "read", "ghost"), (1, "read", "ghost")], "lazy")
        self.count(result, misses=1, hits=1, db_reads=1, cache_writes=1, stale_reads=0)

    def test_lazy_serves_stale_reads_after_a_write(self):
        events = [(0, "write", "k", 1), (1, "read", "k"), (2, "write", "k", 2), (3, "read", "k"), (4, "read", "k")]
        result = simulate(events, "lazy")
        self.count(result, hits=2, misses=1, stale_reads=2, db_writes=2, cache_writes=1)

    def test_write_through_is_never_stale(self):
        events = [(0, "write", "k", 1), (1, "read", "k"), (2, "write", "k", 2), (3, "read", "k"), (4, "read", "k")]
        result = simulate(events, "write-through")
        self.count(result, hits=3, misses=0, stale_reads=0, db_reads=0, db_writes=2, cache_writes=2)

    def test_write_through_caches_data_nobody_reads(self):
        events = [(0, "write", "a", 1), (1, "write", "b", 2), (2, "write", "c", 3), (3, "read", "a")]
        self.count(simulate(events, "write-through"), cache_writes=3, hits=1)
        self.count(simulate(events, "lazy"), cache_writes=1, hits=0, misses=1)

    def test_ttl_boundary_is_a_miss(self):
        events = [(0, "write", "k", 1), (10, "read", "k"), (70, "read", "k"), (71, "read", "k")]
        result = simulate(events, "lazy", ttl=60)
        # t=10 miss (cached, expires 70) · t=70 exactly at expiry: miss again (expires 130) · t=71 hit
        self.count(result, misses=2, hits=1, db_reads=2)

    def test_just_before_expiry_is_a_hit(self):
        result = simulate([(0, "write", "k", 1), (0, "read", "k"), (59.9, "read", "k")], "lazy", ttl=60)
        self.count(result, hits=1, misses=1)

    def test_ttl_ends_staleness(self):
        events = [(0, "write", "k", 1), (1, "read", "k"), (2, "write", "k", 2), (30, "read", "k"), (61, "read", "k"), (62, "read", "k")]
        result = simulate(events, "lazy", ttl=60)
        # cached at t=1 (expires 61): t=30 hit but stale; t=61 miss reloads value 2; t=62 hit, fresh
        self.count(result, hits=2, misses=2, stale_reads=1, db_reads=2)

    def test_write_through_entries_expire_too(self):
        events = [(0, "write", "k", 1), (59, "read", "k"), (60, "read", "k")]
        result = simulate(events, "write-through", ttl=60)
        self.count(result, hits=1, misses=1, db_reads=1, cache_writes=2)

    def test_empty_event_list(self):
        self.count(simulate([], "lazy"), hits=0, misses=0, db_reads=0, db_writes=0, cache_writes=0, stale_reads=0)

    def test_returns_exactly_the_six_counts(self):
        self.assertEqual(set(simulate([], "lazy")), {"hits", "misses", "db_reads", "db_writes", "cache_writes", "stale_reads"})

    def test_invalid_input(self):
        bad = [
            ([(0, "read", "k")], "write-behind", None),
            ([(0, "delete", "k")], "lazy", None),
            ([(0, "write", "k")], "lazy", None),
            ([(0, "read")], "lazy", None),
            ([(5, "read", "k"), (4, "read", "k")], "lazy", None),
            ([(0, "read", "k")], "lazy", 0),
            ([(0, "read", "k")], "lazy", -5),
        ]
        for events, strategy, ttl in bad:
            with self.subTest(events=events, strategy=strategy, ttl=ttl):
                with self.assertRaises(ValueError):
                    simulate(events, strategy, ttl)


# ── Exercise 07: Too many connections ────────────────────────────────
"""
Every database connection costs memory, so a database has a ceiling called max_connections (RDS sets it
from the instance memory: bigger instance, more connections; a tiny one allows only a few dozen to a
hundred). A web server reuses a handful of connections. Lambda cannot: each running function instance
opens its own, so a burst of requests becomes a burst of connections, and the database starts refusing
them ("too many connections") long before the CPU is busy.
RDS Proxy fixes this: it keeps a POOL of database connections open and shares them among many short
client connections, and it also makes failover faster (it skips waiting for DNS to update).
peak_concurrency(requests_per_second, avg_duration_s) -> int
    How many function instances run at once (Little's law): requests per second x duration, rounded UP.
    Beware floating point: 10 x 0.3 is 3.0000000000000004 in Python and must give 3. Zero or negative
    inputs are a ValueError.
needs_proxy(concurrency, max_connections, connections_per_invocation=1, headroom=0.0) -> bool
    Without a proxy every concurrent invocation holds connections_per_invocation connections. True when
    that total is MORE than max_connections x (1 - headroom) (exactly equal still fits). headroom is the
    share you keep free for admin and replication, from 0 up to but not including 1. Zero or negative
    concurrency or max_connections, or a bad headroom, is a ValueError.
proxy_pool_size(max_connections, max_connections_percent) -> int
    The connections the proxy may open to the database: max_connections x percent / 100, rounded DOWN.
    The percent must be above 0 and at most 100; otherwise ValueError.
Examples:
    peak_concurrency(500, 0.2) == 100       needs_proxy(100, 90) is True       proxy_pool_size(90, 50) == 45
Why? The proxy lets 300 short function instances share, say, 50 database connections. The exam signal is
"Lambda + RDS + connection errors" and the answer is RDS Proxy (or fewer connections per function).
Hint: math.ceil(round(x, 9)) removes float noise before rounding up; math.floor for the pool.
"""
def peak_concurrency(requests_per_second, avg_duration_s):
    raise NotImplementedError  # YOUR CODE


def needs_proxy(concurrency, max_connections, connections_per_invocation=1, headroom=0.0):
    raise NotImplementedError  # YOUR CODE


def proxy_pool_size(max_connections, max_connections_percent):
    raise NotImplementedError  # YOUR CODE


class Ex07(Drill):
    """Too many connections"""
    tasks = ("3.3",)

    def test_peak_concurrency(self):
        self.assertEqual(peak_concurrency(500, 0.2), 100)
        self.assertEqual(peak_concurrency(1000, 0.3), 300)
        self.assertEqual(peak_concurrency(1, 1), 1)

    def test_concurrency_rounds_up(self):
        self.assertEqual(peak_concurrency(7, 0.5), 4, "3.5 instances do not exist: you need 4")
        self.assertEqual(peak_concurrency(1, 0.01), 1, "a tiny load still needs one instance")

    def test_float_noise_does_not_add_an_instance(self):
        self.assertEqual(peak_concurrency(10, 0.3), 3, "10 x 0.3 is 3.0000000000000004 in floating point")
        self.assertEqual(peak_concurrency(3, 0.1), 1)

    def test_concurrency_rejects_bad_input(self):
        for rps, dur in ((0, 1), (-5, 1), (5, 0), (5, -1)):
            with self.subTest(rps=rps, dur=dur):
                with self.assertRaises(ValueError):
                    peak_concurrency(rps, dur)

    def test_a_lambda_burst_needs_a_proxy(self):
        concurrency = peak_concurrency(1000, 0.3)      # 300 functions at once
        self.assertTrue(needs_proxy(concurrency, 100), "300 connections against a 100-connection database")
        self.assertFalse(needs_proxy(concurrency, 500))

    def test_exactly_at_the_limit_still_fits(self):
        self.assertFalse(needs_proxy(100, 100))
        self.assertTrue(needs_proxy(101, 100))
        self.assertTrue(needs_proxy(100, 90))

    def test_several_connections_per_invocation(self):
        self.assertTrue(needs_proxy(60, 100, connections_per_invocation=2), "60 x 2 = 120 connections")
        self.assertFalse(needs_proxy(50, 100, connections_per_invocation=2))

    def test_headroom_keeps_connections_free(self):
        self.assertFalse(needs_proxy(85, 100))
        self.assertTrue(needs_proxy(85, 100, headroom=0.2), "only 80 of the 100 may be used")
        self.assertFalse(needs_proxy(80, 100, headroom=0.2))

    def test_needs_proxy_rejects_bad_input(self):
        for args, kwargs in (((0, 100), {}), ((10, 0), {}), ((10, -1), {}), ((10, 100), {"headroom": -0.1}),
                             ((10, 100), {"headroom": 1.0})):
            with self.subTest(args=args, kwargs=kwargs):
                with self.assertRaises(ValueError):
                    needs_proxy(*args, **kwargs)

    def test_pool_size(self):
        self.assertEqual(proxy_pool_size(90, 50), 45)
        self.assertEqual(proxy_pool_size(100, 100), 100)
        self.assertEqual(proxy_pool_size(100, 33), 33)

    def test_pool_size_rounds_down(self):
        self.assertEqual(proxy_pool_size(91, 50), 45, "45.5 connections: you cannot open half, and must not exceed the share")
        self.assertEqual(proxy_pool_size(10, 99), 9)

    def test_pool_size_rejects_bad_input(self):
        for maxc, pct in ((0, 50), (-1, 50), (100, 0), (100, -5), (100, 101)):
            with self.subTest(max_connections=maxc, percent=pct):
                with self.assertRaises(ValueError):
                    proxy_pool_size(maxc, pct)

    def test_the_proxy_makes_the_burst_fit(self):
        pool = proxy_pool_size(100, 80)
        self.assertEqual(pool, 80)
        self.assertLess(pool, peak_concurrency(1000, 0.3), "the proxy shares 80 connections among 300 functions")


# ── Exercise 08: A database that fails over ──────────────────────────
"""
Build shortly's production database with boto3. Each setting answers a failure or a risk:
create_primary(rds, subnet_group, sg_id) -> "shortly-db"
    create_db_instance with: identifier "shortly-db" · engine "postgres", EngineVersion "17.4" ·
    class "db.t4g.micro" · 20 GiB of "gp3" storage ·
    MultiAZ True  (a synchronous standby in another AZ: if the AZ fails, RDS fails over automatically in
                   about 60-120 seconds; the standby serves NO reads — it is for availability only) ·
    StorageEncrypted True  (encryption can only be turned on at creation, never later) ·
    ManageMasterUserPassword True with MasterUsername "shortly_admin" and NO MasterUserPassword
                   (RDS creates the password in Secrets Manager and rotates it; it never sits in your code) ·
    BackupRetentionPeriod 7 (days of point-in-time restore) · DeletionProtection True (a delete is refused
    until protection is switched off) · PubliclyAccessible False ·
    DBSubnetGroupName=subnet_group · VpcSecurityGroupIds=[sg_id]
add_replica(rds, primary_id) -> "shortly-db-replica"
    create_db_instance_read_replica from the primary, class "db.t4g.micro". A read replica copies data
    asynchronously and CAN serve reads (reporting, scaling reads). It is a different tool from Multi-AZ.
take_snapshot(rds, db_id) -> "<db_id>-baseline"
    create_db_snapshot with that id. A manual snapshot is kept until you delete it, even after the
    database is gone.
Note: moto stores these settings but has no standby, no failover and no real replication, so the tests
read the settings back.
Why? These are the five defaults of a database you can defend in an exam answer: Multi-AZ, encryption,
no hard-coded password, backups, and protection against accidental deletion.
Hint: rds.create_db_instance(DBInstanceIdentifier=..., Engine=..., MultiAZ=True, ...);
      rds.create_db_instance_read_replica(DBInstanceIdentifier=..., SourceDBInstanceIdentifier=...).
"""
def create_primary(rds, subnet_group, sg_id):
    raise NotImplementedError  # YOUR CODE


def add_replica(rds, primary_id):
    raise NotImplementedError  # YOUR CODE


def take_snapshot(rds, db_id):
    raise NotImplementedError  # YOUR CODE


class Ex08(Drill):
    """A database that fails over"""
    tasks = ("2.2", "3.3")
    uses_aws = True

    def make(self):
        ec2, rds = self.client("ec2"), self.client("rds")
        vpc = ec2.create_vpc(CidrBlock="10.80.0.0/16")["Vpc"]["VpcId"]
        subnets = [ec2.create_subnet(VpcId=vpc, CidrBlock=f"10.80.{i}.0/24", AvailabilityZone=az)["Subnet"]["SubnetId"]
                   for i, az in enumerate(("us-east-1a", "us-east-1b"))]
        sg = ec2.create_security_group(GroupName="shortly-db", Description="db", VpcId=vpc)["GroupId"]
        rds.create_db_subnet_group(DBSubnetGroupName="shortly-subnets", DBSubnetGroupDescription="db", SubnetIds=subnets)
        calls = []
        rds.meta.events.register("provide-client-params.rds.CreateDBInstance",
                                 lambda params, **kw: calls.append(dict(params)))
        return rds, sg, calls

    def primary(self):
        rds, sg, calls = self.make()
        db_id = create_primary(rds, "shortly-subnets", sg)
        described = rds.describe_db_instances(DBInstanceIdentifier=db_id)["DBInstances"][0]
        return rds, sg, db_id, described, calls

    def test_identity_and_engine(self):
        _, _, db_id, db, _ = self.primary()
        self.assertEqual(db_id, "shortly-db")
        self.assertEqual((db["Engine"], db["DBInstanceClass"]), ("postgres", "db.t4g.micro"))
        self.assertTrue(db["EngineVersion"].startswith("17"), "pass EngineVersion explicitly (17.4)")

    def test_multi_az(self):
        _, _, _, db, _ = self.primary()
        self.assertTrue(db["MultiAZ"], "Multi-AZ gives a standby in a second AZ and automatic failover")

    def test_encrypted_gp3_storage(self):
        _, _, _, db, _ = self.primary()
        self.assertTrue(db["StorageEncrypted"], "encryption can only be set when the database is created")
        self.assertEqual((db["StorageType"], db["AllocatedStorage"]), ("gp3", 20))

    def test_password_is_managed_by_secrets_manager(self):
        rds, _, db_id, db, calls = self.primary()
        self.assertTrue(db.get("MasterUserSecret", {}).get("SecretArn"), "set ManageMasterUserPassword=True")
        self.assertEqual(db["MasterUsername"], "shortly_admin")
        self.assertTrue(calls, "create_db_instance was not called")
        self.assertNotIn("MasterUserPassword", calls[0], "no password in code: let RDS manage it")
        secrets = self.client("secretsmanager").list_secrets()["SecretList"]
        self.assertEqual(len(secrets), 1)
        self.assertTrue(secrets[0]["Name"].startswith("rds!"), "RDS-managed secrets are named rds!...")

    def test_backups_and_deletion_protection(self):
        rds, _, db_id, db, _ = self.primary()
        self.assertEqual(db["BackupRetentionPeriod"], 7)
        self.assertTrue(db["DeletionProtection"])
        with self.assertClientError("InvalidParameterCombination"):
            rds.delete_db_instance(DBInstanceIdentifier=db_id, SkipFinalSnapshot=True)

    def test_private_and_inside_your_network(self):
        _, sg, _, db, _ = self.primary()
        self.assertFalse(db["PubliclyAccessible"])
        self.assertEqual(db["DBSubnetGroup"]["DBSubnetGroupName"], "shortly-subnets")
        self.assertEqual([g["VpcSecurityGroupId"] for g in db["VpcSecurityGroups"]], [sg])

    def test_read_replica(self):
        rds, _, db_id, _, _ = self.primary()
        replica_id = add_replica(rds, db_id)
        self.assertEqual(replica_id, "shortly-db-replica")
        replica = rds.describe_db_instances(DBInstanceIdentifier=replica_id)["DBInstances"][0]
        self.assertEqual(replica["ReadReplicaSourceDBInstanceIdentifier"], db_id)
        self.assertEqual(replica["DBInstanceClass"], "db.t4g.micro")
        source = rds.describe_db_instances(DBInstanceIdentifier=db_id)["DBInstances"][0]
        self.assertEqual(source["ReadReplicaDBInstanceIdentifiers"], [replica_id])

    def test_manual_snapshot(self):
        rds, _, db_id, _, _ = self.primary()
        snapshot_id = take_snapshot(rds, db_id)
        self.assertEqual(snapshot_id, "shortly-db-baseline")
        snap = rds.describe_db_snapshots(DBSnapshotIdentifier=snapshot_id)["DBSnapshots"][0]
        self.assertEqual((snap["DBInstanceIdentifier"], snap["SnapshotType"], snap["Status"]), (db_id, "manual", "available"))


# ── Exercise 09 (decide): High availability, read scale or disaster recovery? ──
"""
Databases fail in different ways, and each AWS feature answers one of them. Choose ONE answer for
each scenario in CHOICES:
  "multi-az instance"          RDS: a synchronous standby in another AZ; automatic failover; the standby
                               serves no reads
  "multi-az cluster"           RDS: a writer plus two readable standbys in three AZs; faster failover
  "read replica"               RDS: an asynchronous copy that serves reads (and can be promoted)
  "aurora replica"             Aurora: up to 15 readers on the shared cluster storage; also failover targets
  "aurora global database"     Aurora: storage-level replication to other Regions, read-only secondaries
  "cross-region read replica"  RDS: a read replica in a different Region
  "rds proxy"                  a connection pool in front of the database
Replace every None with one of those answers. (The answers are stored as hashes, so reading the test
will not give them away.)
"""
CHOICE_SCENARIOS = {
    1: "RDS PostgreSQL on a single instance. It must survive the loss of an Availability Zone with automatic failover. "
       "It does not need more read capacity, and the team wants the smallest change.",
    2: "An RDS MySQL primary is slowed down by heavy reporting queries. Move the reports to a separate copy of the data. "
       "Reports may lag a little. Nobody asked for faster failover.",
    3: "An Aurora cluster needs more read capacity inside its Region, and wants a standby to take over quickly if the writer fails.",
    4: "A global Aurora MySQL application needs local low-latency reads in two other Regions, replication in under a second, "
       "and the ability to move writes to another Region if the primary Region fails.",
    5: "RDS PostgreSQL in one Region needs automatic failover that typically finishes in under 35 seconds, "
       "and two standby copies in other AZs that can also serve reads.",
    6: "An RDS MySQL database must have a copy in another Region that can be promoted for disaster recovery, "
       "without moving the database to Aurora.",
    7: "Lambda functions exhaust the database's connections during traffic bursts, and failovers take too long "
       "because applications wait for DNS to update.",
}
CHOICE_OPTIONS = ("multi-az instance", "multi-az cluster", "read replica", "aurora replica",
                  "aurora global database", "cross-region read replica", "rds proxy")
CHOICES = {n: None for n in CHOICE_SCENARIOS}   # YOUR ANSWERS: one of CHOICE_OPTIONS
CHOICE_DIGESTS = {
    1: "9a87adb6fb66d7fe68574ae02b3d4f4c81c1eaf464a0e7636368ea07bef8bdcf",
    2: "f8071d9f65c8d5e948c254d0653ce1e7588877d412392e2fe2f67880f113bb2e",
    3: "f47b6d932e642ca85546dd39f351b71d933fc37d038b7fc22c1b2dcd63cede13",
    4: "a04c8e260796069883ff55331ace0594671fe9656ffb9ee8b6f9773d197f59f4",
    5: "bfbe4038d81632b639c5678ba672f36ef84ba19a37dd7f209bd7dead1cf65e46",
    6: "9a48f643bf177be908753e817d0bc07bd2e70eae11c11e9a3ce1e73b152b6e62",
    7: "485f3fb0643281d5bafae2c5c04a879c039698af2df9931157b4a6a222705c25",
}


class Ex09(Drill):
    """High availability, read scale or disaster recovery? (decide)"""
    tasks = ("2.2", "3.3")

    def test_choices(self):
        for n, story in CHOICE_SCENARIOS.items():
            with self.subTest(scenario=n):
                value = CHOICES.get(n)
                self.assertIn(value, CHOICE_OPTIONS, f"scenario {n}: answer one of {CHOICE_OPTIONS}, not {value!r}")
                self.assertHashed(value, f"w05-ex09-{n}", CHOICE_DIGESTS[n],
                                  f"scenario {n} ({story}): {value!r} is not right — is it availability, read scale, "
                                  "another Region, or connections?")


# ── Exercise 10 (decide): The right engine ───────────────────────────
"""
AWS has a purpose-built database for most shapes of data. Choose the best service for each scenario:
  "rds"          managed MySQL, PostgreSQL, MariaDB, Oracle, SQL Server or Db2 on an instance
  "aurora"       MySQL- or PostgreSQL-compatible relational database with shared, auto-growing storage
  "dynamodb"     serverless key-value and document database
  "elasticache"  managed Valkey, Redis OSS or Memcached, used mostly as a cache
  "documentdb"   MongoDB-compatible document database
  "neptune"      graph database
  "keyspaces"    Apache Cassandra-compatible database
  "opensearch"   search and log analytics
  "memorydb"     durable in-memory database, Valkey and Redis OSS compatible
Replace every None in ENGINES. (Hashed answers again.)
"""
ENGINE_SCENARIOS = {
    1: "A relational order system built on PostgreSQL. Managed PostgreSQL on a single small instance is enough: "
       "no cluster features, and the least change from the current setup.",
    2: "A MySQL-compatible database that needs up to 15 low-lag read replicas sharing one storage volume that grows by itself.",
    3: "Shopping carts as key-value items: millions of requests per second, single-digit-millisecond latency, no servers to manage.",
    4: "A sub-millisecond leaderboard that sits in front of an existing database to take repeated reads off it.",
    5: "An application that stores JSON documents and talks to its database with MongoDB drivers.",
    6: "Fraud-ring detection: finding connections between accounts, cards and devices several hops apart.",
    7: "An existing application written for Apache Cassandra (CQL) that should run without managing any servers.",
    8: "Full-text search and log analytics over millions of events.",
    9: "A durable in-memory PRIMARY database (Redis-compatible) that must survive the loss of a node without losing acknowledged writes.",
}
ENGINE_OPTIONS = ("rds", "aurora", "dynamodb", "elasticache", "documentdb", "neptune", "keyspaces", "opensearch", "memorydb")
ENGINES = {n: None for n in ENGINE_SCENARIOS}   # YOUR ANSWERS: one of ENGINE_OPTIONS
ENGINE_DIGESTS = {
    1: "337191136a5f4a9dcc250faa253a757c167d3be737c4f9ff705399f74601e5ba",
    2: "dc9e0e13925bb2e0b2363fb3edc5d6b0156fade881ca79241ec64cda0666afb9",
    3: "7427a03aa2793b419a44df614b578523aed2c436a5e14b6405db408cb88adcb2",
    4: "dd986df93c9559e5778734fe568b6ef7d7dd51313d623c2ab13e07499845a68c",
    5: "eb9aeb6ac11bb890420fcd6836354610fa84cdde4c3ca3a249ced1cb63f17b77",
    6: "1034682c5cb780b756888d02cccc6e36b992f081bb93eefb2b0fc22a6ae7d611",
    7: "ab299714018294bb185827d55ce494c799d34c0fee08868528bc75f84d1e15aa",
    8: "7a23a497d65fc2f7cbb14348d8b08c89d4280f191e2944d5aff7554b51217ea9",
    9: "e46a403adec715d29ee7c93a002364831253659a7a917ee7b415fb9de3557c4e",
}


class Ex10(Drill):
    """The right engine (decide)"""
    tasks = ("3.3",)

    def test_engines(self):
        for n, story in ENGINE_SCENARIOS.items():
            with self.subTest(scenario=n):
                value = ENGINES.get(n)
                self.assertIn(value, ENGINE_OPTIONS, f"scenario {n}: answer one of {ENGINE_OPTIONS}, not {value!r}")
                self.assertHashed(value, f"w05-ex10-{n}", ENGINE_DIGESTS[n],
                                  f"scenario {n} ({story}): {value!r} is not right — what shape is the data and "
                                  "what is the service's job?")


if __name__ == "__main__":
    run()

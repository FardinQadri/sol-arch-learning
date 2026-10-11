"""
Week 00 drills — Foundations & exam technique
=============================================
Run:    python practice/exercises.py          every drill
        python practice/exercises.py 3        drill 3 only
Stuck?  read the hint line; then compare with practice/solutions.py.
Every drill runs offline: AWS calls go to moto (a fake AWS) with fake credentials — nothing here can
touch a real AWS account or cost money.
"""
import math  # noqa: F401  (you may need it)
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.awsdrill import Drill, run  # noqa: E402
from _harness.awslib import prices  # noqa: E402


# ── Exercise 01 ★: Read an ARN ───────────────────────────────────────
"""
parse_arn(arn: str) -> dict with keys partition, service, region, account, resource_type, resource_id

An ARN is  arn:PARTITION:SERVICE:REGION:ACCOUNT:RESOURCE  — split on the first five ':' only.
RESOURCE is "type/id", "type:id" or just "id": split it on whichever of '/' or ':' comes FIRST.
Exceptions: S3 has no resource type (all of RESOURCE is bucket[/key]); a resource with no '/' or ':'
has resource_type "". Empty region/account stay "" (S3 and IAM are global, so their ARNs leave them out).
Partitions: aws, aws-cn, aws-us-gov. Anything else, fewer than six parts, or a first part that is not
"arn" → ValueError.

Examples:
  parse_arn("arn:aws:iam::111122223333:role/team/app") == {"partition": "aws", "service": "iam",
      "region": "", "account": "111122223333", "resource_type": "role", "resource_id": "team/app"}
  parse_arn("arn:aws:s3:::shortly-assets/logos/a.png")["resource_id"] == "shortly-assets/logos/a.png"
  parse_arn("arn:aws:lambda:us-east-1:111122223333:function:shorten:PROD")["resource_id"] == "shorten:PROD"
Hint: arn.split(":", 5) gives exactly six parts for a valid ARN.
"""
def parse_arn(arn):
    raise NotImplementedError  # YOUR CODE


class Ex01(Drill):
    """Read an ARN ★"""
    tasks = ("1.1",)

    def test_iam_role_with_path(self):
        self.assertEqual(parse_arn("arn:aws:iam::111122223333:role/team/app"),
                         {"partition": "aws", "service": "iam", "region": "", "account": "111122223333",
                          "resource_type": "role", "resource_id": "team/app"})

    def test_s3_object_has_no_type(self):
        self.assertEqual(parse_arn("arn:aws:s3:::shortly-assets/logos/a.png"),
                         {"partition": "aws", "service": "s3", "region": "", "account": "",
                          "resource_type": "", "resource_id": "shortly-assets/logos/a.png"})

    def test_colon_separated_resource(self):
        got = parse_arn("arn:aws:lambda:us-east-1:111122223333:function:shorten:PROD")
        self.assertEqual((got["region"], got["resource_type"], got["resource_id"]), ("us-east-1", "function", "shorten:PROD"))

    def test_first_separator_wins(self):
        got = parse_arn("arn:aws:logs:us-east-1:111122223333:log-group:/shortly/app:*")
        self.assertEqual((got["resource_type"], got["resource_id"]), ("log-group", "/shortly/app:*"))

    def test_resource_without_type(self):
        got = parse_arn("arn:aws:sns:us-east-1:111122223333:alerts")
        self.assertEqual((got["resource_type"], got["resource_id"]), ("", "alerts"))

    def test_other_partitions(self):
        self.assertEqual(parse_arn("arn:aws-cn:s3:::b1")["partition"], "aws-cn")
        self.assertEqual(parse_arn("arn:aws-us-gov:iam::111122223333:user/x")["partition"], "aws-us-gov")

    def test_invalid(self):
        for bad in ("arn:aws:s3", "urn:aws:s3:::b1", "arn:azure:s3:::b1", ""):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError, msg=f"parse_arn({bad!r}) should raise ValueError"):
                    parse_arn(bad)


# ── Exercise 02 ★: Availability maths ────────────────────────────────
"""
series(*availabilities) -> float        every part is needed: multiply the availabilities
parallel(availability, copies) -> float  any one of `copies` identical parts is enough: 1 - (1 - a) ** copies
downtime_minutes(availability, days=30) -> float   expected minutes of downtime in `days` days
Availabilities are fractions (0.999, not 99.9). Values outside 0 < a ≤ 1, or copies < 1 → ValueError.

Examples:
  series(0.999, 0.999)  ≈ 0.998001
  parallel(0.99, 2)     ≈ 0.9999
  downtime_minutes(0.999) ≈ 43.2      (30 days × 24 h × 60 min × 0.001)
Why it matters: two instances in two AZs behind a load balancer are in parallel; the load balancer
and the database they all need are in series — a chain is never better than its weakest link.
Hint: math.prod() multiplies an iterable.
"""
def series(*availabilities):
    raise NotImplementedError  # YOUR CODE


def parallel(availability, copies):
    raise NotImplementedError  # YOUR CODE


def downtime_minutes(availability, days=30):
    raise NotImplementedError  # YOUR CODE


class Ex02(Drill):
    """Availability maths ★"""
    tasks = ("2.2",)

    def test_series(self):
        self.assertAlmostEqual(series(0.999, 0.999), 0.998001, places=9)
        self.assertAlmostEqual(series(0.9995), 0.9995, places=9)

    def test_parallel(self):
        self.assertAlmostEqual(parallel(0.99, 2), 0.9999, places=9)
        self.assertAlmostEqual(parallel(0.9, 3), 0.999, places=9)
        self.assertAlmostEqual(parallel(0.95, 1), 0.95, places=9)

    def test_downtime(self):
        self.assertAlmostEqual(downtime_minutes(0.999), 43.2, places=6)
        self.assertAlmostEqual(downtime_minutes(0.9999, days=365), 52.56, places=6)

    def test_web_tier_example(self):
        # load balancer (99.99 %) → two app instances in two AZs (99 % each) → database (99.95 %)
        expected = 0.9999 * (1 - 0.01 ** 2) * 0.9995
        self.assertAlmostEqual(series(0.9999, parallel(0.99, 2), 0.9995), expected, places=12)

    def test_rejects_bad_values(self):
        for call in (lambda: series(1.5), lambda: series(0.99, 0), lambda: parallel(0.9, 0), lambda: parallel(-0.1, 2)):
            with self.subTest():
                with self.assertRaises(ValueError):
                    call()


# ── Exercise 03 ★: Survive the loss of an AZ ─────────────────────────
"""
per_az_needed(needed, azs) -> int
    How many instances must run in EACH of `azs` Availability Zones so that `needed` instances are
    still running after any one AZ fails? Spread evenly, round up. azs < 2 → ValueError.
    per_az_needed(6, 3) == 3    (9 in total: lose one AZ, 6 remain)
survives_az_loss(layout, needed) -> bool
    layout maps AZ name → instances there. True when, whichever ONE AZ is lost, at least `needed`
    instances remain. A layout with fewer than two AZs never survives.
    survives_az_loss({"us-east-1a": 6, "us-east-1b": 2}, 6) is False   (lose 1a → 2 left)
This is "static stability": capacity already running, so an AZ failure needs no scaling to recover.
Hint: after losing the AZ with the most instances, how many are left?
"""
def per_az_needed(needed, azs):
    raise NotImplementedError  # YOUR CODE


def survives_az_loss(layout, needed):
    raise NotImplementedError  # YOUR CODE


class Ex03(Drill):
    """Survive the loss of an AZ ★"""
    tasks = ("2.2",)

    def test_per_az_needed(self):
        for (needed, azs), want in {(6, 3): 3, (4, 2): 4, (10, 3): 5, (7, 4): 3, (1, 2): 1}.items():
            with self.subTest(needed=needed, azs=azs):
                self.assertEqual(per_az_needed(needed, azs), want)

    def test_one_az_is_not_enough(self):
        with self.assertRaises(ValueError):
            per_az_needed(4, 1)

    def test_survives(self):
        self.assertTrue(survives_az_loss({"us-east-1a": 3, "us-east-1b": 3, "us-east-1c": 3}, 6))
        self.assertTrue(survives_az_loss({"us-east-1a": 4, "us-east-1b": 4}, 4))

    def test_does_not_survive(self):
        self.assertFalse(survives_az_loss({"us-east-1a": 6, "us-east-1b": 2}, 6))
        self.assertFalse(survives_az_loss({"us-east-1a": 3, "us-east-1b": 3, "us-east-1c": 2}, 6))
        self.assertFalse(survives_az_loss({"us-east-1a": 10}, 1))
        self.assertFalse(survives_az_loss({}, 1))


# ── Exercise 04 (decide): Who is responsible? ────────────────────────
"""
For each numbered task in RESPONSIBILITY_TASKS, who does it — "customer" or "aws"?
Replace every None in RESPONSIBILITY with "customer" or "aws".
The line AWS draws: AWS secures the cloud itself ("security OF the cloud"); you secure what you put
in it ("security IN the cloud"). The more managed the service, the more AWS does — but your data,
who can access it, and how you configure it always stay yours.
(The answers are stored as hashes, so reading the test will not give them away.)
"""
RESPONSIBILITY_TASKS = {
    1: ("Amazon EC2", "patch the guest operating system"),
    2: ("Amazon RDS", "patch the database engine"),
    3: ("AWS Lambda", "patch the operating system that runs your functions"),
    4: ("Amazon EC2", "configure security group rules"),
    5: ("Amazon S3", "turn on encryption for data at rest"),
    6: ("Amazon S3", "physical security of the data centres"),
    7: ("Amazon DynamoDB", "write IAM policies that grant access to a table"),
    8: ("Amazon EBS", "replace failed disks behind a volume"),
    9: ("AWS Lambda", "keep the libraries in your function code free of known vulnerabilities"),
    10: ("Amazon RDS", "choose which network ports a DB instance accepts traffic on"),
}
RESPONSIBILITY = {n: None for n in RESPONSIBILITY_TASKS}   # YOUR ANSWERS: "customer" or "aws"

RESPONSIBILITY_DIGESTS = {
    1: "8682259a3d1c74ad4125bc6d13e03d8732817a02ec6601058de2a5de05322157",
    2: "a4eac6f2e952919cb4646dfcc46769490f0eb7e084dff7b657244fa7551526e9",
    3: "234b6927abcc493df1f528666c12d40d158fccd6919e2fd6820696c417a929a8",
    4: "8fa7e625a1edd1bb65b1bc9d6e8246fc31c18638b0c75b0598cc46ca9ca4b253",
    5: "f6675df3fb3cfa269768cd5c4a9cb377c04f6d45e8a72dab449c9f6a63eff45c",
    6: "a9995d7cef5fe00b28a1038f71911305c082884e9f1481a319dffa89cab0c0e3",
    7: "27711b0e304c157bc0c85029fa2b5972876ad8f6e67e169a2ec20873ffc2ea04",
    8: "9ac7d2eaf30017ba60d930b003354829a8a98f43209919683b94f17013de9ebe",
    9: "c6d9da1d6e520b2e9042e4aeea14ff7ab08c014933195bd5bf1b7f2c63ef33f2",
    10: "2ae29c906ba517125916da97d183790a05c0284463b0355579079919629725f9",
}


class Ex04(Drill):
    """Who is responsible?"""
    tasks = ("1.2",)

    def test_each_task(self):
        for n, (service, task) in RESPONSIBILITY_TASKS.items():
            with self.subTest(n=n):
                value = RESPONSIBILITY.get(n)
                self.assertIn(value, ("customer", "aws"), f"task {n} ({service}: {task}): answer 'customer' or 'aws', not {value!r}")
                self.assertHashed(value, f"w00-ex04-{n}", RESPONSIBILITY_DIGESTS[n],
                                  f"task {n} ({service}: {task}): {value!r} is not right — think OF vs IN the cloud")


# ── Exercise 05: Who am I, and where? ────────────────────────────────
"""
whoami() -> {"account": str, "arn": str}    from STS GetCallerIdentity
region_names() -> list[str]                 every Region name from EC2 DescribeRegions, sorted
Create clients with boto3.client("sts") / boto3.client("ec2", region_name="us-east-1").
In this drill AWS is moto, whose fake account is 123456789012.
Example: whoami()["account"] == "123456789012";  "eu-west-1" in region_names()
Hint: get_caller_identity() returns a dict with "Account" and "Arn".
"""
def whoami():
    raise NotImplementedError  # YOUR CODE


def region_names():
    raise NotImplementedError  # YOUR CODE


class Ex05(Drill):
    """Who am I, and where?"""
    tasks = ("1.1",)
    uses_aws = True

    def test_whoami(self):
        got = whoami()
        self.assertEqual(set(got), {"account", "arn"}, "return exactly the keys 'account' and 'arn'")
        self.assertEqual(got["account"], "123456789012")
        self.assertTrue(got["arn"].startswith("arn:aws:"), got["arn"])

    def test_region_names(self):
        names = region_names()
        self.assertEqual(names, sorted(names), "sort the names")
        self.assertGreaterEqual(len(names), 30)
        self.assertTrue({"us-east-1", "eu-west-1", "ap-southeast-2"} <= set(names))


# ── Exercise 06: Every page, not just the first ─────────────────────
"""
count_objects(s3, bucket, prefix="", page_size=1000) -> int
Count every object whose key starts with `prefix`. One ListObjectsV2 call returns at most
`page_size` keys (S3's maximum is 1,000), so a single call silently undercounts big buckets.
Use s3.get_paginator("list_objects_v2") with PaginationConfig={"PageSize": page_size}.
Example: 250 objects under "logs/", page_size=100 → 250, fetched in 3 calls.
Hint: each page has "KeyCount" (and no "Contents" when it is empty).
"""
def count_objects(s3, bucket, prefix="", page_size=1000):
    raise NotImplementedError  # YOUR CODE


class Ex06(Drill):
    """Every page, not just the first"""
    tasks = ("3.1",)
    uses_aws = True

    def test_counts_across_pages(self):
        s3 = self.client("s3")
        s3.create_bucket(Bucket="drill-logs")
        for i in range(250):
            s3.put_object(Bucket="drill-logs", Key=f"logs/{i:04d}.json", Body=b"{}")
        for i in range(5):
            s3.put_object(Bucket="drill-logs", Key=f"img/{i}.png", Body=b"")
        calls = []
        s3.meta.events.register("before-call.s3.ListObjectsV2", lambda **kwargs: calls.append(1))
        self.assertEqual(count_objects(s3, "drill-logs", "logs/", page_size=100), 250)
        self.assertEqual(len(calls), 3, "250 keys at 100 per page need 3 ListObjectsV2 calls")
        self.assertEqual(count_objects(s3, "drill-logs", "img/"), 5)
        self.assertEqual(count_objects(s3, "drill-logs"), 255)

    def test_empty_bucket(self):
        s3 = self.client("s3")
        s3.create_bucket(Bucket="drill-empty")
        self.assertEqual(count_objects(s3, "drill-empty"), 0)


# ── Exercise 07: Errors and the us-east-1 rule ───────────────────────
"""
bucket_exists(s3, name) -> bool
    head_bucket raises botocore.exceptions.ClientError when the bucket is missing (error code "404")
    or belongs to someone else ("403"). Return False for "404", True for "403" (it exists — just not
    yours), and re-raise any other error.
ensure_bucket(s3, name, region) -> "created" | "exists"
    Create the bucket unless it exists. The rule that trips everyone: in us-east-1 you must NOT pass
    CreateBucketConfiguration; in every other Region you MUST pass {"LocationConstraint": region}.
    If create_bucket answers "BucketAlreadyOwnedByYou", return "exists".
Hint: exc.response["Error"]["Code"] holds the error code.
"""
from botocore.exceptions import ClientError  # noqa: E402


def bucket_exists(s3, name):
    raise NotImplementedError  # YOUR CODE


def ensure_bucket(s3, name, region):
    raise NotImplementedError  # YOUR CODE


class _FakeS3:
    """A stand-in client whose head_bucket / create_bucket fail with a chosen error code."""

    def __init__(self, head_code=None, create_code=None):
        self.head_code, self.create_code, self.created = head_code, create_code, []

    def head_bucket(self, Bucket):
        if self.head_code:
            raise ClientError({"Error": {"Code": self.head_code, "Message": "x"}}, "HeadBucket")
        return {}

    def create_bucket(self, **kwargs):
        if self.create_code:
            raise ClientError({"Error": {"Code": self.create_code, "Message": "x"}}, "CreateBucket")
        self.created.append(kwargs)
        return {}


class Ex07(Drill):
    """Errors and the us-east-1 rule"""
    tasks = ("3.1",)
    uses_aws = True

    def test_exists(self):
        s3 = self.client("s3")
        self.assertFalse(bucket_exists(s3, "drill-missing"))
        s3.create_bucket(Bucket="drill-here")
        self.assertTrue(bucket_exists(s3, "drill-here"))

    def test_forbidden_means_it_exists(self):
        self.assertTrue(bucket_exists(_FakeS3(head_code="403"), "someone-elses"))

    def test_other_errors_are_raised(self):
        with self.assertRaises(ClientError):
            bucket_exists(_FakeS3(head_code="500"), "broken")

    def test_us_east_1(self):
        s3 = self.client("s3", "us-east-1")
        self.assertEqual(ensure_bucket(s3, "drill-east", "us-east-1"), "created")
        self.assertIsNone(s3.get_bucket_location(Bucket="drill-east")["LocationConstraint"])
        self.assertEqual(ensure_bucket(s3, "drill-east", "us-east-1"), "exists")

    def test_other_region(self):
        s3 = self.client("s3", "eu-west-1")
        self.assertEqual(ensure_bucket(s3, "drill-west", "eu-west-1"), "created")
        self.assertEqual(s3.get_bucket_location(Bucket="drill-west")["LocationConstraint"], "eu-west-1")

    def test_race_already_owned(self):
        fake = _FakeS3(head_code="404", create_code="BucketAlreadyOwnedByYou")
        self.assertEqual(ensure_bucket(fake, "raced", "eu-west-1"), "exists")


# ── Exercise 08 ★: What does moving data cost? ───────────────────────
"""
transfer_cost(flows, price=PRICES) -> float     (USD, rounded to 4 decimal places)
Each flow is (source, destination, gb). A place is "internet" or an Availability Zone name such as
"us-east-1a" (its Region is the name without the final letter).
  internet → AWS                   free
  AWS → internet                   gb × egress_internet_per_gb
  same AZ                          free (private IP addresses)
  different AZ, same Region        gb × inter_az_per_gb_each_way × 2   (charged going out AND coming in)
  different Region                 gb × inter_region_per_gb
A flow with "internet" at both ends → ValueError.
PRICES are the course's illustrative us-east-1 prices (_harness/awslib/prices.toml), not a quote.
Example: transfer_cost([("us-east-1a", "us-east-1b", 100)]) == 2.0
Hint: "us-east-1a"[:-1] == "us-east-1".
"""
PRICES = prices.section("data_transfer")


def transfer_cost(flows, price=PRICES):
    raise NotImplementedError  # YOUR CODE


class Ex08(Drill):
    """What does moving data cost? ★"""
    tasks = ("4.4",)

    def test_each_kind_of_flow(self):
        p = PRICES
        cases = {
            ("internet", "us-east-1a", 500): 0.0,
            ("us-east-1a", "internet", 1000): round(1000 * p["egress_internet_per_gb"], 4),
            ("us-east-1a", "us-east-1a", 800): 0.0,
            ("us-east-1a", "us-east-1b", 100): round(100 * p["inter_az_per_gb_each_way"] * 2, 4),
            ("us-east-1a", "eu-west-1b", 50): round(50 * p["inter_region_per_gb"], 4),
        }
        for flow, want in cases.items():
            with self.subTest(flow=flow):
                self.assertAlmostEqual(transfer_cost([flow]), want, places=4)

    def test_sum_of_flows(self):
        flows = [("us-east-1a", "us-east-1b", 100), ("us-east-1b", "internet", 10)]
        self.assertAlmostEqual(transfer_cost(flows), round(2.0 + 10 * PRICES["egress_internet_per_gb"], 4), places=4)

    def test_uses_the_price_argument(self):
        custom = {"ingress_per_gb": 0.0, "egress_internet_per_gb": 0.05, "inter_az_per_gb_each_way": 0.02,
                  "inter_region_per_gb": 0.04}
        self.assertAlmostEqual(transfer_cost([("us-east-1a", "us-east-1c", 10)], price=custom), 0.4, places=4)

    def test_internet_to_internet(self):
        with self.assertRaises(ValueError):
            transfer_cost([("internet", "internet", 1)])


# ── Exercise 09: A client that retries well ──────────────────────────
"""
make_client(service, region, total_attempts=5, connect_timeout=3, read_timeout=10)
Return a boto3 client that retries throttling and transient errors in "adaptive" mode, makes at
most `total_attempts` attempts in total (the first try included) and uses the given timeouts.
Hint: botocore.config.Config(retries={"total_max_attempts": ..., "mode": "adaptive"},
      connect_timeout=..., read_timeout=...)  — note botocore's own "max_attempts" key means RETRIES,
      one fewer than the total.
"""
def make_client(service, region, total_attempts=5, connect_timeout=3, read_timeout=10):
    raise NotImplementedError  # YOUR CODE


class Ex09(Drill):
    """A client that retries well"""
    tasks = ("2.1",)

    def test_defaults(self):
        client = make_client("s3", "eu-west-1")
        self.assertEqual(client.meta.region_name, "eu-west-1")
        self.assertEqual(client.meta.config.retries, {"mode": "adaptive", "total_max_attempts": 5})
        self.assertEqual((client.meta.config.connect_timeout, client.meta.config.read_timeout), (3, 10))

    def test_custom(self):
        client = make_client("dynamodb", "us-east-1", total_attempts=1, connect_timeout=1, read_timeout=2)
        self.assertEqual(client.meta.config.retries["total_max_attempts"], 1)
        self.assertEqual(client.meta.service_model.service_name, "dynamodb")
        self.assertEqual(client.meta.config.read_timeout, 2)


# ── Exercise 10 (combined): What is running where? ───────────────────
"""
inventory(regions) -> dict
For each Region name in `regions` report what exists there:
    {"us-east-1": {"buckets": ["a-bucket", …] (sorted), "instances": 2, "queues": 1}, …}
Buckets: S3's ListBuckets returns every bucket whatever the Region — place each one with
get_bucket_location (a LocationConstraint of None means us-east-1).
Instances: count every instance in every reservation of ec2.describe_instances() in that Region.
Queues: len(sqs.list_queues().get("QueueUrls", [])) in that Region.
Hint: make the clients inside the loop with region_name=region.
"""
def inventory(regions):
    raise NotImplementedError  # YOUR CODE


class Ex10(Drill):
    """What is running where?"""
    tasks = ("2.2",)
    uses_aws = True

    def test_two_regions(self):
        east, west = self.client("s3", "us-east-1"), self.client("s3", "eu-west-1")
        east.create_bucket(Bucket="inv-east-bucket")
        west.create_bucket(Bucket="inv-west-bucket", CreateBucketConfiguration={"LocationConstraint": "eu-west-1"})
        ec2 = self.client("ec2", "us-east-1")
        image = ec2.describe_images(Owners=["amazon"])["Images"][0]["ImageId"]
        ec2.run_instances(ImageId=image, MinCount=2, MaxCount=2)
        self.client("sqs", "eu-west-1").create_queue(QueueName="inv-queue")
        self.assertEqual(inventory(["us-east-1", "eu-west-1"]), {
            "us-east-1": {"buckets": ["inv-east-bucket"], "instances": 2, "queues": 0},
            "eu-west-1": {"buckets": ["inv-west-bucket"], "instances": 0, "queues": 1},
        })

    def test_empty_region(self):
        self.assertEqual(inventory(["ap-southeast-2"]), {"ap-southeast-2": {"buckets": [], "instances": 0, "queues": 0}})


if __name__ == "__main__":
    run()

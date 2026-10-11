"""
Week 04 drills — storage
========================
Run:    python practice/exercises.py          every drill
        python practice/exercises.py 4        drill 4 only
Drills 01–04 are pure Python models of how storage is billed and limited: what a storage class costs,
when a lifecycle rule moves an object, which EBS volume fits, and how a big upload is split. Drills
05–09 build, predict and fix the real thing with boto3 against moto (a fake AWS) or with the policy
evaluator you met in week 01. Drill 10 is a decide drill. Nothing here can touch a real account or
cost money.
The course's own versions of drills 01–04 (_harness/awslib/s3cost.py, lifecycle.py, ebs.py) are their
answer key — don't open them until you are done.
Note: moto stores what you send but enforces little. It never runs lifecycle rules, never copies
replicated objects, ignores Block Public Access, and treats a bucket-policy Deny crudely (it ignores
Principal and Condition). So the drills read your settings back, and the models and the policy
evaluator show the behaviour. Never open a presigned URL in a test: it could leave your machine.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.awsdrill import Drill, normalise, run  # noqa: E402
from _harness.awslib import prices  # noqa: E402


# ── Exercise 01 ★: What does this storage cost? ──────────────────────
"""
PRICES (given) are illustrative us-east-1 numbers from _harness/awslib/prices.toml. The six classes are
CLASSES; GLACIER means Glacier Flexible Retrieval and GLACIER_IR means Glacier Instant Retrieval.
Given: RATE_KEY (the price name of each class's storage), MIN_DAYS and MIN_OBJECT_KB (the billing minimums),
RETRIEVAL_KEY (retrieval price per GB, for the classes that charge it) and ARCHIVE_RETRIEVAL_KEY (the two
archive classes have a standard and a bulk retrieval price).
storage_cost(storage_class, objects, object_kb, days, retrieved_gb=0.0, *, retrieval="standard", price=PRICES) -> float
    USD to keep `objects` objects of `object_kb` KB each for `days` days, then retrieve `retrieved_gb` GB in
    total. Round to 2 decimal places.
      billable GB   = objects x max(object_kb, MIN_OBJECT_KB[class]) / 1,048,576      (1 GB = 1,048,576 KB)
      billable days = max(days, MIN_DAYS[class])
      storage       = billable GB x price per GB-month x billable days / 30           (a month = 30 days)
      retrieval     = retrieved_gb x the class's retrieval price     (Standard has none)
    `retrieval` ("standard" or "bulk") only changes the price for GLACIER and DEEP_ARCHIVE.
    ValueError for: an unknown class, an unknown retrieval option, a negative objects, object_kb, days
    or retrieved_gb.
cheapest_class(objects, object_kb, days, retrieved_gb=0.0, *, millisecond_access=True, single_az_ok=False, price=PRICES)
    -> (class, cost)
    The cheapest ALLOWED class. millisecond_access=True rules out GLACIER and DEEP_ARCHIVE (they take minutes
    to hours to read). ONEZONE_IA keeps data in one AZ, so it is allowed only when single_az_ok is True.
    A tie goes to the class that comes first in CLASSES. (Intelligent-Tiering is not modelled: week 11.)
Examples (1 TB = 1024 objects of 1 GiB = 1,048,576 KB):
    storage_cost("STANDARD", 1024, 1_048_576, 30) == 23.55
    storage_cost("STANDARD_IA", 1024, 1_048_576, 5) == 12.8      # deleted after 5 days, billed for 30
    storage_cost("STANDARD_IA", 1_000_000, 10, 30) == 1.53        # 10 KB objects are billed as 128 KB each
    cheapest_class(1024, 1_048_576, 365, 0) == ("GLACIER_IR", 49.83)
Why? Cheap classes are cheap because they charge for something else: a minimum time, a minimum size and a fee
per GB you read back. The cheapest class on the price list is often the dearest for your access pattern.
Hint: write storage_cost first; cheapest_class is a min() over the allowed classes (keep the first on a tie).
"""
PRICES = prices.section("storage")
CLASSES = ("STANDARD", "STANDARD_IA", "ONEZONE_IA", "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE")
MIN_DAYS = {"STANDARD": 0, "STANDARD_IA": 30, "ONEZONE_IA": 30, "GLACIER_IR": 90, "GLACIER": 90, "DEEP_ARCHIVE": 180}
MIN_OBJECT_KB = {"STANDARD": 0, "STANDARD_IA": 128, "ONEZONE_IA": 128, "GLACIER_IR": 128, "GLACIER": 0, "DEEP_ARCHIVE": 0}
RATE_KEY = {"STANDARD": "s3_standard_per_gb_month", "STANDARD_IA": "s3_standard_ia_per_gb_month",
            "ONEZONE_IA": "s3_onezone_ia_per_gb_month", "GLACIER_IR": "s3_glacier_ir_per_gb_month",
            "GLACIER": "s3_glacier_flexible_per_gb_month", "DEEP_ARCHIVE": "s3_deep_archive_per_gb_month"}
RETRIEVAL_KEY = {"STANDARD_IA": "s3_standard_ia_retrieval_per_gb", "ONEZONE_IA": "s3_onezone_ia_retrieval_per_gb",
                 "GLACIER_IR": "s3_glacier_ir_retrieval_per_gb"}
ARCHIVE_RETRIEVAL_KEY = {("GLACIER", "standard"): "s3_glacier_flexible_standard_retrieval_per_gb",
                         ("GLACIER", "bulk"): "s3_glacier_flexible_bulk_retrieval_per_gb",
                         ("DEEP_ARCHIVE", "standard"): "s3_deep_archive_standard_retrieval_per_gb",
                         ("DEEP_ARCHIVE", "bulk"): "s3_deep_archive_bulk_retrieval_per_gb"}


def storage_cost(storage_class, objects, object_kb, days, retrieved_gb=0.0, *, retrieval="standard", price=PRICES):
    raise NotImplementedError  # YOUR CODE


def cheapest_class(objects, object_kb, days, retrieved_gb=0.0, *, millisecond_access=True, single_az_ok=False, price=PRICES):
    raise NotImplementedError  # YOUR CODE


class Ex01(Drill):
    """What does this storage cost? ★"""
    tasks = ("4.1",)
    TB = (1024, 1_048_576)   # 1 TB as 1024 objects of 1 GiB

    def test_a_month_in_each_class(self):
        want = {"STANDARD": 23.55, "STANDARD_IA": 12.8, "ONEZONE_IA": 10.24, "GLACIER_IR": 12.29, "GLACIER": 11.06, "DEEP_ARCHIVE": 6.08}
        for cls, cost in want.items():
            with self.subTest(cls=cls):
                self.assertEqual(storage_cost(cls, *self.TB, 30), cost)

    def test_a_year_in_each_class(self):
        want = {"STANDARD": 286.55, "STANDARD_IA": 155.73, "GLACIER_IR": 49.83, "GLACIER": 44.85, "DEEP_ARCHIVE": 12.33}
        for cls, cost in want.items():
            with self.subTest(cls=cls):
                self.assertEqual(storage_cost(cls, *self.TB, 365), cost, "days / 30 x the monthly rate")

    def test_deleting_early_still_pays_the_minimum_duration(self):
        self.assertEqual(storage_cost("STANDARD", *self.TB, 5), 3.93, "Standard has no minimum: 5 days cost 5 days")
        for cls in ("STANDARD_IA", "ONEZONE_IA", "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE"):
            with self.subTest(cls=cls):
                self.assertEqual(storage_cost(cls, *self.TB, 5), storage_cost(cls, *self.TB, MIN_DAYS[cls]),
                                 f"{cls} bills at least {MIN_DAYS[cls]} days even if you delete after 5")
        self.assertEqual(storage_cost("STANDARD_IA", *self.TB, 45), 19.2, "past the minimum, the real days count")

    def test_tiny_objects_are_billed_at_the_minimum_size(self):
        self.assertEqual(storage_cost("STANDARD", 1_000_000, 10, 30), 0.22)
        self.assertEqual(storage_cost("STANDARD_IA", 1_000_000, 10, 30), 1.53, "10 KB objects bill as 128 KB in Standard-IA")
        self.assertEqual(storage_cost("STANDARD_IA", 1_000_000, 10, 30), storage_cost("STANDARD_IA", 1_000_000, 128, 30))
        self.assertEqual(storage_cost("GLACIER_IR", 1_000_000, 10, 30), 1.46)
        self.assertEqual(storage_cost("GLACIER", 1_000_000, 10, 90), 0.1, "Glacier Flexible has no minimum size here")
        self.assertEqual(storage_cost("STANDARD_IA", 1_000_000, 200, 30), 2.38, "above the minimum, the real size counts")

    def test_retrieval_fees(self):
        self.assertEqual(storage_cost("STANDARD", *self.TB, 365, 100), 286.55, "Standard has no retrieval fee")
        self.assertEqual(storage_cost("STANDARD_IA", *self.TB, 365, 100), 156.73)
        self.assertEqual(storage_cost("GLACIER_IR", *self.TB, 365, 100), 52.83)
        self.assertEqual(storage_cost("GLACIER", *self.TB, 365, 100), 45.85)
        self.assertEqual(storage_cost("DEEP_ARCHIVE", *self.TB, 365, 100), 14.33)

    def test_bulk_retrieval(self):
        self.assertEqual(storage_cost("GLACIER", *self.TB, 100, 100, retrieval="bulk"), 12.29, "bulk from Flexible Retrieval is free")
        self.assertEqual(storage_cost("DEEP_ARCHIVE", *self.TB, 200, 100, retrieval="bulk"), 7.01)
        self.assertEqual(storage_cost("DEEP_ARCHIVE", *self.TB, 200, 100), 8.76, "standard retrieval is the default")
        self.assertEqual(storage_cost("STANDARD_IA", *self.TB, 30, 100, retrieval="bulk"), 13.8, "bulk only matters for the archive classes")

    def test_the_price_argument_is_used(self):
        custom = dict(PRICES, s3_standard_per_gb_month=0.5)
        self.assertEqual(storage_cost("STANDARD", 10, 1_048_576, 30, price=custom), 5.0)

    def test_storage_cost_rejects_bad_inputs(self):
        for call in (lambda: storage_cost("GLACIER_FLEX", 1, 1, 1), lambda: storage_cost("STANDARD", -1, 1, 1),
                     lambda: storage_cost("STANDARD", 1, -1, 1), lambda: storage_cost("STANDARD", 1, 1, -1),
                     lambda: storage_cost("STANDARD", 1, 1, 1, -1), lambda: storage_cost("GLACIER", 1, 1, 1, retrieval="expedited")):
            with self.subTest():
                with self.assertRaises(ValueError):
                    call()

    def test_a_year_kept_and_read_once_wants_an_archive_class(self):
        self.assertEqual(cheapest_class(*self.TB, 365, 0), ("GLACIER_IR", 49.83))
        self.assertEqual(cheapest_class(*self.TB, 365, 0, millisecond_access=False), ("DEEP_ARCHIVE", 12.33))
        self.assertEqual(cheapest_class(*self.TB, 365, 1024), ("GLACIER_IR", 80.55), "reading it all back adds 3 cents per GB")
        self.assertEqual(cheapest_class(*self.TB, 365, 1024, millisecond_access=False), ("DEEP_ARCHIVE", 32.81))

    def test_hot_or_tiny_data_stays_in_standard(self):
        self.assertEqual(cheapest_class(1_000_000, 10, 365), ("STANDARD", 2.67), "tiny objects: the 128 KB minimum kills the IA classes")
        self.assertEqual(cheapest_class(*self.TB, 10, 0, single_az_ok=True), ("STANDARD", 7.85), "10 days: the 30-day minimum is paid in full")
        self.assertEqual(cheapest_class(1000, 10, 365, 0)[0], "STANDARD")

    def test_one_month_data_is_cheapest_in_glacier_instant(self):
        self.assertEqual(cheapest_class(*self.TB, 30, 0), ("GLACIER_IR", 12.29), "Glacier IR beats Standard-IA, even at 30 days")

    def test_one_zone_needs_permission(self):
        self.assertEqual(cheapest_class(*self.TB, 30, 0, single_az_ok=True), ("ONEZONE_IA", 10.24))
        self.assertEqual(cheapest_class(*self.TB, 30, 0)[0], "GLACIER_IR", "without single_az_ok, One Zone-IA is out")
        self.assertEqual(cheapest_class(*self.TB, 60, 500, single_az_ok=True), ("ONEZONE_IA", 25.48))
        self.assertEqual(cheapest_class(*self.TB, 365, 10000, single_az_ok=True), ("ONEZONE_IA", 224.59))

    def test_cheapest_uses_the_price_argument(self):
        custom = dict(PRICES, s3_standard_per_gb_month=0.0001)
        self.assertEqual(cheapest_class(*self.TB, 365, 0, price=custom)[0], "STANDARD")


# ── Exercise 02 ★: When does this object move? ───────────────────────
"""
A lifecycle configuration is a list of rules in the S3 API shape (what boto3 put_bucket_lifecycle_configuration
takes). A rule is a dict with these keys (all optional except Status and at least one action):
    "ID": str                       "Status": "Enabled" or "Disabled"        "Filter": {...}   (missing means {})
    "Transitions": [{"Days": 30, "StorageClass": "STANDARD_IA"}, ...]
    "Expiration": {"Days": 365}  or  {"ExpiredObjectDeleteMarker": True}
    "NoncurrentVersionTransitions": [{"NoncurrentDays": 30, "StorageClass": "GLACIER_IR"}, ...]
    "NoncurrentVersionExpiration": {"NoncurrentDays": 90, "NewerNoncurrentVersions": 3}
    "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7}
A Filter is ONE of: {"Prefix": "logs/"}, {"Tag": {"Key": k, "Value": v}}, {"ObjectSizeGreaterThan": n},
{"ObjectSizeLessThan": n} or {"And": {"Prefix": ..., "Tags": [{"Key": k, "Value": v}], "ObjectSizeGreaterThan": n,
"ObjectSizeLessThan": n}}. Two of them side by side is not allowed: combine them inside "And". Sizes are bytes.
WATERFALL = STANDARD, STANDARD_IA, INTELLIGENT_TIERING, ONEZONE_IA, GLACIER_IR, GLACIER, DEEP_ARCHIVE (given).
Objects only move DOWN it, and not every step is allowed. ALLOWED_NEXT (given) lists, for each class, the classes
it may move to. Deep Archive is one-way.
validate(rules) -> None
    Raise ValueError (the message names the rule and the constraint) for:
      more than 1000 rules; an ID longer than 255 characters or used twice; a Status that is not Enabled/Disabled;
      a rule with no action at all; a Filter with two of its parts side by side (not in "And");
      a transition to a class that is not in the waterfall or is STANDARD, or one the previous class may not
      move to (start from STANDARD); transition days (or NoncurrentDays) that do not increase;
      the TWO-STEP MINIMUM: a later transition must come at least the previous class's MIN_DAYS after the earlier
      one (Glacier IR at day 4 means Deep Archive no earlier than day 94; Standard-IA at 30 means Glacier no earlier
      than 60), because an object that leaves a class early is still billed for the minimum;
      Expiration with both or neither of Days and ExpiredObjectDeleteMarker; Expiration Days that is not later than
      every transition; ExpiredObjectDeleteMarker or AbortIncompleteMultipartUpload on a rule whose filter uses a
      tag; NewerNoncurrentVersions without NoncurrentDays, outside 1 to 100, or in a rule with no "Filter" key;
      a NoncurrentVersionExpiration that is not later than every noncurrent transition.
    Apply the waterfall, increasing-days and two-step checks to NoncurrentVersionTransitions too.
    Do NOT require 30 days before Standard-IA: the course's research could not confirm that old rule.
current_class(rules, key, age_days, size_bytes, tags=None) -> str
    The storage class of a CURRENT object `age_days` old once the rules have run: a class name or "EXPIRED".
    Only Enabled rules count. A rule applies when its Filter matches: the key starts with the Prefix; every filter
    tag is on the object with that value; size_bytes is STRICTLY greater than ObjectSizeGreaterThan and STRICTLY
    less than ObjectSizeLessThan. (An empty Filter matches everything.)
    A transition counts once age_days >= its Days. If several rules apply: expiration wins over any transition
    (Expiration Days <= age_days -> "EXPIRED"); among transitions, the one furthest down the waterfall wins.
    SMALL OBJECTS: an object under 128 KB (131,072 bytes) is not transitioned unless the rule's Filter has an
    object-size part. It still expires. No transition reached -> "STANDARD".
noncurrent_fate(rules, key, days_noncurrent, newer_noncurrent=0, size_bytes=1 << 20, tags=None) -> str
    Same idea for a NONCURRENT version, `days_noncurrent` days after it stopped being current, when
    `newer_noncurrent` newer noncurrent versions of the same key exist. "DELETED" when a NoncurrentVersionExpiration
    applies (days_noncurrent >= its NoncurrentDays and, if it has NewerNoncurrentVersions, newer_noncurrent >= that
    number); otherwise the furthest NoncurrentVersionTransitions class reached, else "STANDARD". The same filter and
    small-object rules apply.
Example (a logs rule):
    LOGS = [{"ID": "logs", "Status": "Enabled", "Filter": {"Prefix": "logs/"},
             "Transitions": [{"Days": 30, "StorageClass": "STANDARD_IA"}, {"Days": 90, "StorageClass": "GLACIER"}],
             "Expiration": {"Days": 365}}]
    current_class(LOGS, "logs/a.gz", 45, 1 << 20) == "STANDARD_IA"      current_class(LOGS, "logs/a.gz", 400, 1 << 20) == "EXPIRED"
    current_class(LOGS, "logs/a.gz", 45, 1000) == "STANDARD"           # tiny: not transitioned
Why? Lifecycle rules are how you stop paying Standard prices for old data, but every move has rules: the
waterfall, minimum durations that make a quick second hop pointless, and small objects that cost more in
IA than they save. AWS runs lifecycle in the background; these functions give the state once the rule has run.
Hint: write a helper that flattens a Filter (look inside "And") and one that says whether a rule applies;
      max(classes, key=WATERFALL.index) finds the furthest class.
"""
WATERFALL = ("STANDARD", "STANDARD_IA", "INTELLIGENT_TIERING", "ONEZONE_IA", "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE")
ALLOWED_NEXT = {
    "STANDARD": WATERFALL[1:],
    "STANDARD_IA": ("INTELLIGENT_TIERING", "ONEZONE_IA", "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE"),
    "INTELLIGENT_TIERING": ("ONEZONE_IA", "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE"),
    "ONEZONE_IA": ("GLACIER", "DEEP_ARCHIVE"),
    "GLACIER_IR": ("GLACIER", "DEEP_ARCHIVE"),
    "GLACIER": ("DEEP_ARCHIVE",),
    "DEEP_ARCHIVE": (),
}


def validate(rules):
    raise NotImplementedError  # YOUR CODE


def current_class(rules, key, age_days, size_bytes, tags=None):
    raise NotImplementedError  # YOUR CODE


def noncurrent_fate(rules, key, days_noncurrent, newer_noncurrent=0, size_bytes=1 << 20, tags=None):
    raise NotImplementedError  # YOUR CODE


class Ex02(Drill):
    """When does this object move? ★"""
    tasks = ("4.1", "1.3")
    MIB = 1 << 20
    LOGS = [{"ID": "logs", "Status": "Enabled", "Filter": {"Prefix": "logs/"},
             "Transitions": [{"Days": 30, "StorageClass": "STANDARD_IA"}, {"Days": 90, "StorageClass": "GLACIER"}],
             "Expiration": {"Days": 365}}]
    VERSIONED = [{"ID": "old-versions", "Status": "Enabled", "Filter": {},
                  "NoncurrentVersionTransitions": [{"NoncurrentDays": 30, "StorageClass": "GLACIER_IR"}],
                  "NoncurrentVersionExpiration": {"NoncurrentDays": 90, "NewerNoncurrentVersions": 3}}]

    def rule(self, **parts):
        return dict({"ID": "r", "Status": "Enabled", "Filter": {}}, **parts)

    def test_good_rules_are_accepted(self):
        good = [self.LOGS, self.VERSIONED,
                [self.rule(Transitions=[{"Days": 4, "StorageClass": "GLACIER_IR"}, {"Days": 94, "StorageClass": "DEEP_ARCHIVE"}])],
                [self.rule(Transitions=[{"Days": 30, "StorageClass": "STANDARD_IA"}, {"Days": 60, "StorageClass": "GLACIER"}])],
                [self.rule(Filter={"Prefix": "tmp/"}, Expiration={"ExpiredObjectDeleteMarker": True})],
                [self.rule(Filter={"And": {"Prefix": "a/", "Tags": [{"Key": "k", "Value": "v"}]}}, Expiration={"Days": 30})],
                [self.rule(AbortIncompleteMultipartUpload={"DaysAfterInitiation": 7})],
                [self.rule(Status="Disabled", Expiration={"Days": 1})],
                [{"ID": "x", "Status": "Enabled", "Expiration": {"Days": 10}}]]
        for rules in good:
            with self.subTest(rules=rules):
                validate(rules)

    def test_validation_status_actions_and_ids(self):
        bad = {
            "bad status": [self.rule(Status="On", Expiration={"Days": 30})],
            "no action": [self.rule()],
            "duplicate ids": [self.rule(Expiration={"Days": 30}), self.rule(Expiration={"Days": 60})],
            "id too long": [self.rule(ID="x" * 256, Expiration={"Days": 30})],
            "too many rules": [self.rule(ID=f"r{i}", Expiration={"Days": 30}) for i in range(1001)],
            "filter parts side by side": [self.rule(Filter={"Prefix": "a/", "Tag": {"Key": "k", "Value": "v"}}, Expiration={"Days": 30})],
        }
        for label, rules in bad.items():
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    validate(rules)

    def test_validation_waterfall(self):
        def t(*steps):
            return [self.rule(Transitions=[{"Days": d, "StorageClass": c} for c, d in steps])]
        bad = {
            "back up the waterfall": t(("GLACIER", 90), ("STANDARD_IA", 200)),
            "to Standard": t(("STANDARD", 30)),
            "unknown class": t(("BOGUS", 30)),
            "out of Deep Archive": t(("DEEP_ARCHIVE", 100), ("GLACIER", 400)),
            "One Zone-IA to Standard-IA": t(("ONEZONE_IA", 30), ("STANDARD_IA", 90)),
            "days that do not increase": t(("STANDARD_IA", 60), ("GLACIER", 60)),
            "days that go down": t(("STANDARD_IA", 60), ("GLACIER", 40)),
        }
        for label, rules in bad.items():
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    validate(rules)

    def test_validation_two_step_minimum(self):
        def t(*steps):
            return [self.rule(Transitions=[{"Days": d, "StorageClass": c} for c, d in steps])]
        for label, rules in {"Glacier IR at 4, Deep Archive at 50": t(("GLACIER_IR", 4), ("DEEP_ARCHIVE", 50)),
                             "Standard-IA at 30, Glacier at 40": t(("STANDARD_IA", 30), ("GLACIER", 40)),
                             "Glacier at 100, Deep Archive at 150": t(("GLACIER", 100), ("DEEP_ARCHIVE", 150))}.items():
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    validate(rules)
        validate(t(("GLACIER", 100), ("DEEP_ARCHIVE", 190)))
        with self.assertRaises(ValueError):
            validate([self.rule(NoncurrentVersionTransitions=[{"NoncurrentDays": 4, "StorageClass": "GLACIER_IR"},
                                                              {"NoncurrentDays": 50, "StorageClass": "DEEP_ARCHIVE"}])])
        with self.assertRaises(ValueError):
            validate([self.rule(NoncurrentVersionTransitions=[{"NoncurrentDays": 90, "StorageClass": "GLACIER"},
                                                              {"NoncurrentDays": 120, "StorageClass": "STANDARD_IA"}])])

    def test_validation_expiration(self):
        bad = {
            "expires before it transitions": [self.rule(Transitions=[{"Days": 30, "StorageClass": "STANDARD_IA"}], Expiration={"Days": 20})],
            "expires the day it transitions": [self.rule(Transitions=[{"Days": 30, "StorageClass": "STANDARD_IA"}], Expiration={"Days": 30})],
            "both kinds of expiration": [self.rule(Expiration={"Days": 30, "ExpiredObjectDeleteMarker": True})],
            "neither kind of expiration": [self.rule(Expiration={})],
            "delete marker with a tag filter": [self.rule(Filter={"Tag": {"Key": "k", "Value": "v"}}, Expiration={"ExpiredObjectDeleteMarker": True})],
            "abort multipart with a tag filter": [self.rule(Filter={"And": {"Prefix": "a/", "Tags": [{"Key": "k", "Value": "v"}]}},
                                                            AbortIncompleteMultipartUpload={"DaysAfterInitiation": 7})],
        }
        for label, rules in bad.items():
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    validate(rules)

    def test_validation_noncurrent_versions(self):
        trans = [{"NoncurrentDays": 30, "StorageClass": "GLACIER_IR"}]
        bad = {
            "newer count without days": [self.rule(NoncurrentVersionExpiration={"NewerNoncurrentVersions": 3})],
            "newer count of 0": [self.rule(NoncurrentVersionExpiration={"NoncurrentDays": 30, "NewerNoncurrentVersions": 0})],
            "newer count of 101": [self.rule(NoncurrentVersionExpiration={"NoncurrentDays": 30, "NewerNoncurrentVersions": 101})],
            "newer count with no Filter element": [{"ID": "x", "Status": "Enabled",
                                                    "NoncurrentVersionExpiration": {"NoncurrentDays": 30, "NewerNoncurrentVersions": 3}}],
            "deleted before it transitions": [self.rule(NoncurrentVersionTransitions=trans, NoncurrentVersionExpiration={"NoncurrentDays": 30})],
        }
        for label, rules in bad.items():
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    validate(rules)
        validate([self.rule(NoncurrentVersionExpiration={"NoncurrentDays": 30, "NewerNoncurrentVersions": 100})])

    def test_a_logs_rule_by_age(self):
        want = {0: "STANDARD", 29: "STANDARD", 30: "STANDARD_IA", 89: "STANDARD_IA", 90: "GLACIER", 364: "GLACIER", 365: "EXPIRED", 1000: "EXPIRED"}
        for age, cls in want.items():
            with self.subTest(age=age):
                self.assertEqual(current_class(self.LOGS, "logs/a.gz", age, self.MIB), cls)

    def test_a_filter_that_does_not_match_changes_nothing(self):
        self.assertEqual(current_class(self.LOGS, "images/a.png", 1000, self.MIB), "STANDARD")
        self.assertEqual(current_class(self.LOGS, "xlogs/a.gz", 100, self.MIB), "STANDARD", "a prefix must match from the start of the key")

    def test_small_objects_are_not_transitioned(self):
        self.assertEqual(current_class(self.LOGS, "logs/a", 100, 100 * 1024), "STANDARD", "100 KB is under the 128 KB default minimum")
        self.assertEqual(current_class(self.LOGS, "logs/a", 100, 131_071), "STANDARD")
        self.assertEqual(current_class(self.LOGS, "logs/a", 100, 131_072), "GLACIER", "exactly 128 KB is big enough")
        self.assertEqual(current_class(self.LOGS, "logs/a", 400, 100), "EXPIRED", "small objects still expire")

    def test_an_object_size_filter_lets_small_objects_move(self):
        small = [self.rule(Filter={"ObjectSizeLessThan": 100_000}, Transitions=[{"Days": 30, "StorageClass": "STANDARD_IA"}])]
        self.assertEqual(current_class(small, "k", 40, 50_000), "STANDARD_IA", "the size filter explicitly asks for small objects")
        self.assertEqual(current_class(small, "k", 40, 200_000), "STANDARD", "too big for the filter")
        self.assertEqual(current_class(small, "k", 40, 100_000), "STANDARD", "ObjectSizeLessThan is strict")
        big = [self.rule(Filter={"And": {"Prefix": "v/", "ObjectSizeGreaterThan": 1_000_000}},
                         Transitions=[{"Days": 30, "StorageClass": "STANDARD_IA"}])]
        self.assertEqual(current_class(big, "v/a", 40, 1_000_001), "STANDARD_IA")
        self.assertEqual(current_class(big, "v/a", 40, 1_000_000), "STANDARD", "ObjectSizeGreaterThan is strict")
        self.assertEqual(current_class(big, "w/a", 40, 5_000_000), "STANDARD", "prefix AND size must both match")

    def test_tag_filters(self):
        single = [self.rule(Filter={"Tag": {"Key": "archive", "Value": "yes"}}, Transitions=[{"Days": 30, "StorageClass": "GLACIER_IR"}])]
        self.assertEqual(current_class(single, "k", 40, self.MIB, {"archive": "yes", "team": "x"}), "GLACIER_IR")
        self.assertEqual(current_class(single, "k", 40, self.MIB, {"archive": "no"}), "STANDARD")
        self.assertEqual(current_class(single, "k", 40, self.MIB), "STANDARD")
        both = [self.rule(Filter={"And": {"Prefix": "a/", "Tags": [{"Key": "k1", "Value": "v1"}, {"Key": "k2", "Value": "v2"}]}},
                          Transitions=[{"Days": 30, "StorageClass": "GLACIER_IR"}])]
        self.assertEqual(current_class(both, "a/x", 40, self.MIB, {"k1": "v1", "k2": "v2"}), "GLACIER_IR")
        self.assertEqual(current_class(both, "a/x", 40, self.MIB, {"k1": "v1"}), "STANDARD", "every tag must match")
        self.assertEqual(current_class(both, "b/x", 40, self.MIB, {"k1": "v1", "k2": "v2"}), "STANDARD")

    def test_disabled_rules_do_nothing(self):
        off = [dict(self.LOGS[0], Status="Disabled")]
        self.assertEqual(current_class(off, "logs/a.gz", 1000, self.MIB), "STANDARD")

    def test_expiration_beats_transition_and_the_furthest_transition_wins(self):
        a = self.rule(ID="a", Transitions=[{"Days": 30, "StorageClass": "GLACIER"}])
        b = self.rule(ID="b", Expiration={"Days": 60})
        for rules in ([a, b], [b, a]):
            self.assertEqual(current_class(rules, "k", 59, self.MIB), "GLACIER")
            self.assertEqual(current_class(rules, "k", 60, self.MIB), "EXPIRED", "expiration beats a transition, whatever the rule order")
        c = self.rule(ID="c", Transitions=[{"Days": 30, "StorageClass": "STANDARD_IA"}])
        d = self.rule(ID="d", Transitions=[{"Days": 30, "StorageClass": "GLACIER_IR"}])
        for rules in ([c, d], [d, c]):
            self.assertEqual(current_class(rules, "k", 30, self.MIB), "GLACIER_IR", "two rules at once: the furthest class wins")

    def test_noncurrent_versions(self):
        for days, newer, want in ((10, 0, "STANDARD"), (30, 0, "GLACIER_IR"), (89, 5, "GLACIER_IR"), (90, 2, "GLACIER_IR"),
                                  (90, 3, "DELETED"), (400, 0, "GLACIER_IR"), (400, 10, "DELETED"), (45, 50, "GLACIER_IR")):
            with self.subTest(days=days, newer=newer):
                self.assertEqual(noncurrent_fate(self.VERSIONED, "k", days, newer), want,
                                 "delete only when the version is old enough AND at least 3 newer noncurrent versions exist")

    def test_noncurrent_expiration_without_a_count_is_by_age_alone(self):
        rules = [self.rule(NoncurrentVersionExpiration={"NoncurrentDays": 90})]
        self.assertEqual(noncurrent_fate(rules, "k", 89), "STANDARD")
        self.assertEqual(noncurrent_fate(rules, "k", 90), "DELETED")

    def test_noncurrent_small_versions_and_filters(self):
        self.assertEqual(noncurrent_fate(self.VERSIONED, "k", 40, size_bytes=1000), "STANDARD", "small versions are not transitioned")
        self.assertEqual(noncurrent_fate(self.VERSIONED, "k", 100, 5, size_bytes=1000), "DELETED", "but they can still be deleted")
        scoped = [self.rule(Filter={"Prefix": "docs/"}, NoncurrentVersionTransitions=[{"NoncurrentDays": 30, "StorageClass": "GLACIER_IR"}])]
        self.assertEqual(noncurrent_fate(scoped, "docs/a", 40), "GLACIER_IR")
        self.assertEqual(noncurrent_fate(scoped, "other/a", 40), "STANDARD")


# ── Exercise 03 ★: Pick the volume ───────────────────────────────────
"""
An EBS volume lives in one AZ and is attached to an instance. Pick the type and check the limits.
PRICES (given) are illustrative numbers from prices.toml. Types: gp3, gp2, io2, st1, sc1 (VOLUME_TYPES).
Limits (given as SIZE_GIB, in GiB): gp3 1 to 65,536 (64 TiB); gp2 1 to 16,384; io2 4 to 65,536;
st1 and sc1 125 to 16,384. They are HDDs: never boot volumes, and big-sequential-only.
gp2_iops(size_gib) -> int
    gp2 gives 3 IOPS per GiB, at least 100 and at most 16,000 (reached at 5,334 GiB). ValueError outside its size range.
gp3_config(size_gib, iops=None, throughput=None) -> {"iops": ..., "throughput": ...}
    gp3 includes 3,000 IOPS and 125 MiB/s at ANY size, free. None means that baseline. Provisioning less is a ValueError.
    Above the baseline: IOPS at most 500 per GiB (so 10 GiB allows 5,000) and 80,000 in total; throughput at most
    0.25 MiB/s per provisioned IOPS and 2,000 MiB/s in total. ValueError for any limit broken or a size out of range.
monthly_cost(volume_type, size_gib, iops=None, throughput=None, price=PRICES) -> float     (2 decimal places)
    gp3: size x ebs_gp3_per_gb_month, PLUS ebs_gp3_per_iops_month for each IOPS above 3,000, PLUS
         ebs_gp3_per_mibps_month for each MiB/s above 125. The baseline is free.
    gp2, st1, sc1: size x their per-GB price; iops or throughput given -> ValueError (nothing to provision).
    io2: size x ebs_io2_per_gb_month, PLUS provisioned IOPS: ebs_io2_per_iops_month_first_32k for the first 32,000,
         ebs_io2_per_iops_month_32k_to_64k for the next 32,000. `iops` is required, at most 1,000 per GiB and 256,000;
         above 64,000 has no price here -> ValueError. throughput above 4,000 -> ValueError.
    An unknown type (io1 is left out) or a size out of range -> ValueError.
choose_volume(iops=0, throughput_mibs=0, *, boot=False, multi_attach=False, sequential=False, rarely_accessed=False) -> str
    The cheapest type that does the job, by these rules in order:
      1. multi_attach with boot -> ValueError (a Multi-Attach volume cannot be a boot volume).
         Negative iops or throughput -> ValueError. More than 256,000 IOPS or 4,000 MiB/s -> ValueError (no EBS volume does).
      2. Multi-Attach (only io1/io2 support it), or iops above gp3's 80,000, or throughput above gp3's 2,000 -> "io2".
      3. sequential and not boot: "sc1" if rarely_accessed and the need fits sc1 (250 IOPS and 250 MiB/s),
         else "st1" if it fits st1 (500 IOPS and 500 MiB/s).
      4. Otherwise "gp3".
Examples:
    gp2_iops(1000) == 3000     gp3_config(100) == {"iops": 3000, "throughput": 125}     monthly_cost("gp3", 100) == 8.0
    monthly_cost("gp3", 1000, 6000) == 95.0      monthly_cost("io2", 100, 5000) == 337.5      choose_volume(iops=100000) == "io2"
Why? gp3 is cheaper than gp2 and its speed is independent of its size, so gp3 is the default. io2 is for
the database that needs more than gp3 can give, or a volume shared by two instances. HDDs are for big
sequential reads (logs, data warehouses) and cold data, never for boot or random I/O.
Hint: gp3_config does all the validating; monthly_cost for gp3 calls it and charges only for the part above the baseline.
"""
SIZE_GIB = {"gp3": (1, 65_536), "gp2": (1, 16_384), "io2": (4, 65_536), "st1": (125, 16_384), "sc1": (125, 16_384)}
VOLUME_TYPES = tuple(SIZE_GIB)


def gp2_iops(size_gib):
    raise NotImplementedError  # YOUR CODE


def gp3_config(size_gib, iops=None, throughput=None):
    raise NotImplementedError  # YOUR CODE


def monthly_cost(volume_type, size_gib, iops=None, throughput=None, price=PRICES):
    raise NotImplementedError  # YOUR CODE


def choose_volume(iops=0, throughput_mibs=0, *, boot=False, multi_attach=False, sequential=False, rarely_accessed=False):
    raise NotImplementedError  # YOUR CODE


class Ex03(Drill):
    """Pick the volume ★"""
    tasks = ("3.1", "4.1")

    def test_gp2_iops(self):
        for size, want in {1: 100, 33: 100, 34: 102, 1000: 3000, 5333: 15999, 5334: 16000, 6000: 16000, 16384: 16000}.items():
            with self.subTest(size=size):
                self.assertEqual(gp2_iops(size), want, "3 IOPS per GiB, never below 100 or above 16,000")

    def test_gp2_rejects_bad_sizes(self):
        for size in (0, 16385):
            with self.subTest(size=size):
                with self.assertRaises(ValueError):
                    gp2_iops(size)

    def test_gp3_baseline_is_free_at_any_size(self):
        self.assertEqual(gp3_config(1), {"iops": 3000, "throughput": 125})
        self.assertEqual(gp3_config(100), {"iops": 3000, "throughput": 125})
        self.assertEqual(gp3_config(100, 3000, 125), {"iops": 3000, "throughput": 125})
        self.assertEqual(gp3_config(1000, 16000, 1000), {"iops": 16000, "throughput": 1000})
        self.assertEqual(gp3_config(10, 5000), {"iops": 5000, "throughput": 125}, "500 IOPS per GiB: 10 GiB allows 5,000")
        self.assertEqual(gp3_config(200, 3000, 750), {"iops": 3000, "throughput": 750}, "0.25 MiB/s per IOPS: 3,000 allows 750")

    def test_gp3_limits(self):
        bad = {"size 0": (0,), "size over 64 TiB": (65_537,), "below the IOPS baseline": (100, 2999),
               "below the throughput baseline": (100, None, 124), "over 80,000 IOPS": (1000, 80_001),
               "more than 500 IOPS per GiB": (10, 5001), "throughput over 0.25 per IOPS": (200, 3000, 751),
               "over 2,000 MiB/s": (1000, 80_000, 2001)}
        for label, args in bad.items():
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    gp3_config(*args)
        self.assertEqual(gp3_config(1000, 80_000, 2000), {"iops": 80_000, "throughput": 2000})

    def test_gp3_costs(self):
        self.assertEqual(monthly_cost("gp3", 100), 8.0)
        self.assertEqual(monthly_cost("gp3", 1000), 80.0, "the free baseline is never charged")
        self.assertEqual(monthly_cost("gp3", 1000, 6000), 95.0, "only the 3,000 IOPS above the baseline are charged")
        self.assertEqual(monthly_cost("gp3", 1000, 6000, 500), 117.5, "plus 375 MiB/s above 125")
        self.assertEqual(monthly_cost("gp3", 500, 16000, 1000), 157.5)
        self.assertEqual(monthly_cost("gp3", 100, 3000, 125), 8.0)

    def test_other_volume_costs(self):
        self.assertEqual(monthly_cost("gp2", 1000), 100.0)
        self.assertEqual(monthly_cost("st1", 1000), 45.0)
        self.assertEqual(monthly_cost("sc1", 1000), 15.0)
        self.assertEqual(monthly_cost("io2", 100, 5000), 337.5)
        self.assertEqual(monthly_cost("io2", 1000, 50000), 3033.0, "32,000 IOPS at the first rate, 18,000 at the second")
        self.assertEqual(monthly_cost("io2", 2000, 64000), 3802.0)

    def test_gp3_beats_gp2_for_the_same_speed(self):
        for size in (100, 500, 1000, 3000, 5334):
            with self.subTest(size=size):
                speed = gp2_iops(size)
                self.assertLess(monthly_cost("gp3", size, max(3000, speed)), monthly_cost("gp2", size),
                                f"{size} GiB: gp3 gives the same {speed} IOPS for less money")
        self.assertEqual(monthly_cost("gp3", 5334, 16000), 491.72)
        self.assertEqual(monthly_cost("gp2", 5334), 533.4)

    def test_cost_rejects_bad_inputs(self):
        calls = {"gp2 with iops": lambda: monthly_cost("gp2", 100, 3000), "st1 with throughput": lambda: monthly_cost("st1", 500, None, 100),
                 "st1 under 125 GiB": lambda: monthly_cost("st1", 124), "io2 without iops": lambda: monthly_cost("io2", 100),
                 "io2 under 4 GiB": lambda: monthly_cost("io2", 3, 100), "io2 over 1,000 IOPS per GiB": lambda: monthly_cost("io2", 10, 10001),
                 "io2 above the priced range": lambda: monthly_cost("io2", 1000, 70000), "io2 over 4,000 MiB/s": lambda: monthly_cost("io2", 100, 5000, 4001),
                 "unknown type": lambda: monthly_cost("io1", 100, 1000), "gp3 over the ratio": lambda: monthly_cost("gp3", 10, 6000)}
        for label, call in calls.items():
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    call()

    def test_the_price_argument_is_used(self):
        custom = dict(PRICES, ebs_gp3_per_gb_month=1.0, ebs_gp3_per_iops_month=0.0, ebs_gp3_per_mibps_month=0.0)
        self.assertEqual(monthly_cost("gp3", 10, 5000, 500, price=custom), 10.0)

    def test_choose_volume_default_and_high_end(self):
        self.assertEqual(choose_volume(), "gp3")
        self.assertEqual(choose_volume(iops=6000, throughput_mibs=500), "gp3")
        self.assertEqual(choose_volume(iops=80_000, throughput_mibs=2000), "gp3", "gp3's own maximum is still gp3")
        self.assertEqual(choose_volume(iops=80_001), "io2")
        self.assertEqual(choose_volume(iops=100_000), "io2")
        self.assertEqual(choose_volume(throughput_mibs=2001), "io2")
        self.assertEqual(choose_volume(iops=100, multi_attach=True), "io2", "only io1/io2 can be attached to several instances")

    def test_choose_volume_hdds(self):
        self.assertEqual(choose_volume(iops=300, throughput_mibs=400, sequential=True), "st1")
        self.assertEqual(choose_volume(iops=100, throughput_mibs=200, sequential=True, rarely_accessed=True), "sc1")
        self.assertEqual(choose_volume(iops=400, throughput_mibs=500, sequential=True, rarely_accessed=True), "st1", "too fast for sc1")
        self.assertEqual(choose_volume(iops=600, throughput_mibs=100, sequential=True), "gp3", "too many IOPS for an HDD")
        self.assertEqual(choose_volume(iops=300, throughput_mibs=400), "gp3", "random access: no HDD")
        self.assertEqual(choose_volume(iops=100, throughput_mibs=200, sequential=True, rarely_accessed=True, boot=True), "gp3",
                         "HDDs cannot be boot volumes")

    def test_choose_volume_rejects_the_impossible(self):
        for kwargs in ({"iops": 300_000}, {"throughput_mibs": 4001}, {"multi_attach": True, "boot": True}, {"iops": -1}, {"throughput_mibs": -5}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    choose_volume(**kwargs)


# ── Exercise 04 ★: Big objects, busy buckets ─────────────────────────
"""
S3 limits (given): MIB = 1024 x 1024 bytes; a single PUT is at most 5 GiB; a multipart upload has parts of
5 MiB to 5 GiB (only the LAST part may be smaller than 5 MiB), at most 10,000 parts, and an object is at most 50 TB
(50 x 10^12 bytes, MAX_OBJECT_BYTES). AWS suggests multipart once an object passes 100 MiB. S3 serves at least
5,500 GET/HEAD and 3,500 PUT/COPY/POST/DELETE requests per second PER PREFIX.
plan_parts(object_bytes, part_mib=None) -> {"part_bytes", "parts", "last_part_bytes", "multipart"}
    Split an upload into parts of part_mib MiB. parts = ceil(object_bytes / part_bytes); the last part holds
    whatever is left (a full part when it divides exactly). "multipart" is True when object_bytes is MORE than
    100 MiB or more than 5 GiB (the single-PUT limit). part_mib None picks the smallest whole-MiB part size that is
    at least 5 MiB and keeps the parts at 10,000 or fewer.
    ValueError for: object_bytes of 0 or less; more than MAX_OBJECT_BYTES; a part_mib below 5 or above 5,120 (5 GiB);
    more than 10,000 parts.
prefixes_needed(gets_per_second, puts_per_second) -> int
    The fewest prefixes that carry the load: max(ceil(gets / 5500), ceil(puts / 3500)), at least 1. Negative rates -> ValueError.
Examples:
    plan_parts(10 * MIB) == {"part_bytes": 5 * MIB, "parts": 2, "last_part_bytes": 5 * MIB, "multipart": False}
    plan_parts(11 * MIB)["parts"] == 3        plan_parts(1024 * MIB * 1024)["part_bytes"] == 105 * MIB      # 1 TiB
    prefixes_needed(11_000, 3_500) == 2
Why? Parts are the unit of retry and of parallelism: lose a part, resend only that part. The 10,000-part cap makes the
part size grow with the object. And a hot bucket is scaled by spreading keys over prefixes, not by buying anything.
Hint: math.ceil; the automatic part size is max(5, ceil(object_bytes / (10_000 x MIB))).
"""
import math  # noqa: E402,F401

MIB = 1024 ** 2
GIB = 1024 ** 3
MAX_OBJECT_BYTES = 50 * 10 ** 12


def plan_parts(object_bytes, part_mib=None):
    raise NotImplementedError  # YOUR CODE


def prefixes_needed(gets_per_second, puts_per_second):
    raise NotImplementedError  # YOUR CODE


class Ex04(Drill):
    """Big objects, busy buckets ★"""
    tasks = ("3.1",)

    def test_small_uploads(self):
        self.assertEqual(plan_parts(10 * MIB), {"part_bytes": 5 * MIB, "parts": 2, "last_part_bytes": 5 * MIB, "multipart": False})
        got = plan_parts(11 * MIB)
        self.assertEqual((got["parts"], got["last_part_bytes"]), (3, 1 * MIB))
        self.assertEqual(plan_parts(1)["parts"], 1)
        self.assertEqual(plan_parts(1)["last_part_bytes"], 1)

    def test_a_chosen_part_size(self):
        got = plan_parts(100 * MIB, 16)
        self.assertEqual((got["part_bytes"], got["parts"], got["last_part_bytes"]), (16 * MIB, 7, 4 * MIB))
        got = plan_parts(96 * MIB, 16)
        self.assertEqual((got["parts"], got["last_part_bytes"]), (6, 16 * MIB), "an exact fit: the last part is a full part")

    def test_when_to_use_multipart(self):
        self.assertFalse(plan_parts(50 * MIB)["multipart"])
        self.assertFalse(plan_parts(100 * MIB)["multipart"], "the course rule is MORE than 100 MiB, so exactly 100 MiB is not")
        self.assertTrue(plan_parts(100 * MIB + 1)["multipart"])
        self.assertTrue(plan_parts(200 * MIB)["multipart"])
        self.assertTrue(plan_parts(5 * GIB + 1)["multipart"], "above 5 GiB a single PUT is impossible")
        self.assertTrue(plan_parts(6 * GIB)["multipart"])

    def test_the_automatic_part_size_grows_with_the_object(self):
        self.assertEqual(plan_parts(1024 * GIB)["part_bytes"], 105 * MIB, "1 TiB / 10,000 parts, rounded up to whole MiB")
        self.assertEqual(plan_parts(100 * GIB)["part_bytes"], 11 * MIB, "100 GiB / 10,000 = 10.24 MiB, rounded up")
        self.assertEqual(plan_parts(10 * GIB)["part_bytes"], 5 * MIB, "never below 5 MiB")
        for size in (10 * GIB, 500 * GIB, 5 * 10 ** 12, MAX_OBJECT_BYTES):
            with self.subTest(size=size):
                got = plan_parts(size)
                self.assertLessEqual(got["parts"], 10_000)
                self.assertLessEqual(got["part_bytes"], 5 * GIB)
                self.assertEqual((got["parts"] - 1) * got["part_bytes"] + got["last_part_bytes"], size, "the parts add up to the object")

    def test_the_part_count_limit_is_10000(self):
        ok = plan_parts(50_000 * MIB, 5)
        self.assertEqual(ok["parts"], 10_000, "exactly 10,000 parts is allowed")
        with self.assertRaises(ValueError):
            plan_parts(50_000 * MIB + 1, 5)
        with self.assertRaises(ValueError):
            plan_parts(60 * GIB, 5)

    def test_the_part_size_limits(self):
        self.assertEqual(plan_parts(10 * GIB, 5)["part_bytes"], 5 * MIB)
        self.assertEqual(plan_parts(10 * GIB, 5120)["part_bytes"], 5 * GIB)
        for part in (4, 0, -5, 5121):
            with self.subTest(part=part):
                with self.assertRaises(ValueError):
                    plan_parts(10 * GIB, part)

    def test_the_object_size_limits(self):
        self.assertEqual(plan_parts(MAX_OBJECT_BYTES)["parts"], 9999)
        for size in (0, -1, MAX_OBJECT_BYTES + 1):
            with self.subTest(size=size):
                with self.assertRaises(ValueError):
                    plan_parts(size)

    def test_prefixes_needed(self):
        for gets, puts, want in ((100, 100, 1), (0, 0, 1), (5500, 3500, 1), (5501, 0, 2), (0, 3501, 2), (11_000, 3_500, 2),
                                 (11_000, 10_500, 3), (55_000, 1000, 10), (1000, 35_000, 10)):
            with self.subTest(gets=gets, puts=puts):
                self.assertEqual(prefixes_needed(gets, puts), want, "reads and writes have separate limits: the larger need decides")

    def test_prefixes_needed_rejects_negative_rates(self):
        for args in ((-1, 0), (0, -1)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    prefixes_needed(*args)


# ── helpers for the boto3 drills ─────────────────────────────────────
import random  # noqa: E402


class _NetworkDrop(Exception):
    """The simulated failure of one upload part."""


class _Spy:
    """Wraps a boto3 client: logs every call as (name, kwargs) in .calls and can fail one upload part.
    The drills pass it to your function in place of the client, so they can see WHAT you called and in what order."""

    def __init__(self, client, fail_part=None):
        self._client, self._fail_part, self.calls = client, fail_part, []

    def __getattr__(self, name):
        attr = getattr(self._client, name)
        if not callable(attr):
            return attr

        def call(*args, **kwargs):
            self.calls.append((name, kwargs))
            if name == "upload_part" and kwargs.get("PartNumber") == self._fail_part:
                raise _NetworkDrop("the network dropped this part")
            return attr(*args, **kwargs)
        return call

    def names(self):
        return [name for name, _ in self.calls]


# ── Exercise 05: A bucket that keeps secrets ─────────────────────────
"""
secure_bucket(s3, name, kms_key_id) -> None
    Create the bucket `name` (us-east-1, so no location constraint) and lock it down, using the boto3 client `s3`:
      versioning                   Enabled (a delete or overwrite can be undone)
      default encryption           SSE-KMS with the key kms_key_id, and Bucket Keys ON (BucketKeyEnabled=True: far
                                   fewer KMS calls, so a lower KMS bill)
      Block Public Access          ALL FOUR settings True: BlockPublicAcls, IgnorePublicAcls, BlockPublicPolicy,
                                   RestrictPublicBuckets. Setting only some leaves the others False.
      Object Ownership             BucketOwnerEnforced (ACLs are switched off; the bucket policy and IAM decide everything)
    An empty kms_key_id -> ValueError (SSE-KMS needs YOUR key: that is what gives you key policies and an audit trail).
tls_only_policy(bucket) -> dict
    RETURN (do not put) a bucket policy, as a Python dict, with Version "2012-10-17" that DENIES every S3 action
    (s3:*) to everyone ("*") when the request did not use HTTPS: Condition Bool aws:SecureTransport "false".
    It must cover BOTH the bucket ARN (arn:aws:s3:::name — ListBucket and friends) and the objects (arn:aws:s3:::name/*).
    It must contain no Allow: a deny-only policy adds a guard rail without opening anything.
    Why it is not put in this drill: moto enforces a bucket-policy Deny crudely. It ignores Condition and Principal, so
    this Deny would block the test's own HTTPS calls too. In real AWS you would put_bucket_policy it. The tests evaluate
    the dict with the policy evaluator from week 01 instead.
Examples:
    tls_only_policy("logs")["Statement"][0]["Effect"] == "Deny"
Why? "Deny unless HTTPS" is the standard guard rail, because a Deny beats every Allow. And the policy must name the
bucket ARN as well as the objects, or a plain-HTTP ListBucket request slips through.
Hint: put_bucket_versioning(Bucket=…, VersioningConfiguration={"Status": "Enabled"}); put_bucket_encryption(Bucket=…,
      ServerSideEncryptionConfiguration={"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "aws:kms",
      "KMSMasterKeyID": …}, "BucketKeyEnabled": True}]}); put_public_access_block(…, PublicAccessBlockConfiguration={…});
      put_bucket_ownership_controls(…, OwnershipControls={"Rules": [{"ObjectOwnership": "BucketOwnerEnforced"}]}).
"""
def secure_bucket(s3, name, kms_key_id):
    raise NotImplementedError  # YOUR CODE


def tls_only_policy(bucket):
    raise NotImplementedError  # YOUR CODE


from _harness.awslib import policy_eval as _pe  # noqa: E402


class Ex05(Drill):
    """A bucket that keeps secrets"""
    tasks = ("1.3",)
    uses_aws = True
    KEY = "arn:aws:kms:us-east-1:111122223333:key/1234abcd-12ab-34cd-56ef-1234567890ab"
    ALICE = "arn:aws:iam::111122223333:user/alice"
    ALLOW_ALL = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "s3:*", "Resource": "*"}]}

    def make(self, name="shortly-secrets"):
        s3 = self.client("s3")
        secure_bucket(s3, name, self.KEY)
        return s3, name

    def verdict(self, policy, action, resource, https):
        request = _pe.Request(self.ALICE, action, resource, {"aws:SecureTransport": https})
        return _pe.evaluate(request, identity=[self.ALLOW_ALL], resource_policy=policy)

    def test_the_bucket_exists_and_is_versioned(self):
        s3, name = self.make()
        self.assertIn(name, [b["Name"] for b in s3.list_buckets()["Buckets"]])
        self.assertEqual(s3.get_bucket_versioning(Bucket=name).get("Status"), "Enabled")

    def test_default_encryption_is_kms_with_a_bucket_key(self):
        s3, name = self.make()
        rule = s3.get_bucket_encryption(Bucket=name)["ServerSideEncryptionConfiguration"]["Rules"][0]
        default = rule["ApplyServerSideEncryptionByDefault"]
        self.assertEqual(default["SSEAlgorithm"], "aws:kms", "SSE-S3 (AES256) is not enough: use your own KMS key")
        self.assertEqual(default["KMSMasterKeyID"], self.KEY)
        self.assertTrue(rule["BucketKeyEnabled"], "turn Bucket Keys on: they cut KMS request costs")

    def test_new_objects_inherit_the_encryption(self):
        s3, name = self.make()
        s3.put_object(Bucket=name, Key="a.txt", Body=b"hello")
        head = s3.head_object(Bucket=name, Key="a.txt")
        self.assertEqual(head["ServerSideEncryption"], "aws:kms")
        self.assertEqual(head["SSEKMSKeyId"], self.KEY)

    def test_all_four_public_access_settings_are_on(self):
        s3, name = self.make()
        config = s3.get_public_access_block(Bucket=name)["PublicAccessBlockConfiguration"]
        self.assertEqual(config, {"BlockPublicAcls": True, "IgnorePublicAcls": True,
                                  "BlockPublicPolicy": True, "RestrictPublicBuckets": True},
                         "Block Public Access has four switches: turn on all four")

    def test_acls_are_off(self):
        s3, name = self.make()
        rules = s3.get_bucket_ownership_controls(Bucket=name)["OwnershipControls"]["Rules"]
        self.assertEqual(rules, [{"ObjectOwnership": "BucketOwnerEnforced"}])

    def test_a_key_is_required(self):
        s3 = self.client("s3")
        for bad in ("", None):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    secure_bucket(s3, "shortly-nokey", bad)

    def test_tls_policy_lets_https_through_and_blocks_http(self):
        policy = tls_only_policy("shortly-secrets")
        self.assertEqual(policy["Version"], "2012-10-17")
        json.dumps(policy)
        bucket, objects = "arn:aws:s3:::shortly-secrets", "arn:aws:s3:::shortly-secrets/report.csv"
        for action, resource in (("s3:GetObject", objects), ("s3:PutObject", objects), ("s3:ListBucket", bucket)):
            with self.subTest(action=action):
                self.assertEqual(self.verdict(policy, action, resource, https=True), "Allow", "HTTPS requests must not be affected")
                self.assertEqual(self.verdict(policy, action, resource, https=False), "ExplicitDeny", "plain HTTP must be denied")

    def test_the_bucket_itself_is_covered_not_only_its_objects(self):
        policy = tls_only_policy("shortly-secrets")
        self.assertEqual(self.verdict(policy, "s3:ListBucket", "arn:aws:s3:::shortly-secrets", https=False), "ExplicitDeny",
                         "listing the bucket over HTTP is on the BUCKET ARN, which has no /*")
        self.assertEqual(self.verdict(policy, "s3:GetBucketPolicy", "arn:aws:s3:::shortly-secrets", https=False), "ExplicitDeny")

    def test_the_policy_is_deny_only_and_belongs_to_this_bucket(self):
        policy = tls_only_policy("shortly-secrets")
        self.assertTrue(policy["Statement"], "at least one statement")
        self.assertTrue(all(s["Effect"] == "Deny" for s in policy["Statement"]), "a guard rail denies; it never allows")
        self.assertEqual(self.verdict(policy, "s3:GetObject", "arn:aws:s3:::another-bucket/x", https=False), "Allow",
                         "the policy must name this bucket only")
        self.assertEqual(self.verdict(policy, "s3:GetObject", "arn:aws:s3:::shortly-secrets/x", https=False), "ExplicitDeny")


# ── Exercise 06: Upload big, share briefly ───────────────────────────
"""
upload_in_parts(s3, bucket, key, data, part_mib) -> None
    Upload the bytes `data` to s3://bucket/key as a MULTIPART upload with parts of part_mib MiB (the last part may be
    smaller): create_multipart_upload, then upload_part for part numbers 1, 2, 3 ... (they start at 1), then
    complete_multipart_upload with the list of {"PartNumber", "ETag"} you collected. Use drill 04's plan_parts if you
    like, or just slice the data.
    If any part fails, ABORT the upload (abort_multipart_upload) and re-raise the error: an upload left unfinished keeps
    billing you for the stored parts and never shows up in a normal listing.
    ValueError (before anything is created) for a part_mib outside 5 to 5,120, or empty data.
share_link(s3, bucket, key, seconds) -> str
    A presigned GET URL for the object that stops working after `seconds` seconds: s3.generate_presigned_url("get_object",
    Params={"Bucket": …, "Key": …}, ExpiresIn=seconds). A presigned URL carries YOUR permissions to whoever holds it, so keep it
    short. ValueError if seconds is less than 1 or more than 604,800 (7 days, the longest SigV4 allows).
    (Signed with temporary credentials such as an IAM role, the URL also dies when those credentials expire.)
    NEVER open the URL in a test: urllib would go to the real internet. The tests read the URL's parts.
Examples:
    upload_in_parts(s3, "b", "big.bin", data_of_12_MiB, 5)   # 3 parts: 5 MiB, 5 MiB, 2 MiB
    share_link(s3, "b", "report.pdf", 3600)   # …/report.pdf?X-Amz-Expires=3600&X-Amz-Signature=…
Why? Multipart makes a big upload retryable and parallel; the abort keeps failures from leaving billable debris. And a
link is a key to the door: the shorter it lives, the less it matters if it leaks.
"""
def upload_in_parts(s3, bucket, key, data, part_mib):
    raise NotImplementedError  # YOUR CODE


def share_link(s3, bucket, key, seconds):
    raise NotImplementedError  # YOUR CODE


class Ex06(Drill):
    """Upload big, share briefly"""
    tasks = ("3.1", "1.3")
    uses_aws = True

    def data(self, size):
        return random.Random(4).randbytes(size)

    def bucket(self):
        s3 = self.client("s3")
        s3.create_bucket(Bucket="shortly-uploads")
        return s3

    def test_the_object_reads_back_intact(self):
        s3 = self.bucket()
        data = self.data(12 * MIB + 123)
        upload_in_parts(s3, "shortly-uploads", "big.bin", data, 5)
        body = s3.get_object(Bucket="shortly-uploads", Key="big.bin")["Body"].read()
        self.assertEqual(len(body), len(data))
        self.assertTrue(body == data, "the parts must go back together in order")

    def test_it_really_used_a_multipart_upload(self):
        s3 = self.bucket()
        spy = _Spy(s3)
        upload_in_parts(spy, "shortly-uploads", "big.bin", self.data(12 * MIB + 123), 5)
        etag = s3.head_object(Bucket="shortly-uploads", Key="big.bin")["ETag"].strip('"')
        self.assertTrue(etag.endswith("-3"), f"a 3-part multipart object has an ETag ending -3, got {etag}")
        parts = [kwargs["PartNumber"] for name, kwargs in spy.calls if name == "upload_part"]
        self.assertEqual(parts, [1, 2, 3], "part numbers start at 1 and go up by one")
        self.assertEqual(spy.names().count("complete_multipart_upload"), 1)

    def test_part_size_decides_the_number_of_parts(self):
        s3 = self.bucket()
        spy = _Spy(s3)
        upload_in_parts(spy, "shortly-uploads", "a.bin", self.data(17 * MIB), 8)
        self.assertEqual(spy.names().count("upload_part"), 3, "17 MiB in 8 MiB parts is 8 + 8 + 1")
        small = _Spy(s3)
        upload_in_parts(small, "shortly-uploads", "b.bin", self.data(1 * MIB), 5)
        self.assertEqual(small.names().count("upload_part"), 1, "an object smaller than one part is a single (last) part")
        self.assertEqual(len(s3.get_object(Bucket="shortly-uploads", Key="b.bin")["Body"].read()), 1 * MIB)

    def test_a_failed_part_aborts_the_upload(self):
        s3 = self.bucket()
        spy = _Spy(s3, fail_part=2)
        with self.assertRaises(_NetworkDrop):
            upload_in_parts(spy, "shortly-uploads", "big.bin", self.data(12 * MIB), 5)
        self.assertEqual(s3.list_multipart_uploads(Bucket="shortly-uploads").get("Uploads", []), [],
                         "abort_multipart_upload, or the stored parts keep costing money")
        with self.assertClientError("NoSuchKey"):
            s3.get_object(Bucket="shortly-uploads", Key="big.bin")

    def test_bad_part_sizes_and_empty_data_create_nothing(self):
        s3 = self.bucket()
        spy = _Spy(s3)
        for part_mib, data in ((4, b"x" * 10), (5121, b"x" * 10), (0, b"x" * 10), (5, b"")):
            with self.subTest(part_mib=part_mib, size=len(data)):
                with self.assertRaises(ValueError):
                    upload_in_parts(spy, "shortly-uploads", "bad.bin", data, part_mib)
        self.assertEqual(spy.calls, [], "validate first: no call to S3 for a request that cannot work")

    def test_the_link_names_the_object_and_expires(self):
        from botocore.config import Config
        s3 = self.client("s3", config=Config(signature_version="s3v4"))
        s3.create_bucket(Bucket="shortly-uploads")
        url = share_link(s3, "shortly-uploads", "reports/q1.pdf", 3600)
        self.assertIsInstance(url, str)
        self.assertIn("shortly-uploads", url)
        self.assertIn("reports/q1.pdf", url)
        self.assertIn("X-Amz-Expires=3600", url, "ExpiresIn is what makes the link short-lived")
        self.assertIn("X-Amz-Signature=", url)
        self.assertIn("X-Amz-Expires=60&", share_link(s3, "shortly-uploads", "reports/q1.pdf", 60) + "&")

    def test_the_longest_link_is_seven_days(self):
        from botocore.config import Config
        s3 = self.client("s3", config=Config(signature_version="s3v4"))
        self.assertIn("X-Amz-Expires=604800", share_link(s3, "b", "k", 604_800))
        for seconds in (604_801, 0, -5):
            with self.subTest(seconds=seconds):
                with self.assertRaises(ValueError):
                    share_link(s3, "b", "k", seconds)
        self.assertIn("X-Amz-Expires=1", share_link(s3, "b", "k", 1))


# ── Exercise 07 (predict): What survives a delete? ───────────────────
"""
A VERSIONED bucket never loses data on a plain delete: it adds a DELETE MARKER on top. For each scenario, work out the
answer BEFORE running anything and write it in PREDICTIONS. The test runs the scenario against moto (a fake S3 that
follows these rules) and shows the truth when you are wrong.
Answers: an AWS error code like "AccessDenied" (what boto3 puts in e.response["Error"]["Code"]), the object's body text,
a number, or "M markers, V versions" (always plural, for example "2 markers, 5 versions").
"""
SCENARIOS7 = {
    1: "A versioned bucket holds report.txt with body 'first'. You call delete_object(Bucket, Key) with no VersionId, then get_object(Bucket, Key). "
       "Which error code comes back?",
    2: "The same, but now you call get_object with the VersionId the object had BEFORE the delete. What is the body?",
    3: "The same plain delete. How many keys does list_objects_v2 return for the bucket? (a number)",
    4: "The same plain delete. What does list_object_versions show? Answer like '2 markers, 5 versions'.",
    5: "report.txt has two versions, 'first' then 'second'. You delete it with no VersionId, then delete the DELETE MARKER by its own VersionId, "
       "then get_object. What is the body?",
    6: "report.txt has ONE version, 'first'. You call delete_object with that version's VersionId, then get_object. Which error code comes back?",
    7: "report.txt is written twice: 'first', then 'second'. What does list_object_versions show? Answer like '2 markers, 5 versions'.",
    8: "report.txt has two versions, 'first' then 'second'. You delete the LATEST version by its VersionId, then get_object with no VersionId. "
       "What is the body?",
}
PREDICTIONS = {n: None for n in SCENARIOS7}   # YOUR ANSWERS: an error code, a body, a number or "M markers, V versions"


def _versioned_bucket(s3, name, bodies):
    """A fresh versioned bucket whose key report.txt was written once per body; returns the version ids in order."""
    s3.create_bucket(Bucket=name)
    s3.put_bucket_versioning(Bucket=name, VersioningConfiguration={"Status": "Enabled"})
    return [s3.put_object(Bucket=name, Key="report.txt", Body=body)["VersionId"] for body in bodies]


def _error_code(call):
    from botocore.exceptions import ClientError
    try:
        call()
    except ClientError as exc:
        return exc.response["Error"]["Code"]
    return "no error"


def _text(s3, name, **kwargs):
    return s3.get_object(Bucket=name, Key="report.txt", **kwargs)["Body"].read().decode()


def _counts(s3, name):
    listed = s3.list_object_versions(Bucket=name)
    return f"{len(listed.get('DeleteMarkers', []))} markers, {len(listed.get('Versions', []))} versions"


def _run7(n, s3):
    name = f"shortly-ex07-s{n}"
    if n in (1, 2, 3, 4):
        (first,) = _versioned_bucket(s3, name, [b"first"])
        s3.delete_object(Bucket=name, Key="report.txt")
        return {1: lambda: _error_code(lambda: _text(s3, name)), 2: lambda: _text(s3, name, VersionId=first),
                3: lambda: s3.list_objects_v2(Bucket=name)["KeyCount"], 4: lambda: _counts(s3, name)}[n]()
    if n == 5:
        _versioned_bucket(s3, name, [b"first", b"second"])
        marker = s3.delete_object(Bucket=name, Key="report.txt")["VersionId"]
        s3.delete_object(Bucket=name, Key="report.txt", VersionId=marker)
        return _text(s3, name)
    if n == 6:
        (first,) = _versioned_bucket(s3, name, [b"first"])
        s3.delete_object(Bucket=name, Key="report.txt", VersionId=first)
        return _error_code(lambda: _text(s3, name))
    if n == 7:
        _versioned_bucket(s3, name, [b"first", b"second"])
        return _counts(s3, name)
    _, second = _versioned_bucket(s3, name, [b"first", b"second"])
    s3.delete_object(Bucket=name, Key="report.txt", VersionId=second)
    return _text(s3, name)


class Ex07(Drill):
    """What survives a delete? (predict)"""
    tasks = ("1.3", "2.2")
    uses_aws = True

    def test_predictions(self):
        s3 = self.client("s3")
        for n, story in SCENARIOS7.items():
            with self.subTest(scenario=n):
                truth = _run7(n, s3)
                self.assertIsNotNone(PREDICTIONS.get(n), f"scenario {n}: write your answer")
                self.assertEqual(normalise(PREDICTIONS[n]), normalise(truth), f"scenario {n}: {story} — the answer is {truth!r}")


# ── Exercise 08 (fix the bug): Too public ────────────────────────────
"""
ASSETS_POLICY is the bucket policy of "shortly-assets", the bucket behind a CloudFront distribution. It is too open: it
lets ANYONE on the internet read every object, and ANYONE write to it. Edit ASSETS_POLICY (a Python dict) so that:
  * s3:GetObject on the objects (arn:aws:s3:::shortly-assets/*) is allowed ONLY to the CloudFront service
    (Principal {"Service": "cloudfront.amazonaws.com"}) and ONLY when the request comes from OUR distribution:
    Condition StringEquals "AWS:SourceArn" = DISTRIBUTION_ARN. This is Origin Access Control (OAC). Without the
    condition ANY CloudFront distribution in the world could serve your files, a "confused deputy".
  * s3:PutObject is allowed ONLY to the application role (Principal {"AWS": APP_ROLE_ARN}) and ONLY under the
    uploads/ prefix (arn:aws:s3:::shortly-assets/uploads/*).
Nobody else gets anything from this policy.
Why? A bucket policy is an open door unless every Allow names WHO and, where it matters, WHERE the request comes from.
Principal "*" means everyone, including people with no AWS account. The tests evaluate your policy with the policy
evaluator from week 01 (moto cannot: it ignores principals and conditions).
Hint: the CloudFront caller is the service itself, so Principal is {"Service": "cloudfront.amazonaws.com"}, not an AWS ARN.
"""
BUCKET_ARN = "arn:aws:s3:::shortly-assets"
DISTRIBUTION_ARN = "arn:aws:cloudfront::111122223333:distribution/E2EXAMPLE1234"
APP_ROLE_ARN = "arn:aws:iam::111122223333:role/shortly-app"
ASSETS_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {"Sid": "ReadAssets", "Effect": "Allow", "Principal": "*", "Action": "s3:GetObject", "Resource": f"{BUCKET_ARN}/*"},
        {"Sid": "WriteAssets", "Effect": "Allow", "Principal": "*", "Action": "s3:PutObject", "Resource": f"{BUCKET_ARN}/*"},
    ],
}


class Ex08(Drill):
    """Too public (fix the bug)"""
    tasks = ("1.3",)
    CLOUDFRONT = "cloudfront.amazonaws.com"
    OTHER_DISTRIBUTION = "arn:aws:cloudfront::999999999999:distribution/EEVIL000000"
    APP_SESSION = "arn:aws:sts::111122223333:assumed-role/shortly-app/i-0abc123"
    OTHER_SESSION = "arn:aws:sts::111122223333:assumed-role/other-team/i-0def456"
    ALICE = "arn:aws:iam::111122223333:user/alice"
    ASSET = f"{BUCKET_ARN}/images/logo.png"

    def verdict(self, principal, action, resource, **context):
        return _pe.evaluate(_pe.Request(principal, action, resource, context), resource_policy=ASSETS_POLICY)

    def test_only_our_distribution_can_read(self):
        json.dumps(ASSETS_POLICY)
        self.assertEqual(ASSETS_POLICY["Version"], "2012-10-17")
        self.assertEqual(self.verdict(self.CLOUDFRONT, "s3:GetObject", self.ASSET, **{"aws:SourceArn": DISTRIBUTION_ARN}), "Allow",
                         "our distribution must still be able to read")
        self.assertNotEqual(self.verdict("anonymous", "s3:GetObject", self.ASSET), "Allow", "an anonymous visitor must not read the bucket directly")
        self.assertNotEqual(self.verdict(self.ALICE, "s3:GetObject", self.ASSET), "Allow", "no other principal is granted read")

    def test_another_distribution_is_refused(self):
        self.assertNotEqual(self.verdict(self.CLOUDFRONT, "s3:GetObject", self.ASSET, **{"aws:SourceArn": self.OTHER_DISTRIBUTION}), "Allow",
                            "the SourceArn condition is what stops other people's distributions")
        self.assertNotEqual(self.verdict(self.CLOUDFRONT, "s3:GetObject", self.ASSET), "Allow", "CloudFront with no source ARN at all")
        self.assertEqual(self.verdict(self.CLOUDFRONT, "s3:GetObject", self.ASSET, **{"aws:SourceArn": DISTRIBUTION_ARN}), "Allow")

    def test_cloudfront_reads_but_never_writes(self):
        ours = {"aws:SourceArn": DISTRIBUTION_ARN}
        self.assertEqual(self.verdict(self.CLOUDFRONT, "s3:GetObject", f"{BUCKET_ARN}/uploads/a.png", **ours), "Allow")
        self.assertNotEqual(self.verdict(self.CLOUDFRONT, "s3:PutObject", f"{BUCKET_ARN}/uploads/a.png", **ours), "Allow")
        self.assertNotEqual(self.verdict(self.CLOUDFRONT, "s3:DeleteObject", self.ASSET, **ours), "Allow")

    def test_the_app_role_writes_only_under_uploads(self):
        self.assertEqual(self.verdict(self.APP_SESSION, "s3:PutObject", f"{BUCKET_ARN}/uploads/a.png"), "Allow", "the app must still be able to upload")
        self.assertEqual(self.verdict(self.APP_SESSION, "s3:PutObject", f"{BUCKET_ARN}/uploads/2026/b.png"), "Allow")
        self.assertNotEqual(self.verdict(self.APP_SESSION, "s3:PutObject", self.ASSET), "Allow", "outside uploads/ the app role may not write")
        self.assertNotEqual(self.verdict(self.APP_SESSION, "s3:PutObject", f"{BUCKET_ARN}/index.html"), "Allow")

    def test_nobody_else_can_write(self):
        target = f"{BUCKET_ARN}/uploads/a.png"
        self.assertEqual(self.verdict(self.APP_SESSION, "s3:PutObject", target), "Allow")
        for who in ("anonymous", self.ALICE, self.OTHER_SESSION):
            with self.subTest(who=who):
                self.assertNotEqual(self.verdict(who, "s3:PutObject", target), "Allow", f"{who} must not be able to upload")


# ── Exercise 09 (fix the bug): Replication that never starts ─────────
"""
make_replicated_pair(s3, source, destination, role_arn) -> None
    Create two buckets and replicate every new object from `source` to `destination`. As written it fails the moment it
    calls put_bucket_replication. Fix it so that:
      * both buckets exist, and versioning is Enabled on BOTH — and turned on BEFORE the replication rule is put.
        Replication copies object VERSIONS, so S3 refuses a rule when the source is not versioned, and a destination that
        is not versioned cannot receive them.
      * ONE rule, Status "Enabled", for all objects (Filter {"Prefix": ""}), with Priority 1.
      * the rule's Destination Bucket is the destination bucket's ARN (arn:aws:s3:::name), NOT its name.
      * the replication Role is role_arn (S3 assumes this role to copy; its trust policy names s3.amazonaws.com).
      * DeleteMarkerReplication Status "Enabled": a delete in the source is copied as a delete marker. Say "Disabled" and the
        two buckets drift apart after the first delete.
    source and destination must differ (ValueError).
Note: moto stores the rule but never copies a byte, and always reads DeleteMarkerReplication back as "Disabled". So the
tests check the settings you send, not a copy.
Why? Replication is a copy of every new version, so it needs a versioned source and destination. Existing objects are not
copied by a new rule (that needs S3 Batch Replication). Cross-region copies cost transfer, and the same-region kind
(SRR) is for log aggregation or a separate-owner copy.
"""
def make_replicated_pair(s3, source, destination, role_arn):
    s3.create_bucket(Bucket=source)
    s3.create_bucket(Bucket=destination)
    s3.put_bucket_replication(Bucket=source, ReplicationConfiguration={
        "Role": role_arn,
        "Rules": [{"ID": "all", "Status": "Enabled", "Prefix": "", "Destination": {"Bucket": destination}}],
    })


class Ex09(Drill):
    """Replication that never starts (fix the bug)"""
    tasks = ("2.2", "1.3")
    uses_aws = True
    ROLE = "arn:aws:iam::111122223333:role/shortly-replication"

    def make(self):
        s3 = self.client("s3")
        spy = _Spy(s3)
        make_replicated_pair(spy, "shortly-src", "shortly-dst", self.ROLE)
        return s3, spy

    def rule(self, s3):
        return s3.get_bucket_replication(Bucket="shortly-src")["ReplicationConfiguration"]["Rules"][0]

    def test_both_buckets_are_versioned(self):
        s3, _ = self.make()
        for name in ("shortly-src", "shortly-dst"):
            with self.subTest(bucket=name):
                self.assertEqual(s3.get_bucket_versioning(Bucket=name).get("Status"), "Enabled",
                                 f"{name}: replication copies versions, so both ends need versioning")

    def test_versioning_comes_before_the_rule(self):
        _, spy = self.make()
        names = spy.names()
        self.assertIn("put_bucket_replication", names)
        rule_at = names.index("put_bucket_replication")
        for bucket in ("shortly-src", "shortly-dst"):
            with self.subTest(bucket=bucket):
                turned_on = [i for i, (name, kwargs) in enumerate(spy.calls) if name == "put_bucket_versioning" and kwargs["Bucket"] == bucket]
                self.assertTrue(turned_on and turned_on[0] < rule_at, f"turn versioning on for {bucket} before you put the replication rule")

    def test_the_rule_points_at_the_destination_arn(self):
        s3, _ = self.make()
        rule = self.rule(s3)
        self.assertEqual(rule["Status"], "Enabled")
        self.assertEqual(rule["Destination"]["Bucket"], "arn:aws:s3:::shortly-dst", "the destination is an ARN, not a bucket name")
        self.assertEqual(len(s3.get_bucket_replication(Bucket="shortly-src")["ReplicationConfiguration"]["Rules"]), 1)

    def test_the_role_and_scope(self):
        s3, _ = self.make()
        config = s3.get_bucket_replication(Bucket="shortly-src")["ReplicationConfiguration"]
        self.assertEqual(config["Role"], self.ROLE)
        rule = config["Rules"][0]
        self.assertEqual(rule.get("Filter", {}).get("Prefix", ""), "", "replicate everything: an empty prefix")
        self.assertEqual(rule.get("Priority"), 1)

    def test_deletes_are_replicated_as_delete_markers(self):
        _, spy = self.make()
        sent = [kwargs for name, kwargs in spy.calls if name == "put_bucket_replication"][0]["ReplicationConfiguration"]["Rules"][0]
        self.assertEqual(sent.get("DeleteMarkerReplication"), {"Status": "Enabled"},
                         "DeleteMarkerReplication is part of the rule you send (moto will not show it when read back)")

    def test_both_buckets_exist_and_must_differ(self):
        s3, _ = self.make()
        s3.head_bucket(Bucket="shortly-src")
        s3.head_bucket(Bucket="shortly-dst")
        with self.assertRaises(ValueError):
            make_replicated_pair(s3, "shortly-same", "shortly-same", self.ROLE)


# ── Exercise 10 (decide): Which storage service? ─────────────────────
"""
Choose the best storage service for each scenario. Replace every None in CHOICES with one of these words:
  "s3"                object storage at any scale over HTTP: websites, backups, data lakes
  "ebs"               a block volume for ONE EC2 instance (in one AZ): boot disks, databases
  "instance store"    disks physically on the host: very fast, but gone when the instance stops or fails
  "efs"               shared NFS file system for Linux, across AZs, grows by itself
  "fsx for windows"   managed Windows file server: SMB, Active Directory, NTFS
  "fsx for lustre"    high-performance file system for HPC and ML, can read an S3 bucket
  "fsx for ontap"     NetApp ONTAP: NFS, SMB and iSCSI on the same data, snapshots, SnapMirror
  "storage gateway"   an on-premises appliance that caches locally and stores in AWS
(The answers are stored as hashes, so reading the test will not give them away.)
"""
SCENARIOS10 = {
    1: "A shared POSIX file system that 20 Linux web servers in 3 Availability Zones mount at the same time.",
    2: "Scratch space for a temporary cache that may vanish when the instance stops.",
    3: "Windows home directories for a company using Active Directory, reached over SMB.",
    4: "An HPC job that reads a 50 TB dataset stored in S3 at hundreds of GB/s.",
    5: "The boot volume of one EC2 instance.",
    6: "An on-premises file server that must keep local caching but store its data in S3.",
    7: "Static website images and backups, at any scale, with no capacity planning.",
    8: "NFS and SMB clients using the same data, with NetApp snapshots and SnapMirror replication.",
}
OPTIONS10 = ("s3", "ebs", "instance store", "efs", "fsx for windows", "fsx for lustre", "fsx for ontap", "storage gateway")
CHOICES = {n: None for n in SCENARIOS10}   # YOUR ANSWERS: one of the words in the docstring
CHOICE_DIGESTS = {
    1: "186c54acc6d75432c2b61825c4fc8ebb4df485e158395661da3b41ab5b8151d3",
    2: "f2984e1c134a0ec3c0331678376188006f45239c7834c7a6aeaf83796f19e8a2",
    3: "c235d5c3b017c6b21430e476fc522b65a3b152e7b410b25f7c20aa38a7c20efe",
    4: "41844a05eb6cae94cee1416c1bdc0e386eac64bc79d6fa7245198dae11c840ae",
    5: "e6d30d3dec3b88800ed52b0ed20dd3cb6381974d8d672ecbdd64abedd90f601b",
    6: "c3a5443e81dc92b7daf1dea2ac4ec2fc33e82133b62e6f7b5620ac4be6e3ec84",
    7: "3f83e0575a4ae45f4aa452cb719fffffd0a586a9619d0e84059582a1db79ce4d",
    8: "8dd82848a36c9dd09ef4ec452bb19ece39f78b8a9bfe3212a52ae3dcfdb39d29",
}


class Ex10(Drill):
    """Which storage service? (decide)"""
    tasks = ("3.1", "4.1")

    def test_choices(self):
        for n, story in SCENARIOS10.items():
            with self.subTest(scenario=n):
                value = CHOICES.get(n)
                self.assertIn(value, OPTIONS10, f"scenario {n}: answer one of {OPTIONS10}, not {value!r}")
                self.assertHashed(value, f"w04-ex10-{n}", CHOICE_DIGESTS[n],
                                  f"scenario {n} ({story}): {value!r} is not right — who mounts it, which protocol, how long must it last?")


if __name__ == "__main__":
    run()

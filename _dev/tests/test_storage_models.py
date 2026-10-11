import copy

import pytest

from _harness.awslib import ebs, lifecycle, s3cost

TB_KB = 1_048_576  # object_kb that makes "objects" count whole GB (1 GB = 1,048,576 KB)


# ---------------------------------------------------------------- s3cost.storage_cost
def test_docstring_example():
    assert s3cost.storage_cost("STANDARD", 1024, TB_KB, 30) == 23.55


# 1,024 GB for 365 days, 100 GB retrieved
@pytest.mark.parametrize("cls,standard,bulk", [
    ("STANDARD", 286.55, 286.55),
    ("STANDARD_IA", 156.73, 156.73),
    ("ONEZONE_IA", 125.59, 125.59),
    ("GLACIER_IR", 52.83, 52.83),
    ("GLACIER", 45.85, 44.85),
    ("DEEP_ARCHIVE", 14.33, 12.58),
])
def test_storage_cost_a_year_with_retrieval(cls, standard, bulk):
    assert s3cost.storage_cost(cls, 1024, TB_KB, 365, 100) == standard
    assert s3cost.storage_cost(cls, 1024, TB_KB, 365, 100, retrieval="bulk") == bulk


def test_retrieval_only_costs_for_non_standard():
    assert s3cost.storage_cost("STANDARD", 0, 0, 0, 500) == 0.0
    assert s3cost.storage_cost("STANDARD_IA", 0, 0, 0, 500) == 5.0
    assert s3cost.storage_cost("GLACIER_IR", 0, 0, 0, 100) == 3.0
    assert s3cost.storage_cost("DEEP_ARCHIVE", 0, 0, 0, 100) == 2.0
    assert s3cost.storage_cost("DEEP_ARCHIVE", 0, 0, 0, 100, retrieval="bulk") == 0.25


def test_minimum_duration_is_billed():
    # deleting a Deep Archive object after 10 days still pays 180 days
    assert s3cost.storage_cost("DEEP_ARCHIVE", 1024, TB_KB, 10) == s3cost.storage_cost("DEEP_ARCHIVE", 1024, TB_KB, 180)
    assert s3cost.storage_cost("STANDARD_IA", 1024, TB_KB, 1) == s3cost.storage_cost("STANDARD_IA", 1024, TB_KB, 30) == 12.8
    # Standard has no minimum: 15 days is half a month
    assert s3cost.storage_cost("STANDARD", 1024, TB_KB, 15) == 11.78


def test_minimum_object_size_is_billed():
    # 4 KB objects are billed as 128 KB in the IA classes and Glacier IR, not in Standard or the archives
    small = (10_000_000, 4, 30)
    assert s3cost.storage_cost("STANDARD", *small) == 0.88
    assert s3cost.storage_cost("STANDARD_IA", *small) == 15.26
    assert s3cost.storage_cost("STANDARD_IA", 10_000_000, 128, 30) == 15.26
    assert s3cost.storage_cost("GLACIER", 10_000_000, 4, 90) == 0.41


@pytest.mark.parametrize("args,kwargs", [
    (("NOPE", 1, 1, 1), {}),
    (("STANDARD", -1, 1, 1), {}),
    (("STANDARD", 1, -1, 1), {}),
    (("STANDARD", 1, 1, -1), {}),
    (("STANDARD", 1, 1, 1, -1), {}),
    (("GLACIER", 1, 1, 1, 1), {"retrieval": "expedited"}),
    (("STANDARD", 1, 1, 1), {"retrieval": "fast"}),
])
def test_storage_cost_rejects(args, kwargs):
    with pytest.raises(ValueError):
        s3cost.storage_cost(*args, **kwargs)


def test_class_tables_agree():
    assert set(s3cost.MIN_DAYS) == set(s3cost.MIN_OBJECT_KB) == set(s3cost.MILLISECOND_ACCESS) == set(s3cost.CLASSES)
    assert s3cost.MIN_DAYS == {"STANDARD": 0, "STANDARD_IA": 30, "ONEZONE_IA": 30, "GLACIER_IR": 90,
                               "GLACIER": 90, "DEEP_ARCHIVE": 180}
    assert s3cost.SINGLE_AZ == {"ONEZONE_IA"}


# ---------------------------------------------------------------- s3cost.cheapest_class
def test_hot_small_objects_stay_standard():
    assert s3cost.cheapest_class(10_000_000, 4, 30) == ("STANDARD", 0.88)


def test_terabyte_kept_a_year_read_once():
    # needs milliseconds: Glacier Instant Retrieval; can wait hours: Deep Archive
    assert s3cost.cheapest_class(1024, TB_KB, 365, 1024) == ("GLACIER_IR", 80.55)
    assert s3cost.cheapest_class(1024, TB_KB, 365, 1024, millisecond_access=False) == ("DEEP_ARCHIVE", 32.81)


def test_single_az_ok_switches_ia_to_one_zone():
    assert s3cost.cheapest_class(100, TB_KB, 30, 100) == ("STANDARD_IA", 2.25)
    assert s3cost.cheapest_class(100, TB_KB, 30, 100, single_az_ok=True) == ("ONEZONE_IA", 2.0)


def test_cheapest_class_tie_keeps_earlier():
    assert s3cost.cheapest_class(0, 0, 0)[0] == "STANDARD"


# ---------------------------------------------------------------- s3cost.plan_parts / prefixes_needed
def test_plan_parts_smallest_object_edge():
    assert s3cost.plan_parts(5 * 1024 ** 2) == {"part_bytes": 5 * 1024 ** 2, "parts": 1,
                                                "last_part_bytes": 5 * 1024 ** 2, "multipart": False}
    assert s3cost.plan_parts(10 * 1024 ** 2)["parts"] == 2


def test_plan_parts_multipart_advice_threshold():
    assert s3cost.plan_parts(100 * 1024 ** 2)["multipart"] is False
    assert s3cost.plan_parts(100 * 1024 ** 2 + 1)["multipart"] is True


def test_plan_parts_single_put_limit():
    plan = s3cost.plan_parts(5 * 1024 ** 3 + 1)
    assert plan["multipart"] is True and plan["parts"] == 1025 and plan["last_part_bytes"] == 1
    assert s3cost.plan_parts(5 * 1024 ** 3)["multipart"] is True  # over the 100 MB advice


def test_plan_parts_ten_thousand_parts_edge():
    exactly = 10_000 * 5 * 1024 ** 2
    assert s3cost.plan_parts(exactly)["parts"] == 10_000
    bigger = s3cost.plan_parts(exactly + 1)          # the default part size grows by 1 MiB
    assert bigger["part_bytes"] == 6 * 1024 ** 2 and bigger["parts"] < 10_000
    with pytest.raises(ValueError):
        s3cost.plan_parts(exactly + 1, part_mib=5)


def test_plan_parts_last_part_and_biggest_object():
    plan = s3cost.plan_parts(12 * 1024 ** 2, part_mib=5)
    assert (plan["parts"], plan["last_part_bytes"]) == (3, 2 * 1024 ** 2)
    top = s3cost.plan_parts(50 * 10 ** 12)
    assert top["parts"] <= 10_000 and top["part_bytes"] <= 5 * 1024 ** 3
    assert (top["parts"] - 1) * top["part_bytes"] < 50 * 10 ** 12 <= top["parts"] * top["part_bytes"]


@pytest.mark.parametrize("size,part", [(0, None), (-1, None), (50 * 10 ** 12 + 1, None),
                                       (10 ** 9, 4), (10 ** 9, 5121)])
def test_plan_parts_rejects(size, part):
    with pytest.raises(ValueError):
        s3cost.plan_parts(size, part)


@pytest.mark.parametrize("gets,puts,want", [(0, 0, 1), (5500, 3500, 1), (5501, 0, 2), (0, 3501, 2),
                                            (11_000, 3_500, 2), (55_000, 100, 10), (100, 35_000, 10)])
def test_prefixes_needed(gets, puts, want):
    assert s3cost.prefixes_needed(gets, puts) == want


def test_prefixes_needed_rejects():
    with pytest.raises(ValueError):
        s3cost.prefixes_needed(-1, 0)
    with pytest.raises(ValueError):
        s3cost.prefixes_needed(0, -1)


# ---------------------------------------------------------------- lifecycle
LOGS = {"ID": "logs", "Status": "Enabled", "Filter": {"Prefix": "alb/"},
        "Transitions": [{"Days": 30, "StorageClass": "STANDARD_IA"}, {"Days": 90, "StorageClass": "GLACIER_IR"},
                        {"Days": 180, "StorageClass": "GLACIER"}],
        "Expiration": {"Days": 365}}


def test_realistic_rule_is_valid():
    lifecycle.validate([LOGS])


def test_waterfall_constant():
    assert lifecycle.WATERFALL == ("STANDARD", "STANDARD_IA", "INTELLIGENT_TIERING", "ONEZONE_IA",
                                   "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE")


def _rule(**kw):
    base = {"ID": "r", "Status": "Enabled", "Filter": {}}
    base.update(kw)
    return base


@pytest.mark.parametrize("rules,match", [
    ([_rule(Status="On", Expiration={"Days": 5})], "Status"),
    ([_rule()], "no action"),
    ([_rule(Transitions=[{"Days": 30, "StorageClass": "GLACIER"}, {"Days": 400, "StorageClass": "STANDARD_IA"}])], "waterfall"),
    ([_rule(Transitions=[{"Days": 30, "StorageClass": "ONEZONE_IA"}, {"Days": 100, "StorageClass": "STANDARD_IA"}])], "waterfall"),
    ([_rule(Transitions=[{"Days": 30, "StorageClass": "GLACIER_IR"}, {"Days": 100, "StorageClass": "ONEZONE_IA"}])], "waterfall"),
    ([_rule(Transitions=[{"Days": 30, "StorageClass": "DEEP_ARCHIVE"}, {"Days": 400, "StorageClass": "GLACIER"}])], "waterfall"),
    ([_rule(Transitions=[{"Days": 30, "StorageClass": "REDUCED_REDUNDANCY"}])], "valid transition target"),
    ([_rule(Transitions=[{"Days": 60, "StorageClass": "STANDARD_IA"}, {"Days": 60, "StorageClass": "GLACIER"}])], "increase"),
    ([_rule(Transitions=[{"Days": 90, "StorageClass": "STANDARD_IA"}, {"Days": 60, "StorageClass": "GLACIER"}])], "increase"),
    ([_rule(Transitions=[{"Days": 4, "StorageClass": "GLACIER_IR"}, {"Days": 93, "StorageClass": "DEEP_ARCHIVE"}])], "two-step"),
    ([_rule(Transitions=[{"Days": 30, "StorageClass": "STANDARD_IA"}, {"Days": 40, "StorageClass": "GLACIER"}])], "two-step"),
    ([_rule(Transitions=[{"Days": 30, "StorageClass": "STANDARD_IA"}], Expiration={"Days": 30})], "later than every transition"),
    ([_rule(Expiration={"Days": 5, "ExpiredObjectDeleteMarker": True})], "exactly one"),
    ([_rule(Expiration={})], "no action"),
    ([_rule(Expiration={"Days": 5}), _rule(Expiration={"Days": 9})], "duplicate"),
    ([_rule(NoncurrentVersionExpiration={"NewerNoncurrentVersions": 3})], "NoncurrentDays"),
    ([_rule(NoncurrentVersionExpiration={"NoncurrentDays": 5, "NewerNoncurrentVersions": 0})], "1 to 100"),
    ([_rule(NoncurrentVersionExpiration={"NoncurrentDays": 5, "NewerNoncurrentVersions": 101})], "1 to 100"),
    ([{"ID": "r", "Status": "Enabled", "NoncurrentVersionExpiration": {"NoncurrentDays": 5, "NewerNoncurrentVersions": 2}}], "Filter"),
    ([_rule(Filter={"Tag": {"Key": "k", "Value": "v"}}, Expiration={"ExpiredObjectDeleteMarker": True})], "tag filter"),
    ([_rule(Filter={"And": {"Prefix": "a/", "Tags": [{"Key": "k", "Value": "v"}]}},
            AbortIncompleteMultipartUpload={"DaysAfterInitiation": 7})], "tag filter"),
    ([_rule(Filter={"Prefix": "a/", "ObjectSizeGreaterThan": 5}, Expiration={"Days": 5})], "And"),
    ([_rule(NoncurrentVersionTransitions=[{"NoncurrentDays": 30, "StorageClass": "GLACIER"},
                                          {"NoncurrentDays": 400, "StorageClass": "GLACIER_IR"}])], "waterfall"),
    ([_rule(NoncurrentVersionTransitions=[{"NoncurrentDays": 4, "StorageClass": "GLACIER_IR"},
                                          {"NoncurrentDays": 50, "StorageClass": "DEEP_ARCHIVE"}])], "two-step"),
    ([_rule(NoncurrentVersionTransitions=[{"NoncurrentDays": 30, "StorageClass": "GLACIER"}],
            NoncurrentVersionExpiration={"NoncurrentDays": 20})], "later than every noncurrent"),
    ([_rule(Expiration={"Days": 5}, ID="x" * 256)], "255"),
])
def test_validate_rejects(rules, match):
    with pytest.raises(ValueError, match=match):
        lifecycle.validate(rules)


def test_validate_accepts_edges():
    lifecycle.validate([_rule(Transitions=[{"Days": 4, "StorageClass": "GLACIER_IR"},
                                           {"Days": 94, "StorageClass": "DEEP_ARCHIVE"}])])
    lifecycle.validate([_rule(Status="Disabled", Expiration={"Days": 1})])
    lifecycle.validate([_rule(Filter={"Prefix": "tmp/"}, AbortIncompleteMultipartUpload={"DaysAfterInitiation": 7})])
    lifecycle.validate([_rule(Filter={}, Expiration={"ExpiredObjectDeleteMarker": True})])
    lifecycle.validate([_rule(NoncurrentVersionExpiration={"NoncurrentDays": 30, "NewerNoncurrentVersions": 3})])
    lifecycle.validate([_rule(Transitions=[{"Days": 0, "StorageClass": "STANDARD_IA"}])])


def test_validate_rejects_too_many_rules():
    with pytest.raises(ValueError, match="1000"):
        lifecycle.validate([{"ID": str(i), "Status": "Enabled", "Expiration": {"Days": 1}} for i in range(1001)])


def test_validate_does_not_enforce_the_unconfirmed_30_day_rule():
    lifecycle.validate([_rule(Transitions=[{"Days": 1, "StorageClass": "STANDARD_IA"}])])


def test_validate_does_not_change_rules():
    rules = [copy.deepcopy(LOGS)]
    lifecycle.validate(rules)
    assert rules == [LOGS]


KB = 1024


@pytest.mark.parametrize("age,want", [(0, "STANDARD"), (29, "STANDARD"), (30, "STANDARD_IA"), (89, "STANDARD_IA"),
                                      (90, "GLACIER_IR"), (179, "GLACIER_IR"), (180, "GLACIER"), (364, "GLACIER"),
                                      (365, "EXPIRED"), (1000, "EXPIRED")])
def test_current_class_logs_rule(age, want):
    assert lifecycle.current_class([LOGS], "alb/2026/10/a.log.gz", age, 10 * KB * KB) == want


def test_current_class_filter_misses():
    assert lifecycle.current_class([LOGS], "other/a.log", 400, 10 * KB * KB) == "STANDARD"
    disabled = {**LOGS, "Status": "Disabled"}
    assert lifecycle.current_class([disabled], "alb/a", 400, 10 * KB * KB) == "STANDARD"


def test_small_objects_are_not_transitioned_but_still_expire():
    assert lifecycle.current_class([LOGS], "alb/a", 200, 127 * KB) == "STANDARD"
    assert lifecycle.current_class([LOGS], "alb/a", 200, 128 * KB) == "GLACIER"
    assert lifecycle.current_class([LOGS], "alb/a", 365, 1) == "EXPIRED"


def test_size_filter_lets_small_objects_transition():
    rule = _rule(Filter={"ObjectSizeLessThan": 128 * KB}, Transitions=[{"Days": 30, "StorageClass": "GLACIER"}])
    assert lifecycle.current_class([rule], "a", 40, 10 * KB) == "GLACIER"
    assert lifecycle.current_class([rule], "a", 40, 128 * KB) == "STANDARD"   # strictly less than
    big = _rule(Filter={"ObjectSizeGreaterThan": 1000}, Transitions=[{"Days": 30, "StorageClass": "GLACIER"}])
    assert lifecycle.current_class([big], "a", 40, 1000) == "STANDARD"        # strictly greater than
    assert lifecycle.current_class([big], "a", 40, 1001) == "GLACIER"


def test_tag_and_combined_filters():
    tagged = _rule(Filter={"Tag": {"Key": "tier", "Value": "cold"}}, Transitions=[{"Days": 10, "StorageClass": "GLACIER_IR"}])
    assert lifecycle.current_class([tagged], "a", 20, 1 << 20, {"tier": "cold"}) == "GLACIER_IR"
    assert lifecycle.current_class([tagged], "a", 20, 1 << 20, {"tier": "hot"}) == "STANDARD"
    assert lifecycle.current_class([tagged], "a", 20, 1 << 20) == "STANDARD"
    both = _rule(Filter={"And": {"Prefix": "p/", "Tags": [{"Key": "a", "Value": "1"}, {"Key": "b", "Value": "2"}],
                                 "ObjectSizeGreaterThan": 10}},
                 Expiration={"Days": 5})
    assert lifecycle.current_class([both], "p/x", 6, 100, {"a": "1", "b": "2", "c": "3"}) == "EXPIRED"
    assert lifecycle.current_class([both], "p/x", 6, 100, {"a": "1"}) == "STANDARD"
    assert lifecycle.current_class([both], "q/x", 6, 100, {"a": "1", "b": "2"}) == "STANDARD"


def test_several_rules_expiration_beats_transition_and_furthest_wins():
    cold = _rule(ID="cold", Transitions=[{"Days": 10, "StorageClass": "GLACIER"}])
    ia = _rule(ID="ia", Transitions=[{"Days": 5, "StorageClass": "STANDARD_IA"}])
    gone = _rule(ID="gone", Expiration={"Days": 20})
    assert lifecycle.current_class([ia, cold], "a", 12, 1 << 20) == "GLACIER"
    assert lifecycle.current_class([cold, ia], "a", 7, 1 << 20) == "STANDARD_IA"
    assert lifecycle.current_class([ia, cold, gone], "a", 20, 1 << 20) == "EXPIRED"


NONCURRENT = _rule(ID="nc", Filter={"Prefix": "docs/"},
                   NoncurrentVersionTransitions=[{"NoncurrentDays": 30, "StorageClass": "GLACIER_IR"}],
                   NoncurrentVersionExpiration={"NoncurrentDays": 90, "NewerNoncurrentVersions": 3})


def test_noncurrent_fate():
    nf = lifecycle.noncurrent_fate
    assert nf([NONCURRENT], "docs/a", 10) == "STANDARD"
    assert nf([NONCURRENT], "docs/a", 30) == "GLACIER_IR"
    assert nf([NONCURRENT], "docs/a", 90, newer_noncurrent=2) == "GLACIER_IR"   # still within the 3 newest to keep
    assert nf([NONCURRENT], "docs/a", 90, newer_noncurrent=3) == "DELETED"
    assert nf([NONCURRENT], "docs/a", 89, newer_noncurrent=50) == "GLACIER_IR"
    assert nf([NONCURRENT], "other/a", 500, newer_noncurrent=50) == "STANDARD"


def test_noncurrent_expiration_without_count_and_small_objects():
    plain = _rule(NoncurrentVersionExpiration={"NoncurrentDays": 7})
    assert lifecycle.noncurrent_fate([plain], "a", 7) == "DELETED"
    assert lifecycle.noncurrent_fate([plain], "a", 6) == "STANDARD"
    assert lifecycle.noncurrent_fate([NONCURRENT], "docs/a", 40, size_bytes=1000) == "STANDARD"


# ---------------------------------------------------------------- ebs
def test_gp2_iops():
    assert ebs.gp2_iops(10) == 100
    assert ebs.gp2_iops(33) == 100
    assert ebs.gp2_iops(34) == 102
    assert ebs.gp2_iops(1000) == 3000
    assert ebs.gp2_iops(5334) == 16_000
    assert ebs.gp2_iops(16_384) == 16_000


@pytest.mark.parametrize("size", [0, 16_385])
def test_gp2_iops_rejects(size):
    with pytest.raises(ValueError):
        ebs.gp2_iops(size)


def test_gp3_config_fills_the_free_baseline():
    assert ebs.gp3_config(100) == {"iops": 3000, "throughput": 125}
    assert ebs.gp3_config(1) == {"iops": 3000, "throughput": 125}
    assert ebs.gp3_config(100, iops=5000) == {"iops": 5000, "throughput": 125}


def test_gp3_config_maximums():
    assert ebs.gp3_config(160, 80_000, 2000) == {"iops": 80_000, "throughput": 2000}
    assert ebs.gp3_config(64 * 1024) == {"iops": 3000, "throughput": 125}


@pytest.mark.parametrize("args", [
    (0,), (65_537,),                 # size range 1 GiB to 64 TiB
    (200, 80_001),                   # over the 80,000 IOPS maximum
    (159, 80_000),                   # 500 IOPS per GiB: 160 GiB needed
    (100, 50_001),                   # 100 GiB gives 50,000
    (200, 4000, 2001),               # over 2,000 MiB/s
    (200, 4000, 1001),               # 0.25 MiB/s per IOPS: 4,000 IOPS gives 1,000
    (200, 2999),                     # below the free baseline
    (200, None, 124),                # below the free 125 MiB/s
])
def test_gp3_config_rejects(args):
    with pytest.raises(ValueError):
        ebs.gp3_config(*args)


def test_gp3_throughput_ratio_edge():
    assert ebs.gp3_config(200, 4000, 1000)["throughput"] == 1000
    assert ebs.gp3_config(200, None, 750)["throughput"] == 750
    with pytest.raises(ValueError):
        ebs.gp3_config(200, None, 751)


def test_monthly_cost_gp3():
    assert ebs.monthly_cost("gp3", 100) == 8.0
    assert ebs.monthly_cost("gp3", 500, 6000, 500) == 77.5           # 40 + 3,000 x 0.005 + 375 x 0.06
    assert ebs.monthly_cost("gp3", 100, throughput=125) == 8.0


def test_monthly_cost_other_types():
    assert ebs.monthly_cost("gp2", 100) == 10.0
    assert ebs.monthly_cost("st1", 1000) == 45.0
    assert ebs.monthly_cost("sc1", 1000) == 15.0
    assert ebs.monthly_cost("io2", 1000, 10_000) == 775.0            # 125 + 10,000 x 0.065
    assert ebs.monthly_cost("io2", 1000, 40_000) == 2573.0           # 125 + 32,000 x 0.065 + 8,000 x 0.046


def test_gp3_is_cheaper_than_gp2_per_gib():
    assert ebs.monthly_cost("gp3", 1000) == 0.8 * ebs.monthly_cost("gp2", 1000)


@pytest.mark.parametrize("args,kwargs", [
    (("magnetic", 100), {}),
    (("st1", 124), {}), (("sc1", 16_385), {}), (("io2", 3), {"iops": 100}),
    (("io2", 100), {}),                     # io2 needs iops
    (("io2", 100), {"iops": 100_001}),      # 1,000 IOPS per GiB
    (("io2", 1000), {"iops": 256_001}),
    (("io2", 1000), {"iops": 70_000}),      # third price tier unknown
    (("io2", 1000), {"iops": 1000, "throughput": 4001}),
    (("gp2", 100), {"iops": 3000}),
    (("st1", 500), {"throughput": 200}),
    (("gp3", 100), {"iops": 80_001}),
])
def test_monthly_cost_rejects(args, kwargs):
    with pytest.raises(ValueError):
        ebs.monthly_cost(*args, **kwargs)


def test_type_tables():
    assert ebs.BOOTABLE == {"gp2", "gp3", "io1", "io2"}
    assert ebs.MULTI_ATTACH == {"io1", "io2"}
    assert "st1" not in ebs.BOOTABLE and "sc1" not in ebs.BOOTABLE


@pytest.mark.parametrize("kwargs,want", [
    ({}, "gp3"),
    ({"iops": 16_000, "throughput_mibs": 1000}, "gp3"),
    ({"iops": 80_000}, "gp3"),
    ({"iops": 80_001}, "io2"),
    ({"throughput_mibs": 2001}, "io2"),
    ({"iops": 256_000, "throughput_mibs": 4000}, "io2"),
    ({"multi_attach": True}, "io2"),
    ({"sequential": True, "throughput_mibs": 400}, "st1"),
    ({"sequential": True, "throughput_mibs": 500, "iops": 500}, "st1"),
    ({"sequential": True, "throughput_mibs": 501}, "gp3"),
    ({"sequential": True, "throughput_mibs": 200, "rarely_accessed": True}, "sc1"),
    ({"sequential": True, "throughput_mibs": 251, "rarely_accessed": True}, "st1"),
    ({"sequential": True, "throughput_mibs": 100, "boot": True}, "gp3"),
    ({"rarely_accessed": True}, "gp3"),
    ({"sequential": True, "throughput_mibs": 100, "multi_attach": True}, "io2"),
])
def test_choose_volume(kwargs, want):
    assert ebs.choose_volume(**kwargs) == want


@pytest.mark.parametrize("kwargs", [{"iops": 256_001}, {"throughput_mibs": 4001}, {"multi_attach": True, "boot": True},
                                    {"iops": -1}, {"throughput_mibs": -1}])
def test_choose_volume_rejects(kwargs):
    with pytest.raises(ValueError):
        ebs.choose_volume(**kwargs)

import pytest

from _harness.awslib import ec2types, elb, purchasing, scaling


# ---------------------------------------------------------------- ec2types
def test_decode_m7g_2xlarge():
    assert ec2types.decode("m7g.2xlarge") == {
        "series": "m", "category": "general purpose", "generation": 7, "options": ["g"],
        "processor": "AWS Graviton", "size": "2xlarge", "burstable": False, "instance_store": False,
        "bare_metal": False, "flex": False}


def test_decode_c7gn():
    d = ec2types.decode("c7gn.xlarge")
    assert (d["series"], d["generation"], d["options"], d["processor"]) == ("c", 7, ["g", "n"], "AWS Graviton")
    assert d["category"] == "compute optimized"


def test_decode_instance_store():
    d = ec2types.decode("r6id.large")
    assert d["options"] == ["i", "d"] and d["processor"] == "Intel" and d["instance_store"] is True


def test_decode_flex():
    d = ec2types.decode("m7i-flex.large")
    assert d["options"] == ["i", "flex"] and d["flex"] is True


def test_decode_burstable():
    d = ec2types.decode("t4g.micro")
    assert d["burstable"] is True and d["processor"] == "AWS Graviton"


def test_decode_multi_letter_series():
    d = ec2types.decode("inf2.xlarge")
    assert (d["series"], d["category"], d["generation"], d["options"]) == ("inf", "accelerated computing", 2, [])
    assert ec2types.decode("mac2.metal")["series"] == "mac"
    assert ec2types.decode("mac2.metal")["bare_metal"] is True


def test_decode_many_options():
    assert ec2types.decode("x2iedn.xlarge")["options"] == ["i", "e", "d", "n"]


def test_decode_not_stated_and_case():
    assert ec2types.decode("  C7.Large ")["processor"] == "not stated"
    assert ec2types.decode("M7G.LARGE")["series"] == "m"


@pytest.mark.parametrize("bad", ["m7g", "k7g.large", "mg.large", "m0g.large", "m7y.large", "m7g.huge",
                                 "u-6tb1.metal", "m7g.0xlarge", ""])
def test_decode_rejects(bad):
    with pytest.raises(ValueError):
        ec2types.decode(bad)


@pytest.mark.parametrize("args, kwargs, expected", [
    ((8, 32), {}, "m7g.2xlarge"), ((4, 8), {}, "c7g.xlarge"), ((2, 16), {}, "r7g.large"),
    ((2, 5), {}, "m7g.large"), ((16, 64), {"processor": "intel"}, "m7i.4xlarge"), ((1, 4), {}, "m7g.medium"),
    ((4, 16), {"processor": "amd", "generation": 6}, "m6a.xlarge"),
])
def test_choose_type(args, kwargs, expected):
    assert ec2types.choose_type(*args, **kwargs) == expected


@pytest.mark.parametrize("args, kwargs", [
    ((2, 17), {}), ((3, 12), {}), ((6, 24), {}), ((0, 4), {}), ((-4, 8), {}), ((4, 0), {}), ((4, 8), {"processor": "arm"}),
])
def test_choose_type_rejects(args, kwargs):
    with pytest.raises(ValueError):
        ec2types.choose_type(*args, **kwargs)


# -------------------------------------------------------------- purchasing
def test_prices_come_from_toml():
    assert purchasing.PRICES["m7g_large_per_hour"] == 0.0816
    assert purchasing.PRICES["compute_savings_plan_discount"] == 0.31


def test_monthly_cost_each_option():
    rate = 0.1
    assert purchasing.monthly_cost("on-demand", rate, 10, 100) == 100.0
    assert purchasing.monthly_cost("spot", rate, 10, 100) == 30.0
    assert purchasing.monthly_cost("compute savings plan", rate, 10, 100) == round(10 * 730 * 0.1 * 0.69, 2)
    assert purchasing.monthly_cost("standard reserved", rate, 10, 0) == 438.0


def test_commitments_pay_for_unused_hours():
    assert (purchasing.monthly_cost("compute savings plan", 0.0816, 4, 0)
            == purchasing.monthly_cost("compute savings plan", 0.0816, 4, 730))


@pytest.mark.parametrize("args", [("nope", 0.1, 1, 1), ("on-demand", -0.1, 1, 1), ("on-demand", 0.1, -1, 1),
                                  ("on-demand", 0.1, 1, -1), ("on-demand", 0.1, 1, 731)])
def test_monthly_cost_rejects(args):
    with pytest.raises(ValueError):
        purchasing.monthly_cost(*args)


def test_cheapest_light_use_is_on_demand():
    assert purchasing.cheapest(0.1, 1, 100)[0] == "on-demand"


def test_cheapest_steady_use_prefers_standard_ri_unless_family_may_change():
    assert purchasing.cheapest(0.1, 1, 730)[0] == "standard reserved"
    assert purchasing.cheapest(0.1, 1, 730, may_change_family=True)[0] == "compute savings plan"


def test_cheapest_spot_only_if_interruptible():
    assert purchasing.cheapest(0.1, 1, 730)[0] != "spot"
    assert purchasing.cheapest(0.1, 1, 730, interruptible=True) == ("spot", 21.9)


def test_cheapest_tie_keeps_earlier_option():
    assert purchasing.cheapest(0.0, 3, 10, interruptible=True) == ("on-demand", 0.0)


def test_break_even_hours():
    assert purchasing.break_even_hours("compute savings plan") == 503.7
    assert purchasing.break_even_hours("standard reserved") == 438.0
    assert purchasing.break_even_hours("standard reserved", hours_in_month=720) == 432.0


@pytest.mark.parametrize("option", ["on-demand", "spot", "bogus"])
def test_break_even_rejects(option):
    with pytest.raises(ValueError):
        purchasing.break_even_hours(option)


# ----------------------------------------------------------------- scaling
@pytest.mark.parametrize("args, expected", [((4, 90, 50, 2, 10), 8), ((4, 20, 50, 2, 10), 2),
                                            ((10, 100, 50, 2, 12), 12), ((0, 90, 50, 2, 10), 2),
                                            ((3, 50, 50, 1, 10), 3), ((10, 55, 50, 1, 30), 11)])
def test_target_tracking(args, expected):
    assert scaling.target_tracking(*args) == expected


def test_target_tracking_float_error_does_not_round_up():
    assert scaling.target_tracking(3, 0.7 * 10, 7.0, 1, 10) == 3  # 3 * 7.000000000000001 / 7


@pytest.mark.parametrize("args", [(-1, 50, 50, 1, 5), (2, 50, 0, 1, 5), (2, 50, -5, 1, 5), (2, 50, 50, 6, 5), (2, 50, 50, -1, 5)])
def test_target_tracking_rejects(args):
    with pytest.raises(ValueError):
        scaling.target_tracking(*args)


STEPS = [(0, 10, 1), (10, 20, 2), (20, None, 3)]


@pytest.mark.parametrize("metric, expected", [(65, 5), (80, 7), (75, 6), (60, 5), (70, 6), (59, 4)])
def test_step_scaling_above(metric, expected):
    assert scaling.step_scaling(4, metric, 60, STEPS, 1, 10) == expected


def test_step_scaling_below_threshold_bounds():
    steps = [(None, -20, -2), (-20, -10, -1)]
    assert scaling.step_scaling(5, 40, 60, steps, 1, 10) == 3      # breach -20: upper inclusive of the first step, lower exclusive of the second
    assert scaling.step_scaling(5, 30, 60, steps, 1, 10) == 3      # breach -30
    assert scaling.step_scaling(5, 50, 60, steps, 1, 10) == 4      # breach -10: upper inclusive of (-20, -10]
    assert scaling.step_scaling(5, 55, 60, steps, 1, 10) == 5      # breach -5: nothing


def test_step_scaling_clamps_and_negative_change():
    assert scaling.step_scaling(9, 90, 60, STEPS, 1, 10) == 10
    assert scaling.step_scaling(2, 40, 60, [(None, 0, -5)], 2, 10) == 2


def test_step_scaling_overlap_rejected():
    with pytest.raises(ValueError):
        scaling.step_scaling(4, 70, 60, [(0, 15, 1), (10, None, 2)], 1, 10)
    with pytest.raises(ValueError):
        scaling.step_scaling(4, 70, 60, [(0, None, 1), (5, 10, 2)], 1, 10)
    with pytest.raises(ValueError):
        scaling.step_scaling(4, 70, 60, STEPS, 5, 2)


def test_simple_scaling_cooldown_example():
    assert scaling.simple_scaling_run([90] * 7, 2, 70, 30, 1, 300, 1, 10) == [3, 3, 3, 3, 3, 4, 4]


def test_simple_scaling_no_cooldown_and_scale_in():
    assert scaling.simple_scaling_run([90, 90, 90], 2, 70, 30, 1, 0, 1, 10) == [3, 4, 5]
    assert scaling.simple_scaling_run([10, 10, 50, 10], 3, 70, 30, 2, 0, 1, 10) == [1, 1, 1, 1]


def test_simple_scaling_clamp_does_not_start_cooldown():
    # at max already: no change, so no cooldown; once load drops the scale-in happens at once
    assert scaling.simple_scaling_run([90, 10], 5, 70, 30, 1, 300, 1, 5) == [5, 4]


def test_simple_scaling_rejects_bad_bounds():
    with pytest.raises(ValueError):
        scaling.simple_scaling_run([1], 2, 70, 30, 1, 300, 5, 2)


def test_default_cooldown_constant():
    assert scaling.DEFAULT_COOLDOWN == 300


@pytest.mark.parametrize("kind, ec2_ok, elb_ok, grace, expected", [
    ("EC2", True, False, False, False), ("EC2", False, True, False, True),
    ("ELB", True, False, False, True), ("ELB", False, True, False, True), ("ELB", True, True, False, False),
    ("ELB", False, False, True, False),
])
def test_replaces_instance(kind, ec2_ok, elb_ok, grace, expected):
    assert scaling.replaces_instance(kind, ec2_ok, elb_ok, grace) is expected


def test_replaces_instance_rejects_unknown_type():
    with pytest.raises(ValueError):
        scaling.replaces_instance("HTTP", True, True)


# --------------------------------------------------------------------- elb
REQ = {"host": "api.shortly.example", "path": "/api/links", "method": "GET",
       "headers": {"User-Agent": "Mozilla Mobile Safari"}, "query": {"lang": "en", "Version": "V1"},
       "source_ip": "203.0.113.7"}


def rule(priority, action, *conditions):
    return {"priority": priority, "conditions": list(conditions), "action": action}


DEFAULT = {"priority": "default", "conditions": [], "action": "default"}


def test_match_rule_priority_order_and_default():
    rules = [DEFAULT, rule(20, "late", {"field": "path-pattern", "values": ["/api/*"]}),
             rule(10, "early", {"field": "host-header", "values": ["*.shortly.example"]})]
    assert elb.match_rule(REQ, rules) == "early"
    assert elb.match_rule({**REQ, "host": "other.test"}, rules) == "late"
    assert elb.match_rule({"host": "x.test", "path": "/"}, rules) == "default"


def test_match_rule_all_conditions_and_any_value():
    r = rule(1, "hit", {"field": "path-pattern", "values": ["/nope", "/api/*"]},
             {"field": "http-request-method", "values": ["POST"]})
    assert elb.match_rule(REQ, [r, DEFAULT]) == "default"
    assert elb.match_rule({**REQ, "method": "POST"}, [r, DEFAULT]) == "hit"


def test_host_header_case_and_wildcard():
    r = rule(1, "hit", {"field": "host-header", "values": ["*.EXAMPLE.com"]})
    assert elb.match_rule({"host": "test.example.com"}, [r, DEFAULT]) == "hit"
    assert elb.match_rule({"host": "example.com"}, [r, DEFAULT]) == "default"


def test_path_is_case_sensitive_and_ignores_query():
    r = rule(1, "hit", {"field": "path-pattern", "values": ["/api/?inks"]})
    assert elb.match_rule({"path": "/api/links"}, [r, DEFAULT]) == "hit"
    assert elb.match_rule({"path": "/API/links"}, [r, DEFAULT]) == "default"
    assert elb.match_rule({"path": "/api/links?x=1"}, [r, DEFAULT]) == "hit"


def test_method_is_exact_and_case_sensitive():
    r = rule(1, "hit", {"field": "http-request-method", "values": ["GET"]})
    assert elb.match_rule({"method": "GET"}, [r, DEFAULT]) == "hit"
    assert elb.match_rule({"method": "get"}, [r, DEFAULT]) == "default"
    star = rule(1, "hit", {"field": "http-request-method", "values": ["G*"]})
    assert elb.match_rule({"method": "GET"}, [star, DEFAULT]) == "default"


def test_http_header_name_and_value_ignore_case():
    r = rule(1, "hit", {"field": "http-header", "name": "user-agent", "values": ["*mobile*"]})
    assert elb.match_rule(REQ, [r, DEFAULT]) == "hit"
    assert elb.match_rule({"headers": {}}, [r, DEFAULT]) == "default"
    assert elb.match_rule({}, [r, DEFAULT]) == "default"


def test_query_string_key_value_and_value_only():
    both = rule(1, "hit", {"field": "query-string", "values": [{"key": "VERSION", "value": "v1"}]})
    assert elb.match_rule(REQ, [both, DEFAULT]) == "hit"
    wrong_key = rule(1, "hit", {"field": "query-string", "values": [{"key": "lang", "value": "v1"}]})
    assert elb.match_rule(REQ, [wrong_key, DEFAULT]) == "default"
    value_only = rule(1, "hit", {"field": "query-string", "values": [{"value": "E?"}]})
    assert elb.match_rule(REQ, [value_only, DEFAULT]) == "hit"


def test_source_ip():
    r = rule(1, "hit", {"field": "source-ip", "values": ["203.0.113.0/24"]})
    assert elb.match_rule(REQ, [r, DEFAULT]) == "hit"
    assert elb.match_rule({**REQ, "source_ip": "198.51.100.1"}, [r, DEFAULT]) == "default"
    assert elb.match_rule({}, [r, DEFAULT]) == "default"


def test_rule_validation():
    cond = {"field": "path-pattern", "values": ["/a"]}
    bad_sets = [
        [rule(1, "x", cond)],                                        # no default
        [DEFAULT, DEFAULT],                                          # two defaults
        [{**DEFAULT, "conditions": [cond]}],                         # default with conditions
        [DEFAULT, rule(1, "x", cond), rule(1, "y", cond)],           # duplicate priority
        [DEFAULT, rule(0, "x", cond)],                               # below 1
        [DEFAULT, rule(50001, "x", cond)],                           # above 50000
        [DEFAULT, rule(True, "x", cond)],                            # bool
        [DEFAULT, rule(1.5, "x", cond)],                             # not an int
        [DEFAULT, rule(1, "x")],                                     # numeric rule, no conditions
        [DEFAULT, rule(1, "x", {"field": "nope", "values": ["a"]})],  # unknown field
        [DEFAULT, rule(1, "x", {"field": "host-header", "values": []})],
        [DEFAULT, rule(1, "x", {"field": "host-header", "values": list("abcd")})],  # 4 > 3
        [DEFAULT, rule(1, "x", {"field": "host-header", "values": list("abc")},
                       {"field": "path-pattern", "values": list("abc")})],           # 6 > 5
    ]
    for rules in bad_sets:
        with pytest.raises(ValueError):
            elb.match_rule(REQ, rules)


def test_rule_limits_boundaries_accepted():
    r = rule(50000, "ok", {"field": "host-header", "values": list("abc")},
             {"field": "path-pattern", "values": list("de")})
    assert elb.match_rule(REQ, [r, DEFAULT]) == "default"


def test_cross_zone_docs_example():
    assert elb.cross_zone_share({"a": 2, "b": 8}, True) == {"a": 0.1, "b": 0.1}
    assert elb.cross_zone_share({"a": 2, "b": 8}, False) == {"a": 0.25, "b": 0.0625}


def test_cross_zone_empty_az_is_out_of_dns():
    assert elb.cross_zone_share({"a": 0, "b": 4}, False) == {"a": 0.0, "b": 0.25}
    assert elb.cross_zone_share({"a": 0, "b": 4}, True) == {"a": 0.0, "b": 0.25}


@pytest.mark.parametrize("counts", [{"a": 0, "b": 0}, {}, {"a": -1, "b": 3}])
def test_cross_zone_rejects(counts):
    with pytest.raises(ValueError):
        elb.cross_zone_share(counts, True)


def test_alb_monthly_cost():
    assert elb.alb_monthly_cost(0) == 16.43
    assert elb.alb_monthly_cost(10) == round(730 * (0.0225 + 10 * 0.008), 2) == 74.83
    assert elb.alb_monthly_cost(1, hours=100) == 3.05


@pytest.mark.parametrize("args", [(-1,), (1, -5)])
def test_alb_monthly_cost_rejects(args):
    with pytest.raises(ValueError):
        elb.alb_monthly_cost(*args)

"""M03.5 — the HTTP listener and path-based rules: /healthz hidden from the internet, /api/* explicit."""
import pytest

LISTENER = "AWS::ElasticLoadBalancingV2::Listener"
RULE = "AWS::ElasticLoadBalancingV2::ListenerRule"


def of_type(res, type_):
    return {name: r for name, r in res.items() if r["Type"] == type_}


def action_key(action):
    """('forward', 'AppTargetGroup') or ('fixed-response', 404) — comparable in a test."""
    kind = action.get("Type")
    if kind == "forward":
        return ("forward", action.get("TargetGroupArn") or [t.get("TargetGroupArn") for t in (action.get("ForwardConfig") or {}).get("TargetGroups", [])][0])
    if kind == "fixed-response":
        return ("fixed-response", int(action["FixedResponseConfig"]["StatusCode"]))
    return (kind, None)


def to_model_rules(res):
    """The listener rules as elb.match_rule wants them: conditions with AWS field names, plus the default."""
    rules = [{"priority": "default", "conditions": [], "action": action_key(res["HttpListener"]["Properties"]["DefaultActions"][0])}]
    for rule in of_type(res, RULE).values():
        p = rule["Properties"]
        conditions = []
        for c in p.get("Conditions") or []:
            config = c.get("PathPatternConfig") or c.get("HostHeaderConfig") or {}
            conditions.append({"field": c["Field"], "values": list(config.get("Values") or c.get("Values") or [])})
        rules.append({"priority": int(p["Priority"]), "conditions": conditions, "action": action_key(p["Actions"][0])})
    return rules


def route(elb, request, model):
    try:
        return elb.match_rule(request, model)
    except ValueError as exc:
        pytest.fail(f"the listener rules are not valid: {exc}", pytrace=False)


@pytest.fixture
def rules(resources):
    res = resources("compute")
    assert res.get("HttpListener", {}).get("Type") == LISTENER, f"add HttpListener ({LISTENER})"
    return res, to_model_rules(res)


def test_http_listener(resources):
    res = resources("compute")
    assert res.get("HttpListener", {}).get("Type") == LISTENER, f"add HttpListener ({LISTENER})"
    p = res["HttpListener"]["Properties"]
    assert p.get("LoadBalancerArn") == "LoadBalancer", "HttpListener LoadBalancerArn: !Ref LoadBalancer"
    assert (p.get("Port"), p.get("Protocol")) == (80, "HTTP"), "HttpListener: Port 80, Protocol HTTP"
    actions = [action_key(a) for a in p.get("DefaultActions") or []]
    assert actions == [("forward", "AppTargetGroup")], "HttpListener DefaultActions: forward to AppTargetGroup"


def test_no_https_yet(resources):
    for name, listener in of_type(resources("compute"), LISTENER).items():
        p = listener["Properties"]
        assert p.get("Protocol") not in ("HTTPS", "TLS") and int(p.get("Port", 0)) != 443, \
            f"{name}: no HTTPS listener yet. It needs a certificate, which milestone M07 adds; keep M03 HTTP only"


def test_priorities_are_unique(resources):
    res = of_type(resources("compute"), RULE)
    for name in ("HealthzRule", "ApiRule"):
        assert name in res, f"add {name} ({RULE})"
    priorities = [(n, r["Properties"].get("Priority")) for n, r in res.items()]
    values = [p for _, p in priorities]
    assert len(values) == len(set(values)), f"two rules share a priority {priorities}: every rule on a listener needs its own number"
    assert res["HealthzRule"]["Properties"].get("Priority") == 10 and res["ApiRule"]["Properties"].get("Priority") == 20, \
        "HealthzRule has Priority 10 and ApiRule Priority 20 (the lowest number is checked first)"


def test_healthz_is_not_public(rules, elb):
    _, model = rules
    request = {"method": "GET", "path": "/healthz", "host": "shortly-alb.example.com"}
    assert route(elb, request, model) == ("fixed-response", 404), \
        ("GET /healthz from the internet must get a fixed-response 404 from the load balancer. Target health checks go straight "
         "to the instances and never pass through listener rules, so hiding the endpoint does not break them")


def test_api_requests_reach_the_app(rules, elb):
    _, model = rules
    api = {"method": "POST", "path": "/api/links", "host": "shortly-alb.example.com"}
    assert route(elb, api, model) == ("forward", "AppTargetGroup"), "POST /api/links must forward to AppTargetGroup (ApiRule: path-pattern /api/*)"
    short = {"method": "GET", "path": "/Ab3dE9x", "host": "shortly-alb.example.com"}
    assert route(elb, short, model) == ("forward", "AppTargetGroup"), "a short link like /Ab3dE9x must still reach the app (default action)"

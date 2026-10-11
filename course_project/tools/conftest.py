"""Course-owned pytest setup for your shortly-infra repo.

start_milestone.py copies this to tests/conftest.py (with helpers in tests/_course/) and overwrites
it each milestone — don't edit it. It forces fake AWS credentials first, so no test can ever reach
your real AWS account, even if you have a profile configured.
"""
import json
import sys
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parent
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from _course.safety import use_fake_aws_env  # noqa: E402

use_fake_aws_env()

from _course import cfn, policy_eval  # noqa: E402
from _course import cidr as _cidr, dynamo as _dynamo, ec2types as _ec2types, elb as _elb, lifecycle as _lifecycle, netsim as _netsim, scaling as _scaling  # noqa: E402

PARAMS = {"Prefix": "shortly", "Env": "prod"}
ACCOUNT = "111122223333"
PSEUDO = {"AWS::AccountId": ACCOUNT, "AWS::Region": "us-east-1"}
collect_ignore = ["_course"]


def _path(layer: str) -> Path:
    path = REPO / "infra" / f"{layer}.yaml"
    if not path.exists():
        pytest.fail(f"infra/{layer}.yaml does not exist yet", pytrace=False)
    return path


@pytest.fixture(scope="session")
def repo():
    return REPO


@pytest.fixture(scope="session")
def template():
    cache = {}

    def load(layer: str) -> dict:
        if layer not in cache:
            try:
                cache[layer] = cfn.load_template(_path(layer))
            except cfn.TemplateError as exc:
                pytest.fail(f"infra/{layer}.yaml does not load: {exc}", pytrace=False)
        return cache[layer]
    return load


@pytest.fixture(scope="session")
def lint_errors():
    return lambda layer: cfn.errors_only(cfn.lint_template(_path(layer)))


@pytest.fixture
def render():
    return lambda value, **params: cfn.render(value, {**PARAMS, **params}, PSEUDO)


@pytest.fixture
def role_policies(template):
    return lambda layer, role, **params: cfn.role_policies(template(layer), role, {**PARAMS, **params}, PSEUDO)


@pytest.fixture
def trust_policy(template):
    return lambda layer, role, **params: cfn.trust_policy(template(layer), role, {**PARAMS, **params}, PSEUDO)


@pytest.fixture
def evaluator():
    return policy_eval


@pytest.fixture
def resources(template):
    """resources(layer, **params) -> {logical id: resource} that exist for these parameters, with
    every intrinsic function rendered (Conditions and !If applied; parameter Defaults filled in)."""
    return lambda layer, **params: cfn.active_resources(template(layer), {**PARAMS, **params}, PSEUDO)


@pytest.fixture
def outputs(template):
    """outputs(layer, **params) -> the rendered Outputs section."""
    def render(layer, **params):
        tpl = template(layer)
        values = cfn.parameter_values(tpl, {**PARAMS, **params})
        return cfn.render(tpl.get("Outputs") or {}, values, PSEUDO, cfn.evaluate_conditions(tpl, values, PSEUDO), tpl.get("Mappings"))
    return render


@pytest.fixture
def netsim():
    return _netsim


@pytest.fixture
def cidr():
    return _cidr


@pytest.fixture(scope="session")
def ec2types():
    return _ec2types


@pytest.fixture(scope="session")
def elb():
    return _elb


@pytest.fixture(scope="session")
def scaling():
    return _scaling


@pytest.fixture(scope="session")
def lifecycle():
    """The S3 lifecycle model: validate(rules), current_class(...), noncurrent_fate(...)."""
    return _lifecycle


@pytest.fixture(scope="session")
def dynamo():
    """The DynamoDB model: read_units, write_units, provisioned_capacity, monthly_cost_on_demand, …"""
    return _dynamo


@pytest.fixture
def user_data(resources):
    """user_data(layer, logical_id, **params) -> the rendered text of a launch template's UserData
    (the input of Fn::Base64, not encoded)."""
    def read(layer: str, logical_id: str, **params) -> str:
        res = resources(layer, **params).get(logical_id)
        if res is None:
            pytest.fail(f"infra/{layer}.yaml has no resource {logical_id}", pytrace=False)
        text = ((res.get("Properties") or {}).get("LaunchTemplateData") or {}).get("UserData")
        if not isinstance(text, str):
            pytest.fail(f"{logical_id}: LaunchTemplateData needs UserData: !Base64 !Sub | …", pytrace=False)
        return text
    return read


@pytest.fixture
def moto_stacks():
    """deploy(layer, skip_types=(), getatt_values=None, **params) creates the stack in a fake AWS (moto) and returns its status. Stacks that
    import another stack's exports (compute needs iam and network) are deployed after it, in the same test.
    moto skips some resource types silently, so tests only read back what moto really models."""
    import boto3
    from moto import mock_aws

    mock = mock_aws()
    mock.start()

    def deploy(layer: str, skip_types=(), getatt_values=None, **params) -> str:
        """skip_types: resource types moto cannot create (removed from the template, with the Outputs and
        references that point at them); getatt_values: {"Logical.Attr": "literal"} for attributes moto lacks."""
        merged = {**PARAMS, **params}
        tpl = cfn.load_template_text(_path(layer).read_text(encoding="utf-8"))
        declared = tpl.get("Parameters") or {}
        # moto cannot evaluate !Cidr, so hand it the rendered subnet blocks instead
        flat = cfn.inline_functions(tpl, {"Fn::Cidr"}, merged, PSEUDO)
        if skip_types or getatt_values:
            flat = cfn.for_moto(flat, skip_types, getatt_values)
        body = json.dumps(flat)
        cf = boto3.client("cloudformation", region_name="us-east-1")
        cf.create_stack(StackName=f"shortly-{layer}", TemplateBody=body,
                        Capabilities=["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"],
                        Parameters=[{"ParameterKey": k, "ParameterValue": str(v)} for k, v in merged.items() if k in declared])
        return cf.describe_stacks(StackName=f"shortly-{layer}")["Stacks"][0]["StackStatus"]
    yield deploy
    mock.stop()

"""cfn — load, lint and inspect CloudFormation templates.

Shared by drills, milestone tests (copied into the learner's repo as tests/_course/cfn.py) and
verify_course.py. Templates may use short-form tags (!Ref, !Sub, !GetAtt …); loading turns them
into the long form ({"Ref": …}, {"Fn::Sub": …}) as plain dicts and lists.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import tempfile
from importlib.metadata import version
from pathlib import Path
from typing import Any

CACHE_DIR = Path(tempfile.gettempdir()) / "saa-course-lintcache"
DEFAULT_PSEUDO = {
    "AWS::AccountId": "111122223333",
    "AWS::Region": "us-east-1",
    "AWS::Partition": "aws",
    "AWS::URLSuffix": "amazonaws.com",
    "AWS::StackName": "shortly-stack",
    "AWS::NoValue": None,
}
_SUB_VAR = re.compile(r"\$\{([^}]+)\}")


class TemplateError(ValueError):
    """A template could not be loaded or rendered."""


def load_template_text(text: str) -> dict:
    from cfnlint.decode import decode_str

    template, errors = decode_str(text)
    if errors or template is None:
        problems = "; ".join(f"line {e.linenumber}: {e.message}" for e in errors) or "empty template"
        raise TemplateError(problems)
    return json.loads(json.dumps(template))


def load_template(path) -> dict:
    return load_template_text(Path(path).read_text(encoding="utf-8"))


def _run_cfnlint(text: str) -> list[dict]:
    import cfnlint.api

    return [{"rule": m.rule.id, "line": m.linenumber, "message": m.message} for m in cfnlint.api.lint(text)]


def lint_text(text: str) -> list[dict]:
    """cfn-lint findings for a template, cached by (cfn-lint version, text) because one run costs ≈ 2 s."""
    key = hashlib.sha256(f"{version('cfn-lint')}\0{text}".encode("utf-8")).hexdigest()
    cached = CACHE_DIR / f"{key}.json"
    try:
        return json.loads(cached.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    findings = _run_cfnlint(text)
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cached.write_text(json.dumps(findings), encoding="utf-8")
    except OSError:
        pass
    return findings


def lint_template(path) -> list[dict]:
    return lint_text(Path(path).read_text(encoding="utf-8"))


def errors_only(findings: list[dict]) -> list[dict]:
    return [f for f in findings if f["rule"].startswith("E")]


def resources(template: dict, type_: str | None = None) -> dict[str, dict]:
    found = template.get("Resources") or {}
    return {name: res for name, res in found.items() if type_ is None or res.get("Type") == type_}


def _lookup(name: str, params: dict, pseudo: dict):
    if name in params:
        return params[name]
    if name in pseudo:
        return pseudo[name]
    raise TemplateError(f"unknown parameter {name}")


class _NoValue:
    """Marker for {"Ref": "AWS::NoValue"}: the property or list item is dropped."""

    def __repr__(self):
        return "AWS::NoValue"


NOVALUE = _NoValue()
AZ_LETTERS = "abcdef"


def parameter_values(template: dict, params: dict | None = None) -> dict:
    """The template's parameter Defaults, overridden by `params`."""
    defaults = {name: spec["Default"] for name, spec in (template.get("Parameters") or {}).items()
                if isinstance(spec, dict) and "Default" in spec}
    return {**defaults, **(params or {})}


def evaluate_conditions(template: dict, params: dict | None = None, pseudo: dict | None = None) -> dict[str, bool]:
    """Every entry of the template's Conditions section, evaluated with the given parameters.
    Supports Fn::Equals, Fn::Not, Fn::And, Fn::Or and {"Condition": name}."""
    params = parameter_values(template, params)
    pseudo = {**DEFAULT_PSEUDO, **(pseudo or {})}
    raw = template.get("Conditions") or {}
    done: dict[str, bool] = {}

    def value(name: str, stack: tuple = ()) -> bool:
        if name in done:
            return done[name]
        if name not in raw:
            raise TemplateError(f"unknown condition {name}")
        if name in stack:
            raise TemplateError(f"condition {name} refers to itself")
        done[name] = test(raw[name], stack + (name,))
        return done[name]

    def test(expr, stack) -> bool:
        if not isinstance(expr, dict) or len(expr) != 1:
            raise TemplateError(f"bad condition expression {expr!r}")
        (key, arg), = expr.items()
        if key == "Condition":
            return value(arg, stack)
        if key == "Fn::Equals":
            left, right = (render(a, params, pseudo, {}) for a in arg)
            return str(left) == str(right)
        if key == "Fn::Not":
            return not test(arg[0], stack)
        if key == "Fn::And":
            return all(test(a, stack) for a in arg)
        if key == "Fn::Or":
            return any(test(a, stack) for a in arg)
        raise TemplateError(f"unsupported condition function {key}")

    return {name: value(name) for name in raw}


def render(value: Any, params: dict | None = None, pseudo: dict | None = None, conditions: dict | None = None,
           mappings: dict | None = None) -> Any:
    """Resolve intrinsic functions with test parameter values:
    Ref, Fn::Sub, Fn::Join, Fn::Split, Fn::GetAtt, Fn::If, Fn::Select, Fn::GetAZs, Fn::Cidr,
    Fn::ImportValue, Fn::Base64, Fn::FindInMap (looks up the template's Mappings, which active_resources and
    the conftest `outputs` fixture pass in; a missing map or key is a TemplateError).
    A Ref to a resource renders as its logical id; Fn::GetAtt as "Logical.Attr"; Fn::ImportValue as
    "import:<name>"; Fn::GetAZs as the Region's names with letters a–f. Fn::If needs `conditions`
    (see evaluate_conditions). Fn::Split gives the list of pieces of a rendered string (a rendered
    list is an error). Fn::Base64 renders as its rendered input, NOT encoded, so a test can read the
    user data. {"Ref": "AWS::NoValue"} removes the property or list item."""
    global _MAPPINGS
    saved, _MAPPINGS = _MAPPINGS, mappings or {}
    try:
        result = _render(value, params or {}, {**DEFAULT_PSEUDO, **(pseudo or {})}, conditions)
    finally:
        _MAPPINGS = saved
    return None if result is NOVALUE else result


_MAPPINGS: dict = {}


def _render(value, params, pseudo, conditions):
    if isinstance(value, list):
        items = [_render(v, params, pseudo, conditions) for v in value]
        return [i for i in items if i is not NOVALUE]
    if not isinstance(value, dict):
        return value
    if len(value) == 1:
        (key, arg), = value.items()
        if key == "Ref":
            if arg == "AWS::NoValue":
                return NOVALUE
            if arg in params or arg in pseudo:
                return _lookup(arg, params, pseudo)
            return arg
        if key == "Fn::GetAtt":
            parts = arg.split(".", 1) if isinstance(arg, str) else arg
            return f"{parts[0]}.{parts[1]}"
        if key == "Fn::Join":
            sep, items = arg
            rendered = _render(items, params, pseudo, conditions)
            return sep.join(str(i) for i in rendered)
        if key == "Fn::Split":
            delimiter, source = arg
            rendered = _render(source, params, pseudo, conditions)
            if not isinstance(rendered, str):
                raise TemplateError(f"Fn::Split needs a string to split, got {rendered!r}")
            return rendered.split(delimiter)
        if key == "Fn::Base64":
            return _render(arg, params, pseudo, conditions)
        if key == "Fn::Select":
            index, items = arg
            rendered = _render(items, params, pseudo, conditions)
            position = int(_render(index, params, pseudo, conditions))
            if not isinstance(rendered, list) or not 0 <= position < len(rendered):
                raise TemplateError(f"Fn::Select index {position} is outside {rendered!r}")
            return rendered[position]
        if key == "Fn::GetAZs":
            region = _render(arg, params, pseudo, conditions) or pseudo["AWS::Region"]
            return [f"{region}{letter}" for letter in AZ_LETTERS]
        if key == "Fn::Cidr":
            block, count, bits = (_render(a, params, pseudo, conditions) for a in arg)
            network = ipaddress.ip_network(str(block))
            new_prefix = network.max_prefixlen - int(bits)
            subnets = network.subnets(new_prefix=new_prefix)
            return [str(next(subnets)) for _ in range(int(count))]
        if key == "Fn::FindInMap":
            name, first, second = (_render(a, params, pseudo, conditions) for a in arg)
            try:
                return _MAPPINGS[name][first][second]
            except (KeyError, TypeError):
                raise TemplateError(f"Fn::FindInMap: no value for {name} / {first} / {second} in Mappings") from None
        if key == "Fn::ImportValue":
            return f"import:{_render(arg, params, pseudo, conditions)}"
        if key == "Fn::If":
            if conditions is None:
                raise TemplateError("Fn::If needs condition values (use evaluate_conditions)")
            name, if_true, if_false = arg
            if name not in conditions:
                raise TemplateError(f"Fn::If uses unknown condition {name}")
            return _render(if_true if conditions[name] else if_false, params, pseudo, conditions)
        if key == "Fn::Sub":
            text, local = (arg, {}) if isinstance(arg, str) else (arg[0], arg[1])
            local = {k: _render(v, params, pseudo, conditions) for k, v in local.items()}

            def replace(match):
                name = match.group(1)
                if name.startswith("!"):
                    return "${" + name[1:] + "}"
                if name in local:
                    return str(local[name])
                if "." in name:
                    return name
                if name in params or name in pseudo:
                    return str(_lookup(name, params, pseudo))
                raise TemplateError(f"Fn::Sub uses ${{{name}}} but no parameter or pseudo parameter {name} exists")
            return _SUB_VAR.sub(replace, text)
    rendered = {k: _render(v, params, pseudo, conditions) for k, v in value.items()}
    return {k: v for k, v in rendered.items() if v is not NOVALUE}


def active_resources(template: dict, params: dict | None = None, pseudo: dict | None = None) -> dict[str, dict]:
    """Resources that exist for these parameters (their Condition, if any, is true), rendered."""
    params = parameter_values(template, params)
    conditions = evaluate_conditions(template, params, pseudo)
    found = {}
    for name, res in resources(template).items():
        condition = res.get("Condition")
        if condition is not None and not conditions.get(condition, False):
            continue
        found[name] = render(res, params, pseudo, conditions, template.get("Mappings"))
    return found


def inline_functions(template: dict, functions: set[str], params: dict | None = None, pseudo: dict | None = None) -> dict:
    """A copy of the template where every call to one of `functions` (e.g. {"Fn::Cidr"}) is replaced
    by its rendered value — for tools such as moto that cannot evaluate those functions."""
    params = parameter_values(template, params)
    conditions = evaluate_conditions(template, params, pseudo)

    def walk(value):
        if isinstance(value, list):
            return [walk(v) for v in value]
        if isinstance(value, dict):
            if len(value) == 1 and next(iter(value)) in functions:
                return render(value, params, pseudo, conditions, template.get("Mappings"))
            return {k: walk(v) for k, v in value.items()}
        return value
    return walk(template)


def _role(template: dict, logical_id: str) -> dict:
    res = resources(template).get(logical_id)
    if res is None or res.get("Type") != "AWS::IAM::Role":
        raise TemplateError(f"no AWS::IAM::Role named {logical_id}")
    return res.get("Properties") or {}


def role_policies(template: dict, logical_id: str, params=None, pseudo=None) -> list[dict]:
    """Every identity policy document attached to a role: inline Policies plus in-template
    AWS::IAM::ManagedPolicy resources referenced from ManagedPolicyArns (AWS-managed ARNs are
    skipped — their contents are not available offline)."""
    props = _role(template, logical_id)
    docs = [p["PolicyDocument"] for p in props.get("Policies") or []]
    for arn in props.get("ManagedPolicyArns") or []:
        if isinstance(arn, dict) and "Ref" in arn:
            target = resources(template).get(arn["Ref"])
            if target and target.get("Type") == "AWS::IAM::ManagedPolicy":
                docs.append(target["Properties"]["PolicyDocument"])
    params = parameter_values(template, params)
    return render(docs, params, pseudo, evaluate_conditions(template, params, pseudo), template.get("Mappings"))


def trust_policy(template: dict, logical_id: str, params=None, pseudo=None) -> dict:
    document = _role(template, logical_id).get("AssumeRolePolicyDocument") or {}
    params = parameter_values(template, params)
    return render(document, params, pseudo, evaluate_conditions(template, params, pseudo), template.get("Mappings"))


def _refs(value) -> set[str]:
    """Logical ids a template fragment points at: Ref, Fn::GetAtt, ${Name} / ${Name.Attr} in Fn::Sub, DependsOn."""
    found: set[str] = set()
    if isinstance(value, list):
        for item in value:
            found |= _refs(item)
    elif isinstance(value, dict):
        for key, arg in value.items():
            if key == "Ref" and isinstance(arg, str):
                found.add(arg)
            elif key == "Fn::GetAtt":
                found.add((arg.split(".", 1)[0] if isinstance(arg, str) else arg[0]))
            elif key == "Fn::Sub":
                text = arg if isinstance(arg, str) else arg[0]
                local = set() if isinstance(arg, str) else set(arg[1])
                found |= {m.split(".", 1)[0] for m in _SUB_VAR.findall(text) if not m.startswith("!")} - local
                if not isinstance(arg, str):
                    found |= _refs(arg[1])
            else:
                found |= _refs(arg)
    return found


def _getatt_name(arg) -> str:
    return arg if isinstance(arg, str) else ".".join(str(p) for p in arg)


def for_moto(template: dict, skip_types, getatt_values: dict | None = None) -> dict:
    """A copy of the template that moto can create, for types moto skips or attributes it lacks:
    - every resource whose Type is in `skip_types` is removed (also from DependsOn lists);
    - every Output that refers to a removed resource, or to an attribute listed in `getatt_values`, is removed;
    - every remaining Fn::GetAtt listed in `getatt_values` ("Logical.Attr.Path" -> literal) is replaced by that literal.
    A resource that still refers to a removed resource is a TemplateError naming both, so the test author
    sees it instead of a confusing crash inside moto."""
    skip_types = set(skip_types or ())
    getatt_values = dict(getatt_values or {})
    out = json.loads(json.dumps(template))
    removed = {name for name, res in (out.get("Resources") or {}).items() if res.get("Type") in skip_types}
    for name in removed:
        del out["Resources"][name]

    def replace(value):
        if isinstance(value, list):
            return [replace(v) for v in value]
        if isinstance(value, dict):
            if len(value) == 1 and next(iter(value)) == "Fn::GetAtt":
                key = _getatt_name(value["Fn::GetAtt"])
                if key in getatt_values:
                    return getatt_values[key]
            return {k: replace(v) for k, v in value.items()}
        return value

    def uses_listed_attribute(value) -> bool:
        if isinstance(value, list):
            return any(uses_listed_attribute(v) for v in value)
        if isinstance(value, dict):
            if len(value) == 1 and next(iter(value)) == "Fn::GetAtt" and _getatt_name(value["Fn::GetAtt"]) in getatt_values:
                return True
            return any(uses_listed_attribute(v) for v in value.values())
        return False

    for name, res in out.get("Resources", {}).items():
        depends = res.get("DependsOn")
        if isinstance(depends, list):
            res["DependsOn"] = [d for d in depends if d not in removed]
        elif depends in removed:
            del res["DependsOn"]
        bad = sorted(_refs(res) & removed)
        if bad:
            raise TemplateError(f"resource {name} still refers to {', '.join(bad)}, which for_moto removed "
                                f"(type in skip_types); remove it too or stop referring to it")
        out["Resources"][name] = replace(res)
    outputs = out.get("Outputs") or {}
    for key in list(outputs):
        if _refs(outputs[key]) & removed or uses_listed_attribute(outputs[key]):
            del outputs[key]
    if "Outputs" in out and not outputs:
        del out["Outputs"]
    return out

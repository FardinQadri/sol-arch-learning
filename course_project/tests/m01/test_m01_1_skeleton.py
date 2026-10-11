"""M01.1 — repo skeleton and the iam stack's parameters."""
import json


def test_layout(repo):
    for rel in ("infra", "params", "README.md", ".gitignore"):
        assert (repo / rel).exists(), f"create {rel}"


def test_gitignore(repo):
    text = (repo / ".gitignore").read_text(encoding="utf-8")
    for entry in (".venv", "__pycache__"):
        assert entry in text, f".gitignore should list {entry}"


def test_params_files(repo):
    for env in ("lab", "prod"):
        path = repo / "params" / f"{env}.json"
        assert path.exists(), f"create params/{env}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data == {"Prefix": "shortly", "Env": env}, f"params/{env}.json should be {{\"Prefix\": \"shortly\", \"Env\": \"{env}\"}}"


def test_iam_parameters_and_lint(template, lint_errors):
    params = template("iam").get("Parameters", {})
    assert params.get("Prefix", {}).get("Default") == "shortly", "Parameter Prefix (String, Default shortly)"
    assert sorted(params.get("Env", {}).get("AllowedValues", [])) == ["lab", "prod"], "Parameter Env with AllowedValues [lab, prod]"
    errors = lint_errors("iam")
    assert errors == [], "cfn-lint errors: " + "; ".join(f"line {e['line']} {e['rule']} {e['message']}" for e in errors)

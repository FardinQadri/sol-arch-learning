"""bankgen — build valid (or deliberately broken) question banks for the maintainer tests."""
import json

from _harness import quizlib


def raw_single(n=1, domain=4, task="4.1", answer="A", stem=None, ref=None, week=4):
    return {
        "id": f"w{week:02d}-q{n:02d}", "domain": domain, "task": task, "services": ["S3"], "kind": "single",
        "stem": stem or (f"Question {n}: a company keeps logs in Amazon S3 and reads them for 30 days, then rarely. "
                         f"Variant {n * 7919 + week * 104729} of the scenario. Which solution is the MOST cost-effective?"),
        "options": [f"Option one {n}", f"Option two {n} longer", f"Option three {n}", f"Option four {n}"],
        "answer": [answer], "explain": {k: f"Because {k}." for k in "ABCD"},
        "ref": ref or "week_04_storage/concepts/01_s3.md",
    }


def raw_multi(n=2, choose=2, ref=None, week=4):
    q = raw_single(n, ref=ref, week=week)
    letters = quizlib.LETTERS[: quizlib.OPTION_COUNT[choose]]
    q.update(kind="multi", choose=choose, options=[f"Choice {c} {n}" for c in letters],
             answer=list(letters[:choose]), explain={c: f"Because {c}." for c in letters},
             stem=q["stem"].replace("Which solution is the MOST cost-effective?",
                                    "Which steps meet these requirements? " + quizlib.SELECT_SUFFIX[choose]))
    return q


def balanced_raws(n=30, multi=4, week=4, ref=None):
    """A bank that passes quizlib.bank_problems: spread answers, the correct option is never the longest."""
    raws = []
    for i in range(1, n + 1):
        if i <= multi:
            raws.append(raw_multi(i, ref=ref, week=week))
            continue
        raw = raw_single(i, answer="ABCD"[i % 4], ref=ref, week=week)
        right = "ABCD".index(raw["answer"][0])
        raw["options"] = [f"Option {i}-{k}" + (" padded" if k == (right + 1) % 4 else "") for k in range(4)]
        raws.append(raw)
    return raws


def toml_bank(questions) -> str:
    lines = []
    for q in questions:
        lines.append("[[question]]")
        for key, value in q.items():
            if key == "explain":
                lines.append("explain = { " + ", ".join(f"{k} = {json.dumps(v)}" for k, v in value.items()) + " }")
            else:
                lines.append(f"{key} = {json.dumps(value)}")
        lines.append("")
    return "\n".join(lines)

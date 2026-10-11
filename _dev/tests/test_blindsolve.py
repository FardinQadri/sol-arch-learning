import json
import subprocess
import sys
from pathlib import Path

from bankgen import balanced_raws, toml_bank

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable


def test_export_hides_answers_and_compare_finds_disagreements(tmp_path):
    bank = tmp_path / "questions.toml"
    raws = balanced_raws(12, multi=2, week=0)
    bank.write_text(toml_bank(raws), encoding="utf-8")
    out = tmp_path / "blind.md"
    proc = subprocess.run([PY, str(ROOT / "_dev" / "blindsolve.py"), "export", str(bank), str(out)],
                          capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    text = out.read_text(encoding="utf-8")
    assert "w00-q01" in text and "Because" not in text  # explanations (and so answers) stay hidden
    assert "(Select TWO.)" in text
    answers = {r["id"]: r["answer"] for r in raws}
    answers["w00-q05"] = ["A"] if raws[4]["answer"] != ["A"] else ["B"]
    (tmp_path / "answers.json").write_text(json.dumps(answers), encoding="utf-8")
    proc = subprocess.run([PY, str(ROOT / "_dev" / "blindsolve.py"), "compare", str(bank), str(tmp_path / "answers.json")],
                          capture_output=True, text=True, timeout=120)
    assert proc.returncode == 1 and "w00-q05" in proc.stdout and "1 disagreement" in proc.stdout

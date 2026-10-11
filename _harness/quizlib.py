"""quizlib — load, validate, run and track the course's scenario-question banks (TOML).

One [[question]] table per question:
    id        "w04-q07" (weekly bank) or "mock1-q42" (mock exam)
    domain    1 Secure · 2 Resilient · 3 High-performing · 4 Cost-optimised
    task      exam task statement, e.g. "4.1" — must belong to the domain
    services  list of AWS services the question is about (non-empty)
    kind      "single" (4 options, 1 answer) or "multi" (choose = 2 → 5 options, 3 → 6 options)
    stem      2–6 sentences; single ends with "?", multi ends with "(Select TWO.)"/"(Select THREE.)"
    options   option texts in order A, B, C, …
    answer    list of correct letters
    explain   table: one explanation per option letter (why right / why wrong)
    ref       course-relative path of the concept note that teaches it
    legacy    optional bool: true when a correct answer is a service closed to new customers (spec §7)
"""
from __future__ import annotations

import datetime as dt
import difflib
import json
import os
import random
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

DOMAINS = {1: "Design Secure Architectures", 2: "Design Resilient Architectures",
           3: "Design High-Performing Architectures", 4: "Design Cost-Optimized Architectures"}
TASKS = {
    "1.1": "Design secure access to AWS resources",
    "1.2": "Design secure workloads and applications",
    "1.3": "Determine appropriate data security controls",
    "2.1": "Design scalable and loosely coupled architectures",
    "2.2": "Design highly available and/or fault-tolerant architectures",
    "3.1": "Determine high-performing and/or scalable storage solutions",
    "3.2": "Design high-performing and elastic compute solutions",
    "3.3": "Determine high-performing database solutions",
    "3.4": "Determine high-performing and/or scalable network architectures",
    "3.5": "Determine high-performing data ingestion and transformation solutions",
    "4.1": "Design cost-optimized storage solutions",
    "4.2": "Design cost-optimized compute solutions",
    "4.3": "Design cost-optimized database solutions",
    "4.4": "Design cost-optimized network architectures",
}
LETTERS = "ABCDEF"
OPTION_COUNT = {1: 4, 2: 5, 3: 6}
SELECT_SUFFIX = {2: "(Select TWO.)", 3: "(Select THREE.)"}
ID_PATTERN = re.compile(r"^(w\d\d|mock\d)-q\d{2,3}$")
LEITNER_DAYS = {1: 0, 2: 1, 3: 3, 4: 7, 5: 16}
REQUIRED = ("id", "domain", "task", "services", "kind", "stem", "options", "answer", "explain", "ref")

# spec §7 rule 1 — never in a bank, only on "retired" lines in notes (case-sensitive proper names)
RETIRED = {name: re.compile(rx) for name, rx in {
    "Amazon QLDB": r"\bQLDB\b",
    "Elastic Transcoder": r"\bElastic Transcoder\b",
    "AWS Data Pipeline": r"\bAWS Data Pipeline\b",
    "AWS Proton": r"\bAWS Proton\b",
    "Amazon Pinpoint": r"\bAmazon Pinpoint\b",
    "AWS OpsWorks": r"\bOpsWorks\b",
    "EC2-Classic": r"\bEC2-Classic\b",
    "Aurora Serverless v1": r"\bAurora Serverless v1\b",
    "Kinesis Data Analytics": r"\bKinesis Data Analytics\b",
    "WAF Classic": r"\bWAF Classic\b",
    "Inspector Classic": r"\bInspector Classic\b",
    "Snowmobile": r"\bSnowmobile\b",
    "Snowcone": r"\bSnowcone\b",
    "launch configurations": r"\b[Ll]aunch [Cc]onfigurations?\b",
    "S3 Select": r"\bS3 Select\b",
    "Glacier vaults": r"\bGlacier [Vv]aults?\b|\bVault Lock\b",
    "AWS Cloud9": r"\bCloud9\b",
    "AWS App Mesh": r"\bApp Mesh\b",
}.items()}
# spec §7 rule 2 — allowed as a correct answer only in questions marked legacy = true
LEGACY = {name: re.compile(rx) for name, rx in {
    "Snowball Edge": r"\bSnowball\b",
    "Application Discovery Service": r"\bApplication Discovery Service\b",
    "Migration Hub": r"\bMigration Hub\b",
}.items()}


class BankError(ValueError):
    """A bank file could not be loaded; the message lists every problem."""


@dataclass(frozen=True)
class Question:
    id: str
    domain: int
    task: str
    services: tuple
    kind: str
    choose: int
    stem: str
    options: tuple
    answer: frozenset
    explain: dict = field(hash=False, compare=False)
    ref: str = ""
    legacy: bool = False
    source: str = ""

    @classmethod
    def from_raw(cls, raw: dict, source: str = "") -> "Question":
        choose = raw.get("choose", 1) if raw.get("kind") == "multi" else 1
        return cls(id=raw["id"], domain=raw["domain"], task=raw["task"], services=tuple(raw["services"]),
                   kind=raw["kind"], choose=choose, stem=raw["stem"].strip(), options=tuple(raw["options"]),
                   answer=frozenset(raw["answer"]), explain=dict(raw["explain"]), ref=raw["ref"],
                   legacy=bool(raw.get("legacy", False)), source=source)


def retired_hits(text: str) -> list[str]:
    return [name for name, rx in RETIRED.items() if rx.search(text)]


def legacy_hits(text: str) -> list[str]:
    return [name for name, rx in LEGACY.items() if rx.search(text)]


def validate_question(raw: dict, root: Path | None = None) -> list[str]:
    qid = raw.get("id", "<no id>")
    problems = [f"missing {key}" for key in REQUIRED if key not in raw]
    if problems:
        return [f"{qid}: {p}" for p in problems]
    p = problems
    if not isinstance(raw["id"], str) or not ID_PATTERN.match(raw["id"]):
        p.append("id must look like w04-q07 or mock1-q42")
    if raw["domain"] not in DOMAINS:
        p.append("domain must be 1, 2, 3 or 4")
    if raw["task"] not in TASKS:
        p.append(f"unknown task {raw['task']!r}")
    elif raw["domain"] in DOMAINS and not raw["task"].startswith(f"{raw['domain']}."):
        p.append(f"task {raw['task']} is not in domain {raw['domain']}")
    if not isinstance(raw["services"], list) or not raw["services"] or not all(isinstance(s, str) and s for s in raw["services"]):
        p.append("services must be a non-empty list of names")
    if "legacy" in raw and not isinstance(raw["legacy"], bool):
        p.append("legacy must be true or false")
    if raw["kind"] not in ("single", "multi"):
        p.append("kind must be single or multi")
        return [f"{qid}: {x}" for x in p]
    choose = raw.get("choose", 1) if raw["kind"] == "multi" else 1
    if raw["kind"] == "multi" and choose not in (2, 3):
        p.append("multi questions need choose = 2 or 3")
        return [f"{qid}: {x}" for x in p]
    if raw["kind"] == "single" and raw.get("choose", 1) != 1:
        p.append("single questions must not set choose")
    want = OPTION_COUNT[choose]
    options = raw["options"]
    if not isinstance(options, list) or len(options) != want:
        p.append(f"needs {want} options")
    elif len(set(options)) != len(options) or not all(isinstance(o, str) and o.strip() for o in options):
        p.append("duplicate options or empty option text")
    letters = LETTERS[:want]
    answer = raw["answer"]
    if not isinstance(answer, list) or any(a not in letters for a in answer) or len(set(answer)) != len(answer):
        p.append(f"answer letters must be distinct letters from {letters}")
    elif len(answer) != choose:
        p.append(f"answer must have exactly {choose} letter(s)")
    explain = raw["explain"]
    if not isinstance(explain, dict) or set(explain) != set(letters) or not all(isinstance(v, str) and v.strip() for v in explain.values()):
        p.append(f"explain needs one non-empty text for each of {', '.join(letters)}")
    stem = raw["stem"].strip() if isinstance(raw["stem"], str) else ""
    if not 80 <= len(stem) <= 1200:
        p.append("stem must be a 2–6 sentence scenario (80–1200 characters)")
    ending = SELECT_SUFFIX[choose] if choose > 1 else "?"
    if stem and not stem.endswith(ending):
        p.append(f"stem must end with {ending}")
    if root is not None and isinstance(raw["ref"], str) and not (Path(root) / raw["ref"]).is_file():
        p.append(f"ref {raw['ref']} does not exist")
    return [f"{qid}: {x}" for x in p]


def load_bank(path, root=None) -> list[Question]:
    path = Path(path)
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise BankError(f"{path}: cannot read TOML: {exc}") from None
    raws = data.get("question", [])
    problems, seen = [], set()
    for raw in raws:
        problems += validate_question(raw, root)
        qid = raw.get("id")
        if qid in seen:
            problems.append(f"duplicate id {qid}")
        seen.add(qid)
    if problems:
        raise BankError(f"{path}:\n  " + "\n  ".join(problems))
    return [Question.from_raw(raw, str(path)) for raw in raws]


def _longest_is_correct(q: Question) -> bool:
    lengths = [len(o) for o in q.options]
    best = max(lengths)
    winners = [LETTERS[i] for i, n in enumerate(lengths) if n == best]
    return len(winners) == 1 and winners[0] in q.answer


def bank_problems(questions: list[Question], expected_count: int) -> list[str]:
    """Bank-level rules from spec §4.3 (count, multi share, answer-letter spread, longest-option bias,
    retired/legacy names, legacy cap)."""
    n = len(questions)
    problems = []
    if n != expected_count:
        problems.append(f"expected {expected_count} questions, found {n}")
    multi = sum(q.kind == "multi" for q in questions)
    low, high = int(0.10 * n), -(-n * 20 // 100)
    if n >= 10 and not low <= multi <= high:
        problems.append(f"{multi} multi-response questions; need {low}–{high} (10–20 %)")
    singles = [q for q in questions if q.kind == "single"]
    if len(singles) >= 12:
        counts = {letter: sum(letter in q.answer for q in singles) for letter in "ABCD"}
        cap, floor = -(-len(singles) * 40 // 100), int(0.10 * len(singles))
        for letter, count in counts.items():
            if count > cap or count < floor:
                problems.append(f"letter {letter} is the answer {count} times out of {len(singles)}; keep each between {floor} and {cap}")
        longest = sum(_longest_is_correct(q) for q in singles)
        if longest > 0.40 * len(singles):
            problems.append(f"the correct option is the longest in {longest} of {len(singles)} single questions (max 40 %)")
    legacy_cap = max(1, int(0.02 * n))
    if sum(q.legacy for q in questions) > legacy_cap:
        problems.append(f"more than {legacy_cap} legacy questions")
    for q in questions:
        text = " ".join([q.stem, *q.options, *q.explain.values()])
        for name in retired_hits(text):
            problems.append(f"{q.id}: mentions retired {name} (spec §7 rule 1)")
        correct = " ".join(q.options[LETTERS.index(a)] for a in q.answer)
        if legacy_hits(correct) and not q.legacy:
            problems.append(f"{q.id}: correct answer uses {', '.join(legacy_hits(correct))} — mark legacy = true (spec §7 rule 2)")
    return problems


def _norm(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", text.lower()).split())


def near_duplicates(questions: list[Question], threshold: float = 0.85) -> list[tuple[str, str, float]]:
    stems = [(q.id, _norm(q.stem)) for q in questions]
    found = []
    for i, (id_a, a) in enumerate(stems):
        for id_b, b in stems[i + 1:]:
            matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
            if matcher.real_quick_ratio() < threshold or matcher.quick_ratio() < threshold:
                continue
            ratio = matcher.ratio()
            if ratio >= threshold:
                found.append((id_a, id_b, round(ratio, 3)))
    return found


# ── answering ───────────────────────────────────────────────────────


def parse_answer(text: str, n_options: int, choose: int) -> tuple[list[str] | None, str]:
    allowed = LETTERS[:n_options]
    cleaned = re.sub(r"[\s,;/]+", "", text or "").upper()
    if not cleaned:
        return None, "Type the letter of your answer (or q to quit)."
    if any(c not in allowed for c in cleaned):
        return None, f"Use letters {allowed[0]}–{allowed[-1]}."
    if len(set(cleaned)) != len(cleaned):
        return None, "Use each letter once."
    if len(cleaned) != choose:
        return None, "Pick one letter." if choose == 1 else f"Pick exactly {choose} letters."
    return sorted(cleaned), ""


def shuffle_options(question: Question, rng: random.Random) -> list[tuple[str, str]]:
    originals = list(LETTERS[:len(question.options)])
    rng.shuffle(originals)
    return list(zip(LETTERS, originals))


def grade(question: Question, original_letters) -> bool:
    return frozenset(original_letters) == question.answer


# ── progress (Leitner boxes) ────────────────────────────────────────


class Progress:
    """Per-question Leitner box (1 = missed … 5 = well known) and due date, saved atomically."""

    def __init__(self, path, today: dt.date | None = None):
        self.path = Path(path)
        self.warning = ""
        self.data = {"version": 1, "questions": {}, "sessions": [], "mocks": []}
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
                if not isinstance(loaded, dict) or not isinstance(loaded.get("questions"), dict):
                    raise ValueError("unexpected shape")
                self.data.update(loaded)
            except (ValueError, OSError):
                stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
                backup = self.path.with_name(f"{self.path.name}.bad-{stamp}")
                os.replace(self.path, backup)
                self.warning = f"Your progress file was damaged; it was backed up to {backup.name} and a fresh one started."

    def _entry(self, qid: str) -> dict:
        return self.data["questions"].get(qid, {})

    def seen(self, qid: str) -> bool:
        return bool(self._entry(qid))

    def box(self, qid: str) -> int:
        return self._entry(qid).get("box", 0)

    def is_due(self, qid: str, today: dt.date) -> bool:
        due = self._entry(qid).get("due")
        return due is not None and dt.date.fromisoformat(due) <= today

    def record(self, qid: str, correct: bool, today: dt.date) -> None:
        entry = self.data["questions"].setdefault(qid, {"box": 0, "seen": 0, "right": 0})
        entry["seen"] += 1
        entry["right"] += int(correct)
        entry["box"] = min(5, max(entry["box"], 1) + 1) if correct else 1
        entry["due"] = (today + dt.timedelta(days=LEITNER_DAYS[entry["box"]])).isoformat()
        entry["last"] = today.isoformat()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps(self.data, indent=1), encoding="utf-8")
        os.replace(tmp, self.path)


def select_questions(questions, progress: Progress, n: int, today: dt.date, rng: random.Random,
                     review: bool = False) -> list[Question]:
    missed = [q for q in questions if progress.seen(q.id) and progress.box(q.id) == 1]
    due = [q for q in questions if progress.seen(q.id) and progress.box(q.id) > 1 and progress.is_due(q.id, today)]
    unseen = [q for q in questions if not progress.seen(q.id)]
    rest = [q for q in questions if q not in missed and q not in due and q not in unseen]
    for group in (missed, due, unseen, rest):
        rng.shuffle(group)
    ordered = missed + due if review else missed + unseen + due + rest
    return ordered[:n]


# ── a terminal session ──────────────────────────────────────────────


def render_question(q: Question, mapping, number: int, total: int) -> str:
    lines = [f"\nQuestion {number} of {total}  ·  Domain {q.domain}: {DOMAINS[q.domain]}  ·  task {q.task}", "", q.stem, ""]
    for display, original in mapping:
        lines.append(f"  {display}. {q.options[LETTERS.index(original)]}")
    return "\n".join(lines)


def render_feedback(q: Question, mapping, correct: bool) -> str:
    right = [d for d, o in mapping if o in q.answer]
    lines = ["", "✔ Correct" if correct else f"✘ Not quite — the answer is {', '.join(right)}", ""]
    for display, original in mapping:
        mark = "✔" if original in q.answer else "·"
        lines.append(f"  {mark} {display}. {q.explain[original]}")
    if q.legacy:
        lines.append("  (legacy: this service is closed to new customers in 2026 but still in the exam guide)")
    lines.append(f"\n  Read more: {q.ref}")
    return "\n".join(lines)


def run_session(questions, progress: Progress, *, input_fn=input, print_fn=print, rng=None, today=None) -> dict:
    rng = rng or random.Random()
    today = today or dt.date.today()
    if progress.warning:
        print_fn(progress.warning)
    asked = correct_count = 0
    quit_ = False
    for number, q in enumerate(questions, 1):
        mapping = shuffle_options(q, rng)
        print_fn(render_question(q, mapping, number, len(questions)))
        prompt = "\nYour answer (one letter, q to quit): " if q.choose == 1 else f"\nYour answer (pick {q.choose}, e.g. AC; q to quit): "
        while True:
            try:
                text = input_fn(prompt)
            except EOFError:
                text = "q"
            if text.strip().lower() == "q":
                quit_ = True
                break
            letters, message = parse_answer(text, len(q.options), q.choose)
            if letters is not None:
                break
            print_fn(message)
        if quit_:
            break
        originals = [dict(mapping)[d] for d in letters]
        ok = grade(q, originals)
        progress.record(q.id, ok, today)
        asked += 1
        correct_count += ok
        print_fn(render_feedback(q, mapping, ok))
    if asked:
        progress.data["sessions"].append({"date": today.isoformat(), "asked": asked, "correct": correct_count})
        print_fn(f"\nScore: {correct_count}/{asked} ({round(100 * correct_count / asked)}%)")
    progress.save()
    return {"asked": asked, "correct": correct_count, "quit": quit_}


def discover_banks(root) -> dict[int, Path]:
    banks = {}
    for path in sorted(Path(root).glob("week_[0-9][0-9]_*/quiz/questions.toml")):
        banks[int(path.parts[-3][5:7])] = path
    return banks

"""lifecycle — validate S3 lifecycle rules and replay what they do to an object.

This is the reference solution for week 04's drill 02 (lifecycle rules): finish that drill before you
read it. Rules use the S3 API shape that boto3 put_bucket_lifecycle_configuration takes.
Facts (docs/research/2026-10-12-storage-facts.md §3): the transition waterfall (Deep Archive is
one-way); the two-step minimum (a later transition must come at least the previous class's minimum
storage duration after the earlier one: Glacier IR on day 4 means Deep Archive no earlier than day 94);
objects under 128 KB are not transitioned by default (since Sep 2024) unless the rule has an
object-size filter; expiration beats transition, and among transitions the furthest down the waterfall
wins; ExpiredObjectDeleteMarker and AbortIncompleteMultipartUpload cannot be used with a tag filter;
NewerNoncurrentVersions is 1 to 100, needs NoncurrentDays and a Filter element.
NOT enforced: the old "30 days in Standard before Standard-IA" rule: the research could not confirm it.
Lifecycle runs asynchronously in AWS: these functions give the state "once the rule has run".
"""
from __future__ import annotations

from . import s3cost

WATERFALL = ("STANDARD", "STANDARD_IA", "INTELLIGENT_TIERING", "ONEZONE_IA", "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE")
_ALLOWED_NEXT = {
    "STANDARD": WATERFALL[1:],
    "STANDARD_IA": ("INTELLIGENT_TIERING", "ONEZONE_IA", "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE"),
    "INTELLIGENT_TIERING": ("ONEZONE_IA", "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE"),
    "ONEZONE_IA": ("GLACIER", "DEEP_ARCHIVE"),
    "GLACIER_IR": ("GLACIER", "DEEP_ARCHIVE"),
    "GLACIER": ("DEEP_ARCHIVE",),
    "DEEP_ARCHIVE": (),
}
_MIN_DAYS = {**s3cost.MIN_DAYS, "INTELLIGENT_TIERING": 0}
DEFAULT_MIN_TRANSITION_BYTES = 128 * 1024
MAX_RULES = 1000
_ACTIONS = ("Transitions", "Expiration", "NoncurrentVersionTransitions", "NoncurrentVersionExpiration",
            "AbortIncompleteMultipartUpload")
_FILTER_KEYS = ("Prefix", "Tag", "ObjectSizeGreaterThan", "ObjectSizeLessThan", "And")


def _rid(rule: dict, index: int) -> str:
    return f"rule {rule.get('ID', index)!r}"


def _filter_parts(flt: dict) -> dict:
    """Flatten a Filter into {"Prefix", "Tags": {k: v}, "gt", "lt"} (missing parts are None / empty)."""
    src = flt.get("And", flt)
    tags = {t["Key"]: t["Value"] for t in src.get("Tags", [])}
    if "Tag" in src:
        tags[src["Tag"]["Key"]] = src["Tag"]["Value"]
    return {"Prefix": src.get("Prefix"), "Tags": tags,
            "gt": src.get("ObjectSizeGreaterThan"), "lt": src.get("ObjectSizeLessThan")}


def _matches(flt: dict, key: str, size_bytes: int, tags: dict) -> bool:
    p = _filter_parts(flt)
    if p["Prefix"] and not key.startswith(p["Prefix"]):
        return False
    if any(tags.get(k) != v for k, v in p["Tags"].items()):
        return False
    if p["gt"] is not None and not size_bytes > p["gt"]:
        return False
    if p["lt"] is not None and not size_bytes < p["lt"]:
        return False
    return True


def _has_size_filter(flt: dict) -> bool:
    p = _filter_parts(flt)
    return p["gt"] is not None or p["lt"] is not None


def _check_chain(who: str, steps: list[tuple[str, int]], label: str) -> None:
    """steps = [(storage class, day)] in listed order: waterfall, increasing days, two-step minimum."""
    prev_cls, prev_day = "STANDARD", None
    for cls, day in steps:
        if cls not in WATERFALL or cls == "STANDARD":
            raise ValueError(f"{who}: {cls!r} is not a valid transition target {WATERFALL[1:]}")
        if cls not in _ALLOWED_NEXT[prev_cls]:
            raise ValueError(f"{who}: waterfall violated: {prev_cls} cannot transition to {cls}"
                             f" (allowed: {_ALLOWED_NEXT[prev_cls] or 'nothing, Deep Archive is one-way'})")
        if prev_day is not None:
            if day <= prev_day:
                raise ValueError(f"{who}: {label} must increase: {cls} at {day} follows {prev_cls} at {prev_day}")
            earliest = prev_day + _MIN_DAYS[prev_cls]
            if day < earliest:
                raise ValueError(f"{who}: two-step minimum violated: {prev_cls} has a {_MIN_DAYS[prev_cls]}-day"
                                 f" minimum, so {cls} cannot come before {label} {earliest} (got {day})")
        prev_cls, prev_day = cls, day


def validate(rules: list[dict]) -> None:
    """Raise ValueError (naming the constraint that failed) if the rules would be rejected or are unsound."""
    if len(rules) > MAX_RULES:
        raise ValueError(f"{len(rules)} rules is more than the {MAX_RULES} rules per bucket limit")
    seen: set[str] = set()
    for i, rule in enumerate(rules):
        who = _rid(rule, i)
        rid = rule.get("ID")
        if rid is not None:
            if len(rid) > 255:
                raise ValueError(f"{who}: ID is longer than 255 characters")
            if rid in seen:
                raise ValueError(f"{who}: duplicate rule ID")
            seen.add(rid)
        if rule.get("Status") not in ("Enabled", "Disabled"):
            raise ValueError(f"{who}: Status must be 'Enabled' or 'Disabled', got {rule.get('Status')!r}")
        if not any(rule.get(a) for a in _ACTIONS):
            raise ValueError(f"{who}: rule has no action (Transitions, Expiration, Noncurrent..., Abort...)")
        flt = rule.get("Filter", {})
        top = [k for k in _FILTER_KEYS if k in flt]
        if len(top) > 1:
            raise ValueError(f"{who}: Filter has {top} side by side: combine them inside 'And'")
        uses_tags = bool(_filter_parts(flt)["Tags"])

        trans = rule.get("Transitions", [])
        _check_chain(who, [(t["StorageClass"], t["Days"]) for t in trans], "day")
        exp = rule.get("Expiration")
        if exp is not None:
            if ("Days" in exp) == ("ExpiredObjectDeleteMarker" in exp):
                raise ValueError(f"{who}: Expiration needs exactly one of Days or ExpiredObjectDeleteMarker")
            if "Days" in exp and any(exp["Days"] <= t["Days"] for t in trans):
                raise ValueError(f"{who}: Expiration Days {exp['Days']} must be later than every transition")
            if "ExpiredObjectDeleteMarker" in exp and uses_tags:
                raise ValueError(f"{who}: ExpiredObjectDeleteMarker cannot be used with a tag filter")
        if rule.get("AbortIncompleteMultipartUpload") and uses_tags:
            raise ValueError(f"{who}: AbortIncompleteMultipartUpload cannot be used with a tag filter")

        ntrans = rule.get("NoncurrentVersionTransitions", [])
        _check_chain(who, [(t["StorageClass"], t["NoncurrentDays"]) for t in ntrans], "NoncurrentDays")
        nexp = rule.get("NoncurrentVersionExpiration")
        if nexp is not None:
            if "NewerNoncurrentVersions" in nexp:
                if "NoncurrentDays" not in nexp:
                    raise ValueError(f"{who}: NewerNoncurrentVersions needs NoncurrentDays")
                if not 1 <= nexp["NewerNoncurrentVersions"] <= 100:
                    raise ValueError(f"{who}: NewerNoncurrentVersions must be 1 to 100")
                if "Filter" not in rule:
                    raise ValueError(f"{who}: NewerNoncurrentVersions needs a Filter element (use {{}} for all)")
            if "NoncurrentDays" in nexp and any(nexp["NoncurrentDays"] <= t["NoncurrentDays"] for t in ntrans):
                raise ValueError(f"{who}: NoncurrentVersionExpiration must be later than every noncurrent transition")


def _applicable(rules, key, size_bytes, tags):
    for rule in rules:
        if rule.get("Status") == "Enabled" and _matches(rule.get("Filter", {}), key, size_bytes, tags):
            yield rule, (size_bytes >= DEFAULT_MIN_TRANSITION_BYTES or _has_size_filter(rule.get("Filter", {})))


def _furthest(classes: list[str]) -> str:
    return max(classes, key=WATERFALL.index, default="STANDARD")


def current_class(rules: list[dict], key: str, age_days: int, size_bytes: int, tags: dict | None = None) -> str:
    """Storage class of a current object `age_days` old once the rules have run, or "EXPIRED".

    Objects under 128 KB skip transitions unless the rule has an object-size filter.
    """
    tags = tags or {}
    reached = []
    for rule, may_transition in _applicable(rules, key, size_bytes, tags):
        exp = rule.get("Expiration", {})
        if "Days" in exp and age_days >= exp["Days"]:
            return "EXPIRED"
        if may_transition:
            reached += [t["StorageClass"] for t in rule.get("Transitions", []) if age_days >= t["Days"]]
    return _furthest(reached)


def noncurrent_fate(rules: list[dict], key: str, days_noncurrent: int, newer_noncurrent: int = 0,
                    size_bytes: int = 1 << 20, tags: dict | None = None) -> str:
    """Class of a noncurrent version, or "DELETED", `days_noncurrent` days after it became noncurrent."""
    tags = tags or {}
    reached = []
    for rule, may_transition in _applicable(rules, key, size_bytes, tags):
        nexp = rule.get("NoncurrentVersionExpiration")
        if nexp and days_noncurrent >= nexp.get("NoncurrentDays", 0) and (
                "NewerNoncurrentVersions" not in nexp or newer_noncurrent >= nexp["NewerNoncurrentVersions"]):
            return "DELETED"
        if may_transition:
            reached += [t["StorageClass"] for t in rule.get("NoncurrentVersionTransitions", [])
                        if days_noncurrent >= t["NoncurrentDays"]]
    return _furthest(reached)

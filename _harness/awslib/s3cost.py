"""s3cost — what an S3 storage class costs, and how a big upload is split.

This is the reference solution for week 04's drills 01 (storage-class cost) and 04 (multipart and
request rates): finish those drills before you read it.
Rules (docs/research/2026-10-12-storage-facts.md §1, §2, §12): the IA and Glacier Instant Retrieval
classes bill at least 128 KB per object; Standard-IA and One Zone-IA bill at least 30 days, Glacier
Instant and Flexible Retrieval 90, Deep Archive 180 (delete early and you still pay the rest);
everything except Standard charges per GB retrieved; a single PUT is at most 5 GB; a multipart part is
5 MiB to 5 GiB, at most 10,000 parts, object at most 50 TB; 3,500 write and 5,500 read requests per
second per prefix. Prices are the course's illustrative figures (prices.toml).
Left out on purpose: Intelligent-Tiering (its monitoring fee and tiers are week 11), request charges,
Expedited retrieval (it also bills per request) and the 40 KB per-object overhead of the two archive
classes (32 KB at the archive rate plus 8 KB at the Standard rate).
"""
from __future__ import annotations

import math

from . import prices

PRICES = prices.section("storage")
CLASSES = ("STANDARD", "STANDARD_IA", "ONEZONE_IA", "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE")  # GLACIER = Glacier Flexible Retrieval
MIN_DAYS = {"STANDARD": 0, "STANDARD_IA": 30, "ONEZONE_IA": 30, "GLACIER_IR": 90, "GLACIER": 90, "DEEP_ARCHIVE": 180}
MIN_OBJECT_KB = {"STANDARD": 0, "STANDARD_IA": 128, "ONEZONE_IA": 128, "GLACIER_IR": 128, "GLACIER": 0, "DEEP_ARCHIVE": 0}
MILLISECOND_ACCESS = {"STANDARD": True, "STANDARD_IA": True, "ONEZONE_IA": True, "GLACIER_IR": True,
                      "GLACIER": False, "DEEP_ARCHIVE": False}
SINGLE_AZ = {"ONEZONE_IA"}

_STORAGE_KEY = {"STANDARD": "s3_standard_per_gb_month", "STANDARD_IA": "s3_standard_ia_per_gb_month",
                "ONEZONE_IA": "s3_onezone_ia_per_gb_month", "GLACIER_IR": "s3_glacier_ir_per_gb_month",
                "GLACIER": "s3_glacier_flexible_per_gb_month", "DEEP_ARCHIVE": "s3_deep_archive_per_gb_month"}
_RETRIEVAL_KEY = {"STANDARD_IA": "s3_standard_ia_retrieval_per_gb", "ONEZONE_IA": "s3_onezone_ia_retrieval_per_gb",
                  "GLACIER_IR": "s3_glacier_ir_retrieval_per_gb"}
_ARCHIVE_RETRIEVAL_KEY = {("GLACIER", "standard"): "s3_glacier_flexible_standard_retrieval_per_gb",
                          ("GLACIER", "bulk"): "s3_glacier_flexible_bulk_retrieval_per_gb",
                          ("DEEP_ARCHIVE", "standard"): "s3_deep_archive_standard_retrieval_per_gb",
                          ("DEEP_ARCHIVE", "bulk"): "s3_deep_archive_bulk_retrieval_per_gb"}

KB_PER_GB = 1_048_576
MIB = 1024 ** 2
GIB = 1024 ** 3
SINGLE_PUT_MAX = 5 * GIB                # one PUT: up to 5 GB
MULTIPART_ADVICE = 100 * MIB            # "when your object size reaches 100 MB, consider multipart"
MAX_OBJECT_BYTES = 50 * 10 ** 12         # 50 TB (decimal; 10,000 parts of 5 GiB hold 48.8 TiB) since 2025-12-02, was 5 TB
MIN_PART_MIB = 5
MAX_PART_MIB = 5 * 1024                 # 5 GiB
MAX_PARTS = 10_000
GET_PER_PREFIX = 5_500
WRITE_PER_PREFIX = 3_500


def _retrieval_rate(storage_class: str, retrieval: str, price: dict) -> float:
    if retrieval not in ("standard", "bulk"):
        raise ValueError(f"unknown retrieval option {retrieval!r}: choose 'standard' or 'bulk' "
                         "(Expedited is not modelled: it also bills per request)")
    if storage_class == "STANDARD":
        return 0.0
    if storage_class in _RETRIEVAL_KEY:
        return price[_RETRIEVAL_KEY[storage_class]]
    return price[_ARCHIVE_RETRIEVAL_KEY[(storage_class, retrieval)]]


def storage_cost(storage_class: str, objects: int, object_kb: float, days: float, retrieved_gb: float = 0.0, *,
                 retrieval: str = "standard", price: dict = PRICES) -> float:
    """USD to keep `objects` objects of `object_kb` KB for `days` days, then retrieve `retrieved_gb` GB.

    Billable size is at least MIN_OBJECT_KB per object, billable days at least MIN_DAYS (1 GB = 1,048,576 KB,
    a month = 30 days). `retrieval` ("standard"/"bulk") only matters for GLACIER and DEEP_ARCHIVE.

    >>> storage_cost("STANDARD", 1024, 1_048_576, 30)      # 1 TB for a month
    23.55
    """
    if storage_class not in CLASSES:
        raise ValueError(f"unknown storage class {storage_class!r}: choose from {CLASSES}")
    if objects < 0 or object_kb < 0 or days < 0 or retrieved_gb < 0:
        raise ValueError("objects, object_kb, days and retrieved_gb must not be negative")
    rate = _retrieval_rate(storage_class, retrieval, price)
    billable_gb = objects * max(object_kb, MIN_OBJECT_KB[storage_class]) / KB_PER_GB
    billable_days = max(days, MIN_DAYS[storage_class])
    storage = billable_gb * price[_STORAGE_KEY[storage_class]] * billable_days / 30
    return round(storage + retrieved_gb * rate, 2)


def cheapest_class(objects: int, object_kb: float, days: float, retrieved_gb: float = 0.0, *,
                   millisecond_access: bool = True, single_az_ok: bool = False,
                   price: dict = PRICES) -> tuple[str, float]:
    """The cheapest allowed class and its cost. A tie keeps the earlier class in CLASSES.

    millisecond_access=True excludes GLACIER and DEEP_ARCHIVE; ONEZONE_IA needs single_az_ok=True.
    Intelligent-Tiering is not modelled (week 11).
    """
    best: tuple[str, float] | None = None
    for cls in CLASSES:
        if millisecond_access and not MILLISECOND_ACCESS[cls]:
            continue
        if cls in SINGLE_AZ and not single_az_ok:
            continue
        cost = storage_cost(cls, objects, object_kb, days, retrieved_gb, price=price)
        if best is None or cost < best[1]:
            best = (cls, cost)
    assert best is not None  # STANDARD is always allowed
    return best


def plan_parts(object_bytes: int, part_mib: int | None = None) -> dict:
    """Split an upload into parts: {"part_bytes", "parts", "last_part_bytes", "multipart"}.

    part_mib None picks the smallest whole-MiB part size that is at least 5 MiB and keeps parts <= 10,000.
    `multipart` is True above the 100 MB advice threshold (and always above the 5 GB single-PUT limit).

    >>> plan_parts(10 * 1024**2)["parts"]
    2
    """
    if object_bytes <= 0:
        raise ValueError("object_bytes must be positive")
    if object_bytes > MAX_OBJECT_BYTES:
        raise ValueError(f"{object_bytes} bytes is more than the 50 TB S3 maximum object size")
    if part_mib is None:
        part_mib = max(MIN_PART_MIB, math.ceil(object_bytes / (MAX_PARTS * MIB)))
    if not MIN_PART_MIB <= part_mib <= MAX_PART_MIB:
        raise ValueError(f"part size {part_mib} MiB is outside {MIN_PART_MIB} MiB to 5 GiB")
    part_bytes = part_mib * MIB
    parts = math.ceil(object_bytes / part_bytes)
    if parts > MAX_PARTS:
        raise ValueError(f"{parts} parts is more than the {MAX_PARTS} limit: use a bigger part size")
    return {"part_bytes": part_bytes, "parts": parts,
            "last_part_bytes": object_bytes - (parts - 1) * part_bytes,
            "multipart": object_bytes > SINGLE_PUT_MAX or object_bytes > MULTIPART_ADVICE}


def prefixes_needed(gets_per_second: float, puts_per_second: float) -> int:
    """Fewest prefixes that carry the load: 5,500 GET/HEAD and 3,500 PUT/COPY/POST/DELETE per second each.

    >>> prefixes_needed(11_000, 3_500)
    2
    """
    if gets_per_second < 0 or puts_per_second < 0:
        raise ValueError("request rates must not be negative")
    return max(math.ceil(gets_per_second / GET_PER_PREFIX), math.ceil(puts_per_second / WRITE_PER_PREFIX), 1)

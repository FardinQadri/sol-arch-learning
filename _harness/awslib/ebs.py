"""ebs — EBS volume limits, cost and choice.

This is the reference solution for week 04's drill 03 (EBS volume types): finish that drill before you
read it. Facts (docs/research/2026-10-12-storage-facts.md §7, §12): gp3 is 1 GiB to 64 TiB with 3,000
IOPS and 125 MiB/s free at any size, up to 80,000 IOPS (500 per GiB) and 2,000 MiB/s (0.25 MiB/s per
IOPS) since Sep 2025; gp2 is 3 IOPS per GiB, 100 to 16,000; io2 Block Express is 4 GiB to 64 TiB, up to
256,000 IOPS (1,000 per GiB) and 4,000 MiB/s; st1/sc1 are 125 GiB to 16 TiB HDDs (500 / 250 IOPS and
MiB/s), never bootable; only io1/io2 support Multi-Attach. Prices are illustrative (prices.toml).
Left out: io1, the io2 IOPS price above 64,000 (the research does not give the third tier), snapshots.
"""
from __future__ import annotations

from . import prices

PRICES = prices.section("storage")

GIB_PER_TIB = 1024
GP3_BASELINE_IOPS, GP3_BASELINE_THROUGHPUT = 3000, 125
GP3_MAX_IOPS, GP3_MAX_THROUGHPUT = 80_000, 2000
GP3_IOPS_PER_GIB = 500
GP3_THROUGHPUT_PER_IOPS = 0.25
GP2_IOPS_PER_GIB, GP2_MIN_IOPS, GP2_MAX_IOPS = 3, 100, 16_000
IO2_MAX_IOPS, IO2_IOPS_PER_GIB, IO2_MAX_THROUGHPUT = 256_000, 1000, 4000
IO2_PRICED_IOPS = 64_000                 # the research prices io2 IOPS only up to here
HDD_MAX = {"st1": {"iops": 500, "throughput": 500}, "sc1": {"iops": 250, "throughput": 250}}
SIZE_GIB = {"gp3": (1, 64 * GIB_PER_TIB), "gp2": (1, 16 * GIB_PER_TIB), "io2": (4, 64 * GIB_PER_TIB),
            "st1": (125, 16 * GIB_PER_TIB), "sc1": (125, 16 * GIB_PER_TIB)}
VOLUME_TYPES = tuple(SIZE_GIB)
BOOTABLE = {"gp2", "gp3", "io1", "io2"}
MULTI_ATTACH = {"io1", "io2"}


def _check_size(volume_type: str, size_gib: int) -> None:
    if volume_type not in SIZE_GIB:
        raise ValueError(f"unknown volume type {volume_type!r}: choose from {VOLUME_TYPES}")
    low, high = SIZE_GIB[volume_type]
    if not low <= size_gib <= high:
        raise ValueError(f"{volume_type} volumes are {low} GiB to {high} GiB, got {size_gib}")


def gp2_iops(size_gib: int) -> int:
    """gp2 baseline IOPS: 3 per GiB, at least 100, at most 16,000 (reached at 5,334 GiB).

    >>> gp2_iops(10), gp2_iops(1000), gp2_iops(6000)
    (100, 3000, 16000)
    """
    _check_size("gp2", size_gib)
    return max(GP2_MIN_IOPS, min(GP2_MAX_IOPS, GP2_IOPS_PER_GIB * size_gib))


def gp3_config(size_gib: int, iops: int | None = None, throughput: int | None = None) -> dict:
    """Validate a gp3 request; None means the free baseline. Returns {"iops", "throughput"}.

    Above the baseline: IOPS at most 500 per GiB and 80,000; throughput at most 0.25 MiB/s per
    provisioned IOPS and 2,000 MiB/s. Below the baseline is not possible.

    >>> gp3_config(100)
    {'iops': 3000, 'throughput': 125}
    """
    _check_size("gp3", size_gib)
    iops = GP3_BASELINE_IOPS if iops is None else iops
    throughput = GP3_BASELINE_THROUGHPUT if throughput is None else throughput
    if iops < GP3_BASELINE_IOPS or throughput < GP3_BASELINE_THROUGHPUT:
        raise ValueError(f"gp3 includes {GP3_BASELINE_IOPS} IOPS and {GP3_BASELINE_THROUGHPUT} MiB/s: you cannot provision less")
    if iops > GP3_MAX_IOPS:
        raise ValueError(f"gp3 tops out at {GP3_MAX_IOPS} IOPS, got {iops}")
    if iops > GP3_BASELINE_IOPS and iops > GP3_IOPS_PER_GIB * size_gib:
        raise ValueError(f"gp3 allows {GP3_IOPS_PER_GIB} IOPS per GiB: {size_gib} GiB gives at most {GP3_IOPS_PER_GIB * size_gib}")
    if throughput > GP3_MAX_THROUGHPUT:
        raise ValueError(f"gp3 tops out at {GP3_MAX_THROUGHPUT} MiB/s, got {throughput}")
    if throughput > GP3_BASELINE_THROUGHPUT and throughput > GP3_THROUGHPUT_PER_IOPS * iops:
        raise ValueError(f"gp3 allows {GP3_THROUGHPUT_PER_IOPS} MiB/s per IOPS: {iops} IOPS gives at most {GP3_THROUGHPUT_PER_IOPS * iops:g}")
    return {"iops": iops, "throughput": throughput}


def _io2_iops_cost(iops: int, price: dict) -> float:
    if iops > IO2_PRICED_IOPS:
        raise ValueError(f"io2 IOPS above {IO2_PRICED_IOPS} have no price in the course's research")
    first = min(iops, 32_000)
    return first * price["ebs_io2_per_iops_month_first_32k"] + (iops - first) * price["ebs_io2_per_iops_month_32k_to_64k"]


def monthly_cost(volume_type: str, size_gib: int, iops: int | None = None, throughput: int | None = None,
                 price: dict = PRICES) -> float:
    """Monthly USD for one volume (no snapshots). gp3 pays only for IOPS above 3,000 and MiB/s above 125;
    io2 needs `iops`; gp2, st1 and sc1 are size only.

    >>> monthly_cost("gp3", 100)
    8.0
    """
    _check_size(volume_type, size_gib)
    if volume_type == "gp3":
        cfg = gp3_config(size_gib, iops, throughput)
        cost = (size_gib * price["ebs_gp3_per_gb_month"]
                + (cfg["iops"] - GP3_BASELINE_IOPS) * price["ebs_gp3_per_iops_month"]
                + (cfg["throughput"] - GP3_BASELINE_THROUGHPUT) * price["ebs_gp3_per_mibps_month"])
    elif volume_type == "io2":
        if iops is None or iops <= 0:
            raise ValueError("io2 is billed per provisioned IOPS: pass iops")
        if iops > IO2_MAX_IOPS or iops > IO2_IOPS_PER_GIB * size_gib:
            raise ValueError(f"io2 allows {IO2_IOPS_PER_GIB} IOPS per GiB and {IO2_MAX_IOPS} in total: {size_gib} GiB, {iops} IOPS")
        if throughput is not None and throughput > IO2_MAX_THROUGHPUT:
            raise ValueError(f"io2 tops out at {IO2_MAX_THROUGHPUT} MiB/s")
        cost = size_gib * price["ebs_io2_per_gb_month"] + _io2_iops_cost(iops, price)
    else:
        if iops is not None or throughput is not None:
            raise ValueError(f"{volume_type} performance is not provisioned: leave iops and throughput out")
        cost = size_gib * price[f"ebs_{volume_type}_per_gb_month"]
    return round(cost, 2)


def choose_volume(iops: int = 0, throughput_mibs: int = 0, *, boot: bool = False, multi_attach: bool = False,
                  sequential: bool = False, rarely_accessed: bool = False) -> str:
    """Cheapest volume type that meets the need.

    Rules, in order: Multi-Attach needs io2 (and cannot be a boot volume); IOPS above gp3's 80,000 or
    throughput above 2,000 MiB/s needs io2; a sequential, non-boot workload gets sc1 if it is rarely
    accessed and fits sc1 (250 IOPS, 250 MiB/s), else st1 if it fits st1 (500, 500); everything else gp3.
    HDDs are never chosen for a boot volume. ValueError if even io2 cannot do it.
    """
    if iops < 0 or throughput_mibs < 0:
        raise ValueError("iops and throughput_mibs must not be negative")
    if multi_attach and boot:
        raise ValueError("a Multi-Attach volume cannot be a boot volume")
    if iops > IO2_MAX_IOPS or throughput_mibs > IO2_MAX_THROUGHPUT:
        raise ValueError(f"no EBS volume gives more than {IO2_MAX_IOPS} IOPS or {IO2_MAX_THROUGHPUT} MiB/s")
    if multi_attach or iops > GP3_MAX_IOPS or throughput_mibs > GP3_MAX_THROUGHPUT:
        return "io2"
    if sequential and not boot:
        for kind, wanted in (("sc1", rarely_accessed), ("st1", True)):
            if wanted and iops <= HDD_MAX[kind]["iops"] and throughput_mibs <= HDD_MAX[kind]["throughput"]:
                return kind
    return "gp3"

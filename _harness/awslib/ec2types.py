"""ec2types — read EC2 instance-type names and pick a size.

This is the reference solution for week 03's drill 01: finish that drill before you read it.
Rules (docs/research/2026-10-11-compute-facts.md §1): a name is <series><generation><options>.<size>,
e.g. c7gn.xlarge = series c, generation 7, options g (Graviton) and n (network optimized), size xlarge.
Memory per vCPU: C = 2 GiB, M = 4 GiB, R = 8 GiB (c7g.large, m7g.large, r7g.large).
"""
from __future__ import annotations

import re

SERIES = {  # longest prefixes first when parsing
    "mac": "general purpose", "inf": "accelerated computing", "trn": "accelerated computing",
    "hpc": "high performance computing", "dl": "accelerated computing", "vt": "accelerated computing",
    "m": "general purpose", "t": "general purpose", "a": "general purpose",
    "c": "compute optimized",
    "r": "memory optimized", "x": "memory optimized", "z": "memory optimized", "u": "memory optimized",
    "i": "storage optimized", "d": "storage optimized", "h": "storage optimized",
    "p": "accelerated computing", "g": "accelerated computing", "f": "accelerated computing",
}
OPTIONS = {"a": "AMD processor", "g": "AWS Graviton processor", "i": "Intel processor",
           "d": "instance store volumes", "n": "network and EBS optimized",
           "e": "extra storage or memory", "z": "high CPU frequency", "b": "block storage optimized",
           "q": "Qualcomm inference accelerators", "flex": "flex instance"}
PROCESSORS = {"g": "AWS Graviton", "a": "AMD", "i": "Intel"}
_SIZE = re.compile(r"nano|micro|small|medium|large|xlarge|[1-9][0-9]*xlarge|metal(-[0-9]+xl)?")


def decode(instance_type: str) -> dict:
    """Split an instance type name into its parts. Raises ValueError naming what is wrong."""
    name = instance_type.strip().lower()
    if "." not in name:
        raise ValueError(f"{instance_type!r} has no '.' between the family and the size")
    family, size = name.split(".", 1)
    if not _SIZE.fullmatch(size):
        raise ValueError(f"{instance_type!r}: unknown size {size!r}")
    flex = family.endswith("-flex")
    if flex:
        family = family[: -len("-flex")]
    series = next((key for key in sorted(SERIES, key=len, reverse=True) if family.startswith(key)), None)
    if series is None:
        raise ValueError(f"{instance_type!r}: unknown series in {family!r}")
    rest = family[len(series):]
    digits = re.match(r"[0-9]+", rest)
    if not digits or int(digits.group()) < 1:
        raise ValueError(f"{instance_type!r}: no generation number after the series {series!r}")
    options = list(rest[digits.end():])
    for letter in options:
        if letter not in OPTIONS:
            raise ValueError(f"{instance_type!r}: unknown option letter {letter!r}")
    if flex:
        options.append("flex")
    processor = next((PROCESSORS[o] for o in options if o in PROCESSORS), "not stated")
    return {"series": series, "category": SERIES[series], "generation": int(digits.group()),
            "options": options, "processor": processor, "size": size, "burstable": series == "t",
            "instance_store": "d" in options, "bare_metal": size.startswith("metal"), "flex": flex}


def choose_type(vcpus: int, memory_gib: float, processor: str = "graviton", generation: int = 7) -> str:
    """Pick C, M or R by memory per vCPU (<= 2, <= 4, <= 8 GiB) and the size by vCPU count."""
    if vcpus <= 0 or memory_gib <= 0:
        raise ValueError("vcpus and memory_gib must be positive")
    letters = {"graviton": "g", "intel": "i", "amd": "a"}
    if processor not in letters:
        raise ValueError(f"unknown processor {processor!r}: use graviton, intel or amd")
    ratio = memory_gib / vcpus
    if ratio <= 2:
        series = "c"
    elif ratio <= 4:
        series = "m"
    elif ratio <= 8:
        series = "r"
    else:
        raise ValueError("more than 8 GiB per vCPU: look at the X or U families")
    if vcpus == 1:
        size = "medium"
    elif vcpus == 2:
        size = "large"
    elif vcpus == 4:
        size = "xlarge"
    elif vcpus % 4 == 0:
        size = f"{vcpus // 4}xlarge"
    else:
        raise ValueError(f"no standard size has {vcpus} vCPUs")
    return f"{series}{generation}{letters[processor]}.{size}"

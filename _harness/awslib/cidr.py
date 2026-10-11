"""cidr — IPv4 subnet maths for AWS VPCs.

This is the reference solution for week 02's drills 01–02: finish those drills before you read it.
Rules (docs/facts.md): a VPC or subnet IPv4 block is /16 to /28; AWS reserves 5 addresses in every
subnet — the network address, .1 (VPC router), .2 (Amazon DNS), .3 (future use) and the last address.
"""
from __future__ import annotations

import ipaddress

RESERVED_PER_SUBNET = 5
MIN_PREFIX, MAX_PREFIX = 16, 28


def _network(cidr: str) -> ipaddress.IPv4Network:
    try:
        net = ipaddress.ip_network(cidr, strict=True)
    except ValueError as exc:
        raise ValueError(f"not a network block: {cidr!r} ({exc})") from None
    if net.version != 4 or not MIN_PREFIX <= net.prefixlen <= MAX_PREFIX:
        raise ValueError(f"{cidr} is outside the /{MIN_PREFIX}–/{MAX_PREFIX} range AWS allows")
    return net


def usable_ips(cidr: str) -> int:
    return _network(cidr).num_addresses - RESERVED_PER_SUBNET


def reserved_ips(cidr: str) -> list[str]:
    net = _network(cidr)
    first = int(net.network_address)
    return [str(ipaddress.ip_address(first + i)) for i in range(4)] + [str(net.broadcast_address)]


def prefix_for_hosts(hosts: int) -> int:
    """The smallest subnet (largest prefix length) with at least `hosts` usable addresses."""
    if hosts < 1:
        raise ValueError("hosts must be at least 1")
    for prefix in range(MAX_PREFIX, MIN_PREFIX - 1, -1):
        if 2 ** (32 - prefix) - RESERVED_PER_SUBNET >= hosts:
            return prefix
    raise ValueError(f"{hosts} hosts do not fit in one subnet (a /{MIN_PREFIX} holds {2 ** 16 - 5})")


def plan_subnets(vpc_cidr: str, tiers: dict[str, int], azs: list[str]) -> dict[tuple[str, str], str]:
    """One subnet per (tier, AZ). `tiers` maps tier name → hosts needed in each subnet.
    Biggest subnets first (ties keep the order of `tiers`), each aligned to its own size and packed
    from the start of the VPC block. Raises ValueError when they do not fit."""
    vpc = _network(vpc_cidr)
    order = sorted(tiers, key=lambda tier: (prefix_for_hosts(tiers[tier]), list(tiers).index(tier)))
    plan, cursor, end = {}, int(vpc.network_address), int(vpc.broadcast_address)
    for tier in order:
        prefix = prefix_for_hosts(tiers[tier])
        size = 2 ** (32 - prefix)
        for az in azs:
            cursor = -(-cursor // size) * size  # align up to a multiple of the block size
            if cursor + size - 1 > end:
                raise ValueError(f"the subnets do not fit in {vpc_cidr}")
            plan[(tier, az)] = str(ipaddress.ip_network((cursor, prefix)))
            cursor += size
    return plan


def overlaps(a: str, b: str) -> bool:
    return ipaddress.ip_network(a).overlaps(ipaddress.ip_network(b))

"""netsim — small, readable models of VPC routing, security groups, network ACLs and VPC links.

This is the reference solution for week 02's drills 03–05: finish those drills before you read it.

Rules modelled (docs/facts.md):
  • A route table sends a packet to the target of the most specific route that contains the
    destination (longest prefix match). The local route covers the VPC's own CIDR.
  • Security groups are stateful and only allow: a reply to an allowed request is always let back.
    A rule's "peer" is a CIDR block or another security group's id.
  • Network ACLs are stateless, allow AND deny, and are checked in rule-number order — the first
    matching rule decides; if none matches, the final "*" rule denies. Replies must be allowed
    explicitly, on the client's ephemeral port. Traffic between two hosts in the same subnet does
    not cross a network ACL.
  • VPC peering is not transitive. A transit gateway is a hub: attached VPCs reach each other.
"""
from __future__ import annotations

import ipaddress
from dataclasses import dataclass

ANY_OUT = {"protocol": "-1", "ports": (0, 65535), "peer": "0.0.0.0/0"}
NACL_ALLOW_ALL = {"rule": 100, "action": "allow", "protocol": "-1", "ports": (0, 65535), "cidr": "0.0.0.0/0"}


def route_target(destination_ip: str, routes: dict[str, str]) -> str | None:
    """`routes` maps destination CIDR → target id. Returns the target of the longest matching
    prefix, or None when no route matches (the packet is dropped)."""
    ip = ipaddress.ip_address(destination_ip)
    best, best_len = None, -1
    for cidr, target in routes.items():
        net = ipaddress.ip_network(cidr)
        if ip in net and net.prefixlen > best_len:
            best, best_len = target, net.prefixlen
    return best


def _protocol_matches(rule_protocol: str, protocol: str) -> bool:
    return rule_protocol == "-1" or rule_protocol == protocol


def _port_matches(ports, protocol: str, port: int) -> bool:
    low, high = ports
    return protocol == "icmp" or low <= port <= high


def sg_allows(rules, peer_ip: str, peer_sgs, protocol: str, port: int) -> bool:
    """True if any rule allows traffic with this peer (its IP, or one of its security groups)."""
    ip = ipaddress.ip_address(peer_ip)
    for rule in rules:
        if not (_protocol_matches(rule["protocol"], protocol) and _port_matches(rule["ports"], protocol, port)):
            continue
        peer = rule["peer"]
        if peer.startswith("sg-"):
            if peer in peer_sgs:
                return True
        elif ip in ipaddress.ip_network(peer):
            return True
    return False


def nacl_allows(rules, peer_ip: str, protocol: str, port: int) -> bool:
    """Lowest rule number first; the first rule that matches decides; nothing matches → deny."""
    ip = ipaddress.ip_address(peer_ip)
    for rule in sorted(rules, key=lambda r: r["rule"]):
        if (_protocol_matches(rule["protocol"], protocol) and _port_matches(rule["ports"], protocol, port)
                and ip in ipaddress.ip_network(rule["cidr"])):
            return rule["action"] == "allow"
    return False


@dataclass(frozen=True)
class Host:
    """One network interface: its IP, subnet, security groups (ids + rules) and its subnet's NACL."""
    ip: str
    subnet: str
    sgs: tuple = ()
    sg_in: tuple = ()
    sg_out: tuple = (ANY_OUT,)
    nacl_in: tuple = (NACL_ALLOW_ALL,)
    nacl_out: tuple = (NACL_ALLOW_ALL,)


def tcp_connection(client: Host, server: Host, port: int, client_port: int = 49152) -> tuple[bool, str]:
    """Can `client` open a TCP connection to `server` on `port` and get replies back?
    Returns (True, "allowed") or (False, <the first check that blocks it>)."""
    crosses = client.subnet != server.subnet
    checks = [("client security group (outbound)",
               sg_allows(client.sg_out, server.ip, server.sgs, "tcp", port))]
    if crosses:
        checks += [("client network ACL (outbound)", nacl_allows(client.nacl_out, server.ip, "tcp", port)),
                   ("server network ACL (inbound)", nacl_allows(server.nacl_in, client.ip, "tcp", port))]
    checks.append(("server security group (inbound)", sg_allows(server.sg_in, client.ip, client.sgs, "tcp", port)))
    if crosses:  # replies: security groups are stateful, network ACLs are not
        checks += [("server network ACL (outbound, reply)", nacl_allows(server.nacl_out, client.ip, "tcp", client_port)),
                   ("client network ACL (inbound, reply)", nacl_allows(client.nacl_in, server.ip, "tcp", client_port))]
    for name, ok in checks:
        if not ok:
            return False, name
    return True, "allowed"


def can_peer(cidr_a: str, cidr_b: str) -> bool:
    """Two VPCs can be peered only if their CIDR blocks do not overlap."""
    return not ipaddress.ip_network(cidr_a).overlaps(ipaddress.ip_network(cidr_b))


def can_reach(source: str, target: str, peerings, tgw_attachments=()) -> bool:
    """`peerings` is a collection of (vpc, vpc) pairs; `tgw_attachments` the VPCs attached to one
    transit gateway (with routes to each other). Peering is not transitive."""
    if source == target:
        return True
    if {source, target} in [set(pair) for pair in peerings]:
        return True
    attached = set(tgw_attachments)
    return source in attached and target in attached


def peerings_for_full_mesh(vpcs: int) -> int:
    """Peering connections needed so every one of `vpcs` VPCs can reach every other."""
    if vpcs < 0:
        raise ValueError("vpcs must not be negative")
    return vpcs * (vpcs - 1) // 2

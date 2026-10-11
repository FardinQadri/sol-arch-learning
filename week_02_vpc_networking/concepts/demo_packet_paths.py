"""Demo — five connection checks with the netsim model: who allows it, and which check blocks it.
Run it: python concepts/demo_packet_paths.py   (pure Python; no AWS, no network)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from _harness.awslib.netsim import (  # noqa: E402
    ANY_OUT, NACL_ALLOW_ALL, Host, can_reach, route_target, tcp_connection,
)
from _harness.awslib.safety import force_utf8  # noqa: E402

force_utf8()


def rule(port, peer, protocol="tcp"):
    return {"protocol": protocol, "ports": (port, port), "peer": peer}


def nacl(number, action, cidr, low, high=None):
    return {"rule": number, "action": action, "protocol": "tcp", "ports": (low, high or low), "cidr": cidr}


rows = []

# 1. An internet client reaches an app server that has no load balancer in front: the SG only
#    allows the load balancer's group, so the connection is refused at the instance.
client = Host(ip="203.0.113.25", subnet="internet")
app = Host(ip="10.0.2.15", subnet="app-subnet", sgs=("sg-app",), sg_in=(rule(8080, "sg-alb"),))
rows.append(("1. Internet client → app server :8080, SG allows only the ALB group", *tcp_connection(client, app, 8080)))

# 2. SSH from the internet to a private instance whose SG has no port 22 rule (no bastion).
laptop = Host(ip="198.51.100.7", subnet="internet")
private_box = Host(ip="10.0.3.40", subnet="private-subnet", sgs=("sg-priv",), sg_in=(rule(443, "10.0.0.0/16"),))
rows.append(("2. Laptop → private instance :22, no bastion, no rule", *tcp_connection(laptop, private_box, 22)))

# 3. The database subnet's NACL allows port 5432 in, but forgets the ephemeral ports out.
web = Host(ip="10.0.1.20", subnet="app-subnet", sgs=("sg-app",))
db_nacl_in = (nacl(100, "allow", "10.0.0.0/16", 5432),)
db_nacl_out = (nacl(100, "allow", "10.0.0.0/16", 443),)  # wrong: replies need 1024-65535
db = Host(ip="10.0.9.5", subnet="db-subnet", sgs=("sg-db",), sg_in=(rule(5432, "sg-app"),),
          nacl_in=db_nacl_in, nacl_out=db_nacl_out)
rows.append(("3. App → database :5432, NACL forgets ephemeral ports", *tcp_connection(web, db, 5432)))
db_fixed = Host(ip="10.0.9.5", subnet="db-subnet", sgs=("sg-db",), sg_in=(rule(5432, "sg-app"),),
                nacl_in=db_nacl_in, nacl_out=(nacl(100, "allow", "10.0.0.0/16", 1024, 65535),))
rows.append(("3b. Same, outbound allows 1024–65535", *tcp_connection(web, db_fixed, 5432)))

# 4. Two hosts in the same subnet; the subnet's NACL denies everything. The NACL never sees them.
deny_all = (nacl(100, "deny", "0.0.0.0/0", 0, 65535),)
a = Host(ip="10.0.4.10", subnet="locked-subnet", sgs=("sg-a",), nacl_in=deny_all, nacl_out=deny_all)
b = Host(ip="10.0.4.11", subnet="locked-subnet", sgs=("sg-b",), sg_in=(rule(6379, "sg-a"),),
         nacl_in=deny_all, nacl_out=deny_all)
rows.append(("4. Host → host, same subnet, deny-all NACL (never consulted), SG allows :6379", *tcp_connection(a, b, 6379)))

# 5. A peering chain: A–B and B–C are peered. A cannot reach C. A transit gateway fixes that.
chain = [("vpc-a", "vpc-b"), ("vpc-b", "vpc-c")]
ok_ab = can_reach("vpc-a", "vpc-b", chain)
ok_ac = can_reach("vpc-a", "vpc-c", chain)
ok_tgw = can_reach("vpc-a", "vpc-c", [], tgw_attachments=["vpc-a", "vpc-b", "vpc-c"])
rows.append(("5a. vpc-a → vpc-b, peered", ok_ab, "allowed" if ok_ab else "no peering"))
rows.append(("5b. vpc-a → vpc-c, peering chain A–B–C", ok_ac, "allowed" if ok_ac else "peering is not transitive"))
rows.append(("5c. vpc-a → vpc-c, all attached to a TGW", ok_tgw, "allowed" if ok_tgw else "no route"))

width = max(len(r[0]) for r in rows)
print(f"{'Connection':<{width}}  Allowed?  Blocked by")
print(f"{'-' * width}  --------  ----------------------------")
for story, ok, reason in rows:
    print(f"{story:<{width}}  {'✔ yes' if ok else '✘ no ':<8}  {'—' if ok else reason}")

print("\nOne routing lookup (longest prefix wins):")
routes = {"10.0.0.0/16": "local", "10.1.0.0/16": "pcx-peer", "0.0.0.0/0": "nat-gw"}
for ip in ("10.0.7.7", "10.1.4.9", "8.8.8.8"):
    print(f"  {ip:<10} → {route_target(ip, routes)}")

_ = (ANY_OUT, NACL_ALLOW_ALL)  # defaults used by Host when you pass no rules
print("\nNow do drills 04, 05 and 10.")

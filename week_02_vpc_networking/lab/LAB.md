# Week 02 lab — a VPC, a private instance and one short-lived NAT gateway

About 60–90 minutes. Cost: about 0.05 USD if the NAT gateway step stays under 30 minutes. A NAT gateway
bills about 0.045 USD per hour (illustrative) plus data, and its public IPv4 address bills 0.005 USD per hour.
Everything else here is free or pennies. This lab is optional. Everything the course grades runs offline.

## 1. Before you start

- The week 00 guard rails are done (budget alert, MFA, no root keys) and you have the `saa-lab` profile.
- Use `--profile saa-lab` on every CLI command and pick one Region for the whole lab.
- Tag **every** resource `saa-course=lab`: the VPC, the Elastic IP, the NAT gateway, the instance.
  The cleanup script only finds tagged ones. In the VPC wizard, add the tag under "Additional tags".
- Keep a clock handy. You will delete the NAT gateway within 30 minutes of creating it.

## 2. Create a VPC with the console wizard

1. VPC console → Create VPC → **VPC and more**.
2. Name tag prefix `saa-lab`. IPv4 CIDR `10.0.0.0/16`.
3. Availability Zones: **2**. Public subnets: **1 per AZ**. Private subnets: **1 per AZ**.
4. NAT gateways: **None**. VPC endpoints: **S3 Gateway** (on).
5. Add the tag `saa-course=lab`, then create.

Now read what it made:

- **Route tables.** One public table with `0.0.0.0/0 → igw-…`. Two private tables (one per AZ), each with the `local` route and a `pl-…` route to the S3 endpoint. No route to the internet.
- **Subnets.** Open one and look at its route table association and its AZ.
- **Reserved addresses.** A /20 subnet shows "available IPv4 addresses". It is 5 fewer than the total.
- The wizard's private route tables are separate per AZ on purpose. Later you would point each at its own NAT gateway.

## 3. A private instance with no internet

1. IAM → Roles → Create role → AWS service **EC2**. Attach `AmazonSSMManagedInstanceCore`. Name it `saa-lab-ssm-role`. Tag it `saa-course=lab`.
2. EC2 → Launch instance. Amazon Linux, **t4g.micro** (or **t3.micro** if you choose an x86 image). No key pair.
3. Network: your new VPC, a **private** subnet, **no public IP**. Security group: no inbound rules.
4. Advanced → IAM instance profile `saa-lab-ssm-role`. Tag the instance (and its volume) `saa-course=lab`.
5. Wait a few minutes. Open Systems Manager → Fleet Manager (or Session Manager → Start session).
   The instance does **not** appear. It has no path to the SSM service: no NAT, no interface endpoints.
   That failure is the lesson.
6. Turn on the flow log now so records collect while you work: CloudWatch → Log groups → create `/saa-lab/flow-logs`, retention 1 day, tag `saa-course=lab`; then VPC → your VPC → Flow logs → Create, filter **All**, destination that log group, let the console create a service role.

## 4. Add ONE NAT gateway (watch the clock)

1. VPC → Elastic IPs → Allocate. Tag it `saa-course=lab`.
2. VPC → NAT gateways → Create. Subnet: a **public** subnet in the same AZ as your instance. Connectivity: **Public**. Attach the Elastic IP. Tag it `saa-course=lab`.
   **Write down the time now.**
3. When it shows Available, edit the private route table that your instance's subnet uses. Add `0.0.0.0/0 → the NAT gateway`.
4. Wait a minute or two. The instance registers in Systems Manager. Start a **Session Manager** session. You now have a shell with no open inbound port and no key.
5. In the session run `curl -sI https://aws.amazon.com | head -1`. It works, because traffic goes out through the NAT gateway.
6. Go straight on to section 5. You delete the NAT gateway at its end, within 30 minutes of step 2.

## 5. Security groups vs network ACLs

In the Session Manager shell, keep `curl -sI https://aws.amazon.com | head -1` ready. Do this while the NAT gateway still exists.

1. Run the curl. It works. Note that the instance's security group has **no inbound rules** and the outbound reply still came back: security groups are stateful.
2. VPC → Network ACLs → create a custom NACL `saa-lab-nacl` for your VPC. Tag it `saa-course=lab`.
   A new custom NACL denies everything. Add inbound and outbound **allow all** at rule 100 so you start from a working state.
3. Associate it with the instance's **private subnet**.
4. Add an **outbound deny** rule: rule number 90, TCP, port 443, destination `0.0.0.0/0`. Rule 90 comes before 100, so it wins.
5. Run the curl again. It hangs and times out. A network ACL denied the outbound request.
6. Delete rule 90. The curl works again. Note what you learned about rule order.
7. Associate the subnet back with the default NACL, then delete `saa-lab-nacl`.
8. Delete the NAT gateway now (VPC → NAT gateways → Delete), then release the Elastic IP once it shows Deleted. The idle address keeps billing until released.

## 6. VPC Flow Logs

Reading only. No new curl runs: the flow log has been collecting since section 3.

1. Wait a few minutes (flow logs are not real time). Open the log group `/saa-lab/flow-logs`.
2. Find one `ACCEPT` record (from the curls in sections 4–5) and one `REJECT` record (from the rule-90 deny).
3. Read the fields: source, destination, ports, protocol, action.
4. The records stay in the log group after the NAT gateway is gone.

## 7. Clean up

First delete the flow log itself (VPC → your VPC → Flow logs → Delete).

```bash
python lab/cleanup.py --profile saa-lab          # dry run: read the list
python lab/cleanup.py --profile saa-lab --yes    # deletes tagged resources
```

The script terminates tagged instances, deletes tagged NAT gateways, releases tagged Elastic IPs and deletes
tagged VPCs together with everything inside them. It does not touch anything without the `saa-course=lab` tag.
If it cannot delete a VPC because of a resource it does not own (for example an untagged instance), it
reports an error for that resource and carries on. Delete the leftover by hand and run it again.

By hand, after `--yes`: delete the log group `/saa-lab/flow-logs`, the flow-log service role the console
created (it is not tagged, so no script deletes it) and `saa-lab-ssm-role` (or let week 01's cleanup remove it; it is tagged). Then open Billing and check the next day that no NAT gateway or
Elastic IP charge appears.

## 8. What to write down

- The private route table before and after the NAT route (section 4).
- Why the instance could not register in step 3.
- What a hanging `curl` looked like when the NACL blocked it, and which rule number did it.
- One ACCEPT and one REJECT flow-log line, and how you told the two apart.
- How long the NAT gateway existed, and the cost for that time.

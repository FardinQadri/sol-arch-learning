# Week 03 lab — a self-healing web fleet behind an Application Load Balancer

About 60–90 minutes. Cost: about 0.10 USD if you finish and clean up within 90 minutes. The ALB bills about
0.0225 USD per hour plus a little for LCUs. Two `t4g.micro` instances bill about 0.0084 USD per hour each, and each
public IPv4 address bills 0.005 USD per hour (all illustrative). A free plan or the Free Tier may cover the
`t4g.micro` hours. This lab is optional. Everything the course grades runs offline.

## 1. Before you start

- The week 00 guard rails are done (budget alert, MFA, no root keys) and you have the `saa-lab` profile.
- Use one Region for the whole lab and stay in it. Use the **default VPC** (it has one public subnet per AZ).
- Tag **every** resource `saa-course=lab`: both security groups, the launch template, the target group, the load
  balancer, the Auto Scaling group. The cleanup script only finds tagged ones.
- For the Auto Scaling group, add the tag with **Tag new instances** ticked (`PropagateAtLaunch`). Then the instances are tagged too.
- Keep a clock handy. Aim to be finished and cleaned up within 90 minutes.

## 2. Two security groups

EC2 → Security Groups → Create. Choose the default VPC. Tag both `saa-course=lab`.

1. `saa-lab-alb`: inbound **HTTP 80 from anywhere** (`0.0.0.0/0`). Leave the default outbound rule.
2. `saa-lab-web`: inbound **HTTP 80 from the security group `saa-lab-alb`** (type the group's name or id as the source). Nothing else.

The instances accept traffic only from the load balancer. Nobody can reach them directly, even though they get public IPs.

## 3. A launch template

EC2 → Launch Templates → Create launch template. Name `saa-lab-web`. Tick the box that says to provide guidance for Auto Scaling.

1. **AMI**: Amazon Linux 2023, **64-bit (Arm)**.
2. **Instance type**: `t4g.micro`. **Key pair**: none.
3. **Security group**: `saa-lab-web`. Do not set a subnet here.
4. **Resource tags**: `saa-course=lab` for **Instance** and **Volume**. Also tag the template itself.
5. **Advanced details**:
   - **Metadata version**: choose **V2 only (token required)**. When you review the template, look for "Metadata version: V2 only". This is the IMDSv2 setting.
   - **User data**: paste the script below.

```bash
#!/bin/bash
# Fetch this instance's id with an IMDSv2 token: first PUT for a token, then GET with it.
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 300")
ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" "http://169.254.169.254/latest/meta-data/instance-id")
mkdir -p /srv/www
printf '<h1>served by %s</h1>\n' "$ID" > /srv/www/index.html
echo ok > /srv/www/healthz
# Run the web server as a service so it keeps running after the boot script ends.
systemd-run --unit=saa-web --working-directory=/srv/www /usr/bin/python3 -m http.server 80
```

What it does: it asks IMDSv2 for a token (PUT), uses it to read the instance id (GET), writes an `index.html` that shows the id,
writes a `healthz` file, and starts Python's web server on port 80. It installs nothing. It runs as root on first boot only.
If the page does not work later, read `/var/log/cloud-init-output.log` on the instance.

No instance profile is needed: the script calls only the metadata service, not an AWS API.

## 4. A target group and an Application Load Balancer

1. EC2 → Target Groups → Create. Target type **Instances**. Name `saa-lab-tg`. **HTTP**, port **80**, default VPC.
   Health check path: `/healthz`. Register no targets. Tag `saa-course=lab`.
2. EC2 → Load Balancers → Create → **Application Load Balancer**. Name `saa-lab-alb`. **Internet-facing**, IPv4.
   Network mapping: the default VPC and **two or more** subnets in different AZs. Security group: `saa-lab-alb` only.
   Listener **HTTP 80** → forward to `saa-lab-tg`. Tag `saa-course=lab`.

The load balancer takes a few minutes to become Active.

## 5. An Auto Scaling group

EC2 → Auto Scaling Groups → Create.

1. Name `saa-lab-asg`. Launch template `saa-lab-web`, version **Default** (or Latest).
2. Network: the default VPC and the same default subnets (at least two AZs).
3. Load balancing: **Attach to an existing load balancer** → target group `saa-lab-tg`.
4. Health checks: tick **Turn on Elastic Load Balancing health checks**. Set the **health check grace period** to **120** seconds.
5. Group size: desired **2**, minimum **2**, maximum **4**.
6. Scaling policy: **Target tracking**, metric **Average CPU utilization**, target **50**. Set the instance warmup to 120 seconds.
7. Tags: `saa-course=lab`, with **Tag new instances** ticked.

Create it. Two instances launch.

## 6. Watch it work

1. Target group `saa-lab-tg` → Targets. Both targets start as `initial` and turn `healthy` after the grace period and the
   health check thresholds (default: 5 passes, 30 seconds apart).
2. Copy the ALB's DNS name and run it a few times:
   ```bash
   for i in 1 2 3 4 5 6; do curl -s http://<ALB-DNS-NAME>/; done
   ```
   You see two different instance ids as the ALB spreads requests. Compare them with the ids in the EC2 console.
3. Try `curl -s http://<instance-public-ip>/` to one instance directly. It times out. The instance security group allows only the ALB.
4. In the EC2 console, check one instance → Actions → Instance settings → **Modify instance metadata options**.
   It shows IMDSv2 as required. That is the template's setting.

## 7. Self-healing

1. **Terminate one instance** in the EC2 console. Watch the Auto Scaling group → Activity tab. It notices the lost
   instance and launches a replacement. The group is back at 2 in a few minutes and the new target turns healthy.
2. Now break the health check. Target group → Health checks → Edit → path `/nope`. The app answers 404, so the targets
   go `unhealthy` after two failed checks. Because the group uses **ELB health checks**, it marks them unhealthy and
   starts **replacing** them. (With EC2 health checks it would do nothing: the instances are still running.)
   Watch the Activity tab. The new instances fail too, so the cycle repeats. That is the cost of a bad health check.
3. Set the path back to `/healthz`. The next replacements turn `healthy` and the group settles.

## 8. Clean up

```bash
python lab/cleanup.py --profile saa-lab          # dry run: read the list
python lab/cleanup.py --profile saa-lab --yes    # deletes tagged resources
```

The script deletes, in this order: the Auto Scaling group (with its instances), the load balancer, the target group,
the launch template, any tagged instances left over, and finally the two security groups. It does not touch anything
without the `saa-course=lab` tag. If one deletion fails (for example a security group still in use while
instances shut down), it reports the error and carries on. Wait a minute and run it again.

Check the next day in Billing that no load balancer hours or instance charges still appear.

## 9. What to write down

- The launch template setting that requires IMDSv2, and what the console shows when it is on.
- The two instance ids your `curl` loop returned.
- What the Activity tab said when you terminated an instance, and how long the replacement took.
- What happened to the targets when the health check path was `/nope`, and why EC2 health checks would not have noticed.
- Why the instance security group allows the ALB's security group, not `0.0.0.0/0`.
- How long the lab ran and the cost for that time.

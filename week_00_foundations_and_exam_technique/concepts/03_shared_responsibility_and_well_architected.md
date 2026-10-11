Exam tasks: 1.1, 1.2, 1.3

# 03 — Shared responsibility and the Well-Architected Framework

## What it is

Two ideas that sit behind many exam questions.

**The shared responsibility model** says who is responsible for what when you use
AWS. AWS looks after some things. You look after the rest. Misreading the line is
the most common cause of security mistakes in the cloud, and a favourite exam
topic.

**The AWS Well-Architected Framework** is AWS's checklist for judging a design. It
has six pillars. When a question asks for the "best" design, the pillars tell you
what "best" can mean.

## How it works

### Security OF the cloud versus security IN the cloud

The model has one sentence you must know:

- AWS is responsible for security **of** the cloud.
- You are responsible for security **in** the cloud.

Security **of** the cloud is everything AWS must run so that the services exist:
the data centres, the physical hardware, the network cabling, the virtualisation
layer that separates customers, and the software of the services themselves.
Auditors check this. AWS publishes the reports (find them in AWS Artifact).

Security **in** the cloud is what you do with those services: who may use them,
what data you put in them, how that data is protected, and how you set them up.

You can picture a stack of layers:

```
  your data
  access control (who may do what)
  application code
  runtime / language libraries
  operating system
  virtualisation
  physical hardware, buildings, network
```

AWS always owns the bottom of the stack. You always own the top. The question is
where the line between them sits for the service in front of you.

### The line moves with how managed the service is

The more managed a service is, the more layers AWS runs for you and the fewer
you do.

- With a service where you rent a virtual machine, you get a blank machine. You
  build upward from the virtualisation layer.
- With a managed service, AWS builds some of the upper layers for you and hands
  you a ready-made engine or runtime.
- With a serverless service, AWS runs nearly everything below your code, and you
  bring only code, data and configuration.

So moving from "virtual machine" to "managed" to "serverless" shifts the line
upward. This is the heart of "LEAST operational overhead" questions: managed and
serverless services remove work from your side of the line.

Which layers sit on which side for EC2, RDS and Lambda is what drill 04 asks you
to work out. Use the layer picture above and the rule "more managed means the
line moves up". To practise the idea on other services first, try these:

- **Amazon S3.** AWS runs the storage fleet, the hardware and the S3 software.
  You decide the bucket policy, who has access, whether to turn on versioning, and
  whether to use a customer-managed encryption key.
- **Elastic Load Balancing.** AWS runs the load balancer fleet. You decide the
  listeners, the security groups, the certificates and which targets sit behind it.
- **Amazon EBS.** AWS runs the storage hardware. You decide whether the volume is
  encrypted, who may attach it, and when to snapshot it.

### What never moves

No matter how managed a service is, these stay with you:

- **Your data.** What you store, how it is classified, who may see it, and how
  long you keep it.
- **Identity and access.** IAM users, roles, policies, MFA, the principle of
  least privilege. AWS provides IAM. You configure it.
- **Your configuration.** A managed service can still be set up unsafely: a
  public bucket, a security group open to the whole internet, no backups.
- **Client-side encryption choices.** If you encrypt data before sending it to
  AWS, you manage those keys and that process. For server-side encryption you
  choose the key type and key policy, though AWS does the encrypting.
- **Your own application code and its dependencies.**
- **Network access you define**, such as security groups and network ACLs.

Memory aid: AWS runs the platform. You decide who gets in and what is inside.

### Shared controls

Some controls are shared. Each side does its part. Examples: patch management
(AWS patches the infrastructure it runs; you patch what you run), configuration
management, and awareness and training (AWS trains its staff; you train yours).

### The six pillars

| Pillar | Two design principles | Task statements it maps to |
|---|---|---|
| Operational excellence | perform operations as code; make frequent, small, reversible changes | 2.2 (automation strategies, immutable infrastructure) |
| Security | implement a strong identity foundation (least privilege); apply security at all layers and enable traceability | 1.1, 1.2, 1.3 |
| Reliability | automatically recover from failure; scale horizontally to increase aggregate availability | 2.1, 2.2 |
| Performance efficiency | use serverless architectures; go global in minutes | 3.1, 3.2, 3.3, 3.4, 3.5 |
| Cost optimisation | adopt a consumption model (pay for what you use); stop spending money on undifferentiated heavy lifting | 4.1, 4.2, 4.3, 4.4 |
| Sustainability | maximise utilisation of what you run; use managed services to share the load | 4.2 (optimise compute utilisation) |

The principles above are short paraphrases. The framework lists more.

How to use the pillars on the exam:

- A question that stresses **security** wants least privilege, encryption,
  private networking and audit logs.
- **Reliability** wants Multi-AZ, no single point of failure, automatic recovery.
- **Performance efficiency** wants the right resource type, caching, scaling.
- **Cost optimisation** wants the cheapest design that still meets every stated
  requirement. Never cheaper than the requirement allows.
- **Operational excellence** wants automation: infrastructure as code,
  monitoring, runbooks.
- **Sustainability** shows up as high utilisation and fewer idle resources.

Pillars can pull against each other. A Multi-AZ database improves reliability
and costs more. The deciding phrase in the question settles the trade-off.

### The Well-Architected Tool

The AWS Well-Architected Tool is a free service in the console. You answer
questions about your workload and it lists risks against the pillars. It reviews
a design. It does not change anything.

## Numbers to know

Little here is numeric. Know these counts:

| Fact | Value |
|---|---|
| Well-Architected pillars | 6 |
| Task statements in Domain 1 (Secure) | 3 |
| Domain 1 weight | 30 % — the largest single domain |

## When to choose it

Use the shared responsibility model when a question asks "who is responsible
for…" or "what must the company still do…". Work down the layer stack and ask
which layers the service hands to you.

Use the pillars when a question asks you to "improve" or "review" a design. Ask
which pillar the stated problem belongs to. Then look for the option that
repairs that pillar without breaking the hard constraints.

## Exam traps

- **"AWS handles security, so we do not need to."** Never true. Data, IAM and
  configuration are always yours.
- **Assuming a managed service is secure by default in every way.** AWS secures
  the service. You can still make it public by misconfiguring it.
- **Mixing up "of" and "in".** "Physical security of the data centre" is AWS.
  "Who can read the object" is you.
- **Thinking serverless means no responsibility.** Serverless shrinks your side.
  It does not empty it: code, data and permissions remain.
- **Pillar confusion.** Cost optimisation does not mean "cheapest at any price".
  It means the lowest cost that still meets the requirements.
- **Choosing a pillar the question did not ask for.** If the question says
  "improve reliability", a faster but single-AZ design is wrong.
- **Forgetting the shared controls.** Patching is not purely one side's job. It
  depends on which layer is being patched.

## Cost angle

- The more managed the service, the less staff time you spend on the lower
  layers. That is a real cost, even if the hourly price looks higher.
  "Undifferentiated heavy lifting" is the Well-Architected name for work AWS can
  do better than you.
- The cost pillar principle "adopt a consumption model" means paying for use,
  not for peak capacity sitting idle.
- Sustainability and cost often agree: fewer idle resources means a smaller bill
  and a smaller footprint.
- Compliance evidence (the AWS Artifact reports) is free to download. It saves
  you from auditing the data centres yourself.

## Comparison

This table compares what *you* are asked to run or decide in each service. It
deliberately leaves out the patching and operating-system rows, which are drill
04.

| Question | EC2 (virtual machine) | RDS (managed database) | Lambda (serverless function) |
|---|---|---|---|
| What do you bring? | an image, software, data | a database schema and data | function code and configuration |
| What do you size? | instance type and count | instance class and storage | memory per invocation and timeout |
| How does it scale? | you set up Auto Scaling | you resize, add replicas, or use Aurora | AWS runs more copies when needed |
| How is availability designed? | you spread across AZs | you turn on Multi-AZ | AWS runs it across AZs in the Region |
| Who decides who may use it? | you (IAM, security groups) | you (IAM, security groups, database users) | you (IAM execution role, resource policies) |
| Who owns the data and its encryption choices? | you | you | you |
| What does the bill follow? | time instances run | time instances run plus storage | requests and run time |

Now do drill 04, then the quiz questions on shared responsibility and the Well-Architected pillars.

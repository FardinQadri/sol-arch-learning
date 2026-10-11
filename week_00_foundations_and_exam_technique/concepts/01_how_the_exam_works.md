Exam tasks: 1.1, 2.2, 3.2, 4.2

# 01 — How the exam works

## What it is

The AWS Certified Solutions Architect – Associate exam (code SAA-C03) is a
scenario exam. Each question describes a business problem. You pick the AWS
design that fits best.

It does not test whether you can click through the console. It tests whether you
can read a short story, spot what matters, and choose between services that all
sound reasonable.

The facts of record (from `docs/facts.md`):

| Item | Value |
|---|---|
| Questions | 65 in total |
| Scored | 50 |
| Unscored | 15 (AWS does not tell you which) |
| Question types | multiple choice (1 right of 4) · multiple response (2 or more right of 5 or more) |
| Time | 130 minutes |
| Price | 150 USD |
| Score | scaled 100–1,000 |
| Pass mark | 720 |
| Scoring model | compensatory |
| Guessing | no penalty; an unanswered question counts as wrong |

Take a moment with the last two rows.

- Compensatory means you do not need to pass each domain. Only the overall
  score counts. A weak domain can be paid for by a strong one.
- No penalty for guessing means you never leave a blank. Always pick something.

## How it works

### The four domains

| Domain | Name | Weight of scored content |
|---|---|---|
| 1 | Design Secure Architectures | 30 % |
| 2 | Design Resilient Architectures | 26 % |
| 3 | Design High-Performing Architectures | 24 % |
| 4 | Design Cost-Optimized Architectures | 20 % |

The weights add up to 100 % (30 + 26 + 24 + 20). Applied to the 50 scored
questions, that is roughly 15, 13, 12 and 10 questions. (50 × 0.30 = 15,
50 × 0.26 = 13, 50 × 0.24 = 12, 50 × 0.20 = 10.) You cannot tell which of the 65
are the unscored ones, so treat every question as if it counts.

### The 14 task statements

Each domain splits into task statements. There are 14: Domain 1 has 3,
Domain 2 has 2, Domain 3 has 5 and Domain 4 has 4. Every note and every drill in
this course is tagged with the task ids it serves.

| Id | Task statement |
|---|---|
| 1.1 | Design secure access to AWS resources |
| 1.2 | Design secure workloads and applications |
| 1.3 | Determine appropriate data security controls |
| 2.1 | Design scalable and loosely coupled architectures |
| 2.2 | Design highly available and/or fault-tolerant architectures |
| 3.1 | Determine high-performing and/or scalable storage solutions |
| 3.2 | Design high-performing and elastic compute solutions |
| 3.3 | Determine high-performing database solutions |
| 3.4 | Determine high-performing and/or scalable network architectures |
| 3.5 | Determine high-performing data ingestion and transformation solutions |
| 4.1 | Design cost-optimized storage solutions |
| 4.2 | Design cost-optimized compute solutions |
| 4.3 | Design cost-optimized database solutions |
| 4.4 | Design cost-optimized network architectures |

### How to read a scenario

Most scenarios contain more detail than you need. Use the same three steps every
time.

1. Find the deciding requirement. It is usually one phrase near the end of the
   question. Typical ones:
   - MOST cost-effective
   - LEAST operational overhead
   - highest availability
   - with minimum changes to the application
   - MOST secure
2. Cross out options that break a hard constraint. Hard constraints are facts
   such as "must stay in one Region", "data must be encrypted at rest", "cannot
   change the code", "needs a relational database". An option that breaks one is
   wrong, however good it looks otherwise.
3. Between the last two, choose on the deciding requirement. Both survive the
   constraints, so the deciding phrase is what separates them.

Do this in order. People lose marks by jumping to step 3 with a favourite
service in mind.

### Select TWO (and THREE) questions

- The question says "Select TWO" (or THREE). Count the options: five for TWO,
  six for THREE.
- You must pick all the right ones to score. There is no partial credit to rely
  on, so be careful rather than quick.
- Treat each option as a true/false statement against the scenario. Mark each
  one, then see if the count matches what was asked.
- Two options that do the same job are usually both wrong or one is a decoy.
  The correct pair usually does two different jobs, for example one for
  security and one for availability.

### Keyword to direction

Keywords do not give you the answer. They point you at the right family of
services. Always confirm against the hard constraints.

| Phrase in the question | Think first of |
|---|---|
| least operational overhead | managed or serverless services (Lambda, Fargate, DynamoDB, Aurora) |
| decouple the components | SQS, SNS, EventBridge |
| millisecond reads at any scale | DynamoDB (DAX in front if it must be microseconds) |
| static content to users worldwide | CloudFront in front of S3 |
| relational, joins, transactions | RDS or Aurora |
| survive the loss of an Availability Zone | Multi-AZ, spread across at least 2 AZs |
| survive the loss of a Region | cross-Region replication, DR strategy, Route 53 failover |
| minimum changes to the application | lift-and-shift style: same engine, same protocol (EC2, RDS, EFS, Storage Gateway) |
| irregular or unpredictable traffic | auto scaling, serverless, on-demand capacity |
| steady, predictable, long-running | Savings Plans or Reserved capacity |
| interruptible batch work | Spot Instances |
| encrypt and control the keys | AWS KMS (customer managed key) |
| store credentials securely, rotate | Secrets Manager |
| archive that is rarely read | S3 Glacier storage classes |
| temporary access, no long-lived keys | IAM roles with STS, IAM Identity Center |
| block SQL injection or bad bots | AWS WAF |
| private access to a service, not over the internet | VPC endpoints, PrivateLink |

Warning signs: the words "only" and "must" are hard constraints. The words
"MOST" and "LEAST" are comparisons, so more than one option may work and you
need the best.

### Time plan

130 minutes for 65 questions is 2 minutes per question (130 ÷ 65 = 2).

- First pass: answer what you can in about 2 minutes. If you are stuck after
  that, pick your best guess, flag the question, and move on.
- Second pass: spend the time you saved on the flagged ones.
- Never leave a question blank when time runs out — a guess is free.
- Long scenarios: read the last sentence (the actual question) first, then the
  story.

### How this course prepares you

- `python quiz.py --week 0 -n 15` asks questions from the week-0 bank. Every
  option is explained, right or wrong.
- Mock exams (in `exam_prep/`) practise the pacing at full length.
- Drills train the skills the questions need, so you can compute and reason
  instead of memorising.

## Numbers to know

| Number | Meaning |
|---|---|
| 65 | questions on the exam |
| 50 + 15 | scored plus unscored |
| 130 min | time allowed |
| 2 min | average time per question (130 ÷ 65) |
| 720 | passing scaled score |
| 100–1,000 | scaled score range |
| 150 USD | exam fee |
| 30 / 26 / 24 / 20 % | domain weights |
| 14 | task statements (3 + 2 + 5 + 4) |

## When to choose it

Read this note when you are about to take a first mock exam, and again the week
before the real one. The method (deciding requirement, cross out, choose) is the
one habit that applies to all 14 task statements.

## Exam traps

- Picking the first service that "sounds right". Cross out first.
- Ignoring the deciding phrase. A secure, resilient design can still be the
  wrong answer if the question said LEAST operational overhead and your pick
  needs servers to patch.
- Over-engineering. If the question asks for the lowest cost, do not choose a
  multi-Region design because it feels safer.
- Answering a different question. "Highest availability" is not the same as
  "lowest latency".
- Select TWO with a partial answer. Count your selections before moving on.
- Trusting old facts. Some limits changed after 2022 (for example the S3 maximum
  object size is now 50 TB, previously 5 TB). The exam may lag behind. When a
  question depends on such a number, the rest of the scenario usually makes the
  intent clear. The course only ever teaches today's value.
- Leaving questions blank. A blank is wrong; a guess has a chance.
- Assuming the exam is fixed. AWS has replaced associate exams with only a few
  weeks of notice. Re-check the certification page before booking:
  https://aws.amazon.com/certification/certified-solutions-architect-associate/

## Cost angle

The exam costs 150 USD. That is a reason to sit it ready, not to sit it twice.
Use the mock exams to find weak domains before you pay. Also, about one fifth of
the scored questions (Domain 4, 20 %) are about cost, so the cost angle in every
note is exam content, not decoration.

## Comparison

| Question type | Options shown | Right answers | Best habit |
|---|---|---|---|
| Multiple choice | 4 | 1 | cross out the two clearly wrong, then choose on the deciding requirement |
| Multiple response (TWO) | 5 | 2 | judge each option true or false, then check the count |
| Multiple response (THREE) | 6 | 3 | same, and expect each right option to add a different capability |

Now do drill 01 (read an ARN) and the quiz questions on exam technique (`python quiz.py --week 0 -n 15`).

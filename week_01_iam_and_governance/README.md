# Week 01 — IAM & multi-account governance

## Goals

By the end of this week you can:

1. Evaluate any set of policies by hand: explicit deny, SCPs, resource policy, identity policy, boundary, session policy.
2. Write least-privilege policies and find permissions nobody uses.
3. Use roles and temporary credentials everywhere, with no long-lived keys.
4. Design cross-account access safely: both sides allow, and an external ID for third parties.
5. Choose the right federation option: IAM Identity Center, SAML, OIDC, Cognito or Directory Service.
6. Lay out accounts with Organizations, SCPs and Control Tower, and explain how consolidated billing saves money.

## Your week

About 10–12 hours. Do the steps in order.

1. Concept notes 01–05 and the two demos in `concepts/` (~3 h). Run the demos:
   `python concepts/demo_policy_decisions.py` and `python concepts/demo_iam_enforced.py`.
2. Drills: `python practice/exercises.py` (~3–4 h). Drills 01–04 are the heart of the domain: you build a policy evaluator. Do them in order.
3. Quiz: `python quiz.py --week 1 -n 30` until you score 80 % or more (~1.5 h).
4. Milestone M01: IAM baseline for the course project (~2 h). See `course_project/milestones/M01.md`.
5. Optional lab (~1 h, 0 USD): `lab/LAB.md`. Roles, the policy simulator, Access Analyzer.

## Exam tasks covered

| Task | Title |
|---|---|
| 1.1 | Design secure access to AWS resources |
| 1.2 | Design secure workloads and applications |
| 4.1 | Design cost-optimized storage solutions |

Task 1.1 is the main target: roles, policies, federation, multiple accounts.
Task 1.2 appears through roles, Cognito and credential security. The 4.1 link is
consolidated billing and pooled volume tiers (note 04, drill 09).

## Service comparison

| Option | Who signs in | Credentials | Use it when |
|---|---|---|---|
| IAM user | A named person or tool | Long-lived password / access keys | A legacy tool cannot assume roles; break-glass only |
| IAM role | Anyone trusted: a service, another account, a federated user | Temporary, from STS | Almost everything: EC2, Lambda, cross-account, CI |
| IAM Identity Center | Your workforce | Temporary, through a portal | Many accounts, one place to manage staff access |
| Amazon Cognito | Your app's customers | Tokens; AWS credentials via identity pools | Sign-up and sign-in for app users |
| AWS Directory Service | Windows and AD users | Kerberos / AD | "Use our Active Directory", Windows workloads |

## Interview questions

Answer each out loud in under two minutes.

1. Walk through how AWS decides whether a request is allowed.
2. What is the difference between an explicit deny and an implicit deny?
3. How does an EC2 instance get credentials?
4. How would you give a partner read access to one bucket?
5. What is the confused-deputy problem, and how does an external ID fix it?
6. What can an SCP do that an IAM policy cannot, and what can it never do?
7. How do permissions boundaries let you delegate role creation safely?
8. How would you find and remove unused permissions?
9. When would you use IAM Identity Center instead of IAM users?
10. How does consolidated billing save money?

Now you may read `_harness/awslib/policy_eval.py` — compare it with your drills 01–04.

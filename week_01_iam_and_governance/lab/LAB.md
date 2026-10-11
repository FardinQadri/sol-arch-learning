# Week 01 lab — roles, the simulator and Access Analyzer

About 60 minutes. Cost: 0 USD — IAM, STS, the policy simulator and an account Access Analyzer are free.
This lab is optional. Everything the course grades runs offline.

## 1. Before you start

- The week 00 lab is done: you have the `saa-lab` profile and sign in through IAM Identity Center.
- Use `--profile saa-lab` on every CLI command below.
- Do **not** create an AWS Organization or a Control Tower landing zone in a Free-plan account.
  A Free-plan account that joins Organizations is upgraded to Paid automatically (`docs/facts.md`).
  Practise SCPs offline with the drills.
- Tag everything you create `saa-course=lab`, so the cleanup script can find it.

## 2. A role for EC2, in the console

1. IAM → Roles → Create role. Trusted entity: **AWS service**, use case **EC2**.
2. Skip the managed policies. Name the role `saa-lab-ec2-role`.
3. After creating it, open the role → Add permissions → Create inline policy (JSON): allow
   `s3:ListAllMyBuckets` on `*`. Name it `list-buckets`.
4. Add the tag `saa-course=lab`.
5. Open the **Trust relationships** tab and read it. It names `ec2.amazonaws.com`.
6. The console also created an **instance profile** with the same name. The CLI would have made you create it yourself.
   You will not launch an instance.

## 3. A role you can assume, with MFA

1. Create a role `saa-lab-mfa-role` whose trusted entity is **your own account**, and tick **Require MFA**.
   Attach the AWS managed policy `ReadOnlyAccess`. Tag it `saa-course=lab`.
2. Read its trust policy. Find the `aws:MultiFactorAuthPresent` condition.
3. Assume it from the CLI (you need an MFA device registered to the identity you call from):

   ```bash
   aws sts assume-role --profile saa-lab \
     --role-arn arn:aws:iam::<ACCOUNT_ID>:role/saa-lab-mfa-role \
     --role-session-name my-lab-session \
     --serial-number <MFA_DEVICE_ARN> --token-code <6_DIGITS>
   ```

4. Export the three returned values (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`)
   in a shell, then run `aws sts get-caller-identity`.
5. Compare the ARN with week 00's. This one ends in `assumed-role/saa-lab-mfa-role/my-lab-session`.
   Close that shell afterwards so the credentials are gone.

If you sign in only through Identity Center and have no IAM-side MFA device, the call will fail.
Write down why. That failure is the lesson: an MFA condition needs an MFA-authenticated caller.

## 4. The IAM policy simulator

1. Open the simulator (search "IAM policy simulator" or use the link in the IAM console).
2. Select `saa-lab-ec2-role`. Choose the service **S3** and the actions `GetObject` and `DeleteObject`. Run it.
3. Both are **denied** (the role only allows `ListAllMyBuckets`). Now simulate `ListAllMyBuckets`: allowed.
4. Add an explicit `Deny` for `s3:*` to the inline policy and simulate `ListAllMyBuckets` again.
   It flips to denied. The simulator names the statement that decided it.

## 5. IAM Access Analyzer

1. Open IAM Access Analyzer → Create analyzer. Type: **External access**, zone of trust: **this account**.
   (An account-level external-access analyzer is free.)
2. Create a test bucket `saa-lab-analyzer-<your-initials>-<random>` and tag it `saa-course=lab`.
3. Add a bucket policy that allows `s3:GetObject` to another AWS account ID (use a made-up but valid
   12-digit ID). Block Public Access is on for new buckets and does not stop cross-account grants like this.
4. Wait a few minutes and refresh the analyzer. A **finding** appears: external access to the bucket.
5. Remove the statement from the bucket policy. The finding resolves.

## 6. A customer managed policy and a user with no console access

1. Create a customer managed policy `saa-lab-read-one-bucket` allowing `s3:GetObject` on
   `arn:aws:s3:::saa-lab-analyzer-*/*`. Tag it `saa-course=lab`.
2. Create an IAM user `saa-lab-user` with **no console access**, no access keys, and the tag `saa-course=lab`.
   Attach your policy. The user cannot sign in or call anything. It is only here for the cleanup to find.

## 7. Clean up

```bash
python lab/cleanup.py --profile saa-lab          # dry run: read the list
python lab/cleanup.py --profile saa-lab --yes    # deletes tagged roles, policies and users
```

The script deletes the tagged IAM roles, customer managed policies and users only.
By hand: delete the Access Analyzer and the test bucket (empty it first), or tag the bucket and run
week 00's cleanup. The instance profile from step 2 goes with the role.

## 8. What to write down

- The assumed-role ARN from step 3 (or why it failed).
- The simulator results from step 4, before and after the explicit deny.
- The Access Analyzer finding from step 5: resource, external principal, action.

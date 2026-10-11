# Week 00 lab — a safe first hour in a real AWS account

Time: about 60–90 minutes. Cost: about 0 USD if you follow the clean-up step.

## 1. Before you start

- This lab uses your **real AWS account**. It is optional. Everything the course
  grades runs offline, so you lose nothing by skipping it.
- If you need an account, create one. When you sign up you choose a plan:
  - New accounts pick a **Free plan** or a **Paid plan**. Both get 100 USD in
    credits, plus up to 100 USD more for completing activities.
  - The Free plan ends after 6 months or when the credits run out. The account
    then closes, and you have 90 days to upgrade before it is deleted.
  - A Free-plan account is upgraded to Paid automatically if it joins AWS
    Organizations or sets up a Control Tower landing zone. This course never asks
    you to do either in a lab.
  - Do not count on the older "12-month free tier". It applies only to older
    accounts.
- Read this whole file before you click anything. Do the guard rails (step 5)
  before the first calls (step 6).
- Never paste access keys into a file, a chat or a terminal history.

## 2. Lock the root user

The root user is the e-mail address you signed up with. It can do everything and
cannot be restricted.

1. Sign in as root. Open **Security credentials** (account menu, top right).
2. Add an **MFA device** (an authenticator app is fine).
3. Make sure there are **no root access keys**. If any exist, delete them.
4. Sign out of root. You will not use it again for day-to-day work.

## 3. An admin you sign in with

1. Open **IAM Identity Center** and enable it (choose a Region you will keep using).
2. Create a **user** for yourself (your own e-mail). Accept the invitation and set
   a password and MFA.
3. Create a **permission set** that uses the managed policy `AdministratorAccess`.
4. Assign your user and that permission set to your AWS account.
5. Note the **AWS access portal URL**. You sign in there from now on.

## 4. CLI with short-lived credentials

1. Install AWS CLI v2 from the official AWS documentation.
2. Run `aws configure sso`. Give it the access portal URL, the Identity Center
   Region, then pick your account and the permission set. Use the profile name
   `saa-lab`.
3. Sign in and check who you are:

   ```
   aws sso login --profile saa-lab
   aws sts get-caller-identity --profile saa-lab
   ```

4. Look at the `Arn` field. It shows an **assumed role**, not a user. That is the
   short-lived credential at work. You will study how assumed roles work in week 01.

## 5. Spending guard-rails

Do these before you create anything.

1. **Budgets.** In AWS Budgets, create a budget from the template **Zero spend
   budget** (alerts when you spend anything). Create a second from **Monthly
   cost budget** with a limit such as 5 USD. Use your e-mail for notifications.
2. **Billing preferences.** Turn on **Receive CloudWatch Billing Alerts**.
3. **Billing alarm.** Switch to the `us-east-1` Region (billing metrics live
   there). In CloudWatch, create an alarm on the metric `EstimatedCharges`
   with the threshold greater than 5 USD. Send the alarm to a new SNS topic with
   an e-mail subscription. Confirm the e-mail subscription.

## 6. First calls

Replace `<your-initials>` and `<random>` so the bucket name is unique worldwide.

1. Create a bucket in `us-east-1`. Give **no** LocationConstraint here:

   ```
   aws s3api create-bucket --bucket saa-lab-<your-initials>-<random> --region us-east-1 --profile saa-lab
   ```

2. Create a second bucket in `eu-west-1`. First **without** a location:

   ```
   aws s3api create-bucket --bucket saa-lab-<your-initials>-<random>-eu --region eu-west-1 --profile saa-lab
   ```

   Read the error and write it down. Then repeat **with** it:

   ```
   aws s3api create-bucket --bucket saa-lab-<your-initials>-<random>-eu --region eu-west-1 --create-bucket-configuration LocationConstraint=eu-west-1 --profile saa-lab
   ```

3. **Tag every bucket you made** so the clean-up script can find it:

   ```
   aws s3api put-bucket-tagging --bucket <bucket-name> --tagging 'TagSet=[{Key=saa-course,Value=lab}]' --profile saa-lab
   ```

   (Add `--region eu-west-1` for the second bucket.)

4. Upload a small file: `aws s3 cp hello.txt s3://<bucket-name>/ --profile saa-lab`.
5. Return one item at a time with `--max-items 1` and see the token:

   ```
   aws s3api list-objects-v2 --bucket <bucket-name> --max-items 1 --profile saa-lab
   ```

   If the bucket holds more than one object the output ends with a `NextToken`.
   Upload a second file first if needed.

## 7. Clean up

The script only deletes S3 buckets tagged `saa-course=lab`. It does nothing
unless you add `--yes`.

1. Dry run. Read the list it prints:

   ```
   python lab/cleanup.py --profile saa-lab
   ```

2. Delete for real:

   ```
   python lab/cleanup.py --profile saa-lab --yes
   ```

3. Repeat both for each other Region you used:

   ```
   python lab/cleanup.py --profile saa-lab --region eu-west-1
   python lab/cleanup.py --profile saa-lab --region eu-west-1 --yes
   ```

Leave in place: the budgets, the billing alarm, the SNS topic and IAM Identity
Center. They are your safety net.

## 8. What to write down

Keep these three in a notes file:

- your **account ID** (from `get-caller-identity`);
- the **assumed-role ARN** you saw in step 4;
- the **error message** you got in step 6.2, and what it taught you about
  `LocationConstraint`.

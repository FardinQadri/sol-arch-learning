# Week 04 lab — a versioned bucket, a lifecycle rule, a presigned URL and an EBS volume

About 60 minutes. Cost: a few cents. A bucket with a few bytes in it costs nothing noticeable. A 1 GiB gp3 volume (then 8 GiB)
costs 0.08 USD per GB-month at the course's illustrative price, which is a fraction of a cent for the hour you keep it.
Snapshots of an empty volume store almost nothing. This lab is optional. Everything the course grades runs offline.

## 1. Before you start

- The week 00 guard rails are done (budget alert, MFA, no root keys) and you have the `saa-lab` profile.
- Use one Region for the whole lab and stay in it. The commands below use `us-east-1`. If you pick another Region, add
  `--create-bucket-configuration LocationConstraint=<region>` to `create-bucket`.
- Tag **every** resource `saa-course=lab`: the bucket, the volume and both snapshots. The cleanup script only finds tagged ones.
- Set two shell variables. In Git Bash or Linux:

```bash
export AWS_PROFILE=saa-lab AWS_DEFAULT_REGION=us-east-1
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
BUCKET=saa-lab-$ACCOUNT-w04
```

(In PowerShell use `$env:AWS_PROFILE = "saa-lab"` and build `$BUCKET` the same way.)

## 2. A versioned bucket

```bash
aws s3api create-bucket --bucket $BUCKET
aws s3api put-bucket-tagging --bucket $BUCKET --tagging 'TagSet=[{Key=saa-course,Value=lab}]'
aws s3api put-bucket-versioning --bucket $BUCKET --versioning-configuration Status=Enabled
```

Now look at what a new bucket already has, without changing anything:

```bash
aws s3api get-bucket-encryption --bucket $BUCKET
aws s3api get-public-access-block --bucket $BUCKET
aws s3api get-bucket-ownership-controls --bucket $BUCKET
```

Write down: the default encryption algorithm (SSE-S3, `AES256`), the four Block Public Access settings (all `true`) and the
Object Ownership value (`BucketOwnerEnforced`, which means ACLs are disabled). You did not set any of them.

Wait about 15 minutes after enabling versioning before you write objects, as the docs advise. Meanwhile, read step 3.

Upload a file twice, with different content, then delete it:

```bash
echo "version one" > note.txt
aws s3 cp note.txt s3://$BUCKET/note.txt
echo "version two" > note.txt
aws s3 cp note.txt s3://$BUCKET/note.txt
aws s3 rm s3://$BUCKET/note.txt
aws s3 ls s3://$BUCKET/
aws s3api list-object-versions --bucket $BUCKET
```

`aws s3 ls` shows nothing: the key looks deleted. `list-object-versions` shows two versions and one **delete marker** with
`IsLatest: true`. Copy the delete marker's `VersionId`, then restore the object by deleting the marker:

```bash
aws s3api delete-object --bucket $BUCKET --key note.txt --version-id <delete-marker-version-id>
aws s3 cp s3://$BUCKET/note.txt -
```

You see `version two`. Read the old one too, with `aws s3api get-object --bucket $BUCKET --key note.txt --version-id <older-version-id> old.txt`.
Check `list-object-versions` once more: two versions, no marker.

## 3. A lifecycle rule

Save this as `lifecycle.json`:

```json
{
  "Rules": [
    {
      "ID": "tier-and-tidy",
      "Status": "Enabled",
      "Filter": {},
      "Transitions": [{ "Days": 30, "StorageClass": "STANDARD_IA" }],
      "NoncurrentVersionExpiration": { "NoncurrentDays": 30 },
      "AbortIncompleteMultipartUpload": { "DaysAfterInitiation": 7 }
    }
  ]
}
```

```bash
aws s3api put-bucket-lifecycle-configuration --bucket $BUCKET --lifecycle-configuration file://lifecycle.json
aws s3api get-bucket-lifecycle-configuration --bucket $BUCKET
```

Read it back. Current versions move to Standard-IA at 30 days, old versions are deleted 30 days after they are replaced, and unfinished multipart
uploads are aborted after 7 days. Lifecycle runs **asynchronously** and your objects are minutes old, so **nothing moves today**. That
is the point: you will not see this rule work in a lab, which is why drill 02 models it. Also note that `note.txt` is under 128 KB, so by default
it would not be transitioned even after 30 days.

## 4. A presigned URL

```bash
aws s3 presign s3://$BUCKET/note.txt --expires-in 300
```

Copy the long URL. Open it in a browser or run `curl -s "<url>"`. You get `version two`. Wait five minutes and open it again. S3 now refuses it
with an error about an expired request. If your profile signs with temporary credentials (a role or SSO), the URL can expire even earlier,
when the session does. Anyone holding the URL could read the file for those five minutes without credentials.

## 5. An EBS volume

Pick an AZ in your Region (`us-east-1a` below). The volume is **not attached to anything**.

```bash
aws ec2 create-volume --availability-zone us-east-1a --size 1 --volume-type gp3 \
  --tag-specifications 'ResourceType=volume,Tags=[{Key=saa-course,Value=lab}]'
```

Note the `VolumeId`. A new gp3 volume has 3,000 IOPS and 125 MiB/s. Before you run the next command, predict: **will AWS accept 2 GiB with
4,000 IOPS?** (gp3 allows 500 IOPS per GiB.) Try it:

```bash
aws ec2 modify-volume --volume-id <volume-id> --size 2 --iops 4000
```

Read the error, work out the smallest size that allows 4,000 IOPS (8 GiB), then do that:

```bash
aws ec2 modify-volume --volume-id <volume-id> --size 8 --iops 4000
aws ec2 describe-volumes-modifications --volume-ids <volume-id>
```

Run the second command a few times. The state goes `modifying`, `optimizing`, then `completed`. The volume stayed usable all along: that is Elastic
Volumes. You can modify it only a limited number of times a day, and size can never shrink.

Snapshot it, then copy the snapshot with encryption switched on:

```bash
aws ec2 create-snapshot --volume-id <volume-id> \
  --tag-specifications 'ResourceType=snapshot,Tags=[{Key=saa-course,Value=lab}]'
aws ec2 copy-snapshot --source-region us-east-1 --source-snapshot-id <snapshot-id> --encrypted \
  --tag-specifications 'ResourceType=snapshot,Tags=[{Key=saa-course,Value=lab}]'
aws ec2 describe-snapshots --owner-ids self --filters Name=tag:saa-course,Values=lab \
  --query 'Snapshots[].[SnapshotId,VolumeSize,Encrypted,State,Progress]' --output table
```

This is how you encrypt an unencrypted volume: you cannot do it in place, so you snapshot, copy with encryption, then create a volume from the copy.
Both snapshots show `VolumeSize` 8 GiB, but snapshots are incremental and the volume is empty, so little is actually stored. If your CLI version
shows `FullSnapshotSizeInBytes`, compare it with the volume size.

## 6. Clean up

```bash
python lab/cleanup.py --profile saa-lab          # dry run: read the list
python lab/cleanup.py --profile saa-lab --yes    # deletes tagged resources
```

The script deletes, in this order: the tagged bucket (after aborting unfinished multipart uploads and removing every object version and delete marker; a bucket with objects under Object Lock retention is reported, not deleted), the tagged snapshots, then the tagged
volume. It does not touch anything without the `saa-course=lab` tag. If one deletion fails, it reports the error and carries on. Wait a minute
and run it again. Run the dry run first and check that exactly your bucket, two snapshots and one volume are listed.

Check the next day in Billing that no storage charges are still growing.

## 7. What to write down

- The default encryption, the four Block Public Access values and the Object Ownership value of a brand new bucket.
- What `aws s3 ls` showed after the delete, and what `list-object-versions` showed. Which entry was the delete marker.
- The exact command that brought the file back, and why it did not delete any data.
- What your lifecycle rule says, and why nothing moved.
- How long the presigned URL worked, and what the error looked like when it expired.
- Why 2 GiB with 4,000 IOPS was refused and what size made it legal.
- The volume's modification states, in order, and whether the volume was ever detached.
- How the encrypted snapshot copy differs from the first snapshot.
- How long the lab ran and the cost for that time.

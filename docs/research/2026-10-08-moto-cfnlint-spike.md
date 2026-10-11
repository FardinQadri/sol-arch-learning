# AWS offline course feasibility spike (moto + cfn-lint)

Python 3.14.2 (Windows 11, WDAC), venv in `aws-spike/venv`. Full pin list: `requirements-lock.txt`. All scripts use fake creds and `mock_aws`. No Docker.

## 1. Install
`pip install "moto[all]" cfn-lint boto3 pytest` worked first time, no Docker needed (the `docker` pip package is pulled in but unused).

| package | version |
|---|---|
| moto | 5.2.3 |
| boto3 / botocore | 1.43.109 / 1.43.109 |
| cfn-lint | 1.57.2 |
| pydantic / pydantic-core | 2.13.5 / 2.46.5 |
| regex | 2026.9.29 |
| PyYAML | 6.0.3 |
| cryptography | 50.0.2 |
| pytest | 9.1.1 |
| also | antlr4-python3-runtime 4.13.2 (Step Functions parser), py-partiql-parser 0.6.3, jsonschema 4.26.0, pywin32 312 |

**WDAC blocks: none** with the latest of everything (cryptography, pydantic-core, regex, PyYAML, pywin32 native wheels all imported fine). No pins were needed.
**Anomaly:** midway through, `venv\Scripts\python.exe` (and pythonw.exe) vanished from the venv (cause unknown, possibly Defender/AV acting on the venv launcher; no WDAC message). `python -m venv --upgrade venv` restored it. Course setup should tell students how to recreate the venv if that happens.

## 2. Import / mock_aws time (Windows, warm disk cache)
- `import boto3; from moto import mock_aws`: ~1.5-1.6 s (5.7 s on the very first cold run after install).
- First `with mock_aws():` + create S3 bucket in a process: ~0.62 s; subsequent blocks: ~0.12-0.13 s.
- `import cfnlint.api`: ~3.3 s.

## 3. Per-service smoke tests (`t3a.py`, output `t3a.out`)
All 37 targets WORK under `mock_aws` (first attempts failed only from my too-short names; moto enforces AWS min-length validation, which is itself useful for teaching).

| Service | Result | Notes |
|---|---|---|
| IAM (role, inline, managed attach, list) | WORKS | |
| STS assume_role / get_caller_identity | WORKS | account 123456789012; `RoleSessionName` min length 2 enforced |
| Organizations (org, OU, SCP create + attach) | WORKS | |
| EC2 (VPC, 2-AZ subnets, IGW, RT+routes, NAT, EIP, SG referencing SG, NACL entry, S3 gateway endpoint, launch template, run_instances) | WORKS | ~2.9 s first time (loads AMI list, 1177 images) |
| ELBv2 (ALB, TG, listener, path rule) | WORKS | |
| Auto Scaling (ASG from LT, target tracking) | WORKS | creates real mock instance |
| S3 (versioning, lifecycle, policy, PAB, SSE, presigned URL) | WORKS | presigned URL is generated (uses FOOBARKEY style signature, fine for mock) |
| EBS (gp3 volume, snapshot) | WORKS | |
| EFS (FS + mount target) | WORKS | |
| DynamoDB (GSI, TTL, PITR, conditional put fails, GSI query, transact_write) | WORKS | |
| RDS (postgres MultiAZ, read replica, snapshot) | WORKS | metadata only, no real DB |
| ElastiCache (redis replication group) | WORKS | |
| SQS (std + DLQ redrive, FIFO dedup, visibility timeout) | WORKS | message moved to DLQ after maxReceiveCount=2 (3rd receive returns none, DLQ has it); FIFO content dedup -> 1 msg |
| SNS (topic, SQS sub, filter policy, publish) | WORKS | filtered delivery verified: only matching message arrived |
| EventBridge (schedule rule + target) | WORKS | schedule does not fire on its own |
| Step Functions | WORKS with caveat | default: execution stays `RUNNING` forever. With `mock_aws(config={"stepfunctions": {"execute_state_machine": True}})` a Pass->Wait machine reaches `SUCCEEDED` with correct output (antlr4 installed via moto[all]) |
| Lambda create_function (zip) | WORKS | |
| Lambda invoke | see below | |
| API Gateway (REST API, resource, method, MOCK integration) | WORKS | |
| KMS (key, encrypt/decrypt, key policy) | WORKS | |
| Secrets Manager (+ rotation config) | WORKS | `rotate_secret` with lambda ARN accepted, rules stored |
| SSM SecureString | WORKS | |
| CloudWatch (metric, alarm, describe) | WORKS | |
| CloudWatch Logs | WORKS | |
| CloudTrail create trail | WORKS | |
| AWS Config rule | WORKS | |
| Route 53 (zone, weighted + failover records, health check) | WORKS | |
| CloudFront (S3 origin distribution) | WORKS | |
| ACM request cert | WORKS | status PENDING_VALIDATION |
| WAFv2 web ACL + rate-based rule | WORKS | |
| Kinesis put/get | WORKS | |
| Firehose -> S3 | WORKS | record actually written to the S3 bucket |
| Glue db + table | WORKS | |
| Athena start query | WORKS (stub) | state SUCCEEDED but empty result set (no rows/columns) |
| Backup plan | WORKS | |
| ECS (cluster, task def, service) | WORKS | no containers run |
| ECR | WORKS | |
| Cognito user pool + client | WORKS | |

### Lambda invoke without Docker
- Default config: `invoke` returns HTTP 200, `FunctionError: Handled`, payload text `error running docker: Error while fetching server API version...` (also prints that line to stdout). Code is NOT run.
- With `mock_aws(config={"lambda": {"use_docker": False}})`: invoke returns 200, no FunctionError, payload `{}`. Stub only, the handler is NOT executed. So Lambda function code can never be run under moto without Docker; course must test Lambda by calling the handler function directly in Python.

## 4. CloudFormation in moto (`stack.yaml`, `t4_cfn.py`, `t4b_verify.py`)
Short-form YAML (`!Ref !Sub !GetAtt !Select !GetAZs !ImportValue`) is parsed by moto directly. Full stack of 46 resources `create_stack` -> `CREATE_COMPLETE` in ~2.8 s. No resource caused the stack to fail. Bisect (each type alone plus its dependencies): every type reaches CREATE_COMPLETE; 5 types are **silently skipped** (moto prints "No Moto CloudFormation support for ..." as a warning only, stack still COMPLETE, resource not created and not listed in `list_stack_resources`).

| Resource type | Result |
|---|---|
| EC2::VPC, Subnet (GetAZs/Select, 2 AZs verified), InternetGateway, VPCGatewayAttachment, RouteTable, Route, SubnetRouteTableAssociation, EIP, NatGateway (available), SecurityGroup (SG-to-SG ingress verified) | CREATED |
| EC2::LaunchTemplate, AutoScaling::AutoScalingGroup (1 instance launched) | CREATED |
| S3::Bucket | CREATED, but only partly: BucketEncryption applied; **PublicAccessBlockConfiguration and LifecycleConfiguration silently NOT applied** (get_public_access_block / get_bucket_lifecycle_configuration return NoSuch...) |
| DynamoDB::Table, SQS::Queue (RedrivePolicy verified), SNS::Topic | CREATED |
| **SNS::Subscription** | **SKIPPED** (no subscription exists) |
| IAM::Role, IAM::Policy (inline policy verified), IAM::InstanceProfile | CREATED |
| KMS::Key, Lambda::Function (inline ZipFile), SSM::Parameter, Logs::LogGroup (retention 14 verified), Events::Rule (+target) | CREATED |
| ElasticLoadBalancingV2::LoadBalancer, TargetGroup, Listener | CREATED |
| RDS::DBSubnetGroup, RDS::DBInstance (MultiAZ true) | CREATED |
| Route53::HostedZone, RecordSet | CREATED |
| **CloudWatch::Alarm** | **SKIPPED** |
| **SecretsManager::Secret** | **SKIPPED** |
| **CloudFront::Distribution** | **SKIPPED** |
| **WAFv2::WebACL** | **SKIPPED** |

Edge behaviours:
- `!Ref` to a skipped resource gives an empty value -> downstream validation error at create_stack (e.g. SSM param Value ''). `!GetAtt` on a skipped resource -> create_stack raises `ValidationError: ... references undefined resource`. So skipped types can break a stack only when referenced.
- Unknown type (`AWS::Foo::Bar`) and invalid property (`NotAProp` on SQS Queue) both give CREATE_COMPLETE: moto does NO template validation. cfn-lint is therefore the validation layer.
- Outputs and Exports work (`list_exports` OK). `Fn::ImportValue` across two stacks works (consumer SG + SSM param got the VPC id). `list_imports` raises NotImplementedError.

## 5. cfn-lint
- CLI: `venv\Scripts\cfn-lint.exe stack.yaml` ~8.4 s wall (cold-ish); output: only `W2501 Password shouldn't be hardcoded` for the RDS password (intentional in spike). Otherwise clean (0 errors).
- In-process (`lint`) after import: 2.3-2.9 s per run for this 46-resource template; import of `cfnlint.api` 3.3 s.
- Injected errors, all caught:
  - invalid property (`RetentionDays`) -> E3002 "Additional properties are not allowed ('RetentionDays' was unexpected. Did you mean 'RetentionInDays'?)" line 292
  - bad !Ref target -> E1020 "'NoSuchThing' is not one of [...]" line 119
  - wrong value type (`Port: eighty`) -> E3012 "'eighty' is not of type 'integer'" line 229
- API (verified in `t5_lint.py`, source: `cfnlint/api.py`, `cfnlint/decode/decode.py`):
```python
from cfnlint.decode import decode_str      # decode_str(s: str) -> (template, list[Match]); also decode(filename)
tpl, errors = decode_str(open("stack.yaml").read())   # short-form tags become {"Fn::Sub": ...}, {"Ref": ...} etc.
print(tpl["Resources"]["PublicSubnetA"]["Properties"]["AvailabilityZone"])  # {'Fn::Select': [0, {'Fn::GetAZs': ''}]}
```
```python
from cfnlint.api import lint               # lint(s: str, rules=None, regions=None, config=None) -> list[Match]
for m in lint(open("stack.yaml").read()): print(m.rule.id, m.linenumber, m.message)   # also lint_file(path), lint_all(s)
```
  `decode_str` returns a `dict_node` (dict subclass); `json.loads(json.dumps(tpl))` gives a plain dict.

## 6. IAM enforcement in moto: WORKS (`t6_iam.py`)
```python
from moto.core import set_initial_no_auth_action_count
@set_initial_no_auth_action_count(4)   # first N API calls unauthenticated (admin setup), then enforced
@mock_aws
def demo(): ...   # create user + inline policy + access key (4 calls), build client with that key
```
User allowed `s3:ListAllMyBuckets` succeeded; `s3.create_bucket` -> `AccessDenied` (403); DynamoDB `list_tables` -> 403 (error Code field reads "403" rather than AccessDeniedException). The count must exactly equal the number of setup calls; the decorator order is `set_initial_no_auth_action_count` outermost. Env var `INITIAL_NO_AUTH_ACTION_COUNT` is the alternative.

## 7. Test-runner timing (`test_pytest15.py`, `test_unittest15.py`)
15 tests, each in its own `@mock_aws`, S3 + DynamoDB + SQS (+ EC2 VPC/subnet in 5 of them).
- pytest: 12.3-13.5 s reported, ~15.3-16.8 s wall including startup. First test costs ~3.7 s (cold service loading); others ~0.3-0.85 s.
- unittest: 10.8-12.4 s reported, ~14.4-16.1 s wall.
Budget ~1 s/test plus ~4 s startup.

## 8. UTF-8 (`t8.py`, `t8b.py`)
Piped or redirected output (`python x.py | cat`, `> file`) uses cp1252 and **crashes** with `UnicodeEncodeError` on the check mark. Any one of these fixes it: `sys.stdout.reconfigure(encoding="utf-8")` at the top of the script, env `PYTHONUTF8=1`, or `PYTHONIOENCODING=utf-8`; all three verified to print `✔ ✘ ★ →`. Needed in every course script that prints these symbols.

## Misc
- moto prints `error running docker: ...` lines to stdout whenever Lambda invoke is attempted with default config.
- Scripts: `env.py`, `t2_import.py`, `t3a.py`, `t3b.py`, `t4_cfn.py`, `t4b_verify.py`, `t5_lint.py`, `t6_iam.py`, `gen7.py`, `test_*15.py`, `t8*.py`.

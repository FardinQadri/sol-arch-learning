# Week 03 feasibility spike: EC2 launch templates, Auto Scaling, ELBv2 (moto 5.2.3 + cfn-lint 1.57.2)

Course venv (`.venv`): moto 5.2.3, boto3 1.43.109, cfn-lint 1.57.2, pytest 9.1.1. Fake credentials, `mock_aws`, region us-east-1, no network. Scripts and raw outputs are in the scratch folder `C:\Users\SYEDQA~1\AppData\Local\Temp\claude\C--Users-SyedQadri-Downloads-courses\65cfdac0-9a22-471b-8d76-56cc720b5245\scratchpad\spike03\`:
`common.py`, `a_ec2.py` (a.out), `b_asg.py` (b.out), `c_elb.py` (c.out), `net.yaml` + `compute.yaml` + `d_cfn.py` (d.out), `e_extra.py` (e.out), `f_lint.py` (f.out), `g_lint2.py` (g.out).
Earlier spike: `2026-10-08-moto-cfnlint-spike.md`.

Headline: moto stores almost every API field and returns it, but it **simulates very little behaviour**. Launch template settings do not reach instances, ASGs do not spread across AZs, health is always "healthy", and there is almost no cross-field validation. Only the API shape and CRUD are reliable, so scaling and placement behaviour must be taught from pure-Python models.

## A. EC2: launch templates, instance types, spot, placement groups (`a_ec2.py`, `e_extra.py`)

| Feature | Result | Notes |
|---|---|---|
| `create_launch_template` with ImageId, InstanceType, UserData (base64), IamInstanceProfile `{Name}`, MetadataOptions (HttpTokens, HttpPutResponseHopLimit, HttpEndpoint), SecurityGroupIds | YES | Everything stored and returned verbatim by `describe_launch_template_versions`. UserData comes back as the same base64 string. Create returns `DefaultVersionNumber=1, LatestVersionNumber=1`. |
| HttpTokens `required` / `optional`, any HopLimit | YES (stored) | No validation of the enum or the 1-64 hop-limit range at the LT level. |
| `create_launch_template_version` | PARTIAL | Version numbers increment, `VersionDescription` kept, but **`SourceVersion` is NOT merged**. The new version holds only the fields passed in (v2 had just `MetadataOptions`). A run from v2 then gave `m1.small` and an empty ImageId. Always pass the full `LaunchTemplateData`. |
| `$Latest` / `$Default`, `modify_launch_template(DefaultVersion=)`, `describe_launch_templates` | YES | `DefaultVersion` flag flips correctly. |
| `delete_launch_template_versions` | NO | `NotImplementedError: The delete_launch_template_versions action has not been implemented` |
| `run_instances(LaunchTemplate=...)` | PARTIAL | ImageId, InstanceType, UserData (readable with `describe_instance_attribute userData`) and SGs are applied. **`MetadataOptions.HttpTokens` from the template is NOT applied**: the instance shows `optional` even for a template saying `required` (v1, v2 and `$Latest` all tried). **`IamInstanceProfile` from the template is NOT applied** (`None`), with either `{Name}` or `{Arn}` in the template. |
| `run_instances(MetadataOptions=...)` direct | YES | Direct HttpTokens=required is reflected. Template plus explicit `MetadataOptions` on the call also works. Default for an instance with nothing specified is `HttpTokens: optional, HttpPutResponseHopLimit: 1, HttpEndpoint: enabled`. |
| `run_instances(IamInstanceProfile={'Name':...})` direct | YES | Returns `{'Arn': ..., 'Id': 'iip-assoc-...'}`. |
| `modify_instance_metadata_options` | YES | Updates are reflected in `describe_instances` (HttpTokens required, hop limit 3). |
| `describe_instance_types` m7g.large | YES | 2 vCPU, 8192 MiB, `['arm64']`, CurrentGeneration True. |
| `describe_instance_types` t4g.micro / c7g.xlarge | YES | t4g.micro 2 vCPU, 1024 MiB, arm64. c7g.xlarge 4 vCPU, 8192 MiB, arm64. |
| `describe_instance_types` t3.micro, m5.large, p4d.24xlarge | YES | t3.micro 2 vCPU/1024 MiB x86_64. m5.large 2/8192, `CurrentGeneration=False`. p4d.24xlarge 96/1179648. |
| Catalogue size and filters | YES | 1373 types in total. The `processor-info.supported-architecture=arm64` filter returns 396. `describe_instance_type_offerings(m7g.large)` returns 5 AZs. |
| `describe_spot_price_history` | PARTIAL | Returns fake data, a flat `0.00001` per AZ with timestamp 2006-01-02. Shape is correct and the numbers are meaningless. |
| `request_spot_instances` | YES | Immediately `State: active`, `Status.Code: fulfilled`, with an InstanceId. `describe_spot_instance_requests` works. `run_instances(InstanceMarketOptions={'MarketType':'spot'})` gives `InstanceLifecycle: spot`. |
| `request_spot_fleet` | NO | `KeyError: 'AllocationStrategy'` when the config omits it. Not investigated further. |
| Placement groups (`create_placement_group`, `describe_placement_groups`, `delete_placement_group`) | NO | `NotImplementedError: The create_placement_group action has not been implemented` (same text for describe and delete). cluster, spread and partition cannot be created at all. |
| `run_instances(Placement={'GroupName': 'pg-spread'})` | NO (silently ignored) | 9 instances went into one AZ with a group name that does not exist. No 7-per-AZ limit, no error. The group name is not stored (`Placement.GroupName` is `''`), and `describe_instances` filter `placement-group-name` raises `NotImplementedError: Filter dicts have not been implemented in Moto for 'placement-group-name' yet`. |

## B. Auto Scaling (`b_asg.py`, `e_extra.py`)

| Feature | Result | Notes |
|---|---|---|
| `create_auto_scaling_group` with LaunchTemplate, 2 subnets, Min/Max/Desired, HealthCheckType ELB, HealthCheckGracePeriod, TargetGroupARNs, DefaultCooldown, TerminationPolicies | YES | All fields round-trip. `AvailabilityZones` is derived from the subnets. Defaults: HealthCheckType `EC2`, GracePeriod 300, Cooldown 300, TerminationPolicies `['Default']`, Desired 0 if omitted. |
| Instances launched | YES | Desired=4 gives 4 real mock EC2 instances, `InService` / `Healthy`. They carry tags `aws:ec2launchtemplate:id`, `aws:ec2launchtemplate:version` (resolved to "1" even when the ASG says `$Latest`) and `aws:autoscaling:groupName`. |
| **AZ spreading** | NO | All 4 (then 6) instances landed in **us-east-1a**, the first subnet, though two subnets in two AZs were given. With `AvailabilityZones=[a,b]` and no subnets, both landed in one AZ (us-east-1b), not balanced. AZ rebalancing must be modelled. |
| Template HttpTokens / IamInstanceProfile on ASG instances | NO | Same as section A: HttpTokens `optional` and profile `None`, though the template has `required` and a profile. |
| `describe_auto_scaling_instances` | YES | InstanceId, AZ, LifecycleState `InService`, HealthStatus, group name. |
| Auto-registration in target group | YES | Instances launched by the ASG appear in `describe_target_health` of each `TargetGroupARNs` entry, state `healthy`. `attach_load_balancer_targets_groups` and `describe_load_balancer_target_groups` also work (State `Added`). |
| Target deregistration on scale-in / terminate | NO | After scaling 6 down to 3 the target group still listed 9 targets. Terminated instances are never deregistered, so TG state is unreliable after scaling in. |
| `set_desired_capacity` | PARTIAL | Scales out and in, launching and terminating instances. **No bounds check**: 7 with Max=6 and 1 with Min=2 both returned 200. (The ASG then followed the value; I only confirmed 6 and 3.) |
| `update_auto_scaling_group` | YES | |
| `create_auto_scaling_group` validation | PARTIAL | Rejects: no subnets and no AZs (`ValidationError: At least one Availability Zone or VPC Subnet is required.`), no LT/LC/instance id (`Valid requests must contain either LaunchTemplate, LaunchConfigurationName, InstanceId or MixedInstancesPolicy parameter.`), missing LT (`InvalidLaunchTemplateId.NotFound`). **Accepts** MinSize > MaxSize and Desired > Max without error. |
| `terminate_instance_in_auto_scaling_group` | YES | With `ShouldDecrementDesiredCapacity=False` a replacement is launched (count stays 3). |
| `set_instance_health(Unhealthy)` | PARTIAL | Flag stored, **no replacement** launched. Self-healing must be modelled. |
| `put_scaling_policy` TargetTracking: ASGAverageCPUUtilization, ALBRequestCountPerTarget (with ResourceLabel), custom metric | YES | Stored and returned by `describe_policies`. `ResourceLabel` is not validated (any string accepted). |
| `put_scaling_policy` StepScaling, SimpleScaling, PredictiveScaling | YES | Stored. Step adjustments come back as floats. `describe_policies` returns `AdjustmentType`, `StepAdjustments`. For SimpleScaling, `ScalingAdjustment` and `Cooldown` printed `None` in my describe (the fields were not in the output I extracted). Not retested. |
| Alarms for policies | NO | `cloudwatch.describe_alarms()` is empty after policies were created. No CloudWatch wiring, and nothing ever triggers. |
| `execute_policy` (SimpleScaling +2) | YES | Capacity moved from 3 to 5, instances launched. |
| Scheduled actions, warm pool | YES (stored) | `put_scheduled_update_group_action`, `describe_scheduled_actions`, `put_warm_pool` returned 200. Nothing fires. |
| Lifecycle hooks | PARTIAL | `put_lifecycle_hook` and `describe_lifecycle_hooks` work, and hooks can be set at create time. **`complete_lifecycle_action` is not implemented** (`NotImplementedError: The complete_lifecycle_action action has not been implemented`). Instances never wait in `Pending:Wait`, going straight to `InService`. Moto invents `NotificationTargetARN` `arn:aws:sqs:us-east-1:123456789012:my-queue` and `RoleARN` `arn:aws:iam::1234567890:role/my-auto-scaling-role` when none are given. |
| Instance refresh | NO | `start_instance_refresh`, `describe_instance_refreshes`, `cancel_instance_refresh`, `rollback_instance_refresh` all raise `NotImplementedError: The <action> action has not been implemented`. |
| MixedInstancesPolicy | PARTIAL | Accepted and returned verbatim (OnDemandBaseCapacity, OnDemandPercentageAboveBaseCapacity, SpotAllocationStrategy, Overrides with WeightedCapacity). **Ignored for launching**: every instance is the template's type, on-demand, no spot. With three overrides one of weight 2, Desired=4 produced only 3 instances. With a single override, 4. Weights seem to be partly honoured. Base and percentage split cannot be observed. |
| Passing both `LaunchTemplate` and `MixedInstancesPolicy` | YES (rejected) | Rejected with the unhelpful `ValidationError: Valid requests must contain either LaunchTemplate, LaunchConfigurationName, InstanceId or MixedInstancesPolicy parameter.` |
| `delete_auto_scaling_group(ForceDelete=True)` | YES | Instances end `terminated`. |

## C. ELBv2 (`c_elb.py`)

| Feature | Result | Notes |
|---|---|---|
| `create_load_balancer` ALB (internet-facing, 2 subnets, SGs, Tags) | YES | Fields: DNSName `alb-1.us-east-1.elb.amazonaws.com`, State `provisioning` (never becomes `active`), AZs derived from the subnets, VpcId, `IpAddressType: ipv4`. |
| NLB (`Type='network'`) | YES with quirks | Created, `SecurityGroups=[]`. **The ARN contains `loadbalancer/app/nlb/...` even for NLBs** (real AWS uses `net/`). Gateway type also accepted. |
| LB validation | NO | Accepted: `Scheme='bogus'`, 1 subnet, no SG, **duplicate LB name** (a second LB is created with the same name and a different ARN, no `DuplicateLoadBalancerName`). |
| `set_security_groups`, `set_subnets`, `set_ip_address_type` | YES | |
| LB attributes default (ALB and NLB identical) | YES | `access_logs.s3.bucket=''`, `access_logs.s3.prefix=''`, `deletion_protection.enabled=false`, `load_balancing.cross_zone.enabled=false`. `idle_timeout.timeout_seconds` is **not listed by default** (appears only after being set). The ALB's real defaults (`routing.http2.enabled` etc.) are absent. |
| `modify_load_balancer_attributes` incl. NLB `load_balancing.cross_zone.enabled=true` | YES | Persisted and shown by describe. An unknown key is rejected: `InvalidConfigurationRequest: Key bogus.key not valid`. |
| Deletion protection | NO | With `deletion_protection.enabled=true`, `delete_load_balancer` returned 200 and the LB was gone (AWS gives `OperationNotPermitted`). |
| `create_target_group` defaults | YES | Instance TG, HTTP/80: `HealthCheckProtocol HTTP`, `HealthCheckPort 'traffic-port'`, `HealthCheckEnabled True`, `HealthCheckIntervalSeconds 30`, `HealthCheckTimeoutSeconds 5`, `HealthyThresholdCount 5`, `UnhealthyThresholdCount 2`, `HealthCheckPath '/'`, `Matcher {'HttpCode': '200'}`, `TargetType instance`, `ProtocolVersion HTTP1`, `IpAddressType ipv4`. TCP target group: interval 30, timeout **10**, healthy 5. |
| Custom health check (`/healthz`, interval 15, `Matcher 200-299`, thresholds) | YES | `modify_target_group` also updates them. |
| TG validation | PARTIAL | Rejected client-side by botocore: interval < 5, HealthyThreshold < 2. Rejected by moto: timeout >= interval (`ValidationError: Health check timeout '20' must be smaller than the interval '10'`), duplicate TG name (`DuplicateTargetGroupName`). **Accepted**: Matcher `999`, HealthCheckPath without leading `/`. |
| TargetType ip / lambda | YES | |
| TG attribute defaults | YES | `deregistration_delay.timeout_seconds=300`, `stickiness.enabled=false`, `stickiness.type=lb_cookie`, `load_balancing.algorithm.type=round_robin`, `load_balancing.cross_zone.enabled=use_load_balancer_configuration`, `slow_start.duration_seconds=0`, `waf.fail_open.enabled=false`. |
| `modify_target_group_attributes` | PARTIAL | dereg delay, stickiness (enabled, type, `lb_cookie.duration_seconds`), `cross_zone`, `slow_start`, algorithm all persist. Range check on dereg delay works (`'deregistration_delay.timeout_seconds' value '9999' must be between '0-3600' inclusive`). **Unknown key `nope` is accepted** and echoed. |
| `register_targets` / `deregister_targets` | YES | Port override per target works. A **bogus instance id registers fine** (`i-doesnotexist`). |
| `describe_target_health` | PARTIAL | A registered target is **`healthy` immediately**, even with no listener, and regardless of the health check. It never reports `initial`, `unhealthy` or `draining`. The only other state: a **stopped instance gives `unused` / `Target.InvalidState` / "Target is in the stopped state"**. A terminated instance disappears from the list. `HealthCheckPort` is returned. |
| Listeners | YES | HTTP default forward, fixed-response (StatusCode, ContentType, MessageBody), redirect, weighted forward (ForwardConfig, TargetGroupStickinessConfig), TCP on NLB. HTTPS **without a certificate is accepted**. **Duplicate listener port is accepted** (two listeners on 80). `SslPolicy` defaults to `ELBSecurityPolicy-2016-08`. `describe_listener_attributes` gives `tcp.idle_timeout.seconds=350` even for an ALB listener. |
| `create_rule` Conditions: path-pattern, host-header, http-header, query-string, http-request-method, source-ip, multiple conditions | YES | Both the old `Values` form and the `*Config` form are echoed back as given (not normalised). `Priority` comes back as a string. |
| Rule validation | PARTIAL | Rejected: **duplicate priority** (`PriorityInUse: The specified priority is in use.`, also via `set_rule_priorities`), priority 0 (botocore min 1), unknown condition field (`ValidationError: Condition field 'bogus' must be one of '[path-pattern,host-header,http-header,http-request-method,query-string,source-ip]'`), unknown TG (`TargetGroupNotFound`). **Accepted**: priority 50001 (AWS max is 50000), **empty Conditions list**, path pattern without leading `/`. |
| `describe_rules` order | PARTIAL | Rules in **creation order** (10, 20, 30, 40, 45, 46, 50, 50001, 60, 70, 91 as created), **not sorted by priority**, and the `default` rule is last. Sort in the test. |
| `set_rule_priorities`, `modify_rule`, `delete_rule`, `describe_tags`, `describe_account_limits` (20 ALBs, 3000 TGs, 30 targets/ALB), `describe_ssl_policies` (18) | YES | |
| `delete_target_group` in use | YES | `ResourceInUse: The target group '...' is currently in use by a listener or a rule`. |
| `delete_load_balancer` removes listeners | YES | `ListenerNotFound` afterwards. |

## D. CloudFormation in moto (`net.yaml`, `compute.yaml`, `d_cfn.py`, `e_extra.py`)

Two stacks. `net` (VPC, 2 subnets via `!Select/!GetAZs`) exports `net-VpcId` and `net-SubnetIds` (`!Join`). `compute` imports them.

| Item | Result | Notes |
|---|---|---|
| Both stacks reach `CREATE_COMPLETE` | YES | |
| `Fn::ImportValue` across stacks, `!Split [",", !ImportValue net-SubnetIds]`, VPC id via `!ImportValue` | YES | ALB got both subnets, the ASG got the comma-joined `VPCZoneIdentifier`, SG and TG got the VPC id. |
| `AWS::EC2::SecurityGroup`, `AWS::IAM::Role`, `AWS::IAM::InstanceProfile` | CREATED | |
| `AWS::EC2::LaunchTemplate` | CREATED | `MetadataOptions` (HttpTokens required, hop limit 1, HttpEndpoint), `IamInstanceProfile.Name` (= the generated profile name), `SecurityGroupIds`, `ImageId`, `InstanceType` all present in `describe_launch_template_versions`. |
| `Fn::Base64` + `!Sub` UserData | YES | Stored as base64 and decodes to the text with the `${AWS::StackName}` and `${AWS::Region}` substituted. |
| `!GetAtt LT.LatestVersionNumber` | YES | Resolves to `1` in the ASG and in an Output. |
| `AWS::ElasticLoadBalancingV2::LoadBalancer` / `Listener` (fixed-response default) / `ListenerRule` | CREATED | Rule priority 10, path condition and forward action present. TG linked to the LB. |
| `AWS::ElasticLoadBalancingV2::TargetGroup` | CREATED, PARTIAL | `HealthCheckPath`, interval, Matcher applied. **`TargetGroupAttributes` are silently NOT applied**: dereg delay stayed `300` (30 requested), `stickiness.enabled` stayed `false`. Set them afterwards with `modify_target_group_attributes`. |
| `AWS::AutoScaling::AutoScalingGroup` | CREATED | 2 real instances launched, HealthCheckType ELB kept, TargetGroupARNs kept and the instances registered `healthy`. Both instances in the same AZ (no spreading, as in B). |
| **`AWS::AutoScaling::ScalingPolicy`** | **SKIPPED** | moto prints `No Moto CloudFormation support for AWS::AutoScaling::ScalingPolicy`. The stack is still `CREATE_COMPLETE`, `describe_policies` returns `[]`, and the resource is absent from `list_stack_resources`. Workaround: call `put_scaling_policy` after the stack, or check the policy as a template-only assertion (`cfn.resources(template, "AWS::AutoScaling::ScalingPolicy")`). |
| Other types skipped | SKIPPED | `AWS::AutoScaling::LifecycleHook` and `AWS::EC2::PlacementGroup` print the same "No Moto CloudFormation support" warning and are not listed in the stack resources. `AWS::AutoScaling::ScheduledAction` was listed. Not verified in the ASG. |
| Stack status with skipped types | `CREATE_COMPLETE` | Skips never fail the stack unless something `!Ref`s them. |
| `Outputs` with `!GetAtt LT.LatestVersionNumber`, `!GetAtt Alb.DNSName` | YES | `1` and `shortly-alb-1.us-east-1.elb.amazonaws.com`. |
| `update_stack` (InstanceType t3.micro to t3.small) | PARTIAL | `UPDATE_COMPLETE`, a **new LT version 2** is created and the `LatestVersionNumber` output becomes `2`. **The ASG keeps `Version: '1'`** (not re-pointed), so rolling-update behaviour cannot be shown. |
| `update_stack` with `UsePreviousValue` for an SSM-typed param | NO | `KeyError: 'ImageId'` (moto bug in `d_cfn.py`, run 1). Passing `ImageId` explicitly works. If every parameter is `UsePreviousValue` with the same template: `ValidationError: No updates are to be performed.` |
| `delete_stack` | YES | The ASG's instances end `terminated`. |
| Fn::ImportValue / Base64 / GetAtt needing a workaround | none | No `inline_functions` entry is needed for this template. The earlier `!Cidr` gap still applies. |

## E. cfn-lint 1.57.2 (`f_lint.py`, `g_lint2.py`; about 1 minute for 45 lints, roughly 1.4 s each)

A correct template (`compute.yaml`) gives **0 findings, no warnings**, in default region us-east-1.

| Probe | Result |
|---|---|
| `HttpTokens: optional` | **No rule fires**, so IMDSv2 enforcement needs a custom check (read the LT `MetadataOptions` from the template). |
| `HttpTokens: maybe` | E3030 "'maybe' is not one of ['optional', 'required']" |
| `HttpPutResponseHopLimit: 99` | no finding (the range is not checked) |
| **Duplicate ListenerRule priority** | **no finding**. Needs a custom template check. |
| ListenerRule missing `Conditions` | E3003 "'Conditions' is a required property" |
| Priority 0 / `"ten"` | E3034 "0 is less than the minimum of 1" / E3012 "'ten' is not of type 'integer'" |
| Unknown condition `Field`, path pattern without `/`, Matcher `999`, HealthCheckPath without `/` | no finding |
| TG interval 1 | E3034 "1 is less than the minimum of 5" |
| ASG MinSize 9 > MaxSize 4 | E3706 "'4' is less than the minimum of 9" and E3712 "TargetTrackingScaling policy requires the referenced AutoScalingGroup to have MaxSize greater than MinSize" |
| ASG DesiredCapacity 9 > MaxSize 4, ASG without subnets | no finding |
| `HealthCheckType: ALB` | E3031 "'ALB' does not match '^(EBS\|EC2\|ELB\|VPC_LATTICE)(,(EBS\|EC2\|ELB\|VPC_LATTICE))*,?$'" |
| Literal LT `InstanceType: m7g.large` | no finding (so t4g.small, m7i.large and c8g.large are fine too) |
| Literal LT `InstanceType: m7g.hugee` | E3628 "'m7g.hugee' is not one of ['a1.2xlarge', ...]" |
| **Region sensitivity** | None. m7g.large, t4g.small, m7i.large and c8g.large give 0 findings in us-east-1, eu-north-1 and ap-southeast-4. The instance-type list is global, so **no `regions=` argument is needed**. A bogus type passed through a Parameter *Default* is not checked at all. |
| SSM-typed ImageId parameter (arm64, x86_64, or a bogus path) | no finding. cfn-lint does not resolve or check the SSM path. |
| `${NoSuch}` in `!Sub` UserData | E1021 "'NoSuch' is not one of ['ImageId', 'InstanceType', 'WebSg', ...]" |
| `Fn::Sub` without `Fn::Base64` in UserData | no finding |
| `!GetAtt LT.Nope` | E1010 and E6101 "'Nope' is not one of ['DefaultVersionNumber', 'LaunchTemplateId', 'LatestVersionNumber']" |
| ScalingPolicy bad metric / missing `TargetValue` | E3030 "'CPU' is not one of [ALBRequestCountPerTarget, ASGAverageCPUUtilization, ASGAverageNetworkIn, ASGAverageNetworkOut]" / E3003 |
| ScalingPolicy `ALBRequestCountPerTarget` without `ResourceLabel` | no finding |
| SG ingress 22 from 0.0.0.0/0, ALB without SG | no finding (no security-opinion rules by default) |
| ALB with one subnet | E3680 "expected minimum item count: 2, found: 1" |
| Listener missing `DefaultActions` | E3003 |
| ASG with both `LaunchTemplate` and `MixedInstancesPolicy` | E3014 "Only one of ['InstanceId', 'LaunchConfigurationName', 'LaunchTemplate', 'MixedInstancesPolicy'] is a required property" (twice) |
| Correct MixedInstancesPolicy (Overrides m7g.large and t4g.small, InstancesDistribution) | 0 findings |
| PlacementGroup `Strategy: wide` | E3030 "'wide' is not one of ['cluster', 'partition', 'precision-time', 'spread']" |
| LifecycleHook, PlacementGroup (valid) | 0 findings |
| Unused parameter | W2001 "Parameter InstanceType not used." (the only warning seen) |

## F. Extra probes

| # | Question | Result |
|---|---|---|
| F1 | CFN parameter `Type: AWS::SSM::Parameter::Value<AWS::EC2::Image::Id>` with Default `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64` (and arm64) | **YES, resolved at `create_stack`.** x86_64 resolved to `ami-0006118602dfc1c09` (visible in `describe_stacks` Parameters and in the LT). arm64 resolved to `ami-04fc404d256fd34a2` (confirmed on the update run, LT v2). The AMIs exist in `describe_images`. `ssm.get_parameter` on these names also works: moto ships a built-in set of 10 parameters under `/aws/service/ami-amazon-linux-latest` (arm64 and x86_64 al2023, `al2023-ami-kernel-6.1-x86_64`, `amzn2-ami-hvm-x86_64-gp2`). cfn-lint accepts the parameter (0 findings), including a made-up path. **An unknown SSM path fails ugly**: `create_stack` raised `AttributeError: 'NoneType' object has no attribute 'value'` (not a ValidationError). |
| F2 | UserData `Fn::Base64: !Sub \|` multi-line bash with `cat > /opt/shortly/app.py <<'EOF' ... EOF` and Python with `{}` and an f-string, no `${` | **YES.** Deploys, stack `CREATE_COMPLETE`. `describe_launch_template_versions` returns base64 that decodes to the script with heredoc, quotes and f-string braces **intact**; only `${AWS::StackName}` / `${AWS::Region}` were substituted. Note that `{{literal}}` is untouched because only `${` is special in `Fn::Sub`. A literal `${` would need `${!`. |
| F3 | `describe_instances` for ASG-launched instances: LT id/version, IamInstanceProfile, HttpTokens | **LT id/version: YES**, as tags `aws:ec2launchtemplate:id` and `aws:ec2launchtemplate:version` (version resolved to a number) plus `aws:autoscaling:groupName`. **IamInstanceProfile: NO** (`None`). **MetadataOptions.HttpTokens: NO** (`optional`, though the template says `required`). The same holds for plain `run_instances(LaunchTemplate=...)` and when the template comes from CloudFormation. The template data itself (`describe_launch_template_versions`) is correct, so assert IMDSv2 and the profile on the **launch template**, not on instances. |

## What the plan can rely on
- Launch templates: create, versions (pass full data each time), `$Latest`/`$Default`, default-version change, and reading back MetadataOptions, IamInstanceProfile, UserData (base64) and SGs from `describe_launch_template_versions`.
- Instance types: m7g/t4g/c7g/t3/m5 with vCPU, memory and architecture via `describe_instance_types`, and the arm64 filter. Spot request APIs return fake but well-shaped data.
- `run_instances(MetadataOptions=...)` directly and `modify_instance_metadata_options`.
- ASG create/update/delete, field round-trips, `describe_auto_scaling_instances`, `set_desired_capacity`, `execute_policy`, policy storage (target tracking, step, simple), lifecycle hook storage, `attach_load_balancer_target_groups`, and automatic target-group registration.
- ELBv2: ALB/NLB creation, listeners of every action type, rules of every condition type with duplicate-priority errors, target-group defaults and attributes (with the NLB cross-zone attribute), register/deregister, and the stopped-instance `unused` state.
- CloudFormation: LT, ALB, TG, Listener, ListenerRule, ASG, SG, IAM Role and InstanceProfile deploy to `CREATE_COMPLETE`; `ImportValue` with `Split`; `Base64` with `Sub` (including the heredoc UserData); `!GetAtt LT.LatestVersionNumber`; SSM-typed parameters with the built-in AMI names.
- cfn-lint: 0 findings on a correct template; catches required properties, enums (HttpTokens, HealthCheckType, instance types, metrics), integer minimums, mutually exclusive ASG properties, `Sub` variables and `GetAtt` attributes. No region argument is needed.

## Must be modelled in pure Python instead
- AZ balancing and rebalancing across subnets (moto puts everything in one AZ).
- Which launch-template settings (HttpTokens, instance profile) reach the instance; assert on the template data instead.
- Placement groups (cluster, spread with the 7-per-AZ limit, partition); `create_placement_group` is not implemented.
- Health: ELB health checks, grace period, replacement of unhealthy instances, and target states `initial`, `unhealthy`, `draining`.
- Scaling decisions: target tracking, step and simple policy maths, cooldown and warm-up, CloudWatch alarm linkage, scheduled actions, and min/max/desired clamping (moto accepts out-of-range values).
- Instance refresh (unimplemented), lifecycle hook waits and `complete_lifecycle_action` (unimplemented), warm pool behaviour.
- MixedInstancesPolicy capacity split (on-demand base, percentage above base, spot allocation, override choice).
- Spot price history, spot interruption and fleet behaviour.
- Deletion protection, duplicate LB names or listener ports, and stricter rule validation (priority above 50000, empty conditions, path pattern format) beyond what moto catches.
- `AWS::AutoScaling::ScalingPolicy`, `AWS::AutoScaling::LifecycleHook`, `AWS::EC2::PlacementGroup` in CloudFormation (skipped by moto), `TargetGroupAttributes` in CFN (ignored), and re-pointing the ASG to a new LT version on `update_stack`: check these on the rendered template with `cfn.resources(...)` instead of the deployed state.
- Checks cfn-lint lacks: IMDSv2 enforcement, duplicate rule priorities within a listener, desired > max, hop-limit range, ALB `ResourceLabel` presence. These need small template-level assertions in the harness.

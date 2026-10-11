"""Wrong versions of the M03 snapshot — exact text edits applied to a copy of course_project/solutions/m03."""
COMPUTE = "infra/compute.yaml"
HEALTHZ_RULE = """  HealthzRule:
    Type: AWS::ElasticLoadBalancingV2::ListenerRule
    Properties:
      ListenerArn: !Ref HttpListener
      Priority: 10
      Conditions:
        - {Field: path-pattern, PathPatternConfig: {Values: [/healthz]}}
      Actions:
        - Type: fixed-response
          FixedResponseConfig: {StatusCode: '404', ContentType: text/plain, MessageBody: not found}

"""
HTTPS_LISTENER = """  HttpsListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      LoadBalancerArn: !Ref LoadBalancer
      Port: 443
      Protocol: HTTPS
      Certificates:
        - CertificateArn: arn:aws:acm:us-east-1:111122223333:certificate/12345678-1234-1234-1234-123456789012
      DefaultActions:
        - {Type: forward, TargetGroupArn: !Ref AppTargetGroup}

"""
MUTANTS = [
    {"id": "imdsv1-allowed", "edits": {COMPUTE: [["HttpTokens: required", "HttpTokens: optional"]]}},
    {"id": "hop-limit-3", "edits": {COMPUTE: [["HttpPutResponseHopLimit: 1", "HttpPutResponseHopLimit: 3"]]}},
    {"id": "ec2-health-checks", "edits": {COMPUTE: [["HealthCheckType: ELB", "HealthCheckType: EC2"]]}},
    {"id": "x86-type-allowed", "edits": {COMPUTE: [["AllowedValues: [t4g.small, t4g.medium, m7g.large, c7g.large]",
                                                    "AllowedValues: [t4g.small, t4g.medium, m7g.large, c7g.large, m7i.large]"]]}},
    {"id": "ssh-key", "edits": {COMPUTE: [["        InstanceType: !Ref InstanceType\n", "        InstanceType: !Ref InstanceType\n        KeyName: shortly\n"]]}},
    {"id": "prod-single-instance", "edits": {COMPUTE: [["MinSize: !If [IsProd, 2, 1]", "MinSize: !If [IsProd, 1, 1]"]]}},
    {"id": "healthz-public", "edits": {COMPUTE: [[HEALTHZ_RULE, ""]]}},
    {"id": "scale-at-95-percent", "edits": {COMPUTE: [["TargetValue: 50", "TargetValue: 95"]]}},
    {"id": "app-not-inlined", "edits": {COMPUTE: [["            LINKS = {}\n", ""]]}},
    {"id": "drain-300", "edits": {COMPUTE: [["Value: '30'}", "Value: '300'}"]]}},
    {"id": "https-too-early", "edits": {COMPUTE: [["  HealthzRule:\n", HTTPS_LISTENER + "  HealthzRule:\n"]]}},
    {"id": "duplicate-priority", "edits": {COMPUTE: [["Priority: 20", "Priority: 10"]]}},
    {"id": "grace-period-zero", "edits": {COMPUTE: [["HealthCheckGracePeriod: 120", "HealthCheckGracePeriod: 0"]]}},
    {"id": "service-not-enabled", "edits": {COMPUTE: [["            systemctl enable --now shortly\n", "            systemctl start shortly\n"]]}},
]

"""Wrong versions of the M01 snapshot — exact text edits applied to a copy of course_project/solutions/m01."""
MUTANTS = [
    {"id": "app-s3-star", "edits": {"infra/iam.yaml": [["Action: [s3:GetObject, s3:PutObject]", "Action: 's3:*'"]]}},
    {"id": "auditor-12-hours", "edits": {"infra/iam.yaml": [["MaxSessionDuration: 3600", "MaxSessionDuration: 43200"]]}},
    {"id": "boundary-key-typo", "edits": {"infra/iam.yaml": [["'iam:PermissionsBoundary': !Sub", "'iam:PermissionBoundary': !Sub"]]}},
    {"id": "metrics-any-namespace", "edits": {"infra/iam.yaml": [["StringEquals: {'cloudwatch:namespace': Shortly}",
                                                                 "StringLike: {'cloudwatch:namespace': '*'}"]]}},
    {"id": "consumer-sends", "edits": {"infra/iam.yaml": [["Action: [sqs:ReceiveMessage, sqs:DeleteMessage, sqs:GetQueueAttributes]",
                                                          "Action: [sqs:SendMessage]"]]}},
    {"id": "no-params", "delete": ["params/prod.json"]},
]

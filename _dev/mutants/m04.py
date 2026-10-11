"""Wrong versions of the M04 snapshot — exact text edits applied to a copy of course_project/solutions/m04."""
STORAGE = "infra/storage.yaml"
TLS_DENY = """          - Sid: DenyInsecureTransport
            Effect: Deny
            Principal: '*'
            Action: 's3:*'
            Resource:
              - !GetAtt AssetsBucket.Arn
              - !Sub '${AssetsBucket.Arn}/*'
            Condition:
              Bool: {'aws:SecureTransport': 'false'}
"""
PUBLIC_READ = """          - Sid: PublicRead
            Effect: Allow
            Principal: '*'
            Action: s3:GetObject
            Resource: !Sub '${AssetsBucket.Arn}/*'
"""
NONCURRENT = """            NoncurrentVersionExpiration:
              NoncurrentDays: 30
              NewerNoncurrentVersions: 3
"""
KMS_BPA = "SSEAlgorithm: aws:kms\n      PublicAccessBlockConfiguration:\n        BlockPublicAcls: true\n        BlockPublicPolicy: true"
MUTANTS = [
    {"id": "versioning-suspended", "edits": {STORAGE: [["        Status: Enabled\n      BucketEncryption", "        Status: Suspended\n      BucketEncryption"]]}},
    {"id": "bpa-off", "edits": {STORAGE: [[KMS_BPA, KMS_BPA.replace("BlockPublicPolicy: true", "BlockPublicPolicy: false")]]}},
    {"id": "sse-s3-on-assets", "edits": {STORAGE: [["SSEAlgorithm: aws:kms", "SSEAlgorithm: AES256"]]}},
    {"id": "no-bucket-key", "edits": {STORAGE: [["          - BucketKeyEnabled: true\n            ServerSideEncryptionByDefault:", "          - ServerSideEncryptionByDefault:"]]}},
    {"id": "http-allowed", "edits": {STORAGE: [[TLS_DENY, ""]]}},
    {"id": "tls-deny-objects-only", "edits": {STORAGE: [["              - !GetAtt AssetsBucket.Arn\n              - !Sub '${AssetsBucket.Arn}/*'\n", "              - !Sub '${AssetsBucket.Arn}/*'\n"]]}},
    {"id": "public-read", "edits": {STORAGE: [["          - Sid: AllowAppUploads\n", PUBLIC_READ + "          - Sid: AllowAppUploads\n"]]}},
    {"id": "app-role-everything", "edits": {STORAGE: [["Resource: !Sub '${AssetsBucket.Arn}/uploads/*'", "Resource: !Sub '${AssetsBucket.Arn}/*'"]]}},
    {"id": "noncurrent-forever", "edits": {STORAGE: [[NONCURRENT, ""]]}},
    {"id": "keep-50-versions", "edits": {STORAGE: [["NewerNoncurrentVersions: 3", "NewerNoncurrentVersions: 50"]]}},
    {"id": "no-multipart-cleanup-assets", "edits": {STORAGE: [["              NewerNoncurrentVersions: 3\n            AbortIncompleteMultipartUpload:\n              DaysAfterInitiation: 7\n", "              NewerNoncurrentVersions: 3\n"]]}},
    {"id": "logs-kms", "edits": {STORAGE: [["              SSEAlgorithm: AES256", "              SSEAlgorithm: aws:kms"]]}},
    {"id": "logs-never-expire", "edits": {STORAGE: [["            ExpirationInDays: !If [IsProd, 730, 365]\n", ""]]}},
    {"id": "lab-expires-too-early", "edits": {STORAGE: [["!If [IsProd, 730, 365]", "!If [IsProd, 730, 200]"]]}},
    {"id": "ia-after-glacier", "edits": {STORAGE: [["{StorageClass: STANDARD_IA, TransitionInDays: 30}", "{StorageClass: STANDARD_IA, TransitionInDays: 120}"]]}},
    {"id": "elb-anywhere", "edits": {STORAGE: [["Resource: !Sub '${LogsBucket.Arn}/alb/AWSLogs/${AWS::AccountId}/*'", "Resource: !Sub '${LogsBucket.Arn}/*'"]]}},
    {"id": "no-retain", "edits": {STORAGE: [["    DeletionPolicy: Retain\n", ""]]}},
    {"id": "no-update-replace-retain", "edits": {STORAGE: [["    UpdateReplacePolicy: Retain\n", ""]]}},
    {"id": "ownership-acls-allowed", "edits": {STORAGE: [["          - ObjectOwnership: BucketOwnerEnforced\n      LifecycleConfiguration:\n        Rules:\n          - Id: noncurrent", "          - ObjectOwnership: BucketOwnerPreferred\n      LifecycleConfiguration:\n        Rules:\n          - Id: noncurrent"]]}},
    {"id": "logs-prefix-missing", "edits": {STORAGE: [["            Prefix: alb/\n", ""]]}},
]

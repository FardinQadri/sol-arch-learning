# AWS SAA-C03 course research (fetched 2026-10-08)

All facts below were fetched on 2026-10-08 from the URLs shown. Items marked "unconfirmed" could not be verified from an official AWS source.

---

## 1. Exam status

**Conclusion: SAA-C03 is still the current Solutions Architect - Associate exam as of 2026-10-08. No official AWS announcement of a successor (SAA-C04) or a retirement date for SAA-C03 was found.**

Evidence:
- The official certification page (fetched live today) lists the exam as "AWS Certified Solutions Architect - Associate", 130 minutes, 65 questions, 150 USD, and links to `https://skillbuilder.aws/category/exam-prep/solutions-architect-associate-SAA-C03`. It mentions no successor. Source: https://aws.amazon.com/certification/certified-solutions-architect-associate/
- The same page says: "The AWS Certified Solutions Architect - Associate exam in Italian will be retired after December 31, 2026." This is a language retirement, not an exam retirement. Languages offered: English, French (France), Italian, Japanese, Korean, Portuguese (Brazil), Spanish (Latin America), Spanish (Spain), Simplified Chinese, Traditional Chinese. Testing: Pearson VUE center or online proctored.
- The same page says the exam uses short names for some AWS services and a list of short and full names will be available via the Help button in the exam.
- The official "Coming soon / exam updates" page lists only the SysOps Administrator to CloudOps Engineer - Associate (SOA-C03) update. It has no entry for Solutions Architect - Associate. Source: https://aws.amazon.com/certification/coming-soon/
- The official PDF exam guide is "Version 1.1 SAA-C03". Source: https://d1.awsstatic.com/training-and-certification/docs-sa-assoc/AWS-Certified-Solutions-Architect-Associate_Exam-Guide.pdf
- Third-party claims found by web search are contradictory and unsupported by AWS links: one blog says SAA-C04 launched in March 2024, another says a C04 rollout is planned for Q2-Q3 2026 with a 30 Sep 2026 grace period. Neither appears on AWS pages. Treat both as unreliable. Sources of the claims (do not rely on them): https://www.citadelcloudmanagement.com/blogs/news/aws-saa-c04-exam-guide-2026-format-domains-and-pass-score and https://jayendrapatil.com/tag/saa-c03/
- Caveat: AWS has updated other associate exams with only about 3-4 weeks of notice on the Coming-soon page (SOA-C02 to SOA-C03 had registration open 2025-09-09). A course should keep exam-guide-version-specific content separable and tell learners to re-check the cert page before booking.

---

## 2. Official SAA-C03 exam guide (verbatim from the official PDF)

Source of everything in this section: https://d1.awsstatic.com/training-and-certification/docs-sa-assoc/AWS-Certified-Solutions-Architect-Associate_Exam-Guide.pdf (Version 1.1 SAA-C03, 23 pages; text extracted with pdftotext on 2026-10-08). The docs-site version `https://docs.aws.amazon.com/aws-certification/latest/examguides/solutions-architect-associate-03.html` was not needed because the PDF is complete (not independently diffed against the docs site; unconfirmed that they are identical).

### 2.1 Exam format

| Item | Value | Source |
|---|---|---|
| Target candidate | At least 1 year of hands-on experience designing cloud solutions that use AWS services | PDF p.1 |
| Question types | Multiple choice: one correct response and three distractors. Multiple response: two or more correct responses out of five or more options | PDF p.1 |
| Number of questions | 65 total: 50 scored + 15 unscored (unscored are not identified) | PDF p.2; cert page for the 65 total |
| Scoring | Unanswered = incorrect; no penalty for guessing. Compensatory model: no per-section pass needed, only overall | PDF p.2 |
| Result | Pass/fail; scaled score 100-1,000; minimum passing score 720 | PDF p.2 |
| Duration | 130 minutes | https://aws.amazon.com/certification/certified-solutions-architect-associate/ |
| Cost | 150 USD (plus local taxes/FX per exam pricing page) | same cert page |

### 2.2 Domains and weightings (verbatim)

- Domain 1: Design Secure Architectures (30% of scored content)
- Domain 2: Design Resilient Architectures (26% of scored content)
- Domain 3: Design High-Performing Architectures (24% of scored content)
- Domain 4: Design Cost-Optimized Architectures (20% of scored content)

Counts: 14 task statements (D1: 3, D2: 2, D3: 5, D4: 4).

### 2.3 Task statements with Knowledge of / Skills in (verbatim; bullets re-joined from PDF line wraps)

#### Domain 1: Design Secure Architectures

##### Task Statement 1.1: Design secure access to AWS resources.

**Knowledge of:**
- Access controls and management across multiple accounts
- AWS federated access and identity services (for example, AWS Identity and Access Management [IAM], AWS IAM Identity Center [AWS Single Sign-On])
- AWS global infrastructure (for example, Availability Zones, AWS Regions)
- AWS security best practices (for example, the principle of least privilege)
- The AWS shared responsibility model

**Skills in:**
- Applying AWS security best practices to IAM users and root users (for example, multi-factor authentication [MFA])
- Designing a flexible authorization model that includes IAM users, groups, roles, and policies
- Designing a role-based access control strategy (for example, AWS Security Token Service [AWS STS], role switching, cross-account access)
- Designing a security strategy for multiple AWS accounts (for example, AWS Control Tower, service control policies [SCPs])
- Determining the appropriate use of resource policies for AWS services
- Determining when to federate a directory service with IAM roles

##### Task Statement 1.2: Design secure workloads and applications.

**Knowledge of:**
- Application configuration and credentials security
- AWS service endpoints
- Control ports, protocols, and network traffic on AWS
- Secure application access

- Security services with appropriate use cases (for example, Amazon Cognito, Amazon GuardDuty, Amazon Macie)

- Threat vectors external to AWS (for example, DDoS, SQL injection)

**Skills in:**
- Designing VPC architectures with security components (for example, security groups, route tables, network ACLs, NAT gateways)
- Determining network segmentation strategies (for example, using public subnets and private subnets)
- Integrating AWS services to secure applications (for example, AWS Shield, AWS WAF, IAM Identity Center, AWS Secrets Manager)
- Securing external network connections to and from the AWS Cloud (for example, VPN, AWS Direct Connect)

##### Task Statement 1.3: Determine appropriate data security controls.

**Knowledge of:**
- Data access and governance
- Data recovery
- Data retention and classification
- Encryption and appropriate key management

**Skills in:**
- Aligning AWS technologies to meet compliance requirements
- Encrypting data at rest (for example, AWS Key Management Service [AWS KMS])
- Encrypting data in transit (for example, AWS Certificate Manager [ACM] using TLS)
- Implementing access policies for encryption keys
- Implementing data backups and replications
- Implementing policies for data access, lifecycle, and protection
- Rotating encryption keys and renewing certificates

#### Domain 2: Design Resilient Architectures

##### Task Statement 2.1: Design scalable and loosely coupled architectures.

**Knowledge of:**
- API creation and management (for example, Amazon API Gateway, REST API)
- AWS managed services with appropriate use cases (for example, AWS Transfer Family, Amazon Simple Queue Service [Amazon SQS], Secrets Manager)
- Caching strategies
- Design principles for microservices (for example, stateless workloads compared with stateful workloads)
- Event-driven architectures
- Horizontal scaling and vertical scaling
- How to appropriately use edge accelerators (for example, content delivery network [CDN])
- How to migrate applications into containers
- Load balancing concepts (for example, Application Load Balancer)
- Multi-tier architectures
- Queuing and messaging concepts (for example, publish/subscribe)
- Serverless technologies and patterns (for example, AWS Fargate, AWS Lambda)
- Storage types with associated characteristics (for example, object, file, block)
- The orchestration of containers (for example, Amazon Elastic Container Service [Amazon ECS], Amazon Elastic Kubernetes Service [Amazon EKS])
- When to use read replicas
- Workflow orchestration (for example, AWS Step Functions)

**Skills in:**
- Designing event-driven, microservice, and/or multi-tier architectures based on requirements
- Determining scaling strategies for components used in an architecture design
- Determining the AWS services required to achieve loose coupling based on requirements
- Determining when to use containers
- Determining when to use serverless technologies and patterns
- Recommending appropriate compute, storage, networking, and database technologies based on requirements
- Using purpose-built AWS services for workloads

##### Task Statement 2.2: Design highly available and/or fault-tolerant architectures.

**Knowledge of:**
- AWS global infrastructure (for example, Availability Zones, AWS Regions, Amazon Route 53)
- AWS managed services with appropriate use cases (for example, Amazon Comprehend, Amazon Polly)
- Basic networking concepts (for example, route tables)
- Disaster recovery (DR) strategies (for example, backup and restore, pilot light, warm standby, active-active failover, recovery point objective [RPO], recovery time objective [RTO])
- Distributed design patterns
- Failover strategies
- Immutable infrastructure
- Load balancing concepts (for example, Application Load Balancer)
- Proxy concepts (for example, Amazon RDS Proxy)
- Service quotas and throttling (for example, how to configure the service quotas for a workload in a standby environment)
- Storage options and characteristics (for example, durability, replication)
- Workload visibility (for example, AWS X-Ray)

**Skills in:**
- Determining automation strategies to ensure infrastructure integrity
- Determining the AWS services required to provide a highly available and/or fault-tolerant architecture across AWS Regions or Availability Zones
- Identifying metrics based on business requirements to deliver a highly available solution
- Implementing designs to mitigate single points of failure
- Implementing strategies to ensure the durability and availability of data (for example, backups)
- Selecting an appropriate DR strategy to meet business requirements
- Using AWS services that improve the reliability of legacy applications and applications not built for the cloud (for example, when application changes are not possible)
- Using purpose-built AWS services for workloads

#### Domain 3: Design High-Performing Architectures

##### Task Statement 3.1: Determine high-performing and/or scalable storage solutions.

**Knowledge of:**
- Hybrid storage solutions to meet business requirements
- Storage services with appropriate use cases (for example, Amazon S3, Amazon Elastic File System [Amazon EFS], Amazon Elastic Block Store [Amazon EBS])
- Storage types with associated characteristics (for example, object, file, block)

**Skills in:**
- Determining storage services and configurations that meet performance demands
- Determining storage services that can scale to accommodate future needs

##### Task Statement 3.2: Design high-performing and elastic compute solutions.

**Knowledge of:**
- AWS compute services with appropriate use cases (for example, AWS Batch, Amazon EMR, Fargate)

- Distributed computing concepts supported by AWS global infrastructure and edge services

- Queuing and messaging concepts (for example, publish/subscribe)
- Scalability capabilities with appropriate use cases (for example, Amazon EC2 Auto Scaling, AWS Auto Scaling)
- Serverless technologies and patterns (for example, Lambda, Fargate)
- The orchestration of containers (for example, Amazon ECS, Amazon EKS)

**Skills in:**
- Decoupling workloads so that components can scale independently
- Identifying metrics and conditions to perform scaling actions
- Selecting the appropriate compute options and features (for example, EC2 instance types) to meet business requirements
- Selecting the appropriate resource type and size (for example, the amount of Lambda memory) to meet business requirements

##### Task Statement 3.3: Determine high-performing database solutions.

**Knowledge of:**
- AWS global infrastructure (for example, Availability Zones, AWS Regions)
- Caching strategies and services (for example, Amazon ElastiCache)
- Data access patterns (for example, read-intensive compared with write- intensive)
- Database capacity planning (for example, capacity units, instance types, Provisioned IOPS)
- Database connections and proxies
- Database engines with appropriate use cases (for example, heterogeneous migrations, homogeneous migrations)
- Database replication (for example, read replicas)
- Database types and services (for example, serverless, relational compared with non-relational, in-memory)

**Skills in:**
- Configuring read replicas to meet business requirements
- Designing database architectures

- Determining an appropriate database engine (for example, MySQL compared with PostgreSQL)

- Determining an appropriate database type (for example, Amazon Aurora, Amazon DynamoDB)

- Integrating caching to meet business requirements

##### Task Statement 3.4: Determine high-performing and/or scalable network architectures.

**Knowledge of:**
- Edge networking services with appropriate use cases (for example, Amazon CloudFront, AWS Global Accelerator)
- How to design network architecture (for example, subnet tiers, routing, IP addressing)
- Load balancing concepts (for example, Application Load Balancer)
- Network connection options (for example, AWS VPN, Direct Connect, AWS PrivateLink)

**Skills in:**
- Creating a network topology for various architectures (for example, global, hybrid, multi-tier)
- Determining network configurations that can scale to accommodate future needs
- Determining the appropriate placement of resources to meet business requirements
- Selecting the appropriate load balancing strategy

##### Task Statement 3.5: Determine high-performing data ingestion and transformation solutions.

**Knowledge of:**
- Data analytics and visualization services with appropriate use cases (for example, Amazon Athena, AWS Lake Formation, Amazon QuickSight)
- Data ingestion patterns (for example, frequency)
- Data transfer services with appropriate use cases (for example, AWS DataSync, AWS Storage Gateway)

- Data transformation services with appropriate use cases (for example, AWS Glue)

- Secure access to ingestion access points
- Sizes and speeds needed to meet business requirements
- Streaming data services with appropriate use cases (for example, Amazon Kinesis)

**Skills in:**
- Building and securing data lakes
- Designing data streaming architectures
- Designing data transfer solutions
- Implementing visualization strategies
- Selecting appropriate compute options for data processing (for example, Amazon EMR)
- Selecting appropriate configurations for ingestion
- Transforming data between formats (for example, .csv to .parquet)

#### Domain 4: Design Cost-Optimized Architectures

##### Task Statement 4.1: Design cost-optimized storage solutions.

**Knowledge of:**
- Access options (for example, an S3 bucket with Requester Pays object storage)
- AWS cost management service features (for example, cost allocation tags, multi-account billing)
- AWS cost management tools with appropriate use cases (for example, AWS Cost Explorer, AWS Budgets, AWS Cost and Usage Report)
- AWS storage services with appropriate use cases (for example, Amazon FSx, Amazon EFS, Amazon S3, Amazon EBS)
- Backup strategies
- Block storage options (for example, hard disk drive [HDD] volume types, solid state drive [SSD] volume types)
- Data lifecycles
- Hybrid storage options (for example, DataSync, Transfer Family, Storage Gateway)

- Storage access patterns
- Storage tiering (for example, cold tiering for object storage)
- Storage types with associated characteristics (for example, object, file, block)

**Skills in:**
- Designing appropriate storage strategies (for example, batch uploads to Amazon S3 compared with individual uploads)
- Determining the correct storage size for a workload
- Determining the lowest cost method of transferring data for a workload to AWS storage
- Determining when storage auto scaling is required
- Managing S3 object lifecycles
- Selecting the appropriate backup and/or archival solution
- Selecting the appropriate service for data migration to storage services
- Selecting the appropriate storage tier
- Selecting the correct data lifecycle for storage
- Selecting the most cost-effective storage service for a workload

##### Task Statement 4.2: Design cost-optimized compute solutions.

**Knowledge of:**
- AWS cost management service features (for example, cost allocation tags, multi-account billing)
- AWS cost management tools with appropriate use cases (for example, Cost Explorer, AWS Budgets, AWS Cost and Usage Report)
- AWS global infrastructure (for example, Availability Zones, AWS Regions)
- AWS purchasing options (for example, Spot Instances, Reserved Instances, Savings Plans)
- Distributed compute strategies (for example, edge processing)
- Hybrid compute options (for example, AWS Outposts, AWS Snowball Edge)
- Instance types, families, and sizes (for example, memory optimized, compute optimized, virtualization)
- Optimization of compute utilization (for example, containers, serverless computing, microservices)
- Scaling strategies (for example, auto scaling, hibernation)

**Skills in:**
- Determining an appropriate load balancing strategy (for example, Application Load Balancer [Layer 7] compared with Network Load Balancer [Layer 4] compared with Gateway Load Balancer)
- Determining appropriate scaling methods and strategies for elastic workloads (for example, horizontal compared with vertical, EC2 hibernation)
- Determining cost-effective AWS compute services with appropriate use cases (for example, Lambda, Amazon EC2, Fargate)
- Determining the required availability for different classes of workloads (for example, production workloads, non-production workloads)
- Selecting the appropriate instance family for a workload
- Selecting the appropriate instance size for a workload

##### Task Statement 4.3: Design cost-optimized database solutions.

**Knowledge of:**
- AWS cost management service features (for example, cost allocation tags, multi-account billing)
- AWS cost management tools with appropriate use cases (for example, Cost Explorer, AWS Budgets, AWS Cost and Usage Report)
- Caching strategies
- Data retention policies
- Database capacity planning (for example, capacity units)
- Database connections and proxies
- Database engines with appropriate use cases (for example, heterogeneous migrations, homogeneous migrations)
- Database replication (for example, read replicas)
- Database types and services (for example, relational compared with non- relational, Aurora, DynamoDB)

**Skills in:**
- Designing appropriate backup and retention policies (for example, snapshot frequency)
- Determining an appropriate database engine (for example, MySQL compared with PostgreSQL)

- Determining cost-effective AWS database services with appropriate use cases (for example, DynamoDB compared with Amazon RDS, serverless)

- Determining cost-effective AWS database types (for example, time series format, columnar format)

- Migrating database schemas and data to different locations and/or different database engines

##### Task Statement 4.4: Design cost-optimized network architectures.

**Knowledge of:**
- AWS cost management service features (for example, cost allocation tags, multi-account billing)
- AWS cost management tools with appropriate use cases (for example, Cost Explorer, AWS Budgets, AWS Cost and Usage Report)
- Load balancing concepts (for example, Application Load Balancer)
- NAT gateways (for example, NAT instance costs compared with NAT gateway costs)
- Network connectivity (for example, private lines, dedicated lines, VPNs)
- Network routing, topology, and peering (for example, AWS Transit Gateway, VPC peering)
- Network services with appropriate use cases (for example, DNS)

**Skills in:**
- Configuring appropriate NAT gateway types for a network (for example, a single shared NAT gateway compared with NAT gateways for each Availability Zone)
- Configuring appropriate network connections (for example, Direct Connect compared with VPN compared with internet)
- Configuring appropriate network routes to minimize network transfer costs (for example, Region to Region, Availability Zone to Availability Zone, private to public, Global Accelerator, VPC endpoints)
- Determining strategic needs for content delivery networks (CDNs) and edge caching
- Reviewing existing workloads for network optimizations
- Selecting an appropriate throttling strategy

- Selecting the appropriate bandwidth allocation for a network device (for example, a single VPN compared with multiple VPNs, Direct Connect speed)


### 2.4 Appendix (verbatim from the PDF; the in-scope and out-of-scope lists are marked "non-exhaustive and subject to change" by AWS)

Course-design warning: the in-scope list is the 2022-era guide and still names services AWS has since retired or closed (for example AWS Data Pipeline, Amazon QLDB, Amazon Elastic Transcoder, AWS Proton, Amazon Forecast, AWS Snow Family, Amazon Pinpoint, AWS Application Discovery Service, AWS Migration Hub; see section 4). The out-of-scope list includes AWS Cloud9, AWS CodeCommit, AWS OpsWorks, AWS App Mesh and Amazon Lookout services. The exam guide has NOT been revised to remove them.

Appendix

###### Technologies and concepts that might appear on the exam

The following list contains technologies and concepts that might appear on the exam.
This list is non-exhaustive and is subject to change. The order and placement of the
items in this list is no indication of their relative weight or importance on the exam:

- Compute
- Cost management
- Database
- Disaster recovery
- High performance
- Management and governance
- Microservices and component delivery
- Migration and data transfer
- Networking, connectivity, and content delivery
- Resiliency
- Security
- Serverless and event-driven design principles
- Storage

###### In-scope AWS services and features

The following list contains AWS services and features that are in scope for the exam.
This list is non-exhaustive and is subject to change. AWS offerings appear in
categories that align with the offerings' primary functions:

**Analytics:**
- Amazon Athena
- AWS Data Exchange
- AWS Data Pipeline
- Amazon EMR
- AWS Glue
- Amazon Kinesis
- AWS Lake Formation
- Amazon Managed Streaming for Apache Kafka (Amazon MSK)

- Amazon OpenSearch Service
- Amazon QuickSight
- Amazon Redshift

**Application Integration:**
- Amazon AppFlow
- AWS AppSync
- Amazon EventBridge
- Amazon MQ
- Amazon Simple Notification Service (Amazon SNS)
- Amazon Simple Queue Service (Amazon SQS)
- AWS Step Functions

**AWS Cost Management:**
- AWS Budgets
- AWS Cost and Usage Report
- AWS Cost Explorer
- Savings Plans

**Compute:**
- AWS Batch
- Amazon EC2
- Amazon EC2 Auto Scaling
- AWS Elastic Beanstalk
- AWS Outposts
- AWS Serverless Application Repository
- VMware Cloud on AWS
- AWS Wavelength

**Containers:**
- Amazon ECS Anywhere
- Amazon EKS Anywhere
- Amazon EKS Distro
- Amazon Elastic Container Registry (Amazon ECR)

- Amazon Elastic Container Service (Amazon ECS)
- Amazon Elastic Kubernetes Service (Amazon EKS)

**Database:**
- Amazon Aurora
- Amazon Aurora Serverless
- Amazon DocumentDB (with MongoDB compatibility)
- Amazon DynamoDB
- Amazon ElastiCache
- Amazon Keyspaces (for Apache Cassandra)
- Amazon Neptune
- Amazon Quantum Ledger Database (Amazon QLDB)
- Amazon RDS
- Amazon Redshift

**Developer Tools:**
- AWS X-Ray

**Front-End Web and Mobile:**
- AWS Amplify
- Amazon API Gateway
- AWS Device Farm
- Amazon Pinpoint

**Machine Learning:**
- Amazon Comprehend
- Amazon Forecast
- Amazon Fraud Detector
- Amazon Kendra
- Amazon Lex
- Amazon Polly
- Amazon Rekognition
- Amazon SageMaker
- Amazon Textract

- Amazon Transcribe
- Amazon Translate

**Management and Governance:**
- AWS Auto Scaling
- AWS CloudFormation
- AWS CloudTrail
- Amazon CloudWatch
- AWS Command Line Interface (AWS CLI)
- AWS Compute Optimizer
- AWS Config
- AWS Control Tower
- AWS Health Dashboard
- AWS License Manager
- Amazon Managed Grafana
- Amazon Managed Service for Prometheus
- AWS Management Console
- AWS Organizations
- AWS Proton
- AWS Service Catalog
- AWS Systems Manager
- AWS Trusted Advisor
- AWS Well-Architected Tool

**Media Services:**
- Amazon Elastic Transcoder
- Amazon Kinesis Video Streams

**Migration and Transfer:**
- AWS Application Discovery Service
- AWS Application Migration Service
- AWS Database Migration Service (AWS DMS)
- AWS DataSync
- AWS Migration Hub

- AWS Snow Family
- AWS Transfer Family

**Networking and Content Delivery:**
- AWS Client VPN
- Amazon CloudFront
- AWS Direct Connect
- Elastic Load Balancing (ELB)
- AWS Global Accelerator
- AWS PrivateLink
- Amazon Route 53
- AWS Site-to-Site VPN
- AWS Transit Gateway
- Amazon VPC

**Security, Identity, and Compliance:**
- AWS Artifact
- AWS Audit Manager
- AWS Certificate Manager (ACM)
- AWS CloudHSM
- Amazon Cognito
- Amazon Detective
- AWS Directory Service
- AWS Firewall Manager
- Amazon GuardDuty
- AWS IAM Identity Center (AWS Single Sign-On)
- AWS Identity and Access Management (IAM)
- Amazon Inspector
- AWS Key Management Service (AWS KMS)
- Amazon Macie
- AWS Network Firewall
- AWS Resource Access Manager (AWS RAM)
- AWS Secrets Manager

- AWS Security Hub
- AWS Shield
- AWS WAF

**Serverless:**
- AWS AppSync
- AWS Fargate
- AWS Lambda

**Storage:**
- AWS Backup
- Amazon Elastic Block Store (Amazon EBS)
- Amazon Elastic File System (Amazon EFS)
- Amazon FSx (for all types)
- Amazon S3
- Amazon S3 Glacier
- AWS Storage Gateway

###### Out-of-scope AWS services and features
The following list contains AWS services and features that are out of scope for the
exam. This list is non-exhaustive and is subject to change. AWS offerings that are
entirely unrelated to the target job roles for the exam are excluded from this list:

**Analytics:**
- Amazon CloudSearch

**Application Integration:**
- Amazon Managed Workflows for Apache Airflow (Amazon MWAA)

**AR and VR:**
- Amazon Sumerian

**Blockchain:**
- Amazon Managed Blockchain

**Compute:**
- Amazon Lightsail

**Database:**
- Amazon RDS on VMware

**Developer Tools:**
- AWS Cloud9
- AWS Cloud Development Kit (AWS CDK)
- AWS CloudShell
- AWS CodeArtifact
- AWS CodeBuild
- AWS CodeCommit
- AWS CodeDeploy
- Amazon CodeGuru
- AWS CodeStar
- Amazon Corretto
- AWS Fault Injection Simulator (AWS FIS)
- AWS Tools and SDKs

**Front-End Web and Mobile:**
- Amazon Location Service

**Game Tech:**
- Amazon GameLift
- Amazon Lumberyard

**Internet of Things:**
- All services

**Machine Learning:**
- Apache MXNet on AWS
- Amazon Augmented AI (Amazon A2I)
- AWS DeepComposer
- AWS Deep Learning AMIs (DLAMI)
- AWS Deep Learning Containers
- AWS DeepLens
- AWS DeepRacer
- Amazon DevOps Guru
- Amazon Elastic Inference
- Amazon HealthLake
- AWS Inferentia
- Amazon Lookout for Equipment
- Amazon Lookout for Metrics
- Amazon Lookout for Vision
- Amazon Monitron
- AWS Panorama
- Amazon Personalize
- PyTorch on AWS
- Amazon SageMaker Data Wrangler
- Amazon SageMaker Ground Truth
- TensorFlow on AWS

**Management and Governance:**
- AWS Chatbot
- AWS Console Mobile Application
- AWS Distro for OpenTelemetry
- AWS OpsWorks

**Media Services:**
- AWS Elemental Appliances and Software
- AWS Elemental MediaConnect
- AWS Elemental MediaConvert
- AWS Elemental MediaLive

- AWS Elemental MediaPackage
- AWS Elemental MediaStore
- AWS Elemental MediaTailor
- Amazon Interactive Video Service (Amazon IVS)

**Migration and Transfer:**
- Migration Evaluator

**Networking and Content Delivery:**
- AWS App Mesh
- AWS Cloud Map

**Quantum Technologies:**
- Amazon Braket

**Robotics:**
- AWS RoboMaker

**Satellite:**
- AWS Ground Station

Survey
How useful was this exam guide? Let us know by taking our survey.


---

## 3. AWS Free Tier for new accounts (2026)

Primary sources: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html , https://aws.amazon.com/free/ , https://aws.amazon.com/free/terms/

- **Two plans at sign-up: Free plan or Paid plan.** Both give new customers USD $100 in credits at sign-up, plus up to USD $100 more for completing activities (up to $200 total). Both include access to 30+ "always free" services with monthly usage limits. (free-tier-plans doc; aws.amazon.com/free)
- **Free plan duration:** ends after 6 months or when credits are fully used, whichever comes first. (free-tier-plans doc)
- **Free Tier Credits expire 12 months after the account was opened** (terms), but the Free plan itself ends sooner (6 months), so unused credits only matter if you upgrade. Source: https://aws.amazon.com/free/terms/
- **When the Free plan ends:** the account closes automatically and you lose access to resources and data. AWS retains content for 90 days, then permanently deletes the account and resources. Within 90 days you can upgrade to the Paid plan to keep access; remaining credits are then applied to future bills. (free-tier-plans doc; terms)
- **No charges on the Free plan**, because it excludes services/features that could deplete credits or incur charges (for example Savings Plans, Reserved Instances, some Marketplace offers, hardware purchases). The eligible-service list is on https://aws.amazon.com/free/ (not enumerated in the fetched text; list unconfirmed).
- **Paid plan:** all services, pay-as-you-go beyond the credit balance, account does not close when credits run out, eligible for other promotional credits, plus short-term trials for select services.
- **Free plan auto-upgrades to Paid** if you join AWS Organizations, set up a Control Tower landing zone, join APN, create a Professional Services contract, enroll in an Enterprise Agreement, buy a Skill Builder Team subscription, or designate the account HIPAA/SEC compliant. Relevant to labs: do NOT create an Organization or Control Tower landing zone in a Free-plan lab account unless you accept being upgraded to Paid. (free-tier-plans doc)
- **Free plan is not eligible for other promotional credits.** Upgrade path: Billing console > Upgrade plan.
- **Always-free example I could confirm:** DynamoDB free tier (25 WCU/25 RCU provisioned, 25 GB storage, 2.5M stream read requests, 1 GB data transfer out): https://aws.amazon.com/dynamodb/pricing/provisioned/ . Other always-free allowances (for example Lambda 1M requests/month) are widely cited but I could not retrieve them from the JS-rendered free page: unconfirmed. Link learners to https://aws.amazon.com/free/ for the current list.
- **Old 12-month free tier (750 h t2/t3.micro etc.)** applies to accounts created before the 2025 change. The fetched official pages do not describe it for new accounts, so do not promise it. The exact date of the change (mid-2025 per the task brief) is not stated in the fetched docs: unconfirmed.
- **Public IPv4 addresses cost money** (USD 0.005/hour per address since 2024-02-01), so lab VPCs should avoid idle Elastic IPs and public IPs left running. Source: https://aws.amazon.com/blogs/aws/new-aws-public-ipv4-address-charge-public-ip-insights/

### Budget and billing alarm setup (official docs)

- **Create a budget from a template:** Billing and Cost Management console > Budgets > Create budget > "Use a template (simplified)". Templates: **Zero spend budget** ("notifies you after your spending exceeds AWS Free Tier limits"), **Monthly cost budget** ("notifies you if you exceed, or are forecasted to exceed, the budget amount"), Daily Savings Plans coverage budget, Daily reservation utilization budget. Source: https://docs.aws.amazon.com/cost-management/latest/userguide/budget-templates.html ; overview: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-create.html
- **Budgets pricing / how many budgets are free:** not retrieved (JS-rendered): unconfirmed.
- **CloudWatch billing alarm:** https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/monitor_estimated_charges_with_cloudwatch.html . Steps: (1) Billing console > Billing Preferences > Alert preferences > Edit > "Receive CloudWatch Billing Alerts" > Save (about 15 minutes before data appears; cannot be disabled afterward). (2) Switch Region to US East (N. Virginia), where billing metrics live. (3) CloudWatch > Alarms > Create alarm > Select metric > Billing > Total Estimated Charge > EstimatedCharges; Statistic Maximum, Period 6 hours, Static, Greater than a USD threshold; 1 out of 1; missing data = "Treat missing data as missing"; notify an SNS topic with your email. The alarm fires on actual current charges, not forecasts. Needs root or an IAM user with billing permission.
- Tracking Free Tier usage / credit balance: Billing and Cost Management console home. https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/tracking-free-tier-usage.html

---

## 4. Retired or changed services (do not teach as current)

**Primary official source for lifecycle status:** AWS Lifecycle Changes. Stages: Maintenance (no new onboarding), Sunset (typically 12 months to end of support), Full Shutdown (removed).
- Overview: https://docs.aws.amazon.com/general/latest/gr/service-lifecycle.html
- Maintenance list: https://docs.aws.amazon.com/general/latest/gr/maintenance_services.html
- Sunset list: https://docs.aws.amazon.com/general/latest/gr/sunset_services.html
- Full shutdown list: https://docs.aws.amazon.com/general/latest/gr/full_shutdown_services.html

Dates below are from those pages unless another URL is given. Today is 2026-10-08, so a date before that has already passed.

### 4.1 Services you asked about

| Service | Status (as of 2026-10-08) | Detail / source |
|---|---|---|
| Amazon QLDB | Full shutdown, end of support 2025-07-31 | full_shutdown_services. Still in the SAA-C03 in-scope list. |
| AWS CodeCommit | **Re-opened.** Closed to new customers 2024-07-25, then returned to full GA | AWS DevOps blog "The Future of AWS CodeCommit", 2025-11-24: "returning to full General Availability, effective immediately": https://aws.amazon.com/blogs/devops/aws-codecommit-returns-to-general-availability/ . Not on any lifecycle list. A search result suggested a pricing page still says "no longer available to new customers" (probably stale; unconfirmed). Out of exam scope either way. |
| AWS Cloud9 | Maintenance, announced 2024-07-25 (closed to new customers) | https://aws.amazon.com/blogs/devops/how-to-migrate-from-aws-cloud9-to-aws-ide-toolkits-or-aws-cloudshell/ |
| S3 Select (and S3 Glacier Select) | Maintenance, announced 2024-07-25 (closed to new customers) | https://aws.amazon.com/blogs/storage/how-to-optimize-querying-your-data-in-amazon-s3/ |
| Amazon S3 Object Lambda | Maintenance, announced 2025-11-07 | https://docs.aws.amazon.com/AmazonS3/latest/userguide/amazons3-ol-change.html |
| Original "Amazon Glacier" (vault/archive service, separate API) | Closed to new customers 2025-12-15; existing data stays accessible; AWS does not recommend it. Lifecycle page lists "Amazon S3 Glacier Direct" in maintenance, announced 2025-10-07 | S3 docs: "We recommend using the S3 Glacier storage classes within the Amazon S3 service for all of your long-term data": https://docs.aws.amazon.com/AmazonS3/latest/userguide/glacier-storage-classes.html . The 2025-12-15 date is from a search snippet of https://aws.amazon.com/s3/glacier/pricing/ (not fetched directly). The S3 Glacier STORAGE CLASSES (Instant Retrieval, Flexible Retrieval, Deep Archive) are current and are what the exam means by "S3 Glacier". |
| AWS Snowmobile | Full shutdown, 2024-03-14 | full_shutdown_services |
| AWS Snowcone | Discontinued 2024-11-12 for new and existing customers (support for existing devices until 2025-11-12) | https://aws.amazon.com/blogs/storage/aws-snow-device-updates/ |
| AWS Snowball Edge | **Closed to new customers effective 2025-11-07**; AWS says it will no longer offer ANY Snow Family device to new customers. Existing customers keep using them. Maintenance list has Snowball Edge Compute Optimized and Storage Optimized (2025-10-07). Older models (80TB V3S, GPU V3G, and a row named "AWS Snowball Edge") are in full shutdown on 2025-11-12 | https://docs.aws.amazon.com/snowball/latest/developer-guide/snowball-edge-availability-change.html . Replacements: DataSync (online), AWS Data Transfer Terminal (physical), Outposts (edge compute). |
| AWS Data Pipeline | Maintenance mode, not available to new customers (not on the lifecycle pages) | https://docs.aws.amazon.com/datapipeline/latest/DeveloperGuide/what-is-datapipeline.html . Still in the SAA-C03 in-scope list. |
| AWS App Mesh | **Sunset**, announced 2024-09-24, end of support 2026-09-30 (already passed) | https://aws.amazon.com/blogs/containers/migrating-from-aws-app-mesh-to-amazon-ecs-service-connect/ . Listed OUT of scope in the exam guide. |
| Amazon Elastic Transcoder | Full shutdown 2025-11-13 | full_shutdown_services. Still in the exam guide in-scope list (successor MediaConvert is on the out-of-scope list). |
| AWS OpsWorks (all variants) | Full shutdown 2024-05-01 | full_shutdown_services |
| Amazon Forecast | Maintenance, announced 2024-07-29 | https://aws.amazon.com/blogs/machine-learning/transition-your-amazon-forecast-usage-to-amazon-sagemaker-canvas/ |
| Amazon Lookout for Equipment | Sunset, end of support 2026-10-07 (yesterday) | sunset_services |
| Amazon Lookout for Metrics / for Vision | Full shutdown 2025-10-10 / 2025-10-31 | full_shutdown_services |
| AWS IoT Analytics | Full shutdown 2025-12-15 (AWS IoT Events: 2026-05-20) | full_shutdown_services |
| Amazon WorkDocs | Full shutdown 2025-04-25 | full_shutdown_services |
| AWS Proton | **Sunset**, announced 2025-10-07, end of support 2026-10-07 (yesterday) | https://docs.aws.amazon.com/proton/latest/userguide/proton-end-of-support.html . Still in the exam guide in-scope list. |
| Amazon Timestream for LiveAnalytics | Maintenance, announced 2025-06-20; use Timestream for InfluxDB | https://docs.aws.amazon.com/timestream/latest/developerguide/timestream-for-influxdb.html |
| EC2-Classic | Retired 2022-08-15 | https://aws.amazon.com/blogs/aws/ec2-classic-is-retiring-heres-how-to-prepare/ |
| Launch Configurations (EC2 Auto Scaling) | Legacy. Since 2023-01-01 no new instance types; accounts created on/after 2023-06-01 cannot create via console; accounts created on/after 2024-10-01 cannot create by any method. Use Launch Templates | https://docs.aws.amazon.com/autoscaling/ec2/userguide/launch-configurations.html |
| AWS Application Discovery Service | Maintenance; closed to new customers 2025-11-07 (announced 2025-10-07); Discovery Connector shut down 2025-11-17; successor AWS Transform | https://docs.aws.amazon.com/application-discovery/latest/userguide/application-discovery-service-availability-change.html |
| AWS Migration Hub | Maintenance, announced 2025-11-07 | https://docs.aws.amazon.com/migrationhub/latest/ug/migrationhub-availability-change.html |
| CloudEndure Migration | Retired in commercial Regions 2022-12-30; replaced by AWS Application Migration Service (MGN). A later AMS doc says CloudEndure Migration is end of life in all Regions and MGN is now called "AWS Transform MGN" | https://docs.aws.amazon.com/prescriptive-guidance/latest/migration-cloudendure/introduction.html ; all-Regions claim from an AMS doc snippet (https://docs.aws.amazon.com/managedservices/latest/userguide/cloud-endure.html), moderate confidence. CloudEndure DR - GovCloud shut down 2025-10-01. |
| Aurora Serverless v1 | No new clusters from 2025-01-08; end of life 2025-03-31; remaining clusters migrated to v2 or converted to provisioned | https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2.upgrade.html |
| RDS / Aurora engine versions | Older engines (for example Aurora MySQL v2 / MySQL 5.7) are past standard support and on paid Extended Support. Per-engine EOL tables not collected: unconfirmed | https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.MySQL57.EOL.html |
| gp2 vs gp3 | Both current. gp3 is the better-spec volume (up to 64 TiB, 80,000 IOPS, 2,000 MiB/s). No official statement found that gp3 is the default in every launch path: unconfirmed | https://docs.aws.amazon.com/ebs/latest/userguide/ebs-volume-types.html |

### 4.2 Other lifecycle items that touch the exam guide's in-scope list

- Amazon Pinpoint (in scope): Sunset, announced 2025-05-20, end of support 2026-10-30. https://docs.aws.amazon.com/pinpoint/latest/userguide/migrate.html
- Amazon Kendra (in scope): Maintenance, announced 2026-06-30.
- AWS Audit Manager (in scope): Maintenance, announced 2026-03-31.
- Amazon Fraud Detector (in scope): Maintenance, announced 2025-10-07.
- Amazon FSx File Gateway: Maintenance, 2024-10-28 (other Storage Gateway types are not listed).
- Amazon CloudSearch (exam out-of-scope list): Maintenance since 2024-07-25.
- Amazon Managed Blockchain (out of scope): Sunset, ends 2027-09-29.
- AWS WAF Classic: Sunset, ends 2026-10-07 (WAF v2 is current).
- Amazon Inspector Classic: shut down 2026-05-20. AWS Panorama (2026-05-20), DeepComposer, DeepLens, RoboMaker, Sumerian: shut down.
- Amazon Kinesis Data Analytics for SQL: shut down 2026-01-27. The Apache Flink product was renamed Amazon Managed Service for Apache Flink on 2023-08-30: https://aws.amazon.com/blogs/aws/announcing-amazon-managed-service-for-apache-flink-renamed-from-amazon-kinesis-data-analytics/
- Also in maintenance or sunset: Simple AD (maintenance 2026-06-30), AWS App Runner (maintenance 2026-03-31), CloudTrail Lake (maintenance 2026-03-31), Amazon WorkMail (sunset, ends 2027-03-31), Amazon DevOps Guru (sunset, ends 2027-09-29), AWS Infrastructure Composer (sunset, ends 2027-09-29), RDS Custom for Oracle (sunset, ends 2027-03-31).
- Renames: AWS Single Sign-On is AWS IAM Identity Center. Amazon QuickSight is being rebranded Amazon Quick Suite (the BI part is called "Quick Sight"), new UI for all customers from 2025-10-09: https://aws.amazon.com/blogs/business-intelligence/reimagine-business-intelligence-amazon-quicksight-evolves-to-amazon-quick-suite/ . Aurora Serverless v2 appears as "Aurora serverless" in AWS's 2026-09-30 announcement https://aws.amazon.com/about-aws/whats-new/2026/08/aurora-serverless-instant-16-acu-scaling/ (exact rename date unconfirmed).

### 4.3 Notable NEW things since 2022 relevant to architecture questions

- **S3 default encryption:** since 2023-01-05 all new objects are automatically encrypted with SSE-S3 at no cost; encryption cannot be turned off. https://aws.amazon.com/about-aws/whats-new/2023/01/amazon-s3-automatically-encrypts-new-objects/
- **S3 Block Public Access on and ACLs disabled (Bucket owner enforced) for all new buckets**, deployment began 2023-04-05, no change for existing buckets. https://aws.amazon.com/about-aws/whats-new/2023/04/amazon-s3-security-best-practices-buckets-default/
- **S3 Express One Zone** (directory buckets, single AZ, single-digit ms), launched at re:Invent 2023; 15 Regions as of Sep 2026; price cuts April 2025. https://aws.amazon.com/blogs/aws/new-amazon-s3-express-one-zone-high-performance-storage-class/ ; https://aws.amazon.com/about-aws/whats-new/2026/09/s3-express-one-zone-7-regions/
- **S3 maximum object size raised from 5 TB to 50 TB on 2025-12-02.** https://aws.amazon.com/about-aws/whats-new/2025/12/amazon-s3-maximum-object-size-50-tb/
- **Amazon VPC Lattice GA 2023-03-31.** https://aws.amazon.com/about-aws/whats-new/2023/03/general-availability-amazon-vpc-lattice/
- **Aurora Serverless v2 scales to 0 ACUs** (auto-pause) since 2024-11-20: https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-aurora-serverless-v2-scaling-zero-capacity/ . Idle window 300 s to 86,400 s, resume under 15 s, from a search summary of https://aws.amazon.com/blogs/database/introducing-scaling-to-0-capacity-with-amazon-aurora-serverless-v2/ . Range now up to 256 ACUs. The exam guide still says "Amazon Aurora Serverless".
- **IMDSv2:** Amazon Linux 2023 disables IMDSv1 by default (2023). Account-level "IMDSv2 as default for new launches" since 2024-03: https://aws.amazon.com/about-aws/whats-new/2024/03/set-imdsv2-default-new-instance-launches/ . A 2026-02 account-level enforcement option is from a search summary only (unconfirmed).
- **Public IPv4 charge** USD 0.005 per address-hour from 2024-02-01, in use or idle; BYOIP exempt; 750 h/month free for 12-month-tier EC2 accounts: https://aws.amazon.com/blogs/aws/new-aws-public-ipv4-address-charge-public-ip-insights/ ; https://aws.amazon.com/about-aws/whats-new/2024/02/aws-free-tier-750-hours-free-public-ipv4-addresses/
- **SQS max message size raised from 256 KiB to 1 MiB on 2025-08-04.** https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-sqs-max-payload-size-1mib/
- **SQS fair queues** (MessageGroupId on standard queues) now exist: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html
- **EBS limits grew:** gp3 now 64 TiB / 80,000 IOPS / 2,000 MiB/s (older material says 16 TiB / 16,000 / 1,000 MiB/s); io2 Block Express 256,000 IOPS / 4,000 MiB/s / 64 TiB. https://docs.aws.amazon.com/ebs/latest/userguide/ebs-volume-types.html
- **Lambda** still 900 s max timeout; a newer "Lambda Managed Instances" mode allows up to 5,400 s for async and event-source-mapping invocations: https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html

---

## 5. Key numeric facts (current as of 2026-10-08)

| Fact | Value | Source |
|---|---|---|
| S3 single PUT | up to 5 GB; console upload of a single object up to 160 GB | https://docs.aws.amazon.com/AmazonS3/latest/userguide/upload-objects.html |
| S3 max object size | **50 TB** (since 2025-12-02; was 5 TB). Multipart upload for 5 MB to 50 TB objects | same doc; https://aws.amazon.com/about-aws/whats-new/2025/12/amazon-s3-maximum-object-size-50-tb/ . Older exam material says 5 TB. |
| SQS message size | min 1 byte, max 1,048,576 bytes (1 MiB), raised from 256 KiB on 2025-08-04; Extended Client Library payloads up to 2 GB via S3 | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html |
| SQS retention | default 4 days; min 60 s; max 1,209,600 s (14 days) | same |
| SQS visibility timeout | default 30 s; min 0; max 12 hours | same |
| SQS delay | default 0; max 15 minutes | same |
| SQS throughput | Standard: nearly unlimited. FIFO (default mode): 300 transactions/s per API action per partition; with batching up to 3,000 messages/s per action (300 calls x batch of 10). High-throughput mode raises this (exact numbers not captured: unconfirmed) | same |
| Lambda timeout | 900 s (15 min) | https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html |
| Lambda memory | 128 MB to 10,240 MB in 1-MB steps; 1,769 MB = one vCPU equivalent | same |
| Lambda /tmp (ephemeral storage) | configurable 512 MB to 10,240 MB | https://docs.aws.amazon.com/lambda/latest/dg/configuration-ephemeral-storage.html |
| Lambda payload | 6 MB sync request and response; 1 MB async; streamed response 200 MB | gettingstarted-limits |
| DynamoDB item size | 400 KB maximum | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html |
| RDS MySQL read replicas | up to 15 per source instance in the same Region (cascading supported) | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_MySQL.Replication.ReadReplicas.html |
| RDS PostgreSQL read replicas | number not found on the fetched page: unconfirmed (older material says 5; do not assert) | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PostgreSQL.Replication.ReadReplicas.html |
| Aurora Replicas | up to 15 Aurora Replicas per cluster | https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.Replication.html |
| Reserved IPs per subnet | 5 (network address, .1 VPC router, .2 DNS, .3 future use, last address = broadcast) | https://docs.aws.amazon.com/vpc/latest/userguide/subnet-sizing.html |

### EBS volume types (from the tables at https://docs.aws.amazon.com/ebs/latest/userguide/ebs-volume-types.html)

| Type | Size | Max IOPS | Max throughput | Notes |
|---|---|---|---|---|
| gp3 | 1 GiB - 64 TiB | 80,000 | 2,000 MiB/s | Boot supported; Multi-Attach not supported. On Outposts: 16 TiB / 16,000 / 1,000 |
| gp2 | 1 GiB - 16 TiB | 16,000 | 250 MiB/s (128-250 by size) | Boot supported |
| io2 Block Express | 4 GiB - 64 TiB | 256,000 | 4,000 MiB/s | 99.999% durability; sub-ms latency; Multi-Attach supported; 256k IOPS needs Nitro |
| io1 | 4 GiB - 16 TiB | 64,000 | 1,000 MiB/s | Multi-Attach supported; 1,000 MiB/s needs 64,000 IOPS on Nitro |
| st1 (Throughput Optimized HDD) | 125 GiB - 16 TiB | 500 (1 MiB I/O) | 500 MiB/s | Not bootable |
| sc1 (Cold HDD) | 125 GiB - 16 TiB | 250 (1 MiB I/O) | 250 MiB/s | Not bootable |

Durability: gp3, gp2, io1 and HDD 99.8%-99.9% (0.1%-0.2% annual failure rate); io2 Block Express 99.999%.

### S3 Glacier retrieval times (typical)

- **S3 Glacier Flexible Retrieval:** Expedited 1-5 minutes (objects under 250 MB); Standard 3-5 hours; Bulk 5-12 hours.
- **S3 Glacier Deep Archive:** Standard within 12 hours; Bulk within 48 hours. (No Expedited.) The summary table in the Glacier doc says "9 to 48 hours" for Deep Archive and "Minutes to 12 hours" for Flexible Retrieval.
- **S3 Glacier Instant Retrieval:** milliseconds.
- Sources: https://docs.aws.amazon.com/AmazonS3/latest/userguide/restoring-objects-retrieval-options.html and https://docs.aws.amazon.com/AmazonS3/latest/userguide/glacier-storage-classes.html

### S3 minimum storage durations

- S3 Standard: none. S3 Intelligent-Tiering: none (no retrieval fee). Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html
- S3 Standard-IA: 30 days (also 128 KB minimum billable object size). S3 One Zone-IA: 30 days is the commonly cited value, but its table row was not separately captured: treat as unconfirmed here. Source: storage-class-intro.
- S3 Glacier Instant Retrieval: 90 days. S3 Glacier Flexible Retrieval: 90 days. S3 Glacier Deep Archive: 180 days. Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/glacier-storage-classes.html
- S3 Express One Zone minimum duration: not captured: unconfirmed.

---

## Confidence notes (what I could not confirm)

- Exam guide: complete and verbatim from the official PDF (v1.1). I did not diff it against the JS-rendered docs.aws.amazon.com version. The guide is dated by version number only.
- No official statement for or against a future SAA-C04 beyond its absence from the cert page and the Coming-soon page today. Absence is not a guarantee.
- Free Tier: the exact date of the 2025 change and the full always-free service list were not retrievable (JS-rendered pages). Credit amounts, 6-month limit, 90-day retention, auto-upgrade triggers and 12-month credit expiry are confirmed from AWS docs and terms. Number of free budgets not confirmed.
- Snow Family: lifecycle pages are a bit inconsistent about which Snowball Edge rows are maintenance vs full shutdown; the Snowball Edge availability-change page (closed to new customers from 2025-11-07; no Snow devices for new customers) is the clearest statement.
- Original Glacier closed-to-new-customers date (2025-12-15) comes from a search snippet of the Glacier pricing page. CodeCommit's return is confirmed by the 2025-11-24 AWS blog, but a stale pricing page may still say otherwise.
- CloudEndure all-Region EOL and "AWS Transform MGN" naming: from an AMS doc snippet only.
- Unconfirmed: RDS PostgreSQL read replica count, SQS FIFO high-throughput exact numbers, S3 Express One Zone and One Zone-IA minimum durations, Lambda always-free allowances, "gp3 is default" claim, per-engine RDS/Aurora EOL dates, IMDSv2 enforcement release note, exact Aurora serverless rename date.

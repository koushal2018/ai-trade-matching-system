# AWS Resource Inventory - OTC Trade Matching System

**Project**: AI Trade Matching System (OTC_Agent)  
**AWS Account**: 401552979575  
**Region**: us-east-1  
**Generated**: December 24, 2025  

## AWS Application Registry

| Resource | Value |
|----------|-------|
| Application Name | OTC_Agent |
| Application ARN | `arn:aws:resource-groups:us-east-1:401552979575:group/OTC_Agent/038wkdij7bnpfmi7bbkvpt87s1` |
| Service Catalog ARN | `arn:aws:servicecatalog:us-east-1:401552979575:/applications/038wkdij7bnpfmi7bbkvpt87s1` |

---

## 1. Storage Resources

### S3 Buckets

| Bucket Name | Purpose | Created |
|-------------|---------|---------|
| `trade-matching-system-agentcore-production` | Main storage for PDFs, extracted text, canonical data | 2025-11-26 |
| `trade-matching-system-agentcore-logs-production` | Access logs for main bucket | 2025-11-26 |
| `trade-matching-system-agentcore-production-production` | Additional production storage | 2025-12-20 |

**S3 Folder Structure** (`trade-matching-system-agentcore-production`):
- `BANK/` - Bank trade confirmation PDFs
- `COUNTERPARTY/` - Counterparty trade confirmation PDFs
- `extracted/` - Text extraction outputs from PDF Adapter
- `canonical/` - Structured JSON outputs from Trade Extraction
- `reports/` - Matching reports and analytics

---

## 2. Database Resources

### DynamoDB Tables

| Table Name | Purpose | Partition Key |
|------------|---------|---------------|
| `BankTradeData` | Bank-side trade records | tradeId |
| `BankTradeData-production` | Production bank trade records | tradeId |
| `CounterpartyTradeData` | Counterparty-side trade records | tradeId |
| `CounterpartyTradeData-production` | Production counterparty records | tradeId |
| `trade-matching-system-processing-status` | Real-time workflow status tracking | sessionId |
| `trade-matching-system-exceptions-production` | Exceptions and errors | exceptionId |
| `trade-matching-system-agent-registry-production` | Agent metadata and routing | agentId |
| `trade-matching-system-idempotency` | Idempotency tracking | requestId |

---

## 3. Identity & Access Management

### Cognito User Pool

| Resource | Value |
|----------|-------|
| User Pool ID | `us-east-1_uQ2lN39dT` |
| User Pool Name | `trade-matching-system-agentcore-identity-production` |
| Client ID | `78daptta2m4lb6k5jm3n2hd8oc` |
| MFA | Enabled |

### IAM Roles

| Role Name | Purpose |
|-----------|---------|
| `trade-matching-system-agentcore-runtime-production` | AgentCore runtime execution |
| `trade-matching-system-agentcore-gateway-production` | AgentCore gateway access |
| `trade-matching-system-lambda-orchestrator-production` | Orchestrator Lambda execution |
| `trade-matching-system-lambda-pdf-adapter-production` | PDF Adapter Lambda execution |
| `trade-matching-system-lambda-trade-extraction-production` | Trade Extraction Lambda execution |
| `trade-matching-system-lambda-trade-matching-production` | Trade Matching Lambda execution |
| `trade-matching-system-lambda-exception-mgmt-production` | Exception Management Lambda execution |
| `trade-matching-system-lambda-custom-ops-production` | Custom operations Lambda execution |
| `trade-matching-system-cognito-admin-production` | Cognito admin access |
| `trade-matching-system-cognito-operator-production` | Cognito operator access |
| `trade-matching-system-cognito-auditor-production` | Cognito auditor access |
| `agentcore` | Base AgentCore role |
| `agentcore-handler-execution-role` | AgentCore handler execution |
| `agentcore-s3-proxy-role` | AgentCore S3 proxy access |

### IAM Policies

| Policy Name | Purpose |
|-------------|---------|
| `trade-matching-system-agentcore-s3-access-production` | S3 bucket access |
| `trade-matching-system-agentcore-bedrock-access-production` | Bedrock model access |
| `trade-matching-system-agentcore-dynamodb-access-production` | DynamoDB table access |
| `trade-matching-system-agentcore-sqs-access-production` | SQS queue access |
| `trade-matching-system-agentcore-memory-access-production` | AgentCore Memory access |
| `trade-matching-system-agentcore-observability-production` | Observability access |
| `trade-matching-system-agentcore-cloudwatch-logs-production` | CloudWatch Logs access |
| `trade-matching-system-cognito-admin-policy-production` | Cognito admin policy |
| `trade-matching-system-cognito-operator-policy-production` | Cognito operator policy |
| `trade-matching-system-cognito-auditor-policy-production` | Cognito auditor policy |

---

## 4. Messaging Resources

### SQS Queues

| Queue Name | Type | Purpose |
|------------|------|---------|
| `trade-matching-system-document-upload-events-production.fifo` | FIFO | Document upload events |
| `trade-matching-system-document-upload-dlq-production.fifo` | FIFO | Document upload DLQ |
| `trade-matching-system-extraction-events-production` | Standard | Extraction events |
| `trade-matching-system-extraction-dlq-production` | Standard | Extraction DLQ |
| `trade-matching-system-matching-events-production` | Standard | Matching events |
| `trade-matching-system-matching-dlq-production` | Standard | Matching DLQ |
| `trade-matching-system-exception-events-production` | Standard | Exception events |
| `trade-matching-system-exception-dlq-production` | Standard | Exception DLQ |
| `trade-matching-system-hitl-review-queue-production.fifo` | FIFO | HITL review queue |
| `trade-matching-system-hitl-dlq-production.fifo` | FIFO | HITL DLQ |
| `trade-matching-system-compliance-queue-production.fifo` | FIFO | Compliance queue |
| `trade-matching-system-ops-desk-queue-production.fifo` | FIFO | Operations desk queue |
| `trade-matching-system-senior-ops-queue-production.fifo` | FIFO | Senior operations queue |
| `trade-matching-system-engineering-queue-production` | Standard | Engineering queue |
| `trade-matching-system-orchestrator-monitoring-queue-production` | Standard | Orchestrator monitoring |

### SNS Topics

| Topic Name | Purpose |
|------------|---------|
| `trade-matching-system-agentcore-alerts-production` | AgentCore alerts |
| `trade-matching-system-agent-events-fanout-production` | Agent events fanout |
| `trade-matching-system-billing-alerts-production` | Billing alerts |

---

## 5. Compute Resources

### Lambda Functions

| Function Name | Purpose |
|---------------|---------|
| `trade-matching-system-custom-operations-production` | Custom operations handler |

### AgentCore Agents (Bedrock AgentCore Runtime)

| Agent Name | Location | Purpose |
|------------|----------|---------|
| PDF Adapter Agent | `deployment/pdf_adapter/` | PDF text extraction via Bedrock multimodal |
| Trade Extraction Agent | `deployment/trade_extraction/` | Structured trade data extraction |
| Trade Matching Agent | `deployment/trade_matching/` | AI-driven fuzzy matching |
| Exception Management Agent | `deployment/exception_management/` | Exception triage and routing |
| Orchestrator Agent | `deployment/orchestrator/` | Workflow orchestration |
| HTTP Orchestrator | `deployment/swarm_agentcore/` | HTTP-based orchestration |

### AgentCore Memory

| Resource | Value |
|----------|-------|
| Memory ID | `trade_matching_decisions-Z3tG4b4Xsd` |
| Namespace Strategies | `/facts/{actorId}`, `/preferences/{actorId}`, `/summaries/{actorId}/{sessionId}` |
| Retention | 90 days |

---

## 6. Monitoring & Observability

### CloudWatch Log Groups

| Log Group | Purpose |
|-----------|---------|
| `/aws/agentcore/trade-matching-system/orchestrator-production` | Orchestrator logs |
| `/aws/agentcore/trade-matching-system/pdf-adapter-production` | PDF Adapter logs |
| `/aws/agentcore/trade-matching-system/trade-extraction-production` | Trade Extraction logs |
| `/aws/agentcore/trade-matching-system/trade-matching-production` | Trade Matching logs |
| `/aws/agentcore/trade-matching-system/exception-management-production` | Exception Management logs |

### CloudWatch Alarms

| Alarm Name | Purpose |
|------------|---------|
| `trade-matching-system-pdf-adapter-latency-production` | PDF Adapter latency monitoring |
| `trade-matching-system-pdf-adapter-error-rate-production` | PDF Adapter error rate |
| `trade-matching-system-trade-matching-error-rate-production` | Trade Matching error rate |
| `trade-matching-system-total-charges-production` | Total charges alarm |
| `trade-matching-system-total-charges-warning-production` | Total charges warning |
| `trade-matching-system-daily-charges-production` | Daily charges alarm |
| `trade-matching-system-bedrock-charges-production` | Bedrock charges alarm |
| `trade-matching-system-s3-charges-production` | S3 charges alarm |
| `trade-matching-system-dynamodb-charges-production` | DynamoDB charges alarm |
| `trade-matching-system-cloudwatch-charges-production` | CloudWatch charges alarm |

### X-Ray

| Resource | Value |
|----------|-------|
| Sampling Rule | `tms-agentcore-production` |

---

## 7. Security Resources

### KMS Keys

| Key ID | Purpose |
|--------|---------|
| `a54ae526-a4a6-4099-85c8-d1baa5d1332c` | Encryption key for trade matching system |

---

## 8. AI/ML Resources

### Bedrock Models

| Model | Model ID | Purpose |
|-------|----------|---------|
| Amazon Nova Pro v1 | `us.amazon.nova-pro-v1:0` | Primary model for all agents |

**Model Configuration**:
- Temperature: 0 (deterministic outputs)
- Max Tokens: 4096
- Region: us-east-1

---

## 9. Required Tags for All Resources

All resources should have these tags for cost allocation and governance:

| Tag Key | Tag Value |
|---------|-----------|
| `applicationName` | `OTC_Agent` |
| `awsApplication` | `arn:aws:resource-groups:us-east-1:401552979575:group/OTC_Agent/038wkdij7bnpfmi7bbkvpt87s1` |

---

## 10. Resource Summary by Service

| Service | Count | Notes |
|---------|-------|-------|
| S3 Buckets | 3 | Main storage + logs |
| DynamoDB Tables | 8 | Trade data + system tables |
| Cognito User Pools | 1 | Authentication |
| IAM Roles | 18 | Execution roles |
| IAM Policies | 10 | Access policies |
| SQS Queues | 15 | Event queues + DLQs |
| SNS Topics | 3 | Alerts and fanout |
| Lambda Functions | 1 | Custom operations |
| CloudWatch Log Groups | 5 | Agent logs |
| CloudWatch Alarms | 10 | Monitoring alarms |
| KMS Keys | 1 | Encryption |
| X-Ray Sampling Rules | 1 | Tracing |

---

## 11. Infrastructure as Code

### Terraform Configurations

| Path | Purpose |
|------|---------|
| `terraform/agentcore/` | AgentCore infrastructure |
| `terraform/agentcore/main.tf` | Main Terraform configuration |
| `terraform/agentcore/dynamodb.tf` | DynamoDB tables |
| `terraform/agentcore/s3.tf` | S3 buckets |
| `terraform/agentcore/iam.tf` | IAM roles and policies |
| `terraform/agentcore/cognito.tf` | Cognito configuration |
| `terraform/agentcore/sqs.tf` | SQS queues |
| `terraform/agentcore/billing_alarms.tf` | Billing alarms |
| `terraform/agentcore/agentcore_gateway.tf` | AgentCore Gateway |
| `terraform/agentcore/agentcore_memory.tf` | AgentCore Memory |
| `terraform/agentcore/agentcore_observability.tf` | Observability config |

### AgentCore Deployment Configurations

| Agent | Config Path |
|-------|-------------|
| PDF Adapter | `deployment/pdf_adapter/agentcore.yaml` |
| Trade Extraction | `deployment/trade_extraction/agentcore.yaml` |
| Trade Matching | `deployment/trade_matching/agentcore.yaml` |
| Exception Management | `deployment/exception_management/agentcore.yaml` |
| Orchestrator | `deployment/orchestrator/agentcore.yaml` |
| HTTP Orchestrator | `deployment/swarm_agentcore/agentcore.yaml` |

---

## 12. Cost Allocation

Resources are tagged with `applicationName: OTC_Agent` for AWS Cost Explorer filtering.

**Monthly Cost Drivers** (estimated):
1. Bedrock API calls (Nova Pro model)
2. DynamoDB read/write capacity
3. S3 storage and requests
4. CloudWatch Logs ingestion
5. Lambda invocations (minimal)

---

*Last Updated: December 24, 2025*

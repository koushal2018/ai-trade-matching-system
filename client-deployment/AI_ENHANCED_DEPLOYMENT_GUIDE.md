# AI-Enhanced Trade Reconciliation Deployment Guide

This guide covers the deployment of the enhanced Trade Reconciliation Solution with configurable AI provider support, regional deployment options, and intelligent decision-making capabilities.

## Overview

The enhanced solution supports:
- **Multiple AI Providers**: AWS Bedrock, SageMaker AI Jumpstart, HuggingFace models
- **Configurable Decision Modes**: Deterministic, LLM-based, or Hybrid approaches
- **Regional Deployments**: Optimized templates for US, EU, and UAE regions
- **Performance Optimization**: Batching, caching, and parallel processing
- **Flexible Deployment**: VDI, standalone, and cloud-native options

## AI Provider Support by Region

| Region | Bedrock | SageMaker | HuggingFace | Recommended |
|--------|---------|-----------|-------------|-------------|
| US (us-east-1, us-west-2) | ✅ | ✅ | ✅ | Bedrock |
| EU (eu-west-1, eu-central-1) | ✅ | ✅ | ✅ | Bedrock |
| UAE (me-central-1, me-south-1) | ❌ | ✅ | ✅ | SageMaker |
| APAC (ap-southeast-1, ap-northeast-1) | ✅ | ✅ | ✅ | Bedrock |

## Quick Start

### 1. Validate Your Configuration

```bash
# Validate UAE deployment with SageMaker
./client-deployment/validate-ai-deployment.sh \
    -r me-central-1 \
    -p sagemaker \
    -m llm \
    -b your-templates-bucket \
    -v

# Validate US deployment with Bedrock
./client-deployment/validate-ai-deployment.sh \
    -r us-east-1 \
    -p bedrock \
    -m hybrid \
    -b your-templates-bucket \
    -v
```

### 2. Deploy Using Regional Templates

#### US Region Deployment
```bash
aws cloudformation deploy \
    --template-file client-deployment/cloudformation/regional/us-master-template.yaml \
    --stack-name prod-trade-reconciliation-enhanced \
    --parameter-overrides \
        TemplateS3Bucket=your-templates-bucket \
        EnvironmentName=prod \
        AIProviderType=bedrock \
        DecisionMode=hybrid \
        AIProviderRegion=us-east-1 \
        BedrockModelId=anthropic.claude-3-sonnet-20240229-v1:0 \
        ConfidenceThreshold=0.85 \
    --capabilities CAPABILITY_NAMED_IAM \
    --region us-east-1
```

#### UAE Region Deployment
```bash
aws cloudformation deploy \
    --template-file client-deployment/cloudformation/regional/uae-master-template.yaml \
    --stack-name prod-trade-reconciliation-enhanced \
    --parameter-overrides \
        TemplateS3Bucket=your-templates-bucket \
        EnvironmentName=prod \
        AIProviderType=sagemaker \
        DecisionMode=llm \
        AIProviderRegion=me-central-1 \
        SagemakerEndpointName=your-sagemaker-endpoint \
        ConfidenceThreshold=0.8 \
    --capabilities CAPABILITY_NAMED_IAM \
    --region me-central-1
```

#### EU Region Deployment
```bash
aws cloudformation deploy \
    --template-file client-deployment/cloudformation/regional/eu-master-template.yaml \
    --stack-name prod-trade-reconciliation-enhanced \
    --parameter-overrides \
        TemplateS3Bucket=your-templates-bucket \
        EnvironmentName=prod \
        AIProviderType=bedrock \
        DecisionMode=hybrid \
        AIProviderRegion=eu-west-1 \
        BedrockModelId=anthropic.claude-3-sonnet-20240229-v1:0 \
        GDPRCompliance=true \
        DataResidencyRegion=eu-west-1 \
    --capabilities CAPABILITY_NAMED_IAM \
    --region eu-west-1
```

## Configuration Parameters

### Core Parameters

| Parameter | Description | Default | Required |
|-----------|-------------|---------|----------|
| `EnvironmentName` | Environment (dev/test/prod) | dev | Yes |
| `AIProviderType` | AI provider (bedrock/sagemaker/huggingface/none) | bedrock | Yes |
| `DecisionMode` | Decision approach (deterministic/llm/hybrid) | deterministic | Yes |
| `AIProviderRegion` | Region for AI services | us-east-1 | Yes |

### AI Provider Specific Parameters

#### Bedrock Configuration
```yaml
BedrockModelId: anthropic.claude-3-sonnet-20240229-v1:0
# Available models:
# - anthropic.claude-3-sonnet-20240229-v1:0
# - anthropic.claude-3-haiku-20240307-v1:0
# - amazon.titan-text-express-v1
# - ai21.j2-ultra-v1
```

#### SageMaker Configuration
```yaml
SagemakerEndpointName: your-sagemaker-endpoint
# Must be a deployed SageMaker endpoint in the target region
```

#### HuggingFace Configuration
```yaml
HuggingfaceModelName: microsoft/DialoGPT-medium
HuggingfaceApiToken: your-api-token  # Stored in Secrets Manager
```

### Performance Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ConfidenceThreshold` | AI matching confidence threshold | 0.8 |
| `SemanticThreshold` | Semantic similarity threshold | 0.85 |
| `EnablePerformanceOptimization` | Enable batching/caching | true |

## Decision Modes

### 1. Deterministic Mode
- Uses existing rule-based matching
- No AI provider required
- Fastest performance
- Consistent results

```yaml
DecisionMode: deterministic
AIProviderType: none
```

### 2. LLM Mode
- Uses AI for all matching decisions
- Requires AI provider configuration
- Intelligent contextual understanding
- Semantic field matching

```yaml
DecisionMode: llm
AIProviderType: bedrock  # or sagemaker/huggingface
```

### 3. Hybrid Mode
- Combines deterministic and AI approaches
- Falls back to deterministic on AI failures
- Balanced performance and intelligence
- Recommended for production

```yaml
DecisionMode: hybrid
AIProviderType: bedrock
```

## Regional Deployment Considerations

### United States
- **Template**: `regional/us-master-template.yaml`
- **AI Providers**: All supported (Bedrock recommended)
- **Regions**: us-east-1, us-west-2
- **DR Region**: Automatic cross-region selection

### European Union
- **Template**: `regional/eu-master-template.yaml`
- **AI Providers**: All supported (Bedrock recommended)
- **Regions**: eu-west-1, eu-central-1
- **Compliance**: GDPR compliance features
- **Data Residency**: EU-only data storage

### United Arab Emirates
- **Template**: `regional/uae-master-template.yaml`
- **AI Providers**: SageMaker, HuggingFace (Bedrock not available)
- **Regions**: me-central-1, me-south-1
- **DR Region**: me-south-1 for me-central-1 deployments

## Environment Variables

The enhanced Lambda functions receive these AI-related environment variables:

```bash
# AI Provider Configuration
AI_PROVIDER_TYPE=bedrock
DECISION_MODE=hybrid
AI_PROVIDER_REGION=us-east-1

# Provider-Specific Settings
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
SAGEMAKER_ENDPOINT_NAME=your-endpoint
HUGGINGFACE_MODEL_NAME=microsoft/DialoGPT-medium
HUGGINGFACE_SECRET_ARN=arn:aws:secretsmanager:...

# Performance Settings
CONFIDENCE_THRESHOLD=0.8
SEMANTIC_THRESHOLD=0.85
ENABLE_PERFORMANCE_OPTIMIZATION=true
```

## IAM Permissions

The enhanced IAM roles include permissions for:

### Bedrock Permissions
```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream"
  ],
  "Resource": "arn:aws:bedrock:*::foundation-model/*"
}
```

### SageMaker Permissions
```json
{
  "Effect": "Allow",
  "Action": [
    "sagemaker:InvokeEndpoint"
  ],
  "Resource": "arn:aws:sagemaker:*:*:endpoint/*"
}
```

### Secrets Manager Permissions (HuggingFace)
```json
{
  "Effect": "Allow",
  "Action": [
    "secretsmanager:GetSecretValue"
  ],
  "Resource": "arn:aws:secretsmanager:*:*:secret:*-huggingface-api-token-*"
}
```

## Monitoring and Troubleshooting

### CloudWatch Metrics
- AI provider response times
- Confidence score distributions
- Fallback usage patterns
- Error rates by provider

### Common Issues

#### 1. Bedrock Access Denied
```bash
# Check model access in Bedrock console
aws bedrock list-foundation-models --region us-east-1

# Verify IAM permissions
aws iam simulate-principal-policy \
    --policy-source-arn arn:aws:iam::ACCOUNT:role/ROLE-NAME \
    --action-names bedrock:InvokeModel \
    --resource-arns arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0
```

#### 2. SageMaker Endpoint Not Found
```bash
# List available endpoints
aws sagemaker list-endpoints --region me-central-1

# Check endpoint status
aws sagemaker describe-endpoint --endpoint-name your-endpoint --region me-central-1
```

#### 3. HuggingFace API Token Issues
```bash
# Verify secret exists
aws secretsmanager describe-secret --secret-id dev-huggingface-api-token

# Test token validity
curl -H "Authorization: Bearer YOUR_TOKEN" https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium
```

## Performance Optimization

### Batching Configuration
```yaml
EnablePerformanceOptimization: true
# Enables:
# - Intelligent batching of AI requests
# - Response caching
# - Parallel processing
# - Priority queuing
```

### Caching Strategy
- AI analysis results cached for 1 hour
- Semantic similarity scores cached for 24 hours
- Document context analysis cached per document hash

### Scaling Considerations
- Lambda concurrency limits
- AI provider rate limits
- DynamoDB read/write capacity
- S3 request patterns

## Cost Optimization

### AI Provider Costs
- **Bedrock**: Pay per token (input/output)
- **SageMaker**: Pay per endpoint hour + inference requests
- **HuggingFace**: Pay per API call

### Cost Monitoring
```bash
# Enable cost allocation tags
aws cloudformation update-stack \
    --stack-name your-stack \
    --use-previous-template \
    --parameters ParameterKey=EnableCostAllocationTags,ParameterValue=true
```

## Security Best Practices

### 1. API Token Management
- Store HuggingFace tokens in Secrets Manager
- Rotate tokens regularly
- Use least-privilege IAM policies

### 2. Network Security
- Deploy in private subnets when possible
- Use VPC endpoints for AWS services
- Enable CloudTrail for API auditing

### 3. Data Protection
- Enable encryption at rest for all storage
- Use TLS 1.2+ for all communications
- Implement data retention policies

## Backup and Disaster Recovery

### Regional DR Strategy
- **US**: us-east-1 ↔ us-west-2
- **EU**: eu-west-1 ↔ eu-central-1
- **UAE**: me-central-1 ↔ me-south-1

### Backup Components
- DynamoDB point-in-time recovery
- S3 cross-region replication
- Lambda function code versioning
- CloudFormation template versioning

## Migration from Legacy System

### 1. Gradual Migration
```yaml
# Start with hybrid mode
DecisionMode: hybrid
AIProviderType: bedrock
```

### 2. A/B Testing
- Deploy parallel stacks
- Route percentage of traffic to enhanced version
- Compare results and performance

### 3. Rollback Strategy
```yaml
# Quick rollback to deterministic
DecisionMode: deterministic
AIProviderType: none
```

## Support and Troubleshooting

### Log Analysis
```bash
# View Lambda logs
aws logs filter-log-events \
    --log-group-name /aws/lambda/dev-trade-reconciliation-engine \
    --filter-pattern "AI_PROVIDER"

# Monitor AI provider errors
aws logs filter-log-events \
    --log-group-name /aws/lambda/dev-trade-reconciliation-engine \
    --filter-pattern "AIProviderError"
```

### Health Checks
```bash
# Test AI provider connectivity
curl -X POST https://your-api-gateway/health/ai-provider

# Validate configuration
curl -X GET https://your-api-gateway/config/ai-provider
```

For additional support, refer to the troubleshooting guide and monitoring dashboard created during deployment.
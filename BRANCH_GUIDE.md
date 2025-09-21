# Branch Guide

## Branch Structure

| Branch | Purpose | Key Technologies |
|--------|---------|------------------|
| `main` | Production-ready local version | TinyDB, CrewAI, Local processing |
| `develop` | Development/testing | Same as main + experimental features |
| `aws-native` | Full AWS services integration | DynamoDB, Lambda, S3, Step Functions |
| `sagemaker` | ML model hosting with SageMaker | SageMaker endpoints, DynamoDB |
| `aws-agentcore` | Bedrock Agents + AWS services | Bedrock Agents, DynamoDB, Lambda |

## Quick Switch Commands

```bash
# Local development
git checkout main

# AWS native services
git checkout aws-native

# SageMaker ML hosting
git checkout sagemaker

# Bedrock Agents
git checkout aws-agentcore

# Development/testing
git checkout develop
```

## Shared Components

All branches share:
- Core trade matching logic
- PDF processing utilities
- Data validation schemas
- Test frameworks

## Branch-Specific Components

### aws-native
- DynamoDB storage layer
- Lambda function handlers
- CloudFormation/CDK templates
- API Gateway integration

### sagemaker
- SageMaker model endpoints
- Custom inference containers
- Model training pipelines
- A/B testing framework

### aws-agentcore
- Bedrock Agent configurations
- Agent orchestration logic
- Knowledge base integration
- Action group definitions
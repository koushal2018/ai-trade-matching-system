---
inclusion: fileMatch
fileMatchPattern: "terraform/**/*.tf"
---

# AWS Infrastructure Guidelines

## Terraform Structure
```
terraform/
├── main.tf           # Provider config, backend
├── variables.tf      # Input variables
├── terraform.tfvars  # Variable values
├── dynamodb.tf       # DynamoDB tables
├── s3.tf             # S3 buckets
└── agentcore/        # AgentCore-specific resources
```

## Backend Configuration
- State stored in S3: `trade-matching-terraform-state`
- State locking via DynamoDB: `terraform-state-lock`
- Region: us-east-1

## Required Tags
All resources must include:
```hcl
default_tags {
  tags = {
    Environment = var.environment
    Project     = "trade-matching-system"
    ManagedBy   = "terraform"
  }
}
```

## DynamoDB Table Pattern
```hcl
resource "aws_dynamodb_table" "trades" {
  name         = "TradeData"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "trade_id"
  range_key    = "internal_reference"

  attribute {
    name = "trade_id"
    type = "S"
  }

  attribute {
    name = "internal_reference"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }
}
```

## Security Best Practices
- Enable encryption at rest for S3 and DynamoDB
- Use IAM roles instead of access keys
- Enable CloudTrail for audit logging
- Use VPC endpoints for private AWS service access
- Implement least-privilege access policies

## IAM Permissions Required
- S3: GetObject, PutObject, ListBucket
- DynamoDB: PutItem, GetItem, Scan, Query, DescribeTable
- Bedrock: InvokeModel
- SQS: SendMessage, ReceiveMessage, DeleteMessage
- CloudWatch: PutMetricData, CreateLogGroup, CreateLogStream

# AgentCore Gateway Configuration
# Note: AgentCore Gateway is a managed service configured via AWS CLI/Console
# These resources document the configuration that should be applied

# Local file to store AgentCore Gateway configuration
resource "local_file" "agentcore_gateway_config" {
  filename = "${path.module}/configs/agentcore_gateway_config.json"
  content = jsonencode({
    gateways = [
      {
        name        = "${var.project_name}-dynamodb-gateway-${var.environment}"
        description = "MCP Gateway for DynamoDB operations"
        target_type = "MCP_SERVER"
        mcp_config = {
          server_type = "dynamodb"
          operations = [
            "GetItem",
            "PutItem",
            "UpdateItem",
            "DeleteItem",
            "Query",
            "Scan",
            "BatchGetItem",
            "BatchWriteItem"
          ]
          resources = [
            aws_dynamodb_table.bank_trade_data.arn,
            aws_dynamodb_table.counterparty_trade_data.arn,
            aws_dynamodb_table.exceptions.arn,
            aws_dynamodb_table.agent_registry.arn
          ]
        }
        authentication = {
          type     = "IAM"
          role_arn = aws_iam_role.agentcore_gateway.arn
        }
        tags = {
          Component   = "AgentCore"
          Environment = var.environment
          Purpose     = "DynamoDB"
        }
      },
      {
        name        = "${var.project_name}-s3-gateway-${var.environment}"
        description = "MCP Gateway for S3 operations"
        target_type = "MCP_SERVER"
        mcp_config = {
          server_type = "s3"
          operations = [
            "GetObject",
            "PutObject",
            "DeleteObject",
            "ListObjects",
            "HeadObject"
          ]
          resources = [
            aws_s3_bucket.agentcore_trade_documents.arn,
            "${aws_s3_bucket.agentcore_trade_documents.arn}/*"
          ]
        }
        authentication = {
          type     = "IAM"
          role_arn = aws_iam_role.agentcore_gateway.arn
        }
        tags = {
          Component   = "AgentCore"
          Environment = var.environment
          Purpose     = "S3"
        }
      },
      {
        name        = "${var.project_name}-custom-ops-gateway-${var.environment}"
        description = "MCP Gateway for custom Lambda operations"
        target_type = "LAMBDA"
        lambda_config = {
          function_arn    = aws_lambda_function.custom_operations.arn
          timeout_seconds = 60
        }
        authentication = {
          type     = "IAM"
          role_arn = aws_iam_role.agentcore_gateway.arn
        }
        tags = {
          Component   = "AgentCore"
          Environment = var.environment
          Purpose     = "CustomOperations"
        }
      }
    ]
  })
}

# Lambda function for custom operations
resource "aws_lambda_function" "custom_operations" {
  filename      = "${path.module}/lambda/custom_operations.zip"
  function_name = "${var.project_name}-custom-operations-${var.environment}"
  role          = aws_iam_role.lambda_custom_operations.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = 60
  memory_size   = 512

  environment {
    variables = {
      ENVIRONMENT  = var.environment
      PROJECT_NAME = var.project_name
    }
  }

  tags = merge(var.tags, {
    Name        = "Custom Operations Lambda"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# IAM role for custom operations Lambda
resource "aws_iam_role" "lambda_custom_operations" {
  name = "${var.project_name}-lambda-custom-ops-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(var.tags, {
    Name        = "Lambda Custom Operations Role"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# Attach policies to custom operations Lambda role
resource "aws_iam_role_policy_attachment" "lambda_custom_ops_s3" {
  role       = aws_iam_role.lambda_custom_operations.name
  policy_arn = aws_iam_policy.agentcore_s3_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_custom_ops_dynamodb" {
  role       = aws_iam_role.lambda_custom_operations.name
  policy_arn = aws_iam_policy.agentcore_dynamodb_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_custom_ops_cloudwatch" {
  role       = aws_iam_role.lambda_custom_operations.name
  policy_arn = aws_iam_policy.agentcore_cloudwatch_logs.arn
}

# Create deployment script for AgentCore Gateway
resource "local_file" "deploy_agentcore_gateway_script" {
  filename = "${path.module}/scripts/deploy_agentcore_gateway.sh"
  content  = <<-EOT
#!/bin/bash
set -e

echo "Deploying AgentCore Gateway resources..."

# DynamoDB Gateway
echo "Creating DynamoDB MCP Gateway..."
aws bedrock-agent create-gateway \
  --name "${var.project_name}-dynamodb-gateway-${var.environment}" \
  --description "MCP Gateway for DynamoDB operations" \
  --target-type MCP_SERVER \
  --mcp-server-type dynamodb \
  --authentication-type IAM \
  --role-arn ${aws_iam_role.agentcore_gateway.arn} \
  --region ${var.aws_region} \
  --tags Component=AgentCore,Environment=${var.environment},Purpose=DynamoDB

# S3 Gateway
echo "Creating S3 MCP Gateway..."
aws bedrock-agent create-gateway \
  --name "${var.project_name}-s3-gateway-${var.environment}" \
  --description "MCP Gateway for S3 operations" \
  --target-type MCP_SERVER \
  --mcp-server-type s3 \
  --authentication-type IAM \
  --role-arn ${aws_iam_role.agentcore_gateway.arn} \
  --region ${var.aws_region} \
  --tags Component=AgentCore,Environment=${var.environment},Purpose=S3

# Custom Operations Gateway (Lambda)
echo "Creating Custom Operations Gateway..."
aws bedrock-agent create-gateway \
  --name "${var.project_name}-custom-ops-gateway-${var.environment}" \
  --description "MCP Gateway for custom Lambda operations" \
  --target-type LAMBDA \
  --lambda-function-arn ${aws_lambda_function.custom_operations.arn} \
  --authentication-type IAM \
  --role-arn ${aws_iam_role.agentcore_gateway.arn} \
  --region ${var.aws_region} \
  --tags Component=AgentCore,Environment=${var.environment},Purpose=CustomOperations

echo "AgentCore Gateway resources deployed successfully!"
EOT

  file_permission = "0755"
}

# Create README for AgentCore Gateway setup
resource "local_file" "agentcore_gateway_readme" {
  filename = "${path.module}/configs/AGENTCORE_GATEWAY_README.md"
  content  = <<-EOT
# AgentCore Gateway Setup

This directory contains configuration for AgentCore Gateway resources.

## Gateway Resources

### 1. DynamoDB MCP Gateway
- **Name**: ${var.project_name}-dynamodb-gateway-${var.environment}
- **Target Type**: MCP_SERVER
- **Purpose**: Expose DynamoDB operations as MCP tools
- **Operations**: GetItem, PutItem, UpdateItem, DeleteItem, Query, Scan, BatchGetItem, BatchWriteItem
- **Resources**:
  - ${aws_dynamodb_table.bank_trade_data.name}
  - ${aws_dynamodb_table.counterparty_trade_data.name}
  - ${aws_dynamodb_table.exceptions.name}
  - ${aws_dynamodb_table.agent_registry.name}

### 2. S3 MCP Gateway
- **Name**: ${var.project_name}-s3-gateway-${var.environment}
- **Target Type**: MCP_SERVER
- **Purpose**: Expose S3 operations as MCP tools
- **Operations**: GetObject, PutObject, DeleteObject, ListObjects, HeadObject
- **Resources**:
  - ${aws_s3_bucket.agentcore_trade_documents.id}

### 3. Custom Operations Gateway
- **Name**: ${var.project_name}-custom-ops-gateway-${var.environment}
- **Target Type**: LAMBDA
- **Purpose**: Expose custom business logic as MCP tools
- **Lambda Function**: ${aws_lambda_function.custom_operations.function_name}

## Deployment

### Using AWS CLI (Manual)

Run the deployment script:
```bash
cd ${path.module}/scripts
./deploy_agentcore_gateway.sh
```

### Using AgentCore CLI (Recommended)

Once AgentCore CLI is available, use:
```bash
agentcore gateway create --config ${path.module}/configs/agentcore_gateway_config.json
```

## Verification

List all gateways:
```bash
aws bedrock-agent list-gateways --region ${var.aws_region}
```

Get details of a specific gateway:
```bash
aws bedrock-agent describe-gateway \
  --gateway-id <gateway-id> \
  --region ${var.aws_region}
```

## Integration with Agents

Agents can access gateway tools using the MCP protocol:

### DynamoDB Operations
```python
from bedrock_agentcore import Gateway

dynamodb_gateway = Gateway(name="${var.project_name}-dynamodb-gateway-${var.environment}")

# Put item
dynamodb_gateway.invoke_tool("PutItem", {
    "TableName": "${aws_dynamodb_table.bank_trade_data.name}",
    "Item": {
        "Trade_ID": {"S": "GCS382857"},
        "TRADE_SOURCE": {"S": "BANK"},
        "notional": {"N": "1000000"}
    }
})

# Query items
result = dynamodb_gateway.invoke_tool("Query", {
    "TableName": "${aws_dynamodb_table.bank_trade_data.name}",
    "KeyConditionExpression": "Trade_ID = :trade_id",
    "ExpressionAttributeValues": {
        ":trade_id": {"S": "GCS382857"}
    }
})
```

### S3 Operations
```python
s3_gateway = Gateway(name="${var.project_name}-s3-gateway-${var.environment}")

# Put object
s3_gateway.invoke_tool("PutObject", {
    "Bucket": "${aws_s3_bucket.agentcore_trade_documents.id}",
    "Key": "extracted/BANK/trade_123.json",
    "Body": json.dumps(trade_data)
})

# Get object
result = s3_gateway.invoke_tool("GetObject", {
    "Bucket": "${aws_s3_bucket.agentcore_trade_documents.id}",
    "Key": "extracted/BANK/trade_123.json"
})
```

### Custom Operations
```python
custom_gateway = Gateway(name="${var.project_name}-custom-ops-gateway-${var.environment}")

# Invoke custom operation
result = custom_gateway.invoke_tool("CustomOperation", {
    "operation": "validate_trade",
    "trade_id": "GCS382857"
})
```

## Authentication

All gateways use IAM authentication with the AgentCore Gateway role:
- **Role ARN**: ${aws_iam_role.agentcore_gateway.arn}

Agents must have permissions to assume this role or have equivalent permissions.

## Monitoring

Monitor gateway usage:
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/BedrockAgent \
  --metric-name GatewayInvocations \
  --dimensions Name=GatewayName,Value=${var.project_name}-dynamodb-gateway-${var.environment} \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-31T23:59:59Z \
  --period 3600 \
  --statistics Sum \
  --region ${var.aws_region}
```

## Cleanup

To delete gateway resources:
```bash
aws bedrock-agent delete-gateway \
  --gateway-id <gateway-id> \
  --region ${var.aws_region}
```
EOT
}

# Create placeholder Lambda function code
resource "local_file" "custom_operations_lambda" {
  filename = "${path.module}/lambda/custom_operations.py"
  content  = <<-EOT
import json
import boto3
import os

def handler(event, context):
    """
    Custom operations Lambda function for AgentCore Gateway.
    
    This function handles custom business logic that can be invoked
    by agents through the AgentCore Gateway.
    """
    
    operation = event.get('operation')
    
    if operation == 'validate_trade':
        return validate_trade(event)
    elif operation == 'compute_match_score':
        return compute_match_score(event)
    elif operation == 'classify_exception':
        return classify_exception(event)
    else:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Unknown operation: {operation}'})
        }

def validate_trade(event):
    """Validate trade data against business rules."""
    trade_id = event.get('trade_id')
    
    # Add validation logic here
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'valid': True,
            'trade_id': trade_id
        })
    }

def compute_match_score(event):
    """Compute match score between two trades."""
    bank_trade = event.get('bank_trade')
    cp_trade = event.get('counterparty_trade')
    
    # Add scoring logic here
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'match_score': 0.85,
            'classification': 'MATCHED'
        })
    }

def classify_exception(event):
    """Classify exception severity and routing."""
    exception_data = event.get('exception')
    
    # Add classification logic here
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'severity': 'MEDIUM',
            'routing': 'OPS_DESK'
        })
    }
EOT
}

# Outputs
output "agentcore_gateway_config_file" {
  description = "Path to AgentCore Gateway configuration file"
  value       = local_file.agentcore_gateway_config.filename
}

output "agentcore_gateway_deployment_script" {
  description = "Path to AgentCore Gateway deployment script"
  value       = local_file.deploy_agentcore_gateway_script.filename
}

output "custom_operations_lambda_arn" {
  description = "ARN of the custom operations Lambda function"
  value       = aws_lambda_function.custom_operations.arn
}

output "agentcore_gateway_names" {
  description = "List of AgentCore Gateway names"
  value = [
    "${var.project_name}-dynamodb-gateway-${var.environment}",
    "${var.project_name}-s3-gateway-${var.environment}",
    "${var.project_name}-custom-ops-gateway-${var.environment}"
  ]
}

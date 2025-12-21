# IAM Role for AgentCore Runtime Execution (Default Service Role)
resource "aws_iam_role" "agentcore_runtime_default_service_role" {
  name = "AmazonBedrockAgentCoreRuntimeDefaultServiceRole-${random_string.role_suffix.result}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "bedrock-agentcore.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(var.tags, {
    Name        = "AgentCore Runtime Default Service Role"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# Random string for role suffix to avoid conflicts
resource "random_string" "role_suffix" {
  length  = 5
  special = false
  upper   = false
}

# IAM Role for AgentCore Runtime Execution (Custom)
resource "aws_iam_role" "agentcore_runtime_execution" {
  name = "${var.project_name}-agentcore-runtime-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = [
            "bedrock.amazonaws.com",
            "bedrock-agentcore.amazonaws.com",
            "lambda.amazonaws.com"
          ]
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(var.tags, {
    Name        = "AgentCore Runtime Execution Role"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# IAM Policy for AgentCore Runtime - S3 Access
resource "aws_iam_policy" "agentcore_s3_access" {
  name        = "${var.project_name}-agentcore-s3-access-${var.environment}"
  description = "Policy for AgentCore agents to access S3 buckets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.agentcore_trade_documents.arn,
          "${aws_s3_bucket.agentcore_trade_documents.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.agentcore_trade_documents.arn
        ]
      }
    ]
  })

  tags = merge(var.tags, {
    Name        = "AgentCore S3 Access Policy"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# IAM Policy for AgentCore Runtime - DynamoDB Access
resource "aws_iam_policy" "agentcore_dynamodb_access" {
  name        = "${var.project_name}-agentcore-dynamodb-access-${var.environment}"
  description = "Policy for AgentCore agents to access DynamoDB tables"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = [
          aws_dynamodb_table.bank_trade_data.arn,
          "${aws_dynamodb_table.bank_trade_data.arn}/index/*",
          aws_dynamodb_table.counterparty_trade_data.arn,
          "${aws_dynamodb_table.counterparty_trade_data.arn}/index/*",
          aws_dynamodb_table.exceptions.arn,
          "${aws_dynamodb_table.exceptions.arn}/index/*",
          aws_dynamodb_table.agent_registry.arn,
          "${aws_dynamodb_table.agent_registry.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:Encrypt",
          "kms:GenerateDataKey"
        ]
        Resource = [
          aws_kms_key.dynamodb.arn
        ]
      }
    ]
  })

  tags = merge(var.tags, {
    Name        = "AgentCore DynamoDB Access Policy"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# IAM Policy for AgentCore Runtime - SQS Access
resource "aws_iam_policy" "agentcore_sqs_access" {
  name        = "${var.project_name}-agentcore-sqs-access-${var.environment}"
  description = "Policy for AgentCore agents to access SQS queues"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:GetQueueUrl"
        ]
        Resource = [
          aws_sqs_queue.document_upload_events.arn,
          aws_sqs_queue.extraction_events.arn,
          aws_sqs_queue.matching_events.arn,
          aws_sqs_queue.exception_events.arn,
          aws_sqs_queue.hitl_review_queue.arn,
          aws_sqs_queue.ops_desk_queue.arn,
          aws_sqs_queue.senior_ops_queue.arn,
          aws_sqs_queue.compliance_queue.arn,
          aws_sqs_queue.engineering_queue.arn,
          aws_sqs_queue.orchestrator_monitoring_queue.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = [
          aws_sns_topic.agent_events_fanout.arn
        ]
      }
    ]
  })

  tags = merge(var.tags, {
    Name        = "AgentCore SQS Access Policy"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# IAM Policy for AgentCore Runtime - Bedrock Access
resource "aws_iam_policy" "agentcore_bedrock_access" {
  name        = "${var.project_name}-agentcore-bedrock-access-${var.environment}"
  description = "Policy for AgentCore agents to access AWS Bedrock"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-sonnet-4*"
        ]
      }
    ]
  })

  tags = merge(var.tags, {
    Name        = "AgentCore Bedrock Access Policy"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# IAM Policy for AgentCore Runtime - CloudWatch Logs
resource "aws_iam_policy" "agentcore_cloudwatch_logs" {
  name        = "${var.project_name}-agentcore-cloudwatch-logs-${var.environment}"
  description = "Policy for AgentCore agents to write CloudWatch logs"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "arn:aws:logs:${var.aws_region}:*:log-group:/aws/agentcore/${var.project_name}/*"
        ]
      }
    ]
  })

  tags = merge(var.tags, {
    Name        = "AgentCore CloudWatch Logs Policy"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# Attach policies to AgentCore Runtime Default Service Role
resource "aws_iam_role_policy_attachment" "agentcore_default_s3" {
  role       = aws_iam_role.agentcore_runtime_default_service_role.name
  policy_arn = aws_iam_policy.agentcore_s3_access.arn
}

resource "aws_iam_role_policy_attachment" "agentcore_default_dynamodb" {
  role       = aws_iam_role.agentcore_runtime_default_service_role.name
  policy_arn = aws_iam_policy.agentcore_dynamodb_access.arn
}

resource "aws_iam_role_policy_attachment" "agentcore_default_sqs" {
  role       = aws_iam_role.agentcore_runtime_default_service_role.name
  policy_arn = aws_iam_policy.agentcore_sqs_access.arn
}

resource "aws_iam_role_policy_attachment" "agentcore_default_bedrock" {
  role       = aws_iam_role.agentcore_runtime_default_service_role.name
  policy_arn = aws_iam_policy.agentcore_bedrock_access.arn
}

resource "aws_iam_role_policy_attachment" "agentcore_default_cloudwatch" {
  role       = aws_iam_role.agentcore_runtime_default_service_role.name
  policy_arn = aws_iam_policy.agentcore_cloudwatch_logs.arn
}

# Attach AWS managed policy for AgentCore Runtime
resource "aws_iam_role_policy_attachment" "agentcore_default_managed" {
  role       = aws_iam_role.agentcore_runtime_default_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonBedrockAgentCoreRuntimeServiceRolePolicy"
}

# Attach policies to AgentCore Runtime Execution Role
resource "aws_iam_role_policy_attachment" "agentcore_s3" {
  role       = aws_iam_role.agentcore_runtime_execution.name
  policy_arn = aws_iam_policy.agentcore_s3_access.arn
}

resource "aws_iam_role_policy_attachment" "agentcore_dynamodb" {
  role       = aws_iam_role.agentcore_runtime_execution.name
  policy_arn = aws_iam_policy.agentcore_dynamodb_access.arn
}

resource "aws_iam_role_policy_attachment" "agentcore_sqs" {
  role       = aws_iam_role.agentcore_runtime_execution.name
  policy_arn = aws_iam_policy.agentcore_sqs_access.arn
}

resource "aws_iam_role_policy_attachment" "agentcore_bedrock" {
  role       = aws_iam_role.agentcore_runtime_execution.name
  policy_arn = aws_iam_policy.agentcore_bedrock_access.arn
}

resource "aws_iam_role_policy_attachment" "agentcore_cloudwatch" {
  role       = aws_iam_role.agentcore_runtime_execution.name
  policy_arn = aws_iam_policy.agentcore_cloudwatch_logs.arn
}

# IAM Role for AgentCore Gateway
resource "aws_iam_role" "agentcore_gateway" {
  name = "${var.project_name}-agentcore-gateway-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(var.tags, {
    Name        = "AgentCore Gateway Role"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# Attach policies to AgentCore Gateway Role
resource "aws_iam_role_policy_attachment" "gateway_s3" {
  role       = aws_iam_role.agentcore_gateway.name
  policy_arn = aws_iam_policy.agentcore_s3_access.arn
}

resource "aws_iam_role_policy_attachment" "gateway_dynamodb" {
  role       = aws_iam_role.agentcore_gateway.name
  policy_arn = aws_iam_policy.agentcore_dynamodb_access.arn
}

# IAM Role for Lambda Execution (PDF Adapter Agent)
resource "aws_iam_role" "lambda_pdf_adapter" {
  name = "${var.project_name}-lambda-pdf-adapter-${var.environment}"

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
    Name        = "Lambda PDF Adapter Role"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# Attach policies to Lambda PDF Adapter Role
resource "aws_iam_role_policy_attachment" "lambda_pdf_adapter_s3" {
  role       = aws_iam_role.lambda_pdf_adapter.name
  policy_arn = aws_iam_policy.agentcore_s3_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_pdf_adapter_sqs" {
  role       = aws_iam_role.lambda_pdf_adapter.name
  policy_arn = aws_iam_policy.agentcore_sqs_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_pdf_adapter_bedrock" {
  role       = aws_iam_role.lambda_pdf_adapter.name
  policy_arn = aws_iam_policy.agentcore_bedrock_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_pdf_adapter_cloudwatch" {
  role       = aws_iam_role.lambda_pdf_adapter.name
  policy_arn = aws_iam_policy.agentcore_cloudwatch_logs.arn
}

# IAM Role for Lambda Execution (Trade Extraction Agent)
resource "aws_iam_role" "lambda_trade_extraction" {
  name = "${var.project_name}-lambda-trade-extraction-${var.environment}"

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
    Name        = "Lambda Trade Extraction Role"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# Attach policies to Lambda Trade Extraction Role
resource "aws_iam_role_policy_attachment" "lambda_trade_extraction_s3" {
  role       = aws_iam_role.lambda_trade_extraction.name
  policy_arn = aws_iam_policy.agentcore_s3_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_trade_extraction_dynamodb" {
  role       = aws_iam_role.lambda_trade_extraction.name
  policy_arn = aws_iam_policy.agentcore_dynamodb_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_trade_extraction_sqs" {
  role       = aws_iam_role.lambda_trade_extraction.name
  policy_arn = aws_iam_policy.agentcore_sqs_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_trade_extraction_bedrock" {
  role       = aws_iam_role.lambda_trade_extraction.name
  policy_arn = aws_iam_policy.agentcore_bedrock_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_trade_extraction_cloudwatch" {
  role       = aws_iam_role.lambda_trade_extraction.name
  policy_arn = aws_iam_policy.agentcore_cloudwatch_logs.arn
}

# IAM Role for Lambda Execution (Trade Matching Agent)
resource "aws_iam_role" "lambda_trade_matching" {
  name = "${var.project_name}-lambda-trade-matching-${var.environment}"

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
    Name        = "Lambda Trade Matching Role"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# Attach policies to Lambda Trade Matching Role
resource "aws_iam_role_policy_attachment" "lambda_trade_matching_s3" {
  role       = aws_iam_role.lambda_trade_matching.name
  policy_arn = aws_iam_policy.agentcore_s3_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_trade_matching_dynamodb" {
  role       = aws_iam_role.lambda_trade_matching.name
  policy_arn = aws_iam_policy.agentcore_dynamodb_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_trade_matching_sqs" {
  role       = aws_iam_role.lambda_trade_matching.name
  policy_arn = aws_iam_policy.agentcore_sqs_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_trade_matching_bedrock" {
  role       = aws_iam_role.lambda_trade_matching.name
  policy_arn = aws_iam_policy.agentcore_bedrock_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_trade_matching_cloudwatch" {
  role       = aws_iam_role.lambda_trade_matching.name
  policy_arn = aws_iam_policy.agentcore_cloudwatch_logs.arn
}

# IAM Role for Lambda Execution (Exception Management Agent)
resource "aws_iam_role" "lambda_exception_management" {
  name = "${var.project_name}-lambda-exception-mgmt-${var.environment}"

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
    Name        = "Lambda Exception Management Role"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# Attach policies to Lambda Exception Management Role
resource "aws_iam_role_policy_attachment" "lambda_exception_management_dynamodb" {
  role       = aws_iam_role.lambda_exception_management.name
  policy_arn = aws_iam_policy.agentcore_dynamodb_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_exception_management_sqs" {
  role       = aws_iam_role.lambda_exception_management.name
  policy_arn = aws_iam_policy.agentcore_sqs_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_exception_management_bedrock" {
  role       = aws_iam_role.lambda_exception_management.name
  policy_arn = aws_iam_policy.agentcore_bedrock_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_exception_management_cloudwatch" {
  role       = aws_iam_role.lambda_exception_management.name
  policy_arn = aws_iam_policy.agentcore_cloudwatch_logs.arn
}

# IAM Role for Lambda Execution (Orchestrator Agent)
resource "aws_iam_role" "lambda_orchestrator" {
  name = "${var.project_name}-lambda-orchestrator-${var.environment}"

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
    Name        = "Lambda Orchestrator Role"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# Attach policies to Lambda Orchestrator Role
resource "aws_iam_role_policy_attachment" "lambda_orchestrator_dynamodb" {
  role       = aws_iam_role.lambda_orchestrator.name
  policy_arn = aws_iam_policy.agentcore_dynamodb_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_orchestrator_sqs" {
  role       = aws_iam_role.lambda_orchestrator.name
  policy_arn = aws_iam_policy.agentcore_sqs_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_orchestrator_bedrock" {
  role       = aws_iam_role.lambda_orchestrator.name
  policy_arn = aws_iam_policy.agentcore_bedrock_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_orchestrator_cloudwatch" {
  role       = aws_iam_role.lambda_orchestrator.name
  policy_arn = aws_iam_policy.agentcore_cloudwatch_logs.arn
}

# Outputs
output "agentcore_runtime_default_service_role_arn" {
  description = "ARN of the AgentCore Runtime default service role"
  value       = aws_iam_role.agentcore_runtime_default_service_role.arn
}

output "agentcore_runtime_execution_role_arn" {
  description = "ARN of the AgentCore Runtime execution role"
  value       = aws_iam_role.agentcore_runtime_execution.arn
}

output "agentcore_gateway_role_arn" {
  description = "ARN of the AgentCore Gateway role"
  value       = aws_iam_role.agentcore_gateway.arn
}

output "lambda_pdf_adapter_role_arn" {
  description = "ARN of the Lambda PDF Adapter role"
  value       = aws_iam_role.lambda_pdf_adapter.arn
}

output "lambda_trade_extraction_role_arn" {
  description = "ARN of the Lambda Trade Extraction role"
  value       = aws_iam_role.lambda_trade_extraction.arn
}

output "lambda_trade_matching_role_arn" {
  description = "ARN of the Lambda Trade Matching role"
  value       = aws_iam_role.lambda_trade_matching.arn
}

output "lambda_exception_management_role_arn" {
  description = "ARN of the Lambda Exception Management role"
  value       = aws_iam_role.lambda_exception_management.arn
}

output "lambda_orchestrator_role_arn" {
  description = "ARN of the Lambda Orchestrator role"
  value       = aws_iam_role.lambda_orchestrator.arn
}

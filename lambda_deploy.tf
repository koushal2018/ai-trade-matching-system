terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Lambda function
resource "aws_lambda_function" "s3_event_processor" {
  filename         = "lambda/s3_event_processor.zip"
  function_name    = "trade-s3-event-processor"
  role            = aws_iam_role.lambda.arn
  handler         = "s3_event_processor.lambda_handler"
  runtime         = "python3.11"
  timeout         = 60
  memory_size     = 512

  environment {
    variables = {
      EKS_API_ENDPOINT = "http://a1bd3de0ceb044d48b7c0b5d1e2a1dcf-1158084584.us-east-1.elb.amazonaws.com"
      AWS_REGION      = "us-east-1"
    }
  }

  tags = {
    Environment = "production"
    Project     = "trade-matching-system"
    ManagedBy   = "terraform"
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_cloudwatch_log_group.lambda,
  ]
}

# IAM role for Lambda
resource "aws_iam_role" "lambda" {
  name = "trade-s3-event-processor-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy attachment for basic Lambda execution
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda.name
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/trade-s3-event-processor"
  retention_in_days = 30

  tags = {
    Environment = "production"
    Project     = "trade-matching-system"
    ManagedBy   = "terraform"
  }
}

# S3 bucket notification to trigger Lambda
resource "aws_s3_bucket_notification" "trade_documents" {
  bucket = "fab-otc-reconciliation-deployment"

  lambda_function {
    id                  = "ProcessBankPDFs"
    lambda_function_arn = aws_lambda_function.s3_event_processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "BANK/"
    filter_suffix       = ".pdf"
  }

  lambda_function {
    id                  = "ProcessCounterpartyPDFs"
    lambda_function_arn = aws_lambda_function.s3_event_processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "COUNTERPARTY/"
    filter_suffix       = ".pdf"
  }

  depends_on = [aws_lambda_permission.allow_bucket]
}

# Lambda permission to allow S3 to invoke the function
resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.s3_event_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::fab-otc-reconciliation-deployment"
}

# Output
output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.s3_event_processor.arn
}
# Lambda execution role
resource "aws_iam_role" "lambda_execution_simple" {
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

# Lambda execution policy
resource "aws_iam_role_policy" "lambda_execution_simple" {
  name = "trade-s3-event-processor-policy"
  role = aws_iam_role.lambda_execution_simple.id

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
        Resource = "arn:aws:logs:us-east-1:401552979575:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::fab-otc-reconciliation-deployment",
          "arn:aws:s3:::fab-otc-reconciliation-deployment/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter"
        ]
        Resource = "arn:aws:ssm:us-east-1:401552979575:parameter/trade-matching/eks-api-endpoint"
      }
    ]
  })
}

# Lambda function
resource "aws_lambda_function" "s3_event_processor_simple" {
  filename         = "../lambda/s3_event_processor.zip"
  function_name    = "trade-s3-event-processor"
  role            = aws_iam_role.lambda_execution_simple.arn
  handler         = "s3_event_processor.lambda_handler"
  source_code_hash = filebase64sha256("../lambda/s3_event_processor.zip")
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 256

  environment {
    variables = {
      EKS_API_ENDPOINT_PARAM = "/trade-matching/eks-api-endpoint"
      MAX_FILE_SIZE         = "104857600"  # 100MB
    }
  }

  tags = {
    Name = "S3 Event Processor"
    Type = "Lambda"
  }

  depends_on = [
    aws_iam_role_policy.lambda_execution_simple,
    aws_cloudwatch_log_group.lambda_simple
  ]
}

# Lambda permission for S3
resource "aws_lambda_permission" "allow_s3_simple" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.s3_event_processor_simple.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::fab-otc-reconciliation-deployment"
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_simple" {
  name              = "/aws/lambda/trade-s3-event-processor"
  retention_in_days = 30

  tags = {
    Name = "Lambda Logs"
    Type = "Logs"
  }
}

# SSM Parameter for EKS API Endpoint
resource "aws_ssm_parameter" "eks_api_endpoint_simple" {
  name  = "/trade-matching/eks-api-endpoint"
  type  = "String"
  value = "http://a73da16d612d4a49b03da519479fc1e-f54774935b2b938a.elb.us-east-1.amazonaws.com"

  tags = {
    Name = "EKS API Endpoint"
    Type = "Parameter"
  }
}

# S3 Event Notification Configuration (using existing bucket)
resource "aws_s3_bucket_notification" "trade_documents_simple" {
  bucket = "fab-otc-reconciliation-deployment"

  lambda_function {
    lambda_function_arn = aws_lambda_function.s3_event_processor_simple.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "BANK/"
    filter_suffix       = ".pdf"
  }

  lambda_function {
    lambda_function_arn = aws_lambda_function.s3_event_processor_simple.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "COUNTERPARTY/"
    filter_suffix       = ".pdf"
  }

  depends_on = [aws_lambda_permission.allow_s3_simple]
}
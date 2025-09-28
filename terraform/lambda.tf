# Lambda execution role
resource "aws_iam_role" "lambda_execution" {
  name = "${var.lambda_function_name}-role"

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
resource "aws_iam_role_policy" "lambda_execution" {
  name = "${var.lambda_function_name}-policy"
  role = aws_iam_role.lambda_execution.id

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
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.trade_documents.arn,
          "${aws_s3_bucket.trade_documents.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter"
        ]
        Resource = aws_ssm_parameter.eks_api_endpoint.arn
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = aws_sqs_queue.dlq.arn
      }
    ]
  })
}

# Attach AWS managed policy for VPC access (if Lambda is in VPC)
resource "aws_iam_role_policy_attachment" "lambda_vpc_execution" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# Lambda function
resource "aws_lambda_function" "s3_event_processor" {
  filename         = "${path.module}/../lambda/s3_event_processor.zip"
  function_name    = var.lambda_function_name
  role            = aws_iam_role.lambda_execution.arn
  handler         = "s3_event_processor.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/../lambda/s3_event_processor.zip")
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory

  environment {
    variables = {
      EKS_API_ENDPOINT_PARAM = aws_ssm_parameter.eks_api_endpoint.name
      DLQ_NAME              = aws_sqs_queue.dlq.name
      MAX_FILE_SIZE         = "104857600"  # 100MB
    }
  }

  dead_letter_config {
    target_arn = aws_sqs_queue.dlq.arn
  }

  tags = merge(var.tags, {
    Name = "S3 Event Processor"
    Type = "Lambda"
  })

  depends_on = [
    aws_iam_role_policy.lambda_execution,
    aws_cloudwatch_log_group.lambda
  ]
}

# Lambda permission for S3
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.s3_event_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.trade_documents.arn
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.lambda_function_name}"
  retention_in_days = 30

  tags = merge(var.tags, {
    Name = "Lambda Logs"
    Type = "Logs"
  })
}

# Dead Letter Queue for failed events
resource "aws_sqs_queue" "dlq" {
  name                      = "${var.lambda_function_name}-dlq"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 1209600  # 14 days
  receive_wait_time_seconds = 0

  tags = merge(var.tags, {
    Name = "Lambda DLQ"
    Type = "Queue"
  })
}

# SSM Parameter for EKS API Endpoint
resource "aws_ssm_parameter" "eks_api_endpoint" {
  name  = "/trade-matching/eks-api-endpoint"
  type  = "String"
  value = "http://a73da16d612d4a49b03da519479fc1e-f54774935b2b938a.elb.us-east-1.amazonaws.com"

  tags = merge(var.tags, {
    Name = "EKS API Endpoint"
    Type = "Parameter"
  })
}
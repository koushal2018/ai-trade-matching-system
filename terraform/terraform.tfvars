# Production environment configuration
aws_region = "us-east-1"
environment = "production"
project_name = "trade-matching-system"

# Using existing S3 bucket
s3_bucket_name = "fab-otc-reconciliation-deployment"

# Using existing DynamoDB tables
dynamodb_bank_table = "BankTradeData"
dynamodb_counterparty_table = "CounterpartyTradeData"

# EKS Configuration (will create if not exists)
eks_cluster_name = "trade-matching-eks"

# ECR Configuration (already created)
ecr_repository_name = "trade-matching-system"

# Notification configuration
notification_emails = []

# Tags
tags = {
  Owner = "koushald"
  CostCenter = "trading-operations"
  Application = "trade-matching"
}
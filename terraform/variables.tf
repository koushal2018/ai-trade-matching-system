variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "trade-matching-system"
}

variable "eks_cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "trade-matching-eks"
}

# S3 Configuration
variable "s3_bucket_name" {
  description = "Name of the S3 bucket for trade documents"
  type        = string
  default     = "trade-documents-production"
}

variable "s3_lifecycle_days" {
  description = "Number of days to retain processed documents"
  type        = number
  default     = 90
}

# DynamoDB Configuration
variable "dynamodb_bank_table" {
  description = "Name of DynamoDB table for bank trades"
  type        = string
  default     = "BankTradeData"
}

variable "dynamodb_counterparty_table" {
  description = "Name of DynamoDB table for counterparty trades"
  type        = string
  default     = "CounterpartyTradeData"
}

variable "dynamodb_billing_mode" {
  description = "DynamoDB billing mode (PROVISIONED or PAY_PER_REQUEST)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

# Lambda Configuration
variable "lambda_function_name" {
  description = "Name of the Lambda function for S3 event processing"
  type        = string
  default     = "trade-s3-event-processor"
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 60
}

variable "lambda_memory" {
  description = "Lambda function memory in MB"
  type        = number
  default     = 512
}

# SNS Configuration
variable "sns_topic_name" {
  description = "Name of SNS topic for notifications"
  type        = string
  default     = "trade-processing-notifications"
}

variable "notification_emails" {
  description = "List of email addresses for notifications"
  type        = list(string)
  default     = []
}

# ECR Configuration
variable "ecr_repository_name" {
  description = "Name of ECR repository for Docker images"
  type        = string
  default     = "trade-matching-system"
}

# CloudFront Configuration
variable "cloudfront_price_class" {
  description = "CloudFront price class (PriceClass_All, PriceClass_200, PriceClass_100)"
  type        = string
  default     = "PriceClass_100"
}

# Tags
variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}
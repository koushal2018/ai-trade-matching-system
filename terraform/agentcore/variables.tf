# Variables for AgentCore Infrastructure

variable "aws_region" {
  description = "AWS region for AgentCore resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "production"

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "trade-matching-system"
}

# S3 Configuration
variable "s3_lifecycle_days" {
  description = "Number of days to retain documents before transitioning to cheaper storage"
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

# Cognito Configuration
variable "web_portal_callback_urls" {
  description = "Callback URLs for Web Portal OAuth"
  type        = list(string)
  default = [
    "http://localhost:3000/callback",
    "https://trade-matching-portal.example.com/callback"
  ]
}

variable "web_portal_logout_urls" {
  description = "Logout URLs for Web Portal OAuth"
  type        = list(string)
  default = [
    "http://localhost:3000/logout",
    "https://trade-matching-portal.example.com/logout"
  ]
}

# Alerting Configuration
variable "alert_emails" {
  description = "Email addresses for CloudWatch alerts"
  type        = list(string)
  default     = []
}

# Billing Alarm Configuration
variable "billing_alert_emails" {
  description = "Email addresses for billing alerts (separate from operational alerts)"
  type        = list(string)
  default     = []
}

variable "billing_alarm_threshold" {
  description = "Monthly billing alarm threshold in USD"
  type        = number
  default     = 500
}

variable "enable_service_billing_alarms" {
  description = "Enable per-service billing alarms (S3, DynamoDB, Bedrock, CloudWatch)"
  type        = bool
  default     = true
}

variable "enable_aws_budget" {
  description = "Enable AWS Budget for cost tracking"
  type        = bool
  default     = true
}

variable "enable_cost_anomaly_detection" {
  description = "Enable AWS Cost Anomaly Detection"
  type        = bool
  default     = false
}

# Tags
variable "tags" {
  description = "Additional tags for all resources"
  type        = map(string)
  default     = {}
}

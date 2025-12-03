# AgentCore Infrastructure - Main Configuration
# This module provisions all AWS infrastructure for the AgentCore migration

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
  }

  backend "s3" {
    bucket         = "trade-matching-terraform-state"
    key            = "agentcore/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "terraform"
      Component   = "AgentCore"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

# Local variables
locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
}

# Outputs
output "summary" {
  description = "Summary of deployed AgentCore infrastructure"
  value = {
    account_id  = local.account_id
    region      = local.region
    environment = var.environment

    s3 = {
      bucket_name = aws_s3_bucket.agentcore_trade_documents.id
      bucket_arn  = aws_s3_bucket.agentcore_trade_documents.arn
    }

    dynamodb = {
      bank_trade_table         = aws_dynamodb_table.bank_trade_data.name
      counterparty_trade_table = aws_dynamodb_table.counterparty_trade_data.name
      exceptions_table         = aws_dynamodb_table.exceptions.name
      agent_registry_table     = aws_dynamodb_table.agent_registry.name
    }

    sqs = {
      document_upload_queue = aws_sqs_queue.document_upload_events.url
      extraction_queue      = aws_sqs_queue.extraction_events.url
      matching_queue        = aws_sqs_queue.matching_events.url
      exception_queue       = aws_sqs_queue.exception_events.url
      hitl_queue            = aws_sqs_queue.hitl_review_queue.url
    }

    iam = {
      runtime_execution_role = aws_iam_role.agentcore_runtime_execution.arn
      gateway_role           = aws_iam_role.agentcore_gateway.arn
    }

    cognito = {
      user_pool_id     = aws_cognito_user_pool.agentcore_identity.id
      user_pool_domain = "${aws_cognito_user_pool_domain.agentcore_identity.domain}.auth.${var.aws_region}.amazoncognito.com"
      web_client_id    = aws_cognito_user_pool_client.web_portal.id
      api_client_id    = aws_cognito_user_pool_client.api_client.id
    }

    observability = {
      metric_namespace = local.metric_namespace
      dashboard_name   = aws_cloudwatch_dashboard.agentcore_dashboard.dashboard_name
      alerts_topic     = aws_sns_topic.agentcore_alerts.arn
    }
  }
}

output "deployment_instructions" {
  description = "Next steps for deployment"
  value       = <<-EOT
  
  ========================================
  AgentCore Infrastructure Deployed!
  ========================================
  
  Next Steps:
  
  1. Configure AgentCore Memory:
     cd ${path.module}/scripts
     ./deploy_agentcore_memory.sh
  
  2. Configure AgentCore Gateway:
     cd ${path.module}/scripts
     ./deploy_agentcore_gateway.sh
  
  3. Create Cognito Users:
     aws cognito-idp admin-create-user \
       --user-pool-id ${aws_cognito_user_pool.agentcore_identity.id} \
       --username admin@example.com \
       --user-attributes Name=email,Value=admin@example.com Name=name,Value="Admin User" \
       --temporary-password "TempPass123!" \
       --region ${var.aws_region}
  
  4. Deploy Agents:
     - See tasks 14.1-14.6 in the implementation plan
  
  5. View CloudWatch Dashboard:
     https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.agentcore_dashboard.dashboard_name}
  
  Configuration Files:
  - AgentCore Memory: ${path.module}/configs/AGENTCORE_MEMORY_README.md
  - AgentCore Gateway: ${path.module}/configs/AGENTCORE_GATEWAY_README.md
  - AgentCore Identity: ${path.module}/configs/AGENTCORE_IDENTITY_README.md
  - Observability: ${path.module}/configs/AGENTCORE_OBSERVABILITY_README.md
  
  ========================================
  EOT
}

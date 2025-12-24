# DynamoDB Table for Bank Trade Data
resource "aws_dynamodb_table" "bank_trade_data" {
  name         = "${var.dynamodb_bank_table}-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "Trade_ID"

  attribute {
    name = "Trade_ID"
    type = "S"
  }

  attribute {
    name = "Trade_Date"
    type = "S"
  }

  attribute {
    name = "Counterparty"
    type = "S"
  }

  attribute {
    name = "TRADE_SOURCE"
    type = "S"
  }

  global_secondary_index {
    name            = "TradeDateIndex"
    hash_key        = "Trade_Date"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "CounterpartyIndex"
    hash_key        = "Counterparty"
    range_key       = "Trade_Date"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "TradeSourceIndex"
    hash_key        = "TRADE_SOURCE"
    range_key       = "Trade_Date"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  ttl {
    attribute_name = "ttl"
    enabled        = false
  }

  tags = merge(var.tags, {
    Name        = "Bank Trade Data"
    Type        = "Database"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# DynamoDB Table for Counterparty Trade Data
resource "aws_dynamodb_table" "counterparty_trade_data" {
  name         = "${var.dynamodb_counterparty_table}-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "Trade_ID"

  attribute {
    name = "Trade_ID"
    type = "S"
  }

  attribute {
    name = "Trade_Date"
    type = "S"
  }

  attribute {
    name = "Bank"
    type = "S"
  }

  attribute {
    name = "TRADE_SOURCE"
    type = "S"
  }

  global_secondary_index {
    name            = "TradeDateIndex"
    hash_key        = "Trade_Date"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "BankIndex"
    hash_key        = "Bank"
    range_key       = "Trade_Date"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "TradeSourceIndex"
    hash_key        = "TRADE_SOURCE"
    range_key       = "Trade_Date"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  ttl {
    attribute_name = "ttl"
    enabled        = false
  }

  tags = merge(var.tags, {
    Name        = "Counterparty Trade Data"
    Type        = "Database"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# DynamoDB Table for Exceptions
resource "aws_dynamodb_table" "exceptions" {
  name         = "${var.project_name}-exceptions-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "exception_id"
  range_key    = "timestamp"

  attribute {
    name = "exception_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  attribute {
    name = "trade_id"
    type = "S"
  }

  attribute {
    name = "severity_score"
    type = "N"
  }

  attribute {
    name = "triage_routing"
    type = "S"
  }

  attribute {
    name = "resolution_status"
    type = "S"
  }

  global_secondary_index {
    name            = "TradeIdIndex"
    hash_key        = "trade_id"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "SeverityIndex"
    hash_key        = "severity_score"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "TriageRoutingIndex"
    hash_key        = "triage_routing"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "ResolutionStatusIndex"
    hash_key        = "resolution_status"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = merge(var.tags, {
    Name        = "Exceptions Table"
    Type        = "Database"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# DynamoDB Table for Agent Registry
resource "aws_dynamodb_table" "agent_registry" {
  name         = "${var.project_name}-agent-registry-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "agent_id"

  attribute {
    name = "agent_id"
    type = "S"
  }

  attribute {
    name = "agent_type"
    type = "S"
  }

  attribute {
    name = "deployment_status"
    type = "S"
  }

  global_secondary_index {
    name            = "AgentTypeIndex"
    hash_key        = "agent_type"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "DeploymentStatusIndex"
    hash_key        = "deployment_status"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  tags = merge(var.tags, {
    Name        = "Agent Registry"
    Type        = "Database"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# DynamoDB Table for Orchestrator Status Tracking
resource "aws_dynamodb_table" "orchestrator_status" {
  name         = "trade-matching-system-processing-status"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "sessionId"

  attribute {
    name = "sessionId"
    type = "S"
  }

  ttl {
    attribute_name = "expiresAt"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  tags = merge(var.tags, {
    Name        = "Orchestrator Processing Status"
    Type        = "Database"
    Component   = "AgentCore"
    Environment = var.environment
    Purpose     = "Real-time workflow status tracking"
  })
}

# KMS Key for DynamoDB Encryption
resource "aws_kms_key" "dynamodb" {
  description             = "KMS key for DynamoDB table encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = merge(var.tags, {
    Name        = "DynamoDB Encryption Key"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

resource "aws_kms_alias" "dynamodb" {
  name          = "alias/${var.project_name}-dynamodb-${var.environment}"
  target_key_id = aws_kms_key.dynamodb.key_id
}

# Outputs
output "bank_trade_table_name" {
  description = "Name of the Bank Trade Data table"
  value       = aws_dynamodb_table.bank_trade_data.name
}

output "bank_trade_table_arn" {
  description = "ARN of the Bank Trade Data table"
  value       = aws_dynamodb_table.bank_trade_data.arn
}

output "counterparty_trade_table_name" {
  description = "Name of the Counterparty Trade Data table"
  value       = aws_dynamodb_table.counterparty_trade_data.name
}

output "counterparty_trade_table_arn" {
  description = "ARN of the Counterparty Trade Data table"
  value       = aws_dynamodb_table.counterparty_trade_data.arn
}

output "exceptions_table_name" {
  description = "Name of the Exceptions table"
  value       = aws_dynamodb_table.exceptions.name
}

output "exceptions_table_arn" {
  description = "ARN of the Exceptions table"
  value       = aws_dynamodb_table.exceptions.arn
}

output "agent_registry_table_name" {
  description = "Name of the Agent Registry table"
  value       = aws_dynamodb_table.agent_registry.name
}

output "agent_registry_table_arn" {
  description = "ARN of the Agent Registry table"
  value       = aws_dynamodb_table.agent_registry.arn
}

output "orchestrator_status_table_name" {
  description = "Name of the Orchestrator Status table"
  value       = aws_dynamodb_table.orchestrator_status.name
}

output "orchestrator_status_table_arn" {
  description = "ARN of the Orchestrator Status table"
  value       = aws_dynamodb_table.orchestrator_status.arn
}

output "dynamodb_kms_key_id" {
  description = "ID of the KMS key for DynamoDB encryption"
  value       = aws_kms_key.dynamodb.key_id
}

output "dynamodb_kms_key_arn" {
  description = "ARN of the KMS key for DynamoDB encryption"
  value       = aws_kms_key.dynamodb.arn
}

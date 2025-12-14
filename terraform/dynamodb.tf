# DynamoDB Table for Bank Trade Data
resource "aws_dynamodb_table" "bank_trade_data" {
  name           = var.dynamodb_bank_table
  billing_mode   = var.dynamodb_billing_mode
  hash_key       = "Trade_ID"

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

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = merge(var.tags, {
    Name = "Bank Trade Data"
    Type = "Database"
  })
}

# DynamoDB Table for Counterparty Trade Data
resource "aws_dynamodb_table" "counterparty_trade_data" {
  name           = var.dynamodb_counterparty_table
  billing_mode   = var.dynamodb_billing_mode
  hash_key       = "Trade_ID"

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

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = merge(var.tags, {
    Name = "Counterparty Trade Data"
    Type = "Database"
  })
}

# DynamoDB Table for Processing Status
resource "aws_dynamodb_table" "processing_status" {
  name           = "${var.project_name}-processing-status"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "processing_id"

  attribute {
    name = "processing_id"
    type = "S"
  }

  attribute {
    name = "unique_identifier"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  global_secondary_index {
    name            = "UniqueIdentifierIndex"
    hash_key        = "unique_identifier"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "CreatedAtIndex"
    hash_key        = "created_at"
    projection_type = "KEYS_ONLY"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = merge(var.tags, {
    Name = "Processing Status"
    Type = "Database"
  })
}

# DynamoDB Table for Exceptions
resource "aws_dynamodb_table" "exceptions" {
  name           = "ExceptionsTable"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "exception_id"

  attribute {
    name = "exception_id"
    type = "S"
  }

  attribute {
    name = "trade_id"
    type = "S"
  }

  attribute {
    name = "severity"
    type = "S"
  }

  global_secondary_index {
    name            = "TradeIdIndex"
    hash_key        = "trade_id"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "SeverityIndex"
    hash_key        = "severity"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = merge(var.tags, {
    Name = "Exceptions Table"
    Type = "Database"
  })
}

# DynamoDB Table for Agent Registry (Web Portal)
resource "aws_dynamodb_table" "agent_registry" {
  name           = "AgentRegistry"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "agent_id"

  attribute {
    name = "agent_id"
    type = "S"
  }

  attribute {
    name = "agent_name"
    type = "S"
  }

  global_secondary_index {
    name            = "AgentNameIndex"
    hash_key        = "agent_name"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = merge(var.tags, {
    Name = "Agent Registry"
    Type = "Database"
  })
}

# DynamoDB Table for HITL Reviews (Web Portal)
resource "aws_dynamodb_table" "hitl_reviews" {
  name           = "HITLReviews"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "review_id"

  attribute {
    name = "review_id"
    type = "S"
  }

  attribute {
    name = "trade_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name            = "TradeIdIndex"
    hash_key        = "trade_id"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "StatusIndex"
    hash_key        = "status"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = merge(var.tags, {
    Name = "HITL Reviews"
    Type = "Database"
  })
}

# DynamoDB Table for Audit Trail (Web Portal)
resource "aws_dynamodb_table" "audit_trail" {
  name           = "AuditTrail"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "audit_id"

  attribute {
    name = "audit_id"
    type = "S"
  }

  attribute {
    name = "trade_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  global_secondary_index {
    name            = "TradeIdIndex"
    hash_key        = "trade_id"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "TimestampIndex"
    hash_key        = "timestamp"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = merge(var.tags, {
    Name = "Audit Trail"
    Type = "Database"
  })
}
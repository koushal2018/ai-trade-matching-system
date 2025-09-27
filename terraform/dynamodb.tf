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
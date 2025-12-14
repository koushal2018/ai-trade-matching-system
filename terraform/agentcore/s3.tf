# S3 Bucket for AgentCore Trade Documents and Outputs
resource "aws_s3_bucket" "agentcore_trade_documents" {
  bucket = "${var.project_name}-agentcore-${var.environment}"

  tags = merge(var.tags, {
    Name        = "AgentCore Trade Documents"
    Type        = "Data"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "agentcore_trade_documents" {
  bucket = aws_s3_bucket.agentcore_trade_documents.id

  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket Encryption (AES-256)
resource "aws_s3_bucket_server_side_encryption_configuration" "agentcore_trade_documents" {
  bucket = aws_s3_bucket.agentcore_trade_documents.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "agentcore_trade_documents" {
  bucket = aws_s3_bucket.agentcore_trade_documents.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket Lifecycle Configuration for Cost Optimization
resource "aws_s3_bucket_lifecycle_configuration" "agentcore_trade_documents" {
  bucket = aws_s3_bucket.agentcore_trade_documents.id

  # Rule for BANK folder
  rule {
    id     = "bank-documents-lifecycle"
    status = "Enabled"

    filter {
      prefix = "BANK/"
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER_IR"
    }

    expiration {
      days = 365
    }

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }

  # Rule for COUNTERPARTY folder
  rule {
    id     = "counterparty-documents-lifecycle"
    status = "Enabled"

    filter {
      prefix = "COUNTERPARTY/"
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER_IR"
    }

    expiration {
      days = 365
    }

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }

  # Rule for extracted data
  rule {
    id     = "extracted-data-lifecycle"
    status = "Enabled"

    filter {
      prefix = "extracted/"
    }

    transition {
      days          = 60
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 180
      storage_class = "GLACIER_IR"
    }

    expiration {
      days = 730
    }
  }

  # Rule for reports
  rule {
    id     = "reports-lifecycle"
    status = "Enabled"

    filter {
      prefix = "reports/"
    }

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 180
      storage_class = "GLACIER_IR"
    }

    expiration {
      days = 1095
    }
  }

  # Rule for temporary processing files
  rule {
    id     = "temp-files-cleanup"
    status = "Enabled"

    filter {
      prefix = "temp/"
    }

    expiration {
      days = 7
    }
  }
}

# Create folder structure using S3 objects with zero-byte files
resource "aws_s3_object" "bank_folder" {
  bucket       = aws_s3_bucket.agentcore_trade_documents.id
  key          = "BANK/.keep"
  content      = ""
  content_type = "text/plain"

  tags = {
    Purpose = "Folder structure"
  }
}

resource "aws_s3_object" "counterparty_folder" {
  bucket       = aws_s3_bucket.agentcore_trade_documents.id
  key          = "COUNTERPARTY/.keep"
  content      = ""
  content_type = "text/plain"

  tags = {
    Purpose = "Folder structure"
  }
}

resource "aws_s3_object" "extracted_folder" {
  bucket       = aws_s3_bucket.agentcore_trade_documents.id
  key          = "extracted/.keep"
  content      = ""
  content_type = "text/plain"

  tags = {
    Purpose = "Folder structure"
  }
}

resource "aws_s3_object" "extracted_bank_folder" {
  bucket       = aws_s3_bucket.agentcore_trade_documents.id
  key          = "extracted/BANK/.keep"
  content      = ""
  content_type = "text/plain"

  tags = {
    Purpose = "Folder structure"
  }
}

resource "aws_s3_object" "extracted_counterparty_folder" {
  bucket       = aws_s3_bucket.agentcore_trade_documents.id
  key          = "extracted/COUNTERPARTY/.keep"
  content      = ""
  content_type = "text/plain"

  tags = {
    Purpose = "Folder structure"
  }
}

resource "aws_s3_object" "reports_folder" {
  bucket       = aws_s3_bucket.agentcore_trade_documents.id
  key          = "reports/.keep"
  content      = ""
  content_type = "text/plain"

  tags = {
    Purpose = "Folder structure"
  }
}

resource "aws_s3_object" "config_folder" {
  bucket       = aws_s3_bucket.agentcore_trade_documents.id
  key          = "config/.keep"
  content      = ""
  content_type = "text/plain"

  tags = {
    Purpose = "Folder structure"
  }
}

# S3 Bucket Logging
resource "aws_s3_bucket_logging" "agentcore_trade_documents" {
  bucket = aws_s3_bucket.agentcore_trade_documents.id

  target_bucket = aws_s3_bucket.agentcore_logs.id
  target_prefix = "s3-access-logs/"
}

# S3 Bucket for Logs
resource "aws_s3_bucket" "agentcore_logs" {
  bucket = "${var.project_name}-agentcore-logs-${var.environment}"

  tags = merge(var.tags, {
    Name        = "AgentCore Logs"
    Type        = "Logs"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

resource "aws_s3_bucket_versioning" "agentcore_logs" {
  bucket = aws_s3_bucket.agentcore_logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "agentcore_logs" {
  bucket = aws_s3_bucket.agentcore_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "agentcore_logs" {
  bucket = aws_s3_bucket.agentcore_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "agentcore_logs" {
  bucket = aws_s3_bucket.agentcore_logs.id

  rule {
    id     = "log-retention"
    status = "Enabled"

    filter {
      prefix = ""
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER_IR"
    }

    expiration {
      days = 180
    }
  }
}

# Outputs
output "s3_bucket_name" {
  description = "Name of the AgentCore S3 bucket"
  value       = aws_s3_bucket.agentcore_trade_documents.id
}

output "s3_bucket_arn" {
  description = "ARN of the AgentCore S3 bucket"
  value       = aws_s3_bucket.agentcore_trade_documents.arn
}

output "s3_logs_bucket_name" {
  description = "Name of the AgentCore logs S3 bucket"
  value       = aws_s3_bucket.agentcore_logs.id
}

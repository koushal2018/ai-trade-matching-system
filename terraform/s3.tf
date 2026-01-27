# S3 Bucket for trade documents
resource "aws_s3_bucket" "trade_documents" {
  bucket = var.s3_bucket_name

  tags = merge(var.tags, {
    Name = "Trade Documents Storage"
    Type = "Data"
  })
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "trade_documents" {
  bucket = aws_s3_bucket.trade_documents.id

  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "trade_documents" {
  bucket = aws_s3_bucket.trade_documents.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "trade_documents" {
  bucket = aws_s3_bucket.trade_documents.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket Lifecycle Configuration
resource "aws_s3_bucket_lifecycle_configuration" "trade_documents" {
  bucket = aws_s3_bucket.trade_documents.id

  rule {
    id     = "cleanup-processed-documents"
    status = "Enabled"

    filter {
      prefix = "PDFIMAGES/"
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 60
      storage_class = "GLACIER"
    }

    expiration {
      days = var.s3_lifecycle_days
    }
  }

  rule {
    id     = "cleanup-temp-files"
    status = "Enabled"

    filter {
      prefix = "TEMP/"
    }

    expiration {
      days = 7
    }
  }
}

# S3 Event Notification Configuration
# Commented out until Lambda function is created
# resource "aws_s3_bucket_notification" "trade_documents" {
#   bucket = aws_s3_bucket.trade_documents.id
#
#   lambda_function {
#     lambda_function_arn = aws_lambda_function.s3_event_processor.arn
#     events              = ["s3:ObjectCreated:*"]
#     filter_prefix       = "BANK/"
#     filter_suffix       = ".pdf"
#   }
#
#   lambda_function {
#     lambda_function_arn = aws_lambda_function.s3_event_processor.arn
#     events              = ["s3:ObjectCreated:*"]
#     filter_prefix       = "COUNTERPARTY/"
#     filter_suffix       = ".pdf"
#   }
#
#   depends_on = [aws_lambda_permission.allow_s3]
# }

# S3 Bucket CORS Configuration
resource "aws_s3_bucket_cors_configuration" "trade_documents" {
  bucket = aws_s3_bucket.trade_documents.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}
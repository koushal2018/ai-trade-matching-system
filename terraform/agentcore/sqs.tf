# SQS Queue: Document Upload Events (FIFO)
resource "aws_sqs_queue" "document_upload_events" {
  name                        = "${var.project_name}-document-upload-events-${var.environment}.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  visibility_timeout_seconds  = 300
  message_retention_seconds   = 345600 # 4 days
  max_message_size            = 262144
  receive_wait_time_seconds   = 20
  deduplication_scope         = "messageGroup"
  fifo_throughput_limit       = "perMessageGroupId"

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.document_upload_dlq.arn
    maxReceiveCount     = 3
  })

  tags = merge(var.tags, {
    Name        = "Document Upload Events Queue"
    Type        = "FIFO"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

resource "aws_sqs_queue" "document_upload_dlq" {
  name                      = "${var.project_name}-document-upload-dlq-${var.environment}.fifo"
  fifo_queue                = true
  message_retention_seconds = 1209600 # 14 days
  receive_wait_time_seconds = 20

  tags = merge(var.tags, {
    Name        = "Document Upload DLQ"
    Type        = "FIFO"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# SQS Queue: Extraction Events (Standard)
resource "aws_sqs_queue" "extraction_events" {
  name                       = "${var.project_name}-extraction-events-${var.environment}"
  visibility_timeout_seconds = 600
  message_retention_seconds  = 345600 # 4 days
  max_message_size           = 262144
  receive_wait_time_seconds  = 20

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.extraction_dlq.arn
    maxReceiveCount     = 3
  })

  tags = merge(var.tags, {
    Name        = "Extraction Events Queue"
    Type        = "Standard"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

resource "aws_sqs_queue" "extraction_dlq" {
  name                      = "${var.project_name}-extraction-dlq-${var.environment}"
  message_retention_seconds = 1209600 # 14 days
  receive_wait_time_seconds = 20

  tags = merge(var.tags, {
    Name        = "Extraction DLQ"
    Type        = "Standard"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# SQS Queue: Matching Events (Standard)
resource "aws_sqs_queue" "matching_events" {
  name                       = "${var.project_name}-matching-events-${var.environment}"
  visibility_timeout_seconds = 900
  message_retention_seconds  = 345600 # 4 days
  max_message_size           = 262144
  receive_wait_time_seconds  = 20

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.matching_dlq.arn
    maxReceiveCount     = 3
  })

  tags = merge(var.tags, {
    Name        = "Matching Events Queue"
    Type        = "Standard"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

resource "aws_sqs_queue" "matching_dlq" {
  name                      = "${var.project_name}-matching-dlq-${var.environment}"
  message_retention_seconds = 1209600 # 14 days
  receive_wait_time_seconds = 20

  tags = merge(var.tags, {
    Name        = "Matching DLQ"
    Type        = "Standard"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# SQS Queue: Exception Events (Standard)
resource "aws_sqs_queue" "exception_events" {
  name                       = "${var.project_name}-exception-events-${var.environment}"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 1209600 # 14 days (longer retention for exceptions)
  max_message_size           = 262144
  receive_wait_time_seconds  = 20

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.exception_dlq.arn
    maxReceiveCount     = 5 # More retries for exceptions
  })

  tags = merge(var.tags, {
    Name        = "Exception Events Queue"
    Type        = "Standard"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

resource "aws_sqs_queue" "exception_dlq" {
  name                      = "${var.project_name}-exception-dlq-${var.environment}"
  message_retention_seconds = 1209600 # 14 days
  receive_wait_time_seconds = 20

  tags = merge(var.tags, {
    Name        = "Exception DLQ"
    Type        = "Standard"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# SQS Queue: HITL Review Queue (FIFO)
resource "aws_sqs_queue" "hitl_review_queue" {
  name                        = "${var.project_name}-hitl-review-queue-${var.environment}.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  visibility_timeout_seconds  = 3600    # 1 hour for human review
  message_retention_seconds   = 1209600 # 14 days
  max_message_size            = 262144
  receive_wait_time_seconds   = 20
  deduplication_scope         = "messageGroup"
  fifo_throughput_limit       = "perMessageGroupId"

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.hitl_dlq.arn
    maxReceiveCount     = 1 # No retries for HITL
  })

  tags = merge(var.tags, {
    Name        = "HITL Review Queue"
    Type        = "FIFO"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

resource "aws_sqs_queue" "hitl_dlq" {
  name                      = "${var.project_name}-hitl-dlq-${var.environment}.fifo"
  fifo_queue                = true
  message_retention_seconds = 1209600 # 14 days
  receive_wait_time_seconds = 20

  tags = merge(var.tags, {
    Name        = "HITL DLQ"
    Type        = "FIFO"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# SQS Queue: Ops Desk Queue (FIFO)
resource "aws_sqs_queue" "ops_desk_queue" {
  name                        = "${var.project_name}-ops-desk-queue-${var.environment}.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  visibility_timeout_seconds  = 1800    # 30 minutes
  message_retention_seconds   = 1209600 # 14 days
  max_message_size            = 262144
  receive_wait_time_seconds   = 20
  deduplication_scope         = "messageGroup"
  fifo_throughput_limit       = "perMessageGroupId"

  tags = merge(var.tags, {
    Name        = "Ops Desk Queue"
    Type        = "FIFO"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# SQS Queue: Senior Ops Queue (FIFO)
resource "aws_sqs_queue" "senior_ops_queue" {
  name                        = "${var.project_name}-senior-ops-queue-${var.environment}.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  visibility_timeout_seconds  = 1800    # 30 minutes
  message_retention_seconds   = 1209600 # 14 days
  max_message_size            = 262144
  receive_wait_time_seconds   = 20
  deduplication_scope         = "messageGroup"
  fifo_throughput_limit       = "perMessageGroupId"

  tags = merge(var.tags, {
    Name        = "Senior Ops Queue"
    Type        = "FIFO"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# SQS Queue: Compliance Queue (FIFO)
resource "aws_sqs_queue" "compliance_queue" {
  name                        = "${var.project_name}-compliance-queue-${var.environment}.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  visibility_timeout_seconds  = 3600    # 1 hour
  message_retention_seconds   = 1209600 # 14 days
  max_message_size            = 262144
  receive_wait_time_seconds   = 20
  deduplication_scope         = "messageGroup"
  fifo_throughput_limit       = "perMessageGroupId"

  tags = merge(var.tags, {
    Name        = "Compliance Queue"
    Type        = "FIFO"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# SQS Queue: Engineering Queue (Standard)
resource "aws_sqs_queue" "engineering_queue" {
  name                       = "${var.project_name}-engineering-queue-${var.environment}"
  visibility_timeout_seconds = 3600    # 1 hour
  message_retention_seconds  = 1209600 # 14 days
  max_message_size           = 262144
  receive_wait_time_seconds  = 20

  tags = merge(var.tags, {
    Name        = "Engineering Queue"
    Type        = "Standard"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# SQS Queue: Orchestrator Monitoring Queue (Standard - Fanout)
resource "aws_sqs_queue" "orchestrator_monitoring_queue" {
  name                       = "${var.project_name}-orchestrator-monitoring-queue-${var.environment}"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 345600 # 4 days
  max_message_size           = 262144
  receive_wait_time_seconds  = 20

  tags = merge(var.tags, {
    Name        = "Orchestrator Monitoring Queue"
    Type        = "Standard"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# SNS Topic for Fanout to Orchestrator
resource "aws_sns_topic" "agent_events_fanout" {
  name = "${var.project_name}-agent-events-fanout-${var.environment}"

  tags = merge(var.tags, {
    Name        = "Agent Events Fanout Topic"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# Subscribe Orchestrator Monitoring Queue to SNS Topic
resource "aws_sns_topic_subscription" "orchestrator_monitoring" {
  topic_arn = aws_sns_topic.agent_events_fanout.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.orchestrator_monitoring_queue.arn
}

# SQS Queue Policy for SNS to send messages
resource "aws_sqs_queue_policy" "orchestrator_monitoring_policy" {
  queue_url = aws_sqs_queue.orchestrator_monitoring_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "sns.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.orchestrator_monitoring_queue.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_sns_topic.agent_events_fanout.arn
          }
        }
      }
    ]
  })
}

# Outputs
output "document_upload_events_queue_url" {
  description = "URL of the document upload events queue"
  value       = aws_sqs_queue.document_upload_events.url
}

output "document_upload_events_queue_arn" {
  description = "ARN of the document upload events queue"
  value       = aws_sqs_queue.document_upload_events.arn
}

output "extraction_events_queue_url" {
  description = "URL of the extraction events queue"
  value       = aws_sqs_queue.extraction_events.url
}

output "extraction_events_queue_arn" {
  description = "ARN of the extraction events queue"
  value       = aws_sqs_queue.extraction_events.arn
}

output "matching_events_queue_url" {
  description = "URL of the matching events queue"
  value       = aws_sqs_queue.matching_events.url
}

output "matching_events_queue_arn" {
  description = "ARN of the matching events queue"
  value       = aws_sqs_queue.matching_events.arn
}

output "exception_events_queue_url" {
  description = "URL of the exception events queue"
  value       = aws_sqs_queue.exception_events.url
}

output "exception_events_queue_arn" {
  description = "ARN of the exception events queue"
  value       = aws_sqs_queue.exception_events.arn
}

output "hitl_review_queue_url" {
  description = "URL of the HITL review queue"
  value       = aws_sqs_queue.hitl_review_queue.url
}

output "hitl_review_queue_arn" {
  description = "ARN of the HITL review queue"
  value       = aws_sqs_queue.hitl_review_queue.arn
}

output "ops_desk_queue_url" {
  description = "URL of the ops desk queue"
  value       = aws_sqs_queue.ops_desk_queue.url
}

output "senior_ops_queue_url" {
  description = "URL of the senior ops queue"
  value       = aws_sqs_queue.senior_ops_queue.url
}

output "compliance_queue_url" {
  description = "URL of the compliance queue"
  value       = aws_sqs_queue.compliance_queue.url
}

output "engineering_queue_url" {
  description = "URL of the engineering queue"
  value       = aws_sqs_queue.engineering_queue.url
}

output "orchestrator_monitoring_queue_url" {
  description = "URL of the orchestrator monitoring queue"
  value       = aws_sqs_queue.orchestrator_monitoring_queue.url
}

output "orchestrator_monitoring_queue_arn" {
  description = "ARN of the orchestrator monitoring queue"
  value       = aws_sqs_queue.orchestrator_monitoring_queue.arn
}

output "agent_events_fanout_topic_arn" {
  description = "ARN of the agent events fanout SNS topic"
  value       = aws_sns_topic.agent_events_fanout.arn
}

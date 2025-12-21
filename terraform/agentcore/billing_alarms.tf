# Billing Alarms for Cost Monitoring
# Note: Billing metrics are only available in us-east-1 region

# SNS Topic for Billing Alerts
resource "aws_sns_topic" "billing_alerts" {
  name = "${var.project_name}-billing-alerts-${var.environment}"

  tags = merge(var.tags, {
    Name        = "Billing Alerts Topic"
    Component   = "AgentCore"
    Environment = var.environment
    Purpose     = "CostMonitoring"
  })
}

# SNS Topic Subscription for Billing Alerts
resource "aws_sns_topic_subscription" "billing_alerts_email" {
  count     = length(var.billing_alert_emails) > 0 ? length(var.billing_alert_emails) : 0
  topic_arn = aws_sns_topic.billing_alerts.arn
  protocol  = "email"
  endpoint  = var.billing_alert_emails[count.index]
}

# CloudWatch Billing Alarm - Total Estimated Charges
resource "aws_cloudwatch_metric_alarm" "total_estimated_charges" {
  alarm_name          = "${var.project_name}-total-charges-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 21600 # 6 hours
  statistic           = "Maximum"
  threshold           = var.billing_alarm_threshold
  alarm_description   = "Alert when total AWS charges exceed $${var.billing_alarm_threshold}"
  alarm_actions       = [aws_sns_topic.billing_alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    Currency = "USD"
  }

  tags = merge(var.tags, {
    Name        = "Total Charges Alarm"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# CloudWatch Billing Alarm - Warning Threshold (80% of limit)
resource "aws_cloudwatch_metric_alarm" "total_estimated_charges_warning" {
  alarm_name          = "${var.project_name}-total-charges-warning-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 21600 # 6 hours
  statistic           = "Maximum"
  threshold           = var.billing_alarm_threshold * 0.8
  alarm_description   = "Warning when total AWS charges exceed 80% of budget ($${var.billing_alarm_threshold * 0.8})"
  alarm_actions       = [aws_sns_topic.billing_alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    Currency = "USD"
  }

  tags = merge(var.tags, {
    Name        = "Total Charges Warning"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# CloudWatch Billing Alarm - Daily Charges
resource "aws_cloudwatch_metric_alarm" "daily_estimated_charges" {
  alarm_name          = "${var.project_name}-daily-charges-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 86400 # 24 hours
  statistic           = "Maximum"
  threshold           = var.billing_alarm_threshold / 30 # Daily threshold
  alarm_description   = "Alert when daily AWS charges exceed $${var.billing_alarm_threshold / 30}"
  alarm_actions       = [aws_sns_topic.billing_alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    Currency = "USD"
  }

  tags = merge(var.tags, {
    Name        = "Daily Charges Alarm"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# Service-Specific Billing Alarms

# S3 Charges Alarm
resource "aws_cloudwatch_metric_alarm" "s3_charges" {
  count               = var.enable_service_billing_alarms ? 1 : 0
  alarm_name          = "${var.project_name}-s3-charges-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 21600 # 6 hours
  statistic           = "Maximum"
  threshold           = 100 # $100/month for S3
  alarm_description   = "Alert when S3 charges exceed $100"
  alarm_actions       = [aws_sns_topic.billing_alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    Currency    = "USD"
    ServiceName = "AmazonS3"
  }

  tags = merge(var.tags, {
    Name        = "S3 Charges Alarm"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# DynamoDB Charges Alarm
resource "aws_cloudwatch_metric_alarm" "dynamodb_charges" {
  count               = var.enable_service_billing_alarms ? 1 : 0
  alarm_name          = "${var.project_name}-dynamodb-charges-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 21600 # 6 hours
  statistic           = "Maximum"
  threshold           = 200 # $200/month for DynamoDB
  alarm_description   = "Alert when DynamoDB charges exceed $200"
  alarm_actions       = [aws_sns_topic.billing_alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    Currency    = "USD"
    ServiceName = "AmazonDynamoDB"
  }

  tags = merge(var.tags, {
    Name        = "DynamoDB Charges Alarm"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# Bedrock Charges Alarm
resource "aws_cloudwatch_metric_alarm" "bedrock_charges" {
  count               = var.enable_service_billing_alarms ? 1 : 0
  alarm_name          = "${var.project_name}-bedrock-charges-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 21600 # 6 hours
  statistic           = "Maximum"
  threshold           = 300 # $300/month for Bedrock
  alarm_description   = "Alert when Bedrock charges exceed $300"
  alarm_actions       = [aws_sns_topic.billing_alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    Currency    = "USD"
    ServiceName = "AmazonBedrock"
  }

  tags = merge(var.tags, {
    Name        = "Bedrock Charges Alarm"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# CloudWatch Charges Alarm
resource "aws_cloudwatch_metric_alarm" "cloudwatch_charges" {
  count               = var.enable_service_billing_alarms ? 1 : 0
  alarm_name          = "${var.project_name}-cloudwatch-charges-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 21600 # 6 hours
  statistic           = "Maximum"
  threshold           = 100 # $100/month for CloudWatch
  alarm_description   = "Alert when CloudWatch charges exceed $100"
  alarm_actions       = [aws_sns_topic.billing_alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    Currency    = "USD"
    ServiceName = "AmazonCloudWatch"
  }

  tags = merge(var.tags, {
    Name        = "CloudWatch Charges Alarm"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# AWS Budget (Alternative to CloudWatch Alarms)
# Only create if billing_alert_emails is not empty (budget notifications require subscribers)
resource "aws_budgets_budget" "monthly_cost_budget" {
  count        = var.enable_aws_budget && length(var.billing_alert_emails) > 0 ? 1 : 0
  name         = "${var.project_name}-monthly-budget-${var.environment}"
  budget_type  = "COST"
  limit_amount = var.billing_alarm_threshold
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  cost_filter {
    name = "TagKeyValue"
    values = [
      "Component$AgentCore"
    ]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = var.billing_alert_emails
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = var.billing_alert_emails
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 90
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = var.billing_alert_emails
  }

  tags = merge(var.tags, {
    Name        = "Monthly Cost Budget"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# Cost Anomaly Detection
resource "aws_ce_anomaly_monitor" "agentcore_anomaly_monitor" {
  count             = var.enable_cost_anomaly_detection ? 1 : 0
  name              = "${var.project_name}-anomaly-monitor-${var.environment}"
  monitor_type      = "DIMENSIONAL"
  monitor_dimension = "SERVICE"

  tags = merge(var.tags, {
    Name        = "Cost Anomaly Monitor"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

resource "aws_ce_anomaly_subscription" "agentcore_anomaly_subscription" {
  count     = var.enable_cost_anomaly_detection ? 1 : 0
  name      = "${var.project_name}-anomaly-subscription-${var.environment}"
  frequency = "DAILY"

  monitor_arn_list = [
    aws_ce_anomaly_monitor.agentcore_anomaly_monitor[0].arn
  ]

  subscriber {
    type    = "EMAIL"
    address = var.billing_alert_emails[0]
  }

  threshold_expression {
    dimension {
      key           = "ANOMALY_TOTAL_IMPACT_ABSOLUTE"
      values        = ["50"] # Alert on anomalies > $50
      match_options = ["GREATER_THAN_OR_EQUAL"]
    }
  }

  tags = merge(var.tags, {
    Name        = "Cost Anomaly Subscription"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# Outputs
output "billing_alerts_topic_arn" {
  description = "ARN of the billing alerts SNS topic"
  value       = aws_sns_topic.billing_alerts.arn
}

output "billing_alarm_threshold" {
  description = "Monthly billing alarm threshold in USD"
  value       = var.billing_alarm_threshold
}

output "billing_alarms" {
  description = "List of billing alarm names"
  value = {
    total_charges         = aws_cloudwatch_metric_alarm.total_estimated_charges.alarm_name
    total_charges_warning = aws_cloudwatch_metric_alarm.total_estimated_charges_warning.alarm_name
    daily_charges         = aws_cloudwatch_metric_alarm.daily_estimated_charges.alarm_name
  }
}

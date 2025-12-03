# AgentCore Observability Configuration
# CloudWatch resources for monitoring, tracing, and alerting

# CloudWatch Log Groups for each agent
resource "aws_cloudwatch_log_group" "pdf_adapter_agent" {
  name              = "/aws/agentcore/${var.project_name}/pdf-adapter-${var.environment}"
  retention_in_days = 30

  tags = merge(var.tags, {
    Name        = "PDF Adapter Agent Logs"
    Component   = "AgentCore"
    Environment = var.environment
    Agent       = "PDFAdapter"
  })
}

resource "aws_cloudwatch_log_group" "trade_extraction_agent" {
  name              = "/aws/agentcore/${var.project_name}/trade-extraction-${var.environment}"
  retention_in_days = 30

  tags = merge(var.tags, {
    Name        = "Trade Extraction Agent Logs"
    Component   = "AgentCore"
    Environment = var.environment
    Agent       = "TradeExtraction"
  })
}

resource "aws_cloudwatch_log_group" "trade_matching_agent" {
  name              = "/aws/agentcore/${var.project_name}/trade-matching-${var.environment}"
  retention_in_days = 30

  tags = merge(var.tags, {
    Name        = "Trade Matching Agent Logs"
    Component   = "AgentCore"
    Environment = var.environment
    Agent       = "TradeMatching"
  })
}

resource "aws_cloudwatch_log_group" "exception_management_agent" {
  name              = "/aws/agentcore/${var.project_name}/exception-management-${var.environment}"
  retention_in_days = 30

  tags = merge(var.tags, {
    Name        = "Exception Management Agent Logs"
    Component   = "AgentCore"
    Environment = var.environment
    Agent       = "ExceptionManagement"
  })
}

resource "aws_cloudwatch_log_group" "orchestrator_agent" {
  name              = "/aws/agentcore/${var.project_name}/orchestrator-${var.environment}"
  retention_in_days = 30

  tags = merge(var.tags, {
    Name        = "Orchestrator Agent Logs"
    Component   = "AgentCore"
    Environment = var.environment
    Agent       = "Orchestrator"
  })
}

# CloudWatch Metric Namespace
locals {
  metric_namespace = "AgentCore/${var.project_name}"
}

# CloudWatch Alarms for Agent Health

# PDF Adapter Agent - Error Rate Alarm
resource "aws_cloudwatch_metric_alarm" "pdf_adapter_error_rate" {
  alarm_name          = "${var.project_name}-pdf-adapter-error-rate-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ErrorRate"
  namespace           = local.metric_namespace
  period              = 300
  statistic           = "Average"
  threshold           = 5.0
  alarm_description   = "PDF Adapter Agent error rate exceeds 5%"
  alarm_actions       = [aws_sns_topic.agentcore_alerts.arn]

  dimensions = {
    Agent       = "PDFAdapter"
    Environment = var.environment
  }

  tags = merge(var.tags, {
    Name        = "PDF Adapter Error Rate Alarm"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# PDF Adapter Agent - Latency Alarm
resource "aws_cloudwatch_metric_alarm" "pdf_adapter_latency" {
  alarm_name          = "${var.project_name}-pdf-adapter-latency-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ProcessingLatency"
  namespace           = local.metric_namespace
  period              = 300
  statistic           = "Average"
  threshold           = 30000 # 30 seconds
  alarm_description   = "PDF Adapter Agent latency exceeds 30 seconds"
  alarm_actions       = [aws_sns_topic.agentcore_alerts.arn]

  dimensions = {
    Agent       = "PDFAdapter"
    Environment = var.environment
  }

  tags = merge(var.tags, {
    Name        = "PDF Adapter Latency Alarm"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# Trade Matching Agent - Error Rate Alarm
resource "aws_cloudwatch_metric_alarm" "trade_matching_error_rate" {
  alarm_name          = "${var.project_name}-trade-matching-error-rate-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ErrorRate"
  namespace           = local.metric_namespace
  period              = 300
  statistic           = "Average"
  threshold           = 5.0
  alarm_description   = "Trade Matching Agent error rate exceeds 5%"
  alarm_actions       = [aws_sns_topic.agentcore_alerts.arn]

  dimensions = {
    Agent       = "TradeMatching"
    Environment = var.environment
  }

  tags = merge(var.tags, {
    Name        = "Trade Matching Error Rate Alarm"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# Anomaly Detection - Latency
resource "aws_cloudwatch_metric_alarm" "latency_anomaly" {
  alarm_name          = "${var.project_name}-latency-anomaly-${var.environment}"
  comparison_operator = "GreaterThanUpperThreshold"
  evaluation_periods  = 2
  threshold_metric_id = "e1"
  alarm_description   = "Latency anomaly detected (>2x baseline)"
  alarm_actions       = [aws_sns_topic.agentcore_alerts.arn]

  metric_query {
    id          = "e1"
    expression  = "ANOMALY_DETECTION_BAND(m1, 2)"
    label       = "Latency (Expected)"
    return_data = true
  }

  metric_query {
    id = "m1"
    metric {
      metric_name = "ProcessingLatency"
      namespace   = local.metric_namespace
      period      = 300
      stat        = "Average"
      dimensions = {
        Environment = var.environment
      }
    }
  }

  tags = merge(var.tags, {
    Name        = "Latency Anomaly Alarm"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# SNS Topic for Alerts
resource "aws_sns_topic" "agentcore_alerts" {
  name = "${var.project_name}-agentcore-alerts-${var.environment}"

  tags = merge(var.tags, {
    Name        = "AgentCore Alerts Topic"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# SNS Topic Subscription (Email)
resource "aws_sns_topic_subscription" "agentcore_alerts_email" {
  count     = length(var.alert_emails) > 0 ? 1 : 0
  topic_arn = aws_sns_topic.agentcore_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_emails[0]
}

# X-Ray Tracing Configuration
resource "aws_xray_sampling_rule" "agentcore_sampling" {
  rule_name      = "${var.project_name}-agentcore-sampling-${var.environment}"
  priority       = 1000
  version        = 1
  reservoir_size = 1
  fixed_rate     = 0.05 # Sample 5% of requests
  url_path       = "*"
  host           = "*"
  http_method    = "*"
  service_type   = "*"
  service_name   = "${var.project_name}-*"
  resource_arn   = "*"

  attributes = {
    Environment = var.environment
  }
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "agentcore_dashboard" {
  dashboard_name = "${var.project_name}-agentcore-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            [local.metric_namespace, "ProcessingLatency", { stat = "Average", label = "Avg Latency" }],
            ["...", { stat = "p95", label = "P95 Latency" }],
            ["...", { stat = "p99", label = "P99 Latency" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Processing Latency"
          yAxis = {
            left = {
              label = "Milliseconds"
            }
          }
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            [local.metric_namespace, "ErrorRate", { Agent = "PDFAdapter", label = "PDF Adapter" }],
            ["...", { Agent = "TradeExtraction", label = "Trade Extraction" }],
            ["...", { Agent = "TradeMatching", label = "Trade Matching" }],
            ["...", { Agent = "ExceptionManagement", label = "Exception Mgmt" }],
            ["...", { Agent = "Orchestrator", label = "Orchestrator" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Error Rate by Agent"
          yAxis = {
            left = {
              label = "Percentage"
            }
          }
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            [local.metric_namespace, "Throughput", { stat = "Sum", label = "Trades Processed" }]
          ]
          period = 3600
          stat   = "Sum"
          region = var.aws_region
          title  = "Throughput (Trades/Hour)"
        }
      },
      {
        type = "log"
        properties = {
          query  = "SOURCE '${aws_cloudwatch_log_group.pdf_adapter_agent.name}' | fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20"
          region = var.aws_region
          title  = "Recent Errors - PDF Adapter"
        }
      },
      {
        type = "log"
        properties = {
          query  = "SOURCE '${aws_cloudwatch_log_group.trade_matching_agent.name}' | fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20"
          region = var.aws_region
          title  = "Recent Errors - Trade Matching"
        }
      }
    ]
  })
}

# Local file for observability configuration
resource "local_file" "agentcore_observability_config" {
  filename = "${path.module}/configs/agentcore_observability_config.json"
  content = jsonencode({
    distributed_tracing = {
      enabled              = true
      service_name         = var.project_name
      sampling_rate        = 0.05
      x_ray_daemon_address = "127.0.0.1:2000"
    }
    metrics = {
      namespace = local.metric_namespace
      dimensions = {
        Environment = var.environment
        Project     = var.project_name
      }
      metrics_to_track = [
        {
          name        = "ProcessingLatency"
          unit        = "Milliseconds"
          description = "Time taken to process a request"
        },
        {
          name        = "ErrorRate"
          unit        = "Percent"
          description = "Percentage of failed requests"
        },
        {
          name        = "Throughput"
          unit        = "Count"
          description = "Number of trades processed"
        }
      ]
    }
    anomaly_detection = {
      enabled = true
      rules = [
        {
          metric               = "ProcessingLatency"
          threshold_multiplier = 2.0
          description          = "Alert when latency exceeds 2x baseline"
        },
        {
          metric      = "ErrorRate"
          threshold   = 5.0
          description = "Alert when error rate exceeds 5%"
        }
      ]
    }
    alerting = {
      sns_topic_arn = aws_sns_topic.agentcore_alerts.arn
      critical_events = [
        "AgentUnhealthy",
        "SLAViolation",
        "HighErrorRate"
      ]
    }
  })
}

# Create README for AgentCore Observability
resource "local_file" "agentcore_observability_readme" {
  filename = "${path.module}/configs/AGENTCORE_OBSERVABILITY_README.md"
  content  = <<-EOT
# AgentCore Observability Setup

This directory contains configuration for AgentCore Observability resources.

## CloudWatch Log Groups

Each agent has a dedicated log group:
- PDF Adapter: ${aws_cloudwatch_log_group.pdf_adapter_agent.name}
- Trade Extraction: ${aws_cloudwatch_log_group.trade_extraction_agent.name}
- Trade Matching: ${aws_cloudwatch_log_group.trade_matching_agent.name}
- Exception Management: ${aws_cloudwatch_log_group.exception_management_agent.name}
- Orchestrator: ${aws_cloudwatch_log_group.orchestrator_agent.name}

## Metrics

Metrics are published to namespace: `${local.metric_namespace}`

### Key Metrics:
1. **ProcessingLatency**: Time taken to process requests (milliseconds)
2. **ErrorRate**: Percentage of failed requests
3. **Throughput**: Number of trades processed per hour

### Dimensions:
- Agent: PDFAdapter, TradeExtraction, TradeMatching, ExceptionManagement, Orchestrator
- Environment: ${var.environment}

## Distributed Tracing

X-Ray tracing is enabled with 5% sampling rate.

### View Traces:
```bash
aws xray get-trace-summaries \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --region ${var.aws_region}
```

### Trace a Specific Request:
```bash
aws xray get-trace-graph \
  --trace-ids <trace-id> \
  --region ${var.aws_region}
```

## Alarms

### Configured Alarms:
1. **PDF Adapter Error Rate**: Triggers when error rate > 5%
2. **PDF Adapter Latency**: Triggers when latency > 30 seconds
3. **Trade Matching Error Rate**: Triggers when error rate > 5%
4. **Latency Anomaly**: Triggers when latency > 2x baseline

### Alert Notifications:
- SNS Topic: ${aws_sns_topic.agentcore_alerts.arn}
- Subscriptions: Email notifications to configured addresses

## Dashboard

CloudWatch Dashboard: ${var.project_name}-agentcore-${var.environment}

View dashboard:
```bash
aws cloudwatch get-dashboard \
  --dashboard-name ${var.project_name}-agentcore-${var.environment} \
  --region ${var.aws_region}
```

Or visit: https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${var.project_name}-agentcore-${var.environment}

## Instrumentation

### Python Agents

Add to agent code:
```python
import boto3
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

# Patch AWS SDK
patch_all()

# Start segment
segment = xray_recorder.begin_segment('pdf-adapter-agent')

# Add metadata
segment.put_metadata('trade_id', trade_id)
segment.put_annotation('agent', 'PDFAdapter')

# Publish metrics
cloudwatch = boto3.client('cloudwatch')
cloudwatch.put_metric_data(
    Namespace='${local.metric_namespace}',
    MetricData=[
        {
            'MetricName': 'ProcessingLatency',
            'Value': latency_ms,
            'Unit': 'Milliseconds',
            'Dimensions': [
                {'Name': 'Agent', 'Value': 'PDFAdapter'},
                {'Name': 'Environment', 'Value': '${var.environment}'}
            ]
        }
    ]
)

# End segment
xray_recorder.end_segment()
```

## Querying Logs

### CloudWatch Insights Queries

Recent errors:
```
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 20
```

Processing time by trade:
```
fields @timestamp, trade_id, processing_time
| filter @message like /Processing complete/
| stats avg(processing_time) as avg_time by trade_id
```

Error patterns:
```
fields @timestamp, @message
| filter @message like /ERROR/
| parse @message /ERROR: (?<error_type>.*?) -/
| stats count() by error_type
```

## Monitoring Best Practices

1. **Set up alerts** for critical metrics (error rate, latency)
2. **Review dashboard** daily for trends
3. **Investigate anomalies** using X-Ray traces
4. **Analyze logs** for error patterns
5. **Monitor costs** of CloudWatch usage

## Cost Optimization

- Log retention: 30 days (adjust as needed)
- X-Ray sampling: 5% (adjust based on traffic)
- Metric resolution: 5 minutes (standard)
- Dashboard refresh: Manual (avoid auto-refresh)
EOT
}

# Outputs
output "cloudwatch_log_groups" {
  description = "Map of agent names to CloudWatch log group names"
  value = {
    pdf_adapter          = aws_cloudwatch_log_group.pdf_adapter_agent.name
    trade_extraction     = aws_cloudwatch_log_group.trade_extraction_agent.name
    trade_matching       = aws_cloudwatch_log_group.trade_matching_agent.name
    exception_management = aws_cloudwatch_log_group.exception_management_agent.name
    orchestrator         = aws_cloudwatch_log_group.orchestrator_agent.name
  }
}

output "metric_namespace" {
  description = "CloudWatch metric namespace for AgentCore"
  value       = local.metric_namespace
}

output "alerts_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = aws_sns_topic.agentcore_alerts.arn
}

output "dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.agentcore_dashboard.dashboard_name
}

output "observability_config_file" {
  description = "Path to observability configuration file"
  value       = local_file.agentcore_observability_config.filename
}

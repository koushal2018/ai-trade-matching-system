# AgentCore Observability Setup

This directory contains configuration for AgentCore Observability resources.

## CloudWatch Log Groups

Each agent has a dedicated log group:
- PDF Adapter: /aws/agentcore/trade-matching-system/pdf-adapter-production
- Trade Extraction: /aws/agentcore/trade-matching-system/trade-extraction-production
- Trade Matching: /aws/agentcore/trade-matching-system/trade-matching-production
- Exception Management: /aws/agentcore/trade-matching-system/exception-management-production
- Orchestrator: /aws/agentcore/trade-matching-system/orchestrator-production

## Metrics

Metrics are published to namespace: `AgentCore/trade-matching-system`

### Key Metrics:
1. **ProcessingLatency**: Time taken to process requests (milliseconds)
2. **ErrorRate**: Percentage of failed requests
3. **Throughput**: Number of trades processed per hour

### Dimensions:
- Agent: PDFAdapter, TradeExtraction, TradeMatching, ExceptionManagement, Orchestrator
- Environment: production

## Distributed Tracing

X-Ray tracing is enabled with 5% sampling rate.

### View Traces:
```bash
aws xray get-trace-summaries \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --region us-east-1
```

### Trace a Specific Request:
```bash
aws xray get-trace-graph \
  --trace-ids <trace-id> \
  --region us-east-1
```

## Alarms

### Configured Alarms:
1. **PDF Adapter Error Rate**: Triggers when error rate > 5%
2. **PDF Adapter Latency**: Triggers when latency > 30 seconds
3. **Trade Matching Error Rate**: Triggers when error rate > 5%
4. **Latency Anomaly**: Triggers when latency > 2x baseline

### Alert Notifications:
- SNS Topic: arn:aws:sns:us-east-1:401552979575:trade-matching-system-agentcore-alerts-production
- Subscriptions: Email notifications to configured addresses

## Dashboard

CloudWatch Dashboard: trade-matching-system-agentcore-production

View dashboard:
```bash
aws cloudwatch get-dashboard \
  --dashboard-name trade-matching-system-agentcore-production \
  --region us-east-1
```

Or visit: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=trade-matching-system-agentcore-production

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
    Namespace='AgentCore/trade-matching-system',
    MetricData=[
        {
            'MetricName': 'ProcessingLatency',
            'Value': latency_ms,
            'Unit': 'Milliseconds',
            'Dimensions': [
                {'Name': 'Agent', 'Value': 'PDFAdapter'},
                {'Name': 'Environment', 'Value': 'production'}
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

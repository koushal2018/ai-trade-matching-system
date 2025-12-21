# CloudWatch Logs Insights Queries for Trade Extraction Agent

## Performance Analysis
```
fields @timestamp, correlation_id, processing_time_ms, document_id
| filter @message like /INVOKE_SUCCESS/
| stats avg(processing_time_ms), max(processing_time_ms), min(processing_time_ms) by bin(5m)
```

## Error Analysis
```
fields @timestamp, correlation_id, error_type, error_message, document_id
| filter @message like /INVOKE_ERROR/
| stats count() by error_type
| sort count desc
```

## AWS Operations Monitoring
```
fields @timestamp, service_name, operation_name, operation_time_ms, success
| filter @message like /AWS_OPERATION/
| stats avg(operation_time_ms) by service_name, operation_name
| sort avg desc
```

## Slow Processing Detection
```
fields @timestamp, correlation_id, processing_time_ms, document_id
| filter processing_time_ms > 30000
| sort @timestamp desc
```

## Token Usage Analysis
```
fields @timestamp, correlation_id, token_usage.total_tokens, model_id
| filter @message like /INVOKE_SUCCESS/
| stats avg(token_usage.total_tokens), sum(token_usage.total_tokens) by bin(1h)
```

## Source Type Distribution
```
fields @timestamp, source_type, document_id
| filter @message like /INVOKE_START/
| stats count() by source_type
```
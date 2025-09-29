# API Reference

## Overview

The AI Trade Matching System exposes a RESTful API built with FastAPI that provides endpoints for document processing, status monitoring, and system health checks. The API is designed for integration with trading systems, operations dashboards, and automated workflows.

**Base URL**: `https://your-eks-cluster-endpoint`  
**API Version**: v1  
**Content Type**: `application/json`

## Endpoints

### Processing Endpoints

#### POST /process
Initiates processing of a trade document from S3.

**Request**:
```http
POST /process
Content-Type: application/json

{
    "s3_bucket": "trade-documents-production",
    "s3_key": "BANK/GCS382857_V1.pdf",
    "source_type": "BANK",
    "event_time": "2024-01-15T10:30:00Z",
    "unique_identifier": "GCS382857",
    "metadata": {
        "object_size": 1024000,
        "lambda_request_id": "abc-123-def",
        "processing_timestamp": "2024-01-15T10:30:00Z"
    }
}
```

**Parameters**:
- `s3_bucket` (string, required): S3 bucket containing the document
- `s3_key` (string, required): S3 object key for the PDF document
- `source_type` (string, required): Document source - "BANK" or "COUNTERPARTY"
- `event_time` (string, required): ISO 8601 timestamp of the S3 event
- `unique_identifier` (string, required): Unique identifier for the trade
- `metadata` (object, optional): Additional processing metadata

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "processing_id": "fab-test_1759053194",
    "status": "initiated",
    "message": "Processing started successfully",
    "unique_identifier": "GCS382857",
    "estimated_completion": "2024-01-15T10:35:00Z",
    "s3_bucket": "trade-documents-production",
    "s3_key": "BANK/GCS382857_V1.pdf"
}
```

**Error Response**:
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
    "error": "Invalid source_type",
    "message": "source_type must be either 'BANK' or 'COUNTERPARTY'",
    "details": {
        "provided_value": "INVALID",
        "valid_values": ["BANK", "COUNTERPARTY"]
    }
}
```

#### GET /status/{processing_id}
Retrieves the current status of a processing job.

**Request**:
```http
GET /status/fab-test_1759053194
```

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "processing_id": "fab-test_1759053194",
    "status": "completed",
    "unique_identifier": "GCS382857",
    "started_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:33:45Z",
    "duration_seconds": 225,
    "stages": {
        "document_processing": {
            "status": "completed",
            "duration_seconds": 15,
            "output": "4 pages converted to images"
        },
        "ocr_extraction": {
            "status": "completed", 
            "duration_seconds": 120,
            "output": "Trade data extracted successfully"
        },
        "data_storage": {
            "status": "completed",
            "duration_seconds": 5,
            "output": "Stored in BankTradeData table"
        },
        "matching_analysis": {
            "status": "completed",
            "duration_seconds": 85,
            "output": "Match found with counterparty trade ML-REF-789456"
        }
    },
    "results": {
        "trade_id": "GCS382857",
        "counterparty": "MERRILL LYNCH INTERNATIONAL",
        "match_status": "MATCHED",
        "match_confidence": 0.95,
        "report_s3_key": "reports/matching_report_GCS382857_20240115_103345.md"
    }
}
```

**Status Values**:
- `initiated`: Processing has started
- `in_progress`: Currently being processed
- `completed`: Successfully completed
- `failed`: Processing failed
- `timeout`: Processing timed out

#### GET /status
Retrieves status for multiple processing jobs with optional filtering.

**Request**:
```http
GET /status?unique_identifier=GCS382857&limit=10&status=completed
```

**Query Parameters**:
- `unique_identifier` (string, optional): Filter by unique identifier
- `status` (string, optional): Filter by processing status
- `limit` (integer, optional): Maximum number of results (default: 50, max: 100)
- `offset` (integer, optional): Pagination offset (default: 0)
- `start_date` (string, optional): Filter by start date (ISO 8601)
- `end_date` (string, optional): Filter by end date (ISO 8601)

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "total_count": 1,
    "returned_count": 1,
    "offset": 0,
    "limit": 10,
    "results": [
        {
            "processing_id": "fab-test_1759053194",
            "status": "completed",
            "unique_identifier": "GCS382857",
            "started_at": "2024-01-15T10:30:00Z",
            "completed_at": "2024-01-15T10:33:45Z"
        }
    ]
}
```

### Health and Monitoring Endpoints

#### GET /health
Basic health check endpoint for load balancers and monitoring systems.

**Request**:
```http
GET /health
```

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.0.0",
    "uptime_seconds": 3600,
    "checks": {
        "database": "healthy",
        "s3": "healthy", 
        "bedrock": "healthy",
        "mcp_server": "healthy"
    }
}
```

#### GET /ready
Readiness check for Kubernetes readiness probes.

**Request**:
```http
GET /ready
```

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "status": "ready",
    "timestamp": "2024-01-15T10:30:00Z",
    "dependencies": {
        "dynamodb_mcp": "connected",
        "aws_bedrock": "available",
        "s3_access": "verified"
    }
}
```

#### GET /metrics
Prometheus metrics endpoint for monitoring and alerting.

**Request**:
```http
GET /metrics
```

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: text/plain

# HELP trade_processing_total Total number of trade processing requests
# TYPE trade_processing_total counter
trade_processing_total{source_type="BANK"} 150
trade_processing_total{source_type="COUNTERPARTY"} 142

# HELP trade_processing_duration_seconds Time spent processing trades
# TYPE trade_processing_duration_seconds histogram
trade_processing_duration_seconds_bucket{le="60"} 45
trade_processing_duration_seconds_bucket{le="120"} 180
trade_processing_duration_seconds_bucket{le="300"} 285
trade_processing_duration_seconds_bucket{le="+Inf"} 292

# HELP trade_matches_total Total number of trade matches found
# TYPE trade_matches_total counter
trade_matches_total{match_type="MATCHED"} 275
trade_matches_total{match_type="PROBABLE_MATCH"} 12
trade_matches_total{match_type="BREAK"} 5
```

### Batch Processing Endpoints

#### POST /batch/process
Process multiple documents in a single request.

**Request**:
```http
POST /batch/process
Content-Type: application/json

{
    "documents": [
        {
            "s3_bucket": "trade-documents-production",
            "s3_key": "BANK/GCS382857_V1.pdf",
            "source_type": "BANK",
            "unique_identifier": "GCS382857"
        },
        {
            "s3_bucket": "trade-documents-production", 
            "s3_key": "COUNTERPARTY/ML-REF-789456.pdf",
            "source_type": "COUNTERPARTY",
            "unique_identifier": "ML-REF-789456"
        }
    ],
    "options": {
        "parallel_processing": true,
        "max_concurrent": 3,
        "timeout_seconds": 600
    }
}
```

**Response**:
```http
HTTP/1.1 202 Accepted
Content-Type: application/json

{
    "batch_id": "batch_20240115_103000",
    "status": "initiated",
    "total_documents": 2,
    "processing_ids": [
        "fab-test_1759053194",
        "ml-test_1759053195"
    ],
    "estimated_completion": "2024-01-15T10:40:00Z"
}
```

## Authentication

The API uses AWS IAM-based authentication through IRSA (IAM Roles for Service Accounts) when deployed on EKS. For external access, API Gateway with IAM authentication is recommended.

### IRSA Configuration
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: trade-matching-sa
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT:role/trade-matching-irsa-role
```

### Required IAM Permissions
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "dynamodb:GetItem",
                "dynamodb:PutItem", 
                "dynamodb:Query",
                "dynamodb:Scan",
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": [
                "arn:aws:bedrock:*:*:model/*",
                "arn:aws:dynamodb:*:*:table/BankTradeData*",
                "arn:aws:dynamodb:*:*:table/CounterpartyTradeData*",
                "arn:aws:s3:::trade-documents-production/*"
            ]
        }
    ]
}
```

### API Gateway Integration (Optional)
For external access, integrate with AWS API Gateway:

```yaml
# API Gateway configuration
Resources:
  TradeMatchingApi:
    Type: AWS::ApiGateway::RestApi
    Properties:
      Name: trade-matching-api
      EndpointConfiguration:
        Types:
          - REGIONAL
      
  ProcessResource:
    Type: AWS::ApiGateway::Resource
    Properties:
      RestApiId: !Ref TradeMatchingApi
      ParentId: !GetAtt TradeMatchingApi.RootResourceId
      PathPart: process
```

## Error Handling

### Standard Error Response Format
```json
{
    "error": "error_code",
    "message": "Human-readable error description",
    "details": {
        "field": "Additional context",
        "timestamp": "2024-01-15T10:30:00Z",
        "request_id": "req_abc123def456"
    }
}
```

### HTTP Status Codes

| Status Code | Description | Common Causes |
|-------------|-------------|---------------|
| 200 | Success | Request completed successfully |
| 202 | Accepted | Async processing initiated |
| 400 | Bad Request | Invalid parameters, malformed JSON |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Processing ID not found |
| 409 | Conflict | Duplicate processing request |
| 422 | Unprocessable Entity | Valid JSON but invalid business logic |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 502 | Bad Gateway | Upstream service unavailable |
| 503 | Service Unavailable | System overloaded or maintenance |
| 504 | Gateway Timeout | Processing timeout exceeded |

### Error Codes

| Error Code | Description | Resolution |
|------------|-------------|------------|
| `invalid_source_type` | Invalid source_type parameter | Use "BANK" or "COUNTERPARTY" |
| `s3_access_denied` | Cannot access S3 object | Check IAM permissions and object existence |
| `processing_timeout` | Processing exceeded time limit | Retry with smaller document or increase timeout |
| `bedrock_unavailable` | AWS Bedrock service unavailable | Check service status and retry |
| `dynamodb_error` | Database operation failed | Check table status and permissions |
| `duplicate_processing` | Document already being processed | Wait for completion or check status |
| `invalid_pdf` | PDF document is corrupted or invalid | Verify document integrity |
| `rate_limit_exceeded` | Too many concurrent requests | Implement backoff and retry logic |

### Retry Logic
Implement exponential backoff for transient errors:

```python
import time
import random

def retry_with_backoff(func, max_retries=3, base_delay=1):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            time.sleep(delay)
```

### Rate Limiting
- **Default Limits**: 100 requests per minute per IP
- **Burst Capacity**: 20 requests per second
- **Headers**: Rate limit information included in response headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

This API documentation provides comprehensive guidance for integrating with the AI Trade Matching System, ensuring reliable and efficient trade processing operations.
# Trade Matching Web Portal API

FastAPI backend for the AI Trade Matching Web Portal.

## Features

- REST API for agent status, HITL decisions, audit trail, and metrics
- WebSocket endpoint for real-time updates
- JWT authentication
- DynamoDB integration

## Endpoints

### Agents
- `GET /api/agents/status` - Get health status of all agents

### HITL
- `GET /api/hitl/pending` - Get pending HITL reviews
- `GET /api/hitl/{review_id}` - Get specific review
- `POST /api/hitl/{review_id}/decision` - Submit decision

### Audit
- `GET /api/audit` - Get audit records with filtering
- `GET /api/audit/export` - Export audit records (CSV/JSON/XML)

### Metrics
- `GET /api/metrics/processing` - Get processing metrics

### Matching
- `GET /api/matching/results` - Get matching results

### WebSocket
- `WS /ws` - Real-time updates

## Setup

```bash
cd web-portal-api
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

## Environment Variables

```env
AWS_DEFAULT_REGION=us-east-1
DYNAMODB_BANK_TABLE=BankTradeData
DYNAMODB_COUNTERPARTY_TABLE=CounterpartyTradeData
DYNAMODB_EXCEPTIONS_TABLE=ExceptionsTable
DYNAMODB_AUDIT_TABLE=AuditTrail
DYNAMODB_AGENT_REGISTRY_TABLE=AgentRegistry
DYNAMODB_HITL_TABLE=HITLReviews
S3_BUCKET_NAME=trade-matching-us-east-1
JWT_SECRET_KEY=your-secret-key
HITL_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/...
```

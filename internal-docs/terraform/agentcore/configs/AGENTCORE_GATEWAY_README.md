# AgentCore Gateway Setup

This directory contains configuration for AgentCore Gateway resources.

## Gateway Resources

### 1. DynamoDB MCP Gateway
- **Name**: trade-matching-system-dynamodb-gateway-production
- **Target Type**: MCP_SERVER
- **Purpose**: Expose DynamoDB operations as MCP tools
- **Operations**: GetItem, PutItem, UpdateItem, DeleteItem, Query, Scan, BatchGetItem, BatchWriteItem
- **Resources**:
  - BankTradeData-production
  - CounterpartyTradeData-production
  - trade-matching-system-exceptions-production
  - trade-matching-system-agent-registry-production

### 2. S3 MCP Gateway
- **Name**: trade-matching-system-s3-gateway-production
- **Target Type**: MCP_SERVER
- **Purpose**: Expose S3 operations as MCP tools
- **Operations**: GetObject, PutObject, DeleteObject, ListObjects, HeadObject
- **Resources**:
  - trade-matching-system-agentcore-production

### 3. Custom Operations Gateway
- **Name**: trade-matching-system-custom-ops-gateway-production
- **Target Type**: LAMBDA
- **Purpose**: Expose custom business logic as MCP tools
- **Lambda Function**: trade-matching-system-custom-operations-production

## Deployment

### Using AWS CLI (Manual)

Run the deployment script:
```bash
cd ./scripts
./deploy_agentcore_gateway.sh
```

### Using AgentCore CLI (Recommended)

Once AgentCore CLI is available, use:
```bash
agentcore gateway create --config ./configs/agentcore_gateway_config.json
```

## Verification

List all gateways:
```bash
aws bedrock-agent list-gateways --region us-east-1
```

Get details of a specific gateway:
```bash
aws bedrock-agent describe-gateway \
  --gateway-id <gateway-id> \
  --region us-east-1
```

## Integration with Agents

Agents can access gateway tools using the MCP protocol:

### DynamoDB Operations
```python
from bedrock_agentcore import Gateway

dynamodb_gateway = Gateway(name="trade-matching-system-dynamodb-gateway-production")

# Put item
dynamodb_gateway.invoke_tool("PutItem", {
    "TableName": "BankTradeData-production",
    "Item": {
        "Trade_ID": {"S": "GCS382857"},
        "TRADE_SOURCE": {"S": "BANK"},
        "notional": {"N": "1000000"}
    }
})

# Query items
result = dynamodb_gateway.invoke_tool("Query", {
    "TableName": "BankTradeData-production",
    "KeyConditionExpression": "Trade_ID = :trade_id",
    "ExpressionAttributeValues": {
        ":trade_id": {"S": "GCS382857"}
    }
})
```

### S3 Operations
```python
s3_gateway = Gateway(name="trade-matching-system-s3-gateway-production")

# Put object
s3_gateway.invoke_tool("PutObject", {
    "Bucket": "trade-matching-system-agentcore-production",
    "Key": "extracted/BANK/trade_123.json",
    "Body": json.dumps(trade_data)
})

# Get object
result = s3_gateway.invoke_tool("GetObject", {
    "Bucket": "trade-matching-system-agentcore-production",
    "Key": "extracted/BANK/trade_123.json"
})
```

### Custom Operations
```python
custom_gateway = Gateway(name="trade-matching-system-custom-ops-gateway-production")

# Invoke custom operation
result = custom_gateway.invoke_tool("CustomOperation", {
    "operation": "validate_trade",
    "trade_id": "GCS382857"
})
```

## Authentication

All gateways use IAM authentication with the AgentCore Gateway role:
- **Role ARN**: arn:aws:iam::401552979575:role/trade-matching-system-agentcore-gateway-production

Agents must have permissions to assume this role or have equivalent permissions.

## Monitoring

Monitor gateway usage:
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/BedrockAgent \
  --metric-name GatewayInvocations \
  --dimensions Name=GatewayName,Value=trade-matching-system-dynamodb-gateway-production \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-31T23:59:59Z \
  --period 3600 \
  --statistics Sum \
  --region us-east-1
```

## Cleanup

To delete gateway resources:
```bash
aws bedrock-agent delete-gateway \
  --gateway-id <gateway-id> \
  --region us-east-1
```

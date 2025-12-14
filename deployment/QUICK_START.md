# AgentCore Deployment - Quick Start Guide

This guide will help you deploy all agents to Amazon Bedrock AgentCore Runtime in under 30 minutes.

## Prerequisites (5 minutes)

### 1. Install Required Tools

```bash
# Install AgentCore CLI
pip install bedrock-agentcore

# Verify installation
agentcore --version
```

### 2. Configure AWS Credentials

```bash
# Configure AWS CLI
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: us-east-1
# Default output format: json

# Verify credentials
aws sts get-caller-identity
```

### 3. Set Environment Variables

```bash
# Set AgentCore Memory ARN (get from infrastructure setup)
export AGENTCORE_MEMORY_ARN="arn:aws:bedrock:us-east-1:ACCOUNT_ID:memory/MEMORY_ID"

# Set S3 bucket name
export S3_BUCKET_NAME="trade-matching-bucket"

# Verify
echo $AGENTCORE_MEMORY_ARN
echo $S3_BUCKET_NAME
```

## Deploy All Agents (15 minutes)

### Option 1: One-Command Deployment (Recommended)

```bash
# Navigate to deployment directory
cd deployment

# Make script executable
chmod +x deploy_all.sh

# Deploy all agents
./deploy_all.sh
```

This will deploy all 5 agents in the correct order with automatic validation.

### Option 2: Manual Deployment

If you prefer to deploy agents individually:

```bash
# 1. Deploy Orchestrator Agent
cd deployment/orchestrator
chmod +x deploy.sh
./deploy.sh

# 2. Deploy PDF Adapter Agent
cd ../pdf_adapter
chmod +x deploy.sh
./deploy.sh

# 3. Deploy Trade Extraction Agent
cd ../trade_extraction
chmod +x deploy.sh
./deploy.sh

# 4. Deploy Trade Matching Agent
cd ../trade_matching
chmod +x deploy.sh
./deploy.sh

# 5. Deploy Exception Management Agent
cd ../exception_management
chmod +x deploy.sh
./deploy.sh
```

## Validate Deployment (5 minutes)

```bash
# Run validation script
cd deployment
chmod +x validate_deployment.sh
./validate_deployment.sh
```

This will check:
- ✓ All agents are deployed and active
- ✓ Infrastructure resources exist
- ✓ Agent invocations work correctly
- ✓ Logs are accessible

## Test End-to-End Workflow (5 minutes)

### 1. Upload Test PDF

```bash
# Upload a test trade confirmation PDF
aws s3 cp test_trade.pdf s3://trade-matching-bucket/COUNTERPARTY/test_trade.pdf
```

### 2. Trigger PDF Processing

```bash
# Send event to document-upload-events queue
aws sqs send-message \
  --queue-url $(aws sqs get-queue-url --queue-name document-upload-events.fifo --query 'QueueUrl' --output text) \
  --message-body '{
    "document_path": "s3://trade-matching-bucket/COUNTERPARTY/test_trade.pdf",
    "document_id": "test_001",
    "source_type": "COUNTERPARTY"
  }' \
  --message-group-id "test-group"
```

### 3. Monitor Processing

```bash
# Watch PDF Adapter logs
agentcore logs --agent-name pdf-adapter-agent --follow

# In another terminal, watch Trade Extraction logs
agentcore logs --agent-name trade-extraction-agent --follow

# In another terminal, watch Trade Matching logs
agentcore logs --agent-name trade-matching-agent --follow
```

### 4. Verify Results

```bash
# Check if trade was extracted and stored
aws dynamodb get-item \
  --table-name CounterpartyTradeData \
  --key '{"Trade_ID": {"S": "test_001"}}'

# Check if matching report was generated
aws s3 ls s3://trade-matching-bucket/reports/
```

## Common Issues and Solutions

### Issue: "agentcore: command not found"

**Solution:**
```bash
pip install bedrock-agentcore
# Or if using virtual environment:
source .venv/bin/activate
pip install bedrock-agentcore
```

### Issue: "AWS credentials not configured"

**Solution:**
```bash
aws configure
# Or set environment variables:
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=us-east-1
```

### Issue: "AGENTCORE_MEMORY_ARN not set"

**Solution:**
```bash
# Get Memory ARN from AgentCore console or CLI
export AGENTCORE_MEMORY_ARN="arn:aws:bedrock:us-east-1:123456789012:memory/abc123"
```

### Issue: "Agent deployment failed"

**Solution:**
```bash
# Check agent logs for errors
agentcore logs --agent-name <agent-name> --tail 50

# Delete and redeploy
agentcore delete --agent-name <agent-name>
cd deployment/<agent-name>
./deploy.sh
```

### Issue: "Agent invocation times out"

**Solution:**
- Check if agent has sufficient memory (increase in agentcore.yaml)
- Verify network connectivity to AWS services
- Check IAM permissions for agent execution role

## Next Steps

After successful deployment:

1. **Set Up Monitoring**
   - Configure CloudWatch dashboards
   - Set up billing alarms
   - Enable detailed metrics

2. **Deploy Web Portal**
   - Deploy React frontend for HITL interactions
   - Configure WebSocket connections
   - Set up authentication

3. **Run Load Tests**
   - Test with 100 concurrent requests
   - Verify auto-scaling works
   - Measure end-to-end latency

4. **Enable Production Traffic**
   - Start with 10% traffic
   - Gradually increase to 100%
   - Monitor error rates and SLAs

5. **Document Procedures**
   - Create runbooks for common issues
   - Document escalation procedures
   - Train operations team

## Useful Commands

```bash
# List all deployed agents
agentcore list --region us-east-1

# Get agent details
agentcore describe --agent-name <agent-name>

# View agent logs
agentcore logs --agent-name <agent-name> --tail 100

# Follow logs in real-time
agentcore logs --agent-name <agent-name> --follow

# Invoke agent manually
agentcore invoke --agent-name <agent-name> --payload '{...}'

# Update agent configuration
agentcore update --agent-name <agent-name> --config agentcore.yaml

# Delete agent
agentcore delete --agent-name <agent-name>

# Check agent metrics
agentcore metrics --agent-name <agent-name> --period 1h
```

## Support

For help:
- Check [README.md](README.md) for detailed documentation
- Review [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for step-by-step guide
- Check agent logs for error details
- Contact AWS Support for AgentCore-specific issues

## Success Criteria

Your deployment is successful when:
- ✓ All 5 agents show `ACTIVE` status
- ✓ Validation script passes all checks
- ✓ End-to-end test completes in ≤90 seconds
- ✓ No errors in agent logs
- ✓ Trade data stored correctly in DynamoDB
- ✓ Matching reports generated in S3

Congratulations! Your AgentCore deployment is complete. 🎉

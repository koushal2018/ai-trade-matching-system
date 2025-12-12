# AgentCore Deployment Guide

This directory contains deployment packages and scripts for deploying all agents to Amazon Bedrock AgentCore Runtime.

## Prerequisites

**IMPORTANT**: Before deploying agents, you must complete the setup steps in [SETUP_GUIDE.md](SETUP_GUIDE.md).

Quick checklist:
- [ ] AgentCore SDK installed: `pip install bedrock-agentcore`
- [ ] AWS credentials configured
- [ ] AgentCore Memory resource created (run `python deployment/setup_memory.py`)
- [ ] Environment variables set:
  - `AGENTCORE_MEMORY_ARN` (from memory setup)
  - `S3_BUCKET_NAME`
- [ ] Infrastructure provisioned (S3, DynamoDB, SQS from tasks 1.1-1.3)

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed step-by-step instructions.

## Directory Structure

```
deployment/
├── README.md                           # This file
├── deploy_all.sh                       # Master deployment script
├── pdf_adapter/
│   ├── requirements.txt                # Dependencies
│   └── deploy.sh                       # Deployment script
├── trade_extraction/
│   ├── requirements.txt
│   └── deploy.sh
├── trade_matching/
│   ├── requirements.txt
│   └── deploy.sh
├── exception_management/
│   ├── requirements.txt
│   └── deploy.sh
└── orchestrator/
    ├── requirements.txt
    └── deploy.sh
```

## Deployment Options

### Option 1: Deploy All Agents (Recommended)

Deploy all agents in the correct order with a single command:

```bash
cd deployment
chmod +x deploy_all.sh
./deploy_all.sh
```

This will:
1. Check prerequisites
2. Deploy Orchestrator Agent first
3. Deploy PDF Adapter Agent
4. Deploy Trade Extraction Agent
5. Deploy Trade Matching Agent
6. Deploy Exception Management Agent
7. Wait 30 seconds between deployments to avoid rate limits

### Option 2: Deploy Individual Agents

Deploy agents one at a time:

```bash
# Deploy PDF Adapter Agent
cd deployment/pdf_adapter
chmod +x deploy.sh
./deploy.sh

# Deploy Trade Extraction Agent
cd ../trade_extraction
chmod +x deploy.sh
./deploy.sh

# And so on...
```

## Deployment Steps (Per Agent)

Each deployment script performs these steps:

1. **Configure Agent**: Set up agent with runtime, region, and entry point
2. **Attach Memory**: Configure AgentCore Memory integration
3. **Launch Agent**: Deploy to AgentCore Runtime
4. **Test Agent**: Invoke with sample payload to verify deployment

## Agent Details

### 1. Orchestrator Agent

- **Name**: `orchestrator-agent`
- **Runtime**: Python 3.11
- **Memory Strategy**: Semantic
- **Purpose**: Monitor SLAs, enforce compliance, coordinate workflows

### 2. PDF Adapter Agent

- **Name**: `pdf-adapter-agent`
- **Runtime**: Python 3.11
- **Memory Strategy**: Event
- **Purpose**: Convert PDFs to images and extract text via OCR

### 3. Trade Data Extraction Agent

- **Name**: `trade-extraction-agent`
- **Runtime**: Python 3.11
- **Memory Strategy**: Semantic
- **Purpose**: Parse OCR text into structured trade data

### 4. Trade Matching Agent

- **Name**: `trade-matching-agent`
- **Runtime**: Python 3.11
- **Memory Strategy**: Semantic
- **Purpose**: Match bank and counterparty trades with fuzzy matching

### 5. Exception Management Agent

- **Name**: `exception-management-agent`
- **Runtime**: Python 3.11
- **Memory Strategy**: Event + Semantic
- **Purpose**: Handle errors, triage exceptions, route to handlers

## Verification

### Check Agent Status

```bash
# List all deployed agents
agentcore list --region us-east-1

# Get specific agent details
agentcore describe --agent-name pdf-adapter-agent --region us-east-1
```

### View Agent Logs

```bash
# View logs for an agent
agentcore logs --agent-name pdf-adapter-agent --region us-east-1

# Follow logs in real-time
agentcore logs --agent-name pdf-adapter-agent --region us-east-1 --follow
```

### Test Agent Invocation

```bash
# Test PDF Adapter Agent
agentcore invoke \
  --agent-name pdf-adapter-agent \
  --region us-east-1 \
  --payload '{
    "document_path": "s3://trade-matching-bucket/COUNTERPARTY/test.pdf",
    "document_id": "test_001",
    "source_type": "COUNTERPARTY"
  }'

# Test Trade Extraction Agent
agentcore invoke \
  --agent-name trade-extraction-agent \
  --region us-east-1 \
  --payload '{
    "event_type": "PDF_PROCESSED",
    "document_id": "test_001",
    "canonical_output_location": "s3://trade-matching-bucket/extracted/COUNTERPARTY/test_001.json"
  }'
```

## Troubleshooting

### Agent Fails to Deploy

1. Check AWS credentials: `aws sts get-caller-identity`
2. Verify region is set to `us-east-1`
3. Check IAM permissions for AgentCore operations
4. Review deployment logs for specific errors

### Agent Invocation Fails

1. Check agent status: `agentcore describe --agent-name <agent-name>`
2. Review agent logs: `agentcore logs --agent-name <agent-name>`
3. Verify payload format matches expected schema
4. Check S3 bucket permissions and file existence

### Memory Integration Issues

1. Verify `AGENTCORE_MEMORY_ARN` is set correctly
2. Check IAM permissions for AgentCore Memory access
3. Ensure memory resource exists in `us-east-1`

## Updating Agents

To update an agent after code changes:

```bash
# Navigate to agent directory
cd deployment/pdf_adapter

# Re-run deployment script
./deploy.sh
```

AgentCore supports zero-downtime deployments, so updates won't disrupt running workflows.

## Cleanup

To remove all deployed agents:

```bash
# Delete individual agents
agentcore delete --agent-name pdf-adapter-agent --region us-east-1
agentcore delete --agent-name trade-extraction-agent --region us-east-1
agentcore delete --agent-name trade-matching-agent --region us-east-1
agentcore delete --agent-name exception-management-agent --region us-east-1
agentcore delete --agent-name orchestrator-agent --region us-east-1
```

## Cost Considerations

- AgentCore Runtime charges per invocation and compute time
- Memory storage has monthly costs based on data volume
- Monitor costs via AWS Cost Explorer
- Set up billing alarms for unexpected usage

## Next Steps

After successful deployment:

1. **Configure SQS Queues**: Set up event queues for agent communication
2. **Deploy Web Portal**: Deploy React frontend for monitoring and HITL
3. **Run Integration Tests**: Test end-to-end workflow with sample PDFs
4. **Set Up Monitoring**: Configure CloudWatch dashboards and alarms
5. **Enable Observability**: Integrate with AgentCore Observability for tracing

## Support

For issues or questions:
- Check AgentCore documentation: https://docs.aws.amazon.com/bedrock/agentcore
- Review agent logs for error details
- Contact AWS Support for AgentCore-specific issues

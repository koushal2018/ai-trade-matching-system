# AgentCore Deployment Checklist

Use this checklist to ensure all prerequisites are met and deployment steps are completed successfully.

## Pre-Deployment Checklist

### Infrastructure Setup

- [ ] AWS account configured with access to `us-east-1` region
- [ ] S3 bucket created: `trade-matching-bucket`
- [ ] DynamoDB tables created:
  - [ ] `BankTradeData`
  - [ ] `CounterpartyTradeData`
  - [ ] `ExceptionsTable`
  - [ ] `AgentRegistry`
- [ ] SQS queues created:
  - [ ] `document-upload-events` (FIFO)
  - [ ] `extraction-events` (Standard)
  - [ ] `matching-events` (Standard)
  - [ ] `exception-events` (Standard)
  - [ ] `hitl-review-queue` (FIFO)
  - [ ] `ops-desk-queue` (FIFO)
  - [ ] `senior-ops-queue` (FIFO)
  - [ ] `compliance-queue` (FIFO)
  - [ ] `engineering-queue` (Standard)
  - [ ] `orchestrator-monitoring-queue` (Standard)
- [ ] AgentCore Memory resources created:
  - [ ] Semantic memory for trade patterns
  - [ ] Event memory for processing history
  - [ ] Memory for exception patterns and RL policies
- [ ] AgentCore Gateway configured with MCP targets:
  - [ ] DynamoDB operations gateway
  - [ ] S3 operations gateway
  - [ ] Lambda custom operations target
- [ ] AgentCore Observability enabled:
  - [ ] Distributed tracing configured
  - [ ] Metrics collection enabled
  - [ ] Anomaly detection rules set up
  - [ ] Alerting rules configured
- [ ] AgentCore Identity configured:
  - [ ] Cognito User Pool created
  - [ ] OAuth2 client credentials flow set up
  - [ ] User roles configured (Admin, Operator, Auditor)
  - [ ] MFA enabled for admin users
- [ ] IAM roles and policies configured:
  - [ ] AgentCore Runtime execution role
  - [ ] AgentCore Gateway role
  - [ ] Lambda execution roles
  - [ ] Cross-service permissions (S3, DynamoDB, SQS, Bedrock)

### Tools and CLI

- [ ] AWS CLI installed and configured
- [ ] AgentCore CLI installed: `pip install bedrock-agentcore`
- [ ] Python 3.11+ installed
- [ ] Environment variables set:
  - [ ] `AWS_ACCESS_KEY_ID`
  - [ ] `AWS_SECRET_ACCESS_KEY`
  - [ ] `AWS_DEFAULT_REGION=us-east-1`
  - [ ] `AGENTCORE_MEMORY_ARN`
  - [ ] `S3_BUCKET_NAME`

### Code Preparation

- [ ] All agent implementations completed and tested locally
- [ ] Dependencies listed in requirements.txt files
- [ ] Agent entry points defined correctly
- [ ] Configuration files reviewed and updated

## Deployment Checklist

### Agent Deployments

#### 1. Orchestrator Agent

- [ ] Navigate to `deployment/orchestrator/`
- [ ] Review `agentcore.yaml` configuration
- [ ] Run deployment script: `./deploy.sh`
- [ ] Verify deployment: `agentcore describe --agent-name orchestrator-agent`
- [ ] Test invocation with sample payload
- [ ] Check logs for errors: `agentcore logs --agent-name orchestrator-agent`
- [ ] Verify agent registered in AgentRegistry table

#### 2. PDF Adapter Agent

- [ ] Navigate to `deployment/pdf_adapter/`
- [ ] Review `agentcore.yaml` configuration
- [ ] Run deployment script: `./deploy.sh`
- [ ] Verify deployment: `agentcore describe --agent-name pdf-adapter-agent`
- [ ] Test invocation with sample PDF
- [ ] Check logs for errors: `agentcore logs --agent-name pdf-adapter-agent`
- [ ] Verify agent registered in AgentRegistry table
- [ ] Verify memory integration: Check event memory for processing history

#### 3. Trade Data Extraction Agent

- [ ] Navigate to `deployment/trade_extraction/`
- [ ] Review `agentcore.yaml` configuration
- [ ] Run deployment script: `./deploy.sh`
- [ ] Verify deployment: `agentcore describe --agent-name trade-extraction-agent`
- [ ] Test invocation with sample canonical output
- [ ] Check logs for errors: `agentcore logs --agent-name trade-extraction-agent`
- [ ] Verify agent registered in AgentRegistry table
- [ ] Verify memory integration: Check semantic memory for trade patterns

#### 4. Trade Matching Agent

- [ ] Navigate to `deployment/trade_matching/`
- [ ] Review `agentcore.yaml` configuration
- [ ] Run deployment script: `./deploy.sh`
- [ ] Verify deployment: `agentcore describe --agent-name trade-matching-agent`
- [ ] Test invocation with sample trade data
- [ ] Check logs for errors: `agentcore logs --agent-name trade-matching-agent`
- [ ] Verify agent registered in AgentRegistry table
- [ ] Verify memory integration: Check semantic memory for matching decisions

#### 5. Exception Management Agent

- [ ] Navigate to `deployment/exception_management/`
- [ ] Review `agentcore.yaml` configuration
- [ ] Run deployment script: `./deploy.sh`
- [ ] Verify deployment: `agentcore describe --agent-name exception-management-agent`
- [ ] Test invocation with sample exception
- [ ] Check logs for errors: `agentcore logs --agent-name exception-management-agent`
- [ ] Verify agent registered in AgentRegistry table
- [ ] Verify memory integration: Check both event and semantic memory

## Post-Deployment Validation

### Agent Health Checks

- [ ] All agents show status: `ACTIVE`
- [ ] No deployment errors in CloudWatch logs
- [ ] Memory resources attached successfully
- [ ] Event subscriptions configured correctly
- [ ] Scaling policies active

### Integration Testing

- [ ] Upload test PDF to S3 `COUNTERPARTY/` folder
- [ ] Verify PDF Adapter processes document
- [ ] Verify Trade Extraction stores data in DynamoDB
- [ ] Verify Trade Matching generates report
- [ ] Verify Exception Management handles errors
- [ ] Verify Orchestrator monitors all agents
- [ ] Check end-to-end processing time (target: ≤90 seconds)

### Event Flow Validation

- [ ] Document upload triggers PDF Adapter
- [ ] PDF processing publishes to extraction queue
- [ ] Extraction publishes to matching queue
- [ ] Matching publishes to HITL or exception queue
- [ ] Exceptions routed to appropriate handler queues
- [ ] All events visible in orchestrator monitoring queue

### Memory Validation

- [ ] Trade patterns stored in semantic memory
- [ ] Processing history stored in event memory
- [ ] Exception patterns stored for RL learning
- [ ] Memory queries return results within 500ms

### Observability Validation

- [ ] Distributed traces visible in AgentCore Observability
- [ ] Metrics collected for all agents (latency, throughput, errors)
- [ ] Anomaly detection rules active
- [ ] Alerts configured and tested

### Security Validation

- [ ] AgentCore Identity authentication working
- [ ] JWT tokens validated for API calls
- [ ] RBAC enforced for permissions
- [ ] S3 encryption at rest enabled
- [ ] DynamoDB encryption at rest enabled
- [ ] TLS 1.3 for data in transit

## Rollback Plan

If deployment fails or issues arise:

1. **Stop Processing**
   ```bash
   # Pause all agents
   agentcore update --agent-name <agent-name> --status PAUSED
   ```

2. **Review Logs**
   ```bash
   # Check logs for errors
   agentcore logs --agent-name <agent-name> --tail 100
   ```

3. **Rollback Agent**
   ```bash
   # Delete problematic agent
   agentcore delete --agent-name <agent-name>
   
   # Redeploy previous version
   cd deployment/<agent-name>
   ./deploy.sh
   ```

4. **Verify Rollback**
   ```bash
   # Check agent status
   agentcore describe --agent-name <agent-name>
   
   # Test with sample payload
   agentcore invoke --agent-name <agent-name> --payload '{...}'
   ```

## Success Criteria

Deployment is successful when:

- [ ] All 5 agents deployed and showing `ACTIVE` status
- [ ] End-to-end test completes successfully
- [ ] Processing time ≤90 seconds per trade confirmation
- [ ] No errors in agent logs
- [ ] Memory integration working correctly
- [ ] Event flow validated across all queues
- [ ] Observability metrics visible
- [ ] Security controls validated

## Next Steps After Deployment

1. **Deploy Web Portal**: Deploy React frontend for monitoring and HITL
2. **Configure Monitoring**: Set up CloudWatch dashboards and alarms
3. **Run Load Tests**: Test with 100 concurrent requests
4. **Enable Production Traffic**: Gradually shift traffic from old system
5. **Monitor Performance**: Track SLAs and error rates
6. **Document Lessons Learned**: Update runbooks and procedures

## Support Contacts

- **AWS Support**: For AgentCore-specific issues
- **DevOps Team**: For infrastructure and deployment issues
- **Development Team**: For agent code and logic issues
- **Security Team**: For authentication and authorization issues

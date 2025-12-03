# PDF Adapter Agent - Invocation Guide

## Current State

### ✅ What's Deployed
- AWS Infrastructure (S3, DynamoDB, SQS, IAM, CloudWatch, Cognito)
- All supporting services in `us-east-1`

### ❌ What's NOT Deployed Yet
- **PDF Adapter Agent to AgentCore Runtime** (Task 14.2)
- Agent currently runs **locally only**

## How to Invoke the Agent

### Method 1: Direct Python Invocation (Simplest)

Process a PDF directly without SQS:

```bash
# Process a local PDF
python invoke_pdf_adapter.py data/COUNTERPARTY/GCS381315_V1.pdf --source-type COUNTERPARTY

# Process a PDF already in S3
python invoke_pdf_adapter.py s3://trade-matching-system-agentcore-production/BANK/trade_001.pdf --source-type BANK
```

**Pros:**
- ✅ Immediate processing
- ✅ Direct feedback
- ✅ Good for testing

**Cons:**
- ❌ Not event-driven
- ❌ Doesn't use SQS queues
- ❌ Not how it will work in production

---

### Method 2: Via SQS Queue (Event-Driven)

#### Step 1: Send event to SQS

```bash
# Send a document upload event
python invoke_via_sqs.py data/COUNTERPARTY/GCS381315_V1.pdf --source-type COUNTERPARTY
```

This will:
1. Upload the PDF to S3
2. Send a `DOCUMENT_UPLOADED` event to the `document-upload-events` queue
3. Return event details

#### Step 2: Run the agent listener

In a separate terminal:

```bash
# Start the agent listener
python run_pdf_adapter_listener.py
```

This will:
1. Poll the `document-upload-events` queue
2. Process documents as they arrive
3. Publish `PDF_PROCESSED` events to `extraction-events` queue
4. Run continuously until you press Ctrl+C

**Pros:**
- ✅ Event-driven (production-like)
- ✅ Uses SQS queues
- ✅ Publishes events for downstream agents
- ✅ Can process multiple documents

**Cons:**
- ❌ Requires running listener separately
- ❌ Still running locally (not in AgentCore)

---

### Method 3: Deploy to AgentCore Runtime (Production)

**Status:** ⏭️ Not implemented yet (Task 14.2)

To deploy to AgentCore Runtime, you'll need to:

1. **Prepare the agent package:**
   ```bash
   # Create requirements.txt
   cat > requirements.txt << EOF
   bedrock-agentcore>=1.0.0
   strands-agents>=1.0.0
   boto3>=1.40.0
   pydantic>=2.11.0
   pdf2image>=1.17.0
   Pillow>=11.3.0
   EOF
   ```

2. **Configure AgentCore:**
   ```bash
   agentcore configure \
     --agent-name pdf-adapter-agent \
     --runtime PYTHON_3_11 \
     --region us-east-1 \
     --memory-integration trade-matching-system-processing-history-production
   ```

3. **Launch the agent:**
   ```bash
   agentcore launch \
     --agent-name pdf-adapter-agent \
     --entry-point src/latest_trade_matching_agent/agents/pdf_adapter_agent.py:PDFAdapterAgent
   ```

4. **Invoke via AgentCore:**
   ```bash
   agentcore invoke \
     --agent-name pdf-adapter-agent \
     --payload '{"document_id": "test_001", "document_path": "s3://...", "source_type": "COUNTERPARTY"}'
   ```

**Pros:**
- ✅ Serverless (auto-scaling)
- ✅ Managed by AWS
- ✅ Production-ready
- ✅ Integrated with AgentCore Memory, Gateway, Observability

**Cons:**
- ❌ Not implemented yet
- ❌ Requires AgentCore CLI setup

---

## Quick Start Examples

### Example 1: Process a Single PDF (Quick Test)

```bash
# Direct invocation - fastest way to test
python invoke_pdf_adapter.py data/COUNTERPARTY/GCS381315_V1.pdf
```

### Example 2: Event-Driven Processing (Production-Like)

Terminal 1 - Start listener:
```bash
python run_pdf_adapter_listener.py
```

Terminal 2 - Send documents:
```bash
# Send first document
python invoke_via_sqs.py data/COUNTERPARTY/GCS381315_V1.pdf --source-type COUNTERPARTY

# Send second document
python invoke_via_sqs.py data/BANK/FAB_26933659.pdf --source-type BANK
```

Watch Terminal 1 for processing logs!

### Example 3: Batch Processing

```bash
# Process all PDFs in a directory
for pdf in data/COUNTERPARTY/*.pdf; do
    python invoke_via_sqs.py "$pdf" --source-type COUNTERPARTY
    sleep 2  # Avoid rate limiting
done
```

---

## Checking Results

### 1. Check S3 for Canonical Output

```bash
# List canonical outputs
aws s3 ls s3://trade-matching-system-agentcore-production/extracted/COUNTERPARTY/ --recursive

# Download a canonical output
aws s3 cp s3://trade-matching-system-agentcore-production/extracted/COUNTERPARTY/doc_1234567890.json ./output.json

# View the output
cat output.json | jq .
```

### 2. Check SQS for Events

```bash
# Check extraction-events queue for PDF_PROCESSED events
aws sqs receive-message \
  --queue-url https://sqs.us-east-1.amazonaws.com/401552979575/trade-matching-system-extraction-events-production \
  --max-number-of-messages 10 \
  --wait-time-seconds 5
```

### 3. Check DynamoDB for Agent Registry

```bash
# Check agent registration
aws dynamodb scan \
  --table-name trade-matching-system-agent-registry-production \
  --region us-east-1
```

### 4. Check CloudWatch Logs

```bash
# View agent logs (when deployed to AgentCore)
aws logs tail /aws/agentcore/pdf-adapter-agent --follow
```

---

## Troubleshooting

### Issue: "Queue does not exist"

**Solution:** Make sure infrastructure is deployed:
```bash
terraform -chdir=terraform/agentcore output | grep queue_url
```

### Issue: "Access Denied" to S3/DynamoDB

**Solution:** Check AWS credentials:
```bash
aws sts get-caller-identity
aws s3 ls s3://trade-matching-system-agentcore-production
```

### Issue: Agent processing is slow

**Expected:** OCR takes ~15 seconds per page with Bedrock Claude Sonnet 4
- 3-page PDF: ~50 seconds
- 5-page PDF: ~80 seconds

### Issue: No messages in queue

**Solution:** Check if messages were sent:
```bash
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/401552979575/trade-matching-system-document-upload-events-production.fifo \
  --attribute-names ApproximateNumberOfMessages
```

---

## Next Steps

### Immediate
1. ✅ Test with Method 1 (direct invocation)
2. ✅ Test with Method 2 (event-driven)
3. ⏭️ Deploy to AgentCore Runtime (Task 14.2)

### Short Term
1. Implement Trade Data Extraction Agent (Task 6)
2. Set up agent-to-agent communication via SQS
3. Test complete workflow: PDF → Extraction → Matching

### Production
1. Deploy all agents to AgentCore Runtime
2. Set up monitoring and alerting
3. Configure auto-scaling policies
4. Implement HITL workflows

---

## Cost Considerations

### Per Document Processing
- **S3 Storage**: ~$0.001 per document
- **S3 Requests**: ~$0.001 per document
- **SQS Messages**: ~$0.0001 per document
- **DynamoDB**: ~$0.001 per document
- **Bedrock OCR**: ~$0.05 per page (~$0.15 for 3-page PDF)
- **Total**: ~$0.15-0.20 per 3-page document

### Monthly Costs (100 documents/day)
- **Processing**: ~$450-600/month (3,000 documents)
- **Infrastructure**: ~$50-100/month
- **Total**: ~$500-700/month

---

## Support

For issues or questions:
1. Check `E2E_TEST_RESULTS.md` for test results
2. Check CloudWatch logs for errors
3. Review agent code in `src/latest_trade_matching_agent/agents/pdf_adapter_agent.py`
4. Check SQS dead letter queues for failed messages

---

**Last Updated**: November 26, 2024  
**Agent Version**: 1.0.0 (Local)  
**Infrastructure**: Deployed to us-east-1

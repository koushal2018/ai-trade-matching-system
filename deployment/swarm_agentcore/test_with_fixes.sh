#!/bin/bash
# Quick test script with all fixes applied

echo "========================================="
echo "Testing Status Tracking with Fixes"
echo "========================================="

# Set environment variables
export AWS_REGION=us-east-1
export S3_BUCKET_NAME=trade-matching-system-agentcore-production
export STATUS_TABLE_NAME=trade-matching-system-processing-status

# Agent ARNs
export PDF_ADAPTER_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/pdf_adapter_agent-Az72YP53FJ
export TRADE_EXTRACTION_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/agent_matching_ai-KrY5QeCyXe
export TRADE_MATCHING_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/trade_matching_ai-r8eaGb4u7B
export EXCEPTION_MANAGEMENT_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/exception_manager-uliBS5DsX3

echo ""
echo "Environment configured:"
echo "  Region: $AWS_REGION"
echo "  Status Table: $STATUS_TABLE_NAME"
echo ""

# Test with document that exists
echo "Running orchestrator test with FAB_27254314 (document that exists)..."
python test_local_orchestrator.py FAB_27254314 BANK

echo ""
echo "========================================="
echo "Test Complete!"
echo "========================================="

# Extract session_id from the output (it should be in the result)
echo ""
echo "Verifying status in DynamoDB..."
echo ""

# Get the most recent status entry
RECENT_SESSION=$(aws dynamodb scan \
  --table-name trade-matching-system-processing-status \
  --region us-east-1 \
  --limit 1 \
  --query 'Items[0].processing_id.S' \
  --output text 2>/dev/null)

if [ -n "$RECENT_SESSION" ] && [ "$RECENT_SESSION" != "None" ]; then
  echo "Found recent session: $RECENT_SESSION"
  echo ""
  echo "Status details:"
  aws dynamodb get-item \
    --table-name trade-matching-system-processing-status \
    --key "{\"processing_id\": {\"S\": \"$RECENT_SESSION\"}}" \
    --region us-east-1 \
    --output json | jq '{
      processing_id: .Item.processing_id.S,
      overallStatus: .Item.overallStatus.S,
      pdfAdapter: .Item.pdfAdapter.M.status.S,
      tradeExtraction: .Item.tradeExtraction.M.status.S,
      tradeMatching: .Item.tradeMatching.M.status.S,
      lastUpdated: .Item.lastUpdated.S
    }'
  
  echo ""
  echo "✅ Status tracking verification complete!"
else
  echo "⚠️  No status found in DynamoDB - status writes may have failed"
  echo "Check the logs above for status_tracker warnings"
fi

echo ""
echo "========================================="

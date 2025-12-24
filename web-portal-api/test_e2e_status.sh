#!/bin/bash

echo "=========================================="
echo "End-to-End Status Tracking Test"
echo "=========================================="
echo ""

# Step 1: Upload a file
echo "1. Uploading test PDF..."
UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:8000/api/upload \
  -F "file=@../deployment/swarm_agentcore/test.pdf" \
  -F "sourceType=BANK" 2>/dev/null || echo '{"sessionId":"manual-test"}')

SESSION_ID=$(echo $UPLOAD_RESPONSE | jq -r '.sessionId // "manual-test"')
echo "   Session ID: $SESSION_ID"
echo ""

# Step 2: Check initial status (should be pending)
echo "2. Checking initial status (should be pending)..."
curl -s "http://localhost:8000/api/workflow/${SESSION_ID}/status" | jq -r '.overallStatus'
echo ""

# Step 3: Manually trigger orchestrator (simulating Lambda trigger)
echo "3. Triggering orchestrator..."
echo "   Note: In production, Lambda automatically triggers on S3 upload"
echo "   For testing, you can manually invoke the deployed orchestrator:"
echo ""
echo "   aws bedrock-agentcore invoke-runtime \\"
echo "     --runtime-arn arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/trade_matching_swarm_agentcore_http-XXXXX \\"
echo "     --payload '{\"document_path\": \"BANK/test.pdf\", \"source_type\": \"BANK\", \"correlation_id\": \"${SESSION_ID}\"}' \\"
echo "     --region us-east-1"
echo ""

# Step 4: Poll for status updates
echo "4. Polling for status updates (Ctrl+C to stop)..."
echo ""

COUNT=0
while [ $COUNT -lt 20 ]; do
  STATUS=$(curl -s "http://localhost:8000/api/workflow/${SESSION_ID}/status" | jq -r '.overallStatus')
  PDF_STATUS=$(curl -s "http://localhost:8000/api/workflow/${SESSION_ID}/status" | jq -r '.agents.pdfAdapter.status')
  
  echo "   Poll #$((COUNT+1)): Overall=$STATUS, PDF Adapter=$PDF_STATUS"
  
  if [ "$STATUS" == "completed" ] || [ "$STATUS" == "failed" ]; then
    echo ""
    echo "✅ Workflow completed!"
    echo ""
    echo "Final status:"
    curl -s "http://localhost:8000/api/workflow/${SESSION_ID}/status" | jq '.'
    break
  fi
  
  COUNT=$((COUNT+1))
  sleep 5
done

if [ $COUNT -eq 20 ]; then
  echo ""
  echo "⏱️  Polling timeout (workflow still processing or not started)"
  echo "   Check if orchestrator was triggered"
fi

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="

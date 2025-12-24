#!/bin/bash

# Test with the actual session from the logs
SESSION_ID="session-2664b772-30ba-41b2-adc6-3cafa6da3ab7"

echo "Testing status endpoint with real session: $SESSION_ID"
echo ""

# Test the status endpoint
echo "Calling: GET /api/workflow/${SESSION_ID}/status"
curl -s "http://localhost:8000/api/workflow/${SESSION_ID}/status" | jq '.'

echo ""
echo "---"
echo ""

# Also check what's actually in DynamoDB for this session
echo "Checking DynamoDB for this session..."
aws dynamodb get-item \
  --table-name trade-matching-system-processing-status \
  --key "{\"processing_id\": {\"S\": \"${SESSION_ID}\"}}" \
  --region us-east-1 \
  --output json | jq '.Item // "Not found in DynamoDB"'

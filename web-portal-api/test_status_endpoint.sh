#!/bin/bash

# Test script for workflow status endpoint

echo "=========================================="
echo "Testing Workflow Status Endpoint"
echo "=========================================="
echo ""

# Check if backend is running
echo "1. Checking if backend is running..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is running"
else
    echo "❌ Backend is not running"
    echo "Start it with: uvicorn app.main:app --reload --port 8000"
    exit 1
fi
echo ""

# Test with non-existent session (should return pending)
echo "2. Testing with non-existent session (should return pending)..."
curl -s http://localhost:8000/api/workflow/test-nonexistent-session/status | jq -r '.overallStatus'
echo ""

# Test with a real session from DynamoDB
echo "3. Getting a real session from DynamoDB..."
REAL_SESSION=$(aws dynamodb scan \
  --table-name trade-matching-system-processing-status \
  --limit 1 \
  --region us-east-1 \
  --query 'Items[0].processing_id.S' \
  --output text 2>/dev/null)

if [ -n "$REAL_SESSION" ] && [ "$REAL_SESSION" != "None" ]; then
    echo "Found session: $REAL_SESSION"
    echo ""
    echo "4. Testing with real session..."
    curl -s "http://localhost:8000/api/workflow/${REAL_SESSION}/status" | jq '.'
else
    echo "No sessions found in DynamoDB yet"
    echo "Upload a PDF to create a session first"
fi

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="

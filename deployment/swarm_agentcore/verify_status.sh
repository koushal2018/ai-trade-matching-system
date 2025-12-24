#!/bin/bash
# Verify status tracking in DynamoDB

echo "========================================="
echo "Status Tracking Verification"
echo "========================================="

TABLE_NAME="trade-matching-system-processing-status"
REGION="us-east-1"

# Check if session_id was provided
if [ -n "$1" ]; then
  SESSION_ID="$1"
  echo "Querying specific session: $SESSION_ID"
  echo ""
  
  aws dynamodb get-item \
    --table-name "$TABLE_NAME" \
    --key "{\"processing_id\": {\"S\": \"$SESSION_ID\"}}" \
    --region "$REGION" \
    --output json | jq '{
      processing_id: .Item.processing_id.S,
      sessionId: .Item.sessionId.S,
      correlationId: .Item.correlationId.S,
      documentId: .Item.documentId.S,
      sourceType: .Item.sourceType.S,
      overallStatus: .Item.overallStatus.S,
      agents: {
        pdfAdapter: {
          status: .Item.pdfAdapter.M.status.S,
          activity: .Item.pdfAdapter.M.activity.S,
          tokenUsage: .Item.pdfAdapter.M.tokenUsage.M
        },
        tradeExtraction: {
          status: .Item.tradeExtraction.M.status.S,
          activity: .Item.tradeExtraction.M.activity.S,
          tokenUsage: .Item.tradeExtraction.M.tokenUsage.M
        },
        tradeMatching: {
          status: .Item.tradeMatching.M.status.S,
          activity: .Item.tradeMatching.M.activity.S,
          tokenUsage: .Item.tradeMatching.M.tokenUsage.M
        }
      },
      timestamps: {
        createdAt: .Item.createdAt.S,
        lastUpdated: .Item.lastUpdated.S
      }
    }'
else
  echo "Showing recent status entries..."
  echo ""
  
  # Get the 5 most recent entries
  aws dynamodb scan \
    --table-name "$TABLE_NAME" \
    --region "$REGION" \
    --limit 5 \
    --output json | jq '.Items[] | {
      processing_id: .processing_id.S,
      documentId: .documentId.S,
      overallStatus: .overallStatus.S,
      pdfAdapter: .pdfAdapter.M.status.S,
      tradeExtraction: .tradeExtraction.M.status.S,
      tradeMatching: .tradeMatching.M.status.S,
      lastUpdated: .lastUpdated.S
    }'
  
  echo ""
  echo "To see details for a specific session, run:"
  echo "  ./verify_status.sh <session-id>"
fi

echo ""
echo "========================================="

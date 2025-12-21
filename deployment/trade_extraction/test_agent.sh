#!/bin/bash
# Test script for Trade Extraction Agent using real counterparty file

# Test payload with counterparty file from S3
TEST_PAYLOAD='{
  "document_id": "GCS381315V1",
  "canonical_output_location": "s3://trade-matching-system-agentcore-production/extracted/COUNTERPARTY/GCS381315V1.json",
  "source_type": "COUNTERPARTY",
  "correlation_id": "corr_test_counterparty_001"
}'

echo "Testing Trade Extraction Agent with counterparty file..."
echo "File: s3://trade-matching-system-agentcore-production/COUNTERPARTY/GCS381315V1.pdf"
echo "Payload: $TEST_PAYLOAD"
echo ""

agentcore invoke --dev "$TEST_PAYLOAD"
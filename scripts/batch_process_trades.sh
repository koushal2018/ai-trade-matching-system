#!/bin/bash
# Batch Process All Trade Confirmations from S3
# Dynamically discovers and processes all PDFs in BANK and COUNTERPARTY folders

set -e

S3_BUCKET="trade-matching-system-agentcore-production"
REGION="us-east-1"

echo "=============================================="
echo "Batch Trade Processing - Real World Simulation"
echo "=============================================="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# Function to process a single PDF
process_pdf() {
    local source_type=$1
    local filename=$2
    local doc_id=$3

    echo ""
    echo "======================================================"
    echo "Processing: $source_type / $filename"
    echo "Document ID: $doc_id"
    echo "======================================================"

    # Step 1: PDF Adapter
    echo ""
    echo "[Step 1] PDF Adapter - Extracting text from PDF..."
    cd /Users/koushald/ai-trade-matching-system-2/deployment/pdf_adapter

    agentcore invoke --agent pdf_adapter_agent "{\"document_id\": \"$doc_id\", \"document_path\": \"s3://$S3_BUCKET/$source_type/$filename\", \"source_type\": \"$source_type\"}"

    echo ""
    echo "[Step 2] Trade Extraction - Extracting trade data..."
    cd /Users/koushald/ai-trade-matching-system-2/deployment/trade_extraction

    EXTRACTION_RESULT=$(agentcore invoke --agent trade_extraction_agent "{\"document_id\": \"$doc_id\", \"canonical_output_location\": \"s3://$S3_BUCKET/extracted/$source_type/$doc_id.json\", \"source_type\": \"$source_type\"}")

    echo "$EXTRACTION_RESULT"

    # Extract trade_id from result
    TRADE_ID=$(echo "$EXTRACTION_RESULT" | grep -o '"trade_id": "[^"]*"' | head -1 | cut -d'"' -f4)

    if [ -n "$TRADE_ID" ]; then
        echo ""
        echo "[Step 3] Trade Matching - Attempting to match trade: $TRADE_ID (source: $source_type)"
        cd /Users/koushald/ai-trade-matching-system-2/deployment/trade_matching

        agentcore invoke --agent trade_matching_agent "{\"trade_id\": \"$TRADE_ID\", \"source_type\": \"$source_type\", \"correlation_id\": \"batch_$(date +%s)\"}"
    else
        echo "Could not extract trade_id from extraction result"
    fi

    echo ""
    echo "Completed processing: $filename"
    echo "------------------------------------------------------"
}

# Process COUNTERPARTY trades first (they often arrive first in real world)
echo ""
echo "=========================================="
echo "PHASE 1: Processing COUNTERPARTY trades"
echo "=========================================="

# Get all PDFs from COUNTERPARTY folder
COUNTERPARTY_PDFS=$(aws s3 ls s3://$S3_BUCKET/COUNTERPARTY/ --region $REGION | grep "\.pdf$" | awk '{print $4}')

for pdf in $COUNTERPARTY_PDFS; do
    # Extract document ID from filename (remove .pdf extension)
    doc_id=$(basename "$pdf" .pdf)
    process_pdf "COUNTERPARTY" "$pdf" "$doc_id"
    sleep 2
done

# Process BANK trades (they arrive later from internal systems)
echo ""
echo "=========================================="
echo "PHASE 2: Processing BANK trades"
echo "=========================================="

# Get all PDFs from BANK folder
BANK_PDFS=$(aws s3 ls s3://$S3_BUCKET/BANK/ --region $REGION | grep "\.pdf$" | awk '{print $4}')

for pdf in $BANK_PDFS; do
    # Extract document ID from filename (remove .pdf extension)
    doc_id=$(basename "$pdf" .pdf)
    process_pdf "BANK" "$pdf" "$doc_id"
    sleep 2
done

echo ""
echo "=============================================="
echo "Batch Processing Complete!"
echo "=============================================="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""
echo "Check DynamoDB tables for stored trades:"
echo "  aws dynamodb scan --table-name BankTradeData --region $REGION"
echo "  aws dynamodb scan --table-name CounterpartyTradeData --region $REGION"
echo ""
echo "Check S3 for matching reports:"
echo "  aws s3 ls s3://$S3_BUCKET/reports/ --region $REGION"

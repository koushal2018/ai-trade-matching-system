#!/bin/bash

# Create a test PDF file
echo "This is a test PDF file content." > test.pdf

# Step 1: Get a pre-signed URL
echo "Getting pre-signed URL..."
RESPONSE=$(curl -s -X POST https://mdj9ch24qg.execute-api.us-east-1.amazonaws.com/dev/documents \
  -H "Content-Type: application/json" \
  -d '{"fileName": "test.pdf", "source": "BANK"}')

echo "Response: $RESPONSE"

# Extract the upload URL using a more reliable method
UPLOAD_URL=$(echo $RESPONSE | sed -n 's/.*"uploadUrl": *"\([^"]*\)".*/\1/p')
KEY=$(echo $RESPONSE | sed -n 's/.*"key": *"\([^"]*\)".*/\1/p')

echo "Upload URL: $UPLOAD_URL"
echo "Key: $KEY"

if [ -z "$UPLOAD_URL" ]; then
  echo "Failed to get upload URL"
  exit 1
fi

# Step 2: Upload the file to S3
echo "Uploading file to S3..."
UPLOAD_RESPONSE=$(curl -v -X PUT "$UPLOAD_URL" \
  -H "Content-Type: application/pdf" \
  --data-binary @test.pdf)

echo "Upload response: $UPLOAD_RESPONSE"

# Clean up
rm test.pdf

echo "Test completed"
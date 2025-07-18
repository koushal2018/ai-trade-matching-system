#!/bin/bash

# Get the API ID from the API Gateway URL
API_ID="mdj9ch24qg"
STAGE_NAME="dev"

# Enable CORS for the entire API
aws apigateway update-rest-api \
  --rest-api-id $API_ID \
  --patch-operations \
  op=replace,path=/corsConfiguration,value='{
    "allowOrigins": ["*"],
    "allowMethods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allowHeaders": ["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key", "X-Amz-Security-Token"],
    "allowCredentials": false,
    "exposeHeaders": []
  }'

# Deploy the API to apply changes
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name $STAGE_NAME \
  --description "Enabling CORS"

echo "CORS configuration updated and deployed to $STAGE_NAME stage"
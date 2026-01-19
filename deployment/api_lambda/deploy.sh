#!/bin/bash
# Deploy Trade Matching API to AWS Lambda + API Gateway

set -e

REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
FUNCTION_NAME="trade-matching-api"
API_NAME="trade-matching-api"
ROLE_NAME="trade-matching-api-role"

echo "========================================"
echo "Deploying Trade Matching API"
echo "========================================"
echo "Region: $REGION"
echo "Account: $ACCOUNT_ID"
echo ""

# Create IAM role for Lambda if it doesn't exist
echo "Creating IAM role..."
ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text 2>/dev/null || true)

if [ -z "$ROLE_ARN" ] || [ "$ROLE_ARN" == "None" ]; then
    echo "Creating new IAM role: $ROLE_NAME"

    cat > /tmp/trust-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

    ROLE_ARN=$(aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document file:///tmp/trust-policy.json \
        --query 'Role.Arn' \
        --output text)

    # Attach basic execution policy
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

    echo "Waiting for role to propagate..."
    sleep 10
fi

echo "Role ARN: $ROLE_ARN"

# Package Lambda function
echo ""
echo "Packaging Lambda function..."
cd "$(dirname "$0")"
zip -j /tmp/lambda_function.zip lambda_handler.py

# Create or update Lambda function
echo ""
echo "Deploying Lambda function..."
FUNCTION_EXISTS=$(aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>/dev/null || echo "NOT_FOUND")

if [ "$FUNCTION_EXISTS" == "NOT_FOUND" ]; then
    echo "Creating new Lambda function: $FUNCTION_NAME"

    FUNCTION_ARN=$(aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.11 \
        --role $ROLE_ARN \
        --handler lambda_handler.handler \
        --zip-file fileb:///tmp/lambda_function.zip \
        --timeout 30 \
        --memory-size 256 \
        --region $REGION \
        --query 'FunctionArn' \
        --output text)
else
    echo "Updating existing Lambda function: $FUNCTION_NAME"

    FUNCTION_ARN=$(aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb:///tmp/lambda_function.zip \
        --region $REGION \
        --query 'FunctionArn' \
        --output text)
fi

echo "Lambda ARN: $FUNCTION_ARN"

# Wait for function to be ready
echo "Waiting for Lambda function to be active..."
aws lambda wait function-active --function-name $FUNCTION_NAME --region $REGION

# Create or get API Gateway HTTP API
echo ""
echo "Setting up API Gateway..."
API_ID=$(aws apigatewayv2 get-apis --region $REGION \
    --query "Items[?Name=='$API_NAME'].ApiId | [0]" \
    --output text 2>/dev/null || echo "None")

if [ "$API_ID" == "None" ] || [ -z "$API_ID" ]; then
    echo "Creating new API Gateway: $API_NAME"

    API_ID=$(aws apigatewayv2 create-api \
        --name $API_NAME \
        --protocol-type HTTP \
        --cors-configuration AllowOrigins="*",AllowMethods="*",AllowHeaders="*" \
        --region $REGION \
        --query 'ApiId' \
        --output text)
fi

echo "API ID: $API_ID"

# Create Lambda integration
echo "Creating Lambda integration..."
INTEGRATION_ID=$(aws apigatewayv2 get-integrations \
    --api-id $API_ID \
    --region $REGION \
    --query "Items[?IntegrationType=='AWS_PROXY'].IntegrationId | [0]" \
    --output text 2>/dev/null || echo "None")

if [ "$INTEGRATION_ID" == "None" ] || [ -z "$INTEGRATION_ID" ]; then
    INTEGRATION_ID=$(aws apigatewayv2 create-integration \
        --api-id $API_ID \
        --integration-type AWS_PROXY \
        --integration-uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$FUNCTION_ARN/invocations" \
        --payload-format-version "2.0" \
        --region $REGION \
        --query 'IntegrationId' \
        --output text)
fi

echo "Integration ID: $INTEGRATION_ID"

# Create catch-all route
echo "Creating routes..."
ROUTE_EXISTS=$(aws apigatewayv2 get-routes \
    --api-id $API_ID \
    --region $REGION \
    --query "Items[?RouteKey=='\$default'].RouteId | [0]" \
    --output text 2>/dev/null || echo "None")

if [ "$ROUTE_EXISTS" == "None" ] || [ -z "$ROUTE_EXISTS" ]; then
    aws apigatewayv2 create-route \
        --api-id $API_ID \
        --route-key '$default' \
        --target "integrations/$INTEGRATION_ID" \
        --region $REGION
fi

# Also create explicit routes for /api paths
for ROUTE in "GET /api/{proxy+}" "POST /api/{proxy+}" "OPTIONS /api/{proxy+}"; do
    METHOD=$(echo $ROUTE | cut -d' ' -f1)
    PATH=$(echo $ROUTE | cut -d' ' -f2)
    ROUTE_KEY="$METHOD $PATH"

    ROUTE_EXISTS=$(aws apigatewayv2 get-routes \
        --api-id $API_ID \
        --region $REGION \
        --query "Items[?RouteKey=='$ROUTE_KEY'].RouteId | [0]" \
        --output text 2>/dev/null || echo "None")

    if [ "$ROUTE_EXISTS" == "None" ] || [ -z "$ROUTE_EXISTS" ]; then
        aws apigatewayv2 create-route \
            --api-id $API_ID \
            --route-key "$ROUTE_KEY" \
            --target "integrations/$INTEGRATION_ID" \
            --region $REGION 2>/dev/null || true
    fi
done

# Create or update stage
echo "Creating/updating stage..."
STAGE_EXISTS=$(aws apigatewayv2 get-stages \
    --api-id $API_ID \
    --region $REGION \
    --query "Items[?StageName=='\$default'].StageName | [0]" \
    --output text 2>/dev/null || echo "None")

if [ "$STAGE_EXISTS" == "None" ] || [ -z "$STAGE_EXISTS" ]; then
    aws apigatewayv2 create-stage \
        --api-id $API_ID \
        --stage-name '$default' \
        --auto-deploy \
        --region $REGION
fi

# Add Lambda permission for API Gateway
echo "Adding Lambda permission for API Gateway..."
aws lambda add-permission \
    --function-name $FUNCTION_NAME \
    --statement-id "apigateway-invoke-$(date +%s)" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*" \
    --region $REGION 2>/dev/null || true

# Get API endpoint
API_ENDPOINT=$(aws apigatewayv2 get-api \
    --api-id $API_ID \
    --region $REGION \
    --query 'ApiEndpoint' \
    --output text)

echo ""
echo "========================================"
echo "Deployment Complete!"
echo "========================================"
echo ""
echo "API Endpoint: $API_ENDPOINT"
echo ""
echo "Test endpoints:"
echo "  Health:        $API_ENDPOINT/api/health"
echo "  Agent Status:  $API_ENDPOINT/api/agents/status"
echo "  Metrics:       $API_ENDPOINT/api/metrics/processing"
echo "  Results:       $API_ENDPOINT/api/matching/results"
echo "  HITL Reviews:  $API_ENDPOINT/api/hitl/reviews"
echo ""
echo "To test:"
echo "  curl $API_ENDPOINT/api/health"
echo ""
echo "Update frontend .env.production with:"
echo "  VITE_API_URL=$API_ENDPOINT"
echo "  VITE_ENABLE_MSW=false"
echo ""

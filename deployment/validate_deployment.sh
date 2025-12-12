#!/bin/bash
# Validation script to verify all agents are deployed correctly

set -e

echo "========================================="
echo "AgentCore Deployment Validation"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Agents to validate
AGENTS=(
    "orchestrator-agent"
    "pdf-adapter-agent"
    "trade-extraction-agent"
    "trade-matching-agent"
    "exception-management-agent"
)

REGION="us-east-1"
FAILED_CHECKS=0
PASSED_CHECKS=0

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        ((PASSED_CHECKS++))
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        ((FAILED_CHECKS++))
    fi
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠ WARN${NC}: $1"
}

echo "1. Checking Prerequisites..."
echo "----------------------------"

# Check AWS CLI
if command -v aws &> /dev/null; then
    print_status 0 "AWS CLI installed"
else
    print_status 1 "AWS CLI not found"
fi

# Check AgentCore CLI
if command -v agentcore &> /dev/null; then
    print_status 0 "AgentCore CLI installed"
else
    print_status 1 "AgentCore CLI not found"
fi

# Check AWS credentials
if aws sts get-caller-identity &> /dev/null; then
    print_status 0 "AWS credentials configured"
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    echo "   Account ID: ${ACCOUNT_ID}"
else
    print_status 1 "AWS credentials not configured"
fi

echo ""
echo "2. Validating Agent Deployments..."
echo "-----------------------------------"

for agent in "${AGENTS[@]}"; do
    echo ""
    echo "Checking ${agent}..."
    
    # Check if agent exists
    if agentcore describe --agent-name "${agent}" --region "${REGION}" &> /dev/null; then
        print_status 0 "${agent} exists"
        
        # Get agent status
        STATUS=$(agentcore describe --agent-name "${agent}" --region "${REGION}" --query 'status' --output text 2>/dev/null || echo "UNKNOWN")
        
        if [ "${STATUS}" == "ACTIVE" ]; then
            print_status 0 "${agent} status is ACTIVE"
        else
            print_status 1 "${agent} status is ${STATUS} (expected ACTIVE)"
        fi
        
        # Check last deployment time
        LAST_UPDATED=$(agentcore describe --agent-name "${agent}" --region "${REGION}" --query 'lastUpdated' --output text 2>/dev/null || echo "UNKNOWN")
        echo "   Last updated: ${LAST_UPDATED}"
        
    else
        print_status 1 "${agent} not found"
    fi
done

echo ""
echo "3. Validating Infrastructure..."
echo "--------------------------------"

# Check S3 bucket
BUCKET_NAME="trade-matching-bucket"
if aws s3 ls "s3://${BUCKET_NAME}" --region "${REGION}" &> /dev/null; then
    print_status 0 "S3 bucket ${BUCKET_NAME} exists"
else
    print_status 1 "S3 bucket ${BUCKET_NAME} not found"
fi

# Check DynamoDB tables
TABLES=(
    "BankTradeData"
    "CounterpartyTradeData"
    "ExceptionsTable"
    "AgentRegistry"
)

for table in "${TABLES[@]}"; do
    if aws dynamodb describe-table --table-name "${table}" --region "${REGION}" &> /dev/null; then
        print_status 0 "DynamoDB table ${table} exists"
    else
        print_status 1 "DynamoDB table ${table} not found"
    fi
done

# Check SQS queues
QUEUES=(
    "document-upload-events.fifo"
    "extraction-events"
    "matching-events"
    "exception-events"
    "hitl-review-queue.fifo"
    "orchestrator-monitoring-queue"
)

for queue in "${QUEUES[@]}"; do
    QUEUE_URL=$(aws sqs get-queue-url --queue-name "${queue}" --region "${REGION}" --query 'QueueUrl' --output text 2>/dev/null || echo "")
    
    if [ -n "${QUEUE_URL}" ]; then
        print_status 0 "SQS queue ${queue} exists"
    else
        print_status 1 "SQS queue ${queue} not found"
    fi
done

echo ""
echo "4. Testing Agent Invocations..."
echo "--------------------------------"

# Test Orchestrator Agent
echo ""
echo "Testing orchestrator-agent..."
ORCHESTRATOR_RESULT=$(agentcore invoke \
    --agent-name "orchestrator-agent" \
    --region "${REGION}" \
    --payload '{"event_type":"AGENT_STATUS","agent_id":"test","status":"ACTIVE"}' \
    2>&1 || echo "FAILED")

if [[ "${ORCHESTRATOR_RESULT}" != *"FAILED"* ]]; then
    print_status 0 "Orchestrator agent invocation successful"
else
    print_status 1 "Orchestrator agent invocation failed"
    echo "   Error: ${ORCHESTRATOR_RESULT}"
fi

# Test PDF Adapter Agent (if test PDF exists)
echo ""
echo "Testing pdf-adapter-agent..."
print_warning "Skipping PDF adapter test (requires test PDF in S3)"

# Test Trade Extraction Agent
echo ""
echo "Testing trade-extraction-agent..."
print_warning "Skipping trade extraction test (requires canonical output in S3)"

# Test Trade Matching Agent
echo ""
echo "Testing trade-matching-agent..."
print_warning "Skipping trade matching test (requires trades in DynamoDB)"

# Test Exception Management Agent
echo ""
echo "Testing exception-management-agent..."
EXCEPTION_RESULT=$(agentcore invoke \
    --agent-name "exception-management-agent" \
    --region "${REGION}" \
    --payload '{"event_type":"MATCHING_EXCEPTION","trade_id":"TEST001","match_score":0.65,"reason_codes":["NOTIONAL_MISMATCH"]}' \
    2>&1 || echo "FAILED")

if [[ "${EXCEPTION_RESULT}" != *"FAILED"* ]]; then
    print_status 0 "Exception management agent invocation successful"
else
    print_status 1 "Exception management agent invocation failed"
    echo "   Error: ${EXCEPTION_RESULT}"
fi

echo ""
echo "5. Checking Agent Logs..."
echo "--------------------------"

for agent in "${AGENTS[@]}"; do
    echo ""
    echo "Recent logs for ${agent}:"
    agentcore logs --agent-name "${agent}" --region "${REGION}" --tail 5 2>/dev/null || echo "   No logs available"
done

echo ""
echo "========================================="
echo "Validation Summary"
echo "========================================="
echo -e "${GREEN}Passed checks: ${PASSED_CHECKS}${NC}"
echo -e "${RED}Failed checks: ${FAILED_CHECKS}${NC}"
echo ""

if [ ${FAILED_CHECKS} -eq 0 ]; then
    echo -e "${GREEN}✓ All validation checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Run end-to-end integration test with a sample PDF"
    echo "2. Monitor agent logs for any errors"
    echo "3. Set up CloudWatch dashboards for monitoring"
    echo "4. Configure alerting for SLA violations"
    exit 0
else
    echo -e "${RED}✗ Some validation checks failed.${NC}"
    echo ""
    echo "Please review the failed checks above and:"
    echo "1. Verify infrastructure is set up correctly"
    echo "2. Check agent deployment logs for errors"
    echo "3. Ensure all prerequisites are met"
    echo "4. Re-run deployment scripts if needed"
    exit 1
fi

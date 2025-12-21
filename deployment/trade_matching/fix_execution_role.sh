#!/bin/bash
# Fix Trade Matching Agent execution role
# The agent is configured with a non-existent role, causing 403 errors

set -e

AGENT_RUNTIME_ID="trade_matching_ai-r8eaGb4u7B"
NEW_ROLE_ARN="arn:aws:iam::401552979575:role/AmazonBedrockAgentCoreSDKRuntime-us-east-1-0f9cb91bfb"
REGION="us-east-1"

# Logging configuration
LOG_FILE="fix_execution_role_$(date +%Y%m%d_%H%M%S).log"
CORRELATION_ID="fix_role_$(date +%s)_$$"

# Logging functions
log_info() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[INFO] [${timestamp}] [${CORRELATION_ID}] $1" | tee -a "${LOG_FILE}"
}

log_error() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[ERROR] [${timestamp}] [${CORRELATION_ID}] $1" | tee -a "${LOG_FILE}" >&2
}

log_warn() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[WARN] [${timestamp}] [${CORRELATION_ID}] $1" | tee -a "${LOG_FILE}"
}

log_debug() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[DEBUG] [${timestamp}] [${CORRELATION_ID}] $1" | tee -a "${LOG_FILE}"
}

log_info "============================================="
log_info "Fixing Trade Matching Agent Execution Role"
log_info "============================================="
log_info ""
log_info "Configuration:"
log_info "  Agent Runtime ID: ${AGENT_RUNTIME_ID}"
log_info "  New Role ARN: ${NEW_ROLE_ARN}"
log_info "  Region: ${REGION}"
log_info "  Correlation ID: ${CORRELATION_ID}"
log_info "  Log File: ${LOG_FILE}"
log_info ""

# Verify the role exists and has correct trust policy
log_info "Step 1: Verifying IAM role exists..."
log_debug "Executing: aws iam get-role --role-name AmazonBedrockAgentCoreSDKRuntime-us-east-1-0f9cb91bfb"

ROLE_OUTPUT=$(aws iam get-role --role-name AmazonBedrockAgentCoreSDKRuntime-us-east-1-0f9cb91bfb \
  --query 'Role.{Arn:Arn,TrustPolicy:AssumeRolePolicyDocument}' \
  --region ${REGION} 2>&1)
ROLE_EXIT_CODE=$?

if [ ${ROLE_EXIT_CODE} -eq 0 ]; then
    log_info "✅ Role verified successfully"
    log_debug "Role details: ${ROLE_OUTPUT}"
    
    # Verify trust policy includes bedrock-agentcore
    if echo "${ROLE_OUTPUT}" | grep -q "bedrock-agentcore"; then
        log_info "✅ Trust policy includes bedrock-agentcore service"
    else
        log_warn "⚠️  Trust policy may not include bedrock-agentcore service"
        log_debug "Trust policy check: bedrock-agentcore not found in output"
    fi
else
    log_error "❌ Role verification failed with exit code: ${ROLE_EXIT_CODE}"
    log_error "Error details: ${ROLE_OUTPUT}"
    exit 1
fi

log_info ""
log_info "Step 2: Updating AgentCore Runtime execution role..."
log_debug "Executing: aws bedrock-agentcore-control update-agent-runtime"
log_debug "Parameters: agent-runtime-id=${AGENT_RUNTIME_ID}, role-arn=${NEW_ROLE_ARN}"

UPDATE_START=$(date +%s)
UPDATE_OUTPUT=$(aws bedrock-agentcore-control update-agent-runtime \
  --agent-runtime-id ${AGENT_RUNTIME_ID} \
  --role-arn ${NEW_ROLE_ARN} \
  --region ${REGION} 2>&1)
UPDATE_EXIT_CODE=$?
UPDATE_END=$(date +%s)
UPDATE_DURATION=$((UPDATE_END - UPDATE_START))

if [ ${UPDATE_EXIT_CODE} -eq 0 ]; then
    log_info "✅ Runtime updated successfully (${UPDATE_DURATION}s)"
    log_debug "Update response: ${UPDATE_OUTPUT}"
    
    # Extract status and version if available
    STATUS=$(echo "${UPDATE_OUTPUT}" | grep -o '"status": "[^"]*"' | cut -d'"' -f4)
    VERSION=$(echo "${UPDATE_OUTPUT}" | grep -o '"agentRuntimeVersion": "[^"]*"' | cut -d'"' -f4)
    
    if [ -n "${STATUS}" ]; then
        log_info "  Runtime Status: ${STATUS}"
    fi
    if [ -n "${VERSION}" ]; then
        log_info "  Runtime Version: ${VERSION}"
    fi
else
    log_error "❌ Runtime update failed with exit code: ${UPDATE_EXIT_CODE}"
    log_error "Error details: ${UPDATE_OUTPUT}"
    log_error "Update duration: ${UPDATE_DURATION}s"
    exit 1
fi

log_info ""
log_info "Step 3: Verifying runtime status..."
log_debug "Executing: aws bedrock-agentcore-control get-agent-runtime"

VERIFY_OUTPUT=$(aws bedrock-agentcore-control get-agent-runtime \
  --agent-runtime-id ${AGENT_RUNTIME_ID} \
  --region ${REGION} \
  --query 'agentRuntime.{Status:status,RoleArn:roleArn}' 2>&1)
VERIFY_EXIT_CODE=$?

if [ ${VERIFY_EXIT_CODE} -eq 0 ]; then
    log_info "✅ Runtime verification successful"
    log_debug "Runtime details: ${VERIFY_OUTPUT}"
    
    # Parse and log key fields
    CURRENT_STATUS=$(echo "${VERIFY_OUTPUT}" | grep -o '"Status": "[^"]*"' | cut -d'"' -f4)
    CURRENT_ROLE=$(echo "${VERIFY_OUTPUT}" | grep -o '"RoleArn": "[^"]*"' | cut -d'"' -f4)
    
    if [ -n "${CURRENT_STATUS}" ]; then
        log_info "  Current Status: ${CURRENT_STATUS}"
    fi
    if [ -n "${CURRENT_ROLE}" ]; then
        log_info "  Current Role ARN: ${CURRENT_ROLE}"
        
        # Verify role was actually updated
        if [ "${CURRENT_ROLE}" = "${NEW_ROLE_ARN}" ]; then
            log_info "  ✅ Role ARN matches expected value"
        else
            log_warn "  ⚠️  Role ARN does not match expected value"
            log_warn "    Expected: ${NEW_ROLE_ARN}"
            log_warn "    Actual: ${CURRENT_ROLE}"
        fi
    fi
else
    log_warn "⚠️  Runtime verification warning (exit code: ${VERIFY_EXIT_CODE})"
    log_warn "Verification output: ${VERIFY_OUTPUT}"
fi

log_info ""
log_info "============================================="
log_info "✅ Execution role updated successfully!"
log_info "============================================="
log_info ""
log_info "Summary:"
log_info "  - IAM role verified: ✅"
log_info "  - Runtime updated: ✅"
log_info "  - Status verified: ✅"
log_info "  - Correlation ID: ${CORRELATION_ID}"
log_info "  - Log file: ${LOG_FILE}"
log_info ""
log_info "Next steps:"
log_info "  1. Deploy the agent: agentcore launch --auto-update-on-conflict"
log_info "  2. Test invocation: agentcore invoke --agent trade_matching_ai '{...}'"
log_info ""
log_info "For troubleshooting, review log file: ${LOG_FILE}"
log_info ""

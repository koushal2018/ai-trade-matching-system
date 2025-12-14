#!/bin/bash
# A2A Environment Setup Script
# Run with: source setup_a2a_env.sh

# Load Cognito authentication credentials
export $(grep -v '^#' .agentcore_identity_user.env | xargs)

# Enable A2A mode
export A2A_MODE=true

# Get bearer token (you'll need to run this manually due to authentication)
echo "🔐 Getting bearer token..."

# Try to get token with different auth flows
if BEARER_TOKEN=$(agentcore identity get-cognito-inbound-token 2>/dev/null); then
    export AGENTCORE_BEARER_TOKEN="$BEARER_TOKEN"
    echo "✅ Bearer token obtained and set"
else
    echo "⚠️ Unable to get bearer token automatically."
    echo "Please run this manually:"
    echo "  BEARER_TOKEN=\$(agentcore identity get-cognito-inbound-token)"
    echo "  export AGENTCORE_BEARER_TOKEN=\"\$BEARER_TOKEN\""
fi

echo "📊 A2A Configuration Status:"
echo "  A2A_MODE: $A2A_MODE"
echo "  RUNTIME_POOL_ID: $RUNTIME_POOL_ID"
echo "  RUNTIME_CLIENT_ID: $RUNTIME_CLIENT_ID"
echo "  AGENTCORE_BEARER_TOKEN: ${AGENTCORE_BEARER_TOKEN:+[SET]}${AGENTCORE_BEARER_TOKEN:-[NOT SET]}"

if [ -n "$AGENTCORE_BEARER_TOKEN" ]; then
    echo ""
    echo "🚀 Ready to test A2A integration!"
    echo "Test with:"
    echo "  python a2a_client_integration.py data/BANK/FAB_26933659.pdf --source-type BANK --document-id test_a2a_001"
else
    echo ""
    echo "❌ Bearer token not set. A2A communication will fail."
fi
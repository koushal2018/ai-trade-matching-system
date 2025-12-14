#!/bin/bash
# Run property test for session ID format

export AGENTCORE_MEMORY_ID="test-memory-id-12345"
export AWS_REGION="us-east-1"

# Run the property test
python test_property_3_session_id_format.py

# Capture exit code
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Property test passed"
else
    echo "❌ Property test failed with exit code $EXIT_CODE"
fi

exit $EXIT_CODE

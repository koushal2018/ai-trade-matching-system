#!/usr/bin/env python3
"""
Quick test script to invoke the trade extraction agent directly.
"""

import json
from trade_extraction_agent_strands import invoke

# Test payload
payload = {
    "document_id": "FAB_26933659",
    "canonical_output_location": "s3://trade-matching-system-agentcore-production/extracted/BANK/FAB_26933659.json",
    "source_type": "BANK",
    "correlation_id": "test_direct_001"
}

print("=" * 80)
print("Testing Trade Extraction Agent (Direct Invoke)")
print("=" * 80)
print(f"Payload: {json.dumps(payload, indent=2)}")
print("=" * 80)

# Invoke the agent
result = invoke(payload, context=None)

# Print results
print("\n" + "=" * 80)
print("RESULT")
print("=" * 80)
print(json.dumps(result, indent=2, default=str))
print("=" * 80)

if result.get("success"):
    print("\n✅ SUCCESS!")
else:
    print("\n❌ FAILED!")

#!/usr/bin/env python3
"""
Quick test to verify all imports work correctly before deployment.

Usage:
    python test_imports.py
"""

import sys
import os

print("=" * 80)
print("Testing Orchestrator Imports")
print("=" * 80)

# Test 1: Import status_tracker
print("\n1. Testing status_tracker import...")
try:
    from status_tracker import StatusTracker
    print("   ✅ StatusTracker imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import StatusTracker: {e}")
    sys.exit(1)

# Test 2: Import status_writer
print("\n2. Testing status_writer import...")
try:
    from status_writer import StatusWriter
    print("   ✅ StatusWriter imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import StatusWriter: {e}")
    sys.exit(1)

# Test 3: Import http_agent_orchestrator
print("\n3. Testing http_agent_orchestrator import...")
try:
    from http_agent_orchestrator import TradeMatchingHTTPOrchestrator
    print("   ✅ TradeMatchingHTTPOrchestrator imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import TradeMatchingHTTPOrchestrator: {e}")
    sys.exit(1)

# Test 4: Import main entrypoint
print("\n4. Testing main entrypoint import...")
try:
    from trade_matching_swarm_agentcore_http import app
    print("   ✅ BedrockAgentCoreApp imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import app: {e}")
    sys.exit(1)

# Test 5: Verify StatusTracker initialization
print("\n5. Testing StatusTracker initialization...")
try:
    tracker = StatusTracker(
        table_name="trade-matching-system-processing-status",
        region_name="us-east-1"
    )
    print("   ✅ StatusTracker initialized successfully")
    print(f"   Table: {tracker.table_name}")
    print(f"   Region: {tracker.region_name}")
except Exception as e:
    print(f"   ❌ Failed to initialize StatusTracker: {e}")
    sys.exit(1)

# Test 6: Verify StatusWriter initialization
print("\n6. Testing StatusWriter initialization...")
try:
    writer = StatusWriter(
        table_name="trade-matching-system-processing-status",
        region_name="us-east-1"
    )
    print("   ✅ StatusWriter initialized successfully")
    print(f"   Table: {writer.table_name}")
    print(f"   Region: {writer.region_name}")
    print(f"   Using Strands Tool: {writer.use_strands_tool}")
except Exception as e:
    print(f"   ❌ Failed to initialize StatusWriter: {e}")
    sys.exit(1)

# Test 7: Check required files exist
print("\n7. Checking required files...")
required_files = [
    "status_tracker.py",
    "status_writer.py",
    "http_agent_orchestrator.py",
    "trade_matching_swarm_agentcore_http.py",
    "idempotency.py",
    "Dockerfile",
    "requirements.txt"
]

for filename in required_files:
    if os.path.exists(filename):
        print(f"   ✅ {filename}")
    else:
        print(f"   ❌ {filename} NOT FOUND")
        sys.exit(1)

# Test 8: Verify Dockerfile includes status_writer.py
print("\n8. Checking Dockerfile...")
try:
    with open("Dockerfile", "r") as f:
        dockerfile_content = f.read()
        if "status_writer.py" in dockerfile_content:
            print("   ✅ Dockerfile includes status_writer.py")
        else:
            print("   ❌ Dockerfile missing status_writer.py")
            sys.exit(1)
        
        if "status_tracker.py" in dockerfile_content:
            print("   ✅ Dockerfile includes status_tracker.py")
        else:
            print("   ⚠️  Dockerfile missing status_tracker.py (may be needed)")
except Exception as e:
    print(f"   ❌ Failed to check Dockerfile: {e}")
    sys.exit(1)

# Test 9: Verify requirements.txt has boto3
print("\n9. Checking requirements.txt...")
try:
    with open("requirements.txt", "r") as f:
        requirements = f.read()
        if "boto3" in requirements:
            print("   ✅ requirements.txt includes boto3")
        else:
            print("   ❌ requirements.txt missing boto3")
            sys.exit(1)
except Exception as e:
    print(f"   ❌ Failed to check requirements.txt: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ ALL IMPORT TESTS PASSED!")
print("=" * 80)
print("\nThe orchestrator is ready for deployment!")
print("\nNext steps:")
print("  1. Test status tracking: python test_status_tracking_local.py")
print("  2. Deploy to AgentCore: agentcore deploy --agent http_agent_orchestrator")
print("=" * 80)

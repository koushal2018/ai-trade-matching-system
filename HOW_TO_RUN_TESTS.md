# How to Run Tests - Quick Guide

## You Are Here: `deployment/swarm_agentcore/`

The test scripts are in the **project root**, not in this directory.

## Quick Solution

### Option 1: Use the Local Test Runner (Easiest)

```bash
bash run_tests.sh
```

This script automatically navigates to the project root and runs all tests.

### Option 2: Navigate to Root First

```bash
# Go to project root
cd ../..

# Now you can run any test command
bash run_all_swarm_agentcore_tests.sh
```

### Option 3: Run from Root Directly

```bash
# From deployment/swarm_agentcore, run:
cd ../.. && bash run_all_swarm_agentcore_tests.sh
```

## What You Saw

```bash
20a5cbcaa9c0:swarm_agentcore koushald$ python check_test_status.py
# Error: No such file or directory
```

**Why**: `check_test_status.py` is in the project root (`../../check_test_status.py`), not in `deployment/swarm_agentcore/`.

## File Locations

```
ai-trade-matching-system-2/              ← PROJECT ROOT (you need to be here)
├── run_all_swarm_agentcore_tests.sh     ← Main test runner
├── HOW_TO_RUN_TESTS.md                  ← This guide
├── test_property_1_*.py                 ← Property tests (6 files)
├── test_property_2_*.py
├── test_property_3_*.py
├── test_property_4_*.py
├── test_property_5_*.py
├── test_property_6_*.py
└── deployment/
    └── swarm_agentcore/                 ← YOU ARE HERE
        ├── run_tests.sh                 ← Local test runner (use this!)
        ├── test_memory_resource_creation.py
        ├── test_session_manager_creation.py
        ├── test_agent_creation.py
        ├── test_error_handling.py
        ├── test_integration_*.py
        └── test_performance_*.py
```

## Commands That Work

### From `deployment/swarm_agentcore/` (where you are now):

```bash
# Use the local runner
bash run_tests.sh

# Or navigate to root
cd ../..
bash run_all_swarm_agentcore_tests.sh
```

### From project root:

```bash
# Run all tests
bash run_all_swarm_agentcore_tests.sh
```

## Expected Behavior

Tests will either:
- ✅ **PASS**: Test executed successfully
- ⚠️  **SKIP**: Test skipped (missing AGENTCORE_MEMORY_ID) - **This is normal!**
- ❌ **FAIL**: Test found an issue

**Skipped tests are expected** when `AGENTCORE_MEMORY_ID` is not set. The tests are designed to gracefully skip when AWS resources are not configured.

## To Run Full Tests (Optional)

If you want to run tests with AWS resources:

```bash
# 1. Create memory resource (from project root)
cd ../..
python deployment/swarm_agentcore/setup_memory.py

# 2. Export the memory ID (from setup output)
export AGENTCORE_MEMORY_ID=<memory-id-from-setup>

# 3. Run tests
bash run_all_swarm_agentcore_tests.sh
```

## Summary

**The key point**: Test scripts are in the project root, not in `deployment/swarm_agentcore/`.

**Easiest solution**: Run `bash run_tests.sh` from where you are now.

**Alternative**: Navigate to root first with `cd ../..` then run any test command.

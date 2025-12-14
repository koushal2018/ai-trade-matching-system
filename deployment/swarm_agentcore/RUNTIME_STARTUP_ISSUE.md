# Runtime Startup Issue - Import Error

**Date**: December 14, 2025  
**Agent**: trade_matching_swarm-k8M6uU5w6H  
**Status**: ❌ FAILING AT RUNTIME

## Problem

The AgentCore Runtime is failing with error:
```
RuntimeClientError: An error occurred when starting the runtime
```

## Root Cause Analysis

### What We Know:
1. ✅ Container builds successfully
2. ✅ Entrypoint file is present: `/app/trade_matching_swarm_agentcore_http.py`
3. ✅ Observability warning appears (non-critical)
4. ❌ Runtime fails when trying to process requests

### The Issue:

The entrypoint file `trade_matching_swarm_agentcore_http.py` contains this import:
```python
from http_agent_orchestrator import TradeMatchingHTTPOrchestrator
```

**This import is likely failing because `http_agent_orchestrator.py` is not being included in the container build.**

### Why This Happens:

AgentCore's container build process may not automatically include all Python files in the source directory. The entrypoint file is explicitly specified, but supporting modules need to be either:
1. In the same directory and explicitly referenced
2. Installed as a package
3. Listed in a specific way for the build process

## Evidence from Logs:

```
code.file.path": "/app/trade_matching_swarm_agentcore_http.py"
```

This shows the entrypoint is loaded, but there are NO logs showing:
- The import of `http_agent_orchestrator` succeeding
- The `TradeMatchingHTTPOrchestrator` class being initialized
- Any actual invocation processing

The runtime starts, loads the entrypoint, but then fails silently when the import fails.

## Solution Options

### Option 1: Combine Files (RECOMMENDED - FASTEST)
Merge `http_agent_orchestrator.py` into `trade_matching_swarm_agentcore_http.py` as a single file.

**Pros:**
- Guaranteed to work
- Single file deployment
- No import issues

**Cons:**
- Larger file
- Less modular

### Option 2: Create Python Package
Structure the code as a proper Python package with `__init__.py` and `setup.py`.

**Pros:**
- Clean module structure
- Reusable code

**Cons:**
- More complex
- Requires package installation in container

### Option 3: Verify source_path Configuration
Ensure `.bedrock_agentcore.yaml` has correct `source_path` that includes all files.

Current config:
```yaml
source_path: /Users/koushald/ai-trade-matching-system/deployment/swarm_agentcore
```

This SHOULD include all files in the directory, but may not be working as expected.

## Recommended Fix: Option 1 (Merge Files)

Create a single `trade_matching_swarm_agentcore_http_combined.py` that contains:
1. All imports from both files
2. The `AgentCoreHTTPClient` class
3. The `TradeMatchingHTTPOrchestrator` class  
4. The `@app.entrypoint` and `@app.ping` functions

Then update `.bedrock_agentcore.yaml`:
```yaml
entrypoint: trade_matching_swarm_agentcore_http_combined.py
```

And redeploy.

## Next Steps

1. Create combined file
2. Update `.bedrock_agentcore.yaml`
3. Redeploy: `agentcore deploy`
4. Test invocation
5. Monitor CloudWatch logs for success

## Alternative: Test Local Import

Before redeploying, we can test if the import works locally:
```bash
cd deployment/swarm_agentcore
python -c "from http_agent_orchestrator import TradeMatchingHTTPOrchestrator; print('Import successful')"
```

If this works locally but fails in container, it confirms the file is not being included in the build.

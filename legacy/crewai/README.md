# Legacy CrewAI Implementation

⚠️ **WARNING: This code is archived and NOT used in production** ⚠️

## Overview

This directory contains the legacy CrewAI-based implementation of the AI Trade Matching System. This code has been **deprecated** and replaced by the Strands SDK implementation.

## Why This Code Is Archived

The system has fully migrated to:
- **Strands SDK** for multi-agent orchestration
- **AWS Bedrock AgentCore** for deployment and management
- **Direct boto3 access** for AWS services

The CrewAI implementation is preserved here for:
- Historical reference
- Understanding the migration path
- Comparison with the new implementation

## What's Included

- `crew_fixed.py` - Main CrewAI crew definition
- `main.py` - CrewAI entry point
- `config/` - Agent and task configurations (agents.yaml, tasks.yaml)
- `tools/` - CrewAI-specific tools (custom_tool.py, ocr_tool.py, pdf_to_image.py)
- `tests/` - CrewAI functional parity tests

## Current Production Implementation

The active implementation is located in:
- `deployment/` - Strands-based agent deployments
- `deployment/swarm/trade_matching_swarm.py` - Main entry point

## Do NOT Use This Code

This code is:
- ❌ Not maintained
- ❌ Not deployed
- ❌ Not tested
- ❌ Missing dependencies (CrewAI removed from requirements.txt)

For current implementation, see the `deployment/` directory.

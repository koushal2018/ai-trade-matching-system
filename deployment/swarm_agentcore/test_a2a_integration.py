#!/usr/bin/env python3
"""
A2A Integration Test Script

This script tests the A2A integration with deployed AgentCore agents to ensure
the trade matching workflow works correctly using agent-to-agent communication.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from a2a_client_integration import (
    TradeMatchingA2AOrchestrator,
    get_bearer_token_from_env,
    AGENT_CONFIGS
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_individual_agent(agent_name: str, bearer_token: str) -> Dict[str, Any]:
    """
    Test communication with a single agent.
    
    Args:
        agent_name: Name of the agent to test
        bearer_token: Authentication token
        
    Returns:
        Test result dictionary
    """
    from a2a_client_integration import A2AAgentClient
    
    agent_config = AGENT_CONFIGS.get(agent_name)
    if not agent_config:
        return {
            "success": False,
            "error": f"Agent {agent_name} not found in configuration"
        }
    
    client = A2AAgentClient(
        agent_arn=agent_config["arn"],
        bearer_token=bearer_token,
        timeout=60  # 1 minute timeout for testing
    )
    
    # Simple test message
    test_message = f"Hello {agent_name}, this is a connectivity test. Please respond with your capabilities."
    
    try:
        logger.info(f"Testing {agent_name}...")
        result = await client.send_message(test_message)
        
        if result.get("success"):
            logger.info(f"✅ {agent_name} responded successfully")
            return {
                "success": True,
                "agent_name": agent_name,
                "agent_arn": agent_config["arn"],
                "response_length": len(str(result.get("response", ""))),
                "session_id": result.get("session_id")
            }
        else:
            logger.error(f"❌ {agent_name} failed: {result.get('error')}")
            return {
                "success": False,
                "agent_name": agent_name,
                "error": result.get("error")
            }
            
    except Exception as e:
        logger.error(f"❌ {agent_name} exception: {e}")
        return {
            "success": False,
            "agent_name": agent_name,
            "error": str(e)
        }


async def test_full_workflow(bearer_token: str) -> Dict[str, Any]:
    """
    Test the complete A2A workflow with a sample document.
    
    Args:
        bearer_token: Authentication token
        
    Returns:
        Workflow test result
    """
    orchestrator = TradeMatchingA2AOrchestrator(bearer_token)
    
    # Test with a sample document
    test_payload = {
        "document_path": "data/BANK/FAB_26933659.pdf",
        "source_type": "BANK", 
        "document_id": "test_a2a_workflow_001"
    }
    
    try:
        logger.info("Testing full A2A workflow...")
        result = await orchestrator.process_trade_confirmation(
            document_path=test_payload["document_path"],
            source_type=test_payload["source_type"],
            document_id=test_payload["document_id"]
        )
        
        if result.get("success"):
            logger.info("✅ Full workflow completed successfully")
            return {
                "success": True,
                "test_type": "full_workflow",
                "document_id": test_payload["document_id"],
                "workflow_steps_completed": len(result.get("workflow_steps", {})),
                "session_id": result.get("session_id")
            }
        else:
            logger.error(f"❌ Workflow failed: {result.get('error')}")
            return {
                "success": False,
                "test_type": "full_workflow", 
                "error": result.get("error"),
                "step": result.get("step")
            }
            
    except Exception as e:
        logger.error(f"❌ Workflow exception: {e}")
        return {
            "success": False,
            "test_type": "full_workflow",
            "error": str(e)
        }


async def run_connectivity_tests(bearer_token: str) -> Dict[str, Any]:
    """
    Run connectivity tests for all agents.
    
    Args:
        bearer_token: Authentication token
        
    Returns:
        Test results summary
    """
    logger.info("🧪 Running A2A Connectivity Tests")
    logger.info("=" * 50)
    
    results = {
        "connectivity_tests": {},
        "summary": {
            "total_agents": len(AGENT_CONFIGS),
            "successful_agents": 0,
            "failed_agents": 0
        }
    }
    
    # Test each agent individually
    for agent_name in AGENT_CONFIGS.keys():
        result = await test_individual_agent(agent_name, bearer_token)
        results["connectivity_tests"][agent_name] = result
        
        if result.get("success"):
            results["summary"]["successful_agents"] += 1
        else:
            results["summary"]["failed_agents"] += 1
    
    return results


def check_prerequisites() -> tuple[bool, str]:
    """
    Check if all prerequisites are met for testing.
    
    Returns:
        Tuple of (success, message)
    """
    logger.info("🔍 Checking prerequisites...")
    
    # Check bearer token
    try:
        bearer_token = get_bearer_token_from_env()
        if not bearer_token or len(bearer_token) < 10:
            return False, "Invalid bearer token. Run setup_a2a_authentication.py first."
    except ValueError as e:
        return False, f"Bearer token not configured: {e}"
    
    # Check A2A mode
    a2a_mode = os.environ.get("A2A_MODE", "false").lower()
    if a2a_mode != "true":
        return False, "A2A_MODE not enabled. Run: export A2A_MODE=true"
    
    # Check required modules
    try:
        import httpx
        from a2a.client import A2ACardResolver
    except ImportError as e:
        return False, f"A2A dependencies not installed: {e}. Run: pip install strands-agents[a2a] httpx"
    
    logger.info("✅ Prerequisites check passed")
    return True, "All prerequisites met"


async def main():
    """Main test function."""
    print("🧪 A2A Integration Test Suite")
    print("Testing communication with deployed AgentCore agents")
    print("=" * 60)
    
    # Check prerequisites
    prereq_ok, prereq_msg = check_prerequisites()
    if not prereq_ok:
        print(f"❌ Prerequisites check failed: {prereq_msg}")
        return 1
    
    # Get bearer token
    try:
        bearer_token = get_bearer_token_from_env()
    except Exception as e:
        print(f"❌ Failed to get bearer token: {e}")
        return 1
    
    print("✅ Authentication configured")
    print(f"✅ Testing {len(AGENT_CONFIGS)} agents")
    
    # Run connectivity tests
    try:
        connectivity_results = await run_connectivity_tests(bearer_token)
        
        print("\n📊 Connectivity Test Results:")
        print("-" * 30)
        
        for agent_name, result in connectivity_results["connectivity_tests"].items():
            status = "✅ PASS" if result.get("success") else "❌ FAIL"
            error_msg = f" - {result.get('error', '')}" if not result.get("success") else ""
            print(f"{agent_name:20} {status}{error_msg}")
        
        summary = connectivity_results["summary"]
        print(f"\nSummary: {summary['successful_agents']}/{summary['total_agents']} agents responding")
        
        # Run full workflow test if connectivity is good
        if summary["successful_agents"] >= 3:  # Need at least 3 agents for meaningful test
            print("\n🔄 Running Full Workflow Test...")
            workflow_result = await test_full_workflow(bearer_token)
            
            if workflow_result.get("success"):
                print("✅ Full workflow test PASSED")
                print(f"   Document ID: {workflow_result.get('document_id')}")
                print(f"   Steps completed: {workflow_result.get('workflow_steps_completed')}")
            else:
                print("❌ Full workflow test FAILED")
                print(f"   Error: {workflow_result.get('error')}")
                print(f"   Failed at step: {workflow_result.get('step', 'unknown')}")
        else:
            print("\n⚠️ Skipping workflow test - insufficient agents responding")
        
        # Final results
        all_passed = (summary["failed_agents"] == 0 and 
                     (summary["successful_agents"] < 3 or workflow_result.get("success")))
        
        print("\n" + "=" * 60)
        if all_passed:
            print("🎉 ALL TESTS PASSED!")
            print("Your A2A integration is working correctly.")
            print("\nNext steps:")
            print("1. Deploy swarm with A2A mode: agentcore deploy")
            print("2. Test via AgentCore: agentcore invoke '{\"document_path\": \"data/BANK/FAB_26933659.pdf\", \"source_type\": \"BANK\", \"document_id\": \"test_001\"}'")
        else:
            print("❌ SOME TESTS FAILED!")
            print("Please check the error messages above and ensure:")
            print("1. All agents are deployed and ready")
            print("2. Bearer token is valid and not expired")
            print("3. Network connectivity to AgentCore")
        
        return 0 if all_passed else 1
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        logger.error(f"Test execution failed: {e}", exc_info=True)
        return 1


def main_sync():
    """Synchronous wrapper for main function."""
    return asyncio.run(main())


if __name__ == "__main__":
    exit(main_sync())
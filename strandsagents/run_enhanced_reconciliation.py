#!/usr/bin/env python3
"""
Run Enhanced AI-Powered Trade Reconciliation

This script demonstrates the enhanced Strands agents with AI capabilities
in different decision modes (deterministic, LLM, hybrid).
"""

import asyncio
import logging
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_workflow import (
    EnhancedReconciliationWorkflow,
    run_deterministic_workflow,
    run_llm_workflow,
    run_hybrid_workflow
)
from enhanced_config import (
    EnhancedMatcherConfig,
    EnhancedReconcilerConfig,
    EnhancedReportConfig,
    DecisionMode,
    AIProviderType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'enhanced_reconciliation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)


def print_banner():
    """Print application banner."""
    print("\n" + "="*80)
    print("ENHANCED AI-POWERED TRADE RECONCILIATION")
    print("Strands Agents SDK with Configurable AI Providers")
    print("="*80)


def print_configuration_info():
    """Print current configuration information."""
    print("\nCurrent Configuration:")
    print("-" * 40)
    print(f"Decision Mode: {os.getenv('DECISION_MODE', 'deterministic')}")
    print(f"AI Provider: {os.getenv('AI_PROVIDER_TYPE', 'bedrock')}")
    print(f"AI Region: {os.getenv('AI_PROVIDER_REGION', 'us-east-1')}")
    print(f"Confidence Threshold: {os.getenv('CONFIDENCE_THRESHOLD', '0.8')}")
    print(f"Semantic Threshold: {os.getenv('MATCHER_SEMANTIC_THRESHOLD', '0.85')}")
    print(f"Context Analysis: {os.getenv('MATCHER_CONTEXT_ANALYSIS_ENABLED', 'True')}")


def print_results_summary(results: Dict[str, Any]):
    """Print workflow results summary."""
    print("\n" + "="*80)
    print("WORKFLOW EXECUTION RESULTS")
    print("="*80)
    
    print(f"Workflow ID: {results.get('workflow_id', 'N/A')}")
    print(f"Status: {results.get('status', 'N/A')}")
    print(f"Total Duration: {results.get('total_duration_seconds', 0):.2f} seconds")
    
    if 'configuration' in results:
        config = results['configuration']
        print(f"\nConfiguration Used:")
        print(f"  Matcher Mode: {config.get('matcher_mode', 'N/A')}")
        print(f"  Reconciler Mode: {config.get('reconciler_mode', 'N/A')}")
        print(f"  AI Provider: {config.get('ai_provider', 'N/A')}")
        print(f"  AI Region: {config.get('ai_region', 'N/A')}")
    
    if 'phases' in results:
        print(f"\nPhase Execution:")
        for phase_name, phase_data in results['phases'].items():
            status = phase_data.get('status', 'N/A')
            duration = phase_data.get('duration_seconds', 0)
            print(f"  {phase_name.title()}: {status} ({duration:.2f}s)")
    
    if 'summary' in results:
        print(f"\nExecution Summary:")
        summary = results['summary']
        for key, value in summary.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
    
    if results.get('status') == 'failed' and 'error' in results:
        print(f"\nError: {results['error']}")


async def run_demo_workflow(mode: str = "deterministic", 
                           ai_provider: str = "bedrock",
                           region: str = "us-east-1") -> Dict[str, Any]:
    """
    Run a demonstration workflow with mock data.
    
    Args:
        mode: Decision mode ("deterministic", "llm", "hybrid")
        ai_provider: AI provider type ("bedrock", "sagemaker", "huggingface")
        region: AWS region
        
    Returns:
        Workflow execution results
    """
    logger.info(f"Starting demo workflow in {mode} mode with {ai_provider} provider")
    
    try:
        # Set environment variables for this demo
        os.environ['DECISION_MODE'] = mode
        os.environ['AI_PROVIDER_TYPE'] = ai_provider
        os.environ['AI_PROVIDER_REGION'] = region
        
        # Run appropriate workflow based on mode
        if mode == "deterministic":
            results = await run_deterministic_workflow(
                matching_limit=50,
                reconciliation_limit=50,
                report_limit=100
            )
        elif mode == "llm":
            results = await run_llm_workflow(
                ai_provider_type=ai_provider,
                region=region,
                matching_limit=50,
                reconciliation_limit=50,
                report_limit=100
            )
        elif mode == "hybrid":
            results = await run_hybrid_workflow(
                ai_provider_type=ai_provider,
                region=region,
                matching_limit=50,
                reconciliation_limit=50,
                report_limit=100
            )
        else:
            raise ValueError(f"Invalid mode: {mode}")
        
        logger.info(f"Demo workflow completed successfully in {mode} mode")
        return results
        
    except Exception as e:
        logger.error(f"Demo workflow failed: {e}")
        return {
            "workflow_id": f"demo-{mode}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "status": "failed",
            "error": str(e),
            "mode": mode,
            "ai_provider": ai_provider
        }


async def run_configuration_test():
    """Test different configuration scenarios."""
    print("\n" + "="*80)
    print("CONFIGURATION TESTING")
    print("="*80)
    
    test_scenarios = [
        {
            "name": "Deterministic Mode",
            "mode": "deterministic",
            "ai_provider": "bedrock",
            "region": "us-east-1"
        },
        {
            "name": "LLM Mode with Bedrock",
            "mode": "llm", 
            "ai_provider": "bedrock",
            "region": "us-east-1"
        },
        {
            "name": "Hybrid Mode with Sagemaker",
            "mode": "hybrid",
            "ai_provider": "sagemaker", 
            "region": "me-central-1"
        }
    ]
    
    results = {}
    
    for scenario in test_scenarios:
        print(f"\nTesting: {scenario['name']}")
        print("-" * 40)
        
        try:
            # Create workflow with specific configuration
            from enhanced_config import AIProviderConfig, DecisionModeConfig
            
            decision_config = DecisionModeConfig(mode=scenario['mode'])
            ai_config = AIProviderConfig(
                provider_type=scenario['ai_provider'],
                region=scenario['region']
            )
            
            matcher_config = EnhancedMatcherConfig(
                decision_mode_config=decision_config,
                ai_provider_config=ai_config
            )
            
            workflow = EnhancedReconciliationWorkflow(
                matcher_config=matcher_config,
                reconciler_config=None,  # Will use defaults
                report_config=None  # Will use defaults
            )
            
            # Test agent initialization
            init_success = await workflow.initialize_agents()
            
            # Get configuration summary
            config_summary = workflow.get_configuration_summary()
            
            results[scenario['name']] = {
                "initialization_success": init_success,
                "configuration": config_summary,
                "mode": scenario['mode'],
                "ai_provider": scenario['ai_provider']
            }
            
            print(f"  Initialization: {'SUCCESS' if init_success else 'FAILED'}")
            print(f"  Mode: {config_summary['matcher_configuration']['decision_mode']}")
            print(f"  AI Provider: {config_summary['matcher_configuration']['ai_provider']}")
            
        except Exception as e:
            logger.error(f"Configuration test failed for {scenario['name']}: {e}")
            results[scenario['name']] = {
                "initialization_success": False,
                "error": str(e)
            }
            print(f"  ERROR: {e}")
    
    return results


async def interactive_mode():
    """Run in interactive mode allowing user to choose options."""
    print("\n" + "="*80)
    print("INTERACTIVE MODE")
    print("="*80)
    
    print("\nAvailable Decision Modes:")
    print("1. Deterministic (traditional rule-based)")
    print("2. LLM (AI-powered intelligent matching)")
    print("3. Hybrid (combination of both)")
    
    while True:
        try:
            choice = input("\nSelect decision mode (1-3) or 'q' to quit: ").strip()
            
            if choice.lower() == 'q':
                print("Exiting interactive mode.")
                return
            
            mode_map = {"1": "deterministic", "2": "llm", "3": "hybrid"}
            if choice not in mode_map:
                print("Invalid choice. Please select 1, 2, 3, or 'q'.")
                continue
            
            mode = mode_map[choice]
            
            # Get AI provider if needed
            ai_provider = "bedrock"
            region = "us-east-1"
            
            if mode in ["llm", "hybrid"]:
                print("\nAvailable AI Providers:")
                print("1. AWS Bedrock (us-east-1)")
                print("2. AWS Sagemaker (me-central-1)")
                print("3. Huggingface (any region)")
                
                provider_choice = input("Select AI provider (1-3): ").strip()
                provider_map = {
                    "1": ("bedrock", "us-east-1"),
                    "2": ("sagemaker", "me-central-1"), 
                    "3": ("huggingface", "us-east-1")
                }
                
                if provider_choice in provider_map:
                    ai_provider, region = provider_map[provider_choice]
                else:
                    print("Invalid choice, using default Bedrock.")
            
            print(f"\nRunning workflow in {mode} mode with {ai_provider} provider...")
            
            # Run the workflow
            results = await run_demo_workflow(mode, ai_provider, region)
            print_results_summary(results)
            
            # Ask if user wants to continue
            continue_choice = input("\nRun another workflow? (y/n): ").strip().lower()
            if continue_choice != 'y':
                break
                
        except KeyboardInterrupt:
            print("\nExiting interactive mode.")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue


async def main():
    """Main execution function."""
    print_banner()
    print_configuration_info()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            # Run configuration tests
            test_results = await run_configuration_test()
            print(f"\nConfiguration test results:")
            print(json.dumps(test_results, indent=2, default=str))
            
        elif command == "interactive":
            # Run in interactive mode
            await interactive_mode()
            
        elif command in ["deterministic", "llm", "hybrid"]:
            # Run specific mode
            ai_provider = sys.argv[2] if len(sys.argv) > 2 else "bedrock"
            region = sys.argv[3] if len(sys.argv) > 3 else "us-east-1"
            
            results = await run_demo_workflow(command, ai_provider, region)
            print_results_summary(results)
            
        else:
            print(f"Unknown command: {command}")
            print("Usage: python run_enhanced_reconciliation.py [test|interactive|deterministic|llm|hybrid] [ai_provider] [region]")
            sys.exit(1)
    else:
        # Default: run based on environment configuration
        mode = os.getenv('DECISION_MODE', 'deterministic')
        ai_provider = os.getenv('AI_PROVIDER_TYPE', 'bedrock')
        region = os.getenv('AI_PROVIDER_REGION', 'us-east-1')
        
        print(f"\nRunning default workflow in {mode} mode...")
        results = await run_demo_workflow(mode, ai_provider, region)
        print_results_summary(results)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExecution interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application failed: {e}")
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)
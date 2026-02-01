#!/usr/bin/env python3
"""
Agent Registration Deployment Script for Trade Extraction Agent.

This script handles the registration of the Trade Extraction Agent
in the DynamoDB AgentRegistry table as part of the deployment process.

Requirements: 3.5, 7.4
"""

import os
import sys
import argparse
import logging
import boto3
from typing import Optional, Tuple
from datetime import datetime, timezone

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from agent_registry import AgentRegistryManager
except ImportError as e:
    print(f"❌ Error importing agent_registry module: {e}")
    print("Make sure agent_registry.py is in the same directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_agentcore_runtime_arn(agent_name: str, region: str) -> Optional[str]:
    """
    Retrieve the AgentCore runtime ARN for the deployed agent.
    
    Args:
        agent_name: Name of the agent
        region: AWS region
        
    Returns:
        Runtime ARN if found, None otherwise
    """
    try:
        # Try to get runtime ARN from AgentCore CLI
        import subprocess
        import json
        
        result = subprocess.run(
            ['agentcore', 'status', '--agent', agent_name, '--output', 'json'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            status_data = json.loads(result.stdout)
            runtime_arn = status_data.get('runtime_arn')
            if runtime_arn:
                logger.info(f"Retrieved runtime ARN from AgentCore: {runtime_arn}")
                return runtime_arn
        
        logger.warning("Could not retrieve runtime ARN from AgentCore CLI")
        
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
        logger.warning(f"Failed to get runtime ARN from AgentCore CLI: {e}")
    
    # Fallback: construct expected ARN pattern
    account_id = boto3.client('sts', region_name=region).get_caller_identity()['Account']
    fallback_arn = f"arn:aws:bedrock-agentcore:{region}:{account_id}:runtime/{agent_name}"
    logger.info(f"Using fallback runtime ARN: {fallback_arn}")
    return fallback_arn


def register_agent(
    agent_name: str,
    version: str,
    environment: str,
    region: str,
    runtime_arn: Optional[str] = None,
    force_update: bool = False
) -> Tuple[bool, Optional[str]]:
    """
    Register the Trade Extraction Agent in the registry.
    
    Args:
        agent_name: Name of the agent
        version: Agent version
        environment: Deployment environment
        region: AWS region
        runtime_arn: Optional runtime ARN (will be retrieved if not provided)
        force_update: Whether to force update existing registration
        
    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Initialize registry manager
        registry = AgentRegistryManager(region_name=region)
        
        # Get runtime ARN if not provided
        if not runtime_arn:
            runtime_arn = get_agentcore_runtime_arn(agent_name, region)
            if not runtime_arn:
                return False, "Could not determine runtime ARN"
        
        # Check if agent already exists
        success, existing_agent, error = registry.get_agent_info(agent_name)
        
        if success and existing_agent and not force_update:
            logger.info(f"Agent {agent_name} already registered with version {existing_agent.version}")
            
            # Update status and version if different
            if existing_agent.version != version or existing_agent.status != 'active':
                logger.info(f"Updating agent status and version...")
                return registry.update_agent_status(agent_name, 'active', version)
            else:
                logger.info("Agent registration is up to date")
                return True, None
        
        # Register or update the agent
        logger.info(f"Registering agent {agent_name} version {version}...")
        success, error = registry.register_trade_extraction_agent(
            runtime_arn=runtime_arn,
            version=version,
            status='active'
        )
        
        if success:
            logger.info(f"Successfully registered agent {agent_name}")
            
            # Verify registration
            verify_success, agent_info, verify_error = registry.get_agent_info(agent_name)
            if verify_success and agent_info:
                logger.info(f"Registration verified:")
                logger.info(f"  Agent ID: {agent_info.agent_id}")
                logger.info(f"  Version: {agent_info.version}")
                logger.info(f"  Status: {agent_info.status}")
                logger.info(f"  Runtime ARN: {agent_info.runtime_arn}")
                logger.info(f"  Capabilities: {', '.join(agent_info.capabilities)}")
                logger.info(f"  SOP Enabled: {agent_info.sop_enabled}")
            else:
                logger.warning(f"Could not verify registration: {verify_error}")
        
        return success, error
        
    except Exception as e:
        error_msg = f"Unexpected error during agent registration: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def unregister_agent(agent_name: str, region: str) -> Tuple[bool, Optional[str]]:
    """
    Unregister the agent by setting status to inactive.
    
    Args:
        agent_name: Name of the agent
        region: AWS region
        
    Returns:
        Tuple of (success, error_message)
    """
    try:
        registry = AgentRegistryManager(region_name=region)
        
        logger.info(f"Setting agent {agent_name} status to inactive...")
        success, error = registry.update_agent_status(agent_name, 'inactive')
        
        if success:
            logger.info(f"Successfully deactivated agent {agent_name}")
        
        return success, error
        
    except Exception as e:
        error_msg = f"Error during agent deactivation: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def list_agents(region: str, agent_type: Optional[str] = None):
    """
    List registered agents.
    
    Args:
        region: AWS region
        agent_type: Optional agent type filter
    """
    try:
        registry = AgentRegistryManager(region_name=region)
        
        if agent_type:
            success, agents, error = registry.list_agents_by_type(agent_type)
            if not success:
                logger.error(f"Failed to list agents: {error}")
                return
        else:
            # For simplicity, just try to get the trade extraction agent
            success, agent_info, error = registry.get_agent_info('trade-extraction-agent')
            if success and agent_info:
                agents = [agent_info]
            else:
                agents = []
        
        if not agents:
            print("No agents found")
            return
        
        print(f"\nRegistered Agents ({len(agents)}):")
        print("-" * 80)
        
        for agent in agents:
            print(f"Agent ID: {agent.agent_id}")
            print(f"  Name: {agent.agent_name}")
            print(f"  Type: {agent.agent_type}")
            print(f"  Version: {agent.version}")
            print(f"  Status: {agent.status}")
            print(f"  Runtime ARN: {agent.runtime_arn}")
            print(f"  Capabilities: {', '.join(agent.capabilities)}")
            print(f"  SOP Enabled: {agent.sop_enabled}")
            print(f"  Created: {agent.created_at}")
            print(f"  Updated: {agent.updated_at}")
            print()
        
    except Exception as e:
        logger.error(f"Error listing agents: {e}")


def main():
    """Main function for agent registration deployment."""
    parser = argparse.ArgumentParser(
        description='Deploy agent registration for Trade Extraction Agent'
    )
    
    parser.add_argument(
        'action',
        choices=['register', 'unregister', 'list', 'status'],
        help='Action to perform'
    )
    
    parser.add_argument(
        '--agent-name',
        default='trade-extraction-agent',
        help='Name of the agent (default: trade-extraction-agent)'
    )
    
    parser.add_argument(
        '--version',
        default='2.0.0',
        help='Agent version (default: 2.0.0)'
    )
    
    parser.add_argument(
        '--environment',
        default='production',
        choices=['development', 'staging', 'production'],
        help='Deployment environment (default: production)'
    )
    
    parser.add_argument(
        '--region',
        default=os.getenv('AWS_REGION', 'us-east-1'),
        help='AWS region (default: us-east-1 or AWS_REGION env var)'
    )
    
    parser.add_argument(
        '--runtime-arn',
        help='AgentCore runtime ARN (will be auto-detected if not provided)'
    )
    
    parser.add_argument(
        '--force-update',
        action='store_true',
        help='Force update existing agent registration'
    )
    
    parser.add_argument(
        '--agent-type',
        help='Filter agents by type (for list action)'
    )
    
    args = parser.parse_args()
    
    # Validate AWS credentials
    try:
        boto3.client('sts', region_name=args.region).get_caller_identity()
    except Exception as e:
        logger.error(f"AWS credentials not configured or invalid: {e}")
        sys.exit(1)
    
    # Execute the requested action
    if args.action == 'register':
        success, error = register_agent(
            agent_name=args.agent_name,
            version=args.version,
            environment=args.environment,
            region=args.region,
            runtime_arn=args.runtime_arn,
            force_update=args.force_update
        )
        
        if success:
            print(f"✅ Agent {args.agent_name} registered successfully")
            sys.exit(0)
        else:
            print(f"❌ Failed to register agent: {error}")
            sys.exit(1)
    
    elif args.action == 'unregister':
        success, error = unregister_agent(args.agent_name, args.region)
        
        if success:
            print(f"✅ Agent {args.agent_name} deactivated successfully")
            sys.exit(0)
        else:
            print(f"❌ Failed to deactivate agent: {error}")
            sys.exit(1)
    
    elif args.action == 'list':
        list_agents(args.region, args.agent_type)
    
    elif args.action == 'status':
        try:
            registry = AgentRegistryManager(region_name=args.region)
            success, agent_info, error = registry.get_agent_info(args.agent_name)
            
            if success and agent_info:
                print(f"\nAgent Status: {args.agent_name}")
                print("-" * 40)
                print(f"Name: {agent_info.agent_name}")
                print(f"Type: {agent_info.agent_type}")
                print(f"Version: {agent_info.version}")
                print(f"Status: {agent_info.status}")
                print(f"Runtime ARN: {agent_info.runtime_arn}")
                print(f"Capabilities: {', '.join(agent_info.capabilities)}")
                print(f"SOP Enabled: {agent_info.sop_enabled}")
                print(f"SOP Version: {agent_info.sop_version}")
                print(f"Created: {agent_info.created_at}")
                print(f"Updated: {agent_info.updated_at}")
            else:
                print(f"❌ Agent {args.agent_name} not found: {error}")
                sys.exit(1)
                
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            sys.exit(1)


if __name__ == '__main__':
    main()
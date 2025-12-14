#!/usr/bin/env python3
"""
A2A Authentication Setup Script

This script helps configure authentication for A2A communication with deployed AgentCore agents.
It guides you through setting up the bearer token required for secure agent-to-agent communication.
"""

import os
import subprocess
import sys
import json
from typing import Optional


def run_command(command: str, capture_output: bool = True) -> tuple[bool, str]:
    """
    Run a shell command and return success status and output.
    
    Args:
        command: Command to run
        capture_output: Whether to capture and return output
        
    Returns:
        Tuple of (success, output)
    """
    try:
        if capture_output:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout.strip()
        else:
            result = subprocess.run(command, shell=True, timeout=30)
            return result.returncode == 0, ""
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def check_agentcore_cli() -> bool:
    """Check if AgentCore CLI is available."""
    success, _ = run_command("agentcore --help")
    return success


def setup_cognito_authentication():
    """
    Guide user through setting up Cognito authentication.
    """
    print("\n🔐 Setting up Cognito Authentication for A2A Communication")
    print("=" * 60)
    
    print("\nThis will set up Cognito user pools for authenticating A2A calls to your deployed agents.")
    print("You'll get a bearer token that the swarm orchestrator can use to communicate with agents.")
    
    # Check if AgentCore CLI is available
    if not check_agentcore_cli():
        print("\n❌ AgentCore CLI not found!")
        print("Install with: pip install bedrock-agentcore-starter-toolkit")
        return False
    
    print("\n✅ AgentCore CLI found")
    
    # Step 1: Setup Cognito pools
    print("\n📋 Step 1: Setting up Cognito user pools")
    print("This creates the necessary authentication infrastructure...")
    
    user_choice = input("Run 'agentcore identity setup-cognito'? (y/n): ").lower().strip()
    if user_choice != 'y':
        print("⚠️ Skipping Cognito setup. You'll need to set this up manually.")
        return False
    
    print("\n🏗️ Creating Cognito user pools...")
    success, output = run_command("agentcore identity setup-cognito", capture_output=False)
    
    if not success:
        print(f"❌ Failed to setup Cognito pools: {output}")
        return False
    
    print("✅ Cognito pools created successfully!")
    
    # Step 2: Load environment variables
    print("\n📋 Step 2: Loading authentication credentials")
    
    env_file = ".agentcore_identity_user.env"
    if not os.path.exists(env_file):
        print(f"❌ Environment file {env_file} not found!")
        print("The Cognito setup may not have completed successfully.")
        return False
    
    print(f"✅ Found environment file: {env_file}")
    
    # Load environment variables from file
    env_vars = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value.strip('"')
    
    # Export to current environment
    for key, value in env_vars.items():
        os.environ[key] = value
    
    print("✅ Environment variables loaded")
    
    # Step 3: Get bearer token
    print("\n📋 Step 3: Generating bearer token")
    
    success, token_output = run_command("agentcore identity get-cognito-inbound-token")
    
    if not success:
        print(f"❌ Failed to get bearer token: {token_output}")
        return False
    
    bearer_token = token_output.strip()
    print("✅ Bearer token generated successfully!")
    
    # Step 4: Save configuration
    print("\n📋 Step 4: Saving A2A configuration")
    
    a2a_config = {
        "bearer_token": bearer_token,
        "region": "us-east-1",
        "agents": {
            "pdf_adapter": "arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/pdf_adapter_agent-Az72YP53FJ",
            "trade_extractor": "arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/trade_extraction_agent-KnAx4O4ezw",
            "trade_matcher": "arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/trade_matching_agent-3aAvK64dQz",
            "exception_handler": "arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/exception_manager-uliBS5DsX3"
        }
    }
    
    # Save to JSON file
    config_file = "a2a_config.json"
    with open(config_file, 'w') as f:
        json.dump(a2a_config, f, indent=2)
    
    print(f"✅ A2A configuration saved to {config_file}")
    
    # Create environment setup script
    setup_script = """#!/bin/bash
# A2A Authentication Environment Setup
# Run with: source setup_a2a_env.sh

export A2A_MODE=true
export AGENTCORE_BEARER_TOKEN="{bearer_token}"

echo "✅ A2A mode enabled"
echo "✅ Bearer token configured"
echo "🚀 Ready to use A2A orchestration!"
""".format(bearer_token=bearer_token)
    
    with open("setup_a2a_env.sh", 'w') as f:
        f.write(setup_script)
    
    os.chmod("setup_a2a_env.sh", 0o755)
    
    print("✅ Environment setup script created: setup_a2a_env.sh")
    
    # Final instructions
    print("\n" + "="*60)
    print("🎉 A2A Authentication Setup Complete!")
    print("="*60)
    
    print("\nTo use A2A mode:")
    print("1. Load the environment:")
    print("   source setup_a2a_env.sh")
    print("")
    print("2. Test A2A communication:")
    print("   python a2a_client_integration.py \\")
    print("     data/BANK/FAB_26933659.pdf \\")
    print("     --source-type BANK \\")
    print("     --document-id test_a2a_001")
    print("")
    print("3. Deploy to AgentCore with A2A mode:")
    print("   export A2A_MODE=true")
    print("   export AGENTCORE_BEARER_TOKEN=\"$(cat a2a_config.json | jq -r '.bearer_token')\"")
    print("   agentcore deploy")
    
    return True


def verify_agent_status():
    """Verify that all required agents are deployed and ready."""
    print("\n🔍 Verifying deployed agent status...")
    
    required_agents = [
        "pdf_adapter_agent",
        "trade_extraction_agent", 
        "trade_matching_agent",
        "exception_manager"
    ]
    
    agent_dirs = [
        "/Users/koushald/ai-trade-matching-system-2/deployment/pdf_adapter",
        "/Users/koushald/ai-trade-matching-system-2/deployment/trade_extraction",
        "/Users/koushald/ai-trade-matching-system-2/deployment/trade_matching",
        "/Users/koushald/ai-trade-matching-system-2/deployment/exception_management"
    ]
    
    all_ready = True
    
    for i, agent_dir in enumerate(agent_dirs):
        agent_name = required_agents[i]
        print(f"\nChecking {agent_name}...")
        
        if not os.path.exists(agent_dir):
            print(f"❌ Agent directory not found: {agent_dir}")
            all_ready = False
            continue
        
        # Change to agent directory and check status
        original_dir = os.getcwd()
        try:
            os.chdir(agent_dir)
            success, output = run_command("agentcore status")
            
            if success and "Ready" in output:
                print(f"✅ {agent_name} is ready")
            else:
                print(f"⚠️ {agent_name} status: {output[:100]}...")
                all_ready = False
                
        except Exception as e:
            print(f"❌ Failed to check {agent_name}: {e}")
            all_ready = False
        finally:
            os.chdir(original_dir)
    
    if all_ready:
        print("\n✅ All agents are deployed and ready!")
    else:
        print("\n⚠️ Some agents may not be ready. Deploy them with 'agentcore deploy' in their respective directories.")
    
    return all_ready


def main():
    """Main setup function."""
    print("🚀 A2A Authentication Setup for Trade Matching System")
    print("This script helps you configure authentication to communicate with your deployed AgentCore agents.")
    
    # Step 1: Verify agent deployment status
    if not verify_agent_status():
        print("\n⚠️ Please ensure all agents are deployed before setting up A2A authentication.")
        user_choice = input("Continue anyway? (y/n): ").lower().strip()
        if user_choice != 'y':
            print("Exiting setup. Deploy your agents first and then run this script again.")
            return 1
    
    # Step 2: Setup authentication
    if setup_cognito_authentication():
        print("\n🎉 Setup completed successfully!")
        print("\nYou now have two modes available:")
        print("1. Strands Swarm Mode (default): Local agents with emergent collaboration")
        print("2. A2A Mode: Agent-to-Agent communication with deployed AgentCore agents")
        print("\nUse the environment setup script to switch between modes.")
        return 0
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
        return 1


if __name__ == "__main__":
    exit(main())
#!/usr/bin/env python3
"""
Script to check strands-agents-tools versions and find use_aws
"""

import subprocess
import sys

def run_command(cmd):
    """Run a command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def check_current_version():
    """Check current installed version"""
    try:
        import strands_agents_tools
        version = getattr(strands_agents_tools, '__version__', 'Unknown')
        print(f"Current strands-agents-tools version: {version}")
        
        # Check if use_aws is available
        try:
            from strands_tools import use_aws
            print("✓ use_aws found in strands_tools")
            return True
        except ImportError:
            try:
                from strands_agents_tools import use_aws
                print("✓ use_aws found in strands_agents_tools")
                return True
            except ImportError:
                print("✗ use_aws not found in current version")
                return False
    except ImportError:
        print("strands-agents-tools not installed")
        return False

def try_install_version(version):
    """Try to install a specific version"""
    print(f"\nTrying to install strands-agents-tools=={version}")
    stdout, stderr, code = run_command(f"pip install strands-agents-tools=={version}")
    
    if code == 0:
        print(f"✓ Successfully installed version {version}")
        return check_current_version()
    else:
        print(f"✗ Failed to install version {version}")
        print(f"Error: {stderr}")
        return False

def main():
    print("Checking strands-agents-tools for use_aws availability...\n")
    
    # Check current version first
    if check_current_version():
        print("use_aws is available in current version!")
        return
    
    # Try different versions that might have use_aws
    versions_to_try = [
        "0.2.0",
        "0.1.9", 
        "0.1.8",
        "0.1.7",
        "0.1.6",
        "0.1.5",
        "0.1.4",
        "0.1.3",
        "0.1.2",
        "0.1.1",
        "0.1.0"
    ]
    
    for version in versions_to_try:
        if try_install_version(version):
            print(f"\n🎉 Found use_aws in version {version}!")
            break
    else:
        print("\n❌ Could not find use_aws in any tested version")
        print("Recommendation: Use custom AWS tool implementation")

if __name__ == "__main__":
    main()
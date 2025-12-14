#!/usr/bin/env python3
"""
Script to find which version of strands-agents-tools has use_aws
"""

import subprocess
import sys
import json

def run_pip_command(cmd):
    """Run pip command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Timeout", 1
    except Exception as e:
        return "", str(e), 1

def test_use_aws_import():
    """Test if use_aws can be imported"""
    try:
        # Try different import paths
        import_paths = [
            "from strands_tools import use_aws",
            "from strands.tools import use_aws", 
            "from strands_agents_tools import use_aws",
            "from strands_agents_tools.use_aws import use_aws"
        ]
        
        for import_path in import_paths:
            try:
                exec(import_path)
                return True, import_path
            except ImportError:
                continue
        
        return False, "No valid import path found"
    except Exception as e:
        return False, str(e)

def try_version(version):
    """Try installing and testing a specific version"""
    print(f"\n🔍 Testing strands-agents-tools=={version}")
    
    # Install the version
    stdout, stderr, code = run_pip_command(f"pip install strands-agents-tools=={version} --quiet")
    
    if code != 0:
        print(f"   ❌ Failed to install: {stderr.strip()}")
        return False
    
    print(f"   ✅ Installed successfully")
    
    # Test import
    success, result = test_use_aws_import()
    if success:
        print(f"   🎉 use_aws found! Import: {result}")
        return True
    else:
        print(f"   ❌ use_aws not found: {result}")
        return False

def main():
    print("🔎 Searching for strands-agents-tools version with use_aws...")
    
    # Test current version first
    print("\n📋 Testing current installation:")
    success, result = test_use_aws_import()
    if success:
        print(f"✅ use_aws already available! Import: {result}")
        return
    
    # List of versions to try (starting from newer ones)
    versions_to_try = [
        "1.0.0", "0.9.0", "0.8.0", "0.7.0", "0.6.0", "0.5.0",
        "0.4.0", "0.3.0", "0.2.9", "0.2.8", "0.2.7", "0.2.6", 
        "0.2.5", "0.2.4", "0.2.3", "0.2.2", "0.2.1", "0.2.0",
        "0.1.9", "0.1.8", "0.1.7", "0.1.6", "0.1.5", "0.1.4",
        "0.1.3", "0.1.2", "0.1.1", "0.1.0"
    ]
    
    found_version = None
    for version in versions_to_try:
        if try_version(version):
            found_version = version
            break
    
    if found_version:
        print(f"\n🎉 SUCCESS! use_aws found in version {found_version}")
        print(f"\nTo use this version, update your requirements.txt:")
        print(f"strands-agents-tools=={found_version}")
    else:
        print(f"\n❌ use_aws not found in any tested version")
        print(f"\n💡 Recommendation: Use custom AWS tool implementation")
        print(f"   The current Strands SDK supports custom tools with @tool decorator")

if __name__ == "__main__":
    main()
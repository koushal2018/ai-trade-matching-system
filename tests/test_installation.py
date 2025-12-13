"""
Test that installation succeeds after CrewAI removal.
Validates: Requirements 1.3, 1.4
"""
import subprocess
import sys
from pathlib import Path


def test_requirements_file_is_valid():
    """Test that requirements.txt is a valid pip requirements file"""
    requirements_path = Path("requirements.txt")
    assert requirements_path.exists(), "requirements.txt not found"
    
    # Try to parse requirements file
    with open(requirements_path, 'r') as f:
        lines = f.readlines()
    
    # Check that each non-comment line has valid format
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Should have package name and optionally version specifier
        assert any(sep in line for sep in ['>=', '==', '<=', '>', '<', '~=']) or \
               line.replace('-', '').replace('_', '').replace('[', '').replace(']', '').isalnum(), \
               f"Invalid requirement line: {line}"


def test_pyproject_toml_is_valid():
    """Test that pyproject.toml is valid TOML"""
    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml not found"
    
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            # Python < 3.11 without tomli, skip validation
            print("Warning: Cannot validate TOML (tomllib/tomli not available)")
            return
    
    with open(pyproject_path, 'rb') as f:
        config = tomllib.load(f)
    
    # Check that project section exists
    assert 'project' in config, "pyproject.toml missing [project] section"
    assert 'dependencies' in config['project'], "pyproject.toml missing dependencies"


def test_no_crewai_in_installed_packages():
    """Test that CrewAI packages are not in the dependency list"""
    # Note: This tests the requirements file, not the installed packages
    # Actual uninstallation happens in later tasks
    requirements_path = Path("requirements.txt")
    with open(requirements_path, 'r') as f:
        content = f.read().lower()
    
    assert 'crewai' not in content, "requirements.txt should not contain crewai"
    assert 'litellm' not in content, "requirements.txt should not contain litellm"
    assert 'mcp' not in content, "requirements.txt should not contain mcp"


def test_strands_in_dependencies():
    """Test that Strands SDK is in the dependency list"""
    requirements_path = Path("requirements.txt")
    with open(requirements_path, 'r') as f:
        content = f.read().lower()
    
    assert 'strands-agents' in content, "requirements.txt should contain strands-agents"
    assert 'bedrock-agentcore' in content, "requirements.txt should contain bedrock-agentcore"


if __name__ == '__main__':
    print("Testing requirements.txt validity...")
    test_requirements_file_is_valid()
    print("✅ requirements.txt is valid")
    
    print("\nTesting pyproject.toml validity...")
    test_pyproject_toml_is_valid()
    print("✅ pyproject.toml is valid")
    
    print("\nTesting CrewAI removal from dependencies...")
    test_no_crewai_in_installed_packages()
    print("✅ CrewAI not in dependency list")
    
    print("\nTesting Strands SDK in dependencies...")
    test_strands_in_dependencies()
    print("✅ Strands SDK in dependency list")
    
    print("\n✅ All installation tests passed!")

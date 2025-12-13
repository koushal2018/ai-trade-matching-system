"""
Unit tests for CrewAI dependency removal.
Validates: Requirements 1.1, 1.2
"""
import re
from pathlib import Path


def test_requirements_txt_no_crewai():
    """Test that requirements.txt doesn't contain crewai or crewai-tools"""
    requirements_path = Path("requirements.txt")
    assert requirements_path.exists(), "requirements.txt not found"
    
    content = requirements_path.read_text()
    
    # Check for crewai packages (case-insensitive)
    assert not re.search(r'crewai', content, re.IGNORECASE), \
        "requirements.txt should not contain 'crewai'"
    
    # Check for litellm (CrewAI dependency)
    assert 'litellm' not in content.lower(), \
        "requirements.txt should not contain 'litellm'"
    
    # Check for mcp (CrewAI tool dependency)
    assert 'mcp' not in content.lower(), \
        "requirements.txt should not contain 'mcp'"
    
    # Check for pdf2image (only used by CrewAI tools)
    assert 'pdf2image' not in content.lower(), \
        "requirements.txt should not contain 'pdf2image'"
    
    # Check for Pillow (only used for PDF-to-image conversion)
    assert 'pillow' not in content.lower(), \
        "requirements.txt should not contain 'Pillow'"


def test_pyproject_toml_no_crewai():
    """Test that pyproject.toml doesn't contain crewai dependencies"""
    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml not found"
    
    content = pyproject_path.read_text()
    
    # Check for crewai packages (case-insensitive)
    assert not re.search(r'crewai', content, re.IGNORECASE), \
        "pyproject.toml should not contain 'crewai'"
    
    # Check for litellm
    assert 'litellm' not in content.lower(), \
        "pyproject.toml should not contain 'litellm'"
    
    # Check for mcp
    assert 'mcp' not in content.lower(), \
        "pyproject.toml should not contain 'mcp'"
    
    # Check for pdf2image
    assert 'pdf2image' not in content.lower(), \
        "pyproject.toml should not contain 'pdf2image'"
    
    # Check for Pillow
    assert 'pillow' not in content.lower(), \
        "pyproject.toml should not contain 'pillow'"


def test_pyproject_toml_no_crewai_scripts():
    """Test that pyproject.toml doesn't contain CrewAI-specific scripts"""
    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml not found"
    
    content = pyproject_path.read_text()
    
    # Check for CrewAI tool section
    assert '[tool.crewai]' not in content, \
        "pyproject.toml should not contain [tool.crewai] section"
    
    # Check for CrewAI-specific scripts
    assert 'run_crew' not in content, \
        "pyproject.toml should not contain 'run_crew' script"


def test_pyproject_toml_description_updated():
    """Test that pyproject.toml description reflects Strands implementation"""
    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml not found"
    
    content = pyproject_path.read_text()
    
    # Description should not mention CrewAI
    assert not re.search(r'crewai', content, re.IGNORECASE), \
        "pyproject.toml description should not mention CrewAI"
    
    # Description should mention Strands or AgentCore
    assert 'strands' in content.lower() or 'agentcore' in content.lower(), \
        "pyproject.toml description should mention Strands or AgentCore"


def test_requirements_has_strands():
    """Test that requirements.txt contains Strands SDK dependencies"""
    requirements_path = Path("requirements.txt")
    assert requirements_path.exists(), "requirements.txt not found"
    
    content = requirements_path.read_text()
    
    # Should have strands-agents
    assert 'strands-agents' in content.lower(), \
        "requirements.txt should contain 'strands-agents'"
    
    # Should have bedrock-agentcore
    assert 'bedrock-agentcore' in content.lower(), \
        "requirements.txt should contain 'bedrock-agentcore'"


def test_pyproject_has_strands():
    """Test that pyproject.toml contains Strands SDK dependencies"""
    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml not found"
    
    content = pyproject_path.read_text()
    
    # Should have strands-agents
    assert 'strands-agents' in content.lower(), \
        "pyproject.toml should contain 'strands-agents'"
    
    # Should have bedrock-agentcore
    assert 'bedrock-agentcore' in content.lower(), \
        "pyproject.toml should contain 'bedrock-agentcore'"

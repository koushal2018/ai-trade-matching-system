"""
Unit tests for eks_main.py cleanup verification.
Validates that all CrewAI-related code has been removed.

Requirements: 3.1, 3.2, 3.3, 3.5
"""

import pytest
from pathlib import Path


def test_eks_main_no_crew_fixed_import():
    """
    Test that eks_main.py doesn't import crew_fixed.
    Requirements: 3.1
    """
    eks_main_path = Path("src/latest_trade_matching_agent/eks_main.py")
    assert eks_main_path.exists(), "eks_main.py should exist"
    
    content = eks_main_path.read_text()
    
    # Check for crew_fixed imports
    assert "from .crew_fixed import" not in content, "Should not import from crew_fixed"
    assert "import crew_fixed" not in content, "Should not import crew_fixed"
    assert "LatestTradeMatchingAgent" not in content, "Should not reference LatestTradeMatchingAgent"


def test_eks_main_no_crewai_tools_import():
    """
    Test that eks_main.py doesn't import crewai_tools.
    Requirements: 3.2
    """
    eks_main_path = Path("src/latest_trade_matching_agent/eks_main.py")
    assert eks_main_path.exists(), "eks_main.py should exist"
    
    content = eks_main_path.read_text()
    
    # Check for crewai_tools imports
    assert "from crewai_tools import" not in content, "Should not import from crewai_tools"
    assert "import crewai_tools" not in content, "Should not import crewai_tools"
    assert "MCPServerAdapter" not in content, "Should not reference MCPServerAdapter"


def test_eks_main_no_mcp_import():
    """
    Test that eks_main.py doesn't import mcp.
    Requirements: 3.2
    """
    eks_main_path = Path("src/latest_trade_matching_agent/eks_main.py")
    assert eks_main_path.exists(), "eks_main.py should exist"
    
    content = eks_main_path.read_text()
    
    # Check for mcp imports
    assert "from mcp import" not in content, "Should not import from mcp"
    assert "import mcp" not in content, "Should not import mcp"
    assert "StdioServerParameters" not in content, "Should not reference StdioServerParameters"


def test_eks_main_no_crewai_available_flag():
    """
    Test that eks_main.py doesn't contain CREWAI_AVAILABLE flag.
    Requirements: 3.3
    """
    eks_main_path = Path("src/latest_trade_matching_agent/eks_main.py")
    assert eks_main_path.exists(), "eks_main.py should exist"
    
    content = eks_main_path.read_text()
    
    # Check for CREWAI_AVAILABLE flag
    assert "CREWAI_AVAILABLE" not in content, "Should not contain CREWAI_AVAILABLE flag"


def test_eks_main_no_simulation_mode():
    """
    Test that eks_main.py doesn't contain simulation mode logic.
    Requirements: 3.5
    """
    eks_main_path = Path("src/latest_trade_matching_agent/eks_main.py")
    assert eks_main_path.exists(), "eks_main.py should exist"
    
    content = eks_main_path.read_text()
    
    # Check for simulation mode references
    assert "simulation mode" not in content.lower(), "Should not contain simulation mode logic"
    assert "Simulated processing" not in content, "Should not contain simulated processing"


def test_eks_main_no_mcp_dynamodb_setup():
    """
    Test that eks_main.py doesn't contain MCP DynamoDB server setup.
    Requirements: 3.4
    """
    eks_main_path = Path("src/latest_trade_matching_agent/eks_main.py")
    assert eks_main_path.exists(), "eks_main.py should exist"
    
    content = eks_main_path.read_text()
    
    # Check for MCP DynamoDB setup
    assert "dynamodb_params" not in content, "Should not contain dynamodb_params"
    assert "awslabs.dynamodb-mcp-server" not in content, "Should not reference MCP DynamoDB server"
    assert "DDB_MCP_READONLY" not in content, "Should not contain DDB_MCP_READONLY"


def test_eks_main_no_process_document_async():
    """
    Test that eks_main.py doesn't contain process_document_async function.
    Requirements: 3.4
    """
    eks_main_path = Path("src/latest_trade_matching_agent/eks_main.py")
    assert eks_main_path.exists(), "eks_main.py should exist"
    
    content = eks_main_path.read_text()
    
    # Check for process_document_async function
    assert "async def process_document_async" not in content, "Should not contain process_document_async function"
    assert "def process_document_async" not in content, "Should not contain process_document_async function"


def test_eks_main_no_processing_endpoint():
    """
    Test that eks_main.py doesn't contain /process endpoint.
    Requirements: 3.4
    """
    eks_main_path = Path("src/latest_trade_matching_agent/eks_main.py")
    assert eks_main_path.exists(), "eks_main.py should exist"
    
    content = eks_main_path.read_text()
    
    # Check for /process endpoint
    assert '@app.post("/process"' not in content, "Should not contain /process endpoint"
    assert "process_trade_document" not in content, "Should not contain process_trade_document function"


def test_eks_main_has_health_endpoint():
    """
    Test that eks_main.py still has health check endpoint.
    Requirements: 3.4 (verify simplified functionality)
    """
    eks_main_path = Path("src/latest_trade_matching_agent/eks_main.py")
    assert eks_main_path.exists(), "eks_main.py should exist"
    
    content = eks_main_path.read_text()
    
    # Check for health endpoint
    assert '@app.get("/health"' in content, "Should contain /health endpoint"
    assert "health_check" in content, "Should contain health_check function"


def test_eks_main_has_readiness_endpoint():
    """
    Test that eks_main.py still has readiness check endpoint.
    Requirements: 3.4 (verify simplified functionality)
    """
    eks_main_path = Path("src/latest_trade_matching_agent/eks_main.py")
    assert eks_main_path.exists(), "eks_main.py should exist"
    
    content = eks_main_path.read_text()
    
    # Check for readiness endpoint
    assert '@app.get("/ready"' in content, "Should contain /ready endpoint"
    assert "readiness_check" in content, "Should contain readiness_check function"


def test_eks_main_has_strands_reference():
    """
    Test that eks_main.py references Strands Swarm for processing.
    Requirements: 3.4 (verify documentation)
    """
    eks_main_path = Path("src/latest_trade_matching_agent/eks_main.py")
    assert eks_main_path.exists(), "eks_main.py should exist"
    
    content = eks_main_path.read_text()
    
    # Check for Strands reference
    assert "Strands Swarm" in content or "deployment/swarm" in content, \
        "Should reference Strands Swarm implementation"

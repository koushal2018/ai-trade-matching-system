"""
Test that APIs start successfully after CrewAI removal.
Requirements: 8.4
"""

import pytest
import sys
from pathlib import Path


def test_eks_main_api_imports_successfully():
    """
    Test that eks_main.py API imports without errors.
    This verifies that all CrewAI dependencies have been properly removed.
    Requirements: 8.4
    """
    # Add src to path
    src_path = Path("src")
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    # Try to import the app - this will fail if there are import errors
    try:
        from latest_trade_matching_agent.eks_main import app
        assert app is not None, "App should be initialized"
        assert app.title == "Trade Matching System Health API", "App should have correct title"
    except ImportError as e:
        pytest.fail(f"Failed to import eks_main.py: {e}")


def test_eks_main_has_health_endpoint():
    """
    Test that eks_main.py has health endpoint configured.
    Requirements: 8.4
    """
    # Add src to path
    src_path = Path("src")
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    from latest_trade_matching_agent.eks_main import app
    
    # Check that health endpoint exists
    routes = [route.path for route in app.routes]
    assert "/health" in routes, "Should have /health endpoint"
    assert "/ready" in routes, "Should have /ready endpoint"


def test_eks_main_no_processing_endpoint():
    """
    Test that eks_main.py doesn't have processing endpoint.
    Requirements: 8.4
    """
    # Add src to path
    src_path = Path("src")
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    from latest_trade_matching_agent.eks_main import app
    
    # Check that processing endpoint doesn't exist
    routes = [route.path for route in app.routes]
    assert "/process" not in routes, "Should not have /process endpoint"
    assert "/status" not in routes, "Should not have /status endpoint"
    assert "/metrics" not in routes, "Should not have /metrics endpoint"

"""
Basic tests for AI Trade Matching System
"""
import pytest
import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

class TestBasicSetup:
    """Test basic system setup and configuration"""
    
    def test_project_structure(self):
        """Test that required directories exist"""
        required_dirs = [
            'src/latest_trade_matching_agent',
            'data/BANK',
            'data/COUNTERPARTY',
            'storage'
        ]
        
        for directory in required_dirs:
            assert os.path.exists(directory), f"Required directory missing: {directory}"
    
    def test_sample_pdfs_exist(self):
        """Test that sample PDFs are present"""
        sample_pdfs = [
            'data/BANK/FAB_26933659.pdf',
            'data/COUNTERPARTY/GCS381315_V1.pdf'
        ]
        
        for pdf in sample_pdfs:
            assert os.path.exists(pdf), f"Sample PDF missing: {pdf}"
            assert os.path.getsize(pdf) > 1000, f"Sample PDF too small: {pdf}"
    
    def test_config_files_exist(self):
        """Test that configuration files exist"""
        config_files = [
            'src/latest_trade_matching_agent/config/agents.yaml',
            'src/latest_trade_matching_agent/config/tasks.yaml'
        ]
        
        for config in config_files:
            assert os.path.exists(config), f"Config file missing: {config}"
    
    def test_main_files_exist(self):
        """Test that main application files exist"""
        main_files = [
            'src/latest_trade_matching_agent/crew_fixed.py',
            'src/latest_trade_matching_agent/main.py',
            'src/latest_trade_matching_agent/tools/trade_tools.py'
        ]
        
        for file in main_files:
            assert os.path.exists(file), f"Main file missing: {file}"

class TestEnvironment:
    """Test environment configuration"""
    
    def test_env_example_exists(self):
        """Test that .env.example exists"""
        assert os.path.exists('.env.example'), ".env.example file missing"
    
    def test_env_example_has_required_keys(self):
        """Test that .env.example has required configuration"""
        with open('.env.example', 'r') as f:
            content = f.read()
        
        required_keys = [
            'OPENAI_API_KEY',
            'AWS_ACCESS_KEY_ID',
            'ANTHROPIC_API_KEY'
        ]
        
        for key in required_keys:
            assert key in content, f"Required key missing from .env.example: {key}"

class TestImports:
    """Test that main modules can be imported"""
    
    def test_import_crew(self):
        """Test that main crew can be imported"""
        try:
            from latest_trade_matching_agent.crew_fixed import LatestTradeMatchingAgent
            assert LatestTradeMatchingAgent is not None
        except ImportError as e:
            pytest.skip(f"Cannot import crew (missing dependencies): {e}")
    
    def test_import_tools(self):
        """Test that trade tools can be imported"""
        try:
            from latest_trade_matching_agent.tools.trade_tools import TradeStorageTool, PDFExtractorTool
            assert TradeStorageTool is not None
            assert PDFExtractorTool is not None
        except ImportError as e:
            pytest.skip(f"Cannot import tools (missing dependencies): {e}")

if __name__ == "__main__":
    pytest.main([__file__])
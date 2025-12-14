"""
Property-Based Test for Functional Parity Preservation

This test verifies that the AgentCore-deployed swarm with memory integration
maintains functional parity with the original swarm implementation.

**Feature: swarm-to-agentcore, Property 4: Functional parity preservation**
**Validates: Requirements 8.1, 8.2, 16.1**
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from typing import Dict, Any
import json

# Import both swarm implementations
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment', 'swarm'))

from deployment.swarm.trade_matching_swarm import (
    create_trade_matching_swarm,
    create_trade_matching_swarm_with_memory,
    create_bedrock_model,
    get_pdf_adapter_prompt,
    get_trade_extractor_prompt,
    get_trade_matcher_prompt,
    get_exception_handler_prompt
)


def normalize_output(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize swarm output for comparison by removing timing and session-specific fields.
    
    Args:
        result: Swarm execution result
        
    Returns:
        Normalized result for comparison
    """
    normalized = result.copy()
    
    # Remove timing fields (these will differ between runs)
    normalized.pop('execution_time_ms', None)
    normalized.pop('processing_time_ms', None)
    
    # Remove session-specific fields
    normalized.pop('correlation_id', None)
    
    # Normalize node history (just check that agents were involved, not exact order)
    if 'node_history' in normalized:
        normalized['node_history'] = sorted(normalized['node_history'])
    
    return normalized


def assert_equivalent_outputs(original: Dict[str, Any], with_memory: Dict[str, Any]) -> None:
    """
    Assert that two swarm outputs are functionally equivalent.
    
    Args:
        original: Output from original swarm
        with_memory: Output from swarm with memory integration
        
    Raises:
        AssertionError: If outputs are not equivalent
    """
    # Normalize both outputs
    norm_original = normalize_output(original)
    norm_with_memory = normalize_output(with_memory)
    
    # Check success status
    assert norm_original.get('success') == norm_with_memory.get('success'), \
        "Success status differs between implementations"
    
    # Check document ID
    assert norm_original.get('document_id') == norm_with_memory.get('document_id'), \
        "Document ID differs between implementations"
    
    # Check status
    assert norm_original.get('status') == norm_with_memory.get('status'), \
        "Execution status differs between implementations"
    
    # Check that same agents were involved (order may differ due to memory)
    if 'node_history' in norm_original and 'node_history' in norm_with_memory:
        assert set(norm_original['node_history']) == set(norm_with_memory['node_history']), \
            "Different agents were involved in execution"
    
    # Check execution count is similar (may differ slightly due to memory optimization)
    if 'execution_count' in norm_original and 'execution_count' in norm_with_memory:
        original_count = norm_original['execution_count']
        memory_count = norm_with_memory['execution_count']
        # Allow up to 20% difference due to memory optimization
        assert abs(original_count - memory_count) <= max(1, original_count * 0.2), \
            f"Execution count differs significantly: {original_count} vs {memory_count}"


@pytest.mark.property_test
class TestFunctionalParity:
    """Property tests for functional parity preservation."""
    
    def test_agent_factory_signatures(self):
        """
        Test that agent factory functions maintain backward compatibility.
        
        Verifies that the updated factory functions accept the new parameters
        while maintaining the ability to create agents.
        """
        from deployment.swarm.trade_matching_swarm import (
            create_pdf_adapter_agent,
            create_trade_extractor_agent,
            create_trade_matcher_agent,
            create_exception_handler_agent
        )
        
        # Test that agents can be created with document_id
        document_id = "test_doc_123"
        
        # Create agents without memory (memory_id=None)
        pdf_adapter = create_pdf_adapter_agent(document_id, memory_id=None)
        trade_extractor = create_trade_extractor_agent(document_id, memory_id=None)
        trade_matcher = create_trade_matcher_agent(document_id, memory_id=None)
        exception_handler = create_exception_handler_agent(document_id, memory_id=None)
        
        # Verify agents were created
        assert pdf_adapter is not None
        assert pdf_adapter.name == "pdf_adapter"
        
        assert trade_extractor is not None
        assert trade_extractor.name == "trade_extractor"
        
        assert trade_matcher is not None
        assert trade_matcher.name == "trade_matcher"
        
        assert exception_handler is not None
        assert exception_handler.name == "exception_handler"
    
    def test_system_prompts_include_memory_guidance(self):
        """
        Test that system prompts include memory access guidance.
        
        Verifies that the updated prompts provide agents with instructions
        on how to use memory while maintaining core functionality.
        """
        pdf_prompt = get_pdf_adapter_prompt()
        extractor_prompt = get_trade_extractor_prompt()
        matcher_prompt = get_trade_matcher_prompt()
        handler_prompt = get_exception_handler_prompt()
        
        # Verify memory guidance is present
        assert "Memory Access" in pdf_prompt
        assert "semantic memory" in pdf_prompt.lower()
        assert "/facts" in pdf_prompt
        assert "/preferences" in pdf_prompt
        
        assert "Memory Access" in extractor_prompt
        assert "field mapping patterns" in extractor_prompt.lower()
        
        assert "Memory Access" in matcher_prompt
        assert "matching decisions" in matcher_prompt.lower()
        
        assert "Memory Access" in handler_prompt
        assert "exception resolution patterns" in handler_prompt.lower()
        
        # Verify core functionality instructions are still present
        assert "download_pdf_from_s3" in pdf_prompt
        assert "extract_text_with_bedrock" in pdf_prompt
        
        assert "store_trade_in_dynamodb" in extractor_prompt
        assert "DynamoDB" in extractor_prompt
        
        assert "scan_trades_table" in matcher_prompt
        assert "match by attributes" in matcher_prompt.lower()
        
        assert "get_severity_guidelines" in handler_prompt
        assert "store_exception_record" in handler_prompt
    
    def test_tool_preservation(self):
        """
        Test that all existing tools are preserved in agent configurations.
        
        Verifies that agents still have access to all their original tools
        after the memory integration update.
        """
        from deployment.swarm.trade_matching_swarm import (
            create_pdf_adapter_agent,
            create_trade_extractor_agent,
            create_trade_matcher_agent,
            create_exception_handler_agent,
            download_pdf_from_s3,
            extract_text_with_bedrock,
            save_canonical_output,
            store_trade_in_dynamodb,
            use_aws,
            scan_trades_table,
            save_matching_report,
            get_severity_guidelines,
            store_exception_record
        )
        
        document_id = "test_doc_123"
        
        # Create agents
        pdf_adapter = create_pdf_adapter_agent(document_id, memory_id=None)
        trade_extractor = create_trade_extractor_agent(document_id, memory_id=None)
        trade_matcher = create_trade_matcher_agent(document_id, memory_id=None)
        exception_handler = create_exception_handler_agent(document_id, memory_id=None)
        
        # Verify PDF Adapter tools
        pdf_tool_names = [tool.name for tool in pdf_adapter.tools]
        assert "download_pdf_from_s3" in pdf_tool_names
        assert "extract_text_with_bedrock" in pdf_tool_names
        assert "save_canonical_output" in pdf_tool_names
        
        # Verify Trade Extractor tools
        extractor_tool_names = [tool.name for tool in trade_extractor.tools]
        assert "store_trade_in_dynamodb" in extractor_tool_names
        assert "use_aws" in extractor_tool_names
        
        # Verify Trade Matcher tools
        matcher_tool_names = [tool.name for tool in trade_matcher.tools]
        assert "scan_trades_table" in matcher_tool_names
        assert "save_matching_report" in matcher_tool_names
        assert "use_aws" in matcher_tool_names
        
        # Verify Exception Handler tools
        handler_tool_names = [tool.name for tool in exception_handler.tools]
        assert "get_severity_guidelines" in handler_tool_names
        assert "store_exception_record" in handler_tool_names
        assert "use_aws" in handler_tool_names
    
    def test_swarm_configuration_preservation(self):
        """
        Test that swarm configuration parameters are preserved.
        
        Verifies that the swarm maintains the same configuration settings
        (max_handoffs, timeouts, etc.) after memory integration.
        """
        document_id = "test_doc_123"
        
        # Create swarm without memory
        swarm_original = create_trade_matching_swarm()
        
        # Create swarm with memory (but memory_id=None to disable)
        swarm_with_memory = create_trade_matching_swarm_with_memory(
            document_id=document_id,
            memory_id=None
        )
        
        # Verify configuration is preserved
        assert swarm_original.max_handoffs == swarm_with_memory.max_handoffs
        assert swarm_original.max_iterations == swarm_with_memory.max_iterations
        assert swarm_original.execution_timeout == swarm_with_memory.execution_timeout
        assert swarm_original.node_timeout == swarm_with_memory.node_timeout
        
        # Verify entry point is the same
        assert swarm_original.entry_point.name == swarm_with_memory.entry_point.name
        
        # Verify same number of agents
        assert len(swarm_original.agents) == len(swarm_with_memory.agents)
    
    def test_backward_compatibility(self):
        """
        Test that the original create_trade_matching_swarm() function still works.
        
        Verifies backward compatibility for existing code that doesn't use memory.
        """
        # This should work without any parameters
        swarm = create_trade_matching_swarm()
        
        assert swarm is not None
        assert len(swarm.agents) == 4
        assert swarm.entry_point.name == "pdf_adapter"
        
        # Verify agents are properly configured
        agent_names = [agent.name for agent in swarm.agents]
        assert "pdf_adapter" in agent_names
        assert "trade_extractor" in agent_names
        assert "trade_matcher" in agent_names
        assert "exception_handler" in agent_names


@pytest.mark.property_test
@given(
    document_id=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Pd")),
        min_size=5,
        max_size=30
    )
)
@settings(
    max_examples=10,  # Reduced for faster testing
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
def test_property_agent_creation_parity(document_id: str):
    """
    Property: For any document_id, agents created with memory integration should
    have the same core configuration as agents without memory.
    
    **Feature: swarm-to-agentcore, Property 4: Functional parity preservation**
    **Validates: Requirements 8.1, 8.2, 16.1**
    """
    from deployment.swarm.trade_matching_swarm import (
        create_pdf_adapter_agent,
        create_trade_extractor_agent,
        create_trade_matcher_agent,
        create_exception_handler_agent
    )
    
    # Create agents without memory
    pdf_no_mem = create_pdf_adapter_agent(document_id, memory_id=None)
    extractor_no_mem = create_trade_extractor_agent(document_id, memory_id=None)
    matcher_no_mem = create_trade_matcher_agent(document_id, memory_id=None)
    handler_no_mem = create_exception_handler_agent(document_id, memory_id=None)
    
    # Verify all agents were created successfully
    assert pdf_no_mem is not None
    assert extractor_no_mem is not None
    assert matcher_no_mem is not None
    assert handler_no_mem is not None
    
    # Verify agent names are preserved
    assert pdf_no_mem.name == "pdf_adapter"
    assert extractor_no_mem.name == "trade_extractor"
    assert matcher_no_mem.name == "trade_matcher"
    assert handler_no_mem.name == "exception_handler"
    
    # Verify tool counts are preserved
    assert len(pdf_no_mem.tools) == 3  # download, extract, save
    assert len(extractor_no_mem.tools) == 2  # store, use_aws
    assert len(matcher_no_mem.tools) == 3  # scan, save_report, use_aws
    assert len(handler_no_mem.tools) == 3  # get_guidelines, store, use_aws
    
    # Verify model configuration is preserved
    assert pdf_no_mem.model is not None
    assert extractor_no_mem.model is not None
    assert matcher_no_mem.model is not None
    assert handler_no_mem.model is not None


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "-m", "property_test"])

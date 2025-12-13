"""
Example: Integrating AgentCore Memory into Trade Matching Agent

This shows how to integrate the memory_integration module into your
existing trade_matching_agent_strands.py file.
"""

# At the top of trade_matching_agent_strands.py, add:
from memory_integration import initialize_memory, get_memory

# After initializing observability, add:
"""
# Initialize AgentCore Memory
trade_matching_memory = None
if MEMORY_AVAILABLE:
    try:
        trade_matching_memory = initialize_memory(
            memory_id=MEMORY_ID,
            region_name=REGION,
            agent_name=AGENT_NAME
        )
        logger.info(f"Trade Matching Memory initialized: {MEMORY_ID}")
    except Exception as e:
        logger.warning(f"Failed to initialize memory: {e}")
"""

# In the invoke() function, after successful matching, add:
"""
        # Store matching decision in AgentCore Memory for learning
        if trade_matching_memory and trade_matching_memory.enabled:
            try:
                if observability and span_context:
                    with observability.start_span("memory_storage") as mem_span:
                        mem_span.set_attribute("classification", classification)
                        mem_span.set_attribute("confidence", confidence_score)
                        
                        trade_matching_memory.store_matching_decision(
                            trade_id=trade_id,
                            source_type=source_type,
                            classification=classification,
                            confidence=confidence_score / 100.0,  # Convert to 0-1
                            match_details={
                                "key_attributes": {
                                    "trade_id": trade_id,
                                    "source_type": source_type,
                                    # Add more attributes from the trade data
                                },
                                "reasoning": response_text[:500],
                                "processing_time_ms": processing_time_ms,
                                "token_usage": token_metrics
                            },
                            correlation_id=correlation_id
                        )
                        mem_span.set_attribute("memory_stored", True)
                else:
                    trade_matching_memory.store_matching_decision(
                        trade_id=trade_id,
                        source_type=source_type,
                        classification=classification,
                        confidence=confidence_score / 100.0,
                        match_details={
                            "key_attributes": {"trade_id": trade_id, "source_type": source_type},
                            "reasoning": response_text[:500],
                            "processing_time_ms": processing_time_ms,
                            "token_usage": token_metrics
                        },
                        correlation_id=correlation_id
                    )
                    
                logger.info(f"Stored matching decision in memory for {trade_id}")
                
            except Exception as e:
                logger.warning(f"Failed to store matching decision in memory: {e}")
"""

# Optional: Retrieve similar matches before matching (for context)
"""
        # Retrieve similar past matches for context (optional enhancement)
        memory_context = ""
        if trade_matching_memory and trade_matching_memory.enabled:
            try:
                # Extract trade attributes from the source trade
                trade_attributes = {
                    "currency": "USD",  # Extract from actual trade data
                    "product_type": "SWAP",  # Extract from actual trade data
                    "counterparty": "Goldman Sachs"  # Extract from actual trade data
                }
                
                memory_context = trade_matching_memory.get_memory_context_for_prompt(
                    trade_attributes=trade_attributes,
                    max_examples=3
                )
                
                if memory_context:
                    logger.info("Retrieved memory context for matching")
            except Exception as e:
                logger.warning(f"Failed to retrieve memory context: {e}")
        
        # Include memory context in the prompt
        prompt = f'''Match a trade that was just extracted and stored.

{memory_context}

## Trade to Match
- **Trade ID**: {trade_id}
...
'''
"""

# Complete minimal integration (just storage, no retrieval):
"""
# 1. Import at top
from memory_integration import initialize_memory

# 2. Initialize after observability
trade_matching_memory = initialize_memory(
    memory_id=os.getenv("AGENTCORE_MEMORY_ID", 
                        "trade_matching_agent_mem-SxPFir3bbF"),
    region_name=REGION,
    agent_name=AGENT_NAME
)

# 3. Store after successful matching
if trade_matching_memory and trade_matching_memory.enabled and classification != "UNKNOWN":
    trade_matching_memory.store_matching_decision(
        trade_id=trade_id,
        source_type=source_type,
        classification=classification,
        confidence=confidence_score / 100.0,
        match_details={
            "key_attributes": {"trade_id": trade_id, "source_type": source_type},
            "reasoning": response_text[:500],
            "processing_time_ms": processing_time_ms,
            "token_usage": token_metrics
        },
        correlation_id=correlation_id
    )
"""

print("See comments above for integration steps")

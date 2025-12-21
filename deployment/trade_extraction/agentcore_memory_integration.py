"""
AgentCore Memory Integration for Trade Extraction Agent

This enables the agent to:
- Learn from successful extraction patterns
- Store and retrieve similar trade contexts
- Improve extraction accuracy over time
- Track processing history for audit and optimization
"""

from bedrock_agentcore import Memory
import json
from typing import Dict, Any, List
from datetime import datetime

class TradeExtractionMemoryManager:
    """Manages memory operations for trade extraction patterns and history."""
    
    def __init__(self):
        # Initialize memory resources
        self.trade_patterns_memory = Memory(
            resource_name="trade-matching-system-trade-patterns-production"
        )
        self.processing_history_memory = Memory(
            resource_name="trade-matching-system-processing-history-production"
        )
    
    def store_successful_extraction_pattern(self, 
                                          trade_data: Dict[str, Any],
                                          extraction_context: Dict[str, Any]) -> bool:
        """
        Store successful extraction patterns for future reference.
        
        Args:
            trade_data: The successfully extracted trade data
            extraction_context: Context about the extraction (confidence, field mappings, etc.)
        """
        try:
            pattern_data = {
                "trade_id": trade_data.get("trade_id"),
                "counterparty": trade_data.get("counterparty"),
                "product_type": trade_data.get("product_type"),
                "source_type": trade_data.get("TRADE_SOURCE"),
                "extraction_confidence": extraction_context.get("confidence", 0.0),
                "field_mappings": extraction_context.get("field_mappings", {}),
                "extraction_tips": extraction_context.get("tips", ""),
                "document_structure": extraction_context.get("structure", ""),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store in semantic memory for pattern matching
            self.trade_patterns_memory.store(
                content=json.dumps(pattern_data),
                metadata={
                    "counterparty": trade_data.get("counterparty", ""),
                    "product_type": trade_data.get("product_type", ""),
                    "source_type": trade_data.get("TRADE_SOURCE", ""),
                    "confidence": extraction_context.get("confidence", 0.0)
                }
            )
            
            return True
            
        except Exception as e:
            print(f"Failed to store extraction pattern: {e}")
            return False
    
    def get_similar_extraction_patterns(self, 
                                      counterparty: str,
                                      product_type: str,
                                      source_type: str,
                                      top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve similar extraction patterns to guide current extraction.
        
        Args:
            counterparty: Counterparty name
            product_type: Product type (SWAP, OPTION, etc.)
            source_type: BANK or COUNTERPARTY
            top_k: Number of similar patterns to return
        """
        try:
            query = f"{counterparty} {product_type} {source_type} extraction pattern"
            
            results = self.trade_patterns_memory.query(
                query=query,
                top_k=top_k
            )
            
            patterns = []
            for result in results:
                try:
                    pattern_data = json.loads(result.get("content", "{}"))
                    patterns.append({
                        "similarity_score": result.get("similarity_score", 0.0),
                        "pattern": pattern_data,
                        "extraction_tips": pattern_data.get("extraction_tips", ""),
                        "field_mappings": pattern_data.get("field_mappings", {}),
                        "confidence_boost": min(0.1, result.get("similarity_score", 0.0) * 0.1)
                    })
                except json.JSONDecodeError:
                    continue
            
            return patterns
            
        except Exception as e:
            print(f"Failed to retrieve similar patterns: {e}")
            return []
    
    def record_processing_event(self, 
                              document_id: str,
                              agent_name: str,
                              action: str,
                              result: Dict[str, Any]) -> bool:
        """
        Record processing events for audit trail and performance analysis.
        
        Args:
            document_id: Document identifier
            agent_name: Name of the processing agent
            action: Action performed (e.g., "trade_extracted")
            result: Result of the action
        """
        try:
            event_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "document_id": document_id,
                "agent_name": agent_name,
                "action": action,
                "success": result.get("success", False),
                "processing_time_ms": result.get("processing_time_ms", 0),
                "token_usage": result.get("token_usage", {}),
                "error": result.get("error", "") if not result.get("success") else ""
            }
            
            # Store in event memory for temporal analysis
            self.processing_history_memory.add_event(event_data)
            
            return True
            
        except Exception as e:
            print(f"Failed to record processing event: {e}")
            return False

# Enhanced tool with memory integration
@tool
def use_agentcore_memory_enhanced(operation: str, 
                                memory_resource: str, 
                                data: dict = None, 
                                query: str = None, 
                                top_k: int = 5) -> str:
    """
    Enhanced AgentCore Memory operations with trade-specific intelligence.
    
    This replaces your current use_agentcore_memory tool with full integration.
    """
    memory_manager = TradeExtractionMemoryManager()
    
    try:
        if operation == "store_pattern":
            success = memory_manager.store_successful_extraction_pattern(
                trade_data=data.get("trade_data", {}),
                extraction_context=data.get("extraction_context", {})
            )
            return json.dumps({
                "success": success,
                "operation": "store_pattern",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        elif operation == "get_similar_patterns":
            patterns = memory_manager.get_similar_extraction_patterns(
                counterparty=data.get("counterparty", ""),
                product_type=data.get("product_type", ""),
                source_type=data.get("source_type", ""),
                top_k=top_k
            )
            return json.dumps({
                "success": True,
                "patterns": patterns,
                "count": len(patterns)
            })
        
        elif operation == "record_event":
            success = memory_manager.record_processing_event(
                document_id=data.get("document_id", ""),
                agent_name=data.get("agent_name", ""),
                action=data.get("action", ""),
                result=data.get("result", {})
            )
            return json.dumps({
                "success": success,
                "operation": "record_event",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        else:
            return json.dumps({
                "success": False,
                "error": f"Unknown operation: {operation}"
            })
            
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "operation": operation
        })

# Integration example for your agent's system prompt
ENHANCED_SYSTEM_PROMPT_ADDITION = """

## AgentCore Memory Integration

You now have access to intelligent memory capabilities:

### Learning from Past Extractions
- Before extracting trade data, query memory for similar patterns using `use_agentcore_memory_enhanced`
- Look for trades with the same counterparty, product type, and source type
- Use the extraction tips and field mappings from similar successful extractions
- Apply confidence boosts based on pattern similarity

### Storing Successful Patterns
- After successful extraction, store the pattern for future reference
- Include field mappings, extraction tips, and confidence scores
- This helps improve accuracy for similar trades in the future

### Example Usage:
```
# Query for similar patterns before extraction
similar_patterns = use_agentcore_memory_enhanced(
    operation="get_similar_patterns",
    data={
        "counterparty": "Goldman Sachs",
        "product_type": "SWAP",
        "source_type": "BANK"
    },
    top_k=3
)

# Use the patterns to guide extraction strategy
# Then store successful extraction for future use
store_result = use_agentcore_memory_enhanced(
    operation="store_pattern",
    data={
        "trade_data": extracted_trade_data,
        "extraction_context": {
            "confidence": 0.95,
            "field_mappings": {"notional": "paragraph_2_amount"},
            "tips": "Focus on notional amount in paragraph 2"
        }
    }
)
```

This memory integration makes you smarter over time and improves extraction accuracy.
"""
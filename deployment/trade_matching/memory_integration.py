"""
AgentCore Memory Integration for Trade Matching Agent

This module provides memory-enhanced learning capabilities for the Trade Matching Agent.
It stores matching decisions and retrieves similar past cases to improve accuracy over time.

Requirements: 11.2, 11.3, 16.5, 20.6
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# AgentCore Memory imports
try:
    from bedrock_agentcore.memory.session import MemorySessionManager
    from bedrock_agentcore.memory.constants import ConversationalMessage, MessageRole
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    logger.warning("AgentCore Memory not available - memory features disabled")


class TradeMatchingMemory:
    """
    Memory manager for Trade Matching Agent.
    
    Provides:
    - Storage of matching decisions for learning
    - Retrieval of similar past matches for context
    - Integration with HITL feedback
    - Continuous improvement through pattern recognition
    """
    
    def __init__(
        self,
        memory_id: str,
        region_name: str = "us-east-1",
        agent_name: str = "trade-matching-agent"
    ):
        """
        Initialize memory manager.
        
        Args:
            memory_id: AgentCore Memory resource ID
            region_name: AWS region
            agent_name: Agent identifier for memory sessions
        """
        self.memory_id = memory_id
        self.region_name = region_name
        self.agent_name = agent_name
        self.enabled = MEMORY_AVAILABLE
        
        if self.enabled:
            try:
                self.session_manager = MemorySessionManager(
                    memory_id=memory_id,
                    region_name=region_name
                )
                logger.info(f"Memory initialized: {memory_id}")
            except Exception as e:
                logger.error(f"Failed to initialize memory: {e}")
                self.enabled = False
        else:
            self.session_manager = None
    
    def store_matching_decision(
        self,
        trade_id: str,
        source_type: str,
        classification: str,
        confidence: float,
        match_details: Dict[str, Any],
        correlation_id: str
    ) -> bool:
        """
        Store matching decision in AgentCore Memory.
        
        This enables:
        - Learning from past matching decisions
        - Retrieving similar cases for context
        - Improving matching accuracy over time
        - Supporting HITL feedback integration
        
        Args:
            trade_id: Trade identifier
            source_type: BANK or COUNTERPARTY
            classification: MATCHED, PROBABLE_MATCH, REVIEW_REQUIRED, or BREAK
            confidence: Confidence score (0.0 to 1.0)
            match_details: Detailed matching information including:
                - key_attributes: Trade attributes used for matching
                - reasoning: Explanation of the matching decision
                - processing_time_ms: Time taken for matching
                - token_usage: LLM token consumption
            correlation_id: Correlation ID for tracing
            
        Returns:
            bool: True if stored successfully
        """
        if not self.enabled or not self.session_manager:
            logger.debug("Memory not available - skipping decision storage")
            return False
        
        try:
            # Create a memory session for this matching decision
            session = self.session_manager.create_memory_session(
                actor_id=self.agent_name,
                session_id=f"match_{trade_id}_{correlation_id}"
            )
            
            # Format the matching decision for semantic storage
            decision_summary = self._format_decision_summary(
                trade_id=trade_id,
                source_type=source_type,
                classification=classification,
                confidence=confidence,
                match_details=match_details
            )
            
            # Store as a conversational turn (will be indexed semantically)
            session.add_turns(
                messages=[
                    ConversationalMessage(
                        decision_summary,
                        MessageRole.ASSISTANT
                    )
                ]
            )
            
            logger.info(
                f"Stored matching decision in memory: "
                f"trade_id={trade_id}, classification={classification}, "
                f"confidence={confidence:.2%}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to store matching decision: {e}", exc_info=True)
            return False
    
    def retrieve_similar_matches(
        self,
        trade_attributes: Dict[str, Any],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query AgentCore Memory for similar past matching decisions.
        
        This helps the agent:
        - Learn from historical patterns
        - Apply consistent matching logic
        - Identify edge cases based on past experience
        - Leverage HITL feedback from similar trades
        
        Args:
            trade_attributes: Trade attributes to search for:
                - currency: Trade currency (e.g., "USD")
                - product_type: Product type (e.g., "SWAP", "OPTION")
                - counterparty: Counterparty name
                - notional: Notional amount (optional)
            top_k: Number of similar matches to retrieve
            
        Returns:
            List of similar matching decisions with:
            - content: Decision summary
            - metadata: Additional context
            - similarity_score: Relevance score
        """
        if not self.enabled or not self.session_manager:
            logger.debug("Memory not available - skipping similarity search")
            return []
        
        try:
            # Build semantic search query from trade attributes
            query = self._build_search_query(trade_attributes)
            
            # Create a temporary session for searching
            session = self.session_manager.create_memory_session(
                actor_id=self.agent_name,
                session_id=f"search_{uuid.uuid4().hex[:12]}"
            )
            
            # Search semantic memory for similar cases
            memory_records = session.search_long_term_memories(
                query=query,
                namespace_prefix="/",
                top_k=top_k
            )
            
            logger.info(
                f"Retrieved {len(memory_records)} similar matches from memory "
                f"for query: {query[:100]}..."
            )
            
            return memory_records
            
        except Exception as e:
            logger.error(f"Failed to retrieve similar matches: {e}", exc_info=True)
            return []
    
    def _format_decision_summary(
        self,
        trade_id: str,
        source_type: str,
        classification: str,
        confidence: float,
        match_details: Dict[str, Any]
    ) -> str:
        """Format matching decision for semantic storage."""
        key_attrs = match_details.get('key_attributes', {})
        reasoning = match_details.get('reasoning', 'N/A')
        
        # Extract key attributes for better semantic search
        currency = key_attrs.get('currency', 'N/A')
        product_type = key_attrs.get('product_type', 'N/A')
        counterparty = key_attrs.get('counterparty', 'N/A')
        notional = key_attrs.get('notional', 'N/A')
        
        summary = f"""Trade Matching Decision

Trade ID: {trade_id}
Source Type: {source_type}
Classification: {classification}
Confidence: {confidence:.2%}

Key Attributes:
- Currency: {currency}
- Product Type: {product_type}
- Counterparty: {counterparty}
- Notional: {notional}

Reasoning:
{reasoning[:500]}

Timestamp: {datetime.utcnow().isoformat()}Z
"""
        return summary
    
    def _build_search_query(self, trade_attributes: Dict[str, Any]) -> str:
        """Build semantic search query from trade attributes."""
        query_parts = []
        
        if trade_attributes.get('currency'):
            query_parts.append(f"currency {trade_attributes['currency']}")
        
        if trade_attributes.get('product_type'):
            query_parts.append(f"product type {trade_attributes['product_type']}")
        
        if trade_attributes.get('counterparty'):
            query_parts.append(f"counterparty {trade_attributes['counterparty']}")
        
        if trade_attributes.get('notional'):
            query_parts.append(f"notional amount {trade_attributes['notional']}")
        
        if not query_parts:
            return "trade matching decision"
        
        return f"Similar trades: {' '.join(query_parts)}"
    
    def get_memory_context_for_prompt(
        self,
        trade_attributes: Dict[str, Any],
        max_examples: int = 3
    ) -> str:
        """
        Get memory context to include in agent prompt.
        
        This provides the agent with relevant past decisions to inform
        the current matching analysis.
        
        Args:
            trade_attributes: Current trade attributes
            max_examples: Maximum number of examples to include
            
        Returns:
            Formatted string with past matching examples
        """
        similar_matches = self.retrieve_similar_matches(
            trade_attributes=trade_attributes,
            top_k=max_examples
        )
        
        if not similar_matches:
            return ""
        
        context = "\n## Past Matching Decisions (For Context)\n\n"
        context += "Here are similar trades you've matched before:\n\n"
        
        for i, match in enumerate(similar_matches, 1):
            content = match.get('content', '')
            # Extract key info from the stored decision
            context += f"### Example {i}\n{content[:300]}...\n\n"
        
        context += "Use these examples to inform your current matching decision.\n"
        return context


# Global memory instance (initialized in main agent file)
_memory_instance: Optional[TradeMatchingMemory] = None


def initialize_memory(
    memory_id: str,
    region_name: str = "us-east-1",
    agent_name: str = "trade-matching-agent"
) -> TradeMatchingMemory:
    """
    Initialize global memory instance.
    
    Call this once during agent startup.
    """
    global _memory_instance
    _memory_instance = TradeMatchingMemory(
        memory_id=memory_id,
        region_name=region_name,
        agent_name=agent_name
    )
    return _memory_instance


def get_memory() -> Optional[TradeMatchingMemory]:
    """Get the global memory instance."""
    return _memory_instance

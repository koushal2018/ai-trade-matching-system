"""High-level memory storage utilities for trade matching operations."""

import json
from datetime import datetime
from typing import Optional, Any
from .client import memory_client


async def store_trade_pattern(
    trade_id: str,
    trade_data: dict[str, Any],
    source_type: str,
    extraction_confidence: float = 1.0
) -> dict:
    """
    Store a trade pattern in semantic memory for future reference.
    
    Args:
        trade_id: Unique trade identifier
        trade_data: Extracted trade data
        source_type: BANK or COUNTERPARTY
        extraction_confidence: Confidence score of extraction
    
    Returns:
        Storage result
    """
    # Create searchable content from trade data
    content = f"""
    Trade ID: {trade_id}
    Source: {source_type}
    Counterparty: {trade_data.get('counterparty', 'Unknown')}
    Product Type: {trade_data.get('product_type', 'Unknown')}
    Currency: {trade_data.get('currency', 'Unknown')}
    Notional: {trade_data.get('notional', 0)}
    Trade Date: {trade_data.get('trade_date', 'Unknown')}
    """
    
    metadata = {
        "trade_id": trade_id,
        "source_type": source_type,
        "extraction_confidence": extraction_confidence,
        "counterparty": trade_data.get("counterparty"),
        "product_type": trade_data.get("product_type"),
        "currency": trade_data.get("currency"),
        "stored_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return await memory_client.store_semantic(
        content=content,
        metadata=metadata,
        namespace="trade_patterns"
    )


async def retrieve_similar_trades(
    query_trade: dict[str, Any],
    limit: int = 5
) -> list[dict]:
    """
    Retrieve similar trades from memory for context.
    
    Args:
        query_trade: Trade data to find similar matches for
        limit: Maximum number of results
    
    Returns:
        List of similar trade patterns with metadata
    """
    # Build query from trade characteristics
    query = f"""
    Counterparty: {query_trade.get('counterparty', '')}
    Product Type: {query_trade.get('product_type', '')}
    Currency: {query_trade.get('currency', '')}
    """
    
    return await memory_client.retrieve_semantic(
        query=query,
        namespace="trade_patterns",
        limit=limit,
        threshold=0.6
    )


async def store_matching_decision(
    trade_id: str,
    match_score: float,
    classification: str,
    decision_status: str,
    reason_codes: list[str],
    differences: dict[str, Any],
    human_decision: Optional[str] = None,
    decision_reason: Optional[str] = None
) -> dict:
    """
    Store a matching decision in semantic memory for learning.
    
    Args:
        trade_id: Trade identifier
        match_score: Computed match score (0-1)
        classification: Match classification (MATCHED, BREAK, etc.)
        decision_status: Decision status (AUTO_MATCH, ESCALATE, etc.)
        reason_codes: List of reason codes
        differences: Field differences between trades
        human_decision: Optional human override decision
        decision_reason: Optional reason for human decision
    
    Returns:
        Storage result
    """
    content = f"""
    Trade {trade_id} matching decision:
    Score: {match_score}
    Classification: {classification}
    Status: {decision_status}
    Reason Codes: {', '.join(reason_codes)}
    Human Decision: {human_decision or 'None'}
    """
    
    metadata = {
        "trade_id": trade_id,
        "match_score": match_score,
        "classification": classification,
        "decision_status": decision_status,
        "reason_codes": reason_codes,
        "differences": differences,
        "human_decision": human_decision,
        "decision_reason": decision_reason,
        "stored_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return await memory_client.store_semantic(
        content=content,
        metadata=metadata,
        namespace="matching_decisions"
    )


async def store_error_pattern(
    error_type: str,
    error_context: dict[str, Any],
    resolution: Optional[str] = None,
    severity: str = "MEDIUM"
) -> dict:
    """
    Store an error pattern for future prevention and learning.
    
    Args:
        error_type: Type of error (e.g., EXTRACTION_FAILED, MATCHING_ERROR)
        error_context: Context information about the error
        resolution: How the error was resolved (if known)
        severity: Error severity (LOW, MEDIUM, HIGH, CRITICAL)
    
    Returns:
        Storage result
    """
    content = f"""
    Error Type: {error_type}
    Severity: {severity}
    Context: {json.dumps(error_context)}
    Resolution: {resolution or 'Pending'}
    """
    
    metadata = {
        "error_type": error_type,
        "severity": severity,
        "context": error_context,
        "resolution": resolution,
        "stored_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return await memory_client.store_semantic(
        content=content,
        metadata=metadata,
        namespace="error_patterns"
    )


async def retrieve_error_patterns(
    error_type: Optional[str] = None,
    limit: int = 10
) -> list[dict]:
    """
    Retrieve error patterns for analysis and prevention.
    
    Args:
        error_type: Filter by error type
        limit: Maximum number of results
    
    Returns:
        List of error patterns
    """
    query = f"Error Type: {error_type}" if error_type else "Error patterns"
    
    return await memory_client.retrieve_semantic(
        query=query,
        namespace="error_patterns",
        limit=limit,
        threshold=0.5
    )


async def store_processing_history(
    event_type: str,
    document_id: str,
    processing_result: dict[str, Any],
    correlation_id: Optional[str] = None
) -> dict:
    """
    Store processing history as an event for temporal tracking.
    
    Args:
        event_type: Type of processing event
        document_id: Document or trade identifier
        processing_result: Result of the processing
        correlation_id: Correlation ID for distributed tracing
    
    Returns:
        Storage result
    """
    event_data = {
        "document_id": document_id,
        "result": processing_result,
        "processed_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return await memory_client.store_event(
        event_type=event_type,
        event_data=event_data,
        correlation_id=correlation_id
    )


async def retrieve_hitl_feedback(
    trade_characteristics: dict[str, Any],
    limit: int = 5
) -> list[dict]:
    """
    Retrieve HITL feedback for similar cases to suggest decisions.
    
    Args:
        trade_characteristics: Characteristics of the current trade
        limit: Maximum number of results
    
    Returns:
        List of similar HITL decisions with outcomes
    """
    query = f"""
    Similar trade characteristics:
    Counterparty: {trade_characteristics.get('counterparty', '')}
    Product Type: {trade_characteristics.get('product_type', '')}
    Reason Codes: {', '.join(trade_characteristics.get('reason_codes', []))}
    """
    
    results = await memory_client.retrieve_semantic(
        query=query,
        namespace="matching_decisions",
        limit=limit,
        threshold=0.7
    )
    
    # Filter to only include human decisions
    return [
        r for r in results
        if r.get("metadata", {}).get("human_decision") is not None
    ]


async def store_rl_policy(
    policy_name: str,
    policy_data: dict[str, Any],
    version: str = "1.0"
) -> dict:
    """
    Store RL policy for exception routing.
    
    Args:
        policy_name: Name of the policy
        policy_data: Policy parameters and weights
        version: Policy version
    
    Returns:
        Storage result
    """
    content = f"""
    RL Policy: {policy_name}
    Version: {version}
    Parameters: {json.dumps(policy_data)}
    """
    
    metadata = {
        "policy_name": policy_name,
        "version": version,
        "policy_data": policy_data,
        "stored_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return await memory_client.store_semantic(
        content=content,
        metadata=metadata,
        namespace="rl_policies"
    )


async def retrieve_rl_policy(policy_name: str) -> Optional[dict]:
    """
    Retrieve the latest RL policy by name.
    
    Args:
        policy_name: Name of the policy to retrieve
    
    Returns:
        Policy data or None if not found
    """
    results = await memory_client.retrieve_semantic(
        query=f"RL Policy: {policy_name}",
        namespace="rl_policies",
        limit=1,
        threshold=0.9
    )
    
    if results:
        return results[0].get("metadata", {}).get("policy_data")
    return None

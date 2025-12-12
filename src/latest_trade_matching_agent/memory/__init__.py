"""AgentCore Memory integration module."""

from .storage import (
    store_trade_pattern,
    retrieve_similar_trades,
    store_matching_decision,
    store_error_pattern,
    store_processing_history,
    retrieve_error_patterns,
)
from .client import AgentCoreMemoryClient

__all__ = [
    "store_trade_pattern",
    "retrieve_similar_trades",
    "store_matching_decision",
    "store_error_pattern",
    "store_processing_history",
    "retrieve_error_patterns",
    "AgentCoreMemoryClient",
]

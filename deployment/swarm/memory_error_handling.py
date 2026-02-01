"""
Memory Error Handling Module

This module provides error handling utilities for AgentCore Memory operations,
including retry logic, circuit breaker pattern, and graceful fallback mechanisms.
"""

import time
import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional
from concurrent.futures import TimeoutError
from datetime import datetime

from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager
)

logger = logging.getLogger(__name__)


class MemoryFallbackHandler:
    """
    Handle memory service failures gracefully with retry logic and circuit breaker.
    
    This class implements:
    - Exponential backoff retry logic
    - Circuit breaker pattern to prevent cascading failures
    - Fallback to operation without memory when circuit breaker is open
    - Comprehensive logging for monitoring and debugging
    
    Validates: Requirements 18.1, 18.2, 18.3, 18.4, 18.5
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_reset_timeout: float = 60.0
    ):
        """
        Initialize the memory fallback handler.
        
        Args:
            max_retries: Maximum number of retry attempts (default: 3)
            backoff_factor: Exponential backoff multiplier (default: 2.0)
            circuit_breaker_threshold: Number of failures before opening circuit (default: 5)
            circuit_breaker_reset_timeout: Seconds before attempting to close circuit (default: 60.0)
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_reset_timeout = circuit_breaker_reset_timeout
        
        self.circuit_breaker_failures = 0
        self.circuit_breaker_open = False
        self.circuit_breaker_opened_at: Optional[datetime] = None
        
        logger.info(
            f"MemoryFallbackHandler initialized: max_retries={max_retries}, "
            f"backoff_factor={backoff_factor}, threshold={circuit_breaker_threshold}"
        )
    
    def _check_circuit_breaker(self) -> bool:
        """
        Check if circuit breaker should be closed after timeout.
        
        Returns:
            True if circuit breaker is open, False if closed
        """
        if not self.circuit_breaker_open:
            return False
        
        # Check if enough time has passed to attempt closing the circuit
        if self.circuit_breaker_opened_at:
            elapsed = (datetime.utcnow() - self.circuit_breaker_opened_at).total_seconds()
            if elapsed >= self.circuit_breaker_reset_timeout:
                logger.info(
                    f"Circuit breaker timeout reached ({elapsed:.1f}s), "
                    "attempting to close circuit"
                )
                self.circuit_breaker_open = False
                self.circuit_breaker_failures = 0
                self.circuit_breaker_opened_at = None
                return False
        
        return True
    
    def execute_with_fallback(
        self,
        operation: Callable,
        *args,
        operation_name: str = "memory_operation",
        **kwargs
    ) -> Any:
        """
        Execute memory operation with retry and circuit breaker.
        Falls back to operation without memory if circuit breaker is open.
        
        Args:
            operation: Callable to execute (memory operation)
            *args: Positional arguments for the operation
            operation_name: Name of the operation for logging
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Result from the operation, or None if fallback is triggered
        """
        # Check if circuit breaker should be closed
        if self._check_circuit_breaker():
            logger.warning(
                f"Circuit breaker open for {operation_name} - executing without memory"
            )
            return self._execute_without_memory(operation_name)
        
        # Attempt operation with retry logic
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Executing {operation_name} (attempt {attempt + 1}/{self.max_retries})"
                )
                result = operation(*args, **kwargs)
                
                # Success - reset circuit breaker failure count
                if self.circuit_breaker_failures > 0:
                    logger.info(
                        f"{operation_name} succeeded after {self.circuit_breaker_failures} "
                        "previous failures - resetting circuit breaker"
                    )
                    self.circuit_breaker_failures = 0
                
                return result
                
            except Exception as e:
                logger.error(
                    f"{operation_name} failed (attempt {attempt + 1}/{self.max_retries}): {e}",
                    exc_info=True
                )
                
                # If not the last attempt, apply exponential backoff
                if attempt < self.max_retries - 1:
                    sleep_time = self.backoff_factor ** attempt
                    logger.info(f"Retrying {operation_name} in {sleep_time:.1f}s...")
                    time.sleep(sleep_time)
                else:
                    # Last attempt failed - increment circuit breaker counter
                    self.circuit_breaker_failures += 1
                    logger.error(
                        f"{operation_name} failed after {self.max_retries} attempts. "
                        f"Circuit breaker failures: {self.circuit_breaker_failures}/"
                        f"{self.circuit_breaker_threshold}"
                    )
                    
                    # Check if circuit breaker threshold reached
                    if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
                        self.circuit_breaker_open = True
                        self.circuit_breaker_opened_at = datetime.utcnow()
                        logger.error(
                            f"Circuit breaker opened after {self.circuit_breaker_failures} "
                            f"failures. Will retry after {self.circuit_breaker_reset_timeout}s"
                        )
                    
                    return self._execute_without_memory(operation_name)
    
    def _execute_without_memory(self, operation_name: str) -> None:
        """
        Execute operation without memory access (fallback mode).
        
        Args:
            operation_name: Name of the operation for logging
            
        Returns:
            None to indicate memory operation was skipped
        """
        logger.info(
            f"Executing {operation_name} without memory access (fallback mode)"
        )
        # Operation continues but without memory retrieval/storage
        return None
    
    def reset_circuit_breaker(self) -> None:
        """Manually reset the circuit breaker (for testing or manual intervention)."""
        logger.info("Manually resetting circuit breaker")
        self.circuit_breaker_open = False
        self.circuit_breaker_failures = 0
        self.circuit_breaker_opened_at = None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the fallback handler.
        
        Returns:
            Dictionary with circuit breaker status and failure count
        """
        return {
            "circuit_breaker_open": self.circuit_breaker_open,
            "circuit_breaker_failures": self.circuit_breaker_failures,
            "circuit_breaker_opened_at": (
                self.circuit_breaker_opened_at.isoformat()
                if self.circuit_breaker_opened_at
                else None
            ),
            "max_retries": self.max_retries,
            "backoff_factor": self.backoff_factor,
            "circuit_breaker_threshold": self.circuit_breaker_threshold
        }


# Global fallback handler instance
_global_fallback_handler: Optional[MemoryFallbackHandler] = None


def get_fallback_handler() -> MemoryFallbackHandler:
    """
    Get or create the global fallback handler instance.
    
    Returns:
        Global MemoryFallbackHandler instance
    """
    global _global_fallback_handler
    if _global_fallback_handler is None:
        _global_fallback_handler = MemoryFallbackHandler()
    return _global_fallback_handler


def create_session_manager_safe(
    agent_name: str,
    document_id: str,
    memory_id: str = None,
    actor_id: str = "trade_matching_system",
    region_name: str = "us-east-1"
) -> Optional[AgentCoreMemorySessionManager]:
    """
    Create session manager with error handling.
    Returns None on failure instead of raising exceptions.
    
    This function wraps session manager creation with try-catch to handle:
    - Missing or invalid memory_id
    - Network connectivity issues
    - AgentCore Memory service unavailability
    - Configuration errors
    
    Args:
        agent_name: Name of the agent (pdf_adapter, trade_extractor, etc.)
        document_id: Unique document identifier for this trade
        memory_id: AgentCore Memory ID (from environment if not provided)
        actor_id: Actor identifier (default: trade_matching_system)
        region_name: AWS region (default: us-east-1)
        
    Returns:
        Configured session manager instance, or None if initialization fails
        
    Validates: Requirements 18.1, 18.2, 18.3, 18.4, 18.5
    """
    try:
        # Import here to avoid circular dependency
        from trade_matching_swarm import create_agent_session_manager
        
        logger.info(
            f"Creating session manager for {agent_name} (document_id={document_id})"
        )
        
        session_manager = create_agent_session_manager(
            agent_name=agent_name,
            document_id=document_id,
            memory_id=memory_id,
            actor_id=actor_id,
            region_name=region_name
        )
        
        logger.info(f"Successfully created session manager for {agent_name}")
        return session_manager
        
    except ValueError as e:
        logger.error(
            f"Session manager initialization failed for {agent_name}: {e}. "
            "Continuing without memory integration."
        )
        return None
        
    except Exception as e:
        logger.error(
            f"Unexpected error creating session manager for {agent_name}: {e}. "
            "Continuing without memory integration.",
            exc_info=True
        )
        return None


async def retrieve_with_timeout(
    session_manager: AgentCoreMemorySessionManager,
    query: str,
    namespace: str = None,
    timeout_seconds: float = 2.0
) -> Optional[List[Dict]]:
    """
    Retrieve from memory with timeout.
    Returns None if timeout occurs.
    
    This async function implements timeout handling for memory retrieval to prevent
    slow memory operations from blocking agent execution.
    
    Args:
        session_manager: AgentCore Memory session manager
        query: Query string for memory retrieval
        namespace: Optional namespace to retrieve from
        timeout_seconds: Timeout in seconds (default: 2.0)
        
    Returns:
        List of retrieved memory items, or None if timeout/error occurs
        
    Validates: Requirements 18.1, 18.2, 18.3, 18.4, 18.5
    """
    try:
        logger.debug(
            f"Retrieving from memory with timeout={timeout_seconds}s: {query[:50]}..."
        )
        
        # Create async task for retrieval
        async def _retrieve():
            # Note: If session_manager.retrieve is not async, wrap it
            if asyncio.iscoroutinefunction(session_manager.retrieve):
                return await session_manager.retrieve(query=query, namespace=namespace)
            else:
                # Run synchronous function in executor
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    None,
                    lambda: session_manager.retrieve(query=query, namespace=namespace)
                )
        
        result = await asyncio.wait_for(_retrieve(), timeout=timeout_seconds)
        
        logger.debug(f"Memory retrieval succeeded: {len(result) if result else 0} results")
        return result
        
    except asyncio.TimeoutError:
        logger.warning(
            f"Memory retrieval timed out after {timeout_seconds}s for query: {query[:50]}..."
        )
        return None
        
    except Exception as e:
        logger.error(f"Memory retrieval error: {e}", exc_info=True)
        return None


def store_pattern_safe(
    session_manager: AgentCoreMemorySessionManager,
    pattern: Dict[str, Any],
    namespace: str
) -> bool:
    """
    Store pattern to memory with error handling.
    Returns True if successful, False otherwise.
    
    This function wraps memory storage with try-catch to ensure that storage
    failures don't interrupt the main processing flow.
    
    Args:
        session_manager: AgentCore Memory session manager
        pattern: Pattern data to store
        namespace: Memory namespace to store in
        
    Returns:
        True if storage succeeded, False if it failed
        
    Validates: Requirements 18.1, 18.2, 18.3, 18.4, 18.5
    """
    try:
        logger.debug(f"Storing pattern to namespace: {namespace}")
        
        session_manager.store(pattern, namespace=namespace)
        
        logger.info(f"Successfully stored pattern to {namespace}")
        return True
        
    except Exception as e:
        logger.error(
            f"Failed to store pattern to {namespace}: {e}. "
            "Pattern not stored - continuing without memory update.",
            exc_info=True
        )
        return False

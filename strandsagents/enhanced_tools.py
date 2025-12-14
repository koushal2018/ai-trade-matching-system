"""
Enhanced Strands Tools for AI-Powered Trade Reconciliation Analysis

This module provides AI-powered tools that integrate with the Strands agents framework
to support intelligent trade matching, semantic field comparison, and context-aware analysis.
"""

import json
import logging
import asyncio
import time
import random
import re
from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from difflib import SequenceMatcher
from decimal import Decimal
from datetime import datetime

from strands import tool
try:
    from .ai_providers.base import AIProviderAdapter
    from .ai_providers.factory import AIProviderFactory
    from .ai_providers.exceptions import (
        AIProviderError, 
        AIProviderUnavailableError, 
        AIProviderTimeoutError,
        AIProviderRateLimitError,
        AIProviderConfigurationError
    )
    from .enhanced_config import DecisionMode, EnhancedMatcherConfig, EnhancedReconcilerConfig
    from .financial_domain_intelligence import (
        get_domain_intelligence, 
        AssetClass, 
        TradingContext,
        FinancialDomainIntelligence
    )
    from .domain_prompts import get_domain_prompt_generator
except ImportError:
    # Handle relative import for standalone testing
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    
    from ai_providers.base import AIProviderAdapter
    from ai_providers.factory import AIProviderFactory
    from ai_providers.exceptions import (
        AIProviderError, 
        AIProviderUnavailableError, 
        AIProviderTimeoutError,
        AIProviderRateLimitError,
        AIProviderConfigurationError
    )
    from enhanced_config import DecisionMode, EnhancedMatcherConfig, EnhancedReconcilerConfig
    from financial_domain_intelligence import (
        get_domain_intelligence, 
        AssetClass, 
        TradingContext,
        FinancialDomainIntelligence
    )
    from domain_prompts import get_domain_prompt_generator

logger = logging.getLogger(__name__)


class AIOperationError(Exception):
    """Exception raised when AI operations fail"""
    pass


class AIServiceMonitor:
    """Monitor AI service health and fallback usage patterns"""
    
    def __init__(self):
        self.failure_counts = {}
        self.fallback_counts = {}
        self.health_status = {}
        self.last_health_check = {}
        self.operation_metrics = {}
        
    def record_failure(self, provider_name: str, operation: str, error_type: str):
        """Record AI service failure for monitoring"""
        key = f"{provider_name}:{operation}"
        if key not in self.failure_counts:
            self.failure_counts[key] = {}
        if error_type not in self.failure_counts[key]:
            self.failure_counts[key][error_type] = 0
        self.failure_counts[key][error_type] += 1
        
        logger.warning(f"AI service failure recorded: {provider_name} {operation} - {error_type}")
        
    def record_fallback(self, provider_name: str, operation: str, reason: str):
        """Record fallback usage for monitoring"""
        key = f"{provider_name}:{operation}"
        if key not in self.fallback_counts:
            self.fallback_counts[key] = {}
        if reason not in self.fallback_counts[key]:
            self.fallback_counts[key][reason] = 0
        self.fallback_counts[key][reason] += 1
        
        logger.info(f"AI fallback usage recorded: {provider_name} {operation} - {reason}")
        
    def record_operation_metrics(self, provider_name: str, operation: str, 
                               duration_ms: float, success: bool):
        """Record operation performance metrics"""
        key = f"{provider_name}:{operation}"
        if key not in self.operation_metrics:
            self.operation_metrics[key] = {
                'total_calls': 0,
                'successful_calls': 0,
                'total_duration_ms': 0,
                'avg_duration_ms': 0
            }
        
        metrics = self.operation_metrics[key]
        metrics['total_calls'] += 1
        if success:
            metrics['successful_calls'] += 1
        metrics['total_duration_ms'] += duration_ms
        metrics['avg_duration_ms'] = metrics['total_duration_ms'] / metrics['total_calls']
        
    def update_health_status(self, provider_name: str, status: Dict[str, Any]):
        """Update health status for a provider"""
        self.health_status[provider_name] = status
        self.last_health_check[provider_name] = time.time()
        
    def get_failure_stats(self) -> Dict[str, Any]:
        """Get comprehensive failure and performance statistics"""
        return {
            "failure_counts": self.failure_counts,
            "fallback_counts": self.fallback_counts,
            "health_status": self.health_status,
            "last_health_check": self.last_health_check,
            "operation_metrics": self.operation_metrics,
            "timestamp": time.time()
        }
    
    def should_circuit_break(self, provider_name: str, operation: str, 
                           failure_threshold: int = 5, time_window: int = 300) -> bool:
        """Determine if circuit breaker should be triggered"""
        key = f"{provider_name}:{operation}"
        if key not in self.failure_counts:
            return False
            
        # Simple circuit breaker logic - could be enhanced with time windows
        total_failures = sum(self.failure_counts[key].values())
        return total_failures >= failure_threshold


# Global monitor instance
ai_monitor = AIServiceMonitor()


async def robust_ai_operation(
    ai_provider: AIProviderAdapter,
    operation_name: str,
    fallback_func: Callable,
    *args,
    **kwargs
) -> Any:
    """
    Execute AI operation with enhanced error handling, retry logic, and automatic fallback.
    
    Features:
    - Exponential backoff with jitter for retries
    - Circuit breaker pattern for failing providers
    - Comprehensive monitoring and alerting
    - Graceful degradation with detailed logging
    
    Args:
        ai_provider: AI provider adapter instance
        operation_name: Name of the operation for logging
        fallback_func: Fallback function to call if AI fails
        *args: Arguments to pass to both AI and fallback functions
        **kwargs: Keyword arguments to pass to both AI and fallback functions
        
    Returns:
        Result from AI operation or fallback function
    """
    provider_name = getattr(ai_provider, 'provider_name', 'unknown')
    max_retries = kwargs.pop('max_retries', 3)
    base_delay = kwargs.pop('retry_delay', 1.0)
    max_delay = kwargs.pop('max_retry_delay', 30.0)
    enable_circuit_breaker = kwargs.pop('enable_circuit_breaker', True)
    
    start_time = time.time()
    
    # Check circuit breaker
    if enable_circuit_breaker and ai_monitor.should_circuit_break(provider_name, operation_name):
        logger.warning(f"Circuit breaker triggered for {provider_name}:{operation_name}, using fallback")
        ai_monitor.record_fallback(provider_name, operation_name, "circuit_breaker")
        result = fallback_func(*args, **kwargs)
        ai_monitor.record_operation_metrics(provider_name, operation_name, 
                                          (time.time() - start_time) * 1000, False)
        return result
    
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            # Execute AI operation based on operation name
            if operation_name == "analyze_document_context":
                result = await ai_provider.analyze_document_context(*args, **kwargs)
            elif operation_name == "semantic_field_matching":
                result = await ai_provider.semantic_field_matching(*args, **kwargs)
            elif operation_name == "intelligent_trade_matching":
                result = await ai_provider.intelligent_trade_matching(*args, **kwargs)
            elif operation_name == "explain_mismatch":
                result = await ai_provider.explain_mismatch(*args, **kwargs)
            else:
                raise ValueError(f"Unknown AI operation: {operation_name}")
            
            # Success - record metrics and return
            duration_ms = (time.time() - start_time) * 1000
            ai_monitor.record_operation_metrics(provider_name, operation_name, duration_ms, True)
            logger.debug(f"AI operation {provider_name}:{operation_name} succeeded in {duration_ms:.2f}ms")
            return result
                
        except AIProviderTimeoutError as e:
            last_exception = e
            ai_monitor.record_failure(provider_name, operation_name, "timeout")
            logger.warning(f"AI operation {provider_name}:{operation_name} timed out "
                         f"(attempt {attempt + 1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                delay = min(base_delay * (2 ** attempt), max_delay)
                jitter = random.uniform(0, delay * 0.1)  # Add up to 10% jitter
                await asyncio.sleep(delay + jitter)
                continue
                
        except AIProviderRateLimitError as e:
            last_exception = e
            ai_monitor.record_failure(provider_name, operation_name, "rate_limit")
            logger.warning(f"AI operation {provider_name}:{operation_name} rate limited "
                         f"(attempt {attempt + 1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                # Use retry_after if provided, otherwise exponential backoff
                delay = getattr(e, 'retry_after', base_delay * (2 ** attempt))
                delay = min(delay, max_delay)
                await asyncio.sleep(delay)
                continue
                
        except AIProviderUnavailableError as e:
            last_exception = e
            ai_monitor.record_failure(provider_name, operation_name, "unavailable")
            logger.warning(f"AI provider {provider_name} unavailable for {operation_name}: {e}")
            # Don't retry for unavailable errors - fail fast to fallback
            break
            
        except AIProviderConfigurationError as e:
            last_exception = e
            ai_monitor.record_failure(provider_name, operation_name, "configuration")
            logger.error(f"AI provider {provider_name} configuration error for {operation_name}: {e}")
            # Don't retry for configuration errors
            break
            
        except AIProviderError as e:
            last_exception = e
            ai_monitor.record_failure(provider_name, operation_name, "provider_error")
            logger.warning(f"AI provider {provider_name} error for {operation_name} "
                         f"(attempt {attempt + 1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                delay = min(base_delay * (2 ** attempt), max_delay)
                jitter = random.uniform(0, delay * 0.1)
                await asyncio.sleep(delay + jitter)
                continue
                
        except Exception as e:
            last_exception = e
            ai_monitor.record_failure(provider_name, operation_name, "unexpected")
            logger.error(f"Unexpected error in AI operation {provider_name}:{operation_name} "
                        f"(attempt {attempt + 1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                delay = min(base_delay * (2 ** attempt), max_delay)
                jitter = random.uniform(0, delay * 0.1)
                await asyncio.sleep(delay + jitter)
                continue
    
    # All retries exhausted - fallback to deterministic approach
    fallback_reason = f"max_retries_exceeded_{type(last_exception).__name__}" if last_exception else "unknown_failure"
    ai_monitor.record_fallback(provider_name, operation_name, fallback_reason)
    
    logger.info(f"AI operation {provider_name}:{operation_name} failed after {max_retries} attempts, "
               f"using deterministic fallback. Last error: {last_exception}")
    
    try:
        result = fallback_func(*args, **kwargs)
        duration_ms = (time.time() - start_time) * 1000
        ai_monitor.record_operation_metrics(provider_name, operation_name, duration_ms, False)
        return result
    except Exception as fallback_error:
        logger.error(f"Fallback function also failed for {operation_name}: {fallback_error}")
        raise AIOperationError(f"Both AI operation and fallback failed for {operation_name}. "
                             f"AI error: {last_exception}, Fallback error: {fallback_error}")


async def check_ai_provider_health(ai_provider: AIProviderAdapter, 
                                 cache_duration: int = 300) -> Dict[str, Any]:
    """
    Perform health check on AI provider with caching to avoid excessive checks.
    
    Args:
        ai_provider: AI provider to check
        cache_duration: Cache duration in seconds
        
    Returns:
        Health status dictionary
    """
    provider_name = getattr(ai_provider, 'provider_name', 'unknown')
    
    # Check if we have recent health status
    if provider_name in ai_monitor.last_health_check:
        last_check = ai_monitor.last_health_check[provider_name]
        if time.time() - last_check < cache_duration:
            return ai_monitor.health_status.get(provider_name, {"status": "unknown"})
    
    try:
        health_status = await ai_provider.health_check()
        ai_monitor.update_health_status(provider_name, health_status)
        return health_status
    except Exception as e:
        error_status = {
            "status": "error",
            "provider": provider_name,
            "error": str(e),
            "timestamp": time.time()
        }
        ai_monitor.update_health_status(provider_name, error_status)
        return error_status


def get_ai_service_metrics() -> Dict[str, Any]:
    """
    Get comprehensive AI service metrics for monitoring and alerting.
    
    Returns:
        Dictionary containing failure stats, health status, and performance metrics
    """
    return ai_monitor.get_failure_stats()


def reset_ai_service_metrics():
    """Reset AI service metrics - useful for testing or periodic cleanup"""
    global ai_monitor
    ai_monitor = AIServiceMonitor()


def _deterministic_trade_analysis(trade_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced deterministic trade context analysis using financial domain intelligence.
    
    Args:
        trade_data: Trade information to analyze
        
    Returns:
        Dictionary containing transaction type, critical fields, and context
    """
    # Get domain intelligence instance
    domain_intel = get_domain_intelligence()
    
    # Get comprehensive domain context
    domain_context = domain_intel.get_domain_context(trade_data)
    
    # Determine transaction type using domain intelligence
    asset_class = domain_context.asset_class
    trading_context = domain_context.trading_context
    
    # Map asset class and trading context to transaction type
    if asset_class == AssetClass.COMMODITIES:
        if trading_context == TradingContext.FORWARD:
            transaction_type = "commodity_forward"
        elif trading_context == TradingContext.SWAP:
            transaction_type = "commodity_swap"
        else:
            transaction_type = "commodity_trade"
    elif asset_class == AssetClass.FX:
        if trading_context == TradingContext.SPOT:
            transaction_type = "fx_spot"
        elif trading_context == TradingContext.FORWARD:
            transaction_type = "fx_forward"
        else:
            transaction_type = "fx_trade"
    elif asset_class == AssetClass.RATES:
        if trading_context == TradingContext.SWAP:
            transaction_type = "interest_rate_swap"
        else:
            transaction_type = "rates_trade"
    elif asset_class == AssetClass.DERIVATIVES:
        if trading_context == TradingContext.OPTION:
            transaction_type = "option"
        else:
            transaction_type = "derivative"
    else:
        transaction_type = "unknown"
    
    # Get critical fields from domain context
    critical_fields = [fp.field_name for fp in domain_context.field_priorities 
                      if fp.criticality in ["CRITICAL", "IMPORTANT"]]
    
    # If no domain-specific fields, use defaults
    if not critical_fields:
        critical_fields = ["trade_date", "total_notional_quantity", "currency"]
    
    # Get field mappings from domain context
    field_mappings = {}
    for term, mapping in domain_context.terminology_mappings.items():
        if term != mapping.standard_term:
            field_mappings[term] = mapping.standard_term
    
    # Add default mappings if none from domain
    if not field_mappings:
        field_mappings = {
            "settlement_date": "termination_date",
            "maturity_date": "termination_date",
            "notional": "total_notional_quantity",
            "amount": "total_notional_quantity",
            "counterparty": "buyer_legal_entity"
        }
    
    return {
        "transaction_type": transaction_type,
        "critical_fields": list(set(critical_fields)),  # Remove duplicates
        "field_mappings": field_mappings,
        "confidence": 0.85,  # Higher confidence with domain intelligence
        "method": "deterministic_enhanced",
        "context_metadata": {
            "reasoning": f"Determined transaction type using domain intelligence",
            "asset_class": asset_class.value,
            "trading_context": trading_context.value,
            "domain_confidence": {
                "asset_class_confidence": domain_context.field_priorities[0].priority_score if domain_context.field_priorities else 0.8,
                "trading_context_confidence": 0.8
            },
            "market_conventions": domain_context.market_conventions,
            "validation_rules": domain_context.validation_rules
        }
    }


def _determine_asset_class(trade_data: Dict[str, Any]) -> str:
    """Determine asset class from trade data"""
    if trade_data.get('commodity_type'):
        return "commodities"
    elif trade_data.get('currency_pair'):
        return "fx"
    elif trade_data.get('interest_rate'):
        return "rates"
    elif trade_data.get('equity_symbol'):
        return "equities"
    else:
        return "unknown"


def _deterministic_field_match(
    field1_name: str, 
    field1_value: Any, 
    field2_name: str, 
    field2_value: Any,
    context: str = ""
) -> Dict[str, Any]:
    """
    Enhanced deterministic field matching using financial domain intelligence.
    
    Args:
        field1_name: First field name
        field1_value: First field value
        field2_name: Second field name
        field2_value: Second field value
        context: Optional context information
        
    Returns:
        Dictionary with match status, confidence, and reasoning
    """
    domain_intel = get_domain_intelligence()
    
    # Try to extract asset class from context
    asset_class = AssetClass.UNKNOWN
    trading_context = TradingContext.UNKNOWN
    
    if context:
        # Simple context parsing - in real implementation this would be more sophisticated
        context_lower = context.lower()
        if "commodity" in context_lower or "oil" in context_lower or "gas" in context_lower:
            asset_class = AssetClass.COMMODITIES
        elif "fx" in context_lower or "currency" in context_lower:
            asset_class = AssetClass.FX
        elif "rate" in context_lower or "swap" in context_lower:
            asset_class = AssetClass.RATES
        elif "option" in context_lower or "derivative" in context_lower:
            asset_class = AssetClass.DERIVATIVES
    
    # Normalize field names using domain intelligence
    norm_field1, conf1 = domain_intel.normalize_field_name(field1_name, asset_class, trading_context)
    norm_field2, conf2 = domain_intel.normalize_field_name(field2_name, asset_class, trading_context)
    
    # Calculate field name similarity
    if norm_field1.lower() == norm_field2.lower():
        field_name_similarity = 1.0
        is_semantic_match = True
    else:
        # Use fuzzy matching for field names
        field_name_similarity = SequenceMatcher(None, norm_field1.lower(), norm_field2.lower()).ratio()
        is_semantic_match = field_name_similarity >= 0.85
    
    # Determine if fields are semantically equivalent
    if is_semantic_match:
        # Compare values
        if field1_value is None and field2_value is None:
            match_status = "MATCHED"
            confidence = 1.0
            reasoning = "Both values are null"
        elif field1_value is None or field2_value is None:
            match_status = "MISSING"
            confidence = 0.0
            reasoning = "One value is missing"
        elif str(field1_value).lower() == str(field2_value).lower():
            match_status = "MATCHED"
            confidence = 1.0
            reasoning = "Exact value match"
        else:
            # Try numeric comparison with tolerance
            try:
                val1 = float(field1_value)
                val2 = float(field2_value)
                pct_diff = abs(val1 - val2) / abs(val1) if val1 != 0 else (1.0 if val2 != 0 else 0.0)
                
                # Use asset class specific tolerances
                tolerance = 0.001  # Default 0.1%
                if asset_class == AssetClass.COMMODITIES:
                    tolerance = 0.005  # 0.5% for commodities
                elif asset_class == AssetClass.FX:
                    tolerance = 0.0001  # 0.01% for FX rates
                elif asset_class == AssetClass.RATES:
                    tolerance = 0.000001  # Very tight for rates (1 basis point)
                
                if pct_diff <= tolerance:
                    match_status = "MATCHED"
                    confidence = 0.95
                    reasoning = f"Numeric values match within {asset_class.value} tolerance (diff: {pct_diff:.4%})"
                else:
                    match_status = "MISMATCHED"
                    confidence = 0.8
                    reasoning = f"Numeric values differ by {pct_diff:.4%} (tolerance: {tolerance:.4%})"
            except (ValueError, TypeError):
                # String comparison with domain-aware normalization
                string_similarity = SequenceMatcher(None, str(field1_value), str(field2_value)).ratio()
                if string_similarity >= 0.85:
                    match_status = "MATCHED"
                    confidence = string_similarity
                    reasoning = f"String similarity: {string_similarity:.2%}"
                else:
                    match_status = "MISMATCHED"
                    confidence = string_similarity
                    reasoning = f"String similarity too low: {string_similarity:.2%}"
    else:
        match_status = "SEMANTIC_MISMATCH"
        confidence = field_name_similarity
        reasoning = f"Field names not semantically equivalent (similarity: {field_name_similarity:.2%})"
        
        # Add domain intelligence insights
        if norm_field1 != field1_name or norm_field2 != field2_name:
            reasoning += f" (normalized: {norm_field1} vs {norm_field2})"
    
    return {
        "match_status": match_status,
        "confidence": confidence,
        "reasoning": reasoning,
        "field_name_similarity": field_name_similarity,
        "method": "deterministic_enhanced",
        "domain_insights": {
            "normalized_field1": norm_field1,
            "normalized_field2": norm_field2,
            "normalization_confidence1": conf1,
            "normalization_confidence2": conf2,
            "asset_class": asset_class.value,
            "trading_context": trading_context.value
        }
    }


@tool
async def ai_analyze_trade_context(
    trade_data: Dict[str, Any],
    mode: str = "deterministic"
) -> Dict[str, Any]:
    """
    Analyze trade context using AI or deterministic rules based on mode.
    
    This tool supports three modes:
    - deterministic: Uses rule-based analysis only
    - llm: Uses AI provider for intelligent analysis
    - hybrid: Combines deterministic and AI analysis
    
    Args:
        trade_data: Trade information to analyze
        ai_provider: Configured AI provider adapter (required for LLM and hybrid modes)
        mode: Analysis mode ("deterministic", "llm", or "hybrid")
    
    Returns:
        Dict containing transaction type, critical fields, field mappings, and context metadata
    """
    logger.info(f"Analyzing trade context in {mode} mode")
    
    # For now, always use deterministic mode since AI provider is not passed
    # In a real implementation, the AI provider would be configured globally
    # or passed through a different mechanism
    if mode == "deterministic":
        return _deterministic_trade_analysis(trade_data)
    
    elif mode == "llm":
        logger.warning("LLM mode requested but AI provider not available, falling back to deterministic")
        return _deterministic_trade_analysis(trade_data)
        
        # This would be the AI implementation:
        # try:
        #     result = await robust_ai_operation(
        #         ai_provider,
        #         "analyze_document_context",
        #         _deterministic_trade_analysis,
        #         trade_data
        #     )
        #     
        #     # Convert AI result to expected format
        #     if hasattr(result, '__dict__'):
        #         return {
        #             "transaction_type": result.transaction_type,
        #             "critical_fields": result.critical_fields,
        #             "field_mappings": result.field_mappings,
        #             "confidence": result.confidence,
        #             "method": "llm",
        #             "context_metadata": result.context_metadata
        #         }
        #     else:
        #         return result
        #         
        # except Exception as e:
        #     logger.error(f"AI analysis failed: {e}")
        #     return _deterministic_trade_analysis(trade_data)
    
    elif mode == "hybrid":
        # Get deterministic result (AI would be combined in real implementation)
        deterministic_result = _deterministic_trade_analysis(trade_data)
        logger.warning("Hybrid mode requested but AI provider not available, using deterministic only")
        return deterministic_result
        
        # This would be the AI implementation:
        # try:
        #     ai_result = await robust_ai_operation(
        #         ai_provider,
        #         "analyze_document_context",
        #         lambda x: deterministic_result,
        #         trade_data
        #     )
        #     
        #     # Convert AI result if needed
        #     if hasattr(ai_result, '__dict__'):
        #         ai_result = {
        #             "transaction_type": ai_result.transaction_type,
        #             "critical_fields": ai_result.critical_fields,
        #             "field_mappings": ai_result.field_mappings,
        #             "confidence": ai_result.confidence,
        #             "method": "llm",
        #             "context_metadata": ai_result.context_metadata
        #         }
        #     
        #     # Merge results - prefer AI if confidence is high, otherwise use deterministic
        #     if ai_result.get("confidence", 0) > 0.8:
        #         merged_result = ai_result.copy()
        #         # Combine critical fields from both approaches
        #         combined_fields = list(set(
        #             deterministic_result["critical_fields"] + 
        #             ai_result.get("critical_fields", [])
        #         ))
        #         merged_result["critical_fields"] = combined_fields
        #         merged_result["method"] = "hybrid_ai_preferred"
        #     else:
        #         merged_result = deterministic_result.copy()
        #         # Add AI insights to metadata
        #         merged_result["context_metadata"]["ai_insights"] = ai_result
        #         merged_result["method"] = "hybrid_deterministic_preferred"
        #     
        #     return merged_result
        #     
        # except Exception as e:
        #     logger.error(f"Hybrid analysis AI component failed: {e}")
        #     deterministic_result["method"] = "hybrid_fallback"
        #     return deterministic_result
    
    else:
        raise ValueError(f"Unsupported analysis mode: {mode}")


@tool
async def context_aware_field_extraction(
    trade_data: Dict[str, Any],
    asset_class: str = None,
    trading_context: str = None
) -> Dict[str, Any]:
    """
    Extract and prioritize fields based on asset class and trading context.
    
    Args:
        trade_data: Trade data dictionary
        asset_class: Optional asset class hint
        trading_context: Optional trading context hint
        
    Returns:
        Dict with extracted fields, priorities, and context information
    """
    domain_intel = get_domain_intelligence()
    
    # Get domain context
    domain_context = domain_intel.get_domain_context(trade_data)
    
    # Override with provided hints if available
    if asset_class:
        try:
            domain_context.asset_class = AssetClass(asset_class.lower())
        except ValueError:
            logger.warning(f"Invalid asset class hint: {asset_class}")
    
    if trading_context:
        try:
            domain_context.trading_context = TradingContext(trading_context.lower())
        except ValueError:
            logger.warning(f"Invalid trading context hint: {trading_context}")
    
    # Extract and normalize field names
    normalized_fields = {}
    field_priorities = {}
    
    for field_name, field_value in trade_data.items():
        normalized_name, confidence = domain_intel.normalize_field_name(
            field_name, 
            domain_context.asset_class, 
            domain_context.trading_context
        )
        
        normalized_fields[normalized_name] = {
            "original_name": field_name,
            "value": field_value,
            "normalization_confidence": confidence
        }
        
        # Get priority for this field
        field_priority = None
        for priority in domain_context.field_priorities:
            if priority.field_name == normalized_name:
                field_priority = priority
                break
        
        if field_priority:
            field_priorities[normalized_name] = {
                "priority_score": field_priority.priority_score,
                "criticality": field_priority.criticality,
                "validation_rules": field_priority.validation_rules
            }
        else:
            # Default priority for unknown fields
            field_priorities[normalized_name] = {
                "priority_score": 0.5,
                "criticality": "OPTIONAL",
                "validation_rules": []
            }
    
    # Sort fields by priority
    sorted_fields = sorted(
        normalized_fields.keys(),
        key=lambda f: field_priorities[f]["priority_score"],
        reverse=True
    )
    
    return {
        "asset_class": domain_context.asset_class.value,
        "trading_context": domain_context.trading_context.value,
        "normalized_fields": normalized_fields,
        "field_priorities": field_priorities,
        "sorted_fields": sorted_fields,
        "critical_fields": [
            f for f in sorted_fields 
            if field_priorities[f]["criticality"] == "CRITICAL"
        ],
        "important_fields": [
            f for f in sorted_fields 
            if field_priorities[f]["criticality"] == "IMPORTANT"
        ],
        "market_conventions": domain_context.market_conventions,
        "validation_rules": domain_context.validation_rules
    }


@tool
async def detect_asset_class_and_context(
    trade_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Detect asset class and trading context from trade data.
    
    Args:
        trade_data: Trade data dictionary
        
    Returns:
        Dict with detected asset class, trading context, and confidence scores
    """
    domain_intel = get_domain_intelligence()
    
    # Detect asset class
    asset_class, ac_confidence = domain_intel.detect_asset_class(trade_data)
    
    # Detect trading context
    trading_context, tc_confidence = domain_intel.detect_trading_context(trade_data, asset_class)
    
    # Get domain context for additional insights
    domain_context = domain_intel.get_domain_context(trade_data)
    
    return {
        "asset_class": asset_class.value,
        "asset_class_confidence": ac_confidence,
        "trading_context": trading_context.value,
        "trading_context_confidence": tc_confidence,
        "detection_method": "pattern_and_field_analysis",
        "market_conventions": domain_context.market_conventions,
        "recommended_field_priorities": [
            {
                "field_name": fp.field_name,
                "priority_score": fp.priority_score,
                "criticality": fp.criticality
            }
            for fp in domain_context.field_priorities[:10]
        ],
        "terminology_mappings_count": len(domain_context.terminology_mappings),
        "validation_rules": domain_context.validation_rules
    }


@tool
async def normalize_market_terminology(
    field_name: str,
    field_value: Any,
    asset_class: str = None,
    trading_context: str = None,
    learn_from_usage: bool = True
) -> Dict[str, Any]:
    """
    Normalize field names and values using market terminology intelligence.
    
    Args:
        field_name: Original field name
        field_value: Field value
        asset_class: Optional asset class context
        trading_context: Optional trading context
        learn_from_usage: Whether to learn from this usage
        
    Returns:
        Dict with normalized field name, value insights, and confidence
    """
    domain_intel = get_domain_intelligence()
    
    # Parse asset class and trading context
    ac = AssetClass.UNKNOWN
    tc = TradingContext.UNKNOWN
    
    if asset_class:
        try:
            ac = AssetClass(asset_class.lower())
        except ValueError:
            logger.warning(f"Invalid asset class: {asset_class}")
    
    if trading_context:
        try:
            tc = TradingContext(trading_context.lower())
        except ValueError:
            logger.warning(f"Invalid trading context: {trading_context}")
    
    # Normalize field name
    normalized_name, confidence = domain_intel.normalize_field_name(field_name, ac, tc)
    
    # Analyze field value for additional insights
    value_insights = _analyze_field_value(field_name, field_value, ac, tc)
    
    # Learn from usage if enabled
    if learn_from_usage and normalized_name != field_name and confidence > 0.7:
        domain_intel.learn_terminology(field_name, normalized_name, ac, tc, confidence)
    
    return {
        "original_field_name": field_name,
        "normalized_field_name": normalized_name,
        "normalization_confidence": confidence,
        "field_value": field_value,
        "value_insights": value_insights,
        "asset_class": ac.value,
        "trading_context": tc.value,
        "learned": learn_from_usage and normalized_name != field_name
    }


@tool
async def explain_terminology_difference(
    term1: str,
    term2: str,
    asset_class: str = None,
    trading_context: str = None
) -> Dict[str, Any]:
    """
    Explain the difference or equivalence between two financial terms.
    
    Args:
        term1: First term
        term2: Second term
        asset_class: Optional asset class context
        trading_context: Optional trading context
        
    Returns:
        Dict with explanation, equivalence assessment, and context
    """
    domain_intel = get_domain_intelligence()
    
    # Parse contexts
    ac = AssetClass.UNKNOWN
    tc = TradingContext.UNKNOWN
    
    if asset_class:
        try:
            ac = AssetClass(asset_class.lower())
        except ValueError:
            pass
    
    if trading_context:
        try:
            tc = TradingContext(trading_context.lower())
        except ValueError:
            pass
    
    # Normalize both terms
    norm_term1, conf1 = domain_intel.normalize_field_name(term1, ac, tc)
    norm_term2, conf2 = domain_intel.normalize_field_name(term2, ac, tc)
    
    # Check if they normalize to the same standard term
    are_equivalent = norm_term1.lower() == norm_term2.lower()
    
    # Calculate similarity
    similarity = domain_intel._calculate_field_similarity(term1.lower(), term2.lower())
    
    # Generate explanation
    if are_equivalent:
        explanation = f"'{term1}' and '{term2}' are equivalent terms in {ac.value} trading. "
        explanation += f"Both normalize to the standard term '{norm_term1}'."
        
        if ac != AssetClass.UNKNOWN:
            explanation += f" In {ac.value} markets, these terms are commonly used interchangeably."
    else:
        explanation = f"'{term1}' and '{term2}' are different terms in {ac.value} trading. "
        explanation += f"'{term1}' normalizes to '{norm_term1}' while '{term2}' normalizes to '{norm_term2}'."
        
        if similarity > 0.5:
            explanation += f" However, they have {similarity:.1%} similarity and may be related concepts."
    
    return {
        "term1": term1,
        "term2": term2,
        "normalized_term1": norm_term1,
        "normalized_term2": norm_term2,
        "are_equivalent": are_equivalent,
        "similarity_score": similarity,
        "explanation": explanation,
        "asset_class": ac.value,
        "trading_context": tc.value,
        "confidence1": conf1,
        "confidence2": conf2
    }


def _analyze_field_value(field_name: str, field_value: Any, 
                        asset_class: AssetClass, trading_context: TradingContext) -> Dict[str, Any]:
    """Analyze field value for domain-specific insights"""
    insights = {
        "data_type": type(field_value).__name__,
        "is_numeric": False,
        "is_date": False,
        "is_currency": False,
        "validation_status": "unknown"
    }
    
    if field_value is None:
        insights["validation_status"] = "missing"
        return insights
    
    value_str = str(field_value).strip()
    
    # Check if numeric
    try:
        float_val = float(field_value)
        insights["is_numeric"] = True
        insights["numeric_value"] = float_val
        
        # Asset class specific validations
        if asset_class == AssetClass.FX and "rate" in field_name.lower():
            if 0.0001 <= float_val <= 1000:  # Reasonable FX rate range
                insights["validation_status"] = "valid"
            else:
                insights["validation_status"] = "suspicious_range"
        elif asset_class == AssetClass.COMMODITIES and "price" in field_name.lower():
            if float_val > 0:
                insights["validation_status"] = "valid"
            else:
                insights["validation_status"] = "invalid_negative"
        elif "notional" in field_name.lower() or "amount" in field_name.lower():
            if float_val > 0:
                insights["validation_status"] = "valid"
            else:
                insights["validation_status"] = "invalid_negative"
    except (ValueError, TypeError):
        pass
    
    # Check if date
    date_patterns = [
        r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
        r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
        r'\d{2}-\d{2}-\d{4}'   # MM-DD-YYYY
    ]
    
    for pattern in date_patterns:
        if re.match(pattern, value_str):
            insights["is_date"] = True
            insights["validation_status"] = "valid_date_format"
            break
    
    # Check if currency
    currency_pattern = r'^[A-Z]{3}$'
    if re.match(currency_pattern, value_str):
        insights["is_currency"] = True
        insights["validation_status"] = "valid_currency_code"
    
    return insights


@tool
async def semantic_field_match(
    field1_name: str,
    field1_value: str,
    field2_name: str,
    field2_value: str,
    mode: str = "deterministic",
    context: str = ""
) -> Dict[str, Any]:
    """
    Compare fields using semantic understanding or exact matching based on mode.
    
    Args:
        field1_name: First field name
        field1_value: First field value
        field2_name: Second field name
        field2_value: Second field value
        ai_provider: Configured AI provider adapter (required for LLM and hybrid modes)
        mode: Matching mode ("deterministic", "llm", or "hybrid")
        context: Optional context information (e.g., transaction type)
    
    Returns:
        Dict with match_status, confidence, reasoning, and method used
    """
    logger.debug(f"Comparing fields '{field1_name}' and '{field2_name}' in {mode} mode")
    
    if mode == "deterministic":
        return _deterministic_field_match(field1_name, field1_value, field2_name, field2_value)
    
    elif mode == "llm":
        if not ai_provider:
            logger.warning("AI provider not available for LLM mode, falling back to deterministic")
            return _deterministic_field_match(field1_name, field1_value, field2_name, field2_value)
        
        try:
            # First check semantic similarity of field names
            semantic_result = await robust_ai_operation(
                ai_provider,
                "semantic_field_matching",
                lambda f1, f2, ctx: {"similarity_score": 0.0, "is_match": False, "reasoning": "Fallback", "confidence": 0.3},
                field1_name,
                field2_name,
                context
            )
            
            # Convert result if needed
            if hasattr(semantic_result, '__dict__'):
                semantic_score = semantic_result.similarity_score
                is_semantic_match = semantic_result.is_match
                semantic_reasoning = semantic_result.reasoning
            else:
                semantic_score = semantic_result.get("similarity_score", 0.0)
                is_semantic_match = semantic_result.get("is_match", False)
                semantic_reasoning = semantic_result.get("reasoning", "No reasoning provided")
            
            if semantic_score > 0.85 or is_semantic_match:
                # Fields are semantically similar, now compare values using AI
                trade1_data = {field1_name: field1_value}
                trade2_data = {field2_name: field2_value}
                
                match_result = await robust_ai_operation(
                    ai_provider,
                    "intelligent_trade_matching",
                    lambda t1, t2: {"match_confidence": 0.0, "overall_status": "UNCERTAIN", "reasoning": "Fallback"},
                    trade1_data,
                    trade2_data
                )
                
                # Convert result if needed
                if hasattr(match_result, '__dict__'):
                    return {
                        "match_status": match_result.overall_status,
                        "confidence": match_result.match_confidence,
                        "reasoning": f"Semantic match: {semantic_reasoning}. Value comparison: {match_result.reasoning}",
                        "field_name_similarity": semantic_score,
                        "method": "llm"
                    }
                else:
                    return {
                        "match_status": match_result.get("overall_status", "UNCERTAIN"),
                        "confidence": match_result.get("match_confidence", 0.0),
                        "reasoning": f"Semantic match: {semantic_reasoning}. Value comparison: {match_result.get('reasoning', 'No reasoning')}",
                        "field_name_similarity": semantic_score,
                        "method": "llm"
                    }
            else:
                return {
                    "match_status": "SEMANTIC_MISMATCH",
                    "confidence": semantic_score,
                    "reasoning": f"Field names not semantically equivalent: {semantic_reasoning}",
                    "field_name_similarity": semantic_score,
                    "method": "llm"
                }
                
        except Exception as e:
            logger.error(f"AI semantic matching failed: {e}")
            return _deterministic_field_match(field1_name, field1_value, field2_name, field2_value)
    
    elif mode == "hybrid":
        # Try deterministic first for exact matches
        det_result = _deterministic_field_match(field1_name, field1_value, field2_name, field2_value)
        
        # If deterministic is confident, use it
        if det_result["confidence"] >= 0.9:
            det_result["method"] = "hybrid_deterministic"
            return det_result
        
        # Otherwise, try AI for uncertain cases
        if ai_provider:
            try:
                ai_result = await semantic_field_match(
                    field1_name, field1_value, field2_name, field2_value,
                    ai_provider, "llm", context
                )
                
                # Prefer AI result if it's more confident
                if ai_result.get("confidence", 0) > det_result["confidence"]:
                    ai_result["method"] = "hybrid_ai"
                    return ai_result
                else:
                    det_result["method"] = "hybrid_deterministic_preferred"
                    det_result["ai_insights"] = ai_result
                    return det_result
                    
            except Exception as e:
                logger.error(f"Hybrid mode AI component failed: {e}")
                det_result["method"] = "hybrid_fallback"
                return det_result
        else:
            det_result["method"] = "hybrid_no_ai"
            return det_result
    
    else:
        raise ValueError(f"Unsupported matching mode: {mode}")


@tool
async def intelligent_trade_matching(
    trade1: Dict[str, Any],
    trade2: Dict[str, Any],
    mode: str = "deterministic",
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Perform intelligent trade matching that combines traditional and AI-based matching.
    
    Args:
        trade1: First trade data dictionary
        trade2: Second trade data dictionary
        ai_provider: Configured AI provider adapter (required for LLM and hybrid modes)
        mode: Matching mode ("deterministic", "llm", or "hybrid")
        weights: Optional field weights for deterministic matching
    
    Returns:
        Dict with match_confidence, field_comparisons, overall_status, reasoning, and method
    """
    logger.info(f"Performing intelligent trade matching in {mode} mode")
    
    if weights is None:
        weights = {
            "trade_date": 0.30,
            "total_notional_quantity": 0.25,
            "currency": 0.15,
            "counterparty": 0.20,
            "commodity_type": 0.10
        }
    
    def _deterministic_trade_matching(t1: Dict[str, Any], t2: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic trade matching using weighted field comparison"""
        field_comparisons = {}
        total_score = 0.0
        total_weight = 0.0
        
        for field, weight in weights.items():
            if field in t1 and field in t2:
                field_result = _deterministic_field_match(field, t1[field], field, t2[field])
                field_comparisons[field] = {
                    "status": field_result["match_status"],
                    "confidence": field_result["confidence"],
                    "reasoning": field_result["reasoning"]
                }
                
                if field_result["match_status"] == "MATCHED":
                    total_score += weight * field_result["confidence"]
                total_weight += weight
        
        # Normalize score
        match_confidence = total_score / total_weight if total_weight > 0 else 0.0
        
        # Determine overall status
        if match_confidence >= 0.9:
            overall_status = "MATCHED"
        elif match_confidence >= 0.6:
            overall_status = "PARTIAL_MATCH"
        else:
            overall_status = "MISMATCHED"
        
        return {
            "match_confidence": match_confidence,
            "field_comparisons": field_comparisons,
            "overall_status": overall_status,
            "reasoning": f"Deterministic matching with weighted score: {match_confidence:.2%}",
            "method": "deterministic"
        }
    
    if mode == "deterministic":
        return _deterministic_trade_matching(trade1, trade2)
    
    elif mode == "llm":
        if not ai_provider:
            logger.warning("AI provider not available for LLM mode, falling back to deterministic")
            return _deterministic_trade_matching(trade1, trade2)
        
        try:
            result = await robust_ai_operation(
                ai_provider,
                "intelligent_trade_matching",
                _deterministic_trade_matching,
                trade1,
                trade2
            )
            
            # Convert result if needed
            if hasattr(result, '__dict__'):
                return {
                    "match_confidence": result.match_confidence,
                    "field_comparisons": result.field_comparisons,
                    "overall_status": result.overall_status,
                    "reasoning": result.reasoning,
                    "method": result.method_used
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"AI trade matching failed: {e}")
            return _deterministic_trade_matching(trade1, trade2)
    
    elif mode == "hybrid":
        # Get both deterministic and AI results
        det_result = _deterministic_trade_matching(trade1, trade2)
        
        if not ai_provider:
            logger.warning("AI provider not available for hybrid mode, using deterministic only")
            det_result["method"] = "hybrid_no_ai"
            return det_result
        
        try:
            ai_result = await robust_ai_operation(
                ai_provider,
                "intelligent_trade_matching",
                lambda t1, t2: det_result,
                trade1,
                trade2
            )
            
            # Convert AI result if needed
            if hasattr(ai_result, '__dict__'):
                ai_result = {
                    "match_confidence": ai_result.match_confidence,
                    "field_comparisons": ai_result.field_comparisons,
                    "overall_status": ai_result.overall_status,
                    "reasoning": ai_result.reasoning,
                    "method": ai_result.method_used
                }
            
            # Combine results - use AI if it's more confident and reasonable
            ai_confidence = ai_result.get("match_confidence", 0.0)
            det_confidence = det_result.get("match_confidence", 0.0)
            
            if ai_confidence > det_confidence and ai_confidence > 0.7:
                # Use AI result but include deterministic insights
                ai_result["method"] = "hybrid_ai_preferred"
                ai_result["deterministic_insights"] = det_result
                return ai_result
            else:
                # Use deterministic result but include AI insights
                det_result["method"] = "hybrid_deterministic_preferred"
                det_result["ai_insights"] = ai_result
                return det_result
                
        except Exception as e:
            logger.error(f"Hybrid matching AI component failed: {e}")
            det_result["method"] = "hybrid_fallback"
            return det_result
    
    else:
        raise ValueError(f"Unsupported matching mode: {mode}")


@tool
async def explain_mismatch(
    field_name: str,
    value1: str,
    value2: str,
    context: str = "",
    mode: str = "deterministic"
) -> str:
    """
    Generate human-readable explanations of reconciliation differences.
    
    Args:
        field_name: Name of the field that mismatched
        value1: First value
        value2: Second value
        ai_provider: Configured AI provider adapter (required for LLM mode)
        context: Optional context information (e.g., transaction type)
        mode: Explanation mode ("deterministic", "llm", or "hybrid")
    
    Returns:
        Human-readable explanation string
    """
    logger.debug(f"Generating mismatch explanation for field '{field_name}' in {mode} mode")
    
    def _deterministic_explanation(field: str, val1: Any, val2: Any, ctx: str = "") -> str:
        """Generate deterministic explanation for field mismatch"""
        if val1 is None and val2 is None:
            return f"Both values for '{field}' are missing."
        elif val1 is None:
            return f"Field '{field}' is missing from the first trade (value in second trade: '{val2}')."
        elif val2 is None:
            return f"Field '{field}' is missing from the second trade (value in first trade: '{val1}')."
        
        # Try to determine the type of difference
        try:
            num1 = float(val1)
            num2 = float(val2)
            diff = abs(num1 - num2)
            pct_diff = diff / abs(num1) if num1 != 0 else float('inf')
            
            if pct_diff < 0.001:
                return f"Field '{field}' values are very close: {val1} vs {val2} (difference: {diff:.6f})."
            elif pct_diff < 0.01:
                return f"Field '{field}' has minor numeric difference: {val1} vs {val2} ({pct_diff:.2%} difference)."
            else:
                return f"Field '{field}' has significant numeric difference: {val1} vs {val2} ({pct_diff:.2%} difference)."
                
        except (ValueError, TypeError):
            # String comparison
            str1, str2 = str(val1), str(val2)
            similarity = SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
            
            if similarity > 0.8:
                return f"Field '{field}' has similar but not identical text values: '{val1}' vs '{val2}' ({similarity:.1%} similarity)."
            elif similarity > 0.5:
                return f"Field '{field}' has somewhat similar text values: '{val1}' vs '{val2}' ({similarity:.1%} similarity)."
            else:
                return f"Field '{field}' has completely different values: '{val1}' vs '{val2}'."
    
    if mode == "deterministic":
        return _deterministic_explanation(field_name, value1, value2, context)
    
    elif mode == "llm":
        if not ai_provider:
            logger.warning("AI provider not available for LLM mode, falling back to deterministic")
            return _deterministic_explanation(field_name, value1, value2, context)
        
        try:
            explanation = await robust_ai_operation(
                ai_provider,
                "explain_mismatch",
                _deterministic_explanation,
                field_name,
                value1,
                value2,
                context
            )
            return explanation
            
        except Exception as e:
            logger.error(f"AI explanation failed: {e}")
            return _deterministic_explanation(field_name, value1, value2, context)
    
    elif mode == "hybrid":
        # Get deterministic explanation first
        det_explanation = _deterministic_explanation(field_name, value1, value2, context)
        
        if not ai_provider:
            return det_explanation
        
        try:
            # Try to enhance with AI explanation
            ai_explanation = await robust_ai_operation(
                ai_provider,
                "explain_mismatch",
                lambda f, v1, v2, ctx: det_explanation,
                field_name,
                value1,
                value2,
                context
            )
            
            # If AI provides a more detailed explanation, use it
            if len(ai_explanation) > len(det_explanation) and "fallback" not in ai_explanation.lower():
                return f"{ai_explanation} (Enhanced with AI analysis)"
            else:
                return det_explanation
                
        except Exception as e:
            logger.error(f"Hybrid explanation AI component failed: {e}")
            return det_explanation
    
    else:
        raise ValueError(f"Unsupported explanation mode: {mode}")


@tool
async def context_aware_field_extraction(
    trade_data: Dict[str, Any],
    transaction_type: str,
    mode: str = "deterministic"
) -> Dict[str, Any]:
    """
    Identify relevant fields for comparison based on transaction type and context.
    
    Args:
        trade_data: Trade data dictionary
        transaction_type: Type of transaction (e.g., "commodity_swap", "fx_forward")
        ai_provider: Configured AI provider adapter (required for LLM mode)
        mode: Extraction mode ("deterministic", "llm", or "hybrid")
    
    Returns:
        Dict with extracted_fields, field_priorities, and field_mappings
    """
    logger.info(f"Extracting context-aware fields for {transaction_type} in {mode} mode")
    
    def _deterministic_field_extraction(data: Dict[str, Any], tx_type: str) -> Dict[str, Any]:
        """Deterministic field extraction based on transaction type"""
        # Base fields that are always important
        base_fields = ["trade_date", "currency", "total_notional_quantity"]
        
        # Transaction-type specific fields
        type_specific_fields = {
            "commodity_swap": ["commodity_type", "fixed_price", "settlement_type", "effective_date", "termination_date"],
            "commodity_trade": ["commodity_type", "fixed_price", "settlement_type", "delivery_date"],
            "fx_forward": ["currency_pair", "exchange_rate", "settlement_date"],
            "fx_trade": ["currency_pair", "exchange_rate", "value_date"],
            "interest_rate_swap": ["interest_rate", "floating_rate_index", "payment_frequency", "day_count_convention"],
            "derivative": ["underlying_asset", "option_type", "strike_price", "expiry_date"],
            "bond": ["bond_type", "coupon_rate", "maturity_date", "face_value"],
            "equity": ["equity_symbol", "share_quantity", "share_price"]
        }
        
        # Get fields for this transaction type
        relevant_fields = base_fields + type_specific_fields.get(tx_type, [])
        
        # Filter to only include fields that exist in the data
        extracted_fields = [field for field in relevant_fields if field in data]
        
        # Define field priorities
        field_priorities = {
            "critical": ["trade_date", "total_notional_quantity", "currency"],
            "important": ["commodity_type", "fixed_price", "counterparty", "settlement_date"],
            "optional": ["business_days_convention", "price_unit", "unit_of_measure"]
        }
        
        # Standard field mappings
        field_mappings = {
            "settlement_date": "termination_date",
            "maturity_date": "termination_date",
            "notional": "total_notional_quantity",
            "amount": "total_notional_quantity",
            "counterparty": "buyer_legal_entity",
            "ccy": "currency",
            "rate": "fixed_price"
        }
        
        return {
            "extracted_fields": extracted_fields,
            "field_priorities": field_priorities,
            "field_mappings": field_mappings,
            "transaction_type": tx_type,
            "method": "deterministic"
        }
    
    if mode == "deterministic":
        return _deterministic_field_extraction(trade_data, transaction_type)
    
    elif mode == "llm":
        if not ai_provider:
            logger.warning("AI provider not available for LLM mode, falling back to deterministic")
            return _deterministic_field_extraction(trade_data, transaction_type)
        
        try:
            # Use AI to analyze the document context with transaction type
            enhanced_data = trade_data.copy()
            enhanced_data["_transaction_type"] = transaction_type
            
            result = await robust_ai_operation(
                ai_provider,
                "analyze_document_context",
                lambda data: _deterministic_field_extraction(trade_data, transaction_type),
                enhanced_data
            )
            
            # Convert result if needed
            if hasattr(result, '__dict__'):
                return {
                    "extracted_fields": result.critical_fields,
                    "field_priorities": {
                        "critical": result.critical_fields[:3],
                        "important": result.critical_fields[3:6],
                        "optional": result.critical_fields[6:]
                    },
                    "field_mappings": result.field_mappings,
                    "transaction_type": transaction_type,
                    "method": "llm",
                    "ai_confidence": result.confidence
                }
            else:
                return {
                    "extracted_fields": result.get("critical_fields", []),
                    "field_priorities": {
                        "critical": result.get("critical_fields", [])[:3],
                        "important": result.get("critical_fields", [])[3:6],
                        "optional": result.get("critical_fields", [])[6:]
                    },
                    "field_mappings": result.get("field_mappings", {}),
                    "transaction_type": transaction_type,
                    "method": "llm",
                    "ai_confidence": result.get("confidence", 0.5)
                }
                
        except Exception as e:
            logger.error(f"AI field extraction failed: {e}")
            return _deterministic_field_extraction(trade_data, transaction_type)
    
    elif mode == "hybrid":
        # Get deterministic baseline
        det_result = _deterministic_field_extraction(trade_data, transaction_type)
        
        if not ai_provider:
            det_result["method"] = "hybrid_no_ai"
            return det_result
        
        try:
            # Get AI enhancement
            ai_result = await context_aware_field_extraction(
                trade_data, transaction_type, ai_provider, "llm"
            )
            
            # Merge results - combine field lists and use AI mappings if available
            combined_fields = list(set(
                det_result["extracted_fields"] + 
                ai_result.get("extracted_fields", [])
            ))
            
            # Merge field mappings
            combined_mappings = det_result["field_mappings"].copy()
            combined_mappings.update(ai_result.get("field_mappings", {}))
            
            # Use AI priorities if confidence is high, otherwise use deterministic
            if ai_result.get("ai_confidence", 0) > 0.8:
                field_priorities = ai_result.get("field_priorities", det_result["field_priorities"])
                method = "hybrid_ai_preferred"
            else:
                field_priorities = det_result["field_priorities"]
                method = "hybrid_deterministic_preferred"
            
            return {
                "extracted_fields": combined_fields,
                "field_priorities": field_priorities,
                "field_mappings": combined_mappings,
                "transaction_type": transaction_type,
                "method": method,
                "ai_insights": ai_result,
                "deterministic_baseline": det_result
            }
            
        except Exception as e:
            logger.error(f"Hybrid field extraction AI component failed: {e}")
            det_result["method"] = "hybrid_fallback"
            return det_result
    
    else:
        raise ValueError(f"Unsupported extraction mode: {mode}")


# Utility functions for tool integration

def get_ai_provider_from_config(config: Union[EnhancedMatcherConfig, EnhancedReconcilerConfig]) -> Optional[AIProviderAdapter]:
    """
    Get AI provider instance from configuration.
    
    Args:
        config: Enhanced configuration object
        
    Returns:
        AI provider adapter instance or None if not available
    """
    try:
        provider = AIProviderFactory.create_provider(
            config.ai_provider_config.provider_type,
            {
                "region": config.ai_provider_config.region,
                **config.ai_provider_config.model_config
            }
        )
        return provider
    except Exception as e:
        logger.error(f"Failed to create AI provider: {e}")
        return None


async def initialize_ai_provider_from_config(config: Union[EnhancedMatcherConfig, EnhancedReconcilerConfig]) -> Optional[AIProviderAdapter]:
    """
    Initialize AI provider from configuration.
    
    Args:
        config: Enhanced configuration object
        
    Returns:
        Initialized AI provider adapter or None if initialization fails
    """
    try:
        provider = await AIProviderFactory.create_and_initialize_provider(
            config.ai_provider_config.provider_type,
            {
                "region": config.ai_provider_config.region,
                **config.ai_provider_config.model_config
            },
            fallback_providers=[config.ai_provider_config.fallback_provider] if config.ai_provider_config.fallback_provider else None
        )
        return provider
    except Exception as e:
        logger.error(f"Failed to initialize AI provider: {e}")
        return None
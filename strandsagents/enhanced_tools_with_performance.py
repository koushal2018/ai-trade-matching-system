"""
Enhanced tools with performance optimization integration

This module demonstrates how to integrate the performance optimization features
with the existing enhanced tools for AI-powered trade reconciliation.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from strands import tool

from performance_optimization import (
    optimize_ai_operation, Priority, global_cache, global_metrics_collector,
    get_performance_dashboard
)

logger = logging.getLogger(__name__)


@tool
async def ai_analyze_trade_context_optimized(
    trade_data: Dict[str, Any],
    mode: str = "deterministic",
    priority: str = "normal",
    use_caching: bool = True,
    use_batching: bool = True
) -> Dict[str, Any]:
    """
    Optimized AI-powered trade context analysis with caching, batching, and performance tracking.
    
    Args:
        trade_data: Trade information to analyze
        mode: Analysis mode ("deterministic", "llm", or "hybrid")
        priority: Operation priority ("low", "normal", "high", "urgent")
        use_caching: Whether to use intelligent caching
        use_batching: Whether to use intelligent batching
    
    Returns:
        Dict containing transaction type, critical fields, field mappings, and performance metadata
    """
    start_time = time.time()
    
    # Convert priority string to enum
    priority_map = {
        "low": Priority.LOW,
        "normal": Priority.NORMAL,
        "high": Priority.HIGH,
        "urgent": Priority.URGENT
    }
    priority_enum = priority_map.get(priority.lower(), Priority.NORMAL)
    
    logger.info(f"Analyzing trade context in {mode} mode with {priority} priority")
    
    try:
        if mode == "deterministic":
            # Use deterministic analysis (no AI optimization needed)
            result = _deterministic_trade_analysis(trade_data)
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Record metrics
            global_metrics_collector.record_operation(
                'analyze_context', 'deterministic', processing_time_ms, True, False
            )
            
        elif mode in ["llm", "hybrid"]:
            # Use AI optimization for LLM modes
            if use_caching:
                # Check cache first
                cache_key_data = {**trade_data, "mode": mode}
                cached_result = global_cache.get('analyze_context', cache_key_data)
                if cached_result is not None:
                    logger.debug("Cache hit for trade context analysis")
                    processing_time_ms = (time.time() - start_time) * 1000
                    global_metrics_collector.record_operation(
                        'analyze_context', mode, processing_time_ms, True, True
                    )
                    return cached_result
            
            # Use optimized AI operation
            result = await optimize_ai_operation(
                'analyze_context',
                {**trade_data, "mode": mode},
                priority=priority_enum,
                use_batching=use_batching and priority_enum in [Priority.LOW, Priority.NORMAL]
            )
            
            # Cache result if caching is enabled
            if use_caching and result:
                global_cache.put('analyze_context', {**trade_data, "mode": mode}, result)
        
        else:
            raise ValueError(f"Unsupported analysis mode: {mode}")
        
        # Add performance metadata to result
        processing_time_ms = (time.time() - start_time) * 1000
        if isinstance(result, dict):
            result["performance_metadata"] = {
                "processing_time_ms": processing_time_ms,
                "mode": mode,
                "priority": priority,
                "cache_enabled": use_caching,
                "batch_enabled": use_batching
            }
        
        return result
        
    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000
        global_metrics_collector.record_operation(
            'analyze_context', mode, processing_time_ms, False, False
        )
        logger.error(f"Error in optimized trade context analysis: {e}")
        
        # Fallback to deterministic analysis
        logger.info("Falling back to deterministic analysis")
        fallback_result = _deterministic_trade_analysis(trade_data)
        fallback_result["performance_metadata"] = {
            "processing_time_ms": processing_time_ms,
            "mode": "deterministic_fallback",
            "error": str(e),
            "fallback_used": True
        }
        return fallback_result


@tool
async def semantic_field_match_optimized(
    field1_name: str,
    field1_value: str,
    field2_name: str,
    field2_value: str,
    mode: str = "deterministic",
    context: str = "",
    priority: str = "normal",
    use_caching: bool = True,
    use_batching: bool = True
) -> Dict[str, Any]:
    """
    Optimized semantic field matching with performance optimization.
    
    Args:
        field1_name: First field name
        field1_value: First field value
        field2_name: Second field name
        field2_value: Second field value
        mode: Matching mode ("deterministic", "llm", or "hybrid")
        context: Optional context information
        priority: Operation priority
        use_caching: Whether to use intelligent caching
        use_batching: Whether to use intelligent batching
    
    Returns:
        Dict with match_status, confidence, reasoning, and performance metadata
    """
    start_time = time.time()
    
    # Convert priority string to enum
    priority_map = {
        "low": Priority.LOW,
        "normal": Priority.NORMAL,
        "high": Priority.HIGH,
        "urgent": Priority.URGENT
    }
    priority_enum = priority_map.get(priority.lower(), Priority.NORMAL)
    
    logger.debug(f"Comparing fields '{field1_name}' and '{field2_name}' in {mode} mode")
    
    try:
        if mode == "deterministic":
            # Use deterministic field matching
            result = _deterministic_field_match(field1_name, field1_value, field2_name, field2_value)
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Record metrics
            global_metrics_collector.record_operation(
                'semantic_match', 'deterministic', processing_time_ms, True, False
            )
            
        elif mode in ["llm", "hybrid"]:
            # Prepare data for AI operation
            match_data = {
                "field1_name": field1_name,
                "field1_value": field1_value,
                "field2_name": field2_name,
                "field2_value": field2_value,
                "context": context,
                "mode": mode
            }
            
            if use_caching:
                # Check cache first
                cached_result = global_cache.get('semantic_match', match_data)
                if cached_result is not None:
                    logger.debug("Cache hit for semantic field matching")
                    processing_time_ms = (time.time() - start_time) * 1000
                    global_metrics_collector.record_operation(
                        'semantic_match', mode, processing_time_ms, True, True
                    )
                    return cached_result
            
            # Use optimized AI operation
            result = await optimize_ai_operation(
                'semantic_match',
                match_data,
                priority=priority_enum,
                use_batching=use_batching and priority_enum in [Priority.LOW, Priority.NORMAL]
            )
            
            # Cache result if caching is enabled
            if use_caching and result:
                global_cache.put('semantic_match', match_data, result)
        
        else:
            raise ValueError(f"Unsupported matching mode: {mode}")
        
        # Add performance metadata to result
        processing_time_ms = (time.time() - start_time) * 1000
        if isinstance(result, dict):
            result["performance_metadata"] = {
                "processing_time_ms": processing_time_ms,
                "mode": mode,
                "priority": priority,
                "cache_enabled": use_caching,
                "batch_enabled": use_batching
            }
        
        return result
        
    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000
        global_metrics_collector.record_operation(
            'semantic_match', mode, processing_time_ms, False, False
        )
        logger.error(f"Error in optimized semantic field matching: {e}")
        
        # Fallback to deterministic matching
        logger.info("Falling back to deterministic field matching")
        fallback_result = _deterministic_field_match(field1_name, field1_value, field2_name, field2_value)
        fallback_result["performance_metadata"] = {
            "processing_time_ms": processing_time_ms,
            "mode": "deterministic_fallback",
            "error": str(e),
            "fallback_used": True
        }
        return fallback_result


@tool
async def intelligent_trade_matching_optimized(
    trade1: Dict[str, Any],
    trade2: Dict[str, Any],
    mode: str = "deterministic",
    priority: str = "normal",
    use_caching: bool = True,
    use_batching: bool = True
) -> Dict[str, Any]:
    """
    Optimized intelligent trade matching with performance optimization.
    
    Args:
        trade1: First trade data dictionary
        trade2: Second trade data dictionary
        mode: Matching mode ("deterministic", "llm", or "hybrid")
        priority: Operation priority
        use_caching: Whether to use intelligent caching
        use_batching: Whether to use intelligent batching
    
    Returns:
        Dict with match_confidence, field_comparisons, overall_status, and performance metadata
    """
    start_time = time.time()
    
    # Convert priority string to enum
    priority_map = {
        "low": Priority.LOW,
        "normal": Priority.NORMAL,
        "high": Priority.HIGH,
        "urgent": Priority.URGENT
    }
    priority_enum = priority_map.get(priority.lower(), Priority.NORMAL)
    
    logger.debug(f"Performing intelligent trade matching in {mode} mode")
    
    try:
        if mode == "deterministic":
            # Use deterministic trade matching (simplified)
            result = _deterministic_trade_matching(trade1, trade2)
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Record metrics
            global_metrics_collector.record_operation(
                'intelligent_match', 'deterministic', processing_time_ms, True, False
            )
            
        elif mode in ["llm", "hybrid"]:
            # Prepare data for AI operation
            match_data = {
                "trade1": trade1,
                "trade2": trade2,
                "mode": mode
            }
            
            if use_caching:
                # Check cache first
                cached_result = global_cache.get('intelligent_match', match_data)
                if cached_result is not None:
                    logger.debug("Cache hit for intelligent trade matching")
                    processing_time_ms = (time.time() - start_time) * 1000
                    global_metrics_collector.record_operation(
                        'intelligent_match', mode, processing_time_ms, True, True
                    )
                    return cached_result
            
            # Use optimized AI operation
            result = await optimize_ai_operation(
                'intelligent_match',
                match_data,
                priority=priority_enum,
                use_batching=use_batching and priority_enum in [Priority.LOW, Priority.NORMAL]
            )
            
            # Cache result if caching is enabled
            if use_caching and result:
                global_cache.put('intelligent_match', match_data, result)
        
        else:
            raise ValueError(f"Unsupported matching mode: {mode}")
        
        # Add performance metadata to result
        processing_time_ms = (time.time() - start_time) * 1000
        if isinstance(result, dict):
            result["performance_metadata"] = {
                "processing_time_ms": processing_time_ms,
                "mode": mode,
                "priority": priority,
                "cache_enabled": use_caching,
                "batch_enabled": use_batching
            }
        
        return result
        
    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000
        global_metrics_collector.record_operation(
            'intelligent_match', mode, processing_time_ms, False, False
        )
        logger.error(f"Error in optimized intelligent trade matching: {e}")
        
        # Fallback to deterministic matching
        logger.info("Falling back to deterministic trade matching")
        fallback_result = _deterministic_trade_matching(trade1, trade2)
        fallback_result["performance_metadata"] = {
            "processing_time_ms": processing_time_ms,
            "mode": "deterministic_fallback",
            "error": str(e),
            "fallback_used": True
        }
        return fallback_result


@tool
def get_performance_metrics() -> Dict[str, Any]:
    """
    Get comprehensive performance metrics and dashboard data.
    
    Returns:
        Dict containing performance metrics, cache statistics, and optimization insights
    """
    dashboard = get_performance_dashboard()
    
    # Add additional insights
    cache_stats = dashboard['cache_stats']
    metrics_summary = dashboard['metrics_summary']
    
    insights = {
        "cache_effectiveness": "High" if cache_stats['hit_rate'] > 0.7 else "Medium" if cache_stats['hit_rate'] > 0.3 else "Low",
        "optimization_recommendations": []
    }
    
    # Generate recommendations based on metrics
    if cache_stats['hit_rate'] < 0.3:
        insights["optimization_recommendations"].append(
            "Consider increasing cache size or TTL to improve cache hit rate"
        )
    
    if metrics_summary['overall_stats']['batch_utilization'] < 0.5:
        insights["optimization_recommendations"].append(
            "Consider using batching for more operations to improve throughput"
        )
    
    if metrics_summary['overall_stats']['parallel_utilization'] < 0.3:
        insights["optimization_recommendations"].append(
            "Consider using parallel processing for large volumes to reduce processing time"
        )
    
    dashboard["performance_insights"] = insights
    return dashboard


# Helper functions (simplified versions for demonstration)
def _deterministic_trade_analysis(trade_data: Dict[str, Any]) -> Dict[str, Any]:
    """Simplified deterministic trade analysis"""
    transaction_type = "unknown"
    critical_fields = ["trade_date", "total_notional_quantity", "currency"]
    
    if trade_data.get('commodity_type'):
        transaction_type = "commodity_trade"
        critical_fields.extend(["commodity_type", "settlement_type"])
    elif trade_data.get('currency_pair'):
        transaction_type = "fx_trade"
        critical_fields.extend(["currency_pair", "exchange_rate"])
    
    return {
        "transaction_type": transaction_type,
        "critical_fields": critical_fields,
        "field_mappings": {"settlement_date": "termination_date"},
        "confidence": 0.8,
        "method": "deterministic"
    }


def _deterministic_field_match(field1_name: str, field1_value: str, 
                              field2_name: str, field2_value: str) -> Dict[str, Any]:
    """Simplified deterministic field matching"""
    if field1_name.lower() == field2_name.lower() and field1_value == field2_value:
        return {
            "match_status": "MATCHED",
            "confidence": 1.0,
            "reasoning": "Exact field name and value match",
            "method": "deterministic"
        }
    else:
        return {
            "match_status": "MISMATCHED",
            "confidence": 0.2,
            "reasoning": "Field names or values do not match exactly",
            "method": "deterministic"
        }


def _deterministic_trade_matching(trade1: Dict[str, Any], trade2: Dict[str, Any]) -> Dict[str, Any]:
    """Simplified deterministic trade matching"""
    # Simple matching based on key fields
    key_fields = ['trade_date', 'currency', 'total_notional_quantity']
    matches = 0
    total_fields = 0
    
    for field in key_fields:
        if field in trade1 and field in trade2:
            total_fields += 1
            if trade1[field] == trade2[field]:
                matches += 1
    
    confidence = matches / total_fields if total_fields > 0 else 0.0
    status = "MATCHED" if confidence > 0.8 else "MISMATCHED" if confidence < 0.3 else "UNCERTAIN"
    
    return {
        "match_confidence": confidence,
        "field_comparisons": {field: trade1.get(field) == trade2.get(field) for field in key_fields},
        "overall_status": status,
        "reasoning": f"Matched {matches}/{total_fields} key fields",
        "method": "deterministic"
    }


# Example usage and testing
async def demo_performance_optimization():
    """Demonstrate performance optimization features"""
    print("=== Performance Optimization Demo ===\n")
    
    # Sample trade data
    trade_data = {
        "trade_id": "T123456",
        "trade_date": "2024-01-15",
        "currency": "USD",
        "total_notional_quantity": 1000000,
        "counterparty": "Bank A",
        "commodity_type": "Gold"
    }
    
    print("1. Testing AI-powered trade context analysis with optimization...")
    
    # Test different modes and priorities
    modes = ["deterministic", "llm"]
    priorities = ["normal", "high"]
    
    for mode in modes:
        for priority in priorities:
            print(f"\n   Mode: {mode}, Priority: {priority}")
            
            start_time = time.time()
            result = await ai_analyze_trade_context_optimized(
                trade_data, mode=mode, priority=priority, use_caching=True, use_batching=True
            )
            elapsed = time.time() - start_time
            
            print(f"   Result: {result.get('transaction_type', 'unknown')}")
            print(f"   Processing time: {elapsed:.3f}s")
            if 'performance_metadata' in result:
                print(f"   Metadata: {result['performance_metadata']}")
    
    print("\n2. Testing semantic field matching with optimization...")
    
    # Test field matching
    result = await semantic_field_match_optimized(
        "settlement_date", "2024-01-20",
        "maturity_date", "2024-01-20",
        mode="llm", priority="normal", use_caching=True
    )
    
    print(f"   Match status: {result.get('match_status', 'unknown')}")
    print(f"   Confidence: {result.get('confidence', 0):.2f}")
    if 'performance_metadata' in result:
        print(f"   Metadata: {result['performance_metadata']}")
    
    print("\n3. Testing intelligent trade matching with optimization...")
    
    trade1 = {"trade_id": "T1", "currency": "USD", "amount": 1000000}
    trade2 = {"trade_id": "T2", "currency": "USD", "amount": 1000000}
    
    result = await intelligent_trade_matching_optimized(
        trade1, trade2, mode="llm", priority="high", use_caching=True
    )
    
    print(f"   Match confidence: {result.get('match_confidence', 0):.2f}")
    print(f"   Overall status: {result.get('overall_status', 'unknown')}")
    if 'performance_metadata' in result:
        print(f"   Metadata: {result['performance_metadata']}")
    
    print("\n4. Getting performance metrics...")
    
    metrics = get_performance_metrics()
    print(f"   Cache hit rate: {metrics['cache_stats']['hit_rate']:.2%}")
    print(f"   Total operations: {metrics['metrics_summary']['overall_stats']['total_operations']}")
    print(f"   Cache effectiveness: {metrics['performance_insights']['cache_effectiveness']}")
    
    if metrics['performance_insights']['optimization_recommendations']:
        print("   Recommendations:")
        for rec in metrics['performance_insights']['optimization_recommendations']:
            print(f"     - {rec}")
    
    print("\n=== Demo completed successfully! ===")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run demo
    asyncio.run(demo_performance_optimization())
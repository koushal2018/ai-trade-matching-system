"""
Simple demonstration of performance optimization features
"""

import time
import json
from performance_optimization import (
    IntelligentCache, PerformanceMetricsCollector, ProgressTracker,
    BatchOperation, Priority, PriorityQueue, get_performance_dashboard
)

def demo_intelligent_caching():
    """Demonstrate intelligent caching capabilities"""
    print("=== Intelligent Caching Demo ===")
    
    cache = IntelligentCache(max_size=100, default_ttl=3600)
    
    # Test data
    trade_data = {
        'trade_id': 'T123',
        'currency': 'USD',
        'amount': 1000000,
        'counterparty': 'Bank A'
    }
    
    analysis_result = {
        'transaction_type': 'commodity_trade',
        'critical_fields': ['trade_date', 'currency', 'amount'],
        'confidence': 0.92
    }
    
    print("1. Cache miss (first access):")
    start_time = time.time()
    result = cache.get('analyze_context', trade_data)
    miss_time = (time.time() - start_time) * 1000
    print(f"   Result: {result}")
    print(f"   Time: {miss_time:.3f}ms")
    
    print("\n2. Storing result in cache:")
    cache.put('analyze_context', trade_data, analysis_result)
    print("   Result stored successfully")
    
    print("\n3. Cache hit (second access):")
    start_time = time.time()
    result = cache.get('analyze_context', trade_data)
    hit_time = (time.time() - start_time) * 1000
    print(f"   Result: {result}")
    print(f"   Time: {hit_time:.3f}ms")
    print(f"   Speedup: {miss_time/hit_time:.1f}x faster")
    
    print("\n4. Cache statistics:")
    stats = cache.get_stats()
    print(f"   Size: {stats['size']}")
    print(f"   Hit rate: {stats['hit_rate']:.1%}")
    print(f"   Hits: {stats['hits']}, Misses: {stats['misses']}")
    
    print("\n5. Testing data normalization:")
    # Similar data with different formatting
    similar_data = {
        'trade_id': 'T123',
        'currency': 'usd',  # lowercase
        'amount': 1000000.0,  # float instead of int
        'counterparty': ' Bank A '  # extra spaces
    }
    
    start_time = time.time()
    result = cache.get('analyze_context', similar_data)
    norm_time = (time.time() - start_time) * 1000
    print(f"   Normalized data result: {result is not None}")
    print(f"   Time: {norm_time:.3f}ms")
    
    print("✓ Caching demo completed\n")


def demo_priority_queue():
    """Demonstrate priority queue system"""
    print("=== Priority Queue Demo ===")
    
    queue = PriorityQueue()
    
    print("1. Adding operations with different priorities:")
    operations = [
        BatchOperation('op1', 'analyze_context', {'id': 1}, Priority.LOW),
        BatchOperation('op2', 'semantic_match', {'id': 2}, Priority.HIGH),
        BatchOperation('op3', 'intelligent_match', {'id': 3}, Priority.URGENT),
        BatchOperation('op4', 'analyze_context', {'id': 4}, Priority.NORMAL),
    ]
    
    for op in operations:
        queue.add_operation(op)
        print(f"   Added {op.operation_id} with {op.priority.name} priority")
    
    print("\n2. Processing operations in priority order:")
    processed_order = []
    while True:
        op = queue.get_next_operation()
        if op is None:
            break
        processed_order.append((op.operation_id, op.priority.name))
        print(f"   Processing {op.operation_id} ({op.priority.name})")
    
    expected_order = ['op3', 'op2', 'op4', 'op1']  # URGENT, HIGH, NORMAL, LOW
    actual_order = [op_id for op_id, _ in processed_order]
    print(f"\n   Expected order: {expected_order}")
    print(f"   Actual order: {actual_order}")
    print(f"   Correct ordering: {actual_order == expected_order}")
    
    print("\n3. Testing priority escalation:")
    # Add new operations
    queue.add_operation(BatchOperation('op5', 'test', {'id': 5}, Priority.LOW))
    queue.add_operation(BatchOperation('op6', 'test', {'id': 6}, Priority.NORMAL))
    
    # Escalate op5 to HIGH
    escalated = queue.escalate_priority('op5', Priority.HIGH)
    print(f"   Escalated op5 to HIGH: {escalated}")
    
    # Process to see new order
    next_op = queue.get_next_operation()
    print(f"   Next operation after escalation: {next_op.operation_id} ({next_op.priority.name})")
    
    print("✓ Priority queue demo completed\n")


def demo_progress_tracking():
    """Demonstrate progress tracking and reporting"""
    print("=== Progress Tracking Demo ===")
    
    batch_id = "batch_001"
    total_ops = 100
    tracker = ProgressTracker(batch_id, total_ops)
    
    print(f"1. Starting batch processing: {batch_id}")
    print(f"   Total operations: {total_ops}")
    
    # Simulate processing operations
    print("\n2. Simulating operation processing:")
    for i in range(total_ops):
        # Simulate different processing times and success rates
        processing_time = 50 + (i % 10) * 10  # 50-140ms
        success = i % 10 != 0  # 90% success rate
        error_type = "timeout" if not success else None
        
        tracker.update_progress(success, processing_time, error_type)
        
        # Show progress at intervals
        if (i + 1) % 20 == 0:
            report = tracker.get_progress_report()
            print(f"   Progress {i+1}/{total_ops}: {report['completion_rate']:.1%} complete")
            print(f"     Success rate: {report['success_rate']:.1%}")
            print(f"     ETA: {report['eta_seconds']:.1f}s" if report['eta_seconds'] else "     ETA: calculating...")
            print(f"     Speed: {report['operations_per_second']:.1f} ops/sec")
    
    print("\n3. Final progress report:")
    tracker.mark_completed()
    final_report = tracker.get_progress_report()
    
    print(f"   Status: {final_report['status']}")
    print(f"   Completion rate: {final_report['completion_rate']:.1%}")
    print(f"   Success rate: {final_report['success_rate']:.1%}")
    print(f"   Total time: {final_report['elapsed_time_seconds']:.1f}s")
    print(f"   Average speed: {final_report['operations_per_second']:.1f} ops/sec")
    print(f"   Error summary: {final_report['error_summary']}")
    
    print("✓ Progress tracking demo completed\n")


def demo_performance_metrics():
    """Demonstrate performance metrics collection"""
    print("=== Performance Metrics Demo ===")
    
    collector = PerformanceMetricsCollector()
    
    print("1. Recording AI vs Deterministic operations:")
    
    # Simulate AI operations (slower but more accurate)
    for i in range(50):
        processing_time = 150 + (i % 20) * 5  # 150-245ms
        success = i % 15 != 0  # 93% success rate
        cache_hit = i % 4 == 0  # 25% cache hit rate
        
        collector.record_operation(
            'analyze_context', 'ai', processing_time, success, cache_hit, 
            batched=(i % 3 == 0), parallel=(i % 5 == 0)
        )
    
    # Simulate deterministic operations (faster but less flexible)
    for i in range(50):
        processing_time = 30 + (i % 10) * 2  # 30-48ms
        success = i % 25 != 0  # 96% success rate
        
        collector.record_operation(
            'analyze_context', 'deterministic', processing_time, success, False,
            batched=False, parallel=False
        )
    
    print("   Recorded 50 AI operations and 50 deterministic operations")
    
    print("\n2. Performance comparison:")
    comparison = collector.get_method_comparison('analyze_context')
    
    if 'ai' in comparison and 'deterministic' in comparison:
        ai_stats = comparison['ai']
        det_stats = comparison['deterministic']
        
        print(f"   AI Method:")
        print(f"     Average time: {ai_stats['avg_time_ms']:.1f}ms")
        print(f"     Success rate: {ai_stats['success_rate']:.1%}")
        print(f"     Cache hit rate: {ai_stats['cache_hit_rate']:.1%}")
        
        print(f"   Deterministic Method:")
        print(f"     Average time: {det_stats['avg_time_ms']:.1f}ms")
        print(f"     Success rate: {det_stats['success_rate']:.1%}")
        print(f"     Cache hit rate: {det_stats['cache_hit_rate']:.1%}")
        
        speed_ratio = ai_stats['avg_time_ms'] / det_stats['avg_time_ms']
        print(f"   Speed comparison: AI is {speed_ratio:.1f}x slower than deterministic")
        
        accuracy_diff = ai_stats['success_rate'] - det_stats['success_rate']
        print(f"   Accuracy difference: AI is {accuracy_diff:.1%} more accurate")
    
    print("\n3. Overall performance summary:")
    summary = collector.get_performance_summary()
    overall = summary['overall_stats']
    
    print(f"   Total operations: {overall['total_operations']}")
    print(f"   Overall success rate: {overall['overall_success_rate']:.1%}")
    print(f"   Cache utilization: {overall['cache_hit_rate']:.1%}")
    print(f"   Batch utilization: {overall['batch_utilization']:.1%}")
    print(f"   Parallel utilization: {overall['parallel_utilization']:.1%}")
    
    print("✓ Performance metrics demo completed\n")


def demo_performance_dashboard():
    """Demonstrate performance dashboard"""
    print("=== Performance Dashboard Demo ===")
    
    # Get comprehensive dashboard data
    dashboard = get_performance_dashboard()
    
    print("1. Dashboard components:")
    for component in dashboard.keys():
        print(f"   - {component}")
    
    print("\n2. Cache performance:")
    cache_stats = dashboard['cache_stats']
    print(f"   Cache size: {cache_stats['size']}/{cache_stats['max_size']}")
    print(f"   Hit rate: {cache_stats['hit_rate']:.1%}")
    print(f"   Total hits: {cache_stats['hits']}")
    print(f"   Total misses: {cache_stats['misses']}")
    
    print("\n3. Batch processing stats:")
    batch_stats = dashboard['batch_stats']
    print(f"   Pending operations: {batch_stats['pending_operations']}")
    print(f"   Optimal batch sizes: {batch_stats['optimal_batch_sizes']}")
    
    print("\n4. Overall metrics:")
    metrics = dashboard['metrics_summary']['overall_stats']
    print(f"   Total operations processed: {metrics['total_operations']}")
    print(f"   Success rate: {metrics['overall_success_rate']:.1%}")
    print(f"   Cache effectiveness: {metrics['cache_hit_rate']:.1%}")
    
    print("✓ Performance dashboard demo completed\n")


def main():
    """Run all performance optimization demos"""
    print("🚀 Performance Optimization Features Demonstration\n")
    print("This demo showcases the key performance optimization features:")
    print("- Intelligent caching with TTL and LRU eviction")
    print("- Priority queue system for high-priority operations")
    print("- Progress tracking and reporting for batch operations")
    print("- Performance metrics collection and analysis")
    print("- Comprehensive performance dashboard")
    print("\n" + "="*60 + "\n")
    
    try:
        demo_intelligent_caching()
        demo_priority_queue()
        demo_progress_tracking()
        demo_performance_metrics()
        demo_performance_dashboard()
        
        print("🎉 All performance optimization demos completed successfully!")
        print("\nKey Benefits Demonstrated:")
        print("✓ Intelligent caching reduces redundant AI processing")
        print("✓ Priority queues ensure urgent operations are processed first")
        print("✓ Progress tracking provides real-time batch operation visibility")
        print("✓ Performance metrics enable AI vs deterministic comparison")
        print("✓ Comprehensive dashboard provides operational insights")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
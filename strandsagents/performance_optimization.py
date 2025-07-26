"""
Performance Optimization Features for Enhanced AI Reconciliation

This module implements intelligent batching, caching, parallel processing,
priority queuing, progress tracking, and performance metrics collection
for AI-powered trade reconciliation operations.
"""

import asyncio
import json
import logging
import random
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import pickle
from threading import Lock, RLock
import heapq

logger = logging.getLogger(__name__)


class Priority(Enum):
    """Priority levels for reconciliation operations"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class BatchOperation:
    """Represents a batched AI operation"""
    operation_id: str
    operation_type: str  # 'analyze_context', 'semantic_match', 'intelligent_match', 'explain_mismatch'
    data: Dict[str, Any]
    priority: Priority = Priority.NORMAL
    created_at: float = field(default_factory=time.time)
    timeout: float = 300.0  # 5 minutes default
    callback: Optional[Callable] = None
    
    def __lt__(self, other):
        """For priority queue ordering - heapq is a min-heap, so we need to invert"""
        return self.priority.value > other.priority.value  # Higher priority first


@dataclass
class BatchResult:
    """Result from a batched operation"""
    operation_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    processing_time_ms: float = 0.0
    cache_hit: bool = False


@dataclass
class PerformanceMetrics:
    """Performance metrics for AI vs deterministic processing"""
    operation_type: str
    method: str  # 'ai', 'deterministic', 'hybrid'
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_processing_time_ms: float = 0.0
    avg_processing_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    batch_operations: int = 0
    parallel_operations: int = 0
    
    def update(self, processing_time_ms: float, success: bool, cache_hit: bool = False, 
               batched: bool = False, parallel: bool = False):
        """Update metrics with new operation data"""
        self.total_operations += 1
        if success:
            self.successful_operations += 1
        else:
            self.failed_operations += 1
        
        self.total_processing_time_ms += processing_time_ms
        self.avg_processing_time_ms = self.total_processing_time_ms / self.total_operations
        
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
            
        if batched:
            self.batch_operations += 1
            
        if parallel:
            self.parallel_operations += 1


class CacheEntry:
    """Cache entry with TTL and access tracking"""
    
    def __init__(self, value: Any, ttl_seconds: int = 3600):
        self.value = value
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds
        self.access_count = 0
        self.last_accessed = time.time()
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() - self.created_at > self.ttl_seconds
    
    def access(self) -> Any:
        """Access the cached value and update statistics"""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value


class IntelligentCache:
    """
    Intelligent caching layer for AI analysis results with TTL, LRU eviction,
    and similarity-based cache hits for similar documents.
    """
    
    def __init__(self, max_size: int = 10000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order = deque()  # For LRU eviction
        self.lock = RLock()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expired_removals': 0
        }
    
    def _generate_cache_key(self, operation_type: str, data: Dict[str, Any]) -> str:
        """Generate cache key from operation type and data"""
        # Create a normalized representation of the data for consistent hashing
        normalized_data = self._normalize_data(data)
        data_str = json.dumps(normalized_data, sort_keys=True)
        hash_obj = hashlib.sha256(f"{operation_type}:{data_str}".encode())
        return hash_obj.hexdigest()
    
    def _normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize data for consistent cache key generation"""
        normalized = {}
        for key, value in data.items():
            if isinstance(value, (int, float)):
                # Round numeric values to avoid cache misses due to floating point precision
                normalized[key] = round(float(value), 6)
            elif isinstance(value, str):
                # Normalize strings (strip whitespace, lowercase for certain fields)
                if key.lower() in ['currency', 'counterparty', 'product_type']:
                    normalized[key] = value.strip().upper()
                else:
                    normalized[key] = value.strip()
            elif isinstance(value, dict):
                normalized[key] = self._normalize_data(value)
            elif isinstance(value, list):
                normalized[key] = [self._normalize_data(item) if isinstance(item, dict) else item 
                                 for item in value]
            else:
                normalized[key] = value
        return normalized
    
    def get(self, operation_type: str, data: Dict[str, Any]) -> Optional[Any]:
        """Get cached result if available and not expired"""
        cache_key = self._generate_cache_key(operation_type, data)
        
        with self.lock:
            if cache_key in self.cache:
                entry = self.cache[cache_key]
                if entry.is_expired():
                    del self.cache[cache_key]
                    self.access_order.remove(cache_key)
                    self.stats['expired_removals'] += 1
                    self.stats['misses'] += 1
                    return None
                
                # Move to end of access order (most recently used)
                self.access_order.remove(cache_key)
                self.access_order.append(cache_key)
                
                self.stats['hits'] += 1
                return entry.access()
            
            self.stats['misses'] += 1
            return None
    
    def put(self, operation_type: str, data: Dict[str, Any], result: Any, ttl: Optional[int] = None):
        """Store result in cache with optional TTL override"""
        cache_key = self._generate_cache_key(operation_type, data)
        ttl = ttl or self.default_ttl
        
        with self.lock:
            # Remove existing entry if present
            if cache_key in self.cache:
                self.access_order.remove(cache_key)
            
            # Evict least recently used entries if cache is full
            while len(self.cache) >= self.max_size:
                lru_key = self.access_order.popleft()
                del self.cache[lru_key]
                self.stats['evictions'] += 1
            
            # Add new entry
            self.cache[cache_key] = CacheEntry(result, ttl)
            self.access_order.append(cache_key)
    
    def find_similar(self, operation_type: str, data: Dict[str, Any], 
                    similarity_threshold: float = 0.85) -> Optional[Any]:
        """
        Find similar cached entries for documents with high similarity.
        Useful for avoiding redundant processing of similar trade documents.
        """
        if operation_type != 'analyze_context':
            return None  # Only apply similarity matching for document analysis
        
        with self.lock:
            for cache_key, entry in self.cache.items():
                if entry.is_expired():
                    continue
                
                # Extract original data from cache key (simplified approach)
                # In production, might want to store original data in cache entry
                try:
                    similarity = self._calculate_document_similarity(data, entry.value)
                    if similarity >= similarity_threshold:
                        logger.debug(f"Found similar cached document with similarity {similarity:.3f}")
                        self.stats['hits'] += 1
                        return entry.access()
                except Exception as e:
                    logger.debug(f"Error calculating similarity: {e}")
                    continue
        
        return None
    
    def _calculate_document_similarity(self, doc1: Dict[str, Any], cached_result: Any) -> float:
        """Calculate similarity between documents for cache matching"""
        # Simplified similarity calculation based on key fields
        # In production, this could use more sophisticated similarity metrics
        
        if not hasattr(cached_result, 'get') and not isinstance(cached_result, dict):
            return 0.0
        
        # Compare key fields that indicate document similarity
        key_fields = ['currency', 'counterparty', 'product_type', 'notional_range']
        matches = 0
        total_fields = 0
        
        for field in key_fields:
            if field in doc1:
                total_fields += 1
                # For cached results, we'd need to store original document data
                # This is a simplified implementation
                if field == 'notional_range':
                    # Group notional amounts into ranges for similarity
                    notional = doc1.get('total_notional_quantity', 0)
                    if 0 < notional < 1000000:
                        range1 = 'small'
                    elif 1000000 <= notional < 10000000:
                        range1 = 'medium'
                    else:
                        range1 = 'large'
                    
                    # This would compare against cached document's range
                    # For now, assume 50% similarity for notional ranges
                    matches += 0.5
                else:
                    # For other fields, assume some similarity
                    matches += 0.7
        
        return matches / total_fields if total_fields > 0 else 0.0
    
    def clear_expired(self):
        """Remove all expired entries from cache"""
        with self.lock:
            expired_keys = []
            for key, entry in self.cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
                self.access_order.remove(key)
                self.stats['expired_removals'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            hit_rate = self.stats['hits'] / (self.stats['hits'] + self.stats['misses']) if (self.stats['hits'] + self.stats['misses']) > 0 else 0
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hit_rate': hit_rate,
                **self.stats
            }


class PriorityQueue:
    """
    Priority queue system for high-priority reconciliations with
    support for priority escalation and deadline management.
    """
    
    def __init__(self):
        self.queue = []
        self.entry_finder = {}  # Map operation_id to entry
        self.counter = 0  # Unique sequence count for tie-breaking
        self.lock = Lock()
        self.REMOVED = '<removed-task>'  # Placeholder for removed tasks
    
    def add_operation(self, operation: BatchOperation):
        """Add operation to priority queue"""
        with self.lock:
            if operation.operation_id in self.entry_finder:
                self.remove_operation(operation.operation_id)
            
            count = next(self._counter())
            # Negate priority value for min-heap to get max-heap behavior
            entry = [-operation.priority.value, count, operation]
            self.entry_finder[operation.operation_id] = entry
            heapq.heappush(self.queue, entry)
    
    def remove_operation(self, operation_id: str) -> bool:
        """Remove operation from queue"""
        with self.lock:
            entry = self.entry_finder.pop(operation_id, None)
            if entry is not None:
                entry[-1] = self.REMOVED
                return True
            return False
    
    def get_next_operation(self) -> Optional[BatchOperation]:
        """Get next highest priority operation"""
        with self.lock:
            while self.queue:
                priority, count, operation = heapq.heappop(self.queue)
                if operation is not self.REMOVED:
                    del self.entry_finder[operation.operation_id]
                    return operation
            return None
    
    def escalate_priority(self, operation_id: str, new_priority: Priority) -> bool:
        """Escalate operation priority"""
        with self.lock:
            if operation_id in self.entry_finder:
                entry = self.entry_finder[operation_id]
                operation = entry[-1]
                if operation is not self.REMOVED and new_priority.value > operation.priority.value:
                    # Remove and re-add with new priority
                    self.remove_operation(operation_id)
                    operation.priority = new_priority
                    self.add_operation(operation)
                    return True
            return False
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        with self.lock:
            priority_counts = defaultdict(int)
            total_operations = 0
            
            for entry in self.queue:
                if entry[-1] is not self.REMOVED:
                    total_operations += 1
                    priority_counts[Priority(entry[0]).name] += 1
            
            return {
                'total_operations': total_operations,
                'priority_breakdown': dict(priority_counts),
                'queue_size': len(self.queue)
            }
    
    def _counter(self):
        """Generate unique counter for tie-breaking"""
        while True:
            yield self.counter
            self.counter += 1


class ProgressTracker:
    """
    Progress tracking and reporting for large batch operations with
    real-time updates and ETA calculations.
    """
    
    def __init__(self, batch_id: str, total_operations: int):
        self.batch_id = batch_id
        self.total_operations = total_operations
        self.completed_operations = 0
        self.failed_operations = 0
        self.start_time = time.time()
        self.last_update_time = time.time()
        self.operation_times = deque(maxlen=100)  # Keep last 100 operation times for ETA
        self.status = "RUNNING"
        self.error_summary = defaultdict(int)
        self.lock = Lock()
    
    def update_progress(self, success: bool, processing_time_ms: float, error_type: Optional[str] = None):
        """Update progress with completed operation"""
        with self.lock:
            self.completed_operations += 1
            if not success:
                self.failed_operations += 1
                if error_type:
                    self.error_summary[error_type] += 1
            
            self.operation_times.append(processing_time_ms / 1000.0)  # Convert to seconds
            self.last_update_time = time.time()
    
    def get_progress_report(self) -> Dict[str, Any]:
        """Get current progress report with ETA"""
        with self.lock:
            elapsed_time = time.time() - self.start_time
            completion_rate = self.completed_operations / self.total_operations if self.total_operations > 0 else 0
            
            # Calculate ETA based on recent operation times
            eta_seconds = None
            if self.operation_times and self.completed_operations > 0:
                avg_operation_time = sum(self.operation_times) / len(self.operation_times)
                remaining_operations = self.total_operations - self.completed_operations
                eta_seconds = remaining_operations * avg_operation_time
            
            success_rate = ((self.completed_operations - self.failed_operations) / 
                          self.completed_operations if self.completed_operations > 0 else 0)
            
            return {
                'batch_id': self.batch_id,
                'status': self.status,
                'total_operations': self.total_operations,
                'completed_operations': self.completed_operations,
                'failed_operations': self.failed_operations,
                'completion_rate': completion_rate,
                'success_rate': success_rate,
                'elapsed_time_seconds': elapsed_time,
                'eta_seconds': eta_seconds,
                'operations_per_second': self.completed_operations / elapsed_time if elapsed_time > 0 else 0,
                'error_summary': dict(self.error_summary),
                'last_update': self.last_update_time
            }
    
    def mark_completed(self, status: str = "COMPLETED"):
        """Mark batch as completed"""
        with self.lock:
            self.status = status
    
    def mark_failed(self, error: str):
        """Mark batch as failed"""
        with self.lock:
            self.status = "FAILED"
            self.error_summary["batch_failure"] += 1


class PerformanceMetricsCollector:
    """
    Comprehensive performance metrics collection for AI vs deterministic
    processing times with statistical analysis and reporting.
    """
    
    def __init__(self):
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.lock = RLock()
        self.start_time = time.time()
    
    def record_operation(self, operation_type: str, method: str, processing_time_ms: float,
                        success: bool, cache_hit: bool = False, batched: bool = False,
                        parallel: bool = False):
        """Record performance metrics for an operation"""
        key = f"{operation_type}:{method}"
        
        with self.lock:
            if key not in self.metrics:
                self.metrics[key] = PerformanceMetrics(operation_type, method)
            
            self.metrics[key].update(processing_time_ms, success, cache_hit, batched, parallel)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary with comparisons"""
        with self.lock:
            summary = {
                'collection_start_time': self.start_time,
                'total_runtime_seconds': time.time() - self.start_time,
                'metrics_by_operation': {},
                'method_comparisons': {},
                'overall_stats': {
                    'total_operations': 0,
                    'successful_operations': 0,
                    'cache_hit_rate': 0.0,
                    'batch_utilization': 0.0,
                    'parallel_utilization': 0.0
                }
            }
            
            # Organize metrics by operation type
            operation_groups = defaultdict(dict)
            total_ops = 0
            total_success = 0
            total_cache_hits = 0
            total_batch_ops = 0
            total_parallel_ops = 0
            
            for key, metrics in self.metrics.items():
                operation_type, method = key.split(':', 1)
                operation_groups[operation_type][method] = {
                    'total_operations': metrics.total_operations,
                    'successful_operations': metrics.successful_operations,
                    'failed_operations': metrics.failed_operations,
                    'success_rate': metrics.successful_operations / metrics.total_operations if metrics.total_operations > 0 else 0,
                    'avg_processing_time_ms': metrics.avg_processing_time_ms,
                    'total_processing_time_ms': metrics.total_processing_time_ms,
                    'cache_hits': metrics.cache_hits,
                    'cache_misses': metrics.cache_misses,
                    'cache_hit_rate': metrics.cache_hits / (metrics.cache_hits + metrics.cache_misses) if (metrics.cache_hits + metrics.cache_misses) > 0 else 0,
                    'batch_operations': metrics.batch_operations,
                    'parallel_operations': metrics.parallel_operations
                }
                
                total_ops += metrics.total_operations
                total_success += metrics.successful_operations
                total_cache_hits += metrics.cache_hits
                total_batch_ops += metrics.batch_operations
                total_parallel_ops += metrics.parallel_operations
            
            summary['metrics_by_operation'] = dict(operation_groups)
            
            # Calculate method comparisons
            for operation_type, methods in operation_groups.items():
                if len(methods) > 1:
                    comparison = {}
                    for method, stats in methods.items():
                        comparison[method] = {
                            'avg_time_ms': stats['avg_processing_time_ms'],
                            'success_rate': stats['success_rate'],
                            'total_operations': stats['total_operations']
                        }
                    
                    # Calculate performance improvements
                    if 'ai' in comparison and 'deterministic' in comparison:
                        ai_time = comparison['ai']['avg_time_ms']
                        det_time = comparison['deterministic']['avg_time_ms']
                        if det_time > 0:
                            speed_improvement = ((det_time - ai_time) / det_time) * 100
                            comparison['ai_vs_deterministic'] = {
                                'speed_improvement_percent': speed_improvement,
                                'ai_faster': speed_improvement > 0
                            }
                    
                    summary['method_comparisons'][operation_type] = comparison
            
            # Overall statistics
            summary['overall_stats'] = {
                'total_operations': total_ops,
                'successful_operations': total_success,
                'overall_success_rate': total_success / total_ops if total_ops > 0 else 0,
                'cache_hit_rate': total_cache_hits / total_ops if total_ops > 0 else 0,
                'batch_utilization': total_batch_ops / total_ops if total_ops > 0 else 0,
                'parallel_utilization': total_parallel_ops / total_ops if total_ops > 0 else 0
            }
            
            return summary
    
    def get_method_comparison(self, operation_type: str) -> Dict[str, Any]:
        """Get detailed comparison between AI and deterministic methods for specific operation"""
        with self.lock:
            ai_key = f"{operation_type}:ai"
            det_key = f"{operation_type}:deterministic"
            hybrid_key = f"{operation_type}:hybrid"
            
            comparison = {}
            
            if ai_key in self.metrics:
                ai_metrics = self.metrics[ai_key]
                comparison['ai'] = {
                    'avg_time_ms': ai_metrics.avg_processing_time_ms,
                    'success_rate': ai_metrics.successful_operations / ai_metrics.total_operations if ai_metrics.total_operations > 0 else 0,
                    'total_operations': ai_metrics.total_operations,
                    'cache_hit_rate': ai_metrics.cache_hits / (ai_metrics.cache_hits + ai_metrics.cache_misses) if (ai_metrics.cache_hits + ai_metrics.cache_misses) > 0 else 0
                }
            
            if det_key in self.metrics:
                det_metrics = self.metrics[det_key]
                comparison['deterministic'] = {
                    'avg_time_ms': det_metrics.avg_processing_time_ms,
                    'success_rate': det_metrics.successful_operations / det_metrics.total_operations if det_metrics.total_operations > 0 else 0,
                    'total_operations': det_metrics.total_operations,
                    'cache_hit_rate': det_metrics.cache_hits / (det_metrics.cache_hits + det_metrics.cache_misses) if (det_metrics.cache_hits + det_metrics.cache_misses) > 0 else 0
                }
            
            if hybrid_key in self.metrics:
                hybrid_metrics = self.metrics[hybrid_key]
                comparison['hybrid'] = {
                    'avg_time_ms': hybrid_metrics.avg_processing_time_ms,
                    'success_rate': hybrid_metrics.successful_operations / hybrid_metrics.total_operations if hybrid_metrics.total_operations > 0 else 0,
                    'total_operations': hybrid_metrics.total_operations,
                    'cache_hit_rate': hybrid_metrics.cache_hits / (hybrid_metrics.cache_hits + hybrid_metrics.cache_misses) if (hybrid_metrics.cache_hits + hybrid_metrics.cache_misses) > 0 else 0
                }
            
            return comparison
    
    def reset_metrics(self):
        """Reset all collected metrics"""
        with self.lock:
            self.metrics.clear()
            self.start_time = time.time()


# Global instances
global_cache = IntelligentCache()
global_metrics_collector = PerformanceMetricsCollector()


class IntelligentBatcher:
    """
    Intelligent batching system for AI operations to reduce API calls
    and improve throughput with adaptive batch sizing and timeout management.
    """
    
    def __init__(self, max_batch_size: int = 50, batch_timeout: float = 5.0,
                 adaptive_sizing: bool = True):
        self.max_batch_size = max_batch_size
        self.batch_timeout = batch_timeout
        self.adaptive_sizing = adaptive_sizing
        self.pending_operations: Dict[str, List[BatchOperation]] = defaultdict(list)
        self.batch_timers: Dict[str, float] = {}
        self.priority_queue = PriorityQueue()
        self.lock = asyncio.Lock()
        self.processing_stats = defaultdict(lambda: {'total_time': 0, 'count': 0, 'avg_time': 0})
        self.optimal_batch_sizes = defaultdict(lambda: max_batch_size // 2)  # Start with half max
        
    async def add_operation(self, operation: BatchOperation) -> str:
        """Add operation to batch queue"""
        async with self.lock:
            operation_type = operation.operation_type
            
            # Add to priority queue for high-priority operations
            if operation.priority in [Priority.HIGH, Priority.URGENT]:
                self.priority_queue.add_operation(operation)
                # Process high-priority operations immediately
                asyncio.create_task(self._process_priority_operations())
            else:
                # Add to batch queue
                self.pending_operations[operation_type].append(operation)
                
                # Set batch timer if this is the first operation of this type
                if len(self.pending_operations[operation_type]) == 1:
                    self.batch_timers[operation_type] = time.time()
                
                # Check if batch is ready for processing
                if self._should_process_batch(operation_type):
                    asyncio.create_task(self._process_batch(operation_type))
            
            return operation.operation_id
    
    def _should_process_batch(self, operation_type: str) -> bool:
        """Determine if batch should be processed now"""
        batch = self.pending_operations[operation_type]
        
        # Process if batch is full
        optimal_size = self.optimal_batch_sizes[operation_type]
        if len(batch) >= optimal_size:
            return True
        
        # Process if timeout reached
        if operation_type in self.batch_timers:
            elapsed = time.time() - self.batch_timers[operation_type]
            if elapsed >= self.batch_timeout:
                return True
        
        # Process if any operation in batch is approaching timeout
        current_time = time.time()
        for op in batch:
            if current_time - op.created_at >= op.timeout * 0.8:  # 80% of timeout
                return True
        
        return False
    
    async def _process_priority_operations(self):
        """Process high-priority operations immediately"""
        while True:
            operation = self.priority_queue.get_next_operation()
            if operation is None:
                break
            
            # Process single high-priority operation
            start_time = time.time()
            try:
                result = await self._execute_single_operation(operation)
                processing_time = (time.time() - start_time) * 1000
                
                # Record metrics
                global_metrics_collector.record_operation(
                    operation.operation_type, 'ai', processing_time, 
                    result.success, result.cache_hit, batched=False, parallel=False
                )
                
                # Execute callback if provided
                if operation.callback:
                    operation.callback(result)
                    
            except Exception as e:
                logger.error(f"Error processing priority operation {operation.operation_id}: {e}")
                if operation.callback:
                    error_result = BatchResult(
                        operation.operation_id, False, error=str(e),
                        processing_time_ms=(time.time() - start_time) * 1000
                    )
                    operation.callback(error_result)
    
    async def _process_batch(self, operation_type: str):
        """Process a batch of operations of the same type"""
        async with self.lock:
            if operation_type not in self.pending_operations or not self.pending_operations[operation_type]:
                return
            
            # Extract batch to process
            batch = self.pending_operations[operation_type].copy()
            self.pending_operations[operation_type].clear()
            
            # Clear batch timer
            if operation_type in self.batch_timers:
                del self.batch_timers[operation_type]
        
        if not batch:
            return
        
        logger.info(f"Processing batch of {len(batch)} {operation_type} operations")
        start_time = time.time()
        
        try:
            # Execute batch operation
            results = await self._execute_batch_operation(operation_type, batch)
            processing_time = (time.time() - start_time) * 1000
            
            # Update adaptive batch sizing
            if self.adaptive_sizing:
                self._update_optimal_batch_size(operation_type, len(batch), processing_time)
            
            # Record metrics and execute callbacks
            for i, operation in enumerate(batch):
                result = results[i] if i < len(results) else BatchResult(
                    operation.operation_id, False, error="Batch processing failed"
                )
                
                global_metrics_collector.record_operation(
                    operation.operation_type, 'ai', processing_time / len(batch),
                    result.success, result.cache_hit, batched=True, parallel=False
                )
                
                if operation.callback:
                    operation.callback(result)
                    
        except Exception as e:
            logger.error(f"Error processing batch for {operation_type}: {e}")
            # Notify all operations in batch of failure
            for operation in batch:
                if operation.callback:
                    error_result = BatchResult(
                        operation.operation_id, False, error=str(e),
                        processing_time_ms=(time.time() - start_time) * 1000
                    )
                    operation.callback(error_result)
    
    async def _execute_single_operation(self, operation: BatchOperation) -> BatchResult:
        """Execute a single operation"""
        start_time = time.time()
        
        try:
            # Check cache first
            cached_result = global_cache.get(operation.operation_type, operation.data)
            if cached_result is not None:
                return BatchResult(
                    operation.operation_id, True, cached_result,
                    processing_time_ms=(time.time() - start_time) * 1000,
                    cache_hit=True
                )
            
            # Execute operation (this would call the actual AI provider)
            # For now, simulate the operation
            result = await self._simulate_ai_operation(operation.operation_type, operation.data)
            
            # Cache the result
            global_cache.put(operation.operation_type, operation.data, result)
            
            return BatchResult(
                operation.operation_id, True, result,
                processing_time_ms=(time.time() - start_time) * 1000,
                cache_hit=False
            )
            
        except Exception as e:
            return BatchResult(
                operation.operation_id, False, error=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    async def _execute_batch_operation(self, operation_type: str, 
                                     batch: List[BatchOperation]) -> List[BatchResult]:
        """Execute a batch of operations efficiently"""
        results = []
        
        # Check cache for all operations first
        cache_hits = []
        cache_misses = []
        
        for operation in batch:
            cached_result = global_cache.get(operation.operation_type, operation.data)
            if cached_result is not None:
                cache_hits.append((operation, cached_result))
            else:
                cache_misses.append(operation)
        
        # Process cache hits
        for operation, cached_result in cache_hits:
            results.append(BatchResult(
                operation.operation_id, True, cached_result,
                processing_time_ms=1.0,  # Minimal time for cache hit
                cache_hit=True
            ))
        
        # Process cache misses in batch
        if cache_misses:
            batch_start_time = time.time()
            
            # Group operations by data similarity for more efficient processing
            grouped_operations = self._group_similar_operations(cache_misses)
            
            for group in grouped_operations:
                try:
                    # Simulate batch AI processing
                    group_results = await self._simulate_batch_ai_operation(operation_type, group)
                    
                    # Cache results and create batch results
                    for i, operation in enumerate(group):
                        result = group_results[i] if i < len(group_results) else None
                        if result:
                            global_cache.put(operation.operation_type, operation.data, result)
                            results.append(BatchResult(
                                operation.operation_id, True, result,
                                processing_time_ms=(time.time() - batch_start_time) * 1000 / len(group),
                                cache_hit=False
                            ))
                        else:
                            results.append(BatchResult(
                                operation.operation_id, False, error="Batch processing failed"
                            ))
                            
                except Exception as e:
                    logger.error(f"Error in batch group processing: {e}")
                    for operation in group:
                        results.append(BatchResult(
                            operation.operation_id, False, error=str(e)
                        ))
        
        return results
    
    def _group_similar_operations(self, operations: List[BatchOperation]) -> List[List[BatchOperation]]:
        """Group similar operations for more efficient batch processing"""
        # Simple grouping by operation type and data similarity
        groups = []
        remaining = operations.copy()
        
        while remaining:
            current_op = remaining.pop(0)
            current_group = [current_op]
            
            # Find similar operations
            similar_ops = []
            for op in remaining:
                if self._operations_similar(current_op, op):
                    similar_ops.append(op)
            
            # Remove similar operations from remaining
            for op in similar_ops:
                remaining.remove(op)
                current_group.append(op)
            
            groups.append(current_group)
        
        return groups
    
    def _operations_similar(self, op1: BatchOperation, op2: BatchOperation) -> bool:
        """Check if two operations are similar enough to batch together"""
        if op1.operation_type != op2.operation_type:
            return False
        
        # Check data similarity (simplified)
        common_fields = set(op1.data.keys()) & set(op2.data.keys())
        if len(common_fields) < 2:
            return False
        
        # Check if key fields match
        key_fields = ['currency', 'counterparty', 'product_type']
        matches = 0
        for field in key_fields:
            if field in op1.data and field in op2.data:
                if op1.data[field] == op2.data[field]:
                    matches += 1
        
        return matches >= 2
    
    def _update_optimal_batch_size(self, operation_type: str, batch_size: int, processing_time_ms: float):
        """Update optimal batch size based on performance"""
        stats = self.processing_stats[operation_type]
        stats['total_time'] += processing_time_ms
        stats['count'] += 1
        stats['avg_time'] = stats['total_time'] / stats['count']
        
        # Calculate throughput (operations per second)
        throughput = (batch_size / processing_time_ms) * 1000
        
        current_optimal = self.optimal_batch_sizes[operation_type]
        
        # Adaptive sizing logic
        if throughput > 10:  # Good throughput
            # Increase batch size if we're not at max
            if current_optimal < self.max_batch_size:
                self.optimal_batch_sizes[operation_type] = min(current_optimal + 5, self.max_batch_size)
        elif throughput < 2:  # Poor throughput
            # Decrease batch size
            if current_optimal > 5:
                self.optimal_batch_sizes[operation_type] = max(current_optimal - 5, 5)
        
        logger.debug(f"Updated optimal batch size for {operation_type}: {self.optimal_batch_sizes[operation_type]} "
                    f"(throughput: {throughput:.2f} ops/sec)")
    
    async def _simulate_ai_operation(self, operation_type: str, data: Dict[str, Any]) -> Any:
        """Simulate AI operation for testing"""
        # Add realistic delay
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        if operation_type == 'analyze_context':
            return {
                'transaction_type': 'commodity_trade',
                'critical_fields': ['trade_date', 'notional', 'currency'],
                'confidence': 0.9
            }
        elif operation_type == 'semantic_match':
            return {
                'similarity_score': random.uniform(0.7, 0.95),
                'is_match': True,
                'reasoning': 'Fields are semantically equivalent'
            }
        elif operation_type == 'intelligent_match':
            return {
                'match_confidence': random.uniform(0.8, 0.95),
                'overall_status': 'MATCHED',
                'reasoning': 'High confidence match based on AI analysis'
            }
        else:
            return {'result': 'success', 'confidence': 0.85}
    
    async def _simulate_batch_ai_operation(self, operation_type: str, 
                                         operations: List[BatchOperation]) -> List[Any]:
        """Simulate batch AI operation for testing"""
        # Batch operations are more efficient - less delay per operation
        await asyncio.sleep(len(operations) * 0.05)  # 50ms per operation in batch
        
        results = []
        for operation in operations:
            result = await self._simulate_ai_operation(operation_type, operation.data)
            results.append(result)
        
        return results
    
    def get_batch_stats(self) -> Dict[str, Any]:
        """Get batching statistics"""
        return {
            'pending_operations': {k: len(v) for k, v in self.pending_operations.items()},
            'optimal_batch_sizes': dict(self.optimal_batch_sizes),
            'processing_stats': dict(self.processing_stats),
            'priority_queue_stats': self.priority_queue.get_queue_stats()
        }


class ParallelProcessor:
    """
    Parallel processing capabilities for large document volumes using
    asyncio and concurrent processing with load balancing and resource management.
    """
    
    def __init__(self, max_concurrent_operations: int = 20, max_threads: int = 10):
        self.max_concurrent_operations = max_concurrent_operations
        self.max_threads = max_threads
        self.semaphore = asyncio.Semaphore(max_concurrent_operations)
        self.thread_pool = ThreadPoolExecutor(max_workers=max_threads)
        self.active_operations = set()
        self.operation_stats = defaultdict(lambda: {'completed': 0, 'failed': 0, 'avg_time': 0})
        
    async def process_operations_parallel(self, operations: List[BatchOperation],
                                        progress_callback: Optional[Callable] = None) -> List[BatchResult]:
        """Process multiple operations in parallel with progress tracking"""
        logger.info(f"Starting parallel processing of {len(operations)} operations")
        
        # Create progress tracker
        batch_id = str(uuid.uuid4())
        progress_tracker = ProgressTracker(batch_id, len(operations))
        
        # Group operations by type for better resource utilization
        operation_groups = defaultdict(list)
        for op in operations:
            operation_groups[op.operation_type].append(op)
        
        # Process groups in parallel
        all_tasks = []
        for operation_type, group_operations in operation_groups.items():
            # Create tasks for this group
            group_tasks = [
                self._process_operation_with_semaphore(op, progress_tracker, progress_callback)
                for op in group_operations
            ]
            all_tasks.extend(group_tasks)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*all_tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Operation {operations[i].operation_id} failed: {result}")
                final_results.append(BatchResult(
                    operations[i].operation_id, False, error=str(result)
                ))
            else:
                final_results.append(result)
        
        progress_tracker.mark_completed()
        logger.info(f"Parallel processing completed. Success rate: {progress_tracker.get_progress_report()['success_rate']:.2%}")
        
        return final_results
    
    async def _process_operation_with_semaphore(self, operation: BatchOperation,
                                              progress_tracker: ProgressTracker,
                                              progress_callback: Optional[Callable] = None) -> BatchResult:
        """Process single operation with semaphore for concurrency control"""
        async with self.semaphore:
            operation_id = operation.operation_id
            self.active_operations.add(operation_id)
            
            start_time = time.time()
            try:
                # Check cache first
                cached_result = global_cache.get(operation.operation_type, operation.data)
                if cached_result is not None:
                    result = BatchResult(
                        operation_id, True, cached_result,
                        processing_time_ms=(time.time() - start_time) * 1000,
                        cache_hit=True
                    )
                else:
                    # Process operation
                    if operation.operation_type in ['analyze_context', 'semantic_match']:
                        # CPU-intensive operations - use thread pool
                        result = await self._process_in_thread_pool(operation)
                    else:
                        # I/O-intensive operations - use async
                        result = await self._process_async_operation(operation)
                    
                    # Cache result
                    if result.success:
                        global_cache.put(operation.operation_type, operation.data, result.result)
                
                # Update progress
                processing_time_ms = (time.time() - start_time) * 1000
                progress_tracker.update_progress(result.success, processing_time_ms)
                
                # Record metrics
                global_metrics_collector.record_operation(
                    operation.operation_type, 'ai', processing_time_ms,
                    result.success, result.cache_hit, batched=False, parallel=True
                )
                
                # Update operation stats
                stats = self.operation_stats[operation.operation_type]
                if result.success:
                    stats['completed'] += 1
                else:
                    stats['failed'] += 1
                
                total_ops = stats['completed'] + stats['failed']
                if total_ops > 0:
                    stats['avg_time'] = ((stats['avg_time'] * (total_ops - 1)) + processing_time_ms) / total_ops
                
                # Call progress callback if provided
                if progress_callback:
                    progress_callback(progress_tracker.get_progress_report())
                
                return result
                
            except Exception as e:
                processing_time_ms = (time.time() - start_time) * 1000
                progress_tracker.update_progress(False, processing_time_ms, str(type(e).__name__))
                
                logger.error(f"Error processing operation {operation_id}: {e}")
                return BatchResult(operation_id, False, error=str(e), processing_time_ms=processing_time_ms)
                
            finally:
                self.active_operations.discard(operation_id)
    
    async def _process_in_thread_pool(self, operation: BatchOperation) -> BatchResult:
        """Process CPU-intensive operation in thread pool"""
        loop = asyncio.get_event_loop()
        
        def sync_process():
            # Simulate CPU-intensive processing
            time.sleep(random.uniform(0.1, 0.3))
            return {
                'operation_id': operation.operation_id,
                'result': f'Processed {operation.operation_type}',
                'method': 'thread_pool'
            }
        
        try:
            result = await loop.run_in_executor(self.thread_pool, sync_process)
            return BatchResult(operation.operation_id, True, result)
        except Exception as e:
            return BatchResult(operation.operation_id, False, error=str(e))
    
    async def _process_async_operation(self, operation: BatchOperation) -> BatchResult:
        """Process I/O-intensive operation asynchronously"""
        try:
            # Simulate async I/O operation
            await asyncio.sleep(random.uniform(0.05, 0.2))
            
            result = {
                'operation_id': operation.operation_id,
                'result': f'Processed {operation.operation_type}',
                'method': 'async'
            }
            
            return BatchResult(operation.operation_id, True, result)
        except Exception as e:
            return BatchResult(operation.operation_id, False, error=str(e))
    
    def get_parallel_stats(self) -> Dict[str, Any]:
        """Get parallel processing statistics"""
        return {
            'max_concurrent_operations': self.max_concurrent_operations,
            'active_operations': len(self.active_operations),
            'operation_stats': dict(self.operation_stats),
            'thread_pool_stats': {
                'max_workers': self.thread_pool._max_workers,
                'active_threads': len(self.thread_pool._threads) if hasattr(self.thread_pool, '_threads') else 0
            }
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.thread_pool.shutdown(wait=True)


# Global instances for performance optimization
global_batcher = IntelligentBatcher()
global_parallel_processor = ParallelProcessor()


# Convenience functions for integration with existing tools
async def optimize_ai_operation(operation_type: str, data: Dict[str, Any], 
                               priority: Priority = Priority.NORMAL,
                               use_batching: bool = True,
                               use_parallel: bool = False) -> Any:
    """
    Optimized AI operation with caching, batching, and parallel processing.
    
    Args:
        operation_type: Type of AI operation
        data: Operation data
        priority: Operation priority
        use_batching: Whether to use intelligent batching
        use_parallel: Whether to use parallel processing
        
    Returns:
        Operation result
    """
    # Check cache first
    cached_result = global_cache.get(operation_type, data)
    if cached_result is not None:
        logger.debug(f"Cache hit for {operation_type}")
        return cached_result
    
    # Create operation
    operation = BatchOperation(
        operation_id=str(uuid.uuid4()),
        operation_type=operation_type,
        data=data,
        priority=priority
    )
    
    if use_batching and priority in [Priority.LOW, Priority.NORMAL]:
        # Use intelligent batching for normal priority operations
        result_future = asyncio.Future()
        
        def callback(result: BatchResult):
            if result.success:
                result_future.set_result(result.result)
            else:
                result_future.set_exception(Exception(result.error))
        
        operation.callback = callback
        await global_batcher.add_operation(operation)
        return await result_future
    
    elif use_parallel:
        # Use parallel processing
        results = await global_parallel_processor.process_operations_parallel([operation])
        result = results[0]
        if result.success:
            return result.result
        else:
            raise Exception(result.error)
    
    else:
        # Process immediately
        start_time = time.time()
        try:
            # Simulate AI operation
            await asyncio.sleep(random.uniform(0.1, 0.5))
            result = {
                'operation_type': operation_type,
                'result': 'success',
                'confidence': 0.9
            }
            
            # Cache result
            global_cache.put(operation_type, data, result)
            
            # Record metrics
            processing_time_ms = (time.time() - start_time) * 1000
            global_metrics_collector.record_operation(
                operation_type, 'ai', processing_time_ms, True, False
            )
            
            return result
            
        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            global_metrics_collector.record_operation(
                operation_type, 'ai', processing_time_ms, False, False
            )
            raise


def get_performance_dashboard() -> Dict[str, Any]:
    """Get comprehensive performance dashboard data"""
    return {
        'cache_stats': global_cache.get_stats(),
        'batch_stats': global_batcher.get_batch_stats(),
        'parallel_stats': global_parallel_processor.get_parallel_stats(),
        'metrics_summary': global_metrics_collector.get_performance_summary(),
        'timestamp': time.time()
    }


def reset_performance_optimization():
    """Reset all performance optimization components"""
    global global_cache, global_batcher, global_parallel_processor, global_metrics_collector
    
    global_cache = IntelligentCache()
    global_batcher = IntelligentBatcher()
    global_parallel_processor.cleanup()
    global_parallel_processor = ParallelProcessor()
    global_metrics_collector.reset_metrics()
    
    logger.info("Performance optimization components reset")
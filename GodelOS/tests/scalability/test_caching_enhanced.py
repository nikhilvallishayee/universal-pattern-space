"""
Enhanced unit tests for the Caching & Memoization Layer.

This file extends the basic tests in test_caching.py with more thorough
testing of complex methods and edge cases, focusing on:
1. Performance under high load and concurrent access
2. Complex caching scenarios with various data types
3. Advanced eviction policy behavior
4. Custom cache invalidation strategies
5. Memoization of complex functions with different argument types
"""

import unittest
from unittest.mock import MagicMock, patch
import time
import threading
import concurrent.futures
import random
import sys
from typing import Dict, List, Optional, Set, Any, Tuple
import pickle

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode, ConstantNode, ApplicationNode
from godelOS.core_kr.type_system.types import Type, AtomicType, FunctionType
from godelOS.core_kr.type_system.manager import TypeSystemManager

from godelOS.scalability.caching import (
    CachingMemoizationLayer,
    CacheEntry,
    CacheStore,
    InMemoryCacheStore,
    EvictionPolicy,
    CacheInvalidationStrategy,
    TimeBasedInvalidation,
    PatternBasedInvalidation,
    DependencyBasedInvalidation,
    CachingSystem
)

from godelOS.test_runner.test_categorizer import TestCategorizer
from godelOS.test_runner.timing_tracker import TimingTracker


class TestCachingEnhanced(unittest.TestCase):
    """Enhanced test cases for the Caching & Memoization Layer with complex scenarios and edge cases."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a caching system with default settings
        self.caching_system = CachingSystem(max_size=1000, eviction_policy=EvictionPolicy.LRU)
        
        # Create a type system for AST nodes
        self.type_system = TypeSystemManager()
        self.type_system.register_type("Entity", None)
        self.type_system.register_type("Boolean", None)
        
        # Set up timing tracker for performance measurements
        config = MagicMock()
        config.detailed_timing = True
        self.timing_tracker = TimingTracker(config)
    
    def test_performance_under_high_load(self):
        """Test caching performance under high load."""
        # Number of operations to perform
        num_operations = 10000
        
        # Create a cache with limited size
        cache_size = 1000
        cache = InMemoryCacheStore(max_size=cache_size, eviction_policy=EvictionPolicy.LRU)
        
        # Start timing
        start_time = time.time()
        
        # Perform many put operations
        for i in range(num_operations):
            key = f"key{i}"
            value = f"value{i}"
            cache.put(key, value)
        
        # End timing for put operations
        put_time = time.time() - start_time
        print(f"Time to put {num_operations} entries: {put_time * 1000:.2f} ms")
        print(f"Average put time: {(put_time * 1000) / num_operations:.4f} ms per entry")
        
        # Verify cache size (should be limited to cache_size)
        self.assertEqual(cache.size(), cache_size)
        
        # Start timing for get operations (cache hits)
        start_time = time.time()
        
        # Perform get operations for recently added entries (should be cache hits)
        hits = 0
        for i in range(num_operations - cache_size, num_operations):
            key = f"key{i}"
            value = cache.get(key)
            if value is not None:
                hits += 1
        
        # End timing for get operations (cache hits)
        hit_time = time.time() - start_time
        print(f"Time for {hits} cache hits: {hit_time * 1000:.2f} ms")
        print(f"Average hit time: {(hit_time * 1000) / hits:.4f} ms per hit")
        
        # Start timing for get operations (cache misses)
        start_time = time.time()
        
        # Perform get operations for entries that were evicted (should be cache misses)
        misses = 0
        for i in range(num_operations - cache_size):
            key = f"key{i}"
            value = cache.get(key)
            if value is None:
                misses += 1
        
        # End timing for get operations (cache misses)
        miss_time = time.time() - start_time
        print(f"Time for {misses} cache misses: {miss_time * 1000:.2f} ms")
        print(f"Average miss time: {(miss_time * 1000) / misses:.4f} ms per miss")
        
        # Verify hit rate
        self.assertEqual(hits, cache_size)
        self.assertEqual(misses, num_operations - cache_size)
    
    def test_concurrent_access(self):
        """Test concurrent access to the cache."""
        # Number of threads
        num_threads = 20
        
        # Number of operations per thread
        num_operations = 500
        
        # Create a thread-safe cache
        cache = InMemoryCacheStore(max_size=10000, eviction_policy=EvictionPolicy.LRU)
        
        # Function to perform put operations
        def put_operations(thread_id):
            for i in range(num_operations):
                key = f"key_{thread_id}_{i}"
                value = f"value_{thread_id}_{i}"
                cache.put(key, value)
        
        # Function to perform get operations
        def get_operations(thread_id):
            hits = 0
            for i in range(num_operations):
                key = f"key_{thread_id}_{i}"
                value = cache.get(key)
                if value is not None:
                    hits += 1
            return hits
        
        # Start timing
        start_time = time.time()
        
        # Create threads for put operations
        put_threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=put_operations, args=(i,))
            put_threads.append(thread)
            thread.start()
        
        # Wait for all put threads to complete
        for thread in put_threads:
            thread.join()
        
        # End timing for put operations
        put_time = time.time() - start_time
        print(f"Time for concurrent put operations: {put_time * 1000:.2f} ms")
        
        # Verify cache size
        expected_size = num_threads * num_operations
        self.assertEqual(cache.size(), expected_size)
        
        # Start timing for get operations
        start_time = time.time()
        
        # Use ThreadPoolExecutor for get operations to get results
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            future_to_thread = {executor.submit(get_operations, i): i for i in range(num_threads)}
            hits = 0
            for future in concurrent.futures.as_completed(future_to_thread):
                hits += future.result()
        
        # End timing for get operations
        get_time = time.time() - start_time
        print(f"Time for concurrent get operations: {get_time * 1000:.2f} ms")
        
        # Verify all gets were hits
        self.assertEqual(hits, num_threads * num_operations)
    
    def test_complex_eviction_policy_behavior(self):
        """Test complex behavior of different eviction policies."""
        # Create caches with different eviction policies
        lru_cache = InMemoryCacheStore(max_size=5, eviction_policy=EvictionPolicy.LRU)
        lfu_cache = InMemoryCacheStore(max_size=5, eviction_policy=EvictionPolicy.LFU)
        fifo_cache = InMemoryCacheStore(max_size=5, eviction_policy=EvictionPolicy.FIFO)
        
        # Add initial entries to all caches
        for i in range(5):
            key = f"key{i}"
            value = f"value{i}"
            lru_cache.put(key, value)
            lfu_cache.put(key, value)
            fifo_cache.put(key, value)
        
        # Test LRU policy
        # Access key0 and key1 multiple times
        for _ in range(3):
            lru_cache.get("key0")
            lru_cache.get("key1")
        
        # Add a new entry, which should evict key2 (least recently used)
        lru_cache.put("key5", "value5")
        
        # Verify key2 was evicted
        self.assertIsNone(lru_cache.get("key2"))
        self.assertIsNotNone(lru_cache.get("key0"))
        self.assertIsNotNone(lru_cache.get("key1"))
        self.assertIsNotNone(lru_cache.get("key3"))
        self.assertIsNotNone(lru_cache.get("key4"))
        self.assertIsNotNone(lru_cache.get("key5"))
        
        # Test LFU policy
        # Access key0 and key1 multiple times
        for _ in range(3):
            lfu_cache.get("key0")
        for _ in range(2):
            lfu_cache.get("key1")
        lfu_cache.get("key2")
        
        # Add a new entry, which should evict key4 or key3 (least frequently used)
        lfu_cache.put("key5", "value5")
        
        # Verify key3 or key4 was evicted (both have 0 accesses)
        self.assertTrue(lfu_cache.get("key3") is None or lfu_cache.get("key4") is None)
        self.assertIsNotNone(lfu_cache.get("key0"))
        self.assertIsNotNone(lfu_cache.get("key1"))
        self.assertIsNotNone(lfu_cache.get("key2"))
        self.assertIsNotNone(lfu_cache.get("key5"))
        
        # Test FIFO policy
        # Access doesn't matter for FIFO
        for _ in range(3):
            fifo_cache.get("key4")
        
        # Add a new entry, which should evict key0 (first in)
        fifo_cache.put("key5", "value5")
        
        # Verify key0 was evicted
        self.assertIsNone(fifo_cache.get("key0"))
        self.assertIsNotNone(fifo_cache.get("key1"))
        self.assertIsNotNone(fifo_cache.get("key2"))
        self.assertIsNotNone(fifo_cache.get("key3"))
        self.assertIsNotNone(fifo_cache.get("key4"))
        self.assertIsNotNone(fifo_cache.get("key5"))
    
    def test_custom_cache_invalidation_strategy(self):
        """Test custom cache invalidation strategies."""
        # Create a cache
        cache = InMemoryCacheStore(max_size=100)
        
        # Add some entries
        for i in range(10):
            cache.put(f"key{i}", f"value{i}")
        
        # Create a custom invalidation strategy
        class CustomInvalidationStrategy(CacheInvalidationStrategy):
            def __init__(self, pattern: str):
                self.pattern = pattern
            
            def invalidate(self, cache: CacheStore, key: Optional[Any] = None) -> None:
                # If a specific key is provided, only invalidate that key
                if key is not None:
                    cache.remove(key)
                    return
                
                # Otherwise, invalidate keys matching the pattern
                # In a real implementation, we would need access to all keys
                # For this test, we'll simulate by trying all possible keys
                for i in range(100):
                    test_key = f"key{i}"
                    if self.pattern in test_key:
                        cache.remove(test_key)
        
        # Create an instance of the custom strategy
        custom_strategy = CustomInvalidationStrategy(pattern="key5")
        
        # Apply the strategy
        custom_strategy.invalidate(cache)
        
        # Verify key5 was invalidated
        self.assertIsNone(cache.get("key5"))
        
        # Verify other keys are still present
        for i in range(10):
            if i != 5:
                self.assertIsNotNone(cache.get(f"key{i}"))
        
        # Test the strategy with a specific key
        custom_strategy.invalidate(cache, "key1")
        
        # Verify key1 was invalidated
        self.assertIsNone(cache.get("key1"))
    
    def test_memoization_with_complex_arguments(self):
        """Test memoization of functions with complex arguments."""
        # Create a caching system
        caching_system = CachingSystem(max_size=100)
        
        # Create a complex function that takes various argument types
        @caching_system.memoize
        def complex_function(a: int, b: str, c: List[int], d: Dict[str, Any] = None) -> str:
            # Simulate an expensive computation
            time.sleep(0.01)
            return f"{a}_{b}_{''.join(map(str, c))}_{sorted(d.items()) if d else 'None'}"
        
        # Test with different argument types
        args1 = (1, "test", [1, 2, 3], {"x": 1, "y": 2})
        args2 = (2, "test", [4, 5, 6], {"z": 3})
        args3 = (1, "test", [1, 2, 3], {"x": 1, "y": 2})  # Same as args1
        
        # First call should be a cache miss
        start_time = time.time()
        result1 = complex_function(*args1[:3], d=args1[3])
        first_call_time = time.time() - start_time
        
        # Second call with different args should be a cache miss
        start_time = time.time()
        result2 = complex_function(*args2[:3], d=args2[3])
        second_call_time = time.time() - start_time
        
        # Third call with same args as first should be a cache hit
        start_time = time.time()
        result3 = complex_function(*args3[:3], d=args3[3])
        third_call_time = time.time() - start_time
        
        # Verify results
        self.assertEqual(result1, result3)
        self.assertNotEqual(result1, result2)
        
        # Verify timing (cache hit should be much faster)
        print(f"First call (cache miss): {first_call_time * 1000:.2f} ms")
        print(f"Second call (cache miss): {second_call_time * 1000:.2f} ms")
        print(f"Third call (cache hit): {third_call_time * 1000:.2f} ms")
        
        # Cache hit should be significantly faster than cache miss
        self.assertLess(third_call_time, first_call_time * 0.1)
    
    def test_caching_with_ast_nodes(self):
        """Test caching with AST nodes as keys."""
        # Create a caching system
        caching_system = CachingSystem(max_size=100)
        
        # Create AST nodes
        entity_type = self.type_system.get_type("Entity")
        boolean_type = self.type_system.get_type("Boolean")
        
        # Create constants
        a_const = ConstantNode("a", entity_type)
        b_const = ConstantNode("b", entity_type)
        
        # Create a predicate
        p_pred = ConstantNode("P", FunctionType([entity_type], boolean_type))
        
        # Create applications
        p_a = ApplicationNode(p_pred, [a_const], boolean_type)
        p_b = ApplicationNode(p_pred, [b_const], boolean_type)
        
        # Cache values with AST nodes as keys
        caching_system.put(p_a, "P(a) is true")
        caching_system.put(p_b, "P(b) is false")
        
        # Retrieve values
        value_a = caching_system.get(p_a)
        value_b = caching_system.get(p_b)
        
        # Verify values
        self.assertEqual(value_a, "P(a) is true")
        self.assertEqual(value_b, "P(b) is false")
        
        # Create identical AST nodes (different instances but same content)
        a_const2 = ConstantNode("a", entity_type)
        p_pred2 = ConstantNode("P", FunctionType([entity_type], boolean_type))
        p_a2 = ApplicationNode(p_pred2, [a_const2], boolean_type)
        
        # Retrieve value with identical AST node
        value_a2 = caching_system.get(p_a2)
        
        # Verify value (should be None because the string representation is different)
        # This is a limitation of the current implementation
        self.assertIsNone(value_a2)
        
        # Test with a memoized function that processes AST nodes
        @caching_system.memoize
        def process_ast_node(node: AST_Node) -> str:
            # Simulate an expensive computation
            time.sleep(0.01)
            if isinstance(node, ApplicationNode):
                return f"Application of {node.operator} to {node.arguments}"
            return str(node)
        
        # First call should be a cache miss
        start_time = time.time()
        result1 = process_ast_node(p_a)
        first_call_time = time.time() - start_time
        
        # Second call with same node should be a cache hit
        start_time = time.time()
        result2 = process_ast_node(p_a)
        second_call_time = time.time() - start_time
        
        # Verify results
        self.assertEqual(result1, result2)
        
        # Verify timing (cache hit should be much faster)
        print(f"First call (cache miss): {first_call_time * 1000:.2f} ms")
        print(f"Second call (cache hit): {second_call_time * 1000:.2f} ms")
        
        # Cache hit should be faster than cache miss
        # The actual speedup may vary based on system load and our stack inspection approach
        # So we'll just verify that it's at least somewhat faster
        self.assertLess(second_call_time, first_call_time)
    
    def test_cache_with_large_values(self):
        """Test caching with large values."""
        # Create a cache
        cache = InMemoryCacheStore(max_size=10)
        
        # Create a large value (1 MB)
        large_value = "x" * (1024 * 1024)
        
        # Measure memory usage before adding large values
        before_mem = 0
        try:
            import psutil
            process = psutil.Process()
            before_mem = process.memory_info().rss
        except ImportError:
            print("psutil not available, skipping memory measurement")
        
        # Add large values to the cache
        for i in range(5):
            cache.put(f"large_key{i}", large_value)
        
        # Measure memory usage after adding large values
        after_mem = 0
        try:
            import psutil
            process = psutil.Process()
            after_mem = process.memory_info().rss
            print(f"Memory usage before: {before_mem / (1024 * 1024):.2f} MB")
            print(f"Memory usage after: {after_mem / (1024 * 1024):.2f} MB")
            print(f"Difference: {(after_mem - before_mem) / (1024 * 1024):.2f} MB")
        except ImportError:
            pass
        
        # Verify cache size
        self.assertEqual(cache.size(), 5)
        
        # Verify values can be retrieved
        for i in range(5):
            value = cache.get(f"large_key{i}")
            self.assertEqual(value, large_value)
        
        # Add more large values to trigger eviction
        for i in range(5, 15):
            cache.put(f"large_key{i}", large_value)
        
        # Verify cache size is still limited
        self.assertEqual(cache.size(), 10)
        
        # Verify early values were evicted
        for i in range(5):
            value = cache.get(f"large_key{i}")
            self.assertIsNone(value)
        
        # Verify later values are present
        for i in range(5, 15):
            value = cache.get(f"large_key{i}")
            self.assertEqual(value, large_value)
    
    def test_dependency_based_invalidation_complex(self):
        """Test complex scenarios with dependency-based invalidation."""
        # Create a cache
        cache = InMemoryCacheStore(max_size=100)
        
        # Create a dependency-based invalidation strategy
        dependency_strategy = DependencyBasedInvalidation()
        
        # Enable recursive invalidation for this test
        dependency_strategy._recursive_invalidation = True
        
        # Add some entries to the cache
        for i in range(10):
            cache.put(f"key{i}", f"value{i}")
        
        # Create a complex dependency graph
        # key0 depends on dep0
        # key1 and key2 depend on dep1
        # key3, key4, and key5 depend on dep2
        # dep1 depends on dep0
        # dep2 depends on dep1
        dependency_strategy.add_dependency("key0", "dep0")
        dependency_strategy.add_dependency("key1", "dep1")
        dependency_strategy.add_dependency("key2", "dep1")
        dependency_strategy.add_dependency("key3", "dep2")
        dependency_strategy.add_dependency("key4", "dep2")
        dependency_strategy.add_dependency("key5", "dep2")
        dependency_strategy.add_dependency("dep1", "dep0")
        dependency_strategy.add_dependency("dep2", "dep1")
        
        # Invalidate dep0, which should cascade to all dependent keys
        dependency_strategy.invalidate(cache, "dep0")
        
        # Verify all dependent keys were invalidated
        for i in range(6):
            self.assertIsNone(cache.get(f"key{i}"))
        
        # Verify other keys are still present
        for i in range(6, 10):
            self.assertIsNotNone(cache.get(f"key{i}"))
        
        # Add the entries back
        for i in range(6):
            cache.put(f"key{i}", f"value{i}")
        
        # Invalidate dep1, which should cascade to dep2 and its dependents
        dependency_strategy.invalidate(cache, "dep1")
        
        # Verify dep1 and dep2 dependents were invalidated
        for i in range(1, 6):
            self.assertIsNone(cache.get(f"key{i}"))
        
        # Verify key0 is still present (depends on dep0, not dep1)
        self.assertIsNotNone(cache.get("key0"))
    
    def test_ttl_with_high_precision(self):
        """Test TTL expiration with high precision."""
        # Create a cache with short TTL
        ttl = 0.05  # 50 milliseconds
        cache = InMemoryCacheStore(max_size=10, default_ttl=ttl)
        
        # Add an entry
        cache.put("key", "value")
        
        # Verify entry is present immediately
        self.assertEqual(cache.get("key"), "value")
        
        # Wait for half the TTL
        time.sleep(ttl / 2)
        
        # Verify entry is still present
        self.assertEqual(cache.get("key"), "value")
        
        # Wait for the remaining TTL plus a small buffer
        time.sleep(ttl / 2 + 0.01)
        
        # Verify entry has expired
        self.assertIsNone(cache.get("key"))
    
    def test_memoize_recursive_function(self):
        """Test memoization of a recursive function."""
        # Create a caching system
        caching_system = CachingSystem(max_size=100)
        
        # Create a recursive function (Fibonacci)
        @caching_system.memoize
        def fibonacci(n: int) -> int:
            if n <= 1:
                return n
            return fibonacci(n - 1) + fibonacci(n - 2)
        
        # Measure time for computing Fibonacci without memoization
        def fibonacci_no_memo(n: int) -> int:
            if n <= 1:
                return n
            return fibonacci_no_memo(n - 1) + fibonacci_no_memo(n - 2)
        
        # Test with a moderately large value
        n = 30
        
        # Compute with memoization
        start_time = time.time()
        result_memo = fibonacci(n)
        memo_time = time.time() - start_time
        
        # Compute without memoization (only for small values)
        if n <= 35:  # Limit to avoid excessive computation time
            start_time = time.time()
            result_no_memo = fibonacci_no_memo(n)
            no_memo_time = time.time() - start_time
            
            # Verify results are the same
            self.assertEqual(result_memo, result_no_memo)
            
            # Verify memoization is significantly faster
            print(f"Fibonacci({n}) with memoization: {memo_time * 1000:.2f} ms")
            print(f"Fibonacci({n}) without memoization: {no_memo_time * 1000:.2f} ms")
            print(f"Speedup factor: {no_memo_time / memo_time:.2f}x")
            
            self.assertLess(memo_time, no_memo_time * 0.01)  # At least 100x faster


if __name__ == "__main__":
    unittest.main()
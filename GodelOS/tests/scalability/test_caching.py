"""
Unit tests for the Caching & Memoization Layer.

This module contains tests for the CachingMemoizationLayer, CacheEntry,
CacheStore, and various cache invalidation strategy classes.
"""

import unittest
import time
from unittest.mock import MagicMock, patch

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode, ConstantNode, ApplicationNode
from godelOS.core_kr.type_system.types import Type
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
    DependencyBasedInvalidation
)


class TestCacheEntry(unittest.TestCase):
    """Test cases for the CacheEntry class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a cache entry
        self.value = "test_value"
        self.entry = CacheEntry(self.value)
        
        # Create a cache entry with TTL
        self.ttl = 1.0  # 1 second
        self.entry_with_ttl = CacheEntry(self.value, self.ttl)
    
    def test_initialization(self):
        """Test initialization of a cache entry."""
        # Check if the entry is initialized correctly
        self.assertEqual(self.entry.value, self.value)
        self.assertGreater(self.entry.created_at, 0)
        self.assertEqual(self.entry.last_accessed_at, self.entry.created_at)
        self.assertEqual(self.entry.access_count, 0)
        self.assertIsNone(self.entry.ttl)
        
        # Check if the entry with TTL is initialized correctly
        self.assertEqual(self.entry_with_ttl.value, self.value)
        self.assertEqual(self.entry_with_ttl.ttl, self.ttl)
    
    def test_access(self):
        """Test accessing a cache entry."""
        # Record the initial last_accessed_at
        initial_last_accessed = self.entry.last_accessed_at
        
        # Wait a bit to ensure time difference
        time.sleep(0.01)
        
        # Access the entry
        self.entry.access()
        
        # Check if the access metadata is updated correctly
        self.assertGreater(self.entry.last_accessed_at, initial_last_accessed)
        self.assertEqual(self.entry.access_count, 1)
    
    def test_is_expired(self):
        """Test checking if a cache entry has expired."""
        # Check if an entry without TTL never expires
        self.assertFalse(self.entry.is_expired())
        
        # Check if an entry with TTL is not expired initially
        self.assertFalse(self.entry_with_ttl.is_expired())
        
        # Wait for the entry to expire
        time.sleep(self.ttl + 0.1)
        
        # Check if the entry is now expired
        self.assertTrue(self.entry_with_ttl.is_expired())


class TestInMemoryCacheStore(unittest.TestCase):
    """Test cases for the InMemoryCacheStore class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create an in-memory cache store
        self.max_size = 3
        self.store = InMemoryCacheStore(max_size=self.max_size, eviction_policy=EvictionPolicy.LRU)
        
        # Create some test data
        self.key1 = "key1"
        self.value1 = "value1"
        self.key2 = "key2"
        self.value2 = "value2"
        self.key3 = "key3"
        self.value3 = "value3"
        self.key4 = "key4"
        self.value4 = "value4"
    
    def test_put_and_get(self):
        """Test putting and getting values from the cache."""
        # Put values in the cache
        self.store.put(self.key1, self.value1)
        self.store.put(self.key2, self.value2)
        
        # Get values from the cache
        value1 = self.store.get(self.key1)
        value2 = self.store.get(self.key2)
        value3 = self.store.get(self.key3)  # Non-existent key
        
        # Check if the values are correct
        self.assertEqual(value1, self.value1)
        self.assertEqual(value2, self.value2)
        self.assertIsNone(value3)
    
    def test_remove(self):
        """Test removing values from the cache."""
        # Put values in the cache
        self.store.put(self.key1, self.value1)
        self.store.put(self.key2, self.value2)
        
        # Remove a value
        self.store.remove(self.key1)
        
        # Check if the value is removed
        value1 = self.store.get(self.key1)
        value2 = self.store.get(self.key2)
        
        self.assertIsNone(value1)
        self.assertEqual(value2, self.value2)
    
    def test_clear(self):
        """Test clearing the cache."""
        # Put values in the cache
        self.store.put(self.key1, self.value1)
        self.store.put(self.key2, self.value2)
        
        # Clear the cache
        self.store.clear()
        
        # Check if the cache is empty
        value1 = self.store.get(self.key1)
        value2 = self.store.get(self.key2)
        
        self.assertIsNone(value1)
        self.assertIsNone(value2)
        self.assertEqual(self.store.size(), 0)
    
    def test_size(self):
        """Test getting the size of the cache."""
        # Check initial size
        self.assertEqual(self.store.size(), 0)
        
        # Put values in the cache
        self.store.put(self.key1, self.value1)
        self.store.put(self.key2, self.value2)
        
        # Check size after putting values
        self.assertEqual(self.store.size(), 2)
        
        # Remove a value
        self.store.remove(self.key1)
        
        # Check size after removing a value
        self.assertEqual(self.store.size(), 1)
        
        # Clear the cache
        self.store.clear()
        
        # Check size after clearing
        self.assertEqual(self.store.size(), 0)
    
    def test_eviction_lru(self):
        """Test LRU eviction policy."""
        # Create a cache store with LRU eviction policy
        store = InMemoryCacheStore(max_size=2, eviction_policy=EvictionPolicy.LRU)
        
        # Put values in the cache
        store.put(self.key1, self.value1)
        store.put(self.key2, self.value2)
        
        # Access key1 to make it more recently used
        store.get(self.key1)
        
        # Put another value, which should evict key2 (least recently used)
        store.put(self.key3, self.value3)
        
        # Check if key2 is evicted and key1 and key3 are still in the cache
        value1 = store.get(self.key1)
        value2 = store.get(self.key2)
        value3 = store.get(self.key3)
        
        self.assertEqual(value1, self.value1)
        self.assertIsNone(value2)
        self.assertEqual(value3, self.value3)
    
    def test_eviction_lfu(self):
        """Test LFU eviction policy."""
        # Create a cache store with LFU eviction policy
        store = InMemoryCacheStore(max_size=2, eviction_policy=EvictionPolicy.LFU)
        
        # Put values in the cache
        store.put(self.key1, self.value1)
        store.put(self.key2, self.value2)
        
        # Access key1 multiple times to increase its frequency
        store.get(self.key1)
        store.get(self.key1)
        
        # Put another value, which should evict key2 (least frequently used)
        store.put(self.key3, self.value3)
        
        # Check if key2 is evicted and key1 and key3 are still in the cache
        value1 = store.get(self.key1)
        value2 = store.get(self.key2)
        value3 = store.get(self.key3)
        
        self.assertEqual(value1, self.value1)
        self.assertIsNone(value2)
        self.assertEqual(value3, self.value3)
    
    def test_eviction_fifo(self):
        """Test FIFO eviction policy."""
        # Create a cache store with FIFO eviction policy
        store = InMemoryCacheStore(max_size=2, eviction_policy=EvictionPolicy.FIFO)
        
        # Put values in the cache
        store.put(self.key1, self.value1)
        store.put(self.key2, self.value2)
        
        # Access key1 to make it more recently used (should not matter for FIFO)
        store.get(self.key1)
        
        # Put another value, which should evict key1 (first in)
        store.put(self.key3, self.value3)
        
        # Check if key1 is evicted and key2 and key3 are still in the cache
        value1 = store.get(self.key1)
        value2 = store.get(self.key2)
        value3 = store.get(self.key3)
        
        self.assertIsNone(value1)
        self.assertEqual(value2, self.value2)
        self.assertEqual(value3, self.value3)
    
    def test_ttl_expiration(self):
        """Test TTL expiration."""
        # Create a cache store with TTL
        ttl = 0.1  # 100 milliseconds
        store = InMemoryCacheStore(max_size=2, default_ttl=ttl)
        
        # Put a value in the cache
        store.put(self.key1, self.value1)
        
        # Check if the value is in the cache
        value1 = store.get(self.key1)
        self.assertEqual(value1, self.value1)
        
        # Wait for the value to expire
        time.sleep(ttl + 0.1)
        
        # Check if the value is expired
        value1 = store.get(self.key1)
        self.assertIsNone(value1)


class TestCacheInvalidationStrategies(unittest.TestCase):
    """Test cases for the cache invalidation strategy classes."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock cache store
        self.cache_store = MagicMock(spec=CacheStore)
        
        # Create invalidation strategies
        self.time_based = TimeBasedInvalidation(max_age=1.0)
        self.pattern_based = PatternBasedInvalidation(pattern="key*")
        self.dependency_based = DependencyBasedInvalidation()
    
    def test_time_based_invalidation(self):
        """Test time-based cache invalidation strategy."""
        # Invalidate the cache
        self.time_based.invalidate(self.cache_store)
        
        # Check if the cache is cleared
        self.cache_store.clear.assert_called_once()
    
    def test_pattern_based_invalidation(self):
        """Test pattern-based cache invalidation strategy."""
        # Invalidate the cache
        self.pattern_based.invalidate(self.cache_store)
        
        # Check if the cache is cleared
        self.cache_store.clear.assert_called_once()
    
    def test_dependency_based_invalidation(self):
        """Test dependency-based cache invalidation strategy."""
        # Add dependencies
        self.dependency_based.add_dependency("key1", "dep1")
        self.dependency_based.add_dependency("key2", "dep1")
        self.dependency_based.add_dependency("key3", "dep2")
        
        # Invalidate a specific key
        self.dependency_based.invalidate(self.cache_store, "dep1")
        
        # Check if the dependent keys are invalidated
        self.cache_store.remove.assert_any_call("dep1")
        self.cache_store.remove.assert_any_call("key1")
        self.cache_store.remove.assert_any_call("key2")
        self.assertEqual(self.cache_store.remove.call_count, 3)
        
        # Reset the mock
        self.cache_store.remove.reset_mock()
        
        # Invalidate all keys
        self.dependency_based.invalidate(self.cache_store)
        
        # Check if the cache is cleared
        self.cache_store.clear.assert_called_once()


class TestCachingMemoizationLayer(unittest.TestCase):
    """Test cases for the CachingMemoizationLayer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a caching and memoization layer
        self.layer = CachingMemoizationLayer(max_size=10, eviction_policy=EvictionPolicy.LRU)
        
        # Create some test data
        self.key1 = "key1"
        self.value1 = "value1"
        self.key2 = "key2"
        self.value2 = "value2"
        
        # Create a type system manager
        self.type_system = TypeSystemManager()
        self.type_system.register_type("Entity", None)
        
        # Create an AST node
        self.entity_type = self.type_system.get_type("Entity")
        self.node = ConstantNode("Person", "Person", self.entity_type)
    
    def test_put_and_get(self):
        """Test putting and getting values from the cache."""
        # Put values in the cache
        self.layer.put(self.key1, self.value1)
        self.layer.put(self.key2, self.value2)
        
        # Get values from the cache
        value1 = self.layer.get(self.key1)
        value2 = self.layer.get(self.key2)
        value3 = self.layer.get("key3")  # Non-existent key
        
        # Check if the values are correct
        self.assertEqual(value1, self.value1)
        self.assertEqual(value2, self.value2)
        self.assertIsNone(value3)
    
    def test_invalidate(self):
        """Test invalidating cache entries."""
        # Put values in the cache
        self.layer.put(self.key1, self.value1)
        self.layer.put(self.key2, self.value2)
        
        # Invalidate a specific key
        self.layer.invalidate(self.key1)
        
        # Check if the key is invalidated
        value1 = self.layer.get(self.key1)
        value2 = self.layer.get(self.key2)
        
        self.assertIsNone(value1)
        self.assertEqual(value2, self.value2)
        
        # Invalidate all keys
        self.layer.invalidate()
        
        # Check if all keys are invalidated
        value2 = self.layer.get(self.key2)
        self.assertIsNone(value2)
    
    def test_clear(self):
        """Test clearing the cache."""
        # Put values in the cache
        self.layer.put(self.key1, self.value1)
        self.layer.put(self.key2, self.value2)
        
        # Clear the cache
        self.layer.clear()
        
        # Check if the cache is empty
        value1 = self.layer.get(self.key1)
        value2 = self.layer.get(self.key2)
        
        self.assertIsNone(value1)
        self.assertIsNone(value2)
        self.assertEqual(self.layer.size(), 0)
    
    def test_size(self):
        """Test getting the size of the cache."""
        # Check initial size
        self.assertEqual(self.layer.size(), 0)
        
        # Put values in the cache
        self.layer.put(self.key1, self.value1)
        self.layer.put(self.key2, self.value2)
        
        # Check size after putting values
        self.assertEqual(self.layer.size(), 2)
        
        # Invalidate a key
        self.layer.invalidate(self.key1)
        
        # Check size after invalidating a key
        self.assertEqual(self.layer.size(), 1)
        
        # Clear the cache
        self.layer.clear()
        
        # Check size after clearing
        self.assertEqual(self.layer.size(), 0)
    
    def test_memoize(self):
        """Test memoizing a function."""
        # Create a mock function
        mock_func = MagicMock(return_value=self.value1)
        
        # Memoize the function
        memoized_func = self.layer.memoize(mock_func)
        
        # Call the memoized function
        result1 = memoized_func(self.key1)
        
        # Check if the result is correct
        self.assertEqual(result1, self.value1)
        mock_func.assert_called_once_with(self.key1)
        
        # Reset the mock
        mock_func.reset_mock()
        
        # Call the memoized function again with the same argument
        result2 = memoized_func(self.key1)
        
        # Check if the result is correct and the function is not called again
        self.assertEqual(result2, self.value1)
        mock_func.assert_not_called()
        
        # Call the memoized function with a different argument
        mock_func.return_value = self.value2
        result3 = memoized_func(self.key2)
        
        # Check if the result is correct and the function is called
        self.assertEqual(result3, self.value2)
        mock_func.assert_called_once_with(self.key2)
    
    def test_convert_key(self):
        """Test converting keys to strings."""
        # Convert a string key
        string_key = self.layer._convert_key(self.key1)
        self.assertEqual(string_key, self.key1)
        
        # Convert an AST node key
        node_key = self.layer._convert_key(self.node)
        self.assertEqual(node_key, str(self.node))
        
        # Convert a complex key
        complex_key = self.layer._convert_key((self.key1, self.key2))
        self.assertIsInstance(complex_key, str)
    
    def test_generate_cache_key(self):
        """Test generating a cache key for a function call."""
        # Create a function
        def test_func(a, b, c=None):
            return a + b + (c or "")
        
        # Generate a cache key
        key1 = self.layer._generate_cache_key(test_func, (self.key1, self.key2), {})
        key2 = self.layer._generate_cache_key(test_func, (self.key1, self.key2), {"c": "c"})
        
        # Check if the keys are different
        self.assertNotEqual(key1, key2)
        
        # Generate the same key again
        key1_again = self.layer._generate_cache_key(test_func, (self.key1, self.key2), {})
        
        # Check if the keys are the same
        self.assertEqual(key1, key1_again)


if __name__ == "__main__":
    unittest.main()
"""
Base test classes with common setup/teardown logic.

This module provides base test classes to eliminate duplicated setup/teardown code
across the test suite, particularly for cache management.
"""

from django.test import TestCase
from django.core.cache import cache


class CacheTestCase(TestCase):
    """
    Base test case that manages cache clearing.

    Automatically clears the cache before and after each test to ensure
    clean test isolation and prevent contamination between tests.

    Usage:
        class MyTest(CacheTestCase):
            def test_something(self):
                # Cache is already cleared before this test
                # Your test code here
                pass
    """

    def setUp(self):
        """Clear cache before each test to ensure clean state."""
        super().setUp()
        cache.clear()

    def tearDown(self):
        """Clear cache after each test to prevent contamination."""
        cache.clear()
        super().tearDown()

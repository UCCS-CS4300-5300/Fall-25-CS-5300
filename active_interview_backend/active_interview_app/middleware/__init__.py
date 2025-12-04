"""Middleware package for active_interview_app."""

from .ratelimit_middleware import RateLimitMiddleware

# Import middleware classes from the middleware.py module file
# Note: There's both a middleware.py file AND a middleware/ package in the same directory.
# When both exist, Python's import system finds the package first.
# We need to explicitly load the .py file using importlib.
import importlib.util
import os

# Get path to middleware.py file (sibling to this package directory)
_middleware_module_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'middleware.py'
)

# Load the middleware.py module
_spec = importlib.util.spec_from_file_location("observability_middleware", _middleware_module_path)
_observability_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_observability_module)

# Re-export observability middleware classes
MetricsMiddleware = _observability_module.MetricsMiddleware
PerformanceMonitorMiddleware = _observability_module.PerformanceMonitorMiddleware

__all__ = [
    'RateLimitMiddleware',
    'MetricsMiddleware',
    'PerformanceMonitorMiddleware'
]

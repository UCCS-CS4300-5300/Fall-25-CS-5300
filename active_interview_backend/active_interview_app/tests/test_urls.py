"""
Test URLs for rate limiting tests.

This module provides test-only URL patterns with rate limiting decorators applied.
These URLs are used by test_ratelimit.py to test rate limiting behavior.
"""

from django.urls import path
from django.http import HttpResponse
from ..decorators.ratelimit_decorators import (
    ratelimit_default,
    ratelimit_strict,
    ratelimit_lenient
)


# Test views with rate limiting decorators
@ratelimit_default(methods=['GET', 'POST'])
def test_default_view(request):
    """Test view with default rate limiting."""
    return HttpResponse('OK', status=200)


@ratelimit_strict(methods=['GET', 'POST'])
def test_strict_view(request):
    """Test view with strict rate limiting."""
    return HttpResponse('OK', status=200)


@ratelimit_lenient(methods=['GET', 'POST'])
def test_lenient_view(request):
    """Test view with lenient rate limiting."""
    return HttpResponse('OK', status=200)


# Simple views for template links
def index_view(request):
    """Simple index view for testing."""
    return HttpResponse('Index', status=200)


def features_view(request):
    """Simple features view for testing."""
    return HttpResponse('Features', status=200)


def about_us_view(request):
    """Simple about us view for testing."""
    return HttpResponse('About Us', status=200)


# URL patterns for testing
urlpatterns = [
    path('', index_view, name='index'),  # Add index for template {% url 'index' %}
    path('features/', features_view, name='features'),  # For navbar {% url 'features' %}
    path('about-us/', about_us_view, name='about-us'),  # For navbar {% url 'about-us' %}
    path('test/default/', test_default_view, name='test_default'),
    path('test/strict/', test_strict_view, name='test_strict'),
    path('test/lenient/', test_lenient_view, name='test_lenient'),
]

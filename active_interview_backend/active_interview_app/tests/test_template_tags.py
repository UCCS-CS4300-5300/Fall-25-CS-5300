"""Tests for custom template tags."""

from django.test import TestCase
from django.template import Context, Template
from ..templatetags import ratelimit_extras
import active_interview_app.templatetags  # Import __init__.py for coverage


class RatelimitExtrasTest(TestCase):
    """Tests for ratelimit_extras template tags."""

    def test_template_tags_module_import(self):
        """Test that the templatetags module imports correctly."""
        # This ensures __init__.py is covered
        self.assertIsNotNone(active_interview_app.templatetags)

    def test_multiply_filter_in_template(self):
        """Test multiply filter within a template context."""
        template = Template("{% load ratelimit_extras %}{{ value|multiply:arg }}")
        context = Context({'value': 10, 'arg': 5})
        result = template.render(context)
        self.assertEqual(result.strip(), '50.0')

    def test_divide_filter_in_template(self):
        """Test divide filter within a template context."""
        template = Template("{% load ratelimit_extras %}{{ value|divide:arg }}")
        context = Context({'value': 100, 'arg': 5})
        result = template.render(context)
        self.assertEqual(result.strip(), '20.0')

    def test_multiply_filter(self):
        """Test multiply filter with valid numbers."""
        result = ratelimit_extras.multiply(10, 5)
        self.assertEqual(result, 50)

    def test_multiply_filter_floats(self):
        """Test multiply filter with floats."""
        result = ratelimit_extras.multiply(10.5, 2)
        self.assertEqual(result, 21.0)

    def test_multiply_filter_invalid_value(self):
        """Test multiply filter with invalid value."""
        result = ratelimit_extras.multiply('invalid', 5)
        self.assertEqual(result, 0)

    def test_multiply_filter_invalid_arg(self):
        """Test multiply filter with invalid argument."""
        result = ratelimit_extras.multiply(10, 'invalid')
        self.assertEqual(result, 0)

    def test_divide_filter(self):
        """Test divide filter with valid numbers."""
        result = ratelimit_extras.divide(100, 5)
        self.assertEqual(result, 20.0)

    def test_divide_filter_floats(self):
        """Test divide filter with floats."""
        result = ratelimit_extras.divide(10.0, 4.0)
        self.assertEqual(result, 2.5)

    def test_divide_filter_by_zero(self):
        """Test divide filter with zero divisor."""
        result = ratelimit_extras.divide(100, 0)
        self.assertEqual(result, 0)

    def test_divide_filter_invalid_value(self):
        """Test divide filter with invalid value."""
        result = ratelimit_extras.divide('invalid', 5)
        self.assertEqual(result, 0)

    def test_divide_filter_invalid_arg(self):
        """Test divide filter with invalid argument."""
        result = ratelimit_extras.divide(100, 'invalid')
        self.assertEqual(result, 0)

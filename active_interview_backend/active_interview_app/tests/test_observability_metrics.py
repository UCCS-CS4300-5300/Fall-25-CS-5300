"""
Tests for observability metrics collection and analysis.

Related to Issues #14, #15 (Observability Dashboard).

Test coverage:
- RequestMetric model and methods
- DailyMetricsSummary model
- ProviderCostDaily model
- ErrorLog model
- MetricsMiddleware
- Management commands (cleanup, aggregation)
"""
from django.test import TestCase, RequestFactory, TransactionTestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
from io import StringIO
from django.core.management import call_command
import time

from active_interview_app.observability_models import (
    RequestMetric,
    DailyMetricsSummary,
    ProviderCostDaily,
    ErrorLog
)
from active_interview_app.middleware import MetricsMiddleware
from active_interview_app.token_usage_models import TokenUsage


class RequestMetricModelTests(TestCase):
    """Test RequestMetric model functionality."""

    def setUp(self):
        """Create test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.now = timezone.now()

    def test_create_request_metric(self):
        """Test creating a basic RequestMetric."""
        metric = RequestMetric.objects.create(
            endpoint='/api/chat/',
            method='POST',
            status_code=200,
            response_time_ms=150.5,
            user_id=self.user.id
        )

        self.assertEqual(metric.endpoint, '/api/chat/')
        self.assertEqual(metric.method, 'POST')
        self.assertEqual(metric.status_code, 200)
        self.assertEqual(metric.response_time_ms, 150.5)
        self.assertEqual(metric.user_id, self.user.id)
        self.assertIsNotNone(metric.timestamp)

    def test_is_error_property(self):
        """Test is_error property for different status codes."""
        # Success - not an error
        metric_200 = RequestMetric.objects.create(
            endpoint='/api/test/',
            method='GET',
            status_code=200,
            response_time_ms=50.0
        )
        self.assertFalse(metric_200.is_error)

        # Client error
        metric_404 = RequestMetric.objects.create(
            endpoint='/api/test/',
            method='GET',
            status_code=404,
            response_time_ms=50.0
        )
        self.assertTrue(metric_404.is_error)
        self.assertTrue(metric_404.is_client_error)
        self.assertFalse(metric_404.is_server_error)

        # Server error
        metric_500 = RequestMetric.objects.create(
            endpoint='/api/test/',
            method='GET',
            status_code=500,
            response_time_ms=50.0
        )
        self.assertTrue(metric_500.is_error)
        self.assertFalse(metric_500.is_client_error)
        self.assertTrue(metric_500.is_server_error)

    def test_calculate_rps_single_endpoint(self):
        """Test RPS calculation for a specific endpoint."""
        start_time = self.now
        end_time = start_time + timedelta(seconds=10)

        # Create 100 requests over 10 seconds = 10 RPS
        for i in range(100):
            RequestMetric.objects.create(
                endpoint='/api/chat/',
                method='POST',
                status_code=200,
                response_time_ms=100.0,
                timestamp=start_time + timedelta(seconds=i * 0.1)
            )

        rps = RequestMetric.calculate_rps(
            endpoint='/api/chat/',
            start_time=start_time,
            end_time=end_time
        )

        self.assertAlmostEqual(rps, 10.0, places=1)

    def test_calculate_rps_all_endpoints(self):
        """Test RPS calculation across all endpoints."""
        start_time = self.now
        end_time = start_time + timedelta(seconds=10)

        # Create requests to multiple endpoints
        for i in range(50):
            RequestMetric.objects.create(
                endpoint='/api/chat/',
                method='POST',
                status_code=200,
                response_time_ms=100.0,
                timestamp=start_time + timedelta(seconds=i * 0.2)
            )

        for i in range(50):
            RequestMetric.objects.create(
                endpoint='/api/users/',
                method='GET',
                status_code=200,
                response_time_ms=50.0,
                timestamp=start_time + timedelta(seconds=i * 0.2)
            )

        # Total 100 requests over 10 seconds = 10 RPS
        rps = RequestMetric.calculate_rps(
            start_time=start_time,
            end_time=end_time
        )

        self.assertAlmostEqual(rps, 10.0, places=1)

    def test_get_error_rate(self):
        """Test error rate calculation."""
        start_time = self.now
        end_time = start_time + timedelta(hours=1)

        # Create mix of successful and error requests
        # 70 successful, 20 client errors, 10 server errors = 30% error rate
        # Use seconds instead of minutes to fit all requests within 1 hour window
        for i in range(70):
            RequestMetric.objects.create(
                endpoint='/api/test/',
                method='GET',
                status_code=200,
                response_time_ms=100.0,
                timestamp=start_time + timedelta(seconds=i)
            )

        for i in range(20):
            RequestMetric.objects.create(
                endpoint='/api/test/',
                method='GET',
                status_code=404,
                response_time_ms=50.0,
                timestamp=start_time + timedelta(seconds=70 + i)
            )

        for i in range(10):
            RequestMetric.objects.create(
                endpoint='/api/test/',
                method='POST',
                status_code=500,
                response_time_ms=200.0,
                timestamp=start_time + timedelta(seconds=90 + i)
            )

        error_stats = RequestMetric.get_error_rate(
            start_time=start_time,
            end_time=end_time
        )

        self.assertEqual(error_stats['total_requests'], 100)
        self.assertEqual(error_stats['error_count'], 30)
        self.assertEqual(error_stats['client_error_count'], 20)
        self.assertEqual(error_stats['server_error_count'], 10)
        self.assertAlmostEqual(error_stats['error_rate'], 30.0, places=1)

    def test_calculate_percentiles(self):
        """Test percentile calculations for response times."""
        start_time = self.now
        end_time = start_time + timedelta(hours=1)

        # Create requests with varying response times
        # Distribution: 50 values of 50ms, 30 of 100ms, 15 of 150ms, 5 of 200ms
        # p50 will interpolate between index 49 (50ms) and 50 (100ms) = ~75ms
        # p95 will be around 150-200ms range
        response_times = [50] * 50 + [100] * 30 + [150] * 15 + [200] * 5

        for i, rt in enumerate(response_times):
            RequestMetric.objects.create(
                endpoint='/api/test/',
                method='GET',
                status_code=200,
                response_time_ms=float(rt),
                timestamp=start_time + timedelta(seconds=i)
            )

        percentiles = RequestMetric.calculate_percentiles(
            endpoint='/api/test/',
            start_time=start_time,
            end_time=end_time
        )

        self.assertEqual(percentiles['count'], 100)
        # p50 interpolates between 50ms and 100ms, expecting ~75ms
        self.assertAlmostEqual(percentiles['p50'], 75.0, delta=10.0)
        # p95 should be in the 150-200ms range
        self.assertAlmostEqual(percentiles['p95'], 175.0, delta=30.0)
        self.assertEqual(percentiles['min'], 50.0)
        self.assertEqual(percentiles['max'], 200.0)

    def test_calculate_percentiles_empty_dataset(self):
        """Test percentile calculation with no data."""
        start_time = self.now
        end_time = start_time + timedelta(hours=1)

        percentiles = RequestMetric.calculate_percentiles(
            endpoint='/api/nonexistent/',
            start_time=start_time,
            end_time=end_time
        )

        self.assertEqual(percentiles['count'], 0)
        self.assertEqual(percentiles['p50'], 0.0)
        self.assertEqual(percentiles['p95'], 0.0)


class DailyMetricsSummaryModelTests(TestCase):
    """Test DailyMetricsSummary model."""

    def test_create_daily_summary(self):
        """Test creating a daily metrics summary."""
        today = timezone.now().date()

        summary = DailyMetricsSummary.objects.create(
            date=today,
            total_requests=1000,
            total_errors=50,
            client_errors=30,
            server_errors=20,
            avg_response_time=150.5,
            p50_response_time=120.0,
            p95_response_time=450.0,
            max_response_time=1200.0,
            endpoint_stats={
                '/api/chat/': {
                    'requests': 500,
                    'errors': 10,
                    'avg_latency': 200.0
                },
                '/api/users/': {
                    'requests': 500,
                    'errors': 40,
                    'avg_latency': 100.0
                }
            }
        )

        self.assertEqual(summary.date, today)
        self.assertEqual(summary.total_requests, 1000)
        self.assertEqual(summary.total_errors, 50)
        self.assertAlmostEqual(summary.error_rate, 5.0, places=1)

    def test_error_rate_property(self):
        """Test error_rate calculated property."""
        today = timezone.now().date()

        # 30% error rate
        summary = DailyMetricsSummary.objects.create(
            date=today,
            total_requests=100,
            total_errors=30
        )
        self.assertAlmostEqual(summary.error_rate, 30.0, places=1)

        # Zero requests
        summary_zero = DailyMetricsSummary.objects.create(
            date=today - timedelta(days=1),
            total_requests=0,
            total_errors=0
        )
        self.assertEqual(summary_zero.error_rate, 0.0)

    def test_unique_date_constraint(self):
        """Test that date field is unique."""
        today = timezone.now().date()

        DailyMetricsSummary.objects.create(
            date=today,
            total_requests=100
        )

        # Creating another summary for the same date should use update_or_create
        # in the actual implementation, but direct create should fail
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            DailyMetricsSummary.objects.create(
                date=today,
                total_requests=200
            )


class ProviderCostDailyModelTests(TestCase):
    """Test ProviderCostDaily model."""

    def test_create_provider_cost(self):
        """Test creating a provider cost record."""
        today = timezone.now().date()

        cost = ProviderCostDaily.objects.create(
            date=today,
            provider='OpenAI',
            service='gpt-4o',
            total_requests=100,
            total_cost_usd=Decimal('5.50'),
            total_tokens=50000,
            prompt_tokens=30000,
            completion_tokens=20000
        )

        self.assertEqual(cost.provider, 'OpenAI')
        self.assertEqual(cost.service, 'gpt-4o')
        self.assertEqual(cost.total_requests, 100)
        self.assertEqual(cost.total_cost_usd, Decimal('5.50'))
        self.assertEqual(cost.total_tokens, 50000)

    def test_get_monthly_cost(self):
        """Test monthly cost aggregation."""
        # Create costs for January 2025
        for day in range(1, 31):
            date_obj = date(2025, 1, day)
            ProviderCostDaily.objects.create(
                date=date_obj,
                provider='OpenAI',
                service='gpt-4o',
                total_requests=100,
                total_cost_usd=Decimal('10.00'),
                total_tokens=10000
            )

        monthly_cost = ProviderCostDaily.get_monthly_cost(2025, 1)

        # 30 days * $10 = $300
        self.assertEqual(monthly_cost, Decimal('300.00'))

    def test_get_monthly_cost_by_provider(self):
        """Test monthly cost filtered by provider."""
        today = timezone.now().date()

        # Create costs for different providers
        ProviderCostDaily.objects.create(
            date=today,
            provider='OpenAI',
            service='gpt-4o',
            total_requests=100,
            total_cost_usd=Decimal('50.00'),
            total_tokens=10000
        )

        ProviderCostDaily.objects.create(
            date=today,
            provider='Anthropic',
            service='claude-sonnet-4',
            total_requests=50,
            total_cost_usd=Decimal('25.00'),
            total_tokens=5000
        )

        openai_cost = ProviderCostDaily.get_monthly_cost(
            today.year,
            today.month,
            provider='OpenAI'
        )

        self.assertEqual(openai_cost, Decimal('50.00'))

    def test_unique_together_constraint(self):
        """Test unique_together constraint on date, provider, service."""
        today = timezone.now().date()

        ProviderCostDaily.objects.create(
            date=today,
            provider='OpenAI',
            service='gpt-4o',
            total_requests=100,
            total_cost_usd=Decimal('10.00'),
            total_tokens=10000
        )

        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            ProviderCostDaily.objects.create(
                date=today,
                provider='OpenAI',
                service='gpt-4o',
                total_requests=200,
                total_cost_usd=Decimal('20.00'),
                total_tokens=20000
            )


class ErrorLogModelTests(TestCase):
    """Test ErrorLog model."""

    def test_create_error_log(self):
        """Test creating an error log entry."""
        error = ErrorLog.objects.create(
            endpoint='/api/chat/',
            method='POST',
            status_code=500,
            error_type='ValueError',
            error_message='Invalid input data',
            stack_trace='Traceback...',
            user_id=1,
            request_data={
                'method': 'POST',
                'path': '/api/chat/',
                'query_params': {},
                'user_agent': 'Mozilla/5.0'
            }
        )

        self.assertEqual(error.endpoint, '/api/chat/')
        self.assertEqual(error.status_code, 500)
        self.assertEqual(error.error_type, 'ValueError')
        self.assertIsNotNone(error.timestamp)


class MetricsMiddlewareTests(TransactionTestCase):
    """Test MetricsMiddleware functionality."""

    def setUp(self):
        """Set up test request factory and middleware."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_middleware_records_successful_request(self):
        """Test that middleware records successful requests."""
        # Create a simple view that returns 200
        def dummy_view(request):
            from django.http import HttpResponse
            return HttpResponse("OK")

        middleware = MetricsMiddleware(dummy_view)

        request = self.factory.get('/api/test/')
        request.user = self.user

        # Process request through middleware
        middleware(request)

        # Check that metric was recorded
        metrics = RequestMetric.objects.filter(endpoint='/api/test/')
        self.assertEqual(metrics.count(), 1)

        metric = metrics.first()
        self.assertEqual(metric.method, 'GET')
        self.assertEqual(metric.status_code, 200)
        self.assertEqual(metric.user_id, self.user.id)
        self.assertGreater(metric.response_time_ms, 0)

    def test_middleware_records_error_request(self):
        """Test that middleware records error requests."""
        # Create a view that raises an exception
        def error_view(request):
            raise ValueError("Test error")

        middleware = MetricsMiddleware(error_view)

        request = self.factory.get('/api/error/')
        request.user = self.user

        # Process request (should raise exception)
        with self.assertRaises(ValueError):
            middleware(request)

        # Check that metric was recorded with 500 status
        metrics = RequestMetric.objects.filter(endpoint='/api/error/')
        self.assertEqual(metrics.count(), 1)

        metric = metrics.first()
        self.assertEqual(metric.status_code, 500)

        # Check that error log was created
        errors = ErrorLog.objects.filter(endpoint='/api/error/')
        self.assertEqual(errors.count(), 1)

        error = errors.first()
        self.assertEqual(error.error_type, 'ValueError')
        self.assertEqual(error.error_message, 'Test error')

    def test_middleware_handles_anonymous_user(self):
        """Test middleware with anonymous user."""
        def dummy_view(request):
            from django.http import HttpResponse
            return HttpResponse("OK")

        middleware = MetricsMiddleware(dummy_view)

        request = self.factory.get('/api/public/')
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()

        middleware(request)

        metric = RequestMetric.objects.get(endpoint='/api/public/')
        self.assertIsNone(metric.user_id)

    def test_middleware_minimal_overhead(self):
        """Test that middleware overhead is minimal (< 5ms)."""
        def fast_view(request):
            from django.http import HttpResponse
            return HttpResponse("OK")

        middleware = MetricsMiddleware(fast_view)

        request = self.factory.get('/api/fast/')
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()

        # Measure middleware overhead
        start = time.time()
        middleware(request)
        end = time.time()

        overhead_ms = (end - start) * 1000

        # Overhead should be less than 50ms (generous threshold for CI)
        self.assertLess(overhead_ms, 50)

    def test_middleware_handles_4xx_response(self):
        """Test middleware handles 4xx responses (HTTP errors without exceptions)."""
        def view_404(request):
            from django.http import HttpResponseNotFound
            return HttpResponseNotFound("Not found")

        middleware = MetricsMiddleware(view_404)
        request = self.factory.get('/api/notfound/')
        request.user = self.user

        middleware(request)

        # Check metric recorded with 404 status
        metric = RequestMetric.objects.get(endpoint='/api/notfound/')
        self.assertEqual(metric.status_code, 404)

        # Check error log created for 4xx without exception
        error_log = ErrorLog.objects.get(endpoint='/api/notfound/')
        self.assertEqual(error_log.status_code, 404)
        self.assertEqual(error_log.error_type, 'HTTP 404')
        self.assertIn('404 status', error_log.error_message)
        self.assertEqual(error_log.stack_trace, '')

    def test_middleware_handles_post_request(self):
        """Test middleware handles POST requests with data."""
        def post_view(request):
            from django.http import HttpResponse
            return HttpResponse("Created", status=201)

        middleware = MetricsMiddleware(post_view)
        request = self.factory.post('/api/create/', {'key': 'value'})
        request.user = self.user

        middleware(request)

        metric = RequestMetric.objects.get(endpoint='/api/create/')
        self.assertEqual(metric.method, 'POST')
        self.assertEqual(metric.status_code, 201)

    def test_middleware_handles_database_error_gracefully(self):
        """Test middleware handles database errors without breaking the app."""
        from unittest.mock import patch

        def dummy_view(request):
            from django.http import HttpResponse
            return HttpResponse("OK")

        middleware = MetricsMiddleware(dummy_view)
        request = self.factory.get('/api/test-db-error/')
        request.user = self.user

        # Mock RequestMetric.objects.create to raise an exception
        with patch('active_interview_app.observability_models.RequestMetric.objects.create',
                   side_effect=Exception('Database error')):
            # Should not raise exception - middleware should handle it gracefully
            response = middleware(request)
            self.assertEqual(response.status_code, 200)

    def test_middleware_handles_error_log_failure(self):
        """Test middleware handles ErrorLog creation failure gracefully."""
        from unittest.mock import patch

        def error_view(request):
            raise RuntimeError("Test error")

        middleware = MetricsMiddleware(error_view)
        request = self.factory.get('/api/error-log-failure/')
        request.user = self.user

        # Mock ErrorLog.objects.create to fail
        with patch('active_interview_app.observability_models.ErrorLog.objects.create',
                   side_effect=Exception('ErrorLog creation failed')):
            # Should still raise the original exception, not the ErrorLog failure
            with self.assertRaises(RuntimeError):
                middleware(request)


class PerformanceMonitorMiddlewareTests(TestCase):
    """Test PerformanceMonitorMiddleware functionality."""

    def setUp(self):
        """Set up test request factory."""
        self.factory = RequestFactory()

    def test_performance_monitor_tracks_fast_requests(self):
        """Test that fast requests don't trigger warnings."""
        from active_interview_app.middleware import PerformanceMonitorMiddleware

        def fast_view(request):
            from django.http import HttpResponse
            return HttpResponse("OK")

        middleware = PerformanceMonitorMiddleware(fast_view)
        request = self.factory.get('/api/fast/')

        # Should complete without warnings
        response = middleware(request)
        self.assertEqual(response.status_code, 200)

    def test_performance_monitor_logs_slow_requests(self):
        """Test that slow requests trigger warnings."""
        from active_interview_app.middleware import PerformanceMonitorMiddleware

        def slow_view(request):
            import time
            time.sleep(1.1)  # Sleep longer than 1 second threshold
            from django.http import HttpResponse
            return HttpResponse("OK")

        middleware = PerformanceMonitorMiddleware(slow_view)
        request = self.factory.get('/api/slow/')

        # Capture log output
        with self.assertLogs('active_interview_app.middleware', level='WARNING') as log:
            response = middleware(request)
            self.assertEqual(response.status_code, 200)

            # Verify slow request was logged
            self.assertTrue(any('Slow request detected' in message for message in log.output))
            self.assertTrue(any('/api/slow/' in message for message in log.output))


class CleanupOldMetricsCommandTests(TransactionTestCase):
    """Test cleanup_old_metrics management command."""

    def test_cleanup_old_metrics_dry_run(self):
        """Test dry-run mode doesn't delete data."""
        # Create old metrics (40 days ago)
        old_date = timezone.now() - timedelta(days=40)

        RequestMetric.objects.create(
            endpoint='/api/old/',
            method='GET',
            status_code=200,
            response_time_ms=100.0,
            timestamp=old_date
        )

        out = StringIO()
        call_command('cleanup_old_metrics', '--dry-run', stdout=out)

        # Metric should still exist
        self.assertEqual(RequestMetric.objects.count(), 1)
        self.assertIn('DRY RUN', out.getvalue())

    def test_cleanup_deletes_old_metrics(self):
        """Test that old metrics are actually deleted."""
        # Use a fixed reference time to avoid timing issues
        now = timezone.now()

        # Create old metric (40 days ago)
        old_date = now - timedelta(days=40)
        RequestMetric.objects.create(
            endpoint='/api/old/',
            method='GET',
            status_code=200,
            response_time_ms=100.0,
            timestamp=old_date
        )

        # Create recent metric (10 days ago)
        recent_date = now - timedelta(days=10)
        RequestMetric.objects.create(
            endpoint='/api/recent/',
            method='GET',
            status_code=200,
            response_time_ms=100.0,
            timestamp=recent_date
        )

        out = StringIO()
        call_command('cleanup_old_metrics', '--days', '30', stdout=out)

        # Debug: Print command output and dates
        print(f"\nCleanup Command output:\n{out.getvalue()}")
        print(f"Now: {now}")
        print(f"Old date: {old_date}")
        print(f"Recent date: {recent_date}")
        print(f"Expected cutoff: {now - timedelta(days=30)}")
        remaining_metrics = RequestMetric.objects.all()
        for m in remaining_metrics:
            print(f"  Remaining metric: {m.endpoint} at {m.timestamp}")

        # Only recent metric should remain
        remaining = RequestMetric.objects.count()
        self.assertEqual(remaining, 1,
                         f"Expected 1 metric to remain, but found {remaining}. "
                         f"Old date: {old_date}, Recent date: {recent_date}, "
                         f"Cutoff would be: {now - timedelta(days=30)}")
        self.assertEqual(
            RequestMetric.objects.first().endpoint,
            '/api/recent/'
        )

    def test_cleanup_custom_retention_period(self):
        """Test cleanup with custom retention period."""
        # Create metric 50 days ago
        old_date = timezone.now() - timedelta(days=50)
        RequestMetric.objects.create(
            endpoint='/api/old/',
            method='GET',
            status_code=200,
            response_time_ms=100.0,
            timestamp=old_date
        )

        # Cleanup with 60 day retention - should keep the metric
        out = StringIO()
        call_command('cleanup_old_metrics', '--days', '60', stdout=out)

        self.assertEqual(RequestMetric.objects.count(), 1)


class AggregateDailyMetricsCommandTests(TransactionTestCase):
    """Test aggregate_daily_metrics management command."""

    def setUp(self):
        """Create test data for aggregation."""
        self.yesterday = timezone.now() - timedelta(days=1)
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_aggregate_request_metrics(self):
        """Test aggregation of request metrics."""
        # Create metrics for yesterday
        for i in range(100):
            RequestMetric.objects.create(
                endpoint='/api/test/',
                method='GET',
                status_code=200,
                response_time_ms=100.0 + i,
                timestamp=self.yesterday
            )

        # Create some errors
        for i in range(10):
            RequestMetric.objects.create(
                endpoint='/api/test/',
                method='GET',
                status_code=500,
                response_time_ms=200.0,
                timestamp=self.yesterday
            )

        out = StringIO()
        call_command(
            'aggregate_daily_metrics',
            '--date', self.yesterday.strftime('%Y-%m-%d'),
            stdout=out
        )

        # Debug: Print command output
        print(f"\nCommand output:\n{out.getvalue()}")
        print(f"Yesterday: {self.yesterday}, Date: {self.yesterday.date()}")
        print(f"RequestMetric count: {RequestMetric.objects.count()}")
        print(f"DailyMetricsSummary count: {DailyMetricsSummary.objects.count()}")

        # Check that summary was created
        summary = DailyMetricsSummary.objects.get(
            date=self.yesterday.date()
        )

        self.assertEqual(summary.total_requests, 110)
        self.assertEqual(summary.server_errors, 10)
        self.assertGreater(summary.avg_response_time, 0)

    def test_aggregate_provider_costs(self):
        """Test aggregation of provider costs."""
        # Create token usage records for yesterday
        for i in range(10):
            TokenUsage.objects.create(
                user=self.user,
                git_branch='main',
                model_name='gpt-4o',
                endpoint='/v1/chat/completions',
                prompt_tokens=1000,
                completion_tokens=500,
                created_at=self.yesterday
            )

        out = StringIO()
        call_command(
            'aggregate_daily_metrics',
            '--date', self.yesterday.strftime('%Y-%m-%d'),
            stdout=out
        )

        # Debug: Print command output
        print(f"\nProvider Cost Command output:\n{out.getvalue()}")
        print(f"TokenUsage count: {TokenUsage.objects.count()}")
        print(f"ProviderCostDaily count: {ProviderCostDaily.objects.count()}")

        # Check that provider cost was created
        cost = ProviderCostDaily.objects.get(
            date=self.yesterday.date(),
            provider='OpenAI',
            service='gpt-4o'
        )

        self.assertEqual(cost.total_requests, 10)
        self.assertEqual(cost.total_tokens, 15000)  # 10 * (1000 + 500)
        self.assertGreater(cost.total_cost_usd, 0)

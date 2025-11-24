"""
Tests for observability dashboard views and APIs.

Related to Issues #14, #15 (Observability Dashboard).
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
import json

from active_interview_app.observability_models import (
    RequestMetric,
    ProviderCostDaily
)


class ObservabilityDashboardViewTests(TestCase):
    """Test main dashboard view."""

    def setUp(self):
        """Create test user."""
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='user',
            password='testpass123',
            is_staff=False
        )

    def test_dashboard_requires_staff(self):
        """Test that dashboard requires staff login."""
        # Unauthenticated
        response = self.client.get(reverse('observability_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Regular user
        self.client.login(username='user', password='testpass123')
        response = self.client.get(reverse('observability_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect

    def test_dashboard_accessible_to_staff(self):
        """Test that staff can access dashboard."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('observability_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Observability Dashboard')
        self.assertContains(response, 'chartRPS')
        self.assertContains(response, 'chartLatency')
        self.assertContains(response, 'chartErrors')
        self.assertContains(response, 'chartCosts')

    def test_dashboard_includes_time_ranges(self):
        """Test that dashboard includes time range options."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('observability_dashboard'))
        self.assertContains(response, '1 Hour')
        self.assertContains(response, '24 Hours')
        self.assertContains(response, '7 Days')
        self.assertContains(response, '30 Days')


class RPSMetricsAPITests(TestCase):
    """Test RPS metrics API endpoint."""

    def setUp(self):
        """Create test data."""
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='admin', password='testpass123')

        # Create test metrics
        now = timezone.now()
        for i in range(10):
            RequestMetric.objects.create(
                endpoint='/api/test/',
                method='GET',
                status_code=200,
                response_time_ms=100.0,
                timestamp=now - timedelta(minutes=i)
            )

    def test_rps_api_requires_staff(self):
        """Test that RPS API requires staff login."""
        self.client.logout()
        response = self.client.get(reverse('api_metrics_rps'))
        self.assertEqual(response.status_code, 302)

    def test_rps_api_returns_json(self):
        """Test that RPS API returns JSON data."""
        response = self.client.get(reverse('api_metrics_rps'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        data = json.loads(response.content)
        self.assertEqual(data['metric'], 'rps')
        self.assertIn('data', data)
        self.assertIsInstance(data['data'], list)

    def test_rps_api_filters_by_time_range(self):
        """Test that RPS API filters by time range."""
        # Test 1h time range
        response = self.client.get(reverse('api_metrics_rps') + '?time_range=1h')
        data = json.loads(response.content)
        self.assertEqual(data['time_range'], '1h')

        # Test 24h time range
        response = self.client.get(reverse('api_metrics_rps') + '?time_range=24h')
        data = json.loads(response.content)
        self.assertEqual(data['time_range'], '24h')

    def test_rps_api_data_structure(self):
        """Test RPS API data structure."""
        response = self.client.get(reverse('api_metrics_rps'))
        data = json.loads(response.content)

        # Check data point structure
        if len(data['data']) > 0:
            point = data['data'][0]
            self.assertIn('timestamp', point)
            self.assertIn('value', point)
            self.assertIsInstance(point['value'], (int, float))


class LatencyMetricsAPITests(TestCase):
    """Test latency metrics API endpoint."""

    def setUp(self):
        """Create test data."""
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='admin', password='testpass123')

        # Create test metrics with varying response times
        now = timezone.now()
        for i in range(50):
            RequestMetric.objects.create(
                endpoint='/api/test/',
                method='GET',
                status_code=200,
                response_time_ms=50.0 + i,
                timestamp=now - timedelta(seconds=i)
            )

    def test_latency_api_returns_percentiles(self):
        """Test that latency API returns p50 and p95."""
        response = self.client.get(reverse('api_metrics_latency'))
        data = json.loads(response.content)

        self.assertEqual(data['metric'], 'latency')
        if len(data['data']) > 0:
            point = data['data'][0]
            self.assertIn('p50', point)
            self.assertIn('p95', point)
            self.assertIn('mean', point)


class ErrorMetricsAPITests(TestCase):
    """Test error metrics API endpoint."""

    def setUp(self):
        """Create test data."""
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='admin', password='testpass123')

        # Create mix of successful and error requests
        now = timezone.now()
        for i in range(70):
            RequestMetric.objects.create(
                endpoint='/api/test/',
                method='GET',
                status_code=200,
                response_time_ms=100.0,
                timestamp=now - timedelta(seconds=i)
            )
        for i in range(30):
            RequestMetric.objects.create(
                endpoint='/api/test/',
                method='GET',
                status_code=500,
                response_time_ms=100.0,
                timestamp=now - timedelta(seconds=70 + i)
            )

    def test_error_api_returns_error_rate(self):
        """Test that error API returns error rate."""
        response = self.client.get(reverse('api_metrics_errors'))
        data = json.loads(response.content)

        self.assertEqual(data['metric'], 'error_rate')
        if len(data['data']) > 0:
            point = data['data'][0]
            self.assertIn('error_rate', point)
            self.assertIn('total_requests', point)
            self.assertIn('error_count', point)


class CostMetricsAPITests(TestCase):
    """Test cost metrics API endpoint."""

    def setUp(self):
        """Create test data."""
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='admin', password='testpass123')

        # Create provider cost data
        today = timezone.now().date()
        ProviderCostDaily.objects.create(
            date=today,
            provider='OpenAI',
            service='gpt-4o',
            total_requests=100,
            total_cost_usd=5.50,
            total_tokens=10000,
            prompt_tokens=7000,
            completion_tokens=3000
        )

    def test_cost_api_returns_cost_data(self):
        """Test that cost API returns cost data."""
        response = self.client.get(reverse('api_metrics_costs'))
        data = json.loads(response.content)

        self.assertEqual(data['metric'], 'costs')
        self.assertIn('data', data)
        if len(data['data']) > 0:
            point = data['data'][0]
            self.assertIn('date', point)
            self.assertIn('total_cost', point)
            self.assertIn('by_service', point)


class ExportMetricsAPITests(TestCase):
    """Test metrics export API endpoint."""

    def setUp(self):
        """Create test data."""
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='admin', password='testpass123')

        # Create test metrics
        now = timezone.now()
        for i in range(10):
            RequestMetric.objects.create(
                endpoint='/api/test/',
                method='GET',
                status_code=200,
                response_time_ms=100.0,
                timestamp=now - timedelta(minutes=i)
            )

    def test_export_api_requires_staff(self):
        """Test that export API requires staff login."""
        self.client.logout()
        response = self.client.get(reverse('api_export_metrics'))
        self.assertEqual(response.status_code, 302)

    def test_export_api_returns_csv(self):
        """Test that export API returns CSV."""
        response = self.client.get(reverse('api_export_metrics'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])

    def test_export_api_includes_headers(self):
        """Test that export CSV includes headers."""
        response = self.client.get(reverse('api_export_metrics') + '?metrics=rps,latency,errors')
        content = response.content.decode('utf-8')

        self.assertIn('timestamp', content)
        self.assertIn('rps', content)
        self.assertIn('p50_latency', content)
        self.assertIn('p95_latency', content)
        self.assertIn('error_rate', content)

    def test_export_api_filters_metrics(self):
        """Test that export API can filter specific metrics."""
        # Export only RPS
        response = self.client.get(reverse('api_export_metrics') + '?metrics=rps')
        content = response.content.decode('utf-8')

        self.assertIn('timestamp', content)
        self.assertIn('rps', content)
        self.assertNotIn('p50_latency', content)

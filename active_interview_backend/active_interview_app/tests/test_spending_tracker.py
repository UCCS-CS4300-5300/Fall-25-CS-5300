"""
Tests for monthly spending tracker functionality.

Related to Issues #10, #11, #12 (Cost Caps & API Key Rotation, Track Monthly Spending,
Set Monthly Spend Cap).

This test suite covers:
- MonthlySpendingCap model functionality
- MonthlySpending model functionality
- Automatic spending tracking via signals
- Admin dashboard views for spending monitoring
- Management commands for spending cap configuration
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal

from active_interview_app.spending_tracker_models import (
    MonthlySpendingCap,
    MonthlySpending
)
from active_interview_app.token_usage_models import TokenUsage


class MonthlySpendingCapModelTest(TestCase):
    """Test MonthlySpendingCap model."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass',
            is_staff=True
        )

    def test_create_spending_cap(self):
        """Test creating a spending cap."""
        cap = MonthlySpendingCap.objects.create(  # noqa: F841
            cap_amount_usd=Decimal('200.00'),
            is_active=True,
            created_by=self.admin_user
        )

        self.assertEqual(cap.cap_amount_usd, Decimal('200.00'))
        self.assertTrue(cap.is_active)
        self.assertEqual(cap.created_by, self.admin_user)

    def test_only_one_active_cap(self):
        """Test that only one cap can be active at a time."""
        cap1 = MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('100.00'),
            is_active=True
        )

        cap2 = MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('200.00'),
            is_active=True
        )

        # Refresh cap1 from database
        cap1.refresh_from_db()

        # cap1 should now be inactive
        self.assertFalse(cap1.is_active)
        self.assertTrue(cap2.is_active)

    def test_get_active_cap(self):
        """Test retrieving the active cap."""
        # No cap initially
        self.assertIsNone(MonthlySpendingCap.get_active_cap())

        # Create active cap
        cap = MonthlySpendingCap.objects.create(  # noqa: F841
            cap_amount_usd=Decimal('200.00'),
            is_active=True
        )

        # Should return the active cap
        active_cap = MonthlySpendingCap.get_active_cap()
        self.assertIsNotNone(active_cap)
        self.assertEqual(active_cap.cap_amount_usd, Decimal('200.00'))

    def test_str_representation(self):
        """Test string representation of cap."""
        cap = MonthlySpendingCap.objects.create(  # noqa: F841
            cap_amount_usd=Decimal('200.00'),
            is_active=True
        )

        self.assertIn('$200', str(cap))
        self.assertIn('Active', str(cap))


class MonthlySpendingModelTest(TestCase):
    """Test MonthlySpending model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_create_monthly_spending(self):
        """Test creating a monthly spending record."""
        spending = MonthlySpending.objects.create(
            year=2025,
            month=11
        )

        self.assertEqual(spending.year, 2025)
        self.assertEqual(spending.month, 11)
        self.assertEqual(spending.total_cost_usd, Decimal('0.0'))

    def test_get_current_month(self):
        """Test getting current month's spending."""
        spending = MonthlySpending.get_current_month()

        now = timezone.now()
        self.assertEqual(spending.year, now.year)
        self.assertEqual(spending.month, now.month)

    def test_add_llm_cost(self):
        """Test adding LLM cost to monthly spending."""
        spending = MonthlySpending.get_current_month()
        initial_cost = spending.total_cost_usd

        spending.add_llm_cost(5.50)

        self.assertEqual(spending.llm_cost_usd, Decimal('5.50'))
        self.assertEqual(spending.llm_requests, 1)
        self.assertEqual(spending.total_cost_usd, initial_cost + Decimal('5.50'))
        self.assertEqual(spending.total_requests, 1)

    def test_add_multiple_costs(self):
        """Test adding multiple costs."""
        spending = MonthlySpending.get_current_month()

        spending.add_llm_cost(2.50)
        spending.add_llm_cost(3.00)
        spending.add_tts_cost(0.50)

        self.assertEqual(spending.llm_cost_usd, Decimal('5.50'))
        self.assertEqual(spending.tts_cost_usd, Decimal('0.50'))
        self.assertEqual(spending.total_cost_usd, Decimal('6.00'))
        self.assertEqual(spending.llm_requests, 2)
        self.assertEqual(spending.tts_requests, 1)
        self.assertEqual(spending.total_requests, 3)

    def test_get_percentage_of_cap_no_cap(self):
        """Test percentage calculation when no cap is set."""
        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(50.00)

        percentage = spending.get_percentage_of_cap()
        self.assertIsNone(percentage)

    def test_get_percentage_of_cap_with_cap(self):
        """Test percentage calculation with cap."""
        MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('200.00'),
            is_active=True
        )

        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(50.00)

        percentage = spending.get_percentage_of_cap()
        self.assertAlmostEqual(percentage, 25.0, places=1)

    def test_is_over_cap(self):
        """Test checking if spending exceeds cap."""
        MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('100.00'),
            is_active=True
        )

        spending = MonthlySpending.get_current_month()

        # Below cap
        spending.add_llm_cost(50.00)
        self.assertFalse(spending.is_over_cap())

        # Over cap
        spending.add_llm_cost(60.00)
        self.assertTrue(spending.is_over_cap())

    def test_get_remaining_budget(self):
        """Test calculating remaining budget."""
        MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('200.00'),
            is_active=True
        )

        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(75.00)

        remaining = spending.get_remaining_budget()
        self.assertEqual(remaining, Decimal('125.00'))

    def test_get_cap_status_with_cap(self):
        """Test getting comprehensive cap status."""
        MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('200.00'),
            is_active=True
        )

        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(150.00)

        status = spending.get_cap_status()

        self.assertTrue(status['has_cap'])
        self.assertEqual(status['cap_amount'], 200.00)
        self.assertEqual(status['spent'], 150.00)
        self.assertEqual(status['remaining'], 50.00)
        self.assertAlmostEqual(status['percentage'], 75.0, places=1)
        self.assertEqual(status['alert_level'], 'warning')
        self.assertFalse(status['is_over_cap'])

    def test_get_cap_status_alert_levels(self):
        """Test different alert levels."""
        MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('100.00'),
            is_active=True
        )

        spending = MonthlySpending.get_current_month()

        # OK level (< 50%)
        spending.add_llm_cost(40.00)
        self.assertEqual(spending.get_cap_status()['alert_level'], 'ok')

        # Caution level (50-75%)
        spending.add_llm_cost(15.00)  # Total: 55
        self.assertEqual(spending.get_cap_status()['alert_level'], 'caution')

        # Warning level (75-90%)
        spending.add_llm_cost(25.00)  # Total: 80
        self.assertEqual(spending.get_cap_status()['alert_level'], 'warning')

        # Critical level (90-100%)
        spending.add_llm_cost(15.00)  # Total: 95
        self.assertEqual(spending.get_cap_status()['alert_level'], 'critical')

        # Danger level (>= 100%)
        spending.add_llm_cost(10.00)  # Total: 105
        self.assertEqual(spending.get_cap_status()['alert_level'], 'danger')

    def test_update_from_token_usage(self):
        """Test updating spending from TokenUsage records."""
        now = timezone.now()
        spending = MonthlySpending.objects.create(
            year=now.year,
            month=now.month
        )

        # Create some TokenUsage records
        TokenUsage.objects.create(
            user=self.user,
            git_branch='test',
            model_name='gpt-4o',
            endpoint='/api/test',
            prompt_tokens=1000,
            completion_tokens=500
        )

        TokenUsage.objects.create(
            user=self.user,
            git_branch='test',
            model_name='gpt-4o',
            endpoint='/api/test',
            prompt_tokens=2000,
            completion_tokens=1000
        )

        # Update spending from TokenUsage
        summary = spending.update_from_token_usage()

        self.assertGreater(summary['llm_cost'], 0)
        self.assertEqual(summary['llm_requests'], 2)
        self.assertGreater(spending.total_cost_usd, Decimal('0.0'))


class SpendingTrackerSignalTest(TestCase):
    """Test automatic spending tracking via signals."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_token_usage_creates_spending_record(self):
        """Test that creating TokenUsage automatically updates spending."""
        # Create TokenUsage record
        token_usage = TokenUsage.objects.create(  # noqa: F841
            user=self.user,
            git_branch='test',
            model_name='gpt-4o',
            endpoint='/api/test',
            prompt_tokens=1000,
            completion_tokens=500
        )

        # Check that monthly spending was updated
        spending = MonthlySpending.get_current_month()

        self.assertGreater(spending.total_cost_usd, Decimal('0.0'))
        self.assertEqual(spending.llm_requests, 1)


class SpendingTrackerViewTest(TestCase):
    """Test spending tracker API views."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass',
            is_staff=True,
            is_superuser=True
        )
        self.client.login(username='admin', password='testpass')

    def test_api_update_spending_cap_success(self):
        """Test updating spending cap via API."""
        url = reverse('api_update_spending_cap')

        response = self.client.post(
            url,
            data='{"cap_amount": 250.00}',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('250.00', data['message'])
        self.assertEqual(data['cap']['amount'], 250.00)
        self.assertEqual(data['cap']['created_by'], 'admin')

        # Verify cap was created
        cap = MonthlySpendingCap.get_active_cap()
        self.assertIsNotNone(cap)
        self.assertEqual(cap.cap_amount_usd, Decimal('250.00'))

    def test_api_update_spending_cap_validation(self):
        """Test spending cap validation."""
        url = reverse('api_update_spending_cap')

        # Test negative number
        response = self.client.post(
            url,
            data='{"cap_amount": -100}',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('positive', data['error'].lower())

        # Test zero
        response = self.client.post(
            url,
            data='{"cap_amount": 0}',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])

        # Test non-numeric
        response = self.client.post(
            url,
            data='{"cap_amount": "not a number"}',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])

    def test_api_update_spending_cap_requires_staff(self):
        """Test that cap update requires staff permission."""
        # Logout admin
        self.client.logout()

        # Login as regular user
        _regular_user = User.objects.create_user(  # noqa: F841
            username='regular',
            password='testpass'
        )
        self.client.login(username='regular', password='testpass')

        url = reverse('api_update_spending_cap')
        response = self.client.post(
            url,
            data='{"cap_amount": 200}',
            content_type='application/json'
        )

        # Should be redirected to login
        self.assertEqual(response.status_code, 302)

    def test_api_update_spending_cap_replaces_old(self):
        """Test that new cap replaces old active cap."""
        # Create initial cap
        old_cap = MonthlySpendingCap.objects.create(  # noqa: F841
            cap_amount_usd=Decimal('100.00'),
            is_active=True
        )

        # Update cap via API
        url = reverse('api_update_spending_cap')
        response = self.client.post(
            url,
            data='{"cap_amount": 200}',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        # Refresh old cap from database
        old_cap.refresh_from_db()

        # Old cap should be inactive
        self.assertFalse(old_cap.is_active)

        # New cap should be active
        new_cap = MonthlySpendingCap.get_active_cap()
        self.assertTrue(new_cap.is_active)
        self.assertEqual(new_cap.cap_amount_usd, Decimal('200.00'))

    def test_api_spending_current_month(self):
        """Test current month spending API endpoint."""
        # Set up data
        MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('200.00'),
            is_active=True
        )

        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(75.00)
        spending.add_tts_cost(10.00)

        # Make request
        url = reverse('api_spending_current_month')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['total_cost'], 85.00)
        self.assertEqual(data['llm_cost'], 75.00)
        self.assertEqual(data['tts_cost'], 10.00)
        self.assertTrue(data['cap_status']['has_cap'])
        self.assertEqual(data['cap_status']['cap_amount'], 200.00)

    def test_api_spending_history(self):
        """Test spending history API endpoint."""
        # Create some historical data
        MonthlySpending.objects.create(
            year=2025,
            month=10,
            total_cost_usd=Decimal('150.00'),
            llm_cost_usd=Decimal('150.00')
        )

        MonthlySpending.objects.create(
            year=2025,
            month=11,
            total_cost_usd=Decimal('175.00'),
            llm_cost_usd=Decimal('175.00')
        )

        # Make request
        url = reverse('api_spending_history')
        response = self.client.get(url + '?months=3')

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('months', data)
        self.assertGreaterEqual(len(data['months']), 2)

    def test_spending_views_require_staff(self):
        """Test that spending views require staff permission."""
        # Logout admin
        self.client.logout()

        # Login as regular user
        _regular_user = User.objects.create_user(  # noqa: F841
            username='regular',
            password='testpass'
        )
        self.client.login(username='regular', password='testpass')

        # Try to access spending endpoint
        url = reverse('api_spending_current_month')
        response = self.client.get(url)

        # Should be redirected to login
        self.assertEqual(response.status_code, 302)


class SpendingTrackerIntegrationTest(TestCase):
    """Integration tests for complete spending tracking workflow."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass',
            is_staff=True
        )

    def test_complete_spending_tracking_workflow(self):
        """Test complete workflow from API call to dashboard display."""
        # 1. Set spending cap
        cap = MonthlySpendingCap.objects.create(  # noqa: F841
            cap_amount_usd=Decimal('200.00'),
            is_active=True,
            created_by=self.admin_user
        )

        # 2. Simulate API calls (TokenUsage creation)
        for i in range(5):
            TokenUsage.objects.create(
                user=self.user,
                git_branch='test',
                model_name='gpt-4o',
                endpoint='/api/test',
                prompt_tokens=1000,
                completion_tokens=500
            )

        # 3. Check monthly spending was updated
        spending = MonthlySpending.get_current_month()

        self.assertEqual(spending.llm_requests, 5)
        self.assertGreater(spending.total_cost_usd, Decimal('0.0'))

        # 4. Verify cap status
        cap_status = spending.get_cap_status()

        self.assertTrue(cap_status['has_cap'])
        self.assertFalse(cap_status['is_over_cap'])

    def test_over_budget_scenario(self):
        """Test scenario where spending exceeds cap."""
        # Set low cap
        MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('1.00'),  # Very low cap
            is_active=True
        )

        # Create expensive API calls
        for i in range(10):
            TokenUsage.objects.create(
                user=self.user,
                git_branch='test',
                model_name='gpt-4o',
                endpoint='/api/test',
                prompt_tokens=5000,
                completion_tokens=3000
            )

        spending = MonthlySpending.get_current_month()
        cap_status = spending.get_cap_status()

        # Should be over budget
        self.assertTrue(cap_status['is_over_cap'])
        self.assertEqual(cap_status['alert_level'], 'danger')

"""
Tests for model_tier_manager.py - Cost Control and Fallback Switching

Related to Issue #10 (Cost Caps & API Key Rotation) and Issue #14 (Automatic Fallback).

This test suite covers:
- Active tier determination based on spending
- Model selection for different tiers and providers
- Tier information retrieval
- Fallback switching logic
- Cost estimation for different tiers
"""
from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from unittest.mock import patch, MagicMock

from active_interview_app import model_tier_manager
from active_interview_app.spending_tracker_models import (
    MonthlySpendingCap,
    MonthlySpending
)


class GetActiveTierTest(TestCase):
    """Test get_active_tier() function."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass',
            is_staff=True
        )

    def test_force_tier_override(self):
        """Test that force_tier parameter overrides all logic."""
        # Force each tier
        self.assertEqual(model_tier_manager.get_active_tier(force_tier='premium'), 'premium')
        self.assertEqual(model_tier_manager.get_active_tier(force_tier='standard'), 'standard')
        self.assertEqual(model_tier_manager.get_active_tier(force_tier='fallback'), 'fallback')

    def test_normal_operation_returns_premium(self):
        """Test that normal operation returns premium tier."""
        # No spending cap set
        tier = model_tier_manager.get_active_tier()
        self.assertEqual(tier, 'premium')

        # Set cap but no spending
        MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('200.00'),
            is_active=True
        )
        tier = model_tier_manager.get_active_tier()
        self.assertEqual(tier, 'premium')

    def test_over_cap_returns_fallback(self):
        """Test that exceeding cap returns fallback tier."""
        # Set cap
        MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('100.00'),
            is_active=True
        )

        # Add spending that exceeds cap
        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(150.00)

        tier = model_tier_manager.get_active_tier()
        self.assertEqual(tier, 'fallback')

    def test_approaching_cap_returns_standard(self):
        """Test that approaching cap (>=85%) returns standard tier."""
        # Set cap
        MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('100.00'),
            is_active=True
        )

        # Add spending at 85%
        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(85.00)

        tier = model_tier_manager.get_active_tier()
        self.assertEqual(tier, 'standard')

    def test_at_85_percent_exactly(self):
        """Test boundary condition at exactly 85% of cap."""
        MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('200.00'),
            is_active=True
        )

        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(170.00)  # 85%

        tier = model_tier_manager.get_active_tier()
        self.assertEqual(tier, 'standard')

    def test_below_85_percent_returns_premium(self):
        """Test that below 85% returns premium tier."""
        MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('100.00'),
            is_active=True
        )

        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(80.00)  # 80%

        tier = model_tier_manager.get_active_tier()
        self.assertEqual(tier, 'premium')

    @patch('django.db.connection')
    def test_database_not_ready_returns_premium(self, mock_connection):
        """Test that when database is not ready, returns premium."""
        mock_connection.introspection.table_names.return_value = []

        tier = model_tier_manager.get_active_tier()
        self.assertEqual(tier, 'premium')

    def test_exception_handling_returns_premium(self):
        """Test that exceptions default to premium tier."""
        with patch('active_interview_app.spending_tracker_models.MonthlySpending.get_current_month') as mock_get:
            mock_get.side_effect = Exception("Database error")

            tier = model_tier_manager.get_active_tier()
            self.assertEqual(tier, 'premium')


class GetModelForTierTest(TestCase):
    """Test get_model_for_tier() function."""

    def test_openai_premium_tier(self):
        """Test OpenAI premium tier returns correct model."""
        model = model_tier_manager.get_model_for_tier(tier='premium', provider='openai')
        self.assertEqual(model, 'gpt-4o')

    def test_openai_standard_tier(self):
        """Test OpenAI standard tier returns correct model."""
        model = model_tier_manager.get_model_for_tier(tier='standard', provider='openai')
        self.assertEqual(model, 'gpt-4-turbo')

    def test_openai_fallback_tier(self):
        """Test OpenAI fallback tier returns correct model."""
        model = model_tier_manager.get_model_for_tier(tier='fallback', provider='openai')
        self.assertEqual(model, 'gpt-3.5-turbo')

    def test_anthropic_premium_tier(self):
        """Test Anthropic premium tier returns correct model."""
        model = model_tier_manager.get_model_for_tier(tier='premium', provider='anthropic')
        self.assertEqual(model, 'claude-opus-4-20250514')

    def test_anthropic_standard_tier(self):
        """Test Anthropic standard tier returns correct model."""
        model = model_tier_manager.get_model_for_tier(tier='standard', provider='anthropic')
        self.assertEqual(model, 'claude-sonnet-4-5-20250929')

    def test_anthropic_fallback_tier(self):
        """Test Anthropic fallback tier returns correct model."""
        model = model_tier_manager.get_model_for_tier(tier='fallback', provider='anthropic')
        self.assertEqual(model, 'claude-haiku-3-5-20241022')

    def test_invalid_tier_returns_default(self):
        """Test that invalid tier returns default model."""
        model = model_tier_manager.get_model_for_tier(tier='invalid', provider='openai')
        self.assertEqual(model, 'gpt-4o')

    def test_invalid_provider_returns_default(self):
        """Test that invalid provider returns default model."""
        model = model_tier_manager.get_model_for_tier(tier='premium', provider='invalid')
        self.assertEqual(model, 'gpt-4o')

    def test_default_parameters(self):
        """Test function with default parameters."""
        model = model_tier_manager.get_model_for_tier()
        self.assertEqual(model, 'gpt-4o')


class GetTierInfoTest(TestCase):
    """Test get_tier_info() function."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass',
            is_staff=True
        )

    def test_normal_operations_info(self):
        """Test tier info during normal operations."""
        MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('200.00'),
            is_active=True
        )

        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(50.00)  # 25% of cap

        info = model_tier_manager.get_tier_info()

        self.assertEqual(info['active_tier'], 'premium')
        self.assertEqual(info['model'], 'gpt-4o')
        self.assertEqual(info['reason'], 'Normal operations')
        self.assertIsNotNone(info['spending_info'])
        self.assertEqual(info['tier_cost_multiplier'], 10.0)

    def test_over_cap_info(self):
        """Test tier info when over cap."""
        MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('100.00'),
            is_active=True
        )

        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(120.00)  # Over cap

        info = model_tier_manager.get_tier_info()

        self.assertEqual(info['active_tier'], 'fallback')
        self.assertEqual(info['model'], 'gpt-3.5-turbo')
        self.assertIn('Budget exceeded', info['reason'])
        self.assertTrue(info['spending_info']['is_over_cap'])
        self.assertEqual(info['tier_cost_multiplier'], 1.0)

    def test_approaching_cap_info(self):
        """Test tier info when approaching cap."""
        MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('100.00'),
            is_active=True
        )

        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(90.00)  # 90% of cap

        info = model_tier_manager.get_tier_info()

        self.assertEqual(info['active_tier'], 'standard')
        self.assertEqual(info['model'], 'gpt-4-turbo')
        self.assertIn('Approaching cap', info['reason'])
        self.assertEqual(info['tier_cost_multiplier'], 5.0)

    def test_exception_handling(self):
        """Test tier info when spending tracker not configured."""
        with patch('active_interview_app.spending_tracker_models.MonthlySpending.get_current_month') as mock_get:
            mock_get.side_effect = Exception("Database error")

            info = model_tier_manager.get_tier_info()

            self.assertEqual(info['active_tier'], 'premium')
            self.assertEqual(info['model'], 'gpt-4o')
            self.assertIn('not configured', info['reason'])
            self.assertIsNone(info['spending_info'])
            self.assertEqual(info['tier_cost_multiplier'], 10.0)

    def test_tier_info_includes_all_fields(self):
        """Test that tier info includes all expected fields."""
        info = model_tier_manager.get_tier_info()

        required_fields = ['active_tier', 'model', 'reason', 'spending_info', 'tier_cost_multiplier']
        for field in required_fields:
            self.assertIn(field, info)


class ShouldSwitchToFallbackTest(TestCase):
    """Test should_switch_to_fallback() function."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass',
            is_staff=True
        )

    def test_within_budget_no_switch(self):
        """Test that within budget returns False."""
        MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('200.00'),
            is_active=True
        )

        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(50.00)

        should_switch, reason = model_tier_manager.should_switch_to_fallback()

        self.assertFalse(should_switch)
        self.assertEqual(reason, 'Within budget limits')

    def test_over_budget_should_switch(self):
        """Test that over budget returns True."""
        MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('100.00'),
            is_active=True
        )

        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(150.00)

        should_switch, reason = model_tier_manager.should_switch_to_fallback()

        self.assertTrue(should_switch)
        self.assertIn('cap exceeded', reason)
        self.assertIn('150', reason)  # Should include percentage

    def test_at_cap_exactly(self):
        """Test behavior when at exactly 100% of cap."""
        MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('100.00'),
            is_active=True
        )

        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(100.00)

        should_switch, reason = model_tier_manager.should_switch_to_fallback()

        # At exactly 100%, should not switch (not "over")
        self.assertFalse(should_switch)

    def test_just_over_cap(self):
        """Test behavior when just over cap."""
        MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('100.00'),
            is_active=True
        )

        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(100.01)

        should_switch, reason = model_tier_manager.should_switch_to_fallback()

        self.assertTrue(should_switch)
        self.assertIn('cap exceeded', reason)

    def test_exception_handling(self):
        """Test exception handling returns False with explanation."""
        with patch('active_interview_app.spending_tracker_models.MonthlySpending.get_current_month') as mock_get:
            mock_get.side_effect = Exception("Database error")

            should_switch, reason = model_tier_manager.should_switch_to_fallback()

            self.assertFalse(should_switch)
            self.assertIn('Unable to check spending', reason)
            self.assertIn('Database error', reason)

    def test_no_cap_set(self):
        """Test behavior when no cap is set."""
        # No cap created
        should_switch, reason = model_tier_manager.should_switch_to_fallback()

        self.assertFalse(should_switch)
        self.assertEqual(reason, 'Within budget limits')


class EstimateCostForTierTest(TestCase):
    """Test estimate_cost_for_tier() function."""

    def test_fallback_tier_cost(self):
        """Test cost estimation for fallback tier."""
        # 1000 tokens = $0.002 (1x multiplier)
        cost = model_tier_manager.estimate_cost_for_tier('fallback', 1000)
        self.assertEqual(cost, Decimal('0.002'))

    def test_standard_tier_cost(self):
        """Test cost estimation for standard tier."""
        # 1000 tokens = $0.010 (5x multiplier)
        cost = model_tier_manager.estimate_cost_for_tier('standard', 1000)
        self.assertEqual(cost, Decimal('0.010'))

    def test_premium_tier_cost(self):
        """Test cost estimation for premium tier."""
        # 1000 tokens = $0.020 (10x multiplier)
        cost = model_tier_manager.estimate_cost_for_tier('premium', 1000)
        self.assertEqual(cost, Decimal('0.020'))

    def test_large_token_count(self):
        """Test cost estimation with large token count."""
        # 100,000 tokens on premium = $2.00
        cost = model_tier_manager.estimate_cost_for_tier('premium', 100000)
        self.assertEqual(cost, Decimal('2.000'))

    def test_small_token_count(self):
        """Test cost estimation with small token count."""
        # 100 tokens on fallback = $0.0002
        cost = model_tier_manager.estimate_cost_for_tier('fallback', 100)
        self.assertEqual(cost, Decimal('0.0002'))

    def test_zero_tokens(self):
        """Test cost estimation with zero tokens."""
        cost = model_tier_manager.estimate_cost_for_tier('premium', 0)
        self.assertEqual(cost, Decimal('0.0'))

    def test_invalid_tier_uses_default(self):
        """Test that invalid tier uses default multiplier."""
        # Invalid tier should use 1.0 multiplier (fallback default)
        cost = model_tier_manager.estimate_cost_for_tier('invalid', 1000)
        self.assertEqual(cost, Decimal('0.002'))

    def test_return_type_is_decimal(self):
        """Test that return type is Decimal for precision."""
        cost = model_tier_manager.estimate_cost_for_tier('premium', 500)
        self.assertIsInstance(cost, Decimal)


class TierConstantsTest(TestCase):
    """Test tier-related constants."""

    def test_tier_to_model_structure(self):
        """Test that TIER_TO_MODEL has correct structure."""
        tiers = ['premium', 'standard', 'fallback']
        providers = ['openai', 'anthropic']

        for tier in tiers:
            self.assertIn(tier, model_tier_manager.TIER_TO_MODEL)
            for provider in providers:
                self.assertIn(provider, model_tier_manager.TIER_TO_MODEL[tier])
                # Ensure it's a non-empty string
                model_name = model_tier_manager.TIER_TO_MODEL[tier][provider]
                self.assertIsInstance(model_name, str)
                self.assertGreater(len(model_name), 0)

    def test_tier_cost_multiplier_values(self):
        """Test that tier cost multipliers are correct."""
        self.assertEqual(model_tier_manager.TIER_COST_MULTIPLIER['premium'], 10.0)
        self.assertEqual(model_tier_manager.TIER_COST_MULTIPLIER['standard'], 5.0)
        self.assertEqual(model_tier_manager.TIER_COST_MULTIPLIER['fallback'], 1.0)

    def test_openai_models_are_correct(self):
        """Test that OpenAI model names are correct."""
        self.assertEqual(model_tier_manager.TIER_TO_MODEL['premium']['openai'], 'gpt-4o')
        self.assertEqual(model_tier_manager.TIER_TO_MODEL['standard']['openai'], 'gpt-4-turbo')
        self.assertEqual(model_tier_manager.TIER_TO_MODEL['fallback']['openai'], 'gpt-3.5-turbo')

    def test_anthropic_models_are_correct(self):
        """Test that Anthropic model names are correct."""
        self.assertEqual(
            model_tier_manager.TIER_TO_MODEL['premium']['anthropic'],
            'claude-opus-4-20250514'
        )
        self.assertEqual(
            model_tier_manager.TIER_TO_MODEL['standard']['anthropic'],
            'claude-sonnet-4-5-20250929'
        )
        self.assertEqual(
            model_tier_manager.TIER_TO_MODEL['fallback']['anthropic'],
            'claude-haiku-3-5-20241022'
        )


class TierManagerIntegrationTest(TestCase):
    """Integration tests for complete tier management workflow."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass',
            is_staff=True
        )

    def test_complete_tier_progression(self):
        """Test complete progression from premium -> standard -> fallback."""
        # Set up cap
        MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('100.00'),
            is_active=True
        )

        spending = MonthlySpending.get_current_month()

        # Start: Should be premium
        tier = model_tier_manager.get_active_tier()
        self.assertEqual(tier, 'premium')

        # Add spending to 50% - still premium
        spending.add_llm_cost(50.00)
        tier = model_tier_manager.get_active_tier()
        self.assertEqual(tier, 'premium')

        # Add spending to 85% - should switch to standard
        spending.add_llm_cost(35.00)
        tier = model_tier_manager.get_active_tier()
        self.assertEqual(tier, 'standard')

        # Add spending over 100% - should switch to fallback
        spending.add_llm_cost(20.00)
        tier = model_tier_manager.get_active_tier()
        self.assertEqual(tier, 'fallback')

    def test_tier_info_consistency(self):
        """Test that tier info is consistent with active tier."""
        MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('200.00'),
            is_active=True
        )

        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(180.00)  # 90%, should be standard

        active_tier = model_tier_manager.get_active_tier()
        tier_info = model_tier_manager.get_tier_info()

        self.assertEqual(active_tier, tier_info['active_tier'])
        self.assertEqual(tier_info['active_tier'], 'standard')

    def test_cost_estimation_matches_tier(self):
        """Test that cost estimation matches selected tier."""
        MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('100.00'),
            is_active=True
        )

        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(95.00)  # Trigger standard tier

        active_tier = model_tier_manager.get_active_tier()
        cost = model_tier_manager.estimate_cost_for_tier(active_tier, 1000)

        # Standard tier should be 5x more expensive than fallback
        self.assertEqual(active_tier, 'standard')
        self.assertEqual(cost, Decimal('0.010'))

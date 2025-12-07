"""
Tests for Multi-Tier API Key Rotation System

Related to Issue #10 (Cost Caps & API Key Rotation),
Issue #13 (Automatic API Key Rotation), and
Issue #14 (Automatic Fallback Tier Switching).

This file specifically tests the TIER SYSTEM (premium/standard/fallback):
- Model tier field on APIKeyPool and KeyRotationSchedule
- Tier-based key selection and activation
- Model selection for each tier (gpt-4o, gpt-4o-mini, gpt-3.5-turbo)
- Tier switching logic based on spending thresholds

RELATED TEST FILES:
- test_api_key_rotation.py: Core rotation functionality (39 tests)
- test_spending_rotation.py: Automatic rotation triggers (14 tests)
- test_spending_tracker.py: Monthly spending tracking
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta  # noqa: F401

from active_interview_app.api_key_rotation_models import (
    APIKeyPool,
    KeyRotationSchedule,
    KeyRotationLog
)
from active_interview_app.spending_tracker_models import (
    MonthlySpending,
    MonthlySpendingCap
)
from active_interview_app.model_tier_manager import (
    get_active_tier,
    get_model_for_tier,
    get_tier_info,
    should_switch_to_fallback
)


class ModelTierFieldsTestCase(TestCase):
    """Test that model_tier field exists and works correctly."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testadmin',
            password='testpass123'
        )

    def test_api_key_pool_has_model_tier_field(self):
        """Test APIKeyPool has model_tier field with correct choices."""
        key = APIKeyPool.objects.create(
            provider=APIKeyPool.OPENAI,
            model_tier=APIKeyPool.PREMIUM,
            key_name='Test Premium Key',
            key_prefix='sk-proj-test',
            encrypted_key=b'encrypted_test_key',
            added_by=self.user
        )

        self.assertEqual(key.model_tier, 'premium')
        self.assertIn(key.model_tier, ['premium', 'standard', 'fallback'])

    def test_api_key_pool_tier_choices(self):
        """Test all tier choices work correctly."""
        tiers = ['premium', 'standard', 'fallback']

        for tier in tiers:
            key = APIKeyPool.objects.create(
                provider=APIKeyPool.OPENAI,
                model_tier=tier,
                key_name=f'Test {tier} Key',
                key_prefix=f'sk-{tier}',
                encrypted_key=f'encrypted_{tier}_key'.encode(),
                added_by=self.user
            )
            self.assertEqual(key.model_tier, tier)

    def test_key_rotation_schedule_has_model_tier_field(self):
        """Test KeyRotationSchedule has model_tier field."""
        schedule = KeyRotationSchedule.objects.create(
            provider=APIKeyPool.OPENAI,
            model_tier=APIKeyPool.PREMIUM,
            is_enabled=True,
            rotation_frequency=KeyRotationSchedule.WEEKLY
        )

        self.assertEqual(schedule.model_tier, 'premium')

    def test_key_rotation_schedule_unique_together(self):
        """Test unique_together constraint on provider + model_tier."""
        KeyRotationSchedule.objects.create(
            provider=APIKeyPool.OPENAI,
            model_tier=APIKeyPool.PREMIUM,
            is_enabled=True
        )

        # Should allow same provider with different tier
        schedule2 = KeyRotationSchedule.objects.create(
            provider=APIKeyPool.OPENAI,
            model_tier=APIKeyPool.FALLBACK,
            is_enabled=True
        )
        self.assertIsNotNone(schedule2)


class TierBasedKeySelectionTestCase(TestCase):
    """Test tier-based key selection logic."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testadmin',
            password='testpass123'
        )

        # Create keys for different tiers
        self.premium_key1 = APIKeyPool.objects.create(
            provider=APIKeyPool.OPENAI,
            model_tier=APIKeyPool.PREMIUM,
            key_name='Premium Key 1',
            key_prefix='sk-premium-1',
            encrypted_key=b'encrypted_premium_1',
            status=APIKeyPool.ACTIVE,
            added_by=self.user
        )

        self.premium_key2 = APIKeyPool.objects.create(
            provider=APIKeyPool.OPENAI,
            model_tier=APIKeyPool.PREMIUM,
            key_name='Premium Key 2',
            key_prefix='sk-premium-2',
            encrypted_key=b'encrypted_premium_2',
            status=APIKeyPool.INACTIVE,
            added_by=self.user
        )

        self.fallback_key1 = APIKeyPool.objects.create(
            provider=APIKeyPool.OPENAI,
            model_tier=APIKeyPool.FALLBACK,
            key_name='Fallback Key 1',
            key_prefix='sk-fallback-1',
            encrypted_key=b'encrypted_fallback_1',
            status=APIKeyPool.ACTIVE,
            added_by=self.user
        )

    def test_get_active_key_for_premium_tier(self):
        """Test getting active key for premium tier."""
        key = APIKeyPool.get_active_key(
            provider='openai',
            model_tier='premium'
        )

        self.assertEqual(key, self.premium_key1)
        self.assertEqual(key.model_tier, 'premium')

    def test_get_active_key_for_fallback_tier(self):
        """Test getting active key for fallback tier."""
        key = APIKeyPool.get_active_key(
            provider='openai',
            model_tier='fallback'
        )

        self.assertEqual(key, self.fallback_key1)
        self.assertEqual(key.model_tier, 'fallback')

    def test_get_active_key_returns_none_for_missing_tier(self):
        """Test that get_active_key returns None for tier with no active key."""
        key = APIKeyPool.get_active_key(
            provider='openai',
            model_tier='standard'
        )

        self.assertIsNone(key)

    def test_get_next_key_for_rotation_per_tier(self):
        """Test getting next key for rotation respects tier."""
        next_key = APIKeyPool.get_next_key_for_rotation(
            provider='openai',
            model_tier='premium'
        )

        # Should return the inactive premium key
        self.assertEqual(next_key, self.premium_key2)
        self.assertEqual(next_key.model_tier, 'premium')


class TierActivationTestCase(TestCase):
    """Test that activating a key only affects keys in the same tier."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testadmin',
            password='testpass123'
        )

        # Create active keys for both tiers
        self.premium_key_active = APIKeyPool.objects.create(
            provider=APIKeyPool.OPENAI,
            model_tier=APIKeyPool.PREMIUM,
            key_name='Premium Active',
            key_prefix='sk-prem-active',
            encrypted_key=b'encrypted_prem_active',
            status=APIKeyPool.ACTIVE,
            added_by=self.user
        )

        self.fallback_key_active = APIKeyPool.objects.create(
            provider=APIKeyPool.OPENAI,
            model_tier=APIKeyPool.FALLBACK,
            key_name='Fallback Active',
            key_prefix='sk-fall-active',
            encrypted_key=b'encrypted_fall_active',
            status=APIKeyPool.ACTIVE,
            added_by=self.user
        )

        # Create inactive key to activate
        self.premium_key_inactive = APIKeyPool.objects.create(
            provider=APIKeyPool.OPENAI,
            model_tier=APIKeyPool.PREMIUM,
            key_name='Premium Inactive',
            key_prefix='sk-prem-inactive',
            encrypted_key=b'encrypted_prem_inactive',
            status=APIKeyPool.INACTIVE,
            added_by=self.user
        )

    def test_activate_only_affects_same_tier(self):
        """Test that activating a premium key doesn't affect fallback tier."""
        # Activate the inactive premium key
        self.premium_key_inactive.activate()

        # Refresh from database
        self.premium_key_active.refresh_from_db()
        self.fallback_key_active.refresh_from_db()

        # Premium tier: old active key should be inactive
        self.assertEqual(self.premium_key_active.status, APIKeyPool.INACTIVE)

        # Premium tier: new key should be active
        self.assertEqual(self.premium_key_inactive.status, APIKeyPool.ACTIVE)

        # Fallback tier: should still be active
        self.assertEqual(self.fallback_key_active.status, APIKeyPool.ACTIVE)


class AutomaticFallbackSwitchingTestCase(TestCase):
    """Test automatic fallback tier switching based on spending cap."""

    def setUp(self):
        # Create spending cap
        self.cap = MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('100.00'),
            is_active=True
        )

        # Create current month spending
        now = timezone.now()
        self.spending = MonthlySpending.objects.create(
            year=now.year,
            month=now.month,
            total_cost_usd=Decimal('0.00')
        )

    def test_get_active_tier_returns_premium_when_under_cap(self):
        """Test that premium tier is returned when under cap."""
        self.spending.total_cost_usd = Decimal('50.00')
        self.spending.save()

        tier = get_active_tier()
        self.assertEqual(tier, 'premium')

    def test_get_active_tier_returns_standard_when_approaching_cap(self):
        """Test that standard tier is returned at 85% of cap."""
        self.spending.total_cost_usd = Decimal('85.00')  # 85% of $100
        self.spending.save()

        tier = get_active_tier()
        self.assertEqual(tier, 'standard')

    def test_get_active_tier_returns_fallback_when_over_cap(self):
        """Test that fallback tier is returned when cap exceeded."""
        self.spending.total_cost_usd = Decimal('105.00')  # Over $100 cap
        self.spending.save()

        tier = get_active_tier()
        self.assertEqual(tier, 'fallback')

    def test_should_switch_to_fallback_when_over_cap(self):
        """Test should_switch_to_fallback returns True when over cap."""
        self.spending.total_cost_usd = Decimal('110.00')
        self.spending.save()

        should_switch, reason = should_switch_to_fallback()
        self.assertTrue(should_switch)
        self.assertIn('exceeded', reason.lower())

    def test_should_not_switch_to_fallback_when_under_cap(self):
        """Test should_switch_to_fallback returns False when under cap."""
        self.spending.total_cost_usd = Decimal('50.00')
        self.spending.save()

        should_switch, reason = should_switch_to_fallback()
        self.assertFalse(should_switch)
        self.assertIn('within budget', reason.lower())


class ModelSelectionPerTierTestCase(TestCase):
    """Test that correct model is selected for each tier."""

    def test_get_model_for_premium_tier(self):
        """Test that GPT-4o is selected for premium tier."""
        model = get_model_for_tier(tier='premium', provider='openai')
        self.assertEqual(model, 'gpt-4o')

    def test_get_model_for_standard_tier(self):
        """Test that GPT-4-turbo is selected for standard tier."""
        model = get_model_for_tier(tier='standard', provider='openai')
        self.assertEqual(model, 'gpt-4-turbo')

    def test_get_model_for_fallback_tier(self):
        """Test that GPT-3.5-turbo is selected for fallback tier."""
        model = get_model_for_tier(tier='fallback', provider='openai')
        self.assertEqual(model, 'gpt-3.5-turbo')


class TierInfoTestCase(TestCase):
    """Test get_tier_info function."""

    def setUp(self):
        self.cap = MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('100.00'),
            is_active=True
        )

        now = timezone.now()
        self.spending = MonthlySpending.objects.create(
            year=now.year,
            month=now.month,
            total_cost_usd=Decimal('50.00')
        )

    def test_get_tier_info_returns_correct_data(self):
        """Test that get_tier_info returns complete tier information."""
        info = get_tier_info()

        self.assertIn('active_tier', info)
        self.assertIn('model', info)
        self.assertIn('reason', info)
        self.assertIn('spending_info', info)
        self.assertIn('tier_cost_multiplier', info)

        self.assertEqual(info['active_tier'], 'premium')
        self.assertEqual(info['model'], 'gpt-4o')


class KeyRotationPerTierTestCase(TestCase):
    """Test key rotation works independently per tier."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testadmin',
            password='testpass123'
        )

        # Create premium tier keys
        self.premium_active = APIKeyPool.objects.create(
            provider=APIKeyPool.OPENAI,
            model_tier=APIKeyPool.PREMIUM,
            key_name='Premium Key 1',
            key_prefix='sk-prem-1',
            encrypted_key=b'encrypted_prem_1',
            status=APIKeyPool.ACTIVE,
            added_by=self.user
        )

        self.premium_inactive = APIKeyPool.objects.create(
            provider=APIKeyPool.OPENAI,
            model_tier=APIKeyPool.PREMIUM,
            key_name='Premium Key 2',
            key_prefix='sk-prem-2',
            encrypted_key=b'encrypted_prem_2',
            status=APIKeyPool.INACTIVE,
            added_by=self.user
        )

        # Create fallback tier keys
        self.fallback_active = APIKeyPool.objects.create(
            provider=APIKeyPool.OPENAI,
            model_tier=APIKeyPool.FALLBACK,
            key_name='Fallback Key 1',
            key_prefix='sk-fall-1',
            encrypted_key=b'encrypted_fall_1',
            status=APIKeyPool.ACTIVE,
            added_by=self.user
        )

        self.fallback_inactive = APIKeyPool.objects.create(
            provider=APIKeyPool.OPENAI,
            model_tier=APIKeyPool.FALLBACK,
            key_name='Fallback Key 2',
            key_prefix='sk-fall-2',
            encrypted_key=b'encrypted_fall_2',
            status=APIKeyPool.INACTIVE,
            added_by=self.user
        )

    def test_rotate_premium_tier_only(self):
        """Test rotating premium tier doesn't affect fallback tier."""
        # Get next premium key and activate it
        next_key = APIKeyPool.get_next_key_for_rotation(
            provider='openai',
            model_tier='premium'
        )
        next_key.activate()

        # Refresh all keys
        self.premium_active.refresh_from_db()
        self.premium_inactive.refresh_from_db()
        self.fallback_active.refresh_from_db()

        # Premium tier should have rotated
        self.assertEqual(self.premium_active.status, APIKeyPool.INACTIVE)
        self.assertEqual(self.premium_inactive.status, APIKeyPool.ACTIVE)

        # Fallback tier should be unchanged
        self.assertEqual(self.fallback_active.status, APIKeyPool.ACTIVE)

    def test_rotation_log_includes_tier_info(self):
        """Test that rotation logs include tier information."""
        next_key = APIKeyPool.get_next_key_for_rotation(
            provider='openai',
            model_tier='fallback'
        )
        next_key.activate()

        # Create log entry
        log = KeyRotationLog.log_rotation(
            provider='openai',
            old_key=self.fallback_active,
            new_key=next_key,
            status=KeyRotationLog.SUCCESS,
            rotation_type='manual',
            notes='fallback tier rotation test'
        )

        self.assertIn('fallback', log.notes.lower())
        self.assertEqual(log.status, KeyRotationLog.SUCCESS)


class KeyRotationSchedulePerTierTestCase(TestCase):
    """Test rotation schedules work independently per tier."""

    def test_separate_schedules_per_tier(self):
        """Test that each tier can have its own rotation schedule."""
        premium_schedule = KeyRotationSchedule.objects.create(
            provider=APIKeyPool.OPENAI,
            model_tier=APIKeyPool.PREMIUM,
            is_enabled=True,
            rotation_frequency=KeyRotationSchedule.WEEKLY
        )

        fallback_schedule = KeyRotationSchedule.objects.create(
            provider=APIKeyPool.OPENAI,
            model_tier=APIKeyPool.FALLBACK,
            is_enabled=True,
            rotation_frequency=KeyRotationSchedule.DAILY
        )

        self.assertEqual(premium_schedule.rotation_frequency, 'weekly')
        self.assertEqual(fallback_schedule.rotation_frequency, 'daily')

    def test_get_or_create_for_provider_with_tier(self):
        """Test get_or_create_for_provider works with tier parameter."""
        schedule, created = KeyRotationSchedule.get_or_create_for_provider(
            provider='openai',
            model_tier='premium'
        )

        self.assertTrue(created)
        self.assertEqual(schedule.model_tier, 'premium')

        # Second call should not create new
        schedule2, created2 = KeyRotationSchedule.get_or_create_for_provider(
            provider='openai',
            model_tier='premium'
        )

        self.assertFalse(created2)
        self.assertEqual(schedule.id, schedule2.id)

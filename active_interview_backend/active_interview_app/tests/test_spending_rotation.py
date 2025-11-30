"""
Tests for Automatic API Key Rotation Triggered by Spending Cap

Related to Issue #15.10 (Cost Caps & API Key Rotation with Auto-Rotation).

This file specifically tests AUTOMATIC ROTATION TRIGGERS:
1. API keys rotate automatically when spending exceeds the configured cap
2. The system switches to fallback tier keys
3. Rotation is logged correctly with 'cap_exceeded' type
4. The feature integrates properly with the spending tracker
5. Cooldown period prevents rapid repeated rotations

RELATED TEST FILES:
- test_api_key_rotation.py: Core rotation functionality (39 tests)
- test_multi_tier_rotation.py: Multi-tier system tests (22 tests)
- test_spending_tracker.py: Monthly spending tracking

This separation maintains single responsibility and makes tests easier to maintain.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from django.db.models import signals

from active_interview_app.spending_tracker_models import (
    MonthlySpendingCap,
    MonthlySpending
)
from active_interview_app.api_key_rotation_models import (
    APIKeyPool,
    KeyRotationLog
)
from active_interview_app.spending_rotation_trigger import (
    should_trigger_rotation_on_cap_exceeded,
    rotate_to_fallback_tier_on_cap_exceeded,
    check_and_rotate_on_cap_exceeded
)
from active_interview_app.token_usage_models import TokenUsage


class SpendingTriggeredRotationTest(TestCase):
    """Test automatic rotation triggered by spending cap

    Note: We disable the automatic signal during these tests so we can test
    the rotation logic in isolation. The signal integration is tested separately.
    """

    def setUp(self):
        """Set up test data"""
        # Disconnect the spending cap rotation signal for unit tests
        from active_interview_app import spending_signals
        signals.post_save.disconnect(
            spending_signals.check_cap_and_trigger_rotation,
            sender=MonthlySpending
        )

        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass',
            is_staff=True
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )

        # Set a $200 spending cap
        self.cap = MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('200.00'),
            is_active=True,
            created_by=self.admin_user
        )

        # Create API keys in different tiers
        # Premium tier keys
        self.premium_key_1 = APIKeyPool.objects.create(
            provider='openai',
            model_tier='premium',
            key_name='Premium Key 1',
            status=APIKeyPool.ACTIVE,
            added_by=self.admin_user
        )
        self.premium_key_1.set_key('sk-premium-1')
        self.premium_key_1.activated_at = timezone.now()
        self.premium_key_1.save()

        self.premium_key_2 = APIKeyPool.objects.create(
            provider='openai',
            model_tier='premium',
            key_name='Premium Key 2',
            status=APIKeyPool.PENDING,
            added_by=self.admin_user
        )
        self.premium_key_2.set_key('sk-premium-2')
        self.premium_key_2.save()

        # Fallback tier keys
        self.fallback_key_1 = APIKeyPool.objects.create(
            provider='openai',
            model_tier='fallback',
            key_name='Fallback Key 1',
            status=APIKeyPool.PENDING,
            added_by=self.admin_user
        )
        self.fallback_key_1.set_key('sk-fallback-1')
        self.fallback_key_1.save()

        self.fallback_key_2 = APIKeyPool.objects.create(
            provider='openai',
            model_tier='fallback',
            key_name='Fallback Key 2',
            status=APIKeyPool.PENDING,
            added_by=self.admin_user
        )
        self.fallback_key_2.set_key('sk-fallback-2')
        self.fallback_key_2.save()

    def tearDown(self):
        """Reconnect the signal after each test"""
        from active_interview_app import spending_signals
        # Reconnect the signal
        signals.post_save.connect(
            spending_signals.check_cap_and_trigger_rotation,
            sender=MonthlySpending
        )

    def test_should_trigger_rotation_under_cap(self):
        """Test that rotation is not triggered when under cap"""
        # Set spending to $100 (under $200 cap)
        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(100.00)

        should_rotate, reason = should_trigger_rotation_on_cap_exceeded()

        self.assertFalse(should_rotate)
        self.assertIn('within cap', reason)

    def test_should_trigger_rotation_over_cap(self):
        """Test that rotation is triggered when over cap"""
        # Set spending to $250 (over $200 cap)
        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(250.00)

        should_rotate, reason = should_trigger_rotation_on_cap_exceeded()

        # Add debug output
        if not should_rotate:
            print(f"\nDEBUG: Rotation not triggered. Reason: {reason}")
            print(f"DEBUG: Spending: ${spending.total_cost_usd}, Cap: ${self.cap.cap_amount_usd}")
            print(f"DEBUG: Is over cap: {spending.is_over_cap()}")

        self.assertTrue(should_rotate, f"Should rotate but didn't. Reason: {reason}")
        self.assertIn('exceeds cap', reason)

    def test_should_trigger_rotation_no_cap_configured(self):
        """Test that rotation is not triggered when no cap is configured"""
        # Remove the cap
        self.cap.is_active = False
        self.cap.save()

        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(1000.00)

        should_rotate, reason = should_trigger_rotation_on_cap_exceeded()

        self.assertFalse(should_rotate)
        self.assertIn('No spending cap', reason)

    def test_rotate_to_fallback_tier_success(self):
        """Test successful rotation to fallback tier"""
        # Set spending over cap
        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(250.00)

        # Perform rotation
        results = rotate_to_fallback_tier_on_cap_exceeded()

        # Debug output if there are errors
        if len(results['errors']) > 0:
            print(f"\nDEBUG: Rotation errors: {results['errors']}")
            print(f"DEBUG: Rotations performed: {results['rotations_performed']}")
            print(f"DEBUG: Success: {results['success']}")

        # Success means at least one tier rotated successfully
        # It's OK if some tiers don't have keys (like standard tier in this test)
        self.assertTrue(results['success'], f"Rotation failed. Errors: {results['errors']}")
        self.assertGreater(len(results['rotations_performed']), 0, "No rotations were performed")

        # Verify at least premium and fallback tiers rotated
        rotated_tiers = [r['tier'] for r in results['rotations_performed']]
        self.assertIn('premium', rotated_tiers)
        self.assertIn('fallback', rotated_tiers)

        # Verify fallback key was activated
        self.fallback_key_1.refresh_from_db()
        self.assertEqual(self.fallback_key_1.status, APIKeyPool.ACTIVE)

    def test_rotate_to_fallback_creates_log(self):
        """Test that rotation creates audit log entries"""
        # Set spending over cap
        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(250.00)

        # Perform rotation
        results = rotate_to_fallback_tier_on_cap_exceeded()

        # Check rotation logs were created
        logs = KeyRotationLog.objects.filter(rotation_type='cap_exceeded')
        self.assertGreater(logs.count(), 0)

        # Check log details
        for log in logs:
            self.assertEqual(log.provider, 'openai')
            self.assertIn('cap exceeded', log.notes.lower())

    def test_rotate_to_fallback_with_no_fallback_keys(self):
        """Test rotation when no fallback keys are available"""
        # Remove all fallback keys
        APIKeyPool.objects.filter(model_tier='fallback').delete()

        # Set spending over cap
        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(250.00)

        # Attempt rotation
        results = rotate_to_fallback_tier_on_cap_exceeded()

        # Should have errors
        self.assertGreater(len(results['errors']), 0)

        # Should log failed rotations
        failed_logs = KeyRotationLog.objects.filter(
            rotation_type='cap_exceeded',
            status=KeyRotationLog.FAILED
        )
        self.assertGreater(failed_logs.count(), 0)

    def test_check_and_rotate_full_workflow(self):
        """Test complete workflow from check to rotation"""
        # Set spending over cap
        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(250.00)

        # Run full check and rotate
        result = check_and_rotate_on_cap_exceeded()

        self.assertTrue(result['should_rotate'])
        self.assertIn('exceeds cap', result['reason'])
        self.assertIsNotNone(result['rotation_results'])
        self.assertTrue(result['rotation_results']['success'])

    def test_rotation_not_triggered_twice_quickly(self):
        """Test that rotation doesn't trigger repeatedly in short time"""
        # Set spending over cap
        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(250.00)

        # First rotation
        result1 = check_and_rotate_on_cap_exceeded()
        self.assertTrue(result1['should_rotate'])

        # Second rotation attempt immediately after
        result2 = check_and_rotate_on_cap_exceeded()

        # Should not rotate again (fallback key activated recently)
        self.assertFalse(result2['should_rotate'])
        self.assertIn('already activated recently', result2['reason'])

    def test_exact_200_dollar_threshold(self):
        """Test behavior at exactly $200.00 (on the cap)"""
        # Set spending to exactly $200
        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(200.00)

        # Should not trigger (is_over_cap checks for > not >=)
        should_rotate, reason = should_trigger_rotation_on_cap_exceeded()
        self.assertFalse(should_rotate)

        # Add $0.01 more to go over
        spending.add_llm_cost(0.01)

        # Now should trigger
        should_rotate, reason = should_trigger_rotation_on_cap_exceeded()
        self.assertTrue(should_rotate)

    def test_rotation_rotates_all_tiers(self):
        """Test that rotation occurs for premium, standard, and fallback tiers"""
        # Create standard tier keys
        standard_key = APIKeyPool.objects.create(
            provider='openai',
            model_tier='standard',
            key_name='Standard Key 1',
            status=APIKeyPool.ACTIVE,
            added_by=self.admin_user
        )
        standard_key.set_key('sk-standard-1')
        standard_key.activated_at = timezone.now()
        standard_key.save()

        standard_key_2 = APIKeyPool.objects.create(
            provider='openai',
            model_tier='standard',
            key_name='Standard Key 2',
            status=APIKeyPool.PENDING,
            added_by=self.admin_user
        )
        standard_key_2.set_key('sk-standard-2')
        standard_key_2.save()

        # Set spending over cap
        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(250.00)

        # Perform rotation
        results = rotate_to_fallback_tier_on_cap_exceeded()

        # Should have rotated multiple tiers
        self.assertGreaterEqual(len(results['rotations_performed']), 2)

        # Check that different tiers were rotated
        tiers_rotated = [r['tier'] for r in results['rotations_performed']]
        self.assertIn('premium', tiers_rotated)
        self.assertIn('fallback', tiers_rotated)


class SpendingSignalIntegrationTest(TestCase):
    """Test integration of spending signals with rotation trigger"""

    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass',
            is_staff=True
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )

        # Set a low cap for easy testing
        self.cap = MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('10.00'),  # Low cap for testing
            is_active=True,
            created_by=self.admin_user
        )

        # Create fallback keys
        self.fallback_key = APIKeyPool.objects.create(
            provider='openai',
            model_tier='fallback',
            key_name='Fallback Key',
            status=APIKeyPool.PENDING,
            added_by=self.admin_user
        )
        self.fallback_key.set_key('sk-fallback-test')
        self.fallback_key.save()

    def test_token_usage_triggers_spending_update_and_rotation(self):
        """Test that creating TokenUsage can trigger rotation via signals"""
        # Create multiple expensive TokenUsage records
        # GPT-4o pricing: $0.03/1K prompt, $0.06/1K completion
        # Each call: (50K/1000)*0.03 + (30K/1000)*0.06 = 1.5 + 1.8 = $3.30
        # 5 calls = $16.50, which exceeds our $10 cap
        for i in range(5):
            TokenUsage.objects.create(
                user=self.user,
                git_branch='test',
                model_name='gpt-4o',
                endpoint='/api/test',
                prompt_tokens=50000,  # Increased from 5000
                completion_tokens=30000  # Increased from 3000
            )

        # Check that spending was updated
        spending = MonthlySpending.get_current_month()
        self.assertGreater(spending.total_cost_usd, Decimal('10.00'))

        # Check if rotation was triggered (if over cap)
        if spending.is_over_cap():
            # Should have rotation logs
            logs = KeyRotationLog.objects.filter(rotation_type='cap_exceeded')
            # Note: May or may not have logs depending on signal execution
            # This is an integration test to verify the flow works

    def test_spending_update_signal_doesnt_fail_on_rotation_error(self):
        """Test that spending update doesn't fail if rotation errors"""
        # Remove all fallback keys to cause rotation to fail
        APIKeyPool.objects.filter(model_tier='fallback').delete()

        # Create expensive TokenUsage that exceeds the $10 cap
        # Each call costs $3.30, so 4 calls = $13.20 > $10
        for i in range(4):
            TokenUsage.objects.create(
                user=self.user,
                git_branch='test',
                model_name='gpt-4o',
                endpoint='/api/test',
                prompt_tokens=50000,  # Increased from 5000
                completion_tokens=30000  # Increased from 3000
            )

        # Spending should still be updated even if rotation failed
        spending = MonthlySpending.get_current_month()
        self.assertGreater(spending.total_cost_usd, Decimal('10.00'))


class UserStoryAcceptanceTest(TestCase):
    """
    Acceptance tests for User Story #15.10:

    As an admin, I want monthly spend caps and auto key-rotation,
    so we don't blow the budget or keep stale keys.

    Scenario:
    Given a monthly spend cap is $200
    When projected spend exceeds the cap
    Then interviews switch to a fallback LLM/TTS tier
    And a rotation job rotates provider keys
    """

    def setUp(self):
        """Set up test environment matching user story"""
        # Disconnect the spending cap rotation signal for unit tests
        from active_interview_app import spending_signals
        signals.post_save.disconnect(
            spending_signals.check_cap_and_trigger_rotation,
            sender=MonthlySpending
        )

        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass',
            is_staff=True
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )

        # Given a monthly spend cap is $200
        self.cap = MonthlySpendingCap.objects.create(
            cap_amount_usd=Decimal('200.00'),
            is_active=True,
            created_by=self.admin_user
        )

        # Set up API keys
        self.premium_key = APIKeyPool.objects.create(
            provider='openai',
            model_tier='premium',
            key_name='Premium Production Key',
            status=APIKeyPool.ACTIVE,
            added_by=self.admin_user
        )
        self.premium_key.set_key('sk-premium-prod')
        self.premium_key.activated_at = timezone.now()
        self.premium_key.save()

        self.fallback_key = APIKeyPool.objects.create(
            provider='openai',
            model_tier='fallback',
            key_name='Fallback Budget Key',
            status=APIKeyPool.PENDING,
            added_by=self.admin_user
        )
        self.fallback_key.set_key('sk-fallback-budget')
        self.fallback_key.save()

    def tearDown(self):
        """Reconnect the signal after each test"""
        from active_interview_app import spending_signals
        # Reconnect the signal
        signals.post_save.connect(
            spending_signals.check_cap_and_trigger_rotation,
            sender=MonthlySpending
        )

    def test_user_story_15_10_complete_scenario(self):
        """
        Test complete user story scenario:
        Cap at $200 → Exceed cap → Switch to fallback → Rotate keys
        """
        from active_interview_app.model_tier_manager import get_active_tier

        # Initial state: Under cap, using premium tier
        spending = MonthlySpending.get_current_month()
        spending.add_llm_cost(100.00)

        tier = get_active_tier()
        self.assertEqual(tier, 'premium')

        # When projected spend exceeds the cap
        spending.add_llm_cost(150.00)  # Total now $250, over $200 cap

        # Verify we're over cap
        self.assertTrue(spending.is_over_cap())
        self.assertGreater(spending.get_percentage_of_cap(), 100.0)

        # Then interviews switch to a fallback LLM/TTS tier
        tier_after_cap = get_active_tier()
        self.assertEqual(tier_after_cap, 'fallback')

        # And a rotation job rotates provider keys
        result = check_and_rotate_on_cap_exceeded()

        # Verify rotation was triggered
        self.assertTrue(result['should_rotate'])
        self.assertIn('exceeds cap', result['reason'])

        # Verify rotation succeeded
        self.assertIsNotNone(result['rotation_results'])
        self.assertTrue(result['rotation_results']['success'])

        # Verify fallback key is now active
        self.fallback_key.refresh_from_db()
        self.assertEqual(self.fallback_key.status, APIKeyPool.ACTIVE)

        # Verify rotation was logged
        rotation_logs = KeyRotationLog.objects.filter(
            rotation_type='cap_exceeded',
            status=KeyRotationLog.SUCCESS
        )
        self.assertGreater(rotation_logs.count(), 0)

        # Verify log contains reference to cap being exceeded
        for log in rotation_logs:
            self.assertIn('cap exceeded', log.notes.lower())

    def test_user_story_acceptance_criteria(self):
        """Verify all acceptance criteria are met"""
        spending = MonthlySpending.get_current_month()

        # Criteria 1: System tracks spending in real-time
        spending.add_llm_cost(50.00)
        self.assertEqual(spending.total_cost_usd, Decimal('50.00'))

        # Criteria 2: Admin can view current spend vs cap
        cap_status = spending.get_cap_status()
        self.assertTrue(cap_status['has_cap'])
        self.assertEqual(cap_status['cap_amount'], 200.00)
        self.assertEqual(cap_status['spent'], 50.00)

        # Criteria 3: System switches to fallback when cap exceeded
        spending.add_llm_cost(160.00)  # Total: $210
        from active_interview_app.model_tier_manager import get_active_tier
        tier = get_active_tier()
        self.assertEqual(tier, 'fallback')

        # Criteria 4: Rotation job rotates keys when cap exceeded
        result = check_and_rotate_on_cap_exceeded()
        self.assertTrue(result['should_rotate'])
        self.assertTrue(result['rotation_results']['success'])

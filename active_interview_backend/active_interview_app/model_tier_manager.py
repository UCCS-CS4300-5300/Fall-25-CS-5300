"""
Model Tier Manager for Cost Control and Fallback Switching

Related to Issue #10 (Cost Caps & API Key Rotation) and Issue #14 (Automatic Fallback).

This module provides functionality for:
- Determining which model tier to use based on spending cap
- Automatic fallback to cheaper models when budget exceeded
- Model selection for each tier
"""

from decimal import Decimal


# Model tier to model name mapping
TIER_TO_MODEL = {
    'premium': {
        'openai': 'gpt-4o',
        'anthropic': 'claude-opus-4-20250514',
    },
    'standard': {
        'openai': 'gpt-4-turbo',
        'anthropic': 'claude-sonnet-4-5-20250929',
    },
    'fallback': {
        'openai': 'gpt-3.5-turbo',
        'anthropic': 'claude-haiku-3-5-20241022',
    }
}

# Cost multipliers (relative to fallback tier)
TIER_COST_MULTIPLIER = {
    'premium': 10.0,      # GPT-4o is ~10x more expensive than GPT-3.5
    'standard': 5.0,       # GPT-4-turbo is ~5x more expensive
    'fallback': 1.0,       # Baseline
}


def get_active_tier(force_tier=None):
    """
    Determine which model tier should be used based on spending cap.

    This function checks:
    1. If a tier is explicitly forced (for admin override)
    2. If monthly spending has exceeded the cap (auto-switch to fallback)
    3. If approaching cap threshold (switch to standard)
    4. Otherwise use premium tier

    Args:
        force_tier (str): Force a specific tier (for testing or admin override)

    Returns:
        str: Active tier ('premium', 'standard', or 'fallback')
    """
    # Allow forced tier for testing or admin override
    if force_tier:
        return force_tier

    try:
        # Import here to avoid circular imports
        from .spending_tracker_models import MonthlySpending
        from django.db import connection

        # Check if database tables exist (important for tests and migrations)
        if not connection.introspection.table_names():
            # Database not ready, default to premium
            return 'premium'

        # Get current month spending
        current_month = MonthlySpending.get_current_month()

        # Check if over cap
        if current_month.is_over_cap():
            return 'fallback'

        # Check if approaching cap (>85% used)
        percentage = current_month.get_percentage_of_cap()
        if percentage and percentage >= 85:
            return 'standard'

        # Default to premium tier
        return 'premium'

    except Exception:
        # If spending tracker is not configured or DB error, default to premium
        # This is normal during tests, migrations, or when feature is not set up
        return 'premium'


def get_model_for_tier(tier='premium', provider='openai'):
    """
    Get the model name for a specific tier and provider.

    Args:
        tier (str): Model tier ('premium', 'standard', 'fallback')
        provider (str): Provider name ('openai', 'anthropic')

    Returns:
        str: Model name (e.g., 'gpt-4o', 'gpt-3.5-turbo')
    """
    return TIER_TO_MODEL.get(tier, {}).get(provider, 'gpt-4o')


def get_tier_info():
    """
    Get information about the current tier and spending status.

    Returns:
        dict: Tier information including:
            - active_tier: Currently active tier
            - model: Model being used
            - reason: Why this tier was selected
            - spending_info: Current spending vs cap
    """
    try:
        from .spending_tracker_models import MonthlySpending

        current_month = MonthlySpending.get_current_month()
        cap_status = current_month.get_cap_status()

        active_tier = get_active_tier()
        model = get_model_for_tier(tier=active_tier)

        # Determine reason for tier selection
        if cap_status['is_over_cap']:
            reason = f"Budget exceeded ({cap_status['percentage']}% of cap used)"
        elif cap_status['percentage'] and cap_status['percentage'] >= 85:
            reason = f"Approaching cap ({cap_status['percentage']}% used)"
        else:
            reason = "Normal operations"

        return {
            'active_tier': active_tier,
            'model': model,
            'reason': reason,
            'spending_info': cap_status,
            'tier_cost_multiplier': TIER_COST_MULTIPLIER.get(active_tier, 1.0)
        }

    except Exception as e:
        return {
            'active_tier': 'premium',
            'model': 'gpt-4o',
            'reason': f'Spending tracker not configured: {e}',
            'spending_info': None,
            'tier_cost_multiplier': 10.0
        }


def should_switch_to_fallback():
    """
    Check if system should switch to fallback tier.

    Returns:
        tuple: (should_switch, reason)
            - should_switch (bool): True if should switch to fallback
            - reason (str): Explanation for the decision
    """
    try:
        from .spending_tracker_models import MonthlySpending

        current_month = MonthlySpending.get_current_month()

        if current_month.is_over_cap():
            percentage = current_month.get_percentage_of_cap()
            return (
                True,
                f"Monthly spending cap exceeded ({percentage:.1f}% of cap used)"
            )

        return (False, "Within budget limits")

    except Exception as e:
        return (False, f"Unable to check spending: {e}")


def estimate_cost_for_tier(tier, token_count):
    """
    Estimate cost for a given tier and token count.

    This is a rough estimate for planning purposes.

    Args:
        tier (str): Model tier
        token_count (int): Estimated token count

    Returns:
        Decimal: Estimated cost in USD
    """
    # Base cost per 1K tokens (GPT-3.5-turbo baseline)
    BASE_COST_PER_1K = Decimal('0.002')

    multiplier = Decimal(str(TIER_COST_MULTIPLIER.get(tier, 1.0)))
    tokens_in_thousands = Decimal(str(token_count)) / Decimal('1000')

    return BASE_COST_PER_1K * multiplier * tokens_in_thousands

"""
Signals for automatic spending tracking and cap-based rotation.

Related to:
- Issue #11 (Track Monthly Spending)
- Issue #15.10 (Automatic API Key Rotation on Cap Exceeded)

This module contains Django signals that automatically:
1. Update monthly spending totals when new TokenUsage records are created
2. Trigger API key rotation when spending exceeds the configured cap
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .token_usage_models import TokenUsage
from .spending_tracker_models import MonthlySpending
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=TokenUsage)
def update_monthly_spending(sender, instance, created, **kwargs):
    """
    Update monthly spending when a new TokenUsage record is created.

    This signal handler is triggered after a TokenUsage record is saved.
    It calculates the cost of the API call and adds it to the current
    month's spending total.

    Args:
        sender: The model class (TokenUsage)
        instance: The actual TokenUsage instance being saved
        created: Boolean indicating if this is a new record
        **kwargs: Additional keyword arguments
    """
    if not created:
        # Only track new records, not updates
        return

    # Get or create the current month's spending record
    spending = MonthlySpending.get_current_month()

    # Add the cost to the monthly total
    cost = instance.estimated_cost
    if cost > 0:
        # Determine tier from model name (Issue #15.10)
        tier = _get_tier_from_model(instance.model_name)
        spending.add_llm_cost(cost, tier=tier)


def _get_tier_from_model(model_name):
    """
    Determine the tier (premium/standard/fallback) from model name.

    Args:
        model_name: Model identifier (e.g., 'gpt-4o', 'gpt-3.5-turbo')

    Returns:
        str: 'premium', 'standard', or 'fallback'
    """
    model_lower = model_name.lower()

    # Premium models
    if 'gpt-4o' in model_lower or 'claude-opus' in model_lower:
        return 'premium'

    # Fallback models
    if 'gpt-3.5' in model_lower or 'haiku' in model_lower:
        return 'fallback'

    # Standard models (default)
    return 'standard'


@receiver(post_save, sender=MonthlySpending)
def check_cap_and_trigger_rotation(sender, instance, created, **kwargs):
    """
    Check if spending cap is exceeded and trigger automatic key rotation.

    This signal handler is triggered after MonthlySpending is updated.
    If spending has exceeded the cap, it triggers automatic rotation to
    fallback tier keys.

    Related to Issue #15.10 (Auto Key Rotation on Cap Exceeded).

    Args:
        sender: The model class (MonthlySpending)
        instance: The actual MonthlySpending instance being saved
        created: Boolean indicating if this is a new record
        **kwargs: Additional keyword arguments
    """
    # Only check if spending was updated (not on initial creation)
    # and we're over the cap
    if not instance.is_over_cap():
        return

    try:
        from .spending_rotation_trigger import check_and_rotate_on_cap_exceeded

        # Check if we should trigger rotation
        result = check_and_rotate_on_cap_exceeded()

        if result['should_rotate']:
            rotation_results = result.get('rotation_results', {})
            if rotation_results.get('success'):
                logger.info(
                    f"Automatic rotation triggered due to cap exceeded. "
                    f"Rotated {len(rotation_results.get('rotations_performed', []))} tier(s)"
                )
            else:
                logger.warning(
                    f"Automatic rotation triggered but failed. "
                    f"Errors: {rotation_results.get('errors', [])}"
                )
        else:
            logger.debug(f"Cap exceeded but rotation not triggered: {result['reason']}")

    except Exception as e:
        # Don't fail the spending update if rotation fails
        logger.error(f"Error checking cap-exceeded rotation: {e}", exc_info=True)

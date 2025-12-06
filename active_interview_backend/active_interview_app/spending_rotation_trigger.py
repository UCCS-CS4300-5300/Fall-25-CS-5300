"""
Automatic API Key Rotation Trigger based on Spending Cap

Related to Issue #15.10 (Cost Caps & API Key Rotation with Auto-Rotation).

This module provides functionality to automatically rotate API keys when monthly
spending exceeds the configured cap. This is a key security measure to:
1. Switch to fallback tier keys when budget is exceeded
2. Rotate keys to prevent overuse of a single key
3. Maintain service availability with cost controls

The rotation is triggered via signals when spending crosses the cap threshold.
"""

from django.utils import timezone
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


def should_trigger_rotation_on_cap_exceeded():
    """
    Check if automatic rotation should be triggered due to cap being exceeded.

    This is called when spending is updated to determine if we've just crossed
    the spending cap threshold and should trigger an automatic key rotation.

    Returns:
        tuple: (should_rotate, reason)
            - should_rotate (bool): True if rotation should be triggered
            - reason (str): Explanation for the decision
    """
    try:
        from .spending_tracker_models import MonthlySpending, MonthlySpendingCap
        from .api_key_rotation_models import APIKeyPool
        from django.db import connection

        # Check if database tables exist (important for tests and migrations)
        table_names = connection.introspection.table_names()
        if not table_names:
            return (False, "Database not ready - no tables")

        # Get current spending
        current_spending = MonthlySpending.get_current_month()
        cap = MonthlySpendingCap.get_active_cap()

        logger.debug(f"Checking rotation trigger: spending=${current_spending.total_cost_usd}, cap=${cap.cap_amount_usd if cap else 'None'}")

        if not cap:
            return (False, "No spending cap configured")

        # Check if we're over the cap
        is_over = current_spending.is_over_cap()
        logger.debug(f"Is over cap: {is_over} (${current_spending.total_cost_usd} > ${cap.cap_amount_usd})")

        if not is_over:
            return (False, f"Spending ${current_spending.total_cost_usd} is within cap ${cap.cap_amount_usd}")

        # We're over cap - check if we have fallback keys available
        fallback_key = APIKeyPool.get_active_key(provider='openai', model_tier='fallback')
        logger.debug(f"Active fallback key: {fallback_key.key_name if fallback_key else 'None'}")

        # If already using fallback tier, check if recently activated
        if fallback_key and fallback_key.activated_at:
            seconds_since_activation = (timezone.now() - fallback_key.activated_at).total_seconds()
            logger.debug(f"Fallback key activated {seconds_since_activation:.0f} seconds ago")
            if seconds_since_activation < 3600:
                return (False, f"Fallback key already activated recently ({seconds_since_activation:.0f}s ago)")

        # Check if we have available fallback keys to rotate to
        available_fallback_keys = APIKeyPool.objects.filter(
            provider='openai',
            model_tier='fallback',
            status__in=[APIKeyPool.INACTIVE, APIKeyPool.PENDING]
        ).count()

        logger.debug(f"Available fallback keys for rotation: {available_fallback_keys}")

        if available_fallback_keys == 0 and not fallback_key:
            return (False, "No fallback keys available for rotation")

        # All conditions met - trigger rotation
        reason = f"Spending ${current_spending.total_cost_usd} exceeds cap ${cap.cap_amount_usd} ({current_spending.get_percentage_of_cap():.1f}%)"
        logger.info(f"Rotation trigger condition met: {reason}")
        return (True, reason)

    except Exception as e:
        # Log error with full traceback for debugging
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Error checking rotation trigger: {e}\n{error_detail}")
        return (False, f"Error checking rotation: {str(e)}")


def rotate_to_fallback_tier_on_cap_exceeded():
    """
    Automatically rotate to fallback tier keys when spending cap is exceeded.

    This function is called when spending crosses the cap threshold.
    It will:
    1. Rotate all tiers to fallback tier keys if available
    2. Log the rotation with reason "cap_exceeded"
    3. Ensure the system switches to cost-effective keys

    Returns:
        dict: Rotation results
            - success (bool): Whether rotation succeeded
            - rotations_performed (list): List of tier rotations performed
            - errors (list): Any errors encountered
    """
    from .api_key_rotation_models import APIKeyPool, KeyRotationLog

    results = {
        'success': False,
        'rotations_performed': [],
        'errors': []
    }

    try:
        # For each tier, try to rotate to a fallback key
        tiers_to_rotate = ['premium', 'standard', 'fallback']

        with transaction.atomic():
            for tier in tiers_to_rotate:
                try:
                    # Get current active key for this tier
                    current_key = APIKeyPool.get_active_key(provider='openai', model_tier=tier)

                    # Get next available key for this tier
                    next_key = APIKeyPool.get_next_key_for_rotation(provider='openai', model_tier=tier)

                    if not next_key:
                        # No keys available for this tier
                        results['errors'].append(f"No keys available for {tier} tier rotation")

                        # Log the failed rotation
                        KeyRotationLog.log_rotation(
                            provider='openai',
                            old_key=current_key,
                            new_key=None,
                            status=KeyRotationLog.FAILED,
                            rotation_type='cap_exceeded',
                            error_message=f'No keys available for {tier} tier',
                            notes='Automatic rotation triggered by spending cap exceeded'
                        )
                        continue

                    # Perform the rotation
                    next_key.activate()

                    # Log successful rotation
                    log_entry = KeyRotationLog.log_rotation(
                        provider='openai',
                        old_key=current_key,
                        new_key=next_key,
                        status=KeyRotationLog.SUCCESS,
                        rotation_type='cap_exceeded',
                        notes=f'Automatic rotation to {tier} tier triggered by spending cap exceeded'
                    )

                    results['rotations_performed'].append({
                        'tier': tier,
                        'old_key': current_key.key_name if current_key else None,
                        'new_key': next_key.key_name,
                        'log_id': log_entry.id
                    })

                    logger.info(
                        f"Auto-rotated {tier} tier: "
                        f"{current_key.key_name if current_key else 'None'} -> {next_key.key_name}"
                    )

                except Exception as e:
                    error_msg = f"Error rotating {tier} tier: {e}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg, exc_info=True)

        # Mark success if at least one rotation was performed
        results['success'] = len(results['rotations_performed']) > 0

        if results['success']:
            logger.info(
                f"Cap-exceeded rotation completed. "
                f"Rotated {len(results['rotations_performed'])} tier(s)"
            )
        else:
            logger.warning(
                f"Cap-exceeded rotation triggered but no keys were rotated. "
                f"Errors: {results['errors']}"
            )

        return results

    except Exception as e:
        error_msg = f"Critical error during cap-exceeded rotation: {e}"
        results['errors'].append(error_msg)
        logger.error(error_msg, exc_info=True)
        return results


def check_and_rotate_on_cap_exceeded():
    """
    Check if rotation should be triggered and perform it if needed.

    This is the main entry point called by signals or scheduled tasks.

    Returns:
        dict: Results of the check and rotation
            - should_rotate (bool): Whether rotation was needed
            - reason (str): Reason for decision
            - rotation_results (dict): Results if rotation was performed
    """
    should_rotate, reason = should_trigger_rotation_on_cap_exceeded()

    result = {
        'should_rotate': should_rotate,
        'reason': reason,
        'rotation_results': None
    }

    if should_rotate:
        logger.info(f"Triggering automatic rotation: {reason}")
        rotation_results = rotate_to_fallback_tier_on_cap_exceeded()
        result['rotation_results'] = rotation_results
    else:
        logger.debug(f"Rotation not triggered: {reason}")

    return result

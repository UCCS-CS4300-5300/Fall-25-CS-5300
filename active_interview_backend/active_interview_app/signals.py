"""
Django Signals for Active Interview App

This module contains general application signals.
For spending-related signals, see spending_signals.py (Issue #11, #15.10).
For audit logging signals, see admin action logging below (Issues #66, #67, #68).
"""

from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed


@receiver(post_migrate)
def ensure_average_role_group(sender, **kwargs):
    """Ensure the average_role group exists after migrations."""
    Group.objects.get_or_create(name='average_role')


# Audit Logging Signals (Issues #66, #67, #68)

# Map Django admin action flags to our audit action types
ADMIN_ACTION_MAP = {
    ADDITION: 'ADMIN_CREATE',
    CHANGE: 'ADMIN_UPDATE',
    DELETION: 'ADMIN_DELETE',
}


@receiver(post_save, sender=LogEntry)
def log_admin_action(sender, instance, created, **kwargs):
    """
    Mirror Django admin actions to our immutable audit log.

    Captures all admin CRUD operations with full context including:
    - User who performed the action
    - Object type and ID
    - Action type (create/update/delete)
    - Change details from Django's change message

    Related to Issues #66, #67, #68 (Audit Logging).
    """
    # Only log new LogEntry records (not updates)
    if not created:
        return

    # Import here to avoid circular imports
    from .audit_utils import create_audit_log

    # Map Django action flag to our action type
    action_type = ADMIN_ACTION_MAP.get(instance.action_flag)
    if not action_type:
        # Unknown action type, skip
        return

    # Build human-readable description
    resource_name = instance.object_repr or 'Unknown'
    model_name = instance.content_type.model if instance.content_type else 'Unknown'

    if instance.action_flag == ADDITION:
        description = f"Admin {instance.user.username} created {model_name}: {resource_name}"
    elif instance.action_flag == CHANGE:
        description = f"Admin {instance.user.username} updated {model_name}: {resource_name}"
    elif instance.action_flag == DELETION:
        description = f"Admin {instance.user.username} deleted {model_name}: {resource_name}"
    else:
        description = f"Admin {instance.user.username} performed action on {model_name}: {resource_name}"

    # Create audit log entry
    create_audit_log(
        user=instance.user,
        action_type=action_type,
        resource_type=model_name,
        resource_id=instance.object_id,
        description=description,
        extra_data={
            'change_message': instance.get_change_message(),
            'content_type': model_name,
            'action_flag': instance.action_flag
        }
    )


# Authentication Event Logging (Issues #66, #67, #68)

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Log successful user login events.

    Captures:
    - User who logged in
    - IP address
    - User agent
    - Timestamp (automatic via model)

    Related to Issues #66, #67, #68 (Audit Logging).
    """
    from .audit_utils import create_audit_log

    create_audit_log(
        user=user,
        action_type='LOGIN',
        description=f"User {user.username} logged in successfully"
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """
    Log user logout events.

    Note: user may be None if session expired

    Related to Issues #66, #67, #68 (Audit Logging).
    """
    from .audit_utils import create_audit_log

    if user:
        create_audit_log(
            user=user,
            action_type='LOGOUT',
            description=f"User {user.username} logged out"
        )


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """
    Log failed login attempts.

    Captures:
    - Username/email attempted (not password)
    - IP address
    - User agent

    This helps detect brute-force attacks and unauthorized access attempts.

    Related to Issues #66, #67, #68 (Audit Logging).
    """
    from .audit_utils import create_audit_log

    # Get username from credentials (don't log password)
    username = credentials.get('username', 'unknown')

    create_audit_log(
        user=None,  # No user for failed login
        action_type='LOGIN_FAILED',
        description=f"Failed login attempt for username: {username}",
        extra_data={
            'attempted_username': username
        }
    )

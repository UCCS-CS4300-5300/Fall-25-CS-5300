"""
Audit Logging Utilities

Centralized functions for creating audit log entries with error handling.
Ensures audit logging failures don't break user actions.

Related to Issues #66, #67, #68 (Audit Logging).
"""

import logging
from .models import AuditLog
from .middleware import get_current_ip, get_user_agent

logger = logging.getLogger(__name__)


def create_audit_log(
    user,
    action_type,
    resource_type=None,
    resource_id=None,
    description="",
    extra_data=None
):
    """
    Create an audit log entry with full request context.

    Args:
        user: User instance or None (for anonymous actions)
        action_type: One of AuditLog.ACTION_TYPES (e.g., 'LOGIN', 'LOGOUT')
        resource_type: Type of resource affected (e.g., "User", "Chat", "Resume")
        resource_id: ID of the affected resource
        description: Human-readable description of the action
        extra_data: Dict of additional action-specific metadata

    Returns:
        AuditLog instance if successful, None if failed

    Example:
        create_audit_log(
            user=request.user,
            action_type='LOGIN',
            description=f"User {request.user.username} logged in successfully"
        )
    """
    try:
        # Get request context from thread-local storage
        ip_address = get_current_ip()
        user_agent = get_user_agent()

        # Truncate user agent to fit field limit
        if user_agent and len(user_agent) > 256:
            user_agent = user_agent[:255]

        # Create the audit log entry
        log_entry = AuditLog.objects.create(
            user=user,
            action_type=action_type,
            resource_type=resource_type or '',
            resource_id=str(resource_id) if resource_id else '',
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data=extra_data or {}
        )

        return log_entry

    except Exception as e:
        # Log the error but don't break the user's action
        # Audit logging failures should never impact user experience
        logger.error(
            f"Failed to create audit log entry: {e}",
            exc_info=True,
            extra={
                'user_id': user.id if user else None,
                'action_type': action_type,
                'resource_type': resource_type,
                'resource_id': resource_id
            }
        )
        return None

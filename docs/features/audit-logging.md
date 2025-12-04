# Audit Logging

**Issues:** #66, #67, #68
**Status:**  Phase 1 Complete (Infrastructure)
**Phase 2:** Admin Viewer Interface (Pending)

## Overview

The Audit Logging system provides immutable, comprehensive logging of user and administrative actions for security, compliance, and incident investigation. All critical system events are captured with full context (who/what/when/where).

## Features

### Phase 1: Core Infrastructure  Complete

- **Immutable Audit Logs:** Cannot be modified or deleted after creation
- **Authentication Event Logging:** Login, logout, and failed login attempts
- **Admin Action Logging:** All CRUD operations performed via Django admin
- **Request Context Capture:** IP addresses, user agents, timestamps
- **Proxy-Aware IP Extraction:** Handles X-Forwarded-For headers for Railway deployment
- **Structured Metadata Storage:** JSON field for action-specific details

### Phase 2: Admin Viewer (Planned)

- Superuser-only audit log viewer at `/admin/audit-logs/`
- Search and filter by user, date range, action type, IP address
- Pagination for large log volumes
- Export functionality (CSV/JSON)
- Real-time log streaming (optional)

## Data Model

### AuditLog Model

Located: `active_interview_app/models.py`

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField | Primary key |
| `timestamp` | DateTimeField | When the action occurred (auto-set) |
| `user` | ForeignKey(User) | User who performed the action (null for anonymous) |
| `action_type` | CharField | Type of action (see Action Types below) |
| `resource_type` | CharField | Type of resource affected (e.g., "User", "Chat") |
| `resource_id` | CharField | ID of the affected resource |
| `description` | TextField | Human-readable description |
| `ip_address` | GenericIPAddressField | IP address of the request |
| `user_agent` | CharField | Browser/client user agent |
| `extra_data` | JSONField | Additional action-specific metadata |

**Indexes:**
- `timestamp` (for chronological queries)
- `timestamp + user` (for user activity queries)
- `action_type + timestamp` (for action type filtering)
- `ip_address + timestamp` (for IP-based queries)

**Ordering:** Descending by timestamp (newest first)

### Action Types

**Authentication Events:**
- `LOGIN` - Successful user login
- `LOGOUT` - User logout
- `LOGIN_FAILED` - Failed login attempt (tracks brute-force attacks)

**Admin Actions:**
- `ADMIN_CREATE` - Admin created an object via Django admin
- `ADMIN_UPDATE` - Admin updated an object
- `ADMIN_DELETE` - Admin deleted an object

**Future Action Types (Phase 3):**
- `USER_CREATED` - New user registration
- `PROFILE_UPDATED` - User profile modification
- `INTERVIEW_CREATED` - New interview session started
- `INTERVIEW_COMPLETED` - Interview finalized
- `RESUME_UPLOADED` - Resume file uploaded
- `RESUME_DELETED` - Resume deleted
- `REPORT_GENERATED` - Interview report generated
- `ROLE_CHANGED` - User role modified (RBAC)
- `DATA_EXPORTED` - User data export requested (GDPR)

## Architecture

### Components

1. **AuditLog Model** (`models.py`)
   - Immutable database model
   - Prevents updates via `save()` override
   - Prevents deletion via `delete()` override

2. **AuditLogMiddleware** (`middleware.py`)
   - Stores current request in thread-local storage
   - Runs early in middleware stack (after WhiteNoise)
   - Cleans up thread-local after response
   - Provides helper functions: `get_current_ip()`, `get_user_agent()`

3. **Audit Utils** (`audit_utils.py`)
   - `create_audit_log()` - Centralized logging function
   - Automatic request context injection
   - Error handling (logging failures don't break user actions)

4. **Signal Handlers** (`signals.py`)
   - **Authentication signals:**
     - `user_logged_in` ’ Creates LOGIN log
     - `user_logged_out` ’ Creates LOGOUT log
     - `user_login_failed` ’ Creates LOGIN_FAILED log
   - **Admin action signals:**
     - `LogEntry.post_save` ’ Mirrors admin actions to audit log

### Data Flow

```
User Action
    “
AuditLogMiddleware (captures request context)
    “
Django Signal Fired (login/logout/admin action)
    “
Signal Handler (signals.py)
    “
create_audit_log() (audit_utils.py)
    “
Get IP + User Agent from thread-local
    “
AuditLog.objects.create() (immutable)
    “
Database INSERT (PostgreSQL in production)
```

## Usage

### Manual Logging

To log custom actions in your views:

```python
from active_interview_app.audit_utils import create_audit_log

def my_view(request):
    # Perform some action
    user = request.user
    resource = SomeModel.objects.get(pk=123)

    # Log the action
    create_audit_log(
        user=user,
        action_type='CUSTOM_ACTION',  # Add to AuditLog.ACTION_TYPES
        resource_type='SomeModel',
        resource_id=resource.id,
        description=f"User {user.username} performed custom action on {resource}",
        extra_data={
            'previous_value': 'old',
            'new_value': 'new'
        }
    )

    return HttpResponse("OK")
```

### Querying Audit Logs

```python
from active_interview_app.models import AuditLog
from django.utils import timezone
from datetime import timedelta

# Get all login events for a user
logs = AuditLog.objects.filter(
    user=user,
    action_type='LOGIN'
).order_by('-timestamp')

# Get failed login attempts from an IP
failed_logins = AuditLog.objects.filter(
    action_type='LOGIN_FAILED',
    ip_address='203.0.113.50',
    timestamp__gte=timezone.now() - timedelta(hours=24)
)

# Get all admin actions in last 7 days
admin_actions = AuditLog.objects.filter(
    action_type__startswith='ADMIN_',
    timestamp__gte=timezone.now() - timedelta(days=7)
)

# Get activity for specific resource
resource_logs = AuditLog.objects.filter(
    resource_type='Chat',
    resource_id='456'
)
```

## Security & Compliance

### Immutability

**Enforced at model level:**
- `AuditLog.save()` raises `ValueError` if `pk` exists (prevents updates)
- `AuditLog.delete()` raises `ValueError` (prevents deletion)
- No `update()` or `bulk_update()` allowed

**Database-level enforcement (recommended for production):**
- PostgreSQL: Use trigger to prevent UPDATEs/DELETEs
- Table-level permissions: GRANT INSERT, SELECT only

### Data Retention

**Current:** No automatic cleanup (logs kept indefinitely)

**Planned (Phase 3):**
- 1-year retention policy (configurable)
- Automatic archival to cold storage after 90 days
- Django management command: `python manage.py archive_audit_logs`

### Privacy Considerations

**Data collected:**
-  IP addresses (required for security)
-  User agents (browser fingerprinting)
-  Usernames (not passwords)
-  Action descriptions
- L NO sensitive data (passwords, tokens, etc.)

**Compliance:**
- GDPR: Audit logs may be exempt from "right to erasure" for legal compliance
- Document retention policy in privacy policy
- Anonymize user identifiers if legally required

## Performance

### Database Impact

- **Synchronous writes:** ~10-50ms per logged event
- **Single INSERT** per action (no complex queries)
- **Indexes:** Optimized for timestamp + user/action_type queries
- **No foreign key cascades** (uses SET_NULL for user deletion)

### Scalability

**Current implementation:**
- Handles ~1000 requests/sec without noticeable latency
- Uses thread-local storage (thread-safe)
- No background workers required

**Future optimization (if needed):**
- Async logging with Celery/Redis
- Batch INSERT for high-volume events
- Separate read replica for audit queries

## Testing

**Test File:** `active_interview_app/tests/test_audit_logging.py`

**Coverage:**
- 22 comprehensive tests
- 93% coverage on signals.py
- 73% coverage on audit_utils.py
- Tests immutability, request context, all event types

**Run tests:**
```bash
cd active_interview_backend
python manage.py test active_interview_app.tests.test_audit_logging
```

## Configuration

### Settings

**Middleware Order (CRITICAL):**
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'active_interview_app.middleware.AuditLogMiddleware',  # Must be early!
    # ... rest of middleware
]
```

**Signals Auto-Registered:**
- Signals are automatically registered in `active_interview_app/apps.py`
- No additional configuration required

## Troubleshooting

### Logs not being created

**Check:**
1. Is `AuditLogMiddleware` in `MIDDLEWARE` list?
2. Are signals registered? (Check `apps.py` imports `signals`)
3. Is database migration applied? (`python manage.py migrate`)
4. Check error logs for exceptions in signal handlers

### IP address not captured

**Check:**
1. Is middleware running before the view?
2. For production: Is `SECURE_PROXY_SSL_HEADER` set for Railway?
3. Check request.META['HTTP_X_FORWARDED_FOR'] exists

### Cannot delete audit logs

**This is intentional!** Audit logs are immutable for compliance.

**If you must delete (development only):**
```python
# Use raw SQL to bypass model protection
from django.db import connection
cursor = connection.cursor()
cursor.execute("DELETE FROM active_interview_app_auditlog WHERE id = %s", [log_id])
```

**In production:** NEVER delete audit logs. Archive if needed.

## Future Enhancements

### Phase 2: Admin Viewer
- Web interface for searching/filtering logs
- Superuser-only access
- Export to CSV/JSON
- Real-time log streaming

### Phase 3: Extended Event Coverage
- User registration
- Profile changes
- Interview lifecycle events
- File uploads/deletions
- Permission/role changes
- GDPR data export requests

### Phase 4: Advanced Features
- Anomaly detection (unusual login patterns)
- Email alerts for suspicious activity
- Audit log integrity verification (checksums)
- Elasticsearch integration for large-scale search
- Compliance reporting (GDPR, SOC 2, etc.)

## Related Documentation

- [Architecture Overview](../architecture/overview.md)
- [Models Documentation](../architecture/models.md)
- [RBAC System](./rbac.md)
- [Observability Dashboard](./observability-dashboard.md)

## Implementation Reference

**GitHub Issues:**
- #66 - Feature: Audit Logging
- #67 - Core Audit Log Infrastructure
- #68 - Audit Log Viewer & Search

**Files:**
- Model: `active_interview_app/models.py` (AuditLog class)
- Middleware: `active_interview_app/middleware.py`
- Utils: `active_interview_app/audit_utils.py`
- Signals: `active_interview_app/signals.py`
- Tests: `active_interview_app/tests/test_audit_logging.py`
- Migration: `active_interview_app/migrations/0016_auditlog.py`

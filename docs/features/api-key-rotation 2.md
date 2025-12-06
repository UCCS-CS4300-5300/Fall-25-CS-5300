# Automatic API Key Rotation

**Related Issues:** #10 (Cost Caps & API Key Rotation), #13 (Automatic API Key Rotation)

## Overview

The Automatic API Key Rotation feature allows administrators to maintain security by regularly rotating API keys on a configurable schedule without manual intervention. Since most API providers (including OpenAI) don't support programmatic key creation, this system uses a **Key Pool Rotation** approach where administrators pre-load multiple keys and the system automatically rotates between them.

## Features

### 1. Encrypted Key Storage

All API keys are stored securely in the database:

- **Fernet Encryption**: Industry-standard symmetric encryption at rest
- **Masked Display**: Keys displayed in masked format (e.g., "sk-proj-abc...xyz")
- **Audit Trail**: Tracks who added keys and when
- **Usage Tracking**: Monitors usage count and last used timestamp per key

### 2. Configurable Rotation Schedule

Administrators can configure rotation frequency per provider:

- **Rotation Frequencies**: Daily, Weekly, Monthly, or Quarterly
- **Enable/Disable**: Turn automatic rotation on or off
- **Manual Override**: Force rotation at any time regardless of schedule
- **Provider-Specific**: Different schedules for OpenAI, Anthropic, etc.

### 3. Round-Robin Rotation

Keys rotate in a round-robin pattern:

- **Automatic Selection**: System selects oldest pending key for activation
- **Deactivation**: Old keys automatically deactivated on rotation
- **Status Tracking**: Keys can be Active, Inactive, Pending, or Revoked
- **Multi-Provider**: Each provider has independent key pool

### 4. Comprehensive Audit Logs

All rotation events are logged immutably:

- **Rotation History**: Complete audit trail of all rotations
- **Status Tracking**: Success, Failed, or Skipped status
- **Error Details**: Failed rotations include error messages
- **Immutable**: Logs cannot be deleted (compliance requirement)

### 5. Graceful Fallback

System gracefully falls back to environment variable if pool not configured:

- **Backward Compatible**: Existing deployments continue working
- **Dual Support**: Supports both key pool and environment variable
- **Automatic Detection**: Uses pool if available, otherwise falls back
- **Migration Path**: Easy migration from environment variable to pool

## Database Schema

### APIKeyPool

Stores encrypted API keys with metadata.

```python
class APIKeyPool(models.Model):
    provider = CharField()              # openai, anthropic, etc.
    key_name = CharField()              # Friendly name (e.g., "Production Key 1")
    encrypted_key = BinaryField()       # Fernet-encrypted API key
    key_prefix = CharField()            # First few chars for identification

    # Status Management
    status = CharField()                # active, inactive, pending, revoked
    activated_at = DateTimeField()
    deactivated_at = DateTimeField()

    # Usage Tracking
    usage_count = IntegerField()
    last_used_at = DateTimeField()

    # Audit Fields
    added_at = DateTimeField()
    updated_at = DateTimeField()
    added_by = ForeignKey(User)
    notes = TextField()
```

### KeyRotationSchedule

Configures rotation schedule per provider.

```python
class KeyRotationSchedule(models.Model):
    provider = CharField(unique=True)   # One schedule per provider

    # Rotation Settings
    is_enabled = BooleanField()
    rotation_frequency = CharField()    # daily, weekly, monthly, quarterly

    # Schedule Tracking
    last_rotation_at = DateTimeField()
    next_rotation_at = DateTimeField()

    # Notifications
    notify_on_rotation = BooleanField()
    notification_email = EmailField()

    # Audit Fields
    created_at = DateTimeField()
    updated_at = DateTimeField()
    created_by = ForeignKey(User)
```

### KeyRotationLog

Immutable audit trail of rotation events.

```python
class KeyRotationLog(models.Model):
    provider = CharField()

    # Key References
    old_key = ForeignKey(APIKeyPool)
    new_key = ForeignKey(APIKeyPool)
    old_key_masked = CharField()        # Persisted even if key deleted
    new_key_masked = CharField()

    # Status
    status = CharField()                # success, failed, skipped
    rotation_type = CharField()         # scheduled, manual, forced

    # Audit Information
    rotated_at = DateTimeField()
    rotated_by = ForeignKey(User)       # null for automatic rotations
    error_message = TextField()
    notes = TextField()
```

## Setup

### Prerequisites

1. **Install Dependencies**

   The `cryptography` package is required for key encryption:

   ```bash
   pip install cryptography
   ```

   (Already included in `requirements.txt`)

2. **Generate Encryption Key**

   Generate a Fernet encryption key for securing API keys:

   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

   Add to your `.env` file:

   ```bash
   API_KEY_ENCRYPTION_KEY=your-generated-key-here
   ```

   **IMPORTANT**: Store this key securely. If lost, encrypted keys cannot be recovered.

3. **Run Database Migration**

   ```bash
   python manage.py migrate
   ```

   This creates three new tables:
   - `active_interview_app_apikeypool`
   - `active_interview_app_keyrotationschedule`
   - `active_interview_app_keyrotationlog`

### Adding Keys to Pool

**Via Django Admin (Recommended):**

1. Navigate to Django Admin → **Active Interview App** → **API Key Pool**
2. Click **"Add API Key"**
3. Fill in the form:
   - **Provider**: Select provider (OpenAI, Anthropic)
   - **Key Name**: Friendly name (e.g., "Production Key 1")
   - **API Key Input**: Paste your actual API key
   - **Status**: Select "Pending" (will be activated during first rotation)
   - **Notes**: Optional notes about this key
4. Click **"Save"**

**Important**: Add at least 2 keys per provider for rotation to work.

### Configuring Rotation Schedule

**Via Django Admin:**

1. Navigate to Django Admin → **Active Interview App** → **Key Rotation Schedules**
2. Click **"Add Key Rotation Schedule"** or edit existing one
3. Configure:
   - **Provider**: Select provider (openai, anthropic)
   - **Is Enabled**: Check to enable automatic rotation
   - **Rotation Frequency**: Select frequency (Daily/Weekly/Monthly/Quarterly)
   - **Notify on Rotation**: Check to enable email notifications
   - **Notification Email**: Enter email for rotation alerts
4. Click **"Save"**

### Initial Rotation

Activate your first key manually:

```bash
python manage.py rotate_api_keys --force
```

Or via Django Admin:
1. Go to API Key Pool
2. Select a key
3. Change status to "Active"
4. Save

## Usage

### Manual Rotation

Rotate keys immediately regardless of schedule:

```bash
# Force rotation for default provider (openai)
python manage.py rotate_api_keys --force

# Force rotation for specific provider
python manage.py rotate_api_keys --provider anthropic --force

# Dry run (preview without actually rotating)
python manage.py rotate_api_keys --force --dry-run
```

### Scheduled Rotation

Set up automatic rotation using cron:

**Option 1: System Cron Job**

```cron
# Run every day at 2 AM (checks if rotation is due)
0 2 * * * cd /path/to/project && python manage.py rotate_api_keys
```

**Option 2: Django-Crontab**

Add to `settings.py`:

```python
CRONJOBS = [
    ('0 2 * * *', 'django.core.management.call_command', ['rotate_api_keys']),
]
```

Then:

```bash
python manage.py crontab add
```

### Monitoring

**View Current Key Information:**

```python
from active_interview_app.openai_utils import get_current_api_key_info

info = get_current_api_key_info()
print(f"Using: {info['key_name']}")
print(f"Masked: {info['masked_key']}")
print(f"Usage: {info['usage_count']} times")
print(f"Source: {info['source']}")  # 'key_pool' or 'environment'
```

**View Rotation Logs:**

Navigate to Django Admin → **Active Interview App** → **Key Rotation Logs**

**View Key Pool Status:**

Navigate to Django Admin → **Active Interview App** → **API Key Pool**

Or use the management command:

```bash
python manage.py rotate_api_keys --force
```

Output shows:
```
Key Pool Status:
------------------------------------------------------------
  ACTIVE      Production Key 2          sk-proj-def...uvw    Used: 157 times
  INACTIVE    Production Key 1          sk-proj-abc...xyz    Used: 305 times
  PENDING     Production Key 3          sk-proj-ghi...rst    Used: 0 times
```

## Command Reference

### rotate_api_keys

Rotate API keys based on schedule or force rotation.

**Syntax:**
```bash
python manage.py rotate_api_keys [options]
```

**Options:**
- `--provider PROVIDER`: Provider to rotate keys for (default: openai)
- `--force`: Force rotation even if not due
- `--dry-run`: Show what would be rotated without actually rotating

**Examples:**

```bash
# Check if rotation is due and rotate if needed
python manage.py rotate_api_keys

# Force immediate rotation
python manage.py rotate_api_keys --force

# Rotate specific provider
python manage.py rotate_api_keys --provider anthropic --force

# Preview rotation without executing
python manage.py rotate_api_keys --dry-run

# Force rotation for OpenAI
python manage.py rotate_api_keys --provider openai --force
```

**Output:**

```
API Key Rotation for openai
============================================================
Current active key: Production Key 1 (sk-proj-abc...xyz)
Next key to activate: Production Key 2 (sk-proj-def...uvw)

Performing rotation...

✓ Successfully rotated to Production Key 2
Old key deactivated: Production Key 1
New key activated: Production Key 2
Next rotation scheduled for: 2025-11-29 10:00:00

Key Pool Status:
------------------------------------------------------------
  ACTIVE      Production Key 2          sk-proj-def...uvw    Used: 0 times
  INACTIVE    Production Key 1          sk-proj-abc...xyz    Used: 157 times
  PENDING     Production Key 3          sk-proj-ghi...rst    Used: 0 times
```

## How It Works

### Rotation Process

1. **Check Schedule**: System checks if rotation is due based on configured frequency
2. **Get Next Key**: Selects oldest pending key from pool (round-robin)
3. **Activate New Key**: New key status changes to "active", timestamp set
4. **Deactivate Old Key**: Old key status changes to "inactive", timestamp set
5. **Update Schedule**: Last rotation and next rotation timestamps updated
6. **Log Event**: Immutable log entry created with all details
7. **Notify**: Email sent if notifications enabled

### OpenAI Client Integration

The OpenAI client automatically detects and uses rotated keys:

```python
def get_openai_client(force_refresh=False):
    """Get OpenAI client, refreshing if active key has changed."""
    global _openai_client, _current_api_key

    current_key = get_api_key_from_pool()

    # Refresh client if key has changed
    if _openai_client is None or _current_api_key != current_key:
        _openai_client = OpenAI(api_key=current_key)
        _current_api_key = current_key

    return _openai_client
```

**Benefits:**
- Seamless rotation without service interruption
- Automatic client refresh on key change
- Usage tracking for each key
- Graceful fallback to environment variable

### Encryption

Keys are encrypted using Fernet symmetric encryption:

```python
from cryptography.fernet import Fernet

# Encryption (when storing)
f = Fernet(encryption_key)
encrypted = f.encrypt(api_key.encode())

# Decryption (when using)
decrypted = f.decrypt(encrypted).decode()
```

**Security Features:**
- Keys encrypted at rest in database
- Encryption key stored in environment variable
- Keys decrypted only when needed for API calls
- Masked display in all UI and logs

## API Integration

The key rotation system integrates seamlessly with existing code:

**Resume Parser** (`resume_parser.py`):
```python
from active_interview_app.openai_utils import get_openai_client

client = get_openai_client()  # Automatically uses active key from pool
response = client.chat.completions.create(...)
```

**Interview Generation** (`views.py`):
```python
from active_interview_app.openai_utils import get_openai_client

client = get_openai_client()  # Automatically uses active key from pool
response = client.chat.completions.create(...)
```

No code changes needed - existing code automatically uses rotated keys!

## Testing

Run the comprehensive test suite:

```bash
cd active_interview_backend
python manage.py test active_interview_app.tests.test_api_key_rotation
```

Test coverage includes:

- **Model Functionality**:
  - Key encryption/decryption
  - Key activation/deactivation
  - Usage tracking
  - Masked key display
  - Active key retrieval
  - Next key for rotation logic

- **Rotation Schedule**:
  - Schedule creation
  - Rotation due calculation
  - Next rotation date calculation
  - Different frequencies (daily/weekly/monthly/quarterly)

- **Rotation Logs**:
  - Log creation
  - Deletion prevention
  - Status tracking

- **Management Command**:
  - Successful rotation
  - Failed rotation (no keys available)
  - Forced rotation
  - Dry run mode
  - Schedule-based rotation

- **OpenAI Utils Integration**:
  - Key pool usage
  - Fallback to environment variable
  - Client refresh on key change
  - Usage increment

**Coverage Target**: 80% minimum

## Security Best Practices

### Key Management

1. **Regular Rotation**: Rotate keys weekly or monthly
2. **Multiple Keys**: Maintain at least 2 active keys in pool
3. **Backup Keys**: Keep backup keys in secure vault (e.g., 1Password, Vault)
4. **Monitor Usage**: Review usage counts regularly for anomalies
5. **Audit Logs**: Regularly review rotation logs for failed attempts

### Encryption

1. **Secure Storage**: Store encryption key in secure secrets manager
2. **Key Rotation**: Rotate encryption key periodically (requires re-encrypting all keys)
3. **Access Control**: Limit access to encryption key
4. **Backup**: Backup encryption key securely and separately

### Access Control

1. **Admin Only**: Only staff users can access key management
2. **Audit Trail**: All actions tracked with performing user
3. **No Deletion**: Rotation logs cannot be deleted
4. **Masked Display**: Keys never displayed in full

### Compliance

1. **Audit Trail**: Immutable rotation logs for compliance
2. **User Attribution**: All rotations tracked with performing user
3. **Error Logging**: Failed rotations logged with error details
4. **Notification**: Email alerts on rotation events

## Troubleshooting

### Common Issues

**"No keys available for rotation"**

**Cause**: No pending keys in pool

**Solution**: Add more keys via Django admin
```bash
# Check current keys
python manage.py shell
>>> from active_interview_app.api_key_rotation_models import APIKeyPool
>>> APIKeyPool.objects.filter(provider='openai').values('key_name', 'status')
```

**"Decryption failed"**

**Cause**: Encryption key changed or corrupted

**Solution**: Verify `API_KEY_ENCRYPTION_KEY` in environment
```bash
echo $API_KEY_ENCRYPTION_KEY
```

**"Rotation not due yet"**

**Cause**: Rotation schedule not reached

**Solution**: Use `--force` flag or adjust schedule
```bash
python manage.py rotate_api_keys --force
```

**OpenAI client still using old key**

**Cause**: Client not refreshed after rotation

**Solution**: Client refreshes automatically on next request. If immediate refresh needed:
```python
from active_interview_app.openai_utils import get_openai_client
client = get_openai_client(force_refresh=True)
```

**"Permission denied" in admin**

**Cause**: User not staff or superuser

**Solution**: Grant staff status
```bash
python manage.py shell
>>> from django.contrib.auth.models import User
>>> user = User.objects.get(username='username')
>>> user.is_staff = True
>>> user.save()
```

### Debugging

**Enable verbose logging:**

Add to `settings.py`:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'active_interview_app.api_key_rotation_models': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

**Check rotation schedule:**
```bash
python manage.py shell
>>> from active_interview_app.api_key_rotation_models import KeyRotationSchedule
>>> schedule = KeyRotationSchedule.objects.get(provider='openai')
>>> print(f"Enabled: {schedule.is_enabled}")
>>> print(f"Frequency: {schedule.rotation_frequency}")
>>> print(f"Next rotation: {schedule.next_rotation_at}")
>>> print(f"Rotation due: {schedule.is_rotation_due()}")
```

## Monitoring and Alerts

### Key Metrics to Monitor

1. **Active Key Usage**: Track usage_count per key
2. **Rotation Success Rate**: Monitor SUCCESS vs FAILED in logs
3. **Rotation Frequency**: Verify rotations happening on schedule
4. **Key Pool Size**: Ensure enough keys available
5. **Fallback Usage**: Alert if using environment variable (indicates pool issue)

### Recommended Alerts

Configure monitoring alerts for:

1. **Rotation Failure**: Alert on failed rotation attempts
   ```python
   if KeyRotationLog.objects.filter(status='failed',
                                     rotated_at__gt=last_check).exists():
       send_alert("API key rotation failed")
   ```

2. **Low Key Count**: Alert when pool has < 2 keys
   ```python
   active_count = APIKeyPool.objects.filter(
       provider='openai',
       status__in=['active', 'pending']
   ).count()
   if active_count < 2:
       send_alert("Low key count in pool")
   ```

3. **No Pending Keys**: Alert when no keys available for next rotation
   ```python
   if not APIKeyPool.objects.filter(provider='openai', status='pending').exists():
       send_alert("No pending keys for next rotation")
   ```

4. **Fallback Usage**: Alert when using environment variable
   ```python
   from active_interview_app.openai_utils import get_current_api_key_info
   info = get_current_api_key_info()
   if info['source'] == 'environment':
       send_alert("Using fallback API key from environment")
   ```

## Future Enhancements

Potential improvements for future iterations:

1. **Dashboard Integration**: Add key rotation status to observability dashboard
2. **Slack Notifications**: Alert team on rotation events via Slack
3. **Health Checks**: API endpoint to verify key validity
4. **Auto-Revocation**: Automatically revoke keys that fail repeatedly
5. **Usage Limits**: Set usage limits per key before forced rotation
6. **Multi-Region**: Support different keys for different regions
7. **Key Expiration**: Auto-revoke keys after set expiration date
8. **Provider Key Generation**: Integrate with providers that support programmatic key creation

## Related Documentation

- [Monthly Spending Tracker](./monthly-spending-tracker.md)
- [Observability Dashboard](./observability-dashboard.md)
- [Architecture Overview](../architecture/overview.md)
- [Testing Guide](../setup/testing.md)
- [Security Scanning](../setup/security-scanning.md)

## References

- **GitHub Issue #10**: [Cost Caps & API Key Rotation](https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/issues/10)
- **GitHub Issue #13**: [Automatic API Key Rotation](https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/issues/13)
- **Cryptography Library**: [https://cryptography.io/](https://cryptography.io/)
- **Fernet Encryption**: [https://cryptography.io/en/latest/fernet/](https://cryptography.io/en/latest/fernet/)

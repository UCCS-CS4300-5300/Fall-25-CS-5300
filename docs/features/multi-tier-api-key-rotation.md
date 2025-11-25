# Multi-Tier API Key Rotation with Automatic Fallback

**Related Issues:** #10, #13, #14
**Status:** ✅ Implemented
**Version:** 1.0.0

## Overview

The Multi-Tier API Key Rotation system provides automatic cost management and security through:

1. **Multi-tier model selection** - Premium, Standard, and Fallback tiers
2. **Automatic fallback** - Switches to cheaper models when budget is exceeded
3. **Independent key rotation** - Separate rotating key pools for each tier
4. **Budget-aware API calls** - All OpenAI calls automatically select the appropriate tier

## Table of Contents

- [Architecture](#architecture)
- [Model Tiers](#model-tiers)
- [Automatic Fallback Logic](#automatic-fallback-logic)
- [Key Rotation](#key-rotation)
- [Setup Guide](#setup-guide)
- [Usage](#usage)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## Architecture

### System Flow

```
User Makes API Call
      ↓
get_client_and_model()
      ↓
Check Monthly Spending
      ↓
┌─────────────────────┬──────────────────────┬───────────────────┐
│ Under 85% of cap    │ 85% - 100% of cap    │ Over 100% of cap  │
├─────────────────────┼──────────────────────┼───────────────────┤
│ Use Premium Tier    │ Use Standard Tier    │ Use Fallback Tier │
│ (GPT-4o)            │ (GPT-4-turbo)        │ (GPT-3.5-turbo)   │
└─────────────────────┴──────────────────────┴───────────────────┘
      ↓
Get Active Key for Selected Tier
      ↓
Make API Call with Tier-Specific Key & Model
      ↓
Track Usage & Cost
```

### Components

1. **APIKeyPool** - Stores encrypted API keys with tier assignment
2. **KeyRotationSchedule** - Manages rotation schedules per tier
3. **KeyRotationLog** - Audit trail of all rotations
4. **MonthlySpending** - Tracks current month's API spending
5. **MonthlySpendingCap** - Configurable budget limit
6. **model_tier_manager.py** - Tier selection logic

---

## Model Tiers

### Tier Definitions

| Tier | Model | Cost Multiplier | Use Case |
|------|-------|-----------------|----------|
| **Premium** | GPT-4o | 10x | Normal operations, highest quality |
| **Standard** | GPT-4-turbo | 5x | Approaching budget limit |
| **Fallback** | GPT-3.5-turbo | 1x | Budget exceeded, cost savings |

### Automatic Tier Selection

The system automatically selects the appropriate tier based on spending:

```python
# Spending < 85% of cap → Premium (GPT-4o)
if percentage < 85:
    tier = 'premium'

# Spending 85-100% of cap → Standard (GPT-4-turbo)
elif percentage < 100:
    tier = 'standard'

# Spending > 100% of cap → Fallback (GPT-3.5-turbo)
else:
    tier = 'fallback'
```

---

## Automatic Fallback Logic

### When Fallback Activates

**Scenario:** Monthly spending cap is $200

- **$0 - $170** (0-85%): Uses Premium tier (GPT-4o)
- **$170 - $200** (85-100%): Uses Standard tier (GPT-4-turbo)
- **$200+** (100%+): Uses Fallback tier (GPT-3.5-turbo)

### Example Flow

```python
from active_interview_app.openai_utils import get_client_and_model

# This function automatically handles everything!
client, model, tier_info = get_client_and_model()

print(tier_info)
# Output when over budget:
# {
#     'active_tier': 'fallback',
#     'model': 'gpt-3.5-turbo',
#     'reason': 'Budget exceeded (105% of cap used)',
#     'spending_info': {
#         'spent': 210.00,
#         'cap_amount': 200.00,
#         'percentage': 105.0,
#         'is_over_cap': True
#     }
# }

# Make API call with automatically selected model
response = client.chat.completions.create(
    model=model,  # Automatically 'gpt-3.5-turbo' when over budget
    messages=[{"role": "user", "content": "Hello"}]
)
```

---

## Key Rotation

### Independent Rotation Per Tier

Each tier maintains its own pool of rotating keys:

```
Premium Tier Pool:
  ✅ sk-proj-premium-1 (ACTIVE)
  ⏸ sk-proj-premium-2 (INACTIVE)
  ⏸ sk-proj-premium-3 (INACTIVE)

Standard Tier Pool:
  ✅ sk-proj-standard-1 (ACTIVE)
  ⏸ sk-proj-standard-2 (INACTIVE)

Fallback Tier Pool:
  ✅ sk-proj-fallback-1 (ACTIVE)
  ⏸ sk-proj-fallback-2 (INACTIVE)
  🔄 OPENAI_API_FALLBACK_KEY (env var backup)
```

### Rotation Commands

```bash
# Rotate specific tier
python manage.py rotate_api_keys --tier premium

# Rotate fallback tier
python manage.py rotate_api_keys --tier fallback

# Rotate all tiers
python manage.py rotate_api_keys --all

# Force rotation even if not due
python manage.py rotate_api_keys --force --tier premium

# Dry run (see what would happen)
python manage.py rotate_api_keys --dry-run --tier fallback
```

### Rotation Schedules

Each tier can have different rotation frequencies:

```python
# Premium tier: weekly rotation
KeyRotationSchedule.objects.create(
    provider='openai',
    model_tier='premium',
    is_enabled=True,
    rotation_frequency='weekly'
)

# Fallback tier: daily rotation (higher security)
KeyRotationSchedule.objects.create(
    provider='openai',
    model_tier='fallback',
    is_enabled=True,
    rotation_frequency='daily'
)
```

---

## Setup Guide

### 1. Run Migration

```bash
cd active_interview_backend
python manage.py migrate
```

This creates the `model_tier` field on `APIKeyPool` and `KeyRotationSchedule`.

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Primary API key (used for premium/standard tiers)
OPENAI_API_KEY=sk-proj-xxx

# Fallback API key (used when budget exceeded)
OPENAI_API_FALLBACK_KEY=sk-proj-yyy
```

### 3. Set Monthly Spending Cap

```bash
# Set $200/month cap (as per user story)
python manage.py set_spending_cap 200 --user admin
```

### 4. Add Keys to Pool (Optional but Recommended)

Via Django Admin (`/admin/`):

1. Go to **API Key Pool**
2. Click **Add API Key**
3. Fill in:
   - **Provider**: OpenAI
   - **Model Tier**: Premium, Standard, or Fallback
   - **Key Name**: Descriptive name (e.g., "Production Premium Key 1")
   - **API Key**: Your actual OpenAI API key
   - **Status**: Active (for first key) or Inactive (for rotation pool)

Repeat for multiple keys per tier to enable rotation.

### 5. Configure Rotation Schedules (Optional)

```bash
# Via Django Admin or shell
from active_interview_app.api_key_rotation_models import KeyRotationSchedule

# Premium tier: weekly rotation
KeyRotationSchedule.objects.create(
    provider='openai',
    model_tier='premium',
    is_enabled=True,
    rotation_frequency='weekly',
    notification_email='admin@example.com'
)

# Fallback tier: daily rotation
KeyRotationSchedule.objects.create(
    provider='openai',
    model_tier='fallback',
    is_enabled=True,
    rotation_frequency='daily'
)
```

---

## Usage

### For Developers

**Before (hardcoded GPT-4o):**

```python
response = get_openai_client().chat.completions.create(
    model="gpt-4o",  # Hardcoded!
    messages=[...]
)
```

**After (automatic tier selection):**

```python
from active_interview_app.openai_utils import get_client_and_model

# Automatically selects model based on budget
client, model, tier_info = get_client_and_model()

response = client.chat.completions.create(
    model=model,  # Dynamically selected based on spending
    messages=[...]
)

# Optional: Log which tier was used
print(f"Used {tier_info['active_tier']} tier: {model}")
# Output: "Used fallback tier: gpt-3.5-turbo"
```

### For Admins

**Monitor Current Tier:**

```python
from active_interview_app.model_tier_manager import get_tier_info

info = get_tier_info()
print(f"Active Tier: {info['active_tier']}")
print(f"Model: {info['model']}")
print(f"Reason: {info['reason']}")
print(f"Spending: ${info['spending_info']['spent']}/{info['spending_info']['cap_amount']}")
```

**Manually Force Tier (for testing):**

```python
from active_interview_app.openai_utils import get_client_and_model

# Force fallback tier (ignores spending)
client, model, tier_info = get_client_and_model(force_tier='fallback')
```

**Check if Fallback is Active:**

```python
from active_interview_app.model_tier_manager import should_switch_to_fallback

should_switch, reason = should_switch_to_fallback()
if should_switch:
    print(f"ALERT: Fallback tier active - {reason}")
```

---

## Testing

### Run Tests

```bash
cd active_interview_backend

# Run all multi-tier rotation tests
python manage.py test active_interview_app.tests.test_multi_tier_rotation

# Run specific test class
python manage.py test active_interview_app.tests.test_multi_tier_rotation.AutomaticFallbackSwitchingTestCase

# Run with verbose output
python manage.py test active_interview_app.tests.test_multi_tier_rotation -v 2
```

### Test Coverage

The test suite covers:

- ✅ Model tier fields exist and work
- ✅ Tier-based key selection
- ✅ Key activation only affects same tier
- ✅ Automatic fallback switching at budget thresholds
- ✅ Model selection per tier
- ✅ Independent key rotation per tier
- ✅ Rotation logging includes tier info
- ✅ Separate rotation schedules per tier

### Manual Testing Workflow

1. **Set low spending cap** for testing:
   ```bash
   python manage.py set_spending_cap 10
   ```

2. **Make API calls** to accumulate spending:
   ```python
   # In Django shell (python manage.py shell)
   from active_interview_app.openai_utils import get_client_and_model

   client, model, tier_info = get_client_and_model()
   print(f"Tier: {tier_info['active_tier']}, Model: {model}")
   ```

3. **Verify tier switches**:
   - At 0% of cap → Should use `premium` tier
   - At 85%+ of cap → Should use `standard` tier
   - At 100%+ of cap → Should use `fallback` tier

4. **Test rotation**:
   ```bash
   python manage.py rotate_api_keys --tier fallback --force
   ```

---

## Troubleshooting

### Issue: "No OpenAI API key available for tier 'fallback'"

**Cause:** No fallback key configured.

**Solution:** Add `OPENAI_API_FALLBACK_KEY` to `.env` or add keys to the pool:

```bash
# Option 1: Use environment variable
OPENAI_API_FALLBACK_KEY=sk-proj-your-fallback-key

# Option 2: Add to API Key Pool via Django admin
# Set model_tier='fallback' when adding the key
```

### Issue: "No keys available for rotation in openai fallback pool"

**Cause:** Only one fallback key exists, nothing to rotate to.

**Solution:** Add more keys to the fallback tier pool via Django admin.

### Issue: Still using GPT-4o even though over budget

**Cause:** Views are still using old `get_openai_client()` directly.

**Solution:** Ensure all views use `get_client_and_model()`:

```python
# Wrong:
client = get_openai_client()
response = client.chat.completions.create(model="gpt-4o", ...)

# Correct:
client, model, tier_info = get_client_and_model()
response = client.chat.completions.create(model=model, ...)
```

### Issue: Migration fails with "max_digits" error

**Cause:** Old migration file had typo using `max_digits` instead of `max_length` for CharField.

**Solution:** This was fixed in migration `0016_add_model_tier_to_api_keys.py`. If you encounter this:

```bash
# Delete old migration (if it exists)
rm active_interview_backend/active_interview_app/migrations/0015_apikeypool_keyrotationlog_keyrotationschedule.py

# Re-run migrations
python manage.py migrate
```

### Issue: How do I know which tier is being used?

**Solution:** Check tier info in the response:

```python
client, model, tier_info = get_client_and_model()

print(f"Active Tier: {tier_info['active_tier']}")
print(f"Model: {model}")
print(f"Reason: {tier_info['reason']}")

if tier_info['spending_info']:
    print(f"Budget Status: {tier_info['spending_info']['percentage']}%")
```

Or check the observability dashboard at `/admin/observability/`.

---

## API Reference

### `get_client_and_model(force_tier=None)`

Get OpenAI client and model name with automatic tier selection.

**Parameters:**
- `force_tier` (str, optional): Force specific tier ('premium', 'standard', 'fallback')

**Returns:**
- `tuple`: (client, model_name, tier_info)
  - `client`: OpenAI client instance
  - `model_name`: Model to use (e.g., 'gpt-4o', 'gpt-3.5-turbo')
  - `tier_info`: Dict with tier details and spending info

**Example:**
```python
from active_interview_app.openai_utils import get_client_and_model

client, model, tier_info = get_client_and_model()
response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Hello"}]
)
```

### `get_active_tier(force_tier=None)`

Determine which model tier should be used based on spending cap.

**Parameters:**
- `force_tier` (str, optional): Force specific tier

**Returns:**
- `str`: Active tier ('premium', 'standard', or 'fallback')

### `get_model_for_tier(tier='premium', provider='openai')`

Get the model name for a specific tier and provider.

**Parameters:**
- `tier` (str): Model tier
- `provider` (str): Provider name

**Returns:**
- `str`: Model name

### `get_tier_info()`

Get comprehensive information about current tier and spending.

**Returns:**
- `dict`: Tier information including active tier, model, reason, and spending details

### `should_switch_to_fallback()`

Check if system should switch to fallback tier.

**Returns:**
- `tuple`: (should_switch, reason)
  - `should_switch` (bool): True if should switch
  - `reason` (str): Explanation

---

## Best Practices

### 1. Always Use `get_client_and_model()`

Don't call `get_openai_client()` directly in new code. Use the wrapper that handles tier selection:

```python
# ❌ Don't do this
client = get_openai_client()
response = client.chat.completions.create(model="gpt-4o", ...)

# ✅ Do this
client, model, tier_info = get_client_and_model()
response = client.chat.completions.create(model=model, ...)
```

### 2. Set Reasonable Budget Caps

Don't set caps too low or you'll spend most of your time in fallback mode:

```bash
# Too low - will hit fallback quickly
python manage.py set_spending_cap 10

# Better - reasonable buffer
python manage.py set_spending_cap 500
```

### 3. Add Multiple Keys Per Tier

For effective rotation, add at least 2-3 keys per tier:

```
Premium Tier: 3 keys (weekly rotation)
Standard Tier: 2 keys (weekly rotation)
Fallback Tier: 2-3 keys (daily rotation)
```

### 4. Monitor Rotation Logs

Check rotation logs regularly to ensure keys are rotating as expected:

```python
from active_interview_app.api_key_rotation_models import KeyRotationLog

# Get recent rotations
recent_rotations = KeyRotationLog.get_recent_rotations(limit=10)

for log in recent_rotations:
    print(f"{log.provider} {log.old_key_masked} → {log.new_key_masked}: {log.status}")
```

### 5. Set Up Rotation Notifications

Enable email notifications for rotation events:

```python
schedule = KeyRotationSchedule.objects.get(
    provider='openai',
    model_tier='premium'
)
schedule.notify_on_rotation = True
schedule.notification_email = 'admin@example.com'
schedule.save()
```

---

## Related Documentation

- [Monthly Spending Tracker](monthly-spending-tracker.md)
- [API Key Rotation](api-key-rotation.md)
- [Architecture Overview](../architecture/overview.md)
- [Testing Guide](../setup/testing.md)

---

## Changelog

### Version 1.0.0 (2025-11-22)

- ✅ Initial implementation
- ✅ Multi-tier model selection (premium/standard/fallback)
- ✅ Automatic fallback when budget exceeded
- ✅ Independent key rotation per tier
- ✅ Comprehensive test suite
- ✅ Management command updates
- ✅ Documentation complete

---

## Support

For issues or questions:
- **GitHub Issues**: [#10](../../issues/10), [#13](../../issues/13), [#14](../../issues/14)
- **Documentation**: This file
- **Tests**: `active_interview_app/tests/test_multi_tier_rotation.py`

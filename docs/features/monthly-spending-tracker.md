# Monthly Spending Tracker

**Related Issues:** #10 (Cost Caps & API Key Rotation), #11 (Track Monthly Spending), #12 (Set Monthly Spend Cap)

## Overview

The Monthly Spending Tracker provides administrators with real-time visibility into API spending across all services (LLM, TTS, etc.). It helps prevent budget overruns by tracking costs against a configurable monthly cap and providing visual alerts when spending approaches or exceeds limits.

## Features

### 1. Real-Time Spending Tracking (Issue #11)

The system automatically tracks spending as API calls are made:

- **Automatic Updates**: Spending totals update automatically when `TokenUsage` records are created
- **Service Breakdown**: Separate tracking for LLM (GPT-4o, Claude), TTS, and other services
- **Request Counting**: Tracks both cost and number of requests per service

### 2. Monthly Spending Cap (Issue #12)

Administrators can configure a monthly spending limit:

- **Configurable Cap**: Set via Django admin or management command
- **Single Active Cap**: Only one cap can be active at a time
- **Audit Trail**: Tracks who set the cap and when

### 3. Visual Dashboard

The observability dashboard displays:

- **Progress Bar**: Visual representation of spending vs. cap
- **Alert Levels**: Color-coded warnings (OK, Caution, Warning, Critical, Danger)
- **Service Breakdown**: Detailed cost breakdown by service type
- **Real-Time Updates**: Auto-refresh capability

### 4. Alert Levels

The system provides visual alerts based on spending percentage:

| Percentage | Alert Level | Color  | Description                  |
|-----------|-------------|--------|------------------------------|
| 0-50%     | OK          | Green  | Spending within normal range |
| 50-75%    | Caution     | Blue   | Approaching midpoint         |
| 75-90%    | Warning     | Yellow | Getting close to limit       |
| 90-100%   | Critical    | Orange | Very close to limit          |
| 100%+     | Danger      | Red    | Over budget                  |

## Database Schema

### MonthlySpendingCap

Stores monthly spending cap configuration.

```python
class MonthlySpendingCap(models.Model):
    cap_amount_usd = DecimalField()      # Maximum monthly spending in USD
    is_active = BooleanField()           # Whether this cap is active
    created_by = ForeignKey(User)        # Admin who set this cap
    created_at = DateTimeField()
    updated_at = DateTimeField()
```

### MonthlySpending

Tracks actual spending for each month.

```python
class MonthlySpending(models.Model):
    year = IntegerField()                # Year (e.g., 2025)
    month = IntegerField()               # Month (1-12)

    # Cost breakdown
    total_cost_usd = DecimalField()      # Total spending
    llm_cost_usd = DecimalField()        # LLM costs
    tts_cost_usd = DecimalField()        # TTS costs
    other_cost_usd = DecimalField()      # Other costs

    # Request counts
    total_requests = IntegerField()
    llm_requests = IntegerField()
    tts_requests = IntegerField()

    # Metadata
    created_at = DateTimeField()
    updated_at = DateTimeField()
    last_updated_from_token_usage = DateTimeField()
```

## Usage

### Setting a Spending Cap

**Via Dashboard UI (Recommended):**

1. Navigate to `/admin/observability/`
2. Click the **"Configure Cap"** button in the Monthly Spending Tracker section
3. Enter your desired monthly spending limit (e.g., 200.00)
4. Click **"Save Cap"**
5. The dashboard will update immediately with the new cap

The modal shows:
- Current cap amount
- Current spending for the month
- Status (OK, Warning, Critical, etc.)

**Via Management Command:**

```bash
# Set cap to $200/month
python manage.py set_spending_cap 200

# Set cap with admin user tracking
python manage.py set_spending_cap 200 --user admin
```

**Via Django Admin:**

1. Navigate to Django Admin → Active Interview App → Monthly Spending Caps
2. Click "Add Monthly Spending Cap"
3. Enter cap amount and ensure "Is active" is checked
4. Save

### Viewing Spending in Dashboard

1. Navigate to `/admin/observability/`
2. The Monthly Spending Tracker appears at the top of the dashboard
3. View current month spending, cap status, and service breakdown

### Updating Spending from Historical Data

If you're enabling spending tracking on an existing system with historical `TokenUsage` data:

```bash
# Update current month
python manage.py update_monthly_spending

# Update specific month
python manage.py update_monthly_spending --month 2025-11

# Update all months
python manage.py update_monthly_spending --all
```

### API Endpoints

**Update Spending Cap:**

```
POST /admin/observability/api/spending/update-cap/
Content-Type: application/json

{
  "cap_amount": 200.00
}
```

Response:
```json
{
  "success": true,
  "message": "Spending cap updated to $200.00/month",
  "cap": {
    "id": 1,
    "amount": 200.00,
    "created_by": "admin",
    "created_at": "2025-11-22T10:30:00Z"
  }
}
```

Validation errors (400):
```json
{
  "success": false,
  "error": "cap_amount must be a positive number"
}
```

**Current Month Spending:**

```
GET /admin/observability/api/spending/current/
```

Response:
```json
{
  "year": 2025,
  "month": 11,
  "total_cost": 110.00,
  "llm_cost": 100.00,
  "tts_cost": 10.00,
  "other_cost": 0.00,
  "total_requests": 35,
  "llm_requests": 15,
  "tts_requests": 20,
  "cap_status": {
    "has_cap": true,
    "cap_amount": 200.00,
    "spent": 110.00,
    "remaining": 90.00,
    "percentage": 55.0,
    "alert_level": "caution",
    "is_over_cap": false
  },
  "last_updated": "2025-11-22T10:30:00Z"
}
```

**Spending History:**

```
GET /admin/observability/api/spending/history/?months=6
```

Response:
```json
{
  "months": [
    {
      "year": 2025,
      "month": 11,
      "month_label": "2025-11",
      "total_cost": 110.00,
      "llm_cost": 100.00,
      "tts_cost": 10.00,
      "total_requests": 35
    },
    ...
  ]
}
```

## Technical Implementation

### Automatic Spending Tracking

Spending is tracked automatically via Django signals:

```python
@receiver(post_save, sender='active_interview_app.TokenUsage')
def update_monthly_spending(sender, instance, created, **kwargs):
    """Update monthly spending when a new TokenUsage record is created."""
    if not created:
        return

    spending = MonthlySpending.get_current_month()
    cost = instance.estimated_cost
    if cost > 0:
        spending.add_llm_cost(cost)
```

### Cost Calculation

Costs are calculated from token usage based on model pricing:

```python
# GPT-4o pricing (per 1000 tokens)
prompt_cost = (prompt_tokens / 1000) * 0.03
completion_cost = (completion_tokens / 1000) * 0.06
total_cost = prompt_cost + completion_cost
```

### Monthly Reset

Spending automatically resets at the beginning of each month because records are keyed by year and month. When a new month begins, a new `MonthlySpending` record is automatically created on the first API call.

## Testing

Run the test suite:

```bash
cd active_interview_backend
python manage.py test active_interview_app.tests.test_spending_tracker
```

Test coverage includes:

- Model functionality (MonthlySpendingCap, MonthlySpending)
- Signal-based automatic tracking
- API views
- Alert level calculations
- Complete integration workflows

## Permissions

All spending tracker features require staff permissions:

- Dashboard views: `@staff_member_required`
- API endpoints: `@staff_member_required`
- Django admin: Standard admin permissions

## Monitoring and Maintenance

### Daily Monitoring

1. Check dashboard daily to monitor spending trends
2. Review alert levels and adjust usage if approaching cap
3. Verify spending totals match expected usage

### Monthly Tasks

1. Review previous month's spending
2. Adjust cap if needed for upcoming month
3. Analyze spending patterns by service type

### Troubleshooting

**Spending totals seem incorrect:**

```bash
python manage.py update_monthly_spending --month YYYY-MM
```

**No cap showing in dashboard:**

Verify an active cap exists in Django admin or create one:

```bash
python manage.py set_spending_cap 200
```

**Dashboard not updating:**

1. Check browser console for JavaScript errors
2. Verify API endpoints are accessible
3. Check staff permissions for current user

## Future Enhancements

Related issues for future implementation:

- **Issue #13**: Automatic API Key Rotation
- **Issue #14**: Automatic Fallback Service Switching (when cap is exceeded)
- Email notifications when spending reaches thresholds
- Spending forecasting based on historical trends
- Per-user or per-service spending limits

## Related Documentation

- [Observability Dashboard](../architecture/observability-dashboard.md)
- [Token Usage Tracking](./token-usage-tracking.md)
- [Architecture Overview](../architecture/overview.md)
- [Testing Guide](../setup/testing.md)

## References

- **GitHub Issue #10**: [Cost Caps & API Key Rotation](https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/issues/10)
- **GitHub Issue #11**: [Track Monthly Spending](https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/issues/11)
- **GitHub Issue #12**: [Set Monthly Spend Cap](https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/issues/12)

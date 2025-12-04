# Rate Limiting

## Overview

The Active Interview Service implements rate limiting to prevent API abuse and ensure fair usage across all users. Rate limits are enforced on all API endpoints and vary based on user authentication status and operation type.

## Rate Limit Configuration

### Default Limits

| User Type | Limit | Window |
|-----------|-------|--------|
| **Authenticated Users** | 60 requests | 1 minute |
| **Anonymous Users** | 30 requests | 1 minute |

### Operation-Specific Limits

Different types of operations have different rate limits based on their resource intensity:

#### Strict Limits (Resource-Intensive Operations)
- **Authenticated**: 20 requests/minute
- **Anonymous**: 10 requests/minute
- **Applies to**: Create, Update, Delete operations, AI-powered analysis

#### Lenient Limits (Read-Only Operations)
- **Authenticated**: 120 requests/minute
- **Anonymous**: 60 requests/minute
- **Applies to**: List, Retrieve operations

## How It Works

### Rate Limiting Key

Rate limits are tracked based on:
- **Authenticated users**: User ID
- **Anonymous users**: IP address

This ensures that each user or IP address has their own independent rate limit counter.

### Time Windows

Rate limit counters reset after the time window expires (1 minute for all current limits). The counters are stored in Django's cache backend for efficient tracking.

## HTTP 429 Response

When you exceed the rate limit, you'll receive an HTTP 429 (Too Many Requests) response with the following:

### Response Headers

```
HTTP/1.1 429 Too Many Requests
Retry-After: 60
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1234567890
```

- **Retry-After**: Seconds until you can make requests again
- **X-RateLimit-Limit**: Your maximum requests per window
- **X-RateLimit-Remaining**: Requests remaining in current window
- **X-RateLimit-Reset**: Unix timestamp when the limit resets

### JSON Response (API Endpoints)

```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 60
}
```

### HTML Response (Web Pages)

Web pages will display a user-friendly error page (429.html) explaining the rate limit and when they can try again.

## Affected Endpoints

### API Views (Strict Limits)

These endpoints have strict rate limits due to resource-intensive operations:

- `POST /api/job-listing/analyze/` - Job listing AI analysis
- `POST /api/uploaded-job-listing/` - Upload job listing
- `POST /api/uploaded-resume/` - Upload resume
- `POST /api/job-listing/` - Create job listing

### ViewSets (Dynamic Limits)

ViewSets automatically apply different limits based on the operation:

- **List/Retrieve** (Lenient): Question banks, Questions, Tags, Templates
- **Create/Update/Delete** (Strict): Question banks, Questions, Tags, Templates

#### Specific ViewSets:
- `/api/question-banks/` - QuestionBankViewSet
- `/api/questions/` - QuestionViewSet
- `/api/tags/` - TagViewSet
- `/api/interview-templates/` - InterviewTemplateViewSet

## Configuration

### Settings

Rate limiting can be configured in `settings.py`:

```python
# Enable/disable rate limiting
RATELIMIT_ENABLE = True

# Cache backend to use for rate limiting
RATELIMIT_USE_CACHE = 'default'
```

### Rate Limit Groups

Three rate limit groups are defined in `ratelimit_config.py`:

```python
# Default limits
DEFAULT_AUTHENTICATED_RATE = '60/m'
DEFAULT_ANONYMOUS_RATE = '30/m'

# Strict limits (resource-intensive)
STRICT_AUTHENTICATED_RATE = '20/m'
STRICT_ANONYMOUS_RATE = '10/m'

# Lenient limits (read-only)
LENIENT_AUTHENTICATED_RATE = '120/m'
LENIENT_ANONYMOUS_RATE = '60/m'
```

## Implementation Details

### For Developers

#### Applying Rate Limits to Views

**Function-Based Views:**

```python
from .decorators import ratelimit_default, ratelimit_strict

@ratelimit_default(methods=['GET', 'POST'])
def my_view(request):
    # View logic
    pass

@ratelimit_strict(methods=['POST'])
def resource_intensive_view(request):
    # View logic
    pass
```

**Class-Based API Views:**

```python
from .decorators import ratelimit_api

class MyAPIView(APIView):
    @ratelimit_api('strict')
    def post(self, request):
        # View logic
        pass

    @ratelimit_api('lenient')
    def get(self, request):
        # View logic
        pass
```

**ViewSets:**

```python
from .mixins import RateLimitMixin

class MyViewSet(RateLimitMixin, viewsets.ModelViewSet):
    # Automatically applies lenient limits to read operations
    # and strict limits to write operations
    pass
```

## Best Practices

### For API Consumers

1. **Implement Retry Logic**: When you receive a 429 response, respect the `Retry-After` header
2. **Cache Responses**: Cache GET responses when possible to reduce API calls
3. **Batch Operations**: Combine multiple operations into single requests when possible
4. **Use Authentication**: Authenticated users have higher rate limits

### Example Retry Logic (Python)

```python
import time
import requests

def make_request_with_retry(url):
    response = requests.get(url)

    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        print(f"Rate limited. Waiting {retry_after} seconds...")
        time.sleep(retry_after)
        return make_request_with_retry(url)

    return response
```

### Example Retry Logic (JavaScript)

```javascript
async function makeRequestWithRetry(url) {
    const response = await fetch(url);

    if (response.status === 429) {
        const retryAfter = response.headers.get('Retry-After') || 60;
        console.log(`Rate limited. Waiting ${retryAfter} seconds...`);
        await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
        return makeRequestWithRetry(url);
    }

    return response;
}
```

## Violation Monitoring and Analytics

### Overview

The system automatically logs all rate limit violations and provides comprehensive monitoring tools for administrators to identify abuse patterns and adjust limits as needed.

### Violation Logging

Every rate limit violation is automatically logged with:
- **Timestamp**: When the violation occurred
- **User Information**: User ID and username (if authenticated)
- **IP Address**: Client IP address
- **Endpoint**: The API endpoint that was rate limited
- **HTTP Method**: GET, POST, PUT, DELETE, etc.
- **Rate Limit Type**: default, strict, or lenient
- **Limit Value**: The limit that was exceeded
- **User Agent**: Client user agent string
- **Country Code**: Geographic location (if available)
- **Alert Status**: Whether an alert was sent for this violation

### Admin Dashboard

Administrators can access the rate limit monitoring dashboard at:

```
/admin/ratelimit/dashboard/
```

**Dashboard Features:**

1. **Statistics Cards**
   - Violations in last hour
   - Violations in last 24 hours
   - Violations in last 7 days
   - Total violations

2. **Authentication Analysis**
   - Authenticated vs Anonymous violations
   - Breakdown by rate limit type

3. **Top Violators**
   - Shows users/IPs with most violations
   - Sortable by time period (last 7 days by default)

4. **Top Endpoints**
   - Identifies which endpoints are being rate limited most
   - Helps identify potential issues or abuse patterns

5. **Recent Violations**
   - Real-time feed of latest violations
   - Detailed information for each violation
   - Link to view full details

### Violation Details

Click on any violation to view:
- Complete violation information
- Related violations from same user/IP
- Full user agent string
- Geographic information

**URL Pattern:**
```
/admin/ratelimit/violation/<violation_id>/
```

### Advanced Analytics

Access detailed analytics at:

```
/admin/ratelimit/analytics/
```

**Analytics Features:**

1. **Hourly Distribution**
   - Violations by hour of day (0-23)
   - Identify peak abuse times

2. **Daily Distribution**
   - Violations by day of week
   - Pattern recognition

3. **Client Type Analysis**
   - Browser vs Mobile vs Bot vs Script
   - Identify automated abuse

4. **Geographic Distribution**
   - Top 10 countries by violations
   - Visual distribution charts

**Time Range Options:**
- Last 24 Hours
- Last 7 Days (default)
- Last 30 Days
- Last 90 Days

### Alert System

#### Configuration

Alerts are configured in `settings.py`:

```python
# Alert threshold settings
RATELIMIT_ALERT_THRESHOLD = 10  # Number of violations to trigger alert
RATELIMIT_ALERT_WINDOW = 5      # Time window in minutes
```

#### How Alerts Work

When violations exceed the threshold within the time window:
1. Email is sent to all admin users (via `mail_admins`)
2. Alert includes:
   - Total violation count
   - Time window
   - Top violators list
   - Link to dashboard

**Alert Email Example:**
```
Subject: ⚠️ Rate Limit Alert: 12 violations in 5 minutes

Rate Limit Threshold Exceeded

Total Violations: 12
Time Window: 5 minutes
Timestamp: 2025-01-30 14:23:45

Top Violators:
- testuser (User ID: 1): 8 violations
- 192.168.1.1: 4 violations

Please review the rate limit violations in the admin dashboard:
https://activeinterviewservice.app/admin/ratelimit/dashboard/
```

#### Configuring Email Alerts

Ensure email is configured in `settings.py`:

```python
# Production email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@activeinterviewservice.app')

# Admin users to receive alerts
ADMINS = [
    ('Admin Name', 'admin@example.com'),
]
```

### Export Functionality

#### CSV Export

Export violation logs for analysis:

```
/admin/ratelimit/export/
```

**Available Filters:**
- Start date (`start_date=2025-01-01`)
- End date (`end_date=2025-01-31`)
- User ID (`user_id=123`)
- IP address (`ip_address=192.168.1.1`)
- Endpoint (`endpoint=/api/test/`)

**Example Export URL:**
```
/admin/ratelimit/export/?start_date=2025-01-01&end_date=2025-01-31&user_id=5
```

**CSV Format:**

The exported CSV includes these columns:
- Timestamp
- User ID
- Username
- IP Address
- Endpoint
- Method
- Rate Limit Type
- Limit Value
- User Agent (truncated to 100 chars)
- Country Code
- Alert Sent

**Example Usage:**
```bash
# Download violations for specific date range
curl -H "Cookie: sessionid=YOUR_SESSION" \
    "https://activeinterviewservice.app/admin/ratelimit/export/?start_date=2025-01-01&end_date=2025-01-31" \
    > violations.csv
```

### Django Admin Integration

The `RateLimitViolation` model is registered in Django admin:

```
/admin/active_interview_app/ratelimitviolation/
```

**Admin Features:**
- List view with filters (type, method, alert sent, date)
- Search by username, email, IP, endpoint
- Date hierarchy for easy browsing
- Read-only fields (violations can't be manually created)
- Link to dashboard from changelist view
- Optimized queries with select_related

**List Filters:**
- Rate limit type (default/strict/lenient)
- HTTP method (GET/POST/PUT/DELETE)
- Alert sent (Yes/No)
- Timestamp (date hierarchy)
- Country code

**Search Fields:**
- Username
- Email
- IP address
- Endpoint

### Monitoring Best Practices

#### For Administrators

1. **Regular Review**
   - Check dashboard daily
   - Review weekly trends
   - Identify abuse patterns

2. **Alert Response**
   - Investigate high-volume violators
   - Check for legitimate vs malicious traffic
   - Adjust rate limits if needed

3. **Pattern Analysis**
   - Use analytics to identify peak times
   - Check geographic distribution for anomalies
   - Monitor client types for bot activity

4. **Export and Archive**
   - Regularly export logs for long-term storage
   - Analyze trends over time
   - Keep records for compliance

#### Identifying Abuse vs Legitimate Use

**Abuse Indicators:**
- Same IP with many violations in short period
- Bot/script user agents with high violation count
- Unusual geographic distribution
- Violations outside normal business hours
- Consistent endpoint targeting

**Legitimate Use Indicators:**
- Browser user agents
- Normal usage patterns with occasional spikes
- Authenticated users with valid reasons
- Responsive to rate limit errors (stops retrying)

### Adjusting Rate Limits

If monitoring reveals legitimate users hitting limits:

1. **Review the data**
   ```python
   # Check violation patterns
   violations = RateLimitViolation.get_top_violators(days=7)
   ```

2. **Adjust limits in `ratelimit_config.py`**
   ```python
   # Increase limits if needed
   STRICT_AUTHENTICATED_RATE = '30/m'  # Was 20/m
   ```

3. **Monitor impact**
   - Check if violations decrease
   - Ensure server performance remains good
   - Review after 24-48 hours

### Monitoring API

Access monitoring data programmatically:

**Trends Data (JSON):**
```
/admin/ratelimit/trends-data/?period=24h
```

**Period Options:**
- `1h` - Last hour (5-minute intervals)
- `24h` - Last 24 hours (1-hour intervals)
- `7d` - Last 7 days (6-hour intervals)
- `30d` - Last 30 days (1-day intervals)

**Response Format:**
```json
{
  "data": [
    {
      "time": "14:00",
      "count": 5,
      "timestamp": 1706623200
    },
    ...
  ],
  "period": "24h"
}
```

## Monitoring and Debugging

### Checking Current Limits

You can check your current rate limit status by examining the response headers on any API request:

```bash
curl -I -H "Authorization: Bearer YOUR_TOKEN" \
    https://activeinterviewservice.app/api/question-banks/
```

### Common Issues

**Issue**: Getting 429 errors unexpectedly
- **Solution**: Check if you're making requests in a loop without delays
- **Solution**: Ensure you're using authentication for higher limits
- **Solution**: Check the dashboard to see your violation history

**Issue**: Rate limits seem to reset slowly
- **Solution**: Rate limits are per-minute; wait a full minute for reset
- **Solution**: Check that cache backend is properly configured

**Issue**: Alerts not being sent
- **Solution**: Verify email configuration in settings.py
- **Solution**: Check ADMINS setting has valid email addresses
- **Solution**: Review email backend logs for errors

## Testing

Rate limiting behavior and monitoring can be tested using the test suite:

```bash
# Run all rate limit tests
pytest active_interview_app/tests/test_ratelimit.py

# Run monitoring tests
pytest active_interview_app/tests/test_ratelimit_monitoring.py

# Run specific test class
pytest active_interview_app/tests/test_ratelimit.py::APIViewRateLimitTest

# Run specific monitoring test
pytest active_interview_app/tests/test_ratelimit_monitoring.py::RateLimitViolationModelTest

# Disable rate limiting for other tests
pytest --override-settings=RATELIMIT_ENABLE=False
```

**Test Coverage:**

Rate Limiting Tests (`test_ratelimit.py`):
- API view rate limiting
- ViewSet rate limiting
- Authenticated vs anonymous limits
- Different rate limit groups
- Enable/disable functionality

Monitoring Tests (`test_ratelimit_monitoring.py`):
- Violation model creation and queries
- Top violators detection
- Alert threshold checking
- Admin dashboard views
- CSV export functionality
- Analytics views

## Security Considerations

1. **IP-based limiting** helps prevent anonymous abuse
2. **User-based limiting** ensures fair usage among authenticated users
3. **Different limits by operation** prevents resource exhaustion
4. **Cache-based tracking** ensures efficient performance

## Future Enhancements

Potential improvements for consideration:

- [ ] Per-user custom rate limits (premium users)
- [ ] Dynamic rate limiting based on server load
- [x] ~~Rate limit analytics dashboard~~ (Completed - Issues #10, #15)
- [ ] Whitelist/blacklist functionality
- [ ] Rate limit bypass for trusted services
- [ ] Automated response to repeated violators (temporary bans)
- [ ] Integration with CDN/WAF for DDoS protection

## Support

If you're experiencing issues with rate limiting or need higher limits:

1. Ensure you're authenticated
2. Contact support with your use case
3. Consider caching responses
4. Implement proper retry logic

For more information, see:
- [Django-ratelimit documentation](https://django-ratelimit.readthedocs.io/)
- [API Documentation](API.md)
- [Contributing Guidelines](CONTRIBUTING.md)

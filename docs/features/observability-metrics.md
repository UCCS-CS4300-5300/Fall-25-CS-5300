# Observability Metrics

**Related Issues:** #14, #15

## Overview

The observability metrics system provides comprehensive monitoring and analysis of application performance, error rates, and provider costs. It enables historical data analysis and helps identify performance bottlenecks, error patterns, and cost trends.

## Features

### 1. Request Metrics Collection

Tracks every HTTP request to the application:
- **Endpoint path** - Which URL was accessed
- **HTTP method** - GET, POST, PUT, DELETE, etc.
- **Status code** - 2xx, 4xx, 5xx
- **Response time** - Latency in milliseconds
- **User ID** - For authenticated requests
- **Timestamp** - When the request occurred

### 2. Performance Analysis

- **Requests Per Second (RPS)** - Calculate traffic volume
- **Latency Percentiles** - p50 (median), p95 for SLA monitoring
- **Endpoint-specific metrics** - Analyze individual API performance
- **Time-windowed queries** - Analyze specific time periods

### 3. Error Tracking

- **Error rates** - Percentage of failed requests
- **Error classification** - Client errors (4xx) vs server errors (5xx)
- **Detailed error logs** - Stack traces and request context
- **Error trends** - Identify recurring issues

### 4. Provider Cost Tracking

- **Daily cost aggregation** - Track spending by provider and service
- **Token usage** - Monitor AI API consumption
- **Monthly summaries** - Budget tracking and forecasting
- **Multi-provider support** - OpenAI, Anthropic, etc.

### 5. Data Retention

- **30-day retention** - Configurable retention period
- **Automated cleanup** - Management command for old data removal
- **Historical summaries** - Daily aggregates preserved longer

## Architecture

### Models

#### RequestMetric
Stores individual request data for detailed analysis.

**Fields:**
- `timestamp` - Request time (indexed)
- `endpoint` - Request path (indexed)
- `method` - HTTP method
- `status_code` - Response status (indexed)
- `response_time_ms` - Latency
- `user_id` - Authenticated user (optional)

**Methods:**
- `calculate_rps()` - Calculate requests per second
- `get_error_rate()` - Calculate error percentage
- `calculate_percentiles()` - Get p50/p95 latency

#### DailyMetricsSummary
Aggregated daily statistics for efficient historical queries.

**Fields:**
- `date` - Summary date (unique)
- `total_requests` - Request count
- `total_errors` - Error count
- `client_errors` - 4xx count
- `server_errors` - 5xx count
- `avg_response_time` - Average latency
- `p50_response_time` - Median latency
- `p95_response_time` - 95th percentile latency
- `max_response_time` - Maximum latency
- `endpoint_stats` - Per-endpoint breakdown (JSON)

**Properties:**
- `error_rate` - Calculated error percentage

#### ProviderCostDaily
Daily provider spending aggregation.

**Fields:**
- `date` - Cost date
- `provider` - Provider name (e.g., "OpenAI")
- `service` - Service name (e.g., "gpt-4o")
- `total_requests` - API call count
- `total_cost_usd` - Total cost in USD
- `total_tokens` - Token usage (AI providers)
- `prompt_tokens` - Input tokens
- `completion_tokens` - Output tokens

**Methods:**
- `get_monthly_cost()` - Aggregate monthly spending

#### ErrorLog
Detailed error tracking with stack traces.

**Fields:**
- `timestamp` - Error time
- `endpoint` - Request path
- `method` - HTTP method
- `status_code` - Error status
- `error_type` - Exception class
- `error_message` - Error description
- `stack_trace` - Full traceback
- `user_id` - User (if authenticated)
- `request_data` - Request context (JSON)

### Middleware

#### MetricsMiddleware
Automatically captures request/response metrics.

**Functionality:**
- Records every request
- Measures response time
- Captures error details
- Non-blocking database writes
- Minimal overhead (< 5ms)
- Graceful error handling

**Usage:**
Add to `MIDDLEWARE` in `settings.py`:
```python
MIDDLEWARE = [
    # ... other middleware ...
    'active_interview_app.middleware.MetricsMiddleware',
    # ... more middleware ...
]
```

#### PerformanceMonitorMiddleware
Logs warnings for slow requests.

**Configuration:**
- Default threshold: 1000ms
- Logs to Django logger

### Management Commands

#### cleanup_old_metrics
Removes metrics older than retention period.

**Usage:**
```bash
# Cleanup with default 30-day retention
python manage.py cleanup_old_metrics

# Custom retention period
python manage.py cleanup_old_metrics --days 60

# Dry run (preview without deleting)
python manage.py cleanup_old_metrics --dry-run
```

**Scheduled Execution:**
Add to cron or task scheduler:
```bash
# Daily at 2 AM
0 2 * * * cd /path/to/project && python manage.py cleanup_old_metrics
```

#### aggregate_daily_metrics
Creates daily summaries from raw metrics.

**Usage:**
```bash
# Aggregate yesterday's metrics
python manage.py aggregate_daily_metrics

# Aggregate specific date
python manage.py aggregate_daily_metrics --date 2025-01-15

# Backfill multiple days
python manage.py aggregate_daily_metrics --backfill-days 7
```

**Scheduled Execution:**
```bash
# Daily at 1 AM (after day completes)
0 1 * * * cd /path/to/project && python manage.py aggregate_daily_metrics
```

## Setup

### 1. Run Migrations

```bash
cd active_interview_backend
python manage.py makemigrations
python manage.py migrate
```

### 2. Enable Middleware

Add to `active_interview_backend/active_interview_backend/settings.py`:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Observability middleware (add these)
    'active_interview_app.middleware.MetricsMiddleware',
    'active_interview_app.middleware.PerformanceMonitorMiddleware',
]
```

### 3. Schedule Cleanup Task

Add to cron (Linux/Mac) or Task Scheduler (Windows):

```bash
# Cleanup old metrics daily at 2 AM
0 2 * * * cd /path/to/active_interview_backend && python manage.py cleanup_old_metrics

# Aggregate metrics daily at 1 AM
0 1 * * * cd /path/to/active_interview_backend && python manage.py aggregate_daily_metrics
```

### 4. Configure Logging (Optional)

Add to `settings.py` for detailed logging:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': 'logs/observability.log',
        },
    },
    'loggers': {
        'active_interview_app.middleware': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}
```

## Usage Examples

### Query Request Metrics

```python
from active_interview_app.observability_models import RequestMetric
from django.utils import timezone
from datetime import timedelta

# Get RPS for last minute
rps = RequestMetric.calculate_rps(
    endpoint='/api/chat/',
    start_time=timezone.now() - timedelta(minutes=1),
    end_time=timezone.now()
)
print(f"RPS: {rps:.2f}")

# Get error rate for last hour
error_stats = RequestMetric.get_error_rate(
    start_time=timezone.now() - timedelta(hours=1),
    end_time=timezone.now()
)
print(f"Error rate: {error_stats['error_rate']:.1f}%")
print(f"4xx errors: {error_stats['client_error_count']}")
print(f"5xx errors: {error_stats['server_error_count']}")

# Get latency percentiles
percentiles = RequestMetric.calculate_percentiles(
    endpoint='/api/chat/',
    start_time=timezone.now() - timedelta(hours=1),
    end_time=timezone.now()
)
print(f"p50: {percentiles['p50']:.2f}ms")
print(f"p95: {percentiles['p95']:.2f}ms")
```

### Query Daily Summaries

```python
from active_interview_app.observability_models import DailyMetricsSummary
from datetime import date, timedelta

# Get yesterday's summary
yesterday = date.today() - timedelta(days=1)
summary = DailyMetricsSummary.objects.get(date=yesterday)

print(f"Requests: {summary.total_requests:,}")
print(f"Errors: {summary.total_errors} ({summary.error_rate:.1f}%)")
print(f"Avg latency: {summary.avg_response_time:.2f}ms")
print(f"p95 latency: {summary.p95_response_time:.2f}ms")

# Get last 7 days
last_week = DailyMetricsSummary.objects.filter(
    date__gte=date.today() - timedelta(days=7)
).order_by('-date')

for day in last_week:
    print(f"{day.date}: {day.total_requests:,} requests, "
          f"{day.error_rate:.1f}% errors")
```

### Query Provider Costs

```python
from active_interview_app.observability_models import ProviderCostDaily

# Get monthly OpenAI cost
from datetime import date
monthly_cost = ProviderCostDaily.get_monthly_cost(
    year=2025,
    month=1,
    provider='OpenAI'
)
print(f"OpenAI January cost: ${monthly_cost:.2f}")

# Get daily breakdown
daily_costs = ProviderCostDaily.objects.filter(
    date__year=2025,
    date__month=1,
    provider='OpenAI'
).order_by('date')

for cost in daily_costs:
    print(f"{cost.date}: {cost.service} - "
          f"{cost.total_requests:,} requests, "
          f"${cost.total_cost_usd:.2f}")
```

### Query Error Logs

```python
from active_interview_app.observability_models import ErrorLog
from datetime import timedelta
from django.utils import timezone

# Get recent 5xx errors
server_errors = ErrorLog.objects.filter(
    status_code__gte=500,
    timestamp__gte=timezone.now() - timedelta(hours=1)
).order_by('-timestamp')

for error in server_errors:
    print(f"{error.timestamp}: {error.error_type} at {error.endpoint}")
    print(f"  Message: {error.error_message}")
    print(f"  Stack: {error.stack_trace[:200]}...")

# Get error frequency by type
from django.db.models import Count

error_types = ErrorLog.objects.filter(
    timestamp__gte=timezone.now() - timedelta(days=1)
).values('error_type').annotate(
    count=Count('id')
).order_by('-count')

for error_type in error_types:
    print(f"{error_type['error_type']}: {error_type['count']} occurrences")
```

## Performance Considerations

### Database Indexes

All time-based queries use indexed fields:
- `RequestMetric.timestamp`
- `RequestMetric.endpoint`
- `RequestMetric.status_code`
- `DailyMetricsSummary.date`
- `ProviderCostDaily.date`
- `ErrorLog.timestamp`

### Middleware Overhead

- **Target:** < 5ms per request
- **Non-blocking:** Database writes don't delay responses
- **Graceful degradation:** Metrics failures don't break app
- **Exception handling:** All errors are caught and logged

### Data Volume Management

**Without cleanup:**
- 100 RPS = 8.6M records/day
- 30 days = 258M records

**With cleanup:**
- 30-day retention limits growth
- Daily summaries provide long-term trends
- Automatic cleanup via management command

### Query Optimization

**Use daily summaries for:**
- Historical trends (> 1 day old)
- Monthly/yearly reports
- Dashboard displays

**Use raw metrics for:**
- Real-time monitoring (< 1 day)
- Detailed debugging
- Specific time windows

## Testing

Run tests with:
```bash
cd active_interview_backend
python manage.py test active_interview_app.tests.test_observability_metrics
```

**Test coverage includes:**
- Model methods and properties
- Middleware request tracking
- Error logging
- Management commands
- Percentile calculations
- Cost aggregation

## Monitoring Recommendations

### Key Metrics to Track

1. **Latency (p95)** - SLA compliance
2. **Error rate** - Service reliability
3. **RPS** - Traffic patterns
4. **Provider costs** - Budget management

### Alert Thresholds

Suggested thresholds for monitoring:
- **p95 latency > 1000ms** - Performance degradation
- **Error rate > 5%** - Service issues
- **5xx errors > 10/min** - Critical system errors
- **Daily cost increase > 50%** - Unexpected usage spike

### Dashboard Queries

Example queries for observability dashboard:

```python
# Last hour summary
from django.utils import timezone
from datetime import timedelta

now = timezone.now()
hour_ago = now - timedelta(hours=1)

metrics = {
    'rps': RequestMetric.calculate_rps(start_time=hour_ago, end_time=now),
    'error_rate': RequestMetric.get_error_rate(start_time=hour_ago, end_time=now),
    'latency': RequestMetric.calculate_percentiles(start_time=hour_ago, end_time=now),
}
```

## Future Enhancements

Potential improvements:
- Real-time alerting integration
- Grafana/Prometheus export
- Custom metric tags
- Distributed tracing support
- API endpoint for metrics access
- Web-based dashboard UI

## Related Documentation

- [Architecture Overview](../architecture/overview.md)
- [Database Models](../architecture/models.md)
- [Testing Guide](../setup/testing.md)
- [Local Development](../setup/local-development.md)

## References

- **Issues:** #14, #15 (Observability Dashboard)
- **BDD Feature:** `features/observability_metrics.feature`
- **Models:** `active_interview_app/observability_models.py`
- **Middleware:** `active_interview_app/middleware.py`
- **Tests:** `active_interview_app/tests/test_observability_metrics.py`

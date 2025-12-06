# Latency Budget for Interview Responses

**Related Issues:** [#20](https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/issues/20), [#54](https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/issues/54)

## Overview

The Latency Budget feature ensures that interview responses maintain fast response times (<2 seconds median) to create a natural, responsive interview experience for candidates. The system tracks, logs, and alerts on response latencies to maintain a 90% compliance rate for sub-2-second responses.

## Key Features

- **Automatic Latency Tracking**: Every interview AI response is automatically tracked
- **Granular Metrics**: Separate tracking for total response time and AI processing time
- **Compliance Monitoring**: Real-time calculation of compliance rates against the 2-second budget
- **Automated Alerts**: Warnings and error logs for responses exceeding thresholds
- **Historical Analysis**: Support for percentile calculations (p50, p90, p95) and trend analysis
- **Per-Interview Statistics**: Session-level compliance tracking and reporting

## Architecture

### Database Model

**`InterviewResponseLatency`** (in `observability_models.py`)

Stores individual response latency metrics with the following key fields:

- `chat` - ForeignKey to the interview Chat session
- `user` - ForeignKey to the User (candidate)
- `response_time_ms` - Total response time in milliseconds
- `ai_processing_time_ms` - OpenAI API call duration specifically
- `question_number` - Sequence number of the question in the interview
- `interview_type` - PRACTICE or INVITED interview
- `exceeded_threshold` - Boolean flag for budget violations
- `threshold_ms` - The configured threshold at time of request (default: 2000ms)
- `timestamp` - When the response was generated

### Latency Tracking Utilities

**Module:** `active_interview_app/latency_utils.py`

#### Core Functions

**`track_interview_response_latency(chat, response_time_ms, ai_processing_time_ms=None, question_number=None)`**
- Records a latency measurement for an interview response
- Automatically checks against threshold and logs violations
- Returns: `InterviewResponseLatency` instance

**`trigger_latency_alert(latency_record)`**
- Triggers alerts for severe latency violations (>5 seconds)
- Creates `ErrorLog` entries for debugging
- Logs detailed error messages

**`check_session_compliance(chat)`**
- Calculates compliance statistics for a specific interview session
- Returns: Dict with compliance rate, pass/fail status, and message

**`get_global_compliance_stats(interview_type=None, hours=24)`**
- Get system-wide latency compliance statistics
- Returns: Dict with compliance rates and percentile metrics

#### Context Managers

**`LatencyTracker`**

Automatically tracks response time and records metrics:

```python
from active_interview_app.latency_utils import LatencyTracker

with LatencyTracker(chat, question_number=1) as tracker:
    # Track specific AI processing time
    with tracker.track_ai_processing():
        response = openai_client.chat.completions.create(...)

    # Process response...
    ai_message = response.choices[0].message.content

# Latency automatically recorded when exiting context
```

**Features:**
- Automatically calculates total response time
- Optionally tracks AI-specific processing time
- Auto-increments question numbers if not provided
- Handles unsaved Chat objects gracefully
- Doesn't suppress exceptions

## Integration Points

### Views with Latency Tracking

1. **`ChatView.post()`** (`views.py:525-580`)
   - Tracks every user question/AI response interaction
   - Primary endpoint for latency budget compliance

2. **`CreateChat.post()`** (`views.py:315-336`)
   - Tracks initial AI greeting (question #0)
   - Only tracked after chat is saved to database

3. **`start_invited_interview()`** (`views.py:3245-3262`)
   - Tracks initial greeting for invited interviews
   - Chat is pre-saved, so tracking always occurs

### Middleware

**`MetricsMiddleware`** (`middleware.py:15-169`)
- Already tracks HTTP-level response times
- Complements interview-specific latency tracking
- Stores data in `RequestMetric` model

## Configuration

### Settings

Add to `settings.py`:

```python
# Interview response latency threshold in milliseconds
INTERVIEW_LATENCY_THRESHOLD_MS = 2000  # Default: 2000 (2 seconds)
```

### Threshold Customization

The latency threshold can be configured globally via settings or overridden per request:

```python
from active_interview_app.latency_utils import track_interview_response_latency

# Use custom threshold
latency_record = track_interview_response_latency(
    chat=chat,
    response_time_ms=response_time,
    threshold_ms=3000  # Custom 3-second threshold
)
```

## Usage Examples

### Check Interview Session Compliance

```python
from active_interview_app.latency_utils import check_session_compliance

# Get compliance stats for a specific interview
stats = check_session_compliance(chat)

print(stats['message'])
# Output: "Session latency: 92.3% within budget (12/13 responses). Target: 90%. Status: ✓ PASS"

if stats['meets_target']:
    print("Interview met latency budget requirements!")
```

### Analyze Global Compliance

```python
from active_interview_app.latency_utils import get_global_compliance_stats

# Get last 24 hours of data
stats = get_global_compliance_stats(hours=24)

print(f"Compliance Rate: {stats['compliance_rate']:.1f}%")
print(f"p50 Latency: {stats['p50']:.0f}ms")
print(f"p95 Latency: {stats['p95']:.0f}ms")

# Filter by interview type
practice_stats = get_global_compliance_stats(interview_type='PRACTICE', hours=24)
invited_stats = get_global_compliance_stats(interview_type='INVITED', hours=24)
```

### Query Session Statistics

```python
from active_interview_app.observability_models import InterviewResponseLatency

# Get detailed statistics for a session
stats = InterviewResponseLatency.get_session_stats(chat_id=123)

print(f"Total Responses: {stats['total_responses']}")
print(f"Within Budget: {stats['within_budget']}")
print(f"Exceeded Budget: {stats['exceeded_budget']}")
print(f"Compliance Rate: {stats['budget_compliance_rate']:.1f}%")
print(f"Median Latency (p50): {stats['p50']:.0f}ms")
print(f"p95 Latency: {stats['p95']:.0f}ms")
```

### Calculate Compliance Rate for Time Window

```python
from django.utils import timezone
from datetime import timedelta
from active_interview_app.observability_models import InterviewResponseLatency

# Last hour
end_time = timezone.now()
start_time = end_time - timedelta(hours=1)

compliance = InterviewResponseLatency.calculate_compliance_rate(
    interview_type='PRACTICE',
    start_time=start_time,
    end_time=end_time
)

if compliance['meets_target']:
    print(f"✓ Meeting target: {compliance['compliance_rate']:.1f}% >= 90%")
else:
    print(f"✗ Below target: {compliance['compliance_rate']:.1f}% < 90%")
```

## Monitoring & Alerts

### Logging Levels

**WARNING** - Latency threshold exceeded (>2000ms):
```
Latency budget exceeded: 2500ms > 2000ms (Chat #123, Q5, User: john.doe)
```

**ERROR** - Severe latency violation (>5000ms):
```
SEVERE LATENCY VIOLATION: 6000ms (Chat #123, Q5, User: john.doe)
```

### Error Log Entries

Severe violations (>5 seconds) automatically create `ErrorLog` entries:

```python
from active_interview_app.observability_models import ErrorLog

# Query latency violation logs
violations = ErrorLog.objects.filter(error_type='LatencyViolation')

for log in violations:
    print(f"{log.timestamp}: {log.error_message}")
    print(f"  Chat ID: {log.request_data['chat_id']}")
    print(f"  Response Time: {log.request_data['response_time_ms']}ms")
```

### Dashboard Integration

The latency data integrates with the existing observability dashboard (Issues #14, #15):

- View latency trends over time
- Compare PRACTICE vs INVITED interview performance
- Track compliance rates by time period
- Identify slow response patterns

## Acceptance Criteria Met

✅ **Issue #20**: Audio Q&A session with 10 questions
- System tracks latency for each response
- Calculates 90% compliance rate
- Logs all response times

✅ **Issue #54**: Fast interview responses
- 90% of responses delivered in <2 seconds (tracked)
- Each response latency logged with timestamp
- Automated alerts when latency exceeds threshold

## Testing

### Test Coverage

Comprehensive test suite in `tests/test_latency_tracking.py`:

- **24 test cases** covering all functionality
- **96% coverage** for `latency_utils.py`
- Model methods (session stats, compliance rates, percentiles)
- Context manager behavior (LatencyTracker)
- Integration with views
- Alert triggering
- Edge cases (unsaved chats, exceptions)

### Running Tests

```bash
# Run latency tracking tests
cd active_interview_backend
python manage.py test active_interview_app.tests.test_latency_tracking

# Run with coverage
coverage run manage.py test active_interview_app.tests.test_latency_tracking
coverage report -m --include='active_interview_app/latency_utils.py'
```

## Performance Impact

- **Minimal overhead**: Latency tracking adds <5ms per request
- **Non-blocking**: Database writes occur within request context
- **Indexed queries**: Optimized database indexes for fast queries
- **Efficient calculations**: Percentile calculations use Python statistics library

## Related Features

- [Observability Dashboard](../docs/architecture/overview.md#observability) (Issues #14, #15)
- [Invited Interviews](./invitation-workflow.md) (Issue #138)
- [Request Metrics](../architecture/overview.md#metrics-tracking)

## Future Enhancements

Potential improvements for future iterations:

1. **Adaptive Thresholds**: Adjust thresholds based on interview type or user tier
2. **Real-time Dashboards**: Live monitoring of latency metrics
3. **Predictive Alerts**: ML-based prediction of potential slowdowns
4. **Auto-scaling Integration**: Trigger infrastructure scaling on high latency
5. **Client-side Tracking**: Measure end-to-end latency including network time
6. **Percentile-based SLOs**: Track compliance against p95/p99 instead of median

## API Reference

See [InterviewResponseLatency Model](../architecture/models.md#interviewresponselatency) for complete API documentation.

## Troubleshooting

### High Latency Issues

If experiencing consistent latency threshold violations:

1. **Check OpenAI API Status**: Verify third-party service health
2. **Review Database Performance**: Query execution times
3. **Analyze Network Latency**: Connection to OpenAI servers
4. **Check System Load**: CPU/memory utilization
5. **Review Prompt Complexity**: Large prompts increase processing time

### Query Latency Data

```python
# Find all slow responses in last hour
from django.utils import timezone
from datetime import timedelta
from active_interview_app.observability_models import InterviewResponseLatency

slow_responses = InterviewResponseLatency.objects.filter(
    exceeded_threshold=True,
    timestamp__gte=timezone.now() - timedelta(hours=1)
).order_by('-response_time_ms')

for response in slow_responses:
    print(f"{response.chat_id} - Q{response.question_number}: {response.response_time_ms:.0f}ms")
```

## Migration

The latency tracking feature requires running database migrations:

```bash
cd active_interview_backend
python manage.py makemigrations
python manage.py migrate
```

This creates the `InterviewResponseLatency` table with appropriate indexes.

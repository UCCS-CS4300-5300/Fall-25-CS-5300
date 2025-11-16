# Observability Dashboard

**Related Issues:** #14, #15

## Overview

The Observability Dashboard provides real-time system health monitoring and metrics visualization for SREs and administrators. It displays key performance indicators (KPIs) including request rates, latency, error rates, and provider costs.

## Features

### Metrics Displayed

1. **Requests Per Second (RPS)**
   - Real-time request throughput
   - Line chart showing traffic patterns over time
   - Average RPS summary statistic

2. **Latency (p50/p95)**
   - Response time percentiles
   - Dual-line chart showing p50 and p95 latency
   - Helps identify performance degradation

3. **Error Rate**
   - Percentage of failed requests (4xx/5xx)
   - Line chart with error rate over time
   - Average error rate summary statistic

4. **Provider Costs**
   - Daily costs by AI provider (OpenAI, Anthropic)
   - Bar chart with breakdown by service (gpt-4o, claude-sonnet-4, etc.)
   - Total cost summary statistic

### Time Range Selection

Users can view metrics across different time windows:
- **1 Hour:** 1-minute granularity, recent traffic
- **24 Hours:** 5-minute granularity, daily patterns
- **7 Days:** 1-hour granularity, weekly trends
- **30 Days:** 6-hour granularity, monthly overview

### Auto-Refresh

- Click "Auto-refresh" to enable automatic data updates every 30 seconds
- Useful for monitoring live systems
- Click again to pause auto-refresh

### Export Capabilities

Export metrics data as CSV for:
- External analysis
- Reporting
- Archival

The export includes:
- Timestamps
- RPS values
- p50/p95 latency
- Error rates
- Provider costs

### Sharing

Generate a shareable URL with:
- Current time range selection
- Direct access to dashboard view
- Useful for incident communication

## Access

**URL:** `/admin/observability/`

**Requirements:**
- Must be logged in
- Must have staff status (`is_staff=True`)

## Technical Architecture

### Backend Components

**Views:** `active_interview_app/observability_views.py`
- `observability_dashboard` - Main dashboard view
- `api_metrics_rps` - RPS data endpoint
- `api_metrics_latency` - Latency data endpoint
- `api_metrics_errors` - Error rate data endpoint
- `api_metrics_costs` - Cost data endpoint
- `api_export_metrics` - CSV export endpoint

**Models:** `active_interview_app/observability_models.py`
- `RequestMetric` - Individual request tracking
- `DailyMetricsSummary` - Aggregated daily metrics
- `ProviderCostDaily` - Daily provider costs
- `ErrorLog` - Detailed error logging

**URL Routing:** `active_interview_app/urls.py`
- Dashboard and API endpoints registered with `/admin/observability/` prefix

### Frontend Components

**Template:** `templates/admin/observability_dashboard.html`
- Responsive grid layout
- Bootstrap 5 styling
- Chart.js integration
- Theme-aware colors

**JavaScript:** `static/js/observability_dashboard.js`
- Chart initialization and rendering
- API data fetching
- Time range filtering
- Auto-refresh logic
- Export and share functionality

### Data Flow

1. User accesses dashboard at `/admin/observability/`
2. JavaScript loads and initializes Chart.js charts
3. Parallel API calls fetch metrics for current time range:
   - `/admin/observability/api/metrics/rps/`
   - `/admin/observability/api/metrics/latency/`
   - `/admin/observability/api/metrics/errors/`
   - `/admin/observability/api/metrics/costs/`
4. Charts update with new data
5. Summary statistics calculated and displayed
6. Auto-refresh (if enabled) repeats every 30 seconds

## API Endpoints

### GET /admin/observability/api/metrics/rps/

Returns requests per second data.

**Query Parameters:**
- `time_range` (optional): `1h`, `24h`, `7d`, `30d` (default: `24h`)
- `endpoint` (optional): Filter by specific endpoint path

**Response:**
```json
{
  "metric": "rps",
  "time_range": "24h",
  "endpoint": null,
  "data": [
    {
      "timestamp": "2025-11-16T10:00:00+00:00",
      "value": 12.345
    },
    ...
  ]
}
```

### GET /admin/observability/api/metrics/latency/

Returns latency percentile data.

**Query Parameters:**
- `time_range` (optional): `1h`, `24h`, `7d`, `30d`
- `endpoint` (optional): Filter by specific endpoint

**Response:**
```json
{
  "metric": "latency",
  "time_range": "24h",
  "endpoint": null,
  "data": [
    {
      "timestamp": "2025-11-16T10:00:00+00:00",
      "p50": 45.23,
      "p95": 125.67,
      "mean": 67.89
    },
    ...
  ]
}
```

### GET /admin/observability/api/metrics/errors/

Returns error rate data.

**Query Parameters:**
- `time_range` (optional): `1h`, `24h`, `7d`, `30d`
- `endpoint` (optional): Filter by specific endpoint

**Response:**
```json
{
  "metric": "error_rate",
  "time_range": "24h",
  "endpoint": null,
  "data": [
    {
      "timestamp": "2025-11-16T10:00:00+00:00",
      "error_rate": 2.5,
      "total_requests": 1000,
      "error_count": 25
    },
    ...
  ]
}
```

### GET /admin/observability/api/metrics/costs/

Returns provider cost data.

**Query Parameters:**
- `time_range` (optional): `1h`, `24h`, `7d`, `30d`
- `provider` (optional): Filter by provider (e.g., "OpenAI")

**Response:**
```json
{
  "metric": "costs",
  "time_range": "24h",
  "provider": null,
  "data": [
    {
      "date": "2025-11-16",
      "total_cost": 45.67,
      "by_service": {
        "OpenAI/gpt-4o": 35.50,
        "OpenAI/gpt-3.5-turbo": 10.17
      }
    },
    ...
  ]
}
```

### GET /admin/observability/api/export/

Exports metrics as CSV file.

**Query Parameters:**
- `time_range` (optional): `1h`, `24h`, `7d`, `30d`
- `metrics` (optional): Comma-separated list (e.g., "rps,latency,errors,costs")

**Response:** CSV file download

## Usage Examples

### Viewing Dashboard

1. Log in as staff user
2. Navigate to `/admin/observability/`
3. Select desired time range (default: 24 hours)
4. View charts and summary statistics

### Monitoring Live Traffic

1. Open dashboard
2. Select "1 Hour" time range for recent data
3. Click "Auto-refresh" to enable live updates
4. Monitor RPS and error rate charts

### Investigating Performance Issues

1. Select "7 Days" or "30 Days" time range
2. Look for spikes in p95 latency chart
3. Correlate with error rate chart
4. Check if cost increases correlate with issues

### Exporting Data for Reports

1. Select desired time range
2. Click "Export" button
3. CSV file downloads with all metrics
4. Use in spreadsheets or external tools

### Sharing Dashboard with Team

1. Select time range of interest
2. Click "Share" button
3. Copy generated URL
4. Share with team members (requires staff access)

## Performance Considerations

- Dashboard data refreshes are throttled to prevent excessive database queries
- Time buckets are automatically adjusted based on time range:
  - 1h: 1-minute buckets
  - 24h: 5-minute buckets
  - 7d: 1-hour buckets
  - 30d: 6-hour buckets
- Auto-refresh interval is 30 seconds (not configurable)
- API endpoints are staff-only to prevent unauthorized access

## Testing

Comprehensive tests are available in `tests/test_observability_dashboard.py`:

- Dashboard view access control
- API endpoint authentication
- JSON response structure validation
- CSV export functionality
- Time range filtering
- Data accuracy

Run tests:
```bash
python manage.py test active_interview_app.tests.test_observability_dashboard
```

## Future Enhancements

Potential improvements for future iterations:

1. **Alerting**
   - Configurable thresholds for RPS, latency, errors
   - Email/Slack notifications when thresholds exceeded

2. **Custom Time Ranges**
   - User-defined date range picker
   - "Last N hours/days" selector

3. **Endpoint Filtering**
   - Dropdown to filter by specific endpoints
   - Compare multiple endpoints side-by-side

4. **Historical Comparisons**
   - Compare current metrics to previous time periods
   - "Week over week" or "Month over month" views

5. **Anomaly Detection**
   - Automatic detection of unusual patterns
   - Highlight anomalies on charts

6. **Dashboard Customization**
   - User-configurable chart layouts
   - Save custom dashboard configurations

7. **Mobile Responsiveness**
   - Optimize for mobile viewing
   - Touch-friendly controls

## Troubleshooting

### Dashboard shows "No data"

**Cause:** No metrics have been recorded yet

**Solution:**
1. Ensure `MetricsMiddleware` is enabled in `settings.py`
2. Generate some traffic to the application
3. Wait a few minutes for data to accumulate
4. Refresh dashboard

### Charts not loading

**Cause:** JavaScript errors or missing Chart.js library

**Solution:**
1. Check browser console for errors
2. Ensure Chart.js CDN is accessible
3. Verify `observability_dashboard.js` is loaded correctly
4. Check network tab for failed API requests

### Export returns empty CSV

**Cause:** No data in selected time range

**Solution:**
1. Verify metrics exist for the selected time range
2. Try a different time range
3. Check if `RequestMetric` table has data

### Permission denied errors

**Cause:** User is not staff

**Solution:**
1. Log in with staff account
2. Or grant `is_staff=True` to user in Django admin

## Related Documentation

- [Architecture Overview](../architecture/overview.md)
- [Observability Models](../architecture/models.md#observability-models)
- [Testing Guide](../setup/testing.md)
- [AGENTS.md](../../AGENTS.md) - Test logging requirements

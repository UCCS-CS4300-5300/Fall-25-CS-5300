"""
Observability dashboard views for system monitoring and metrics visualization.

Related to Issues #14, #15 (Observability Dashboard).
"""
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Avg, Sum
from datetime import timedelta
from decimal import Decimal

from .observability_models import (
    RequestMetric,
    DailyMetricsSummary,
    ProviderCostDaily,
    ErrorLog
)


@staff_member_required
def observability_dashboard(request):
    """
    Main observability dashboard view.

    Displays system health metrics including:
    - RPS (Requests Per Second)
    - Latency (p50/p95)
    - Error rates
    - Provider costs

    Accessible at /observability/
    """
    context = {
        'title': 'Observability Dashboard',
        'available_time_ranges': [
            ('1h', '1 Hour'),
            ('24h', '24 Hours'),
            ('7d', '7 Days'),
            ('30d', '30 Days'),
        ]
    }
    return render(request, 'admin/observability_dashboard.html', context)


@staff_member_required
def api_metrics_rps(request):
    """
    API endpoint for RPS (Requests Per Second) data.

    Query params:
        time_range: 1h, 24h, 7d, 30d (default: 24h)
        endpoint: Optional filter by specific endpoint

    Returns:
        JSON with timestamps and RPS values
    """
    time_range = request.GET.get('time_range', '24h')
    endpoint = request.GET.get('endpoint', None)

    # Parse time range
    end_time = timezone.now()
    if time_range == '1h':
        start_time = end_time - timedelta(hours=1)
        bucket_minutes = 1  # 1-minute buckets
    elif time_range == '7d':
        start_time = end_time - timedelta(days=7)
        bucket_minutes = 60  # 1-hour buckets
    elif time_range == '30d':
        start_time = end_time - timedelta(days=30)
        bucket_minutes = 360  # 6-hour buckets
    else:  # 24h default
        start_time = end_time - timedelta(hours=24)
        bucket_minutes = 5  # 5-minute buckets

    # Calculate RPS for each time bucket
    data_points = []
    current_time = start_time

    while current_time < end_time:
        bucket_end = current_time + timedelta(minutes=bucket_minutes)

        # Count requests in this bucket
        queryset = RequestMetric.objects.filter(
            timestamp__gte=current_time,
            timestamp__lt=bucket_end
        )
        if endpoint:
            queryset = queryset.filter(endpoint=endpoint)

        count = queryset.count()
        rps = count / (bucket_minutes * 60) if bucket_minutes > 0 else count

        data_points.append({
            'timestamp': current_time.isoformat(),
            'value': round(rps, 3)
        })

        current_time = bucket_end

    return JsonResponse({
        'metric': 'rps',
        'time_range': time_range,
        'endpoint': endpoint,
        'data': data_points
    })


@staff_member_required
def api_metrics_latency(request):
    """
    API endpoint for latency (p50/p95) data.

    Query params:
        time_range: 1h, 24h, 7d, 30d (default: 24h)
        endpoint: Optional filter by specific endpoint

    Returns:
        JSON with timestamps, p50, and p95 values
    """
    time_range = request.GET.get('time_range', '24h')
    endpoint = request.GET.get('endpoint', None)

    # Parse time range
    end_time = timezone.now()
    if time_range == '1h':
        start_time = end_time - timedelta(hours=1)
        bucket_minutes = 1
    elif time_range == '7d':
        start_time = end_time - timedelta(days=7)
        bucket_minutes = 60
    elif time_range == '30d':
        start_time = end_time - timedelta(days=30)
        bucket_minutes = 360
    else:  # 24h
        start_time = end_time - timedelta(hours=24)
        bucket_minutes = 5

    # Calculate percentiles for each time bucket
    data_points = []
    current_time = start_time

    while current_time < end_time:
        bucket_end = current_time + timedelta(minutes=bucket_minutes)

        percentiles = RequestMetric.calculate_percentiles(
            endpoint=endpoint,
            start_time=current_time,
            end_time=bucket_end
        )

        data_points.append({
            'timestamp': current_time.isoformat(),
            'p50': round(percentiles['p50'], 2),
            'p95': round(percentiles['p95'], 2),
            'mean': round(percentiles['mean'], 2)
        })

        current_time = bucket_end

    return JsonResponse({
        'metric': 'latency',
        'time_range': time_range,
        'endpoint': endpoint,
        'data': data_points
    })


@staff_member_required
def api_metrics_errors(request):
    """
    API endpoint for error rate data.

    Query params:
        time_range: 1h, 24h, 7d, 30d (default: 24h)
        endpoint: Optional filter by specific endpoint

    Returns:
        JSON with timestamps and error rate percentages
    """
    time_range = request.GET.get('time_range', '24h')
    endpoint = request.GET.get('endpoint', None)

    # Parse time range
    end_time = timezone.now()
    if time_range == '1h':
        start_time = end_time - timedelta(hours=1)
        bucket_minutes = 1
    elif time_range == '7d':
        start_time = end_time - timedelta(days=7)
        bucket_minutes = 60
    elif time_range == '30d':
        start_time = end_time - timedelta(days=30)
        bucket_minutes = 360
    else:  # 24h
        start_time = end_time - timedelta(hours=24)
        bucket_minutes = 5

    # Calculate error rate for each time bucket
    data_points = []
    current_time = start_time

    while current_time < end_time:
        bucket_end = current_time + timedelta(minutes=bucket_minutes)

        error_stats = RequestMetric.get_error_rate(
            endpoint=endpoint,
            start_time=current_time,
            end_time=bucket_end
        )

        data_points.append({
            'timestamp': current_time.isoformat(),
            'error_rate': round(error_stats['error_rate'], 2),
            'total_requests': error_stats['total_requests'],
            'error_count': error_stats['error_count']
        })

        current_time = bucket_end

    return JsonResponse({
        'metric': 'error_rate',
        'time_range': time_range,
        'endpoint': endpoint,
        'data': data_points
    })


@staff_member_required
def api_metrics_costs(request):
    """
    API endpoint for provider cost data.

    Query params:
        time_range: 1h, 24h, 7d, 30d (default: 24h)
        provider: Optional filter by provider

    Returns:
        JSON with daily costs broken down by service
    """
    time_range = request.GET.get('time_range', '24h')
    provider = request.GET.get('provider', None)

    # Parse time range
    end_time = timezone.now()
    if time_range == '1h':
        start_time = end_time - timedelta(hours=1)
    elif time_range == '7d':
        start_time = end_time - timedelta(days=7)
    elif time_range == '30d':
        start_time = end_time - timedelta(days=30)
    else:  # 24h
        start_time = end_time - timedelta(hours=24)

    # Query provider costs
    queryset = ProviderCostDaily.objects.filter(
        date__gte=start_time.date(),
        date__lte=end_time.date()
    )
    if provider:
        queryset = queryset.filter(provider=provider)

    # Group by date and service
    costs_by_date = {}
    for cost in queryset:
        date_str = cost.date.isoformat()
        if date_str not in costs_by_date:
            costs_by_date[date_str] = {
                'total': Decimal('0.0'),
                'by_service': {}
            }

        service_key = f"{cost.provider}/{cost.service}"
        costs_by_date[date_str]['by_service'][service_key] = float(cost.total_cost_usd)
        costs_by_date[date_str]['total'] += cost.total_cost_usd

    # Format for charts
    data_points = []
    for date_str in sorted(costs_by_date.keys()):
        data_points.append({
            'date': date_str,
            'total_cost': float(costs_by_date[date_str]['total']),
            'by_service': costs_by_date[date_str]['by_service']
        })

    return JsonResponse({
        'metric': 'costs',
        'time_range': time_range,
        'provider': provider,
        'data': data_points
    })


@staff_member_required
def api_export_metrics(request):
    """
    Export metrics data as CSV.

    Query params:
        time_range: 1h, 24h, 7d, 30d (default: 24h)
        metrics: Comma-separated list (rps,latency,errors,costs)

    Returns:
        CSV file download
    """
    import csv
    from django.http import HttpResponse

    time_range = request.GET.get('time_range', '24h')
    metrics = request.GET.get('metrics', 'rps,latency,errors').split(',')

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="metrics_{time_range}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    writer = csv.writer(response)

    # Write header
    headers = ['timestamp']
    if 'rps' in metrics:
        headers.append('rps')
    if 'latency' in metrics:
        headers.extend(['p50_latency', 'p95_latency'])
    if 'errors' in metrics:
        headers.extend(['error_rate', 'error_count'])
    if 'costs' in metrics:
        headers.append('total_cost')

    writer.writerow(headers)

    # Parse time range
    end_time = timezone.now()
    if time_range == '1h':
        start_time = end_time - timedelta(hours=1)
    elif time_range == '7d':
        start_time = end_time - timedelta(days=7)
    elif time_range == '30d':
        start_time = end_time - timedelta(days=30)
    else:
        start_time = end_time - timedelta(hours=24)

    # Collect data points
    # For simplicity, use 5-minute buckets
    bucket_minutes = 5
    current_time = start_time

    while current_time < end_time:
        bucket_end = current_time + timedelta(minutes=bucket_minutes)
        row = [current_time.isoformat()]

        if 'rps' in metrics:
            count = RequestMetric.objects.filter(
                timestamp__gte=current_time,
                timestamp__lt=bucket_end
            ).count()
            rps = count / (bucket_minutes * 60)
            row.append(round(rps, 3))

        if 'latency' in metrics:
            percentiles = RequestMetric.calculate_percentiles(
                start_time=current_time,
                end_time=bucket_end
            )
            row.extend([
                round(percentiles['p50'], 2),
                round(percentiles['p95'], 2)
            ])

        if 'errors' in metrics:
            error_stats = RequestMetric.get_error_rate(
                start_time=current_time,
                end_time=bucket_end
            )
            row.extend([
                round(error_stats['error_rate'], 2),
                error_stats['error_count']
            ])

        if 'costs' in metrics:
            costs = ProviderCostDaily.objects.filter(
                date=current_time.date()
            ).aggregate(total=Sum('total_cost_usd'))['total'] or Decimal('0.0')
            row.append(float(costs))

        writer.writerow(row)
        current_time = bucket_end

    return response

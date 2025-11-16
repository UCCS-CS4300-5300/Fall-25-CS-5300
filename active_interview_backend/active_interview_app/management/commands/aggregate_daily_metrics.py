"""
Management command to aggregate daily metrics from raw request data.
Creates DailyMetricsSummary and ProviderCostDaily records.

Related to Issues #14, #15 (Observability Dashboard).

Usage:
    python manage.py aggregate_daily_metrics
    python manage.py aggregate_daily_metrics --date 2025-01-15
    python manage.py aggregate_daily_metrics --backfill-days 7
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Avg, Max, Sum
from datetime import datetime, timedelta
from decimal import Decimal

from active_interview_app.observability_models import (
    RequestMetric,
    DailyMetricsSummary,
    ProviderCostDaily
)
from active_interview_app.token_usage_models import TokenUsage


class Command(BaseCommand):
    help = 'Aggregate daily metrics from raw request data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Specific date to aggregate (YYYY-MM-DD). Default: yesterday'
        )
        parser.add_argument(
            '--backfill-days',
            type=int,
            help='Number of days to backfill from today'
        )

    def handle(self, *args, **options):
        # Determine which dates to process
        if options.get('backfill_days'):
            # Backfill multiple days
            days_to_process = []
            for i in range(options['backfill_days'], 0, -1):
                date = (timezone.now() - timedelta(days=i)).date()
                days_to_process.append(date)
        elif options.get('date'):
            # Specific date
            date = datetime.strptime(options['date'], '%Y-%m-%d').date()
            days_to_process = [date]
        else:
            # Default: yesterday
            date = (timezone.now() - timedelta(days=1)).date()
            days_to_process = [date]

        self.stdout.write(
            self.style.WARNING(
                f"\nAggregating metrics for {len(days_to_process)} day(s)...\n"
            )
        )

        for date in days_to_process:
            self.aggregate_request_metrics(date)
            self.aggregate_provider_costs(date)

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Successfully aggregated metrics for {len(days_to_process)} day(s)\n"
            )
        )

    def aggregate_request_metrics(self, date):
        """
        Aggregate request metrics for a specific date.

        Args:
            date: Date object to aggregate
        """
        self.stdout.write(f"\nProcessing request metrics for {date}...")

        # Get all requests for this date using date filtering
        # This works correctly with both timezone-aware and naive datetimes
        requests = RequestMetric.objects.filter(
            timestamp__date=date
        )

        total_requests = requests.count()

        if total_requests == 0:
            self.stdout.write(
                self.style.WARNING(
                    f"  No requests found for {date}, skipping..."
                )
            )
            return

        # Calculate aggregate statistics
        errors = requests.filter(status_code__gte=400)
        client_errors = requests.filter(status_code__gte=400, status_code__lt=500)
        server_errors = requests.filter(status_code__gte=500)

        # Calculate latency statistics
        latency_stats = requests.aggregate(
            avg=Avg('response_time_ms'),
            max=Max('response_time_ms')
        )

        # Calculate percentiles (p50, p95)
        response_times = sorted(
            requests.values_list('response_time_ms', flat=True)
        )
        p50_index = int(len(response_times) * 0.50)
        p95_index = int(len(response_times) * 0.95)
        p50 = response_times[p50_index] if response_times else 0.0
        p95 = response_times[p95_index] if response_times else 0.0

        # Calculate per-endpoint statistics
        endpoint_stats = {}
        endpoints = requests.values('endpoint').distinct()

        for endpoint_dict in endpoints:
            endpoint = endpoint_dict['endpoint']
            endpoint_requests = requests.filter(endpoint=endpoint)
            endpoint_errors = endpoint_requests.filter(status_code__gte=400)

            endpoint_latency = endpoint_requests.aggregate(
                avg=Avg('response_time_ms')
            )

            endpoint_stats[endpoint] = {
                'requests': endpoint_requests.count(),
                'errors': endpoint_errors.count(),
                'avg_latency': float(endpoint_latency['avg'] or 0.0)
            }

        # Create or update DailyMetricsSummary
        summary, created = DailyMetricsSummary.objects.update_or_create(
            date=date,
            defaults={
                'total_requests': total_requests,
                'total_errors': errors.count(),
                'client_errors': client_errors.count(),
                'server_errors': server_errors.count(),
                'avg_response_time': float(latency_stats['avg'] or 0.0),
                'p50_response_time': float(p50),
                'p95_response_time': float(p95),
                'max_response_time': float(latency_stats['max'] or 0.0),
                'endpoint_stats': endpoint_stats
            }
        )

        action = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"  ✓ {action} DailyMetricsSummary: "
                f"{total_requests:,} requests, {errors.count()} errors, "
                f"p50={p50:.2f}ms, p95={p95:.2f}ms"
            )
        )

    def aggregate_provider_costs(self, date):
        """
        Aggregate provider costs for a specific date.

        Args:
            date: Date object to aggregate
        """
        self.stdout.write(f"\nProcessing provider costs for {date}...")

        # Get all token usage for this date using date filtering
        # This works correctly with both timezone-aware and naive datetimes
        token_records = TokenUsage.objects.filter(
            created_at__date=date
        )

        if not token_records.exists():
            self.stdout.write(
                self.style.WARNING(
                    f"  No token usage found for {date}, skipping..."
                )
            )
            return

        # Group by model
        models = token_records.values('model_name').distinct()

        for model_dict in models:
            model_name = model_dict['model_name']
            model_records = token_records.filter(model_name=model_name)

            # Determine provider
            if 'gpt' in model_name.lower():
                provider = 'OpenAI'
            elif 'claude' in model_name.lower():
                provider = 'Anthropic'
            else:
                provider = 'Unknown'

            # Aggregate token usage and costs
            total_requests = model_records.count()
            total_prompt_tokens = model_records.aggregate(
                sum=Sum('prompt_tokens')
            )['sum'] or 0
            total_completion_tokens = model_records.aggregate(
                sum=Sum('completion_tokens')
            )['sum'] or 0
            total_tokens = total_prompt_tokens + total_completion_tokens

            # Calculate total cost
            total_cost = Decimal('0.0')
            for record in model_records:
                total_cost += Decimal(str(record.estimated_cost))

            # Create or update ProviderCostDaily
            cost_summary, created = ProviderCostDaily.objects.update_or_create(
                date=date,
                provider=provider,
                service=model_name,
                defaults={
                    'total_requests': total_requests,
                    'total_cost_usd': total_cost,
                    'total_tokens': total_tokens,
                    'prompt_tokens': total_prompt_tokens,
                    'completion_tokens': total_completion_tokens
                }
            )

            action = "Created" if created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✓ {action} ProviderCostDaily: "
                    f"{provider}/{model_name} - "
                    f"{total_requests:,} requests, "
                    f"{total_tokens:,} tokens, "
                    f"${total_cost:.4f}"
                )
            )

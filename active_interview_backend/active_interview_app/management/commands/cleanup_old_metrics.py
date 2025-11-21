"""
Management command to clean up old metrics data.
Retains data for the configured retention period (default: 30 days).

Related to Issues #14, #15 (Observability Dashboard).

Usage:
    python manage.py cleanup_old_metrics
    python manage.py cleanup_old_metrics --days 60
    python manage.py cleanup_old_metrics --dry-run
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from active_interview_app.observability_models import (
    RequestMetric,
    DailyMetricsSummary,
    ProviderCostDaily,
    ErrorLog
)


class Command(BaseCommand):
    help = 'Clean up old observability metrics data (default: keep last 30 days)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to retain (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        retention_days = options['days']
        dry_run = options['dry_run']

        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=retention_days)

        self.stdout.write(
            self.style.WARNING(
                f"\n{'DRY RUN: ' if dry_run else ''}"
                f"Cleaning up metrics older than {retention_days} days "
                f"(before {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')})\n"
            )
        )

        # Track totals
        total_deleted = 0

        # Clean up RequestMetric records
        request_metrics = RequestMetric.objects.filter(
            timestamp__lt=cutoff_date
        )
        request_count = request_metrics.count()
        self.stdout.write(
            f"  RequestMetric: {request_count:,} records to delete"
        )
        if not dry_run and request_count > 0:
            deleted = request_metrics.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f"    ✓ Deleted {deleted[0]:,} RequestMetric records"
                )
            )
            total_deleted += deleted[0]

        # Clean up ErrorLog records
        error_logs = ErrorLog.objects.filter(
            timestamp__lt=cutoff_date
        )
        error_count = error_logs.count()
        self.stdout.write(
            f"  ErrorLog: {error_count:,} records to delete"
        )
        if not dry_run and error_count > 0:
            deleted = error_logs.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f"    ✓ Deleted {deleted[0]:,} ErrorLog records"
                )
            )
            total_deleted += deleted[0]

        # Clean up DailyMetricsSummary records (use date field)
        daily_summaries = DailyMetricsSummary.objects.filter(
            date__lt=cutoff_date.date()
        )
        daily_count = daily_summaries.count()
        self.stdout.write(
            f"  DailyMetricsSummary: {daily_count:,} records to delete"
        )
        if not dry_run and daily_count > 0:
            deleted = daily_summaries.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f"    ✓ Deleted {deleted[0]:,} DailyMetricsSummary records"
                )
            )
            total_deleted += deleted[0]

        # Clean up ProviderCostDaily records (use date field)
        provider_costs = ProviderCostDaily.objects.filter(
            date__lt=cutoff_date.date()
        )
        cost_count = provider_costs.count()
        self.stdout.write(
            f"  ProviderCostDaily: {cost_count:,} records to delete"
        )
        if not dry_run and cost_count > 0:
            deleted = provider_costs.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f"    ✓ Deleted {deleted[0]:,} ProviderCostDaily records"
                )
            )
            total_deleted += deleted[0]

        # Summary
        self.stdout.write("\n" + "=" * 60)
        if dry_run:
            total_to_delete = request_count + error_count + daily_count + cost_count
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: Would delete {total_to_delete:,} total records"
                )
            )
            self.stdout.write(
                "Run without --dry-run to actually delete the records.\n"
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Successfully deleted {total_deleted:,} total records\n"
                )
            )

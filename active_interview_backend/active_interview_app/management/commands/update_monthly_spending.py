"""
Management command to update monthly spending from TokenUsage records.

Related to Issue #11 (Track Monthly Spending).

This command recalculates monthly spending totals from TokenUsage records.
Useful for:
- Initial setup when adding spending tracking to existing system
- Correcting spending totals if they get out of sync
- Backfilling historical data

Usage:
    python manage.py update_monthly_spending
    python manage.py update_monthly_spending --month 2025-11
    python manage.py update_monthly_spending --all
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from active_interview_app.spending_tracker_models import MonthlySpending
from datetime import datetime


class Command(BaseCommand):
    help = 'Update monthly spending totals from TokenUsage records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--month',
            type=str,
            default=None,
            help='Specific month to update in YYYY-MM format (e.g., 2025-11)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Update all existing monthly spending records'
        )

    def handle(self, *args, **options):
        month_str = options.get('month')
        update_all = options.get('all', False)

        if month_str:
            # Update specific month
            try:
                year, month = map(int, month_str.split('-'))
                spending, created = MonthlySpending.objects.get_or_create(
                    year=year,
                    month=month
                )
                if created:
                    self.stdout.write(f'Created new record for {year}-{month:02d}')
                else:
                    self.stdout.write(f'Updating existing record for {year}-{month:02d}')

                summary = spending.update_from_token_usage()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated {year}-{month:02d}: '
                        f'${summary["total_cost"]:.4f} '
                        f'({summary["total_requests"]} requests)'
                    )
                )
            except ValueError:
                self.stdout.write(
                    self.style.ERROR(
                        'Invalid month format. Use YYYY-MM (e.g., 2025-11)'
                    )
                )
                return

        elif update_all:
            # Update all existing records
            all_spending = MonthlySpending.objects.all()
            total_updated = 0

            self.stdout.write(f'Updating {all_spending.count()} month(s)...')

            for spending in all_spending:
                summary = spending.update_from_token_usage()
                self.stdout.write(
                    f'  {spending.year}-{spending.month:02d}: '
                    f'${summary["total_cost"]:.4f} '
                    f'({summary["total_requests"]} requests)'
                )
                total_updated += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated {total_updated} month(s)'
                )
            )

        else:
            # Update current month (default)
            spending = MonthlySpending.get_current_month()
            now = timezone.now()

            self.stdout.write(
                f'Updating current month: {now.year}-{now.month:02d}'
            )

            summary = spending.update_from_token_usage()

            self.stdout.write(
                self.style.SUCCESS(
                    f'Current month spending: ${summary["total_cost"]:.4f}'
                )
            )
            self.stdout.write(f'LLM cost: ${summary["llm_cost"]:.4f}')
            self.stdout.write(f'Total requests: {summary["total_requests"]}')

            # Show cap status
            cap_status = spending.get_cap_status()
            if cap_status['has_cap']:
                self.stdout.write(
                    f'\nCap: ${cap_status["cap_amount"]:.2f}'
                )
                self.stdout.write(
                    f'Used: {cap_status["percentage"]:.1f}%'
                )
                self.stdout.write(
                    f'Remaining: ${cap_status["remaining"]:.2f}'
                )

                if cap_status['is_over_cap']:
                    self.stdout.write(
                        self.style.ERROR('WARNING: Over budget!')
                    )
                elif cap_status['alert_level'] in ['critical', 'warning']:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Alert: {cap_status["alert_level"].upper()}'
                        )
                    )
            else:
                self.stdout.write(
                    self.style.WARNING('No spending cap configured')
                )

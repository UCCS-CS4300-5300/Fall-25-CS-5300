"""
Management command to set the monthly spending cap.

Related to Issue #12 (Set Monthly Spend Cap).

Usage:
    python manage.py set_spending_cap 200
    python manage.py set_spending_cap 200 --user admin
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from active_interview_app.spending_tracker_models import MonthlySpendingCap


class Command(BaseCommand):
    help = 'Set the monthly spending cap for API services'

    def add_arguments(self, parser):
        parser.add_argument(
            'amount',
            type=float,
            help='Monthly spending cap amount in USD (e.g., 200)'
        )
        parser.add_argument(
            '--user',
            type=str,
            default=None,
            help='Username of admin setting this cap (optional)'
        )

    def handle(self, *args, **options):
        amount = options['amount']
        username = options.get('user')

        # Validate amount
        if amount < 0:
            raise CommandError('Spending cap must be a positive number')

        # Get user if specified
        user = None
        if username:
            try:
                user = User.objects.get(username=username)
                if not user.is_staff:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Warning: User {username} is not a staff member'
                        )
                    )
            except User.DoesNotExist:
                raise CommandError(f'User "{username}" does not exist')

        # Create new cap (this automatically deactivates old ones)
        MonthlySpendingCap.objects.create(
            cap_amount_usd=amount,
            is_active=True,
            created_by=user
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully set monthly spending cap to ${amount:.2f}'
            )
        )

        if user:
            self.stdout.write(f'Set by: {user.username}')

        # Show previous cap if any
        previous_caps = MonthlySpendingCap.objects.filter(
            is_active=False
        ).order_by('-created_at')[:1]

        if previous_caps.exists():
            prev_cap = previous_caps.first()
            self.stdout.write(
                f'Previous cap: ${prev_cap.cap_amount_usd:.2f}'
            )

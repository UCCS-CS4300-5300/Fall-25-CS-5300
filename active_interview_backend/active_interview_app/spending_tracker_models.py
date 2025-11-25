"""
Monthly spending tracking models for budget management.

Related to Issue #10 (Cost Caps & API Key Rotation) and Issue #11 (Track Monthly Spending).
"""
from django.db import models
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from datetime import date


class MonthlySpendingCap(models.Model):
    """
    Configurable monthly spending cap for API services.

    This model stores the maximum allowed spending per month for all API services
    (OpenAI, TTS, etc.). Only one active cap should exist at a time.

    Related to Issue #12 (Set Monthly Spend Cap).
    """
    cap_amount_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Maximum allowed monthly spending in USD'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this cap is currently active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Admin who set this cap'
    )

    class Meta:
        verbose_name = 'Monthly Spending Cap'
        verbose_name_plural = 'Monthly Spending Caps'
        ordering = ['-created_at']

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"${self.cap_amount_usd}/month ({status})"

    @classmethod
    def get_active_cap(cls):
        """
        Get the currently active spending cap.

        Returns:
            MonthlySpendingCap: Active cap object or None if no cap is set
        """
        try:
            return cls.objects.filter(is_active=True).latest('created_at')
        except cls.DoesNotExist:
            return None

    def save(self, *args, **kwargs):
        """
        Ensure only one cap is active at a time.
        When a new cap is set to active, deactivate all others.
        """
        if self.is_active:
            # Deactivate all other caps
            MonthlySpendingCap.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class MonthlySpending(models.Model):
    """
    Tracks actual spending for each month.

    This model maintains a running total of API costs for the current month,
    broken down by service type (LLM, TTS, etc.). A new record is created
    automatically at the start of each month.

    Related to Issue #11 (Track Monthly Spending).
    """
    year = models.IntegerField(
        help_text='Year (e.g., 2025)'
    )
    month = models.IntegerField(
        help_text='Month (1-12)'
    )

    # Total spending for the month
    total_cost_usd = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text='Total spending for this month in USD'
    )

    # Breakdown by service type
    llm_cost_usd = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text='LLM (GPT-4o, Claude) costs in USD'
    )
    tts_cost_usd = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text='Text-to-Speech costs in USD'
    )
    other_cost_usd = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text='Other API costs in USD'
    )

    # Request counts
    total_requests = models.IntegerField(
        default=0,
        help_text='Total number of API requests this month'
    )
    llm_requests = models.IntegerField(
        default=0,
        help_text='Number of LLM requests this month'
    )
    tts_requests = models.IntegerField(
        default=0,
        help_text='Number of TTS requests this month'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_updated_from_token_usage = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last time spending was calculated from TokenUsage records'
    )

    class Meta:
        unique_together = ['year', 'month']
        ordering = ['-year', '-month']
        verbose_name = 'Monthly Spending'
        verbose_name_plural = 'Monthly Spending Records'
        indexes = [
            models.Index(fields=['-year', '-month']),
        ]

    def __str__(self):
        return f"{self.year}-{self.month:02d}: ${self.total_cost_usd}"

    @classmethod
    def get_or_create_current_month(cls):
        """
        Get or create the MonthlySpending record for the current month.

        Returns:
            tuple: (MonthlySpending instance, created boolean)
        """
        now = timezone.now()
        return cls.objects.get_or_create(
            year=now.year,
            month=now.month
        )

    @classmethod
    def get_current_month(cls):
        """
        Get the MonthlySpending record for the current month.
        Creates one if it doesn't exist.

        Returns:
            MonthlySpending: Current month's spending record
        """
        record, _ = cls.get_or_create_current_month()
        return record

    def update_from_token_usage(self):
        """
        Recalculate spending from TokenUsage records for this month.

        This method queries all TokenUsage records for this month
        and updates the spending totals.

        Returns:
            dict: Summary of updated costs
        """
        from .token_usage_models import TokenUsage
        from datetime import datetime

        # Get all token usage for this month
        start_date = datetime(self.year, self.month, 1)
        if self.month == 12:
            end_date = datetime(self.year + 1, 1, 1)
        else:
            end_date = datetime(self.year, self.month + 1, 1)

        # Query TokenUsage records
        token_records = TokenUsage.objects.filter(
            created_at__gte=start_date,
            created_at__lt=end_date
        )

        # Calculate totals
        llm_cost = Decimal('0.0')
        llm_count = 0

        for record in token_records:
            cost = Decimal(str(record.estimated_cost))
            llm_cost += cost
            llm_count += 1

        # Update fields
        self.llm_cost_usd = llm_cost
        self.llm_requests = llm_count
        self.total_cost_usd = llm_cost + self.tts_cost_usd + self.other_cost_usd
        self.total_requests = llm_count + self.tts_requests
        self.last_updated_from_token_usage = timezone.now()
        self.save()

        return {
            'llm_cost': float(llm_cost),
            'llm_requests': llm_count,
            'total_cost': float(self.total_cost_usd),
            'total_requests': self.total_requests
        }

    def add_llm_cost(self, cost_usd):
        """
        Add an LLM cost to this month's spending.

        Args:
            cost_usd: Cost in USD (float or Decimal)
        """
        cost = Decimal(str(cost_usd))
        self.llm_cost_usd += cost
        self.llm_requests += 1
        self.total_cost_usd += cost
        self.total_requests += 1
        self.save()

    def add_tts_cost(self, cost_usd):
        """
        Add a TTS cost to this month's spending.

        Args:
            cost_usd: Cost in USD (float or Decimal)
        """
        cost = Decimal(str(cost_usd))
        self.tts_cost_usd += cost
        self.tts_requests += 1
        self.total_cost_usd += cost
        self.total_requests += 1
        self.save()

    def get_percentage_of_cap(self):
        """
        Calculate percentage of monthly cap used.

        Returns:
            float: Percentage (0-100+) or None if no cap is set
        """
        cap = MonthlySpendingCap.get_active_cap()
        if not cap:
            return None

        if cap.cap_amount_usd == 0:
            return 100.0 if self.total_cost_usd > 0 else 0.0

        percentage = (self.total_cost_usd / cap.cap_amount_usd) * Decimal('100')
        return float(percentage)

    def is_over_cap(self):
        """
        Check if spending has exceeded the monthly cap.

        Returns:
            bool: True if over cap, False otherwise
        """
        cap = MonthlySpendingCap.get_active_cap()
        if not cap:
            return False

        return self.total_cost_usd > cap.cap_amount_usd

    def get_remaining_budget(self):
        """
        Calculate remaining budget for the month.

        Returns:
            Decimal: Remaining budget in USD or None if no cap is set
        """
        cap = MonthlySpendingCap.get_active_cap()
        if not cap:
            return None

        remaining = cap.cap_amount_usd - self.total_cost_usd
        return max(remaining, Decimal('0.0'))

    def get_cap_status(self):
        """
        Get a human-readable status of spending vs cap.

        Returns:
            dict: Status information including percentage, remaining, and alert level
        """
        cap = MonthlySpendingCap.get_active_cap()
        if not cap:
            return {
                'has_cap': False,
                'cap_amount': None,
                'spent': float(self.total_cost_usd),
                'remaining': None,
                'percentage': None,
                'alert_level': 'none'
            }

        percentage = self.get_percentage_of_cap()

        # Determine alert level
        if percentage >= 100:
            alert_level = 'danger'
        elif percentage >= 90:
            alert_level = 'critical'
        elif percentage >= 75:
            alert_level = 'warning'
        elif percentage >= 50:
            alert_level = 'caution'
        else:
            alert_level = 'ok'

        return {
            'has_cap': True,
            'cap_amount': float(cap.cap_amount_usd),
            'spent': float(self.total_cost_usd),
            'remaining': float(self.get_remaining_budget()),
            'percentage': round(percentage, 2),
            'alert_level': alert_level,
            'is_over_cap': self.is_over_cap()
        }

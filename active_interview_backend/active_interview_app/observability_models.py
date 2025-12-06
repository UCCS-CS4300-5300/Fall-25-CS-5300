"""
Observability and metrics tracking models.
Stores performance metrics, error rates, and latency data for system monitoring.

Related to Issues #14, #15 (Observability Dashboard).
"""
from django.db import models
from django.utils import timezone
from datetime import timedelta
import statistics


class RequestMetric(models.Model):
    """
    Tracks individual HTTP requests for calculating RPS and analyzing traffic patterns.
    Records every request with timestamp, endpoint, method, and status code.
    """
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    endpoint = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Request path (e.g., '/api/chat/')"
    )
    method = models.CharField(
        max_length=10,
        help_text="HTTP method (GET, POST, etc.)"
    )
    status_code = models.IntegerField(
        db_index=True,
        help_text="HTTP response status code"
    )
    response_time_ms = models.FloatField(
        help_text="Response time in milliseconds"
    )
    user_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of authenticated user (null for anonymous)"
    )

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['endpoint', '-timestamp']),
            models.Index(fields=['status_code', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
        verbose_name = "Request Metric"
        verbose_name_plural = "Request Metrics"

    def __str__(self):
        return (
            f"{self.method} {self.endpoint} - "
            f"{self.status_code} ({self.response_time_ms}ms)"
        )

    @property
    def is_error(self):
        """Check if this request resulted in an error (4xx or 5xx)."""
        return self.status_code >= 400

    @property
    def is_client_error(self):
        """Check if this request resulted in a client error (4xx)."""
        return 400 <= self.status_code < 500

    @property
    def is_server_error(self):
        """Check if this request resulted in a server error (5xx)."""
        return self.status_code >= 500

    @classmethod
    def calculate_rps(cls, endpoint=None, start_time=None, end_time=None):
        """
        Calculate requests per second for an endpoint or all endpoints.

        Args:
            endpoint: Specific endpoint to analyze (None for all endpoints)
            start_time: Start of time window (default: 1 minute ago)
            end_time: End of time window (default: now)

        Returns:
            Float representing requests per second
        """
        if end_time is None:
            end_time = timezone.now()
        if start_time is None:
            start_time = end_time - timedelta(minutes=1)

        # Build query
        queryset = cls.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time
        )
        if endpoint:
            queryset = queryset.filter(endpoint=endpoint)

        # Calculate RPS
        total_requests = queryset.count()
        time_span_seconds = (end_time - start_time).total_seconds()

        if time_span_seconds == 0:
            return 0.0

        return total_requests / time_span_seconds

    @classmethod
    def get_error_rate(cls, endpoint=None, start_time=None, end_time=None):
        """
        Calculate error rate (percentage of requests that resulted in errors).

        Args:
            endpoint: Specific endpoint to analyze (None for all endpoints)
            start_time: Start of time window (default: 1 hour ago)
            end_time: End of time window (default: now)

        Returns:
            Dict with error statistics
        """
        if end_time is None:
            end_time = timezone.now()
        if start_time is None:
            start_time = end_time - timedelta(hours=1)

        # Build query
        queryset = cls.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time
        )
        if endpoint:
            queryset = queryset.filter(endpoint=endpoint)

        total = queryset.count()
        if total == 0:
            return {
                'total_requests': 0,
                'error_count': 0,
                'client_error_count': 0,
                'server_error_count': 0,
                'error_rate': 0.0
            }

        errors = queryset.filter(status_code__gte=400)
        client_errors = queryset.filter(status_code__gte=400, status_code__lt=500)
        server_errors = queryset.filter(status_code__gte=500)

        return {
            'total_requests': total,
            'error_count': errors.count(),
            'client_error_count': client_errors.count(),
            'server_error_count': server_errors.count(),
            'error_rate': (errors.count() / total) * 100
        }

    @classmethod
    def calculate_percentiles(cls, endpoint=None, start_time=None, end_time=None):
        """
        Calculate p50 and p95 latency percentiles.

        Args:
            endpoint: Specific endpoint to analyze (None for all endpoints)
            start_time: Start of time window (default: 1 hour ago)
            end_time: End of time window (default: now)

        Returns:
            Dict with p50, p95, min, max, and mean latency in milliseconds
        """
        if end_time is None:
            end_time = timezone.now()
        if start_time is None:
            start_time = end_time - timedelta(hours=1)

        # Build query
        queryset = cls.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time
        )
        if endpoint:
            queryset = queryset.filter(endpoint=endpoint)

        # Get response times
        response_times = list(
            queryset.values_list('response_time_ms', flat=True)
        )

        if not response_times:
            return {
                'count': 0,
                'p50': 0.0,
                'p95': 0.0,
                'min': 0.0,
                'max': 0.0,
                'mean': 0.0
            }

        # Calculate percentiles
        sorted_times = sorted(response_times)

        return {
            'count': len(response_times),
            'p50': statistics.quantiles(sorted_times, n=100)[49],  # 50th percentile
            'p95': statistics.quantiles(sorted_times, n=100)[94],  # 95th percentile
            'min': min(response_times),
            'max': max(response_times),
            'mean': statistics.mean(response_times)
        }


class DailyMetricsSummary(models.Model):
    """
    Daily aggregated metrics for efficient historical analysis.
    Calculated by a background task or management command.
    """
    date = models.DateField(unique=True, db_index=True)

    # Request statistics
    total_requests = models.IntegerField(default=0)
    total_errors = models.IntegerField(default=0)
    client_errors = models.IntegerField(default=0)
    server_errors = models.IntegerField(default=0)

    # Latency statistics (in milliseconds)
    avg_response_time = models.FloatField(default=0.0)
    p50_response_time = models.FloatField(default=0.0)
    p95_response_time = models.FloatField(default=0.0)
    max_response_time = models.FloatField(default=0.0)

    # Endpoints breakdown (JSON)
    endpoint_stats = models.JSONField(
        default=dict,
        help_text="Per-endpoint statistics for the day"
    )
    # Structure: {"endpoint": {"requests": int, "errors": int, "avg_latency": float}}

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        verbose_name = "Daily Metrics Summary"
        verbose_name_plural = "Daily Metrics Summaries"

    def __str__(self):
        return f"Metrics for {self.date}"

    @property
    def error_rate(self):
        """Calculate error rate as percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.total_errors / self.total_requests) * 100


class ProviderCostDaily(models.Model):
    """
    Daily aggregated provider costs for budget tracking and analysis.
    Aggregates costs from TokenUsage and other provider usage models.
    """
    date = models.DateField(db_index=True)
    provider = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Provider name (e.g., 'OpenAI', 'Anthropic')"
    )
    service = models.CharField(
        max_length=100,
        help_text="Service type (e.g., 'gpt-4o', 'claude-sonnet-4')"
    )

    # Cost tracking
    total_requests = models.IntegerField(default=0)
    total_cost_usd = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0.0,
        help_text="Total cost in USD"
    )

    # Token usage (for AI providers)
    total_tokens = models.BigIntegerField(
        default=0,
        help_text="Total tokens used (if applicable)"
    )
    prompt_tokens = models.BigIntegerField(
        default=0,
        help_text="Prompt tokens used"
    )
    completion_tokens = models.BigIntegerField(
        default=0,
        help_text="Completion tokens used"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'provider']
        unique_together = ['date', 'provider', 'service']
        indexes = [
            models.Index(fields=['-date', 'provider']),
            models.Index(fields=['provider', '-date']),
        ]
        verbose_name = "Provider Cost (Daily)"
        verbose_name_plural = "Provider Costs (Daily)"

    def __str__(self):
        return f"{self.provider}/{self.service} - {self.date} (${self.total_cost_usd})"

    @classmethod
    def get_monthly_cost(cls, year, month, provider=None):
        """
        Get total cost for a specific month.

        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)
            provider: Optional provider filter

        Returns:
            Decimal representing total cost in USD
        """
        from decimal import Decimal

        queryset = cls.objects.filter(
            date__year=year,
            date__month=month
        )
        if provider:
            queryset = queryset.filter(provider=provider)

        total = queryset.aggregate(
            total=models.Sum('total_cost_usd')
        )['total']

        return total or Decimal('0.0')


class ErrorLog(models.Model):
    """
    Detailed error logging for debugging and analysis.
    Captures full error details including stack traces.
    """
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    endpoint = models.CharField(max_length=255, db_index=True)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField(db_index=True)

    # Error details
    error_type = models.CharField(
        max_length=255,
        help_text="Exception class name"
    )
    error_message = models.TextField(
        help_text="Error message"
    )
    stack_trace = models.TextField(
        blank=True,
        help_text="Full stack trace"
    )

    # Request context
    user_id = models.IntegerField(null=True, blank=True)
    request_data = models.JSONField(
        default=dict,
        help_text="Request parameters and headers"
    )

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['endpoint', '-timestamp']),
            models.Index(fields=['error_type', '-timestamp']),
        ]
        verbose_name = "Error Log"
        verbose_name_plural = "Error Logs"

    def __str__(self):
        return (
            f"{self.error_type} at {self.endpoint} - "
            f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        )


class InterviewResponseLatency(models.Model):
    """
    Tracks latency for individual interview AI responses.
    Used to ensure 90% of responses meet the 2-second latency budget.

    Related to Issues #20, #54 (Latency Budget).
    """
    chat = models.ForeignKey(
        'active_interview_app.Chat',
        on_delete=models.CASCADE,
        related_name='response_latencies',
        help_text="Interview chat session"
    )
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="User who received the response"
    )

    # Timing data
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    response_time_ms = models.FloatField(
        help_text="Total response time in milliseconds"
    )
    ai_processing_time_ms = models.FloatField(
        null=True,
        blank=True,
        help_text="OpenAI API call duration in milliseconds"
    )

    # Context
    question_number = models.IntegerField(
        help_text="Question sequence number in the interview"
    )
    interview_type = models.CharField(
        max_length=20,
        help_text="Interview type (PRACTICE or INVITED)"
    )

    # Threshold tracking
    exceeded_threshold = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True if response time exceeded latency budget (2000ms)"
    )
    threshold_ms = models.IntegerField(
        default=2000,
        help_text="Latency threshold that was configured at time of request"
    )

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['chat', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['exceeded_threshold', '-timestamp']),
            models.Index(fields=['interview_type', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
        verbose_name = "Interview Response Latency"
        verbose_name_plural = "Interview Response Latencies"

    def __str__(self):
        status = "⚠️ SLOW" if self.exceeded_threshold else "✓ OK"
        return (
            f"{status} Q{self.question_number} - {self.response_time_ms:.0f}ms "
            f"(Chat #{self.chat_id})"
        )

    @property
    def is_within_budget(self):
        """Check if response met the latency budget."""
        return self.response_time_ms <= self.threshold_ms

    @property
    def latency_budget_percentage(self):
        """Calculate what percentage of the budget was used."""
        return (self.response_time_ms / self.threshold_ms) * 100

    @classmethod
    def get_session_stats(cls, chat_id):
        """
        Get latency statistics for a specific interview session.

        Args:
            chat_id: Chat ID to analyze

        Returns:
            Dict with latency statistics for the session
        """
        metrics = cls.objects.filter(chat_id=chat_id)

        if not metrics.exists():
            return {
                'total_responses': 0,
                'within_budget': 0,
                'exceeded_budget': 0,
                'budget_compliance_rate': 0.0,
                'p50': 0.0,
                'p90': 0.0,
                'p95': 0.0,
                'min': 0.0,
                'max': 0.0,
                'mean': 0.0
            }

        total = metrics.count()
        within_budget = metrics.filter(exceeded_threshold=False).count()
        exceeded_budget = metrics.filter(exceeded_threshold=True).count()

        response_times = list(metrics.values_list('response_time_ms', flat=True))
        sorted_times = sorted(response_times)

        return {
            'total_responses': total,
            'within_budget': within_budget,
            'exceeded_budget': exceeded_budget,
            'budget_compliance_rate': (within_budget / total) * 100,
            'p50': statistics.quantiles(sorted_times, n=100)[49] if len(sorted_times) >= 100 else statistics.median(sorted_times),
            'p90': statistics.quantiles(sorted_times, n=100)[89] if len(sorted_times) >= 100 else sorted_times[int(len(sorted_times) * 0.9)],
            'p95': statistics.quantiles(sorted_times, n=100)[94] if len(sorted_times) >= 100 else sorted_times[int(len(sorted_times) * 0.95)],
            'min': min(response_times),
            'max': max(response_times),
            'mean': statistics.mean(response_times)
        }

    @classmethod
    def calculate_compliance_rate(cls, interview_type=None, start_time=None, end_time=None):
        """
        Calculate what percentage of responses met the latency budget.

        Args:
            interview_type: Filter by interview type (PRACTICE or INVITED)
            start_time: Start of time window (default: 1 hour ago)
            end_time: End of time window (default: now)

        Returns:
            Dict with compliance statistics
        """
        if end_time is None:
            end_time = timezone.now()
        if start_time is None:
            start_time = end_time - timedelta(hours=1)

        queryset = cls.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time
        )
        if interview_type:
            queryset = queryset.filter(interview_type=interview_type)

        total = queryset.count()
        if total == 0:
            return {
                'total_responses': 0,
                'within_budget': 0,
                'exceeded_budget': 0,
                'compliance_rate': 0.0,
                'target_rate': 90.0,
                'meets_target': False
            }

        within_budget = queryset.filter(exceeded_threshold=False).count()
        exceeded_budget = queryset.filter(exceeded_threshold=True).count()
        compliance_rate = (within_budget / total) * 100

        return {
            'total_responses': total,
            'within_budget': within_budget,
            'exceeded_budget': exceeded_budget,
            'compliance_rate': compliance_rate,
            'target_rate': 90.0,
            'meets_target': compliance_rate >= 90.0
        }

    @classmethod
    def calculate_percentiles(cls, interview_type=None, start_time=None, end_time=None):
        """
        Calculate latency percentiles for interview responses.

        Args:
            interview_type: Filter by interview type (PRACTICE or INVITED)
            start_time: Start of time window (default: 1 hour ago)
            end_time: End of time window (default: now)

        Returns:
            Dict with p50, p90, p95, min, max, and mean latency in milliseconds
        """
        if end_time is None:
            end_time = timezone.now()
        if start_time is None:
            start_time = end_time - timedelta(hours=1)

        queryset = cls.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time
        )
        if interview_type:
            queryset = queryset.filter(interview_type=interview_type)

        response_times = list(queryset.values_list('response_time_ms', flat=True))

        if not response_times:
            return {
                'count': 0,
                'p50': 0.0,
                'p90': 0.0,
                'p95': 0.0,
                'min': 0.0,
                'max': 0.0,
                'mean': 0.0
            }

        sorted_times = sorted(response_times)

        return {
            'count': len(response_times),
            'p50': statistics.quantiles(sorted_times, n=100)[49] if len(sorted_times) >= 100 else statistics.median(sorted_times),
            'p90': statistics.quantiles(sorted_times, n=100)[89] if len(sorted_times) >= 100 else sorted_times[int(len(sorted_times) * 0.9)],
            'p95': statistics.quantiles(sorted_times, n=100)[94] if len(sorted_times) >= 100 else sorted_times[int(len(sorted_times) * 0.95)],
            'min': min(response_times),
            'max': max(response_times),
            'mean': statistics.mean(response_times)
        }

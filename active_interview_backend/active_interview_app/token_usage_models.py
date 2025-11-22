"""
Token usage tracking models for monitoring API calls to Claude and ChatGPT.
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class TokenUsage(models.Model):
    """
    Tracks individual API calls to Claude and ChatGPT services.
    Records token usage per request with model differentiation.
    """
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who made the request"
    )
    git_branch = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Git branch where this request originated"
    )
    model_name = models.CharField(
        max_length=100,
        db_index=True,
        help_text=(
            "AI model used (e.g., 'gpt-4o', "
            "'claude-sonnet-4-5-20250929')")
    )
    endpoint = models.CharField(
        max_length=255,
        help_text="API endpoint called"
    )
    prompt_tokens = models.IntegerField(
        default=0,
        help_text="Number of tokens in the prompt/input"
    )
    completion_tokens = models.IntegerField(
        default=0,
        help_text="Number of tokens in the completion/output"
    )
    total_tokens = models.IntegerField(
        default=0,
        help_text="Total tokens used (prompt + completion)"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['git_branch', 'model_name']),
            models.Index(fields=['created_at', 'git_branch']),
        ]
        verbose_name = "Token Usage"
        verbose_name_plural = "Token Usage Records"

    def save(self, *args, **kwargs):
        """Auto-calculate total_tokens before saving."""
        self.total_tokens = self.prompt_tokens + self.completion_tokens
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.model_name} - {self.git_branch} - "
            f"{self.total_tokens} tokens at {self.created_at}"
        )

    @property
    def estimated_cost(self):
        """
        Calculate estimated cost based on model and token usage.
        Returns cost in USD.
        """
        # Cost per 1000 tokens
        costs = {
            # OpenAI GPT-4o pricing (as of 2024)
            'gpt-4o': {
                'prompt': 0.03,
                'completion': 0.06
            },
            # Claude Sonnet 4.5 pricing (as of 2025)
            'claude-sonnet-4-5-20250929': {
                'prompt': 0.003,
                'completion': 0.015
            },
            'claude-sonnet-4': {
                'prompt': 0.003,
                'completion': 0.015
            },
            # Fallback for unknown models
            'default': {
                'prompt': 0.03,
                'completion': 0.06
            }
        }

        # Get cost rates for this model
        model_costs = costs.get(self.model_name, costs['default'])

        # Calculate cost
        prompt_cost = ((self.prompt_tokens / 1000) *
                       model_costs['prompt'])
        completion_cost = ((self.completion_tokens / 1000) *
                           model_costs['completion'])

        return prompt_cost + completion_cost

    @classmethod
    def get_branch_summary(cls, branch_name):
        """
        Get token usage summary for a specific branch.
        Returns dict with totals by model.
        """
        records = cls.objects.filter(git_branch=branch_name)

        summary = {
            'total_requests': records.count(),
            'by_model': {},
            'total_tokens': 0,
            'total_cost': 0.0
        }

        for record in records:
            model = record.model_name
            if model not in summary['by_model']:
                summary['by_model'][model] = {
                    'requests': 0,
                    'prompt_tokens': 0,
                    'completion_tokens': 0,
                    'total_tokens': 0,
                    'cost': 0.0
                }

            summary['by_model'][model]['requests'] += 1
            summary['by_model'][model]['prompt_tokens'] += (
                record.prompt_tokens)
            summary['by_model'][model]['completion_tokens'] += (
                record.completion_tokens)
            summary['by_model'][model]['total_tokens'] += (
                record.total_tokens)
            summary['by_model'][model]['cost'] += record.estimated_cost

            summary['total_tokens'] += record.total_tokens
            summary['total_cost'] += record.estimated_cost

        return summary

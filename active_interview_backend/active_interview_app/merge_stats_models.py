"""
Merge token statistics models for tracking cumulative token usage across branches.
"""
from django.db import models
from django.contrib.auth.models import User


class MergeTokenStats(models.Model):
    """
    Aggregates token usage when branches are merged.
    Tracks cumulative totals across all merges with model differentiation.
    """
    merge_date = models.DateTimeField(auto_now_add=True, db_index=True)
    source_branch = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Branch that was merged"
    )
    target_branch = models.CharField(
        max_length=255,
        default="main",
        help_text="Branch that received the merge"
    )
    merge_commit_sha = models.CharField(
        max_length=40,
        unique=True,
        help_text="Git commit hash of the merge"
    )
    merged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who performed the merge"
    )
    pr_number = models.IntegerField(
        null=True,
        blank=True,
        help_text="Pull request number if applicable"
    )

    # Per-model statistics
    claude_prompt_tokens = models.IntegerField(
        default=0,
        help_text="Claude prompt tokens used by this branch"
    )
    claude_completion_tokens = models.IntegerField(
        default=0,
        help_text="Claude completion tokens used by this branch"
    )
    claude_total_tokens = models.IntegerField(
        default=0,
        help_text="Total Claude tokens used by this branch"
    )
    claude_request_count = models.IntegerField(
        default=0,
        help_text="Number of Claude API requests"
    )

    chatgpt_prompt_tokens = models.IntegerField(
        default=0,
        help_text="ChatGPT prompt tokens used by this branch"
    )
    chatgpt_completion_tokens = models.IntegerField(
        default=0,
        help_text="ChatGPT completion tokens used by this branch"
    )
    chatgpt_total_tokens = models.IntegerField(
        default=0,
        help_text="Total ChatGPT tokens used by this branch"
    )
    chatgpt_request_count = models.IntegerField(
        default=0,
        help_text="Number of ChatGPT API requests"
    )

    # Combined totals
    total_prompt_tokens = models.IntegerField(
        default=0,
        help_text="All prompt tokens (Claude + ChatGPT)"
    )
    total_completion_tokens = models.IntegerField(
        default=0,
        help_text="All completion tokens (Claude + ChatGPT)"
    )
    total_tokens = models.IntegerField(
        default=0,
        help_text="All tokens used by this branch"
    )
    request_count = models.IntegerField(
        default=0,
        help_text="Total number of API requests"
    )

    # Cumulative tracking (running totals across ALL merges)
    cumulative_claude_tokens = models.IntegerField(
        default=0,
        help_text="Running total of all Claude tokens across all merges"
    )
    cumulative_chatgpt_tokens = models.IntegerField(
        default=0,
        help_text="Running total of all ChatGPT tokens across all merges"
    )
    cumulative_total_tokens = models.IntegerField(
        default=0,
        help_text="Running total of ALL tokens across all merges"
    )
    cumulative_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Running total cost in USD across all merges"
    )

    notes = models.TextField(
        blank=True,
        help_text="Additional notes or metadata"
    )

    class Meta:
        ordering = ['-merge_date']
        indexes = [
            models.Index(fields=['source_branch']),
            models.Index(fields=['merge_date']),
        ]
        verbose_name = "Merge Token Statistics"
        verbose_name_plural = "Merge Token Statistics"

    def __str__(self):
        return (
            f"{self.source_branch} → {self.target_branch} - "
            f"{self.total_tokens} tokens ({self.merge_date.strftime('%Y-%m-%d')})"
        )

    @property
    def branch_cost(self):
        """Calculate cost for this branch's token usage."""
        # OpenAI GPT-4o pricing
        chatgpt_cost = (
            (self.chatgpt_prompt_tokens / 1000) * 0.03 +
            (self.chatgpt_completion_tokens / 1000) * 0.06
        )

        # Claude Sonnet 4.5 pricing
        claude_cost = (
            (self.claude_prompt_tokens / 1000) * 0.003 +
            (self.claude_completion_tokens / 1000) * 0.015
        )

        return chatgpt_cost + claude_cost

    def save(self, *args, **kwargs):
        """Calculate totals and update cumulative values before saving."""
        # Calculate this branch's totals
        self.claude_total_tokens = self.claude_prompt_tokens + self.claude_completion_tokens
        self.chatgpt_total_tokens = self.chatgpt_prompt_tokens + self.chatgpt_completion_tokens

        self.total_prompt_tokens = self.claude_prompt_tokens + self.chatgpt_prompt_tokens
        self.total_completion_tokens = self.claude_completion_tokens + self.chatgpt_completion_tokens
        self.total_tokens = self.total_prompt_tokens + self.total_completion_tokens
        self.request_count = self.claude_request_count + self.chatgpt_request_count

        # Update cumulative totals
        if self.pk is None:  # Only update cumulative on creation
            previous = MergeTokenStats.objects.order_by('-merge_date').first()

            if previous:
                self.cumulative_claude_tokens = previous.cumulative_claude_tokens + self.claude_total_tokens
                self.cumulative_chatgpt_tokens = previous.cumulative_chatgpt_tokens + self.chatgpt_total_tokens
                self.cumulative_total_tokens = previous.cumulative_total_tokens + self.total_tokens
                self.cumulative_cost = previous.cumulative_cost + float(self.branch_cost)
            else:
                self.cumulative_claude_tokens = self.claude_total_tokens
                self.cumulative_chatgpt_tokens = self.chatgpt_total_tokens
                self.cumulative_total_tokens = self.total_tokens
                self.cumulative_cost = float(self.branch_cost)

        super().save(*args, **kwargs)

    @classmethod
    def create_from_branch(cls, branch_name, commit_sha, merged_by=None, pr_number=None):
        """
        Create a merge statistics record by aggregating TokenUsage records for a branch.
        Separates Claude and ChatGPT tokens.
        """
        from .token_usage_models import TokenUsage

        # Get all token usage for this branch
        branch_tokens = TokenUsage.objects.filter(git_branch=branch_name)

        # Separate by model type
        claude_tokens = branch_tokens.filter(model_name__icontains='claude')
        chatgpt_tokens = branch_tokens.filter(model_name__icontains='gpt')

        # Aggregate Claude tokens
        claude_stats = claude_tokens.aggregate(
            prompt=models.Sum('prompt_tokens'),
            completion=models.Sum('completion_tokens'),
            count=models.Count('id')
        )

        # Aggregate ChatGPT tokens
        chatgpt_stats = chatgpt_tokens.aggregate(
            prompt=models.Sum('prompt_tokens'),
            completion=models.Sum('completion_tokens'),
            count=models.Count('id')
        )

        # Create the merge stats record
        merge_stat = cls.objects.create(
            source_branch=branch_name,
            merge_commit_sha=commit_sha,
            merged_by=merged_by,
            pr_number=pr_number,
            claude_prompt_tokens=claude_stats['prompt'] or 0,
            claude_completion_tokens=claude_stats['completion'] or 0,
            claude_request_count=claude_stats['count'] or 0,
            chatgpt_prompt_tokens=chatgpt_stats['prompt'] or 0,
            chatgpt_completion_tokens=chatgpt_stats['completion'] or 0,
            chatgpt_request_count=chatgpt_stats['count'] or 0,
        )

        return merge_stat

    def get_breakdown_summary(self):
        """Get a detailed breakdown of token usage."""
        return {
            'branch': self.source_branch,
            'merge_date': self.merge_date,
            'claude': {
                'prompt_tokens': self.claude_prompt_tokens,
                'completion_tokens': self.claude_completion_tokens,
                'total_tokens': self.claude_total_tokens,
                'requests': self.claude_request_count,
            },
            'chatgpt': {
                'prompt_tokens': self.chatgpt_prompt_tokens,
                'completion_tokens': self.chatgpt_completion_tokens,
                'total_tokens': self.chatgpt_total_tokens,
                'requests': self.chatgpt_request_count,
            },
            'totals': {
                'prompt_tokens': self.total_prompt_tokens,
                'completion_tokens': self.total_completion_tokens,
                'total_tokens': self.total_tokens,
                'requests': self.request_count,
                'cost': f"${self.branch_cost:.2f}",
            },
            'cumulative': {
                'claude_tokens': self.cumulative_claude_tokens,
                'chatgpt_tokens': self.cumulative_chatgpt_tokens,
                'total_tokens': self.cumulative_total_tokens,
                'cost': f"${self.cumulative_cost:.2f}",
            }
        }

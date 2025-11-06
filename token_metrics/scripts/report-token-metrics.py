#!/usr/bin/env python3
"""
Generate Token Metrics Report

This script generates a comprehensive report of token usage across
all branches, sessions, and time periods.

Usage:
    python token_metrics/scripts/report-token-metrics.py
"""

import os
import sys
from datetime import datetime, timedelta

# Setup Django environment
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'active_interview_backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'active_interview_project.settings')
import django
django.setup()

from active_interview_app.token_usage_models import TokenUsage
from django.db.models import Sum, Count
from django.utils import timezone


def get_current_branch():
    """Get current git branch from environment or git."""
    import subprocess

    # Try environment variables first (for CI/CD)
    branch = (
        os.environ.get('GITHUB_HEAD_REF') or
        os.environ.get('GITHUB_REF_NAME') or
        None
    )

    if branch:
        return branch

    # Fall back to git command
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    return 'unknown'


def format_large_number(num):
    """Format large numbers with commas."""
    return f"{num:,}"


def generate_report():
    """Generate comprehensive token usage report."""
    current_branch = get_current_branch()

    print("=" * 80)
    print(" " * 25 + "TOKEN USAGE METRICS REPORT")
    print("=" * 80)
    print()

    # Overall statistics
    total_records = TokenUsage.objects.count()

    if total_records == 0:
        print("📊 No token usage data found in database.")
        print()
        print("💡 Token tracking is ready - data will appear after:")
        print("   • AI code reviews run in CI/CD")
        print("   • Local token tracking submissions")
        print("   • Imported token files from temp/")
        print()
        return

    total_stats = TokenUsage.objects.aggregate(
        total_tokens=Sum('total_tokens'),
        total_prompt=Sum('prompt_tokens'),
        total_completion=Sum('completion_tokens')
    )

    print(f"📊 OVERALL STATISTICS")
    print("-" * 80)
    print(f"   Total Records:      {format_large_number(total_records)}")
    print(f"   Total Tokens:       {format_large_number(total_stats['total_tokens'] or 0)}")
    print(f"   Prompt Tokens:      {format_large_number(total_stats['total_prompt'] or 0)}")
    print(f"   Completion Tokens:  {format_large_number(total_stats['total_completion'] or 0)}")
    print()

    # Current branch statistics
    branch_stats = TokenUsage.objects.filter(git_branch=current_branch).aggregate(
        total_tokens=Sum('total_tokens'),
        total_prompt=Sum('prompt_tokens'),
        total_completion=Sum('completion_tokens'),
        count=Count('id')
    )

    if branch_stats['count'] and branch_stats['count'] > 0:
        print(f"🌳 CURRENT BRANCH: {current_branch}")
        print("-" * 80)
        print(f"   Records:          {format_large_number(branch_stats['count'])}")
        print(f"   Total Tokens:     {format_large_number(branch_stats['total_tokens'] or 0)}")
        print(f"   Prompt Tokens:    {format_large_number(branch_stats['total_prompt'] or 0)}")
        print(f"   Completion:       {format_large_number(branch_stats['total_completion'] or 0)}")

        # Calculate percentage of total
        if total_stats['total_tokens'] and total_stats['total_tokens'] > 0:
            percentage = (branch_stats['total_tokens'] / total_stats['total_tokens']) * 100
            print(f"   % of Total:       {percentage:.1f}%")

        print()
    else:
        print(f"🌳 CURRENT BRANCH: {current_branch}")
        print("-" * 80)
        print(f"   No token usage recorded for this branch yet.")
        print()
        print("💡 Tokens will appear here after:")
        print("   • Committing with auto-tracking enabled")
        print("   • Manually tracking: track-tokens.bat add [tokens] 'notes'")
        print("   • Pushing to GitHub (CI/CD imports automatically)")
        print()

    # Recent activity (last 7 days)
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_stats = TokenUsage.objects.filter(created_at__gte=seven_days_ago).aggregate(
        total_tokens=Sum('total_tokens'),
        count=Count('id')
    )

    if recent_stats['count'] and recent_stats['count'] > 0:
        print(f"📅 LAST 7 DAYS")
        print("-" * 80)
        print(f"   Records:       {format_large_number(recent_stats['count'])}")
        print(f"   Total Tokens:  {format_large_number(recent_stats['total_tokens'] or 0)}")
        print()

    # Branch breakdown
    branch_breakdown = TokenUsage.objects.values('git_branch').annotate(
        total_tokens=Sum('total_tokens'),
        count=Count('id')
    ).order_by('-total_tokens')[:10]

    if branch_breakdown:
        print(f"🌿 TOP BRANCHES BY TOKEN USAGE")
        print("-" * 80)
        for i, branch_data in enumerate(branch_breakdown, 1):
            branch_name = branch_data['git_branch']
            tokens = branch_data['total_tokens']
            count = branch_data['count']
            print(f"   {i:2d}. {branch_name:<30} {format_large_number(tokens):>15} tokens ({count} records)")
        print()

    # Model breakdown
    model_breakdown = TokenUsage.objects.values('model_name').annotate(
        total_tokens=Sum('total_tokens'),
        count=Count('id')
    ).order_by('-total_tokens')

    if model_breakdown:
        print(f"🤖 MODEL BREAKDOWN")
        print("-" * 80)
        for model_data in model_breakdown:
            model_name = model_data['model_name']
            tokens = model_data['total_tokens']
            count = model_data['count']

            # Estimate costs (rough approximations)
            if 'claude' in model_name.lower():
                # Claude Sonnet 4.5: ~$3/M input, ~$15/M output (estimated)
                estimated_cost = (tokens / 1_000_000) * 9  # Average
                cost_str = f" (≈${estimated_cost:.2f})"
            elif 'gpt-4' in model_name.lower():
                # GPT-4: ~$2.50/M input, ~$10/M output (estimated)
                estimated_cost = (tokens / 1_000_000) * 6.25  # Average
                cost_str = f" (≈${estimated_cost:.2f})"
            else:
                cost_str = ""

            print(f"   {model_name:<40} {format_large_number(tokens):>15} tokens ({count} records){cost_str}")
        print()

    # Recent records
    recent_records = TokenUsage.objects.order_by('-created_at')[:5]

    if recent_records:
        print(f"📝 MOST RECENT RECORDS")
        print("-" * 80)
        for record in recent_records:
            timestamp = record.created_at.strftime('%Y-%m-%d %H:%M:%S')
            branch = record.git_branch[:25]
            model = record.model_name.split('-')[0] if '-' in record.model_name else record.model_name
            tokens = format_large_number(record.total_tokens)
            print(f"   {timestamp} | {branch:<25} | {model:<10} | {tokens:>10} tokens")
        print()

    print("=" * 80)
    print()
    print("💡 TIP: Use track-tokens.bat to add local Claude Code session tokens")
    print("   Example: track-tokens.bat add 50000 \"Feature work\"")
    print()


if __name__ == '__main__':
    try:
        generate_report()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error generating report: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

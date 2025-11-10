#!/usr/bin/env python3
"""
Generate Comprehensive Token Metrics Report with Granular Statistics

This script generates a detailed report of token usage across all dimensions:
- Overall statistics and costs
- Branch-level breakdown
- Daily/hourly patterns
- Model and endpoint analysis
- Recent activity with full details
- User attribution (when available)
- Cost estimates with detailed breakdown

Usage:
    python token_metrics/scripts/report-token-metrics.py
"""

import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

# Setup Django environment
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'active_interview_backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'active_interview_project.settings')
import django
django.setup()

from active_interview_app.token_usage_models import TokenUsage
from django.db.models import Sum, Count, Avg, Max, Min, Q
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


def format_number(num):
    """Format large numbers with commas."""
    if num is None:
        return "0"
    return f"{num:,}"


def calculate_cost(prompt_tokens, completion_tokens, model_name):
    """Calculate cost based on token usage and model pricing."""
    if not prompt_tokens or not completion_tokens:
        return 0.0

    # Pricing per 1M tokens
    if 'claude-sonnet-4-5' in model_name.lower():
        # Claude Sonnet 4.5 pricing (Jan 2025)
        prompt_cost = (prompt_tokens / 1_000_000) * 3.00  # $3/M
        completion_cost = (completion_tokens / 1_000_000) * 15.00  # $15/M
    elif 'claude-sonnet-3-5' in model_name.lower():
        # Claude Sonnet 3.5 pricing
        prompt_cost = (prompt_tokens / 1_000_000) * 3.00
        completion_cost = (completion_tokens / 1_000_000) * 15.00
    elif 'gpt-4' in model_name.lower():
        # GPT-4 pricing
        prompt_cost = (prompt_tokens / 1_000_000) * 2.50
        completion_cost = (completion_tokens / 1_000_000) * 10.00
    elif 'gpt-3.5' in model_name.lower():
        # GPT-3.5 Turbo pricing
        prompt_cost = (prompt_tokens / 1_000_000) * 0.50
        completion_cost = (completion_tokens / 1_000_000) * 1.50
    else:
        # Default estimate
        prompt_cost = (prompt_tokens / 1_000_000) * 3.00
        completion_cost = (completion_tokens / 1_000_000) * 15.00

    return prompt_cost + completion_cost


def generate_report():
    """Generate comprehensive token usage report with granular statistics."""
    current_branch = get_current_branch()

    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "🤖 TOKEN USAGE METRICS REPORT" + " " * 29 + "║")
    print("║" + " " * 15 + "Comprehensive Statistics & Cost Analysis" + " " * 23 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    # Check if we have any data
    total_records = TokenUsage.objects.count()

    if total_records == 0:
        print("📊 No token usage data found in database.")
        print()
        print("💡 Token tracking is ready - data will appear after:")
        print("   • AI code reviews run in CI/CD")
        print("   • Local token tracking submissions")
        print("   • Imported token files from temp/")
        print()
        print("🚀 Quick Start:")
        print("   track-tokens.bat --add         # Interactive tracking")
        print("   track-tokens.bat --help        # See all options")
        print()
        return

    # ========================================================================
    # SECTION 1: OVERALL STATISTICS
    # ========================================================================
    print("═" * 80)
    print("📊 OVERALL STATISTICS")
    print("═" * 80)

    total_stats = TokenUsage.objects.aggregate(
        total_tokens=Sum('total_tokens'),
        total_prompt=Sum('prompt_tokens'),
        total_completion=Sum('completion_tokens'),
        avg_tokens=Avg('total_tokens'),
        max_tokens=Max('total_tokens'),
        min_tokens=Min('total_tokens'),
        count=Count('id')
    )

    total_cost = calculate_cost(
        total_stats['total_prompt'] or 0,
        total_stats['total_completion'] or 0,
        'claude-sonnet-4-5-20250929'  # Default model for estimation
    )

    print(f"  📝 Total Records:        {format_number(total_stats['count'])}")
    print(f"  🔢 Total Tokens:         {format_number(total_stats['total_tokens'] or 0)}")
    print(f"  📥 Prompt Tokens:        {format_number(total_stats['total_prompt'] or 0)}")
    print(f"  📤 Completion Tokens:    {format_number(total_stats['total_completion'] or 0)}")
    print(f"  💰 Estimated Cost:       ${total_cost:.4f}")
    print()
    print(f"  📊 Average per Session:  {format_number(int(total_stats['avg_tokens'] or 0))} tokens")
    print(f"  📈 Largest Session:      {format_number(total_stats['max_tokens'] or 0)} tokens")
    print(f"  📉 Smallest Session:     {format_number(total_stats['min_tokens'] or 0)} tokens")
    print()

    # ========================================================================
    # SECTION 2: CURRENT BRANCH DETAILED STATISTICS
    # ========================================================================
    print("═" * 80)
    print(f"🌳 CURRENT BRANCH: {current_branch}")
    print("═" * 80)

    branch_records = TokenUsage.objects.filter(git_branch=current_branch)
    branch_stats = branch_records.aggregate(
        total_tokens=Sum('total_tokens'),
        total_prompt=Sum('prompt_tokens'),
        total_completion=Sum('completion_tokens'),
        avg_tokens=Avg('total_tokens'),
        count=Count('id'),
        first_use=Min('created_at'),
        last_use=Max('created_at')
    )

    if branch_stats['count'] and branch_stats['count'] > 0:
        branch_cost = calculate_cost(
            branch_stats['total_prompt'] or 0,
            branch_stats['total_completion'] or 0,
            'claude-sonnet-4-5-20250929'
        )

        print(f"  📊 Sessions:             {format_number(branch_stats['count'])}")
        print(f"  🔢 Total Tokens:         {format_number(branch_stats['total_tokens'] or 0)}")
        print(f"  📥 Prompt Tokens:        {format_number(branch_stats['total_prompt'] or 0)}")
        print(f"  📤 Completion Tokens:    {format_number(branch_stats['total_completion'] or 0)}")
        print(f"  💰 Estimated Cost:       ${branch_cost:.4f}")
        print(f"  📊 Avg per Session:      {format_number(int(branch_stats['avg_tokens'] or 0))} tokens")

        if total_stats['total_tokens'] and total_stats['total_tokens'] > 0:
            percentage = (branch_stats['total_tokens'] / total_stats['total_tokens']) * 100
            print(f"  📈 % of Total Usage:     {percentage:.1f}%")

        if branch_stats['first_use']:
            print(f"  📅 First Use:            {branch_stats['first_use'].strftime('%Y-%m-%d %H:%M:%S')}")
        if branch_stats['last_use']:
            print(f"  📅 Last Use:             {branch_stats['last_use'].strftime('%Y-%m-%d %H:%M:%S')}")

        # Branch activity breakdown by day
        print()
        print("  📅 Daily Activity on This Branch:")
        daily_breakdown = branch_records.extra(
            select={'day': 'DATE(created_at)'}
        ).values('day').annotate(
            tokens=Sum('total_tokens'),
            count=Count('id')
        ).order_by('-day')[:7]

        if daily_breakdown:
            for day_data in daily_breakdown:
                day = day_data['day']
                tokens = day_data['tokens']
                count = day_data['count']
                cost = calculate_cost(tokens * 0.8, tokens * 0.2, 'claude-sonnet-4-5-20250929')
                print(f"     {day}:  {format_number(tokens):>12} tokens  ({count} sessions)  ${cost:.4f}")

        print()
    else:
        print(f"  ⚠️  No token usage recorded for this branch yet.")
        print()
        print("  💡 Tokens will appear here after:")
        print("     • Committing with auto-tracking enabled")
        print("     • Manually tracking: track-tokens.bat --add")
        print("     • Pushing to GitHub (CI/CD imports automatically)")
        print()

    # ========================================================================
    # SECTION 3: TIME-BASED ANALYSIS
    # ========================================================================
    print("═" * 80)
    print("📅 TIME-BASED ANALYSIS")
    print("═" * 80)

    # Last 24 hours
    one_day_ago = timezone.now() - timedelta(days=1)
    day_stats = TokenUsage.objects.filter(created_at__gte=one_day_ago).aggregate(
        total_tokens=Sum('total_tokens'),
        count=Count('id')
    )

    if day_stats['count'] and day_stats['count'] > 0:
        day_cost = calculate_cost(
            day_stats['total_tokens'] * 0.8,
            day_stats['total_tokens'] * 0.2,
            'claude-sonnet-4-5-20250929'
        )
        print(f"  🕐 Last 24 Hours:")
        print(f"     Sessions:  {format_number(day_stats['count'])}")
        print(f"     Tokens:    {format_number(day_stats['total_tokens'] or 0)}")
        print(f"     Cost:      ${day_cost:.4f}")
        print()

    # Last 7 days
    seven_days_ago = timezone.now() - timedelta(days=7)
    week_stats = TokenUsage.objects.filter(created_at__gte=seven_days_ago).aggregate(
        total_tokens=Sum('total_tokens'),
        total_prompt=Sum('prompt_tokens'),
        total_completion=Sum('completion_tokens'),
        count=Count('id')
    )

    if week_stats['count'] and week_stats['count'] > 0:
        week_cost = calculate_cost(
            week_stats['total_prompt'] or 0,
            week_stats['total_completion'] or 0,
            'claude-sonnet-4-5-20250929'
        )
        print(f"  📅 Last 7 Days:")
        print(f"     Sessions:  {format_number(week_stats['count'])}")
        print(f"     Tokens:    {format_number(week_stats['total_tokens'] or 0)}")
        print(f"     Cost:      ${week_cost:.4f}")

        # Daily average
        avg_daily = (week_stats['total_tokens'] or 0) / 7
        avg_cost_daily = week_cost / 7
        print(f"     Daily Avg: {format_number(int(avg_daily))} tokens (${avg_cost_daily:.4f}/day)")

        # Monthly projection
        monthly_projection = avg_daily * 30
        monthly_cost = avg_cost_daily * 30
        print(f"     📊 Monthly Projection: {format_number(int(monthly_projection))} tokens (${monthly_cost:.2f}/month)")
        print()

    # Last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    month_stats = TokenUsage.objects.filter(created_at__gte=thirty_days_ago).aggregate(
        total_tokens=Sum('total_tokens'),
        count=Count('id')
    )

    if month_stats['count'] and month_stats['count'] > 0:
        month_cost = calculate_cost(
            month_stats['total_tokens'] * 0.8,
            month_stats['total_tokens'] * 0.2,
            'claude-sonnet-4-5-20250929'
        )
        print(f"  📅 Last 30 Days:")
        print(f"     Sessions:  {format_number(month_stats['count'])}")
        print(f"     Tokens:    {format_number(month_stats['total_tokens'] or 0)}")
        print(f"     Cost:      ${month_cost:.4f}")
        print()

    # ========================================================================
    # SECTION 4: BRANCH BREAKDOWN
    # ========================================================================
    print("═" * 80)
    print("🌿 BRANCH BREAKDOWN (Top 10)")
    print("═" * 80)
    print()

    branch_breakdown = TokenUsage.objects.values('git_branch').annotate(
        total_tokens=Sum('total_tokens'),
        prompt_tokens=Sum('prompt_tokens'),
        completion_tokens=Sum('completion_tokens'),
        count=Count('id'),
        last_used=Max('created_at')
    ).order_by('-total_tokens')[:10]

    if branch_breakdown:
        print(f"  {'Rank':<6} {'Branch':<35} {'Tokens':>15} {'Sessions':>10} {'Cost':>12}")
        print(f"  {'-'*6} {'-'*35} {'-'*15} {'-'*10} {'-'*12}")

        for i, branch_data in enumerate(branch_breakdown, 1):
            branch_name = branch_data['git_branch'][:34]
            tokens = branch_data['total_tokens']
            count = branch_data['count']
            cost = calculate_cost(
                branch_data['prompt_tokens'] or 0,
                branch_data['completion_tokens'] or 0,
                'claude-sonnet-4-5-20250929'
            )

            # Highlight current branch
            marker = "→" if branch_name == current_branch[:34] else " "
            print(f"  {marker}{i:<5} {branch_name:<35} {format_number(tokens):>15} {count:>10} ${cost:>11.4f}")
        print()

    # ========================================================================
    # SECTION 5: MODEL & ENDPOINT BREAKDOWN
    # ========================================================================
    print("═" * 80)
    print("🤖 MODEL & ENDPOINT ANALYSIS")
    print("═" * 80)
    print()

    # Model breakdown
    model_breakdown = TokenUsage.objects.values('model_name').annotate(
        total_tokens=Sum('total_tokens'),
        prompt_tokens=Sum('prompt_tokens'),
        completion_tokens=Sum('completion_tokens'),
        count=Count('id')
    ).order_by('-total_tokens')

    if model_breakdown:
        print("  📱 By Model:")
        print(f"     {'Model':<45} {'Tokens':>15} {'Sessions':>10} {'Cost':>12}")
        print(f"     {'-'*45} {'-'*15} {'-'*10} {'-'*12}")

        for model_data in model_breakdown:
            model_name = model_data['model_name'][:44]
            tokens = model_data['total_tokens']
            count = model_data['count']
            cost = calculate_cost(
                model_data['prompt_tokens'] or 0,
                model_data['completion_tokens'] or 0,
                model_name
            )

            print(f"     {model_name:<45} {format_number(tokens):>15} {count:>10} ${cost:>11.4f}")
        print()

    # Endpoint breakdown
    endpoint_breakdown = TokenUsage.objects.values('endpoint').annotate(
        total_tokens=Sum('total_tokens'),
        count=Count('id'),
        avg_tokens=Avg('total_tokens')
    ).order_by('-total_tokens')

    if endpoint_breakdown:
        print("  🔗 By Endpoint:")
        print(f"     {'Endpoint':<30} {'Total Tokens':>15} {'Sessions':>10} {'Avg/Session':>15}")
        print(f"     {'-'*30} {'-'*15} {'-'*10} {'-'*15}")

        for endpoint_data in endpoint_breakdown:
            endpoint = endpoint_data['endpoint'][:29]
            tokens = endpoint_data['total_tokens']
            count = endpoint_data['count']
            avg = endpoint_data['avg_tokens']

            print(f"     {endpoint:<30} {format_number(tokens):>15} {count:>10} {format_number(int(avg)):>15}")
        print()

    # ========================================================================
    # SECTION 6: RECENT ACTIVITY (Last 10 sessions)
    # ========================================================================
    print("═" * 80)
    print("📝 RECENT ACTIVITY (Last 10 Sessions)")
    print("═" * 80)
    print()

    recent_records = TokenUsage.objects.select_related('user').order_by('-created_at')[:10]

    if recent_records:
        print(f"  {'Timestamp':<20} {'Branch':<25} {'Model':<12} {'Endpoint':<15} {'Tokens':>12} {'Cost':>10}")
        print(f"  {'-'*20} {'-'*25} {'-'*12} {'-'*15} {'-'*12} {'-'*10}")

        for record in recent_records:
            timestamp = record.created_at.strftime('%Y-%m-%d %H:%M:%S')
            branch = record.git_branch[:24]
            model = (record.model_name.split('-')[0] if '-' in record.model_name else record.model_name)[:11]
            endpoint = record.endpoint[:14]
            tokens = format_number(record.total_tokens)
            cost = calculate_cost(
                record.prompt_tokens or 0,
                record.completion_tokens or 0,
                record.model_name
            )

            print(f"  {timestamp:<20} {branch:<25} {model:<12} {endpoint:<15} {tokens:>12} ${cost:>9.4f}")
        print()

    # ========================================================================
    # SECTION 7: COST ANALYSIS
    # ========================================================================
    print("═" * 80)
    print("💰 DETAILED COST ANALYSIS")
    print("═" * 80)
    print()

    # Calculate costs by model with detailed breakdown
    for model_data in model_breakdown:
        model_name = model_data['model_name']
        prompt_tokens = model_data['prompt_tokens'] or 0
        completion_tokens = model_data['completion_tokens'] or 0

        cost = calculate_cost(prompt_tokens, completion_tokens, model_name)

        # Get pricing info
        if 'claude-sonnet-4-5' in model_name.lower():
            prompt_rate, completion_rate = 3.00, 15.00
        elif 'claude-sonnet-3-5' in model_name.lower():
            prompt_rate, completion_rate = 3.00, 15.00
        elif 'gpt-4' in model_name.lower():
            prompt_rate, completion_rate = 2.50, 10.00
        elif 'gpt-3.5' in model_name.lower():
            prompt_rate, completion_rate = 0.50, 1.50
        else:
            prompt_rate, completion_rate = 3.00, 15.00

        prompt_cost = (prompt_tokens / 1_000_000) * prompt_rate
        completion_cost = (completion_tokens / 1_000_000) * completion_rate

        print(f"  🤖 {model_name}")
        print(f"     Prompt:      {format_number(prompt_tokens):>15} tokens × ${prompt_rate}/M = ${prompt_cost:.4f}")
        print(f"     Completion:  {format_number(completion_tokens):>15} tokens × ${completion_rate}/M = ${completion_cost:.4f}")
        print(f"     Total Cost:  ${cost:.4f}")
        print()

    # Total cost summary
    print(f"  💵 TOTAL ESTIMATED COST: ${total_cost:.4f}")
    print()

    # ========================================================================
    # SECTION 8: INSIGHTS & RECOMMENDATIONS
    # ========================================================================
    print("═" * 80)
    print("💡 INSIGHTS & RECOMMENDATIONS")
    print("═" * 80)
    print()

    # Find most expensive branch
    if branch_breakdown:
        most_expensive = branch_breakdown[0]
        most_expensive_cost = calculate_cost(
            most_expensive['prompt_tokens'] or 0,
            most_expensive['completion_tokens'] or 0,
            'claude-sonnet-4-5-20250929'
        )
        print(f"  📊 Most Active Branch:")
        print(f"     {most_expensive['git_branch']} - {format_number(most_expensive['total_tokens'])} tokens (${most_expensive_cost:.4f})")
        print()

    # Check if usage is increasing
    if week_stats['count'] and week_stats['count'] > 0:
        week_avg_daily = (week_stats['total_tokens'] or 0) / 7

        # Compare to previous week
        fourteen_days_ago = timezone.now() - timedelta(days=14)
        prev_week_stats = TokenUsage.objects.filter(
            created_at__gte=fourteen_days_ago,
            created_at__lt=seven_days_ago
        ).aggregate(
            total_tokens=Sum('total_tokens')
        )

        if prev_week_stats['total_tokens']:
            prev_week_avg = prev_week_stats['total_tokens'] / 7
            if week_avg_daily > prev_week_avg * 1.2:
                increase_pct = ((week_avg_daily - prev_week_avg) / prev_week_avg) * 100
                print(f"  📈 Usage Trend: INCREASING (+{increase_pct:.1f}% vs previous week)")
                print(f"     Current week avg:  {format_number(int(week_avg_daily))} tokens/day")
                print(f"     Previous week avg: {format_number(int(prev_week_avg))} tokens/day")
                print()
            elif week_avg_daily < prev_week_avg * 0.8:
                decrease_pct = ((prev_week_avg - week_avg_daily) / prev_week_avg) * 100
                print(f"  📉 Usage Trend: DECREASING (-{decrease_pct:.1f}% vs previous week)")
                print(f"     Current week avg:  {format_number(int(week_avg_daily))} tokens/day")
                print(f"     Previous week avg: {format_number(int(prev_week_avg))} tokens/day")
                print()
            else:
                print(f"  ➡️  Usage Trend: STABLE (±20% vs previous week)")
                print(f"     Weekly avg: {format_number(int(week_avg_daily))} tokens/day")
                print()

    # ========================================================================
    # FOOTER
    # ========================================================================
    print("═" * 80)
    print()
    print("📚 QUICK REFERENCE")
    print("  • Track tokens:     track-tokens.bat --add")
    print("  • View trends:      track-tokens.bat --trends")
    print("  • Export data:      track-tokens.bat --export monthly.csv")
    print("  • Generate report:  track-tokens.bat --dashboard")
    print("  • Full help:        track-tokens.bat --help")
    print()
    print("🔗 Documentation:")
    print("  • Quick Start:      token_metrics/QUICK_START_CLAUDE_TRACKING.md")
    print("  • Bash Scripts:     token_metrics/BASH_SCRIPTS_GUIDE.md")
    print("  • Time Series:      token_metrics/TRACKING_OVER_TIME_GUIDE.md")
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + " " * 22 + "📊 End of Token Metrics Report" + " " * 26 + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")
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

#!/usr/bin/env python3
"""
Token Metrics Reporter

Reports token usage metrics for Claude and OpenAI API calls.
Used in CI/CD pipeline to show token consumption on merge to main.
"""

import os
import sys
import subprocess
import django
from datetime import datetime, timedelta

# Setup Django environment
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'active_interview_backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'active_interview_project.settings')
django.setup()

from active_interview_app.token_usage_models import TokenUsage
from active_interview_app.merge_stats_models import MergeTokenStats
from django.db.models import Sum


def get_git_info():
    """Get current git branch and commit information."""
    try:
        branch = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5
        ).stdout.strip()

        commit_sha = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5
        ).stdout.strip()

        # Check if merging to main
        target_branch = os.environ.get('GITHUB_BASE_REF', 'main')

        return {
            'source_branch': branch,
            'target_branch': target_branch,
            'commit_sha': commit_sha
        }
    except Exception as e:
        print(f"Warning: Could not get git info: {e}")
        return {
            'source_branch': os.environ.get('GITHUB_HEAD_REF', 'unknown'),
            'target_branch': os.environ.get('GITHUB_BASE_REF', 'main'),
            'commit_sha': os.environ.get('GITHUB_SHA', 'unknown')
        }


def format_cost(cost):
    """Format cost as USD string."""
    return f"${cost:.4f}"


def print_branch_summary(branch_name):
    """Print detailed token usage summary for a branch."""
    summary = TokenUsage.get_branch_summary(branch_name)

    print(f"\n{'='*70}")
    print(f"TOKEN USAGE REPORT - Branch: {branch_name}")
    print(f"{'='*70}\n")

    if summary['total_requests'] == 0:
        print("ℹ️  No API calls tracked for this branch")
        return summary

    print(f"📊 Total API Requests: {summary['total_requests']}")
    print(f"🔢 Total Tokens Used: {summary['total_tokens']:,}")
    print(f"💰 Estimated Cost: {format_cost(summary['total_cost'])}\n")

    if summary['by_model']:
        print("📈 Breakdown by Model:")
        print(f"{'-'*70}")

        for model_name, stats in summary['by_model'].items():
            print(f"\n  Model: {model_name}")
            print(f"  ├─ Requests: {stats['requests']}")
            print(f"  ├─ Prompt Tokens: {stats['prompt_tokens']:,}")
            print(f"  ├─ Completion Tokens: {stats['completion_tokens']:,}")
            print(f"  ├─ Total Tokens: {stats['total_tokens']:,}")
            print(f"  └─ Cost: {format_cost(stats['cost'])}")

    print(f"\n{'='*70}\n")
    return summary


def print_comparison_summary(current_branch, target_branch='main'):
    """Print comparison between current branch and target branch."""
    current_summary = TokenUsage.get_branch_summary(current_branch)
    target_summary = TokenUsage.get_branch_summary(target_branch)

    print(f"\n{'='*70}")
    print(f"COMPARISON: {current_branch} vs {target_branch}")
    print(f"{'='*70}\n")

    # Calculate differences
    token_diff = current_summary['total_tokens'] - target_summary['total_tokens']
    cost_diff = current_summary['total_cost'] - target_summary['total_cost']
    request_diff = current_summary['total_requests'] - target_summary['total_requests']

    print(f"📊 API Requests: {current_summary['total_requests']} "
          f"({request_diff:+d} vs {target_branch})")
    print(f"🔢 Total Tokens: {current_summary['total_tokens']:,} "
          f"({token_diff:+,d} vs {target_branch})")
    print(f"💰 Cost: {format_cost(current_summary['total_cost'])} "
          f"({format_cost(cost_diff).replace('$', '$+' if cost_diff >= 0 else '$')} "
          f"vs {target_branch})")

    print(f"\n{'='*70}\n")


def print_recent_activity(branch_name, days=7):
    """Print recent token usage activity."""
    since_date = datetime.now() - timedelta(days=days)
    recent_records = TokenUsage.objects.filter(
        git_branch=branch_name,
        created_at__gte=since_date
    ).order_by('-created_at')[:10]

    if not recent_records:
        return

    print(f"\n📅 Recent Activity (Last {days} days - Top 10):")
    print(f"{'-'*70}")

    for record in recent_records:
        timestamp = record.created_at.strftime('%Y-%m-%d %H:%M:%S')
        print(f"  {timestamp} | {record.model_name:30s} | "
              f"{record.total_tokens:6,} tokens | "
              f"{format_cost(record.estimated_cost)}")

    print(f"{'-'*70}\n")


def create_merge_stats_record(git_info):
    """Create MergeTokenStats record for this merge."""
    try:
        source_branch = git_info['source_branch']
        target_branch = git_info['target_branch']
        commit_sha = git_info['commit_sha']

        # Check if already recorded
        if MergeTokenStats.objects.filter(merge_commit_sha=commit_sha).exists():
            print(f"ℹ️  Merge stats already recorded for commit {commit_sha[:8]}")
            return

        # Create the merge stats record
        merge_stats = MergeTokenStats.create_from_branch(
            source_branch=source_branch,
            target_branch=target_branch,
            merge_commit_sha=commit_sha
        )

        if merge_stats:
            print(f"\n✅ Merge stats recorded successfully!")
            print(f"   Source: {source_branch} → Target: {target_branch}")
            print(f"   Commit: {commit_sha[:8]}")

            # Print the breakdown
            breakdown = merge_stats.get_breakdown_summary()
            print(f"\n📊 Merge Summary:")
            print(f"   Claude Tokens: {breakdown['claude_total']:,}")
            print(f"   ChatGPT Tokens: {breakdown['chatgpt_total']:,}")
            print(f"   Total Cost: {format_cost(breakdown['total_cost'])}")
            print(f"\n   Cumulative All-Time:")
            print(f"   Total Tokens: {merge_stats.cumulative_total_tokens:,}")
            print(f"   Total Cost: {format_cost(merge_stats.cumulative_cost)}")

    except Exception as e:
        print(f"⚠️  Warning: Could not create merge stats: {e}")


def print_all_branches_breakdown():
    """Print token usage breakdown for all branches."""
    # Get all unique branches
    all_branches = TokenUsage.objects.values_list('git_branch', flat=True).distinct().order_by('git_branch')

    if not all_branches:
        return

    print(f"\n{'='*70}")
    print(f"TOKEN USAGE BY BRANCH")
    print(f"{'='*70}\n")

    branch_data = []
    total_tokens = 0
    total_cost = 0.0

    for branch in all_branches:
        summary = TokenUsage.get_branch_summary(branch)
        if summary['total_requests'] > 0:
            branch_data.append({
                'branch': branch,
                'requests': summary['total_requests'],
                'tokens': summary['total_tokens'],
                'cost': summary['total_cost']
            })
            total_tokens += summary['total_tokens']
            total_cost += summary['total_cost']

    # Sort by tokens (highest first)
    branch_data.sort(key=lambda x: x['tokens'], reverse=True)

    # Print table header
    print(f"{'Branch':<40} {'Requests':>10} {'Tokens':>15} {'Cost':>12} {'%':>8}")
    print(f"{'-'*70}")

    # Print each branch
    for data in branch_data:
        branch_display = data['branch'][:37] + '...' if len(data['branch']) > 40 else data['branch']
        percentage = (data['tokens'] / total_tokens * 100) if total_tokens > 0 else 0

        print(f"{branch_display:<40} {data['requests']:>10} {data['tokens']:>15,} "
              f"{format_cost(data['cost']):>12} {percentage:>7.1f}%")

    # Print totals
    print(f"{'-'*70}")
    print(f"{'TOTAL':<40} {sum(d['requests'] for d in branch_data):>10} "
          f"{total_tokens:>15,} {format_cost(total_cost):>12} {100.0:>7.1f}%")

    print(f"\n{'='*70}\n")


def print_cumulative_stats():
    """Print cumulative token usage statistics across all merges."""
    all_merges = MergeTokenStats.objects.all().order_by('-merge_date')

    if not all_merges.exists():
        return

    latest = all_merges.first()

    print(f"\n{'='*70}")
    print(f"CUMULATIVE STATISTICS (All Time)")
    print(f"{'='*70}\n")

    print(f"📊 Total Merges Tracked: {all_merges.count()}")
    print(f"🔢 Total Tokens Used: {latest.cumulative_total_tokens:,}")
    print(f"💰 Total Cost: {format_cost(latest.cumulative_cost)}")

    # Breakdown by model
    claude_tokens = latest.cumulative_claude_tokens
    chatgpt_tokens = latest.cumulative_chatgpt_tokens

    print(f"\n📈 Breakdown by Provider:")
    print(f"   Claude: {claude_tokens:,} tokens "
          f"({claude_tokens / latest.cumulative_total_tokens * 100:.1f}%)")
    print(f"   ChatGPT: {chatgpt_tokens:,} tokens "
          f"({chatgpt_tokens / latest.cumulative_total_tokens * 100:.1f}%)")

    print(f"\n{'='*70}\n")


def main():
    """Main execution function."""
    print("\n" + "="*70)
    print(" "*20 + "TOKEN USAGE METRICS REPORT")
    print("="*70)

    # Get git information
    git_info = get_git_info()
    source_branch = git_info['source_branch']
    target_branch = git_info['target_branch']

    print(f"\n🌳 Source Branch: {source_branch}")
    print(f"🎯 Target Branch: {target_branch}")
    print(f"📝 Commit: {git_info['commit_sha'][:8]}\n")

    # Print current branch summary
    print_branch_summary(source_branch)

    # Print recent activity
    print_recent_activity(source_branch, days=7)

    # Print breakdown by all branches
    print_all_branches_breakdown()

    # If merging to main, create merge stats and show comparison
    is_merging_to_main = (
        target_branch in ['main', 'master'] or
        os.environ.get('GITHUB_EVENT_NAME') == 'push' and
        source_branch in ['main', 'master']
    )

    if is_merging_to_main:
        print(f"\n🔀 Detected merge to {target_branch}")

        # Create merge stats record
        create_merge_stats_record(git_info)

        # Show cumulative statistics
        print_cumulative_stats()

    # Always show comparison if different branches
    if source_branch != target_branch:
        print_comparison_summary(source_branch, target_branch)

    print("\n" + "="*70)
    print("Report generated: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("="*70 + "\n")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error generating token metrics report: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

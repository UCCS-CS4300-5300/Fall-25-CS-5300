#!/usr/bin/env python3
"""
Token Usage Trend Analysis

Analyzes historical token usage data to show trends, patterns, and insights.
Useful for tracking your Claude Code usage over time.

Usage:
    python token_metrics/scripts/analyze-token-trends.py
    python token_metrics/scripts/analyze-token-trends.py --days 30
    python token_metrics/scripts/analyze-token-trends.py --export-csv
    python token_metrics/scripts/analyze-token-trends.py --by-branch
"""

import os
import sys
import json
import argparse
import csv
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import subprocess


def get_repo_root():
    """Get repository root directory."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return os.getcwd()


def load_all_tracking_data():
    """Load all local tracking data from all branches."""
    repo_root = get_repo_root()
    tracking_dir = os.path.join(repo_root, 'token_metrics', 'local_tracking')

    if not os.path.exists(tracking_dir):
        return {}

    all_data = {}

    for filename in os.listdir(tracking_dir):
        if filename.startswith('tokens_') and filename.endswith('.json'):
            filepath = os.path.join(tracking_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    branch_name = data.get('branch', 'unknown')
                    all_data[branch_name] = data
            except Exception as e:
                print(f"Warning: Could not load {filename}: {e}", file=sys.stderr)

    return all_data


def load_temp_files():
    """Load all temp token files for additional data."""
    repo_root = get_repo_root()
    temp_dir = os.path.join(repo_root, 'temp')

    if not os.path.exists(temp_dir):
        return []

    records = []

    for filename in os.listdir(temp_dir):
        if filename.startswith('claude_local_') and filename.endswith('.json'):
            filepath = os.path.join(temp_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    record = json.load(f)
                    records.append(record)
            except Exception:
                pass

    return records


def parse_datetime(dt_string):
    """Parse ISO datetime string."""
    try:
        return datetime.fromisoformat(dt_string)
    except:
        return None


def get_sessions_in_range(sessions, days):
    """Filter sessions to last N days."""
    if days == 0:  # All time
        return sessions

    cutoff = datetime.now() - timedelta(days=days)
    filtered = []

    for session in sessions:
        dt = parse_datetime(session.get('timestamp', ''))
        if dt and dt >= cutoff:
            filtered.append(session)

    return filtered


def calculate_daily_totals(sessions):
    """Group sessions by day and calculate totals."""
    daily = defaultdict(lambda: {'tokens': 0, 'sessions': 0})

    for session in sessions:
        dt = parse_datetime(session.get('timestamp', ''))
        if dt:
            date_key = dt.strftime('%Y-%m-%d')
            daily[date_key]['tokens'] += session.get('tokens', 0)
            daily[date_key]['sessions'] += 1

    return dict(daily)


def calculate_weekly_totals(sessions):
    """Group sessions by week and calculate totals."""
    weekly = defaultdict(lambda: {'tokens': 0, 'sessions': 0})

    for session in sessions:
        dt = parse_datetime(session.get('timestamp', ''))
        if dt:
            # Get Monday of that week
            week_start = dt - timedelta(days=dt.weekday())
            week_key = week_start.strftime('%Y-%m-%d')
            weekly[week_key]['tokens'] += session.get('tokens', 0)
            weekly[week_key]['sessions'] += 1

    return dict(weekly)


def estimate_cost(tokens):
    """Estimate cost for Claude Sonnet 4.5 tokens."""
    # Assume 80/20 split (prompt/completion)
    prompt_tokens = tokens * 0.8
    completion_tokens = tokens * 0.2

    prompt_cost = (prompt_tokens / 1000) * 0.003
    completion_cost = (completion_tokens / 1000) * 0.015

    return prompt_cost + completion_cost


def print_summary_stats(all_data, days):
    """Print summary statistics."""
    total_tokens = 0
    total_sessions = 0
    branches_count = len(all_data)

    # Collect all sessions
    all_sessions = []
    for branch_data in all_data.values():
        sessions = branch_data.get('sessions', [])
        all_sessions.extend(sessions)

    # Filter by date range
    filtered_sessions = get_sessions_in_range(all_sessions, days)

    for session in filtered_sessions:
        total_tokens += session.get('tokens', 0)
        total_sessions += 1

    period = f"Last {days} days" if days > 0 else "All time"

    print("\n" + "="*70)
    print(f"📊 CLAUDE CODE TOKEN USAGE ANALYSIS - {period}")
    print("="*70)
    print()
    print(f"🌳 Branches tracked:        {branches_count}")
    print(f"📝 Total sessions:          {total_sessions:,}")
    print(f"🔢 Total tokens:            {total_tokens:,}")
    print(f"💰 Estimated cost:          ${estimate_cost(total_tokens):.4f}")

    if total_sessions > 0:
        avg_per_session = total_tokens / total_sessions
        print(f"📊 Average per session:     {avg_per_session:,.0f} tokens")

    print()


def print_daily_breakdown(all_data, days):
    """Print daily token usage breakdown."""
    # Collect all sessions
    all_sessions = []
    for branch_data in all_data.values():
        sessions = branch_data.get('sessions', [])
        all_sessions.extend(sessions)

    # Filter and calculate
    filtered_sessions = get_sessions_in_range(all_sessions, days)
    daily = calculate_daily_totals(filtered_sessions)

    if not daily:
        return

    print("="*70)
    print("📅 DAILY USAGE BREAKDOWN")
    print("="*70)
    print()
    print(f"{'Date':<12} {'Sessions':>10} {'Tokens':>15} {'Cost':>12}")
    print("-"*70)

    # Sort by date (most recent first)
    for date in sorted(daily.keys(), reverse=True):
        stats = daily[date]
        tokens = stats['tokens']
        cost = estimate_cost(tokens)
        print(f"{date:<12} {stats['sessions']:>10} {tokens:>15,} ${cost:>11.4f}")

    print()


def print_weekly_trends(all_data, days):
    """Print weekly trends."""
    # Collect all sessions
    all_sessions = []
    for branch_data in all_data.values():
        sessions = branch_data.get('sessions', [])
        all_sessions.extend(sessions)

    # Filter and calculate
    filtered_sessions = get_sessions_in_range(all_sessions, days)
    weekly = calculate_weekly_totals(filtered_sessions)

    if not weekly:
        return

    print("="*70)
    print("📊 WEEKLY TRENDS")
    print("="*70)
    print()
    print(f"{'Week Starting':<15} {'Sessions':>10} {'Tokens':>15} {'Cost':>12}")
    print("-"*70)

    for week in sorted(weekly.keys(), reverse=True):
        stats = weekly[week]
        tokens = stats['tokens']
        cost = estimate_cost(tokens)
        print(f"{week:<15} {stats['sessions']:>10} {tokens:>15,} ${cost:>11.4f}")

    print()


def print_branch_breakdown(all_data):
    """Print per-branch breakdown."""
    if not all_data:
        return

    print("="*70)
    print("🌳 USAGE BY BRANCH")
    print("="*70)
    print()
    print(f"{'Branch':<30} {'Sessions':>10} {'Tokens':>15} {'Cost':>12}")
    print("-"*70)

    # Sort by tokens (descending)
    sorted_branches = sorted(
        all_data.items(),
        key=lambda x: x[1].get('total_tokens', 0),
        reverse=True
    )

    for branch_name, data in sorted_branches:
        tokens = data.get('total_tokens', 0)
        sessions = len(data.get('sessions', []))
        cost = estimate_cost(tokens)

        # Truncate long branch names
        display_name = branch_name if len(branch_name) <= 30 else branch_name[:27] + '...'

        print(f"{display_name:<30} {sessions:>10} {tokens:>15,} ${cost:>11.4f}")

    print()


def export_to_csv(all_data, output_file):
    """Export all session data to CSV."""
    rows = []

    for branch_name, branch_data in all_data.items():
        for session in branch_data.get('sessions', []):
            dt = parse_datetime(session.get('timestamp', ''))
            date_str = dt.strftime('%Y-%m-%d %H:%M:%S') if dt else ''
            tokens = session.get('tokens', 0)

            rows.append({
                'timestamp': date_str,
                'branch': branch_name,
                'tokens': tokens,
                'estimated_cost': f"{estimate_cost(tokens):.4f}",
                'notes': session.get('notes', '')
            })

    # Sort by timestamp
    rows.sort(key=lambda x: x['timestamp'], reverse=True)

    # Write CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'branch', 'tokens', 'estimated_cost', 'notes'])
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def export_to_json(all_data, output_file):
    """Export analysis data to JSON for visualization."""
    # Collect all sessions
    all_sessions = []
    for branch_name, branch_data in all_data.items():
        for session in branch_data.get('sessions', []):
            session_copy = session.copy()
            session_copy['branch'] = branch_name
            all_sessions.append(session_copy)

    # Calculate various aggregations
    daily = calculate_daily_totals(all_sessions)
    weekly = calculate_weekly_totals(all_sessions)

    # Prepare export data
    export_data = {
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_branches': len(all_data),
            'total_sessions': len(all_sessions),
            'total_tokens': sum(s.get('tokens', 0) for s in all_sessions),
            'total_cost': sum(estimate_cost(s.get('tokens', 0)) for s in all_sessions)
        },
        'daily_breakdown': daily,
        'weekly_breakdown': weekly,
        'by_branch': {
            name: {
                'total_tokens': data.get('total_tokens', 0),
                'session_count': len(data.get('sessions', [])),
                'estimated_cost': estimate_cost(data.get('total_tokens', 0))
            }
            for name, data in all_data.items()
        },
        'sessions': all_sessions
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2)

    return export_data


def print_insights(all_data, days):
    """Print insights and recommendations."""
    # Collect all sessions
    all_sessions = []
    for branch_data in all_data.values():
        sessions = branch_data.get('sessions', [])
        all_sessions.extend(sessions)

    filtered_sessions = get_sessions_in_range(all_sessions, days)

    if not filtered_sessions:
        return

    print("="*70)
    print("💡 INSIGHTS")
    print("="*70)
    print()

    # Find peak usage day
    daily = calculate_daily_totals(filtered_sessions)
    if daily:
        peak_day = max(daily.items(), key=lambda x: x[1]['tokens'])
        print(f"📈 Peak usage day:         {peak_day[0]} ({peak_day[1]['tokens']:,} tokens)")

    # Find most active branch
    branch_tokens = defaultdict(int)
    for session in filtered_sessions:
        # Extract branch from temp files
        for branch_name, branch_data in all_data.items():
            if session in branch_data.get('sessions', []):
                branch_tokens[branch_name] += session.get('tokens', 0)
                break

    if branch_tokens:
        top_branch = max(branch_tokens.items(), key=lambda x: x[1])
        print(f"🌳 Most active branch:     {top_branch[0]} ({top_branch[1]:,} tokens)")

    # Calculate average tokens per day
    if daily:
        avg_per_day = sum(d['tokens'] for d in daily.values()) / len(daily)
        print(f"📊 Average per day:        {avg_per_day:,.0f} tokens")

    # Estimate monthly cost at current rate
    if days > 0 and len(filtered_sessions) > 0:
        total_tokens = sum(s.get('tokens', 0) for s in filtered_sessions)
        daily_avg = total_tokens / days
        monthly_projection = daily_avg * 30
        monthly_cost = estimate_cost(monthly_projection)
        print(f"💰 Projected monthly cost: ${monthly_cost:.2f}")

    print()


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description='Analyze Claude Code token usage trends over time'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days to analyze (0 for all time, default: 30)'
    )
    parser.add_argument(
        '--by-branch',
        action='store_true',
        help='Show breakdown by branch'
    )
    parser.add_argument(
        '--daily',
        action='store_true',
        help='Show daily breakdown'
    )
    parser.add_argument(
        '--weekly',
        action='store_true',
        help='Show weekly trends'
    )
    parser.add_argument(
        '--insights',
        action='store_true',
        help='Show insights and recommendations'
    )
    parser.add_argument(
        '--export-csv',
        type=str,
        metavar='FILE',
        help='Export data to CSV file'
    )
    parser.add_argument(
        '--export-json',
        type=str,
        metavar='FILE',
        help='Export analysis to JSON file'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Show all reports (equivalent to --by-branch --daily --weekly --insights)'
    )

    args = parser.parse_args()

    # Load all data
    all_data = load_all_tracking_data()

    if not all_data:
        print("\n⚠️  No token tracking data found.")
        print("\n💡 Start tracking tokens with:")
        print("   python token_metrics/scripts/track-claude-tokens.py --interactive")
        print()
        return 1

    # Print summary
    print_summary_stats(all_data, args.days)

    # Print requested reports
    if args.all or args.by_branch:
        print_branch_breakdown(all_data)

    if args.all or args.daily:
        print_daily_breakdown(all_data, args.days)

    if args.all or args.weekly:
        print_weekly_trends(all_data, args.days)

    if args.all or args.insights:
        print_insights(all_data, args.days)

    # Export if requested
    if args.export_csv:
        count = export_to_csv(all_data, args.export_csv)
        print(f"✅ Exported {count} sessions to {args.export_csv}")
        print()

    if args.export_json:
        export_to_json(all_data, args.export_json)
        print(f"✅ Exported analysis to {args.export_json}")
        print()

    return 0


if __name__ == '__main__':
    sys.exit(main())

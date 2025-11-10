#!/usr/bin/env python3
"""
Generate HTML Dashboard for Token Usage

Creates an interactive HTML dashboard with charts showing token usage over time.
Uses Chart.js for visualization (no external dependencies needed).

Usage:
    python token_metrics/scripts/generate-dashboard.py
    python token_metrics/scripts/generate-dashboard.py --output dashboard.html
    python token_metrics/scripts/generate-dashboard.py --days 30
"""

import os
import sys
import json
import argparse
from datetime import datetime
import subprocess

# Import the analysis functions
sys.path.insert(0, os.path.dirname(__file__))
from analyze_token_trends import (
    load_all_tracking_data,
    calculate_daily_totals,
    calculate_weekly_totals,
    get_sessions_in_range,
    estimate_cost,
    get_repo_root
)


def generate_html_dashboard(all_data, days, output_file):
    """Generate an interactive HTML dashboard."""

    # Collect all sessions
    all_sessions = []
    for branch_data in all_data.values():
        sessions = branch_data.get('sessions', [])
        all_sessions.extend(sessions)

    # Filter by date
    filtered_sessions = get_sessions_in_range(all_sessions, days)

    # Calculate aggregations
    daily = calculate_daily_totals(filtered_sessions)
    weekly = calculate_weekly_totals(filtered_sessions)

    # Prepare chart data
    daily_labels = sorted(daily.keys())
    daily_tokens = [daily[d]['tokens'] for d in daily_labels]
    daily_costs = [estimate_cost(daily[d]['tokens']) for d in daily_labels]

    # Branch data
    branch_names = list(all_data.keys())
    branch_tokens = [all_data[b].get('total_tokens', 0) for b in branch_names]
    branch_costs = [estimate_cost(t) for t in branch_tokens]

    # Calculate summary stats
    total_tokens = sum(s.get('tokens', 0) for s in filtered_sessions)
    total_cost = estimate_cost(total_tokens)
    total_sessions = len(filtered_sessions)
    avg_per_session = total_tokens / total_sessions if total_sessions > 0 else 0

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claude Code Token Usage Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        header {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #666;
            font-size: 14px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .stat-label {{
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}
        .stat-icon {{
            font-size: 40px;
            margin-bottom: 10px;
        }}
        .chart-container {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .chart-title {{
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin-bottom: 20px;
        }}
        canvas {{
            max-height: 400px;
        }}
        .footer {{
            text-align: center;
            color: white;
            margin-top: 30px;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 Claude Code Token Usage Dashboard</h1>
            <p class="subtitle">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | Period: {'Last ' + str(days) + ' days' if days > 0 else 'All time'}</p>
        </header>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">📊</div>
                <div class="stat-label">Total Sessions</div>
                <div class="stat-value">{total_sessions:,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🔢</div>
                <div class="stat-label">Total Tokens</div>
                <div class="stat-value">{total_tokens:,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">💰</div>
                <div class="stat-label">Estimated Cost</div>
                <div class="stat-value">${total_cost:.2f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📈</div>
                <div class="stat-label">Avg per Session</div>
                <div class="stat-value">{avg_per_session:,.0f}</div>
            </div>
        </div>

        <div class="chart-container">
            <div class="chart-title">📅 Daily Token Usage</div>
            <canvas id="dailyChart"></canvas>
        </div>

        <div class="chart-container">
            <div class="chart-title">💵 Daily Cost Trend</div>
            <canvas id="costChart"></canvas>
        </div>

        <div class="chart-container">
            <div class="chart-title">🌳 Usage by Branch</div>
            <canvas id="branchChart"></canvas>
        </div>

        <div class="footer">
            <p>📊 Token Usage Tracking System | Active Interview Project</p>
        </div>
    </div>

    <script>
        // Daily tokens chart
        new Chart(document.getElementById('dailyChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps(daily_labels)},
                datasets: [{{
                    label: 'Tokens Used',
                    data: {json.dumps(daily_tokens)},
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1,
                    fill: true
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{
                        display: true
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            callback: function(value) {{
                                return value.toLocaleString();
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Daily cost chart
        new Chart(document.getElementById('costChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(daily_labels)},
                datasets: [{{
                    label: 'Daily Cost ($)',
                    data: {json.dumps(daily_costs)},
                    backgroundColor: 'rgba(153, 102, 255, 0.6)',
                    borderColor: 'rgb(153, 102, 255)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{
                        display: true
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            callback: function(value) {{
                                return '$' + value.toFixed(2);
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Branch chart
        new Chart(document.getElementById('branchChart'), {{
            type: 'horizontalBar' in Chart ? 'horizontalBar' : 'bar',
            data: {{
                labels: {json.dumps(branch_names)},
                datasets: [{{
                    label: 'Tokens',
                    data: {json.dumps(branch_tokens)},
                    backgroundColor: 'rgba(54, 162, 235, 0.6)',
                    borderColor: 'rgb(54, 162, 235)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{
                        display: true
                    }}
                }},
                scales: {{
                    x: {{
                        beginAtZero: true,
                        ticks: {{
                            callback: function(value) {{
                                return value.toLocaleString();
                            }}
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description='Generate HTML dashboard for token usage'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='token_dashboard.html',
        help='Output HTML file (default: token_dashboard.html)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days to include (0 for all time, default: 30)'
    )

    args = parser.parse_args()

    # Load data
    all_data = load_all_tracking_data()

    if not all_data:
        print("\n⚠️  No token tracking data found.")
        print("\n💡 Start tracking tokens with:")
        print("   python token_metrics/scripts/track-claude-tokens.py --interactive")
        print()
        return 1

    # Generate dashboard
    generate_html_dashboard(all_data, args.days, args.output)

    print(f"\n✅ Dashboard generated: {args.output}")
    print(f"\n💡 Open in browser:")
    print(f"   start {args.output}  # Windows")
    print(f"   open {args.output}   # Mac")
    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())

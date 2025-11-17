#!/usr/bin/env python3
"""
Extract statistics from test sequence logs for research analysis.

Usage:
    python extract_stats.py                    # Analyze all logs
    python extract_stats.py test_sequence_*.md # Analyze specific logs
"""

import yaml
import glob
import sys
from pathlib import Path
from typing import List, Dict


def parse_log(filepath: Path) -> Dict:
    """Parse YAML frontmatter from test sequence log."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract YAML frontmatter between --- markers
    if not content.startswith('---'):
        raise ValueError(f"No YAML frontmatter found in {filepath}")

    parts = content.split('---', 2)
    if len(parts) < 3:
        raise ValueError(f"Invalid frontmatter format in {filepath}")

    metadata = yaml.safe_load(parts[1])
    return metadata


def calculate_stats(logs: List[Dict]) -> Dict:
    """Calculate aggregate statistics from multiple logs."""
    if not logs:
        return {}

    total_sequences = len(logs)
    total_iterations = sum(log['summary']['total_iterations'] for log in logs)

    # First-run failure rates
    first_run_failures = []
    regression_counts = []

    for log in logs:
        first_iteration = log['iterations'][0]
        total_tests = first_iteration['total_tests']

        if total_tests > 0:
            failure_rate = (first_iteration['failed'] / total_tests) * 100
            first_run_failures.append(failure_rate)

        regression_counts.append(first_iteration['regression_failures'])

    # Calculate aggregates
    avg_iterations = total_iterations / total_sequences
    avg_first_run_failure = sum(first_run_failures) / len(first_run_failures) if first_run_failures else 0
    total_regressions = sum(regression_counts)
    sequences_with_regressions = sum(1 for r in regression_counts if r > 0)
    regression_rate = (sequences_with_regressions / total_sequences) * 100 if total_sequences > 0 else 0

    return {
        'total_sequences': total_sequences,
        'avg_iterations': round(avg_iterations, 2),
        'avg_first_run_failure_rate': round(avg_first_run_failure, 2),
        'total_regressions': total_regressions,
        'regression_rate': round(regression_rate, 2),
        'success_rate': round(sum(1 for log in logs if log['summary']['final_status'] == 'success') / total_sequences * 100, 2)
    }


def print_detailed_stats(logs: List[Dict]):
    """Print detailed statistics for each log."""
    print("\n" + "="*70)
    print("DETAILED TEST SEQUENCE ANALYSIS")
    print("="*70 + "\n")

    for log in logs:
        print(f"Feature: {log['feature']}")
        print(f"  Test file: {log['test_file']}")
        print(f"  Iterations: {log['summary']['total_iterations']}")
        print(f"  First-run failure rate: {log['summary']['first_run_failure_rate']}%")
        print(f"  Final status: {log['summary']['final_status']}")

        # Show iteration progression
        print(f"  Progression: ", end="")
        for i, iteration in enumerate(log['iterations']):
            status = "PASS" if iteration['failed'] == 0 else f"FAIL ({iteration['failed']})"
            print(f"Run {iteration['number']}: {status}", end=" -> " if i < len(log['iterations']) - 1 else "\n")

        # Regressions
        total_regressions = sum(it['regression_failures'] for it in log['iterations'])
        if total_regressions > 0:
            print(f"  [!] Regressions detected: {total_regressions}")
        else:
            print(f"  No regressions")

        print()


def main():
    # Get log files
    if len(sys.argv) > 1:
        pattern = sys.argv[1]
    else:
        pattern = 'test_sequence_*.md'

    log_dir = Path(__file__).parent
    log_files = list(log_dir.glob(pattern))

    if not log_files:
        print(f"No log files found matching: {pattern}")
        return

    print(f"Found {len(log_files)} test sequence log(s)")

    # Parse all logs
    logs = []
    for filepath in log_files:
        try:
            metadata = parse_log(filepath)
            logs.append(metadata)
        except Exception as e:
            print(f"Error parsing {filepath.name}: {e}")

    if not logs:
        print("No valid logs could be parsed")
        return

    # Calculate and print aggregate stats
    stats = calculate_stats(logs)

    print("\n" + "="*70)
    print("AGGREGATE STATISTICS")
    print("="*70)
    print(f"\nTotal test sequences analyzed: {stats['total_sequences']}")
    print(f"Average iterations per sequence: {stats['avg_iterations']}")
    print(f"Average first-run failure rate: {stats['avg_first_run_failure_rate']}%")
    print(f"Success rate (all tests passed): {stats['success_rate']}%")
    print(f"Sequences with regressions: {stats['regression_rate']}%")
    print(f"Total regression failures: {stats['total_regressions']}")

    # Print detailed stats
    print_detailed_stats(logs)

    # Research insights
    print("="*70)
    print("RESEARCH INSIGHTS")
    print("="*70)
    print(f"\n[+] Claude Code achieves {stats['success_rate']}% success rate through iteration")
    print(f"[+] Average {stats['avg_iterations']} iterations to get all tests passing")
    print(f"[!] First-run tests fail {stats['avg_first_run_failure_rate']}% of the time")
    print(f"[+] Low regression rate ({stats['regression_rate']}%) indicates careful coding")
    print()


if __name__ == '__main__':
    main()

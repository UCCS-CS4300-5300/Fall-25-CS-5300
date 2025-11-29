#!/usr/bin/env python3
"""
Extract statistics from test sequence logs for research analysis.

Usage:
    python extract_stats.py                    # Analyze all logs
    python extract_stats.py test_sequence_*.md # Analyze specific logs
"""

import yaml
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

    total_tests_all_seq = 0
    total_sequences = len(logs)
    total_iterations = sum(
        log['summary']['total_iterations'] for log in logs
    )

    # First-run failure rates
    first_run_failures = []
    regression_counts = []

    for log in logs:
        first_iteration = log['iterations'][0]
        total_tests = first_iteration['total_tests']
        total_tests_all_seq += total_tests

        if total_tests > 0:
            failure_rate = (first_iteration['failed'] / total_tests) * 100
            first_run_failures.append(failure_rate)

        regression_counts.append(first_iteration['regression_failures'])

    # Calculate aggregates
    avg_iterations = total_iterations / total_sequences
    avg_first_run_failure = (
        sum(first_run_failures) / len(first_run_failures)
        if first_run_failures else 0
    )
    total_regressions = sum(regression_counts)
    sequences_with_regressions = sum(
        1 for r in regression_counts if r > 0
    )
    regression_rate = ((sequences_with_regressions / total_sequences)
                       * 100 if total_sequences > 0 else 0)

    success_count = sum(
        1 for log in logs
        if log['summary']['final_status'] == 'success'
    )
    success_rate = round(
        (success_count / total_sequences * 100), 2
    )

    return {
        'total_sequences': total_sequences,
        'total_tests_all_sequences': total_tests_all_seq,
        'avg_iterations': round(avg_iterations, 2),
        'avg_first_run_failure_rate': round(avg_first_run_failure, 2),
        'total_regressions': total_regressions,
        'regression_rate': round(regression_rate, 2),
        'success_rate': success_rate
    }


def print_detailed_stats(logs: List[Dict]):
    """Print detailed statistics for each log."""
    print("\n" + "="*70)
    print("DETAILED TEST SEQUENCE ANALYSIS")
    print("="*70 + "\n")

    for log in logs:
        print("Feature: {}".format(log['feature']))
        print("  Test file: {}".format(log['test_file']))
        print("  Iterations: {}".format(
            log['summary']['total_iterations']
        ))
        print("  First-run failure rate: {}%".format(
            log['summary']['first_run_failure_rate']
        ))
        print("  Final status: {}".format(
            log['summary']['final_status']
        ))

        # Show iteration progression
        print("  Progression: ", end="")
        for i, iteration in enumerate(log['iterations']):
            status = ("PASS" if iteration['failed'] == 0
                      else "FAIL ({})".format(iteration['failed']))
            separator = " -> " if i < len(log['iterations']) - 1 else "\n"
            print("Run {}: {}".format(iteration['number'], status),
                  end=separator)

        # Regressions
        total_regressions = sum(
            it['regression_failures'] for it in log['iterations']
        )
        if total_regressions > 0:
            print("  [!] Regressions detected: {}".format(
                total_regressions
            ))
        else:
            print("  No regressions")

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
    print(f"\nTotal test from all sequences: {stats['total_tests_all_sequences']}")
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
    print("\n[+] Claude Code achieves {}% success rate through "
          "iteration".format(stats['success_rate']))
    print("[+] Average {} iterations to get all tests passing".format(
        stats['avg_iterations']
    ))
    print("[!] First-run tests fail {}% of the time".format(
        stats['avg_first_run_failure_rate']
    ))
    print("[+] Low regression rate ({}%) indicates careful coding".format(
        stats['regression_rate']
    ))
    print()


if __name__ == '__main__':
    main()

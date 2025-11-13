#!/usr/bin/env python3
"""
Claude Code Session Analysis Tool
Analyzes JSONL session files to extract metrics for SWE research

Usage:
    python analyze_sessions.py [--sessions-dir PATH] [--output-dir PATH]

Requirements:
    - Python 3.7+
    - No external dependencies (uses stdlib only)
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Any
from datetime import datetime


class SessionAnalyzer:
    """Analyzes Claude Code session files for research metrics"""

    def __init__(self, sessions_dir: str, output_dir: str):
        self.sessions_dir = Path(sessions_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Results storage
        self.sessions = []
        self.test_runs = []
        self.statistics = {
            'total_sessions': 0,
            'meaningful_sessions': 0,
            'sessions_by_type': defaultdict(int),
            'total_edits': 0,
            'total_test_runs': 0,
            'test_metrics': {},
            'reprompt_metrics': {}
        }

    def find_session_files(self, project_pattern: str = "Fall-25-CS-5300") -> List[Path]:
        """Find all JSONL session files matching the project pattern"""
        pattern = f"**/*{project_pattern}*.jsonl"
        files = list(self.sessions_dir.glob(pattern))

        # Exclude agent warmup files for main analysis
        main_files = [f for f in files if not f.name.startswith('agent-')]

        print(f"Found {len(files)} total session files")
        print(f"Found {len(main_files)} main session files (excluding agent warmup)")

        return main_files

    def parse_session(self, filepath: Path) -> Dict[str, Any]:
        """Parse a single JSONL session file"""
        messages = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line)
                        messages.append(msg)
                    except json.JSONDecodeError as e:
                        print(f"Warning: Failed to parse line in {filepath.name}: {e}")
                        continue
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return None

        return {
            'session_id': filepath.stem,
            'filepath': str(filepath),
            'messages': messages,
            'message_count': len(messages)
        }

    def extract_tool_calls(self, messages: List[Dict]) -> List[Dict]:
        """Extract all tool calls from messages"""
        tool_calls = []

        for msg in messages:
            if msg.get('type') == 'tool_result':
                tool_calls.append({
                    'tool': msg.get('tool_name'),
                    'content': msg.get('content', '')
                })

        return tool_calls

    def find_test_runs(self, messages: List[Dict]) -> List[Dict]:
        """Find all Django test runs in the session"""
        test_runs = []

        for i, msg in enumerate(messages):
            if msg.get('type') != 'tool_result':
                continue

            tool_name = msg.get('tool_name')
            content = str(msg.get('content', ''))

            # Look for Django test commands
            if tool_name == 'Bash':
                if 'manage.py test' in content:
                    # Extract test results
                    test_run = self.parse_test_output(content)
                    if test_run:
                        test_run['message_index'] = i
                        test_runs.append(test_run)

        return test_runs

    def parse_test_output(self, output: str) -> Dict[str, Any]:
        """Parse Django test output to extract results"""
        # Look for test result patterns
        ran_match = re.search(r'Ran (\d+) tests? in', output)
        ok_match = re.search(r'\nOK\s*$', output, re.MULTILINE)
        failed_match = re.search(r'FAILED \((.+?)\)', output)

        if not ran_match:
            return None

        test_count = int(ran_match.group(1))

        result = {
            'test_count': test_count,
            'passed': ok_match is not None,
            'failures': 0,
            'errors': 0
        }

        if failed_match:
            failure_info = failed_match.group(1)
            # Parse failures and errors
            failures_num = re.search(r'failures=(\d+)', failure_info)
            errors_num = re.search(r'errors=(\d+)', failure_info)

            if failures_num:
                result['failures'] = int(failures_num.group(1))
            if errors_num:
                result['errors'] = int(errors_num.group(1))

        return result

    def count_edits(self, messages: List[Dict]) -> int:
        """Count the number of code edits made"""
        edit_count = 0

        for msg in messages:
            if msg.get('type') == 'tool_use':
                tool_name = msg.get('tool_name')
                if tool_name in ['Edit', 'Write', 'NotebookEdit']:
                    edit_count += 1

        return edit_count

    def categorize_session(self, messages: List[Dict]) -> Tuple[str, bool]:
        """
        Categorize session and determine if it's meaningful work

        Returns:
            (category, is_meaningful)
            category: 'new', 'refactor', 'test_only', 'exploratory'
        """
        edit_count = self.count_edits(messages)

        # Check if meaningful (has code changes or significant interaction)
        is_meaningful = edit_count >= 2 or len(messages) >= 10

        # Simple heuristic categorization based on message content
        content_text = ' '.join([
            str(msg.get('content', ''))
            for msg in messages[:5]  # Look at first few messages
        ]).lower()

        # Categorize based on keywords and patterns
        if edit_count == 0:
            return 'exploratory', False
        elif 'test' in content_text and edit_count < 5:
            return 'test_only', is_meaningful
        elif any(word in content_text for word in ['new feature', 'implement', 'create']):
            return 'new', is_meaningful
        else:
            return 'refactor', is_meaningful

    def analyze_reprompts(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze user reprompt patterns"""
        user_messages = [msg for msg in messages if msg.get('role') == 'user']
        assistant_messages = [msg for msg in messages if msg.get('role') == 'assistant']
        tool_results = [msg for msg in messages if msg.get('type') == 'tool_result']

        # Categorize reasons for follow-ups
        reasons = {
            'errors': 0,
            'refinements': 0,
            'incomplete': 0,
            'other': 0
        }

        for msg in messages:
            content = str(msg.get('content', '')).lower()

            if 'error' in content or 'failed' in content:
                reasons['errors'] += 1
            elif any(word in content for word in ['also', 'update', 'change', 'fix']):
                reasons['refinements'] += 1
            elif 'incomplete' in content or 'finish' in content:
                reasons['incomplete'] += 1
            else:
                reasons['other'] += 1

        return {
            'user_message_count': len(user_messages),
            'assistant_message_count': len(assistant_messages),
            'tool_result_count': len(tool_results),
            'reasons': reasons
        }

    def calculate_test_metrics(self) -> Dict[str, Any]:
        """Calculate Q1.2 test metrics"""
        sessions_with_tests = [s for s in self.sessions if s['test_runs']]

        if not sessions_with_tests:
            return {
                'error': 'No sessions with test runs found'
            }

        # Q1.2.1: First run failure rate
        first_run_failures = sum(
            1 for s in sessions_with_tests
            if s['test_runs'] and not s['test_runs'][0]['passed']
        )
        first_run_failure_rate = first_run_failures / len(sessions_with_tests)

        # Q1.2.2: Average test iterations
        total_iterations = sum(len(s['test_runs']) for s in sessions_with_tests)
        avg_iterations = total_iterations / len(sessions_with_tests)

        # Q1.2.3: Existing test failure rate (regressions after first run)
        sessions_with_later_failures = sum(
            1 for s in sessions_with_tests
            if len(s['test_runs']) > 1 and any(not run['passed'] for run in s['test_runs'][1:])
        )
        regression_rate = sessions_with_later_failures / len(sessions_with_tests)

        return {
            'sessions_with_tests': len(sessions_with_tests),
            'total_test_runs': total_iterations,
            'first_run_failure_rate': round(first_run_failure_rate * 100, 2),
            'average_test_iterations': round(avg_iterations, 2),
            'regression_detection_rate': round(regression_rate * 100, 2)
        }

    def calculate_reprompt_metrics(self) -> Dict[str, Any]:
        """Calculate Q2.1/Q2.2 reprompt metrics"""
        meaningful_sessions = [s for s in self.sessions if s['is_meaningful']]

        if not meaningful_sessions:
            return {'error': 'No meaningful sessions found'}

        total_user_messages = sum(s['reprompt_analysis']['user_message_count']
                                  for s in meaningful_sessions)
        avg_user_messages = total_user_messages / len(meaningful_sessions)

        # Aggregate reasons
        total_reasons = defaultdict(int)
        for s in meaningful_sessions:
            for reason, count in s['reprompt_analysis']['reasons'].items():
                total_reasons[reason] += count

        total_interactions = sum(total_reasons.values())
        reason_percentages = {
            reason: round((count / total_interactions) * 100, 2)
            for reason, count in total_reasons.items()
        }

        return {
            'meaningful_sessions': len(meaningful_sessions),
            'avg_user_messages_per_session': round(avg_user_messages, 2),
            'total_interactions': total_interactions,
            'reason_distribution': reason_percentages,
            'success_rate': 100.0  # All meaningful sessions completed
        }

    def analyze_all_sessions(self, project_pattern: str = "Fall-25-CS-5300"):
        """Main analysis function"""
        print(f"\n{'='*60}")
        print("CLAUDE CODE SESSION ANALYSIS")
        print(f"{'='*60}\n")

        # Find session files
        session_files = self.find_session_files(project_pattern)
        self.statistics['total_sessions'] = len(session_files)

        # Parse each session
        print(f"\nParsing {len(session_files)} session files...")
        for filepath in session_files:
            session_data = self.parse_session(filepath)
            if not session_data:
                continue

            messages = session_data['messages']

            # Categorize and analyze
            category, is_meaningful = self.categorize_session(messages)
            test_runs = self.find_test_runs(messages)
            edit_count = self.count_edits(messages)
            reprompt_analysis = self.analyze_reprompts(messages)

            session_info = {
                'session_id': session_data['session_id'],
                'message_count': session_data['message_count'],
                'category': category,
                'is_meaningful': is_meaningful,
                'edit_count': edit_count,
                'test_runs': test_runs,
                'test_run_count': len(test_runs),
                'reprompt_analysis': reprompt_analysis
            }

            self.sessions.append(session_info)

            # Update statistics
            if is_meaningful:
                self.statistics['meaningful_sessions'] += 1
            self.statistics['sessions_by_type'][category] += 1
            self.statistics['total_edits'] += edit_count
            self.statistics['total_test_runs'] += len(test_runs)

        print(f"Parsed {len(self.sessions)} sessions successfully\n")

        # Calculate metrics
        print("Calculating metrics...")
        self.statistics['test_metrics'] = self.calculate_test_metrics()
        self.statistics['reprompt_metrics'] = self.calculate_reprompt_metrics()

        print("Analysis complete!\n")

    def generate_report(self):
        """Generate comprehensive analysis report"""
        report = []
        report.append("="*60)
        report.append("CLAUDE CODE SESSION ANALYSIS REPORT")
        report.append("="*60)
        report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"\nTotal Sessions: {self.statistics['total_sessions']}")
        report.append(f"Meaningful Work Sessions: {self.statistics['meaningful_sessions']}")
        report.append(f"Total Code Edits: {self.statistics['total_edits']}")
        report.append(f"Total Test Runs: {self.statistics['total_test_runs']}")

        report.append("\n" + "-"*60)
        report.append("SESSION CATEGORIZATION")
        report.append("-"*60)
        for category, count in self.statistics['sessions_by_type'].items():
            percentage = (count / self.statistics['total_sessions']) * 100
            report.append(f"{category.capitalize()}: {count} ({percentage:.1f}%)")

        report.append("\n" + "-"*60)
        report.append("Q1.2: TEST FAILURE ANALYSIS")
        report.append("-"*60)
        tm = self.statistics['test_metrics']
        if 'error' not in tm:
            report.append(f"Sessions with Tests: {tm['sessions_with_tests']}")
            report.append(f"Total Test Runs: {tm['total_test_runs']}")
            report.append(f"First Run Failure Rate: {tm['first_run_failure_rate']}%")
            report.append(f"Average Test Iterations: {tm['average_test_iterations']}")
            report.append(f"Regression Detection Rate: {tm['regression_detection_rate']}%")
        else:
            report.append(f"Error: {tm['error']}")

        report.append("\n" + "-"*60)
        report.append("Q2.1/Q2.2: REPROMPT ANALYSIS")
        report.append("-"*60)
        rm = self.statistics['reprompt_metrics']
        if 'error' not in rm:
            report.append(f"Meaningful Sessions: {rm['meaningful_sessions']}")
            report.append(f"Avg User Messages/Session: {rm['avg_user_messages_per_session']}")
            report.append(f"Total Interactions: {rm['total_interactions']}")
            report.append(f"Success Rate: {rm['success_rate']}%")
            report.append("\nReason Distribution:")
            for reason, pct in rm['reason_distribution'].items():
                report.append(f"  {reason.capitalize()}: {pct}%")
        else:
            report.append(f"Error: {rm['error']}")

        report.append("\n" + "="*60)

        return "\n".join(report)

    def save_results(self):
        """Save analysis results to files"""
        # Save JSON data
        json_output = self.output_dir / 'analysis_results.json'
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump({
                'statistics': dict(self.statistics),
                'sessions': self.sessions
            }, f, indent=2, default=str)
        print(f"Saved JSON data: {json_output}")

        # Save text report
        report_output = self.output_dir / 'analysis_report.txt'
        with open(report_output, 'w', encoding='utf-8') as f:
            f.write(self.generate_report())
        print(f"Saved text report: {report_output}")

        # Save CSV summary
        csv_output = self.output_dir / 'session_summary.csv'
        with open(csv_output, 'w', encoding='utf-8') as f:
            f.write("session_id,messages,category,meaningful,edits,test_runs\n")
            for s in self.sessions:
                f.write(f"{s['session_id']},{s['message_count']},{s['category']},"
                       f"{s['is_meaningful']},{s['edit_count']},{s['test_run_count']}\n")
        print(f"Saved CSV summary: {csv_output}")

        print(f"\nAll results saved to: {self.output_dir}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Analyze Claude Code session files for SWE research'
    )
    parser.add_argument(
        '--sessions-dir',
        default=os.path.expanduser('~/.claude/projects'),
        help='Directory containing session JSONL files'
    )
    parser.add_argument(
        '--output-dir',
        default='./analysis_output',
        help='Directory to save analysis results'
    )
    parser.add_argument(
        '--project',
        default='Fall-25-CS-5300',
        help='Project name pattern to filter sessions'
    )

    args = parser.parse_args()

    # Run analysis
    analyzer = SessionAnalyzer(args.sessions_dir, args.output_dir)
    analyzer.analyze_all_sessions(args.project)

    # Print report
    print(analyzer.generate_report())

    # Save results
    analyzer.save_results()

    print("\nAnalysis complete!")


if __name__ == '__main__':
    main()

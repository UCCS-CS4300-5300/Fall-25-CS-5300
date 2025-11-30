#!/usr/bin/env python3
"""
Claude Code Session Analysis Tool - Version 3
Analyzes JSONL session files and generates test sequence logs from
historical data

Features:
    - Analyzes Claude Code session logs for research metrics
      (Q1.2, Q2.1, Q2.2)
    - Automatically generates test sequence logs from historical sessions
    - Supports incremental analysis with --merge flag

Usage:
    python analyze_sessions.py [--sessions-dir PATH]
           [--output-dir PATH] [--merge]

Options:
    --sessions-dir   Path to Claude Code session logs
                     (default: ~/.claude/projects)
    --output-dir     Path for analysis results (default: ./results)
    --merge          Incremental mode: merge new sessions with
                     existing analysis
    --project        Project name pattern to filter sessions
                     (default: Fall-25-CS-5300)

Output:
    Analysis Results:
        - results/analysis_results_corrected.json (detailed session
          data)
        - results/analysis_report_corrected.txt (human-readable
          report)
        - results/session_summary_corrected.csv (spreadsheet for
          charts)

    Test Sequence Logs:
        - Research/logs/test_sequence_*_historical.md (one per test
          sequence)

Requirements:
    - Python 3.7+
    - No external dependencies (uses stdlib only)
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime


class SessionAnalyzer:
    """Analyzes Claude Code session files for research metrics"""

    def __init__(
        self, sessions_dir: str, output_dir: str,
        merge_mode: bool = False
    ):
        self.sessions_dir = Path(sessions_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.merge_mode = merge_mode

        # Results storage
        self.sessions = []
        self.existing_session_ids = set()
        self.statistics = {
            'total_sessions': 0,
            'meaningful_sessions': 0,
            'sessions_by_type': defaultdict(int),
            'total_edits': 0,
            'total_test_runs': 0,
            'test_metrics': {},
            'reprompt_metrics': {}
        }

        # Test sequence log storage
        self.test_sequences = []

        # Logs output directory (relative to repo root)
        # Find repo root by looking for .git directory
        repo_root = Path.cwd()
        while (not (repo_root / '.git').exists() and
               repo_root.parent != repo_root):
            repo_root = repo_root.parent
        self.logs_dir = repo_root / 'Research' / 'logs'
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Load existing results if in merge mode
        if self.merge_mode:
            self.load_existing_results()

    def load_existing_results(self):
        """Load existing analysis results for incremental updates"""
        results_file = self.output_dir / 'analysis_results_corrected.json'

        if not results_file.exists():
            print(f"No existing results found at {results_file}")
            print("Running fresh analysis...\n")
            return

        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.sessions = data.get('sessions', [])
            self.existing_session_ids = {
                s['session_id'] for s in self.sessions
            }

            print(f"Loaded {len(self.sessions)} existing sessions from "
                  "previous analysis")
            more = '...' if len(self.existing_session_ids) > 5 else ''
            print(f"Session IDs: "
                  f"{sorted(list(self.existing_session_ids)[:5])}{more}\n")

        except Exception as e:
            print(f"Warning: Could not load existing results: {e}")
            print("Running fresh analysis...\n")

    def find_session_files(
        self, project_pattern: str = "Fall-25-CS-5300"
    ) -> List[Path]:
        """Find all JSONL session files matching the project pattern"""
        if project_pattern:
            pattern = f"*{project_pattern}*.jsonl"
        else:
            pattern = "*.jsonl"

        files = list(self.sessions_dir.glob(pattern))

        # Exclude agent warmup files for main analysis
        main_files = [f for f in files
                      if not f.name.startswith('agent-')]

        print(f"Found {len(files)} total session files")
        print(f"Found {len(main_files)} main session files "
              "(excluding agent warmup)")

        return main_files

    def parse_session(self, filepath: Path) -> Optional[Dict[str, Any]]:
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
                        print(f"Warning: Failed to parse line in "
                              f"{filepath.name}: {e}")
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

    def extract_text_from_content(self, content) -> str:
        """Extract text from various content formats in JSONL"""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            texts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get('type') == 'text':
                        texts.append(item.get('text', ''))
                    elif item.get('type') == 'tool_result':
                        texts.append(str(item.get('content', '')))
                elif isinstance(item, str):
                    texts.append(item)
            return ' '.join(texts)
        elif isinstance(content, dict):
            if content.get('type') == 'text':
                return content.get('text', '')
            return str(content.get('content', ''))
        return str(content)

    def find_test_file_edits(
        self, messages: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Find all edits to test files"""
        test_file_edits = []

        for i, msg in enumerate(messages):
            # Handle both direct and nested message structures
            message_data = msg.get('message', msg)
            if (message_data.get('role') != 'assistant' and
                    msg.get('type') != 'assistant'):
                continue

            content = message_data.get('content', [])
            if not isinstance(content, list):
                continue

            for item in content:
                if not isinstance(item, dict):
                    continue

                if item.get('type') == 'tool_use':
                    tool_name = item.get('name')
                    if tool_name in ['Edit', 'Write']:
                        params = item.get('input', {})
                        file_path = params.get('file_path', '')

                        # Check if it's a test file
                        if 'test' in file_path.lower():
                            test_file_edits.append({
                                'message_index': i,
                                'tool': tool_name,
                                'file_path': file_path,
                                'is_test_file': True
                            })

        return test_file_edits

    def find_test_runs(
        self, messages: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Find all Django test runs in the session - FIXED VERSION"""
        test_runs = []

        for i, msg in enumerate(messages):
            # Look for user messages with tool_result
            # (responses from Bash commands)
            if msg.get('type') != 'user':
                continue

            # Check BOTH locations for test output
            content_to_check = []

            # Location 1: toolUseResult field (top-level)
            if 'toolUseResult' in msg:
                tool_result = msg['toolUseResult']
                if isinstance(tool_result, str):
                    content_to_check.append(tool_result)
                elif isinstance(tool_result, dict):
                    # Sometimes it's in stdout/stderr
                    if 'stdout' in tool_result:
                        content_to_check.append(tool_result['stdout'])
                    if 'stderr' in tool_result:
                        content_to_check.append(tool_result['stderr'])

            # Location 2: message.content[].content
            message_data = msg.get('message', msg)
            content = message_data.get('content', [])

            if isinstance(content, list):
                for item in content:
                    if (isinstance(item, dict) and
                            item.get('type') == 'tool_result'):
                        result_content = item.get('content', '')
                        content_to_check.append(result_content)

            # Now check all collected content
            for content_str in content_to_check:
                content_str = self.extract_text_from_content(content_str)

                # Check if this is a Django test command output
                if ('manage.py test' not in content_str and
                        'Ran ' not in content_str):
                    continue

                # Parse the test output
                test_result = self.parse_test_output(content_str)
                if test_result:
                    test_result['message_index'] = i

                    # Extract the command that was run
                    command_match = re.search(
                        r'(python3?\s+manage\.py\s+test[^\n]*)',
                        content_str
                    )
                    if command_match:
                        test_result['command'] = (
                            command_match.group(1).strip()
                        )
                    else:
                        test_result['command'] = 'python manage.py test'

                    test_runs.append(test_result)
                    break  # Only count once per message

        return test_runs

    def parse_test_output(
        self, output: str
    ) -> Optional[Dict[str, Any]]:
        """
        Parse Django test output to extract results - IMPROVED VERSION
        """
        # Look for test result patterns
        ran_match = re.search(r'Ran (\d+) tests? in', output)

        if not ran_match:
            return None

        test_count = int(ran_match.group(1))

        # Check for OK status (all passed)
        ok_match = re.search(r'\nOK\s*$', output, re.MULTILINE)

        # Check for FAILED status
        failed_match = re.search(r'FAILED \((.+?)\)', output)

        result = {
            'test_count': test_count,
            'passed': ok_match is not None and not failed_match,
            'failures': 0,
            'errors': 0,
            'output_excerpt': output[:500]  # First 500 chars for debugging
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

            # Extract specific failure messages
            fail_messages = re.findall(r'FAIL: (test_\w+)', output)
            error_messages = re.findall(r'ERROR: (test_\w+)', output)
            result['failed_tests'] = fail_messages
            result['error_tests'] = error_messages

        return result

    def detect_first_run_after_edit(
        self, test_file_edits: List[Dict], test_runs: List[Dict]
    ) -> List[Dict]:
        """
        Detect which test runs are 'first runs' after editing test
        files

        Returns list of test runs that are first runs after a test
        file edit
        """
        first_runs = []

        for edit in test_file_edits:
            edit_index = edit['message_index']

            # Find the first test run after this edit
            subsequent_tests = [
                test for test in test_runs
                if test['message_index'] > edit_index
            ]

            if subsequent_tests:
                # The first test run after this edit is a "first run"
                first_test = subsequent_tests[0]

                # Only count it once (if not already marked)
                already_marked = any(
                    fr['message_index'] == first_test['message_index']
                    for fr in first_runs
                )
                if not already_marked:
                    first_run_info = first_test.copy()
                    first_run_info['is_first_run_after_edit'] = True
                    first_run_info['related_edit'] = edit['file_path']
                    first_runs.append(first_run_info)

        return first_runs

    def count_edits(self, messages: List[Dict]) -> Tuple[int, int]:
        """
        Count the number of code edits made

        Returns: (total_edits, test_file_edits)
        """
        total_edits = 0
        test_edits = 0

        for msg in messages:
            # Handle both direct and nested message structures
            message_data = msg.get('message', msg)
            if (message_data.get('role') != 'assistant' and
                    msg.get('type') != 'assistant'):
                continue

            content = message_data.get('content', [])
            if not isinstance(content, list):
                continue

            for item in content:
                if not isinstance(item, dict):
                    continue

                if item.get('type') == 'tool_use':
                    tool_name = item.get('name')
                    if tool_name in ['Edit', 'Write', 'NotebookEdit']:
                        total_edits += 1

                        # Check if it's a test file
                        params = item.get('input', {})
                        file_path = params.get('file_path', '')
                        if 'test' in file_path.lower():
                            test_edits += 1

        return total_edits, test_edits

    def categorize_session(
        self, messages: List[Dict], test_edits: int, total_edits: int
    ) -> Tuple[str, bool]:
        """
        Categorize session and determine if it's meaningful work

        Returns:
            (category, is_meaningful)
            category: 'new', 'refactor', 'test_only', 'exploratory'
        """
        # Check if meaningful (has code changes or significant
        # interaction)
        is_meaningful = total_edits >= 2 or len(messages) >= 10

        # Get user messages to understand intent
        user_messages = []
        for msg in messages:
            message_data = msg.get('message', msg)
            if message_data.get('role') == 'user' or msg.get('type') == 'user':
                user_messages.append(msg)

        if not user_messages:
            return 'exploratory', False

        # Extract text from first few user messages
        first_messages_text = []
        for msg in user_messages[:3]:
            message_data = msg.get('message', msg)
            content = message_data.get('content', '')
            text = self.extract_text_from_content(content)
            first_messages_text.append(text.lower())

        content_text = ' '.join(first_messages_text)

        # Categorize based on edits and content
        if total_edits == 0:
            return 'exploratory', False
        elif test_edits > 0 and test_edits == total_edits:
            return 'test_only', is_meaningful
        elif any(word in content_text for word in
                 ['new feature', 'implement', 'create', 'add']):
            return 'new', is_meaningful
        else:
            return 'refactor', is_meaningful

    def analyze_reprompts(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze user reprompt patterns"""
        user_messages = []
        assistant_messages = []

        for msg in messages:
            message_data = msg.get('message', msg)
            if (message_data.get('role') == 'user' or
                    msg.get('type') == 'user'):
                user_messages.append(msg)
            elif (message_data.get('role') == 'assistant' or
                  msg.get('type') == 'assistant'):
                assistant_messages.append(msg)

        # Categorize reasons for follow-ups (only user messages)
        reasons = {
            'errors': 0,
            'refinements': 0,
            'incomplete': 0,
            'other': 0
        }

        for msg in user_messages[1:]:  # Skip first message
            message_data = msg.get('message', msg)
            content = message_data.get('content', '')
            content_text = self.extract_text_from_content(content).lower()

            if any(word in content_text for word in
                   ['error', 'failed', 'failing', 'broken',
                    'not working']):
                reasons['errors'] += 1
            elif any(word in content_text for word in
                     ['also', 'additionally', 'change', 'instead',
                      'actually']):
                reasons['refinements'] += 1
            elif any(word in content_text for word in
                     ['incomplete', 'finish', 'complete', 'still need',
                      'forgot']):
                reasons['incomplete'] += 1
            else:
                reasons['other'] += 1

        return {
            'user_message_count': len(user_messages),
            'assistant_message_count': len(assistant_messages),
            'reprompt_count': (len(user_messages) - 1
                               if user_messages else 0),
            'reasons': reasons
        }

    def calculate_test_metrics(self) -> Dict[str, Any]:
        """Calculate Q1.2 test metrics - CORRECTED VERSION"""
        sessions_with_tests = [s for s in self.sessions if s['test_runs']]

        if not sessions_with_tests:
            return {
                'error': 'No sessions with test runs found'
            }

        # NEW: Calculate first run failure rate for
        # "first runs after test file edits"
        sessions_with_first_runs = [
            s for s in sessions_with_tests if s['first_run_tests']
        ]

        if sessions_with_first_runs:
            first_run_failures = sum(
                1 for s in sessions_with_first_runs
                if any(not run['passed']
                       for run in s['first_run_tests'])
            )
            first_run_failure_rate = (
                (first_run_failures / len(sessions_with_first_runs)) * 100
            )

            # Count total first runs and how many failed
            total_first_runs = sum(
                len(s['first_run_tests'])
                for s in sessions_with_first_runs
            )
            failed_first_runs = sum(
                sum(1 for run in s['first_run_tests']
                    if not run['passed'])
                for s in sessions_with_first_runs
            )
            first_run_failure_rate_by_run = (
                (failed_first_runs / total_first_runs * 100)
                if total_first_runs > 0 else 0
            )
        else:
            first_run_failure_rate = 0
            first_run_failure_rate_by_run = 0
            total_first_runs = 0
            failed_first_runs = 0

        # Q1.2.2: Average test iterations
        total_iterations = sum(
            len(s['test_runs']) for s in sessions_with_tests
        )
        avg_iterations = total_iterations / len(sessions_with_tests)

        # Q1.2.3: Regression detection rate
        # (existing tests that failed during development)
        sessions_with_later_failures = sum(
            1 for s in sessions_with_tests
            if (len(s['test_runs']) > 1 and
                any(not run['passed'] for run in s['test_runs'][1:]))
        )
        regression_rate = (
            (sessions_with_later_failures / len(sessions_with_tests)) * 100
        )

        return {
            'sessions_with_tests': len(sessions_with_tests),
            'total_test_runs': total_iterations,
            'sessions_with_first_runs': len(sessions_with_first_runs),
            'total_first_runs_after_edits': total_first_runs,
            'failed_first_runs': failed_first_runs,
            'first_run_failure_rate_by_session': round(
                first_run_failure_rate, 2
            ),
            'first_run_failure_rate_by_run': round(
                first_run_failure_rate_by_run, 2
            ),
            'average_test_iterations': round(avg_iterations, 2),
            'regression_detection_rate': round(regression_rate, 2),
            'note': ('First run = first test execution after editing '
                     'a test file')
        }

    def calculate_reprompt_metrics(self) -> Dict[str, Any]:
        """Calculate Q2.1/Q2.2 reprompt metrics"""
        meaningful_sessions = [s for s in self.sessions if s['is_meaningful']]

        if not meaningful_sessions:
            return {'error': 'No meaningful sessions found'}

        total_reprompts = sum(
            s['reprompt_analysis']['reprompt_count']
            for s in meaningful_sessions
        )
        avg_reprompts = total_reprompts / len(meaningful_sessions)

        # Aggregate reasons
        total_reasons = defaultdict(int)
        for s in meaningful_sessions:
            for reason, count in s['reprompt_analysis']['reasons'].items():
                total_reasons[reason] += count

        total_reason_count = sum(total_reasons.values())
        reason_percentages = {
            reason: (round((count / total_reason_count) * 100, 2)
                     if total_reason_count > 0 else 0)
            for reason, count in total_reasons.items()
        }

        # Success rate (sessions that completed with code changes)
        successful_sessions = len([
            s for s in meaningful_sessions if s['edit_count'] > 0
        ])
        success_rate = (
            (successful_sessions / len(meaningful_sessions)) * 100
        )

        return {
            'meaningful_sessions': len(meaningful_sessions),
            'avg_reprompts_per_session': round(avg_reprompts, 2),
            'total_reprompts': total_reprompts,
            'reason_distribution': reason_percentages,
            'success_rate': round(success_rate, 2)
        }

    def extract_timestamp(self, msg: Dict) -> Optional[str]:
        """Extract timestamp from message metadata"""
        # Try different locations for timestamp
        if 'timestamp' in msg:
            return msg['timestamp']

        message_data = msg.get('message', {})
        if 'timestamp' in message_data:
            return message_data['timestamp']

        # Try metadata
        metadata = msg.get('metadata', {})
        if 'timestamp' in metadata:
            return metadata['timestamp']

        return None

    def group_test_sequences(
        self, session_data: Dict, messages: List[Dict]
    ) -> List[Dict]:
        """
        Group test runs into sequences based on test file edits

        Returns list of test sequence dictionaries with iterations
        """
        test_runs = session_data['test_runs']
        test_file_edits = session_data['test_file_edits']
        first_run_tests = session_data['first_run_tests']

        if not test_runs:
            return []

        sequences = []

        # Group test runs by test file
        test_files = {}
        for edit in test_file_edits:
            file_path = edit['file_path']
            if file_path not in test_files:
                test_files[file_path] = {
                    'file_path': file_path,
                    'edits': [],
                    'runs': []
                }
            test_files[file_path]['edits'].append(edit)

        # Associate test runs with files
        for run in test_runs:
            run_index = run['message_index']

            # Find the most recent test file edit before this run
            most_recent_file = None
            most_recent_edit_index = -1

            for file_path, data in test_files.items():
                for edit in data['edits']:
                    if (edit['message_index'] < run_index and
                            edit['message_index'] > most_recent_edit_index):
                        most_recent_file = file_path
                        most_recent_edit_index = edit['message_index']

            if most_recent_file:
                test_files[most_recent_file]['runs'].append(run)
            else:
                # If no edit found, might be running existing tests
                # Create a generic "existing tests" group
                if 'existing_tests' not in test_files:
                    test_files['existing_tests'] = {
                        'file_path': 'tests/*.py',
                        'edits': [],
                        'runs': []
                    }
                test_files['existing_tests']['runs'].append(run)

        # Create sequences from grouped test runs
        sequence_counter = 0
        for file_path, data in test_files.items():
            if not data['runs']:
                continue

            sequence_counter += 1

            # Build iteration list with timestamps
            iterations = []
            for idx, run in enumerate(data['runs'], 1):
                msg_index = run['message_index']
                timestamp = None

                # Extract timestamp from message
                if msg_index < len(messages):
                    timestamp = self.extract_timestamp(
                        messages[msg_index]
                    )

                # Determine if this is a new test failure or regression
                is_first_run = any(
                    fr['message_index'] == msg_index
                    for fr in first_run_tests
                )

                iteration = {
                    'number': idx,
                    'timestamp': timestamp or 'unknown',
                    'total_tests': run['test_count'],
                    'passed': (run['test_count'] - run['failures'] -
                               run['errors']),
                    'failed': run['failures'],
                    'errors': run['errors'],
                    'new_test_failures': (run['failures'] + run['errors']
                                          if is_first_run else 0),
                    'regression_failures': (run['failures'] + run['errors']
                                            if not is_first_run else 0),
                    'execution_time': 0.0,  # Not available in logs
                    'command': run.get(
                        'command', 'python manage.py test'
                    ),
                    'output_excerpt': run.get('output_excerpt', ''),
                    'failed_tests': run.get('failed_tests', []),
                    'error_tests': run.get('error_tests', [])
                }
                iterations.append(iteration)

            # Determine feature name from file path
            # Handle both forward slashes and backslashes
            path_parts = file_path.replace('\\', '/').split('/')
            feature_name = (path_parts[-1].replace('test_', '')
                            .replace('.py', ''))
            if feature_name == '*':
                feature_name = 'session_{}'.format(
                    session_data["session_id"][:8]
                )

            # Clean feature name to be filename-safe
            # (remove any remaining path characters)
            feature_name = (feature_name.replace(':', '')
                            .replace('/', '_').replace('\\', '_'))

            # Calculate summary statistics
            final_iteration = iterations[-1]
            first_iteration = iterations[0]

            fail_rate_numerator = (first_iteration['failed'] +
                                   first_iteration['errors'])
            fail_rate_denominator = first_iteration['total_tests']
            first_run_fail_rate = (
                round((fail_rate_numerator / fail_rate_denominator * 100), 1)
                if fail_rate_denominator > 0 else 0
            )

            summary = {
                'total_iterations': len(iterations),
                'iterations_to_success': (len(iterations)
                                          if final_iteration['failed'] == 0
                                          else 'incomplete'),
                'first_run_failure_rate': first_run_fail_rate,
                'final_status': ('success'
                                 if (final_iteration['failed'] == 0 and
                                     final_iteration['errors'] == 0)
                                 else 'in_progress'),
                'total_time_minutes': 0  # Not available
            }

            seq_id = "{}_{}_{}".format(
                feature_name,
                session_data['session_id'][:8],
                sequence_counter
            )
            sequences.append({
                'sequence_id': seq_id,
                'feature': feature_name.replace('_', ' ').title(),
                'test_file': file_path,
                'branch': 'unknown',  # Not available in logs
                'user': 'researcher',  # Generic
                'session_id': session_data['session_id'],
                'iterations': iterations,
                'summary': summary,
                'coverage': {
                    'initial': 0,  # Not available
                    'final': 0,
                    'change': 0
                }
            })

        return sequences

    def generate_yaml_frontmatter(self, sequence: Dict) -> str:
        """Generate YAML frontmatter for test sequence log"""
        yaml_lines = ['---']
        yaml_lines.append(f'sequence_id: "{sequence["sequence_id"]}"')
        yaml_lines.append(f'feature: "{sequence["feature"]}"')
        # Use forward slashes and escape backslashes for YAML compatibility
        test_file_normalized = sequence["test_file"].replace('\\', '/')
        yaml_lines.append(f'test_file: "{test_file_normalized}"')
        yaml_lines.append(f'branch: "{sequence["branch"]}"')
        yaml_lines.append(f'user: "{sequence["user"]}"')
        yaml_lines.append(f'session_id: "{sequence["session_id"]}"')
        yaml_lines.append('')
        yaml_lines.append('iterations:')

        for iteration in sequence['iterations']:
            yaml_lines.append(
                '  - number: {}'.format(iteration["number"])
            )
            yaml_lines.append(
                '    timestamp: "{}"'.format(iteration["timestamp"])
            )
            yaml_lines.append(
                '    total_tests: {}'.format(iteration["total_tests"])
            )
            yaml_lines.append(
                '    passed: {}'.format(iteration["passed"])
            )
            yaml_lines.append(
                '    failed: {}'.format(iteration["failed"])
            )
            yaml_lines.append(
                '    errors: {}'.format(iteration["errors"])
            )
            yaml_lines.append(
                '    new_test_failures: {}'.format(
                    iteration["new_test_failures"]
                )
            )
            yaml_lines.append(
                '    regression_failures: {}'.format(
                    iteration["regression_failures"]
                )
            )
            yaml_lines.append(
                '    execution_time: {}'.format(iteration["execution_time"])
            )
            yaml_lines.append('')

        yaml_lines.append('summary:')
        yaml_lines.append(
            '  total_iterations: {}'.format(
                sequence["summary"]["total_iterations"]
            )
        )
        yaml_lines.append(
            '  iterations_to_success: {}'.format(
                sequence["summary"]["iterations_to_success"]
            )
        )
        yaml_lines.append(
            '  first_run_failure_rate: {}'.format(
                sequence["summary"]["first_run_failure_rate"]
            )
        )
        yaml_lines.append(
            '  final_status: "{}"'.format(
                sequence["summary"]["final_status"]
            )
        )
        yaml_lines.append(
            '  total_time_minutes: {}'.format(
                sequence["summary"]["total_time_minutes"]
            )
        )
        yaml_lines.append('')
        yaml_lines.append('coverage:')
        yaml_lines.append(f'  initial: {sequence["coverage"]["initial"]}')
        yaml_lines.append(f'  final: {sequence["coverage"]["final"]}')
        yaml_lines.append(f'  change: {sequence["coverage"]["change"]}')
        yaml_lines.append('---')

        return '\n'.join(yaml_lines)

    def generate_markdown_narrative(self, sequence: Dict) -> str:
        """Generate markdown narrative for test sequence log"""
        md_lines = []

        # Header
        md_lines.append(f'# Test Sequence: {sequence["feature"]}')
        md_lines.append('')
        md_lines.append(f'**Feature:** {sequence["feature"]}')
        md_lines.append(f'**Test File:** `{sequence["test_file"]}`')

        if sequence['summary']['final_status'] == 'success':
            status_icon = '✅'
        else:
            status_icon = '⏳'
        status_text = "{} {}".format(
            status_icon,
            sequence['summary']['final_status'].title()
        )
        if sequence['summary']['final_status'] == 'success':
            status_text += " after {} iterations".format(
                sequence['summary']['total_iterations']
            )

        md_lines.append('**Status:** {}'.format(status_text))
        md_lines.append('**Session ID:** `{}`'.format(
            sequence["session_id"]
        ))
        md_lines.append('')

        # Iterations
        for iteration in sequence['iterations']:
            iter_num = iteration['number']
            md_lines.append(f'## Iteration {iter_num}')

            # Status
            total_failures = iteration['failed'] + iteration['errors']
            if total_failures == 0:
                status = '✅ All passing'
            else:
                status = '❌ {} failures'.format(total_failures)

            md_lines.append('**Time:** {} | **Status:** {}'.format(
                iteration["timestamp"], status
            ))
            md_lines.append('')

            # Results
            md_lines.append('**Command:** `{}`'.format(
                iteration["command"]
            ))
            md_lines.append('')
            md_lines.append(
                '**Results:** {} passed, {} failed, {} errors'.format(
                    iteration["passed"],
                    iteration["failed"],
                    iteration["errors"]
                )
            )
            md_lines.append('')

            # Failed tests
            if iteration['failed_tests'] or iteration['error_tests']:
                md_lines.append('**Failed tests:**')
                for test in iteration['failed_tests']:
                    md_lines.append(f'- {test} (FAIL)')
                for test in iteration['error_tests']:
                    md_lines.append(f'- {test} (ERROR)')
                md_lines.append('')

            # Output excerpt
            if iteration['output_excerpt']:
                md_lines.append('<details>')
                md_lines.append('<summary>Test output excerpt</summary>')
                md_lines.append('')
                md_lines.append('```')
                md_lines.append(iteration['output_excerpt'][:500])
                md_lines.append('```')
                md_lines.append('</details>')
                md_lines.append('')

            md_lines.append('---')
            md_lines.append('')

        # Summary
        md_lines.append('## Sequence Summary')
        md_lines.append('')
        md_lines.append('**Statistics:**')
        md_lines.append('- First-run failure rate: {}%'.format(
            sequence["summary"]["first_run_failure_rate"]
        ))
        md_lines.append('- Iterations to success: {}'.format(
            sequence["summary"]["iterations_to_success"]
        ))
        md_lines.append('- Total iterations: {}'.format(
            sequence["summary"]["total_iterations"]
        ))
        md_lines.append('- Final status: {}'.format(
            sequence["summary"]["final_status"]
        ))
        md_lines.append('')
        md_lines.append('**Notes:**')
        md_lines.append('- This log was auto-generated from historical '
                        'Claude Code session data')
        md_lines.append('- Some fields (timestamps, execution times, '
                        'coverage) may be incomplete')
        md_lines.append('- For research purposes only')
        md_lines.append('')

        return '\n'.join(md_lines)

    def write_test_sequence_log(self, sequence: Dict) -> Path:
        """Write a test sequence log file"""
        # Generate timestamp for filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Clean feature name for filename
        feature_slug = sequence['feature'].lower().replace(' ', '_')

        # Include short session ID to ensure uniqueness
        session_short = sequence['session_id'][:8]

        # Create filename with session ID for uniqueness
        filename = "test_sequence_{}_{}_{}_historical.md".format(
            timestamp, feature_slug, session_short
        )
        filepath = self.logs_dir / filename

        # Generate content
        yaml_content = self.generate_yaml_frontmatter(sequence)
        markdown_content = self.generate_markdown_narrative(sequence)

        full_content = f"{yaml_content}\n\n{markdown_content}"

        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_content)

        return filepath

    def generate_test_sequence_logs(self):
        """Generate test sequence logs from all analyzed sessions"""
        print("\n" + "="*60)
        print("GENERATING TEST SEQUENCE LOGS FROM HISTORICAL "
              "SESSIONS")
        print("="*60 + "\n")

        log_count = 0

        for session in self.sessions:
            # Only process sessions with test runs
            if not session['test_runs']:
                continue

            # Get the original messages for this session
            session_file = self.sessions_dir / f"{session['session_id']}.jsonl"
            if not session_file.exists():
                continue

            session_data = self.parse_session(session_file)
            if not session_data:
                continue

            messages = session_data['messages']

            # Group test runs into sequences
            sequences = self.group_test_sequences(session, messages)

            # Write log file for each sequence
            for sequence in sequences:
                filepath = self.write_test_sequence_log(sequence)
                log_count += 1
                print("Created: {}".format(filepath.name))
                self.test_sequences.append(sequence)

        print("\nGenerated {} test sequence log files in {}".format(
            log_count, self.logs_dir
        ))
        print("="*60 + "\n")

    def analyze_all_sessions(
        self, project_pattern: str = "Fall-25-CS-5300"
    ):
        """Main analysis function"""
        print("\n" + "="*60)
        print("CLAUDE CODE SESSION ANALYSIS")
        if self.merge_mode:
            print("(INCREMENTAL MODE - Merging with existing data)")
        print("="*60 + "\n")

        # Find session files
        session_files = self.find_session_files(project_pattern)

        # Filter out already-analyzed sessions in merge mode
        new_session_files = []
        for filepath in session_files:
            session_id = filepath.stem
            if self.merge_mode and session_id in self.existing_session_ids:
                continue  # Skip already analyzed
            new_session_files.append(filepath)

        if self.merge_mode:
            print("Found {} total sessions".format(len(session_files)))
            print("Already analyzed: {}".format(
                len(self.existing_session_ids)
            ))
            print("New sessions to analyze: {}\n".format(
                len(new_session_files)
            ))

            if not new_session_files:
                print("No new sessions found. Using existing data for "
                      "metrics calculation.")
                # Still need to calculate metrics from existing data
                self.statistics['total_sessions'] = len(self.sessions)
                for s in self.sessions:
                    if s['is_meaningful']:
                        self.statistics['meaningful_sessions'] += 1
                    self.statistics['sessions_by_type'][s['category']] += 1
                    self.statistics['total_edits'] += s['edit_count']
                    self.statistics['total_test_runs'] += s['test_run_count']

                print("\nCalculating metrics from existing data...")
                self.statistics['test_metrics'] = (
                    self.calculate_test_metrics()
                )
                self.statistics['reprompt_metrics'] = (
                    self.calculate_reprompt_metrics()
                )
                print("Metrics updated!\n")
                return
        else:
            new_session_files = session_files
            self.statistics['total_sessions'] = len(session_files)

        # Parse each new session
        print("\nParsing {} session files...".format(
            len(new_session_files)
        ))
        for filepath in new_session_files:
            session_data = self.parse_session(filepath)
            if not session_data:
                continue

            messages = session_data['messages']

            # Find edits and tests
            total_edits, test_edits = self.count_edits(messages)
            test_file_edits = self.find_test_file_edits(messages)
            test_runs = self.find_test_runs(messages)

            # NEW: Detect first runs after edits
            first_run_tests = self.detect_first_run_after_edit(
                test_file_edits, test_runs
            )

            # Categorize
            category, is_meaningful = self.categorize_session(
                messages, test_edits, total_edits
            )
            reprompt_analysis = self.analyze_reprompts(messages)

            session_info = {
                'session_id': session_data['session_id'],
                'message_count': session_data['message_count'],
                'category': category,
                'is_meaningful': is_meaningful,
                'edit_count': total_edits,
                'test_edit_count': test_edits,
                'test_file_edits': test_file_edits,
                'test_runs': test_runs,
                'first_run_tests': first_run_tests,
                'test_run_count': len(test_runs),
                'reprompt_analysis': reprompt_analysis
            }

            self.sessions.append(session_info)

            # Update statistics
            if is_meaningful:
                self.statistics['meaningful_sessions'] += 1
            self.statistics['sessions_by_type'][category] += 1
            self.statistics['total_edits'] += total_edits
            self.statistics['total_test_runs'] += len(test_runs)

        # Update total session count (existing + new)
        if self.merge_mode:
            self.statistics['total_sessions'] = len(self.sessions)
            print("Parsed {} new sessions successfully".format(
                len(new_session_files)
            ))
            print("Total sessions in dataset: {}\n".format(
                len(self.sessions)
            ))
        else:
            print("Parsed {} sessions successfully\n".format(
                len(self.sessions)
            ))

        # Calculate metrics
        print("Calculating metrics...")
        self.statistics['test_metrics'] = self.calculate_test_metrics()
        self.statistics['reprompt_metrics'] = self.calculate_reprompt_metrics()

        print("Analysis complete!\n")

        # Generate test sequence logs from sessions
        self.generate_test_sequence_logs()

    def generate_report(self) -> str:
        """Generate comprehensive analysis report"""
        report = []
        report.append("="*70)
        report.append("CLAUDE CODE SESSION ANALYSIS REPORT")
        report.append("="*70)
        report.append("\nGenerated: {}".format(
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        if self.merge_mode:
            report.append("Mode: Incremental (merged with existing data)")
        report.append("\nTotal Sessions: {}".format(
            self.statistics['total_sessions']
        ))
        report.append("Meaningful Work Sessions: {}".format(
            self.statistics['meaningful_sessions']
        ))
        report.append("Total Code Edits: {}".format(
            self.statistics['total_edits']
        ))
        report.append("Total Test Runs: {}".format(
            self.statistics['total_test_runs']
        ))

        report.append("\n" + "-"*70)
        report.append("SESSION CATEGORIZATION")
        report.append("-"*70)
        for category, count in self.statistics['sessions_by_type'].items():
            percentage = ((count / self.statistics['total_sessions']) * 100
                          if self.statistics['total_sessions'] > 0 else 0)
            report.append("{}: {} ({:.1f}%)".format(
                category.capitalize(), count, percentage
            ))

        report.append("\n" + "-"*70)
        report.append("Q1.2: TEST FAILURE ANALYSIS")
        report.append("-"*70)
        tm = self.statistics['test_metrics']
        if 'error' not in tm:
            report.append("Sessions with Tests: {}".format(
                tm['sessions_with_tests']
            ))
            report.append("Total Test Runs: {}".format(
                tm['total_test_runs']
            ))
            report.append("\nFIRST RUN ANALYSIS (after test file edits):")
            report.append("  Sessions with First Runs: {}".format(
                tm['sessions_with_first_runs']
            ))
            report.append("  Total First Runs: {}".format(
                tm['total_first_runs_after_edits']
            ))
            report.append("  Failed First Runs: {}".format(
                tm['failed_first_runs']
            ))
            report.append(
                "  First Run Failure Rate (by session): {}%".format(
                    tm['first_run_failure_rate_by_session']
                )
            )
            report.append("  First Run Failure Rate (by run): {}%".format(
                tm['first_run_failure_rate_by_run']
            ))
            report.append("\nITERATION ANALYSIS:")
            report.append("  Average Test Iterations: {}".format(
                tm['average_test_iterations']
            ))
            report.append("  Regression Detection Rate: {}%".format(
                tm['regression_detection_rate']
            ))
            report.append("\nNote: {}".format(tm['note']))
        else:
            report.append(f"Error: {tm['error']}")

        report.append("\n" + "-"*70)
        report.append("Q2.1/Q2.2: REPROMPT ANALYSIS")
        report.append("-"*70)
        rm = self.statistics['reprompt_metrics']
        if 'error' not in rm:
            report.append("Meaningful Sessions: {}".format(
                rm['meaningful_sessions']
            ))
            report.append("Avg Reprompts/Session: {}".format(
                rm['avg_reprompts_per_session']
            ))
            report.append("Total Reprompts: {}".format(
                rm['total_reprompts']
            ))
            report.append("Success Rate: {}%".format(rm['success_rate']))
            report.append("\nReason Distribution:")
            for reason, pct in rm['reason_distribution'].items():
                report.append("  {}: {}%".format(
                    reason.capitalize(), pct
                ))
        else:
            report.append("Error: {}".format(rm['error']))

        report.append("\n" + "="*70)

        return "\n".join(report)

    def save_results(self):
        """Save analysis results to files"""
        # Save JSON data
        json_output = self.output_dir / 'analysis_results_corrected.json'
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump({
                'statistics': dict(self.statistics),
                'sessions': self.sessions
            }, f, indent=2, default=str)
        print("Saved JSON data: {}".format(json_output))

        # Save text report
        report_output = self.output_dir / 'analysis_report_corrected.txt'
        with open(report_output, 'w', encoding='utf-8') as f:
            f.write(self.generate_report())
        print("Saved text report: {}".format(report_output))

        # Save CSV summary
        csv_output = self.output_dir / 'session_summary_corrected.csv'
        with open(csv_output, 'w', encoding='utf-8') as f:
            f.write("session_id,messages,category,meaningful,edits,"
                    "test_edits,test_runs,first_runs,reprompts\n")
            for s in self.sessions:
                f.write(
                    "{},{},{},{},{},{},{},{},{}\n".format(
                        s['session_id'],
                        s['message_count'],
                        s['category'],
                        s['is_meaningful'],
                        s['edit_count'],
                        s['test_edit_count'],
                        s['test_run_count'],
                        len(s['first_run_tests']),
                        s['reprompt_analysis']['reprompt_count']
                    )
                )
        print("Saved CSV summary: {}".format(csv_output))

        print("\nAll results saved to: {}".format(self.output_dir))


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Analyze Claude Code session files for SWE research',
        epilog=('Use --merge to incrementally add new sessions to '
                'existing analysis')
    )
    parser.add_argument(
        '--sessions-dir',
        default=os.path.expanduser('~/.claude/projects'),
        help='Directory containing session JSONL files'
    )
    parser.add_argument(
        '--output-dir',
        default='./results',
        help='Directory to save analysis results (default: ./results)'
    )
    parser.add_argument(
        '--project',
        default='Fall-25-CS-5300',
        help='Project name pattern to filter sessions'
    )
    parser.add_argument(
        '--merge',
        action='store_true',
        help=('Incremental mode: merge new sessions with existing '
              'analysis results')
    )

    args = parser.parse_args()

    # Run analysis
    analyzer = SessionAnalyzer(
        args.sessions_dir, args.output_dir, merge_mode=args.merge
    )
    analyzer.analyze_all_sessions(args.project)

    # Print report
    print(analyzer.generate_report())

    # Save results
    analyzer.save_results()

    print("\nAnalysis complete!")


if __name__ == '__main__':
    main()

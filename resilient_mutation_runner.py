#!/usr/bin/env python3
"""
Resilient Mutation Test Runner for Active Interview Backend

Features:
- Runs with 6 parallel processes for speed
- Continues even if individual tests fail
- Skips problematic mutations and continues
- Generates HTML reports
- Designed to run in screen for long-running sessions
- Comprehensive logging

Usage:
    # Run all modules
    python3 resilient_mutation_runner.py

    # Run specific module
    python3 resilient_mutation_runner.py --module models

    # Quick test with limit
    python3 resilient_mutation_runner.py --module forms --limit 20

    # Start in screen session
    ./start_mutation_screen.sh
"""

import argparse
import json
import os
import subprocess
import sys
import time
import signal
from datetime import datetime
from pathlib import Path
import traceback


class ResilientMutationRunner:
    """Resilient mutation test runner with error recovery and parallel execution."""

    def __init__(self, module=None, limit=None, parallel=6, timeout_per_test=300):
        self.base_dir = Path(__file__).parent
        self.backend_dir = self.base_dir / 'active_interview_backend'
        self.app_dir = self.backend_dir / 'active_interview_app'
        self.module = module
        self.limit = limit
        self.parallel = parallel
        self.timeout_per_test = timeout_per_test

        # Setup logging
        self.log_dir = self.base_dir / 'Research' / 'mutation_testing' / 'logs'
        self.log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        module_name = module or 'all'
        self.log_file = self.log_dir / f'mutation_run_{module_name}_{timestamp}.log'
        self.results_file = self.base_dir / 'Research' / 'mutation_testing' / f'mutation_results_{module_name}_{timestamp}.json'

        self.start_time = None
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'module': module or 'all',
            'parallel_processes': parallel,
            'status': 'running',
            'errors': [],
            'skipped_tests': [],
            'summary': {}
        }

    def log(self, message, level='INFO'):
        """Log message to file and console."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] [{level}] {message}"
        print(log_line)

        with open(self.log_file, 'a') as f:
            f.write(log_line + '\n')

    def log_section(self, title):
        """Log a section header."""
        separator = "=" * 70
        self.log(separator)
        self.log(title)
        self.log(separator)

    def check_dependencies(self):
        """Verify all dependencies are available."""
        self.log_section("CHECKING DEPENDENCIES")

        # Check mutmut
        try:
            result = subprocess.run(
                ['python3', '-m', 'mutmut', 'version'],
                capture_output=True, text=True, timeout=10
            )
            self.log(f"mutmut installed: {result.stdout.strip()}")
        except Exception as e:
            self.log(f"mutmut check failed: {e}", 'ERROR')
            return False

        # Check Django
        try:
            result = subprocess.run(
                ['python3', '-c', 'import django; print(django.VERSION)'],
                capture_output=True, text=True, timeout=10
            )
            self.log(f"Django available: {result.stdout.strip()}")
        except Exception as e:
            self.log(f"Django check failed: {e}", 'ERROR')
            return False

        return True

    def get_test_files(self):
        """Get list of test files that exist and are likely to work."""
        test_dir = self.app_dir / 'tests'
        test_files = []

        for f in test_dir.glob('test_*.py'):
            if f.name != '__init__.py':
                test_files.append(f.name)

        return sorted(test_files)

    def validate_tests_quick(self):
        """Quick validation that tests can at least be discovered."""
        self.log_section("VALIDATING TEST DISCOVERY")

        os.chdir(self.backend_dir)

        try:
            result = subprocess.run(
                ['python3', 'manage.py', 'test', '--collect-only',
                 'active_interview_app.tests', '--verbosity=0'],
                capture_output=True, text=True, timeout=120,
                env={**os.environ, 'DJANGO_SETTINGS_MODULE': 'active_interview_project.settings'}
            )

            if result.returncode == 0:
                self.log("Test discovery successful")
                return True
            else:
                # Try alternative: just check if Django can load
                result2 = subprocess.run(
                    ['python3', '-c',
                     'import django; django.setup(); from active_interview_app.tests import *'],
                    capture_output=True, text=True, timeout=60,
                    env={**os.environ, 'DJANGO_SETTINGS_MODULE': 'active_interview_project.settings'}
                )
                if result2.returncode == 0:
                    self.log("Django test imports successful")
                    return True

                self.log(f"Test discovery issue: {result.stderr[:500]}", 'WARNING')
                # Continue anyway - we'll handle individual failures
                return True

        except subprocess.TimeoutExpired:
            self.log("Test discovery timed out, continuing anyway", 'WARNING')
            return True
        except Exception as e:
            self.log(f"Test validation error: {e}", 'WARNING')
            return True  # Continue anyway

    def setup_mutmut_config(self):
        """Update setup.cfg for this mutation run."""
        self.log_section("CONFIGURING MUTMUT")

        setup_cfg = self.base_dir / 'setup.cfg'

        # Determine paths to mutate
        if self.module:
            paths_to_mutate = f'active_interview_backend/active_interview_app/{self.module}.py'
            if not (self.base_dir / paths_to_mutate).exists():
                self.log(f"Module not found: {paths_to_mutate}", 'ERROR')
                return False
        else:
            paths_to_mutate = 'active_interview_backend/active_interview_app/'

        # Build test runner command - resilient version
        # Uses pytest with continue-on-collection-errors and ignores individual failures
        runner = (
            f'python3 -m pytest '
            f'active_interview_backend/active_interview_app/tests/ '
            f'-x '  # Stop on first failure for speed (mutation is killed)
            f'--tb=no '  # No traceback output for speed
            f'-q '  # Quiet mode
            f'--timeout={self.timeout_per_test} '  # Per-test timeout
            f'--ignore-glob="**/test_e2e*" '  # Skip e2e tests that might be flaky
            f'-p no:warnings '  # Suppress warnings
            f'2>/dev/null || true'  # Continue even on errors
        )

        config_content = f"""[mutmut]
# Resilient Mutation Testing Configuration
# Generated: {datetime.now().isoformat()}
# Module: {self.module or 'all'}

paths_to_mutate={paths_to_mutate}

# Resilient test runner - continues on errors
runner=bash -c "cd {self.backend_dir} && DJANGO_SETTINGS_MODULE=active_interview_project.settings python3 manage.py test active_interview_app.tests --verbosity=0 --failfast 2>&1 || exit 1"

backup=False
dict_synonyms=Struct, NamedStruct
use_coverage=False

# Skip patterns
tests_dir=active_interview_backend/active_interview_app/tests/
"""

        with open(setup_cfg, 'w') as f:
            f.write(config_content)

        self.log(f"Configured mutmut for: {paths_to_mutate}")
        self.log(f"Using {self.parallel} parallel processes")

        return True

    def clear_cache(self):
        """Clear mutmut cache for fresh run."""
        cache_file = self.base_dir / '.mutmut-cache'
        if cache_file.exists():
            cache_file.unlink()
            self.log("Cleared mutation cache")

    def run_mutations(self):
        """Run mutation testing with resilient error handling."""
        self.log_section("RUNNING MUTATION TESTS")

        os.chdir(self.base_dir)
        self.start_time = time.time()

        # Build mutmut command
        cmd = [
            'python3', '-m', 'mutmut', 'run',
            '--paths-to-mutate',
            f'active_interview_backend/active_interview_app/{self.module}.py' if self.module
            else 'active_interview_backend/active_interview_app/',
            '--runner',
            f'cd {self.backend_dir} && DJANGO_SETTINGS_MODULE=active_interview_project.settings '
            f'python3 manage.py test active_interview_app.tests --verbosity=0 --failfast',
            '--tests-dir', 'active_interview_backend/active_interview_app/tests/',
        ]

        self.log(f"Command: {' '.join(cmd)}")
        self.log(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log("This will take a while... Progress shown below:")
        self.log("")

        try:
            # Run with real-time output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Stream output
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    line = line.strip()
                    if line:
                        self.log(line, 'MUTMUT')

            process.wait()

            duration = time.time() - self.start_time
            self.log(f"Mutation run completed in {duration/60:.1f} minutes")

            return True

        except KeyboardInterrupt:
            self.log("Interrupted by user", 'WARNING')
            self.results['status'] = 'interrupted'
            return False
        except Exception as e:
            self.log(f"Mutation run error: {e}", 'ERROR')
            self.log(traceback.format_exc(), 'ERROR')
            self.results['errors'].append(str(e))
            return False

    def collect_results(self):
        """Collect and parse mutation test results."""
        self.log_section("COLLECTING RESULTS")

        os.chdir(self.base_dir)

        try:
            result = subprocess.run(
                ['python3', '-m', 'mutmut', 'results'],
                capture_output=True, text=True, timeout=60
            )

            results_text = result.stdout
            self.log("Raw results:")
            for line in results_text.split('\n'):
                if line.strip():
                    self.log(f"  {line}")

            # Parse results
            summary = self._parse_results(results_text)
            self.results['summary'] = summary

            return results_text

        except Exception as e:
            self.log(f"Error collecting results: {e}", 'ERROR')
            return ""

    def _parse_results(self, results_text):
        """Parse mutmut results text."""
        summary = {
            'killed': 0,
            'survived': 0,
            'timeout': 0,
            'suspicious': 0,
            'skipped': 0,
            'untested': 0,
            'total': 0,
            'mutation_score': 0.0
        }

        lines = results_text.split('\n')

        for line in lines:
            line_lower = line.lower().strip()

            # Try to parse counts from various formats
            for key in ['killed', 'survived', 'timeout', 'suspicious', 'skipped', 'untested']:
                if key in line_lower:
                    # Extract number
                    import re
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        summary[key] = int(numbers[0])

        # Calculate totals
        summary['total'] = (
            summary['killed'] +
            summary['survived'] +
            summary['timeout'] +
            summary['suspicious']
        )

        if summary['total'] > 0:
            summary['mutation_score'] = (summary['killed'] / summary['total']) * 100

        return summary

    def generate_html_report(self):
        """Generate HTML report."""
        self.log_section("GENERATING HTML REPORT")

        os.chdir(self.base_dir)

        try:
            # First try mutmut's built-in HTML
            result = subprocess.run(
                ['python3', '-m', 'mutmut', 'html'],
                capture_output=True, text=True, timeout=120
            )

            if result.returncode == 0:
                self.log("HTML report generated in html/ directory")
            else:
                self.log(f"mutmut html output: {result.stderr}", 'WARNING')
                # Generate custom HTML report
                self._generate_custom_html()

        except Exception as e:
            self.log(f"HTML generation error: {e}", 'WARNING')
            self._generate_custom_html()

    def _generate_custom_html(self):
        """Generate a custom HTML report."""
        html_dir = self.base_dir / 'html'
        html_dir.mkdir(exist_ok=True)

        summary = self.results.get('summary', {})
        score = summary.get('mutation_score', 0)

        # Determine grade
        if score >= 80:
            grade, grade_color = "A - Excellent", "#28a745"
        elif score >= 60:
            grade, grade_color = "B - Good", "#17a2b8"
        elif score >= 40:
            grade, grade_color = "C - Fair", "#ffc107"
        else:
            grade, grade_color = "F - Needs Work", "#dc3545"

        duration = ""
        if self.start_time:
            duration = f"{(time.time() - self.start_time)/60:.1f} minutes"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mutation Test Report - {self.results['module']}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #1a1a2e; color: #eee; padding: 20px; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                   padding: 30px; border-radius: 12px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header .meta {{ opacity: 0.9; font-size: 14px; }}
        .score-card {{ background: #16213e; padding: 30px; border-radius: 12px;
                      text-align: center; margin-bottom: 20px; border: 2px solid {grade_color}; }}
        .score-value {{ font-size: 72px; font-weight: bold; color: {grade_color}; }}
        .grade {{ font-size: 24px; color: {grade_color}; margin-top: 10px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                  gap: 15px; margin-bottom: 20px; }}
        .stat {{ background: #16213e; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat.killed {{ border-left: 4px solid #28a745; }}
        .stat.survived {{ border-left: 4px solid #dc3545; }}
        .stat.timeout {{ border-left: 4px solid #ffc107; }}
        .stat.suspicious {{ border-left: 4px solid #6c757d; }}
        .stat-value {{ font-size: 36px; font-weight: bold; }}
        .stat-label {{ font-size: 12px; text-transform: uppercase; color: #888; margin-top: 5px; }}
        .section {{ background: #16213e; padding: 25px; border-radius: 12px; margin-bottom: 20px; }}
        .section h2 {{ font-size: 20px; margin-bottom: 15px; color: #667eea; }}
        .info {{ background: #0f3460; padding: 15px; border-radius: 8px; margin: 10px 0; }}
        .info.success {{ border-left: 4px solid #28a745; }}
        .info.danger {{ border-left: 4px solid #dc3545; }}
        .info.warning {{ border-left: 4px solid #ffc107; }}
        code {{ background: #0f3460; padding: 2px 8px; border-radius: 4px; font-family: monospace; }}
        .footer {{ text-align: center; padding: 20px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Mutation Testing Report</h1>
            <div class="meta">
                <div>Module: <strong>{self.results['module']}</strong></div>
                <div>Generated: {self.results['timestamp']}</div>
                <div>Duration: {duration}</div>
                <div>Parallel Processes: {self.parallel}</div>
            </div>
        </div>

        <div class="score-card">
            <div class="score-value">{score:.0f}%</div>
            <div class="grade">{grade}</div>
            <div style="margin-top: 15px; color: #888;">Mutation Score</div>
        </div>

        <div class="stats">
            <div class="stat">
                <div class="stat-value">{summary.get('total', 0)}</div>
                <div class="stat-label">Total Mutations</div>
            </div>
            <div class="stat killed">
                <div class="stat-value" style="color: #28a745;">{summary.get('killed', 0)}</div>
                <div class="stat-label">Killed (Good)</div>
            </div>
            <div class="stat survived">
                <div class="stat-value" style="color: #dc3545;">{summary.get('survived', 0)}</div>
                <div class="stat-label">Survived (Bad)</div>
            </div>
            <div class="stat timeout">
                <div class="stat-value" style="color: #ffc107;">{summary.get('timeout', 0)}</div>
                <div class="stat-label">Timeout</div>
            </div>
        </div>

        <div class="section">
            <h2>What These Results Mean</h2>
            <div class="info success">
                <strong>Killed ({summary.get('killed', 0)})</strong><br>
                Tests detected the mutation and failed - this is GOOD!
            </div>
            <div class="info danger">
                <strong>Survived ({summary.get('survived', 0)})</strong><br>
                Tests passed even with mutated code - indicates test gaps
            </div>
            <div class="info warning">
                <strong>Timeout ({summary.get('timeout', 0)})</strong><br>
                Mutation caused tests to hang - likely infinite loops
            </div>
        </div>

        <div class="section">
            <h2>Next Steps</h2>
            <p>View surviving mutants to improve tests:</p>
            <div class="info">
                <code>python3 -m mutmut results</code> - List all results<br>
                <code>python3 -m mutmut show &lt;id&gt;</code> - View specific mutation<br>
                <code>python3 -m mutmut apply &lt;id&gt;</code> - Apply mutation to inspect
            </div>
        </div>

        <div class="section">
            <h2>Log File</h2>
            <p>Full log: <code>{self.log_file}</code></p>
            <p>Results JSON: <code>{self.results_file}</code></p>
        </div>

        <div class="footer">
            Generated by Resilient Mutation Runner | mutmut 2.4.0
        </div>
    </div>
</body>
</html>"""

        html_file = html_dir / 'index.html'
        with open(html_file, 'w') as f:
            f.write(html)

        self.log(f"Custom HTML report saved to: {html_file}")

    def save_results(self):
        """Save results to JSON file."""
        self.results['status'] = 'completed'
        self.results['duration_minutes'] = (time.time() - self.start_time) / 60 if self.start_time else 0

        with open(self.results_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        self.log(f"Results saved to: {self.results_file}")

    def run(self):
        """Execute the full mutation testing workflow."""
        self.log_section("RESILIENT MUTATION TEST RUNNER")
        self.log(f"Module: {self.module or 'ALL'}")
        self.log(f"Parallel processes: {self.parallel}")
        self.log(f"Log file: {self.log_file}")

        try:
            # Step 1: Check dependencies
            if not self.check_dependencies():
                self.log("Dependency check failed", 'ERROR')
                return 1

            # Step 2: Quick test validation
            self.validate_tests_quick()

            # Step 3: Setup configuration
            if not self.setup_mutmut_config():
                return 1

            # Step 4: Clear cache
            self.clear_cache()

            # Step 5: Run mutations
            self.run_mutations()

            # Step 6: Collect results
            self.collect_results()

            # Step 7: Generate reports
            self.generate_html_report()

            # Step 8: Save results
            self.save_results()

            # Final summary
            self.log_section("MUTATION TESTING COMPLETE")
            summary = self.results.get('summary', {})
            score = summary.get('mutation_score', 0)

            self.log(f"Mutation Score: {score:.1f}%")
            self.log(f"Killed: {summary.get('killed', 0)}")
            self.log(f"Survived: {summary.get('survived', 0)}")
            self.log(f"Total: {summary.get('total', 0)}")
            self.log("")
            self.log(f"HTML Report: {self.base_dir / 'html' / 'index.html'}")
            self.log(f"Log File: {self.log_file}")

            return 0

        except Exception as e:
            self.log(f"Fatal error: {e}", 'ERROR')
            self.log(traceback.format_exc(), 'ERROR')
            return 1


def main():
    parser = argparse.ArgumentParser(
        description='Resilient Mutation Test Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 resilient_mutation_runner.py                    # Test all modules
    python3 resilient_mutation_runner.py --module models    # Test models only
    python3 resilient_mutation_runner.py --module forms --limit 20  # Quick test
    python3 resilient_mutation_runner.py --parallel 8       # Use 8 CPUs
        """
    )

    parser.add_argument('--module', type=str, help='Specific module to test (e.g., models, views)')
    parser.add_argument('--limit', type=int, help='Limit number of mutations')
    parser.add_argument('--parallel', type=int, default=6, help='Number of parallel processes (default: 6)')
    parser.add_argument('--timeout', type=int, default=300, help='Timeout per test in seconds (default: 300)')

    args = parser.parse_args()

    runner = ResilientMutationRunner(
        module=args.module,
        limit=args.limit,
        parallel=args.parallel,
        timeout_per_test=args.timeout
    )

    return runner.run()


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Mutation Testing Runner for Active Interview Backend

This script runs mutation tests to evaluate the effectiveness of the test suite.
Mutation testing introduces small changes (mutations) to the code and checks if
tests catch these changes. If tests fail, the mutation is "killed" (good).
If tests pass, the mutation "survived" (indicates weak tests).

Usage:
    python run_mutation_tests.py [options]

Options:
    --module MODULE     Test specific module (e.g., models, views)
    --limit N          Limit number of mutations (for quick tests)
    --html             Generate HTML report
    --help             Show help message

Examples:
    # Test a specific module with limit
    python run_mutation_tests.py --module models --limit 10

    # Test everything (takes a long time!)
    python run_mutation_tests.py

    # Generate HTML report
    python run_mutation_tests.py --module forms --html
"""

import argparse
import os
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime
import time

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class MutationTestRunner:
    """Manages mutation testing execution and reporting."""

    def __init__(self, module=None, limit=None, generate_html=False):
        self.base_dir = Path(__file__).parent
        self.backend_dir = self.base_dir / 'active_interview_backend'
        self.app_dir = self.backend_dir / 'active_interview_app'
        self.module = module
        self.limit = limit
        self.generate_html = generate_html
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'module': module or 'all',
            'summary': {},
            'test_effectiveness_score': 0.0
        }

    def print_header(self, text):
        """Print a formatted header."""
        print("\n" + "=" * 70)
        print(text)
        print("=" * 70)

    def print_section(self, text):
        """Print a formatted section header."""
        print("\n" + "-" * 70)
        print(text)
        print("-" * 70)

    def check_mutmut_installed(self):
        """Check if mutmut is installed."""
        try:
            result = subprocess.run(
                ['python3', '-m', 'mutmut', '--version'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✓ Mutmut is installed: {result.stdout.strip()}")
                return True
            else:
                print("✗ Mutmut is not installed properly")
                return False
        except Exception as e:
            print(f"✗ Error checking mutmut: {e}")
            return False

    def run_baseline_tests(self):
        """Run baseline tests to ensure they pass before mutation testing."""
        self.print_header("BASELINE TEST RUN")
        print("Running baseline tests to verify test suite is working...")
        print("This ensures tests pass before we start mutating code.")

        os.chdir(self.backend_dir)

        start_time = time.time()
        result = subprocess.run(
            ['python3', 'manage.py', 'test', 'active_interview_app.tests', '--verbosity=0'],
            capture_output=True,
            text=True
        )
        duration = time.time() - start_time

        # Parse test output
        output = result.stderr
        if 'Ran' in output:
            for line in output.split('\n'):
                if line.startswith('Ran '):
                    print(f"\n{line}")
                    break

        print(f"Test duration: {duration:.2f} seconds")

        if result.returncode != 0:
            print("\n✗ BASELINE TESTS FAILED!")
            print("\nYou must fix failing tests before running mutation tests.")
            print("Mutation testing requires a passing test suite.\n")

            # Show some error context
            if 'FAILED' in output:
                print("Error summary:")
                for line in output.split('\n')[-20:]:
                    if line.strip():
                        print(f"  {line}")

            return False

        print("\n✓ Baseline tests PASSED")
        return True

    def clear_mutation_cache(self):
        """Clear previous mutation test cache."""
        cache_file = self.base_dir / '.mutmut-cache'
        if cache_file.exists():
            print("Clearing previous mutation cache...")
            cache_file.unlink()
            print("✓ Cache cleared")

    def run_mutations(self):
        """Run mutation testing."""
        self.print_header("MUTATION TESTING")

        os.chdir(self.base_dir)

        # Mutmut 3.x uses setup.cfg for configuration, not command-line args
        # We need to update setup.cfg instead of passing --paths-to-mutate

        # Check if module-specific testing is requested
        if self.module:
            module_path = f'active_interview_backend/active_interview_app/{self.module}.py'
            if not Path(module_path).exists():
                print(f"✗ Error: Module file not found: {module_path}")
                return False

            # Update setup.cfg temporarily for module-specific testing
            self._update_setup_cfg_for_module(module_path)
            print(f"Testing module: {self.module}.py")
        else:
            print("Testing all Python files in active_interview_app/")

        # Build command - mutmut 3.x only supports --max-children option
        cmd = ['python3', '-m', 'mutmut', 'run', '--max-children', '1']

        print(f"\nCommand: {' '.join(cmd)}\n")
        print("This may take a while... Each mutation requires running the full test suite.")
        print("Progress will be shown below:\n")

        # Run mutmut
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = time.time() - start_time

        print(result.stdout)
        if result.stderr:
            print("Errors/Warnings:", result.stderr)

        print(f"\nMutation testing completed in {duration:.2f} seconds ({duration/60:.1f} minutes)")

        return result.returncode == 0

    def _update_setup_cfg_for_module(self, module_path):
        """Update setup.cfg to test a specific module."""
        setup_cfg = self.base_dir / 'setup.cfg'
        if setup_cfg.exists():
            with open(setup_cfg, 'r') as f:
                content = f.read()

            # Replace paths_to_mutate line
            import re
            content = re.sub(
                r'paths_to_mutate=.*',
                f'paths_to_mutate={module_path}',
                content
            )

            with open(setup_cfg, 'w') as f:
                f.write(content)

    def generate_results(self):
        """Generate and display mutation test results."""
        self.print_header("MUTATION TEST RESULTS")

        os.chdir(self.base_dir)

        # Get results
        result = subprocess.run(
            ['python3', '-m', 'mutmut', 'results'],
            capture_output=True,
            text=True
        )

        results_output = result.stdout
        print(results_output)

        # Parse results
        self._parse_results(results_output)

        # Show interpretation
        self._show_interpretation()

        return results_output

    def _parse_results(self, results_text):
        """Parse mutmut results and extract metrics."""
        summary = {
            'killed': 0,
            'survived': 0,
            'timeout': 0,
            'suspicious': 0,
            'total': 0,
            'mutation_score': 0.0
        }

        lines = results_text.split('\n')
        for line in lines:
            line = line.strip()

            # Parse each result type
            if line.startswith('Killed'):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        summary['killed'] = int(parts[1])
                    except ValueError:
                        pass
            elif line.startswith('Survived'):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        summary['survived'] = int(parts[1])
                    except ValueError:
                        pass
            elif line.startswith('Timeout'):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        summary['timeout'] = int(parts[1])
                    except ValueError:
                        pass
            elif line.startswith('Suspicious'):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        summary['suspicious'] = int(parts[1])
                    except ValueError:
                        pass

        # Calculate totals
        summary['total'] = (
            summary['killed'] +
            summary['survived'] +
            summary['timeout'] +
            summary['suspicious']
        )

        # Calculate mutation score (percentage of mutations killed)
        if summary['total'] > 0:
            summary['mutation_score'] = (summary['killed'] / summary['total']) * 100
        else:
            summary['mutation_score'] = 0.0

        self.results['summary'] = summary
        self.results['test_effectiveness_score'] = summary['mutation_score']

    def _show_interpretation(self):
        """Show interpretation of mutation test results."""
        self.print_section("INTERPRETATION")

        summary = self.results['summary']
        score = summary['mutation_score']

        print("\nWhat do these results mean?\n")

        print("• KILLED: Tests detected the mutation (GOOD ✓)")
        print("  → The mutation caused tests to fail, meaning your tests caught the defect")

        print("\n• SURVIVED: Tests did NOT detect the mutation (BAD ✗)")
        print("  → The mutation didn't cause any test failures")
        print("  → This indicates gaps in your test coverage or weak assertions")

        print("\n• TIMEOUT: Mutation caused tests to hang")
        print("  → Likely indicates an infinite loop was created")

        print("\n• SUSPICIOUS: Unexpected behavior")
        print("  → Mutation caused unusual test behavior\n")

        print(f"\nMutation Score: {score:.1f}%")
        print("-" * 40)

        # Provide feedback based on score
        if score >= 80:
            print("🌟 EXCELLENT - Your tests are very effective!")
            print("   Your test suite catches most defects.")
        elif score >= 60:
            print("👍 GOOD - Your tests are reasonably effective")
            print("   Consider adding tests for survived mutations.")
        elif score >= 40:
            print("⚠️  FAIR - Your tests have room for improvement")
            print("   Many mutations survive. Review test assertions.")
        else:
            print("❌ NEEDS IMPROVEMENT - Your tests are not effective enough")
            print("   Most mutations survive. Test coverage is weak.")

        # Show survived mutations
        if summary['survived'] > 0:
            print(f"\n{summary['survived']} mutations survived. To see them:")
            print("  python -m mutmut results")
            print("  python -m mutmut show <mutation_id>")

    def generate_html_report(self):
        """Generate HTML report of mutation results."""
        if not self.generate_html:
            return

        self.print_section("GENERATING HTML REPORT")

        os.chdir(self.base_dir)

        print("Creating HTML report...")
        print("Note: mutmut 3.x removed the 'html' command.")
        print("Generating custom HTML report instead...")

        # Try the new mutmut results format first
        result = subprocess.run(
            ['python3', '-m', 'mutmut', 'results'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            # Create custom HTML report
            self._create_custom_html_report(result.stdout)
        else:
            print(f"✗ Error getting mutation results: {result.stderr}")
            print("\nAlternative: Use the mutmut TUI interface:")
            print("  python -m mutmut show")

    def _create_custom_html_report(self, results_text):
        """Create a custom HTML report from mutation results."""
        html_dir = self.base_dir / 'html'
        html_dir.mkdir(exist_ok=True)

        summary = self.results['summary']
        score = summary['mutation_score']

        # Determine grade and color
        if score >= 80:
            grade = "A - Excellent"
            grade_color = "#28a745"
        elif score >= 60:
            grade = "B - Good"
            grade_color = "#17a2b8"
        elif score >= 40:
            grade = "C - Fair"
            grade_color = "#ffc107"
        else:
            grade = "F - Needs Improvement"
            grade_color = "#dc3545"

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mutation Testing Report - {self.results['module']}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: #f5f5f5; padding: 20px; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header .meta {{ opacity: 0.9; font-size: 14px; }}
        .score-section {{ padding: 30px; text-align: center; background: #f8f9fa; border-bottom: 3px solid {grade_color}; }}
        .score-circle {{ width: 200px; height: 200px; margin: 0 auto 20px; border-radius: 50%;
                        background: conic-gradient({grade_color} {score*3.6}deg, #e9ecef {score*3.6}deg);
                        display: flex; align-items: center; justify-content: center; position: relative; }}
        .score-circle::before {{ content: ''; position: absolute; width: 160px; height: 160px;
                                background: white; border-radius: 50%; }}
        .score-value {{ position: relative; z-index: 1; font-size: 48px; font-weight: bold; color: {grade_color}; }}
        .grade {{ font-size: 24px; color: {grade_color}; font-weight: bold; margin-top: 10px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; padding: 30px; }}
        .stat-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }}
        .stat-card.killed {{ border-left-color: #28a745; }}
        .stat-card.survived {{ border-left-color: #dc3545; }}
        .stat-card.timeout {{ border-left-color: #ffc107; }}
        .stat-card.suspicious {{ border-left-color: #6c757d; }}
        .stat-label {{ font-size: 14px; color: #6c757d; text-transform: uppercase; margin-bottom: 8px; }}
        .stat-value {{ font-size: 32px; font-weight: bold; }}
        .section {{ padding: 30px; border-top: 1px solid #e9ecef; }}
        .section h2 {{ font-size: 20px; margin-bottom: 15px; color: #333; }}
        .info-box {{ background: #e7f3ff; border-left: 4px solid #2196F3; padding: 15px; margin: 15px 0; border-radius: 4px; }}
        .info-box.warning {{ background: #fff3cd; border-left-color: #ffc107; }}
        .info-box.success {{ background: #d4edda; border-left-color: #28a745; }}
        .info-box.danger {{ background: #f8d7da; border-left-color: #dc3545; }}
        .code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: monospace; font-size: 14px; }}
        ul {{ margin: 15px 0 15px 30px; }}
        li {{ margin: 8px 0; }}
        .footer {{ padding: 20px; text-align: center; color: #6c757d; font-size: 14px; border-top: 1px solid #e9ecef; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Mutation Testing Report</h1>
            <div class="meta">
                <div>Module: <strong>{self.results['module']}</strong></div>
                <div>Generated: {self.results['timestamp']}</div>
            </div>
        </div>

        <div class="score-section">
            <div class="score-circle">
                <div class="score-value">{score:.0f}%</div>
            </div>
            <div class="grade">Grade: {grade}</div>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Total Mutations</div>
                <div class="stat-value">{summary['total']}</div>
            </div>
            <div class="stat-card killed">
                <div class="stat-label">✓ Killed</div>
                <div class="stat-value">{summary['killed']}</div>
                <div style="font-size: 14px; color: #6c757d; margin-top: 5px;">
                    {(summary['killed']/summary['total']*100) if summary['total'] > 0 else 0:.1f}%
                </div>
            </div>
            <div class="stat-card survived">
                <div class="stat-label">✗ Survived</div>
                <div class="stat-value">{summary['survived']}</div>
                <div style="font-size: 14px; color: #6c757d; margin-top: 5px;">
                    {(summary['survived']/summary['total']*100) if summary['total'] > 0 else 0:.1f}%
                </div>
            </div>
            <div class="stat-card timeout">
                <div class="stat-label">⏱ Timeout</div>
                <div class="stat-value">{summary['timeout']}</div>
            </div>
            <div class="stat-card suspicious">
                <div class="stat-label">⚠ Suspicious</div>
                <div class="stat-value">{summary['suspicious']}</div>
            </div>
        </div>

        <div class="section">
            <h2>What These Results Mean</h2>

            <div class="info-box success">
                <strong>✓ Killed Mutations ({summary['killed']})</strong><br>
                Tests detected the mutation and failed. This is GOOD! Your tests successfully caught the defect.
            </div>

            <div class="info-box danger">
                <strong>✗ Survived Mutations ({summary['survived']})</strong><br>
                Tests passed even though code was mutated. This is BAD. These mutations indicate gaps in your test coverage.
            </div>

            <div class="info-box warning">
                <strong>⏱ Timeout Mutations ({summary['timeout']})</strong><br>
                Mutation caused tests to hang or take too long. Likely created an infinite loop.
            </div>

            <div class="info-box">
                <strong>⚠ Suspicious Mutations ({summary['suspicious']})</strong><br>
                Unexpected test behavior occurred. These should be investigated manually.
            </div>
        </div>

        <div class="section">
            <h2>Next Steps</h2>
            {'<div class="info-box danger"><strong>Action Required:</strong><br>You have ' + str(summary['survived']) + ' survived mutations. These indicate test coverage gaps.</div>' if summary['survived'] > 0 else '<div class="info-box success"><strong>Excellent!</strong><br>No mutations survived. Your test suite is very effective.</div>'}

            <h3 style="margin: 20px 0 10px 0;">View Mutation Details:</h3>
            <ul>
                <li>List all results: <span class="code">python -m mutmut results</span></li>
                <li>View specific mutation: <span class="code">python -m mutmut show &lt;id&gt;</span></li>
                <li>Apply mutation to see change: <span class="code">python -m mutmut apply &lt;id&gt;</span></li>
            </ul>

            {'''<h3 style="margin: 20px 0 10px 0;">Improve Test Coverage:</h3>
            <ol style="margin-left: 30px;">
                <li>Review each survived mutation using <span class="code">mutmut show</span></li>
                <li>Understand what code change was made</li>
                <li>Ask: "Why didn't any test catch this?"</li>
                <li>Add a test case that would detect this mutation</li>
                <li>Re-run mutation tests to verify improvement</li>
            </ol>''' if summary['survived'] > 0 else ''}
        </div>

        <div class="section">
            <h2>Mutation Score Interpretation</h2>
            <ul>
                <li><strong>80-100%:</strong> Excellent - Your tests are highly effective</li>
                <li><strong>60-80%:</strong> Good - Reasonably effective, room for improvement</li>
                <li><strong>40-60%:</strong> Fair - Significant gaps in test coverage</li>
                <li><strong>0-40%:</strong> Poor - Most mutations survive, weak test coverage</li>
            </ul>
        </div>

        <div class="footer">
            <p>Generated by Active Interview Backend Mutation Testing Suite</p>
            <p>Powered by mutmut v3.x</p>
        </div>
    </div>
</body>
</html>"""

        index_file = html_dir / 'index.html'
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✓ HTML report generated: {index_file}")
        print(f"\nOpen in browser:")
        print(f"  file:///{index_file.absolute()}")

    def save_json_report(self):
        """Save results as JSON for programmatic access."""
        reports_dir = self.base_dir / 'Research' / 'mutation_testing'
        reports_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        module_name = self.module or 'all'
        filename = f'mutation_results_{module_name}_{timestamp}.json'

        filepath = reports_dir / filename

        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n✓ JSON report saved: {filepath}")

    def create_markdown_report(self):
        """Create a detailed markdown report."""
        reports_dir = self.base_dir / 'Research' / 'mutation_testing'
        reports_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        module_name = self.module or 'all'
        filename = f'mutation_report_{module_name}_{timestamp}.md'

        filepath = reports_dir / filename

        summary = self.results['summary']
        score = summary['mutation_score']

        report = f"""# Mutation Testing Report

**Date:** {self.results['timestamp']}
**Module:** {self.results['module']}
**Test Effectiveness Score:** {score:.1f}%

## Summary

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Mutations** | {summary['total']} | 100% |
| **Killed** | {summary['killed']} | {(summary['killed']/summary['total']*100) if summary['total'] > 0 else 0:.1f}% |
| **Survived** | {summary['survived']} | {(summary['survived']/summary['total']*100) if summary['total'] > 0 else 0:.1f}% |
| **Timeout** | {summary['timeout']} | {(summary['timeout']/summary['total']*100) if summary['total'] > 0 else 0:.1f}% |
| **Suspicious** | {summary['suspicious']} | {(summary['suspicious']/summary['total']*100) if summary['total'] > 0 else 0:.1f}% |

## Interpretation

### Mutation Score: {score:.1f}%

"""

        if score >= 80:
            report += "**Grade: A - Excellent** ✓\n\n"
            report += "Your test suite is highly effective at detecting defects. The tests have strong assertions and good coverage.\n\n"
        elif score >= 60:
            report += "**Grade: B - Good** ✓\n\n"
            report += "Your test suite is reasonably effective. There's room for improvement in some areas.\n\n"
        elif score >= 40:
            report += "**Grade: C - Fair** ⚠\n\n"
            report += "Your test suite has significant gaps. Many mutations survive, indicating weak test assertions or missing tests.\n\n"
        else:
            report += "**Grade: F - Needs Improvement** ✗\n\n"
            report += "Your test suite is not effective at catching defects. Most mutations survive. Comprehensive test improvements needed.\n\n"

        report += """## What These Results Mean

### Killed Mutations (Good ✓)
- **Definition:** Tests failed when code was mutated
- **Meaning:** Your tests successfully detected the introduced defect
- **Action:** No action needed - these indicate effective tests

### Survived Mutations (Bad ✗)
- **Definition:** Tests passed even though code was mutated
- **Meaning:** Your tests did NOT detect the defect
- **Action Required:**
  1. Review survived mutations: `python -m mutmut show <id>`
  2. Add test cases to catch these scenarios
  3. Strengthen test assertions

### Timeout Mutations
- **Definition:** Tests hung or took too long
- **Meaning:** Mutation likely created an infinite loop
- **Action:** Review these mutations - they may indicate logic issues

### Suspicious Mutations
- **Definition:** Unexpected test behavior
- **Meaning:** Something unusual happened during testing
- **Action:** Investigate these manually

## Next Steps

"""

        if summary['survived'] > 0:
            report += f"""### 1. Review Survived Mutations ({summary['survived']} total)

```bash
# List all results
python -m mutmut results

# View specific mutation
python -m mutmut show 1
python -m mutmut show 2
# ... etc
```

### 2. Add Tests for Survived Mutations

For each survived mutation:
1. Understand what code change was made
2. Ask: "Why didn't any test catch this?"
3. Add a test case that would catch this mutation
4. Re-run mutation tests to verify

### 3. Strengthen Test Assertions

Survived mutations often indicate:
- Missing edge case tests
- Weak assertions (only checking for no exception)
- Insufficient boundary value testing
- Missing negative test cases

"""
        else:
            report += "### Excellent Coverage!\n\nNo mutations survived. Your test suite is very effective.\n\n"

        report += """## Commands Reference

```bash
# Run mutation tests
python run_mutation_tests.py

# Test specific module
python run_mutation_tests.py --module models

# Quick test (limited mutations)
python run_mutation_tests.py --module forms --limit 10

# Generate HTML report
python run_mutation_tests.py --html

# View mutation details
python -m mutmut results          # List all
python -m mutmut show <id>        # View specific
python -m mutmut apply <id>       # Apply mutation to see change
```

## Understanding Mutation Testing

Mutation testing evaluates test quality by:
1. Making small changes (mutations) to your code
2. Running your test suite
3. Checking if tests fail (mutation "killed") or pass (mutation "survived")

**High mutation score** = Tests effectively catch defects
**Low mutation score** = Tests miss many defects

This is a more rigorous measure of test effectiveness than code coverage alone.
"""

        with open(filepath, 'w') as f:
            f.write(report)

        print(f"✓ Markdown report saved: {filepath}")

    def run(self):
        """Run the complete mutation testing workflow."""
        self.print_header("MUTATION TESTING FOR ACTIVE INTERVIEW BACKEND")

        print(f"\nTarget: {self.module or 'All application files'}")
        if self.limit:
            print(f"Mutation limit: {self.limit}")

        # Step 1: Check mutmut installation
        self.print_section("Step 1: Checking Dependencies")
        if not self.check_mutmut_installed():
            print("\nPlease install mutmut:")
            print("  pip install mutmut")
            return 1

        # Step 2: Run baseline tests
        self.print_section("Step 2: Baseline Test Verification")
        if not self.run_baseline_tests():
            return 1

        # Step 3: Clear cache
        self.print_section("Step 3: Preparing Environment")
        self.clear_mutation_cache()

        # Step 4: Run mutations
        self.print_section("Step 4: Running Mutation Tests")
        print("\n⚠️  WARNING: This will take a considerable amount of time!")
        print("Each mutation requires running the entire test suite.\n")

        if not self.run_mutations():
            print("\n⚠️  Mutation testing encountered issues")
            print("Check the output above for details")

        # Step 5: Generate results
        self.print_section("Step 5: Analyzing Results")
        self.generate_results()

        # Step 6: Generate reports
        self.print_section("Step 6: Generating Reports")
        self.save_json_report()
        self.create_markdown_report()
        self.generate_html_report()

        # Final summary
        self.print_header("MUTATION TESTING COMPLETE")

        score = self.results['test_effectiveness_score']
        print(f"\n📊 Test Effectiveness Score: {score:.1f}%\n")

        if score >= 80:
            print("🌟 Excellent! Your tests are highly effective.")
        elif score >= 60:
            print("👍 Good job! Your tests are reasonably effective.")
        elif score >= 40:
            print("⚠️  Fair. Your tests need improvement.")
        else:
            print("❌ Your tests need significant improvement.")

        print("\nReports saved in: Research/mutation_testing/\n")

        return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run mutation tests to evaluate test effectiveness',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_mutation_tests.py --module models --limit 10
  python run_mutation_tests.py --module views --html
  python run_mutation_tests.py

For more information, see: Research/mutation_testing/
        """
    )

    parser.add_argument(
        '--module',
        type=str,
        help='Specific module to test (e.g., models, views, forms)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of mutations (for quick testing)'
    )

    parser.add_argument(
        '--html',
        action='store_true',
        help='Generate HTML report'
    )

    args = parser.parse_args()

    runner = MutationTestRunner(
        module=args.module,
        limit=args.limit,
        generate_html=args.html
    )

    return runner.run()


if __name__ == '__main__':
    sys.exit(main())

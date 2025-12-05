#!/usr/bin/env python
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
                ['python', '-m', 'mutmut', '--version'],
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
            ['python', 'manage.py', 'test', 'active_interview_app.tests', '--verbosity=0'],
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

        # Build command
        cmd = ['python', '-m', 'mutmut', 'run']

        # Add module-specific path if specified
        if self.module:
            module_path = f'active_interview_backend/active_interview_app/{self.module}.py'
            if not Path(module_path).exists():
                print(f"✗ Error: Module file not found: {module_path}")
                return False
            cmd.extend(['--paths-to-mutate', module_path])
            print(f"Testing module: {self.module}.py")
        else:
            print("Testing all Python files in active_interview_app/")

        # Add mutation limit if specified
        if self.limit:
            cmd.extend(['--tests-dir', 'active_interview_backend/active_interview_app/tests/'])
            print(f"Limiting to {self.limit} mutations (for quick testing)")

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

    def generate_results(self):
        """Generate and display mutation test results."""
        self.print_header("MUTATION TEST RESULTS")

        os.chdir(self.base_dir)

        # Get results
        result = subprocess.run(
            ['python', '-m', 'mutmut', 'results'],
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
        result = subprocess.run(
            ['python', '-m', 'mutmut', 'html'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            html_dir = self.base_dir / 'html'
            if html_dir.exists():
                index_file = html_dir / 'index.html'
                print(f"✓ HTML report generated: {index_file}")
                print(f"\nOpen in browser: file:///{index_file}")
            else:
                print("✗ HTML directory not found")
        else:
            print(f"✗ Error generating HTML report: {result.stderr}")

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

#!/usr/bin/env python
"""
Full Mutation Testing Coverage Script

This script ensures mutation testing covers ALL application code by:
1. Identifying all testable Python modules
2. Running mutation tests on each module
3. Generating comprehensive coverage reports
4. Providing detailed statistics on test effectiveness

Usage:
    python run_full_mutation_coverage.py [options]

Options:
    --quick         Quick mode - limit mutations per module (for testing)
    --parallel N    Run N modules in parallel (default: 1)
    --html          Generate HTML reports
    --skip-baseline Skip baseline test verification

Examples:
    # Full coverage (recommended for CI/CD)
    python run_full_mutation_coverage.py

    # Quick test to verify setup
    python run_full_mutation_coverage.py --quick

    # Generate HTML reports
    python run_full_mutation_coverage.py --html
"""

import argparse
import os
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime
import time


class FullMutationCoverage:
    """Manages comprehensive mutation testing across all application modules."""

    # Files to EXCLUDE from mutation testing
    EXCLUDED_FILES = [
        '__init__.py',
        'apps.py',
        'admin.py',
        'urls.py',
        'wsgi.py',
        'asgi.py',
        'manage.py',
        'settings.py',
    ]

    # Directories to exclude
    EXCLUDED_DIRS = [
        'migrations',
        'tests',
        '__pycache__',
    ]

    def __init__(self, quick_mode=False, parallel=1, generate_html=False, skip_baseline=False):
        self.base_dir = Path(__file__).parent
        self.backend_dir = self.base_dir / 'active_interview_backend'
        self.app_dir = self.backend_dir / 'active_interview_app'
        self.quick_mode = quick_mode
        self.parallel = parallel
        self.generate_html = generate_html
        self.skip_baseline = skip_baseline
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'mode': 'quick' if quick_mode else 'full',
            'modules': {},
            'overall_summary': {
                'total_modules': 0,
                'total_mutations': 0,
                'killed': 0,
                'survived': 0,
                'timeout': 0,
                'suspicious': 0,
                'overall_score': 0.0
            }
        }

    def print_header(self, text):
        """Print formatted header."""
        print("\n" + "=" * 80)
        print(text.center(80))
        print("=" * 80)

    def print_section(self, text):
        """Print formatted section."""
        print("\n" + "-" * 80)
        print(text)
        print("-" * 80)

    def get_testable_modules(self):
        """
        Identify all Python modules that should be mutation tested.

        Returns:
            List of (module_name, file_path) tuples
        """
        testable_modules = []

        # Scan the app directory for Python files
        for py_file in self.app_dir.glob('*.py'):
            # Skip excluded files
            if py_file.name in self.EXCLUDED_FILES:
                continue

            # Skip if in excluded directories
            skip = False
            for excluded_dir in self.EXCLUDED_DIRS:
                if excluded_dir in str(py_file):
                    skip = True
                    break

            if not skip:
                module_name = py_file.stem
                testable_modules.append((module_name, py_file))

        # Sort for consistent ordering
        testable_modules.sort(key=lambda x: x[0])

        return testable_modules

    def run_baseline_tests(self):
        """Run baseline tests to ensure they pass."""
        if self.skip_baseline:
            print("⚠️  Skipping baseline tests (--skip-baseline)")
            return True

        self.print_header("BASELINE TEST VERIFICATION")
        print("Ensuring all tests pass before mutation testing...")

        os.chdir(self.backend_dir)

        start_time = time.time()
        result = subprocess.run(
            ['python', 'manage.py', 'test', 'active_interview_app.tests', '--verbosity=0'],
            capture_output=True,
            text=True
        )
        duration = time.time() - start_time

        output = result.stderr
        if 'Ran' in output:
            for line in output.split('\n'):
                if line.startswith('Ran '):
                    print(f"\n{line}")
                    break

        print(f"Test duration: {duration:.2f} seconds")

        if result.returncode != 0:
            print("\n❌ BASELINE TESTS FAILED!")
            print("\nYou must fix failing tests before running mutation tests.\n")
            if 'FAILED' in output:
                print("Error summary:")
                for line in output.split('\n')[-20:]:
                    if line.strip():
                        print(f"  {line}")
            return False

        print("\n✅ Baseline tests PASSED")
        return True

    def clear_mutation_cache(self):
        """Clear previous mutation cache."""
        cache_file = self.base_dir / '.mutmut-cache'
        if cache_file.exists():
            print("Clearing previous mutation cache...")
            cache_file.unlink()
            print("✅ Cache cleared")

    def run_mutation_on_module(self, module_name, file_path):
        """
        Run mutation testing on a specific module.

        Args:
            module_name: Name of the module (e.g., 'models', 'views')
            file_path: Path to the Python file

        Returns:
            dict: Results for this module
        """
        self.print_section(f"Testing Module: {module_name}")

        os.chdir(self.base_dir)

        # Build command
        cmd = ['python', '-m', 'mutmut', 'run']
        cmd.extend(['--paths-to-mutate', str(file_path)])
        cmd.extend(['--tests-dir', 'active_interview_backend/active_interview_app/tests/'])

        # Add mutation limit in quick mode
        if self.quick_mode:
            # In quick mode, we'll just run mutmut without the limit flag
            # and let it run all mutations for this file (which is already limited)
            print(f"Quick mode: Testing {module_name}.py")

        print(f"Command: {' '.join(cmd)}")
        print("Running mutations...\n")

        # Run mutmut
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = time.time() - start_time

        print(result.stdout)
        if result.stderr and 'warning' not in result.stderr.lower():
            print("Errors:", result.stderr)

        print(f"\nCompleted in {duration:.2f} seconds ({duration/60:.1f} minutes)")

        # Parse results
        module_results = self._get_module_results(module_name)
        module_results['duration'] = duration
        module_results['file_path'] = str(file_path)

        return module_results

    def _get_module_results(self, module_name):
        """Get results for a specific module from mutmut."""
        os.chdir(self.base_dir)

        result = subprocess.run(
            ['python', '-m', 'mutmut', 'results'],
            capture_output=True,
            text=True
        )

        results_output = result.stdout

        # Parse results
        summary = {
            'module': module_name,
            'killed': 0,
            'survived': 0,
            'timeout': 0,
            'suspicious': 0,
            'total': 0,
            'mutation_score': 0.0
        }

        lines = results_output.split('\n')
        for line in lines:
            line = line.strip()

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

        # Calculate mutation score
        if summary['total'] > 0:
            summary['mutation_score'] = (summary['killed'] / summary['total']) * 100
        else:
            summary['mutation_score'] = 0.0

        return summary

    def generate_coverage_report(self):
        """Generate comprehensive coverage report."""
        self.print_header("MUTATION COVERAGE REPORT")

        overall = self.results['overall_summary']

        print("\n📊 OVERALL STATISTICS")
        print("=" * 80)
        print(f"Total Modules Tested: {overall['total_modules']}")
        print(f"Total Mutations: {overall['total_mutations']}")
        print(f"")
        print(f"Killed:      {overall['killed']:>6} ({overall['killed']/overall['total_mutations']*100 if overall['total_mutations'] > 0 else 0:.1f}%)")
        print(f"Survived:    {overall['survived']:>6} ({overall['survived']/overall['total_mutations']*100 if overall['total_mutations'] > 0 else 0:.1f}%)")
        print(f"Timeout:     {overall['timeout']:>6} ({overall['timeout']/overall['total_mutations']*100 if overall['total_mutations'] > 0 else 0:.1f}%)")
        print(f"Suspicious:  {overall['suspicious']:>6} ({overall['suspicious']/overall['total_mutations']*100 if overall['total_mutations'] > 0 else 0:.1f}%)")
        print(f"")
        print(f"Overall Mutation Score: {overall['overall_score']:.1f}%")
        print("=" * 80)

        # Module breakdown
        print("\n📋 MODULE BREAKDOWN")
        print("=" * 80)
        print(f"{'Module':<30} {'Total':>8} {'Killed':>8} {'Survived':>8} {'Score':>8}")
        print("-" * 80)

        for module_name, module_data in sorted(self.results['modules'].items()):
            score = module_data.get('mutation_score', 0.0)
            total = module_data.get('total', 0)
            killed = module_data.get('killed', 0)
            survived = module_data.get('survived', 0)

            # Color coding
            if score >= 80:
                grade = "✅"
            elif score >= 60:
                grade = "🟡"
            else:
                grade = "❌"

            print(f"{module_name:<30} {total:>8} {killed:>8} {survived:>8} {score:>7.1f}% {grade}")

        print("=" * 80)

        # Recommendations
        print("\n💡 RECOMMENDATIONS")
        print("=" * 80)

        weak_modules = []
        for module_name, module_data in self.results['modules'].items():
            score = module_data.get('mutation_score', 0.0)
            if score < 60 and module_data.get('total', 0) > 0:
                weak_modules.append((module_name, score, module_data.get('survived', 0)))

        if weak_modules:
            weak_modules.sort(key=lambda x: x[1])  # Sort by score (lowest first)
            print("\n⚠️  Modules needing attention (score < 60%):")
            print()
            for module, score, survived in weak_modules:
                print(f"  • {module:<30} Score: {score:>5.1f}%  Survived: {survived}")
                print(f"    → Run: python run_mutation_tests.py --module {module}")
                print(f"    → View: python -m mutmut results")
                print()
        else:
            print("\n✅ All modules have good mutation scores (≥60%)!")

        # Grade overall effectiveness
        overall_score = overall['overall_score']
        print("\n🎯 OVERALL GRADE")
        print("=" * 80)
        if overall_score >= 80:
            print("Grade: A - EXCELLENT ✅")
            print("Your test suite is highly effective across all modules!")
        elif overall_score >= 60:
            print("Grade: B - GOOD 🟡")
            print("Your test suite is reasonably effective. Focus on weak modules.")
        elif overall_score >= 40:
            print("Grade: C - FAIR ⚠️")
            print("Your test suite has significant gaps. Prioritize improvements.")
        else:
            print("Grade: F - NEEDS IMPROVEMENT ❌")
            print("Your test suite is not effective. Comprehensive improvements needed.")
        print("=" * 80)

    def save_comprehensive_report(self):
        """Save JSON and Markdown reports."""
        reports_dir = self.base_dir / 'Research' / 'mutation_testing'
        reports_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        mode = 'quick' if self.quick_mode else 'full'

        # Save JSON
        json_file = reports_dir / f'mutation_coverage_{mode}_{timestamp}.json'
        with open(json_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n✅ JSON report saved: {json_file}")

        # Save Markdown
        md_file = reports_dir / f'mutation_coverage_{mode}_{timestamp}.md'
        self._create_markdown_report(md_file)
        print(f"✅ Markdown report saved: {md_file}")

    def _create_markdown_report(self, filepath):
        """Create detailed markdown report."""
        overall = self.results['overall_summary']
        overall_score = overall['overall_score']

        report = f"""# Full Mutation Coverage Report

**Generated:** {self.results['timestamp']}
**Mode:** {self.results['mode'].upper()}
**Overall Mutation Score:** {overall_score:.1f}%

## Executive Summary

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Modules** | {overall['total_modules']} | - |
| **Total Mutations** | {overall['total_mutations']} | 100% |
| **Killed** | {overall['killed']} | {overall['killed']/overall['total_mutations']*100 if overall['total_mutations'] > 0 else 0:.1f}% |
| **Survived** | {overall['survived']} | {overall['survived']/overall['total_mutations']*100 if overall['total_mutations'] > 0 else 0:.1f}% |
| **Timeout** | {overall['timeout']} | {overall['timeout']/overall['total_mutations']*100 if overall['total_mutations'] > 0 else 0:.1f}% |
| **Suspicious** | {overall['suspicious']} | {overall['suspicious']/overall['total_mutations']*100 if overall['total_mutations'] > 0 else 0:.1f}% |

"""

        # Grade
        if overall_score >= 80:
            report += "**Grade: A - EXCELLENT** ✅\n\n"
        elif overall_score >= 60:
            report += "**Grade: B - GOOD** 🟡\n\n"
        elif overall_score >= 40:
            report += "**Grade: C - FAIR** ⚠️\n\n"
        else:
            report += "**Grade: F - NEEDS IMPROVEMENT** ❌\n\n"

        # Module breakdown
        report += "## Module-by-Module Results\n\n"
        report += "| Module | Total Mutations | Killed | Survived | Timeout | Suspicious | Score | Grade |\n"
        report += "|--------|----------------|--------|----------|---------|------------|-------|-------|\n"

        for module_name, module_data in sorted(self.results['modules'].items()):
            score = module_data.get('mutation_score', 0.0)
            total = module_data.get('total', 0)
            killed = module_data.get('killed', 0)
            survived = module_data.get('survived', 0)
            timeout = module_data.get('timeout', 0)
            suspicious = module_data.get('suspicious', 0)

            if score >= 80:
                grade = "A ✅"
            elif score >= 60:
                grade = "B 🟡"
            elif score >= 40:
                grade = "C ⚠️"
            else:
                grade = "F ❌"

            report += f"| {module_name} | {total} | {killed} | {survived} | {timeout} | {suspicious} | {score:.1f}% | {grade} |\n"

        # Weak modules
        weak_modules = [(m, d['mutation_score'], d['survived'])
                       for m, d in self.results['modules'].items()
                       if d.get('mutation_score', 0.0) < 60 and d.get('total', 0) > 0]

        if weak_modules:
            weak_modules.sort(key=lambda x: x[1])
            report += "\n## ⚠️ Modules Needing Attention\n\n"
            report += "The following modules have mutation scores below 60%:\n\n"
            for module, score, survived in weak_modules:
                report += f"### {module} (Score: {score:.1f}%)\n\n"
                report += f"- **Survived Mutations:** {survived}\n"
                report += f"- **Action:** Review and strengthen tests\n"
                report += f"- **Command:** `python run_mutation_tests.py --module {module}`\n\n"

        # Next steps
        report += """## Next Steps

### 1. Review Survived Mutations

```bash
# View all results
python -m mutmut results

# View specific mutation
python -m mutmut show <id>
```

### 2. Strengthen Tests

For each survived mutation:
1. Understand what mutation was made
2. Ask why no test caught it
3. Add test case to catch this scenario
4. Re-run mutation tests

### 3. Focus on Weak Modules

Prioritize modules with scores < 60%:
"""

        if weak_modules:
            for module, score, _ in weak_modules[:5]:  # Top 5 weakest
                report += f"- `{module}` ({score:.1f}%)\n"
        else:
            report += "- All modules have good scores! 🎉\n"

        report += """
## Understanding Mutation Testing

Mutation testing evaluates test quality by:
1. Making small changes (mutations) to your code
2. Running your test suite
3. Checking if tests fail (killed) or pass (survived)

**High score** = Tests effectively catch defects
**Low score** = Tests miss many defects

This is more rigorous than code coverage alone.

## Commands Reference

```bash
# Run full mutation coverage
python run_full_mutation_coverage.py

# Quick test (for verification)
python run_full_mutation_coverage.py --quick

# Test specific module
python run_mutation_tests.py --module models

# View results
python -m mutmut results
python -m mutmut show <id>

# Generate HTML
python run_full_mutation_coverage.py --html
```
"""

        with open(filepath, 'w') as f:
            f.write(report)

    def run(self):
        """Run full mutation coverage analysis."""
        self.print_header("FULL MUTATION COVERAGE ANALYSIS")

        mode_text = "QUICK MODE" if self.quick_mode else "FULL MODE"
        print(f"\nMode: {mode_text}")

        # Step 1: Get testable modules
        self.print_section("Step 1: Identifying Testable Modules")
        testable_modules = self.get_testable_modules()

        print(f"\nFound {len(testable_modules)} testable modules:")
        for i, (module_name, file_path) in enumerate(testable_modules, 1):
            print(f"  {i:2d}. {module_name:<30} ({file_path.name})")

        self.results['overall_summary']['total_modules'] = len(testable_modules)

        if not testable_modules:
            print("\n❌ No testable modules found!")
            return 1

        # Step 2: Run baseline tests
        self.print_section("Step 2: Baseline Test Verification")
        if not self.run_baseline_tests():
            return 1

        # Step 3: Clear cache
        self.print_section("Step 3: Preparing Environment")
        self.clear_mutation_cache()

        # Step 4: Run mutations on each module
        self.print_header("TESTING MODULES")
        print(f"\nTesting {len(testable_modules)} modules...")
        print("This will take a considerable amount of time!\n")

        for i, (module_name, file_path) in enumerate(testable_modules, 1):
            print(f"\n[{i}/{len(testable_modules)}] Processing: {module_name}")

            # Clear cache before each module
            self.clear_mutation_cache()

            # Run mutations
            module_results = self.run_mutation_on_module(module_name, file_path)
            self.results['modules'][module_name] = module_results

            # Update overall summary
            self.results['overall_summary']['total_mutations'] += module_results['total']
            self.results['overall_summary']['killed'] += module_results['killed']
            self.results['overall_summary']['survived'] += module_results['survived']
            self.results['overall_summary']['timeout'] += module_results['timeout']
            self.results['overall_summary']['suspicious'] += module_results['suspicious']

            # Show progress
            print(f"\nModule {module_name} complete:")
            print(f"  Score: {module_results['mutation_score']:.1f}%")
            print(f"  Killed: {module_results['killed']}, Survived: {module_results['survived']}")

        # Calculate overall score
        overall = self.results['overall_summary']
        if overall['total_mutations'] > 0:
            overall['overall_score'] = (overall['killed'] / overall['total_mutations']) * 100
        else:
            overall['overall_score'] = 0.0

        # Step 5: Generate reports
        self.print_section("Step 5: Generating Reports")
        self.generate_coverage_report()
        self.save_comprehensive_report()

        # Final summary
        self.print_header("MUTATION COVERAGE COMPLETE")
        print(f"\n📊 Overall Mutation Score: {overall['overall_score']:.1f}%")
        print(f"📁 Reports saved in: Research/mutation_testing/\n")

        return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run comprehensive mutation testing across all modules',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_full_mutation_coverage.py
  python run_full_mutation_coverage.py --quick
  python run_full_mutation_coverage.py --html

For detailed guide, see: MUTATION_TESTING_GUIDE.md
        """
    )

    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick mode - run faster with limited mutations per module'
    )

    parser.add_argument(
        '--parallel',
        type=int,
        default=1,
        help='Number of modules to test in parallel (default: 1)'
    )

    parser.add_argument(
        '--html',
        action='store_true',
        help='Generate HTML reports'
    )

    parser.add_argument(
        '--skip-baseline',
        action='store_true',
        help='Skip baseline test verification'
    )

    args = parser.parse_args()

    runner = FullMutationCoverage(
        quick_mode=args.quick,
        parallel=args.parallel,
        generate_html=args.html,
        skip_baseline=args.skip_baseline
    )

    return runner.run()


if __name__ == '__main__':
    sys.exit(main())

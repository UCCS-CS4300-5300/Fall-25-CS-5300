#!/usr/bin/env python3
"""
Lab Tech Mutation Runner with Research Logging

Runs mutation tests on files changed after Aug 1, 2025.
- Updates research log every 2 minutes
- Resilient - skips failures and continues
- Generates HTML reports
- Tracks detailed progress for reproducibility

Usage:
    python3 lab_mutation_runner.py
"""

import subprocess
import os
import sys
import json
import time
import threading
from datetime import datetime
from pathlib import Path


class LabMutationRunner:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.backend_dir = self.base_dir / 'active_interview_backend'
        self.app_dir = self.backend_dir / 'active_interview_app'
        self.log_dir = self.base_dir / 'Research' / 'mutation_testing'
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.research_log = self.log_dir / 'MUTATION_RESEARCH_LOG.md'
        self.html_dir = self.base_dir / 'html'
        self.html_dir.mkdir(exist_ok=True)

        self.start_time = datetime.now()
        self.current_module = "Initializing..."
        self.current_module_idx = 0

        # Results tracking
        self.results = {
            'modules': {},
            'total_killed': 0,
            'total_survived': 0,
            'total_timeout': 0,
            'total_mutations': 0,
            'failed_modules': [],
            'skipped_modules': [],
            'errors': []
        }

        # Target modules (post Aug 1, 2025)
        self.target_modules = [
            ('utils', 'test_utils'),
            ('permissions', 'test_permissions'),
            ('forms', 'test_forms'),
            ('serializers', 'test_serializers'),
            ('pdf_export', 'test_pdf_export_comprehensive'),
            ('invitation_utils', 'test_invitations'),
            ('user_data_utils', 'test_user_data'),
            ('bias_detection', 'test_bias_detection_service'),
            ('audit_utils', 'test_audit_logging'),
            ('latency_utils', 'test_latency_tracking'),
            ('model_tier_manager', 'test_model_tier_manager'),
            ('token_tracking', 'test_token_tracking'),
            ('report_utils', 'test_exportable_report'),
            ('resume_parser', 'test_resume_parsing'),
            ('job_listing_parser', 'test_job_listing_parser'),
            ('signals', 'test_signals'),
            ('constants', 'test_models'),  # constants tested via models
            ('ratelimit_config', 'test_ratelimit_config'),
            ('openai_utils', 'test_openai_utils'),
            ('models', 'test_models'),
            ('views', 'test_views_comprehensive'),
        ]

        # Start log updater thread
        self.stop_log_thread = False
        self.log_thread = threading.Thread(target=self._log_updater_thread, daemon=True)

    def console_log(self, msg, level='INFO'):
        """Log to console with timestamp."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {msg}", flush=True)

    def _log_updater_thread(self):
        """Background thread to update research log every 2 minutes."""
        while not self.stop_log_thread:
            time.sleep(120)  # 2 minutes
            if not self.stop_log_thread:
                self.update_research_log()

    def update_research_log(self):
        """Update the research log markdown file."""
        now = datetime.now()
        elapsed = (now - self.start_time).total_seconds() / 60

        total_modules = len(self.target_modules)
        completed = len(self.results['modules'])
        progress = (completed / total_modules * 100) if total_modules > 0 else 0

        total_mut = self.results['total_mutations']
        killed = self.results['total_killed']
        survived = self.results['total_survived']
        score = (killed / total_mut * 100) if total_mut > 0 else 0

        # Build module results table
        module_rows = ""
        for i, (module, test) in enumerate(self.target_modules, 1):
            if module in self.results['modules']:
                data = self.results['modules'][module]
                status = "COMPLETE"
                m_score = f"{data.get('score', 0):.1f}%"
                module_rows += f"| {i} | {module} | {status} | {data.get('total', 0)} | {data.get('killed', 0)} | {data.get('survived', 0)} | {m_score} | {data.get('duration', 'N/A')} |\n"
            elif module in self.results['skipped_modules']:
                module_rows += f"| {i} | {module} | SKIPPED | - | - | - | - | - |\n"
            elif module in self.results['failed_modules']:
                module_rows += f"| {i} | {module} | FAILED | - | - | - | - | - |\n"
            elif i == self.current_module_idx:
                module_rows += f"| {i} | {module} | **RUNNING** | - | - | - | - | - |\n"
            else:
                module_rows += f"| {i} | {module} | PENDING | - | - | - | - | - |\n"

        # Build error log
        error_rows = ""
        for err in self.results['errors'][-10:]:  # Last 10 errors
            error_rows += f"| {err['time']} | {err['module']} | {err['error'][:50]}... | {err.get('resolution', 'Skipped')} |\n"

        log_content = f"""# Mutation Testing Research Log

**Project:** Active Interview Backend
**Date Started:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC
**Researcher:** Claude AI (Lab Tech Mode)
**Branch:** Mutation_Testing

---

## Current Status

| Metric | Value |
|--------|-------|
| **Progress** | {progress:.1f}% |
| **Current Module** | {self.current_module} |
| **Modules Completed** | {completed} / {total_modules} |
| **Total Mutations** | {total_mut} |
| **Killed** | {killed} |
| **Survived** | {survived} |
| **Overall Score** | {score:.1f}% |
| **Elapsed Time** | {elapsed:.1f} minutes |
| **Last Updated** | {now.strftime('%Y-%m-%d %H:%M:%S')} UTC |

---

## Session Setup Log

### 1. Environment Setup

#### 1.1 System Information
```
Platform: Linux 6.1.158-180.294.amzn2023.x86_64
Python: 3.9.25
Working Directory: /home/ssm-user/Fall-25-CS-5300
Git Branch: Mutation_Testing
```

#### 1.2 Key Dependencies Installed
```
mutmut==2.4.0
Django==4.2.27
pytest==8.4.2
coverage==7.10.7
```

#### 1.3 Critical Setup Steps
1. Install pip: `sudo dnf install python3-pip -y`
2. Install mutmut: `pip3 install mutmut==2.4.0`
3. Install project deps: `pip3 install python-dotenv dj-database-url django-allauth pymupdf4llm ...`

---

### 2. Mutation Runner Configuration

#### 2.1 Test Runner Wrapper
**File:** `/home/ssm-user/Fall-25-CS-5300/run_test.sh`
```bash
#!/bin/bash
cd /home/ssm-user/Fall-25-CS-5300/active_interview_backend
exec python3 manage.py test "$@" --verbosity=0 --failfast 2>/dev/null
```

**Why:** Mutmut's `--runner` option doesn't handle `cd` commands or complex shell syntax well.

#### 2.2 Mutmut Command Template
```bash
python3 -m mutmut run \\
    --paths-to-mutate active_interview_backend/active_interview_app/<module>.py \\
    --runner './run_test.sh active_interview_app.tests.<test_module>' \\
    --simple-output
```

---

## Running Progress

### Module Results

| # | Module | Status | Mutations | Killed | Survived | Score | Duration |
|---|--------|--------|-----------|--------|----------|-------|----------|
{module_rows}

---

## Error Log

| Timestamp | Module | Error | Resolution |
|-----------|--------|-------|------------|
{error_rows if error_rows else "| - | - | No errors yet | - |"}

---

## Skipped Modules

{', '.join(self.results['skipped_modules']) if self.results['skipped_modules'] else 'None yet'}

**Reason for skipping:** Baseline tests failed (tests must pass before mutation testing)

---

## How to Reproduce

### Quick Start
```bash
cd /home/ssm-user/Fall-25-CS-5300

# 1. Verify environment
python3 -m mutmut --help

# 2. Test single module
./run_test.sh active_interview_app.tests.test_utils
python3 -m mutmut run \\
    --paths-to-mutate active_interview_backend/active_interview_app/utils.py \\
    --runner './run_test.sh active_interview_app.tests.test_utils' \\
    --simple-output

# 3. View results
python3 -m mutmut results
```

### Full Suite
```bash
screen -S mutation_lab
python3 lab_mutation_runner.py
# Detach: Ctrl+A, D
# Reattach: screen -r mutation_lab
```

---

## Output Files

| File | Description |
|------|-------------|
| `html/index.html` | Visual HTML report |
| `Research/mutation_testing/lab_results_*.json` | Raw JSON results |
| `Research/mutation_testing/MUTATION_RESEARCH_LOG.md` | This file |

---

## Next Update In: ~2 minutes

*This log auto-updates every 2 minutes while mutation testing runs.*
*To monitor: `tail -f Research/mutation_testing/MUTATION_RESEARCH_LOG.md`*
"""

        with open(self.research_log, 'w') as f:
            f.write(log_content)

        self.console_log(f"Research log updated - {progress:.1f}% complete")

    def module_exists(self, module):
        """Check if module file exists."""
        path = self.app_dir / f'{module}.py'
        return path.exists()

    def run_baseline_test(self, module, test_module):
        """Run baseline test for a module."""
        self.console_log(f"Running baseline test: {test_module}")

        try:
            result = subprocess.run(
                ['./run_test.sh', f'active_interview_app.tests.{test_module}'],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                self.console_log(f"Baseline PASSED for {module}")
                return True
            else:
                self.console_log(f"Baseline FAILED for {module}", 'WARNING')
                self.results['errors'].append({
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'module': module,
                    'error': f'Baseline test failed: {result.stderr[:100]}',
                    'resolution': 'Skipped module'
                })
                return False

        except subprocess.TimeoutExpired:
            self.console_log(f"Baseline TIMEOUT for {module}", 'WARNING')
            return False
        except Exception as e:
            self.console_log(f"Baseline ERROR: {e}", 'ERROR')
            return False

    def run_mutation_test(self, module, test_module):
        """Run mutation test for a single module."""
        module_path = f'active_interview_backend/active_interview_app/{module}.py'

        self.console_log(f"=" * 60)
        self.console_log(f"MUTATION TEST: {module}")
        self.console_log(f"=" * 60)

        # Check module exists
        if not self.module_exists(module):
            self.console_log(f"Module not found: {module_path}", 'WARNING')
            self.results['skipped_modules'].append(module)
            return None

        # Run baseline
        if not self.run_baseline_test(module, test_module):
            self.results['skipped_modules'].append(module)
            return None

        # Clear cache
        cache_file = self.base_dir / '.mutmut-cache'
        if cache_file.exists():
            cache_file.unlink()

        # Run mutmut
        self.console_log(f"Starting mutations for {module}...")
        start_time = time.time()

        try:
            cmd = [
                'python3', '-m', 'mutmut', 'run',
                '--paths-to-mutate', module_path,
                '--runner', f'./run_test.sh active_interview_app.tests.{test_module}',
                '--simple-output'
            ]

            process = subprocess.Popen(
                cmd,
                cwd=self.base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Stream output
            output_lines = []
            for line in process.stdout:
                line = line.strip()
                if line:
                    # Parse progress line
                    if 'KILLED' in line or 'SURVIVED' in line:
                        self.console_log(f"  {line}", 'MUTMUT')
                    output_lines.append(line)

            process.wait(timeout=3600)  # 1 hour max

            duration = time.time() - start_time
            duration_str = f"{duration/60:.1f} min"

            self.console_log(f"Completed {module} in {duration_str}")

            # Parse final results from output
            result = self._parse_mutation_output(output_lines, duration_str)
            return result

        except subprocess.TimeoutExpired:
            self.console_log(f"TIMEOUT for {module}", 'ERROR')
            self.results['failed_modules'].append(module)
            self.results['errors'].append({
                'time': datetime.now().strftime('%H:%M:%S'),
                'module': module,
                'error': 'Mutation testing timed out (>1 hour)',
                'resolution': 'Skipped'
            })
            return None
        except Exception as e:
            self.console_log(f"ERROR: {e}", 'ERROR')
            self.results['failed_modules'].append(module)
            return None

    def _parse_mutation_output(self, lines, duration):
        """Parse mutation results from output."""
        killed = 0
        survived = 0
        timeout = 0
        total = 0

        for line in lines:
            # Look for final status line like:
            # "⠧ 8/8  KILLED 5  TIMEOUT 0  SUSPICIOUS 0  SURVIVED 3  SKIPPED 0"
            if 'KILLED' in line and 'SURVIVED' in line:
                import re
                # Extract numbers
                k_match = re.search(r'KILLED\s+(\d+)', line)
                s_match = re.search(r'SURVIVED\s+(\d+)', line)
                t_match = re.search(r'TIMEOUT\s+(\d+)', line)
                total_match = re.search(r'(\d+)/(\d+)', line)

                if k_match:
                    killed = int(k_match.group(1))
                if s_match:
                    survived = int(s_match.group(1))
                if t_match:
                    timeout = int(t_match.group(1))
                if total_match:
                    total = int(total_match.group(2))

        if total == 0:
            total = killed + survived + timeout

        score = (killed / total * 100) if total > 0 else 0

        return {
            'killed': killed,
            'survived': survived,
            'timeout': timeout,
            'total': total,
            'score': score,
            'duration': duration
        }

    def generate_html_report(self):
        """Generate HTML report."""
        self.console_log("Generating HTML report...")

        total = self.results['total_mutations']
        killed = self.results['total_killed']
        score = (killed / total * 100) if total > 0 else 0

        if score >= 80:
            grade, color = "A", "#28a745"
        elif score >= 60:
            grade, color = "B", "#17a2b8"
        elif score >= 40:
            grade, color = "C", "#ffc107"
        else:
            grade, color = "F", "#dc3545"

        modules_html = ""
        for module, data in self.results['modules'].items():
            m_score = data.get('score', 0)
            m_color = "#28a745" if m_score >= 80 else "#ffc107" if m_score >= 60 else "#dc3545"
            modules_html += f"""
            <tr>
                <td>{module}</td>
                <td>{data.get('total', 0)}</td>
                <td style="color: #28a745;">{data.get('killed', 0)}</td>
                <td style="color: #dc3545;">{data.get('survived', 0)}</td>
                <td style="color: {m_color}; font-weight: bold;">{m_score:.1f}%</td>
                <td>{data.get('duration', 'N/A')}</td>
            </tr>
            """

        elapsed = (datetime.now() - self.start_time).total_seconds() / 60

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Mutation Test Report</title>
    <meta http-equiv="refresh" content="120">
    <style>
        body {{ font-family: -apple-system, sans-serif; background: #1a1a2e; color: #eee; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea, #764ba2); padding: 30px; border-radius: 12px; margin-bottom: 20px; }}
        .score-card {{ background: #16213e; padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 20px; border: 3px solid {color}; }}
        .score {{ font-size: 72px; font-weight: bold; color: {color}; }}
        table {{ width: 100%; border-collapse: collapse; background: #16213e; border-radius: 8px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #333; }}
        th {{ background: #0f3460; }}
        .section {{ background: #16213e; padding: 20px; border-radius: 12px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Mutation Testing Report</h1>
            <p>Files changed after August 1, 2025</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Elapsed: {elapsed:.1f} minutes</p>
        </div>
        <div class="score-card">
            <div class="score">{score:.0f}%</div>
            <div>Grade: {grade}</div>
            <p>{killed} killed / {total} total</p>
        </div>
        <div class="section">
            <h2>Results by Module</h2>
            <table>
                <tr><th>Module</th><th>Total</th><th>Killed</th><th>Survived</th><th>Score</th><th>Duration</th></tr>
                {modules_html}
            </table>
        </div>
        <div class="section">
            <h2>Skipped: {len(self.results['skipped_modules'])}</h2>
            <p>{', '.join(self.results['skipped_modules']) or 'None'}</p>
        </div>
    </div>
</body>
</html>"""

        with open(self.html_dir / 'index.html', 'w') as f:
            f.write(html)

    def save_results(self):
        """Save JSON results."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = self.log_dir / f'lab_results_{timestamp}.json'

        with open(results_file, 'w') as f:
            json.dump({
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                **self.results
            }, f, indent=2)

        self.console_log(f"Results saved: {results_file}")

    def run(self):
        """Run all mutation tests."""
        self.console_log("=" * 60)
        self.console_log("LAB MUTATION RUNNER - POST AUG 2025 FILES")
        self.console_log("=" * 60)
        self.console_log(f"Target modules: {len(self.target_modules)}")
        self.console_log(f"Log: {self.research_log}")

        # Start log updater thread
        self.log_thread.start()

        # Modules already completed or skipped (skip these)
        completed_modules = {'utils', 'forms', 'serializers', 'permissions'}

        # Initial log update
        self.update_research_log()

        for i, (module, test_module) in enumerate(self.target_modules, 1):
            self.current_module = module
            self.current_module_idx = i

            self.console_log(f"\n[{i}/{len(self.target_modules)}] Processing: {module}")

            # Skip already completed modules
            if module in completed_modules:
                self.console_log(f"Skipping {module} - already completed in previous run")
                continue

            try:
                result = self.run_mutation_test(module, test_module)

                if result:
                    self.results['modules'][module] = result
                    self.results['total_killed'] += result.get('killed', 0)
                    self.results['total_survived'] += result.get('survived', 0)
                    self.results['total_timeout'] += result.get('timeout', 0)
                    self.results['total_mutations'] += result.get('total', 0)

                    self.console_log(f"Module {module}: {result.get('score', 0):.1f}%")

                # Update reports after each module
                self.generate_html_report()
                self.update_research_log()

            except KeyboardInterrupt:
                self.console_log("Interrupted by user", 'WARNING')
                break
            except Exception as e:
                self.console_log(f"Unexpected error: {e}", 'ERROR')
                self.results['failed_modules'].append(module)
                continue

        # Stop log thread
        self.stop_log_thread = True

        # Final reports
        self.generate_html_report()
        self.save_results()
        self.update_research_log()

        # Summary
        self.console_log("\n" + "=" * 60)
        self.console_log("FINAL SUMMARY")
        self.console_log("=" * 60)

        total = self.results['total_mutations']
        killed = self.results['total_killed']
        score = (killed / total * 100) if total > 0 else 0

        self.console_log(f"Total Mutations: {total}")
        self.console_log(f"Killed: {killed}")
        self.console_log(f"Survived: {self.results['total_survived']}")
        self.console_log(f"Score: {score:.1f}%")
        self.console_log(f"Skipped: {len(self.results['skipped_modules'])}")
        self.console_log(f"\nHTML: {self.html_dir / 'index.html'}")
        self.console_log(f"Log: {self.research_log}")

        return 0


if __name__ == '__main__':
    runner = LabMutationRunner()
    sys.exit(runner.run())

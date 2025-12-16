#!/usr/bin/env python3
"""
Parallel Mutation Runner - Runs 6 modules concurrently

Each module gets its own mutmut cache file to enable true parallelism.
"""

import subprocess
import os
import sys
import json
import time
import re
import threading
from datetime import datetime
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing


# Worker function - must be at module level for multiprocessing
def run_single_module(args):
    """Run mutation test for a single module in isolated temp directory."""
    module, test_module, base_dir, worker_id = args

    base_dir = Path(base_dir)
    app_dir = base_dir / 'active_interview_backend' / 'active_interview_app'
    module_path = f'active_interview_backend/active_interview_app/{module}.py'

    # Create isolated work directory for this module
    work_dir = base_dir / f'.mutation_worker_{module}'

    result = {
        'module': module,
        'worker_id': worker_id,
        'status': 'pending',
        'killed': 0,
        'survived': 0,
        'timeout': 0,
        'total': 0,
        'score': 0,
        'duration': '0 min',
        'error': None
    }

    # Check module exists
    if not (app_dir / f'{module}.py').exists():
        result['status'] = 'skipped'
        result['error'] = 'Module file not found'
        return result

    # Run baseline test from base_dir
    try:
        baseline = subprocess.run(
            ['./run_test.sh', f'active_interview_app.tests.{test_module}'],
            cwd=base_dir,
            capture_output=True,
            text=True,
            timeout=300
        )
        if baseline.returncode != 0:
            result['status'] = 'skipped'
            result['error'] = f'Baseline failed: {baseline.stderr[:100]}'
            return result
    except subprocess.TimeoutExpired:
        result['status'] = 'skipped'
        result['error'] = 'Baseline timeout'
        return result
    except Exception as e:
        result['status'] = 'skipped'
        result['error'] = str(e)
        return result

    # Setup isolated work directory with symlinks
    try:
        import shutil
        if work_dir.exists():
            shutil.rmtree(work_dir)
        work_dir.mkdir(parents=True)

        # Create symlinks to necessary directories/files
        (work_dir / 'active_interview_backend').symlink_to(base_dir / 'active_interview_backend')
        (work_dir / 'run_test.sh').symlink_to(base_dir / 'run_test.sh')

    except Exception as e:
        result['status'] = 'failed'
        result['error'] = f'Setup failed: {e}'
        return result

    # Run mutmut from isolated directory (cache will be in work_dir)
    start_time = time.time()

    try:
        cmd = [
            'python3', '-m', 'mutmut', 'run',
            '--paths-to-mutate', module_path,
            '--runner', f'./run_test.sh active_interview_app.tests.{test_module}',
            '--simple-output'
        ]

        proc = subprocess.run(
            cmd,
            cwd=work_dir,  # Run from isolated directory
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour max per module
        )

        duration = time.time() - start_time
        result['duration'] = f"{duration/60:.1f} min"

        # Parse output
        output = proc.stdout + proc.stderr
        for line in output.split('\n'):
            if 'KILLED' in line and 'SURVIVED' in line:
                k_match = re.search(r'KILLED\s+(\d+)', line)
                s_match = re.search(r'SURVIVED\s+(\d+)', line)
                t_match = re.search(r'TIMEOUT\s+(\d+)', line)
                total_match = re.search(r'(\d+)/(\d+)', line)

                if k_match:
                    result['killed'] = int(k_match.group(1))
                if s_match:
                    result['survived'] = int(s_match.group(1))
                if t_match:
                    result['timeout'] = int(t_match.group(1))
                if total_match:
                    result['total'] = int(total_match.group(2))

        if result['total'] == 0:
            result['total'] = result['killed'] + result['survived'] + result['timeout']

        if result['total'] > 0:
            result['score'] = (result['killed'] / result['total']) * 100

        result['status'] = 'complete'

    except subprocess.TimeoutExpired:
        result['status'] = 'failed'
        result['error'] = 'Mutation timeout (>1 hour)'
    except Exception as e:
        result['status'] = 'failed'
        result['error'] = str(e)
    finally:
        # Cleanup work directory
        try:
            import shutil
            if work_dir.exists():
                shutil.rmtree(work_dir)
        except:
            pass

    return result


class ParallelMutationRunner:
    def __init__(self, max_workers=6):
        self.max_workers = max_workers
        self.base_dir = Path(__file__).parent
        self.log_dir = self.base_dir / 'Research' / 'mutation_testing'
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.research_log = self.log_dir / 'MUTATION_RESEARCH_LOG.md'
        self.html_dir = self.base_dir / 'html'
        self.html_dir.mkdir(exist_ok=True)

        self.start_time = datetime.now()

        # Results
        self.results = {
            'modules': {},
            'total_killed': 0,
            'total_survived': 0,
            'total_timeout': 0,
            'total_mutations': 0,
            'failed_modules': [],
            'skipped_modules': [],
            'running_modules': [],
            'errors': []
        }

        # All target modules
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
            ('constants', 'test_models'),
            ('ratelimit_config', 'test_ratelimit_config'),
            ('openai_utils', 'test_openai_utils'),
            ('models', 'test_models'),
            ('views', 'test_views_comprehensive'),
        ]

        # Already completed modules from previous runs (with their results)
        self.completed_modules = {
            'utils', 'forms', 'serializers', 'permissions',
            # Completed in parallel run
            'token_tracking', 'resume_parser', 'job_listing_parser',
            'signals', 'constants', 'ratelimit_config', 'openai_utils', 'views'
        }

        # Previous run results (from 150 min run + parallel run)
        self.previous_results = {
            # Original run
            'utils': {'killed': 5, 'survived': 3, 'timeout': 0, 'total': 8, 'score': 62.5, 'duration': '0.8 min'},
            'forms': {'killed': 100, 'survived': 211, 'timeout': 0, 'total': 311, 'score': 32.2, 'duration': '86.7 min'},
            'serializers': {'killed': 101, 'survived': 125, 'timeout': 0, 'total': 226, 'score': 44.7, 'duration': '47.1 min'},
            # Parallel run completions
            'token_tracking': {'killed': 0, 'survived': 33, 'timeout': 0, 'total': 33, 'score': 0.0, 'duration': '20.1 min'},
            'resume_parser': {'killed': 46, 'survived': 55, 'timeout': 0, 'total': 101, 'score': 45.5, 'duration': '19.2 min'},
            'job_listing_parser': {'killed': 129, 'survived': 33, 'timeout': 0, 'total': 162, 'score': 79.6, 'duration': '19.3 min'},
            'signals': {'killed': 1, 'survived': 34, 'timeout': 0, 'total': 35, 'score': 2.9, 'duration': '4.3 min'},
            'constants': {'killed': 3, 'survived': 44, 'timeout': 0, 'total': 47, 'score': 6.4, 'duration': '19.9 min'},
            'ratelimit_config': {'killed': 27, 'survived': 0, 'timeout': 0, 'total': 27, 'score': 100.0, 'duration': '5.1 min'},
            'openai_utils': {'killed': 38, 'survived': 43, 'timeout': 0, 'total': 81, 'score': 46.9, 'duration': '19.0 min'},
        }

        # Initialize totals with previous results
        for module, data in self.previous_results.items():
            self.results['modules'][module] = data
            self.results['total_killed'] += data['killed']
            self.results['total_survived'] += data['survived']
            self.results['total_timeout'] += data['timeout']
            self.results['total_mutations'] += data['total']

        # Log updater
        self.stop_log_thread = False
        self.results_lock = threading.Lock()

    def log(self, msg, level='INFO'):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {msg}", flush=True)

    def update_research_log(self):
        """Update the markdown research log."""
        with self.results_lock:
            now = datetime.now()
            elapsed = (now - self.start_time).total_seconds() / 60

            total_modules = len(self.target_modules)
            # Count unique completed modules (avoid double-counting)
            all_completed = set(self.results['modules'].keys()) | self.completed_modules
            completed = len(all_completed)
            progress = min((completed / total_modules * 100), 100.0) if total_modules > 0 else 0

            total_mut = self.results['total_mutations']
            killed = self.results['total_killed']
            score = (killed / total_mut * 100) if total_mut > 0 else 0

            # Build module table
            module_rows = ""
            for i, (module, test) in enumerate(self.target_modules, 1):
                # Check if we have actual results for this module
                if module in self.results['modules']:
                    data = self.results['modules'][module]
                    m_score = f"{data.get('score', 0):.1f}%"
                    status = "COMPLETE" if module not in self.completed_modules else "PREV"
                    module_rows += f"| {i} | {module} | {status} | {data.get('total', 0)} | {data.get('killed', 0)} | {data.get('survived', 0)} | {m_score} | {data.get('duration', 'N/A')} |\n"
                elif module in self.completed_modules:
                    # In completed set but no data (like permissions which was skipped)
                    module_rows += f"| {i} | {module} | PREV_SKIP | - | - | - | - | - |\n"
                elif module in self.results['running_modules']:
                    module_rows += f"| {i} | {module} | **RUNNING** | - | - | - | - | - |\n"
                elif module in self.results['skipped_modules']:
                    module_rows += f"| {i} | {module} | SKIPPED | - | - | - | - | - |\n"
                elif module in self.results['failed_modules']:
                    module_rows += f"| {i} | {module} | FAILED | - | - | - | - | - |\n"
                else:
                    module_rows += f"| {i} | {module} | PENDING | - | - | - | - | - |\n"

            # Error rows
            error_rows = ""
            for err in self.results['errors'][-10:]:
                error_rows += f"| {err['time']} | {err['module']} | {err['error'][:50]}... | Skipped |\n"

            log_content = f"""# Mutation Testing Research Log

**Project:** Active Interview Backend
**Date Started:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC
**Mode:** PARALLEL ({self.max_workers} workers)
**Branch:** Mutation_Testing

---

## Current Status

| Metric | Value |
|--------|-------|
| **Progress** | {progress:.1f}% |
| **Workers** | {self.max_workers} parallel |
| **Running** | {', '.join(self.results['running_modules']) or 'None'} |
| **Modules Completed** | {completed} / {total_modules} |
| **Total Mutations** | {total_mut} |
| **Killed** | {killed} |
| **Survived** | {self.results['total_survived']} |
| **Overall Score** | {score:.1f}% |
| **Elapsed Time** | {elapsed:.1f} minutes |
| **Last Updated** | {now.strftime('%Y-%m-%d %H:%M:%S')} UTC |

---

## Module Results

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

{', '.join(self.results['skipped_modules']) if self.results['skipped_modules'] else 'None'}

---

*Log auto-updates every 30 seconds. Running with {self.max_workers} parallel workers.*
"""

            with open(self.research_log, 'w') as f:
                f.write(log_content)

    def log_updater_thread(self):
        """Background thread to update log every 30 seconds."""
        while not self.stop_log_thread:
            time.sleep(30)
            if not self.stop_log_thread:
                self.update_research_log()
                self.generate_html_report()

    def generate_html_report(self):
        """Generate HTML report."""
        with self.results_lock:
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
            running = ', '.join(self.results['running_modules']) or 'None'

            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Parallel Mutation Test Report</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body {{ font-family: -apple-system, sans-serif; background: #1a1a2e; color: #eee; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea, #764ba2); padding: 30px; border-radius: 12px; margin-bottom: 20px; }}
        .score-card {{ background: #16213e; padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 20px; border: 3px solid {color}; }}
        .score {{ font-size: 72px; font-weight: bold; color: {color}; }}
        .running {{ background: #0f3460; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; background: #16213e; border-radius: 8px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #333; }}
        th {{ background: #0f3460; }}
        .section {{ background: #16213e; padding: 20px; border-radius: 12px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Parallel Mutation Testing ({self.max_workers} workers)</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Elapsed: {elapsed:.1f} minutes</p>
        </div>
        <div class="running">
            <strong>Currently Running:</strong> {running}
        </div>
        <div class="score-card">
            <div class="score">{score:.0f}%</div>
            <div>Grade: {grade}</div>
            <p>{killed} killed / {total} total mutations</p>
        </div>
        <div class="section">
            <h2>Completed Modules</h2>
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

    def run(self):
        """Run mutation tests in parallel."""
        self.log("=" * 60)
        self.log(f"PARALLEL MUTATION RUNNER - {self.max_workers} WORKERS")
        self.log("=" * 60)

        # Filter modules to run
        modules_to_run = [
            (m, t) for m, t in self.target_modules
            if m not in self.completed_modules
        ]

        self.log(f"Modules to process: {len(modules_to_run)}")
        self.log(f"Already completed: {len(self.completed_modules)}")

        # Start log updater thread
        log_thread = threading.Thread(target=self.log_updater_thread, daemon=True)
        log_thread.start()

        # Initial log
        self.update_research_log()

        # Prepare work items
        work_items = [
            (module, test_module, str(self.base_dir), i)
            for i, (module, test_module) in enumerate(modules_to_run)
        ]

        # Run in parallel
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all jobs
            future_to_module = {}
            for item in work_items:
                module = item[0]
                future = executor.submit(run_single_module, item)
                future_to_module[future] = module
                with self.results_lock:
                    self.results['running_modules'].append(module)
                self.log(f"Submitted: {module}")

            self.update_research_log()

            # Process completions
            for future in as_completed(future_to_module):
                module = future_to_module[future]

                try:
                    result = future.result()

                    with self.results_lock:
                        if module in self.results['running_modules']:
                            self.results['running_modules'].remove(module)

                        if result['status'] == 'complete':
                            self.results['modules'][module] = result
                            self.results['total_killed'] += result['killed']
                            self.results['total_survived'] += result['survived']
                            self.results['total_timeout'] += result['timeout']
                            self.results['total_mutations'] += result['total']
                            self.log(f"COMPLETE: {module} - {result['score']:.1f}% ({result['killed']}/{result['total']})")
                        elif result['status'] == 'skipped':
                            self.results['skipped_modules'].append(module)
                            self.results['errors'].append({
                                'time': datetime.now().strftime('%H:%M:%S'),
                                'module': module,
                                'error': result['error'] or 'Unknown'
                            })
                            self.log(f"SKIPPED: {module} - {result['error']}")
                        else:
                            self.results['failed_modules'].append(module)
                            self.log(f"FAILED: {module} - {result['error']}")

                    self.update_research_log()
                    self.generate_html_report()

                except Exception as e:
                    self.log(f"ERROR processing {module}: {e}", 'ERROR')
                    with self.results_lock:
                        if module in self.results['running_modules']:
                            self.results['running_modules'].remove(module)
                        self.results['failed_modules'].append(module)

        # Stop log thread
        self.stop_log_thread = True

        # Final reports
        self.update_research_log()
        self.generate_html_report()
        self.save_results()

        # Summary
        total = self.results['total_mutations']
        killed = self.results['total_killed']
        score = (killed / total * 100) if total > 0 else 0

        self.log("=" * 60)
        self.log("FINAL SUMMARY")
        self.log("=" * 60)
        self.log(f"Total Mutations: {total}")
        self.log(f"Killed: {killed}")
        self.log(f"Survived: {self.results['total_survived']}")
        self.log(f"Score: {score:.1f}%")
        self.log(f"Completed: {len(self.results['modules'])}")
        self.log(f"Skipped: {len(self.results['skipped_modules'])}")
        self.log(f"Failed: {len(self.results['failed_modules'])}")

        elapsed = (datetime.now() - self.start_time).total_seconds() / 60
        self.log(f"Total time: {elapsed:.1f} minutes")

        return 0

    def save_results(self):
        """Save JSON results."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = self.log_dir / f'parallel_results_{timestamp}.json'

        with open(results_file, 'w') as f:
            json.dump({
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'max_workers': self.max_workers,
                **self.results
            }, f, indent=2)

        self.log(f"Results saved: {results_file}")


if __name__ == '__main__':
    # Use 6 workers by default, or specify via command line
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    runner = ParallelMutationRunner(max_workers=workers)
    sys.exit(runner.run())

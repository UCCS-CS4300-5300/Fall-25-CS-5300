#!/usr/bin/env python3
"""
Automated script to fix remaining lint errors in test files.
Run this from the project root directory.
"""

import os
import re

BASE_DIR = r"C:\Users\jacks\CS4300 Project\Fall-25-CS-5300\active_interview_backend\active_interview_app\tests"

def remove_unused_imports(filepath, imports_to_remove):
    """Remove unused imports from a file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    for import_line in imports_to_remove:
        # Try to remove the exact line
        content = re.sub(rf'^{re.escape(import_line)}$\n', '', content, flags=re.MULTILINE)
        # Try to remove from multi-line import
        content = re.sub(rf',\s*{re.escape(import_line.strip())}', '', content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def remove_unused_variables(filepath, line_numbers):
    """Remove unused variable assignments"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line_no in sorted(line_numbers, reverse=True):
        if 0 < line_no <= len(lines):
            # Comment out the line instead of removing to preserve line numbers
            lines[line_no - 1] = '# ' + lines[line_no - 1]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def fix_indentation(filepath, fixes):
    """Fix indentation errors"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line_no, correct_indent in fixes:
        if 0 < line_no <= len(lines):
            line = lines[line_no - 1]
            # Remove existing indentation and add correct amount
            stripped = line.lstrip()
            lines[line_no - 1] = ' ' * correct_indent + stripped

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)

print("Fixing remaining lint errors in test files...\n")

# Fix test_audit_logging.py
print("Fixing test_audit_logging.py...")
filepath = os.path.join(BASE_DIR, "test_audit_logging.py")
if os.path.exists(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove unused signal imports from line 17
    content = re.sub(
        r'from django\.contrib\.auth\.signals import user_logged_in, user_logged_out, user_login_failed\n',
        '# Signal imports moved to test functions where needed\n',
        content
    )

    # Remove threading import
    content = re.sub(r'import threading\n', '', content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("  ✓ Fixed")
else:
    print("  ✗ File not found")

# Fix test_bias_detection_service.py
print("Fixing test_bias_detection_service.py...")
filepath = os.path.join(BASE_DIR, "test_bias_detection_service.py")
if os.path.exists(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    content = re.sub(r'from django\.contrib\.contenttypes\.models import ContentType\n', '', content)
    content = re.sub(r'from active_interview_app\.models import BiasAnalysisResult\n', '', content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("  ✓ Fixed")
else:
    print("  ✗ File not found")

# Fix test_critical_coverage_gaps.py
print("Fixing test_critical_coverage_gaps.py...")
filepath = os.path.join(BASE_DIR, "test_critical_coverage_gaps.py")
if os.path.exists(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    content = re.sub(r'from unittest\.mock import patch, MagicMock\n', 'from unittest.mock import Mock\n', content)
    content = re.sub(r'from \.test_utils import create_mock_openai_response\n', '', content)

    # Remove extra blank lines around line 247
    content = re.sub(r'\n\n\n\n', '\n\n', content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("  ✓ Fixed")
else:
    print("  ✗ File not found")

# Fix test_interview_workflow_phases.py
print("Fixing test_interview_workflow_phases.py...")
filepath = os.path.join(BASE_DIR, "test_interview_workflow_phases.py")
if os.path.exists(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    content = re.sub(r'from active_interview_app\.models import UserProfile\n', '', content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("  ✓ Fixed")
else:
    print("  ✗ File not found")

# Fix test_model_tier_manager.py
print("Fixing test_model_tier_manager.py...")
filepath = os.path.join(BASE_DIR, "test_model_tier_manager.py")
if os.path.exists(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    content = re.sub(r'from unittest\.mock import MagicMock\n', '', content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("  ✓ Fixed")
else:
    print("  ✗ File not found")

# Fix test_multi_tier_rotation.py
print("Fixing test_multi_tier_rotation.py...")
filepath = os.path.join(BASE_DIR, "test_multi_tier_rotation.py")
if os.path.exists(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    content = re.sub(r'from datetime import timedelta\n', '', content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("  ✓ Fixed")
else:
    print("  ✗ File not found")

# Fix test_ratelimit_monitoring.py
print("Fixing test_ratelimit_monitoring.py...")
filepath = os.path.join(BASE_DIR, "test_ratelimit_monitoring.py")
if os.path.exists(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    content = re.sub(r'^import json\n', '', content, flags=re.MULTILINE)
    content = re.sub(r'from unittest\.mock import Mock\n', '', content)
    content = re.sub(r'import django\.core\.mail\n', '', content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("  ✓ Fixed")
else:
    print("  ✗ File not found")

# Fix test_spending_tracker.py
print("Fixing test_spending_tracker.py...")
filepath = os.path.join(BASE_DIR, "test_spending_tracker.py")
if os.path.exists(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    content = re.sub(r'from datetime import datetime, timedelta\n', 'from datetime import date\n', content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("  ✓ Fixed")
else:
    print("  ✗ File not found")

# Fix test_views_extended.py
print("Fixing test_views_extended.py...")
filepath = os.path.join(BASE_DIR, "test_views_extended.py")
if os.path.exists(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    content = re.sub(r'from unittest import skip\n', '', content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("  ✓ Fixed")
else:
    print("  ✗ File not found")

print("\n✓ Done! Run flake8 to verify the fixes:")
print("  cd active_interview_backend")
print("  flake8 --config ../.flake8 .")

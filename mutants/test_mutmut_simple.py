#!/usr/bin/env python3
"""
Simple test to verify mutmut is working correctly.
This will run mutation testing on just the forms.py file to verify the setup.
"""
import subprocess
import sys

print("=" * 70)
print("SIMPLE MUTMUT TEST")
print("=" * 70)

# Clear any existing cache
print("\n1. Clearing cache...")
subprocess.run(['rm', '-f', '.mutmut-cache'])

# Run mutmut on just forms.py with a limit
print("\n2. Running mutmut on forms.py...")
result = subprocess.run(
    ['python3', '-m', 'mutmut', 'run', '--max-children', '1'],
    capture_output=True,
    text=True,
    timeout=300
)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print("\nReturn code:", result.returncode)

# Check results
print("\n3. Checking results...")
result = subprocess.run(
    ['python3', '-m', 'mutmut', 'results'],
    capture_output=True,
    text=True
)

print(result.stdout)

sys.exit(0)

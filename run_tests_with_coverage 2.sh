#!/bin/bash
# Shell script to run tests with coverage

echo "========================================"
echo "Running Django Tests with Coverage"
echo "========================================"
echo

cd active_interview_backend

echo "Running tests with coverage..."
python3 -m coverage run manage.py test -v 2

if [ $? -ne 0 ]; then
    echo
    echo "========================================"
    echo "Tests FAILED!"
    echo "========================================"
    exit 1
fi

echo
echo "========================================"
echo "Generating Coverage Report"
echo "========================================"
echo

# Generate text report
python3 -m coverage report -m > coverage_report.txt

# Also display to console
python3 -m coverage report -m

echo
echo "Coverage report saved to: coverage_report.txt"
echo

# Generate HTML report
python3 -m coverage html

echo "HTML coverage report generated in: htmlcov/index.html"
echo
echo "========================================"
echo "Tests completed successfully!"
echo "========================================"

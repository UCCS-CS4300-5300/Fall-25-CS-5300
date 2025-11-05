#!/bin/bash
#
# Run Token Tracking Tests with Coverage
# This script runs only the token tracking tests and generates a coverage report
#

set -e

echo ""
echo "============================================================"
echo "Running Token Tracking Tests with Coverage"
echo "============================================================"
echo ""

cd active_interview_backend

echo "Installing dependencies if needed..."
pip install coverage -q

echo ""
echo "Running token tracking tests with coverage..."
echo ""

# Run all token-related tests
coverage run --source=active_interview_app manage.py test \
    active_interview_app.tests.test_token_tracking \
    active_interview_app.tests.test_token_tracking_comprehensive \
    active_interview_app.tests.test_token_tracker_module \
    active_interview_app.tests.test_openai_utils_extended \
    active_interview_app.tests.test_token_scripts

echo ""
echo "============================================================"
echo "Token Tracking Coverage Report"
echo "============================================================"
echo ""

# Show coverage for token tracking modules only
coverage report --include="active_interview_app/token_*.py,active_interview_app/openai_utils.py,active_interview_app/merge_stats_models.py"

echo ""
echo "============================================================"
echo "Detailed Coverage Report"
echo "============================================================"
echo ""

# Generate HTML report
coverage html --include="active_interview_app/token_*.py,active_interview_app/openai_utils.py,active_interview_app/merge_stats_models.py"

echo ""
echo "Token tracking coverage report generated!"
echo "Open 'htmlcov/index.html' to view detailed coverage"
echo ""
echo "Look for these files in the report:"
echo "  - token_usage_models.py (should be ~98%)"
echo "  - merge_stats_models.py (should be ~98%)"
echo "  - token_tracker.py (should be ~95%)"
echo "  - openai_utils.py (should be ~98%)"
echo ""

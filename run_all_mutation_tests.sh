#!/bin/bash
################################################################################
# Mutation Testing - Run All Tests (Linux/Mac/WSL)
################################################################################
# This script runs mutation tests on all Python modules in the application.
#
# WARNING: This will take MANY HOURS to complete (8-24+ hours)
# Each mutation requires running the entire test suite.
#
# Usage:
#   ./run_all_mutation_tests.sh
#
# Or for specific modules:
#   ./run_all_mutation_tests.sh --module models
#   ./run_all_mutation_tests.sh --module forms --limit 20
################################################################################

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "============================================================================"
echo "MUTATION TESTING - FULL TEST SUITE"
echo "============================================================================"
echo ""

# Parse arguments
MODULE=""
LIMIT=""
HTML=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --module)
            MODULE="--module $2"
            shift 2
            ;;
        --limit)
            LIMIT="--limit $2"
            shift 2
            ;;
        --html)
            HTML="--html"
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

if [ -z "$MODULE" ]; then
    echo -e "${YELLOW}WARNING: Testing ALL modules will take 8-24+ hours!${NC}"
    echo ""
    echo "Recommended: Run with --module flag for faster results"
    echo "Example: ./run_all_mutation_tests.sh --module models --limit 20"
    echo ""
    read -p "Continue with full test? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
fi

# Check Python
echo "[Step 1/5] Checking Python installation..."
if ! command -v python &> /dev/null; then
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}ERROR: Python is not installed${NC}"
        exit 1
    fi
    PYTHON="python3"
else
    PYTHON="python"
fi
echo -e "${GREEN}✓ Python is installed${NC}"

# Check mutmut
echo ""
echo "[Step 2/5] Checking mutmut installation..."
if ! $PYTHON -m mutmut --version &> /dev/null; then
    echo -e "${YELLOW}mutmut is not installed. Installing...${NC}"
    $PYTHON -m pip install mutmut
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Failed to install mutmut${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✓ mutmut is installed${NC}"

# Check baseline tests
echo ""
echo "[Step 3/5] Running baseline tests..."
echo "This ensures tests pass before we start mutating code..."
cd active_interview_backend
$PYTHON manage.py test active_interview_app.tests --verbosity=0 > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Baseline tests are failing!${NC}"
    echo "You must fix failing tests before running mutation tests."
    echo ""
    echo "Run this command to see failures:"
    echo "  cd active_interview_backend"
    echo "  $PYTHON manage.py test active_interview_app.tests"
    cd ..
    exit 1
fi
cd ..
echo -e "${GREEN}✓ Baseline tests passed${NC}"

# Create reports directory
echo ""
echo "[Step 4/5] Setting up reports directory..."
mkdir -p "Research/mutation_testing"
echo -e "${GREEN}✓ Reports directory ready${NC}"

# Start mutation testing
echo ""
echo "[Step 5/5] Running mutation tests..."
echo ""
echo "============================================================================"
echo "MUTATION TESTING IN PROGRESS"
echo "============================================================================"
echo ""
echo "Started at: $(date)"
echo ""

if [ -z "$MODULE" ]; then
    echo "Testing: ALL modules"
    echo "Estimated time: 8-24+ hours"
else
    echo "Testing: $MODULE"
    echo "Estimated time: 30-90 minutes per module"
fi

if [ ! -z "$LIMIT" ]; then
    echo "Mutation limit: $LIMIT"
fi

echo ""
echo "You can monitor progress below."
echo "Feel free to run this in a screen/tmux session."
echo ""
echo "============================================================================"
echo ""

# Record start time
START_TIME=$(date +%s)

# Run mutation tests
$PYTHON run_mutation_tests.py $MODULE $LIMIT $HTML

# Record end time
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
HOURS=$((DURATION / 3600))
MINUTES=$(((DURATION % 3600) / 60))

echo ""
echo "============================================================================"
echo "MUTATION TESTING COMPLETE"
echo "============================================================================"
echo ""
echo "Started:  $(date -d @$START_TIME)"
echo "Finished: $(date -d @$END_TIME)"
echo "Duration: ${HOURS}h ${MINUTES}m"
echo ""
echo "Reports saved in: Research/mutation_testing/"
echo ""
echo -e "${GREEN}View your results:${NC}"
echo "  1. cat Research/mutation_testing/mutation_report_*.md"
echo "  2. open html/index.html (if --html was used)"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "  1. Review the mutation score"
echo "  2. Check survived mutations: python -m mutmut results"
echo "  3. View specific mutations: python -m mutmut show 1"
echo "  4. Add tests for survived mutations"
echo ""

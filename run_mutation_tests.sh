#!/bin/bash
################################################################################
# Unified Mutation Testing Script (Linux/Mac/WSL)
################################################################################
# This script provides a menu-driven interface for mutation testing.
################################################################################

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;96m'
NC='\033[0m' # No Color

# Detect Python command
if command -v python3 &> /dev/null; then
    PYTHON="python3"
elif command -v python &> /dev/null; then
    PYTHON="python"
else
    echo -e "${RED}ERROR: Python is not installed${NC}"
    exit 1
fi

main_menu() {
    clear
    echo ""
    echo "============================================================================"
    echo "MUTATION TESTING - UNIFIED RUNNER"
    echo "============================================================================"
    echo ""
    echo "Select your testing approach:"
    echo ""
    echo -e "  ${CYAN}1.${NC} Quick Test (Single module with limit) ${GREEN}[RECOMMENDED]${NC}"
    echo "     Perfect for rapid feedback - 20-40 minutes"
    echo ""
    echo -e "  ${CYAN}2.${NC} Full Module Test (Complete module analysis)"
    echo "     Comprehensive testing - 30-90 minutes per module"
    echo ""
    echo -e "  ${CYAN}3.${NC} Full Application Test ${YELLOW}[WARNING: 8-24+ hours]${NC}"
    echo "     Test ALL Python files - Very time intensive"
    echo ""
    echo -e "  ${CYAN}4.${NC} Custom Configuration (Advanced)"
    echo "     Specify your own parameters"
    echo ""
    echo -e "  ${CYAN}5.${NC} View Previous Results"
    echo "     Browse existing mutation test reports"
    echo ""
    echo -e "  ${CYAN}6.${NC} Help / Documentation"
    echo "     Learn about mutation testing"
    echo ""
    echo -e "  ${CYAN}0.${NC} Exit"
    echo ""
    echo "============================================================================"
    echo ""

    read -p "Enter your choice (0-6): " MAIN_CHOICE

    case $MAIN_CHOICE in
        1) quick_test ;;
        2) full_module_test ;;
        3) full_app_test ;;
        4) custom_config ;;
        5) view_results ;;
        6) show_help ;;
        0) exit 0 ;;
        *)
            echo -e "${RED}Invalid choice!${NC}"
            read -p "Press Enter to continue..."
            main_menu
            ;;
    esac
}

quick_test() {
    clear
    echo ""
    echo "============================================================================"
    echo "QUICK MUTATION TEST"
    echo "============================================================================"
    echo ""
    echo "This runs a limited mutation test on one module (20-40 minutes)"
    echo "Perfect for getting quick feedback on test effectiveness."
    echo ""
    echo "Available modules:"
    echo -e "  1. pdf_export      (Simplest - ~10-20 mutations) ${GREEN}[BEST FOR FIRST TIME]${NC}"
    echo "  2. permissions     (Small - ~10-20 mutations)"
    echo "  3. serializers     (Small - ~15-25 mutations)"
    echo "  4. invitation_utils(Small - ~20-30 mutations)"
    echo "  5. forms           (Medium - ~30-50 mutations)"
    echo "  6. user_data_utils (Medium - ~30-50 mutations)"
    echo "  7. models          (Large - ~50-100 mutations)"
    echo "  8. views           (Very Large - ~100+ mutations)"
    echo "  9. Custom module name"
    echo ""

    read -p "Select module (1-9): " MODULE_CHOICE

    case $MODULE_CHOICE in
        1) MODULE="pdf_export" ;;
        2) MODULE="permissions" ;;
        3) MODULE="serializers" ;;
        4) MODULE="invitation_utils" ;;
        5) MODULE="forms" ;;
        6) MODULE="user_data_utils" ;;
        7) MODULE="models" ;;
        8) MODULE="views" ;;
        9)
            read -p "Enter module name (without .py): " MODULE
            ;;
        *)
            echo -e "${RED}Invalid choice!${NC}"
            read -p "Press Enter to continue..."
            quick_test
            return
            ;;
    esac

    echo ""
    echo -e "Selected module: ${CYAN}${MODULE}${NC}"
    echo ""
    read -p "Enter mutation limit (recommended: 10-50): " LIMIT

    read -p "Generate HTML report? (y/N): " HTML_CHOICE
    HTML=""
    if [[ "$HTML_CHOICE" =~ ^[Yy]$ ]]; then
        HTML="--html"
    fi

    run_test
}

full_module_test() {
    clear
    echo ""
    echo "============================================================================"
    echo "FULL MODULE MUTATION TEST"
    echo "============================================================================"
    echo ""
    echo "This tests ALL mutations in a single module (30-90 minutes)"
    echo ""
    echo "Available modules:"
    echo "  1. pdf_export      (Simple, ~20-40 min)"
    echo "  2. permissions     (Simple, ~20-40 min)"
    echo "  3. serializers     (Simple, ~30-50 min)"
    echo "  4. invitation_utils(Medium, ~30-60 min)"
    echo "  5. forms           (Medium, ~40-80 min)"
    echo "  6. user_data_utils (Medium, ~40-80 min)"
    echo "  7. models          (Large, ~1-3 hours)"
    echo "  8. views           (Very Large, ~3-6 hours)"
    echo "  9. Custom module name"
    echo ""

    read -p "Select module (1-9): " MODULE_CHOICE

    case $MODULE_CHOICE in
        1) MODULE="pdf_export" ;;
        2) MODULE="permissions" ;;
        3) MODULE="serializers" ;;
        4) MODULE="invitation_utils" ;;
        5) MODULE="forms" ;;
        6) MODULE="user_data_utils" ;;
        7) MODULE="models" ;;
        8) MODULE="views" ;;
        9)
            read -p "Enter module name (without .py): " MODULE
            ;;
        *)
            echo -e "${RED}Invalid choice!${NC}"
            read -p "Press Enter to continue..."
            full_module_test
            return
            ;;
    esac

    LIMIT=""

    read -p "Generate HTML report? (y/N): " HTML_CHOICE
    HTML=""
    if [[ "$HTML_CHOICE" =~ ^[Yy]$ ]]; then
        HTML="--html"
    fi

    run_test
}

full_app_test() {
    clear
    echo ""
    echo "============================================================================"
    echo "FULL APPLICATION MUTATION TEST"
    echo "============================================================================"
    echo ""
    echo -e "${YELLOW}WARNING: This will take 8-24+ HOURS to complete!${NC}"
    echo ""
    echo "This tests ALL Python files in active_interview_app/"
    echo "Each mutation requires running the entire test suite."
    echo ""
    echo "Recommended alternatives:"
    echo "  - Test modules individually (Option 2)"
    echo "  - Use quick test mode (Option 1)"
    echo ""

    read -p "Are you SURE you want to continue? (yes/NO): " CONFIRM

    if [[ ! "$CONFIRM" =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Cancelled."
        read -p "Press Enter to continue..."
        main_menu
        return
    fi

    MODULE=""
    LIMIT=""

    read -p "Generate HTML report? (y/N): " HTML_CHOICE
    HTML=""
    if [[ "$HTML_CHOICE" =~ ^[Yy]$ ]]; then
        HTML="--html"
    fi

    run_test
}

custom_config() {
    clear
    echo ""
    echo "============================================================================"
    echo "CUSTOM MUTATION TEST CONFIGURATION"
    echo "============================================================================"
    echo ""

    read -p "Enter module name (leave empty for all modules): " MODULE

    if [ ! -z "$MODULE" ]; then
        read -p "Enter mutation limit (leave empty for no limit): " LIMIT
    else
        LIMIT=""
    fi

    read -p "Generate HTML report? (y/N): " HTML_CHOICE
    HTML=""
    if [[ "$HTML_CHOICE" =~ ^[Yy]$ ]]; then
        HTML="--html"
    fi

    run_test
}

run_test() {
    clear
    echo ""
    echo "============================================================================"
    echo "MUTATION TEST CONFIGURATION"
    echo "============================================================================"
    echo ""

    if [ -z "$MODULE" ]; then
        echo -e "Target: ${YELLOW}ALL modules${NC}"
        echo -e "Estimated time: ${YELLOW}8-24+ hours${NC}"
    else
        echo -e "Target: ${CYAN}${MODULE}.py${NC}"
        if [ -z "$LIMIT" ]; then
            echo -e "Mutations: ${CYAN}All${NC}"
        else
            echo -e "Mutations: ${CYAN}Limited to ${LIMIT}${NC}"
        fi
    fi

    if [[ "$HTML_CHOICE" =~ ^[Yy]$ ]]; then
        echo -e "HTML Report: ${GREEN}Yes${NC}"
    else
        echo "HTML Report: No"
    fi

    echo "============================================================================"
    echo ""
    read -p "Press Enter to continue or Ctrl+C to cancel..."

    # Check Python installation
    echo ""
    echo "[Step 1/5] Checking Python installation..."
    if ! command -v $PYTHON &> /dev/null; then
        echo -e "${RED}ERROR: Python is not installed${NC}"
        read -p "Press Enter to return to menu..."
        main_menu
        return
    fi
    echo -e "${GREEN}✓ Python is installed${NC}"

    # Check mutmut installation
    echo ""
    echo "[Step 2/5] Checking mutmut installation..."
    if ! $PYTHON -m mutmut --version &> /dev/null; then
        echo -e "${YELLOW}mutmut is not installed. Installing...${NC}"
        $PYTHON -m pip install mutmut
        if [ $? -ne 0 ]; then
            echo -e "${RED}ERROR: Failed to install mutmut${NC}"
            read -p "Press Enter to return to menu..."
            main_menu
            return
        fi
    fi
    echo -e "${GREEN}✓ mutmut is installed${NC}"

    # Check if tests pass
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
        read -p "Press Enter to return to menu..."
        main_menu
        return
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

    # Build command
    CMD="$PYTHON run_mutation_tests.py"
    if [ ! -z "$MODULE" ]; then
        CMD="$CMD --module $MODULE"
    fi
    if [ ! -z "$LIMIT" ]; then
        CMD="$CMD --limit $LIMIT"
    fi
    if [ "$HTML" == "--html" ]; then
        CMD="$CMD --html"
    fi

    echo "Command: $CMD"
    echo ""
    echo "You can monitor progress below."
    echo "Feel free to run this in a screen/tmux session."
    echo ""
    echo "============================================================================"
    echo ""

    # Record start time
    START_TIME=$(date +%s)

    # Run mutation tests
    $CMD

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
    echo "Started:  $(date -d @$START_TIME 2>/dev/null || date -r $START_TIME)"
    echo "Finished: $(date -d @$END_TIME 2>/dev/null || date -r $END_TIME)"
    echo "Duration: ${HOURS}h ${MINUTES}m"
    echo ""
    echo "Reports saved in: Research/mutation_testing/"
    echo ""
    echo -e "${GREEN}View your results:${NC}"
    echo "  1. cat Research/mutation_testing/mutation_report_*.md"
    if [ "$HTML" == "--html" ]; then
        echo "  2. open html/index.html"
    fi
    echo ""
    echo -e "${GREEN}Next steps:${NC}"
    echo "  1. Review the mutation score"
    echo "  2. Check survived mutations: $PYTHON -m mutmut results"
    echo "  3. View specific mutations: $PYTHON -m mutmut show [id]"
    echo "  4. Add tests for survived mutations"
    echo ""
    echo ""

    read -p "Return to main menu? (Y/n): " MENU_CHOICE
    if [[ ! "$MENU_CHOICE" =~ ^[Nn]$ ]]; then
        main_menu
    fi
}

view_results() {
    clear
    echo ""
    echo "============================================================================"
    echo "PREVIOUS MUTATION TEST REPORTS"
    echo "============================================================================"
    echo ""

    if [ ! -d "Research/mutation_testing" ]; then
        echo "No reports found. Run a mutation test first."
        read -p "Press Enter to continue..."
        main_menu
        return
    fi

    echo "Recent reports:"
    echo ""

    # List reports with numbers
    ls -t Research/mutation_testing/mutation_report_*.md 2>/dev/null | nl

    if [ $? -ne 0 ]; then
        echo "No reports found. Run a mutation test first."
    else
        echo ""
        echo "Reports are located in: Research/mutation_testing/"
        echo ""
        read -p "Enter report number to view (or 0 to go back): " VIEW_CHOICE

        if [ "$VIEW_CHOICE" != "0" ] && [ ! -z "$VIEW_CHOICE" ]; then
            REPORT_FILE=$(ls -t Research/mutation_testing/mutation_report_*.md 2>/dev/null | sed -n "${VIEW_CHOICE}p")
            if [ ! -z "$REPORT_FILE" ]; then
                clear
                cat "$REPORT_FILE"
                echo ""
                read -p "Press Enter to continue..."
            fi
        fi
    fi

    main_menu
}

show_help() {
    clear
    echo ""
    echo "============================================================================"
    echo "MUTATION TESTING HELP"
    echo "============================================================================"
    echo ""
    echo "WHAT IS MUTATION TESTING?"
    echo "  Mutation testing evaluates test quality by making small changes"
    echo "  (mutations) to your code and checking if tests catch them."
    echo ""
    echo "  - KILLED mutation = Tests detected the change (GOOD!)"
    echo "  - SURVIVED mutation = Tests missed the change (Need more tests)"
    echo ""
    echo "MUTATION SCORE:"
    echo "  Percentage of mutations killed by your tests"
    echo "  - 80%+ = Excellent test coverage"
    echo "  - 60-80% = Good test coverage"
    echo "  - 40-60% = Fair, needs improvement"
    echo "  - Below 40% = Poor, needs significant work"
    echo ""
    echo "WHICH OPTION TO CHOOSE?"
    echo "  1. QUICK TEST: Best for getting started and rapid feedback"
    echo "     - Tests one module with limited mutations"
    echo "     - Takes 20-40 minutes"
    echo "     - Perfect for iterative development"
    echo ""
    echo "  2. FULL MODULE: Complete analysis of one module"
    echo "     - Tests all mutations in one module"
    echo "     - Takes 30-90 minutes per module"
    echo "     - Good for thorough module validation"
    echo ""
    echo "  3. FULL APP: Comprehensive testing (rarely needed)"
    echo "     - Tests entire application"
    echo "     - Takes 8-24+ hours"
    echo "     - Only use before major releases"
    echo ""
    echo "TIPS:"
    echo "  - Start with Quick Test on pdf_export or permissions"
    echo "  - Fix survived mutations by adding test cases"
    echo "  - Use HTML reports for visual analysis"
    echo "  - Run baseline tests first to ensure they pass"
    echo ""
    echo "DOCUMENTATION:"
    echo "  - See MUTATION_TESTING_GUIDE.md for detailed info"
    echo "  - See MANUAL_MUTATION_TESTING.md for alternatives"
    echo "  - See Research/mutation_testing/ for past results"
    echo ""
    echo "============================================================================"
    echo ""

    read -p "Press Enter to continue..."
    main_menu
}

# Make script executable
chmod +x "$0" 2>/dev/null

# Start main menu
main_menu

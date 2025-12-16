#!/bin/bash
###############################################################################
# Start Mutation Tests in Screen Session
#
# This script starts mutation testing in a detached screen session so it
# continues running even if your SSH session ends.
#
# Usage:
#   ./start_mutation_screen.sh                    # Test all modules
#   ./start_mutation_screen.sh models             # Test specific module
#   ./start_mutation_screen.sh forms 20           # Test with mutation limit
#
# To reconnect:
#   screen -r mutation_tests
#
# To check if running:
#   screen -ls
#
###############################################################################

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
SCREEN_NAME="mutation_tests"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNNER="$SCRIPT_DIR/resilient_mutation_runner.py"

# Parse arguments
MODULE="${1:-}"
LIMIT="${2:-}"
PARALLEL="${3:-6}"

echo ""
echo "============================================================================"
echo -e "${CYAN}MUTATION TEST SCREEN LAUNCHER${NC}"
echo "============================================================================"
echo ""

# Check if screen session already exists
if screen -list | grep -q "$SCREEN_NAME"; then
    echo -e "${YELLOW}A mutation test session is already running!${NC}"
    echo ""
    echo "Options:"
    echo "  1. Attach to existing session:  screen -r $SCREEN_NAME"
    echo "  2. Kill existing session:       screen -X -S $SCREEN_NAME quit"
    echo ""
    read -p "Kill existing session and start new one? (y/N): " KILL_EXISTING

    if [[ "$KILL_EXISTING" =~ ^[Yy]$ ]]; then
        screen -X -S "$SCREEN_NAME" quit 2>/dev/null || true
        echo "Killed existing session."
        sleep 1
    else
        echo ""
        echo "To attach to existing session:"
        echo -e "  ${GREEN}screen -r $SCREEN_NAME${NC}"
        exit 0
    fi
fi

# Build command
CMD="python3 $RUNNER --parallel $PARALLEL"

if [ -n "$MODULE" ]; then
    CMD="$CMD --module $MODULE"
    echo -e "Module:     ${CYAN}$MODULE${NC}"
else
    echo -e "Module:     ${CYAN}ALL${NC}"
fi

if [ -n "$LIMIT" ]; then
    CMD="$CMD --limit $LIMIT"
    echo -e "Limit:      ${CYAN}$LIMIT mutations${NC}"
fi

echo -e "Parallel:   ${CYAN}$PARALLEL processes${NC}"
echo -e "Screen:     ${CYAN}$SCREEN_NAME${NC}"
echo ""
echo -e "Command:    ${CYAN}$CMD${NC}"
echo ""

# Confirm start
read -p "Start mutation tests in screen? (Y/n): " CONFIRM
if [[ "$CONFIRM" =~ ^[Nn]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Start screen session
echo ""
echo -e "${GREEN}Starting mutation tests in screen session...${NC}"
echo ""

screen -dmS "$SCREEN_NAME" bash -c "cd $SCRIPT_DIR && $CMD; echo ''; echo 'Press Enter to close...'; read"

sleep 2

# Verify it started
if screen -list | grep -q "$SCREEN_NAME"; then
    echo -e "${GREEN}SUCCESS!${NC} Mutation tests are running in background."
    echo ""
    echo "============================================================================"
    echo -e "${YELLOW}IMPORTANT COMMANDS:${NC}"
    echo "============================================================================"
    echo ""
    echo -e "  ${CYAN}Attach to session:${NC}      screen -r $SCREEN_NAME"
    echo -e "  ${CYAN}Detach (keep running):${NC}  Press Ctrl+A then D"
    echo -e "  ${CYAN}Check if running:${NC}       screen -ls"
    echo -e "  ${CYAN}Kill session:${NC}           screen -X -S $SCREEN_NAME quit"
    echo ""
    echo "============================================================================"
    echo -e "${YELLOW}OUTPUT LOCATIONS:${NC}"
    echo "============================================================================"
    echo ""
    echo -e "  ${CYAN}HTML Report:${NC}   $SCRIPT_DIR/html/index.html"
    echo -e "  ${CYAN}Log Files:${NC}     $SCRIPT_DIR/Research/mutation_testing/logs/"
    echo -e "  ${CYAN}JSON Results:${NC}  $SCRIPT_DIR/Research/mutation_testing/"
    echo ""
    echo "============================================================================"
    echo ""
    echo -e "${GREEN}Tip:${NC} You can safely close this terminal. Tests will continue running."
    echo ""

    # Offer to attach
    read -p "Attach to session now to watch progress? (Y/n): " ATTACH
    if [[ ! "$ATTACH" =~ ^[Nn]$ ]]; then
        echo ""
        echo "Attaching to screen... (Ctrl+A then D to detach)"
        sleep 1
        screen -r "$SCREEN_NAME"
    fi
else
    echo -e "${YELLOW}Warning: Screen session may not have started properly.${NC}"
    echo "Try running manually: $CMD"
fi

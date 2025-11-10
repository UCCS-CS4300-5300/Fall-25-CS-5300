#!/bin/bash
# Claude Code Token Tracker - Simplified Interface
#
# Usage:
#   ./track-tokens.sh                    - Show usage summary (default)
#   ./track-tokens.sh --help             - Show this help
#   ./track-tokens.sh --add              - Track tokens interactively
#   ./track-tokens.sh --add 1000 500     - Track specific counts
#   ./track-tokens.sh --trends           - Show detailed trends
#   ./track-tokens.sh --export file.csv  - Export to CSV

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Python command
PYTHON_CMD=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Error: Python not found${NC}"
    echo "Please install Python 3"
    exit 1
fi

# Show help
show_help() {
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║       📊 CLAUDE CODE TOKEN TRACKER                   ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BOLD}USAGE:${NC}"
    echo "  ./track-tokens.sh [OPTIONS]"
    echo ""
    echo -e "${BOLD}DEFAULT (no arguments):${NC}"
    echo "  Shows quick usage summary for current branch (last 30 days)"
    echo ""
    echo -e "${BOLD}OPTIONS:${NC}"
    echo ""
    echo -e "  ${GREEN}-h, --help${NC}"
    echo "      Show this help message"
    echo ""
    echo -e "  ${GREEN}-a, --add [INPUT] [OUTPUT] [NOTES]${NC}"
    echo "      Track tokens"
    echo "      • No args: Interactive mode (prompts for input)"
    echo "      • With args: Track specific counts"
    echo "      Examples:"
    echo "        ./track-tokens.sh --add                    # Interactive"
    echo "        ./track-tokens.sh -a 10000 5000            # Quick add"
    echo "        ./track-tokens.sh -a 10000 5000 \"Bug fix\" # With notes"
    echo ""
    echo -e "  ${GREEN}--auto${NC}"
    echo "      Attempt automatic token extraction from Claude logs"
    echo "      Example:"
    echo "        ./track-tokens.sh --auto"
    echo ""
    echo -e "  ${GREEN}-s, --show [DAYS]${NC}"
    echo "      Show usage summary"
    echo "      • Default: Last 30 days"
    echo "      • 0 = All time"
    echo "      Examples:"
    echo "        ./track-tokens.sh --show      # Last 30 days"
    echo "        ./track-tokens.sh -s 7        # Last 7 days"
    echo "        ./track-tokens.sh -s 0        # All time"
    echo ""
    echo -e "  ${GREEN}-t, --trends [DAYS]${NC}"
    echo "      Show detailed trends with daily/weekly breakdown"
    echo "      • Default: Last 30 days"
    echo "      Examples:"
    echo "        ./track-tokens.sh --trends    # Last 30 days"
    echo "        ./track-tokens.sh -t 90       # Last 90 days"
    echo ""
    echo -e "  ${GREEN}--all${NC}"
    echo "      Show complete analysis (all time, all branches)"
    echo "      Example:"
    echo "        ./track-tokens.sh --all"
    echo ""
    echo -e "  ${GREEN}-e, --export [FILE]${NC}"
    echo "      Export to CSV"
    echo "      • Default: token_usage_export.csv"
    echo "      Examples:"
    echo "        ./track-tokens.sh --export              # Default filename"
    echo "        ./track-tokens.sh -e monthly_jan.csv    # Custom filename"
    echo ""
    echo -e "  ${GREEN}-d, --dashboard [FILE]${NC}"
    echo "      Generate interactive HTML dashboard"
    echo "      • Default: token_dashboard.html"
    echo "      • Automatically opens in browser"
    echo "      Examples:"
    echo "        ./track-tokens.sh --dashboard           # Default filename"
    echo "        ./track-tokens.sh -d report.html        # Custom filename"
    echo ""
    echo -e "${BOLD}COMMON WORKFLOWS:${NC}"
    echo ""
    echo "  Daily check:"
    echo "    ./track-tokens.sh"
    echo ""
    echo "  Track new session:"
    echo "    ./track-tokens.sh --add"
    echo ""
    echo "  Weekly review:"
    echo "    ./track-tokens.sh --trends"
    echo ""
    echo "  Monthly export:"
    echo "    ./track-tokens.sh --export monthly_\$(date +%Y%m).csv"
    echo ""
    echo "  Generate dashboard:"
    echo "    ./track-tokens.sh --dashboard"
    echo ""
    echo -e "${BOLD}AUTOMATION:${NC}"
    echo "  For automated tracking, see:"
    echo "    ./automate-tracking.sh --help"
    echo ""
}

# Parse arguments
ACTION="show"  # Default action
DAYS=30
OUTPUT_FILE=""
INPUT_TOKENS=""
OUTPUT_TOKENS=""
NOTES=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -a|--add)
            ACTION="add"
            shift
            # Check if next args are numbers (not flags)
            if [[ -n "${1:-}" && "$1" =~ ^[0-9]+$ ]]; then
                INPUT_TOKENS="$1"
                shift
                if [[ -n "${1:-}" && "$1" =~ ^[0-9]+$ ]]; then
                    OUTPUT_TOKENS="$1"
                    shift
                    # Check for notes
                    if [[ -n "${1:-}" && ! "$1" =~ ^- ]]; then
                        NOTES="$1"
                        shift
                    fi
                fi
            fi
            ;;
        --auto)
            ACTION="auto"
            shift
            ;;
        -s|--show)
            ACTION="show"
            shift
            if [[ -n "${1:-}" && "$1" =~ ^[0-9]+$ ]]; then
                DAYS="$1"
                shift
            fi
            ;;
        -t|--trends)
            ACTION="trends"
            shift
            if [[ -n "${1:-}" && "$1" =~ ^[0-9]+$ ]]; then
                DAYS="$1"
                shift
            fi
            ;;
        --all)
            ACTION="all"
            shift
            ;;
        -e|--export)
            ACTION="export"
            shift
            if [[ -n "${1:-}" && ! "$1" =~ ^- ]]; then
                OUTPUT_FILE="$1"
                shift
            else
                OUTPUT_FILE="token_usage_export.csv"
            fi
            ;;
        -d|--dashboard)
            ACTION="dashboard"
            shift
            if [[ -n "${1:-}" && ! "$1" =~ ^- ]]; then
                OUTPUT_FILE="$1"
                shift
            else
                OUTPUT_FILE="token_dashboard.html"
            fi
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            echo ""
            echo "Run './track-tokens.sh --help' for usage information"
            exit 1
            ;;
    esac
done

# Execute action
case "$ACTION" in
    add)
        if [ -z "$INPUT_TOKENS" ]; then
            # Interactive mode
            echo -e "${BLUE}🤖 Interactive Token Tracking${NC}"
            $PYTHON_CMD "$SCRIPT_DIR/track-claude-tokens.py" --interactive
        else
            # Specific counts mode
            if [ -z "$OUTPUT_TOKENS" ]; then
                echo -e "${RED}❌ Error: Need both input and output tokens${NC}"
                echo "Usage: ./track-tokens.sh --add [input-tokens] [output-tokens]"
                exit 1
            fi

            if [ -n "$NOTES" ]; then
                $PYTHON_CMD "$SCRIPT_DIR/track-claude-tokens.py" \
                    --input-tokens "$INPUT_TOKENS" \
                    --output-tokens "$OUTPUT_TOKENS" \
                    --notes "$NOTES"
            else
                $PYTHON_CMD "$SCRIPT_DIR/track-claude-tokens.py" \
                    --input-tokens "$INPUT_TOKENS" \
                    --output-tokens "$OUTPUT_TOKENS"
            fi
        fi
        ;;

    auto)
        echo -e "${BLUE}🔍 Attempting automatic token extraction...${NC}"
        $PYTHON_CMD "$SCRIPT_DIR/extract-claude-tokens.py" --auto-track
        ;;

    show)
        $PYTHON_CMD "$SCRIPT_DIR/analyze-token-trends.py" --days "$DAYS"
        ;;

    trends)
        $PYTHON_CMD "$SCRIPT_DIR/analyze-token-trends.py" \
            --days "$DAYS" --daily --weekly --insights
        ;;

    all)
        $PYTHON_CMD "$SCRIPT_DIR/analyze-token-trends.py" \
            --days 0 --all
        ;;

    export)
        [ -z "$OUTPUT_FILE" ] && OUTPUT_FILE="token_usage_export.csv"
        echo -e "${BLUE}📊 Exporting to $OUTPUT_FILE...${NC}"
        $PYTHON_CMD "$SCRIPT_DIR/analyze-token-trends.py" \
            --days 0 --export-csv "$OUTPUT_FILE"
        echo -e "${GREEN}✅ Export complete: $OUTPUT_FILE${NC}"
        ;;

    dashboard)
        [ -z "$OUTPUT_FILE" ] && OUTPUT_FILE="token_dashboard.html"
        echo -e "${BLUE}📊 Generating dashboard...${NC}"
        $PYTHON_CMD "$SCRIPT_DIR/generate-dashboard.py" --output "$OUTPUT_FILE"
        echo -e "${GREEN}✅ Dashboard created: $OUTPUT_FILE${NC}"

        # Try to open in browser
        if command -v open >/dev/null 2>&1; then
            echo -e "${BLUE}🌐 Opening in browser...${NC}"
            open "$OUTPUT_FILE"
        elif command -v xdg-open >/dev/null 2>&1; then
            echo -e "${BLUE}🌐 Opening in browser...${NC}"
            xdg-open "$OUTPUT_FILE"
        else
            echo -e "${YELLOW}💡 Open $OUTPUT_FILE in your browser${NC}"
        fi
        ;;
esac

#!/bin/bash
# Automated Token Tracking and Reporting
#
# This script provides automation for token tracking:
# - Daily summaries
# - Weekly reports
# - Monthly exports
# - Auto-detection and tracking
#
# Usage:
#   ./automate-tracking.sh daily          - Daily summary
#   ./automate-tracking.sh weekly         - Weekly report
#   ./automate-tracking.sh monthly        - Monthly export
#   ./automate-tracking.sh watch          - Watch and auto-track
#   ./automate-tracking.sh setup-cron     - Setup automated cron jobs

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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
    exit 1
fi

# Reports directory
REPORTS_DIR="$REPO_ROOT/token_metrics/reports"
mkdir -p "$REPORTS_DIR"

# Daily summary
daily_summary() {
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║        📅 DAILY TOKEN USAGE SUMMARY                   ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""

    DATE=$(date +%Y-%m-%d)
    REPORT_FILE="$REPORTS_DIR/daily_$DATE.txt"

    # Generate report
    $PYTHON_CMD "$SCRIPT_DIR/analyze-token-trends.py" \
        --days 1 --daily --insights | tee "$REPORT_FILE"

    echo -e "${GREEN}✅ Daily summary saved to: $REPORT_FILE${NC}"
    echo ""
}

# Weekly report
weekly_report() {
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║        📊 WEEKLY TOKEN USAGE REPORT                   ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""

    WEEK=$(date +%Y-W%V)
    REPORT_FILE="$REPORTS_DIR/weekly_$WEEK.txt"
    CSV_FILE="$REPORTS_DIR/weekly_$WEEK.csv"

    # Generate report
    $PYTHON_CMD "$SCRIPT_DIR/analyze-token-trends.py" \
        --days 7 --all | tee "$REPORT_FILE"

    # Export CSV
    $PYTHON_CMD "$SCRIPT_DIR/analyze-token-trends.py" \
        --days 7 --export-csv "$CSV_FILE"

    echo ""
    echo -e "${GREEN}✅ Weekly report saved to:${NC}"
    echo -e "   Text: $REPORT_FILE"
    echo -e "   CSV:  $CSV_FILE"
    echo ""

    # Show summary stats
    echo -e "${BLUE}📈 Quick Stats:${NC}"
    grep "Total tokens:" "$REPORT_FILE" || true
    grep "Estimated cost:" "$REPORT_FILE" || true
    grep "Projected monthly cost:" "$REPORT_FILE" || true
    echo ""
}

# Monthly export
monthly_export() {
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║        📦 MONTHLY TOKEN USAGE EXPORT                  ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""

    MONTH=$(date +%Y-%m)
    REPORT_FILE="$REPORTS_DIR/monthly_$MONTH.txt"
    CSV_FILE="$REPORTS_DIR/monthly_$MONTH.csv"
    JSON_FILE="$REPORTS_DIR/monthly_$MONTH.json"
    DASHBOARD_FILE="$REPORTS_DIR/monthly_$MONTH.html"

    echo -e "${BLUE}Generating comprehensive monthly reports...${NC}"
    echo ""

    # Text report
    echo "📄 Generating text report..."
    $PYTHON_CMD "$SCRIPT_DIR/analyze-token-trends.py" \
        --days 30 --all > "$REPORT_FILE"

    # CSV export
    echo "📊 Exporting to CSV..."
    $PYTHON_CMD "$SCRIPT_DIR/analyze-token-trends.py" \
        --days 30 --export-csv "$CSV_FILE"

    # JSON export
    echo "📋 Exporting to JSON..."
    $PYTHON_CMD "$SCRIPT_DIR/analyze-token-trends.py" \
        --days 30 --export-json "$JSON_FILE"

    # Dashboard
    echo "🌐 Generating HTML dashboard..."
    $PYTHON_CMD "$SCRIPT_DIR/generate-dashboard.py" \
        --days 30 --output "$DASHBOARD_FILE"

    echo ""
    echo -e "${GREEN}✅ Monthly export complete!${NC}"
    echo ""
    echo "Files created:"
    echo "  📄 Report:    $REPORT_FILE"
    echo "  📊 CSV:       $CSV_FILE"
    echo "  📋 JSON:      $JSON_FILE"
    echo "  🌐 Dashboard: $DASHBOARD_FILE"
    echo ""

    # Show cost summary
    echo -e "${BLUE}💰 Monthly Cost Summary:${NC}"
    grep "Estimated cost:" "$REPORT_FILE" | head -1 || true
    grep "Projected monthly cost:" "$REPORT_FILE" || true
    echo ""
}

# Watch mode - continuously check for new sessions
watch_mode() {
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║        👀 WATCH MODE - Auto Token Tracking            ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Monitoring for Claude Code usage...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""

    LAST_COUNT=0

    while true; do
        # Try auto-extraction
        $PYTHON_CMD "$SCRIPT_DIR/extract-claude-tokens.py" \
            --auto-track --silent 2>/dev/null && {
            # Check if new session was added
            CURRENT_COUNT=$(find "$REPO_ROOT/temp" -name "claude_local_*.json" 2>/dev/null | wc -l)

            if [ "$CURRENT_COUNT" -gt "$LAST_COUNT" ]; then
                echo -e "${GREEN}✅ [$(date +%H:%M:%S)] New tokens tracked automatically!${NC}"
                LAST_COUNT=$CURRENT_COUNT
            fi
        }

        # Wait before next check (every 5 minutes)
        sleep 300
    done
}

# Setup cron jobs
setup_cron() {
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║        ⏰ SETUP AUTOMATED CRON JOBS                   ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""

    CRON_SCRIPT="$SCRIPT_DIR/automate-tracking.sh"

    echo "This will add the following cron jobs:"
    echo ""
    echo "  Daily summary:   Every day at 9 AM"
    echo "  Weekly report:   Every Monday at 9 AM"
    echo "  Monthly export:  1st of month at 9 AM"
    echo ""
    echo "Cron entries to add:"
    echo ""
    echo "# Token tracking automation"
    echo "0 9 * * *   $CRON_SCRIPT daily  >> $REPORTS_DIR/daily.log 2>&1"
    echo "0 9 * * 1   $CRON_SCRIPT weekly >> $REPORTS_DIR/weekly.log 2>&1"
    echo "0 9 1 * *   $CRON_SCRIPT monthly >> $REPORTS_DIR/monthly.log 2>&1"
    echo ""

    read -p "Add these to your crontab? (y/N): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Add to crontab
        (crontab -l 2>/dev/null || true; cat <<EOF

# Token tracking automation
0 9 * * *   $CRON_SCRIPT daily  >> $REPORTS_DIR/daily.log 2>&1
0 9 * * 1   $CRON_SCRIPT weekly >> $REPORTS_DIR/weekly.log 2>&1
0 9 1 * *   $CRON_SCRIPT monthly >> $REPORTS_DIR/monthly.log 2>&1
EOF
        ) | crontab -

        echo -e "${GREEN}✅ Cron jobs added successfully!${NC}"
        echo ""
        echo "View with: crontab -l"
        echo "Edit with: crontab -e"
        echo "Remove with: crontab -r"
    else
        echo -e "${YELLOW}⏭  Skipped cron setup${NC}"
        echo "You can manually add these entries with: crontab -e"
    fi
    echo ""
}

# Show usage
show_usage() {
    echo -e "${CYAN}🤖 Automated Token Tracking${NC}"
    echo ""
    echo "Usage:"
    echo "  ./automate-tracking.sh daily         - Generate daily summary"
    echo "  ./automate-tracking.sh weekly        - Generate weekly report"
    echo "  ./automate-tracking.sh monthly       - Generate monthly export"
    echo "  ./automate-tracking.sh watch         - Watch mode (auto-track)"
    echo "  ./automate-tracking.sh setup-cron    - Setup automated cron jobs"
    echo ""
    echo "Reports are saved to: $REPORTS_DIR"
    echo ""
}

# Main
CMD="${1:-}"

case "$CMD" in
    daily)
        daily_summary
        ;;
    weekly)
        weekly_report
        ;;
    monthly)
        monthly_export
        ;;
    watch)
        watch_mode
        ;;
    setup-cron)
        setup_cron
        ;;
    help|--help|-h|"")
        show_usage
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $CMD${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac

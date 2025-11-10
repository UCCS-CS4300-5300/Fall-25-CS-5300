#!/bin/bash
# Token Tracking Utilities
#
# Collection of useful bash functions for token tracking
#
# Usage:
#   source token-utils.sh
#   token_summary
#   token_cost_check 50
#   token_branch_compare feature/a feature/b

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Get repo root
get_repo_root() {
    git rev-parse --show-toplevel 2>/dev/null || pwd
}

# Get current branch
get_current_branch() {
    git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown"
}

# Quick token summary
token_summary() {
    local REPO_ROOT=$(get_repo_root)
    local BRANCH=$(get_current_branch)

    echo -e "${CYAN}📊 Quick Token Summary${NC}"
    echo -e "${BLUE}Branch: $BRANCH${NC}"
    echo ""

    # Check if tracking file exists
    local SAFE_BRANCH=$(echo "$BRANCH" | tr '/' '_')
    local TRACKING_FILE="$REPO_ROOT/token_metrics/local_tracking/tokens_$SAFE_BRANCH.json"

    if [ -f "$TRACKING_FILE" ]; then
        # Parse JSON (requires jq or python)
        if command -v jq >/dev/null 2>&1; then
            local TOTAL=$(jq -r '.total_tokens // 0' "$TRACKING_FILE")
            local SESSIONS=$(jq -r '.sessions | length' "$TRACKING_FILE")
            local COST=$(echo "scale=4; ($TOTAL * 0.8 * 0.003 + $TOTAL * 0.2 * 0.015) / 1000" | bc)

            echo -e "  Tokens:   ${GREEN}${TOTAL}${NC}"
            echo -e "  Sessions: ${GREEN}${SESSIONS}${NC}"
            echo -e "  Cost:     ${GREEN}\$${COST}${NC}"
        else
            echo -e "${YELLOW}⚠️  Install 'jq' for detailed summary${NC}"
            echo -e "File: $TRACKING_FILE"
        fi
    else
        echo -e "${YELLOW}⚠️  No tracking data for this branch yet${NC}"
        echo -e "Start tracking: ./track-tokens.sh add"
    fi
    echo ""
}

# Check if cost exceeds threshold
token_cost_check() {
    local THRESHOLD=${1:-50}
    local REPO_ROOT=$(get_repo_root)
    local BRANCH=$(get_current_branch)

    local SAFE_BRANCH=$(echo "$BRANCH" | tr '/' '_')
    local TRACKING_FILE="$REPO_ROOT/token_metrics/local_tracking/tokens_$SAFE_BRANCH.json"

    if [ ! -f "$TRACKING_FILE" ]; then
        echo -e "${YELLOW}⚠️  No tracking data${NC}"
        return 0
    fi

    if command -v jq >/dev/null 2>&1; then
        local TOTAL=$(jq -r '.total_tokens // 0' "$TRACKING_FILE")
        local COST=$(echo "scale=4; ($TOTAL * 0.8 * 0.003 + $TOTAL * 0.2 * 0.015) / 1000" | bc)
        local THRESHOLD_DOLLARS=$(echo "scale=2; $THRESHOLD" | bc)

        if (( $(echo "$COST > $THRESHOLD_DOLLARS" | bc -l) )); then
            echo -e "${RED}⚠️  COST ALERT!${NC}"
            echo -e "Current cost: ${RED}\$$COST${NC}"
            echo -e "Threshold:    \$$THRESHOLD_DOLLARS"
            return 1
        else
            echo -e "${GREEN}✅ Under budget${NC}"
            echo -e "Current cost: \$$COST / \$$THRESHOLD_DOLLARS"
            return 0
        fi
    else
        echo -e "${YELLOW}⚠️  Install 'jq' and 'bc' for cost checking${NC}"
        return 0
    fi
}

# Compare two branches
token_branch_compare() {
    local BRANCH1=${1:-}
    local BRANCH2=${2:-}

    if [ -z "$BRANCH1" ] || [ -z "$BRANCH2" ]; then
        echo "Usage: token_branch_compare <branch1> <branch2>"
        return 1
    fi

    local REPO_ROOT=$(get_repo_root)

    echo -e "${CYAN}🔄 Branch Comparison${NC}"
    echo ""

    # Branch 1
    local SAFE_BRANCH1=$(echo "$BRANCH1" | tr '/' '_')
    local FILE1="$REPO_ROOT/token_metrics/local_tracking/tokens_$SAFE_BRANCH1.json"

    if [ -f "$FILE1" ] && command -v jq >/dev/null 2>&1; then
        local TOTAL1=$(jq -r '.total_tokens // 0' "$FILE1")
        local SESSIONS1=$(jq -r '.sessions | length' "$FILE1")
        local COST1=$(echo "scale=4; ($TOTAL1 * 0.8 * 0.003 + $TOTAL1 * 0.2 * 0.015) / 1000" | bc)

        echo -e "${BLUE}$BRANCH1:${NC}"
        echo -e "  Tokens:   $TOTAL1"
        echo -e "  Sessions: $SESSIONS1"
        echo -e "  Cost:     \$$COST1"
    else
        echo -e "${YELLOW}$BRANCH1: No data${NC}"
        TOTAL1=0
        COST1=0
    fi

    echo ""

    # Branch 2
    local SAFE_BRANCH2=$(echo "$BRANCH2" | tr '/' '_')
    local FILE2="$REPO_ROOT/token_metrics/local_tracking/tokens_$SAFE_BRANCH2.json"

    if [ -f "$FILE2" ] && command -v jq >/dev/null 2>&1; then
        local TOTAL2=$(jq -r '.total_tokens // 0' "$FILE2")
        local SESSIONS2=$(jq -r '.sessions | length' "$FILE2")
        local COST2=$(echo "scale=4; ($TOTAL2 * 0.8 * 0.003 + $TOTAL2 * 0.2 * 0.015) / 1000" | bc)

        echo -e "${BLUE}$BRANCH2:${NC}"
        echo -e "  Tokens:   $TOTAL2"
        echo -e "  Sessions: $SESSIONS2"
        echo -e "  Cost:     \$$COST2"
    else
        echo -e "${YELLOW}$BRANCH2: No data${NC}"
        TOTAL2=0
        COST2=0
    fi

    echo ""
    echo -e "${CYAN}Difference:${NC}"

    if [ "$TOTAL1" -gt 0 ] && [ "$TOTAL2" -gt 0 ]; then
        local DIFF_TOKENS=$((TOTAL1 - TOTAL2))
        local DIFF_COST=$(echo "scale=4; $COST1 - $COST2" | bc)

        if [ "$DIFF_TOKENS" -gt 0 ]; then
            echo -e "  $BRANCH1 used ${GREEN}$DIFF_TOKENS more tokens${NC} (\$${DIFF_COST} more)"
        else
            echo -e "  $BRANCH2 used ${GREEN}${DIFF_TOKENS#-} more tokens${NC} (\$${DIFF_COST#-} more)"
        fi
    fi
    echo ""
}

# Show top N most expensive branches
token_top_branches() {
    local N=${1:-5}
    local REPO_ROOT=$(get_repo_root)
    local TRACKING_DIR="$REPO_ROOT/token_metrics/local_tracking"

    if [ ! -d "$TRACKING_DIR" ]; then
        echo -e "${YELLOW}⚠️  No tracking data found${NC}"
        return 1
    fi

    echo -e "${CYAN}🏆 Top $N Most Expensive Branches${NC}"
    echo ""

    if ! command -v jq >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Install 'jq' for this feature${NC}"
        return 1
    fi

    # Collect all branch data
    local TEMP_FILE=$(mktemp)

    for file in "$TRACKING_DIR"/tokens_*.json; do
        if [ -f "$file" ]; then
            local BRANCH=$(jq -r '.branch // "unknown"' "$file")
            local TOKENS=$(jq -r '.total_tokens // 0' "$file")
            local COST=$(echo "scale=4; ($TOKENS * 0.8 * 0.003 + $TOKENS * 0.2 * 0.015) / 1000" | bc)

            echo "$TOKENS|$COST|$BRANCH" >> "$TEMP_FILE"
        fi
    done

    # Sort and display
    sort -t'|' -k1 -nr "$TEMP_FILE" | head -n "$N" | while IFS='|' read -r tokens cost branch; do
        printf "  %-40s %15s tokens  \$%.4f\n" "$branch" "$tokens" "$cost"
    done

    rm "$TEMP_FILE"
    echo ""
}

# Estimate monthly cost projection
token_monthly_projection() {
    local DAYS=${1:-7}
    local REPO_ROOT=$(get_repo_root)

    echo -e "${CYAN}💰 Monthly Cost Projection${NC}"
    echo -e "${BLUE}Based on last $DAYS days${NC}"
    echo ""

    # Run analysis and extract projection
    python3 "$REPO_ROOT/token_metrics/scripts/analyze-token-trends.py" \
        --days "$DAYS" --insights 2>/dev/null | grep "Projected monthly cost" || {
        echo -e "${YELLOW}⚠️  Not enough data for projection${NC}"
    }
    echo ""
}

# Quick add tokens
token_quick_add() {
    local TOKENS=${1:-}

    if [ -z "$TOKENS" ]; then
        echo "Usage: token_quick_add <total_tokens>"
        echo "Example: token_quick_add 15000"
        return 1
    fi

    # Assume 80/20 split
    local INPUT=$(echo "scale=0; $TOKENS * 0.8 / 1" | bc)
    local OUTPUT=$(echo "scale=0; $TOKENS * 0.2 / 1" | bc)

    local REPO_ROOT=$(get_repo_root)

    echo -e "${BLUE}Adding $TOKENS tokens (${INPUT} input, ${OUTPUT} output)${NC}"

    python3 "$REPO_ROOT/token_metrics/scripts/track-claude-tokens.py" \
        --input-tokens "$INPUT" \
        --output-tokens "$OUTPUT"
}

# Show all available functions
token_help() {
    echo -e "${CYAN}🔧 Token Tracking Utilities${NC}"
    echo ""
    echo "Available functions:"
    echo ""
    echo -e "  ${GREEN}token_summary${NC}"
    echo "    Show quick summary for current branch"
    echo ""
    echo -e "  ${GREEN}token_cost_check [threshold]${NC}"
    echo "    Check if cost exceeds threshold (default: \$50)"
    echo "    Example: token_cost_check 25"
    echo ""
    echo -e "  ${GREEN}token_branch_compare <branch1> <branch2>${NC}"
    echo "    Compare token usage between two branches"
    echo "    Example: token_branch_compare feature/a feature/b"
    echo ""
    echo -e "  ${GREEN}token_top_branches [n]${NC}"
    echo "    Show top N most expensive branches (default: 5)"
    echo "    Example: token_top_branches 10"
    echo ""
    echo -e "  ${GREEN}token_monthly_projection [days]${NC}"
    echo "    Estimate monthly cost based on recent usage"
    echo "    Example: token_monthly_projection 14"
    echo ""
    echo -e "  ${GREEN}token_quick_add <tokens>${NC}"
    echo "    Quickly add tokens with 80/20 split assumption"
    echo "    Example: token_quick_add 15000"
    echo ""
    echo "Usage:"
    echo "  source token-utils.sh"
    echo "  token_summary"
    echo ""
}

# If sourced, show help
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    echo -e "${YELLOW}This script is meant to be sourced, not executed${NC}"
    echo ""
    echo "Usage:"
    echo -e "  ${GREEN}source ${BASH_SOURCE[0]}${NC}"
    echo -e "  ${GREEN}token_help${NC}"
    echo ""
else
    # Sourced successfully
    echo -e "${GREEN}✅ Token utilities loaded${NC}"
    echo -e "Run ${CYAN}token_help${NC} for available functions"
    echo ""
fi

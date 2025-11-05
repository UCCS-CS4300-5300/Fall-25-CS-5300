#!/bin/bash
#
# Install Git Hooks
#
# This script installs custom git hooks for the repository.
# It creates symlinks from .git/hooks to .githooks directory.
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the repository root
REPO_ROOT=$(git rev-parse --show-toplevel)
HOOKS_DIR="$REPO_ROOT/.githooks"
GIT_HOOKS_DIR="$REPO_ROOT/.git/hooks"

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║            Git Hooks Installation Script                ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if .githooks directory exists
if [ ! -d "$HOOKS_DIR" ]; then
    echo -e "${RED}❌ Error: .githooks directory not found${NC}"
    echo -e "${YELLOW}   Expected: $HOOKS_DIR${NC}"
    exit 1
fi

# Check if .git/hooks directory exists
if [ ! -d "$GIT_HOOKS_DIR" ]; then
    echo -e "${RED}❌ Error: .git/hooks directory not found${NC}"
    echo -e "${YELLOW}   Expected: $GIT_HOOKS_DIR${NC}"
    echo -e "${YELLOW}   Are you in a git repository?${NC}"
    exit 1
fi

# Install hooks
INSTALLED=0
SKIPPED=0

echo -e "${BLUE}📦 Installing git hooks...${NC}"
echo ""

for hook_file in "$HOOKS_DIR"/*; do
    if [ -f "$hook_file" ]; then
        hook_name=$(basename "$hook_file")
        target="$GIT_HOOKS_DIR/$hook_name"

        # Check if hook already exists
        if [ -e "$target" ] || [ -L "$target" ]; then
            # Check if it's a symlink to our hook
            if [ -L "$target" ] && [ "$(readlink "$target")" == "$hook_file" ]; then
                echo -e "${YELLOW}⏭  Skipped:${NC} $hook_name (already installed)"
                SKIPPED=$((SKIPPED + 1))
                continue
            fi

            # Backup existing hook
            backup="$target.backup-$(date +%Y%m%d-%H%M%S)"
            mv "$target" "$backup"
            echo -e "${YELLOW}📋 Backed up:${NC} $hook_name -> $(basename "$backup")"
        fi

        # Create symlink
        ln -s "$hook_file" "$target"
        chmod +x "$target"

        echo -e "${GREEN}✅ Installed:${NC} $hook_name"
        INSTALLED=$((INSTALLED + 1))
    fi
done

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                  Installation Summary                   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${GREEN}✓${NC} Installed: $INSTALLED hook(s)"
echo -e "  ${YELLOW}⏭${NC} Skipped:   $SKIPPED hook(s)"
echo ""

if [ $INSTALLED -gt 0 ]; then
    echo -e "${GREEN}🎉 Git hooks installed successfully!${NC}"
    echo ""
    echo -e "${BLUE}ℹ  Installed hooks:${NC}"

    for hook_file in "$HOOKS_DIR"/*; do
        if [ -f "$hook_file" ]; then
            hook_name=$(basename "$hook_file")
            echo -e "   • ${YELLOW}$hook_name${NC}"

            # Show description based on hook name
            case "$hook_name" in
                post-commit)
                    echo -e "     ${BLUE}→${NC} Prompts to track Claude Code token usage after commits"
                    ;;
                pre-push)
                    echo -e "     ${BLUE}→${NC} Runs checks before pushing to remote"
                    ;;
                *)
                    echo -e "     ${BLUE}→${NC} Custom hook"
                    ;;
            esac
        fi
    done
else
    echo -e "${YELLOW}ℹ  No new hooks were installed${NC}"
fi

echo ""
echo -e "${BLUE}💡 Tip:${NC} You can disable hooks temporarily with:"
echo -e "   ${YELLOW}git commit --no-verify${NC}"
echo ""

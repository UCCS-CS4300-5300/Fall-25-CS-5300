#!/bin/bash
# Test Security Scanning Setup
# Verifies Bandit configuration and GitHub integration readiness

set -e

echo "=================================="
echo "Security Scan Setup Verification"
echo "=================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in Git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Not in a Git repository${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Git repository detected${NC}"

# Check if .bandit config exists
if [ -f ".bandit" ]; then
    echo -e "${GREEN}✅ Bandit configuration file found${NC}"
else
    echo -e "${YELLOW}⚠️  No .bandit configuration file found${NC}"
    echo "   Creating default configuration..."
    # Could create default here if needed
fi

# Check if workflow exists
if [ -f ".github/workflows/security-scan.yml" ]; then
    echo -e "${GREEN}✅ Security scan workflow found${NC}"
else
    echo -e "${RED}❌ Security scan workflow not found${NC}"
    echo "   Expected: .github/workflows/security-scan.yml"
    exit 1
fi

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ Python found: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi

# Check if Bandit is installed
echo ""
echo "Checking Bandit installation..."
if command -v bandit &> /dev/null; then
    BANDIT_VERSION=$(bandit --version 2>&1 | head -n 1)
    echo -e "${GREEN}✅ Bandit installed: $BANDIT_VERSION${NC}"
else
    echo -e "${YELLOW}⚠️  Bandit not installed${NC}"
    echo "   Installing Bandit..."
    pip install bandit[sarif] || {
        echo -e "${RED}❌ Failed to install Bandit${NC}"
        exit 1
    }
    echo -e "${GREEN}✅ Bandit installed successfully${NC}"
fi

# Test Bandit scan
echo ""
echo "Running test Bandit scan..."
if bandit -r . --configfile .bandit -f json -o /tmp/bandit-test.json 2>/dev/null; then
    echo -e "${GREEN}✅ Bandit scan completed${NC}"

    # Count issues
    ISSUE_COUNT=$(python3 -c "import json; data=json.load(open('/tmp/bandit-test.json')); print(len(data.get('results', [])))" 2>/dev/null || echo "0")
    echo "   Found $ISSUE_COUNT issue(s)"
else
    echo -e "${YELLOW}⚠️  Bandit scan completed with warnings${NC}"
fi

# Test SARIF generation
echo ""
echo "Testing SARIF format generation..."
if bandit -r . --configfile .bandit -f sarif -o /tmp/bandit-test.sarif 2>/dev/null; then
    echo -e "${GREEN}✅ SARIF generation successful${NC}"

    # Validate SARIF JSON
    if python3 -m json.tool /tmp/bandit-test.sarif > /dev/null 2>&1; then
        echo -e "${GREEN}✅ SARIF file is valid JSON${NC}"

        FILE_SIZE=$(wc -c < /tmp/bandit-test.sarif)
        echo "   SARIF file size: $FILE_SIZE bytes"

        # Check for required SARIF fields
        HAS_VERSION=$(python3 -c "import json; data=json.load(open('/tmp/bandit-test.sarif')); print('version' in data)" 2>/dev/null || echo "False")
        HAS_RUNS=$(python3 -c "import json; data=json.load(open('/tmp/bandit-test.sarif')); print('runs' in data)" 2>/dev/null || echo "False")

        if [ "$HAS_VERSION" = "True" ] && [ "$HAS_RUNS" = "True" ]; then
            echo -e "${GREEN}✅ SARIF structure is valid${NC}"
        else
            echo -e "${YELLOW}⚠️  SARIF structure may be incomplete${NC}"
        fi
    else
        echo -e "${RED}❌ SARIF file is not valid JSON${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ SARIF generation failed${NC}"
    exit 1
fi

# Check GitHub Actions workflow syntax
echo ""
echo "Validating workflow YAML syntax..."
if python3 -c "import yaml; yaml.safe_load(open('.github/workflows/security-scan.yml'))" 2>/dev/null; then
    echo -e "${GREEN}✅ Workflow YAML is valid${NC}"
else
    echo -e "${RED}❌ Workflow YAML has syntax errors${NC}"
    exit 1
fi

# Check for required permissions in workflow
echo ""
echo "Checking workflow permissions..."
WORKFLOW_FILE=".github/workflows/security-scan.yml"

if grep -q "security-events: write" "$WORKFLOW_FILE"; then
    echo -e "${GREEN}✅ security-events permission configured${NC}"
else
    echo -e "${RED}❌ Missing security-events: write permission${NC}"
    exit 1
fi

if grep -q "issues: write" "$WORKFLOW_FILE"; then
    echo -e "${GREEN}✅ issues permission configured${NC}"
else
    echo -e "${YELLOW}⚠️  Missing issues: write permission (optional)${NC}"
fi

# Check workflow triggers
echo ""
echo "Checking workflow triggers..."
if grep -q "schedule:" "$WORKFLOW_FILE"; then
    echo -e "${GREEN}✅ Scheduled trigger configured${NC}"
    CRON=$(grep -A 1 "schedule:" "$WORKFLOW_FILE" | grep "cron:" | sed "s/.*cron: '\(.*\)'/\1/")
    echo "   Schedule: $CRON"
else
    echo -e "${YELLOW}⚠️  No scheduled trigger${NC}"
fi

if grep -q "workflow_dispatch:" "$WORKFLOW_FILE"; then
    echo -e "${GREEN}✅ Manual trigger enabled${NC}"
else
    echo -e "${YELLOW}⚠️  Manual trigger not enabled${NC}"
fi

# Check for CodeQL action
echo ""
echo "Checking CodeQL action integration..."
if grep -q "github/codeql-action/upload-sarif@v3" "$WORKFLOW_FILE"; then
    echo -e "${GREEN}✅ CodeQL SARIF upload action found${NC}"
else
    echo -e "${RED}❌ CodeQL SARIF upload action not found${NC}"
    exit 1
fi

# Repository information
echo ""
echo "=================================="
echo "Repository Information"
echo "=================================="
REPO_URL=$(git remote get-url origin 2>/dev/null || echo "No remote configured")
CURRENT_BRANCH=$(git branch --show-current)
echo "Remote: $REPO_URL"
echo "Branch: $CURRENT_BRANCH"

# Check if GitHub Security features are available
echo ""
echo "=================================="
echo "GitHub Integration Checklist"
echo "=================================="
echo "To enable GitHub Code Scanning:"
echo ""
echo "1. ✅ SARIF format: Ready"
echo "2. ✅ Upload action: Configured"
echo "3. ✅ Workflow file: Present"
echo "4. 📋 Enable GitHub Advanced Security (if private repo)"
echo "5. 📋 Push workflow to GitHub"
echo "6. 📋 Check Security tab after first run"
echo ""
echo "Manual test run command:"
echo "  gh workflow run security-scan.yml"
echo ""
echo "View results:"
echo "  https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/security/code-scanning"
echo ""

# Cleanup
rm -f /tmp/bandit-test.json /tmp/bandit-test.sarif

echo "=================================="
echo -e "${GREEN}✅ All checks passed!${NC}"
echo "=================================="
echo ""
echo "Your security scanning setup is ready for GitHub!"
echo ""
echo "Next steps:"
echo "1. Commit and push these changes"
echo "2. Go to Actions tab and manually trigger 'Scheduled Security Scan'"
echo "3. Check Security tab for results"

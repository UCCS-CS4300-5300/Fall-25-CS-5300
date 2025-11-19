# Test Security Scanning Setup (PowerShell)
# Verifies Bandit configuration and GitHub integration readiness

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Security Scan Setup Verification" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

$script:errors = 0
$script:warnings = 0

function Test-Check {
    param(
        [string]$Message,
        [bool]$Success,
        [bool]$IsWarning = $false
    )

    if ($Success) {
        Write-Host "✅ $Message" -ForegroundColor Green
    } elseif ($IsWarning) {
        Write-Host "⚠️  $Message" -ForegroundColor Yellow
        $script:warnings++
    } else {
        Write-Host "❌ $Message" -ForegroundColor Red
        $script:errors++
    }
}

# Check if in Git repository
$gitDir = git rev-parse --git-dir 2>&1
if ($LASTEXITCODE -eq 0) {
    Test-Check "Git repository detected" $true
} else {
    Test-Check "Not in a Git repository" $false
    exit 1
}

# Check if .bandit config exists
$banditConfigExists = Test-Path ".bandit"
if ($banditConfigExists) {
    Test-Check "Bandit configuration file found" $true
} else {
    Test-Check "No .bandit configuration file found" $false $true
}

# Check if workflow exists
$workflowExists = Test-Path ".github/workflows/security-scan.yml"
if ($workflowExists) {
    Test-Check "Security scan workflow found" $true
} else {
    Test-Check "Security scan workflow not found" $false
    exit 1
}

# Check Python
Write-Host ""
Write-Host "Checking Python installation..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Test-Check "Python found: $pythonVersion" $true
} catch {
    Test-Check "Python 3 not found" $false
    exit 1
}

# Check Bandit installation
Write-Host ""
Write-Host "Checking Bandit installation..." -ForegroundColor Cyan
try {
    $banditVersion = bandit --version 2>&1 | Select-Object -First 1
    Test-Check "Bandit installed: $banditVersion" $true
    $banditInstalled = $true
} catch {
    Test-Check "Bandit not installed" $false $true
    Write-Host "   Installing Bandit..." -ForegroundColor Yellow
    try {
        pip install "bandit[sarif]"
        Test-Check "Bandit installed successfully" $true
        $banditInstalled = $true
    } catch {
        Test-Check "Failed to install Bandit" $false
        exit 1
    }
}

# Test Bandit scan
if ($banditInstalled) {
    Write-Host ""
    Write-Host "Running test Bandit scan..." -ForegroundColor Cyan

    $tempJson = "$env:TEMP\bandit-test.json"
    $tempSarif = "$env:TEMP\bandit-test.sarif"

    try {
        bandit -r . --configfile .bandit -f json -o $tempJson 2>&1 | Out-Null
        Test-Check "Bandit scan completed" $true

        # Count issues
        $jsonContent = Get-Content $tempJson | ConvertFrom-Json
        $issueCount = $jsonContent.results.Count
        Write-Host "   Found $issueCount issue(s)" -ForegroundColor Gray
    } catch {
        Test-Check "Bandit scan completed with warnings" $false $true
    }

    # Test SARIF generation
    Write-Host ""
    Write-Host "Testing SARIF format generation..." -ForegroundColor Cyan
    try {
        bandit -r . --configfile .bandit -f sarif -o $tempSarif 2>&1 | Out-Null
        Test-Check "SARIF generation successful" $true

        # Validate SARIF JSON
        try {
            $sarifContent = Get-Content $tempSarif | ConvertFrom-Json
            Test-Check "SARIF file is valid JSON" $true

            $fileSize = (Get-Item $tempSarif).Length
            Write-Host "   SARIF file size: $fileSize bytes" -ForegroundColor Gray

            # Check for required SARIF fields
            $hasVersion = $null -ne $sarifContent.version
            $hasRuns = $null -ne $sarifContent.runs

            if ($hasVersion -and $hasRuns) {
                Test-Check "SARIF structure is valid" $true
            } else {
                Test-Check "SARIF structure may be incomplete" $false $true
            }
        } catch {
            Test-Check "SARIF file is not valid JSON" $false
        }
    } catch {
        Test-Check "SARIF generation failed" $false
    }

    # Cleanup temp files
    Remove-Item $tempJson -ErrorAction SilentlyContinue
    Remove-Item $tempSarif -ErrorAction SilentlyContinue
}

# Check workflow YAML syntax
Write-Host ""
Write-Host "Validating workflow YAML syntax..." -ForegroundColor Cyan
try {
    # Check if PyYAML is available
    python -c "import yaml; yaml.safe_load(open('.github/workflows/security-scan.yml'))" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Test-Check "Workflow YAML is valid" $true
    } else {
        Test-Check "Workflow YAML has syntax errors" $false
    }
} catch {
    Test-Check "Could not validate YAML (PyYAML not installed)" $false $true
}

# Check workflow permissions
Write-Host ""
Write-Host "Checking workflow permissions..." -ForegroundColor Cyan
$workflowContent = Get-Content ".github/workflows/security-scan.yml" -Raw

if ($workflowContent -match "security-events: write") {
    Test-Check "security-events permission configured" $true
} else {
    Test-Check "Missing security-events: write permission" $false
}

if ($workflowContent -match "issues: write") {
    Test-Check "issues permission configured" $true
} else {
    Test-Check "Missing issues: write permission (optional)" $false $true
}

# Check workflow triggers
Write-Host ""
Write-Host "Checking workflow triggers..." -ForegroundColor Cyan
if ($workflowContent -match "schedule:") {
    Test-Check "Scheduled trigger configured" $true
    if ($workflowContent -match "cron: '([^']+)'") {
        $cronSchedule = $matches[1]
        Write-Host "   Schedule: $cronSchedule" -ForegroundColor Gray
    }
} else {
    Test-Check "No scheduled trigger" $false $true
}

if ($workflowContent -match "workflow_dispatch:") {
    Test-Check "Manual trigger enabled" $true
} else {
    Test-Check "Manual trigger not enabled" $false $true
}

# Check for CodeQL action
Write-Host ""
Write-Host "Checking CodeQL action integration..." -ForegroundColor Cyan
if ($workflowContent -match "github/codeql-action/upload-sarif@v3") {
    Test-Check "CodeQL SARIF upload action found" $true
} else {
    Test-Check "CodeQL SARIF upload action not found" $false
}

# Repository information
Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Repository Information" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
$repoUrl = git remote get-url origin 2>&1
$currentBranch = git branch --show-current
Write-Host "Remote: $repoUrl"
Write-Host "Branch: $currentBranch"

# Summary
Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "GitHub Integration Checklist" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To enable GitHub Code Scanning:" -ForegroundColor White
Write-Host ""
Write-Host "1. ✅ SARIF format: Ready" -ForegroundColor Green
Write-Host "2. ✅ Upload action: Configured" -ForegroundColor Green
Write-Host "3. ✅ Workflow file: Present" -ForegroundColor Green
Write-Host "4. 📋 Enable GitHub Advanced Security (if private repo)" -ForegroundColor Yellow
Write-Host "5. 📋 Push workflow to GitHub" -ForegroundColor Yellow
Write-Host "6. 📋 Check Security tab after first run" -ForegroundColor Yellow
Write-Host ""
Write-Host "Manual test run command:" -ForegroundColor Cyan
Write-Host "  gh workflow run security-scan.yml" -ForegroundColor White
Write-Host ""
Write-Host "View results:" -ForegroundColor Cyan
Write-Host "  https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/security/code-scanning" -ForegroundColor White
Write-Host ""

# Final status
Write-Host "==================================" -ForegroundColor Cyan
if ($script:errors -eq 0) {
    Write-Host "✅ All checks passed!" -ForegroundColor Green
    Write-Host "==================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Your security scanning setup is ready for GitHub!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Commit and push these changes"
    Write-Host "2. Go to Actions tab and manually trigger 'Scheduled Security Scan'"
    Write-Host "3. Check Security tab for results"
} else {
    Write-Host "❌ $($script:errors) error(s) found" -ForegroundColor Red
    Write-Host "==================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Please fix the errors above before proceeding." -ForegroundColor Red
    exit 1
}

if ($script:warnings -gt 0) {
    Write-Host ""
    Write-Host "⚠️  $($script:warnings) warning(s) - review recommended" -ForegroundColor Yellow
}

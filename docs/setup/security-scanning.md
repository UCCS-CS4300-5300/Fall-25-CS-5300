# Security Scanning Guide

Automated security scanning setup similar to Dependabot for proactive vulnerability detection.

## Overview

This project uses multiple automated security scanning tools:

1. **Bandit** - Static code analysis for Python security issues
2. **Safety** - Dependency vulnerability scanning
3. **GitHub Code Scanning** - Centralized security findings

## How It Works (Like Dependabot)

### Scheduled Scans

**Security Scan Workflow** (`.github/workflows/security-scan.yml`)
- **Schedule:** Every Monday at 9 AM UTC
- **Triggers:**
  - Weekly scheduled runs
  - Manual workflow dispatch
  - Push to main when Python files change
- **Actions:**
  - Scans codebase with Bandit
  - Checks dependencies with Safety
  - Uploads results to GitHub Security tab
  - Creates GitHub issues for critical findings (High severity)

### CI/CD Integration

**Standard CI Pipeline** (`.github/workflows/CI.yml`)
- Runs on every PR and push to main
- Quick security check as part of standard workflow
- Fails PR if critical security issues found
- Uploads SARIF reports to Security tab

## Features Similar to Dependabot

| Feature | Bandit Setup | How It Works |
|---------|-------------|--------------|
| **Scheduled Scans** | ✅ Weekly (Mondays) | Automated cron job |
| **Security Tab Integration** | ✅ SARIF format | Results appear in Security → Code Scanning |
| **Automatic Alerts** | ✅ GitHub Issues | Creates issues for High severity findings |
| **PR Checks** | ✅ CI integration | Blocks PRs with security issues |
| **Report Retention** | ✅ 90 days | Artifacts stored for historical analysis |
| **Manual Triggers** | ✅ workflow_dispatch | Run scans on-demand |

## Viewing Security Findings

### 1. GitHub Security Tab (Recommended)

Navigate to: `https://github.com/UCCS-CS4300-5300/Fall-25-CS-5300/security/code-scanning`

**Features:**
- Centralized view of all security issues
- Filter by severity, confidence, status
- Dismiss false positives
- Track issue resolution
- Historical trends

**Example:**
```
Security → Code Scanning → Filter: "Bandit"
```

### 2. Workflow Artifacts

Download detailed reports from workflow runs:
- `bandit-results.sarif` - SARIF format for tools
- `bandit-report.json` - JSON format for parsing
- `bandit-screen.txt` - Human-readable text
- `safety-report.txt` - Dependency vulnerabilities

### 3. GitHub Issues

Critical findings (High severity) automatically create issues:
- **Title:** "🚨 Bandit Security Scan Alert - X High Severity Issue(s) Found"
- **Labels:** `security`, `automated`, `bandit`
- **Contains:** Issue details, workflow links, recommended actions

## Configuration

### Bandit Configuration (`.bandit`)

Customize Bandit behavior:

```ini
[bandit]
# Exclude directories from scanning
exclude_dirs = [
    '.git',
    'venv',
    'tests',
    'migrations'
]

# Skip specific tests (use with caution)
# skips = ['B201']  # Example: skip flask_debug_true

# Severity threshold (low, medium, high)
# severity = medium

# Confidence threshold (low, medium, high)
# confidence = medium
```

**Common Customizations:**

1. **Skip false positives:**
   ```ini
   skips = ['B101']  # Skip assert_used if intentional
   ```

2. **Adjust thresholds:**
   ```ini
   severity = high    # Only report high severity
   confidence = high  # Only high confidence issues
   ```

3. **Exclude more paths:**
   ```ini
   exclude_dirs = [
       'docs',
       'scripts',
       'Research'
   ]
   ```

### Workflow Configuration

Edit `.github/workflows/security-scan.yml`:

**Change Schedule:**
```yaml
schedule:
  - cron: '0 9 * * 1'  # Monday at 9 AM UTC

# Examples:
# - cron: '0 0 * * *'   # Daily at midnight UTC
# - cron: '0 9 * * 1,4' # Monday and Thursday at 9 AM UTC
# - cron: '0 */6 * * *' # Every 6 hours
```

**Disable Auto-Issue Creation:**
```yaml
# Comment out or remove the "Create GitHub Issue" step
# - name: Create GitHub Issue for Critical Findings
#   if: steps.check_critical.outputs.found_critical == 'true'
```

**Change Severity Threshold:**
```yaml
# In "Run Bandit Scan" step:
--severity-level high    # Only scan for high severity
--confidence-level high  # Only high confidence
```

## Managing Security Findings

### 1. Review Findings

In Security tab:
1. Click on finding for details
2. View code location
3. See severity and confidence
4. Read remediation advice

### 2. Fix Issues

**High Priority:**
- SQL injection (B608)
- Command injection (B602, B603)
- Hardcoded secrets (B105, B106, B107)
- Insecure crypto (B324, B303)

**Medium Priority:**
- Weak hashing (B303)
- Bad file permissions (B103)
- Unsafe deserialization (B301, B302)

**Example Fix:**
```python
# ❌ BAD: Command injection risk
import os
os.system(f"ls {user_input}")

# ✅ GOOD: Use subprocess with list
import subprocess
subprocess.run(["ls", user_input], check=True)
```

### 3. Dismiss False Positives

In Security tab:
1. Open finding
2. Click "Dismiss alert"
3. Select reason:
   - "Won't fix" - Accepted risk
   - "False positive" - Not a real issue
   - "Used in tests" - Test-only code
4. Add comment explaining decision

### 4. Track Progress

**View Open Issues:**
```bash
gh issue list --label security,bandit
```

**Close Resolved Issues:**
- Security findings auto-close when fixed
- Manual issues need manual closing

## Manual Scanning

### Local Scan

Run Bandit locally before committing:

```bash
# Quick scan
bandit -r . --configfile .bandit

# Detailed report
bandit -r . --configfile .bandit -f screen

# JSON output
bandit -r . --configfile .bandit -f json -o report.json

# Only high severity
bandit -r . --configfile .bandit --severity-level high
```

### GitHub Actions Manual Trigger

1. Go to Actions → "Scheduled Security Scan"
2. Click "Run workflow"
3. Select branch
4. Click "Run workflow" button

## Comparison to Dependabot

| Feature | Dependabot | Bandit Setup |
|---------|-----------|-------------|
| **Type** | Dependency updates | Code security scanning |
| **Scope** | `requirements.txt` vulnerabilities | Python code vulnerabilities |
| **Schedule** | Daily (configurable) | Weekly (configurable) |
| **Auto-PRs** | Yes (version updates) | No (creates issues instead) |
| **Security Tab** | Yes | Yes (SARIF integration) |
| **Alerts** | Yes | Yes (GitHub Issues) |
| **Dismiss** | Yes | Yes |

**Using Both:**
- **Dependabot:** Handles dependency updates and known CVEs
- **Bandit:** Finds code-level security issues (injection, secrets, etc.)
- **Safety:** Backup dependency scanner in CI

## Best Practices

### 1. Regular Review

- Check Security tab weekly
- Review auto-created issues promptly
- Keep dismissed findings documented

### 2. Fix Prioritization

**Priority Order:**
1. High severity, High confidence
2. High severity, Medium confidence
3. Medium severity, High confidence
4. Low severity issues (code quality)

### 3. CI Integration

- Never merge PRs with High severity issues
- Document exceptions in PR description
- Require security sign-off for exceptions

### 4. False Positive Management

- Document why issues are dismissed
- Re-review dismissed findings quarterly
- Update `.bandit` config to skip recurring false positives

### 5. Continuous Improvement

- Review Bandit documentation for new checks
- Update configuration as codebase evolves
- Train team on secure coding practices

## Troubleshooting

### Issue: Too Many False Positives

**Solution:** Tune `.bandit` configuration
```ini
# Increase confidence threshold
confidence = high

# Skip specific tests
skips = ['B101', 'B601']
```

### Issue: Scan Takes Too Long

**Solution:** Exclude more directories
```ini
exclude_dirs = [
    'docs',
    'scripts',
    'Research',
    'staticfiles'
]
```

### Issue: SARIF Upload Fails

**Causes:**
- Missing permissions in workflow
- Invalid SARIF format
- GitHub API rate limit

**Solution:**
```yaml
# Ensure permissions are set
permissions:
  security-events: write
  contents: read
```

### Issue: No Issues Created

**Check:**
1. Workflow has `issues: write` permission
2. High severity issues were found
3. No duplicate open issue exists
4. Workflow ran via schedule (not PR)

## Additional Resources

- [Bandit Documentation](https://bandit.readthedocs.io/)
- [GitHub Code Scanning](https://docs.github.com/en/code-security/code-scanning)
- [SARIF Format](https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/sarif-support-for-code-scanning)
- [Django Security Best Practices](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

## Next Steps

1. Enable GitHub Advanced Security (if not already enabled)
2. Configure Dependabot for dependency updates
3. Set up Secret Scanning (GitHub feature)
4. Consider adding CodeQL for additional analysis

---

**Related Documentation:**
- [CI/CD Pipeline](../deployment/ci-cd.md)
- [Testing Guide](testing.md)
- [Contributing Guide](../../CONTRIBUTING.md)

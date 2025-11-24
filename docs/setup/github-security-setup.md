# GitHub Security Setup Checklist

Complete guide to enabling and verifying Bandit security scanning integration with GitHub.

## Pre-Deployment Checklist

### 1. Local Verification

Run the verification script to ensure everything is configured correctly:

**Windows (PowerShell):**
```powershell
.\scripts\test-security-scan.ps1
```

**Linux/Mac (Bash):**
```bash
chmod +x scripts/test-security-scan.sh
./scripts/test-security-scan.sh
```

**Expected Output:**
- ✅ All checks passed!
- SARIF file generation successful
- Workflow YAML is valid
- All required permissions configured

### 2. Commit and Push Changes

```bash
git add .
git commit -m "feat: Add Bandit security scanning with GitHub integration

- Add scheduled security scan workflow (Dependabot-style)
- Configure SARIF upload to GitHub Security tab
- Add Bandit configuration file
- Add verification scripts for setup validation
- Update README with workflow badges
- Add comprehensive security scanning documentation"

git push origin your-branch-name
```

## GitHub Repository Setup

### 3. Enable GitHub Security Features

#### For Public Repositories
Security features are **automatically enabled** ✅

#### For Private Repositories
1. Go to repository **Settings**
2. Navigate to **Security** → **Code security and analysis**
3. Enable the following:
   - ✅ **Dependency graph** (should be on by default)
   - ✅ **Dependabot alerts** (recommended)
   - ✅ **Dependabot security updates** (recommended)
   - ✅ **Code scanning** → Click "Set up" → Choose "Default"
   - ✅ **Secret scanning** (if available)

**Note:** Some features require GitHub Advanced Security (paid for private repos on personal accounts, free for public repos and GitHub Enterprise).

### 4. Configure Workflow Permissions

#### Option A: Repository Settings (Recommended)
1. Go to **Settings** → **Actions** → **General**
2. Scroll to **Workflow permissions**
3. Select: **"Read and write permissions"**
4. Check: ☑️ **"Allow GitHub Actions to create and approve pull requests"**
5. Click **Save**

#### Option B: Organization Settings (If applicable)
1. Go to Organization **Settings** → **Actions** → **General**
2. Set workflow permissions for the organization
3. Allow individual repositories to override if needed

### 5. Verify Workflow File Permissions

The workflow file already includes required permissions:

```yaml
permissions:
  contents: read           # Read repository contents
  security-events: write   # Upload to Security tab ✅ REQUIRED
  issues: write           # Create issues for findings
  actions: read           # Check workflow status
```

## Post-Deployment Verification

### 6. Manual Test Run

Trigger the workflow manually to verify it works:

**Using GitHub Web UI:**
1. Go to **Actions** tab
2. Click **"Scheduled Security Scan"** workflow
3. Click **"Run workflow"** button
4. Select branch (usually `main`)
5. Click **"Run workflow"**

**Using GitHub CLI:**
```bash
gh workflow run security-scan.yml --ref main
```

**Check Status:**
```bash
gh run list --workflow=security-scan.yml --limit 5
```

### 7. Verify SARIF Upload

After the workflow completes:

1. Go to **Security** tab
2. Click **Code scanning** in left sidebar
3. Look for **"Bandit"** in the tool filter
4. You should see findings (if any) or "No alerts" message

**Expected Results:**
- ✅ Workflow completes successfully (green checkmark)
- ✅ SARIF file uploaded to Security tab
- ✅ Findings appear in Code Scanning (if issues exist)
- ✅ Workflow summary shows scan results

### 8. Check Auto-Generated Issues

If high-severity issues are found during scheduled runs:

1. Go to **Issues** tab
2. Filter by label: `security`, `automated`, `bandit`
3. Verify issue was created with:
   - Clear title: "🚨 Bandit Security Scan Alert - X High Severity Issue(s) Found"
   - Detailed findings
   - Links to workflow run
   - Remediation guidance

## Troubleshooting

### Issue: SARIF Upload Fails

**Error:** `Error: Advanced Security must be enabled for this repository`

**Solution for Private Repos:**
1. Enable GitHub Advanced Security (requires paid plan)
2. Or make repository public
3. Or disable SARIF upload (less recommended):
   ```yaml
   # Comment out in .github/workflows/security-scan.yml
   # - name: Upload SARIF to GitHub Security
   ```

**Error:** `Error: Resource not accessible by integration`

**Solution:**
1. Check workflow permissions in Settings → Actions → General
2. Ensure `security-events: write` is in workflow file
3. Verify branch protection rules don't block workflow

### Issue: Workflow Doesn't Trigger

**Scheduled trigger not working:**
- First scheduled run happens AFTER the workflow is merged to default branch
- Check if Actions are enabled: Settings → Actions → General
- Verify cron syntax is correct

**Manual trigger not visible:**
- Workflow must be on default branch (usually `main`)
- Push workflow file first, then refresh Actions page
- Check `workflow_dispatch:` is present in workflow file

### Issue: No Findings Appear in Security Tab

**Check:**
1. Workflow completed successfully? (Actions tab)
2. SARIF upload step succeeded? (Check workflow logs)
3. Viewing correct branch/tool filter?
4. File size > 0? (Empty SARIF = no issues found)

**Debug:**
```bash
# Download workflow artifacts
gh run download <run-id> -n bandit-security-reports

# Check SARIF content
cat bandit-results.sarif | python -m json.tool
```

### Issue: Too Many False Positives

**Solution:** Configure `.bandit` file

```ini
[bandit]
# Increase severity threshold
severity = high

# Skip specific tests
skips = ['B101', 'B201']

# Exclude more directories
exclude_dirs = [
    'tests',
    'migrations',
    'docs',
    'scripts'
]
```

## Scheduled Scan Behavior

### Default Schedule
- **Frequency:** Every Monday at 9 AM UTC
- **Cron:** `0 9 * * 1`

### When It Runs
- **First run:** Next scheduled time AFTER merge to main
- **Subsequent runs:** Weekly on schedule
- **Manual runs:** Anytime via Actions tab

### What Happens on Each Run

1. **Checkout Code** - Gets latest code from main branch
2. **Install Bandit** - Installs latest Bandit with SARIF support
3. **Run Scan** - Scans entire codebase (excluding configured paths)
4. **Generate Reports** - Creates SARIF, JSON, and text reports
5. **Upload to Security Tab** - Uploads SARIF to GitHub Code Scanning
6. **Check Severity** - Counts high-severity issues
7. **Create Issue** - If high-severity found, creates GitHub issue (scheduled runs only)
8. **Archive Reports** - Saves artifacts for 90 days

## Monitoring and Maintenance

### Weekly Tasks
- [ ] Review Security tab for new findings
- [ ] Triage auto-generated issues
- [ ] Dismiss false positives with explanations
- [ ] Track fix progress

### Monthly Tasks
- [ ] Review dismissed findings (ensure still valid)
- [ ] Update `.bandit` configuration if needed
- [ ] Check for Bandit updates
- [ ] Review workflow artifact retention

### Quarterly Tasks
- [ ] Audit security issue resolution time
- [ ] Review and update documentation
- [ ] Train team on new security patterns
- [ ] Evaluate need for additional security tools

## Integration with Development Workflow

### Pull Request Process

1. **Developer creates PR**
2. **CI runs security scan** (from CI.yml)
3. **Findings appear in PR checks**
4. **High severity issues block merge** (recommended)
5. **Developer fixes or dismisses findings**
6. **Re-run checks**
7. **Merge when green**

### Security Review Process

1. **Weekly scan runs Monday morning**
2. **If high severity found:**
   - GitHub issue created automatically
   - Tagged with `security`, `automated`, `bandit`
   - Assigned to security team (configure in workflow)
3. **Team triages within 48 hours**
4. **Prioritize by severity × confidence**
5. **Track fix progress in issue**
6. **Close issue when resolved**

## Customization Options

### Change Schedule

Edit `.github/workflows/security-scan.yml`:

```yaml
schedule:
  # Daily at midnight UTC
  - cron: '0 0 * * *'

  # Twice weekly (Monday and Thursday)
  - cron: '0 9 * * 1,4'

  # First day of month
  - cron: '0 9 1 * *'
```

### Adjust Severity Threshold

In workflow file:

```yaml
# Scan only high severity
--severity-level high
--confidence-level high

# Scan all levels
--severity-level low
--confidence-level low
```

### Disable Auto-Issue Creation

Comment out in workflow:

```yaml
# - name: Create GitHub Issue for Critical Findings
#   if: steps.check_critical.outputs.found_critical == 'true'
#   ...
```

### Add Email Notifications

Add notification step:

```yaml
- name: Send Email Notification
  if: steps.check_critical.outputs.found_critical == 'true'
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.gmail.com
    server_port: 465
    username: ${{ secrets.EMAIL_USERNAME }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    subject: Security Alert - High Severity Issues Found
    to: security-team@example.com
    from: github-actions@example.com
    body: Check ${{ github.server_url }}/${{ github.repository }}/security/code-scanning
```

## Best Practices

### 1. Never Commit These Files
```
.env
*.key
*.pem
credentials.json
secrets.yaml
```

### 2. Use GitHub Secrets
Store sensitive data in:
- Settings → Secrets and variables → Actions
- Reference as: `${{ secrets.SECRET_NAME }}`

### 3. Regularly Update Dependencies
```bash
pip install --upgrade bandit
```

### 4. Document Dismissals
When dismissing findings in Security tab:
- Always add comment explaining why
- Link to related documentation
- Set reminder to re-review

### 5. Track Metrics
Monitor over time:
- Total findings count
- High severity count
- Time to resolve
- False positive rate

## Success Criteria

✅ **Setup Complete When:**
1. Workflow runs successfully on schedule
2. Findings appear in Security tab
3. High-severity issues create GitHub issues
4. Team receives notifications
5. PR checks include security scan
6. Documentation is up-to-date

## Support and Resources

**Internal Documentation:**
- [Security Scanning Guide](security-scanning.md)
- [Bandit Quick Reference](bandit-quick-reference.md)
- [CI/CD Pipeline](../deployment/ci-cd.md)

**External Resources:**
- [GitHub Code Scanning Docs](https://docs.github.com/en/code-security/code-scanning)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [SARIF Format Spec](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html)
- [GitHub Actions Security](https://docs.github.com/en/actions/security-guides)

## Quick Commands Reference

```bash
# Test setup locally
.\scripts\test-security-scan.ps1  # Windows
./scripts/test-security-scan.sh   # Linux/Mac

# Manual workflow trigger
gh workflow run security-scan.yml

# View recent runs
gh run list --workflow=security-scan.yml

# View workflow logs
gh run view <run-id> --log

# Download artifacts
gh run download <run-id>

# View security alerts
gh api repos/:owner/:repo/code-scanning/alerts

# List open security issues
gh issue list --label security,bandit
```

---

**Last Updated:** 2025-01-17
**Maintained By:** Development Team
**Questions?** Open an issue or contact the security team

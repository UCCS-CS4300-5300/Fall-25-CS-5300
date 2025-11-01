# AGENTS.md

This file provides operational guidance to AI coding assistants (Claude Code, GitHub Copilot, etc.) when working with this repository.

## Project Overview

**Active Interview Service** - AI-powered interview practice platform built with Django and OpenAI GPT-4o.

**For detailed project information, see:**
- [README.md](README.md) - Project overview and quick start
- [Architecture Overview](docs/architecture/overview.md) - System design
- [Local Development Guide](docs/setup/local-development.md) - Setup instructions

---

## Core Principles for AI Agents

### 1. Task Completion Standards

**Always verify your work before reporting completion:**
- ✅ Run tests after making code changes
- ✅ Check linting before finalizing changes
- ✅ Verify coverage meets 80% threshold
- ✅ If you encounter errors, debug them - don't just report failure
- ✅ Provide specific file paths and line numbers in your final report

### 2. Code Quality Requirements

**Maintain project standards:**
- **80% test coverage** - Write tests for new functionality
- **flake8 compliance** - Python code style
- **djlint compliance** - Django template style
- **Match existing patterns** - Follow established code style in the codebase

### 3. Testing Workflow

When making code changes:
1. Make your changes
2. Run relevant tests: `cd active_interview_backend && python manage.py test`
3. Check coverage: `coverage run manage.py test && coverage report -m`
4. Run linting: `flake8 --config .flake8 .`
5. Fix any failures before reporting completion

**See:** [Testing Guide](docs/setup/testing.md) for detailed testing instructions.

---

## Documentation Maintenance

### When to Update Documentation

Update documentation **immediately** when you:
- ✅ Add a new feature
- ✅ Change existing behavior or API
- ✅ Add/modify models or database schema
- ✅ Change setup or deployment process
- ✅ Modify environment variables or configuration
- ✅ Add new dependencies

### What to Update

**Feature Changes:**
```
1. Update relevant docs/features/*.md if feature-specific
2. Update docs/architecture/models.md if models changed
3. Update docs/architecture/api.md if API changed
4. Update docs/architecture/overview.md if architecture changed
```

**Setup Changes:**
```
1. Update docs/setup/local-development.md if setup process changed
2. Update docs/deployment/*.md if deployment changed
3. Update requirements.txt if dependencies changed
```

**Always check and update:**
- README.md - If it affects quick start or overview
- CONTRIBUTING.md - If it affects contributor workflow

### Documentation Standards

**When writing/updating docs:**
- Use clear, concise language
- Include code examples
- Add links to related documentation
- Keep formatting consistent (Markdown)
- Test code examples before committing
- Use relative links for internal docs

**Example:**
```markdown
## New Feature: Export Reports

Users can now export interview reports as PDFs.

**Usage:**
1. Complete an interview
2. Navigate to results page
3. Click "Generate Report"
4. Download PDF

**Technical Details:**
See [Exportable Reports Documentation](docs/features/exportable-reports.md)
for implementation details.

**API Endpoints:**
- `POST /chat/<id>/generate-report/` - Generate report
- `GET /chat/<id>/download-pdf/` - Download PDF

See [API Reference](docs/architecture/api.md#report-endpoints) for details.
```

### Documentation File Locations

```
docs/
├── setup/
│   ├── local-development.md   # Setup instructions
│   ├── testing.md            # Testing guide
│   └── troubleshooting.md    # Common issues
│
├── deployment/
│   ├── railway.md            # Railway deployment
│   └── ci-cd.md             # CI/CD pipeline
│
├── architecture/
│   ├── overview.md          # System architecture
│   ├── models.md           # Database models
│   └── api.md              # REST API reference
│
└── features/
    └── *.md                # Feature-specific docs
```

### What NOT to Create

**Never create these without explicit user request:**
- ❌ `*_SUMMARY.md` files
- ❌ `*_FIXES.md` files
- ❌ `*_COMPLETE.md` files
- ❌ `QUICK_*_GUIDE.md` files
- ❌ Files in `Claude_Reports/` directory
- ❌ Duplicate README files in subdirectories

**These belong in PR descriptions, not committed to the repo.**

---

## Project Structure Quick Reference

```
active_interview_backend/
├── active_interview_app/
│   ├── models.py          # Database models
│   ├── views.py          # View logic (~900 lines)
│   ├── urls.py           # URL patterns
│   ├── forms.py          # Django forms
│   ├── serializers.py    # DRF serializers
│   ├── templates/        # HTML templates
│   └── tests/            # Test suite
├── features/             # BDD feature files (Gherkin only)
└── manage.py            # Django CLI
```

**For detailed structure:** See [Architecture Overview](docs/architecture/overview.md)

---

## Key Technology References

### Models
- User (Django built-in)
- UploadedResume
- UploadedJobListing
- Chat (interview sessions)
- ExportableReport

**Full reference:** [Models Documentation](docs/architecture/models.md)

### OpenAI Integration
- Model: GPT-4o
- Max tokens: 15,000
- Client initialized at module level in `views.py`
- System prompts generated dynamically

**Details:** [Architecture Overview - OpenAI Integration](docs/architecture/overview.md#openai-integration)

### Database
- Development: SQLite
- Production: PostgreSQL (Railway)

**Schema:** [Models Documentation](docs/architecture/models.md)

---

## Common Task Patterns

### Adding New Features

1. **Request GitHub issue information from user:**
   - Ask: "Is there a GitHub issue for this feature? If so, what is the issue number?"
   - Ask: "Are there user stories or Gherkin scenarios in the issue?"
   - Ask: "Are there related sub-issues or dependencies?"
   - Review the issue(s) to understand requirements and acceptance criteria
   - Use `gh issue view <number>` to fetch issue details if needed

2. **Create or update BDD feature file:**
   - Check for existing `.feature` file in `active_interview_backend/features/`
   - If exists: Update with new scenarios from GitHub issue
   - If not exists: Create new `.feature` file
   - Extract user stories, acceptance criteria, and scenarios from the GitHub issue
   - Tag scenarios with issue number (e.g., `@issue-123`)
   - **See:** [BDD Feature Files Guide](docs/setup/bdd-feature-files.md) for detailed instructions

3. **Review architecture:**
   - [Architecture Overview](docs/architecture/overview.md)
   - [Models Reference](docs/architecture/models.md) if database changes needed

4. **Identify files to change:**
   - Models (`models.py`) if data storage needed
   - Views (`views.py`) for logic
   - Forms (`forms.py`) for user input
   - Templates (`templates/`) for UI
   - URLs (`urls.py`) for routing

5. **Write tests** in `tests/` directory
   - Implement Gherkin scenarios as tests if provided
   - Ensure tests cover acceptance criteria from issue

6. **Run migrations** if models changed: `python manage.py makemigrations && python manage.py migrate`

7. **Update documentation:**
   - Create `docs/features/your-feature.md` if substantial
   - Update `docs/architecture/models.md` if models changed
   - Update `docs/architecture/api.md` if API changed
   - Reference the GitHub issue number in documentation

8. **Verify with tests and linting**

9. **Report:**
   - What was added
   - Files changed with line numbers
   - Test results
   - Which GitHub issue(s) this addresses
   - Whether acceptance criteria were met

### Bug Fixing

1. Reproduce the bug
2. Identify root cause (use grep/read tools)
3. Fix the issue
4. **Add test case** to prevent regression
5. Verify fix with full test suite
6. **Update docs if behavior changed**
7. Report: what was broken, what you changed, which test proves it's fixed

### Refactoring

1. Understand current implementation thoroughly
2. **Write tests for current behavior** if coverage is lacking
3. Make incremental changes
4. Run tests after each change
5. Ensure no functionality is lost
6. **Update documentation if public interfaces changed**
7. Report: what you refactored, why, and test results

---

## Search and Analysis Guidance

### When to Use Task Tool

Use the Task tool with `subagent_type=Explore` when:
- ❌ Question is open-ended (e.g., "how are errors handled?")
- ❌ Need to explore multiple files
- ❌ Looking for patterns across codebase
- ❌ Understanding architecture or flow

**Don't use Task tool when:**
- ✅ Searching for specific file path (use Glob)
- ✅ Searching for specific class/function (use Glob)
- ✅ Searching within 2-3 known files (use Read)

### File Discovery

**For specific targets:**
```bash
# Find specific file
Glob: "**/*models.py"

# Find specific class
Glob: "**/*views.py" then Read to find class
```

**For exploration:**
```bash
# Use Task tool
Task(subagent_type="Explore", prompt="How are API endpoints structured?")
```

---

## Environment and Configuration

### Environment Variables Required

**Development:**
- `PROD=false`
- `DJANGO_SECRET_KEY=<generated-key>`
- `OPENAI_API_KEY=<your-key>`

**Production:**
- `PROD=true`
- `DJANGO_SECRET_KEY=<secure-key>`
- `OPENAI_API_KEY=<your-key>`
- `DATABASE_URL=<postgresql-url>` (auto-provided by Railway)

**See:** [Local Development Guide](docs/setup/local-development.md) for setup details.

---

## Reporting Results

Your final report should include:

### Good Report Template

```markdown
## Summary
[2-3 sentence overview of what was accomplished]

## GitHub Issues
- Closes #123
- Addresses #456 (partial implementation)
- Related to #789

## Acceptance Criteria Met
- [x] User can export reports as PDF
- [x] Reports include performance scores
- [ ] Email delivery (deferred to future issue)

## Files Changed
- `path/to/file.py:123` - [Brief description of change]
- `path/to/other.py:456` - [Brief description of change]

## Documentation Updated
- `docs/architecture/models.md` - Added new model documentation
- `docs/features/new-feature.md` - Created feature documentation

## Tests
- All tests passed: [X tests]
- Coverage: [X%] (requirement: ≥80%)
- Linting: No errors

## Verification
[How you verified the changes work]

## Notes
[Any important context or next steps]
```

### Poor Report Example ❌

```
I made some changes to the views file and added stuff.
It might work but I'm not sure. There were some errors
but I tried to fix them.
```

---

## Error Handling

If you encounter errors:

1. **Test failures:** Read full traceback, identify failing assertion, fix root cause
2. **Import errors:** Check requirements.txt, verify file structure
3. **Migration errors:** Check for conflicts, try `--merge` if needed
4. **Docker errors:** Check logs with `docker logs django`, verify .env exists
5. **Coverage failures:** Write tests for uncovered code, check `.coveragerc`

**See:** [Troubleshooting Guide](docs/setup/troubleshooting.md) for detailed solutions.

---

## Key Commands Reference

### Django Management

```bash
cd active_interview_backend

# Database
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# Testing
python manage.py test
coverage run manage.py test
coverage report -m

# Development server
python manage.py runserver

# Static files (if CSS/images changed)
rm -Rf staticfiles
python manage.py collectstatic --noinput
```

### Docker

```bash
# Development mode
docker-compose up -d --build

# Production testing
docker-compose -f docker-compose.prod.yml up -d --build

# Execute in container
docker exec django python manage.py test

# View logs
docker logs django

# Cleanup
docker-compose down --volumes --remove-orphans
```

### GitHub CLI (Issue Management)

```bash
# View issue details
gh issue view <issue-number>

# List issues
gh issue list

# View issue in browser
gh issue view <issue-number> --web

# Get issue body (for parsing user stories/scenarios)
gh issue view <issue-number> --json body --jq .body

# List related issues (by label, milestone, etc.)
gh issue list --label "feature" --milestone "Sprint-1"
```

**Full reference:** [Local Development Guide](docs/setup/local-development.md)

---

## CI/CD Pipeline

### Pipeline Jobs

1. **Lint** - flake8, djlint
2. **Security** - safety, bandit
3. **Test** - Django tests with 80% coverage requirement
4. **AI Review** - OpenAI code review (parallel)
5. **Cleanup** - Archive reports

**Deployment** - Railway (on push to `main`)

**See:** [CI/CD Documentation](docs/deployment/ci-cd.md) for details.

---

## Getting Unstuck

If you're stuck:

1. Review this file for architecture overview
2. Check [Documentation](docs/) for detailed guidance
3. Search for similar existing functionality (grep/read)
4. Look at test files to understand expected behavior
5. Use Glob to find relevant files
6. Read full context of files, not just snippets

---

## Summary

**This file provides operational guidance. For detailed technical information:**

- 📖 [Complete Documentation](docs/)
- 🏗️ [Architecture Overview](docs/architecture/overview.md)
- 🧪 [Testing Guide](docs/setup/testing.md)
- 🚀 [Deployment Docs](docs/deployment/)
- 🤝 [Contributing Guide](CONTRIBUTING.md)

**Key Principles:**
1. Always verify your work (tests, linting, coverage)
2. Update documentation when making changes
3. Follow existing patterns
4. Report results with specific details
5. Debug errors, don't just report them

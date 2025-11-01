# Contributing to Active Interview Service

Thank you for your interest in contributing! This document provides guidelines and best practices for contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Commit Guidelines](#commit-guidelines)
- [Documentation](#documentation)

---

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Git
- Docker (optional, recommended)
- OpenAI API key (for AI features)

### Setup

1. **Fork the repository** on GitHub
2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Fall-25-CS-5300.git
   cd Fall-25-CS-5300
   ```

3. **Set up development environment:**

   See [Local Development Guide](docs/setup/local-development.md) for detailed instructions.

   **Quick start:**
   ```bash
   python3 -m venv myenv
   source myenv/bin/activate  # Windows: .\myenv\Scripts\activate
   cd active_interview_backend
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   export PROD=false
   export DJANGO_SECRET_KEY='your-secret-key'
   export OPENAI_API_KEY='your-api-key'
   ```

5. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Verify setup:**
   ```bash
   python manage.py runserver
   # Visit http://127.0.0.1:8000
   ```

---

## Development Workflow

### Creating a Feature Branch

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
```

**Branch naming conventions:**
- `feature/` - New features (e.g., `feature/export-reports`)
- `fix/` - Bug fixes (e.g., `fix/login-redirect`)
- `docs/` - Documentation updates (e.g., `docs/api-reference`)
- `refactor/` - Code refactoring (e.g., `refactor/views-cleanup`)
- `test/` - Test additions (e.g., `test/chat-coverage`)

### Making Changes

1. **Write code** following our [code standards](#code-standards)
2. **Write tests** for new functionality
3. **Run tests** to ensure they pass
4. **Check coverage** (must be ≥ 80%)
5. **Run linters** to catch style issues

---

## Code Standards

### Python Code (flake8)

We use flake8 for Python linting with PEP 8 standards.

**Run linter:**
```bash
cd active_interview_backend
flake8 --config .flake8 .
```

**Key rules:**
- Max line length: 100 characters
- Use 4 spaces for indentation (no tabs)
- Follow PEP 8 naming conventions
- Add docstrings to functions and classes
- No wildcard imports (`from x import *`)

### Django Templates (djlint)

We use djlint for Django template linting.

**Run linter:**
```bash
cd active_interview_backend
djlint --configuration djlint.toml active_interview_app/templates/ --lint
```

**Key rules:**
- Proper template tag formatting
- Consistent indentation
- No deprecated template tags

### General Guidelines

**Code organization:**
- Keep functions focused and small
- Avoid deep nesting (max 3-4 levels)
- Use meaningful variable names
- Comment complex logic

**Django-specific:**
- Use class-based views where appropriate
- Follow Django's model-view-template pattern
- Use Django's built-in features (auth, admin, forms)
- Avoid raw SQL (use ORM)

**Security:**
- Never commit secrets or API keys
- Validate user input
- Use Django's CSRF protection
- Follow OWASP best practices

---

## Testing Requirements

### Minimum Coverage: 80%

All contributions must maintain **at least 80% code coverage**.

### Running Tests

```bash
cd active_interview_backend

# Run all tests
python manage.py test

# Run with coverage
coverage run manage.py test
coverage report -m

# Generate HTML report
coverage html
open htmlcov/index.html
```

### Writing Tests

**Test file location:**
- Place tests in `active_interview_backend/active_interview_app/tests/`
- Name test files `test_*.py`
- Organize by feature or module

**Test structure:**
```python
from django.test import TestCase, Client
from django.contrib.auth.models import User

class MyFeatureTest(TestCase):
    def setUp(self):
        """Run before each test method"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_something_works(self):
        """Test description"""
        # Arrange
        self.client.login(username='testuser', password='testpass123')

        # Act
        response = self.client.get('/some-url/')

        # Assert
        self.assertEqual(response.status_code, 200)
```

**What to test:**
- All new functions and methods
- Edge cases and error conditions
- Authentication and permissions
- Form validation
- API endpoints

**See:** [Testing Guide](docs/setup/testing.md) for detailed testing documentation.

---

## Pull Request Process

### Before Submitting

**Checklist:**
- [ ] Code follows style guidelines (flake8, djlint pass)
- [ ] Tests are written and pass
- [ ] Coverage is ≥ 80%
- [ ] Documentation is updated (if needed)
- [ ] Commit messages follow guidelines
- [ ] Branch is up to date with main

### Creating a Pull Request

1. **Push your branch:**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Open PR on GitHub:**
   - Go to the repository on GitHub
   - Click "Pull requests" → "New pull request"
   - Select your branch
   - Fill out the PR template

3. **PR Title Format:**
   ```
   [Type] Brief description
   ```

   **Examples:**
   - `[Feature] Add exportable PDF reports`
   - `[Fix] Resolve chat deletion cascade bug`
   - `[Docs] Update API reference`
   - `[Test] Increase model coverage`

4. **PR Description:**

   Include:
   - **Summary:** What does this PR do?
   - **Motivation:** Why is this change needed?
   - **Changes:** List of key changes
   - **Testing:** How was this tested?
   - **Screenshots:** (if UI changes)
   - **Related Issues:** Closes #123

### Review Process

1. **Automated checks** will run (CI pipeline)
   - Linting
   - Security scans
   - Tests
   - Coverage validation

2. **Code review** by maintainers
   - Feedback will be provided
   - Address requested changes

3. **Approval and merge**
   - Once approved, maintainers will merge
   - Branch will be deleted automatically

### CI Requirements

All of these must pass:
- ✅ Linting (flake8, djlint)
- ✅ Security scans (safety, bandit)
- ✅ Tests (all pass)
- ✅ Coverage ≥ 80%

---

## Commit Guidelines

### Commit Message Format

```
[Type] Brief description (50 chars or less)

Longer explanation if needed (wrap at 72 characters).
Explain what and why, not how.

- Bullet points are okay
- Use present tense ("Add feature" not "Added feature")
- Reference issues: Closes #123, Relates to #456
```

### Commit Types

- `[Feature]` - New feature
- `[Fix]` - Bug fix
- `[Docs]` - Documentation only
- `[Test]` - Test additions/fixes
- `[Refactor]` - Code refactoring (no behavior change)
- `[Style]` - Code style changes (formatting)
- `[Chore]` - Maintenance tasks (dependencies, config)

### Examples

**Good:**
```
[Feature] Add PDF export for interview reports

Implements ExportableReport model and pdf_export.py
using ReportLab. Adds three new views for report
generation, viewing, and downloading.

Closes #45
```

**Bad:**
```
updated stuff
```

---

## Documentation

### When to Update Docs

Update documentation when you:
- Add a new feature
- Change existing behavior
- Add new API endpoints
- Modify setup/deployment process

### Documentation Structure

```
docs/
├── setup/          # Setup and development guides
├── deployment/     # Deployment and CI/CD docs
├── architecture/   # System architecture docs
└── features/       # Feature-specific documentation
```

### Writing Documentation

**Guidelines:**
- Use clear, concise language
- Include code examples
- Add links to related docs
- Keep formatting consistent (Markdown)
- Test examples before committing

**See existing docs for examples:**
- [Testing Guide](docs/setup/testing.md)
- [API Reference](docs/architecture/api.md)

---

## Additional Guidelines

### Issue Reporting

**Before creating an issue:**
1. Search existing issues
2. Check [Troubleshooting Guide](docs/setup/troubleshooting.md)
3. Verify it's not a local environment issue

**When creating an issue:**
- Use a clear, descriptive title
- Provide steps to reproduce
- Include error messages
- Specify environment details (OS, Python version)
- Add screenshots if relevant

### Feature Requests

**Include:**
- Use case and motivation
- Expected behavior
- Proposed implementation (optional)
- Willingness to contribute

### Getting Help

- 📖 **Documentation:** [docs/](docs/)
- 💬 **Discussions:** GitHub Discussions
- 🐛 **Issues:** GitHub Issues
- 📧 **Email:** [Your contact info]

---

## Code of Conduct

### Our Standards

- Be respectful and professional
- Welcome newcomers
- Accept constructive criticism
- Focus on what's best for the project

### Not Acceptable

- Harassment or discrimination
- Trolling or insulting comments
- Publishing others' private information
- Unprofessional conduct

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

## Questions?

If you have questions about contributing:
1. Check this guide and [documentation](docs/)
2. Search existing issues/discussions
3. Ask in GitHub Discussions
4. Create an issue if needed

**Thank you for contributing!** 🎉

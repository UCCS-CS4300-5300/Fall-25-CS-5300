# Testing Guide

This guide covers how to run tests, check coverage, and understand the testing infrastructure.

## Quick Start

### Run All Tests

```bash
cd active_interview_backend
python manage.py test
```

### Run Tests with Coverage

**Windows:**
```batch
cd active_interview_backend
python -m coverage run manage.py test
python -m coverage report -m
python -m coverage html
```

**Linux/Mac:**
```bash
cd active_interview_backend
coverage run manage.py test
coverage report -m
coverage html
```

### View Coverage Report

Open the HTML report in your browser:

```bash
# Windows
start htmlcov/index.html

# Mac
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html
```

---

## Test Structure

### Test Files Location

All tests are in `active_interview_backend/active_interview_app/tests/`:

```
tests/
├── __init__.py
├── test.py                              # Basic authentication tests
├── test_chat.py                         # Chat functionality (481 lines)
├── test_models.py                       # Model tests (261 lines)
├── test_forms.py                        # Form validation (303 lines)
├── test_serializers.py                  # API serializers (252 lines)
├── test_views_coverage.py               # View coverage (474 lines)
├── test_views_extended.py               # Extended views (480 lines)
├── test_views_comprehensive.py          # Comprehensive views (550 lines)
├── test_additional_views.py             # Additional views (475 lines)
├── test_upload.py                       # File uploads (458 lines)
├── test_registration.py                 # User registration (140 lines)
├── test_token_tracking.py               # Token usage tracking (520 lines)
├── test_exportable_report.py            # Report generation (369 lines)
└── test_e2e.py                          # Selenium E2E tests (156 lines)
```

### What Each Test Suite Covers

| Test File | Coverage Area | Key Tests |
|-----------|---------------|-----------|
| **test_models.py** | Django models | Field validation, defaults, relationships, JSON fields |
| **test_forms.py** | Form validation | Required fields, custom validation, user-specific querysets |
| **test_serializers.py** | REST API | Serialization, deserialization, CRUD operations |
| **test_views_*.py** | Views | Authentication, permissions, GET/POST handling, OpenAI mocking |
| **test_upload.py** | File uploads | PDF/DOCX processing, validation, error handling |
| **test_chat.py** | Chat system | Interview sessions, OpenAI integration, message handling |
| **test_token_tracking.py** | Token tracking | Cost calculations, branch aggregations, cumulative stats |
| **test_exportable_report.py** | PDF reports | Report generation, PDF export, scoring |
| **test_e2e.py** | End-to-end | Selenium browser tests, full user workflows |

---

## Running Specific Tests

### Run a Specific Test File

```bash
cd active_interview_backend
python manage.py test active_interview_app.tests.test_models
```

### Run a Specific Test Class

```bash
python manage.py test active_interview_app.tests.test_models.ChatModelTest
```

### Run a Specific Test Method

```bash
python manage.py test active_interview_app.tests.test_models.ChatModelTest.test_create_chat
```

### Run with Verbosity

```bash
# Show test names as they run
python manage.py test -v 2

# Show even more detail
python manage.py test -v 3
```

---

## Coverage Requirements

### Minimum Coverage: 80%

The CI pipeline enforces **minimum 80% code coverage**.

### Coverage Configuration

Coverage is configured in `active_interview_backend/.coveragerc`:

**Excluded from coverage:**
- Test files (`*/tests/*`)
- Migrations (`*/migrations/*`)
- Init files (`*/__init__.py`)
- Management scripts (`manage.py`)

### Check Coverage Threshold

```bash
cd active_interview_backend
coverage run manage.py test
coverage report -m

# Check if meets 80% (Linux/Mac/Git Bash)
bash ../scripts/check-coverage.sh coverage_report.txt
```

---

## Test Data and Mocking

### Django Test Database

Tests automatically use a separate test database that:
- Is created before tests run
- Is destroyed after tests complete
- Never affects your development database

### Mocking External Services

Tests use `@patch` to mock external dependencies:

**OpenAI API:**
```python
@patch('active_interview_app.views.get_openai_client')
def test_chat_with_ai(self, mock_client):
    mock_client.return_value = MagicMock()
    # Test code here
```

**File Processing:**
```python
@patch('pymupdf4llm.to_markdown')
def test_pdf_upload(self, mock_pdf):
    mock_pdf.return_value = "Test resume content"
    # Test code here
```

---

## Coverage Report Interpretation

### Reading the Console Report

```
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
active_interview_app/views.py           450     50    89%
active_interview_app/models.py          120     10    92%
-----------------------------------------------------------
TOTAL                                   2000    150    92%
```

- **Stmts**: Total lines of code
- **Miss**: Lines not covered by tests
- **Cover**: Percentage covered

### HTML Report Features

The HTML report (`htmlcov/index.html`) shows:
- ✅ **Green lines**: Covered by tests
- ❌ **Red lines**: Not covered
- **Yellow lines**: Partially covered (branches)

Click on any file to see line-by-line coverage.

---

## BDD/Feature Tests

### Feature Files

Gherkin feature files are in `active_interview_backend/features/`:

```bash
features/
├── authentication.feature
├── chat_management.feature
├── interview_session.feature
└── document_upload.feature
```

**For creating/updating feature files from GitHub issues:**

See [BDD Feature Files Guide](bdd-feature-files.md) for comprehensive instructions on:
- Creating feature files from GitHub issues
- Gherkin syntax reference
- Best practices
- Step definitions

### Running BDD Tests

**With Behave:**
```bash
cd active_interview_backend
pip install behave
behave

# Run specific feature
behave features/authentication.feature

# Run scenarios with specific tag
behave --tags=issue-123
```

**With pytest-bdd:**
```bash
pip install pytest-bdd
pytest --bdd
```

**Note:** BDD tests are supplementary. CI uses Django's test runner.

---

## Continuous Integration

### CI Test Workflow

When you push code, GitHub Actions automatically:

1. **Lints code** (flake8, djlint)
2. **Scans for security issues** (safety, bandit)
3. **Runs test suite** with coverage
4. **Validates coverage ≥ 80%**
5. **Generates coverage reports**
6. **Archives reports** (14-30 days retention)

### CI Environment

CI tests run in Docker using:
- `docker-compose.prod.yml`
- Chrome/Chromedriver for E2E tests
- PostgreSQL test database
- Environment variables from GitHub secrets

### View CI Results

1. Go to **Actions** tab in GitHub
2. Click on your commit/PR
3. View test results and coverage reports
4. Download artifacts for detailed reports

---

## Writing New Tests

### Test File Template

```python
from django.test import TestCase, Client
from django.contrib.auth.models import User
from active_interview_app.models import Chat

class MyChatTest(TestCase):
    def setUp(self):
        """Run before each test method"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_something(self):
        """Test description"""
        # Arrange
        self.client.login(username='testuser', password='testpass123')

        # Act
        response = self.client.get('/chat/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Expected Content')
```

### Best Practices

1. **One assertion per test** (when possible)
2. **Use descriptive test names** (`test_user_cannot_delete_other_users_chat`)
3. **Follow AAA pattern** (Arrange, Act, Assert)
4. **Mock external dependencies** (OpenAI, file processing)
5. **Test edge cases** (empty data, missing fields, permissions)
6. **Clean up in tearDown** (if needed)

---

## Common Testing Scenarios

### Testing Views

```python
def test_view_requires_login(self):
    response = self.client.get('/chat/')
    self.assertEqual(response.status_code, 302)  # Redirect to login

def test_view_with_login(self):
    self.client.login(username='testuser', password='testpass123')
    response = self.client.get('/chat/')
    self.assertEqual(response.status_code, 200)
```

### Testing Models

```python
def test_model_creation(self):
    chat = Chat.objects.create(
        user=self.user,
        title="Test Chat",
        difficulty=5
    )
    self.assertEqual(chat.title, "Test Chat")
    self.assertEqual(chat.difficulty, 5)
```

### Testing Forms

```python
def test_form_valid_data(self):
    form = CreateChatForm(data={
        'title': 'Test',
        'difficulty': 5,
        'type': 'GENERAL'
    })
    self.assertTrue(form.is_valid())

def test_form_invalid_data(self):
    form = CreateChatForm(data={'title': ''})
    self.assertFalse(form.is_valid())
```

---

## Troubleshooting Tests

### Tests Fail with Import Errors

```bash
# Make sure you're in the right directory
cd active_interview_backend

# Install all dependencies
pip install -r requirements.txt
```

### Database Errors

```bash
# Reset test database
python manage.py test --keepdb
rm db.sqlite3  # If using SQLite
```

### E2E Tests Fail

E2E tests require Chrome/Chromedriver. For local E2E testing:

```bash
# Install Chrome and Chromedriver
# Or run E2E tests in Docker:
docker exec django python3 manage.py test active_interview_app.tests.test_e2e
```

### Coverage Shows 0%

Make sure `.coveragerc` exists and is properly configured. Check that you're running coverage from `active_interview_backend/`.

---

## Next Steps

- **[Troubleshooting Guide](troubleshooting.md)** - Solutions to common issues
- **[Local Development](local-development.md)** - Setup and run the app
- **[CI/CD Documentation](../deployment/ci-cd.md)** - Understand the pipeline

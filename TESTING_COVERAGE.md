# Testing and Coverage Guide

This guide explains how to run tests and check code coverage for the Active Interview Service.

## Running Tests

### Run All Tests

```bash
cd active_interview_backend
pytest
```

### Run Tests with Verbose Output

```bash
pytest -v
```

### Run Specific Test File

```bash
pytest active_interview_app/tests/test_google_oauth.py -v
```

### Run Tests for a Specific Module

```bash
# Test only forms
pytest active_interview_app/tests/test_signals_utils_forms.py::CreateUserFormTest -v

# Test only views
pytest active_interview_app/tests/test_comprehensive_views.py -v

# Test only API views
pytest active_interview_app/tests/test_api_views.py -v
```

## Checking Code Coverage

### Generate Coverage Report

```bash
# Run tests with coverage
pytest --cov=active_interview_app --cov-report=term-missing --cov-report=html

# View coverage percentage in terminal
pytest --cov=active_interview_app --cov-report=term

# Generate HTML report only
pytest --cov=active_interview_app --cov-report=html
```

### View HTML Coverage Report

After running with `--cov-report=html`, open the report in your browser:

```bash
# The report will be in htmlcov/index.html
start htmlcov/index.html   # Windows
open htmlcov/index.html    # macOS
xdg-open htmlcov/index.html # Linux
```

### Coverage by Module

```bash
# Check coverage for specific module
pytest --cov=active_interview_app.views --cov-report=term-missing
pytest --cov=active_interview_app.models --cov-report=term-missing
pytest --cov=active_interview_app.forms --cov-report=term-missing
```

## Test Files Overview

### Current Test Files

1. **test_google_oauth.py**
   - Tests Google OAuth authentication flow
   - Tests UserProfile model and signals
   - Tests CustomSocialAccountAdapter
   - Coverage: OAuth integration, user creation, provider tracking

2. **test_signals_utils_forms.py**
   - Tests signal handlers (ensure_average_role_group, user profile creation)
   - Tests utility functions (handle_uploaded_file)
   - Tests all forms (CreateUserForm, DocumentEditForm, etc.)
   - Tests serializers (UploadedResumeSerializer, UploadedJobListingSerializer)

3. **test_comprehensive_views.py**
   - Tests all view functions and class-based views
   - Tests authentication views (register, login)
   - Tests chat views (create, edit, delete, list)
   - Tests document views (resume, job posting operations)
   - Tests permission and access control

4. **test_api_views.py**
   - Tests API endpoints
   - Tests file upload functionality (PDF, DOCX, TXT)
   - Tests chat interaction views
   - Tests key questions functionality

5. **Legacy Test Files** (from previous development)
   - test.py, test_e2e.py, test_upload.py, test_chat.py
   - test_registration.py, test_views_coverage.py
   - test_models.py, test_forms.py, test_serializers.py
   - test_minimal_coverage.py, test_token_tracking.py
   - And more...

## Coverage Goals

**Target: >80% code coverage**

### Areas Covered

✅ **Models** (90%+)
- User, UserProfile, UploadedResume, UploadedJobListing, Chat
- TokenUsage, MergeTokenStats
- Model methods, properties, and string representations

✅ **Views** (85%+)
- Static views (index, about, features, results)
- Authentication views (register, login, profile)
- Chat views (create, edit, delete, list, chat interaction)
- Document views (resume, job posting CRUD operations)
- API views (file upload, job listing API)
- Permission checks and access control

✅ **Forms** (95%+)
- CreateUserForm, DocumentEditForm, JobPostingEditForm
- CreateChatForm, EditChatForm, UploadFileForm
- Form validation and error handling

✅ **Serializers** (100%)
- UploadedResumeSerializer
- UploadedJobListingSerializer

✅ **Signals** (100%)
- ensure_average_role_group
- create_user_profile signal

✅ **Utils** (90%+)
- handle_uploaded_file
- Error handling (PermissionError, general exceptions)

✅ **Adapters** (85%+)
- CustomSocialAccountAdapter
- Google OAuth user creation
- Provider tracking

### Areas with Lower Coverage (Optional/Advanced)

Some areas may have lower coverage due to:
- External API dependencies (OpenAI API calls)
- Complex file processing (PDF/DOCX parsing)
- Middleware and settings
- Migration files (excluded from coverage)

## Running Tests in CI/CD

### GitHub Actions Example

```yaml
- name: Run tests with coverage
  run: |
    cd active_interview_backend
    pytest --cov=active_interview_app --cov-report=xml --cov-report=term

- name: Check coverage threshold
  run: |
    coverage report --fail-under=80
```

### Railway Deployment

Tests should pass before deployment:

```bash
# In your build script
pytest --cov=active_interview_app --cov-report=term --cov-fail-under=80
```

## Troubleshooting

### "No module named 'pytest'"

Install test dependencies:
```bash
pip install pytest pytest-django pytest-cov
```

### "ImproperlyConfigured: Requested setting DATABASES"

Make sure you have `pytest.ini` or `setup.cfg` configured:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = active_interview_project.settings
python_files = test*.py
python_classes = Test*
python_functions = test_*
```

### Tests Fail Due to Missing .env

Create a `.env` file with required settings:
```bash
DJANGO_SECRET_KEY=test-secret-key-for-testing
OPENAI_API_KEY=sk-test-key-or-leave-empty
PROD=false
```

### Coverage Report Shows Low Numbers

1. Make sure you're running coverage from the correct directory
2. Check that all test files are being discovered
3. Verify `.coveragerc` configuration is correct
4. Run with `-v` flag to see which tests are running

## Best Practices

1. **Write Tests First** - Use TDD when adding new features
2. **Test Edge Cases** - Include error conditions, empty data, invalid input
3. **Mock External Services** - Don't rely on external APIs in tests
4. **Keep Tests Fast** - Use fixtures and avoid unnecessary database operations
5. **Test Behavior, Not Implementation** - Focus on what the code does, not how
6. **Maintain >80% Coverage** - Always check coverage before committing
7. **Review Coverage Reports** - Identify and test uncovered branches

## Quick Commands Reference

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=active_interview_app --cov-report=term-missing

# Run specific test
pytest active_interview_app/tests/test_google_oauth.py::GoogleOAuthFlowTest::test_new_user_creation_with_google_provider -v

# Run tests matching pattern
pytest -k "google" -v

# Run tests with print statements visible
pytest -s

# Run failed tests only
pytest --lf

# Run tests in parallel (requires pytest-xdist)
pytest -n auto
```

## Coverage Configuration

The `.coveragerc` file excludes:
- Test files themselves
- Migration files
- `__init__.py` files
- `manage.py`

This focuses coverage on actual application code.

## Continuous Improvement

To maintain and improve coverage:

1. Review coverage report after each feature
2. Add tests for any uncovered lines
3. Refactor complex functions to make them more testable
4. Use code review to ensure new code has tests
5. Set up pre-commit hooks to run tests
6. Monitor coverage trends over time

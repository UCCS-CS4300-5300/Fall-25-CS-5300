# Step Definitions

This directory contains step definitions for BDD feature tests.

## Purpose

Step definitions implement the actual test logic for Given/When/Then statements in feature files.

## Structure

Organize step files by feature area:

```
steps/
├── __init__.py
├── README.md                    # This file
├── authentication_steps.py      # User auth-related steps
├── chat_steps.py               # Chat/interview session steps
├── upload_steps.py             # File upload steps
├── navigation_steps.py         # Common navigation steps
└── common_steps.py             # Shared/reusable steps
```

## Framework Support

This project can use either:
- **Behave** (recommended) - Python-native BDD framework
- **pytest-bdd** - pytest plugin for BDD

### Behave Example

```python
# authentication_steps.py
from behave import given, when, then
from django.contrib.auth.models import User

@given('a user exists with username "{username}" and password "{password}"')
def create_user(context, username, password):
    User.objects.create_user(username=username, password=password)
    context.username = username
    context.password = password

@when('I fill in "{field}" with "{value}"')
def fill_field(context, field, value):
    context.browser.fill(field, value)

@then('I should be logged in')
def check_logged_in(context):
    assert context.client.session.get('_auth_user_id') is not None
```

### pytest-bdd Example

```python
# authentication_steps.py
from pytest_bdd import given, when, then, scenarios
from django.contrib.auth.models import User

scenarios('../../../features/authentication.feature')

@given('a user exists with username "<username>" and password "<password>"')
def create_user(username, password):
    return User.objects.create_user(username=username, password=password)

@when('I fill in "<field>" with "<value>"')
def fill_field(browser, field, value):
    browser.fill(field, value)

@then('I should be logged in')
def check_logged_in(client):
    assert client.session.get('_auth_user_id') is not None
```

## Best Practices

1. **Keep steps atomic** - Each step should do one thing
2. **Reuse steps** - Import common steps across multiple step files
3. **Use context** (behave) or fixtures (pytest-bdd) - Store state between steps
4. **Avoid implementation details** - Steps should test behavior, not implementation
5. **Use descriptive step patterns** - Make step definitions match natural language
6. **Clean up after tests** - Use hooks to reset database/state between scenarios

## Testing with Django

Common patterns for Django BDD tests:

### Database Setup

```python
from django.test import TestCase
from behave import given

@given('the database is clean')
def clean_database(context):
    # Django test database is automatically cleaned between tests
    pass
```

### Using Django Test Client

```python
from django.test import Client
from behave import given, when, then

@given('I am on the login page')
def visit_login_page(context):
    context.client = Client()
    context.response = context.client.get('/accounts/login/')

@when('I submit the login form')
def submit_login(context):
    context.response = context.client.post('/accounts/login/', {
        'username': context.username,
        'password': context.password,
    })

@then('I should be redirected to "{url}"')
def check_redirect(context, url):
    assert context.response.status_code == 302
    assert context.response.url == url
```

### Using Selenium for E2E Tests

```python
from selenium import webdriver
from behave import given, when, then

@given('I am on the registration page')
def visit_registration(context):
    if not hasattr(context, 'browser'):
        context.browser = webdriver.Chrome()
    context.browser.get('http://127.0.0.1:8000/accounts/register/')

@when('I click "{button_text}"')
def click_button(context, button_text):
    button = context.browser.find_element_by_xpath(f"//button[text()='{button_text}']")
    button.click()
```

## File Organization

Organize steps by domain:

- **authentication_steps.py** - Login, logout, registration
- **chat_steps.py** - Creating, editing, deleting chats
- **upload_steps.py** - Uploading resumes and job postings
- **navigation_steps.py** - Common page navigation
- **common_steps.py** - Generic steps used across features

## Running Step Definitions

Steps are automatically discovered when running behave or pytest-bdd from the `active_interview_backend/` directory.

```bash
cd active_interview_backend

# Behave automatically discovers steps in tests/steps/
behave

# pytest-bdd requires explicit scenarios() calls in step files
pytest --bdd
```

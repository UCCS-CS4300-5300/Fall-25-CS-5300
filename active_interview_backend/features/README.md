# Feature Files

This directory contains BDD (Behavior-Driven Development) feature files written in Gherkin syntax.

## Purpose

Feature files document user stories and acceptance criteria in a human-readable format that can also be executed as automated tests.

## Structure

```
features/
├── README.md                   # This file
├── authentication.feature      # User authentication stories
├── chat_management.feature     # Interview chat CRUD operations
├── interview_session.feature   # Active interview session scenarios
├── document_upload.feature     # Resume and job listing upload
└── results_analysis.feature    # Interview results and analytics
```

## Gherkin Syntax

Each feature file follows this structure:

```gherkin
Feature: Brief description of the feature
  As a [user type]
  I want [goal]
  So that [benefit]

  Scenario: Specific scenario name
    Given [precondition]
    And [another precondition]
    When [action]
    And [another action]
    Then [expected outcome]
    And [another expected outcome]
```

## Running Feature Tests

### Using Behave (Recommended)

```bash
# Install behave
pip install behave

# Run all features
cd active_interview_backend
behave

# Run specific feature
behave features/authentication.feature

# Run specific scenario
behave features/authentication.feature:10  # Line number of scenario
```

### Using pytest-bdd

```bash
# Install pytest-bdd
pip install pytest-bdd

# Run BDD tests
cd active_interview_backend
pytest --bdd
```

## Step Definitions

Step definitions are located in `active_interview_app/tests/steps/` and implement the actual test logic for each Given/When/Then statement.

## Best Practices

1. **Keep scenarios independent** - Each scenario should be runnable in isolation
2. **Use descriptive names** - Scenario names should clearly describe the behavior being tested
3. **Focus on user behavior** - Write from the user's perspective, not implementation details
4. **Reuse steps** - Create reusable Given/When/Then steps across scenarios
5. **One feature per file** - Keep related scenarios together in a single feature file
6. **Use Background** - For common preconditions shared across scenarios in a feature
7. **Use Scenario Outline** - For testing the same behavior with different data

## Example Feature File

```gherkin
Feature: User Authentication
  As a job seeker
  I want to create an account and log in
  So that I can access interview practice sessions

  Background:
    Given the application is running
    And the database is clean

  Scenario: Successful user registration
    Given I am on the registration page
    When I fill in "username" with "testuser"
    And I fill in "email" with "test@example.com"
    And I fill in "password" with "SecurePass123"
    And I fill in "password confirmation" with "SecurePass123"
    And I click "Register"
    Then I should see "Registration successful"
    And I should be redirected to the login page

  Scenario: Login with valid credentials
    Given a user exists with username "testuser" and password "SecurePass123"
    And I am on the login page
    When I fill in "username" with "testuser"
    And I fill in "password" with "SecurePass123"
    And I click "Login"
    Then I should be logged in
    And I should see "Welcome, testuser"
```

## Integration with CI/CD

When adding BDD tests to CI pipeline:
1. Add behave or pytest-bdd to `requirements.txt`
2. Update `.github/workflows/CI.yml` to run BDD tests
3. Consider running BDD tests separately from unit tests for clarity
4. BDD test results should be included in coverage reports

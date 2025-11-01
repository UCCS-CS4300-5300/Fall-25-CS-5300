# BDD Feature Files Guide

This guide explains how to create and maintain Behavior-Driven Development (BDD) feature files from GitHub issues.

## Overview

Feature files use **Gherkin syntax** to describe application behavior in a human-readable format. These files serve as both documentation and executable tests.

**Location:** `active_interview_backend/features/`

**Format:** `.feature` files written in Gherkin

---

## Creating Feature Files from GitHub Issues

### Step 1: Extract Information from Issue

When implementing a feature, gather this information from the GitHub issue:

**User Stories:** Typically formatted as:
```
As a [user type]
I want [goal]
So that [benefit]
```

**Acceptance Criteria:** Usually a checklist of requirements

**Gherkin Scenarios:** May already be written in the issue

**Sub-issues:** Related issues that should be included as scenarios

---

### Step 2: Check for Existing Feature File

```bash
# Search for related feature files
ls active_interview_backend/features/*.feature

# Look for keywords in file names
grep -l "keyword" active_interview_backend/features/*.feature
```

**Decision:**
- **File exists** → Add new scenarios to existing file
- **File doesn't exist** → Create new `.feature` file

---

### Step 3: Create or Update Feature File

#### File Naming Convention

Use descriptive, lowercase names with underscores:
- ✅ `exportable_reports.feature`
- ✅ `user_authentication.feature`
- ✅ `chat_management.feature`
- ❌ `feature1.feature`
- ❌ `ExportableReports.feature`

#### Feature File Structure

```gherkin
@issue-123
Feature: [Feature Name]
  As a [user type]
  I want [goal]
  So that [benefit]

  Background:
    Given [common preconditions for all scenarios]

  @issue-123
  Scenario: [Scenario name]
    Given [precondition]
    And [another precondition]
    When [action]
    And [another action]
    Then [expected outcome]
    And [another expected outcome]

  @issue-123 @issue-124
  Scenario: [Another scenario]
    Given [precondition]
    When [action]
    Then [expected outcome]
```

---

## Example: Creating Feature from GitHub Issue

### GitHub Issue #123

**Title:** Add PDF Export for Interview Reports

**User Story:**
```
As a job seeker
I want to export my interview results as a PDF
So that I can share my performance with others
```

**Acceptance Criteria:**
- [ ] User can generate a report from completed interview
- [ ] Report includes performance scores
- [ ] Report can be downloaded as PDF
- [ ] PDF includes all interview details

**Sub-issue #124:** Add email delivery option (future)

---

### Resulting Feature File

**File:** `active_interview_backend/features/exportable_reports.feature`

```gherkin
@issue-123
Feature: Export Interview Reports
  As a job seeker
  I want to export my interview results as a PDF
  So that I can share my performance with others

  Background:
    Given I am logged in as a user
    And I have completed an interview

  @issue-123
  Scenario: Generate PDF report from completed interview
    Given I am on the interview results page
    When I click "Generate Report"
    Then a report should be created
    And I should see "Report generated successfully"
    And I should see a "Download PDF" button

  @issue-123
  Scenario: Download PDF report
    Given I have generated a report
    When I click "Download PDF"
    Then a PDF file should be downloaded
    And the file should be named "interview_report_[chat_title]_[timestamp].pdf"

  @issue-123
  Scenario: PDF includes performance scores
    Given I have generated a report
    When I download the PDF
    Then the PDF should include "Professionalism Score"
    And the PDF should include "Subject Knowledge Score"
    And the PDF should include "Clarity Score"
    And the PDF should include "Overall Score"

  @issue-123
  Scenario: PDF includes interview details
    Given I have generated a report for a "Technical Skills" interview
    When I download the PDF
    Then the PDF should include the interview type
    And the PDF should include the difficulty level
    And the PDF should include the completion date
    And the PDF should include all questions and answers

  @issue-124
  Scenario: Email report (future feature - not implemented)
    Given I have generated a report
    When I click "Email Report"
    Then I should see an email composition dialog
    # This scenario is a placeholder for future issue #124
```

---

## Gherkin Syntax Reference

### Feature

Describes the feature being implemented.

```gherkin
Feature: Brief description
  Longer description explaining the feature
  and its value to users
```

### Background

Steps that run before each scenario in the file.

```gherkin
Background:
  Given the user is logged in
  And the database contains test data
```

### Scenario

A single test case.

```gherkin
Scenario: User logs in successfully
  Given I am on the login page
  When I enter valid credentials
  And I click "Login"
  Then I should see the dashboard
```

### Scenario Outline

Template for multiple similar scenarios with different data.

```gherkin
Scenario Outline: Test different interview types
  Given I create a chat with type "<type>"
  When I start the interview
  Then I should see questions appropriate for "<type>"

  Examples:
    | type                  |
    | General Interview     |
    | Technical Skills      |
    | Personality          |
    | Final Screening      |
```

### Tags

Organize and filter scenarios.

```gherkin
@issue-123 @smoke-test
Scenario: Critical feature test
  ...

@issue-123 @integration
Scenario: Full workflow test
  ...
```

**Common tags:**
- `@issue-123` - Link to GitHub issue
- `@smoke-test` - Critical path tests
- `@integration` - Integration tests
- `@wip` - Work in progress (skip in CI)

---

## Given/When/Then Guidelines

### Given - Preconditions

Set up the initial state.

**Examples:**
```gherkin
Given I am logged in as a user
Given the database contains 5 chat sessions
Given I have uploaded a resume
Given the OpenAI API is available
```

### When - Actions

Describe the action being tested.

**Examples:**
```gherkin
When I click "Create Chat"
When I submit the login form
When I upload a PDF file
When I navigate to "/chat/1/"
```

### Then - Assertions

Verify the expected outcome.

**Examples:**
```gherkin
Then I should see "Chat created successfully"
Then the chat should be saved to the database
Then I should be redirected to "/chat/1/"
Then the response status code should be 200
```

### And/But - Continuation

Add additional steps of the same type.

```gherkin
Given I am logged in
And I have a resume uploaded
And I have a job listing saved
When I click "Create Chat"
And I fill in the form
And I submit the form
Then I should see a success message
And the chat should appear in my chat list
But I should not see validation errors
```

---

## Best Practices

### 1. Keep Scenarios Independent

Each scenario should be runnable in isolation.

**Good:**
```gherkin
Scenario: Create chat
  Given I am logged in
  When I create a new chat
  Then the chat should exist

Scenario: Delete chat
  Given I am logged in
  And I have a chat
  When I delete the chat
  Then the chat should not exist
```

**Bad:**
```gherkin
Scenario: Create chat
  When I create a new chat
  Then the chat should exist

Scenario: Delete chat (depends on previous)
  When I delete the chat
  Then the chat should not exist
```

### 2. Use Descriptive Scenario Names

**Good:**
```gherkin
Scenario: User cannot delete another user's chat
Scenario: PDF report includes all performance scores
Scenario: Form validation prevents empty chat title
```

**Bad:**
```gherkin
Scenario: Test 1
Scenario: Delete functionality
Scenario: Check form
```

### 3. Focus on User Behavior

Describe what the user does, not implementation details.

**Good:**
```gherkin
When I upload a resume
Then I should see "Resume uploaded successfully"
```

**Bad:**
```gherkin
When I POST to /upload-file/ with a valid PDF
Then the response status should be 201
And the UploadedResume model should have a new instance
```

### 4. Use Background for Common Setup

**Good:**
```gherkin
Background:
  Given I am logged in
  And I have a resume uploaded

Scenario: Create chat with resume
  When I create a chat
  Then the chat should link to my resume

Scenario: View resume details
  When I view my resume
  Then I should see the resume details
```

**Bad:**
```gherkin
Scenario: Create chat with resume
  Given I am logged in
  And I have a resume uploaded
  When I create a chat
  Then the chat should link to my resume

Scenario: View resume details
  Given I am logged in
  And I have a resume uploaded
  When I view my resume
  Then I should see the resume details
```

### 5. Tag with Issue Numbers

Always tag scenarios with the GitHub issue they implement.

```gherkin
@issue-123
Feature: Export Reports

  @issue-123
  Scenario: Generate report
    ...

  @issue-123 @issue-124
  Scenario: Email report
    ...
```

---

## Updating Existing Feature Files

### Adding Scenarios

When a new GitHub issue adds functionality to an existing feature:

1. Open the existing `.feature` file
2. Add new scenarios at the end
3. Tag with the new issue number
4. Update feature description if needed

**Example:**

```gherkin
@issue-45 @issue-67
Feature: User Authentication
  As a user
  I want to authenticate securely
  So that my data is protected

  @issue-45
  Scenario: Login with valid credentials
    ...

  @issue-45
  Scenario: Login with invalid credentials
    ...

  @issue-67
  Scenario: Two-factor authentication (NEW)
    Given I have 2FA enabled
    When I login with valid credentials
    Then I should see a 2FA prompt
    When I enter the correct 2FA code
    Then I should be logged in
```

---

## Running BDD Tests

### With Behave

```bash
cd active_interview_backend

# Run all features
behave

# Run specific feature
behave features/exportable_reports.feature

# Run scenarios with specific tag
behave --tags=issue-123

# Run scenarios at specific line
behave features/exportable_reports.feature:15
```

### With pytest-bdd

```bash
cd active_interview_backend

# Run all BDD tests
pytest --bdd

# Run specific feature
pytest --bdd -k "exportable_reports"
```

**Note:** Currently, the project uses Django's test runner as primary. BDD tests are supplementary.

---

## Step Definitions

After creating feature files, implement step definitions.

**Location:** `active_interview_backend/active_interview_app/tests/steps/`

**Example:**

```python
# active_interview_app/tests/steps/exportable_reports_steps.py

from behave import given, when, then
from django.contrib.auth.models import User
from active_interview_app.models import Chat, ExportableReport

@given('I have completed an interview')
def step_impl(context):
    context.user = User.objects.create_user(
        username='testuser',
        password='testpass'
    )
    context.chat = Chat.objects.create(
        user=context.user,
        title='Test Interview',
        messages=[
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': 'Hi there!'}
        ]
    )

@when('I click "Generate Report"')
def step_impl(context):
    context.response = context.client.post(
        f'/chat/{context.chat.id}/generate-report/'
    )

@then('a report should be created')
def step_impl(context):
    assert ExportableReport.objects.filter(chat=context.chat).exists()
```

---

## Common Patterns

### Testing Permissions

```gherkin
Scenario: User cannot access another user's chat
  Given I am logged in as "user1"
  And another user "user2" has a chat
  When I try to view user2's chat
  Then I should see "Permission denied"
  And I should be redirected to my chat list
```

### Testing Validation

```gherkin
Scenario: Form validation prevents invalid data
  Given I am on the create chat page
  When I submit the form with an empty title
  Then I should see "Title is required"
  And the chat should not be created
```

### Testing Different States

```gherkin
Scenario: Behavior when OpenAI is unavailable
  Given the OpenAI API is unavailable
  When I try to create a chat
  Then I should see "AI service temporarily unavailable"
  But I should still be able to save my data
```

---

## Next Steps

- **[Testing Guide](testing.md)** - Run tests and check coverage
- **[Local Development](local-development.md)** - Setup for running BDD tests
- **[Contributing Guide](../../CONTRIBUTING.md)** - Contribution workflow

---

## References

- **Behave Documentation:** https://behave.readthedocs.io/
- **Gherkin Syntax:** https://cucumber.io/docs/gherkin/reference/
- **pytest-bdd:** https://pytest-bdd.readthedocs.io/

---
# STRUCTURED METADATA (for quick parsing/statistics)
sequence_id: "invitation_workflow_20251114"
feature: "Invitation Workflow (Phases 2-5)"
test_file: "active_interview_app/tests/test_invitations.py"
branch: "Invitation-Interviews"
user: "dakota"

# Iteration summary (one entry per test run)
iterations:
  - number: 1
    timestamp: "2025-11-14 20:45:00"
    total_tests: 27
    passed: 15
    failed: 5
    errors: 7
    new_test_failures: 12      # Failures in newly added tests
    regression_failures: 0      # Failures in pre-existing tests
    execution_time: 13.77

  - number: 2
    timestamp: "2025-11-14 20:52:00"
    total_tests: 27
    passed: 26
    failed: 1
    errors: 0
    new_test_failures: 1
    regression_failures: 0
    execution_time: 13.87

  - number: 3
    timestamp: "2025-11-14 21:00:00"
    total_tests: 27
    passed: 27
    failed: 0
    errors: 0
    new_test_failures: 0
    regression_failures: 0
    execution_time: 13.87

# Aggregated statistics
summary:
  total_iterations: 3
  iterations_to_success: 3
  first_run_failure_rate: 44.4  # 12/27 tests failed
  final_status: "success"
  total_time_minutes: 20

# Coverage tracking
coverage:
  initial: 80
  final: 80
  change: 0
  note: "Added 27 new tests covering invitation workflow views"
---

# Test Sequence: Invitation Workflow (Phases 2-5)

**Feature:** Complete invitation workflow including creation, confirmation, dashboard, and email integration
**Test File:** `active_interview_app/tests/test_invitations.py` (27 tests)
**Status:** ✅ Success after 3 iterations
**Branch:** Invitation-Interviews

## Iteration 1: Initial Test Run
**Time:** 2025-11-14 20:45:00 | **Status:** ❌ 12 failures (5 failures + 7 errors)

**What changed:**
- Created new test file `test_invitations.py` with 27 test cases covering:
  - InvitationModelTests (10 tests) - Model helper methods
  - InvitationFormTests (4 tests) - Form validation
  - InvitationCreateViewTests (6 tests) - Invitation creation views
  - InvitationConfirmationViewTests (3 tests) - Confirmation page
  - InvitationDashboardViewTests (4 tests) - Invitation listing

**Command:** `python manage.py test active_interview_app.tests.test_invitations --verbosity=2`

**Results:** 15 passed, 12 failed (44.4% failure rate)

**Failed tests breakdown:**

*Form tests (7 errors):*
- `test_form_valid_data` - TypeError: fromisoformat: argument must be str
- `test_form_invalid_email` - Same error
- `test_form_past_datetime` - Same error
- `test_form_template_from_different_user` - Same error

*View tests (5 failures):*
- `test_get_as_interviewer` - AssertionError: 403 != 200
- `test_get_shows_confirmation` - AssertionError: 403 != 200
- `test_post_valid_data_creates_invitation` - AssertionError: 0 != 1 (no invitation created)
- `test_post_invalid_data_shows_errors` - AssertionError: 403 != 200
- `test_get_shows_all_invitations` - AssertionError: 403 != 200

**Root causes identified:**

1. **Form validation errors** - InvitationCreationForm had 'scheduled_date' and 'scheduled_time' in Meta.fields, but these are custom form fields, not model fields. When ModelForm tried to validate the model instance, it attempted to set InvitedInterview.scheduled_time (DateTimeField) with a time object, causing TypeError.

2. **Permission failures (403)** - Test users created with `create_user_with_role()` helper were getting role='candidate' instead of 'interviewer' due to timing issue with UserProfile signal auto-creation.

3. **Form data format** - Tests passed Python date/time objects to forms, but forms expect string data (as they would receive from POST requests).

---

## Iteration 2: Fix Form Definition and Test Data
**Time:** 2025-11-14 20:52:00 | **Status:** ❌ 1 error

**What changed:**

1. **Fixed InvitationCreationForm** (forms.py:184-188):
   - Removed 'scheduled_date' and 'scheduled_time' from Meta.fields
   - Only included actual model fields: ['template', 'candidate_email', 'duration_minutes']
   - Added comment explaining that scheduled_date/time are form-only fields

2. **Fixed test data formatting** - Changed all form tests to pass strings:
   ```python
   # Before: 'scheduled_date': future_time.date()
   # After:  'scheduled_date': future_time.strftime('%Y-%m-%d')
   ```

3. **Fixed create_user_with_role() helper**:
   - Always explicitly set role after get_or_create
   - Added user.refresh_from_db() to ensure profile is loaded

4. **Fixed URL pattern name**:
   - Changed 'invitation_create_with_template' → 'invitation_create_from_template'

**Results:** 26 passed, 1 error (96% pass rate) - **Progress: 12→1 failures** ⬇️

**Remaining error:**
- `test_get_with_template_id_preselects_template` - KeyError: 'template' in form.initial

**Root cause:** Test tried to access `form.initial['template']` but the form sets `form.fields['template'].initial` instead.

---

## Iteration 3: Fix Template Initial Value Test
**Time:** 2025-11-14 21:00:00 | **Status:** ✅ All passing

**What changed:**
- Fixed test assertion from `form.initial['template']` to `form.fields['template'].initial`

**Results:** 27 passed, 0 failed ✅

**Success!** All tests passing after 3 iterations.

**Full test suite verification:**
- Total tests in project: 918 (was 891, added 27 new tests)
- All tests passing: ✅
- No regressions detected: ✅

---

## Sequence Summary

**Statistics:**
- First-run failure rate: 44.4% (12/27 tests)
- Iterations to success: 3
- Regression failures: 0 (no pre-existing tests broke)
- Total debugging time: ~20 minutes
- New test coverage: 27 tests covering invitation workflow Phases 2-5

**Failure patterns by iteration:**
- Iteration 1: Form validation (58% of failures) + Permission/RBAC (42%)
- Iteration 2: Form initial value access pattern (100% of failures)
- Iteration 3: All resolved ✅

**Key learnings:**

1. **Django ModelForm validation** - Meta.fields should only include actual model fields. Custom form fields that don't map to model fields cause validation errors in _post_clean().

2. **Test data formatting** - Forms expect string data (matching POST data), not Python objects. Always use strftime() for dates/times in form tests.

3. **Signal timing** - UserProfile auto-creation via signals means get_or_create() gets existing profile with default values. Must explicitly update fields after get_or_create().

4. **Form initial values** - Django sets initial values on field objects (`form.fields['name'].initial`), not in the form's initial dict.

**Bug fixes made:**
1. `forms.py:184-188` - Removed non-model fields from InvitationCreationForm.Meta.fields
2. `test_invitations.py:30-43` - Fixed create_user_with_role() to properly set roles
3. Multiple test fixes for data formatting and assertions

**Research notes:**
This sequence demonstrates effective TDD workflow:
- 44% first-run failure rate (typical for complex feature with forms + permissions)
- Efficient iteration (3 runs to success)
- Clear failure patterns (form validation, then RBAC, then edge cases)
- No regressions in 891 existing tests
- Discovered and fixed production bug in form definition

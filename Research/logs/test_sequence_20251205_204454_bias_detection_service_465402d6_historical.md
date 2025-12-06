---
sequence_id: "bias_detection_service_465402d6_1"
feature: "Bias Detection Service"
test_file: "C:/Users/jacks/CS4300 Project/Fall-25-CS-5300/active_interview_backend/active_interview_app/tests/test_bias_detection_service.py"
branch: "unknown"
user: "researcher"
session_id: "465402d6-0f08-4e04-b0c4-03b3b37e3c1a"

iterations:
  - number: 1
    timestamp: "2025-11-28T02:16:39.966Z"
    total_tests: 51
    passed: 34
    failed: 3
    errors: 14
    new_test_failures: 17
    regression_failures: 0
    execution_time: 0.0

  - number: 2
    timestamp: "2025-11-28T02:42:00.096Z"
    total_tests: 51
    passed: 37
    failed: 0
    errors: 14
    new_test_failures: 14
    regression_failures: 0
    execution_time: 0.0

  - number: 3
    timestamp: "2025-11-28T02:48:18.414Z"
    total_tests: 51
    passed: 47
    failed: 2
    errors: 2
    new_test_failures: 0
    regression_failures: 4
    execution_time: 0.0

  - number: 4
    timestamp: "2025-11-28T02:53:51.749Z"
    total_tests: 51
    passed: 50
    failed: 0
    errors: 1
    new_test_failures: 1
    regression_failures: 0
    execution_time: 0.0

  - number: 5
    timestamp: "2025-11-28T02:57:40.302Z"
    total_tests: 51
    passed: 51
    failed: 0
    errors: 0
    new_test_failures: 0
    regression_failures: 0
    execution_time: 0.0

summary:
  total_iterations: 5
  iterations_to_success: 5
  first_run_failure_rate: 33.3
  final_status: "success"
  total_time_minutes: 0

coverage:
  initial: 0
  final: 0
  change: 0
---

# Test Sequence: Bias Detection Service

**Feature:** Bias Detection Service
**Test File:** `C:\Users\jacks\CS4300 Project\Fall-25-CS-5300\active_interview_backend\active_interview_app\tests\test_bias_detection_service.py`
**Status:** ✅ Success after 5 iterations
**Session ID:** `465402d6-0f08-4e04-b0c4-03b3b37e3c1a`

## Iteration 1
**Time:** 2025-11-28T02:16:39.966Z | **Status:** ❌ 17 failures

**Command:** `python manage.py test`

**Results:** 34 passed, 3 failed, 14 errors

**Failed tests:**
- test_severity_level_low (FAIL)

<details>
<summary>Test output excerpt</summary>

```
Error: Exit code 1
Creating test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
System check identified some issues:

WARNINGS:
?: settings.ACCOUNT_AUTHENTICATION_METHOD is deprecated, use: settings.ACCOUNT_LOGIN_METHODS = {'username', 'email'}
?: settings.ACCOUNT_EMAIL_REQUIRED is deprecated, use: settings.ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
?: settings.ACCOUNT_USERNAME_REQUIRED is deprecated, use: settings.ACCOUNT_SIGNUP_FIE
```
</details>

---

## Iteration 2
**Time:** 2025-11-28T02:42:00.096Z | **Status:** ❌ 14 failures

**Command:** `python manage.py test`

**Results:** 37 passed, 0 failed, 14 errors

<details>
<summary>Test output excerpt</summary>

```
Error: Exit code 1
Creating test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
System check identified some issues:

WARNINGS:
?: settings.ACCOUNT_AUTHENTICATION_METHOD is deprecated, use: settings.ACCOUNT_LOGIN_METHODS = {'username', 'email'}
?: settings.ACCOUNT_EMAIL_REQUIRED is deprecated, use: settings.ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
?: settings.ACCOUNT_USERNAME_REQUIRED is deprecated, use: settings.ACCOUNT_SIGNUP_FIE
```
</details>

---

## Iteration 3
**Time:** 2025-11-28T02:48:18.414Z | **Status:** ❌ 4 failures

**Command:** `python manage.py test`

**Results:** 47 passed, 2 failed, 2 errors

**Failed tests:**
- test_bias_analysis_result_json_field (FAIL)
- test_save_analysis_result (FAIL)
- test_bias_analysis_result_bias_score_validation (ERROR)
- test_bias_analysis_result_generic_foreign_key (ERROR)

<details>
<summary>Test output excerpt</summary>

```
Error: Exit code 1
Creating test database for alias 'default'...
System check identified some issues:

WARNINGS:
?: settings.ACCOUNT_AUTHENTICATION_METHOD is deprecated, use: settings.ACCOUNT_LOGIN_METHODS = {'username', 'email'}
?: settings.ACCOUNT_EMAIL_REQUIRED is deprecated, use: settings.ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
?: settings.ACCOUNT_USERNAME_REQUIRED is deprecated, use: settings.ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']

Sys
```
</details>

---

## Iteration 4
**Time:** 2025-11-28T02:53:51.749Z | **Status:** ❌ 1 failures

**Command:** `python manage.py test`

**Results:** 50 passed, 0 failed, 1 errors

**Failed tests:**
- test_bias_analysis_result_bias_score_validation (ERROR)

<details>
<summary>Test output excerpt</summary>

```
Error: Exit code 1
Creating test database for alias 'default'...
System check identified some issues:

WARNINGS:
?: settings.ACCOUNT_AUTHENTICATION_METHOD is deprecated, use: settings.ACCOUNT_LOGIN_METHODS = {'email', 'username'}
?: settings.ACCOUNT_EMAIL_REQUIRED is deprecated, use: settings.ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
?: settings.ACCOUNT_USERNAME_REQUIRED is deprecated, use: settings.ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']

Sys
```
</details>

---

## Iteration 5
**Time:** 2025-11-28T02:57:40.302Z | **Status:** ✅ All passing

**Command:** `python manage.py test`

**Results:** 51 passed, 0 failed, 0 errors

<details>
<summary>Test output excerpt</summary>

```
Found 51 test(s).
Consider using the pymupdf_layout package for a greatly improved page layout analysis.
Invalid regex pattern for term 'bad pattern': unterminated character set at position 0
Invalid regex pattern for term 'bad pattern': unterminated character set at position 0
Creating test database for alias 'default'...
System check identified some issues:

WARNINGS:
?: settings.ACCOUNT_AUTHENTICATION_METHOD is deprecated, use: settings.ACCOUNT_LOGIN_METHODS = {'email', 'username'}

```
</details>

---

## Sequence Summary

**Statistics:**
- First-run failure rate: 33.3%
- Iterations to success: 5
- Total iterations: 5
- Final status: success

**Notes:**
- This log was auto-generated from historical Claude Code session data
- Some fields (timestamps, execution times, coverage) may be incomplete
- For research purposes only

---
sequence_id: "existing_tests_dd468525_6"
feature: "Existing Tests"
test_file: "existing_tests"
branch: "unknown"
user: "researcher"
session_id: "dd468525-c975-4296-a9a5-90bc886a63b0"

iterations:
  - number: 1
    timestamp: "2025-10-28T05:32:31.969Z"
    total_tests: 492
    passed: 458
    failed: 13
    errors: 21
    new_test_failures: 0
    regression_failures: 34
    execution_time: 0.0

summary:
  total_iterations: 1
  iterations_to_success: incomplete
  first_run_failure_rate: 6.9
  final_status: "in_progress"
  total_time_minutes: 0

coverage:
  initial: 0
  final: 0
  change: 0
---

# Test Sequence: Existing Tests

**Feature:** Existing Tests
**Test File:** `existing_tests`
**Status:** ⏳ In_Progress
**Session ID:** `dd468525-c975-4296-a9a5-90bc886a63b0`

## Iteration 1
**Time:** 2025-10-28T05:32:31.969Z | **Status:** ❌ 34 failures

**Command:** `python manage.py test`

**Results:** 458 passed, 13 failed, 21 errors

**Failed tests:**
- test_missing_email (FAIL)
- test_missing_title (FAIL)
- test_cumulative_cost_decimal_conversion (FAIL)
- test_create_chat_key_questions_json_extraction_fails (FAIL)
- test_create_chat_key_questions_with_json (FAIL)
- test_create_chat_ai_unavailable (FAIL)
- test_create_chat_without_resume (FAIL)
- test_create_chat_with_ai (FAIL)
- test_create_chat_without_ai (FAIL)

<details>
<summary>Test output excerpt</summary>

```
  -100→AssertionError: 400 != 201
   -99→
   -98→======================================================================
   -97→FAIL: test_missing_email (active_interview_app.tests.test_forms.CreateUserFormTest)
   -96→Test form fails when email is missing
   -95→----------------------------------------------------------------------
   -94→Traceback (most recent call last):
   -93→  File "/Users/theaaron730/Documents/Fall-25-CS-5300/active_interview_backend/active_interview_app/tests/test_forms.p
```
</details>

---

## Sequence Summary

**Statistics:**
- First-run failure rate: 6.9%
- Iterations to success: incomplete
- Total iterations: 1
- Final status: in_progress

**Notes:**
- This log was auto-generated from historical Claude Code session data
- Some fields (timestamps, execution times, coverage) may be incomplete
- For research purposes only

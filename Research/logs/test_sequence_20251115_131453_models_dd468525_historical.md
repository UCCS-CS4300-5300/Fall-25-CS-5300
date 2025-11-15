---
sequence_id: "models_dd468525_3"
feature: "Models"
test_file: "/Users/theaaron730/Documents/Fall-25-CS-5300/active_interview_backend/active_interview_app/tests/test_models.py"
branch: "unknown"
user: "researcher"
session_id: "dd468525-c975-4296-a9a5-90bc886a63b0"

iterations:
  - number: 1
    timestamp: "2025-10-28T06:43:42.256Z"
    total_tests: 492
    passed: 487
    failed: 5
    errors: 0
    new_test_failures: 5
    regression_failures: 0
    execution_time: 0.0

summary:
  total_iterations: 1
  iterations_to_success: incomplete
  first_run_failure_rate: 1.0
  final_status: "in_progress"
  total_time_minutes: 0

coverage:
  initial: 0
  final: 0
  change: 0
---

# Test Sequence: Models

**Feature:** Models
**Test File:** `/Users/theaaron730/Documents/Fall-25-CS-5300/active_interview_backend/active_interview_app/tests/test_models.py`
**Status:** ⏳ In_Progress
**Session ID:** `dd468525-c975-4296-a9a5-90bc886a63b0`

## Iteration 1
**Time:** 2025-10-28T06:43:42.256Z | **Status:** ❌ 5 failures

**Command:** `python manage.py test`

**Results:** 487 passed, 5 failed, 0 errors

**Failed tests:**
- test_uploaded_resume_view_post_valid (FAIL)
- test_missing_title (FAIL)
- test_missing_title (FAIL)
- test_create_chat_key_questions_with_json (FAIL)
- test_register_success (FAIL)

<details>
<summary>Test output excerpt</summary>

```
FAIL: test_uploaded_resume_view_post_valid (active_interview_app.tests.test_complete_coverage_all_files.ViewsCompleteCoverageTest)
Test UploadedResumeView POST with valid data
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/theaaron730/Documents/Fall-25-CS-5300/active_interview_backend/active_interview_app/tests/test_complete_coverage_all_files.py", line 977, in test_uploaded_resume_view_post_valid
    self.assertEqual(resp
```
</details>

---

## Sequence Summary

**Statistics:**
- First-run failure rate: 1.0%
- Iterations to success: incomplete
- Total iterations: 1
- Final status: in_progress

**Notes:**
- This log was auto-generated from historical Claude Code session data
- Some fields (timestamps, execution times, coverage) may be incomplete
- For research purposes only

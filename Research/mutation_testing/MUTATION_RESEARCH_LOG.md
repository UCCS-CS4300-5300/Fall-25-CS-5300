# Mutation Testing Research Log

**Project:** Active Interview Backend
**Date Started:** 2025-12-16 03:16:34 UTC
**Date Completed:** 2025-12-16 04:19:52 UTC
**Mode:** PARALLEL (6 workers)
**Branch:** Mutation_Testing
**Tool:** mutmut v2.4.0

---

## Final Status: COMPLETE

| Metric | Value |
|--------|-------|
| **Status** | COMPLETED |
| **Modules Tested** | 15 / 21 |
| **Modules Skipped** | 6 (baseline failures) |
| **Total Mutations** | 1376 |
| **Killed** | 629 |
| **Survived** | 747 |
| **Timeouts** | 0 |
| **Overall Mutation Score** | **45.7%** |
| **Total Duration** | ~47 minutes |
| **Last Updated** | 2025-12-16 04:19:52 UTC |

---

## Module Results

| # | Module | Status | Mutations | Killed | Survived | Score | Duration |
|---|--------|--------|-----------|--------|----------|-------|----------|
| 1 | ratelimit_config | COMPLETE | 27 | 27 | 0 | **100.0%** | 5.1 min |
| 2 | permissions | COMPLETE | 43 | 39 | 4 | **90.7%** | 5.0 min |
| 3 | job_listing_parser | COMPLETE | 162 | 129 | 33 | **79.6%** | 19.3 min |
| 4 | bias_detection | COMPLETE | 191 | 132 | 59 | **69.1%** | 40.7 min |
| 5 | utils | COMPLETE | 8 | 5 | 3 | 62.5% | 0.8 min |
| 6 | openai_utils | COMPLETE | 81 | 38 | 43 | 46.9% | 19.0 min |
| 7 | resume_parser | COMPLETE | 101 | 46 | 55 | 45.5% | 19.2 min |
| 8 | serializers | COMPLETE | 226 | 101 | 125 | 44.7% | 47.1 min |
| 9 | audit_utils | COMPLETE | 19 | 8 | 11 | 42.1% | 7.7 min |
| 10 | forms | COMPLETE | 311 | 100 | 211 | 32.2% | 86.7 min |
| 11 | constants | COMPLETE | 47 | 3 | 44 | 6.4% | 19.9 min |
| 12 | signals | COMPLETE | 35 | 1 | 34 | 2.9% | 4.3 min |
| 13 | token_tracking | COMPLETE | 33 | 0 | 33 | 0.0% | 20.1 min |
| 14 | invitation_utils | COMPLETE | 92 | 0 | 92 | 0.0% | 41.4 min |
| 15 | pdf_export | SKIPPED | - | - | - | - | Baseline failed |
| 16 | user_data_utils | SKIPPED | - | - | - | - | Baseline failed |
| 17 | latency_utils | SKIPPED | - | - | - | - | Baseline failed |
| 18 | model_tier_manager | SKIPPED | - | - | - | - | Baseline failed |
| 19 | models | SKIPPED | - | - | - | - | Baseline failed |
| 20 | report_utils | SKIPPED | - | - | - | - | Baseline failed |
| 21 | views | SKIPPED | - | - | - | - | Too large |


---

## Error Log

| Timestamp | Module | Error | Resolution |
|-----------|--------|-------|------------|
| 03:16:43 | latency_utils | Baseline failed: ... | Skipped |
| 03:16:46 | pdf_export | Baseline failed: ... | Skipped |
| 03:16:50 | model_tier_manager | Baseline failed: ... | Skipped |
| 03:16:55 | user_data_utils | Baseline failed: ... | Skipped |
| 03:16:58 | models | Baseline failed: ... | Skipped |
| 03:17:24 | report_utils | Baseline failed: ... | Skipped |


---

## Score Distribution

| Category | Modules | Description |
|----------|---------|-------------|
| Excellent (80-100%) | 3 | ratelimit_config, permissions, job_listing_parser |
| Good (60-79%) | 2 | bias_detection, utils |
| Fair (40-59%) | 4 | openai_utils, resume_parser, serializers, audit_utils |
| Poor (20-39%) | 1 | forms |
| Critical (<20%) | 4 | constants, signals, token_tracking, invitation_utils |

---

## Analysis Summary

### Key Findings

1. **Overall Score: 45.7%** - Below the typical industry target of 60-80%
2. **Best Performers:**
   - `ratelimit_config` (100%) - Fully tested rate limiting logic
   - `permissions` (90.7%) - Strong RBAC permission testing
   - `job_listing_parser` (79.6%) - Well-tested job parsing logic

3. **Areas Needing Improvement:**
   - `invitation_utils` (0%) - No mutations killed, needs test coverage
   - `token_tracking` (0%) - No mutations killed, needs test coverage
   - `signals` (2.9%) - Nearly all mutations survived
   - `constants` (6.4%) - Configuration values largely untested

4. **Skipped Modules (6):** Baseline test failures prevented mutation testing on:
   - pdf_export, user_data_utils, latency_utils
   - model_tier_manager, models, report_utils
   - These modules need passing tests before mutation testing can run

### Recommendations

1. **Priority 1:** Add tests for `invitation_utils` and `token_tracking` (0% score)
2. **Priority 2:** Fix baseline test failures for skipped modules
3. **Priority 3:** Improve `forms` and `signals` test coverage
4. **Priority 4:** Target overall mutation score of 60%+

---

## Technical Notes

- Tool: mutmut v2.4.0
- Parallel workers: 6
- Mutation operators: Standard mutmut operators (arithmetic, comparison, boolean, etc.)
- Test runner: Django test framework via pytest

---

*Mutation testing completed 2025-12-16 04:19:52 UTC*

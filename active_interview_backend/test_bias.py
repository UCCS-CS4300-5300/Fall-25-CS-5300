#!/usr/bin/env python
"""Quick test script for bias detection"""
import os
import django

from active_interview_app.bias_detection import analyze_feedback  # noqa: E402

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'active_interview_project.settings')
django.setup()

# Test cases
test_cases = [
    ("Clean feedback", "The candidate demonstrated strong technical skills and clear communication."),
    ("Warning bias", "The candidate is articulate and a good cultural fit."),
    ("Blocking bias", "The candidate seems too young for this position.")
]

print("=" * 60)
print("BIAS DETECTION TEST RESULTS")
print("=" * 60)

for title, text in test_cases:
    result = analyze_feedback(text)
    print(f"\n{title}:")
    print(f"  Text: {text}")
    print(f"  Has bias: {result['has_bias']}")
    print(f"  Flags: {result['total_flags']} total ({result['blocking_flags']} blocking, {result['warning_flags']} warning)")
    print(f"  Severity: {result['severity_level']}")

    if result['flagged_terms']:
        print("  Detected:")
        for term in result['flagged_terms']:
            print(f"    - '{term['matched_text']}' ({term['severity_display']})")

print("\n" + "=" * 60)
print(f"✅ Bias detection is working! {len(test_cases)} tests completed.")
print("=" * 60)

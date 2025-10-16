#!/bin/bash

# Coverage validation script - requires >= 80% code coverage for all files and total

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <coverage_report_file>"
    exit 1
fi

coverage_file="$1"

if [ ! -f "$coverage_file" ]; then
    echo "Error: File '$coverage_file' not found!"
    exit 1
fi

threshold=80
failed_files=()
total_coverage=""

echo "Checking coverage threshold: >= ${threshold}%"
echo ""

# Check each file's coverage (skip header, separator lines, and TOTAL line for now)
while IFS= read -r line; do
    # Skip header and separator lines
    if [[ "$line" =~ ^Name || "$line" =~ ^-+ ]]; then
        continue
    fi

    # Extract coverage percentage (last column before "Missing" info)
    coverage=$(echo "$line" | awk '{print $(NF-1)}' | tr -d '%')
    filename=$(echo "$line" | awk '{print $1}')

    # Skip if we couldn't extract coverage (empty lines, etc.)
    if [ -z "$coverage" ] || [ -z "$filename" ]; then
        continue
    fi

    # Save TOTAL for later
    if [[ "$filename" == "TOTAL" ]]; then
        total_coverage="$coverage"
        continue
    fi

    # Check if this file meets threshold using awk for float comparison
    result=$(awk -v cov="$coverage" -v thresh="$threshold" 'BEGIN {
        if (cov >= thresh) print "PASS"; else print "FAIL"
    }')

    if [ "$result" = "FAIL" ]; then
        echo "✗ $filename: ${coverage}% < ${threshold}%"
        failed_files+=("$filename")
    else
        echo "✓ $filename: ${coverage}%"
    fi
done < "$coverage_file"

echo ""

# Check total coverage
if [ -z "$total_coverage" ]; then
    echo "Error: Could not extract TOTAL coverage from report."
    exit 1
fi

total_result=$(awk -v cov="$total_coverage" -v thresh="$threshold" 'BEGIN {
    if (cov >= thresh) print "PASS"; else print "FAIL"
}')

if [ "$total_result" = "FAIL" ]; then
    echo "✗ TOTAL coverage: ${total_coverage}% < ${threshold}%"
    failed_files+=("TOTAL")
else
    echo "✓ TOTAL coverage: ${total_coverage}%"
fi

# Final result
echo ""
if [ ${#failed_files[@]} -eq 0 ]; then
    echo "════════════════════════════════════════"
    echo "✓ All files meet ${threshold}% coverage threshold (PASS)"
    echo "════════════════════════════════════════"
    exit 0
else
    echo "════════════════════════════════════════"
    echo "✗ ${#failed_files[@]} file(s) below ${threshold}% coverage threshold (FAIL)"
    echo "════════════════════════════════════════"
    echo "Files needing attention:"
    for file in "${failed_files[@]}"; do
        echo "  - $file"
    done
    exit 1
fi


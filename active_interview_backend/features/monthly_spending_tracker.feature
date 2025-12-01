# Feature: Monthly Spending Tracker for API Services
#
# Related to:
# - Issue #10: Cost Caps & API Key Rotation
# - Issue #11: Track Monthly Spending
# - Issue #12: Set Monthly Spend Cap
#
# This feature allows administrators to monitor and control monthly API spending
# to prevent budget overruns and manage costs effectively.

@issue-11
Feature: Track Monthly Spending for ChatGPT API
  As an admin
  I want to monitor current monthly spending against the cap
  So that I can see how close we are to the limit

  Background:
    Given I am logged in as an admin
    And a monthly spending cap of $200 is configured

  @issue-11
  Scenario: View current month spending in dashboard
    Given the current month is November 2025
    And the following API calls have been made this month:
      | service | cost_usd |
      | LLM     | 75.00    |
      | LLM     | 25.00    |
      | TTS     | 10.00    |
    When I visit the observability dashboard
    Then I should see the monthly spending tracker
    And I should see the current month is "Nov 2025"
    And I should see total spending of "$110.00"
    And I should see spending cap of "$200.00"
    And I should see "$90.00" remaining
    And I should see "55.0%" of cap used

  @issue-11
  Scenario: Real-time spending tracking
    Given the current month spending is $50.00
    When a new API call is made costing $25.00
    Then the monthly spending should update to $75.00
    And the total requests count should increase by 1

  @issue-11
  Scenario: Spending resets at beginning of month
    Given it is October 31, 2025
    And current month spending is $150.00
    When the date changes to November 1, 2025
    And I make a new API call costing $10.00
    Then November spending should be $10.00
    And October spending should remain $150.00

  @issue-11
  Scenario: Breakdown by service type
    Given the following API calls have been made:
      | service | cost_usd | requests |
      | LLM     | 75.00    | 10       |
      | LLM     | 25.00    | 5        |
      | TTS     | 10.00    | 20       |
    When I view the spending breakdown
    Then I should see LLM cost of "$100.00" with "15 requests"
    And I should see TTS cost of "$10.00" with "20 requests"
    And I should see total cost of "$110.00" with "35 requests"

  @issue-12
  Scenario: Alert levels based on spending percentage
    Given a monthly spending cap of $100 is configured
    When spending reaches the following levels:
      | amount | expected_alert |
      | $40    | ok             |
      | $60    | caution        |
      | $80    | warning        |
      | $95    | critical       |
      | $105   | danger         |
    Then the dashboard should display the correct alert level for each amount

  @issue-11
  Scenario: No spending cap configured
    Given no monthly spending cap is configured
    And current month spending is $75.00
    When I view the spending tracker
    Then I should see total spending of "$75.00"
    And I should see "No cap configured" message
    And I should not see a percentage bar

  @issue-11
  Scenario: Over budget warning
    Given a monthly spending cap of $100 is configured
    And current month spending is $110.00
    When I view the spending tracker
    Then I should see "OVER CAP" warning
    And the progress bar should be red
    And I should see percentage as "110.0%"

  @issue-12
  Scenario: Administrator sets new spending cap
    Given I am an admin user
    When I run the command "python manage.py set_spending_cap 200"
    Then a new spending cap of $200 should be active
    And all previous spending caps should be inactive

  @issue-11
  Scenario: Update spending from historical data
    Given there are TokenUsage records for October 2025:
      | cost_usd |
      | 25.00    |
      | 30.00    |
      | 45.00    |
    When I run "python manage.py update_monthly_spending --month 2025-10"
    Then October 2025 spending should be $100.00
    And October 2025 should show 3 requests

  @issue-11
  Scenario: View spending history
    Given the following monthly spending history:
      | month   | total_cost |
      | 2025-09 | $125.00    |
      | 2025-10 | $150.00    |
      | 2025-11 | $110.00    |
    When I request spending history for 3 months
    Then I should receive data for 3 months
    And the data should be ordered from most recent to oldest

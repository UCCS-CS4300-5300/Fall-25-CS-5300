Feature: Latency Budget for Interview Responses
  As a candidate
  I want prompt responses (<2s median) during interviews
  So the experience feels natural

  Background:
    Given the interview system is active
    And latency logging is enabled
    And the candidate is in an active interview session

  @issue-20 @issue-54
  Scenario: Audio Q&A session with 10 questions meets latency budget
    Given an audio Q&A session is in progress
    When the user asks 10 questions during the interview
    Then 90% of responses should return in under 2 seconds
    And each response latency should be logged
    And the median response time should be less than 2 seconds

  @issue-54
  Scenario: Interview responses are delivered within performance target
    Given a candidate is conducting an interview
    When the candidate submits multiple questions
    Then 90% of responses must be delivered in under 2 seconds
    And the response time should be measured from request to completion
    And all response latencies should be recorded in the logs

  @issue-54
  Scenario: Response latency is logged for performance tracking
    Given an interview session is active
    When a candidate submits a question
    And the system generates a response
    Then the response latency should be logged with a timestamp
    And the log should include the question ID
    And the log should include the response generation time
    And the log should be stored in a queryable format

  @issue-54
  Scenario: Automated alerts trigger when latency exceeds threshold
    Given the latency monitoring system is active
    And the acceptable latency threshold is 2 seconds
    When a response takes longer than 2 seconds to generate
    Then an automated alert should be triggered
    And the alert should include the latency value
    And the alert should include the session ID
    And the alert should include the timestamp

  @issue-20 @issue-54
  Scenario: System maintains fast responses under normal load
    Given multiple interview sessions are active
    And the system is under normal load conditions
    When candidates submit questions across different sessions
    Then the system should maintain sub-2-second response times for 90% of requests
    And response times should be tracked independently per session
    And aggregate metrics should be available for analysis

  @issue-54
  Scenario: Latency metrics are available for performance analysis
    Given interview sessions have been completed
    And latency data has been logged
    When retrieving latency metrics for analysis
    Then the system should provide p50 (median) latency
    And the system should provide p90 latency
    And the system should provide p95 latency
    And the metrics should be filterable by time range
    And the metrics should be filterable by session type

  @issue-20 @issue-54
  Scenario: Slow responses are identified and tracked
    Given latency logging is active
    When a response takes longer than 2 seconds
    Then the slow response should be flagged in the logs
    And the response should include detailed timing breakdown
    And the timing data should identify bottlenecks (AI processing, database, etc.)
    And the slow response data should be retained for troubleshooting

  @issue-54
  Scenario: Alert threshold is configurable for different interview types
    Given different interview types may have different latency requirements
    When configuring latency thresholds
    Then administrators should be able to set custom thresholds per interview type
    And alerts should respect the configured thresholds
    And threshold changes should not require system restart

  @issue-20 @issue-54
  Scenario: Interview experience feels natural with fast responses
    Given a candidate is participating in a real-time interview
    When the candidate completes a full interview with 15 questions
    Then at least 13 responses (90%) should be delivered in under 2 seconds
    And no response should take longer than 5 seconds
    And the candidate should not experience noticeable delays
    And the conversation flow should feel natural and uninterrupted

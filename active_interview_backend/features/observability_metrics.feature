Feature: Observability Metrics Collection
  As a system
  I want to collect and store metrics data (RPS, latency, error rates, provider costs)
  So that historical performance data is available for analysis

  Background:
    Given the metrics collection system is active
    And the database is initialized

  @issue-14 @issue-15
  Scenario: Track requests per second across all endpoints
    Given the application is receiving traffic
    When multiple requests are made to different endpoints
    Then the system should record each request with timestamp
    And the system should track requests per endpoint
    And the request metrics should be stored in the database

  @issue-14 @issue-15
  Scenario: Collect response times and calculate percentiles
    Given the application is processing requests
    When requests complete with varying response times
    Then the system should record each response time
    And the system should be able to calculate p50 latency
    And the system should be able to calculate p95 latency
    And percentile calculations should be accurate within 1ms

  @issue-14 @issue-15
  Scenario: Record error rates by type and endpoint
    Given the application is receiving requests
    When some requests result in 4xx errors
    And some requests result in 5xx errors
    And some requests succeed with 2xx status
    Then the system should record error status codes
    And the system should track errors by endpoint
    And the system should differentiate between 4xx and 5xx errors

  @issue-14 @issue-15
  Scenario: Store daily provider spending by service
    Given the application is using external AI services
    When API calls are made to OpenAI
    And API calls are made to other providers
    Then the system should aggregate costs by provider per day
    And the system should track costs by service type
    And daily cost summaries should be queryable

  @issue-14 @issue-15
  Scenario: Retain historical data for at least 30 days
    Given metrics data has been collected for 60 days
    When the data retention cleanup runs
    Then metrics older than 30 days should be deleted
    And metrics within the last 30 days should be preserved
    And the cleanup should run without errors

  @issue-14 @issue-15
  Scenario: Query metrics for time-based analysis
    Given metrics data exists for multiple time periods
    When querying metrics for a specific date range
    Then the system should return only metrics within that range
    And the results should be ordered by timestamp
    And the query should complete efficiently with indexes

  @issue-14 @issue-15
  Scenario: Calculate requests per second for an endpoint
    Given 100 requests were made to "/api/chat/" in 10 seconds
    When calculating RPS for that endpoint
    Then the RPS should be 10.0 requests per second
    And the calculation should account for the time window

  @issue-14 @issue-15
  Scenario: Track middleware performance overhead
    Given the metrics middleware is active
    When requests are processed through the middleware
    Then the middleware overhead should be minimal (< 5ms)
    And the middleware should not block request processing
    And the middleware should handle exceptions gracefully

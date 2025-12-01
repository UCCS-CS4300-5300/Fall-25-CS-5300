# Feature: Automatic API Key Rotation
#
# Related to:
# - Issue #10: Cost Caps & API Key Rotation
# - Issue #13: Automatic API Key Rotation
#
# This feature allows administrators to automatically rotate API keys on a schedule
# to maintain security without manual intervention.

@issue-13
Feature: Automatic API Key Rotation
  As an admin
  I want to automatically rotate API keys on a schedule
  So that we maintain security without manual intervention

  Background:
    Given I am logged in as an admin
    And the following API keys are in the pool for "openai":
      | key_name         | status   | added_at            |
      | Production Key 1 | active   | 2025-11-01 10:00:00 |
      | Production Key 2 | pending  | 2025-11-02 10:00:00 |
      | Production Key 3 | pending  | 2025-11-03 10:00:00 |

  @issue-13
  Scenario: Manual key rotation
    Given I have an active key "Production Key 1"
    When I run the command "python manage.py rotate_api_keys --force"
    Then "Production Key 1" should be deactivated
    And "Production Key 2" should be activated
    And a rotation log should be created with status "success"
    And the rotation type should be "manual"

  @issue-13
  Scenario: Scheduled weekly rotation
    Given a rotation schedule is configured:
      | provider | enabled | frequency | last_rotation_at    |
      | openai   | true    | weekly    | 2025-11-01 10:00:00 |
    And the current date is "2025-11-08 10:00:00"
    When I run the command "python manage.py rotate_api_keys"
    Then the rotation should occur
    And the next rotation should be scheduled for "2025-11-15"

  @issue-13
  Scenario: Scheduled monthly rotation
    Given a rotation schedule is configured:
      | provider | enabled | frequency | last_rotation_at    |
      | openai   | true    | monthly   | 2025-10-15 10:00:00 |
    And the current date is "2025-11-16 10:00:00"
    When I run the command "python manage.py rotate_api_keys"
    Then the rotation should occur
    And the next rotation should be scheduled for approximately "2025-12-15"

  @issue-13
  Scenario: Rotation not due yet
    Given a rotation schedule is configured:
      | provider | enabled | frequency | last_rotation_at    |
      | openai   | true    | weekly    | 2025-11-01 10:00:00 |
    And the current date is "2025-11-03 10:00:00"
    When I run the command "python manage.py rotate_api_keys"
    Then the rotation should not occur
    And I should see message "Rotation not due yet"
    And the next rotation date should be displayed

  @issue-13
  Scenario: Rotation disabled in schedule
    Given a rotation schedule is configured:
      | provider | enabled | frequency | last_rotation_at    |
      | openai   | false   | weekly    | 2025-11-01 10:00:00 |
    And the current date is "2025-11-15 10:00:00"
    When I run the command "python manage.py rotate_api_keys"
    Then the rotation should not occur
    And I should see message "Automatic rotation is disabled"

  @issue-13
  Scenario: Force rotation when disabled
    Given a rotation schedule is configured:
      | provider | enabled | frequency |
      | openai   | false   | weekly    |
    When I run the command "python manage.py rotate_api_keys --force"
    Then the rotation should occur
    And a rotation log should be created

  @issue-13
  Scenario: Dry run mode
    Given I have an active key "Production Key 1"
    When I run the command "python manage.py rotate_api_keys --force --dry-run"
    Then I should see message "DRY RUN"
    And I should see what key would be activated
    And "Production Key 1" should still be active
    And "Production Key 2" should still be pending
    And no rotation log should be created

  @issue-13
  Scenario: No keys available for rotation
    Given all keys in the pool are:
      | key_name         | status   |
      | Production Key 1 | active   |
      | Production Key 2 | revoked  |
      | Production Key 3 | revoked  |
    When I run the command "python manage.py rotate_api_keys --force"
    Then the rotation should fail
    And I should see error "No keys available for rotation"
    And a failed rotation log should be created
    And "Production Key 1" should still be active

  @issue-13
  Scenario: Round-robin rotation order
    Given the following keys exist:
      | key_name         | status   | added_at            |
      | Production Key 1 | active   | 2025-11-01 10:00:00 |
      | Production Key 2 | pending  | 2025-11-02 10:00:00 |
      | Production Key 3 | pending  | 2025-11-03 10:00:00 |
    When I rotate keys 3 times
    Then the activation order should be:
      | rotation | activated_key    |
      | 1        | Production Key 2 |
      | 2        | Production Key 3 |
      | 3        | Production Key 1 |

  @issue-13
  Scenario: Rotation updates schedule timestamps
    Given a rotation schedule exists for "openai"
    And last_rotation_at is "2025-11-01 10:00:00"
    And next_rotation_at is "2025-11-08 10:00:00"
    When I run a successful rotation at "2025-11-08 10:00:00"
    Then last_rotation_at should be "2025-11-08 10:00:00"
    And next_rotation_at should be approximately "2025-11-15 10:00:00"

  @issue-13
  Scenario: Multiple providers rotate independently
    Given the following keys exist for "openai":
      | key_name      | status  |
      | OpenAI Key 1  | active  |
      | OpenAI Key 2  | pending |
    And the following keys exist for "anthropic":
      | key_name         | status  |
      | Anthropic Key 1  | active  |
      | Anthropic Key 2  | pending |
    When I rotate keys for "openai"
    Then "OpenAI Key 2" should be activated
    And "Anthropic Key 1" should still be active

  @issue-13
  Scenario: Rotation creates audit log entry
    Given I have an active key "Production Key 1"
    When I run the command "python manage.py rotate_api_keys --force"
    Then a rotation log should exist with:
      | field            | value            |
      | provider         | openai           |
      | old_key_masked   | sk-*...          |
      | new_key_masked   | sk-*...          |
      | status           | success          |
      | rotation_type    | manual           |

  @issue-13
  Scenario: Failed rotation creates error log
    Given no pending keys are available
    When I attempt to rotate keys
    Then a rotation log should exist with:
      | field            | value                          |
      | status           | failed                         |
      | error_message    | No keys available for rotation |

  @issue-13
  Scenario: Rotation logs are immutable
    Given a rotation log exists
    When I attempt to delete the rotation log via admin
    Then the deletion should be prevented
    And the rotation log should still exist

  @issue-13
  Scenario: Key encryption and decryption
    Given I add a new key with value "sk-test-1234567890abcdef"
    When the key is stored in the database
    Then the key should be encrypted
    And the encrypted value should not match the original
    When the key is retrieved for use
    Then the decrypted value should match "sk-test-1234567890abcdef"

  @issue-13
  Scenario: Key masking for security
    Given I have a key with value "sk-proj-abc123xyz789def456"
    When I view the key in the admin interface
    Then I should see a masked version like "sk-proj-abc...456"
    And I should not see the full key value

  @issue-13
  Scenario: Usage tracking per key
    Given I have an active key "Production Key 1"
    And the key has usage_count of 0
    When the key is used 5 times for API calls
    Then the usage_count should be 5
    And last_used_at should be recently updated

  @issue-13
  Scenario: OpenAI client refreshes on key change
    Given the OpenAI client is using "Production Key 1"
    When a key rotation occurs to "Production Key 2"
    And I make a new API call
    Then the OpenAI client should use "Production Key 2"
    And the API call should succeed

  @issue-13
  Scenario: Fallback to environment variable
    Given no keys are active in the pool
    And OPENAI_API_KEY environment variable is set to "sk-env-fallback"
    When I get the API key
    Then the system should return "sk-env-fallback"
    And the source should be "environment"

  @issue-13
  Scenario: Key pool takes precedence over environment
    Given an active key "Production Key 1" exists in pool
    And OPENAI_API_KEY environment variable is set to "sk-env-fallback"
    When I get the API key
    Then the system should return the pool key
    And the source should be "key_pool"
    And the usage_count for "Production Key 1" should increment

  @issue-13
  Scenario: Add key via Django admin
    Given I am on the Django admin API Key Pool page
    When I add a new key with:
      | field     | value            |
      | provider  | openai           |
      | key_name  | New Test Key     |
      | api_key   | sk-new-key-12345 |
      | status    | pending          |
    Then the key should be saved with encrypted value
    And the key_prefix should be extracted
    And added_by should be set to current admin user

  @issue-13
  Scenario: Configure rotation schedule via admin
    Given I am on the Django admin Key Rotation Schedules page
    When I configure a schedule with:
      | field                | value              |
      | provider             | openai             |
      | is_enabled           | true               |
      | rotation_frequency   | weekly             |
      | notification_email   | admin@example.com  |
      | notify_on_rotation   | true               |
    Then the schedule should be saved
    And created_by should be set to current admin user

  @issue-13
  Scenario: View rotation history in admin
    Given the following rotations have occurred:
      | date                | old_key          | new_key          | status  |
      | 2025-11-01 10:00:00 | Production Key 1 | Production Key 2 | success |
      | 2025-11-08 10:00:00 | Production Key 2 | Production Key 3 | success |
      | 2025-11-15 10:00:00 | Production Key 3 | Production Key 1 | success |
    When I view the Key Rotation Logs in admin
    Then I should see 3 rotation logs
    And they should be ordered from newest to oldest
    And each log should show masked key values

  @issue-13
  Scenario: Key status transitions
    Given I have a key "Test Key" with status "pending"
    When I activate the key
    Then the status should change to "active"
    And activated_at should be set
    When the key is rotated out
    Then the status should change to "inactive"
    And deactivated_at should be set

  @issue-13
  Scenario: Quarterly rotation frequency
    Given a rotation schedule is configured:
      | provider | enabled | frequency  | last_rotation_at    |
      | openai   | true    | quarterly  | 2025-11-01 10:00:00 |
    When the schedule calculates next rotation
    Then the next rotation should be approximately 90 days later
    And next_rotation_at should be around "2025-01-30"

  @issue-13
  Scenario: Display key pool status after rotation
    Given I have 3 keys in the pool
    When I run the command "python manage.py rotate_api_keys --force"
    Then I should see "Key Pool Status" in the output
    And I should see status for each key
    And I should see usage counts for each key

  @issue-13
  Scenario: Rotation with notes
    When I rotate keys with notes "Scheduled weekly rotation"
    Then the rotation log should have notes "Scheduled weekly rotation"

  @issue-13
  Scenario: Get current key info for monitoring
    Given "Production Key 1" is active with 42 uses
    When I call get_current_api_key_info()
    Then I should receive:
      | field         | value            |
      | key_name      | Production Key 1 |
      | masked_key    | sk-*...          |
      | usage_count   | 42               |
      | source        | key_pool         |

@issue-63
Feature: GDPR/CCPA Data Export & Delete
  As a candidate
  I want to export or delete my data
  So that I can control my privacy and exercise my data rights

  Background:
    Given the application is running
    And I am a registered user
    And I am logged in
    And I have personal data stored in the system

  @issue-64
  Scenario: Access data export option from user profile
    Given I am on my user profile page
    When I navigate to the settings section
    Then I should see an "Export my data" button

  @issue-64
  Scenario: Request data export
    Given I am on my user profile settings
    When I click the "Export my data" button
    Then a data export request should be initiated
    And I should see a confirmation message
    And I should be notified that I will receive an email when the export is ready

  @issue-64
  Scenario: Data export includes all personal data
    Given I have requested a data export
    When the export is processed
    Then the export should include my profile information
    And the export should include my interview transcripts
    And the export should include my scores
    And the export should include my feedback
    And the export should include my uploaded resumes

  @issue-64
  Scenario: Data export delivered as downloadable ZIP file
    Given my data export request has been processed
    When the export is ready
    Then a ZIP file should be generated
    And the ZIP should contain data in JSON format
    And the ZIP should contain data in CSV format
    And the ZIP should be available for download

  @issue-64
  Scenario: Export processing completes within time limit
    Given I have typical dataset size
    When I request a data export
    Then the export should be completed within 5 minutes

  @issue-64
  Scenario: Email notification when export is ready
    Given I have requested a data export
    When the export processing is complete
    Then I should receive an email notification
    And the email should contain a download link
    And the download link should be active

  @issue-64
  Scenario: Export link expires after 7 days
    Given I have received an export download link
    And the link was generated 7 days ago
    When I try to access the download link
    Then the link should be expired
    And I should see an error message
    And I should be able to request a new export

  @issue-64
  Scenario: Download data export package
    Given my data export is ready
    And I have received the download link via email
    When I click the download link
    Then the ZIP file should download to my device
    And the filename should contain "data_export"
    And the filename should contain my user identifier
    And the filename should contain a timestamp

  @issue-65
  Scenario: Access data deletion option from user profile
    Given I am on my user profile page
    When I navigate to the settings section
    Then I should see a "Delete my data" option

  @issue-65
  Scenario: Request data deletion with confirmation dialog
    Given I am on my user profile settings
    When I click the "Delete my data" option
    Then a confirmation dialog should appear
    And the dialog should warn me about permanent deletion
    And the dialog should have "Cancel" and "Confirm Delete" buttons

  @issue-65
  Scenario: Cancel data deletion request
    Given I have clicked "Delete my data"
    And the confirmation dialog is displayed
    When I click "Cancel"
    Then the dialog should close
    And no data should be deleted
    And I should remain on my profile settings page

  @issue-65
  Scenario: Confirm data deletion request
    Given I have clicked "Delete my data"
    And the confirmation dialog is displayed
    When I click "Confirm Delete"
    Then my data deletion request should be processed
    And I should see a confirmation message

  @issue-65
  Scenario: Hard deletion of personal information
    Given I have confirmed my data deletion request
    When the deletion is processed
    Then my profile information should be completely removed
    And my contact details should be completely removed
    And my resume materials should be completely removed
    And my audio recordings should be completely removed

  @issue-65
  Scenario: Soft deletion with anonymization of interview data
    Given I have confirmed my data deletion request
    When the deletion is processed
    Then my interview scores should be retained for analytics
    But the interview scores should be anonymized
    And all personally identifiable information should be removed from interview records
    And interview data should not be linkable to me

  @issue-65
  Scenario: Audit trail for deletion requests
    Given I have confirmed my data deletion request
    When the deletion is processed
    Then the deletion request should be logged in the audit system
    And the audit log should contain the deletion timestamp
    And the audit log should contain the anonymized user identifier

  @issue-65
  Scenario: Email confirmation upon deletion completion
    Given I have requested data deletion
    When the deletion is successfully completed
    Then I should receive a confirmation email
    And the email should confirm that my data has been deleted
    And the email should explain what data was retained for legal compliance

  @issue-65
  Scenario: Deleted accounts are permanently unrecoverable
    Given my data has been deleted
    When I try to log in with my previous credentials
    Then I should not be able to access the account
    And I should see a message that the account no longer exists
    And there should be no way to recover the deleted data

  @issue-65
  Scenario: Minimal data retention for legal compliance
    Given my data deletion has been completed
    When I check what data is retained
    Then only anonymized user identifiers should be retained
    And only deletion timestamps should be retained
    And no other personally identifiable information should be retained
    And retained data should meet legal compliance requirements

  @issue-63
  Scenario: Access both export and delete options
    Given I am on my user profile settings
    Then I should see both "Export my data" and "Delete my data" options
    And both options should be clearly labeled
    And each option should have explanatory text

  @issue-63
  Scenario: Export data before deletion
    Given I want to delete my account
    When I am on my user profile settings
    Then I should be able to export my data first
    And then proceed with deletion after export completes

  @issue-64
  Scenario: Multiple export requests
    Given I have previously requested a data export
    When I request another data export
    Then a new export should be generated
    And the new export should contain the most current data
    And previous export links should remain valid until their expiration

  @issue-65
  Scenario: Access control after deletion
    Given another user tries to access my profile
    And my data has been deleted
    When they search for my profile
    Then they should not find any of my personal information
    And they should not be able to view my interview details

  @issue-64
  Scenario: Export request for user with no data
    Given I am a new user with minimal data
    When I request a data export
    Then the export should still be generated
    And the export should contain any available data
    And empty sections should be clearly marked

  @issue-65
  Scenario: Deletion request validation
    Given I am logged in
    When I request data deletion
    Then the system should verify my identity
    And the system should validate my authorization to delete the account
    And the deletion should only proceed if validation passes

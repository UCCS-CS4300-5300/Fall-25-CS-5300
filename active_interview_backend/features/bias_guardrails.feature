@issue-18
Feature: Bias Guardrails for Interview Feedback
  As an admin
  I want bias-term detection in feedback
  So that reports avoid discriminatory language

  Background:
    Given the application is running
    And the bias term library is populated with common bias terms
    And I am logged in as an interviewer

  @issue-18 @issue-57
  Scenario: Flagged bias terms are highlighted in feedback editor
    Given I am reviewing a completed interview invitation
    And I navigate to the feedback form
    When I type "He is a cultural fit for the team" in the feedback field
    Then the term "cultural fit" should be highlighted
    And I should see a visual indicator for the flagged term

  @issue-18 @issue-57
  Scenario: Tooltip explains why term is flagged
    Given I am reviewing a completed interview invitation
    And I have typed "She seems too old for this role" in the feedback field
    And the term "too old" is highlighted
    When I hover over the highlighted term "too old"
    Then I should see a tooltip
    And the tooltip should contain "Age-related language"
    And the tooltip should explain why the term is problematic

  @issue-18 @issue-57
  Scenario: Multiple bias terms are all highlighted
    Given I am reviewing a completed interview invitation
    When I type "He is young and energetic, a real culture fit" in the feedback field
    Then the term "young" should be highlighted
    And the term "culture fit" should be highlighted
    And each term should have its own category indicator

  @issue-18 @issue-58
  Scenario: Neutral phrasing suggestions appear for flagged terms
    Given I am reviewing a completed interview invitation
    And I have typed "He is a cultural fit" in the feedback field
    And the term "cultural fit" is highlighted
    When I click on the highlighted term "cultural fit"
    Then I should see a suggestions modal
    And the modal should contain neutral alternatives:
      | suggestion                        |
      | team collaboration skills         |
      | alignment with company values     |
      | working style compatibility       |

  @issue-18 @issue-58
  Scenario: Admin can accept a suggested neutral phrase
    Given I am reviewing a completed interview invitation
    And I have typed "She is a cultural fit" in the feedback field
    And the suggestions modal is showing alternatives for "cultural fit"
    When I click "Accept" on the suggestion "alignment with company values"
    Then the feedback text should be updated to "She has alignment with company values"
    And the term "cultural fit" should no longer be highlighted
    And the suggestions modal should close

  @issue-18 @issue-58
  Scenario: Admin can manually edit flagged terms
    Given I am reviewing a completed interview invitation
    And I have typed "He is too young for this position" in the feedback field
    And the term "too young" is highlighted
    When I manually replace "too young" with "requires more experience"
    Then the term "too young" should no longer be highlighted
    And the feedback should be considered clean

  @issue-18 @issue-59
  Scenario: Save is blocked when biased feedback contains high-severity terms
    Given I am reviewing a completed interview invitation
    And I have typed "She is too old and not a culture fit" in the feedback field
    And the feedback contains flagged terms
    When I click "Save Feedback"
    Then the save operation should be blocked
    And I should see an error message "Your feedback contains bias terms that must be resolved"
    And the feedback should not be saved to the database

  @issue-18 @issue-59
  Scenario: Save succeeds after all flagged terms are resolved
    Given I am reviewing a completed interview invitation
    And I have typed "He is a cultural fit" in the feedback field
    And I resolved the flagged term by replacing it with "has strong collaboration skills"
    And the feedback is now clean
    When I click "Save Feedback"
    Then the save operation should succeed
    And I should see a confirmation message "Feedback saved successfully"
    And the feedback should be saved to the database

  @issue-18 @issue-59
  Scenario: Confirmation shown when clean feedback is saved
    Given I am reviewing a completed interview invitation
    When I type "Candidate demonstrated strong technical skills and clear communication" in the feedback field
    And the feedback contains no flagged terms
    And I click "Save Feedback"
    Then the save operation should succeed
    And I should see a success message "Clean feedback saved successfully"
    And a green checkmark icon should be displayed

  @issue-18 @issue-59
  Scenario: Mark as reviewed is blocked with unresolved bias terms
    Given I am reviewing a completed interview invitation
    And I have typed "She is young but talented" in the feedback field
    And the term "young" is flagged
    When I click "Mark as Reviewed & Notify Candidate"
    Then the operation should be blocked
    And I should see an error message "Cannot notify candidate with biased feedback. Please resolve all flagged terms."
    And the interview should remain in "Pending Review" status
    And no email should be sent to the candidate

  @issue-18 @issue-59
  Scenario: Mark as reviewed succeeds with clean feedback
    Given I am reviewing a completed interview invitation
    And I have typed "Candidate showed excellent problem-solving abilities" in the feedback field
    And the feedback contains no flagged terms
    When I click "Mark as Reviewed & Notify Candidate"
    Then the operation should succeed
    And the interview status should change to "Review Complete"
    And the candidate should receive an email notification
    And I should see "Review completed and candidate notified"

  @issue-18
  Scenario: Bias detection categorizes terms correctly
    Given I am reviewing a completed interview invitation
    When I type feedback containing various bias categories:
      | feedback_text                          | expected_category    |
      | She is too old for this role          | age                  |
      | He is not a cultural fit              | other                |
      | She seems pregnant                    | family               |
      | He is overweight                      | appearance           |
      | She has a heavy accent                | race                 |
      | He seems disabled                     | disability           |
    Then each term should be flagged with the correct category
    And each category should have a distinct visual indicator

  @issue-18
  Scenario: Bias detection uses pattern matching for variations
    Given I am reviewing a completed interview invitation
    When I type feedback with variations of the same bias term:
      | feedback_text                          |
      | cultural fit                           |
      | culture fit                            |
      | fits our culture                       |
      | good culture match                     |
    Then all variations should be detected and flagged
    And all should show the same category and explanation

  @issue-18
  Scenario: Real-time highlighting as interviewer types
    Given I am reviewing a completed interview invitation
    And the feedback field is empty
    When I type "She is " (no flagged terms yet)
    Then no terms should be highlighted
    When I continue typing "She is too young"
    Then the term "too young" should be highlighted immediately
    And the highlighting should occur without page refresh

  @issue-18 @issue-57
  Scenario: Severity levels affect visual presentation
    Given I am reviewing a completed interview invitation
    And the bias term library has terms with different severity levels
    When I type "He is young" (severity: warning)
    Then the term "young" should be highlighted in yellow
    When I type "She is pregnant" (severity: block)
    Then the term "pregnant" should be highlighted in red
    And the save button should be disabled for blocking terms

  @issue-18 @issue-58
  Scenario: Suggestions modal shows context-appropriate alternatives
    Given I am reviewing a completed interview invitation
    And I have typed "He is too old for this fast-paced environment" in the feedback field
    When I click on the flagged term "too old"
    Then the suggestions modal should show:
      | suggestion                                           |
      | may benefit from additional training in new tools    |
      | demonstrated thoughtful, methodical approach         |
      | brings extensive experience to the role              |
    And suggestions should maintain the sentence context

  @issue-18
  Scenario: Admin can view bias detection statistics
    Given I am an admin
    And multiple interviewers have submitted feedback
    And some feedback contained flagged bias terms
    When I navigate to the bias analysis dashboard
    Then I should see statistics:
      | metric                          | value |
      | Total feedback analyzed         | 150   |
      | Feedback with bias flags        | 23    |
      | Most common bias category       | other |
      | Bias detection rate             | 15.3% |
    And I should see a breakdown by category

  @issue-18
  Scenario: Bias term library can be updated by admin
    Given I am logged in as an admin
    When I navigate to the bias term library admin page
    Then I should see a list of all bias terms
    And I should be able to add new terms
    And I should be able to edit existing terms
    And I should be able to activate/deactivate terms
    And I should be able to set severity levels

  @issue-18
  Scenario: Existing feedback is not retroactively flagged in database
    Given an interviewer submitted feedback "He is young" before bias detection was implemented
    And the feedback was saved to the database
    When I view the historical feedback
    Then the feedback should be displayed as-is
    And it should not be modified or blocked
    But it should show a badge indicating "Submitted before bias detection"

  @issue-18
  Scenario: Feedback with only low-severity warnings can be saved with acknowledgment
    Given I am reviewing a completed interview invitation
    And I have typed feedback with only warning-level terms (not blocking)
    When I click "Save Feedback"
    Then I should see a warning dialog "Your feedback contains potential bias indicators. Are you sure you want to save?"
    And I should have options:
      | option                    |
      | Review and Edit           |
      | Save Anyway               |
    When I click "Save Anyway"
    Then the feedback should be saved with a flag indicating "saved_with_warnings"

  @issue-18
  Scenario: Bias detection respects context and avoids false positives
    Given I am reviewing a completed interview invitation
    When I type feedback with legitimate non-biased uses of flagged words:
      | feedback_text                                                    |
      | Candidate demonstrated cultural awareness when discussing global markets |
      | Strong fit for the technical requirements outlined in the job description |
    Then these terms should not be flagged
    And the feedback should be considered clean

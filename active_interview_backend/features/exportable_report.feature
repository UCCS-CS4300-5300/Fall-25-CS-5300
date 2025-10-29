@issue-1
Feature: Exportable Interview Report
  As a job seeker
  I want to generate and download professional interview reports
  So that I can share my interview performance with potential employers

  Background:
    Given the application is running
    And I am a registered user
    And I am logged in
    And I have completed an interview chat session

  @issue-1
  Scenario: Generate report from completed interview
    Given I am on the interview results page for my completed chat
    When I click the "Generate Report" button
    Then a report should be created from my interview data
    And I should be redirected to the export report view
    And I should see my interview performance scores
    And I should see AI-generated feedback

  @issue-1
  Scenario: View report details before downloading
    Given I have generated a report for my interview
    And I am on the export report page
    Then I should see the interview metadata
    And I should see my professionalism score out of 100
    And I should see my subject knowledge score out of 100
    And I should see my clarity score out of 100
    And I should see my overall score out of 100
    And I should see the AI feedback text
    And I should see a preview of my questions and responses
    And I should see interview statistics

  @issue-3
  Scenario: Download interview report as PDF
    Given I have generated a report for my interview
    And I am on the export report page
    When I click the "Download as PDF" button
    Then a PDF file should be generated
    And the PDF should download to my device
    And the filename should contain "interview_report"
    And the filename should contain the chat title
    And the filename should contain a timestamp

  @issue-3
  Scenario: PDF report contains all sections
    Given I have generated a report for my interview
    When I download the PDF report
    Then the PDF should contain a title section with the interview name
    And the PDF should contain interview metadata details
    And the PDF should contain performance scores with ratings
    And the PDF should contain AI feedback
    And the PDF should contain question and response analysis
    And the PDF should contain interview statistics
    And the PDF should contain a generation timestamp footer

  @issue-1
  Scenario: Report shows correct performance ratings
    Given I have an interview with professionalism score of 85
    And I have subject knowledge score of 90
    And I have clarity score of 78
    And I have overall score of 84
    When I view the report
    Then the professionalism score should show "Good" rating
    And the subject knowledge score should show "Excellent" rating
    And the clarity score should show "Good" rating
    And the overall score should show "Good" rating

  @issue-1
  Scenario: Report includes detailed question responses
    Given my interview has 10 questions asked
    And I have provided 10 responses
    When I view the report
    Then I should see all 10 questions listed
    And each question should show my answer
    And each question should show a score out of 10
    And each question should show individual feedback

  @issue-1
  Scenario: Access control - only owner can view report
    Given another user has completed an interview
    And a report has been generated for their interview
    When I try to access their report page
    Then I should be denied access
    And I should see an error message

  @issue-3
  Scenario: Access control - only owner can download PDF
    Given another user has completed an interview
    And a report has been generated for their interview
    When I try to download their PDF report
    Then the download should be denied
    And I should see an error message

  @issue-1
  Scenario: Update existing report
    Given I have already generated a report for my interview
    And I click "Generate Report" again
    Then the existing report should be updated
    And I should see the latest interview data
    And the report's last_updated timestamp should be current

  @issue-1
  Scenario: Report generation with all interview types
    Given I have completed a "<interview_type>" interview
    When I generate a report
    Then the report should display the interview type as "<interview_type>"
    And the report should be generated successfully

    Examples:
      | interview_type    |
      | General          |
      | Skills           |
      | Personality      |
      | Final Screening  |

  @issue-1
  Scenario: Report generation with difficulty levels
    Given I have completed an interview with difficulty level <level>
    When I generate a report
    Then the report should show difficulty level <level>
    And the report should be generated successfully

    Examples:
      | level |
      | 1     |
      | 5     |
      | 10    |

  @issue-1
  Scenario: Report with job position and resume
    Given I have uploaded a resume for my interview
    And I have specified a job position
    When I generate a report
    Then the report should show the job position
    And the report should indicate a resume was uploaded

  @issue-1
  Scenario: Navigate back from report page
    Given I am viewing an exported report
    When I click the "Back to Results" button
    Then I should be redirected to the interview results page

  @issue-1
  Scenario: Report generation extracts scores from chat messages
    Given my interview chat contains messages with score patterns
    And the messages include "8/10" ratings
    And the messages include "Professionalism: 85/100"
    When I generate a report
    Then the report should extract and store these scores
    And the scores should be displayed correctly

  @issue-1
  Scenario: Report handles missing data gracefully
    Given my interview has no explicit score data
    When I generate a report
    Then the report should still be generated
    And default values should be used for missing scores
    And the report should display available information

  @issue-1
  Scenario: Report shows interview statistics
    Given my interview has 15 questions asked
    And I have provided 14 responses
    When I view the report
    Then the statistics should show "15" total questions
    And the statistics should show "14" total responses

  @issue-3
  Scenario: PDF report has professional styling
    Given I have generated a report
    When I download the PDF
    Then the PDF should have a clean, professional layout
    And the PDF should use consistent branding colors
    And the PDF should have proper page breaks
    And tables should have alternating row colors
    And section headers should be clearly visible

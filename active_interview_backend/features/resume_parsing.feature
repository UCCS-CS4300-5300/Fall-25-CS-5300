@issue-48 @issue-49 @issue-50
Feature: Resume Upload with AI Parsing
  As a job seeker
  I want to upload my resume and have it automatically parsed by AI
  So that I don't have to manually enter my skills, experience, and education

  Background:
    Given the application is running
    And I am a registered user
    And I am logged in
    And the OpenAI API is configured

  @issue-48
  Scenario: Upload PDF resume successfully
    Given I am on the document upload page
    When I upload a valid PDF resume file
    Then the resume should be saved to the database
    And I should see "Resume uploaded and parsed successfully"
    And the resume parsing status should be "success"

  @issue-49
  Scenario: AI successfully extracts skills from resume
    Given I have uploaded a resume with skills listed
    When the AI parsing completes
    Then the resume should have skills extracted
    And the skills list should contain technical skills
    And the skills list should contain soft skills
    And the skills should be stored in JSON format

  @issue-49
  Scenario: AI successfully extracts work experience from resume
    Given I have uploaded a resume with work history
    When the AI parsing completes
    Then the resume should have experience extracted
    And each experience entry should have a company name
    And each experience entry should have a job title
    And each experience entry should have duration
    And each experience entry should have a description
    And the experience should be stored in JSON format

  @issue-49
  Scenario: AI successfully extracts education from resume
    Given I have uploaded a resume with education information
    When the AI parsing completes
    Then the resume should have education extracted
    And each education entry should have an institution
    And each education entry should have a degree
    And each education entry should have a field of study
    And each education entry should have a graduation year
    And the education should be stored in JSON format

  @issue-50
  Scenario: View parsed resume data on profile page
    Given I have uploaded a resume that was successfully parsed
    When I navigate to my profile page
    Then I should see my extracted skills
    And I should see my work experience
    And I should see my education history
    And the data should be clearly formatted and readable

  @issue-50
  Scenario: Edit parsed skills on profile
    Given I have a resume with parsed skills
    And I am on my profile page
    When I edit my skills list
    And I add a new skill
    And I remove an existing skill
    And I save the changes
    Then my updated skills should be saved
    And I should see a success message
    And the changes should persist when I refresh the page

  @issue-50
  Scenario: Edit parsed work experience on profile
    Given I have a resume with parsed work experience
    And I am on my profile page
    When I edit a work experience entry
    And I update the job title
    And I modify the description
    And I save the changes
    Then my updated experience should be saved
    And I should see a success message
    And the changes should persist when I refresh the page

  @issue-50
  Scenario: Edit parsed education on profile
    Given I have a resume with parsed education
    And I am on my profile page
    When I edit an education entry
    And I update the degree information
    And I save the changes
    Then my updated education should be saved
    And I should see a success message
    And the changes should persist when I refresh the page

  @issue-48 @issue-49
  Scenario: Handle parsing error gracefully when AI is unavailable
    Given the OpenAI API is unavailable
    When I upload a PDF resume file
    Then the resume should still be saved to the database
    And I should see "Resume uploaded but AI parsing is currently unavailable"
    And the resume parsing status should be "error"
    And the resume parsing error should be "AI service unavailable"

  @issue-48 @issue-49
  Scenario: Handle parsing error when OpenAI returns invalid response
    Given the OpenAI API returns invalid JSON
    When I upload a PDF resume file
    Then the resume should still be saved to the database
    And I should see "Resume uploaded but parsing failed"
    And the resume parsing status should be "error"
    And the resume parsing error should contain "parsing failed"

  @issue-48
  Scenario: Reject unsupported file formats
    Given I am on the document upload page
    When I attempt to upload a .exe file
    Then I should see an error message "Invalid filetype"
    And the file should not be saved
    And no parsing should be attempted

  @issue-48
  Scenario: Support DOCX resume upload
    Given I am on the document upload page
    When I upload a valid DOCX resume file
    Then the resume should be saved to the database
    And AI parsing should be triggered
    And the text should be extracted from the DOCX file

  @issue-49
  Scenario: Parse resume with mixed content successfully
    Given I upload a resume containing skills, experience, and education
    When the AI parsing completes
    Then all three data types should be extracted
    And skills should be in a list format
    And experience should be in a structured array
    And education should be in a structured array
    And the parsing status should be "success"
    And the parsed_at timestamp should be set

  @issue-49
  Scenario: Handle resume with missing sections
    Given I upload a resume with only skills listed
    And the resume has no work experience section
    And the resume has no education section
    When the AI parsing completes
    Then the skills should be extracted
    And the experience list should be empty
    And the education list should be empty
    And the parsing status should be "success"

  @issue-48
  Scenario: Show parsing status during upload
    Given I am uploading a resume file
    When the upload is processing
    Then the parsing status should change to "in_progress"
    And the resume should be saved with status "in_progress"
    When parsing completes successfully
    Then the parsing status should change to "success"

  @issue-50
  Scenario: Display parsing error details to user
    Given my resume failed to parse
    And I am on my profile page
    When I view my resume details
    Then I should see the parsing status as "error"
    And I should see a clear error message
    And I should have the option to retry parsing
    And I should still be able to access the raw resume content

  @issue-48 @issue-49 @issue-50
  Scenario: Complete resume upload and edit workflow
    Given I am on the document upload page
    When I upload a valid PDF resume
    Then the resume should be uploaded successfully
    And AI parsing should extract my data
    When I navigate to my profile
    Then I should see all my parsed information
    When I edit my skills
    And I add new work experience
    And I save all changes
    Then all my updates should be persisted
    And I should be able to use this data in interviews

Feature: Job Listing Ingestion and AI-Powered Parsing
  As a job candidate
  I want to upload job descriptions and have them automatically analyzed
  So that I can prepare for interviews tailored to specific job requirements

  Background:
    Given the user is logged in
    And the OpenAI API is available and configured

  # Issue #21: Job Listing Upload and Storage
  Scenario: Successfully upload a job listing from text
    Given I am on the Documents page
    When I paste a job description into the text area:
      """
      Senior Python Developer

      We're seeking an experienced Python developer to join our team.

      Requirements:
      - 5+ years of Python experience
      - Expert knowledge of Django and Flask
      - Experience with PostgreSQL and Redis
      - Strong problem-solving skills

      Responsibilities:
      - Lead backend development projects
      - Mentor junior developers
      - Design scalable systems
      """
    And I click "Upload Job Listing"
    Then a new job listing should be created in the database
    And the job listing should be associated with my user account
    And the job listing content should match the pasted text
    And I should see a success message
    And the job listing should appear in my documents list

  Scenario: Successfully upload a job listing from file
    Given I am on the Documents page
    When I select a job listing file "senior_dev_role.txt"
    And I click "Upload Job Listing"
    Then a new job listing should be created in the database
    And the filename should be stored as "senior_dev_role.txt"
    And the file content should be extracted and stored
    And I should see the job listing in my documents list

  Scenario: Validation error when uploading empty job listing
    Given I am on the Documents page
    When I leave the job description text area empty
    And I click "Upload Job Listing"
    Then I should see an error message "Job description cannot be empty"
    And no job listing should be created

  # Issue #51: AI-Powered Job Parsing - Required Skills Extraction
  Scenario: Parse required skills from job description
    Given I have uploaded a job listing with content:
      """
      Senior Full Stack Developer

      Required Skills:
      - Python, Django, React
      - 5+ years of software development
      - PostgreSQL, MongoDB
      - Docker, Kubernetes
      - Team leadership and mentoring
      - Strong communication skills
      """
    When the AI parsing is triggered
    Then the job listing should have parsing_status "success"
    And the required_skills should contain:
      | skill                          |
      | Python                         |
      | Django                         |
      | React                          |
      | PostgreSQL                     |
      | MongoDB                        |
      | Docker                         |
      | Kubernetes                     |
      | Team leadership                |
      | Strong communication skills    |
      | 5+ years of software development |
    And the parsed_at timestamp should be set

  # Issue #52: AI-Powered Job Parsing - Seniority Level Detection
  Scenario Outline: Detect seniority level from job description
    Given I have uploaded a job listing with content:
      """
      <job_title>

      <description>
      """
    When the AI parsing is triggered
    Then the seniority_level should be "<expected_level>"
    And the parsing_status should be "success"

    Examples:
      | job_title                      | description                                    | expected_level |
      | Junior Developer               | 0-2 years experience, entry-level position     | entry          |
      | Software Developer             | 3-5 years experience, mid-level role           | mid            |
      | Senior Python Engineer         | 5+ years experience, lead technical projects   | senior         |
      | Principal Engineer             | 10+ years, architectural leadership            | lead           |
      | Director of Engineering        | Executive leadership, strategic planning       | executive      |

  # Issue #52: AI-Powered Job Parsing - Requirements Extraction
  Scenario: Extract structured requirements from job description
    Given I have uploaded a job listing with content:
      """
      Lead Software Engineer

      Education:
      - Bachelor's degree in Computer Science or related field
      - Master's degree preferred

      Experience:
      - 7+ years of professional software development

      Certifications:
      - AWS Certified Solutions Architect preferred
      - Scrum Master certification a plus

      Responsibilities:
      - Design and implement scalable backend systems
      - Lead a team of 5-7 engineers
      - Collaborate with product managers on technical roadmap
      - Conduct code reviews and establish best practices
      """
    When the AI parsing is triggered
    Then the requirements should contain:
      | field              | value                                                    |
      | education          | ["Bachelor's degree in Computer Science", "Master's degree preferred"] |
      | years_experience   | 7+                                                       |
      | certifications     | ["AWS Certified Solutions Architect", "Scrum Master certification"] |
      | responsibilities   | ["Design and implement scalable backend systems", "Lead a team of 5-7 engineers", "Collaborate with product managers", "Conduct code reviews"] |
    And the parsing_status should be "success"

  # Issue #53: Template Recommendation Based on Job Analysis
  Scenario: Recommend interview template based on job seniority
    Given I have the following templates:
      | name                    | difficulty | type    |
      | Entry Level Coding      | 1          | BEH     |
      | Mid-Level Technical     | 2          | SKL     |
      | Senior System Design    | 4          | SKL     |
      | Leadership Assessment   | 3          | FNL     |
    And I have uploaded a job listing for a "Senior Python Developer" position
    When the AI parsing is triggered
    Then the seniority_level should be "senior"
    And the recommended_template should be "Senior System Design"
    And the parsing_status should be "success"

  Scenario: Recommend template for entry-level position
    Given I have a template named "Entry Level Coding" with difficulty 1
    And I have uploaded a job listing for a "Junior Developer" position
    When the AI parsing is triggered
    Then the seniority_level should be "entry"
    And the recommended_template should be "Entry Level Coding"

  # Issue #53: Create Interview from Job Analysis (Navigation Flow)
  Scenario: Create interview directly from analyzed job listing
    Given I have an analyzed job listing with:
      | field                | value                  |
      | title               | Senior Backend Role     |
      | seniority_level     | senior                  |
      | recommended_template | Senior System Design    |
    When I am on the Documents page
    And I click "Create Interview" for the job listing
    Then I should be redirected to the chat creation page
    And the job listing should be pre-selected in the form
    And I should see a helper message "Job listing pre-selected from analysis"
    And I should see "Recommended template: Senior System Design"
    And the form should have the job listing pre-populated

  # Error Handling and Edge Cases
  Scenario: Handle parsing failure when OpenAI is unavailable
    Given the OpenAI API is unavailable
    And I have uploaded a job listing
    When the AI parsing is triggered
    Then the parsing_status should be "error"
    And the parsing_error should contain "OpenAI service is unavailable"
    And the job listing should still be accessible
    And I should be able to manually create an interview with it

  Scenario: Handle malformed job descriptions gracefully
    Given I have uploaded a job listing with minimal content:
      """
      Looking for a developer.
      """
    When the AI parsing is triggered
    Then the parsing should complete without errors
    And the required_skills should be an empty list
    And the seniority_level should be empty
    And the requirements should have empty values
    And the parsing_status should be "success"

  Scenario: Display parsing status in UI
    Given I have multiple job listings with different parsing statuses:
      | title                  | parsing_status |
      | Parsed Successfully    | success        |
      | Parsing in Progress    | in_progress    |
      | Parsing Failed         | error          |
    When I view the Documents page
    Then each job listing should display its parsing status
    And successfully parsed listings should show a success indicator
    And failed listings should show an error indicator with details

  # Integration with Existing Features
  Scenario: Use parsed job data in interview creation
    Given I have an analyzed job listing for "Senior Python Developer"
    And the job requires skills: ["Python", "Django", "PostgreSQL"]
    When I create an interview using this job listing
    Then the interview should be associated with the job listing
    And the AI should tailor questions based on required skills
    And the interview difficulty should match the seniority level

  Scenario: View job listing details and parsed data
    Given I have an analyzed job listing
    When I click "View Details" for the job listing
    Then I should see the original job description
    And I should see the extracted required skills
    And I should see the detected seniority level
    And I should see the structured requirements
    And I should see the recommended template (if any)

  # Security and Privacy
  Scenario: Job listings are isolated by user
    Given user "alice@example.com" has uploaded a job listing
    And user "bob@example.com" is logged in
    When "bob@example.com" views the Documents page
    Then "bob@example.com" should not see Alice's job listing
    And "bob@example.com" should not be able to access Alice's job listing by ID

  Scenario: Only authenticated users can upload job listings
    Given I am not logged in
    When I attempt to access the job listing upload endpoint
    Then I should be redirected to the login page
    And no job listing should be created

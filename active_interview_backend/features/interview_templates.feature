Feature: Interview Template Management
  As an interviewer
  I want to create named interview templates
  So that I can start organizing my interview structure

  Background:
    Given the application is running
    And the database is clean

  Scenario: Create Empty Template
    Given I am logged in as an interviewer
    When I create a new template with the name "Technical Interview"
    Then an empty template should be saved
    And I should see it in my template list

  Scenario: View template list as interviewer
    Given I am logged in as an interviewer
    And I have created templates:
      | name                  | description                           |
      | Technical Interview   | For software engineering positions    |
      | Behavioral Interview  | To assess soft skills and culture fit |
    When I navigate to the template list page
    Then I should see 2 templates
    And I should see "Technical Interview"
    And I should see "Behavioral Interview"

  Scenario: Create template with description
    Given I am logged in as an interviewer
    When I navigate to "/templates/create/"
    And I fill in "Template Name" with "System Design Interview"
    And I fill in "Description" with "For senior engineering roles"
    And I submit the template creation form
    Then the template "System Design Interview" should be created
    And the description should be "For senior engineering roles"
    And I should be redirected to the template list page
    And I should see "Template \"System Design Interview\" created successfully"

  Scenario: View template details
    Given I am logged in as an interviewer
    And I have a template named "Technical Interview"
    When I navigate to the template detail page for "Technical Interview"
    Then I should see the template name "Technical Interview"
    And I should see the created date
    And I should see the last updated date

  Scenario: Edit existing template
    Given I am logged in as an interviewer
    And I have a template named "Technical Interview" with description "Initial description"
    When I navigate to the edit page for "Technical Interview"
    And I change the name to "Advanced Technical Interview"
    And I change the description to "For senior positions only"
    And I submit the edit form
    Then the template should be updated with name "Advanced Technical Interview"
    And the description should be "For senior positions only"
    And I should see "Template \"Advanced Technical Interview\" updated successfully"

  Scenario: Delete a template
    Given I am logged in as an interviewer
    And I have a template named "Old Template"
    When I navigate to the template detail page for "Old Template"
    And I click the delete button
    And I confirm the deletion
    Then the template "Old Template" should be deleted
    And I should be redirected to the template list page
    And I should see "Template \"Old Template\" deleted successfully"
    And I should not see "Old Template" in my template list

  Scenario: Templates are isolated by user
    Given a user "interviewer1" has templates:
      | name           |
      | Template A     |
      | Template B     |
    And a user "interviewer2" has templates:
      | name           |
      | Template C     |
    When I am logged in as "interviewer1"
    And I navigate to the template list page
    Then I should see 2 templates
    And I should see "Template A"
    And I should see "Template B"
    And I should not see "Template C"

  Scenario: Candidate cannot access template management
    Given I am logged in as a candidate
    When I request "/templates/"
    Then the response status should be 403
    And I should see "Forbidden" or be redirected

  Scenario: Admin can access template management
    Given I am logged in as an admin
    When I navigate to "/templates/"
    Then the response status should be 200
    And I should be able to create templates

  Scenario: Unauthenticated user cannot access templates
    Given I am not logged in
    When I request "/templates/"
    Then the response status should be 302 or 401
    And I should be redirected to login page

  Scenario: Template name is required
    Given I am logged in as an interviewer
    When I navigate to "/templates/create/"
    And I leave the "Template Name" field empty
    And I submit the template creation form
    Then I should see a validation error
    And the template should not be created

  Scenario: Empty template list shows helpful message
    Given I am logged in as an interviewer
    And I have no templates
    When I navigate to the template list page
    Then I should see "No Templates Created"
    And I should see "Create your first interview template to start organizing your interview structure"
    And I should see a "Create New Template" button

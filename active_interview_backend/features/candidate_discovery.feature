@issue-69
Feature: Candidate discovery and search
  As an admin or interviewer
  I want to search for candidate
  So that view a candidate's profile

  Background:
    Given the application is running
    And the database is clean

  @issue-69
  Scenario: Admin can access candidate search
    Given I am logged in as an admin
    When I navigate to "/candidates/search/"
    Then the response status should be 200
    And I should see the search form

  @issue-69
  Scenario: Interviewer can access candidate search
    Given I am logged in as an interviewer
    When I navigate to "/candidates/search/"
    Then the response status should be 200
    And I should see the search form

  @issue-69
  Scenario: Candidate cannot access candidate search
    Given I am logged in as a candidate
    When I navigate to "/candidates/search/"
    Then the response status should be 403
    And I should see "Forbidden"

  @issue-69
  Scenario: Unauthenticated user cannot access candidate search
    Given I am not logged in
    When I navigate to "/candidates/search/"
    Then the response status should be 401
    And I should be denied access

  @issue-69
  Scenario: Search returns matching candidates by username
    Given I am logged in as an admin
    And the following candidates exist:
      | username     | email               | first_name | last_name |
      | john_doe     | john@example.com    | John       | Doe       |
      | jane_smith   | jane@example.com    | Jane       | Smith     |
      | bob_johnson  | bob@example.com     | Bob        | Johnson   |
    When I navigate to "/candidates/search/?q=john"
    Then the response status should be 200
    And I should see 2 search results
    And I should see candidate "john_doe" in the results
    And I should see candidate "bob_johnson" in the results
    And I should not see candidate "jane_smith" in the results

  @issue-69
  Scenario: Search is case-insensitive
    Given I am logged in as an admin
    And a candidate exists with username "john_doe"
    When I navigate to "/candidates/search/?q=JOHN"
    Then the response status should be 200
    And I should see candidate "john_doe" in the results

  @issue-69
  Scenario: Search returns exact username match
    Given I am logged in as an admin
    And the following candidates exist:
      | username    | email             |
      | john_doe    | john@example.com  |
      | jane_smith  | jane@example.com  |
    When I navigate to "/candidates/search/?q=jane_smith"
    Then the response status should be 200
    And I should see 1 search result
    And I should see candidate "jane_smith" in the results

  @issue-69
  Scenario: Search with no results shows appropriate message
    Given I am logged in as an admin
    And a candidate exists with username "john_doe"
    When I navigate to "/candidates/search/?q=nonexistent_user"
    Then the response status should be 200
    And I should see "No candidates found matching"

  @issue-69
  Scenario: Empty search shows instruction message
    Given I am logged in as an admin
    When I navigate to "/candidates/search/"
    Then the response status should be 200
    And I should see "Enter a username to search for candidates"

  @issue-69
  Scenario: Search only returns candidates, not admins or interviewers
    Given I am logged in as an admin
    And a candidate exists with username "john_candidate"
    And an admin exists with username "john_admin"
    And an interviewer exists with username "john_interviewer"
    When I navigate to "/candidates/search/?q=john"
    Then the response status should be 200
    And I should see 1 search result
    And I should see user "john_candidate" in the results
    And I should not see user "john_admin" in the results
    And I should not see user "john_interviewer" in the results

  @issue-69
  Scenario: Admin can view candidate profile from search results
    Given I am logged in as an admin
    And a candidate exists with username "john_doe" and user ID "123"
    When I navigate to "/candidates/search/?q=john"
    And I click "View Profile" for candidate "john_doe"
    Then I should be redirected to "/api/candidates/123/"
    And I should see the candidate's profile information

  @issue-69
  Scenario: Search results display candidate information
    Given I am logged in as an interviewer
    And a candidate exists with the following details:
      | username   | email            | first_name | last_name |
      | john_doe   | john@example.com | John       | Doe       |
    When I navigate to "/candidates/search/?q=john"
    Then I should see the following candidate details:
      | field      | value            |
      | Username   | john_doe         |
      | Email      | john@example.com |
      | Name       | John Doe         |

  @issue-69
  Scenario: Search limits results to 20 candidates
    Given I am logged in as an admin
    And 25 candidates exist with usernames containing "test"
    When I navigate to "/candidates/search/?q=test"
    Then the response status should be 200
    And I should see exactly 20 search results

  @issue-69
  Scenario: Search navigation link visible to admin
    Given I am logged in as an admin
    When I view the navigation bar
    Then I should see a link to "Search Candidates"

  @issue-69
  Scenario: Search navigation link visible to interviewer
    Given I am logged in as an interviewer
    When I view the navigation bar
    Then I should see a link to "Search Candidates"

  @issue-69
  Scenario: Search navigation link hidden from candidate
    Given I am logged in as a candidate
    When I view the navigation bar
    Then I should not see a link to "Search Candidates"

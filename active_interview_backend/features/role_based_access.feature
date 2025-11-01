@issue-69
Feature: Role-based access control
  As an admin
  I want RBAC (admin/interviewer/candidate)
  So that permissions are enforced

  Background:
    Given the application is running
    And the database is clean

  @issue-70
  Scenario: Role field exists on user model with default value
    When a new user registers with username "testuser" and password "SecurePass123"
    Then the user "testuser" should have role "candidate"

  @issue-70
  Scenario: User model supports all three role types
    Given a user exists with username "admin_user" and role "admin"
    And a user exists with username "interviewer_user" and role "interviewer"
    And a user exists with username "candidate_user" and role "candidate"
    Then the user "admin_user" should have role "admin"
    And the user "interviewer_user" should have role "interviewer"
    And the user "candidate_user" should have role "candidate"

  @issue-70
  Scenario: Admin can update user role via PATCH endpoint
    Given I am logged in as an admin
    And a user exists with username "testuser" and role "candidate"
    When I send a PATCH request to "/admin/users/<testuser_id>/role" with role "interviewer"
    Then the response status should be 200
    And the user "testuser" should have role "interviewer"

  @issue-70
  Scenario: Non-admin cannot update user roles
    Given I am logged in as a candidate
    And a user exists with username "otheruser" and role "candidate"
    When I send a PATCH request to "/admin/users/<otheruser_id>/role" with role "admin"
    Then the response status should be 403
    And the user "otheruser" should have role "candidate"

  @issue-71
  Scenario: Candidate cannot access admin routes
    Given roles "admin", "interviewer", "candidate" exist
    And I am logged in as a candidate
    When I request "/admin/users"
    Then the response status should be 403
    And I should see "Forbidden: Insufficient permissions"

  @issue-71
  Scenario: Admin can access admin routes
    Given roles "admin", "interviewer", "candidate" exist
    And I am logged in as an admin
    When I request "/admin/users"
    Then the response status should be 200
    And I should see the list of users

  @issue-71
  Scenario: Interviewer cannot access admin routes
    Given roles "admin", "interviewer", "candidate" exist
    And I am logged in as an interviewer
    When I request "/admin/users"
    Then the response status should be 403
    And I should see "Forbidden: Insufficient permissions"

  @issue-71
  Scenario: Unauthenticated user cannot access admin routes
    Given roles "admin", "interviewer", "candidate" exist
    And I am not logged in
    When I request "/admin/users"
    Then the response status should be 401 or redirect to login

  @issue-72
  Scenario: Candidate can access their own profile
    Given I am logged in as a candidate with user ID "123"
    When I send a GET request to "/candidates/123"
    Then the response status should be 200
    And I should see my profile information

  @issue-72
  Scenario: Candidate cannot access another candidate's profile
    Given I am logged in as a candidate with user ID "123"
    And a candidate exists with user ID "456"
    When I send a GET request to "/candidates/456"
    Then the response status should be 403
    And I should see "Forbidden"

  @issue-72
  Scenario: Candidate can update their own profile
    Given I am logged in as a candidate with user ID "123"
    When I send a PATCH request to "/candidates/123" with data:
      | field | value           |
      | name  | Updated Name    |
      | email | new@example.com |
    Then the response status should be 200
    And my profile should be updated with the new data

  @issue-72
  Scenario: Candidate cannot update another candidate's profile
    Given I am logged in as a candidate with user ID "123"
    And a candidate exists with user ID "456"
    When I send a PATCH request to "/candidates/456" with data:
      | field | value        |
      | name  | Hacked Name  |
    Then the response status should be 403
    And the candidate "456" profile should not be modified

  @issue-72
  Scenario: Admin can access any candidate's profile
    Given I am logged in as an admin
    And a candidate exists with user ID "123"
    When I send a GET request to "/candidates/123"
    Then the response status should be 200
    And I should see the candidate's profile information

  @issue-72
  Scenario: Interviewer can access any candidate's profile
    Given I am logged in as an interviewer
    And a candidate exists with user ID "123"
    When I send a GET request to "/candidates/123"
    Then the response status should be 200
    And I should see the candidate's profile information

  @issue-69
  Scenario: Candidate can submit a role change request
    Given I am logged in as a candidate
    When I navigate to my profile page
    And I click "Request Interviewer Role"
    And I fill in the reason as "I have 5 years of experience conducting technical interviews"
    And I submit the role change request
    Then I should see "Your request has been submitted"
    And I should have a pending role change request
    And I should not see the "Request Interviewer Role" button

  @issue-69
  Scenario: Candidate cannot submit duplicate pending requests
    Given I am logged in as a candidate
    And I have a pending role change request
    When I navigate to my profile page
    Then I should not see the "Request Interviewer Role" button
    And I should see "You have a pending role change request"

  @issue-69
  Scenario: Admin can view pending role requests
    Given I am logged in as an admin
    And a candidate "john_doe" has a pending role change request to "interviewer"
    And a candidate "jane_smith" has a pending role change request to "interviewer"
    When I navigate to "/role-requests/"
    Then the response status should be 200
    And I should see 2 pending requests
    And I should see user "john_doe" in the pending requests
    And I should see user "jane_smith" in the pending requests

  @issue-69
  Scenario: Admin can approve a role change request
    Given I am logged in as an admin
    And a candidate "john_doe" has a pending role change request to "interviewer"
    When I navigate to "/role-requests/"
    And I click "Approve" for user "john_doe"
    Then the request should be marked as "approved"
    And the user "john_doe" should have role "interviewer"
    And the request should show "reviewed_by" as the current admin
    And the "reviewed_at" timestamp should be set

  @issue-69
  Scenario: Admin can reject a role change request
    Given I am logged in as an admin
    And a candidate "john_doe" has a pending role change request to "interviewer"
    When I navigate to "/role-requests/"
    And I click "Reject" for user "john_doe"
    And I fill in admin notes as "Need more interview experience"
    And I confirm the rejection
    Then the request should be marked as "rejected"
    And the user "john_doe" should have role "candidate"
    And the request should include admin notes "Need more interview experience"

  @issue-69
  Scenario: Non-admin cannot access role request management
    Given I am logged in as a candidate
    When I request "/role-requests/"
    Then the response status should be 403

  @issue-69
  Scenario: Interviewer cannot approve role requests
    Given I am logged in as an interviewer
    When I request "/role-requests/"
    Then the response status should be 403

  @issue-69
  Scenario: Unauthenticated user cannot submit role request
    Given I am not logged in
    When I send a POST request to "/profile/request-role-change/" with data:
      | field          | value        |
      | requested_role | interviewer  |
      | reason         | I want this  |
    Then the response status should be 302 or 401
    And I should be redirected to login page

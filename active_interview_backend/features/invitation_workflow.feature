@issue-4
Feature: Interview Invitation Workflow
  As an interviewer
  I want to invite candidates and add to Google Calendar
  So that scheduling is painless

  Background:
    Given the application is running
    And the database is clean
    And I am logged in as an interviewer
    And I have a complete interview template named "Software Engineering Interview"

  # Issue #5: Create Interview Invitation from Template
  @issue-5
  Scenario: Create invitation from template detail page
    Given I am viewing the template "Software Engineering Interview"
    When I click "Invite Candidate"
    Then I should see the invitation creation form
    And the template field should be pre-filled with "Software Engineering Interview"
    And I should see fields for candidate email, scheduled date/time, and duration

  @issue-5
  Scenario: Create invitation from interview management dashboard
    Given I am on the interview management dashboard
    When I click "Create New Invitation"
    Then I should see the invitation creation form
    And I should see a dropdown to select a template
    And I should see fields for candidate email, scheduled date/time, and duration

  @issue-5
  Scenario: Successfully create an invitation with all required fields
    Given I am on the invitation creation form
    When I select template "Software Engineering Interview"
    And I enter candidate email "candidate@example.com"
    And I set scheduled date to "2025-12-15" at "10:00 AM"
    And I set duration to "60" minutes
    And I click "Send Invitation"
    Then the invitation should be created with a unique identifier
    And the interview should inherit the structure from the selected template

  @issue-5
  Scenario: Validation - Required fields must be filled
    Given I am on the invitation creation form
    When I leave the candidate email field empty
    And I click "Send Invitation"
    Then I should see a validation error "Candidate email is required"
    And the invitation should not be created

  @issue-5
  Scenario: Validation - Email format must be valid
    Given I am on the invitation creation form
    When I enter candidate email "invalid-email"
    And I fill in all other required fields
    And I click "Send Invitation"
    Then I should see a validation error "Please enter a valid email address"
    And the invitation should not be created

  # Issue #6: Generate Join Link
  @issue-6
  Scenario: Unique join link is generated when invitation is created
    Given I have created an invitation for "candidate@example.com"
    Then a unique join link should be generated
    And the join link should be in the format "/interview/invite/<unique-id>/"
    And the join link should be stored with the invitation

  @issue-6
  Scenario: Join link remains valid until interview completion
    Given I have created an invitation with a join link
    When the scheduled time has not arrived
    Then the join link should be accessible
    When the interview is in progress
    Then the join link should be accessible
    When the interview is completed
    Then the join link should remain accessible but show completion status

  @issue-6
  Scenario: Each invitation has a unique join link
    Given I create an invitation for "candidate1@example.com"
    And I create another invitation for "candidate2@example.com"
    Then each invitation should have a different join link
    And the links should not be predictable

  # Issue #7: Google Calendar Integration
  @issue-7
  Scenario: Calendar invitation sent to candidate
    Given I have created an invitation for "candidate@example.com"
    When the invitation email is sent
    Then a calendar invitation file (.ics format) should be included
    And the calendar invitation should contain the interview title
    And the calendar invitation should contain the scheduled date and time
    And the calendar invitation should contain the duration
    And the calendar invitation should contain the join link

  @issue-7
  Scenario: Event added to interviewer's Google Calendar
    Given I have connected my Google Calendar
    When I send an invitation to "candidate@example.com"
    Then an event should be added to my Google Calendar
    And the event should include the interview title
    And the event should include the scheduled date and time
    And the event should include the candidate email
    And the event should include the join link

  @issue-7
  Scenario: Candidate can accept calendar invitation
    Given I am a candidate who received an invitation email
    When I open the calendar invitation attachment
    Then I should be able to accept the invitation
    And the event should be added to my calendar application

  # Issue #8: Send Interview Invitation Email
  @issue-8
  Scenario: Email sent with all required information
    Given I have created an invitation for "candidate@example.com"
    When I click "Send Invitation"
    Then an email should be sent to "candidate@example.com"
    And the email should contain the interview position/title
    And the email should contain the scheduled date and time
    And the email should contain the duration
    And the email should contain the unique join link
    And the email should include a calendar invitation attachment (.ics file)

  @issue-8
  Scenario: Email contains professional formatting
    Given I send an invitation to "candidate@example.com"
    Then the email should have a professional template
    And the email should include the interviewer's name
    And the email should include instructions on how to join
    And the email should be mobile-friendly

  # Issue #9: Interview Confirmation Page
  @issue-9
  Scenario: Confirmation page shown after successful invitation send
    Given I have filled in all invitation details
    When I click "Send Invitation"
    And the invitation is sent successfully
    Then I should be redirected to the confirmation page
    And I should see "Invitation sent successfully"

  @issue-9
  Scenario: Confirmation page displays interview details
    Given I am on the confirmation page after sending an invitation
    Then I should see the interview template name
    And I should see the candidate email address
    And I should see the scheduled date and time
    And I should see the duration
    And I should see the generated join link

  @issue-9
  Scenario: Confirmation page provides Google Calendar option
    Given I am on the confirmation page
    Then I should see an "Add to Google Calendar" button
    When I click "Add to Google Calendar"
    Then the event should be added to my calendar

  @issue-9
  Scenario: Option to send additional invitations from confirmation page
    Given I am on the confirmation page
    Then I should see a "Send Another Invitation" button
    When I click "Send Another Invitation"
    Then I should be redirected to the invitation creation form

  # Issue #134: Interviewer Dashboard - Invitation Management
  @issue-134
  Scenario: View all sent invitations
    Given I have sent invitations to:
      | candidate_email       | status    | template                        |
      | candidate1@example.com| Pending   | Software Engineering Interview  |
      | candidate2@example.com| Completed | System Design Interview         |
      | candidate3@example.com| Reviewed  | Behavioral Interview            |
    When I navigate to the interview management dashboard
    Then I should see 3 invitations
    And each invitation should show candidate email, status, and template

  @issue-134
  Scenario: Filter invitations by status - Pending
    Given I have invitations with different statuses
    When I filter by "Pending" status
    Then I should only see invitations with "Pending" status
    And I should not see "Completed" or "Reviewed" invitations

  @issue-134
  Scenario: Filter invitations by status - Completed
    Given I have invitations with different statuses
    When I filter by "Completed" status
    Then I should only see invitations with "Completed" status
    And I should not see "Pending" or "Reviewed" invitations

  @issue-134
  Scenario: Filter invitations by status - Reviewed
    Given I have invitations with different statuses
    When I filter by "Reviewed" status
    Then I should only see invitations with "Reviewed" status
    And I should not see "Pending" or "Completed" invitations

  @issue-134
  Scenario: Click invitation to view details
    Given I have a completed invitation for "candidate@example.com"
    When I click on the invitation in the dashboard
    Then I should be taken to the interview results page
    And I should see the candidate's responses
    And I should see the AI-generated feedback

  @issue-134
  Scenario: Dashboard shows key information for each invitation
    Given I have sent an invitation to "candidate@example.com"
    When I view the dashboard
    Then for that invitation I should see:
      | field            | value                          |
      | Candidate Email  | candidate@example.com          |
      | Template         | Software Engineering Interview |
      | Scheduled Time   | 2025-12-15 10:00 AM           |
      | Status           | Pending                        |
      | Duration         | 60 minutes                     |

  # Issue #135: Candidate Registration Redirect Flow
  @issue-135
  Scenario: Unregistered candidate clicks invitation link
    Given I am an unregistered candidate
    When I click the invitation link in my email
    Then I should be redirected to the registration page
    And I should see a message "Please register to access your interview"

  @issue-135
  Scenario: Invitation context preserved during registration
    Given I am an unregistered candidate
    And I have clicked an invitation link with ID "abc123"
    When I am redirected to the registration page
    And I complete the registration form
    And I submit the registration
    Then my account should be created
    And I should be automatically redirected to the interview detail page for invitation "abc123"

  @issue-135
  Scenario: Registered candidate clicks invitation link
    Given I am a registered candidate
    And I am logged in
    When I click the invitation link in my email
    Then I should be taken directly to the interview detail page
    And I should not see the registration page

  @issue-135
  Scenario: Registered but not logged in candidate clicks invitation link
    Given I am a registered candidate
    And I am not logged in
    When I click the invitation link in my email
    Then I should be redirected to the login page
    And after logging in, I should be redirected to the interview detail page

  # Issue #136: Time-Gated Interview Access
  @issue-136
  Scenario: Candidate views interview before scheduled time
    Given I am a candidate with an invitation
    And the scheduled time is "2025-12-15 10:00 AM"
    And the current time is "2025-12-15 09:00 AM"
    When I navigate to the interview join link
    Then I should see the interview details
    And I should see position, scheduled time, and duration
    And the "Start Interview" button should be disabled
    And I should see a message "This interview will be available on 2025-12-15 at 10:00 AM"

  @issue-136
  Scenario: Interview becomes available at scheduled time
    Given I am a candidate with an invitation
    And the scheduled time is "2025-12-15 10:00 AM"
    And the current time is "2025-12-15 10:00 AM"
    When I navigate to the interview join link
    Then the "Start Interview" button should be enabled
    And I should be able to start the interview

  @issue-136
  Scenario: Candidate can start interview during duration window
    Given I am a candidate with an invitation
    And the scheduled time is "2025-12-15 10:00 AM"
    And the duration is 60 minutes
    And the current time is "2025-12-15 10:30 AM"
    When I navigate to the interview join link
    Then the "Start Interview" button should be enabled
    And I should be able to start the interview

  @issue-136
  Scenario: Candidate cannot start interview after window expires
    Given I am a candidate with an invitation
    And the scheduled time is "2025-12-15 10:00 AM"
    And the duration is 60 minutes
    And the current time is "2025-12-15 11:01 AM"
    And I have not started the interview
    When I navigate to the interview join link
    Then I should see a message "This interview time has passed and you can no longer take it"
    And the "Start Interview" button should be disabled
    And I should still be able to view the interview details

  # Issue #137: Interview Categorization - Practice vs Invited
  @issue-137
  Scenario: Candidate sees practice and invited interviews separately
    Given I am logged in as a candidate
    And I have 2 practice interviews
    And I have 3 invited interviews
    When I navigate to my interviews page
    Then I should see a "My Practice Interviews" section with 2 interviews
    And I should see an "Invited Interviews" section with 3 interviews
    And the sections should be visually distinct

  @issue-137
  Scenario: Practice interviews show self-initiated indicator
    Given I have a practice interview
    When I view my interviews
    Then the practice interview should be in the "My Practice Interviews" section
    And it should show "Self-initiated" or similar indicator

  @issue-137
  Scenario: Invited interviews show interviewer information
    Given I have an invited interview from "interviewer@company.com"
    When I view my interviews
    Then the invited interview should be in the "Invited Interviews" section
    And it should show the interviewer email or name

  @issue-137
  Scenario: Interview status displayed for both types
    Given I have practice and invited interviews in various states
    When I view my interviews page
    Then each interview should show its status:
      | type      | status      |
      | Practice  | Completed   |
      | Practice  | In Progress |
      | Invited   | Upcoming    |
      | Invited   | Completed   |
      | Invited   | Expired     |

  # Issue #138: Interviewer Review & Feedback
  @issue-138
  Scenario: Invited interview receives AI feedback and scoring upon completion
    Given a candidate has completed an invited interview
    Then the interview should have AI-generated feedback
    And the interview should have AI performance scores (professionalism, subject knowledge, clarity, overall)
    And the interview status should be "Completed"
    And the interviewer review status should be "Pending"

  @issue-138
  Scenario: Interviewer views completed interview results with AI feedback
    Given a candidate has completed an invited interview
    When I navigate to the interview results page
    Then I should see the candidate's responses
    And I should see the AI-generated feedback
    And I should see AI performance scores
    And I should see an indicator "Interviewer Review: Pending"

  @issue-138
  Scenario: Candidate views results before interviewer review
    Given I have completed an invited interview
    And the interviewer has not yet reviewed it
    When I view the interview results page
    Then I should see all my responses
    And I should see AI-generated feedback and scores
    And I should see a clear indicator "Interviewer Review: Pending"
    And I should not see any interviewer feedback yet

  @issue-138
  Scenario: Interviewer adds feedback to completed interview
    Given I am viewing a completed interview
    When I click "Add Feedback"
    And I enter my feedback in the text area
    And I click "Save Feedback"
    Then my feedback should be saved
    And it should be stored separately from AI feedback

  @issue-138
  Scenario: Interviewer marks interview as reviewed
    Given I am viewing a completed interview
    And I have added my feedback
    When I click "Mark as Reviewed"
    Then the interview status should change to "Reviewed"
    And the interview should appear in the "Reviewed" filter on my dashboard

  @issue-138
  Scenario: Candidate views both AI and interviewer feedback after review
    Given an interviewer has reviewed my interview
    And the interviewer has added feedback
    When I view the interview results
    Then I should see a section labeled "AI Feedback"
    And I should see a section labeled "Interviewer Feedback"
    And both sections should be clearly distinguished
    And I should see an indicator "Interviewer Review: Completed"

  @issue-138
  Scenario: Cannot mark as reviewed without adding feedback
    Given I am viewing a completed interview
    And I have not added any feedback
    When I try to click "Mark as Reviewed"
    Then I should see a validation message "Please add feedback before marking as reviewed"
    And the status should remain "Completed"

  # Issue #139: Email Notifications - Completion & Review
  @issue-139
  Scenario: Interviewer receives notification when candidate completes interview
    Given I have sent an invitation to "candidate@example.com"
    When the candidate completes the interview
    Then I should receive an email notification
    And the email should contain the candidate's email
    And the email should contain the interview template name
    And the email should contain a link to view the results

  @issue-139
  Scenario: Candidate receives notification when interview is reviewed
    Given I have completed an invited interview
    When the interviewer marks the interview as "Reviewed"
    Then I should receive an email notification
    And the email should contain the interview position
    And the email should contain a message that feedback is available
    And the email should contain a link to view the interviewer feedback

  @issue-139
  Scenario: No notification sent if interview abandoned
    Given I have sent an invitation to "candidate@example.com"
    And the candidate has not completed the interview
    When the interview window expires
    Then no completion notification should be sent to me

  # Issue #140: Duration Window Enforcement - Graceful Termination
  @issue-140
  Scenario: Candidate starts interview during valid window
    Given I am a candidate with an invitation
    And the scheduled time is "2025-12-15 10:00 AM"
    And the duration is 60 minutes
    And the current time is "2025-12-15 10:15 AM"
    When I start the interview
    Then the interview should begin normally
    And I should be able to answer questions

  @issue-140
  Scenario: AI poses question before window closes, candidate responds after
    Given I am in an active interview
    And the duration window is "2025-12-15 10:00 AM" to "11:00 AM"
    And the current time is "2025-12-15 10:59 AM"
    And the AI poses a new question
    When the time becomes "2025-12-15 11:05 AM"
    And I submit my response
    Then my response should be accepted
    And the AI should inform me "Thank you. Time is up for this interview."
    And the interview should be finalized
    And no new questions should be posed

  @issue-140
  Scenario: Window expires with no question in progress
    Given I am in an active interview
    And the duration window is "2025-12-15 10:00 AM" to "11:00 AM"
    And the current time is "2025-12-15 11:00 AM"
    And I have submitted my last response
    When the AI attempts to continue the interview
    Then the AI should inform me "Time is up for this interview."
    And the interview should be finalized
    And no new questions should be posed

  @issue-140
  Scenario: Candidate attempts to access expired interview that was never started
    Given I am a candidate with an invitation
    And the scheduled time is "2025-12-15 10:00 AM"
    And the duration is 60 minutes
    And the current time is "2025-12-15 11:30 AM"
    And I never started the interview
    When I navigate to the interview join link
    Then I should see "This interview time has passed and you can no longer take it"
    And I should not be able to start the interview
    And I should still be able to view the interview details

  @issue-140
  Scenario: Candidate can view past expired interviews
    Given I have an expired interview that I never took
    When I navigate to my interviews page
    Then the interview should appear in "Invited Interviews"
    And it should show status "Expired"
    When I click on it
    Then I should see the details
    And I should see "This interview time has passed and you can no longer take it"

  # Access Control & Edge Cases
  @issue-4
  Scenario: Only interviewer can create invitations
    Given I am logged in as a candidate
    When I attempt to access the invitation creation form
    Then I should receive a 403 Forbidden response
    And I should not be able to create invitations

  @issue-4
  Scenario: Candidate cannot access another candidate's invited interview
    Given candidate "alice@example.com" has an invited interview
    And I am logged in as candidate "bob@example.com"
    When I attempt to access Alice's interview join link
    Then I should receive a 403 Forbidden response
    And I should see "You do not have permission to access this interview"

  @issue-4
  Scenario: Interview invitation for non-existent template
    Given I am on the invitation creation form
    When I select a template that has been deleted
    And I fill in all other required fields
    And I click "Send Invitation"
    Then I should see an error "Selected template does not exist"
    And the invitation should not be created

  # Issue #141: PDF Reports for Invited Interviews
  @issue-141
  Scenario: Generate PDF report before interviewer review
    Given I have completed an invited interview
    And the interviewer has not yet reviewed it
    When I navigate to the interview results page
    And I click "Generate Report"
    Then a report should be created from my interview data
    And I should be able to download it as a PDF

  @issue-141
  Scenario: PDF report shows AI feedback before interviewer review
    Given I have completed an invited interview
    And the interviewer has not yet reviewed it
    When I download the PDF report
    Then the PDF should contain a section "AI Performance Scores"
    And the PDF should contain a section "AI Feedback"
    And the PDF should contain a section "Interviewer Feedback"
    And the "Interviewer Feedback" section should display "Status: Pending Review"
    And the PDF should show a clear indicator "Interviewer Review: Pending"

  @issue-141
  Scenario: PDF report structure before interviewer review
    Given I have completed an invited interview
    And the interviewer has not yet reviewed it
    When I download the PDF report
    Then the PDF should contain these sections in order:
      | section_order | section_name                      | content                                    |
      | 1             | Interview Details                 | Position, date, scheduled time, duration   |
      | 2             | AI Performance Scores             | Professionalism, knowledge, clarity, overall|
      | 3             | AI Feedback                       | AI-generated feedback text                 |
      | 4             | Interviewer Feedback              | "Pending Interviewer Review"               |
      | 5             | Questions and Responses           | All Q&A with individual scores             |
      | 6             | Interview Statistics              | Total questions, responses, etc.           |

  @issue-141
  Scenario: PDF report updated after interviewer review
    Given I have completed an invited interview
    And I had previously downloaded a PDF report
    And the interviewer has now reviewed the interview
    When I regenerate the PDF report
    Then the PDF should contain the AI feedback section
    And the PDF should contain a new "Interviewer Feedback" section with the interviewer's comments
    And the "Interviewer Feedback" section should display "Status: Completed"
    And the PDF should show "Interviewer Review: Completed"
    And the interviewer feedback should be clearly distinguished from AI feedback

  @issue-141
  Scenario: PDF report shows interviewer name and review date
    Given I have completed an invited interview
    And the interviewer "John Doe" has reviewed it on "2025-12-16"
    When I download the PDF report
    Then the "Interviewer Feedback" section should show "Reviewed by: John Doe"
    And the "Interviewer Feedback" section should show "Review Date: 2025-12-16"

  @issue-141
  Scenario: Candidate can regenerate PDF after interviewer review
    Given I have completed an invited interview
    And I generated a PDF before interviewer review
    And the interviewer has now reviewed the interview
    When I navigate to the interview results page
    And I click "Download as PDF" again
    Then the new PDF should include both AI and interviewer feedback
    And the PDF filename should include a current timestamp

  @issue-141
  Scenario: PDF report visual distinction between AI and interviewer feedback
    Given I have completed an invited interview
    And the interviewer has reviewed it
    When I download the PDF report
    Then the AI feedback section should have a distinct header style
    And the interviewer feedback section should have a distinct header style
    And both sections should be easily distinguishable visually
    And section headers should clearly label the source of feedback

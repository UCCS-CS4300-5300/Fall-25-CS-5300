@issue-24
Feature: Question Bank Tagging
  As an interviewer
  I want to tag questions (e.g., #python #sql #behavioral)
  So that I can auto-assemble interviews

  Background:
    Given the application is running
    And I am a registered interviewer
    And I am logged in

  @issue-38
  Scenario: Create a new question bank
    Given I am on the question banks page
    When I click the "Create Question Bank" button
    And I enter the name "Technical Interview Questions"
    And I enter the description "Questions for software engineering roles"
    And I click "Save"
    Then a new question bank should be created
    And I should see "Technical Interview Questions" in my question banks list
    And the question bank should be empty

  @issue-38
  Scenario: Add question to question bank
    Given I have created a question bank named "Python Questions"
    When I click "Add Question"
    And I enter the question text "What is a Python decorator?"
    And I enter the difficulty level "Medium"
    And I click "Save Question"
    Then the question should be added to the question bank
    And I should see the question in the question bank

  @issue-38
  Scenario: View question bank details
    Given I have a question bank with 10 questions
    When I click on the question bank
    Then I should see the question bank name
    And I should see the question bank description
    And I should see all 10 questions listed
    And I should see the question count "10 questions"

  @issue-38
  Scenario: Edit question in question bank
    Given I have a question "What is a Python decorator?" in my question bank
    When I click "Edit" on the question
    And I modify the question text to "Explain how Python decorators work"
    And I click "Save"
    Then the question should be updated
    And I should see the new question text

  @issue-38
  Scenario: Delete question from question bank
    Given I have a question in my question bank
    When I click "Delete" on the question
    And I confirm the deletion
    Then the question should be removed from the question bank
    And the question count should decrease by 1

  @issue-38
  Scenario: Delete entire question bank
    Given I have created a question bank
    When I click "Delete Question Bank"
    And I confirm the deletion
    Then the question bank should be removed
    And I should not see it in my question banks list

  @issue-39
  Scenario: Add single tag to a question
    Given I have a question "What is a Python decorator?" in my question bank
    When I click "Add Tag"
    And I enter the tag "#python"
    And I click "Save"
    Then the question should be tagged with "#python"
    And I should see "#python" displayed on the question

  @issue-39
  Scenario: Add multiple tags to a question
    Given I have a question in my question bank
    When I add tags "#python", "#advanced", and "#decorators"
    Then the question should have all three tags
    And I should see all three tags displayed on the question

  @issue-39
  Scenario: Remove tag from question
    Given I have a question tagged with "#python" and "#sql"
    When I click remove on the "#sql" tag
    Then the "#sql" tag should be removed
    And the question should still have the "#python" tag

  @issue-39
  Scenario: Tags are case-insensitive
    Given I have a question in my question bank
    When I add the tag "#Python"
    And I later try to add the tag "#python"
    Then only one "#python" tag should exist
    And I should see a message "Tag already exists"

  @issue-39
  Scenario: Bulk tag multiple questions
    Given I have selected 5 questions in my question bank
    When I click "Bulk Tag"
    And I enter tags "#behavioral" and "#leadership"
    And I click "Apply Tags"
    Then all 5 questions should be tagged with "#behavioral" and "#leadership"
    And I should see a confirmation "Tags applied to 5 questions"

  @issue-40
  Scenario: View all available tags
    Given I have created multiple questions with various tags
    When I navigate to the "Tag Management" page
    Then I should see a list of all unique tags
    And I should see the count of questions for each tag

  @issue-40
  Scenario: Rename a tag globally
    Given I have 10 questions tagged with "#python"
    When I go to "Tag Management"
    And I rename the tag "#python" to "#python3"
    And I confirm the change
    Then all 10 questions should now be tagged with "#python3"
    And the "#python" tag should no longer exist

  @issue-40
  Scenario: Merge duplicate tags
    Given I have questions tagged with both "#sql" and "#SQL"
    When I go to "Tag Management"
    And I select both tags
    And I click "Merge Tags"
    And I choose "#sql" as the primary tag
    Then all questions should be tagged with "#sql"
    And the "#SQL" tag should be removed

  @issue-40
  Scenario: Delete unused tag
    Given I have a tag "#outdated" that is not used on any questions
    When I go to "Tag Management"
    And I select the "#outdated" tag
    And I click "Delete Tag"
    Then the tag should be removed from the system
    And I should see a confirmation "Tag deleted"

  @issue-40
  Scenario: Standardize tag format
    Given I am creating a new tag
    When I enter "python"
    Then the system should automatically format it as "#python"
    And the tag should be stored in lowercase

  @issue-40
  Scenario: Prevent invalid tag names
    Given I am adding a tag to a question
    When I enter "tag with spaces"
    Then I should see an error "Tags cannot contain spaces"
    And the tag should not be created

  @issue-40
  Scenario: View tag usage statistics
    Given I have multiple tags in the system
    When I view the tag management page
    Then I should see how many questions use each tag
    And I should see which tags are most frequently used
    And I should see which tags are unused

  @issue-41
  Scenario: Filter questions by single tag
    Given I have a question bank with 20 questions
    And 8 questions are tagged with "#python"
    When I select the "#python" tag filter
    Then I should see only the 8 questions tagged with "#python"
    And other questions should be hidden

  @issue-41
  Scenario: Filter questions by multiple tags with AND logic
    Given I have questions tagged with various combinations
    And 5 questions are tagged with both "#python" and "#behavioral"
    When I select filters "#python" AND "#behavioral"
    Then I should see only the 5 questions that have both tags
    And questions with only one of the tags should be hidden

  @issue-41
  Scenario: Filter questions by multiple tags with OR logic
    Given I have a question bank with various tagged questions
    And 8 questions are tagged with "#python"
    And 6 questions are tagged with "#sql"
    When I select filters "#python" OR "#sql"
    Then I should see all 14 questions
    And questions without either tag should be hidden

  @issue-41
  Scenario: Clear tag filters
    Given I have applied filters "#python" and "#behavioral"
    And I am viewing filtered results
    When I click "Clear Filters"
    Then I should see all questions in the question bank
    And no filters should be active

  @issue-41
  Scenario: Save custom filter preset
    Given I have applied filters "#python" AND "#advanced"
    When I click "Save Filter Preset"
    And I name it "Advanced Python Questions"
    Then the filter preset should be saved
    And I should be able to quickly apply it later

  @issue-41
  Scenario: Search tags with autocomplete
    Given I have many tags in the system
    When I start typing "pyth" in the tag filter
    Then I should see autocomplete suggestions
    And "#python" and "#python3" should appear as options

  @issue-42
  Scenario: Auto-assemble interview with single tag
    Given I have a question bank with 15 questions tagged "#python"
    When I click "Generate Interview"
    And I select the tag "#python"
    And I specify 5 questions
    And I click "Assemble Interview"
    Then an interview should be created with 5 questions
    And all 5 questions should be tagged with "#python"

  @issue-42
  Scenario: Auto-assemble interview with multiple tags
    Given I have questions tagged with "#python" and "#behavioral"
    When I generate an interview using tags "#python" and "#behavioral"
    And I request 10 questions total
    Then at least 5 questions matching those tags should be selected
    And the interview should contain questions with the specified tags

  @issue-42
  Scenario: Exclude untagged questions from assembly
    Given I have 20 questions in my question bank
    And 15 questions are tagged
    And 5 questions have no tags
    When I auto-assemble an interview using tags "#python"
    Then only tagged questions should be included
    And the 5 untagged questions should be excluded

  @issue-42
  Scenario: Auto-assemble with difficulty level weighting
    Given I have questions tagged "#python" with various difficulty levels
    When I generate an interview with tag "#python"
    And I specify difficulty distribution: 30% easy, 50% medium, 20% hard
    And I request 10 questions
    Then the interview should have approximately 3 easy questions
    And approximately 5 medium questions
    And approximately 2 hard questions

  @issue-42
  Scenario: Insufficient questions for assembly
    Given I have only 3 questions tagged with "#advanced-sql"
    When I try to generate an interview with tag "#advanced-sql"
    And I request 10 questions
    Then I should see a warning "Only 3 questions available with selected tags"
    And I should be asked if I want to proceed with 3 questions

  @issue-42
  Scenario: Randomize question selection in assembly
    Given I have 20 questions tagged with "#python"
    When I generate an interview requesting 5 questions
    Then 5 questions should be randomly selected
    And generating another interview should likely produce different questions

  @issue-42
  Scenario: Auto-assemble with tag priority
    Given I have questions tagged with "#python", "#sql", and "#behavioral"
    When I generate an interview with tag priorities
    And I set "#python" as high priority
    And I set "#behavioral" as low priority
    And I request 10 questions
    Then the interview should contain more "#python" questions
    And fewer "#behavioral" questions

  @issue-42
  Scenario: Preview generated interview before saving
    Given I have configured interview assembly settings
    When I click "Generate Interview"
    Then I should see a preview of selected questions
    And I should see which tags each question has
    And I should be able to regenerate if not satisfied
    And I should be able to confirm and save the interview

  @issue-42
  Scenario: Track tag distribution in generated interview
    Given I have generated an interview with multiple tags
    When I view the interview details
    Then I should see a breakdown of tags used
    And I should see how many questions per tag
    And I should see the difficulty distribution

  @issue-24
  Scenario: Complete workflow - create bank, tag questions, generate interview
    Given I create a new question bank "Full Stack Interview"
    And I add 10 questions about Python
    And I add 8 questions about SQL
    And I add 7 questions about behavioral topics
    When I tag the Python questions with "#python"
    And I tag the SQL questions with "#sql"
    And I tag the behavioral questions with "#behavioral"
    And I generate an interview using tags "#python" and "#behavioral"
    And I request 5 questions
    Then an interview should be created with 5 questions
    And all questions should have either "#python" or "#behavioral" tags
    And no "#sql" questions should be included
    And untagged questions should be excluded

  @issue-39
  Scenario: Tag suggestion based on question content
    Given I am adding a new question "What is a JOIN in SQL?"
    When the system analyzes the question text
    Then I should see suggested tags "#sql" and "#database"
    And I should be able to accept or modify the suggestions

  @issue-41
  Scenario: Combined filtering and search
    Given I have applied tag filters "#python"
    When I also search for questions containing "decorator"
    Then I should see only "#python" questions containing "decorator"
    And all other questions should be hidden

  @issue-40
  Scenario: Tag analytics dashboard
    Given I have been using the question bank system for a while
    When I view the tag analytics
    Then I should see the most popular tags
    And I should see tag usage trends
    And I should see which tags need more questions

  @issue-42
  Scenario: Save assembly configuration as template
    Given I have configured interview assembly with specific tags and settings
    When I click "Save as Template"
    And I name it "Standard Python Interview"
    Then the configuration should be saved
    And I should be able to reuse it for future interviews

Feature: Change Enrollment Events
  As a registered user
  I want to change my enrollment mode


  Scenario: I can change my enrollment
	Given The course "6.002x" exists
	And the course "6.002x" has verified and honor modes
    And I am logged in
    Given I enable capturing of screenshots before and after each step
    And I visit the courses page
    When I register to audit the course "6.002x"
	And a "edx.course.enrollment.activated" server event is emitted
	And 1 "edx.course.enrollment.mode_changed" server events are emitted
    And I visit the dashboard
    And I click on Challenge Yourself
    And I choose an honor code upgrade
    Then I should be on the dashboard page
    And 2 "edx.course.enrollment.mode_changed" server events are emitted


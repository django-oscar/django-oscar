Feature: Smoke test
    Scenario: Homepage exists
        Given a user
        When I view the homepage
        Then I get a 200 response
        And page includes "Oscar"

    Scenario: Silly page doesn't exist
        Given a user
        When I view a silly page
        Then I get a 404 response
        And page includes "Page not found!"

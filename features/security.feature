Feature: API Token Authentication
  As a payment system
  I want to verify the API token on every transaction
  So that only authorised requests are processed

  Scenario: Correct token is accepted
    Given the API token is "SECURE123TOKEN"
    When I authenticate with token "SECURE123TOKEN"
    Then authentication should pass

  Scenario: Wrong token is rejected
    Given the API token is "SECURE123TOKEN"
    When I authenticate with token "INVALIDTOKEN"
    Then it should raise a PermissionError with "Invalid API token"

  Scenario: Empty token is rejected
    Given the API token is "SECURE123TOKEN"
    When I authenticate with token ""
    Then it should raise a PermissionError with "Invalid API token"

  Scenario: Partial token is rejected
    Given the API token is "SECURE123TOKEN"
    When I authenticate with token "SECURE123"
    Then it should raise a PermissionError with "Invalid API token"

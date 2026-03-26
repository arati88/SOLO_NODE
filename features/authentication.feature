Feature: API Token Authentication
  As a secure transaction processing pipeline
  I need API token verification to be both correct and timing-safe
  So that only authorized callers can process transactions

  Background:
    Given the API token environment variable is set to "SECURE123TOKEN"

  # -------------------------------------------------------
  # Happy path -- functional correctness
  # -------------------------------------------------------

  Scenario: Valid token authenticates successfully
    When I authenticate with token "SECURE123TOKEN"
    Then no exception is raised

  Scenario: Wrong token raises PermissionError
    When I authenticate with token "WRONGTOKEN"
    Then a PermissionError is raised

  Scenario: Empty token raises PermissionError
    When I authenticate with token ""
    Then a PermissionError is raised

  Scenario: Token of wrong type raises PermissionError
    When I authenticate with a non-string token
    Then a PermissionError is raised

  Scenario: Missing API_TOKEN env variable raises RuntimeError
    Given the API token environment variable is not set
    When I authenticate with token "SECURE123TOKEN"
    Then a RuntimeError is raised

  # -------------------------------------------------------
  # SN-03: Constant-time comparison must be used
  # Plain == is vulnerable to timing attacks
  # This scenario FAILS on buggy code -- hmac is imported but not used
  # -------------------------------------------------------

  Scenario: Authentication uses constant-time comparison
    Then the authenticate function uses hmac.compare_digest for token comparison

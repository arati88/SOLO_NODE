Feature: Transaction Audit Logging
  As a payment system
  I want to log every transaction result to the database
  So that there is a permanent audit trail for all transactions

  Scenario: Successful transaction is logged to database
    Given the database is available
    When I log transaction "TXN1001" with amount 767.67 fee 15.35 and status "SUCCESS"
    Then the audit log should be saved without errors

  Scenario: Failed transaction is logged to database
    Given the database is available
    When I log transaction "TXN1025" with amount 500.0 fee 0.0 and status "FAILED"
    Then the audit log should be saved without errors

  Scenario: Database error is logged and re-raised
    Given the database is unavailable
    When I log transaction "TXN1001" with amount 767.67 fee 15.35 and status "SUCCESS"
    Then it should raise a database exception

  Scenario: Audit failure is never silently swallowed
    Given the database is unavailable
    When I log transaction "TXN1001" with amount 767.67 fee 15.35 and status "SUCCESS"
    Then the error should be logged before raising

Feature: Audit Logging
  As a compliance system
  I need all audit log failures to raise exceptions
  So that failed writes are never silently ignored

  Background:
    Given the API token environment variable is set

  # -------------------------------------------------------
  # Happy path -- DB available
  # -------------------------------------------------------

  Scenario: Successful audit log write completes without error
    Given the database stored procedure will succeed
    When I call log_transaction with txn_id "TXN001" amount "500.00" fee "10.00" status "SUCCESS"
    Then no exception is raised

  Scenario: log_transaction rejects a negative amount
    When I call log_transaction with txn_id "TXN001" amount "-100.00" fee "2.00" status "SUCCESS"
    Then a ValueError is raised

  Scenario: log_transaction rejects an unknown status
    When I call log_transaction with txn_id "TXN001" amount "100.00" fee "2.00" status "UNKNOWN"
    Then a ValueError is raised

  Scenario: log_transaction rejects an empty txn_id
    When I call log_transaction with txn_id "" amount "100.00" fee "2.00" status "SUCCESS"
    Then a ValueError is raised

  # -------------------------------------------------------
  # SN-01: DB failure must NOT be silently swallowed
  # This scenario FAILS on buggy code -- except: pass hides the error
  # -------------------------------------------------------

  Scenario: DB failure during audit write raises an exception to the caller
    Given the database stored procedure will raise an exception
    When I call log_transaction with txn_id "TXN001" amount "500.00" fee "10.00" status "SUCCESS"
    Then an exception is raised
    And the exception message contains database error information

  Scenario: DB failure is not silently ignored
    Given the database stored procedure will raise an exception
    When I call log_transaction with txn_id "TXN002" amount "200.00" fee "4.00" status "FAILED"
    Then log_transaction does not return normally

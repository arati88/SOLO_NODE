Feature: Transaction Validation
  As a transaction processing pipeline
  I need batch validation to be safe and complete
  So that no valid transaction is lost and caller data is never mutated

  # -------------------------------------------------------
  # Happy path -- single transaction validation
  # -------------------------------------------------------

  Scenario: Valid transaction passes validation
    Given a transaction with id "TXN001" amount "767.67" merchant "M101"
    When I validate the transaction
    Then the result is True

  Scenario: Transaction with missing transaction_id is rejected
    Given a transaction with id "" amount "100.00" merchant "M101"
    When I validate the transaction
    Then a ValueError is raised

  Scenario: Transaction with missing merchant_id is rejected
    Given a transaction with id "TXN001" amount "100.00" merchant ""
    When I validate the transaction
    Then a ValueError is raised

  Scenario: Transaction with zero amount is rejected
    Given a transaction with id "TXN001" amount "0.00" merchant "M101"
    When I validate the transaction
    Then a ValueError is raised

  Scenario: Transaction with negative amount is rejected
    Given a transaction with id "TXN001" amount "-50.00" merchant "M101"
    When I validate the transaction
    Then a ValueError is raised

  Scenario: Transaction with float amount is rejected
    Given a transaction with float amount 100.0 and id "TXN001" merchant "M101"
    When I validate the transaction
    Then a TypeError is raised

  Scenario: Transaction above maximum limit is rejected
    Given a transaction with id "TXN001" amount "1000001.00" merchant "M101"
    When I validate the transaction
    Then a ValueError is raised

  # -------------------------------------------------------
  # SN-02: Batch validation must not mutate caller's transaction objects
  # These scenarios FAIL on buggy code -- txn["amount"] = int(txn["amount"]) modifies original dicts
  # -------------------------------------------------------

  Scenario: validate_batch does not mutate original transaction amounts
    Given a batch of transactions:
      | transaction_id | amount   | merchant_id | valid |
      | TXN001         | 100.50   | M1          | yes   |
      | TXN002         | 250.75   | M2          | yes   |
      | TXN003         | 75.99    | M3          | yes   |
    When I call validate_batch with the batch
    Then the original transaction amounts are unchanged
    And TXN001 original amount is still "100.50"
    And TXN002 original amount is still "250.75"
    And TXN003 original amount is still "75.99"

  Scenario: validate_batch returns valid transactions with their original amounts
    Given a batch of transactions:
      | transaction_id | amount   | merchant_id | valid |
      | TXN001         | 100.50   | M1          | yes   |
      | TXN002         | -50.00   | M2          | no    |
      | TXN003         | 200.75   | M3          | yes   |
    When I call validate_batch with the batch
    Then "TXN001" in the valid result has amount "100.50"
    And "TXN003" in the valid result has amount "200.75"

  Scenario: validate_batch with all valid transactions returns all of them
    Given a batch of transactions:
      | transaction_id | amount   | merchant_id | valid |
      | TXN001         | 100.00   | M1          | yes   |
      | TXN002         | 200.00   | M2          | yes   |
      | TXN003         | 300.00   | M3          | yes   |
    When I call validate_batch with the batch
    Then the returned valid list contains 3 transactions

  Scenario: validate_batch with all invalid transactions returns empty list
    Given a batch of transactions:
      | transaction_id | amount   | merchant_id | valid |
      | TXN001         | -10.00   | M1          | no    |
      | TXN002         | -20.00   | M2          | no    |
    When I call validate_batch with the batch
    Then the returned valid list contains 0 transactions

Feature: Transaction Validation
  As a payment system
  I want to validate each transaction before processing
  So that only correct and complete transactions enter the pipeline

  Scenario: Valid transaction passes validation
    Given a transaction with id "TXN1001" amount 500.0 and merchant "M101"
    When I validate the transaction
    Then validation should pass

  Scenario: Missing transaction_id is rejected
    Given a transaction with no transaction_id
    When I validate the transaction
    Then it should raise a ValueError with "Missing field transaction_id"

  Scenario: Missing amount is rejected
    Given a transaction with no amount
    When I validate the transaction
    Then it should raise a ValueError with "Missing field amount"

  Scenario: Missing merchant_id is rejected
    Given a transaction with no merchant_id
    When I validate the transaction
    Then it should raise a ValueError with "Missing field merchant_id"

  Scenario: Amount as string is rejected
    Given a transaction with amount as string "500"
    When I validate the transaction
    Then it should raise a TypeError

  Scenario: Negative amount is rejected
    Given a transaction with amount -100.0
    When I validate the transaction
    Then it should raise a ValueError with "Amount must be positive"

  Scenario: Zero amount is rejected
    Given a transaction with amount 0
    When I validate the transaction
    Then it should raise a ValueError with "Amount must be positive"

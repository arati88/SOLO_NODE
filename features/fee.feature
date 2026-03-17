Feature: Transaction Fee Calculation
  As a payment system
  I want to calculate a precise 2% fee on every transaction
  So that merchants are charged accurately

  Scenario: Fee calculated correctly for decimal amount
    Given a transaction amount of 767.67
    When I calculate the fee
    Then the fee should be 15.35

  Scenario: Fee calculated correctly for whole number
    Given a transaction amount of 100.0
    When I calculate the fee
    Then the fee should be 2.0

  Scenario: Fee calculated correctly for small amount
    Given a transaction amount of 0.10
    When I calculate the fee
    Then the fee should be 0.0

  Scenario: Fee calculated correctly for large amount
    Given a transaction amount of 99999.99
    When I calculate the fee
    Then the fee should be 2000.0

  Scenario: Fee is precise and not truncated
    Given a transaction amount of 199.99
    When I calculate the fee
    Then the fee should be 4.0

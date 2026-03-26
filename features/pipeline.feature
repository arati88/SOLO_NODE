Feature: Transaction Processing Pipeline
  As a transaction processing system
  I need the end-to-end pipeline to process transactions accurately
  So that authentication, validation, fees, and auditing all work together correctly

  Background:
    Given the pipeline environment is configured with token "SECURE123TOKEN"
    And the database stored procedure will succeed

  # -------------------------------------------------------
  # Happy path -- single transaction end-to-end
  # -------------------------------------------------------

  Scenario: Valid transaction is processed successfully
    Given a pipeline transaction with id "TXN001" amount "500.00" merchant "M101" token "SECURE123TOKEN"
    When I process the transaction through the pipeline
    Then the result status is "SUCCESS"
    And the result contains a fee

  Scenario: Transaction with invalid token is rejected
    Given a pipeline transaction with id "TXN001" amount "500.00" merchant "M101" token "WRONGTOKEN"
    When I process the transaction through the pipeline
    Then the result status is "FAILED"
    And the error message is "Authentication failed."

  Scenario: Transaction with missing required field is rejected
    Given an incomplete pipeline transaction missing the merchant_id
    When I process the transaction through the pipeline
    Then the result status is "FAILED"
    And the error message is "Invalid transaction data."

  Scenario: Transaction with negative amount is rejected
    Given a pipeline transaction with id "TXN001" amount "-100.00" merchant "M101" token "SECURE123TOKEN"
    When I process the transaction through the pipeline
    Then the result status is "FAILED"
    And the error message is "Invalid transaction data."

  # -------------------------------------------------------
  # Full dataset run
  # -------------------------------------------------------

  Scenario: Pipeline processes the sample dataset with expected success and failure counts
    Given the sample transaction dataset file
    When I run the full pipeline
    Then the total transactions processed is 100
    And the number of successful transactions is 96
    And the number of failed transactions is 4

  Scenario: The 4 security test transactions all fail with authentication error
    Given the sample transaction dataset file
    When I run the full pipeline
    Then transaction "TXN1025" has status "FAILED"
    And transaction "TXN1050" has status "FAILED"
    And transaction "TXN1075" has status "FAILED"
    And transaction "TXN1100" has status "FAILED"

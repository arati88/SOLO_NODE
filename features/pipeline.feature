Feature: Transaction Pipeline Orchestration
  As a payment system
  I want to process transactions through the full pipeline
  So that each transaction is validated, authenticated, fee-calculated, and audited

  Scenario: Valid transaction is processed successfully
    Given a valid transaction "TXN1001" with amount 500.0 and merchant "M101" and token "SECURE123TOKEN"
    When I run the transaction through the pipeline
    Then the result status should be "SUCCESS"
    And the result should contain a fee

  Scenario: Transaction with invalid amount is rejected
    Given a valid transaction "TXN1002" with amount -50.0 and merchant "M101" and token "SECURE123TOKEN"
    When I run the transaction through the pipeline
    Then the result status should be "FAILED"
    And the result should contain an error message

  Scenario: Transaction with wrong token is rejected
    Given a valid transaction "TXN1003" with amount 200.0 and merchant "M101" and token "WRONGTOKEN"
    When I run the transaction through the pipeline
    Then the result status should be "FAILED"
    And the result should contain an error message

  Scenario: Failed transaction is still logged to the audit database
    Given a valid transaction "TXN1004" with amount -10.0 and merchant "M101" and token "SECURE123TOKEN"
    When I run the transaction through the pipeline
    Then the audit log should be called with status "FAILED"

  Scenario: Successful transaction is logged to the audit database
    Given a valid transaction "TXN1005" with amount 300.0 and merchant "M101" and token "SECURE123TOKEN"
    When I run the transaction through the pipeline
    Then the audit log should be called with status "SUCCESS"

  Scenario: Transaction with missing field returns FAILED status
    Given an incomplete transaction missing the amount field
    When I run the transaction through the pipeline
    Then the result status should be "FAILED"
    And the result should contain an error message

Feature: Fee Calculation
  As a financial transaction system
  I need fees to be calculated with correct rounding
  So that no revenue is lost due to truncation errors

  # -------------------------------------------------------
  # Happy path -- amounts that don't expose the rounding bug
  # -------------------------------------------------------

  Scenario: Fee for round amount calculates correctly
    Given a transaction amount of "100.00"
    When I calculate the fee
    Then the fee should be "2.00"

  Scenario: Fee for zero amount is zero
    Given a transaction amount of "0.00"
    When I calculate the fee
    Then the fee should be "0.00"

  Scenario: Fee for amount 250.00 calculates correctly
    Given a transaction amount of "250.00"
    When I calculate the fee
    Then the fee should be "5.00"

  Scenario: calculate_fee rejects negative amounts
    Given a transaction amount of "-100.00"
    When I calculate the fee
    Then a ValueError is raised

  Scenario: calculate_fee rejects float input
    When I calculate the fee for a float amount 100.0
    Then a TypeError is raised

  # -------------------------------------------------------
  # SN-04: Integer truncation causes wrong fees
  # These scenarios FAIL on buggy code -- int() drops the fractional cent
  # -------------------------------------------------------

  Scenario Outline: Fee rounds half-up correctly for amounts requiring rounding
    Given a transaction amount of "<amount>"
    When I calculate the fee
    Then the fee should be "<expected_fee>"

    Examples: Amounts where int() truncation causes wrong result
      | amount   | expected_fee |
      | 812.36   | 16.25        |
      | 506.88   | 10.14        |
      | 279.96   | 5.60         |
      | 239.41   | 4.79         |
      | 4.89     | 0.10         |
      | 24.35    | 0.49         |
      | 70.45    | 1.41         |
      | 172.30   | 3.45         |
      | 320.90   | 6.42         |

  Scenario: Majority of dataset transactions have correct fees
    Given the sample transaction dataset
    When I calculate fees for all transactions
    Then at least 95 out of 100 transactions should have the correct fee

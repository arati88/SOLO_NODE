# SoloNode Transaction Audit — Defect Diagnosis POC

>This is the buggy version of the SoloNode transaction processing pipeline. It contains 4 intentionally seeded defects for use in a Solo Hackathon debugging challenge.
---

## Overview

SoloNode is a Python-based financial transaction processing pipeline. It authenticates callers, validates transactions, calculates processing fees, and writes immutable audit records to a MySQL database.

This version (**Buggy**) contains 4 defects injected across 4 modules. Participants are asked to identify and fix all defects using AI assistance.

---

## System Architecture

Each transaction passes through the pipeline in this fixed order:

```
sample_transactions.json
          |
     pipeline.py          <- reads input, loops transactions, logs summary
          |
authentication.py         <- AUTH FIRST -- verifies API token
          |
transaction_validator.py  <- checks fields, Decimal type, positive value, upper bound
          |
  fee_calculator.py       <- calculates 2% fee
          |
   audit_logger.py        <- validates inputs, calls stored procedure
          |
     database.py          <- manages MySQL connection, executes callproc()
          |
    solonode_db           <- MySQL audit_log table (append-only)
```

---

## Dataset

`data/sample_transactions.json` contains **100 transactions**:

| Transaction Type | Count | Token Used |
|---|---|---|
| `NORMAL` | 96 | `SECURE123TOKEN` (valid) |
| `SECURITY_TEST` | 4 | `INVALIDTOKEN` (deliberately wrong) |

The 4 `SECURITY_TEST` transactions (TXN1025, TXN1050, TXN1075, TXN1100) are designed to fail authentication and verify that auth rejection works correctly.

---

## Actual Pipeline Output

Running the pipeline as-is (with all 4 bugs present):

```
INFO: Starting pipeline: 100 transactions
INFO: Transaction TXN1001 completed with status SUCCESS
INFO: Transaction TXN1002 completed with status SUCCESS
INFO: Transaction TXN1003 completed with status SUCCESS
...
WARNING: Authentication failure: invalid token presented
ERROR: Auth failed for TXN1025
INFO: Transaction TXN1025 completed with status FAILED
...
WARNING: Authentication failure: invalid token presented
ERROR: Auth failed for TXN1100
INFO: Transaction TXN1100 completed with status FAILED
INFO: Pipeline complete -- Total: 100 | SUCCESS: 96 | FAILED: 4
WARNING: Failed transaction TXN1025: Authentication failed.
WARNING: Failed transaction TXN1050: Authentication failed.
WARNING: Failed transaction TXN1075: Authentication failed.
WARNING: Failed transaction TXN1100: Authentication failed.
```

The pipeline appears to run correctly. It does not crash. This is the danger -- **all 4 bugs are invisible in the pipeline output**. Both the buggy and clean versions produce exactly the same output when run.

---

## Defect Reference

---

### SN-01 -- Silent Failure in Audit Logger

| Field | Detail |
|---|---|
| **File** | `audit_logger.py` |
| **Line** | 49-50 |
| **Category** | Silent Failure |
| **Severity** | Critical |

**The buggy code:**

```python
params = (txn_id, amount, fee, status)
try:
    call_procedure("sp_insert_audit_log", params)
except:       # catches EVERYTHING
    pass      # and discards it silently
```

The bare `except: pass` catches every possible exception -- database connection errors, stored procedure failures, network timeouts, wrong credentials -- and discards them all silently. No exception is raised. No warning is logged. The function returns `None` as if the write succeeded.

The docstring on the same function explicitly states:

The implementation directly contradicts its own contract.

**Actual output when DB write fails (verified with simulated DB failure):**

```
# With SN-01 bug present -- DB goes down mid-run:

INFO: Transaction TXN1001 completed with status SUCCESS   <- pipeline reports success
INFO: Transaction TXN1002 completed with status SUCCESS   <- no audit record written
INFO: Transaction TXN1003 completed with status SUCCESS   <- no error surfaced anywhere
INFO: Pipeline complete -- Total: 100 | SUCCESS: 96 | FAILED: 4

log_transaction() returned normally -- NO exception raised
DB write FAILED silently. No audit record written. Caller has no idea.
```

Zero audit records written to MySQL. Pipeline still reports SUCCESS: 96 — identical to normal operation. The DB failure is completely invisible.


**Gherkin Tests (features/audit_logging.feature):**

```gherkin
# This scenario FAILS on buggy code
Scenario: DB failure during audit write raises an exception to the caller
  Given the database stored procedure will raise an exception
  When I call log_transaction with txn_id "TXN001" amount "500.00" fee "10.00" status "SUCCESS"
  Then an exception is raised
  And the exception message contains database error information

Scenario: DB failure is not silently ignored
  Given the database stored procedure will raise an exception
  When I call log_transaction with txn_id "TXN002" amount "200.00" fee "4.00" status "FAILED"
  Then log_transaction does not return normally
```

**Behave result on buggy code:**
```
Scenario: DB failure during audit write raises an exception to the caller
  ASSERT FAILED: Expected an exception to be raised, but log_transaction returned normally.

Scenario: DB failure is not silently ignored
  ASSERT FAILED: log_transaction returned normally despite a DB failure.
```

---

### SN-02 -- State Mutation in Batch Validator

| Field | Detail |
|---|---|
| **File** | `transaction_validator.py` |
| **Line** | 51 |
| **Category** | State Mutation |
| **Severity** | High |

**The buggy code:**

```python
def validate_batch(transactions: list) -> list:
    valid = []
    for txn in transactions:
        txn["amount"] = int(txn["amount"])  # BUG: mutates the caller's transaction objects directly
        try:
            validate_transaction(txn)
            valid.append(txn)
        except (ValueError, TypeError):
            pass
    return valid
```

`txn["amount"] = int(txn["amount"])` modifies the **original dict that the caller passed in**. Since Python dicts are passed by reference, this change persists after `validate_batch` returns. The caller's transaction objects now have `int` amounts instead of `Decimal` amounts -- truncated, with the decimal part gone.

This causes **silent financial errors downstream**: any module that uses `txn["amount"]` after calling `validate_batch` -- such as `calculate_fee()` -- receives the wrong value.

**Step-by-step for `amount = 100.50`:**

```
Original:           Decimal("100.50")
After int():        100                  <- 0.50 discarded
Correct fee (2%):   2.01
Fee received:       2.00                 <- wrong, calculated on 100 not 100.50
```

**Actual output -- running `validate_batch()` with decimal amounts:**

```
Input batch:
  TXN001  amount=Decimal("100.50")
  TXN002  amount=Decimal("250.75")
  TXN003  amount=Decimal("75.99")
```

```
Caller's transaction amounts after validate_batch (mutated -- should be unchanged):
  TXN001  amount=100     <- was Decimal("100.50"), now int 100
  TXN002  amount=250     <- was Decimal("250.75"), now int 250
  TXN003  amount=75      <- was Decimal("75.99"),  now int 75

Fee impact (2% rate):
  TXN001: expected fee=2.01, actual fee=2.00  (-0.01)
  TXN002: expected fee=5.02, actual fee=5.00  (-0.02)
  TXN003: expected fee=1.52, actual fee=1.00  (-0.52 -- large error for small amounts)
```

**What the output should look like after the fix (`copy.deepcopy`):**

```
Caller's transaction amounts after validate_batch (unchanged):
  TXN001  amount=Decimal("100.50")
  TXN002  amount=Decimal("250.75")
  TXN003  amount=Decimal("75.99")
```

**Gherkin Tests (features/transaction_validation.feature):**

```gherkin
# These scenarios FAIL on buggy code
Scenario: validate_batch does not mutate original transaction amounts
  Given a batch of transactions:
    | transaction_id | amount  | merchant_id | valid |
    | TXN001         | 100.50  | M1          | yes   |
    | TXN002         | 250.75  | M2          | yes   |
    | TXN003         | 75.99   | M3          | yes   |
  When I call validate_batch with the batch
  Then the original transaction amounts are unchanged
  And TXN001 original amount is still "100.50"
  And TXN002 original amount is still "250.75"
  And TXN003 original amount is still "75.99"

Scenario: validate_batch returns valid transactions with their original amounts
  Given a batch of transactions:
    | transaction_id | amount  | merchant_id | valid |
    | TXN001         | 100.50  | M1          | yes   |
    | TXN002         | -50.00  | M2          | no    |
    | TXN003         | 200.75  | M3          | yes   |
  When I call validate_batch with the batch
  Then "TXN001" in the valid result has amount "100.50"
  And "TXN003" in the valid result has amount "200.75"
```

**Behave result on buggy code:**
```
Scenario: validate_batch does not mutate original transaction amounts
  ASSERT FAILED: Amount for TXN001 was mutated!
    Before: 100.50 (Decimal)
    After:  100 (int)
  This is SN-02: validate_batch() sets txn["amount"] = int(txn["amount"])

Scenario: validate_batch returns valid transactions with their original amounts
  ASSERT FAILED: TXN001 in valid result has wrong amount!
    Expected: 100.50
    Got:      100
```

---

### SN-03 -- Timing Attack Vulnerability in Authentication

| Field | Detail |
|---|---|
| **File** | `authentication.py` |
| **Line** | 25 |
| **Category** | Security |
| **Severity** | High |

**The buggy code:**

```python

def authenticate(token: str) -> None:
    ...
    if token != api_token:          # BUG: plain equality -- short-circuits on first mismatch
        logger.warning("Authentication failure: invalid token presented")
        raise PermissionError("Invalid API token")
```

The docstring says *"Uses constant-time comparison to prevent timing attacks"* but the comparison uses Python's `!=` operator, which is a plain string equality check that **short-circuits** -- it stops as soon as it finds the first character that differs.

This means a token that shares more leading characters with the real token takes slightly longer to reject. An attacker can send thousands of guesses and measure response time character by character, eventually reconstructing the full token without triggering a rate limit or lockout.

**Actual timing measured from running `authenticate()` 5,000 times per token:**

```
Token                      Description                      Avg time/call
-------------------------------------------------------------------------
'AXXXXXXXXXXXXXXX'         no match at char 1               26.298 us
'SXXXXXXXXXXXXXXX'         matches 1 char (S)               27.027 us
'SECURE123TOKEN'           full match -- succeeds            0.529 us
```

The difference is measurable. An attacker can use this timing signal to iteratively guess the correct token one character at a time.

`hmac.compare_digest()` eliminates this signal -- every comparison takes the same time regardless of how many characters match.

**What the fix looks like:**

```python
if not hmac.compare_digest(token, api_token):   # constant-time -- no timing signal
    raise PermissionError("Invalid API token")
```

**Gherkin Tests (features/authentication.feature):**

```gherkin
# This scenario FAILS on buggy code -- hmac is imported but not used
Scenario: Authentication uses constant-time comparison
  Then the authenticate function uses hmac.compare_digest for token comparison
```

**Behave result on buggy code:**
```
Scenario: Authentication uses constant-time comparison
  ASSERT FAILED: authenticate() does not use hmac.compare_digest().
  The current implementation uses plain '!=' which leaks token information
  through timing differences.
```

---

### SN-04 -- Fee Rounding Error via Integer Truncation

| Field | Detail |
|---|---|
| **File** | `fee_calculator.py` |
| **Line** | 34 |
| **Category** | Logic Error |
| **Severity** | Medium |

**The buggy code:**

```python
from decimal import Decimal

def calculate_fee(amount: Decimal) -> Decimal:
    return Decimal(int(amount * _FEE_RATE))
    #                   ^^^
    #                   int() truncates the entire fee -- discards everything after the decimal point
```

`amount * _FEE_RATE` produces a full-precision `Decimal`. Wrapping it in `int()` discards everything after the decimal point entirely -- not just rounding, but full truncation. For `amount = 199.99`, the fee `3.9998` becomes `3` instead of `4`. `ROUND_HALF_UP` and `_CENT` are imported and defined but never applied.

**Step-by-step for `amount = 199.99`:**

```
199.99 x 0.02  =  3.9998      <- correct fee value
int(3.9998)    =  3            <- entire decimal part discarded
correct fee    =  4.00         <- should be 4.00
error          =  -1.00        <- under-charge per transaction
```

**Step-by-step for `amount = 812.36`:**

```
812.36 x 0.02  =  16.2472     <- correct fee value
int(16.2472)   =  16           <- .2472 discarded
correct fee    =  16.25        <- should be 16.25
error          =  -0.25        <- under-charge
```

**Actual results for selected transactions:**

```
NOTE: This bug is NOT visible in pipeline output (python pipeline.py).
The pipeline only shows SUCCESS/FAILED -- not individual fee values.
The wrong fees are only detectable by inspecting the fee_calculator directly
or running the Behave test suite.

TXN ID       Amount     Buggy Fee  Correct Fee   Error
-------------------------------------------------------
TXN1003      812.36        16         16.25       -0.25
TXN1004      506.88        10         10.14       -0.14
TXN1005      279.96         5          5.60       -0.60
TXN1039       24.35         0          0.49       -0.49
TXN1034        4.89         0          0.10       -0.10
TXN1001      100.00         2          2.00        0.00  <- correct (multiple of 50)
TXN1002      250.00         5          5.00        0.00  <- correct (multiple of 50)
```

Most transactions in the dataset have amounts that are NOT multiples of 50, so the majority have wrong fees. Only amounts where `amount × 0.02` is already a whole number produce correct results.

At scale (100,000 transactions/day), systematic truncation causes approximately ₹100,000 daily revenue loss.

**What the fix looks like:**

```python
fee = Decimal(amount) * Decimal("0.02")
# or with proper rounding:
return (amount * _FEE_RATE).quantize(_CENT, rounding=ROUND_HALF_UP)
```

**Gherkin Tests (features/fee_calculation.feature):**

```gherkin
# These scenarios FAIL on buggy code -- int() truncates instead of rounding
Scenario Outline: Fee rounds half-up correctly for amounts requiring rounding
  Given a transaction amount of "<amount>"
  When I calculate the fee
  Then the fee should be "<expected_fee>"

  Examples: Amounts where int() truncation causes wrong result
    | amount | expected_fee |
    | 812.36 | 16.25        |
    | 506.88 | 10.14        |
    | 279.96 | 5.60         |
    | 239.41 | 4.79         |
    | 4.89   | 0.10         |
    | 24.35  | 0.49         |
    | 70.45  | 1.41         |
    | 172.30 | 3.45         |
    | 320.90 | 6.42         |

Scenario: Majority of dataset transactions have correct fees
  Given the sample transaction dataset
  When I calculate fees for all transactions
  Then at least 95 out of 100 transactions should have the correct fee
```

**Behave result on buggy code:**
```
Scenario: Fee for 812.36 should be 16.25
  ASSERT FAILED: Fee mismatch for amount 812.36:
    Expected: 16.25
    Got:      16

Scenario: Majority of dataset transactions have correct fees
  ASSERT FAILED: Only a small fraction of transactions have the correct fee (threshold: 95).
  Wrong fees on majority of transactions: TXN1003 expected=16.25 got=16,
  TXN1004 expected=10.14 got=10, TXN1005 expected=5.60 got=5 ... and many more
```

---

## Gherkin Test Suite Results

Run with `python -m behave`. The test suite is the validation mechanism — not the pipeline output.

| Version | Features | Scenarios | Steps |
|---|---|---|---|
| **Buggy (this repo)** | 1 passed, 4 failed | 29 passed, 15 failed | 140 passed, 15 failed |
| **Clean (all bugs fixed)** | 5 passed, 0 failed | 26 passed, 0 failed | 82 passed, 0 failed |

The pipeline output (`python pipeline.py`) is **identical** in both versions:

```
INFO: Pipeline complete -- Total: 100 | SUCCESS: 96 | FAILED: 4
```

Running the pipeline tells you nothing. Only `behave` reveals the defects.

### Test Files

| Feature File | Tests Happy Path | Tests Defect |
|---|---|---|
| `features/audit_logging.feature` | 4 scenarios | SN-01: 2 scenarios fail |
| `features/transaction_validation.feature` | 7 scenarios | SN-02: 4 scenarios fail |
| `features/authentication.feature` | 5 scenarios | SN-03: 1 scenario fails |
| `features/fee_calculation.feature` | 5 scenarios | SN-04: 10 scenarios fail |
| `features/pipeline.feature` | 6 end-to-end scenarios | — |

---

## Defect Summary

| Defect ID | File | Line | Category | Severity | One-line Description |
|---|---|---|---|---|---|
| SN-01 | `audit_logger.py` | 49-50 | Silent Failure | Critical | `except: pass` swallows all DB exceptions -- audit records lost with no trace |
| SN-02 | `transaction_validator.py` | 51 | State Mutation | High | `txn["amount"] = int(txn["amount"])` mutates caller's dict, truncating amounts -- fee calculation receives wrong values |
| SN-03 | `authentication.py` | 25 | Security | High | `!=` instead of `hmac.compare_digest()` -- timing side-channel leaks token character by character |
| SN-04 | `fee_calculator.py` | 34 | Logic Error | Medium | `int(amount * rate)` truncates entire fee decimal -- e.g. 199.99 × 2% = 3.9998 → fee charged is 3, not 4 |

---

## Setup Instructions

### 1. Install dependencies

```bash
pip install mysql-connector-python behave
```

### 2. Start MySQL and create the schema

Ensure MySQL 8.0 is running on `localhost:3306`. Open MySQL Workbench, paste the contents of `procedures/schema_and_procedures.sql` and execute. This creates:

- Database: `solonode_db`
- Table: `audit_log`
- Stored procedure: `sp_insert_audit_log`

### 3. Update database credentials

Edit `settings.py`:

```python
DB_CONFIG = {
    "host":     "localhost",
    "database": "solonode_db",
    "user":     "root",
    "password": "your_mysql_password"
}
```

### 4. Set environment variables


**Windows:**
```cmd
set API_TOKEN=SECURE123TOKEN
set PIPELINE_API_TOKEN=SECURE123TOKEN
```

---

## Running the Pipeline

```bash
python pipeline.py
```

## Running BDD Tests

```bash
behave
```

---

## Evaluation Criteria

| Criteria | Description |
|---|---|
| Defect Detection | All 4 seeded defects identified |
| Root Cause Analysis | Accurate explanation of each issue |
| System Stabilization | Pipeline runs without failures after fixes |
| Test Coverage | Unit tests validate each fix |
| Pipeline Execution | Automated workflow executes successfully end-to-end |

---

## Project Structure

```
Claude_Code_Buggy/
├── pipeline.py                         # Entry point -- orchestrates the full pipeline
├── transaction_validator.py            # Validates transaction fields, types, and bounds  [SN-02]
├── authentication.py                   # Authenticates API token                          [SN-03]
├── fee_calculator.py                   # Calculates 2% processing fee                     [SN-04]
├── audit_logger.py                     # Logs each transaction to MySQL                   [SN-01]
├── database.py                         # MySQL connection manager and procedure caller
├── settings.py                         # DB credentials and fee rate
├── data/
│   └── sample_transactions.json        # 100 sample transactions (96 NORMAL + 4 SECURITY_TEST)
├── procedures/
│   └── schema_and_procedures.sql       # MySQL database + table + stored procedure setup
└── features/
    ├── transaction_validation.feature
    ├── authentication.feature
    ├── fee_calculation.feature
    ├── audit_logging.feature
    ├── pipeline.feature
    └── steps/
        └── step_definitions.py
```

---


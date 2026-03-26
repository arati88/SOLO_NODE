# SoloNode — Buggy vs Clean Code Comparison

> Side-by-side comparison of the buggy hackathon version and the clean base code. Shows the exact defect in code, what output changes, and what risk is resolved.

---

## Test Suite Summary

| | Clean Code | Buggy Code |
|---|---|---|
| Features | 5 passed, 0 failed | 1 passed, 4 failed |
| Scenarios | 26 passed, 0 failed | 29 passed, 15 failed |
| Steps | 82 passed, 0 failed | 140 passed, 15 failed |
| Run command | `python -m behave` | `python -m behave` |

**Key insight:** The pipeline output (`python pipeline.py`) looks identical in both versions — `Total: 100 | SUCCESS: 96 | FAILED: 4`. The defects are invisible at the surface. Only the test suite reveals them.

---

## SN-01 — Silent Failure in Audit Logger

**File:** `audit_logger.py` | **Severity:** Critical

### Code Difference

| | Buggy | Clean |
|---|---|---|
| **Line 49** | `except:` | `except Exception:` |
| **Line 50** | `pass` | `logger.exception("Audit logging failed...")` |
| **Line 51** | *(nothing)* | `raise` |

```python
# BUGGY — audit_logger.py lines 47-50
try:
    call_procedure("sp_insert_audit_log", params)
except:
    pass
```

```python
# CLEAN — audit_logger.py lines 47-56
try:
    call_procedure("sp_insert_audit_log", params)
except Exception:
    logger.exception(
        "Audit logging failed for txn_id=%s amount=%s fee=%s status=%s",
        txn_id, amount, fee, status,
    )
    raise
```

### Output Difference — DB Failure Scenario

**Buggy code:**
```
=== BUGGY CODE: DB failure behaviour ===
  log_transaction returned normally — DB error was IGNORED
  No audit record written. No exception. Caller has no idea.
```

**Clean code:**
```
=== CLEAN CODE: DB failure behaviour ===
ERROR: Audit logging failed for txn_id=TXN001 amount=500.00 fee=10.00 status=SUCCESS
  Exception raised to caller: MySQL connection refused
  Caller is notified. Failure is visible.
```

### Behave Test Result

**Buggy:**
```
Scenario: DB failure during audit write raises an exception to the caller
  ASSERT FAILED: Expected an exception to be raised, but log_transaction returned normally.
  This is SN-01: the bare 'except: pass' is swallowing the DB error.

Scenario: DB failure is not silently ignored
  ASSERT FAILED: log_transaction returned normally despite a DB failure.
  This is SN-01: the bare 'except: pass' is hiding the error from the caller.
```

**Clean:**
```
Scenario: DB failure during audit write raises an exception to the caller  PASSED
Scenario: DB failure is not silently ignored                               PASSED
```

### Risk

| | Buggy | Clean |
|---|---|---|
| DB goes down mid-run | Pipeline reports SUCCESS. Zero audit records written. Zero errors visible. | Exception raised. Pipeline marks transaction FAILED. Operations team alerted. |
| Compliance audit | No way to detect missing audit records | Every DB failure is logged and surfaced |

---

## SN-02 — State Mutation in Batch Validator

**File:** `transaction_validator.py` | **Severity:** High

### Code Difference

| | Buggy | Clean |
|---|---|---|
| **Line 51** | `txn["amount"] = int(txn["amount"])` | Not present — no mutation |
| `validate_batch()` | Mutates caller's dicts | Uses `copy.deepcopy(transactions)` |

```python
# BUGGY — transaction_validator.py
def validate_batch(transactions: list) -> list:
    valid = []
    for txn in transactions:
        txn["amount"] = int(txn["amount"])  # mutates the caller's transaction objects directly
        try:
            validate_transaction(txn)
            valid.append(txn)
        except (ValueError, TypeError):
            pass
    return valid
```

```python
# CLEAN — transaction_validator.py
def validate_batch(transactions: list) -> list:
    import copy
    transactions_copy = copy.deepcopy(transactions)
    valid = []
    for txn in transactions_copy:
        try:
            validate_transaction(txn)
            valid.append(txn)
        except (ValueError, TypeError):
            pass
    return valid
```

### Output Difference — Batch with decimal amounts

**Buggy code:**
```
Input:
  TXN001  amount=Decimal("100.50")
  TXN002  amount=Decimal("250.75")
  TXN003  amount=Decimal("75.99")

Caller's amounts after validate_batch (mutated — should be unchanged):
  TXN001  amount=100    <- was 100.50, decimal part lost
  TXN002  amount=250    <- was 250.75, decimal part lost
  TXN003  amount=75     <- was 75.99,  decimal part lost

Fee impact (2% rate):
  TXN001: correct=2.01  charged=2.00  loss=-0.01
  TXN002: correct=5.02  charged=5.00  loss=-0.02
  TXN003: correct=1.52  charged=1.00  loss=-0.52
```

**Clean code:**
```
Input:
  TXN001  amount=Decimal("100.50")
  TXN002  amount=Decimal("250.75")
  TXN003  amount=Decimal("75.99")

Caller's amounts after validate_batch (unchanged):
  TXN001  amount=Decimal("100.50")
  TXN002  amount=Decimal("250.75")
  TXN003  amount=Decimal("75.99")
```

### Behave Test Result

**Buggy:**
```
Scenario: validate_batch does not mutate original transaction amounts
  ASSERT FAILED: Amount for TXN001 was mutated!
    Before: 100.50 (Decimal)
    After:  100 (int)

Scenario: validate_batch returns valid transactions with their original amounts
  ASSERT FAILED: TXN001 in valid result has wrong amount!
    Expected: 100.50
    Got:      100
```

**Clean:**
```
Scenario: validate_batch does not mutate original transaction amounts           PASSED
Scenario: validate_batch returns valid transactions with their original amounts  PASSED
```

### Risk

| | Buggy | Clean |
|---|---|---|
| Transaction amounts | Permanently truncated to int after batch validation | Preserved exactly as passed |
| Fee calculation | Receives int amounts — fractional cents lost | Receives correct Decimal amounts |
| Failure mode | Silent — pipeline continues, fees are under-charged | N/A |

---

## SN-03 — Timing Attack in Authentication

**File:** `authentication.py` | **Severity:** High

### Code Difference

| | Buggy | Clean |
|---|---|---|
| **Line 25** | `if token != api_token:` | `if not hmac.compare_digest(token, api_token):` |
| `import hmac` | Not imported | Imported and used |

```python
# BUGGY — authentication.py line 25
if token != api_token:
    logger.warning("Authentication failure: invalid token presented")
    raise PermissionError("Invalid API token")
```

```python
# CLEAN — authentication.py line 25
if not hmac.compare_digest(token, api_token):
    logger.warning("Authentication failure: invalid token presented")
    raise PermissionError("Invalid API token")
```

### Output Difference — Functional Behaviour

Both versions reject wrong tokens and accept correct ones — **functional output is identical**. The difference is in timing:

| Token | Buggy avg time | Clean avg time |
|---|---|---|
| `AXXXXXXXXXXXXXXX` (0 chars match) | 26.298 µs | ~same for all |
| `SXXXXXXXXXXXXXXX` (1 char match) | 27.027 µs | ~same for all |
| `SECURE123TOKEN` (full match) | 0.529 µs | ~same for all |

With `!=`, each additional matching character adds measurable time. An attacker sends thousands of guesses and uses timing differences to reconstruct the token one character at a time — without triggering lockout.

`hmac.compare_digest()` always takes the same time regardless of how many characters match, eliminating the signal entirely.

### Behave Test Result

**Buggy:**
```
Scenario: Authentication uses constant-time comparison
  ASSERT FAILED: authenticate() does not use hmac.compare_digest().
  This is SN-03: the current implementation uses plain '!=' which leaks token
  information through timing differences.
  Fix: replace 'if token != api_token:' with 'if not hmac.compare_digest(token, api_token):'
```

**Clean:**
```
Scenario: Authentication uses constant-time comparison   PASSED
```

### Risk

| | Buggy | Clean |
|---|---|---|
| Token leakage | Character-by-character via response timing | No timing signal — all rejections take equal time |
| Attack feasibility | Automatable with ~10,000 requests per character | Not feasible — no measurable signal |

---

## SN-04 — Fee Rounding Error

**File:** `fee_calculator.py` | **Severity:** Medium

### Code Difference

| | Buggy | Clean |
|---|---|---|
| **Line 34** | `Decimal(int(amount * _FEE_RATE))` | `(amount * _FEE_RATE).quantize(_CENT, rounding=ROUND_HALF_UP)` |
| `ROUND_HALF_UP` | Imported but unused | Imported and used |
| `_CENT` | Defined but unused | Used in `.quantize()` |

```python
# BUGGY — fee_calculator.py line 34
return Decimal(int(amount * _FEE_RATE))
#                   ^^^
#                   int() discards the entire decimal part of the fee
```

```python
# CLEAN — fee_calculator.py line 34
return (amount * _FEE_RATE).quantize(_CENT, rounding=ROUND_HALF_UP)
#                            ^^^^^^^^                ^^^^^^^^^^^^^
#                            rounds to 2dp           correct rounding mode
```

### Output Difference — calculate_fee()

```
amount      Clean fee    Buggy fee    Difference
-------------------------------------------------
199.99      4.00         3            -1.00
812.36      16.25        16           -0.25
506.88      10.14        10           -0.14
279.96       5.60         5           -0.60
4.89         0.10         0           -0.10
24.35        0.49         0           -0.49
100.00       2.00         2           (no diff — fee is whole number)
250.00       5.00         5           (no diff — fee is whole number)
500.00      10.00        10           (no diff — fee is whole number)
```

> The bug only produces the correct result when `amount × 0.02` is already a whole number (e.g. 100, 250, 500). All other amounts are under-charged.

### Scale of Impact Across Dataset

| | Clean | Buggy |
|---|---|---|
| Correct fees | 100 / 100 | Minority — only round-fee amounts correct |
| Wrong fees | 0 | Majority of dataset |
| Error magnitude | — | Up to -1.00 per transaction |

### Behave Test Result

**Buggy:**
```
Scenario: Fee for 812.36 should be 16.25
  ASSERT FAILED: Fee mismatch for amount 812.36:
    Expected: 16.25
    Got:      16

Scenario: Majority of dataset transactions have correct fees
  ASSERT FAILED: Only a small fraction of transactions have the correct fee (threshold: 95).
```

**Clean:**
```
Scenario: Fee for 812.36 should be 16.25                              PASSED
Scenario: Majority of dataset transactions have correct fees           PASSED
```

### Risk

| | Buggy | Clean |
|---|---|---|
| Fee accuracy | Most transactions under-charged by up to ₹1 | 100% accurate |
| Revenue loss per 100 txns | Significant (varies by amount distribution) | 0.00 |
| At 100,000 txns/day | ~₹100,000 daily loss | None |

---

## Pipeline Run — Surface Output (Both Versions)

This is what both versions print when you run `python pipeline.py`. **They look identical** — this is why the defects are hard to spot without tests.

```
INFO: Starting pipeline: 100 transactions
INFO: Transaction TXN1001 completed with status SUCCESS
INFO: Transaction TXN1002 completed with status SUCCESS
...
WARNING: Authentication failure: invalid token presented
ERROR: Auth failed for TXN1025
INFO: Transaction TXN1025 completed with status FAILED
...
INFO: Pipeline complete — Total: 100 | SUCCESS: 96 | FAILED: 4
WARNING: Failed transaction TXN1025: Authentication failed.
WARNING: Failed transaction TXN1050: Authentication failed.
WARNING: Failed transaction TXN1075: Authentication failed.
WARNING: Failed transaction TXN1100: Authentication failed.
```

The only way to see the difference is to run `behave`.

---

## Defect Fix Summary

| Defect | File | Buggy Line | Fix |
|---|---|---|---|
| SN-01 | `audit_logger.py:49` | `except: pass` | `except Exception: logger.exception(...); raise` |
| SN-02 | `transaction_validator.py:51` | `txn["amount"] = int(txn["amount"])` | Use `copy.deepcopy(transactions)` before iterating |
| SN-03 | `authentication.py:25` | `if token != api_token:` | `if not hmac.compare_digest(token, api_token):` |
| SN-04 | `fee_calculator.py:34` | `Decimal(int(amount * _FEE_RATE))` | `(amount * _FEE_RATE).quantize(_CENT, rounding=ROUND_HALF_UP)` |

---


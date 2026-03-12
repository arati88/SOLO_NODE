# SoloNode Transaction Audit – Design Document

## 1. Introduction

### Purpose

The purpose of this Proof of Concept (POC) is to demonstrate **AI-assisted debugging and system stabilization** using a simulated transaction processing system. The system will intentionally contain defects that engineers must identify and resolve using **Claude AI assistance**.

### Concept

The POC follows a **Solo Hackathon-style debugging challenge** where an individual engineer receives a codebase with intentionally injected defects. The participant analyzes system behavior, collaborates with **Claude AI** to diagnose issues, and stabilizes the system.

### Key Goals

- Simulate a real-world debugging environment  
- Evaluate AI-assisted engineering workflows  
- Measure how effectively engineers collaborate with AI tools  
- Provide a structured environment for defect discovery and resolution

- ## 2. Implementation Strategy

The system will be developed in three stages.

---

### Stage 1 – Base System Development

A clean and correct transaction processing system will be implemented with modular architecture.

This base system will:

- Accept transaction inputs  
- Validate transaction structure  
- Verify API authentication  
- Calculate transaction fees  
- Log transaction activity  

The base version will serve as the reference implementation before defect injection.

---

### Stage 2 – Defect Injection

Once the base system is stable, controlled defects will be injected across different modules.

These defects will simulate common real-world software issues.

| Defect Category | Purpose |
|-----------------|---------|
| Silent Failure | Test debugging of hidden failures |
| State Mutation | Detect unintended data modification |
| Security Vulnerability | Identify insecure authentication logic |
| Logic Error | Identify incorrect business calculations |

---

### Stage 3 – Debugging Challenge

Participants will receive only the buggy version of the system.

They will:

- Run the system  
- Observe incorrect behavior  
- Use Claude AI to analyze the issue  
- Identify root causes  
- Implement fixes  

Their debugging process and AI interactions will be documented.

## 3. System Architecture

The system follows a **modular pipeline architecture**, where each component performs a specific responsibility.

### Architecture Components

| Module | Responsibility |
|------|------|
| `main.py` | Entry point that orchestrates transaction processing |
| `validation.py` | Validates transaction structure and required fields |
| `security.py` | Verifies API token authentication |
| `fee.py` | Calculates transaction processing fees |
| `audit.py` | Records transaction logs and audit data |

---

## 4. System Workflow

The system processes transactions through a **sequential pipeline**.

### Processing Steps

1. Transaction request is received  
2. Input validation checks transaction structure  
3. Security module verifies API token  
4. Fee module calculates transaction fee  
5. Audit module records the transaction  
6. System returns transaction result  

---

## 5. Processing Flow Diagram

```
Transaction Input
        |
        v
  validation.py
        |
        v
   security.py
        |
        v
     fee.py
        |
        v
    audit.py
        |
        v
Transaction Result
```
This pipeline ensures **separation of responsibilities**, making debugging easier.

## 6. Defect Injection Strategy

Defects will be distributed across system modules.

| Defect ID | Module | Category | Description |
|-----------|--------|----------|-------------|
| SN-01 | `audit.py` | Silent Failure | Exception swallowed by `except: pass` |
| SN-02 | `validation.py` | State Mutation | Input list mutated during validation |
| SN-03 | `security.py` | Security Vulnerability | Token compared using `==` |
| SN-04 | `fee.py` | Logic Error | Incorrect fee calculation |


## 7. Defect Scenarios

### SN-01 – Silent Failure in Audit Logging

**Module:** `audit.py`  
**Category:** Silent Failure  
**Severity:** Critical  
**Root Cause:** Exception swallowed using `except: pass`

---

## Example

Consider a **payment gateway system** processing thousands of transactions per minute.

A transaction is successfully processed:

- **Transaction ID:** TXN10283  
- **Amount:** ₹5000  
- **Status:** SUCCESS  

However, due to a temporary database issue, the **audit logging fails**. Because the exception is silently ignored, the transaction is **never recorded in the audit logs**.

Later during **financial reconciliation**:

- Finance teams cannot locate the transaction in audit logs  
- Compliance teams cannot trace the transaction history  
- The system appears to have lost transactions  

This type of defect is extremely dangerous because the system **appears to work correctly while silently losing critical operational data**.

---

## Correct Fix

Replace the silent exception with **explicit error handling**.

```
python
except Exception as e:
    logger.error(f"Audit logging failed: {e}")
    raise
 id="pmzog4"
```

## How Participants Will Notice the Defect

Participants will execute the transaction system with the provided dataset.

### Example Transaction

- **Transaction ID:** TXN10283  
- **Amount:** ₹5000  
- **Status:** SUCCESS  

The system reports that the transaction was processed successfully.

However, when participants inspect the **audit logs**, they may notice that some transactions are missing.

### Example Audit Log
```
TXN10281
TXN10282
TXN10284
```

Transaction **TXN10283** is missing even though it was processed successfully.

This inconsistency indicates that the **audit logging system may not be recording all transactions**.

---

## Participant Investigation

Participants will trace the **transaction pipeline**:

```
Transaction Input
        |
        v
  validation.py
        |
        v
   security.py
        |
        v
     fee.py
        |
        v
    audit.py

```


Since the issue involves **missing logs**, they will inspect the **`audit.py` module**.

Inside the code they may find the following implementation:

```
python
try:
    write_to_audit_store(transaction)
except:
    pass
```

At this point participants may suspect that errors during audit logging are being silently ignored.

----

## SN-02 – State Mutation in Transaction Validation

**Module:** `validation.py`  
**Category:** State Mutation  
**Severity:** High  
**Root Cause:** Input list modified during validation without defensive copy

---

### Example:

Consider a **payment gateway system** processing batch transactions from merchants.

A merchant submits a batch request:

- **Batch ID:** BATCH4582

### Transactions
```
- **TXN1001** – Amount: ₹100.50  
- **TXN1002** – Amount: ₹250.75  
- **TXN1003** – Amount: ₹75.99
```

During validation, the system converts transaction amounts to integers for format checking.
```
100.50 → 100
250.75 → 250
75.99 → 75
```

However, the **validation module modifies the original transaction objects directly** instead of working on a copy.

Later in the processing pipeline, the **fee calculation module receives modified values**, resulting in incorrect fee calculations.

### Example

- **Original amount:** ₹100.50  
- **Correct fee (2%):** ₹2.01  

After mutation:

- **Modified amount:** ₹100  
- **Calculated fee:** ₹2.00  

While the difference seems small, at scale it creates **financial discrepancies across large transaction volumes**.

---

### Correct Fix

Use **defensive copying** to prevent modifying original data.
```
python

transactions_copy = copy.deepcopy(transactions)
 id="q07xvo"
```

### Participant Investigation

Participants trace the **transaction pipeline** to determine where the modification occurs.

validation → security → fee → audit


Since the amount appears to change **before fee calculation**, they investigate **`validation.py`**.

Inside the validation module they may find code similar to:
```
python
for txn in transactions:
    txn["amount"] = int(txn["amount"])
```
Participants may compare the expected transaction values with the values observed during fee calculation.

| Transaction ID | Expected Amount | Actual Amount Used by System |
|----------------|----------------|------------------------------|
| TXN1001 | ₹100.50 | ₹100 |
| TXN1002 | ₹250.75 | ₹250 |
| TXN1003 | ₹75.99 | ₹75 |
---

## SN-03 – Insecure Token Comparison

**Module:** `security.py`  
**Category:** Security Vulnerability  
**Severity:** High  
**Root Cause:** Token compared using `==`

---

## Example:

Consider a **payment gateway API** used by merchants to submit transactions.

### Example Request
```
- Merchant ID: M102  
- API Token: ABF23D89XK92  
- Transaction ID: TXN20384  
- Amount: ₹3500  
```
The **security module verifies the API token** before processing the transaction.

## Authentication Logic

The authentication logic compares tokens directly.
```
python
if provided_token == expected_token
```

This approach introduces a timing attack vulnerability.

Attackers can send repeated requests with partial token guesses and measure response time differences to reconstruct the correct token.

Once the token is discovered:

- Attackers may submit fraudulent transactions
- Unauthorized systems can access the payment API
- Security breaches may occur

## Correct Fix

Use **constant-time comparison**.
```
python
import hmac

hmac.compare_digest(provided_token, expected_token)
```

### How Participants Will Notice the Defect

This defect is intentionally subtle.

Participants running the system will observe:

- Transactions with valid tokens succeed  
- Transactions with invalid tokens fail  
- No visible errors in logs  

So initially, nothing appears wrong.

The defect becomes noticeable only when participants inspect the **authentication implementation in the security module**.

While reviewing `security.py`, they may see:
```
python
if provided_token == expected_token
```

At this point participants may begin questioning:

- Is direct token comparison secure?
- Are there recommended security practices for comparing authentication tokens?
- Could this introduce a vulnerability?

Participants may then consult Claude AI to analyze the code.

----

## SN-04 – Fee Calculation Rounding Error

**Module:** `fee.py`  
**Category:** Logic Error  
**Severity:** Medium  
**Root Cause:** Integer arithmetic used in financial calculation

---

### Example:

Consider a **digital payment platform** charging a **2% processing fee**.

### Example Transaction
```
Transaction ID: TXN30921
Amount: ₹199.99  
Processing Fee: 2%
```
### Correct Calculation
```
199.99 × 2% = 3.9998
Rounded Fee = ₹4.00
```
### System Calculation

```
python
fee = int(amount * 0.02)
```

Result
```
int(3.9998) = 3
```

The system undercharges the fee.

Across thousands of transactions:
```
Loss per transaction: ₹1
Transactions per day: 100,000
Daily loss: ₹100,000
```

## Correct Fix

Use **precise decimal arithmetic**.
```
python
from decimal import Decimal

fee = Decimal(amount) * Decimal("0.02")
```

## 8. System Artifacts

The POC maintains three versions of the system.

| Artifact | Description |
|----------|-------------|
| Base Code | Clean and correct system implementation |
| Buggy Code | Version containing injected defects |
| Solution Code | Internal reference implementation |

The **buggy version** will be provided to participants, while the **solution version remains internal**.

## 9. AI Collaboration Workflow

Participants will use **Claude AI** during debugging.

### Typical Workflow

1. Engineer observes system failure  
2. Engineer writes prompt to Claude  
3. Claude suggests possible fixes  
4. Engineer evaluates the suggestion  
5. Engineer modifies or implements solution  
6. Engineer documents the interaction  

This process measures **AI collaboration effectiveness**.

## 10. Expected Outcomes

- Effectiveness of AI-assisted debugging  
- Engineer ability to analyze system architecture  
- Quality of AI collaboration  
- Accuracy of bug diagnosis

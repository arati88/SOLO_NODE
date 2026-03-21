# SoloNode Transaction Audit System

> A secure, production-grade financial transaction processing pipeline built in Python — validates, authenticates, calculates fees, and writes immutable audit records to a MySQL database.

---

## Problem Statement

Financial systems that process transactions manually face three core risks:

- **Data corruption** — using `float` arithmetic for money introduces rounding errors that compound over thousands of transactions
- **No audit trail** — without a persistent, append-only log, there is no forensic record if a transaction dispute arises
- **No authentication** — processing transactions without validating the caller's identity exposes the pipeline to unauthorised access

These are not theoretical risks. They are the root cause of real compliance failures under PCI-DSS and SOX.

---

## Solution

SoloNode solves these problems with a layered pipeline that enforces security and correctness at every step:

1. **Authenticate first** — every request is verified using constant-time token comparison before any business logic runs
2. **Validate strictly** — transaction structure, field types, and amount bounds are enforced using `Decimal`, not `float`
3. **Calculate precisely** — fees use `Decimal.quantize` with `ROUND_HALF_UP`, not floating-point arithmetic
4. **Audit immutably** — every transaction result (success or failure) is written to MySQL via a stored procedure and never deleted

---

## Features

| Feature | Detail |
|---|---|
| Constant-time authentication | `hmac.compare_digest` prevents timing-based token inference |
| Decimal financial arithmetic | `Decimal` with `ROUND_HALF_UP` — no float precision loss |
| Strict input validation | Type checks, empty-string guards, upper bound limits |
| Immutable audit log | Append-only MySQL records — never wiped between runs |
| Structured logging | All output via `logging` — compatible with Datadog, CloudWatch |
| Environment-based secrets | API tokens loaded from env vars — never in source code |
| BDD test coverage | 26 scenarios across 5 modules, fully mocked — no live DB needed |

---

## Project Structure

```
Claude_Code/
├── pipeline.py                         # Entry point — orchestrates the full pipeline
├── transaction_validator.py            # Validates transaction fields, types, and bounds
├── authentication.py                   # Authenticates API token (constant-time comparison)
├── fee_calculator.py                   # Calculates 2% processing fee using Decimal
├── audit_logger.py                     # Logs each transaction to MySQL via stored procedure
├── database.py                         # MySQL connection manager and procedure caller
├── settings.py                         # DB credentials and fee rate (non-sensitive settings only)
├── data/
│   ├── sample_transactions.json        # Input — 100 sample transactions
│   └── solonode.db                     # Legacy SQLite file (superseded by MySQL)
├── procedures/
│   └── schema_and_procedures.sql       # MySQL database + table + stored procedure setup
└── features/
    ├── transaction_validation.feature  # 7 BDD scenarios for transaction_validator.py
    ├── authentication.feature          # 4 BDD scenarios for authentication.py
    ├── fee_calculation.feature         # 5 BDD scenarios for fee_calculator.py
    ├── audit_logging.feature           # 4 BDD scenarios for audit_logger.py
    ├── pipeline.feature                # 6 BDD scenarios for pipeline.py
    └── steps/
        └── step_definitions.py        # All BDD step definitions
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.8+ |
| Financial arithmetic | `decimal.Decimal` with `ROUND_HALF_UP` |
| Authentication | `hmac.compare_digest` (constant-time) |
| Database | MySQL 8.0 |
| DB driver | `mysql-connector-python` |
| BDD testing | `behave` (Gherkin syntax) |
| Test isolation | `unittest.mock.patch` + `patch.dict(os.environ)` |

---

## Setup Instructions

### 1. Install dependencies

```bash
pip install mysql-connector-python behave
```

### 2. Start MySQL Server

Ensure MySQL 8.0 is running on `localhost:3306`.

### 3. Create the database, table, and stored procedure

Open MySQL Workbench, paste the contents of `procedures/schema_and_procedures.sql` and execute. This creates:

- Database: `solonode_db`
- Table: `audit_log`
- Stored procedure: `sp_insert_audit_log`

### 4. Update database credentials

Edit `settings.py` with your MySQL password:

```python
DB_CONFIG = {
    "host":     "localhost",
    "database": "solonode_db",
    "user":     "root",
    "password": "your_mysql_password"
}
```

### 5. Set environment variables

**macOS / Linux:**
```bash
export API_TOKEN="your_api_token_here"
export PIPELINE_API_TOKEN="your_api_token_here"
```

**Windows:**
```cmd
set API_TOKEN=your_api_token_here
set PIPELINE_API_TOKEN=your_api_token_here
```

> Both variables must be set. `API_TOKEN` is read by `authentication.py` on each request. `PIPELINE_API_TOKEN` is the token passed into the pipeline at startup from `pipeline.py`.

---

## Usage

### Run the pipeline

```bash
python pipeline.py
```

The pipeline reads `data/sample_transactions.json`, processes each transaction through the full chain, and writes audit records to MySQL.

### Run the BDD tests

```bash
behave
```

All 26 scenarios run in under 1 second — no live database needed.

### Query audit results in MySQL Workbench

```sql
-- All records
SELECT * FROM solonode_db.audit_log;

-- Successful transactions only
SELECT * FROM solonode_db.audit_log WHERE status = 'SUCCESS';

-- Failed transactions only
SELECT * FROM solonode_db.audit_log WHERE status = 'FAILED';

-- Summary by status
SELECT status, COUNT(*) AS total FROM solonode_db.audit_log GROUP BY status;
```

---

## Pipeline Architecture

Each transaction passes through the following layers in order. Authentication always runs first — an unauthenticated caller cannot reach validation or see error messages that reveal internal structure.

```
sample_transactions.json
          |
     pipeline.py          ← reads input, loops transactions, logs summary
          |
authentication.py         ← AUTH FIRST — verifies API token (constant-time comparison)
          |
transaction_validator.py  ← checks fields, Decimal type, positive value, upper bound
          |
  fee_calculator.py       ← calculates 2% fee — Decimal precision, ROUND_HALF_UP
          |
   audit_logger.py        ← validates inputs, calls stored procedure, re-raises on failure
          |
     database.py          ← manages MySQL connection, executes callproc()
          |
    solonode_db           ← MySQL audit_log table (append-only)
```

---

## Results / Expected Output

### Pipeline run

```
INFO: Starting pipeline: 100 transactions
INFO: Transaction TXN1001 completed with status SUCCESS
INFO: Transaction TXN1002 completed with status SUCCESS
...
ERROR: Auth failed for TXN1025
...
INFO: Pipeline complete — Total: 100 | SUCCESS: 96 | FAILED: 4
WARNING: Failed transaction TXN1025: Authentication failed.
WARNING: Failed transaction TXN1050: Authentication failed.
WARNING: Failed transaction TXN1075: Authentication failed.
WARNING: Failed transaction TXN1100: Authentication failed.
```

### BDD test run

```
5 features passed, 0 failed, 0 skipped
26 scenarios passed, 0 failed, 0 skipped
82 steps passed, 0 failed, 0 skipped
Took 0min 0.081s
```

### MySQL audit_log (sample rows)

| id | transaction_id | amount | fee | status | created_at |
|---|---|---|---|---|---|
| 1 | TXN1001 | 767.67 | 15.35 | SUCCESS | 2026-03-20 10:00:01 |
| 2 | TXN1002 | 199.99 | 4.00 | SUCCESS | 2026-03-20 10:00:01 |
| 3 | TXN1025 | 450.00 | 0.00 | FAILED | 2026-03-20 10:00:02 |

---

## Database Schema

### Table: `audit_log`

| Column | Type | Description |
|---|---|---|
| `id` | INT AUTO_INCREMENT | Primary key |
| `transaction_id` | VARCHAR(50) | Unique transaction identifier |
| `amount` | DECIMAL(10,2) | Original transaction amount |
| `fee` | DECIMAL(10,2) | Calculated 2% processing fee |
| `status` | VARCHAR(20) | `SUCCESS` or `FAILED` |
| `created_at` | TIMESTAMP | Auto-set on insert |

### Stored Procedure: `sp_insert_audit_log`

Accepts four parameters — `transaction_id`, `amount`, `fee`, `status` — and inserts one row into `audit_log`. Called from Python via `database.py` using `cursor.callproc()`. The procedure is the only write path — no raw `INSERT` statements exist in Python code.

---

## BDD Test Coverage

Tests are written in Gherkin and run with `behave`. The database layer is fully mocked — no MySQL connection is required.

### How mocking works

**Authentication** — `API_TOKEN` is injected via environment variable:
```python
with patch.dict(os.environ, {'API_TOKEN': 'SECURE123TOKEN'}):
    authenticate(token)
```

**Audit logging** — `call_procedure` is patched to simulate success or failure:
```python
# Simulate a working database
with patch('audit_logger.call_procedure') as mock_proc:
    mock_proc.return_value = None
    log_transaction(txn_id, amount, fee, status)

# Simulate a broken database
with patch('audit_logger.call_procedure') as mock_proc:
    mock_proc.side_effect = Exception("DB connection failed")
    log_transaction(txn_id, amount, fee, status)
```

**Pipeline** — `log_transaction` is mocked and `API_TOKEN` is set:
```python
with patch.dict(os.environ, {'API_TOKEN': 'SECURE123TOKEN'}):
    with patch('pipeline.log_transaction') as mock_log:
        result = process_transaction(txn, token)
```

### Scenario breakdown

| Feature File | Scenarios | Key cases covered |
|---|---|---|
| `transaction_validation.feature` | 7 | Happy path, missing fields, string amount, negative, zero |
| `authentication.feature` | 4 | Valid token, wrong token, empty token, partial token |
| `fee_calculation.feature` | 5 | Decimal amount, whole number, small, large, precision |
| `audit_logging.feature` | 4 | Success log, failure log, DB error propagation, no silent swallow |
| `pipeline.feature` | 6 | Happy path, invalid amount, wrong token, failed logged, success logged, missing field |

---

## Security Notes

- `hmac.compare_digest` ensures token comparison takes the same time regardless of where strings differ — prevents attackers from inferring token values by measuring response time
- API tokens are read from environment variables at call time — never hardcoded in source files or `settings.py`
- Authentication runs **before** validation in `pipeline.py` — unauthenticated callers cannot probe the input structure via validation error messages
- Error messages returned to callers are generic (`"Invalid transaction data."`, `"Authentication failed."`) — internal details are logged server-side only
- Audit records are append-only — the pipeline never deletes rows, satisfying PCI-DSS and SOX forensic requirements
- Failed transactions are still written to the audit log with `fee = 0` and `status = FAILED` — every event is traceable

---

## Future Improvements

| Improvement | Why |
|---|---|
| Pydantic model for transaction validation | Replaces manual dict checks in `transaction_validator.py` with a typed, self-documenting contract |
| Token rotation without restart | Load `API_TOKEN` from a secrets manager (AWS Secrets Manager, HashiCorp Vault) |
| Dead-letter queue on audit failure | Currently a failed audit write re-raises — a DLQ ensures no record is permanently lost |
| Currency field validation | Amounts without an ISO 4217 currency code are ambiguous in multi-currency systems |
| Rate limiting on authentication | Repeated failed auth attempts should trigger alerting and backoff |
| Async processing | For high-volume pipelines, `asyncio` or a task queue (Celery, RQ) would improve throughput |
| Containerisation | Dockerise the pipeline and MySQL to remove local setup friction |

---

## Contributors

| Name | Role |
|---|---|
| Arati | Developer — initial design, implementation, and BDD test authoring |

---

*Built as base code for a Hackathon. Reviewed and hardened to production-grade financial standards.*

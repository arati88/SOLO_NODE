# SoloNode Transaction Audit System

A modular Python transaction processing pipeline that validates, authenticates, calculates fees, and audits financial transactions into a MySQL database via stored procedures.(Initial code setup for Hackathon)

---

## Project Structure

```
Claude_Code/
├── main.py                         # Entry point — orchestrates the pipeline
├── validation.py                   # Validates transaction fields and amount
├── security.py                     # Authenticates API token
├── fee.py                          # Calculates 2% processing fee
├── audit.py                        # Logs each transaction to the database
├── db.py                           # MySQL connection and procedure caller
├── config.py                       # Centralised settings (DB, token, fee rate)
├── data/
│   ├── transactions.json           # Input — 100 sample transactions
│   └── solonode.db                 # Legacy SQLite file (replaced by MySQL)
└── procedures/
    └── transaction_procedure.sql   # MySQL database + table + stored procedure
```

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.8+ |
| MySQL Server | 8.0 |
| mysql-connector-python | Latest |

### Install Python dependency

```bash
pip install mysql-connector-python
```

---

## Database Setup

### 1. Start MySQL Server

Ensure MySQL 8.0 is running on `localhost:3306`.

### 2. Run the SQL setup script

Open MySQL Workbench, paste the contents of `procedures/transaction_procedure.sql` and execute it. This will:

- Create database `solonode_db`
- Create table `audit_log`
- Create stored procedure `sp_insert_audit_log`

### 3. Verify credentials in config.py

```python
DB_CONFIG = {
    "host":     "localhost",
    "database": "solonode_db",
    "user":     "root",
    "password": "password"
}
```

Update the password if your MySQL root password is different.

---

## Running the Pipeline

```bash
python main.py
```

That is the only command needed. The pipeline will:

1. Read 100 transactions from `data/transactions.json`
2. Clear the `audit_log` table (fresh run every time)
3. Process each transaction through the pipeline
4. Print a summary to the terminal

---

## Expected Output

```
INFO: Starting pipeline: 100 transactions
INFO: {'transaction_id': 'TXN1001', 'status': 'SUCCESS', 'fee': 15.35}
INFO: {'transaction_id': 'TXN1002', 'status': 'SUCCESS', 'fee': 5.89}
...
ERROR: Auth failed for TXN1025: Invalid API token
...

=============================================
           PIPELINE SUMMARY
=============================================
  Total Transactions : 100
  SUCCESS            : 96
  FAILED             : 4

  Failed Transactions:
    - TXN1025: Invalid API token
    - TXN1050: Invalid API token
    - TXN1075: Invalid API token
    - TXN1100: Invalid API token
=============================================
```

---

## Pipeline Architecture

```
transactions.json
        |
     main.py          — reads input, loops transactions, prints summary
        |
 validation.py        — checks required fields, type, and positive amount
        |
  security.py         — verifies API token using constant-time comparison
        |
     fee.py           — calculates 2% fee using Decimal precision
        |
   audit.py           — calls stored procedure to save result
        |
     db.py            — manages MySQL connection
        |
  solonode_db         — MySQL database (audit_log table)
```

---

## Module Responsibilities

| File | Responsibility |
|---|---|
| `main.py` | Orchestrates the full pipeline, handles errors, prints summary |
| `validation.py` | Validates transaction structure and amount |
| `security.py` | Authenticates API token using `hmac.compare_digest` |
| `fee.py` | Calculates fee using `Decimal` for financial precision |
| `audit.py` | Logs transaction result to MySQL via stored procedure |
| `db.py` | Opens MySQL connection, clears table, calls stored procedures |
| `config.py` | Single source of truth for DB credentials, token, and fee rate |

---

## Database Schema

### Table: `audit_log`

| Column | Type | Description |
|---|---|---|
| `id` | INT AUTO_INCREMENT | Primary key |
| `transaction_id` | VARCHAR(50) | Unique transaction identifier |
| `amount` | DECIMAL(10,2) | Original transaction amount |
| `fee` | DECIMAL(10,2) | Calculated 2% fee |
| `status` | VARCHAR(20) | SUCCESS or FAILED |
| `created_at` | TIMESTAMP | Auto-set on insert |

### Stored Procedure: `sp_insert_audit_log`

Accepts four parameters — `transaction_id`, `amount`, `fee`, `status` — and inserts one row into `audit_log`. Called by Python via `db.py` using `cursor.callproc()`.

---

## Configuration

All settings live in `config.py`:

| Setting | Default | Description |
|---|---|---|
| `DB_CONFIG.host` | `localhost` | MySQL host |
| `DB_CONFIG.database` | `solonode_db` | Database name |
| `DB_CONFIG.user` | `root` | MySQL username |
| `DB_CONFIG.password` | `password` | MySQL password |
| `API_TOKEN` | `SECURE123TOKEN` | Valid token for authentication |
| `FEE_PERCENTAGE` | `0.02` | Processing fee rate (2%) |

---

## BDD Tests (Behaviour-Driven Development)

Tests are written in Gherkin syntax and executed using the `behave` framework. They cover all four core modules without requiring a live database — the DB layer is fully mocked.

### Install behave

```bash
pip install behave
```

### Test Structure

```
Claude_Code/
└── features/
    ├── validation.feature      # 7 scenarios for validation.py
    ├── security.feature        # 4 scenarios for security.py
    ├── fee.feature             # 5 scenarios for fee.py
    ├── audit.feature           # 4 scenarios for audit.py
    ├── main.feature            # 6 scenarios for main.py
    └── steps/
        └── steps.py            # All step definitions
```

### Running the Tests

```bash
C:\Users\HP\AppData\Roaming\Python\Python313\Scripts\behave.exe
```

Or if `behave` is on your PATH:

```bash
behave
```

### Expected Test Output

```
5 features passed, 0 failed, 0 skipped
26 scenarios passed, 0 failed, 0 skipped
82 steps passed, 0 failed, 0 skipped
Took 0min 0.081s
```

### Feature Breakdown

#### main.feature — 6 Scenarios

| Scenario | Covers |
|---|---|
| Valid transaction is processed successfully | Happy path — returns SUCCESS status and a calculated fee |
| Transaction with invalid amount is rejected | Negative amount → FAILED status with error message |
| Transaction with wrong token is rejected | Bad token → FAILED status with error message |
| Failed transaction is still logged to audit DB | Verifies `log_transaction` is called with `FAILED` |
| Successful transaction is logged to audit DB | Verifies `log_transaction` is called with `SUCCESS` |
| Transaction with missing field returns FAILED | Incomplete input → FAILED status with error message |

#### validation.feature — 7 Scenarios

| Scenario | Covers |
|---|---|
| Valid transaction passes validation | Happy path — all fields present and valid |
| Missing `transaction_id` is rejected | Raises `ValueError: Missing field transaction_id` |
| Missing `amount` is rejected | Raises `ValueError: Missing field amount` |
| Missing `merchant_id` is rejected | Raises `ValueError: Missing field merchant_id` |
| Amount as string is rejected | Raises `TypeError` for non-numeric amount |
| Negative amount is rejected | Raises `ValueError: Amount must be positive` |
| Zero amount is rejected | Raises `ValueError: Amount must be positive` |

#### security.feature — 4 Scenarios

| Scenario | Covers |
|---|---|
| Correct token is accepted | Valid token returns `True` |
| Wrong token is rejected | Raises `PermissionError: Invalid API token` |
| Empty token is rejected | Raises `PermissionError: Invalid API token` |
| Partial token is rejected | Raises `PermissionError: Invalid API token` |

#### fee.feature — 5 Scenarios

| Scenario | Input | Expected Fee |
|---|---|---|
| Decimal amount | 767.67 | 15.35 |
| Whole number | 100.00 | 2.00 |
| Small amount | 0.10 | 0.00 |
| Large amount | 99999.99 | 2000.00 |
| Precision check | 199.99 | 4.00 |

#### audit.feature — 4 Scenarios

| Scenario | Covers |
|---|---|
| Successful transaction is logged | `call_procedure` is called — no exception raised |
| Failed transaction is logged | FAILED status saved without error |
| Database error is logged and re-raised | Exception propagates with `DB connection failed` message |
| Audit failure is never silently swallowed | `logger.error` is called before the exception re-raises |

### How Mocking Works

All tests that touch the database layer use `unittest.mock.patch` to intercept calls so no real MySQL connection is needed.

**Audit tests** — mock `call_procedure` directly:

```python
# Simulates a working database
with patch('audit.call_procedure') as mock_proc:
    mock_proc.return_value = None
    log_transaction(txn_id, amount, fee, status)

# Simulates a broken database
with patch('audit.call_procedure') as mock_proc:
    mock_proc.side_effect = Exception("DB connection failed")
    log_transaction(txn_id, amount, fee, status)
```

**Pipeline (main) tests** — mock `log_transaction` in main to capture the status passed by the pipeline:

```python
with patch('main.log_transaction') as mock_log:
    def capture_log(txn_id, amount, fee, status):
        context.audit_status = status
    mock_log.side_effect = capture_log
    result = process_transaction(txn, token)
```

This ensures all tests are fast, isolated, and environment-independent.

---

## Security Notes

- Token comparison uses `hmac.compare_digest` to prevent timing attacks
- Database credentials are centralised in `config.py` — do not commit real passwords to version control
- Failed transactions (invalid token) are logged to the database with `fee = 0` and `status = FAILED`

---

## Verifying Results in MySQL Workbench

```sql
-- All transactions
SELECT * FROM solonode_db.audit_log;

-- Only successful
SELECT * FROM solonode_db.audit_log WHERE status = 'SUCCESS';

-- Only failed
SELECT * FROM solonode_db.audit_log WHERE status = 'FAILED';

-- Count
SELECT status, COUNT(*) as total FROM solonode_db.audit_log GROUP BY status;
```

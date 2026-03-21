"""
Transaction processing orchestration layer.
Validates, authenticates, calculates fees, and audits each transaction end-to-end.
"""
import json
import logging
import os
from decimal import Decimal

from transaction_validator import validate_transaction
from authentication import authenticate
from fee_calculator import calculate_fee
from audit_logger import log_transaction

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _safe_log_failure(txn: dict) -> None:
    """Attempt to write a FAILED audit entry, swallowing any logging errors."""
    try:
        log_transaction(
            txn.get("transaction_id"),
            txn.get("amount", Decimal("0")),
            Decimal("0"),
            "FAILED",
        )
    except Exception as log_err:
        logger.warning("Audit log failed for %s: %s", txn.get("transaction_id"), log_err)


def process_transaction(txn: dict, token: str) -> dict:
    try:
        # Authenticate before any business logic to avoid leaking
        # structural information to unauthenticated callers
        authenticate(token)
        validate_transaction(txn)
        fee = calculate_fee(txn["amount"])
        log_transaction(txn["transaction_id"], txn["amount"], fee, "SUCCESS")
        return {"transaction_id": txn["transaction_id"], "status": "SUCCESS", "fee": str(fee)}

    except (ValueError, TypeError) as e:
        logger.warning("Validation error for %s: %s", txn.get("transaction_id"), e)
        _safe_log_failure(txn)
        return {"transaction_id": txn.get("transaction_id"), "status": "FAILED", "error": "Invalid transaction data."}

    except PermissionError:
        logger.error("Auth failed for %s", txn.get("transaction_id"))
        _safe_log_failure(txn)
        return {"transaction_id": txn.get("transaction_id"), "status": "FAILED", "error": "Authentication failed."}

    except Exception:
        logger.exception("Unexpected error for %s", txn.get("transaction_id"))
        _safe_log_failure(txn)
        return {"transaction_id": txn.get("transaction_id"), "status": "FAILED", "error": "An unexpected error occurred. Contact support."}


def run_pipeline(file_path: str, token: str) -> None:
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error("Input file not found: %s", file_path)
        raise
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON from %s: %s", file_path, e)
        raise

    transactions = data.get("transactions")
    if not isinstance(transactions, list):
        raise ValueError(f"Expected 'transactions' list in {file_path}, got: {type(transactions)}")

    logger.info("Starting pipeline: %d transactions", len(transactions))
    success, failed, failed_txns = 0, 0, []

    for row in transactions:
        txn = {
            "transaction_id": row["transaction_id"],
            "amount": Decimal(str(row["amount"])),  # Decimal preserves exact financial precision
            "merchant_id": row["merchant_id"],
        }
        txn_token = row.get("token", token)
        result = process_transaction(txn, txn_token)

        logger.info(
            "Transaction %s completed with status %s",
            result["transaction_id"],
            result["status"],
        )

        if result["status"] == "SUCCESS":
            success += 1
        else:
            failed += 1
            failed_txns.append((result["transaction_id"], result.get("error", "")))

    total = len(transactions)
    logger.info(
        "Pipeline complete — Total: %d | SUCCESS: %d | FAILED: %d",
        total, success, failed,
    )
    for txn_id, reason in failed_txns:
        logger.warning("Failed transaction %s: %s", txn_id, reason)


if __name__ == "__main__":
    api_token = os.environ.get("PIPELINE_API_TOKEN")
    if not api_token:
        raise EnvironmentError("PIPELINE_API_TOKEN environment variable is not set")
    run_pipeline("data/sample_transactions.json", api_token)

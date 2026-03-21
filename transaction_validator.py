"""
Transaction validation utilities for the processing pipeline.
"""
from decimal import Decimal

MAX_TRANSACTION_AMOUNT = Decimal("1_000_000.00")


def validate_transaction(txn) -> bool:
    """
    Validate transaction input data before processing.

    Raises:
        TypeError: If txn is not a dict, or amount is the wrong type.
        ValueError: If required fields are missing, empty, or out of range.
    """
    if not isinstance(txn, dict):
        raise TypeError(f"Transaction must be a dict, got {type(txn).__name__}")

    required_fields = ["transaction_id", "amount", "merchant_id"]
    for field in required_fields:
        if field not in txn:
            raise ValueError(f"Missing field: {field}")

    # transaction_id must be a non-empty string
    if not isinstance(txn["transaction_id"], str) or not txn["transaction_id"].strip():
        raise ValueError("transaction_id must be a non-empty string")

    # merchant_id must be a non-empty string
    if not isinstance(txn["merchant_id"], str) or not txn["merchant_id"].strip():
        raise ValueError("merchant_id must be a non-empty string")

    # float is not safe for financial data — callers must pass Decimal
    if not isinstance(txn["amount"], Decimal):
        raise TypeError(f"Amount must be Decimal, got {type(txn['amount']).__name__}")

    if txn["amount"] <= 0:
        raise ValueError("Amount must be positive")

    if txn["amount"] > MAX_TRANSACTION_AMOUNT:
        raise ValueError(f"Amount exceeds maximum allowed: {MAX_TRANSACTION_AMOUNT}")

    return True

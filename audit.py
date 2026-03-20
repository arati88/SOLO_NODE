"""
Audit logging utilities for the transaction processing pipeline.
Writes immutable audit records to the database via stored procedures.
"""
import logging
from decimal import Decimal, InvalidOperation
from typing import Literal

from db import call_procedure

logger = logging.getLogger(__name__)

TransactionStatus = Literal["SUCCESS", "FAILED", "PENDING", "REVERSED"]
_VALID_STATUSES = {"SUCCESS", "FAILED", "PENDING", "REVERSED"}


def log_transaction(
    txn_id: str,
    amount: Decimal,
    fee: Decimal,
    status: TransactionStatus,
) -> None:
    """
    Log a transaction audit record to the database via stored procedure.

    Raises:
        ValueError: If any parameter fails validation.
        Exception: Propagated from call_procedure on DB failure.
                   Callers MUST NOT suppress this — a failed audit write is a compliance event.
    """
    if not txn_id or not isinstance(txn_id, str):
        raise ValueError(f"Invalid txn_id: {repr(txn_id)}")

    try:
        amount = Decimal(str(amount))
        fee = Decimal(str(fee))
    except InvalidOperation:
        raise ValueError(f"Non-numeric amount/fee for txn {txn_id}: {amount}, {fee}")

    if amount < 0 or fee < 0:
        raise ValueError(f"Negative monetary values for txn {txn_id}: {amount}, {fee}")

    if status not in _VALID_STATUSES:
        raise ValueError(f"Unknown status '{status}' for txn {txn_id}")

    params = (txn_id, amount, fee, status)
    try:
        call_procedure("sp_insert_audit_log", params)
    except Exception:
        logger.exception(
            "Audit logging failed for txn_id=%s amount=%s fee=%s status=%s",
            txn_id, amount, fee, status,
        )
        # NOTE: Callers MUST NOT suppress this exception.
        # A failed audit record is a compliance event.
        raise

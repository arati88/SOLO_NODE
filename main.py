"""
This is the main orchestration layer that processes transactions 
end-to-end by validating input, authenticating requests, 
calculating fees, and logging results while handling all
failure scenarios gracefully.
"""

import json
import logging
from db import clear_audit_log
from validation import validate_transaction
from security import authenticate
from fee import calculate_fee
from audit import log_transaction

# ---------------------------------------------------------
# Configure logging for the application
# ---------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Function: process_transaction
# Processes a single transaction end-to-end
# Steps   : Validation → Authentication → Fee Calculation → Audit Logging
# ---------------------------------------------------------
def process_transaction(txn, token):
    try:
        # Step 1: Validate transaction data (amount, structure, etc.)
        validate_transaction(txn)

        # Step 2: Authenticate API token
        authenticate(token)

        # Step 3: Calculate transaction fee
        fee = calculate_fee(txn["amount"])

        # Step 4: Log successful transaction in audit table
        log_transaction(txn["transaction_id"], txn["amount"], fee, "SUCCESS")
        
        # Return success response
        return {"transaction_id": txn["transaction_id"], "status": "SUCCESS", "fee": fee}
    
    # ---------------------------------------------------------
    # Handle validation errors (bad input, wrong data types)
    # ---------------------------------------------------------
    except (ValueError, TypeError) as e:
        # Attempt to log failed transaction
        
        try:
            log_transaction(txn["transaction_id"], txn["amount"], 0, "FAILED")
        except Exception as log_err:
            logger.warning("Audit log failed for %s: %s", txn.get("transaction_id"), log_err)
        return {"transaction_id": txn["transaction_id"], "status": "FAILED", "error": str(e)}
    
    # ---------------------------------------------------------
    # Handle authentication failures
    # ---------------------------------------------------------
    except PermissionError as e:
        logger.error("Auth failed for %s: %s", txn.get("transaction_id"), e)
        try:
            log_transaction(txn["transaction_id"], txn["amount"], 0, "FAILED")
        except Exception as log_err:
            logger.warning("Audit log failed for %s: %s", txn.get("transaction_id"), log_err)
        return {"transaction_id": txn["transaction_id"], "status": "FAILED", "error": str(e)}
    
    # ---------------------------------------------------------
    # Handle unexpected system errors
    # ---------------------------------------------------------
    except Exception as e:
        # Logs full stack trace (very useful for debugging)
        logger.exception("Unexpected error for %s", txn.get("transaction_id"))
        
        try:
            log_transaction(txn["transaction_id"], txn["amount"], 0, "FAILED")
        except Exception:
            pass   # Ignore logging failure in critical error scenario
        return {"transaction_id": txn["transaction_id"], "status": "FAILED", "error": str(e)}


# Function: run_pipeline
# Executes transaction processing pipeline for all records
# Input   : file_path - Path to JSON input file
#           token     - Default API token
# ---------------------------------------------------------
def run_pipeline(file_path, token):
    # Read input JSON file
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
    
    # Extract transactions list
    transactions = data["transactions"]

    # Clear previous audit logs before starting
    clear_audit_log()

    logger.info("Starting pipeline: %d transactions", len(transactions))
    
    # Initialize counters
    success, failed, failed_txns = 0, 0, []
    
    # Process each transaction
    for row in transactions:
        # Normalize transaction structure
        txn = {
            "transaction_id": row["transaction_id"],
            "amount": float(row["amount"]),
            "merchant_id": row["merchant_id"]
        }

        # Use transaction-specific token if available, else default
        txn_token = row.get("token", token)

        # Process transaction
        result = process_transaction(txn, txn_token)

        # Log result
        logger.info(result)
        
        # Track success/failure metrics
        if result["status"] == "SUCCESS":
            success += 1
        else:
            failed += 1
            failed_txns.append((result["transaction_id"], result.get("error", "")))
    
    # Print pipeline summary report
    # ---------------------------------------------------------
    print("\n" + "=" * 45)
    print("           PIPELINE SUMMARY")
    print("=" * 45)
    print(f"  Total Transactions : {len(transactions)}")
    print(f"  SUCCESS            : {success}")
    print(f"  FAILED             : {failed}")
    
    # Print failed transaction details
    if failed_txns:
        print("\n  Failed Transactions:")
        for txn_id, reason in failed_txns:
            print(f"    - {txn_id}: {reason}")
    print("=" * 45)

# Entry point of the program
# ---------------------------------------------------------
if __name__ == "__main__":
    run_pipeline("data/transactions.json", "SECURE123TOKEN")
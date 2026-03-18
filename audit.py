"""
This function logs transaction details into the database 
using a stored procedure, with proper exception handling 
and logging to ensure failures are traceable and not silent
"""

import logging
from db import call_procedure

# Create a logger for this module
logger = logging.getLogger(__name__)

# Function: log_transaction
# Logs transaction details into the audit table
# Inputs  : txn_id - Unique transaction ID
#           amount - Transaction amount
#           fee    - Processing fee
#           status - Transaction status (e.g., SUCCESS/FAILED)
# ---------------------------------------------------------

def log_transaction(txn_id, amount, fee, status):

    # Prepare parameters as a tuple to pass to stored procedure
    params = (txn_id, amount, fee, status)
    
    # Attempt to log transaction into DB via stored procedure
    try:
        # Calls stored procedure: sp_insert_audit_log
        call_procedure("sp_insert_audit_log", params)

    except Exception as e:
        # Log error with transaction ID and exception details
        logger.error("Audit logging failed for %s: %s", txn_id, e)

        # Re-raise the exception so upstream systems are aware of failure
        raise
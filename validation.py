"""
This function validates transaction data by ensuring 
required fields are present, the amount is numeric, and 
the value is positive to prevent invalid data from entering the system.
"""

# ---------------------------------------------------------
# Function: validate_transaction
# Validates transaction input data before processing
# Inputs  : txn - Dictionary containing transaction details
# Returns : True if validation passes
# Raises  : ValueError / TypeError for invalid inputs
# ---------------------------------------------------------

def validate_transaction(txn):
    
    # List of mandatory fields required for a valid transaction
    required_fields = ["transaction_id", "amount", "merchant_id"]
    
    # Check if all required fields are present in the transaction
    for field in required_fields:
        if field not in txn:

            # Raise error if any field is missing
            raise ValueError(f"Missing field {field}")

    # Validate amount field
    # ---------------------------------------------------------
    
    # Prevents runtime errors during fee calculation
    if not isinstance(txn["amount"], (int, float)):
        raise TypeError(f"Amount must be a number, got {type(txn['amount']).__name__}")
    
    # Ensure amount is greater than zero
    if txn["amount"] <= 0:
        raise ValueError("Amount must be positive")
    
    # Return True if all validations pass
    return True
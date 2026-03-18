"""
 This function calculates transaction fees using 
 precise decimal arithmetic to avoid floating-point errors 
 and ensures accurate financial computations.
"""

from decimal import Decimal
from config import FEE_PERCENTAGE

# Function: calculate_fee
# Calculates transaction fee based on percentage
# Inputs  : amount - Transaction amount (float or numeric)
# Returns : Fee rounded to 2 decimal places (float)
# ---------------------------------------------------------

def calculate_fee(amount):

    # Convert amount and percentage to Decimal for precise calculations
    # (avoids floating-point precision issues)
    fee = Decimal(str(amount)) * Decimal(str(FEE_PERCENTAGE))

    # Round fee to 2 decimal places (standard for currency)
    # Convert back to float for compatibility with rest of system
    return float(round(fee, 2))
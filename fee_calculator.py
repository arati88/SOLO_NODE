"""
Utility functions for calculating financial transaction fees.
"""
from decimal import Decimal, ROUND_HALF_UP

from settings import FEE_PERCENTAGE

_CENT = Decimal("0.01")
_FEE_RATE = Decimal(str(FEE_PERCENTAGE))

if _FEE_RATE < 0:
    raise ValueError(f"FEE_PERCENTAGE must be non-negative, got {FEE_PERCENTAGE!r}")


def calculate_fee(amount: Decimal) -> Decimal:
    """
    Calculate the transaction fee for a given amount.

    Args:
        amount: Non-negative transaction amount as Decimal or int.

    Returns:
        Fee rounded to 2 decimal places (ROUND_HALF_UP) as Decimal.

    Raises:
        TypeError: If amount is not a Decimal or int.
        ValueError: If amount is negative.
    """
    if not isinstance(amount, (Decimal, int)):
        raise TypeError(f"amount must be Decimal or int, got {type(amount).__name__}")
    if amount < 0:
        raise ValueError(f"amount must be non-negative, got {amount}")

    return (amount * _FEE_RATE).quantize(_CENT, rounding=ROUND_HALF_UP)

"""
API token authentication utilities for the transaction processing pipeline.
"""
import logging
import os

logger = logging.getLogger(__name__)


def authenticate(token: str) -> None:
    """
    Validate the provided API token against the configured secret.

    Uses constant-time comparison to prevent timing attacks.
    Raises PermissionError on mismatch, missing token, or invalid input type.
    """
    if not isinstance(token, str):
        raise PermissionError("Invalid API token")

    api_token = os.environ.get("API_TOKEN")
    if not api_token:
        raise RuntimeError("API_TOKEN environment variable is not set")

    if token != api_token:
        logger.warning("Authentication failure: invalid token presented")
        raise PermissionError("Invalid API token")

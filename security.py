"""
This function securely validates API tokens using 
constant-time comparison to prevent timing attacks and 
ensure safe authentication
"""
import hmac
from config import API_TOKEN

# Function: authenticate
# Validates API token for secure access
# Inputs  : token - Token provided in the request
# Returns : True if authentication is successful
# Raises  : PermissionError if token is invalid
# ---------------------------------------------------------
def authenticate(token):

    # Use hmac.compare_digest for secure comparison
    # (prevents timing attacks by avoiding early exit comparison)
    if not hmac.compare_digest(token, API_TOKEN):

        # Raise error if token does not match expected value
        raise PermissionError("Invalid API token")
    
    # Return True if authentication is successful
    return True
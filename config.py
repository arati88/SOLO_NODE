"""
 Configuration File: config.py
 Stores application-level configuration values
 Notes   : In production, sensitive data should NOT be hardcoded

"""

# Database configuration dictionary
# Used by db.py to establish MySQL connection
DB_CONFIG = {
    "host": "localhost",        # Database server location
    "database": "solonode_db",  # Database name
    "user": "root",             # Database username
    "password": "password"      # Database password (use env variables in real apps)
}

# API Configuration
# ---------------------------------------------------------

# Token used for authenticating API requests
# Ensures only authorized users/systems can access services
API_TOKEN = "SECURE123TOKEN"

# Business Logic Configuration
# ---------------------------------------------------------

# Fee percentage applied on transactions
# Example: 0.02 = 2% processing fee
FEE_PERCENTAGE = 0.02
"""
 This module manages database operations by handling connections,
 executing stored procedures, and ensuring proper cleanup
 using try-finally blocks.
"""

import mysql.connector   # Python driver to connect to MySQL
from config import DB_CONFIG    # dictionary containing DB credentials

# Function: get_connection
# Establishes and returns a new database connection
# ---------------------------------------------------------
def get_connection():
    return mysql.connector.connect(
        host=DB_CONFIG["host"],           # Database host (e.g., localhost)
        database=DB_CONFIG["database"],   # Database name
        user=DB_CONFIG["user"],           # Username
        password=DB_CONFIG["password"]    # Password
    )


# Function: clear_audit_log
# Clears all records from the audit_log table
# ---------------------------------------------------------
def clear_audit_log():
    conn = get_connection()    # Open DB connection
    try:
        cursor = conn.cursor()  # Create cursor to execute SQL
        try:  
            # Execute SQL command to remove all records             
            cursor.execute("TRUNCATE TABLE audit_log")

            # Commit the transaction to persist changes
            conn.commit()
        finally:
            # Ensure cursor is always closed
            cursor.close()
    finally:
        # Ensure connection is always closed
        conn.close()


# Function: call_procedure
# Executes a stored procedure with given parameters
# Inputs  : proc_name - Name of the stored procedure
#           params    - Tuple of parameters to pass
# Returns : Result set (if the procedure returns data)
# ---------------------------------------------------------
def call_procedure(proc_name, params):
    conn = get_connection()    # Open DB connection
    try:
        cursor = conn.cursor()  # Create cursor
        try:
            # Call the stored procedure with parameters
            cursor.callproc(proc_name, params)

            # Commit transaction (important for insert/update operations)
            conn.commit()

            # Fetch results if the stored procedure returns any
            for result in cursor.stored_results():
                return result.fetchall()    # Return first result set
        finally:
            # Ensure cursor is closed even if error occurs
            cursor.close()
    finally:
        # Ensure connection is always closed
        conn.close()

-- ============================================
-- SoloNode Transaction Audit
-- Stored Procedure: sp_insert_audit_log
-- ============================================

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS solonode_db;
USE solonode_db;

-- Create audit_log table if it doesn't exist
CREATE TABLE IF NOT EXISTS audit_log (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id VARCHAR(50)    NOT NULL,
    amount         DECIMAL(10,2)  NOT NULL,
    fee            DECIMAL(10,2)  NOT NULL,
    status         VARCHAR(20)    NOT NULL,
    created_at     TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
);

-- Drop procedure if it already exists (for clean re-runs)
DROP PROCEDURE IF EXISTS sp_insert_audit_log;

-- Create the stored procedure
DELIMITER $$

CREATE PROCEDURE sp_insert_audit_log(
    IN p_txn_id  VARCHAR(50),
    IN p_amount  DECIMAL(10,2),
    IN p_fee     DECIMAL(10,2),
    IN p_status  VARCHAR(20)
)
BEGIN
    INSERT INTO audit_log (transaction_id, amount, fee, status)
    VALUES (p_txn_id, p_amount, p_fee, p_status);
END$$

DELIMITER ;

-- ============================================================================
-- Purpose: Schema design and database creation for CLTV Prediction System
-- Author: Nisarga N
-- Date: June 2026
-- Dataset: UCI Online Retail II
-- Dialect: SQLite-compatible
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table 1: transactions (Raw Transactional logs)
-- Contains the raw retail data lines from the transactional systems.
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS transactions;

CREATE TABLE transactions (
    Invoice TEXT,            -- Unique 6-digit transaction ID (Starts with 'C' for returns)
    StockCode TEXT,          -- Unique product stock code ID
    Description TEXT,        -- Text description of product
    Quantity INTEGER,        -- Number of items sold in this transaction line
    InvoiceDate DATETIME,    -- Exact timestamp of the transaction
    Price REAL,              -- Unit price of product (in GBP)
    CustomerID TEXT,         -- Unique customer code (can be NULL for guest sales)
    Country TEXT             -- Country name of customer location
);

-- ----------------------------------------------------------------------------
-- Create Indexes to Optimize Query Performance
-- ----------------------------------------------------------------------------
CREATE INDEX idx_transactions_customer ON transactions(CustomerID);
CREATE INDEX idx_transactions_invoice ON transactions(Invoice);
CREATE INDEX idx_transactions_date ON transactions(InvoiceDate);
CREATE INDEX idx_transactions_stock ON transactions(StockCode);

-- ----------------------------------------------------------------------------
-- Example Insertion Syntax for Reference
-- ----------------------------------------------------------------------------
-- INSERT INTO transactions VALUES ('489434', '85123A', 'WHITE HANGING HEART T-LIGHT HOLDER', 6, '2009-12-01 07:45:00', 2.55, '13085', 'United Kingdom');
-- INSERT INTO transactions VALUES ('C489435', '22632', 'HAND WARMER RED POLKA DOT', -1, '2009-12-01 07:46:00', 1.85, '13085', 'United Kingdom');

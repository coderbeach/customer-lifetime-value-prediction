-- ============================================================================
-- Purpose: Creating reusable Views and Indexes for Power BI & analytics dashboards
-- Author: Nisarga N
-- Date: June 2026
-- Dataset: UCI Online Retail II
-- Dialect: SQLite-compatible
-- ============================================================================

-- ----------------------------------------------------------------------------
-- View 1: v_customer_summary
-- Aggregated customer KPIs for CRM integrations
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_customer_summary;

CREATE VIEW v_customer_summary AS
SELECT 
    CustomerID,
    Country,
    MIN(InvoiceDate) AS first_purchase_date,
    MAX(InvoiceDate) AS last_purchase_date,
    COUNT(DISTINCT Invoice) AS total_orders,
    SUM(Quantity) AS total_items_bought,
    SUM(Quantity * Price) AS total_revenue_spend,
    AVG(Quantity * Price) AS avg_item_revenue,
    SUM(Quantity * Price) / COUNT(DISTINCT Invoice) AS avg_order_value
FROM transactions
WHERE CustomerID IS NOT NULL 
  AND Invoice NOT LIKE 'C%'
GROUP BY CustomerID, Country;

-- ----------------------------------------------------------------------------
-- View 2: v_monthly_revenue
-- Consolidated monthly net revenue
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_monthly_revenue;

CREATE VIEW v_monthly_revenue AS
SELECT 
    STRFTIME('%Y', InvoiceDate) AS sales_year,
    STRFTIME('%m', InvoiceDate) AS sales_month,
    STRFTIME('%Y-%m', InvoiceDate) AS year_month,
    SUM(Quantity * Price) AS net_revenue,
    COUNT(DISTINCT Invoice) AS total_orders,
    COUNT(DISTINCT CustomerID) AS active_customers
FROM transactions
WHERE CustomerID IS NOT NULL 
  AND Invoice NOT LIKE 'C%'
GROUP BY year_month;

-- ----------------------------------------------------------------------------
-- View 3: v_rfm_segments
-- Combines RFM logic for direct consumption in Power BI
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_rfm_segments;

CREATE VIEW v_rfm_segments AS
WITH max_date_cte AS (
    SELECT MAX(InvoiceDate) AS max_date FROM transactions
),
raw_rfm AS (
    SELECT 
        t.CustomerID,
        CAST(JULIANDAY((SELECT max_date FROM max_date_cte)) - JULIANDAY(MAX(t.InvoiceDate)) AS INTEGER) AS recency_raw,
        COUNT(DISTINCT t.Invoice) AS frequency_raw,
        SUM(t.Quantity * t.Price) AS monetary_raw
    FROM transactions t
    WHERE t.CustomerID IS NOT NULL 
      AND t.Invoice NOT LIKE 'C%'
    GROUP BY t.CustomerID
),
rfm_scores AS (
    SELECT 
        CustomerID,
        recency_raw,
        frequency_raw,
        monetary_raw,
        NTILE(5) OVER (ORDER BY recency_raw DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency_raw ASC) AS f_score,
        NTILE(5) OVER (ORDER BY monetary_raw ASC) AS m_score
    FROM raw_rfm
)
SELECT 
    CustomerID,
    recency_raw AS Recency,
    frequency_raw AS Frequency,
    monetary_raw AS Monetary,
    r_score,
    f_score,
    m_score,
    (CAST(r_score AS TEXT) || CAST(f_score AS TEXT) || CAST(m_score AS TEXT)) AS rfm_score,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal Customers'
        WHEN r_score >= 3 AND f_score = 2 THEN 'Potential Loyalists'
        WHEN r_score >= 4 AND f_score = 1 THEN 'New Customers'
        WHEN r_score = 2 AND f_score >= 3 THEN 'At Risk'
        WHEN r_score = 1 AND f_score >= 4 THEN 'Cant Lose Them'
        WHEN r_score = 2 AND f_score = 2 THEN 'Need Attention'
        WHEN r_score = 3 AND f_score = 1 THEN 'About to Sleep'
        WHEN r_score = 1 AND f_score <= 3 AND f_score > 1 THEN 'Hibernating'
        ELSE 'Lost'
    END AS Segment
FROM rfm_scores;

-- ----------------------------------------------------------------------------
-- View 4: v_product_summary
-- Product inventory sales velocity and return rates
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_product_summary;

CREATE VIEW v_product_summary AS
WITH product_sales AS (
    SELECT 
        StockCode,
        MIN(Description) AS product_description,
        SUM(CASE WHEN Quantity > 0 THEN Quantity ELSE 0 END) AS units_sold,
        SUM(CASE WHEN Quantity > 0 THEN Quantity * Price ELSE 0 END) AS gross_sales_value,
        SUM(CASE WHEN Quantity < 0 THEN ABS(Quantity) ELSE 0 END) AS units_returned,
        SUM(CASE WHEN Quantity < 0 THEN ABS(Quantity * Price) ELSE 0 END) AS refunds_value,
        COUNT(DISTINCT CustomerID) AS unique_buyers
    FROM transactions
    WHERE Price > 0
    GROUP BY StockCode
)
SELECT 
    StockCode,
    product_description,
    units_sold,
    gross_sales_value,
    units_returned,
    refunds_value,
    (gross_sales_value - refunds_value) AS net_sales_value,
    unique_buyers,
    ROUND(units_returned * 100.0 / (units_sold + 1e-5), 2) AS return_rate_pct
FROM product_sales;

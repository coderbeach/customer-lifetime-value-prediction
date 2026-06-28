-- ============================================================================
-- Purpose: Revenue analytics, trend analysis, and ranking queries
-- Author: Nisarga N
-- Date: June 2026
-- Dataset: UCI Online Retail II
-- Dialect: SQLite-compatible
-- ============================================================================

-- Q1: Total gross and net revenue overall
-- Excludes cancellations (Invoice starts with 'C') and NULL/zero unit prices
SELECT 
    SUM(CASE WHEN Quantity > 0 THEN Quantity * Price ELSE 0 END) AS gross_revenue,
    SUM(CASE WHEN Invoice LIKE 'C%' THEN Quantity * Price ELSE 0 END) AS refund_revenue,
    SUM(Quantity * Price) AS net_revenue
FROM transactions
WHERE CustomerID IS NOT NULL 
  AND Price > 0;

-- Q2: Monthly revenue trend (Net)
-- Useful for forecasting and identifying seasonality
SELECT 
    STRFTIME('%Y-%m', InvoiceDate) AS year_month,
    SUM(Quantity * Price) AS monthly_revenue,
    COUNT(DISTINCT Invoice) AS total_orders,
    COUNT(DISTINCT CustomerID) AS unique_active_customers
FROM transactions
WHERE CustomerID IS NOT NULL 
  AND Invoice NOT LIKE 'C%'
GROUP BY year_month
ORDER BY year_month ASC;

-- Q3: Weekly revenue trend
SELECT 
    STRFTIME('%Y-%W', InvoiceDate) AS year_week,
    SUM(Quantity * Price) AS weekly_revenue,
    COUNT(DISTINCT Invoice) AS total_orders
FROM transactions
WHERE CustomerID IS NOT NULL 
  AND Invoice NOT LIKE 'C%'
GROUP BY year_week
ORDER BY year_week ASC;

-- Q4: Top 10 revenue months ranked with RANK() window function
WITH monthly_sales AS (
    SELECT 
        STRFTIME('%Y-%m', InvoiceDate) AS year_month,
        SUM(Quantity * Price) AS monthly_revenue
    FROM transactions
    WHERE CustomerID IS NOT NULL 
      AND Invoice NOT LIKE 'C%'
    GROUP BY year_month
)
SELECT 
    year_month,
    monthly_revenue,
    RANK() OVER (ORDER BY monthly_revenue DESC) as revenue_rank
FROM monthly_sales
LIMIT 10;

-- Q5: Revenue by year comparison
SELECT 
    STRFTIME('%Y', InvoiceDate) AS sales_year,
    SUM(Quantity * Price) AS annual_revenue,
    COUNT(DISTINCT CustomerID) AS annual_unique_customers
FROM transactions
WHERE CustomerID IS NOT NULL 
  AND Invoice NOT LIKE 'C%'
GROUP BY sales_year;

-- Q6: Average daily revenue
SELECT 
    AVG(daily_revenue) AS avg_daily_revenue
FROM (
    SELECT 
        STRFTIME('%Y-%m-%d', InvoiceDate) AS order_date,
        SUM(Quantity * Price) AS daily_revenue
    FROM transactions
    WHERE CustomerID IS NOT NULL 
      AND Invoice NOT LIKE 'C%'
    GROUP BY order_date
);

-- Q7: Revenue percentile distribution using NTILE(4)
-- Groups months into revenue quartiles
WITH monthly_sales AS (
    SELECT 
        STRFTIME('%Y-%m', InvoiceDate) AS year_month,
        SUM(Quantity * Price) AS monthly_revenue
    FROM transactions
    WHERE CustomerID IS NOT NULL 
      AND Invoice NOT LIKE 'C%'
    GROUP BY year_month
)
SELECT 
    year_month,
    monthly_revenue,
    NTILE(4) OVER (ORDER BY monthly_revenue ASC) as revenue_quartile
FROM monthly_sales;

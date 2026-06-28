-- ============================================================================
-- Purpose: Advanced analysis, window metrics, cohort retention, basket analysis
-- Author: Nisarga N
-- Date: June 2026
-- Dataset: UCI Online Retail II
-- Dialect: SQLite-compatible
-- ============================================================================

-- Q1: Rolling 3-month revenue using window functions
-- SQLite does not support calendar-month ranges directly, so we aggregate by month and window over it.
WITH monthly_revenue AS (
    SELECT 
        STRFTIME('%Y-%m', InvoiceDate) AS year_month,
        SUM(Quantity * Price) AS revenue
    FROM transactions
    WHERE CustomerID IS NOT NULL 
      AND Invoice NOT LIKE 'C%'
    GROUP BY year_month
)
SELECT 
    year_month,
    revenue,
    AVG(revenue) OVER (
        ORDER BY year_month 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS rolling_3month_avg_revenue,
    SUM(revenue) OVER (
        ORDER BY year_month 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS rolling_3month_total_revenue
FROM monthly_revenue;

-- Q2: Month-over-month revenue growth rate
WITH monthly_revenue AS (
    SELECT 
        STRFTIME('%Y-%m', InvoiceDate) AS year_month,
        SUM(Quantity * Price) AS revenue
    FROM transactions
    WHERE CustomerID IS NOT NULL 
      AND Invoice NOT LIKE 'C%'
    GROUP BY year_month
),
mom_revenue AS (
    SELECT 
        year_month,
        revenue,
        LAG(revenue, 1) OVER (ORDER BY year_month) AS prev_month_revenue
    FROM monthly_revenue
)
SELECT 
    year_month,
    revenue,
    prev_month_revenue,
    ROUND((revenue - prev_month_revenue) * 100.0 / prev_month_revenue, 2) AS mom_growth_percentage
FROM mom_revenue;

-- Q3: Average days between purchases per customer (purchase gap analysis)
WITH invoice_dates AS (
    SELECT DISTINCT
        CustomerID,
        Invoice,
        InvoiceDate
    FROM transactions
    WHERE CustomerID IS NOT NULL 
      AND Invoice NOT LIKE 'C%'
),
purchase_lead AS (
    SELECT 
        CustomerID,
        InvoiceDate,
        LAG(InvoiceDate, 1) OVER (PARTITION BY CustomerID ORDER BY InvoiceDate) AS prev_invoice_date
    FROM invoice_dates
)
SELECT 
    CustomerID,
    COUNT(prev_invoice_date) AS repeat_purchase_count,
    ROUND(AVG(JULIANDAY(InvoiceDate) - JULIANDAY(prev_invoice_date)), 1) AS avg_days_between_purchases
FROM purchase_lead
WHERE prev_invoice_date IS NOT NULL
GROUP BY CustomerID
ORDER BY avg_days_between_purchases ASC
LIMIT 15;

-- Q4: Revenue per country with running cumulative total
WITH country_revenue AS (
    SELECT 
        Country,
        SUM(Quantity * Price) AS total_revenue
    FROM transactions
    WHERE CustomerID IS NOT NULL 
      AND Invoice NOT LIKE 'C%'
    GROUP BY Country
)
SELECT 
    Country,
    total_revenue,
    SUM(total_revenue) OVER (ORDER BY total_revenue DESC) AS cumulative_running_revenue,
    ROUND(total_revenue * 100.0 / (SELECT SUM(Quantity*Price) FROM transactions WHERE CustomerID IS NOT NULL AND Invoice NOT LIKE 'C%'), 2) as revenue_share_pct
FROM country_revenue
ORDER BY total_revenue DESC;

-- Q5: Top product per customer (StockCode with highest quantity purchased)
WITH customer_product_qty AS (
    SELECT 
        CustomerID,
        StockCode,
        MIN(Description) AS product_name,
        SUM(Quantity) AS total_quantity,
        ROW_NUMBER() OVER (PARTITION BY CustomerID ORDER BY SUM(Quantity) DESC) AS rank
    FROM transactions
    WHERE CustomerID IS NOT NULL 
      AND Invoice NOT LIKE 'C%'
    GROUP BY CustomerID, StockCode
)
SELECT 
    CustomerID,
    StockCode,
    product_name,
    total_quantity
FROM customer_product_qty
WHERE rank = 1
ORDER BY total_quantity DESC
LIMIT 15;

-- Q6: Basket size distribution (items per invoice)
WITH basket_sizes AS (
    SELECT 
        Invoice,
        SUM(Quantity) AS total_items,
        SUM(Quantity * Price) AS basket_revenue
    FROM transactions
    WHERE Invoice NOT LIKE 'C%'
    GROUP BY Invoice
)
SELECT 
    CASE 
        WHEN total_items <= 5 THEN '1. Tiny (1-5 items)'
        WHEN total_items <= 15 THEN '2. Small (6-15 items)'
        WHEN total_items <= 50 THEN '3. Medium (16-50 items)'
        WHEN total_items <= 150 THEN '4. Large (51-150 items)'
        ELSE '5. Bulk (>150 items)'
    END AS basket_size_category,
    COUNT(Invoice) AS invoice_count,
    ROUND(AVG(basket_revenue), 2) AS avg_basket_value
FROM basket_sizes
GROUP BY basket_size_category
ORDER BY basket_size_category;

-- Q7: Cross-sell recommendation query
-- Find customers who bought 'WHITE HANGING HEART T-LIGHT HOLDER' (StockCode: 85123A)
-- but did not buy 'RED WOOLLY HOTTIE WHITE HEART' (StockCode: 84029E)
-- These are strong prospects for targeting.
SELECT DISTINCT CustomerID 
FROM transactions 
WHERE StockCode = '85123A' 
  AND CustomerID IS NOT NULL
  AND CustomerID NOT IN (
      SELECT DISTINCT CustomerID 
      FROM transactions 
      WHERE StockCode = '84029E'
  )
LIMIT 15;

-- Q8: Seasonal Analysis — revenue by quarter
SELECT 
    STRFTIME('%Y', InvoiceDate) AS sales_year,
    CASE 
        WHEN STRFTIME('%m', InvoiceDate) IN ('01', '02', '03') THEN 'Q1'
        WHEN STRFTIME('%m', InvoiceDate) IN ('04', '05', '06') THEN 'Q2'
        WHEN STRFTIME('%m', InvoiceDate) IN ('07', '08', '09') THEN 'Q3'
        ELSE 'Q4'
    END AS quarter,
    SUM(Quantity * Price) AS quarterly_revenue,
    COUNT(DISTINCT Invoice) AS order_count
FROM transactions
WHERE CustomerID IS NOT NULL 
  AND Invoice NOT LIKE 'C%'
GROUP BY sales_year, quarter
ORDER BY sales_year ASC, quarter ASC;

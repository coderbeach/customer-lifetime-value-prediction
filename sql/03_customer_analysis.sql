-- ============================================================================
-- Purpose: Customer engagement, frequency, retention, and concentration metrics
-- Author: Nisarga N
-- Date: June 2026
-- Dataset: UCI Online Retail II
-- Dialect: SQLite-compatible
-- ============================================================================

-- Q1: Total unique customers
SELECT COUNT(DISTINCT CustomerID) AS total_unique_customers
FROM transactions
WHERE CustomerID IS NOT NULL;

-- Q2: Top 20 customers by total spend with RANK()
SELECT 
    CustomerID,
    Country,
    SUM(Quantity * Price) AS total_spend,
    COUNT(DISTINCT Invoice) AS total_orders,
    RANK() OVER (ORDER BY SUM(Quantity * Price) DESC) as customer_spend_rank
FROM transactions
WHERE CustomerID IS NOT NULL 
  AND Invoice NOT LIKE 'C%'
GROUP BY CustomerID
LIMIT 20;

-- Q3: Customer purchase frequency distribution
-- Group customers by how many times they purchased
WITH customer_orders AS (
    SELECT 
        CustomerID,
        COUNT(DISTINCT Invoice) AS order_count
    FROM transactions
    WHERE CustomerID IS NOT NULL 
      AND Invoice NOT LIKE 'C%'
    GROUP BY CustomerID
)
SELECT 
    order_count,
    COUNT(CustomerID) AS customer_count,
    ROUND(COUNT(CustomerID) * 100.0 / (SELECT COUNT(DISTINCT CustomerID) FROM transactions WHERE CustomerID IS NOT NULL), 2) AS customer_percentage
FROM customer_orders
GROUP BY order_count
ORDER BY order_count ASC
LIMIT 15;

-- Q4: Average order value per customer
SELECT 
    CustomerID,
    SUM(Quantity * Price) / COUNT(DISTINCT Invoice) AS avg_order_value,
    COUNT(DISTINCT Invoice) AS order_count
FROM transactions
WHERE CustomerID IS NOT NULL 
  AND Invoice NOT LIKE 'C%'
GROUP BY CustomerID
ORDER BY avg_order_value DESC
LIMIT 10;

-- Q5: Repeat purchase rate (customers with >1 invoice / total customers)
WITH customer_order_counts AS (
    SELECT 
        CustomerID,
        COUNT(DISTINCT Invoice) AS order_count
    FROM transactions
    WHERE CustomerID IS NOT NULL 
      AND Invoice NOT LIKE 'C%'
    GROUP BY CustomerID
)
SELECT 
    SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) AS repeat_customers,
    COUNT(CustomerID) AS total_customers,
    ROUND(SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(CustomerID), 2) AS repeat_purchase_rate_pct
FROM customer_order_counts;

-- Q6: Customer cohort analysis — first purchase month, subsequent purchases
WITH cohort_base AS (
    SELECT 
        CustomerID,
        MIN(STRFTIME('%Y-%m', InvoiceDate)) AS cohort_month
    FROM transactions
    WHERE CustomerID IS NOT NULL 
      AND Invoice NOT LIKE 'C%'
    GROUP BY CustomerID
),
activity_base AS (
    SELECT 
        t.CustomerID,
        STRFTIME('%Y-%m', t.InvoiceDate) AS activity_month,
        cb.cohort_month
    FROM transactions t
    JOIN cohort_base cb ON t.CustomerID = cb.CustomerID
    WHERE t.Invoice NOT LIKE 'C%'
)
SELECT 
    cohort_month,
    activity_month,
    COUNT(DISTINCT CustomerID) AS active_customers
FROM activity_base
GROUP BY cohort_month, activity_month
ORDER BY cohort_month, activity_month;

-- Q7: Customer lifetime in days (last_purchase - first_purchase)
SELECT 
    CustomerID,
    MIN(InvoiceDate) AS first_purchase,
    MAX(InvoiceDate) AS last_purchase,
    CAST(JULIANDAY(MAX(InvoiceDate)) - JULIANDAY(MIN(InvoiceDate)) AS INTEGER) AS customer_lifetime_days
FROM transactions
WHERE CustomerID IS NOT NULL 
  AND Invoice NOT LIKE 'C%'
GROUP BY CustomerID
ORDER BY customer_lifetime_days DESC
LIMIT 10;

-- Q8: Active vs inactive customers (active = purchased in last 90 days of dataset)
WITH dataset_max AS (
    SELECT MAX(InvoiceDate) AS max_date FROM transactions
),
customer_recency AS (
    SELECT 
        t.CustomerID,
        CAST(JULIANDAY((SELECT max_date FROM dataset_max)) - JULIANDAY(MAX(t.InvoiceDate)) AS INTEGER) AS days_since_last
    FROM transactions t
    WHERE t.CustomerID IS NOT NULL 
      AND t.Invoice NOT LIKE 'C%'
    GROUP BY t.CustomerID
)
SELECT 
    CASE WHEN days_since_last <= 90 THEN 'Active (<= 90 days)' ELSE 'Inactive (> 90 days)' END AS customer_status,
    COUNT(CustomerID) AS customer_count,
    ROUND(COUNT(CustomerID) * 100.0 / (SELECT COUNT(DISTINCT CustomerID) FROM transactions WHERE CustomerID IS NOT NULL), 2) AS pct
FROM customer_recency
GROUP BY customer_status;

-- Q9: Revenue concentration (Pareto principle - top 20% of customers contributing what % of revenue)
WITH customer_revenue AS (
    SELECT 
        CustomerID,
        SUM(Quantity * Price) AS total_spend,
        ROW_NUMBER() OVER (ORDER BY SUM(Quantity * Price) DESC) AS customer_rank,
        (SELECT COUNT(DISTINCT CustomerID) FROM transactions WHERE CustomerID IS NOT NULL) AS total_customers,
        (SELECT SUM(Quantity * Price) FROM transactions WHERE CustomerID IS NOT NULL AND Invoice NOT LIKE 'C%') AS grand_total_revenue
    FROM transactions
    WHERE CustomerID IS NOT NULL 
      AND Invoice NOT LIKE 'C%'
    GROUP BY CustomerID
)
SELECT 
    CASE WHEN customer_rank <= (total_customers * 0.20) THEN 'Top 20%' ELSE 'Bottom 80%' END AS customer_tier,
    COUNT(CustomerID) AS customer_count,
    SUM(total_spend) AS total_tier_spend,
    ROUND(SUM(total_spend) * 100.0 / MIN(grand_total_revenue), 2) AS contribution_percentage
FROM customer_revenue
GROUP BY customer_tier;

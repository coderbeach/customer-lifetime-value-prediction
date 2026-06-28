-- ============================================================================
-- Purpose: Product diagnostics, top products, return rates, geographic sales
-- Author: Nisarga N
-- Date: June 2026
-- Dataset: UCI Online Retail II
-- Dialect: SQLite-compatible
-- ============================================================================

-- Q1: Top 20 products by revenue (excluding returns)
SELECT 
    StockCode,
    Description,
    SUM(Quantity * Price) AS total_revenue,
    SUM(Quantity) AS units_sold,
    COUNT(DISTINCT Invoice) AS order_count
FROM transactions
WHERE Invoice NOT LIKE 'C%' 
  AND Price > 0
GROUP BY StockCode
ORDER BY total_revenue DESC
LIMIT 20;

-- Q2: Top 20 products by quantity sold
SELECT 
    StockCode,
    Description,
    SUM(Quantity) AS units_sold,
    SUM(Quantity * Price) AS total_revenue
FROM transactions
WHERE Invoice NOT LIKE 'C%' 
  AND Price > 0
GROUP BY StockCode
ORDER BY units_sold DESC
LIMIT 20;

-- Q3: Products with most returns (Invoice LIKE 'C%')
SELECT 
    StockCode,
    Description,
    ABS(SUM(Quantity)) AS returned_units,
    ABS(SUM(Quantity * Price)) AS refunded_amount,
    COUNT(DISTINCT Invoice) AS return_count
FROM transactions
WHERE Invoice LIKE 'C%'
GROUP BY StockCode
ORDER BY returned_units DESC
LIMIT 20;

-- Q4: Average price per product across invoices
SELECT 
    StockCode,
    Description,
    AVG(Price) AS avg_price,
    MIN(Price) AS min_price,
    MAX(Price) AS max_price
FROM transactions
WHERE Price > 0
GROUP BY StockCode
ORDER BY avg_price DESC
LIMIT 10;

-- Q5: Product diversity per customer (unique StockCodes per CustomerID)
SELECT 
    CustomerID,
    COUNT(DISTINCT StockCode) AS unique_products_bought,
    SUM(Quantity) AS total_units_bought
FROM transactions
WHERE CustomerID IS NOT NULL
GROUP BY CustomerID
ORDER BY unique_products_bought DESC
LIMIT 15;

-- Q6: Products only bought once (unique buyers)
SELECT 
    StockCode,
    MIN(Description) AS product_name,
    COUNT(DISTINCT CustomerID) AS unique_buyer_count
FROM transactions
WHERE CustomerID IS NOT NULL
GROUP BY StockCode
HAVING unique_buyer_count = 1
LIMIT 10;

-- Q7: Best-selling products per country using window functions
WITH country_product_sales AS (
    SELECT 
        Country,
        StockCode,
        Description,
        SUM(Quantity) AS total_quantity,
        ROW_NUMBER() OVER (PARTITION BY Country ORDER BY SUM(Quantity) DESC) as ranking
    FROM transactions
    WHERE Invoice NOT LIKE 'C%'
      AND Country != 'United Kingdom'  -- Filter out domestic UK sales to see export items
    GROUP BY Country, StockCode
)
SELECT 
    Country,
    StockCode,
    Description,
    total_quantity
FROM country_product_sales
WHERE ranking = 1
ORDER BY total_quantity DESC
LIMIT 15;

-- Q8: Products with highest return rate
WITH product_totals AS (
    SELECT 
        StockCode,
        MIN(Description) AS product_name,
        SUM(CASE WHEN Quantity > 0 THEN Quantity ELSE 0 END) AS sold_qty,
        SUM(CASE WHEN Quantity < 0 THEN ABS(Quantity) ELSE 0 END) AS returned_qty
    FROM transactions
    GROUP BY StockCode
)
SELECT 
    StockCode,
    product_name,
    sold_qty,
    returned_qty,
    ROUND(returned_qty * 100.0 / (sold_qty + 1e-5), 2) AS return_rate_pct
FROM product_totals
WHERE sold_qty > 100 -- Limit to popular items to avoid small sample noise
ORDER BY return_rate_pct DESC
LIMIT 10;

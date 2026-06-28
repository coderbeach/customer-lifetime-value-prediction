-- ============================================================================
-- Purpose: Quintile-based RFM scoring and segment assignment queries
-- Author: Nisarga N
-- Date: June 2026
-- Dataset: UCI Online Retail II
-- Dialect: SQLite-compatible
-- ============================================================================

-- Complete RFM Pipeline in SQL
-- Uses NTILE() window function to segment customers dynamically
WITH max_date_cte AS (
    SELECT MAX(InvoiceDate) AS max_date FROM transactions
),
raw_rfm AS (
    -- Step 1: Calculate raw RFM metric values
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
    -- Step 2: Bin values into quintiles (1 to 5)
    -- For Recency: lower days is better, so we rank ascending and bin
    -- SQLite's NTILE(5) distributes observations evenly
    SELECT 
        CustomerID,
        recency_raw,
        frequency_raw,
        monetary_raw,
        NTILE(5) OVER (ORDER BY recency_raw DESC) AS r_score, -- Inverted: lower recency value gets higher score
        NTILE(5) OVER (ORDER BY frequency_raw ASC) AS f_score,
        NTILE(5) OVER (ORDER BY monetary_raw ASC) AS m_score
    FROM raw_rfm
),
rfm_segments AS (
    -- Step 3: Combine scores and assign marketing segment names
    SELECT 
        CustomerID,
        recency_raw,
        frequency_raw,
        monetary_raw,
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
            ELSE 'Lost' -- R=1, F=1
        END AS segment
    FROM rfm_scores
)
-- Step 4: Display segment summary with customer count, average metrics, and revenue share
SELECT 
    segment,
    COUNT(CustomerID) AS customer_count,
    ROUND(AVG(recency_raw), 1) AS avg_recency_days,
    ROUND(AVG(frequency_raw), 1) AS avg_frequency_orders,
    ROUND(AVG(monetary_raw), 2) AS avg_monetary_spend,
    ROUND(SUM(monetary_raw), 2) AS total_segment_revenue,
    ROUND(COUNT(CustomerID) * 100.0 / (SELECT COUNT(*) FROM rfm_segments), 2) AS customer_percentage,
    ROUND(SUM(monetary_raw) * 100.0 / (SELECT SUM(monetary_raw) FROM rfm_segments), 2) AS revenue_percentage
FROM rfm_segments
GROUP BY segment
ORDER BY total_segment_revenue DESC;

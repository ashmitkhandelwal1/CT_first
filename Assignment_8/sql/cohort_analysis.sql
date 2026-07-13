-- =============================================================
-- cohort_analysis.sql
-- Steps 6 & 7: Cohort/Retention Analysis + Customer Segmentation
-- Author : Ashmit Gupta
-- Project: Assignment 8 — End-to-End Data Analytics
-- =============================================================
-- Covers:
--   6.1  Define cohorts by first-purchase month
--   6.2  Cohort size per month
--   6.3  Monthly active customers per cohort
--   6.4  Retention rate matrix
--   6.5  Churned vs repeat customers
--   6.6  Month-1 retention rate summary
--   7.1  Frequency segmentation (one-time / occasional / loyal)
--   7.2  Spend tier segmentation (low / medium / high)
--   7.3  Combined RFM-style analysis
--   7.4  RFM scoring and segment labeling
--   7.5  Segment summary dashboard
-- =============================================================

-- ─────────────────────────────────────────────
-- 6.1  Cohort Definition — First Purchase Month
-- ─────────────────────────────────────────────
-- Each customer is assigned to the month of their FIRST order.
WITH first_orders AS (
    SELECT
        customer_id,
        MIN(order_date)                                          AS first_order_date,
        STRFTIME('%Y-%m', MIN(order_date))                       AS cohort_month
    FROM   orders
    WHERE  status NOT IN ('cancelled', 'returned')
      AND  order_date IS NOT NULL
    GROUP  BY customer_id
)
SELECT
    cohort_month,
    COUNT(customer_id)                                           AS cohort_size
FROM   first_orders
GROUP  BY cohort_month
ORDER  BY cohort_month;


-- ─────────────────────────────────────────────
-- 6.2  Full Cohort-Activity Grid
--      (cohort_month × activity_month)
-- ─────────────────────────────────────────────
WITH first_orders AS (
    SELECT
        customer_id,
        STRFTIME('%Y-%m', MIN(order_date))                       AS cohort_month
    FROM   orders
    WHERE  status NOT IN ('cancelled', 'returned')
    GROUP  BY customer_id
),
cohort_activity AS (
    SELECT
        f.cohort_month,
        STRFTIME('%Y-%m', o.order_date)                          AS activity_month,
        COUNT(DISTINCT o.customer_id)                            AS active_customers
    FROM   orders       o
    JOIN   first_orders f ON o.customer_id = f.customer_id
    WHERE  o.status NOT IN ('cancelled', 'returned')
    GROUP  BY f.cohort_month, activity_month
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(*) AS cohort_size
    FROM   first_orders
    GROUP  BY cohort_month
)
SELECT
    ca.cohort_month                                              AS cohort_month,
    ca.activity_month                                            AS activity_month,
    cs.cohort_size,
    ca.active_customers,
    ROUND(ca.active_customers * 100.0 / cs.cohort_size, 2)      AS retention_pct
FROM   cohort_activity ca
JOIN   cohort_sizes    cs ON ca.cohort_month = cs.cohort_month
ORDER  BY ca.cohort_month, ca.activity_month;


-- ─────────────────────────────────────────────
-- 6.3  Period Offset Retention
--      Month 0 = acquisition, Month N = N months later
-- ─────────────────────────────────────────────
WITH first_orders AS (
    SELECT
        customer_id,
        STRFTIME('%Y-%m', MIN(order_date))                       AS cohort_month,
        MIN(order_date)                                          AS first_date
    FROM   orders
    WHERE  status NOT IN ('cancelled', 'returned')
    GROUP  BY customer_id
),
activity AS (
    SELECT
        f.cohort_month,
        o.customer_id,
        -- Approximate months since acquisition
        CAST(
            (JULIANDAY(o.order_date) - JULIANDAY(f.first_date)) / 30
        AS INTEGER)                                              AS month_offset
    FROM   orders       o
    JOIN   first_orders f ON o.customer_id = f.customer_id
    WHERE  o.status NOT IN ('cancelled', 'returned')
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(*) AS cohort_size
    FROM   first_orders
    GROUP  BY cohort_month
)
SELECT
    a.cohort_month,
    a.month_offset,
    cs.cohort_size,
    COUNT(DISTINCT a.customer_id)                                AS active,
    ROUND(COUNT(DISTINCT a.customer_id) * 100.0 / cs.cohort_size, 2) AS retention_pct
FROM   activity     a
JOIN   cohort_sizes cs ON a.cohort_month = cs.cohort_month
WHERE  a.month_offset <= 12
GROUP  BY a.cohort_month, a.month_offset
ORDER  BY a.cohort_month, a.month_offset;


-- ─────────────────────────────────────────────
-- 6.4  Churned vs. Repeat Customers
--      Churn = placed only ONE order; Repeat = >1 order
-- ─────────────────────────────────────────────
WITH customer_orders AS (
    SELECT
        customer_id,
        COUNT(DISTINCT order_id) AS order_count
    FROM   orders
    WHERE  status NOT IN ('cancelled', 'returned')
    GROUP  BY customer_id
)
SELECT
    CASE
        WHEN order_count = 1 THEN 'Churned (one-time)'
        ELSE                      'Repeat Buyer'
    END                                                          AS customer_type,
    COUNT(*)                                                     AS num_customers,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2)          AS pct_of_total
FROM   customer_orders
GROUP  BY customer_type
ORDER  BY num_customers DESC;


-- ─────────────────────────────────────────────
-- 6.5  Month-1 Retention Rate per Cohort
--      (% of cohort who returned in month 1)
-- ─────────────────────────────────────────────
WITH first_orders AS (
    SELECT
        customer_id,
        STRFTIME('%Y-%m', MIN(order_date))                       AS cohort_month
    FROM   orders
    WHERE  status NOT IN ('cancelled', 'returned')
    GROUP  BY customer_id
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(*) AS cohort_size
    FROM   first_orders
    GROUP  BY cohort_month
),
month1_actives AS (
    SELECT
        f.cohort_month,
        COUNT(DISTINCT o.customer_id)                            AS month1_customers
    FROM   orders       o
    JOIN   first_orders f ON o.customer_id = f.customer_id
    WHERE  o.status NOT IN ('cancelled', 'returned')
      -- exactly 1 month later (within ±15 days)
      AND  ABS(JULIANDAY(o.order_date) -
               JULIANDAY(f.cohort_month || '-01') - 30) <= 15
      AND  STRFTIME('%Y-%m', o.order_date) <> f.cohort_month
    GROUP  BY f.cohort_month
)
SELECT
    cs.cohort_month,
    cs.cohort_size,
    COALESCE(m1.month1_customers, 0)                             AS month1_active,
    ROUND(
        COALESCE(m1.month1_customers, 0) * 100.0 / cs.cohort_size,
        2
    )                                                            AS month1_retention_pct
FROM   cohort_sizes cs
LEFT   JOIN month1_actives m1 ON cs.cohort_month = m1.cohort_month
ORDER  BY cs.cohort_month;


-- ─────────────────────────────────────────────
-- 7.1  Frequency Segmentation
-- ─────────────────────────────────────────────
WITH freq AS (
    SELECT
        customer_id,
        COUNT(DISTINCT order_id)                                 AS order_count
    FROM   orders
    WHERE  status NOT IN ('cancelled', 'returned')
    GROUP  BY customer_id
)
SELECT
    CASE
        WHEN order_count = 1           THEN 'One-Time'
        WHEN order_count BETWEEN 2 AND 4 THEN 'Occasional'
        ELSE                               'Loyal'
    END                                                          AS freq_segment,
    COUNT(*)                                                     AS num_customers,
    ROUND(AVG(order_count), 2)                                   AS avg_orders,
    MIN(order_count)                                             AS min_orders,
    MAX(order_count)                                             AS max_orders
FROM   freq
GROUP  BY freq_segment
ORDER  BY num_customers DESC;


-- ─────────────────────────────────────────────
-- 7.2  Spend Tier Segmentation
-- ─────────────────────────────────────────────
WITH spend AS (
    SELECT
        o.customer_id,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount))    AS total_spend
    FROM   orders      o
    JOIN   order_items oi ON o.order_id = oi.order_id
    WHERE  o.status NOT IN ('cancelled', 'returned')
    GROUP  BY o.customer_id
)
SELECT
    CASE
        WHEN total_spend < 500    THEN 'Low Spender    (<$500)'
        WHEN total_spend < 2000   THEN 'Medium Spender ($500–$2000)'
        ELSE                          'High Spender   (>$2000)'
    END                                                          AS spend_tier,
    COUNT(*)                                                     AS num_customers,
    ROUND(AVG(total_spend), 2)                                   AS avg_spend,
    ROUND(SUM(total_spend), 2)                                   AS total_revenue
FROM   spend
GROUP  BY spend_tier
ORDER  BY avg_spend DESC;


-- ─────────────────────────────────────────────
-- 7.3  Combined Frequency × Spend Matrix
-- ─────────────────────────────────────────────
WITH metrics AS (
    SELECT
        o.customer_id,
        COUNT(DISTINCT o.order_id)                               AS freq,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount))    AS monetary
    FROM   orders      o
    JOIN   order_items oi ON o.order_id = oi.order_id
    WHERE  o.status NOT IN ('cancelled', 'returned')
    GROUP  BY o.customer_id
),
segmented AS (
    SELECT
        customer_id,
        CASE
            WHEN freq = 1           THEN 'One-Time'
            WHEN freq BETWEEN 2 AND 4 THEN 'Occasional'
            ELSE                        'Loyal'
        END AS freq_seg,
        CASE
            WHEN monetary < 500   THEN 'Low'
            WHEN monetary < 2000  THEN 'Medium'
            ELSE                      'High'
        END AS spend_tier
    FROM metrics
)
SELECT
    freq_seg,
    spend_tier,
    COUNT(*)                                                     AS num_customers
FROM   segmented
GROUP  BY freq_seg, spend_tier
ORDER  BY freq_seg, spend_tier;


-- ─────────────────────────────────────────────
-- 7.4  Full RFM Scoring
--      R = Recency (lower days = better, score 1-5)
--      F = Frequency (more orders = better, score 1-5)
--      M = Monetary  (higher spend = better, score 1-5)
-- ─────────────────────────────────────────────
WITH rfm_raw AS (
    SELECT
        c.customer_id,
        c.name,
        ROUND(JULIANDAY('now') - JULIANDAY(MAX(o.order_date)), 0) AS recency_days,
        COUNT(DISTINCT o.order_id)                                AS frequency,
        ROUND(
            SUM(oi.quantity * oi.unit_price * (1 - oi.discount)),
            2
        )                                                         AS monetary
    FROM   customers   c
    JOIN   orders      o  ON c.customer_id = o.customer_id
    JOIN   order_items oi ON o.order_id    = oi.order_id
    WHERE  o.status NOT IN ('cancelled', 'returned')
    GROUP  BY c.customer_id, c.name
),
rfm_scored AS (
    SELECT
        customer_id,
        name,
        recency_days,
        frequency,
        monetary,
        -- R score (5 = most recent)
        CASE
            WHEN recency_days <= 30  THEN 5
            WHEN recency_days <= 90  THEN 4
            WHEN recency_days <= 180 THEN 3
            WHEN recency_days <= 365 THEN 2
            ELSE 1
        END AS r_score,
        -- F score (5 = highest frequency)
        CASE
            WHEN frequency >= 10 THEN 5
            WHEN frequency >= 6  THEN 4
            WHEN frequency >= 3  THEN 3
            WHEN frequency >= 2  THEN 2
            ELSE 1
        END AS f_score,
        -- M score (5 = highest spend)
        CASE
            WHEN monetary >= 5000 THEN 5
            WHEN monetary >= 2000 THEN 4
            WHEN monetary >= 1000 THEN 3
            WHEN monetary >= 500  THEN 2
            ELSE 1
        END AS m_score
    FROM rfm_raw
)
SELECT
    customer_id,
    name,
    recency_days,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    (r_score + f_score + m_score)                                AS rfm_total,
    CASE
        WHEN (r_score + f_score + m_score) >= 13 THEN 'Champions'
        WHEN (r_score + f_score + m_score) >= 10 THEN 'Loyal Customers'
        WHEN (r_score + f_score + m_score) >= 7  THEN 'At Risk'
        WHEN (r_score + f_score + m_score) >= 4  THEN 'Dormant'
        ELSE                                          'Lost'
    END                                                          AS rfm_segment
FROM   rfm_scored
ORDER  BY rfm_total DESC;


-- ─────────────────────────────────────────────
-- 7.5  RFM Segment Summary Dashboard
-- ─────────────────────────────────────────────
WITH rfm_raw AS (
    SELECT
        c.customer_id,
        ROUND(JULIANDAY('now') - JULIANDAY(MAX(o.order_date)), 0) AS recency_days,
        COUNT(DISTINCT o.order_id)                                AS frequency,
        ROUND(
            SUM(oi.quantity * oi.unit_price * (1 - oi.discount)),
            2
        )                                                         AS monetary
    FROM   customers   c
    JOIN   orders      o  ON c.customer_id = o.customer_id
    JOIN   order_items oi ON o.order_id    = oi.order_id
    WHERE  o.status NOT IN ('cancelled', 'returned')
    GROUP  BY c.customer_id
),
rfm_scored AS (
    SELECT *,
        CASE
            WHEN recency_days <= 30  THEN 5
            WHEN recency_days <= 90  THEN 4
            WHEN recency_days <= 180 THEN 3
            WHEN recency_days <= 365 THEN 2
            ELSE 1
        END +
        CASE
            WHEN frequency >= 10 THEN 5
            WHEN frequency >= 6  THEN 4
            WHEN frequency >= 3  THEN 3
            WHEN frequency >= 2  THEN 2
            ELSE 1
        END +
        CASE
            WHEN monetary >= 5000 THEN 5
            WHEN monetary >= 2000 THEN 4
            WHEN monetary >= 1000 THEN 3
            WHEN monetary >= 500  THEN 2
            ELSE 1
        END AS rfm_total
    FROM rfm_raw
)
SELECT
    CASE
        WHEN rfm_total >= 13 THEN 'Champions'
        WHEN rfm_total >= 10 THEN 'Loyal Customers'
        WHEN rfm_total >= 7  THEN 'At Risk'
        WHEN rfm_total >= 4  THEN 'Dormant'
        ELSE                     'Lost'
    END                                                          AS rfm_segment,
    COUNT(*)                                                     AS num_customers,
    ROUND(AVG(recency_days), 1)                                  AS avg_recency_days,
    ROUND(AVG(frequency),    1)                                  AS avg_frequency,
    ROUND(AVG(monetary),     2)                                  AS avg_monetary,
    ROUND(SUM(monetary),     2)                                  AS segment_revenue
FROM   rfm_scored
GROUP  BY rfm_segment
ORDER  BY avg_monetary DESC;

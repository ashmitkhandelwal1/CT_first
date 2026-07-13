-- =============================================================
-- window_functions.sql
-- Step 5: SQL Analytics — Window Functions & CTEs
-- Author : Ashmit Gupta
-- Project: Assignment 8 — End-to-End Data Analytics
-- =============================================================
-- Covers:
--   5.1  Rank customers by lifetime value (RANK / DENSE_RANK)
--   5.2  Running total revenue over time (SUM OVER)
--   5.3  3-month moving average of revenue (AVG OVER)
--   5.4  Customer order sequence (ROW_NUMBER OVER)
--   5.5  Revenue percentile buckets (NTILE)
--   5.6  Monthly revenue growth rate (LAG CTE)
--   5.7  Cumulative revenue share per category (SUM OVER partition)
--   5.8  First and last order per customer (FIRST_VALUE / LAST_VALUE)
-- =============================================================

-- ─────────────────────────────────────────────
-- 5.1  Customer LTV Ranking
--      RANK() + DENSE_RANK() side by side
-- ─────────────────────────────────────────────
WITH customer_ltv AS (
    SELECT
        c.customer_id,
        c.name                                                  AS customer_name,
        c.city,
        COUNT(DISTINCT o.order_id)                              AS total_orders,
        ROUND(
            SUM(oi.quantity * oi.unit_price * (1 - oi.discount)),
            2
        )                                                       AS lifetime_value
    FROM   customers   c
    JOIN   orders      o  ON c.customer_id = o.customer_id
    JOIN   order_items oi ON o.order_id    = oi.order_id
    WHERE  o.status NOT IN ('cancelled', 'returned')
    GROUP  BY c.customer_id, c.name, c.city
)
SELECT
    customer_id,
    customer_name,
    city,
    total_orders,
    lifetime_value,
    RANK()       OVER (ORDER BY lifetime_value DESC)            AS ltv_rank,
    DENSE_RANK() OVER (ORDER BY lifetime_value DESC)            AS ltv_dense_rank,
    PERCENT_RANK() OVER (ORDER BY lifetime_value)               AS ltv_percentile
FROM   customer_ltv
ORDER  BY ltv_rank
LIMIT  20;


-- ─────────────────────────────────────────────
-- 5.2  Running Total Revenue (Cumulative)
--      SUM() OVER with ORDER BY order_date
-- ─────────────────────────────────────────────
WITH daily_revenue AS (
    SELECT
        o.order_date,
        ROUND(
            SUM(oi.quantity * oi.unit_price * (1 - oi.discount)),
            2
        )                                                       AS daily_revenue
    FROM   orders      o
    JOIN   order_items oi ON o.order_id = oi.order_id
    WHERE  o.status NOT IN ('cancelled', 'returned')
    GROUP  BY o.order_date
)
SELECT
    order_date,
    daily_revenue,
    ROUND(
        SUM(daily_revenue) OVER (ORDER BY order_date
                                 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),
        2
    )                                                           AS running_total
FROM   daily_revenue
ORDER  BY order_date;


-- ─────────────────────────────────────────────
-- 5.3  3-Month Moving Average of Monthly Revenue
--      AVG() OVER sliding window
-- ─────────────────────────────────────────────
WITH monthly_revenue AS (
    SELECT
        STRFTIME('%Y-%m', o.order_date)                         AS year_month,
        ROUND(
            SUM(oi.quantity * oi.unit_price * (1 - oi.discount)),
            2
        )                                                       AS revenue
    FROM   orders      o
    JOIN   order_items oi ON o.order_id = oi.order_id
    WHERE  o.status NOT IN ('cancelled', 'returned')
    GROUP  BY year_month
)
SELECT
    year_month,
    revenue,
    ROUND(
        AVG(revenue) OVER (ORDER BY year_month
                           ROWS BETWEEN 2 PRECEDING AND CURRENT ROW),
        2
    )                                                           AS moving_avg_3m
FROM   monthly_revenue
ORDER  BY year_month;


-- ─────────────────────────────────────────────
-- 5.4  Customer Order Sequence
--      ROW_NUMBER() OVER PARTITION BY customer
-- ─────────────────────────────────────────────
SELECT
    o.customer_id,
    c.name                                                      AS customer_name,
    o.order_id,
    o.order_date,
    ROUND(
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount)),
        2
    )                                                           AS order_value,
    ROW_NUMBER() OVER (
        PARTITION BY o.customer_id
        ORDER       BY o.order_date
    )                                                           AS order_seq
FROM   orders      o
JOIN   customers   c  ON o.customer_id = c.customer_id
JOIN   order_items oi ON o.order_id    = oi.order_id
WHERE  o.status NOT IN ('cancelled', 'returned')
GROUP  BY o.order_id, o.customer_id, c.name, o.order_date
ORDER  BY o.customer_id, order_seq
LIMIT  40;


-- ─────────────────────────────────────────────
-- 5.5  Customer Revenue Quartiles (NTILE)
-- ─────────────────────────────────────────────
WITH customer_spend AS (
    SELECT
        c.customer_id,
        c.name,
        ROUND(
            SUM(oi.quantity * oi.unit_price * (1 - oi.discount)),
            2
        )                                                       AS total_spend
    FROM   customers   c
    JOIN   orders      o  ON c.customer_id = o.customer_id
    JOIN   order_items oi ON o.order_id    = oi.order_id
    WHERE  o.status NOT IN ('cancelled', 'returned')
    GROUP  BY c.customer_id, c.name
)
SELECT
    customer_id,
    name,
    total_spend,
    NTILE(4) OVER (ORDER BY total_spend)                        AS spend_quartile,
    CASE NTILE(4) OVER (ORDER BY total_spend)
        WHEN 1 THEN 'Q1 – Low'
        WHEN 2 THEN 'Q2 – Mid-Low'
        WHEN 3 THEN 'Q3 – Mid-High'
        WHEN 4 THEN 'Q4 – High'
    END                                                         AS quartile_label
FROM   customer_spend
ORDER  BY total_spend DESC
LIMIT  30;


-- ─────────────────────────────────────────────
-- 5.6  Month-over-Month Revenue Growth Rate
--      Multi-step CTE with LAG()
-- ─────────────────────────────────────────────
WITH monthly AS (
    SELECT
        STRFTIME('%Y-%m', o.order_date)                         AS ym,
        ROUND(
            SUM(oi.quantity * oi.unit_price * (1 - oi.discount)),
            2
        )                                                       AS revenue
    FROM   orders      o
    JOIN   order_items oi ON o.order_id = oi.order_id
    WHERE  o.status NOT IN ('cancelled', 'returned')
    GROUP  BY ym
),
with_lag AS (
    SELECT
        ym,
        revenue,
        LAG(revenue, 1) OVER (ORDER BY ym)                     AS prev_month_revenue,
        LAG(revenue, 3) OVER (ORDER BY ym)                     AS prev_quarter_revenue
    FROM monthly
)
SELECT
    ym                                                          AS month,
    revenue,
    prev_month_revenue,
    CASE
        WHEN prev_month_revenue IS NULL OR prev_month_revenue = 0 THEN NULL
        ELSE ROUND(
                (revenue - prev_month_revenue) * 100.0 / prev_month_revenue,
                2
             )
    END                                                         AS mom_growth_pct,
    CASE
        WHEN prev_quarter_revenue IS NULL OR prev_quarter_revenue = 0 THEN NULL
        ELSE ROUND(
                (revenue - prev_quarter_revenue) * 100.0 / prev_quarter_revenue,
                2
             )
    END                                                         AS qoq_growth_pct
FROM   with_lag
ORDER  BY ym;


-- ─────────────────────────────────────────────
-- 5.7  Cumulative Revenue Share per Category
--      SUM() OVER PARTITION
-- ─────────────────────────────────────────────
WITH cat_rev AS (
    SELECT
        p.category,
        STRFTIME('%Y-%m', o.order_date)                         AS ym,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount))   AS revenue
    FROM   products    p
    JOIN   order_items oi ON p.product_id = oi.product_id
    JOIN   orders      o  ON oi.order_id  = o.order_id
    WHERE  o.status NOT IN ('cancelled', 'returned')
    GROUP  BY p.category, ym
)
SELECT
    category,
    ym,
    ROUND(revenue, 2)                                           AS monthly_revenue,
    ROUND(
        SUM(revenue) OVER (PARTITION BY category ORDER BY ym),
        2
    )                                                           AS cumulative_revenue,
    ROUND(
        revenue * 100.0 /
        SUM(revenue) OVER (PARTITION BY ym),
        2
    )                                                           AS monthly_share_pct
FROM   cat_rev
ORDER  BY category, ym
LIMIT  50;


-- ─────────────────────────────────────────────
-- 5.8  First and Last Order Dates per Customer
--      (using MIN/MAX as window-like aggregates)
-- ─────────────────────────────────────────────
WITH order_vals AS (
    SELECT
        o.customer_id,
        o.order_id,
        o.order_date,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount))   AS order_value
    FROM   orders      o
    JOIN   order_items oi ON o.order_id = oi.order_id
    WHERE  o.status NOT IN ('cancelled', 'returned')
    GROUP  BY o.order_id, o.customer_id, o.order_date
)
SELECT
    ov.customer_id,
    c.name,
    MIN(ov.order_date)                                          AS first_order_date,
    MAX(ov.order_date)                                          AS last_order_date,
    COUNT(ov.order_id)                                          AS total_orders,
    ROUND(SUM(ov.order_value), 2)                               AS total_spend,
    ROUND(
        JULIANDAY(MAX(ov.order_date)) - JULIANDAY(MIN(ov.order_date)),
        0
    )                                                           AS customer_lifespan_days
FROM   order_vals ov
JOIN   customers  c ON ov.customer_id = c.customer_id
GROUP  BY ov.customer_id, c.name
ORDER  BY customer_lifespan_days DESC
LIMIT  20;

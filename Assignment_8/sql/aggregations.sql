-- =============================================================
-- aggregations.sql
-- Step 4: SQL Analytics — JOINs & Aggregations
-- Author : Ashmit Gupta
-- Project: Assignment 8 — End-to-End Data Analytics
-- =============================================================
-- Covers:
--   4.1  Total revenue per customer
--   4.2  Total revenue per category
--   4.3  Total revenue per month
--   4.4  Top products by quantity sold
--   4.5  Top products by revenue
--   4.6  Average Order Value (AOV) overall
--   4.7  AOV by payment method
--   4.8  AOV by customer segment (frequency-based)
--   4.9  Revenue share % per category
--  4.10  Orders & revenue by status
-- =============================================================

-- ─────────────────────────────────────────────
-- 4.1  Total Revenue per Customer
--      (using all four tables with JOINs)
-- ─────────────────────────────────────────────
SELECT
    c.customer_id                                           AS customer_id,
    c.name                                                  AS customer_name,
    c.city,
    c.country,
    COUNT(DISTINCT o.order_id)                              AS total_orders,
    SUM(oi.quantity)                                        AS total_items_bought,
    ROUND(
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount)),
        2
    )                                                       AS lifetime_revenue
FROM   customers   c
JOIN   orders      o  ON c.customer_id = o.customer_id
JOIN   order_items oi ON o.order_id    = oi.order_id
WHERE  o.status NOT IN ('cancelled', 'returned')
GROUP  BY c.customer_id, c.name, c.city, c.country
ORDER  BY lifetime_revenue DESC
LIMIT  20;


-- ─────────────────────────────────────────────
-- 4.2  Total Revenue per Product Category
-- ─────────────────────────────────────────────
SELECT
    p.category                                              AS category,
    COUNT(DISTINCT p.product_id)                            AS num_products,
    COUNT(DISTINCT o.order_id)                              AS num_orders,
    SUM(oi.quantity)                                        AS units_sold,
    ROUND(
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount)),
        2
    )                                                       AS total_revenue,
    ROUND(
        AVG(oi.unit_price),
        2
    )                                                       AS avg_unit_price
FROM   products    p
JOIN   order_items oi ON p.product_id  = oi.product_id
JOIN   orders      o  ON oi.order_id   = o.order_id
WHERE  o.status NOT IN ('cancelled', 'returned')
GROUP  BY p.category
ORDER  BY total_revenue DESC;


-- ─────────────────────────────────────────────
-- 4.3  Monthly Revenue Trend
-- ─────────────────────────────────────────────
SELECT
    STRFTIME('%Y', o.order_date)                            AS year,
    STRFTIME('%m', o.order_date)                            AS month,
    STRFTIME('%Y-%m', o.order_date)                         AS year_month,
    COUNT(DISTINCT o.order_id)                              AS num_orders,
    SUM(oi.quantity)                                        AS units_sold,
    ROUND(
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount)),
        2
    )                                                       AS monthly_revenue
FROM   orders      o
JOIN   order_items oi ON o.order_id = oi.order_id
WHERE  o.status NOT IN ('cancelled', 'returned')
GROUP  BY year_month
ORDER  BY year_month;


-- ─────────────────────────────────────────────
-- 4.4  Top 10 Products by Quantity Sold
-- ─────────────────────────────────────────────
SELECT
    p.product_id,
    p.name                                                  AS product_name,
    p.category,
    SUM(oi.quantity)                                        AS units_sold,
    COUNT(DISTINCT o.order_id)                              AS order_count,
    ROUND(
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount)),
        2
    )                                                       AS total_revenue
FROM   products    p
JOIN   order_items oi ON p.product_id = oi.product_id
JOIN   orders      o  ON oi.order_id  = o.order_id
WHERE  o.status NOT IN ('cancelled', 'returned')
GROUP  BY p.product_id, p.name, p.category
ORDER  BY units_sold DESC
LIMIT  10;


-- ─────────────────────────────────────────────
-- 4.5  Top 10 Products by Revenue
-- ─────────────────────────────────────────────
SELECT
    p.product_id,
    p.name                                                  AS product_name,
    p.category,
    SUM(oi.quantity)                                        AS units_sold,
    ROUND(
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount)),
        2
    )                                                       AS total_revenue,
    ROUND(AVG(oi.unit_price), 2)                            AS avg_price
FROM   products    p
JOIN   order_items oi ON p.product_id = oi.product_id
JOIN   orders      o  ON oi.order_id  = o.order_id
WHERE  o.status NOT IN ('cancelled', 'returned')
GROUP  BY p.product_id, p.name, p.category
ORDER  BY total_revenue DESC
LIMIT  10;


-- ─────────────────────────────────────────────
-- 4.6  Overall Average Order Value (AOV)
-- ─────────────────────────────────────────────
SELECT
    COUNT(DISTINCT o.order_id)                              AS total_orders,
    ROUND(
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount)),
        2
    )                                                       AS total_revenue,
    ROUND(
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount))
        / COUNT(DISTINCT o.order_id),
        2
    )                                                       AS aov
FROM   orders      o
JOIN   order_items oi ON o.order_id = oi.order_id
WHERE  o.status NOT IN ('cancelled', 'returned');


-- ─────────────────────────────────────────────
-- 4.7  AOV by Payment Method
-- ─────────────────────────────────────────────
SELECT
    o.payment_method,
    COUNT(DISTINCT o.order_id)                              AS total_orders,
    ROUND(
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount)),
        2
    )                                                       AS total_revenue,
    ROUND(
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount))
        / COUNT(DISTINCT o.order_id),
        2
    )                                                       AS aov
FROM   orders      o
JOIN   order_items oi ON o.order_id = oi.order_id
WHERE  o.status NOT IN ('cancelled', 'returned')
GROUP  BY o.payment_method
ORDER  BY aov DESC;


-- ─────────────────────────────────────────────
-- 4.8  AOV by Customer Frequency Segment
-- ─────────────────────────────────────────────
WITH customer_freq AS (
    SELECT
        customer_id,
        COUNT(DISTINCT order_id) AS order_count
    FROM orders
    WHERE status NOT IN ('cancelled', 'returned')
    GROUP BY customer_id
),
segmented_customers AS (
    SELECT
        customer_id,
        CASE
            WHEN order_count = 1           THEN 'One-Time'
            WHEN order_count BETWEEN 2 AND 4 THEN 'Occasional'
            ELSE                               'Loyal'
        END AS segment
    FROM customer_freq
),
order_values AS (
    SELECT
        o.order_id,
        o.customer_id,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS order_value
    FROM   orders      o
    JOIN   order_items oi ON o.order_id = oi.order_id
    WHERE  o.status NOT IN ('cancelled', 'returned')
    GROUP  BY o.order_id, o.customer_id
)
SELECT
    sc.segment,
    COUNT(DISTINCT ov.order_id)               AS total_orders,
    ROUND(SUM(ov.order_value), 2)             AS total_revenue,
    ROUND(AVG(ov.order_value), 2)             AS avg_order_value
FROM   order_values        ov
JOIN   segmented_customers sc ON ov.customer_id = sc.customer_id
GROUP  BY sc.segment
ORDER  BY avg_order_value DESC;


-- ─────────────────────────────────────────────
-- 4.9  Revenue Share % per Category
-- ─────────────────────────────────────────────
WITH category_revenue AS (
    SELECT
        p.category,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS revenue
    FROM   products    p
    JOIN   order_items oi ON p.product_id = oi.product_id
    JOIN   orders      o  ON oi.order_id  = o.order_id
    WHERE  o.status NOT IN ('cancelled', 'returned')
    GROUP  BY p.category
),
total AS (
    SELECT SUM(revenue) AS grand_total FROM category_revenue
)
SELECT
    cr.category,
    ROUND(cr.revenue, 2)                                    AS revenue,
    ROUND(cr.revenue * 100.0 / t.grand_total, 2)           AS revenue_share_pct
FROM   category_revenue cr
CROSS  JOIN total t
ORDER  BY revenue DESC;


-- ─────────────────────────────────────────────
-- 4.10  Orders & Revenue by Order Status
-- ─────────────────────────────────────────────
SELECT
    o.status,
    COUNT(DISTINCT o.order_id)                              AS num_orders,
    ROUND(
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount)),
        2
    )                                                       AS total_revenue,
    ROUND(
        AVG(oi.quantity * oi.unit_price * (1 - oi.discount)),
        2
    )                                                       AS avg_item_value
FROM   orders      o
JOIN   order_items oi ON o.order_id = oi.order_id
GROUP  BY o.status
ORDER  BY num_orders DESC;

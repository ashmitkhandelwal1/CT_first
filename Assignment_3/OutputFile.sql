-- Superstore Sales Analysis
-- Celebal Technologies - Week 3 Assessment
-- Name: Ashmit Gupta


-- ─────────────────────────────────────
-- STEP 1: Create the raw table
-- ─────────────────────────────────────
CREATE TABLE superstore_raw (
    row_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id     TEXT,
    order_date   TEXT,
    customer_id  TEXT,
    segment      TEXT,
    category     TEXT,
    sub_category TEXT,
    product_id   TEXT,
    product_name TEXT,
    sales        REAL,
    quantity     INTEGER,
    discount     REAL,
    profit       REAL
);
-- Load data from CSV here


-- ─────────────────────────────────────
-- STEP 2: Create 3 tables from raw data
-- ─────────────────────────────────────

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    segment     TEXT
);
INSERT OR IGNORE INTO customers
SELECT DISTINCT customer_id, segment FROM superstore_raw;

CREATE TABLE products (
    product_id   TEXT PRIMARY KEY,
    product_name TEXT,
    category     TEXT,
    sub_category TEXT
);
INSERT OR IGNORE INTO products
SELECT DISTINCT product_id, product_name, category, sub_category FROM superstore_raw;

CREATE TABLE orders (
    order_id    TEXT,
    order_date  TEXT,
    customer_id TEXT,
    product_id  TEXT,
    sales       REAL,
    quantity    INTEGER,
    discount    REAL,
    profit      REAL
);
INSERT INTO orders
SELECT order_id, order_date, customer_id, product_id,
       sales, quantity, discount, profit
FROM superstore_raw;


-- ─────────────────────────────────────
-- STEP 3: Subqueries
-- ─────────────────────────────────────

-- 3A. Orders with above-average sales
SELECT order_id, customer_id, ROUND(sales,2) AS sales
FROM orders
WHERE sales > (SELECT AVG(sales) FROM orders)
ORDER BY sales DESC;

-- 3B. Highest order per customer
SELECT o.customer_id, o.order_id, ROUND(o.sales,2) AS top_sale
FROM orders o
WHERE o.sales = (
    SELECT MAX(o2.sales)
    FROM orders o2
    WHERE o2.customer_id = o.customer_id
)
ORDER BY top_sale DESC;


-- ─────────────────────────────────────
-- STEP 4: CTEs
-- ─────────────────────────────────────

-- 4A. Total sales per customer
WITH customer_sales AS (
    SELECT customer_id,
           ROUND(SUM(sales),2) AS total_sales,
           COUNT(DISTINCT order_id) AS num_orders
    FROM orders
    GROUP BY customer_id
)
SELECT cs.customer_id, c.segment, cs.total_sales, cs.num_orders
FROM customer_sales cs
JOIN customers c ON cs.customer_id = c.customer_id
ORDER BY total_sales DESC;

-- 4B. Top 5 customers
WITH customer_sales AS (
    SELECT customer_id, ROUND(SUM(sales),2) AS total_sales
    FROM orders GROUP BY customer_id
)
SELECT customer_id, total_sales
FROM customer_sales
ORDER BY total_sales DESC LIMIT 5;

-- 4C. Bottom 5 customers
WITH customer_sales AS (
    SELECT customer_id, ROUND(SUM(sales),2) AS total_sales
    FROM orders GROUP BY customer_id
)
SELECT customer_id, total_sales
FROM customer_sales
ORDER BY total_sales ASC LIMIT 5;


-- ─────────────────────────────────────
-- STEP 5: Window Functions
-- ─────────────────────────────────────

-- 5A. ROW_NUMBER per category
SELECT p.category, p.product_name, ROUND(o.sales,2) AS sales,
       ROW_NUMBER() OVER (PARTITION BY p.category ORDER BY o.sales DESC) AS row_num
FROM orders o
JOIN products p ON o.product_id = p.product_id;

-- 5B. RANK customers by total sales
SELECT customer_id,
       ROUND(SUM(sales),2) AS total_sales,
       RANK() OVER (ORDER BY SUM(sales) DESC) AS rank
FROM orders
GROUP BY customer_id;

-- 5C. Running total of sales
SELECT order_date, order_id, ROUND(sales,2) AS sale,
       ROUND(SUM(sales) OVER (ORDER BY order_date), 2) AS running_total
FROM orders
ORDER BY order_date;


-- ─────────────────────────────────────
-- STEP 6: JOIN + CTE + Window Function
-- ─────────────────────────────────────
WITH totals AS (
    SELECT customer_id,
           ROUND(SUM(sales),2)  AS total_sales,
           ROUND(SUM(profit),2) AS total_profit,
           COUNT(DISTINCT order_id) AS orders
    FROM orders
    GROUP BY customer_id
),
ranked AS (
    SELECT *, RANK() OVER (ORDER BY total_sales DESC) AS sales_rank
    FROM totals
)
SELECT r.sales_rank, r.customer_id, c.segment,
       r.orders, r.total_sales, r.total_profit
FROM ranked r
JOIN customers c ON r.customer_id = c.customer_id
ORDER BY sales_rank;


-- ─────────────────────────────────────
-- STEP 7: Business Questions
-- ─────────────────────────────────────

-- Q1. Customers with only 1 order
SELECT customer_id, COUNT(DISTINCT order_id) AS num_orders
FROM orders
GROUP BY customer_id
HAVING COUNT(DISTINCT order_id) = 1;

-- Q2. Above-average spending customers
WITH totals AS (
    SELECT customer_id, ROUND(SUM(sales),2) AS total_sales
    FROM orders GROUP BY customer_id
)
SELECT customer_id, total_sales
FROM totals
WHERE total_sales > (SELECT AVG(total_sales) FROM totals)
ORDER BY total_sales DESC;

-- Q3. Sales by category
SELECT p.category,
       ROUND(SUM(o.sales),2)  AS total_sales,
       ROUND(SUM(o.profit),2) AS total_profit
FROM orders o
JOIN products p ON o.product_id = p.product_id
GROUP BY p.category
ORDER BY total_sales DESC;

-- Q4. Most profitable sub-categories
SELECT p.sub_category, ROUND(SUM(o.profit),2) AS total_profit
FROM orders o
JOIN products p ON o.product_id = p.product_id
GROUP BY p.sub_category
ORDER BY total_profit DESC
LIMIT 8;

-- End of script – Ashmit Gupta | Celebal Week 3

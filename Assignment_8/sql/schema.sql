-- =============================================================
-- schema.sql
-- E-Commerce Analytics System — Database Schema (SQLite)
-- Author : Ashmit Gupta
-- Project: Assignment 8 — End-to-End Data Analytics
-- =============================================================
-- Creates four core tables with:
--   PK  → PRIMARY KEY constraints
--   FK  → FOREIGN KEY relationships
--   NOT NULL on critical columns
--   DEFAULT values where appropriate
-- =============================================================

PRAGMA foreign_keys = OFF;

-- ─────────────────────────────────────────────
-- Drop in reverse dependency order
-- ─────────────────────────────────────────────
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

PRAGMA foreign_keys = ON;

-- ─────────────────────────────────────────────
-- 1. Customers
-- ─────────────────────────────────────────────
CREATE TABLE customers (
    customer_id    INTEGER  PRIMARY KEY,
    name           TEXT     NOT NULL,
    email          TEXT     NOT NULL UNIQUE,
    phone          TEXT,
    city           TEXT     DEFAULT 'Unknown',
    country        TEXT     DEFAULT 'Unknown',
    signup_date    TEXT,                        -- stored as YYYY-MM-DD
    age            REAL,
    gender         TEXT     DEFAULT 'Unknown',
    loyalty_points INTEGER  DEFAULT 0
);

-- ─────────────────────────────────────────────
-- 2. Products
-- ─────────────────────────────────────────────
CREATE TABLE products (
    product_id   INTEGER  PRIMARY KEY,
    name         TEXT     NOT NULL,
    category     TEXT     DEFAULT 'Uncategorised',
    price        REAL     NOT NULL CHECK (price > 0),
    stock_qty    INTEGER  DEFAULT 0 CHECK (stock_qty >= 0),
    supplier_id  INTEGER,
    created_at   TEXT                            -- YYYY-MM-DD
);

-- ─────────────────────────────────────────────
-- 3. Orders
-- ─────────────────────────────────────────────
CREATE TABLE orders (
    order_id        INTEGER  PRIMARY KEY,
    customer_id     INTEGER  NOT NULL
                             REFERENCES customers (customer_id)
                             ON DELETE RESTRICT,
    order_date      TEXT     NOT NULL,           -- YYYY-MM-DD
    ship_date       TEXT,                        -- YYYY-MM-DD
    status          TEXT     DEFAULT 'unknown'
                             CHECK (status IN (
                                 'pending','shipped','delivered',
                                 'cancelled','returned','unknown'
                             )),
    total_amount    REAL     DEFAULT 0.0 CHECK (total_amount >= 0),
    payment_method  TEXT,
    shipping_city   TEXT
);

-- ─────────────────────────────────────────────
-- 4. Order Items
-- ─────────────────────────────────────────────
CREATE TABLE order_items (
    item_id    INTEGER  PRIMARY KEY,
    order_id   INTEGER  NOT NULL
                        REFERENCES orders   (order_id)
                        ON DELETE CASCADE,
    product_id INTEGER  NOT NULL
                        REFERENCES products (product_id)
                        ON DELETE RESTRICT,
    quantity   INTEGER  NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price REAL     NOT NULL CHECK (unit_price > 0),
    discount   REAL     DEFAULT 0.0
                        CHECK (discount >= 0 AND discount <= 1)
);

-- ─────────────────────────────────────────────
-- Indexes for query performance
-- ─────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_orders_customer
    ON orders (customer_id);

CREATE INDEX IF NOT EXISTS idx_orders_date
    ON orders (order_date);

CREATE INDEX IF NOT EXISTS idx_order_items_order
    ON order_items (order_id);

CREATE INDEX IF NOT EXISTS idx_order_items_product
    ON order_items (product_id);

CREATE INDEX IF NOT EXISTS idx_products_category
    ON products (category);

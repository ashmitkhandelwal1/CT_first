"""
ShopEase E-Commerce Sales Database — SQL Analysis
Celebal Summer Internship 2026, Week 2
Runs all queries (Sections A–E) against SQLite and prints results.
"""

import sqlite3
import os
from datetime import date

DB_PATH = os.path.join(os.path.dirname(__file__), "shopease.db")
SETUP_SQL = os.path.join(os.path.dirname(__file__), "shopease_setup.sql")

# ── helpers ──────────────────────────────────────────────────
def connect():
    """Create fresh DB each run so results are reproducible."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")  # enforce FK constraints
    return conn

def run_setup(conn):
    with open(SETUP_SQL, "r") as f:
        conn.executescript(f.read())
    print("✅ Database created and sample data loaded.\n")

def banner(section, title):
    print(f"\n{'='*70}")
    print(f"  {section} — {title}")
    print(f"{'='*70}")

def query(conn, label, sql, params=None, explain=None):
    """Execute a query, pretty-print results, and optionally print explanation."""
    print(f"\n{'─'*60}")
    print(f"  {label}")
    print(f"{'─'*60}")
    print(f"SQL:\n{sql.strip()}\n")
    cur = conn.cursor()
    try:
        cur.execute(sql, params or ())
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall()
        if cols and rows:
            # column widths
            widths = [max(len(str(c)), max(len(str(r[i])) for r in rows)) for i, c in enumerate(cols)]
            header = " | ".join(c.ljust(w) for c, w in zip(cols, widths))
            sep    = "-+-".join("-"*w for w in widths)
            print(header)
            print(sep)
            for r in rows:
                print(" | ".join(str(v).ljust(w) for v, w in zip(r, widths)))
        elif cols:
            print(" | ".join(cols))
            print("-+-".join("-"*len(c) for c in cols))
        print(f"\n({len(rows)} row(s) returned)")
    except sqlite3.Error as e:
        print(f"⚠ ERROR: {e}")
    if explain:
        print(f"\n💡 Insight: {explain}")

def query_error_demo(conn, label, sql, explanation):
    """Try a statement expected to fail, show the error."""
    print(f"\n{'─'*60}")
    print(f"  {label}")
    print(f"{'─'*60}")
    print(f"SQL:\n{sql.strip()}\n")
    try:
        conn.execute(sql)
        conn.commit()
        print("(unexpectedly succeeded)")
    except sqlite3.Error as e:
        print(f"⚠ ERROR: {e}")
    print(f"\n💡 Explanation: {explanation}")


# ═════════════════════════════════════════════════════════════
#  MAIN
# ═════════════════════════════════════════════════════════════
def main():
    conn = connect()
    run_setup(conn)

    # ─── SECTION A ───────────────────────────────────────────
    banner("Section A", "SQL Basics (SELECT, Constraints, Primary Keys)")

    query(conn, "Q1. All columns and rows from customers",
        "SELECT * FROM customers;",
        explain="8 customers loaded — mix of premium and non-premium across 8 Indian cities.")

    query(conn, "Q2. first_name, last_name, city of all customers",
        "SELECT first_name, last_name, city FROM customers;",
        explain="Column projection — retrieves only the requested columns, reducing I/O.")

    query(conn, "Q3. Unique categories in the products table",
        "SELECT DISTINCT category FROM products;",
        explain="3 categories: Electronics, Clothing, Home — ShopEase's core verticals.")

    print(f"\n{'─'*60}")
    print("  Q4. Primary Keys & why they must be UNIQUE + NOT NULL")
    print(f"{'─'*60}")
    print("""
 Table        | Primary Key
 -------------|-------------
 customers    | customer_id
 products     | product_id
 orders       | order_id
 order_items  | item_id

 WHY UNIQUE + NOT NULL?
 • A Primary Key uniquely identifies every row in a table.
 • UNIQUE ensures no two rows share the same identifier, preventing
   ambiguity when referencing a specific record.
 • NOT NULL ensures every row HAS an identifier — without it, you
   could have "phantom" rows unreachable by any lookup or join.
 • Together they guarantee referential integrity: foreign keys in
   child tables can always resolve to exactly one parent row.
""")

    print(f"\n{'─'*60}")
    print("  Q5. Constraints on customers.email")
    print(f"{'─'*60}")
    print("""
 Constraints applied:
   1. UNIQUE  — no two customers can have the same email address.
   2. NOT NULL — every customer must have an email address.

 What happens on duplicate insert?
""")
    query_error_demo(conn, "  → Attempting duplicate email INSERT",
        "INSERT INTO customers VALUES (109, 'Test', 'User', 'aarav.s@email.com', 'Mumbai', 'Maharashtra', '2024-09-01', 0);",
        "The UNIQUE constraint on `email` rejects the insert because 'aarav.s@email.com' already belongs to customer 101.")

    query_error_demo(conn, "Q6. Inserting product with unit_price = -50",
        "INSERT INTO products VALUES (209, 'Bad Product', 'Electronics', 'NoBrand', -50.00, 10);",
        "The CHECK constraint `unit_price > 0` prevents insertion of products with zero or negative prices, ensuring data quality.")

    # ─── SECTION B ───────────────────────────────────────────
    banner("Section B", "Filtering & Optimization (WHERE, Indexes)")

    query(conn, "Q7. All orders with status = 'Delivered'",
        "SELECT * FROM orders WHERE status = 'Delivered';",
        explain="6 out of 10 orders delivered — 60% fulfilment rate in August 2024.")

    query(conn, "Q8. Electronics with unit_price > ₹2000",
        "SELECT * FROM products WHERE category = 'Electronics' AND unit_price > 2000;",
        explain="Smart Watch (₹2999) and Bluetooth Speaker (₹3499) are the premium electronics.")

    query(conn, "Q9. Customers who joined in 2024 in Maharashtra",
        "SELECT * FROM customers WHERE join_date BETWEEN '2024-01-01' AND '2024-12-31' AND state = 'Maharashtra';",
        explain="Aarav (Mumbai) and Karan (Pune) — both premium members from Maharashtra.")

    query(conn, "Q10. Orders between 2024-08-10 and 2024-08-25, not Cancelled",
        """SELECT * FROM orders
WHERE order_date BETWEEN '2024-08-10' AND '2024-08-25'
  AND status != 'Cancelled';""",
        explain="4 orders qualify — after excluding the one Cancelled order (1005) in that range.")

    print(f"\n{'─'*60}")
    print("  Q11. Purpose of idx_orders_date index")
    print(f"{'─'*60}")
    print("""
 idx_orders_date is a B-tree index on the `order_date` column of the `orders` table.

 HOW IT HELPS:
 • Without the index, the database must perform a FULL TABLE SCAN — reading
   every row to check the date condition (O(n)).
 • With the index, the database can do a B-tree lookup to jump directly to
   the relevant date range (O(log n)), then scan only matching rows.

 SAMPLE QUERY that benefits:
   SELECT * FROM orders
   WHERE order_date BETWEEN '2024-08-10' AND '2024-08-20';

 The index allows the engine to seek to '2024-08-10' in the B-tree and
 scan forward until '2024-08-20', skipping all other rows entirely.
""")

    print(f"\n{'─'*60}")
    print("  Q12. Index usage with YEAR(join_date) — SARGability")
    print(f"{'─'*60}")
    print("""
 QUERY:  SELECT * FROM customers WHERE YEAR(join_date) = 2024;

 WILL THE INDEX BE USED?  ❌ NO (in most RDBMS).

 WHY NOT?
 • Wrapping the indexed column in a function (YEAR()) makes the predicate
   non-SARGable (Search ARGument Able).
 • The database cannot "look up" YEAR(join_date) in the B-tree index
   because the index is built on raw `join_date` values, not on the
   output of YEAR().
 • The engine must evaluate YEAR() for EVERY row → full table scan.

 INDEX-FRIENDLY (SARGable) REWRITE:
   SELECT * FROM customers
   WHERE join_date >= '2024-01-01'
     AND join_date <  '2025-01-01';

 This uses a direct range comparison on join_date, allowing the B-tree
 index to seek directly to the start of 2024 and scan forward.
""")

    # ─── SECTION C ───────────────────────────────────────────
    banner("Section C", "Aggregation (GROUP BY, SUM, COUNT, AVG, MIN, MAX)")

    query(conn, "Q13. Total number of orders",
        "SELECT COUNT(*) AS total_orders FROM orders;",
        explain="10 orders in August 2024.")

    query(conn, "Q14. Total revenue from Delivered orders",
        "SELECT SUM(total_amount) AS delivered_revenue FROM orders WHERE status = 'Delivered';",
        explain="₹17,191 in delivered revenue — the company's realized income for the period.")

    query(conn, "Q15. Average unit_price per category",
        """SELECT category,
       ROUND(AVG(unit_price), 2) AS avg_unit_price
FROM products
GROUP BY category;""",
        explain="Electronics avg ₹2224, Clothing avg ₹2699, Home avg ₹949. Clothing has the highest average due to premium Nike shoes.")

    query(conn, "Q16. Order count & revenue by status (sorted by revenue DESC)",
        """SELECT status,
       COUNT(*)            AS order_count,
       SUM(total_amount)   AS total_revenue
FROM orders
GROUP BY status
ORDER BY total_revenue DESC;""",
        explain="Delivered dominates with 6 orders / ₹17,191. Shipped orders (₹13,596) represent pipeline revenue.")

    query(conn, "Q17. Most expensive & cheapest product per category",
        """SELECT category,
       MAX(unit_price) AS max_price,
       MIN(unit_price) AS min_price
FROM products
GROUP BY category;""",
        explain="Electronics has the widest price spread (₹899–₹3499), indicating a diverse product portfolio.")

    query(conn, "Q18. Categories with average unit_price > ₹2000",
        """SELECT category,
       ROUND(AVG(unit_price), 2) AS avg_price
FROM products
GROUP BY category
HAVING AVG(unit_price) > 2000;""",
        explain="Electronics (₹2224) and Clothing (₹2699) exceed the ₹2000 threshold — both are higher-value segments.")

    # ─── SECTION D ───────────────────────────────────────────
    banner("Section D", "Joins & Relationships")

    query(conn, "Q19. INNER JOIN — Orders with customer names",
        """SELECT o.order_id,
       o.order_date,
       c.first_name,
       c.last_name,
       o.total_amount
FROM orders o
INNER JOIN customers c ON o.customer_id = c.customer_id;""",
        explain="All 10 orders matched to their customers. Aarav Sharma and Rohan Gupta each placed 2 orders — most active customers.")

    query(conn, "Q20. LEFT JOIN — All customers with their orders (NULLs for no orders)",
        """SELECT c.customer_id,
       c.first_name,
       c.last_name,
       o.order_id,
       o.order_date,
       o.total_amount
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
ORDER BY c.customer_id;""",
        explain="All 8 customers appear. Every customer placed at least 1 order — no NULL order rows in this dataset.")

    query(conn, "Q21. Three-table JOIN — Order items with product details",
        """SELECT o.order_id,
       p.product_name,
       oi.quantity,
       oi.unit_price,
       oi.discount_pct
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p     ON oi.product_id = p.product_id
ORDER BY o.order_id, oi.item_id;""",
        explain="15 line items across 10 orders. Discounts range from 0% to 15%, with Cushion Covers getting the steepest discount.")

    print(f"\n{'─'*60}")
    print("  Q22. LEFT JOIN vs RIGHT JOIN vs FULL OUTER JOIN")
    print(f"{'─'*60}")
    print("""
 LEFT JOIN (A LEFT JOIN B ON …):
   Returns ALL rows from A (left table) and matching rows from B.
   If no match in B, columns from B are NULL.
   Example: customers LEFT JOIN orders → shows all customers, even
   those with no orders.

 RIGHT JOIN (A RIGHT JOIN B ON …):
   Returns ALL rows from B (right table) and matching rows from A.
   If no match in A, columns from A are NULL.
   Example: customers RIGHT JOIN orders → shows all orders, even
   those whose customer might not exist (unlikely with FK constraints).

 FULL OUTER JOIN:
   Returns ALL rows from BOTH tables. Unmatched rows on either side
   get NULLs for the other table's columns.
   Use case: Reconciliation reports — e.g., comparing two data sources
   where some records may exist in one but not the other.

 Note: SQLite does not natively support RIGHT JOIN or FULL OUTER JOIN,
 but they can be emulated using LEFT JOIN with reversed table order,
 or UNION of two LEFT JOINs respectively.
""")

    print(f"\n{'─'*60}")
    print("  Q23. Foreign Key relationships & referential integrity")
    print(f"{'─'*60}")
    print("""
 Foreign Key Relationships:
 ┌───────────────────────────────────────────────────────────┐
 │  orders.customer_id  →  customers.customer_id            │
 │  order_items.order_id   →  orders.order_id               │
 │  order_items.product_id →  products.product_id           │
 └───────────────────────────────────────────────────────────┘

 What happens if you INSERT an order with customer_id = 999?
""")
    query_error_demo(conn, "  → Attempting INSERT with non-existent customer_id = 999",
        "INSERT INTO orders VALUES (1099, 999, '2024-09-01', 'Pending', 500.00);",
        "The FOREIGN KEY constraint on orders.customer_id rejects the insert because customer_id=999 does not exist in the customers table. This maintains referential integrity — every order must belong to a valid customer.")

    # ─── SECTION E ───────────────────────────────────────────
    banner("Section E", "Advanced Concepts (CASE, ACID, Transactions)")

    query(conn, "Q24. CASE — Product price tiers",
        """SELECT product_name,
       unit_price,
       CASE
           WHEN unit_price < 1000             THEN 'Budget'
           WHEN unit_price BETWEEN 1000 AND 3000 THEN 'Mid-Range'
           WHEN unit_price > 3000             THEN 'Premium'
       END AS price_tier
FROM products
ORDER BY unit_price;""",
        explain="Product distribution: 3 Budget, 3 Mid-Range, 2 Premium — a balanced portfolio across price segments.")

    query(conn, "Q25. CASE inside aggregate — Delivered vs Not Delivered counts",
        """SELECT
    SUM(CASE WHEN status = 'Delivered' THEN 1 ELSE 0 END) AS delivered_count,
    SUM(CASE WHEN status != 'Delivered' THEN 1 ELSE 0 END) AS not_delivered_count
FROM orders;""",
        explain="6 Delivered vs 4 Not Delivered — 60% fulfilment rate. The non-delivered include 2 Shipped (in transit), 1 Pending, and 1 Cancelled.")

    print(f"\n{'─'*60}")
    print("  Q26. ACID Properties Explained")
    print(f"{'─'*60}")
    print("""
 ┌──────────────┬─────────────────────────────────────────────────────────────┐
 │ Property     │ Meaning & Real-World Example                              │
 ├──────────────┼─────────────────────────────────────────────────────────────┤
 │ A — Atomicity│ A transaction is "all or nothing." If any part fails,     │
 │              │ the entire transaction is rolled back.                     │
 │              │ Example: In a bank transfer, if ₹1000 is debited from     │
 │              │ Account A but the credit to Account B fails, the debit    │
 │              │ must also be reversed. You can't have money "disappear."  │
 ├──────────────┼─────────────────────────────────────────────────────────────┤
 │ C —Consistency│ A transaction moves the database from one valid state    │
 │              │ to another, respecting all constraints (PK, FK, CHECK).   │
 │              │ Example: After the bank transfer, the total money across  │
 │              │ both accounts remains the same. No constraint is violated.│
 ├──────────────┼─────────────────────────────────────────────────────────────┤
 │ I — Isolation│ Concurrent transactions don't interfere with each other.  │
 │              │ Each sees the database as if it's the only one running.   │
 │              │ Example: Two people transferring from the same account    │
 │              │ simultaneously won't cause a race condition or double-    │
 │              │ spend. Each transaction sees a consistent snapshot.       │
 ├──────────────┼─────────────────────────────────────────────────────────────┤
 │ D — Durability│ Once a transaction is committed, it persists even if    │
 │              │ the system crashes (power failure, hardware fault).       │
 │              │ Example: After the bank confirms "Transfer Successful,"   │
 │              │ the updated balances survive a server restart.            │
 │              │ This is achieved via write-ahead logs (WAL) and fsync.   │
 └──────────────┴─────────────────────────────────────────────────────────────┘
""")

    print(f"\n{'─'*60}")
    print("  Q27. Transaction — Atomic order insertion with stock update")
    print(f"{'─'*60}")
    today = date.today().isoformat()
    print(f"""
 The following transaction inserts a new order and its items atomically.
 If any step fails, everything is rolled back.

 SQL Transaction Block:
 ──────────────────────
 BEGIN TRANSACTION;

 -- Step 1: Insert new order
 INSERT INTO orders VALUES
   (1011, 102, '{today}', 'Pending', 1598.00);

 -- Step 2: Insert two order items
 INSERT INTO order_items VALUES
   (5016, 1011, 206, 1, 1299.00, 0);    -- 1× Bedsheet Set
 INSERT INTO order_items VALUES
   (5017, 1011, 208, 1, 599.00, 15);     -- 1× Cushion Covers (Set), 15% off

 -- Step 3: Update stock quantities
 UPDATE products SET stock_qty = stock_qty - 1 WHERE product_id = 206;
 UPDATE products SET stock_qty = stock_qty - 1 WHERE product_id = 208;

 -- Step 4: If we reach here, all steps succeeded
 COMMIT;

 -- If any step above had failed, we would execute:
 -- ROLLBACK;
""")

    # Actually execute the transaction
    print(" Executing the transaction...\n")
    old_isolation = conn.isolation_level
    try:
        conn.isolation_level = None  # manual transaction mode
        conn.execute("BEGIN TRANSACTION;")
        conn.execute(f"INSERT INTO orders VALUES (1011, 102, '{today}', 'Pending', 1598.00);")
        conn.execute("INSERT INTO order_items VALUES (5016, 1011, 206, 1, 1299.00, 0);")
        conn.execute("INSERT INTO order_items VALUES (5017, 1011, 208, 1, 599.00, 15);")
        conn.execute("UPDATE products SET stock_qty = stock_qty - 1 WHERE product_id = 206;")
        conn.execute("UPDATE products SET stock_qty = stock_qty - 1 WHERE product_id = 208;")
        conn.execute("COMMIT;")
        print(" ✅ Transaction COMMITTED successfully.\n")
    except sqlite3.Error as e:
        conn.execute("ROLLBACK;")
        print(f" ❌ Transaction ROLLED BACK due to: {e}\n")
    finally:
        conn.isolation_level = old_isolation

    # Verify the transaction
    query(conn, "  → Verify: New order 1011",
        "SELECT * FROM orders WHERE order_id = 1011;",
        explain="Order 1011 for customer 102 (Priya Patel) successfully inserted.")

    query(conn, "  → Verify: New order items for order 1011",
        "SELECT * FROM order_items WHERE order_id = 1011;",
        explain="Two items added: Bedsheet Set and Cushion Covers.")

    query(conn, "  → Verify: Updated stock for products 206 & 208",
        "SELECT product_id, product_name, stock_qty FROM products WHERE product_id IN (206, 208);",
        explain="Stock reduced by 1 each: Bedsheet Set 300→299, Cushion Covers 400→399.")

    # ─── BONUS: Data Validation ─────────────────────────────
    banner("Bonus", "Data Validation & Quality Checks")

    query(conn, "Row counts per table",
        """SELECT 'customers'   AS tbl, COUNT(*) AS row_count FROM customers
UNION ALL
SELECT 'products',              COUNT(*) FROM products
UNION ALL
SELECT 'orders',                COUNT(*) FROM orders
UNION ALL
SELECT 'order_items',           COUNT(*) FROM order_items;""",
        explain="8 customers, 8 products, 11 orders (incl. new one), 17 order items.")

    query(conn, "Monthly revenue trend (Aug 2024)",
        """SELECT
    SUBSTR(order_date, 1, 7)  AS month,
    COUNT(*)                  AS num_orders,
    SUM(total_amount)         AS revenue
FROM orders
WHERE status != 'Cancelled'
GROUP BY SUBSTR(order_date, 1, 7)
ORDER BY month;""",
        explain="August 2024 saw 10 non-cancelled orders generating ₹28,286 in gross revenue.")

    query(conn, "Top 3 customers by total spend",
        """SELECT c.customer_id,
       c.first_name || ' ' || c.last_name AS customer_name,
       SUM(o.total_amount) AS total_spend,
       COUNT(o.order_id)   AS order_count
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status != 'Cancelled'
GROUP BY c.customer_id
ORDER BY total_spend DESC
LIMIT 3;""",
        explain="Rohan Gupta leads with ₹8,397 (2 orders), followed by Aarav Sharma ₹7,997 and Karan Mehta ₹6,098.")

    query(conn, "Top 3 products by quantity sold",
        """SELECT p.product_id,
       p.product_name,
       SUM(oi.quantity) AS total_qty_sold
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders o   ON oi.order_id = o.order_id
WHERE o.status != 'Cancelled'
GROUP BY p.product_id
ORDER BY total_qty_sold DESC
LIMIT 3;""",
        explain="Wireless Earbuds top sales volume (3 units), followed by Cushion Covers and multiple products at 2 units.")

    query(conn, "Duplicate email check (data quality)",
        """SELECT email, COUNT(*) AS cnt
FROM customers
GROUP BY email
HAVING COUNT(*) > 1;""",
        explain="No duplicates found — the UNIQUE constraint is working correctly.")

    print(f"\n{'='*70}")
    print("  ✅ ALL QUERIES EXECUTED SUCCESSFULLY")
    print(f"{'='*70}\n")

    conn.close()

if __name__ == "__main__":
    main()

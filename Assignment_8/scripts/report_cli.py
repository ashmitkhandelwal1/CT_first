"""
report_cli.py
-------------
Author : Ashmit Gupta
Project: E-Commerce Analytics System (Assignment 8)

Steps 8 & 9: Command-Line Reporting Tool

Usage:
  python report_cli.py --report revenue
  python report_cli.py --report top_customers [--limit N]
  python report_cli.py --report top_products  [--limit N]
  python report_cli.py --report retention
  python report_cli.py --report segmentation
  python report_cli.py --report monthly_revenue
  python report_cli.py --report aov
  python report_cli.py --report rfm
  python report_cli.py --report all

Available reports:
  revenue          - Total revenue per category
  top_customers    - Customers ranked by lifetime value
  top_products     - Products ranked by revenue & qty sold
  retention        - Cohort-based monthly retention rates
  segmentation     - Customer segments by frequency & spend
  monthly_revenue  - Monthly revenue with growth %
  aov              - Average order value by segment
  rfm              - RFM analysis (Recency, Frequency, Monetary)
  all              - Run every report
"""

import argparse
import os
import sys
import sqlite3
from datetime import datetime

# ── Optional pretty-printer ────────────────────────────────────────────────
try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH  = os.path.join(BASE_DIR, "ecommerce.db")


# ─────────────────────────────────────────────
# DB Connection
# ─────────────────────────────────────────────
def get_connection():
    if not os.path.exists(DB_PATH):
        print(f"\n❌  Database not found: {DB_PATH}")
        print("    Please run clean_data.py first to create the database.")
        sys.exit(1)
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"\n❌  Database connection error: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────
# Display helpers
# ─────────────────────────────────────────────
def print_header(title: str):
    width = max(len(title) + 4, 60)
    print(f"\n{'═' * width}")
    print(f"  📊  {title}")
    print(f"{'═' * width}")


def render_table(rows, headers=None):
    """Print rows as a formatted table."""
    if not rows:
        print("  ⚠️   No data returned for this report.")
        return

    if HAS_TABULATE:
        if headers:
            data = [list(r) for r in rows]
        else:
            headers = list(rows[0].keys())
            data    = [[r[k] for k in headers] for r in rows]
        print(tabulate(data, headers=headers, tablefmt="rounded_outline",
                       numalign="right", floatfmt=".2f"))
    else:
        # Plain-text fallback
        if not headers:
            headers = list(rows[0].keys())
        col_widths = [max(len(str(h)), max(len(str(r[h] if hasattr(r,'keys') else r[i]))
                          for r in rows))
                      for i, h in enumerate(headers)]
        sep  = "  ".join("-" * w for w in col_widths)
        line = "  ".join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers))
        print(f"  {line}")
        print(f"  {sep}")
        for row in rows:
            vals = [row[k] if hasattr(row, "keys") else row[i] for i, k in enumerate(headers)]
            line = "  ".join(str(v).ljust(col_widths[i]) for i, v in enumerate(vals))
            print(f"  {line}")

    print(f"\n  Total rows: {len(rows)}")


def run_query(conn, sql, params=()):
    """Execute a query and return rows, handling errors gracefully."""
    try:
        cur = conn.execute(sql, params)
        return cur.fetchall()
    except sqlite3.Error as e:
        print(f"\n  ❌  Query error: {e}")
        return []


# ─────────────────────────────────────────────
# Reports
# ─────────────────────────────────────────────

def report_revenue(conn):
    print_header("Total Revenue by Category")
    sql = """
        SELECT
            p.category                             AS Category,
            COUNT(DISTINCT o.order_id)             AS Orders,
            SUM(oi.quantity * oi.unit_price
                * (1 - oi.discount))               AS Revenue,
            ROUND(AVG(oi.unit_price), 2)           AS Avg_Unit_Price
        FROM   order_items oi
        JOIN   orders      o  ON oi.order_id   = o.order_id
        JOIN   products    p  ON oi.product_id = p.product_id
        WHERE  o.status NOT IN ('cancelled', 'returned')
        GROUP  BY p.category
        ORDER  BY Revenue DESC;
    """
    rows = run_query(conn, sql)
    render_table(rows)


def report_top_customers(conn, limit=10):
    print_header(f"Top {limit} Customers by Lifetime Value")
    sql = """
        SELECT
            c.customer_id                              AS ID,
            c.name                                     AS Name,
            c.city                                     AS City,
            COUNT(DISTINCT o.order_id)                 AS Total_Orders,
            ROUND(SUM(oi.quantity * oi.unit_price
                  * (1 - oi.discount)), 2)             AS Lifetime_Value,
            DENSE_RANK() OVER (
                ORDER BY SUM(oi.quantity * oi.unit_price * (1-oi.discount)) DESC
            )                                          AS LTV_Rank
        FROM   customers   c
        JOIN   orders      o  ON c.customer_id = o.customer_id
        JOIN   order_items oi ON o.order_id    = oi.order_id
        WHERE  o.status NOT IN ('cancelled', 'returned')
        GROUP  BY c.customer_id, c.name, c.city
        ORDER  BY Lifetime_Value DESC
        LIMIT  ?;
    """
    rows = run_query(conn, sql, (limit,))
    render_table(rows)


def report_top_products(conn, limit=10):
    print_header(f"Top {limit} Products by Revenue & Quantity Sold")
    sql = """
        SELECT
            p.product_id                               AS ID,
            p.name                                     AS Product,
            p.category                                 AS Category,
            SUM(oi.quantity)                           AS Qty_Sold,
            ROUND(SUM(oi.quantity * oi.unit_price
                  * (1 - oi.discount)), 2)             AS Revenue,
            RANK() OVER (ORDER BY SUM(oi.quantity) DESC) AS Qty_Rank
        FROM   order_items oi
        JOIN   products    p  ON oi.product_id = p.product_id
        JOIN   orders      o  ON oi.order_id   = o.order_id
        WHERE  o.status NOT IN ('cancelled', 'returned')
        GROUP  BY p.product_id, p.name, p.category
        ORDER  BY Revenue DESC
        LIMIT  ?;
    """
    rows = run_query(conn, sql, (limit,))
    render_table(rows)


def report_monthly_revenue(conn):
    print_header("Monthly Revenue with MoM Growth Rate")
    sql = """
        WITH monthly AS (
            SELECT
                STRFTIME('%Y-%m', o.order_date)            AS Month,
                ROUND(SUM(oi.quantity * oi.unit_price
                      * (1 - oi.discount)), 2)             AS Revenue
            FROM   orders      o
            JOIN   order_items oi ON o.order_id = oi.order_id
            WHERE  o.status NOT IN ('cancelled', 'returned')
            GROUP  BY Month
        ),
        with_growth AS (
            SELECT
                Month,
                Revenue,
                LAG(Revenue) OVER (ORDER BY Month)         AS Prev_Revenue
            FROM monthly
        )
        SELECT
            Month,
            Revenue,
            CASE
                WHEN Prev_Revenue IS NULL OR Prev_Revenue = 0 THEN NULL
                ELSE ROUND((Revenue - Prev_Revenue) * 100.0 / Prev_Revenue, 2)
            END                                            AS Growth_Pct
        FROM   with_growth
        ORDER  BY Month;
    """
    rows = run_query(conn, sql)
    render_table(rows)


def report_aov(conn):
    print_header("Average Order Value (AOV) by Customer Segment")
    sql = """
        WITH customer_orders AS (
            SELECT
                o.customer_id,
                o.order_id,
                SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS order_value
            FROM   orders      o
            JOIN   order_items oi ON o.order_id = oi.order_id
            WHERE  o.status NOT IN ('cancelled', 'returned')
            GROUP  BY o.customer_id, o.order_id
        ),
        customer_metrics AS (
            SELECT
                customer_id,
                COUNT(order_id)    AS order_count,
                SUM(order_value)   AS total_spend,
                AVG(order_value)   AS avg_order_val
            FROM customer_orders
            GROUP BY customer_id
        ),
        segmented AS (
            SELECT
                customer_id,
                avg_order_val,
                CASE
                    WHEN order_count = 1       THEN 'One-Time'
                    WHEN order_count BETWEEN 2 AND 4 THEN 'Occasional'
                    ELSE                            'Loyal'
                END AS freq_segment,
                CASE
                    WHEN total_spend < 500     THEN 'Low Spender'
                    WHEN total_spend < 2000    THEN 'Medium Spender'
                    ELSE                           'High Spender'
                END AS spend_tier
            FROM customer_metrics
        )
        SELECT
            freq_segment                       AS Segment,
            spend_tier                         AS Spend_Tier,
            COUNT(*)                           AS Customers,
            ROUND(AVG(avg_order_val), 2)       AS Avg_Order_Value
        FROM   segmented
        GROUP  BY freq_segment, spend_tier
        ORDER  BY Avg_Order_Value DESC;
    """
    rows = run_query(conn, sql)
    render_table(rows)


def report_retention(conn):
    print_header("Cohort Retention Analysis (by First Purchase Month)")
    sql = """
        WITH first_orders AS (
            SELECT
                customer_id,
                MIN(STRFTIME('%Y-%m', order_date)) AS cohort_month
            FROM   orders
            WHERE  status NOT IN ('cancelled','returned')
            GROUP  BY customer_id
        ),
        cohort_activity AS (
            SELECT
                f.cohort_month,
                STRFTIME('%Y-%m', o.order_date)    AS activity_month,
                COUNT(DISTINCT o.customer_id)       AS active_customers
            FROM   orders       o
            JOIN   first_orders f ON o.customer_id = f.customer_id
            WHERE  o.status NOT IN ('cancelled','returned')
            GROUP  BY f.cohort_month, activity_month
        ),
        cohort_sizes AS (
            SELECT cohort_month, COUNT(*) AS cohort_size
            FROM   first_orders
            GROUP  BY cohort_month
        )
        SELECT
            ca.cohort_month                             AS Cohort,
            ca.activity_month                           AS Month,
            cs.cohort_size                              AS Cohort_Size,
            ca.active_customers                         AS Active,
            ROUND(ca.active_customers * 100.0
                  / cs.cohort_size, 2)                  AS Retention_Pct
        FROM   cohort_activity ca
        JOIN   cohort_sizes    cs ON ca.cohort_month = cs.cohort_month
        ORDER  BY ca.cohort_month, ca.activity_month
        LIMIT  60;
    """
    rows = run_query(conn, sql)
    render_table(rows)


def report_segmentation(conn):
    print_header("Customer Segmentation (Frequency + Spend Tier)")
    sql = """
        WITH customer_summary AS (
            SELECT
                c.customer_id,
                c.name,
                COUNT(DISTINCT o.order_id)                  AS order_count,
                ROUND(SUM(oi.quantity * oi.unit_price
                      * (1 - oi.discount)), 2)              AS total_spend,
                MAX(o.order_date)                           AS last_order
            FROM   customers   c
            JOIN   orders      o  ON c.customer_id = o.customer_id
            JOIN   order_items oi ON o.order_id    = oi.order_id
            WHERE  o.status NOT IN ('cancelled','returned')
            GROUP  BY c.customer_id, c.name
        )
        SELECT
            customer_id                     AS ID,
            name                            AS Name,
            order_count                     AS Orders,
            total_spend                     AS Total_Spend,
            last_order                      AS Last_Order,
            CASE
                WHEN order_count = 1       THEN 'One-Time'
                WHEN order_count BETWEEN 2 AND 4 THEN 'Occasional'
                ELSE                            'Loyal'
            END                             AS Frequency_Segment,
            CASE
                WHEN total_spend < 500     THEN 'Low'
                WHEN total_spend < 2000    THEN 'Medium'
                ELSE                           'High'
            END                             AS Spend_Tier
        FROM   customer_summary
        ORDER  BY total_spend DESC
        LIMIT  30;
    """
    rows = run_query(conn, sql)
    render_table(rows)


def report_rfm(conn):
    print_header("RFM Analysis (Recency · Frequency · Monetary)")
    sql = """
        WITH rfm_base AS (
            SELECT
                c.customer_id,
                c.name,
                JULIANDAY('now') - JULIANDAY(MAX(o.order_date))  AS recency_days,
                COUNT(DISTINCT o.order_id)                        AS frequency,
                ROUND(SUM(oi.quantity * oi.unit_price
                      * (1 - oi.discount)), 2)                    AS monetary
            FROM   customers   c
            JOIN   orders      o  ON c.customer_id = o.customer_id
            JOIN   order_items oi ON o.order_id    = oi.order_id
            WHERE  o.status NOT IN ('cancelled','returned')
            GROUP  BY c.customer_id, c.name
        ),
        rfm_scores AS (
            SELECT *,
                CASE
                    WHEN recency_days <= 30  THEN 5
                    WHEN recency_days <= 90  THEN 4
                    WHEN recency_days <= 180 THEN 3
                    WHEN recency_days <= 365 THEN 2
                    ELSE 1
                END AS r_score,
                CASE
                    WHEN frequency >= 10 THEN 5
                    WHEN frequency >= 6  THEN 4
                    WHEN frequency >= 3  THEN 3
                    WHEN frequency >= 2  THEN 2
                    ELSE 1
                END AS f_score,
                CASE
                    WHEN monetary >= 5000 THEN 5
                    WHEN monetary >= 2000 THEN 4
                    WHEN monetary >= 1000 THEN 3
                    WHEN monetary >= 500  THEN 2
                    ELSE 1
                END AS m_score
            FROM rfm_base
        )
        SELECT
            customer_id              AS ID,
            name                     AS Name,
            ROUND(recency_days, 1)   AS Recency_Days,
            frequency                AS Frequency,
            monetary                 AS Monetary,
            r_score                  AS R,
            f_score                  AS F,
            m_score                  AS M,
            (r_score + f_score + m_score) AS RFM_Total,
            CASE
                WHEN (r_score + f_score + m_score) >= 13 THEN '🏆 Champions'
                WHEN (r_score + f_score + m_score) >= 10 THEN '💎 Loyal'
                WHEN (r_score + f_score + m_score) >= 7  THEN '🔄 At Risk'
                ELSE                                          '😴 Churned'
            END                      AS RFM_Segment
        FROM   rfm_scores
        ORDER  BY RFM_Total DESC
        LIMIT  25;
    """
    rows = run_query(conn, sql)
    render_table(rows)


# ─────────────────────────────────────────────
# Report Registry
# ─────────────────────────────────────────────
REPORTS = {
    "revenue"        : ("Total Revenue by Category",           report_revenue),
    "top_customers"  : ("Top Customers by Lifetime Value",     report_top_customers),
    "top_products"   : ("Top Products by Revenue",             report_top_products),
    "monthly_revenue": ("Monthly Revenue with Growth %",       report_monthly_revenue),
    "aov"            : ("Average Order Value by Segment",      report_aov),
    "retention"      : ("Cohort Retention Analysis",           report_retention),
    "segmentation"   : ("Customer Segmentation",               report_segmentation),
    "rfm"            : ("RFM Analysis",                        report_rfm),
}


# ─────────────────────────────────────────────
# Argument parser
# ─────────────────────────────────────────────
def build_parser():
    parser = argparse.ArgumentParser(
        prog="report_cli",
        description="📊 E-Commerce Analytics CLI Reporting Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available reports:
{'':4}{'  '.join(REPORTS.keys())}
{'':4}all   → Run every report

Examples:
  python report_cli.py --report revenue
  python report_cli.py --report top_customers --limit 5
  python report_cli.py --report all
        """,
    )
    parser.add_argument(
        "--report", "-r",
        required=True,
        metavar="REPORT_NAME",
        help=f"Report to run. Choices: {', '.join(list(REPORTS.keys()) + ['all'])}",
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=10,
        metavar="N",
        help="Number of rows to return for top-N reports (default: 10)",
    )
    parser.add_argument(
        "--db",
        default=DB_PATH,
        metavar="PATH",
        help=f"Path to SQLite database (default: {DB_PATH})",
    )
    return parser


# ─────────────────────────────────────────────
# Validate inputs
# ─────────────────────────────────────────────
def validate_args(args, parser):
    valid_choices = list(REPORTS.keys()) + ["all"]
    if args.report not in valid_choices:
        parser.error(
            f"Unknown report '{args.report}'.\n"
            f"  Valid options: {', '.join(valid_choices)}"
        )
    if args.limit < 1 or args.limit > 1000:
        parser.error("--limit must be between 1 and 1000")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    parser = build_parser()
    args   = parser.parse_args()
    validate_args(args, parser)

    global DB_PATH
    DB_PATH = args.db

    print(f"\n{'\u2580' * 60}")
    print(f"  \U0001f6d2  E-Commerce Analytics Report Tool")
    print(f"  \U0001f464  Author : Ashmit Gupta")
    print(f"  \U0001f550  {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}")
    print(f"  \U0001f4c1  DB: {args.db}")
    print(f"{'\u2584' * 60}")

    conn = get_connection()

    try:
        if args.report == "all":
            for key, (title, fn) in REPORTS.items():
                if key in ("top_customers", "top_products"):
                    fn(conn, args.limit)
                else:
                    fn(conn)
        else:
            fn = REPORTS[args.report][1]
            if args.report in ("top_customers", "top_products"):
                fn(conn, args.limit)
            else:
                fn(conn)
    finally:
        conn.close()

    print(f"\n{'─' * 60}")
    print("  ✅  Report complete.")
    print(f"{'─' * 60}\n")


if __name__ == "__main__":
    main()

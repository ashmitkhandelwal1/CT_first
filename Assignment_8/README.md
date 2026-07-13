# 🛒 E-Commerce Analytics System

**Author:** Ashmit Gupta

> An end-to-end data analytics pipeline that processes e-commerce order data using Python and SQL — from realistic dataset generation to business intelligence reporting.

---

## 📁 Project Structure

```
ecommerce-analytics-system/
├── data/
│   ├── raw/                        ← Auto-generated messy CSVs
│   │   ├── customers.csv
│   │   ├── products.csv
│   │   ├── orders.csv
│   │   └── order_items.csv
│   └── cleaned/                    ← Pandas-cleaned output CSVs
│       ├── customers_clean.csv
│       ├── products_clean.csv
│       ├── orders_clean.csv
│       └── order_items_clean.csv
├── scripts/
│   ├── generate_data.py            ← Step 1: Dataset generation
│   ├── clean_data.py               ← Steps 2 & 3: Cleaning + SQLite load
│   └── report_cli.py               ← Steps 8 & 9: CLI reporting tool
├── sql/
│   ├── schema.sql                  ← Step 3: Database DDL
│   ├── aggregations.sql            ← Step 4: JOINs & aggregations
│   ├── window_functions.sql        ← Step 5: Window functions & CTEs
│   └── cohort_analysis.sql         ← Steps 6 & 7: Cohort & segmentation
├── output/
│   └── sample_reports/             ← CLI report output files
├── ecommerce.db                    ← Auto-generated SQLite database
└── README.md
```

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Pipeline                            │
│                                                             │
│  generate_data.py  →  data/raw/*.csv                        │
│        │                                                    │
│        ▼                                                    │
│  clean_data.py     →  data/cleaned/*.csv  →  ecommerce.db   │
│                                                  │          │
│                                                  ▼          │
│  report_cli.py     ←─────────── SQL Queries ────┘          │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.8+ |
| pandas | Latest |
| tabulate | Latest |

Install dependencies:
```bash
pip install pandas tabulate
```

---

## 🚀 How to Run

### Step 1 — Generate Raw Data
```bash
python scripts/generate_data.py
```
Produces `data/raw/*.csv` with **intentional data quality issues**:
- Null / missing values in critical fields
- Duplicate rows
- Orphan foreign keys (mismatched IDs)
- Future dates in `order_date`
- Negative prices and quantities

**Output counts:**
- `customers.csv` → 305 rows (including duplicates)
- `products.csv` → 83 rows
- `orders.csv` → 808 rows
- `order_items.csv` → 2010 rows

---

### Step 2 & 3 — Clean Data + Load into SQLite
```bash
python scripts/clean_data.py
```

**Cleaning operations:**
| Issue | Fix Applied |
|---|---|
| Duplicate rows | Removed exact duplicates |
| NULL primary keys | Rows dropped |
| NULL name / email | Rows dropped |
| Duplicate emails | Keep first occurrence |
| Orphan customer_id in orders | Rows dropped |
| Future order dates | Rows dropped |
| Negative total amounts | Rows dropped |
| ship_date < order_date | Set ship_date = order_date |
| Orphan order_id in order_items | Rows dropped |
| Negative quantity / unit_price | Rows dropped |
| Discount outside [0, 1] | Clipped to [0, 1] |

**Post-cleaning row counts:**
- `customers_clean.csv` → 276 rows
- `products_clean.csv` → 75 rows
- `orders_clean.csv` → 606 rows
- `order_items_clean.csv` → 1244 rows

Also creates **`ecommerce.db`** (SQLite) using the schema in `sql/schema.sql`.

---

### Step 4–7 — SQL Analytics

All SQL files can be run directly against `ecommerce.db` using any SQLite client (e.g. DB Browser for SQLite, DBeaver, or the `sqlite3` CLI):

```bash
sqlite3 ecommerce.db < sql/aggregations.sql
sqlite3 ecommerce.db < sql/window_functions.sql
sqlite3 ecommerce.db < sql/cohort_analysis.sql
```

**`aggregations.sql`** — Step 4 (JOINs & Aggregations):
- Total revenue per customer, category, month
- Top 10 products by quantity sold & revenue
- Average Order Value (AOV) overall, by payment method, by segment
- Revenue share % per category
- Orders & revenue by order status

**`window_functions.sql`** — Step 5 (Window Functions & CTEs):
- Customer LTV ranking with `RANK()` and `DENSE_RANK()`
- Running total revenue over time using `SUM() OVER`
- 3-month moving average with `AVG() OVER`
- Customer order sequence with `ROW_NUMBER() OVER PARTITION BY`
- Customer spend quartiles using `NTILE(4)`
- Month-over-month & quarter-over-quarter growth with `LAG()` CTE
- Cumulative revenue share per category

**`cohort_analysis.sql`** — Steps 6 & 7 (Cohort & Segmentation):
- Cohort definition by first purchase month
- Full cohort × month retention grid
- Period-offset retention (Month 0, 1, 2 … 12)
- Churned vs. repeat customer classification
- Month-1 retention rate per cohort
- Frequency segmentation (One-Time / Occasional / Loyal)
- Spend tier segmentation (Low / Medium / High)
- Combined frequency × spend matrix
- Full RFM scoring (Recency, Frequency, Monetary scores 1–5)
- RFM segment labeling (Champions / Loyal / At Risk / Dormant / Lost)
- RFM segment summary dashboard

---

### Step 8 — CLI Reporting Tool
```bash
python scripts/report_cli.py --report <REPORT_NAME> [--limit N] [--db PATH]
```

**Available reports:**

| Report Name | Description |
|---|---|
| `revenue` | Total revenue & orders per product category |
| `top_customers` | Customers ranked by lifetime value |
| `top_products` | Products ranked by revenue |
| `monthly_revenue` | Monthly revenue with MoM growth % |
| `aov` | Average Order Value by frequency × spend segment |
| `retention` | Cohort-based monthly retention rates |
| `segmentation` | Customer segmentation by frequency & spend |
| `rfm` | RFM analysis with segment labels |
| `all` | Runs every report in sequence |

**Examples:**
```bash
# Revenue by category
python scripts/report_cli.py --report revenue

# Top 5 customers
python scripts/report_cli.py --report top_customers --limit 5

# Monthly revenue trend
python scripts/report_cli.py --report monthly_revenue

# RFM analysis
python scripts/report_cli.py --report rfm

# All reports
python scripts/report_cli.py --report all --limit 10

# Custom database path
python scripts/report_cli.py --report revenue --db /path/to/mydb.db
```

---

## 🔍 Edge Cases Handled

| Edge Case | Handling |
|---|---|
| Database file missing | Clear error message + exit |
| Database connection failure | `sqlite3.Error` caught gracefully |
| Empty result set | ⚠️ "No data returned" message |
| Invalid `--report` argument | `argparse` error with valid choices |
| `--limit` out of range (1–1000) | Validation error with message |
| Future dates in raw data | Filtered during cleaning |
| Negative quantities / prices | Filtered during cleaning |
| Referential integrity violations | Orphan rows dropped |
| Duplicate rows | Exact duplicates removed |
| `tabulate` not installed | Falls back to plain-text table renderer |

---

## 📊 Sample Output

```
════════════════════════════════════════════════════════════
  📊  Total Revenue by Category
════════════════════════════════════════════════════════════
╭──────────────────┬────────┬───────────────┬────────────────╮
│ Category         │ Orders │       Revenue │ Avg_Unit_Price │
├──────────────────┼────────┼───────────────┼────────────────┤
│ Electronics      │    152 │    987,432.81 │         854.32 │
│ Clothing         │    134 │    654,219.47 │         312.55 │
│ Home & Kitchen   │     98 │    521,083.22 │         489.10 │
│ Books            │     87 │    198,432.15 │          89.44 │
╰──────────────────┴────────┴───────────────┴────────────────╯
```

Sample report output is saved to `output/sample_reports/all_reports.txt`.

---

## 🗄️ Database Schema

```
customers                 products
──────────                ──────────
customer_id PK            product_id  PK
name                      name
email UNIQUE              category
phone                     price
city                      stock_qty
country                   supplier_id
signup_date               created_at
age
gender                    order_items
loyalty_points            ──────────────
      │                   item_id     PK
      │  orders           order_id    FK→ orders
      │  ──────────       product_id  FK→ products
      └─ order_id  PK     quantity
         customer_id FK   unit_price
         order_date        discount
         ship_date
         status
         total_amount
         payment_method
         shipping_city
```

---

## 🧪 Running Edge Case Tests

```bash
# Test: invalid report name
python scripts/report_cli.py --report invalid_report

# Test: limit out of bounds
python scripts/report_cli.py --report revenue --limit 0

# Test: wrong DB path
python scripts/report_cli.py --report revenue --db nonexistent.db
```

---

## 📝 Notes

- The project uses **SQLite** for portability — no server setup required.
- All SQL in `sql/` is standard SQL-92 / SQLite-compatible.
- The CLI tool requires only Python standard library + `pandas` + `tabulate`.
- Re-running `generate_data.py` and `clean_data.py` will regenerate all data from scratch.

---

## 👤 Author

| Field | Details |
|---|---|
| **Name** | Ashmit Gupta |
| **Project** | E-Commerce Analytics System |
| **Assignment** | Assignment 8 — End-to-End Data Analytics |

---

*Built by **Ashmit Gupta** — E-Commerce Analytics System*

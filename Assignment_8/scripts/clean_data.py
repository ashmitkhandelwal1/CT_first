"""
clean_data.py
-------------
Author : Ashmit Gupta
Project: E-Commerce Analytics System (Assignment 8)

Steps 2 & 3: Clean the raw CSVs using Pandas, then load into SQLite.

Cleaning operations performed:
  ✓ Remove fully duplicate rows
  ✓ Drop rows with critical NULL values (PKs, FKs)
  ✓ Standardise data types (dates, numerics)
  ✓ Remove rows with invalid prices / quantities (negatives)
  ✓ Validate referential integrity (foreign key consistency)
  ✓ De-duplicate emails in customers
  ✓ Export cleaned CSVs
  ✓ Create SQLite schema and load all cleaned data

Output:
  data/cleaned/*.csv
  ecommerce.db  (SQLite database in project root)
"""

import os
import sys
import sqlite3
import pandas as pd

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────
BASE_DIR     = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DIR      = os.path.join(BASE_DIR, "data", "raw")
CLEANED_DIR  = os.path.join(BASE_DIR, "data", "cleaned")
DB_PATH      = os.path.join(BASE_DIR, "ecommerce.db")
SCHEMA_PATH  = os.path.join(BASE_DIR, "sql", "schema.sql")

os.makedirs(CLEANED_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# Logging helpers
# ─────────────────────────────────────────────
def section(title):
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}")


def log(msg):
    print(f"  {msg}")


# ─────────────────────────────────────────────
# Load raw data
# ─────────────────────────────────────────────
def load_raw():
    section("Loading raw CSVs")
    dfs = {}
    for name in ["customers", "products", "orders", "order_items"]:
        path = os.path.join(RAW_DIR, f"{name}.csv")
        if not os.path.exists(path):
            print(f"\n❌  File not found: {path}")
            print("    Please run generate_data.py first.")
            sys.exit(1)
        dfs[name] = pd.read_csv(path, dtype=str)   # load everything as str first
        log(f"Loaded {name}.csv → {len(dfs[name])} rows")
    return dfs


# ─────────────────────────────────────────────
# Generic helpers
# ─────────────────────────────────────────────
def report_nulls(df, label):
    null_counts = df.isnull().sum()
    null_counts = null_counts[null_counts > 0]
    if not null_counts.empty:
        log(f"  Null counts in {label}:")
        for col, cnt in null_counts.items():
            log(f"    {col}: {cnt}")


def drop_duplicates_report(df, label, subset=None):
    before = len(df)
    df = df.drop_duplicates(subset=subset)
    after  = len(df)
    log(f"Duplicates removed from {label}: {before - after}")
    return df


# ─────────────────────────────────────────────
# Clean customers
# ─────────────────────────────────────────────
def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    section("Cleaning customers")
    log(f"Raw rows: {len(df)}")

    # Remove fully duplicate rows
    df = drop_duplicates_report(df, "customers")

    # Convert types
    df["customer_id"]    = pd.to_numeric(df["customer_id"], errors="coerce")
    df["age"]            = pd.to_numeric(df["age"],         errors="coerce")
    df["loyalty_points"] = pd.to_numeric(df["loyalty_points"], errors="coerce")
    df["signup_date"]    = pd.to_datetime(df["signup_date"], errors="coerce")

    # Drop rows with missing primary key
    before = len(df)
    df = df.dropna(subset=["customer_id"])
    log(f"Dropped {before - len(df)} rows with NULL customer_id")

    # Cast PK to int
    df["customer_id"] = df["customer_id"].astype(int)

    # Drop missing name or email (critical fields)
    before = len(df)
    df = df.dropna(subset=["name", "email"])
    log(f"Dropped {before - len(df)} rows with NULL name/email")

    # Remove duplicate emails (keep first occurrence)
    before = len(df)
    df = df.drop_duplicates(subset=["email"], keep="first")
    log(f"Removed {before - len(df)} duplicate emails")

    # Age sanity check (18–100)
    before = len(df)
    df = df[df["age"].isna() | df["age"].between(18, 100)]
    log(f"Removed {before - len(df)} rows with invalid age")

    # Fill remaining nulls with sensible defaults
    df["loyalty_points"] = df["loyalty_points"].fillna(0).astype(int)
    df["gender"]         = df["gender"].fillna("Unknown")
    df["city"]           = df["city"].fillna("Unknown")
    df["country"]        = df["country"].fillna("Unknown")

    # Standardise signup_date
    df["signup_date"]    = df["signup_date"].dt.date.astype(str)
    df.loc[df["signup_date"] == "NaT", "signup_date"] = None

    df = df.reset_index(drop=True)
    log(f"Clean rows: {len(df)}")
    return df


# ─────────────────────────────────────────────
# Clean products
# ─────────────────────────────────────────────
def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    section("Cleaning products")
    log(f"Raw rows: {len(df)}")

    df = drop_duplicates_report(df, "products")

    df["product_id"]  = pd.to_numeric(df["product_id"],  errors="coerce")
    df["price"]       = pd.to_numeric(df["price"],        errors="coerce")
    df["stock_qty"]   = pd.to_numeric(df["stock_qty"],    errors="coerce")
    df["supplier_id"] = pd.to_numeric(df["supplier_id"],  errors="coerce")
    df["created_at"]  = pd.to_datetime(df["created_at"],  errors="coerce")

    # Drop NULL PK
    before = len(df)
    df = df.dropna(subset=["product_id"])
    log(f"Dropped {before - len(df)} rows with NULL product_id")
    df["product_id"] = df["product_id"].astype(int)

    # Drop NULL name
    before = len(df)
    df = df.dropna(subset=["name"])
    log(f"Dropped {before - len(df)} rows with NULL name")

    # Remove negative or zero prices
    before = len(df)
    df = df[df["price"].isna() | (df["price"] > 0)]
    log(f"Removed {before - len(df)} rows with invalid price (≤0)")

    # Fill defaults
    df["price"]     = df["price"].fillna(df["price"].median())
    df["stock_qty"] = df["stock_qty"].fillna(0).astype(int)
    df["category"]  = df["category"].fillna("Uncategorised")
    df["created_at"]= df["created_at"].dt.date.astype(str)
    df.loc[df["created_at"] == "NaT", "created_at"] = None

    df = df.reset_index(drop=True)
    log(f"Clean rows: {len(df)}")
    return df


# ─────────────────────────────────────────────
# Clean orders
# ─────────────────────────────────────────────
def clean_orders(df: pd.DataFrame, valid_customer_ids: set) -> pd.DataFrame:
    section("Cleaning orders")
    log(f"Raw rows: {len(df)}")

    df = drop_duplicates_report(df, "orders")

    df["order_id"]     = pd.to_numeric(df["order_id"],     errors="coerce")
    df["customer_id"]  = pd.to_numeric(df["customer_id"],  errors="coerce")
    df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce")
    df["order_date"]   = pd.to_datetime(df["order_date"],  errors="coerce")
    df["ship_date"]    = pd.to_datetime(df["ship_date"],   errors="coerce")

    # Drop NULL PK
    before = len(df)
    df = df.dropna(subset=["order_id"])
    log(f"Dropped {before - len(df)} rows with NULL order_id")
    df["order_id"] = df["order_id"].astype(int)

    # Drop NULL / orphan customer_id
    before = len(df)
    df = df.dropna(subset=["customer_id"])
    df["customer_id"] = df["customer_id"].astype(int)
    df = df[df["customer_id"].isin(valid_customer_ids)]
    log(f"Removed {before - len(df)} rows with NULL/orphan customer_id")

    # Drop NULL order_date
    before = len(df)
    df = df.dropna(subset=["order_date"])
    log(f"Dropped {before - len(df)} rows with NULL order_date")

    # Remove future dates
    today  = pd.Timestamp.today()
    before = len(df)
    df = df[df["order_date"] <= today]
    log(f"Removed {before - len(df)} rows with future order_date")

    # Remove negative total_amount
    before = len(df)
    df = df[df["total_amount"].isna() | (df["total_amount"] >= 0)]
    log(f"Removed {before - len(df)} rows with negative total_amount")

    # Ensure ship_date >= order_date
    mask = df["ship_date"].notna() & (df["ship_date"] < df["order_date"])
    log(f"Fixed {mask.sum()} ship_date < order_date (set to order_date)")
    df.loc[mask, "ship_date"] = df.loc[mask, "order_date"]

    # Fill defaults
    df["status"]         = df["status"].fillna("unknown")
    df["payment_method"] = df["payment_method"].fillna("unknown")
    df["shipping_city"]  = df["shipping_city"].fillna("Unknown")
    df["total_amount"]   = df["total_amount"].fillna(0.0)

    df["order_date"] = df["order_date"].dt.date.astype(str)
    df["ship_date"]  = df["ship_date"].dt.date.astype(str)

    df = df.reset_index(drop=True)
    log(f"Clean rows: {len(df)}")
    return df


# ─────────────────────────────────────────────
# Clean order_items
# ─────────────────────────────────────────────
def clean_order_items(df: pd.DataFrame,
                      valid_order_ids: set,
                      valid_product_ids: set) -> pd.DataFrame:
    section("Cleaning order_items")
    log(f"Raw rows: {len(df)}")

    df = drop_duplicates_report(df, "order_items")

    df["item_id"]    = pd.to_numeric(df["item_id"],    errors="coerce")
    df["order_id"]   = pd.to_numeric(df["order_id"],   errors="coerce")
    df["product_id"] = pd.to_numeric(df["product_id"], errors="coerce")
    df["quantity"]   = pd.to_numeric(df["quantity"],   errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["discount"]   = pd.to_numeric(df["discount"],   errors="coerce")

    # Drop NULL PKs
    before = len(df)
    df = df.dropna(subset=["item_id"])
    df["item_id"] = df["item_id"].astype(int)
    log(f"Dropped {before - len(df)} rows with NULL item_id")

    # Drop orphan order_ids
    before = len(df)
    df = df.dropna(subset=["order_id"])
    df["order_id"] = df["order_id"].astype(int)
    df = df[df["order_id"].isin(valid_order_ids)]
    log(f"Removed {before - len(df)} rows with NULL/orphan order_id")

    # Drop orphan product_ids
    before = len(df)
    df = df.dropna(subset=["product_id"])
    df["product_id"] = df["product_id"].astype(int)
    df = df[df["product_id"].isin(valid_product_ids)]
    log(f"Removed {before - len(df)} rows with NULL/orphan product_id")

    # Remove negative / zero quantity
    before = len(df)
    df = df[df["quantity"].isna() | (df["quantity"] > 0)]
    log(f"Removed {before - len(df)} rows with invalid quantity (≤0)")

    # Remove negative unit_price
    before = len(df)
    df = df[df["unit_price"].isna() | (df["unit_price"] > 0)]
    log(f"Removed {before - len(df)} rows with invalid unit_price (≤0)")

    # Discount must be [0, 1]
    df["discount"] = df["discount"].clip(0, 1).fillna(0.0)

    # Fill remaining nulls
    df["quantity"]   = df["quantity"].fillna(1).astype(int)
    df["unit_price"] = df["unit_price"].fillna(df["unit_price"].median())

    df = df.reset_index(drop=True)
    log(f"Clean rows: {len(df)}")
    return df


# ─────────────────────────────────────────────
# Export cleaned CSVs
# ─────────────────────────────────────────────
def export_clean(df: pd.DataFrame, name: str):
    path = os.path.join(CLEANED_DIR, f"{name}_clean.csv")
    df.to_csv(path, index=False)
    log(f"Exported → {path}")


# ─────────────────────────────────────────────
# SQLite: schema + load
# ─────────────────────────────────────────────
def create_schema(conn: sqlite3.Connection):
    if os.path.exists(SCHEMA_PATH):
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        log("Schema applied from schema.sql")
    else:
        # Inline fallback schema
        conn.executescript("""
            DROP TABLE IF EXISTS order_items;
            DROP TABLE IF EXISTS orders;
            DROP TABLE IF EXISTS products;
            DROP TABLE IF EXISTS customers;

            CREATE TABLE customers (
                customer_id    INTEGER PRIMARY KEY,
                name           TEXT    NOT NULL,
                email          TEXT    NOT NULL UNIQUE,
                phone          TEXT,
                city           TEXT,
                country        TEXT,
                signup_date    TEXT,
                age            REAL,
                gender         TEXT,
                loyalty_points INTEGER DEFAULT 0
            );

            CREATE TABLE products (
                product_id  INTEGER PRIMARY KEY,
                name        TEXT    NOT NULL,
                category    TEXT,
                price       REAL    NOT NULL,
                stock_qty   INTEGER DEFAULT 0,
                supplier_id INTEGER,
                created_at  TEXT
            );

            CREATE TABLE orders (
                order_id       INTEGER PRIMARY KEY,
                customer_id    INTEGER NOT NULL REFERENCES customers(customer_id),
                order_date     TEXT    NOT NULL,
                ship_date      TEXT,
                status         TEXT,
                total_amount   REAL    DEFAULT 0,
                payment_method TEXT,
                shipping_city  TEXT
            );

            CREATE TABLE order_items (
                item_id    INTEGER PRIMARY KEY,
                order_id   INTEGER NOT NULL REFERENCES orders(order_id),
                product_id INTEGER NOT NULL REFERENCES products(product_id),
                quantity   INTEGER NOT NULL DEFAULT 1,
                unit_price REAL    NOT NULL,
                discount   REAL    DEFAULT 0
            );
        """)
        log("Schema applied from inline fallback")


def load_to_sqlite(dfs: dict):
    section("Loading cleaned data into SQLite")
    log(f"Database: {DB_PATH}")

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        log("Removed existing database")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF;")

    create_schema(conn)

    # Load in dependency order
    order = ["customers", "products", "orders", "order_items"]
    for name in order:
        df = dfs[name]
        df.to_sql(name, conn, if_exists="append", index=False)
        count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        log(f"Loaded {name}: {count} rows")

    conn.execute("PRAGMA foreign_keys = ON;")
    conn.commit()
    conn.close()
    log("SQLite database ready ✅")


# ─────────────────────────────────────────────
# Verify
# ─────────────────────────────────────────────
def verify_db():
    section("Verification")
    conn = sqlite3.connect(DB_PATH)
    tables = ["customers", "products", "orders", "order_items"]
    for t in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        log(f"  {t}: {count} rows")
    conn.close()


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  E-Commerce Data Cleaner & Loader")
    print("=" * 55)

    raw = load_raw()

    # ── Step 2: Clean ──
    customers   = clean_customers(raw["customers"])
    products    = clean_products(raw["products"])

    valid_cids  = set(customers["customer_id"].tolist())
    orders      = clean_orders(raw["orders"], valid_cids)

    valid_oids  = set(orders["order_id"].tolist())
    valid_pids  = set(products["product_id"].tolist())
    order_items = clean_order_items(raw["order_items"], valid_oids, valid_pids)

    # ── Export cleaned CSVs ──
    section("Exporting cleaned CSVs")
    export_clean(customers,   "customers")
    export_clean(products,    "products")
    export_clean(orders,      "orders")
    export_clean(order_items, "order_items")

    # ── Step 3: Load into SQLite ──
    dfs = {
        "customers"  : customers,
        "products"   : products,
        "orders"     : orders,
        "order_items": order_items,
    }
    load_to_sqlite(dfs)
    verify_db()

    print(f"\n✅  Pipeline complete! DB saved to: {DB_PATH}")


if __name__ == "__main__":
    main()

"""
generate_data.py
----------------
Author : Ashmit Gupta
Project: E-Commerce Analytics System (Assignment 8)

Step 1: Generate realistic (but intentionally messy) e-commerce datasets.

Generates four CSV files with intentional inconsistencies:
  - Null / missing values
  - Duplicate rows
  - Mismatched / orphan foreign keys
  - Invalid / future dates
  - Negative prices / quantities

Output files (data/raw/):
  customers.csv | products.csv | orders.csv | order_items.csv
"""

import os
import random
import csv
import string
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
SEED = 42
random.seed(SEED)

NUM_CUSTOMERS   = 300
NUM_PRODUCTS    = 80
NUM_ORDERS      = 800
NUM_ORDER_ITEMS = 2000

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# Helper utilities
# ─────────────────────────────────────────────
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael",
    "Linda", "William", "Barbara", "David", "Elizabeth", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen", "Priya",
    "Rahul", "Ananya", "Vikram", "Sneha", "Arjun", "Divya", "Ravi",
    "Neha", "Amit", "Pooja", "Suresh", "Kavya", "Manish", "Deepa",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson",
    "Sharma", "Verma", "Singh", "Gupta", "Patel", "Kumar", "Reddy",
    "Nair", "Pillai", "Mehta", "Joshi", "Iyer", "Rao", "Das", "Bose",
]
DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "example.com"]
CITIES  = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata",
           "Pune", "Ahmedabad", "Jaipur", "Surat", "New York", "London", "Toronto"]
COUNTRIES = ["India", "USA", "UK", "Canada", "Australia"]
CATEGORIES = ["Electronics", "Clothing", "Books", "Home & Kitchen",
               "Sports", "Toys", "Beauty", "Automotive", "Grocery"]
PRODUCT_ADJECTIVES = ["Premium", "Budget", "Pro", "Lite", "Ultra", "Classic", "Smart", "Eco"]
PRODUCT_NOUNS      = ["Laptop", "Shirt", "Novel", "Blender", "Shoes", "Watch", "Camera",
                      "Headphones", "Desk", "Chair", "Bag", "Gloves", "Jacket", "Charger",
                      "Keyboard", "Monitor", "Mouse", "Tablet", "Phone", "Speaker"]


def rand_str(n=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))


def rand_date(start_year=2022, end_year=2025):
    start = datetime(start_year, 1, 1)
    end   = datetime(end_year, 12, 31)
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def maybe_null(value, prob=0.06):
    """Return None with probability `prob`, else value."""
    return None if random.random() < prob else value


def fmt(v):
    """Format value for CSV (None → empty string)."""
    return "" if v is None else str(v)


def fmt_date(d):
    return "" if d is None else d.strftime("%Y-%m-%d")


# ─────────────────────────────────────────────
# 1. Customers
# ─────────────────────────────────────────────
def generate_customers():
    print("Generating customers …")
    customers = []
    used_emails = set()

    for i in range(1, NUM_CUSTOMERS + 1):
        first = random.choice(FIRST_NAMES)
        last  = random.choice(LAST_NAMES)
        name  = f"{first} {last}"
        email = f"{first.lower()}.{last.lower()}{random.randint(1,999)}@{random.choice(DOMAINS)}"

        # intentional: occasionally duplicate email
        if random.random() < 0.04 and used_emails:
            email = random.choice(list(used_emails))
        used_emails.add(email)

        phone = f"+91-{random.randint(7000000000, 9999999999)}"

        row = {
            "customer_id"   : i,
            "name"          : maybe_null(name, 0.03),
            "email"         : maybe_null(email, 0.04),
            "phone"         : maybe_null(phone, 0.07),
            "city"          : maybe_null(random.choice(CITIES), 0.05),
            "country"       : maybe_null(random.choice(COUNTRIES), 0.03),
            "signup_date"   : maybe_null(rand_date(2020, 2024), 0.04),
            "age"           : maybe_null(random.randint(18, 70), 0.06),
            "gender"        : maybe_null(random.choice(["M", "F", "Other", None]), 0.08),
            "loyalty_points": maybe_null(random.randint(0, 5000), 0.05),
        }
        customers.append(row)

    # intentional: add ~5 duplicate rows
    for _ in range(5):
        dup = random.choice(customers).copy()
        customers.append(dup)

    random.shuffle(customers)
    return customers


# ─────────────────────────────────────────────
# 2. Products
# ─────────────────────────────────────────────
def generate_products():
    print("Generating products …")
    products = []

    for i in range(1, NUM_PRODUCTS + 1):
        name  = f"{random.choice(PRODUCT_ADJECTIVES)} {random.choice(PRODUCT_NOUNS)}"
        price = round(random.uniform(5.0, 2000.0), 2)

        # intentional: some negative prices
        if random.random() < 0.04:
            price = -abs(price)

        row = {
            "product_id"  : i,
            "name"        : maybe_null(name, 0.02),
            "category"    : maybe_null(random.choice(CATEGORIES), 0.05),
            "price"       : maybe_null(price, 0.04),
            "stock_qty"   : maybe_null(random.randint(0, 500), 0.05),
            "supplier_id" : maybe_null(random.randint(1, 20), 0.08),
            "created_at"  : maybe_null(rand_date(2019, 2023), 0.03),
        }
        products.append(row)

    # intentional: duplicate products
    for _ in range(3):
        dup = random.choice(products).copy()
        products.append(dup)

    return products


# ─────────────────────────────────────────────
# 3. Orders
# ─────────────────────────────────────────────
def generate_orders(customer_ids):
    print("Generating orders …")
    orders = []
    valid_statuses = ["pending", "shipped", "delivered", "cancelled", "returned"]

    for i in range(1, NUM_ORDERS + 1):
        cust_id     = random.choice(customer_ids)
        order_date  = rand_date(2022, 2025)

        # intentional: some future dates
        if random.random() < 0.03:
            order_date = datetime.now() + timedelta(days=random.randint(1, 180))

        # intentional: some orphan customer IDs
        if random.random() < 0.04:
            cust_id = random.randint(9000, 9999)

        ship_date   = order_date + timedelta(days=random.randint(1, 10))
        total_amt   = round(random.uniform(10.0, 5000.0), 2)

        # intentional: some negative totals
        if random.random() < 0.03:
            total_amt = -abs(total_amt)

        row = {
            "order_id"       : i,
            "customer_id"    : maybe_null(cust_id, 0.04),
            "order_date"     : maybe_null(fmt_date(order_date), 0.03),
            "ship_date"      : maybe_null(fmt_date(ship_date), 0.06),
            "status"         : maybe_null(random.choice(valid_statuses), 0.05),
            "total_amount"   : maybe_null(total_amt, 0.04),
            "payment_method" : maybe_null(random.choice(["credit_card","debit_card","upi","cash","wallet"]), 0.06),
            "shipping_city"  : maybe_null(random.choice(CITIES), 0.07),
        }
        orders.append(row)

    # intentional: duplicate orders
    for _ in range(8):
        dup = random.choice(orders).copy()
        orders.append(dup)

    return orders


# ─────────────────────────────────────────────
# 4. Order Items
# ─────────────────────────────────────────────
def generate_order_items(order_ids, product_ids):
    print("Generating order_items …")
    items = []

    for i in range(1, NUM_ORDER_ITEMS + 1):
        order_id   = random.choice(order_ids)
        product_id = random.choice(product_ids)

        # intentional: orphan order IDs
        if random.random() < 0.04:
            order_id = random.randint(9000, 9999)

        # intentional: orphan product IDs
        if random.random() < 0.03:
            product_id = random.randint(9000, 9999)

        qty         = random.randint(1, 10)
        unit_price  = round(random.uniform(5.0, 2000.0), 2)
        discount    = round(random.uniform(0, 0.4), 2)

        # intentional: negative quantity
        if random.random() < 0.03:
            qty = -qty

        row = {
            "item_id"   : i,
            "order_id"  : maybe_null(order_id, 0.02),
            "product_id": maybe_null(product_id, 0.03),
            "quantity"  : maybe_null(qty, 0.04),
            "unit_price": maybe_null(unit_price, 0.04),
            "discount"  : maybe_null(discount, 0.06),
        }
        items.append(row)

    # intentional: duplicate items
    for _ in range(10):
        dup = random.choice(items).copy()
        items.append(dup)

    return items


# ─────────────────────────────────────────────
# Write CSVs
# ─────────────────────────────────────────────
def write_csv(filename, rows, fieldnames):
    path = os.path.join(RAW_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: fmt(v) for k, v in row.items()})
    print(f"  -> Written {len(rows)} rows to {path}")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  E-Commerce Data Generator")
    print("=" * 55)

    customers = generate_customers()
    products  = generate_products()

    # Extract clean IDs for reference (before intentional corruption)
    customer_ids = list(range(1, NUM_CUSTOMERS + 1))
    product_ids  = list(range(1, NUM_PRODUCTS  + 1))
    order_ids    = list(range(1, NUM_ORDERS    + 1))

    orders      = generate_orders(customer_ids)
    order_items = generate_order_items(order_ids, product_ids)

    write_csv("customers.csv",   customers,
              ["customer_id","name","email","phone","city","country",
               "signup_date","age","gender","loyalty_points"])

    write_csv("products.csv",    products,
              ["product_id","name","category","price","stock_qty",
               "supplier_id","created_at"])

    write_csv("orders.csv",      orders,
              ["order_id","customer_id","order_date","ship_date",
               "status","total_amount","payment_method","shipping_city"])

    write_csv("order_items.csv", order_items,
              ["item_id","order_id","product_id","quantity",
               "unit_price","discount"])

    print("\n✅  Raw data generation complete!")
    print(f"    Files saved to: {os.path.abspath(RAW_DIR)}")


if __name__ == "__main__":
    main()

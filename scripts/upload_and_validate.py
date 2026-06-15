"""
=============================================================================
Assignment 4 - Azure Data Pipeline: Data Validation & Upload Script
Author: Ashmit Gupta
Dataset: Sample - Superstore.csv
Description: Validates the Superstore dataset and uploads it to Azure Blob Storage
=============================================================================
"""

import os
import sys
import csv
import json
import hashlib
from datetime import datetime

# -------------------------------------------------------------------
# Try to import Azure SDK; gracefully degrade if not installed
# -------------------------------------------------------------------
try:
    from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False
    print("[WARNING] azure-storage-blob not installed.")
    print("          Install with: pip install azure-storage-blob")
    print("          Running in LOCAL VALIDATION ONLY mode.\n")


# ==================== CONFIGURATION ====================
STORAGE_ACCOUNT_NAME   = "stashmitsuperstore01"
STORAGE_ACCOUNT_KEY    = "<YOUR_STORAGE_ACCOUNT_KEY>"   # Replace with actual key
SOURCE_CONTAINER       = "source-data"
DESTINATION_CONTAINER  = "destination-data"
LOCAL_CSV_PATH         = r"Sample - Superstore.csv"
BLOB_NAME              = "Sample - Superstore.csv"

EXPECTED_COLUMNS = [
    "Row ID", "Order ID", "Order Date", "Ship Date", "Ship Mode",
    "Customer ID", "Customer Name", "Segment", "Country", "City",
    "State", "Postal Code", "Region", "Product ID", "Category",
    "Sub-Category", "Product Name", "Sales", "Quantity", "Discount", "Profit"
]
EXPECTED_COLUMN_COUNT  = 21
MIN_EXPECTED_ROWS      = 9000   # at least 9000 data rows
# =======================================================


def print_banner():
    """Print assignment banner."""
    print("=" * 65)
    print("  Assignment 4 – Azure Data Pipeline")
    print("  Author  : Ashmit Gupta")
    print("  Dataset : Sample - Superstore.csv")
    print(f"  Run At  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)
    print()


# ---------------------------------------------------------------
# STEP 1: Local Data Validation
# ---------------------------------------------------------------
def validate_csv(filepath: str) -> dict:
    """
    Validates the CSV file for:
    - File existence
    - Correct column headers
    - Minimum row count
    - Null / missing value check
    - Numeric column sanity (Sales, Profit, Quantity, Discount)
    Returns a validation report dictionary.
    """
    print("[STEP 1] Running local data validation...")
    report = {
        "file": filepath,
        "timestamp": datetime.now().isoformat(),
        "author": "Ashmit Gupta",
        "checks": {}
    }

    # -- Check 1: File exists --
    if not os.path.isfile(filepath):
        report["checks"]["file_exists"] = {"passed": False, "message": f"File not found: {filepath}"}
        report["overall"] = "FAILED"
        return report
    report["checks"]["file_exists"] = {"passed": True, "message": "File found."}

    # -- Check 2: File size --
    file_size_bytes = os.path.getsize(filepath)
    file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
    report["checks"]["file_size"] = {
        "passed": file_size_bytes > 0,
        "message": f"File size: {file_size_mb} MB ({file_size_bytes:,} bytes)"
    }

    # -- Compute MD5 checksum --
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    report["file_md5"] = md5.hexdigest()

    # -- Read CSV --
    rows = []
    null_cells = 0
    numeric_errors = 0
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        actual_cols = reader.fieldnames or []

        # -- Check 3: Columns --
        cols_match = actual_cols == EXPECTED_COLUMNS
        report["checks"]["column_headers"] = {
            "passed": cols_match,
            "message": f"Columns: {len(actual_cols)} found, {EXPECTED_COLUMN_COUNT} expected.",
            "actual_columns": actual_cols
        }
        if not cols_match:
            missing = [c for c in EXPECTED_COLUMNS if c not in actual_cols]
            extra   = [c for c in actual_cols if c not in EXPECTED_COLUMNS]
            report["checks"]["column_headers"]["missing_columns"] = missing
            report["checks"]["column_headers"]["extra_columns"]   = extra

        for row in reader:
            rows.append(row)
            # Null check
            for col in EXPECTED_COLUMNS:
                if col in row and (row[col] is None or str(row[col]).strip() == ""):
                    null_cells += 1
            # Numeric sanity
            for num_col in ["Sales", "Profit", "Quantity", "Discount"]:
                try:
                    val = float(row.get(num_col, "0") or "0")
                    if num_col == "Quantity" and val <= 0:
                        numeric_errors += 1
                except (ValueError, TypeError):
                    numeric_errors += 1

    total_rows = len(rows)

    # -- Check 4: Row count --
    report["checks"]["row_count"] = {
        "passed": total_rows >= MIN_EXPECTED_ROWS,
        "message": f"Total data rows: {total_rows:,} (min expected: {MIN_EXPECTED_ROWS:,})"
    }

    # -- Check 5: Null values --
    report["checks"]["null_values"] = {
        "passed": null_cells == 0,
        "message": f"Null/empty cells found: {null_cells}"
    }

    # -- Check 6: Numeric integrity --
    report["checks"]["numeric_integrity"] = {
        "passed": numeric_errors == 0,
        "message": f"Numeric errors in Sales/Profit/Quantity/Discount: {numeric_errors}"
    }

    # -- Summary statistics --
    sales_vals  = []
    profit_vals = []
    for row in rows:
        try: sales_vals.append(float(row.get("Sales", 0) or 0))
        except: pass
        try: profit_vals.append(float(row.get("Profit", 0) or 0))
        except: pass

    if sales_vals:
        report["summary_stats"] = {
            "total_rows": total_rows,
            "total_sales": round(sum(sales_vals), 2),
            "avg_sales": round(sum(sales_vals) / len(sales_vals), 2),
            "max_sales": round(max(sales_vals), 2),
            "min_sales": round(min(sales_vals), 2),
            "total_profit": round(sum(profit_vals), 2),
            "avg_profit": round(sum(profit_vals) / len(profit_vals), 2),
        }

    # -- Overall result --
    all_passed = all(v.get("passed", False) for v in report["checks"].values())
    report["overall"] = "PASSED" if all_passed else "FAILED"
    return report


def print_validation_report(report: dict):
    """Pretty-print validation report."""
    print(f"\n{'─'*55}")
    print(f"  VALIDATION REPORT — {report['timestamp'][:19]}")
    print(f"{'─'*55}")
    status_icon = "✅" if report["overall"] == "PASSED" else "❌"
    print(f"  Overall: {status_icon}  {report['overall']}")
    print(f"  File   : {report['file']}")
    print(f"  MD5    : {report.get('file_md5', 'N/A')}")
    print()
    for check_name, result in report.get("checks", {}).items():
        icon = "✅" if result.get("passed") else "❌"
        print(f"  {icon} [{check_name}] {result.get('message', '')}")
    if "summary_stats" in report:
        s = report["summary_stats"]
        print(f"\n  {'─'*50}")
        print(f"  📊 DATASET SUMMARY STATISTICS")
        print(f"  {'─'*50}")
        print(f"  Total Rows    : {s['total_rows']:,}")
        print(f"  Total Sales   : ${s['total_sales']:,.2f}")
        print(f"  Avg Sales     : ${s['avg_sales']:,.2f}")
        print(f"  Max Sales     : ${s['max_sales']:,.2f}")
        print(f"  Total Profit  : ${s['total_profit']:,.2f}")
        print(f"  Avg Profit    : ${s['avg_profit']:,.2f}")
    print(f"{'─'*55}\n")


# ---------------------------------------------------------------
# STEP 2: Upload to Azure Blob Storage
# ---------------------------------------------------------------
def upload_to_blob(local_path: str, container: str, blob_name: str) -> bool:
    """Upload a local file to Azure Blob Storage."""
    if not AZURE_SDK_AVAILABLE:
        print(f"[SKIP] Azure SDK not available. Cannot upload '{blob_name}'.")
        return False

    print(f"[STEP 2] Uploading '{blob_name}' to container '{container}'...")
    try:
        conn_str = (
            f"DefaultEndpointsProtocol=https;"
            f"AccountName={STORAGE_ACCOUNT_NAME};"
            f"AccountKey={STORAGE_ACCOUNT_KEY};"
            f"EndpointSuffix=core.windows.net"
        )
        blob_service_client = BlobServiceClient.from_connection_string(conn_str)
        blob_client = blob_service_client.get_blob_client(
            container=container, blob=blob_name
        )
        with open(local_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        print(f"  ✅ Successfully uploaded '{blob_name}' to container '{container}'.")
        print(f"  URL: https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{container}/{blob_name}")
        return True
    except Exception as e:
        print(f"  ❌ Upload failed: {e}")
        return False


# ---------------------------------------------------------------
# STEP 3: List blobs in a container
# ---------------------------------------------------------------
def list_blobs(container: str):
    """List all blobs in the specified container."""
    if not AZURE_SDK_AVAILABLE:
        print(f"[SKIP] Azure SDK not available. Cannot list blobs in '{container}'.")
        return

    print(f"\n[STEP 3] Listing blobs in container '{container}'...")
    try:
        conn_str = (
            f"DefaultEndpointsProtocol=https;"
            f"AccountName={STORAGE_ACCOUNT_NAME};"
            f"AccountKey={STORAGE_ACCOUNT_KEY};"
            f"EndpointSuffix=core.windows.net"
        )
        blob_service_client = BlobServiceClient.from_connection_string(conn_str)
        container_client = blob_service_client.get_container_client(container)
        blobs = list(container_client.list_blobs())
        if not blobs:
            print(f"  ℹ️  Container '{container}' is empty.")
        for blob in blobs:
            size_kb = round(blob.size / 1024, 2)
            print(f"  📄 {blob.name}  ({size_kb} KB)  Modified: {blob.last_modified}")
    except Exception as e:
        print(f"  ❌ Error listing blobs: {e}")


# ---------------------------------------------------------------
# STEP 4: Save validation report as JSON
# ---------------------------------------------------------------
def save_report(report: dict, output_path: str = "validation_report.json"):
    """Save validation report to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"[STEP 4] Validation report saved to '{output_path}'")


# ---------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------
def main():
    print_banner()

    # Step 1: Validate CSV
    report = validate_csv(LOCAL_CSV_PATH)
    print_validation_report(report)

    if report["overall"] == "FAILED":
        print("❌ Validation failed. Please fix data issues before uploading.")
        sys.exit(1)

    # Step 2: Upload to Source Blob Container
    upload_success = upload_to_blob(LOCAL_CSV_PATH, SOURCE_CONTAINER, BLOB_NAME)

    # Step 3: List blobs
    if upload_success:
        list_blobs(SOURCE_CONTAINER)

    # Step 4: Save report
    save_report(report, "validation_report.json")

    print("\n" + "=" * 65)
    print("  ✅ All steps completed successfully!")
    print("  Next: Trigger the ADF pipeline 'PL_Superstore_BlobToBlob'")
    print("        via Azure Data Factory → Author → Pipelines → Debug/Trigger")
    print("  Author: Ashmit Gupta | Assignment-4")
    print("=" * 65)


if __name__ == "__main__":
    main()

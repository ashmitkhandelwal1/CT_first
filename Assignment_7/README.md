# Assignment 7 — Incremental Data Processing with Delta Lake

> **Student:** Ashmit Gupta  
> **Subject:** Big Data Engineering  
> **Date:** July 2026  

---

## 📌 Objective

Perform **incremental data processing** using Delta Lake by:

1. Loading a customer dataset into a Delta table
2. Performing basic cleaning (handle nulls, remove duplicates)
3. Creating a second dataset simulating new/incremental data
4. Applying a **MERGE** operation to update existing and insert new records
5. Validating results (row count, duplicate check)
6. Displaying the final dataset and generating a summary

---

## 🗂️ Project Structure

```
Assignment_7/
│
├── data/
│   ├── customer_master.csv          # Initial dataset (20 records + 2 intentional duplicates)
│   └── customer_incremental.csv     # Incremental data (updates + new customers)
│
├── notebooks/
│   └── delta_scd_assignment.ipynb   # Main Jupyter Notebook (all 6 steps)
│
├── screenshots/
│   ├── data_loading/                # Screenshots from Step 1
│   ├── data_cleaning/               # Charts from Step 2 (cleaning_summary.png)
│   ├── scd1/                        # Charts from Step 4 (merge_results.png)
│   ├── scd2/                        # Reserved for SCD Type 2 extensions
│   ├── validation/                  # Charts from Step 5 (validation_charts.png)
│   └── final_output/                # Charts from Step 6 (final_summary.png)
│
├── delta_tables/
│   └── customer_master/             # Delta Lake table (auto-generated on run)
│
├── report/
│   └── assignment_summary.pdf       # (optional) written summary report
│
├── objective.txt                    # Original assignment brief
└── README.md                        # This file
```

---

## 🚀 How to Run

### Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.8+ |
| Java (JDK) | 8 or 11 (required by Spark) |
| Apache Spark | 3.3+ |
| delta-spark | 2.3+ |
| Jupyter Notebook / JupyterLab | Latest |

### 1. Install Python dependencies

```bash
pip install pyspark delta-spark pandas matplotlib seaborn jupyter
```

### 2. Set up Java

Make sure `JAVA_HOME` is set and Java is in your PATH:

```bash
java -version   # Should show Java 8 or 11
```

### 3. Launch Jupyter

```bash
jupyter notebook
```

### 4. Open and run the notebook

Navigate to `notebooks/delta_scd_assignment.ipynb` and run all cells **top-to-bottom**.

> ⚠️ The notebook automatically creates the `delta_tables/` directory at runtime. Do **not** run cells out of order.

---

## 📊 Pipeline Steps — Detail

### Step 1 — Data Loading
- Reads `customer_master.csv` with an explicit Spark schema
- Writes the DataFrame to a **Delta table** at `delta_tables/customer_master/`

### Step 2 — Data Cleaning
- **Null handling:** Drops rows where `customer_id`, `name`, or `email` is null; fills remaining nulls with defaults
- **Deduplication:** Uses a Window function partitioned by `customer_id` (ordered by `last_updated desc`) to keep the most recent record per customer
- Overwrites the Delta table with clean data

### Step 3 — Incremental Dataset
- Reads `customer_incremental.csv` (12 records: 6 updates + 6 new customers)
- Tags each record as `UPDATE` or `INSERT` for visual inspection

### Step 4 — MERGE Operation (Upsert)
- Uses the Delta Lake `DeltaTable.merge()` API
- **`whenMatchedUpdate`** — updates all fields for existing `customer_id`
- **`whenNotMatchedInsert`** — inserts brand-new customers
- Result: 26 unique, up-to-date customer records

### Step 5 — Validation
- Checks: total row count, distinct ID count, duplicate count, null count
- Computes aggregate statistics (avg/max/min purchase amount, active/inactive split)
- Runs **assertions** to fail fast if data quality issues are detected

### Step 6 — Final Output
- Displays the full merged dataset sorted by `customer_id`
- Generates country-wise and status-wise aggregation summaries
- Prints Delta table **version history** (shows 3 versions: load → clean → merge)
- Saves 4 summary charts to the `screenshots/` folders

---

## 📈 Output Charts

| Chart | Location | Description |
|---|---|---|
| Cleaning Summary | `screenshots/data_cleaning/cleaning_summary.png` | Null counts + row count pipeline |
| Merge Results | `screenshots/scd1/merge_results.png` | Before/after row counts + UPDATE vs INSERT breakdown |
| Validation Charts | `screenshots/validation/validation_charts.png` | Data quality metrics, status pie, purchase histogram |
| Final Summary | `screenshots/final_output/final_summary.png` | Country counts, top purchases, age distribution, status split |

---

## 🧠 Key Concepts Used

| Concept | Technology |
|---|---|
| Delta Lake MERGE (Upsert) | `delta.tables.DeltaTable.merge()` |
| Window Functions (Dedup) | `pyspark.sql.Window.partitionBy().orderBy()` |
| Schema Enforcement | `pyspark.sql.types.StructType` |
| Delta Table History | `DeltaTable.history()` |
| Incremental Processing | Batch MERGE pattern |

---

## 📋 Dataset Description

### `customer_master.csv` (22 rows = 20 unique + 2 duplicates)

| Column | Type | Description |
|---|---|---|
| customer_id | String | Unique identifier (C001–C020) |
| name | String | Full name |
| email | String | Email address |
| city | String | City of residence |
| country | String | Country |
| age | Integer | Customer age |
| purchase_amount | Double | Total purchase value ($) |
| status | String | `active` / `inactive` |
| last_updated | String | Last record update date |

### `customer_incremental.csv` (12 rows)
- **6 updates** to existing customers: C003, C005, C007, C010, C012, C017
- **6 new customers**: C021–C026

---

## 👨‍💻 Author

**Ashmit Gupta**  
Big Data Engineering | Assignment 7  
July 2026

---

## 📝 Notes

- The `delta_tables/` directory is auto-generated when the notebook runs — it is not tracked by Git (add to `.gitignore`)
- Screenshot PNG files are auto-saved by the notebook into the appropriate `screenshots/` subdirectories
- Java must be installed for PySpark to work on Windows

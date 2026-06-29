# Assignment 6 — Apache Spark: Architecture & Data Processing

**Student:** Ashmit Gupta
**Week:** 6
**Topic:** Spark Architecture, Lazy Evaluation, Transformations, File Formats & Data Pipelines

---

## Objective

Understand Spark architecture and perform efficient data processing using transformations, filtering, schema handling, and optimized file formats.

---

## Repository Structure

```
Assignment-6/
│
├── README.md                    <- You are here
├── objective.txt                <- Assignment objective
├── questions.txt                <- All 15 questions (Week 6)
│
├── Assignment6_Answers.md       <- Complete written answers for all 15 questions
├── assignment6_pyspark.py       <- Runnable PySpark code (Q3, Q5, Q6, Q8, Q10, Q12, Q14)
│
└── data/
    └── source.csv               <- Sample dataset (25 rows, multi-domain products)
```

---

## Dataset — `data/source.csv`

A 25-row sample dataset containing product and order information with the following columns:

| Column | Type | Description |
|---|---|---|
| `product_id` | String | Unique product identifier (e.g. P001) |
| `product_name` | String | Name of the product |
| `category` | String | Electronics, Clothing, Sports, Books, etc. |
| `price` | Double | Selling price (INR) |
| `base_price` | Double | Price before tax |
| `status` | String | Order status: Completed / Pending / Cancelled |
| `amount` | Integer | Transaction amount |
| `user_id` | String | Buyer ID (nullable — some rows intentionally null) |
| `region` | String | North / South / East / West |
| `priority` | String | High / Medium / Low |

> Some `user_id` values are intentionally left null to demonstrate null-filtering (Q12).

---

## Questions Covered

| Q# | Type | Topic |
|---|---|---|
| Q1 | Theory | Driver, Cluster Manager & Executor roles |
| Q2 | Theory | Lazy Evaluation & DAG optimization |
| Q3 | **Code** | Read CSV with `header=true` & `inferSchema=true` |
| Q4 | Theory | CSV vs Parquet — row-based vs columnar storage |
| Q5 | **Code** | `select` + `filter` on category |
| Q6 | **Code** | `withColumnRenamed` + `cast(DoubleType())` |
| Q7 | Theory | DAG Lineage Graph & fault tolerance |
| Q8 | **Code** | Compound AND filter on status & amount |
| Q9 | Theory | Predicate Pushdown in Parquet |
| Q10 | **Code** | Add `final_price` column with 18% GST |
| Q11 | Theory | Transformations vs Actions (2 examples each) |
| Q12 | **Code** | Full pipeline: Parquet read → filter nulls → CSV write |
| Q13 | Theory | Client Mode vs Cluster Mode |
| Q14 | **Code** | OR filter on region & priority |
| Q15 | Theory | `.show(5)` vs `.collect()` on large datasets |

---

## How to Run

### Prerequisites

- Python 3.8+
- Java 8 or 11 (required by Spark)
- PySpark installed

```bash
pip install pyspark
```

### Run the PySpark Script

```bash
cd "Assignment-6"
python assignment6_pyspark.py
```

The script will:
1. Initialize a local SparkSession
2. Load `data/source.csv` with schema inference
3. Execute and print results for each coding question
4. Write Parquet output to `path/to/input/`
5. Write cleaned CSV output to `path/to/output/`
6. Run a bonus CSV vs Parquet performance comparison

> **Note:** All outputs use `.show()` (never `.collect()`) to follow best practices for large-scale data.

---

## Key Concepts Demonstrated

| Concept | Where |
|---|---|
| SparkSession initialization | Top of `assignment6_pyspark.py` |
| Schema inference from CSV | Q3 |
| Column selection & filtering | Q5, Q8, Q14 |
| Column renaming & type casting | Q6 |
| Adding computed columns | Q10 |
| Null value handling | Q12 |
| Parquet read/write | Q12, Bonus |
| Lazy evaluation demo + `.explain()` | Bonus section |
| CSV vs Parquet timing comparison | Bonus section |
| DAG physical plan inspection | Bonus section |

---

## Output Files Generated at Runtime

After running `assignment6_pyspark.py`, the following directories will be created:

```
Assignment-6/
├── path/
│   ├── to/
│   │   ├── input/       <- Parquet output (intermediate)
│   │   └── output/      <- Cleaned CSV output (null user_id removed)
└── data/
    ├── output_csv/      <- CSV copy for performance comparison
    └── output_parquet/  <- Parquet copy for performance comparison
```

---

## Performance Insights

- **Parquet** is faster than CSV for analytics due to columnar storage, compression (Snappy), and Predicate Pushdown
- **Lazy Evaluation** ensures Spark optimizes the full transformation chain before any computation begins
- **Predicate Pushdown** skips entire row groups in Parquet based on min/max statistics — drastically reducing I/O
- **`.show()`** fetches only a few rows to the Driver, while **`.collect()`** brings the entire dataset — dangerous on TB-scale data

---

## References

- [Apache Spark Official Docs](https://spark.apache.org/docs/latest/)
- [PySpark API Reference](https://spark.apache.org/docs/latest/api/python/)
- [Parquet File Format](https://parquet.apache.org/documentation/latest/)

---

*Submitted by **Ashmit Gupta** | Week 6 | Big Data & Cloud Computing*

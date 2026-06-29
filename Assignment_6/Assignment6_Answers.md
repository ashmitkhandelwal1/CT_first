# Assignment 6 — Apache Spark: Architecture & Data Processing
**Student:** Ashmit Gupta
**Subject:** Big Data & Cloud Computing
**Topic:** Spark Architecture, Lazy Evaluation, Transformations, File Formats & Pipelines

---

## Q1: Explain the roles of the Driver, Cluster Manager, and Executor in a Spark application.

Apache Spark follows a **master-worker architecture** consisting of three key components:

### 1. Driver (Master Node)
- The **Driver** is the brain of a Spark application. It runs the `main()` function (or the Python/Scala script you submit).
- Responsibilities:
  - Creates the `SparkSession` / `SparkContext`
  - Converts user code into a **DAG (Directed Acyclic Graph)** of stages and tasks
  - Schedules tasks onto Executors via the Cluster Manager
  - Collects results from Executors
  - Maintains metadata about the running application

### 2. Cluster Manager
- Acts as the **resource negotiator** between the Driver and the worker nodes.
- It allocates CPU and memory resources for Executors.
- Spark supports multiple cluster managers:
  - **Standalone** (built-in)
  - **YARN** (Hadoop's resource manager)
  - **Mesos**
  - **Kubernetes**
- The Driver requests resources; the Cluster Manager grants them.

### 3. Executor (Worker Node)
- Executors are **JVM processes** launched on worker nodes.
- Responsibilities:
  - Execute the actual tasks assigned by the Driver
  - Store data in memory (RDD partitions / DataFrame blocks) for fast access
  - Report task status back to the Driver
  - Each Executor runs one or more **Tasks** in parallel (multi-threaded)

```
User Script
    |
    v
 [Driver]
    |-- Builds DAG ------------------------------------------|
    |                                                         |
    v                                                         v
[Cluster Manager]                                   [Executors x N]
 (YARN / K8s / Standalone)                    (run tasks, cache data)
    |
    +-- Allocates Resources to Executors
```

---

## Q2: How does Spark's Lazy Evaluation strategy improve performance when chain-processing large datasets?

### What is Lazy Evaluation?
In Spark, **transformations** (like `filter()`, `select()`, `map()`) are **not executed immediately** when called. Instead, Spark records them as a **logical plan** (the DAG). Actual computation only happens when an **action** (like `show()`, `count()`, `write()`) is triggered.

### How it Improves Performance

| Optimization | Description |
|---|---|
| **Pipelining** | Multiple transformations are merged into a single-pass operation, reducing data scans |
| **Predicate Pushdown** | Filters are pushed as early as possible in the plan, reducing data read from disk |
| **Projection Pruning** | Only required columns are read/processed, skipping unused data |
| **Fusion of Stages** | Spark combines narrow transformations into one stage to avoid unnecessary shuffles |
| **Query Optimization** | Catalyst Optimizer rewrites the logical plan into the most efficient physical plan |

### Example
```python
# No execution happens here -- just building the DAG
df_lazy = df.filter(col("category") == "Electronics") \
            .select("product_id", "price") \
            .withColumn("discounted", col("price") * 0.9)

# Execution only starts here:
df_lazy.show()  # <- Action triggers the optimized plan
```
Without lazy evaluation, each line would trigger a full data scan. With it, Spark combines them into **one optimized pass**.

---

## Q3: Write a Spark command to read a CSV file located at "data/source.csv", ensuring the first row is treated as a header and inferSchema is enabled.

```python
df = spark.read \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .csv("data/source.csv")

df.printSchema()
df.show(5)
```

**Key options explained:**
- `header="true"` -> treats the first row as column names instead of data
- `inferSchema="true"` -> Spark automatically detects data types (IntegerType, DoubleType, StringType) by scanning the data -- without this, everything is read as StringType

---

## Q4: What is the difference between CSV and Parquet in terms of storage (row-based vs. columnar) and why does it matter for performance?

### Storage Format Comparison

| Feature | CSV | Parquet |
|---|---|---|
| **Storage Model** | Row-based (all columns of a row stored together) | Columnar (each column stored separately) |
| **Compression** | None by default, large files | Built-in Snappy/Gzip compression, ~3-10x smaller |
| **Schema** | No schema embedded; must be inferred | Schema embedded in file metadata |
| **Read Performance** | Full row scan even for 1 column | Only reads required columns |
| **Write Performance** | Fast | Slightly slower (encoding overhead) |
| **Predicate Pushdown** | Not supported | Fully supported (row groups skipped) |
| **Splittability** | Partially splittable | Fully splittable |
| **Use Case** | Human-readable exchange, small data | Analytics, big data, production pipelines |

### Why It Matters for Performance
- **Query with 2 of 50 columns:** CSV reads all 50 columns (100% I/O), Parquet reads only 2 (4% I/O)
- **Aggregations on a single column:** Parquet reads just that column's byte range from disk
- **Predicate Pushdown:** Parquet stores min/max statistics per row group -- Spark can skip entire blocks without reading them

> **Ashmit's Rule of Thumb:** Use CSV for data exchange/logging; use Parquet for any production Spark pipeline.

---

## Q5: Given a DataFrame df, write a query to select the columns product_id and price where the category is 'Electronics'.

```python
df_electronics = df.select("product_id", "price") \
                   .filter(col("category") == "Electronics")

df_electronics.show()
```

**Alternative using SQL-style:**
```python
df.createOrReplaceTempView("products")
df_electronics = spark.sql("""
    SELECT product_id, price
    FROM products
    WHERE category = 'Electronics'
""")
df_electronics.show()
```

---

## Q6: Write the code to "revise" a DataFrame by renaming the column old_name to new_name and casting the price column from a String to a Double.

```python
from pyspark.sql.types import DoubleType

df_revised = df \
    .withColumnRenamed("old_name", "new_name") \
    .withColumn("price", col("price").cast(DoubleType()))

df_revised.printSchema()
df_revised.show(5)
```

**Why this is needed:**
- `withColumnRenamed()` -- renames a column without changing its data
- `cast(DoubleType())` -- converts String "1299.00" to numeric 1299.0 so arithmetic operations work correctly
- Without casting, operations like `col("price") * 1.18` would fail or produce incorrect results

---

## Q7: How does Spark use the Lineage Graph (DAG) to provide fault tolerance if a worker node fails?

### The Lineage Graph (DAG)
When you apply transformations, Spark builds a **Directed Acyclic Graph (DAG)** -- a complete blueprint of every operation applied to the data, from source to result.

### Fault Tolerance Mechanism

1. **No Replication by Default:** Unlike Hadoop, Spark doesn't replicate data to multiple nodes by default.
2. **Recomputation via Lineage:** If an Executor fails and loses its partition, Spark consults the DAG lineage to **recompute only the lost partition** from the last stable checkpoint or source.
3. **Selective Rebuild:** Spark doesn't rerun the whole job -- only the failed partition is recomputed by reassigning it to another available Executor.

```
Source CSV
    |
    v
[filter: category='Electronics']   <- Lineage Step 1
    |
    v
[select: product_id, price]        <- Lineage Step 2
    |
    v
[Partition 3 lost on Node B!]
    |
    Spark recomputes Partition 3
    by replaying Steps 1 & 2 on
    the source data -> assigns to Node C
```

### RDD Checkpointing
For very long chains, you can use `df.checkpoint()` to materialize data to disk and truncate the lineage, avoiding expensive full recomputation.

---

## Q8: Write a query to filter a DataFrame df_orders for rows where the status is 'Completed' AND the amount is greater than 1000.

```python
df_completed_high_value = df_orders.filter(
    (col("status") == "Completed") & (col("amount") > 1000)
)

df_completed_high_value.show()
```

**Important:** In PySpark, use `&` (bitwise AND) instead of Python's `and` keyword, and wrap each condition in parentheses to avoid operator precedence issues.

**Alternative using SQL string expression:**
```python
df_completed_high_value = df_orders.filter(
    "status = 'Completed' AND amount > 1000"
)
```

---

## Q9: Explain the concept of Predicate Pushdown in Parquet and how it affects the amount of data loaded into memory.

### What is Predicate Pushdown?
Predicate Pushdown is an **optimization technique** where filter conditions (predicates) are "pushed down" to the **data source level** -- meaning the filtering happens **before** data is loaded into memory, not after.

### How it Works with Parquet

Parquet files are organized into **Row Groups**, and each Row Group stores **min/max statistics** for every column:

```
Parquet File
+-- Row Group 1 [rows 1-10,000]      -> price_min=100,  price_max=500
+-- Row Group 2 [rows 10,001-20,000] -> price_min=501,  price_max=2000
+-- Row Group 3 [rows 20,001-30,000] -> price_min=2001, price_max=50000
```

If you run:
```python
df.filter(col("price") > 1500)
```

Spark's Catalyst Optimizer pushes this filter to Parquet:
- Row Group 1: max=500 < 1500  -> **SKIP** (not loaded at all)
- Row Group 2: range overlaps  -> **LOAD**
- Row Group 3: min=2001 > 1500 -> **LOAD**

### Impact on Performance
- **Without Pushdown (CSV):** All data loaded -> filtered in memory
- **With Pushdown (Parquet):** Only relevant row groups loaded -> massive I/O savings
- For a 1TB dataset with 10% matching rows, predicate pushdown can reduce I/O from 1TB to ~100GB

---

## Q10: Write a code snippet to add a new column final_price which is the base_price multiplied by 1.18 (18% tax).

```python
from pyspark.sql.functions import col, lit

df_with_tax = df.withColumn("final_price", col("base_price") * lit(1.18))

df_with_tax.select("product_id", "product_name", "base_price", "final_price").show()
```

**Note:** `lit(1.18)` wraps the Python literal `1.18` into a Spark Column expression. This is best practice over just using `* 1.18` directly, making the intent explicit and avoiding type inference ambiguity.

---

## Q11: What is the difference between Transformations and Actions? Provide two examples of each.

### Transformations
- Operations that **define a new DataFrame** from an existing one
- They are **lazy** -- not executed immediately; added to the DAG
- Return a new DataFrame/RDD

| Example | Description |
|---|---|
| `df.filter(col("price") > 1000)` | Creates a new DF with filtered rows |
| `df.select("product_id", "price")` | Creates a new DF with selected columns |

Other examples: `map()`, `groupBy()`, `join()`, `withColumn()`, `orderBy()`

### Actions
- Operations that **trigger actual execution** of the DAG
- Cause Spark to compute results and return a value to the Driver or write to storage

| Example | Description |
|---|---|
| `df.count()` | Returns the number of rows (triggers full computation) |
| `df.show(5)` | Prints first 5 rows to console (triggers computation) |

Other examples: `collect()`, `write()`, `first()`, `take(n)`, `save()`

### Key Distinction
```python
# TRANSFORMATION (lazy -- no computation)
df_filtered = df.filter(col("category") == "Electronics")

# ACTION (triggers computation of entire DAG)
df_filtered.count()  # <- execution happens here
```

---

## Q12: Write the Spark command to load a Parquet file from "path/to/input", filter out any rows where user_id is null, and save the result as a CSV at "path/to/output".

```python
# Step 1: Load from Parquet
df_parquet = spark.read.parquet("path/to/input")

# Step 2: Filter out rows where user_id is null
df_clean = df_parquet.filter(col("user_id").isNotNull())

# Step 3: Save as CSV
df_clean.write \
    .mode("overwrite") \
    .option("header", "true") \
    .csv("path/to/output")
```

**Full pipeline:**
```
[Parquet Source] -> [Filter nulls on user_id] -> [CSV Output]
   Read Phase           Transform Phase            Write Phase
```

`mode("overwrite")` ensures that if the output path already exists, it is replaced.
Other modes: `"append"`, `"ignore"`, `"error"` (default).

---

## Q13: In Spark Architecture, what is the difference between Client Mode and Cluster Mode?

### Overview

| Feature | Client Mode | Cluster Mode |
|---|---|---|
| **Driver Location** | Runs on the **submitting machine** (your laptop/edge node) | Runs **inside the cluster** (on a worker/application master node) |
| **Best For** | Interactive sessions, Jupyter notebooks, development | Production batch jobs, long-running pipelines |
| **Network Dependency** | Driver must stay connected; network latency affects shuffle data collection | Driver is co-located with cluster; low latency |
| **Failure Impact** | If the submitting machine disconnects, the job fails | Driver failure handled by cluster; more resilient |
| **Example** | `spark-submit --deploy-mode client app.py` | `spark-submit --deploy-mode cluster app.py` |

### Visual Difference

```
CLIENT MODE:                          CLUSTER MODE:
+----------------------+             +------------------------------------+
|  Your Machine        |             |           Cluster                  |
|  [Driver]            |--network--> |  [App Master / Driver]             |
|                      |             |  [Executor 1] [Executor 2] ...     |
+----------------------+             +------------------------------------+
 Submitter = Driver                   Driver lives inside the cluster
```

> **Ashmit's Tip:** Use **Client Mode** for development/debugging (real-time logs visible). Use **Cluster Mode** for production to avoid single points of failure.

---

## Q14: Write a query to filter a dataset for rows where the region is 'North' OR the priority is 'High'.

```python
df_priority_north = df.filter(
    (col("region") == "North") | (col("priority") == "High")
)

df_priority_north.select("product_id", "product_name", "region", "priority").show()
```

**Important:** Use `|` (bitwise OR) in PySpark, not Python's `or`. Always wrap each condition in parentheses.

**Alternative using SQL expression string:**
```python
df_priority_north = df.filter(
    "region = 'North' OR priority = 'High'"
)
```

---

## Q15: When exploring a dataset, why is it safer to use .show(5) instead of .collect() on a multi-terabyte dataset?

### The Core Problem with `.collect()`
`.collect()` brings **all rows** of the DataFrame from every Executor across the cluster **back to the Driver** as a Python list in memory.

```
Executor 1: [100 GB data] --|
Executor 2: [100 GB data] --+--> [Driver Memory: 300 GB -> CRASH / OOM]
Executor 3: [100 GB data] --|
```

### Comparison

| | `.show(5)` | `.collect()` |
|---|---|---|
| **Data transferred to Driver** | Only 5 rows | ALL rows (potentially TBs) |
| **Driver memory risk** | Negligible | Extremely high (OOM error) |
| **Network overhead** | Minimal | Massive |
| **Speed** | Fast (partial scan) | Slow (full scan + transfer) |
| **Use Case** | Exploration, debugging | Small DataFrames only |

### Safe Exploration Practices
```python
# Safe -- only fetches 5 rows
df.show(5)

# Safe -- aggregate result is tiny
df.count()

# Safe -- uses head optimization
df.first()

# Dangerous on large datasets
df.collect()  # brings ALL data to driver memory

# If you must use collect(), filter first:
df.filter(col("category") == "Electronics").limit(100).collect()
```

> **Ashmit's Rule:** On production datasets, **never use `.collect()`** unless you've first applied a `.limit()` or you're absolutely certain the result is small. Use `.show()`, `.describe()`, or `.summary()` for safe exploration.

---

## Performance & Architecture Insights (Bonus)

### Shuffle Operations (Wide Transformations)
Wide transformations like `groupBy()`, `join()`, `distinct()` cause **shuffles** -- data is redistributed across all partitions/nodes. This is the most expensive operation in Spark.

**Optimization:** Minimize shuffles by filtering data early, using broadcast joins for small tables, and tuning `spark.sql.shuffle.partitions`.

### Best Practices Summary

| Practice | Why |
|---|---|
| Use `.show()` over `.collect()` | Avoids OOM on Driver |
| Filter early in the pipeline | Reduces data volume for later stages |
| Use Parquet over CSV for analytics | Columnar, compressed, pushdown-enabled |
| Set appropriate partition count | Avoid too many small tasks or too few large ones |
| Use `explain()` to view query plan | Verify optimizations are applied |
| Cache with `.cache()` or `.persist()` | Avoid recomputing frequently used DataFrames |

---

*Assignment completed by **Ashmit Gupta** | Week 6 | Apache Spark & PySpark*

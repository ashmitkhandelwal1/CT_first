# =============================================================================
# Assignment 6 - PySpark Data Processing
# Student : Ashmit Gupta
# Objective: Spark Architecture, Transformations, File Formats & Data Pipelines
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, when, isnull
from pyspark.sql.types import DoubleType, StringType, IntegerType, StructType, StructField

# ------------------------------------------------------------------------------
# Initialize SparkSession (Driver starts here)
# ------------------------------------------------------------------------------
spark = SparkSession.builder \
    .appName("Assignment6_AshmitGupta") \
    .master("local[*]") \
    .config("spark.sql.shuffle.partitions", "4") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

print("=" * 60)
print("  Spark Assignment 6 — Ashmit Gupta")
print("=" * 60)
print(f"  Spark Version   : {spark.version}")
print(f"  App Name        : {spark.sparkContext.appName}")
print(f"  Master          : {spark.sparkContext.master}")
print("=" * 60)


# ==============================================================================
# Q3 — Read CSV with header and inferSchema
# ==============================================================================
print("\n[Q3] Reading CSV file with header=True and inferSchema=True")
print("-" * 60)

df = spark.read \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .csv("data/source.csv")

print("Schema inferred by Spark:")
df.printSchema()

print(f"Total rows loaded: {df.count()}")
df.show(5)


# ==============================================================================
# Q5 — Select product_id and price where category = 'Electronics'
# ==============================================================================
print("\n[Q5] Select product_id and price where category = 'Electronics'")
print("-" * 60)

df_electronics = df.select("product_id", "price") \
                   .filter(col("category") == "Electronics")

print(f"Electronics products count: {df_electronics.count()}")
df_electronics.show()


# ==============================================================================
# Q6 — Rename column and cast data type
# ==============================================================================
print("\n[Q6] Rename 'product_name' → 'product_title' and cast 'price' from String to Double")
print("-" * 60)

# First, read CSV treating all columns as strings to demonstrate casting
df_raw = spark.read \
    .option("header", "true") \
    .option("inferSchema", "false") \
    .csv("data/source.csv")

print("Schema before rename & cast:")
df_raw.printSchema()

df_revised = df_raw \
    .withColumnRenamed("product_name", "product_title") \
    .withColumn("price", col("price").cast(DoubleType()))

print("\nSchema after rename & cast:")
df_revised.printSchema()
df_revised.select("product_id", "product_title", "price").show(5)


# ==============================================================================
# Q8 — Filter where status = 'Completed' AND amount > 1000
# ==============================================================================
print("\n[Q8] Filter: status = 'Completed' AND amount > 1000")
print("-" * 60)

df_orders = df  # reusing the main dataframe as df_orders

df_filtered_orders = df_orders.filter(
    (col("status") == "Completed") & (col("amount") > 1000)
)

print(f"Completed orders with amount > 1000: {df_filtered_orders.count()}")
df_filtered_orders.select("product_id", "product_name", "status", "amount").show()


# ==============================================================================
# Q10 — Add new column final_price = base_price * 1.18 (18% tax)
# ==============================================================================
print("\n[Q10] Add column 'final_price' = base_price * 1.18")
print("-" * 60)

df_with_tax = df.withColumn("final_price", col("base_price") * lit(1.18))

print("DataFrame with final_price (GST inclusive):")
df_with_tax.select("product_id", "product_name", "base_price", "final_price").show()


# ==============================================================================
# Q12 — Load Parquet, filter nulls on user_id, save as CSV
# ==============================================================================
print("\n[Q12] Data Pipeline: Read → Filter nulls → Write")
print("-" * 60)

# Step 1: Save current df as Parquet first (to simulate reading from Parquet)
print("  Step 1: Saving DataFrame as Parquet to 'path/to/input'...")
df_with_tax.write.mode("overwrite").parquet("path/to/input")
print("  Parquet file written successfully.")

# Step 2: Load from Parquet
print("  Step 2: Loading from Parquet 'path/to/input'...")
df_parquet = spark.read.parquet("path/to/input")
print(f"  Rows loaded from Parquet: {df_parquet.count()}")

# Step 3: Filter out rows where user_id is null
print("  Step 3: Filtering out rows where user_id is null...")
df_clean = df_parquet.filter(col("user_id").isNotNull())
print(f"  Rows after null filter (user_id): {df_clean.count()}")

# Step 4: Save result as CSV
print("  Step 4: Saving clean data as CSV to 'path/to/output'...")
df_clean.write.mode("overwrite") \
        .option("header", "true") \
        .csv("path/to/output")
print("  CSV output written successfully.")
df_clean.select("product_id", "user_id", "status", "final_price").show(5)


# ==============================================================================
# Q14 — Filter where region = 'North' OR priority = 'High'
# ==============================================================================
print("\n[Q14] Filter: region = 'North' OR priority = 'High'")
print("-" * 60)

df_priority_north = df.filter(
    (col("region") == "North") | (col("priority") == "High")
)

print(f"Rows where region='North' OR priority='High': {df_priority_north.count()}")
df_priority_north.select("product_id", "product_name", "region", "priority").show()


# ==============================================================================
# BONUS — Demonstrate Lazy Evaluation: build transformation chain (no action yet)
# ==============================================================================
print("\n[BONUS] Demonstrating Lazy Evaluation")
print("-" * 60)

# No computation happens until .show() or .count() is called
lazy_df = df \
    .filter(col("category") == "Electronics") \
    .select("product_id", "product_name", "price") \
    .withColumn("price_in_usd", col("price") / lit(84.0))

print("  Transformation chain built (no execution yet — Lazy Evaluation!)")
print("  Calling .explain() to see the Physical Plan / DAG:")
lazy_df.explain(mode="formatted")

print("  Now calling .show() → triggers actual execution:")
lazy_df.show()


# ==============================================================================
# BONUS — CSV vs Parquet Performance Comparison
# ==============================================================================
print("\n[BONUS] CSV vs Parquet — Performance Comparison")
print("-" * 60)

import time

# Write CSV
df.write.mode("overwrite").option("header", "true").csv("data/output_csv")

# Write Parquet
df.write.mode("overwrite").parquet("data/output_parquet")

# Time CSV read
t0 = time.time()
count_csv = spark.read.option("header","true").option("inferSchema","true").csv("data/output_csv").count()
t_csv = time.time() - t0

# Time Parquet read
t1 = time.time()
count_parquet = spark.read.parquet("data/output_parquet").count()
t_parquet = time.time() - t1

print(f"  CSV     → rows: {count_csv}, read time: {t_csv:.4f}s")
print(f"  Parquet → rows: {count_parquet}, read time: {t_parquet:.4f}s")
print("  Parquet is faster due to columnar storage & predicate pushdown.")


# ==============================================================================
# Summary
# ==============================================================================
print("\n" + "=" * 60)
print("  All Questions Demonstrated Successfully!")
print("  Student: Ashmit Gupta | Assignment 6 | PySpark")
print("=" * 60)

spark.stop()

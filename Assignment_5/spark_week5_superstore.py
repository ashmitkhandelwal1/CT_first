"""
Celebal Technologies - Week 5 Assessment
Name: Ashmit Gupta
Dataset: Superstore_messy.csv
Topic: Apache Spark Fundamentals using PySpark
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, avg, count, sum as total_sum,
    min as min_value, max as max_value,
    mean, to_date
)

# Create Spark Session
spark = SparkSession.builder \
    .appName("CelebalWeek5_AshmitGupta_Superstore") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

# Load dataset
# The dataset contains a few duplicate records and missing values
# added intentionally to demonstrate Spark data-cleaning operations.
sales_df = spark.read.csv(
    "Superstore_messy.csv",
    header=True,
    inferSchema=True,
    multiLine=True,
    escape='"'
)

print("\n================ DATASET OVERVIEW ================")
print("Total Records:", sales_df.count())
sales_df.printSchema()

# ---------------- Q3 ----------------
print("\n================ Q3: Removing Duplicate Records ================")

clean_df = sales_df.dropDuplicates(["Order ID", "Order Date"])

print("Rows Before Cleaning :", sales_df.count())
print("Rows After Cleaning  :", clean_df.count())

# ---------------- Q4 ----------------
print("\n================ Q4: Average Sales by Category (West Region) ================")

west_sales = (
    sales_df
    .filter(col("Region") == "West")
    .groupBy("Category")
    .agg(avg("Sales").alias("average_sales"))
)

west_sales.show()

# ---------------- Q5 ----------------
print("\n================ Q5: Handling Missing Ship Mode Values ================")

null_before = sales_df.filter(col("Ship Mode").isNull()).count()
print("Null Ship Mode values before fill:", null_before)

filled_df = sales_df.na.fill({"Ship Mode": "Unknown"})

null_after = filled_df.filter(col("Ship Mode").isNull()).count()
print("Null Ship Mode values after fill :", null_after)

# ---------------- Q6 ----------------
print("\n================ Q6: Cities Having More Than 100 Orders ================")

city_summary = (
    sales_df
    .groupBy("City")
    .agg(count("*").alias("record_count"))
    .filter(col("record_count") > 100)
    .orderBy(col("record_count").desc())
)

city_summary.show()

# ---------------- Q8 ----------------
print("\n================ Q8: Consumer Orders with Quantity 1 to 5 ================")

filtered_orders = sales_df.filter(
    (col("Quantity") >= 1) &
    (col("Quantity") <= 5) &
    (col("Segment") == "Consumer")
)

print("Matching Records:", filtered_orders.count())

filtered_orders.select(
    "Order ID",
    "Quantity",
    "Segment"
).show(5)

# ---------------- Q10 ----------------
print("\n================ Q10: Convert and Rename Order Date Column ================")

date_df = (
    sales_df
    .withColumn(
        "order_date",
        to_date(col("Order Date"), "M/d/yyyy")
    )
    .drop("Order Date")
)

date_df.select("order_date").show(5)
date_df.printSchema()

# ---------------- Q12 ----------------
print("\n================ Q12: Remove Invalid Customer Records ================")

print("Rows Before Filtering:", sales_df.count())

valid_customers = sales_df.filter(
    col("Customer Name").isNotNull() &
    (col("City") != "")
)

print("Rows After Filtering :", valid_customers.count())

# ---------------- Q13 ----------------
print("\n================ Q13: Sales Statistics ================")

sales_statistics = sales_df.agg(
    min_value("Sales").alias("minimum_sales"),
    max_value("Sales").alias("maximum_sales"),
    mean("Sales").alias("average_sales")
)

sales_statistics.show()

# ---------------- Q15 ----------------
print("\n================ Q15: Revenue Analysis by Region ================")

step_1 = sales_df.dropDuplicates()

step_2 = step_1.na.fill({
    "Sales": 0
})

region_revenue = (
    step_2
    .groupBy("Region")
    .agg(total_sum("Sales").alias("total_revenue"))
    .orderBy(col("total_revenue").desc())
)

region_revenue.show()

spark.stop()

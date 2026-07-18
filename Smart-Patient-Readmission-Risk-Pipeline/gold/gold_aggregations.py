# Databricks notebook source
# DBTITLE 1,Gold Layer Overview
# MAGIC %md
# MAGIC # Gold Layer — Business Aggregations
# MAGIC
# MAGIC Reads `silver_admissions_enriched` and computes four business-ready
# MAGIC analytics tables, each answering a specific operational or clinical question.
# MAGIC
# MAGIC **Pipeline step**: `gold_aggregations`
# MAGIC
# MAGIC **Reads**: `silver_admissions_enriched`
# MAGIC
# MAGIC **Writes**:
# MAGIC | Table | Business Question |
# MAGIC |---|---|
# MAGIC | `readmission_by_diagnosis` | Which diagnoses drive readmissions? |
# MAGIC | `department_performance` | Which departments underperform? |
# MAGIC | `age_group_risk` | Which age groups are highest risk? |
# MAGIC | `patient_risk_profile` | Per-patient risk categorization |

# COMMAND ----------

# DBTITLE 1,Imports and Configuration
# Databricks notebook source
import os
import sys

# Add project root to Python path
project_root = os.path.abspath("..")

if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("Project root:", project_root)

from pyspark.sql import functions as F
from pyspark.sql.window import Window

import config as cfg
from utils.helpers import (
    log_table_stats,
    write_delta_overwrite,
)

# Setup namespace contexts dynamically
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {cfg.CATALOG}.{cfg.SCHEMA}")
spark.sql(f"USE CATALOG {cfg.CATALOG}")
spark.sql(f"USE SCHEMA {cfg.SCHEMA}")

print(f"\nUsing: {cfg.CATALOG}.{cfg.SCHEMA}")

silver_df = spark.table(cfg.SILVER_ADMISSIONS_ENRICHED)

print(f"silver_admissions_enriched: {silver_df.count()} rows")

# COMMAND ----------

# DBTITLE 1,Gold Table 1 - Readmission by Diagnosis
# ────────────────────────────────────────────
# 1) readmission_by_diagnosis
# ────────────────────────────────────────────
readmission_by_diagnosis = (
    silver_df.withColumnRenamed("category", "diagnosis_category")
    .groupBy("diagnosis_category")
    .agg(
        F.count("admission_id").alias("total_admissions"),
        F.sum("readmission_flag").alias("total_readmissions"),
        F.round(F.avg("readmission_flag"), 4).alias("readmission_rate"),
        F.round(F.avg("length_of_stay"), 2).alias("avg_los"),
    )
    .withColumn(
        "readmission_rank",
        F.dense_rank().over(Window.orderBy(F.desc("readmission_rate"))),
    )
    .orderBy(F.desc("readmission_rate"))
)

readmission_by_diagnosis.show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Gold Table 2 - Department Performance
# ────────────────────────────────────────────
# 2) department_performance
# performance_score = readmission_rate * 100 + avg_los * 2 (higher = worse)
# ────────────────────────────────────────────
department_performance = (
    silver_df.groupBy("department")
    .agg(
        F.count("admission_id").alias("total_admissions"),
        F.round(F.avg("readmission_flag"), 4).alias("readmission_rate"),
        F.round(F.avg("length_of_stay"), 2).alias("avg_los"),
    )
    .withColumn(
        "performance_score",
        F.round(F.col("readmission_rate") * 100 + F.col("avg_los") * 2, 2),
    )
    .withColumn(
        "performance_rank",
        F.dense_rank().over(Window.orderBy(F.desc("performance_score"))),
    )
    .orderBy(F.desc("performance_score"))
)

department_performance.show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Gold Table 3 - Age Group Risk
# ────────────────────────────────────────────
# 3) age_group_risk
# ────────────────────────────────────────────
age_group_risk = (
    silver_df.groupBy("age_group")
    .agg(
        F.countDistinct("patient_id").alias("patient_count"),
        F.count("admission_id").alias("total_admissions"),
        F.round(F.avg("readmission_flag"), 4).alias("readmission_rate"),
        F.round(F.avg("length_of_stay"), 2).alias("avg_los"),
    )
    .orderBy(F.desc("readmission_rate"))
)

age_group_risk.show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Gold Table 4 - Patient Risk Profile
# ────────────────────────────────────────────
# 4) patient_risk_profile
# risk_category: High (>=3 readmissions), Medium (1-2), Low (0)
# ────────────────────────────────────────────
patient_agg = silver_df.groupBy("patient_id", "name", "age", "age_group").agg(
    F.count("admission_id").alias("total_admissions"),
    F.sum("readmission_flag").alias("total_readmissions"),
    F.round(F.avg("length_of_stay"), 2).alias("avg_los"),
    F.max("comorbidity_index").alias("comorbidity_index"),
)

patient_risk_profile = (
    patient_agg.withColumn(
        "risk_category",
        F.when(F.col("total_readmissions") >= 3, "High")
        .when(F.col("total_readmissions") >= 1, "Medium")
        .otherwise("Low"),
    )
    .withColumn(
        "risk_rank",
        F.dense_rank().over(Window.orderBy(F.desc("total_readmissions"))),
    )
    .orderBy(F.desc("total_readmissions"))
)

patient_risk_profile.show(10, truncate=False)

# COMMAND ----------

# DBTITLE 1,Write Gold Delta Tables
# ────────────────────────────────────────────
# 5) Write all 4 Gold Delta tables (idempotent overwrite)
# ────────────────────────────────────────────
write_delta_overwrite(readmission_by_diagnosis, cfg.GOLD_READMISSION_BY_DIAGNOSIS)
write_delta_overwrite(department_performance, cfg.GOLD_DEPARTMENT_PERFORMANCE)
write_delta_overwrite(age_group_risk, cfg.GOLD_AGE_GROUP_RISK)
write_delta_overwrite(patient_risk_profile, cfg.GOLD_PATIENT_RISK_PROFILE)

print("\n" + "=" * 60)
print("GOLD LAYER WRITE COMPLETE")
print("=" * 60)
for table in (
    cfg.GOLD_READMISSION_BY_DIAGNOSIS,
    cfg.GOLD_DEPARTMENT_PERFORMANCE,
    cfg.GOLD_AGE_GROUP_RISK,
    cfg.GOLD_PATIENT_RISK_PROFILE,
):
    log_table_stats(spark, table)

# COMMAND ----------

# DBTITLE 1,Validation Summary
# ────────────────────────────────────────────
# 6) Business validation checks
# ────────────────────────────────────────────
print("\nRisk category distribution:")
spark.table(cfg.GOLD_PATIENT_RISK_PROFILE).groupBy("risk_category").count().orderBy(
    F.desc("count")
).show(truncate=False)

print("Top 3 worst-performing departments:")
spark.table(cfg.GOLD_DEPARTMENT_PERFORMANCE).orderBy(F.desc("performance_score")).show(
    3, truncate=False
)

print("Highest-risk diagnosis category:")
spark.table(cfg.GOLD_READMISSION_BY_DIAGNOSIS).orderBy(
    F.desc("readmission_rate")
).show(1, truncate=False)
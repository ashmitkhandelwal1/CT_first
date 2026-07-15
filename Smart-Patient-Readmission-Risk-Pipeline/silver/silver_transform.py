# Databricks notebook source
# DBTITLE 1,Silver Layer Overview
# MAGIC %md
# MAGIC # Silver Layer — Cleaning, Enrichment, Feature Engineering
# MAGIC
# MAGIC Reads the three Bronze tables, cleans and standardizes them, joins them into
# MAGIC a single admissions-grain table, and engineers features for downstream analytics.
# MAGIC
# MAGIC **Pipeline step**: `silver_transform` → writes `silver_admissions_enriched`
# MAGIC
# MAGIC **Reads**: `patients_bronze`, `diagnoses_bronze`, `admissions_bronze`
# MAGIC
# MAGIC **Writes**: `silver_admissions_enriched` (20 columns, one row per valid admission)

# COMMAND ----------

# DBTITLE 1,Imports and Configuration
import os
import sys

# Add project root to Python path
project_root = os.path.abspath("..")

if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("Project root:", project_root)

from pyspark.sql import functions as F

import config as cfg
from utils.helpers import (
    optimize_table,
    analyze_table,
    log_table_stats,
    validate_no_duplicates,
    write_delta_overwrite,
)

from transformations.feature_engineering import (
    build_silver_admissions_enriched
)

# Databricks Free Edition
# apply_spark_optimizations(spark, cfg.SPARK_OPTIMIZATIONS)

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {cfg.CATALOG}.{cfg.SCHEMA}")

print(f"\nUsing: {cfg.CATALOG}.{cfg.SCHEMA}")

# COMMAND ----------

# DBTITLE 1,Read Bronze Tables
# ────────────────────────────────────────────
# 1) Read Bronze Delta tables
# ────────────────────────────────────────────
patients_bronze = spark.table(cfg.BRONZE_PATIENTS)
diagnoses_bronze = spark.table(cfg.BRONZE_DIAGNOSES)
admissions_bronze = spark.table(cfg.BRONZE_ADMISSIONS)

print(f"patients_bronze:   {patients_bronze.count()} rows")
print(f"diagnoses_bronze:  {diagnoses_bronze.count()} rows")
print(f"admissions_bronze: {admissions_bronze.count()} rows")

# COMMAND ----------

# DBTITLE 1,Build Silver Enriched Table
# ────────────────────────────────────────────
# 2) Clean, join, and engineer features
# ────────────────────────────────────────────
silver_admissions_enriched = build_silver_admissions_enriched(
    patients_bronze, diagnoses_bronze, admissions_bronze
)

silver_admissions_enriched.cache()
row_count = silver_admissions_enriched.count()
print(f"silver_admissions_enriched: {row_count} rows, {len(silver_admissions_enriched.columns)} columns")
silver_admissions_enriched.show(10, truncate=False)

# COMMAND ----------

# DBTITLE 1,Write Silver Delta Table
# ────────────────────────────────────────────
# 3) Write silver_admissions_enriched (idempotent overwrite)
# ────────────────────────────────────────────
write_delta_overwrite(silver_admissions_enriched, cfg.SILVER_ADMISSIONS_ENRICHED)

print("\n" + "=" * 60)
print("SILVER LAYER WRITE COMPLETE")
print("=" * 60)
log_table_stats(spark, cfg.SILVER_ADMISSIONS_ENRICHED)

# ── Delta optimization pass ──
print("\nDelta optimization:")
optimize_table(
    spark,
    cfg.SILVER_ADMISSIONS_ENRICHED,
    cfg.ZORDER_COLUMNS.get(cfg.SILVER_ADMISSIONS_ENRICHED),
)
analyze_table(spark, cfg.SILVER_ADMISSIONS_ENRICHED)

silver_admissions_enriched.unpersist()

# COMMAND ----------

# DBTITLE 1,Validation and Quality Summary
# ────────────────────────────────────────────
# 4) Quality validation checks
# ────────────────────────────────────────────
silver_df = spark.table(cfg.SILVER_ADMISSIONS_ENRICHED)

print("Validation checks:")
validate_no_duplicates(silver_df, ["admission_id"], "silver_admissions_enriched")

null_counts = silver_df.select(
    [F.sum(F.col(c).isNull().cast("int")).alias(c) for c in silver_df.columns]
).collect()[0].asDict()
remaining_nulls = {k: v for k, v in null_counts.items() if v > 0}
print(f"Remaining nulls after cleaning: {remaining_nulls if remaining_nulls else 'none'}")

print("\nRow count comparison (Bronze admissions -> Silver):")
print(f"  admissions_bronze: {admissions_bronze.count()}")
print(f"  silver_admissions_enriched: {silver_df.count()}")

print("\nDepartment distribution (should show only canonical values):")
silver_df.groupBy("department").count().orderBy(F.desc("count")).show(truncate=False)

print("Readmission rate by age group:")
(
    silver_df.groupBy("age_group")
    .agg(F.round(F.avg("readmission_flag"), 4).alias("readmission_rate"))
    .orderBy("age_group")
    .show(truncate=False)
)
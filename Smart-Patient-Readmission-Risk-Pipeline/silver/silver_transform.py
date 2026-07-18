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

project_root = os.path.abspath("..")
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("Project root:", project_root)

from pyspark.sql import functions as F
import config as cfg
from utils.helpers import (
    log_table_stats,
    validate_no_duplicates,
    write_delta_overwrite,
)
from transformations.feature_engineering import build_silver_admissions_enriched

# Setup namespace contexts dynamically
spark.sql(f"USE CATALOG {cfg.CATALOG}")
spark.sql(f"USE SCHEMA {cfg.SCHEMA}")

# COMMAND ----------

# DBTITLE 1,Read Bronze Tables
# ────────────────────────────────────────────
# 1) Read Bronze Delta tables
# ────────────────────────────────────────────
patients_bronze = spark.table(cfg.BRONZE_PATIENTS)
diagnoses_bronze = spark.table(cfg.BRONZE_DIAGNOSES)
admissions_bronze = spark.table(cfg.BRONZE_ADMISSIONS)

print(f"Ingested patients_bronze:  {patients_bronze.count()} rows")
print(f"Ingested diagnoses_bronze: {diagnoses_bronze.count()} rows")
print(f"Ingested admissions_bronze: {admissions_bronze.count()} rows")

# COMMAND ----------

# DBTITLE 1,Build Silver Enriched Table
    # ────────────────────────────────────────────
    # 2) Clean, join, and engineer features
    # ────────────────────────────────────────────
silver_admissions_enriched = build_silver_admissions_enriched(
    patients_bronze, diagnoses_bronze, admissions_bronze
)

row_count = silver_admissions_enriched.count()
print(f"Generated silver_admissions_enriched table matrix: {row_count} rows")
silver_admissions_enriched.show(10, truncate=False)

# COMMAND ----------

# DBTITLE 1,Write Silver Delta Table
write_delta_overwrite(silver_admissions_enriched, cfg.SILVER_ADMISSIONS_ENRICHED)

print("\n" + "=" * 60)
print("SILVER LAYER ENRICHMENT COMPLETE")
print("=" * 60)
log_table_stats(spark, cfg.SILVER_ADMISSIONS_ENRICHED)

# COMMAND ----------

# DBTITLE 1,Validation and Quality Summary
# ────────────────────────────────────────────
# 4) Quality validation checks
# ────────────────────────────────────────────
silver_df = spark.table(cfg.SILVER_ADMISSIONS_ENRICHED)
validate_no_duplicates(silver_df, ["admission_id"], "silver_admissions_enriched")

null_counts = silver_df.select(
    [F.sum(F.col(c).isNull().cast("int")).alias(c) for c in silver_df.columns]
).collect()[0].asDict()
remaining_nulls = {k: v for k, v in null_counts.items() if v > 0}
print(f"Remaining tracking null vectors: {remaining_nulls if remaining_nulls else 'none'}")
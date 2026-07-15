# Architecture

## Medallion Layers

| Layer | Purpose | Tables |
|---|---|---|
| **Bronze** | Raw ingestion with intentional data quality issues preserved | `patients_bronze`, `diagnoses_bronze`, `admissions_bronze` |
| **Silver** | Cleaned, joined, feature-engineered single source of truth | `silver_admissions_enriched` |
| **Gold** | Business-level aggregations for specific analytical questions | `readmission_by_diagnosis`, `department_performance`, `age_group_risk`, `patient_risk_profile` |

## Data Flow

```
generate_data (Bronze)
  └─→ Generates synthetic patients, diagnoses, admissions
  └─→ Injects quality issues (nulls, inconsistent categoricals, date noise)
  └─→ Writes 3 Delta tables
  └─→ OPTIMIZE + ZORDER + ANALYZE

silver_transform (Silver)
  └─→ Reads 3 Bronze tables
  └─→ Cleans nulls, standardizes categoricals, deduplicates
  └─→ Broadcast-joins small dimension tables (patients, diagnoses)
  └─→ Enforces referential integrity (drops orphaned admissions)
  └─→ Engineers features via window functions
  └─→ Writes silver_admissions_enriched
  └─→ OPTIMIZE + ZORDER + ANALYZE

gold_aggregations (Gold)
  └─→ Reads silver_admissions_enriched
  └─→ Computes 4 business aggregation tables
  └─→ Uses window functions (dense_rank) for ranking
  └─→ Writes 4 Gold Delta tables
  └─→ OPTIMIZE + ZORDER + ANALYZE on all tables

sql_analytics (Analytics)
  └─→ Interactive SQL queries on Gold + Silver tables
  └─→ Dashboarding-ready outputs
```

## Module Responsibilities

| Module | Role |
|---|---|
| `config.py` | Single source of truth for catalog/schema (via widgets), table names, generation parameters, ZORDER strategy, Spark optimization settings |
| `utils/helpers.py` | Reusable: data quality injection, validation, Delta writes, OPTIMIZE/ZORDER/ANALYZE |
| `transformations/feature_engineering.py` | Composable PySpark transformation functions used by Silver |
| `bronze/generate_data.py` | Synthetic data generation with quality-issue simulation |
| `silver/silver_transform.py` | Cleaning + joining + feature engineering pipeline |
| `gold/gold_aggregations.py` | Business aggregations with window functions |
| `sql/sql_analytics.py` | SQL queries for dashboarding and ad-hoc analysis |

## Design Decisions

- **`config` resolved via Databricks widgets**, defaulting to the `workspace` catalog — this is the catalog that ships built-in on Databricks Free Edition, so the pipeline runs without requiring an external Unity Catalog metastore to be provisioned.
- **Referential integrity is enforced in Silver, not Bronze** — Bronze preserves raw data exactly as ingested (including orphaned foreign keys, if any arose), and Silver is the layer responsible for producing a single trustworthy source of truth.
- **Gold tables are pre-aggregated, not views** — each is materialized as its own Delta table so dashboards get millisecond reads instead of re-scanning Silver on every query.

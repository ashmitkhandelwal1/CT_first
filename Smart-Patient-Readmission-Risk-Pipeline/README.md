# Smart Patient Readmission Risk Pipeline

A production-grade batch data engineering pipeline built on Databricks, implementing the **Medallion Architecture** (Bronze → Silver → Gold) to transform raw hospital admission data into actionable readmission risk insights.

## Problem Statement

Hospitals generate large volumes of patient admission and discharge data daily, but this data is typically underutilized for proactive analytics. Clinical and operational teams lack structured pipelines to answer critical questions:

- **Which diagnoses** have the highest readmission rates?
- **Which departments** perform poorly (high length-of-stay + readmissions)?
- **Which patient groups** are at highest risk of readmission?
- **How does length of stay** trend over time?
- **Which individual patients** need clinical intervention to prevent readmission?

This pipeline produces analytics-ready tables that power dashboards, clinical decision support, and operational reporting.

## Architecture

```
┌─────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│  BRONZE LAYER    │     │     SILVER LAYER        │     │      GOLD LAYER         │
│                  │     │                         │     │                         │
│ Raw Ingestion    │ ──→ │ Cleaning + Enrichment   │ ──→ │ Business Aggregations   │
│ No transforms    │     │ Joins + Features        │     │ Analytics-ready         │
│ Preserve issues  │     │ Standardization         │     │ Dashboarding            │
└──────────────────┘     └─────────────────────────┘     └─────────────────────────┘
```

See [`docs/architecture.md`](docs/architecture.md) for the full layer-by-layer breakdown.

## Project Structure

```
Smart-Patient-Readmission-Risk-Pipeline/
├── config.py                              # Central configuration
├── utils/
│   └── helpers.py                         # Reusable Spark/Delta/data-quality utilities
├── transformations/
│   └── feature_engineering.py             # Composable Silver-layer transform functions
├── bronze/
│   └── generate_data.py                   # Synthetic data generation + Bronze writes
├── silver/
│   └── silver_transform.py                # Cleaning, joining, feature engineering
├── gold/
│   └── gold_aggregations.py               # Business aggregations
├── sql/
│   └── sql_analytics.py                   # Interactive SQL queries for dashboarding
└── docs/
    ├── architecture.md
    ├── bronze.md
    ├── silver.md
    ├── gold.md
    ├── workflow.md
    ├── feature_engineering.md
    ├── delta_lake.md
    ├── spark_optimizations.md
    ├── data_dictionary.md
    ├── interview_questions.md
    └── future_improvements.md
```

## Dataset Description

| Layer | Table | Key | Records | Description |
|---|---|---|---|---|
| Bronze | `patients_bronze` | `patient_id` | 200–250 | Patient demographics with intentional nulls |
| Bronze | `diagnoses_bronze` | `diagnosis_id` | 12 | ICD-10 diagnosis master data |
| Bronze | `admissions_bronze` | `admission_id` | 500–700 | Admission events with quality issues (nulls, inconsistent categoricals, date noise) |
| Silver | `silver_admissions_enriched` | `admission_id` | ~500-700 (post referential-integrity filter) | Cleaned, joined, feature-engineered, 20 columns |
| Gold | `readmission_by_diagnosis` | `diagnosis_category` | 8 | Readmission rate by diagnosis category |
| Gold | `department_performance` | `department` | 7 | Composite performance score by department |
| Gold | `age_group_risk` | `age_group` | 4 | Readmission rate by age group |
| Gold | `patient_risk_profile` | `patient_id` | ~200-250 | Per-patient risk categorization |

Full column-level detail: [`docs/data_dictionary.md`](docs/data_dictionary.md).

## How to Run

### Prerequisites
- Databricks workspace (Free Edition supported) with a Python/PySpark cluster or serverless compute attached
- Files uploaded to a Databricks Workspace folder or Git-synced Repo, matching the structure above

### Configuration

`config.py` resolves `catalog`/`schema` from Databricks widgets, defaulting to `workspace.hrm6321_aman`. `workspace` is the built-in catalog available out of the box on Databricks Free Edition — no external Unity Catalog metastore setup is required. To target a different catalog/schema, set the `catalog` and `schema` widgets when running any notebook.

### Execution Order

```
1. bronze/generate_data.py     # Generates synthetic patients/diagnoses/admissions, writes Bronze
2. silver/silver_transform.py  # Cleans + joins + engineers features, writes Silver
3. gold/gold_aggregations.py   # Computes 4 business aggregation tables, writes Gold
4. sql/sql_analytics.py        # Interactive SQL queries against Gold + Silver
```

All notebooks are **idempotent** — safe to re-run at any time (Delta overwrite mode with schema evolution).

## Validation

Every notebook in this pipeline was executed end-to-end against a local PySpark session before delivery (data generation, cleaning, joins, window functions, and aggregations all confirmed against real Spark DataFrames — see each `docs/*.md` file for the specific checks run). The only step not locally executable was the actual `OPTIMIZE`/`ZORDER` Delta command, since this sandbox has no network access to download the Delta Lake JAR; this runs natively on any real Databricks cluster.

## Future Improvements

See [`docs/future_improvements.md`](docs/future_improvements.md).

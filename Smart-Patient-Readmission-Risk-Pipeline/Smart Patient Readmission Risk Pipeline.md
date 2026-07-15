# Smart Patient Readmission Risk Pipeline

A production-grade batch data engineering pipeline built on Databricks, implementing the **Medallion Architecture** (Bronze → Silver → Gold) to transform raw hospital admission data into actionable readmission risk insights.



## Problem Statement

Hospitals generate large volumes of patient admission and discharge data daily, but this data is typically underutilized for proactive analytics. Clinical and operational teams lack structured pipelines to answer critical questions:

- **Which diagnoses** have the highest readmission rates?
- **Which departments** perform poorly (high length-of-stay + readmissions)?
- **Which patient groups** are at highest risk of readmission?
- **How does length of stay** trend over time?
- **Which individual patients** need clinical intervention to prevent readmission?

This pipeline addresses these gaps by producing analytics-ready tables that power dashboards, clinical decision support, and operational reporting.

---

## Architecture

```
┌─────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│  BRONZE LAYER   │     │     SILVER LAYER       │     │      GOLD LAYER        │
│                 │     │                         │     │                         │
│ Raw Ingestion   │ ──→ │ Cleaning + Enrichment   │ ──→ │ Business Aggregations  │
│ No transforms   │     │ Joins + Features        │     │ Analytics-ready         │
│ Preserve issues │     │ Standardization         │     │ Dashboarding            │
└─────────────────┘     └─────────────────────────┘     └─────────────────────────┘
```

### Medallion Layers

| Layer | Purpose | Tables |
|---|---|---|
| **Bronze** | Raw ingestion with intentional data quality issues preserved | `patients_bronze`, `diagnoses_bronze`, `admissions_bronze` |
| **Silver** | Cleaned, joined, feature-engineered single source of truth | `silver_admissions_enriched` |
| **Gold** | Business-level aggregations for specific analytical questions | 4 tables (see below) |

---

## Dataset Description

### Source Tables (Bronze)

| Table | Key | Records | Description |
|---|---|---|---|
| `patients_bronze` | `patient_id` | 200–250 | Patient demographics: name, age, gender, contact |
| `diagnoses_bronze` | `diagnosis_id` | 12 | ICD-10 diagnosis master data with categories |
| `admissions_bronze` | `admission_id` | 500–700 | Hospital admission events with department, physician, dates, LOS, readmission flag |

### Enriched Table (Silver)

| Table | Key | Description |
|---|---|---|
| `silver_admissions_enriched` | `admission_id` | Fully joined, cleaned, and feature-engineered dataset with 20 columns |

**Engineered Features:**
- `age_group` — Clinical buckets: 0–18, 19–35, 36–60, 60+
- `readmission_flag` — Clean binary (0/1)
- `comorbidity_index` — Count of distinct diagnoses per patient (proxy)
- `prior_admission_count` — Running count of previous admissions
- `admission_month` — Year-month for time-series analysis
- `length_of_stay` — Recomputed from dates for consistency

### Business Tables (Gold)

| Table | Business Question | Key Metric |
|---|---|---|
| `readmission_by_diagnosis` | Which diagnoses drive readmissions? | `readmission_rate` per category |
| `department_performance` | Which departments underperform? | Composite `performance_score` |
| `age_group_risk` | Which age groups are highest risk? | `readmission_rate` per age group |
| `patient_risk_profile` | Per-patient risk categorization | `risk_category` (High/Medium/Low) |

---

## Data Generation Approach

Synthetic data is generated with **realistic clinical distributions**:

- **Age distribution**: Skewed towards adults/seniors (reflecting hospital demographics)
- **Readmission probability**: Age-driven (elderly → higher) + diagnosis-driven (cardiovascular, respiratory, oncology → higher) + department effect
- **Length of stay**: Department-specific base ranges + age modifiers + category modifiers + random noise
- **Department assignment**: Weighted by diagnosis category (e.g., Cardiovascular → 72% Cardiology, 20% ICU)
- **Physician roster**: Department-specific physician lists

### Data Quality Simulation (Bronze Realism)
- **5% null injection** on name, contact, physician, and LOS columns
- **3% inconsistent categoricals** (e.g., "cardiology", "CARDIOLOGY", "Cardio")
- **2% date noise** (+/-2 day jitter on discharge dates)

---

## Pipeline Flow

```
1. generate_data (Bronze)
   └─→ Generates synthetic patients, diagnoses, admissions
   └─→ Injects quality issues
   └─→ Writes 3 Delta tables
   └─→ OPTIMIZE + ZORDER + ANALYZE

2. silver_transform (Silver)
   └─→ Reads 3 bronze tables
   └─→ Broadcast-joins small dimensions
   └─→ Applies transformation chain (cleaning + features)
   └─→ Writes silver_admissions_enriched
   └─→ OPTIMIZE + ZORDER + ANALYZE

3. gold_aggregations (Gold)
   └─→ Reads silver table
   └─→ Computes 4 business aggregation tables
   └─→ Uses window functions, CASE logic
   └─→ Writes 4 gold Delta tables
   └─→ OPTIMIZE + ZORDER + ANALYZE on all tables

4. sql_analytics (Analytics)
   └─→ Interactive SQL queries on gold tables
   └─→ Dashboarding-ready outputs
```

---

## Spark Optimization Techniques

This pipeline implements production-grade Spark optimizations across all layers:

### Adaptive Query Execution (AQE)

| Setting | Value | Purpose |
|---|---|---|
| `spark.sql.adaptive.enabled` | `true` | Runtime query plan optimization |
| `spark.sql.adaptive.coalescePartitions.enabled` | `true` | Auto-coalesce small shuffle partitions |
| `spark.sql.adaptive.skewJoin.enabled` | `true` | Handle skewed join partitions |
| `spark.sql.adaptive.skewJoin.skewedPartitionFactor` | `5` | Skew detection threshold |
| `spark.sql.adaptive.advisoryPartitionSizeInBytes` | `128m` | Target partition size post-shuffle |

### Join Optimization
- **Broadcast joins** for small dimension tables (patients: 200–250 rows, diagnoses: 12 rows)
- `spark.sql.autoBroadcastJoinThreshold` set to 10 MB
- AQE skew join handling for future data growth

### Shuffle Optimization
- `spark.sql.shuffle.partitions` = 200 (tuned for small–medium datasets)
- AQE adaptive coalescing reduces post-shuffle partitions at runtime
- Window functions use explicit `partitionBy` to minimize shuffle width

### Delta Lake Optimization

| Technique | Where Applied | Purpose |
|---|---|---|
| **Optimized Writes** | All tables | Auto file-sizing on write |
| **Auto Compaction** | All tables | Merge small files automatically |
| **OPTIMIZE** | All tables post-write | Compact files for scan performance |
| **ZORDER** | Key columns per table | Co-locate data for predicate pushdown |
| **ANALYZE TABLE** | All tables post-write | Compute statistics for query planner |
| **Schema overwrite** | All layers | Idempotent re-runs with schema evolution |

### ZORDER Configuration

| Table | ZORDER Columns |
|---|---|
| `admissions_bronze` | `patient_id`, `admission_date` |
| `silver_admissions_enriched` | `patient_id`, `admission_date`, `department` |
| `readmission_by_diagnosis` | `diagnosis_category` |
| `department_performance` | `department` |
| `patient_risk_profile` | `patient_id`, `risk_category` |

---

## Project Structure

```
Smart-Patient-Readmission-Risk-Pipeline/
├── config.py                          # Central configuration (catalog, schema, tables, optimizations)
├── README.md                          # This file
├── utils/
│   └── helpers.py                     # Data quality injection, validation, optimization utilities
├── transformations/
│   └── feature_engineering.py          # Silver layer transformation functions
├── bronze/
│   └── generate_data                  # Data generation + bronze write notebook
├── silver/
│   └── silver_transform               # Cleaning, joining, feature engineering
├── gold/
│   └── gold_aggregations              # Business metrics computation
└── analytics/
    └── sql_analytics                  # Interactive SQL queries
```

### Module Responsibilities

| Module | Role |
|---|---|
| `config.py` | Single source of truth for all paths, tables, constants, Spark optimization settings |
| `utils/helpers.py` | Reusable: data quality injection, validation, Delta writes, OPTIMIZE/ZORDER/ANALYZE |
| `transformations/feature_engineering.py` | Composable PySpark transformation functions |
| `bronze/generate_data` | Synthetic data generation with quality simulation |
| `silver/silver_transform` | Cleaning + joining + feature engineering pipeline |
| `gold/gold_aggregations` | Business aggregations with window functions |
| `analytics/sql_analytics` | SQL queries for dashboarding and ad-hoc analysis |

---

## Key Metrics

| Metric | Definition | Source Table |
|---|---|---|
| **Readmission Rate** | % of admissions where patient was readmitted within 30 days | All gold tables |
| **Performance Score** | `readmission_rate * 100 + avg_LOS * 2` (higher = worse) | `department_performance` |
| **Risk Category** | High (≥3 readmissions), Medium (1–2), Low (0) | `patient_risk_profile` |
| **Comorbidity Index** | Count of distinct diagnoses per patient | `silver_admissions_enriched` |

---

## Business Value

1. **Clinical Decision Support**: Identify high-risk patients before discharge for targeted follow-up programs
2. **Department Optimization**: Surface underperforming departments for resource reallocation and process improvement
3. **Diagnosis-Based Programs**: Design condition-specific care pathways for high-readmission diagnoses
4. **Capacity Planning**: Monthly LOS trends inform bed management and staffing decisions
5. **Cost Reduction**: Each prevented readmission saves $15K–$25K (CMS Hospital Readmissions Reduction Program)
6. **Regulatory Compliance**: Track CMS-penalized conditions and demonstrate improvement

---

## How to Run the Pipeline

### Prerequisites
- Databricks workspace with Unity Catalog enabled
- Access to catalog `learning_catalog_de_feb`, schema `hrm6321_aman`
- Python/PySpark compute (cluster or serverless)

### Execution Order

```bash
# Step 1: Generate synthetic data and write bronze tables
Run: bronze/generate_data

# Step 2: Clean, join, and engineer features
Run: silver/silver_transform

# Step 3: Compute business aggregations
Run: gold/gold_aggregations

# Step 4: Run SQL analytics (interactive)
Run: analytics/sql_analytics
```

All notebooks are **idempotent** — safe to re-run at any time (overwrite mode).

### Configuration

All paths, table names, and optimization settings are centralized in `config.py`. To point at a different catalog/schema:

```python
# config.py
CATALOG = "your_catalog"
SCHEMA = "your_schema"
```

No other files need modification.

---

## Engineering Practices

- **Idempotent writes**: All tables use Delta `overwrite` mode with schema evolution
- **AQE enabled**: Adaptive Query Execution with coalescing, skew handling across all notebooks
- **Broadcast joins**: Small dimension tables (patients, diagnoses) are broadcast-joined to avoid shuffles
- **Explicit schemas**: All DataFrames created with `StructType` schemas (not inferred)
- **Modular design**: Transformation functions are composable and testable in isolation
- **Data validation**: Duplicate key checks, referential integrity checks, null auditing at each layer
- **Configuration-driven**: Zero hardcoded paths in pipeline code; all Spark settings centralized
- **Schema enforcement**: Delta Lake enforces schema on write
- **Post-write optimization**: OPTIMIZE + ZORDER + ANALYZE TABLE on all Delta tables
- **Observability**: Logging at each layer with row counts and null summaries

---

## Future Improvements

1. **Streaming ingestion**: Replace batch generation with Auto Loader for real-time HL7/FHIR feeds
2. **ML scoring**: Train a readmission prediction model and score patients in a gold table
3. **SCD Type 2**: Track patient dimension changes over time using slowly changing dimensions
4. **Data quality framework**: Integrate Great Expectations or Spark Declarative Pipeline expectations
5. **Dashboard**: Build an AI/BI dashboard for clinical and operational stakeholders
6. **Alerting**: Trigger alerts when high-risk patient count exceeds threshold
7. **MERGE writes**: Replace overwrite with MERGE INTO for incremental processing at scale
8. **Partitioning**: Partition silver/gold tables by `admission_month` for query performance
9. **CI/CD**: Databricks Asset Bundles for deployment automation
10. **Liquid clustering**: Migrate from ZORDER to Liquid Clustering for adaptive data layout

---

## Unity Catalog Tables

All tables live in `learning_catalog_de_feb.hrm6321_aman`:

| Layer | Table | Type |
|---|---|---|
| Bronze | `patients_bronze` | Delta |
| Bronze | `diagnoses_bronze` | Delta |
| Bronze | `admissions_bronze` | Delta |
| Silver | `silver_admissions_enriched` | Delta |
| Gold | `readmission_by_diagnosis` | Delta |
| Gold | `department_performance` | Delta |
| Gold | `age_group_risk` | Delta |
| Gold | `patient_risk_profile` | Delta |
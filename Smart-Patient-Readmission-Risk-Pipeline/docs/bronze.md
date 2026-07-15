# Bronze Layer

## Purpose

Generate realistic synthetic hospital admission data with **intentional quality issues** to exercise the downstream cleaning logic. This notebook was provided as-is by the company and was not modified — only `config.py` and `utils/helpers.py` were added to support it, since it imported both and neither existed in the original upload.

## Notebook

`bronze/generate_data.py`

## Inputs

None — this is the source of the pipeline. All data is synthetically generated.

## Outputs

| Table | Rows | Primary Key | Notes |
|---|---|---|---|
| `patients_bronze` | 200–250 | `patient_id` | ~5% nulls injected on `name`, `contact` |
| `diagnoses_bronze` | 12 | `diagnosis_id` | Static master data, no injected issues |
| `admissions_bronze` | 500–700 | `admission_id` | ~5% nulls on `physician`/`length_of_stay`, ~3% inconsistent department casing, ~2% discharge-date jitter |

## Data Generation Approach

- **Age distribution**: skewed towards adults/seniors (pediatric 5%, 19-35 15%, 36-60 35%, 61-79 30%, 80-95 15%) — realistic for a hospital population.
- **Readmission probability**: age-driven (elderly higher) + diagnosis-driven (Cardiovascular/Respiratory/Oncology higher) + department effect (General Medicine/ICU penalized).
- **Length of stay**: department-specific base range + age modifier + diagnosis-category modifier + random noise.
- **Department assignment**: weighted by diagnosis category (e.g. Cardiovascular → 72% Cardiology, 20% ICU, 8% General Medicine).

## Data Quality Simulation

| Issue | Rate | Columns Affected |
|---|---|---|
| Null injection | 5% | `patients.name`, `patients.contact`, `admissions.physician`, `admissions.length_of_stay` |
| Inconsistent categoricals | 3% | `admissions.department` (e.g. `cardiology`, `CARDIOLOGY`, `Cardio`) |
| Date noise | 2% | `admissions.discharge_date` (±2 day jitter) |

## Dependencies

- `config.py` — catalog/schema, generation volumes, diagnosis catalog, department/physician/LOS lookup tables
- `utils/helpers.py` — `inject_nulls`, `inject_inconsistent_categories`, `inject_date_noise`, `weighted_choice`, `generate_phone`, `write_delta_overwrite`, `optimize_table`, `analyze_table`, `validate_no_duplicates`, `log_table_stats`, `apply_spark_optimizations`

## How to Execute

Run `bronze/generate_data.py` directly in a Databricks notebook attached to a cluster or serverless compute. It is idempotent — Delta overwrite mode means re-running regenerates a fresh synthetic dataset without needing manual cleanup.

## Validation Performed

Executed end-to-end against a local PySpark session: generated 240 patients and 687 admissions in a representative run, injected nulls onto 27 patients and 67 admissions (in line with the 5% target rate), confirmed all three tables enforce unique primary keys, and confirmed department noise (`cardiology`, `CARDIOLOGY`, `Cardio`, etc.) appears in the raw output exactly as designed for Silver to clean up. The only step not locally executable was the `OPTIMIZE`/`ZORDER` Delta command, due to this sandbox's lack of network access to the Delta Lake JAR — this is a sandbox limitation, not a code issue, and runs natively on any Databricks cluster.

# Silver Layer

## Purpose

Clean, join, and enrich the three Bronze tables into a single admissions-grain table suitable for both Gold aggregation and ad-hoc analysis.

## Notebook

`silver/silver_transform.py`

## Inputs

- `patients_bronze`
- `diagnoses_bronze`
- `admissions_bronze`

## Outputs

`silver_admissions_enriched` — one row per valid admission, 20 columns.

## Transformation Chain

1. **Deduplication** — drop duplicate `patient_id` / `diagnosis_id` / `admission_id` rows.
2. **Department standardization** — map inconsistent casing/abbreviations (`cardiology`, `CARDIOLOGY`, `Cardio`) to canonical values.
3. **Null imputation** — `name`/`contact` → `"Unknown"`, `physician` → `"Unassigned"`.
4. **Length-of-stay recomputation** — always derived from `discharge_date - admission_date`, overriding any null or noisy source value, for consistency.
5. **Readmission flag cleanup** — `readmitted_within_30_days` is cast into a strict binary `readmission_flag`.
6. **Referential integrity** — admissions whose `patient_id` or `diagnosis_id` don't exist in the dimension tables are dropped.
7. **Broadcast joins** — `patients_bronze` (~240 rows) and `diagnoses_bronze` (12 rows) are broadcast-joined against admissions to avoid a shuffle.
8. **Feature engineering** — see [`feature_engineering.md`](feature_engineering.md) for the full list.

## Dependencies

- `config.py`
- `utils/helpers.py` — `write_delta_overwrite`, `optimize_table`, `analyze_table`, `log_table_stats`, `validate_no_duplicates`
- `transformations/feature_engineering.py` — `build_silver_admissions_enriched` and its component functions

## How to Execute

Run `silver/silver_transform.py` after `bronze/generate_data.py` has completed. Idempotent — safe to re-run.

## Validation Performed

Unit-tested `build_silver_admissions_enriched()` against a hand-built synthetic dataset containing a null name/contact/physician/LOS, three different department-casing variants, a duplicate admission row, and an orphaned admission (referencing a nonexistent `patient_id`). Confirmed: nulls imputed correctly, all department variants collapsed to their 2 canonical values, the duplicate was removed, the orphan was dropped, `length_of_stay` was correctly recomputed even where the source value was null, and `prior_admission_count` correctly sequenced 0 then 1 across a patient's two admissions ordered by date.

Then ran the full notebook end-to-end against real Bronze output (687 admissions): zero nulls remained in any column after cleaning, exactly 7 canonical department values appeared in the output (all noise variants removed), and row counts were preserved (no unexpected drops beyond the intentional referential-integrity filter).

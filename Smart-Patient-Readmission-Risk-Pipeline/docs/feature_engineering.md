# Feature Engineering

All features below are computed in `transformations/feature_engineering.py` and materialized into `silver_admissions_enriched`.

## Engineered Features

| Feature | Definition | Implementation |
|---|---|---|
| `age_group` | Clinical age bucket: `0-18`, `19-35`, `36-60`, `60+` | Simple `CASE`/`when` expression on `age` |
| `admission_month` | `yyyy-MM` string, for time-series grouping | `date_format(admission_date, 'yyyy-MM')` |
| `los_bucket` | `Short` (≤2 days), `Medium` (3–7 days), `Long` (8+ days) | `CASE`/`when` on recomputed `length_of_stay` |
| `readmission_flag` | Strict binary 0/1, replacing the raw `readmitted_within_30_days` | `when(col == 1, 1).otherwise(0)` |
| `length_of_stay` | Recomputed from `discharge_date - admission_date`, overriding any null/noisy source value | `datediff(discharge_date, admission_date)` |
| `comorbidity_index` | Count of distinct diagnoses a patient has received across all their admissions (proxy for comorbidity burden) | `size(collect_set(diagnosis_id))` over a window partitioned by `patient_id` |
| `prior_admission_count` | Running count of a patient's admissions strictly before the current one, ordered by date | `count(admission_id)` over a window partitioned by `patient_id`, ordered by `admission_date`, rows between unbounded preceding and -1 |

## Window Functions Used

Two window functions do the heavy lifting for per-patient history features:

```python
# comorbidity_index: all-time distinct diagnosis count per patient
Window.partitionBy("patient_id")

# prior_admission_count: admissions strictly before the current row
Window.partitionBy("patient_id").orderBy("admission_date").rowsBetween(
    Window.unboundedPreceding, -1
)
```

The `rowsBetween(unboundedPreceding, -1)` frame is what makes `prior_admission_count` a *running* count rather than a total — a patient's first admission always gets 0, and it increments for each subsequent one.

## Why Recompute Length of Stay Instead of Trusting the Source?

`admissions_bronze.length_of_stay` has ~5% injected nulls and the `discharge_date` has ~2% injected noise (jitter). Recomputing `length_of_stay` directly from the (already-standardized) dates is more reliable than trying to impute the original column, and guarantees internal consistency between `length_of_stay`, `los_bucket`, and the two date columns downstream.

## Validation Performed

Unit-tested against a synthetic dataset engineered to exercise every edge case: a null `length_of_stay` on a patient's first admission (correctly recomputed to 8 days from the dates), two admissions for the same patient across different months (correctly sequenced `prior_admission_count` 0 → 1), and a single diagnosis per patient (`comorbidity_index` correctly evaluated to 1 for both).

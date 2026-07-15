# Bronze Layer — `generate_data`

## Purpose

The bronze layer is the entry point of the pipeline. It generates synthetic
hospital admission data that mimics what a real ingestion job would pull from
a hospital's EHR / admissions system — with the same kind of quality problems
those source systems actually produce. The goal is not just to create clean
sample data, but to create *realistic, messy* data so that the silver layer
has genuine cleaning work to do, and the whole pipeline can be demonstrated
end-to-end the way it would run against a real feed.

Bronze does no business transformation. It preserves the data as received,
quality issues included. That's the medallion contract: bronze is a raw,
auditable landing zone.

## Inputs

None. This is the origination point of the pipeline. All generation
parameters (row counts, distributions, quality-injection rates) are read
from `config.py`.

## Outputs

Three Unity Catalog Delta tables, written with `overwrite` mode so the
notebook is safe to re-run:

| Table | Grain | Approx. Rows | Primary Key |
|---|---|---|---|
| `patients_bronze` | one row per patient | 200–250 | `patient_id` |
| `diagnoses_bronze` | one row per diagnosis code | 12 (static) | `diagnosis_id` |
| `admissions_bronze` | one row per admission event | 500–700 | `admission_id` |

## Transformations

Bronze is intentionally transformation-light. What happens here is data
*generation*, not data *cleaning*:

1. **Patient generation** — age drawn from a weighted distribution skewed
   toward adults and seniors (5% pediatric, 15% young adult, 35% middle-aged,
   30% senior, 15% elderly), gender assigned with realistic proportions, name
   and contact synthesized from lookup lists.
2. **Admission generation** — each admission is assigned a random patient, a
   diagnosis (weighted by clinical prevalence), a department (weighted by
   diagnosis category via `CATEGORY_DEPARTMENT_MAP`), a physician (from the
   department's roster), an admission date within the configured window, a
   length of stay (department baseline + age modifier + category modifier +
   noise), and a readmission flag (probability driven by age and diagnosis
   category).
3. **Quality injection** — after generation, three categories of realistic
   source-system noise are layered on top:
   - **Nulls**: 5% of name/contact/physician/LOS values are blanked out.
   - **Inconsistent categoricals**: 3% of department values are replaced
     with an inconsistent casing/abbreviation variant (e.g. `"cardiology"`,
     `"CARDIOLOGY"`, `"Cardio"`).
   - **Date noise**: 2% of discharge dates are jittered by up to 2 days,
     simulating clock skew or late corrections in a source system.
4. **Explicit schema enforcement** — all three DataFrames are created from
   `StructType` schemas rather than relying on type inference, matching how
   a production ingestion job would receive typed records from an API or
   CDC feed.

## Business Logic

- **Age-driven readmission risk**: elderly patients (80+) carry a 34% base
  readmission probability, tapering down to 10% for patients under 50 —
  reflecting the clinical reality that comorbidity burden rises with age.
- **Diagnosis-driven risk**: cardiovascular, respiratory, and oncology cases
  carry an additional readmission risk premium, consistent with CMS
  Hospital Readmissions Reduction Program (HRRP) target conditions.
- **Department effect**: General Medicine and ICU are deliberately modeled
  as weaker performers (additional readmission risk) so the gold-layer
  `department_performance` table has a genuine signal to surface — this is
  what makes the "which departments underperform" business question
  answerable at all.
- **Length of stay** combines a department-specific baseline (ICU stays
  longest, General Medicine shortest) with age and diagnosis-severity
  modifiers, so LOS correlates with the same risk factors as readmission —
  as it does clinically.

## Spark Concepts Used

- **Explicit `StructType` schemas** on `createDataFrame` — avoids the cost
  and risk of schema inference on every run.
- **Adaptive Query Execution (AQE)** — enabled via `apply_spark_optimizations`
  before any DataFrame work, so partition coalescing and skew handling are
  active for the joins and aggregations run in the validation section.
- **`groupBy` + aggregate functions** (`F.avg`, `F.round`, `F.min`, `F.max`)
  for the readmission-pattern and LOS summary checks at the end of the
  notebook.
- **Broadcast-friendly design** — `patients_bronze` (≤250 rows) and
  `diagnoses_bronze` (12 rows) are small enough to be broadcast in
  downstream joins; `autoBroadcastJoinThreshold` is set accordingly in
  `config.SPARK_OPTIMIZATIONS`.

## Delta Lake Concepts Used

- **`saveAsTable` with `mode("overwrite")` + `overwriteSchema=true`** —
  idempotent, schema-evolving writes so the notebook can be re-run freely
  during development without manual table drops.
- **`OPTIMIZE ... ZORDER BY`** on `admissions_bronze`, clustered on
  `patient_id` and `admission_date` — the two columns the silver layer will
  filter and join on.
- **`ANALYZE TABLE ... COMPUTE STATISTICS`** on all three bronze tables so
  the query planner has accurate cardinality estimates for downstream joins.
- **Unity Catalog three-level namespace** (`catalog.schema.table`) via
  `config._table()`, avoiding any hardcoded paths in notebook code.

## Interview Questions

1. **Why inject data quality issues instead of generating clean data?**
   Because a pipeline that has never seen a null or an inconsistent category
   hasn't actually demonstrated any cleaning logic. Injecting realistic
   noise here lets the silver layer's deduplication, standardization, and
   null-handling be genuinely exercised and tested.

2. **Why is bronze allowed to have nulls and inconsistent values while
   silver isn't?** That's the medallion contract: bronze preserves the raw
   feed as-is for auditability and reprocessing; cleaning and enrichment is
   silver's job. If bronze pre-cleaned the data, you'd lose the ability to
   trace a downstream anomaly back to what the source system actually sent.

3. **Why use `overwrite` mode instead of `append` here?** The generator
   creates a full synthetic dataset each run, not incremental records, so
   overwrite keeps every re-run idempotent. In a real ingestion job pulling
   from a live source, this would instead be an incremental `MERGE` keyed
   on `admission_id`.

4. **Why ZORDER `admissions_bronze` on `patient_id, admission_date` and not,
   say, `department`?** ZORDER should target the columns used most often in
   downstream filter and join predicates. Silver joins on `patient_id` and
   later windows/filters on `admission_date`; `department` is lower
   cardinality and gets its own ZORDER treatment at the gold layer instead.

5. **Why explicit schemas instead of `inferSchema`?** Inference requires an
   extra read pass over the data and can silently misinterpret types (e.g.
   a numeric-looking ID column becoming a `LongType`). Explicit schemas are
   deterministic, cheaper, and match how a real ingestion contract would be
   defined against a source system.

6. **How would this change for a real hospital feed instead of synthetic
   data?** The generation cells would be replaced by an Auto Loader read
   against a landing zone (HL7/FHIR files or a CDC feed from the EHR), but
   the schema enforcement, quality injection instrumentation (replaced by
   quality *measurement*), and Delta write/optimize pattern would remain
   the same.

## Future Improvements

- Replace batch generation with Auto Loader for streaming HL7/FHIR ingestion.
- Add a `_ingested_at` and `_source_file` audit column to every bronze table.
- Move quality-injection rates into a data contract / expectations config so
  drift can be tracked run over run.
- Add row-count and null-rate assertions as a pre-silver quality gate rather
  than print statements only.
- Partition `admissions_bronze` by `admission_month` once data volume grows
  beyond a single-node OPTIMIZE's practical range.

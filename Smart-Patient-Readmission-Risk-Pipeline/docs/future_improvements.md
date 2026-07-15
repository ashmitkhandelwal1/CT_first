# Future Improvements

## Incremental Processing

The current pipeline uses full `overwrite` on every run. A production system handling continuous admissions data would move to:
- **Bronze**: `COPY INTO` or Auto Loader for incremental file ingestion instead of synthetic batch generation.
- **Silver**: `MERGE INTO` keyed on `admission_id`, so only new/changed admissions are reprocessed.
- **Gold**: incremental aggregation (e.g. Delta Live Tables materialized views, or manual delta-aware re-aggregation of only affected grouping keys) instead of full recompute.

## Partitioning

At larger scale, `silver_admissions_enriched` would benefit from partitioning by `admission_month` (already computed as a column), turning most Gold aggregation queries and the SQL analytics monthly-trend query into partition-pruned scans instead of full-table scans.

## Machine Learning Risk Scoring

`patient_risk_profile.risk_category` is currently a fixed business rule (≥3 readmissions = High). A natural next step is training a classification model (e.g. gradient-boosted trees) on the Silver table's engineered features (`age_group`, `comorbidity_index`, `los_bucket`, `department`, `category`) to predict 30-day readmission probability directly, replacing or supplementing the rule-based `risk_category` with a calibrated probability score. This would be a natural fit for Databricks' MLflow integration.

## Data Quality Monitoring

Add a dedicated data quality notebook that runs `validate_no_duplicates` and null-rate checks on every layer after each run and writes the results to a `dq_results` table, rather than only printing them to notebook output — this would let a dashboard or alert surface data quality regressions over time instead of requiring someone to read notebook logs.

## Real Source Systems

Bronze currently generates synthetic data. A real deployment would replace `generate_data.py` with actual EHR/HIS extract ingestion (e.g. HL7/FHIR feeds landed in cloud storage, ingested via Auto Loader), while keeping the same downstream Silver/Gold/SQL structure unchanged — this is precisely why the pipeline is layered the way it is.

## Power BI Dashboard

Explicitly out of scope for this phase per project instructions, but the four Gold tables are already shaped for direct Power BI (or Databricks SQL dashboard) consumption without further transformation — see `dashboard/` for scaffolding once this phase begins.

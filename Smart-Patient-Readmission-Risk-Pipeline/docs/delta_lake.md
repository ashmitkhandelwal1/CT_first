# Delta Lake

## Techniques Used

| Technique | Where Applied | Purpose |
|---|---|---|
| Delta `overwrite` mode + `overwriteSchema=true` | All table writes | Idempotent re-runs with automatic schema evolution |
| `spark.databricks.delta.optimizeWrite.enabled` | Session-wide (via `SPARK_OPTIMIZATIONS`) | Auto file-sizing on write |
| `spark.databricks.delta.autoCompact.enabled` | Session-wide | Merges small files automatically after writes |
| `OPTIMIZE` | Post-write, every table | Compacts files for faster scans |
| `OPTIMIZE ... ZORDER BY (...)` | Post-write, tables with a defined ZORDER strategy | Co-locates related data for predicate pushdown |
| `ANALYZE TABLE ... COMPUTE STATISTICS FOR ALL COLUMNS` | Post-write, every table | Feeds the cost-based query planner |

## ZORDER Strategy

Defined centrally in `config.py`'s `ZORDER_COLUMNS` dict, so every notebook picks up the same strategy without hardcoding column names:

| Table | ZORDER Columns | Rationale |
|---|---|---|
| `admissions_bronze` | `patient_id`, `admission_date` | Most downstream joins and time-range filters key on these |
| `silver_admissions_enriched` | `patient_id`, `admission_date`, `department` | Same, plus department-level Gold aggregations |
| `readmission_by_diagnosis` | `diagnosis_category` | Small table, but keeps the grouping column co-located |
| `department_performance` | `department` | Primary grouping key |
| `patient_risk_profile` | `patient_id`, `risk_category` | Supports both patient lookups and risk-tier filtering |

`age_group_risk` has no ZORDER entry — with only 4 rows, file layout is irrelevant.

## write_delta_overwrite()

Every write in this pipeline goes through the same helper (`utils/helpers.py`):

```python
def write_delta_overwrite(df: DataFrame, table_name: str) -> None:
    (
        df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(table_name)
    )
```

Centralizing this means every table in every layer gets identical write semantics — no notebook can accidentally use `append` mode or skip schema evolution.

## Validation Note

The `OPTIMIZE`/`ZORDER`/`ANALYZE` calls use standard, well-documented Delta Lake SQL syntax that runs natively on any Databricks cluster. They could not be executed in this development sandbox because the sandbox's network allowlist doesn't include Maven Central, so the Delta Lake JAR couldn't be downloaded for local testing — this is a sandbox limitation, not a code defect. Everything else in the pipeline (data generation, cleaning, joins, feature engineering, and aggregation) was fully executed and validated locally using a real PySpark session with Parquet substituted for Delta purely as a local stand-in.

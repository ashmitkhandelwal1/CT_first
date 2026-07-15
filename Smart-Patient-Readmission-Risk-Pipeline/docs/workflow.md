# Workflow

## Execution Order

The pipeline must be run in this order — each notebook depends on the Delta table(s) written by the previous one:

```
1. bronze/generate_data.py
2. silver/silver_transform.py
3. gold/gold_aggregations.py
4. sql/sql_analytics.py
```

## Running in Databricks

1. Upload or Git-sync this project to a Databricks Workspace folder, preserving the directory structure exactly (the shared modules `config.py`, `utils/helpers.py`, and `transformations/feature_engineering.py` are imported by relative path from each notebook).
2. Attach the notebooks to a cluster or serverless compute with PySpark available (any standard Databricks runtime).
3. Run each notebook in order, either manually or via a Databricks Job with four sequential tasks.
4. Optionally set the `catalog` / `schema` widgets on any notebook before running to target a different Unity Catalog location (defaults to `workspace.hrm6321_aman`).

## Idempotency

Every write in this pipeline uses Delta `overwrite` mode with `overwriteSchema=true`. This means:
- Re-running any notebook regenerates that notebook's table(s) from scratch — safe to re-run after a failure without manual cleanup.
- Schema changes (e.g. adding a new engineered feature column) are automatically picked up on the next run.
- There is no incremental/MERGE logic in this version — see [`future_improvements.md`](future_improvements.md) for the planned upgrade path.

## Orchestration as a Databricks Job

Recommended job configuration: 4 sequential tasks, one per notebook, each depending on the previous task's success. This gives per-layer retry granularity and a clear DAG view of the medallion flow in the Jobs UI.

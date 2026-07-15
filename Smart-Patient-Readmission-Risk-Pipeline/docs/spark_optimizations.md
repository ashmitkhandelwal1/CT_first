# Spark Optimizations

All settings below live in `config.py`'s `SPARK_OPTIMIZATIONS` dict and are applied once per notebook via `apply_spark_optimizations(spark, cfg.SPARK_OPTIMIZATIONS)`.

## Adaptive Query Execution (AQE)

| Setting | Value | Purpose |
|---|---|---|
| `spark.sql.adaptive.enabled` | `true` | Runtime query plan optimization |
| `spark.sql.adaptive.coalescePartitions.enabled` | `true` | Auto-coalesce small shuffle partitions |
| `spark.sql.adaptive.skewJoin.enabled` | `true` | Handle skewed join partitions |
| `spark.sql.adaptive.skewJoin.skewedPartitionFactor` | `5` | Skew detection threshold |
| `spark.sql.adaptive.advisoryPartitionSizeInBytes` | `128m` | Target partition size post-shuffle |

## Join Optimization

- `spark.sql.autoBroadcastJoinThreshold` set to 10 MB.
- Both dimension tables in this pipeline are far under that threshold (`patients_bronze` ~240 rows, `diagnoses_bronze` 12 rows), so Silver's joins against them are explicitly broadcast via `F.broadcast(...)` rather than relying solely on auto-detection — this makes the optimization visible in the query plan and guarantees it regardless of the auto-threshold's cost estimate.

## Shuffle Optimization

- `spark.sql.shuffle.partitions` = 200, tuned for this pipeline's small-to-medium data volumes (a few hundred to a few thousand rows per table).
- AQE's `coalescePartitions` reduces the actual post-shuffle partition count at runtime regardless of this static setting.
- Window functions (`comorbidity_index`, `prior_admission_count`, and all Gold ranking columns) use explicit `partitionBy` to keep shuffle width minimal.

## Why These Settings for This Data Volume?

This pipeline's tables are small (hundreds to low thousands of rows). The settings are chosen to be safe defaults that scale gracefully rather than hand-tuned for this exact volume — the same `config.py` will keep working sensibly if `NUM_ADMISSIONS` in a future run is bumped from ~700 to ~700,000.

## Validation Performed

`apply_spark_optimizations()` was executed against a real local `SparkSession` and confirmed to set all 9 configuration keys without error. The broadcast joins in `build_silver_admissions_enriched()` were exercised as part of the full Silver notebook test run.

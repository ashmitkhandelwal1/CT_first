"""
Shared utilities for the Smart Patient Readmission Risk Pipeline.

Covers three concerns used across all layers:
  - Synthetic data quality injection (nulls, inconsistent categories, date noise)
  - Delta Lake write / optimize / analyze helpers
  - Validation helpers (duplicate keys, table stats)
"""

import random
from datetime import datetime, timedelta

from pyspark.sql import DataFrame, SparkSession


def apply_spark_optimizations(spark: SparkSession, optimizations: dict) -> None:
    """Apply a dict of Spark SQL conf settings to the active session."""
    for key, value in optimizations.items():
        spark.conf.set(key, value)
    print(f"Applied {len(optimizations)} Spark optimization settings")


def write_delta_overwrite(df: DataFrame, table_name: str) -> None:
    """Idempotent overwrite write to a Delta table with schema evolution."""
    (
        df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(table_name)
    )
    print(f"Wrote {df.count()} rows to {table_name}")


def optimize_table(spark: SparkSession, table_name: str, zorder_cols: list = None) -> None:
    """Run Delta OPTIMIZE, optionally with ZORDER BY the given columns."""
    if zorder_cols:
        cols = ", ".join(zorder_cols)
        spark.sql(f"OPTIMIZE {table_name} ZORDER BY ({cols})")
        print(f"OPTIMIZE + ZORDER({cols}) complete: {table_name}")
    else:
        spark.sql(f"OPTIMIZE {table_name}")
        print(f"OPTIMIZE complete: {table_name}")


def analyze_table(spark: SparkSession, table_name: str) -> None:
    """Compute table statistics for the query planner."""
    spark.sql(f"ANALYZE TABLE {table_name} COMPUTE STATISTICS FOR ALL COLUMNS")
    print(f"ANALYZE complete: {table_name}")


def log_table_stats(spark: SparkSession, table_name: str) -> None:
    """Print row count and schema for a Delta table."""
    df = spark.table(table_name)
    print(f"{table_name}: {df.count()} rows, {len(df.columns)} columns")
    df.printSchema()


def validate_no_duplicates(df: DataFrame, key_cols: list, table_name: str) -> bool:
    """Check a DataFrame for duplicate values across key_cols; log the result."""
    total = df.count()
    distinct = df.select(*key_cols).distinct().count()
    is_clean = total == distinct
    status = "PASS" if is_clean else "FAIL"
    print(f"[{status}] {table_name}: {total} rows, {distinct} distinct keys on {key_cols}")
    return is_clean


def weighted_choice(weight_map: dict):
    """Pick a single key from a dict of {value: weight} using weighted random choice."""
    values = list(weight_map.keys())
    weights = list(weight_map.values())
    return random.choices(values, weights=weights, k=1)[0]


def generate_phone() -> str:
    """Generate a synthetic 10-digit Indian-style mobile number."""
    prefix = random.choice(["6", "7", "8", "9"])
    rest = "".join(str(random.randint(0, 9)) for _ in range(9))
    return prefix + rest


def inject_nulls(rows: list, col_indices: list, rate: float) -> list:
    """Randomly null out values at the given column indices in a fraction of rows."""
    result = []
    for row in rows:
        row = list(row)
        for idx in col_indices:
            if random.random() < rate:
                row[idx] = None
        result.append(row)
    return result


def inject_inconsistent_categories(
    rows: list,
    col_idx: int,
    valid_values: tuple,
    noise_map: dict,
    rate: float,
) -> list:
    """Replace a fraction of a categorical column's values with noisy variants."""
    result = []
    for row in rows:
        row = list(row)
        value = row[col_idx]
        if value in noise_map and random.random() < rate:
            row[col_idx] = random.choice(noise_map[value])
        result.append(row)
    return result


def inject_date_noise(rows: list, col_idx: int, max_jitter_days: int, rate: float) -> list:
    """Jitter a fraction of an ISO date-string column by up to max_jitter_days."""
    result = []
    for row in rows:
        row = list(row)
        if random.random() < rate:
            jitter = random.randint(-max_jitter_days, max_jitter_days)
            original = datetime.strptime(row[col_idx], "%Y-%m-%d").date()
            row[col_idx] = (original + timedelta(days=jitter)).isoformat()
        result.append(row)
    return result

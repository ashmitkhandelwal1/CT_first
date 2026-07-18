"""
Composable PySpark transformation functions for the Silver layer.

Each function takes a DataFrame and returns a DataFrame, so they can be
chained via `.transform()` in silver/silver_transform.py.
"""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window

DEPARTMENT_CANONICALIZATION = {
    "cardiology": "Cardiology",
    "cardio": "Cardiology",
    "general medicine": "General Medicine",
    "gen medicine": "General Medicine",
    "gen. medicine": "General Medicine",
    "orthopedics": "Orthopedics",
    "ortho": "Orthopedics",
    "neurology": "Neurology",
    "neuro": "Neurology",
    "oncology": "Oncology",
    "onco": "Oncology",
    "pulmonology": "Pulmonology",
    "pulmo": "Pulmonology",
    "icu": "ICU",
}

def clean_patients(patients_df: DataFrame) -> DataFrame:
    """Impute missing patient demographics and drop duplicate patient_id rows."""
    return (
        patients_df.dropDuplicates(["patient_id"])
        .withColumn("name", F.coalesce(F.col("name"), F.lit("Unknown")))
        .withColumn("contact", F.coalesce(F.col("contact"), F.lit("Unknown")))
    )

def clean_diagnoses(diagnoses_df: DataFrame) -> DataFrame:
    """Drop duplicate diagnosis_id rows."""
    return diagnoses_df.dropDuplicates(["diagnosis_id"])

def standardize_department(admissions_df: DataFrame) -> DataFrame:
    """Normalize inconsistent department casing/abbreviations to canonical values."""
    mapping_expr = F.create_map(
        [F.lit(x) for pair in DEPARTMENT_CANONICALIZATION.items() for x in pair]
    )
    normalized = F.lower(F.trim(F.col("department")))
    return admissions_df.withColumn(
        "department",
        F.coalesce(mapping_expr[normalized], F.col("department")),
    )

def clean_admissions(admissions_df: DataFrame) -> DataFrame:
    """Impute missing physician values and drop duplicate admission_id rows."""
    return (
        admissions_df.dropDuplicates(["admission_id"])
        .transform(standardize_department)
        .withColumn("physician", F.coalesce(F.col("physician"), F.lit("Unassigned")))
    )

def recompute_length_of_stay(admissions_df: DataFrame) -> DataFrame:
    """Recompute length_of_stay from admission/discharge dates for consistency,
    overriding any null or noisy source value."""
    return admissions_df.withColumn(
        "length_of_stay",
        F.datediff(F.col("discharge_date"), F.col("admission_date")).cast("int"),
    )

def add_readmission_flag(admissions_df: DataFrame) -> DataFrame:
    """Clean readmitted_within_30_days into a strict binary readmission_flag."""
    return admissions_df.withColumn(
        "readmission_flag",
        F.when(F.col("readmitted_within_30_days") == 1, 1).otherwise(0),
    ).drop("readmitted_within_30_days")

def add_age_group(df: DataFrame) -> DataFrame:
    """Bucket patients into clinical age groups."""
    return df.withColumn(
        "age_group",
        F.when(F.col("age") <= 18, "0-18")
        .when(F.col("age") <= 35, "19-35")
        .when(F.col("age") <= 60, "36-60")
        .otherwise("60+"),
    )

def add_admission_month(df: DataFrame) -> DataFrame:
    """Derive year-month for time-series analysis."""
    return df.withColumn("admission_month", F.date_format("admission_date", "yyyy-MM"))

def add_los_bucket(df: DataFrame) -> DataFrame:
    """Bucket length of stay into short/medium/long stay categories."""
    return df.withColumn(
        "los_bucket",
        F.when(F.col("length_of_stay") <= 2, "Short")
        .when(F.col("length_of_stay") <= 7, "Medium")
        .otherwise("Long"),
    )

def add_comorbidity_index(df: DataFrame) -> DataFrame:
    """Count of distinct diagnoses per patient across all admissions, as a
    proxy for comorbidity burden."""
    window = Window.partitionBy("patient_id")
    return df.withColumn(
        "comorbidity_index", F.size(F.collect_set("diagnosis_id").over(window))
    )

def add_prior_admission_count(df: DataFrame) -> DataFrame:
    """Running count of a patient's admissions strictly before the current one,
    ordered by admission_date."""
    window = (
        Window.partitionBy("patient_id")
        .orderBy("admission_date")
        .rowsBetween(Window.unboundedPreceding, -1)
    )
    return df.withColumn("prior_admission_count", F.count("admission_id").over(window))

def validate_referential_integrity(
    admissions_df: DataFrame, patients_df: DataFrame, diagnoses_df: DataFrame
) -> DataFrame:
    """Keep only admissions whose patient_id and diagnosis_id exist in the
    dimension tables, dropping orphaned records."""
    valid_patients = patients_df.select("patient_id")
    valid_diagnoses = diagnoses_df.select("diagnosis_id")
    return admissions_df.join(valid_patients, "patient_id", "inner").join(
        valid_diagnoses, "diagnosis_id", "inner"
    )

def build_silver_admissions_enriched(
    patients_df: DataFrame, diagnoses_df: DataFrame, admissions_df: DataFrame
) -> DataFrame:
    """Full Silver transformation chain: clean, join, and engineer features
    to produce the single enriched admissions table."""
    patients_clean = clean_patients(patients_df)
    diagnoses_clean = clean_diagnoses(diagnoses_df)
    admissions_clean = (
        clean_admissions(admissions_df)
        .transform(recompute_length_of_stay)
        .transform(add_readmission_flag)
    )

    admissions_valid = validate_referential_integrity(
        admissions_clean, patients_clean, diagnoses_clean
    )

    enriched = (
        admissions_valid.join(F.broadcast(patients_clean), "patient_id", "inner")
        .join(F.broadcast(diagnoses_clean), "diagnosis_id", "inner")
        .transform(add_age_group)
        .transform(add_admission_month)
        .transform(add_los_bucket)
        .transform(add_comorbidity_index)
        .transform(add_prior_admission_count)
    )

    return enriched.select(
        "admission_id",
        "patient_id",
        "diagnosis_id",
        "department",
        "physician",
        "admission_date",
        "discharge_date",
        "length_of_stay",
        "readmission_flag",
        "name",
        "age",
        "gender",
        "contact",
        "icd_code",
        "category",
        "age_group",
        "admission_month",
        "los_bucket",
        "comorbidity_index",
        "prior_admission_count",
    )
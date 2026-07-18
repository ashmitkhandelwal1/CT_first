# Databricks notebook source
# Databricks notebook source
import os
import sys
from datetime import date, timedelta
import random

# Allow importing from the root configuration directory
project_root = os.path.abspath("..")
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("Project root:", project_root)

from pyspark.sql import functions as F
from pyspark.sql import types as T
import config as cfg
from utils.helpers import (
    inject_nulls,
    inject_inconsistent_categories,
    inject_date_noise,
    weighted_choice,
    generate_phone,
    log_table_stats,
    validate_no_duplicates,
    write_delta_overwrite,
)

random.seed(cfg.RANDOM_SEED)

# Ensure schema targeting matches local catalog configuration
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {cfg.CATALOG}.{cfg.SCHEMA}")
print(f"\nUsing Environment Workspace Namespace: {cfg.CATALOG}.{cfg.SCHEMA}")

# COMMAND ----------

# DBTITLE 1,Generate Patient Records
FIRST_NAMES_M = [
    "Rahul", "Amit", "Vikram", "Suresh", "Rajesh", "Arjun", "Kiran", "Manoj",
    "Deepak", "Sanjay", "Anil", "Ravi", "Nitin", "Pankaj", "Gaurav",
    "Ashok", "Vijay", "Pradeep", "Sandeep", "Naveen", "Rakesh", "Mukesh",
]
FIRST_NAMES_F = [
    "Priya", "Anita", "Sunita", "Kavita", "Neha", "Pooja", "Meera", "Swati",
    "Asha", "Rekha", "Divya", "Nisha", "Ritu", "Seema", "Jyoti",
    "Shalini", "Geeta", "Lata", "Sarita", "Padma", "Usha", "Radha",
]
LAST_NAMES = [
    "Sharma", "Patel", "Singh", "Kumar", "Gupta", "Reddy", "Mehta",
    "Verma", "Joshi", "Nair", "Das", "Roy", "Sen", "Bhat", "Rao",
    "Iyer", "Pillai", "Chatterjee", "Ghosh", "Banerjee", "Mishra",
    "Tiwari", "Pandey", "Saxena", "Kapoor", "Deshmukh", "Kulkarni",
]

num_patients = random.randint(*cfg.NUM_PATIENTS)
patients = []

for i in range(1, num_patients + 1):
    age_bucket = random.random()
    if age_bucket < 0.05:
        age = random.randint(1, 18)
    elif age_bucket < 0.20:
        age = random.randint(19, 35)
    elif age_bucket < 0.55:
        age = random.randint(36, 60)
    elif age_bucket < 0.85:
        age = random.randint(61, 79)
    else:
        age = random.randint(80, 95)

    gender = random.choices(["F", "M", "Other"], weights=[0.49, 0.49, 0.02], k=1)[0]

    if gender == "F":
        first = random.choice(FIRST_NAMES_F)
    else:
        first = random.choice(FIRST_NAMES_M)
    last = random.choice(LAST_NAMES)
    name = f"{first} {last}"

    contact = generate_phone()
    patients.append([f"P{str(i).zfill(5)}", name, age, gender, contact])

print(f"Generated {len(patients)} patients")

# COMMAND ----------

# DBTITLE 1,Diagnosis Master Data
# ────────────────────────────────────────────
# 2) Diagnoses are static master data from config
# ────────────────────────────────────────────
diagnosis_rows = list(cfg.DIAGNOSIS_CATALOG)
diagnoses_by_id = {d[0]: {"icd_code": d[1], "category": d[2]} for d in diagnosis_rows}
diag_ids = [d[0] for d in diagnosis_rows]

# COMMAND ----------

# DBTITLE 1,Generate Admission Records
# ────────────────────────────────────────────
# 3) Generate admissions (500-700 records)
# ────────────────────────────────────────────
num_admissions = random.randint(*cfg.NUM_ADMISSIONS)
start_date = date.today() - timedelta(days=cfg.DATA_WINDOW_DAYS)
patients_by_id = {p[0]: {"age": p[2], "gender": p[3]} for p in patients}

admissions = []
for i in range(1, num_admissions + 1):
    admission_id = f"A{str(i).zfill(6)}"
    patient_id = random.choice(patients)[0]
    diagnosis_id = random.choices(diag_ids, weights=cfg.DIAGNOSIS_WEIGHTS, k=1)[0]

    age = patients_by_id[patient_id]["age"]
    category = diagnoses_by_id[diagnosis_id]["category"]

    department = weighted_choice(cfg.CATEGORY_DEPARTMENT_MAP[category])
    physician = random.choice(cfg.PHYSICIANS.get(department, ["Dr. Unknown"]))
    admission_date = start_date + timedelta(days=random.randint(0, cfg.DATA_WINDOW_DAYS - 1))

    los_range = cfg.BASE_LOS_RANGES.get(department, (1, 6))
    base_los = random.randint(*los_range)
    age_modifier = 2 if age >= 80 else (1 if age >= 65 else 0)
    category_modifier = 2 if category in ("Cardiovascular", "Oncology", "Infectious") else 0
    length_of_stay = max(1, base_los + age_modifier + category_modifier + random.randint(-1, 2))

    discharge_date = admission_date + timedelta(days=length_of_stay)

    if age >= 80:
        readmit_prob = 0.34
    elif age >= 65:
        readmit_prob = 0.26
    elif age >= 50:
        readmit_prob = 0.18
    else:
        readmit_prob = 0.10

    if category in ("Cardiovascular", "Respiratory", "Oncology"):
        readmit_prob += 0.06
    if department in ("General Medicine", "ICU"):
        readmit_prob += 0.04

    readmitted_within_30_days = 1 if random.random() < min(readmit_prob, 0.55) else 0

    admissions.append([
        admission_id,
        patient_id,
        diagnosis_id,
        department,
        physician,
        admission_date.isoformat(),
        discharge_date.isoformat(),
        length_of_stay,
        readmitted_within_30_days,
    ])

print(f"Generated {len(admissions)} admissions")

# COMMAND ----------

# DBTITLE 1,Inject Data Quality Issues
# ────────────────────────────────────────────
# 4) Inject data quality issues into raw data
# ────────────────────────────────────────────
# Simulate real-world source system problems
patients = inject_nulls(patients, col_indices=[1, 4], rate=cfg.NULL_INJECTION_RATE)
admissions = inject_nulls(admissions, col_indices=[4, 7], rate=cfg.NULL_INJECTION_RATE)

dept_noise = {
    "Cardiology":       ["cardiology", "CARDIOLOGY", "Cardio"],
    "General Medicine": ["general medicine", "Gen Medicine", "Gen. Medicine"],
    "Orthopedics":      ["orthopedics", "ORTHOPEDICS", "Ortho"],
    "Neurology":        ["neurology", "NEUROLOGY", "Neuro"],
    "Oncology":         ["oncology", "ONCOLOGY", "Onco"],
    "Pulmonology":      ["pulmonology", "Pulmo"],
    "ICU":              ["icu"],
}
admissions = inject_inconsistent_categories(
    admissions, col_idx=3,
    valid_values=cfg.DEPARTMENTS,
    noise_map=dept_noise,
    rate=cfg.INCONSISTENT_CATEGORY_RATE,
)

admissions = inject_date_noise(
    admissions, col_idx=6,
    max_jitter_days=cfg.DATE_NOISE_DAYS,
    rate=0.02,
)

# COMMAND ----------

# DBTITLE 1,Create Spark DataFrames with Explicit Schemas
patients_schema = T.StructType([
    T.StructField("patient_id", T.StringType(), False),
    T.StructField("name", T.StringType(), True),
    T.StructField("age", T.IntegerType(), True),
    T.StructField("gender", T.StringType(), True),
    T.StructField("contact", T.StringType(), True),
])

diagnoses_schema = T.StructType([
    T.StructField("diagnosis_id", T.StringType(), False),
    T.StructField("icd_code", T.StringType(), False),
    T.StructField("category", T.StringType(), False),
])

admissions_schema = T.StructType([
    T.StructField("admission_id", T.StringType(), False),
    T.StructField("patient_id", T.StringType(), False),
    T.StructField("diagnosis_id", T.StringType(), False),
    T.StructField("department", T.StringType(), True),
    T.StructField("physician", T.StringType(), True),
    T.StructField("admission_date", T.StringType(), True),
    T.StructField("discharge_date", T.StringType(), True),
    T.StructField("length_of_stay", T.IntegerType(), True),
    T.StructField("readmitted_within_30_days", T.IntegerType(), True),
])

patients_df = spark.createDataFrame(patients, schema=patients_schema)
diagnoses_df = spark.createDataFrame(diagnosis_rows, schema=diagnoses_schema)
admissions_df = (
    spark.createDataFrame(admissions, schema=admissions_schema)
    .withColumn("admission_date", F.to_date("admission_date"))
    .withColumn("discharge_date", F.to_date("discharge_date"))
)

# COMMAND ----------

# DBTITLE 1,Write Bronze Delta Tables
# ────────────────────────────────────────────
# 6) Write Bronze Delta tables (overwrite = idempotent)
# ────────────────────────────────────────────
write_delta_overwrite(patients_df, cfg.BRONZE_PATIENTS)
write_delta_overwrite(diagnoses_df, cfg.BRONZE_DIAGNOSES)
write_delta_overwrite(admissions_df, cfg.BRONZE_ADMISSIONS)

print("\n" + "="*60)
print("BRONZE LAYER WRITE COMPLETE")
print("="*60)
log_table_stats(spark, cfg.BRONZE_PATIENTS)
log_table_stats(spark, cfg.BRONZE_DIAGNOSES)
log_table_stats(spark, cfg.BRONZE_ADMISSIONS)

# COMMAND ----------

# DBTITLE 1,Validation and Quality Summary
# ────────────────────────────────────────────
# 7) Quality validation checks
# ────────────────────────────────────────────
validate_no_duplicates(patients_df, ["patient_id"], "patients_bronze")
validate_no_duplicates(diagnoses_df, ["diagnosis_id"], "diagnoses_bronze")
validate_no_duplicates(admissions_df, ["admission_id"], "admissions_bronze")

print("\nReadmission pattern (age-based):")
admissions_df \
    .join(patients_df, "patient_id") \
    .groupBy(
        F.when(F.col("age") >= 65, "elderly")
        .otherwise("non_elderly")
        .alias("age_group")
    ) \
    .agg(F.round(F.avg("readmitted_within_30_days"), 4).alias("readmission_rate")) \
    .show(truncate=False)
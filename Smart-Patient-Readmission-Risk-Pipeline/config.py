"""
Central configuration for the Smart Patient Readmission Risk Pipeline.

Single source of truth for catalog/schema targeting, table names,
data generation parameters, and Spark/Delta optimization settings.
Refactored for Databricks Free Edition & Spark Connect compatibility.
"""

from pyspark.sql import SparkSession

# ── Safe Widget & Environment Resolution ──
try:
    # Access the runtime utility framework safely in serverless environments
    from databricks.sdk.runtime import dbutils
    
    dbutils.widgets.text("catalog", "workspace")
    dbutils.widgets.text("schema", "ashmit_readmission")
    CATALOG = dbutils.widgets.get("catalog")
    SCHEMA = dbutils.widgets.get("schema")
except Exception:
    try:
        # Fallback to globally bound namespace inside notebook scope
        CATALOG = dbutils.widgets.get("catalog")
        SCHEMA = dbutils.widgets.get("schema")
    except Exception:
        # Fallback for local testing and static linting
        CATALOG = "workspace"
        SCHEMA = "ashmit_readmission"

RANDOM_SEED = 42

# ── Data generation volumes ──
NUM_PATIENTS = (200, 250)
NUM_ADMISSIONS = (500, 700)
DATA_WINDOW_DAYS = 365

# ── Data quality injection rates ──
NULL_INJECTION_RATE = 0.05
INCONSISTENT_CATEGORY_RATE = 0.03
DATE_NOISE_DAYS = 2

# ── Diagnosis master data: (diagnosis_id, icd_code, category) ──
DIAGNOSIS_CATALOG = (
    ("D001", "I50.9", "Cardiovascular"),
    ("D002", "I21.9", "Cardiovascular"),
    ("D003", "J44.9", "Respiratory"),
    ("D004", "J18.9", "Respiratory"),
    ("D005", "G45.9", "Neurological"),
    ("D006", "I63.9", "Neurological"),
    ("D007", "M17.9", "Orthopedic"),
    ("D008", "S72.0", "Orthopedic"),
    ("D009", "C34.9", "Oncology"),
    ("D010", "A41.9", "Infectious"),
    ("D011", "K92.2", "Gastrointestinal"),
    ("D012", "E11.9", "Endocrine"),
)

# Relative sampling weights, same order as DIAGNOSIS_CATALOG
DIAGNOSIS_WEIGHTS = (14, 10, 12, 10, 8, 6, 10, 6, 5, 6, 7, 6)

# ── Departments (canonical, clean values) ──
DEPARTMENTS = (
    "Cardiology",
    "General Medicine",
    "Orthopedics",
    "Neurology",
    "Oncology",
    "Pulmonology",
    "ICU",
)

# Diagnosis category -> department sampling weights
CATEGORY_DEPARTMENT_MAP = {
    "Cardiovascular": {"Cardiology": 0.72, "ICU": 0.20, "General Medicine": 0.08},
    "Respiratory": {"Pulmonology": 0.65, "ICU": 0.20, "General Medicine": 0.15},
    "Neurological": {"Neurology": 0.80, "ICU": 0.10, "General Medicine": 0.10},
    "Orthopedic": {"Orthopedics": 0.90, "General Medicine": 0.10},
    "Oncology": {"Oncology": 0.85, "ICU": 0.10, "General Medicine": 0.05},
    "Infectious": {"General Medicine": 0.55, "ICU": 0.30, "Pulmonology": 0.15},
    "Gastrointestinal": {"General Medicine": 0.80, "ICU": 0.20},
    "Endocrine": {"General Medicine": 0.85, "ICU": 0.15},
}

# Department -> physician roster
PHYSICIANS = {
    "Cardiology": ["Dr. Malhotra", "Dr. Chawla", "Dr. Bose"],
    "General Medicine": ["Dr. Iyer", "Dr. Rathi", "Dr. Sengupta"],
    "Orthopedics": ["Dr. Menon", "Dr. Trivedi"],
    "Neurology": ["Dr. Kulkarni", "Dr. Bhattacharya"],
    "Oncology": ["Dr. Desai", "Dr. Krishnan"],
    "Pulmonology": ["Dr. Ahluwalia", "Dr. Narayanan"],
    "ICU": ["Dr. Suri", "Dr. Ramaswamy", "Dr. Bakshi"],
}

# Department -> (min, max) base length-of-stay in days
BASE_LOS_RANGES = {
    "Cardiology": (2, 6),
    "General Medicine": (1, 4),
    "Orthopedics": (3, 8),
    "Neurology": (2, 7),
    "Oncology": (3, 9),
    "Pulmonology": (2, 6),
    "ICU": (4, 10),
}

# ── Delta table paths (fully qualified, resolved after CATALOG/SCHEMA) ──
BRONZE_PATIENTS = f"{CATALOG}.{SCHEMA}.patients_bronze"
BRONZE_DIAGNOSES = f"{CATALOG}.{SCHEMA}.diagnoses_bronze"
BRONZE_ADMISSIONS = f"{CATALOG}.{SCHEMA}.admissions_bronze"

SILVER_ADMISSIONS_ENRICHED = f"{CATALOG}.{SCHEMA}.silver_admissions_enriched"

GOLD_READMISSION_BY_DIAGNOSIS = f"{CATALOG}.{SCHEMA}.readmission_by_diagnosis"
GOLD_DEPARTMENT_PERFORMANCE = f"{CATALOG}.{SCHEMA}.department_performance"
GOLD_AGE_GROUP_RISK = f"{CATALOG}.{SCHEMA}.age_group_risk"
GOLD_PATIENT_RISK_PROFILE = f"{CATALOG}.{SCHEMA}.patient_risk_profile"

# ── Spark Connect Compatible Metadata Structures ──
# Maintained as empty lists/dictionaries to prevent down-stream script compilation errors
ZORDER_COLUMNS = {
    BRONZE_ADMISSIONS: [],
    SILVER_ADMISSIONS_ENRICHED: [],
    GOLD_READMISSION_BY_DIAGNOSIS: [],
    GOLD_DEPARTMENT_PERFORMANCE: [],
    GOLD_PATIENT_RISK_PROFILE: [],
}

# Cluster-level optimization strings removed to prevent serverless execution crashes
SPARK_OPTIMIZATIONS = {}
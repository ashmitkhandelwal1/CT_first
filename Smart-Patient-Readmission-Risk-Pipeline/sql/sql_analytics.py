# Databricks notebook source
# DBTITLE 1,SQL Analytics Overview
# MAGIC %md
# MAGIC # SQL Analytics — Interactive Queries
# MAGIC
# MAGIC Ad-hoc and dashboarding-ready SQL queries against the Gold tables (and Silver
# MAGIC where a Gold table doesn't already cover the question, e.g. monthly trends).
# MAGIC
# MAGIC **Reads**: `readmission_by_diagnosis`, `department_performance`, `age_group_risk`,
# MAGIC `patient_risk_profile`, `silver_admissions_enriched`
# MAGIC
# MAGIC **Writes**: none — this notebook is read-only / interactive.

# COMMAND ----------

# DBTITLE 1,Configuration
import sys, os, importlib

PROJECT_ROOT = "/Workspace/Users/ashmitkhandelwal58@gmail.com/CT_first/Smart-Patient-Readmission-Risk-Pipeline"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

for mod_name in list(sys.modules.keys()):
    if mod_name in ("config",):
        del sys.modules[mod_name]
importlib.invalidate_caches()

import config as cfg

spark.sql(f"USE CATALOG {cfg.CATALOG}")
spark.sql(f"USE SCHEMA {cfg.SCHEMA}")
print(f"Using: {cfg.CATALOG}.{cfg.SCHEMA}")

# COMMAND ----------

# DBTITLE 1,Q1 - Which diagnoses drive the most readmissions?
# MAGIC %sql
# MAGIC SELECT
# MAGIC   diagnosis_category,
# MAGIC   total_admissions,
# MAGIC   total_readmissions,
# MAGIC   readmission_rate,
# MAGIC   avg_los,
# MAGIC   readmission_rank
# MAGIC FROM readmission_by_diagnosis
# MAGIC ORDER BY readmission_rate DESC

# COMMAND ----------

# DBTITLE 1,Q2 - Which departments underperform?
# MAGIC %sql
# MAGIC SELECT
# MAGIC   department,
# MAGIC   total_admissions,
# MAGIC   readmission_rate,
# MAGIC   avg_los,
# MAGIC   performance_score,
# MAGIC   performance_rank
# MAGIC FROM department_performance
# MAGIC ORDER BY performance_score DESC

# COMMAND ----------

# DBTITLE 1,Q3 - Which age groups carry the highest risk?
# MAGIC %sql
# MAGIC SELECT
# MAGIC   age_group,
# MAGIC   patient_count,
# MAGIC   total_admissions,
# MAGIC   readmission_rate,
# MAGIC   avg_los
# MAGIC FROM age_group_risk
# MAGIC ORDER BY readmission_rate DESC

# COMMAND ----------

# DBTITLE 1,Q4 - Which patients need clinical intervention?
# MAGIC %sql
# MAGIC SELECT
# MAGIC   patient_id,
# MAGIC   name,
# MAGIC   age,
# MAGIC   age_group,
# MAGIC   total_admissions,
# MAGIC   total_readmissions,
# MAGIC   avg_los,
# MAGIC   comorbidity_index,
# MAGIC   risk_category
# MAGIC FROM patient_risk_profile
# MAGIC WHERE risk_category = 'High'
# MAGIC ORDER BY total_readmissions DESC, comorbidity_index DESC

# COMMAND ----------

# DBTITLE 1,Q5 - How does length of stay trend over time?
# MAGIC %sql
# MAGIC SELECT
# MAGIC   admission_month,
# MAGIC   COUNT(admission_id) AS total_admissions,
# MAGIC   ROUND(AVG(length_of_stay), 2) AS avg_los,
# MAGIC   ROUND(AVG(readmission_flag), 4) AS readmission_rate
# MAGIC FROM silver_admissions_enriched
# MAGIC GROUP BY admission_month
# MAGIC ORDER BY admission_month

# COMMAND ----------

# DBTITLE 1,Q6 - Department x Diagnosis Category Cross-Tab
# MAGIC %sql
# MAGIC SELECT
# MAGIC   department,
# MAGIC   category AS diagnosis_category,
# MAGIC   COUNT(admission_id) AS total_admissions,
# MAGIC   ROUND(AVG(readmission_flag), 4) AS readmission_rate,
# MAGIC   ROUND(AVG(length_of_stay), 2) AS avg_los
# MAGIC FROM silver_admissions_enriched
# MAGIC GROUP BY department, category
# MAGIC ORDER BY readmission_rate DESC

# COMMAND ----------

# DBTITLE 1,Q7 - High-Risk Patient Count by Department
# MAGIC %sql
# MAGIC SELECT
# MAGIC   s.department,
# MAGIC   COUNT(DISTINCT p.patient_id) AS high_risk_patient_count
# MAGIC FROM patient_risk_profile p
# MAGIC JOIN silver_admissions_enriched s
# MAGIC   ON p.patient_id = s.patient_id
# MAGIC WHERE p.risk_category = 'High'
# MAGIC GROUP BY s.department
# MAGIC ORDER BY high_risk_patient_count DESC

# COMMAND ----------

# DBTITLE 1,Summary Stats for Dashboard Header
# MAGIC %sql
# MAGIC SELECT
# MAGIC   (SELECT COUNT(DISTINCT patient_id) FROM silver_admissions_enriched) AS total_patients,
# MAGIC   (SELECT COUNT(admission_id) FROM silver_admissions_enriched) AS total_admissions,
# MAGIC   (SELECT ROUND(AVG(readmission_flag), 4) FROM silver_admissions_enriched) AS overall_readmission_rate,
# MAGIC   (SELECT ROUND(AVG(length_of_stay), 2) FROM silver_admissions_enriched) AS overall_avg_los,
# MAGIC   (SELECT COUNT(*) FROM patient_risk_profile WHERE risk_category = 'High') AS high_risk_patients
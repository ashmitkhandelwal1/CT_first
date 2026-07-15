# Data Dictionary

## Bronze

### `patients_bronze`

| Column | Type | Nullable | Description |
|---|---|---|---|
| `patient_id` | string | No | Primary key, format `P00001` |
| `name` | string | Yes (~5% null) | Patient full name |
| `age` | int | No | Patient age at time of generation |
| `gender` | string | No | `F`, `M`, or `Other` |
| `contact` | string | Yes (~5% null) | 10-digit synthetic phone number |

### `diagnoses_bronze`

| Column | Type | Nullable | Description |
|---|---|---|---|
| `diagnosis_id` | string | No | Primary key, format `D001` |
| `icd_code` | string | No | ICD-10 code |
| `category` | string | No | One of 8 clinical categories |

### `admissions_bronze`

| Column | Type | Nullable | Description |
|---|---|---|---|
| `admission_id` | string | No | Primary key, format `A000001` |
| `patient_id` | string | No | Foreign key → `patients_bronze` |
| `diagnosis_id` | string | No | Foreign key → `diagnoses_bronze` |
| `department` | string | No (but ~3% inconsistent casing) | Hospital department |
| `physician` | string | Yes (~5% null) | Attending physician |
| `admission_date` | date | No | Admission date |
| `discharge_date` | date | No (but ~2% jittered) | Discharge date |
| `length_of_stay` | int | Yes (~5% null) | Raw LOS in days (recomputed in Silver) |
| `readmitted_within_30_days` | int | No | 0 or 1 |

## Silver

### `silver_admissions_enriched`

| Column | Type | Source | Description |
|---|---|---|---|
| `admission_id` | string | Bronze | Primary key |
| `patient_id` | string | Bronze | Foreign key |
| `diagnosis_id` | string | Bronze | Foreign key |
| `department` | string | Bronze (standardized) | Canonicalized department name |
| `physician` | string | Bronze (imputed) | `"Unassigned"` if originally null |
| `admission_date` | date | Bronze | — |
| `discharge_date` | date | Bronze | — |
| `length_of_stay` | int | Engineered | Recomputed from dates |
| `readmission_flag` | int | Engineered | Clean binary 0/1 |
| `name` | string | Bronze (imputed) | `"Unknown"` if originally null |
| `age` | int | Bronze | — |
| `gender` | string | Bronze | — |
| `contact` | string | Bronze (imputed) | `"Unknown"` if originally null |
| `icd_code` | string | Bronze | — |
| `category` | string | Bronze | Diagnosis category |
| `age_group` | string | Engineered | `0-18` / `19-35` / `36-60` / `60+` |
| `admission_month` | string | Engineered | `yyyy-MM` |
| `los_bucket` | string | Engineered | `Short` / `Medium` / `Long` |
| `comorbidity_index` | int | Engineered | Distinct diagnosis count per patient |
| `prior_admission_count` | long | Engineered | Running count of prior admissions per patient |

## Gold

### `readmission_by_diagnosis`

| Column | Type | Description |
|---|---|---|
| `diagnosis_category` | string | Grouping key |
| `total_admissions` | long | Count of admissions |
| `total_readmissions` | long | Sum of `readmission_flag` |
| `readmission_rate` | double | Average of `readmission_flag`, rounded to 4dp |
| `avg_los` | double | Average `length_of_stay`, rounded to 2dp |
| `readmission_rank` | int | `dense_rank()` by `readmission_rate` descending |

### `department_performance`

| Column | Type | Description |
|---|---|---|
| `department` | string | Grouping key |
| `total_admissions` | long | Count of admissions |
| `readmission_rate` | double | Average of `readmission_flag` |
| `avg_los` | double | Average `length_of_stay` |
| `performance_score` | double | `readmission_rate * 100 + avg_los * 2` |
| `performance_rank` | int | `dense_rank()` by `performance_score` descending |

### `age_group_risk`

| Column | Type | Description |
|---|---|---|
| `age_group` | string | Grouping key |
| `patient_count` | long | Distinct patients in this age group |
| `total_admissions` | long | Count of admissions |
| `readmission_rate` | double | Average of `readmission_flag` |
| `avg_los` | double | Average `length_of_stay` |

### `patient_risk_profile`

| Column | Type | Description |
|---|---|---|
| `patient_id` | string | Primary key |
| `name` | string | Patient name |
| `age` | int | Patient age |
| `age_group` | string | Age bucket |
| `total_admissions` | long | Count of admissions for this patient |
| `total_readmissions` | long | Sum of `readmission_flag` for this patient |
| `avg_los` | double | Average `length_of_stay` for this patient |
| `comorbidity_index` | int | Distinct diagnosis count |
| `risk_category` | string | `High` (≥3 readmissions), `Medium` (1-2), `Low` (0) |
| `risk_rank` | int | `dense_rank()` by `total_readmissions` descending |

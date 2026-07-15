# Gold Layer

## Purpose

Compute business-ready aggregation tables, each answering a specific operational or clinical question, for downstream dashboarding.

## Notebook

`gold/gold_aggregations.py`

## Inputs

`silver_admissions_enriched`

## Outputs

| Table | Business Question | Key Metric |
|---|---|---|
| `readmission_by_diagnosis` | Which diagnoses drive readmissions? | `readmission_rate` per diagnosis category, with `readmission_rank` |
| `department_performance` | Which departments underperform? | Composite `performance_score`, with `performance_rank` |
| `age_group_risk` | Which age groups are highest risk? | `readmission_rate` per age group |
| `patient_risk_profile` | Per-patient risk categorization | `risk_category` (High / Medium / Low), with `risk_rank` |

## Metric Definitions

- **`performance_score`** = `readmission_rate * 100 + avg_los * 2` (higher = worse performing department).
- **`risk_category`**: `High` if a patient has ≥3 readmissions across their history, `Medium` if 1–2, `Low` if 0.
- All ranking columns (`readmission_rank`, `performance_rank`, `risk_rank`) use `dense_rank()` window functions, so ties share a rank with no gaps.

## Dependencies

- `config.py`
- `utils/helpers.py` — `write_delta_overwrite`, `optimize_table`, `analyze_table`, `log_table_stats`

## How to Execute

Run `gold/gold_aggregations.py` after `silver/silver_transform.py` has completed. Idempotent — safe to re-run.

## Validation Performed

Ran end-to-end against real Silver output (687 admissions, 228 patients). Results were cross-checked for business sensibility:
- ICU came out as the worst-performing department (`performance_score` 46.32, driven by both a 28% readmission rate and a 9.04-day average LOS) — clinically expected, since ICU handles the sickest patients.
- Infectious disease had the highest readmission rate among diagnosis categories (29.7%).
- Risk category distribution across 228 patients: 117 Low, 99 Medium, 12 High — a plausible long-tail shape for a risk-stratified population.

# Interview Questions

Questions an interviewer is likely to ask about this project, with grounded answers based on the actual implementation.

**Q: Why Medallion architecture instead of a single transformation script?**
Each layer has a distinct responsibility and a distinct consumer. Bronze preserves raw data exactly as ingested (useful for audits and reprocessing). Silver is the single cleaned source of truth every downstream consumer can trust. Gold is pre-aggregated specifically for dashboard read patterns. Separating them means a bug in a Gold aggregation never requires re-ingesting from source, and a change in cleaning logic only requires re-running Silver + Gold, not Bronze.

**Q: Why recompute `length_of_stay` in Silver instead of just imputing the nulls?**
The raw column has both nulls and (separately) noisy discharge dates. Recomputing directly from `discharge_date - admission_date` is a single source of truth that's guaranteed internally consistent with the two date columns, rather than trying to reconcile three independently-dirty signals.

**Q: Walk me through how `prior_admission_count` is computed.**
It's a window function: `count("admission_id")` over a window partitioned by `patient_id`, ordered by `admission_date`, with a frame of `rowsBetween(unboundedPreceding, -1)`. The `-1` upper bound is what makes it a running count of admissions *strictly before* the current row — a patient's first admission always gets 0.

**Q: Why broadcast join patients and diagnoses instead of a regular shuffle join?**
Both are small dimension tables (~240 rows and 12 rows respectively) well under the 10MB auto-broadcast threshold. Broadcasting them avoids a shuffle on the much larger admissions side of the join entirely — the small table is sent to every executor instead.

**Q: How would this scale if admissions grew from ~700 rows to 700 million?**
The shuffle-partition count (200) and broadcast threshold (10MB) would need re-tuning, `NUM_ADMISSIONS` and the write mode would move from `overwrite` to incremental `MERGE INTO`, and Silver/Gold would likely need to be partitioned by `admission_month`. See `future_improvements.md`.

**Q: Why `dense_rank()` instead of `rank()` for the Gold ranking columns?**
`dense_rank()` doesn't leave gaps after ties — if two departments tie for the worst `performance_score`, the next department gets rank 2, not rank 3. For a small number of departments/diagnosis categories this makes the ranking easier to read and reason about.

**Q: How do you guarantee idempotency?**
Every write goes through one shared helper (`write_delta_overwrite`) using Delta `overwrite` mode with `overwriteSchema=true`. There's no notebook in this pipeline that can accidentally append duplicate data on a re-run.

**Q: What would you change about the risk_category thresholds?**
They're a reasonable first-pass business rule (≥3 readmissions = High), but a production system would likely validate these thresholds against actual clinical outcomes data or feed a proper predictive model rather than a fixed readmission-count cutoff — see `future_improvements.md`'s ML scoring item.

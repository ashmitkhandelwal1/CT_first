# Celebal Technologies – Week 5 Assessment

**Name:** Ashmit Gupta
**Topic:** Apache Spark Fundamentals

---

## Overview

This assessment is part of **Week 5** of the Celebal Technologies Internship Program.

The objective of this assignment is to demonstrate the use of **Apache Spark and PySpark DataFrames** for data cleaning, transformation, aggregation, and analysis on a retail dataset.

---

## Files Included

| File                                               | Description                                                                                                                     |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `Celebal_Week5_Spark_Assessment_Ashmit_Gupta.docx` | Complete assessment document containing answers to all 15 questions with explanations, code snippets, outputs, and observations |
| `spark_week5_superstore.py`                        | PySpark implementation used to generate the results                                                                             |
| `Superstore_messy.csv`                             | Dataset used throughout the assessment                                                                                          |
| `README.md`                                        | Documentation describing the project structure and execution steps                                                              |

---

## Dataset Information

**Sample - Superstore.csv**

* Contains 9,994 retail transaction records
* Includes 21 attributes such as Order ID, Customer Name, Category, Region, City, Sales, Quantity, Ship Mode, and more
* A modified version named **Superstore_messy.csv** was created by introducing duplicate records and missing values to demonstrate Spark's data cleaning capabilities

---

## Questions Covered (Q1 – Q15)

| Question | Topic                                                                                   |
| -------- | --------------------------------------------------------------------------------------- |
| Q1       | Limitations of MapReduce compared to Apache Spark                                       |
| Q2       | Importance of in-memory computation for Machine Learning                                |
| Q3       | Removing duplicate records using `dropDuplicates()`                                     |
| Q4       | Filtering data by Region and calculating average Sales                                  |
| Q5       | Difference between `na.drop()` and `na.fill()`                                          |
| Q6       | Finding cities with more than 100 records                                               |
| Q7       | Understanding DataFrame immutability during transformations                             |
| Q8       | Applying multiple filtering conditions                                                  |
| Q9       | Importance of handling null values before aggregations                                  |
| Q10      | Casting and renaming DataFrame columns                                                  |
| Q11      | Understanding Shuffle operations and wide transformations                               |
| Q12      | Removing records with null emails or empty usernames                                    |
| Q13      | Using `.agg()` for multiple aggregate functions                                         |
| Q14      | Risks associated with `inferSchema=True` on inconsistent data                           |
| Q15      | End-to-end data processing pipeline: deduplication, null handling, and revenue analysis |

---

## Execution Steps

1. Install Python and PySpark on your system.
2. Place `spark_week5_superstore.py` and `Superstore_messy.csv` in the same directory.
3. Open a terminal in that directory.
4. Run the following command:

```bash
python3 spark_week5_superstore.py
```

5. The output for all tasks will be displayed in the terminal.

---

## Technologies Used

* Python 3
* Apache Spark (PySpark)
* Superstore Retail Dataset

---

### Submission Details

**Submitted By:** Ashmit Gupta
**Celebal Technologies – Week 5 Assessment**

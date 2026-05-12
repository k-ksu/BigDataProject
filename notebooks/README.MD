# Notebooks

This directory contains Jupyter/Zeppelin notebooks used during development and exploration. They are **not** part of the automated pipeline and are included for reference only.

## Purpose

- Interactive prototyping of feature engineering logic
- Quick visual checks of data distributions before writing production HQL or PySpark scripts
- Debugging and experimenting with different model configurations

## Notes

- These notebooks were run directly on the Hadoop cluster.
- They are **not** required to reproduce the pipeline results; all logic has been migrated to `scripts/model.py` and `sql/*.hql`.
- Notebooks may contain hard‑coded paths or credentials and should not be shared publicly without review.
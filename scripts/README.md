# Scripts

This directory contains all executable scripts for the project pipeline. Each stage has a dedicated entry-point script, plus supporting Python modules for database and Hive operations.

## Files

| Script                  | Description                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| `stage1.sh`             | Stage 1 entry point: data collection, PostgreSQL build, Sqoop import (`scripts/stage1.sh`) |
| `stage2.sh`             | Stage 2 entry point: Hive database creation, EDA queries (q1 … q6) (`scripts/stage2.sh`) |
| `stage3.sh`             | Stage 3 entry point: Spark ML training, evaluation, artifact retrieval (`scripts/stage3.sh`) |
| `stage4.sh`             | Stage 4 entry point: Hive table registration for Superset dashboards (`scripts/stage4.sh`) |
| `data_collection.sh`    | Downloads dataset from Kaggle; skips if files exist (`scripts/data_collection.sh`) |
| `data_storage.sh`       | Runs `build_projectdb.py` to load CSV into PostgreSQL |
| `build_projectdb.py`    | Python script that executes SQL schema creation, COPY import, and validation (`scripts/build_projectdb.py`) |
| `build_hive.py`         | Python alternative for Stage 2 Hive operations (`scripts/build_hive.py`) |
| `model.py`              | PySpark ML pipeline: feature engineering, training, hyperparameter tuning, evaluation (`scripts/model.py`) |

## Usage

All stage scripts are invoked from the repository root:

```bash
bash scripts/stage1.sh
bash scripts/stage2.sh
bash scripts/stage3.sh 
bash scripts/stage4.sh
```

Password files must be created beforehand in `secrets/.psql.pass` and/or `secrets/.hive.pass`.

## Reproducibility

- Each stage is idempotent: re-running clears previous outputs before creating new ones.
- Stage 3 runs on YARN only (`spark-submit --master yarn`).
- Python code is linted with `pylint` (config in `.pylintrc`).


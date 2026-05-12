# SQL

This directory contains all SQL and HQL files used in the pipeline.

## Files

| File | Stage | Description |
|---|---|---|
| `create_tables.sql` | 1 | DDL for PostgreSQL tables `tracks` and `interactions` (PK, FK, indexes) (`sql/create_tables.sql`)[reference:13] |
| `import_data.sql` | 1 | `COPY … FROM STDIN` commands for loading CSV data into PostgreSQL |
| `test_database.sql` | 1 | Verification queries (row counts, orphan checks, distinct users/tracks) |
| `db.hql` | 2 | HiveQL script to create database `team11_projectdb`, external AVRO tables, optimised ORC tables, and drop un‑optimised originals (`sql/db.hql`)[reference:14] |
| `q1.hql` … `q6.hql` | 2 | EDA insight queries; each creates a `qN_results` table, materialises the result, and exports it to HDFS |
| `stage4.hql` | 4 | HiveQL script to register Stage 3 CSV outputs as external Hive tables for Superset |

## Execution

SQL files are executed by `scripts/build_projectdb.py` (Stage 1). HQL files are executed by `beeline` via `scripts/stage2.sh` and `scripts/stage4.sh`.

```bash
# Example: running a single HQL file manually
beeline -u jdbc:hive2://hadoop-03.uni.innopolis.ru:10001 \
        -n team11 \
        -p $(head -n 1 secrets/.hive.pass) \
        -f sql/db.hql
```

## Notes

- All HQL scripts are idempotent: they drop objects before recreating them (DROP … IF EXISTS).

- Hive execution engine is set to Tez for all analytical queries.

- SET hive.exec.dynamic.partition.mode=nonstrict is enabled for dynamic partitioning.
# Big Data Project — Team 11

**Course:** Big Data — Innopolis University  
**Team:** team11 (4 members)  
**Dataset:** [Music Interaction](https://www.kaggle.com/datasets/huynguyen1902/music-interaction/data) (~1.3 GB)  
**ML Task:** Binary classification (`exists`) — metrics: AUC ROC + AUC PR

## Repository Structure

```
├── data/              Dataset files (gitignored, downloaded automatically)
├── models/            Spark ML models
├── notebooks/         Jupyter/Zeppelin notebooks (learning only)
├── output/            Pipeline output: .avsc, .java, results
├── scripts/           Shell and Python scripts
├── sql/               SQL and HQL files
├── main.sh            Main pipeline script (do not modify)
└── requirements.txt   Python dependencies
```

## Dataset

| File | Size | Rows | Description |
|------|------|------|-------------|
| `interaction.csv` | 574 MB | 11,808,554 | User-track interactions |
| `tracks_features.csv` | 330 MB | 1,204,025 | 24 audio features per track |
| `train.csv` | 257 MB | 626,141 | ML training set |
| `test.csv` | 91 MB | 200,575 | ML test set |

## Quick Start on Cluster

```bash
ssh team11@hadoop-01.uni.innopolis.ru

cd ~/BigDataProject

mkdir -p secrets
echo 'YOUR_PASSWORD' > secrets/.psql.pass

mkdir -p ~/.kaggle
echo '{"username":"YOUR_USER","key":"YOUR_KEY"}' > ~/.kaggle/kaggle.json
chmod 600 ~/.kaggle/kaggle.json

bash scripts/stage1.sh
```

## Pipeline Stages

### Stage 1: Data Collection and Ingestion

**Scripts:** `scripts/stage1.sh` → `data_collection.sh` → `data_storage.sh` (via `build_projectdb.py`)

**What it does:**
1. Downloads dataset from Kaggle via CLI
2. Creates PostgreSQL tables (`tracks`, `interactions`) with PK, FK, and indexes
3. Loads CSV data via `COPY` (psycopg2)
4. Imports tables into HDFS via Sqoop (AVRO + Snappy)
5. Saves `.avsc` and `.java` artifacts to `output/`

**PostgreSQL schema:**
- `tracks` — 24 columns, PK on `id`
- `interactions` — columns: `id` (SERIAL PK), `user_id`, `item_id`, `interaction_flag`, `ts`; FK on `item_id` → `tracks.id`

**HDFS location:** `/user/team11/project/warehouse`

### Stage 2: Data Storage / Preparation / EDA

**Scripts:** `scripts/stage2.sh` (primary, beeline-driven) — optional Python alt: `scripts/build_hive.py` (hivejdbc).

**SQL artefacts:**
- `sql/db.hql` — creates Hive DB `team11_projectdb` at `project/hive/warehouse`, defines external AVRO tables on the Sqoop output, then builds optimised tables and drops the un-optimised originals.
- `sql/q1.hql` … `sql/q5.hql` — five EDA insights, each materialised as a `qN_results` external table **and** exported to `output/qN.csv`.

**Hive tables:**
| Table | Storage | Partitioning | Bucketing | Notes |
|---|---|---|---|---|
| `tracks_part` | AVRO + Snappy | `year` | `id` × 11 | catalogue-style table for content joins |
| `interactions_part` | AVRO + Snappy | `interaction_flag` | `user_id` × 11 | fact table; partition key is the ML target |

**EDA insights produced (each one is wired to a Stage 3 modelling decision):**
1. `q1` — class balance of `interaction_flag` → class weights & metric choice (PR-AUC vs ROC-AUC).
2. `q2` — distribution of positive interactions per (user, artist) pair → whether artist features / embeddings will pay off.
3. `q3` — average audio features for positive vs negative interactions → which audio features actually discriminate the target.
4. `q4` — positive-rate vs track popularity bucket → popularity bias and cold-start severity.
5. `q5` — user-activity power law → per-user train/test split and activity-stratified evaluation.

**HDFS layout after Stage 2:**
```
project/warehouse/avsc/        # *.avsc schemas pushed from output/
project/warehouse/{tracks,interactions}/   # raw Sqoop AVRO (cold archive, no Hive metadata anymore)
project/hive/warehouse/        # Hive-managed DB folder
    tracks_part/year=YYYY/...
    interactions_part/interaction_flag=N/...
    qN_results/...
project/output/qN/             # CSV part-files, fetched into local output/qN.csv by stage2.sh
```

See `STAGE2_INSTRUCTIONS.md` for a step-by-step run guide and the Apache Superset checklist (the only manual part).

### Stage 3: Data Analysis
*TODO*

### Stage 4: Presentation
*TODO*

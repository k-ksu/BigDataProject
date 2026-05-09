# Big Data Project — Team 11

**Course:** Big Data — Innopolis University  
**Team:** team11 (4 members)  
**Dataset:** [Music Interaction](https://www.kaggle.com/datasets/huynguyen1902/music-interaction/data) (~1.3 GB)  
**ML Task:** Recommendation System with soft relevance score (`rel_score`)

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

**EDA insights produced (used to motivate Stage 3 modelling decisions):**
1. `q1` — class balance of `interaction_flag` → class weights & PR-AUC metric choice.
2. `q2` — distribution of positive interactions per (user, artist) pair → whether artist features / embeddings will pay off.
3. `q3` — average audio features for positive vs negative interactions → which audio features actually discriminate the target.
4. `q4` — positive-rate vs track popularity bucket → popularity bias and cold-start severity.
5. `q5` — user-activity power law → user-level split with temporal context.

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

### Stage 3: Predictive Data Analytics

**Scripts:** `scripts/stage3.sh` → `scripts/model.py` via `spark-submit --master yarn`

**What it does:**
1. Reads Stage 2 Hive tables (`tracks_part`, `interactions_part`) as Spark DataFrames
2. Splits each user's history into temporal train, validation, and test rows
3. Uses train-period interactions as the known past for future scoring
4. Builds a feature pipeline over track audio features, categorical metadata,
   artist text, timestamp-derived cyclic features, and last-50 history features
5. Trains two Spark ML classifiers: Logistic Regression and Random Forest
6. Tunes each classifier with Spark CrossValidator and 6 grid combinations
7. Trains ALS as an additional collaborative filtering recommender
8. Builds a hybrid score from ALS and `model1`
9. Selects thresholds and hybrid alpha on validation rows
10. Adds sampled unseen tracks to test ranking candidates
11. Reports PR-AUC, binary threshold metrics, and user-level ranking metrics
12. Saves models, train/test data, predictions, soft scores, and evaluation output

**Target and score:**
- `label` = `interaction_flag` (`0`/`1`)
- `rel_score` = soft relevance score in `[0, 1]`
- Missing user-track pairs are not treated as implicit negative labels
- The split is temporal inside each user: past rows train, later rows validate/test
- This evaluates future preference prediction after observing user history
- Validation/test history features use only train-period rows, not future labels
- Target rows exclude tracks already seen earlier by the same user
- History features are bounded last-50 statistical aggregates
- Threshold metrics are reported on labeled held-out test rows
- Ranking metrics use labeled test rows plus sampled unseen candidate tracks
- Ranking metrics are reported at `10` and `100`
- `evaluation.csv` also reports test users, target rows, true interactions,
  ranking rows, and sampled candidate count

**Outputs:**
- `data/train.json`, `data/test.json`
- `models/model1/`, `models/model2/`, `models/model3/`
- `output/model1_predictions.csv`, `output/model2_predictions.csv`,
  `output/model3_predictions.csv`, `output/hybrid_predictions.csv`
  (`label,prediction`)
- `output/model1_scores.csv`, `output/model2_scores.csv`,
  `output/model3_scores.csv`, `output/hybrid_scores.csv`
  (`user_id,item_id,label,prediction,rel_score`)
- `output/evaluation.csv`

Stage 3 must run on the cluster with Yarn; do not run it in Spark local mode.

### Stage 4: Presentation
*TODO*

# Stage 2 — What you need to do

> Big Data — Innopolis University, team **team11**
> **Goal of this stage:** build a Hive data warehouse on top of the Sqoop output from Stage 1, optimise it with **partitioning + bucketing**, run **5 EDA queries**, and visualise them in Apache Superset.

If you have never used Hadoop / Hive / HDFS before, **read section 0 first** — it explains the only really confusing thing about this course (the local vs. cluster split) before you touch any commands.

---

## 0. The only thing you really need to understand: local vs. cluster

You are working with **two separate computers**.

| | Your laptop (the one you're sitting at) | The cluster (`hadoop-01.uni.innopolis.ru`) |
|---|---|---|
| Operating system | Windows | Linux |
| Has your editor (Cursor / VS Code) | ✅ | ❌ |
| Has the *code* of this repo | ✅ (you cloned it) | ✅ (someone has to put it there too) |
| Has Hadoop, HDFS, Hive, Sqoop, beeline, Tez, Spark, Apache Superset | ❌ | ✅ |
| Has the 1.3 GB dataset & the PostgreSQL DB | ❌ | ✅ |

**Rule:** files are *written* on your laptop, but the pipeline is *run* on the cluster.
None of `scripts/stage2.sh` would work on your Windows machine, because the tools and the data simply aren't there.

So every Stage 2 session has the same shape:

1. Edit code locally on your laptop (with my help, in Cursor).
2. **Move that code to the cluster** (3 ways shown in section 2 — pick one).
3. **SSH into the cluster** and run `bash scripts/stage2.sh` from there.
4. Visualise the results in Apache Superset (which runs on the cluster — you open it in your browser as a webpage).

That's it. The rest of this file just spells out each of those four steps.

---

## 1. Prerequisites (check before you start)

- [ ] Stage 1 already finished successfully on the cluster (`scripts/stage1.sh` exited 0).
  - You can verify by SSHing in (see step 3) and running `hdfs dfs -ls project/warehouse` — you should see `tracks` and `interactions` folders with `.avro` files in them.
- [ ] You know the cluster password (the same one you put into `secrets/.psql.pass` for Stage 1).
- [ ] You can reach `hadoop-01.uni.innopolis.ru` from your network (you may need the university VPN if you are off-campus).

---

## 2. Move the Stage 2 files from your laptop to the cluster

The Stage 2 work lives on the GitHub branch **`stage-2`** ([github.com/k-ksu/BigDataProject/tree/stage-2](https://github.com/k-ksu/BigDataProject/tree/stage-2)). The pull request into `main` isn't merged yet, so on the cluster you need to **explicitly check out that branch** rather than just `git pull`.

### Option A — pull the `stage-2` branch on the cluster (recommended)

After SSHing in (step 3), from `~/BigDataProject`:

**First time only** — the cluster's clone has only ever seen `main`, so create a local branch that tracks `origin/stage-2`:

```bash
cd ~/BigDataProject
git fetch origin
git checkout -b stage-2 origin/stage-2
```

That single `git checkout -b` does three things at once: fetches the remote branch, creates a matching local branch, and switches to it. From now on, `git pull` (no args) pulls from `origin/stage-2`.

**Every subsequent time** you push new commits from your laptop:

```bash
cd ~/BigDataProject
git pull
```

When the PR finally gets merged into `main`, switch back with:

```bash
git checkout main
git pull
git branch -d stage-2     # optional cleanup
```

> If `git checkout` complains about local changes that would be overwritten (often the auto-generated `secrets/`, `output/*.csv`, `*.avsc` from a previous run), either `git stash` them or just delete the conflicting paths — the pipeline regenerates them.

### Option B — direct copy with `scp` (skip GitHub entirely)

From a PowerShell on your **laptop**, in the repo root:

```powershell
scp -r scripts sql STAGE2_INSTRUCTIONS.md README.md requirements.txt team11@hadoop-01.uni.innopolis.ru:~/BigDataProject/
```

This is handy when you've made local edits you haven't committed yet. It bypasses git entirely — the cluster's git state will not change.

> If `scp` is missing on Windows, install OpenSSH ("Manage optional features" → add **OpenSSH Client**), or use WinSCP / FileZilla / the built-in upload of JupyterLab on `hadoop-01:8888`.

### Option C — edit directly on the cluster

After SSHing in (step 3), open files with `nano sql/db.hql` etc. Works fine but you lose the comfort of Cursor.

---

## 3. SSH into the cluster

From your laptop:

```powershell
ssh team11@hadoop-01.uni.innopolis.ru
```

Type your cluster password when prompted. After this, **your terminal is on the cluster** — every command you type goes there until you type `exit`.

Then go to the project folder:

```bash
cd ~/BigDataProject
ls                # should now include scripts/stage2.sh, sql/db.hql, etc.
```

If `secrets/.hive.pass` does not exist yet (it's the same password as `.psql.pass`):

```bash
mkdir -p secrets
[ -f secrets/.hive.pass ] || cp secrets/.psql.pass secrets/.hive.pass
chmod 600 secrets/.hive.pass

chmod +x scripts/stage2.sh
```

> **Why a separate file name?** The Hive password and the PostgreSQL password could in principle differ. On the IU cluster they are the same value, so we just copy the file.

---

## 4. Run the automated pipeline (on the cluster)

Still inside the SSH session:

```bash
bash scripts/stage2.sh
```

Expected runtime: **5–15 min**. The slowest step is the AVRO→AVRO repartitioning insert, which Hive runs as a Tez job across the cluster.

What the script does, top to bottom:

1. Pushes `output/*.avsc` from local-to-cluster filesystem (`output/`) to HDFS at `project/warehouse/avsc/`. Hive needs the schema files to read AVRO data.
2. Runs `sql/db.hql` via `beeline` (the Hive command-line client). This:
   - drops & recreates the database `team11_projectdb` at `project/hive/warehouse`,
   - creates the two raw external tables (`tracks`, `interactions`) reading the Sqoop AVRO files,
   - creates `tracks_part` (partitioned by `year`, bucketed by `id` ×11) and `interactions_part` (partitioned by `interaction_flag`, bucketed by `user_id` ×11),
   - copies the data from raw → optimised tables,
   - drops the raw external tables (the spec requires this).
3. Runs `sql/q1.hql … q5.hql` — each one creates a `qN_results` table and writes a clean CSV part-file to HDFS at `project/output/qN/`.
4. Pulls those part-files back to the cluster's local filesystem at `~/BigDataProject/output/q1.csv … q5.csv` and prepends a header row.

> Reminder: "local filesystem" in step 4 means **the cluster's** local disk (the SSH session you're in), not your laptop. To get the CSVs onto your laptop, run an `scp` in the **other** direction from your laptop — see the Appendix at the bottom.

---

## 5. Verify it worked (still on the cluster)

```bash
# 1. Local CSVs (on the cluster, in ~/BigDataProject/output/)
ls -lh output/*.csv          # q1.csv … q5.csv, all non-empty
head output/q2.csv           # should show header + 1-2 lines of class balance

# 2. Hive metadata
beeline -u jdbc:hive2://hadoop-03.uni.innopolis.ru:10001 \
        -n team11 -p "$(cat secrets/.hive.pass)" -e "
USE team11_projectdb;
SHOW TABLES;
SHOW PARTITIONS tracks_part;
SHOW PARTITIONS interactions_part;
SELECT COUNT(*) FROM tracks_part;
SELECT COUNT(*) FROM interactions_part;
"

# 3. HDFS layout
hdfs dfs -ls -R project/hive/warehouse | head -n 40
```

You should see:

- `tracks` and `interactions` are **gone** from `SHOW TABLES` (only the `_part` and `qN_results` ones remain).
- `tracks_part` row count ≈ **1,204,025**, `interactions_part` ≈ **11,808,554**.
- One sub-folder per partition (`year=2010/`, `year=2011/`, … and `interaction_flag=0/`, `interaction_flag=1/`).
- 11 bucket files per partition.

If the row counts are wrong, see "Troubleshooting" at the bottom.

---

## 6. Apache Superset — click-by-click

Superset URL: **http://hadoop-03.uni.innopolis.ru:8088/** (log in with your team credentials).

### 6.1. One-time: confirm the Hive database connection

1. Top-right gear icon → **Settings → Database Connections**.
2. You should see a row for Hive (something like `Hive` or `hive_team11`). If yes — great, skip to 6.2.
3. If there's no Hive connection, click **+ DATABASE → Apache Hive**, then paste the SQLAlchemy URI:
   ```
   hive://team11@hadoop-03.uni.innopolis.ru:10001/team11_projectdb
   ```
   In the **Advanced → Security → Connect** options, set the password to the same value as `secrets/.hive.pass`. Click **TEST CONNECTION** → **CONNECT**.

### 6.2. Register all five Hive result tables as Superset datasets

Do this **once per query** (q1 through q5):

1. Top nav → **Datasets**.
2. Top-right **+ DATASET** button.
3. Fill the modal:
   - **DATABASE**: the Hive connection from 6.1.
   - **SCHEMA**: `team11_projectdb`.
   - **TABLE**: `q1_results` (then `q2_results`, etc).
4. **CREATE DATASET AND CREATE CHART**.

You'll land directly on the chart-builder for that dataset. Keep one browser tab open per chart so you don't lose work.

### 6.3. Build each chart

For every chart, after saving, click the **⋮** menu (top-right of the chart) → **Download → Download as image**. Save the file as `output/q1.jpg`, `output/q2.jpg`, etc., on your **laptop** first, then upload to the cluster's `~/BigDataProject/output/` folder via JupyterLab (`http://hadoop-01.uni.innopolis.ru:8888`) drag-and-drop, **or** see the Appendix for `scp`.

#### Chart q1 — class balance

- **Chart type**: `Pie Chart` (search "pie" in the type picker).
- **DIMENSIONS**: `interaction_flag`.
- **METRIC**: click the field → **SIMPLE** tab → **COLUMN** = `cnt`, **AGGREGATE** = `SUM` → **SAVE**.
- **NAME**: `q1 — class balance (interaction_flag)`.
- **DESCRIPTION**: `Stage-3 implication: ratio dictates class weights and metric choice.`
- Click **SAVE** (top right).

#### Chart q2 — artist loyalty histogram

- **Chart type**: `Bar Chart`.
- **X-AXIS**: `positives_per_user_artist`.
- **METRICS**: `SUM(pair_count)` (same flow as above).
- **SORT BY**: X-axis ascending.
- **NAME**: `q2 — artist loyalty distribution`.

#### Chart q3 — audio-feature mean by class

- **Chart type**: `Bar Chart`.
- **X-AXIS**: `interaction_flag`.
- **METRICS**: add **six** of them, one per audio feature:
  - `AVG(avg_danceability)` (or just the column itself — the column already holds the average; use **AGGREGATE = AVG** so two-row aggregation works correctly. With only 2 rows there's nothing to aggregate so MIN/MAX/AVG all give the same result).
  - same for `avg_energy`, `avg_valence`, `avg_acousticness`, `avg_loudness`, `avg_tempo`.
- This will plot 6 bars per class side by side (grouped bar).
- **NAME**: `q3 — audio features: positives vs negatives`.

#### Chart q4 — popularity bias

- **Chart type**: `Mixed Chart` (search "mixed").
- **X-AXIS**: `popularity_bucket`.
- **QUERY A → METRICS**: `SUM(n_tracks)` (these become bars).
- **QUERY B → METRICS**: `AVG(positive_rate)` (becomes the overlay line).
- In the customise tab, set **QUERY A → CHART TYPE = Bar**, **QUERY B → CHART TYPE = Line**.
- **NAME**: `q4 — positive rate vs track popularity`.

#### Chart q5 — user-activity power law

- **Chart type**: `Bar Chart`.
- **X-AXIS**: `activity_bucket`.
- **METRICS**: two of them — `SUM(pct_users)` and `SUM(pct_interactions)`.
- This plots two bars per bucket: % of users in the bucket vs % of total interactions they account for. The classic power-law signature is bar 2 ≫ bar 1 in the rightmost bucket.
- **NAME**: `q5 — user activity vs interaction share`.

### 6.4. Sanity check before saving each chart

In the chart explorer, click **VIEW QUERY** (the `</>` icon, bottom-right of the data preview pane) to see the SQL Superset will run. Click **REFRESH** to re-run it. The bottom panel should show 2–10 rows for q1/q2/q3/q4/q5 — these are tiny aggregate tables, so they should load instantly. If you see 0 rows, the dataset was registered against the wrong schema or the `qN_results` table is empty.

### 6.5. Backup option — SQL Lab if Datasets behaves weirdly

If "+ DATASET" doesn't show your `qN_results` tables, you can chart from a saved SQL query instead:

1. Top nav → **SQL → SQL Lab**.
2. **DATABASE** = Hive, **SCHEMA** = `team11_projectdb`.
3. Paste `SELECT * FROM q1_results;` and **RUN**.
4. Below the results table, **EXPLORE** → builds the same chart UI.

> Keep all five `qN.jpg` files. Stage 4 assembles them into the final dashboard.

---

## 7. Quality gate

Still on the cluster:

```bash
pylint scripts
```

Aim for ≥ 8.0 on the new files. The existing `scripts/build_projectdb.py` already passes; `scripts/build_hive.py` was written to match.

---

## 8. Add to the project report

Append a Stage 2 section to your report covering:

- Hive DB layout (`team11_projectdb` @ `project/hive/warehouse`).
- The two external Hive tables created from the Sqoop AVRO output.
- Choice of partition key + bucket key for each optimised table and **why**:
  - `interactions_part` partitioned by `interaction_flag` because it is the Stage 3 ML target → free class-based pruning.
  - `tracks_part` partitioned by `year` because EDA / dashboard queries are usually time-sliced.
  - Both bucketed into a **prime** number (11) for hash uniformity, on the natural join keys (`id`, `user_id`).
- Each of the 5 EDA insights, the HiveQL behind it, and the saved chart `qN.jpg`.
- Engine choice: HiveQL on **Tez** (set in `db.hql`).

---

## TL;DR — first-time run from the `stage-2` branch

```powershell
# on your laptop:
ssh team11@hadoop-01.uni.innopolis.ru
```
```bash
# now on the cluster:
cd ~/BigDataProject
git fetch origin
git checkout -b stage-2 origin/stage-2          # one-time
[ -f secrets/.hive.pass ] || cp secrets/.psql.pass secrets/.hive.pass
chmod +x scripts/stage2.sh
bash scripts/stage2.sh                          # 5-15 min
pylint scripts
```

After that, every later run is just:

```bash
ssh team11@hadoop-01.uni.innopolis.ru
cd ~/BigDataProject && git pull && bash scripts/stage2.sh
```

Then in your browser: open Apache Superset, build 5 charts on the `qN_results` tables, save as `output/q{1..5}.jpg`.

---

## Appendix — common file-transfer patterns

All run from a **laptop** PowerShell (not from the cluster):

```powershell
# Push a single file laptop → cluster
scp scripts/stage2.sh team11@hadoop-01.uni.innopolis.ru:~/BigDataProject/scripts/

# Pull a single file cluster → laptop  (e.g. fetching a CSV result)
scp team11@hadoop-01.uni.innopolis.ru:~/BigDataProject/output/q1.csv .

# Pull a whole folder cluster → laptop
scp -r team11@hadoop-01.uni.innopolis.ru:~/BigDataProject/output ./output_from_cluster
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ssh: Could not resolve hostname hadoop-01.uni.innopolis.ru` | not on the university network / VPN | connect to the IU VPN and retry |
| `Permission denied (publickey,password)` on SSH | wrong password | use the same password as `secrets/.psql.pass` |
| `FAILED: Database team11_projectdb is not empty` when re-running | left-over tables from a half-run | the script already uses `DROP DATABASE … CASCADE`, just re-run `stage2.sh` |
| `avro.schema.url` errors during `db.hql` | `.avsc` files not in HDFS | `hdfs dfs -ls project/warehouse/avsc` — re-run step 1 of `stage2.sh` |
| `tracks_part` count == 0 | dynamic-partition mode not set | `db.hql` sets `nonstrict` already; check `output/hive_results.txt` for the real Tez error |
| `output/qN.csv` only contains the header | `INSERT OVERWRITE DIRECTORY` ran before `qN_results` finished | re-run that one query: `beeline -u jdbc:hive2://hadoop-03.uni.innopolis.ru:10001 -n team11 -p "$(cat secrets/.hive.pass)" -f sql/qN.hql` and the matching `hdfs dfs -cat` block of `stage2.sh` |
| `command not found: beeline` / `hdfs` | you're running on your laptop, not the cluster | `ssh team11@hadoop-01.uni.innopolis.ru` first |
| Tez not available | cluster temporarily restarted | comment out `SET hive.execution.engine = tez;` in `sql/db.hql` to fall back to MapReduce |

#!/bin/bash
# Stage 2: build the Hive warehouse, run EDA queries, fetch CSV results.

set -euo pipefail

echo "==========================================================="
echo "  Stage 2: Hive Storage / Preparation / EDA"
echo "==========================================================="

TEAM="team11"
HIVE_HOST="hadoop-03.uni.innopolis.ru"
HIVE_PORT="10001"
JDBC_URL="jdbc:hive2://${HIVE_HOST}:${HIVE_PORT}"

HDFS_AVSC_DIR="project/warehouse/avsc"
HDFS_OUTPUT_DIR="project/output"

SECRETS_FILE="secrets/.hive.pass"
PSQL_SECRETS_FILE="secrets/.psql.pass"

if   [ -f "${SECRETS_FILE}" ]; then PASS_FILE="${SECRETS_FILE}"
elif [ -f "${PSQL_SECRETS_FILE}" ]; then PASS_FILE="${PSQL_SECRETS_FILE}"
else
    echo "ERROR: no password file found. Create one of:"
    echo "       ${SECRETS_FILE}   or   ${PSQL_SECRETS_FILE}"
    exit 1
fi
password="$(head -n 1 "${PASS_FILE}")"

mkdir -p output

beeline_run () {
    local hql="$1"
    local out="${2:-/dev/stdout}"
    beeline -u "${JDBC_URL}" \
            -n "${TEAM}" -p "${password}" \
            --silent=false --showHeader=true --outputformat=table \
            -f "${hql}" \
            > "${out}" 2> /dev/null
}

echo ""
echo "--- Step 1: Pushing AVRO schemas to HDFS ---"

if ! ls output/*.avsc >/dev/null 2>&1; then
    echo "ERROR: no *.avsc files in output/. Did stage 1 finish successfully?"
    exit 1
fi

hdfs dfs -mkdir -p "${HDFS_AVSC_DIR}"
hdfs dfs -rm  -f "${HDFS_AVSC_DIR}"/*.avsc 2>/dev/null || true
hdfs dfs -put -f output/*.avsc "${HDFS_AVSC_DIR}"
echo "Schemas in HDFS:"
hdfs dfs -ls "${HDFS_AVSC_DIR}"

echo ""
echo "--- Step 2: Building Hive database (sql/db.hql) ---"
beeline_run "sql/db.hql" "output/hive_results.txt"
echo "Hive results saved to output/hive_results.txt"

echo ""
echo "--- Step 3: Running EDA queries q1..q5 ---"

# Headers are owned by this script because  INSERT OVERWRITE DIRECTORY  does
# not emit them; keeping them here keeps the q*.hql files reusable elsewhere.
declare -A HEADERS=(
    [q1]="track_id,track_name,artists,interaction_count"
    [q2]="interaction_flag,cnt,pct"
    [q3]="year,track_count,avg_duration_min,avg_energy,avg_danceability"
    [q4]="user_id,interaction_count,distinct_tracks"
    [q5]="bucket,n_tracks,avg_danceability,avg_energy,avg_valence,avg_loudness,avg_tempo,avg_acousticness"
)

for q in q1 q2 q3 q4 q5; do
    hql="sql/${q}.hql"
    [ -f "${hql}" ] || { echo "SKIP: ${hql} not found"; continue; }

    echo ""
    echo "  >> ${q}"
    hdfs dfs -rm -r -f "${HDFS_OUTPUT_DIR}/${q}" >/dev/null 2>&1 || true

    beeline_run "${hql}" "output/${q}_run.log"

    if hdfs dfs -test -d "${HDFS_OUTPUT_DIR}/${q}"; then
        echo "${HEADERS[$q]}"                       >  "output/${q}.csv"
        hdfs dfs -cat "${HDFS_OUTPUT_DIR}/${q}"/*   >> "output/${q}.csv"
        rows=$(($(wc -l < "output/${q}.csv") - 1))
        echo "     -> output/${q}.csv  (${rows} rows)"
    else
        echo "     WARN: HDFS folder ${HDFS_OUTPUT_DIR}/${q} not found."
    fi
done

echo ""
echo "--- Step 4: Final inventory ---"
echo "Local output/ :"
ls -lh output/*.csv 2>/dev/null || true
echo ""
echo "HDFS Hive warehouse :"
hdfs dfs -ls -R project/hive/warehouse | head -n 40 || true

echo ""
echo "==========================================================="
echo "  Stage 2 completed successfully!"
echo "==========================================================="

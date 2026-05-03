#!/bin/bash

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

# INSERT OVERWRITE DIRECTORY drops headers, so we add them here.
declare -A HEADERS=(
    [q1]="interaction_flag,cnt,pct"
    [q2]="positives_per_user_artist,pair_count,pct"
    [q3]="interaction_flag,n,avg_danceability,avg_energy,avg_valence,avg_acousticness,avg_loudness,avg_tempo"
    [q4]="popularity_bucket,n_tracks,n_interactions,n_positive,positive_rate"
    [q5]="activity_bucket,user_count,pct_users,n_interactions,pct_interactions"
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

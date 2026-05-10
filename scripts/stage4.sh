#!/bin/bash

set -euo pipefail

echo "==========================================================="
echo "  Stage 4: Superset Dashboard Preparation"
echo "==========================================================="

TEAM="team11"
HIVE_HOST="hadoop-03.uni.innopolis.ru"
HIVE_PORT="10001"
JDBC_URL="jdbc:hive2://${HIVE_HOST}:${HIVE_PORT}"

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

if ! command -v beeline >/dev/null 2>&1; then
    echo "ERROR: beeline not found. Run this stage on the Hadoop cluster."
    exit 1
fi

if ! command -v hdfs >/dev/null 2>&1; then
    echo "ERROR: hdfs CLI not found. Run this stage on the Hadoop cluster."
    exit 1
fi

mkdir -p output

beeline_run () {
    local hql="$1"
    local out="${2:-/dev/stdout}"
    local base err ec

    base="$(basename "${hql}" .hql)"
    err="output/beeline_${base}.stderr"
    set +e
    beeline -u "${JDBC_URL}" \
            -n "${TEAM}" -p "${password}" \
            --silent=false --showHeader=true --outputformat=table \
            -f "${hql}" \
            > "${out}" 2> "${err}"
    ec=$?
    set -e
    if [ "${ec}" -ne 0 ]; then
        echo "ERROR: beeline exited ${ec} on ${hql}"
        echo "---- tail ${err} ----"
        tail -80 "${err}" 2>/dev/null || true
        exit "${ec}"
    fi
}

require_hdfs_dir () {
    local path="$1"

    if ! hdfs dfs -test -d "${path}"; then
        echo "ERROR: required HDFS directory is missing: ${path}"
        exit 1
    fi
}

echo ""
echo "--- Step 1: Checking Stage 2 and Stage 3 HDFS artifacts ---"
for path in \
    project/hive/warehouse/tracks_part \
    project/hive/warehouse/interactions_part \
    project/hive/warehouse/q1_results \
    project/hive/warehouse/q2_results \
    project/hive/warehouse/q3_results \
    project/hive/warehouse/q4_results \
    project/hive/warehouse/q5_results \
    project/hive/warehouse/q6_results \
    project/output/evaluation \
    project/output/model1_predictions \
    project/output/model2_predictions \
    project/output/model1_scores \
    project/output/model2_scores
do
    require_hdfs_dir "${path}"
    echo "OK: ${path}"
done

echo ""
echo "--- Step 2: Creating Stage 4 Hive tables and views ---"
beeline_run "sql/stage4.hql" "output/stage4_hive_results.txt"
echo "Stage 4 Hive results saved to output/stage4_hive_results.txt"

echo ""
echo "--- Step 3: Superset dashboard datasets ---"
cat <<'DATASETS'
Data description:
  - stage4_dataset_summary
  - stage4_table_columns
  - stage4_track_sample
  - stage4_interaction_sample

Stage 2 EDA:
  - q1_results
  - q2_results
  - q3_results
  - q4_results
  - q5_results
  - q6_results

Stage 3 ML:
  - stage4_feature_extraction_summary
  - stage4_model_comparison
  - stage4_model_metrics_long
  - stage4_prediction_confusion
  - stage4_prediction_rates
  - stage4_score_summary
DATASETS

echo ""
echo "==========================================================="
echo "  Stage 4 completed successfully!"
echo "==========================================================="

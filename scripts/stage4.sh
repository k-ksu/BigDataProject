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

ensure_hdfs_csv_dir () {
    local local_file="$1"
    local hdfs_dir="$2"

    if hdfs dfs -test -d "${hdfs_dir}"; then
        echo "OK: ${hdfs_dir}"
        return
    fi

    if [ ! -f "${local_file}" ]; then
        echo "ERROR: required local file is missing: ${local_file}"
        exit 1
    fi

    hdfs dfs -mkdir -p "${hdfs_dir}"
    hdfs dfs -put -f "${local_file}" "${hdfs_dir}/part-00000.csv"
    echo "UPLOADED: ${local_file} -> ${hdfs_dir}"
}

echo ""
echo "--- Step 1: Checking Stage 3 HDFS artifacts ---"
ensure_hdfs_csv_dir "output/evaluation.csv" "project/output/evaluation"
ensure_hdfs_csv_dir "output/model1_predictions.csv" "project/output/model1_predictions"
ensure_hdfs_csv_dir "output/model2_predictions.csv" "project/output/model2_predictions"
ensure_hdfs_csv_dir "output/model1_scores.csv" "project/output/model1_scores"
ensure_hdfs_csv_dir "output/model2_scores.csv" "project/output/model2_scores"

echo ""
echo "--- Step 2: Creating Stage 3 Hive tables ---"
beeline_run "sql/stage4.hql" "output/stage4_hive_results.txt"
echo "Stage 4 Hive results saved to output/stage4_hive_results.txt"

echo ""
echo "--- Step 3: Superset datasets ---"
cat <<'DATASETS'
  - team11_stage3_feature_extraction_characteristics
  - stage3_evaluation
  - stage3_model1_predictions
  - stage3_model2_predictions
  - stage3_model1_scores
  - stage3_model2_scores
DATASETS

echo ""
echo "==========================================================="
echo "  Stage 4 completed successfully!"
echo "==========================================================="

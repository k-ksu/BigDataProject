#!/bin/bash

set -euo pipefail

echo "==========================================================="
echo "  Stage 3: Spark ML Soft Binary Classification"
echo "==========================================================="

if ! command -v spark-submit >/dev/null 2>&1; then
    echo "ERROR: spark-submit not found. Run this stage on the Hadoop cluster."
    exit 1
fi

if ! command -v hdfs >/dev/null 2>&1; then
    echo "ERROR: hdfs CLI not found. Run this stage on the Hadoop cluster."
    exit 1
fi

mkdir -p data models output

echo ""
echo "--- Step 1: Running Spark ML app on Yarn ---"
spark-submit \
    --master yarn \
    --deploy-mode client \
    --driver-memory 4g \
    --executor-memory 4g \
    --executor-cores 2 \
    --num-executors 4 \
    --conf spark.sql.shuffle.partitions=88 \
    --conf spark.default.parallelism=88 \
    scripts/model.py

fetch_file () {
    local hdfs_path="$1"
    local local_path="$2"

    # spark writes directories, so merge part files into the expected file.
    rm -f "${local_path}"
    hdfs dfs -getmerge "${hdfs_path}" "${local_path}"
    if [ ! -s "${local_path}" ]; then
        echo "ERROR: ${local_path} is empty after fetching ${hdfs_path}"
        exit 1
    fi
}

fetch_model () {
    local hdfs_path="$1"
    local local_path="$2"

    rm -rf "${local_path}"
    hdfs dfs -get "${hdfs_path}" "${local_path}"
    if [ ! -d "${local_path}" ]; then
        echo "ERROR: ${local_path} was not fetched from ${hdfs_path}"
        exit 1
    fi
}

check_prediction_header () {
    local path="$1"

    # checklist prediction files should stay minimal.
    if [ "$(head -n 1 "${path}")" != "label,prediction" ]; then
        echo "ERROR: ${path} must contain only label,prediction columns"
        exit 1
    fi
}

check_scores () {
    local path="$1"

    # rel_score is the fifth column in score csv files.
    awk -F, '
        NR == 1 { next }
        $5 < 0 || $5 > 1 { exit 1 }
    ' "${path}" || {
        echo "ERROR: ${path} contains rel_score outside [0, 1]"
        exit 1
    }
}

echo ""
echo "--- Step 2: Fetching Stage 3 artifacts from HDFS ---"
fetch_file "project/data/train" "data/train.json"
fetch_file "project/data/test" "data/test.json"
fetch_file "project/output/model1_predictions" "output/model1_predictions.csv"
fetch_file "project/output/model2_predictions" "output/model2_predictions.csv"
fetch_file "project/output/model1_scores" "output/model1_scores.csv"
fetch_file "project/output/model2_scores" "output/model2_scores.csv"
fetch_file "project/output/evaluation" "output/evaluation.csv"
fetch_model "project/models/model1" "models/model1"
fetch_model "project/models/model2" "models/model2"

check_prediction_header "output/model1_predictions.csv"
check_prediction_header "output/model2_predictions.csv"
check_scores "output/model1_scores.csv"
check_scores "output/model2_scores.csv"

echo ""
echo "--- Step 3: Final inventory ---"
ls -lh data/train.json data/test.json output/model*_predictions.csv \
    output/model*_scores.csv output/evaluation.csv
find models/model1 models/model2 -maxdepth 2 -type f | head -n 20

echo ""
echo "==========================================================="
echo "  Stage 3 completed successfully!"
echo "==========================================================="

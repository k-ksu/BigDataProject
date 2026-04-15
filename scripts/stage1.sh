#!/bin/bash

# ==============================================================
# Stage 1: Data Collection and Ingestion
# ==============================================================
# This script orchestrates the full Stage 1 pipeline:
#   1. Download / verify the dataset
#   2. Build PostgreSQL database (create tables, load data, test)
#   3. Import tables from PostgreSQL into HDFS via Sqoop (AVRO + Snappy)
#   4. Copy .avsc and .java artifacts to output/
#
# Prerequisites:
#   - secrets/.psql.pass contains the PostgreSQL password
#   - Dataset CSV files are in data/ directory
#   - Run from the project root directory
# ==============================================================

set -e

echo "==========================================================="
echo "  Stage 1: Data Collection and Ingestion"
echo "==========================================================="

# ---------------------------
# Configuration
# ---------------------------
TEAM="team11"
DB_NAME="${TEAM}_projectdb"
DB_HOST="hadoop-04.uni.innopolis.ru"
DB_PORT="5432"
JDBC_URL="jdbc:postgresql://${DB_HOST}/${DB_NAME}"
HDFS_WAREHOUSE="project/warehouse"
SECRETS_FILE="secrets/.psql.pass"

# Read password
if [ ! -f "$SECRETS_FILE" ]; then
    echo "ERROR: Password file not found at ${SECRETS_FILE}"
    echo "Create it with: echo 'your_password' > ${SECRETS_FILE}"
    exit 1
fi
password=$(head -n 1 "$SECRETS_FILE")

# ---------------------------
# Step 1: Data Collection
# ---------------------------
echo ""
echo "--- Step 1: Data Collection ---"
bash scripts/data_collection.sh

# Verify required files exist
for file in data/tracks_features.csv data/interaction.csv; do
    if [ ! -f "$file" ]; then
        echo "ERROR: Required file ${file} not found!"
        exit 1
    fi
done
echo "All required data files are present."

# ---------------------------
# Step 2: Build PostgreSQL DB
# ---------------------------
echo ""
echo "--- Step 2: Building PostgreSQL database ---"
bash scripts/data_storage.sh

# ---------------------------
# Step 3: Import to HDFS via Sqoop
# ---------------------------
echo ""
echo "--- Step 3: Importing data to HDFS via Sqoop ---"

# Clear HDFS warehouse directory if it exists (idempotency)
echo "Clearing HDFS warehouse directory: ${HDFS_WAREHOUSE}"
hdfs dfs -rm -r -f "${HDFS_WAREHOUSE}"

# Import all tables from PostgreSQL to HDFS
# Format: AVRO (row-based, good for ETL and full-row reads)
# Compression: Snappy (fast compression/decompression, good balance)
echo "Running Sqoop import-all-tables..."
sqoop import-all-tables \
    --connect "${JDBC_URL}" \
    --username "${TEAM}" \
    --password "${password}" \
    --compression-codec=snappy \
    --compress \
    --as-avrodatafile \
    --warehouse-dir="${HDFS_WAREHOUSE}" \
    --m 1

echo "Sqoop import completed."

# ---------------------------
# Step 4: Collect artifacts
# ---------------------------
echo ""
echo "--- Step 4: Collecting .avsc and .java artifacts ---"

# Sqoop generates .avsc (Avro schema) and .java files in the current directory
# Move them to the output/ folder for the repo
mkdir -p output

if ls *.avsc 1>/dev/null 2>&1; then
    cp *.avsc output/
    echo "Copied .avsc files to output/"
    rm -f *.avsc
else
    echo "WARNING: No .avsc files found in current directory"
fi

if ls *.java 1>/dev/null 2>&1; then
    cp *.java output/
    echo "Copied .java files to output/"
    rm -f *.java
else
    echo "WARNING: No .java files found in current directory"
fi

# ---------------------------
# Step 5: Verify HDFS data
# ---------------------------
echo ""
echo "--- Step 5: Verifying HDFS data ---"
echo "Contents of HDFS warehouse:"
hdfs dfs -ls -R "${HDFS_WAREHOUSE}" 2>/dev/null || echo "WARNING: Could not list HDFS warehouse"

echo ""
echo "==========================================================="
echo "  Stage 1 completed successfully!"
echo "==========================================================="

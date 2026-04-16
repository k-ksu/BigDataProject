#!/bin/bash

set -e

echo "==========================================================="
echo "  Stage 1: Data Collection and Ingestion"
echo "==========================================================="

TEAM="team11"
DB_NAME="${TEAM}_projectdb"
DB_HOST="hadoop-04.uni.innopolis.ru"
DB_PORT="5432"
JDBC_URL="jdbc:postgresql://${DB_HOST}/${DB_NAME}"
HDFS_WAREHOUSE="project/warehouse"
SECRETS_FILE="secrets/.psql.pass"

if [ ! -f "$SECRETS_FILE" ]; then
    echo "ERROR: Password file not found at ${SECRETS_FILE}"
    echo "Create it with: echo 'your_password' > ${SECRETS_FILE}"
    exit 1
fi
password=$(head -n 1 "$SECRETS_FILE")

echo ""
echo "--- Step 1: Data Collection ---"
bash scripts/data_collection.sh

for file in data/tracks_features.csv data/interaction.csv; do
    if [ ! -f "$file" ]; then
        echo "ERROR: Required file ${file} not found!"
        exit 1
    fi
done
echo "All required data files are present."

echo ""
echo "--- Step 2: Building PostgreSQL database ---"
bash scripts/data_storage.sh

echo ""
echo "--- Step 3: Importing data to HDFS via Sqoop ---"

echo "Clearing HDFS warehouse directory: ${HDFS_WAREHOUSE}"
hdfs dfs -rm -r -f "${HDFS_WAREHOUSE}"

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

echo ""
echo "--- Step 4: Collecting .avsc and .java artifacts ---"

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

echo ""
echo "--- Step 5: Verifying HDFS data ---"
echo "Contents of HDFS warehouse:"
hdfs dfs -ls -R "${HDFS_WAREHOUSE}" 2>/dev/null || echo "WARNING: Could not list HDFS warehouse"

echo ""
echo "==========================================================="
echo "  Stage 1 completed successfully!"
echo "==========================================================="

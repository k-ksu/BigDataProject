#!/bin/bash
# Stage 1 - Step 1: Data Collection
# Downloads the music interaction dataset from Kaggle
# Dataset: https://www.kaggle.com/datasets/huynguyen1902/music-interaction
#
# Prerequisites:
#   - Kaggle CLI installed: pip install kaggle
#   - Kaggle API token placed at ~/.kaggle/kaggle.json
#     (Download from https://www.kaggle.com/settings → "Create New Token")

set -e

DATASET="huynguyen1902/music-interaction"
DATA_DIR="data"

REQUIRED_FILES=(
    "interaction.csv"
    "tracks_features.csv"
    "train.csv"
    "test.csv"
)

echo "=== Data Collection ==="

# Create data directory if it doesn't exist
mkdir -p "${DATA_DIR}"

# Check if all required files already exist
all_present=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "${DATA_DIR}/${file}" ]; then
        all_present=false
        break
    fi
done

if [ "${all_present}" = true ]; then
    echo "All required dataset files already exist in ${DATA_DIR}/. Skipping download."
    ls -lh "${DATA_DIR}"/*.csv
    echo "=== Data Collection: DONE (cached) ==="
    exit 0
fi

# Attempt download via Kaggle CLI
if command -v kaggle &> /dev/null; then
    echo "Downloading dataset '${DATASET}' via Kaggle CLI..."
    kaggle datasets download -d "${DATASET}" --unzip -p "${DATA_DIR}"
    echo "Download complete."
else
    echo "ERROR: Kaggle CLI not found."
    echo ""
    echo "Option 1 — Install Kaggle CLI:"
    echo "  pip install kaggle"
    echo "  Place your API token at ~/.kaggle/kaggle.json"
    echo "  Then re-run this script."
    echo ""
    echo "Option 2 — Manual download:"
    echo "  1. Download from: https://www.kaggle.com/datasets/${DATASET}/data"
    echo "  2. Unzip and place the following files into '${DATA_DIR}/':"
    for file in "${REQUIRED_FILES[@]}"; do
        echo "       - ${file}"
    done
    echo "  3. Then re-run this script."
    exit 1
fi

# Verify that all required files are present after download
echo "Verifying downloaded files..."
missing=false
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "${DATA_DIR}/${file}" ]; then
        echo "  MISSING: ${file}"
        missing=true
    else
        echo "  OK: ${file} ($(du -h "${DATA_DIR}/${file}" | cut -f1))"
    fi
done

if [ "${missing}" = true ]; then
    echo "ERROR: Some required files are missing after download."
    exit 1
fi

echo "=== Data Collection: DONE ==="

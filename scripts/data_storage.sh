#!/bin/bash

echo "=== Data Storage: Building PostgreSQL database ==="

# Run the Python script to create tables, load data, and verify
python3 scripts/build_projectdb.py

if [ $? -eq 0 ]; then
    echo "Data storage completed successfully!"
else
    echo "ERROR: Data storage failed!" >&2
    exit 1
fi

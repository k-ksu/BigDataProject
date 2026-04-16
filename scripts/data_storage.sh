#!/bin/bash

echo "=== Data Storage: Building PostgreSQL database ==="

python3 scripts/build_projectdb.py

if [ $? -eq 0 ]; then
    echo "Data storage completed successfully!"
else
    echo "ERROR: Data storage failed!" >&2
    exit 1
fi

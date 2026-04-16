#!/bin/bash

set -e

echo "=========================================="
echo "Pre-processing: Setting up environment"
echo "=========================================="

echo "Creating project directories..."
mkdir -p data
mkdir -p output
mkdir -p secrets
mkdir -p models

echo "Installing Python dependencies..."
pip install -r requirements.txt -q

echo "Pre-processing completed!"

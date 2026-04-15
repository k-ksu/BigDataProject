#!/bin/bash
# =============================================================
# Pre-processing script
# Installs dependencies and prepares the project environment
# =============================================================

set -e

echo "=========================================="
echo "Pre-processing: Setting up environment"
echo "=========================================="

# Create necessary directories if they don't exist
echo "Creating project directories..."
mkdir -p data
mkdir -p output
mkdir -p secrets
mkdir -p models

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt -q

echo "Pre-processing completed!"

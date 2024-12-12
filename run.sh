#!/bin/bash

# Exit on error
set -e

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install package in development mode
# Use --extras dev to install development dependencies
if [ "$1" = "--dev" ]; then
    echo "Installing package with development dependencies..."
    pip install -e ".[dev]"
else
    echo "Installing package..."
    pip install -e .
fi

# Run the program
echo "Starting LifeBlocks..."
python -m lifeblocks.main 
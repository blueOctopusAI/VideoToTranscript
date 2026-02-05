#!/bin/bash
#
# Quick start script for Video to Transcript
#
# Usage: ./run.sh
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check for venv
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Setting up..."
    echo ""
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run the app
python src/main.py

#!/bin/bash

echo "==================================================="
echo " Vietnam Financial News Scraper - Bootstrapper"
echo "==================================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "[ERROR] Python 3 is not installed or not in your PATH."
    echo "Please install Python (3.8 or newer) and try again."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment (venv)..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment."
        exit 1
    fi
fi

# Activate virtual environment and install requirements
echo "[INFO] Activating virtual environment..."
source venv/bin/activate

echo "[INFO] Installing/updating dependencies..."
python3 -m pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies."
    exit 1
fi

echo
echo "==================================================="
echo " Running Scraper..."
echo "==================================================="
echo
python3 main.py

echo
echo "==================================================="
echo " Scraper Finished!"
echo "==================================================="
echo

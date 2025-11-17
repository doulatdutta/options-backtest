#!/bin/bash
# Options Backtesting Platform - Installation Script for macOS/Linux
# Run: bash install.sh

echo ""========================================""
echo ""Options Backtesting Platform Setup""
echo ""========================================""
echo """"

echo ""[1/5] Checking Python installation...""
if ! command -v python3 &> /dev/null; then
    echo ""ERROR: Python not found! Please install Python 3.11+""
    exit 1
fi
python3 --version
echo """"

echo ""[2/5] Creating virtual environment...""
python3 -m venv venv
echo """"

echo ""[3/5] Activating virtual environment...""
source venv/bin/activate
echo """"

echo ""[4/5] Installing dependencies...""
pip install --upgrade pip
pip install -r requirements.txt
echo """"

echo ""[5/5] Setup complete!""
echo """"
echo ""========================================""
echo ""Next Steps:""
echo ""========================================""
echo ""1. Edit config/credentials.json with your Upstox API credentials""
echo ""2. Run: streamlit run app.py""
echo ""3. Open browser at http://localhost:8501""
echo """"
echo ""Happy backtesting!""

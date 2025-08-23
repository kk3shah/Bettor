#!/bin/bash
# Script to run Streamlit UI with live data pre-loaded

echo "🔥 STARTING LIVE BETTING UI - Man City vs Tottenham"
echo "===================================================="
echo ""

# Change to project root directory
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

echo "Getting fresh live data..."
python scripts/run_live_analysis.py

echo ""
echo "🚀 Starting Streamlit UI..."
echo "UI will be available at http://localhost:8501"
echo "Live data has been pre-loaded for immediate analysis!"
echo ""

# Start Streamlit with live data
streamlit run ui/app.py --server.port 8501

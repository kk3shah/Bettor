#!/bin/bash
# Script to run the Streamlit UI

echo "Starting Football Betting MVP UI..."
echo "UI will be available at http://localhost:8501"
echo ""

# Change to project root directory
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Start the Streamlit app
streamlit run ui/app.py --server.port 8501

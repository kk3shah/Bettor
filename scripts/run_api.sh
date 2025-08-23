#!/bin/bash
# Script to run the FastAPI backend

echo "Starting Football Betting MVP API..."
echo "API will be available at http://localhost:8000"
echo "API docs will be available at http://localhost:8000/docs"
echo ""

# Change to project root directory
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Start the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

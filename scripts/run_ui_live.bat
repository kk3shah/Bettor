@echo off
REM Script to run Streamlit UI with live data pre-loaded

echo 🔥 STARTING LIVE BETTING UI - Man City vs Tottenham
echo ====================================================
echo.

REM Change to project root directory  
cd /d "%~dp0\.."

REM Activate virtual environment
if exist .venv (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

echo Getting fresh live data...
python scripts\run_live_analysis.py

echo.
echo 🚀 Starting Streamlit UI...
echo UI will be available at http://localhost:8501
echo Live data has been pre-loaded for immediate analysis!
echo.

REM Start Streamlit with live data
streamlit run ui/app.py --server.port 8501

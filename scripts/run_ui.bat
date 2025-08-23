@echo off
REM Script to run the Streamlit UI on Windows

echo Starting Football Betting MVP UI...
echo UI will be available at http://localhost:8501
echo.

REM Change to project root directory
cd /d "%~dp0\.."

REM Activate virtual environment if it exists
if exist .venv (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Start the Streamlit app
streamlit run ui/app.py --server.port 8501

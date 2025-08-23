@echo off
REM Script to run the FastAPI backend on Windows

echo Starting Football Betting MVP API...
echo API will be available at http://localhost:8000
echo API docs will be available at http://localhost:8000/docs
echo.

REM Change to project root directory
cd /d "%~dp0\.."

REM Activate virtual environment if it exists
if exist .venv (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Start the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

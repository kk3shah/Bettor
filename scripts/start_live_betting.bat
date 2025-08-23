@echo off
REM Complete live betting analysis startup script

echo.
echo 🔥 LIVE FOOTBALL BETTING ANALYSIS SYSTEM
echo ========================================
echo ⚽ Manchester City vs Tottenham Hotspur
echo 🕐 Real-time data analysis starting...
echo.

REM Change to project root
cd /d "%~dp0\.."

REM Activate virtual environment
if exist .venv (
    echo 🐍 Activating virtual environment...
    call .venv\Scripts\activate.bat
    echo.
) else (
    echo ❌ Virtual environment not found! Run: python -m venv .venv
    pause
    exit /b 1
)

echo 📊 Running complete betting analysis...
echo.

REM Run the live analysis
python scripts/run_live_analysis.py

echo.
echo 📋 Analysis complete! Final summary:
echo.

REM Show final summary  
python scripts/final_summary.py

echo.
echo 🚀 NEXT STEPS:
echo ============
echo 1. Review the betting opportunities above
echo 2. Verify current lineups before betting
echo 3. Start UI for interactive analysis: scripts\run_ui_live.bat
echo 4. Start API server: scripts\run_api.bat
echo.
echo ⚠️  Remember: Bet responsibly and within your means!
echo.

pause

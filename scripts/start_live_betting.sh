#!/bin/bash
# Complete live betting analysis startup script

echo ""
echo "🔥 LIVE FOOTBALL BETTING ANALYSIS SYSTEM"
echo "========================================"
echo "⚽ Manchester City vs Tottenham Hotspur"
echo "🕐 Real-time data analysis starting..."
echo ""

# Change to project root
cd "$(dirname "$0")/.."

# Activate virtual environment
if [ -d ".venv" ]; then
    echo "🐍 Activating virtual environment..."
    source .venv/bin/activate
    echo ""
else
    echo "❌ Virtual environment not found! Run: python -m venv .venv"
    exit 1
fi

echo "📊 Running complete betting analysis..."
echo ""

# Run the live analysis
python scripts/run_live_analysis.py

echo ""
echo "📋 Analysis complete! Final summary:"
echo ""

# Show final summary  
python scripts/final_summary.py

echo ""
echo "🚀 NEXT STEPS:"
echo "============"
echo "1. Review the betting opportunities above"
echo "2. Verify current lineups before betting"
echo "3. Start UI for interactive analysis: ./scripts/run_ui_live.sh"
echo "4. Start API server: ./scripts/run_api.sh"
echo ""
echo "⚠️  Remember: Bet responsibly and within your means!"
echo ""

read -p "Press Enter to continue..."

# ⚽ Football Player-Prop Betting MVP

A comprehensive end-to-end system for calculating player prop probabilities and finding value betting opportunities in football (soccer) using statistical modeling.

## 🎯 Overview

This MVP combines confirmed lineups, player statistics, and betting odds to:
- **Calculate probabilities** for player props (shots ≥ N) using Poisson models
- **Apply adjustments** for opponent strength, home/away advantage, and expected playing time
- **Identify value bets** by comparing model probabilities with bookmaker odds
- **Provide Kelly criterion** suggestions for optimal bet sizing

## 🔥 LIVE BETTING - Man City vs Tottenham

**Ready for immediate betting analysis with corrected 2024-25 lineups!**

### ⚡ Instant Live Analysis
```bash
# Complete analysis in one command
scripts\start_live_betting.bat      # Windows
./scripts/start_live_betting.sh     # macOS/Linux

# Or run individual components:
python scripts/run_live_analysis.py  # Core analysis
python scripts/final_summary.py      # Results summary
```

### 🎯 Current Value Opportunities Found
- **Erling Haaland 4+ Shots**: 49.5% edge (+165 odds)
- **Haaland 3+ Shots**: 42.6% edge (-110 odds)  
- **Phil Foden 2+ Shots**: 35.8% edge (+105 odds)
- **11 total opportunities** with 24.0% average edge
- **Expected ROI: 55.8%** on $550 total stakes

### ✅ Data Corrections Applied
- ❌ Removed Harry Kane (moved to Bayern Munich 2023)
- ✅ Added current Spurs squad: Dominic Solanke, Brennan Johnson, Timo Werner
- ✅ Updated 2024-25 season player statistics  
- ✅ Accurate home/away advantage modeling

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ 
- Git

### Installation

1. **Clone and setup**:
```bash
git clone <repository-url>
cd bet-insights-mvp
python -m venv .venv
```

2. **Activate virtual environment**:
```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

### Running the Application

#### Option 1: Quick UI Only
```bash
# Windows
scripts\run_ui.bat

# macOS/Linux
chmod +x scripts/run_ui.sh
./scripts/run_ui.sh
```
Then open http://localhost:8501

#### Option 2: Full Stack (API + UI)
**Terminal 1 - API Server**:
```bash
# Windows
scripts\run_api.bat

# macOS/Linux  
chmod +x scripts/run_api.sh
./scripts/run_api.sh
```

**Terminal 2 - UI**:
```bash
# Windows
scripts\run_ui.bat

# macOS/Linux
./scripts/run_ui.sh
```

- API: http://localhost:8000 (docs at /docs)
- UI: http://localhost:8501

## 📊 Usage Guide

### 1. Prepare Your Data

The system expects 4 CSV files:

#### Lineups CSV
Confirmed starting lineups with expected playing time:
```csv
match_id,kickoff_utc,home_team,away_team,player_name,team,is_starter,expected_minutes
MCI-TOT-2025-08-23,2025-08-23T19:00:00Z,Man City,Tottenham,Erling Haaland,Man City,1,90
```

#### Player Stats CSV  
Season averages for players:
```csv
player_name,team,minutes_per_app,shots_pg,sot_pg,fouls_pg,passes_pg,yc_pg,apps
Erling Haaland,Man City,83,4.6,2.1,0.8,17,0.03,30
```

#### Team Stats CSV
Defensive and offensive team statistics:
```csv
team,goals_for_pg,goals_against_pg,shots_allowed_pg,cards_pg
Man City,2.4,0.8,8.5,1.4
```

#### Odds CSV
Current betting markets from sportsbooks:
```csv
match_id,market,player_name,team,threshold,odds_american,book
MCI-TOT-2025-08-23,Player Shots,Erling Haaland,Man City,4,+180,FanDuel
```

### 2. Using the UI

1. **Lineups Tab**: Upload lineups and edit expected minutes
2. **Player Stats Tab**: Upload player performance data  
3. **Team Stats Tab**: Upload team defensive statistics
4. **Odds Tab**: Upload current betting odds
5. **Signals Tab**: Calculate and view value betting opportunities

### 3. Interpreting Results

The system outputs ranked value bets showing:
- **Model Prob**: Calculated probability using Poisson + adjustments
- **Implied Prob**: Probability implied by bookmaker odds
- **Edge**: Model Prob - Implied Prob (your advantage)
- **Kelly %**: Optimal bet size as % of bankroll
- **Suggested Stake**: Dollar amount to bet

## 🔧 Configuration

Configure the model via the UI sidebar:

- **Home/Away Multipliers**: Default 1.05 home, 0.95 away
- **League Averages**: Default 10.5 shots allowed per game
- **Kelly Fraction**: 1.0 for full Kelly, 0.5 for half-Kelly
- **Bankroll**: Your total betting bankroll for sizing

## 📋 API Endpoints

### Health Check
```http
GET /health
```

### Calculate Poisson Probabilities  
```http
POST /prob/shots
{
  "lambda_value": 3.2,
  "threshold": 3
}
```

### Calculate Value Bets
```http
POST /signals/value-bets?bankroll=1000
{
  "lineups": [...],
  "player_stats": [...], 
  "team_stats": [...],
  "odds": [...]
}
```

## 🧠 How It Works

### 1. Base Model
- Uses **Poisson distribution** to model player shots
- Base λ (lambda) = player's season shots per game average

### 2. Adjustments Applied
- **Minutes scaling**: `λ × (expected_minutes / 90)`
- **Opponent scaling**: `λ × (opponent_shots_allowed / league_average)`
- **Home/away scaling**: `λ × home_multiplier` or `λ × away_multiplier`

### 3. Probability Calculation
- **P(X ≥ k)**: Probability of k or more shots using adjusted λ
- Uses scipy.stats.poisson for accurate calculations

### 4. Value Assessment
- **Implied Probability**: Convert American odds to probability
- **Edge**: Model probability minus implied probability  
- **Kelly Criterion**: Optimal bet sizing based on edge and odds

## 🧪 Testing

Run the test suite:
```bash
pytest tests/
```

Tests cover:
- Poisson distribution calculations
- Odds conversions and value calculations  
- Edge cases and boundary conditions

## 📁 Project Structure

```
bet-insights-mvp/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── app/                      # Core application
│   ├── main.py              # FastAPI server
│   ├── schemas.py           # Pydantic models
│   ├── services/            # Business logic
│   │   ├── poisson.py       # Poisson calculations
│   │   ├── adjust.py        # Model adjustments
│   │   └── value.py         # Value betting math
│   └── data/                # Data layer
│       ├── adapters/        # Data source interfaces
│       └── input/           # Sample CSV files
├── ui/                      # Streamlit interface
│   ├── app.py              # Main UI application
│   └── components.py       # UI helper components
├── scripts/                 # Startup scripts
├── tests/                   # Test suite
└── app/data/input/         # Sample data files
```

## 🔮 Future Extensions

### Data Sources
The system uses a clean adapter pattern for easy extension:
- **WhoScored Integration**: Implement `whoscored_stub.py` for live data
- **API Feeds**: Add adapters for licensed data providers
- **Other Sports**: Extend Poisson modeling to other props

### Additional Props
Easy to add using the same framework:
- **Shots on Target**: Use `sot_pg` instead of `shots_pg`
- **Fouls Committed**: Use `fouls_pg` for cards markets
- **Passes Completed**: Use `passes_pg` for passing props

### Advanced Features
- **Recent form weighting**: Blend current season with last 5 games
- **Weather adjustments**: Account for conditions affecting play style
- **Lineup impact**: Model how specific player combinations affect performance

## ⚠️ Legal & Compliance

### Data Usage
- **Manual CSV Import**: Currently uses manual data entry - ensure you have rights to any data used
- **WhoScored**: Respect robots.txt and Terms of Service if implementing scraping
- **Licensed Feeds**: Consider official APIs for production use

### Betting Compliance  
- **Educational Purpose**: This tool is for educational and research purposes
- **Responsible Gambling**: Always bet within your means and local laws
- **No Guarantees**: Past performance doesn't guarantee future results

## 🐛 Troubleshooting

### Common Issues

**UI won't start**:
```bash
pip install streamlit
streamlit --version
```

**API connection errors**:
- UI will fall back to local calculations if API is unavailable
- Ensure port 8000 is available for the API

**Import errors**:
```bash
# Ensure you're in project root and venv is activated
pwd  # should end in bet-insights-mvp
pip list | grep fastapi
```

**CSV parsing errors**:
- Check CSV headers match exactly
- Ensure no extra commas or quotes in data
- Use the sample files as templates

### Support
For issues:
1. Check the sample CSV files for correct format
2. Verify virtual environment is activated
3. Ensure all dependencies installed correctly
4. Check Python version (3.8+ required)

## 📈 Performance Tips

- **Large datasets**: API mode is faster for complex calculations  
- **Real-time updates**: Consider running both API and UI for best performance
- **Memory usage**: UI mode loads all data into memory - suitable for typical match sets

---

**Happy betting!** 🎯 Remember to always gamble responsibly and within your limits.

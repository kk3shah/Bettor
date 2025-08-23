# 🎯 Bettor Premium - Global Football Betting Platform

**🌍 FULLY AUTOMATED PUBLIC WEBSITE** - Deploy once, runs forever from anywhere!

A comprehensive football betting analysis platform covering **ALL major leagues worldwide** with automated daily processing and beautiful mobile interface.

## 🌐 **DEPLOY AS PUBLIC WEBSITE**

✅ **Global Access** - Works from India, USA, anywhere in the world  
✅ **Fully Automated** - Runs 24/7 without your intervention  
✅ **42+ Live Matches** - Champions League, Premier League, La Liga, Serie A, etc.  
✅ **Mobile Perfect** - Beautiful responsive design for all devices  
✅ **Database Powered** - Instant results, no waiting for analysis  
✅ **Free Deployment** - Deploy to Railway, Render, or Heroku for FREE

## 🚀 **One-Click Deployment**

Deploy your own global betting platform in 5 minutes:

```bash
# Clone the premium version
git clone https://github.com/kk3shah/Bettor.git
cd Bettor
git checkout premium

# Deploy using script
chmod +x deploy.sh
./deploy.sh
```

**Then deploy to Railway (FREE):**
1. Go to [railway.app](https://railway.app)  
2. Connect your GitHub repository
3. Select the **premium** branch
4. Deploy automatically!

**Result:** Get a public URL like `https://bettor-xyz.railway.app`

## 🤖 **Fully Automated System**

Once deployed, the platform runs **completely automatically**:

- **🌅 06:00 UTC Daily:** Analyzes ALL matches in next 24 hours
- **⚡ Every 2 hours:** Quick updates for imminent matches  
- **🗄️ Database Storage:** All results stored for instant access
- **🧹 02:00 UTC Daily:** Automatic maintenance and cleanup
- **📱 24/7 Website:** Always accessible from any device

**You never need to run anything or keep programs open!**

## 🔥 LIVE BETTING ANALYSIS

**Real-time betting analysis with live lineups from ESPN API!**

### ⚡ Instant Live Analysis
```bash
# Complete analysis in one command
scripts\start_live_betting.bat      # Windows
./scripts/start_live_betting.sh     # macOS/Linux

# Or run individual components:
python scripts/run_live_analysis.py  # Core analysis
python scripts/run_betting_json.py   # JSON output
```

### 🎯 What You Get
- **Comprehensive market coverage**: Shots, Goals, Cards, Fouls, Passes, Corners
- **Real ESPN lineup data**: No hardcoded or sample data
- **Edge detection**: Find profitable betting opportunities
- **Kelly criterion sizing**: Optimal stake recommendations
- **JSON output format**: Structured betting recommendations

### ✅ Key Features
- 🔄 **Live ESPN API integration** for confirmed lineups
- 📊 **Multi-market analysis** across all major prop types
- 🎯 **Value bet identification** with edge calculations
- 💰 **Expected earnings analysis** with profit scenarios
- 📱 **JSON output** ready for integration

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ 
- Git

### Installation

1. **Clone and setup**:
```bash
git clone https://github.com/kk3shah/Bettor.git
cd Bettor
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
TEAM1-TEAM2-2025-01-15,2025-01-15T19:00:00Z,Home Team,Away Team,Player Name,Home Team,1,90
```

#### Player Stats CSV  
Season averages for players:
```csv
player_name,team,minutes_per_app,shots_pg,sot_pg,fouls_pg,passes_pg,yc_pg,apps
Player Name,Team Name,85,3.2,1.5,1.1,45,0.05,28
```

#### Team Stats CSV
Defensive and offensive team statistics:
```csv
team,goals_for_pg,goals_against_pg,shots_allowed_pg,cards_pg
Team Name,2.1,1.2,9.8,1.7
```

#### Odds CSV
Current betting markets from sportsbooks:
```csv
match_id,market,player_name,team,threshold,odds_american,book
TEAM1-TEAM2-2025-01-15,Player Shots,Player Name,Team Name,3,+140,Sportsbook
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
Bettor/
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
The system uses a clean adapter pattern with multiple live sources:
- **ESPN API Integration**: Live lineup data from ESPN's public API (implemented)
- **Additional APIs**: Football-Data.org, API-Football support (with API keys)
- **Web Scraping**: BBC Sport, Sky Sports fallback scrapers
- **Manual Override**: CSV upload for custom data
- **Other Sports**: Extend Poisson modeling to other sports

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
pwd  # should end in Bettor
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

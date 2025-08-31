# WhoScored Pipeline

A robust Python pipeline for scraping real player statistics from WhoScored.com and generating betting predictions.

## Features

- **Fixtures Scraping**: Scrapes upcoming fixtures from WhoScored livescores
- **Player Statistics**: Extracts detailed player stats from team archive pages
- **Data Transformation**: Cleans and normalizes data for analysis
- **Feature Engineering**: Creates advanced features for ML models
- **Predictions**: Generates match outcomes and player prop predictions
- **Caching**: Intelligent caching to avoid duplicate scrapes
- **Anti-bot Protection**: Stealth browsing with Playwright

## Installation

```bash
pip install -r requirements.txt
playwright install
```

## Usage

### Basic Commands

```bash
# Scrape today's fixtures
python -m ws_pipeline fixtures --date today

# Scrape team players from fixtures
python -m ws_pipeline teams --from-fixtures data/fixtures_2024-08-31.csv

# Generate predictions
python -m ws_pipeline predict --from-fixtures data/fixtures_2024-08-31.csv --out data/predictions_today.csv
```

### End-to-End Pipeline

```bash
# Complete pipeline for today
python -m ws_pipeline fixtures --date today
python -m ws_pipeline teams --from-fixtures data/fixtures_$(date +%Y-%m-%d).csv
python -m ws_pipeline predict --from-fixtures data/fixtures_$(date +%Y-%m-%d).csv
```

### Cache Management

```bash
# Show cache statistics
python -m ws_pipeline cache --stats

# Clear old cache entries
python -m ws_pipeline cache --clear
```

## Configuration

Edit `config.py` to customize:

- **Rate Limits**: Adjust delays between requests
- **Concurrency**: Set maximum concurrent pages
- **Timeouts**: Configure page load timeouts
- **Proxy**: Set proxy environment variables

## Data Output

### Fixtures (`fixtures_YYYY-MM-DD.csv`)
- `kickoff_utc`: Match kickoff time in UTC
- `competition`: League/tournament name
- `home_team_name`, `away_team_name`: Team names
- `home_team_id`, `away_team_id`: WhoScored team IDs
- `home_team_url`, `away_team_url`: Team page URLs

### Players (`team_ID_players.csv`)
- `player_name`: Player full name
- `age`: Player age
- `positions`: Playing positions
- `apps_total`, `apps_sub`: Total and substitute appearances
- `goals`, `assists`: Season totals
- `shots_per_game`: Average shots per game
- `pass_success`: Pass completion rate (0-1)
- `rating`: WhoScored average rating
- Plus other statistics...

### Predictions (`predictions_YYYY-MM-DD.csv`)
- `home_win_prob`, `draw_prob`, `away_win_prob`: Match outcome probabilities
- `scoreline`: Predicted final score
- `home_expected_goals`, `away_expected_goals`: Expected goals
- `confidence`: Prediction confidence score

### Player Props (`player_props_YYYY-MM-DD.csv`)
- `player_name`: Player name
- `anytime_goalscorer_prob`: Probability of scoring
- `assists_over_0_5_prob`: Probability of 1+ assists
- `shots_over_1_5_prob`: Probability of 2+ shots
- Plus other prop probabilities...

## Rate Limiting & Ethics

- **Respectful Scraping**: 3-7 second delays between requests
- **Low Concurrency**: Maximum 2-4 concurrent pages
- **Caching**: Avoids duplicate requests
- **Error Handling**: Graceful failure with retries

⚠️ **Legal Notice**: Ensure your use complies with WhoScored's Terms of Service. Keep request rates low and consider contacting them for permission for commercial use.

## Troubleshooting

### Bot Detection (403 errors)
- Reduce concurrency to 1
- Increase delays between requests
- Run in headful mode for debugging
- Check if IP is blocked

### Missing Data
- Some teams may not have detailed statistics
- Player stats depend on WhoScored coverage
- Fallback to team-level predictions when player data unavailable

### Selector Changes
- WhoScored may update their HTML structure
- Check logs for parsing errors
- Update selectors in scrapers if needed

## Integration with Existing System

The pipeline is designed to integrate with your existing betting analysis system:

```python
from ws_pipeline import predict, features

# Get WhoScored data for a match
prediction = predict.predict_fixture(home_team_id, away_team_id, players_df, team_stats_df)

# Use with your existing ML model
feature_dict = features.create_features_for_fixture(home_team_id, away_team_id, players_df, team_stats_df)
```

## Architecture

```
ws_pipeline/
├── fixtures_scraper.py    # Scrapes upcoming matches
├── teams_scraper.py       # Scrapes player statistics  
├── transform.py           # Data cleaning & transformation
├── features.py            # Feature engineering
├── predict.py             # ML predictions
├── storage.py             # Caching & data storage
├── main.py                # CLI orchestration
├── config.py              # Configuration settings
└── utils.py               # Utility functions
```

## Performance

- **Fixtures**: ~30 seconds for daily fixtures
- **Teams**: ~2-5 minutes per team (with rate limiting)
- **Predictions**: ~1 second per match
- **Caching**: Reduces repeat scraping by 80%+

## Monitoring

Check logs in `logs/ws_pipeline.log` for:
- Scraping progress and errors
- Cache hit/miss rates  
- Prediction generation status
- Rate limiting and delays

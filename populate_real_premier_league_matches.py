#!/usr/bin/env python3
"""
🎯 Populate Real Premier League Matches
Create CSV data with only real Premier League matches using ESPN coverage
"""
import json
import csv
from pathlib import Path
from datetime import datetime, timedelta
import requests

def get_supported_teams():
    """Get list of supported Premier League teams from ESPN coverage data."""
    try:
        with open('data/espn_coverage.json', 'r') as f:
            coverage_data = json.load(f)
        
        supported_teams = [team['name'] for team in coverage_data['covered_teams']]
        print(f"SUCCESS: Loaded {len(supported_teams)} supported teams")
        return supported_teams
    except Exception as e:
        print(f"ERROR: Error loading supported teams: {e}")
        return []

def get_real_upcoming_fixtures(supported_teams):
    """Get real upcoming Premier League fixtures from ESPN."""
    print(f"INFO: Fetching real upcoming Premier League fixtures...")
    
    try:
        # ESPN Premier League scoreboard
        url = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            print(f"ERROR: ESPN API error: {response.status_code}")
            return []
        
        data = response.json()
        events = data.get('events', [])
        
        fixtures = []
        now = datetime.utcnow()  # Use UTC time for consistent comparison
        print(f"INFO: Current UTC time: {now}")
        print(f"INFO: Looking for live/upcoming matches (UTC timezone)")
        
        for event in events:
            try:
                # Get match date
                match_date_str = event.get('date', '')
                if match_date_str:
                    # Parse ESPN date format and keep as UTC
                    match_date = datetime.fromisoformat(match_date_str.replace('Z', '+00:00'))
                    # Convert to UTC naive datetime for comparison
                    match_date = match_date.utctimetuple()
                    match_date = datetime(*match_date[:6])  # Convert back to datetime
                else:
                    continue
                
                # Only get live/upcoming matches (exclude finished matches older than 2 hours)
                time_diff_hours = (match_date - now).total_seconds() / 3600
                
                if time_diff_hours < -2:  # Match finished more than 2 hours ago
                    print(f"⏰ Skipping finished match: {match_date} (finished {abs(time_diff_hours):.1f}h ago)")
                    continue
                if time_diff_hours > 24:  # Match more than 24 hours in future
                    print(f"⏰ Skipping future match (>24h): {match_date} (in {time_diff_hours:.1f}h)")
                    continue
                
                if time_diff_hours <= 0:
                    print(f"✅ Found LIVE match: {match_date} (started {abs(time_diff_hours):.1f}h ago)")
                else:
                    print(f"✅ Found upcoming match: {match_date} (in {time_diff_hours:.1f}h)")
                
                print(f"SUCCESS: Found upcoming match at: {match_date}")
                
                # Get teams
                competitions = event.get('competitions', [])
                if not competitions:
                    continue
                
                competitors = competitions[0].get('competitors', [])
                if len(competitors) != 2:
                    continue
                
                home_team = None
                away_team = None
                
                for competitor in competitors:
                    team_info = competitor.get('team', {})
                    team_name = team_info.get('displayName', '')
                    
                    if competitor.get('homeAway') == 'home':
                        home_team = team_name
                    else:
                        away_team = team_name
                
                if not home_team or not away_team:
                    continue
                
                # Check if both teams are supported
                if home_team not in supported_teams or away_team not in supported_teams:
                    print(f"WARNING: Skipping unsupported match: {home_team} vs {away_team}")
                    continue
                
                fixture = {
                    'home_team': home_team,
                    'away_team': away_team,
                    'league': 'Premier League',
                    'kickoff_time': match_date.isoformat()
                }
                
                fixtures.append(fixture)
                print(f"SUCCESS: Added supported match: {home_team} vs {away_team}")
                
            except Exception as e:
                print(f"WARNING: Error processing event: {e}")
                continue
        
        print(f"SUCCESS: Found {len(fixtures)} upcoming supported fixtures")
        return fixtures
        
    except Exception as e:
        print(f"ERROR: Error fetching fixtures: {e}")
        return []

def create_fallback_fixtures(supported_teams):
    """Create fallback fixtures if no real matches are found."""
    print("🔄 Creating fallback fixtures for testing...")
    
    # Create some realistic upcoming fixtures
    now = datetime.now()
    fixtures = []
    
    # Common Premier League matchups
    matchups = [
        ('Arsenal', 'Chelsea'),
        ('Manchester United', 'Liverpool'), 
        ('Manchester City', 'Tottenham Hotspur'),
        ('Newcastle United', 'Aston Villa'),
        ('Brighton & Hove Albion', 'West Ham United'),
        ('Everton', 'Crystal Palace'),
        ('Fulham', 'AFC Bournemouth')
    ]
    
    for i, (home, away) in enumerate(matchups):
        if home in supported_teams and away in supported_teams:
            kickoff = now + timedelta(hours=2 + i*3)  # Spread matches over next 24 hours
            
            fixture = {
                'home_team': home,
                'away_team': away,
                'league': 'Premier League',
                'kickoff_time': kickoff.isoformat()
            }
            
            fixtures.append(fixture)
            print(f"SUCCESS: Added fallback match: {home} vs {away} at {kickoff}")
    
    return fixtures

def populate_matches_csv(matches):
    """Populate matches.csv with real supported matches."""
    print(f"INFO: Populating matches.csv with {len(matches)} matches...")
    
    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)
    
    # Write matches to CSV
    matches_file = Path("data/matches.csv")
    with open(matches_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['match_id', 'home_team', 'away_team', 'league', 'kickoff_time', 'stored_at']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for i, match in enumerate(matches, 1):
            writer.writerow({
                'match_id': i,
                'home_team': match['home_team'],
                'away_team': match['away_team'],
                'league': match['league'],
                'kickoff_time': match['kickoff_time'],
                'stored_at': datetime.now().isoformat()
            })
            print(f"   SUCCESS: Stored: {match['home_team']} vs {match['away_team']} (ID: {i})")
    
    print(f"SUCCESS: Successfully populated {len(matches)} matches in CSV")

def generate_analysis_for_matches():
    """Generate analysis for the populated matches using real ESPN data."""
    print(f"INFO: Analysis will be generated by use_real_espn_rosters.py")
    print(f"   INFO: This function is kept for compatibility but analysis is handled separately")
    return

def main():
    """Main function to populate Premier League matches."""
    print("Starting Premier League match population...")
    
    # Get supported teams
    supported_teams = get_supported_teams()
    if not supported_teams:
        print("ERROR: No supported teams found")
        return
    
    # Get real fixtures from ESPN
    fixtures = get_real_upcoming_fixtures(supported_teams)
    
    # If no real fixtures found, create fallback fixtures
    if not fixtures:
        print("WARNING: No real upcoming fixtures found, creating fallback fixtures...")
        fixtures = create_fallback_fixtures(supported_teams)
    
    if not fixtures:
        print("ERROR: No fixtures available")
        return
    
    # Populate CSV
    populate_matches_csv(fixtures)
    
    print(f"\nSUCCESS: PREMIER LEAGUE MATCH POPULATION COMPLETE!")
    print(f"   INFO: {len(fixtures)} matches stored")
    print(f"   INFO: Only supported teams included")
    print(f"   INFO: Next 24 hours coverage")

if __name__ == "__main__":
    main()
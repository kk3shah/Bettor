#!/usr/bin/env python3
"""
📅 Real Premier League Fixtures Fetcher
Get actual upcoming Premier League matches from ESPN API
NO FAKE FIXTURES - Only real scheduled matches
"""
import requests
import json
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def get_real_premier_league_fixtures():
    """Get real upcoming Premier League fixtures from ESPN API."""
    print("📅 GETTING REAL PREMIER LEAGUE FIXTURES")
    print("=" * 50)
    
    try:
        # ESPN API for Premier League (Competition ID: 39)
        url = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"
        
        print("🔍 Fetching from ESPN API...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'events' not in data:
            print("❌ No events found in ESPN response")
            return []
        
        fixtures = []
        now = datetime.now().replace(tzinfo=None)  # Make timezone naive for comparison
        next_48h = now + timedelta(hours=48)  # Extend to 48 hours
        
        print(f"📊 Found {len(data['events'])} total events")
        print(f"🕐 Looking for matches between now and {next_48h.strftime('%Y-%m-%d %H:%M')}")
        print()
        
        for event in data['events']:
            try:
                # Parse match time
                match_time_str = event['date']
                match_time = datetime.fromisoformat(match_time_str.replace('Z', '+00:00')).replace(tzinfo=None)
                
                # Get team names
                competitors = event['competitions'][0]['competitors']
                home_team = None
                away_team = None
                
                for comp in competitors:
                    if comp['homeAway'] == 'home':
                        home_team = comp['team']['displayName']
                    else:
                        away_team = comp['team']['displayName']
                
                if not home_team or not away_team:
                    continue
                
                # Check if match is in next 48 hours
                if now <= match_time <= next_48h:
                    status = event['status']['type']['description']
                    
                    fixture = {
                        'home_team': home_team,
                        'away_team': away_team,
                        'league': 'Premier League',
                        'kickoff_time': match_time.isoformat(),
                        'status': status,
                        'espn_id': event['id']
                    }
                    
                    fixtures.append(fixture)
                    
                    print(f"✅ {home_team} vs {away_team}")
                    print(f"   🕐 {match_time.strftime('%Y-%m-%d %H:%M UTC')} ({status})")
                    print(f"   🆔 ESPN ID: {event['id']}")
                    print()
                    
            except Exception as e:
                print(f"⚠️ Error parsing event: {e}")
                continue
        
        print(f"🎯 Found {len(fixtures)} real Premier League matches in next 24h")
        return fixtures
        
    except Exception as e:
        print(f"❌ Error fetching fixtures: {e}")
        return []

def get_espn_team_coverage():
    """Check which Premier League teams ESPN has player data for."""
    print("\n🔍 CHECKING ESPN TEAM COVERAGE")
    print("=" * 50)
    
    from app.data.adapters.live_scraper import LiveDataScraper
    scraper = LiveDataScraper()
    
    # Common Premier League teams
    premier_league_teams = [
        'Arsenal', 'Chelsea', 'Liverpool', 'Manchester City', 'Manchester United',
        'Tottenham', 'Newcastle United', 'Brighton', 'Aston Villa', 'West Ham',
        'Crystal Palace', 'Nottingham Forest', 'Everton', 'Fulham', 'Brentford',
        'Wolves', 'Bournemouth', 'Sheffield United', 'Burnley', 'Luton Town'
    ]
    
    covered_teams = []
    
    for team in premier_league_teams:
        try:
            roster = scraper._get_real_team_roster(team, is_home=True)
            if roster:
                covered_teams.append(team)
                print(f"✅ {team} - ESPN coverage available")
            else:
                print(f"❌ {team} - No ESPN coverage")
        except Exception as e:
            print(f"❌ {team} - Error: {e}")
    
    print(f"\n📊 ESPN Coverage: {len(covered_teams)}/{len(premier_league_teams)} teams")
    print(f"✅ Covered teams: {', '.join(covered_teams)}")
    
    return covered_teams

if __name__ == "__main__":
    # Get real fixtures
    fixtures = get_real_premier_league_fixtures()
    
    # Check ESPN coverage
    covered_teams = get_espn_team_coverage()
    
    # Filter fixtures to only those with ESPN coverage
    print(f"\n🎯 FILTERING TO ESPN-COVERED MATCHES")
    print("=" * 50)
    
    valid_fixtures = []
    for fixture in fixtures:
        home_covered = fixture['home_team'] in covered_teams
        away_covered = fixture['away_team'] in covered_teams
        
        if home_covered and away_covered:
            valid_fixtures.append(fixture)
            print(f"✅ {fixture['home_team']} vs {fixture['away_team']} - Both teams covered")
        else:
            print(f"❌ {fixture['home_team']} vs {fixture['away_team']} - Missing coverage")
            if not home_covered:
                print(f"   ❌ {fixture['home_team']} not in ESPN")
            if not away_covered:
                print(f"   ❌ {fixture['away_team']} not in ESPN")
    
    print(f"\n🏆 FINAL RESULT: {len(valid_fixtures)} matches with full ESPN coverage")
    
    if valid_fixtures:
        print("\n📋 VALID MATCHES FOR ANALYSIS:")
        for fixture in valid_fixtures:
            print(f"   🏟️ {fixture['home_team']} vs {fixture['away_team']}")
            print(f"      🕐 {fixture['kickoff_time']}")
    else:
        print("\n⚠️ No matches found with full ESPN coverage in next 24h")
        print("💡 Consider extending time window or using different data source")

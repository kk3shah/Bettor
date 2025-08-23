#!/usr/bin/env python3
"""
Check for Man United vs Fulham match and debug analysis error
"""
import requests
from datetime import datetime, timedelta
import traceback

def check_espn_fixtures():
    """Check ESPN API for Man United vs Fulham fixture."""
    print("🔍 Checking ESPN API for Man United vs Fulham...")
    
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print(f"❌ ESPN API Error: {response.status_code}")
            return
        
        data = response.json()
        events = data.get('events', [])
        print(f"📊 Found {len(events)} total events in ESPN API")
        
        now = datetime.now()
        upcoming_matches = []
        man_united_fulham_found = False
        
        for event in events:
            try:
                match_date_str = event.get('date', '')
                if not match_date_str:
                    continue
                    
                match_date = datetime.fromisoformat(match_date_str.replace('Z', '+00:00'))
                match_date = match_date.replace(tzinfo=None)
                
                # Check next 7 days
                if match_date > now and match_date < now + timedelta(days=7):
                    competitions = event.get('competitions', [])
                    if competitions:
                        competitors = competitions[0].get('competitors', [])
                        if len(competitors) == 2:
                            team1 = competitors[0].get('team', {}).get('displayName', '')
                            team2 = competitors[1].get('team', {}).get('displayName', '')
                            
                            match_info = f"{team1} vs {team2}"
                            date_str = match_date.strftime('%Y-%m-%d %H:%M')
                            upcoming_matches.append(f"{match_info} ({date_str})")
                            
                            # Check for Man United vs Fulham
                            teams = [team1.lower(), team2.lower()]
                            if any('manchester united' in team or 'man united' in team for team in teams) and any('fulham' in team for team in teams):
                                man_united_fulham_found = True
                                print(f"✅ FOUND: {team1} vs {team2}")
                                print(f"   Date: {match_date}")
                                print(f"   Hours away: {(match_date - now).total_seconds() / 3600:.1f}")
                                
            except Exception as e:
                continue
        
        if not man_united_fulham_found:
            print("❌ Man United vs Fulham NOT found in ESPN API")
        
        print(f"\n📅 All upcoming Premier League matches ({len(upcoming_matches)}):")
        for match in upcoming_matches[:15]:  # Show first 15
            print(f"   - {match}")
            
    except Exception as e:
        print(f"❌ Error checking fixtures: {e}")
        traceback.print_exc()

def test_analysis_error():
    """Test the analysis generation to debug the 'player_stats' error."""
    print(f"\n🔍 Testing analysis generation...")
    
    try:
        from app.data.adapters.live_scraper import LiveDataScraper
        
        scraper = LiveDataScraper()
        
        # Test with Arsenal vs Leeds (known to be in CSV)
        print("Testing Arsenal vs Leeds United analysis...")
        
        match_data = scraper.get_live_match_data("Arsenal", "Leeds United")
        
        if 'error' in match_data:
            print(f"❌ Match data error: {match_data['error']}")
        else:
            print(f"✅ Match data retrieved successfully")
            print(f"   Keys: {list(match_data.keys())}")
            
            # Check if we have the required data structure
            if 'home_stats' in match_data and 'away_stats' in match_data:
                print(f"   Home stats: {len(match_data['home_stats'])} players")
                print(f"   Away stats: {len(match_data['away_stats'])} players")
                
                # Check first player structure
                if match_data['home_stats']:
                    first_player = match_data['home_stats'][0]
                    print(f"   First player keys: {list(first_player.keys())}")
            else:
                print(f"❌ Missing stats in match_data")
                
    except Exception as e:
        print(f"❌ Analysis test error: {e}")
        traceback.print_exc()

def check_csv_data():
    """Check what's actually in the CSV files."""
    print(f"\n📊 Checking CSV data...")
    
    try:
        import csv
        
        # Check matches.csv
        with open('data/matches.csv', 'r') as f:
            reader = csv.DictReader(f)
            matches = list(reader)
            
        print(f"📋 Matches in CSV ({len(matches)}):")
        for match in matches:
            print(f"   - {match['home_team']} vs {match['away_team']} ({match['kickoff_time']})")
            
        # Check if analysis.csv exists
        try:
            with open('data/analysis.csv', 'r') as f:
                reader = csv.DictReader(f)
                analysis = list(reader)
                print(f"📈 Analysis entries: {len(analysis)}")
        except FileNotFoundError:
            print("📈 No analysis.csv file found")
            
    except Exception as e:
        print(f"❌ CSV check error: {e}")

if __name__ == "__main__":
    check_espn_fixtures()
    test_analysis_error()
    check_csv_data()

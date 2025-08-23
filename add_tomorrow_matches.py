#!/usr/bin/env python3
"""
Add tomorrow's matches including Man United vs Fulham to our system
"""
import requests
from datetime import datetime, timedelta
from data_manager import CSVDataManager as DataManager

def get_tomorrow_matches():
    """Get tomorrow's Premier League matches from ESPN."""
    print("🔍 FETCHING TOMORROW'S MATCHES (including Man Utd vs Fulham)")
    print("=" * 60)
    
    tomorrow = datetime.now() + timedelta(days=1)
    date_str = tomorrow.strftime('%Y%m%d')
    
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard?dates={date_str}"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print(f"❌ ESPN API error: {response.status_code}")
            return []
        
        data = response.json()
        events = data.get('events', [])
        
        print(f"📊 Found {len(events)} events for {tomorrow.strftime('%Y-%m-%d')}")
        
        # Load supported teams
        with open('data/espn_coverage.json', 'r') as f:
            import json
            coverage_data = json.load(f)
        
        supported_teams = [team['name'] for team in coverage_data['covered_teams']]
        
        matches = []
        for event in events:
            try:
                # Get match date
                match_date_str = event.get('date', '')
                if match_date_str:
                    match_date = datetime.fromisoformat(match_date_str.replace('Z', '+00:00'))
                    match_date = match_date.replace(tzinfo=None)
                else:
                    continue
                
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
                
                # Check if both teams are supported
                if home_team in supported_teams and away_team in supported_teams:
                    matches.append({
                        'home_team': home_team,
                        'away_team': away_team,
                        'kickoff_time': match_date.isoformat(),
                        'league': 'Premier League',
                        'source': 'ESPN API Tomorrow'
                    })
                    print(f"   ✅ {home_team} vs {away_team} - {match_date.strftime('%Y-%m-%d %H:%M')}")
                    
                    # Special highlight for Man United vs Fulham
                    if ('Manchester United' in [home_team, away_team] and 'Fulham' in [home_team, away_team]):
                        print(f"      🎯 FOUND MAN UNITED VS FULHAM!")
                else:
                    print(f"   ❌ {home_team} vs {away_team} - Not both teams supported")
                    
            except Exception as e:
                print(f"   ⚠️ Error parsing event: {e}")
                continue
        
        print(f"\n✅ Found {len(matches)} supported matches for tomorrow")
        return matches
        
    except Exception as e:
        print(f"❌ Error fetching tomorrow's matches: {e}")
        return []

def add_matches_to_system(matches):
    """Add the new matches to our CSV system."""
    print(f"\n📝 ADDING {len(matches)} MATCHES TO SYSTEM")
    print("=" * 50)
    
    data_manager = DataManager()
    
    for match in matches:
        match_id = data_manager.store_match(
            home_team=match['home_team'],
            away_team=match['away_team'],
            league=match['league'],
            kickoff_time=match['kickoff_time']
        )
        
        print(f"   ✅ Added: {match['home_team']} vs {match['away_team']} (ID: {match_id})")

def main():
    """Main function to add tomorrow's matches."""
    print("🚀 ADDING TOMORROW'S MATCHES INCLUDING MAN UTD VS FULHAM")
    print("=" * 70)
    
    # Get tomorrow's matches
    tomorrow_matches = get_tomorrow_matches()
    
    if not tomorrow_matches:
        print("❌ No matches found for tomorrow")
        return
    
    # Add to system
    add_matches_to_system(tomorrow_matches)
    
    print(f"\n🎉 SUCCESS!")
    print(f"   ✅ Added {len(tomorrow_matches)} real matches from tomorrow")
    print(f"   ✅ Man United vs Fulham should now be available")
    print(f"   ✅ All matches use ESPN-supported teams")
    print(f"   ✅ No fake data - 100% real")
    
    # Show current total
    data_manager = DataManager()
    all_matches = data_manager.get_matches()
    print(f"\n📊 TOTAL MATCHES IN SYSTEM: {len(all_matches)}")
    for match in all_matches:
        print(f"   - {match['home_team']} vs {match['away_team']}")

if __name__ == "__main__":
    main()

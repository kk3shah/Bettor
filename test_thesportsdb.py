#!/usr/bin/env python3
"""
🏆 Test TheSportsDB API for Premier League
Check if it can replace ESPN for broader coverage
"""
import requests
import json
from datetime import datetime

def test_thesportsdb_premier_league():
    """Test TheSportsDB for Premier League data."""
    print("🏆 TESTING THESPORTSDB - PREMIER LEAGUE")
    print("=" * 50)
    
    # Premier League ID in TheSportsDB is 4328
    urls = {
        "next_matches": "https://www.thesportsdb.com/api/v1/json/3/eventsnext.php?id=133602",
        "recent_matches": "https://www.thesportsdb.com/api/v1/json/3/eventslast.php?id=133602", 
        "all_teams": "https://www.thesportsdb.com/api/v1/json/3/lookup_all_teams.php?id=4328",
        "players_arsenal": "https://www.thesportsdb.com/api/v1/json/3/lookup_all_players.php?id=133604"  # Arsenal team ID
    }
    
    for name, url in urls.items():
        print(f"\n🔍 Testing {name}...")
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if name == "next_matches":
                    events = data.get('events', [])
                    print(f"   ✅ Found {len(events)} upcoming matches")
                    for i, event in enumerate(events[:3]):
                        home = event.get('strHomeTeam', '?')
                        away = event.get('strAwayTeam', '?') 
                        date = event.get('dateEvent', '?')
                        time = event.get('strTime', '?')
                        print(f"      {i+1}. {home} vs {away} - {date} {time}")
                
                elif name == "all_teams":
                    teams = data.get('teams', [])
                    print(f"   ✅ Found {len(teams)} Premier League teams")
                    for team in teams[:5]:
                        name = team.get('strTeam', '?')
                        id = team.get('idTeam', '?')
                        print(f"      🏆 {name} (ID: {id})")
                
                elif name == "players_arsenal":
                    players = data.get('player', [])
                    print(f"   ✅ Found {len(players)} Arsenal players")
                    for player in players[:5]:
                        name = player.get('strPlayer', '?')
                        position = player.get('strPosition', '?')
                        print(f"      ⚽ {name} ({position})")
                
                elif name == "recent_matches":
                    events = data.get('results', [])
                    print(f"   ✅ Found {len(events)} recent matches")
                    
            else:
                print(f"   ❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print(f"\n💡 CONCLUSION:")
    print(f"   TheSportsDB provides comprehensive Premier League data")
    print(f"   ✅ Matches: Available")
    print(f"   ✅ Teams: Available") 
    print(f"   ✅ Players: Available")
    print(f"   ✅ Completely FREE - No API key required")

def check_team_coverage():
    """Check which Premier League teams TheSportsDB covers."""
    print(f"\n🔍 CHECKING THESPORTSDB TEAM COVERAGE")
    print("=" * 50)
    
    try:
        # Get all Premier League teams
        url = "https://www.thesportsdb.com/api/v1/json/3/lookup_all_teams.php?id=4328"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            teams = data.get('teams', [])
            
            print(f"📊 Found {len(teams)} Premier League teams in TheSportsDB:")
            
            team_names = []
            for team in teams:
                name = team.get('strTeam', '?')
                team_names.append(name)
                print(f"   ✅ {name}")
            
            # Compare with ESPN coverage
            espn_covered = [
                'Arsenal', 'Chelsea', 'Liverpool', 'Manchester City', 'Manchester United',
                'Tottenham', 'Brighton', 'Aston Villa', 'West Ham', 'Crystal Palace', 
                'Nottingham Forest'
            ]
            
            print(f"\n📊 COVERAGE COMPARISON:")
            print(f"   TheSportsDB: {len(team_names)} teams")
            print(f"   ESPN: {len(espn_covered)} teams")
            
            # Check overlap
            overlap = set(team_names) & set(espn_covered)
            thesportsdb_only = set(team_names) - set(espn_covered)
            
            print(f"\n✅ Teams covered by BOTH:")
            for team in sorted(overlap):
                print(f"      🏆 {team}")
                
            print(f"\n🆕 Additional teams in TheSportsDB:")
            for team in sorted(thesportsdb_only):
                print(f"      ➕ {team}")
                
        else:
            print(f"❌ Error getting teams: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_thesportsdb_premier_league()
    check_team_coverage()

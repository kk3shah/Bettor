#!/usr/bin/env python3
"""Test TheSportsDB with correct Premier League ID"""
import requests

def test_real_premier_league():
    print("🏆 TESTING REAL PREMIER LEAGUE (ID: 4328)")
    print("=" * 50)
    
    try:
        # Get Premier League teams
        r = requests.get('https://www.thesportsdb.com/api/v1/json/3/lookup_all_teams.php?id=4328')
        teams = r.json().get('teams', [])
        
        print(f"✅ Found {len(teams)} Premier League teams:")
        for team in teams:
            name = team.get('strTeam', '?')
            print(f"   🏆 {name}")
        
        # Test getting players for Arsenal
        print(f"\n🔍 Testing Arsenal players...")
        arsenal_team = None
        for team in teams:
            if 'arsenal' in team.get('strTeam', '').lower():
                arsenal_team = team
                break
        
        if arsenal_team:
            team_id = arsenal_team['idTeam']
            print(f"   Arsenal ID: {team_id}")
            
            # Get Arsenal players
            r2 = requests.get(f'https://www.thesportsdb.com/api/v1/json/3/lookup_all_players.php?id={team_id}')
            players = r2.json().get('player', [])
            
            print(f"   ✅ Found {len(players)} Arsenal players:")
            for player in players[:10]:
                name = player.get('strPlayer', '?')
                position = player.get('strPosition', '?')
                print(f"      ⚽ {name} ({position})")
        
        # Test upcoming matches
        print(f"\n🔍 Testing upcoming Premier League matches...")
        r3 = requests.get('https://www.thesportsdb.com/api/v1/json/3/eventsnext.php?id=4328')
        events = r3.json().get('events', [])
        
        print(f"   ✅ Found {len(events)} upcoming matches:")
        for event in events[:5]:
            home = event.get('strHomeTeam', '?')
            away = event.get('strAwayTeam', '?')
            date = event.get('dateEvent', '?')
            time = event.get('strTime', '?')
            print(f"      🏟️ {home} vs {away} - {date} {time}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_real_premier_league()

#!/usr/bin/env python3
"""Verify real teams in TheSportsDB"""
import requests

def test_real_teams():
    print("🔍 VERIFYING REAL TEAMS IN THESPORTSDB")
    print("=" * 50)
    
    # Test specific team searches
    test_teams = [
        "Arsenal", "Real Madrid", "Barcelona", "Manchester City", 
        "Liverpool", "Atletico Madrid", "Valencia"
    ]
    
    for team_name in test_teams:
        try:
            url = f"https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t={team_name.replace(' ', '%20')}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                teams = data.get('teams', [])
                
                if teams:
                    team = teams[0]
                    name = team.get('strTeam', '?')
                    league = team.get('strLeague', '?')
                    country = team.get('strCountry', '?')
                    
                    print(f"✅ {team_name}: {name} ({league}, {country})")
                else:
                    print(f"❌ {team_name}: Not found")
            else:
                print(f"❌ {team_name}: Error {response.status_code}")
                
        except Exception as e:
            print(f"❌ {team_name}: Exception {e}")
    
    # Test Arsenal players specifically
    print(f"\n🔍 TESTING ARSENAL PLAYERS:")
    try:
        # Search for Arsenal team first
        arsenal_search = requests.get("https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t=Arsenal")
        if arsenal_search.status_code == 200:
            arsenal_data = arsenal_search.json()
            if arsenal_data.get('teams'):
                arsenal_id = arsenal_data['teams'][0]['idTeam']
                print(f"   Arsenal ID: {arsenal_id}")
                
                # Get Arsenal players
                players_url = f"https://www.thesportsdb.com/api/v1/json/3/lookup_all_players.php?id={arsenal_id}"
                players_response = requests.get(players_url)
                
                if players_response.status_code == 200:
                    players_data = players_response.json()
                    players = players_data.get('player', [])
                    
                    print(f"   ✅ Found {len(players)} Arsenal players:")
                    for player in players[:5]:
                        name = player.get('strPlayer', '?')
                        position = player.get('strPosition', '?')
                        nationality = player.get('strNationality', '?')
                        print(f"      ⚽ {name} ({position}, {nationality})")
    
    except Exception as e:
        print(f"❌ Arsenal test failed: {e}")

if __name__ == "__main__":
    test_real_teams()

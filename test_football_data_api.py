#!/usr/bin/env python3
"""
⚽ Test Football-Data.org API
Check what data is available from their free tier
"""
import requests
import json
from datetime import datetime, timedelta

def test_football_data_api():
    """Test Football-Data.org API without API key (free tier)."""
    print("⚽ TESTING FOOTBALL-DATA.ORG API")
    print("=" * 50)
    
    base_url = "https://api.football-data.org/v4"
    
    # Test endpoints that might work without API key
    test_endpoints = [
        ("competitions", f"{base_url}/competitions"),
        ("premier_league_matches", f"{base_url}/competitions/PL/matches"),
        ("premier_league_teams", f"{base_url}/competitions/PL/teams"),
        ("premier_league_standings", f"{base_url}/competitions/PL/standings")
    ]
    
    for name, url in test_endpoints:
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success! Keys: {list(data.keys())}")
                
                if name == "premier_league_matches" and 'matches' in data:
                    matches = data['matches'][:3]  # First 3 matches
                    print(f"   📊 Found {len(data['matches'])} total matches")
                    for match in matches:
                        home = match['homeTeam']['name']
                        away = match['awayTeam']['name']
                        date = match['utcDate']
                        status = match['status']
                        print(f"      🏟️ {home} vs {away} ({status}) - {date}")
                
                elif name == "premier_league_teams" and 'teams' in data:
                    teams = data['teams'][:5]  # First 5 teams
                    print(f"   📊 Found {len(data['teams'])} total teams")
                    for team in teams:
                        print(f"      🏆 {team['name']} (ID: {team['id']})")
                        
            elif response.status_code == 403:
                print(f"   ❌ Forbidden - Requires API key")
            elif response.status_code == 429:
                print(f"   ⚠️ Rate limited")
            else:
                print(f"   ❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print(f"\n💡 CONCLUSION:")
    print(f"   If any endpoints worked, Football-Data.org could be a good alternative")
    print(f"   If all require API key, we might need to register for free tier")

def test_alternative_apis():
    """Test other free football APIs."""
    print(f"\n🔍 TESTING ALTERNATIVE FREE APIs")
    print("=" * 50)
    
    # Test some other free APIs
    alternatives = [
        ("OpenLigaDB", "https://api.openligadb.de/getmatchdata/bl1/2024"),
        ("TheSportsDB", "https://www.thesportsdb.com/api/v1/json/3/eventsnext.php?id=133602"),
    ]
    
    for name, url in alternatives:
        print(f"\n🔍 Testing {name}...")
        try:
            response = requests.get(url, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success! Data type: {type(data)}")
                if isinstance(data, list) and len(data) > 0:
                    print(f"   📊 Found {len(data)} items")
                elif isinstance(data, dict):
                    print(f"   📊 Keys: {list(data.keys())}")
            else:
                print(f"   ❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    test_football_data_api()
    test_alternative_apis()

#!/usr/bin/env python3
"""
🔍 Test SportMonks API - Verify Access and Data
"""
import requests
import json

print("🔍 TESTING SPORTMONKS API")
print("=" * 30)

api_token = 'Ap7Wk5PSM63kXStqalLrvaZIQD11LIWWDJkBQmKPBHfkJ9s9ko8g8HFhvPvZ'
headers = {'Authorization': f'Bearer {api_token}'}

# Test 1: Get available leagues (try different auth methods)
print("📋 Testing leagues endpoint...")

# Method 1: Query parameter
url = 'https://api.sportmonks.com/v3/football/leagues'
params = {'api_token': api_token}
response = requests.get(url, params=params)
print(f"Method 1 (query param): {response.status_code}")

if response.status_code != 200:
    # Method 2: Header auth
    response = requests.get(url, headers=headers)
    print(f"Method 2 (header): {response.status_code}")

if response.status_code != 200:
    # Method 3: Different endpoint structure
    url = 'https://api.sportmonks.com/v3/core/leagues'
    response = requests.get(url, params=params)
    print(f"Method 3 (core endpoint): {response.status_code}")

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    leagues = data.get('data', [])
    print(f"✅ Found {len(leagues)} leagues")
    
    # Look for major leagues
    major_leagues = ['Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1']
    found_leagues = []
    
    for league in leagues[:10]:  # Check first 10
        name = league.get('name', '')
        league_id = league.get('id')
        if any(major in name for major in major_leagues):
            found_leagues.append(f"{name} (ID: {league_id})")
    
    if found_leagues:
        print("🎯 Major leagues found:")
        for league in found_leagues:
            print(f"   - {league}")
    else:
        print("📋 Sample leagues:")
        for league in leagues[:5]:
            name = league.get('name', 'Unknown')
            league_id = league.get('id')
            print(f"   - {name} (ID: {league_id})")
    
    # Test 2: Check if we can get fixtures
    print(f"\n⚽ Testing fixtures endpoint...")
    if leagues:
        test_league_id = leagues[0].get('id')
        fixtures_url = f'https://api.sportmonks.com/v3/football/fixtures'
        params = {'include': 'odds', 'filters': f'leagueIds:{test_league_id}'}
        
        fixtures_response = requests.get(fixtures_url, headers=headers, params=params)
        print(f"Fixtures status: {fixtures_response.status_code}")
        
        if fixtures_response.status_code == 200:
            fixtures_data = fixtures_response.json()
            fixtures = fixtures_data.get('data', [])
            print(f"✅ Found {len(fixtures)} fixtures")
            
            # Check for odds data
            has_odds = any('odds' in fixture for fixture in fixtures[:3])
            print(f"📊 Odds available: {has_odds}")
        else:
            print("❌ Fixtures failed")
    
else:
    print(f"❌ API Error: {response.status_code}")
    print(f"Response: {response.text[:200]}")

print("\n" + "=" * 30)
print("SportMonks API Test Complete!")

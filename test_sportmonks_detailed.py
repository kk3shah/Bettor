#!/usr/bin/env python3
"""
🔍 Test SportMonks API - Check Available Data for Betting
"""
import requests
import json

print("🔍 SPORTMONKS API - DETAILED ANALYSIS")
print("=" * 40)

api_token = 'Ap7Wk5PSM63kXStqalLrvaZIQD11LIWWDJkBQmKPBHfkJ9s9ko8g8HFhvPvZ'
base_url = 'https://api.sportmonks.com/v3'

def test_endpoint(endpoint, params=None):
    """Test an API endpoint and return response"""
    full_params = {'api_token': api_token}
    if params:
        full_params.update(params)
    
    response = requests.get(f"{base_url}{endpoint}", params=full_params)
    return response

# Test 1: Check what leagues are available
print("📋 TESTING AVAILABLE LEAGUES...")
response = test_endpoint('/football/leagues')

if response.status_code == 200:
    data = response.json()
    leagues = data.get('data', [])
    print(f"✅ Total leagues: {len(leagues)}")
    
    # Show all available leagues
    print("\n📋 ALL AVAILABLE LEAGUES:")
    for league in leagues:
        name = league.get('name', 'Unknown')
        league_id = league.get('id')
        country = league.get('country', {}).get('name', 'Unknown')
        print(f"   - {name} (ID: {league_id}) - {country}")
    
    # Test 2: Try to get recent fixtures for first league
    if leagues:
        test_league_id = leagues[0].get('id')
        print(f"\n⚽ TESTING FIXTURES FOR LEAGUE {test_league_id}...")
        
        fixtures_response = test_endpoint('/football/fixtures', {
            'filters': f'leagueIds:{test_league_id}'
        })
        
        print(f"Fixtures status: {fixtures_response.status_code}")
        if fixtures_response.status_code == 200:
            fixtures_data = fixtures_response.json()
            fixtures = fixtures_data.get('data', [])
            print(f"✅ Found {len(fixtures)} fixtures")
            
            # Check fixture structure
            if fixtures:
                sample_fixture = fixtures[0]
                print(f"\n📊 Sample fixture structure:")
                print(f"   - Home: {sample_fixture.get('participants', [{}])[0].get('name', 'Unknown')}")
                print(f"   - Away: {sample_fixture.get('participants', [{}])[1].get('name', 'Unknown') if len(sample_fixture.get('participants', [])) > 1 else 'Unknown'}")
                print(f"   - Date: {sample_fixture.get('starting_at', 'Unknown')}")
                print(f"   - Has odds: {'odds' in sample_fixture}")
        else:
            print(f"❌ Fixtures failed: {fixtures_response.text[:200]}")

# Test 3: Check what endpoints are available
print(f"\n🔍 TESTING OTHER ENDPOINTS...")

endpoints_to_test = [
    '/football/bookmakers',
    '/football/markets', 
    '/football/odds',
    '/core/countries',
]

for endpoint in endpoints_to_test:
    response = test_endpoint(endpoint)
    status = "✅" if response.status_code == 200 else "❌"
    print(f"   {status} {endpoint}: {response.status_code}")

print("\n" + "=" * 40)
print("Analysis complete - checking if Premier League data available...")

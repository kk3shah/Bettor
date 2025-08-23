#!/usr/bin/env python3
"""
Debug ESPN API data structure
"""
import requests
import json

url = 'https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/teams/384/roster'
response = requests.get(url)
data = response.json()

print("🔍 ESPN API DATA STRUCTURE DEBUG")
print("=" * 40)

athletes = data.get('athletes', [])
print(f"Athletes type: {type(athletes)}")
print(f"Athletes length: {len(athletes)}")

print("\n📊 First 3 athletes:")
for i, athlete in enumerate(athletes[:3]):
    print(f"\n{i+1}. Type: {type(athlete)}")
    if hasattr(athlete, 'keys'):
        print(f"   Keys: {list(athlete.keys())[:10]}")
        print(f"   displayName: {athlete.get('displayName', 'N/A')}")
        print(f"   jersey: {athlete.get('jersey', 'N/A')}")
        print(f"   position: {athlete.get('position', 'N/A')}")
    else:
        print(f"   Value: {str(athlete)[:100]}")

print("\n🔍 SUMMARY:")
print(f"✅ Total athletes found: {len(athletes)}")
if athletes and hasattr(athletes[0], 'keys'):
    print(f"✅ Structure: Direct list of athlete dictionaries")
else:
    print(f"❌ Structure: Unexpected format")

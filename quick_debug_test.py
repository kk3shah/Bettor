#!/usr/bin/env python3
"""
🚨 Quick Debug - Test ESPN API Connectivity
"""
import requests
import json
from datetime import datetime, timezone, timedelta

print("🧪 QUICK ESPN API TEST")
print("=" * 30)

try:
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    # Test basic ESPN API
    print("📡 Testing basic ESPN API...")
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"
    
    print(f"📡 GET {url}")
    response = session.get(url, timeout=10)
    print(f"📡 Response: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        events = data.get('events', [])
        print(f"✅ Success! Found {len(events)} Premier League matches")
        
        if events:
            match = events[0]
            competitors = match.get('competitions', [{}])[0].get('competitors', [])
            if len(competitors) >= 2:
                home_team = competitors[0]['team']['displayName']
                away_team = competitors[1]['team']['displayName']
                print(f"🎯 Sample match: {home_team} vs {away_team}")
            
    else:
        print(f"❌ API failed with status {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
except requests.exceptions.Timeout:
    print("⏰ Request timed out - ESPN API might be slow")
except requests.exceptions.ConnectionError:
    print("🌐 Connection error - Check internet connection")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 30)
print("If this works, the full scraper should work too!")

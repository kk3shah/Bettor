#!/usr/bin/env python3
"""
🔍 Verify ESPN Stats - Check if we're getting REAL stats from ESPN API
"""
import requests
import json

print("🔍 VERIFYING ESPN STATS ACCURACY")
print("=" * 40)

# Get Crystal Palace roster with stats
url = 'https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/teams/384/roster'
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    athletes = data.get('athletes', [])
    
    print(f"✅ Found {len(athletes)} Crystal Palace players")
    
    # Check first few players for real statistics
    print("\n📊 CHECKING FOR REAL STATISTICS:")
    
    for i, athlete in enumerate(athletes[:5]):
        name = athlete.get('displayName', 'Unknown')
        jersey = athlete.get('jersey', 'N/A')
        position = athlete.get('position', {}).get('abbreviation', 'N/A')
        stats = athlete.get('statistics', [])
        
        print(f"\n👤 {name} (#{jersey}) - {position}")
        print(f"   Raw statistics field: {stats}")
        
        if stats:
            print("   📈 HAS STATISTICS!")
            for stat_group in stats:
                print(f"      Group: {stat_group}")
        else:
            print("   📭 NO STATISTICS - Will use fallback")
    
    print("\n" + "=" * 40)
    print("🎯 CONCLUSION:")
    
    # Check if ANY player has real stats
    players_with_stats = 0
    for athlete in athletes[:10]:  # Check first 10
        if athlete.get('statistics'):
            players_with_stats += 1
    
    if players_with_stats > 0:
        print(f"✅ {players_with_stats}/10 players have REAL ESPN statistics")
    else:
        print("❌ NO players have real statistics - all using fallback")
        print("💡 ESPN roster API may not include detailed statistics")
        print("💡 Need to find ESPN stats API endpoint or use fallback")

else:
    print(f"❌ Failed to get ESPN data: {response.status_code}")

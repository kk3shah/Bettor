#!/usr/bin/env python3
"""Quick test - single match analysis"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.data.adapters.live_scraper import LiveDataScraper
from app.services.multi_market import analyze_comprehensive_markets

print("🧪 QUICK TEST: Brentford vs Aston Villa")
print("Testing shirt number matching...")

scraper = LiveDataScraper()
live_data = scraper.get_live_match_data("Brentford", "Aston Villa")

print(f"\n📊 Data Generated:")
print(f"Lineups: {len(live_data['lineups'])}")
print(f"Stats: {len(live_data['player_stats'])}")  
print(f"Odds: {len(live_data['odds'])}")

# Check first few players
print(f"\n🔍 First 3 players:")
for i, player in enumerate(live_data['lineups'][:3]):
    shirt = player.get('shirt_number', 'NO_NUMBER')
    print(f"  {i+1}. {player['player_name']} #{shirt} ({player['team']})")

# Try analysis
config = {'bankroll': 1000, 'max_stake_pct': 0.05, 'kelly_fraction': 0.25, 
          'league_avg_shots': 10.5, 'home_mult': 1.05, 'away_mult': 0.95}

signals = analyze_comprehensive_markets(live_data, config)
print(f"\n🎯 Analysis Result: {len(signals)} betting opportunities")

if signals:
    print("✅ SUCCESS! System working for non-Arsenal/Leeds teams")
    for i, s in enumerate(signals[:2]):
        print(f"  {i+1}. {s['player']} - {s['market']}")
else:
    print("❌ FAILED - No signals generated")

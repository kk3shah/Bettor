#!/usr/bin/env python3
"""
🧪 Test Script - Verify Shirt Number Matching System
Tests the new shirt number-based matching before deployment
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.data.adapters.live_scraper import LiveDataScraper
from app.services.multi_market import analyze_comprehensive_markets
from app.services.earnings import calculate_expected_earnings
import json

def test_shirt_number_matching():
    """Test that shirt number matching works for any team."""
    
    print("🧪 TESTING SHIRT NUMBER MATCHING SYSTEM")
    print("=" * 50)
    
    # Test teams
    test_cases = [
        ("Arsenal", "Leeds"),
        ("Brentford", "Aston Villa"), 
        ("Real Madrid", "Barcelona"),
        ("Manchester United", "Liverpool")
    ]
    
    scraper = LiveDataScraper()
    config = {
        'bankroll': 1000,
        'max_stake_pct': 0.05,
        'kelly_fraction': 0.25,
        'league_avg_shots': 10.5,
        'league_avg_corners': 5.5,
        'home_mult': 1.05,
        'away_mult': 0.95
    }
    
    for i, (home_team, away_team) in enumerate(test_cases, 1):
        print(f"\n🔍 [{i}/{len(test_cases)}] Testing: {home_team} vs {away_team}")
        print("-" * 40)
        
        try:
            # Get live data 
            live_data = scraper.get_live_match_data(home_team, away_team)
            
            # Debug: Check data structure
            print(f"📊 Data Summary:")
            print(f"  Lineups: {len(live_data['lineups'])} players")
            print(f"  Player Stats: {len(live_data['player_stats'])} players") 
            print(f"  Odds: {len(live_data['odds'])} markets")
            
            # Check shirt number presence
            lineups_with_numbers = [p for p in live_data['lineups'] if p.get('shirt_number')]
            stats_with_numbers = [p for p in live_data['player_stats'] if p.get('shirt_number')]
            odds_with_numbers = [o for o in live_data['odds'] if o.get('shirt_number')]
            
            print(f"🔢 Shirt Number Coverage:")
            print(f"  Lineups with numbers: {len(lineups_with_numbers)}/{len(live_data['lineups'])}")
            print(f"  Stats with numbers: {len(stats_with_numbers)}/{len(live_data['player_stats'])}")
            print(f"  Odds with numbers: {len(odds_with_numbers)}/{len(live_data['odds'])}")
            
            # Show sample shirt numbers
            if lineups_with_numbers:
                sample_nums = [p['shirt_number'] for p in lineups_with_numbers[:5]]
                print(f"  Sample numbers: {sample_nums}")
            
            # Run analysis
            signals = analyze_comprehensive_markets(live_data, config)
            
            if signals:
                print(f"✅ ANALYSIS SUCCESS: {len(signals)} betting opportunities found!")
                
                # Show top 3 bets
                print("🎯 Top 3 Opportunities:")
                for j, signal in enumerate(signals[:3], 1):
                    print(f"  {j}. {signal['player']} - {signal['market']} ≥{signal['threshold']} ({signal['odds']})")
                
                # Calculate earnings
                earnings = calculate_expected_earnings(signals, config['bankroll'])
                print(f"💰 Expected ROI: {earnings['expected_roi']:.1f}%")
                
            else:
                print("❌ ANALYSIS FAILED: No betting signals generated")
                
                # Debug matching issues
                print("\n🔍 DEBUGGING:")
                
                # Check for matching issues
                lineup_keys = set()
                for lineup in live_data['lineups']:
                    if lineup.get('shirt_number') and lineup.get('team'):
                        lineup_keys.add((lineup['shirt_number'], lineup['team']))
                
                stats_keys = set()
                for player in live_data['player_stats']:
                    if player.get('shirt_number') and player.get('team'):
                        stats_keys.add((player['shirt_number'], player['team']))
                
                odds_keys = set()
                for odds in live_data['odds']:
                    if odds.get('shirt_number') and odds.get('team'):
                        odds_keys.add((odds['shirt_number'], odds['team']))
                
                print(f"  Unique lineup keys: {len(lineup_keys)}")
                print(f"  Unique stats keys: {len(stats_keys)}")
                print(f"  Unique odds keys: {len(odds_keys)}")
                
                common_keys = lineup_keys & stats_keys & odds_keys
                print(f"  Keys present in ALL datasets: {len(common_keys)}")
                if common_keys:
                    print(f"  Sample matching keys: {list(common_keys)[:3]}")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🧪 SHIRT NUMBER MATCHING TEST COMPLETE")

if __name__ == "__main__":
    test_shirt_number_matching()

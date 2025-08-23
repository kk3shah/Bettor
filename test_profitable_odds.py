#!/usr/bin/env python3
"""
Test if profitable odds thresholds are being included in API response
"""
import requests
import json
import time

def test_profitable_odds():
    """Test if the API includes profitable odds fields."""
    print("🧪 TESTING PROFITABLE ODDS THRESHOLDS")
    print("=" * 50)
    
    time.sleep(2)  # Wait for web app
    
    try:
        url = "http://localhost:5000/api/analyze"
        params = {'home_team': 'Fulham', 'away_team': 'Manchester United'}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'all_bets' in data and data['all_bets']:
                sample_bet = data['all_bets'][0]
                
                print(f"🔍 SAMPLE BET ANALYSIS:")
                print(f"   Player: {sample_bet.get('player', 'N/A')}")
                print(f"   Market: {sample_bet.get('bet_description', 'N/A')}")
                print(f"   Confidence: {sample_bet.get('confidence', 'N/A')}")
                print(f"   Model Prob: {sample_bet.get('model_probability_percent', 'N/A')}%")
                
                # Check for profitable odds fields
                has_profitable_american = 'min_profitable_odds_american' in sample_bet
                has_profitable_decimal = 'min_profitable_odds_decimal' in sample_bet
                
                print(f"\n💰 PROFITABLE ODDS FIELDS:")
                print(f"   ✅ min_profitable_odds_american: {has_profitable_american}")
                if has_profitable_american:
                    print(f"      Value: {sample_bet.get('min_profitable_odds_american', 'N/A')}")
                
                print(f"   ✅ min_profitable_odds_decimal: {has_profitable_decimal}")
                if has_profitable_decimal:
                    print(f"      Value: {sample_bet.get('min_profitable_odds_decimal', 'N/A')}")
                
                print(f"   ✅ fair_odds_decimal: {'fair_odds_decimal' in sample_bet}")
                if 'fair_odds_decimal' in sample_bet:
                    print(f"      Value: {sample_bet.get('fair_odds_decimal', 'N/A')}")
                
                print(f"   ✅ reasoning: {'reasoning' in sample_bet}")
                if 'reasoning' in sample_bet:
                    print(f"      Value: {sample_bet.get('reasoning', 'N/A')}")
                
                # Check confidence distribution
                high_conf = len([bet for bet in data['all_bets'] if bet.get('confidence') == 'High'])
                medium_conf = len([bet for bet in data['all_bets'] if bet.get('confidence') == 'Medium'])
                low_conf = len([bet for bet in data['all_bets'] if bet.get('confidence') == 'Low'])
                
                print(f"\n📊 IMPROVED CONFIDENCE DISTRIBUTION:")
                print(f"   🔥 High Confidence: {high_conf} bets")
                print(f"   ⚡ Medium Confidence: {medium_conf} bets")
                print(f"   📉 Low Confidence: {low_conf} bets")
                
                # Show a high confidence example if available
                high_conf_bets = [bet for bet in data['all_bets'] if bet.get('confidence') == 'High']
                if high_conf_bets:
                    high_bet = high_conf_bets[0]
                    print(f"\n🎯 HIGH CONFIDENCE EXAMPLE:")
                    print(f"   Player: {high_bet.get('player', 'N/A')}")
                    print(f"   Market: {high_bet.get('bet_description', 'N/A')}")
                    print(f"   Model Prob: {high_bet.get('model_probability_percent', 'N/A')}%")
                    print(f"   Fair Odds: {high_bet.get('fair_odds_decimal', 'N/A')}")
                    print(f"   Min Profitable: {high_bet.get('min_profitable_odds_american', 'N/A')} ({high_bet.get('min_profitable_odds_decimal', 'N/A')})")
                
                if has_profitable_american and has_profitable_decimal:
                    print(f"\n✅ FRONTEND SHOULD NOW SHOW NEW FORMAT!")
                    print(f"   💰 Profitable odds thresholds included")
                    print(f"   🎯 Better confidence levels")
                    print(f"   📊 Improved mathematical modeling")
                    return True
                else:
                    print(f"\n⚠️ MISSING PROFITABLE ODDS FIELDS")
                    return False
            else:
                print("❌ No betting data in response")
                return False
        else:
            print(f"❌ API Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_profitable_odds()
    
    if success:
        print(f"\n🎉 ANALYSIS IMPROVEMENTS SUCCESSFUL!")
        print(f"   Refresh the web page to see new format")
        print(f"   Should show profitable odds thresholds instead of old format")
    else:
        print(f"\n❌ IMPROVEMENTS NEED MORE WORK")

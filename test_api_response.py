#!/usr/bin/env python3
"""
Test the API response format to ensure it matches frontend expectations
"""
import requests
import json
import time

def test_api_response():
    """Test the /api/analyze endpoint."""
    print("🧪 TESTING API RESPONSE FORMAT")
    print("=" * 50)
    
    # Wait a moment for web app to start
    print("⏳ Waiting for web app to start...")
    time.sleep(3)
    
    try:
        # Test the API endpoint
        url = "http://localhost:5000/api/analyze"
        params = {
            'home_team': 'Fulham',
            'away_team': 'Manchester United'
        }
        
        print(f"🌐 Making request to: {url}")
        print(f"📋 Parameters: {params}")
        
        response = requests.get(url, params=params, timeout=10)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ SUCCESS - API Response received")
            print(f"📈 Response structure:")
            
            # Check key fields
            if 'match_info' in data:
                print(f"   ✅ match_info: {data['match_info']['home_team']} vs {data['match_info']['away_team']}")
            
            if 'summary' in data:
                summary = data['summary']
                print(f"   ✅ summary:")
                print(f"      - total_opportunities: {summary.get('total_opportunities', 0)}")
                print(f"      - high_confidence_bets: {summary.get('high_confidence_bets', 0)}")
                print(f"      - medium_confidence_bets: {summary.get('medium_confidence_bets', 0)}")
            
            if 'top_bets' in data:
                print(f"   ✅ top_bets: {len(data['top_bets'])} items")
                if data['top_bets']:
                    sample_bet = data['top_bets'][0]
                    print(f"      Sample bet: {sample_bet.get('player', 'N/A')} - {sample_bet.get('bet_description', 'N/A')}")
                    print(f"      Confidence: {sample_bet.get('confidence', 'N/A')}")
                    print(f"      Model Prob: {sample_bet.get('model_probability_percent', 'N/A')}%")
            
            if 'all_bets' in data:
                print(f"   ✅ all_bets: {len(data['all_bets'])} items")
            
            # Show confidence distribution
            if 'all_bets' in data:
                high_conf = len([bet for bet in data['all_bets'] if bet.get('confidence') == 'High'])
                medium_conf = len([bet for bet in data['all_bets'] if bet.get('confidence') == 'Medium'])
                low_conf = len([bet for bet in data['all_bets'] if bet.get('confidence') == 'Low'])
                
                print(f"\n📊 CONFIDENCE DISTRIBUTION:")
                print(f"   🔥 High: {high_conf} bets")
                print(f"   ⚡ Medium: {medium_conf} bets")
                print(f"   📉 Low: {low_conf} bets")
            
            print(f"\n🎯 FRONTEND COMPATIBILITY CHECK:")
            required_fields = ['match_info', 'summary', 'top_bets', 'all_bets']
            for field in required_fields:
                status = "✅" if field in data else "❌"
                print(f"   {status} {field}")
            
            if data.get('top_bets'):
                bet_fields = ['player', 'bet_description', 'confidence', 'model_probability_percent']
                sample_bet = data['top_bets'][0]
                print(f"\n🎯 BET OBJECT COMPATIBILITY:")
                for field in bet_fields:
                    status = "✅" if field in sample_bet else "❌"
                    print(f"   {status} {field}")
            
            return True
            
        else:
            print(f"❌ ERROR - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR - Could not connect to web app")
        print("   Make sure web app is running on localhost:5000")
        return False
    except Exception as e:
        print(f"❌ ERROR - {e}")
        return False

if __name__ == "__main__":
    success = test_api_response()
    
    if success:
        print(f"\n🎉 API RESPONSE FORMAT IS CORRECT!")
        print(f"   Frontend should now display betting opportunities")
        print(f"   Visit http://localhost:5000 and select Fulham vs Manchester United")
    else:
        print(f"\n❌ API RESPONSE ISSUES FOUND")
        print(f"   Check web app logs for errors")

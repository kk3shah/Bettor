#!/usr/bin/env python3
"""
🧪 Test Single Match - Verify Real Data Scraping Works
Tests the real data scraper for just one match
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from real_data_scraper import RealDataScraper
import json

def test_single_match():
    """Test real data scraping for a single match."""
    print("🧪 TESTING SINGLE MATCH REAL DATA SCRAPING")
    print("=" * 50)
    
    scraper = RealDataScraper()
    
    try:
        # Get premium matches
        print("🔍 Getting premium matches...")
        print("   📡 Calling ESPN API for each league...")
        matches = scraper.get_premium_matches()
        print(f"   ⏰ API calls completed")
        
        if not matches:
            print("❌ No premium matches found")
            return
        
        # Take first match for testing
        test_match = matches[0]
        print(f"\n🎯 Testing match: {test_match['home_team']} vs {test_match['away_team']} ({test_match['league']})")
        
        # Test ESPN player stats
        print(f"\n📊 Testing ESPN player stats...")
        player_stats = scraper.scrape_whoscored_player_stats(test_match)
        
        if player_stats:
            print(f"✅ Got {len(player_stats)} players from ESPN")
            print("📋 Sample players:")
            for i, player in enumerate(player_stats[:3]):
                print(f"  {i+1}. {player['player_name']} (#{player['shirt_number']}) - {player['position']} - {player['team']}")
                print(f"     Stats: {player['shots_pg']} shots/game, {player['fouls_pg']} fouls/game")
        else:
            print("❌ Failed to get ESPN player stats")
            return
        
        # Test betting odds
        print(f"\n💰 Testing betting odds...")
        betting_odds = scraper.scrape_betting_odds(test_match, player_stats)
        
        if betting_odds:
            print(f"✅ Got {len(betting_odds)} betting markets")
            print("💰 Sample markets:")
            for i, odds in enumerate(betting_odds[:3]):
                print(f"  {i+1}. {odds['player_name']} - {odds['market']} ≥{odds['threshold']} ({odds['odds_american']})")
        else:
            print("❌ Failed to get betting odds")
            return
        
        # Test database storage
        print(f"\n💾 Testing database storage...")
        scraper.store_real_data(test_match, player_stats, betting_odds)
        print("✅ Data stored in database")
        
        # Verify database
        print(f"\n🔍 Verifying database...")
        from database import BettorDatabase
        import sqlite3
        
        db = BettorDatabase()
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM real_match_data")
            count = cursor.fetchone()[0]
            print(f"✅ Database contains {count} matches with real data")
        
        print(f"\n🎉 SINGLE MATCH TEST COMPLETED SUCCESSFULLY!")
        print(f"📊 Players: {len(player_stats)}")
        print(f"💰 Markets: {len(betting_odds)}")
        print(f"💾 Stored: ✅")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_single_match()
    if success:
        print("\n✅ Ready to run full scraper!")
    else:
        print("\n❌ Fix issues before running full scraper")

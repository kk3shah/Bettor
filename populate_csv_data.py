#!/usr/bin/env python3
"""
📊 CSV Data Populator - Simple script to populate CSV files with match data
No complex database setup - just fill CSV files for instant web app loading
"""
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_manager import CSVDataManager
from web_app import BettorWebService
from app.data.adapters.live_scraper import LiveDataScraper
from app.services.espn_analysis import analyze_espn_based_markets

def populate_csv_data():
    """Populate CSV files with matches and their analysis."""
    print("🤖 CSV DATA POPULATOR STARTING...")
    print("=" * 50)
    
    csv_manager = CSVDataManager()
    web_service = BettorWebService()
    scraper = LiveDataScraper()
    
    try:
        # Step 1: Get and cache matches
        print("📅 Getting upcoming matches...")
        matches = web_service.get_simulation_matches(hours_ahead=24)
        
        if not matches:
            print("❌ No matches found!")
            return
        
        print(f"✅ Found {len(matches)} matches")
        csv_manager.store_matches(matches)
        
        # Step 2: Generate analysis for a few key matches (not all to save time)
        priority_matches = matches[:3]  # Just top 3 for testing
        
        print(f"\n📊 Generating analysis for {len(priority_matches)} priority matches...")
        
        for i, match in enumerate(priority_matches, 1):
            home_team = match['home_team']
            away_team = match['away_team']
            
            print(f"\n[{i}/{len(priority_matches)}] Analyzing {home_team} vs {away_team}")
            print("-" * 40)
            
            try:
                # Check if analysis already exists
                existing = csv_manager.get_analysis(home_team, away_team)
                if existing and csv_manager.is_analysis_fresh(existing):
                    print("✅ Fresh analysis already exists, skipping...")
                    continue
                
                # Generate live data
                print("🔍 Getting live match data...")
                live_data = scraper.get_live_match_data(home_team, away_team)
                
                # Run analysis
                print("🧠 Running analysis...")
                config = {
                    'league_avg_shots': 12.5,
                    'home_mult': 1.1,
                    'away_mult': 0.95,
                    'min_edge_for_profit': 0.05
                }
                
                signals = analyze_espn_based_markets(live_data, config)
                
                # Format analysis results
                analysis_results = {
                    "match_info": {
                        "home_team": home_team,
                        "away_team": away_team,
                        "kickoff_time": match.get('kickoff_full', 'TBD'),
                        "analysis_time": "2025-08-23T12:00:00",
                        "lineup_source": "Squad-based analysis"
                    },
                    "summary": {
                        "total_opportunities": len(signals),
                        "high_confidence_bets": len([s for s in signals if s.get('confidence') == 'High']),
                        "medium_confidence_bets": len([s for s in signals if s.get('confidence') == 'Medium']),
                        "note": "Bet only if your bookmaker offers better odds than shown"
                    },
                    "betting_opportunities": signals
                }
                
                # Store analysis
                csv_manager.store_analysis(home_team, away_team, analysis_results)
                
                print(f"✅ Analysis complete - {len(signals)} opportunities found")
                
            except Exception as e:
                print(f"❌ Failed to analyze {home_team} vs {away_team}: {e}")
                continue
        
        print("\n" + "=" * 50)
        print("🎉 CSV DATA POPULATION COMPLETE!")
        print("✅ Matches cached to CSV")
        print("✅ Analysis cached to CSV") 
        print("⚡ Website will now be INSTANT (no API calls)")
        print("\n🌐 Start the web app: python web_app.py")
        
    except Exception as e:
        print(f"❌ Fatal error during CSV population: {e}")
        raise

if __name__ == "__main__":
    populate_csv_data()

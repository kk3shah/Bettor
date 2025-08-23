#!/usr/bin/env python3
"""
🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League Only Data Populator
Populate CSV with ONLY Premier League matches using real ESPN data
NO FAKE DATA - Only matches where we have confirmed real player data
"""
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_manager import CSVDataManager
from app.data.adapters.live_scraper import LiveDataScraper
from app.services.espn_analysis import analyze_espn_based_markets
from datetime import datetime, timedelta

def get_premier_league_matches():
    """Get upcoming Premier League matches only."""
    # Real Premier League matches for the next 24 hours
    premier_league_matches = [
        {
            'home_team': 'Arsenal',
            'away_team': 'Leeds United',
            'league': 'Premier League',
            'kickoff_time': '2025-08-23T16:30:00+00:00'
        },
        {
            'home_team': 'Crystal Palace', 
            'away_team': 'Nottingham Forest',
            'league': 'Premier League',
            'kickoff_time': '2025-08-24T13:00:00+00:00'
        },
        {
            'home_team': 'Everton',
            'away_team': 'Brighton & Hove Albion', 
            'league': 'Premier League',
            'kickoff_time': '2025-08-24T13:00:00+00:00'
        },
        {
            'home_team': 'Fulham',
            'away_team': 'Manchester United',
            'league': 'Premier League', 
            'kickoff_time': '2025-08-24T15:30:00+00:00'
        },
        {
            'home_team': 'Liverpool',
            'away_team': 'Chelsea',
            'league': 'Premier League',
            'kickoff_time': '2025-08-24T16:30:00+00:00'
        },
        {
            'home_team': 'Manchester City',
            'away_team': 'Tottenham',
            'league': 'Premier League',
            'kickoff_time': '2025-08-24T17:30:00+00:00'
        }
    ]
    
    return premier_league_matches

def populate_premier_league_data():
    """Populate CSV with Premier League matches and real analysis."""
    print("🏴󠁧󠁢󠁥󠁮󠁧󠁿 PREMIER LEAGUE ONLY DATA POPULATOR")
    print("=" * 50)
    print("✅ NO FAKE DATA - Only real ESPN player data")
    print("🎯 Premier League matches only")
    print()
    
    csv_manager = CSVDataManager()
    scraper = LiveDataScraper()
    
    # Clear existing data
    print("🧹 Clearing existing CSV data...")
    csv_manager.clear_all_data()
    
    # Get Premier League matches
    matches = get_premier_league_matches()
    print(f"📋 Found {len(matches)} Premier League matches")
    
    successful_matches = 0
    skipped_matches = 0
    
    for i, match in enumerate(matches, 1):
        home_team = match['home_team']
        away_team = match['away_team']
        
        print(f"\n📊 Processing Match {i}/{len(matches)}: {home_team} vs {away_team}")
        print("-" * 50)
        
        try:
            # Test if ESPN has data for both teams
            print("🔍 Checking ESPN data availability...")
            home_roster = scraper._get_real_team_roster(home_team, is_home=True)
            away_roster = scraper._get_real_team_roster(away_team, is_home=False)
            
            if not home_roster or not away_roster:
                print(f"❌ Skipping {home_team} vs {away_team} - No real ESPN data")
                skipped_matches += 1
                continue
            
            print(f"✅ Real data confirmed for both teams")
            
            # Store match
            csv_manager.store_match(
                home_team=home_team,
                away_team=away_team, 
                league=match['league'],
                kickoff_time=match['kickoff_time']
            )
            
            # Generate analysis with real data
            print("🧠 Generating analysis with real ESPN data...")
            live_data = scraper.get_live_match_data(home_team, away_team)
            
            if not live_data or not live_data.get('lineups'):
                print(f"❌ No lineup data for {home_team} vs {away_team}")
                skipped_matches += 1
                continue
            
            config = {
                'league_avg_shots': 12.5,
                'home_mult': 1.1,
                'away_mult': 0.95,
                'min_edge_for_profit': 0.05
            }
            
            signals = analyze_espn_based_markets(live_data, config)
            
            if not signals:
                print(f"❌ No betting opportunities found for {home_team} vs {away_team}")
                skipped_matches += 1
                continue
            
            # Format and store analysis
            analysis_results = {
                "match_info": {
                    "home_team": home_team,
                    "away_team": away_team,
                    "kickoff_time": match['kickoff_time'],
                    "analysis_time": datetime.now().isoformat(),
                    "lineup_source": "Real ESPN data"
                },
                "summary": {
                    "total_opportunities": len(signals),
                    "high_confidence_bets": len([s for s in signals if s.get('confidence') == 'High']),
                    "medium_confidence_bets": len([s for s in signals if s.get('confidence') == 'Medium']),
                    "note": "All data from real ESPN player statistics"
                },
                "top_bets": signals[:10]  # Top 10 opportunities
            }
            
            csv_manager.store_analysis(home_team, away_team, analysis_results)
            successful_matches += 1
            
            print(f"✅ Successfully processed {home_team} vs {away_team}")
            print(f"   📈 {len(signals)} betting opportunities found")
            
        except Exception as e:
            print(f"❌ Error processing {home_team} vs {away_team}: {e}")
            skipped_matches += 1
            continue
    
    print("\n" + "=" * 50)
    print("🏁 PREMIER LEAGUE DATA POPULATION COMPLETE")
    print(f"✅ Successfully processed: {successful_matches} matches")
    print(f"❌ Skipped (no real data): {skipped_matches} matches")
    print(f"📊 Total real betting opportunities available")
    print("🎯 100% real ESPN player data - NO FAKE PLAYERS")
    print("=" * 50)

if __name__ == "__main__":
    populate_premier_league_data()

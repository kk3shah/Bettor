#!/usr/bin/env python3
"""
🤖 Daily Data Populator - Pre-populate DB with matches + analysis
Runs once daily to fetch all data, so website is instant for users
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from database import BettorDatabase
from app.data.adapters.live_scraper import LiveDataScraper
from app.services.espn_analysis import analyze_espn_based_markets
import json

class DailyPopulator:
    def __init__(self):
        self.db = BettorDatabase()
        self.scraper = LiveDataScraper()
        
    def populate_daily_matches(self):
        """Pre-populate database with matches and analysis for next 24 hours"""
        print("🤖 DAILY DATA POPULATOR STARTING...")
        print("=" * 50)
        
        try:
            # Get next 24 hours of matches
            print("📅 Getting matches for next 24 hours...")
            matches = self.get_upcoming_matches(hours=24)
            
            print(f"✅ Found {len(matches)} matches to analyze")
            
            successful_analyses = 0
            failed_analyses = 0
            
            for i, match in enumerate(matches, 1):
                home_team = match['home_team']
                away_team = match['away_team']
                
                print(f"\n📊 [{i}/{len(matches)}] Analyzing {home_team} vs {away_team}")
                print("-" * 40)
                
                try:
                    # Check if analysis already exists and is recent
                    existing = self.db.get_match_analysis(home_team, away_team)
                    if existing and self._is_analysis_fresh(existing):
                        print(f"✅ Fresh analysis exists, skipping...")
                        successful_analyses += 1
                        continue
                    
                    # Get live data for this match
                    print("🔍 Getting live match data...")
                    live_data = self.scraper.get_live_match_data(home_team, away_team)
                    
                    # Run analysis
                    print("🧠 Running ESPN-based analysis...")
                    config = {
                        'league_avg_shots': 12.5,
                        'home_mult': 1.1,
                        'away_mult': 0.95,
                        'min_edge_for_profit': 0.05  # 5% edge minimum
                    }
                    
                    betting_opportunities = analyze_espn_based_markets(live_data, config)
                    
                    # Prepare analysis for storage
                    analysis_data = {
                        'home_team': home_team,
                        'away_team': away_team,
                        'match_time': match.get('match_time', 'TBD'),
                        'league': match.get('league', 'Unknown'),
                        'analysis_type': 'squad_based',
                        'high_confidence_bets': len([b for b in betting_opportunities if b.get('confidence') == 'High']),
                        'medium_confidence_bets': len([b for b in betting_opportunities if b.get('confidence') == 'Medium']),
                        'total_opportunities': len(betting_opportunities),
                        'betting_opportunities': betting_opportunities,
                        'real_player_stats': True,
                        'generated_at': datetime.now().isoformat()
                    }
                    
                    # Store in database
                    print("💾 Storing analysis in database...")
                    self.db.store_match_analysis(analysis_data)
                    
                    print(f"✅ Successfully analyzed {home_team} vs {away_team}")
                    print(f"   📈 {len(betting_opportunities)} betting opportunities found")
                    successful_analyses += 1
                    
                except Exception as e:
                    print(f"❌ Failed to analyze {home_team} vs {away_team}: {e}")
                    failed_analyses += 1
                    continue
            
            print("\n" + "=" * 50)
            print("🎉 DAILY POPULATION COMPLETE!")
            print(f"✅ Successful: {successful_analyses}")
            print(f"❌ Failed: {failed_analyses}")
            print(f"📊 Total: {len(matches)} matches")
            print(f"⚡ Website will now be INSTANT for users!")
            
        except Exception as e:
            print(f"❌ Fatal error during daily population: {e}")
            raise
    
    def get_upcoming_matches(self, hours=24):
        """Get upcoming matches for the next X hours"""
        # Use existing logic from web_app but return structured data
        from web_app import BettorWebService
        web_app = BettorWebService()
        
        # Get simulation matches (which includes real teams)
        raw_matches = web_app.get_simulation_matches(hours_ahead=hours)
        
        # Convert to structured format
        matches = []
        for match in raw_matches:
            matches.append({
                'home_team': match['home_team'],
                'away_team': match['away_team'],
                'match_time': match.get('match_time', 'TBD'),
                'league': match.get('league', 'Unknown'),
                'competition': match.get('competition', 'Unknown')
            })
        
        return matches
    
    def _is_analysis_fresh(self, analysis):
        """Check if existing analysis is fresh (within last 6 hours)"""
        try:
            if 'generated_at' in analysis:
                generated_time = datetime.fromisoformat(analysis['generated_at'])
                age_hours = (datetime.now() - generated_time).total_seconds() / 3600
                return age_hours < 6  # Consider fresh if less than 6 hours old
        except:
            pass
        return False

def main():
    """Run daily population"""
    populator = DailyPopulator()
    populator.populate_daily_matches()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
🔄 Bettor Batch Processor - Daily analysis for all matches
"""
import sys
import os
from datetime import datetime, timezone, timedelta
import json
import time
import traceback

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import BettorDatabase
from web_app import BettorWebService
from app.services.multi_market import analyze_comprehensive_markets
from app.services.earnings import calculate_expected_earnings
from app.services.value import american_to_decimal

class BettorBatchProcessor:
    """Daily batch processor for analyzing all upcoming matches."""
    
    def __init__(self):
        self.db = BettorDatabase()
        self.web_service = BettorWebService()
        self.config = {
            'bankroll': 1000,
            'max_stake_pct': 0.05,
            'kelly_fraction': 0.25,
            'league_avg_shots': 10.5,
            'league_avg_corners': 5.5,
            'home_mult': 1.05,
            'away_mult': 0.95
        }
    
    def run_daily_batch(self, hours_ahead=24):
        """Run analysis for all matches in the next N hours."""
        start_time = datetime.now(timezone.utc)
        print(f"🚀 Starting daily batch processing at {start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"🔍 Looking for matches in next {hours_ahead} hours...")
        
        try:
            # Get all upcoming matches
            matches = self.web_service.get_upcoming_matches(hours_ahead)
            print(f"✅ Found {len(matches)} matches to analyze")
            
            if not matches:
                print("⚠️ No matches found for analysis")
                return
            
            # Process each match
            successful_analyses = 0
            failed_analyses = 0
            total_opportunities = 0
            
            for i, match in enumerate(matches, 1):
                try:
                    print(f"\n📊 [{i}/{len(matches)}] Analyzing: {match['home_team']} vs {match['away_team']} ({match['league']})")
                    
                    # Store match information
                    self.db.store_match(match)
                    
                    # Check if analysis already exists
                    existing_analysis = self.db.get_analysis_by_match(match['id'])
                    if existing_analysis:
                        print(f"✅ Analysis already exists, skipping...")
                        successful_analyses += 1
                        total_opportunities += existing_analysis['summary']['total_opportunities']
                        continue
                    
                    # Run analysis
                    analysis_result = self._analyze_match(match)
                    
                    if analysis_result and not analysis_result.get('error'):
                        # Store results
                        analysis_id = self.db.store_analysis(match['id'], analysis_result)
                        successful_analyses += 1
                        total_opportunities += analysis_result['summary']['total_opportunities']
                        
                        print(f"✅ Analysis complete - {analysis_result['summary']['total_opportunities']} opportunities found")
                        
                    else:
                        failed_analyses += 1
                        error_msg = analysis_result.get('error', 'Unknown error') if analysis_result else 'Analysis returned None'
                        print(f"❌ Analysis failed: {error_msg}")
                    
                    # Small delay to be respectful to APIs
                    time.sleep(1)
                    
                except Exception as e:
                    failed_analyses += 1
                    print(f"❌ Error analyzing {match['home_team']} vs {match['away_team']}: {e}")
                    traceback.print_exc()
                    continue
            
            # Create daily summary
            today = start_time.date().isoformat()
            summary = self.db.create_daily_summary(today)
            
            # Final report
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            print(f"\n🎯 BATCH PROCESSING COMPLETE")
            print(f"⏱️ Duration: {duration:.1f} seconds")
            print(f"✅ Successful analyses: {successful_analyses}")
            print(f"❌ Failed analyses: {failed_analyses}")
            print(f"🎲 Total opportunities found: {total_opportunities}")
            
            if summary:
                print(f"📊 Daily Summary:")
                print(f"  📅 Date: {summary['date']}")
                print(f"  ⚽ Matches: {summary['total_matches']}")
                print(f"  🎯 Opportunities: {summary['total_opportunities']}")
                print(f"  📈 Avg ROI: {summary['avg_expected_roi']:.1f}%")
                print(f"  💰 Total Profit Potential: ${summary['total_potential_profit']:.2f}")
            
        except Exception as e:
            print(f"❌ Batch processing failed: {e}")
            traceback.print_exc()
    
    def _analyze_match(self, match):
        """Analyze a single match."""
        try:
            # Run comprehensive analysis
            live_data = self.web_service.scraper.get_live_match_data(
                match['home_team'], 
                match['away_team']
            )
            
            signals = analyze_comprehensive_markets(live_data, self.config)
            
            if not signals:
                return {"error": "No betting signals generated"}
            
            # Calculate earnings
            earnings_analysis = calculate_expected_earnings(signals, self.config['bankroll'])
            
            # Format results
            analysis_results = {
                "match_info": {
                    "home_team": match['home_team'],
                    "away_team": match['away_team'],
                    "league": match['league'],
                    "kickoff_time": match['kickoff_full'],
                    "venue": match.get('venue', ''),
                    "analysis_time": datetime.now(timezone.utc).isoformat(),
                    "lineup_source": "Squad-based analysis"
                },
                "summary": {
                    "total_opportunities": len(signals),
                    "total_stake_recommended": earnings_analysis['total_stakes'],
                    "expected_profit": earnings_analysis['expected_profit'],
                    "expected_roi_percent": earnings_analysis['expected_roi'],
                    "bankroll_utilization_percent": earnings_analysis['bankroll_utilization']
                },
                "profit_scenarios": earnings_analysis['scenarios'],
                "top_bets": [],
                "all_bets": []
            }
            
            # Process betting signals
            for i, signal in enumerate(signals, 1):
                decimal_odds = american_to_decimal(signal['odds'])
                potential_profit = (decimal_odds - 1) * signal['suggested_stake']
                confidence = "HIGH" if signal['edge'] > 0.2 else "MEDIUM" if signal['edge'] > 0.1 else "LOW"
                
                bet_info = {
                    "priority": i,
                    "player": signal['player'],
                    "team": signal['team'],
                    "market": signal['market'],
                    "bet_description": f"{signal['market']} ≥ {signal['threshold']}",
                    "threshold": signal['threshold'],
                    "odds_american": signal['odds'],
                    "odds_decimal": round(decimal_odds, 2),
                    "model_probability_percent": round(signal['model_prob'] * 100, 1),
                    "bookmaker_implied_probability_percent": round(signal['implied_prob'] * 100, 1),
                    "edge_percent": round(signal['edge'] * 100, 1),
                    "kelly_percent": round(signal['kelly'] * 100, 1),
                    "recommended_stake_dollars": round(signal['suggested_stake'], 2),
                    "potential_profit_dollars": round(potential_profit, 2),
                    "potential_return_dollars": round(signal['suggested_stake'] + potential_profit, 2),
                    "confidence": confidence,
                    "expected_minutes": signal['expected_minutes'],
                    "home_away": "HOME" if signal['team'] == match['home_team'] else "AWAY"
                }
                
                analysis_results["all_bets"].append(bet_info)
                
                # Top 8 bets for quick view
                if i <= 8:
                    analysis_results["top_bets"].append(bet_info)
            
            return analysis_results
            
        except Exception as e:
            print(f"⚠️ Error in match analysis: {e}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    def cleanup_and_maintenance(self):
        """Perform database cleanup and maintenance."""
        print("🧹 Performing database maintenance...")
        
        try:
            # Cleanup old data
            self.db.cleanup_old_data(days_to_keep=7)
            
            # Get database stats
            stats = self.db.get_database_stats()
            print("📊 Database Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
                
        except Exception as e:
            print(f"❌ Maintenance failed: {e}")
    
    def run_quick_update(self, hours_ahead=8):
        """Quick update for imminent matches only."""
        print(f"⚡ Running quick update for matches in next {hours_ahead} hours...")
        self.run_daily_batch(hours_ahead)

def main():
    """Main entry point for batch processing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bettor Batch Processor')
    parser.add_argument('--hours', type=int, default=24, help='Hours ahead to analyze (default: 24)')
    parser.add_argument('--quick', action='store_true', help='Quick update (8 hours only)')
    parser.add_argument('--maintenance', action='store_true', help='Run maintenance only')
    
    args = parser.parse_args()
    
    processor = BettorBatchProcessor()
    
    if args.maintenance:
        processor.cleanup_and_maintenance()
    elif args.quick:
        processor.run_quick_update()
    else:
        processor.run_daily_batch(args.hours)
        processor.cleanup_and_maintenance()

if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Generate betting recommendations as clean JSON output."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime

from app.data.adapters.live_scraper import LiveDataScraper
from app.services.multi_market import analyze_comprehensive_markets
from app.services.earnings import calculate_expected_earnings


def main():
    """Generate betting recommendations as JSON."""
    print("🔍 Analyzing Man City vs Tottenham for betting opportunities...")
    
    try:
        # Get live data
        scraper = LiveDataScraper()
        live_data = scraper.get_live_match_data("Manchester City", "Tottenham")
        
        # Configuration
        config = {
            'home_mult': 1.05,
            'away_mult': 0.95,
            'league_avg_shots': 10.5,
            'bankroll': 1000.0,
            'kelly_fraction': 1.0,
            'max_stake_pct': 0.05
        }
        
        # Calculate signals
        signals = analyze_comprehensive_markets(live_data, config)
        
        # Calculate earnings
        earnings = calculate_expected_earnings(signals, config['bankroll'])
        
        # Create betting recommendations JSON
        betting_recommendations = {
            "match_info": {
                "home_team": live_data['match_info']['home_team'],
                "away_team": live_data['match_info']['away_team'],
                "kickoff_time": live_data['match_info']['kickoff_utc'],
                "analysis_time": datetime.now().isoformat(),
            },
            "summary": {
                "total_opportunities": len(signals),
                "total_stake_recommended": earnings['total_stakes'],
                "expected_profit": earnings['expected_profit'],
                "expected_roi_percent": earnings['expected_roi'],
                "bankroll_utilization_percent": earnings['bankroll_utilization']
            },
            "profit_scenarios": {
                scenario['name'].lower().replace(' ', '_'): {
                    "profit": scenario['profit'],
                    "roi_percent": scenario['roi']
                } for scenario in earnings['scenarios']
            },
            "betting_recommendations": []
        }
        
        # Add betting recommendations
        for i, signal in enumerate(signals[:20], 1):  # Top 20 opportunities
            rec = {
                "priority": i,
                "player": signal['player'],
                "team": signal['team'],
                "market": signal['market'],
                "bet_description": signal['prop'],
                "threshold": signal['threshold'] if signal['threshold'] > 0 else None,
                "odds_american": signal['odds'],
                "bookmaker": signal['book'],
                "model_probability_percent": round(signal['model_prob'] * 100, 1),
                "bookmaker_implied_probability_percent": round(signal['implied_prob'] * 100, 1),
                "edge_percent": round(signal['edge'] * 100, 1),
                "kelly_percent": round(signal['kelly'] * 100, 1),
                "recommended_stake_dollars": round(signal['suggested_stake'], 2),
                "potential_profit_dollars": round(
                    signal['suggested_stake'] * (
                        (float(signal['odds'].replace('+', '').replace('-', '')) / 100) + 1 
                        if signal['odds'].startswith('+') 
                        else (100 / float(signal['odds'].replace('-', ''))) + 1
                    ) - signal['suggested_stake'], 2
                ),
                "confidence": "HIGH" if signal['edge'] > 0.2 else "MEDIUM" if signal['edge'] > 0.1 else "LOW",
                "expected_minutes": signal['expected_minutes'],
                "home_away": "HOME" if signal['is_home'] else "AWAY"
            }
            betting_recommendations["betting_recommendations"].append(rec)
        
        # Output JSON
        output = json.dumps(betting_recommendations, indent=2)
        print("\n" + "="*80)
        print("📊 BETTING RECOMMENDATIONS JSON")
        print("="*80)
        print(output)
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"betting_recommendations_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(betting_recommendations, f, indent=2)
        
        print(f"\n💾 Saved to: {filename}")
        
        return betting_recommendations
        
    except Exception as e:
        error_response = {
            "error": True,
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(error_response, indent=2))
        return error_response


if __name__ == "__main__":
    result = main()

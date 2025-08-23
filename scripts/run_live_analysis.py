#!/usr/bin/env python
"""Script to run live betting analysis for current match."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import requests
import json
from datetime import datetime

from app.data.adapters.live_scraper import LiveDataScraper
from app.services.poisson import p_geq
from app.services.value import american_to_decimal, american_to_implied_prob, edge, suggested_stake
from app.services.adjust import compound_adjustments
from app.services.earnings import calculate_expected_earnings, format_earnings_report
from app.services.multi_market import analyze_comprehensive_markets


def main():
    """Run live betting analysis."""
    print("🔥 LIVE BETTING ANALYSIS - Man City vs Tottenham")
    print("=" * 60)
    
    # Initialize scraper and get live data
    scraper = LiveDataScraper()
    
    try:
        print("📡 Fetching live match data...")
        live_data = scraper.get_live_match_data("Manchester City", "Tottenham")
        
        print(f"⚽ Match: {live_data['match_info']['home_team']} vs {live_data['match_info']['away_team']}")
        print(f"🕐 Kickoff: {live_data['match_info']['kickoff_utc']}")
        print(f"📋 Players: {len(live_data['lineups'])}")
        print(f"📊 Markets: {len(live_data['odds'])}")
        print()
        
        # Calculate comprehensive betting signals across all markets
        print("🧮 Calculating comprehensive betting signals across ALL markets...")
        signals = calculate_comprehensive_signals(live_data)
        
        if signals:
            print(f"✅ Found {len(signals)} value betting opportunities!")
            print()
            display_signals(signals)
            
            # Calculate and display expected earnings
            print("\n" + "="*60)
            earnings = calculate_expected_earnings(signals, 1000.0)
            earnings_report = format_earnings_report(earnings, signals)
            print(earnings_report)
            
            # Save results
            save_results(live_data, signals, earnings)
        else:
            print("❌ No value betting opportunities found with current parameters.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


def calculate_comprehensive_signals(live_data):
    """Calculate comprehensive betting signals across all markets."""
    config = {
        'home_mult': 1.05,
        'away_mult': 0.95,
        'league_avg_shots': 10.5,
        'bankroll': 1000.0,
        'kelly_fraction': 1.0,
        'max_stake_pct': 0.05
    }
    
    return analyze_comprehensive_markets(live_data, config)


def calculate_signals(live_data):
    """Calculate betting signals from live data."""
    signals = []
    
    # Configuration
    config = {
        'home_mult': 1.05,
        'away_mult': 0.95,
        'league_avg_shots': 10.5,
        'bankroll': 1000.0,
        'kelly_fraction': 1.0,
        'max_stake_pct': 0.05
    }
    
    # Create lookups
    lineups_dict = {}
    for lineup in live_data['lineups']:
        key = (lineup['match_id'], lineup['player_name'], lineup['team'])
        lineups_dict[key] = lineup
    
    player_stats_dict = {}
    for player in live_data['player_stats']:
        key = (player['player_name'], player['team'])
        player_stats_dict[key] = player
    
    team_stats_dict = {}
    for team in live_data['team_stats']:
        team_stats_dict[team['team']] = team
    
    # Calculate signals for each odds entry
    for odds_entry in live_data['odds']:
        lineup_key = (odds_entry['match_id'], odds_entry['player_name'], odds_entry['team'])
        player_key = (odds_entry['player_name'], odds_entry['team'])
        
        if lineup_key not in lineups_dict or player_key not in player_stats_dict:
            continue
        
        lineup = lineups_dict[lineup_key]
        player_stats = player_stats_dict[player_key]
        
        # Determine opponent team
        opponent_team = lineup['away_team'] if lineup['team'] == lineup['home_team'] else lineup['home_team']
        opponent_stats = team_stats_dict.get(opponent_team)
        
        # Calculate adjusted lambda
        is_home = lineup['team'] == lineup['home_team']
        opponent_shots_allowed = opponent_stats['shots_allowed_pg'] if opponent_stats else config['league_avg_shots']
        
        adjusted_lambda = compound_adjustments(
            base_lam=player_stats['shots_pg'],
            expected_minutes=lineup['expected_minutes'],
            opponent_shots_allowed=opponent_shots_allowed,
            league_avg_shots_allowed=config['league_avg_shots'],
            is_home=is_home,
            home_mult=config['home_mult'],
            away_mult=config['away_mult']
        )
        
        # Calculate model probability
        model_prob = p_geq(odds_entry['threshold'], adjusted_lambda)
        
        # Calculate implied probability from odds
        implied_prob = american_to_implied_prob(odds_entry['odds_american'])
        
        # Calculate edge and value metrics
        prob_edge = edge(model_prob, implied_prob)
        
        # Only include positive expected value bets
        if prob_edge > 0:
            decimal_odds = american_to_decimal(odds_entry['odds_american'])
            stake = suggested_stake(model_prob, decimal_odds, config['bankroll'], 
                                  config['kelly_fraction'], config['max_stake_pct'])
            kelly_fraction = stake / config['bankroll'] if config['bankroll'] > 0 else 0
            
            signals.append({
                'match_id': odds_entry['match_id'],
                'player': odds_entry['player_name'],
                'team': odds_entry['team'],
                'prop': f"{odds_entry['market']} ≥ {odds_entry['threshold']}",
                'threshold': odds_entry['threshold'],
                'model_prob': model_prob,
                'implied_prob': implied_prob,
                'edge': prob_edge,
                'odds': odds_entry['odds_american'],
                'book': odds_entry['book'],
                'kelly': kelly_fraction,
                'suggested_stake': stake,
                'adjusted_lambda': adjusted_lambda,
                'base_lambda': player_stats['shots_pg'],
                'expected_minutes': lineup['expected_minutes'],
                'is_home': is_home
            })
    
    # Sort signals by edge (highest first)
    signals.sort(key=lambda x: x['edge'], reverse=True)
    return signals


def display_signals(signals):
    """Display betting signals in a nice format."""
    print("🎯 VALUE BETTING OPPORTUNITIES")
    print("-" * 80)
    
    for i, signal in enumerate(signals[:10], 1):  # Top 10
        print(f"{i:2d}. {signal['player']} ({signal['team']})")
        print(f"    📊 {signal['prop']}")
        print(f"    🎲 Model: {signal['model_prob']:.1%} | Book: {signal['implied_prob']:.1%} | Edge: {signal['edge']:.1%}")
        print(f"    💰 Odds: {signal['odds']} ({signal['book']}) | Kelly: {signal['kelly']:.1%}")
        print(f"    💵 Suggested Stake: ${signal['suggested_stake']:.2f}")
        print(f"    🏠 {'Home' if signal['is_home'] else 'Away'} | Minutes: {signal['expected_minutes']} | λ: {signal['adjusted_lambda']:.2f}")
        print()
    
    # Summary stats
    total_edge = sum(s['edge'] for s in signals)
    total_stake = sum(s['suggested_stake'] for s in signals)
    avg_edge = total_edge / len(signals) if signals else 0
    
    print("📈 SUMMARY")
    print("-" * 30)
    print(f"Total Opportunities: {len(signals)}")
    print(f"Average Edge: {avg_edge:.1%}")
    print(f"Total Suggested Stakes: ${total_stake:.2f}")
    print(f"Best Opportunity: {signals[0]['player']} - {signals[0]['edge']:.1%} edge")


def save_results(live_data, signals, earnings):
    """Save results to CSV files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save signals
    if signals:
        df_signals = pd.DataFrame(signals)
        df_signals.to_csv(f'live_signals_{timestamp}.csv', index=False)
        print(f"💾 Saved signals to: live_signals_{timestamp}.csv")
    
    # Save lineups
    df_lineups = pd.DataFrame(live_data['lineups'])
    df_lineups.to_csv(f'live_lineups_{timestamp}.csv', index=False)
    
    # Save earnings analysis
    with open(f'earnings_analysis_{timestamp}.json', 'w') as f:
        json.dump(earnings, f, indent=2, default=str)
    
    # Save all data as JSON
    live_data_with_earnings = live_data.copy()
    live_data_with_earnings['earnings_analysis'] = earnings
    
    with open(f'live_data_{timestamp}.json', 'w') as f:
        json.dump(live_data_with_earnings, f, indent=2, default=str)
    
    print(f"💾 Saved all data to: live_data_{timestamp}.json")
    print(f"💾 Saved earnings analysis to: earnings_analysis_{timestamp}.json")


if __name__ == "__main__":
    exit(main())

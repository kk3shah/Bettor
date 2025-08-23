#!/usr/bin/env python3
"""
ESPN-based Analysis - Calculate Profitable Odds Thresholds
No fake betting data - pure mathematical analysis based on real ESPN stats
"""

from typing import Dict, List
from .poisson import p_geq
from .adjust import compound_adjustments
from .value import decimal_to_american


def calculate_sot_probability(player_stats: Dict, adjustments: Dict) -> float:
    """Calculate shots on target lambda using conversion rate."""
    shots_lambda = compound_adjustments(
        base_lam=player_stats['shots_pg'],
        expected_minutes=adjustments['expected_minutes'],
        opponent_shots_allowed=adjustments['opponent_shots_allowed'],
        league_avg_shots_allowed=adjustments['league_avg_shots_allowed'],
        is_home=adjustments['is_home'],
        home_mult=1.05,
        away_mult=0.95
    )
    # Assume ~50% shot accuracy on average
    sot_conversion = player_stats.get('sot_pg', 0) / max(player_stats.get('shots_pg', 1), 0.1)
    sot_conversion = min(max(sot_conversion, 0.3), 0.7)  # Reasonable bounds
    return shots_lambda * sot_conversion


def calculate_fouls_probability(player_stats: Dict, adjustments: Dict) -> float:
    """Calculate fouls lambda with position adjustment."""
    base_fouls = player_stats['fouls_pg']
    position_mult = 1.1 if player_stats.get('position') in ['M', 'MF', 'CM', 'CDM'] else 1.0
    return base_fouls * (adjustments['expected_minutes'] / 90) * position_mult


def calculate_card_probability(player_stats: Dict, adjustments: Dict) -> float:
    """Calculate card probability (not Poisson - single event).""" 
    base_card_rate = player_stats.get('yc_pg', 0.05)
    position = player_stats.get('position', 'MF')
    
    # Position adjustments for card probability
    if position in ['CDM', 'CM']:
        base_card_rate *= 1.2
    elif position in ['CB', 'LB', 'RB']:
        base_card_rate *= 1.1
    
    # Minutes adjustment
    minutes_factor = adjustments['expected_minutes'] / 90
    return min(base_card_rate * minutes_factor, 0.4)  # Cap at 40%


def calculate_goals_probability(player_stats: Dict, adjustments: Dict) -> float:
    """Calculate goals lambda for attacking players."""
    base_goals = player_stats.get('goals_pg', 0.1)
    position_mult = 1.0
    
    if player_stats.get('position') in ['F', 'ST', 'CF']:
        position_mult = 1.2
    elif player_stats.get('position') in ['RW', 'LW', 'CAM']:
        position_mult = 1.1
        
    return base_goals * (adjustments['expected_minutes'] / 90) * position_mult


def analyze_espn_based_markets(live_data: Dict, config: Dict) -> List[Dict]:
    """
    Analyze player prop opportunities using ONLY real ESPN stats.
    Returns profitable odds thresholds instead of fake profit calculations.
    """
    signals = []
    
    # Create lookups using SHIRT NUMBERS + TEAM as primary key
    lineups_dict = {}
    for lineup in live_data['lineups']:
        key = (lineup['shirt_number'], lineup['team'])
        lineups_dict[key] = lineup

    player_stats_dict = {}
    for player in live_data['player_stats']:
        key = (player['shirt_number'], player['team'])
        player_stats_dict[key] = player

    team_stats_dict = {}
    for team in live_data['team_stats']:
        team_stats_dict[team['team']] = team

    # Generate analysis for each player with real stats
    for player_key, player_stats in player_stats_dict.items():
        shirt_number, team = player_key
        
        if player_key not in lineups_dict:
            continue
            
        lineup = lineups_dict[player_key]
        player_name = player_stats['player_name']
        position = player_stats['position']
        
        # Skip players with no real game data
        if player_stats.get('apps', 0) == 0:
            continue
        
        # Determine opponent team
        opponent_team = lineup['away_team'] if lineup['team'] == lineup['home_team'] else lineup['home_team']
        opponent_stats = team_stats_dict.get(opponent_team)
        
        # Common adjustments
        is_home = lineup['team'] == lineup['home_team']
        adjustments = {
            'expected_minutes': lineup['expected_minutes'],
            'opponent_shots_allowed': opponent_stats['shots_allowed_pg'] if opponent_stats else config['league_avg_shots'],
            'league_avg_shots_allowed': config['league_avg_shots'],
            'is_home': is_home,
        }
        
        # Generate betting opportunities based on player's real performance
        betting_opportunities = []
        
        # 1. Player Shots (for players who actually shoot)
        if player_stats['shots_pg'] > 0.5:
            # Determine appropriate thresholds based on shooting frequency
            if player_stats['shots_pg'] >= 3.0:
                thresholds = [1, 2, 3]
            elif player_stats['shots_pg'] >= 2.0:
                thresholds = [1, 2] 
            else:
                thresholds = [1]
            
            for threshold in thresholds:
                adjusted_lambda = compound_adjustments(
                    base_lam=player_stats['shots_pg'],
                    expected_minutes=lineup['expected_minutes'],
                    opponent_shots_allowed=adjustments['opponent_shots_allowed'],
                    league_avg_shots_allowed=config['league_avg_shots'],
                    is_home=is_home,
                    home_mult=config.get('home_mult', 1.05),
                    away_mult=config.get('away_mult', 0.95)
                )
                model_prob = p_geq(threshold, adjusted_lambda)
                
                if model_prob > 0.20:  # Only include if reasonable probability
                    betting_opportunities.append({
                        'market': 'Player Shots',
                        'threshold': threshold,
                        'probability': model_prob
                    })
        
        # 2. Shots on Target (for accurate shooters)
        if player_stats.get('sot_pg', 0) > 0.3:
            sot_lambda = calculate_sot_probability(player_stats, adjustments)
            sot_prob = p_geq(1, sot_lambda)
            
            if sot_prob > 0.20:
                betting_opportunities.append({
                    'market': 'Shots on Target',
                    'threshold': 1,
                    'probability': sot_prob
                })
        
        # 3. Player Fouls (for physical players)
        if player_stats.get('fouls_pg', 0) > 0.8:
            fouls_lambda = calculate_fouls_probability(player_stats, adjustments)
            
            # Try different thresholds based on foul frequency
            foul_thresholds = [1, 2] if player_stats['fouls_pg'] > 2.0 else [1]
            
            for threshold in foul_thresholds:
                fouls_prob = p_geq(threshold, fouls_lambda)
                if fouls_prob > 0.30:
                    betting_opportunities.append({
                        'market': 'Player Fouls',
                        'threshold': threshold, 
                        'probability': fouls_prob
                    })
        
        # 4. Yellow Cards (for players with card history)
        if player_stats.get('yc_pg', 0) > 0.03:
            card_prob = calculate_card_probability(player_stats, adjustments)
            
            if card_prob > 0.12:  # 12%+ chance makes it interesting
                betting_opportunities.append({
                    'market': 'To Be Booked',
                    'threshold': 1,
                    'probability': card_prob
                })
        
        # 5. Anytime Goalscorer (for attacking players)
        if position in ['F', 'ST', 'CF', 'RW', 'LW'] and player_stats.get('goals_pg', 0) > 0.05:
            goals_lambda = calculate_goals_probability(player_stats, adjustments)
            goals_prob = p_geq(1, goals_lambda)
            
            if goals_prob > 0.10:  # 10%+ chance for goal
                betting_opportunities.append({
                    'market': 'Anytime Goalscorer',
                    'threshold': 1,
                    'probability': goals_prob
                })
        
        # Convert opportunities to signals with profitable odds thresholds
        for opp in betting_opportunities:
            model_prob = opp['probability']
            
            # Calculate what odds would be profitable
            fair_decimal_odds = 1 / model_prob
            
            # Add 25% margin for profitable betting (accounts for variance)
            profitable_decimal_odds = fair_decimal_odds * 1.25
            profitable_american_odds = decimal_to_american(profitable_decimal_odds)
            
            # Confidence based on sample size and probability
            if player_stats['apps'] >= 10 and model_prob > 0.35:
                confidence = 'High'
            elif player_stats['apps'] >= 5 and model_prob > 0.25:
                confidence = 'Medium'
            else:
                confidence = 'Low'
            
            signals.append({
                'player_name': player_name,
                'shirt_number': shirt_number,
                'team': team,
                'position': position,
                'market': opp['market'],
                'threshold': opp['threshold'],
                'model_prob': round(model_prob, 3),
                'fair_odds_decimal': round(fair_decimal_odds, 2),
                'min_profitable_odds_decimal': round(profitable_decimal_odds, 2),
                'min_profitable_odds_american': profitable_american_odds,
                'confidence': confidence,
                'apps': player_stats['apps'],
                'player_avg': {
                    'shots_pg': player_stats.get('shots_pg', 0),
                    'sot_pg': player_stats.get('sot_pg', 0),
                    'fouls_pg': player_stats.get('fouls_pg', 0),
                    'goals_pg': player_stats.get('goals_pg', 0),
                    'yc_pg': player_stats.get('yc_pg', 0)
                },
                'reasoning': f"{model_prob:.1%} chance based on {player_stats['apps']} apps, avg {player_stats.get(opp['market'].lower().replace(' ', '_').replace('player_', '').replace('anytime_goalscorer', 'goals') + '_pg', 0):.1f}/game"
            })
    
    # Sort by confidence and probability
    signals.sort(key=lambda x: (
        {'High': 3, 'Medium': 2, 'Low': 1}[x['confidence']],
        x['model_prob']
    ), reverse=True)
    
    return signals

"""Multi-market analysis for comprehensive player prop betting."""
from typing import Dict, List, Tuple
from .poisson import p_geq
from .adjust import compound_adjustments
from .value import american_to_decimal, american_to_implied_prob, edge, suggested_stake


def calculate_goal_probability(player_stats: Dict, adjustments: Dict) -> float:
    """Calculate goal scoring probability using goals per game and shot conversion."""
    # Approximate goals per game from shots and conversion rate
    shots_per_game = player_stats.get('shots_pg', 0)
    sot_per_game = player_stats.get('sot_pg', 0)
    
    if shots_per_game == 0:
        return 0.0
    
    # Estimate conversion rate and goals per game
    conversion_rate = 0.15 if player_stats['player_name'] == 'Erling Haaland' else 0.10
    goals_per_game = shots_per_game * conversion_rate
    
    # Apply adjustments similar to shots
    adjusted_goals = compound_adjustments(
        base_lam=goals_per_game,
        expected_minutes=adjustments.get('expected_minutes', 90),
        opponent_shots_allowed=adjustments.get('opponent_shots_allowed'),
        league_avg_shots_allowed=adjustments.get('league_avg_shots_allowed', 10.5),
        is_home=adjustments.get('is_home', True),
        home_mult=1.08,  # Slightly higher for goals
        away_mult=0.92
    )
    
    return adjusted_goals


def calculate_sot_probability(player_stats: Dict, adjustments: Dict) -> float:
    """Calculate shots on target probability."""
    base_sot = player_stats.get('sot_pg', 0)
    
    adjusted_sot = compound_adjustments(
        base_lam=base_sot,
        expected_minutes=adjustments.get('expected_minutes', 90),
        opponent_shots_allowed=adjustments.get('opponent_shots_allowed'),
        league_avg_shots_allowed=adjustments.get('league_avg_shots_allowed', 10.5),
        is_home=adjustments.get('is_home', True),
        home_mult=1.05,
        away_mult=0.95
    )
    
    return adjusted_sot


def calculate_fouls_probability(player_stats: Dict, adjustments: Dict) -> float:
    """Calculate fouls committed probability."""
    base_fouls = player_stats.get('fouls_pg', 0)
    
    # Fouls are less affected by home/away but more by game tempo
    adjusted_fouls = compound_adjustments(
        base_lam=base_fouls,
        expected_minutes=adjustments.get('expected_minutes', 90),
        opponent_shots_allowed=None,  # Not relevant for fouls
        is_home=adjustments.get('is_home', True),
        home_mult=1.02,  # Minimal home advantage for fouls
        away_mult=0.98
    )
    
    return adjusted_fouls


def calculate_cards_probability(player_stats: Dict, adjustments: Dict) -> float:
    """Calculate card probability (not Poisson - just probability)."""
    base_cards = player_stats.get('yc_pg', 0)
    
    # Scale by minutes and add referee factor
    minutes_factor = adjustments.get('expected_minutes', 90) / 90
    card_prob = base_cards * minutes_factor
    
    # Away players get cards more often
    if not adjustments.get('is_home', True):
        card_prob *= 1.15
    
    return min(card_prob, 0.9)  # Cap at 90% probability


def analyze_comprehensive_markets(live_data: Dict, config: Dict) -> List[Dict]:
    """Analyze all player prop markets comprehensively."""
    signals = []
    
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
    
    # Analyze each market
    for odds_entry in live_data['odds']:
        lineup_key = (odds_entry['match_id'], odds_entry['player_name'], odds_entry['team'])
        player_key = (odds_entry['player_name'], odds_entry['team'])
        
        # Skip team markets for now
        if odds_entry['market'] in ['Team Corners', 'Total Corners']:
            continue
            
        if lineup_key not in lineups_dict or player_key not in player_stats_dict:
            continue
        
        lineup = lineups_dict[lineup_key]
        player_stats = player_stats_dict[player_key]
        
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
        
        # Calculate model probability based on market type
        model_prob = 0.0
        
        if odds_entry['market'] == 'Player Shots':
            adjusted_lambda = compound_adjustments(
                base_lam=player_stats['shots_pg'],
                expected_minutes=lineup['expected_minutes'],
                opponent_shots_allowed=adjustments['opponent_shots_allowed'],
                league_avg_shots_allowed=config['league_avg_shots'],
                is_home=is_home,
                home_mult=config['home_mult'],
                away_mult=config['away_mult']
            )
            model_prob = p_geq(odds_entry['threshold'], adjusted_lambda)
            
        elif odds_entry['market'] == 'Player Shots on Target':
            sot_lambda = calculate_sot_probability(player_stats, adjustments)
            model_prob = p_geq(odds_entry['threshold'], sot_lambda)
            
        elif odds_entry['market'] in ['Anytime Goalscorer', '2+ Goals']:
            goal_lambda = calculate_goal_probability(player_stats, adjustments)
            if odds_entry['market'] == 'Anytime Goalscorer':
                model_prob = 1 - p_geq(1, goal_lambda) if goal_lambda > 0 else 0.1  # P(X >= 1) = 1 - P(X = 0)
            else:
                model_prob = p_geq(odds_entry['threshold'], goal_lambda)
                
        elif odds_entry['market'] == 'Player Fouls':
            fouls_lambda = calculate_fouls_probability(player_stats, adjustments)
            model_prob = p_geq(odds_entry['threshold'], fouls_lambda)
            
        elif odds_entry['market'] == 'Player Card':
            model_prob = calculate_cards_probability(player_stats, adjustments)
            
        elif odds_entry['market'] == 'Player Passes':
            # Simple approximation for passes
            base_passes = player_stats.get('passes_pg', 50)
            passes_adjusted = base_passes * (lineup['expected_minutes'] / 90)
            # For passes, we use normal approximation (not Poisson for high numbers)
            # Simplified: assume if expected > threshold, 65% probability
            model_prob = 0.65 if passes_adjusted > odds_entry['threshold'] else 0.35
        
        # Calculate value metrics
        if model_prob > 0:
            implied_prob = american_to_implied_prob(odds_entry['odds_american'])
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
                    'market': odds_entry['market'],
                    'prop': f"{odds_entry['market']} {'≥' if odds_entry['threshold'] > 0 else ''} {odds_entry['threshold'] if odds_entry['threshold'] > 0 else ''}".strip(),
                    'threshold': odds_entry['threshold'],
                    'model_prob': model_prob,
                    'implied_prob': implied_prob,
                    'edge': prob_edge,
                    'odds': odds_entry['odds_american'],
                    'book': odds_entry['book'],
                    'kelly': kelly_fraction,
                    'suggested_stake': stake,
                    'expected_minutes': lineup['expected_minutes'],
                    'is_home': is_home
                })
    
    # Sort signals by edge (highest first)
    signals.sort(key=lambda x: x['edge'], reverse=True)
    return signals

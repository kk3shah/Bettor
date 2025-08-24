#!/usr/bin/env python3
"""
🏟️ Team Props Analysis System
Generates betting opportunities for team-level statistics
"""
import json
import csv
from pathlib import Path
from datetime import datetime
from simple_ml_model import ml_model
import math

def get_team_logo(team_name):
    """Get team logo URL from ESPN mapping."""
    try:
        mapping_file = Path("data/espn_team_mapping.json")
        if mapping_file.exists():
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
                team_data = mapping.get('by_name', {}).get(team_name)
                if team_data:
                    return team_data.get('logo', '')
    except Exception as e:
        print(f"⚠️ Error getting team logo: {e}")
    return ''

def get_realistic_team_stats():
    """Get realistic team statistics for Premier League teams."""
    return {
        # Attacking stats
        'goals_per_game': 1.4,
        'shots_per_game': 12.5,
        'shots_on_target_per_game': 4.2,
        'corners_per_game': 5.8,
        'first_half_goals_per_game': 0.7,
        'second_half_goals_per_game': 0.7,
        
        # Defensive/Disciplinary stats
        'yellow_cards_per_game': 2.1,
        'red_cards_per_game': 0.08,
        'fouls_per_game': 11.2,
        'offsides_per_game': 2.3,
        
        # Match flow stats
        'possession_percentage': 52.0,
        'pass_accuracy_percentage': 82.5,
        'crosses_per_game': 18.5,
        'throw_ins_per_game': 15.2
    }

def calculate_team_poisson_probability(rate, threshold):
    """Calculate probability of team achieving >= threshold using Poisson distribution."""
    if rate <= 0:
        return 0.0
    
    # Calculate P(X >= threshold) = 1 - P(X < threshold)
    cumulative_prob = 0
    for k in range(int(threshold)):
        prob_k = (math.e ** -rate) * (rate ** k) / math.factorial(k)
        cumulative_prob += prob_k
    
    return max(0.01, min(0.99, 1 - cumulative_prob))

def get_team_prop_thresholds(rate_per_game, prop_name):
    """Get optimal thresholds for team props based on rate."""
    if rate_per_game <= 0:
        return []
    
    thresholds = []
    
    if 'goals' in prop_name.lower():
        # Goals: 0.5, 1.5, 2.5, 3.5
        for threshold in [0.5, 1.5, 2.5, 3.5]:
            if rate_per_game >= threshold * 0.3:  # Only if reasonable chance
                thresholds.append(threshold)
    
    elif 'shots' in prop_name.lower() and 'target' not in prop_name.lower():
        # Total shots: 8.5, 10.5, 12.5, 15.5
        for threshold in [8.5, 10.5, 12.5, 15.5]:
            if rate_per_game >= threshold * 0.4:
                thresholds.append(threshold)
    
    elif 'shots on target' in prop_name.lower():
        # Shots on target: 2.5, 3.5, 4.5, 6.5
        for threshold in [2.5, 3.5, 4.5, 6.5]:
            if rate_per_game >= threshold * 0.4:
                thresholds.append(threshold)
    
    elif 'corners' in prop_name.lower():
        # Corners: 3.5, 4.5, 5.5, 7.5
        for threshold in [3.5, 4.5, 5.5, 7.5]:
            if rate_per_game >= threshold * 0.4:
                thresholds.append(threshold)
    
    elif 'yellow cards' in prop_name.lower():
        # Yellow cards: 1.5, 2.5, 3.5
        for threshold in [1.5, 2.5, 3.5]:
            if rate_per_game >= threshold * 0.3:
                thresholds.append(threshold)
    
    elif 'fouls' in prop_name.lower():
        # Fouls: 8.5, 10.5, 12.5, 15.5
        for threshold in [8.5, 10.5, 12.5, 15.5]:
            if rate_per_game >= threshold * 0.4:
                thresholds.append(threshold)
    
    else:
        # Generic thresholds based on rate
        base_threshold = max(0.5, rate_per_game * 0.7)
        thresholds = [base_threshold, base_threshold + 1, base_threshold + 2]
    
    # Return only the highest reasonable threshold for each prop
    if thresholds:
        # Find the threshold with probability between 20-80%
        best_threshold = None
        for threshold in sorted(thresholds, reverse=True):
            prob = calculate_team_poisson_probability(rate_per_game, threshold)
            if 0.2 <= prob <= 0.8:
                best_threshold = threshold
                break
        
        return [best_threshold] if best_threshold else [thresholds[0]]
    
    return []

def generate_team_props_analysis(match_id, home_team, away_team):
    """Generate team-level betting analysis for a match."""
    analysis_entries = []
    
    # Get team logos
    home_logo = get_team_logo(home_team)
    away_logo = get_team_logo(away_team)
    
    # Get realistic team stats
    base_stats = get_realistic_team_stats()
    
    # Process both teams
    for team_name, team_logo in [(home_team, home_logo), (away_team, away_logo)]:
        
        # Add some team-specific variance (based on team strength)
        team_multipliers = {
            'Manchester City': 1.3, 'Arsenal': 1.25, 'Liverpool': 1.25, 'Chelsea': 1.15,
            'Manchester United': 1.1, 'Tottenham Hotspur': 1.1, 'Newcastle United': 1.05,
            'Aston Villa': 1.0, 'Brighton & Hove Albion': 0.95, 'West Ham United': 0.95,
            'Crystal Palace': 0.9, 'AFC Bournemouth': 0.85, 'Fulham': 0.9,
            'Wolverhampton Wanderers': 0.85, 'Everton': 0.8, 'Brentford': 0.85,
            'Nottingham Forest': 0.8, 'Luton Town': 0.7, 'Burnley': 0.7, 'Sheffield United': 0.65
        }
        
        multiplier = team_multipliers.get(team_name, 1.0)
        
        # Define team props with adjusted rates
        team_props = [
            ('Team Goals', base_stats['goals_per_game'] * multiplier),
            ('Team Shots', base_stats['shots_per_game'] * multiplier),
            ('Team Shots on Target', base_stats['shots_on_target_per_game'] * multiplier),
            ('Team Corners', base_stats['corners_per_game'] * multiplier),
            ('Team Yellow Cards', base_stats['yellow_cards_per_game']),  # Less variance for cards
            ('Team Fouls', base_stats['fouls_per_game']),
            ('Team First Half Goals', base_stats['first_half_goals_per_game'] * multiplier),
        ]
        
        for prop_name, rate_per_game in team_props:
            if rate_per_game <= 0:
                continue
            
            # Get optimal thresholds for this prop
            thresholds = get_team_prop_thresholds(rate_per_game, prop_name)
            
            for threshold in thresholds:
                # Calculate model probability
                model_prob = calculate_team_poisson_probability(rate_per_game, threshold)
                
                if model_prob < 0.1 or model_prob > 0.9:
                    continue  # Skip extreme probabilities
                
                # Enhanced analysis data for team props
                enhanced_data = {
                    'team': team_name,
                    'prop': prop_name,
                    'threshold': str(threshold),
                    'model_prob': model_prob,
                    'rate_per_game': rate_per_game,
                    'team_strength': multiplier,
                    'is_home': team_name == home_team,
                    'logo': team_logo
                }
                
                # Calculate Final Score for team props
                final_score = ml_model.calculate_final_score(enhanced_data)
                
                # Add team-specific bonuses to Final Score
                if multiplier > 1.1:  # Strong teams
                    final_score += 5
                elif multiplier < 0.8:  # Weak teams (higher variance)
                    final_score += 3
                
                # Home advantage bonus
                if team_name == home_team:
                    final_score += 3
                
                # Calculate suggested stake
                base_stake = 50
                score_multiplier = final_score / 50
                suggested_stake = base_stake * max(0.5, min(2.0, score_multiplier))
                
                analysis_data = {
                    'team': team_name,
                    'prop': prop_name,
                    'threshold': str(threshold),
                    'model_prob': round(model_prob, 4),
                    'final_score': round(final_score, 1),
                    'suggested_stake': round(suggested_stake, 2),
                    'rate_per_game': round(rate_per_game, 3),
                    'team_strength': round(multiplier, 2),
                    'is_home': team_name == home_team,
                    'logo': team_logo,
                    'prop_type': 'team'  # Distinguish from player props
                }
                
                analysis_entries.append({
                    'match_id': match_id,
                    'analysis_data': json.dumps(analysis_data),
                    'generated_at': datetime.now().isoformat()
                })
    
    return analysis_entries

def add_team_props_to_analysis():
    """Add team props to existing match analysis."""
    print("🏟️ Adding team props to analysis...")
    
    # Read existing matches
    matches_file = Path("data/matches.csv")
    if not matches_file.exists():
        print("❌ No matches file found")
        return
    
    all_analysis = []
    
    # Load existing player analysis
    analysis_file = Path("data/analysis.csv")
    if analysis_file.exists():
        with open(analysis_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Only keep the fields we need
                clean_row = {
                    'match_id': row.get('match_id', ''),
                    'analysis_data': row.get('analysis_data', ''),
                    'generated_at': row.get('generated_at', '')
                }
                all_analysis.append(clean_row)
    
    # Generate team props for each match
    with open(matches_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for match in reader:
            match_id = match['match_id']
            home_team = match['home_team']
            away_team = match['away_team']
            
            print(f"🎯 Generating team props for: {home_team} vs {away_team}")
            
            team_analysis = generate_team_props_analysis(match_id, home_team, away_team)
            
            # Add to all analysis
            all_analysis.extend(team_analysis)
    
    # Write updated analysis
    if all_analysis:
        with open(analysis_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['match_id', 'analysis_data', 'generated_at']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_analysis)
        
        print(f"✅ Added team props analysis - Total: {len(all_analysis)} opportunities")
    else:
        print("❌ No analysis generated")

if __name__ == "__main__":
    add_team_props_to_analysis()

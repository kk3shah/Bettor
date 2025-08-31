"""
Simplified WhoScored integration for Bettor system.
Returns empty results when WhoScored data is unavailable (graceful fallback).
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import pandas as pd

def get_whoscored_analysis(home_team: str, away_team: str) -> List[Dict[str, Any]]:
    """
    Get betting analysis using WhoScored data.
    Returns empty list if no data available (graceful fallback to ESPN).
    """
    try:
        # Check if we have cached WhoScored data
        data_dir = Path("ws_pipeline/data")
        
        if not data_dir.exists():
            print(f"⚠️ WhoScored data directory not found - using ESPN fallback")
            return []
        
        # Look for cached fixtures and team data
        fixture_files = list(data_dir.glob("fixtures_*.csv"))
        team_files = list(data_dir.glob("team_*_players.csv"))
        
        if not fixture_files or not team_files:
            print(f"⚠️ No WhoScored cached data available - using ESPN fallback")
            return []
        
        # Try to find the match in cached fixtures
        for fixture_file in fixture_files:
            try:
                fixtures_df = pd.read_csv(fixture_file)
                match_row = fixtures_df[
                    (fixtures_df['home_team_name'].str.contains(home_team, case=False, na=False)) &
                    (fixtures_df['away_team_name'].str.contains(away_team, case=False, na=False))
                ]
                
                if not match_row.empty:
                    print(f"✅ Found WhoScored data for {home_team} vs {away_team}")
                    # Generate some sample betting opportunities from WhoScored data
                    return _generate_whoscored_opportunities(match_row.iloc[0], team_files)
                    
            except Exception as e:
                continue
        
        print(f"⚠️ Match {home_team} vs {away_team} not found in WhoScored cache - using ESPN fallback")
        return []
        
    except Exception as e:
        print(f"⚠️ WhoScored integration error: {e} - using ESPN fallback")
        return []

def get_whoscored_player_stats(player_name: str, team_name: str = None) -> Optional[Dict[str, Any]]:
    """
    Get player statistics from WhoScored cached data.
    Returns None if no data available (graceful fallback to ESPN).
    """
    try:
        data_dir = Path("ws_pipeline/data")
        team_files = list(data_dir.glob("team_*_players.csv"))
        
        for team_file in team_files:
            try:
                players_df = pd.read_csv(team_file)
                
                # Find player by name (fuzzy match)
                player_matches = players_df[
                    players_df['player_name'].str.contains(player_name, case=False, na=False)
                ]
                
                if not player_matches.empty:
                    player_data = player_matches.iloc[0].to_dict()
                    
                    # Convert to per-game stats
                    apps = max(1, player_data.get('apps_total', 1) or 1)
                    
                    return {
                        'goals_per_game': player_data.get('goals', 0) / apps,
                        'assists_per_game': player_data.get('assists', 0) / apps,
                        'shots_per_game': player_data.get('shots_per_game', 0),
                        'shots_on_target_per_game': player_data.get('shots_on_target_per_game', 0),
                        'yellow_cards_per_game': player_data.get('yellow', 0) / apps,
                        'fouls_per_game': player_data.get('fouls_per_game', 0),
                        'rating': player_data.get('rating', 6.5),
                        'pass_success': player_data.get('pass_success', 0.8),
                        'apps_total': apps,
                        'source': 'WhoScored'
                    }
                    
            except Exception as e:
                continue
        
        return None
        
    except Exception as e:
        print(f"⚠️ Error getting WhoScored player stats: {e}")
        return None

def _generate_whoscored_opportunities(match_data: pd.Series, team_files: List[Path]) -> List[Dict[str, Any]]:
    """Generate betting opportunities from WhoScored match and team data."""
    opportunities = []
    
    try:
        home_team = match_data.get('home_team_name', 'Home Team')
        away_team = match_data.get('away_team_name', 'Away Team')
        match_id = f"ws_{home_team}_{away_team}"
        
        # Load team player data
        home_players = []
        away_players = []
        
        for team_file in team_files:
            try:
                players_df = pd.read_csv(team_file)
                # Add players to respective teams (simplified logic)
                for _, player in players_df.iterrows():
                    player_dict = player.to_dict()
                    apps = max(1, player_dict.get('apps_total', 1) or 1)
                    
                    # Create player opportunity
                    if player_dict.get('goals', 0) > 0:  # Only players with goals
                        opportunities.append({
                            'match_id': match_id,
                            'home_team': home_team,
                            'away_team': away_team,
                            'player_name': player_dict.get('player_name', 'Unknown'),
                            'prop_type': 'Anytime Goalscorer',
                            'rate_per_game': player_dict.get('goals', 0) / apps,
                            'final_score': min(85, (player_dict.get('goals', 0) / apps) * 100),
                            'model_prob': min(0.8, player_dict.get('goals', 0) / apps),
                            'confidence': 0.65,
                            'source': 'WhoScored'
                        })
                    
                    if player_dict.get('assists', 0) > 0:  # Only players with assists
                        opportunities.append({
                            'match_id': match_id,
                            'home_team': home_team,
                            'away_team': away_team,
                            'player_name': player_dict.get('player_name', 'Unknown'),
                            'prop_type': 'Assists Over 0.5',
                            'rate_per_game': player_dict.get('assists', 0) / apps,
                            'final_score': min(80, (player_dict.get('assists', 0) / apps) * 100),
                            'model_prob': min(0.7, player_dict.get('assists', 0) / apps),
                            'confidence': 0.6,
                            'source': 'WhoScored'
                        })
                        
            except Exception as e:
                continue
        
        # Limit to top opportunities to avoid overwhelming
        opportunities = sorted(opportunities, key=lambda x: x['final_score'], reverse=True)[:15]
        
        print(f"✅ Generated {len(opportunities)} WhoScored opportunities")
        return opportunities
        
    except Exception as e:
        print(f"⚠️ Error generating WhoScored opportunities: {e}")
        return []

# Backward compatibility functions
def enhance_analysis_with_whoscored(existing_analysis: List[Dict], 
                                  home_team: str, away_team: str) -> List[Dict]:
    """Enhance existing analysis with WhoScored data."""
    try:
        ws_analysis = get_whoscored_analysis(home_team, away_team)
        if ws_analysis:
            enhanced = existing_analysis.copy()
            enhanced.extend(ws_analysis)
            return enhanced
        return existing_analysis
    except Exception as e:
        print(f"⚠️ Error enhancing with WhoScored: {e}")
        return existing_analysis
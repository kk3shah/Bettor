"""
Feature engineering for WhoScored pipeline.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any

from . import utils

logger = utils.setup_logging(__name__)

class FeatureEngineer:
    """Handles feature engineering for match prediction."""
    
    def __init__(self):
        self.feature_cache = {}
    
    def make_features(self, home_team_id: int, away_team_id: int, 
                     players_df: pd.DataFrame, team_stats_df: pd.DataFrame,
                     fixtures_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Create feature vector for a specific fixture."""
        
        cache_key = f"{home_team_id}_{away_team_id}"
        if cache_key in self.feature_cache:
            return self.feature_cache[cache_key]
        
        logger.info(f"Creating features for teams {home_team_id} vs {away_team_id}")
        
        features = {}
        
        # Basic team information
        features['home_team_id'] = home_team_id
        features['away_team_id'] = away_team_id
        
        # Get team statistics
        home_stats = self._get_team_stats(home_team_id, team_stats_df)
        away_stats = self._get_team_stats(away_team_id, team_stats_df)
        
        # Team-level features
        features.update(self._create_team_features(home_stats, away_stats))
        
        # Player-level features
        home_players = players_df[players_df['team_id'] == home_team_id]
        away_players = players_df[players_df['team_id'] == away_team_id]
        
        features.update(self._create_player_features(home_players, away_players))
        
        # Advanced features
        features.update(self._create_advanced_features(home_stats, away_stats, home_players, away_players))
        
        # Form features (if fixtures history available)
        if fixtures_df is not None:
            features.update(self._create_form_features(home_team_id, away_team_id, fixtures_df))
        
        # Cache the features
        self.feature_cache[cache_key] = features
        
        logger.info(f"Created {len(features)} features for {home_team_id} vs {away_team_id}")
        return features
    
    def _get_team_stats(self, team_id: int, team_stats_df: pd.DataFrame) -> Dict[str, Any]:
        """Get team statistics."""
        team_row = team_stats_df[team_stats_df['team_id'] == team_id]
        
        if team_row.empty:
            logger.warning(f"No team stats found for team {team_id}")
            return self._get_default_team_stats()
        
        return team_row.iloc[0].to_dict()
    
    def _get_default_team_stats(self) -> Dict[str, Any]:
        """Get default team statistics when data is missing."""
        return {
            'avg_rating': 6.5,
            'total_goals': 0,
            'total_assists': 0,
            'avg_shots_per_game': 10.0,
            'avg_pass_success': 0.8,
            'total_cards': 0,
            'squad_size': 25,
            'regular_players': 15,
            'high_rated_players': 5
        }
    
    def _create_team_features(self, home_stats: Dict, away_stats: Dict) -> Dict[str, Any]:
        """Create team-level features."""
        features = {}
        
        # Home team features
        features['home_avg_rating'] = home_stats.get('avg_rating', 6.5)
        features['home_total_goals'] = home_stats.get('total_goals', 0)
        features['home_total_assists'] = home_stats.get('total_assists', 0)
        features['home_avg_shots_per_game'] = home_stats.get('avg_shots_per_game', 10.0)
        features['home_avg_pass_success'] = home_stats.get('avg_pass_success', 0.8)
        features['home_total_cards'] = home_stats.get('total_cards', 0)
        features['home_squad_size'] = home_stats.get('squad_size', 25)
        features['home_regular_players'] = home_stats.get('regular_players', 15)
        features['home_high_rated_players'] = home_stats.get('high_rated_players', 5)
        
        # Away team features
        features['away_avg_rating'] = away_stats.get('avg_rating', 6.5)
        features['away_total_goals'] = away_stats.get('total_goals', 0)
        features['away_total_assists'] = away_stats.get('total_assists', 0)
        features['away_avg_shots_per_game'] = away_stats.get('avg_shots_per_game', 10.0)
        features['away_avg_pass_success'] = away_stats.get('avg_pass_success', 0.8)
        features['away_total_cards'] = away_stats.get('total_cards', 0)
        features['away_squad_size'] = away_stats.get('squad_size', 25)
        features['away_regular_players'] = away_stats.get('regular_players', 15)
        features['away_high_rated_players'] = away_stats.get('high_rated_players', 5)
        
        # Differential features
        features['rating_diff'] = features['home_avg_rating'] - features['away_avg_rating']
        features['goals_diff'] = features['home_total_goals'] - features['away_total_goals']
        features['assists_diff'] = features['home_total_assists'] - features['away_total_assists']
        features['shots_diff'] = features['home_avg_shots_per_game'] - features['away_avg_shots_per_game']
        features['pass_success_diff'] = features['home_avg_pass_success'] - features['away_avg_pass_success']
        features['cards_diff'] = features['home_total_cards'] - features['away_total_cards']
        features['squad_quality_diff'] = features['home_high_rated_players'] - features['away_high_rated_players']
        
        return features
    
    def _create_player_features(self, home_players: pd.DataFrame, away_players: pd.DataFrame) -> Dict[str, Any]:
        """Create player-level aggregated features."""
        features = {}
        
        # Home team player features
        if not home_players.empty:
            features['home_top_player_rating'] = home_players['rating'].max() if 'rating' in home_players.columns else 7.0
            features['home_avg_player_rating'] = home_players['rating'].mean() if 'rating' in home_players.columns else 6.5
            features['home_top_scorer_goals'] = home_players['goals'].max() if 'goals' in home_players.columns else 0
            features['home_total_team_goals'] = home_players['goals'].sum() if 'goals' in home_players.columns else 0
            features['home_top_assister_assists'] = home_players['assists'].max() if 'assists' in home_players.columns else 0
            features['home_total_team_assists'] = home_players['assists'].sum() if 'assists' in home_players.columns else 0
            features['home_avg_shots_per_game'] = home_players['shots_per_game'].mean() if 'shots_per_game' in home_players.columns else 1.0
            features['home_disciplinary_record'] = (home_players['yellow'].sum() + home_players['red'].sum() * 2) if 'yellow' in home_players.columns else 0
            
            # Squad depth features
            features['home_experienced_players'] = len(home_players[home_players['apps_total'] >= 10]) if 'apps_total' in home_players.columns else 15
            features['home_key_players'] = len(home_players[home_players['rating'] >= 7.0]) if 'rating' in home_players.columns else 5
        else:
            # Default values when no player data
            features.update({
                'home_top_player_rating': 7.0,
                'home_avg_player_rating': 6.5,
                'home_top_scorer_goals': 5,
                'home_total_team_goals': 30,
                'home_top_assister_assists': 3,
                'home_total_team_assists': 20,
                'home_avg_shots_per_game': 1.0,
                'home_disciplinary_record': 30,
                'home_experienced_players': 15,
                'home_key_players': 5
            })
        
        # Away team player features
        if not away_players.empty:
            features['away_top_player_rating'] = away_players['rating'].max() if 'rating' in away_players.columns else 7.0
            features['away_avg_player_rating'] = away_players['rating'].mean() if 'rating' in away_players.columns else 6.5
            features['away_top_scorer_goals'] = away_players['goals'].max() if 'goals' in away_players.columns else 0
            features['away_total_team_goals'] = away_players['goals'].sum() if 'goals' in away_players.columns else 0
            features['away_top_assister_assists'] = away_players['assists'].max() if 'assists' in away_players.columns else 0
            features['away_total_team_assists'] = away_players['assists'].sum() if 'assists' in away_players.columns else 0
            features['away_avg_shots_per_game'] = away_players['shots_per_game'].mean() if 'shots_per_game' in away_players.columns else 1.0
            features['away_disciplinary_record'] = (away_players['yellow'].sum() + away_players['red'].sum() * 2) if 'yellow' in away_players.columns else 0
            
            # Squad depth features
            features['away_experienced_players'] = len(away_players[away_players['apps_total'] >= 10]) if 'apps_total' in away_players.columns else 15
            features['away_key_players'] = len(away_players[away_players['rating'] >= 7.0]) if 'rating' in away_players.columns else 5
        else:
            # Default values when no player data
            features.update({
                'away_top_player_rating': 7.0,
                'away_avg_player_rating': 6.5,
                'away_top_scorer_goals': 5,
                'away_total_team_goals': 30,
                'away_top_assister_assists': 3,
                'away_total_team_assists': 20,
                'away_avg_shots_per_game': 1.0,
                'away_disciplinary_record': 30,
                'away_experienced_players': 15,
                'away_key_players': 5
            })
        
        # Player differential features
        features['top_player_rating_diff'] = features['home_top_player_rating'] - features['away_top_player_rating']
        features['avg_player_rating_diff'] = features['home_avg_player_rating'] - features['away_avg_player_rating']
        features['top_scorer_diff'] = features['home_top_scorer_goals'] - features['away_top_scorer_goals']
        features['team_goals_diff'] = features['home_total_team_goals'] - features['away_total_team_goals']
        features['key_players_diff'] = features['home_key_players'] - features['away_key_players']
        features['experience_diff'] = features['home_experienced_players'] - features['away_experienced_players']
        
        return features
    
    def _create_advanced_features(self, home_stats: Dict, away_stats: Dict, 
                                home_players: pd.DataFrame, away_players: pd.DataFrame) -> Dict[str, Any]:
        """Create advanced derived features."""
        features = {}
        
        # Attack vs Defense matchup features
        home_attack_strength = (
            home_stats.get('total_goals', 0) * 0.4 +
            home_stats.get('avg_shots_per_game', 10) * 0.3 +
            home_stats.get('total_assists', 0) * 0.3
        )
        
        away_attack_strength = (
            away_stats.get('total_goals', 0) * 0.4 +
            away_stats.get('avg_shots_per_game', 10) * 0.3 +
            away_stats.get('total_assists', 0) * 0.3
        )
        
        # Defensive strength (inverse of goals conceded - we don't have this data, so use cards as proxy)
        home_defensive_strength = max(0, 100 - home_stats.get('total_cards', 0))
        away_defensive_strength = max(0, 100 - away_stats.get('total_cards', 0))
        
        features['home_attack_strength'] = home_attack_strength
        features['away_attack_strength'] = away_attack_strength
        features['home_defensive_strength'] = home_defensive_strength
        features['away_defensive_strength'] = away_defensive_strength
        
        # Matchup features
        features['home_attack_vs_away_defense'] = home_attack_strength / max(away_defensive_strength, 1)
        features['away_attack_vs_home_defense'] = away_attack_strength / max(home_defensive_strength, 1)
        
        # Squad balance features
        if not home_players.empty and 'rating' in home_players.columns:
            home_rating_std = home_players['rating'].std()
            features['home_squad_balance'] = 1 / (1 + home_rating_std) if pd.notna(home_rating_std) else 0.5
        else:
            features['home_squad_balance'] = 0.5
        
        if not away_players.empty and 'rating' in away_players.columns:
            away_rating_std = away_players['rating'].std()
            features['away_squad_balance'] = 1 / (1 + away_rating_std) if pd.notna(away_rating_std) else 0.5
        else:
            features['away_squad_balance'] = 0.5
        
        # Overall team strength
        features['home_overall_strength'] = (
            home_stats.get('avg_rating', 6.5) * 0.4 +
            (home_attack_strength / 50) * 0.3 +
            (home_defensive_strength / 100) * 0.3
        )
        
        features['away_overall_strength'] = (
            away_stats.get('avg_rating', 6.5) * 0.4 +
            (away_attack_strength / 50) * 0.3 +
            (away_defensive_strength / 100) * 0.3
        )
        
        features['overall_strength_diff'] = features['home_overall_strength'] - features['away_overall_strength']
        
        # Home advantage (constant for now, could be made dynamic)
        features['home_advantage'] = 0.1  # 10% boost for home team
        
        return features
    
    def _create_form_features(self, home_team_id: int, away_team_id: int, 
                            fixtures_df: pd.DataFrame) -> Dict[str, Any]:
        """Create form-based features from recent fixtures."""
        features = {}
        
        # This would require historical results data
        # For now, we'll create placeholder form features
        
        features['home_recent_form'] = 0.5  # Neutral form
        features['away_recent_form'] = 0.5  # Neutral form
        features['form_diff'] = 0.0
        
        # Head-to-head record (placeholder)
        features['h2h_home_wins'] = 0
        features['h2h_away_wins'] = 0
        features['h2h_draws'] = 0
        features['h2h_advantage'] = 0.0
        
        return features
    
    def create_betting_features(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Create features specifically for betting predictions."""
        betting_features = features.copy()
        
        # Expected goals features (simplified)
        home_xg = (
            features.get('home_attack_strength', 30) / 30 * 
            features.get('away_defensive_strength', 80) / 100 * 2.5
        )
        
        away_xg = (
            features.get('away_attack_strength', 30) / 30 * 
            features.get('home_defensive_strength', 80) / 100 * 2.0  # Away teams typically score less
        )
        
        betting_features['home_expected_goals'] = home_xg
        betting_features['away_expected_goals'] = away_xg
        betting_features['total_expected_goals'] = home_xg + away_xg
        
        # Win probabilities (simplified)
        strength_diff = features.get('overall_strength_diff', 0)
        home_advantage = features.get('home_advantage', 0.1)
        
        # Sigmoid function to convert strength difference to probability
        home_win_prob = 1 / (1 + np.exp(-(strength_diff + home_advantage) * 3))
        away_win_prob = 1 / (1 + np.exp((strength_diff + home_advantage) * 3))
        draw_prob = 1 - home_win_prob - away_win_prob
        
        # Normalize probabilities
        total_prob = home_win_prob + away_win_prob + draw_prob
        betting_features['home_win_prob'] = home_win_prob / total_prob
        betting_features['away_win_prob'] = away_win_prob / total_prob
        betting_features['draw_prob'] = draw_prob / total_prob
        
        # Over/Under features
        betting_features['over_2_5_prob'] = 1 / (1 + np.exp(-(betting_features['total_expected_goals'] - 2.5)))
        betting_features['over_1_5_prob'] = 1 / (1 + np.exp(-(betting_features['total_expected_goals'] - 1.5)))
        betting_features['over_3_5_prob'] = 1 / (1 + np.exp(-(betting_features['total_expected_goals'] - 3.5)))
        
        # Both teams to score
        btts_prob = (1 - np.exp(-home_xg)) * (1 - np.exp(-away_xg))
        betting_features['btts_prob'] = btts_prob
        
        return betting_features

def create_features_for_fixture(home_team_id: int, away_team_id: int,
                              players_df: pd.DataFrame, team_stats_df: pd.DataFrame,
                              fixtures_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """Main function to create features for a fixture."""
    engineer = FeatureEngineer()
    features = engineer.make_features(home_team_id, away_team_id, players_df, team_stats_df, fixtures_df)
    return engineer.create_betting_features(features)

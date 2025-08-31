"""
Prediction module for WhoScored pipeline.
"""

import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from . import utils, features

logger = utils.setup_logging(__name__)

class ModelPredictor:
    """Handles model loading and predictions."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.model_path = model_path or "model/model.pkl"
        self.feature_columns = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the trained model."""
        try:
            if Path(self.model_path).exists():
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                
                if isinstance(model_data, dict):
                    self.model = model_data.get('model')
                    self.feature_columns = model_data.get('feature_columns')
                else:
                    self.model = model_data
                
                logger.info(f"Loaded model from {self.model_path}")
            else:
                logger.warning(f"Model file not found at {self.model_path}, using stub predictor")
                self.model = None
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.model = None
    
    def predict_fixture(self, home_team_id: int, away_team_id: int, 
                       feature_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Predict outcome for a fixture."""
        
        if self.model is None:
            return self._stub_prediction(home_team_id, away_team_id, feature_dict)
        
        try:
            # Prepare features for model
            X = self._prepare_features(feature_dict)
            
            # Make prediction
            if hasattr(self.model, 'predict_proba'):
                # Classification model
                probabilities = self.model.predict_proba(X)[0]
                
                # Assuming classes are [away_win, draw, home_win] or similar
                if len(probabilities) == 3:
                    away_win_prob = probabilities[0]
                    draw_prob = probabilities[1]
                    home_win_prob = probabilities[2]
                else:
                    # Binary classification (home win vs not home win)
                    home_win_prob = probabilities[1] if len(probabilities) == 2 else probabilities[0]
                    away_win_prob = (1 - home_win_prob) * 0.6  # Rough estimate
                    draw_prob = (1 - home_win_prob) * 0.4
            
            elif hasattr(self.model, 'predict'):
                # Regression model or other
                prediction = self.model.predict(X)[0]
                
                # Convert single prediction to probabilities
                if prediction > 0.5:
                    home_win_prob = min(0.8, 0.33 + prediction * 0.4)
                    away_win_prob = max(0.1, 0.33 - prediction * 0.2)
                    draw_prob = 1 - home_win_prob - away_win_prob
                else:
                    away_win_prob = min(0.8, 0.33 + (1-prediction) * 0.4)
                    home_win_prob = max(0.1, 0.33 - (1-prediction) * 0.2)
                    draw_prob = 1 - home_win_prob - away_win_prob
            
            else:
                return self._stub_prediction(home_team_id, away_team_id, feature_dict)
            
            # Normalize probabilities
            total = home_win_prob + draw_prob + away_win_prob
            home_win_prob /= total
            draw_prob /= total
            away_win_prob /= total
            
            # Predict scoreline based on expected goals
            home_xg = feature_dict.get('home_expected_goals', 1.5)
            away_xg = feature_dict.get('away_expected_goals', 1.2)
            
            home_goals = max(0, int(np.round(home_xg)))
            away_goals = max(0, int(np.round(away_xg)))
            
            return {
                'home_win_prob': round(home_win_prob, 3),
                'draw_prob': round(draw_prob, 3),
                'away_win_prob': round(away_win_prob, 3),
                'scoreline': f"{home_goals}-{away_goals}",
                'home_expected_goals': round(home_xg, 2),
                'away_expected_goals': round(away_xg, 2),
                'confidence': self._calculate_confidence(home_win_prob, draw_prob, away_win_prob)
            }
            
        except Exception as e:
            logger.error(f"Error in model prediction: {e}")
            return self._stub_prediction(home_team_id, away_team_id, feature_dict)
    
    def _prepare_features(self, feature_dict: Dict[str, Any]) -> np.ndarray:
        """Prepare features for model input."""
        
        if self.feature_columns is not None:
            # Use predefined feature columns
            feature_values = []
            for col in self.feature_columns:
                feature_values.append(feature_dict.get(col, 0))
            return np.array(feature_values).reshape(1, -1)
        
        else:
            # Use all numeric features
            numeric_features = []
            for key, value in feature_dict.items():
                if isinstance(value, (int, float)) and not np.isnan(value):
                    numeric_features.append(value)
            
            return np.array(numeric_features).reshape(1, -1)
    
    def _stub_prediction(self, home_team_id: int, away_team_id: int, 
                        feature_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Generate stub predictions when no real model is available."""
        
        # Use feature-based heuristics for realistic predictions
        overall_strength_diff = feature_dict.get('overall_strength_diff', 0)
        home_advantage = feature_dict.get('home_advantage', 0.1)
        
        # Base probabilities
        if overall_strength_diff > 0.2:
            # Home team significantly stronger
            home_win_prob = 0.55 + min(0.25, overall_strength_diff * 0.5)
            away_win_prob = 0.20
            draw_prob = 1 - home_win_prob - away_win_prob
        elif overall_strength_diff < -0.2:
            # Away team significantly stronger
            away_win_prob = 0.45 + min(0.25, abs(overall_strength_diff) * 0.5)
            home_win_prob = 0.25
            draw_prob = 1 - home_win_prob - away_win_prob
        else:
            # Evenly matched
            home_win_prob = 0.40 + home_advantage
            away_win_prob = 0.30
            draw_prob = 0.30 - home_advantage
        
        # Ensure probabilities sum to 1
        total = home_win_prob + draw_prob + away_win_prob
        home_win_prob /= total
        draw_prob /= total
        away_win_prob /= total
        
        # Expected goals
        home_xg = feature_dict.get('home_expected_goals', 1.5)
        away_xg = feature_dict.get('away_expected_goals', 1.2)
        
        # Scoreline prediction
        home_goals = max(0, int(np.round(home_xg)))
        away_goals = max(0, int(np.round(away_xg)))
        
        return {
            'home_win_prob': round(home_win_prob, 3),
            'draw_prob': round(draw_prob, 3),
            'away_win_prob': round(away_win_prob, 3),
            'scoreline': f"{home_goals}-{away_goals}",
            'home_expected_goals': round(home_xg, 2),
            'away_expected_goals': round(away_xg, 2),
            'confidence': self._calculate_confidence(home_win_prob, draw_prob, away_win_prob),
            'model_type': 'stub'
        }
    
    def _calculate_confidence(self, home_prob: float, draw_prob: float, away_prob: float) -> float:
        """Calculate prediction confidence based on probability distribution."""
        
        # Higher confidence when one outcome is much more likely
        max_prob = max(home_prob, draw_prob, away_prob)
        
        # Entropy-based confidence (lower entropy = higher confidence)
        probs = [home_prob, draw_prob, away_prob]
        entropy = -sum(p * np.log(p + 1e-10) for p in probs if p > 0)
        max_entropy = np.log(3)  # Maximum entropy for 3 outcomes
        
        confidence = 1 - (entropy / max_entropy)
        
        return round(confidence, 3)

class PlayerPropPredictor:
    """Predicts individual player props using WhoScored data."""
    
    def __init__(self):
        self.prop_models = {}
    
    def predict_player_props(self, player_data: Dict[str, Any], 
                           match_context: Dict[str, Any]) -> Dict[str, Any]:
        """Predict player props based on WhoScored statistics."""
        
        props = {}
        
        # Goals prediction
        goals_per_game = player_data.get('goals_per_game', 0)
        if goals_per_game > 0:
            # Adjust for match context
            opponent_defensive_strength = match_context.get('opponent_defensive_strength', 80) / 100
            goals_expected = goals_per_game * (2 - opponent_defensive_strength)  # Easier opponents = more goals
            
            props['anytime_goalscorer_prob'] = min(0.8, 1 - np.exp(-goals_expected))
            props['goals_over_0_5_prob'] = props['anytime_goalscorer_prob']
            props['goals_over_1_5_prob'] = min(0.4, goals_expected * 0.3) if goals_expected > 0.5 else 0
        
        # Assists prediction
        assists_per_game = player_data.get('assists_per_game', 0)
        if assists_per_game > 0:
            team_attack_strength = match_context.get('team_attack_strength', 30) / 30
            assists_expected = assists_per_game * team_attack_strength
            
            props['assists_over_0_5_prob'] = min(0.6, 1 - np.exp(-assists_expected * 2))
        
        # Shots prediction
        shots_per_game = player_data.get('shots_per_game', 0)
        if shots_per_game > 0:
            props['shots_over_1_5_prob'] = min(0.8, 1 - np.exp(-shots_per_game * 0.7))
            props['shots_over_2_5_prob'] = min(0.6, 1 - np.exp(-shots_per_game * 0.4))
            props['shots_on_target_over_0_5_prob'] = min(0.7, shots_per_game * 0.4)
        
        # Cards prediction
        yellow_per_game = player_data.get('yellow_per_game', 0)
        if yellow_per_game > 0:
            props['yellow_card_prob'] = min(0.5, yellow_per_game * 2)
        
        # Pass success (for defensive players)
        pass_success = player_data.get('pass_success', 0)
        if pass_success > 0.8:  # High pass success rate
            props['passes_completed_over_30_prob'] = 0.7
            props['passes_completed_over_50_prob'] = 0.4
        
        return props

def predict_fixture(home_team_id: int, away_team_id: int, 
                   players_df: pd.DataFrame, team_stats_df: pd.DataFrame,
                   fixtures_df: Optional[pd.DataFrame] = None,
                   model_path: Optional[str] = None) -> Dict[str, Any]:
    """Main function to predict fixture outcome."""
    
    # Create features
    feature_dict = features.create_features_for_fixture(
        home_team_id, away_team_id, players_df, team_stats_df, fixtures_df
    )
    
    # Make prediction
    predictor = ModelPredictor(model_path)
    prediction = predictor.predict_fixture(home_team_id, away_team_id, feature_dict)
    
    # Add feature information
    prediction['features_used'] = len(feature_dict)
    prediction['home_team_id'] = home_team_id
    prediction['away_team_id'] = away_team_id
    
    return prediction

def predict_player_props_for_match(home_team_id: int, away_team_id: int,
                                 players_df: pd.DataFrame, team_stats_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Predict player props for all players in a match."""
    
    prop_predictor = PlayerPropPredictor()
    all_props = []
    
    # Get match context
    home_stats = team_stats_df[team_stats_df['team_id'] == home_team_id]
    away_stats = team_stats_df[team_stats_df['team_id'] == away_team_id]
    
    home_context = {
        'opponent_defensive_strength': away_stats.iloc[0].get('avg_rating', 6.5) * 10 if not away_stats.empty else 65,
        'team_attack_strength': home_stats.iloc[0].get('total_goals', 30) if not home_stats.empty else 30
    }
    
    away_context = {
        'opponent_defensive_strength': home_stats.iloc[0].get('avg_rating', 6.5) * 10 if not home_stats.empty else 65,
        'team_attack_strength': away_stats.iloc[0].get('total_goals', 30) if not away_stats.empty else 30
    }
    
    # Predict for home team players
    home_players = players_df[players_df['team_id'] == home_team_id]
    for _, player in home_players.iterrows():
        if player.get('apps_total', 0) >= 5:  # Only regular players
            player_props = prop_predictor.predict_player_props(player.to_dict(), home_context)
            if player_props:  # Only add if there are predictions
                player_props.update({
                    'player_id': player['player_id'],
                    'player_name': player['player_name'],
                    'team_id': home_team_id,
                    'is_home': True
                })
                all_props.append(player_props)
    
    # Predict for away team players
    away_players = players_df[players_df['team_id'] == away_team_id]
    for _, player in away_players.iterrows():
        if player.get('apps_total', 0) >= 5:  # Only regular players
            player_props = prop_predictor.predict_player_props(player.to_dict(), away_context)
            if player_props:  # Only add if there are predictions
                player_props.update({
                    'player_id': player['player_id'],
                    'player_name': player['player_name'],
                    'team_id': away_team_id,
                    'is_home': False
                })
                all_props.append(player_props)
    
    return all_props

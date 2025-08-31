"""
Integration module to connect WhoScored pipeline with existing Bettor system.
"""

import asyncio
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
from datetime import datetime

# Import WhoScored pipeline
from ws_pipeline import main as ws_main
from ws_pipeline import predict, features, storage, utils as ws_utils
from ws_pipeline.transform import clean_and_transform_data

# Import existing system
from simple_ml_model import calculate_final_score

class WSIntegration:
    """Integrates WhoScored data with existing Bettor system."""
    
    def __init__(self):
        self.ws_pipeline = ws_main.WSPipeline()
        self.cache = storage.get_cache()
        self.storage = storage.get_storage()
    
    async def get_whoscored_data_for_match(self, home_team: str, away_team: str) -> Optional[Dict[str, Any]]:
        """Get WhoScored data for a specific match."""
        try:
            # First scrape today's fixtures
            fixtures_file = await self.ws_pipeline.run_fixtures_scrape("today")
            if not fixtures_file:
                return None
            
            # Load fixtures and find the match
            fixtures_df = pd.read_csv(fixtures_file)
            match_row = fixtures_df[
                (fixtures_df['home_team_name'].str.contains(home_team, case=False, na=False)) &
                (fixtures_df['away_team_name'].str.contains(away_team, case=False, na=False))
            ]
            
            if match_row.empty:
                print(f"❌ Match {home_team} vs {away_team} not found in WhoScored fixtures")
                return None
            
            match = match_row.iloc[0]
            home_team_id = match.get('home_team_id')
            away_team_id = match.get('away_team_id')
            
            if pd.isna(home_team_id) or pd.isna(away_team_id):
                print(f"❌ Missing team IDs for {home_team} vs {away_team}")
                return None
            
            # Scrape team data
            team_files = await self.ws_pipeline.run_teams_scrape(fixtures_file)
            
            if not team_files:
                print(f"❌ No team data available for {home_team} vs {away_team}")
                return None
            
            # Clean and transform data
            fixtures_df, players_df, team_stats_df = clean_and_transform_data(fixtures_file, team_files)
            
            # Generate features and prediction
            feature_dict = features.create_features_for_fixture(
                int(home_team_id), int(away_team_id), players_df, team_stats_df, fixtures_df
            )
            
            prediction = predict.predict_fixture(
                int(home_team_id), int(away_team_id), players_df, team_stats_df, fixtures_df
            )
            
            # Get player props
            player_props = predict.predict_player_props_for_match(
                int(home_team_id), int(away_team_id), players_df, team_stats_df
            )
            
            return {
                'match_info': {
                    'home_team': match['home_team_name'],
                    'away_team': match['away_team_name'],
                    'kickoff_utc': match['kickoff_utc'],
                    'competition': match['competition']
                },
                'features': feature_dict,
                'prediction': prediction,
                'player_props': player_props,
                'players_data': players_df[
                    (players_df['team_id'] == int(home_team_id)) | 
                    (players_df['team_id'] == int(away_team_id))
                ].to_dict('records'),
                'team_stats': team_stats_df[
                    (team_stats_df['team_id'] == int(home_team_id)) | 
                    (team_stats_df['team_id'] == int(away_team_id))
                ].to_dict('records')
            }
            
        except Exception as e:
            print(f"❌ Error getting WhoScored data: {e}")
            return None
    
    def convert_ws_to_bettor_format(self, ws_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert WhoScored data to existing Bettor analysis format."""
        if not ws_data:
            return []
        
        analysis_entries = []
        match_info = ws_data['match_info']
        prediction = ws_data['prediction']
        player_props = ws_data['player_props']
        
        # Add match-level bets
        match_id = f"ws_{match_info['home_team']}_{match_info['away_team']}"
        
        # Home Win bet
        if prediction.get('home_win_prob', 0) > 0.4:
            analysis_entries.append({
                'match_id': match_id,
                'home_team': match_info['home_team'],
                'away_team': match_info['away_team'],
                'player_name': 'Match Result',
                'prop_type': 'Home Win',
                'rate_per_game': prediction['home_win_prob'],
                'final_score': prediction['home_win_prob'] * 100,
                'model_prob': prediction['home_win_prob'],
                'confidence': prediction.get('confidence', 0.5),
                'source': 'WhoScored'
            })
        
        # Over/Under bets
        total_xg = prediction.get('home_expected_goals', 0) + prediction.get('away_expected_goals', 0)
        if total_xg > 2.3:
            analysis_entries.append({
                'match_id': match_id,
                'home_team': match_info['home_team'],
                'away_team': match_info['away_team'],
                'player_name': 'Match Total',
                'prop_type': 'Over 2.5 Goals',
                'rate_per_game': total_xg / 3.5,  # Normalize to 0-1
                'final_score': min(95, total_xg * 25),
                'model_prob': min(0.8, total_xg / 4),
                'confidence': 0.7,
                'source': 'WhoScored'
            })
        
        # Player props
        for prop in player_props:
            player_name = prop.get('player_name', 'Unknown')
            
            # Goals
            if 'anytime_goalscorer_prob' in prop and prop['anytime_goalscorer_prob'] > 0.15:
                analysis_entries.append({
                    'match_id': match_id,
                    'home_team': match_info['home_team'],
                    'away_team': match_info['away_team'],
                    'player_name': player_name,
                    'prop_type': 'Anytime Goalscorer',
                    'rate_per_game': prop['anytime_goalscorer_prob'],
                    'final_score': prop['anytime_goalscorer_prob'] * 100,
                    'model_prob': prop['anytime_goalscorer_prob'],
                    'confidence': 0.6,
                    'source': 'WhoScored'
                })
            
            # Assists
            if 'assists_over_0_5_prob' in prop and prop['assists_over_0_5_prob'] > 0.2:
                analysis_entries.append({
                    'match_id': match_id,
                    'home_team': match_info['home_team'],
                    'away_team': match_info['away_team'],
                    'player_name': player_name,
                    'prop_type': 'Assists Over 0.5',
                    'rate_per_game': prop['assists_over_0_5_prob'],
                    'final_score': prop['assists_over_0_5_prob'] * 100,
                    'model_prob': prop['assists_over_0_5_prob'],
                    'confidence': 0.5,
                    'source': 'WhoScored'
                })
            
            # Shots
            if 'shots_over_1_5_prob' in prop and prop['shots_over_1_5_prob'] > 0.3:
                analysis_entries.append({
                    'match_id': match_id,
                    'home_team': match_info['home_team'],
                    'away_team': match_info['away_team'],
                    'player_name': player_name,
                    'prop_type': 'Shots Over 1.5',
                    'rate_per_game': prop['shots_over_1_5_prob'],
                    'final_score': prop['shots_over_1_5_prob'] * 100,
                    'model_prob': prop['shots_over_1_5_prob'],
                    'confidence': 0.6,
                    'source': 'WhoScored'
                })
        
        return analysis_entries
    
    def enhance_existing_analysis_with_ws(self, existing_analysis: List[Dict], 
                                        home_team: str, away_team: str) -> List[Dict]:
        """Enhance existing analysis with WhoScored data."""
        try:
            # Get WhoScored data
            ws_data = asyncio.run(self.get_whoscored_data_for_match(home_team, away_team))
            
            if not ws_data:
                print(f"⚠️ No WhoScored data available for {home_team} vs {away_team}")
                return existing_analysis
            
            # Convert to Bettor format
            ws_analysis = self.convert_ws_to_bettor_format(ws_data)
            
            # Merge with existing analysis
            enhanced_analysis = existing_analysis.copy()
            enhanced_analysis.extend(ws_analysis)
            
            print(f"✅ Enhanced analysis with {len(ws_analysis)} WhoScored opportunities")
            return enhanced_analysis
            
        except Exception as e:
            print(f"❌ Error enhancing analysis with WhoScored: {e}")
            return existing_analysis
    
    def get_ws_player_stats(self, player_name: str, team_name: str) -> Optional[Dict[str, Any]]:
        """Get individual player statistics from WhoScored data."""
        try:
            # Try to find cached team data
            team_files = list(Path("ws_pipeline/data").glob("team_*_players.csv"))
            
            for team_file in team_files:
                try:
                    players_df = pd.read_csv(team_file)
                    
                    # Find player by name (fuzzy match)
                    player_matches = players_df[
                        players_df['player_name'].str.contains(player_name, case=False, na=False)
                    ]
                    
                    if not player_matches.empty:
                        player_data = player_matches.iloc[0].to_dict()
                        
                        # Convert to per-game stats if needed
                        apps = player_data.get('apps_total', 1) or 1
                        
                        return {
                            'player_name': player_data.get('player_name'),
                            'team_id': player_data.get('team_id'),
                            'goals_per_game': player_data.get('goals', 0) / apps,
                            'assists_per_game': player_data.get('assists', 0) / apps,
                            'shots_per_game': player_data.get('shots_per_game', 0),
                            'yellow_cards_per_game': player_data.get('yellow', 0) / apps,
                            'rating': player_data.get('rating', 6.5),
                            'pass_success': player_data.get('pass_success', 0.8),
                            'apps_total': apps,
                            'source': 'WhoScored'
                        }
                        
                except Exception as e:
                    continue
            
            return None
            
        except Exception as e:
            print(f"❌ Error getting WhoScored player stats: {e}")
            return None

# Global integration instance
ws_integration = WSIntegration()

def get_whoscored_analysis(home_team: str, away_team: str) -> List[Dict[str, Any]]:
    """Get betting analysis using WhoScored data."""
    try:
        ws_data = asyncio.run(ws_integration.get_whoscored_data_for_match(home_team, away_team))
        if ws_data:
            return ws_integration.convert_ws_to_bettor_format(ws_data)
        return []
    except Exception as e:
        print(f"❌ Error in WhoScored analysis: {e}")
        return []

def enhance_analysis_with_whoscored(existing_analysis: List[Dict], 
                                  home_team: str, away_team: str) -> List[Dict]:
    """Enhance existing analysis with WhoScored data."""
    return ws_integration.enhance_existing_analysis_with_ws(existing_analysis, home_team, away_team)

def get_whoscored_player_stats(player_name: str, team_name: str = None) -> Optional[Dict[str, Any]]:
    """Get player statistics from WhoScored."""
    return ws_integration.get_ws_player_stats(player_name, team_name or "")

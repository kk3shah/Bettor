"""
Data transformation and cleaning for WhoScored pipeline.
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple

from . import utils

logger = utils.setup_logging(__name__)

class DataTransformer:
    """Handles data cleaning and transformation."""
    
    def clean_fixtures_data(self, fixtures_df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate fixtures data."""
        logger.info(f"Cleaning {len(fixtures_df)} fixtures")
        
        # Ensure required columns exist
        required_cols = ['home_team_name', 'away_team_name', 'kickoff_utc', 'competition']
        for col in required_cols:
            if col not in fixtures_df.columns:
                fixtures_df[col] = None
        
        # Clean team names
        fixtures_df['home_team_name'] = fixtures_df['home_team_name'].astype(str).str.strip()
        fixtures_df['away_team_name'] = fixtures_df['away_team_name'].astype(str).str.strip()
        
        # Parse kickoff times
        fixtures_df['kickoff_utc'] = pd.to_datetime(fixtures_df['kickoff_utc'], errors='coerce')
        
        # Remove invalid fixtures
        initial_count = len(fixtures_df)
        fixtures_df = fixtures_df.dropna(subset=['home_team_name', 'away_team_name', 'kickoff_utc'])
        fixtures_df = fixtures_df[fixtures_df['home_team_name'] != fixtures_df['away_team_name']]
        
        logger.info(f"Cleaned fixtures: {initial_count} -> {len(fixtures_df)} (removed {initial_count - len(fixtures_df)} invalid)")
        
        return fixtures_df
    
    def clean_players_data(self, players_df: pd.DataFrame) -> pd.DataFrame:
        """Clean and transform player statistics data."""
        logger.info(f"Cleaning {len(players_df)} player records")
        
        # Ensure required columns exist
        required_cols = ['player_name', 'team_id', 'season']
        for col in required_cols:
            if col not in players_df.columns:
                players_df[col] = None
        
        # Clean player names
        players_df['player_name'] = players_df['player_name'].astype(str).str.strip()
        
        # Clean numeric columns
        numeric_cols = [
            'age', 'apps_total', 'apps_sub', 'minutes', 'goals', 'assists',
            'yellow', 'red', 'shots_per_game', 'pass_success', 'aerials_won',
            'motm', 'rating'
        ]
        
        for col in numeric_cols:
            if col in players_df.columns:
                players_df[col] = pd.to_numeric(players_df[col], errors='coerce')
        
        # Handle special transformations
        if 'positions' in players_df.columns:
            players_df['positions'] = players_df['positions'].fillna('')
            players_df['positions_list'] = players_df['positions'].apply(self._parse_positions_string)
        
        # Calculate derived metrics
        players_df = self._calculate_derived_metrics(players_df)
        
        # Remove invalid players
        initial_count = len(players_df)
        players_df = players_df.dropna(subset=['player_name', 'team_id'])
        players_df = players_df[players_df['player_name'] != '']
        
        logger.info(f"Cleaned players: {initial_count} -> {len(players_df)} (removed {initial_count - len(players_df)} invalid)")
        
        return players_df
    
    def _parse_positions_string(self, pos_str: str) -> List[str]:
        """Parse positions string into list."""
        if not pos_str or pos_str == '':
            return []
        
        return [p.strip() for p in pos_str.split(',') if p.strip()]
    
    def _calculate_derived_metrics(self, players_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate derived metrics from base statistics."""
        
        # Goals per game
        if 'goals' in players_df.columns and 'apps_total' in players_df.columns:
            players_df['goals_per_game'] = players_df['goals'] / players_df['apps_total'].replace(0, 1)
            players_df['goals_per_game'] = players_df['goals_per_game'].fillna(0)
        
        # Assists per game
        if 'assists' in players_df.columns and 'apps_total' in players_df.columns:
            players_df['assists_per_game'] = players_df['assists'] / players_df['apps_total'].replace(0, 1)
            players_df['assists_per_game'] = players_df['assists_per_game'].fillna(0)
        
        # Minutes per game
        if 'minutes' in players_df.columns and 'apps_total' in players_df.columns:
            players_df['minutes_per_game'] = players_df['minutes'] / players_df['apps_total'].replace(0, 1)
            players_df['minutes_per_game'] = players_df['minutes_per_game'].fillna(0)
        
        # Cards per game
        if 'yellow' in players_df.columns and 'apps_total' in players_df.columns:
            players_df['yellow_per_game'] = players_df['yellow'] / players_df['apps_total'].replace(0, 1)
            players_df['yellow_per_game'] = players_df['yellow_per_game'].fillna(0)
        
        if 'red' in players_df.columns and 'apps_total' in players_df.columns:
            players_df['red_per_game'] = players_df['red'] / players_df['apps_total'].replace(0, 1)
            players_df['red_per_game'] = players_df['red_per_game'].fillna(0)
        
        # Shots per game (if not already present)
        if 'shots_per_game' not in players_df.columns:
            players_df['shots_per_game'] = 0.0
        
        # Pass success rate (ensure it's in 0-1 range)
        if 'pass_success' in players_df.columns:
            # If values are > 1, assume they're percentages and convert
            mask = players_df['pass_success'] > 1
            players_df.loc[mask, 'pass_success'] = players_df.loc[mask, 'pass_success'] / 100
            players_df['pass_success'] = players_df['pass_success'].fillna(0)
        
        return players_df
    
    def aggregate_team_stats(self, players_df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate player stats to team level."""
        logger.info("Aggregating team statistics from player data")
        
        # Group by team
        team_stats = players_df.groupby('team_id').agg({
            'goals': 'sum',
            'assists': 'sum',
            'shots_per_game': 'mean',
            'pass_success': 'mean',
            'rating': 'mean',
            'yellow': 'sum',
            'red': 'sum',
            'motm': 'sum',
            'apps_total': 'sum',
            'minutes': 'sum'
        }).reset_index()
        
        # Calculate team-level derived metrics
        team_stats['avg_rating'] = team_stats['rating']
        team_stats['total_goals'] = team_stats['goals']
        team_stats['total_assists'] = team_stats['assists']
        team_stats['avg_shots_per_game'] = team_stats['shots_per_game']
        team_stats['avg_pass_success'] = team_stats['pass_success']
        team_stats['total_cards'] = team_stats['yellow'] + team_stats['red']
        team_stats['total_motm'] = team_stats['motm']
        
        # Calculate squad depth metrics
        squad_depth = players_df.groupby('team_id').agg({
            'player_id': 'count',
            'apps_total': lambda x: (x > 5).sum(),  # Players with 5+ appearances
            'rating': lambda x: (x >= 7.0).sum()   # Players with 7.0+ rating
        }).reset_index()
        
        squad_depth.columns = ['team_id', 'squad_size', 'regular_players', 'high_rated_players']
        
        # Merge team stats with squad depth
        team_stats = team_stats.merge(squad_depth, on='team_id', how='left')
        
        logger.info(f"Generated team statistics for {len(team_stats)} teams")
        
        return team_stats
    
    def normalize_team_names(self, fixtures_df: pd.DataFrame, players_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Normalize team names between fixtures and players data."""
        logger.info("Normalizing team names between datasets")
        
        # Get unique team names from both datasets
        fixture_teams = set(fixtures_df['home_team_name'].unique()) | set(fixtures_df['away_team_name'].unique())
        
        if 'team_id' in players_df.columns:
            # Create team name mapping from players data if team_id exists
            team_mapping = {}
            
            # This is a simplified approach - in practice, you'd need more sophisticated matching
            # For now, we'll assume team names are already consistent
            
            logger.info(f"Found {len(fixture_teams)} unique teams in fixtures")
        
        return fixtures_df, players_df
    
    def prepare_model_data(self, fixtures_df: pd.DataFrame, players_df: pd.DataFrame, 
                          team_stats_df: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for model training/prediction."""
        logger.info("Preparing model-ready dataset")
        
        model_data = []
        
        for _, fixture in fixtures_df.iterrows():
            try:
                home_team = fixture['home_team_name']
                away_team = fixture['away_team_name']
                
                # Get team IDs if available
                home_team_id = fixture.get('home_team_id')
                away_team_id = fixture.get('away_team_id')
                
                if pd.isna(home_team_id) or pd.isna(away_team_id):
                    # Try to find team IDs from players data
                    home_team_id = self._find_team_id_by_name(home_team, players_df)
                    away_team_id = self._find_team_id_by_name(away_team, players_df)
                
                if home_team_id is None or away_team_id is None:
                    logger.warning(f"Could not find team IDs for {home_team} vs {away_team}")
                    continue
                
                # Get team statistics
                home_stats = team_stats_df[team_stats_df['team_id'] == home_team_id]
                away_stats = team_stats_df[team_stats_df['team_id'] == away_team_id]
                
                if home_stats.empty or away_stats.empty:
                    logger.warning(f"Missing team stats for {home_team} vs {away_team}")
                    continue
                
                home_stats = home_stats.iloc[0]
                away_stats = away_stats.iloc[0]
                
                # Create feature vector
                features = {
                    'fixture_id': f"{home_team_id}_{away_team_id}_{fixture['kickoff_utc']}",
                    'home_team_id': home_team_id,
                    'away_team_id': away_team_id,
                    'home_team_name': home_team,
                    'away_team_name': away_team,
                    'kickoff_utc': fixture['kickoff_utc'],
                    'competition': fixture['competition'],
                    
                    # Home team features
                    'home_avg_rating': home_stats.get('avg_rating', 0),
                    'home_total_goals': home_stats.get('total_goals', 0),
                    'home_total_assists': home_stats.get('total_assists', 0),
                    'home_avg_shots_per_game': home_stats.get('avg_shots_per_game', 0),
                    'home_avg_pass_success': home_stats.get('avg_pass_success', 0),
                    'home_total_cards': home_stats.get('total_cards', 0),
                    'home_squad_size': home_stats.get('squad_size', 0),
                    'home_regular_players': home_stats.get('regular_players', 0),
                    'home_high_rated_players': home_stats.get('high_rated_players', 0),
                    
                    # Away team features
                    'away_avg_rating': away_stats.get('avg_rating', 0),
                    'away_total_goals': away_stats.get('total_goals', 0),
                    'away_total_assists': away_stats.get('total_assists', 0),
                    'away_avg_shots_per_game': away_stats.get('avg_shots_per_game', 0),
                    'away_avg_pass_success': away_stats.get('avg_pass_success', 0),
                    'away_total_cards': away_stats.get('total_cards', 0),
                    'away_squad_size': away_stats.get('squad_size', 0),
                    'away_regular_players': away_stats.get('regular_players', 0),
                    'away_high_rated_players': away_stats.get('high_rated_players', 0),
                    
                    # Differential features
                    'rating_diff': home_stats.get('avg_rating', 0) - away_stats.get('avg_rating', 0),
                    'goals_diff': home_stats.get('total_goals', 0) - away_stats.get('total_goals', 0),
                    'shots_diff': home_stats.get('avg_shots_per_game', 0) - away_stats.get('avg_shots_per_game', 0),
                    'pass_success_diff': home_stats.get('avg_pass_success', 0) - away_stats.get('avg_pass_success', 0),
                }
                
                model_data.append(features)
                
            except Exception as e:
                logger.warning(f"Error preparing model data for fixture: {e}")
                continue
        
        model_df = pd.DataFrame(model_data)
        logger.info(f"Prepared model data for {len(model_df)} fixtures")
        
        return model_df
    
    def _find_team_id_by_name(self, team_name: str, players_df: pd.DataFrame) -> Optional[int]:
        """Find team ID by team name from players data."""
        # This is a simplified approach - you'd need more sophisticated matching in practice
        # For now, return None as we don't have a reliable way to map names to IDs
        return None

def clean_and_transform_data(fixtures_file: str, players_files: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Main function to clean and transform all data."""
    transformer = DataTransformer()
    
    # Load and clean fixtures
    fixtures_df = utils.load_csv(fixtures_file)
    if fixtures_df is None:
        raise ValueError(f"Could not load fixtures from {fixtures_file}")
    
    fixtures_df = transformer.clean_fixtures_data(fixtures_df)
    
    # Load and clean all player data
    all_players = []
    for players_file in players_files:
        players_df = utils.load_csv(players_file)
        if players_df is not None:
            all_players.append(players_df)
    
    if not all_players:
        raise ValueError("No player data files could be loaded")
    
    players_df = pd.concat(all_players, ignore_index=True)
    players_df = transformer.clean_players_data(players_df)
    
    # Generate team statistics
    team_stats_df = transformer.aggregate_team_stats(players_df)
    
    # Normalize team names
    fixtures_df, players_df = transformer.normalize_team_names(fixtures_df, players_df)
    
    return fixtures_df, players_df, team_stats_df

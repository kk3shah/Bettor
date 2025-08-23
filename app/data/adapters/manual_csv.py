"""Manual CSV data adapter for stats import."""
import pandas as pd
from typing import Optional, List, Dict, Any
from pathlib import Path
import os

from .base import StatsAdapter, DataAdapterError
from app.schemas import PlayerStats, TeamStats


class ManualCSVAdapter(StatsAdapter):
    """Adapter for manually imported CSV stats data."""
    
    def __init__(self, data_dir: str = "app/data/input"):
        self.data_dir = Path(data_dir)
        self._player_stats: Optional[pd.DataFrame] = None
        self._team_stats: Optional[pd.DataFrame] = None
        self._load_data()
    
    def _load_data(self):
        """Load CSV data from the input directory."""
        try:
            # Load player stats
            player_file = self.data_dir / "sample_player_stats.csv"
            if player_file.exists():
                self._player_stats = pd.read_csv(player_file)
                print(f"Loaded {len(self._player_stats)} player records")
            
            # Load team stats
            team_file = self.data_dir / "sample_team_stats.csv"
            if team_file.exists():
                self._team_stats = pd.read_csv(team_file)
                print(f"Loaded {len(self._team_stats)} team records")
                
        except Exception as e:
            print(f"Warning: Could not load CSV data: {e}")
    
    def load_from_dataframes(self, player_df: pd.DataFrame, team_df: pd.DataFrame):
        """Load data from pandas DataFrames (for UI uploads)."""
        self._player_stats = player_df.copy()
        self._team_stats = team_df.copy()
    
    def get_player_stats(self, player_name: str, team: str) -> Optional[PlayerStats]:
        """Get stats for a specific player."""
        if self._player_stats is None:
            return None
        
        # Filter by both player name and team
        matches = self._player_stats[
            (self._player_stats['player_name'].str.lower() == player_name.lower()) & 
            (self._player_stats['team'].str.lower() == team.lower())
        ]
        
        if matches.empty:
            return None
        
        row = matches.iloc[0]
        return PlayerStats(
            player_name=row['player_name'],
            team=row['team'],
            minutes_per_app=float(row['minutes_per_app']),
            shots_pg=float(row['shots_pg']),
            sot_pg=float(row['sot_pg']),
            fouls_pg=float(row['fouls_pg']),
            passes_pg=float(row['passes_pg']),
            yc_pg=float(row['yc_pg']),
            apps=int(row['apps'])
        )
    
    def get_team_stats(self, team: str) -> Optional[TeamStats]:
        """Get stats for a specific team."""
        if self._team_stats is None:
            return None
        
        matches = self._team_stats[
            self._team_stats['team'].str.lower() == team.lower()
        ]
        
        if matches.empty:
            return None
        
        row = matches.iloc[0]
        return TeamStats(
            team=row['team'],
            goals_for_pg=float(row['goals_for_pg']),
            goals_against_pg=float(row['goals_against_pg']),
            shots_allowed_pg=float(row['shots_allowed_pg']),
            cards_pg=float(row['cards_pg'])
        )
    
    def find_player(self, team: str, player_name: str) -> Optional[PlayerStats]:
        """Find a player with exact matching (fuzzy matching could be added later)."""
        return self.get_player_stats(player_name, team)
    
    def get_all_players(self) -> List[PlayerStats]:
        """Get all available player stats."""
        if self._player_stats is None:
            return []
        
        players = []
        for _, row in self._player_stats.iterrows():
            players.append(PlayerStats(
                player_name=row['player_name'],
                team=row['team'],
                minutes_per_app=float(row['minutes_per_app']),
                shots_pg=float(row['shots_pg']),
                sot_pg=float(row['sot_pg']),
                fouls_pg=float(row['fouls_pg']),
                passes_pg=float(row['passes_pg']),
                yc_pg=float(row['yc_pg']),
                apps=int(row['apps'])
            ))
        return players
    
    def get_all_teams(self) -> List[TeamStats]:
        """Get all available team stats."""
        if self._team_stats is None:
            return []
        
        teams = []
        for _, row in self._team_stats.iterrows():
            teams.append(TeamStats(
                team=row['team'],
                goals_for_pg=float(row['goals_for_pg']),
                goals_against_pg=float(row['goals_against_pg']),
                shots_allowed_pg=float(row['shots_allowed_pg']),
                cards_pg=float(row['cards_pg'])
            ))
        return teams

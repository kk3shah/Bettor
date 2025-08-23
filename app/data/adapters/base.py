"""Base interface for data adapters."""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from app.schemas import PlayerStats, TeamStats


class StatsAdapter(ABC):
    """Abstract base class for stats data sources."""
    
    @abstractmethod
    def get_player_stats(self, player_name: str, team: str) -> Optional[PlayerStats]:
        """Get stats for a specific player."""
        pass
    
    @abstractmethod
    def get_team_stats(self, team: str) -> Optional[TeamStats]:
        """Get stats for a specific team."""
        pass
    
    @abstractmethod
    def find_player(self, team: str, player_name: str) -> Optional[PlayerStats]:
        """Find a player with fuzzy matching if needed."""
        pass
    
    @abstractmethod
    def get_all_players(self) -> List[PlayerStats]:
        """Get all available player stats."""
        pass
    
    @abstractmethod
    def get_all_teams(self) -> List[TeamStats]:
        """Get all available team stats."""
        pass
    
    def is_available(self) -> bool:
        """Check if the data source is available."""
        try:
            teams = self.get_all_teams()
            return len(teams) > 0
        except Exception:
            return False


class DataAdapterError(Exception):
    """Custom exception for data adapter errors."""
    pass

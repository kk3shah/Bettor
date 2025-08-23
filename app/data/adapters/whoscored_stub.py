"""WhoScored data adapter stub for future implementation."""
from typing import Optional, List
from .base import StatsAdapter, DataAdapterError
from app.schemas import PlayerStats, TeamStats


class WhoScoredAdapter(StatsAdapter):
    """
    Stub adapter for WhoScored data source.
    
    This is a placeholder for future implementation of WhoScored scraping or API integration.
    
    To implement:
    1. Add web scraping using requests/BeautifulSoup or selenium
    2. Implement API integration if WhoScored provides one
    3. Handle rate limiting and respectful scraping practices
    4. Add caching to avoid repeated requests
    5. Implement proper error handling and retries
    
    Legal considerations:
    - Check WhoScored's robots.txt and Terms of Service
    - Implement respectful scraping with delays
    - Consider using official API if available
    - Add User-Agent and follow site guidelines
    
    Example implementation approach:
    ```python
    import requests
    from bs4 import BeautifulSoup
    import time
    
    def scrape_player_stats(self, player_name: str, team: str):
        # Implement scraping logic here
        # Remember to add delays and respect rate limits
        time.sleep(1)  # Be respectful to the server
        # ... scraping implementation
    ```
    """
    
    def __init__(self):
        self.base_url = "https://www.whoscored.com"
        self._enabled = False  # Disabled by default
    
    def get_player_stats(self, player_name: str, team: str) -> Optional[PlayerStats]:
        """Get stats for a specific player from WhoScored."""
        raise NotImplementedError(
            "WhoScored adapter not implemented yet. "
            "Please implement scraping logic or use the manual CSV adapter."
        )
    
    def get_team_stats(self, team: str) -> Optional[TeamStats]:
        """Get stats for a specific team from WhoScored."""
        raise NotImplementedError(
            "WhoScored adapter not implemented yet. "
            "Please implement scraping logic or use the manual CSV adapter."
        )
    
    def find_player(self, team: str, player_name: str) -> Optional[PlayerStats]:
        """Find a player with fuzzy matching."""
        raise NotImplementedError(
            "WhoScored adapter not implemented yet. "
            "Please implement scraping logic or use the manual CSV adapter."
        )
    
    def get_all_players(self) -> List[PlayerStats]:
        """Get all available player stats."""
        raise NotImplementedError(
            "WhoScored adapter not implemented yet. "
            "Please implement scraping logic or use the manual CSV adapter."
        )
    
    def get_all_teams(self) -> List[TeamStats]:
        """Get all available team stats."""
        raise NotImplementedError(
            "WhoScored adapter not implemented yet. "
            "Please implement scraping logic or use the manual CSV adapter."
        )
    
    def is_available(self) -> bool:
        """Check if WhoScored adapter is available."""
        return False  # Always return False until implemented

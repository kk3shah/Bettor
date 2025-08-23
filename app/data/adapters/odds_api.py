"""Odds scraping from The Odds API and other free sources."""
import requests
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time


class OddsAPIScraper:
    """Scraper using The Odds API (free tier available)."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "demo"  # Demo key for testing
        self.base_url = "https://api.the-odds-api.com/v4"
        self.session = requests.Session()
    
    def get_football_matches(self, region='us') -> List[Dict]:
        """Get upcoming football matches."""
        url = f"{self.base_url}/sports/soccer_epl/odds"
        params = {
            'api_key': self.api_key,
            'regions': region,
            'markets': 'h2h,spreads,totals',
            'oddsFormat': 'american',
            'dateFormat': 'iso'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {len(data)} upcoming matches")
                return data
            else:
                print(f"❌ Odds API returned {response.status_code}: {response.text}")
                return []
        except Exception as e:
            print(f"❌ Error fetching matches: {e}")
            return []
    
    def find_match(self, home_team: str, away_team: str, matches: List[Dict]) -> Optional[Dict]:
        """Find specific match in the odds data."""
        
        # Normalize team names for matching
        home_variations = [home_team, home_team.replace(' ', ''), 'Manchester City', 'Man City', 'City']
        away_variations = [away_team, away_team.replace(' ', ''), 'Tottenham Hotspur', 'Tottenham', 'Spurs']
        
        for match in matches:
            home_match = any(var.lower() in match['home_team'].lower() for var in home_variations)
            away_match = any(var.lower() in match['away_team'].lower() for var in away_variations)
            
            if home_match and away_match:
                print(f"✅ Found match: {match['home_team']} vs {match['away_team']}")
                return match
        
        print(f"❌ Could not find {home_team} vs {away_team} in available matches")
        return None
    
    def get_live_odds(self, home_team: str = "Manchester City", away_team: str = "Tottenham") -> List[Dict]:
        """Get live odds for the specific match."""
        print(f"🔍 Searching for live odds: {home_team} vs {away_team}")
        
        # Get all matches
        matches = self.get_football_matches()
        
        if not matches:
            print("⚠️ No matches found from API, using sample data")
            return self._get_sample_odds(home_team, away_team)
        
        # Find our specific match
        match = self.find_match(home_team, away_team, matches)
        
        if not match:
            print("⚠️ Match not found in API data, using sample data")  
            return self._get_sample_odds(home_team, away_team)
        
        # Extract player prop odds if available
        odds_data = self._extract_player_props(match)
        
        if not odds_data:
            print("⚠️ No player props found, using sample data")
            return self._get_sample_odds(home_team, away_team)
        
        return odds_data
    
    def _extract_player_props(self, match: Dict) -> List[Dict]:
        """Extract player prop odds from match data."""
        odds_data = []
        
        # The Odds API doesn't typically include player props in free tier
        # This would need to be implemented based on the specific API response format
        
        print("ℹ️ Player props not available in free API tier")
        return odds_data
    
    def _get_sample_odds(self, home_team: str, away_team: str) -> List[Dict]:
        """Fallback sample odds with realistic pricing."""
        match_id = f"{home_team.replace(' ', '-')}-{away_team.replace(' ', '-')}-{datetime.now().strftime('%Y-%m-%d')}"
        
        return [
            # Manchester City players (with home boost in pricing)
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Erling Haaland', 'team': home_team, 'threshold': 4, 'odds_american': '+165', 'book': 'SampleBook'},
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Erling Haaland', 'team': home_team, 'threshold': 3, 'odds_american': '-110', 'book': 'SampleBook'},
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Phil Foden', 'team': home_team, 'threshold': 3, 'odds_american': '+185', 'book': 'SampleBook'},
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Phil Foden', 'team': home_team, 'threshold': 2, 'odds_american': '+105', 'book': 'SampleBook'},
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Kevin De Bruyne', 'team': home_team, 'threshold': 3, 'odds_american': '+150', 'book': 'SampleBook'},
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Jack Grealish', 'team': home_team, 'threshold': 2, 'odds_american': '+140', 'book': 'SampleBook'},
            
            # Tottenham players (current squad, away pricing)
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Dominic Solanke', 'team': away_team, 'threshold': 3, 'odds_american': '+145', 'book': 'SampleBook'},
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Dominic Solanke', 'team': away_team, 'threshold': 2, 'odds_american': '+105', 'book': 'SampleBook'},
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Brennan Johnson', 'team': away_team, 'threshold': 2, 'odds_american': '+115', 'book': 'SampleBook'},
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Timo Werner', 'team': away_team, 'threshold': 2, 'odds_american': '+125', 'book': 'SampleBook'},
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'James Maddison', 'team': away_team, 'threshold': 2, 'odds_american': '+135', 'book': 'SampleBook'},
        ]


class SampleOddsProvider:
    """Provides realistic sample odds for testing."""
    
    @staticmethod
    def get_realistic_odds(home_team: str, away_team: str) -> List[Dict]:
        """Get realistic odds based on current market prices."""
        match_id = f"{home_team.replace(' ', '-')}-{away_team.replace(' ', '-')}-{datetime.now().strftime('%Y-%m-%d')}"
        
        # These odds are based on realistic market pricing for such a match
        return [
            # Haaland - Premium striker, home advantage
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Erling Haaland', 'team': home_team, 'threshold': 4, 'odds_american': '+160', 'book': 'Market'},
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Erling Haaland', 'team': home_team, 'threshold': 3, 'odds_american': '-115', 'book': 'Market'},
            
            # Foden - Key attacker, good form
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Phil Foden', 'team': home_team, 'threshold': 3, 'odds_american': '+180', 'book': 'Market'},
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Phil Foden', 'team': home_team, 'threshold': 2, 'odds_american': '+110', 'book': 'Market'},
            
            # KDB - Injury concerns, but still class
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Kevin De Bruyne', 'team': home_team, 'threshold': 3, 'odds_american': '+155', 'book': 'Market'},
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Kevin De Bruyne', 'team': home_team, 'threshold': 2, 'odds_american': '+120', 'book': 'Market'},
            
            # Solanke - New signing, away from home
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Dominic Solanke', 'team': away_team, 'threshold': 3, 'odds_american': '+170', 'book': 'Market'},
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Dominic Solanke', 'team': away_team, 'threshold': 2, 'odds_american': '+115', 'book': 'Market'},
            
            # Johnson - Pace threat but inconsistent
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Brennan Johnson', 'team': away_team, 'threshold': 2, 'odds_american': '+125', 'book': 'Market'},
            
            # Werner - Pace but poor finishing
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Timo Werner', 'team': away_team, 'threshold': 2, 'odds_american': '+135', 'book': 'Market'},
            
            # Maddison - Creative but not always shooting
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'James Maddison', 'team': away_team, 'threshold': 2, 'odds_american': '+140', 'book': 'Market'},
        ]
    
    @staticmethod
    def get_premium_odds(home_team: str, away_team: str) -> List[Dict]:
        """Get odds that show clear value opportunities."""
        match_id = f"{home_team.replace(' ', '-')}-{away_team.replace(' ', '-')}-{datetime.now().strftime('%Y-%m-%d')}"
        
        # These odds are intentionally mispriced to show value
        return [
            # Underpriced Haaland props
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Erling Haaland', 'team': home_team, 'threshold': 4, 'odds_american': '+200', 'book': 'ValueBook'},
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Erling Haaland', 'team': home_team, 'threshold': 3, 'odds_american': '+100', 'book': 'ValueBook'},
            
            # Great value on City attackers 
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Phil Foden', 'team': home_team, 'threshold': 2, 'odds_american': '+130', 'book': 'ValueBook'},
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Kevin De Bruyne', 'team': home_team, 'threshold': 2, 'odds_american': '+140', 'book': 'ValueBook'},
            
            # Decent value on Spurs
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Dominic Solanke', 'team': away_team, 'threshold': 2, 'odds_american': '+120', 'book': 'ValueBook'},
            {'match_id': match_id, 'market': 'Player Shots', 'player_name': 'Brennan Johnson', 'team': away_team, 'threshold': 2, 'odds_american': '+140', 'book': 'ValueBook'},
        ]

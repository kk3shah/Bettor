#!/usr/bin/env python3
"""
⚽ API-FOOTBALL Integration
Following Medium article approach with smart caching for 100 requests/day limit
https://medium.com/@bouabdallaoui.yassine/football-apis-made-easy-the-easiest-way-to-fetch-any-player-stats-318aa4146b1d
"""
import requests
import json
import csv
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time

class APIFootballClient:
    """Smart API-FOOTBALL client with caching to maximize 100 requests/day."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api-football-v1.p.rapidapi.com/v3"
        self.headers = {
            'X-RapidAPI-Key': api_key,
            'X-RapidAPI-Host': 'api-football-v1.p.rapidapi.com'
        }
        
        # Cache directory
        self.cache_dir = Path("data/api_football_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Request tracking
        self.requests_file = self.cache_dir / "requests_log.csv"
        self.daily_limit = 100
        
        # League IDs from Medium article
        self.league_ids = {
            'Premier League': 39,
            'La Liga': 140,
            'Serie A': 135,
            'Bundesliga': 78,
            'Ligue 1': 61,
            'Champions League': 2
        }
        
        print(f"🔑 API-FOOTBALL Client initialized with {self.daily_limit} requests/day limit")
    
    def _log_request(self, endpoint: str, success: bool = True):
        """Log API request for daily tracking."""
        timestamp = datetime.now().isoformat()
        
        # Create file if doesn't exist
        if not self.requests_file.exists():
            with open(self.requests_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'endpoint', 'success', 'date'])
        
        # Log request
        with open(self.requests_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, endpoint, success, datetime.now().date()])
    
    def _get_daily_request_count(self) -> int:
        """Get today's request count."""
        if not self.requests_file.exists():
            return 0
        
        today = datetime.now().date()
        count = 0
        
        try:
            with open(self.requests_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['date'] == str(today) and row['success'] == 'True':
                        count += 1
        except Exception as e:
            print(f"⚠️ Error reading request log: {e}")
        
        return count
    
    def _can_make_request(self) -> bool:
        """Check if we can make another API request today."""
        current_count = self._get_daily_request_count()
        remaining = self.daily_limit - current_count
        
        print(f"📊 API Requests today: {current_count}/{self.daily_limit} (Remaining: {remaining})")
        
        return current_count < self.daily_limit
    
    def _get_cache_file(self, cache_key: str) -> Path:
        """Get cache file path for a given key."""
        return self.cache_dir / f"{cache_key}.json"
    
    def _is_cache_valid(self, cache_file: Path, hours: int = 24) -> bool:
        """Check if cache file is still valid."""
        if not cache_file.exists():
            return False
        
        file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        return datetime.now() - file_time < timedelta(hours=hours)
    
    def _load_cache(self, cache_key: str) -> Optional[Dict]:
        """Load data from cache if valid."""
        cache_file = self._get_cache_file(cache_key)
        
        if self._is_cache_valid(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    print(f"💾 Using cached data for {cache_key}")
                    return data
            except Exception as e:
                print(f"⚠️ Cache read error for {cache_key}: {e}")
        
        return None
    
    def _save_cache(self, cache_key: str, data: Dict):
        """Save data to cache."""
        cache_file = self._get_cache_file(cache_key)
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
                print(f"💾 Cached data for {cache_key}")
        except Exception as e:
            print(f"⚠️ Cache save error for {cache_key}: {e}")
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request with caching and rate limiting."""
        # Create cache key
        cache_key = f"{endpoint}_{hash(str(params))}"
        
        # Try cache first
        cached_data = self._load_cache(cache_key)
        if cached_data:
            return cached_data
        
        # Check rate limit
        if not self._can_make_request():
            print(f"❌ Daily API limit reached ({self.daily_limit} requests)")
            return None
        
        # Make request
        url = f"{self.base_url}/{endpoint}"
        
        try:
            print(f"🌐 API Request: {endpoint} {params or ''}")
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                self._log_request(endpoint, True)
                self._save_cache(cache_key, data)
                
                # Rate limiting - be nice to the API
                time.sleep(1)
                
                return data
            else:
                print(f"❌ API Error {response.status_code}: {response.text[:200]}")
                self._log_request(endpoint, False)
                return None
                
        except Exception as e:
            print(f"❌ Request failed for {endpoint}: {e}")
            self._log_request(endpoint, False)
            return None
    
    def get_leagues(self) -> Dict[str, int]:
        """Get available leagues and their IDs."""
        print(f"\n🏆 Fetching leagues...")
        
        data = self._make_request("leagues", {"season": 2024})
        if not data or 'response' not in data:
            return self.league_ids  # Fallback to known IDs
        
        leagues = {}
        for league_data in data['response']:
            league = league_data['league']
            name = league['name']
            league_id = league['id']
            
            # Map to our known leagues
            if 'Premier League' in name or 'England' in name:
                leagues['Premier League'] = league_id
            elif 'La Liga' in name or 'Spain' in name:
                leagues['La Liga'] = league_id
            elif 'Serie A' in name or 'Italy' in name:
                leagues['Serie A'] = league_id
            elif 'Bundesliga' in name or 'Germany' in name:
                leagues['Bundesliga'] = league_id
            elif 'Ligue 1' in name or 'France' in name:
                leagues['Ligue 1'] = league_id
            elif 'Champions League' in name:
                leagues['Champions League'] = league_id
        
        print(f"✅ Found {len(leagues)} leagues")
        return leagues or self.league_ids
    
    def get_teams(self, league_id: int, season: int = 2024) -> List[Dict]:
        """Get teams for a specific league."""
        print(f"\n👥 Fetching teams for league {league_id}...")
        
        data = self._make_request("teams", {"league": league_id, "season": season})
        if not data or 'response' not in data:
            return []
        
        teams = []
        for team_data in data['response']:
            team = team_data['team']
            teams.append({
                'id': team['id'],
                'name': team['name'],
                'logo': team.get('logo', ''),
                'founded': team.get('founded', 0)
            })
        
        print(f"✅ Found {len(teams)} teams")
        return teams
    
    def get_players(self, team_id: int, season: int = 2024) -> List[Dict]:
        """Get players and statistics for a specific team."""
        print(f"\n⚽ Fetching players for team {team_id}...")
        
        data = self._make_request("players", {"team": team_id, "season": season})
        if not data or 'response' not in data:
            return []
        
        players = []
        for player_data in data['response']:
            player = player_data['player']
            statistics = player_data.get('statistics', [])
            
            # Get main statistics (usually first entry)
            stats = statistics[0] if statistics else {}
            games = stats.get('games', {})
            goals = stats.get('goals', {})
            shots = stats.get('shots', {})
            passes = stats.get('passes', {})
            tackles = stats.get('tackles', {})
            cards = stats.get('cards', {})
            
            player_info = {
                'id': player['id'],
                'name': player['name'],
                'age': player.get('age', 0),
                'position': player.get('position', 'Unknown'),
                'nationality': player.get('nationality', 'Unknown'),
                
                # Game statistics
                'apps': games.get('appearences', 0),
                'minutes': games.get('minutes', 0),
                
                # Goal statistics
                'goals': goals.get('total', 0),
                'assists': goals.get('assists', 0),
                
                # Shot statistics
                'shots_total': shots.get('total', 0),
                'shots_on_target': shots.get('on', 0),
                
                # Pass statistics
                'passes_total': passes.get('total', 0),
                'passes_accuracy': passes.get('accuracy', 0),
                
                # Defensive statistics
                'tackles_total': tackles.get('total', 0),
                
                # Disciplinary
                'yellow_cards': cards.get('yellow', 0),
                'red_cards': cards.get('red', 0)
            }
            
            # Calculate per-game averages
            apps = max(player_info['apps'], 1)  # Avoid division by zero
            player_info.update({
                'goals_pg': player_info['goals'] / apps,
                'assists_pg': player_info['assists'] / apps,
                'shots_pg': player_info['shots_total'] / apps,
                'shots_on_target_pg': player_info['shots_on_target'] / apps,
                'tackles_pg': player_info['tackles_total'] / apps,
                'yellow_cards_pg': player_info['yellow_cards'] / apps,
            })
            
            players.append(player_info)
        
        print(f"✅ Found {len(players)} players")
        return players
    
    def get_fixtures(self, league_id: int, days_ahead: int = 1) -> List[Dict]:
        """Get upcoming fixtures for a league."""
        print(f"\n📅 Fetching fixtures for league {league_id}...")
        
        # Get fixtures for next few days
        from_date = datetime.now().strftime('%Y-%m-%d')
        to_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        data = self._make_request("fixtures", {
            "league": league_id,
            "season": 2024,
            "from": from_date,
            "to": to_date
        })
        
        if not data or 'response' not in data:
            return []
        
        fixtures = []
        for fixture_data in data['response']:
            fixture = fixture_data['fixture']
            teams = fixture_data['teams']
            
            fixtures.append({
                'id': fixture['id'],
                'date': fixture['date'],
                'status': fixture['status']['long'],
                'home_team': {
                    'id': teams['home']['id'],
                    'name': teams['home']['name'],
                    'logo': teams['home']['logo']
                },
                'away_team': {
                    'id': teams['away']['id'],
                    'name': teams['away']['name'],
                    'logo': teams['away']['logo']
                }
            })
        
        print(f"✅ Found {len(fixtures)} fixtures")
        return fixtures

def test_api_football_integration():
    """Test the API-FOOTBALL integration with the provided key."""
    print("🚀 TESTING API-FOOTBALL INTEGRATION")
    print("=" * 50)
    
    # Initialize client
    api_key = "11e4e68535c9fb6d241e28f883b10182"
    client = APIFootballClient(api_key)
    
    # Test 1: Get leagues
    print(f"\n1️⃣ Testing leagues...")
    leagues = client.get_leagues()
    print(f"   Available leagues: {list(leagues.keys())}")
    
    # Test 2: Get Premier League teams (if we have requests left)
    if client._can_make_request():
        print(f"\n2️⃣ Testing Premier League teams...")
        pl_id = leagues.get('Premier League', 39)
        teams = client.get_teams(pl_id)
        
        if teams:
            print(f"   Found {len(teams)} teams:")
            for team in teams[:5]:  # Show first 5
                print(f"   - {team['name']} (ID: {team['id']})")
        
        # Test 3: Get players for first team (if we have requests left)
        if teams and client._can_make_request():
            print(f"\n3️⃣ Testing players for {teams[0]['name']}...")
            players = client.get_players(teams[0]['id'])
            
            if players:
                print(f"   Found {len(players)} players:")
                for player in players[:3]:  # Show first 3
                    print(f"   - {player['name']} ({player['position']}) - {player['goals']} goals in {player['apps']} apps")
    
    print(f"\n✅ API-FOOTBALL integration test complete!")
    print(f"📊 Requests remaining today: {client.daily_limit - client._get_daily_request_count()}")

if __name__ == "__main__":
    test_api_football_integration()

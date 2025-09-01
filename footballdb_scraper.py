#!/usr/bin/env python3
"""
Football.db SQLite Database Scraper
Uses openfootball JSON data to build a local SQLite database for real player props.
"""

import sqlite3
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os

class FootballDBScraper:
    """Scraper that builds and queries a local football.db SQLite database."""
    
    def __init__(self, db_path: str = "data/football.db"):
        """Initialize the scraper with database path."""
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with football.db schema."""
        print("🗄️ Initializing football.db SQLite database...")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create teams table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS teams (
                    id INTEGER PRIMARY KEY,
                    key TEXT UNIQUE,
                    title TEXT,
                    code TEXT,
                    country_key TEXT
                )
            ''')
            
            # Create events table (seasons/competitions)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY,
                    key TEXT UNIQUE,
                    title TEXT,
                    league_key TEXT,
                    season TEXT
                )
            ''')
            
            # Create games table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY,
                    event_key TEXT,
                    round TEXT,
                    date TEXT,
                    team1_key TEXT,
                    team2_key TEXT,
                    score1 INTEGER,
                    score2 INTEGER,
                    FOREIGN KEY (team1_key) REFERENCES teams (key),
                    FOREIGN KEY (team2_key) REFERENCES teams (key)
                )
            ''')
            
            # Create players table (extended for betting props)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    team_key TEXT,
                    position TEXT,
                    goals INTEGER DEFAULT 0,
                    assists INTEGER DEFAULT 0,
                    appearances INTEGER DEFAULT 0,
                    shots INTEGER DEFAULT 0,
                    tackles INTEGER DEFAULT 0,
                    season TEXT,
                    FOREIGN KEY (team_key) REFERENCES teams (key)
                )
            ''')
            
            conn.commit()
            print("✅ Database schema initialized")
    
    def populate_database(self):
        """Populate database with real openfootball data."""
        print("📥 Populating database with real openfootball data...")
        
        # Step 1: Load English teams
        self._load_english_teams()
        
        # Step 2: Load Premier League events/seasons
        self._load_premier_league_events()
        
        # Step 3: Load games/fixtures
        self._load_premier_league_games()
        
        # Step 4: Load player statistics
        self._load_player_statistics()
        
        print("✅ Database populated with real data")
    
    def _load_english_teams(self):
        """Load teams from major European leagues."""
        print("🌍 Loading teams from major European leagues...")
        
        # All major league teams
        all_teams = [
            # Premier League
            {'key': 'arsenal', 'title': 'Arsenal', 'code': 'ARS', 'country': 'en', 'league': 'Premier League'},
            {'key': 'chelsea', 'title': 'Chelsea', 'code': 'CHE', 'country': 'en', 'league': 'Premier League'},
            {'key': 'liverpool', 'title': 'Liverpool', 'code': 'LIV', 'country': 'en', 'league': 'Premier League'},
            {'key': 'mancity', 'title': 'Manchester City', 'code': 'MCI', 'country': 'en', 'league': 'Premier League'},
            {'key': 'manutd', 'title': 'Manchester United', 'code': 'MUN', 'country': 'en', 'league': 'Premier League'},
            {'key': 'tottenham', 'title': 'Tottenham Hotspur', 'code': 'TOT', 'country': 'en', 'league': 'Premier League'},
            
            # La Liga
            {'key': 'realmadrid', 'title': 'Real Madrid', 'code': 'RMA', 'country': 'es', 'league': 'La Liga'},
            {'key': 'barcelona', 'title': 'Barcelona', 'code': 'BAR', 'country': 'es', 'league': 'La Liga'},
            {'key': 'atletico', 'title': 'Atletico Madrid', 'code': 'ATM', 'country': 'es', 'league': 'La Liga'},
            {'key': 'sevilla', 'title': 'Sevilla', 'code': 'SEV', 'country': 'es', 'league': 'La Liga'},
            
            # Bundesliga
            {'key': 'bayern', 'title': 'Bayern Munich', 'code': 'BAY', 'country': 'de', 'league': 'Bundesliga'},
            {'key': 'dortmund', 'title': 'Borussia Dortmund', 'code': 'BVB', 'country': 'de', 'league': 'Bundesliga'},
            {'key': 'leipzig', 'title': 'RB Leipzig', 'code': 'RBL', 'country': 'de', 'league': 'Bundesliga'},
            {'key': 'leverkusen', 'title': 'Bayer Leverkusen', 'code': 'B04', 'country': 'de', 'league': 'Bundesliga'},
            
            # Serie A
            {'key': 'juventus', 'title': 'Juventus', 'code': 'JUV', 'country': 'it', 'league': 'Serie A'},
            {'key': 'milan', 'title': 'AC Milan', 'code': 'MIL', 'country': 'it', 'league': 'Serie A'},
            {'key': 'inter', 'title': 'Inter Milan', 'code': 'INT', 'country': 'it', 'league': 'Serie A'},
            {'key': 'napoli', 'title': 'Napoli', 'code': 'NAP', 'country': 'it', 'league': 'Serie A'},
            
            # Ligue 1
            {'key': 'psg', 'title': 'PSG', 'code': 'PSG', 'country': 'fr', 'league': 'Ligue 1'},
            {'key': 'marseille', 'title': 'Marseille', 'code': 'OM', 'country': 'fr', 'league': 'Ligue 1'},
            {'key': 'lyon', 'title': 'Lyon', 'code': 'OL', 'country': 'fr', 'league': 'Ligue 1'},
            {'key': 'monaco', 'title': 'Monaco', 'code': 'ASM', 'country': 'fr', 'league': 'Ligue 1'},
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for team in all_teams:
                cursor.execute('''
                    INSERT OR REPLACE INTO teams (key, title, code, country_key)
                    VALUES (?, ?, ?, ?)
                ''', (team['key'], team['title'], team['code'], team['country']))
            conn.commit()
        
        print(f"✅ Loaded {len(all_teams)} teams from major European leagues")
    
    def _load_premier_league_events(self):
        """Load major European league seasons/events."""
        print("🏆 Loading major European league events...")
        
        events = [
            # Premier League
            {'key': 'en.2024-25', 'title': 'Premier League 2024/25', 'league_key': 'en.1', 'season': '2024-25'},
            {'key': 'en.2023-24', 'title': 'Premier League 2023/24', 'league_key': 'en.1', 'season': '2023-24'},
            # La Liga
            {'key': 'es.2024-25', 'title': 'La Liga 2024/25', 'league_key': 'es.1', 'season': '2024-25'},
            {'key': 'es.2023-24', 'title': 'La Liga 2023/24', 'league_key': 'es.1', 'season': '2023-24'},
            # Bundesliga
            {'key': 'de.2024-25', 'title': 'Bundesliga 2024/25', 'league_key': 'de.1', 'season': '2024-25'},
            {'key': 'de.2023-24', 'title': 'Bundesliga 2023/24', 'league_key': 'de.1', 'season': '2023-24'},
            # Serie A
            {'key': 'it.2024-25', 'title': 'Serie A 2024/25', 'league_key': 'it.1', 'season': '2024-25'},
            {'key': 'it.2023-24', 'title': 'Serie A 2023/24', 'league_key': 'it.1', 'season': '2023-24'},
            # Ligue 1
            {'key': 'fr.2024-25', 'title': 'Ligue 1 2024/25', 'league_key': 'fr.1', 'season': '2024-25'},
            {'key': 'fr.2023-24', 'title': 'Ligue 1 2023/24', 'league_key': 'fr.1', 'season': '2023-24'},
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for event in events:
                cursor.execute('''
                    INSERT OR REPLACE INTO events (key, title, league_key, season)
                    VALUES (?, ?, ?, ?)
                ''', (event['key'], event['title'], event['league_key'], event['season']))
            conn.commit()
        
        print(f"✅ Loaded {len(events)} Premier League events")
    
    def _load_premier_league_games(self):
        """Load Premier League games from openfootball JSON."""
        print("⚽ Loading Premier League games...")
        
        urls_to_try = [
            "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/en.1.json",
            "https://raw.githubusercontent.com/openfootball/football.json/master/2023-24/en.1.json"
        ]
        
        games_loaded = 0
        
        for url in urls_to_try:
            try:
                print(f"📡 Fetching: {url}")
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    season = "2024-25" if "2024-25" in url else "2023-24"
                    
                    # Parse matches from JSON
                    matches = data.get('matches', []) or data.get('rounds', [])
                    
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        
                        for match in matches:
                            if isinstance(match, dict):
                                date_str = match.get('date', '')
                                team1 = match.get('team1', '') or match.get('home', '')
                                team2 = match.get('team2', '') or match.get('away', '')
                                score1 = match.get('score1')
                                score2 = match.get('score2')
                                
                                if date_str and team1 and team2:
                                    # Convert team names to keys
                                    team1_key = self._team_name_to_key(team1)
                                    team2_key = self._team_name_to_key(team2)
                                    
                                    cursor.execute('''
                                        INSERT OR REPLACE INTO games 
                                        (event_key, round, date, team1_key, team2_key, score1, score2)
                                        VALUES (?, ?, ?, ?, ?, ?, ?)
                                    ''', (f'en.{season}', 'Regular', date_str, team1_key, team2_key, score1, score2))
                                    
                                    games_loaded += 1
                        
                        conn.commit()
                    
                    print(f"✅ Loaded {len(matches)} games from {season}")
                    
            except Exception as e:
                print(f"⚠️ Error loading games from {url}: {e}")
                continue
        
        print(f"✅ Total games loaded: {games_loaded}")
    
    def _load_player_statistics(self):
        """Load REAL player statistics from openfootball or return empty."""
        print("👥 Attempting to load REAL player statistics...")
        
        # Get all teams from database (all leagues)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, title FROM teams")
            teams = cursor.fetchall()
            
            players_loaded = 0
            
            for team_key, team_title in teams:
                # Try to get REAL player data from openfootball
                real_players = self._fetch_real_players_from_openfootball(team_key, team_title)
                
                if not real_players:
                    print(f"❌ No real player data found for {team_title} - skipping (no fake data)")
                    continue
                
                for player in real_players:
                    cursor.execute('''
                        INSERT OR REPLACE INTO players 
                        (name, team_key, position, goals, assists, appearances, shots, tackles, season)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        player['name'], team_key, player['position'],
                        player['goals'], player['assists'], player['appearances'],
                        player['shots'], player['tackles'], '2024-25'
                    ))
                    players_loaded += 1
            
            conn.commit()
        
        print(f"✅ Loaded {players_loaded} REAL player records (no fake data)")
    
    def _fetch_real_players_from_openfootball(self, team_key: str, team_title: str) -> List[Dict[str, Any]]:
        """Attempt to fetch real player data from openfootball - returns empty if not found."""
        print(f"🔍 Searching for real players for {team_title}...")
        
        # URLs to try for real player data
        urls_to_try = [
            f"https://raw.githubusercontent.com/openfootball/england/master/2024-25/squads/{team_key}.txt",
            f"https://raw.githubusercontent.com/openfootball/spain/master/2024-25/squads/{team_key}.txt",
            f"https://raw.githubusercontent.com/openfootball/germany/master/2024-25/squads/{team_key}.txt",
            f"https://raw.githubusercontent.com/openfootball/italy/master/2024-25/squads/{team_key}.txt",
            f"https://raw.githubusercontent.com/openfootball/france/master/2024-25/squads/{team_key}.txt"
        ]
        
        for url in urls_to_try:
            try:
                response = self.session.get(url, timeout=5)
                if response.status_code == 200:
                    players = self._parse_openfootball_squad(response.text, team_key)
                    if players:
                        print(f"✅ Found {len(players)} real players for {team_title}")
                        return players
            except Exception as e:
                continue
        
        print(f"❌ No real player data found for {team_title}")
        return []  # Return empty - NO FAKE DATA
    
    def _parse_openfootball_squad(self, data: str, team_key: str) -> List[Dict[str, Any]]:
        """Parse openfootball squad data format."""
        players = []
        
        # This would parse the actual openfootball format
        # Since we don't have real data, return empty
        print("⚠️ Real openfootball parsing not implemented - no fake data generated")
        
        return []  # Return empty - NO FAKE DATA
    
    def _team_name_to_key(self, team_name: str) -> str:
        """Convert team name to database key for all major leagues."""
        name_to_key = {
            # Premier League
            'Arsenal': 'arsenal',
            'Chelsea': 'chelsea', 
            'Liverpool': 'liverpool',
            'Manchester City': 'mancity',
            'Manchester United': 'manutd',
            'Tottenham': 'tottenham',
            'Tottenham Hotspur': 'tottenham',
            
            # La Liga
            'Real Madrid': 'realmadrid',
            'Barcelona': 'barcelona',
            'Atletico Madrid': 'atletico',
            'Sevilla': 'sevilla',
            
            # Bundesliga
            'Bayern Munich': 'bayern',
            'Borussia Dortmund': 'dortmund',
            'RB Leipzig': 'leipzig',
            'Bayer Leverkusen': 'leverkusen',
            
            # Serie A
            'Juventus': 'juventus',
            'AC Milan': 'milan',
            'Inter Milan': 'inter',
            'Napoli': 'napoli',
            
            # Ligue 1
            'PSG': 'psg',
            'Marseille': 'marseille',
            'Lyon': 'lyon',
            'Monaco': 'monaco'
        }
        return name_to_key.get(team_name, team_name.lower().replace(' ', ''))
    
    def get_english_teams(self) -> List[Dict[str, Any]]:
        """Query English teams using SQL (like the documentation example)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT key, title, code
                FROM teams
                WHERE country_key = 'en'
                ORDER BY title
            """)
            
            teams = []
            for row in cursor.fetchall():
                teams.append({
                    'key': row[0],
                    'title': row[1], 
                    'code': row[2]
                })
            
            return teams
    
    def get_premier_league_games(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming Premier League games."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get games from current season
            cursor.execute("""
                SELECT g.date, t1.title as home_team, t2.title as away_team,
                       g.score1, g.score2
                FROM games g
                JOIN teams t1 ON t1.key = g.team1_key
                JOIN teams t2 ON t2.key = g.team2_key
                WHERE g.event_key = 'en.2024-25'
                ORDER BY g.date
            """)
            
            games = []
            for row in cursor.fetchall():
                games.append({
                    'date': row[0],
                    'home_team': row[1],
                    'away_team': row[2],
                    'score1': row[3],
                    'score2': row[4]
                })
            
            return games
    
    def get_player_props(self, team_name: str) -> List[Dict[str, Any]]:
        """Generate betting props from real player statistics only."""
        print(f"🎯 Checking for real player data for {team_name}...")
        
        # Convert team name to key
        team_key = self._team_name_to_key(team_name)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Query players for the team
            cursor.execute("""
                SELECT name, position, goals, assists, appearances, shots, tackles
                FROM players
                WHERE team_key = ? AND season = '2024-25'
                ORDER BY goals DESC, assists DESC
                LIMIT 5
            """, (team_key,))
            
            rows = cursor.fetchall()
            
            if not rows:
                print(f"❌ No real player data found for {team_name} - returning empty")
                return []
            
            props = []
            for row in rows:
                name, position, goals, assists, appearances, shots, tackles = row
                
                # Calculate per-game averages
                apps = max(1, appearances)
                goals_per_game = goals / apps
                assists_per_game = assists / apps
                shots_per_game = shots / apps
                tackles_per_game = tackles / apps
                
                # Generate position-specific props
                if position == 'Forward':
                    props.extend([
                        {
                            'player_name': name,
                            'team': team_name,
                            'prop_type': 'Player Goals',
                            'description': 'To score anytime',
                            'model_prob': min(0.45, goals_per_game * 2.2),
                            'confidence': 'High' if goals_per_game > 0.4 else 'Medium',
                            'expected_value': f"${max(0, goals_per_game * 18):.2f}",
                            'source': 'Football.db Real Stats',
                            'stats': f'{goals}G in {appearances} apps'
                        },
                        {
                            'player_name': name,
                            'team': team_name,
                            'prop_type': 'Player Shots',
                            'description': '2+ shots on target',
                            'model_prob': min(0.75, shots_per_game / 3.5),
                            'confidence': 'High',
                            'expected_value': f"${max(0, shots_per_game * 4):.2f}",
                            'source': 'Football.db Real Stats',
                            'stats': f'{shots} shots in {appearances} apps'
                        }
                    ])
                
                elif position == 'Midfielder':
                    props.extend([
                        {
                            'player_name': name,
                            'team': team_name,
                            'prop_type': 'Player Assists',
                            'description': 'To get an assist',
                            'model_prob': min(0.35, assists_per_game * 2.5),
                            'confidence': 'High' if assists_per_game > 0.2 else 'Medium',
                            'expected_value': f"${max(0, assists_per_game * 12):.2f}",
                            'source': 'Football.db Real Stats',
                            'stats': f'{assists}A in {appearances} apps'
                        },
                        {
                            'player_name': name,
                            'team': team_name,
                            'prop_type': 'Player Tackles',
                            'description': '3+ tackles',
                            'model_prob': min(0.8, tackles_per_game / 4),
                            'confidence': 'High',
                            'expected_value': f"${max(0, tackles_per_game * 2):.2f}",
                            'source': 'Football.db Real Stats',
                            'stats': f'{tackles} tackles in {appearances} apps'
                        }
                    ])
                
                else:  # Defenders
                    props.append({
                        'player_name': name,
                        'team': team_name,
                        'prop_type': 'Player Tackles',
                        'description': '4+ tackles',
                        'model_prob': min(0.85, tackles_per_game / 4.5),
                        'confidence': 'High',
                        'expected_value': f"${max(0, tackles_per_game * 2.5):.2f}",
                        'source': 'Football.db Real Stats',
                        'stats': f'{tackles} tackles in {appearances} apps'
                    })
            
            return props


def test_footballdb_scraper():
    """Test the football.db scraper."""
    print("🧪 Testing Football.db SQLite scraper...")
    
    scraper = FootballDBScraper()
    
    # Populate database
    scraper.populate_database()
    
    # Test queries
    print("\n📊 Testing SQL queries...")
    
    # List English teams (like documentation example)
    teams = scraper.get_english_teams()
    print(f"✅ Found {len(teams)} English teams")
    for team in teams[:5]:
        print(f"   - {team['title']} ({team['code']})")
    
    # Get games
    games = scraper.get_premier_league_games()
    print(f"✅ Found {len(games)} Premier League games")
    
    # Generate player props
    props = scraper.get_player_props('Arsenal')
    print(f"✅ Generated {len(props)} player props for Arsenal")
    for prop in props[:3]:
        print(f"   - {prop['player_name']}: {prop['prop_type']} ({prop['confidence']})")
    
    return scraper


if __name__ == "__main__":
    test_footballdb_scraper()

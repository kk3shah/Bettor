#!/usr/bin/env python3
"""
Real Football Data Integrator
Combines multiple real data sources for comprehensive betting analysis.
"""

import sqlite3
import json
import os
import glob
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd

class RealDataIntegrator:
    """Integrates multiple real football data sources."""
    
    def __init__(self, db_path: str = "data/integrated_football.db"):
        """Initialize the integrator."""
        self.db_path = db_path
        self.clubs_db_path = "data/clubs.db"
        self.football_data_path = "data/football_data/FootballData-master"
        
        # ESPN team IDs for current squad data
        self.espn_team_ids = {
            'Arsenal': '359', 'Aston Villa': '362', 'Brighton & Hove Albion': '331',
            'Burnley': '379', 'Chelsea': '363', 'Crystal Palace': '384',
            'Everton': '368', 'Fulham': '370', 'Liverpool': '364',
            'Manchester City': '382', 'Manchester United': '360', 'Newcastle United': '361',
            'Tottenham Hotspur': '367', 'West Ham United': '371', 'Wolverhampton Wanderers': '380',
            'AFC Bournemouth': '349', 'Brentford': '337', 'Leeds United': '357',
            'Leicester City': '375', 'Nottingham Forest': '393'
        }
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize integrated database
        self._init_integrated_database()
    
    def _init_integrated_database(self):
        """Initialize the integrated database with comprehensive schema."""
        print("🗄️ Initializing integrated football database...")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Clubs table (from clubs.db)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clubs (
                    key TEXT PRIMARY KEY,
                    name TEXT,
                    alt_names TEXT,
                    country_key TEXT,
                    city TEXT,
                    district TEXT,
                    address TEXT,
                    geos TEXT
                )
            ''')
            
            # Stadiums table (from clubs.db)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stadiums (
                    key TEXT PRIMARY KEY,
                    name TEXT,
                    alt_names TEXT,
                    country_key TEXT,
                    city_name TEXT,
                    district TEXT,
                    address TEXT,
                    geos TEXT
                )
            ''')
            
            # Historical matches table (from FootballData)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historical_matches (
                    id TEXT PRIMARY KEY,
                    date TEXT,
                    time TEXT,
                    venue TEXT,
                    referee TEXT,
                    attendance INTEGER,
                    home_team TEXT,
                    away_team TEXT,
                    home_score INTEGER,
                    away_score INTEGER,
                    season TEXT,
                    league TEXT
                )
            ''')
            
            # Player performances table (from FootballData)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS player_performances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id TEXT,
                    player_name TEXT,
                    team TEXT,
                    position TEXT,
                    goals INTEGER DEFAULT 0,
                    assists INTEGER DEFAULT 0,
                    yellow_cards INTEGER DEFAULT 0,
                    red_cards INTEGER DEFAULT 0,
                    substituted_on INTEGER DEFAULT 0,
                    substituted_off INTEGER DEFAULT 0,
                    season TEXT,
                    FOREIGN KEY (match_id) REFERENCES historical_matches (id)
                )
            ''')
            
            # Player statistics aggregated table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS player_stats (
                    player_name TEXT,
                    team TEXT,
                    season TEXT,
                    appearances INTEGER DEFAULT 0,
                    goals INTEGER DEFAULT 0,
                    assists INTEGER DEFAULT 0,
                    yellow_cards INTEGER DEFAULT 0,
                    red_cards INTEGER DEFAULT 0,
                    goals_per_game REAL DEFAULT 0,
                    assists_per_game REAL DEFAULT 0,
                    PRIMARY KEY (player_name, team, season)
                )
            ''')
            
            conn.commit()
            print("✅ Integrated database schema initialized")
    
    def integrate_all_data(self):
        """Integrate data from all sources."""
        print("🔄 Starting comprehensive data integration...")
        
        # Step 1: Import clubs and stadiums
        self._import_clubs_data()
        
        # Step 2: Import historical match data
        self._import_historical_matches()
        
        # Step 3: Calculate player statistics
        self._calculate_player_statistics()
        
        print("✅ Data integration completed")
    
    def _import_clubs_data(self):
        """Import clubs and stadiums from clubs.db."""
        print("🏟️ Importing clubs and stadiums data...")
        
        if not os.path.exists(self.clubs_db_path):
            print("❌ clubs.db not found")
            return
        
        with sqlite3.connect(self.clubs_db_path) as source_conn:
            with sqlite3.connect(self.db_path) as target_conn:
                # Import clubs
                clubs_df = pd.read_sql_query("SELECT * FROM clubs", source_conn)
                clubs_df.to_sql('clubs', target_conn, if_exists='replace', index=False)
                
                # Import stadiums (grounds)
                stadiums_df = pd.read_sql_query("SELECT * FROM grounds", source_conn)
                stadiums_df.to_sql('stadiums', target_conn, if_exists='replace', index=False)
                
                print(f"✅ Imported {len(clubs_df)} clubs and {len(stadiums_df)} stadiums")
    
    def _import_historical_matches(self):
        """Import the most recent available season data (2020-2021) for current statistics."""
        print("⚽ Importing most recent season data (2020-2021)...")
        
        # Use the most recent Premier League data from football-data.co.uk
        recent_csv_path = f"{self.football_data_path}/football-data.co.uk/england/2020-2021 (Until Jan 22)/Premier.csv"
        
        if not os.path.exists(recent_csv_path):
            print("❌ Most recent season CSV not found, falling back to 2018-2019 FootyStats")
            self._import_footystats_data()
            return
        
        season = "2020-21"
        print(f"📅 Processing most recent season: {season}")
        
        try:
            matches_imported = self._process_premier_csv(recent_csv_path, season)
            print(f"✅ Imported {matches_imported} matches from {season}")
            
            # Also import player stats from FootyStats 2018-2019 (most recent player data available)
            print("📊 Supplementing with 2018-2019 player statistics...")
            self._import_footystats_data()
            
        except Exception as e:
            print(f"⚠️ Error processing recent season: {e}")
            print("🔄 Falling back to FootyStats 2018-2019 data...")
            self._import_footystats_data()
    
    def _process_premier_csv(self, csv_path: str, season: str) -> int:
        """Process Premier League CSV data from football-data.co.uk."""
        try:
            df = pd.read_csv(csv_path)
            matches_imported = 0
            
            with sqlite3.connect(self.db_path) as conn:
                for _, row in df.iterrows():
                    # Insert match data
                    conn.execute("""
                        INSERT OR REPLACE INTO matches 
                        (date, home_team, away_team, home_goals, away_goals, season, 
                         home_shots, away_shots, home_shots_target, away_shots_target,
                         home_fouls, away_fouls, home_corners, away_corners,
                         home_yellow, away_yellow, home_red, away_red)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row.get('Date', ''), row.get('HomeTeam', ''), row.get('AwayTeam', ''),
                        row.get('FTHG', 0), row.get('FTAG', 0), season,
                        row.get('HS', 0), row.get('AS', 0), row.get('HST', 0), row.get('AST', 0),
                        row.get('HF', 0), row.get('AF', 0), row.get('HC', 0), row.get('AC', 0),
                        row.get('HY', 0), row.get('AY', 0), row.get('HR', 0), row.get('AR', 0)
                    ))
                    matches_imported += 1
                
                conn.commit()
            
            return matches_imported
        except Exception as e:
            print(f"❌ Error processing CSV: {e}")
            return 0
    
    def _import_footystats_data(self):
        """Import player statistics from FootyStats 2018-2019 data."""
        try:
            players_csv = f"{self.football_data_path}/FootyStats/england-premier-league-players-2018-to-2019-stats.csv"
            matches_csv = f"{self.football_data_path}/FootyStats/england-premier-league-matches-2018-to-2019-stats.csv"
            
            if not os.path.exists(players_csv):
                print("❌ FootyStats player data not found")
                return
            
            # Import player statistics
            players_df = pd.read_csv(players_csv)
            with sqlite3.connect(self.db_path) as conn:
                players_df.to_sql('player_stats', conn, if_exists='replace', index=False)
                print(f"✅ Imported {len(players_df)} player records from FootyStats 2018-19")
            
            # Import match statistics if available
            if os.path.exists(matches_csv):
                matches_df = pd.read_csv(matches_csv)
                with sqlite3.connect(self.db_path) as conn:
                    matches_df.to_sql('footystats_matches', conn, if_exists='replace', index=False)
                    print(f"✅ Imported {len(matches_df)} FootyStats match records")
                    
        except Exception as e:
            print(f"❌ Error importing FootyStats data: {e}")
    
    def _extract_season_from_path(self, path: str) -> str:
        """Extract season from directory path."""
        if "2016 - 2017" in path:
            return "2016-17"
        elif "2015 - 2016" in path:
            return "2015-16"
        elif "1992 - 2015" in path:
            return "1992-2015"
        elif "2011-2019" in path:
            return "2011-19"
        else:
            return "Unknown"
    
    def _process_match_file(self, json_file: str, season: str) -> tuple:
        """Process a single match JSON file."""
        with open(json_file, 'r', encoding='utf-8') as f:
            try:
                # Try to load as array of matches first
                data = json.load(f)
                if isinstance(data, list):
                    return self._process_match_list(data, season)
                elif isinstance(data, dict):
                    return self._process_match_dict(data, season)
            except json.JSONDecodeError:
                return 0, 0
        
        return 0, 0
    
    def _process_match_list(self, matches: List[Dict], season: str) -> tuple:
        """Process a list of matches (simple format)."""
        matches_added = 0
        performances_added = 0
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for match in matches:
                if not isinstance(match, dict):
                    continue
                
                match_id = match.get('id', '')
                home_team = match.get('home', '')
                away_team = match.get('away', '')
                
                if not all([match_id, home_team, away_team]):
                    continue
                
                # Extract scores
                score = match.get('score', ['0', '0'])
                home_score = int(score[0].strip()) if len(score) > 0 and score[0].strip().isdigit() else 0
                away_score = int(score[1].strip()) if len(score) > 1 and score[1].strip().isdigit() else 0
                
                # Insert match
                cursor.execute('''
                    INSERT OR REPLACE INTO historical_matches 
                    (id, home_team, away_team, home_score, away_score, season, league)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (match_id, home_team, away_team, home_score, away_score, season, 'Premier League'))
                
                matches_added += 1
            
            conn.commit()
        
        return matches_added, performances_added
    
    def _process_match_dict(self, data: Dict, season: str) -> tuple:
        """Process detailed match data (complex format)."""
        matches_added = 0
        performances_added = 0
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for match_id, match_data in data.items():
                if not isinstance(match_data, dict):
                    continue
                
                general = match_data.get('general', {})
                score = match_data.get('score', {})
                
                # Extract match details
                date = general.get('date', '')
                time = general.get('time', '')
                venue = general.get('venue', '')
                referee = general.get('referee', '')
                attendance = general.get('attendance', '0')
                
                home_team = score.get('home', '')
                away_team = score.get('away', '')
                home_score = score.get('homeScore', '0')
                away_score = score.get('awayScore', '0')
                
                # Convert attendance to integer
                try:
                    attendance = int(str(attendance).replace(',', ''))
                except:
                    attendance = 0
                
                # Convert scores to integers
                try:
                    home_score = int(home_score)
                    away_score = int(away_score)
                except:
                    home_score = away_score = 0
                
                # Insert match
                cursor.execute('''
                    INSERT OR REPLACE INTO historical_matches 
                    (id, date, time, venue, referee, attendance, home_team, away_team, 
                     home_score, away_score, season, league)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (match_id, date, time, venue, referee, attendance, home_team, away_team,
                      home_score, away_score, season, 'Premier League'))
                
                matches_added += 1
                
                # Process player performances
                performances_added += self._extract_player_performances(
                    cursor, match_id, match_data, home_team, away_team, season
                )
            
            conn.commit()
        
        return matches_added, performances_added
    
    def _extract_player_performances(self, cursor, match_id: str, match_data: Dict, 
                                   home_team: str, away_team: str, season: str) -> int:
        """Extract player performances from match data."""
        performances_added = 0
        
        # Extract goals
        home_goals = match_data.get('goalHome', {})
        away_goals = match_data.get('goalAway', {})
        
        # Extract substitutions
        home_subs = match_data.get('subsHome', {})
        away_subs = match_data.get('subsAway', {})
        
        # Extract fouls/cards
        home_fouls = match_data.get('foulHome', {})
        away_fouls = match_data.get('foulAway', {})
        
        # Process home team goals
        for goal_data in home_goals.values():
            if isinstance(goal_data, dict):
                player_name = goal_data.get('name', '')
                if player_name:
                    cursor.execute('''
                        INSERT OR REPLACE INTO player_performances 
                        (match_id, player_name, team, goals, season)
                        VALUES (?, ?, ?, 1, ?)
                    ''', (match_id, player_name, home_team, season))
                    performances_added += 1
        
        # Process away team goals
        for goal_data in away_goals.values():
            if isinstance(goal_data, dict):
                player_name = goal_data.get('name', '')
                if player_name:
                    cursor.execute('''
                        INSERT OR REPLACE INTO player_performances 
                        (match_id, player_name, team, goals, season)
                        VALUES (?, ?, ?, 1, ?)
                    ''', (match_id, player_name, away_team, season))
                    performances_added += 1
        
        # Process cards
        for foul_data in home_fouls.values():
            if isinstance(foul_data, dict):
                player_name = foul_data.get('name', '')
                card = foul_data.get('card', '')
                if player_name and card:
                    yellow_cards = 1 if 'Yellow' in card else 0
                    red_cards = 1 if 'Red' in card else 0
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO player_performances 
                        (match_id, player_name, team, yellow_cards, red_cards, season)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (match_id, player_name, home_team, yellow_cards, red_cards, season))
                    performances_added += 1
        
        for foul_data in away_fouls.values():
            if isinstance(foul_data, dict):
                player_name = foul_data.get('name', '')
                card = foul_data.get('card', '')
                if player_name and card:
                    yellow_cards = 1 if 'Yellow' in card else 0
                    red_cards = 1 if 'Red' in card else 0
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO player_performances 
                        (match_id, player_name, team, yellow_cards, red_cards, season)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (match_id, player_name, away_team, yellow_cards, red_cards, season))
                    performances_added += 1
        
        return performances_added
    
    def _calculate_player_statistics(self):
        """Calculate aggregated player statistics."""
        print("📊 Calculating player statistics...")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if FootyStats player_stats table exists and has data
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='player_stats'")
            if not cursor.fetchone():
                print("❌ No player_stats table found")
                return
            
            # Get count of player records
            cursor.execute("SELECT COUNT(*) FROM player_stats")
            stats_count = cursor.fetchone()[0]
            
            if stats_count == 0:
                print("❌ No player statistics found")
                return
                
            print(f"✅ Found {stats_count} player records from FootyStats 2018-19")
            
            # Show sample of available data
            cursor.execute("""
                SELECT full_name, "Current Club", position, appearances_overall, 
                       goals_overall, assists_overall 
                FROM player_stats 
                LIMIT 5
            """)
            
            sample_players = cursor.fetchall()
            print("📋 Sample player data:")
            for player in sample_players:
                name, club, pos, apps, goals, assists = player
                print(f"  • {name} ({club}) - {pos}: {apps} apps, {goals} goals, {assists} assists")
    
    def get_player_betting_props(self, team_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Generate real betting props from historical player data."""
        print(f"🎯 Generating real betting props for {team_name}...")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get top players for the team from FootyStats data
            cursor.execute('''
                SELECT full_name, "Current Club", position, appearances_overall, 
                       goals_overall, assists_overall, goals_per_90_overall, 
                       assists_per_90_overall, yellow_cards_overall, red_cards_overall
                FROM player_stats
                WHERE "Current Club" LIKE ? AND appearances_overall >= 10
                ORDER BY goals_overall DESC, assists_overall DESC, appearances_overall DESC
                LIMIT ?
            ''', (f'%{team_name}%', limit))
            
            players = cursor.fetchall()
            
            props = []
            for player_data in players:
                (name, team, position, apps, goals, assists, 
                 goals_per_90, assists_per_90, yellows, reds) = player_data
                
                # Generate props based on real statistics
                if goals_per_90 and goals_per_90 > 0.1:  # Only if player scores regularly
                    props.append({
                        'player_name': name,
                        'team': team,
                        'prop_type': 'Player Goals',
                        'description': 'To score anytime',
                        'model_prob': min(0.5, goals_per_90 * 2.5),
                        'confidence': 'High' if goals_per_90 > 0.3 else 'Medium',
                        'expected_value': f"${max(0, goals_per_90 * 20):.2f}",
                        'source': 'Real Historical Data (FootyStats 2018-19)',
                        'stats': f'{goals}G in {apps} apps',
                        'goals_per_90': goals_per_90
                    })
                
                if assists_per_90 and assists_per_90 > 0.05:  # Only if player assists regularly
                    props.append({
                        'player_name': name,
                        'team': team,
                        'prop_type': 'Player Assists',
                        'description': 'To get an assist',
                        'model_prob': min(0.4, assists_per_90 * 3),
                        'confidence': 'High' if assists_per_90 > 0.2 else 'Medium',
                        'expected_value': f"${max(0, assists_per_90 * 15):.2f}",
                        'source': 'Real Historical Data (FootyStats 2018-19)',
                        'stats': f'{assists}A in {apps} apps',
                        'assists_per_90': assists_per_90
                    })
            
            return props
    
    def get_database_summary(self) -> Dict[str, Any]:
        """Get summary of integrated database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            summary = {}
            
            # Count records in each table
            tables = ['clubs', 'stadiums', 'historical_matches', 'player_performances', 'player_stats']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                summary[table] = cursor.fetchone()[0]
            
            # Get sample player stats from FootyStats data
            cursor.execute('''
                SELECT full_name, "Current Club", goals_overall, assists_overall, 
                       appearances_overall, goals_per_90_overall
                FROM player_stats
                ORDER BY goals_overall DESC
                LIMIT 10
            ''')
            
            summary['top_scorers'] = cursor.fetchall()
            
            return summary
    
    def get_current_squad_from_espn(self, team_name: str) -> List[str]:
        """Get current squad player names from ESPN API."""
        try:
            team_id = self.espn_team_ids.get(team_name)
            if not team_id:
                print(f"❌ No ESPN team ID for {team_name}")
                return []
            
            print(f"📡 Fetching current squad for {team_name} from ESPN...")
            roster_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/teams/{team_id}/roster"
            
            response = requests.get(roster_url, timeout=15)
            if response.status_code != 200:
                print(f"❌ ESPN API failed for {team_name}: {response.status_code}")
                return []
            
            data = response.json()
            athletes = data.get('athletes', [])
            
            if not athletes:
                print(f"❌ No athletes found for {team_name}")
                return []
            
            # Extract player names
            current_players = []
            for athlete in athletes:
                name = athlete.get('displayName', '').strip()
                if name:
                    current_players.append(name)
            
            print(f"✅ Found {len(current_players)} current players for {team_name}")
            return current_players
            
        except Exception as e:
            print(f"❌ Error fetching current squad for {team_name}: {e}")
            return []
    
    def update_current_squads(self):
        """Update database with current squad information."""
        print("🔄 Updating current squad data from ESPN...")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create current_squads table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS current_squads (
                    team_name TEXT,
                    player_name TEXT,
                    updated_at TEXT,
                    PRIMARY KEY (team_name, player_name)
                )
            ''')
            
            # Clear existing data
            cursor.execute("DELETE FROM current_squads")
            
            total_players = 0
            for team_name in self.espn_team_ids.keys():
                current_players = self.get_current_squad_from_espn(team_name)
                
                for player_name in current_players:
                    cursor.execute('''
                        INSERT OR REPLACE INTO current_squads 
                        (team_name, player_name, updated_at)
                        VALUES (?, ?, ?)
                    ''', (team_name, player_name, datetime.now().isoformat()))
                    total_players += 1
                
                # Respectful delay between API calls
                import time
                time.sleep(0.5)
            
            conn.commit()
            print(f"✅ Updated current squads: {total_players} players across {len(self.espn_team_ids)} teams")
    
    def get_current_player_betting_props(self, team_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Generate betting props only for players currently at the club."""
        print(f"🎯 Generating current player props for {team_name}...")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Debug: Show current squad for this team
            cursor.execute('SELECT player_name FROM current_squads WHERE team_name = ?', (team_name,))
            current_squad = [row[0] for row in cursor.fetchall()]
            print(f"🔍 Current {team_name} squad ({len(current_squad)} players): {current_squad[:5]}...")
            
            # Debug: Show historical players for this team
            cursor.execute('SELECT full_name FROM player_stats WHERE "Current Club" LIKE ?', (f'%{team_name}%',))
            historical_players = [row[0] for row in cursor.fetchall()]
            print(f"🔍 Historical {team_name} players ({len(historical_players)} players): {historical_players[:5]}...")
            
            # Get historical stats for players who are currently at the club
            cursor.execute('''
                SELECT ps.full_name, ps."Current Club", ps.position, ps.appearances_overall, 
                       ps.goals_overall, ps.assists_overall, ps.goals_per_90_overall, 
                       ps.assists_per_90_overall, ps.yellow_cards_overall, ps.red_cards_overall
                FROM player_stats ps
                INNER JOIN current_squads cs ON (
                    ps.full_name = cs.player_name AND 
                    ps."Current Club" LIKE ? AND 
                    cs.team_name = ?
                )
                WHERE ps.appearances_overall >= 10
                ORDER BY ps.goals_overall DESC, ps.assists_overall DESC, ps.appearances_overall DESC
                LIMIT ?
            ''', (f'%{team_name}%', team_name, limit))
            
            players = cursor.fetchall()
            
            if not players:
                print(f"❌ No exact name matches found. Trying fuzzy matching...")
                # Try fuzzy matching for common name variations
                fuzzy_players = self._get_fuzzy_matched_players(team_name, limit)
                if fuzzy_players:
                    players = fuzzy_players
                else:
                    print(f"❌ No current players found with historical data for {team_name}")
                    return []
            
            props = []
            for player_data in players:
                (name, team, position, apps, goals, assists, 
                 goals_per_90, assists_per_90, yellows, reds) = player_data
                
                # Generate props based on real statistics for current players only
                if goals_per_90 and goals_per_90 > 0.1:  # Only if player scores regularly
                    props.append({
                        'player_name': name,
                        'team': team,
                        'prop_type': 'Player Goals',
                        'description': 'To score anytime',
                        'model_prob': min(0.5, goals_per_90 * 2.5),
                        'confidence': 'High' if goals_per_90 > 0.3 else 'Medium',
                        'expected_value': f"${max(0, goals_per_90 * 20):.2f}",
                        'source': 'Current Squad + Historical Data (2018-19)',
                        'stats': f'{goals}G in {apps} apps (2018-19)',
                        'goals_per_90': goals_per_90,
                        'current_player': True
                    })
                
                if assists_per_90 and assists_per_90 > 0.05:  # Only if player assists regularly
                    props.append({
                        'player_name': name,
                        'team': team,
                        'prop_type': 'Player Assists',
                        'description': 'To get an assist',
                        'model_prob': min(0.4, assists_per_90 * 3),
                        'confidence': 'High' if assists_per_90 > 0.2 else 'Medium',
                        'expected_value': f"${max(0, assists_per_90 * 15):.2f}",
                        'source': 'Current Squad + Historical Data (2018-19)',
                        'stats': f'{assists}A in {apps} apps (2018-19)',
                        'assists_per_90': assists_per_90,
                        'current_player': True
                    })
            
            print(f"✅ Generated {len(props)} props for {len(players)} current {team_name} players")
            return props
    
    def _get_fuzzy_matched_players(self, team_name: str, limit: int) -> List:
        """Try to match players using fuzzy name matching."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all current squad players for this team
            cursor.execute('SELECT player_name FROM current_squads WHERE team_name = ?', (team_name,))
            current_players = [row[0] for row in cursor.fetchall()]
            
            # Get all historical players for this team
            cursor.execute('''
                SELECT full_name, "Current Club", position, appearances_overall, 
                       goals_overall, assists_overall, goals_per_90_overall, 
                       assists_per_90_overall, yellow_cards_overall, red_cards_overall
                FROM player_stats 
                WHERE "Current Club" LIKE ? AND appearances_overall >= 10
                ORDER BY goals_overall DESC, assists_overall DESC, appearances_overall DESC
            ''', (f'%{team_name}%',))
            
            historical_players = cursor.fetchall()
            
            matched_players = []
            for historical in historical_players:
                hist_name = historical[0]
                
                # Try various name matching strategies
                for current_name in current_players:
                    if self._names_match(hist_name, current_name):
                        print(f"🔗 Fuzzy match: '{hist_name}' (2018-19) ↔ '{current_name}' (current)")
                        matched_players.append(historical)
                        break
                
                if len(matched_players) >= limit:
                    break
            
            return matched_players
    
    def _names_match(self, name1: str, name2: str) -> bool:
        """Check if two player names likely refer to the same person."""
        # Normalize names
        n1 = name1.lower().strip()
        n2 = name2.lower().strip()
        
        # Exact match
        if n1 == n2:
            return True
        
        # Split into parts
        parts1 = n1.split()
        parts2 = n2.split()
        
        # Check if last names match and at least one first name/initial matches
        if len(parts1) >= 2 and len(parts2) >= 2:
            last1, last2 = parts1[-1], parts2[-1]
            if last1 == last2:
                # Check first names or initials
                first1, first2 = parts1[0], parts2[0]
                if first1 == first2 or first1.startswith(first2[0]) or first2.startswith(first1[0]):
                    return True
        
        # Check if one name is contained in the other (for nicknames)
        if len(n1) > 3 and len(n2) > 3:
            if n1 in n2 or n2 in n1:
                return True
        
        return False


def test_real_data_integrator():
    """Test the real data integrator."""
    print("🧪 Testing Real Data Integrator...")
    
    integrator = RealDataIntegrator()
    
    # Integrate all data
    integrator.integrate_all_data()
    
    # Get database summary
    summary = integrator.get_database_summary()
    
    print("\n📊 Database Summary:")
    for table, count in summary.items():
        if table != 'top_scorers':
            print(f"  {table}: {count} records")
    
    print("\n🏆 Top Scorers:")
    for scorer in summary['top_scorers']:
        name, team, goals, assists, apps, gpg = scorer
        print(f"  {name} ({team}): {goals}G, {assists}A in {apps} apps ({gpg:.2f} GPG)")
    
    # Test current squad integration
    print("\n🎯 Testing current squad integration:")
    
    # Update current squads from ESPN (this will take a moment)
    integrator.update_current_squads()
    
    print("\n🎯 Testing current player props for Arsenal:")
    current_props = integrator.get_current_player_betting_props("Arsenal", limit=5)
    if current_props:
        for prop in current_props:
            print(f"  ✅ {prop['player_name']}: {prop['prop_type']} - {prop['confidence']} ({prop['stats']})")
    else:
        print("  ❌ No current Arsenal players found with historical data")
    
    print("\n🎯 Comparing with old method (should show outdated players):")
    old_props = integrator.get_player_betting_props("Arsenal", limit=5)
    for prop in old_props:
        print(f"  ⚠️ {prop['player_name']}: {prop['prop_type']} - {prop['confidence']} ({prop['stats']})")
    
    return integrator


if __name__ == "__main__":
    test_real_data_integrator()

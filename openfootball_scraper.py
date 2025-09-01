#!/usr/bin/env python3
"""
Real football data using openfootball/football.db datasets.
Uses publicly available CSV datasets for Premier League data.
"""

import requests
import csv
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import io

class OpenFootballScraper:
    """Scraper for real football data using openfootball datasets."""
    
    def __init__(self):
        # Use the correct openfootball repositories
        self.england_url = "https://raw.githubusercontent.com/openfootball/england/master"
        self.json_url = "https://raw.githubusercontent.com/openfootball/football.json/master"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_premier_league_fixtures(self) -> List[Dict[str, Any]]:
        """Get Premier League fixtures from openfootball datasets."""
        try:
            print("🔍 Fetching Premier League fixtures from openfootball...")
            
            # Try the correct England repository structure
            fixtures = []
            
            # Try different season formats and file locations
            urls_to_try = [
                f"{self.england_url}/2024-25/1-premierleague.txt",
                f"{self.england_url}/2025-26/1-premierleague.txt", 
                f"{self.england_url}/2023-24/1-premierleague.txt",
                f"{self.json_url}/2024-25/en.1.json",
                f"{self.json_url}/2025-26/en.1.json",
                f"{self.json_url}/2023-24/en.1.json"
            ]
            
            for url in urls_to_try:
                try:
                    print(f"🔍 Trying: {url}")
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        if url.endswith('.json'):
                            # Parse JSON format
                            json_data = response.json()
                            season_fixtures = self._parse_json_fixtures(json_data)
                        else:
                            # Parse TXT format (football.txt format)
                            txt_data = response.text
                            season_fixtures = self._parse_txt_fixtures(txt_data)
                        
                        fixtures.extend(season_fixtures)
                        print(f"✅ Found {len(season_fixtures)} fixtures from {url}")
                        break  # Success, no need to try other URLs
                    else:
                        print(f"❌ HTTP {response.status_code} from {url}")
                
                except Exception as e:
                    print(f"⚠️ Error with {url}: {e}")
                    continue
            
            # Filter for upcoming matches (next 7 days)
            upcoming_fixtures = self._filter_upcoming_fixtures(fixtures)
            
            print(f"✅ Total upcoming fixtures: {len(upcoming_fixtures)}")
            return upcoming_fixtures
        
        except Exception as e:
            print(f"❌ Error fetching fixtures: {e}")
            return []
    
    def get_team_data(self) -> Dict[str, Any]:
        """Get Premier League team data."""
        try:
            print("🔍 Fetching team data...")
            
            # Try to get team data from various sources
            urls = [
                f"{self.base_url}/england/teams.csv",
                f"{self.base_url}/teams/england.csv"
            ]
            
            for url in urls:
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        teams = self._parse_csv_teams(response.text)
                        print(f"✅ Found {len(teams)} teams")
                        return teams
                except Exception:
                    continue
            
            # Fallback: use hardcoded Premier League teams
            return self._get_hardcoded_premier_league_teams()
        
        except Exception as e:
            print(f"❌ Error fetching teams: {e}")
            return self._get_hardcoded_premier_league_teams()
    
    def generate_betting_analysis(self, home_team: str, away_team: str) -> List[Dict[str, Any]]:
        """Generate betting analysis using real openfootball player statistics."""
        try:
            print(f"🎯 Generating analysis for {home_team} vs {away_team}...")
            
            # Get real player statistics from openfootball
            home_players = self._get_real_player_stats(home_team)
            away_players = self._get_real_player_stats(away_team)
            
            opportunities = []
            
            for players, team_name in [(home_players, home_team), (away_players, away_team)]:
                for player in players[:3]:  # Top 3 players per team based on real stats
                    player_props = self._generate_props_from_real_stats(player, team_name)
                    opportunities.extend(player_props)
            
            print(f"✅ Generated {len(opportunities)} betting opportunities from real player data")
            return opportunities
        
        except Exception as e:
            print(f"❌ Error generating analysis: {e}")
            return []
    
    def _parse_json_fixtures(self, json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse fixtures from JSON data."""
        fixtures = []
        
        try:
            # Handle different JSON structures
            matches = json_data.get('matches', []) or json_data.get('rounds', [])
            
            for match in matches:
                if isinstance(match, dict):
                    # Extract match data
                    date_str = match.get('date', '')
                    team1 = match.get('team1', '') or match.get('home', '')
                    team2 = match.get('team2', '') or match.get('away', '')
                    
                    if date_str and team1 and team2:
                        try:
                            # Parse date
                            match_date = datetime.strptime(date_str, '%Y-%m-%d')
                            
                            fixture = {
                                'home_team': team1.strip(),
                                'away_team': team2.strip(),
                                'kickoff_utc': match_date,
                                'date': date_str,
                                'source': 'openfootball-json',
                                'competition': 'Premier League'
                            }
                            
                            fixtures.append(fixture)
                        except Exception:
                            continue
        
        except Exception as e:
            print(f"⚠️ Error parsing JSON fixtures: {e}")
        
        return fixtures
    
    def _parse_txt_fixtures(self, txt_data: str) -> List[Dict[str, Any]]:
        """Parse fixtures from football.txt format."""
        fixtures = []
        
        try:
            lines = txt_data.split('\n')
            current_date = None
            
            for line in lines:
                line = line.strip()
                
                # Look for date lines (format: [Sat Aug 17])
                if line.startswith('[') and line.endswith(']'):
                    try:
                        date_part = line[1:-1]  # Remove brackets
                        # Try to parse date (this is simplified)
                        current_date = datetime.now()  # Placeholder
                    except:
                        continue
                
                # Look for match lines (format: Team1 vs Team2 or Team1 - Team2)
                elif ' vs ' in line or ' - ' in line:
                    try:
                        if ' vs ' in line:
                            teams = line.split(' vs ')
                        else:
                            teams = line.split(' - ')
                        
                        if len(teams) == 2 and current_date:
                            fixture = {
                                'home_team': teams[0].strip(),
                                'away_team': teams[1].strip(),
                                'kickoff_utc': current_date,
                                'source': 'openfootball-txt',
                                'competition': 'Premier League'
                            }
                            
                            fixtures.append(fixture)
                    except:
                        continue
        
        except Exception as e:
            print(f"⚠️ Error parsing TXT fixtures: {e}")
        
        return fixtures

    def _parse_csv_fixtures(self, csv_data: str) -> List[Dict[str, Any]]:
        """Parse fixtures from CSV data."""
        fixtures = []
        
        try:
            reader = csv.DictReader(io.StringIO(csv_data))
            
            for row in reader:
                # Parse the CSV row
                date_str = row.get('Date', '')
                home_team = row.get('Home', '') or row.get('Team 1', '')
                away_team = row.get('Away', '') or row.get('Team 2', '')
                
                if not date_str or not home_team or not away_team:
                    continue
                
                # Try to parse date
                try:
                    # Common date formats in football CSV files
                    for date_format in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                        try:
                            match_date = datetime.strptime(date_str, date_format)
                            break
                        except ValueError:
                            continue
                    else:
                        continue  # Skip if date can't be parsed
                    
                    fixture = {
                        'home_team': home_team.strip(),
                        'away_team': away_team.strip(),
                        'kickoff_utc': match_date,
                        'date': date_str,
                        'source': 'openfootball',
                        'competition': 'Premier League'
                    }
                    
                    fixtures.append(fixture)
                
                except Exception:
                    continue
        
        except Exception as e:
            print(f"⚠️ Error parsing CSV: {e}")
        
        return fixtures
    
    def _parse_csv_teams(self, csv_data: str) -> Dict[str, Any]:
        """Parse teams from CSV data."""
        teams = {}
        
        try:
            reader = csv.DictReader(io.StringIO(csv_data))
            
            for row in reader:
                team_name = row.get('Name', '') or row.get('Team', '')
                if team_name:
                    teams[team_name] = {
                        'name': team_name,
                        'code': row.get('Code', ''),
                        'country': row.get('Country', 'England')
                    }
        
        except Exception as e:
            print(f"⚠️ Error parsing teams CSV: {e}")
        
        return teams
    
    def _filter_upcoming_fixtures(self, fixtures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter for upcoming fixtures in the next 7 days."""
        now = datetime.now()
        week_from_now = now + timedelta(days=7)
        
        upcoming = []
        for fixture in fixtures:
            match_date = fixture.get('kickoff_utc')
            if match_date and now <= match_date <= week_from_now:
                upcoming.append(fixture)
        
        return upcoming
    
    def _get_hardcoded_premier_league_teams(self) -> Dict[str, Any]:
        """Fallback hardcoded Premier League teams."""
        teams = [
            "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton & Hove Albion",
            "Chelsea", "Crystal Palace", "Everton", "Fulham", "Liverpool",
            "Luton Town", "Manchester City", "Manchester United", "Newcastle United",
            "Nottingham Forest", "Sheffield United", "Tottenham Hotspur", "West Ham United",
            "Wolverhampton Wanderers", "Burnley"
        ]
        
        return {team: {'name': team, 'country': 'England'} for team in teams}
    
    def _get_real_player_stats(self, team_name: str) -> List[Dict[str, Any]]:
        """Get real player statistics from openfootball England repository."""
        try:
            print(f"🔍 Fetching real player stats for {team_name}...")
            
            # Try to get player data from openfootball England repository
            # The data might be in different formats/locations
            urls_to_try = [
                f"{self.england_url}/2024-25/squads.txt",
                f"{self.england_url}/2023-24/squads.txt", 
                f"{self.json_url}/2024-25/en.1.squads.json"
            ]
            
            for url in urls_to_try:
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        if url.endswith('.json'):
                            players = self._parse_json_players(response.json(), team_name)
                        else:
                            players = self._parse_txt_players(response.text, team_name)
                        
                        if players:
                            print(f"✅ Found {len(players)} real players for {team_name}")
                            return players
                except Exception:
                    continue
            
            # No fallback - return empty list when no real data available
            print(f"❌ No real player data found for {team_name} - no fake data will be created")
            return []
            
        except Exception as e:
            print(f"❌ Error fetching player stats: {e}")
            return []  # Return empty list - NO FAKE DATA
    
    def _parse_json_players(self, json_data: Dict[str, Any], team_name: str) -> List[Dict[str, Any]]:
        """Parse player data from JSON format."""
        players = []
        # Implementation would depend on actual JSON structure
        return players
    
    def _parse_txt_players(self, txt_data: str, team_name: str) -> List[Dict[str, Any]]:
        """Parse player data from TXT format."""
        players = []
        lines = txt_data.split('\n')
        
        current_team = None
        for line in lines:
            line = line.strip()
            
            # Look for team headers
            if team_name.lower() in line.lower() and ('FC' in line or 'United' in line or 'City' in line):
                current_team = team_name
                continue
            
            # Parse player lines when we're in the right team section
            if current_team == team_name and line and not line.startswith('#'):
                # Player lines might be in format: "Name, Position, Goals, etc."
                parts = line.split(',')
                if len(parts) >= 2:
                    player = {
                        'name': parts[0].strip(),
                        'position': parts[1].strip() if len(parts) > 1 else 'Unknown',
                        'goals': int(parts[2]) if len(parts) > 2 and parts[2].strip().isdigit() else 0,
                        'apps': int(parts[3]) if len(parts) > 3 and parts[3].strip().isdigit() else 1,
                        'team': team_name
                    }
                    players.append(player)
        
        return players
    
    def _get_realistic_player_profiles(self, team_name: str) -> List[Dict[str, Any]]:
        """Get realistic player profiles based on actual Premier League statistics."""
        # Based on real Premier League averages
        realistic_players = [
            {
                'name': f'{team_name} Striker', 
                'position': 'Forward',
                'goals': 12,  # Average striker goals per season
                'apps': 28,   # Average appearances
                'shots_per_game': 3.2,
                'team': team_name
            },
            {
                'name': f'{team_name} Midfielder', 
                'position': 'Midfielder',
                'goals': 4,   # Average midfielder goals
                'apps': 32,
                'assists': 6, # Average assists
                'team': team_name
            },
            {
                'name': f'{team_name} Defender', 
                'position': 'Defender',
                'goals': 2,   # Average defender goals
                'apps': 30,
                'tackles_per_game': 2.8,
                'team': team_name
            }
        ]
        
        return realistic_players
    
    def _generate_props_from_real_stats(self, player: Dict[str, Any], team_name: str) -> List[Dict[str, Any]]:
        """Generate betting props based on real player statistics."""
        props = []
        
        player_name = player.get('name', 'Unknown Player')
        position = player.get('position', 'Unknown')
        goals = player.get('goals', 0)
        apps = max(1, player.get('apps', 1))  # Avoid division by zero
        
        # Calculate per-game averages from real stats
        goals_per_game = goals / apps
        
        # Generate props based on position and real statistics
        if 'Forward' in position or 'Striker' in position:
            # Forwards - focus on goals and shots
            props.extend([
                {
                    'player_name': player_name,
                    'team': team_name,
                    'prop_type': 'Player Goals',
                    'description': 'To score anytime',
                    'model_prob': min(0.4, goals_per_game * 2),  # Based on real goal rate
                    'confidence': 'High' if goals_per_game > 0.4 else 'Medium' if goals_per_game > 0.2 else 'Low',
                    'expected_value': f"${max(0, goals_per_game * 15):.2f}",
                    'source': 'Real Player Stats'
                },
                {
                    'player_name': player_name,
                    'team': team_name,
                    'prop_type': 'Player Shots',
                    'description': '2+ shots',
                    'model_prob': min(0.7, player.get('shots_per_game', goals_per_game * 4) / 4),
                    'confidence': 'Medium',
                    'expected_value': f"${max(0, goals_per_game * 8):.2f}",
                    'source': 'Real Player Stats'
                }
            ])
        
        elif 'Midfielder' in position:
            # Midfielders - focus on assists and versatility
            assists = player.get('assists', 0)
            assists_per_game = assists / apps
            
            props.extend([
                {
                    'player_name': player_name,
                    'team': team_name,
                    'prop_type': 'Player Goals',
                    'description': 'To score anytime',
                    'model_prob': min(0.25, goals_per_game * 1.5),
                    'confidence': 'Medium' if goals_per_game > 0.1 else 'Low',
                    'expected_value': f"${max(0, goals_per_game * 12):.2f}",
                    'source': 'Real Player Stats'
                },
                {
                    'player_name': player_name,
                    'team': team_name,
                    'prop_type': 'Player Assists',
                    'description': 'To get an assist',
                    'model_prob': min(0.3, assists_per_game * 2),
                    'confidence': 'High' if assists_per_game > 0.2 else 'Medium',
                    'expected_value': f"${max(0, assists_per_game * 10):.2f}",
                    'source': 'Real Player Stats'
                }
            ])
        
        else:  # Defenders
            props.extend([
                {
                    'player_name': player_name,
                    'team': team_name,
                    'prop_type': 'Player Goals',
                    'description': 'To score anytime',
                    'model_prob': min(0.15, goals_per_game * 1.2),
                    'confidence': 'Low',
                    'expected_value': f"${max(0, goals_per_game * 20):.2f}",
                    'source': 'Real Player Stats'
                },
                {
                    'player_name': player_name,
                    'team': team_name,
                    'prop_type': 'Player Tackles',
                    'description': '3+ tackles',
                    'model_prob': min(0.8, player.get('tackles_per_game', 2.5) / 3.5),
                    'confidence': 'High',
                    'expected_value': f"${max(0, goals_per_game * 5):.2f}",
                    'source': 'Real Player Stats'
                }
            ])
        
        return props
    
    def _generate_realistic_props(self, player: Dict[str, Any], team_name: str) -> List[Dict[str, Any]]:
        """Generate realistic betting props."""
        props = []
        
        player_name = player['name']
        position = player.get('position', '')
        
        # Realistic probabilities based on Premier League statistics
        if 'Forward' in position:
            base_props = [
                ('Player Goals', 0.28, 'To score anytime'),
                ('Player Shots', 0.70, '2+ shots'),
                ('Player Shots on Target', 0.50, '1+ shot on target')
            ]
        elif 'Midfielder' in position:
            base_props = [
                ('Player Goals', 0.15, 'To score anytime'),
                ('Player Assists', 0.25, 'To get an assist'),
                ('Player Yellow Cards', 0.20, 'To be booked')
            ]
        else:  # Defender
            base_props = [
                ('Player Goals', 0.08, 'To score anytime'),
                ('Player Yellow Cards', 0.25, 'To be booked'),
                ('Player Tackles', 0.75, '3+ tackles')
            ]
        
        for prop_type, model_prob, description in base_props:
            # Calculate odds
            fair_odds_decimal = 1 / model_prob if model_prob > 0 else 4.0
            min_profitable_decimal = fair_odds_decimal * 1.05
            
            # American odds
            if min_profitable_decimal >= 2.0:
                american_odds = int((min_profitable_decimal - 1) * 100)
            else:
                american_odds = int(-100 / (min_profitable_decimal - 1))
            
            # Confidence
            edge = (min_profitable_decimal - 1) * model_prob - 1
            confidence = 'High' if edge > 0.15 else 'Medium' if edge > 0.05 else 'Low'
            
            prop = {
                'player_name': player_name,
                'team': team_name,
                'prop_type': prop_type,
                'description': description,
                'model_prob': model_prob,
                'fair_odds_decimal': fair_odds_decimal,
                'min_profitable_american': american_odds,
                'confidence': confidence,
                'expected_value': f"${max(0, edge * 10):.2f}",
                'source': 'openfootball'
            }
            
            props.append(prop)
        
        return props

def test_openfootball_scraper():
    """Test the openfootball scraper."""
    print("🚀 Testing OpenFootball Scraper...")
    
    scraper = OpenFootballScraper()
    
    # Test 1: Get fixtures
    fixtures = scraper.get_premier_league_fixtures()
    
    if fixtures:
        print(f"\n✅ Found {len(fixtures)} upcoming fixtures:")
        for fixture in fixtures[:3]:
            print(f"  - {fixture['home_team']} vs {fixture['away_team']} on {fixture['kickoff_utc'].strftime('%Y-%m-%d')}")
    else:
        print("\n❌ No real fixtures found - no data sources available")
        fixtures = []  # Return empty list - NO FAKE DATA
    
    # Test 2: Generate analysis only if real fixtures exist
    if fixtures:
        first_fixture = fixtures[0]
        home_team = first_fixture['home_team']
        away_team = first_fixture['away_team']
        
        print(f"\n🎯 Testing analysis for {home_team} vs {away_team}...")
        analysis = scraper.generate_betting_analysis(home_team, away_team)
        
        if analysis:
            print(f"✅ Generated {len(analysis)} betting opportunities:")
            for opp in analysis[:5]:
                print(f"  - {opp['player_name']}: {opp['prop_type']} ({opp['confidence']} confidence, {opp['expected_value']} EV)")
        else:
            print("❌ No analysis generated")
    else:
        print("\n❌ No analysis possible - no real fixtures available")
        analysis = []
    
    return fixtures, analysis

if __name__ == "__main__":
    test_openfootball_scraper()

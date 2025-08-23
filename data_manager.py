#!/usr/bin/env python3
"""
📊 CSV Data Manager - Simple, reliable data storage using CSV files
No database complexity - just fast CSV read/write operations
"""
import csv
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

class CSVDataManager:
    """Manage match data and analysis using CSV files."""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        self.matches_file = self.data_dir / "matches.csv"
        self.analysis_file = self.data_dir / "analysis.csv"
        self.players_file = self.data_dir / "players.csv"
    
    def store_matches(self, matches):
        """Store match list to CSV with incremental match IDs."""
        print(f"💾 Storing {len(matches)} matches to CSV with IDs...")
        
        # Get the next match ID
        next_match_id = self._get_next_match_id()
        
        with open(self.matches_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['match_id', 'home_team', 'away_team', 'league', 'kickoff_time', 'stored_at'])
            
            for i, match in enumerate(matches):
                match_id = next_match_id + i
                writer.writerow([
                    match_id,
                    match.get('home_team', ''),
                    match.get('away_team', ''),
                    match.get('league', ''),
                    match.get('kickoff_full', ''),
                    datetime.now().isoformat()
                ])
        
        print(f"✅ Matches stored to {self.matches_file} with IDs {next_match_id}-{next_match_id + len(matches) - 1}")
    
    def _get_next_match_id(self):
        """Get the next available match ID."""
        if not self.matches_file.exists():
            return 1  # Start from 1
        
        try:
            with open(self.matches_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                max_id = 0
                for row in reader:
                    match_id = int(row.get('match_id', 0))
                    max_id = max(max_id, match_id)
                return max_id + 1
        except Exception as e:
            print(f"⚠️ Error getting next match ID: {e}")
            return 1
    
    def get_match_id(self, home_team, away_team):
        """Get match ID for given teams."""
        if not self.matches_file.exists():
            return None
        
        try:
            with open(self.matches_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if (row['home_team'] == home_team and 
                        row['away_team'] == away_team):
                        return int(row['match_id'])
            return None
        except Exception as e:
            print(f"❌ Error getting match ID: {e}")
            return None
    
    def get_matches(self):
        """Get matches from CSV with match IDs."""
        if not self.matches_file.exists():
            print("⚠️ No matches CSV found")
            return []
        
        matches = []
        try:
            with open(self.matches_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Parse kickoff time properly
                    kickoff_full = row['kickoff_time']
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(kickoff_full.replace('Z', '+00:00'))
                        kickoff_short = dt.strftime('%H:%M')
                        
                        # Calculate time until match
                        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
                        time_diff = dt - now
                        
                        if time_diff.total_seconds() > 0:
                            hours = int(time_diff.total_seconds() // 3600)
                            minutes = int((time_diff.total_seconds() % 3600) // 60)
                            if hours > 0:
                                time_until = f"in {hours}h {minutes}m"
                            else:
                                time_until = f"in {minutes}m"
                        else:
                            time_until = "Live/Finished"
                            
                    except Exception as e:
                        print(f"⚠️ Error parsing time for {row['home_team']} vs {row['away_team']}: {e}")
                        kickoff_short = kickoff_full[:5] if kickoff_full else 'TBD'
                        time_until = 'TBD'
                    
                    matches.append({
                        'id': f"match-{row['match_id']}-csv",
                        'match_id': int(row['match_id']),
                        'home_team': row['home_team'],
                        'away_team': row['away_team'],
                        'league': row['league'],
                        'kickoff': kickoff_short,
                        'kickoff_full': kickoff_full,
                        'time_until': time_until,
                        'data_source': 'CSV_CACHED'
                    })
            
            print(f"⚡ Loaded {len(matches)} matches from CSV")
            return matches
            
        except Exception as e:
            print(f"❌ Error reading matches CSV: {e}")
            return []
    
    def store_analysis(self, home_team, away_team, analysis_data):
        """Store analysis result to CSV using match ID reference."""
        print(f"💾 Storing analysis for {home_team} vs {away_team}...")
        
        # Get match ID for these teams
        match_id = self.get_match_id(home_team, away_team)
        if match_id is None:
            print(f"❌ No match ID found for {home_team} vs {away_team}")
            return False
        
        # Get next analysis ID
        analysis_id = self._get_next_analysis_id()
        
        # Store analysis as JSON string in CSV
        analysis_json = json.dumps(analysis_data, default=str)
        
        # Check if file exists to determine if we need headers
        file_exists = self.analysis_file.exists()
        
        with open(self.analysis_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if not file_exists:
                writer.writerow(['analysis_id', 'match_id', 'analysis_data', 'generated_at'])
            
            writer.writerow([
                analysis_id,
                match_id,
                analysis_json,
                datetime.now().isoformat()
            ])
        
        print(f"✅ Analysis stored for {home_team} vs {away_team} (Match ID: {match_id}, Analysis ID: {analysis_id})")
        return True
    
    def _get_next_analysis_id(self):
        """Get the next available analysis ID."""
        if not self.analysis_file.exists():
            return 1  # Start from 1
        
        try:
            with open(self.analysis_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                max_id = 0
                for row in reader:
                    analysis_id = int(row.get('analysis_id', 0))
                    max_id = max(max_id, analysis_id)
                return max_id + 1
        except Exception as e:
            print(f"⚠️ Error getting next analysis ID: {e}")
            return 1
    
    def get_analysis(self, home_team, away_team):
        """Get analysis from CSV using match ID lookup."""
        if not self.analysis_file.exists():
            print(f"⚠️ No analysis CSV found for {home_team} vs {away_team}")
            return None
        
        # First get the match ID
        match_id = self.get_match_id(home_team, away_team)
        if match_id is None:
            print(f"❌ No match ID found for {home_team} vs {away_team}")
            return None
        
        try:
            with open(self.analysis_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Find most recent analysis for this match ID
                latest_analysis = None
                latest_time = None
                
                for row in reader:
                    if int(row['match_id']) == match_id:
                        generated_at = datetime.fromisoformat(row['generated_at'])
                        if latest_time is None or generated_at > latest_time:
                            latest_time = generated_at
                            latest_analysis = json.loads(row['analysis_data'])
                            latest_analysis['generated_at'] = row['generated_at']
                            latest_analysis['analysis_id'] = int(row['analysis_id'])
                            latest_analysis['match_id'] = match_id
                
                if latest_analysis:
                    print(f"⚡ Found cached analysis for {home_team} vs {away_team} (Match ID: {match_id})")
                    return latest_analysis
                else:
                    print(f"❌ No analysis found for {home_team} vs {away_team} (Match ID: {match_id})")
                    return None
                    
        except Exception as e:
            print(f"❌ Error reading analysis CSV: {e}")
            return None
    
    def store_players(self, team_name, players_data):
        """Store player data to CSV."""
        print(f"👥 Storing {len(players_data)} players for {team_name}...")
        
        # Check if file exists to determine if we need headers
        file_exists = self.players_file.exists()
        
        with open(self.players_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if not file_exists:
                writer.writerow(['team', 'player_name', 'shirt_number', 'position', 
                               'apps', 'shots_pg', 'sot_pg', 'fouls_pg', 'yc_pg', 
                               'goals_pg', 'assists_pg', 'stored_at'])
            
            for player in players_data:
                writer.writerow([
                    team_name,
                    player.get('player_name', ''),
                    player.get('shirt_number', 0),
                    player.get('position', ''),
                    player.get('apps', 0),
                    player.get('shots_pg', 0),
                    player.get('sot_pg', 0),
                    player.get('fouls_pg', 0),
                    player.get('yc_pg', 0),
                    player.get('goals_pg', 0),
                    player.get('assists_pg', 0),
                    datetime.now().isoformat()
                ])
        
        print(f"✅ Players stored for {team_name}")
    
    def is_analysis_fresh(self, analysis, max_age_hours=6):
        """Check if analysis is fresh enough."""
        if not analysis or 'generated_at' not in analysis:
            return False
        
        try:
            generated_time = datetime.fromisoformat(analysis['generated_at'])
            age_hours = (datetime.now() - generated_time).total_seconds() / 3600
            return age_hours < max_age_hours
        except:
            return False
    
    def cleanup_old_data(self, days_to_keep=1):
        """Clean up old CSV data."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # For simplicity, we can just recreate files or implement cleanup logic
        print(f"🗑️ Cleanup would remove data older than {days_to_keep} days")
        # Implementation can be added if needed

if __name__ == "__main__":
    # Test the CSV manager
    manager = CSVDataManager()
    
    # Test match storage
    test_matches = [
        {'home_team': 'Arsenal', 'away_team': 'Leeds United', 'league': 'Premier League', 'kickoff_full': '2025-08-23T16:30:00'}
    ]
    
    manager.store_matches(test_matches)
    retrieved_matches = manager.get_matches()
    print(f"✅ Test successful: {len(retrieved_matches)} matches retrieved")

#!/usr/bin/env python3
"""
🗄️ Bettor Database - Store match analysis results
"""
import sqlite3
import json
from datetime import datetime, timezone
import os

class BettorDatabase:
    """Database manager for storing betting analysis results."""
    
    def __init__(self, db_path="bettor.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS matches (
                    id TEXT PRIMARY KEY,
                    home_team TEXT NOT NULL,
                    away_team TEXT NOT NULL,
                    league TEXT NOT NULL,
                    league_id TEXT NOT NULL,
                    kickoff_time TEXT NOT NULL,
                    venue TEXT,
                    status TEXT,
                    created_at TEXT NOT NULL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id TEXT NOT NULL,
                    analysis_data TEXT NOT NULL,
                    total_opportunities INTEGER,
                    expected_profit REAL,
                    expected_roi REAL,
                    total_stake REAL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (match_id) REFERENCES matches (id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS betting_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id INTEGER NOT NULL,
                    player_name TEXT NOT NULL,
                    team TEXT NOT NULL,
                    market TEXT NOT NULL,
                    threshold REAL,
                    odds_american INTEGER,
                    odds_decimal REAL,
                    model_probability REAL,
                    edge_percent REAL,
                    kelly_percent REAL,
                    recommended_stake REAL,
                    potential_profit REAL,
                    confidence TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (analysis_id) REFERENCES analysis_results (id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE NOT NULL,
                    total_matches INTEGER,
                    total_opportunities INTEGER,
                    avg_expected_roi REAL,
                    total_potential_profit REAL,
                    leagues_analyzed TEXT,
                    created_at TEXT NOT NULL
                )
            ''')
    
    def store_match(self, match_data):
        """Store match information."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO matches 
                (id, home_team, away_team, league, league_id, kickoff_time, venue, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                match_data['id'],
                match_data['home_team'],
                match_data['away_team'],
                match_data['league'],
                match_data['league_id'],
                match_data['kickoff_full'],
                match_data.get('venue', ''),
                match_data['status'],
                datetime.now(timezone.utc).isoformat()
            ))
    
    def store_analysis(self, match_id, analysis_data):
        """Store complete analysis results."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Store main analysis
            cursor.execute('''
                INSERT INTO analysis_results 
                (match_id, analysis_data, total_opportunities, expected_profit, expected_roi, total_stake, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                match_id,
                json.dumps(analysis_data),
                analysis_data['summary']['total_opportunities'],
                analysis_data['summary']['expected_profit'],
                analysis_data['summary']['expected_roi_percent'],
                analysis_data['summary']['total_stake_recommended'],
                datetime.now(timezone.utc).isoformat()
            ))
            
            analysis_id = cursor.lastrowid
            
            # Store individual betting signals
            for bet in analysis_data['all_bets']:
                cursor.execute('''
                    INSERT INTO betting_signals 
                    (analysis_id, player_name, team, market, threshold, odds_american, odds_decimal,
                     model_probability, edge_percent, kelly_percent, recommended_stake, 
                     potential_profit, confidence, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    analysis_id,
                    bet['player'],
                    bet['team'],
                    bet['market'],
                    bet.get('threshold', 0),
                    bet['odds_american'],
                    bet['odds_decimal'],
                    bet['model_probability_percent'] / 100,
                    bet['edge_percent'],
                    bet['kelly_percent'],
                    bet['recommended_stake_dollars'],
                    bet['potential_profit_dollars'],
                    bet['confidence'],
                    datetime.now(timezone.utc).isoformat()
                ))
            
            return analysis_id
    
    def get_analysis_by_match(self, match_id):
        """Retrieve analysis for a specific match."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT analysis_data FROM analysis_results 
                WHERE match_id = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            ''', (match_id,))
            
            result = cursor.fetchone()
            if result:
                return json.loads(result[0])
            return None
    
    def get_matches_by_date(self, date_str):
        """Get all matches for a specific date."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT m.*, ar.total_opportunities, ar.expected_profit, ar.expected_roi
                FROM matches m
                LEFT JOIN analysis_results ar ON m.id = ar.match_id
                WHERE date(m.kickoff_time) = ?
                ORDER BY m.kickoff_time
            ''', (date_str,))
            
            return cursor.fetchall()
    
    def get_recent_analyses(self, limit=50):
        """Get recent analysis results."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT m.home_team, m.away_team, m.league, m.kickoff_time,
                       ar.total_opportunities, ar.expected_profit, ar.expected_roi, ar.created_at
                FROM analysis_results ar
                JOIN matches m ON ar.match_id = m.id
                ORDER BY ar.created_at DESC
                LIMIT ?
            ''', (limit,))
            
            return cursor.fetchall()
    
    def create_daily_summary(self, date_str):
        """Create summary for a specific date."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(DISTINCT m.id) as total_matches,
                    COUNT(ar.id) as total_analyses,
                    SUM(ar.total_opportunities) as total_opportunities,
                    AVG(ar.expected_roi) as avg_roi,
                    SUM(ar.expected_profit) as total_profit,
                    GROUP_CONCAT(DISTINCT m.league) as leagues
                FROM matches m
                LEFT JOIN analysis_results ar ON m.id = ar.match_id
                WHERE date(m.kickoff_time) = ?
            ''', (date_str,))
            
            result = cursor.fetchone()
            
            if result and result[0] > 0:
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_summaries
                    (date, total_matches, total_opportunities, avg_expected_roi, 
                     total_potential_profit, leagues_analyzed, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    date_str,
                    result[0] or 0,
                    result[2] or 0,
                    result[3] or 0,
                    result[4] or 0,
                    result[5] or '',
                    datetime.now(timezone.utc).isoformat()
                ))
                
                return {
                    'date': date_str,
                    'total_matches': result[0] or 0,
                    'total_opportunities': result[2] or 0,
                    'avg_expected_roi': result[3] or 0,
                    'total_potential_profit': result[4] or 0,
                    'leagues': result[5].split(',') if result[5] else []
                }
        
        return None
    
    def get_database_stats(self):
        """Get overall database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total matches analyzed
            cursor.execute('SELECT COUNT(*) FROM matches')
            stats['total_matches'] = cursor.fetchone()[0]
            
            # Total analyses
            cursor.execute('SELECT COUNT(*) FROM analysis_results')
            stats['total_analyses'] = cursor.fetchone()[0]
            
            # Total opportunities
            cursor.execute('SELECT SUM(total_opportunities) FROM analysis_results')
            result = cursor.fetchone()
            stats['total_opportunities'] = result[0] if result[0] else 0
            
            # Average ROI
            cursor.execute('SELECT AVG(expected_roi) FROM analysis_results WHERE expected_roi > 0')
            result = cursor.fetchone()
            stats['avg_roi'] = result[0] if result[0] else 0
            
            # Unique leagues
            cursor.execute('SELECT COUNT(DISTINCT league) FROM matches')
            stats['unique_leagues'] = cursor.fetchone()[0]
            
            return stats

    def cleanup_old_data(self, days_to_keep=7):
        """Clean up old data to keep database size manageable."""
        from datetime import timedelta
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days_to_keep)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Delete old betting signals
            conn.execute('''
                DELETE FROM betting_signals 
                WHERE created_at < ?
            ''', (cutoff_date,))
            
            # Delete old analysis results
            conn.execute('''
                DELETE FROM analysis_results 
                WHERE created_at < ?
            ''', (cutoff_date,))
            
            # Keep matches but clean up very old ones
            very_old_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            conn.execute('''
                DELETE FROM matches 
                WHERE created_at < ?
            ''', (very_old_date,))
            
            print(f"🗑️ Cleaned up data older than {days_to_keep} days")

if __name__ == "__main__":
    # Test database functionality
    db = BettorDatabase()
    stats = db.get_database_stats()
    print("📊 Database Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

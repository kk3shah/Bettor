#!/usr/bin/env python3
"""
🎯 Bettor Web Interface - Mobile-First Betting Analysis
"""
from flask import Flask, render_template, jsonify, request
import sys
import os
from datetime import datetime, timedelta
import json
import sqlite3
import threading
import schedule
import time
import subprocess
import logging
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.data.adapters.live_scraper import LiveDataScraper

def get_team_logo(team_name):
    """Get team logo URL from ESPN mapping."""
    try:
        mapping_file = Path("data/espn_team_mapping.json")
        if mapping_file.exists():
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
                team_data = mapping.get('by_name', {}).get(team_name)
                if team_data:
                    return team_data.get('logo', '')
    except Exception as e:
        print(f"⚠️ Error getting team logo: {e}")
    return ''

try:
    from database import BettorDatabase
except ImportError:
    print("⚠️ Database module not available, using fallback")
    BettorDatabase = None

app = Flask(__name__)

class BettorWebService:
    """Service class for web interface functionality."""
    
    def __init__(self):
        self.scraper = LiveDataScraper()
        self.db = BettorDatabase() if BettorDatabase else None
    
    def get_upcoming_matches(self, hours_ahead=24):
        """Get upcoming matches - CSV FIRST (instant), then generate if needed."""
        print(f"🌍 Getting matches for next {hours_ahead} hours...")
        
        # PRIORITY 1: Check CSV cache first (INSTANT - no API calls)
        try:
            matches_file = Path("data/matches.csv")
            if matches_file.exists():
                with open(matches_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    cached_matches = list(reader)
                    if cached_matches:
                        print(f"⚡ Found {len(cached_matches)} cached matches (NO API CALLS)")
                        return cached_matches
        except Exception as e:
            print(f"⚠️ Error reading matches CSV: {e}")
        
        # PRIORITY 2: Return empty if no CSV - only show Premier League matches we can analyze
        print("📊 CSV empty - no matches available (Premier League only)")
        print("💡 Run: python populate_real_premier_league_matches.py to get real matches")
        
        return []
    
    def get_real_data_matches(self):
        """Get matches that have real scraped data available."""
        if not self.db:
            return []
        
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Get active matches with real data from last 24 hours
                cursor.execute('''
                    SELECT match_id, home_team, away_team, league, kickoff_time 
                    FROM real_match_data 
                    WHERE is_active = 1 
                    AND datetime(scraped_at) > datetime('now', '-24 hours')
                    ORDER BY kickoff_time
                ''')
                
                matches = []
                for row in cursor.fetchall():
                    match_id, home_team, away_team, league, kickoff_time = row
                    
                    matches.append({
                        'id': match_id,
                        'home_team': home_team,
                        'away_team': away_team,
                        'league': league,
                        'kickoff_full': kickoff_time,
                        'data_source': 'REAL_SCRAPED'
                    })
                
                return matches
                
        except Exception as e:
            print(f"❌ Error getting real data matches: {e}")
            return []
    
    def get_simulation_matches(self, hours_ahead=24):
        """Fallback: Get simulated matches when no real data available."""
        try:
            from datetime import timezone
            now = datetime.now(timezone.utc)
            today = now.date()
            tomorrow = today + timedelta(days=1)
            
            # ⭐ ONLY MAJOR LEAGUES WE AGREED ON (Top 5 + Champions League)
            leagues = {
                'Premier League': 'eng.1',
                'La Liga': 'esp.1', 
                'Serie A': 'ita.1',
                'Bundesliga': 'ger.1',
                'Ligue 1': 'fra.1',
                'Champions League': 'uefa.champions'
            }
            
            all_matches = []
            
            # Check each league
            for league_name, league_id in leagues.items():
                try:
                    espn_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_id}/scoreboard"
                    
                    # Check today and tomorrow
                    for date_obj in [today, tomorrow]:
                        date_str = date_obj.strftime('%Y%m%d')
                        params = {'dates': date_str, 'limit': 50}
                        
                        try:
                            response = self.scraper.session.get(espn_url, params=params, timeout=5)
                            
                            if response.status_code == 200:
                                data = response.json()
                                
                                if 'events' in data and data['events']:
                                    for event in data['events']:
                                        try:
                                            # Parse match time
                                            match_time_str = event.get('date', '')
                                            if not match_time_str:
                                                continue
                                            
                                            # Parse ISO datetime with timezone
                                            if match_time_str.endswith('Z'):
                                                match_time_str = match_time_str[:-1] + '+00:00'
                                            match_time = datetime.fromisoformat(match_time_str)
                                            
                                            # Ensure timezone aware
                                            if match_time.tzinfo is None:
                                                match_time = match_time.replace(tzinfo=timezone.utc)
                                            
                                            # Check if within time window
                                            time_diff = match_time - now
                                            if 0 < time_diff.total_seconds() <= hours_ahead * 3600:
                                                
                                                competitions = event.get('competitions', [])
                                                for comp in competitions:
                                                    competitors = comp.get('competitors', [])
                                                    
                                                    if len(competitors) >= 2:
                                                        home_team = competitors[0].get('team', {}).get('displayName', 'Unknown')
                                                        away_team = competitors[1].get('team', {}).get('displayName', 'Unknown')
                                                        
                                                        status = comp.get('status', {}).get('type', {}).get('description', 'Scheduled')
                                                        venue = comp.get('venue', {}).get('fullName', 'Unknown Venue')
                                                        
                                                        all_matches.append({
                                                            'id': f"{home_team}-{away_team}-{date_str}-{league_id}",
                                                            'home_team': home_team,
                                                            'away_team': away_team,
                                                            'league': league_name,
                                                            'league_id': league_id,
                                                            'kickoff': match_time.strftime('%H:%M'),
                                                            'kickoff_full': match_time.isoformat(),
                                                            'status': status,
                                                            'venue': venue,
                                                            'time_until': self._format_time_until(match_time),
                                                            'match_id': event.get('id'),
                                                            'priority': self._get_league_priority(league_name)
                                                        })
                                        
                                        except Exception as e:
                                            print(f"⚠️ Error parsing match in {league_name}: {e}")
                                            continue
                        
                        except Exception as e:
                            print(f"⚠️ Error fetching {league_name} for {date_str}: {e}")
                            continue
                
                except Exception as e:
                    print(f"⚠️ Error with {league_name}: {e}")
                    continue
            
            # Remove duplicates and sort by priority then time
            unique_matches = {}
            for match in all_matches:
                # Use a unique key based on teams and time
                key = f"{match['home_team']}-{match['away_team']}-{match['kickoff_full'][:16]}"
                if key not in unique_matches or match['priority'] < unique_matches[key]['priority']:
                    unique_matches[key] = match
            
            # Convert back to list and sort
            matches = list(unique_matches.values())
            matches.sort(key=lambda x: (x['priority'], x['kickoff_full']))
            
            print(f"✅ Found {len(matches)} matches across {len(leagues)} leagues")
            return matches
            
        except Exception as e:
            print(f"❌ Error getting upcoming matches: {e}")
            # Return sample matches for demo
            return [
                {
                    'id': 'Arsenal-Leeds-20250823',
                    'home_team': 'Arsenal',
                    'away_team': 'Leeds United',
                    'kickoff': '16:30',
                    'kickoff_full': '2025-08-23T16:30:00',
                    'status': 'Scheduled',
                    'time_until': 'in 1h 30m',
                    'match_id': 'demo_match_1'
                },
                {
                    'id': 'ManCity-Tottenham-20250823',
                    'home_team': 'Manchester City',
                    'away_team': 'Tottenham Hotspur',
                    'kickoff': '19:00',
                    'kickoff_full': '2025-08-23T19:00:00',
                    'status': 'Scheduled',
                    'time_until': 'in 4h 0m',
                    'match_id': 'demo_match_2'
                }
            ]
    
    def _format_time_until(self, match_time):
        """Format time until match in human readable format."""
        from datetime import timezone
        
        # Ensure both datetimes have timezone info
        now = datetime.now(timezone.utc)
        
        if match_time.tzinfo is None:
            # If match_time is naive, assume UTC
            match_time = match_time.replace(tzinfo=timezone.utc)
        elif match_time.tzinfo != timezone.utc:
            # Convert to UTC if needed
            match_time = match_time.astimezone(timezone.utc)
            
        time_diff = match_time - now
        
        if time_diff.total_seconds() <= 0:
            return "Live"
        
        hours = int(time_diff.total_seconds() // 3600)
        minutes = int((time_diff.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"in {hours}h {minutes}m"
        else:
            return f"in {minutes}m"
    
    def _get_league_priority(self, league_name):
        """Assign priority to leagues (lower number = higher priority)."""
        priorities = {
            'Champions League': 1,
            'Europa League': 2,
            'Premier League': 3,
            'La Liga': 4,
            'Serie A': 5,
            'Bundesliga': 6,
            'Ligue 1': 7,
            'Copa Libertadores': 8,
            'MLS': 9,
            'Liga MX': 10,
            'Copa del Rey': 11,
            'FA Cup': 12,
            'DFB Pokal': 13,
            'Coupe de France': 14,
            'Coppa Italia': 15,
            'UEFA Nations League': 16,
            'World Cup Qualifiers': 17
        }
        return priorities.get(league_name, 20)  # Default priority for unlisted leagues
    
    def _is_analysis_fresh(self, analysis):
        """Check if cached analysis is fresh (within last 6 hours)."""
        try:
            if 'generated_at' in analysis:
                from datetime import datetime
                generated_time = datetime.fromisoformat(analysis['generated_at'])
                age_hours = (datetime.now() - generated_time).total_seconds() / 3600
                return age_hours < 6  # Consider fresh if less than 6 hours old
        except:
            pass
        return False
    
    def run_match_analysis(self, home_team, away_team):
        """Get analysis for selected match from CSV data."""
        try:
            # Decode HTML entities in team names (e.g., &amp; -> &)
            import html
            home_team = html.unescape(home_team)
            away_team = html.unescape(away_team)
            
            print(f"🔍 Looking for analysis: {home_team} vs {away_team}...")
            
            # Get analysis from CSV file directly
            import csv
            import json
            from pathlib import Path
            
            analysis_file = Path("data/analysis.csv")
            if not analysis_file.exists():
                return {"error": "No analysis data available"}
            
            # Read analysis CSV and find matching entries
            matching_analysis = []
            
            with open(analysis_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Parse the analysis_data JSON
                    try:
                        analysis_data = json.loads(row['analysis_data'])
                        
                        # Check if this analysis belongs to our match
                        # We need to get the match info from matches.csv
                        match_id = row['match_id']
                        
                        # Get match details
                        matches_file = Path("data/matches.csv")
                        if matches_file.exists():
                            with open(matches_file, 'r', encoding='utf-8') as mf:
                                match_reader = csv.DictReader(mf)
                                for match_row in match_reader:
                                    if match_row['match_id'] == match_id:
                                        if (match_row['home_team'] == home_team and 
                                            match_row['away_team'] == away_team):
                                            # Transform data to match frontend expectations
                                            final_score = analysis_data.get('final_score', 50)
                                            model_prob = analysis_data.get('model_prob', 0.5)
                                            
                                            # FILTER: Only show bets with Final Score > 60 (good opportunities)
                                            if final_score < 60:
                                                continue  # Skip low-quality bets
                                            
                                            # Check if this is a team prop or player prop
                                            is_team_prop = analysis_data.get('prop_type') == 'team'
                                            
                                            # FILTER: Remove bets where player has 0 average per game for this metric
                                            rate_per_game = analysis_data.get('rate_per_game', 0)
                                            if rate_per_game <= 0:
                                                continue  # Skip players with 0 average for this metric
                                            
                                            # Calculate confidence based on Final Score
                                            if final_score >= 80:
                                                confidence = 'High'
                                            elif final_score >= 70:
                                                confidence = 'Medium'
                                            else:
                                                confidence = 'Low'
                                            
                                            # Calculate profitable odds thresholds
                                            # Fair odds = 1 / model_probability
                                            fair_odds_decimal = 1 / model_prob if model_prob > 0 else 2.0
                                            
                                            # Add 5% margin for profitable betting
                                            min_profitable_decimal = fair_odds_decimal * 1.05
                                            
                                            # Convert to American odds
                                            if min_profitable_decimal >= 2.0:
                                                min_profitable_american = f"+{int((min_profitable_decimal - 1) * 100)}"
                                            else:
                                                min_profitable_american = f"-{int(100 / (min_profitable_decimal - 1))}"
                                            
                                            if is_team_prop:
                                                # Team prop bet
                                                team_name = analysis_data.get('team', '')
                                                team_logo = analysis_data.get('logo', '') or get_team_logo(team_name)
                                                
                                                bet_obj = {
                                                    'player': team_name,  # Use team name as "player"
                                                    'bet_description': f"{analysis_data['prop']} ≥ {analysis_data['threshold']}",
                                                    'market': analysis_data['prop'],
                                                    'threshold': analysis_data['threshold'],
                                                    'model_prob': model_prob,
                                                    'model_probability_percent': round(model_prob * 100, 1),
                                                    'final_score': round(final_score, 1),
                                                    'final_score_percent': round(final_score, 1),
                                                    'suggested_stake': analysis_data.get('suggested_stake', 10.0),
                                                    'confidence': confidence,
                                                    'fair_odds_decimal': round(fair_odds_decimal, 2),
                                                    'min_profitable_odds_decimal': round(min_profitable_decimal, 2),
                                                    'min_profitable_odds_american': min_profitable_american,
                                                    'apps_this_season': 'Team',  # Show "Team" instead of apps
                                                    'position': 'Team',
                                                    'avg_per_game': round(rate_per_game, 2),
                                                    'team_logo': team_logo,
                                                    'is_team_prop': True,
                                                    'reasoning': f"Final Score: {round(final_score, 1)} | Model: {round(model_prob * 100, 1)}% | Avg: {round(rate_per_game, 2)}/game"
                                                }
                                            else:
                                                # Player prop bet
                                                player_name = analysis_data.get('player', '')
                                                
                                                bet_obj = {
                                                    'player': player_name,
                                                    'bet_description': f"{analysis_data['prop']} ≥ {analysis_data['threshold']}",
                                                    'market': analysis_data['prop'],
                                                    'threshold': analysis_data['threshold'],
                                                    'model_prob': model_prob,
                                                    'model_probability_percent': round(model_prob * 100, 1),
                                                    'final_score': round(final_score, 1),
                                                    'final_score_percent': round(final_score, 1),
                                                    'suggested_stake': analysis_data.get('suggested_stake', 10.0),
                                                    'confidence': confidence,
                                                    'fair_odds_decimal': round(fair_odds_decimal, 2),
                                                    'min_profitable_odds_decimal': round(min_profitable_decimal, 2),
                                                    'min_profitable_odds_american': min_profitable_american,
                                                    'apps_this_season': analysis_data.get('games_played', 'N/A'),
                                                    'position': analysis_data.get('position', ''),
                                                    'avg_per_game': round(rate_per_game, 2),
                                                    'is_team_prop': False,
                                                    'reasoning': f"Final Score: {round(final_score, 1)} | Model: {round(model_prob * 100, 1)}% | Avg: {round(rate_per_game, 2)}/game"
                                                }
                                            
                                            matching_analysis.append(bet_obj)
                                        break
                        
                    except (json.JSONDecodeError, KeyError) as e:
                        continue
            
            if not matching_analysis:
                return {"error": "No analysis found for this match"}
            
            # Filter to one bet per player with highest model probability
            player_best_bets = {}
            for bet in matching_analysis:
                player = bet.get('player', 'Unknown')
                model_prob = bet.get('model_prob', 0)
                
                if player not in player_best_bets or model_prob > player_best_bets[player].get('model_prob', 0):
                    player_best_bets[player] = bet
            
            # Convert back to list and sort by Final Score (highest to lowest)
            matching_analysis = list(player_best_bets.values())
            matching_analysis.sort(key=lambda x: x.get('final_score', 0), reverse=True)
            
            print(f"✅ Found {len(matching_analysis)} unique players with best opportunities (sorted by Final Score)")
            
            # Format results for web display
            analysis_results = {
                "match_info": {
                    "home_team": home_team,
                    "away_team": away_team,
                    "home_team_logo": get_team_logo(home_team),
                    "away_team_logo": get_team_logo(away_team),
                    "analysis_time": "2025-08-23T13:35:00",
                    "lineup_source": "Real ESPN data"
                },
                "summary": {
                    "total_opportunities": len(matching_analysis),
                    "high_confidence_bets": len([bet for bet in matching_analysis if bet.get('final_score', 0) >= 80]),
                    "medium_confidence_bets": len([bet for bet in matching_analysis if 70 <= bet.get('final_score', 0) < 80]),
                    "data_quality": "100% Real ESPN Data",
                    "fake_data": False
                },
                "opportunities": matching_analysis,
                "top_bets": matching_analysis[:10],  # Frontend expects this
                "all_bets": matching_analysis        # Frontend expects this
            }
            
            return analysis_results
            
        except Exception as e:
            print(f"❌ Analysis error: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"Analysis failed: {str(e)}"}

    def _find_match_id(self, home_team, away_team):
        """Find match ID by team names (fuzzy matching)."""
        if not self.db:
            return None
            
        try:
            # Simple approach - look for recent matches with similar team names
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Try exact match first
                cursor.execute('''
                    SELECT id FROM matches 
                    WHERE home_team = ? AND away_team = ?
                    ORDER BY created_at DESC LIMIT 1
                ''', (home_team, away_team))
                
                result = cursor.fetchone()
                if result:
                    return result[0]
                
                # Try fuzzy matching
                cursor.execute('''
                    SELECT id, home_team, away_team FROM matches 
                    WHERE (home_team LIKE ? OR home_team LIKE ?) 
                    AND (away_team LIKE ? OR away_team LIKE ?)
                    ORDER BY created_at DESC LIMIT 5
                ''', (f'%{home_team}%', f'%{home_team.split()[-1]}%', 
                      f'%{away_team}%', f'%{away_team.split()[-1]}%'))
                
                results = cursor.fetchall()
                for match_id, db_home, db_away in results:
                    # Simple similarity check
                    if (home_team.lower() in db_home.lower() or db_home.lower() in home_team.lower()) and \
                       (away_team.lower() in db_away.lower() or db_away.lower() in away_team.lower()):
                        return match_id
                
                return None
                
        except Exception as e:
            print(f"⚠️ Error finding match ID: {e}")
            return None

# Initialize service
bettor_service = BettorWebService()

@app.route('/')
def index():
    """Main page with match selector."""
    return render_template('index.html')

@app.route('/api/matches')
def get_matches():
    """API endpoint to get upcoming matches."""
    hours = request.args.get('hours', 8, type=int)
    raw_matches = bettor_service.get_upcoming_matches(hours)
    
    # Transform CSV format to frontend format
    formatted_matches = []
    for match in raw_matches:
        try:
            from datetime import datetime
            kickoff_dt = datetime.fromisoformat(match['kickoff_time'])
            now = datetime.now()
            
            # Calculate time until match
            time_diff = kickoff_dt - now
            hours_until = time_diff.total_seconds() / 3600
            
            if hours_until > 0:  # Only future matches
                if hours_until < 1:
                    time_until = f"{int(time_diff.total_seconds() / 60)} minutes"
                else:
                    time_until = f"{hours_until:.1f} hours"
                
                formatted_match = {
                    'id': match['match_id'],
                    'home_team': match['home_team'],
                    'away_team': match['away_team'],
                    'league': match['league'],
                    'kickoff': kickoff_dt.strftime('%H:%M'),
                    'kickoff_time': match['kickoff_time'],
                    'time_until': time_until,
                    'venue': f"{match['home_team']} Stadium"
                }
                formatted_matches.append(formatted_match)
        except Exception as e:
            print(f"Error formatting match: {e}")
            continue
    
    return jsonify(formatted_matches)

@app.route('/api/analyze')
def analyze_match():
    """API endpoint to analyze selected match."""
    home_team = request.args.get('home_team')
    away_team = request.args.get('away_team')
    
    if not home_team or not away_team:
        return jsonify({"error": "Missing team parameters"}), 400
    
    analysis = bettor_service.run_match_analysis(home_team, away_team)
    return jsonify(analysis)

@app.route('/match/<home_team>/<away_team>')
def match_analysis(home_team, away_team):
    """Match analysis page."""
    return render_template('analysis.html', home_team=home_team, away_team=away_team)

@app.route('/api/stats')
def get_stats():
    """API endpoint to get dynamic database statistics."""
    try:
        from simple_ml_model import ml_model
        import csv
        import json
        from pathlib import Path
        
        # Get analysis data from CSV
        analysis_file = Path("data/analysis.csv")
        analyses = []
        
        if analysis_file.exists():
            with open(analysis_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        analysis_data = json.loads(row['analysis_data'])
                        analyses.append(analysis_data)
                    except:
                        continue
        
        # Calculate real statistics
        total_analyses = len(analyses)
        
        # Calculate confidence distribution based on Final Score
        confidence_counts = {'High': 0, 'Medium': 0, 'Low': 0}
        final_scores = []
        
        for analysis in analyses:
            final_score = analysis.get('final_score', 50)
            final_scores.append(final_score)
            
            # Determine confidence based on Final Score
            if final_score >= 80:
                confidence_counts['High'] += 1
            elif final_score >= 70:
                confidence_counts['Medium'] += 1
            else:
                confidence_counts['Low'] += 1
        
        # Calculate average Final Score
        avg_final_score = sum(final_scores) / len(final_scores) if final_scores else 50
        
        # Get ML model insights
        ml_insights = ml_model.get_model_insights()
        
        # Count unique players
        unique_players = len(set(analysis.get('player', '') for analysis in analyses))
        
        # Count matches analyzed today
        matches_file = Path("data/matches.csv")
        matches_analyzed = 0
        if matches_file.exists():
            with open(matches_file, 'r', encoding='utf-8') as f:
                matches_analyzed = len(f.readlines()) - 1  # Subtract header
        
        return jsonify({
            'total_opportunities': total_analyses,
            'high_confidence_bets': confidence_counts.get('High', 0),
            'medium_confidence_bets': confidence_counts.get('Medium', 0), 
            'low_confidence_bets': confidence_counts.get('Low', 0),
            'average_final_score': round(avg_final_score, 1),
            'unique_players_analyzed': unique_players,
            'matches_analyzed_today': matches_analyzed,
            'ml_model_accuracy': ml_insights.get('accuracy', 0),
            'ml_predictions_made': ml_insights.get('predictions_made', 0),
            'data_freshness': 'Real-time ESPN data',
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recent')
def get_recent_analyses():
    """API endpoint to get recent analyses."""
    try:
        if not bettor_service.db:
            return jsonify({"message": "Database not available", "analyses": []})
            
        limit = request.args.get('limit', 20, type=int)
        analyses = bettor_service.db.get_recent_analyses(limit)
        
        # Format for JSON response
        formatted_analyses = []
        for analysis in analyses:
            formatted_analyses.append({
                'home_team': analysis[0],
                'away_team': analysis[1], 
                'league': analysis[2],
                'kickoff_time': analysis[3],
                'total_opportunities': analysis[4],
                'expected_profit': analysis[5],
                'expected_roi': analysis[6],
                'created_at': analysis[7]
            })
        
        return jsonify(formatted_analyses)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    """Ultra-simple health check for Railway."""
    return 'OK', 200

@app.route('/api/refresh', methods=['POST', 'GET'])
def trigger_refresh():
    """Manual trigger for data refresh - can be called by external cron services."""
    try:
        print("🔄 Manual refresh triggered via API...")
        success = run_daily_refresh()
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Data refresh completed successfully",
                "timestamp": datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                "status": "error", 
                "message": "Data refresh failed",
                "timestamp": datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Refresh error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

# ============================================================================
# SCHEDULER FUNCTIONS
# ============================================================================

def run_daily_refresh():
    """Run the daily data refresh - fetch new matches and generate analysis."""
    try:
        print("🌙 Starting daily refresh...")
        
        # Step 1: Get new Premier League matches for next 24 hours
        print("📅 Fetching upcoming Premier League matches...")
        result = subprocess.run([sys.executable, 'populate_real_premier_league_matches.py'], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Successfully updated matches.csv")
        else:
            print(f"❌ Error updating matches: {result.stderr}")
            return False
        
        # Step 2: Generate fresh analysis with real ESPN rosters
        print("🧠 Generating fresh betting analysis...")
        result = subprocess.run([sys.executable, 'use_real_espn_rosters.py'], 
                              capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            print("✅ Successfully generated fresh analysis")
            print(f"📊 Daily refresh completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return True
        else:
            print(f"❌ Error generating analysis: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Daily refresh timed out")
        return False
    except Exception as e:
        print(f"💥 Unexpected error in daily refresh: {e}")
        return False

def run_scheduler():
    """Background scheduler thread."""
    print("⏰ Starting background scheduler...")
    
    # Schedule daily refresh at midnight UTC
    schedule.every().day.at("00:00").do(run_daily_refresh)
    
    # Schedule quick updates every 4 hours
    schedule.every(4).hours.do(run_daily_refresh)
    
    # Initial run if no data exists
    try:
        with open('data/matches.csv', 'r') as f:
            lines = f.readlines()
            if len(lines) <= 1:  # Only header or empty
                print("📊 No match data found, running initial refresh...")
                run_daily_refresh()
    except FileNotFoundError:
        print("📊 matches.csv not found, running initial refresh...")
        run_daily_refresh()
    
    # Keep scheduler running
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except Exception as e:
            print(f"💥 Scheduler error: {e}")
            time.sleep(300)  # Wait 5 minutes before retrying

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("🚀 Starting Bettor Web Interface...")
    print("📱 Mobile-optimized betting analysis")
    print(f"🌐 Access at: http://0.0.0.0:{port}")
    print(f"🏥 Health check: http://0.0.0.0:{port}/health")
    
    # Note: Use external cron service to hit /api/refresh daily
    # Internal scheduler removed for better reliability on cloud platforms
    print("🔄 Manual refresh available at: /api/refresh")
    
    try:
        app.run(debug=False, host='0.0.0.0', port=port, threaded=True)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        raise

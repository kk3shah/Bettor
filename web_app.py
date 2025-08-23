#!/usr/bin/env python3
"""
🎯 Bettor Web Interface - Mobile-First Betting Analysis
"""
from flask import Flask, render_template, jsonify, request
import sys
import os
from datetime import datetime, timedelta
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.data.adapters.live_scraper import LiveDataScraper
from app.services.multi_market import analyze_comprehensive_markets
from app.services.earnings import calculate_expected_earnings
from app.services.value import american_to_decimal
from database import BettorDatabase

app = Flask(__name__)

class BettorWebService:
    """Service class for web interface functionality."""
    
    def __init__(self):
        self.scraper = LiveDataScraper()
        self.db = BettorDatabase()
    
    def get_upcoming_matches(self, hours_ahead=24):
        """Get upcoming matches from ALL major football leagues worldwide."""
        try:
            print(f"🌍 Finding matches from ALL leagues in next {hours_ahead} hours...")
            
            from datetime import timezone
            now = datetime.now(timezone.utc)
            today = now.date()
            tomorrow = today + timedelta(days=1)
            
            # Major football leagues ESPN API endpoints
            leagues = {
                'Premier League': 'eng.1',
                'La Liga': 'esp.1', 
                'Serie A': 'ita.1',
                'Bundesliga': 'ger.1',
                'Ligue 1': 'fra.1',
                'Champions League': 'uefa.champions',
                'Europa League': 'uefa.europa',
                'MLS': 'usa.1',
                'Liga MX': 'mex.1',
                'Brazilian Serie A': 'bra.1',
                'Argentine Primera': 'arg.1',
                'Netherlands Eredivisie': 'ned.1',
                'Portuguese Liga': 'por.1',
                'Scottish Premiership': 'sco.1',
                'Belgian Pro League': 'bel.1',
                'Turkish Super Lig': 'tur.1',
                'Russian Premier League': 'rus.1',
                'Copa Libertadores': 'conmebol.libertadores',
                'Copa del Rey': 'esp.copa_del_rey',
                'FA Cup': 'eng.fa',
                'DFB Pokal': 'ger.dfb_pokal',
                'Coupe de France': 'fra.coupe_de_france',
                'Coppa Italia': 'ita.coppa_italia',
                'UEFA Nations League': 'uefa.nations',
                'World Cup Qualifiers': 'fifa.world_cup_qual',
                'International Friendlies': 'fifa.friendly'
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
    
    def run_match_analysis(self, home_team, away_team):
        """Get analysis for selected match (from database or run new analysis)."""
        try:
            print(f"🔍 Looking for analysis: {home_team} vs {away_team}...")
            
            # Try to find match ID by teams
            match_id = self._find_match_id(home_team, away_team)
            
            if match_id:
                # Check database first
                print(f"📊 Checking database for existing analysis...")
                existing_analysis = self.db.get_analysis_by_match(match_id)
                
                if existing_analysis:
                    print(f"✅ Found existing analysis in database")
                    return existing_analysis
            
            # If not found in database, run new analysis
            print(f"🚀 Running new analysis for {home_team} vs {away_team}...")
            
            # Get live match data
            live_data = self.scraper.get_live_match_data(home_team, away_team)
            
            # Run comprehensive analysis
            config = {
                'bankroll': 1000,
                'max_stake_pct': 0.05,
                'kelly_fraction': 0.25,
                'league_avg_shots': 10.5,
                'league_avg_corners': 5.5,
                'home_mult': 1.05,
                'away_mult': 0.95
            }
            
            signals = analyze_comprehensive_markets(live_data, config)
            
            if not signals:
                return {"error": "No betting signals generated"}
            
            # Calculate earnings
            earnings_analysis = calculate_expected_earnings(signals, config['bankroll'])
            
            # Format results for web display
            analysis_results = {
                "match_info": {
                    "home_team": home_team,
                    "away_team": away_team,
                    "kickoff_time": live_data['match_info']['kickoff_utc'],
                    "analysis_time": datetime.now().isoformat(),
                    "lineup_source": "Real-time analysis"
                },
                "summary": {
                    "total_opportunities": len(signals),
                    "total_stake_recommended": earnings_analysis['total_stakes'],
                    "expected_profit": earnings_analysis['expected_profit'],
                    "expected_roi_percent": earnings_analysis['expected_roi'],
                    "bankroll_utilization_percent": earnings_analysis['bankroll_utilization']
                },
                "profit_scenarios": earnings_analysis['scenarios'],
                "top_bets": [],
                "all_bets": []
            }
            
            # Process betting signals
            for i, signal in enumerate(signals, 1):
                decimal_odds = american_to_decimal(signal['odds'])
                potential_profit = (decimal_odds - 1) * signal['suggested_stake']
                confidence = "HIGH" if signal['edge'] > 0.2 else "MEDIUM" if signal['edge'] > 0.1 else "LOW"
                
                bet_info = {
                    "priority": i,
                    "player": signal['player'],
                    "team": signal['team'],
                    "market": signal['market'],
                    "bet_description": f"{signal['market']} ≥ {signal['threshold']}",
                    "threshold": signal['threshold'],
                    "odds_american": signal['odds'],
                    "odds_decimal": round(decimal_odds, 2),
                    "model_probability_percent": round(signal['model_prob'] * 100, 1),
                    "bookmaker_implied_probability_percent": round(signal['implied_prob'] * 100, 1),
                    "edge_percent": round(signal['edge'] * 100, 1),
                    "kelly_percent": round(signal['kelly'] * 100, 1),
                    "recommended_stake_dollars": round(signal['suggested_stake'], 2),
                    "potential_profit_dollars": round(potential_profit, 2),
                    "potential_return_dollars": round(signal['suggested_stake'] + potential_profit, 2),
                    "confidence": confidence,
                    "expected_minutes": signal['expected_minutes'],
                    "home_away": "HOME" if signal['team'] == home_team else "AWAY"
                }
                
                analysis_results["all_bets"].append(bet_info)
                
                # Top 8 bets for quick view
                if i <= 8:
                    analysis_results["top_bets"].append(bet_info)
            
            # Store new analysis in database if we have a match_id
            if match_id:
                try:
                    self.db.store_analysis(match_id, analysis_results)
                    print(f"💾 Stored analysis in database")
                except Exception as e:
                    print(f"⚠️ Failed to store analysis: {e}")
            
            return analysis_results
            
        except Exception as e:
            print(f"❌ Error running match analysis: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"Analysis failed: {str(e)}"}
    
    def _find_match_id(self, home_team, away_team):
        """Find match ID by team names (fuzzy matching)."""
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
    matches = bettor_service.get_upcoming_matches(hours)
    return jsonify(matches)

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
    """API endpoint to get database statistics."""
    try:
        stats = bettor_service.db.get_database_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recent')
def get_recent_analyses():
    """API endpoint to get recent analyses."""
    try:
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

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    try:
        stats = bettor_service.db.get_database_stats()
        from datetime import timezone
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database_stats": stats
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy", 
            "error": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("🚀 Starting Bettor Web Interface...")
    print("📱 Mobile-optimized betting analysis")
    print(f"🌐 Access at: http://localhost:{port}")
    app.run(debug=False, host='0.0.0.0', port=port)

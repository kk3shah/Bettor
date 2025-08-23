#!/usr/bin/env python3
"""
🧠 Intelligent Match-Specific Scheduler for Bettor Premium
Automatically schedules refresh jobs 50 minutes before each match
"""
import schedule
import time
import subprocess
import sys
import os
from datetime import datetime, timezone, timedelta
import threading
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app import BettorWebService
from database import BettorDatabase

class IntelligentMatchScheduler:
    """Smart scheduler that knows about each match and schedules accordingly."""
    
    def __init__(self):
        self.web_service = BettorWebService()
        self.db = BettorDatabase()
        self.scheduled_matches = set()  # Track already scheduled matches
        self.running = True
        
    def get_all_upcoming_matches(self, hours_ahead=72):
        """Get all matches in next N hours with their exact kickoff times."""
        try:
            matches = self.web_service.get_upcoming_matches(hours_ahead)
            print(f"📅 Found {len(matches)} upcoming matches in next {hours_ahead} hours")
            
            # Sort by kickoff time
            matches.sort(key=lambda x: x['kickoff_full'])
            
            for match in matches:
                kickoff = datetime.fromisoformat(match['kickoff_full'].replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                hours_until = (kickoff - now).total_seconds() / 3600
                
                print(f"  ⚽ {match['home_team']} vs {match['away_team']} - {kickoff.strftime('%H:%M')} ({hours_until:.1f}h)")
            
            return matches
            
        except Exception as e:
            print(f"❌ Error getting matches: {e}")
            return []
    
    def schedule_match_specific_jobs(self):
        """Schedule specific refresh jobs for each upcoming match."""
        print("🧠 Scanning for matches that need scheduling...")
        
        matches = self.get_all_upcoming_matches()
        now = datetime.now(timezone.utc)
        
        newly_scheduled = 0
        
        for match in matches:
            match_id = match['id']
            
            # Skip if already scheduled
            if match_id in self.scheduled_matches:
                continue
                
            try:
                # Parse kickoff time
                kickoff = datetime.fromisoformat(match['kickoff_full'].replace('Z', '+00:00'))
                
                # Calculate refresh time (50 minutes before kickoff)
                refresh_time = kickoff - timedelta(minutes=50)
                
                # Skip if refresh time already passed
                if refresh_time <= now:
                    print(f"⚠️ Skipping {match['home_team']} vs {match['away_team']} - refresh time already passed")
                    continue
                
                # Skip matches more than 48 hours away (we'll catch them in next scan)
                hours_until_refresh = (refresh_time - now).total_seconds() / 3600
                if hours_until_refresh > 48:
                    continue
                
                # Schedule the specific job
                self.schedule_match_refresh(match, refresh_time)
                self.scheduled_matches.add(match_id)
                newly_scheduled += 1
                
                print(f"✅ Scheduled: {match['home_team']} vs {match['away_team']} at {refresh_time.strftime('%H:%M')} UTC")
                
            except Exception as e:
                print(f"❌ Error scheduling {match['home_team']} vs {match['away_team']}: {e}")
                continue
        
        if newly_scheduled > 0:
            print(f"🎯 Scheduled {newly_scheduled} new match-specific refresh jobs")
        else:
            print("✅ All upcoming matches already scheduled")
    
    def schedule_match_refresh(self, match, refresh_time):
        """Schedule a specific refresh job for one match."""
        # Convert to schedule-friendly format
        schedule_time = refresh_time.strftime('%H:%M')
        
        # Create a unique job function for this match
        def refresh_this_match():
            self.refresh_single_match(match)
            # Remove from scheduled set after execution
            self.scheduled_matches.discard(match['id'])
        
        # Schedule for today or tomorrow based on the date
        refresh_date = refresh_time.date()
        today = datetime.now(timezone.utc).date()
        
        if refresh_date == today:
            # Schedule for today
            schedule.every().day.at(schedule_time).do(refresh_this_match).tag(f"match_{match['id']}")
        elif refresh_date == today + timedelta(days=1):
            # Schedule for tomorrow (will be handled by daily scheduling scan)
            schedule.every().day.at(schedule_time).do(refresh_this_match).tag(f"match_{match['id']}")
    
    def refresh_single_match(self, match):
        """Refresh analysis for a single specific match."""
        print(f"⚽ MATCH REFRESH: {match['home_team']} vs {match['away_team']} (T-50min)")
        
        try:
            # Run batch processor for this specific match timeframe
            result = subprocess.run([
                sys.executable, 'batch_processor.py', 
                '--hours', '2'  # Small window to capture this match
            ], capture_output=True, text=True, timeout=1800)
            
            if result.returncode == 0:
                print(f"✅ Match refresh successful for {match['home_team']} vs {match['away_team']}")
                
                # Log the successful refresh
                self.log_match_refresh(match, "SUCCESS")
            else:
                print(f"❌ Match refresh failed for {match['home_team']} vs {match['away_team']}")
                print(result.stderr)
                self.log_match_refresh(match, "FAILED", result.stderr)
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Match refresh timed out for {match['home_team']} vs {match['away_team']}")
            self.log_match_refresh(match, "TIMEOUT")
        except Exception as e:
            print(f"❌ Match refresh error for {match['home_team']} vs {match['away_team']}: {e}")
            self.log_match_refresh(match, "ERROR", str(e))
    
    def log_match_refresh(self, match, status, error_msg=None):
        """Log match refresh attempts."""
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'match_id': match['id'],
            'home_team': match['home_team'],
            'away_team': match['away_team'],
            'kickoff': match['kickoff_full'],
            'status': status,
            'error': error_msg
        }
        
        # Could store in database or file - for now just print
        print(f"📝 LOG: {json.dumps(log_entry, indent=2)}")
    
    def run_daily_planning(self):
        """Daily job to plan the next 48 hours of matches."""
        print(f"📋 DAILY PLANNING: Scanning next 48 hours for matches to schedule")
        self.schedule_match_specific_jobs()
    
    def run_maintenance(self):
        """Clean up completed jobs and old schedules."""
        print("🧹 MAINTENANCE: Cleaning up completed scheduled jobs")
        
        # Clear completed jobs
        current_time = datetime.now(timezone.utc)
        
        # Remove jobs for matches that have already started
        jobs_to_remove = []
        for job in schedule.get_jobs():
            if hasattr(job, 'tags') and job.tags:
                for tag in job.tags:
                    if tag.startswith('match_'):
                        # This is a match-specific job - check if it should be removed
                        try:
                            match_id = tag.replace('match_', '')
                            if match_id in self.scheduled_matches:
                                # Check if this job's time has passed
                                # (This is a simplified check - could be more sophisticated)
                                jobs_to_remove.append(job)
                                break
                        except:
                            pass
        
        for job in jobs_to_remove:
            schedule.cancel_job(job)
        
        print(f"🗑️ Removed {len(jobs_to_remove)} completed jobs")
    
    def main_loop(self):
        """Main intelligent scheduler loop."""
        print("🧠 INTELLIGENT MATCH SCHEDULER STARTING...")
        print("📋 Daily Planning: 06:00 UTC (schedule next 48h)")
        print("⚽ Match Refresh: Specific time per match (T-50min)")
        print("🧹 Maintenance: Daily at 02:00 UTC")
        
        # Set up recurring jobs
        schedule.every().day.at("06:00").do(self.run_daily_planning)
        schedule.every().day.at("02:00").do(self.run_maintenance)
        
        # Run initial planning
        print("🚀 Running initial daily planning...")
        self.run_daily_planning()
        
        # Main loop
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds for better precision
            except KeyboardInterrupt:
                print("⏹️ Intelligent scheduler stopped")
                break
            except Exception as e:
                print(f"❌ Scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes on error

def main():
    """Main entry point."""
    scheduler = IntelligentMatchScheduler()
    scheduler.main_loop()

if __name__ == "__main__":
    main()

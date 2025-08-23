#!/usr/bin/env python3
"""
🔄 Background Scheduler - Runs alongside the web app
"""
import schedule
import time
import threading
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from populate_csv_data import populate_csv_data

class BackgroundScheduler:
    def __init__(self):
        self.scheduler_thread = None
        self.running = False
    
    def daily_refresh(self):
        """Run the daily data refresh."""
        print(f"\n🕛 DAILY REFRESH STARTED - {datetime.utcnow().isoformat()}")
        print("=" * 60)
        
        try:
            # Populate all CSV data (matches + analysis)  
            populate_csv_data()
            print(f"✅ DAILY REFRESH COMPLETED - {datetime.utcnow().isoformat()}\n")
            
        except Exception as e:
            print(f"❌ DAILY REFRESH FAILED - {e}")
            print(f"🕛 Next attempt in 24 hours\n")
    
    def run_scheduler(self):
        """Run the scheduler loop."""
        print("🤖 Background Scheduler Started")
        print("⏰ Scheduled: Every day at 12:00 AM UTC")
        
        # Schedule daily refresh at 12 AM UTC
        schedule.every().day.at("00:00").do(self.daily_refresh)
        
        self.running = True
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def start(self):
        """Start the scheduler in a background thread."""
        if not self.scheduler_thread or not self.scheduler_thread.is_alive():
            self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
            self.scheduler_thread.start()
            print("🚀 Background scheduler thread started")
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        print("🛑 Background scheduler stopped")

# Global scheduler instance
scheduler = BackgroundScheduler()

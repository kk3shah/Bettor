#!/usr/bin/env python3
"""
🕛 Railway Cron Job - Runs daily at 12 AM UTC to refresh all data
"""
import schedule
import time
import threading
from datetime import datetime
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from populate_csv_data import populate_csv_data

def daily_refresh():
    """Run the daily data refresh at 12 AM UTC."""
    print(f"🕛 DAILY REFRESH STARTED - {datetime.utcnow().isoformat()}")
    print("=" * 60)
    
    try:
        # Populate all CSV data (matches + analysis)
        populate_csv_data()
        print(f"✅ DAILY REFRESH COMPLETED - {datetime.utcnow().isoformat()}")
        
    except Exception as e:
        print(f"❌ DAILY REFRESH FAILED - {e}")
        print(f"🕛 Next attempt in 24 hours")

def start_scheduler():
    """Start the background scheduler."""
    print("🤖 Starting Railway Cron Scheduler...")
    print(f"⏰ Next refresh: Every day at 12:00 AM UTC")
    
    # Schedule daily refresh at 12 AM UTC
    schedule.every().day.at("00:00").do(daily_refresh)
    
    # Run scheduler in background thread
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    # Run immediately on startup (for testing)
    print("🚀 Running initial data population...")
    daily_refresh()
    
    # Start the scheduler
    start_scheduler()

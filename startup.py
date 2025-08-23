#!/usr/bin/env python3
"""
🚀 Production Startup Script for Bettor
Runs both web server and automated batch processing
"""
import os
import sys
import threading
import time
from datetime import datetime

def start_scheduler():
    """Start the intelligent match-aware scheduler in background."""
    print("🧠 Starting intelligent match-aware scheduler...")
    time.sleep(10)  # Let web server start first
    
    # Check if we should use intelligent scheduler (default: yes)
    use_intelligent = os.environ.get('USE_INTELLIGENT_SCHEDULER', 'true').lower() == 'true'
    
    try:
        if use_intelligent:
            print("🎯 Using INTELLIGENT scheduler (match-specific timing)")
            from intelligent_scheduler import main as run_intelligent_scheduler
            run_intelligent_scheduler()
        else:
            print("⏰ Using basic scheduler (hourly timing)")
            from scheduler import main as run_scheduler
            run_scheduler()
    except Exception as e:
        print(f"❌ Scheduler error: {e}")
        # Restart scheduler after error
        time.sleep(300)  # Wait 5 minutes
        start_scheduler()

def start_web_server():
    """Start the web server."""
    print("🌐 Starting web server...")
    
    from web_app import app
    port = int(os.environ.get('PORT', 8080))
    
    print(f"🚀 Bettor Premium starting on port {port}")
    print(f"🌍 Public access will be available soon...")
    print(f"🧠 INTELLIGENT scheduling: T-50min before each match")
    print(f"📋 Daily planning at 06:00 UTC")
    print(f"⚽ Live lineup detection & analysis switching")
    
    # Run in production mode
    app.run(
        host='0.0.0.0', 
        port=port, 
        debug=False,
        threaded=True
    )

if __name__ == "__main__":
    print("🎯 BETTOR PREMIUM - AUTOMATED FOOTBALL BETTING PLATFORM")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("🚀 Initializing production environment...")
    
    # Start scheduler in background thread
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Start web server (main thread)
    start_web_server()

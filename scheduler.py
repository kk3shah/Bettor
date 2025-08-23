#!/usr/bin/env python3
"""
⏰ Bettor Scheduler - Automated daily processing
"""
import schedule
import time
import subprocess
import sys
import os
from datetime import datetime

def run_daily_batch():
    """Run daily comprehensive analysis."""
    print(f"🌅 Starting daily batch job at {datetime.now()}")
    try:
        result = subprocess.run([
            sys.executable, 'batch_processor.py', 
            '--hours', '24'
        ], capture_output=True, text=True, timeout=7200)  # 2 hour timeout
        
        if result.returncode == 0:
            print("✅ Daily batch completed successfully")
            print(result.stdout)
        else:
            print("❌ Daily batch failed")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⏰ Daily batch timed out")
    except Exception as e:
        print(f"❌ Daily batch error: {e}")

def run_quick_update():
    """Run quick update for imminent matches."""
    print(f"⚡ Starting quick update at {datetime.now()}")
    try:
        result = subprocess.run([
            sys.executable, 'batch_processor.py', 
            '--quick'
        ], capture_output=True, text=True, timeout=1800)  # 30 min timeout
        
        if result.returncode == 0:
            print("✅ Quick update completed")
        else:
            print("❌ Quick update failed")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⏰ Quick update timed out")
    except Exception as e:
        print(f"❌ Quick update error: {e}")

def run_maintenance():
    """Run database maintenance."""
    print(f"🧹 Starting maintenance at {datetime.now()}")
    try:
        result = subprocess.run([
            sys.executable, 'batch_processor.py', 
            '--maintenance'
        ], capture_output=True, text=True, timeout=600)  # 10 min timeout
        
        if result.returncode == 0:
            print("✅ Maintenance completed")
        else:
            print("❌ Maintenance failed")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Maintenance error: {e}")

def run_lineup_refresh():
    """Run lineup-specific refresh for matches starting soon."""
    print(f"⚽ Starting lineup refresh at {datetime.now()}")
    try:
        # Refresh matches starting in next 2 hours (covers the 55-min requirement)
        result = subprocess.run([
            sys.executable, 'batch_processor.py', 
            '--hours', '2'
        ], capture_output=True, text=True, timeout=1800)
        
        if result.returncode == 0:
            print("✅ Lineup refresh completed")
        else:
            print("❌ Lineup refresh failed")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⏰ Lineup refresh timed out")
    except Exception as e:
        print(f"❌ Lineup refresh error: {e}")

def main():
    """Main scheduler loop with enhanced timing for lineups."""
    print("⏰ Bettor Premium Scheduler Starting...")
    print("📅 Master refresh: 06:00 UTC (next 24 hours)")
    print("⚽ Lineup refresh: Every hour (captures lineups 55min before)")
    print("⚡ Quick updates: Every 2 hours (general updates)")
    print("🧹 Maintenance: Daily at 02:00 UTC")
    
    # Enhanced schedule for lineup requirements
    schedule.every().day.at("06:00").do(run_daily_batch)  # Master refresh
    schedule.every().hour.do(run_lineup_refresh)  # Hourly lineup checks
    schedule.every(2).hours.do(run_quick_update)  # General updates
    schedule.every().day.at("02:00").do(run_maintenance)  # Maintenance
    
    # Run initial quick update
    print("🚀 Running initial quick update...")
    run_quick_update()
    
    # Main loop
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("⏹️ Scheduler stopped")
            break
        except Exception as e:
            print(f"❌ Scheduler error: {e}")
            time.sleep(300)  # Wait 5 minutes on error

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
🌙 Midnight Scheduler - 12 AM UTC Real Data Batch
Runs daily scraping of authentic player stats and betting odds
"""
import schedule
import time
import subprocess
import sys
import os
from datetime import datetime, timezone
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('midnight_scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def run_real_data_scraper():
    """Execute the real data scraping process."""
    logging.info("🌙 Starting 12 AM UTC Real Data Batch")
    
    try:
        # Run the real data scraper
        result = subprocess.run([
            sys.executable, 'real_data_scraper.py'
        ], capture_output=True, text=True, timeout=7200)  # 2 hour timeout
        
        if result.returncode == 0:
            logging.info("✅ Real data scraping completed successfully")
            logging.info(f"Output: {result.stdout}")
        else:
            logging.error("❌ Real data scraping failed")
            logging.error(f"Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logging.error("⏰ Real data scraping timed out (2 hours)")
    except Exception as e:
        logging.error(f"❌ Scraping error: {e}")

def test_scraper():
    """Test run the scraper (for development)."""
    logging.info("🧪 Running test scraper batch")
    run_real_data_scraper()

def main():
    """Main scheduler for 12 AM UTC real data scraping."""
    logging.info("🌙 MIDNIGHT SCHEDULER STARTING...")
    logging.info("⏰ Scheduled for 12:00 AM UTC daily")
    logging.info("🎯 Target: Top 5 leagues + Champions League")
    logging.info("📊 Scraping: Real player stats + betting odds")
    
    # Schedule for 12 AM UTC daily
    schedule.every().day.at("00:00").do(run_real_data_scraper)
    
    # Optional: Test run for development (remove in production)
    # schedule.every().minute.do(test_scraper)  # Uncomment for testing
    
    logging.info("⏰ Scheduler active - waiting for 12 AM UTC...")
    
    # Main loop
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logging.info("⏹️ Scheduler stopped by user")
            break
        except Exception as e:
            logging.error(f"❌ Scheduler error: {e}")
            time.sleep(300)  # Wait 5 minutes on error

if __name__ == "__main__":
    main()

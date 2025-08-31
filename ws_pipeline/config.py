"""
Configuration settings for WhoScored scraper pipeline.
"""

import os
import random
from typing import List

# Season handling
DEFAULT_SEASON = "current"

# Browser settings
HEADLESS = os.getenv("WS_HEADLESS", "true").lower() == "true"
VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080

# Rate limiting and delays
MIN_DELAY = 3.0  # minimum seconds between requests
MAX_DELAY = 7.0  # maximum seconds between requests
PAGE_LOAD_TIMEOUT = 30000  # milliseconds
NETWORK_IDLE_TIMEOUT = 5000  # milliseconds

# Concurrency
MAX_CONCURRENT_PAGES = int(os.getenv("WS_MAX_CONCURRENT", "2"))

# Proxy settings (optional)
HTTP_PROXY = os.getenv("HTTP_PROXY")
HTTPS_PROXY = os.getenv("HTTPS_PROXY")

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

# URLs
WHOSCORED_BASE = "https://www.whoscored.com"
LIVESCORES_URL = f"{WHOSCORED_BASE}/livescores"

# Data paths
DATA_DIR = "data"
LOGS_DIR = "logs"

def get_random_delay() -> float:
    """Get a random delay between MIN_DELAY and MAX_DELAY."""
    return random.uniform(MIN_DELAY, MAX_DELAY)

def get_random_user_agent() -> str:
    """Get a random user agent from the list."""
    return random.choice(USER_AGENTS)

# Retry settings
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2.0

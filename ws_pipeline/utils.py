"""
Utility functions for WhoScored scraper pipeline.
"""

import hashlib
import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List

import orjson
import pandas as pd

from . import config

def setup_logging(name: str) -> logging.Logger:
    """Set up logging for the pipeline."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # Create logs directory if it doesn't exist
        Path(config.LOGS_DIR).mkdir(exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(f"{config.LOGS_DIR}/ws_pipeline.log")
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

def extract_team_id(url: str) -> Optional[int]:
    """Extract team ID from WhoScored team URL."""
    match = re.search(r"/Teams/(\d+)/", url)
    return int(match.group(1)) if match else None

def parse_apps_format(apps_str: str) -> tuple[Optional[int], Optional[int]]:
    """Parse apps format like '28(8)' into total and sub appearances."""
    if not apps_str or apps_str == "-":
        return None, None
    
    match = re.match(r"(\d+)(?:\((\d+)\))?", str(apps_str).strip())
    if match:
        total = int(match.group(1))
        sub = int(match.group(2)) if match.group(2) else 0
        return total, sub
    return None, None

def parse_percentage(pct_str: str) -> Optional[float]:
    """Parse percentage string like '86.1' to float 0.861."""
    if not pct_str or pct_str == "-":
        return None
    
    try:
        # Remove % if present and convert to 0-1 scale
        clean_str = str(pct_str).replace("%", "").strip()
        return float(clean_str) / 100.0
    except (ValueError, TypeError):
        return None

def parse_positions(pos_str: str) -> list[str]:
    """Parse position string like 'AM(CLR)' into list of positions."""
    if not pos_str or pos_str == "-":
        return []
    
    # Extract main position and sub-positions
    positions = []
    
    # Main position (before parentheses)
    main_match = re.match(r"([A-Z]+)", pos_str)
    if main_match:
        positions.append(main_match.group(1))
    
    # Sub-positions (in parentheses)
    sub_match = re.search(r"\(([A-Z]+)\)", pos_str)
    if sub_match:
        sub_positions = list(sub_match.group(1))
        positions.extend(sub_positions)
    
    return positions

def safe_float(value: Any) -> Optional[float]:
    """Safely convert value to float."""
    if value is None or value == "-" or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def safe_int(value: Any) -> Optional[int]:
    """Safely convert value to int."""
    if value is None or value == "-" or value == "":
        return None
    try:
        return int(float(value))  # Handle cases like "1.0"
    except (ValueError, TypeError):
        return None

def create_content_hash(content: str) -> str:
    """Create a hash of content for caching."""
    return hashlib.md5(content.encode()).hexdigest()

def save_json(data: Any, filepath: str) -> None:
    """Save data as JSON file."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'wb') as f:
        f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))

def load_json(filepath: str) -> Any:
    """Load JSON file."""
    if not Path(filepath).exists():
        return None
    
    with open(filepath, 'rb') as f:
        return orjson.loads(f.read())

def save_csv(df: pd.DataFrame, filepath: str) -> None:
    """Save DataFrame as CSV."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filepath, index=False)

def load_csv(filepath: str) -> Optional[pd.DataFrame]:
    """Load CSV file as DataFrame."""
    if not Path(filepath).exists():
        return None
    
    return pd.read_csv(filepath)

def get_current_date_str() -> str:
    """Get current date as string in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")

import asyncio

async def random_delay() -> None:
    """Add a random delay to avoid being detected as a bot."""
    delay = config.get_random_delay()
    await asyncio.sleep(delay)

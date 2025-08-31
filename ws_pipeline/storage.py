"""
Storage and caching utilities for WhoScored pipeline.
"""

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from . import config, utils

logger = utils.setup_logging(__name__)

class DataCache:
    """Handles caching of scraped data to avoid duplicate requests."""
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = Path(cache_dir or config.DATA_DIR)
        self.index_file = self.cache_dir / "cache_index.json"
        self.cache_index = self._load_cache_index()
    
    def _load_cache_index(self) -> Dict[str, Any]:
        """Load the cache index."""
        if self.index_file.exists():
            try:
                return utils.load_json(str(self.index_file))
            except Exception as e:
                logger.warning(f"Error loading cache index: {e}")
        
        return {
            'fixtures': {},
            'teams': {},
            'created': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
    
    def _save_cache_index(self) -> None:
        """Save the cache index."""
        self.cache_index['last_updated'] = datetime.now().isoformat()
        utils.save_json(self.cache_index, str(self.index_file))
    
    def _create_content_hash(self, content: Any) -> str:
        """Create a hash of content for caching."""
        if isinstance(content, (dict, list)):
            content_str = json.dumps(content, sort_keys=True)
        else:
            content_str = str(content)
        
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def is_fixtures_cache_valid(self, date_str: str, max_age_hours: int = 6) -> bool:
        """Check if fixtures cache is still valid."""
        cache_key = f"fixtures_{date_str}"
        
        if cache_key not in self.cache_index['fixtures']:
            return False
        
        cache_info = self.cache_index['fixtures'][cache_key]
        cached_time = datetime.fromisoformat(cache_info['timestamp'])
        
        return datetime.now() - cached_time < timedelta(hours=max_age_hours)
    
    def is_team_cache_valid(self, team_id: int, max_age_hours: int = 24) -> bool:
        """Check if team cache is still valid."""
        cache_key = f"team_{team_id}"
        
        if cache_key not in self.cache_index['teams']:
            return False
        
        cache_info = self.cache_index['teams'][cache_key]
        cached_time = datetime.fromisoformat(cache_info['timestamp'])
        
        return datetime.now() - cached_time < timedelta(hours=max_age_hours)
    
    def cache_fixtures(self, fixtures: List[Dict], date_str: str) -> None:
        """Cache fixtures data."""
        cache_key = f"fixtures_{date_str}"
        
        # Save data files
        json_path = self.cache_dir / f"{cache_key}.json"
        csv_path = self.cache_dir / f"{cache_key}.csv"
        
        utils.save_json(fixtures, str(json_path))
        
        if fixtures:
            df = pd.DataFrame(fixtures)
            utils.save_csv(df, str(csv_path))
        
        # Update cache index
        self.cache_index['fixtures'][cache_key] = {
            'timestamp': datetime.now().isoformat(),
            'count': len(fixtures),
            'hash': self._create_content_hash(fixtures),
            'json_path': str(json_path),
            'csv_path': str(csv_path)
        }
        
        self._save_cache_index()
        logger.info(f"Cached {len(fixtures)} fixtures for {date_str}")
    
    def cache_team_players(self, players: List[Dict], team_id: int) -> None:
        """Cache team players data."""
        cache_key = f"team_{team_id}_players"
        
        # Save data files
        json_path = self.cache_dir / f"{cache_key}.json"
        csv_path = self.cache_dir / f"{cache_key}.csv"
        
        utils.save_json(players, str(json_path))
        
        if players:
            df = pd.DataFrame(players)
            utils.save_csv(df, str(csv_path))
        
        # Update cache index
        self.cache_index['teams'][f"team_{team_id}"] = {
            'timestamp': datetime.now().isoformat(),
            'player_count': len(players),
            'hash': self._create_content_hash(players),
            'json_path': str(json_path),
            'csv_path': str(csv_path)
        }
        
        self._save_cache_index()
        logger.info(f"Cached {len(players)} players for team {team_id}")
    
    def load_cached_fixtures(self, date_str: str) -> Optional[List[Dict]]:
        """Load cached fixtures data."""
        cache_key = f"fixtures_{date_str}"
        
        if not self.is_fixtures_cache_valid(date_str):
            return None
        
        cache_info = self.cache_index['fixtures'][cache_key]
        json_path = cache_info['json_path']
        
        try:
            fixtures = utils.load_json(json_path)
            logger.info(f"Loaded {len(fixtures)} cached fixtures for {date_str}")
            return fixtures
        except Exception as e:
            logger.warning(f"Error loading cached fixtures: {e}")
            return None
    
    def load_cached_team_players(self, team_id: int) -> Optional[List[Dict]]:
        """Load cached team players data."""
        cache_key = f"team_{team_id}"
        
        if not self.is_team_cache_valid(team_id):
            return None
        
        cache_info = self.cache_index['teams'][cache_key]
        json_path = cache_info['json_path']
        
        try:
            players = utils.load_json(json_path)
            logger.info(f"Loaded {len(players)} cached players for team {team_id}")
            return players
        except Exception as e:
            logger.warning(f"Error loading cached team players: {e}")
            return None
    
    def clear_cache(self, older_than_hours: int = 48) -> None:
        """Clear old cache entries."""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        
        # Clear old fixtures
        to_remove = []
        for cache_key, cache_info in self.cache_index['fixtures'].items():
            cached_time = datetime.fromisoformat(cache_info['timestamp'])
            if cached_time < cutoff_time:
                # Remove files
                try:
                    Path(cache_info['json_path']).unlink(missing_ok=True)
                    Path(cache_info['csv_path']).unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(f"Error removing cache files: {e}")
                
                to_remove.append(cache_key)
        
        for key in to_remove:
            del self.cache_index['fixtures'][key]
        
        # Clear old teams
        to_remove = []
        for cache_key, cache_info in self.cache_index['teams'].items():
            cached_time = datetime.fromisoformat(cache_info['timestamp'])
            if cached_time < cutoff_time:
                # Remove files
                try:
                    Path(cache_info['json_path']).unlink(missing_ok=True)
                    Path(cache_info['csv_path']).unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(f"Error removing cache files: {e}")
                
                to_remove.append(cache_key)
        
        for key in to_remove:
            del self.cache_index['teams'][key]
        
        self._save_cache_index()
        logger.info(f"Cleared {len(to_remove)} old cache entries")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'fixtures_cached': len(self.cache_index['fixtures']),
            'teams_cached': len(self.cache_index['teams']),
            'created': self.cache_index['created'],
            'last_updated': self.cache_index['last_updated'],
            'cache_dir': str(self.cache_dir)
        }

class PredictionStorage:
    """Handles storage of predictions and results."""
    
    def __init__(self, storage_dir: str = None):
        self.storage_dir = Path(storage_dir or config.DATA_DIR)
        self.storage_dir.mkdir(exist_ok=True)
    
    def save_predictions(self, predictions: List[Dict], date_str: str) -> str:
        """Save predictions to file."""
        filename = f"predictions_{date_str}.csv"
        filepath = self.storage_dir / filename
        
        if predictions:
            df = pd.DataFrame(predictions)
            utils.save_csv(df, str(filepath))
            
            # Also save as JSON for detailed data
            json_filename = f"predictions_{date_str}.json"
            json_filepath = self.storage_dir / json_filename
            utils.save_json(predictions, str(json_filepath))
            
            logger.info(f"Saved {len(predictions)} predictions to {filepath}")
        
        return str(filepath)
    
    def load_predictions(self, date_str: str) -> Optional[pd.DataFrame]:
        """Load predictions from file."""
        filename = f"predictions_{date_str}.csv"
        filepath = self.storage_dir / filename
        
        return utils.load_csv(str(filepath))
    
    def save_player_props(self, props: List[Dict], date_str: str) -> str:
        """Save player prop predictions to file."""
        filename = f"player_props_{date_str}.csv"
        filepath = self.storage_dir / filename
        
        if props:
            df = pd.DataFrame(props)
            utils.save_csv(df, str(filepath))
            
            # Also save as JSON
            json_filename = f"player_props_{date_str}.json"
            json_filepath = self.storage_dir / json_filename
            utils.save_json(props, str(json_filepath))
            
            logger.info(f"Saved {len(props)} player props to {filepath}")
        
        return str(filepath)
    
    def get_available_predictions(self) -> List[str]:
        """Get list of available prediction dates."""
        prediction_files = list(self.storage_dir.glob("predictions_*.csv"))
        dates = []
        
        for file in prediction_files:
            # Extract date from filename
            filename = file.stem
            if filename.startswith("predictions_"):
                date_str = filename.replace("predictions_", "")
                dates.append(date_str)
        
        return sorted(dates)

# Global cache instance
_cache = DataCache()
_storage = PredictionStorage()

def get_cache() -> DataCache:
    """Get the global cache instance."""
    return _cache

def get_storage() -> PredictionStorage:
    """Get the global storage instance."""
    return _storage

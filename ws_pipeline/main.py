"""
Main CLI orchestration for WhoScored pipeline.
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd

from . import config, utils, storage
from .fixtures_scraper import scrape_fixtures
from .teams_scraper import scrape_teams_from_fixtures
from .transform import clean_and_transform_data
from .predict import predict_fixture, predict_player_props_for_match

logger = utils.setup_logging(__name__)

class WSPipeline:
    """Main pipeline orchestrator."""
    
    def __init__(self):
        self.cache = storage.get_cache()
        self.storage = storage.get_storage()
    
    async def run_fixtures_scrape(self, date_filter: str = "today") -> str:
        """Run fixtures scraping."""
        logger.info(f"Starting fixtures scrape for {date_filter}")
        
        date_str = utils.get_current_date_str() if date_filter == "today" else date_filter
        
        # Check cache first
        cached_fixtures = self.cache.load_cached_fixtures(date_str)
        if cached_fixtures:
            logger.info(f"Using cached fixtures for {date_str}")
            return f"{config.DATA_DIR}/fixtures_{date_str}.csv"
        
        # Scrape fresh data
        try:
            fixtures = await scrape_fixtures(date_filter)
            
            if fixtures:
                # Convert to dict format for caching
                fixtures_data = []
                for fixture in fixtures:
                    fixtures_data.append({
                        'kickoff_utc': fixture.kickoff_utc.isoformat(),
                        'competition': fixture.competition,
                        'home_team_name': fixture.home_team_name,
                        'away_team_name': fixture.away_team_name,
                        'home_team_id': fixture.home_team_id,
                        'away_team_id': fixture.away_team_id,
                        'home_team_url': str(fixture.home_team_url) if fixture.home_team_url else None,
                        'away_team_url': str(fixture.away_team_url) if fixture.away_team_url else None
                    })
                
                # Cache the results
                self.cache.cache_fixtures(fixtures_data, date_str)
                
                logger.info(f"Successfully scraped {len(fixtures)} fixtures")
                return f"{config.DATA_DIR}/fixtures_{date_str}.csv"
            else:
                logger.warning("No fixtures found")
                return None
                
        except Exception as e:
            logger.error(f"Error in fixtures scrape: {e}")
            raise
    
    async def run_teams_scrape(self, fixtures_file: str) -> List[str]:
        """Run teams scraping from fixtures."""
        logger.info(f"Starting teams scrape from {fixtures_file}")
        
        if not Path(fixtures_file).exists():
            raise FileNotFoundError(f"Fixtures file not found: {fixtures_file}")
        
        # Load fixtures to get teams
        fixtures_df = utils.load_csv(fixtures_file)
        if fixtures_df is None or fixtures_df.empty:
            raise ValueError(f"No fixtures data in {fixtures_file}")
        
        # Get unique teams with URLs
        teams_to_scrape = set()
        for _, row in fixtures_df.iterrows():
            if pd.notna(row.get('home_team_id')) and pd.notna(row.get('home_team_url')):
                team_id = int(row['home_team_id'])
                # Check cache first
                if not self.cache.is_team_cache_valid(team_id):
                    teams_to_scrape.add((team_id, row['home_team_url']))
            
            if pd.notna(row.get('away_team_id')) and pd.notna(row.get('away_team_url')):
                team_id = int(row['away_team_id'])
                # Check cache first
                if not self.cache.is_team_cache_valid(team_id):
                    teams_to_scrape.add((team_id, row['away_team_url']))
        
        logger.info(f"Found {len(teams_to_scrape)} teams to scrape (after cache check)")
        
        if not teams_to_scrape:
            logger.info("All teams are cached, no scraping needed")
            # Return existing team files
            team_files = []
            for _, row in fixtures_df.iterrows():
                for team_id_col in ['home_team_id', 'away_team_id']:
                    if pd.notna(row.get(team_id_col)):
                        team_id = int(row[team_id_col])
                        team_file = f"{config.DATA_DIR}/team_{team_id}_players.csv"
                        if Path(team_file).exists():
                            team_files.append(team_file)
            return list(set(team_files))
        
        # Scrape teams with concurrency control
        from .teams_scraper import TeamsScraper
        
        semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_PAGES)
        scraper = TeamsScraper()
        
        async def scrape_single_team(team_id: int, team_url: str):
            async with semaphore:
                try:
                    players = await scraper.scrape_team_players(team_id, team_url)
                    
                    if players:
                        # Convert to dict format for caching
                        players_data = []
                        for player in players:
                            players_data.append({
                                'player_id': player.player_id,
                                'player_name': player.player_name,
                                'age': player.age,
                                'positions': ','.join(player.positions) if player.positions else None,
                                'apps_total': player.apps_total,
                                'apps_sub': player.apps_sub,
                                'minutes': player.minutes,
                                'goals': player.goals,
                                'assists': player.assists,
                                'yellow': player.yellow,
                                'red': player.red,
                                'shots_per_game': player.shots_per_game,
                                'pass_success': player.pass_success,
                                'aerials_won': player.aerials_won,
                                'motm': player.motm,
                                'rating': player.rating,
                                'team_id': player.team_id,
                                'season': player.season
                            })
                        
                        # Cache the results
                        self.cache.cache_team_players(players_data, team_id)
                        
                        return f"{config.DATA_DIR}/team_{team_id}_players.csv"
                    else:
                        logger.warning(f"No players found for team {team_id}")
                        return None
                        
                except Exception as e:
                    logger.error(f"Failed to scrape team {team_id}: {e}")
                    return None
        
        # Execute all team scraping tasks
        tasks = [scrape_single_team(team_id, team_url) for team_id, team_url in teams_to_scrape]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect successful results
        team_files = [r for r in results if isinstance(r, str) and r is not None]
        
        # Also include cached team files
        for _, row in fixtures_df.iterrows():
            for team_id_col in ['home_team_id', 'away_team_id']:
                if pd.notna(row.get(team_id_col)):
                    team_id = int(row[team_id_col])
                    team_file = f"{config.DATA_DIR}/team_{team_id}_players.csv"
                    if Path(team_file).exists() and team_file not in team_files:
                        team_files.append(team_file)
        
        logger.info(f"Successfully processed {len(team_files)} team files")
        return team_files
    
    async def run_predictions(self, fixtures_file: str, team_files: List[str], 
                            output_file: str = None) -> str:
        """Run predictions for fixtures."""
        logger.info(f"Starting predictions from {fixtures_file} and {len(team_files)} team files")
        
        try:
            # Clean and transform data
            fixtures_df, players_df, team_stats_df = clean_and_transform_data(fixtures_file, team_files)
            
            logger.info(f"Loaded {len(fixtures_df)} fixtures, {len(players_df)} players, {len(team_stats_df)} teams")
            
            # Generate predictions
            predictions = []
            player_props_all = []
            
            for _, fixture in fixtures_df.iterrows():
                try:
                    home_team_id = fixture.get('home_team_id')
                    away_team_id = fixture.get('away_team_id')
                    
                    if pd.isna(home_team_id) or pd.isna(away_team_id):
                        logger.warning(f"Missing team IDs for {fixture['home_team_name']} vs {fixture['away_team_name']}")
                        continue
                    
                    home_team_id = int(home_team_id)
                    away_team_id = int(away_team_id)
                    
                    # Match prediction
                    prediction = predict_fixture(
                        home_team_id, away_team_id, players_df, team_stats_df, fixtures_df
                    )
                    
                    # Add fixture information
                    prediction.update({
                        'fixture_id': f"{home_team_id}_{away_team_id}_{fixture['kickoff_utc']}",
                        'home_team_name': fixture['home_team_name'],
                        'away_team_name': fixture['away_team_name'],
                        'kickoff_utc': fixture['kickoff_utc'],
                        'competition': fixture['competition']
                    })
                    
                    predictions.append(prediction)
                    
                    # Player props prediction
                    player_props = predict_player_props_for_match(
                        home_team_id, away_team_id, players_df, team_stats_df
                    )
                    
                    # Add fixture context to player props
                    for prop in player_props:
                        prop.update({
                            'fixture_id': prediction['fixture_id'],
                            'home_team_name': fixture['home_team_name'],
                            'away_team_name': fixture['away_team_name'],
                            'kickoff_utc': fixture['kickoff_utc']
                        })
                    
                    player_props_all.extend(player_props)
                    
                except Exception as e:
                    logger.error(f"Error predicting fixture {fixture.get('home_team_name')} vs {fixture.get('away_team_name')}: {e}")
                    continue
            
            # Save predictions
            date_str = utils.get_current_date_str()
            
            if output_file:
                predictions_file = output_file
            else:
                predictions_file = self.storage.save_predictions(predictions, date_str)
            
            # Save player props
            if player_props_all:
                self.storage.save_player_props(player_props_all, date_str)
            
            logger.info(f"Generated {len(predictions)} match predictions and {len(player_props_all)} player props")
            return predictions_file
            
        except Exception as e:
            logger.error(f"Error in predictions: {e}")
            raise

async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="WhoScored scraper pipeline")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Fixtures command
    fixtures_parser = subparsers.add_parser('fixtures', help='Scrape fixtures')
    fixtures_parser.add_argument('--date', default='today', 
                               help='Date filter: today, tomorrow, or YYYY-MM-DD')
    
    # Teams command
    teams_parser = subparsers.add_parser('teams', help='Scrape team players')
    teams_parser.add_argument('--from-fixtures', required=True,
                            help='Path to fixtures CSV file')
    
    # Predict command
    predict_parser = subparsers.add_parser('predict', help='Generate predictions')
    predict_parser.add_argument('--from-fixtures', required=True,
                               help='Path to fixtures CSV file')
    predict_parser.add_argument('--out', help='Output file path')
    
    # Cache command
    cache_parser = subparsers.add_parser('cache', help='Cache management')
    cache_parser.add_argument('--clear', action='store_true', help='Clear old cache')
    cache_parser.add_argument('--stats', action='store_true', help='Show cache stats')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    pipeline = WSPipeline()
    
    try:
        if args.command == 'fixtures':
            result = await pipeline.run_fixtures_scrape(args.date)
            if result:
                print(f"Fixtures saved to: {result}")
            else:
                print("No fixtures found")
        
        elif args.command == 'teams':
            team_files = await pipeline.run_teams_scrape(args.from_fixtures)
            print(f"Team data saved to {len(team_files)} files:")
            for file in team_files:
                print(f"  {file}")
        
        elif args.command == 'predict':
            # First get team files from fixtures
            team_files = await pipeline.run_teams_scrape(args.from_fixtures)
            
            # Then run predictions
            predictions_file = await pipeline.run_predictions(args.from_fixtures, team_files, args.out)
            print(f"Predictions saved to: {predictions_file}")
        
        elif args.command == 'cache':
            if args.clear:
                pipeline.cache.clear_cache()
                print("Cache cleared")
            elif args.stats:
                stats = pipeline.cache.get_cache_stats()
                print("Cache Statistics:")
                for key, value in stats.items():
                    print(f"  {key}: {value}")
            else:
                cache_parser.print_help()
    
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

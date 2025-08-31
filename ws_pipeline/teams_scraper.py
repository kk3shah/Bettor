"""
WhoScored team and player stats scraper.
"""

import asyncio
import re
from typing import Dict, List, Optional, Tuple

import pandas as pd
from playwright.async_api import async_playwright, Page, Response
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from . import config, utils

logger = utils.setup_logging(__name__)

class PlayerRow(BaseModel):
    player_id: str
    player_name: str
    age: Optional[int] = None
    positions: Optional[List[str]] = None
    apps_total: Optional[int] = None
    apps_sub: Optional[int] = None
    minutes: Optional[int] = None
    goals: Optional[int] = None
    assists: Optional[int] = None
    yellow: Optional[int] = None
    red: Optional[int] = None
    shots_per_game: Optional[float] = None
    pass_success: Optional[float] = None
    aerials_won: Optional[float] = None
    motm: Optional[int] = None
    rating: Optional[float] = None
    team_id: int
    season: str

class TeamsScraper:
    def __init__(self):
        self.json_responses = []
    
    async def setup_page(self, page: Page) -> None:
        """Set up page with stealth settings and response listeners."""
        # Set user agent
        await page.set_extra_http_headers({
            'User-Agent': config.get_random_user_agent()
        })
        
        # Set viewport
        await page.set_viewport_size({
            'width': config.VIEWPORT_WIDTH,
            'height': config.VIEWPORT_HEIGHT
        })
        
        # Listen for JSON responses
        async def handle_response(response: Response):
            if (response.url and 'whoscored' in response.url and 
                'application/json' in response.headers.get('content-type', '')):
                try:
                    json_data = await response.json()
                    self.json_responses.append({
                        'url': response.url,
                        'data': json_data
                    })
                    logger.info(f"Captured JSON response from: {response.url}")
                except Exception as e:
                    logger.warning(f"Failed to parse JSON from {response.url}: {e}")
        
        page.on('response', handle_response)
    
    @retry(stop=stop_after_attempt(config.MAX_RETRIES), 
           wait=wait_exponential(multiplier=config.RETRY_BACKOFF_FACTOR))
    async def scrape_team_players(self, team_id: int, team_url: str) -> List[PlayerRow]:
        """Scrape player statistics for a specific team."""
        logger.info(f"Scraping team {team_id} players from {team_url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=config.HEADLESS,
                args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
            )
            
            try:
                context = await browser.new_context()
                page = await context.new_page()
                await self.setup_page(page)
                
                # Navigate to team page
                await page.goto(team_url, wait_until='networkidle')
                await utils.random_delay()
                
                # Try to navigate to the archive/stats section
                archive_url = await self._get_archive_url(page, team_id)
                if archive_url:
                    logger.info(f"Navigating to archive: {archive_url}")
                    await page.goto(archive_url, wait_until='networkidle')
                    await utils.random_delay()
                
                # Look for player statistics table
                await self._ensure_stats_table_visible(page)
                
                # Try to extract from JSON responses first
                players = await self._extract_players_from_json(team_id)
                
                # Fallback to DOM parsing
                if not players:
                    logger.info("No JSON player data found, falling back to DOM parsing")
                    players = await self._extract_players_from_dom(page, team_id)
                
                logger.info(f"Successfully scraped {len(players)} players for team {team_id}")
                return players
                
            except Exception as e:
                logger.error(f"Error scraping team {team_id}: {e}")
                return []
            finally:
                await browser.close()
    
    async def _get_archive_url(self, page: Page, team_id: int) -> Optional[str]:
        """Get the archive URL for the team."""
        try:
            # Look for archive/history links
            archive_selectors = [
                'a[href*="archive"]',
                'a[href*="history"]',
                'a[href*="statistics"]',
                'a[href*="squad"]'
            ]
            
            for selector in archive_selectors:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    href = await element.get_attribute('href')
                    if href and 'archive' in href.lower():
                        if not href.startswith('http'):
                            href = config.WHOSCORED_BASE + href
                        return href
            
            # If no archive link found, try to construct it
            # Common pattern: /Teams/{id}/Archive/{country}-{team-name}
            current_url = page.url
            if '/Teams/' in current_url:
                # Try to extract country and team name from current URL
                match = re.search(r'/Teams/\d+/Show/([^/]+)', current_url)
                if match:
                    country_team = match.group(1)
                    return f"{config.WHOSCORED_BASE}/Teams/{team_id}/Archive/{country_team}"
            
            return None
            
        except Exception as e:
            logger.warning(f"Error getting archive URL: {e}")
            return None
    
    async def _ensure_stats_table_visible(self, page: Page) -> None:
        """Ensure the player statistics table is visible."""
        try:
            # Look for tabs or sections that might contain player stats
            tab_selectors = [
                'a[href*="Summary"]',
                '.tab-summary',
                '.summary-tab',
                'a:has-text("Summary")',
                'a:has-text("Overall")',
                'a:has-text("Statistics")'
            ]
            
            for selector in tab_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await element.click()
                        await page.wait_for_timeout(2000)
                        break
                except:
                    continue
            
            # Wait for table to be visible
            table_selectors = [
                'table',
                '.statistics-table',
                '.player-table',
                '[data-testid*="table"]'
            ]
            
            for selector in table_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=10000)
                    break
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Error ensuring stats table visibility: {e}")
    
    async def _extract_players_from_json(self, team_id: int) -> List[PlayerRow]:
        """Extract player data from captured JSON responses."""
        players = []
        
        for response in self.json_responses:
            try:
                data = response['data']
                
                # Look for player-like data structures
                if isinstance(data, dict):
                    player_keys = ['players', 'squad', 'roster', 'statistics']
                    for key in player_keys:
                        if key in data and isinstance(data[key], list):
                            players.extend(self._parse_json_players(data[key], team_id))
                
                elif isinstance(data, list):
                    players.extend(self._parse_json_players(data, team_id))
                    
            except Exception as e:
                logger.warning(f"Error parsing JSON response for players: {e}")
        
        return players
    
    def _parse_json_players(self, players_data: List[Dict], team_id: int) -> List[PlayerRow]:
        """Parse players from JSON data."""
        players = []
        
        for item in players_data:
            try:
                if not isinstance(item, dict):
                    continue
                
                # Extract player information
                player_name = None
                name_keys = ['name', 'playerName', 'displayName', 'fullName']
                for key in name_keys:
                    if key in item:
                        player_name = str(item[key])
                        break
                
                if not player_name:
                    continue
                
                # Create player ID
                player_id = f"{team_id}_{player_name.lower().replace(' ', '_')}"
                
                # Extract statistics
                age = utils.safe_int(item.get('age'))
                positions = utils.parse_positions(item.get('position', ''))
                
                # Apps parsing
                apps_total, apps_sub = utils.parse_apps_format(item.get('apps', ''))
                
                # Other stats
                minutes = utils.safe_int(item.get('minutes', item.get('mins')))
                goals = utils.safe_int(item.get('goals'))
                assists = utils.safe_int(item.get('assists'))
                yellow = utils.safe_int(item.get('yellow', item.get('yellowCards')))
                red = utils.safe_int(item.get('red', item.get('redCards')))
                shots_per_game = utils.safe_float(item.get('shotsPerGame', item.get('spg')))
                pass_success = utils.parse_percentage(item.get('passSuccess', item.get('ps%')))
                aerials_won = utils.safe_float(item.get('aerialsWon', item.get('aerials')))
                motm = utils.safe_int(item.get('motm', item.get('manOfTheMatch')))
                rating = utils.safe_float(item.get('rating', item.get('averageRating')))
                
                player = PlayerRow(
                    player_id=player_id,
                    player_name=player_name,
                    age=age,
                    positions=positions,
                    apps_total=apps_total,
                    apps_sub=apps_sub,
                    minutes=minutes,
                    goals=goals,
                    assists=assists,
                    yellow=yellow,
                    red=red,
                    shots_per_game=shots_per_game,
                    pass_success=pass_success,
                    aerials_won=aerials_won,
                    motm=motm,
                    rating=rating,
                    team_id=team_id,
                    season=config.DEFAULT_SEASON
                )
                players.append(player)
                
            except Exception as e:
                logger.warning(f"Error parsing player item: {e}")
        
        return players
    
    async def _extract_players_from_dom(self, page: Page, team_id: int) -> List[PlayerRow]:
        """Extract player data from DOM as fallback."""
        players = []
        
        try:
            # Find the statistics table
            table = await page.query_selector('table')
            if not table:
                logger.warning("No table found on page")
                return players
            
            # Get table headers
            header_row = await table.query_selector('thead tr, tr:first-child')
            if not header_row:
                logger.warning("No header row found in table")
                return players
            
            header_cells = await header_row.query_selector_all('th, td')
            headers = []
            for cell in header_cells:
                text = await cell.text_content()
                headers.append(text.strip() if text else '')
            
            logger.info(f"Found table headers: {headers}")
            
            # Map headers to indices
            header_map = {}
            for i, header in enumerate(headers):
                header_lower = header.lower()
                if 'player' in header_lower or 'name' in header_lower:
                    header_map['player'] = i
                elif 'age' in header_lower:
                    header_map['age'] = i
                elif 'pos' in header_lower:
                    header_map['positions'] = i
                elif 'apps' in header_lower or 'app' in header_lower:
                    header_map['apps'] = i
                elif 'mins' in header_lower or 'minutes' in header_lower:
                    header_map['minutes'] = i
                elif 'goals' in header_lower:
                    header_map['goals'] = i
                elif 'assists' in header_lower:
                    header_map['assists'] = i
                elif 'yellow' in header_lower or 'yel' in header_lower:
                    header_map['yellow'] = i
                elif 'red' in header_lower:
                    header_map['red'] = i
                elif 'spg' in header_lower or 'shots' in header_lower:
                    header_map['shots_per_game'] = i
                elif 'ps%' in header_lower or 'pass' in header_lower:
                    header_map['pass_success'] = i
                elif 'aerials' in header_lower:
                    header_map['aerials_won'] = i
                elif 'motm' in header_lower:
                    header_map['motm'] = i
                elif 'rating' in header_lower:
                    header_map['rating'] = i
            
            # Get data rows
            data_rows = await table.query_selector_all('tbody tr, tr:not(:first-child)')
            
            for row in data_rows:
                try:
                    cells = await row.query_selector_all('td, th')
                    if len(cells) < len(headers):
                        continue
                    
                    row_data = []
                    for cell in cells:
                        text = await cell.text_content()
                        row_data.append(text.strip() if text else '')
                    
                    # Extract player name
                    if 'player' not in header_map:
                        continue
                    
                    player_name = row_data[header_map['player']]
                    if not player_name or player_name == '-':
                        continue
                    
                    # Create player ID
                    player_id = f"{team_id}_{player_name.lower().replace(' ', '_')}"
                    
                    # Extract other fields
                    age = utils.safe_int(row_data[header_map.get('age', -1)]) if header_map.get('age', -1) < len(row_data) else None
                    positions = utils.parse_positions(row_data[header_map.get('positions', -1)]) if header_map.get('positions', -1) < len(row_data) else []
                    
                    apps_total, apps_sub = None, None
                    if header_map.get('apps', -1) < len(row_data):
                        apps_total, apps_sub = utils.parse_apps_format(row_data[header_map['apps']])
                    
                    minutes = utils.safe_int(row_data[header_map.get('minutes', -1)]) if header_map.get('minutes', -1) < len(row_data) else None
                    goals = utils.safe_int(row_data[header_map.get('goals', -1)]) if header_map.get('goals', -1) < len(row_data) else None
                    assists = utils.safe_int(row_data[header_map.get('assists', -1)]) if header_map.get('assists', -1) < len(row_data) else None
                    yellow = utils.safe_int(row_data[header_map.get('yellow', -1)]) if header_map.get('yellow', -1) < len(row_data) else None
                    red = utils.safe_int(row_data[header_map.get('red', -1)]) if header_map.get('red', -1) < len(row_data) else None
                    shots_per_game = utils.safe_float(row_data[header_map.get('shots_per_game', -1)]) if header_map.get('shots_per_game', -1) < len(row_data) else None
                    pass_success = utils.parse_percentage(row_data[header_map.get('pass_success', -1)]) if header_map.get('pass_success', -1) < len(row_data) else None
                    aerials_won = utils.safe_float(row_data[header_map.get('aerials_won', -1)]) if header_map.get('aerials_won', -1) < len(row_data) else None
                    motm = utils.safe_int(row_data[header_map.get('motm', -1)]) if header_map.get('motm', -1) < len(row_data) else None
                    rating = utils.safe_float(row_data[header_map.get('rating', -1)]) if header_map.get('rating', -1) < len(row_data) else None
                    
                    player = PlayerRow(
                        player_id=player_id,
                        player_name=player_name,
                        age=age,
                        positions=positions,
                        apps_total=apps_total,
                        apps_sub=apps_sub,
                        minutes=minutes,
                        goals=goals,
                        assists=assists,
                        yellow=yellow,
                        red=red,
                        shots_per_game=shots_per_game,
                        pass_success=pass_success,
                        aerials_won=aerials_won,
                        motm=motm,
                        rating=rating,
                        team_id=team_id,
                        season=config.DEFAULT_SEASON
                    )
                    players.append(player)
                    
                except Exception as e:
                    logger.warning(f"Error parsing player row: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error in DOM extraction for team {team_id}: {e}")
        
        return players
    
    async def save_team_players(self, players: List[PlayerRow], team_id: int) -> None:
        """Save team players to JSON and CSV files."""
        if not players:
            logger.warning(f"No players to save for team {team_id}")
            return
        
        # Convert to DataFrame
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
        
        df = pd.DataFrame(players_data)
        
        # Save files
        json_path = f"{config.DATA_DIR}/team_{team_id}_players.json"
        csv_path = f"{config.DATA_DIR}/team_{team_id}_players.csv"
        
        utils.save_json(players_data, json_path)
        utils.save_csv(df, csv_path)
        
        logger.info(f"Saved {len(players)} players for team {team_id} to {json_path} and {csv_path}")

async def scrape_teams_from_fixtures(fixtures_file: str) -> None:
    """Scrape all teams from a fixtures file."""
    # Load fixtures
    fixtures_df = utils.load_csv(fixtures_file)
    if fixtures_df is None:
        logger.error(f"Could not load fixtures from {fixtures_file}")
        return
    
    # Get unique teams
    teams = set()
    for _, row in fixtures_df.iterrows():
        if pd.notna(row.get('home_team_id')) and pd.notna(row.get('home_team_url')):
            teams.add((int(row['home_team_id']), row['home_team_url']))
        if pd.notna(row.get('away_team_id')) and pd.notna(row.get('away_team_url')):
            teams.add((int(row['away_team_id']), row['away_team_url']))
    
    logger.info(f"Found {len(teams)} unique teams to scrape")
    
    # Scrape teams with concurrency control
    semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_PAGES)
    scraper = TeamsScraper()
    
    async def scrape_single_team(team_id: int, team_url: str):
        async with semaphore:
            try:
                players = await scraper.scrape_team_players(team_id, team_url)
                await scraper.save_team_players(players, team_id)
                return len(players)
            except Exception as e:
                logger.error(f"Failed to scrape team {team_id}: {e}")
                return 0
    
    # Execute all team scraping tasks
    tasks = [scrape_single_team(team_id, team_url) for team_id, team_url in teams]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    total_players = sum(r for r in results if isinstance(r, int))
    logger.info(f"Successfully scraped {total_players} total players from {len(teams)} teams")

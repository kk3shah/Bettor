"""
WhoScored fixtures scraper.
"""

import asyncio
import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

import pandas as pd
from playwright.async_api import async_playwright, Page, Response
from pydantic import BaseModel, HttpUrl
from tenacity import retry, stop_after_attempt, wait_exponential

from . import config, utils

logger = utils.setup_logging(__name__)

class Fixture(BaseModel):
    kickoff_utc: datetime
    competition: str
    home_team_name: str
    away_team_name: str
    home_team_id: Optional[int] = None
    away_team_id: Optional[int] = None
    home_team_url: Optional[HttpUrl] = None
    away_team_url: Optional[HttpUrl] = None

class FixturesScraper:
    def __init__(self):
        self.fixtures_data = []
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
    async def scrape_fixtures(self, date_filter: str = "today") -> List[Fixture]:
        """Scrape fixtures from WhoScored livescores page."""
        logger.info(f"Starting fixtures scrape for {date_filter}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=config.HEADLESS,
                args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
            )
            
            try:
                context = await browser.new_context()
                page = await context.new_page()
                await self.setup_page(page)
                
                # Navigate to livescores
                logger.info(f"Navigating to {config.LIVESCORES_URL}")
                await page.goto(config.LIVESCORES_URL, wait_until='networkidle')
                
                # Wait for fixtures to load
                await page.wait_for_selector('.fixture, .match-row, [data-testid*="fixture"]', timeout=30000)
                await utils.random_delay()
                
                # Try to extract from JSON responses first
                fixtures = await self._extract_from_json()
                
                # Fallback to DOM parsing if no JSON data
                if not fixtures:
                    logger.info("No JSON fixtures found, falling back to DOM parsing")
                    fixtures = await self._extract_from_dom(page)
                
                logger.info(f"Successfully scraped {len(fixtures)} fixtures")
                return fixtures
                
            except Exception as e:
                logger.error(f"Error scraping fixtures: {e}")
                raise
            finally:
                await browser.close()
    
    async def _extract_from_json(self) -> List[Fixture]:
        """Extract fixtures from captured JSON responses."""
        fixtures = []
        
        for response in self.json_responses:
            try:
                data = response['data']
                
                # Look for fixture-like data structures
                if isinstance(data, dict):
                    # Check various possible keys for fixtures
                    fixture_keys = ['fixtures', 'matches', 'events', 'games']
                    for key in fixture_keys:
                        if key in data and isinstance(data[key], list):
                            fixtures.extend(self._parse_json_fixtures(data[key]))
                
                elif isinstance(data, list):
                    fixtures.extend(self._parse_json_fixtures(data))
                    
            except Exception as e:
                logger.warning(f"Error parsing JSON response: {e}")
        
        return fixtures
    
    def _parse_json_fixtures(self, fixtures_data: List[Dict]) -> List[Fixture]:
        """Parse fixtures from JSON data."""
        fixtures = []
        
        for item in fixtures_data:
            try:
                # Try to identify fixture structure
                if not isinstance(item, dict):
                    continue
                
                # Look for common fixture fields
                home_team = None
                away_team = None
                kickoff = None
                competition = None
                
                # Various possible field names
                home_keys = ['homeTeam', 'home_team', 'home', 'homeTeamName']
                away_keys = ['awayTeam', 'away_team', 'away', 'awayTeamName']
                time_keys = ['kickoff', 'startTime', 'date', 'time', 'kickoffTime']
                comp_keys = ['competition', 'league', 'tournament', 'comp']
                
                for key in home_keys:
                    if key in item:
                        home_team = item[key]
                        if isinstance(home_team, dict):
                            home_team = home_team.get('name', home_team.get('displayName', ''))
                        break
                
                for key in away_keys:
                    if key in item:
                        away_team = item[key]
                        if isinstance(away_team, dict):
                            away_team = away_team.get('name', away_team.get('displayName', ''))
                        break
                
                for key in time_keys:
                    if key in item:
                        kickoff = item[key]
                        break
                
                for key in comp_keys:
                    if key in item:
                        competition = item[key]
                        if isinstance(competition, dict):
                            competition = competition.get('name', competition.get('displayName', ''))
                        break
                
                if home_team and away_team and kickoff:
                    # Parse kickoff time
                    if isinstance(kickoff, str):
                        try:
                            kickoff_dt = datetime.fromisoformat(kickoff.replace('Z', '+00:00'))
                        except:
                            continue
                    else:
                        continue
                    
                    fixture = Fixture(
                        kickoff_utc=kickoff_dt,
                        competition=competition or "Unknown",
                        home_team_name=str(home_team),
                        away_team_name=str(away_team)
                    )
                    fixtures.append(fixture)
                    
            except Exception as e:
                logger.warning(f"Error parsing fixture item: {e}")
        
        return fixtures
    
    async def _extract_from_dom(self, page: Page) -> List[Fixture]:
        """Extract fixtures from DOM as fallback."""
        fixtures = []
        
        try:
            # Look for fixture containers with various selectors
            selectors = [
                '.fixture',
                '.match-row',
                '[data-testid*="fixture"]',
                '.live-score-row',
                '.match-item'
            ]
            
            fixture_elements = None
            for selector in selectors:
                try:
                    fixture_elements = await page.query_selector_all(selector)
                    if fixture_elements:
                        logger.info(f"Found {len(fixture_elements)} fixtures with selector: {selector}")
                        break
                except:
                    continue
            
            if not fixture_elements:
                logger.warning("No fixture elements found with any selector")
                return fixtures
            
            for element in fixture_elements:
                try:
                    # Extract team names
                    team_links = await element.query_selector_all('a[href*="/Teams/"]')
                    if len(team_links) >= 2:
                        home_team_name = await team_links[0].text_content()
                        away_team_name = await team_links[1].text_content()
                        
                        # Extract team URLs and IDs
                        home_team_url = await team_links[0].get_attribute('href')
                        away_team_url = await team_links[1].get_attribute('href')
                        
                        if home_team_url and not home_team_url.startswith('http'):
                            home_team_url = config.WHOSCORED_BASE + home_team_url
                        if away_team_url and not away_team_url.startswith('http'):
                            away_team_url = config.WHOSCORED_BASE + away_team_url
                        
                        home_team_id = utils.extract_team_id(home_team_url) if home_team_url else None
                        away_team_id = utils.extract_team_id(away_team_url) if away_team_url else None
                        
                        # Extract time (this is tricky and site-specific)
                        time_element = await element.query_selector('.time, .kickoff, [data-time]')
                        kickoff_time = None
                        
                        if time_element:
                            time_text = await time_element.text_content()
                            # Try to parse various time formats
                            kickoff_time = self._parse_kickoff_time(time_text)
                        
                        if not kickoff_time:
                            # Default to current time + 1 hour as fallback
                            kickoff_time = datetime.now(timezone.utc)
                        
                        # Extract competition
                        comp_element = await element.query_selector('.competition, .league')
                        competition = "Premier League"  # Default assumption
                        if comp_element:
                            competition = await comp_element.text_content()
                        
                        if home_team_name and away_team_name:
                            fixture = Fixture(
                                kickoff_utc=kickoff_time,
                                competition=competition.strip(),
                                home_team_name=home_team_name.strip(),
                                away_team_name=away_team_name.strip(),
                                home_team_id=home_team_id,
                                away_team_id=away_team_id,
                                home_team_url=home_team_url,
                                away_team_url=away_team_url
                            )
                            fixtures.append(fixture)
                
                except Exception as e:
                    logger.warning(f"Error parsing fixture element: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error in DOM extraction: {e}")
        
        return fixtures
    
    def _parse_kickoff_time(self, time_text: str) -> Optional[datetime]:
        """Parse kickoff time from various text formats."""
        if not time_text:
            return None
        
        time_text = time_text.strip()
        
        # Try various time formats
        patterns = [
            r'(\d{1,2}):(\d{2})',  # HH:MM
            r'(\d{1,2})\.(\d{2})',  # HH.MM
        ]
        
        for pattern in patterns:
            match = re.search(pattern, time_text)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))
                
                # Assume today's date for now (this could be improved)
                now = datetime.now(timezone.utc)
                kickoff = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # If time has passed today, assume it's tomorrow
                if kickoff < now:
                    kickoff = kickoff.replace(day=kickoff.day + 1)
                
                return kickoff
        
        return None
    
    async def save_fixtures(self, fixtures: List[Fixture], date_str: str) -> None:
        """Save fixtures to JSON and CSV files."""
        if not fixtures:
            logger.warning("No fixtures to save")
            return
        
        # Convert to DataFrame
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
        
        df = pd.DataFrame(fixtures_data)
        
        # Save files
        json_path = f"{config.DATA_DIR}/fixtures_{date_str}.json"
        csv_path = f"{config.DATA_DIR}/fixtures_{date_str}.csv"
        
        utils.save_json(fixtures_data, json_path)
        utils.save_csv(df, csv_path)
        
        logger.info(f"Saved {len(fixtures)} fixtures to {json_path} and {csv_path}")

async def scrape_fixtures(date_filter: str = "today") -> List[Fixture]:
    """Main function to scrape fixtures."""
    scraper = FixturesScraper()
    return await scraper.scrape_fixtures(date_filter)

#!/usr/bin/env python3
"""
Direct WhoScored API scraper that bypasses anti-bot protection.
Uses direct API endpoints instead of DOM parsing.
"""

import requests
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time
import random

class DirectWhoScoredScraper:
    """Direct API scraper for WhoScored data."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.whoscored.com/',
            'Origin': 'https://www.whoscored.com',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        })
    
    def get_premier_league_fixtures(self) -> List[Dict[str, Any]]:
        """Get Premier League fixtures directly from WhoScored API."""
        try:
            # Premier League tournament ID on WhoScored
            tournament_id = 2  # Premier League
            
            # Try different API endpoints that WhoScored uses
            api_endpoints = [
                f"https://www.whoscored.com/tournamentsfeed/{tournament_id}/Fixtures",
                f"https://www.whoscored.com/StatisticsFeed/1/GetFixturesByTournament?tournamentId={tournament_id}",
                f"https://www.whoscored.com/Matches/GetFixtures?tournamentId={tournament_id}",
                "https://www.whoscored.com/livescores/fixtures",
                "https://www.whoscored.com/StatisticsFeed/1/GetLiveScores"
            ]
            
            fixtures = []
            
            for endpoint in api_endpoints:
                try:
                    print(f"🔍 Trying endpoint: {endpoint}")
                    
                    response = self.session.get(endpoint, timeout=10)
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            print(f"✅ Got JSON response from {endpoint}")
                            print(f"📊 Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                            
                            # Extract fixtures from response
                            extracted = self._extract_fixtures_from_response(data)
                            if extracted:
                                fixtures.extend(extracted)
                                print(f"✅ Extracted {len(extracted)} fixtures from {endpoint}")
                            
                        except json.JSONDecodeError:
                            print(f"⚠️ Not JSON response from {endpoint}")
                            # Try to extract from HTML if it contains JSON
                            fixtures_from_html = self._extract_fixtures_from_html(response.text)
                            if fixtures_from_html:
                                fixtures.extend(fixtures_from_html)
                                print(f"✅ Extracted {len(fixtures_from_html)} fixtures from HTML")
                    else:
                        print(f"❌ HTTP {response.status_code} from {endpoint}")
                    
                    # Random delay between requests
                    time.sleep(random.uniform(2, 5))
                    
                except Exception as e:
                    print(f"❌ Error with {endpoint}: {e}")
                    continue
            
            # Remove duplicates and return
            unique_fixtures = self._deduplicate_fixtures(fixtures)
            print(f"🎯 Total unique fixtures found: {len(unique_fixtures)}")
            
            return unique_fixtures
            
        except Exception as e:
            print(f"❌ Error getting fixtures: {e}")
            return []
    
    def _extract_fixtures_from_response(self, data: Any) -> List[Dict[str, Any]]:
        """Extract fixtures from API response."""
        fixtures = []
        
        try:
            # Handle different response formats
            if isinstance(data, dict):
                # Look for fixtures in common keys
                for key in ['fixtures', 'matches', 'games', 'data', 'results']:
                    if key in data and isinstance(data[key], list):
                        fixtures.extend(self._parse_fixture_list(data[key]))
                
                # Check if the dict itself contains fixture data
                if self._looks_like_fixture(data):
                    fixtures.append(self._parse_fixture_dict(data))
            
            elif isinstance(data, list):
                # Direct list of fixtures
                fixtures.extend(self._parse_fixture_list(data))
        
        except Exception as e:
            print(f"⚠️ Error extracting fixtures: {e}")
        
        return fixtures
    
    def _extract_fixtures_from_html(self, html: str) -> List[Dict[str, Any]]:
        """Extract fixtures from HTML that might contain embedded JSON."""
        fixtures = []
        
        try:
            # Look for JSON data in script tags
            json_patterns = [
                r'var\s+fixtures\s*=\s*(\[.*?\]);',
                r'var\s+matches\s*=\s*(\[.*?\]);',
                r'"fixtures"\s*:\s*(\[.*?\])',
                r'"matches"\s*:\s*(\[.*?\])',
                r'window\.fixtures\s*=\s*(\[.*?\]);'
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, html, re.DOTALL)
                for match in matches:
                    try:
                        data = json.loads(match)
                        extracted = self._parse_fixture_list(data)
                        fixtures.extend(extracted)
                        print(f"✅ Extracted {len(extracted)} fixtures from HTML JSON")
                    except json.JSONDecodeError:
                        continue
        
        except Exception as e:
            print(f"⚠️ Error extracting from HTML: {e}")
        
        return fixtures
    
    def _parse_fixture_list(self, fixture_list: List[Any]) -> List[Dict[str, Any]]:
        """Parse a list of fixture objects."""
        fixtures = []
        
        for item in fixture_list:
            if isinstance(item, dict) and self._looks_like_fixture(item):
                parsed = self._parse_fixture_dict(item)
                if parsed:
                    fixtures.append(parsed)
        
        return fixtures
    
    def _looks_like_fixture(self, data: Dict[str, Any]) -> bool:
        """Check if a dict looks like a fixture."""
        fixture_indicators = [
            'home', 'away', 'homeTeam', 'awayTeam', 'home_team', 'away_team',
            'kickoff', 'kickOff', 'startTime', 'matchTime', 'date'
        ]
        
        return any(key in data for key in fixture_indicators)
    
    def _parse_fixture_dict(self, fixture: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a single fixture dictionary."""
        try:
            # Extract team names
            home_team = self._extract_team_name(fixture, 'home')
            away_team = self._extract_team_name(fixture, 'away')
            
            if not home_team or not away_team:
                return None
            
            # Extract kickoff time
            kickoff = self._extract_kickoff_time(fixture)
            
            if not kickoff:
                return None
            
            return {
                'home_team': home_team,
                'away_team': away_team,
                'kickoff_utc': kickoff,
                'competition': 'Premier League',
                'source': 'whoscored_direct'
            }
        
        except Exception as e:
            print(f"⚠️ Error parsing fixture: {e}")
            return None
    
    def _extract_team_name(self, fixture: Dict[str, Any], side: str) -> Optional[str]:
        """Extract team name from fixture data."""
        possible_keys = [
            f'{side}Team', f'{side}_team', side,
            f'{side}TeamName', f'{side}_team_name',
            f'{side}Name', f'{side}_name'
        ]
        
        for key in possible_keys:
            if key in fixture:
                value = fixture[key]
                if isinstance(value, str):
                    return value.strip()
                elif isinstance(value, dict) and 'name' in value:
                    return value['name'].strip()
        
        return None
    
    def _extract_kickoff_time(self, fixture: Dict[str, Any]) -> Optional[datetime]:
        """Extract kickoff time from fixture data."""
        time_keys = [
            'kickoff', 'kickOff', 'startTime', 'matchTime', 
            'date', 'datetime', 'timestamp'
        ]
        
        for key in time_keys:
            if key in fixture:
                value = fixture[key]
                
                try:
                    # Handle different time formats
                    if isinstance(value, str):
                        # Try parsing different date formats
                        formats = [
                            '%Y-%m-%dT%H:%M:%S',
                            '%Y-%m-%d %H:%M:%S',
                            '%d/%m/%Y %H:%M',
                            '%Y-%m-%dT%H:%M:%SZ'
                        ]
                        
                        for fmt in formats:
                            try:
                                return datetime.strptime(value, fmt)
                            except ValueError:
                                continue
                    
                    elif isinstance(value, (int, float)):
                        # Unix timestamp
                        return datetime.fromtimestamp(value)
                
                except Exception:
                    continue
        
        return None
    
    def _deduplicate_fixtures(self, fixtures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate fixtures."""
        seen = set()
        unique = []
        
        for fixture in fixtures:
            key = (fixture['home_team'], fixture['away_team'], fixture['kickoff_utc'])
            if key not in seen:
                seen.add(key)
                unique.append(fixture)
        
        return unique

def test_direct_scraper():
    """Test the direct scraper."""
    print("🚀 Testing Direct WhoScored Scraper...")
    
    scraper = DirectWhoScoredScraper()
    fixtures = scraper.get_premier_league_fixtures()
    
    if fixtures:
        print(f"\n✅ Successfully scraped {len(fixtures)} fixtures:")
        for fixture in fixtures[:5]:  # Show first 5
            print(f"  - {fixture['home_team']} vs {fixture['away_team']} at {fixture['kickoff_utc']}")
    else:
        print("\n❌ No fixtures found")
    
    return fixtures

if __name__ == "__main__":
    test_direct_scraper()

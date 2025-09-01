#!/usr/bin/env python3
"""
Google Search Scraper for Real Upcoming Soccer Matches
Scrapes Google search results for "soccer matches next 7 days" to get real fixtures.
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

class GoogleMatchesScraper:
    """Scraper for real upcoming soccer matches from Google search."""
    
    def __init__(self):
        """Initialize the scraper."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def search_upcoming_matches(self) -> List[Dict[str, Any]]:
        """Search Google for upcoming soccer matches in next 7 days."""
        print("🔍 Searching Google for upcoming soccer matches...")
        
        search_queries = [
            "soccer matches next 7 days",
            "football fixtures this week",
            "upcoming soccer games September 2025",
            "premier league la liga bundesliga matches this week"
        ]
        
        all_matches = []
        
        for query in search_queries:
            try:
                matches = self._search_google(query)
                all_matches.extend(matches)
                print(f"✅ Found {len(matches)} matches from query: {query}")
            except Exception as e:
                print(f"⚠️ Error searching '{query}': {e}")
                continue
        
        # Remove duplicates and sort by date
        unique_matches = self._deduplicate_matches(all_matches)
        print(f"🎯 Total unique matches found: {len(unique_matches)}")
        
        return unique_matches
    
    def _search_google(self, query: str) -> List[Dict[str, Any]]:
        """Search Google for a specific query and extract match information."""
        try:
            # Google search URL
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            matches = []
            
            # Look for sports cards/widgets
            sports_cards = soup.find_all('div', class_=re.compile(r'sports|match|game', re.I))
            
            for card in sports_cards:
                match_info = self._extract_match_from_card(card)
                if match_info:
                    matches.append(match_info)
            
            # Look for structured data in text
            text_matches = self._extract_matches_from_text(soup.get_text())
            matches.extend(text_matches)
            
            return matches
            
        except Exception as e:
            print(f"❌ Error searching Google: {e}")
            return []
    
    def _extract_match_from_card(self, card) -> Dict[str, Any]:
        """Extract match information from a sports card/widget."""
        try:
            # Look for team names
            teams = []
            team_elements = card.find_all(['span', 'div'], string=re.compile(r'[A-Z][a-z]+ (FC|United|City|Arsenal|Chelsea|Liverpool|Madrid|Barcelona|Bayern|Milan|PSG)', re.I))
            
            for elem in team_elements[:2]:  # Get first two teams
                teams.append(elem.get_text().strip())
            
            if len(teams) < 2:
                return None
            
            # Look for date/time
            date_elem = card.find(['span', 'div'], string=re.compile(r'(Sep|Sept|September|Oct|October|Nov|November)', re.I))
            time_elem = card.find(['span', 'div'], string=re.compile(r'\d{1,2}:\d{2}', re.I))
            
            match_date = self._parse_date_time(
                date_elem.get_text() if date_elem else "",
                time_elem.get_text() if time_elem else ""
            )
            
            # Look for league/competition
            league_elem = card.find(['span', 'div'], string=re.compile(r'(Premier League|La Liga|Bundesliga|Serie A|Ligue 1|Champions League)', re.I))
            league = league_elem.get_text().strip() if league_elem else "Unknown League"
            
            return {
                'home_team': teams[0],
                'away_team': teams[1],
                'league': league,
                'kickoff_time': match_date.isoformat() if match_date else None,
                'source': 'Google Search',
                'stadium': 'TBD',
                'timezone': 'EST'
            }
            
        except Exception as e:
            print(f"⚠️ Error extracting match from card: {e}")
            return None
    
    def _extract_matches_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract match information from plain text using regex patterns."""
        matches = []
        
        # Pattern for "Team A vs Team B" or "Team A v Team B"
        vs_pattern = r'([A-Z][a-z]+(?: [A-Z][a-z]+)*)\s+(?:vs?\.?|v)\s+([A-Z][a-z]+(?: [A-Z][a-z]+)*)'
        
        # Pattern for dates like "Sep 5", "September 7", etc.
        date_pattern = r'(Sep|Sept|September|Oct|October|Nov|November)\s+(\d{1,2})'
        
        # Pattern for times like "3:00 PM", "15:30", etc.
        time_pattern = r'(\d{1,2}):(\d{2})\s*(AM|PM|EST|ET)?'
        
        vs_matches = re.findall(vs_pattern, text, re.IGNORECASE)
        dates = re.findall(date_pattern, text, re.IGNORECASE)
        times = re.findall(time_pattern, text, re.IGNORECASE)
        
        # Combine the information
        for i, (team1, team2) in enumerate(vs_matches[:10]):  # Limit to 10 matches
            match_date = None
            if i < len(dates):
                month, day = dates[i]
                match_date = self._parse_date_from_parts(month, day)
            
            match_time = "15:00"  # Default time
            if i < len(times):
                hour, minute, period = times[i]
                match_time = f"{hour}:{minute}"
                if period and period.upper() in ['PM', 'ET', 'EST'] and int(hour) < 12:
                    match_time = f"{int(hour) + 12}:{minute}"
            
            # Combine date and time
            if match_date:
                try:
                    full_datetime = datetime.combine(match_date.date(), 
                                                   datetime.strptime(match_time, "%H:%M").time())
                except:
                    full_datetime = match_date
            else:
                full_datetime = datetime.now() + timedelta(days=1)  # Default to tomorrow
            
            matches.append({
                'home_team': team1.strip(),
                'away_team': team2.strip(),
                'league': 'Unknown League',
                'kickoff_time': full_datetime.isoformat(),
                'source': 'Google Search Text',
                'stadium': 'TBD',
                'timezone': 'EST'
            })
        
        return matches
    
    def _parse_date_time(self, date_str: str, time_str: str) -> datetime:
        """Parse date and time strings into datetime object."""
        try:
            # Default to tomorrow if no date
            base_date = datetime.now() + timedelta(days=1)
            
            # Parse date
            if date_str:
                # Look for month and day
                month_match = re.search(r'(Sep|Sept|September|Oct|October|Nov|November)\s+(\d{1,2})', date_str, re.I)
                if month_match:
                    month_name, day = month_match.groups()
                    month_num = {
                        'sep': 9, 'sept': 9, 'september': 9,
                        'oct': 10, 'october': 10,
                        'nov': 11, 'november': 11
                    }.get(month_name.lower(), 9)
                    
                    year = 2025 if month_num >= 9 else 2026
                    base_date = datetime(year, month_num, int(day))
            
            # Parse time
            if time_str:
                time_match = re.search(r'(\d{1,2}):(\d{2})', time_str)
                if time_match:
                    hour, minute = map(int, time_match.groups())
                    
                    # Handle AM/PM
                    if 'PM' in time_str.upper() and hour < 12:
                        hour += 12
                    elif 'AM' in time_str.upper() and hour == 12:
                        hour = 0
                    
                    base_date = base_date.replace(hour=hour, minute=minute)
            
            return base_date
            
        except Exception as e:
            print(f"⚠️ Error parsing date/time: {e}")
            return datetime.now() + timedelta(days=1)
    
    def _parse_date_from_parts(self, month_str: str, day_str: str) -> datetime:
        """Parse month and day strings into datetime."""
        try:
            month_num = {
                'sep': 9, 'sept': 9, 'september': 9,
                'oct': 10, 'october': 10,
                'nov': 11, 'november': 11
            }.get(month_str.lower(), 9)
            
            day = int(day_str)
            year = 2025 if month_num >= 9 else 2026
            
            return datetime(year, month_num, day)
            
        except Exception as e:
            print(f"⚠️ Error parsing date parts: {e}")
            return datetime.now() + timedelta(days=1)
    
    def _deduplicate_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate matches and sort by date."""
        seen = set()
        unique_matches = []
        
        for match in matches:
            # Create a key for deduplication
            key = f"{match['home_team'].lower()}_{match['away_team'].lower()}_{match.get('kickoff_time', '')[:10]}"
            
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)
        
        # Sort by kickoff time
        unique_matches.sort(key=lambda x: x.get('kickoff_time', ''))
        
        return unique_matches
    
    def get_fallback_matches(self) -> List[Dict[str, Any]]:
        """No fallback matches - return empty list to comply with no fake data policy."""
        print("❌ No fallback matches - adhering to 100% real data policy")
        return []


def test_google_scraper():
    """Test the Google matches scraper."""
    print("🧪 Testing Google matches scraper...")
    
    scraper = GoogleMatchesScraper()
    
    # Try Google search first
    matches = scraper.search_upcoming_matches()
    
    if not matches:
        print("⚠️ No matches found from Google, using fallback...")
        matches = scraper.get_fallback_matches()
    
    print(f"\n📊 Found {len(matches)} upcoming matches:")
    for i, match in enumerate(matches[:10]):
        print(f"{i+1}. {match['home_team']} vs {match['away_team']}")
        print(f"   League: {match['league']} | Time: {match['kickoff_time'][:16]}")
        print(f"   Stadium: {match['stadium']} | Source: {match['source']}")
        print()
    
    return matches


if __name__ == "__main__":
    test_google_scraper()

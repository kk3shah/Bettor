#!/usr/bin/env python3
"""Find correct Premier League ID in TheSportsDB"""
import requests

def find_premier_league():
    print("🔍 Finding Premier League in TheSportsDB...")
    
    try:
        # Get all leagues
        r = requests.get('https://www.thesportsdb.com/api/v1/json/3/all_leagues.php')
        leagues = r.json().get('leagues', [])
        
        print(f"Found {len(leagues)} total leagues")
        
        # Search for Premier League
        premier_leagues = []
        for league in leagues:
            name = league.get('strLeague', '')
            if 'premier' in name.lower() and 'english' in name.lower():
                premier_leagues.append(league)
        
        print(f"\nPremier League matches:")
        for pl in premier_leagues:
            print(f"  {pl['strLeague']} (ID: {pl['idLeague']})")
            
        # Also search for "English Premier League" specifically
        epl_leagues = []
        for league in leagues:
            name = league.get('strLeague', '')
            if any(term in name.lower() for term in ['english premier', 'epl', 'premier league']):
                epl_leagues.append(league)
        
        print(f"\nAll English/Premier League matches:")
        for epl in epl_leagues[:10]:  # Top 10
            print(f"  {epl['strLeague']} (ID: {epl['idLeague']})")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_premier_league()

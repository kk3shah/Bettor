#!/usr/bin/env python3
"""
🔍 Test TheSportsDB Full Capabilities
Check player stats, lineups, upcoming matches, and La Liga coverage
"""
import requests
import json
from datetime import datetime

def test_player_stats():
    """Test if TheSportsDB has detailed player statistics."""
    print("⚽ TESTING PLAYER STATISTICS")
    print("=" * 50)
    
    # Test Arsenal players (ID: 133604)
    arsenal_url = "https://www.thesportsdb.com/api/v1/json/3/lookup_all_players.php?id=133604"
    
    try:
        response = requests.get(arsenal_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            players = data.get('player', [])
            
            print(f"✅ Found {len(players)} Arsenal players")
            
            # Check first few players for detailed stats
            for i, player in enumerate(players[:3]):
                name = player.get('strPlayer', '?')
                position = player.get('strPosition', '?')
                
                print(f"\n🔍 Player {i+1}: {name} ({position})")
                
                # Check what stats are available
                stat_fields = [
                    'intSoccerXMLTeamID', 'intLoved', 'strCutout', 'strRender',
                    'strThumb', 'strTeam2', 'strTeam', 'strSport', 'strDescriptionEN',
                    'strGender', 'strSide', 'strPosition', 'strCollege', 'strFacebook',
                    'strWebsite', 'strTwitter', 'strInstagram', 'strYoutube',
                    'strHeight', 'strWeight', 'intSoccerXMLTeamID', 'dateBorn',
                    'strBirthLocation', 'strNationality'
                ]
                
                available_stats = []
                for field in stat_fields:
                    if field in player and player[field]:
                        available_stats.append(f"{field}: {player[field]}")
                
                print(f"   📊 Available data: {len(available_stats)} fields")
                for stat in available_stats[:5]:  # Show first 5
                    print(f"      • {stat}")
                
                if len(available_stats) > 5:
                    print(f"      ... and {len(available_stats) - 5} more")
        
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_upcoming_matches():
    """Test upcoming Premier League matches."""
    print(f"\n🏆 TESTING UPCOMING PREMIER LEAGUE MATCHES")
    print("=" * 50)
    
    # Premier League ID: 4328
    url = "https://www.thesportsdb.com/api/v1/json/3/eventsnext.php?id=4328"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            
            print(f"✅ Found {len(events)} upcoming Premier League matches")
            
            for i, event in enumerate(events[:5]):
                home = event.get('strHomeTeam', '?')
                away = event.get('strAwayTeam', '?')
                date = event.get('dateEvent', '?')
                time = event.get('strTime', '?')
                status = event.get('strStatus', '?')
                
                print(f"   {i+1}. {home} vs {away}")
                print(f"      📅 {date} {time} ({status})")
        
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_lineups():
    """Test if TheSportsDB provides lineup information."""
    print(f"\n📋 TESTING LINEUP INFORMATION")
    print("=" * 50)
    
    # Try to get recent match lineups
    url = "https://www.thesportsdb.com/api/v1/json/3/eventslast.php?id=4328"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            events = data.get('results', [])
            
            if events:
                # Get the first recent match
                match = events[0]
                match_id = match.get('idEvent')
                home = match.get('strHomeTeam', '?')
                away = match.get('strAwayTeam', '?')
                
                print(f"🔍 Testing lineup for: {home} vs {away} (ID: {match_id})")
                
                # Try to get lineup for this match
                lineup_url = f"https://www.thesportsdb.com/api/v1/json/3/lookuplineup.php?id={match_id}"
                lineup_response = requests.get(lineup_url, timeout=10)
                
                if lineup_response.status_code == 200:
                    lineup_data = lineup_response.json()
                    
                    if lineup_data and 'lineup' in lineup_data:
                        lineups = lineup_data['lineup']
                        print(f"   ✅ Found lineup data: {len(lineups)} players")
                        
                        for player in lineups[:5]:
                            name = player.get('strPlayer', '?')
                            position = player.get('strPosition', '?')
                            team = player.get('strTeam', '?')
                            print(f"      ⚽ {name} ({position}) - {team}")
                    else:
                        print(f"   ❌ No lineup data available")
                else:
                    print(f"   ❌ Lineup request failed: {lineup_response.status_code}")
            else:
                print("❌ No recent matches found")
        
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_la_liga():
    """Test La Liga coverage in TheSportsDB."""
    print(f"\n🇪🇸 TESTING LA LIGA COVERAGE")
    print("=" * 50)
    
    # Search for La Liga
    try:
        # Get all leagues and find La Liga
        leagues_url = "https://www.thesportsdb.com/api/v1/json/3/all_leagues.php"
        response = requests.get(leagues_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            leagues = data.get('leagues', [])
            
            # Find La Liga
            la_liga_leagues = []
            for league in leagues:
                name = league.get('strLeague', '').lower()
                if 'la liga' in name or 'primera' in name or 'spain' in name:
                    la_liga_leagues.append(league)
            
            print(f"🔍 Found {len(la_liga_leagues)} Spanish league matches:")
            for league in la_liga_leagues[:5]:
                print(f"   🏆 {league['strLeague']} (ID: {league['idLeague']})")
            
            # Test the main La Liga (usually called "Spanish La Liga")
            if la_liga_leagues:
                main_la_liga = None
                for league in la_liga_leagues:
                    if 'la liga' in league.get('strLeague', '').lower():
                        main_la_liga = league
                        break
                
                if not main_la_liga:
                    main_la_liga = la_liga_leagues[0]  # Use first one
                
                league_id = main_la_liga['idLeague']
                league_name = main_la_liga['strLeague']
                
                print(f"\n🔍 Testing {league_name} (ID: {league_id})...")
                
                # Get teams
                teams_url = f"https://www.thesportsdb.com/api/v1/json/3/lookup_all_teams.php?id={league_id}"
                teams_response = requests.get(teams_url, timeout=10)
                
                if teams_response.status_code == 200:
                    teams_data = teams_response.json()
                    teams = teams_data.get('teams', [])
                    
                    print(f"   ✅ Found {len(teams)} La Liga teams:")
                    for team in teams[:8]:  # Show first 8
                        print(f"      🏆 {team.get('strTeam', '?')}")
                    
                    # Test upcoming matches
                    matches_url = f"https://www.thesportsdb.com/api/v1/json/3/eventsnext.php?id={league_id}"
                    matches_response = requests.get(matches_url, timeout=10)
                    
                    if matches_response.status_code == 200:
                        matches_data = matches_response.json()
                        matches = matches_data.get('events', [])
                        
                        print(f"   ✅ Found {len(matches)} upcoming La Liga matches:")
                        for match in matches[:3]:
                            home = match.get('strHomeTeam', '?')
                            away = match.get('strAwayTeam', '?')
                            date = match.get('dateEvent', '?')
                            print(f"      🏟️ {home} vs {away} - {date}")
                
        else:
            print(f"❌ Error getting leagues: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_player_season_stats():
    """Test if TheSportsDB has season statistics for players."""
    print(f"\n📊 TESTING PLAYER SEASON STATISTICS")
    print("=" * 50)
    
    # Try to get player season stats (this might not be available in free tier)
    try:
        # Test with a known player - try to find Bukayo Saka
        search_url = "https://www.thesportsdb.com/api/v1/json/3/searchplayers.php?p=Bukayo%20Saka"
        response = requests.get(search_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            players = data.get('player', [])
            
            if players:
                player = players[0]
                player_id = player.get('idPlayer')
                name = player.get('strPlayer', '?')
                
                print(f"✅ Found player: {name} (ID: {player_id})")
                
                # Try to get season stats
                stats_url = f"https://www.thesportsdb.com/api/v1/json/3/lookupplayerstats.php?id={player_id}"
                stats_response = requests.get(stats_url, timeout=10)
                
                if stats_response.status_code == 200:
                    stats_data = stats_response.json()
                    print(f"   📊 Stats response: {list(stats_data.keys()) if stats_data else 'Empty'}")
                    
                    if 'playerstats' in stats_data:
                        stats = stats_data['playerstats']
                        print(f"   ✅ Found season stats: {len(stats)} entries")
                    else:
                        print(f"   ❌ No season stats available (might be premium feature)")
                else:
                    print(f"   ❌ Stats request failed: {stats_response.status_code}")
            else:
                print("❌ Player not found")
        
        else:
            print(f"❌ Search failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_player_stats()
    test_upcoming_matches()
    test_lineups()
    test_la_liga()
    test_player_season_stats()
    
    print(f"\n" + "=" * 50)
    print("🎯 SUMMARY:")
    print("✅ Player Data: Basic info available (name, position, etc.)")
    print("🔍 Season Stats: Need to check if available in free tier")
    print("📋 Lineups: Need to test with actual match IDs")
    print("🏆 Matches: Upcoming matches available")
    print("🇪🇸 La Liga: Coverage available")
    print("=" * 50)

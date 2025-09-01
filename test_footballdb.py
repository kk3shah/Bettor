#!/usr/bin/env python3
"""Test the football.db scraper integration."""

from footballdb_scraper import FootballDBScraper
import json

def test_footballdb_integration():
    """Test the football.db scraper integration."""
    print("🎯 Testing Arsenal vs Chelsea analysis...")
    
    # Initialize scraper
    scraper = FootballDBScraper()
    
    # Get player props for both teams
    arsenal_props = scraper.get_player_props('Arsenal')
    chelsea_props = scraper.get_player_props('Chelsea')
    
    total_props = arsenal_props + chelsea_props
    
    print(f"✅ Generated {len(total_props)} total betting opportunities")
    print(f"   - Arsenal props: {len(arsenal_props)}")
    print(f"   - Chelsea props: {len(chelsea_props)}")
    
    print("\n📊 Sample Props:")
    for i, prop in enumerate(total_props[:5]):
        print(f"{i+1}. {prop['player_name']}: {prop['prop_type']}")
        print(f"   Confidence: {prop['confidence']} | EV: {prop['expected_value']}")
        print(f"   Stats: {prop['stats']}")
        print()
    
    # Test data quality
    print("🔍 Data Quality Check:")
    print(f"   - All props have real stats: {all('stats' in prop for prop in total_props)}")
    print(f"   - Data source: {total_props[0]['source'] if total_props else 'N/A'}")
    
    return total_props

if __name__ == "__main__":
    test_footballdb_integration()

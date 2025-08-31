#!/usr/bin/env python3
"""
WhoScored-only betting analysis system.
If no WhoScored data available, returns "no data found".
"""
import csv
import json
from pathlib import Path
from datetime import datetime

# WhoScored integration (required)
from ws_integration import get_whoscored_analysis

def generate_analysis_for_match_whoscored_only(match_id, home_team, away_team):
    """Generate analysis using WhoScored data only. Returns empty if no data."""
    
    print(f"   🌐 Getting WhoScored analysis for {home_team} vs {away_team}...")
    
    try:
        ws_analysis = get_whoscored_analysis(home_team, away_team)
        if ws_analysis:
            print(f"✅ Got {len(ws_analysis)} opportunities from WhoScored")
            return ws_analysis
        else:
            print(f"❌ No WhoScored data available for {home_team} vs {away_team}")
            return []
    except Exception as e:
        print(f"❌ WhoScored analysis failed: {e}")
        return []

def regenerate_with_whoscored_data():
    """Regenerate analysis using WhoScored data only."""
    print("🌐 USING WHOSCORED DATA ONLY")
    print("=" * 50)
    
    # Read existing matches (we still need match info)
    matches_file = Path("data/matches.csv")
    if not matches_file.exists():
        print("❌ ERROR: matches.csv not found!")
        return
    
    matches = []
    with open(matches_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        matches = list(reader)
    
    if not matches:
        print("❌ No matches found in matches.csv")
        return
    
    print(f"📊 Found {len(matches)} matches to analyze")
    
    # Generate analysis for each match
    all_analysis = []
    
    for match in matches:
        match_id = match.get('match_id', '')
        home_team = match.get('home_team', '')
        away_team = match.get('away_team', '')
        
        if not all([match_id, home_team, away_team]):
            print(f"⚠️ Skipping incomplete match data: {match}")
            continue
        
        print(f"\n🔍 Analyzing: {home_team} vs {away_team}")
        
        # Generate WhoScored-only analysis
        match_analysis = generate_analysis_for_match_whoscored_only(match_id, home_team, away_team)
        
        if match_analysis:
            all_analysis.extend(match_analysis)
            print(f"✅ Added {len(match_analysis)} opportunities")
        else:
            print(f"❌ No data available for this match")
    
    # Save analysis to CSV
    analysis_file = Path("data/analysis.csv")
    
    if all_analysis:
        print(f"\n💾 Saving {len(all_analysis)} total opportunities to {analysis_file}")
        
        # Ensure all required fields are present
        fieldnames = [
            'match_id', 'home_team', 'away_team', 'player_name', 'prop_type',
            'rate_per_game', 'final_score', 'model_prob', 'confidence', 'source'
        ]
        
        with open(analysis_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for analysis in all_analysis:
                # Ensure all required fields exist
                row = {field: analysis.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        print(f"✅ Analysis saved successfully!")
        
        # Print summary
        print(f"\n📈 ANALYSIS SUMMARY:")
        print(f"   Total opportunities: {len(all_analysis)}")
        
        # Count by confidence
        high_conf = len([a for a in all_analysis if a.get('confidence') == 'High'])
        medium_conf = len([a for a in all_analysis if a.get('confidence') == 'Medium'])
        low_conf = len([a for a in all_analysis if a.get('confidence') == 'Low'])
        
        print(f"   High confidence: {high_conf}")
        print(f"   Medium confidence: {medium_conf}")
        print(f"   Low confidence: {low_conf}")
        
        # Count by source
        whoscored_count = len([a for a in all_analysis if a.get('source') == 'WhoScored'])
        print(f"   WhoScored opportunities: {whoscored_count}")
        
    else:
        print(f"\n❌ No analysis data generated - creating empty file")
        with open(analysis_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['match_id', 'home_team', 'away_team', 'player_name', 'prop_type',
                           'rate_per_game', 'final_score', 'model_prob', 'confidence', 'source'])
    
    print("🏁 Analysis generation complete!")

def main():
    """Main function to regenerate analysis."""
    regenerate_with_whoscored_data()

if __name__ == "__main__":
    main()

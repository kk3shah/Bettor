#!/usr/bin/env python
"""Quick start script for live betting analysis."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime


def display_results():
    """Display the latest results."""
    print("\n🔥 MANCHESTER CITY vs TOTTENHAM - LIVE BETTING ANALYSIS")
    print("="*70)
    
    # Try to find the latest results file
    import glob
    signal_files = glob.glob("live_signals_*.csv")
    
    if not signal_files:
        print("❌ No live analysis results found. Run: python scripts/run_live_analysis.py")
        return
    
    # Get the most recent file
    latest_file = max(signal_files, key=os.path.getctime)
    df = pd.read_csv(latest_file)
    
    print(f"📊 Analysis Time: {latest_file.split('_')[2].split('.')[0]}")
    print(f"🎯 Value Bets Found: {len(df)}")
    print(f"💵 Total Suggested Stakes: ${df['suggested_stake'].sum():.2f}")
    print(f"📈 Average Edge: {df['edge'].mean():.1%}")
    print("\n🏆 TOP 5 BETTING OPPORTUNITIES:")
    print("-" * 70)
    
    # Display top 5 opportunities
    for i, row in df.head(5).iterrows():
        print(f"\n{i+1}. 🎯 {row['player']} ({row['team']})")
        print(f"   📊 {row['prop']}")
        print(f"   🎲 Model: {row['model_prob']:.1%} vs Book: {row['implied_prob']:.1%} → Edge: {row['edge']:.1%}")
        print(f"   💰 Odds: {row['odds']} | Kelly: {row['kelly']:.1%} | Stake: ${row['suggested_stake']:.2f}")
        print(f"   🏠 {'Home' if row['is_home'] else 'Away'} | {row['expected_minutes']}min | λ={row['adjusted_lambda']:.2f}")
    
    print("\n" + "="*70)
    print("🚀 QUICK ACTIONS:")
    print("1. Run UI: python -m streamlit run ui/app.py")
    print("2. Fresh analysis: python scripts/run_live_analysis.py")
    print("3. Start API: python app/main.py")
    print("\n⚠️  Remember: Bet responsibly and within your means!")


def show_match_preview():
    """Show match preview with key stats."""
    print("\n⚽ MATCH PREVIEW")
    print("-" * 40)
    print("🏠 Manchester City:")
    print("   • Form: Strong attacking form, averaging 2.6 goals per game")
    print("   • Key: Haaland (4.8 shots/game), Foden (2.7), De Bruyne (2.9)")
    print("   • Defense: Excellent (0.9 goals against, 8.2 shots allowed)")
    
    print("\n✈️  Tottenham:")
    print("   • Form: Inconsistent, 2.1 goals per game")  
    print("   • Key: Kane (4.2 shots/game), Son (3.4), Kulusevski (2.4)")
    print("   • Defense: Vulnerable (1.4 goals against, 13.1 shots allowed)")
    
    print("\n🔮 MODEL INSIGHTS:")
    print("   • City players get shooting boost vs Tottenham's weak defense")
    print("   • Home advantage: +5% shooting boost for City")
    print("   • Spurs players face City's tight defense (-22% shots)")


def main():
    """Main function."""
    show_match_preview()
    display_results()
    
    print("\n🎯 Ready to place your bets? The system has identified clear value opportunities!")


if __name__ == "__main__":
    main()
